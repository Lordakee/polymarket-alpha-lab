# Level 1B Positions NAV Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a paper-only position ledger and executable NAV mark records derived from accepted paper trade journal records and supplied public order book snapshots.

**Architecture:** Keep this node pure and local: `positions.py` replays `PaperTradeRecord` objects into a frozen `PaperPortfolio`, marks open long positions by simulating sell-side exits through `simulate_order_book_fill(order, book)`, and appends `PaperNavSnapshot` records as strict JSONL. The module consumes already-journaled paper records and already-supplied `OrderBookSnapshot`s. It does not fetch data, authenticate, place orders, cancel orders, open user WebSockets, send heartbeats, reconcile exchange accounts, create proposals, or touch private keys.

**Tech Stack:** Python 3.11+, standard library only, frozen dataclasses, `Decimal`, JSONL files, existing `PaperTradeRecord`, `PaperOrder`, `simulate_order_book_fill`, `OrderBookSnapshot`, `pytest`, CodeGraph.

---

## Review And Execution Protocol

1. Submit this plan to Claude Code with model `claude-opus-4-8`, effort `max`, read-only permissions before implementation.
2. Do not implement Level 1B Node 2 until Claude Code returns `Proceed` or `Proceed with fixes` and all Critical/Important findings are resolved.
3. Before every node commit and push, run and record this required gate:
   - `git status --short --branch --untracked-files=all`; explicitly list untracked files or `none`.
   - `.venv/bin/python -m pytest tests/test_positions.py tests/test_init.py -q`.
   - `.venv/bin/python -m pytest -q`.
   - `git diff --check`; after staging, also run `git diff --cached --check`.
   - `codegraph status .`; if stale or out of date, run `codegraph sync .` and then `codegraph status .` again.
   - Claude Code review with `claude-opus-4-8`, `--effort max`, covering the node diff, untracked files, verification output, and the next node plan when one exists.
4. Do not commit or push the node until all required gate items pass, Claude returns `Proceed` or `Proceed with fixes`, and all Claude Critical/Important findings are resolved.
5. After the node, write a Handoff Summary with repo status, verified commands, uncommitted files, Claude review status, and next step.

Level 1B Node 2 must not add:

- account authentication
- private-key handling
- live trading
- automated order placement
- order cancellation
- user WebSocket
- REST heartbeat
- trading SDK
- human approval proposal workflow
- exchange account position reconciliation
- compliance/legal/geographic-access analysis

## Level 1B Node 2 Scope

This node adds only the paper accounting substrate for later Level 1 validation:

- replay accepted `PaperTradeRecord` inputs into long-only paper positions
- handle buy fills, partial sell fills, full closes, realized PnL, and cash balance deterministically
- mark open positions at executable exit-side liquidity by walking bid depth with `simulate_order_book_fill(PaperOrder(token_id=position.token_id, side="sell", size=position.open_size), book)`
- distinguish executable exit NAV from informational midpoint NAV
- reject duplicate `packet_id` inputs so repeated journal records cannot be double-counted
- persist NAV snapshots as append-only JSONL with Decimal strings, UTC timestamps, mark provenance, and `paper_only=True`
- export stable Python APIs and README status text

This node intentionally does not add exposure analytics, drawdown reports, calibration reports, dashboards, strategy promotion packets, proposal generation, historical loaders, resolution settlement, or exchange reconciliation. The journal remains the source of truth for closed trade history; this node omits fully closed positions from `PaperPortfolio.positions`.

Stale-book enforcement is also deferred. Node 2 records `marked_at` and `order_book_captured_at` in UTC so later validation gates can evaluate freshness, but this node does not choose a freshness threshold or reject marks by age. Crossed books are marked from executable bid depth and preserve negative spread/midpoint metadata for audit; they are not rejected merely because the book is crossed.

## Target File Structure

- Create: `src/polymarket_alpha_lab/positions.py`
  - Frozen position, portfolio, position mark, NAV snapshot, and NAV log dataclasses.
  - Pure replay and mark functions.
- Create: `tests/test_positions.py`
  - Portfolio replay, executable NAV marking, JSONL persistence, invalid input, and frozen dataclass tests.
- Modify: `src/polymarket_alpha_lab/__init__.py`
  - Export stable Level 1B Node 2 public APIs.
- Modify: `tests/test_init.py`
  - Package-root export contract for positions/NAV APIs.
- Modify: `README.md`
  - Add Level 1B Node 2 paper-only status and Python API notes.
- Modify: `docs/superpowers/plans/2026-06-13-level-1b-positions-nav.md`
  - Update gate results and handoff notes as the node is completed.

## Public API Contract

Create these names:

```python
from polymarket_alpha_lab.positions import (
    PaperNavLog,
    PaperNavSnapshot,
    PaperPortfolio,
    PaperPosition,
    PaperPositionMark,
    build_paper_portfolio,
    mark_paper_nav,
)
```

Export all seven from `polymarket_alpha_lab.__init__`.

## Position And NAV Semantics

`build_paper_portfolio(records, *, starting_cash)` returns a `PaperPortfolio`.

- `records` must be an iterable of `PaperTradeRecord` values.
- `starting_cash` must be a finite positive `Decimal`.
- Replay records in input order. Do not sort the journal records.
- Group open positions by `token_id`.
- Reject duplicate `packet_id` values before applying any repeated record to cash, cost basis, realized PnL, or open size.
- Metadata for the same `token_id` must remain stable across records:
  - `condition_id`
  - `market_slug`
  - `market_url`
  - `question`
  - `outcome_name`
  - `strategy_type`
  - `rule_text_hash`
  - `resolution_source`
- `risk_tags` must be canonical nonblank strings with no leading or trailing whitespace. When later records for the same `token_id` add risk tags, aggregate positions preserve an ordered de-duplicated union of all observed tags for audit visibility.
- Buy fills increase `open_size`, decrease `cash_balance`, increase `cost_basis`, and increase `entry_trade_count`.
- Sell fills require an existing open position, cannot exceed `open_size`, increase `cash_balance`, reduce `cost_basis` proportionally from current remaining cost basis (`existing.cost_basis * fill_filled_size / existing.open_size`), update `realized_pnl`, and increase `exit_trade_count`. `realized_pnl` may be negative when a paper position is sold below its average entry price.
- Entry cost basis and sell proceeds intentionally use journal-price basis: `fill_filled_size * fill_average_price`. `PaperTradeRecord` does not store exact entry notional, so this node must not pretend historical entry cash/proceeds are more precise than the journal. Cost-basis relief on partial sells uses the current exact remaining journal basis proportionally instead of the quantized display `average_entry_price`. Exact bid-depth notional is required only for current executable exit NAV because `OrderBookSnapshot` depth is available at mark time.
- Fully closed positions are omitted from `PaperPortfolio.positions`; `PaperPortfolio.realized_pnl` preserves realized PnL.
- Partial journal fills use only `fill_filled_size`; never aggregate `order_requested_size`.
- Buys that would drive `cash_balance` below zero are rejected; this node does not model margin.

`mark_paper_nav(portfolio, books_by_token_id, *, marked_at)` returns a `PaperNavSnapshot`.

- `portfolio` must be a `PaperPortfolio`.
- `books_by_token_id` must be a mapping from token id strings to `OrderBookSnapshot` objects.
- Every open position must have a supplied book whose `book.token_id` equals the position token id.
- For each open long position, create `PaperOrder(token_id=position.token_id, side="sell", size=position.open_size)` and pass it to `simulate_order_book_fill(order, book)`.
- `exit_value` equals the exact executable bid-walk notional for the filled exit size. Do not calculate executable NAV as `exit_filled_size * exit_average_price`, because `PaperFill.average_price` is quantized to `Decimal("0.001")` and can drift from exact bid-depth notional.
- The implementation must use `simulate_order_book_fill(order, book)` for canonical fill metadata and a private equivalent bid-depth notional helper for exact `exit_value`.
- Unfilled exit shares are valued at zero in `exit_nav` because there is no currently executable exit depth.
- `midpoint_value` equals `position.open_size * fill.midpoint` when midpoint is present; otherwise it is `None`. Midpoint values are informational only.
- `exit_nav` equals `portfolio.cash_balance + sum(mark.exit_value)`.
- `midpoint_nav` equals `portfolio.cash_balance + sum(mark.midpoint_value)` only when every open position has a midpoint. If any open position lacks midpoint, `midpoint_nav` is `None`.
- `unrealized_exit_pnl` equals `sum(mark.exit_value - mark.cost_basis)` across open positions.
- `total_cost_basis` equals `sum(position.cost_basis)` across open positions.
- `marked_at`, `opened_at`, `updated_at`, and `order_book_captured_at` are normalized to UTC. Naive datetimes are treated as UTC, matching the journal boundary.

