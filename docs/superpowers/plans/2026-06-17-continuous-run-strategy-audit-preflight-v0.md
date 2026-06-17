# Continuous Run Strategy Audit Preflight v0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an optional `run --strategy-audit-preflight` gate that blocks the continuous paper run before public client construction unless the existing local Strategy Risk Audit is `audit_ready`.

**Architecture:** Keep the feature in `src/polymarket_alpha_lab/cli.py`. Reuse `_run_strategy_audit(...)` to build the local audit from existing paper logs, print the audit summary, and only call `client_factory()` / `loop_runner(...)` when the status is `audit_ready`. Do not modify `runner.py` or `strategy_risk_audit.py`.

**Tech Stack:** Python stdlib argparse/pathlib/datetime/Decimal, existing frozen dataclasses, existing JSONL log readers, pytest.

---

### Task 1: RED CLI Behavior Tests

**Files:**
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Add helper for six-gate Strategy Risk Audit reports**

Add this helper near `_empty_run_summary()` in `tests/test_cli.py`:

```python
def _strategy_audit_report(status="audit_ready") -> PaperStrategyRiskAuditReport:
    statuses = {
        "audit_ready": ("pass", 6, 0, 0),
        "insufficient_evidence": ("incomplete", 0, 0, 6),
        "blocked_by_risk": ("fail", 0, 6, 0),
    }
    gate_status, pass_count, fail_count, incomplete_count = statuses[status]
    return PaperStrategyRiskAuditReport(
        generated_at=datetime(2026, 6, 17, 12, 0, tzinfo=UTC),
        config_version="strategy-risk-audit-v0",
        status=status,
        gate_count=6,
        pass_count=pass_count,
        fail_count=fail_count,
        incomplete_count=incomplete_count,
        gate_results=(
            PaperStrategyRiskAuditGateResult("paper_history", gate_status, "m"),
            PaperStrategyRiskAuditGateResult("settlement_evidence", gate_status, "m"),
            PaperStrategyRiskAuditGateResult("forecast_quality", gate_status, "m"),
            PaperStrategyRiskAuditGateResult("cost_discipline", gate_status, "m"),
            PaperStrategyRiskAuditGateResult("nav_drawdown", gate_status, "m"),
            PaperStrategyRiskAuditGateResult("open_exposure", gate_status, "m"),
        ),
    )
```

- [ ] **Step 2: Add allows-loop test**

Add:

```python
def test_run_cli_strategy_audit_preflight_allows_loop_when_audit_ready(tmp_path):
    audit_calls = []
    loop_calls = []

    def fake_strategy_audit_runner(
        *,
        cycle_log,
        trade_log,
        nav_log,
        outcome_log,
        cost_audit_report,
        config,
        generated_at,
    ):
        audit_calls.append(
            {
                "cycle_log": cycle_log,
                "trade_log": trade_log,
                "nav_log": nav_log,
                "outcome_log": outcome_log,
                "cost_audit_report": cost_audit_report,
                "config": config,
                "generated_at": generated_at,
            }
        )
        return _strategy_audit_report("audit_ready")

    def fake_loop_runner(**kwargs):
        loop_calls.append(kwargs)
        return _empty_run_summary()

    paper_journal = tmp_path / "paper-trades.jsonl"
    paper_journal.write_text("", encoding="utf-8")
    cycle_log = tmp_path / "cycles.jsonl"
    nav_log = tmp_path / "nav.jsonl"
    outcome_log = tmp_path / "outcomes.jsonl"

    exit_code = main(
        [
            "run",
            "--strategy-audit-preflight",
            "--paper-journal",
            str(paper_journal),
            "--cycle-log",
            str(cycle_log),
            "--nav-log",
            str(nav_log),
            "--outcome-log",
            str(outcome_log),
            "--starting-cash",
            "10000",
        ],
        strategy_audit_runner=fake_strategy_audit_runner,
        loop_runner=fake_loop_runner,
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 0
    assert len(audit_calls) == 1
    assert len(loop_calls) == 1
    assert audit_calls[0]["cycle_log"] == cycle_log
    assert audit_calls[0]["trade_log"] == paper_journal
    assert audit_calls[0]["nav_log"] == nav_log
    assert audit_calls[0]["outcome_log"] == outcome_log
    assert isinstance(audit_calls[0]["cost_audit_report"], PaperTradeCostAuditReport)
    assert loop_calls[0]["client"] == "fake-client"
```

- [ ] **Step 3: Add blocking test for non-ready statuses**

