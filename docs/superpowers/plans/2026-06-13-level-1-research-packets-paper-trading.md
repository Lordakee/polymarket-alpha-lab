# Level 1 Research Packets And Paper Trading Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Level 1A automation: convert Level 0A scored candidates into auditable research packets, simulate paper fills against bid/ask order books, and persist paper-trade journal records without authentication or live orders.

**Architecture:** Keep research, fill simulation, and journal persistence separate. Research packets describe why a candidate deserves paper testing; paper fill simulation models executable bid/ask fills; the journal records only complete packets and simulated fills. No module may place orders, sign payloads, authenticate, cancel orders, open user WebSockets, send heartbeat requests, or touch private keys.

**Tech Stack:** Python 3.11+, standard library only, frozen dataclasses, `Decimal`, JSON/JSONL files, `pytest`, existing Level 0A domain/pipeline objects.

---

## Review And Execution Protocol

1. Submit this plan to Claude Code with model `claude-opus-4-8`, effort `max`, read-only permissions before implementation.
2. Do not implement Level 1A until Claude Code returns `Proceed` or `Proceed with fixes` and all Critical/Important findings are resolved.
3. Before every node commit and push, run and record this required gate:
   - `git status --short --branch --untracked-files=all`; explicitly list untracked files or `none`.
   - the node-specific pytest command for that node.
   - `.venv/bin/python -m pytest`.
   - `git diff --check`.
   - `codegraph status .`; if stale or out of date, run `codegraph sync .` and then `codegraph status .` again.
   - Claude Code review with `claude-opus-4-8`, `--effort max`, and `--permission-mode plan`, covering the node diff, untracked files, verification output, and the next node plan when one exists.
4. Do not commit or push a node until all required gate items pass, Claude returns `Proceed` or `Proceed with fixes`, and all Claude Critical/Important findings are resolved.
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
    confidence: Decimal | None
    max_executable_size: Decimal | None
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
    confidence: Decimal | None,
    max_executable_size: Decimal | None,
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

- [ ] **Step 5: Run required pre-commit/pre-push gate for Node 1**

Run:

```bash
git status --short --branch --untracked-files=all
.venv/bin/python -m pytest tests/test_research.py tests/test_pipeline.py -q
.venv/bin/python -m pytest
git diff --check
codegraph status .
# If CodeGraph reports stale/out of date:
codegraph sync .
codegraph status .
```

Expected: untracked files are explicitly listed or `none`; node-specific pytest passes; full pytest passes; diff check reports no whitespace errors; CodeGraph is up to date.

- [ ] **Step 6: Request Claude Code review before commit/push**

Run:

```bash
claude -p --model claude-opus-4-8 --effort max --permission-mode plan "Review Level 1A Node 1 research packet changes in /home/ubuntu/polymarket-alpha-lab before commit/push. First run git status --short --branch --untracked-files=all and review all staged, unstaged, and untracked files. Confirm the recorded Node 1 gate includes node-specific pytest, full pytest, git diff --check, and CodeGraph status/sync-if-stale results. Requirements: auditable packet fields, complete/missing required field checks, execution-cost fields, rule text hash, no auth, no private keys, no order placement, no live trading. Also review next node plan: bid/ask paper fill simulation. Report Critical, Important, Minor findings only, and finish with an explicit verdict: Proceed, Proceed with fixes, or Blocked."
```

Do not run `git commit` or `git push` until Claude returns `Proceed` or `Proceed with fixes` and all Critical/Important findings are resolved.

- [ ] **Step 7: Commit Node 1 after gates pass**

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
  - Paper-fill simulation and normalized snapshot digesting.
- Modify: `src/polymarket_alpha_lab/normalize.py`
  - Coerce non-finite raw order-book Decimal values to zero before sorting.
- Modify: `src/polymarket_alpha_lab/domain.py`
  - Treat best bid/ask as best executable levels and suppress invalid or crossed spreads.
- Create: `tests/test_paper.py`
- Modify: `tests/test_normalize.py`
- Modify: `tests/test_domain.py`
- Modify: `tests/test_scoring.py`

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

- [ ] **Step 2b: Expand paper fill coverage before implementation**

Before implementing, expand `tests/test_paper.py` beyond the starter examples so the contract below is pinned. Minimum coverage must include:

- `PaperOrder` and `PaperFill` are frozen dataclasses.
- buy orders walk asks and sell orders walk bids.
- complete, partial, and zero fills.
- one-sided books: execution can occur on the traded side without midpoint/spread metadata.
- non-executable levels are skipped for execution and quote metadata when `price` or `size` is non-finite, zero, or negative.
- invalid order sizes reject non-finite, zero, and negative `Decimal` values with `ValueError`.
- `order_book_snapshot_sha256` is a lowercase 64-character hex digest, is independent of order side/size, changes when token id/capture time/levels change, includes bid/ask side labels, has at least one golden digest fixture, and canonicalizes equivalent finite `Decimal` spellings such as `Decimal("0.490")` and `Decimal("0.49")`.
- arithmetic is deterministic under hostile caller Decimal precision, rounding, and `Inexact`/`Rounded` traps.
- high-precision weighted average, midpoint, and spread values are not pre-rounded before final `Decimal("0.001")` `ROUND_HALF_EVEN` quantization.
- high-precision multi-level size accounting remains exact on both buy and sell paths.
- depth walking stops as soon as the requested size is filled, so later malformed levels are not inspected.
- normalized order-book sorting is compatible with the simulator.
- raw order-book payloads with non-finite Decimal values such as `NaN`, `Infinity`, and `-Infinity` normalize those values to zero before sorting, avoiding `decimal.InvalidOperation` before the paper-fill simulator can classify them as non-executable.
- shared `OrderBookSnapshot.best_bid` and `best_ask` ignore non-executable zero, negative, or non-finite levels so normalized malformed levels cannot pollute downstream scoring.
- shared `OrderBookSnapshot.spread` and `midpoint` return `None` when either side has no executable quote or the executable book is crossed (`best_ask <= best_bid`), and scoring does not reward those books as tight spreads.
- crossed-book spread metadata is preserved while execution still uses the requested side.

- [ ] **Step 3: Implement paper fill simulation**

