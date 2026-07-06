from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import importlib
import inspect
import json

import pytest


MODULE = "polymarket_alpha_lab.strategy_probability_forecast_source_quality_gate_v2"
GENERATED_AT = datetime(2025, 1, 3, tzinfo=UTC)


def api():
    return importlib.import_module(MODULE)


def d(value: str) -> Decimal:
    return Decimal(value)


def evidence(
    *,
    candidate_id: str = "candidate_alpha",
    source_id: str = "source_alpha",
    source_kind: str = "official",
    observed_at: datetime | None = None,
    forecast_probability: Decimal = d("0.620000"),
    evidence_strength_score: Decimal = d("0.900000"),
    source_relevance_score: Decimal = d("0.800000"),
    calibration_score: Decimal = d("0.900000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.StrategyProbabilityForecastSourceQualityEvidence(
        candidate_id=candidate_id,
        source_id=source_id,
        source_kind=source_kind,
        observed_at=observed_at or GENERATED_AT - timedelta(hours=12),
        forecast_probability=forecast_probability,
        evidence_strength_score=evidence_strength_score,
        source_relevance_score=source_relevance_score,
        calibration_score=calibration_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def config(**overrides: object):
    module = api()
    values = {
        "max_evidence_age_seconds": d("172800.000000"),
    }
    values.update(overrides)
    return module.StrategyProbabilityForecastSourceQualityGateV2Config(**values)


def build_report(*rows: object, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_strategy_probability_forecast_source_quality_gate_v2_report(
        rows,
        config=config(),
        generated_at=generated_at,
    )


def assert_no_public_numeric_literals(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric_literals(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_no_public_numeric_literals(item)
        return
    assert type(value) is not int
    assert type(value) is not float
    assert not isinstance(value, Decimal)


def test_forecast_source_quality_scoring_passes_with_fresh_official_evidence() -> None:
    report = build_report(
        evidence(source_id="official_alpha", source_kind="official"),
        evidence(
            source_id="model_alpha",
            source_kind="model",
            evidence_strength_score=d("0.800000"),
        ),
    )

    row = report.rows[0]
    assert report.status == "pass"
    assert report.pass_count == d("1")
    assert row.status == "pass"
    assert row.source_count == d("2")
    assert row.official_source_count == d("1")
    assert row.official_source_ratio == d("0.500000")
    assert row.freshness_score == d("0.750000")
    assert row.evidence_strength_score == d("0.850000")
    assert row.source_quality_score == d("0.752500")
    assert row.reason_codes == ("forecast_source_quality_pass",)


def test_missing_official_source_penalty_blocks_candidate() -> None:
    report = build_report(
        evidence(
            candidate_id="candidate_model_only",
            source_id="model_only",
            source_kind="model",
        ),
    )

    row = report.rows[0]
    assert report.status == "blocked"
    assert row.status == "blocked"
    assert row.official_source_count == d("0")
    assert row.official_source_ratio == d("0.000000")
    assert "official_source_absent" in row.reason_codes
    assert "official_source_gap_present" in report.reason_codes
    assert row.source_quality_score == d("0.665000")


def test_stale_evidence_penalty_blocks_candidate() -> None:
    report = build_report(
        evidence(
            source_id="stale_official",
            source_kind="official",
            observed_at=GENERATED_AT - timedelta(days=3),
        ),
    )

    row = report.rows[0]
    assert report.status == "blocked"
    assert row.status == "blocked"
    assert row.stale_source_count == d("1")
    assert row.stale_source_ratio == d("1.000000")
    assert row.freshness_score == d("0.000000")
    assert "stale_evidence_blocked" in row.reason_codes
    assert "stale_evidence_present" in report.reason_codes


def test_payload_serialization_is_canonical_and_decimal_strings_only() -> None:
    module = api()
    report = build_report(
        evidence(source_id="official_alpha", source_kind="official"),
        evidence(source_id="model_alpha", source_kind="model"),
    )

    payload = module.strategy_probability_forecast_source_quality_gate_v2_report_to_payload(
        report,
    )

    assert payload["candidate_count"] == "1"
    assert payload["average_source_quality_score"] == "0.765000"
    assert payload["rows"][0]["source_count"] == "2"
    assert payload["rows"][0]["source_quality_score"] == "0.765000"
    assert len(payload["derived_validation_digest"]) == 64
    assert_no_public_numeric_literals(payload)
    assert json.loads(json.dumps(payload)) == payload
    assert (
        module.strategy_probability_forecast_source_quality_gate_v2_report_to_payload(payload)
        == payload
    )


def test_dataclasses_are_frozen_decimal_only_and_reject_subclassing() -> None:
    module = api()
    item = evidence()

    with pytest.raises(FrozenInstanceError):
        item.candidate_id = "candidate_beta"

    class DecimalSubclass(Decimal):
        pass

    with pytest.raises(ValueError, match="exactly Decimal"):
        evidence(forecast_probability=DecimalSubclass("0.500000"))

    for cls in (
        module.StrategyProbabilityForecastSourceQualityGateV2Config,
        module.StrategyProbabilityForecastSourceQualityEvidence,
        module.StrategyProbabilityForecastSourceQualityGateV2Row,
        module.StrategyProbabilityForecastSourceQualityGateV2Report,
    ):
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"{cls.__name__}Subclass", (cls,), {})


def test_hard_flags_are_enforced_for_inputs_reports_and_payloads() -> None:
    module = api()

    with pytest.raises(ValueError, match="paper_only"):
        evidence(paper_only=False)

    with pytest.raises(ValueError, match="readonly"):
        config(readonly=False)

    report = build_report(evidence())
    payload = module.strategy_probability_forecast_source_quality_gate_v2_report_to_payload(
        report,
    )
    payload["report_only"] = False

    with pytest.raises(ValueError, match="report_only"):
        module.strategy_probability_forecast_source_quality_gate_v2_report_to_payload(
            payload,
        )


def test_digest_tampering_is_rejected_for_report_and_payload() -> None:
    module = api()
    report = build_report(evidence())

    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.StrategyProbabilityForecastSourceQualityGateV2Report(
            generated_at=report.generated_at,
            config_version=report.config_version,
            status=report.status,
            candidate_count=report.candidate_count,
            pass_count=report.pass_count,
            watch_count=report.watch_count,
            blocked_count=report.blocked_count,
            official_source_gap_count=report.official_source_gap_count,
            stale_evidence_count=report.stale_evidence_count,
            average_source_quality_score=report.average_source_quality_score,
            min_source_quality_score=report.min_source_quality_score,
            max_source_quality_score=report.max_source_quality_score,
            rows=report.rows,
            reason_codes=report.reason_codes,
            derived_validation_digest="0" * 64,
        )

    payload = module.strategy_probability_forecast_source_quality_gate_v2_report_to_payload(
        report,
    )
    payload["rows"][0]["source_quality_score"] = "0.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.strategy_probability_forecast_source_quality_gate_v2_report_to_payload(
            payload,
        )


@pytest.mark.parametrize(
    "term",
    [
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    ],
)
def test_unsafe_public_payload_keys_and_values_are_rejected(term: str) -> None:
    module = api()
    payload = module.strategy_probability_forecast_source_quality_gate_v2_report_to_payload(
        build_report(evidence()),
    )

    unsafe_key_payload = dict(payload)
    unsafe_key_payload[f"{term}_field"] = "safe_value"
    with pytest.raises(ValueError, match="unsafe public text"):
        module.strategy_probability_forecast_source_quality_gate_v2_report_to_payload(
            unsafe_key_payload,
        )

    unsafe_value_payload = dict(payload)
    unsafe_value_payload["rows"] = [dict(payload["rows"][0])]
    unsafe_value_payload["rows"][0]["candidate_id"] = f"candidate_{term}_marker"
    with pytest.raises(ValueError, match="unsafe public text"):
        module.strategy_probability_forecast_source_quality_gate_v2_report_to_payload(
            unsafe_value_payload,
        )


def test_module_omits_unsafe_public_surfaces() -> None:
    module = api()
    blocked_terms = (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    )

    public_names = tuple(name for name in dir(module) if not name.startswith("_"))
    assert not any(
        term in public_name.lower()
        for public_name in public_names
        for term in blocked_terms
    )

    source = inspect.getsource(module).lower()
    assert "requests" not in source
    assert "httpx" not in source
    assert "sqlite" not in source
    assert "psycopg" not in source
    assert "web3" not in source
