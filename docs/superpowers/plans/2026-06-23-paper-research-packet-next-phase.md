# Paper Research Packet Next Phase Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add readonly quality and DB-history inspection surfaces for paper research packets, then prepare separate loop integration without creating any live trading surface.

**Architecture:** Keep packet quality and packet DB history as pure reducer/readback layers. The first two tasks are intentionally independent and can run in parallel because they touch disjoint files. CLI wiring depends on the DB-history reducer/loader and must run after Task 2 is complete.

**Tech Stack:** Python frozen dataclasses, `Decimal`, UTC `datetime`, existing DB-API store/readback patterns, pytest, CodeGraph-first navigation, OpenCode review with `zhipuai-coding-plan/glm-5.2 --variant max`.

## Global Constraints

- Phase 1 remains paper-only, report-only, readonly.
- No live trading, auth, wallet, private-key, signing, order, relayer, account, or exchange mutation code.
- No network fetches or client construction inside pure reducers.
- Decimal-only math: do not introduce floats into domain objects or JSON payloads.
- All report/config/check dataclasses must be frozen and validate exact hard flags: `paper_only=True`, `report_only=True`, `readonly=True`.
- Public reducer boundaries should reject wrong object types and subclasses when existing local patterns do.
- DB access belongs only in process/boundary layers; pure reducers stay DB-free.
- CLI DB failures must redact configured DSNs and table names before printing.
- Do not combine this batch with run-loop integration; run-loop packet generation is a later separate batch.

---

## File Structure

### Parallel Task 1: Pure Packet Quality

- Create `src/polymarket_alpha_lab/paper_research_packet_quality.py`
  - Pure reducer for freshness, population, skip pressure, and reason-code health.
- Create `tests/test_paper_research_packet_quality.py`
  - Behavior tests for status precedence, age/future timestamps, zero packet handling, skip-share thresholds, reason-code ordering, frozen dataclasses, and hard flag validation.
- Create `tests/test_paper_research_packet_quality_scope.py`
  - Scope guard proving the module is pure and has no DB/network/live execution surface.

### Parallel Task 2: Pure Packet DB History Readback

- Create `src/polymarket_alpha_lab/paper_research_packet_db_history.py`
  - Pure chronological reducer over already-loaded `PaperResearchPacketReport` objects.
- Create `src/polymarket_alpha_lab/paper_research_packet_db_history_load.py`
  - Tiny DB-API helper that loads persisted packet reports from `paper_research_packet_store` and reverses DB-descending order into chronological order before reducing.
- Create `tests/test_paper_research_packet_db_history.py`
  - Behavior tests for empty history, chronological normalization, latest report summary, duplicate timestamp count, exact type rejection, and hard flag validation.
- Create `tests/test_paper_research_packet_db_history_load.py`
  - Loader tests using monkeypatched store calls; prove reverse ordering and no direct psycopg/network/write imports.

### Dependent Task 3: Packet DB History CLI

- Modify `src/polymarket_alpha_lab/cli.py`
  - Add `paper-research-packet-db-history` command.
  - Accept only `--limit`, default `100`.
  - Read only `POLYMARKET_ALPHA_LAB_PAPER_RESEARCH_PACKET_DB_*`.
  - Print aggregate history summary and latest top packet summary.
- Create `tests/test_cli_paper_research_packet_db_history.py`
  - CLI behavior tests with injected runner/fakes and no real DB/network.
- Create `tests/test_cli_paper_research_packet_db_history_scope.py`
  - Parser and boundary scope guard.
- Modify `tests/test_cli_db_connection_cleanup.py`
  - Add the new helper only if it owns a psycopg connection.

## Task 1: Pure Paper Research Packet Quality

**Files:**
- Create: `src/polymarket_alpha_lab/paper_research_packet_quality.py`
- Create: `tests/test_paper_research_packet_quality.py`
- Create: `tests/test_paper_research_packet_quality_scope.py`

