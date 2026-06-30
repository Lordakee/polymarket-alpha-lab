# Strategy Cycle Paper Trade DB-First Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `strategy-cycle --paper-execute` write paper trade records to the configured local Supabase/Postgres sink without requiring or forcing the legacy JSONL `paper-trades.jsonl` file.

**Architecture:** Keep the existing paper trade journal JSONL type as an explicit compatibility sink, but decouple it from enabling inline paper execution. `run_strategy_cycle` should deliver records to the injected sink first when present and only append JSONL when `paper_trade_journal_path` is explicitly supplied. The CLI should prefer the local Supabase/Postgres paper trade sink when enabled and leave `paper_trade_journal_path` unset unless `--paper-journal` is provided.

**Tech Stack:** Python dataclasses, `Decimal`, existing DB-API/psycopg paper trade journal store, argparse CLI, pytest, local Supabase/Postgres environment boundary.

**Execution status:** Implemented in commit `e330500` plus follow-up review fixes in this node. The shared `run_strategy_cycle` paper-trade sink ordering also affects continuous `run` whenever it passes `paper_trade_record_sink`, but this node still does not add DB-backed NAV, outcome, history, or runner read-source migration.

## Global Constraints

- Durable project data must use local Supabase/Postgres only.
- Do not add SQLite, Redis, Mongo, SQLAlchemy, hosted DB assumptions, generic DB abstractions, or new file-backed durable storage.
- Phase 1 boundary: no live trading, no auth/wallet/private keys, no order signing/submission/cancellation/replacement, and no exchange mutation.
- Keep `paper_only is True` and report-only/read-only safety boundaries intact.
- Use `Decimal` for monetary/probability values; do not introduce floats.
- Preserve frozen dataclass patterns.
- Keep the legacy JSONL `PaperTradeJournal` only as explicit compatibility when a journal path is supplied.
- Do not silently drop `PaperTradeRecord`s: paper execution requires either a configured DB sink at runtime or an explicit compatibility `paper_trade_journal_path`.
- Do not migrate `runner.py` DB read sources, NAV, outcome tracking, or strategy cycle report JSONL in this node; those are separate persistence-boundary nodes. Shared-core paper trade sink ordering may be documented and tested in `runner.py` where the loop delegates to `run_strategy_cycle`.
- Redact DB DSNs and table names from CLI failure output.

---

### Task 1: Strategy Cycle Core DB-First Paper Trade Sink

**Files:**
- Modify: `tests/test_strategy_cycle.py`
- Modify: `src/polymarket_alpha_lab/strategy_cycle.py`

**Interfaces:**
- Consumes: `run_strategy_cycle(..., paper_trade_record_sink: Callable[[object], object] | None = None)`
- Produces: `PaperStrategyCycleConfig` accepts `paper_execution_config` with `paper_trade_journal_path=None`; `run_strategy_cycle` sends `PaperTradeRecord` to `paper_trade_record_sink` when present and appends JSONL only when `paper_trade_journal_path` is not `None`.

- [x] **Step 1: Write failing tests**

Add tests near the existing inline paper execution tests:

```python
def test_strategy_cycle_paper_trade_record_sink_does_not_require_jsonl_journal(tmp_path):
    market, books = _screening_ready_market_and_books()
    journal_path = tmp_path / "paper-trades.jsonl"
    config = cycle_config(
        paper_execution_config=PaperExecutionConfig(
            config_version="paper-execution-v1",
            account_equity=Decimal("100.0000"),
            max_notional_per_trade=Decimal("10.0000"),
        ),
        paper_trade_journal_path=None,
    )
    sink_records = []

    report = run_strategy_cycle(
        client=FakeMarketDataClient([market], books),
        scan_config=scan_config(tmp_path),
        cycle_config=config,
        generated_at=GENERATED_AT,
        paper_trade_record_sink=sink_records.append,
    )

    assert report.screening_report is not None
    assert report.screening_report.ready_count == 1
    assert len(sink_records) == 1
    assert not journal_path.exists()
```

Add the sink-failure ordering test:

