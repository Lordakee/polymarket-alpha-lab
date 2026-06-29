# Local Supabase-Only Persistence Hardening (2026-06-29)

## Binding Rules

- All durable project data must use local Supabase/Postgres on this host.
- Do not add new SQLite, JSONL, file-backed database substitutes, Redis, Mongo,
  SQLAlchemy, generic database abstraction layers, or hosted remote database
  assumptions.
- Existing JSONL/file-backed journals, logs, archives, and local input helpers
  are legacy compatibility surfaces. Do not expand them.
- Phase 1 remains paper-only/read-only: no live trading, account auth, wallets,
  private keys, order signing, order submission, cancellation, replacement, or
  exchange mutation.
- All DB DSN process boundaries must validate local-only DSNs with
  `polymarket_alpha_lab.supabase_local_dsn.validate_local_postgres_dsn`.

## Current Baseline

As of `9c33ea6`, the shared local DSN validator is in place and used by:

- `supabase_paper_autonomous_allocation_proposal_config.py`
- `supabase_paper_autonomous_readiness_digest_config.py`
- `supabase_paper_autonomous_readiness_gate_config.py`
- selected CLI probability-selection/readiness-digest agreement DB checks

Read-only audits found 44 DSN-bearing `supabase*_config.py` modules. Only the
three listed config modules currently use the shared local DSN validator; the
remaining modules normalize DSN shape but do not reject remote/non-local hosts.

The main durable file-backed defaults still to migrate are:

- raw market/book archives under `data/raw`
- strategy cycle JSONL logs under `artifacts/strategy-cycle.jsonl`
- paper trade JSONL journals under `artifacts/paper-trades.jsonl`
- NAV snapshot JSONL logs when enabled
- outcome/audit/recommendation report JSONL compatibility logs
- local JSON/JSONL input loaders for recommendation/risk-budget flows

## Parallel Batch Plan

### Batch A: Supabase Config DSN Validation

Goal: migrate DSN-bearing config modules to the shared local-only validator.

Implementation pattern per module:

1. Import `validate_local_postgres_dsn`.
2. After `_normalize_optional_dsn`, call the validator when `self.dsn is not None`.
3. Pass the module's own `*_DB_DSN_ENV_VAR` as `env_var_name`.
4. Preserve existing "enabled requires DSN" behavior.
5. Update direct config tests to use local DSNs.
6. Add reject-remote/no-secret-echo coverage where missing.
7. Run the module's direct tests plus `tests/test_supabase_local_dsn.py`.

Recommended independent groups:

- A1: `supabase_cycle_snapshot_config.py` and
  `tests/test_supabase_cycle_snapshot_config.py`.
- A2: `supabase_paper_probability_recommendation_queue_config.py`,
  `supabase_paper_recommendation_risk_budget_config.py`, and
  `tests/test_supabase_paper_recommendation_report_config.py`.
- A3: `supabase_paper_recommendation_consistency_config.py`,
  `supabase_paper_recommendation_health_config.py`,
  `supabase_paper_recommendation_quality_history_config.py`,
  `supabase_paper_recommendation_quality_summary_config.py`, and their direct
  tests.
- A4: `supabase_paper_recommendation_reason_trend_config.py`,
  `supabase_paper_recommendation_reason_trend_health_config.py`,
  `supabase_strategy_recommendation_reason_trend_config.py`, and their direct
  tests.
- A5: autonomous/trading/execution config group:
  `supabase_outcome_tracking_config.py`,
  `supabase_paper_trade_journal_config.py`,
  `supabase_paper_nav_snapshot_config.py`,
  `supabase_local_observability_trends_config.py`,
  `supabase_paper_execution_pipeline_config.py`.

### Batch B: CLI Durable File Defaults

Goal: stop treating file paths as the default durable project store.

High-priority default writers:

- `scan --archive-root=data/raw`
- `scan --output=artifacts/market-scores.json`
- `strategy-cycle --archive-root=data/raw`
- `strategy-cycle --output=artifacts/strategy-cycle.jsonl`
- `strategy-cycle --paper-journal=artifacts/paper-trades.jsonl`
- `run --archive-root=data/raw`
- `run --cycle-log=artifacts/strategy-cycle.jsonl`
- `run --paper-journal=artifacts/paper-trades.jsonl`

Recommended direction:

- Introduce an explicit storage-mode boundary, for example
  `local-db | files | dual`, with `local-db` allowed only for local DSNs.
- Keep file export/import/replay explicit.
- Keep `--paper-execute` explicit.
- Convert file readers after DB-backed writers are available.

### Batch C: Core History Stores

Goal: make core strategy-cycle, paper-trade, and NAV history DB-primary.

Primary modules:

- `strategy_cycle.py`
- `journal.py`
- `positions.py`
- `runner.py`
- DB row/store/psycopg adapters for cycle snapshots, trade journals, and NAV
  snapshots

### Batch D: Secondary Report Logs

Goal: migrate report-only logs/readers to local DB while preserving explicit
file replay/export.

Primary modules:

- `outcome_tracker.py`
- `strategy_risk_audit_log.py`
- `strategy_recommendation_log.py`
- `local_observability_trends.py`

### Batch E: Local Input Loaders

Goal: replace JSON/JSONL local-input surfaces with DB-backed sources for new
flows, leaving file input as explicit import/replay only.

Primary modules:

- `paper_probability_recommendation_queue_local_input.py`
- `paper_recommendation_risk_budget_local_input.py`
- related CLI side-edge/risk-budget commands

## Verification Expectations

Every node should run:

- focused tests for changed files
- `tests/test_supabase_local_dsn.py` when DSN validation changes
- `PYTHONDONTWRITEBYTECODE=1 python3 -m compileall -q src tests`
- `git diff --check`
- local opencode review with model `zhipuai-coding-plan/glm-5.2` and
  `--variant max`

Before pushing to GitHub from Codex, also run the full suite, sync CodeGraph
when needed, and verify no tracked secrets were introduced.