Create `src/polymarket_alpha_lab/paper.py` with:

- `PaperSide = Literal["buy", "sell"]`
- frozen `PaperOrder(token_id, side, size)`
- frozen `PaperFill` fields:
  - `token_id`
  - `side`
  - `requested_size`
  - `order_book_captured_at`
  - `order_book_snapshot_sha256`
  - `filled_size`
  - `unfilled_size`
  - `average_price`
  - `worst_price`
  - `best_bid`
  - `best_ask`
  - `midpoint`
  - `spread`
  - `slippage_estimate`

Implement `simulate_order_book_fill(order, book)` so that:

- it rejects token mismatch, invalid side, and non-finite or non-positive order size
- buy orders walk executable ask levels; sell orders walk executable bid levels
- executable levels require finite `price`, finite `size`, `price > 0`, and `size > 0`
- top-of-book metadata uses the best executable bid and ask, not non-executable raw levels
- midpoint and spread are metadata only; fills never execute at midpoint
- depth walking stops as soon as the requested size is filled, so later levels cannot overwrite `worst_price`
- partial and zero fills are represented by `filled_size`, `unfilled_size`, and `is_complete`
- if the traded side has no executable levels, `filled_size` is zero and `average_price`, `worst_price`, and `slippage_estimate` are `None`
- if only the opposite side is missing, traded-side execution can still occur while `midpoint` and `spread` remain `None`
- `order_book_captured_at` is copied from `OrderBookSnapshot.captured_at`
- `order_book_snapshot_sha256` is a deterministic lowercase 64-character SHA-256 hex digest of the normalized order book token id, capture time, bid levels, and ask levels
- `order_book_snapshot_sha256` is independent of the paper order side and size
- finite Decimal prices and sizes are serialized canonically for `order_book_snapshot_sha256`, so numerically equal values such as `Decimal("0.490")` and `Decimal("0.49")` contribute the same hash text without quantizing distinct values
- average price, midpoint, spread, and slippage are quantized to `Decimal("0.001")` with explicit `ROUND_HALF_EVEN`
- fill arithmetic, including notional accumulation, division, spread, midpoint, slippage, and `unfilled_size`, is deterministic under hostile caller Decimal precision, rounding, and trap contexts
- size accounting remains exact for accepted finite `Decimal` sizes; price quantization must not round `filled_size` or `unfilled_size`
- high-precision size ratios must not be pre-rounded before the final `Decimal("0.001")` average-price quantization

Modify `src/polymarket_alpha_lab/normalize.py` so `_parse_decimal()` returns `None` for non-finite values. Existing `_book_level()` then coerces those invalid raw payload values to `Decimal("0")`, which preserves the level for provenance/order-book shape while making it non-executable for paper fills and safe to sort.

Modify `src/polymarket_alpha_lab/domain.py` so `OrderBookSnapshot.best_bid` and `best_ask` scan for the first executable level (`finite price`, `finite size`, `price > 0`, `size > 0`). `spread` and `midpoint` must return `None` unless both executable sides exist and `best_ask > best_bid`. Add domain and scoring regression tests so books with no executable ask side or crossed executable prices do not produce negative spreads or a perfect spread-quality score.

