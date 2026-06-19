# Runner CLI Cycle Snapshot DB Wiring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add opt-in runner and CLI wiring that can persist already-built `PaperRecommendationCycleSnapshotReport` objects to the existing Supabase/Postgres adapter without changing strategy-cycle semantics.

**Architecture:** `run_strategy_loop` remains the paper-only/read-only loop owner and keeps JSONL cycle reports. A new optional `cycle_snapshot_source` callable returns a real `PaperRecommendationCycleSnapshotReport` for a completed `PaperStrategyCycleReport`; a new optional `cycle_snapshot_sink` persists that snapshot. The default path leaves both unset, preserving all current behavior and avoiding fake snapshots because `PaperStrategyCycleReport` does not contain the pipeline and artifact-index inputs required by `build_paper_recommendation_cycle_snapshot_report`.

**Tech Stack:** Python stdlib typing/protocols, frozen dataclasses, existing DB adapter `insert_paper_recommendation_cycle_snapshot_with_psycopg`, pytest, CodeGraph-first navigation, local OpenCode review.

---

## Current Facts

- `src/polymarket_alpha_lab/runner.py` currently calls `run_strategy_cycle`, appends `PaperStrategyCycleLog`, optionally marks NAV, and returns `RunLoopSummary`.
- `RunLoopSummary` currently enforces `paper_only is True` and `report_only is True`.
- `PaperRecommendationCycleSnapshotReport` is built from `PaperRecommendationPipelineReport` plus `PaperRecommendationArtifactIndexReport`, not from `PaperStrategyCycleReport`.
- `src/polymarket_alpha_lab/paper_recommendation_cycle_snapshot_psycopg.py` exposes `insert_paper_recommendation_cycle_snapshot_with_psycopg(dsn, report, *, table_name=...)`.
- `src/polymarket_alpha_lab/supabase_cycle_snapshot_config.py` exposes `from_cycle_snapshot_db_env(env=None)` and redacts DSNs in `SupabaseCycleSnapshotConfig.__repr__`.

## Strict Boundary

This node is paper-only, report-only, and read-only. It must not add live trading, authenticated exchange flows, wallet/private-key handling, account reads, order construction, signing, submission, cancellation, replacement, or exchange mutation paths.

## Task 1: Runner Source/Sink API

**Files:**
- Modify: `tests/test_runner.py`
- Modify: `src/polymarket_alpha_lab/runner.py`

- [ ] **Step 1: Write failing runner tests**

Add tests near the existing runner behavior tests:

```python
@dataclass(frozen=True)
class CycleSnapshotShape:
    generated_at: datetime
    config_version: str = "cycle-snapshot-test-v0"
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def test_cycle_snapshot_source_and_sink_run_once_per_completed_iteration(tmp_path):
    market, books = _screening_ready_market_and_books()
    client = FakeMarketDataClient([market], books)
    source_calls = []
    sink_calls = []

    def cycle_snapshot_source(*, cycle_report, iteration_started_at):
        source_calls.append((cycle_report, iteration_started_at))
        return CycleSnapshotShape(generated_at=iteration_started_at)

    def cycle_snapshot_sink(snapshot):
        sink_calls.append(snapshot)

    with patch("polymarket_alpha_lab.runner.time.sleep"):
        summary = run_strategy_loop(
            client=client,
            scan_config=scan_config(tmp_path),
            cycle_config=cycle_config(),
            starting_cash=Decimal("10000"),
            nav_log_path=tmp_path / "nav.jsonl",
            cycle_report_log_path=tmp_path / "cycle.jsonl",
            repeat_mode="interval",
            interval_seconds=0,
            max_iterations=2,
            cycle_snapshot_source=cycle_snapshot_source,
            cycle_snapshot_sink=cycle_snapshot_sink,
        )

    assert summary.iterations_completed == 2
    assert summary.iterations_failed == 0
    assert summary.cycle_snapshots_persisted == 2
    assert len(source_calls) == 2
    assert len(sink_calls) == 2
    assert all(snapshot.paper_only is True for snapshot in sink_calls)
    assert all(snapshot.report_only is True for snapshot in sink_calls)
    assert all(snapshot.readonly is True for snapshot in sink_calls)
```

