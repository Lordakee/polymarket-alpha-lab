from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.strategy_pretrade_checklist_v5 import (
    DEFAULT_STRATEGY_PRETRADE_CHECKLIST_V5_CONFIG_VERSION,
    StrategyPretradeChecklistV5Candidate,
    StrategyPretradeChecklistV5Config,
    StrategyPretradeChecklistV5Result,
    build_strategy_pretrade_checklist_v5,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _StringSubclass(str):
    pass


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


def _config(**overrides: object) -> StrategyPretradeChecklistV5Config:
    values = {
        "config_version": DEFAULT_STRATEGY_PRETRADE_CHECKLIST_V5_CONFIG_VERSION,
        "min_event_feature_score": Decimal("0.800000"),
        "min_source_quality_score": Decimal("0.800000"),
        "min_cost_adjusted_ev": Decimal("0.010000"),
        "max_ev_rank": Decimal("10"),
    }
    values.update(overrides)
    return StrategyPretradeChecklistV5Config(**values)


def _candidate(
    candidate_id: str = "candidate_pass",
    **overrides: object,
) -> StrategyPretradeChecklistV5Candidate:
    values = {
        "candidate_id": candidate_id,
        "event_feature_status": "complete",
        "event_feature_score": Decimal("0.950000"),
        "source_quality_status": "verified",
        "source_quality_score": Decimal("0.920000"),
        "conflict_policy_status": "clear",
        "resolution_contract_status": "complete",
        "cost_model_status": "current",
        "cost_adjusted_ev": Decimal("0.035000"),
        "ev_rank": Decimal("2"),
        "watchlist_status": "eligible",
        "audit_packet_status": "complete",
    }
    values.update(overrides)
    return StrategyPretradeChecklistV5Candidate(**values)


def test_pretrade_checklist_passes_complete_recommendation_inputs() -> None:
    result = build_strategy_pretrade_checklist_v5(
        _candidate("candidate_ready"),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert isinstance(result, StrategyPretradeChecklistV5Result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == DEFAULT_STRATEGY_PRETRADE_CHECKLIST_V5_CONFIG_VERSION
    assert result.candidate_id == "candidate_ready"
    assert result.checklist_status == "pass"
    assert result.blocking_items == ()
    assert result.reason_codes == ("strategy_pretrade_checklist_v5_passed",)
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_pretrade_checklist_blocks_each_missing_recommendation_gate() -> None:
    result = build_strategy_pretrade_checklist_v5(
        _candidate(
            "candidate_blocked",
            event_feature_status="missing",
            event_feature_score=Decimal("0.400000"),
            source_quality_status="weak",
            source_quality_score=Decimal("0.500000"),
            conflict_policy_status="unresolved",
            resolution_contract_status="missing",
            cost_model_status="stale",
            cost_adjusted_ev=Decimal("0.000000"),
            ev_rank=Decimal("11"),
            watchlist_status="paused",
            audit_packet_status="missing",
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert result.checklist_status == "blocked"
    assert result.blocking_items == (
        "event_features",
        "source_quality",
        "conflict_policy",
        "resolution_contract",
        "cost_model",
        "cost_adjusted_ev",
        "ev_rank",
        "watchlist_status",
        "audit_packet",
    )
    assert result.reason_codes == (
        "strategy_pretrade_event_features_not_ready",
        "strategy_pretrade_source_quality_not_ready",
        "strategy_pretrade_conflict_policy_not_clear",
        "strategy_pretrade_resolution_contract_not_ready",
        "strategy_pretrade_cost_model_not_ready",
        "strategy_pretrade_cost_adjusted_ev_below_minimum",
        "strategy_pretrade_ev_rank_outside_cutoff",
        "strategy_pretrade_watchlist_not_eligible",
        "strategy_pretrade_audit_packet_not_ready",
    )


def test_pretrade_checklist_normalizes_decimal_and_utc_values() -> None:
    generated_at = datetime(
        2026,
        7,
        6,
        8,
        0,
        tzinfo=timezone(timedelta(hours=-4)),
    )
    candidate = _candidate(
        event_feature_score=Decimal("0.9000004"),
        source_quality_score=Decimal("0.8999995"),
        cost_adjusted_ev=Decimal("0.0150004"),
        ev_rank=Decimal("2.0000004"),
    )

    result = build_strategy_pretrade_checklist_v5(
        candidate,
        config=_config(),
        generated_at=generated_at,
    )

    assert candidate.event_feature_score == Decimal("0.900000")
    assert candidate.source_quality_score == Decimal("0.900000")
    assert candidate.cost_adjusted_ev == Decimal("0.015000")
    assert candidate.ev_rank == Decimal("2.000000")
    assert result.generated_at == GENERATED_AT


def test_pretrade_checklist_validates_exact_types_and_hard_flags() -> None:
    with pytest.raises(ValueError, match="config_version"):
        StrategyPretradeChecklistV5Config(
            config_version=_StringSubclass(
                DEFAULT_STRATEGY_PRETRADE_CHECKLIST_V5_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="min_event_feature_score"):
        _config(min_event_feature_score=Decimal("1.1"))
    with pytest.raises(ValueError, match="candidate_id"):
        _candidate(_StringSubclass("candidate"))
    with pytest.raises(ValueError, match="event_feature_score"):
        _candidate(event_feature_score=0.9)
    with pytest.raises(ValueError, match="source_quality_score"):
        _candidate(source_quality_score=_DecimalSubclass("0.9"))
    with pytest.raises(ValueError, match="ev_rank"):
        _candidate(ev_rank=Decimal("0"))
    with pytest.raises(ValueError, match="watchlist_status"):
        _candidate(watchlist_status="unknown")
    with pytest.raises(ValueError, match="generated_at"):
        build_strategy_pretrade_checklist_v5(
            _candidate(),
            config=_config(),
            generated_at=_DateTimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="config"):
        build_strategy_pretrade_checklist_v5(
            _candidate(),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(_candidate("non_paper"), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(_candidate("non_report"), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(_candidate("non_readonly"), readonly=False)


def test_pretrade_checklist_result_validates_consistency() -> None:
    result = build_strategy_pretrade_checklist_v5(
        _candidate(),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(ValueError, match="checklist_status"):
        StrategyPretradeChecklistV5Result(
            **{**result.__dict__, "checklist_status": "blocked"},
        )
    with pytest.raises(ValueError, match="blocking_items"):
        StrategyPretradeChecklistV5Result(
            **{**result.__dict__, "blocking_items": ("source_quality",)},
        )
    with pytest.raises(ValueError, match="reason_codes"):
        StrategyPretradeChecklistV5Result(
            **{
                **result.__dict__,
                "reason_codes": ("strategy_pretrade_source_quality_not_ready",),
            },
        )


def test_pretrade_checklist_dataclasses_are_frozen() -> None:
    values = (
        _config(),
        _candidate(),
        build_strategy_pretrade_checklist_v5(
            _candidate(),
            config=_config(),
            generated_at=GENERATED_AT,
        ),
    )

    for value in values:
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False


def test_pretrade_checklist_module_scope_is_pure_report_readonly() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.strategy_pretrade_checklist_v5",
    )
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_fragments = (
        "db",
        "env",
        "cli",
        "psycopg",
        "requests",
        "socket",
        "sqlite",
        "sqlalchemy",
        "subprocess",
        "web3",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )

    assert module.__all__ == (
        "DEFAULT_STRATEGY_PRETRADE_CHECKLIST_V5_CONFIG_VERSION",
        "StrategyPretradeChecklistV5Candidate",
        "StrategyPretradeChecklistV5Config",
        "StrategyPretradeChecklistV5Result",
        "build_strategy_pretrade_checklist_v5",
    )