```python
def test_strategy_cycle_paper_trade_record_sink_failure_leaves_no_jsonl_record(tmp_path):
    market, books = _screening_ready_market_and_books()
    journal_path = tmp_path / "paper-trades.jsonl"
    config = cycle_config(
        paper_execution_config=PaperExecutionConfig(
            config_version="paper-execution-v1",
            account_equity=Decimal("100.0000"),
            max_notional_per_trade=Decimal("10.0000"),
        ),
        paper_trade_journal_path=journal_path,
    )

    def failing_sink(record):
        raise RuntimeError(f"db unavailable for {record.packet_id}")

    with pytest.raises(RuntimeError, match="db unavailable"):
        run_strategy_cycle(
            client=FakeMarketDataClient([market], books),
            scan_config=scan_config(tmp_path),
            cycle_config=config,
            generated_at=GENERATED_AT,
            paper_trade_record_sink=failing_sink,
        )

    assert not journal_path.exists()
```

Add the no-persistence-target guard test:

```python
def test_strategy_cycle_paper_execution_requires_sink_without_journal_path(tmp_path):
    market, books = _screening_ready_market_and_books()
    client = FakeMarketDataClient([market], books)
    config = cycle_config(
        paper_execution_config=PaperExecutionConfig(
            config_version="paper-execution-v1",
            account_equity=Decimal("100.0000"),
            max_notional_per_trade=Decimal("10.0000"),
        ),
        paper_trade_journal_path=None,
    )

    with pytest.raises(ValueError, match="paper_trade_record_sink is required"):
        run_strategy_cycle(
            client=client,
            scan_config=scan_config(tmp_path),
            cycle_config=config,
            generated_at=GENERATED_AT,
        )

    assert client.list_markets_calls == []
    assert client.get_order_book_calls == []
```

Update the existing config validation parameterization so `paper_execution_config` without `paper_trade_journal_path` is valid, while `paper_trade_journal_path` without `paper_execution_config` is still rejected.

- [x] **Step 2: Verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_strategy_cycle.py -k "paper_trade_record_sink or inline_paper_pass or invalid_paper_execution_config"
```

Expected: the new tests fail because `PaperStrategyCycleConfig` still requires both `paper_execution_config` and `paper_trade_journal_path`, and the old sink-failure behavior appends JSONL before the sink.

- [x] **Step 3: Implement minimal core behavior**

In `PaperStrategyCycleConfig.__post_init__`:

```python
if self.paper_execution_config is not None and not isinstance(
    self.paper_execution_config,
    PaperExecutionConfig,
):
    raise ValueError(
        "paper_execution_config must be a PaperExecutionConfig",
    )
if self.paper_trade_journal_path is not None:
    if self.paper_execution_config is None:
        raise ValueError(
            "paper_trade_journal_path requires paper_execution_config",
        )
    if not isinstance(self.paper_trade_journal_path, Path):
        raise ValueError("paper_trade_journal_path must be a Path")
```

In `run_strategy_cycle`, change the inline pass guard to:

```python
if (
    cycle_config.paper_execution_config is not None
    and cycle_config.paper_trade_journal_path is None
    and paper_trade_record_sink is None
):
    raise ValueError(
        "paper_trade_record_sink is required when paper execution has no journal path",
    )

if cycle_config.paper_execution_config is not None and screening is not None:
    journal = (
        PaperTradeJournal(cycle_config.paper_trade_journal_path)
        if cycle_config.paper_trade_journal_path is not None
        else None
    )
```

Change record persistence ordering to:

```python
if paper_result.record is not None:
    if paper_trade_record_sink is not None:
        paper_trade_record_sink(paper_result.record)
    if journal is not None:
        journal.append(paper_result.record)
```

Do not catch sink failures. A local Supabase/Postgres sink failure must abort before JSONL compatibility append so it does not leave a durable file-backed record when DB persistence fails.

Add the runtime guard before any client/archive work so invalid paper execution with no DB sink and no explicit compatibility journal does not fetch markets.

`PaperTradeJournal(path)` is a frozen dataclass wrapper and does not touch the filesystem; only `append()` creates the parent directory and writes the JSONL line. The sink-failure test relies on that existing constructor behavior.

- [x] **Step 4: Verify GREEN**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_strategy_cycle.py
```

Expected: all strategy cycle tests pass.

- [x] **Step 5: Commit**

```bash
git add tests/test_strategy_cycle.py src/polymarket_alpha_lab/strategy_cycle.py
git commit -m "feat: make strategy cycle paper trades db-first"
```

### Task 2: CLI Paper Trade Journal Path Selection

