# Cycle Snapshot DB Trend CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a read-only CLI command that summarizes paper recommendation cycle snapshot trends from Supabase/Postgres-backed snapshot history.

**Architecture:** Keep database access at the CLI edge and existing psycopg adapter boundary. The CLI reads `SupabaseCycleSnapshotConfig` from env, loads already-persisted `PaperRecommendationCycleSnapshotReport` rows through `load_paper_recommendation_cycle_snapshots_with_psycopg`, builds `PaperRecommendationCycleSnapshotTrendReport`, and prints summary fields only. Tests inject a fake trend runner and never require a real database.

**Tech Stack:** Python stdlib argparse, existing Supabase env config, existing psycopg load adapter, existing `build_paper_recommendation_cycle_snapshot_trend_report`, pytest, CodeGraph-first navigation, local OpenCode review.

---

## Strict Boundary

This node is paper-only, report-only, and read-only. It must not add live trading, authenticated exchange flows, wallet/private-key handling, account reads, order construction, signing, submission, cancellation, replacement, or exchange mutation paths.

The command prints aggregate counts and timestamps only. It must not print DSNs, table payload JSON, raw snapshot payloads, credentials, env files, or Supabase secrets.

The default psycopg loader already sanitizes connection failures into a generic
database error; this node relies on that adapter behavior and keeps CLI tests
focused on not echoing env DSN values from CLI-managed errors.

The store-backed loader returns rows in `generated_at DESC, inserted_at DESC,
snapshot_sha256 DESC` order. The CLI default helper must reverse that tuple
before calling the trend builder so equal-timestamp latest-status tie handling
matches the existing DB trend helper.

## Task 1: CLI Tests First

**Files:**
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Add imports and fake report usage**

Use the existing `SimpleNamespace`, `Decimal`, and `datetime` imports already present in `tests/test_cli.py`; no new third-party dependencies are needed.

- [ ] **Step 2: Add disabled-env failure test**

Add near existing trend/history CLI tests:

```python
def test_cycle_snapshot_db_trend_cli_requires_enabled_db_config(
    tmp_path,
    monkeypatch,
    capsys,
):
    monkeypatch.delenv("POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_ENABLED", raising=False)
    monkeypatch.delenv("POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_DSN", raising=False)

    def forbidden_runner(**kwargs):
        raise AssertionError("trend runner should not run")

    exit_code = main(
        ["cycle-snapshot-db-trend"],
        cycle_snapshot_db_trend_runner=forbidden_runner,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "cycle-snapshot-db-trend failed:" in captured.err
    assert "requires cycle snapshot DB to be enabled" in captured.err
```

- [ ] **Step 3: Add enabled-env happy-path test**

```python
def test_cycle_snapshot_db_trend_cli_reads_db_config_and_prints_summary(
    monkeypatch,
    capsys,
):
    monkeypatch.setenv("POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_ENABLED", "true")
    monkeypatch.setenv("POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_DSN", "test-dsn-value")
    monkeypatch.setenv(
        "POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_TABLE",
        "cycle_snapshot_archive",
    )
    calls = []

    def fake_trend_runner(
        *,
        dsn,
        generated_at,
        config_version,
        source_config_version,
        limit,
        table_name,
    ):
        calls.append(
            {
                "dsn": dsn,
                "generated_at": generated_at,
                "config_version": config_version,
                "source_config_version": source_config_version,
                "limit": limit,
                "table_name": table_name,
            },
        )
        return SimpleNamespace(
            snapshot_count=3,
            pass_count=1,
            watch_count=1,
            blocked_count=1,
            latest_status="blocked",
            first_generated_at=datetime(2026, 6, 19, 10, 0, tzinfo=UTC),
            last_generated_at=datetime(2026, 6, 19, 12, 0, tzinfo=UTC),
            blocked_share=Decimal("0.333333"),
            watch_share=Decimal("0.333333"),
            average_stage_count=Decimal("4.000000"),
            average_artifact_count=Decimal("7.000000"),
            paper_only=True,
            report_only=True,
            readonly=True,
        )

    exit_code = main(
        [
            "cycle-snapshot-db-trend",
            "--source-config-version",
            "paper-recommendation-cycle-snapshot-v0",
            "--limit",
            "25",
        ],
        cycle_snapshot_db_trend_runner=fake_trend_runner,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert len(calls) == 1
    assert calls[0]["dsn"] == "test-dsn-value"
    assert calls[0]["config_version"] == "cycle-snapshot-db-trend-v0"
    assert calls[0]["source_config_version"] == "paper-recommendation-cycle-snapshot-v0"
    assert calls[0]["limit"] == 25
    assert calls[0]["table_name"] == "cycle_snapshot_archive"
    assert isinstance(calls[0]["generated_at"], datetime)

    captured = capsys.readouterr()
    assert "cycle-snapshot-db-trend:" in captured.out
    assert "snapshots=3" in captured.out
    assert "pass=1" in captured.out
    assert "watch=1" in captured.out
    assert "blocked=1" in captured.out
    assert "latest_status=blocked" in captured.out
    assert "blocked_share=0.333333" in captured.out
    assert "test-dsn-value" not in captured.out
    assert "test-dsn-value" not in captured.err
```

