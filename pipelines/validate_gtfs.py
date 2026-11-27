
from pathlib import Path
import logging

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GTFS_DIR = PROJECT_ROOT / "data" / "raw" / "gtfs"

CHUNK_SIZE = 100_000

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


def load_table(filename):
    """Load a GTFS table while preserving identifiers."""

    return pd.read_csv(
        GTFS_DIR / filename,
        dtype=str,
        encoding="utf-8-sig",
        keep_default_na=False
    )


def report_check(description, errors):
    """Display the result of a validation check."""

    status = "PASS" if errors == 0 else "FAIL"

    print(
        f"[{status}] {description}: "
        f"{errors:,} invalid records"
    )

    return errors


def check_primary_key(df, columns, table_name):
    """Check primary keys for duplicates and empty values."""

    duplicates = df.duplicated(subset=columns).sum()

    missing = (
        df[columns].apply(
            lambda col: col.str.strip().eq("")
        ).any(axis=1).sum()
    )

    errors = report_check(
        f"{table_name} duplicate keys",
        duplicates
    )

    errors += report_check(
        f"{table_name} missing keys",
        missing
    )

    return errors


def check_foreign_key(values, valid_ids, description):
    """Check whether identifiers exist in a referenced table."""

    invalid = (~values.isin(valid_ids)).sum()

    return report_check(description, invalid)


def validate_coordinates(stops):
    """Validate stop latitude and longitude."""

    latitudes = pd.to_numeric(
        stops["stop_lat"], errors="coerce"
    )

    longitudes = pd.to_numeric(
        stops["stop_lon"], errors="coerce"
    )

    invalid_lat = (~latitudes.between(-90, 90)).sum()
    invalid_lon = (~longitudes.between(-180, 180)).sum()

    errors = report_check(
        "Invalid stop latitudes", invalid_lat
    )

    errors += report_check(
        "Invalid stop longitudes", invalid_lon
    )

    return errors


def validate_stop_times(trip_ids, stop_ids):
    """Validate large stop-time table using chunks."""

    logger.info("Validating stop_times.txt...")

    total_rows = 0
    invalid_trips = 0
    invalid_stops = 0
    invalid_arrivals = 0
    invalid_departures = 0
    overnight_arrivals = 0

    time_pattern = r"\d{1,}:[0-5]\d:[0-5]\d"

    for chunk in pd.read_csv(
        GTFS_DIR / "stop_times.txt",
        chunksize=CHUNK_SIZE,
        dtype=str,
        encoding="utf-8-sig",
        keep_default_na=False
    ):
        total_rows += len(chunk)

        invalid_trips += (
            ~chunk["trip_id"].isin(trip_ids)
        ).sum()

        invalid_stops += (
            ~chunk["stop_id"].isin(stop_ids)
        ).sum()

        invalid_arrivals += (
            ~chunk["arrival_time"].str.fullmatch(time_pattern)
        ).sum()

        invalid_departures += (
            ~chunk["departure_time"].str.fullmatch(time_pattern)
        ).sum()

        hours = pd.to_numeric(
            chunk["arrival_time"].str.split(":").str[0],
            errors="coerce"
        )

        overnight_arrivals += (hours >= 24).sum()

        print(
            f"\rProcessed {total_rows:,} stop-time records",
            end="",
            flush=True
        )

    print("\n")

    errors = report_check(
        "Stop times referencing unknown trips",
        invalid_trips
    )

    errors += report_check(
        "Stop times referencing unknown stops",
        invalid_stops
    )

    errors += report_check(
        "Invalid arrival time formats",
        invalid_arrivals
    )

    errors += report_check(
        "Invalid departure time formats",
        invalid_departures
    )

    print(f"\nTotal stop-time records: {total_rows:,}")
    print(f"Overnight arrivals: {overnight_arrivals:,}")

    return errors


def main():
    logger.info("Starting GTFS validation...")

    agency = load_table("agency.txt")
    calendar = load_table("calendar.txt")
    calendar_dates = load_table("calendar_dates.txt")
    routes = load_table("routes.txt")
    stops = load_table("stops.txt")
    trips = load_table("trips.txt")

    shape_ids = set()

    for chunk in pd.read_csv(
        GTFS_DIR / "shapes.txt",
        usecols=["shape_id"],
        dtype=str,
        chunksize=CHUNK_SIZE,
        keep_default_na=False,
        encoding="utf-8-sig"
    ):
        shape_ids.update(chunk["shape_id"])

    errors = 0

    print("\n=== PRIMARY KEY VALIDATION ===")

    errors += check_primary_key(
        agency, ["agency_id"], "agency"
    )

    errors += check_primary_key(
        calendar, ["service_id"], "calendar"
    )

    errors += check_primary_key(
        calendar_dates,
        ["service_id", "date"],
        "calendar_dates"
    )

    errors += check_primary_key(
        routes, ["route_id"], "routes"
    )

    errors += check_primary_key(
        stops, ["stop_id"], "stops"
    )

    errors += check_primary_key(
        trips, ["trip_id"], "trips"
    )

    print("\n=== FOREIGN KEY VALIDATION ===")

    service_ids = (
        set(calendar["service_id"])
        | set(calendar_dates["service_id"])
    )

    errors += check_foreign_key(
        routes["agency_id"],
        set(agency["agency_id"]),
        "Routes referencing unknown agencies"
    )

    errors += check_foreign_key(
        trips["route_id"],
        set(routes["route_id"]),
        "Trips referencing unknown routes"
    )

    errors += check_foreign_key(
        trips["service_id"],
        service_ids,
        "Trips referencing unknown services"
    )

    errors += check_foreign_key(
        trips.loc[trips["shape_id"] != "", "shape_id"],
        shape_ids,
        "Trips referencing unknown shapes"
    )

    print("\n=== GEOGRAPHIC VALIDATION ===")

    errors += validate_coordinates(stops)

    print("\n=== STOP TIMES VALIDATION ===")

    errors += validate_stop_times(
        set(trips["trip_id"]),
        set(stops["stop_id"])
    )

    print("\n=== TRANSPORT TYPE DISTRIBUTION ===")

    route_types = {
        "0": "Tram / Light rail",
        "1": "Subway / U-Bahn",
        "2": "Rail",
        "3": "Bus",
        "4": "Ferry",
        "5": "Cable tram",
        "6": "Aerial lift",
        "7": "Funicular",
        "11": "Trolleybus",
        "12": "Monorail"
    }

    routes["transport_type"] = (
        routes["route_type"]
        .map(route_types)
        .fillna("Other / Extended type")
    )

    print(
        routes.groupby(
            ["route_type", "transport_type"]
        ).size().to_string()
    )

    print("\n=== SERVICE DATE COVERAGE ===")

    print(
        "Earliest calendar start:",
        calendar["start_date"].min()
    )

    print(
        "Latest calendar end:",
        calendar["end_date"].max()
    )

    print(
        "Earliest exception date:",
        calendar_dates["date"].min()
    )

    print(
        "Latest exception date:",
        calendar_dates["date"].max()
    )

    print("\n=== VALIDATION SUMMARY ===")

    print(f"Total validation violations: {errors:,}")

    if errors == 0:
       logger.info("All implemented validation checks passed.")
    else:
       logger.error("Validation issues require investigation.")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
