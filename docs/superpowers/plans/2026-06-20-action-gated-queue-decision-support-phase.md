# Action-Gated Queue Decision Support Phase Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** After the current action-gated queue runtime sink is pushed, add paper-only decision support for queue priority, Supabase/Postgres-backed read-only persisted report loading, and queue risk summaries.

**Architecture:** Treat the runtime sink as the append path for already-built action-gated queue reports, then layer pure priority and risk reducers plus a raw read-only psycopg report loader above the existing Supabase/Postgres persistence boundary. The implemented priority node ranks whole persisted queue reports for human research attention. The implemented psycopg read node only loads persisted queue reports. The implemented risk node summarizes raw queue reports against configured notional and candidate-count caps. Database access remains opt-in, env-driven, redacted, and read-only for this phase; all operator output is decision support, not permission to trade.

**Tech Stack:** Python frozen dataclasses, `Decimal`, existing action-gated queue report and Supabase/Postgres store/psycopg adapters, argparse CLI wiring, pytest fake loaders, CodeGraph-first navigation, local OpenCode review.

---

## Prerequisite

- The current runtime sink node is completed, reviewed, committed, and pushed.
- Fresh workers start from a clean understanding of current `main` plus any explicitly assigned branch, and must not edit files outside their node ownership.
- This phase assumes the existing action-gated queue persistence path can append reports to local Supabase/Postgres; this plan adds read-only history consumers, not another writer.

## Phase 1 Safety Constraints

This is still Phase 1. Every node must preserve:

- paper-only, report-only, readonly outputs and tests;
- no live trading, authenticated exchange flow, wallet/private-key handling, account reads, balances, positions from exchange accounts, order construction, signing, submission, cancellation, replacement, or exchange mutation;
- no command-line DSN arguments and no sample secrets;
- no printing raw DSNs, credentials, `.env` contents, private keys, full payload JSON, or Supabase secrets;
- no production imports from exchange mutation/auth surfaces in new files.

Supabase/Postgres usage is limited to the existing local persistence/read-only path: use redacted env config at the process boundary, call read adapters for already-persisted action-gated queue reports, and summarize returned typed reports. Do not inspect or document secret values.

## Parallel Work Partition

These nodes can run in parallel only after the prerequisite runtime sink is pushed. File ownership is intentionally non-overlapping.

- **Worker A, queue priority report ranking (complete):** owned only `src/polymarket_alpha_lab/action_gated_strategy_recommendation_queue_priority.py` and `tests/test_action_gated_strategy_recommendation_queue_priority.py`.
- **Worker B, raw read-only persisted report loading (complete):** owned only `src/polymarket_alpha_lab/action_gated_strategy_recommendation_queue_psycopg_read.py` and `tests/test_action_gated_strategy_recommendation_queue_psycopg_read.py`.
- **Worker C, queue risk summary against caps (complete):** owned only `src/polymarket_alpha_lab/action_gated_strategy_recommendation_queue_risk.py` and `tests/test_action_gated_strategy_recommendation_queue_risk.py`.
- **Worker D, CLI decision-support surface:** owns only `src/polymarket_alpha_lab/cli.py`, `tests/test_cli.py`, and `tests/test_cli_action_gated_queue_decision_support_scope.py`.
- **Worker E, operator documentation:** owns only `docs/action-gated-queue-decision-support.md` and `tests/test_docs_action_gated_queue_decision_support_scope.py`.

Workers must stop and report if they need another worker's file. No worker may edit `docs/strategy-recommendation-layer.md` or the current runtime sink plan as part of this phase unless a later explicit user instruction reassigns ownership.

## Node A: Queue Priority Report Ranking

**Files:**

- Complete: `src/polymarket_alpha_lab/action_gated_strategy_recommendation_queue_priority.py`
- Complete: `tests/test_action_gated_strategy_recommendation_queue_priority.py`

- [x] **Step 1: Write priority tests**

Covered deterministic priority rows built from exact `PaperActionGatedStrategyRecommendationQueueReport` objects:

- wrong report collection values are rejected;
- false `paper_only`, `report_only`, or `readonly` flags are rejected;
- `research_ready` queue reports sort before `watch` and `blocked` reports;
- whole queue reports sort deterministically by ready count, top queue score, average ready score, total ready notional, candidate count, config versions, and source timestamp;
- watch/blocked reports remain research-priority rows without fabricating executable intent;
- output contains report-level fields including priority rank, source timestamps, config versions, action status, recommended next step, research priority, status counts, ready notional, queue scores, and research priority score;
- hard Phase 1 flags remain true on all priority outputs.

- [x] **Step 2: Implement pure priority report ranking**

Implemented a frozen report model and builder:

```python
build_paper_action_gated_strategy_recommendation_queue_priority_report(
    reports: Iterable[PaperActionGatedStrategyRecommendationQueueReport],
    *,
    generated_at: datetime,
) -> PaperActionGatedStrategyRecommendationQueuePriorityReport
```

The builder consumes typed action-gated queue reports, validates hard flags, preserves `Decimal` values, ranks whole reports for human research attention, and performs no DB reads or writes.

- [x] **Step 3: Verify Node A**

```bash
.venv/bin/python -m pytest tests/test_action_gated_strategy_recommendation_queue_priority.py -q
.venv/bin/python -m compileall -q src tests
git diff --check
```

## Node B: Raw Read-Only Persisted Report Loading

**Files:**

- Complete: `src/polymarket_alpha_lab/action_gated_strategy_recommendation_queue_psycopg_read.py`
- Complete: `tests/test_action_gated_strategy_recommendation_queue_psycopg_read.py`

- [x] **Step 1: Write read-only psycopg load tests**

Covered a read-only helper that loads persisted action-gated queue report rows as typed report objects:

- read options validate optional source config version, action status, limit, and table name;
- the loader issues only a `SELECT` over persisted queue-report columns;
- results are ordered newest first by `generated_at` and `report_sha256`;
- DB rows are converted through the existing action-gated queue DB row adapter into `PaperActionGatedStrategyRecommendationQueueReport` objects;
- the psycopg helper owns the connection and closes it after loading;
- the module exposes no insert, update, delete, commit, rollback, order, signing, wallet, account, or exchange mutation path.

- [x] **Step 2: Implement raw read-only report loader**

Expose:

```python
PaperActionGatedStrategyRecommendationQueueReadOptions
load_paper_action_gated_strategy_recommendation_queue_reports(
    connection: Any,
    *,
    options: PaperActionGatedStrategyRecommendationQueueReadOptions | None = None,
) -> tuple[PaperActionGatedStrategyRecommendationQueueReport, ...]
load_paper_action_gated_strategy_recommendation_queue_reports_with_psycopg(
    dsn: str,
    *,
    options: PaperActionGatedStrategyRecommendationQueueReadOptions | None = None,
) -> tuple[PaperActionGatedStrategyRecommendationQueueReport, ...]
```

This node is intentionally not a history summary reducer. It is the raw read-only persisted report loading boundary for already-persisted action-gated queue reports and must not add any write adapter, commit behavior, migration, or aggregate summary semantics.

- [x] **Step 3: Verify Node B**

```bash
.venv/bin/python -m pytest tests/test_action_gated_strategy_recommendation_queue_psycopg_read.py -q
.venv/bin/python -m compileall -q src tests
git diff --check
```

## Node C: Queue Risk Summary Against Caps

**Files:**

- Complete: `src/polymarket_alpha_lab/action_gated_strategy_recommendation_queue_risk.py`
- Complete: `tests/test_action_gated_strategy_recommendation_queue_risk.py`

- [x] **Step 1: Write risk-summary tests**

Covered summaries that evaluate raw queue reports against configured paper caps:

- exact queue report and risk config types are required;
- hard flags remain true on all outputs;
- source queue counts, action-status counts, candidate counts, ready counts, watch counts, blocked counts, total ready notional, largest queue ready notional, and utilization values are summarized deterministically;
- blocking and watch reason codes are derived from source queue status, total ready notional cap, single queue ready notional cap, ready candidate cap, total candidate cap, and throttle utilization threshold;
- status labels stay descriptive as `pass`, `watch`, or `blocked`, and never become order approvals;
- recommended next steps stay paper research allocation guidance: `allocate_paper_research_queue`, `throttle_paper_research_queue`, or `block_paper_research_queue`;
- the module has no trading/auth/wallet/account/order/signing/exchange mutation imports.

- [x] **Step 2: Implement pure risk summary**

Expose:

```python
PaperActionGatedStrategyRecommendationQueueRiskConfig
build_paper_action_gated_strategy_recommendation_queue_risk_report(
    queue_reports: object,
    *,
    config: PaperActionGatedStrategyRecommendationQueueRiskConfig,
    generated_at: datetime,
) -> PaperActionGatedStrategyRecommendationQueueRiskReport
```

This module stays pure, summarizes raw queue reports against caps, and does not import DB or CLI modules.

- [x] **Step 3: Verify Node C**

```bash
.venv/bin/python -m pytest tests/test_action_gated_strategy_recommendation_queue_risk.py -q
.venv/bin/python -m compileall -q src tests
git diff --check
```

## Node D: CLI Decision-Support Surface

**Files:**

- Modify: `src/polymarket_alpha_lab/cli.py`
- Modify: `tests/test_cli.py`
- Create: `tests/test_cli_action_gated_queue_decision_support_scope.py`

