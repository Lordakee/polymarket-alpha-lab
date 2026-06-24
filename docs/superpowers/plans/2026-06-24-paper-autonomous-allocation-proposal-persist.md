# Paper Autonomous Allocation Proposal Persist Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a separate paper-only/report-only/read-only persisted handoff producer for `PaperAutonomousAllocationProposalReport` while keeping the existing `paper-autonomous-allocation-proposal` CLI no-write.

**Architecture:** Mirror the completed autonomous screening gate split: the default allocation proposal command remains env-only and read-only, while a sibling `paper-autonomous-allocation-proposal-persist` command builds the same final report and persists only that final report through the existing allocation proposal DB config and psycopg store. The node reuses the existing reducer, read loader, store, env config, migration, and psycopg writer; implementation work is limited to CLI wiring, redaction tests, docs, and handoff ledger.

**Tech Stack:** Python 3.12, argparse CLI, frozen dataclasses, `Decimal`-only finance values, existing `paper_autonomous_allocation_proposal_*` store/psycopg/config modules, Supabase/Postgres env config, pytest, CodeGraph, OpenCode review with `zhipuai-coding-plan/glm-5.2` and variant `max`.

## Global Constraints

- Preserve Phase 1 boundary: no live trading, no auth, no key handling, no wallet handling, no account handling, no account reads, no order construction, no order signing, no order submission, no order cancellation, no order replacement, no exchange mutation.
- The existing `paper-autonomous-allocation-proposal --limit 25` command remains no-write/read-only and must not accept `--persist`, `--dsn`, `--table`, `--trade`, `--execute`, or approval/order flags.
- The new `paper-autonomous-allocation-proposal-persist --limit 25` command accepts only `--limit`; all DB targets are read from existing env config modules.
- The producer may persist only the final `PaperAutonomousAllocationProposalReport` to the allocation proposal DB. It must not repair or create upstream reports.
- Upstream read DBs remain required: autonomous screening gate DB, action-gated queue decision-support DB, and action-gated queue DB.
- Allocation proposal output DB is required only for the `-persist` command and must be validated before the runner or sink is invoked.
- Use existing allocation proposal persistence modules: do not add a second store, migration, or env config for the same table.
- Any persistence error must redact DSNs, table names, payload JSON, hashes, questions, and market slugs from operator output.
- Use `.venv/bin/python -m pytest`, not bare `pytest`.
- Do not use fast mode.
- Reviews go directly to OpenCode with model `zhipuai-coding-plan/glm-5.2` and variant `max`.

---

### Task 1: CLI Contract Tests For Persisted Allocation Producer

**Files:**
- Modify: `tests/test_cli_paper_autonomous_allocation_proposal_scope.py`
- Modify: `tests/test_cli.py`

**Interfaces:**
- Consumes existing `cli.main(...)`.
- Produces tests for `paper-autonomous-allocation-proposal-persist`, sink injection, env guard order, redaction, and parser flag boundaries.

- [ ] **Step 1: Write failing command constant and env helper extension**

Add the allocation proposal DB env imports:

```python
from polymarket_alpha_lab.supabase_paper_autonomous_allocation_proposal_config import (
    PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_DSN_ENV_VAR,
    PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_ENABLED_ENV_VAR,
    PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_TABLE_ENV_VAR,
)
```

Add:

```python
PERSIST_COMMAND = "paper-autonomous-allocation-proposal-persist"
```

Add helper:

```python
def _set_allocation_proposal_db_env(
    monkeypatch: pytest.MonkeyPatch,
    *,
    proposal_dsn: str = "postgresql://allocation-proposal.example.invalid/db",
    proposal_table_name: str = "paper_autonomous_allocation_proposal_reports",
) -> None:
    monkeypatch.setenv(
        PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_ENABLED_ENV_VAR,
        "true",
    )
    monkeypatch.setenv(
        PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_DSN_ENV_VAR,
        proposal_dsn,
    )
    monkeypatch.setenv(
        PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_TABLE_ENV_VAR,
        proposal_table_name,
    )
```

