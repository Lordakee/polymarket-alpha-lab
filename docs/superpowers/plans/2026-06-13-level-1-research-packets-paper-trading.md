# Level 1 Research Packets And Paper Trading Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Level 1A automation: convert Level 0A scored candidates into auditable research packets, simulate paper fills against bid/ask order books, and persist paper-trade journal records without authentication or live orders.

**Architecture:** Keep research, fill simulation, and journal persistence separate. Research packets describe why a candidate deserves paper testing; paper fill simulation models executable bid/ask fills; the journal records only complete packets and simulated fills. No module may place orders, sign payloads, authenticate, cancel orders, open user WebSockets, send heartbeat requests, or touch private keys.

**Tech Stack:** Python 3.11+, standard library only, frozen dataclasses, `Decimal`, JSON/JSONL files, `pytest`, existing Level 0A domain/pipeline objects.

---

## Review And Execution Protocol

1. Submit this plan to Claude Code with model `claude-opus-4-8`, effort `max`, read-only permissions before implementation.
2. Do not implement Level 1A until Claude Code returns `Proceed` or `Proceed with fixes` and all Critical/Important findings are resolved.
3. Before committing each node, submit the new code plus the next node plan to Claude Code.
4. Run the node-specific pytest command and full pytest before each commit.
5. After each node, write a Handoff Summary with repo status, verified commands, uncommitted files, Claude review status, and next step.

Level 1A must not add:

- account authentication
- private-key handling
- live trading
- automated order placement
- order cancellation
- user WebSocket
- REST heartbeat
- compliance/legal/geographic-access analysis

## Level 1A Scope Versus Level 1B Scope

Level 1A is a minimal paper-trading loop. It may create research packets, simulate fills from public order books, and append complete paper records to a JSONL journal. It may reject incomplete packets by raising local validation errors before journaling. It may not build portfolio-level state, order placement, or automated account actions.

Level 1B is deferred. It will add rejected-candidate logs, configurable risk gates, risk constants, paper positions, daily executable NAV marks, exposure analytics, performance reports, richer packet evidence, and dashboards. The Level 1A journal stores enough fields for Level 1B analytics to consume later, but Level 1A does not calculate daily marks, realized PnL, holding days, calibration, or drawdown metrics.

## Target File Structure

- Create: `src/polymarket_alpha_lab/research.py`
  - Research packet dataclass, required-field validation, rule-text hashing.
- Create: `src/polymarket_alpha_lab/paper.py`
  - Paper order dataclass and order-book-walk fill simulation.
- Create: `src/polymarket_alpha_lab/journal.py`
  - JSONL paper-trade journal writer.
- Modify: `src/polymarket_alpha_lab/__init__.py`
  - Export stable Level 1 public dataclasses.
- Create: `tests/test_research.py`
  - Research packet construction and required-field tests.
- Create: `tests/test_paper.py`
  - Bid/ask fill simulation tests, including partial fills.
- Create: `tests/test_journal.py`
  - Journal persistence and validation tests.
- Modify: `README.md`
  - Add Level 1A status note after implementation.

## Node 1: Research Packets

**Goal:** Define auditable research packets that can carry a candidate into paper trading only when thesis, invalidation, rule text, execution-cost fields, and risk context are present.

**Files:**

- Create: `src/polymarket_alpha_lab/research.py`
- Create: `tests/test_research.py`

- [ ] **Step 1: Write failing research packet tests**

Create `tests/test_research.py` with:

