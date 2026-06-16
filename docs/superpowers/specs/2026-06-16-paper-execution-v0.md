# Paper Execution v0 Design (Stage 4) — revised per codex pre-stage review

## Purpose

Close the "self-invest" half of the user's goal (Phase 1: paper execution only).
Stages 1-3 produce real `paper_review_ready` screening candidates on live data.
Stage 4 turns each into an auditable paper trade: simulate the fill against the
in-memory order book captured during the cycle, journal it as a
`PaperTradeRecord`. Deliberate fast paper lane — bypasses the
manual_review_queue/proposal_packet evidence-gate chain; trades are marker-
filterable (`strategy_type="..._screening_paper"`).

No live orders, auth, wallets/keys/credentials, exchange writes, or account
reads. Only `simulate_order_book_fill` + journal append.

## Architecture — INLINE in strategy_cycle (NOT replay from JSONL)

**Codex CRITICAL #1 fix:** the current `PaperStrategyCycleReport` JSONL does NOT
persist the per-market `NormalizedMarket`, order books, cost-aware reports, or
`RawArchiveEntry` paths — so replay-from-JSONL is infeasible without widening
that report. Instead, paper execution runs **inline inside `run_strategy_cycle`**,
where every `snapshot_ready` market's full in-memory context is available:
`NormalizedMarket`, both `OrderBookSnapshot`s, the `RawArchiveEntry` for each
book (returned by `RawArchive.write`), the cost-aware report, and the screening
candidate. No replay, no report widening, no archive re-normalization.

- `paper_execution.execute_paper_trade_from_screening(...)` is a **pure function**
  taking all that context as explicit kwargs (independently unit-testable).
- `strategy_cycle` gains an OPTIONAL `paper_execution_config:
  PaperExecutionConfig | None = None` and `paper_trade_journal_path: Path | None
  = None` on `PaperStrategyCycleConfig`. When `paper_execution_config is not
  None`, after building each `snapshot_ready` market's cost-aware report, the
  cycle calls `execute_paper_trade_from_screening` and appends executed
  `PaperTradeRecord`s to the journal at `paper_trade_journal_path`. Default
  `None` = no paper execution, Stage 1b/2/3 behavior byte-identical.
- The CLI `strategy-cycle` subcommand gains `--paper-execute` (sets the config)
  and `--paper-journal <path>` flags.

## Public API (paper_execution.py — pure in-memory leaf)

```text
__all__ = (
    "PaperExecutionConfig",
    "PaperExecutionResult",
    "PaperExecutionLog",
    "execute_paper_trade_from_screening",
)

PaperExecutionConfig (frozen dataclass):
    config_version: str                              # canonical, e.g. "paper-execution-v1"
    strategy_type: str = "book_imbalance_screening_paper"   # marker; filterable
    paper_budget_size: Decimal = 10.0000              # > 0
    sizing_limiter: str = "screening_book_depth"
    planned_exit_rule: str                           # non-empty
    account_equity_before_trade: Decimal = 10000.0000 # > 0 (from_packet_and_fill rejects nonpositive)
    thesis_template: str                             # non-empty
    invalidating_conditions_template: str             # non-empty
    rule_text: str                                   # non-empty (hashed into rule_text_hash)
    resolution_source_fallback: str = "polymarket_event_resolution"

PaperExecutionResult (frozen, paper_only=True, report_only=True):
    generated_at: datetime                           # UTC
    market_slug: str
    condition_id: str
    token_id: str
    side: str                                        # "yes" | "no" (the outcome token chosen; the ORDER is always a buy)
    fill: PaperFill | None                           # None when skipped
    record: PaperTradeRecord | None                  # None when skipped
    skipped_reason: str | None                       # None when executed
    paper_only: bool = True
    report_only: bool = True
    # INVARIANT (asserted in __post_init__): skipped_reason is None ⇔ (fill is not None and record is not None)

execute_paper_trade_from_screening(
    *,
    candidate: PaperProjectScreeningCandidate,
    cost_aware_report: PaperCostAwareEventStrategyReport,
    market: NormalizedMarket,
    book: OrderBookSnapshot,                          # the CHOSEN SIDE's token book (in-memory from the cycle)
    raw_book_archive_entry: RawArchiveEntry,          # that book's payload_path + payload_sha256
    market_raw_archive_entry: RawArchiveEntry,        # gamma markets payload_path (raw_archive_path)
    config: PaperExecutionConfig,
    generated_at: datetime,
) -> PaperExecutionResult
```