- [ ] **Step 4: Add runner failure redaction test**

```python
def test_cycle_snapshot_db_trend_cli_runner_failure_redacts_dsn(
    monkeypatch,
    capsys,
):
    monkeypatch.setenv("POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_ENABLED", "true")
    monkeypatch.setenv("POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_DSN", "test-dsn-value")

    def broken_runner(**kwargs):
        raise RuntimeError("database unavailable")

    exit_code = main(
        ["cycle-snapshot-db-trend"],
        cycle_snapshot_db_trend_runner=broken_runner,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "cycle-snapshot-db-trend failed: database unavailable" in captured.err
    assert "test-dsn-value" not in captured.err
```

- [ ] **Step 5: Verify RED**

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_cli.py::test_cycle_snapshot_db_trend_cli_requires_enabled_db_config \
  tests/test_cli.py::test_cycle_snapshot_db_trend_cli_reads_db_config_and_prints_summary \
  tests/test_cli.py::test_cycle_snapshot_db_trend_cli_runner_failure_redacts_dsn \
  -q
```

Expected: fail because the subcommand and `cycle_snapshot_db_trend_runner` injection do not exist yet.

## Task 2: Implement CLI Command

**Files:**
- Modify: `src/polymarket_alpha_lab/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Add type alias and injection parameter**

Add imports:

```python
from polymarket_alpha_lab.paper_recommendation_cycle_snapshot_psycopg import (
    insert_paper_recommendation_cycle_snapshot_with_psycopg,
    load_paper_recommendation_cycle_snapshots_with_psycopg,
)
from polymarket_alpha_lab.paper_recommendation_cycle_snapshot_trend import (
    build_paper_recommendation_cycle_snapshot_trend_report,
)
```

Add:

```python
CycleSnapshotDbTrendRunner = Callable[..., object]
```

and `cycle_snapshot_db_trend_runner: CycleSnapshotDbTrendRunner | None = None` to `main(...)`.

- [ ] **Step 2: Add parser**

Add subparser:

```python
cycle_snapshot_db_trend = subparsers.add_parser("cycle-snapshot-db-trend")
cycle_snapshot_db_trend.add_argument(
    "--source-config-version",
    default=None,
    dest="source_config_version",
)
cycle_snapshot_db_trend.add_argument("--limit", type=int, default=50)
```

- [ ] **Step 3: Add command branch before `run` or near other history/trend commands**

Branch behavior:

```python
if args.command == "cycle-snapshot-db-trend":
    try:
        report = _run_cycle_snapshot_db_trend(
            source_config_version=args.source_config_version,
            limit=args.limit,
            runner=cycle_snapshot_db_trend_runner,
        )
        _print_cycle_snapshot_db_trend_summary(report)
        return 0
    except Exception as exc:
        print(f"cycle-snapshot-db-trend failed: {exc}", file=sys.stderr)
        return 1
```

- [ ] **Step 4: Add helper**