```python
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.pipeline import ScoredCandidate
from polymarket_alpha_lab.research import build_research_packet


def candidate() -> ScoredCandidate:
    return ScoredCandidate(
        condition_id="0xabc",
        token_id="111",
        market_slug="example-market",
        question="Will the example resolve yes?",
        total_score="78.500",
        raw_archive_path="data/raw/gamma/markets.json",
    )


def test_build_research_packet_records_required_review_fields():
    packet = build_research_packet(
        candidate=candidate(),
        created_at=datetime(2026, 6, 13, 12, 30, tzinfo=UTC),
        market_url="https://polymarket.com/event/example-market",
        outcome_name="Yes",
        strategy_type="market_quality",
        model_probability=Decimal("0.56"),
        bid=Decimal("0.50"),
        ask=Decimal("0.52"),
        midpoint=Decimal("0.51"),
        expected_entry_price=Decimal("0.514"),
        fair_value_estimate=Decimal("0.56"),
        theoretical_edge=Decimal("0.046"),
        spread=Decimal("0.02"),
        slippage_estimate=Decimal("0.004"),
        cost_adjusted_edge=Decimal("0.026"),
        confidence=Decimal("0.60"),
        max_executable_size=Decimal("100"),
        risk_tags=("liquidity", "rules"),
        thesis="Market is active with tight spread and clear rules.",
        invalidating_conditions="Spread widens above threshold or rules change.",
        rule_text="Example resolution source text.",
        resolution_source="Example source",
    )

    assert packet.packet_id == "0xabc:111:20260613T123000Z"
    assert packet.condition_id == "0xabc"
    assert packet.token_id == "111"
    assert packet.market_url == "https://polymarket.com/event/example-market"
    assert packet.expected_entry_price == Decimal("0.514")
    assert len(packet.rule_text_hash) == 64
    assert packet.is_complete is True
    assert packet.missing_required_fields() == []


def test_research_packet_reports_missing_required_fields():
    packet = build_research_packet(
        candidate=candidate(),
        created_at=datetime(2026, 6, 13, 12, 30, tzinfo=UTC),
        market_url="",
        outcome_name="",
        strategy_type="market_quality",
        model_probability=None,
        bid=None,
        ask=None,
        midpoint=None,
        expected_entry_price=None,
        fair_value_estimate=None,
        theoretical_edge=None,
        spread=None,
        slippage_estimate=None,
        cost_adjusted_edge=None,
        confidence=Decimal("0.40"),
        max_executable_size=Decimal("0"),
        risk_tags=(),
        thesis="",
        invalidating_conditions="",
        rule_text="",
        resolution_source="",
    )

    assert packet.is_complete is False
    assert packet.missing_required_fields() == [
        "market_url",
        "outcome_name",
        "model_probability",
        "bid",
        "ask",
        "midpoint",
        "expected_entry_price",
        "spread",
        "slippage_estimate",
        "cost_adjusted_edge",
        "thesis",
        "invalidating_conditions",
        "rule_text",
        "resolution_source",
        "positive_max_executable_size",
    ]
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/python -m pytest tests/test_research.py -q
```

Expected: import failure because `polymarket_alpha_lab.research` does not exist.

- [ ] **Step 3: Implement research packets**

Create `src/polymarket_alpha_lab/research.py` with:

