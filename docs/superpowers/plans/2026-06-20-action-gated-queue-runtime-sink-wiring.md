# Action-Gated Queue Runtime Sink Wiring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire action-gated strategy recommendation queue reports into the paper runtime and CLI as an opt-in local Supabase/Postgres audit sink.

**Architecture:** Keep the queue reducer and strategy runner free of DB imports. Add a pure source-builder module that derives an action-gated queue report from an in-memory strategy cycle report, extend the runner with injected source/sink callables, and wire CLI env config plus psycopg persistence only at the process boundary. The feature remains Phase 1: paper-only/report-only/readonly evidence persistence only, with no live trading, auth, wallet, private key, order, account, or exchange mutation surfaces.

**Tech Stack:** Python dataclasses, Decimal-only configs, existing paper cycle snapshot/review/action-gate reducers, injected callables, local Supabase/Postgres psycopg adapter, pytest fake runners/connections, CodeGraph.

---

## Parallel Work Partition

The first development wave can run these write scopes in parallel:

- **Worker A, pure source builder:** only `src/polymarket_alpha_lab/strategy_cycle_action_gated_queue_source.py`, `tests/test_strategy_cycle_action_gated_queue_source.py`, and `tests/test_strategy_cycle_action_gated_queue_source_scope.py`.
- **Worker B, runtime hook:** only `src/polymarket_alpha_lab/runner.py` and `tests/test_runner.py`.
- **Worker C, CLI process boundary:** only `src/polymarket_alpha_lab/cli.py` and `tests/test_cli.py`.
- **Worker D, scope/docs:** only `tests/test_cli_action_gated_queue_runtime_sink_scope.py` and `docs/strategy-recommendation-layer.md`.

Workers must not edit each other's files. If a worker discovers it needs another write scope, it should stop and report the required dependency instead of editing outside its scope.

## Task 1: Pure Strategy-Cycle Action-Gated Queue Source

**Files:**
- Create: `src/polymarket_alpha_lab/strategy_cycle_action_gated_queue_source.py`
- Create: `tests/test_strategy_cycle_action_gated_queue_source.py`
- Create: `tests/test_strategy_cycle_action_gated_queue_source_scope.py`

- [ ] **Step 1: Write source-builder tests**

Cover:
- wrong `cycle_report` type is rejected;
- false `paper_only` / `report_only` on the cycle report is rejected;
- a blocked or watch cycle produces a paper-only/report-only/readonly action-gated queue report with no nested queue artifacts;
- a ready cycle with screening and cost reports can produce a ready queue report;
- optional configs must be exact expected config dataclass types;
- no DB, psycopg, Supabase, env, network, auth, wallet, private-key, account, live, or order-submission imports appear.

- [ ] **Step 2: Implement pure source builder**

Expose:

```python
def build_strategy_cycle_action_gated_queue_source_report(
    cycle_report: object,
    iteration_started_at: datetime | None = None,
    *,
    review_config: PaperRecommendationCycleReviewConfig | None = None,
    action_gate_config: PaperRecommendationCycleActionGateConfig | None = None,
    queue_config: PaperActionGatedStrategyRecommendationQueueConfig | None = None,
) -> PaperActionGatedStrategyRecommendationQueueReport:
    ...
```

Implementation path:
- build an in-memory cycle snapshot with `build_strategy_cycle_snapshot_source_report`;
- build a cycle review over a one-item tuple containing that snapshot;
- build the paper cycle action gate from that review;
- pass the gate plus `cycle_report.screening_report` and `cycle_report.cost_aware_reports` into `build_paper_action_gated_strategy_recommendation_queue_report`;
- use conservative defaults:
  - review config `paper-recommendation-cycle-review-v0`, stale after `24`;
  - action gate config `paper-recommendation-cycle-action-gate-v0`;
  - queue config `action-gated-strategy-recommendation-queue-v0` with the existing candidate assessment, bundle recommendation, and selection policy defaults already used in tests.

Run:

```bash
.venv/bin/python -m pytest tests/test_strategy_cycle_action_gated_queue_source.py tests/test_strategy_cycle_action_gated_queue_source_scope.py -q
```

## Task 2: Runtime Source/Sink Hook

**Files:**
- Modify: `src/polymarket_alpha_lab/runner.py`
- Modify: `tests/test_runner.py`

- [ ] **Step 1: Write runner tests**

