import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.forecast_evidence import (
    PaperForecastEvidenceConfig,
    PaperForecastEvidenceGateResult,
    PaperForecastEvidenceLog,
    PaperForecastEvidenceObservation,
    build_paper_forecast_evidence_report,
)


def evidence_observation(
    index: int,
    *,
    probability: Decimal,
    actual: Decimal,
    theoretical_edge: Decimal,
    executable_edge: Decimal,
    fill_probability: Decimal,
    residual: Decimal,
    paper_return: Decimal,
) -> PaperForecastEvidenceObservation:
    return PaperForecastEvidenceObservation(
        observed_at=datetime(2026, 8, 1, tzinfo=UTC) + timedelta(days=index),
        source_packet_id=f"packet-{index}",
        condition_id=f"condition-{index % 2}",
        token_id=f"token-{index}",
        market_slug=f"market-{index % 2}",
        strategy_type="relative_value" if index % 2 else "market_quality",
        risk_tags=("liquidity", "event-risk") if index == 1 else ("liquidity",),
        predicted_probability=probability,
        actual_outcome_value=actual,
        theoretical_edge_ratio=theoretical_edge,
        executable_edge_ratio=executable_edge,
        fill_probability=fill_probability,
        residual_exposure_ratio=residual,
        paper_return_ratio=paper_return,
    )


def sample_observations():
    return (
        evidence_observation(
            1,
            probability=Decimal("0.7000"),
            actual=Decimal("1"),
            theoretical_edge=Decimal("0.1200"),
            executable_edge=Decimal("0.0900"),
            fill_probability=Decimal("0.8000"),
            residual=Decimal("0.0000"),
            paper_return=Decimal("0.1000"),
        ),
        evidence_observation(
            2,
            probability=Decimal("0.6000"),
            actual=Decimal("0"),
            theoretical_edge=Decimal("0.0800"),
            executable_edge=Decimal("0.0300"),
            fill_probability=Decimal("0.6500"),
            residual=Decimal("0.1000"),
            paper_return=Decimal("-0.0200"),
        ),
        evidence_observation(
            3,
            probability=Decimal("0.3000"),
            actual=Decimal("0"),
            theoretical_edge=Decimal("0.0500"),
            executable_edge=Decimal("0.0400"),
            fill_probability=Decimal("0.7000"),
            residual=Decimal("0.0000"),
            paper_return=Decimal("0.0300"),
        ),
    )


def test_build_paper_forecast_evidence_report_summarizes_observations():
    observations = sample_observations()

    report = build_paper_forecast_evidence_report(
        [observations[2], observations[0], observations[1]],
        config=PaperForecastEvidenceConfig(
            config_version="node5-test",
            min_probability_observations=3,
            min_edge_observations=3,
            max_mean_probability_loss=Decimal("0.2000"),
            max_bucket_error=Decimal("0.3500"),
            max_mean_edge_gap_ratio=Decimal("0.0500"),
            min_positive_edge_hit_rate=Decimal("0.6000"),
            max_residual_exposure_ratio=Decimal("0.1000"),
        ),
        generated_at=datetime(2026, 8, 10, tzinfo=UTC),
    )

    assert report.generated_at == datetime(2026, 8, 10, tzinfo=UTC)
    assert report.config_version == "node5-test"
    assert report.first_observed_at == observations[0].observed_at
    assert report.last_observed_at == observations[2].observed_at
    assert report.observation_count == 3
    assert report.probability_observation_count == 3
    assert report.edge_observation_count == 3
    assert report.unique_market_count == 2
    assert report.unique_strategy_count == 2
    assert report.unique_risk_tag_count == 2
    assert report.mean_probability_loss == Decimal("0.1800")
    assert report.worst_bucket_error == Decimal("0.3000")
    assert report.mean_edge_gap_ratio == Decimal("0.0300")
    assert report.positive_edge_hit_rate == Decimal("0.6667")
    assert report.worst_residual_exposure_ratio == Decimal("0.1000")
    assert report.status == "paper_review_ready"
    assert [bucket.bucket_label for bucket in report.buckets] == [
        "0.2000-0.4000",
        "0.6000-0.8000",
    ]
    assert report.buckets[0].lower_probability == Decimal("0.2000")
    assert report.buckets[0].upper_probability == Decimal("0.4000")
    assert report.buckets[0].mean_predicted_probability == Decimal("0.3000")
    assert report.buckets[0].observed_frequency == Decimal("0.0000")
    assert report.buckets[0].bucket_error == Decimal("0.3000")
    assert report.buckets[0].mean_probability_loss == Decimal("0.0900")
    assert report.buckets[1].lower_probability == Decimal("0.6000")
    assert report.buckets[1].upper_probability == Decimal("0.8000")
    assert report.buckets[1].mean_predicted_probability == Decimal("0.6500")
    assert report.buckets[1].observed_frequency == Decimal("0.5000")
    assert report.buckets[1].bucket_error == Decimal("0.1500")
    assert report.buckets[1].mean_probability_loss == Decimal("0.2250")