```python
"""Research packets for Level 1 paper-trading candidates."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.pipeline import ScoredCandidate


@dataclass(frozen=True)
class ResearchPacket:
    packet_id: str
    condition_id: str
    token_id: str
    market_slug: str
    market_url: str
    question: str
    outcome_name: str
    created_at: datetime
    strategy_type: str
    model_probability: Decimal | None
    bid: Decimal | None
    ask: Decimal | None
    midpoint: Decimal | None
    expected_entry_price: Decimal | None
    fair_value_estimate: Decimal | None
    theoretical_edge: Decimal | None
    spread: Decimal | None
    slippage_estimate: Decimal | None
    cost_adjusted_edge: Decimal | None
    confidence: Decimal
    max_executable_size: Decimal
    risk_tags: tuple[str, ...]
    thesis: str
    invalidating_conditions: str
    rule_text: str
    rule_text_hash: str
    resolution_source: str
    source_score: str
    raw_archive_path: str

    @property
    def is_complete(self) -> bool:
        return not self.missing_required_fields()

    def missing_required_fields(self) -> list[str]:
        missing: list[str] = []
        required_values = {
            "market_url": self.market_url,
            "outcome_name": self.outcome_name,
            "model_probability": self.model_probability,
            "bid": self.bid,
            "ask": self.ask,
            "midpoint": self.midpoint,
            "expected_entry_price": self.expected_entry_price,
            "spread": self.spread,
            "slippage_estimate": self.slippage_estimate,
            "cost_adjusted_edge": self.cost_adjusted_edge,
            "thesis": self.thesis,
            "invalidating_conditions": self.invalidating_conditions,
            "rule_text": self.rule_text,
            "resolution_source": self.resolution_source,
        }
        for field_name, value in required_values.items():
            if value is None:
                missing.append(field_name)
            elif isinstance(value, str) and not value.strip():
                missing.append(field_name)
        if self.max_executable_size <= 0:
            missing.append("positive_max_executable_size")
        return missing


def build_research_packet(
    *,
    candidate: ScoredCandidate,
    created_at: datetime,
    market_url: str,
    outcome_name: str,
    strategy_type: str,
    model_probability: Decimal | None,
    bid: Decimal | None,
    ask: Decimal | None,
    midpoint: Decimal | None,
    expected_entry_price: Decimal | None,
    fair_value_estimate: Decimal | None,
    theoretical_edge: Decimal | None,
    spread: Decimal | None,
    slippage_estimate: Decimal | None,
    cost_adjusted_edge: Decimal | None,
    confidence: Decimal,
    max_executable_size: Decimal,
    risk_tags: tuple[str, ...],
    thesis: str,
    invalidating_conditions: str,
    rule_text: str,
    resolution_source: str,
) -> ResearchPacket:
    timestamp = _format_packet_timestamp(created_at)
    return ResearchPacket(
        packet_id=f"{candidate.condition_id}:{candidate.token_id}:{timestamp}",
        condition_id=candidate.condition_id,
        token_id=candidate.token_id,
        market_slug=candidate.market_slug,
        market_url=market_url,
        question=candidate.question,
        outcome_name=outcome_name,
        created_at=created_at,
        strategy_type=strategy_type,
        model_probability=model_probability,
        bid=bid,
        ask=ask,
        midpoint=midpoint,
        expected_entry_price=expected_entry_price,
        fair_value_estimate=fair_value_estimate,
        theoretical_edge=theoretical_edge,
        spread=spread,
        slippage_estimate=slippage_estimate,
        cost_adjusted_edge=cost_adjusted_edge,
        confidence=confidence,
        max_executable_size=max_executable_size,
        risk_tags=risk_tags,
        thesis=thesis,
        invalidating_conditions=invalidating_conditions,
        rule_text=rule_text,
        rule_text_hash=_hash_text(rule_text),
        resolution_source=resolution_source,
        source_score=candidate.total_score,
        raw_archive_path=candidate.raw_archive_path,
    )


def _format_packet_timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
```

- [ ] **Step 4: Run node tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_research.py tests/test_pipeline.py -q
```

Expected: all selected tests pass.

- [ ] **Step 5: Request Claude Code review before commit**

Run:

```bash
claude -p --model claude-opus-4-8 --effort max --permission-mode plan "Review Level 1A Node 1 research packet changes in /home/ubuntu/polymarket-alpha-lab. Requirements: auditable packet fields, complete/missing required field checks, execution-cost fields, rule text hash, no auth, no private keys, no order placement, no live trading. Also review next node plan: bid/ask paper fill simulation. Report Critical, Important, Minor findings only."
```

- [ ] **Step 6: Commit Node 1**

Run:

```bash
git add src/polymarket_alpha_lab/research.py tests/test_research.py
git commit -m "feat: add research packets"
git push
```

## Node 2: Paper Fill Simulation

**Goal:** Simulate paper fills from an order book using executable bid/ask levels, not midpoint.

**Files:**

- Create: `src/polymarket_alpha_lab/paper.py`
- Create: `tests/test_paper.py`

- [ ] **Step 1: Write failing paper fill tests**

Create `tests/test_paper.py` with:

```python
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.domain import OrderBookLevel, OrderBookSnapshot
from polymarket_alpha_lab.paper import PaperOrder, simulate_order_book_fill