Cover:
- non-callable `action_gated_queue_source` and `action_gated_queue_sink` are rejected;
- source+sink run once per completed iteration;
- sink is inert when source is absent;
- source is inert when sink is absent;
- sink/source failures count as iteration failures under `log_and_continue`;
- unsafe queue reports without `paper_only`, `report_only`, or `readonly` are rejected;
- `RunLoopSummary.action_gated_queues_persisted` is nonnegative and defaults to zero.

- [ ] **Step 2: Implement runner hook**

Add keyword-only params to `run_strategy_loop`:

```python
action_gated_queue_source: object | None = None
action_gated_queue_sink: object | None = None
```

Add `action_gated_queues_persisted: int = 0` to `RunLoopSummary`, validate it, and increment only after the sink succeeds. Keep runner free of DB/psycopg/Supabase imports.

Run:

```bash
.venv/bin/python -m pytest tests/test_runner.py -q
```

## Task 3: CLI Env/Sink Wiring

**Files:**
- Modify: `src/polymarket_alpha_lab/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write CLI tests**

Cover:
- action-gated queue DB env disabled by default passes no source/sink to `loop_runner`;
- enabled env passes a source and sink to `loop_runner`;
- injected fake DB sink receives `dsn`, `report`, and `table_name`;
- default source is `build_strategy_cycle_action_gated_queue_source_report`;
- sink failures redact DSN in printed `last_error`;
- output summary includes `action_gated_queues_persisted=N` when the summary has that attribute;
- no CLI flags are added for DSNs or live trading.

- [ ] **Step 2: Implement process-boundary wiring**

Import:
- `insert_paper_action_gated_strategy_recommendation_queue_report_with_psycopg`;
- `from_action_gated_strategy_recommendation_queue_db_env`;
- `build_strategy_cycle_action_gated_queue_source_report`.

Add injectable `main()` params:

```python
action_gated_queue_source: object | None = None
action_gated_queue_db_sink: ActionGatedQueueDbSink = insert_paper_action_gated_strategy_recommendation_queue_report_with_psycopg
```

When env config is enabled, construct a redacted closure:

```python
def action_gated_queue_sink(report):
    try:
        return action_gated_queue_db_sink(dsn=dsn, report=report, table_name=table)
    except Exception as exc:
        _raise_redacted_db_sink_error(exc, dsn=dsn)
```

Pass `action_gated_queue_source` and `action_gated_queue_sink` into `loop_runner`.

Run:

```bash
.venv/bin/python -m pytest tests/test_cli.py -q
```

## Task 4: CLI Scope Guard And Docs

**Files:**
- Create: `tests/test_cli_action_gated_queue_runtime_sink_scope.py`
- Modify: `docs/strategy-recommendation-layer.md`

- [ ] **Step 1: Add scope guard**

Assert:
- `runner.py` has no DB/psycopg/Supabase imports;
- new action-gated queue CLI wiring does not add DSN command-line args;
- forbidden fragments for live/auth/wallet/private-key/account/order submission/cancel/signing are absent from the new scope test target;
- action-gated queue sink wiring names remain under `run`, not Phase 2 commands.

- [ ] **Step 2: Update docs**

Add a short note that runtime persistence is opt-in, env-driven, and persists audit artifacts only after a paper cycle completes. Re-state that persisted queue rows are not approval to trade.

Run:

```bash
.venv/bin/python -m pytest tests/test_cli_action_gated_queue_runtime_sink_scope.py -q
```

## Integration Verification

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_strategy_cycle_action_gated_queue_source.py \
  tests/test_strategy_cycle_action_gated_queue_source_scope.py \
  tests/test_runner.py \
  tests/test_cli.py \
  tests/test_cli_action_gated_queue_runtime_sink_scope.py \
  tests/test_action_gated_strategy_recommendation_queue_db_row.py \
  tests/test_action_gated_strategy_recommendation_queue_store.py \
  tests/test_action_gated_strategy_recommendation_queue_psycopg.py \
  tests/test_supabase_action_gated_strategy_recommendation_queue_config.py \
  -q
.venv/bin/python -m pytest -q
.venv/bin/python -m compileall -q src tests
git diff --check
codegraph sync && codegraph status .
opencode run --model zhipuai-coding-plan/glm-5.2 --variant max --dir /home/ubuntu/polymarket-alpha-lab "<review prompt>"
```

## Self-Review

- Spec coverage: The plan covers pure derivation, runtime injection, CLI env/process boundary wiring, scope guard, docs, tests, OpenCode review, and push.
- Placeholder scan: No TBD/TODO/fill-in-later placeholders remain.
- Conflict control: Initial parallel tasks own disjoint write sets; `cli.py` and `tests/test_cli.py` are owned by one worker only.