**Interfaces:**
- Consumes: `PaperResearchPacketReport` and packet rows from `src/polymarket_alpha_lab/paper_research_packet.py`.
- Produces:
  - `DEFAULT_PAPER_RESEARCH_PACKET_QUALITY_CONFIG_VERSION = "paper-research-packet-quality-v0"`
  - `PaperResearchPacketQualityConfig`
  - `PaperResearchPacketQualityCheckRow`
  - `PaperResearchPacketQualityReasonCodeCount`
  - `PaperResearchPacketQualityReport`
  - `build_paper_research_packet_quality_report(packet_report, *, config, generated_at)`

- [ ] **Step 1: Write failing behavior tests**

Add tests that construct real `PaperResearchPacketReport` instances and assert:
- fresh populated packet returns `quality_status == "pass"`;
- stale packet returns `watch` or `blocked` from freshness thresholds;
- future source packet timestamp is rejected;
- zero packet rows or included count below minimum returns `blocked`;
- skipped share over threshold returns `watch`;
- reason-code counts are ordered by `(-count, reason_code)`;
- report/check rows are frozen;
- wrong report type, report subclass, false hard flags, and config subclass are rejected.

Run:

```bash
.venv/bin/python -m pytest -q tests/test_paper_research_packet_quality.py
```

Expected before implementation: fail because module does not exist.

- [ ] **Step 2: Implement minimal pure reducer**

Implement frozen dataclasses:
- `PaperResearchPacketQualityConfig` with defaults:
  - `config_version="paper-research-packet-quality-v0"`
  - `max_source_age_seconds=21600`
  - `blocked_source_age_seconds=86400`
  - `min_included_count=1`
  - `max_skipped_share=Decimal("0.500000")`
  - hard flags all true
- `PaperResearchPacketQualityCheckRow`
  - fields: `check_name`, `status`, `observed_value`, `threshold`, `reason_codes`, hard flags
- `PaperResearchPacketQualityReasonCodeCount`
  - fields: `reason_code`, `count`, hard flags
- `PaperResearchPacketQualityReport`
  - generated/config/source timestamp fields, packet counts copied from source, `source_age_seconds`, `included_share`, `skipped_share`, check counts, `quality_status`, `check_rows`, `reason_code_counts`, hard flags.

Reducer rules:
- Normalize source and output timestamps to UTC.
- Reject source timestamps after output `generated_at`.
- Quantize ratio fields to `Decimal("0.000001")`; use `None` for zero denominators.
- Fixed checks in this order: `source_freshness`, `packet_population`, `skip_pressure`.
- Status precedence: `blocked > watch > pass`.
- Include check reason codes plus packet row reason codes in aggregate counts.

- [ ] **Step 3: Add scope test**

Scope test must assert this module imports only stdlib plus `polymarket_alpha_lab.paper_research_packet`, and does not mention DB, psycopg, client, auth, wallet, signing, order submission, exchange, or network mutation names.

- [ ] **Step 4: Verify Task 1**

Run:

```bash
.venv/bin/python -m pytest -q tests/test_paper_research_packet_quality.py tests/test_paper_research_packet_quality_scope.py
.venv/bin/python -m compileall -q src tests
git diff --check -- src/polymarket_alpha_lab/paper_research_packet_quality.py tests/test_paper_research_packet_quality.py tests/test_paper_research_packet_quality_scope.py
```

## Task 2: Pure Paper Research Packet DB History Readback

**Files:**
- Create: `src/polymarket_alpha_lab/paper_research_packet_db_history.py`
- Create: `src/polymarket_alpha_lab/paper_research_packet_db_history_load.py`
- Create: `tests/test_paper_research_packet_db_history.py`
- Create: `tests/test_paper_research_packet_db_history_load.py`