Add a parametrized test:

```python
@pytest.mark.parametrize("status", ("insufficient_evidence", "blocked_by_risk"))
def test_run_cli_strategy_audit_preflight_blocks_non_ready_audit(
    tmp_path,
    capsys,
    status,
):
    paper_journal = tmp_path / "paper-trades.jsonl"
    paper_journal.write_text("", encoding="utf-8")

    def fake_strategy_audit_runner(**kwargs):
        return _strategy_audit_report(status)

    def forbidden_client_factory():
        raise AssertionError("client should not be constructed")

    def forbidden_loop_runner(**kwargs):
        raise AssertionError("loop should not run")

    exit_code = main(
        [
            "run",
            "--strategy-audit-preflight",
            "--paper-journal",
            str(paper_journal),
            "--cycle-log",
            str(tmp_path / "cycles.jsonl"),
            "--nav-log",
            str(tmp_path / "nav.jsonl"),
            "--starting-cash",
            "10000",
        ],
        strategy_audit_runner=fake_strategy_audit_runner,
        loop_runner=forbidden_loop_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "strategy-audit:" in captured.out
    assert f"status={status}" in captured.out
    assert (
        f"run blocked by strategy audit preflight: status={status}"
        in captured.err
    )
```

- [ ] **Step 4: Add no-nav-log and audit-failure tests**

Add:

```python
def test_run_cli_strategy_audit_preflight_requires_nav_log(tmp_path, capsys):
    def forbidden_strategy_audit_runner(**kwargs):
        raise AssertionError("audit should not run")

    def forbidden_client_factory():
        raise AssertionError("client should not be constructed")

    def forbidden_loop_runner(**kwargs):
        raise AssertionError("loop should not run")

    exit_code = main(
        [
            "run",
            "--strategy-audit-preflight",
            "--paper-journal",
            str(tmp_path / "paper-trades.jsonl"),
            "--cycle-log",
            str(tmp_path / "cycles.jsonl"),
            "--starting-cash",
            "10000",
        ],
        strategy_audit_runner=forbidden_strategy_audit_runner,
        loop_runner=forbidden_loop_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "run failed: strategy audit preflight requires --nav-log" in captured.err
```

Add:

```python
def test_run_cli_strategy_audit_preflight_failure_does_not_construct_client(
    tmp_path,
    capsys,
):
    def forbidden_client_factory():
        raise AssertionError("client should not be constructed")

    def forbidden_loop_runner(**kwargs):
        raise AssertionError("loop should not run")

    exit_code = main(
        [
            "run",
            "--strategy-audit-preflight",
            "--paper-journal",
            str(tmp_path / "missing-trades.jsonl"),
            "--cycle-log",
            str(tmp_path / "cycles.jsonl"),
            "--nav-log",
            str(tmp_path / "nav.jsonl"),
            "--starting-cash",
            "10000",
        ],
        loop_runner=forbidden_loop_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "run failed:" in captured.err
```

- [ ] **Step 5: Run RED tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli.py -k "run_cli_strategy_audit_preflight" -q
```

Expected: tests fail because the parser does not know `--strategy-audit-preflight` / `--outcome-log` yet.

### Task 2: GREEN CLI Preflight

**Files:**
- Modify: `src/polymarket_alpha_lab/cli.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Add run parser flags**

In the `run_loop` parser setup in `src/polymarket_alpha_lab/cli.py`, add:

```python
    run_loop.add_argument(
        "--strategy-audit-preflight",
        action=argparse.BooleanOptionalAction,
        default=False,
        dest="strategy_audit_preflight",
    )
    run_loop.add_argument(
        "--outcome-log",
        type=Path,
        default=None,
        dest="outcome_log",
    )
```

- [ ] **Step 2: Add preflight before client construction**

In the `if args.command == "run":` branch, after `repeat_mode` and before
`summary = loop_runner(...)`, add:

```python
            if args.strategy_audit_preflight:
                if args.nav_log is None:
                    raise ValueError("strategy audit preflight requires --nav-log")
                audit_report = _run_strategy_audit(
                    cycle_log=args.cycle_log,
                    trade_log=args.paper_journal,
                    nav_log=args.nav_log,
                    outcome_log=args.outcome_log,
                    runner=strategy_audit_runner,
                )
                _print_strategy_audit_summary(audit_report)
                if audit_report.status != "audit_ready":
                    print(
                        "run blocked by strategy audit preflight: "
                        f"status={audit_report.status}",
                        file=sys.stderr,
                    )
                    return 1
```

