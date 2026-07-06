from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.strategy_market_research_priority_queue_v2 import (
    DEFAULT_STRATEGY_MARKET_RESEARCH_PRIORITY_QUEUE_V2_CONFIG_VERSION,
    StrategyMarketResearchPriorityQueueV2Candidate,
    StrategyMarketResearchPriorityQueueV2Config,
    StrategyMarketResearchPriorityQueueV2Item,
    StrategyMarketResearchPriorityQueueV2Report,
    build_strategy_market_research_priority_queue_v2,
    strategy_market_research_priority_queue_v2_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_market_research_priority_queue_v2.py"
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object) -> StrategyMarketResearchPriorityQueueV2Config:
    values = {
        "config_version": DEFAULT_STRATEGY_MARKET_RESEARCH_PRIORITY_QUEUE_V2_CONFIG_VERSION,
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
    return StrategyMarketResearchPriorityQueueV2Config(**values)


def _candidate(
    candidate_id: str,
    *,
    expected_value: Decimal = d("0.070000"),
    information_gap_score: Decimal = d("0.600000"),
    seconds_to_settlement: Decimal = d("43200.000000"),
    available_liquidity: Decimal = d("300.000000"),
    team_expertise_score: Decimal = d("0.700000"),
    source_age_seconds: Decimal = d("3600.000000"),
) -> StrategyMarketResearchPriorityQueueV2Candidate:
    return StrategyMarketResearchPriorityQueueV2Candidate(
        candidate_id=candidate_id,
        expected_value=expected_value,
        information_gap_score=information_gap_score,
        seconds_to_settlement=seconds_to_settlement,
        available_liquidity=available_liquidity,
        team_expertise_score=team_expertise_score,
        source_age_seconds=source_age_seconds,
    )


def test_v2_ranks_by_ev_gap_settlement_liquidity_expertise_and_source_freshness() -> None:
    report = build_strategy_market_research_priority_queue_v2(
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
                "urgent_gap_fresh",
                expected_value=d("0.090000"),
                information_gap_score=d("0.800000"),
                seconds_to_settlement=d("7200.000000"),
                available_liquidity=d("400.000000"),
                team_expertise_score=d("0.900000"),
                source_age_seconds=d("3600.000000"),
            ),
            _candidate(
                "stale_high_ev",
                expected_value=d("0.080000"),
                information_gap_score=d("0.400000"),
                seconds_to_settlement=d("86400.000000"),
                available_liquidity=d("300.000000"),
                team_expertise_score=d("0.700000"),
                source_age_seconds=d("90000.000000"),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, StrategyMarketResearchPriorityQueueV2Report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == DEFAULT_STRATEGY_MARKET_RESEARCH_PRIORITY_QUEUE_V2_CONFIG_VERSION
    assert report.queue_status == "research_required"
    assert report.input_count == d("3.000000")
    assert report.queued_count == d("3.000000")
    assert report.highest_priority_score == d("0.933452")
    assert report.reason_codes == (
        "expected_value_high",
        "information_gap_high",
        "settlement_near",
        "liquidity_ready",
        "liquidity_thin",
        "team_expertise_available",
        "team_expertise_gap",
        "source_fresh",
        "source_stale",
    )
    assert tuple(
        (item.candidate_id, item.research_priority_rank, item.priority_score)
        for item in report.queue_items
    ) == (
        ("urgent_gap_fresh", d("1.000000"), d("0.933452")),
        ("stale_high_ev", d("2.000000"), d("0.741429")),
        ("thin_expertise_gap", d("3.000000"), d("0.598499")),
    )

    assert report.queue_items[0] == StrategyMarketResearchPriorityQueueV2Item(
        candidate_id="urgent_gap_fresh",
        expected_value=d("0.090000"),
        information_gap_score=d("0.800000"),
        seconds_to_settlement=d("7200.000000"),
        available_liquidity=d("400.000000"),
        team_expertise_score=d("0.900000"),
        source_age_seconds=d("3600.000000"),
        priority_score=d("0.933452"),
        research_priority_rank=d("1.000000"),
        next_research_action="collect_missing_evidence",
        reason_codes=(
            "expected_value_high",
            "information_gap_high",
            "settlement_near",
            "liquidity_ready",
            "team_expertise_available",
            "source_fresh",
        ),
    )
    assert report.queue_items[1].next_research_action == "refresh_sources"
    assert report.queue_items[1].reason_codes == (
        "expected_value_high",
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
        "source_fresh",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_v2_empty_queue_is_readonly_clear_report_and_json_ready_payload() -> None:
    report = build_strategy_market_research_priority_queue_v2(
        (),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.queue_status == "clear"
    assert report.input_count == d("0.000000")
    assert report.queued_count == d("0.000000")
    assert report.highest_priority_score == d("0.000000")
    assert report.queue_items == ()
    assert report.reason_codes == ("strategy_market_research_priority_queue_v2_clear",)

    payload = strategy_market_research_priority_queue_v2_payload(report)
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["input_count"] == "0.000000"
    assert payload["queue_items"] == []
    assert payload["reason_codes"] == ["strategy_market_research_priority_queue_v2_clear"]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True


def test_v2_validates_decimal_only_exact_types_frozen_flags_and_utc() -> None:
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

    with pytest.raises(ValueError, match="readonly must be True"):
        replace(_config(), readonly=False)

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_strategy_market_research_priority_queue_v2(
            (candidate,),
            config=_config(),
            generated_at=datetime(2026, 7, 6, 12, 0),
        )

    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        build_strategy_market_research_priority_queue_v2(
            (candidate,),
            config=_config(),
            generated_at=_DateTimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC),
        )

    report = build_strategy_market_research_priority_queue_v2(
        (candidate,),
        config=_config(),
        generated_at=datetime(2026, 7, 6, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )
    assert report.generated_at == GENERATED_AT


def test_v2_rejects_untyped_inputs_duplicates_and_invalid_constructed_reports() -> None:
    with pytest.raises(ValueError, match="candidates must contain"):
        build_strategy_market_research_priority_queue_v2(
            ({"candidate_id": "dict_candidate"},),
            config=_config(),
            generated_at=GENERATED_AT,
        )

    candidate = _candidate("duplicate_candidate")
    with pytest.raises(ValueError, match="candidates must not contain duplicate candidate_id"):
        build_strategy_market_research_priority_queue_v2(
            (candidate, candidate),
            config=_config(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="queue_items must follow deterministic sequence"):
        StrategyMarketResearchPriorityQueueV2Report(
            generated_at=GENERATED_AT,
            config_version=DEFAULT_STRATEGY_MARKET_RESEARCH_PRIORITY_QUEUE_V2_CONFIG_VERSION,
            queue_status="research_required",
            input_count=d("2.000000"),
            queued_count=d("2.000000"),
            highest_priority_score=d("0.900000"),
            queue_items=(
                StrategyMarketResearchPriorityQueueV2Item(
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
                StrategyMarketResearchPriorityQueueV2Item(
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


def test_v2_source_is_pure_report_only_readonly_no_network_db_or_order_surface() -> None:
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
