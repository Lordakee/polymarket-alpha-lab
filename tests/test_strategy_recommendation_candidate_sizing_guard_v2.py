from __future__ import annotations

import ast
import importlib
import json
import re
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.strategy_recommendation_candidate_sizing_guard_v2"
REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_recommendation_candidate_sizing_guard_v2.py"
)
GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": "strategy-recommendation-candidate-sizing-guard-v2-test",
        "bankroll_notional": d("1000.000000"),
        "bankroll_cap_share": d("0.050000"),
        "market_depth_cap_share": d("0.250000"),
        "category_budget_share": d("0.200000"),
        "correlation_budget_share": d("0.100000"),
        "correlation_pressure_watch_share": d("0.800000"),
        "correlation_pressure_block_share": d("1.000000"),
        "min_ready_confidence": d("0.650000"),
        "min_watch_confidence": d("0.550000"),
        "min_ready_cost_adjusted_edge": d("0.020000"),
        "min_watch_cost_adjusted_edge": d("0.000000"),
        "max_loss_share": d("0.040000"),
    }
    values.update(overrides)
    return module.StrategyRecommendationCandidateSizingGuardV2Config(**values)


def snapshot(**overrides: object) -> Any:
    module = api()
    values = {
        "category": "macro",
        "correlation_key": "fomc-july",
        "current_category_exposure": d("100.000000"),
        "current_correlation_exposure": d("20.000000"),
    }
    values.update(overrides)
    return module.StrategyRecommendationCandidateSizingGuardV2ExposureSnapshot(**values)


def candidate(**overrides: object) -> Any:
    module = api()
    values = {
        "candidate_id": "ready",
        "recommendation_id": "manual-ticket-ready",
        "market_slug": "fed-decision-july",
        "category": "macro",
        "correlation_key": "fomc-july",
        "requested_notional": d("20.000000"),
        "market_depth_notional": d("240.000000"),
        "confidence": d("0.720000"),
        "gross_edge": d("0.070000"),
        "total_cost": d("0.015000"),
        "max_loss_notional": d("18.000000"),
        "reason_codes": ("manual_review",),
    }
    values.update(overrides)
    return module.StrategyRecommendationCandidateSizingGuardV2Candidate(**values)