**Files:**
- Modify: `tests/test_cli.py`
- Modify: `src/polymarket_alpha_lab/cli.py`

**Interfaces:**
- Consumes: `from_paper_trade_journal_db_env()` and `insert_paper_trade_record_with_psycopg`
- Produces: `strategy-cycle --paper-execute` leaves `cycle_config.paper_trade_journal_path is None` when the paper trade DB env is enabled and `--paper-journal` is omitted; `--paper-journal` remains explicit compatibility.

- [x] **Step 1: Write failing tests**

Add or update tests near the existing `strategy-cycle --paper-execute` CLI tests:

```python
def test_strategy_cycle_cli_paper_execute_db_enabled_omits_default_jsonl_journal(
    tmp_path,
    monkeypatch,
):
    fake_dsn = "postgresql://paper-trade@localhost/db"
    monkeypatch.setenv(PAPER_TRADE_JOURNAL_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(PAPER_TRADE_JOURNAL_DB_DSN_ENV_VAR, fake_dsn)
    calls = []

    def fake_cycle_runner(
        *,
        client,
        scan_config,
        cycle_config,
        paper_trade_record_sink,
    ):
        calls.append((cycle_config, paper_trade_record_sink))
        return _empty_strategy_cycle_report()

    exit_code = main(
        [
            "strategy-cycle",
            "--paper-execute",
            "--archive-root",
            str(tmp_path / "raw"),
            "--output",
            str(tmp_path / "strategy-cycle.jsonl"),
        ],
        cycle_runner=fake_cycle_runner,
        paper_trade_record_db_sink=lambda **kwargs: None,
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 0
    assert len(calls) == 1
    cycle_config, paper_trade_record_sink = calls[0]
    assert cycle_config.paper_execution_config is not None
    assert cycle_config.paper_trade_journal_path is None
    assert paper_trade_record_sink is not None
    assert not (tmp_path / "paper-trades.jsonl").exists()
```

Update `test_strategy_cycle_cli_wires_paper_trade_db_sink_when_enabled` to omit `--paper-journal` and assert `cycle_config.paper_trade_journal_path is None`.

Update `test_strategy_cycle_cli_redacts_dsn_when_paper_trade_db_sink_fails` to omit `--paper-journal` and assert the legacy JSONL path was not created.

Keep `test_strategy_cycle_cli_paper_execute_flag_enables_inline_paper_pass` with explicit `--paper-journal` so compatibility remains covered.

Add a CLI guard test:

```python
def test_strategy_cycle_cli_paper_execute_requires_db_sink_or_explicit_journal(
    tmp_path,
    monkeypatch,
    capsys,
):
    monkeypatch.delenv(PAPER_TRADE_JOURNAL_DB_ENABLED_ENV_VAR, raising=False)
    monkeypatch.delenv(PAPER_TRADE_JOURNAL_DB_DSN_ENV_VAR, raising=False)

    def forbidden_cycle_runner(**kwargs):
        raise AssertionError("cycle runner should not run")

    exit_code = main(
        [
            "strategy-cycle",
            "--paper-execute",
            "--archive-root",
            str(tmp_path / "raw"),
            "--output",
            str(tmp_path / "strategy-cycle.jsonl"),
        ],
        cycle_runner=forbidden_cycle_runner,
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "paper trade DB persistence or --paper-journal is required" in captured.err
    assert "cycle runner should not run" not in captured.err
```