- [ ] **Step 4: Run node tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_paper.py tests/test_domain.py tests/test_normalize.py tests/test_scoring.py -q
```

Expected: all selected tests pass.

- [ ] **Step 5: Run required pre-commit/pre-push gate for Node 2**

Run:

```bash
git status --short --branch --untracked-files=all
.venv/bin/python -m pytest tests/test_paper.py tests/test_domain.py tests/test_normalize.py tests/test_scoring.py -q
.venv/bin/python -m pytest
git diff --check
codegraph status .
# If CodeGraph reports stale/out of date:
codegraph sync .
codegraph status .
```

Expected: untracked files are explicitly listed or `none`; node-specific pytest passes; full pytest passes; diff check reports no whitespace errors; CodeGraph is up to date.

- [ ] **Step 6: Request Claude Code review before commit/push**

Run:

```bash
claude -p --model claude-opus-4-8 --effort max --permission-mode plan "Review Level 1A Node 2 paper fill simulation changes and the updated Node 3 journal plan in /home/ubuntu/polymarket-alpha-lab before commit/push. First run git status --short --branch --untracked-files=all and review all staged, unstaged, and untracked files, including docs/superpowers/plans/2026-06-13-level-1-research-packets-paper-trading.md, src/polymarket_alpha_lab/paper.py, tests/test_paper.py, src/polymarket_alpha_lab/normalize.py, tests/test_normalize.py, src/polymarket_alpha_lab/domain.py, tests/test_domain.py, and tests/test_scoring.py. Confirm the recorded Node 2 gate includes node-specific pytest, full pytest, git diff --check, and CodeGraph status/sync-if-stale results. Node 2 requirements: uses asks for buy, bids for sell, walks depth, stops after requested size is filled, reports partial and zero fills, rejects non-finite/non-positive order sizes, skips non-executable levels with non-finite price/size or price <= 0 or size <= 0, normalizes non-finite raw order-book Decimal values to zero before sorting, shared OrderBookSnapshot best_bid/best_ask ignore non-executable levels, shared spread/midpoint are absent when either side has no executable quote or when executable quotes are crossed, scoring does not reward no-ask/no-bid/crossed books as tight spreads, records executable bid/ask/midpoint/spread/slippage plus order_book_captured_at and deterministic lowercase hex order_book_snapshot_sha256, canonicalizes equivalent finite Decimal spellings in the snapshot hash, does not use midpoint fills, quantizes average price, midpoint, spread, and slippage with explicit Decimal('0.001') ROUND_HALF_EVEN while leaving best_bid/best_ask/worst_price as raw book prices, keeps fill arithmetic deterministic under hostile caller Decimal precision, rounding, and traps, keeps size accounting exact for accepted finite Decimal sizes, and avoids pre-rounding high-precision weighted-average, midpoint, or spread values before final quantization. Safety requirements: no auth, no private keys, no order placement, no cancellation, no user WebSocket, no heartbeat, no live trading, no trading SDK, and no compliance/legal/geographic-access analysis. Node 3 plan requirements: separate research_* and fill_* fields, require confidence and non-empty non-blank risk_tags before journaling, persist non-empty market_raw_archive_path, order_book_raw_archive_path, order_book_raw_payload_sha256 as raw payload checksum, and order_book_snapshot_sha256 as normalized snapshot digest, validate both SHA-256 digests, normalize decision_timestamp_utc and order_book_captured_at, include fill_status, enforce max_executable_size and positive account_equity_before_trade, include fair value/theoretical edge/cost-adjusted edge, reject token mismatch and invalid fill invariants, use JSONL append-only persistence, and verify the Node 3 commit step stages every file Node 3 modifies. Report Critical, Important, Minor findings only, and finish with an explicit verdict: Proceed, Proceed with fixes, or Blocked."
```

Do not run `git commit` or `git push` until Claude returns `Proceed` or `Proceed with fixes` and all Critical/Important findings are resolved.

- [ ] **Step 7: Commit Node 2 after gates pass**

Run:

```bash
git add src/polymarket_alpha_lab/paper.py tests/test_paper.py src/polymarket_alpha_lab/normalize.py tests/test_normalize.py src/polymarket_alpha_lab/domain.py tests/test_domain.py tests/test_scoring.py docs/superpowers/plans/2026-06-13-level-1-research-packets-paper-trading.md
git commit -m "feat: simulate paper fills"
git push
```

## Node 3: Paper Trade Journal

**Goal:** Persist paper-trade records only when a research packet is complete, risk context is present, and a simulated paper fill has positive filled size.

**Decisions locked for Level 1A:**

- Partial fills are journalable when `fill.filled_size > 0`; the record must persist `fill_unfilled_size` so Level 1B can analyze partial liquidity.
- Journal records must persist `fill_status`, derived as `"complete"` when `fill.is_complete` is true and `"partial"` otherwise.
- A journal record must keep research-time quote fields and fill-time quote fields under separate names.
- `confidence`, `fair_value_estimate`, `theoretical_edge`, non-empty `raw_archive_path`, and non-empty non-blank `risk_tags` are required for packet completeness before journaling.
- `fill.requested_size` and `fill.filled_size` must not exceed `packet.max_executable_size`.
- `decision_timestamp_utc` and `order_book_captured_at` are normalized to UTC; naive timestamps are treated as UTC.
- `account_equity_before_trade` must be positive.
- `order_book_raw_archive_path` and `order_book_raw_payload_sha256` are provided to `PaperTradeRecord.from_packet_and_fill()` and persisted alongside `order_book_snapshot_sha256`.
- `order_book_raw_payload_sha256` is the checksum of the archived raw order-book payload before normalization; `order_book_snapshot_sha256` is the digest of the normalized `OrderBookSnapshot`. They are distinct provenance fields and both must validate as lowercase 64-character SHA-256 hex digests.
- Post-trade review remains deferred to Level 1B; Level 1A persists only entry-time paper records and `planned_exit_rule`.

**Files:**

- Modify: `src/polymarket_alpha_lab/research.py`
- Modify: `tests/test_research.py`
- Create: `src/polymarket_alpha_lab/journal.py`
- Create: `tests/test_journal.py`
- Modify: `src/polymarket_alpha_lab/__init__.py`
- Modify: `README.md`

- [ ] **Step 1: Tighten research packet completeness tests**

Modify `tests/test_research.py` so the incomplete packet test builds a candidate with `raw_archive_path=""`, passes `confidence=None` and `risk_tags=()`, and expects:

```python
assert packet.missing_required_fields() == [
    "market_url",
    "outcome_name",
    "model_probability",
    "bid",
    "ask",
    "midpoint",
    "expected_entry_price",
    "fair_value_estimate",
    "theoretical_edge",
    "spread",
    "slippage_estimate",
    "cost_adjusted_edge",
    "confidence",
    "raw_archive_path",
    "risk_tags",
    "thesis",
    "invalidating_conditions",
    "rule_text",
    "resolution_source",
    "positive_max_executable_size",
]
```

Add a focused test for blank tags:

```python
def test_research_packet_reports_blank_risk_tags_missing():
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
        risk_tags=("liquidity", "   "),
        thesis="Tight spread.",
        invalidating_conditions="Spread widens.",
        rule_text="Example rule.",
        resolution_source="Example source",
    )

    assert "risk_tags" in packet.missing_required_fields()
```

- [ ] **Step 2: Run research test to verify it fails**

Run:

```bash
.venv/bin/python -m pytest tests/test_research.py::test_research_packet_reports_missing_required_fields tests/test_research.py::test_research_packet_reports_blank_risk_tags_missing -q
```

Expected: FAIL because `fair_value_estimate`, `theoretical_edge`, `confidence`, `raw_archive_path`, and `risk_tags` are not reported missing yet.

- [ ] **Step 3: Require confidence, edge fields, and risk tags**

Modify `src/polymarket_alpha_lab/research.py`:

```python
    def missing_required_fields(self) -> list[str]:
        missing: list[str] = []
        for field_name in (
            "market_url",
            "outcome_name",
            "strategy_type",
            "model_probability",
            "bid",
            "ask",
            "midpoint",
            "expected_entry_price",
            "fair_value_estimate",
            "theoretical_edge",
            "spread",
            "slippage_estimate",
            "cost_adjusted_edge",
            "confidence",
            "raw_archive_path",
        ):
            if not _has_value(getattr(self, field_name)):
                missing.append(field_name)
        if not self.risk_tags or any(not tag.strip() for tag in self.risk_tags):
            missing.append("risk_tags")
        for field_name in (
            "thesis",
            "invalidating_conditions",
            "rule_text",
            "resolution_source",
        ):
            if not _has_value(getattr(self, field_name)):
                missing.append(field_name)
        if self.max_executable_size is None or self.max_executable_size <= 0:
            missing.append("positive_max_executable_size")
        return missing
```

Use the existing `_has_value()` helper; `confidence` and `max_executable_size` already accept `Decimal | None` in the packet builder.

- [ ] **Step 4: Write failing journal tests**

Create `tests/test_journal.py` with:

```python
import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.journal import PaperTradeJournal, PaperTradeRecord
from polymarket_alpha_lab.paper import PaperFill
from polymarket_alpha_lab.pipeline import ScoredCandidate
from polymarket_alpha_lab.research import build_research_packet


