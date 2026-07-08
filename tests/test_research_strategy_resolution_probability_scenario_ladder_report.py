from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_resolution_probability_scenario_ladder_report import (
    DEFAULT_RESEARCH_STRATEGY_RESOLUTION_PROBABILITY_SCENARIO_LADDER_REPORT_CONFIG_VERSION,
    RESOLUTION_PROBABILITY_SCENARIO_LADDER_STATUSES,
    ResearchStrategyResolutionProbabilityScenarioLadderConfig,
    ResearchStrategyResolutionProbabilityScenarioLadderInput,
    ResearchStrategyResolutionProbabilityScenarioLadderReasonCodeCount,
    ResearchStrategyResolutionProbabilityScenarioLadderReport,
    ResearchStrategyResolutionProbabilityScenarioLadderRow,
    build_research_strategy_resolution_probability_scenario_ladder_report,
    research_strategy_resolution_probability_scenario_ladder_report_digest,
    research_strategy_resolution_probability_scenario_ladder_report_payload,
    validate_research_strategy_resolution_probability_scenario_ladder_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> ResearchStrategyResolutionProbabilityScenarioLadderConfig:
    values: dict[str, object] = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_RESOLUTION_PROBABILITY_SCENARIO_LADDER_REPORT_CONFIG_VERSION
        ),
        "min_pass_base_evidence_strength": d("0.700000"),
        "min_watch_base_evidence_strength": d("0.450000"),
        "min_pass_liquidity_reliability": d("0.650000"),
        "min_watch_liquidity_reliability": d("0.400000"),
        "min_pass_specialist_confidence": d("0.700000"),
        "min_watch_specialist_confidence": d("0.450000"),
        "max_pass_cost_drag": d("0.120000"),
        "max_watch_cost_drag": d("0.300000"),
        "max_pass_resolution_ambiguity": d("0.150000"),
        "max_watch_resolution_ambiguity": d("0.350000"),
    }
    values.update(overrides)
    return ResearchStrategyResolutionProbabilityScenarioLadderConfig(**values)


