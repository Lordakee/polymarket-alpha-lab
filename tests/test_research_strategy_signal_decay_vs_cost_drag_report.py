from __future__ import annotations

import ast
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_signal_decay_vs_cost_drag_report import (
    DEFAULT_RESEARCH_STRATEGY_SIGNAL_DECAY_VS_COST_DRAG_REPORT_CONFIG_VERSION,
    RESEARCH_STRATEGY_SIGNAL_DECAY_VS_COST_DRAG_STATUSES,
    ResearchStrategySignalDecayVsCostDragConfig,
    ResearchStrategySignalDecayVsCostDragInput,
    ResearchStrategySignalDecayVsCostDragReasonCodeCount,
    ResearchStrategySignalDecayVsCostDragReport,
    ResearchStrategySignalDecayVsCostDragRow,
    build_research_strategy_signal_decay_vs_cost_drag_report,
    research_strategy_signal_decay_vs_cost_drag_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategySignalDecayVsCostDragConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_SIGNAL_DECAY_VS_COST_DRAG_REPORT_CONFIG_VERSION
        ),
        "evidence_age_hours_pass_ceiling": d("6.000000"),
        "evidence_age_hours_watch_ceiling": d("18.000000"),
        "source_authority_pass_floor": d("0.800000"),
        "source_authority_watch_floor": d("0.500000"),
        "market_movement_pass_ceiling": d("0.030000"),
        "market_movement_watch_ceiling": d("0.090000"),
        "cost_drag_pass_ceiling": d("0.030000"),
        "cost_drag_watch_ceiling": d("0.070000"),
        "liquidity_depth_pass_floor": d("0.700000"),
        "liquidity_depth_watch_floor": d("0.400000"),
        "resolution_ambiguity_pass_ceiling": d("0.250000"),
        "resolution_ambiguity_watch_ceiling": d("0.600000"),
        "age_decay_weight": d("0.180000"),
        "authority_decay_weight": d("0.250000"),
        "movement_decay_weight": d("0.220000"),
        "spread_cost_weight": d("1.000000"),
        "fee_cost_weight": d("1.000000"),
        "slippage_cost_weight": d("1.000000"),
        "liquidity_cost_weight": d("0.150000"),
        "resolution_drag_weight": d("0.120000"),
    }
    values.update(overrides)
    return ResearchStrategySignalDecayVsCostDragConfig(**values)


def signal_input(**overrides: object) -> ResearchStrategySignalDecayVsCostDragInput:
    values = {
        "candidate_ref": "candidate_alpha",
        "market_ref": "event_market_alpha",
        "evidence_observed_at": datetime(2026, 7, 8, 9, 0, tzinfo=UTC),
        "source_authority_score": d("0.900000"),
        "market_probability_at_evidence": d("0.600000"),
        "current_market_probability": d("0.620000"),
        "spread_probability_cost": d("0.006000"),
        "fee_probability_cost": d("0.004000"),
        "slippage_probability_cost": d("0.005000"),
        "liquidity_depth_score": d("0.900000"),
        "resolution_ambiguity_score": d("0.100000"),
    }
    values.update(overrides)
    return ResearchStrategySignalDecayVsCostDragInput(**values)


