# Action-Gated Decision-Support Trend CLI Runtime Wiring Plan

**Goal:** Add a Phase 1 CLI/runtime node that turns persisted action-gated decision-support snapshots into a trend report and optionally persists the compact trend DB manifest.

**Architecture:** The command is read/report/paper-only. It reads existing decision-support DB rows through the existing decision-support psycopg loader, builds a trend report from the recovered `(priority_report, risk_report)` pairs, prints a compact summary, and optionally writes the manifest-first trend rows through the new trend psycopg adapter when the trend DB config is enabled.

**Global constraints:**

- No live trading, auth, wallet, account reads, order construction, signing, submission, cancellation, replacement, exchange mutation, or live execution.
- Do not fetch Polymarket or external market data in this node.
- Do not add package-root exports.
- DSN values must be redacted from user-facing errors.
- Store/persist only the compact trend manifest already implemented by the trend DB persistence node.
- CLI default behavior must be useful without mutating any database: it reads source snapshots and prints a trend report.
- DB trend persistence is optional and only runs when `POLYMARKET_ALPHA_LAB_ACTION_GATED_QUEUE_DECISION_SUPPORT_TREND_DB_ENABLED` is true.
- Source decision-support DB config still controls source snapshot loading.

## Task 1: CLI Command And Runner

**Files:**

- Modify `src/polymarket_alpha_lab/cli.py`
- Modify `tests/test_cli.py`

**Command:**

`polymarket-alpha-lab action-gated-queue-decision-support-trend`

**Arguments:**

- `--source-limit`, positive integer, default `50`
- `--source-risk-status`, choices `pass|watch|blocked`, default unset
- `--persist`, flag, default false. When true, insert compact trend rows using trend DB config.

**Runner seam:**

Add an injectable runner argument to `main(...)`, for tests:

`action_gated_queue_decision_support_trend_runner`

Runner receives:

- source DSN
- generated_at
- config version
- source limit
- source risk status
- source reports table
- persist flag
- trend DSN
- trend reports table
- trend sources table

**Runtime rules:**

- Load source decision-support DB rows using existing source decision-support psycopg loader.
- Convert source DB rows back into `(priority_report, risk_report)` pairs using existing DB row codec.
- Source loader returns newest-first; build the trend from chronological order by passing reversed source rows into the trend builder.
- Build `PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendReport`.
- If `--persist` is set:
  - require trend DB config enabled and trend DB DSN present,
  - call `insert_paper_action_gated_strategy_recommendation_queue_decision_support_trend_db_rows_with_psycopg(...)`,
  - pass the same trend report and chronological source pairs.
- If `--persist` is not set:
  - do not require trend DB config and do not write anything.
- Redact both source DB DSN and trend DB DSN from any printed error.

**Summary output:**

First line starts with `action-gated-queue-decision-support-trend:` and includes:

- `snapshots`
- `first`
- `latest`
- `latest_risk_status`
- `pass`
- `watch`
- `blocked`
- `ready_notional_delta`
- `top_priority_score_delta`
- `average_priority_score_delta`
- `duplicate_generated_at_count`
- `persisted`

Second line starts with `trend_reason_codes:` and prints repeated reason code counts as `code:count`, or `none`.

## Task 2: Runtime Scope Guard

**Files:**

- Add or modify a focused scope test in `tests/test_cli.py` or a new `tests/test_action_gated_queue_decision_support_trend_cli_scope.py`.

**Rules:**

- The command path must not import or call live trading, auth, wallet, account, order, signing, submission, cancellation, replacement, or exchange mutation APIs.
- Allow source DB read and optional trend DB insert adapter names.
- Ensure the command has no `--dsn` argument and uses environment config only.

## Task 3: Docs

**Files:**

- Modify `docs/action-gated-queue-decision-support.md`

Document:

- command name,
- source DB env dependency,
- optional trend DB persistence env dependency,
- that the command remains paper/report/readonly and never trades.

## Task 4: Verification, Review, Commit, Push

Run:

```bash
.venv/bin/python -m pytest tests/test_cli.py tests/test_action_gated_queue_decision_support_trend_cli_scope.py -q
.venv/bin/python -m pytest -q
.venv/bin/python -m compileall -q src tests
git diff --check
codegraph sync
codegraph status .
opencode run --model zhipuai-coding-plan/glm-5.2 --variant max --dir /home/ubuntu/polymarket-alpha-lab "<review prompt>"
```

Fix Critical/Important findings, then commit and push.
