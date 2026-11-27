
# Data Sources

## 1. Wiener Linien GTFS Dataset

The primary dataset used in ViennaTransitLab is the
official GTFS timetable dataset published by the City
of Vienna and Wiener Linien.

### Source information

- Dataset: Wiener Linien – Fahrplandaten GTFS Wien
- Format: General Transit Feed Specification (GTFS)
- License: Creative Commons Attribution 4.0 (CC BY 4.0)
- Attribution: Stadt Wien – Wiener Linien
- Download date: 2026-11-27
- Compressed size: 94.80 MiB
- SHA-256: BB10AB9C2FD070FD6FA3B261B0A55370EDE88D8367975B2B7078BC52466E2541

Official dataset page:
https://www.data.gv.at/datasets/ab4a73b6-1c2d-42e1-b4d9-049e04889cf0

Direct download:
https://www.wienerlinien.at/ogd_realtime/doku/ogd/gtfs/gtfs.zip

GTFS specification:
https://gtfs.org/documentation/schedule/reference/

License:
https://creativecommons.org/licenses/by/4.0/

## 2. Dataset Structure

| File | Records | Columns |
|---|---:|---:|
| agency.txt | 2 | 6 |
| calendar.txt | 1,123 | 10 |
| calendar_dates.txt | 28,076 | 3 |
| routes.txt | 942 | 7 |
| shapes.txt | 1,219,418 | 5 |
| stops.txt | 4,348 | 5 |
| stop_times.txt | 8,965,866 | 8 |
| trips.txt | 469,823 | 7 |
| Total | 10,689,598 | |

## 3. Transport Operators

- Wiener Linien GmbH & Co KG
- Wiener Lokalbahnen GmbH

## 4. Transport Modes

| Transport mode | Route records |
|---|---:|
| Tram / Light rail | 272 |
| Subway / U-Bahn | 66 |
| Bus | 604 |
| Total | 942 |

Route records do not represent unique public-facing
transport lines. Multiple records may correspond to
different versions or variations of the same line.

## 5. Temporal Coverage

- Earliest calendar start: 2025-12-14
- Latest calendar end: 2026-12-12
- Earliest calendar exception: 2025-12-14
- Latest calendar exception: 2026-12-12

The dataset represents scheduled transportation
services rather than observed vehicle movements.

## 6. Missing Values

| Table | Column | Missing records |
|---|---|---:|
| agency | agency_fare_url | 1 |
| routes | route_color | 36 |
| routes | route_text_color | 36 |
| stops | zone_id | 6 |
| trips | block_id | 468,937 |

These fields are optional or conditionally applicable.
Records are not removed solely because these values
are missing.

## 7. Data Validation

The initial validation pipeline performs:

- Primary key uniqueness checks.
- Missing primary key checks.
- Foreign key integrity checks.
- Stop coordinate validation.
- Arrival and departure time format validation.
- Transport mode identification.
- Service date coverage inspection.

Validation results:

- Implemented validation checks: 22
- Validation violations: 0
- Stop-time records inspected: 8,965,866
- Arrivals at GTFS times of 24:00 or later: 271,635
- Automated unit tests passed: 10/10

These results apply to the downloaded dataset snapshot
and the implemented validation checks only.

## 8. Data Engineering Approach

Large GTFS tables are processed in chunks of 100,000
records to reduce memory consumption.

Identifiers are initially loaded as strings to preserve
their original representation, including leading zeros.

Raw datasets are stored locally and excluded from Git
using the project's .gitignore configuration.

## 9. Known Limitations

- The dataset contains scheduled services, not actual
  vehicle arrivals or historical delays.
- Some stops are located outside Vienna.
- Stop records may represent individual platforms
  rather than unique physical stations.
- Route records may include timetable variations.
- GTFS times can exceed 24:00 and require special
  treatment during transformation.
- Conventional rail and S-Bahn services are not
  represented in this dataset's route-type distribution.
- The timetable dataset requires periodic updates.
- The initial validator does not cover every GTFS
  specification requirement.

## 10. Reproducing the Data Pipeline

From the project root, activate the Python environment
and execute:

    python pipelines/download_gtfs.py
    python pipelines/inspect_gtfs.py
    python pipelines/validate_gtfs.py
    python -m pytest tests/ -v

Downloading the dataset again may retrieve a newer
timetable version with different records.

## 11. Attribution

Data source: Stadt Wien – Wiener Linien.

The original transportation data is published under
the Creative Commons Attribution 4.0 International
license.

ViennaTransitLab is an independent analytics project
and is not affiliated with Wiener Linien.
