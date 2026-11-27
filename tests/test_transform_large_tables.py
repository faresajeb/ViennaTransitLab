
import sqlite3

import pandas as pd
import pytest
import pyarrow.parquet as pq

from pipelines import transform_large_tables as large

from pipelines.transform_large_tables import (
    transform_stop_times,
    transform_shapes,
    validate_required_columns,
    validate_nonnegative,
    validate_composite_keys,
)


def create_stop_times():
    return pd.DataFrame({
        "trip_id": ["T1", "T1"],
        "arrival_time": ["23:55:00", "24:10:00"],
        "departure_time": ["23:56:00", "24:11:00"],
        "stop_id": ["S1", "S2"],
        "stop_sequence": ["1", "2"],
        "pickup_type": ["0", "0"],
        "drop_off_type": ["0", "0"],
        "shape_dist_traveled": ["0.0", "1500.5"]
    })


def create_shapes():
    return pd.DataFrame({
        "shape_id": ["SH1", "SH1"],
        "shape_pt_lat": ["48.2082", "48.2100"],
        "shape_pt_lon": ["16.3738", "16.3800"],
        "shape_pt_sequence": ["1", "2"],
        "shape_dist_traveled": ["0.0", "1500.5"]
    })


@pytest.fixture
def connection():
    db = sqlite3.connect(":memory:")

    db.execute(
        """
        CREATE TABLE seen_keys (
            identifier TEXT NOT NULL,
            sequence INTEGER NOT NULL,
            PRIMARY KEY (identifier, sequence)
        ) WITHOUT ROWID
        """
    )

    yield db

    db.close()


def test_transform_stop_times():
    result = transform_stop_times(create_stop_times())

    assert len(result) == 2

    assert result["arrival_seconds"].tolist() == [
        86100, 87000
    ]

    assert result["departure_seconds"].tolist() == [
        86160, 87060
    ]

    assert result["stop_sequence"].tolist() == [1, 2]

    assert str(result["stop_sequence"].dtype) == "Int64"


def test_original_time_preserved():
    df = create_stop_times()
    result = transform_stop_times(df)

    assert result["arrival_time"].tolist() == (
        df["arrival_time"].tolist()
    )


def test_departure_before_arrival():
    df = create_stop_times()
    df.loc[0, "departure_time"] = "23:50:00"

    with pytest.raises(ValueError):
        transform_stop_times(df)


def test_invalid_arrival_time():
    df = create_stop_times()
    df.loc[0, "arrival_time"] = "25:70:00"

    with pytest.raises(ValueError):
        transform_stop_times(df)


def test_negative_stop_sequence():
    df = create_stop_times()
    df.loc[0, "stop_sequence"] = "-1"

    with pytest.raises(ValueError):
        transform_stop_times(df)


def test_invalid_pickup_type():
    df = create_stop_times()
    df.loc[0, "pickup_type"] = "9"

    with pytest.raises(ValueError):
        transform_stop_times(df)


def test_invalid_drop_off_type():
    df = create_stop_times()
    df.loc[0, "drop_off_type"] = "9"

    with pytest.raises(ValueError):
        transform_stop_times(df)


def test_negative_stop_distance():
    df = create_stop_times()
    df.loc[0, "shape_dist_traveled"] = "-10"

    with pytest.raises(ValueError):
        transform_stop_times(df)


def test_transform_shapes():
    result = transform_shapes(create_shapes())

    assert len(result) == 2

    assert result["shape_pt_lat"].tolist() == (
        pytest.approx([48.2082, 48.2100])
    )

    assert result["shape_pt_sequence"].tolist() == [
        1, 2
    ]


def test_invalid_shape_latitude():
    df = create_shapes()
    df.loc[0, "shape_pt_lat"] = "95"

    with pytest.raises(ValueError):
        transform_shapes(df)


def test_invalid_shape_longitude():
    df = create_shapes()
    df.loc[0, "shape_pt_lon"] = "190"

    with pytest.raises(ValueError):
        transform_shapes(df)


def test_negative_shape_sequence():
    df = create_shapes()
    df.loc[0, "shape_pt_sequence"] = "-1"

    with pytest.raises(ValueError):
        transform_shapes(df)