def complete_packet(max_executable_size: Decimal = Decimal("100")):
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
        max_executable_size=max_executable_size,
        risk_tags=("liquidity",),
        thesis="Tight spread and clear rules.",
        invalidating_conditions="Spread widens.",
        rule_text="Example rule.",
        resolution_source="Example source",
    )


def complete_fill(
    *,
    token_id: str = "111",
    side: str = "buy",
    requested_size: Decimal = Decimal("100"),
    order_book_captured_at: datetime = datetime(2026, 6, 13, 12, 30, 30, tzinfo=UTC),
    order_book_snapshot_sha256: str = "a" * 64,
    filled_size: Decimal = Decimal("100"),
    unfilled_size: Decimal = Decimal("0"),
    average_price: Decimal | None = Decimal("0.514"),
    worst_price: Decimal | None = Decimal("0.52"),
):
    return PaperFill(
        token_id=token_id,
        side=side,
        requested_size=requested_size,
        order_book_captured_at=order_book_captured_at,
        order_book_snapshot_sha256=order_book_snapshot_sha256,
        filled_size=filled_size,
        unfilled_size=unfilled_size,
        average_price=average_price,
        worst_price=worst_price,
        best_bid=Decimal("0.49"),
        best_ask=Decimal("0.51"),
        midpoint=Decimal("0.500"),
        spread=Decimal("0.020"),
        slippage_estimate=Decimal("0.004"),
    )


def record_from(packet, fill):
    return PaperTradeRecord.from_packet_and_fill(
        packet=packet,
        fill=fill,
        decision_timestamp=datetime(2026, 6, 13, 12, 31),
        order_book_raw_archive_path="data/raw/clob/book-111.json",
        order_book_raw_payload_sha256="b" * 64,
        account_equity_before_trade=Decimal("10000"),
        sizing_limiter="max_executable_size",
        planned_exit_rule="Mark at executable bid on review.",
    )


def test_paper_trade_journal_appends_jsonl_record(tmp_path):
    journal = PaperTradeJournal(path=tmp_path / "paper-trades.jsonl")
    packet = complete_packet()
    fill = complete_fill()
    record = record_from(packet, fill)

    assert record.fill_midpoint == Decimal("0.500")
    assert record.fill_spread == Decimal("0.020")

    journal.append(record)

    lines = journal.path.read_text().splitlines()
    assert len(lines) == 1
    stored = json.loads(lines[0])
    assert stored["packet_id"] == packet.packet_id
    assert stored["packet_created_at"] == "2026-06-13T12:30:00+00:00"
    assert stored["decision_timestamp_utc"] == "2026-06-13T12:31:00+00:00"
    assert stored["condition_id"] == "0xabc"
    assert stored["token_id"] == "111"
    assert stored["market_slug"] == "example-market"
    assert stored["market_url"] == "https://polymarket.com/event/example-market"
    assert stored["question"] == "Will the example resolve yes?"
    assert stored["outcome_name"] == "Yes"
    assert stored["strategy_type"] == "market_quality"
    assert stored["source_score"] == "78.500"
    assert stored["market_raw_archive_path"] == "data/raw/gamma/markets.json"
    assert stored["order_book_raw_archive_path"] == "data/raw/clob/book-111.json"
    assert stored["order_book_raw_payload_sha256"] == "b" * 64
    assert stored["order_book_snapshot_sha256"] == "a" * 64
    assert stored["risk_tags"] == ["liquidity"]
    assert stored["rule_text_hash"] == packet.rule_text_hash
    assert stored["resolution_source"] == "Example source"
    assert stored["model_probability"] == "0.56"
    assert stored["confidence"] == "0.60"
    assert stored["research_bid"] == "0.50"
    assert stored["research_ask"] == "0.52"
    assert stored["research_midpoint"] == "0.51"
    assert stored["research_expected_entry_price"] == "0.514"
    assert stored["research_fair_value_estimate"] == "0.56"
    assert stored["research_theoretical_edge"] == "0.046"
    assert stored["research_spread"] == "0.02"
    assert stored["research_slippage_estimate"] == "0.004"
    assert stored["research_cost_adjusted_edge"] == "0.026"
    assert stored["max_executable_size"] == "100"
    assert stored["order_side"] == "buy"
    assert stored["order_requested_size"] == "100"
    assert stored["fill_filled_size"] == "100"
    assert stored["fill_unfilled_size"] == "0"
    assert stored["fill_status"] == "complete"
    assert stored["fill_average_price"] == "0.514"
    assert stored["fill_worst_price"] == "0.52"
    assert stored["fill_best_bid"] == "0.49"
    assert stored["fill_best_ask"] == "0.51"
    assert stored["fill_midpoint"] == "0.500"
    assert stored["fill_spread"] == "0.020"
    assert stored["fill_slippage_estimate"] == "0.004"
    assert stored["order_book_captured_at"] == "2026-06-13T12:30:30+00:00"
    assert stored["account_equity_before_trade"] == "10000"
    assert stored["sizing_limiter"] == "max_executable_size"
    assert stored["planned_exit_rule"] == "Mark at executable bid on review."
    assert stored["thesis"] == "Tight spread and clear rules."
    assert stored["invalidating_conditions"] == "Spread widens."


def test_paper_trade_journal_appends_without_overwriting(tmp_path):
    journal = PaperTradeJournal(path=tmp_path / "paper-trades.jsonl")
    first = record_from(complete_packet(), complete_fill(order_book_snapshot_sha256="a" * 64))
    second = record_from(complete_packet(), complete_fill(order_book_snapshot_sha256="b" * 64))

    journal.append(first)
    journal.append(second)

    lines = journal.path.read_text().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["order_book_snapshot_sha256"] == "a" * 64
    assert json.loads(lines[1])["order_book_snapshot_sha256"] == "b" * 64