## Execution logic (revised per codex CRITICAL #2 + #3)

```text
# Gate (codex IMPORTANT): check BOTH statuses + valid_depth.
if candidate.screening_status != "screening_ready" or candidate.source_status != "paper_review_ready":
    return result(skipped_reason="not_screening_ready")
if not candidate.valid_depth:
    return result(skipped_reason="invalid_depth")

# Resolve the chosen outcome token from candidate.scoring_side (mirror snapshot_builder).
side = candidate.scoring_side                          # "yes" | "no"
yes_token, no_token = _resolve_yes_no_tokens(market)
token = yes_token if side == "yes" else no_token
if token is None:
    return result(skipped_reason="unresolvable_token")

# Codex CRITICAL #2: PaperSide = Literal["buy","sell"]; a YES or NO token trade
# is ALWAYS a BUY of that token against its ask book. Never "sell".
executable_depth = _executable_ask_depth(book)         # sum of ask levels (the buy-side walk surface)
max_executable_size = executable_depth
order_size = min(config.paper_budget_size, executable_depth)
if order_size <= 0:
    return result(skipped_reason="no_executable_depth")

order = PaperOrder(token_id=token.token_id, side="buy", size=order_size)
fill = simulate_order_book_fill(order, book)           # pure

# Derive model fields from cost_aware_report + the chosen side's SideResult.
side_result = cost_aware_report.yes_result if side == "yes" else cost_aware_report.no_result
model_probability = cost_aware_report.fair_probability_yes if side == "yes" else (ONE - cost_aware_report.fair_probability_yes)
bid = book.bids[0].price if book.bids else None
# claude IMPORTANT: screening_ready/valid_depth only constrains the ASK side, so an
# asks-only book yields bid=None. ResearchPacket requires bid + midpoint, and
# from_packet_and_fill raises on incomplete packet — which would crash the whole
# cycle (violating per-market isolation). Skip instead.
if bid is None:
    return result(skipped_reason="no_bid")
ask = side_result.executable_price
midpoint = ((bid + ask) / TWO) if (bid is not None and ask is not None) else ask
theoretical_edge = model_probability - ask
slippage_estimate = _research_slippage(book)           # midpoint-to-worst ask walk
cost_adjusted_edge = side_result.net_edge_per_share
resolution_source = market.resolution_source or config.resolution_source_fallback

# Codex CRITICAL #3: ResearchPacket field is `created_at` (NOT generated_at),
# `source_score` is REQUIRED, `rule_text_hash` must be computed. No __post_init__
# → direct instantiation is compliant.
rule_text_hash = hashlib.sha256(config.rule_text.encode("utf-8")).hexdigest()
packet = ResearchPacket(
    packet_id=f"paper-exec-{candidate.market_slug}-{side}",
    created_at=generated_at,                           # created_at, not generated_at
    condition_id=market.market.condition_id,
    token_id=token.token_id,
    market_slug=candidate.market_slug,
    question=candidate.question,
    source_score=str(candidate.screening_score),       # REQUIRED
    raw_archive_path=str(market_raw_archive_entry.payload_path),
    market_url=f"https://polymarket.com/event/{candidate.market_slug}",
    outcome_name=side.upper(),
    strategy_type=config.strategy_type,
    model_probability=model_probability,
    confidence=cost_aware_report.confidence,
    bid=bid, ask=ask, midpoint=midpoint,
    expected_entry_price=ask,
    fair_value_estimate=model_probability,
    theoretical_edge=theoretical_edge,
    spread=cost_aware_report.spread,
    slippage_estimate=slippage_estimate,
    cost_adjusted_edge=cost_adjusted_edge,
    max_executable_size=max_executable_size,
    risk_tags=(config.strategy_type,),                # non-empty
    thesis=config.thesis_template.format(reason_codes=",".join(candidate.reason_codes)),
    invalidating_conditions=config.invalidating_conditions_template,
    rule_text=config.rule_text,
    rule_text_hash=rule_text_hash,                     # computed
    resolution_source=resolution_source,
)

record = PaperTradeRecord.from_packet_and_fill(
    packet=packet, fill=fill, decision_timestamp=generated_at,
    order_book_raw_archive_path=str(raw_book_archive_entry.payload_path),
    order_book_raw_payload_sha256=raw_book_archive_entry.payload_sha256,
    account_equity_before_trade=config.account_equity_before_trade,
    sizing_limiter=config.sizing_limiter,
    planned_exit_rule=config.planned_exit_rule,
)
return result(fill=fill, record=record, skipped_reason=None)
```