def test_negative_shape_distance():
    df = create_shapes()
    df.loc[0, "shape_dist_traveled"] = "-10"

    with pytest.raises(ValueError):
        transform_shapes(df)


def test_missing_required_column_value():
    df = pd.DataFrame({
        "trip_id": ["T1", None]
    })

    with pytest.raises(ValueError):
        validate_required_columns(df, ["trip_id"])


def test_empty_required_column_value():
    df = pd.DataFrame({
        "trip_id": ["T1", ""]
    })

    with pytest.raises(ValueError):
        validate_required_columns(df, ["trip_id"])


def test_nonnegative_validation():
    values = pd.Series([0, 1, 2])

    validate_nonnegative(values, "sequence")


def test_negative_validation():
    values = pd.Series([0, -1, 2])

    with pytest.raises(ValueError):
        validate_nonnegative(values, "sequence")


def test_valid_composite_keys(connection):
    df = pd.DataFrame({
        "trip_id": ["T1", "T1", "T2"],
        "stop_sequence": [1, 2, 1]
    })

    validate_composite_keys(
        connection,
        df,
        ["trip_id", "stop_sequence"]
    )

    count = connection.execute(
        "SELECT COUNT(*) FROM seen_keys"
    ).fetchone()[0]

    assert count == 3


def test_duplicate_keys_within_chunk(connection):
    df = pd.DataFrame({
        "trip_id": ["T1", "T1"],
        "stop_sequence": [1, 1]
    })

    with pytest.raises(ValueError):
        validate_composite_keys(
            connection,
            df,
            ["trip_id", "stop_sequence"]
        )


def test_duplicate_keys_across_chunks(connection):
    first_chunk = pd.DataFrame({
        "trip_id": ["T1", "T1"],
        "stop_sequence": [1, 2]
    })

    second_chunk = pd.DataFrame({
        "trip_id": ["T2", "T1"],
        "stop_sequence": [1, 2]
    })

    validate_composite_keys(
        connection,
        first_chunk,
        ["trip_id", "stop_sequence"]
    )

    with pytest.raises(ValueError):
        validate_composite_keys(
            connection,
            second_chunk,
            ["trip_id", "stop_sequence"]
        )


def test_original_dataframe_preserved():
    df = create_stop_times()
    original = df.copy(deep=True)

    transform_stop_times(df)

    pd.testing.assert_frame_equal(df, original)


def test_parquet_pipeline(tmp_path, monkeypatch):
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"

    raw_dir.mkdir()

    create_stop_times().to_csv(
        raw_dir / "stop_times.txt",
        index=False
    )

    monkeypatch.setattr(large, "GTFS_DIR", raw_dir)
    monkeypatch.setattr(
        large, "PROCESSED_DIR", processed_dir
    )
    monkeypatch.setattr(large, "CHUNK_SIZE", 1)

    result = large.process_large_table(
        "stop_times",
        transform_stop_times,
        ["trip_id", "stop_sequence"]
    )

    output = processed_dir / "stop_times.parquet"

    assert output.exists()
    assert result["rows"] == 2
    assert result["chunks"] == 2
    assert pq.read_metadata(output).num_rows == 2

    restored = pd.read_parquet(output)

    assert restored["arrival_seconds"].tolist() == [
        86100, 87000
    ]

    assert not list(processed_dir.glob("*.tmp"))


def test_pipeline_cleanup_on_failure(
    tmp_path, monkeypatch
):
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"

    raw_dir.mkdir()

    df = create_stop_times()
    df.loc[1, "stop_sequence"] = "1"

    df.to_csv(
        raw_dir / "stop_times.txt",
        index=False
    )

    monkeypatch.setattr(large, "GTFS_DIR", raw_dir)
    monkeypatch.setattr(
        large, "PROCESSED_DIR", processed_dir
    )
    monkeypatch.setattr(large, "CHUNK_SIZE", 1)

    with pytest.raises(ValueError):
        large.process_large_table(
            "stop_times",
            transform_stop_times,
            ["trip_id", "stop_sequence"]
        )

    assert not (
        processed_dir / "stop_times.parquet"
    ).exists()

    assert not list(processed_dir.iterdir())