- [x] **Step 2: Verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_cli.py -k "paper_trade_db_sink or paper_execute_flag or paper_trade_db_sink_fails or omits_default_jsonl"
```

Expected: the new DB-enabled no-journal test fails because the CLI still supplies a default paper journal path.

- [x] **Step 3: Implement minimal CLI behavior**

Change the `--paper-journal` argparse option so it defaults to `None`, not `Path("artifacts/paper-trades.jsonl")`. Keep the explicit path behavior unchanged when the user supplies the option.

In the `strategy-cycle` command branch, keep the DB env parse before constructing `cycle_config`. Build the paper trade sink exactly as before when DB config is enabled. If `args.paper_execute` is true and neither `paper_trade_db_config.enabled` nor `args.paper_journal` is set, raise:

```python
ValueError("paper trade DB persistence or --paper-journal is required for --paper-execute")
```

Rely on the existing `strategy-cycle` command `try/except Exception` block to print `strategy-cycle failed: ...` to stderr and return `1`; do not let this guard escape as an uncaught traceback.

Pass `args.paper_journal` through to `_build_default_cycle_config`; when omitted and DB is enabled, this is `None`, so the core cycle uses the DB sink only.

Also update `_build_default_cycle_config` itself so it no longer substitutes `Path("artifacts/paper-trades.jsonl")` when `paper_journal is None`. Its paper execution branch should become:

```python
return replace(
    base,
    paper_execution_config=PaperExecutionConfig(
        config_version="paper-execution-v1",
    ),
    paper_trade_journal_path=paper_journal,
)
```

The CLI guard and `run_strategy_cycle` guard are the persistence-safety checks. `_build_default_cycle_config` must not reintroduce a legacy file path after those checks.

Do not change `run` DB read-source/NAV behavior in this node unless a focused test fails because of shared parser behavior. The shared `run_strategy_cycle` sink-before-JSONL ordering applies to `run_strategy_loop` when it passes a `paper_trade_record_sink`; DB-backed NAV journal/source migration remains a separate node.

- [x] **Step 4: Verify GREEN**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_cli.py -k "paper_trade_db_sink or paper_execute_flag or paper_trade_db_sink_fails or omits_default_jsonl"
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_cli.py
```

Expected: all CLI tests pass.

- [x] **Step 5: Commit**

```bash
git add tests/test_cli.py src/polymarket_alpha_lab/cli.py
git commit -m "feat: prefer db sink for strategy cycle paper trades"
```

### Task 3: Documentation And Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/strategy-recommendation-layer.md`

**Interfaces:**
- Consumes: behavior from Tasks 1 and 2.
- Produces: docs that state one-shot strategy-cycle paper trade writes are DB-first when the local Supabase/Postgres sink is enabled, while JSONL remains the legacy compatibility/export/replay path and the input for not-yet-migrated consumers.

- [x] **Step 1: Update docs**

Update the CLI/paper execution docs with this exact behavior:

```text
When `POLYMARKET_ALPHA_LAB_PAPER_TRADE_JOURNAL_DB_ENABLED=true` and the local
Postgres DSN is configured, `strategy-cycle --paper-execute` sends paper trade
records to the local Supabase/Postgres journal sink without creating the legacy
`artifacts/paper-trades.jsonl` file. Pass `--paper-journal <path>` only when an
explicit JSONL compatibility copy is needed.
```

Do not claim that NAV, outcome tracking, run-loop cycle reports, raw archives, forecast evidence, or all project persistence have been migrated.

- [x] **Step 2: Focused verification**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_strategy_cycle.py tests/test_cli.py
```

Expected: both focused suites pass.

- [x] **Step 3: Full verification**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q
PYTHONDONTWRITEBYTECODE=1 python3 -m compileall -q src tests
git diff --check origin/main..HEAD
git grep -n -E '(ghp_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{20,}|sk-proj-[A-Za-z0-9_-]{20,}|sk-live-[A-Za-z0-9_-]{20,}|-----BEGIN (RSA |OPENSSH |EC |DSA |)PRIVATE KEY-----)' HEAD || true
```

Expected: full suite passes, compileall passes, diff whitespace check is clean, secret scan finds no matches.

- [ ] **Step 4: CodeGraph sync and opencode review**

Run:

```bash
codegraph sync
opencode run --model zhipuai-coding-plan/glm-5.2 --reasoning-effort max "<read-only review prompt>"
```

Expected: opencode reports no Critical or Important findings. Fix any Critical/Important finding and rerun focused tests before proceeding.

- [ ] **Step 5: Commit docs and push**

This project run has explicit user authorization to push verified nodes to GitHub. If a future session executes this plan without that explicit authorization, stop after the local commit and ask before pushing.

```bash
git add README.md docs/strategy-recommendation-layer.md docs/superpowers/plans/2026-06-30-strategy-cycle-paper-trade-db-first.md
git commit -m "docs: document strategy cycle paper trade db-first sink"
git push origin main
```

After push, append a one-node summary to `.superpowers/sdd/progress.md` with the pushed commit range, verification commands, opencode result, uncommitted files, and next recommended node. `.superpowers/sdd/progress.md` is development-process metadata, not project data persistence, and must not be treated as precedent for new file-backed durable project storage.