## strategy_cycle integration (additive, default-off)

`PaperStrategyCycleConfig` adds (optional):
- `paper_execution_config: PaperExecutionConfig | None = None`
- `paper_trade_journal_path: Path | None = None`
Invariant: `paper_trade_journal_path is not None` IFF `paper_execution_config is not None`.

In `run_strategy_cycle`'s per-market loop, when `attempt.status == "snapshot_ready"`
AND `cycle_config.paper_execution_config is not None`: capture the archive entries
(from `archive.write` returns), and after the screening report is built, for each
candidate with `screening_status == "screening_ready"` matching this market, call
`execute_paper_trade_from_screening(...)` **wrapped in try/except** (per-market
isolation — one bad paper-execution must never abort the cycle; on exception, skip
that candidate silently or record a cycle-layer note); if `result.record is not None`,
append to `PaperTradeJournal(paper_trade_journal_path)`.

`paper_execution` added to strategy_cycle's scope `ALLOWED_IMPORT_MODULES`.
Default None → Stage 1b/2/3 behavior unchanged.

## Validation rules

- `config_version` canonical; `paper_budget_size > 0`; `account_equity_before_trade > 0`
  (codex IMPORTANT); thesis/invalidating_conditions/rule_text/planned_exit_rule/
  sizing_limiter non-empty canonical strings.
- `PaperExecutionResult`: `paper_only is True`/`report_only is True` with `is`;
  INVARIANT `skipped_reason is None ⇔ (fill is not None and record is not None)`.
- Sizing: `order_size = min(paper_budget_size, executable_ask_depth)`; `max_executable_size
  = executable_ask_depth` → from_packet_and_fill invariants hold by construction.

## Scope tests (test_paper_execution_scope.py)

- In-memory leaf (NO api). `ALLOWED_IMPORT_MODULES`: stdlib (+ `hashlib`) +
  `polymarket_alpha_lab.{domain, paper, journal, research, cost_aware_event_strategy,
  project_screening}`. NO api/strategy_cycle/normalize/archive/book_imbalance_forecast.
- **Codex IMPORTANT:** forbidden-fragment set MUST NOT include bare `"execution"`
  (module is named paper_execution). Forbid concrete live surfaces only:
  `liveexecution`, `orderplacement`, `placeorder`, `submitorder`, `wallet`,
  `privatekey`, `credential`, `broker`, `killswitch`. Mirror test_strategy_cycle_scope
  carve-out for imported PaperOrder/PaperFill/simulate_order_book_fill.
- Six canonical scope tests; README COMMENTED + package-root SKIPPED.

## Non-goals (Phase 1, enforced)

No live orders/auth/wallets/credentials/exchange writes/account reads. No
manual_review_queue/proposal_packet (bypassed). No replay-from-JSONL (inline).
No NAV aggregation.

## Risks

1. Evidence-gate bypass — mitigated by strategy_type marker.
2. strategy_cycle coupling — additive, default-off preserves prior behavior.
3. Templated thesis/rule_text — compliant (no provenance flag); marker + template auditable.

## Open questions for reviewer

1. INLINE-in-strategy_cycle (vs replay) the right call, given coupling (additive, default-off)?
2. `_research_slippage` (midpoint-to-worst ask walk) acceptable, or reuse a helper?
3. Paper-executed records summarized in PaperStrategyCycleReport (a count), or journal-only?
