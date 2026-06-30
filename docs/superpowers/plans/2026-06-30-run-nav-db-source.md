# Continuous Run NAV DB Source Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let continuous `run` NAV source handling use local Supabase/Postgres paper trade records when the paper trade journal DB env is enabled, without adding DB/env/psycopg dependencies to `runner.py`.

**Architecture:** Add a runner-level `paper_trade_record_source` callable seam that returns typed paper trade records for NAV replay. The runner stays protocol-only and uses the injected source before legacy JSONL fallback; `cli.py` owns the env read, local Postgres DSN/table redaction, and reversal from the existing newest-first DB loader order into append/chronological order. JSONL remains the legacy compatibility/export/replay fallback when no source is injected.

**Tech Stack:** Python, pytest, local Supabase/Postgres through the existing psycopg adapter, Decimal-only paper records, frozen dataclasses, CodeGraph, local opencode review with model `zhipuai-coding-plan/glm-5.2` and variant `max`.

## Global Constraints

- Durable project data uses local Supabase/Postgres only; JSONL remains explicit legacy compatibility/export/replay where not yet migrated.
- No SQLite, Redis, Mongo, SQLAlchemy, hosted DB assumptions, generic DB abstraction, or new file-backed durable storage.
- Phase 1 boundary remains: no live trading, no auth/wallet/private keys, no order signing/submission/cancellation/replacement, no exchange mutation.
- Preserve `Decimal` usage, frozen dataclasses, `paper_only is True`, and paper-only/report-only/read-only behavior.
- `runner.py` must remain free of DB/env/psycopg/Supabase imports and must not import `journal`, `positions`, `api`, or other forbidden live/loader surfaces.
- DB source read failures must not silently fall back to JSONL; redact DSNs and table names in CLI error output.
- The existing DB paper trade loader returns newest-first records; any source used for portfolio/NAV replay must return oldest-first append/chronological order.
- Do not overclaim migration scope: this node migrates only continuous `run` NAV paper-trade source handling. Outcome tracking, history/performance summary, cost audit, strategy audit, and observability/trend consumers remain separate migration surfaces.

---

### Task 1: Runner NAV Source Injection

**Files:**
- Modify: `src/polymarket_alpha_lab/runner.py`
- Test: `tests/test_runner.py`
- Test: `tests/test_runner_scope.py`

**Interfaces:**
- Consumes: `paper_trade_record_source: object | None = None`, an optional callable returning an iterable of `PaperTradeRecord` values
- Produces: `run_strategy_loop(..., paper_trade_record_source=None, ...)` that passes sourced records to `_mark_paper_portfolio_nav_from_records(...)` before falling back to legacy JSONL

- [ ] **Step 1: Write failing runner behavior tests**

Add tests in `tests/test_runner.py` proving:

```python
def test_paper_trade_record_source_marks_nav_without_journal_path(tmp_path):
    market, books = _screening_ready_market_and_books()
    client = FakeMarketDataClient([market], books)
    trade_records = []
    nav_snapshots = []
    nav_log = tmp_path / "nav.jsonl"
    config = cycle_config(
        paper_execution_config=_paper_exec_config(),
        paper_trade_journal_path=None,
    )

    summary = run_strategy_loop(
        client=client,
        scan_config=scan_config(tmp_path),
        cycle_config=config,
        starting_cash=Decimal("10000"),
        nav_log_path=nav_log,
        cycle_report_log_path=tmp_path / "cycle.jsonl",
        paper_trade_record_sink=trade_records.append,
        paper_trade_record_source=lambda: tuple(trade_records),
        nav_snapshot_sink=nav_snapshots.append,
    )

    assert summary.iterations_completed == 1
    assert summary.iterations_failed == 0
    assert summary.nav_marks_skipped == 0
    assert len(trade_records) == 1
    assert len(nav_snapshots) == 1
    assert len(nav_log.read_text(encoding="utf-8").splitlines()) == 1
    assert not (tmp_path / "paper-trades.jsonl").exists()
```