def report(
    *rows: ResearchStrategySignalDecayVsCostDragInput,
    cfg: ResearchStrategySignalDecayVsCostDragConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategySignalDecayVsCostDragReport:
    return build_research_strategy_signal_decay_vs_cost_drag_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk_payload_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        values: list[Any] = []
        for item in value.values():
            values.extend(walk_payload_values(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(walk_payload_values(item))
        return tuple(values)
    return (value,)


def test_report_compares_signal_decay_against_cost_drag_without_action_surface() -> None:
    summary = report(
        signal_input(
            candidate_ref="candidate_alpha",
            market_ref="event_market_alpha",
            evidence_observed_at=datetime(2026, 7, 8, 9, 0, tzinfo=UTC),
            source_authority_score=d("0.900000"),
            market_probability_at_evidence=d("0.600000"),
            current_market_probability=d("0.620000"),
            spread_probability_cost=d("0.006000"),
            fee_probability_cost=d("0.004000"),
            slippage_probability_cost=d("0.005000"),
            liquidity_depth_score=d("0.900000"),
            resolution_ambiguity_score=d("0.100000"),
        ),
        signal_input(
            candidate_ref="candidate_beta",
            market_ref="event_market_beta",
            evidence_observed_at=datetime(2026, 7, 8, 2, 0, tzinfo=UTC),
            source_authority_score=d("0.650000"),
            market_probability_at_evidence=d("0.480000"),
            current_market_probability=d("0.540000"),
            spread_probability_cost=d("0.018000"),
            fee_probability_cost=d("0.010000"),
            slippage_probability_cost=d("0.012000"),
            liquidity_depth_score=d("0.550000"),
            resolution_ambiguity_score=d("0.400000"),
        ),
        signal_input(
            candidate_ref="candidate_gamma",
            market_ref="event_market_gamma",
            evidence_observed_at=datetime(2026, 7, 7, 8, 0, tzinfo=UTC),
            source_authority_score=d("0.300000"),
            market_probability_at_evidence=d("0.320000"),
            current_market_probability=d("0.470000"),
            spread_probability_cost=d("0.035000"),
            fee_probability_cost=d("0.020000"),
            slippage_probability_cost=d("0.025000"),
            liquidity_depth_score=d("0.250000"),
            resolution_ambiguity_score=d("0.800000"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert type(summary) is ResearchStrategySignalDecayVsCostDragReport
    assert summary.generated_at == GENERATED_AT
    assert summary.input_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.mean_signal_decay_score == d("0.337685")
    assert summary.mean_cost_drag_score == d("0.162000")
    assert summary.mean_decay_cost_gap == d("0.175685")
    assert summary.mean_evidence_age_hours == d("13.666667")
    assert summary.mean_market_movement_probability == d("0.076667")
    assert summary.status == "block"
    assert summary.reason_codes == (
        "signal_decay_vs_cost_drag_report_block",
        "evidence_age_review",
        "source_authority_review",
        "market_movement_review",
        "cost_drag_review",
        "liquidity_depth_review",
        "resolution_ambiguity_review",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True
    assert len(summary.derived_validation_digest) == 64
    assert tuple(row.candidate_ref for row in summary.rows) == (
        "candidate_gamma",
        "candidate_beta",
        "candidate_alpha",
    )

    blocked = summary.rows[0]
    assert isinstance(blocked, ResearchStrategySignalDecayVsCostDragRow)
    assert blocked.evidence_age_hours == d("28.000000")
    assert blocked.market_movement_probability == d("0.150000")
    assert blocked.direct_cost_drag_probability == d("0.080000")
    assert blocked.signal_decay_score == d("0.575000")
    assert blocked.cost_drag_score == d("0.288500")
    assert blocked.decay_cost_gap == d("0.286500")
    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "evidence_age_block",
        "source_authority_block",
        "market_movement_block",
        "cost_drag_block",
        "liquidity_depth_block",
        "resolution_ambiguity_block",
    )

    watched = summary.rows[1]
    assert watched.evidence_age_hours == d("10.000000")
    assert watched.market_movement_probability == d("0.060000")
    assert watched.direct_cost_drag_probability == d("0.040000")
    assert watched.signal_decay_score == d("0.334167")
    assert watched.cost_drag_score == d("0.155500")
    assert watched.decay_cost_gap == d("0.178667")
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "evidence_age_watch",
        "source_authority_watch",
        "market_movement_watch",
        "cost_drag_watch",
        "liquidity_depth_watch",
        "resolution_ambiguity_watch",
    )

    passed = summary.rows[2]
    assert passed.evidence_age_hours == d("3.000000")
    assert passed.signal_decay_score == d("0.103889")
    assert passed.cost_drag_score == d("0.042000")
    assert passed.decay_cost_gap == d("0.061889")
    assert passed.status == "pass"
    assert passed.reason_codes == ("signal_decay_vs_cost_drag_pass",)

    counts = {item.reason_code: item for item in summary.reason_code_counts}
    assert counts["market_movement_watch"] == ResearchStrategySignalDecayVsCostDragReasonCodeCount(
        reason_code="market_movement_watch",
        count=d("1.000000"),
        input_ratio=d("0.333333"),
    )


def test_payload_is_redacted_deterministic_decimal_stringed_and_digest_guarded() -> None:
    generated_at = datetime(2026, 7, 8, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    first_payload = research_strategy_signal_decay_vs_cost_drag_report_payload(
        report(signal_input(), generated_at=generated_at),
    )
    second_payload = research_strategy_signal_decay_vs_cost_drag_report_payload(
        report(signal_input(), generated_at=generated_at),
    )

    assert first_payload == second_payload
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["input_count"] == "1.000000"
    assert first_payload["rows"][0]["row_number"] == "1.000000"
    assert first_payload["rows"][0]["evidence_age_hours"] == "3.000000"
    assert first_payload["rows"][0]["signal_decay_score"] == "0.103889"
    assert first_payload["rows"][0]["cost_drag_score"] == "0.042000"
    assert first_payload["rows"][0]["decay_cost_gap"] == "0.061889"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert len(first_payload["derived_validation_digest"]) == 64
    assert not any(
        type(value) in (int, float, Decimal)
        for value in walk_payload_values(first_payload)
    )

    payload_text = json.dumps(first_payload, sort_keys=True).lower()
    for forbidden in (
        "candidate_ref",
        "market_ref",
        "candidate_alpha",
        "event_market_alpha",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "position",
        "sizing",
    ):
        assert forbidden not in payload_text

    tampered_payload = research_strategy_signal_decay_vs_cost_drag_report_payload(
        report(signal_input()),
    )
    tampered_payload["rows"][0]["signal_decay_score"] = "0.999999"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_strategy_signal_decay_vs_cost_drag_report_payload(tampered_payload)

    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_signal_decay_vs_cost_drag_report_payload(
            {
                "market_ref": "event_market_alpha",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


def test_validation_rejects_bad_numerics_flags_times_and_duplicate_candidates() -> None:
    with pytest.raises(ValueError, match="source_authority_score"):
        signal_input(source_authority_score=0.9)
    with pytest.raises(ValueError, match="spread_probability_cost"):
        signal_input(spread_probability_cost=_DecimalSubclass("0.001000"))
    with pytest.raises(ValueError, match="current_market_probability"):
        signal_input(current_market_probability=d("1.200000"))
    with pytest.raises(ValueError, match="evidence_observed_at"):
        signal_input(evidence_observed_at=datetime(2026, 7, 8, 9, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            signal_input(),
            generated_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="evidence_observed_at must not be after generated_at"):
        report(signal_input(evidence_observed_at=datetime(2026, 7, 8, 12, 1, tzinfo=UTC)))
    with pytest.raises(ValueError, match="duplicate"):
        report(
            signal_input(candidate_ref="same_candidate"),
            signal_input(candidate_ref="same_candidate", market_ref="event_market_beta"),
        )
    with pytest.raises(ValueError, match="evidence_age_hours_pass_ceiling"):
        config(evidence_age_hours_pass_ceiling=d("20.000000"))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)


def test_dataclasses_are_frozen_decimal_only_and_module_has_no_external_surfaces() -> None:
    summary = report(signal_input())
    row = summary.rows[0]

    assert is_dataclass(row)
    assert RESEARCH_STRATEGY_SIGNAL_DECAY_VS_COST_DRAG_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    with pytest.raises(FrozenInstanceError):
        row.status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="report_only"):
        replace(row, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(summary, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            row,
            signal_decay_score=d("0.020000"),
            derived_validation_digest=row.derived_validation_digest,
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            summary,
            input_count=d("2.000000"),
            derived_validation_digest=summary.derived_validation_digest,
        )

    for value in (
        config(),
        signal_input(),
        row,
        summary,
        *summary.reason_code_counts,
    ):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item_value is None or item.name in {
                "paper_only",
                "report_only",
                "readonly",
                "reason_codes",
                "reason_code_counts",
                "rows",
                "candidate_ref",
                "market_ref",
                "status",
                "config_version",
                "derived_validation_digest",
                "evidence_observed_at",
                "generated_at",
            }:
                continue
            if any(
                token in item.name
                for token in (
                    "age",
                    "authority",
                    "count",
                    "cost",
                    "drag",
                    "floor",
                    "ceiling",
                    "probability",
                    "ratio",
                    "score",
                    "weight",
                    "depth",
                    "ambiguity",
                    "gap",
                )
            ):
                assert type(item_value) is Decimal

    import polymarket_alpha_lab.research_strategy_signal_decay_vs_cost_drag_report as module

    source = inspect.getsource(module)
    tree = ast.parse(source)

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_SIGNAL_DECAY_VS_COST_DRAG_REPORT_CONFIG_VERSION",
        "RESEARCH_STRATEGY_SIGNAL_DECAY_VS_COST_DRAG_STATUSES",
        "ResearchStrategySignalDecayVsCostDragConfig",
        "ResearchStrategySignalDecayVsCostDragInput",
        "ResearchStrategySignalDecayVsCostDragReasonCodeCount",
        "ResearchStrategySignalDecayVsCostDragRow",
        "ResearchStrategySignalDecayVsCostDragReport",
        "build_research_strategy_signal_decay_vs_cost_drag_report",
        "research_strategy_signal_decay_vs_cost_drag_report_payload",
    )
    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
        for node in ast.walk(tree)
    )

    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

    assert imported_roots <= {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }

    forbidden_call_names = {
        "__import__",
        "connect",
        "execute",
        "float",
        "open",
        "request",
        "write",
        "write_bytes",
        "write_text",
    }
    forbidden_source_tokens = (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "url",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "recommend",
        "position",
        "sizing",
    )
    lowered_source = source.lower()
    for token in forbidden_source_tokens:
        assert token not in lowered_source
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_call_names
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_call_names