`PaperPositionMark.mark_status` values are stable strings:

- `fully_executable`: bid depth covers the full open position.
- `partially_executable`: some bid depth exists but cannot cover the full open position.
- `no_exit_depth`: no executable bid depth exists for the open long position.

Missing books and token mismatches raise `ValueError` instead of producing degraded marks in this node. Crossed books are not rejected; executable exit-side mark behavior follows `simulate_order_book_fill(order, book)`.

## Planned Dataclasses

`positions.py` should use frozen dataclasses and direct construction validation:

```python
@dataclass(frozen=True)
class PaperPosition:
    source_packet_ids: tuple[str, ...]
    condition_id: str
    token_id: str
    market_slug: str
    market_url: str
    question: str
    outcome_name: str
    strategy_type: str
    risk_tags: tuple[str, ...]
    rule_text_hash: str
    resolution_source: str
    market_raw_archive_path: str
    last_order_book_raw_archive_path: str
    last_order_book_raw_payload_sha256: str
    last_order_book_snapshot_sha256: str
    opened_at: datetime
    updated_at: datetime
    open_size: Decimal
    cost_basis: Decimal
    average_entry_price: Decimal
    realized_pnl: Decimal
    entry_trade_count: int
    exit_trade_count: int


@dataclass(frozen=True)
class PaperPortfolio:
    starting_cash: Decimal
    cash_balance: Decimal
    realized_pnl: Decimal
    positions: tuple[PaperPosition, ...]


@dataclass(frozen=True)
class PaperPositionMark:
    condition_id: str
    token_id: str
    market_slug: str
    outcome_name: str
    open_size: Decimal
    cost_basis: Decimal
    average_entry_price: Decimal
    order_book_captured_at: datetime
    order_book_snapshot_sha256: str
    exit_filled_size: Decimal
    exit_unfilled_size: Decimal
    exit_average_price: Decimal | None
    exit_worst_price: Decimal | None
    exit_value: Decimal
    midpoint_price: Decimal | None
    midpoint_value: Decimal | None
    best_bid: Decimal | None
    best_ask: Decimal | None
    spread: Decimal | None
    slippage_estimate: Decimal | None
    mark_status: str


@dataclass(frozen=True)
class PaperNavSnapshot:
    marked_at: datetime
    starting_cash: Decimal
    cash_balance: Decimal
    realized_pnl: Decimal
    exit_nav: Decimal
    midpoint_nav: Decimal | None
    total_cost_basis: Decimal
    unrealized_exit_pnl: Decimal
    marks: tuple[PaperPositionMark, ...]
    paper_only: bool = True


@dataclass(frozen=True)
class PaperNavLog:
    path: Path | str
```

`PaperNavLog` exposes one public method with this exact signature: `append(self, snapshot: PaperNavSnapshot) -> None`.

Direct dataclass construction must validate nonblank canonical strings, finite `Decimal` fields, nonnegative size/cost accounting where applicable, `cost_basis <= open_size` for binary-share positions/marks, `exit_value <= exit_filled_size`, zero executable value when no exit size is filled, portfolio cash accounting identities, finite positive or negative realized PnL, positive open positions, valid mark statuses, `paper_only is True`, tuple field types, timestamp types, lowercase 64-character SHA-256 digests, and JSON-serializable values before file writes.

## Private Helper Contract

`positions.py` should define these private helpers before they are used by dataclasses or public functions:

```python
def _as_utc(value: datetime) -> datetime:
    """Return a UTC datetime, treating naive datetimes as UTC; raise ValueError otherwise."""


def _normalize_string_tuple(field_name: str, value: Iterable[str]) -> tuple[str, ...]:
    """Return a tuple of nonblank strings; reject bare str/bytes and non-string items."""


def _normalize_position_tuple(value: Iterable[PaperPosition]) -> tuple[PaperPosition, ...]:
    """Return a deterministically sorted tuple of PaperPosition values with unique token_id."""


def _normalize_mark_tuple(value: Iterable[PaperPositionMark]) -> tuple[PaperPositionMark, ...]:
    """Return a deterministically sorted tuple of PaperPositionMark values with unique token_id."""


def _require_string(field_name: str, value: str) -> None:
    """Raise ValueError when value is not a string."""


def _require_nonblank_string(field_name: str, value: str) -> None:
    """Raise ValueError when value is not a nonblank string."""


def _require_decimal(field_name: str, value: Decimal) -> None:
    """Raise ValueError when value is not a Decimal."""


def _require_finite_decimal(field_name: str, value: Decimal) -> None:
    """Raise ValueError when value is not a finite Decimal."""


def _require_optional_finite_decimal(field_name: str, value: Decimal | None) -> None:
    """Raise ValueError when value is neither None nor a finite Decimal."""


def _require_positive_decimal(field_name: str, value: Decimal) -> None:
    """Raise ValueError when value is not finite or is <= 0."""


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> None:
    """Raise ValueError when value is not finite or is < 0."""


def _require_price_domain(field_name: str, value: Decimal | None) -> None:
    """Raise ValueError when a present price is not finite or outside [0, 1]."""


def _is_sha256(value: str) -> bool:
    """Return True for lowercase 64-character hexadecimal digests."""


def _require_sha256(field_name: str, value: str) -> None:
    """Raise ValueError when value is not a lowercase 64-character SHA-256 digest."""


def _quantize_price(value: Decimal) -> Decimal:
    """Quantize price-like averages to Decimal("0.001") using ROUND_HALF_EVEN."""


def _exact_sum(values: Iterable[Decimal]) -> Decimal:
    """Sum Decimal values under a local high-precision context and return a Decimal."""


def _bid_depth_notional(requested_size: Decimal, book: OrderBookSnapshot) -> tuple[Decimal, Decimal]:
    """Walk finite positive bid levels and return (filled_size, exact executable notional)."""


def _normalize_log_path(value: Path | str) -> Path:
    """Return a file path and reject blank, non-path-like, directory, or bad-parent paths."""


def _validate_log_parent(path: Path) -> None:
    """Raise ValueError when the nearest existing parent is not a directory."""


def _json_ready(value: Any) -> Any:
    """Convert dataclass-asdict values to strict JSON-compatible values."""
```

`_bid_depth_notional()` must follow the same finite-positive bid filtering and tuple-order walking policy as `simulate_order_book_fill(order, book)` for sell orders. `mark_paper_nav()` must compare the helper's returned `filled_size` with the canonical `PaperFill.filled_size` and raise `ValueError("exit filled size mismatch")` if they differ.

`_json_ready()` must serialize finite `Decimal` values as strings, UTC `datetime` values as ISO strings, finite floats as floats, strings/integers/bools unchanged, dictionaries with string keys recursively, and lists/tuples recursively. It must reject non-finite numeric values and unsupported objects with `ValueError` before file opening.

## Part 0: Existing Contract Check

**Goal:** Reconfirm current Level 1A and Level 1B Node 1 contracts before implementing Level 1B Node 2.

**Files:**

- Inspect: `src/polymarket_alpha_lab/journal.py`
- Inspect: `src/polymarket_alpha_lab/paper.py`
- Inspect: `src/polymarket_alpha_lab/domain.py`
- Inspect: `src/polymarket_alpha_lab/rejections.py`
- Inspect: `src/polymarket_alpha_lab/__init__.py`
- Inspect: `tests/test_journal.py`
- Inspect: `tests/test_paper.py`
- Inspect: `tests/test_rejections.py`
- Inspect: `tests/test_init.py`

- [x] **Step 1: Inspect current contracts with CodeGraph**

Run:

```bash
codegraph explore "PaperTradeRecord PaperTradeJournal PaperOrder PaperFill simulate_order_book_fill OrderBookSnapshot OrderBookLevel RejectedCandidateLog __all__"
codegraph node src/polymarket_alpha_lab/journal.py
codegraph node src/polymarket_alpha_lab/paper.py
codegraph node src/polymarket_alpha_lab/domain.py
codegraph node src/polymarket_alpha_lab/rejections.py
codegraph node tests/test_journal.py
codegraph node tests/test_paper.py
codegraph node tests/test_rejections.py
codegraph node tests/test_init.py
codegraph node src/polymarket_alpha_lab/__init__.py
```

Expected: confirm that `PaperTradeRecord` contains filled trade data, `simulate_order_book_fill()` walks asks for buys and bids for sells, `PaperFill` contains quote metadata and a deterministic snapshot hash, `OrderBookSnapshot` exposes normalized bid/ask levels, `RejectedCandidateLog` validates before opening the file, and package-root exports use explicit imports plus explicit `__all__`.