Also add tests proving:

```python
def test_paper_trade_record_source_takes_precedence_over_missing_journal(tmp_path):
    ...
    config = cycle_config(
        paper_execution_config=_paper_exec_config(),
        paper_trade_journal_path=tmp_path / "missing-paper-trades.jsonl",
    )
    ...
    paper_trade_record_source=lambda: tuple(trade_records),
    ...
    assert summary.nav_marks_skipped == 0
```

Name the no-JSONL success test `test_nav_mark_uses_injected_paper_trade_record_source_without_journal_path` if it fits the surrounding test naming better; the required behavior is the same.

```python
def test_empty_paper_trade_record_source_marks_cash_only_nav(tmp_path):
    ...
    paper_trade_record_source=lambda: (),
    ...
    assert summary.nav_marks_skipped == 0
    assert len(client.fetched_books) == 0
    assert snapshot["position_count"] == 0
    assert Decimal(snapshot["exit_nav"]) == Decimal("10000")
```

```python
def test_paper_trade_record_source_failure_counts_as_iteration_failure(tmp_path):
    def broken_source():
        raise RuntimeError("paper trade source unavailable")
    ...
    summary = run_strategy_loop(..., paper_trade_record_source=broken_source, on_cycle_error="log_and_continue")
    assert summary.iterations_completed == 0
    assert summary.iterations_failed == 1
    assert summary.nav_marks_skipped == 0
    assert summary.last_error == "RuntimeError: paper trade source unavailable"
```

```python
def test_paper_trade_record_source_file_not_found_counts_as_iteration_failure(tmp_path):
    def broken_source():
        raise FileNotFoundError("paper trade source certificate missing")
    ...
    assert summary.iterations_failed == 1
    assert summary.nav_marks_skipped == 0
```

```python
def test_run_strategy_loop_rejects_non_callable_paper_trade_record_source(tmp_path):
    with pytest.raises(ValueError, match="paper_trade_record_source must be callable or None"):
        run_strategy_loop(..., paper_trade_record_source=object())
```

- [ ] **Step 2: Write failing runner scope test**

In `tests/test_runner_scope.py`, extend `test_runner_public_loop_api_allows_cycle_report_sink_without_db_imports` or add a nearby `test_runner_public_loop_api_allows_paper_trade_record_source_without_db_imports` test:

```python
assert "paper_trade_record_source" in keyword_names
assert not any("db" in module_name for module_name in imported_modules(tree))
assert not any("psycopg" in module_name for module_name in imported_modules(tree))
assert not any("postgres" in module_name for module_name in imported_modules(tree))
assert not any("supabase" in module_name for module_name in imported_modules(tree))
assert not any("env" in module_name for module_name in imported_modules(tree))
```

If `test_runner_does_not_define_forbidden_live_or_advice_surface_names` rejects the new argument name because of an existing forbidden fragment, add the exact required name to `ALLOWED_REQUIRED_DOMAIN_NAMES` and do not weaken the forbidden fragments.

Also tighten `FORBIDDEN_SOURCE_STRING_TOKENS` so string-based DB/env drift in `runner.py` is caught. Add these tokens unless an equivalent stricter guard already exists:

```python
"psycopg",
"postgres",
"supabase",
"POLYMARKET_ALPHA_LAB",
"from_paper_trade_journal_db_env",
"paper_trade_record_db",
```

- [ ] **Step 3: Run focused tests and confirm RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q \
  tests/test_runner.py::test_paper_trade_record_source_marks_nav_without_journal_path \
  tests/test_runner.py::test_paper_trade_record_source_takes_precedence_over_missing_journal \
  tests/test_runner.py::test_empty_paper_trade_record_source_marks_cash_only_nav \
  tests/test_runner.py::test_paper_trade_record_source_failure_counts_as_iteration_failure \
  tests/test_runner.py::test_paper_trade_record_source_file_not_found_counts_as_iteration_failure \
  tests/test_runner.py::test_run_strategy_loop_rejects_non_callable_paper_trade_record_source \
  tests/test_runner_scope.py
