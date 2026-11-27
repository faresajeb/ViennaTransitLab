
from pathlib import Path

import pandas as pd

from pipelines.expand_calendar import expand_regular_calendar


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def main():
    calendar = pd.read_parquet(
        PROCESSED_DIR / "calendar.parquet"
    )

    calendar_dates = pd.read_parquet(
        PROCESSED_DIR / "calendar_dates.parquet"
    )

    trips = pd.read_parquet(
        PROCESSED_DIR / "trips.parquet"
    )

    service_dates = pd.read_parquet(
        PROCESSED_DIR / "service_dates.parquet"
    )

    inactive_ids = sorted(
        set(trips["service_id"])
        - set(service_dates["service_id"])
    )

    print("\n=== INACTIVE SERVICE INVESTIGATION ===\n")

    print(f"Inactive service IDs: {len(inactive_ids)}")

    results = []

    for service_id in inactive_ids:

        regular = calendar.loc[
            calendar["service_id"] == service_id
        ]

        exceptions = calendar_dates.loc[
            calendar_dates["service_id"] == service_id
        ]

        affected_trips = trips.loc[
            trips["service_id"] == service_id
        ]

        regular_dates = expand_regular_calendar(
            regular
        )

        added = (
            exceptions["exception_type"] == 1
        ).sum()

        removed = (
            exceptions["exception_type"] == 2
        ).sum()

        results.append({
            "service_id": service_id,
            "calendar_records": len(regular),
            "regular_dates": len(regular_dates),
            "added_dates": int(added),
            "removed_dates": int(removed),
            "affected_trips": len(affected_trips),
        })

    if not results:
        print("No inactive services found.")
        return

    summary = pd.DataFrame(results)

    print(summary.to_string(index=False))

    print(
        "\nTotal affected trip records:",
        f"{summary['affected_trips'].sum():,}"
    )

    print("\n=== INACTIVE SERVICE CALENDAR DETAILS ===\n")

    print(
        calendar.loc[
            calendar["service_id"].isin(inactive_ids)
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
