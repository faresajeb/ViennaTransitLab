
from pathlib import Path
import logging

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GTFS_DIR = PROJECT_ROOT / "data" / "raw" / "gtfs"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

WEEKDAY_COLUMNS = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]

ROUTE_TYPES = {
    0: "Tram / Light rail",
    1: "Subway / U-Bahn",
    2: "Rail",
    3: "Bus",
    4: "Ferry",
    5: "Cable tram",
    6: "Aerial lift",
    7: "Funicular",
    11: "Trolleybus",
    12: "Monorail",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


def load_table(filename):
    """Load a raw GTFS table."""

    return pd.read_csv(
        GTFS_DIR / filename,
        dtype="string",
        encoding="utf-8-sig",
        keep_default_na=False,
        na_values=[""]
    )


def convert_integer(series):
    """Convert a column into nullable integers."""

    return pd.to_numeric(
        series,
        errors="raise"
    ).astype("Int64")


def convert_float(series):
    """Convert a column into floating-point numbers."""

    return pd.to_numeric(
        series,
        errors="raise"
    ).astype("Float64")


def convert_date(series):
    """Convert GTFS YYYYMMDD dates."""

    return pd.to_datetime(
        series,
        format="%Y%m%d",
        errors="raise"
    )


def convert_boolean(series):
    """Convert GTFS binary flags into booleans."""

    valid = series.isin(["0", "1"])

    if not valid.all():
        invalid = series[~valid].head(5).tolist()

        raise ValueError(
            f"Invalid boolean values: {invalid}"
        )

    return series.map({
        "0": False,
        "1": True
    }).astype("boolean")


def transform_agency(df):
    """Transform the agency table."""

    return df.copy()


def transform_routes(df):
    """Transform transport route records."""

    df = df.copy()

    df["route_type"] = convert_integer(
        df["route_type"]
    )

    df["transport_type"] = (
        df["route_type"]
        .map(ROUTE_TYPES)
        .fillna("Other / Extended type")
        .astype("string")
    )

    return df


def transform_stops(df):
    """Transform geographic stop records."""

    df = df.copy()

    df["stop_lat"] = convert_float(df["stop_lat"])
    df["stop_lon"] = convert_float(df["stop_lon"])

    return df


def transform_trips(df):
    """Transform scheduled trip records."""

    df = df.copy()

    df["direction_id"] = convert_integer(
        df["direction_id"]
    )

    return df


def transform_calendar(df):
    """Transform regular service schedules."""

    df = df.copy()

    for column in WEEKDAY_COLUMNS:
        df[column] = convert_boolean(df[column])

    df["start_date"] = convert_date(df["start_date"])
    df["end_date"] = convert_date(df["end_date"])

    if (df["start_date"] > df["end_date"]).any():
        raise ValueError(
            "Calendar contains invalid date ranges."
        )

    return df


def transform_calendar_dates(df):
    """Transform exceptions to regular schedules."""

    df = df.copy()

    df["date"] = convert_date(df["date"])

    df["exception_type"] = convert_integer(
        df["exception_type"]
    )

    if not df["exception_type"].isin([1, 2]).all():
        raise ValueError("Invalid calendar exception type.")

    return df


def save_table(df, table_name):
    """Save a transformed table in Parquet format."""

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path = PROCESSED_DIR / f"{table_name}.parquet"

    df.to_parquet(
        output_path,
        engine="pyarrow",
        compression="snappy",
        index=False
    )

    size_mib = (
        output_path.stat().st_size / (1024 * 1024)
    )

    logger.info(
        "Saved %s | Rows: %s | Size: %.2f MiB",
        output_path.name,
        f"{len(df):,}",
        size_mib
    )

    return output_path


def main():
    """Transform the six smaller GTFS tables."""

    transformations = {
        "agency": transform_agency,
        "routes": transform_routes,
        "stops": transform_stops,
        "trips": transform_trips,
        "calendar": transform_calendar,
        "calendar_dates": transform_calendar_dates,
    }

    logger.info("Starting GTFS table transformation...")

    results = []

    for table_name, transform in transformations.items():

        logger.info("Transforming %s", table_name)

        raw_df = load_table(f"{table_name}.txt")
        transformed_df = transform(raw_df)

        if len(raw_df) != len(transformed_df):
            raise ValueError(
                f"Unexpected row count change: {table_name}"
            )

        output_path = save_table(
            transformed_df,
            table_name
        )

        results.append({
            "table": table_name,
            "rows": len(transformed_df),
            "columns": len(transformed_df.columns),
            "size_mib": round(
                output_path.stat().st_size / (1024 * 1024),
                4
            )
        })

        print(f"\nData types for {table_name}:")
        print(transformed_df.dtypes.to_string())
        print()

    print("\n=== TRANSFORMATION SUMMARY ===\n")
    print(pd.DataFrame(results).to_string(index=False))

    logger.info("GTFS table transformation completed.")


if __name__ == "__main__":
    main()
