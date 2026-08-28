import pytest

from manas.calibration import CalibrationRecord, run_benchmarks


def test_calibration_record_exposes_error_without_claiming_accuracy():
    record = CalibrationRecord(
        scenario_id="future-study",
        metric="trial_rate",
        observed_result=.2,
        predicted_result=.35,
        source="future external study",
    )
    assert record.error == pytest.approx(.15)


def test_behavior_benchmarks_pass():
    results = run_benchmarks()
    assert [item.name for item in results] == [
        "affordability sensitivity",
        "relevance dominates irrelevant wealth",
        "trusted-peer influence",
        "seed variation",
        "contradiction handling",
    ]
    assert all(item.passed for item in results), [item.model_dump() for item in results]
