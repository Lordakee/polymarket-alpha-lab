# DB Runtime Persistence Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire the paper trade journal, NAV snapshot, and outcome tracking DB repositories into runtime command paths behind explicit environment toggles.

**Architecture:** Keep storage adapters at the CLI/process boundary and inject plain callable sinks into pure paper/report orchestrators. `strategy_cycle.py`, `paper_portfolio_nav.py`, and `runner.py` remain protocol-only and do not import psycopg, Supabase config, auth, wallet, exchange, or account surfaces. DB failures propagate through existing CLI/runner error handling when the DB toggle is enabled; disabled env leaves current JSONL behavior unchanged.

**Tech Stack:** Python frozen dataclasses, DB-API/psycopg adapters already present in `src/polymarket_alpha_lab/*_psycopg.py`, pytest, CodeGraph, OpenCode review with `zhipuai-coding-plan/glm-5.2` max.

---

### Task 1: Env Config Modules

**Files:**
- Create: `src/polymarket_alpha_lab/supabase_paper_trade_journal_config.py`
- Create: `src/polymarket_alpha_lab/supabase_paper_nav_snapshot_config.py`
- Create: `src/polymarket_alpha_lab/supabase_outcome_tracking_config.py`
- Create: `tests/test_supabase_paper_trade_journal_config.py`
- Create: `tests/test_supabase_paper_nav_snapshot_config.py`
- Create: `tests/test_supabase_outcome_tracking_config.py`
- Modify: `.env.example`

- [x] **Step 1: Write failing config tests**

Each config test should mirror `tests/test_supabase_cycle_snapshot_config.py` with slice-specific names. Example paper trade assertion:

```python
def test_disabled_env_config_accepts_missing_dsn() -> None:
    config = from_paper_trade_journal_db_env({})

    assert config == SupabasePaperTradeJournalConfig(
        enabled=False,
        dsn=None,
        table_name=DEFAULT_PAPER_TRADE_JOURNAL_DB_TABLE,
    )
```

- [x] **Step 2: Run focused RED tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_supabase_paper_trade_journal_config.py -q
.venv/bin/python -m pytest tests/test_supabase_paper_nav_snapshot_config.py -q
.venv/bin/python -m pytest tests/test_supabase_outcome_tracking_config.py -q
```

Expected: each fails with `ModuleNotFoundError` or missing symbol before implementation.

- [x] **Step 3: Implement config modules**

Each module should match the existing `supabase_cycle_snapshot_config.py` narrow pattern:

```python
@dataclass(frozen=True)
class SupabasePaperTradeJournalConfig:
    enabled: bool
    dsn: str | None
    table_name: str = DEFAULT_PAPER_TRADE_JOURNAL_DB_TABLE

    def __post_init__(self) -> None:
        if type(self.enabled) is not bool:
            raise ValueError("enabled must be a bool")
        object.__setattr__(self, "dsn", _normalize_optional_dsn(self.dsn))
        object.__setattr__(self, "table_name", _validate_table_name(self.table_name))
        if self.enabled and self.dsn is None:
            raise ValueError(
                f"{PAPER_TRADE_JOURNAL_DB_DSN_ENV_VAR} must be set when DB is enabled"
            )
```

- [x] **Step 4: Update `.env.example`**

Append empty, non-secret variable names only:

```dotenv
POLYMARKET_ALPHA_LAB_PAPER_TRADE_JOURNAL_DB_ENABLED=
POLYMARKET_ALPHA_LAB_PAPER_TRADE_JOURNAL_DB_DSN=
POLYMARKET_ALPHA_LAB_PAPER_TRADE_JOURNAL_DB_TABLE=
POLYMARKET_ALPHA_LAB_PAPER_NAV_SNAPSHOT_DB_ENABLED=
POLYMARKET_ALPHA_LAB_PAPER_NAV_SNAPSHOT_DB_DSN=
POLYMARKET_ALPHA_LAB_PAPER_NAV_SNAPSHOT_DB_TABLE=
POLYMARKET_ALPHA_LAB_OUTCOME_TRACKING_DB_ENABLED=
POLYMARKET_ALPHA_LAB_OUTCOME_TRACKING_DB_DSN=
POLYMARKET_ALPHA_LAB_OUTCOME_TRACKING_DB_TABLE=
```

- [x] **Step 5: Run focused GREEN tests**

Run the three focused config test files plus `tests/test_supabase_cycle_snapshot_config.py`.

### Task 2: Paper Trade Record DB Sink Injection

**Files:**
- Modify: `src/polymarket_alpha_lab/strategy_cycle.py`
- Modify: `src/polymarket_alpha_lab/runner.py`
- Modify: `src/polymarket_alpha_lab/cli.py`
- Test: `tests/test_strategy_cycle.py`
- Test: `tests/test_cli.py`
- Test: `tests/test_runner.py` if present, otherwise the runner coverage inside `tests/test_cli.py`

- [ ] **Step 1: Write failing strategy-cycle test**

Add a test proving that when paper execution produces a `PaperTradeRecord`, an injected `paper_trade_record_sink` receives the exact record after JSONL journaling.

- [ ] **Step 2: Run RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_strategy_cycle.py -q
```