```

Expected: fail because `run_strategy_loop` does not accept `paper_trade_record_source`.

- [ ] **Step 4: Implement runner source seam**

In `src/polymarket_alpha_lab/runner.py`:

1. Add `paper_trade_record_source: object | None = None` after `paper_trade_record_sink`.
2. Pass it into `_validate_loop_params(...)`.
3. Pass it into `_mark_nav_or_skip(...)`.
4. In `_validate_loop_params`, reject non-callable non-`None` values with:

```python
if paper_trade_record_source is not None and not callable(paper_trade_record_source):
    raise ValueError("paper_trade_record_source must be callable or None")
```

5. In `_mark_nav_or_skip`, add `paper_trade_record_source: object | None = None`. If it is not `None`, call it before the legacy journal-path branch:

```python
if paper_trade_record_source is not None:
    records = tuple(paper_trade_record_source())
    _mark_paper_portfolio_nav_from_records(
        records,
        starting_cash=starting_cash,
        client=client,
        marked_at=marked_at,
        nav_log_path=nav_log_path,
        nav_snapshot_sink=nav_snapshot_sink,  # type: ignore[arg-type]
    )
    return 0
```

Do not catch `FileNotFoundError` or other exceptions from the injected source; existing loop error policy must classify them as iteration failures.

- [ ] **Step 5: Run focused tests and confirm GREEN**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_runner.py tests/test_runner_scope.py
```

### Task 2: CLI Run DB Source Wiring

