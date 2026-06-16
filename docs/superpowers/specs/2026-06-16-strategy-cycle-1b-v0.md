# Strategy Cycle v0 — Stage 1b Design (orchestrator + CLI)

## Purpose

Stage 1b closes the strategy-cycle pipeline by adding the **live-layer
orchestrator** (`strategy_cycle.py`) and a `strategy-cycle` CLI subcommand.
Stage 1a delivered the two paper-only leaf modules (`forecast_provider`,
`cost_aware_snapshot_builder`); Stage 1b wires them to live Polymarket data,
produces a deterministic `PaperProjectScreeningReport` research queue
end-to-end, and persists a paper-only audit envelope. This is the increment
that converts the project from a library into a runnable system (on demand; no
scheduler in v0).

It does not place orders, authenticate, handle wallets/private keys/credentials,
sign messages, use relayers, read account/position/balance/fill state, or
perform any exchange write. The orchestrator fetches only the same read-only
public surfaces `scan` already uses (Gamma `/markets`, CLOB `/book`).

## Relationship to Stage 1a spec

The Stage 1a spec (`2026-06-16-strategy-cycle-v0.md`) Module 3 described an
orchestrator that reused `pipeline.run_market_scan`. The pre-stage review
blocked that on Critical C1: `ScoredCandidate` is flat
(`condition_id, token_id, market_slug, question, total_score, raw_archive_path`),
carries no `NormalizedMarket`/`.tokens`, and `run_market_scan` discards the
`NormalizedMarket` it builds internally. The orchestrator therefore cannot
source the `NormalizedMarket` + YES/NO token books + `rules_text`/
`resolution_source`/`end_time` the snapshot builder requires.

Stage 1a shipped the two leaf modules (they have zero dependency on the broken
contract). **This Stage 1b spec supersedes the Stage 1a spec's Module 3 / CLI
sections.** Stage 1b resolves C1 with approach **(b2)** below.

## C1 resolution — approach (b2): self-contained scan

Two options were on the table:
- (a) extend `pipeline.run_market_scan` to retain `NormalizedMarket` (or add
  `run_market_scan_detailed`) — modifies codex's `pipeline.py` + its tests.
- (b) have `strategy_cycle` run its own scan.

**Chosen: (b2) — `strategy_cycle` is self-contained.** It calls
`client.list_markets` → `normalize_gamma_market` (retaining `NormalizedMarket`)
→ optional `score_market` pre-filter → per-market `client.get_order_book` × 2
→ `normalize_order_book` × 2 → `build_paper_naive_forecast` →
`build_paper_cost_aware_event_market_snapshot` →
`build_paper_cost_aware_event_strategy_report` → batch →
`build_paper_project_screening_report`.

