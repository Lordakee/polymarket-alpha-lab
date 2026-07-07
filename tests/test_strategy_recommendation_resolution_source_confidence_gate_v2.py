from __future__ import annotations

import ast
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest

import polymarket_alpha_lab.strategy_recommendation_resolution_source_confidence_gate_v2 as api


GENERATED_AT = datetime(2026, 7, 7, 14, 0, tzinfo=timezone(timedelta(hours=2)))
GENERATED_AT_UTC = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object) -> api.StrategyRecommendationResolutionSourceConfidenceGateV2Config:
    values: dict[str, object] = {
        "config_version": api.DEFAULT_STRATEGY_RECOMMENDATION_RESOLUTION_SOURCE_CONFIDENCE_GATE_V2_CONFIG_VERSION,
        "min_official_source_hierarchy_score": d("0.800000"),
        "min_rule_criteria_match_score": d("0.850000"),
        "max_resolution_source_age_seconds": d("3600.000000"),
        "source_age_watch_ratio": d("0.800000"),
        "max_watch_contradiction_severity_score": d("0.100000"),
        "max_block_contradiction_severity_score": d("0.300000"),
        "max_watch_settlement_lag_seconds": d("7200.000000"),
        "max_block_settlement_lag_seconds": d("21600.000000"),
        "min_ready_cost_adjusted_edge_buffer_probability": d("0.030000"),
        "min_watch_cost_adjusted_edge_buffer_probability": d("0.010000"),
    }
    values.update(overrides)
    return api.StrategyRecommendationResolutionSourceConfidenceGateV2Config(**values)


