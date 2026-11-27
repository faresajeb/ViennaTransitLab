
import pandas as pd

from pipelines.validate_gtfs import (
    check_primary_key,
    check_foreign_key,
    validate_coordinates,
)


def test_primary_key_valid():
    df = pd.DataFrame({
        "stop_id": ["S001", "S002", "S003"]
    })

    assert check_primary_key(
        df, ["stop_id"], "stops"
    ) == 0


def test_primary_key_duplicates():
    df = pd.DataFrame({
        "stop_id": ["S001", "S001", "S002"]
    })

    assert check_primary_key(
        df, ["stop_id"], "stops"
    ) == 1


def test_primary_key_missing():
    df = pd.DataFrame({
        "stop_id": ["S001", "", "S003"]
    })

    assert check_primary_key(
        df, ["stop_id"], "stops"
    ) == 1


def test_composite_primary_key():
    df = pd.DataFrame({
        "service_id": ["T1", "T1", "T2"],
        "date": ["20261127", "20261128", "20261127"]
    })

    assert check_primary_key(
        df,
        ["service_id", "date"],
        "calendar_dates"
    ) == 0


def test_foreign_key_valid():
    values = pd.Series(["R001", "R002"])
    valid_ids = {"R001", "R002", "R003"}

    assert check_foreign_key(
        values,
        valid_ids,
        "Route references"
    ) == 0


def test_foreign_key_invalid():
    values = pd.Series(["R001", "R999"])
    valid_ids = {"R001", "R002"}

    assert check_foreign_key(
        values,
        valid_ids,
        "Route references"
    ) == 1


def test_valid_coordinates():
    stops = pd.DataFrame({
        "stop_lat": ["48.2082", "48.2200"],
        "stop_lon": ["16.3738", "16.4000"]
    })

    assert validate_coordinates(stops) == 0


def test_invalid_latitude():
    stops = pd.DataFrame({
        "stop_lat": ["95.0"],
        "stop_lon": ["16.3738"]
    })

    assert validate_coordinates(stops) == 1


def test_invalid_longitude():
    stops = pd.DataFrame({
        "stop_lat": ["48.2082"],
        "stop_lon": ["200.0"]
    })

    assert validate_coordinates(stops) == 1


def test_non_numeric_coordinates():
    stops = pd.DataFrame({
        "stop_lat": ["invalid"],
        "stop_lon": ["invalid"]
    })

    assert validate_coordinates(stops) == 2