def test_simulate_buy_fill_walks_asks_and_reports_execution_costs():
    book = OrderBookSnapshot(
        token_id="111",
        bids=(OrderBookLevel(Decimal("0.49"), Decimal("50")),),
        asks=(
            OrderBookLevel(Decimal("0.51"), Decimal("60")),
            OrderBookLevel(Decimal("0.52"), Decimal("60")),
        ),
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )
    order = PaperOrder(token_id="111", side="buy", size=Decimal("100"))

    fill = simulate_order_book_fill(order, book)

    assert fill.filled_size == Decimal("100")
    assert fill.unfilled_size == Decimal("0")
    assert fill.average_price == Decimal("0.514")
    assert fill.worst_price == Decimal("0.52")
    assert fill.best_bid == Decimal("0.49")
    assert fill.best_ask == Decimal("0.51")
    assert fill.midpoint == Decimal("0.50")
    assert fill.spread == Decimal("0.02")
    assert fill.slippage_estimate == Decimal("0.004")
    assert fill.is_complete is True


def test_simulate_sell_fill_walks_bids_and_reports_partial_fill():
    book = OrderBookSnapshot(
        token_id="111",
        bids=(
            OrderBookLevel(Decimal("0.49"), Decimal("25")),
            OrderBookLevel(Decimal("0.48"), Decimal("25")),
        ),
        asks=(OrderBookLevel(Decimal("0.51"), Decimal("100")),),
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )
    order = PaperOrder(token_id="111", side="sell", size=Decimal("100"))

    fill = simulate_order_book_fill(order, book)

    assert fill.filled_size == Decimal("50")
    assert fill.unfilled_size == Decimal("50")
    assert fill.average_price == Decimal("0.485")
    assert fill.worst_price == Decimal("0.48")
    assert fill.best_bid == Decimal("0.49")
    assert fill.best_ask == Decimal("0.51")
    assert fill.midpoint == Decimal("0.50")
    assert fill.spread == Decimal("0.02")
    assert fill.slippage_estimate == Decimal("0.005")
    assert fill.is_complete is False
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/python -m pytest tests/test_paper.py -q
```

Expected: import failure because `polymarket_alpha_lab.paper` does not exist.

- [ ] **Step 3: Implement paper fill simulation**

Create `src/polymarket_alpha_lab/paper.py` with:

```python
"""Bid/ask paper-trading fill simulation."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from polymarket_alpha_lab.domain import OrderBookLevel, OrderBookSnapshot


PaperSide = Literal["buy", "sell"]


@dataclass(frozen=True)
class PaperOrder:
    token_id: str
    side: PaperSide
    size: Decimal


@dataclass(frozen=True)
class PaperFill:
    token_id: str
    side: PaperSide
    requested_size: Decimal
    filled_size: Decimal
    unfilled_size: Decimal
    average_price: Decimal | None
    worst_price: Decimal | None
    best_bid: Decimal | None
    best_ask: Decimal | None
    midpoint: Decimal | None
    spread: Decimal | None
    slippage_estimate: Decimal | None

    @property
    def is_complete(self) -> bool:
        return self.unfilled_size == 0


def simulate_order_book_fill(order: PaperOrder, book: OrderBookSnapshot) -> PaperFill:
    if order.token_id != book.token_id:
        raise ValueError("order token_id must match order book token_id")
    if order.size <= 0:
        raise ValueError("paper order size must be positive")
    levels = book.asks if order.side == "buy" else book.bids
    filled_size, notional, worst_price = _walk_levels(order.size, levels)
    average_price = None if filled_size == 0 else (notional / filled_size).quantize(Decimal("0.001"))
    slippage_estimate = _estimate_slippage(
        side=order.side,
        average_price=average_price,
        best_bid=book.best_bid,
        best_ask=book.best_ask,
    )
    return PaperFill(
        token_id=order.token_id,
        side=order.side,
        requested_size=order.size,
        filled_size=filled_size,
        unfilled_size=order.size - filled_size,
        average_price=average_price,
        worst_price=worst_price,
        best_bid=book.best_bid,
        best_ask=book.best_ask,
        midpoint=None if book.midpoint is None else book.midpoint.quantize(Decimal("0.001")),
        spread=book.spread,
        slippage_estimate=slippage_estimate,
    )


def _walk_levels(
    requested_size: Decimal, levels: tuple[OrderBookLevel, ...]
) -> tuple[Decimal, Decimal, Decimal | None]:
    remaining = requested_size
    filled_size = Decimal("0")
    notional = Decimal("0")
    worst_price: Decimal | None = None
    for level in levels:
        if remaining <= 0:
            break
        if level.size <= 0:
            continue
        take_size = min(remaining, level.size)
        filled_size += take_size
        notional += take_size * level.price
        remaining -= take_size
        worst_price = level.price
    return filled_size, notional, worst_price


def _estimate_slippage(
    *,
    side: PaperSide,
    average_price: Decimal | None,
    best_bid: Decimal | None,
    best_ask: Decimal | None,
) -> Decimal | None:
    if average_price is None:
        return None
    if side == "buy":
        if best_ask is None:
            return None
        return max(Decimal("0"), average_price - best_ask).quantize(Decimal("0.001"))
    if best_bid is None:
        return None
    return max(Decimal("0"), best_bid - average_price).quantize(Decimal("0.001"))
```

- [ ] **Step 4: Run node tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_paper.py tests/test_domain.py -q
```

Expected: all selected tests pass.

- [ ] **Step 5: Request Claude Code review before commit**

Run:

```bash
claude -p --model claude-opus-4-8 --effort max --permission-mode plan "Review Level 1A Node 2 paper fill simulation changes in /home/ubuntu/polymarket-alpha-lab. Requirements: uses asks for buy, bids for sell, walks depth, reports partial fills, records bid/ask/midpoint/spread/slippage, does not use midpoint fills, no auth, no order placement, no live trading. Also review next node plan: JSONL paper-trade journal. Report Critical, Important, Minor findings only."
```

- [ ] **Step 6: Commit Node 2**

Run:

```bash
git add src/polymarket_alpha_lab/paper.py tests/test_paper.py
git commit -m "feat: simulate paper fills"
git push
```

## Node 3: Paper Trade Journal

**Goal:** Persist paper-trade records only when a research packet is complete and a simulated fill exists.

**Files:**

- Create: `src/polymarket_alpha_lab/journal.py`
- Create: `tests/test_journal.py`
- Modify: `src/polymarket_alpha_lab/__init__.py`
- Modify: `README.md`

- [ ] **Step 1: Write failing journal tests**

Create `tests/test_journal.py` with:

```python
import json
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.journal import PaperTradeJournal, PaperTradeRecord
from polymarket_alpha_lab.paper import PaperFill
from polymarket_alpha_lab.pipeline import ScoredCandidate
from polymarket_alpha_lab.research import build_research_packet


def complete_packet():
    return build_research_packet(
        candidate=ScoredCandidate(
            condition_id="0xabc",
            token_id="111",
            market_slug="example-market",
            question="Will the example resolve yes?",
            total_score="78.500",
            raw_archive_path="data/raw/gamma/markets.json",
        ),
        created_at=datetime(2026, 6, 13, 12, 30, tzinfo=UTC),
        market_url="https://polymarket.com/event/example-market",
        outcome_name="Yes",
        strategy_type="market_quality",
        model_probability=Decimal("0.56"),
        bid=Decimal("0.50"),
        ask=Decimal("0.52"),
        midpoint=Decimal("0.51"),
        expected_entry_price=Decimal("0.514"),
        fair_value_estimate=Decimal("0.56"),
        theoretical_edge=Decimal("0.046"),
        spread=Decimal("0.02"),
        slippage_estimate=Decimal("0.004"),
        cost_adjusted_edge=Decimal("0.026"),
        confidence=Decimal("0.60"),
        max_executable_size=Decimal("100"),
        risk_tags=("liquidity",),
        thesis="Tight spread and clear rules.",
        invalidating_conditions="Spread widens.",
        rule_text="Example rule.",
        resolution_source="Example source",
    )


def complete_fill():
    return PaperFill(
        token_id="111",
        side="buy",
        requested_size=Decimal("100"),
        filled_size=Decimal("100"),
        unfilled_size=Decimal("0"),
        average_price=Decimal("0.514"),
        worst_price=Decimal("0.52"),
        best_bid=Decimal("0.49"),
        best_ask=Decimal("0.51"),
        midpoint=Decimal("0.50"),
        spread=Decimal("0.02"),
        slippage_estimate=Decimal("0.004"),
    )


def test_paper_trade_journal_appends_jsonl_record(tmp_path):
    journal = PaperTradeJournal(path=tmp_path / "paper-trades.jsonl")
    packet = complete_packet()
    fill = complete_fill()
    record = PaperTradeRecord.from_packet_and_fill(
        packet=packet,
        fill=fill,
        decision_timestamp=datetime(2026, 6, 13, 12, 31, tzinfo=UTC),
        account_equity=Decimal("10000"),
        sizing_limiter="max_executable_size",
        exit_rule="Mark at executable bid daily.",
    )

    journal.append(record)

    lines = journal.path.read_text().splitlines()
    assert len(lines) == 1
    stored = json.loads(lines[0])
    assert stored["packet_id"] == packet.packet_id
    assert stored["market_url"] == "https://polymarket.com/event/example-market"
    assert stored["outcome_name"] == "Yes"
    assert stored["rule_text_hash"] == packet.rule_text_hash
    assert stored["resolution_source"] == "Example source"
    assert stored["model_probability"] == "0.56"
    assert stored["research_bid"] == "0.50"
    assert stored["research_ask"] == "0.52"
    assert stored["bid"] == "0.49"
    assert stored["ask"] == "0.51"
    assert stored["midpoint"] == "0.50"
    assert stored["spread"] == "0.02"
    assert stored["slippage_estimate"] == "0.004"
    assert stored["expected_entry_price"] == "0.514"
    assert stored["simulated_fill_price"] == "0.514"
    assert stored["fair_value_estimate"] == "0.56"
    assert stored["theoretical_edge"] == "0.046"
    assert stored["final_size"] == "100"
    assert stored["exit_rule"] == "Mark at executable bid daily."


def test_paper_trade_record_rejects_incomplete_packet():
    packet = complete_packet()
    incomplete_packet = build_research_packet(
        candidate=ScoredCandidate(
            condition_id=packet.condition_id,
            token_id=packet.token_id,
            market_slug=packet.market_slug,
            question=packet.question,
            total_score=packet.source_score,
            raw_archive_path=packet.raw_archive_path,
        ),
        created_at=packet.created_at,
        market_url=packet.market_url,
        outcome_name=packet.outcome_name,
        strategy_type=packet.strategy_type,
        model_probability=packet.model_probability,
        bid=packet.bid,
        ask=packet.ask,
        midpoint=packet.midpoint,
        expected_entry_price=None,
        fair_value_estimate=packet.fair_value_estimate,
        theoretical_edge=packet.theoretical_edge,
        spread=packet.spread,
        slippage_estimate=packet.slippage_estimate,
        cost_adjusted_edge=packet.cost_adjusted_edge,
        confidence=packet.confidence,
        max_executable_size=packet.max_executable_size,
        risk_tags=packet.risk_tags,
        thesis=packet.thesis,
        invalidating_conditions=packet.invalidating_conditions,
        rule_text=packet.rule_text,
        resolution_source=packet.resolution_source,
    )

    try:
        PaperTradeRecord.from_packet_and_fill(
            packet=incomplete_packet,
            fill=complete_fill(),
            decision_timestamp=datetime(2026, 6, 13, 12, 31, tzinfo=UTC),
            account_equity=Decimal("10000"),
            sizing_limiter="max_executable_size",
            exit_rule="Mark at executable bid daily.",
        )
    except ValueError as exc:
        assert "incomplete research packet" in str(exc)
        assert "expected_entry_price" in str(exc)
    else:
        raise AssertionError("expected incomplete packet rejection")
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
.venv/bin/python -m pytest tests/test_journal.py -q
```

Expected: import failure because `polymarket_alpha_lab.journal` does not exist.

- [ ] **Step 3: Implement journal**

Create `src/polymarket_alpha_lab/journal.py` with:

```python
"""Paper-trade journal persistence."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from polymarket_alpha_lab.paper import PaperFill
from polymarket_alpha_lab.research import ResearchPacket


