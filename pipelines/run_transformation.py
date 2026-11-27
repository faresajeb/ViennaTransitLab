
from pathlib import Path
from time import perf_counter
import logging

import pyarrow.parquet as pq

from pipelines import transform_tables
from pipelines import transform_large_tables
from pipelines import expand_calendar


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GTFS_DIR = PROJECT_ROOT / "data" / "raw" / "gtfs"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

SOURCE_TABLES = [
    "agency",
    "calendar",
    "calendar_dates",
    "routes",
    "shapes",
    "stops",
    "stop_times",
    "trips",
]

OUTPUT_TABLES = SOURCE_TABLES + ["service_dates"]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


def validate_inputs():
    """Verify that all required source files exist."""

    missing = [
        f"{table}.txt"
        for table in SOURCE_TABLES
        if not (GTFS_DIR / f"{table}.txt").is_file()
    ]

    if missing:
        raise FileNotFoundError(
            f"Missing GTFS files: {missing}. "
            "Run download_gtfs.py first."
        )

    logger.info("All required GTFS source files found.")


def run_stage(name, function):
    """Execute a pipeline stage and measure its duration."""

    logger.info("Starting stage: %s", name)

    start = perf_counter()

    function()

    duration = perf_counter() - start

    logger.info(
        "Completed stage: %s | Duration: %.2f seconds",
        name,
        duration
    )

    return duration


def verify_outputs():
    """Verify processed Parquet files and their metadata."""

    results = []

    for table in OUTPUT_TABLES:

        path = PROCESSED_DIR / f"{table}.parquet"

        if not path.is_file():
            raise FileNotFoundError(
                f"Missing output: {path.name}"
            )

        metadata = pq.read_metadata(path)

        if metadata.num_rows == 0:
            raise ValueError(
                f"Empty output table: {table}"
            )

        results.append({
            "table": table,
            "rows": metadata.num_rows,
            "columns": metadata.num_columns,
            "bytes": path.stat().st_size,
        })

    return results


def print_summary(results, timings, duration):
    """Display pipeline execution statistics."""

    print("\n" + "=" * 70)
    print("TRANSFORMATION PIPELINE SUMMARY")
    print("=" * 70)

    print(
        f"{'Table':<20}"
        f"{'Rows':>15}"
        f"{'Columns':>10}"
        f"{'Size (MiB)':>15}"
    )

    print("-" * 60)

    for result in results:

        size = result["bytes"] / (1024 * 1024)

        print(
            f"{result['table']:<20}"
            f"{result['rows']:>15,}"
            f"{result['columns']:>10}"
            f"{size:>15.4f}"
        )

    total_rows = sum(
        result["rows"] for result in results
    )

    total_bytes = sum(
        result["bytes"] for result in results
    )

    raw_bytes = sum(
        (GTFS_DIR / f"{table}.txt").stat().st_size
        for table in SOURCE_TABLES
    )

    reduction = (
        1 - total_bytes / raw_bytes
    ) * 100

    print("\n=== STORAGE SUMMARY ===\n")

    print(f"Output tables: {len(results)}")
    print(f"Total output records: {total_rows:,}")
    print(f"Raw size: {raw_bytes / (1024 * 1024):.2f} MiB")
    print(f"Processed size: {total_bytes / (1024 * 1024):.2f} MiB")
    print(f"Storage reduction: {reduction:.2f}%")

    print("\n=== EXECUTION TIMES ===\n")

    for name, seconds in timings.items():
        print(f"{name}: {seconds:.2f} seconds")

    print(f"\nTotal duration: {duration:.2f} seconds")


def main():
    """Execute the complete GTFS transformation pipeline."""

    start = perf_counter()

    logger.info("Starting complete GTFS transformation...")

    validate_inputs()

    timings = {}

    timings["Small-table transformation"] = run_stage(
        "Small-table transformation",
        transform_tables.main
    )

    timings["Large-table transformation"] = run_stage(
        "Large-table transformation",
        transform_large_tables.main
    )

    timings["Calendar expansion"] = run_stage(
        "Calendar expansion",
        expand_calendar.main
    )

    results = verify_outputs()

    duration = perf_counter() - start

    print_summary(results, timings, duration)

    logger.info(
        "Complete GTFS transformation pipeline succeeded."
    )


if __name__ == "__main__":
    main()