def report(
    *candidates: object,
    snapshots: tuple[object, ...] | None = None,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_strategy_recommendation_candidate_sizing_guard_v2_report(
        candidates,
        exposure_snapshots=snapshots if snapshots is not None else (snapshot(),),
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_decimal_only_dataclass(value: object) -> None:
    for item in fields(value):
        field_value = getattr(value, item.name)
        if type(field_value) in (bool, str, datetime, tuple) or field_value is None:
            continue
        assert type(field_value) is Decimal


def assert_no_float_decimal_or_int_payload_values(value: object) -> None:
    if type(value) in (float, int) or isinstance(value, Decimal):
        raise AssertionError(f"unexpected non-JSON numeric value {value!r}")
    if isinstance(value, dict):
        for key, item in value.items():
            assert type(key) is str
            assert_no_float_decimal_or_int_payload_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_decimal_or_int_payload_values(item)


def test_builds_phase_one_candidate_sizing_report_with_pass_watch_block_rows() -> None:
    result = report(
        candidate(
            candidate_id="ready",
            recommendation_id="manual-ready",
            market_slug="fed-decision-july",
            category="macro",
            correlation_key="fomc-july",
        ),
        candidate(
            candidate_id="watch",
            recommendation_id="paper-watch",
            market_slug="championship-final",
            category="sports",
            correlation_key="cup-final",
            confidence=d("0.600000"),
            gross_edge=d("0.040000"),
            total_cost=d("0.015000"),
            market_depth_notional=d("260.000000"),
            max_loss_notional=d("20.000000"),
        ),
        candidate(
            candidate_id="blocked",
            recommendation_id="manual-blocked",
            market_slug="reserve-shock",
            category="crypto",
            correlation_key="reserve-shock",
            requested_notional=d("70.000000"),
            market_depth_notional=d("120.000000"),
            confidence=d("0.500000"),
            gross_edge=d("0.010000"),
            total_cost=d("0.020000"),
            max_loss_notional=d("60.000000"),
        ),
        snapshots=(
            snapshot(
                category="macro",
                correlation_key="fomc-july",
                current_category_exposure=d("100.000000"),
                current_correlation_exposure=d("20.000000"),
            ),
            snapshot(
                category="sports",
                correlation_key="cup-final",
                current_category_exposure=d("90.000000"),
                current_correlation_exposure=d("65.000000"),
            ),
            snapshot(
                category="crypto",
                correlation_key="reserve-shock",
                current_category_exposure=d("190.000000"),
                current_correlation_exposure=d("95.000000"),
            ),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "strategy-recommendation-candidate-sizing-guard-v2-test"
    assert result.candidate_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.blocked_count == d("1")
    assert result.digest_status == "blocked"
    assert result.total_requested_notional == d("110.000000")
    assert result.total_allowed_notional == d("50.000000")
    assert result.min_allowed_notional == d("10.000000")
    assert result.max_correlation_pressure == d("1.650000")
    assert result.min_confidence == d("0.500000")
    assert result.min_cost_adjusted_edge == d("-0.010000")
    assert result.max_loss_notional == d("60.000000")
    assert result.reason_codes == (
        "manual_review",
        "candidate_sizing_pass",
        "candidate_sizing_watch",
        "candidate_sizing_blocked",
        "market_depth_cap_limited",
        "category_budget_limited",
        "correlation_pressure_watch",
        "correlation_pressure_block",
        "confidence_below_ready",
        "confidence_below_watch",
        "cost_adjusted_edge_below_ready",
        "cost_adjusted_edge_below_watch",
        "max_loss_above_cap",
        "requested_notional_exceeds_allowed",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert re.fullmatch(r"[0-9a-f]{64}", result.derived_validation_digest)

    assert tuple(row.candidate_id for row in result.rows) == (
        "blocked",
        "watch",
        "ready",
    )

    blocked = result.rows[0]
    assert blocked.rank == d("1")
    assert blocked.bankroll_cap_notional == d("50.000000")
    assert blocked.market_depth_cap_notional == d("30.000000")
    assert blocked.category_budget_notional == d("200.000000")
    assert blocked.category_remaining_notional == d("10.000000")
    assert blocked.correlation_budget_notional == d("100.000000")
    assert blocked.post_trade_correlation_exposure == d("165.000000")
    assert blocked.correlation_pressure == d("1.650000")
    assert blocked.cost_adjusted_edge == d("-0.010000")
    assert blocked.max_loss_cap_notional == d("40.000000")
    assert blocked.allowed_candidate_notional == d("10.000000")
    assert blocked.sizing_status == "blocked"
    assert blocked.reason_codes == (
        "manual_review",
        "candidate_sizing_blocked",
        "market_depth_cap_limited",
        "category_budget_limited",
        "correlation_pressure_block",
        "confidence_below_watch",
        "cost_adjusted_edge_below_watch",
        "max_loss_above_cap",
        "requested_notional_exceeds_allowed",
    )
    assert re.fullmatch(r"[0-9a-f]{64}", blocked.derived_validation_digest)

    watched = result.rows[1]
    assert watched.rank == d("2")
    assert watched.correlation_pressure == d("0.850000")
    assert watched.cost_adjusted_edge == d("0.025000")
    assert watched.allowed_candidate_notional == d("20.000000")
    assert watched.sizing_status == "watch"
    assert watched.reason_codes == (
        "manual_review",
        "candidate_sizing_watch",
        "correlation_pressure_watch",
        "confidence_below_ready",
    )

    passed = result.rows[2]
    assert passed.rank == d("3")
    assert passed.correlation_pressure == d("0.400000")
    assert passed.cost_adjusted_edge == d("0.055000")
    assert passed.allowed_candidate_notional == d("20.000000")
    assert passed.sizing_status == "pass"
    assert passed.reason_codes == ("manual_review", "candidate_sizing_pass")


def test_payload_serializes_decimal_strings_and_digests_are_deterministic() -> None:
    module = api()
    macro = snapshot(category="macro", correlation_key="fomc-july")
    sports = snapshot(
        category="sports",
        correlation_key="cup-final",
        current_category_exposure=d("90.000000"),
        current_correlation_exposure=d("65.000000"),
    )
    ready = candidate(candidate_id="ready", category="macro", correlation_key="fomc-july")
    watched = candidate(
        candidate_id="watch",
        category="sports",
        correlation_key="cup-final",
        confidence=d("0.600000"),
        gross_edge=d("0.040000"),
        total_cost=d("0.015000"),
        market_depth_notional=d("260.000000"),
        max_loss_notional=d("20.000000"),
    )

    first = report(watched, ready, snapshots=(sports, macro))
    second = report(ready, watched, snapshots=(macro, sports))

    assert first.derived_validation_digest == second.derived_validation_digest
    assert tuple(row.derived_validation_digest for row in first.rows) == tuple(
        row.derived_validation_digest for row in second.rows
    )

    payload = module.strategy_recommendation_candidate_sizing_guard_v2_payload(first)
    encoded = json.dumps(payload, sort_keys=True, allow_nan=False)

    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["candidate_count"] == "2"
    assert payload["total_requested_notional"] == "40.000000"
    assert payload["rows"][0]["rank"] == "1"
    assert payload["rows"][0]["candidate_id"] == "watch"
    assert payload["rows"][0]["correlation_pressure"] == "0.850000"
    assert payload["rows"][0]["reason_codes"] == [
        "manual_review",
        "candidate_sizing_watch",
        "correlation_pressure_watch",
        "confidence_below_ready",
    ]
    assert payload["rows"][0]["derived_validation_digest"] == first.rows[0].derived_validation_digest
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert "private" not in encoded.lower()
    assert not re.search(r'":\s*-?\d+(?:\.\d+)?(?:[,}])', encoded)
    assert_no_float_decimal_or_int_payload_values(payload)


def test_outputs_are_decimal_only_frozen_and_tamper_evident() -> None:
    module = api()
    result = report(candidate())
    row = result.rows[0]

    for instance in (config(), snapshot(), candidate(), row, result):
        assert_decimal_only_dataclass(instance)

    with pytest.raises(FrozenInstanceError):
        row.sizing_status = "blocked"
    with pytest.raises(FrozenInstanceError):
        result.digest_status = "watch"
    with pytest.raises(FrozenInstanceError):
        config().bankroll_cap_share = d("0.100000")

    with pytest.raises(ValueError, match="paper_only"):
        replace(candidate(), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(snapshot(), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(config(), readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(result, paper_only=False)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(row, sizing_status="blocked")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(row, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, blocked_count=d("1"))

    with pytest.raises(ValueError, match="report must be"):
        module.strategy_recommendation_candidate_sizing_guard_v2_payload(object())


def test_validates_decimal_only_inputs_thresholds_utc_and_snapshot_mapping() -> None:
    module = api()
    eastern = timezone(timedelta(hours=-4))
    converted = report(
        candidate(),
        snapshots=(snapshot(),),
        generated_at=datetime(2026, 7, 7, 8, 0, tzinfo=eastern),
    )
    assert converted.generated_at == GENERATED_AT

    with pytest.raises(ValueError, match="correlation_pressure_block_share"):
        config(
            correlation_pressure_watch_share=d("0.900000"),
            correlation_pressure_block_share=d("0.800000"),
        )
    with pytest.raises(ValueError, match="min_watch_confidence"):
        config(min_ready_confidence=d("0.650000"), min_watch_confidence=d("0.700000"))
    with pytest.raises(ValueError, match="requested_notional"):
        candidate(requested_notional=20)
    with pytest.raises(ValueError, match="market_depth_notional"):
        candidate(market_depth_notional=_DecimalSubclass("240.000000"))
    with pytest.raises(ValueError, match="category"):
        snapshot(category=_StringSubclass("macro"))
    with pytest.raises(ValueError, match="confidence"):
        candidate(confidence=d("1.100000"))
    with pytest.raises(ValueError, match="reason_codes"):
        candidate(reason_codes=["manual_review"])
    with pytest.raises(ValueError, match="generated_at"):
        report(candidate(), generated_at=_DatetimeSubclass(2026, 7, 7, 12, tzinfo=UTC))
    with pytest.raises(ValueError, match="timezone-aware"):
        report(candidate(), generated_at=datetime(2026, 7, 7, 12))
    with pytest.raises(ValueError, match="exposure_snapshots"):
        module.build_strategy_recommendation_candidate_sizing_guard_v2_report(
            (candidate(category="missing"),),
            exposure_snapshots=(snapshot(),),
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="candidates"):
        module.build_strategy_recommendation_candidate_sizing_guard_v2_report(
            "not-candidates",
            exposure_snapshots=(snapshot(),),
            config=config(),
            generated_at=GENERATED_AT,
        )


def test_module_scope_has_no_external_io_execution_or_live_surfaces() -> None:
    module = api()
    assert set(module.__all__) == {
        "DEFAULT_STRATEGY_RECOMMENDATION_CANDIDATE_SIZING_GUARD_V2_CONFIG_VERSION",
        "StrategyRecommendationCandidateSizingGuardV2Candidate",
        "StrategyRecommendationCandidateSizingGuardV2Config",
        "StrategyRecommendationCandidateSizingGuardV2ExposureSnapshot",
        "StrategyRecommendationCandidateSizingGuardV2Report",
        "StrategyRecommendationCandidateSizingGuardV2Row",
        "build_strategy_recommendation_candidate_sizing_guard_v2_report",
        "strategy_recommendation_candidate_sizing_guard_v2_payload",
    }

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered_source = source.lower()
    forbidden_source_snippets = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "sqlalchemy",
        "psycopg",
        "supabase",
        "web3",
        "clob",
        "private_key",
        "account",
        "broker",
        "submit",
        "cancel",
        "connect(",
        "execute(",
        "fetch(",
        "commit(",
        "rollback(",
        "open(",
        ".write",
        "live trading",
    )
    assert not any(snippet in lowered_source for snippet in forbidden_source_snippets)

    tree = ast.parse(source)
    imported_modules: list[str] = []
    call_names: list[str] = []
    float_constants: list[float] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    assert not float_constants
    assert not any(
        module_name.split(".")[0]
        in {
            "asyncio",
            "os",
            "pathlib",
            "requests",
            "socket",
            "sqlite3",
            "subprocess",
            "urllib",
        }
        for module_name in imported_modules
    )
    assert not any(
        call_name
        in {
            "buy",
            "connect",
            "cursor",
            "environ",
            "execute",
            "fetch",
            "getenv",
            "insert",
            "login",
            "open",
            "persist",
            "sell",
            "send",
            "write",
        }
        for call_name in call_names
    )
