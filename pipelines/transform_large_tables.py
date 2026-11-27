
from pathlib import Path
from tempfile import TemporaryDirectory
import logging
import sqlite3

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from pipelines.transform_gtfs import convert_time_column
from pipelines.transform_tables import (
    convert_integer,
    convert_float,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GTFS_DIR = PROJECT_ROOT / "data" / "raw" / "gtfs"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

CHUNK_SIZE = 100_000

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


def validate_required_columns(df, columns):
    """Reject missing or empty required values."""

    for column in columns:
        values = df[column]

        if values.isna().any():
            raise ValueError(
                f"Missing required values in {column}"
            )

        if values.astype("string").str.strip().eq("").any():
            raise ValueError(
                f"Empty required values in {column}"
            )


def validate_nonnegative(series, column_name):
    """Reject missing or negative numeric values."""

    if series.isna().any() or (series < 0).any():
        raise ValueError(
            f"Invalid nonnegative values in {column_name}"
        )


def validate_coordinates(series, minimum, maximum, name):
    """Validate geographic coordinate ranges."""

    if not series.between(
        minimum, maximum
    ).fillna(False).all():
        raise ValueError(
            f"Invalid coordinates in {name}"
        )


def transform_stop_times(df):
    """Transform a chunk of scheduled stop-time records."""

    df = df.copy()

    validate_required_columns(
        df,
        [
            "trip_id",
            "stop_id",
            "stop_sequence",
            "arrival_time",
            "departure_time",
        ]
    )

    df["arrival_seconds"] = convert_time_column(
        df["arrival_time"]
    )

    df["departure_seconds"] = convert_time_column(
        df["departure_time"]
    )

    df["stop_sequence"] = convert_integer(
        df["stop_sequence"]
    )

    df["pickup_type"] = convert_integer(
        df["pickup_type"]
    )

    df["drop_off_type"] = convert_integer(
        df["drop_off_type"]
    )

    df["shape_dist_traveled"] = convert_float(
        df["shape_dist_traveled"]
    )

    validate_nonnegative(
        df["stop_sequence"],
        "stop_sequence"
    )

    if (
        df["departure_seconds"] < df["arrival_seconds"]
    ).any():
        raise ValueError(
            "Departure time occurs before arrival time."
        )

    for column in ["pickup_type", "drop_off_type"]:
        values = df[column].dropna()

        if not values.isin([0, 1, 2, 3]).all():
            raise ValueError(
                f"Invalid values in {column}"
            )

    distances = df["shape_dist_traveled"].dropna()

    if (
        not np.isfinite(distances.to_numpy(dtype=float)).all()
        or (distances < 0).any()
    ):
        raise ValueError("Invalid stop-time distances.")

    return df


def transform_shapes(df):
    """Transform a chunk of route geometry records."""

    df = df.copy()

    validate_required_columns(
        df,
        [
            "shape_id",
            "shape_pt_lat",
            "shape_pt_lon",
            "shape_pt_sequence",
        ]
    )

    df["shape_pt_lat"] = convert_float(
        df["shape_pt_lat"]
    )

    df["shape_pt_lon"] = convert_float(
        df["shape_pt_lon"]
    )

    df["shape_pt_sequence"] = convert_integer(
        df["shape_pt_sequence"]
    )

    df["shape_dist_traveled"] = convert_float(
        df["shape_dist_traveled"]
    )

    validate_coordinates(
        df["shape_pt_lat"],
        -90,
        90,
        "shape_pt_lat"
    )

    validate_coordinates(
        df["shape_pt_lon"],
        -180,
        180,
        "shape_pt_lon"
    )

    validate_nonnegative(
        df["shape_pt_sequence"],
        "shape_pt_sequence"
    )

    distances = df["shape_dist_traveled"].dropna()

    if (
        not np.isfinite(distances.to_numpy(dtype=float)).all()
        or (distances < 0).any()
    ):
        raise ValueError("Invalid shape distances.")

    return df


def validate_composite_keys(connection, df, columns):
    """Detect duplicate keys within and across chunks."""

    validate_required_columns(df, columns)

    records = (
        (str(identifier), int(sequence))
        for identifier, sequence in df[columns].itertuples(
            index=False,
            name=None
        )
    )

    try:
        with connection:
            connection.executemany(
                """
                INSERT INTO seen_keys (identifier, sequence)
                VALUES (?, ?)
                """,
                records
            )

    except sqlite3.IntegrityError as exc:
        raise ValueError(
            f"Duplicate composite key detected: {columns}"
        ) from exc


def process_large_table(
    table_name,
    transform_function,
    key_columns
):
    """Transform and save a large GTFS table in chunks."""

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    input_path = GTFS_DIR / f"{table_name}.txt"

    output_path = (
        PROCESSED_DIR / f"{table_name}.parquet"
    )

    temp_path = output_path.with_suffix(".parquet.tmp")

    if not input_path.exists():
        raise FileNotFoundError(input_path)

    logger.info("Processing %s", input_path.name)

    total_rows = 0
    written_rows = 0
    chunk_count = 0
    writer = None

    try:
        with TemporaryDirectory(
            dir=PROCESSED_DIR
        ) as temp_directory:

            database_path = (
                Path(temp_directory) / "validation.sqlite"
            )

            connection = sqlite3.connect(database_path)

            try:
                connection.execute(
                    """
                    CREATE TABLE seen_keys (
                        identifier TEXT NOT NULL,
                        sequence INTEGER NOT NULL,
                        PRIMARY KEY (identifier, sequence)
                    ) WITHOUT ROWID
                    """
                )

                reader = pd.read_csv(
                    input_path,
                    chunksize=CHUNK_SIZE,
                    dtype="string",
                    encoding="utf-8-sig",
                    keep_default_na=False,
                    na_values=[""]
                )

                for chunk in reader:
                    total_rows += len(chunk)

                    transformed = transform_function(chunk)

                    if len(chunk) != len(transformed):
                        raise ValueError(
                            "Unexpected row count change."
                        )

                    validate_composite_keys(
                        connection,
                        transformed,
                        key_columns
                    )

                    arrow_table = pa.Table.from_pandas(
                        transformed,
                        preserve_index=False
                    )

                    if writer is None:
                        writer = pq.ParquetWriter(
                            temp_path,
                            arrow_table.schema,
                            compression="snappy"
                        )

                    writer.write_table(arrow_table)

                    written_rows += len(transformed)
                    chunk_count += 1

                    print(
                        f"\r{table_name}: "
                        f"{written_rows:,} rows processed "
                        f"({chunk_count} chunks)",
                        end="",
                        flush=True
                    )

            finally:
                connection.close()

        print()

        if writer is None:
            raise ValueError(
                f"No records found in {table_name}"
            )

        writer.close()
        writer = None

        metadata = pq.read_metadata(temp_path)

        if not (
            total_rows == written_rows == metadata.num_rows
        ):
            raise ValueError(
                f"Row count mismatch in {table_name}"
            )

        temp_path.replace(output_path)

    finally:
        if writer is not None:
            writer.close()

        temp_path.unlink(missing_ok=True)

    original_size = (
        input_path.stat().st_size / (1024 * 1024)
    )

    processed_size = (
        output_path.stat().st_size / (1024 * 1024)
    )

    reduction = (
        1 - processed_size / original_size
    ) * 100

    logger.info(
        "Saved %s | Rows: %s | Size: %.2f MiB",
        output_path.name,
        f"{written_rows:,}",
        processed_size
    )

    return {
        "table": table_name,
        "rows": written_rows,
        "chunks": chunk_count,
        "raw_mib": round(original_size, 2),
        "parquet_mib": round(processed_size, 2),
        "reduction_pct": round(reduction, 2),
    }


def main():
    """Transform the two largest GTFS tables."""

    logger.info("Starting large-table transformation...")

    results = []

    results.append(
        process_large_table(
            "shapes",
            transform_shapes,
            ["shape_id", "shape_pt_sequence"]
        )
    )

    results.append(
        process_large_table(
            "stop_times",
            transform_stop_times,
            ["trip_id", "stop_sequence"]
        )
    )

    print("\n=== LARGE TABLE TRANSFORMATION SUMMARY ===\n")

    print(pd.DataFrame(results).to_string(index=False))

    logger.info(
        "Large-table transformation completed."
    )


if __name__ == "__main__":
    main()
