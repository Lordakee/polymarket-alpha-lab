from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_recommendation_market_close_readiness_gate_v2.py"
)
GENERATED_AT = datetime(2026, 7, 4, 18, 0, tzinfo=UTC)
EVALUATED_AT = datetime(2026, 7, 4, 17, 55, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _MissingOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_recommendation_market_close_readiness_gate_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_STRATEGY_RECOMMENDATION_MARKET_CLOSE_READINESS_GATE_V2_CONFIG_VERSION
        ),
        "near_close_watch_minutes": d("120.000000"),
        "near_close_block_enter_minutes": d("30.000000"),
        "max_ready_official_result_lag_minutes": d("15.000000"),
        "max_watch_official_result_lag_minutes": d("60.000000"),
        "max_ready_source_contradiction_score": d("0.050000"),
        "max_watch_source_contradiction_score": d("0.200000"),
        "min_ready_exit_capacity_ratio": d("2.000000"),
        "min_watch_exit_capacity_ratio": d("1.000000"),
        "max_ready_settlement_ambiguity_score": d("0.050000"),
        "max_watch_settlement_ambiguity_score": d("0.200000"),
        "min_ready_edge_after_paper_cost": d("0.020000"),
        "min_watch_edge_after_paper_cost": d("0.000000"),
    }
    values.update(overrides)
    return module.StrategyRecommendationMarketCloseReadinessGateV2Config(**values)


def candidate(**overrides: object) -> Any:
    module = api()
    values = {
        "candidate_reference": "candidate-alpha",
        "market_slug": "alpha-market",
        "evaluated_at": EVALUATED_AT,
        "recommendation_intent": "enter",
        "minutes_to_close": d("240.000000"),
        "official_result_lag_minutes": d("5.000000"),
        "source_contradiction_score": d("0.000000"),
        "exit_capacity_ratio": d("3.000000"),
        "settlement_ambiguity_score": d("0.000000"),
        "expected_edge_after_paper_cost": d("0.050000"),
        "reason_codes": ("research_packet_ready",),
    }
    values.update(overrides)
    return module.StrategyRecommendationMarketCloseReadinessGateV2Candidate(**values)


