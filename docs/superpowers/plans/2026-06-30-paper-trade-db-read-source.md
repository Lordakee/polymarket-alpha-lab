# Paper Trade DB Read Source Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first local Supabase/Postgres-backed paper trade read source by migrating one-shot `portfolio-nav` CLI input from legacy JSONL to DB when the paper trade journal DB is enabled.

**Execution status:** Implemented in commit `b03fe72`. This node migrates only the one-shot `portfolio-nav` CLI paper-trade source read to local Supabase/Postgres when the paper trade journal DB env is enabled. It does not migrate continuous-run NAV source reads, outcome tracking, history/performance summary, cost audit, strategy audit, or observability trend consumers.

**Architecture:** Keep the NAV domain module independent of psycopg and environment reads. Reuse the existing record-based NAV composition seam, then let `cli.py` choose between legacy JSONL and the existing paper trade journal DB loader. DB rows are loaded newest-first by the existing store, so the CLI reverses them into append/chronological order before NAV replay.

**Tech Stack:** Python, pytest, local Supabase/Postgres via the existing psycopg adapter, Decimal-only paper records, frozen dataclasses.

## Global Constraints

- Durable project data uses local Supabase/Postgres only; JSONL remains explicit legacy compatibility/export/replay where not yet migrated.
- No SQLite, Redis, Mongo, SQLAlchemy, hosted DB assumptions, generic DB abstraction, or new file-backed durable storage.
- Phase 1 boundary remains: no live trading, no auth/wallet/private keys, no order signing/submission/cancellation/replacement, no exchange mutation.
- Preserve `Decimal` usage, frozen dataclasses, `paper_only is True`, and paper-only/report-only/read-only behavior.
- DB source read failures must not silently fall back to JSONL; redact DSNs and table names in CLI error output.
- Do not overclaim migration scope: this node migrates only one-shot `portfolio-nav` CLI source reads. Runner NAV, outcome tracking, cost audit, strategy audit, history, and observability trend consumers remain separate migration surfaces.

---

### Task 1: Record-Based NAV Seam Coverage

**Files:**
- Modify: `src/polymarket_alpha_lab/paper_portfolio_nav.py`
- Test: `tests/test_paper_portfolio_nav.py`

**Interfaces:**
- Consumes: `tuple[PaperTradeRecord, ...]`, `MarketNavClient`, existing `_mark_paper_portfolio_nav_from_records(...)`
- Produces: coverage for the existing `_mark_paper_portfolio_nav_from_records(records, *, starting_cash, client, marked_at, nav_log_path=None, nav_snapshot_sink=None) -> PaperNavSnapshot` seam

- [x] **Step 1: Write failing tests**

Add tests proving a supplied record tuple can mark NAV without a JSONL path, and invalid supplied records fail before public order-book fetches.

- [x] **Step 2: Run focused tests and confirm RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_paper_portfolio_nav.py::test_marks_supplied_trade_records_without_jsonl tests/test_paper_portfolio_nav.py::test_supplied_trade_records_validate_before_fetch
```

Expected: fail before the seam coverage exists.

- [x] **Step 3: Keep the existing minimal seam**

Do not add DB config or psycopg imports in the NAV module. Keep the package public API unchanged; CLI can inject the existing record seam without widening `__all__`.

- [x] **Step 4: Run focused tests and confirm GREEN**

Run the same focused tests and then all NAV tests:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_paper_portfolio_nav.py
```

### Task 2: `portfolio-nav` DB Source CLI Wiring

**Files:**
- Modify: `src/polymarket_alpha_lab/cli.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: `from_paper_trade_journal_db_env()`, `load_paper_trade_records_with_psycopg(dsn=..., table_name=...)`
- Produces: `main(..., nav_records_runner=_mark_paper_portfolio_nav_from_records, paper_trade_record_db_loader=load_paper_trade_records_with_psycopg, ...)`

- [x] **Step 1: Write failing tests**

Add CLI tests proving:

```python
POLYMARKET_ALPHA_LAB_PAPER_TRADE_JOURNAL_DB_ENABLED=true
```

makes `portfolio-nav` load source trades from the paper trade journal DB, reverses newest-first records into append order, bypasses the legacy `journal_path` runner, preserves NAV snapshot sink wiring, and redacts source DB DSN/table on read failures.

- [x] **Step 2: Run focused tests and confirm RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_cli.py::test_portfolio_nav_cli_uses_paper_trade_db_source_when_enabled tests/test_cli.py::test_portfolio_nav_cli_redacts_dsn_and_table_when_paper_trade_db_source_fails
```

Expected: fail because `main(...)` does not yet accept the injected DB loader/record NAV runner and the CLI branch still always passes `journal_path`.

- [x] **Step 3: Implement CLI DB source branch**

In the `portfolio-nav` branch:

```python
paper_trade_db_config = from_paper_trade_journal_db_env()
if paper_trade_db_config.enabled:
    loaded_records = paper_trade_record_db_loader(
        dsn=paper_trade_db_config.dsn,
        table_name=paper_trade_db_config.table_name,
    )
    records = tuple(reversed(loaded_records))
    snapshot = nav_records_runner(records=records, ...)
else:
    snapshot = nav_runner(journal_path=args.journal, ...)
```

Keep client construction after successful DB source load. Use the existing DB redaction helpers and include table-name redaction.

- [x] **Step 4: Run focused tests and confirm GREEN**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_cli.py::test_portfolio_nav_cli_builds_nav_call_and_prints_summary tests/test_cli.py::test_portfolio_nav_cli_uses_paper_trade_db_source_when_enabled tests/test_cli.py::test_portfolio_nav_cli_redacts_dsn_and_table_when_paper_trade_db_source_fails
```

### Task 3: Documentation and Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/strategy-recommendation-layer.md`
- Modify: `.superpowers/sdd/progress.md`

**Interfaces:**
- Consumes: verified implementation from Tasks 1 and 2
- Produces: exact migration-scope documentation and progress ledger entry

- [x] **Step 1: Update docs**

State that one-shot `portfolio-nav` can read paper trades from local Supabase/Postgres when `POLYMARKET_ALPHA_LAB_PAPER_TRADE_JOURNAL_DB_ENABLED=true`, while runner NAV, outcome tracking, history, cost audit, strategy audit, and observability trend consumers remain JSONL/legacy until separate nodes.

- Document DB source failure as fail-closed: no silent fallback to JSONL when DB env is enabled; DSN/table details must be redacted.
- Do not claim `--journal` is optional; it remains the legacy JSONL source when DB env is disabled.

- [x] **Step 2: Verify**

Run focused suites, full suite, compileall, diff check, secret scan, CodeGraph sync, opencode review, then push the verified node.
