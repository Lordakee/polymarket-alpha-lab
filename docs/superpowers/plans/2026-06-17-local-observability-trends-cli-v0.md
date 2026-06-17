# Local Observability Trends CLI/Runner v0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local-only `observability-trends` CLI command that reads local paper logs and prints a container report made from the four existing observability trend reducers.

**Architecture:** Create `local_observability_trends.py` as the runner/container module. It reads no network state, accepts explicitly supplied local paths, builds source/append-order prefix report sequences from typed reader output, calls the existing trend reducers, and returns a frozen `LocalObservabilityTrendsReport`; `cli.py` only parses paths, calls the runner, and prints compact child summaries.

**Tech Stack:** Python frozen dataclasses, existing typed JSONL readers, existing Phase 1 reducers, `datetime`, `Decimal`, argparse, pytest, AST scope tests.

---

## Commit Boundary

Implement only the Local Observability Trends CLI/Runner node. Do not change
`run`, `runner.py`, `strategy-cycle`, `strategy_cycle.py`, paper execution,
screening, NAV marking, outcome tracking behavior, Strategy Risk Audit math, or
package-root exports.

## Planned File Structure

- Create: `src/polymarket_alpha_lab/local_observability_trends.py`
- Create: `tests/test_local_observability_trends.py`
- Create: `tests/test_local_observability_trends_runner.py`
- Create: `tests/test_local_observability_trends_scope.py`
- Modify: `src/polymarket_alpha_lab/cli.py`
- Modify: `tests/test_cli.py`
- Modify: `README.md`

Do not modify `src/polymarket_alpha_lab/runner.py`,
`src/polymarket_alpha_lab/strategy_cycle.py`, package-root exports, or their
tests except by running verification.

## Task 1: RED CLI Surface Tests

**Files:**
- Modify: `tests/test_cli.py`

- [x] **Step 1: Add CLI tests for runner injection**

Add tests for `observability-trends` with required local paths, optional logs,
`--outcome-stale-after-seconds`, a forbidden `client_factory`, and an injected
runner returning a stub report.

- [x] **Step 2: Add no-regression tests for `run` and `strategy-cycle`**

Extend the existing forbidden runner test so `run` and `strategy-cycle` never
call the new observability trends runner.

