from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.strategy_recommendation_source_freshness_cost_gate_v2 import (
    PaperStrategyRecommendationSourceFreshnessCostGateV2Config,
    PaperStrategyRecommendationSourceFreshnessCostGateV2Input,
    PaperStrategyRecommendationSourceFreshnessCostGateV2ReasonCodeCount,
    PaperStrategyRecommendationSourceFreshnessCostGateV2Report,
    PaperStrategyRecommendationSourceFreshnessCostGateV2Row,
    build_paper_strategy_recommendation_source_freshness_cost_gate_v2_report,
    strategy_recommendation_source_freshness_cost_gate_v2_payload,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_recommendation_source_freshness_cost_gate_v2.py"
)
GENERATED_AT = datetime(2026, 7, 7, 14, 30, tzinfo=timezone(timedelta(hours=2)))
GENERATED_AT_UTC = datetime(2026, 7, 7, 12, 30, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: Decimal | str | bool) -> PaperStrategyRecommendationSourceFreshnessCostGateV2Config:
    values: dict[str, Decimal | str | bool] = {
        "config_version": "source-freshness-cost-gate-v2-test",
        "max_source_age_seconds": d("3600"),
        "min_evidence_source_count": d("3"),
        "min_fresh_source_count": d("2"),
        "max_taker_fee_per_share": d("0.015000"),
        "max_spread_cost_per_share": d("0.020000"),
        "max_slippage_cost_per_share": d("0.010000"),
        "max_total_cost_per_share": d("0.040000"),
        "max_settlement_lag_seconds": d("7200"),
        "min_liquidity_depth": d("500.000000"),
        "watch_band_ratio": d("0.900000"),
        "liquidity_watch_multiplier": d("1.250000"),
    }
    values.update(overrides)
    return PaperStrategyRecommendationSourceFreshnessCostGateV2Config(**values)