def test_build_paper_forecast_evidence_report_records_gate_results():
    observations = sample_observations()

    report = build_paper_forecast_evidence_report(
        observations,
        config=PaperForecastEvidenceConfig(
            config_version="node5-test",
            min_probability_observations=4,
            min_edge_observations=4,
            max_mean_probability_loss=Decimal("0.1000"),
            max_bucket_error=Decimal("0.3500"),
            max_mean_edge_gap_ratio=Decimal("0.0500"),
            min_positive_edge_hit_rate=Decimal("0.6000"),
            max_residual_exposure_ratio=Decimal("0.1000"),
        ),
        generated_at=datetime(2026, 8, 10, tzinfo=UTC),
    )

    gates = {gate.gate_name: gate for gate in report.gate_results}
    assert list(gates) == [
        "data_integrity",
        "sample_size",
        "probability_quality",
        "executable_edge_quality",
        "residual_exposure",
    ]
    assert gates["data_integrity"].status == "pass"
    assert gates["sample_size"].status == "fail"
    assert gates["probability_quality"].status == "fail"
    assert gates["executable_edge_quality"].status == "pass"
    assert gates["residual_exposure"].status == "pass"
    assert "mean_probability_loss" in str(gates["probability_quality"].observed_value)
    assert report.status == "blocked_by_quality"


def test_build_paper_forecast_evidence_report_marks_insufficient_evidence_when_only_sample_fails():
    observations = sample_observations()

    report = build_paper_forecast_evidence_report(
        observations,
        config=PaperForecastEvidenceConfig(
            config_version="node5-test",
            min_probability_observations=4,
            min_edge_observations=4,
            max_mean_probability_loss=Decimal("0.2000"),
            max_bucket_error=Decimal("0.3500"),
            max_mean_edge_gap_ratio=Decimal("0.0500"),
            min_positive_edge_hit_rate=Decimal("0.6000"),
            max_residual_exposure_ratio=Decimal("0.1000"),
        ),
        generated_at=datetime(2026, 8, 10, tzinfo=UTC),
    )

    gates = {gate.gate_name: gate for gate in report.gate_results}
    assert gates["sample_size"].status == "fail"
    assert gates["probability_quality"].status == "pass"
    assert gates["executable_edge_quality"].status == "pass"
    assert gates["residual_exposure"].status == "pass"
    assert report.status == "insufficient_evidence"


def test_build_paper_forecast_evidence_report_handles_empty_input():
    report = build_paper_forecast_evidence_report(
        [],
        config=PaperForecastEvidenceConfig(config_version="node5-test"),
        generated_at=datetime(2026, 8, 10, tzinfo=UTC),
    )

    assert report.observation_count == 0
    assert report.first_observed_at is None
    assert report.last_observed_at is None
    assert report.mean_probability_loss is None
    assert report.buckets == ()
    assert report.status == "incomplete_data"
    assert {gate.status for gate in report.gate_results} == {"incomplete"}


def test_build_paper_forecast_evidence_report_supports_probability_only_observations():
    observations = (
        replace(
            sample_observations()[0],
            theoretical_edge_ratio=None,
            executable_edge_ratio=None,
            fill_probability=None,
            residual_exposure_ratio=None,
            paper_return_ratio=None,
        ),
        replace(
            sample_observations()[1],
            theoretical_edge_ratio=None,
            executable_edge_ratio=None,
            fill_probability=None,
            residual_exposure_ratio=None,
            paper_return_ratio=None,
        ),
    )

    report = build_paper_forecast_evidence_report(
        observations,
        config=PaperForecastEvidenceConfig(
            config_version="node5-test",
            min_probability_observations=2,
            min_edge_observations=0,
        ),
        generated_at=datetime(2026, 8, 10, tzinfo=UTC),
    )

    gates = {gate.gate_name: gate for gate in report.gate_results}
    assert report.probability_observation_count == 2
    assert report.edge_observation_count == 0
    assert report.mean_probability_loss == Decimal("0.2250")
    assert report.mean_edge_gap_ratio is None
    assert gates["probability_quality"].status == "pass"
    assert gates["executable_edge_quality"].status == "incomplete"
    assert gates["residual_exposure"].status == "incomplete"
    assert report.status == "insufficient_evidence"