def input_row(
    event_key: str = "event-pass",
    *,
    downside_evidence_strength: Decimal = d("0.650000"),
    base_evidence_strength: Decimal = d("0.800000"),
    upside_evidence_strength: Decimal = d("0.900000"),
    cost_drag: Decimal = d("0.050000"),
    liquidity_reliability: Decimal = d("0.850000"),
    resolution_ambiguity: Decimal = d("0.100000"),
    specialist_confidence: Decimal = d("0.800000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchStrategyResolutionProbabilityScenarioLadderInput:
    return ResearchStrategyResolutionProbabilityScenarioLadderInput(
        event_key=event_key,
        downside_evidence_strength=downside_evidence_strength,
        base_evidence_strength=base_evidence_strength,
        upside_evidence_strength=upside_evidence_strength,
        cost_drag=cost_drag,
        liquidity_reliability=liquidity_reliability,
        resolution_ambiguity=resolution_ambiguity,
        specialist_confidence=specialist_confidence,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *items: ResearchStrategyResolutionProbabilityScenarioLadderInput,
    cfg: ResearchStrategyResolutionProbabilityScenarioLadderConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyResolutionProbabilityScenarioLadderReport:
    return build_research_strategy_resolution_probability_scenario_ladder_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(
        unsigned,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def test_empty_input_blocks_report_only_scenario_ladder() -> None:
    ladder = report()
    payload = research_strategy_resolution_probability_scenario_ladder_report_payload(
        ladder,
    )

    assert type(ladder) is ResearchStrategyResolutionProbabilityScenarioLadderReport
    assert is_dataclass(ladder)
    assert RESOLUTION_PROBABILITY_SCENARIO_LADDER_STATUSES == ("pass", "watch", "block")
    assert ladder.generated_at == GENERATED_AT
    assert (
        ladder.config_version
        == "research-strategy-resolution-probability-scenario-ladder-report-v0"
    )
    assert ladder.input_count == ZERO
    assert ladder.pass_count == ZERO
    assert ladder.watch_count == ZERO
    assert ladder.block_count == ZERO
    assert ladder.average_readiness_score is None
    assert ladder.min_base_evidence_strength == ZERO
    assert ladder.max_cost_drag == ZERO
    assert ladder.min_liquidity_reliability == ZERO
    assert ladder.max_resolution_ambiguity == ZERO
    assert ladder.min_specialist_confidence == ZERO
    assert ladder.status == "block"
    assert ladder.reason_codes == ("no_resolution_probability_events",)
    assert ladder.reason_code_counts == (
        ResearchStrategyResolutionProbabilityScenarioLadderReasonCodeCount(
            reason_code="no_resolution_probability_events",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert ladder.rows == ()
    assert ladder.paper_only is True
    assert ladder.report_only is True
    assert ladder.readonly is True
    assert len(ladder.derived_validation_digest) == 64
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert validate_research_strategy_resolution_probability_scenario_ladder_report_payload(
        payload,
    )


def test_ladder_scores_pass_watch_and_block_probability_events() -> None:
    ladder = report(
        input_row(
            "event-watch",
            downside_evidence_strength=d("0.500000"),
            base_evidence_strength=d("0.650000"),
            upside_evidence_strength=d("0.740000"),
            cost_drag=d("0.200000"),
            liquidity_reliability=d("0.600000"),
            resolution_ambiguity=d("0.250000"),
            specialist_confidence=d("0.650000"),
            reason_codes=("needs_second_review",),
        ),
        input_row(
            "event-block",
            downside_evidence_strength=d("0.200000"),
            base_evidence_strength=d("0.300000"),
            upside_evidence_strength=d("0.450000"),
            cost_drag=d("0.450000"),
            liquidity_reliability=d("0.250000"),
            resolution_ambiguity=d("0.600000"),
            specialist_confidence=d("0.300000"),
        ),
        input_row("event-pass", reason_codes=("evidence_review_complete",)),
    )

    assert ladder.input_count == d("3.000000")
    assert ladder.pass_count == d("1.000000")
    assert ladder.watch_count == d("1.000000")
    assert ladder.block_count == d("1.000000")
    assert ladder.average_readiness_score == d("0.636667")
    assert ladder.min_base_evidence_strength == d("0.300000")
    assert ladder.max_cost_drag == d("0.450000")
    assert ladder.min_liquidity_reliability == d("0.250000")
    assert ladder.max_resolution_ambiguity == d("0.600000")
    assert ladder.min_specialist_confidence == d("0.300000")
    assert ladder.status == "block"
    assert ladder.reason_codes == (
        "resolution_probability_scenario_ladder_block",
        "base_evidence_strength_block",
        "cost_drag_block",
        "liquidity_reliability_block",
        "resolution_ambiguity_block",
        "specialist_confidence_block",
        "base_evidence_strength_watch",
        "cost_drag_watch",
        "liquidity_reliability_watch",
        "resolution_ambiguity_watch",
        "specialist_confidence_watch",
    )

    block_row, pass_row, watch_row = ladder.rows
    assert type(block_row) is ResearchStrategyResolutionProbabilityScenarioLadderRow
    assert tuple(row.event_key for row in ladder.rows) == (
        "event-block",
        "event-pass",
        "event-watch",
    )
    assert block_row.readiness_score == d("0.360000")
    assert block_row.reliability_discount == d("0.625000")
    assert block_row.downside_probability == d("0.075000")
    assert block_row.base_probability == d("0.112500")
    assert block_row.upside_probability == d("0.168750")
    assert block_row.probability_span == d("0.093750")
    assert block_row.status == "block"
    assert block_row.reason_codes == (
        "base_evidence_strength_block",
        "cost_drag_block",
        "liquidity_reliability_block",
        "resolution_ambiguity_block",
        "resolution_probability_scenario_ladder_block",
        "specialist_confidence_block",
    )
    assert pass_row.readiness_score == d("0.860000")
    assert pass_row.reliability_discount == d("0.125000")
    assert pass_row.downside_probability == d("0.568750")
    assert pass_row.base_probability == d("0.700000")
    assert pass_row.upside_probability == d("0.787500")
    assert pass_row.status == "pass"
    assert pass_row.reason_codes == (
        "base_evidence_strength_pass",
        "cost_drag_pass",
        "input_evidence_review_complete",
        "liquidity_reliability_pass",
        "resolution_ambiguity_pass",
        "resolution_probability_scenario_ladder_pass",
        "specialist_confidence_pass",
    )
    assert watch_row.readiness_score == d("0.690000")
    assert watch_row.reliability_discount == d("0.300000")
    assert watch_row.base_probability == d("0.455000")
    assert watch_row.upside_probability == d("0.518000")
    assert watch_row.status == "watch"
    assert "input_needs_second_review" in watch_row.reason_codes
    assert "base_evidence_strength_watch" in watch_row.reason_codes
    assert "cost_drag_watch" in watch_row.reason_codes
    assert "liquidity_reliability_watch" in watch_row.reason_codes
    assert "resolution_ambiguity_watch" in watch_row.reason_codes
    assert "specialist_confidence_watch" in watch_row.reason_codes


def test_payload_is_deterministic_digest_validated_and_public_safe() -> None:
    first = report(
        input_row("event-z", reason_codes=("zeta", "alpha")),
        input_row("event-a"),
    )
    second = report(
        input_row("event-a"),
        input_row("event-z", reason_codes=("alpha", "zeta")),
    )

    first_payload = research_strategy_resolution_probability_scenario_ladder_report_payload(
        first,
    )
    second_payload = research_strategy_resolution_probability_scenario_ladder_report_payload(
        second,
    )
    encoded = json.dumps(first_payload, allow_nan=False, sort_keys=True)

    assert first_payload == second_payload
    assert research_strategy_resolution_probability_scenario_ladder_report_digest(first) == (
        research_strategy_resolution_probability_scenario_ladder_report_digest(second)
    )
    assert first_payload["derived_validation_digest"] == canonical_digest(first_payload)
    assert validate_research_strategy_resolution_probability_scenario_ladder_report_payload(
        first_payload,
    )
    assert first_payload["rows"][0]["base_probability"] == "0.700000"
    assert first_payload["rows"][0]["readiness_score"] == "0.860000"
    assert not any(type(value) is float for value in _walk_payload_values(first_payload))
    assert not any(type(value) is Decimal for value in _walk_payload_values(first_payload))
    assert not any(type(value) is int for value in _walk_payload_values(first_payload))
    assert ": 0." not in encoded
    assert not any(_has_forbidden_public_surface_key(key) for key in _walk_payload_keys(first_payload))
    assert not any(
        _has_forbidden_public_surface_value(value)
        for value in _walk_payload_values(first_payload)
        if type(value) is str
    )

    tampered = dict(first_payload)
    tampered["status"] = "block"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        validate_research_strategy_resolution_probability_scenario_ladder_report_payload(
            tampered,
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="event_key"):
        input_row("market_slug:secret-event")
    with pytest.raises(ValueError, match="unsafe"):
        validate_research_strategy_resolution_probability_scenario_ladder_report_payload(
            {**first_payload, "wallet_surface": "redacted"},
        )


def test_validation_rejects_non_decimal_bad_flags_and_inconsistent_ladders() -> None:
    populated = report(input_row())

    for value in (config(), input_row(), populated, *populated.rows, *populated.reason_code_counts):
        assert is_dataclass(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {
                "paper_only",
                "report_only",
                "readonly",
                "derived_validation_digest",
            }:
                continue
            if item_value is None:
                continue
            if item.name.endswith(
                (
                    "_count",
                    "_score",
                    "_strength",
                    "_drag",
                    "_reliability",
                    "_ambiguity",
                    "_confidence",
                    "_discount",
                    "_probability",
                    "_span",
                    "_ratio",
                ),
            ):
                assert type(item_value) is Decimal

    with pytest.raises(FrozenInstanceError):
        populated.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        populated.rows[0].base_probability = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="min_pass_base_evidence_strength"):
        config(min_pass_base_evidence_strength=0.7)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="min_watch_base_evidence_strength"):
        config(min_watch_base_evidence_strength=_DecimalSubclass("0.450000"))
    with pytest.raises(ValueError, match="max_pass_cost_drag"):
        config(max_pass_cost_drag=d("0.400000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(input_row(), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(input_row(), generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="base_evidence_strength"):
        input_row(base_evidence_strength=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="scenario ladder"):
        input_row(
            downside_evidence_strength=d("0.700000"),
            base_evidence_strength=d("0.600000"),
            upside_evidence_strength=d("0.800000"),
        )
    with pytest.raises(ValueError, match="reason_codes"):
        input_row(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(input_row(), paper_only=False)
    with pytest.raises(ValueError, match="status"):
        replace(populated, status="blocked")
    with pytest.raises(ValueError, match="base_probability"):
        replace(populated.rows[0], base_probability=d("0.100000"))


def test_owned_module_has_no_execution_or_external_io_surfaces() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_strategy_resolution_probability_scenario_ladder_report.py"
    )
    text = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
        "database",
        "network",
        "wallet",
        "auth",
        "order",
        "trade",
        "live",
        "buy",
        "sell",
        "recommend",
        "sizing",
        "candidate_id",
        "market_id",
        "market_slug",
        "condition_id",
        "token_id",
        "question",
        "source_text",
        "url",
        "dsn",
        "table",
    )

    assert all(term not in text for term in forbidden_terms)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)


def _walk_payload_keys(value: object) -> tuple[str, ...]:
    keys: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            keys.append(key)
            keys.extend(_walk_payload_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.extend(_walk_payload_keys(item))
    return tuple(keys)


def _has_forbidden_public_surface_key(key: str) -> bool:
    lowered = key.lower()
    forbidden = (
        "raw",
        "candidate_id",
        "market_id",
        "market_slug",
        "slug",
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
    )
    return any(term in lowered for term in forbidden)


def _has_forbidden_public_surface_value(value: str) -> bool:
    lowered = value.lower()
    forbidden = (
        "raw",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "http",
        "://",
        "dsn",
        "table=",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "secret",
    )
    return any(term in lowered for term in forbidden)