```python
def _run_cycle_snapshot_db_trend(
    *,
    source_config_version: str | None,
    limit: int,
    runner: CycleSnapshotDbTrendRunner | None,
) -> object:
    if isinstance(limit, bool) or limit < 1:
        raise ValueError("limit must be a positive integer")
    db_config = from_cycle_snapshot_db_env()
    if not db_config.enabled:
        raise ValueError("cycle-snapshot-db-trend requires cycle snapshot DB to be enabled")
    if db_config.dsn is None:
        raise ValueError("cycle-snapshot-db-trend requires a DB DSN")
    generated_at = datetime.now(UTC)
    config_version = "cycle-snapshot-db-trend-v0"
    if runner is not None:
        return runner(
            dsn=db_config.dsn,
            generated_at=generated_at,
            config_version=config_version,
            source_config_version=source_config_version,
            limit=limit,
            table_name=db_config.table_name,
        )
    snapshots = load_paper_recommendation_cycle_snapshots_with_psycopg(
        db_config.dsn,
        config_version=source_config_version,
        limit=limit,
        table_name=db_config.table_name,
    )
    if not snapshots:
        raise ValueError("no paper recommendation cycle snapshots found")
    # Store-backed loaders return newest-first; the trend builder expects
    # chronological input so equal-timestamp latest-status tie handling is stable.
    return build_paper_recommendation_cycle_snapshot_trend_report(
        generated_at=generated_at,
        config_version=config_version,
        snapshots=tuple(reversed(snapshots)),
    )
```

- [ ] **Step 5: Add summary printer**

```python
def _print_cycle_snapshot_db_trend_summary(report: object) -> None:
    print(
        "cycle-snapshot-db-trend: "
        f"snapshots={report.snapshot_count} "
        f"pass={report.pass_count} "
        f"watch={report.watch_count} "
        f"blocked={report.blocked_count} "
        f"latest_status={report.latest_status} "
        f"first={report.first_generated_at.isoformat()} "
        f"last={report.last_generated_at.isoformat()} "
        f"blocked_share={report.blocked_share} "
        f"watch_share={report.watch_share} "
        f"avg_stage_count={report.average_stage_count} "
        f"avg_artifact_count={report.average_artifact_count}",
    )
```

Do not print DSN, table name, env values, or raw payloads.

- [ ] **Step 6: Verify GREEN**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli.py -q
```

## Task 3: Verification, Review, Commit, Push

- [ ] **Step 1: Focused tests**

```bash
.venv/bin/python -m pytest \
  tests/test_cli.py \
  tests/test_paper_recommendation_cycle_snapshot_db_trend.py \
  tests/test_paper_recommendation_cycle_snapshot_psycopg.py \
  tests/test_supabase_cycle_snapshot_config.py \
  -q
```

- [ ] **Step 2: Repository gates**

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m compileall -q src tests
git diff --check
codegraph sync
codegraph status .
```

- [ ] **Step 3: Secret scan**

```bash
rg -n "ghp_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,}|postgresql:/{2}[^[:space:]]+|-----BEGIN [A-Z ]*PRIVATE KEY-----" \
  src/polymarket_alpha_lab/cli.py tests/test_cli.py docs/superpowers/plans/2026-06-19-cycle-snapshot-db-trend-cli-node.md
```

- [ ] **Step 4: OpenCode post-stage review**

Run local OpenCode with `zhipuai-coding-plan/glm-5.2`, `--variant max`, and a read-only prompt.

- [ ] **Step 5: Commit and push**

After all gates pass, follow the current `AGENTS.md` Codex Node Push Policy:
push a completed Codex node after focused tests, full tests, compile,
diff-check, CodeGraph sync, secret scan, and OpenCode post-stage review pass.
The older OMO/Sisyphus remote-pin section is explicitly scoped to opencode only
and Codex ignores it.

```bash
git add src/polymarket_alpha_lab/cli.py tests/test_cli.py docs/superpowers/plans/2026-06-19-cycle-snapshot-db-trend-cli-node.md
git commit -m "Add cycle snapshot DB trend CLI"
git push origin main
```