def test_paper_trade_record_normalizes_decision_and_order_book_timestamps():
    eastern = timezone(timedelta(hours=-4))
    fill = complete_fill(
        order_book_captured_at=datetime(2026, 6, 13, 8, 30, 30, tzinfo=eastern)
    )

    record = PaperTradeRecord.from_packet_and_fill(
        packet=complete_packet(),
        fill=fill,
        decision_timestamp=datetime(2026, 6, 13, 8, 31, tzinfo=eastern),
        order_book_raw_archive_path="data/raw/clob/book-111.json",
        order_book_raw_payload_sha256="b" * 64,
        account_equity_before_trade=Decimal("10000"),
        sizing_limiter="max_executable_size",
        planned_exit_rule="Mark at executable bid on review.",
    )

    assert record.decision_timestamp_utc == datetime(2026, 6, 13, 12, 31, tzinfo=UTC)
    assert record.order_book_captured_at == datetime(2026, 6, 13, 12, 30, 30, tzinfo=UTC)


def test_paper_trade_record_treats_naive_order_book_timestamp_as_utc():
    record = record_from(
        complete_packet(),
        complete_fill(order_book_captured_at=datetime(2026, 6, 13, 12, 30, 30)),
    )

    assert record.order_book_captured_at == datetime(2026, 6, 13, 12, 30, 30, tzinfo=UTC)


def test_paper_trade_record_accepts_partial_fills_with_positive_filled_size():
    record = record_from(
        complete_packet(),
        complete_fill(
            requested_size=Decimal("100"),
            filled_size=Decimal("40"),
            unfilled_size=Decimal("60"),
        ),
    )

    assert record.fill_filled_size == Decimal("40")
    assert record.fill_unfilled_size == Decimal("60")
    assert record.fill_status == "partial"


