# Paper Portfolio NAV v0 Design (Stage 5)

## Purpose

Give paper trades observable mark-to-market P&L. Stage 4 produces a paper-trade
journal (PaperTradeRecord JSONL). Stage 5 reads it back, builds a portfolio, fetches
current books for held tokens, and marks NAV — closing the "did I make money?"
loop. ~95 lines of new code; every downstream primitive already exists.

No live orders/auth/wallets/credentials/exchange writes. Only: read local JSONL +
read-only `get_order_book` fetch (already used by pipeline/strategy_cycle) + pure
local NAV computation.

## The one gap — a JSONL reader

`PaperTradeJournal` (journal.py:243-251) is append-only, WRITE-ONLY. No
`read`/`load`/`iter`. Census: all 29 `*Log`/`*Journal` classes are write-only.
`PaperTradeRecord` (journal.py:16-65) has 47 fields and **NO `__post_init__`** —
validation lives only in `from_packet_and_fill`. So a reader can construct
`PaperTradeRecord(**coerced_row)` directly; `build_paper_portfolio` re-validates
every record via `_validate_trade_record` (positions.py:309), so the reader only
needs type coercion (Decimal str→Decimal, ISO→datetime, list→tuple for risk_tags).

## Architecture

```text
paper_portfolio_nav.py (NEW live-layer orchestrator, ~60 lines)
  mark_paper_portfolio_nav(journal_path, *, starting_cash, client, marked_at, nav_log_path=None) -> PaperNavSnapshot
    1. records = PaperTradeJournal.read(journal_path)        # NEW reader (journal.py)
    2. portfolio = build_paper_portfolio(records, starting_cash=starting_cash)   # positions.py:291 (pure)
    3. books = { pos.token_id: normalize_order_book(client.get_order_book(token_id=pos.token_id), captured_at=marked_at)
                 for pos in portfolio.positions }            # read-only fetch per held token
    4. snapshot = mark_paper_nav(portfolio, books, marked_at=marked_at)   # positions.py:397 (pure)
    5. if nav_log_path: PaperNavLog(nav_log_path).append(snapshot)
    return snapshot

journal.py (ADDITIVE: add read() to PaperTradeJournal, ~35 lines)
  @staticmethod
  def read(path) -> tuple[PaperTradeRecord, ...]
    open text, for line: json.loads → coerce Decimal/datetime/tuple → PaperTradeRecord(**row)
```

## Public API

```text
# journal.py — additive reader (no change to append)
class PaperTradeJournal:
    @staticmethod
    def read(path: Path | str) -> tuple[PaperTradeRecord, ...]: ...

# paper_portfolio_nav.py — NEW
__all__ = ("mark_paper_portfolio_nav",)

def mark_paper_portfolio_nav(
    journal_path: Path | str,
    *,
    starting_cash: Decimal,
    client: MarketDataClient,                    # Protocol (reuse strategy_cycle's local Protocol OR api.PolymarketPublicClient)
    marked_at: datetime,                         # caller-supplied (deterministic for tests)
    nav_log_path: Path | str | None = None,
) -> PaperNavSnapshot
```

NOTE on `client`: to avoid widening `paper_portfolio_nav.py`'s scope with an `api`
import, accept a `MarketDataClient`-like Protocol (only `get_order_book(token_id=)`
needed). Define a local minimal Protocol OR import the strategy_cycle one. The CLI
constructs the concrete `PolymarketPublicClient` and injects it (Q5-style Protocol-only).

## Reader coercion (exact) — IMPORTANT: type-keyed, not value-sniffed

