"""Behavior tests for ``polymarket_alpha_lab.paper_execution``.

Covers Stage 4 Task 1: the pure in-memory leaf that turns a screening-ready
``PaperProjectScreeningCandidate`` plus its in-cycle context into an auditable
``PaperTradeRecord`` via ``simulate_order_book_fill``. No live surfaces.

Scenarios (a)-(k) per the v0 spec execution logic + validation rules.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.cost_aware_event_strategy import (
    GATE_NAMES,
    PaperCostAwareEventStrategyGateResult,
    PaperCostAwareEventStrategyReport,
    PaperCostAwareEventSideResult,
)
from polymarket_alpha_lab.domain import (
    MarketSnapshot,
    NormalizedMarket,
    OrderBookLevel,
    OrderBookSnapshot,
    OutcomeToken,
)
from polymarket_alpha_lab.journal import PaperTradeRecord
from polymarket_alpha_lab.paper import PaperFill
from polymarket_alpha_lab.paper_execution import (
    PaperExecutionConfig,
    PaperExecutionLog,
    PaperExecutionResult,
    execute_paper_trade_from_screening,
)
from polymarket_alpha_lab.project_screening import PaperProjectScreeningCandidate


GENERATED_AT = datetime(2026, 6, 16, 12, 0, 0, tzinfo=UTC)
CONDITION_ID = "0xcondition1234"
YES_TOKEN_ID = "11111"
NO_TOKEN_ID = "22222"
MARKET_SLUG = "test-market"
QUESTION = "Will the test pass?"


# --------------------------------------------------------------------------
# Builders (plain functions, NOT @pytest.fixture per project convention).
# --------------------------------------------------------------------------


def _token(token_id: str, outcome_index: int, outcome_name: str) -> OutcomeToken:
    return OutcomeToken(
        condition_id=CONDITION_ID,
        token_id=token_id,
        outcome_index=outcome_index,
        outcome_name=outcome_name,
    )


def _market() -> NormalizedMarket:
    return NormalizedMarket(
        market=MarketSnapshot(
            condition_id=CONDITION_ID,
            market_slug=MARKET_SLUG,
            question=QUESTION,
            active=True,
            closed=False,
            accepting_orders=True,
            end_time=None,
            volume_24h=Decimal("1000"),
            liquidity=Decimal("500"),
            captured_at=GENERATED_AT,
        ),
        tokens=(
            _token(YES_TOKEN_ID, 0, "Yes"),
            _token(NO_TOKEN_ID, 1, "No"),
        ),
        rules_text="Resolves per the official Polymarket resolution source.",
        resolution_source="polymarket_event_resolution",
    )


def _book(
    token_id: str,
    bids: list[tuple[Decimal, Decimal]],
    asks: list[tuple[Decimal, Decimal]],
) -> OrderBookSnapshot:
    return OrderBookSnapshot(
        token_id=token_id,
        bids=tuple(OrderBookLevel(price=price, size=size) for price, size in bids),
        asks=tuple(OrderBookLevel(price=price, size=size) for price, size in asks),
        captured_at=GENERATED_AT,
    )


def _gate(name: str, status: str = "pass") -> PaperCostAwareEventStrategyGateResult:
    return PaperCostAwareEventStrategyGateResult(
        gate_name=name,
        status=status,
        reason_code=f"{name}_ready" if status == "pass" else f"{name}_fail",
        message="gate fixture",
        observed_value=None,
        threshold=None,
    )


def _all_gates() -> tuple[PaperCostAwareEventStrategyGateResult, ...]:
    return tuple(_gate(name) for name in GATE_NAMES)


def _side_result(
    side: str,
    executable_price: Decimal | None,
    net_edge: Decimal | None,
    fair_probability: Decimal | None = None,
) -> PaperCostAwareEventSideResult:
    if fair_probability is None:
        fair_probability = Decimal("0.60") if side == "yes" else Decimal("0.40")
    return PaperCostAwareEventSideResult(
        side=side,
        fair_probability=fair_probability,
        executable_price=executable_price,
        ask_size=Decimal("100"),
        gross_edge_per_share=Decimal("0.100"),
        fee_cost_per_share=Decimal("0.001"),
        non_fee_cost_per_share=Decimal("0.005"),
        total_cost_per_share=Decimal("0.006"),
        net_edge_per_share=net_edge,
        reason_codes=("paper_edge_complete",),
    )


def _cost_aware_report(
    *,
    yes_price: Decimal | None = Decimal("0.50"),
    no_price: Decimal | None = Decimal("0.35"),
    yes_net: Decimal | None = Decimal("0.050"),
    no_net: Decimal | None = Decimal("0.030"),
    fair_probability_yes: Decimal = Decimal("0.60"),
    status: str = "paper_review_ready",
    selected_side: str = "yes",
) -> PaperCostAwareEventStrategyReport:
    return PaperCostAwareEventStrategyReport(
        generated_at=GENERATED_AT,
        config_version="cost-aware-event-strategy-v1",
        market_slug=MARKET_SLUG,
        question=QUESTION,
        fair_probability_yes=fair_probability_yes,
        confidence=Decimal("0.80"),
        yes_bid=Decimal("0.45"),
        no_bid=Decimal("0.30"),
        spread=Decimal("0.020"),
        resolution_risk=Decimal("0.100"),
        selected_side=selected_side,
        status=status,
        yes_result=_side_result("yes", yes_price, yes_net),
        no_result=_side_result("no", no_price, no_net),
        gate_results=_all_gates(),
    )


def _candidate(
    *,
    screening_status: str = "screening_ready",
    source_status: str = "paper_review_ready",
    valid_depth: bool = True,
    scoring_side: str = "yes",
    screening_score: Decimal = Decimal("0.500000"),
    reason_codes: tuple[str, ...] = ("source_paper_review_ready", "yes_depth_ready"),
) -> PaperProjectScreeningCandidate:
    return PaperProjectScreeningCandidate(
        market_slug=MARKET_SLUG,
        question=QUESTION,
        source_status=source_status,
        scoring_side=scoring_side,
        valid_depth=valid_depth,
        net_edge_per_share=Decimal("0.050"),
        total_cost_per_share=Decimal("0.006"),
        ask_size=Decimal("100"),
        edge_component=Decimal("0.050000"),
        confidence_component=Decimal("0.000000"),
        depth_component=Decimal("0.000000"),
        spread_penalty=Decimal("0.000000"),
        resolution_risk_penalty=Decimal("0.000000"),
        cost_penalty=Decimal("0.000000"),
        screening_score=screening_score,
        screening_status=screening_status,
        reason_codes=reason_codes,
    )


def _config(**overrides: Any) -> PaperExecutionConfig:
    defaults: dict[str, Any] = dict(
        config_version="paper-execution-v1",
        strategy_type="book_imbalance_screening_paper",
        paper_budget_size=Decimal("10"),
        sizing_limiter="screening_book_depth",
        planned_exit_rule="hold_to_resolution",
        account_equity_before_trade=Decimal("10000"),
        thesis_template="Paper edge from screening reasons: {reason_codes}.",
        invalidating_conditions_template="Official resolution source changes materially.",
        rule_text="Buy screening-ready paper candidates against executable ask depth.",
        resolution_source_fallback="polymarket_event_resolution",
    )
    defaults.update(overrides)
    return PaperExecutionConfig(**defaults)


class _FakeArchiveEntry:
    """Duck-typed stand-in for ``RawArchiveEntry`` — payload_path + payload_sha256."""

    def __init__(self, payload_path: Path, payload_sha256: str) -> None:
        self.payload_path = payload_path
        self.payload_sha256 = payload_sha256


def _archive_entry(name: str = "book") -> _FakeArchiveEntry:
    return _FakeArchiveEntry(
        payload_path=Path(f"/tmp/raw/{name}.json"),
        payload_sha256="a" * 64,
    )


def _execute(
    *,
    candidate: PaperProjectScreeningCandidate | None = None,
    cost_aware_report: PaperCostAwareEventStrategyReport | None = None,
    market: NormalizedMarket | None = None,
    book: OrderBookSnapshot | None = None,
    config: PaperExecutionConfig | None = None,
    raw_book_archive_entry: _FakeArchiveEntry | None = None,
    market_raw_archive_entry: _FakeArchiveEntry | None = None,
    generated_at: datetime = GENERATED_AT,
) -> PaperExecutionResult:
    return execute_paper_trade_from_screening(
        candidate=candidate if candidate is not None else _candidate(),
        cost_aware_report=(
            cost_aware_report if cost_aware_report is not None else _cost_aware_report()
        ),
        market=market if market is not None else _market(),
        book=book if book is not None else _yes_book_with_depth(),
        raw_book_archive_entry=(
            raw_book_archive_entry if raw_book_archive_entry is not None else _archive_entry("book")
        ),
        market_raw_archive_entry=(
            market_raw_archive_entry
            if market_raw_archive_entry is not None
            else _archive_entry("market")
        ),
        config=config if config is not None else _config(),
        generated_at=generated_at,
    )


def _yes_book_with_depth() -> OrderBookSnapshot:
    return _book(
        YES_TOKEN_ID,
        bids=[(Decimal("0.45"), Decimal("50"))],
        asks=[(Decimal("0.50"), Decimal("50"))],
    )


def _no_book_with_depth() -> OrderBookSnapshot:
    return _book(
        NO_TOKEN_ID,
        bids=[(Decimal("0.30"), Decimal("50"))],
        asks=[(Decimal("0.35"), Decimal("50"))],
    )


# --------------------------------------------------------------------------
# (a) Happy path.
# --------------------------------------------------------------------------


def test_happy_path_executes_and_journals_valid_record():
    result = _execute()

    assert result.skipped_reason is None
    assert isinstance(result.fill, PaperFill)
    assert result.fill.filled_size > 0
    assert isinstance(result.record, PaperTradeRecord)
    assert result.fill.filled_size == result.record.fill_filled_size
    assert result.fill.token_id == YES_TOKEN_ID
    assert result.token_id == YES_TOKEN_ID
    assert result.condition_id == CONDITION_ID
    assert result.market_slug == MARKET_SLUG
    assert result.generated_at == GENERATED_AT


# --------------------------------------------------------------------------
# (b) not_screening_ready skip — either status fails.
# --------------------------------------------------------------------------


def test_skip_not_screening_ready_when_screening_status_not_ready():
    result = _execute(candidate=_candidate(screening_status="screening_watch"))

    assert result.skipped_reason == "not_screening_ready"
    assert result.fill is None
    assert result.record is None


def test_skip_not_screening_ready_when_source_status_not_paper_review():
    result = _execute(
        candidate=_candidate(
            screening_status="screening_ready",
            source_status="watch",
        )
    )

    assert result.skipped_reason == "not_screening_ready"
    assert result.fill is None
    assert result.record is None


# --------------------------------------------------------------------------
# (c) invalid_depth skip.
# --------------------------------------------------------------------------


def test_skip_invalid_depth_when_valid_depth_false():
    result = _execute(
        candidate=_candidate(
            screening_status="screening_ready",
            source_status="paper_review_ready",
            valid_depth=False,
        )
    )

    assert result.skipped_reason == "invalid_depth"
    assert result.fill is None
    assert result.record is None


# --------------------------------------------------------------------------
# (d) no_executable_depth skip.
# --------------------------------------------------------------------------


def test_skip_no_executable_depth_when_asks_non_executable():
    book = _book(
        YES_TOKEN_ID,
        bids=[(Decimal("0.45"), Decimal("50"))],
        asks=[(Decimal("0.50"), Decimal("0"))],  # non-executable
    )
    result = _execute(book=book)

    assert result.skipped_reason == "no_executable_depth"
    assert result.fill is None
    assert result.record is None


# --------------------------------------------------------------------------
# (e) no_bid skip — asks-only book yields bid=None.
# --------------------------------------------------------------------------


def test_skip_no_bid_when_book_is_asks_only():
    book = _book(
        YES_TOKEN_ID,
        bids=[],  # asks-only → bid is None
        asks=[(Decimal("0.50"), Decimal("50"))],
    )
    result = _execute(book=book)

    assert result.skipped_reason == "no_bid"
    assert result.fill is None
    assert result.record is None


# --------------------------------------------------------------------------
# (f) Sizing: order_size = min(paper_budget_size, executable_ask_depth).
# --------------------------------------------------------------------------


def test_sizing_clamps_to_executable_ask_depth():
    # Budget larger than depth → order_size = depth (10).
    book = _book(
        YES_TOKEN_ID,
        bids=[(Decimal("0.45"), Decimal("50"))],
        asks=[(Decimal("0.50"), Decimal("10"))],
    )
    result = _execute(book=book, config=_config(paper_budget_size=Decimal("20")))

    assert result.skipped_reason is None
    assert result.record is not None
    assert result.record.order_requested_size == Decimal("10")
    assert result.record.fill_filled_size == Decimal("10")
    assert result.record.max_executable_size == Decimal("10")


def test_sizing_clamps_to_budget_when_depth_larger():
    # Budget smaller than depth → order_size = budget (5).
    book = _book(
        YES_TOKEN_ID,
        bids=[(Decimal("0.45"), Decimal("50"))],
        asks=[(Decimal("0.50"), Decimal("50"))],
    )
    result = _execute(book=book, config=_config(paper_budget_size=Decimal("5")))

    assert result.skipped_reason is None
    assert result.record is not None
    assert result.record.order_requested_size == Decimal("5")
    assert result.record.max_executable_size == Decimal("50")


# --------------------------------------------------------------------------
# (g) side="buy" always — both yes and no outcomes produce a BUY order.
# --------------------------------------------------------------------------


def test_yes_outcome_produces_buy_order():
    result = _execute(
        candidate=_candidate(scoring_side="yes"),
        book=_yes_book_with_depth(),
    )

    assert result.skipped_reason is None
    assert result.record is not None
    assert result.record.order_side == "buy"
    assert result.side == "yes"
    assert result.record.outcome_name == "YES"


def test_no_outcome_produces_buy_order():
    result = _execute(
        candidate=_candidate(scoring_side="no"),
        book=_no_book_with_depth(),
    )

    assert result.skipped_reason is None
    assert result.record is not None
    assert result.record.order_side == "buy"
    assert result.side == "no"
    assert result.record.outcome_name == "NO"


# --------------------------------------------------------------------------
# (h) strategy_type marker in record.
# --------------------------------------------------------------------------


def test_strategy_type_marker_propagated_to_record():
    result = _execute(config=_config(strategy_type="custom_screening_paper"))

    assert result.skipped_reason is None
    assert result.record is not None
    assert result.record.strategy_type == "custom_screening_paper"


# --------------------------------------------------------------------------
# (i) ResearchPacket created_at (NOT generated_at) + source_score + rule_text_hash.
# --------------------------------------------------------------------------


def test_research_packet_uses_created_at_source_score_and_rule_text_hash():
    config = _config(rule_text="Buy screening-ready paper candidates against executable ask depth.")
    expected_hash = hashlib.sha256(config.rule_text.encode("utf-8")).hexdigest()
    candidate = _candidate(screening_score=Decimal("0.420000"))

    result = _execute(candidate=candidate, config=config)

    assert result.skipped_reason is None
    assert result.record is not None
    # created_at (not generated_at) — record exposes packet_created_at.
    assert result.record.packet_created_at == GENERATED_AT
    # source_score is the stringified screening_score.
    assert result.record.source_score == str(Decimal("0.420000"))
    # rule_text_hash is a lowercase 64-char sha256 hex digest matching the rule text.
    assert result.record.rule_text_hash == expected_hash
    assert len(result.record.rule_text_hash) == 64
    assert result.record.rule_text_hash == result.record.rule_text_hash.lower()


# --------------------------------------------------------------------------
# (j) paper_only/report_only + immutability + invariant.
# --------------------------------------------------------------------------


def test_result_is_paper_only_and_report_only():
    result = _execute()

    assert result.paper_only is True
    assert result.report_only is True


def test_result_is_frozen():
    result = _execute()

    with pytest.raises(Exception):
        result.fill = None  # type: ignore[misc]


def test_result_invariant_skipped_reason_none_requires_fill_and_record():
    # skipped_reason is None but fill/record None → invariant violation.
    with pytest.raises(ValueError):
        PaperExecutionResult(
            generated_at=GENERATED_AT,
            market_slug=MARKET_SLUG,
            condition_id=CONDITION_ID,
            token_id=YES_TOKEN_ID,
            side="yes",
            fill=None,
            record=None,
            skipped_reason=None,
        )


def test_result_invariant_executed_requires_skipped_reason_none():
    # fill/record present but skipped_reason set → invariant violation.
    fill = _execute().fill
    record = _execute().record
    assert fill is not None and record is not None
    with pytest.raises(ValueError):
        PaperExecutionResult(
            generated_at=GENERATED_AT,
            market_slug=MARKET_SLUG,
            condition_id=CONDITION_ID,
            token_id=YES_TOKEN_ID,
            side="yes",
            fill=fill,
            record=record,
            skipped_reason="no_bid",
        )


def test_result_rejects_paper_only_false():
    with pytest.raises(ValueError):
        PaperExecutionResult(
            generated_at=GENERATED_AT,
            market_slug=MARKET_SLUG,
            condition_id=CONDITION_ID,
            token_id=YES_TOKEN_ID,
            side="yes",
            fill=None,
            record=None,
            skipped_reason="no_bid",
            paper_only=False,
        )


def test_config_rejects_nonpositive_paper_budget_size():
    with pytest.raises(ValueError):
        _config(paper_budget_size=Decimal("0"))


def test_config_rejects_nonpositive_account_equity():
    with pytest.raises(ValueError):
        _config(account_equity_before_trade=Decimal("0"))


def test_config_rejects_blank_rule_text():
    with pytest.raises(ValueError):
        _config(rule_text="  ")


# --------------------------------------------------------------------------
# (k) JSONL round-trip via PaperExecutionLog.
# --------------------------------------------------------------------------


def test_paper_execution_log_round_trip(tmp_path):
    log_path = tmp_path / "paper_execution.jsonl"
    log = PaperExecutionLog(log_path)

    executed = _execute()
    skipped = _execute(candidate=_candidate(screening_status="screening_watch"))

    log.append(executed)
    log.append(skipped)

    lines = log_path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 2

    first = json.loads(lines[0])
    assert first["market_slug"] == MARKET_SLUG
    assert first["condition_id"] == CONDITION_ID
    assert first["token_id"] == YES_TOKEN_ID
    assert first["side"] == "yes"
    assert first["skipped_reason"] is None
    assert first["paper_only"] is True
    assert first["report_only"] is True
    # Nested record + fill round-tripped as dicts with Decimal-as-str.
    assert first["record"]["strategy_type"] == "book_imbalance_screening_paper"
    assert first["record"]["order_side"] == "buy"
    assert first["fill"]["filled_size"] == "10"

    second = json.loads(lines[1])
    assert second["skipped_reason"] == "not_screening_ready"
    assert second["fill"] is None
    assert second["record"] is None


def test_paper_execution_log_rejects_non_result(tmp_path):
    log = PaperExecutionLog(tmp_path / "paper_execution.jsonl")
    with pytest.raises(ValueError):
        log.append("not-a-result")  # type: ignore[arg-type]