def test_paper_trade_record_rejects_incomplete_packet():
    packet = complete_packet()
    incomplete_packet = build_research_packet(
        candidate=ScoredCandidate(
            condition_id=packet.condition_id,
            token_id=packet.token_id,
            market_slug=packet.market_slug,
            question=packet.question,
            total_score=packet.source_score,
            raw_archive_path="",
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
        confidence=None,
        max_executable_size=packet.max_executable_size,
        risk_tags=(),
        thesis=packet.thesis,
        invalidating_conditions=packet.invalidating_conditions,
        rule_text=packet.rule_text,
        resolution_source=packet.resolution_source,
    )

    with pytest.raises(ValueError, match="incomplete research packet") as exc:
        record_from(incomplete_packet, complete_fill())
    assert "expected_entry_price" in str(exc.value)
    assert "confidence" in str(exc.value)
    assert "raw_archive_path" in str(exc.value)
    assert "risk_tags" in str(exc.value)


def test_paper_trade_record_rejects_blank_risk_tag():
    packet = complete_packet()
    blank_tag_packet = build_research_packet(
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
        expected_entry_price=packet.expected_entry_price,
        fair_value_estimate=packet.fair_value_estimate,
        theoretical_edge=packet.theoretical_edge,
        spread=packet.spread,
        slippage_estimate=packet.slippage_estimate,
        cost_adjusted_edge=packet.cost_adjusted_edge,
        confidence=packet.confidence,
        max_executable_size=packet.max_executable_size,
        risk_tags=("liquidity", "   "),
        thesis=packet.thesis,
        invalidating_conditions=packet.invalidating_conditions,
        rule_text=packet.rule_text,
        resolution_source=packet.resolution_source,
    )

    with pytest.raises(ValueError, match="risk_tags"):
        record_from(blank_tag_packet, complete_fill())


def test_paper_trade_record_rejects_blank_market_raw_archive_path():
    packet = complete_packet()
    blank_archive_packet = build_research_packet(
        candidate=ScoredCandidate(
            condition_id=packet.condition_id,
            token_id=packet.token_id,
            market_slug=packet.market_slug,
            question=packet.question,
            total_score=packet.source_score,
            raw_archive_path="   ",
        ),
        created_at=packet.created_at,
        market_url=packet.market_url,
        outcome_name=packet.outcome_name,
        strategy_type=packet.strategy_type,
        model_probability=packet.model_probability,
        bid=packet.bid,
        ask=packet.ask,
        midpoint=packet.midpoint,
        expected_entry_price=packet.expected_entry_price,
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

    with pytest.raises(ValueError, match="raw_archive_path"):
        record_from(blank_archive_packet, complete_fill())


@pytest.mark.parametrize(
    ("fill", "account_equity_before_trade", "match"),
    [
        (complete_fill(filled_size=Decimal("0"), unfilled_size=Decimal("100")), Decimal("10000"), "positive filled_size"),
        (complete_fill(requested_size=Decimal("101"), filled_size=Decimal("101"), unfilled_size=Decimal("0")), Decimal("10000"), "max_executable_size"),
        (complete_fill(requested_size=Decimal("101"), filled_size=Decimal("40"), unfilled_size=Decimal("61")), Decimal("10000"), "requested_size"),
        (complete_fill(), Decimal("0"), "account_equity_before_trade"),
    ],
)
def test_paper_trade_record_rejects_invalid_trade_inputs(
    fill, account_equity_before_trade, match
):
    with pytest.raises(ValueError, match=match):
        PaperTradeRecord.from_packet_and_fill(
            packet=complete_packet(),
            fill=fill,
            decision_timestamp=datetime(2026, 6, 13, 12, 31, tzinfo=UTC),
            order_book_raw_archive_path="data/raw/clob/book-111.json",
            order_book_raw_payload_sha256="b" * 64,
            account_equity_before_trade=account_equity_before_trade,
            sizing_limiter="max_executable_size",
            planned_exit_rule="Mark at executable bid on review.",
        )


@pytest.mark.parametrize(
    (
        "fill",
        "order_book_raw_archive_path",
        "order_book_raw_payload_sha256",
        "sizing_limiter",
        "planned_exit_rule",
        "match",
    ),
    [
        (replace(complete_fill(), token_id="222"), "data/raw/clob/book-111.json", "b" * 64, "max_executable_size", "Exit rule.", "token_id"),
        (complete_fill(), "", "b" * 64, "max_executable_size", "Exit rule.", "order_book_raw_archive_path"),
        (complete_fill(), "   ", "b" * 64, "max_executable_size", "Exit rule.", "order_book_raw_archive_path"),
        (complete_fill(), "data/raw/clob/book-111.json", "not-hex", "max_executable_size", "Exit rule.", "order_book_raw_payload_sha256"),
        (complete_fill(), "data/raw/clob/book-111.json", "b" * 63, "max_executable_size", "Exit rule.", "order_book_raw_payload_sha256"),
        (complete_fill(), "data/raw/clob/book-111.json", "B" * 64, "max_executable_size", "Exit rule.", "order_book_raw_payload_sha256"),
        (complete_fill(order_book_snapshot_sha256=""), "data/raw/clob/book-111.json", "b" * 64, "max_executable_size", "Exit rule.", "order_book_snapshot_sha256"),
        (complete_fill(order_book_snapshot_sha256="not-hex"), "data/raw/clob/book-111.json", "b" * 64, "max_executable_size", "Exit rule.", "order_book_snapshot_sha256"),
        (complete_fill(order_book_snapshot_sha256="a" * 63), "data/raw/clob/book-111.json", "b" * 64, "max_executable_size", "Exit rule.", "order_book_snapshot_sha256"),
        (complete_fill(order_book_snapshot_sha256="A" * 64), "data/raw/clob/book-111.json", "b" * 64, "max_executable_size", "Exit rule.", "order_book_snapshot_sha256"),
        (complete_fill(), "data/raw/clob/book-111.json", "b" * 64, "", "Exit rule.", "sizing_limiter"),
        (complete_fill(), "data/raw/clob/book-111.json", "b" * 64, "   ", "Exit rule.", "sizing_limiter"),
        (complete_fill(), "data/raw/clob/book-111.json", "b" * 64, "max_executable_size", "", "planned_exit_rule"),
        (complete_fill(), "data/raw/clob/book-111.json", "b" * 64, "max_executable_size", "   ", "planned_exit_rule"),
    ],
)
def test_paper_trade_record_rejects_invalid_journal_boundaries(
    fill,
    order_book_raw_archive_path,
    order_book_raw_payload_sha256,
    sizing_limiter,
    planned_exit_rule,
    match,
):
    with pytest.raises(ValueError, match=match):
        PaperTradeRecord.from_packet_and_fill(
            packet=complete_packet(),
            fill=fill,
            decision_timestamp=datetime(2026, 6, 13, 12, 31, tzinfo=UTC),
            order_book_raw_archive_path=order_book_raw_archive_path,
            order_book_raw_payload_sha256=order_book_raw_payload_sha256,
            account_equity_before_trade=Decimal("10000"),
            sizing_limiter=sizing_limiter,
            planned_exit_rule=planned_exit_rule,
        )


@pytest.mark.parametrize(
    ("fill", "match"),
    [
        (complete_fill(side="hold"), "side"),
        (complete_fill(requested_size=Decimal("0")), "requested_size"),
        (complete_fill(filled_size=Decimal("-1")), "filled_size"),
        (complete_fill(unfilled_size=Decimal("-1")), "unfilled_size"),
        (complete_fill(filled_size=Decimal("40"), unfilled_size=Decimal("50")), "fill accounting"),
        (complete_fill(average_price=None), "average_price"),
        (complete_fill(worst_price=None), "worst_price"),
    ],
)
def test_paper_trade_record_rejects_impossible_fill_inputs(fill, match):
    with pytest.raises(ValueError, match=match):
        PaperTradeRecord.from_packet_and_fill(
            packet=complete_packet(),
            fill=fill,
            decision_timestamp=datetime(2026, 6, 13, 12, 31, tzinfo=UTC),
            order_book_raw_archive_path="data/raw/clob/book-111.json",
            order_book_raw_payload_sha256="b" * 64,
            account_equity_before_trade=Decimal("10000"),
            sizing_limiter="max_executable_size",
            planned_exit_rule="Mark at executable bid on review.",
        )
```

- [ ] **Step 5: Run tests to verify they fail**

Run:

```bash
.venv/bin/python -m pytest tests/test_research.py tests/test_journal.py -q
```

Expected: the research completeness test passes after Step 3; journal test collection fails until `polymarket_alpha_lab.journal` exists.

- [ ] **Step 6: Implement journal**

Create `src/polymarket_alpha_lab/journal.py` with:

```python
"""Paper-trade journal persistence."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from polymarket_alpha_lab.paper import PaperFill
from polymarket_alpha_lab.research import ResearchPacket


@dataclass(frozen=True)
class PaperTradeRecord:
    packet_id: str
    packet_created_at: datetime
    condition_id: str
    token_id: str
    market_slug: str
    market_url: str
    question: str
    outcome_name: str
    strategy_type: str
    source_score: str
    market_raw_archive_path: str
    order_book_raw_archive_path: str
    order_book_raw_payload_sha256: str
    order_book_snapshot_sha256: str
    risk_tags: tuple[str, ...]
    rule_text_hash: str
    resolution_source: str
    decision_timestamp_utc: datetime
    model_probability: Decimal
    confidence: Decimal
    research_bid: Decimal
    research_ask: Decimal
    research_midpoint: Decimal
    research_expected_entry_price: Decimal
    research_fair_value_estimate: Decimal
    research_theoretical_edge: Decimal
    research_spread: Decimal
    research_slippage_estimate: Decimal
    research_cost_adjusted_edge: Decimal
    max_executable_size: Decimal
    order_side: str
    order_requested_size: Decimal
    fill_filled_size: Decimal
    fill_unfilled_size: Decimal
    fill_status: str
    fill_average_price: Decimal
    fill_worst_price: Decimal
    fill_best_bid: Decimal | None
    fill_best_ask: Decimal | None
    fill_midpoint: Decimal | None
    fill_spread: Decimal | None
    fill_slippage_estimate: Decimal | None
    order_book_captured_at: datetime
    account_equity_before_trade: Decimal
    sizing_limiter: str
    planned_exit_rule: str
    thesis: str
    invalidating_conditions: str

    @classmethod
    def from_packet_and_fill(
        cls,
        *,
        packet: ResearchPacket,
        fill: PaperFill,
        decision_timestamp: datetime,
        order_book_raw_archive_path: str,
        order_book_raw_payload_sha256: str,
        account_equity_before_trade: Decimal,
        sizing_limiter: str,
        planned_exit_rule: str,
    ) -> "PaperTradeRecord":
        missing = packet.missing_required_fields()
        if missing:
            raise ValueError(f"incomplete research packet: {', '.join(missing)}")
        if packet.token_id != fill.token_id:
            raise ValueError("packet token_id must match paper fill token_id")
        if fill.side not in ("buy", "sell"):
            raise ValueError("fill side must be buy or sell")
        if fill.requested_size <= 0:
            raise ValueError("fill requested_size must be positive")
        if fill.filled_size <= 0:
            raise ValueError("paper fill must have positive filled_size")
        if fill.unfilled_size < 0:
            raise ValueError("fill unfilled_size must be nonnegative")
        if fill.filled_size + fill.unfilled_size != fill.requested_size:
            raise ValueError("fill accounting must match requested_size")
        if fill.average_price is None:
            raise ValueError("fill average_price is required for positive fills")
        if fill.worst_price is None:
            raise ValueError("fill worst_price is required for positive fills")
        if account_equity_before_trade <= 0:
            raise ValueError("account_equity_before_trade must be positive")
        if not sizing_limiter.strip():
            raise ValueError("sizing_limiter is required")
        if not planned_exit_rule.strip():
            raise ValueError("planned_exit_rule is required")
        if not order_book_raw_archive_path.strip():
            raise ValueError("order_book_raw_archive_path is required")
        if not _is_sha256(order_book_raw_payload_sha256):
            raise ValueError("order_book_raw_payload_sha256 must be a lowercase 64-character hex digest")
        if not _is_sha256(fill.order_book_snapshot_sha256):
            raise ValueError("order_book_snapshot_sha256 must be a lowercase 64-character hex digest")

        model_probability = _required_decimal(packet.model_probability, "model_probability")
        confidence = _required_decimal(packet.confidence, "confidence")
        bid = _required_decimal(packet.bid, "bid")
        ask = _required_decimal(packet.ask, "ask")
        midpoint = _required_decimal(packet.midpoint, "midpoint")
        expected_entry_price = _required_decimal(
            packet.expected_entry_price, "expected_entry_price"
        )
        fair_value_estimate = _required_decimal(
            packet.fair_value_estimate, "fair_value_estimate"
        )
        theoretical_edge = _required_decimal(packet.theoretical_edge, "theoretical_edge")
        spread = _required_decimal(packet.spread, "spread")
        slippage_estimate = _required_decimal(packet.slippage_estimate, "slippage_estimate")
        cost_adjusted_edge = _required_decimal(
            packet.cost_adjusted_edge, "cost_adjusted_edge"
        )
        max_executable_size = _required_decimal(
            packet.max_executable_size, "max_executable_size"
        )

        _require_probability(model_probability, "model_probability")
        _require_probability(confidence, "confidence")
        for field_name, value in (
            ("bid", bid),
            ("ask", ask),
            ("midpoint", midpoint),
            ("expected_entry_price", expected_entry_price),
            ("fair_value_estimate", fair_value_estimate),
            ("fill_average_price", fill.average_price),
            ("fill_worst_price", fill.worst_price),
            ("fill_best_bid", fill.best_bid),
            ("fill_best_ask", fill.best_ask),
            ("fill_midpoint", fill.midpoint),
        ):
            _require_price_domain(value, field_name)

        if fill.requested_size > max_executable_size:
            raise ValueError("fill requested_size exceeds max_executable_size")
        if fill.filled_size > max_executable_size:
            raise ValueError("fill filled_size exceeds max_executable_size")

        return cls(
            packet_id=packet.packet_id,
            packet_created_at=_as_utc(packet.created_at),
            condition_id=packet.condition_id,
            token_id=packet.token_id,
            market_slug=packet.market_slug,
            market_url=packet.market_url,
            question=packet.question,
            outcome_name=packet.outcome_name,
            strategy_type=packet.strategy_type,
            source_score=packet.source_score,
            market_raw_archive_path=packet.raw_archive_path,
            order_book_raw_archive_path=order_book_raw_archive_path,
            order_book_raw_payload_sha256=order_book_raw_payload_sha256,
            order_book_snapshot_sha256=fill.order_book_snapshot_sha256,
            risk_tags=tuple(packet.risk_tags),
            rule_text_hash=packet.rule_text_hash,
            resolution_source=packet.resolution_source,
            decision_timestamp_utc=_as_utc(decision_timestamp),
            model_probability=model_probability,
            confidence=confidence,
            research_bid=bid,
            research_ask=ask,
            research_midpoint=midpoint,
            research_expected_entry_price=expected_entry_price,
            research_fair_value_estimate=fair_value_estimate,
            research_theoretical_edge=theoretical_edge,
            research_spread=spread,
            research_slippage_estimate=slippage_estimate,
            research_cost_adjusted_edge=cost_adjusted_edge,
            max_executable_size=max_executable_size,
            order_side=fill.side,
            order_requested_size=fill.requested_size,
            fill_filled_size=fill.filled_size,
            fill_unfilled_size=fill.unfilled_size,
            fill_status="complete" if fill.is_complete else "partial",
            fill_average_price=fill.average_price,
            fill_worst_price=fill.worst_price,
            fill_best_bid=fill.best_bid,
            fill_best_ask=fill.best_ask,
            fill_midpoint=fill.midpoint,
            fill_spread=fill.spread,
            fill_slippage_estimate=fill.slippage_estimate,
            order_book_captured_at=_as_utc(fill.order_book_captured_at),
            account_equity_before_trade=account_equity_before_trade,
            sizing_limiter=sizing_limiter,
            planned_exit_rule=planned_exit_rule,
            thesis=packet.thesis,
            invalidating_conditions=packet.invalidating_conditions,
        )


@dataclass(frozen=True)
class PaperTradeJournal:
    path: Path

    def append(self, record: PaperTradeRecord) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(_json_ready(asdict(record)), sort_keys=True) + "\n")


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _required_decimal(value: Decimal | None, field_name: str) -> Decimal:
    if value is None:
        raise ValueError(f"{field_name} is required")
    return value


def _require_probability(value: Decimal, field_name: str) -> None:
    if value < 0 or value > 1:
        raise ValueError(f"{field_name} must be in [0, 1]")


def _require_price_domain(value: Decimal | None, field_name: str) -> None:
    if value is not None and (value < 0 or value > 1):
        raise ValueError(f"{field_name} must be in [0, 1]")


def _is_sha256(value: str) -> bool:
    return (
        len(value) == 64
        and value == value.lower()
        and all(character in "0123456789abcdef" for character in value)
    )


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    return value
```

- [ ] **Step 7: Export stable Level 1 objects**

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
from polymarket_alpha_lab.paper import PaperFill, PaperOrder, simulate_order_book_fill
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
    "simulate_order_book_fill",
]
```

- [ ] **Step 8: Update README status**

Add this exact section after the current Level 0 usage section:

```markdown
## Level 1A Status

Level 1A adds research packets, bid/ask order-book-walk paper-fill simulation, and JSONL paper-trade journals. It remains paper-only: no account authentication, no private-key handling, no order placement, no order cancellation, no user WebSocket, no heartbeat, no live trading, and no compliance/legal/geographic-access analysis.
```

- [ ] **Step 9: Run required pre-commit/pre-push gate for Node 3**

Run:

```bash
git status --short --branch --untracked-files=all
.venv/bin/python -m pytest tests/test_research.py tests/test_journal.py -q
.venv/bin/python -m pytest
git diff --check
codegraph status .
# If CodeGraph reports stale/out of date:
codegraph sync .
codegraph status .
```

Expected:

- untracked files are explicitly listed or `none`
- Node 3 focused pytest passes
- full pytest reports all tests passing
- `git diff --check` reports no whitespace errors
- CodeGraph index is up to date
- only intentional files are modified or staged

- [ ] **Step 10: Request Claude Code review before final Level 1A push**

Run:

```bash
claude -p --model claude-opus-4-8 --effort max --permission-mode plan "Review all Level 1A research packet and paper trading changes in /home/ubuntu/polymarket-alpha-lab before final push. First run git status --short --branch --untracked-files=all and review all staged, unstaged, and untracked files. Confirm the recorded Node 3 gate includes Node 3 focused pytest, full pytest, git diff --check, and CodeGraph status/sync-if-stale results. Requirements: auditable research packets, rule text hash, bid/ask order-book-walk paper fills, execution-cost fields, non-empty market raw archive provenance, non-empty order-book raw archive path, lowercase order-book raw payload SHA-256, lowercase normalized order-book snapshot SHA-256, JSONL paper journal, separate research_* and fill_* quote fields, non-empty non-blank risk_tags, confidence, fair value, theoretical edge, cost-adjusted edge, fill_status, max_executable_size enforcement, positive account_equity_before_trade, no midpoint fills, no auth, no private keys, no order placement, no cancellation, no user WebSocket, no heartbeat, no live trading, and no compliance/legal/geographic-access analysis. Also review next-stage direction: Level 1B rejected-candidate logs, configurable risk gates, paper positions, daily executable NAV marks, exposure analytics, performance reports, richer packet evidence, and dashboards, still paper-only. Report Critical, Important, Minor findings only, and finish with an explicit verdict: Proceed, Proceed with fixes, or Blocked."
```

Do not run `git commit` or `git push` until Claude returns `Proceed` or `Proceed with fixes` and all Critical/Important findings are resolved.

- [ ] **Step 11: Commit Node 3**

Run:

```bash
git add src/polymarket_alpha_lab/journal.py src/polymarket_alpha_lab/research.py src/polymarket_alpha_lab/__init__.py README.md tests/test_journal.py tests/test_research.py docs/superpowers/plans/2026-06-13-level-1-research-packets-paper-trading.md
git commit -m "feat: journal paper trades"
git push
```

## Level 1A Completion Criteria

Level 1A is complete only when:

- research packets carry condition id, market slug, market URL, token id, outcome, non-empty market raw archive path, rule text hash, resolution source, model probability, thesis, invalidating conditions, bid, ask, midpoint, expected entry price, fair value, theoretical edge, spread, slippage estimate, cost-adjusted edge, confidence, max executable size, and non-empty non-blank risk tags
- incomplete research packets are rejected before journaling
- paper fills use asks for buy and bids for sell
- paper fills walk order book depth and report partial fills
- paper fills record bid, ask, midpoint, spread, slippage estimate, average fill price, worst fill price, order-book capture timestamp, and normalized order-book snapshot SHA-256
- journal records are persisted as JSONL with packet timestamp, decision timestamp, order-book timestamp, strategy type, source score, non-empty market raw archive path, non-empty order-book raw archive path, lowercase order-book raw payload SHA-256, lowercase normalized order-book snapshot SHA-256, non-empty non-blank risk tags, confidence, max executable size, fill status, fair value, theoretical edge, `research_*` quote fields, `fill_*` quote fields, Decimal values, and datetime values serialized safely
- Level 1B-only outputs are not implemented in Level 1A: rejected-candidate logs, portfolio positions, daily exit NAV, realized PnL, holding days, calibration, drawdown, dashboards, and risk-gate configuration
- every node has passed the required gate: `git status --short --branch --untracked-files=all`, node-specific pytest, `.venv/bin/python -m pytest`, `git diff --check`, `codegraph status .`, `codegraph sync .` when stale, and a follow-up `codegraph status .`
- Claude Code reviewed the plan and every code node before push using `claude-opus-4-8`, `--effort max`, and `--permission-mode plan`, and returned `Proceed` or `Proceed with fixes` with all Critical/Important findings resolved
- GitHub `main` contains the verified commits

## Handoff Summary Template

```text
Handoff Summary
- Repo status: branch, latest commit, clean/dirty state, pushed/not pushed, plus `git status --short --branch --untracked-files=all` output.
- Verified commands: exact node-specific pytest, `.venv/bin/python -m pytest`, `git diff --check`, `codegraph status .`, `codegraph sync .` if run, follow-up `codegraph status .`, and pass/fail result.
- Untracked files: list or "none".
- Uncommitted files: list or "none".
- Data-integrity checks: non-empty non-blank `risk_tags`, non-empty market raw archive paths, non-empty order-book raw archive paths, lowercase raw payload SHA-256, lowercase normalized snapshot SHA-256.
- Claude review: exact model `claude-opus-4-8`, effort `max`, `--permission-mode plan`, review scope, explicit verdict, unresolved findings.
- Next step: one concrete next action.
```