def test_build_paper_forecast_evidence_report_supports_edge_only_observations():
    observations = (
        replace(
            sample_observations()[0],
            predicted_probability=None,
            actual_outcome_value=None,
        ),
        replace(
            sample_observations()[1],
            predicted_probability=None,
            actual_outcome_value=None,
        ),
    )

    report = build_paper_forecast_evidence_report(
        observations,
        config=PaperForecastEvidenceConfig(
            config_version="node5-test",
            min_probability_observations=0,
            min_edge_observations=2,
        ),
        generated_at=datetime(2026, 8, 10, tzinfo=UTC),
    )

    gates = {gate.gate_name: gate for gate in report.gate_results}
    assert report.probability_observation_count == 0
    assert report.edge_observation_count == 2
    assert report.mean_probability_loss is None
    assert report.buckets == ()
    assert report.mean_edge_gap_ratio == Decimal("0.0400")
    assert gates["probability_quality"].status == "incomplete"
    assert gates["executable_edge_quality"].status == "pass"
    assert gates["residual_exposure"].status == "pass"
    assert report.status == "insufficient_evidence"


def test_forecast_evidence_observation_rejects_partial_roles():
    with pytest.raises(ValueError, match="probability"):
        replace(sample_observations()[0], actual_outcome_value=None)
    with pytest.raises(ValueError, match="probability"):
        replace(sample_observations()[0], predicted_probability=None)
    with pytest.raises(ValueError, match="executable"):
        replace(sample_observations()[0], fill_probability=None)
    with pytest.raises(ValueError, match="executable"):
        replace(sample_observations()[0], paper_return_ratio=None)


def test_build_paper_forecast_evidence_report_rejects_duplicate_key_after_utc_normalization():
    base = sample_observations()[0]
    same_instant = replace(
        base,
        observed_at=datetime(2026, 8, 2, 8, tzinfo=timezone(timedelta(hours=-4))),
    )
    utc_instant = replace(
        base,
        observed_at=datetime(2026, 8, 2, 12, tzinfo=UTC),
    )

    with pytest.raises(ValueError, match="duplicate"):
        build_paper_forecast_evidence_report(
            [same_instant, utc_instant],
            config=PaperForecastEvidenceConfig(config_version="node5-test"),
            generated_at=datetime(2026, 8, 10, tzinfo=UTC),
        )


def test_build_paper_forecast_evidence_report_rejects_duplicate_evidence_key():
    observation = sample_observations()[0]

    with pytest.raises(ValueError, match="duplicate"):
        build_paper_forecast_evidence_report(
            [observation, observation],
            config=PaperForecastEvidenceConfig(config_version="node5-test"),
            generated_at=datetime(2026, 8, 10, tzinfo=UTC),
        )


