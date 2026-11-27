
from pathlib import Path
import logging
import re

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GTFS_DIR = PROJECT_ROOT / "data" / "raw" / "gtfs"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

CHUNK_SIZE = 100_000

GTFS_TIME_PATTERN = re.compile(
    r"[0-9]+:[0-5][0-9]:[0-5][0-9]"
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


def gtfs_time_to_seconds(value: str) -> int:
    """Convert a GTFS time into service-day seconds.

    GTFS hours may exceed 23 to represent services
    continuing after midnight.
    """

    if not isinstance(value, str):
        raise ValueError(f"Invalid GTFS time: {value!r}")

    if not GTFS_TIME_PATTERN.fullmatch(value):
        raise ValueError(f"Invalid GTFS time: {value!r}")

    hours, minutes, seconds = map(int, value.split(":"))

    return hours * 3600 + minutes * 60 + seconds


def seconds_to_gtfs_time(value: int) -> str:
    """Convert service-day seconds back into GTFS time."""

    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("Seconds must be an integer.")

    if value < 0:
        raise ValueError("Seconds cannot be negative.")

    hours, remainder = divmod(value, 3600)
    minutes, seconds = divmod(remainder, 60)

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def convert_time_column(series: pd.Series) -> pd.Series:
    """Convert a GTFS time column using vectorized operations."""

    values = series.astype("string")

    valid = values.str.fullmatch(
        GTFS_TIME_PATTERN.pattern,
        na=False
    )

    if not valid.all():
        invalid_values = values[~valid].head(5).tolist()

        raise ValueError(
            f"Invalid GTFS time values: {invalid_values}"
        )

    parts = values.str.split(":", expand=True).astype("int64")

    result = (
        parts[0] * 3600
        + parts[1] * 60
        + parts[2]
    )

    return result.rename(series.name)


def main():
    """Demonstrate GTFS time conversion."""

    examples = [
        "00:00:00",
        "08:30:00",
        "12:00:00",
        "23:59:00",
        "24:00:00",
        "24:38:00",
        "25:01:00",
        "26:30:00",
    ]

    print("\n=== GTFS TIME CONVERSION ===\n")

    for value in examples:
        seconds = gtfs_time_to_seconds(value)
        restored = seconds_to_gtfs_time(seconds)

        print(
            f"{value} -> {seconds:>6,} seconds "
            f"-> {restored}"
        )

    logger.info("Time conversion demonstration completed.")


if __name__ == "__main__":
    main()