- [ ] **Step 2: Write failing happy-path injected sink test**

Add a test named `test_allocation_persist_cli_uses_injected_runner_sink_and_prints_persistence_marker`:

```python
def test_allocation_persist_cli_uses_injected_runner_sink_and_prints_persistence_marker(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    screening_gate_dsn = "postgresql://screening.example.invalid/db"
    decision_support_dsn = "postgresql://decision.example.invalid/db"
    source_queue_dsn = "postgresql://source.example.invalid/db"
    proposal_dsn = "postgresql://allocation-proposal.example.invalid/db"
    proposal_table_name = "paper_autonomous_allocation_proposal_reports"
    report = _proposal_report()
    runner_calls: list[dict[str, object]] = []
    sink_calls: list[dict[str, object]] = []

    _set_upstream_db_env(
        monkeypatch,
        screening_gate_dsn=screening_gate_dsn,
        decision_support_dsn=decision_support_dsn,
        source_queue_dsn=source_queue_dsn,
    )
    _set_allocation_proposal_db_env(
        monkeypatch,
        proposal_dsn=proposal_dsn,
        proposal_table_name=proposal_table_name,
    )

    def fake_runner(**kwargs: object) -> object:
        runner_calls.append(dict(kwargs))
        return report

    def fake_sink(**kwargs: object) -> object:
        sink_calls.append(dict(kwargs))
        return SimpleNamespace(inserted=True)

    exit_code = main(
        [PERSIST_COMMAND, "--limit", "25"],
        paper_autonomous_allocation_proposal_runner=fake_runner,
        paper_autonomous_allocation_proposal_db_sink=fake_sink,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed")
        ),
    )

    assert exit_code == 0
    assert len(runner_calls) == 1
    assert len(sink_calls) == 1
    assert sink_calls[0] == {
        "dsn": proposal_dsn,
        "report": report,
        "table_name": proposal_table_name,
    }
    captured = capsys.readouterr()
    assert f"{PERSIST_COMMAND}: persisted=True" in captured.out
    assert captured.err == ""
```

Expected before implementation:

```bash
.venv/bin/python -m pytest tests/test_cli_paper_autonomous_allocation_proposal_scope.py::test_allocation_persist_cli_uses_injected_runner_sink_and_prints_persistence_marker -q
```

Expected result: FAIL because `main()` lacks `paper_autonomous_allocation_proposal_db_sink` and the parser lacks `paper-autonomous-allocation-proposal-persist`.

- [ ] **Step 3: Write failing guard-order test**

Add `test_allocation_persist_cli_requires_enabled_output_db_before_runner_or_sink`:

```python
def test_allocation_persist_cli_requires_enabled_output_db_before_runner_or_sink(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _set_upstream_db_env(
        monkeypatch,
        screening_gate_dsn="postgresql://screening.example.invalid/db",
        decision_support_dsn="postgresql://decision.example.invalid/db",
        source_queue_dsn="postgresql://source.example.invalid/db",
    )
    monkeypatch.delenv(
        PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_ENABLED_ENV_VAR,
        raising=False,
    )

    runner_calls = 0
    sink_calls = 0

    def forbidden_runner(**_kwargs: object) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("runner should not run")

    def forbidden_sink(**_kwargs: object) -> object:
        nonlocal sink_calls
        sink_calls += 1
        raise AssertionError("sink should not run")

    exit_code = main(
        [PERSIST_COMMAND],
        paper_autonomous_allocation_proposal_runner=forbidden_runner,
        paper_autonomous_allocation_proposal_db_sink=forbidden_sink,
    )

    assert exit_code == 1
    assert runner_calls == 0
    assert sink_calls == 0
    captured = capsys.readouterr()
    assert (
        f"{PERSIST_COMMAND} requires autonomous allocation proposal DB to be enabled"
        in captured.err
    )
```

