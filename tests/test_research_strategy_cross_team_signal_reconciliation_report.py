from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_strategy_cross_team_signal_reconciliation_report"
)
GENERATED_AT = datetime(2026, 7, 8, 14, 30, tzinfo=UTC)


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "team_count_floor": d("2"),
        "signal_strength_pass_floor": d("0.650000"),
        "source_authority_pass_floor": d("0.700000"),
        "calibration_history_pass_floor": d("0.700000"),
        "cost_drag_watch_ceiling": d("0.300000"),
        "cost_drag_block_ceiling": d("0.600000"),
        "liquidity_reliability_watch_floor": d("0.450000"),
        "liquidity_reliability_pass_floor": d("0.700000"),
        "resolution_clarity_watch_floor": d("0.450000"),
        "resolution_clarity_pass_floor": d("0.700000"),
        "review_readiness_watch_floor": d("0.450000"),
        "review_readiness_pass_floor": d("0.700000"),
        "conflict_pressure_watch_threshold": d("0.250000"),
        "conflict_pressure_block_threshold": d("0.500000"),
    }
    values.update(overrides)
    return module.ResearchStrategyCrossTeamSignalReconciliationConfig(**values)


def signal(**overrides: object) -> Any:
    module = api()
    values = {
        "signal_ref": "sig-alpha",
        "team_code": "macro-team",
        "signal_direction": "support",
        "signal_strength": d("0.900000"),
        "source_authority": d("0.850000"),
        "calibration_history": d("0.800000"),
        "cost_drag": d("0.100000"),
        "liquidity_reliability": d("0.900000"),
        "resolution_clarity": d("0.850000"),
    }
    values.update(overrides)
    return module.ResearchStrategyCrossTeamSignalInput(**values)