def test_build_paper_forecast_evidence_report_rejects_bad_public_inputs():
    observation = sample_observations()[0]
    config = PaperForecastEvidenceConfig(config_version="node5-test")

    with pytest.raises(ValueError, match="observations"):
        build_paper_forecast_evidence_report(
            "not-observations",
            config=config,
            generated_at=datetime(2026, 8, 10, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="PaperForecastEvidenceObservation"):
        build_paper_forecast_evidence_report(
            [object()],
            config=config,
            generated_at=datetime(2026, 8, 10, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="config"):
        build_paper_forecast_evidence_report(
            [observation],
            config=object(),
            generated_at=datetime(2026, 8, 10, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_forecast_evidence_report(
            [observation],
            config=config,
            generated_at=None,
        )


def test_forecast_evidence_dataclasses_reject_invalid_values():
    with pytest.raises(ValueError, match="max_mean_probability_loss"):
        PaperForecastEvidenceConfig(
            config_version="node5-test",
            max_mean_probability_loss=1,
        )
    with pytest.raises(ValueError, match="probability_bucket_width"):
        PaperForecastEvidenceConfig(
            config_version="node5-test",
            probability_bucket_width=Decimal("0"),
        )
    with pytest.raises(ValueError, match="probability_bucket_width"):
        PaperForecastEvidenceConfig(
            config_version="node5-test",
            probability_bucket_width=Decimal("1.2000"),
        )
    with pytest.raises(ValueError, match="probability_bucket_width"):
        PaperForecastEvidenceConfig(
            config_version="node5-test",
            probability_bucket_width=Decimal("0.00001"),
        )
    with pytest.raises(ValueError, match="probability_bucket_width"):
        PaperForecastEvidenceConfig(
            config_version="node5-test",
            probability_bucket_width=Decimal("0.12345"),
        )
    with pytest.raises(ValueError, match="actual_outcome_value"):
        replace(sample_observations()[0], actual_outcome_value=Decimal("0.5"))
    with pytest.raises(ValueError, match="evidence"):
        PaperForecastEvidenceObservation(
            observed_at=datetime(2026, 8, 1, tzinfo=UTC),
            source_packet_id="packet-empty",
            condition_id="condition-empty",
            token_id="token-empty",
            market_slug="market-empty",
            strategy_type="market_quality",
            risk_tags=("liquidity",),
        )


def test_build_paper_forecast_evidence_report_uses_custom_probability_bucket_width_and_boundaries():
    observations = (
        replace(
            sample_observations()[0],
            predicted_probability=Decimal("0.5000"),
            actual_outcome_value=Decimal("1"),
        ),
        replace(
            sample_observations()[1],
            predicted_probability=Decimal("1.0000"),
            actual_outcome_value=Decimal("1"),
        ),
    )

    report = build_paper_forecast_evidence_report(
        observations,
        config=PaperForecastEvidenceConfig(
            config_version="node5-test",
            min_probability_observations=2,
            min_edge_observations=2,
            probability_bucket_width=Decimal("0.5000"),
            max_mean_probability_loss=Decimal("0.2000"),
            max_bucket_error=Decimal("0.5000"),
            max_mean_edge_gap_ratio=Decimal("0.0500"),
            min_positive_edge_hit_rate=Decimal("0"),
            max_residual_exposure_ratio=Decimal("0.1000"),
        ),
        generated_at=datetime(2026, 8, 10, tzinfo=UTC),
    )

    assert [bucket.bucket_label for bucket in report.buckets] == [
        "0.5000-1.0000",
    ]
    assert report.buckets[0].lower_probability == Decimal("0.5000")
    assert report.buckets[0].upper_probability == Decimal("1.0000")
    assert report.buckets[0].observation_count == 2
    assert report.buckets[0].mean_predicted_probability == Decimal("0.7500")
    assert report.buckets[0].observed_frequency == Decimal("1.0000")


def test_build_paper_forecast_evidence_report_keeps_one_in_final_non_dividing_bucket():
    observations = (
        replace(
            sample_observations()[0],
            predicted_probability=Decimal("0.9000"),
            actual_outcome_value=Decimal("1"),
        ),
        replace(
            sample_observations()[1],
            predicted_probability=Decimal("1.0000"),
            actual_outcome_value=Decimal("1"),
        ),
    )

    report = build_paper_forecast_evidence_report(
        observations,
        config=PaperForecastEvidenceConfig(
            config_version="node5-test",
            min_probability_observations=2,
            min_edge_observations=2,
            probability_bucket_width=Decimal("0.3000"),
            max_mean_probability_loss=Decimal("0.0100"),
            max_bucket_error=Decimal("0.1000"),
            max_mean_edge_gap_ratio=Decimal("0.0500"),
            min_positive_edge_hit_rate=Decimal("0"),
            max_residual_exposure_ratio=Decimal("0.1000"),
        ),
        generated_at=datetime(2026, 8, 10, tzinfo=UTC),
    )

    assert [bucket.bucket_label for bucket in report.buckets] == [
        "0.9000-1.0000",
    ]
    assert report.buckets[0].lower_probability == Decimal("0.9000")
    assert report.buckets[0].upper_probability == Decimal("1.0000")
    assert report.buckets[0].observation_count == 2
    assert report.buckets[0].mean_predicted_probability == Decimal("0.9500")
    assert report.buckets[0].observed_frequency == Decimal("1.0000")


def test_build_paper_forecast_evidence_report_zero_thresholds_pass_on_exact_zero():
    observations = (
        replace(
            sample_observations()[0],
            predicted_probability=Decimal("1.0000"),
            actual_outcome_value=Decimal("1"),
            theoretical_edge_ratio=Decimal("0.0300"),
            executable_edge_ratio=Decimal("0.0300"),
            residual_exposure_ratio=Decimal("0"),
            paper_return_ratio=Decimal("0"),
        ),
    )

    report = build_paper_forecast_evidence_report(
        observations,
        config=PaperForecastEvidenceConfig(
            config_version="node5-test",
            min_probability_observations=1,
            min_edge_observations=1,
            max_mean_probability_loss=Decimal("0"),
            max_bucket_error=Decimal("0"),
            max_mean_edge_gap_ratio=Decimal("0"),
            min_positive_edge_hit_rate=Decimal("0"),
            max_residual_exposure_ratio=Decimal("0"),
        ),
        generated_at=datetime(2026, 8, 10, tzinfo=UTC),
    )

    assert report.mean_probability_loss == Decimal("0.0000")
    assert report.worst_bucket_error == Decimal("0.0000")
    assert report.mean_edge_gap_ratio == Decimal("0.0000")
    assert report.positive_edge_hit_rate == Decimal("0.0000")
    assert report.worst_residual_exposure_ratio == Decimal("0.0000")
    assert report.status == "paper_review_ready"


def test_build_paper_forecast_evidence_report_zero_thresholds_fail_on_positive_metric():
    observations = (
        replace(
            sample_observations()[0],
            predicted_probability=Decimal("0.9999"),
            actual_outcome_value=Decimal("1"),
            theoretical_edge_ratio=Decimal("0.0301"),
            executable_edge_ratio=Decimal("0.0300"),
            residual_exposure_ratio=Decimal("0.0001"),
            paper_return_ratio=Decimal("0"),
        ),
    )

    report = build_paper_forecast_evidence_report(
        observations,
        config=PaperForecastEvidenceConfig(
            config_version="node5-test",
            min_probability_observations=1,
            min_edge_observations=1,
            max_mean_probability_loss=Decimal("0"),
            max_bucket_error=Decimal("0"),
            max_mean_edge_gap_ratio=Decimal("0"),
            min_positive_edge_hit_rate=Decimal("0"),
            max_residual_exposure_ratio=Decimal("0"),
        ),
        generated_at=datetime(2026, 8, 10, tzinfo=UTC),
    )

    gates = {gate.gate_name: gate for gate in report.gate_results}
    assert gates["probability_quality"].status == "fail"
    assert gates["executable_edge_quality"].status == "fail"
    assert gates["residual_exposure"].status == "fail"
    assert report.status == "blocked_by_quality"


def test_forecast_evidence_gate_result_rejects_float_values_and_unknown_status():
    with pytest.raises(ValueError, match="observed_value"):
        PaperForecastEvidenceGateResult(
            gate_name="sample_size",
            status="fail",
            message="bad",
            observed_value=1.0,
        )
    with pytest.raises(ValueError, match="status"):
        PaperForecastEvidenceGateResult(
            gate_name="sample_size",
            status="unknown",
            message="bad",
        )
    with pytest.raises(ValueError, match="threshold"):
        PaperForecastEvidenceGateResult(
            gate_name="sample_size",
            status="fail",
            message="bad",
            threshold=True,
        )


def test_forecast_evidence_dataclasses_are_frozen():
    report = build_paper_forecast_evidence_report(
        sample_observations(),
        config=PaperForecastEvidenceConfig(config_version="node5-test"),
        generated_at=datetime(2026, 8, 10, tzinfo=UTC),
    )

    with pytest.raises(FrozenInstanceError):
        report.observation_count = 0
    with pytest.raises(FrozenInstanceError):
        report.buckets[0].bucket_error = Decimal("0")


def test_paper_forecast_evidence_log_appends_jsonl_report(tmp_path):
    report = build_paper_forecast_evidence_report(
        sample_observations(),
        config=PaperForecastEvidenceConfig(config_version="node5-test"),
        generated_at=datetime(2026, 8, 10, tzinfo=UTC),
    )
    log = PaperForecastEvidenceLog(path=tmp_path / "forecast-evidence.jsonl")

    log.append(report)

    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert lines[0].startswith('{"buckets"')
    stored = json.loads(lines[0])
    assert stored["paper_only"] is True
    assert stored["generated_at"] == "2026-08-10T00:00:00+00:00"
    assert stored["config_version"] == "node5-test"
    assert stored["mean_probability_loss"] == "0.1800"
    assert stored["gate_results"][0]["gate_name"] == "data_integrity"


def test_paper_forecast_evidence_log_appends_without_overwriting_and_creates_parent_dirs(
    tmp_path,
):
    report = build_paper_forecast_evidence_report(
        sample_observations(),
        config=PaperForecastEvidenceConfig(config_version="node5-test"),
        generated_at=datetime(2026, 8, 10, tzinfo=UTC),
    )
    log = PaperForecastEvidenceLog(path=str(tmp_path / "nested" / "forecast.jsonl"))

    log.append(report)
    log.append(report)

    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["generated_at"] == "2026-08-10T00:00:00+00:00"
    assert json.loads(lines[1])["generated_at"] == "2026-08-10T00:00:00+00:00"


def test_paper_forecast_evidence_log_rejects_invalid_paths(tmp_path):
    with pytest.raises(ValueError, match="path"):
        PaperForecastEvidenceLog(path=object())
    with pytest.raises(ValueError, match="path"):
        PaperForecastEvidenceLog(path=" ")

    existing_dir = tmp_path / "existing-dir"
    existing_dir.mkdir()
    with pytest.raises(ValueError, match="path"):
        PaperForecastEvidenceLog(path=existing_dir)

    existing_file = tmp_path / "parent-file"
    existing_file.write_text("already a file", encoding="utf-8")
    with pytest.raises(ValueError, match="parent"):
        PaperForecastEvidenceLog(path=existing_file / "forecast.jsonl")


def test_paper_forecast_evidence_log_rejects_invalid_public_input_before_file_creation(
    tmp_path,
):
    path = tmp_path / "forecast.jsonl"
    log = PaperForecastEvidenceLog(path=path)

    with pytest.raises(ValueError, match="PaperForecastEvidenceReport"):
        log.append(object())

    assert not path.exists()


def test_paper_forecast_evidence_log_preserves_existing_file_when_serialization_fails(
    tmp_path,
):
    report = build_paper_forecast_evidence_report(
        sample_observations(),
        config=PaperForecastEvidenceConfig(config_version="node5-test"),
        generated_at=datetime(2026, 8, 10, tzinfo=UTC),
    )
    object.__setattr__(report, "mean_probability_loss", Decimal("NaN"))
    path = tmp_path / "forecast.jsonl"
    path.write_text('{"existing": true}\n', encoding="utf-8")
    log = PaperForecastEvidenceLog(path=path)

    with pytest.raises(ValueError, match="finite|JSON|serializable"):
        log.append(report)

    assert path.read_text(encoding="utf-8") == '{"existing": true}\n'


def test_paper_forecast_evidence_log_preserves_existing_file_when_nested_report_is_invalid(
    tmp_path,
):
    report = build_paper_forecast_evidence_report(
        sample_observations(),
        config=PaperForecastEvidenceConfig(config_version="node5-test"),
        generated_at=datetime(2026, 8, 10, tzinfo=UTC),
    )
    object.__setattr__(report.gate_results[0], "status", "unknown")
    path = tmp_path / "forecast.jsonl"
    path.write_text('{"existing": true}\n', encoding="utf-8")
    log = PaperForecastEvidenceLog(path=path)

    with pytest.raises(ValueError, match="status"):
        log.append(report)

    assert path.read_text(encoding="utf-8") == '{"existing": true}\n'


def test_paper_forecast_evidence_log_preserves_existing_file_when_nested_bucket_is_invalid(
    tmp_path,
):
    report = build_paper_forecast_evidence_report(
        sample_observations(),
        config=PaperForecastEvidenceConfig(config_version="node5-test"),
        generated_at=datetime(2026, 8, 10, tzinfo=UTC),
    )
    object.__setattr__(report.buckets[0], "observation_count", -1)
    path = tmp_path / "forecast.jsonl"
    path.write_text('{"existing": true}\n', encoding="utf-8")
    log = PaperForecastEvidenceLog(path=path)

    with pytest.raises(ValueError, match="observation_count"):
        log.append(report)

    assert path.read_text(encoding="utf-8") == '{"existing": true}\n'
