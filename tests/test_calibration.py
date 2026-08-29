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
    names = {item.name for item in results}
    assert {
        "target audience relevance", "non-target users can still convert",
        "price-sensitive response", "price-insensitive stability",
        "sentiment-action coherence", "habit dominance guard", "topic diversity",
        "segment minimum sample", "agent explanation diversity",
    } <= names
    assert all(item.passed for item in results), [item.model_dump() for item in results]