**Recorded result:** Completed before implementation planning. CodeGraph confirmed the contracts above. `PaperTradeRecord.from_packet_and_fill()` only accepts positive filled size and stores `fill_filled_size`, `fill_average_price`, `order_side`, UTC timestamps, token/market metadata, and risk tags. `simulate_order_book_fill(PaperOrder(token_id=position.token_id, side="sell", size=position.open_size), book)` is the canonical bid-depth exit simulation and quantizes prices to `Decimal("0.001")` with `ROUND_HALF_EVEN`. `RejectedCandidateLog.append()` builds the JSON line with `allow_nan=False` before opening the path, rejects directory paths, creates parent directories, and appends without overwriting.

## Part 1: Position Replay Tests

**Goal:** Add failing tests that define paper-only portfolio replay semantics.

**Files:**

- Create: `tests/test_positions.py`
- Implemented in Part 2: `src/polymarket_alpha_lab/positions.py`

- [x] **Step 1: Write failing portfolio replay tests**

Create `tests/test_positions.py` with these imports, helpers, and tests:

```python
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.domain import OrderBookLevel, OrderBookSnapshot
from polymarket_alpha_lab.journal import PaperTradeRecord
from polymarket_alpha_lab.paper import PaperFill
from polymarket_alpha_lab.pipeline import ScoredCandidate
from polymarket_alpha_lab.positions import (
    PaperNavLog,
    PaperNavSnapshot,
    PaperPortfolio,
    PaperPosition,
    PaperPositionMark,
    build_paper_portfolio,
    mark_paper_nav,
)
from polymarket_alpha_lab.research import build_research_packet


def complete_packet(**overrides):
    values = {
        "candidate": ScoredCandidate(
            condition_id="0xabc",
            token_id="111",
            market_slug="example-market",
            question="Will the example resolve yes?",
            total_score="78.500",
            raw_archive_path="data/raw/gamma/markets.json",
        ),
        "created_at": datetime(2026, 6, 13, 12, 30, tzinfo=UTC),
        "market_url": "https://polymarket.com/event/example-market",
        "outcome_name": "Yes",
        "strategy_type": "market_quality",
        "model_probability": Decimal("0.56"),
        "bid": Decimal("0.50"),
        "ask": Decimal("0.52"),
        "midpoint": Decimal("0.51"),
        "expected_entry_price": Decimal("0.514"),
        "fair_value_estimate": Decimal("0.56"),
        "theoretical_edge": Decimal("0.046"),
        "spread": Decimal("0.02"),
        "slippage_estimate": Decimal("0.004"),
        "cost_adjusted_edge": Decimal("0.026"),
        "confidence": Decimal("0.60"),
        "max_executable_size": Decimal("100"),
        "risk_tags": ("liquidity",),
        "thesis": "Tight spread and clear rules.",
        "invalidating_conditions": "Spread widens.",
        "rule_text": "Example rule.",
        "resolution_source": "Example source",
    }
    values.update(overrides)
    return build_research_packet(**values)


def complete_fill(**overrides):
    values = {
        "token_id": "111",
        "side": "buy",
        "requested_size": Decimal("100"),
        "order_book_captured_at": datetime(2026, 6, 13, 12, 30, 30, tzinfo=UTC),
        "order_book_snapshot_sha256": "a" * 64,
        "filled_size": Decimal("100"),
        "unfilled_size": Decimal("0"),
        "average_price": Decimal("0.514"),
        "worst_price": Decimal("0.52"),
        "best_bid": Decimal("0.49"),
        "best_ask": Decimal("0.51"),
        "midpoint": Decimal("0.500"),
        "spread": Decimal("0.020"),
        "slippage_estimate": Decimal("0.004"),
    }
    values.update(overrides)
    return PaperFill(**values)


def record_from(packet=None, fill=None, **overrides):
    values = {
        "packet": packet or complete_packet(),
        "fill": fill or complete_fill(),
        "decision_timestamp": datetime(2026, 6, 13, 12, 31),
        "order_book_raw_archive_path": "data/raw/clob/book-111.json",
        "order_book_raw_payload_sha256": "b" * 64,
        "account_equity_before_trade": Decimal("10000"),
        "sizing_limiter": "max_executable_size",
        "planned_exit_rule": "Mark at executable bid on review.",
    }
    values.update(overrides)
    return PaperTradeRecord.from_packet_and_fill(**values)


def packet_at(minute: int, **overrides):
    values = {"created_at": datetime(2026, 6, 13, 12, minute, tzinfo=UTC)}
    values.update(overrides)
    return complete_packet(**values)


def test_build_paper_portfolio_opens_long_position_from_buy_record():
    record = record_from()

    portfolio = build_paper_portfolio(
        [record],
        starting_cash=Decimal("10000"),
    )

    assert portfolio.starting_cash == Decimal("10000")
    assert portfolio.cash_balance == Decimal("9948.600")
    assert portfolio.realized_pnl == Decimal("0")
    assert len(portfolio.positions) == 1
    position = portfolio.positions[0]
    assert position.source_packet_ids == (record.packet_id,)
    assert position.condition_id == "0xabc"
    assert position.token_id == "111"
    assert position.market_slug == "example-market"
    assert position.market_url == "https://polymarket.com/event/example-market"
    assert position.question == "Will the example resolve yes?"
    assert position.outcome_name == "Yes"
    assert position.strategy_type == "market_quality"
    assert position.risk_tags == ("liquidity",)
    assert position.rule_text_hash
    assert position.resolution_source == "Example source"
    assert position.market_raw_archive_path == "data/raw/gamma/markets.json"
    assert position.last_order_book_raw_archive_path == "data/raw/clob/book-111.json"
    assert position.last_order_book_raw_payload_sha256 == "b" * 64
    assert position.last_order_book_snapshot_sha256 == "a" * 64
    assert position.opened_at == datetime(2026, 6, 13, 12, 31, tzinfo=UTC)
    assert position.updated_at == datetime(2026, 6, 13, 12, 31, tzinfo=UTC)
    assert position.open_size == Decimal("100")
    assert position.cost_basis == Decimal("51.400")
    assert position.average_entry_price == Decimal("0.514")
    assert position.realized_pnl == Decimal("0")
    assert position.entry_trade_count == 1
    assert position.exit_trade_count == 0


def test_build_paper_portfolio_uses_filled_size_not_requested_size():
    partial_buy = record_from(
        fill=complete_fill(
            requested_size=Decimal("100"),
            filled_size=Decimal("40"),
            unfilled_size=Decimal("60"),
            average_price=Decimal("0.510"),
            worst_price=Decimal("0.51"),
        )
    )

    portfolio = build_paper_portfolio([partial_buy], starting_cash=Decimal("10000"))

    assert portfolio.cash_balance == Decimal("9979.600")
    assert portfolio.positions[0].open_size == Decimal("40")
    assert portfolio.positions[0].cost_basis == Decimal("20.400")
    assert portfolio.positions[0].average_entry_price == Decimal("0.510")


def test_build_paper_portfolio_replays_partial_sell_and_realized_pnl():
    buy = record_from()
    sell = record_from(
        packet=packet_at(32),
        fill=complete_fill(
            side="sell",
            requested_size=Decimal("40"),
            filled_size=Decimal("40"),
            unfilled_size=Decimal("0"),
            average_price=Decimal("0.600"),
            worst_price=Decimal("0.60"),
        )
    )

    portfolio = build_paper_portfolio([buy, sell], starting_cash=Decimal("10000"))

    assert portfolio.cash_balance == Decimal("9972.600")
    assert portfolio.realized_pnl == Decimal("3.440")
    assert len(portfolio.positions) == 1
    assert portfolio.positions[0].open_size == Decimal("60")
    assert portfolio.positions[0].cost_basis == Decimal("30.840")
    assert portfolio.positions[0].average_entry_price == Decimal("0.514")
    assert portfolio.positions[0].realized_pnl == Decimal("3.440")
    assert portfolio.positions[0].entry_trade_count == 1
    assert portfolio.positions[0].exit_trade_count == 1


def test_build_paper_portfolio_uses_sell_filled_size_not_requested_size():
    buy = record_from()
    sell = record_from(
        packet=packet_at(32, max_executable_size=Decimal("120")),
        fill=complete_fill(
            side="sell",
            requested_size=Decimal("120"),
            filled_size=Decimal("40"),
            unfilled_size=Decimal("80"),
            average_price=Decimal("0.600"),
            worst_price=Decimal("0.60"),
        ),
    )

    portfolio = build_paper_portfolio([buy, sell], starting_cash=Decimal("10000"))

    assert portfolio.cash_balance == Decimal("9972.600")
    assert portfolio.realized_pnl == Decimal("3.440")
    assert portfolio.positions[0].open_size == Decimal("60")
    assert portfolio.positions[0].cost_basis == Decimal("30.840")


def test_build_paper_portfolio_allows_negative_realized_pnl():
    buy = record_from()
    sell = record_from(
        packet=packet_at(32),
        fill=complete_fill(
            side="sell",
            requested_size=Decimal("40"),
            filled_size=Decimal("40"),
            unfilled_size=Decimal("0"),
            average_price=Decimal("0.400"),
            worst_price=Decimal("0.40"),
        ),
    )

    portfolio = build_paper_portfolio([buy, sell], starting_cash=Decimal("10000"))

    assert portfolio.cash_balance == Decimal("9964.600")
    assert portfolio.realized_pnl == Decimal("-4.560")
    assert portfolio.positions[0].open_size == Decimal("60")
    assert portfolio.positions[0].cost_basis == Decimal("30.840")
    assert portfolio.positions[0].realized_pnl == Decimal("-4.560")


def test_build_paper_portfolio_omits_fully_closed_positions():
    buy = record_from()
    sell = record_from(
        packet=packet_at(32),
        fill=complete_fill(
            side="sell",
            requested_size=Decimal("100"),
            filled_size=Decimal("100"),
            unfilled_size=Decimal("0"),
            average_price=Decimal("0.600"),
            worst_price=Decimal("0.60"),
        )
    )

    portfolio = build_paper_portfolio([buy, sell], starting_cash=Decimal("10000"))

    assert portfolio.cash_balance == Decimal("10008.600")
    assert portfolio.realized_pnl == Decimal("8.600")
    assert portfolio.positions == ()


def test_build_paper_portfolio_rejects_sell_before_buy():
    sell = record_from(fill=complete_fill(side="sell"))

    with pytest.raises(ValueError, match="sell.*open position"):
        build_paper_portfolio([sell], starting_cash=Decimal("10000"))


def test_build_paper_portfolio_rejects_oversell():
    buy = record_from(
        fill=complete_fill(
            requested_size=Decimal("40"),
            filled_size=Decimal("40"),
            unfilled_size=Decimal("0"),
            average_price=Decimal("0.510"),
            worst_price=Decimal("0.51"),
        )
    )
    sell = record_from(
        packet=packet_at(32),
        fill=complete_fill(
            side="sell",
            requested_size=Decimal("50"),
            filled_size=Decimal("50"),
            unfilled_size=Decimal("0"),
            average_price=Decimal("0.600"),
            worst_price=Decimal("0.60"),
        )
    )

    with pytest.raises(ValueError, match="sell.*open_size"):
        build_paper_portfolio([buy, sell], starting_cash=Decimal("10000"))


def test_build_paper_portfolio_rejects_insufficient_cash_for_buy():
    with pytest.raises(ValueError, match="cash"):
        build_paper_portfolio([record_from()], starting_cash=Decimal("10"))


def test_build_paper_portfolio_returns_empty_portfolio_for_no_records():
    portfolio = build_paper_portfolio([], starting_cash=Decimal("10000"))

    assert portfolio.starting_cash == Decimal("10000")
    assert portfolio.cash_balance == Decimal("10000")
    assert portfolio.realized_pnl == Decimal("0")
    assert portfolio.positions == ()


def test_build_paper_portfolio_rejects_duplicate_packet_id():
    record = record_from()

    with pytest.raises(ValueError, match="duplicate.*packet_id"):
        build_paper_portfolio([record, record], starting_cash=Decimal("10000"))
```