**Interfaces:**
- Consumes: `PaperResearchPacketReport`, `load_paper_research_packet_reports`.
- Produces:
  - `DEFAULT_PAPER_RESEARCH_PACKET_DB_HISTORY_CONFIG_VERSION = "paper-research-packet-db-history-v0"`
  - `PaperResearchPacketDbHistoryConfig`
  - `PaperResearchPacketDbHistoryReport`
  - `build_paper_research_packet_db_history_report(reports, *, config, generated_at)`
  - `load_paper_research_packet_db_history_report(connection, *, limit, table_name, config, generated_at)`

- [ ] **Step 1: Write failing reducer tests**

Add tests that assert:
- empty input produces a readonly empty history report with `report_count == 0`;
- input reports are sorted chronologically regardless of input order;
- first/latest generated_at fields come from chronological first/latest reports;
- latest packet count fields and latest top packet fields come from the newest report;
- duplicate `generated_at` count is computed;
- wrong report type, report subclass, false source hard flags, config subclass, and non-datetime generated_at are rejected.

Run:

```bash
.venv/bin/python -m pytest -q tests/test_paper_research_packet_db_history.py
```

Expected before implementation: fail because module does not exist.

- [ ] **Step 2: Implement pure history reducer**

Implement frozen dataclasses:
- `PaperResearchPacketDbHistoryConfig` with `config_version="paper-research-packet-db-history-v0"` and hard flags.
- `PaperResearchPacketDbHistoryReport` with:
  - `generated_at`, `config_version`, `report_count`
  - `first_report_generated_at`, `latest_report_generated_at`, `duplicate_generated_at_count`
  - latest packet config/count fields
  - latest top packet fields: rank, market slug, side, research priority, score, net edge, allocated/requested notional, reason codes
  - hard flags.

Reducer rules:
- Accept exact `PaperResearchPacketReport` objects only.
- Normalize timestamps to UTC.
- Sort reports chronologically inside reducer for defensive stability.
- Do not dedupe duplicate timestamps; count duplicates.
- Use `None` for all latest fields when there are no reports or no latest packet rows.

- [ ] **Step 3: Write failing loader tests**

Add tests that monkeypatch `paper_research_packet_db_history_load.load_paper_research_packet_reports` and assert:
- connection, limit, and table name are passed through;
- store-descending output is reversed before reducer sees it;
- empty loaded rows produce empty report;
- loader module has no direct `psycopg`, CLI, env, insert, commit, rollback, or live-client imports.

- [ ] **Step 4: Implement loader**

Implement `load_paper_research_packet_db_history_report(connection, *, limit, table_name, config, generated_at)`:
- call `load_paper_research_packet_reports(connection, limit=limit, table_name=table_name)`;
- reverse loaded reports into chronological order;
- return `build_paper_research_packet_db_history_report(...)`;
- do not commit, rollback, close, connect, read env, or print.

- [ ] **Step 5: Verify Task 2**

Run:

```bash
.venv/bin/python -m pytest -q tests/test_paper_research_packet_db_history.py tests/test_paper_research_packet_db_history_load.py
.venv/bin/python -m compileall -q src tests
git diff --check -- src/polymarket_alpha_lab/paper_research_packet_db_history.py src/polymarket_alpha_lab/paper_research_packet_db_history_load.py tests/test_paper_research_packet_db_history.py tests/test_paper_research_packet_db_history_load.py
```

## Task 3: Packet DB History CLI Command

**Files:**
- Modify: `src/polymarket_alpha_lab/cli.py`
- Create: `tests/test_cli_paper_research_packet_db_history.py`
- Create: `tests/test_cli_paper_research_packet_db_history_scope.py`
- Modify: `tests/test_cli_db_connection_cleanup.py` only if `_run_paper_research_packet_db_history` owns `psycopg.connect`.

**Interfaces:**
- Consumes Task 2 loader: `load_paper_research_packet_db_history_report`.
- Produces CLI command: `polymarket-alpha-lab paper-research-packet-db-history --limit 100`.

- [ ] **Step 1: Write failing CLI tests**