Expected: failure because `run_strategy_cycle` does not accept `paper_trade_record_sink`.

- [ ] **Step 3: Implement minimal sink parameter**

Add optional keyword parameter:

```python
paper_trade_record_sink: Callable[[object], object] | None = None,
```

Validate it is callable or `None`. In the existing paper execution block, after `journal.append(paper_result.record)`, call `paper_trade_record_sink(paper_result.record)` when provided.

- [ ] **Step 4: Wire runner pass-through**

Add optional `paper_trade_record_sink` to `run_strategy_loop` and pass it into `run_strategy_cycle`. Keep `runner.py` free of DB adapter imports.

- [ ] **Step 5: Wire CLI env boundary**

In `cli.py`, import `from_paper_trade_journal_db_env` and `insert_paper_trade_record_with_psycopg`. Add injectable `paper_trade_record_db_sink` defaulting to the psycopg insert function. In `strategy-cycle` and `run`, if env is enabled, require DSN and pass a closure:

```python
def run_paper_trade_record_sink(record: object) -> object:
    return paper_trade_record_db_sink(
        dsn=dsn,
        record=record,
        table_name=paper_trade_db_config.table_name,
    )
```

- [ ] **Step 6: Run focused tests**

Run `tests/test_strategy_cycle.py`, `tests/test_cli.py`, and any runner test file touched by the change.

### Task 3: NAV Snapshot DB Sink Injection

**Files:**
- Modify: `src/polymarket_alpha_lab/paper_portfolio_nav.py`
- Modify: `src/polymarket_alpha_lab/runner.py`
- Modify: `src/polymarket_alpha_lab/cli.py`
- Test: `tests/test_paper_portfolio_nav.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write failing NAV test**

Add a `tests/test_paper_portfolio_nav.py` test proving `nav_snapshot_sink` receives the same `PaperNavSnapshot` returned by `mark_paper_portfolio_nav`.

- [ ] **Step 2: Run RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_portfolio_nav.py -q
```

Expected: failure because `mark_paper_portfolio_nav` does not accept `nav_snapshot_sink`.

- [ ] **Step 3: Implement minimal sink parameter**

Add optional `nav_snapshot_sink: Callable[[PaperNavSnapshot], object] | None = None` and call it after optional `PaperNavLog.append(snapshot)`.

- [ ] **Step 4: Wire runner and CLI**

Add `nav_snapshot_sink` pass-through in `_mark_nav_or_skip` and `run_strategy_loop`. In `portfolio-nav` and `run`, enable DB persistence via `from_paper_nav_snapshot_db_env` and `insert_paper_nav_snapshot_with_psycopg`.

- [ ] **Step 5: Run focused tests**

Run `tests/test_paper_portfolio_nav.py`, `tests/test_cli.py`, and affected runner coverage.

### Task 4: Outcome Tracking DB Sink Injection

**Files:**
- Modify: `src/polymarket_alpha_lab/cli.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write failing CLI test**

Add a no-network `check-outcomes` CLI test that sets outcome tracking DB env enabled, injects a fake `outcome_tracking_db_sink`, and asserts the generated `OutcomeTrackingReport` is passed to the sink without DSN appearing in stdout/stderr.

- [ ] **Step 2: Run RED**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli.py::test_check_outcomes_cli_persists_outcome_tracking_report_when_db_enabled -q
```

Expected: failure because `main` has no outcome tracking DB sink injection.

- [ ] **Step 3: Wire CLI**

Import `from_outcome_tracking_db_env` and `insert_outcome_tracking_report_with_psycopg`. Add injectable `outcome_tracking_db_sink` defaulting to the psycopg insert function. In the `check-outcomes` command, after optional JSONL log append, call the DB sink when env is enabled.

- [ ] **Step 4: Run focused tests**

Run all `check-outcomes` CLI tests and `tests/test_outcome_tracking_psycopg.py`.

### Task 5: Verification, Review, Commit, Push

**Files:**
- All files changed by Tasks 1-4.

- [ ] **Step 1: Run full gate**

Run:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m compileall -q src tests
git diff --check
codegraph sync && codegraph status .
```

- [ ] **Step 2: Secret scan changed files**

Run an `rg` scan over changed files for obvious token/credential patterns. Expected: no live secrets, no real DSNs with credentials.

- [ ] **Step 3: OpenCode review**

Use local OpenCode for plan and code review. Model must be `zhipuai-coding-plan/glm-5.2`, thinking/max variant. Claude is not the review path for this node.

- [ ] **Step 4: Commit and push**

Create logical commits only after tests and review. Push to `origin/main` once the node is green and reviewed.

---

**Self-review notes:** This plan keeps DB adapters out of protocol-only orchestrators; every runtime DB write remains opt-in by explicit env enablement and DSN. It does not introduce live trading, auth, wallet, private key, order construction/submission/cancel/signing, exchange mutation, or account reads.
