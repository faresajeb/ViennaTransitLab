
import pandas as pd
import pytest

from pipelines.transform_tables import (
    convert_integer,
    convert_float,
    convert_date,
    convert_boolean,
    transform_agency,
    transform_routes,
    transform_stops,
    transform_trips,
    transform_calendar,
    transform_calendar_dates,
)


def test_convert_integer():
    values = pd.Series(["1", "2", "3"])
    result = convert_integer(values)

    assert result.tolist() == [1, 2, 3]
    assert str(result.dtype) == "Int64"


def test_convert_integer_missing():
    values = pd.Series(["1", None, "3"])
    result = convert_integer(values)

    assert pd.isna(result.iloc[1])


def test_convert_integer_invalid():
    values = pd.Series(["1", "invalid"])

    with pytest.raises(ValueError):
        convert_integer(values)


def test_convert_float():
    values = pd.Series(["48.2082", "16.3738"])
    result = convert_float(values)

    assert result.tolist() == pytest.approx(
        [48.2082, 16.3738]
    )
    assert str(result.dtype) == "Float64"


def test_convert_float_missing():
    values = pd.Series(["48.2082", None])
    result = convert_float(values)

    assert pd.isna(result.iloc[1])


def test_convert_float_invalid():
    values = pd.Series(["48.2082", "invalid"])

    with pytest.raises(ValueError):
        convert_float(values)


def test_convert_date():
    values = pd.Series(["20261127", "20261212"])
    result = convert_date(values)

    assert result.iloc[0] == pd.Timestamp("2026-11-27")
    assert result.iloc[1] == pd.Timestamp("2026-12-12")


def test_convert_date_invalid():
    values = pd.Series(["20260230"])

    with pytest.raises(ValueError):
        convert_date(values)


def test_convert_boolean():
    values = pd.Series(["0", "1", "1", "0"])
    result = convert_boolean(values)

    assert result.tolist() == [
        False, True, True, False
    ]

    assert str(result.dtype) == "boolean"


def test_convert_boolean_invalid():
    values = pd.Series(["0", "2"])

    with pytest.raises(ValueError):
        convert_boolean(values)


def test_transform_agency_preserves_ids():
    df = pd.DataFrame({
        "agency_id": ["03", "04"],
        "agency_name": ["Operator A", "Operator B"]
    })

    result = transform_agency(df)

    assert result["agency_id"].tolist() == ["03", "04"]
    assert result.equals(df)


def test_transform_routes():
    df = pd.DataFrame({
        "route_id": ["R1", "R2", "R3"],
        "route_type": ["0", "1", "3"]
    })

    result = transform_routes(df)

    assert result["route_type"].tolist() == [0, 1, 3]

    assert result["transport_type"].tolist() == [
        "Tram / Light rail",
        "Subway / U-Bahn",
        "Bus"
    ]


def test_transform_routes_unknown_type():
    df = pd.DataFrame({
        "route_id": ["R1"],
        "route_type": ["999"]
    })

    result = transform_routes(df)

    assert result["transport_type"].iloc[0] == (
        "Other / Extended type"
    )


def test_transform_stops():
    df = pd.DataFrame({
        "stop_id": ["S001"],
        "stop_lat": ["48.2082"],
        "stop_lon": ["16.3738"]
    })

    result = transform_stops(df)

    assert result["stop_id"].iloc[0] == "S001"
    assert result["stop_lat"].iloc[0] == pytest.approx(
        48.2082
    )
    assert result["stop_lon"].iloc[0] == pytest.approx(
        16.3738
    )


def test_transform_trips():
    df = pd.DataFrame({
        "trip_id": ["T001", "T002"],
        "direction_id": ["0", "1"]
    })

    result = transform_trips(df)

    assert result["direction_id"].tolist() == [0, 1]


def create_calendar():
    return pd.DataFrame({
        "service_id": ["S1"],
        "monday": ["1"],
        "tuesday": ["1"],
        "wednesday": ["1"],
        "thursday": ["1"],
        "friday": ["1"],
        "saturday": ["0"],
        "sunday": ["0"],
        "start_date": ["20260101"],
        "end_date": ["20261212"]
    })


def test_transform_calendar():
    result = transform_calendar(create_calendar())

    assert bool(result["monday"].iloc[0]) is True
    assert bool(result["saturday"].iloc[0]) is False

    assert result["start_date"].iloc[0] == (
        pd.Timestamp("2026-01-01")
    )


def test_transform_calendar_invalid_range():
    df = create_calendar()

    df["start_date"] = "20261212"
    df["end_date"] = "20260101"

    with pytest.raises(ValueError):
        transform_calendar(df)


def test_transform_calendar_dates():
    df = pd.DataFrame({
        "service_id": ["S1", "S2"],
        "date": ["20261127", "20261128"],
        "exception_type": ["1", "2"]
    })

    result = transform_calendar_dates(df)

    assert result["exception_type"].tolist() == [1, 2]

    assert result["date"].iloc[0] == (
        pd.Timestamp("2026-11-27")
    )


def test_transform_calendar_dates_invalid_exception():
    df = pd.DataFrame({
        "service_id": ["S1"],
        "date": ["20261127"],
        "exception_type": ["3"]
    })

    with pytest.raises(ValueError):
        transform_calendar_dates(df)


def test_transformation_preserves_original_dataframe():
    df = pd.DataFrame({
        "route_id": ["R1"],
        "route_type": ["3"]
    })

    original = df.copy(deep=True)

    transform_routes(df)

    pd.testing.assert_frame_equal(df, original)
