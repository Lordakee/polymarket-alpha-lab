# Paper Portfolio NAV v0 Implementation Plan (Stage 5)

**Goal:** Read paper-trade journal → build portfolio → fetch live books → mark NAV. ~95 lines. Phase 1 read-only.

**Architecture:** Additive `PaperTradeJournal.read()` (journal.py) + new `paper_portfolio_nav.py` orchestrator + CLI. See spec.

## Pre-stage gate
- [ ] 0. Claude pre-stage review (claude-opus-4-8 / effort max). Fallback codex after 2 failures.

## Tasks
- [ ] 1. `journal.py`: add `PaperTradeJournal.read(path) -> tuple[PaperTradeRecord,...]` staticmethod (JSONL → coerce Decimal/datetime/tuple → PaperTradeRecord(**row); blank-line tolerant; non-JSON → ValueError). RED test (write via append, read back, assert equal) + GREEN.
- [ ] 2. `paper_portfolio_nav.py` (NEW live-layer): `mark_paper_portfolio_nav(journal_path, *, starting_cash, client, marked_at, nav_log_path=None) -> PaperNavSnapshot`. Local `MarketNavClient` Protocol (get_order_book only; NO api import). RED+GREEN (fake client; empty journal→NAV==starting_cash no fetch; multi-position fetch fan-out; nav_log append).
- [ ] 3. `test_paper_portfolio_nav_scope.py` (NEW): ALLOWED stdlib + {domain,journal,positions,normalize}; NO api; forbidden execution fragments; 6 canonical tests.
- [ ] 4. CLI `portfolio-nav --journal --starting-cash [--nav-log]` + test_cli coverage.
- [ ] 5. Wiring: `__init__.py` export mark_paper_portfolio_nav + test_init + README + scope README/package-root unskip.
- [ ] 6. Full verify: pytest green, git diff clean, secret scan, codegraph sync.

## Post-stage gate
- [ ] 7. Claude post-stage (Phase 1 boundary; reader coercion; no float; Protocol-only). Fallback codex.

## Commit (user-authorized)
- [ ] 8. `feat: add paper portfolio nav v0`.