def report(
    *candidates: object,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_strategy_recommendation_market_close_readiness_gate_v2(
        candidates,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_public_numeric_values(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected public numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_public_numeric_values(item)


def test_gate_combines_close_lag_contradiction_liquidity_settlement_and_cost() -> None:
    result = report(
        candidate(
            candidate_reference="ready-alpha",
            market_slug="gamma-ready",
            recommendation_intent="enter",
            minutes_to_close=d("240.000000"),
            official_result_lag_minutes=d("10.000000"),
            source_contradiction_score=d("0.010000"),
            exit_capacity_ratio=d("3.000000"),
            settlement_ambiguity_score=d("0.010000"),
            expected_edge_after_paper_cost=d("0.050000"),
        ),
        candidate(
            candidate_reference="watch-alpha",
            market_slug="beta-watch",
            recommendation_intent="keep",
            minutes_to_close=d("45.000000"),
            official_result_lag_minutes=d("30.000000"),
            source_contradiction_score=d("0.100000"),
            exit_capacity_ratio=d("1.500000"),
            settlement_ambiguity_score=d("0.100000"),
            expected_edge_after_paper_cost=d("0.010000"),
        ),
        candidate(
            candidate_reference="secret-token-alpha",
            market_slug="alpha-blocked",
            recommendation_intent="enter",
            minutes_to_close=d("10.000000"),
            official_result_lag_minutes=d("120.000000"),
            source_contradiction_score=d("0.300000"),
            exit_capacity_ratio=d("0.500000"),
            settlement_ambiguity_score=d("0.300000"),
            expected_edge_after_paper_cost=d("-0.010000"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == (
        "strategy-recommendation-market-close-readiness-gate-v2"
    )
    assert result.candidate_count == d("3")
    assert result.ready_count == d("1")
    assert result.watch_count == d("1")
    assert result.blocked_count == d("1")
    assert result.enter_safe_count == d("1")
    assert result.keep_safe_count == d("2")
    assert result.min_minutes_to_close == d("10.000000")
    assert result.max_official_result_lag_minutes == d("120.000000")
    assert result.max_source_contradiction_score == d("0.300000")
    assert result.min_exit_capacity_ratio == d("0.500000")
    assert result.max_settlement_ambiguity_score == d("0.300000")
    assert result.min_expected_edge_after_paper_cost == d("-0.010000")
    assert result.status == "blocked"
    assert result.report_digest.startswith("market_close_report_digest_")
    assert result.reason_codes == (
        "market_close_gate_blocked",
        "market_close_gate_watch",
        "market_close_gate_ready",
        "close_proximity_block_enter",
        "close_proximity_watch",
        "close_proximity_ready",
        "official_result_lag_blocked",
        "official_result_lag_watch",
        "official_result_lag_ready",
        "source_contradiction_blocked",
        "source_contradiction_watch",
        "source_contradiction_ready",
        "liquidity_exit_capacity_blocked",
        "liquidity_exit_capacity_watch",
        "liquidity_exit_capacity_ready",
        "settlement_ambiguity_blocked",
        "settlement_ambiguity_watch",
        "settlement_ambiguity_ready",
        "paper_cost_floor_blocked",
        "paper_cost_floor_watch",
        "paper_cost_floor_ready",
        "research_packet_ready",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert tuple(row.market_slug for row in result.rows) == (
        "alpha-blocked",
        "beta-watch",
        "gamma-ready",
    )
    blocked, watched, ready = result.rows

    assert blocked.close_readiness_status == "blocked"
    assert blocked.safe_to_enter is False
    assert blocked.safe_to_keep is False
    assert blocked.readiness_digest.startswith("market_close_row_digest_")
    assert blocked.redacted_candidate_reference.startswith("candidate_ref_")
    assert "secret-token-alpha" not in repr(blocked)
    assert "token" not in repr(blocked).lower()
    assert blocked.reason_codes == (
        "research_packet_ready",
        "market_close_gate_blocked",
        "close_proximity_block_enter",
        "official_result_lag_blocked",
        "source_contradiction_blocked",
        "liquidity_exit_capacity_blocked",
        "settlement_ambiguity_blocked",
        "paper_cost_floor_blocked",
    )

    assert watched.close_readiness_status == "watch"
    assert watched.safe_to_enter is False
    assert watched.safe_to_keep is True
    assert watched.reason_codes == (
        "research_packet_ready",
        "market_close_gate_watch",
        "close_proximity_watch",
        "official_result_lag_watch",
        "source_contradiction_watch",
        "liquidity_exit_capacity_watch",
        "settlement_ambiguity_watch",
        "paper_cost_floor_watch",
    )

    assert ready.close_readiness_status == "ready"
    assert ready.safe_to_enter is True
    assert ready.safe_to_keep is True
    assert ready.reason_codes == (
        "research_packet_ready",
        "market_close_gate_ready",
        "close_proximity_ready",
        "official_result_lag_ready",
        "source_contradiction_ready",
        "liquidity_exit_capacity_ready",
        "settlement_ambiguity_ready",
        "paper_cost_floor_ready",
    )

    repeated = report(
        candidate(
            candidate_reference="ready-alpha",
            market_slug="gamma-ready",
        ),
    )
    repeated_again = report(
        candidate(
            candidate_reference="ready-alpha",
            market_slug="gamma-ready",
        ),
    )
    assert repeated.report_digest == repeated_again.report_digest
    assert repeated.rows[0].readiness_digest == repeated_again.rows[0].readiness_digest


def test_empty_report_is_watch_zeroed_decimal_and_readonly() -> None:
    empty = report()

    assert empty.candidate_count == d("0")
    assert empty.ready_count == d("0")
    assert empty.watch_count == d("0")
    assert empty.blocked_count == d("0")
    assert empty.enter_safe_count == d("0")
    assert empty.keep_safe_count == d("0")
    assert empty.min_minutes_to_close == ZERO
    assert empty.max_official_result_lag_minutes == ZERO
    assert empty.max_source_contradiction_score == ZERO
    assert empty.min_exit_capacity_ratio == ZERO
    assert empty.max_settlement_ambiguity_score == ZERO
    assert empty.min_expected_edge_after_paper_cost == ZERO
    assert empty.status == "watch"
    assert empty.reason_codes == (
        "strategy_recommendation_market_close_readiness_gate_v2_empty",
    )
    assert empty.rows == ()
    assert empty.report_digest.startswith("market_close_report_digest_")
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True

    populated = report(candidate())
    for value in (empty, populated, *populated.rows):
        for item in fields(value):
            if item.name in {
                "paper_only",
                "report_only",
                "readonly",
                "safe_to_enter",
                "safe_to_keep",
            }:
                continue
            item_value = getattr(value, item.name)
            if item.name.endswith(
                (
                    "_count",
                    "_minutes",
                    "_score",
                    "_ratio",
                    "_cost",
                ),
            ):
                assert type(item_value) is Decimal


def test_payload_redacts_references_uses_decimal_strings_and_rejects_public_numbers() -> None:
    module = api()
    result = report(
        candidate(
            candidate_reference="secret-token-alpha",
            market_slug="payload-market",
            minutes_to_close=d("45.000000"),
            evaluated_at=datetime(2026, 7, 4, 10, 55, tzinfo=timezone(timedelta(hours=-7))),
        ),
        generated_at=datetime(2026, 7, 4, 11, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload = module.strategy_recommendation_market_close_readiness_gate_v2_payload(
        result,
    )
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True)
    assert payload["generated_at"] == "2026-07-04T18:00:00+00:00"
    assert payload["candidate_count"] == "1"
    assert payload["min_minutes_to_close"] == "45.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["evaluated_at"] == "2026-07-04T17:55:00+00:00"
    assert payload["rows"][0]["redacted_candidate_reference"].startswith(
        "candidate_ref_",
    )
    assert "secret-token-alpha" not in rendered
    assert "token" not in rendered.lower()
    assert_no_public_numeric_values(payload)

    unsafe_report = replace(result)
    object.__setattr__(unsafe_report, "extra_public_count", 1)
    with pytest.raises(ValueError, match="public payload numeric"):
        module.strategy_recommendation_market_close_readiness_gate_v2_payload(
            unsafe_report,
        )


def test_validation_rejects_bad_types_flags_duplicates_and_inconsistent_rows() -> None:
    module = api()

    with pytest.raises(ValueError, match="config"):
        module.build_strategy_recommendation_market_close_readiness_gate_v2(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="minutes_to_close must be a Decimal"):
        candidate(minutes_to_close=45)
    with pytest.raises(ValueError, match="official_result_lag_minutes must be a Decimal"):
        candidate(official_result_lag_minutes=_DecimalSubclass("5.000000"))
    with pytest.raises(ValueError, match="source_contradiction_score"):
        candidate(source_contradiction_score=d("1.000001"))
    with pytest.raises(ValueError, match="exit_capacity_ratio must be nonnegative"):
        candidate(exit_capacity_ratio=d("-0.000001"))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(candidate(), generated_at=datetime(2026, 7, 4, 18, 0))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(
            candidate(),
            generated_at=datetime(2026, 7, 4, 18, 0, tzinfo=_MissingOffsetTz()),
        )
    with pytest.raises(ValueError, match="evaluated_at must be exactly datetime"):
        candidate(evaluated_at=_DatetimeSubclass(2026, 7, 4, 17, 55, tzinfo=UTC))
    with pytest.raises(ValueError, match="evaluated_at must not be after generated_at"):
        report(candidate(evaluated_at=datetime(2026, 7, 4, 18, 1, tzinfo=UTC)))
    with pytest.raises(ValueError, match="duplicate candidate_reference"):
        report(candidate(), candidate())
    with pytest.raises(ValueError, match="near_close_block_enter_minutes"):
        config(near_close_block_enter_minutes=d("121.000000"))
    with pytest.raises(ValueError, match="paper_only"):
        candidate(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        config(readonly=False)

    result = report(
        candidate(candidate_reference="ready-alpha", market_slug="alpha"),
        candidate(
            candidate_reference="blocked-beta",
            market_slug="beta",
            exit_capacity_ratio=d("0.500000"),
        ),
    )
    with pytest.raises(FrozenInstanceError):
        result.ready_count = d("9")  # type: ignore[misc]
    with pytest.raises(ValueError, match="ready_count"):
        replace(result, ready_count=d("0"))
    with pytest.raises(ValueError, match="rows must be sorted"):
        replace(result, rows=tuple(reversed(result.rows)))
    with pytest.raises(ValueError, match="close_readiness_status"):
        replace(result.rows[0], close_readiness_status="watch")
    with pytest.raises(ValueError, match="readiness_digest"):
        replace(result.rows[0], readiness_digest="market_close_row_digest_bad")


def test_payload_requires_report_type_hard_flags_and_safe_public_text() -> None:
    module = api()
    result = report(candidate())

    with pytest.raises(ValueError, match="report must be"):
        module.strategy_recommendation_market_close_readiness_gate_v2_payload(object())
    with pytest.raises(ValueError, match="report_only must be True"):
        module.strategy_recommendation_market_close_readiness_gate_v2_payload(
            replace(result, report_only=False),
        )

    unsafe_report = replace(result)
    object.__setattr__(unsafe_report.rows[0], "redacted_candidate_reference", "secret-token")
    with pytest.raises(ValueError, match="unsafe public text"):
        module.strategy_recommendation_market_close_readiness_gate_v2_payload(
            unsafe_report,
        )


def test_module_scope_has_no_live_io_persistence_or_float_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    forbidden_terms = (
        "psycopg",
        "supabase",
        "sqlite",
        "requests",
        "urllib",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "read_text",
        "write_text",
        "private_key",
        "broker",
        "wallet",
        "order",
        "trade",
    )
    for forbidden in forbidden_terms:
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imported_names = [alias.name for alias in node.names]
            if isinstance(node, ast.ImportFrom) and node.module is not None:
                imported_names.append(node.module)
            for imported in imported_names:
                assert not any(term in imported.lower() for term in forbidden_terms)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {
                "open",
                "connect",
                "execute",
                "fetch",
                "request",
                "submit",
            }