Add tests that assert:
- disabled packet DB env fails before runner/connection is used;
- enabled packet DB without DSN fails before runner/connection is used;
- `--limit 0` fails before runner/connection is used;
- injected runner receives `dsn`, `table_name`, `limit`, config object, and UTC `generated_at`;
- runner failures redact DSN and table name;
- successful summary prints aggregate counts and latest top packet line;
- output does not leak DSN, table name, question text, or payload JSON;
- parser rejects `--dsn`, `--db-dsn`, `--source-config-version`, `--packet-config-version`, `--persist`, and table/env flags.

- [ ] **Step 2: Implement CLI parser and injected helper**

Add:
- `PaperResearchPacketDbHistoryRunner = Callable[..., object]`
- `paper_research_packet_db_history_runner` keyword on `main(...)`
- parser `paper-research-packet-db-history` with only `--limit`
- command branch that calls `_run_paper_research_packet_db_history(...)` and `_print_paper_research_packet_db_history_summary(...)`
- helper validation:
  - `limit` must be positive int and not bool
  - packet DB config must be enabled
  - packet DB DSN must be present
  - redact DSN/table on runner failure

- [ ] **Step 3: Implement default psycopg load path**

If no runner is injected:
- lazy import `psycopg`;
- connect to configured DSN;
- call `load_paper_research_packet_db_history_report(connection, limit=limit, table_name=packet_db_config.table_name, config=config, generated_at=generated_at)`;
- close the connection in all cases;
- no commit is required for read-only load; if existing helper patterns commit read-only transactions, follow local convention and update cleanup tests accordingly.

- [ ] **Step 4: Add CLI scope test**

Assert:
- parser surface only exposes `--limit`;
- command branch does not accept source queue flags or generation config flags;
- helper imports only `psycopg` and the Task 2 loader;
- no live trading/auth/wallet/signing/order/exchange surfaces are added.

- [ ] **Step 5: Verify Task 3**

Run:

```bash
.venv/bin/python -m pytest -q tests/test_cli_paper_research_packet_db_history.py tests/test_cli_paper_research_packet_db_history_scope.py tests/test_cli_db_connection_cleanup.py
.venv/bin/python -m compileall -q src tests
git diff --check -- src/polymarket_alpha_lab/cli.py tests/test_cli_paper_research_packet_db_history.py tests/test_cli_paper_research_packet_db_history_scope.py tests/test_cli_db_connection_cleanup.py
```

## Final Verification And Review

Run after all tasks:

```bash
.venv/bin/python -m pytest -q tests/test_paper_research_packet_quality.py tests/test_paper_research_packet_quality_scope.py tests/test_paper_research_packet_db_history.py tests/test_paper_research_packet_db_history_load.py tests/test_cli_paper_research_packet_db_history.py tests/test_cli_paper_research_packet_db_history_scope.py tests/test_cli_db_connection_cleanup.py
.venv/bin/python -m compileall -q src tests
git diff --check
.venv/bin/python -m pytest -q
```

Then stage the diff and request OpenCode review:

```bash
git diff --cached > .superpowers/sdd/review-paper-research-packet-next-phase.diff
opencode run "Review the attached staged diff for /home/ubuntu/polymarket-alpha-lab. Scope: paper research packet next phase only. Return Critical and Important findings only. Requirements: add pure paper_research_packet_quality reducer, pure paper_research_packet_db_history reducer/load helper, and paper-research-packet-db-history CLI if present. Preserve Phase 1 paper-only/report-only/readonly boundary. No live trading/auth/wallet/signing/order/exchange/network mutation. Decimal-only domain math. Pure reducers must not import DB/env/psycopg/CLI. CLI DB failures must redact DSN/table. Do not edit files." --model zhipuai-coding-plan/glm-5.2 --variant max --file=.superpowers/sdd/review-paper-research-packet-next-phase.diff
```

If review has no Critical/Important findings:
- commit in one or more coherent commits;
- run `codegraph sync`;
- push `main`.