Add a second test proving default behavior does not call snapshot wiring:

```python
def test_cycle_snapshot_sink_is_inert_without_source(tmp_path):
    market, books = _screening_ready_market_and_books()
    sink_calls = []

    summary = run_strategy_loop(
        client=FakeMarketDataClient([market], books),
        scan_config=scan_config(tmp_path),
        cycle_config=cycle_config(),
        starting_cash=Decimal("10000"),
        nav_log_path=tmp_path / "nav.jsonl",
        cycle_report_log_path=tmp_path / "cycle.jsonl",
        cycle_snapshot_sink=lambda snapshot: sink_calls.append(snapshot),
    )

    assert summary.iterations_completed == 1
    assert summary.cycle_snapshots_persisted == 0
    assert sink_calls == []
```

Add a third test proving DB-first failures fail the iteration under the current `on_cycle_error` policy:

```python
def test_cycle_snapshot_sink_failure_counts_as_iteration_failure(tmp_path):
    market, books = _screening_ready_market_and_books()

    def cycle_snapshot_source(*, cycle_report, iteration_started_at):
        return CycleSnapshotShape(generated_at=iteration_started_at)

    def broken_cycle_snapshot_sink(snapshot):
        raise RuntimeError("snapshot db unavailable")

    summary = run_strategy_loop(
        client=FakeMarketDataClient([market], books),
        scan_config=scan_config(tmp_path),
        cycle_config=cycle_config(),
        starting_cash=Decimal("10000"),
        nav_log_path=tmp_path / "nav.jsonl",
        cycle_report_log_path=tmp_path / "cycle.jsonl",
        cycle_snapshot_source=cycle_snapshot_source,
        cycle_snapshot_sink=broken_cycle_snapshot_sink,
        on_cycle_error="log_and_continue",
    )

    assert summary.iterations_completed == 0
    assert summary.iterations_failed == 1
    assert summary.cycle_snapshots_persisted == 0
    assert summary.last_error == "RuntimeError: snapshot db unavailable"
```

Add validation cases to the existing invalid-param test:

```python
({"cycle_snapshot_source": object()}, "cycle_snapshot_source must be callable or None"),
({"cycle_snapshot_sink": object()}, "cycle_snapshot_sink must be callable or None"),
```

- [ ] **Step 2: Run runner tests to verify RED**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_runner.py::test_cycle_snapshot_source_and_sink_run_once_per_completed_iteration \
  tests/test_runner.py::test_cycle_snapshot_sink_is_inert_without_source \
  tests/test_runner.py::test_cycle_snapshot_sink_failure_counts_as_iteration_failure \
  -q
```

Expected: FAIL because `run_strategy_loop` does not yet accept `cycle_snapshot_source`, `cycle_snapshot_sink`, or return `cycle_snapshots_persisted`.

- [ ] **Step 3: Implement minimal runner wiring**

In `runner.py`:

- Add optional keyword-only params:
  - `cycle_snapshot_source: Callable[..., object] | None = None`
  - `cycle_snapshot_sink: Callable[[object], object] | None = None`
- Add `cycle_snapshots_persisted: int = 0` to `RunLoopSummary` and validate it as nonnegative.
- After `PaperStrategyCycleLog(...).append(report)`, call the source only when both source and sink are present:

```python
if cycle_snapshot_source is not None and cycle_snapshot_sink is not None:
    cycle_snapshot = cycle_snapshot_source(
        cycle_report=report,
        iteration_started_at=iteration_at,
    )
    _require_snapshot_safety_flags(cycle_snapshot)
    cycle_snapshot_sink(cycle_snapshot)
    cycle_snapshots_persisted += 1
```

- Keep the snapshot source/sink call inside the existing iteration `try`, so failures follow `on_cycle_error`.
- Do not import DB modules in `runner.py`.
- Define `_require_snapshot_safety_flags(snapshot: object) -> None` in `runner.py`:

```python
def _require_snapshot_safety_flags(snapshot: object) -> None:
    if getattr(snapshot, "paper_only", None) is not True:
        raise ValueError("cycle snapshot must be paper_only")
    if getattr(snapshot, "report_only", None) is not True:
        raise ValueError("cycle snapshot must be report_only")
    if getattr(snapshot, "readonly", None) is not True:
        raise ValueError("cycle snapshot must be readonly")
