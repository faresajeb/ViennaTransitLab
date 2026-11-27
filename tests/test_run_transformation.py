
import pandas as pd
import pytest

from pipelines import run_transformation as pipeline


def create_input_files(directory):

    directory.mkdir(parents=True, exist_ok=True)

    for table in pipeline.SOURCE_TABLES:

        path = directory / f"{table}.txt"

        path.write_text(
            "id\n1\n",
            encoding="utf-8"
        )


def create_output_files(directory):

    directory.mkdir(parents=True, exist_ok=True)

    for table in pipeline.OUTPUT_TABLES:

        df = pd.DataFrame({
            "id": [1, 2, 3]
        })

        df.to_parquet(
            directory / f"{table}.parquet",
            index=False
        )


def test_validate_inputs_success(tmp_path, monkeypatch):

    create_input_files(tmp_path)

    monkeypatch.setattr(
        pipeline, "GTFS_DIR", tmp_path
    )

    pipeline.validate_inputs()


def test_validate_inputs_missing_file(
    tmp_path, monkeypatch
):

    create_input_files(tmp_path)

    (tmp_path / "stops.txt").unlink()

    monkeypatch.setattr(
        pipeline, "GTFS_DIR", tmp_path
    )

    with pytest.raises(FileNotFoundError):
        pipeline.validate_inputs()


def test_run_stage_executes_function():

    calls = []

    def example_stage():
        calls.append("executed")

    duration = pipeline.run_stage(
        "Example stage",
        example_stage
    )

    assert calls == ["executed"]
    assert duration >= 0


def test_run_stage_propagates_exception():

    def failing_stage():
        raise ValueError("Stage failed")

    with pytest.raises(ValueError):
        pipeline.run_stage(
            "Failing stage",
            failing_stage
        )


def test_verify_outputs_success(
    tmp_path, monkeypatch
):

    create_output_files(tmp_path)

    monkeypatch.setattr(
        pipeline, "PROCESSED_DIR", tmp_path
    )

    results = pipeline.verify_outputs()

    assert len(results) == 9

    assert all(
        result["rows"] == 3
        for result in results
    )

    assert all(
        result["bytes"] > 0
        for result in results
    )


def test_verify_outputs_missing_file(
    tmp_path, monkeypatch
):

    create_output_files(tmp_path)

    (tmp_path / "stops.parquet").unlink()

    monkeypatch.setattr(
        pipeline, "PROCESSED_DIR", tmp_path
    )

    with pytest.raises(FileNotFoundError):
        pipeline.verify_outputs()


def test_verify_outputs_empty_table(
    tmp_path, monkeypatch
):

    create_output_files(tmp_path)

    empty = pd.DataFrame({
        "id": pd.Series(dtype="int64")
    })

    empty.to_parquet(
        tmp_path / "stops.parquet",
        index=False
    )

    monkeypatch.setattr(
        pipeline, "PROCESSED_DIR", tmp_path
    )

    with pytest.raises(ValueError):
        pipeline.verify_outputs()


def test_pipeline_execution_order(monkeypatch):

    calls = []

    monkeypatch.setattr(
        pipeline,
        "validate_inputs",
        lambda: calls.append("validate")
    )

    monkeypatch.setattr(
        pipeline.transform_tables,
        "main",
        lambda: calls.append("small_tables")
    )

    monkeypatch.setattr(
        pipeline.transform_large_tables,
        "main",
        lambda: calls.append("large_tables")
    )

    monkeypatch.setattr(
        pipeline.expand_calendar,
        "main",
        lambda: calls.append("calendar")
    )

    def verify():
        calls.append("verify")
        return []

    monkeypatch.setattr(
        pipeline,
        "verify_outputs",
        verify
    )

    monkeypatch.setattr(
        pipeline,
        "print_summary",
        lambda *args: calls.append("summary")
    )

    pipeline.main()

    assert calls == [
        "validate",
        "small_tables",
        "large_tables",
        "calendar",
        "verify",
        "summary"
    ]


def test_pipeline_stops_on_failure(monkeypatch):

    calls = []

    monkeypatch.setattr(
        pipeline,
        "validate_inputs",
        lambda: calls.append("validate")
    )

    def failing_stage():
        calls.append("small_tables")
        raise ValueError("Transformation failed")

    monkeypatch.setattr(
        pipeline.transform_tables,
        "main",
        failing_stage
    )

    monkeypatch.setattr(
        pipeline.transform_large_tables,
        "main",
        lambda: calls.append("large_tables")
    )

    monkeypatch.setattr(
        pipeline.expand_calendar,
        "main",
        lambda: calls.append("calendar")
    )

    with pytest.raises(ValueError):
        pipeline.main()

    assert calls == [
        "validate",
        "small_tables"
    ]
