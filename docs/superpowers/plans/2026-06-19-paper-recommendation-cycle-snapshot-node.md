# Paper Recommendation Cycle Snapshot Node Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Document the paper recommendation cycle snapshot, DB-first Supabase/Postgres persistence, optional non-primary JSONL export/debug, and trend layer as paper-only/report-only/readonly observability over already-built cycle artifacts.

**Architecture:** Add a focused documentation page that sits after the paper recommendation pipeline and artifact-index docs. The page explains why arbitrary reducer artifacts are summarized into stable typed cycle snapshots, how Supabase/Postgres-first persistence and trend summaries fit, where JSONL may remain as export/debug only, and which verification checks future wiring must pass.

**Tech Stack:** Markdown documentation, existing paper recommendation reducer vocabulary, CodeGraph-first repository navigation.

---

## Files

- Update: `docs/paper-recommendation-cycle-snapshot.md`
- Update: `docs/superpowers/plans/2026-06-19-paper-recommendation-cycle-snapshot-node.md`

## Task 1: Documentation Scope

- [x] Use CodeGraph before grep/find/read because the repository has `.codegraph/`.
- [x] Confirm the adjacent reducer vocabulary from the pipeline, artifact index, cycle bundle, and trend context.
- [x] Keep the change docs-only and avoid source/test edits.

## Task 2: Cycle Snapshot Documentation

- [x] Explain why arbitrary supplied bundle artifacts need a stable typed cycle snapshot report.
- [x] Place snapshot construction after the pipeline report and artifact index.
- [x] Replace local JSONL-primary framing with DB-first Supabase/Postgres snapshot persistence.
- [x] Describe JSONL only as optional, non-primary export/debug evidence for already-built snapshots.
- [x] Describe trend reducers as readonly summaries over supplied snapshot or compatible cycle reports.
- [x] Require strict `paper_only`, `report_only`, and `readonly` language.
- [x] Add verification and future wiring checklists.
- [x] Note that fee and external-cost reducers must be included as artifacts before snapshot construction so future paper recommendation reports can account for spread, depth, taker fees, and external frictions.

## Task 3: Local Runtime Findings

- [x] Record Supabase CLI path as `/home/ubuntu/supabase/node_modules/.bin/supabase`.
- [x] Record self-hosted Supabase stack path as `/home/ubuntu/supabase-selfhost`.
- [x] Record exposed local container ports: Kong `8000`/`8443`, pooler `5432`/`6543`.
- [x] Record that host `psql` is not on `PATH`.
- [x] Record that Docker requires `sudo -n` for the current user.
- [x] Avoid secrets, service-role keys, database passwords, wallet material, private keys, and `.env` values.

## Phase Boundary

- [x] Keep this node paper-only/report-only/readonly.
- [x] Exclude live trading, authentication flows, wallet access, private-key access, account reads, order creation, order signing, order placement, order cancellation, and exchange-facing payloads.

## Verification

- [ ] Run `git diff --check`.
- [ ] Confirm `git status --short` shows only owned docs-path changes plus unrelated concurrent-worker files.