@dataclass(frozen=True)
class PaperTradeRecord:
    packet_id: str
    condition_id: str
    token_id: str
    market_slug: str
    market_url: str
    question: str
    outcome_name: str
    side: str
    rule_text_hash: str
    resolution_source: str
    decision_timestamp: datetime
    model_probability: Decimal | None
    research_bid: Decimal | None
    research_ask: Decimal | None
    bid: Decimal | None
    ask: Decimal | None
    midpoint: Decimal | None
    expected_entry_price: Decimal | None
    spread: Decimal | None
    slippage_estimate: Decimal | None
    simulated_fill_price: Decimal | None
    worst_price: Decimal | None
    fair_value_estimate: Decimal | None
    theoretical_edge: Decimal | None
    cost_adjusted_edge: Decimal | None
    confidence: Decimal
    thesis: str
    invalidating_conditions: str
    account_equity: Decimal
    requested_size: Decimal
    final_size: Decimal
    unfilled_size: Decimal
    sizing_limiter: str
    exit_rule: str

    @classmethod
    def from_packet_and_fill(
        cls,
        *,
        packet: ResearchPacket,
        fill: PaperFill,
        decision_timestamp: datetime,
        account_equity: Decimal,
        sizing_limiter: str,
        exit_rule: str,
    ) -> "PaperTradeRecord":
        if not packet.is_complete:
            missing = ", ".join(packet.missing_required_fields())
            raise ValueError(f"incomplete research packet: {missing}")
        if packet.token_id != fill.token_id:
            raise ValueError("packet token_id must match paper fill token_id")
        if fill.filled_size <= 0:
            raise ValueError("paper fill must have positive filled_size")
        if not sizing_limiter.strip():
            raise ValueError("sizing_limiter is required")
        if not exit_rule.strip():
            raise ValueError("exit_rule is required")
        return cls(
            packet_id=packet.packet_id,
            condition_id=packet.condition_id,
            token_id=packet.token_id,
            market_slug=packet.market_slug,
            market_url=packet.market_url,
            question=packet.question,
            outcome_name=packet.outcome_name,
            side=fill.side,
            rule_text_hash=packet.rule_text_hash,
            resolution_source=packet.resolution_source,
            decision_timestamp=decision_timestamp,
            model_probability=packet.model_probability,
            research_bid=packet.bid,
            research_ask=packet.ask,
            bid=fill.best_bid,
            ask=fill.best_ask,
            midpoint=fill.midpoint,
            expected_entry_price=packet.expected_entry_price,
            spread=fill.spread,
            slippage_estimate=fill.slippage_estimate,
            simulated_fill_price=fill.average_price,
            worst_price=fill.worst_price,
            fair_value_estimate=packet.fair_value_estimate,
            theoretical_edge=packet.theoretical_edge,
            cost_adjusted_edge=packet.cost_adjusted_edge,
            confidence=packet.confidence,
            thesis=packet.thesis,
            invalidating_conditions=packet.invalidating_conditions,
            account_equity=account_equity,
            requested_size=fill.requested_size,
            final_size=fill.filled_size,
            unfilled_size=fill.unfilled_size,
            sizing_limiter=sizing_limiter,
            exit_rule=exit_rule,
        )


