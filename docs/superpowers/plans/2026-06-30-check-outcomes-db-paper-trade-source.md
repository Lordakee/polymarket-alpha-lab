# Check-Outcomes DB Paper-Trade Source Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let `check-outcomes` use local Supabase/Postgres `paper_trade_journal_records` as its paper-trade source when the paper trade journal DB env is enabled, while preserving JSONL fallback/export/replay when the env is disabled.

**Architecture:** Add an outcome-tracker source seam that accepts an injected `paper_trade_record_source` callable. `outcome_tracker.py` stays DB/env/psycopg/Supabase-free and only validates typed `PaperTradeRecord` values. `check_outcomes_paper_trade_source.py` owns typed source selection between legacy JSONL and paper-trade DB rows. `cli.py` owns the local DB env read, calls the existing paper-trade DB loader through that helper, redacts DSN/table failures, and reverses newest-first DB rows into oldest-first deterministic replay order before replay.

**Tech Stack:** Python, pytest, local Supabase/Postgres through the existing psycopg paper-trade loader, Decimal-only `PaperTradeRecord`, CodeGraph, local opencode review with model `zhipuai-coding-plan/glm-5.2` and variant `max`.

## Global Constraints

- Durable project data uses local Supabase/Postgres only; JSONL remains explicit legacy compatibility/export/replay when not migrated or when the DB env is disabled.
- No SQLite, Redis, Mongo, SQLAlchemy, hosted DB assumptions, generic DB abstraction, or new durable file storage.
- Phase 1 boundary remains: no live trading, no auth/wallet/private keys, no order signing/submission/cancellation/replacement, no exchange mutation.
- Preserve `Decimal` usage, frozen dataclasses, `paper_only is True`, `report_only`, and `readonly`.
- `outcome_tracker.py` must remain free of DB/env/psycopg/Supabase imports.
- DB source read failures must not silently fall back to JSONL; CLI error output must redact DSNs and table names.
- The existing DB paper trade loader returns newest-first records; outcome replay must receive oldest-first deterministic replay order.
- Do not overclaim migration scope: this node migrates only `check-outcomes` paper-trade source handling. Outcome tracking report persistence already has its own DB sink and is not changed by this source migration. History/performance summary, cost audit, strategy audit, and observability/trend consumers remain separate migration surfaces unless explicitly included by their own node.

## Task 1: Outcome Tracker Source Seam

**Files:**
- Modify: `src/polymarket_alpha_lab/outcome_tracker.py`
- Test: `tests/test_outcome_tracker.py`

**Interfaces:**
- Consumes: `paper_trade_record_source: object | None = None`, an optional callable returning an iterable of `PaperTradeRecord` values.
- Produces: `check_outcomes(..., paper_trade_record_source=None)` that reads injected records before falling back to the legacy JSONL journal reader.

- [x] Write failing tests proving an injected source works without a JSONL journal, and `FileNotFoundError` from the source is a hard source failure rather than a benign missing-journal skip.
- [x] Implement callable validation and source-record normalization in `outcome_tracker.py`.
- [x] Keep the legacy `_read_journal_records` missing-file behavior unchanged when no source is injected.

## Task 2: CLI Source Wiring

**Files:**
- Add: `src/polymarket_alpha_lab/check_outcomes_paper_trade_source.py`
- Modify: `src/polymarket_alpha_lab/cli.py`
- Test: `tests/test_check_outcomes_paper_trade_source.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: `from_paper_trade_journal_db_env()` and the existing `paper_trade_record_db_loader`.
- Produces: `polymarket-alpha-lab check-outcomes ...` passes `paper_trade_record_source` to the injected outcome runner when the paper trade journal DB env is enabled.

- [x] Write failing CLI tests proving env-enabled source wiring, newest-first to oldest-first deterministic replay reversal, and DSN/table redaction on DB source failure.
- [x] Implement typed source selection in `check_outcomes_paper_trade_source.py` and wire the `check-outcomes` command branch through it.
- [x] Verify default JSONL behavior still passes `paper_trade_record_source=None`.

## Task 3: Documentation And Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/strategy-recommendation-layer.md`

- [x] Document the narrow check-outcomes source migration and preserve clear wording that broader JSONL consumers remain separate surfaces.
- [x] Run focused outcome/CLI/helper tests, full suite, compileall, diff check, secret scan, CodeGraph sync, and opencode review before push.
