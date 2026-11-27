
# Data Transformation Pipeline

## 1. Overview

ViennaTransitLab implements a modular data transformation
pipeline for the official Wiener Linien GTFS dataset.

The pipeline converts raw transportation data into typed,
compressed and analysis-ready Parquet datasets while
preserving the original source files.

## 2. Architecture

Raw GTFS files
    |
    v
Data validation
    |
    v
Small-table transformation
    |
    v
Large-table transformation
    |
    v
Service calendar expansion
    |
    v
Processed Parquet datasets
    |
    v
PostgreSQL / PostGIS (planned)

## 3. Pipeline Components

| Module | Responsibility |
|---|---|
| transform_gtfs.py | GTFS time conversion utilities |
| transform_tables.py | Small-table data transformation |
| transform_large_tables.py | Chunk-based large-table processing |
| expand_calendar.py | Service calendar expansion |
| inspect_inactive_services.py | Inactive service diagnostics |
| run_transformation.py | Pipeline orchestration |

## 4. Transformation Strategy

- Preserve identifiers as strings.
- Convert numeric values into appropriate numeric types.
- Convert operating-day flags into booleans.
- Convert calendar dates into datetime values.
- Preserve optional missing values.
- Preserve original GTFS arrival and departure strings.
- Generate arrival_seconds and departure_seconds.
- Generate readable transport mode descriptions.
- Preserve source-table row counts.

## 5. Large-Scale Data Processing

The two largest GTFS tables are processed in chunks
of 100,000 records.

Apache Parquet is used for columnar storage with
Snappy compression.

Temporary SQLite databases enforce composite key
uniqueness across chunks.

Composite keys:

- stop_times: trip_id, stop_sequence
- shapes: shape_id, shape_pt_sequence

Temporary output files are used during large-table
processing to avoid publishing incomplete results.

## 6. Service Calendar Expansion

Regular operating dates are expanded from calendar.txt
and adjusted using calendar_dates.txt.

Exception type 1 adds a service date.
Exception type 2 removes a service date.

Results:

- Regular service-date records: 63,585
- Added service dates: 848
- Removed service dates: 27,228
- Final service-date records: 37,205
- Unique active services: 1,115
- Unique operating dates: 364

Eight service IDs have no remaining active dates.
Their regular operating dates were entirely removed
by calendar exceptions.

The 2,039 associated trip records are preserved,
but excluded from date-specific analytics through
service-date filtering.

## 7. Processed Dataset Structure

| Table | Rows | Columns | Size (MiB) |
|---|---:|---:|---:|
| agency | 2 | 6 | 0.0041 |
| calendar | 1,123 | 10 | 0.0153 |
| calendar_dates | 28,076 | 3 | 0.0258 |
| routes | 942 | 8 | 0.0192 |
| shapes | 1,219,418 | 5 | 6.1674 |
| stops | 4,348 | 5 | 0.1283 |
| stop_times | 8,965,866 | 10 | 62.7144 |
| trips | 469,823 | 7 | 2.8155 |
| service_dates | 37,205 | 2 | 0.0272 |
| Total | 10,726,803 | | 71.92 |

## 8. Storage Performance

Benchmark date: 2026-11-27

| Metric | Result |
|---|---:|
| Raw dataset size | 864.32 MiB |
| Processed dataset size | 71.92 MiB |
| Storage saved | 792.40 MiB |
| Storage reduction | 91.68% |
| Output tables | 9 |

The storage comparison excludes the downloaded ZIP
archive and temporary validation files.

## 9. Execution Performance

Measured on the development machine using Python 3.12.

| Pipeline stage | Duration |
|---|---:|
| Small-table transformation | 1.75 seconds |
| Large-table transformation | 157.39 seconds |
| Calendar expansion | 1.58 seconds |
| Total pipeline duration | 160.83 seconds |

These results are specific to the dataset snapshot
and development environment. Performance may vary
across machines.

## 10. Sample Analytics

Scheduled trip records for selected service dates:

| Date | Day | Scheduled trips |
|---|---|---:|
| 2026-11-27 | Friday | 35,498 |
| 2026-11-28 | Saturday | 25,944 |
| 2026-11-29 | Sunday | 22,613 |
| 2026-11-30 | Monday | 35,501 |
| 2026-12-01 | Tuesday | 35,501 |
| 2026-12-02 | Wednesday | 35,501 |
| 2026-12-03 | Thursday | 35,501 |

These figures represent scheduled journeys,
not actual vehicle movements or passenger demand.

## 11. Automated Testing

The test suite covers:

- Primary and foreign key validation.
- Geographic coordinate validation.
- GTFS time conversion.
- Numeric and date transformations.
- Calendar expansion and exceptions.
- Composite key duplicate detection.
- Cross-chunk data validation.
- Parquet serialization.
- Temporary file cleanup.
- Pipeline orchestration and failure handling.

## 12. Running the Pipeline

From the repository root:

    python pipelines/download_gtfs.py
    python pipelines/validate_gtfs.py
    python -m pipelines.run_transformation
    python -m pytest tests/ -q

Raw and processed datasets remain local and are
excluded from version control.

## 13. Known Limitations

- The pipeline uses a specific GTFS dataset snapshot.
- Benchmark results depend on hardware.
- The complete transformation is not transactional
  across every output table.
- Full GTFS specification compliance is not verified.
- Sequential stop-time ordering and distance
  monotonicity require further validation.
- Actual delays and passenger demand are unavailable
  from the current timetable dataset.

## 14. Next Steps

- PostgreSQL database schema design.
- PostGIS spatial database integration.
- Efficient bulk data loading.
- Database indexes and query optimization.
- Statistical and geospatial analytics.
- Integration with the FastAPI backend.