@dataclass(frozen=True)
class PaperTradeJournal:
    path: Path

    def append(self, record: PaperTradeRecord) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(_json_ready(asdict(record)), sort_keys=True) + "\n")


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return value
```

- [ ] **Step 4: Export stable Level 1 objects**

Modify `src/polymarket_alpha_lab/__init__.py` to:

```python
"""Domain skeleton for Polymarket Alpha Lab."""

from polymarket_alpha_lab.domain import (
    MarketScore,
    MarketSnapshot,
    NormalizedMarket,
    OrderBookLevel,
    OrderBookSnapshot,
    OutcomeToken,
)
from polymarket_alpha_lab.journal import PaperTradeJournal, PaperTradeRecord
from polymarket_alpha_lab.paper import PaperFill, PaperOrder
from polymarket_alpha_lab.research import ResearchPacket

__all__ = [
    "MarketScore",
    "MarketSnapshot",
    "NormalizedMarket",
    "OrderBookLevel",
    "OrderBookSnapshot",
    "OutcomeToken",
    "PaperFill",
    "PaperOrder",
    "PaperTradeJournal",
    "PaperTradeRecord",
    "ResearchPacket",
]
```

- [ ] **Step 5: Update README status**

Add this exact section after the current Level 0 usage section:

```markdown
## Level 1A Status

