
import pandas as pd
import pytest

from pipelines.transform_gtfs import (
    gtfs_time_to_seconds,
    seconds_to_gtfs_time,
    convert_time_column,
)


@pytest.mark.parametrize(
    "value, expected",
    [
        ("00:00:00", 0),
        ("08:30:00", 30600),
        ("12:00:00", 43200),
        ("23:59:59", 86399),
        ("24:00:00", 86400),
        ("24:38:00", 88680),
        ("25:01:00", 90060),
        ("26:30:00", 95400),
    ]
)
def test_gtfs_time_to_seconds(value, expected):
    assert gtfs_time_to_seconds(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        "",
        "invalid",
        "12:60:00",
        "12:30:60",
        "-1:30:00",
        "12:30",
        None,
    ]
)
def test_invalid_gtfs_time(value):
    with pytest.raises(ValueError):
        gtfs_time_to_seconds(value)


@pytest.mark.parametrize(
    "value",
    [
        "00:00:00",
        "08:30:00",
        "23:59:59",
        "24:38:00",
        "25:01:00",
    ]
)
def test_time_round_trip(value):
    seconds = gtfs_time_to_seconds(value)

    assert seconds_to_gtfs_time(seconds) == value


@pytest.mark.parametrize(
    "value",
    [-1, -3600, 3.5, True, None]
)
def test_invalid_seconds(value):
    with pytest.raises(ValueError):
        seconds_to_gtfs_time(value)


def test_vectorized_conversion():
    values = pd.Series(
        ["00:00:00", "12:00:00", "25:01:00"]
    )

    result = convert_time_column(values)

    assert result.tolist() == [0, 43200, 90060]


def test_vectorized_invalid_conversion():
    values = pd.Series(
        ["12:00:00", "invalid"]
    )

    with pytest.raises(ValueError):
        convert_time_column(values)


def test_vectorized_missing_value():
    values = pd.Series(
        ["12:00:00", None]
    )

    with pytest.raises(ValueError):
        convert_time_column(values)