- [ ] **Step 1: Write CLI tests**

Cover a read-only command, for example `action-gated-queue-decision-support`:

- disabled DB config exits with a clear read-only DB configuration message and does not call a loader;
- enabled DB config calls an injected read-only persisted report loader and injected pure builders;
- output prints aggregate priority/risk/history fields only;
- output redacts DSN and never prints raw payload JSON;
- no DSN command-line flag is added;
- no run-loop, sink, insert, order, auth, wallet, signing, submit, cancel, or account path is invoked.

- [ ] **Step 2: Implement CLI wiring at the process boundary**

Wire env config and loader injection in `cli.py` only. The CLI may import the pure priority/risk builders and the read-only psycopg report loader, but must not add persistence writes or mutate exchange state.

- [ ] **Step 3: Verify Node D**

```bash
.venv/bin/python -m pytest tests/test_cli.py tests/test_cli_action_gated_queue_decision_support_scope.py -q
.venv/bin/python -m compileall -q src tests
git diff --check
```

## Node E: Operator Documentation

**Files:**

- Create: `docs/action-gated-queue-decision-support.md`
- Create: `tests/test_docs_action_gated_queue_decision_support_scope.py`

- [ ] **Step 1: Write docs scope test**

Assert the new doc says:

- the feature is Phase 1 paper-only/report-only/readonly decision support;
- Supabase/Postgres is used as a read-only persisted report source for already-persisted action-gated queue reports;
- no secrets, DSNs, wallet keys, account reads, live trading, order signing, submission, or cancellation are part of the flow;
- queue priority and risk summaries are operator review aids, not trade approvals.

- [ ] **Step 2: Add the operator doc**

Document the operator flow:

1. Runtime sink appends action-gated queue reports.
2. Read-only psycopg loader loads persisted queue reports without adding summary or write semantics.
3. Priority reducer ranks whole queue reports for human research attention.
4. Risk summary highlights cap utilization, source queue status pressure, and blocking/watch reason codes.
5. CLI prints a redacted decision-support summary.

- [ ] **Step 3: Verify Node E**

```bash
.venv/bin/python -m pytest tests/test_docs_action_gated_queue_decision_support_scope.py -q
git diff --check
```

## Integration Verification Checklist

Run after all nodes are merged in a single integration branch:

```bash
.venv/bin/python -m pytest \
  tests/test_action_gated_strategy_recommendation_queue_priority.py \
  tests/test_action_gated_strategy_recommendation_queue_psycopg_read.py \
  tests/test_action_gated_strategy_recommendation_queue_risk.py \
  tests/test_cli.py \
  tests/test_cli_action_gated_queue_decision_support_scope.py \
  tests/test_docs_action_gated_queue_decision_support_scope.py \
  -q
.venv/bin/python -m pytest -q
.venv/bin/python -m compileall -q src tests
git diff --check
codegraph sync && codegraph status .
```

Also run a staged-file safety scan before review:

```bash
git diff --cached --name-only
git diff --cached --check
```

Confirm manually from the staged path list that only the node-owned files are staged and that no `.env`, secret, wallet, key, or unrelated runtime sink files are included.

## OpenCode Review Rule

Every node and the final integration branch require local OpenCode review after tests pass and before push:

```bash
opencode run --model zhipuai-coding-plan/glm-5.2 --variant max --dir /home/ubuntu/polymarket-alpha-lab "<read-only review prompt>"
```

The prompt must state that OpenCode is read-only: it may inspect and report findings, but must not stage, commit, push, modify files, access secrets, perform live trading, read accounts, or call exchange mutation APIs. Any Critical or Important finding blocks push until fixed and re-reviewed.

## Push Gate

Do not push any node until all of the following are true:

- prerequisite runtime sink work is already pushed;
- node-specific tests pass;
- full pytest and compileall pass on the integration branch before final phase push;
- `git diff --check` and staged `git diff --cached --check` pass;
- CodeGraph is synced and reports clean status for the repo;
- OpenCode review passes with no unresolved Critical or Important findings;
- staged files match the node ownership list, with no unrelated user edits, no existing runtime sink plan edits, and no `docs/strategy-recommendation-layer.md` edits unless explicitly reassigned later;
- final commit message identifies the node and keeps Phase 1/read-only scope clear.

## Self-Review

- Spec coverage: This plan covers action-gated queue priority, Supabase/Postgres read-only history, risk guard summaries, parallel non-overlapping ownership, Phase 1 safety constraints, OpenCode review, verification, and push gates.
- Marker scan: No unresolved plan markers remain.
- Boundary check: The plan adds only decision-support read surfaces after the runtime sink append path; it does not authorize live trading, auth, wallet, account, signing, order submission, cancellation, or exchange mutation.
