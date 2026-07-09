from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.research_market_settlement_cost_uncertainty_report as settlement_cost_report
from polymarket_alpha_lab.research_market_settlement_cost_uncertainty_report import (
    DEFAULT_RESEARCH_MARKET_SETTLEMENT_COST_UNCERTAINTY_CONFIG_VERSION,
    ResearchMarketSettlementCostUncertaintyCandidate,
    ResearchMarketSettlementCostUncertaintyConfig,
    ResearchMarketSettlementCostUncertaintyReasonCodeCount,
    ResearchMarketSettlementCostUncertaintyReport,
    ResearchMarketSettlementCostUncertaintyRow,
    build_research_market_settlement_cost_uncertainty_report,
    research_market_settlement_cost_uncertainty_digest,
    research_market_settlement_cost_uncertainty_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 14, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_market_settlement_cost_uncertainty_report.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchMarketSettlementCostUncertaintyConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_MARKET_SETTLEMENT_COST_UNCERTAINTY_CONFIG_VERSION
        ),
        "pass_max_uncertainty_cost_score": d("0.300000"),
        "watch_max_uncertainty_cost_score": d("0.650000"),
        "settlement_lag_watch_hours": d("24.000000"),
        "settlement_lag_block_hours": d("72.000000"),
        "fee_spread_haircut_watch_ratio": d("0.020000"),
        "fee_spread_haircut_block_ratio": d("0.060000"),
        "resolution_timing_watch_score": d("0.350000"),
        "resolution_timing_block_score": d("0.800000"),
        "market_mechanics_watch_score": d("0.300000"),
        "market_mechanics_block_score": d("0.750000"),
        "resolution_timing_weight": d("0.250000"),
        "settlement_lag_weight": d("0.250000"),
        "fee_spread_haircut_weight": d("0.250000"),
        "market_mechanics_weight": d("0.250000"),
    }
    values.update(overrides)
    return ResearchMarketSettlementCostUncertaintyConfig(**values)


