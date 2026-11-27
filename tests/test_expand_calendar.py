
import pandas as pd
import pytest

from pipelines.expand_calendar import (
    expand_regular_calendar,
    apply_calendar_exceptions,
    build_service_dates,
    get_active_services,
    get_daily_trip_count,
)


def create_calendar():
    return pd.DataFrame({
        "service_id": ["S1"],
        "monday": [True],
        "tuesday": [True],
        "wednesday": [True],
        "thursday": [True],
        "friday": [True],
        "saturday": [False],
        "sunday": [False],
        "start_date": [
            pd.Timestamp("2026-11-23")
        ],
        "end_date": [
            pd.Timestamp("2026-11-29")
        ],
    })


def create_exceptions(records=None):
    if records is None:
        records = []

    return pd.DataFrame(
        records,
        columns=[
            "service_id",
            "date",
            "exception_type",
        ]
    )


def test_regular_weekday_service():
    result = expand_regular_calendar(
        create_calendar()
    )

    assert len(result) == 5


def test_weekend_excluded():
    result = expand_regular_calendar(
        create_calendar()
    )

    assert (
        "S1", pd.Timestamp("2026-11-28")
    ) not in result

    assert (
        "S1", pd.Timestamp("2026-11-29")
    ) not in result


def test_start_date_included():
    result = expand_regular_calendar(
        create_calendar()
    )

    assert (
        "S1", pd.Timestamp("2026-11-23")
    ) in result


def test_end_date_included():
    calendar = create_calendar()
    calendar.loc[0, "sunday"] = True

    result = expand_regular_calendar(calendar)

    assert (
        "S1", pd.Timestamp("2026-11-29")
    ) in result


def test_invalid_date_range():
    calendar = create_calendar()

    calendar.loc[0, "start_date"] = pd.Timestamp(
        "2026-12-01"
    )

    with pytest.raises(ValueError):
        expand_regular_calendar(calendar)


def test_missing_weekday_flag():
    calendar = create_calendar()

    calendar["monday"] = pd.Series(
        [pd.NA], dtype="boolean"
    )

    with pytest.raises(ValueError):
        expand_regular_calendar(calendar)


def test_added_service():
    regular = expand_regular_calendar(
        create_calendar()
    )

    exceptions = create_exceptions([
        ("S1", pd.Timestamp("2026-11-28"), 1)
    ])

    result, stats = apply_calendar_exceptions(
        regular, exceptions
    )

    assert len(result) == 6
    assert stats["added"] == 1

    assert (
        "S1", pd.Timestamp("2026-11-28")
    ) in result


def test_removed_service():
    regular = expand_regular_calendar(
        create_calendar()
    )

    exceptions = create_exceptions([
        ("S1", pd.Timestamp("2026-11-23"), 2)
    ])

    result, stats = apply_calendar_exceptions(
        regular, exceptions
    )

    assert len(result) == 4
    assert stats["removed"] == 1

    assert (
        "S1", pd.Timestamp("2026-11-23")
    ) not in result


def test_add_existing_service():
    regular = expand_regular_calendar(
        create_calendar()
    )

    exceptions = create_exceptions([
        ("S1", pd.Timestamp("2026-11-23"), 1)
    ])

    result, stats = apply_calendar_exceptions(
        regular, exceptions
    )

    assert len(result) == 5
    assert stats["unchanged"] == 1


def test_remove_nonexistent_service():
    regular = expand_regular_calendar(
        create_calendar()
    )

    exceptions = create_exceptions([
        ("S1", pd.Timestamp("2026-11-29"), 2)
    ])

    result, stats = apply_calendar_exceptions(
        regular, exceptions
    )

    assert len(result) == 5
    assert stats["unchanged"] == 1


def test_exception_only_service():
    exceptions = create_exceptions([
        ("S2", pd.Timestamp("2026-11-28"), 1)
    ])

    result, stats = apply_calendar_exceptions(
        set(), exceptions
    )

    assert (
        "S2", pd.Timestamp("2026-11-28")
    ) in result

    assert stats["added"] == 1


def test_invalid_exception_type():
    exceptions = create_exceptions([
        ("S1", pd.Timestamp("2026-11-23"), 3)
    ])

    with pytest.raises(ValueError):
        apply_calendar_exceptions(
            set(), exceptions
        )


def test_duplicate_exceptions():
    exceptions = create_exceptions([
        ("S1", pd.Timestamp("2026-11-23"), 1),
        ("S1", pd.Timestamp("2026-11-23"), 2),
    ])

    with pytest.raises(ValueError):
        apply_calendar_exceptions(
            set(), exceptions
        )


def test_combined_calendar():
    exceptions = create_exceptions([
        ("S1", pd.Timestamp("2026-11-23"), 2),
        ("S1", pd.Timestamp("2026-11-28"), 1),
    ])

    result, stats = build_service_dates(
        create_calendar(), exceptions
    )

    assert len(result) == 5
    assert stats["added"] == 1
    assert stats["removed"] == 1

    assert not result.duplicated(
        ["service_id", "service_date"]
    ).any()


def test_get_active_services():
    service_dates, _ = build_service_dates(
        create_calendar(),
        create_exceptions()
    )

    result = get_active_services(
        service_dates, "2026-11-23"
    )

    assert result == {"S1"}


def test_no_active_services():
    service_dates, _ = build_service_dates(
        create_calendar(),
        create_exceptions()
    )

    result = get_active_services(
        service_dates, "2026-11-29"
    )

    assert result == set()


def test_daily_trip_count():
    service_dates, _ = build_service_dates(
        create_calendar(),
        create_exceptions()
    )

    trips = pd.DataFrame({
        "trip_id": ["T1", "T2", "T3"],
        "service_id": ["S1", "S1", "S2"],
    })

    count = get_daily_trip_count(
        trips,
        service_dates,
        "2026-11-23"
    )

    assert count == 2


def test_original_calendar_preserved():
    calendar = create_calendar()
    original = calendar.copy(deep=True)

    build_service_dates(
        calendar,
        create_exceptions()
    )

    pd.testing.assert_frame_equal(
        calendar, original
    )


def test_original_active_dates_preserved():
    regular = expand_regular_calendar(
        create_calendar()
    )

    original = regular.copy()

    exceptions = create_exceptions([
        ("S1", pd.Timestamp("2026-11-23"), 2)
    ])

    apply_calendar_exceptions(
        regular, exceptions
    )

    assert regular == original


def test_all_service_dates_removed():
    calendar = create_calendar()

    exceptions = create_exceptions([
        ("S1", date, 2)
        for date in pd.date_range(
            "2026-11-23",
            "2026-11-27"
        )
    ])

    result, stats = build_service_dates(
        calendar, exceptions
    )

    assert result.empty
    assert stats["removed"] == 5