- [ ] **Step 4: Write failing redaction test for sink failure**

Add `test_allocation_persist_cli_sink_failure_redacts_dsns_tables_and_payloads`:

```python
def test_allocation_persist_cli_sink_failure_redacts_dsns_tables_and_payloads(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    proposal_dsn = "postgresql://allocation-secret.example.invalid/db"
    proposal_table_name = "paper_autonomous_allocation_proposal_reports"
    _set_upstream_db_env(
        monkeypatch,
        screening_gate_dsn="postgresql://screening-secret.example.invalid/db",
        decision_support_dsn="postgresql://decision-secret.example.invalid/db",
        source_queue_dsn="postgresql://source-secret.example.invalid/db",
    )
    _set_allocation_proposal_db_env(
        monkeypatch,
        proposal_dsn=proposal_dsn,
        proposal_table_name=proposal_table_name,
    )

    payload_json = '{"market_slug":"secret-market-slug","question":"secret question"}'
    secret_hash = "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"

    def fake_sink(**_kwargs: object) -> object:
        raise RuntimeError(
            f"{proposal_dsn} {proposal_table_name} payload_json={payload_json} "
            f"report_sha256={secret_hash}"
        )

    exit_code = main(
        [PERSIST_COMMAND],
        paper_autonomous_allocation_proposal_runner=lambda **_kwargs: _proposal_report(),
        paper_autonomous_allocation_proposal_db_sink=fake_sink,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert proposal_dsn not in captured.err
    assert proposal_table_name not in captured.err
    assert "secret-market-slug" not in captured.err
    assert "secret question" not in captured.err
    assert secret_hash not in captured.err
    assert "<redacted-dsn>" in captured.err
    assert "<redacted-table>" in captured.err
    assert "<redacted-payload>" in captured.err
    assert "<redacted-sha256>" in captured.err
```

- [ ] **Step 5: Extend parser/flag rejection tests**

Update existing parser flag tests so both `COMMAND` and `PERSIST_COMMAND` reject:

```python
("--persist", "--dsn", "--table", "--trade", "--execute", "--submit", "--approve")
```

Add `PERSIST_COMMAND` to `tests/test_cli.py` help assertions so `polymarket-alpha-lab --help` lists the new sibling command.

- [ ] **Step 6: Run red tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli_paper_autonomous_allocation_proposal_scope.py::test_allocation_persist_cli_uses_injected_runner_sink_and_prints_persistence_marker tests/test_cli_paper_autonomous_allocation_proposal_scope.py::test_allocation_persist_cli_requires_enabled_output_db_before_runner_or_sink tests/test_cli_paper_autonomous_allocation_proposal_scope.py::test_allocation_persist_cli_sink_failure_redacts_dsns_tables_and_payloads -q
```

Expected: FAIL for missing command/sink parameter before production changes.

---

### Task 2: CLI Producer Implementation

**Files:**
- Modify: `src/polymarket_alpha_lab/cli.py`

**Interfaces:**
- Consumes Task 1 tests.
- Produces parser, injected sink, env guard, default psycopg sink import, safe error redaction, and persisted marker.

- [ ] **Step 1: Add sink type and main injection parameter**

Add after `PaperAutonomousAllocationProposalRunner`:

```python
PaperAutonomousAllocationProposalDbSink = Callable[..., object]
```

Add to `main(...)`:

```python
paper_autonomous_allocation_proposal_db_sink: (
    PaperAutonomousAllocationProposalDbSink | None
) = None,
```

- [ ] **Step 2: Import allocation proposal env config**

Add near the existing screening gate env import:

```python
from polymarket_alpha_lab.supabase_paper_autonomous_allocation_proposal_config import (
    from_paper_autonomous_allocation_proposal_db_env,
)
```

- [ ] **Step 3: Add sibling parser**

After the default allocation proposal parser:

```python
paper_autonomous_allocation_proposal_persist = subparsers.add_parser(
    "paper-autonomous-allocation-proposal-persist",
)
paper_autonomous_allocation_proposal_persist.add_argument(
    "--limit",
    type=int,
    default=25,
    dest="limit",
)
```

- [ ] **Step 4: Share command branch with explicit persist flag**

Change:

```python
if args.command == "paper-autonomous-allocation-proposal":
```

to:

```python
if args.command in (
    "paper-autonomous-allocation-proposal",
    "paper-autonomous-allocation-proposal-persist",
):
    command_name = args.command
    persist_proposal_report = (
        command_name == "paper-autonomous-allocation-proposal-persist"
    )
