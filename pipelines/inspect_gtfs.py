
from pathlib import Path
import logging

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GTFS_DIR = PROJECT_ROOT / "data" / "raw" / "gtfs"

CHUNK_SIZE = 100_000

EXPECTED_FILES = [
    "agency.txt",
    "calendar.txt",
    "calendar_dates.txt",
    "routes.txt",
    "shapes.txt",
    "stops.txt",
    "stop_times.txt",
    "trips.txt",
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


def inspect_file(file_path):
    """Inspect a GTFS table without loading it entirely into memory."""

    logger.info("Inspecting %s", file_path.name)

    file_size = file_path.stat().st_size / (1024 * 1024)

    sample = pd.read_csv(
        file_path,
        nrows=5,
        dtype=str,
        encoding="utf-8-sig"
    )

    row_count = 0

    missing_values = pd.Series(
        0,
        index=sample.columns,
        dtype="int64"
    )

    for chunk in pd.read_csv(
        file_path,
        chunksize=CHUNK_SIZE,
        dtype=str,
        encoding="utf-8-sig"
    ):
        row_count += len(chunk)
        missing_values += chunk.isna().sum()

    print("\n" + "=" * 70)
    print(f"FILE: {file_path.name}")
    print("=" * 70)

    print(f"File size: {file_size:.2f} MiB")
    print(f"Rows: {row_count:,}")
    print(f"Columns: {len(sample.columns)}")

    print("\nColumn names:")
    for column in sample.columns:
        print(f"  - {column}")

    print("\nMissing values:")
    for column, count in missing_values.items():

        percentage = (
            count / row_count * 100
            if row_count else 0
        )

        print(
            f"  {column}: "
            f"{count:,} ({percentage:.2f}%)"
        )

    print("\nFirst 5 rows:")
    print(sample.to_string(index=False))

    return {
        "file": file_path.name,
        "rows": row_count,
        "columns": len(sample.columns),
        "size_mib": round(file_size, 2)
    }


def main():
    """Inspect all downloaded GTFS files."""

    if not GTFS_DIR.exists():
        raise FileNotFoundError(
            "GTFS directory not found. "
            "Run download_gtfs.py first."
        )

    results = []

    for filename in EXPECTED_FILES:

        file_path = GTFS_DIR / filename

        if not file_path.exists():
            logger.warning("Missing file: %s", filename)
            continue

        result = inspect_file(file_path)
        results.append(result)

    summary = pd.DataFrame(results)

    print("\n" + "=" * 70)
    print("GTFS DATASET SUMMARY")
    print("=" * 70)

    print(summary.to_string(index=False))

    logger.info("GTFS inspection completed.")


if __name__ == "__main__":
    main()
