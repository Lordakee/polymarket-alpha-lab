from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.strategy_event_resolution_contract import (
    StrategyEventResolutionContract,
    StrategyEventResolutionContractCheck,
    StrategyEventResolutionContractConfig,
    StrategyEventResolutionSource,
    check_strategy_event_resolution_contract,
    strategy_event_resolution_contract_payload,
)


CLOSE_TIME = datetime(2026, 7, 31, 20, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def test_clear_polymarket_probability_event_contract_passes_with_zero_risk() -> None:
    contract = _contract(
        condition_id="fed-rate-cut-july-2026",
        question_text=(
            "Will the Federal Reserve lower its target federal funds rate by "
            "July 31, 2026?"
        ),
        rules_summary=(
            "Resolves Yes only if the official FOMC target range published before "
            "close is below the target range in effect at market open; Polymarket "
            "market rules control tie and correction cases."
        ),
        close_time=datetime(2026, 7, 31, 16, 0, tzinfo=timezone(timedelta(hours=-4))),
        source_hierarchy=(
            _source("polymarket-market-rules", "polymarket_rules", Decimal("1")),
            _source("federal-reserve-official-release", "official_primary", Decimal("2")),
        ),
    )

    check = check_strategy_event_resolution_contract(
        contract,
        config=StrategyEventResolutionContractConfig(),
    )

    assert check == StrategyEventResolutionContractCheck(
        condition_id="fed-rate-cut-july-2026",
        resolution_contract_status="pass",
        risk_score=Decimal("0.000000"),
        reason_codes=("polymarket_probability_event_resolution_contract_passed",),
    )
    assert contract.close_time == CLOSE_TIME
    assert check.paper_only is True
    assert check.report_only is True
    assert check.readonly is True


def test_ambiguity_is_blocking_because_polymarket_markets_are_probability_events() -> None:
    check = check_strategy_event_resolution_contract(
        _contract(
            question_text="Will the thing happen?",
            rules_summary="Resolves according to news reports and community consensus.",
            close_time=None,
            source_hierarchy=(_source("social-media-consensus", "proxy", Decimal("1")),),
        ),
        config=StrategyEventResolutionContractConfig(),
    )

    assert check.resolution_contract_status == "blocked"
    assert check.risk_score == Decimal("16.500000")
    assert check.reason_codes == (
        "ambiguous_question_text",
        "ambiguous_resolution_rules_summary",
        "missing_close_time",
        "insufficient_source_hierarchy",
    )


def test_missing_required_contract_surfaces_blocks_with_deterministic_reasons() -> None:
    check = check_strategy_event_resolution_contract(
        _contract(
            question_text="",
            rules_summary="",
            close_time=None,
            source_hierarchy=(),
        ),
        config=StrategyEventResolutionContractConfig(),
    )

    assert check.resolution_contract_status == "blocked"
    assert check.risk_score == Decimal("22.000000")
    assert check.reason_codes == (
        "missing_question_text",
        "missing_resolution_rules_summary",
        "missing_close_time",
        "missing_source_hierarchy",
    )


def test_unclear_source_hierarchy_watches_otherwise_clear_contract() -> None:
    check = check_strategy_event_resolution_contract(
        _contract(
            source_hierarchy=(
                _source("single-official-source", "official_primary", Decimal("1")),
            ),
        ),
        config=StrategyEventResolutionContractConfig(),
    )

    assert check.resolution_contract_status == "watch"
    assert check.risk_score == Decimal("4.500000")
    assert check.reason_codes == ("insufficient_source_hierarchy",)


def test_payload_uses_string_decimals_and_no_live_execution_surface() -> None:
    check = check_strategy_event_resolution_contract(
        _contract(source_hierarchy=()),
        config=StrategyEventResolutionContractConfig(),
    )

    assert strategy_event_resolution_contract_payload(check) == {
        "condition_id": "condition-a",
        "resolution_contract_status": "blocked",
        "risk_score": "5.000000",
        "reason_codes": ["missing_source_hierarchy"],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def test_rejects_float_ranks_naive_close_time_bad_flags_and_mutation() -> None:
    with pytest.raises(ValueError, match="Decimal"):
        _source("float-rank", "official_primary", 1.0)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="Decimal"):
        _source("subclass-rank", "official_primary", _DecimalSubclass("1"))

    with pytest.raises(ValueError, match="timezone-aware"):
        _contract(close_time=datetime(2026, 7, 31, 20, 0))

    contract = _contract()
    with pytest.raises(FrozenInstanceError):
        contract.condition_id = "other-condition"  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        replace(contract, paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        StrategyEventResolutionContractConfig(report_only=False)


def _contract(
    condition_id: str = "condition-a",
    *,
    question_text: str = (
        "Will Candidate A win the certified 2026 general election for Office B?"
    ),
    rules_summary: str = (
        "Resolves Yes only if the official election authority certifies Candidate A "
        "as the winner before close; Polymarket rules control recount corrections."
    ),
    close_time: datetime | None = CLOSE_TIME,
    source_hierarchy: tuple[StrategyEventResolutionSource, ...] = (
        StrategyEventResolutionSource(
            source_key="polymarket-market-rules",
            source_tier="polymarket_rules",
            hierarchy_rank=Decimal("1"),
        ),
        StrategyEventResolutionSource(
            source_key="official-election-certification",
            source_tier="official_primary",
            hierarchy_rank=Decimal("2"),
        ),
    ),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> StrategyEventResolutionContract:
    return StrategyEventResolutionContract(
        condition_id=condition_id,
        question_text=question_text,
        rules_summary=rules_summary,
        close_time=close_time,
        source_hierarchy=source_hierarchy,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _source(
    source_key: str,
    source_tier: str,
    hierarchy_rank: Decimal,
) -> StrategyEventResolutionSource:
    return StrategyEventResolutionSource(
        source_key=source_key,
        source_tier=source_tier,
        hierarchy_rank=hierarchy_rank,
    )