- [x] **Step 3: Run RED tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli.py -k "observability_trends or run_and_strategy_cycle_do_not_call_strategy_evidence_runner" -q
```

Expected RED result before implementation: `main()` lacks
`observability_trends_runner` and the command does not exist.

## Task 2: Runner Module and Runner Tests

**Files:**
- Create: `src/polymarket_alpha_lab/local_observability_trends.py`
- Create: `tests/test_local_observability_trends.py`
- Create: `tests/test_local_observability_trends_runner.py`

- [x] **Step 1: Add runner tests for empty local logs**

Assert empty required logs produce:

- empty strategy evidence trend history
- empty outcome freshness
- empty NAV risk trend
- empty cost trend
- `paper_only`, `report_only`, and `readonly` set to `True`
- no input file mutation

- [x] **Step 2: Add runner tests for append-order prefix semantics**

Assert:

- NAV trend report count follows non-empty NAV prefixes
- cost trend report count follows non-empty trade prefixes
- strategy evidence trend report count follows the max required stream length
- outcome freshness uses all supplied outcome reports in append order
- latest values come from source/append order, not timestamp sorting by the runner,
  including NAV prefix inputs supplied to NAV risk trend construction

- [x] **Step 3: Implement `LocalObservabilityTrendsConfig`**

Fields:

- `config_version: str`
- `outcome_stale_after_seconds: int = 86400`

Validate canonical config version and nonnegative stale threshold.

- [x] **Step 4: Implement `LocalObservabilityTrendsReport`**

Fields:

- `generated_at`
- `config_version`
- `strategy_evidence_trend`
- `outcome_freshness`
- `nav_risk_trend`
- `paper_trade_cost_trend`
- `paper_only=True`
- `report_only=True`
- `readonly=True`

Validate exact child report types and their hard flags.

- [x] **Step 5: Implement `run_local_observability_trends`**

Read only:

- `PaperStrategyCycleLog.read(cycle_log)`
- `PaperTradeJournal.read(trade_log)`
- `PaperNavLog.read(nav_log)`
- `OutcomeTrackingLog.read(outcome_log)` when supplied
- `PaperStrategyRiskAuditLog.read(strategy_audit_log)` when supplied

Then build the four child trend reports through existing reducers. Do not write,
append, create directories, construct clients, call network APIs, or call
`check_outcomes`.

For local observability trend prefixes, use the tuple order returned by the typed
readers as the only ordering authority. Do not timestamp-sort cycle, trade, NAV,
outcome, or Strategy Risk Audit inputs before slicing prefixes. The shared NAV
risk metrics reducer can keep its standalone chronological metric behavior, but
the local observability runner must pass NAV prefixes in source/append order.

## Task 3: Scope Tests

**Files:**
- Create: `tests/test_local_observability_trends_scope.py`

- [x] **Step 1: Add AST import scope checks**

Allow only local typed readers and pure reducers needed by the runner.

- [x] **Step 2: Add forbidden surface checks**

Forbid API/client/auth/wallet/private-key/network/http/request/order/live/rank/
recommend/advice/instruction surfaces and calls such as `append`, `write`,
`submit`, `sign`, `cancel`, `fetch`, and `list_markets`.

- [x] **Step 3: Add CLI branch isolation checks**

Assert `run` and `strategy-cycle` command branches do not reference
observability trend runner symbols.

## Task 4: CLI Wiring

**Files:**
- Modify: `src/polymarket_alpha_lab/cli.py`
- Modify: `tests/test_cli.py`

- [x] **Step 1: Import the local runner and config**

Import `LocalObservabilityTrendsConfig`, `LocalObservabilityTrendsReport`, and
`run_local_observability_trends`.

- [x] **Step 2: Add runner injection**

Add `ObservabilityTrendsRunner = Callable[..., LocalObservabilityTrendsReport]`
and an `observability_trends_runner` parameter to `main`, defaulting to
`run_local_observability_trends`.

- [x] **Step 3: Add the command parser**

Add `observability-trends` with:

- `--cycle-log`
- `--trade-log`
- `--nav-log`
- `--outcome-log`
- `--strategy-audit-log`
- `--outcome-stale-after-seconds`

- [x] **Step 4: Add execution branch and printer**

Build `LocalObservabilityTrendsConfig`, call the injected runner, print a compact
summary, return `0`, and on exception print
`observability-trends failed: ...` to stderr and return `1`.

Do not touch the `run` or `strategy-cycle` branches.

## Task 5: Docs

**Files:**
- Modify: `README.md`
- Create: `docs/superpowers/specs/2026-06-17-local-observability-trends-cli-v0.md`
- Create: `docs/superpowers/plans/2026-06-17-local-observability-trends-cli-v0.md`

- [x] **Step 1: Document command usage and boundary**

Document the command as local observability only. Mention that it reads
caller-selected local logs, prints trends, and does not write or mutate any
artifact. State that local trend prefixes use source/append order from typed
readers, including NAV trend inputs, and are not timestamp-sorted by the command.

## Verification

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_local_observability_trends.py \
  tests/test_local_observability_trends_report_validation.py \
  tests/test_local_observability_trends_runner.py \
  tests/test_local_observability_trends_scope.py \
  tests/test_cli.py \
  -q
```

Run:

```bash
.venv/bin/python -m pytest tests/test_*_scope.py -q
.venv/bin/python -m compileall src/polymarket_alpha_lab
git diff --check
```

Then run the full suite:

```bash
.venv/bin/python -m pytest -q
```

Finally request the configured Claude audit with
`claude-opus-4-8 --effort max`, commit locally, and do not push unless the
remote pinning rule is explicitly overridden.
