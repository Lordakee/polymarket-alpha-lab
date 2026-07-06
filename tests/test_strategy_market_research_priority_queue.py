from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.strategy_market_research_priority_queue import (
    DEFAULT_STRATEGY_MARKET_RESEARCH_PRIORITY_QUEUE_CONFIG_VERSION,
    StrategyMarketResearchPriorityCandidate,
    StrategyMarketResearchPriorityQueueConfig,
    StrategyMarketResearchPriorityQueueItem,
    StrategyMarketResearchPriorityQueueReport,
    build_strategy_market_research_priority_queue,
    strategy_market_research_priority_queue_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_market_research_priority_queue.py"
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object) -> StrategyMarketResearchPriorityQueueConfig:
    values = {
        "config_version": DEFAULT_STRATEGY_MARKET_RESEARCH_PRIORITY_QUEUE_CONFIG_VERSION,
        "high_expected_value": d("0.060000"),
        "high_information_gap_score": d("0.500000"),
        "urgent_settlement_seconds": d("86400.000000"),
        "max_priority_settlement_seconds": d("604800.000000"),
        "min_research_liquidity": d("250.000000"),
        "high_team_expertise_score": d("0.600000"),
        "low_team_expertise_score": d("0.300000"),
        "max_source_age_seconds": d("43200.000000"),
    }
    values.update(overrides)
    return StrategyMarketResearchPriorityQueueConfig(**values)


def _candidate(
    candidate_id: str,
    *,
    expected_value: Decimal = d("0.070000"),
    information_gap_score: Decimal = d("0.600000"),
    seconds_to_settlement: Decimal = d("43200.000000"),
    available_liquidity: Decimal = d("300.000000"),
    team_expertise_score: Decimal = d("0.700000"),
    source_age_seconds: Decimal = d("3600.000000"),
) -> StrategyMarketResearchPriorityCandidate:
    return StrategyMarketResearchPriorityCandidate(
        candidate_id=candidate_id,
        expected_value=expected_value,
        information_gap_score=information_gap_score,
        seconds_to_settlement=seconds_to_settlement,
        available_liquidity=available_liquidity,
        team_expertise_score=team_expertise_score,
        source_age_seconds=source_age_seconds,
    )


