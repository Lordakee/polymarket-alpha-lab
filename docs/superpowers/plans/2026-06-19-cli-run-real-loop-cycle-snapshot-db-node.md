# CLI Run Real Loop Cycle Snapshot DB Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add no-network coverage proving `polymarket-alpha-lab run` uses the real default loop, default cycle snapshot source, and injected DB sink when cycle snapshot DB persistence is enabled.

**Architecture:** This is a coverage-hardening node. The test exercises the existing CLI `run` branch with a fake public market-data client and fake DB sink, while leaving production code unchanged unless the test exposes a real wiring defect.

**Tech Stack:** Python, pytest, local fake Gamma/CLOB payloads, existing `main(...)`, real `run_strategy_loop`, real `run_strategy_cycle`, real `build_strategy_cycle_snapshot_source_report`.

---

### Task 1: Real CLI Run DB Snapshot Path Test

**Files:**
- Modify: `tests/test_cli.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Add the failing integration-style test**

Add the test in the existing `run` CLI section near `test_run_cli_uses_default_cycle_snapshot_source_when_db_enabled_without_injection`.

```python
def test_run_cli_default_loop_persists_cycle_snapshot_with_fake_client(
    tmp_path,
    monkeypatch,
    capsys,
):
    monkeypatch.setenv("POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_ENABLED", "true")
    monkeypatch.setenv("POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_DSN", "test-dsn-value")
    monkeypatch.setenv(
        "POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_TABLE",
        "cycle_snapshot_archive",
    )
    market = _run_cli_raw_market(
        condition_id="0xcondCliRun",
        slug="cli-run-market",
        question="Will the CLI run path persist a snapshot?",
        token_ids=("yes-cli-run", "no-cli-run"),
    )
    books = {
        "yes-cli-run": _run_cli_raw_book(
            "yes-cli-run",
            bid="0.5300",
            ask="0.5500",
            size="100.0000",
        ),
        "no-cli-run": _run_cli_raw_book(
            "no-cli-run",
            bid="0.3700",
            ask="0.4000",
            size="100.0000",
        ),
    }
    client = _RunCliFakeMarketDataClient([market], books)
    sink_calls = []

    def fake_cycle_snapshot_sink(*, dsn, report, table_name):
        sink_calls.append((dsn, report, table_name))

    cycle_log = tmp_path / "cycle.jsonl"

    exit_code = main(
        [
            "run",
            "--limit",
            "1",
            "--max-markets",
            "1",
            "--archive-root",
            str(tmp_path / "raw"),
            "--starting-cash",
            "10000",
            "--cycle-log",
            str(cycle_log),
            "--nav-log",
            str(tmp_path / "nav.jsonl"),
            "--max-iterations",
            "1",
        ],
        client_factory=lambda: client,
        cycle_snapshot_db_sink=fake_cycle_snapshot_sink,
    )

    assert exit_code == 0
    assert len(sink_calls) == 1
    dsn, report, table_name = sink_calls[0]
    assert dsn == "test-dsn-value"
    assert table_name == "cycle_snapshot_archive"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.stage_count == 4
    assert client.list_markets_calls == [
        {"active": True, "closed": False, "limit": 1, "search": None},
    ]
    assert client.get_order_book_calls == [
        "yes-cli-run",
        "no-cli-run",
    ]
    assert len(PaperStrategyCycleLog.read(cycle_log)) == 1

    captured = capsys.readouterr()
    assert "cycle_snapshots_persisted=1" in captured.out
    assert "test-dsn-value" not in captured.out
    assert "test-dsn-value" not in captured.err
```

If this test needs local helpers, define them in `tests/test_cli.py` instead of importing from `tests.test_runner`:

```python
def _run_cli_raw_market(
    *,
    condition_id: str,
    slug: str,
    question: str,
    token_ids: tuple[str, ...],
):
    return {
        "conditionId": condition_id,
        "outcomes": ["Yes", "No"],
        "clobTokenIds": list(token_ids),
        "slug": slug,
        "question": question,
        "active": True,
        "closed": False,
        "acceptingOrders": True,
        "enableOrderBook": True,
        "volume24hr": "5000",
        "liquidity": "10000",
        "description": "Market resolves according to the public source.",
        "resolutionSource": "public-source",
    }


def _run_cli_raw_book(
    token_id: str,
    *,
    bid: str,
    ask: str,
    size: str,
):
    return {
        "asset_id": token_id,
        "bids": [{"price": bid, "size": size}],
        "asks": [{"price": ask, "size": size}],
    }


class _RunCliFakeMarketDataClient:
    def __init__(self, markets, books):
        self._markets = list(markets)
        self._books = dict(books)
        self.list_markets_calls = []
        self.get_order_book_calls = []

    def list_markets(self, *, active, closed, limit, search=None):
        self.list_markets_calls.append(
            {"active": active, "closed": closed, "limit": limit, "search": search},
        )
        return list(self._markets)

    def get_order_book(self, *, token_id):
        self.get_order_book_calls.append(token_id)
        return self._books[token_id]
```

- [ ] **Step 2: Run the new test to observe RED or immediate coverage pass**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli.py::test_run_cli_default_loop_persists_cycle_snapshot_with_fake_client -q
```

Expected if production wiring is incomplete: FAIL showing no snapshot persisted, missing sink call, or missing log path.

Expected if current production wiring already satisfies the requirement: PASS. In that case this remains a test-only coverage-hardening node; do not modify production code to manufacture a failure.

- [ ] **Step 3: If needed, write the minimal production fix**

Only if Step 2 fails for a real wiring defect, minimally adjust `src/polymarket_alpha_lab/cli.py` so the `run` command passes `build_strategy_cycle_snapshot_source_report` to `run_strategy_loop` when DB config is enabled and no injected source exists.

- [ ] **Step 4: Run focused verification**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli.py::test_run_cli_default_loop_persists_cycle_snapshot_with_fake_client tests/test_cli.py::test_run_cli_uses_default_cycle_snapshot_source_when_db_enabled_without_injection tests/test_runner.py -q
```

Expected: all selected tests pass.

- [ ] **Step 5: Run branch gates**

Run:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m compileall -q src tests
git diff --check
codegraph sync
codegraph status .
```

Expected: full suite passes, compile succeeds, diff has no whitespace errors, CodeGraph is up to date.

- [ ] **Step 6: Review, commit, and push when authorized**

Run OpenCode review:

```bash
opencode run -m zhipuai-coding-plan/glm-5.2 --variant max --dir /home/ubuntu/polymarket-alpha-lab -- "<read-only review prompt>"
```

If review has no critical or important issues, commit locally. Push only when the
current user/project instructions explicitly authorize pushing completed nodes;
this session has that authorization.

```bash
git add tests/test_cli.py docs/superpowers/plans/2026-06-19-cli-run-real-loop-cycle-snapshot-db-node.md
git commit -m "Add CLI run cycle snapshot DB integration coverage"
git push origin main
```

---

## Outcome

- Step 2 outcome: the new CLI run integration test passed against the existing
  production wiring on its first run, so this node is coverage hardening.
- Step 3 outcome: no production fix was needed and no `src/` files were changed.
- Implemented test name:
  `test_run_cli_default_loop_persists_default_snapshot_report_from_real_cycle`.
- The implemented test uses a local fake market-data client and injected fake DB
  sink, while leaving the default `loop_runner` and default
  `cycle_snapshot_source` untouched so the real
  `run_strategy_loop -> run_strategy_cycle -> build_strategy_cycle_snapshot_source_report`
  path is exercised.