```

- [ ] **Step 4: Run runner focused tests to verify GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_runner.py -q
```

Expected: all runner tests pass.

## Task 2: CLI Env And Adapter Wiring

**Files:**
- Modify: `tests/test_cli.py`
- Modify: `src/polymarket_alpha_lab/cli.py`

- [ ] **Step 1: Write failing CLI tests**

Add tests near the existing `run` CLI tests:

```python
def test_run_cli_leaves_cycle_snapshot_db_disabled_by_default(tmp_path, monkeypatch):
    monkeypatch.delenv("POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_ENABLED", raising=False)
    monkeypatch.delenv("POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_DSN", raising=False)
    calls = []

    def fake_loop_runner(**kwargs):
        calls.append(kwargs)
        return _empty_run_summary()

    exit_code = main(
        [
            "run",
            "--archive-root",
            str(tmp_path / "raw"),
            "--starting-cash",
            "10000",
            "--cycle-log",
            str(tmp_path / "cycle.jsonl"),
        ],
        loop_runner=fake_loop_runner,
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 0
    assert len(calls) == 1
    assert calls[0]["cycle_snapshot_source"] is None
    assert calls[0]["cycle_snapshot_sink"] is None
```

Add an enabled-env test that injects a source and fake DB sink without a real database:

```python
def test_run_cli_wires_cycle_snapshot_db_sink_when_env_enabled(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv("POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_ENABLED", "true")
    monkeypatch.setenv(
        "POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_DSN",
        "test-dsn-value",
    )
    monkeypatch.setenv(
        "POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_TABLE",
        "cycle_snapshot_archive",
    )
    calls = []
    sink_calls = []
    source_value = SimpleNamespace(paper_only=True, report_only=True, readonly=True)

    def fake_loop_runner(**kwargs):
        calls.append(kwargs)
        assert kwargs["cycle_snapshot_source"] is not None
        snapshot = kwargs["cycle_snapshot_source"](
            cycle_report=object(),
            iteration_started_at=datetime(2026, 6, 19, 12, 0, tzinfo=UTC),
        )
        kwargs["cycle_snapshot_sink"](snapshot)
        return RunLoopSummary(
            iterations_completed=1,
            iterations_failed=0,
            first_iteration_at=datetime(2026, 6, 19, 12, 0, tzinfo=UTC),
            last_iteration_at=datetime(2026, 6, 19, 12, 0, tzinfo=UTC),
            last_error=None,
            cycle_snapshots_persisted=1,
        )

    def fake_cycle_snapshot_source(*, cycle_report, iteration_started_at):
        return source_value

    def fake_cycle_snapshot_sink(*, dsn, report, table_name):
        sink_calls.append((dsn, report, table_name))

    exit_code = main(
        [
            "run",
            "--archive-root",
            str(tmp_path / "raw"),
            "--starting-cash",
            "10000",
            "--cycle-log",
            str(tmp_path / "cycle.jsonl"),
        ],
        loop_runner=fake_loop_runner,
        client_factory=lambda: "fake-client",
        cycle_snapshot_source=fake_cycle_snapshot_source,
        cycle_snapshot_db_sink=fake_cycle_snapshot_sink,
    )

    assert exit_code == 0
    assert len(calls) == 1
    assert sink_calls == [
        (
            "test-dsn-value",
            source_value,
            "cycle_snapshot_archive",
        ),
    ]
```

Add a missing-source test:

```python
def test_run_cli_rejects_enabled_cycle_snapshot_db_without_source(
    tmp_path,
    monkeypatch,
    capsys,
):
    monkeypatch.setenv("POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_ENABLED", "true")
    monkeypatch.setenv(
        "POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_DSN",
        "test-dsn-value",
    )

    exit_code = main(
        [
            "run",
            "--archive-root",
            str(tmp_path / "raw"),
            "--starting-cash",
            "10000",
            "--cycle-log",
            str(tmp_path / "cycle.jsonl"),
        ],
        loop_runner=lambda **kwargs: _empty_run_summary(),
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "cycle snapshot DB persistence requires a cycle snapshot source" in captured.err
    assert "test-dsn-value" not in captured.err
```