`journal.py` has `from __future__ import annotations`, so `dataclasses.fields().type`
is a STRING (`"Decimal"`, `"Decimal | None"`, `"tuple[str, ...]"`). The reader MUST
resolve types via `typing.get_type_hints(PaperTradeRecord)` and unwrap `X | None`
unions — NEVER string-compare `field.type`, NEVER "try Decimal(value) on anything
that parses." ~13 Decimal fields (model_probability, confidence, all research_*,
max_executable_size, account_equity_before_trade) are NOT re-validated by
`_validate_trade_record`, so a silent mis-coercion there survives into the record.
The round-trip test (write via from_packet_and_fill → append → read → __eq__) is the
non-negotiable guardrail; it must cover BOTH a fully-populated record AND a record
with optional fill_* fields set to None (so Decimal(None) crashes + value-sniff bugs
are caught).

Per `_json_ready` (journal.py:298-311): Decimal→str, datetime→ISO, tuple→list.
Reader reverses, keyed to resolved type:
- resolved type is Decimal AND value is str → `Decimal(value)` (is_finite guard)
- resolved type is datetime AND value is str → `datetime.fromisoformat(value)`
- resolved type is tuple AND value is list → `tuple(value)`
- value is None → None (pass-through; covers Optional fields)
- else: pass-through
Construct `PaperTradeRecord(**row)`. Skip blank lines. Raise ValueError on non-JSON
lines (with line number).

## CLI

Extend cli.py with `portfolio-nav --journal <path> --starting-cash <Decimal>
[--nav-log <path>]`. Constructs concrete client, calls mark_paper_portfolio_nav,
prints NAV summary (starting_cash, cash_balance, realized_pnl, exit_nav,
unrealized_pnl, position_count). runner injection for testability.

## Validation rules

- `read()`: blank-line tolerant; non-JSON → ValueError with line number; returns
  tuple (deterministic order). Empty file → empty tuple.
- `mark_paper_portfolio_nav`: starting_cash > 0 (claude IMPORTANT #2: build_paper_portfolio
  requires positive, not >= 0); isinstance guards. Empty journal
  → empty portfolio → NAV == starting_cash (no fetches performed — guard: if
  portfolio.positions is empty, skip the fetch loop).

## Scope tests

- `test_journal_scope.py` (if exists) — confirm adding `read()` staticmethod does
  NOT change `__all__` (read is a method on the class, not a new export) and the
  module's imports are unchanged (read uses only stdlib json/datetime/decimal/pathlib
  already imported). If journal.py has no scope test, skip.
- `test_paper_portfolio_nav_scope.py` (NEW) — live-layer; ALLOWED stdlib +
  `polymarket_alpha_lab.{domain, journal, positions, normalize}`. NO `api`
  (Protocol-only client). Forbidden execution fragments. Six canonical tests.

## Non-goals (Phase 1, enforced)

No live orders/auth/wallets/credentials/exchange writes/account reads. No
realized-pnl reconciliation against an exchange. No scheduler. No historical NAV
time-series (a single point-in-time mark only; PaperNavLog append is optional).

## Risks

1. **Reader coercion correctness.** A wrong coercion (e.g. float sneaking in) would
   produce a corrupt record. Mitigation: `_json_ready` guarantees Decimals are str
   in the JSONL, so `Decimal(value)` is always safe; build_paper_portfolio
   re-validates. Reader itself never produces float.
2. **mark_nav needs live books per held token.** If a market closed/resolved
   between trade and mark, get_order_book may return an empty/different book.
   mark_nav handles empty books (no_exit_depth classification). Acceptable.
3. **Protocol-only client.** Defining a local `MarketNavClient` Protocol (only
   get_order_book) vs reusing strategy_cycle's `MarketDataClient`. Recommend local
   minimal Protocol (decouples from strategy_cycle; this module only needs books).

## Open questions for reviewer

1. Add `read()` to PaperTradeJournal (colocated with the format) vs a free function
   in a new module? (Journal owns the format → method is idiomatic.)
2. Local minimal `MarketNavClient` Protocol (get_order_book only) vs reuse
   strategy_cycle's MarketDataClient? (Local = tighter scope, no api import.)
3. Should mark_paper_portfolio_nav return only PaperNavSnapshot, or also the
   PaperPortfolio (for callers wanting position detail)?