Rationale:
- **Zero regression risk** — `pipeline.py` (codex's) is untouched.
- **No information loss** — `NormalizedMarket` + both token books are retained
  end-to-end, exactly what the snapshot builder needs.
- **Reuses stable modules** — `api`, `normalize`, `archive`, `scoring`,
  Stage 1a leaves, `cost_aware_event_strategy`, `project_screening`.
- **Acceptable duplication** — the small `list_markets → normalize` loop is
  repeated, but the orchestrator's need (full `NormalizedMarket` + paired books)
  is genuinely different from `scan`'s flat per-token output.

Trade-off acknowledged: `strategy_cycle` does not benefit from future
`run_market_scan` improvements (e.g. pagination, better archiving). If/when
`pipeline` grows a `NormalizedMarket`-retaining API, `strategy_cycle` can
migrate to it; until then it owns its scan loop.

## Architecture

```text
LIVE ORCHESTRATION LAYER  (may import normalize / archive / scoring / domain +
                           the Stage 1a leaves + cost_aware + screening.
                           Protocol-only: does NOT import api — cli.py injects
                           the concrete client; Q5 resolution.)
  ┌──────────────────────────────────────────────────────────────────────┐
  │ strategy_cycle.py                                                    │
  │   run_strategy_cycle(*, client, scan_config, cycle_config,           │
  │                       generated_at=None) -> PaperStrategyCycleReport │
  │     1. client.list_markets(active=True, closed=False, limit=...)     │
  │        archive raw payload (RawArchive) for reproducibility          │
  │     2. for each raw market:                                          │
  │          normalized = normalize_gamma_market(raw, captured_at)       │
  │          (optional) scores = score_market(normalized, {}); pre-filter│
  │          truncate to cycle_config.max_markets_per_cycle              │
  │     3. for each retained NormalizedMarket (try/except per market):   │
  │          resolve YES/NO tokens (binary gate)                         │
  │          yes_book_raw = client.get_order_book(token_id=yes_token_id) │
  │          no_book_raw  = client.get_order_book(token_id=no_token_id)  │
  │          archive both raw books                                      │
  │          yes_book = normalize_order_book(yes_book_raw, captured_at)  │
  │          no_book  = normalize_order_book(no_book_raw,  captured_at)  │
  │          forecast = build_paper_naive_forecast(normalized, yes_book, │
  │                                                no_book, ...)         │
  │          attempt  = build_paper_cost_aware_event_market_snapshot(    │
  │                       normalized, yes_book, no_book, forecast, ...)  │
  │          if attempt.status == "snapshot_ready":                      │
  │              report = build_paper_cost_aware_event_strategy_report(  │
  │                           attempt.snapshot, ...)                     │
  │              collect report                                          │
  │          else: record attempt.status in blocked_counts               │
  │     4. screening = build_paper_project_screening_report(             │
  │                      tuple(collected), ...) if collected else None   │
  │     5. return PaperStrategyCycleReport(...)                         │
  └──────────────────────────────────────────────────────────────────────┘
```

The orchestrator is a **live layer** (it imports `api`/`normalize`/`archive`/
`scoring` and performs network reads), but its **output** `PaperStrategyCycleReport`
is paper-only/report-only: it is a research audit envelope, not a trade
instruction. `paper_only is True` / `report_only is True` are hard-enforced on
the report with `is`.

## Public API

```text
__all__ = (
    "PaperStrategyCycleConfig",
    "PaperStrategyCycleReport",
    "PaperStrategyCycleLog",
    "run_strategy_cycle",
)

PaperStrategyCycleConfig (frozen dataclass):
    config_version: str                                 # canonical, e.g. "strategy-cycle-v1"
    forecast_config: PaperForecastConfig
    snapshot_config: PaperCostAwareSnapshotConfig
    strategy_config: PaperCostAwareEventStrategyConfig
    screening_config: PaperProjectScreeningConfig
    cost_assumptions: PaperCostAwareEventCostAssumptions
    max_markets_per_cycle: int = 50                     # positive, bool rejected
    prefilter_by_score: bool = True                     # use score_market to rank then truncate

PaperStrategyCycleReport (frozen dataclass, paper_only=True, report_only=True):
    generated_at: datetime                              # UTC-normalized
    config_version: str
    scan_market_count: int                              # raw markets returned by list_markets
    considered_count: int                               # retained markets that entered step 3 (binary OR not;
                                                        # non-binary recorded as blocked_non_binary_market)
    snapshot_ready_count: int                           # attempts with status snapshot_ready
    cost_aware_report_count: int                        # == snapshot_ready_count
    blocked_counts: tuple[tuple[str, int], ...]         # deterministic: sorted by status; covers
                                                        #   blocked_non_binary_market,
                                                        #   blocked_unresolvable_outcome_pair,
                                                        #   blocked_book_token_mismatch,
                                                        #   blocked_fetch_error (cycle-layer),
                                                        #   + any non-ready snapshot_builder status
    screening_report: PaperProjectScreeningReport | None   # None when cost_aware_report_count == 0
    paper_only: bool = True
    report_only: bool = True

PaperStrategyCycleLog (frozen dataclass):
    path: Path | str
    def append(self, report: PaperStrategyCycleReport) -> None   # append-only JSONL, allow_nan=False, sort_keys=True

run_strategy_cycle(
    *,
    client: MarketDataClient,                  # a local Protocol defined in THIS module (Protocol-only;
                                               # strategy_cycle.py does NOT import api — cli.py injects
                                               # the concrete client; Q5 resolution)
    scan_config: MarketScanConfig,             # archive_root, limit, etc. (reused for list_markets + archive)
    cycle_config: PaperStrategyCycleConfig,
    generated_at: datetime | None = None,      # default: datetime.now(UTC)
) -> PaperStrategyCycleReport
```

## Orchestration logic (precise)

```text
generated_at = _as_utc(generated_at) if generated_at is not None else datetime.now(UTC).astimezone(UTC)

# 1. Fetch + archive market list
archive = RawArchive(scan_config.archive_root)
markets_payload = client.list_markets(active=True, closed=False, limit=scan_config.limit)
archive.write(source="gamma_markets", name="markets", payload=markets_payload, captured_at=generated_at)

# 2. Normalize + (optional) score-prefilter + truncate
normalized = []
for raw in _as_list(markets_payload):
    try:
        nm = normalize_gamma_market(raw, captured_at=generated_at)
    except Exception:
        continue                      # malformed market — skip (not counted as blocked; logged via archive)
    normalized.append(nm)
# _total_score: aggregate each token's MarketScore into one comparable value,
# mirroring pipeline.py's ScoredCandidate.total_score derivation (max over tokens).
# Deterministic ordering: stable two-pass sort — first by (condition_id, market_slug)
# ascending, then by score descending (stable preserves tie-break for equal scores;
# placeholder weights tie heavily so the tie-break matters).
if cycle_config.prefilter_by_score:
    base = sorted(normalized, key=lambda nm: (nm.market.condition_id, nm.market.market_slug))
    scored = sorted(base, key=lambda nm: _total_score(score_market(nm, {})), reverse=True)
else:
    scored = sorted(normalized, key=lambda nm: (nm.market.condition_id, nm.market.market_slug))
retained = scored[: cycle_config.max_markets_per_cycle]

# 3. Per-market strategy evaluation (try/except isolates failures)
attempts = []
collected_reports = []
for nm in retained:
    try:
        if len(nm.tokens) != 2:
            # Non-binary: record via cycle-layer helper (do NOT call the builder with fabricated books).
            attempts.append(_cycle_blocked(nm, "blocked_non_binary_market", generated_at,
                                           cycle_config.snapshot_config.config_version)); continue
        # _resolve_token_ids MUST mirror cost_aware_snapshot_builder's YES/NO resolution verbatim
        # (YES_NAMES={yes,true,long}/NO_NAMES={no,false,short}, then outcome_index 0/1 fallback) —
        # divergence triggers blocked_book_token_mismatch on every market.
        yes_token_id, no_token_id = _resolve_token_ids(nm)
        yes_book_raw = client.get_order_book(token_id=yes_token_id)
        no_book_raw  = client.get_order_book(token_id=no_token_id)
        # C2b: token-unique archive names (pipeline.py precedent: name=f"book-{token_id}");
        # fixed names would collide across markets within one cycle (constant timestamp) and
        # destroy the reproducibility envelope.
        archive.write(source="clob_book", name=f"book-{yes_token_id}", payload=yes_book_raw, captured_at=generated_at)
        archive.write(source="clob_book", name=f"book-{no_token_id}",  payload=no_book_raw,  captured_at=generated_at)
        yes_book = normalize_order_book(yes_book_raw, captured_at=generated_at)
        no_book  = normalize_order_book(no_book_raw,  captured_at=generated_at)
        forecast = build_paper_naive_forecast(nm, yes_book, no_book,
                                              config=cycle_config.forecast_config, generated_at=generated_at)
        attempt = build_paper_cost_aware_event_market_snapshot(
            nm, yes_book, no_book, forecast,
            config=cycle_config.snapshot_config, generated_at=generated_at)
    except Exception:
        attempts.append(_cycle_blocked("blocked_fetch_error", nm)); continue
    attempts.append(attempt)
    if attempt.status == "snapshot_ready":
        report = build_paper_cost_aware_event_strategy_report(
            attempt.snapshot, cost_assumptions=cycle_config.cost_assumptions,
            config=cycle_config.strategy_config, generated_at=generated_at)
        collected_reports.append(report)

# 4. Screening aggregate (C1b: project_screening._collect_source_reports raises on
#    duplicate market_slug; dedupe keeps first occurrence to preserve MANDATORY
#    per-market isolation at the aggregation boundary.)
deduped = _dedupe_by_market_slug(collected_reports)
screening = (build_paper_project_screening_report(
                reports=tuple(deduped),
                config=cycle_config.screening_config, generated_at=generated_at)
             if deduped else None)

# 5. Assemble + validate invariants
return PaperStrategyCycleReport(
    scan_market_count=len(normalized),       # markets successfully normalized
    considered_count=len(retained),            # all retained markets entering step 3 (binary OR not)
    snapshot_ready_count=<count status snapshot_ready>,
    cost_aware_report_count=len(collected_reports),
    blocked_counts=_deterministic_blocked_counts(attempts),
    screening_report=screening, ...)
```

**Per-market isolation (MANDATORY):** every market's fetch/normalize/snapshot
path is wrapped in try/except. A single bad market (network blip, malformed
payload, crossed book raising in `PaperCostAwareEventMarketSnapshot.__post_init__`,
etc.) is recorded as `blocked_fetch_error` (cycle-layer) or the snapshot
builder's own `blocked_*` status, and the cycle continues. This absorbs Stage
1a post-stage MINOR #1 (crossed-book/out-of-domain-price raises) without
needing a new snapshot-builder status.

## CLI

Extend `cli.py` with a `strategy-cycle` subcommand mirroring `scan`'s shape:
cli.py constructs the concrete `PolymarketPublicClient` and injects it (strategy_cycle.py is Protocol-only — Q5); same scan-config flags (`--limit`,
`--archive-root`, `--output`); plus `--max-markets`, `--prefilter/--no-prefilter`.
Output: `artifacts/strategy-cycle-<timestamp>.jsonl` (one
`PaperStrategyCycleReport`) + human stdout summary (scan/considered/ready/
blocked counts + top-5 screening queue items). No daemon/scheduler in v0.

## Validation rules

- All nested config objects validated by their own `__post_init__`.
- `max_markets_per_cycle` positive int (bool rejected).
- Count invariants in `PaperStrategyCycleReport.__post_init__`:
  - `snapshot_ready_count <= considered_count <= scan_market_count`
  - `cost_aware_report_count == snapshot_ready_count`
  - `screening_report is None` ⇔ `cost_aware_report_count == 0`
  - `sum of blocked_counts values + snapshot_ready_count == considered_count`
- `blocked_counts` sorted by status (deterministic).
- `paper_only is True` and `report_only is True` asserted with `is`.
- `Decimal`-only for all numeric report fields (counts are `int`, bool rejected).
- `_json_ready` rejects `float`; nested `screening_report` serializes via recursion.

## Scope tests (test_strategy_cycle_scope.py) — FIRST live-layer scope test

`pipeline.py` has NO scope test today (verified). This is the first scope
contract for a live-layer module — precedent-setting.

- `ALLOWED_IMPORT_MODULES`: stdlib + `polymarket_alpha_lab.{domain, normalize,
  archive, scoring, forecast_provider, cost_aware_snapshot_builder,
  cost_aware_event_strategy, project_screening}`. (Q5 resolution: `api` is NOT
  imported — strategy_cycle.py depends only on a local `MarketDataClient`
  Protocol defined in this module; `cli.py` constructs the concrete
  `PolymarketPublicClient` and injects it. This removes the `api` widening
  entirely and sets a tighter live-layer precedent than `pipeline.py`'s own
  imports. `pipeline` is also NOT imported — strategy_cycle is self-contained
  per approach b2.)
- `FORBIDDEN_IMPORT_PREFIXES`: raw `os`, `subprocess`, `socket`, `ssl`,
  `sqlite3`, `importlib`, `urllib*`, network/crypto/web/SDK packages
  (`requests`, `httpx`, `aiohttp`, `web3`, `eth_*`, `py_clob_client`,
  non-internal `polymarket*`), scraping/browser.
- `FORBIDDEN_NAME_FRAGMENTS` / `FORBIDDEN_PUBLIC_EXPORT_FRAGMENTS`: the usual
  set PLUS execution surfaces — `place_order`, `submit_order`, `sign`,
  `wallet`, `private_key`, `credential`, `broker`, `kill_switch`,
  `liveexecution`, `orderplacement` — must not appear in any defined
  identifier or public export.
- The 6 canonical scope tests + a module-docstring note recording this as the
  first live-layer scope contract.

## Non-goals (Phase 1 boundary, enforced)

- No live order placement/cancellation/signing/routing.
- No authentication, API keys, wallets, private keys, relayers.
- No account/position/balance/fill/history reads.
- No broker interface, kill switch, `HumanApprovalBroker`, `LiveBroker`.
- No paper-trade execution loop (approved-proposal → `simulate_order_book_fill`
  → journal) — that is a later stage.
- No scheduler/daemon/cron inside the package (external cron is the user's choice).
- No manual-execution-journal importer.
- No real forecast model — Stage 1a's naive baseline is still the only
  probability source; `basis="yes_ask_naive_v0"` makes every report auditable
  as a placeholder.

## Risks

1. **Naive forecast → mostly defer/blocked queue.** Under the naive model
   (`fair_probability_yes == yes_ask`), YES gross edge ≈ 0, so cost-aware emits
   `no_paper_edge`/`blocked_by_*` for most markets; the screening queue
   populates defer/blocked, watch/research_ready essentially unreachable
   (Stage 1a post-stage claude finding I1). EXPECTED — the cycle proves the
   pipeline runs; meaningful edges arrive only when a real forecast model
   replaces the naive baseline.
2. **Live CLOB rate limit / partial fetch failure.** Up to
   `max_markets_per_cycle` × 2 CLOB calls per cycle (100 calls for 50 markets).
   Per-market try/except isolates failures; cycle completes with whatever
   succeeded. No retry/backoff in v0.
3. **First live-layer scope test is precedent.** Documented in the test
   docstring; `api` import is a widening beyond `pipeline.py`'s precedent and
   is justified on its own terms.
4. **Self-contained scan duplication.** `list_markets → normalize` is repeated
   from `pipeline.run_market_scan`. Acceptable per approach b2 rationale;
   migrate if `pipeline` grows a `NormalizedMarket`-retaining API.
5. **Raw payload archive grows unbounded.** `RawArchive.write` per cycle
   appends JSON without rotation. v0 acceptable; operational hardening is a
   later stage.

## Open questions for the reviewer (claude code pre-stage)

1. **(b2) vs (a):** Is the self-contained scan the right call over extending
   `pipeline.run_market_scan`? The trade-off is zero-regression vs DRY. If the
   reviewer prefers (a), the plan must add `MODIFY pipeline.py` + its tests.
2. **Live-layer `paper_only`/`report_only`:** The orchestrator performs live
   network reads but its OUTPUT report is paper-only/report-only. Is asserting
   `paper_only is True`/`report_only is True` on `PaperStrategyCycleReport`
   correct (the report carries no execution semantics), or misleading (the
   module touched the network)?
3. **Score prefilter default:** `prefilter_by_score=True` ranks markets by
   `score_market` then truncates to `max_markets_per_cycle`. The default
   `score_market` has placeholder weights (time_structure=50 etc., per the
   Stage 1a review). Is prefiltering by a placeholder scorer worse than no
   prefilter (FIFO)?
4. **`scan_market_count` semantics:** Should it count raw markets returned by
   `list_markets` (before normalize) or successfully-normalized markets? The
   spec currently counts normalized; malformed markets that fail normalize are
   silently skipped (archived but not counted). Acceptable?
5. **CLI client construction:** The CLI constructs a concrete
   `PolymarketPublicClient`. Should `strategy_cycle.py` import `api` at all, or
   should the client be constructed in `cli.py` and passed in (keeping
   `strategy_cycle.py` depending only on the `MarketDataClient` Protocol)? The
   latter would remove `api` from `strategy_cycle.py`'s imports and from the
   scope test's allowed set — narrowing the live surface.
