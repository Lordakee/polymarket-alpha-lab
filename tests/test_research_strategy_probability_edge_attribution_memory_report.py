from __future__ import annotations

import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 14, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_strategy_probability_edge_attribution_memory_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def memory_change(**overrides: object):
    module = api()
    values = {
        "memory_factor_key": "macro_memory_alpha",
        "domain_key": "macro_rates",
        "observed_at": GENERATED_AT - timedelta(minutes=20),
        "probability_edge_change_abs": d("0.080000"),
        "calibration_recency_hours": d("12.000000"),
        "prior_forecast_error_reuse_score": d("0.900000"),
        "evidence_update_quality_score": d("0.850000"),
        "cost_pressure_score": d("0.100000"),
    }
    values.update(overrides)
    return module.ResearchStrategyProbabilityEdgeAttributionMemoryInput(**values)


def config(**overrides: object):
    module = api()
    return module.ResearchStrategyProbabilityEdgeAttributionMemoryConfig(**overrides)


def build_report(*changes: object, config_override=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_strategy_probability_edge_attribution_memory_report(
        changes,
        generated_at=generated_at,
        config=config() if config_override is None else config_override,
    )


def sample_changes() -> tuple[object, ...]:
    return (
        memory_change(
            memory_factor_key="macro_memory_alpha",
            domain_key="macro_rates",
            observed_at=GENERATED_AT - timedelta(minutes=15),
            probability_edge_change_abs=d("0.080000"),
            calibration_recency_hours=d("12.000000"),
            prior_forecast_error_reuse_score=d("0.900000"),
            evidence_update_quality_score=d("0.850000"),
            cost_pressure_score=d("0.100000"),
        ),
        memory_change(
            memory_factor_key="policy_memory_beta",
            domain_key="policy_rules",
            observed_at=GENERATED_AT - timedelta(minutes=20),
            probability_edge_change_abs=d("0.120000"),
            calibration_recency_hours=d("96.000000"),
            prior_forecast_error_reuse_score=d("0.650000"),
            evidence_update_quality_score=d("0.600000"),
            cost_pressure_score=d("0.400000"),
        ),
        memory_change(
            memory_factor_key="sports_memory_gamma",
            domain_key="sports_soccer",
            observed_at=GENERATED_AT - timedelta(minutes=25),
            probability_edge_change_abs=d("0.300000"),
            calibration_recency_hours=d("200.000000"),
            prior_forecast_error_reuse_score=d("0.250000"),
            evidence_update_quality_score=d("0.200000"),
            cost_pressure_score=d("0.850000"),
        ),
    )


def test_attribution_scoring_rolls_up_pass_watch_and_block_rows() -> None:
    module = api()

    report = build_report(*reversed(sample_changes()))
    payload = module.research_strategy_probability_edge_attribution_memory_report_payload(
        report,
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        "research-strategy-probability-edge-attribution-memory-report-v0"
    )
    assert report.report_status == "block"
    assert report.change_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_probability_edge_change_abs == d("0.166667")
    assert report.average_calibration_recency_score == d("0.452381")
    assert report.average_prior_forecast_error_reuse_score == d("0.600000")
    assert report.average_evidence_update_quality_score == d("0.550000")
    assert report.average_cost_pressure_score == d("0.450000")
    assert report.average_memory_attribution_score == d("0.384881")
    assert report.max_cost_pressure_score == d("0.850000")
    assert report.max_calibration_recency_hours == d("200.000000")
    assert len(report.public_payload_digest) == 64

    blocked, watched, passed = report.rows
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.rank for row in report.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert blocked.domain_key == "sports_soccer"
    assert blocked.calibration_recency_score == d("0.000000")
    assert blocked.memory_attribution_score == d("0.000000")
    assert blocked.attribution_pressure == d("1.000000")
    assert blocked.reason_codes == (
        "probability_edge_attribution_memory_block",
        "material_probability_edge_change",
        "calibration_recency_block",
        "prior_forecast_error_reuse_drag",
        "evidence_update_quality_drag",
        "cost_pressure_block",
    )

    assert watched.domain_key == "policy_rules"
    assert watched.calibration_recency_score == d("0.428571")
    assert watched.memory_attribution_score == d("0.411071")
    assert watched.attribution_pressure == d("0.588929")
    assert watched.reason_codes == (
        "probability_edge_attribution_memory_watch",
        "material_probability_edge_change",
        "calibration_recency_watch",
        "prior_forecast_error_reuse_support",
        "cost_pressure_watch",
    )

    assert passed.domain_key == "macro_rates"
    assert passed.calibration_recency_score == d("0.928571")
    assert passed.memory_attribution_score == d("0.743571")
    assert passed.attribution_pressure == d("0.256429")
    assert passed.reason_codes == (
        "probability_edge_attribution_memory_pass",
        "material_probability_edge_change",
        "calibration_recency_fresh",
        "prior_forecast_error_reuse_support",
        "evidence_update_quality_support",
        "cost_pressure_low",
    )
    assert all(row.paper_only and row.report_only and row.readonly for row in report.rows)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert payload["rows"][0]["memory_factor_digest"].startswith("sha256:")
    assert payload["rows"][0]["rank"] == "1.000000"
    assert_no_decimal_objects(payload)
    assert_no_float_or_int_values(payload)


def test_memory_freshness_boundaries_watch_at_threshold_and_block_at_threshold() -> None:
    watch_boundary = memory_change(
        memory_factor_key="freshness_watch_boundary",
        domain_key="macro_rates",
        probability_edge_change_abs=d("0.070000"),
        calibration_recency_hours=d("72.000000"),
        prior_forecast_error_reuse_score=d("0.900000"),
        evidence_update_quality_score=d("0.850000"),
        cost_pressure_score=d("0.100000"),
    )
    block_boundary = memory_change(
        memory_factor_key="freshness_block_boundary",
        domain_key="macro_rates",
        probability_edge_change_abs=d("0.070000"),
        calibration_recency_hours=d("168.000000"),
        prior_forecast_error_reuse_score=d("0.900000"),
        evidence_update_quality_score=d("0.850000"),
        cost_pressure_score=d("0.100000"),
    )

    report = build_report(watch_boundary, block_boundary)
    blocked, watched = report.rows

    assert blocked.status == "block"
    assert blocked.calibration_recency_hours == d("168.000000")
    assert blocked.calibration_recency_score == d("0.000000")
    assert "calibration_recency_block" in blocked.reason_codes
    assert watched.status == "watch"
    assert watched.calibration_recency_hours == d("72.000000")
    assert watched.calibration_recency_score == d("0.571429")
    assert "calibration_recency_watch" in watched.reason_codes


def test_digest_is_deterministic_and_payload_validation_rejects_tampering() -> None:
    module = api()
    report = build_report(*sample_changes())
    permuted = build_report(*reversed(sample_changes()))

    payload = module.research_strategy_probability_edge_attribution_memory_report_payload(
        report,
    )
    permuted_payload = (
        module.research_strategy_probability_edge_attribution_memory_report_payload(
            permuted,
        )
    )
    assert payload == permuted_payload
    assert report.public_payload_digest == (
        module.research_strategy_probability_edge_attribution_memory_digest(report)
    )

    digest_payload = dict(payload)
    digest_payload.pop("public_payload_digest")
    expected_digest = hashlib.sha256(
        json.dumps(
            digest_payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8"),
    ).hexdigest()
    assert payload["public_payload_digest"] == expected_digest

    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="public_payload_digest"):
        replace(report, public_payload_digest="0" * 64)

    tampered = dict(payload)
    tampered["report_status"] = "watch"
    with pytest.raises(ValueError, match="public_payload_digest"):
        module.validate_research_strategy_probability_edge_attribution_memory_public_payload(
            tampered,
        )


def test_public_payload_hashes_private_memory_keys_and_rejects_leaky_payloads() -> None:
    module = api()
    raw_private_key = (
        "candidate-123 market_id=abc market_slug=raw-question "
        "source_url=https://example.invalid token wallet order trade live"
    )
    report = build_report(
        memory_change(
            memory_factor_key=raw_private_key,
            domain_key="macro_rates",
        ),
    )

    payload = module.research_strategy_probability_edge_attribution_memory_report_payload(
        report,
    )
    encoded = json.dumps(payload, sort_keys=True).lower()

    assert raw_private_key.lower() not in encoded
    for forbidden in (
        "candidate",
        "market",
        "slug",
        "question",
        "source",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
    ):
        assert forbidden not in encoded

    leaky_payload = dict(payload)
    leaky_payload["market_id"] = "raw-market"
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.research_strategy_probability_edge_attribution_memory_report_payload(
            leaky_payload,
        )


def test_custom_config_validation_changes_scoring_and_rejects_invalid_config() -> None:
    strict_config = config(
        pass_attribution_score=d("0.700000"),
        block_attribution_score=d("0.400000"),
        watch_calibration_recency_hours=d("48.000000"),
        block_calibration_recency_hours=d("120.000000"),
        watch_cost_pressure_score=d("0.200000"),
        block_cost_pressure_score=d("0.500000"),
    )
    report = build_report(
        memory_change(
            memory_factor_key="strict_policy_memory",
            domain_key="policy_rules",
            calibration_recency_hours=d("60.000000"),
            prior_forecast_error_reuse_score=d("0.900000"),
            evidence_update_quality_score=d("0.850000"),
            cost_pressure_score=d("0.250000"),
        ),
        config_override=strict_config,
    )

    assert report.report_status == "watch"
    assert report.rows[0].status == "watch"
    assert "calibration_recency_watch" in report.rows[0].reason_codes
    assert "cost_pressure_watch" in report.rows[0].reason_codes

    with pytest.raises(ValueError, match="pass_attribution_score must exceed"):
        config(pass_attribution_score=d("0.300000"), block_attribution_score=d("0.400000"))
    with pytest.raises(ValueError, match="block_calibration_recency_hours must exceed"):
        config(
            watch_calibration_recency_hours=d("120.000000"),
            block_calibration_recency_hours=d("48.000000"),
        )
    with pytest.raises(ValueError, match="block_cost_pressure_score must exceed"):
        config(
            watch_cost_pressure_score=d("0.600000"),
            block_cost_pressure_score=d("0.500000"),
        )
    with pytest.raises(ValueError, match="pass_attribution_score must be a Decimal"):
        config(pass_attribution_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only must be True"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="probability_edge_change_abs must be a Decimal"):
        memory_change(probability_edge_change_abs=0.1)  # type: ignore[arg-type]


def assert_no_decimal_objects(value: Any) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload must not contain Decimal objects")
    if isinstance(value, dict):
        for nested in value.values():
            assert_no_decimal_objects(nested)
    elif isinstance(value, list):
        for nested in value:
            assert_no_decimal_objects(nested)


def assert_no_float_or_int_values(value: Any) -> None:
    if isinstance(value, bool):
        return
    if isinstance(value, (float, int)):
        raise AssertionError(f"payload must not contain numeric JSON values: {value!r}")
    if isinstance(value, dict):
        for nested in value.values():
            assert_no_float_or_int_values(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            assert_no_float_or_int_values(nested)