- [x] **Step 2: Run portfolio replay tests to verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_positions.py -q
```

Expected: fail because `polymarket_alpha_lab.positions` or the new public names do not exist.

## Part 2: Position Replay Implementation

**Goal:** Implement the minimal position replay API to satisfy Part 1.

**Files:**

- Create: `src/polymarket_alpha_lab/positions.py`

- [x] **Step 1: Implement frozen dataclasses, validation helpers, and `build_paper_portfolio()`**

Create `src/polymarket_alpha_lab/positions.py` with this import block and public symbol set:

```python
"""Paper position ledger and executable NAV marks."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from math import isfinite
from pathlib import Path
from typing import Any, Iterable, Mapping

from polymarket_alpha_lab.domain import OrderBookSnapshot
from polymarket_alpha_lab.journal import PaperTradeRecord
from polymarket_alpha_lab.paper import PaperOrder, simulate_order_book_fill

PRICE_QUANTUM = Decimal("0.001")
PRICE_CONTEXT = Context(prec=28, rounding=ROUND_HALF_EVEN)
MARK_STATUSES = frozenset(
    {
        "fully_executable",
        "partially_executable",
        "no_exit_depth",
    }
)
```

Implementation rules:

- Define the five frozen dataclasses exactly as listed in `## Planned Dataclasses`.
- Define `build_paper_portfolio(records: Iterable[PaperTradeRecord], *, starting_cash: Decimal) -> PaperPortfolio`.
- Define `mark_paper_nav(portfolio: PaperPortfolio, books_by_token_id: Mapping[str, OrderBookSnapshot], *, marked_at: datetime) -> PaperNavSnapshot`.
- Define `PaperNavLog.append(self, snapshot: PaperNavSnapshot) -> None`.
- Implement `PaperPosition` and `PaperPortfolio` first; leave NAV-specific classes present but with validation sufficient for imports if needed.
- Validate public inputs with controlled `ValueError`.
- Convert `records` to `tuple(records)` and reject bare `str`/`bytes` as invalid record iterables.
- Normalize datetimes through `_as_utc(value)`.
- Normalize string tuples through `_normalize_string_tuple(field_name, value)`.
- Normalize packet id tuples through `_normalize_string_tuple("source_packet_ids", value)` and reject duplicate packet ids in the input stream before applying accounting changes.
- Use `_require_finite_decimal(field_name, value)`, `_require_nonnegative_decimal(field_name, value)`, `_require_positive_decimal(field_name, value)`, and `_quantize_price(value)`.
- Use `_is_sha256(value)` for every stored lowercase 64-character digest.
- Use a small internal mutable dict while replaying records; return immutable dataclasses.
- Carry `source_packet_ids`, `rule_text_hash`, `resolution_source`, `market_raw_archive_path`, and the latest order-book archive/hash fields from the replayed records into `PaperPosition`.
- Recompute average entry price as `_quantize_price(cost_basis / open_size)` after buys and partial sells.
- Sort final `positions` by `(condition_id, token_id, market_slug, outcome_name, strategy_type)` for deterministic output.
- Use `replace(position, open_size=new_size, cost_basis=new_cost_basis, average_entry_price=new_average_entry_price, updated_at=record.decision_timestamp_utc)` to update frozen positions.

- [x] **Step 2: Run portfolio replay tests to verify GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_positions.py -q
```

Expected: Part 1 tests pass. NAV tests do not exist yet.

## Part 3: Executable NAV Mark Tests

**Goal:** Add failing tests that define executable exit NAV behavior.

**Files:**

- Modify: `tests/test_positions.py`
- Implemented in Part 4: `src/polymarket_alpha_lab/positions.py`

- [x] **Step 1: Add failing NAV mark tests**

Append these tests to `tests/test_positions.py`:

```python
def test_mark_paper_nav_uses_bid_side_exit_depth_for_longs():
    portfolio = build_paper_portfolio([record_from()], starting_cash=Decimal("10000"))
    book = OrderBookSnapshot(
        token_id="111",
        bids=(
            OrderBookLevel(Decimal("0.50"), Decimal("60")),
            OrderBookLevel(Decimal("0.49"), Decimal("40")),
        ),
        asks=(OrderBookLevel(Decimal("0.52"), Decimal("100")),),
        captured_at=datetime(2026, 6, 14, tzinfo=UTC),
    )

    snapshot = mark_paper_nav(
        portfolio,
        {"111": book},
        marked_at=datetime(2026, 6, 14, 0, 0),
    )

    assert snapshot.marked_at == datetime(2026, 6, 14, tzinfo=UTC)
    assert snapshot.cash_balance == Decimal("9948.600")
    assert snapshot.realized_pnl == Decimal("0")
    assert snapshot.total_cost_basis == Decimal("51.400")
    assert snapshot.exit_nav == Decimal("9998.200")
    assert snapshot.midpoint_nav == Decimal("9999.600")
    assert snapshot.unrealized_exit_pnl == Decimal("-1.800")
    assert snapshot.paper_only is True
    assert len(snapshot.marks) == 1
    mark = snapshot.marks[0]
    assert mark.token_id == "111"
    assert mark.open_size == Decimal("100")
    assert mark.cost_basis == Decimal("51.400")
    assert mark.average_entry_price == Decimal("0.514")
    assert mark.order_book_captured_at == datetime(2026, 6, 14, tzinfo=UTC)
    assert len(mark.order_book_snapshot_sha256) == 64
    assert mark.exit_filled_size == Decimal("100")
    assert mark.exit_unfilled_size == Decimal("0")
    assert mark.exit_average_price == Decimal("0.496")
    assert mark.exit_worst_price == Decimal("0.49")
    assert mark.exit_value == Decimal("49.600")
    assert mark.midpoint_price == Decimal("0.510")
    assert mark.midpoint_value == Decimal("51.000")
    assert mark.best_bid == Decimal("0.50")
    assert mark.best_ask == Decimal("0.52")
    assert mark.spread == Decimal("0.020")
    assert mark.slippage_estimate == Decimal("0.004")
    assert mark.mark_status == "fully_executable"


def test_mark_paper_nav_uses_exact_bid_walk_notional_not_quantized_average_product():
    buy = record_from(
        fill=complete_fill(
            requested_size=Decimal("3"),
            filled_size=Decimal("3"),
            unfilled_size=Decimal("0"),
            average_price=Decimal("0.100"),
            worst_price=Decimal("0.10"),
        )
    )
    portfolio = build_paper_portfolio([buy], starting_cash=Decimal("100"))
    book = OrderBookSnapshot(
        token_id="111",
        bids=(
            OrderBookLevel(Decimal("0.20"), Decimal("2")),
            OrderBookLevel(Decimal("0.10"), Decimal("1")),
        ),
        asks=(OrderBookLevel(Decimal("0.30"), Decimal("3")),),
        captured_at=datetime(2026, 6, 14, tzinfo=UTC),
    )

    snapshot = mark_paper_nav(
        portfolio,
        {"111": book},
        marked_at=datetime(2026, 6, 14, tzinfo=UTC),
    )

    mark = snapshot.marks[0]
    assert mark.exit_filled_size == Decimal("3")
    assert mark.exit_average_price == Decimal("0.167")
    assert mark.exit_filled_size * mark.exit_average_price == Decimal("0.501")
    assert mark.exit_value == Decimal("0.500")
    assert snapshot.exit_nav == Decimal("100.200")


def test_mark_paper_nav_values_unfilled_exit_depth_at_zero():
    portfolio = build_paper_portfolio([record_from()], starting_cash=Decimal("10000"))
    book = OrderBookSnapshot(
        token_id="111",
        bids=(OrderBookLevel(Decimal("0.50"), Decimal("25")),),
        asks=(OrderBookLevel(Decimal("0.52"), Decimal("100")),),
        captured_at=datetime(2026, 6, 14, tzinfo=UTC),
    )

    snapshot = mark_paper_nav(
        portfolio,
        {"111": book},
        marked_at=datetime(2026, 6, 14, tzinfo=UTC),
    )

    assert snapshot.exit_nav == Decimal("9961.100")
    assert snapshot.unrealized_exit_pnl == Decimal("-38.900")
    assert snapshot.marks[0].exit_filled_size == Decimal("25")
    assert snapshot.marks[0].exit_unfilled_size == Decimal("75")
    assert snapshot.marks[0].exit_average_price == Decimal("0.500")
    assert snapshot.marks[0].exit_value == Decimal("12.500")
    assert snapshot.marks[0].mark_status == "partially_executable"


def test_mark_paper_nav_reports_no_exit_depth_without_midpoint_nav():
    portfolio = build_paper_portfolio([record_from()], starting_cash=Decimal("10000"))
    book = OrderBookSnapshot(
        token_id="111",
        bids=(),
        asks=(OrderBookLevel(Decimal("0.52"), Decimal("100")),),
        captured_at=datetime(2026, 6, 14, tzinfo=UTC),
    )

    snapshot = mark_paper_nav(
        portfolio,
        {"111": book},
        marked_at=datetime(2026, 6, 14, tzinfo=UTC),
    )

    assert snapshot.exit_nav == Decimal("9948.600")
    assert snapshot.midpoint_nav is None
    assert snapshot.unrealized_exit_pnl == Decimal("-51.400")
    assert snapshot.marks[0].exit_filled_size == Decimal("0")
    assert snapshot.marks[0].exit_unfilled_size == Decimal("100")
    assert snapshot.marks[0].exit_average_price is None
    assert snapshot.marks[0].exit_worst_price is None
    assert snapshot.marks[0].exit_value == Decimal("0")
    assert snapshot.marks[0].midpoint_price is None
    assert snapshot.marks[0].midpoint_value is None
    assert snapshot.marks[0].mark_status == "no_exit_depth"


def test_mark_paper_nav_rejects_missing_book_for_open_position():
    portfolio = build_paper_portfolio([record_from()], starting_cash=Decimal("10000"))

    with pytest.raises(ValueError, match="missing.*111"):
        mark_paper_nav(
            portfolio,
            {},
            marked_at=datetime(2026, 6, 14, tzinfo=UTC),
        )


def test_mark_paper_nav_rejects_token_mismatch_book():
    portfolio = build_paper_portfolio([record_from()], starting_cash=Decimal("10000"))
    book = OrderBookSnapshot(
        token_id="222",
        bids=(OrderBookLevel(Decimal("0.50"), Decimal("100")),),
        asks=(OrderBookLevel(Decimal("0.52"), Decimal("100")),),
        captured_at=datetime(2026, 6, 14, tzinfo=UTC),
    )

    with pytest.raises(ValueError, match="token_id"):
        mark_paper_nav(
            portfolio,
            {"111": book},
            marked_at=datetime(2026, 6, 14, tzinfo=UTC),
        )


def test_mark_paper_nav_preserves_crossed_book_executable_mark():
    portfolio = build_paper_portfolio([record_from()], starting_cash=Decimal("10000"))
    book = OrderBookSnapshot(
        token_id="111",
        bids=(OrderBookLevel(Decimal("0.55"), Decimal("100")),),
        asks=(OrderBookLevel(Decimal("0.53"), Decimal("100")),),
        captured_at=datetime(2026, 6, 14, tzinfo=UTC),
    )

    snapshot = mark_paper_nav(
        portfolio,
        {"111": book},
        marked_at=datetime(2026, 6, 14, tzinfo=UTC),
    )

    assert snapshot.exit_nav == Decimal("10003.600")
    assert snapshot.midpoint_nav == Decimal("10002.600")
    assert snapshot.marks[0].exit_average_price == Decimal("0.550")
    assert snapshot.marks[0].midpoint_price == Decimal("0.540")
    assert snapshot.marks[0].spread == Decimal("-0.020")
    assert snapshot.marks[0].mark_status == "fully_executable"
```

- [x] **Step 2: Run NAV mark tests to verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_positions.py -q
```

Expected: fail because `mark_paper_nav()` and NAV dataclass validation are not implemented.

## Part 4: Executable NAV Mark Implementation

**Goal:** Implement NAV mark dataclasses and `mark_paper_nav()`.

**Files:**

- Modify: `src/polymarket_alpha_lab/positions.py`

- [x] **Step 1: Implement mark dataclasses and `mark_paper_nav()`**

Implementation rules:

- `PaperPositionMark.__post_init__()` validates:
  - identity strings are valid
  - `open_size` is positive and finite
  - `cost_basis`, `exit_filled_size`, `exit_unfilled_size`, `exit_value`, and optional values are finite `Decimal`s
  - optional prices are in `[0, 1]` when present
  - `mark_status in MARK_STATUSES`
  - `exit_filled_size + exit_unfilled_size == open_size`
  - `fully_executable` means `exit_unfilled_size == 0`
  - `partially_executable` means both `exit_filled_size > 0` and `exit_unfilled_size > 0`
  - `no_exit_depth` means `exit_filled_size == 0`
- `PaperNavSnapshot.__post_init__()` validates:
  - `marked_at` is UTC-normalized
  - all numeric fields are finite
  - `paper_only is True`
  - `marks` is a tuple of `PaperPositionMark`
  - `exit_nav == cash_balance + sum(mark.exit_value for mark in marks)`
  - if every mark has `midpoint_value is not None`, `midpoint_nav` equals `cash_balance + sum(mark.midpoint_value for mark in marks)`; otherwise `midpoint_nav is None`
  - `total_cost_basis == sum(mark.cost_basis for mark in marks)`
  - `unrealized_exit_pnl == sum(mark.exit_value - mark.cost_basis for mark in marks)`
- `mark_paper_nav()`:
  - validates inputs
  - iterates positions in existing deterministic portfolio order
  - rejects missing/mismatched books
  - calls `simulate_order_book_fill(PaperOrder(token_id=position.token_id, side="sell", size=position.open_size), book)`
  - computes exact executable bid-walk notional with `_bid_depth_notional(position.open_size, book)`
  - rejects the mark if `_bid_depth_notional(...)[0] != exit_fill.filled_size`
  - sets `exit_value` only from `_bid_depth_notional(...)[1]`; it must never use midpoint, best bid alone, model probability, fair value, or `exit_fill.filled_size * exit_fill.average_price` for executable NAV
  - builds `PaperPositionMark` from the exit fill and position metadata
  - calculates totals with exact Decimal arithmetic under a local context
  - returns `PaperNavSnapshot`

- [x] **Step 2: Run NAV mark tests to verify GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_positions.py -q
```

Expected: all current `tests/test_positions.py` tests pass.

## Part 5: JSONL NAV Log And Direct Validation Tests

**Goal:** Lock down strict persistence, append-without-overwrite behavior, validation-before-open behavior, and public invalid input boundaries.

**Files:**

- Modify: `tests/test_positions.py`
- Modified in Part 6: `src/polymarket_alpha_lab/positions.py`

- [x] **Step 1: Add failing persistence and validation tests**

Append these tests to `tests/test_positions.py`:

```python
def executable_snapshot():
    portfolio = build_paper_portfolio([record_from()], starting_cash=Decimal("10000"))
    book = OrderBookSnapshot(
        token_id="111",
        bids=(OrderBookLevel(Decimal("0.50"), Decimal("100")),),
        asks=(OrderBookLevel(Decimal("0.52"), Decimal("100")),),
        captured_at=datetime(2026, 6, 14, tzinfo=UTC),
    )
    return mark_paper_nav(
        portfolio,
        {"111": book},
        marked_at=datetime(2026, 6, 14, tzinfo=UTC),
    )


def test_paper_nav_log_appends_jsonl_snapshot(tmp_path):
    snapshot = executable_snapshot()
    log = PaperNavLog(path=tmp_path / "nav.jsonl")

    log.append(snapshot)

    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert lines[0].startswith('{"cash_balance"')
    stored = json.loads(lines[0])
    assert stored["paper_only"] is True
    assert stored["marked_at"] == "2026-06-14T00:00:00+00:00"
    assert stored["starting_cash"] == "10000"
    assert stored["cash_balance"] == "9948.600"
    assert stored["exit_nav"] == "9998.600"
    assert stored["midpoint_nav"] == "9999.600"
    assert stored["total_cost_basis"] == "51.400"
    assert stored["unrealized_exit_pnl"] == "-1.400"
    assert stored["marks"][0]["token_id"] == "111"
    assert stored["marks"][0]["order_book_captured_at"] == "2026-06-14T00:00:00+00:00"
    assert stored["marks"][0]["exit_average_price"] == "0.500"
    assert stored["marks"][0]["order_book_snapshot_sha256"]


def test_paper_nav_log_appends_without_overwriting(tmp_path):
    log = PaperNavLog(path=str(tmp_path / "nested" / "nav.jsonl"))
    first = executable_snapshot()
    second = replace(
        executable_snapshot(),
        marked_at=datetime(2026, 6, 15, tzinfo=UTC),
    )

    log.append(first)
    log.append(second)

    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["marked_at"] == "2026-06-14T00:00:00+00:00"
    assert json.loads(lines[1])["marked_at"] == "2026-06-15T00:00:00+00:00"


def test_paper_nav_log_rejects_invalid_paths(tmp_path):
    with pytest.raises(ValueError, match="path"):
        PaperNavLog(path=object())
    with pytest.raises(ValueError, match="path"):
        PaperNavLog(path="")
    with pytest.raises(ValueError, match="path"):
        PaperNavLog(path=tmp_path)
    parent_file = tmp_path / "not-a-directory"
    parent_file.write_text("already a file", encoding="utf-8")
    with pytest.raises(ValueError, match="path"):
        PaperNavLog(path=parent_file / "nav.jsonl")


def test_paper_nav_log_rejects_invalid_public_input(tmp_path):
    log = PaperNavLog(path=tmp_path / "nav.jsonl")

    with pytest.raises(ValueError, match="snapshot"):
        log.append(object())

    assert not log.path.exists()


def test_paper_nav_log_rejects_non_finite_decimal_before_open(tmp_path):
    snapshot = executable_snapshot()
    object.__setattr__(snapshot, "cash_balance", Decimal("NaN"))
    log = PaperNavLog(path=tmp_path / "nav.jsonl")

    with pytest.raises(ValueError, match="finite"):
        log.append(snapshot)

    assert not log.path.exists()


def test_paper_nav_log_preserves_existing_file_when_serialization_fails(tmp_path):
    snapshot = executable_snapshot()
    object.__setattr__(snapshot, "cash_balance", Decimal("NaN"))
    path = tmp_path / "nav.jsonl"
    path.write_text('{"existing": true}\n', encoding="utf-8")
    log = PaperNavLog(path=path)

    with pytest.raises(ValueError, match="finite"):
        log.append(snapshot)

    assert path.read_text(encoding="utf-8") == '{"existing": true}\n'


def test_positions_dataclasses_are_frozen():
    portfolio = build_paper_portfolio([record_from()], starting_cash=Decimal("10000"))
    snapshot = executable_snapshot()

    with pytest.raises(FrozenInstanceError):
        portfolio.cash_balance = Decimal("1")
    with pytest.raises(FrozenInstanceError):
        portfolio.positions[0].open_size = Decimal("1")
    with pytest.raises(FrozenInstanceError):
        snapshot.exit_nav = Decimal("1")
    with pytest.raises(FrozenInstanceError):
        snapshot.marks[0].exit_value = Decimal("1")


@pytest.mark.parametrize(
    "starting_cash",
    [Decimal("0"), Decimal("-1"), Decimal("NaN"), Decimal("Infinity")],
)
def test_build_paper_portfolio_rejects_invalid_starting_cash(starting_cash):
    with pytest.raises(ValueError, match="starting_cash"):
        build_paper_portfolio([record_from()], starting_cash=starting_cash)


def test_build_paper_portfolio_rejects_invalid_public_inputs():
    with pytest.raises(ValueError, match="records"):
        build_paper_portfolio("not-records", starting_cash=Decimal("10000"))
    with pytest.raises(ValueError, match="record"):
        build_paper_portfolio([object()], starting_cash=Decimal("10000"))
    with pytest.raises(ValueError, match="starting_cash"):
        build_paper_portfolio([record_from()], starting_cash="10000")


def test_build_paper_portfolio_rejects_inconsistent_token_metadata():
    first = record_from()
    changed_packet = packet_at(32, market_url="https://polymarket.com/event/changed")
    second = record_from(packet=changed_packet)

    with pytest.raises(ValueError, match="metadata"):
        build_paper_portfolio([first, second], starting_cash=Decimal("10000"))


def test_position_timestamps_normalize_to_utc():
    eastern = timezone(timedelta(hours=-4))
    record = record_from(
        decision_timestamp=datetime(2026, 6, 13, 8, 31, tzinfo=eastern),
    )

    portfolio = build_paper_portfolio([record], starting_cash=Decimal("10000"))

    assert portfolio.positions[0].opened_at == datetime(2026, 6, 13, 12, 31, tzinfo=UTC)
    assert portfolio.positions[0].updated_at == datetime(2026, 6, 13, 12, 31, tzinfo=UTC)


def test_direct_position_construction_rejects_invalid_state():
    position = build_paper_portfolio([record_from()], starting_cash=Decimal("10000")).positions[0]

    with pytest.raises(ValueError, match="open_size"):
        replace(position, open_size=Decimal("0"))
    with pytest.raises(ValueError, match="risk_tags"):
        replace(position, risk_tags=("liquidity", " "))
    with pytest.raises(ValueError, match="average_entry_price"):
        replace(position, average_entry_price=Decimal("NaN"))
    with pytest.raises(ValueError, match="SHA-256|sha256"):
        replace(position, last_order_book_raw_payload_sha256="A" * 64)
    with pytest.raises(ValueError, match="SHA-256|sha256"):
        replace(position, last_order_book_snapshot_sha256="not-hex")


def test_direct_nav_snapshot_rejects_invalid_state():
    snapshot = executable_snapshot()

    with pytest.raises(ValueError, match="paper_only"):
        replace(snapshot, paper_only=False)
    with pytest.raises(ValueError, match="marks"):
        replace(snapshot, marks=(object(),))
    with pytest.raises(ValueError, match="exit_nav"):
        replace(snapshot, exit_nav=Decimal("1"))
    with pytest.raises(ValueError, match="total_cost_basis"):
        replace(snapshot, total_cost_basis=Decimal("1"))
    with pytest.raises(ValueError, match="unrealized_exit_pnl"):
        replace(snapshot, unrealized_exit_pnl=Decimal("1"))


def test_direct_nav_snapshot_normalizes_marked_at_to_utc():
    eastern = timezone(timedelta(hours=-4))
    snapshot = replace(
        executable_snapshot(),
        marked_at=datetime(2026, 6, 13, 20, 0, tzinfo=eastern),
    )

    assert snapshot.marked_at == datetime(2026, 6, 14, 0, 0, tzinfo=UTC)


def test_direct_position_mark_rejects_invalid_status():
    mark = executable_snapshot().marks[0]

    with pytest.raises(ValueError, match="mark_status"):
        replace(mark, mark_status="midpoint_only")
    with pytest.raises(ValueError, match="exit_filled_size"):
        replace(mark, exit_filled_size=Decimal("0"), mark_status="fully_executable")
    with pytest.raises(ValueError, match="SHA-256|sha256"):
        replace(mark, order_book_snapshot_sha256="a" * 63)


def test_direct_position_mark_normalizes_order_book_timestamp_to_utc():
    eastern = timezone(timedelta(hours=-4))
    mark = replace(
        executable_snapshot().marks[0],
        order_book_captured_at=datetime(2026, 6, 13, 20, 0, tzinfo=eastern),
    )

    assert mark.order_book_captured_at == datetime(2026, 6, 14, 0, 0, tzinfo=UTC)
```

- [x] **Step 2: Run persistence and validation tests to verify RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_positions.py -q
```

Expected: fail on missing or incomplete persistence and direct validation behavior.

## Part 6: JSONL NAV Log And Validation Implementation

**Goal:** Implement strict JSONL persistence and harden direct dataclass validation.

**Files:**

- Modify: `src/polymarket_alpha_lab/positions.py`

- [x] **Step 1: Implement `PaperNavLog` and JSON validation helpers**

Implementation rules:

- `PaperNavLog.__post_init__()` normalizes and validates the path:
  - reject non-path-like values
  - reject blank strings
  - reject paths that exist and are directories
  - reject paths whose nearest existing parent is a file
- `PaperNavLog.append(snapshot)`:
  - require `isinstance(snapshot, PaperNavSnapshot)`
  - build `line = json.dumps(_json_ready(asdict(snapshot)), allow_nan=False, sort_keys=True) + "\n"` before path validation, parent directory creation, or file opening
  - create parent directories
  - append with UTF-8
- `_json_ready(value)`:
  - `None` -> `None`
  - finite `Decimal` -> `str(value)`
  - `datetime` -> `_as_utc(value).isoformat()`
  - finite `float` -> `value`
  - `str`, `int`, `bool` -> unchanged
  - `dict` with string keys -> recurse
  - `list` or `tuple` -> recurse
  - everything else -> `ValueError("nav log values must be JSON serializable")`
- Harden direct dataclass `__post_init__()` methods until all validation tests pass.

- [x] **Step 2: Run full positions tests to verify GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_positions.py -q
```

Expected: all positions tests pass.

## Part 7: Package Exports And README

**Goal:** Expose the Node 2 API and document the new paper-only status.

**Files:**

- Modify: `src/polymarket_alpha_lab/__init__.py`
- Modify: `tests/test_init.py`
- Modify: `README.md`

- [x] **Step 1: Add failing package-root export test**

Modify `tests/test_init.py`:

```python
from polymarket_alpha_lab.positions import (
    PaperNavLog,
    PaperNavSnapshot,
    PaperPortfolio,
    PaperPosition,
    PaperPositionMark,
    build_paper_portfolio,
    mark_paper_nav,
)
```

Add this test:

```python
def test_level_1b_node_2_public_api_exports():
    expected_exports = {
        "PaperNavLog",
        "PaperNavSnapshot",
        "PaperPortfolio",
        "PaperPosition",
        "PaperPositionMark",
        "build_paper_portfolio",
        "mark_paper_nav",
    }

    assert expected_exports <= set(lab.__all__)
    assert lab.PaperNavLog is PaperNavLog
    assert lab.PaperNavSnapshot is PaperNavSnapshot
    assert lab.PaperPortfolio is PaperPortfolio
    assert lab.PaperPosition is PaperPosition
    assert lab.PaperPositionMark is PaperPositionMark
    assert lab.build_paper_portfolio is build_paper_portfolio
    assert lab.mark_paper_nav is mark_paper_nav
```

Run:

```bash
.venv/bin/python -m pytest tests/test_init.py -q
```

Expected: fail because package root does not export the new names.

- [x] **Step 2: Export positions APIs from package root**

Modify `src/polymarket_alpha_lab/__init__.py`:

```python
from polymarket_alpha_lab.positions import (
    PaperNavLog,
    PaperNavSnapshot,
    PaperPortfolio,
    PaperPosition,
    PaperPositionMark,
    build_paper_portfolio,
    mark_paper_nav,
)
```

Add these names to `__all__` in the existing explicit list:

```python
"PaperNavLog",
"PaperNavSnapshot",
"PaperPortfolio",
"PaperPosition",
"PaperPositionMark",
"build_paper_portfolio",
"mark_paper_nav",
```

Run:

```bash
.venv/bin/python -m pytest tests/test_init.py -q
```

Expected: pass.

- [x] **Step 3: Update README Level 1B status and repository tree**

Modify `README.md`:

1. Update the Phase 1 Scope sentence to include paper-only position ledgers and executable NAV marks.
2. Add this section after Level 1B Node 1 Python API:

```markdown
## Level 1B Node 2 Status

Level 1B Node 2 adds a paper-only position ledger and executable NAV marks derived from accepted paper-trade journal records and supplied public order book snapshots. It does not fetch order books, place orders, authenticate, handle private keys, cancel orders, open user WebSockets, run heartbeat logic, reconcile exchange account positions, or create live-trading proposals.

## Level 1B Node 2 Python API

Node 2 is exposed through Python APIs:

- Build paper portfolios with `build_paper_portfolio(records, starting_cash=Decimal("10000"))`, which returns `PaperPortfolio`.
- Mark open positions with `mark_paper_nav(portfolio, books_by_token_id, marked_at=datetime.now(UTC))`, which returns `PaperNavSnapshot`.
- Persist executable NAV snapshots with `PaperNavLog(path).append(snapshot)`.
```

3. Add `positions.py` under `src/polymarket_alpha_lab`.
4. Add `test_positions.py` under `tests`.
5. Add both `2026-06-13-level-1b-rejections-risk-gates.md` and `2026-06-13-level-1b-positions-nav.md` under `docs/superpowers/plans` if the README tree does not already list them.

- [x] **Step 4: Run node-specific tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_positions.py tests/test_init.py -q
```

Expected: pass.

## Level 1B Node 2 Completion Criteria

Level 1B Node 2 is complete only when all of these are true:

- `src/polymarket_alpha_lab/positions.py` exists and is paper-only: it consumes `PaperTradeRecord` and supplied `OrderBookSnapshot` values without fetching data, authenticating, touching private keys, placing/canceling orders, opening WebSockets, sending heartbeat requests, reconciling exchange accounts, or creating trade proposals.
- `build_paper_portfolio(...)` deterministically replays accepted paper records in input order, rejects duplicate `packet_id` values, uses `fill_filled_size` rather than requested size, rejects invalid records with controlled `ValueError`, and never creates short or negative paper inventory.
- Buy fills increase open long paper inventory, cost basis, entry count, and reduce cash; sell fills reduce existing long inventory, increase cash, realize PnL, and reject sell-before-buy or oversell.
- Fully closed positions are omitted from `PaperPortfolio.positions`, while portfolio-level realized PnL and cash remain correct.
- Open positions preserve provenance needed for audit: source packet ids, token/market identity, strategy, canonical ordered-union risk tags, rule hash, resolution source, raw market archive path, latest order-book archive path, latest raw payload SHA-256, and latest normalized order-book snapshot SHA-256.
- Partial sells relieve cost basis proportionally from current remaining cost basis rather than from the quantized display `average_entry_price`; direct portfolio and NAV snapshot construction enforces the cash accounting identity under a local high-precision Decimal context.
- `mark_paper_nav(...)` marks each open long position from executable bid-side depth for that token, records filled and unfilled exit size, values unfilled exit size at zero, and never substitutes midpoint, fair value, model probability, or best bid alone as executable NAV.
- `mark_paper_nav(...)` uses `simulate_order_book_fill(order, book)` for canonical fill metadata and an exact bid-depth notional helper for `exit_value`, so quantized `exit_average_price` cannot introduce NAV drift.
- Missing books and token mismatches raise `ValueError`; no-bid books produce `mark_status == "no_exit_depth"`; partial bid depth produces `mark_status == "partially_executable"`; full depth produces `mark_status == "fully_executable"`; crossed books preserve executable marks plus quote metadata.
- `PaperNavSnapshot` stores UTC `marked_at`, cash, realized PnL, executable `exit_nav`, optional informational `midpoint_nav`, total cost basis, unrealized executable PnL, mark entries, and `paper_only=True`; mark construction rejects impossible binary-share values such as `cost_basis > open_size`, `exit_value > exit_filled_size`, nonzero value with no exit depth, or midpoint value above open size.
- `PaperNavLog` follows the strict audit-log pattern: path validation at construction, append-only JSONL, parent directory creation, sorted keys, finite-only Decimal/float validation, Decimal-as-string serialization, UTC datetime ISO serialization, tuple-as-array serialization, and no file creation or file modification when validation/serialization fails before opening the file.
- Package-root exports and `tests/test_init.py` cover `PaperNavLog`, `PaperNavSnapshot`, `PaperPortfolio`, `PaperPosition`, `PaperPositionMark`, `build_paper_portfolio`, and `mark_paper_nav`.
- `README.md` documents Level 1B Node 2 status and Python API in the existing concise style, and the repository tree lists the new module, test, and plan.
- TDD red/green evidence exists in the execution notes or command history for each new behavior group: position replay, executable NAV marks, JSONL persistence, package exports, and README update.
- The required pre-commit/pre-push gate passes: node-specific tests, full tests, `git diff --check`, staged `git diff --cached --check`, CodeGraph status/sync-if-stale/status, and Claude Opus 4.8 review with no unresolved Critical/Important findings.

## Part 8: Node Verification, Claude Review, Commit, Push, Handoff

**Goal:** Verify, review, commit, push, and document Level 1B Node 2.

**Files:**

- Modify: `docs/superpowers/plans/2026-06-13-level-1b-positions-nav.md`
- Stage and commit all Node 2 files after verification and Claude approval.

- [x] **Step 1: Run full verification gate before Claude code review**

Run in order:

```bash
git status --short --branch --untracked-files=all
.venv/bin/python -m pytest tests/test_positions.py tests/test_init.py -q
.venv/bin/python -m pytest -q
git diff --check
codegraph status .
```

If CodeGraph is stale:

```bash
codegraph sync .
codegraph status .
```

Expected:

- status shows only intended Node 2 files
- node-specific tests pass
- full test suite passes
- diff check has no output and exit code 0
- CodeGraph is up to date after sync if sync was needed

**Recorded result before final implementation review:** `git status --short --branch --untracked-files=all` showed only intended Node 2 files. `.venv/bin/python -m pytest tests/test_positions.py tests/test_init.py -q` passed with `54 passed`. `.venv/bin/python -m pytest -q` passed with `264 passed`. `git diff --check` was clean. `codegraph status .` reported the index up to date after the prior sync.

- [x] **Step 2: Submit implementation diff and verification output to Claude**

Run:

```bash
{
  printf '%s\n' 'Review this Level 1B Node 2 implementation for polymarket-alpha-lab.'
  printf '%s\n' 'Model requested by user: claude-opus-4-8. Effort: max.'
  printf '%s\n' 'Return one of: Proceed, Proceed with fixes, or Blocked.'
  printf '%s\n' 'Classify findings as Critical, Important, or Nice-to-have.'
  printf '%s\n' 'Critical and Important findings must be actionable and grounded in the diff.'
  printf '%s\n' ''
  printf '%s\n' 'Plan:'
  cat docs/superpowers/plans/2026-06-13-level-1b-positions-nav.md
  printf '%s\n' ''
  printf '%s\n' 'Git status:'
  git status --short --branch --untracked-files=all
  printf '%s\n' ''
  printf '%s\n' 'Diff:'
  git diff -- src/polymarket_alpha_lab/positions.py src/polymarket_alpha_lab/__init__.py tests/test_positions.py tests/test_init.py README.md docs/superpowers/plans/2026-06-13-level-1b-positions-nav.md
} | claude -p --model claude-opus-4-8 --effort max --permission-mode dontAsk --tools ""
```

Expected: Claude returns `Proceed` or `Proceed with fixes`. Resolve all Critical/Important findings and repeat this review until no Critical/Important findings remain.

**Recorded result:** First implementation review returned `Proceed with fixes` with two Important findings: metadata stability after full close/reopen and required `average_entry_price` accepting `None` in direct construction. Both were fixed with RED/GREEN tests. Second review returned `Proceed` with no Critical or Important findings.

- [ ] **Step 3: Stage and run cached diff check**

Run:

```bash
git add src/polymarket_alpha_lab/positions.py src/polymarket_alpha_lab/__init__.py tests/test_positions.py tests/test_init.py README.md docs/superpowers/plans/2026-06-13-level-1b-positions-nav.md
git diff --cached --check
```

Expected: cached diff check has no output and exit code 0.

- [ ] **Step 4: Commit and push**

Run:

```bash
git commit -m "feat: add paper positions nav"
git push
```

Expected: commit succeeds and push updates `origin/main`.

- [ ] **Step 5: Record Handoff Summary**

Append a `## Handoff Summary` section to this plan using the template below.

Then run:

```bash
git status --short --branch --untracked-files=all
```

Expected: clean working tree after commit and push, unless the Handoff Summary was intentionally appended after commit. If the Handoff Summary is appended after commit, stage it, rerun `git diff --cached --check`, commit it with the node if not already committed, and push again.

## Handoff Summary Template

Use this exact structure for the actual handoff after implementation, review, commit, and push:

```text
## Handoff Summary

- Repo status: branch, latest commit SHA, pushed/not pushed, clean/dirty state.
- Git status output: paste `git status --short --branch --untracked-files=all`.
- Verified commands:
  - `git status --short --branch --untracked-files=all`: pass/fail and notable output.
  - `.venv/bin/python -m pytest tests/test_positions.py tests/test_init.py -q`: pass/fail and test count.
  - `.venv/bin/python -m pytest -q`: pass/fail and test count.
  - `git diff --check`: pass/fail.
  - `codegraph status .`: up to date or stale.
  - `codegraph sync .`: run/not run and result.
  - follow-up `codegraph status .`: up to date or stale.
  - `git diff --cached --check`: pass/fail.
- Untracked files: list or `none`.
- Uncommitted files: list or `none`.
- Data-integrity checks: paper-only position source, duplicate `packet_id` rejection, filled-size-only exposure, buy/sell/closed-position handling, oversell rejection, executable bid-depth NAV, exact exit notional, no midpoint fallback, UTC timestamp normalization, finite Decimal validation, SHA-256 provenance, partial-exit/unfilled-size accounting, JSONL append-without-overwrite and validation-before-open behavior.
- Claude review: model `claude-opus-4-8`, effort `max`, review scope, explicit verdict, unresolved findings.
- Commit/push: commit hash, remote branch, push result.
- Next step: one concrete next action for Level 1B Node 3.
```

## Handoff Summary

- Repo status: `main...origin/main`; commit/push pending at the time this handoff entry was staged. Final pushed commit SHA is reported in the assistant final response because a commit cannot contain its own stable hash.
- Git status output before staging: `## main...origin/main`; modified tracked files: `README.md`, `src/polymarket_alpha_lab/__init__.py`, `tests/test_init.py`; untracked files: `docs/superpowers/plans/2026-06-13-level-1b-positions-nav.md`, `src/polymarket_alpha_lab/positions.py`, `tests/test_positions.py`.
- Verified commands:
  - `git status --short --branch --untracked-files=all`: passed; only intended Node 2 files were dirty/untracked.
  - `.venv/bin/python -m pytest tests/test_positions.py tests/test_init.py -q`: passed, `54 passed`.
  - `.venv/bin/python -m pytest -q`: passed, `264 passed`.
  - `git diff --check`: passed, clean.
  - `codegraph status .`: initially stale after earlier edits, later up to date after sync and final checks.
  - `codegraph sync .`: run; synced 2 changed Python files.
  - follow-up `codegraph status .`: passed, index up to date.
  - `git diff --cached --check`: pending until staging immediately after this handoff update.
- Untracked files before staging: `docs/superpowers/plans/2026-06-13-level-1b-positions-nav.md`, `src/polymarket_alpha_lab/positions.py`, `tests/test_positions.py`.
- Uncommitted files before staging: `README.md`, `src/polymarket_alpha_lab/__init__.py`, `tests/test_init.py`, plus the untracked files above.
- Data-integrity checks: covered paper-only position source, duplicate `packet_id` rejection, filled-size-only exposure, buy/sell/closed-position handling, full-close/reopen metadata stability, risk-tag canonical ordered union, oversell rejection, proportional cost-basis relief, direct accounting identities, executable bid-depth NAV, exact exit notional, no midpoint fallback, mixed-position midpoint nulling, deterministic position/mark ordering, UTC timestamp normalization, finite Decimal validation, required average-entry price validation, SHA-256 provenance, partial-exit/unfilled-size accounting, JSONL append-without-overwrite, and validation-before-open behavior.
- Claude review: model `claude-opus-4-8`, effort `max`. Initial implementation review returned `Proceed with fixes` with two Important findings; both were fixed and covered by RED/GREEN tests. Re-review returned `Proceed` with no unresolved Critical or Important findings.
- Commit/push: pending at this handoff entry; final assistant response reports commit hash, remote branch, and push result after execution.
- Next step: Level 1B Node 3 should add paper-only portfolio analytics and risk/exposure reporting from the journal/NAV artifacts without live trading or exchange reconciliation.