def candidate(
    recommendation_id: str,
    *,
    market_slug: str | None = None,
    side: str = "yes",
    source_count: Decimal = d("4"),
    fresh_source_count: Decimal = d("3"),
    source_age_seconds: Decimal = d("600"),
    taker_fee_per_share: Decimal = d("0.010000"),
    spread_cost_per_share: Decimal = d("0.015000"),
    slippage_cost_per_share: Decimal = d("0.005000"),
    settlement_lag_seconds: Decimal = d("3600"),
    liquidity_depth: Decimal = d("1000.000000"),
    reason_codes: tuple[str, ...] = ("team_recommendation_candidate",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> PaperStrategyRecommendationSourceFreshnessCostGateV2Input:
    return PaperStrategyRecommendationSourceFreshnessCostGateV2Input(
        recommendation_id=recommendation_id,
        market_slug=market_slug or f"{recommendation_id}-market",
        side=side,
        source_count=source_count,
        fresh_source_count=fresh_source_count,
        source_age_seconds=source_age_seconds,
        taker_fee_per_share=taker_fee_per_share,
        spread_cost_per_share=spread_cost_per_share,
        slippage_cost_per_share=slippage_cost_per_share,
        settlement_lag_seconds=settlement_lag_seconds,
        liquidity_depth=liquidity_depth,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(
    *candidates: PaperStrategyRecommendationSourceFreshnessCostGateV2Input,
    cfg: PaperStrategyRecommendationSourceFreshnessCostGateV2Config | None = None,
) -> PaperStrategyRecommendationSourceFreshnessCostGateV2Report:
    return build_paper_strategy_recommendation_source_freshness_cost_gate_v2_report(
        candidates,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_gate_combines_source_freshness_cost_lag_and_liquidity_with_stable_digest() -> None:
    ready = candidate("ready-alpha")
    watch = candidate(
        "watch-beta",
        fresh_source_count=d("2"),
        source_age_seconds=d("3400"),
        taker_fee_per_share=d("0.014000"),
        spread_cost_per_share=d("0.019000"),
        slippage_cost_per_share=d("0.005000"),
        settlement_lag_seconds=d("7000"),
        liquidity_depth=d("600.000000"),
    )
    blocked = candidate(
        "blocked-gamma",
        source_count=d("1"),
        fresh_source_count=d("0"),
        source_age_seconds=d("7201"),
        taker_fee_per_share=d("0.016000"),
        spread_cost_per_share=d("0.030000"),
        slippage_cost_per_share=d("0.005000"),
        settlement_lag_seconds=d("7201"),
        liquidity_depth=d("100.000000"),
    )

    report = build_report(ready, watch, blocked)
    same_report = build_report(blocked, ready, watch)

    assert report == same_report
    assert report.generated_at == GENERATED_AT_UTC
    assert report.config_version == "source-freshness-cost-gate-v2-test"
    assert report.recommendation_count == d("3")
    assert report.ready_count == d("1")
    assert report.watch_count == d("1")
    assert report.blocked_count == d("1")
    assert report.observed_average_total_cost_per_share == d("0.039667")
    assert report.observed_max_total_cost_per_share == d("0.051000")
    assert report.observed_max_settlement_lag_seconds == d("7201")
    assert report.observed_min_liquidity_depth == d("100.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.report_digest) == 64
    int(report.report_digest, 16)

    assert tuple(row.recommendation_id for row in report.rows) == (
        "blocked-gamma",
        "watch-beta",
        "ready-alpha",
    )
    rows_by_id = {row.recommendation_id: row for row in report.rows}
    assert rows_by_id["ready-alpha"].readiness_status == "ready"
    assert rows_by_id["ready-alpha"].total_cost_per_share == d("0.030000")
    assert rows_by_id["ready-alpha"].fresh_source_ratio == d("0.750000")
    assert rows_by_id["ready-alpha"].reason_codes == (
        "team_recommendation_candidate",
        "evidence_quorum_passed",
        "source_freshness_passed",
        "taker_fee_cost_within_limit",
        "spread_cost_within_limit",
        "slippage_cost_within_limit",
        "total_cost_within_limit",
        "settlement_lag_within_limit",
        "liquidity_depth_passed",
    )

    assert rows_by_id["watch-beta"].readiness_status == "watch"
    assert rows_by_id["watch-beta"].total_cost_per_share == d("0.038000")
    assert "source_freshness_near_limit" in rows_by_id["watch-beta"].reason_codes
    assert "taker_fee_cost_near_limit" in rows_by_id["watch-beta"].reason_codes
    assert "spread_cost_near_limit" in rows_by_id["watch-beta"].reason_codes
    assert "total_cost_near_limit" in rows_by_id["watch-beta"].reason_codes
    assert "settlement_lag_near_limit" in rows_by_id["watch-beta"].reason_codes
    assert "liquidity_depth_near_minimum" in rows_by_id["watch-beta"].reason_codes

    assert rows_by_id["blocked-gamma"].readiness_status == "blocked"
    assert rows_by_id["blocked-gamma"].total_cost_per_share == d("0.051000")
    assert "evidence_quorum_below_minimum" in rows_by_id["blocked-gamma"].reason_codes
    assert "source_freshness_below_minimum" in rows_by_id["blocked-gamma"].reason_codes
    assert "source_age_above_limit" in rows_by_id["blocked-gamma"].reason_codes
    assert "taker_fee_cost_above_limit" in rows_by_id["blocked-gamma"].reason_codes
    assert "spread_cost_above_limit" in rows_by_id["blocked-gamma"].reason_codes
    assert "total_cost_above_limit" in rows_by_id["blocked-gamma"].reason_codes
    assert "settlement_lag_above_limit" in rows_by_id["blocked-gamma"].reason_codes
    assert "liquidity_depth_below_minimum" in rows_by_id["blocked-gamma"].reason_codes

    assert report.reason_code_counts[:3] == (
        PaperStrategyRecommendationSourceFreshnessCostGateV2ReasonCodeCount(
            reason_code="slippage_cost_within_limit",
            count=d("3"),
            recommendation_ratio=d("1.000000"),
        ),
        PaperStrategyRecommendationSourceFreshnessCostGateV2ReasonCodeCount(
            reason_code="team_recommendation_candidate",
            count=d("3"),
            recommendation_ratio=d("1.000000"),
        ),
        PaperStrategyRecommendationSourceFreshnessCostGateV2ReasonCodeCount(
            reason_code="evidence_quorum_passed",
            count=d("2"),
            recommendation_ratio=d("0.666667"),
        ),
    )


def test_gate_payload_is_json_ready_decimal_string_report_only_output() -> None:
    report = build_report(candidate("payload-alpha"))

    payload = strategy_recommendation_source_freshness_cost_gate_v2_payload(report)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-07T12:30:00+00:00"
    assert payload["recommendation_count"] == "1"
    assert payload["ready_count"] == "1"
    assert payload["rows"][0]["total_cost_per_share"] == "0.030000"
    assert payload["rows"][0]["fresh_source_ratio"] == "0.750000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert report.report_digest in encoded
    assert_no_float_values(payload)


def test_gate_validates_exact_decimal_inputs_flags_immutability_and_consistency() -> None:
    report = build_report(candidate("valid-alpha"), candidate("valid-beta"))
    row = report.rows[0]

    with pytest.raises(FrozenInstanceError):
        row.readiness_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="taker_fee_per_share"):
        candidate("float-cost", taker_fee_per_share=0.01)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="min_evidence_source_count"):
        config(min_evidence_source_count=3)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="fresh_source_count"):
        candidate("too-fresh", source_count=d("1"), fresh_source_count=d("2"))
    with pytest.raises(ValueError, match="input paper_only"):
        build_report(candidate("paper-flag", paper_only=False))
    with pytest.raises(ValueError, match="timezone-aware"):
        build_paper_strategy_recommendation_source_freshness_cost_gate_v2_report(
            (candidate("naive-time"),),
            config=config(),
            generated_at=datetime(2026, 7, 7, 12, 30),
        )
    with pytest.raises(ValueError, match="ready_count"):
        replace(report, ready_count=d("0"))
    with pytest.raises(ValueError, match="deterministically sorted"):
        replace(report, rows=tuple(reversed(report.rows)))
    with pytest.raises(ValueError, match="report_digest"):
        replace(report, report_digest="0" * 64)

    for value in (report, row):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name.endswith(
                (
                    "_count",
                    "_seconds",
                    "_share",
                    "_depth",
                    "_ratio",
                ),
            ):
                assert type(item_value) is Decimal


def test_report_accepts_empty_input_with_zero_summaries() -> None:
    report = build_report()

    assert report.recommendation_count == d("0")
    assert report.ready_count == d("0")
    assert report.watch_count == d("0")
    assert report.blocked_count == d("0")
    assert report.observed_average_total_cost_per_share == d("0.000000")
    assert report.observed_max_total_cost_per_share == d("0.000000")
    assert report.observed_max_settlement_lag_seconds == d("0")
    assert report.observed_min_liquidity_depth == d("0.000000")
    assert report.rows == ()
    assert report.reason_code_counts == ()


def test_module_scope_has_only_readonly_report_only_paper_surfaces() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    source = MODULE_PATH.read_text(encoding="utf-8").lower()
    imports: list[str] = []
    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "db",
        "http",
        "network",
        "order",
        "psycopg",
        "request",
        "socket",
        "sql",
        "supabase",
        "urllib",
        "wallet",
    )
    forbidden_call_names = {
        "open",
        "read",
        "write",
        "connect",
        "execute",
        "fetch",
        "request",
        "submit",
        "cancel",
        "sign",
        "trade",
    }
    forbidden_attr_fragments = (
        "account",
        "auth",
        "broker",
        "cancel",
        "client",
        "connect",
        "db",
        "execute",
        "fetch",
        "file",
        "network",
        "order",
        "persist",
        "request",
        "submit",
        "trade",
        "wallet",
        "write",
    )

    assert ".action" not in source
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imports.append(node.module or "")
        elif isinstance(node, ast.Call):
            callee_name = None
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in forbidden_call_names
        elif isinstance(node, ast.Attribute):
            lowered = node.attr.lower()
            assert not any(fragment in lowered for fragment in forbidden_attr_fragments)

    assert imports
    for module_name in imports:
        assert not module_name.startswith("polymarket_alpha_lab.")
        lowered = module_name.lower()
        assert not any(fragment in lowered for fragment in forbidden_import_fragments)
