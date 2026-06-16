# Paper Execution v0 Implementation Plan (Stage 4)

> REQUIRED SUB-SKILL: superpowers:subagent-driven-development. RED-first per module; tree green after every task.

**Goal:** Turn each `paper_review_ready` screening candidate into an auditable paper trade (simulate fill + journal) by replaying archives — no live orders, no evidence-gate dependency. Phase 1 boundary intact.

**Architecture:** One new archive-replay module `paper_execution.py` (second live-layer; imports archive/normalize/paper/journal/research + cost_aware/screening types, NO api). Bypasses manual_review_queue + proposal_packet (fast paper lane, marker `strategy_type="..._screening_paper"`). See spec `docs/superpowers/specs/2026-06-16-paper-execution-v0.md`.

**Tech Stack:** Python 3.11+, Decimal-only, frozen dataclasses, paper_only/report_only, append-only JSONL. pytest>=8.0.

## Pre-stage gate (MANDATORY before Task 1)

- [ ] 0. Claude pre-stage review of spec + this plan (claude-opus-4-8 / effort max). Fallback codex (bypass) after 2 Claude failures. **No Task 1 unless Proceed, no Critical.**

      Verdict recorded: `<fill>`

## File Structure

```text
CREATE  src/polymarket_alpha_lab/paper_execution.py
CREATE  tests/test_paper_execution.py
CREATE  tests/test_paper_execution_scope.py
MODIFY  src/polymarket_alpha_lab/cli.py                  # paper-execute subcommand (replay from cycle JSONL)
MODIFY  tests/test_cli.py                                 # paper-execute coverage
MODIFY  src/polymarket_alpha_lab/__init__.py              # import block + __all__ names
MODIFY  tests/test_init.py                                # export-assertion
MODIFY  README.md                                         # Paper Execution v0 Status + API
```

## Task 1 — paper_execution.py (archive-replay live-layer)

- [ ] 1.1 **RED: behavior tests.** Fake `PaperProjectScreeningCandidate` (screening_ready, valid_depth) + fake `PaperCostAwareEventStrategyReport` + a real `NormalizedMarket`/`OrderBookSnapshot` fixture + fake `RawArchiveEntry`. Tests: (a) happy path → `PaperExecutionResult` with `skipped_reason is None`, `record` is a valid `PaperTradeRecord`, `fill.filled_size > 0`, `record.fill_filled_size == fill.filled_size`; (b) non-paper_review_ready candidate → `skipped_reason="not_paper_review_ready"`, `record is None`; (c) invalid_depth → skip; (d) zero executable depth → skip "no_executable_depth"; (e) sizing invariant: `order_size <= max_executable_size` and equals `min(paper_budget_size, executable_depth)`; (f) `strategy_type` marker propagated to `record.strategy_type`; (g) `paper_only`/`report_only` enforced; (h) immutability + JSONL round-trip; (i) invariant `skipped_reason is None ⇔ record is not None`.
- [ ] 1.2 **RED: scope tests.** Second live-layer. `ALLOWED_IMPORT_MODULES`: stdlib + `polymarket_alpha_lab.{domain, normalize, archive, paper, journal, research, cost_aware_event_strategy, project_screening}`. NO api/strategy_cycle/book_imbalance_forecast. Forbidden execution fragments (place_order/sign/wallet/credential/broker/kill_switch/liveexecution/orderplacement). Mirror test_strategy_cycle_scope.py's carve-out for imported PaperOrder/PaperFill/simulate_order_book_fill types. Six canonical scope tests; README COMMENTED + package-root SKIPPED (`# TODO Stage-4 wiring`).
- [ ] 1.3 **GREEN:** implement per spec §"Execution logic". Clone validation helpers + Log pattern. Key helpers: `_resolve_yes_no_tokens` (mirror snapshot_builder), `_executable_depth(book, side)`, `_research_slippage(book, side)` (midpoint-to-worst walk). Build `ResearchPacket` DIRECTLY (no build_research_packet). Set `max_executable_size` from same book as fill. Focused green → full suite green.

## Task 2 — CLI paper-execute (replay from cycle JSONL)

- [ ] 2.1 `cli.py`: `paper-execute --from-cycle <path> [--journal artifacts/paper-trades.jsonl]` subcommand. Loads the `PaperStrategyCycleReport` from JSONL, for each `screening_ready` candidate re-normalizes archived gamma (by market_slug) + book (by token_id) via `RawArchive.read` + `normalize_gamma_market`/`normalize_order_book`, matches the cost-aware report by market_slug, calls `execute_paper_trade_from_screening`, appends executed records to `PaperTradeJournal`. runner injection for testability.
- [ ] 2.2 `test_cli.py`: paper-execute test with a fake runner + fixture cycle report; assert exit 0 + journal appended.

## Task 3 — Wiring

- [ ] 3.1 `__init__.py` import block + 4 `__all__` names. `test_init.py` export-assertion + imports. README `## Paper Execution v0 Status` + `## Paper Execution v0 Python API` (boundary shorthand: paper-only, report-only, no fetch (replays archives), no auth, no wallet, no order (simulate only), no rank, no recommend, no financial advice). Re-enable scope README + package-root tests.

## Task 4 — Full verification

- [ ] 4.1 `.venv/bin/python -m pytest -q` green (was 1041; record new). `git diff --check` clean. Secret scan no matches. `codegraph sync && status` up-to-date.

## Post-stage gate (MANDATORY)

- [ ] 5. Claude post-stage review (primary; codex fallback after 2 failures). Verify Phase 1 boundary (simulate+journal only, no order placement), evidence-gate bypass is marker-filterable, sizing invariant holds, ResearchPacket auto-fields are compliant non-empty strings, no float, scope test sound. **No next stage unless Proceed, no Critical.**

## Commit (ONLY when user explicitly authorizes)

- [ ] 6. `feat: add paper execution v0`. Do NOT push.