def candidate(
    raw_candidate_id: str,
    *,
    observed_at: datetime = GENERATED_AT,
    resolution_timing_uncertainty: Decimal = d("0.100000"),
    settlement_lag_hours: Decimal = d("6.000000"),
    fee_spread_haircut_ratio: Decimal = d("0.006000"),
    market_mechanics_risk: Decimal = d("0.100000"),
    sensitive_context: str | None = (
        "market-id market-slug settlement question "
        "https://example.invalid/source source text postgres://host/db "
        "fills_table token abc wallet order trade buy sell recommend"
    ),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchMarketSettlementCostUncertaintyCandidate:
    return ResearchMarketSettlementCostUncertaintyCandidate(
        raw_candidate_id=raw_candidate_id,
        observed_at=observed_at,
        resolution_timing_uncertainty=resolution_timing_uncertainty,
        settlement_lag_hours=settlement_lag_hours,
        fee_spread_haircut_ratio=fee_spread_haircut_ratio,
        market_mechanics_risk=market_mechanics_risk,
        sensitive_context=sensitive_context,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *rows: ResearchMarketSettlementCostUncertaintyCandidate,
    cfg: ResearchMarketSettlementCostUncertaintyConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchMarketSettlementCostUncertaintyReport:
    return build_research_market_settlement_cost_uncertainty_report(
        rows,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def test_combines_resolution_lag_haircut_and_mechanics_into_pass_watch_block() -> None:
    uncertainty_report = report(
        candidate("raw-pass"),
        candidate(
            "raw-watch",
            resolution_timing_uncertainty=d("0.400000"),
            settlement_lag_hours=d("30.000000"),
            fee_spread_haircut_ratio=d("0.025000"),
            market_mechanics_risk=d("0.350000"),
        ),
        candidate(
            "raw-block",
            resolution_timing_uncertainty=d("0.850000"),
            settlement_lag_hours=d("96.000000"),
            fee_spread_haircut_ratio=d("0.080000"),
            market_mechanics_risk=d("0.800000"),
        ),
    )

    assert type(uncertainty_report) is ResearchMarketSettlementCostUncertaintyReport
    assert uncertainty_report.generated_at == GENERATED_AT
    assert uncertainty_report.config_version == (
        DEFAULT_RESEARCH_MARKET_SETTLEMENT_COST_UNCERTAINTY_CONFIG_VERSION
    )
    assert uncertainty_report.candidate_count == d("3.000000")
    assert uncertainty_report.pass_count == ONE
    assert uncertainty_report.watch_count == ONE
    assert uncertainty_report.block_count == ONE
    assert uncertainty_report.mean_uncertainty_cost_score == d("0.468056")
    assert uncertainty_report.mean_cost_drag_score == d("0.502778")
    assert uncertainty_report.max_settlement_lag_hours == d("96.000000")
    assert uncertainty_report.max_fee_spread_haircut_ratio == d("0.080000")
    assert uncertainty_report.status == "block"
    assert uncertainty_report.reason_codes == (
        "resolution_timing_uncertainty_detected",
        "settlement_lag_detected",
        "fee_spread_haircut_detected",
        "market_mechanics_risk_detected",
        "composite_settlement_cost_uncertainty_detected",
    )
    assert uncertainty_report.paper_only is True
    assert uncertainty_report.report_only is True
    assert uncertainty_report.readonly is True

    first, second, third = uncertainty_report.rows
    assert type(first) is ResearchMarketSettlementCostUncertaintyRow
    assert tuple(row.status for row in uncertainty_report.rows) == (
        "block",
        "watch",
        "pass",
    )
    assert first.row_number == ONE
    assert first.resolution_timing_uncertainty_score == d("0.850000")
    assert first.settlement_lag_score == ONE
    assert first.fee_spread_haircut_score == ONE
    assert first.market_mechanics_risk_score == d("0.800000")
    assert first.cost_drag_score == ONE
    assert first.uncertainty_cost_score == d("0.912500")
    assert first.reason_codes == (
        "resolution_timing_uncertainty_blocking",
        "settlement_lag_blocking",
        "fee_spread_haircut_blocking",
        "market_mechanics_risk_blocking",
        "composite_settlement_cost_uncertainty_blocking",
    )
    assert second.uncertainty_cost_score == d("0.395834")
    assert second.cost_drag_score == d("0.416667")
    assert second.reason_codes == (
        "resolution_timing_uncertainty_watch",
        "settlement_lag_watch",
        "fee_spread_haircut_watch",
        "market_mechanics_risk_watch",
        "composite_settlement_cost_uncertainty_watch",
    )
    assert third.uncertainty_cost_score == d("0.095833")
    assert third.cost_drag_score == d("0.091666")
    assert third.reason_codes == ("settlement_cost_uncertainty_clear",)


def test_payload_digest_is_deterministic_public_safe_and_decimal_only() -> None:
    left = report(
        candidate("raw-z-pass"),
        candidate(
            "raw-a-block",
            resolution_timing_uncertainty=d("0.850000"),
            settlement_lag_hours=d("96.000000"),
            fee_spread_haircut_ratio=d("0.080000"),
            market_mechanics_risk=d("0.800000"),
        ),
        candidate(
            "raw-m-watch",
            resolution_timing_uncertainty=d("0.400000"),
            settlement_lag_hours=d("30.000000"),
            fee_spread_haircut_ratio=d("0.025000"),
            market_mechanics_risk=d("0.350000"),
        ),
    )
    right = report(
        candidate(
            "raw-m-watch",
            resolution_timing_uncertainty=d("0.400000"),
            settlement_lag_hours=d("30.000000"),
            fee_spread_haircut_ratio=d("0.025000"),
            market_mechanics_risk=d("0.350000"),
        ),
        candidate("raw-z-pass"),
        candidate(
            "raw-a-block",
            resolution_timing_uncertainty=d("0.850000"),
            settlement_lag_hours=d("96.000000"),
            fee_spread_haircut_ratio=d("0.080000"),
            market_mechanics_risk=d("0.800000"),
        ),
    )

    left_payload = research_market_settlement_cost_uncertainty_report_payload(left)
    right_payload = research_market_settlement_cost_uncertainty_report_payload(right)

    assert left_payload == right_payload
    assert research_market_settlement_cost_uncertainty_digest(left) == (
        left.public_report_digest
    )
    assert left.public_report_digest == right.public_report_digest
    assert len(left.public_report_digest) == 64
    assert left_payload["candidate_count"] == "3.000000"
    assert left_payload["rows"][0]["uncertainty_cost_score"] == "0.912500"
    assert_no_float(left_payload)
    json.dumps(left_payload, sort_keys=True)

    encoded = json.dumps(left_payload, sort_keys=True)
    for sensitive_value in (
        "raw-z-pass",
        "raw-a-block",
        "raw-m-watch",
        "market-id",
        "market-slug",
        "settlement question",
        "https://example.invalid/source",
        "source text",
        "postgres://host/db",
        "fills_table",
        "token abc",
        "wallet order trade",
        "buy sell recommend",
    ):
        assert sensitive_value not in encoded
    for sensitive_key in (
        "raw_candidate_id",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
    ):
        assert sensitive_key not in encoded

    object.__setattr__(left, "public_report_digest", "0" * 64)
    with pytest.raises(ValueError, match="public_report_digest"):
        research_market_settlement_cost_uncertainty_report_payload(left)


def test_payload_revalidates_public_schema_and_rejects_unsafe_tampering() -> None:
    uncertainty_report = report(candidate("schema-safe"))

    object.__setattr__(uncertainty_report, "config_version", "wallet-order-trade")

    with pytest.raises(ValueError, match="unsafe public value"):
        research_market_settlement_cost_uncertainty_report_payload(uncertainty_report)


def test_payload_rejects_public_numeric_drift_after_report_tamper() -> None:
    uncertainty_report = report(candidate("numeric-safe"))

    object.__setattr__(uncertainty_report.rows[0], "row_number", 1)

    with pytest.raises(ValueError, match="Decimal-derived"):
        research_market_settlement_cost_uncertainty_report_payload(uncertainty_report)


def test_payload_rejects_unexpected_public_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    uncertainty_report = report(candidate("field-safe"))
    original_payload = settlement_cost_report._report_payload_without_digest_from_report

    def payload_with_extra_field(
        item: ResearchMarketSettlementCostUncertaintyReport,
    ) -> dict[str, Any]:
        payload = original_payload(item)
        payload["market_slug"] = "redacted"
        return payload

    monkeypatch.setattr(
        settlement_cost_report,
        "_report_payload_without_digest_from_report",
        payload_with_extra_field,
    )

    with pytest.raises(ValueError, match="unexpected public field"):
        research_market_settlement_cost_uncertainty_report_payload(uncertainty_report)


def test_empty_inputs_block_with_public_reason_count() -> None:
    uncertainty_report = report()

    assert uncertainty_report.status == "block"
    assert uncertainty_report.candidate_count == ZERO
    assert uncertainty_report.reason_codes == (
        "no_settlement_cost_uncertainty_candidates",
    )
    assert uncertainty_report.reason_code_counts == (
        ResearchMarketSettlementCostUncertaintyReasonCodeCount(
            reason_code="no_settlement_cost_uncertainty_candidates",
            count=ONE,
        ),
    )
    assert uncertainty_report.rows == ()


def test_composite_threshold_max_values_are_inclusive() -> None:
    pass_threshold_report = report(
        candidate(
            "exact-pass-max",
            resolution_timing_uncertainty=d("0.340000"),
            settlement_lag_hours=d("21.600000"),
            fee_spread_haircut_ratio=d("0.018000"),
            market_mechanics_risk=d("0.260000"),
        ),
    )
    watch_threshold_report = report(
        candidate(
            "exact-watch-max",
            resolution_timing_uncertainty=d("0.650000"),
            settlement_lag_hours=d("46.800000"),
            fee_spread_haircut_ratio=d("0.039000"),
            market_mechanics_risk=d("0.650000"),
        ),
    )

    assert pass_threshold_report.rows[0].uncertainty_cost_score == d("0.300000")
    assert pass_threshold_report.rows[0].status == "pass"
    assert pass_threshold_report.rows[0].reason_codes == (
        "settlement_cost_uncertainty_clear",
    )
    assert watch_threshold_report.rows[0].uncertainty_cost_score == d("0.650000")
    assert watch_threshold_report.rows[0].status == "watch"
    assert "composite_settlement_cost_uncertainty_blocking" not in (
        watch_threshold_report.rows[0].reason_codes
    )


def test_validation_rejects_non_decimal_bad_time_bad_status_and_flags() -> None:
    with pytest.raises(ValueError, match="settlement_lag_hours"):
        candidate("bad-int", settlement_lag_hours=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="fee_spread_haircut_ratio"):
        candidate("bad-float", fee_spread_haircut_ratio=0.01)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="market_mechanics_risk"):
        candidate("bad-subclass", market_mechanics_risk=_DecimalSubclass("0.1"))
    with pytest.raises(ValueError, match="observed_at"):
        candidate("bad-time", observed_at=datetime(2026, 7, 8, 14, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(candidate("ok"), generated_at=datetime(2026, 7, 8, 14, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            candidate("subclass-time"),
            generated_at=_DatetimeSubclass(2026, 7, 8, 14, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="paper_only"):
        candidate("bad-flag", paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report(candidate("flag-report")), readonly=False)
    with pytest.raises(ValueError, match="settlement_lag_block_hours must exceed"):
        config(settlement_lag_block_hours=d("24.000000"))

    uncertainty_report = report(candidate("status-check"))
    with pytest.raises(ValueError, match="status"):
        replace(uncertainty_report.rows[0], status="blocked")


def test_public_dataclasses_are_frozen_and_module_has_no_live_surfaces() -> None:
    uncertainty_report = report(candidate("frozen"))

    with pytest.raises(FrozenInstanceError):
        uncertainty_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        uncertainty_report.rows[0].uncertainty_cost_score = d("0.500000")  # type: ignore[misc]

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "connect(",
        "open(",
        "write_text",
        "write_bytes",
        "create_order",
        "cancel_order",
        "private_key",
        "api_key",
        "secret",
        "sizing",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "urllib",
        "httpx",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "post",
        "request",
        "send",
        "write",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls


def assert_no_float(value: Any) -> None:
    if isinstance(value, float):
        pytest.fail(f"found float in payload: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float(item)
