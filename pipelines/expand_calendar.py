
from pathlib import Path
import logging

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


def expand_regular_calendar(calendar):
    """Expand regular weekly schedules into active dates."""

    active_dates = set()

    for row in calendar.itertuples(index=False):

        start_date = pd.Timestamp(row.start_date).normalize()
        end_date = pd.Timestamp(row.end_date).normalize()

        if pd.isna(start_date) or pd.isna(end_date):
            raise ValueError("Missing calendar date.")

        if start_date > end_date:
            raise ValueError(
                f"Invalid date range for {row.service_id}"
            )

        operating_days = [
            getattr(row, day)
            for day in WEEKDAY_COLUMNS
        ]

        if any(pd.isna(day) for day in operating_days):
            raise ValueError(
                f"Missing weekday flag for {row.service_id}"
            )

        dates = pd.date_range(
            start=start_date,
            end=end_date,
            freq="D"
        )

        for date in dates:

            if operating_days[date.weekday()]:

                active_dates.add(
                    (str(row.service_id), date)
                )

    return active_dates


def apply_calendar_exceptions(
    active_dates,
    calendar_dates
):
    """Apply added and removed service exceptions."""

    active_dates = active_dates.copy()

    if calendar_dates.duplicated(
        subset=["service_id", "date"]
    ).any():
        raise ValueError("Duplicate calendar exceptions.")

    added = 0
    removed = 0
    unchanged = 0

    for row in calendar_dates.itertuples(index=False):

        date = pd.Timestamp(row.date).normalize()

        if pd.isna(date):
            raise ValueError("Missing exception date.")

        key = (str(row.service_id), date)

        if pd.isna(row.exception_type):
            raise ValueError("Missing exception type.")

        if row.exception_type == 1:

            if key not in active_dates:
                active_dates.add(key)
                added += 1
            else:
                unchanged += 1

        elif row.exception_type == 2:

            if key in active_dates:
                active_dates.remove(key)
                removed += 1
            else:
                unchanged += 1

        else:
            raise ValueError(
                f"Invalid exception type: "
                f"{row.exception_type}"
            )

    return active_dates, {
        "added": added,
        "removed": removed,
        "unchanged": unchanged,
    }


def build_service_dates(calendar, calendar_dates):
    """Combine regular schedules and date exceptions."""

    regular_dates = expand_regular_calendar(calendar)

    logger.info(
        "Regular service-date records: %s",
        f"{len(regular_dates):,}"
    )

    active_dates, statistics = apply_calendar_exceptions(
        regular_dates,
        calendar_dates
    )

    result = pd.DataFrame(
        sorted(active_dates),
        columns=["service_id", "service_date"]
    )

    result["service_id"] = (
        result["service_id"].astype("string")
    )

    result["service_date"] = pd.to_datetime(
        result["service_date"]
    )

    if result.duplicated(
        subset=["service_id", "service_date"]
    ).any():
        raise ValueError("Duplicate service-date records.")

    expected_rows = (
        len(regular_dates)
        + statistics["added"]
        - statistics["removed"]
    )

    if len(result) != expected_rows:
        raise ValueError("Unexpected service-date count.")

    return result, statistics


def get_active_services(service_dates, date):
    """Return service IDs operating on a selected date."""

    target_date = pd.Timestamp(date).normalize()

    active = service_dates.loc[
        service_dates["service_date"] == target_date,
        "service_id"
    ]

    return set(active)


def get_daily_trip_count(trips, service_dates, date):
    """Count scheduled trip records on a selected date."""

    active_services = get_active_services(
        service_dates,
        date
    )

    return int(
        trips["service_id"].isin(active_services).sum()
    )


def main():

    logger.info("Starting service calendar expansion...")

    calendar = pd.read_parquet(
        PROCESSED_DIR / "calendar.parquet"
    )

    calendar_dates = pd.read_parquet(
        PROCESSED_DIR / "calendar_dates.parquet"
    )

    trips = pd.read_parquet(
        PROCESSED_DIR / "trips.parquet"
    )

    service_dates, statistics = build_service_dates(
        calendar,
        calendar_dates
    )

    if service_dates.empty:
        raise ValueError("No active service dates found.")

    output_path = PROCESSED_DIR / "service_dates.parquet"
    temp_path = output_path.with_suffix(".parquet.tmp")

    try:
        service_dates.to_parquet(
            temp_path,
            engine="pyarrow",
            compression="snappy",
            index=False
        )

        temp_path.replace(output_path)

    finally:
        temp_path.unlink(missing_ok=True)

    print("\n=== CALENDAR EXCEPTION SUMMARY ===\n")

    print(f"Added dates: {statistics['added']:,}")
    print(f"Removed dates: {statistics['removed']:,}")
    print(f"Unchanged dates: {statistics['unchanged']:,}")

    print("\n=== SERVICE DATE SUMMARY ===\n")

    print(f"Total records: {len(service_dates):,}")

    print(
        "Unique active services:",
        service_dates["service_id"].nunique()
    )

    print(
        "Unique operating dates:",
        service_dates["service_date"].nunique()
    )

    print(
        "Earliest operating date:",
        service_dates["service_date"].min().date()
    )

    print(
        "Latest operating date:",
        service_dates["service_date"].max().date()
    )

    inactive_services = (
        set(trips["service_id"])
        - set(service_dates["service_id"])
    )

    print(
        "Trip service IDs without active dates:",
        len(inactive_services)
    )

    print("\n=== SAMPLE SERVICE DATES ===\n")

    print(service_dates.head(10).to_string(index=False))

    print("\n=== DAILY SCHEDULED TRIP COUNTS ===\n")

    example_dates = [
        "2026-11-27",
        "2026-11-28",
        "2026-11-29",
        "2026-11-30",
        "2026-12-01",
        "2026-12-02",
        "2026-12-03",
    ]

    for date in example_dates:

        count = get_daily_trip_count(
            trips,
            service_dates,
            date
        )

        weekday = pd.Timestamp(date).day_name()

        print(f"{date} | {weekday:10s} | {count:,} trips")

    logger.info(
        "Saved %s | Size: %.2f MiB",
        output_path.name,
        output_path.stat().st_size / (1024 * 1024)
    )

    logger.info("Service calendar expansion completed.")


if __name__ == "__main__":
    main()