- [ ] **Step 2: Run CLI tests to verify RED**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_cli.py::test_run_cli_leaves_cycle_snapshot_db_disabled_by_default \
  tests/test_cli.py::test_run_cli_wires_cycle_snapshot_db_sink_when_env_enabled \
  tests/test_cli.py::test_run_cli_rejects_enabled_cycle_snapshot_db_without_source \
  -q
```

Expected: FAIL because `main` does not yet accept `cycle_snapshot_source` or `cycle_snapshot_db_sink`, and run does not pass snapshot args into `loop_runner`.

- [ ] **Step 3: Implement minimal CLI wiring**

In `cli.py`:

- Import `from_cycle_snapshot_db_env`.
- Add type aliases:
  - `CycleSnapshotSource = Callable[..., object]`
  - `CycleSnapshotDbSink = Callable[..., object]`
- Add `cycle_snapshot_source: CycleSnapshotSource | None = None` and `cycle_snapshot_db_sink: CycleSnapshotDbSink = insert_paper_recommendation_cycle_snapshot_with_psycopg` to `main`.
- At the `run` command branch, load DB config with `from_cycle_snapshot_db_env()`.
- If config is disabled, pass `cycle_snapshot_source=None` and `cycle_snapshot_sink=None` to `loop_runner`.
- If config is enabled and `cycle_snapshot_source is None`, raise `ValueError("cycle snapshot DB persistence requires a cycle snapshot source")`.
- If config is enabled, build a closure:

```python
def cycle_snapshot_sink(report: object) -> object:
    return cycle_snapshot_db_sink(
        dsn=db_config.dsn,
        report=report,
        table_name=db_config.table_name,
    )
```

- Pass both `cycle_snapshot_source` and `cycle_snapshot_sink` into `loop_runner`.
- Update `_print_run_loop_summary` to include `cycle_snapshots_persisted=<count>` when the summary has the field.
- Do not print DB config, DSN, table payloads, or raw snapshot JSON.

- [ ] **Step 4: Run CLI focused tests to verify GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli.py -q
```

Expected: all CLI tests pass.

## Task 3: Verification, Review, Commit, Push

**Files:**
- Modify only if needed after review: `docs/superpowers/plans/2026-06-19-runner-cli-cycle-snapshot-db-wiring-node.md`

- [ ] **Step 1: Focused verification**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_runner.py \
  tests/test_cli.py \
  tests/test_supabase_cycle_snapshot_config.py \
  tests/test_paper_recommendation_cycle_snapshot_psycopg.py \
  -q
```

- [ ] **Step 2: Repository verification**

Run:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m compileall -q src tests
git diff --check
codegraph status .
```

- [ ] **Step 3: Boundary and secret scan**

Run:

```bash
rg -n "ghp_|postgresql:/{2}[^[:space:]]+|private.?key|wallet|sign|submit|cancel|service.?role" \
  src tests docs AGENTS.md
```

- [ ] **Step 4: OpenCode post-stage review**

Run local OpenCode from repo root:

```bash
opencode run -m zhipuai-coding-plan/glm-5.2 --variant max --dir /home/ubuntu/polymarket-alpha-lab -- "<read-only review prompt>"
```

The prompt must include: `DO NOT modify/create/delete ANY file; output ONLY verdict + findings.`

- [ ] **Step 5: Commit and push**

After all gates pass, follow the current `AGENTS.md` Codex Node Push Policy:
push a completed Codex node only after focused tests, full tests, compile,
diff-check, CodeGraph sync, secret scan, and OpenCode post-stage review pass.
The older OMO/Sisyphus remote-pin section is explicitly scoped to opencode only
and Codex ignores it.

```bash
git add \
  docs/superpowers/plans/2026-06-19-runner-cli-cycle-snapshot-db-wiring-node.md \
  src/polymarket_alpha_lab/runner.py \
  src/polymarket_alpha_lab/cli.py \
  tests/test_runner.py \
  tests/test_cli.py
git commit -m "Add cycle snapshot DB runner wiring"
git push origin main
```