Level 1A adds research packets, bid/ask order-book-walk paper-fill simulation, and JSONL paper-trade journals. It remains paper-only: no account authentication, no private-key handling, no order placement, no order cancellation, no user WebSocket, no heartbeat, and no live trading.
```

- [ ] **Step 6: Run full verification**

Run:

```bash
.venv/bin/python -m pytest
codegraph sync .
codegraph status .
git diff --check
git status --short --branch
```

Expected:

- pytest reports all tests passing
- CodeGraph index is up to date
- `git diff --check` reports no whitespace errors
- only intentional files are modified or staged

- [ ] **Step 7: Request Claude Code review before final Level 1A push**

Run:

```bash
claude -p --model claude-opus-4-8 --effort max --permission-mode plan "Review all Level 1A research packet and paper trading changes in /home/ubuntu/polymarket-alpha-lab before final push. Requirements: auditable research packets, rule text hash, bid/ask order-book-walk paper fills, execution-cost fields, JSONL paper journal, no midpoint fills, no auth, no private keys, no order placement, no cancellation, no user WebSocket, no heartbeat, no live trading. Also review next-stage direction: Level 1B rejected-candidate logs, configurable risk gates, paper positions, daily executable NAV marks, exposure analytics, performance reports, richer packet evidence, and dashboards, still paper-only. Report Critical, Important, Minor findings only."
```

- [ ] **Step 8: Commit Node 3**

Run:

```bash
git add src/polymarket_alpha_lab/journal.py src/polymarket_alpha_lab/__init__.py README.md tests/test_journal.py
git commit -m "feat: journal paper trades"
git push
```

## Level 1A Completion Criteria

Level 1A is complete only when:

- research packets carry market id, market URL, token id, outcome, rule text hash, resolution source, model probability, thesis, invalidating conditions, bid, ask, midpoint, expected entry price, spread, slippage estimate, cost-adjusted edge, confidence, max executable size, and risk tags
- incomplete research packets are rejected before journaling
- paper fills use asks for buy and bids for sell
- paper fills walk order book depth and report partial fills
- paper fills record bid, ask, midpoint, spread, slippage estimate, average fill price, and worst fill price
- journal records are persisted as JSONL with research bid/ask, execution bid/ask, fair value, theoretical edge, Decimal values, and datetime values serialized safely
- Level 1B-only outputs are not implemented in Level 1A: rejected-candidate logs, portfolio positions, daily exit NAV, realized PnL, holding days, calibration, drawdown, dashboards, and risk-gate configuration
- all tests pass
- CodeGraph index is up to date
- Claude Code reviewed the plan and every code node before push
- GitHub `main` contains the verified commits

## Handoff Summary Template

```text
Handoff Summary
- Repo status: branch, latest commit, clean/dirty state, pushed/not pushed.
- Verified commands: exact commands and pass/fail result.
- Uncommitted files: list or "none".
- Claude review: model, review scope, unresolved findings.
- Next step: one concrete next action.
```