**Files:**
- Modify: `src/polymarket_alpha_lab/cli.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: `from_paper_trade_journal_db_env()`, `load_paper_trade_records_with_psycopg(dsn=..., table_name=...)`
- Produces: when paper trade DB env is enabled, `main(... run ...)` passes `paper_trade_record_source` into `loop_runner`

- [ ] **Step 1: Write failing CLI wiring test**

Add a test near `test_run_cli_wires_paper_trade_and_nav_db_sinks_when_env_enabled`:

```python
def test_run_cli_wires_paper_trade_db_source_when_env_enabled(tmp_path, monkeypatch, capsys):
    trade_dsn = "postgresql://paper-trade@localhost/db"
    table_name = "paper_trade_archive"
    monkeypatch.setenv(PAPER_TRADE_JOURNAL_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(PAPER_TRADE_JOURNAL_DB_DSN_ENV_VAR, trade_dsn)
    monkeypatch.setenv(PAPER_TRADE_JOURNAL_DB_TABLE_ENV_VAR, table_name)
    newest = SimpleNamespace(label="newest")
    older = SimpleNamespace(label="older")
    loader_calls = []
    loop_calls = []

    def fake_loader(*, dsn, table_name):
        loader_calls.append((dsn, table_name))
        return (newest, older)

    def fake_loop_runner(**kwargs):
        loop_calls.append(kwargs)
        source = kwargs["paper_trade_record_source"]
        assert source is not None
        assert source() == (older, newest)
        return _empty_run_summary()

    exit_code = main(
        [
            "run",
            "--paper-execute",
            "--archive-root",
            str(tmp_path / "raw"),
            "--starting-cash",
            "10000",
            "--cycle-log",
            str(tmp_path / "cycle.jsonl"),
        ],
        loop_runner=fake_loop_runner,
        paper_trade_record_db_loader=fake_loader,
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 0
    assert loader_calls == [(trade_dsn, table_name)]
    assert len(loop_calls) == 1
    captured = capsys.readouterr()
    assert trade_dsn not in captured.out
    assert trade_dsn not in captured.err
    assert table_name not in captured.out
    assert table_name not in captured.err
```

The assertion calls the source twice only if the fake loop runner needs to test idempotence. Otherwise call it once.

- [ ] **Step 2: Write failing CLI redaction test**

Add:

```python
def test_run_cli_redacts_dsn_and_table_when_paper_trade_db_source_fails(tmp_path, monkeypatch, capsys):
    trade_dsn = "postgresql://paper-trade@localhost/db"
    table_name = "paper_trade_archive"
    monkeypatch.setenv(PAPER_TRADE_JOURNAL_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(PAPER_TRADE_JOURNAL_DB_DSN_ENV_VAR, trade_dsn)
    monkeypatch.setenv(PAPER_TRADE_JOURNAL_DB_TABLE_ENV_VAR, table_name)

    def broken_loader(*, dsn, table_name):
        raise RuntimeError(f"failed reading {dsn} table={table_name}")

    def fake_loop_runner(**kwargs):
        kwargs["paper_trade_record_source"]()
        return _empty_run_summary()

    exit_code = main([...], loop_runner=fake_loop_runner, paper_trade_record_db_loader=broken_loader, client_factory=lambda: "fake-client")

    assert exit_code == 1
    captured = capsys.readouterr()
    assert trade_dsn not in captured.err
    assert table_name not in captured.err
    assert "<redacted-dsn>" in captured.err
    assert "<redacted-table>" in captured.err
```

Use the full `run --paper-execute --archive-root ... --starting-cash 10000 --cycle-log ...` argv from Step 1.

- [ ] **Step 3: Write failing CLI config-before-client test**

Add:

```python
def test_run_cli_requires_valid_paper_trade_db_source_config_before_client_work(
    tmp_path,
    monkeypatch,
    capsys,
):
    monkeypatch.setenv(PAPER_TRADE_JOURNAL_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(PAPER_TRADE_JOURNAL_DB_DSN_ENV_VAR, "postgresql://paper-trade@localhost/db")
    monkeypatch.setenv(PAPER_TRADE_JOURNAL_DB_TABLE_ENV_VAR, "Bad-Table")

    def forbidden_client_factory():
        raise AssertionError("client should not be constructed")

    def forbidden_loop_runner(**kwargs):
        raise AssertionError("loop runner should not run")

    exit_code = main(
        [
            "run",
            "--paper-execute",
            "--archive-root",
            str(tmp_path / "raw"),
            "--starting-cash",
            "10000",
            "--cycle-log",
            str(tmp_path / "cycle.jsonl"),
        ],
        loop_runner=forbidden_loop_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "client should not be constructed" not in captured.err
    assert "loop runner should not run" not in captured.err
    assert PAPER_TRADE_JOURNAL_DB_TABLE_ENV_VAR in captured.err
```

This protects the ordering constraint: invalid DB source configuration fails in `cli.py` before public client construction or loop work.

- [ ] **Step 4: Run focused tests and confirm RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q \
  tests/test_cli.py::test_run_cli_wires_paper_trade_db_source_when_env_enabled \
  tests/test_cli.py::test_run_cli_redacts_dsn_and_table_when_paper_trade_db_source_fails \
  tests/test_cli.py::test_run_cli_requires_valid_paper_trade_db_source_config_before_client_work
```

Expected: fail because `loop_runner_kwargs` does not include `paper_trade_record_source`.

- [ ] **Step 5: Implement CLI source closure**

In `src/polymarket_alpha_lab/cli.py` run branch:

1. Initialize `run_paper_trade_record_source = None` beside the existing sink/snapshot closures.
2. Inside `if paper_trade_db_config.enabled:`, after defining `run_paper_trade_record_sink`, define:

```python
def run_paper_trade_record_source(
    *,
    db_dsn: str = dsn,
    table_name: str = paper_trade_db_config.table_name,
) -> tuple[object, ...]:
    try:
        loaded_records = paper_trade_record_db_loader(
            dsn=db_dsn,
            table_name=table_name,
        )
    except Exception as exc:
        _raise_redacted_db_read_error(
            exc,
            dsn=db_dsn,
            table_name=table_name,
        )
    return tuple(reversed(loaded_records))
```

3. Add `"paper_trade_record_source": run_paper_trade_record_source` to `loop_runner_kwargs`.
4. Update existing explicit fake `loop_runner` signatures in `tests/test_cli.py` to accept `paper_trade_record_source` and assert it is `None` when DB env is disabled.
5. Leave the existing JSONL path behavior untouched when DB env is disabled.

- [ ] **Step 6: Run focused tests and confirm GREEN**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q \
  tests/test_cli.py::test_run_cli_wires_paper_trade_and_nav_db_sinks_when_env_enabled \
  tests/test_cli.py::test_run_cli_wires_paper_trade_db_source_when_env_enabled \
  tests/test_cli.py::test_run_cli_redacts_dsn_when_paper_trade_db_sink_failure_is_reported \
  tests/test_cli.py::test_run_cli_redacts_dsn_and_table_when_paper_trade_db_source_fails
```

### Task 3: Documentation and Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/strategy-recommendation-layer.md`
- Modify: `.superpowers/sdd/progress.md` (git-ignored process ledger)

**Interfaces:**
- Consumes: verified implementation from Tasks 1 and 2
- Produces: exact migration-scope documentation and progress ledger entry

- [ ] **Step 1: Update README scope**

Update the `README.md` `Phase 1 Scope`, `Level 1A Status`, `Level 1A Python API`, `Paper Portfolio NAV v0 Status`, and `Continuous Run v0 Python API` wording to state:

- the one-shot `portfolio-nav` CLI and continuous-run NAV source handling can use `paper_trade_journal_records` when the local paper trade journal DB env is enabled
- continuous run as a whole is not fully DB-backed; only the NAV paper-trade source handling is migrated in this node
- JSONL remains legacy compatibility/export/replay and remains the input for outcome tracking, history/performance summary, cost audit, strategy audit, and observability/trend commands until separate migrations
- no live trading/auth/wallet/private keys/order mutation/account/exchange-state reads are introduced

- [ ] **Step 2: Update strategy layer docs**

Update `docs/strategy-recommendation-layer.md` `Data Flow` wording so it lists both one-shot `portfolio-nav` and continuous-run NAV source handling as DB-backed paper-trade read consumers when enabled, and keeps outcome/history/cost/strategy-audit/observability in the unmigrated list.

- [ ] **Step 3: Verify**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_runner.py tests/test_runner_scope.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src python3 -m pytest -q tests/test_cli.py tests/test_init.py tests/test_codex_node_push_policy_rules.py tests/test_project_database_persistence_rules.py
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' PYTHONPATH=.:src python3 -m pytest -q
PYTHONDONTWRITEBYTECODE=1 python3 -m compileall -q src tests
git diff --check
rg -n --hidden -g '!*.pyc' -g '!__pycache__/**' -g '!.git/**' -g '!.pytest_cache/**' -e 'ghp_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{20,}|sk-proj-[A-Za-z0-9_-]{20,}|sk-live-[A-Za-z0-9_-]{20,}|-----BEGIN (RSA |OPENSSH |EC |DSA |)PRIVATE KEY-----' . || true
codegraph sync
opencode run --dir /home/ubuntu/polymarket-alpha-lab -m zhipuai-coding-plan/glm-5.2 --variant max "<read-only post-node review prompt>"
```

- [ ] **Step 4: Commit and push**

This is a Codex implementation node, not an OMO/Sisyphus session. After all
checks and the configured post-node opencode review pass, follow the repository
Codex Node Push Policy: commit the focused node locally and push it to GitHub.
The `AGENTS.md` OMO/Sisyphus remote-pin section is explicitly labeled
`opencode only — codex ignores this section` and does not govern this Codex
node.

```bash
git add README.md docs/strategy-recommendation-layer.md docs/superpowers/plans/2026-06-30-run-nav-db-source.md src/polymarket_alpha_lab/runner.py src/polymarket_alpha_lab/cli.py tests/test_runner.py tests/test_runner_scope.py tests/test_cli.py
git commit -m "feat: add run nav paper trade db source"
git push origin main
```