def test_priority_queue_ranks_by_research_value_gap_urgency_liquidity_expertise_and_freshness() -> None:
    report = build_strategy_market_research_priority_queue(
        (
            _candidate(
                "thin_expertise_gap",
                expected_value=d("0.080000"),
                information_gap_score=d("0.700000"),
                seconds_to_settlement=d("500000.000000"),
                available_liquidity=d("50.000000"),
                team_expertise_score=d("0.200000"),
                source_age_seconds=d("1000.000000"),
            ),
            _candidate(
                "urgent_high_ev",
                expected_value=d("0.090000"),
                information_gap_score=d("0.800000"),
                seconds_to_settlement=d("7200.000000"),
                available_liquidity=d("400.000000"),
                team_expertise_score=d("0.900000"),
                source_age_seconds=d("72000.000000"),
            ),
            _candidate(
                "stale_event",
                expected_value=d("0.050000"),
                information_gap_score=d("0.400000"),
                seconds_to_settlement=d("86400.000000"),
                available_liquidity=d("300.000000"),
                team_expertise_score=d("0.600000"),
                source_age_seconds=d("90000.000000"),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, StrategyMarketResearchPriorityQueueReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == DEFAULT_STRATEGY_MARKET_RESEARCH_PRIORITY_QUEUE_CONFIG_VERSION
    assert report.queue_status == "research_required"
    assert report.input_count == d("3.000000")
    assert report.queued_count == d("3.000000")
    assert report.highest_priority_score == d("0.938214")
    assert report.reason_codes == (
        "expected_value_high",
        "information_gap_high",
        "settlement_near",
        "liquidity_ready",
        "liquidity_thin",
        "team_expertise_available",
        "team_expertise_gap",
        "source_stale",
    )
    assert tuple(
        (item.candidate_id, item.research_priority_rank, item.priority_score)
        for item in report.queue_items
    ) == (
        ("urgent_high_ev", d("1.000000"), d("0.938214")),
        ("stale_event", d("2.000000"), d("0.738571")),
        ("thin_expertise_gap", d("3.000000"), d("0.543307")),
    )

    assert report.queue_items[0] == StrategyMarketResearchPriorityQueueItem(
        candidate_id="urgent_high_ev",
        expected_value=d("0.090000"),
        information_gap_score=d("0.800000"),
        seconds_to_settlement=d("7200.000000"),
        available_liquidity=d("400.000000"),
        team_expertise_score=d("0.900000"),
        source_age_seconds=d("72000.000000"),
        priority_score=d("0.938214"),
        research_priority_rank=d("1.000000"),
        next_research_action="collect_missing_evidence",
        reason_codes=(
            "expected_value_high",
            "information_gap_high",
            "settlement_near",
            "liquidity_ready",
            "team_expertise_available",
            "source_stale",
        ),
    )
    assert report.queue_items[1].next_research_action == "refresh_sources"
    assert report.queue_items[1].reason_codes == (
        "settlement_near",
        "liquidity_ready",
        "team_expertise_available",
        "source_stale",
    )
    assert report.queue_items[2].next_research_action == "monitor_liquidity_before_research"
    assert report.queue_items[2].reason_codes == (
        "expected_value_high",
        "information_gap_high",
        "liquidity_thin",
        "team_expertise_gap",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_priority_queue_returns_clear_report_and_json_ready_payload() -> None:
    report = build_strategy_market_research_priority_queue(
        (),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.queue_status == "clear"
    assert report.input_count == d("0.000000")
    assert report.queued_count == d("0.000000")
    assert report.highest_priority_score == d("0.000000")
    assert report.queue_items == ()
    assert report.reason_codes == ("strategy_market_research_priority_queue_clear",)

    payload = strategy_market_research_priority_queue_payload(report)
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["input_count"] == "0.000000"
    assert payload["queue_items"] == []
    assert payload["reason_codes"] == ["strategy_market_research_priority_queue_clear"]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert len(payload["derived_validation_digest"]) == 64


def test_priority_queue_validates_decimal_only_exact_types_and_utc_boundaries() -> None:
    candidate = _candidate("typed_candidate")
    with pytest.raises(FrozenInstanceError):
        candidate.expected_value = d("0.090000")

    with pytest.raises(ValueError, match="expected_value must be a Decimal"):
        _candidate("float_ev", expected_value=0.09)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="expected_value must be a Decimal"):
        _candidate("subclass_ev", expected_value=_DecimalSubclass("0.090000"))

    with pytest.raises(ValueError, match="information_gap_score must use six decimal places"):
        _candidate("unquantized_gap", information_gap_score=d("0.3333333"))

    with pytest.raises(ValueError, match="candidate_id must be a canonical string"):
        _candidate(" invalid ")

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(candidate, paper_only=False)

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_strategy_market_research_priority_queue(
            (candidate,),
            config=_config(),
            generated_at=datetime(2026, 7, 6, 12, 0),
        )

    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        build_strategy_market_research_priority_queue(
            (candidate,),
            config=_config(),
            generated_at=_DateTimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC),
        )

    report = build_strategy_market_research_priority_queue(
        (candidate,),
        config=_config(),
        generated_at=datetime(2026, 7, 6, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )
    assert report.generated_at == GENERATED_AT


def test_priority_queue_rejects_untyped_inputs_and_invalid_constructed_reports() -> None:
    with pytest.raises(ValueError, match="candidates must contain"):
        build_strategy_market_research_priority_queue(
            ({"candidate_id": "dict_candidate"},),
            config=_config(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="queue_items must follow deterministic sequence"):
        StrategyMarketResearchPriorityQueueReport(
            generated_at=GENERATED_AT,
            config_version=DEFAULT_STRATEGY_MARKET_RESEARCH_PRIORITY_QUEUE_CONFIG_VERSION,
            queue_status="research_required",
            input_count=d("2.000000"),
            queued_count=d("2.000000"),
            highest_priority_score=d("0.900000"),
            queue_items=(
                StrategyMarketResearchPriorityQueueItem(
                    candidate_id="rank_two",
                    expected_value=d("0.060000"),
                    information_gap_score=d("0.500000"),
                    seconds_to_settlement=d("86400.000000"),
                    available_liquidity=d("250.000000"),
                    team_expertise_score=d("0.600000"),
                    source_age_seconds=d("43200.000000"),
                    priority_score=d("0.800000"),
                    research_priority_rank=d("2.000000"),
                    next_research_action="collect_missing_evidence",
                    reason_codes=("information_gap_high",),
                ),
                StrategyMarketResearchPriorityQueueItem(
                    candidate_id="rank_one",
                    expected_value=d("0.070000"),
                    information_gap_score=d("0.600000"),
                    seconds_to_settlement=d("3600.000000"),
                    available_liquidity=d("300.000000"),
                    team_expertise_score=d("0.700000"),
                    source_age_seconds=d("50000.000000"),
                    priority_score=d("0.900000"),
                    research_priority_rank=d("1.000000"),
                    next_research_action="refresh_sources",
                    reason_codes=("source_stale",),
                ),
            ),
            reason_codes=("information_gap_high", "source_stale"),
        )


def test_priority_queue_payload_is_tamper_evident_and_rejects_unsafe_public_payload() -> None:
    report = build_strategy_market_research_priority_queue(
        (_candidate("payload_candidate"),),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert len(report.derived_validation_digest) == 64
    assert all(
        character in "0123456789abcdef"
        for character in report.derived_validation_digest
    )

    payload = strategy_market_research_priority_queue_payload(report)
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    _assert_no_public_numeric_scalars(payload)

    accepted_payload = strategy_market_research_priority_queue_payload(payload)
    assert accepted_payload == payload

    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        strategy_market_research_priority_queue_payload(missing_digest)

    tampered = dict(payload)
    tampered["highest_priority_score"] = "0.000000"
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        strategy_market_research_priority_queue_payload(tampered)

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(report, derived_validation_digest="0" * 64)

    unsafe_key = dict(payload)
    unsafe_key["wallet_address"] = "redacted"
    with pytest.raises(ValueError, match="unsafe"):
        strategy_market_research_priority_queue_payload(unsafe_key)

    unsafe_value = dict(payload)
    unsafe_value["queue_items"] = [
        {**payload["queue_items"][0], "next_research_action": "submit order"}
    ]
    with pytest.raises(ValueError, match="unsafe"):
        strategy_market_research_priority_queue_payload(unsafe_value)

    numeric_scalar = dict(payload)
    numeric_scalar["input_count"] = 1
    with pytest.raises(ValueError, match="Decimal-derived"):
        strategy_market_research_priority_queue_payload(numeric_scalar)


def test_priority_queue_source_is_pure_report_only_and_readonly() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_import_roots = {
        "asyncio",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "urllib",
    }
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", maxsplit=1)[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", maxsplit=1)[0])

    assert imports.isdisjoint(forbidden_import_roots)
    assert "place_order" not in source
    assert "submit_order" not in source
    assert "execute_order" not in source

    forbidden_call_names = {
        "connect",
        "execute",
        "fetch",
        "input",
        "open",
        "place_order",
        "print",
        "submit_order",
        "trade",
    }
    call_names: set[str] = set()
    public_definition_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
            public_definition_names.add(node.name)
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.add(node.func.attr)

    assert call_names.isdisjoint(forbidden_call_names)
    assert all("wallet" not in name.lower() for name in public_definition_names)
    assert all("auth" not in name.lower() for name in public_definition_names)


def _assert_no_public_numeric_scalars(value: object) -> None:
    if isinstance(value, dict):
        for nested in value.values():
            _assert_no_public_numeric_scalars(nested)
        return
    if isinstance(value, list):
        for nested in value:
            _assert_no_public_numeric_scalars(nested)
        return
    assert type(value) not in {Decimal, int, float}