def candidate(
    recommendation_id: str = "candidate-ready",
    *,
    market_slug: str | None = None,
    side: str = "yes",
    forecast_probability: Decimal = d("0.610000"),
    market_probability: Decimal = d("0.550000"),
    fee_cost_probability: Decimal = d("0.010000"),
    spread_cost_probability: Decimal = d("0.005000"),
    settlement_lag_cost_probability: Decimal = d("0.005000"),
    official_source_hierarchy_score: Decimal = d("0.950000"),
    rule_criteria_match_score: Decimal = d("0.900000"),
    resolution_source_observed_at: datetime = GENERATED_AT_UTC - timedelta(seconds=600),
    contradiction_severity_score: Decimal = d("0.020000"),
    settlement_lag_seconds: Decimal = d("3600.000000"),
    reason_codes: tuple[str, ...] = ("resolution_packet_ready",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> api.StrategyRecommendationResolutionSourceConfidenceGateV2Input:
    return api.StrategyRecommendationResolutionSourceConfidenceGateV2Input(
        recommendation_id=recommendation_id,
        market_slug=market_slug or f"{recommendation_id}-market",
        side=side,
        forecast_probability=forecast_probability,
        market_probability=market_probability,
        fee_cost_probability=fee_cost_probability,
        spread_cost_probability=spread_cost_probability,
        settlement_lag_cost_probability=settlement_lag_cost_probability,
        official_source_hierarchy_score=official_source_hierarchy_score,
        rule_criteria_match_score=rule_criteria_match_score,
        resolution_source_observed_at=resolution_source_observed_at,
        contradiction_severity_score=contradiction_severity_score,
        settlement_lag_seconds=settlement_lag_seconds,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(
    *items: api.StrategyRecommendationResolutionSourceConfidenceGateV2Input,
    config: api.StrategyRecommendationResolutionSourceConfidenceGateV2Config | None = None,
    generated_at: datetime = GENERATED_AT,
) -> api.StrategyRecommendationResolutionSourceConfidenceGateV2Report:
    return api.build_strategy_recommendation_resolution_source_confidence_gate_v2_report(
        items,
        config=config or cfg(),
        generated_at=generated_at,
    )


def assert_no_public_numeric(value: object) -> None:
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, (Decimal, float, int)):
        raise AssertionError(f"unexpected public numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_public_numeric(item)


def unsafe_text(*parts: str) -> str:
    return "".join(parts)


def test_resolution_source_confidence_gate_rollups_with_stable_digest() -> None:
    ready = candidate("ready-alpha")
    watch = candidate(
        "watch-beta",
        forecast_probability=d("0.600000"),
        market_probability=d("0.550000"),
        fee_cost_probability=d("0.015000"),
        spread_cost_probability=d("0.010000"),
        settlement_lag_cost_probability=d("0.005000"),
        resolution_source_observed_at=GENERATED_AT_UTC - timedelta(seconds=3000),
        contradiction_severity_score=d("0.150000"),
        settlement_lag_seconds=d("8000.000000"),
    )
    blocked = candidate(
        "blocked-gamma",
        forecast_probability=d("0.570000"),
        market_probability=d("0.550000"),
        fee_cost_probability=d("0.015000"),
        spread_cost_probability=d("0.010000"),
        settlement_lag_cost_probability=d("0.005000"),
        official_source_hierarchy_score=d("0.500000"),
        rule_criteria_match_score=d("0.700000"),
        resolution_source_observed_at=GENERATED_AT_UTC - timedelta(seconds=4000),
        contradiction_severity_score=d("0.350000"),
        settlement_lag_seconds=d("21601.000000"),
    )

    report = build_report(watch, ready, blocked)
    same_report = build_report(blocked, watch, ready)

    assert report == same_report
    assert report.generated_at == GENERATED_AT_UTC
    assert report.recommendation_count == d("3.000000")
    assert report.ready_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.blocked_count == d("1.000000")
    assert report.total_cost_adjusted_edge_buffer_probability == d("0.050000")
    assert report.min_cost_adjusted_edge_buffer_probability == d("-0.010000")
    assert report.max_resolution_source_age_seconds == d("4000.000000")
    assert report.max_settlement_lag_seconds == d("21601.000000")
    assert report.min_official_source_hierarchy_score == d("0.500000")
    assert report.min_rule_criteria_match_score == d("0.700000")
    assert report.readiness_status == "blocked"
    assert report.recommended_next_step == "block_report_only_resolution_source_confidence"
    assert report.reason_codes == (
        "official_source_hierarchy_below_minimum",
        "rule_criteria_match_below_minimum",
        "resolution_source_stale",
        "resolution_source_near_stale",
        "contradiction_severity_blocking",
        "contradiction_severity_watch",
        "settlement_lag_blocking",
        "settlement_lag_watch",
        "cost_adjusted_edge_buffer_below_watch",
        "cost_adjusted_edge_buffer_below_ready",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64
    int(report.derived_validation_digest, 16)

    assert tuple(row.recommendation_id for row in report.rows) == (
        "blocked-gamma",
        "watch-beta",
        "ready-alpha",
    )
    rows = {row.recommendation_id: row for row in report.rows}

    assert rows["ready-alpha"].readiness_status == "ready"
    assert rows["ready-alpha"].gross_edge_probability == d("0.060000")
    assert rows["ready-alpha"].total_cost_probability == d("0.020000")
    assert rows["ready-alpha"].cost_adjusted_edge_buffer_probability == d("0.040000")
    assert rows["ready-alpha"].reason_codes == (
        "resolution_source_confidence_gate_passed",
    )

    assert rows["watch-beta"].readiness_status == "watch"
    assert rows["watch-beta"].resolution_source_age_seconds == d("3000.000000")
    assert rows["watch-beta"].cost_adjusted_edge_buffer_probability == d("0.020000")
    assert rows["watch-beta"].reason_codes == (
        "resolution_source_near_stale",
        "contradiction_severity_watch",
        "settlement_lag_watch",
        "cost_adjusted_edge_buffer_below_ready",
    )

    assert rows["blocked-gamma"].readiness_status == "blocked"
    assert rows["blocked-gamma"].cost_adjusted_edge_buffer_probability == d("-0.010000")
    assert rows["blocked-gamma"].reason_codes == (
        "official_source_hierarchy_below_minimum",
        "rule_criteria_match_below_minimum",
        "resolution_source_stale",
        "contradiction_severity_blocking",
        "settlement_lag_blocking",
        "cost_adjusted_edge_buffer_below_watch",
    )
    assert len({row.derived_validation_digest for row in report.rows}) == 3

    assert report.reason_code_counts[0] == (
        api.StrategyRecommendationResolutionSourceConfidenceGateV2ReasonCodeCount(
            reason_code="official_source_hierarchy_below_minimum",
            count=d("1.000000"),
            recommendation_ratio=d("0.333333"),
        )
    )


def test_public_payload_decimal_strings_and_digest_validation() -> None:
    report = build_report(candidate("payload-alpha"))

    payload = api.strategy_recommendation_resolution_source_confidence_gate_v2_public_payload(
        report,
    )

    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["recommendation_count"] == "1.000000"
    assert payload["ready_count"] == "1.000000"
    assert payload["total_cost_adjusted_edge_buffer_probability"] == "0.040000"
    assert payload["rows"][0]["resolution_source_observed_at"] == "2026-07-07T11:50:00+00:00"
    assert payload["rows"][0]["gross_edge_probability"] == "0.060000"
    assert payload["rows"][0]["cost_adjusted_edge_buffer_probability"] == "0.040000"
    assert payload["rows"][0]["derived_validation_digest"] == report.rows[0].derived_validation_digest
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert api.validate_strategy_recommendation_resolution_source_confidence_gate_v2_public_payload(
        payload,
    )
    assert_no_public_numeric(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)

    tampered_payload = {**payload, "ready_count": "0.000000"}
    with pytest.raises(ValueError, match="derived_validation_digest"):
        api.validate_strategy_recommendation_resolution_source_confidence_gate_v2_public_payload(
            tampered_payload,
        )

    numeric_payload = {**payload, "recommendation_count": 1}
    with pytest.raises(ValueError, match="public payload"):
        api.validate_strategy_recommendation_resolution_source_confidence_gate_v2_public_payload(
            numeric_payload,
        )


def test_dataclasses_are_frozen_exact_decimal_flags_and_consistency() -> None:
    assert api.__all__ == (
        "DEFAULT_STRATEGY_RECOMMENDATION_RESOLUTION_SOURCE_CONFIDENCE_GATE_V2_CONFIG_VERSION",
        "StrategyRecommendationResolutionSourceConfidenceGateV2Config",
        "StrategyRecommendationResolutionSourceConfidenceGateV2Input",
        "StrategyRecommendationResolutionSourceConfidenceGateV2ReasonCodeCount",
        "StrategyRecommendationResolutionSourceConfidenceGateV2Report",
        "StrategyRecommendationResolutionSourceConfidenceGateV2Row",
        "build_strategy_recommendation_resolution_source_confidence_gate_v2_report",
        "strategy_recommendation_resolution_source_confidence_gate_v2_public_payload",
        "validate_strategy_recommendation_resolution_source_confidence_gate_v2_public_payload",
    )
    for exported_name in api.__all__:
        exported = getattr(api, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)
            assert exported.__dataclass_params__.frozen is True

    report = build_report(candidate("valid-alpha"), candidate("valid-beta"))
    row = report.rows[0]
    with pytest.raises(FrozenInstanceError):
        row.readiness_status = "ready"  # type: ignore[misc]
    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeConfig(api.StrategyRecommendationResolutionSourceConfidenceGateV2Config):
            pass

    with pytest.raises(ValueError, match="forecast_probability must be a Decimal"):
        candidate("float-probability", forecast_probability=0.61)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="max_resolution_source_age_seconds"):
        cfg(max_resolution_source_age_seconds=3600)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only must be True"):
        candidate("bad-flag", paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(cfg(), readonly=False)
    with pytest.raises(ValueError, match="timezone-aware"):
        build_report(candidate("naive"), generated_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="after generated_at"):
        build_report(
            candidate(
                "future-source",
                resolution_source_observed_at=GENERATED_AT_UTC + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="duplicate recommendation_id"):
        build_report(candidate("duplicate"), candidate("duplicate", market_slug="duplicate-b"))
    with pytest.raises(ValueError, match="deterministic sequence"):
        replace(report, rows=tuple(reversed(report.rows)))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    for value in (cfg(), candidate(), row, report):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for field in fields(value):
            item = getattr(value, field.name)
            if field.name.endswith(
                (
                    "_count",
                    "_probability",
                    "_score",
                    "_seconds",
                    "_ratio",
                ),
            ):
                assert item is None or type(item) is Decimal


def test_empty_report_is_readonly_report_only_paper_only_zeroed() -> None:
    report = build_report()

    assert report.recommendation_count == d("0.000000")
    assert report.ready_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.blocked_count == d("0.000000")
    assert report.total_cost_adjusted_edge_buffer_probability == d("0.000000")
    assert report.min_cost_adjusted_edge_buffer_probability == d("0.000000")
    assert report.max_resolution_source_age_seconds == d("0.000000")
    assert report.max_settlement_lag_seconds == d("0.000000")
    assert report.min_official_source_hierarchy_score == d("0.000000")
    assert report.min_rule_criteria_match_score == d("0.000000")
    assert report.readiness_status == "ready"
    assert report.recommended_next_step == "continue_report_only_resolution_source_confidence"
    assert report.reason_codes == ("resolution_source_confidence_gate_empty",)
    assert report.reason_code_counts == ()
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64
    int(report.derived_validation_digest, 16)


def test_static_module_has_no_external_or_action_surfaces() -> None:
    public_names = set(api.__all__) | {name for name in dir(api) if not name.startswith("_")}
    unsafe_terms = (
        "db",
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
    for public_name in public_names:
        lowered = public_name.lower()
        for term in unsafe_terms:
            assert term not in lowered

    source = inspect.getsource(api)
    lowered_source = source.lower()
    forbidden_source_fragments = (
        "asyncio",
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "supabase",
        "subprocess",
        "py_clob_client",
        "web3",
        "private_key",
        "api_key",
        unsafe_text("wal", "let"),
        unsafe_text("net", "work", "_client"),
        unsafe_text("data", "base", "_url"),
        unsafe_text("per", "sist", "_path"),
        "place_" + unsafe_text("ord", "er"),
        "create_" + unsafe_text("ord", "er"),
        "cancel_" + unsafe_text("ord", "er"),
        "submit_" + unsafe_text("ord", "er"),
        unsafe_text("li", "ve", "_trading"),
        unsafe_text("tra", "de", "_executor"),
        "open(",
        ".write(",
        ".read(",
    )
    for fragment in forbidden_source_fragments:
        assert fragment not in lowered_source

    forbidden_call_names = {
        "connect",
        "execute",
        "executemany",
        "open",
        "request",
        "post",
        "put",
        "patch",
        "read",
        "write",
        "submit",
        "cancel",
        "sign",
    }
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in forbidden_call_names