Do not change `loop_runner(...)` arguments.

- [ ] **Step 3: Run GREEN tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli.py -k "run_cli_strategy_audit_preflight or run_cli_builds_loop_call_single_shot or run_cli_paper_execute_flag" -q
```

Expected: all selected tests pass.

### Task 3: Documentation And Boundary Tests

**Files:**
- Modify: `README.md`
- Modify: `docs/superpowers/specs/2026-06-16-continuous-run-v0.md`
- Modify: `docs/superpowers/specs/2026-06-17-strategy-audit-cli-v0.md`
- Modify: `docs/research/validation-gates.md`
- Modify: `docs/superpowers/specs/2026-06-13-automated-investment-roadmap.md`
- Modify: `tests/test_runner_scope.py`

- [ ] **Step 1: Strengthen README boundary test**

In `test_readme_runner_sections_keep_paper_boundaries`, add fragments:

```python
        "strategyauditpreflight",
        "locallogs",
        "auditready",
        "beforepublicclientconstruction",
```

Run:

```bash
.venv/bin/python -m pytest tests/test_runner_scope.py::test_readme_runner_sections_keep_paper_boundaries -q
```

Expected: fails until README is updated.

- [ ] **Step 2: Update README Continuous Run section**

Under `## Continuous Run v0 Status`, add a paragraph with this concept:

```markdown
The optional `run --strategy-audit-preflight` mode reads existing local paper
logs, builds the Strategy Risk Audit report, prints its local summary, and
blocks before public client construction unless the status is `audit_ready`.
It is a paper-only/report-only/read-only safety pause, not a default behavior
change, strategy-promotion signal, approval workflow, trade instruction,
investment ranking, recommendation, live-execution signal, or financial advice.
```

Under `## Continuous Run v0 CLI`, add a bullet for:

```markdown
- Add `--strategy-audit-preflight --nav-log <path> [--outcome-log <path>]`
  when a paper run should be gated by the latest local Strategy Risk Audit.
```

- [ ] **Step 3: Update specs and roadmap docs**

Update:

- `docs/superpowers/specs/2026-06-16-continuous-run-v0.md`: document optional preflight ordering before client construction and loop execution.
- `docs/superpowers/specs/2026-06-17-strategy-audit-cli-v0.md`: change "prints five gates" to "prints six gates" and note `run` can reuse local audit semantics as an optional preflight.
- `docs/research/validation-gates.md`: add a Phase 1 operational note that optional continuous paper-run preflight may pause new paper execution until the local Strategy Risk Audit is `audit_ready`.
- `docs/superpowers/specs/2026-06-13-automated-investment-roadmap.md`: add optional local audit gating to Level 1 capabilities while preserving no live orders/authenticated trading.

- [ ] **Step 4: Run docs/boundary tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_runner_scope.py tests/test_cli.py -q
```

Expected: all tests pass.

### Task 4: Verification And Commit

**Files:**
- All changed files in this node.

- [ ] **Step 1: Run targeted tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli.py tests/test_runner_scope.py -q
```

Expected: pass.

- [ ] **Step 2: Run full verification**

Run:

```bash
.venv/bin/python -m pytest -q
git diff --check
rg -n "ghp_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN (RSA |EC |OPENSSH |)PRIVATE KEY-----" --glob '!docs/superpowers/plans/**' --glob '!docs/superpowers/specs/**' .
codegraph sync && codegraph status .
```

Expected:

- pytest passes.
- `git diff --check` exits 0.
- `rg` exits 1 with no secret matches.
- CodeGraph reports index up to date.

- [ ] **Step 3: Claude review**

Stage the diff and run:

```bash
{ printf '%s\n\n' 'Review this staged diff for Phase 1 paper-only/report-only/read-only boundaries, run strategy audit preflight ordering before client construction, no runner.py or strategy_risk_audit.py scope creep, CLI behavior, tests, README/spec accuracy, and regression risk. Return Critical/Important/Minor findings; say Proceed if no Critical/Important.'; git diff --cached; } | claude --bare -p --model claude-opus-4-8 --effort max --permission-mode dontAsk --no-session-persistence --tools ""
```

Expected: `Proceed` or only Minor findings. Fix Critical/Important before commit.

- [ ] **Step 4: Commit**

Run:

```bash
git commit -m "feat: gate paper run with strategy audit"
```

Expected: local commit on `main`. Do not push `origin/main` unless the user explicitly overrides the repository rule keeping it pinned.