def report(*rows: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_strategy_cross_team_signal_reconciliation_report(
        rows,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def assert_digest(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def assert_numeric_fields_are_decimal(value: object) -> None:
    for field in fields(value):
        item = getattr(value, field.name)
        if type(item) is bool:
            continue
        assert type(item) is not float
        assert type(item) is not int
        if isinstance(item, tuple):
            for nested in item:
                if is_dataclass(nested):
                    assert_numeric_fields_are_decimal(nested)


def assert_no_float_or_int_values(value: object) -> None:
    assert type(value) is not float
    assert type(value) is not int
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_or_int_values(item)


def test_reconciles_conflicting_team_signals_deterministically() -> None:
    result = report(
        signal(
            signal_ref="sig-neutral-watch",
            team_code="liquidity-team",
            signal_direction="neutral",
            signal_strength=d("0.500000"),
            source_authority=d("0.650000"),
            calibration_history=d("0.600000"),
            cost_drag=d("0.350000"),
            liquidity_reliability=d("0.650000"),
            resolution_clarity=d("0.600000"),
        ),
        signal(
            signal_ref="sig-support-strong",
            team_code="macro-team",
            signal_direction="support",
            signal_strength=d("0.900000"),
            source_authority=d("0.850000"),
            calibration_history=d("0.800000"),
            cost_drag=d("0.100000"),
            liquidity_reliability=d("0.900000"),
            resolution_clarity=d("0.850000"),
        ),
        signal(
            signal_ref="sig-oppose-strong",
            team_code="resolution-team",
            signal_direction="oppose",
            signal_strength=d("0.800000"),
            source_authority=d("0.750000"),
            calibration_history=d("0.700000"),
            cost_drag=d("0.200000"),
            liquidity_reliability=d("0.800000"),
            resolution_clarity=d("0.750000"),
        ),
        signal(
            signal_ref="sig-neutral-pass",
            team_code="calibration-team",
            signal_direction="neutral",
            signal_strength=d("0.800000"),
            source_authority=d("0.750000"),
            calibration_history=d("0.800000"),
            cost_drag=d("0.100000"),
            liquidity_reliability=d("0.750000"),
            resolution_clarity=d("0.800000"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == (
        "research-strategy-cross-team-signal-reconciliation-report-v1"
    )
    assert result.signal_count == d("4")
    assert result.team_count == d("4")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.block_count == d("2")
    assert result.conflict_pressure_score == d("0.766667")
    assert result.min_review_readiness_score == d("0.608333")
    assert result.report_status == "block"
    assert result.reason_codes == (
        "cross_team_conflict_block",
        "signal_strength_watch",
        "source_authority_watch",
        "calibration_history_watch",
        "cost_drag_watch",
        "liquidity_reliability_watch",
        "resolution_clarity_watch",
        "review_readiness_watch",
        "cross_team_signal_reconciliation_pass",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_digest(result.validation_digest)
    assert_numeric_fields_are_decimal(result)

    assert tuple(row.signal_ref for row in result.rows) == (
        "sig-oppose-strong",
        "sig-support-strong",
        "sig-neutral-watch",
        "sig-neutral-pass",
    )

    oppose = result.rows[0]
    assert oppose.status == "block"
    assert oppose.authority_calibrated_strength == d("0.580000")
    assert oppose.cost_adjusted_liquidity_score == d("0.800000")
    assert oppose.review_readiness_score == d("0.766667")
    assert oppose.opposing_signal_pressure == d("0.866667")
    assert oppose.reason_codes == ("cross_team_conflict_block",)
    assert_digest(oppose.validation_digest)

    support = result.rows[1]
    assert support.status == "block"
    assert support.review_readiness_score == d("0.866667")
    assert support.opposing_signal_pressure == d("0.766667")
    assert support.reason_codes == ("cross_team_conflict_block",)

    watched = result.rows[2]
    assert watched.status == "watch"
    assert watched.authority_calibrated_strength == d("0.312500")
    assert watched.cost_adjusted_liquidity_score == d("0.650000")
    assert watched.review_readiness_score == d("0.608333")
    assert watched.opposing_signal_pressure == d("0.000000")
    assert watched.reason_codes == (
        "signal_strength_watch",
        "source_authority_watch",
        "calibration_history_watch",
        "cost_drag_watch",
        "liquidity_reliability_watch",
        "resolution_clarity_watch",
        "review_readiness_watch",
    )

    passed = result.rows[3]
    assert passed.status == "pass"
    assert passed.review_readiness_score == d("0.800000")
    assert passed.reason_codes == ("cross_team_signal_reconciliation_pass",)

    same_result = report(
        signal(
            signal_ref="sig-neutral-pass",
            team_code="calibration-team",
            signal_direction="neutral",
            signal_strength=d("0.800000"),
            source_authority=d("0.750000"),
            calibration_history=d("0.800000"),
            cost_drag=d("0.100000"),
            liquidity_reliability=d("0.750000"),
            resolution_clarity=d("0.800000"),
        ),
        signal(
            signal_ref="sig-oppose-strong",
            team_code="resolution-team",
            signal_direction="oppose",
            signal_strength=d("0.800000"),
            source_authority=d("0.750000"),
            calibration_history=d("0.700000"),
            cost_drag=d("0.200000"),
            liquidity_reliability=d("0.800000"),
            resolution_clarity=d("0.750000"),
        ),
        signal(
            signal_ref="sig-support-strong",
            team_code="macro-team",
            signal_direction="support",
            signal_strength=d("0.900000"),
            source_authority=d("0.850000"),
            calibration_history=d("0.800000"),
            cost_drag=d("0.100000"),
            liquidity_reliability=d("0.900000"),
            resolution_clarity=d("0.850000"),
        ),
        signal(
            signal_ref="sig-neutral-watch",
            team_code="liquidity-team",
            signal_direction="neutral",
            signal_strength=d("0.500000"),
            source_authority=d("0.650000"),
            calibration_history=d("0.600000"),
            cost_drag=d("0.350000"),
            liquidity_reliability=d("0.650000"),
            resolution_clarity=d("0.600000"),
        ),
    )
    assert same_result.validation_digest == result.validation_digest


def test_empty_report_blocks_with_hard_flags_and_digest() -> None:
    result = report()

    assert result.signal_count == d("0")
    assert result.team_count == d("0")
    assert result.pass_count == d("0")
    assert result.watch_count == d("0")
    assert result.block_count == d("0")
    assert result.conflict_pressure_score == d("0.000000")
    assert result.min_review_readiness_score is None
    assert result.report_status == "block"
    assert result.reason_codes == ("cross_team_signal_reconciliation_empty",)
    assert result.rows == ()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_digest(result.validation_digest)


def test_payload_is_json_ready_and_rejects_sensitive_surfaces() -> None:
    module = api()
    result = report(signal())

    payload = module.research_strategy_cross_team_signal_reconciliation_report_payload(
        result,
    )
    encoded = json.dumps(payload, sort_keys=True, allow_nan=False)

    assert payload["generated_at"] == "2026-07-08T14:30:00+00:00"
    assert payload["signal_count"] == "1"
    assert payload["rows"][0]["signal_strength"] == "0.900000"
    assert payload["rows"][0]["validation_digest"] == result.rows[0].validation_digest
    assert_no_float_or_int_values(payload)
    assert (
        module.research_strategy_cross_team_signal_reconciliation_report_payload(
            payload,
        )
        == payload
    )

    forbidden_public_terms = (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "https://",
        "postgres://",
        "database",
        "network",
        "recommendation",
        "execution",
        "source_url",
        "source_text",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "table",
        "table_name",
        "raw_text",
    )
    for term in forbidden_public_terms:
        assert term not in encoded

    unsafe_payloads = (
        {**payload, "candidate_id": "abc"},
        {**payload, "market_slug": "abc"},
        {**payload, "question": "abc"},
        {**payload, "source": "https://example.test/path"},
        {**payload, "source_url": "abc"},
        {**payload, "source_text": "abc"},
        {**payload, "storage": "postgres://example.test/db"},
        {**payload, "database": "abc"},
        {**payload, "network": "abc"},
        {**payload, "recommendation": "abc"},
        {**payload, "execution": "abc"},
        {**payload, "token": "secret"},
        {**payload, "wallet": "abc"},
        {**payload, "order": "abc"},
        {**payload, "trade": "abc"},
        {**payload, "live": "abc"},
        {**payload, "table": "abc"},
        {**payload, "table_name": "abc"},
        {**payload, "raw_text": "abc"},
    )
    for unsafe_payload in unsafe_payloads:
        with pytest.raises(ValueError, match="unsafe"):
            module.research_strategy_cross_team_signal_reconciliation_report_payload(
                unsafe_payload,
            )

    with pytest.raises(ValueError, match="readonly"):
        module.research_strategy_cross_team_signal_reconciliation_report_payload(
            {**payload, "readonly": False},
        )

    with pytest.raises(ValueError, match="numeric"):
        module.research_strategy_cross_team_signal_reconciliation_report_payload(
            {**payload, "signal_count": 1},
        )

    with pytest.raises(ValueError, match="numeric"):
        module.research_strategy_cross_team_signal_reconciliation_report_payload(
            {**payload, "conflict_pressure_score": 1.0},
        )


def test_inputs_config_datetimes_and_flags_reject_invalid_values() -> None:
    module = api()

    with pytest.raises(ValueError, match="signal_strength must be a Decimal"):
        signal(signal_strength=1)
    with pytest.raises(ValueError, match="cost_drag must be between 0 and 1"):
        signal(cost_drag=d("-0.000001"))
    with pytest.raises(ValueError, match="signal_direction"):
        signal(signal_direction="lean-long")
    with pytest.raises(ValueError, match="paper_only must be True"):
        signal(paper_only=False)
    with pytest.raises(ValueError, match="team_count_floor"):
        config(team_count_floor=d("0"))
    with pytest.raises(ValueError, match="cost_drag_watch_ceiling"):
        config(
            cost_drag_watch_ceiling=d("0.700000"),
            cost_drag_block_ceiling=d("0.600000"),
        )
    with pytest.raises(ValueError, match="conflict_pressure_watch_threshold"):
        config(
            conflict_pressure_watch_threshold=d("0.700000"),
            conflict_pressure_block_threshold=d("0.600000"),
        )
    with pytest.raises(ValueError, match="report_only must be True"):
        config(report_only=False)

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_strategy_cross_team_signal_reconciliation_report(
            (signal(),),
            config=config(),
            generated_at=datetime(2026, 7, 8, 14, 30),
        )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_strategy_cross_team_signal_reconciliation_report(
            (signal(),),
            config=config(),
            generated_at=datetime(2026, 7, 8, 14, 30, tzinfo=_NoneOffsetTimezone()),
        )

    with pytest.raises(ValueError, match="signal_ref values must be unique"):
        report(signal(), signal(team_code="second-team"))

    result = report(signal())
    with pytest.raises(FrozenInstanceError):
        result.rows[0].status = "block"


def test_validation_digest_and_report_validation_recompute_fields() -> None:
    result = report(signal())
    row = result.rows[0]

    with pytest.raises(ValueError, match="review_readiness_score must match"):
        replace(row, review_readiness_score=row.review_readiness_score + d("0.000001"))

    with pytest.raises(ValueError, match="status must match"):
        replace(row, status="watch")

    with pytest.raises(ValueError, match="validation_digest must match"):
        replace(row, validation_digest="0" * 64)

    with pytest.raises(ValueError, match="pass_count must match"):
        replace(result, pass_count=result.pass_count + d("1"))

    with pytest.raises(ValueError, match="rows must be sorted deterministically"):
        replace(
            result,
            rows=(
                reconciliation_row("sig-zeta"),
                reconciliation_row("sig-alpha"),
            ),
        )

    with pytest.raises(ValueError, match="validation_digest must match"):
        replace(result, validation_digest="0" * 64)


def reconciliation_row(signal_ref: str) -> Any:
    return report(signal(signal_ref=signal_ref)).rows[0]


def test_module_scope_is_report_only_readonly_and_public_api_is_narrow() -> None:
    module = api()
    path = Path(
        "src/polymarket_alpha_lab/"
        "research_strategy_cross_team_signal_reconciliation_report.py",
    )
    tree = ast.parse(path.read_text(encoding="utf-8"))

    banned_imports = {
        "asyncio",
        "http",
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
        "web3",
    }
    banned_calls = {
        "connect",
        "delete",
        "execute",
        "insert",
        "login",
        "open",
        "post",
        "request",
        "send",
        "submit",
        "update",
        "urlopen",
        "write",
    }
    banned_attributes = banned_calls | {"commit", "rollback", "session"}
    forbidden_public_name_fragments = (
        "candidate",
        "market_id",
        "market_slug",
        "question",
        "url",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "position",
        "sizing",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not ({alias.name.split(".")[0] for alias in node.names} & banned_imports)
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned_imports
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in banned_calls
        elif isinstance(node, ast.Attribute):
            assert node.attr not in banned_attributes

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_CROSS_TEAM_SIGNAL_RECONCILIATION_CONFIG_VERSION",
        "ResearchStrategyCrossTeamSignalInput",
        "ResearchStrategyCrossTeamSignalReconciliationConfig",
        "ResearchStrategyCrossTeamSignalReconciliationReport",
        "ResearchStrategyCrossTeamSignalReconciliationRow",
        "build_research_strategy_cross_team_signal_reconciliation_report",
        "research_strategy_cross_team_signal_reconciliation_report_payload",
    )
    for public_name in module.__all__:
        assert [
            fragment
            for fragment in forbidden_public_name_fragments
            if fragment in public_name.lower()
        ] == []