```

Pass `command_name` to the limit error text by changing `_require_paper_autonomous_allocation_proposal_limit` to accept a command name:

```python
def _require_paper_autonomous_allocation_proposal_limit(
    limit: object,
    *,
    command_name: str = "paper-autonomous-allocation-proposal",
) -> None:
```

Use `command_name` in both limit error strings.

- [ ] **Step 5: Validate output DB before runner only for persist command**

After upstream DB configs are validated and before `_run_paper_autonomous_allocation_proposal(...)`:

```python
proposal_dsn = None
proposal_table_name = None
if persist_proposal_report:
    proposal_db_config = from_paper_autonomous_allocation_proposal_db_env()
    if not proposal_db_config.enabled:
        raise ValueError(
            f"{command_name} requires autonomous allocation proposal DB to be enabled",
        )
    proposal_dsn = proposal_db_config.dsn
    if proposal_dsn is None:
        raise ValueError(
            f"{command_name} requires an autonomous allocation proposal DB DSN",
        )
    proposal_table_name = proposal_db_config.table_name
```

- [ ] **Step 6: Persist only after summary report is built**

After `_print_paper_autonomous_allocation_proposal_summary(report)`:

```python
if persist_proposal_report:
    assert proposal_dsn is not None
    assert proposal_table_name is not None
    try:
        if paper_autonomous_allocation_proposal_db_sink is None:
            from polymarket_alpha_lab.paper_autonomous_allocation_proposal_psycopg import (
                insert_paper_autonomous_allocation_proposal_report_with_psycopg,
            )

            paper_autonomous_allocation_proposal_db_sink = (
                insert_paper_autonomous_allocation_proposal_report_with_psycopg
            )
        sink_result = paper_autonomous_allocation_proposal_db_sink(
            dsn=proposal_dsn,
            report=report,
            table_name=proposal_table_name,
        )
    except Exception as exc:
        message = _redact_db_dsn(str(exc), dsn=proposal_dsn)
        message = _redact_db_table_name_and_tail(message, table_name=proposal_table_name)
        message = _redact_paper_research_packet_sensitive_fields(message)
        if not message.strip():
            message = exc.__class__.__name__
        raise RuntimeError(message) from None
    persisted = bool(getattr(sink_result, "inserted", sink_result))
    print(f"{command_name}: persisted={persisted}")
```

The default command must skip this block entirely.

- [ ] **Step 7: Run focused green tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_cli_paper_autonomous_allocation_proposal_scope.py tests/test_cli.py -q
```

Expected: PASS.

---

### Task 3: Docs, Ledger, Review, And Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/paper-autonomous-allocation-proposal.md`
- Modify: `.superpowers/sdd/progress.md`

**Interfaces:**
- Consumes Task 2 command.
- Produces operator docs and a durable progress note.

- [ ] **Step 1: Update README allocation section**

Add a sibling producer block after the existing no-write allocation proposal command:

```markdown
To persist the final paper allocation proposal for later local review, use the
sibling env-only producer command:

```bash
POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_ENABLED=true \
.venv/bin/polymarket-alpha-lab paper-autonomous-allocation-proposal-persist --limit 25
```

The producer builds the same paper-only/report-only/readonly proposal, writes
only that final proposal report to the autonomous allocation proposal DB, prints
the usual aggregate summary plus `persisted=True/False`, and does not create
live instructions or mutate exchange state.
```

- [ ] **Step 2: Update operator doc CLI contract**

In `docs/paper-autonomous-allocation-proposal.md`, keep the default command described as no-write, then add:

```markdown
The persisted handoff is a separate sibling producer command:

```bash
.venv/bin/polymarket-alpha-lab paper-autonomous-allocation-proposal-persist --limit 25
```

It additionally requires:

- `POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_ENABLED`
- `POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_DSN`
- `POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_TABLE`

It accepts only `--limit`, persists only the final proposal report, and remains
paper-only/report-only/read-only. It does not write upstream reports, place
orders, approve execution, read accounts, or mutate exchange state.
```

- [ ] **Step 3: Add docs tests if existing scope tests do not already cover phrases**

If `tests/test_docs_paper_autonomous_allocation_proposal_scope.py` does not cover the new producer, add required phrases:

```python
"paper-autonomous-allocation-proposal-persist --limit 25",
"POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_ENABLED",
"persists only the final proposal report",
"persisted=True/False",
```

Run:

```bash
.venv/bin/python -m pytest tests/test_docs_paper_autonomous_allocation_proposal_scope.py -q
```

- [ ] **Step 4: Update progress ledger**

Append one line to `.superpowers/sdd/progress.md` after implementation review and push:

```markdown
Paper autonomous allocation proposal persist producer: complete (commit <hash>, OpenCode review clean, full pytest <count> passed <skipped> skipped, pushed origin/main).
```

- [ ] **Step 5: Full verification**

Run:

```bash
.venv/bin/python -m pytest
git diff --check
.venv/bin/python -m compileall -q src tests
codegraph sync
```

Expected:

- pytest exits 0
- `git diff --check` exits 0
- compileall exits 0
- CodeGraph sync exits 0

- [ ] **Step 6: OpenCode implementation review before commit**

After all tests pass and before commit, run:

```bash
opencode run --model zhipuai-coding-plan/glm-5.2 --variant max "<review prompt>"
```

Review prompt requirements:

- read-only review
- current uncommitted diff
- verify both command surfaces
- verify output DB guard order
- verify default command remains no-write
- verify Phase 1 boundary
- verify redaction
- verify no store/env/migration duplication
- report Critical/Important findings first

Fix all Critical and Important findings, then rerun focused and full verification.

- [ ] **Step 7: Commit, push, and write Handoff Summary**

Commit only project code/docs/tests and the ledger if intentionally included. Do not commit transient review drafts under `.superpowers/reviews/`.

Use commit message:

```bash
git commit -m "feat: persist allocation proposal handoff"
git push origin main
```

Handoff Summary must include:

- repo status
- commit hash and push status
- verified commands
- OpenCode review status
- uncommitted files
- next step

---

## Parallel Development Plan

After OpenCode plan review approves this plan:

- Worker A can own `tests/test_cli_paper_autonomous_allocation_proposal_scope.py` and `tests/test_cli.py` red tests.
- Worker B can own `README.md`, `docs/paper-autonomous-allocation-proposal.md`, and doc scope tests.
- Main thread owns `src/polymarket_alpha_lab/cli.py` implementation to avoid production-code merge conflicts.
- A review agent can inspect the final diff after Task 2 and Task 3 are integrated.

Workers must not edit each other's files, must not revert unrelated user changes, and must not add live/auth/wallet/account/order/exchange surfaces.

## Self-Review

Spec coverage: The plan advances the automated-investment roadmap from paper allocation proposal generation to a persisted paper handoff without crossing into Level 2 live proposal approval or Level 3 execution. It preserves the existing default no-write command and reuses the existing allocation proposal store/config/psycopg modules.

Placeholder scan: This plan contains exact paths, command names, env vars, test names, snippets, and verification commands. There are no placeholder implementation steps.

Type consistency: The sink uses the existing `insert_paper_autonomous_allocation_proposal_report_with_psycopg(dsn, report, table_name=...)` signature and injected call style already used by the screening gate producer.
