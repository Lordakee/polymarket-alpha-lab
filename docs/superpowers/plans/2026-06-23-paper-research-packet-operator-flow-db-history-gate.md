# Paper Research Packet Operator-Flow DB History Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a paper-only, report-only, read-only gate that reduces persisted operator-flow DB history readback into an autonomous screening decision-support signal.

**Architecture:** The gate is a pure reducer over `PaperResearchPacketOperatorFlowDbHistoryReport`, with a tiny read-only loader composition and a CLI wrapper that reuses the existing operator-flow DB env configuration. The new signal says whether paper autonomous screening decision support may proceed, should be throttled, or should be blocked pending repair.

**Tech Stack:** Python 3, frozen dataclasses, `datetime`, existing CLI/env/redaction patterns, pytest.

## Global Constraints

- Phase 1 only: paper-only, report-only, read-only.
- Do not add live trading, auth, wallet, private key, signing, relayer, account, exchange, order, position, or network-mutation behavior.
- Do not add DSN, table, or persist CLI flags for this command; use the existing operator-flow DB env path.
- Do not import DB/env/psycopg/network clients in the pure reducer.
- Loader composition must not insert, update, commit, rollback, close, or manage connection lifecycle.
- CLI default DB path may connect with `psycopg.connect(dsn, autocommit=True)` and must close only.
- Use exact-type validation for public config/report inputs; reject subclasses where existing nearby modules do.
- Dataclasses must be frozen and must hard-enforce `paper_only is True`, `report_only is True`, and `readonly is True`.
- Keep output deterministic: reason codes and reason-code counts sort by count descending, then code ascending.
- Keep Decimal-only posture; this node should not introduce floats.
- Run tests with `.venv/bin/python -m pytest`, not bare `pytest`.
- Review all completed code and plan changes with local OpenCode using model `zhipuai-coding-plan/glm-5.2` and `--variant max`.
- Push completed, reviewed commits to GitHub.

---

### Task 1: Pure Gate Reducer

**Files:**
- Create: `src/polymarket_alpha_lab/paper_research_packet_operator_flow_db_history_gate.py`
- Create: `tests/test_paper_research_packet_operator_flow_db_history_gate.py`

**Interfaces:**
- Consumes: `PaperResearchPacketOperatorFlowDbHistoryReport` from `paper_research_packet_operator_flow_db_history.py`.
- Produces:
  - `DEFAULT_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_HISTORY_GATE_CONFIG_VERSION = "paper-research-packet-operator-flow-db-history-gate-v0"`
  - `PaperResearchPacketOperatorFlowDbHistoryGateConfig`
  - `PaperResearchPacketOperatorFlowDbHistoryGateReasonCodeCount`
  - `PaperResearchPacketOperatorFlowDbHistoryGateReport`
  - `build_paper_research_packet_operator_flow_db_history_gate_report(history_report: object, *, config: PaperResearchPacketOperatorFlowDbHistoryGateConfig, generated_at: datetime) -> PaperResearchPacketOperatorFlowDbHistoryGateReport`

- [ ] **Step 1: Write reducer tests first**

Cover these behaviors in `tests/test_paper_research_packet_operator_flow_db_history_gate.py`:

```python
def test_operator_flow_db_history_gate_passes_clean_recent_history():
    ...
    assert report.gate_status == "pass"
    assert report.recommended_next_step == "allow_paper_autonomous_screening_decision_support"
    assert report.reason_code_counts == (
        api.PaperResearchPacketOperatorFlowDbHistoryGateReasonCodeCount(
            "paper_operator_flow_db_history_gate_passed",
            1,
        ),
    )
```

Also cover:
- source `history_status == "blocked"` yields `blocked`
- `report_count < min_history_report_count` yields `blocked`
- latest `flow_status == "blocked"` yields `blocked`
- source/latest watch yields `watch`
- duplicate generated-at count over threshold yields `watch`
- stale latest timestamp yields `watch` with exact `latest_source_age_seconds`
- consecutive latest watch/blocked thresholds are enforced
- reason-code counts are deterministic and positive
- hard flags, wrong config/source types, subclasses, and direct constructor corruption are rejected
- module source has no `psycopg`, `supabase`, `os.environ`, public client, wallet, signing, exchange, account, or live-trading surface

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_research_packet_operator_flow_db_history_gate.py -q
```

Expected before implementation: fails because the module or symbols do not exist.

- [ ] **Step 2: Implement the pure reducer**

Use frozen dataclasses and local validation helpers. Required config defaults:

```python
DEFAULT_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_HISTORY_GATE_CONFIG_VERSION = (
    "paper-research-packet-operator-flow-db-history-gate-v0"
)

@dataclass(frozen=True)
class PaperResearchPacketOperatorFlowDbHistoryGateConfig:
    config_version: str = DEFAULT_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_HISTORY_GATE_CONFIG_VERSION
    min_history_report_count: int = 3
    max_latest_age_seconds: int = 86400
    max_consecutive_latest_watch_count: int = 0
    max_consecutive_latest_blocked_count: int = 0
    max_duplicate_generated_at_count: int = 0
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
```

Required status and next-step mapping:

```python
NEXT_STEP_BY_STATUS = {
    "pass": "allow_paper_autonomous_screening_decision_support",
    "watch": "throttle_paper_autonomous_screening_decision_support",
    "blocked": "block_paper_autonomous_screening_decision_support",
}
```

Required blocked reasons:
- `insufficient_operator_flow_db_history`
- `source_operator_flow_db_history_blocked`
- `latest_operator_flow_blocked`
- `consecutive_operator_flow_blocked_threshold_exceeded`
- `missing_latest_operator_flow_history_timestamp`

Required watch reasons:
- `source_operator_flow_db_history_watch`
- `latest_operator_flow_watch`
- `consecutive_operator_flow_watch_threshold_exceeded`
- `duplicate_operator_flow_generated_at_threshold_exceeded`
- `stale_operator_flow_db_history`

Required pass reason:
- `paper_operator_flow_db_history_gate_passed`

Precedence:
- Any blocked reason makes `gate_status == "blocked"`.
- Otherwise any watch reason makes `gate_status == "watch"`.
- Otherwise `gate_status == "pass"`.
- Pass reason must not be mixed with watch/blocked reasons.

- [ ] **Step 3: Run focused reducer tests**

```bash
.venv/bin/python -m pytest tests/test_paper_research_packet_operator_flow_db_history_gate.py -q
```

Expected: all tests in the file pass.

---

### Task 2: Read-Only Loader Composition

**Files:**
- Create: `src/polymarket_alpha_lab/paper_research_packet_operator_flow_db_history_gate_load.py`
- Create: `tests/test_paper_research_packet_operator_flow_db_history_gate_load.py`

**Interfaces:**
- Consumes:
  - `load_paper_research_packet_operator_flow_db_history_report(...)`
  - `PaperResearchPacketOperatorFlowDbHistoryConfig`
  - `PaperResearchPacketOperatorFlowDbHistoryGateConfig`
- Produces:
  - `load_paper_research_packet_operator_flow_db_history_gate_report(connection: object, *, limit: int | None, table_name: str, history_config: PaperResearchPacketOperatorFlowDbHistoryConfig, gate_config: PaperResearchPacketOperatorFlowDbHistoryGateConfig, generated_at: datetime) -> PaperResearchPacketOperatorFlowDbHistoryGateReport`

- [ ] **Step 1: Write loader composition tests first**

Cover:
- Delegates `connection`, `limit`, `table_name`, and `history_config` to the existing DB-history loader.
- Builds the gate report from the exact loaded history report and `gate_config`.
- Rejects non-exact `history_config` and `gate_config` before calling the loader.
- Does not call `commit`, `rollback`, `close`, `cursor`, or any write operation on the supplied connection.

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_research_packet_operator_flow_db_history_gate_load.py -q
```

Expected before implementation: fails because the module or symbol does not exist.

- [ ] **Step 2: Implement loader composition**

Keep the module small. It should import the existing readback loader and the pure gate builder only. It must not import `psycopg`, `os`, env config, or CLI helpers.

- [ ] **Step 3: Run focused loader tests**

```bash
.venv/bin/python -m pytest tests/test_paper_research_packet_operator_flow_db_history_gate_load.py -q
```

Expected: all tests in the file pass.

---

### Task 3: CLI Read-Only Gate Command

**Files:**
- Modify: `src/polymarket_alpha_lab/cli.py`
- Create: `tests/test_cli_paper_research_packet_operator_flow_db_history_gate.py`

**Interfaces:**
- Adds command: `paper-research-packet-operator-flow-db-history-gate`
- Adds runner injection type matching:

```python
PaperResearchPacketOperatorFlowDbHistoryGateRunner = Callable[
    ...,
    object,
]
```

- Adds helper:

```python
def _run_paper_research_packet_operator_flow_db_history_gate(
    *,
    dsn: str,
    table_name: str,
    limit: int,
    runner: PaperResearchPacketOperatorFlowDbHistoryGateRunner | None,
) -> object:
    ...
```

- Adds summary printer:

```python
def _print_paper_research_packet_operator_flow_db_history_gate_summary(report: object) -> None:
    ...
```

- [ ] **Step 1: Write CLI tests first**

Cover:
- command requires existing operator-flow DB env to be enabled and DSN present
- non-positive `--limit` rejects before env, runner, or connection
- injected runner receives `dsn`, `table_name`, `limit`, `history_config`, `gate_config`, and deterministic `generated_at`
- default path imports `psycopg`, connects with `autocommit=True`, calls loader composition, and closes only
- failure messages redact DSN/table/payload details using the existing operator-flow DB-history redaction helper
- printed output contains `gate_status`, `recommended_next_step`, `source_report_count`, `source_history_status`, `latest_flow_status`, `duplicate_generated_at_count`, `latest_source_age_seconds`, and `reason_code_counts`

Run:

```bash
.venv/bin/python -m pytest tests/test_cli_paper_research_packet_operator_flow_db_history_gate.py -q
```

Expected before implementation: fails because the parser branch/helper do not exist.

- [ ] **Step 2: Implement the command**

Mirror the existing `paper-research-packet-operator-flow-db-history` command style:
- Use the same env source for DSN and table.
- Do not add `--dsn`, `--table`, `--persist`, auth, wallet, account, exchange, order, or live flags.
- Construct `PaperResearchPacketOperatorFlowDbHistoryConfig()` and `PaperResearchPacketOperatorFlowDbHistoryGateConfig()` internally.
- Keep default DB behavior read-only: connect autocommit, load gate report, close only.

- [ ] **Step 3: Run focused CLI tests**

```bash
.venv/bin/python -m pytest tests/test_cli_paper_research_packet_operator_flow_db_history_gate.py -q
```

Expected: all tests in the file pass.

---

### Task 4: Scope Guards, Exports, And Docs

**Files:**
- Modify: `src/polymarket_alpha_lab/__init__.py`
- Modify: `README.md`
- Create: `tests/test_cli_paper_research_packet_operator_flow_db_history_gate_scope.py`
- Modify: `tests/test_init.py`

**Interfaces:**
- Export only pure gate reducer dataclasses and build function if this matches current `__init__.py` export style.
- Add README documentation under `## Paper Research Packet Operator Commands`, immediately after the operator-flow DB history block.

- [ ] **Step 1: Write scope/export/docs tests first**

Cover:
- parser surface for the new command is read-only and does not include `--dsn`, `--table`, `--persist`, live, auth, wallet, private-key, account, exchange, order, relayer, or fast flags
- command branch imports only existing operator-flow DB config/readback pieces and the new gate builder/composition
- summary printer is aggregate-only and does not print DSN, table, payload, hash, or question details
- README documents env-only/read-only/paper-only decision support and includes the exact command name
- package exports import cleanly and expose no live execution surface

Run:

```bash
.venv/bin/python -m pytest tests/test_cli_paper_research_packet_operator_flow_db_history_gate_scope.py tests/test_init.py -q
```

Expected before implementation: fails because docs/exports/scope guards are not present.

- [ ] **Step 2: Implement exports/docs/scope guards**

Keep README language factual and bounded. Use this wording in the new docs block:

```text
The gate is a paper-only/read-only decision-support signal. It does not place orders, sign messages, read wallets/accounts, or mutate exchange state. Only a `pass` gate should be treated by downstream paper automation as eligible to advance.
```

- [ ] **Step 3: Run focused scope/export/docs tests**

```bash
.venv/bin/python -m pytest tests/test_cli_paper_research_packet_operator_flow_db_history_gate_scope.py tests/test_init.py -q
```

Expected: all selected tests pass.

---

### Task 5: Integration Review, Full Verification, And Push

**Files:**
- Modify only as needed for fixes from verification or review.

- [ ] **Step 1: Run focused node tests**

```bash
.venv/bin/python -m pytest \
  tests/test_paper_research_packet_operator_flow_db_history_gate.py \
  tests/test_paper_research_packet_operator_flow_db_history_gate_load.py \
  tests/test_cli_paper_research_packet_operator_flow_db_history_gate.py \
  tests/test_cli_paper_research_packet_operator_flow_db_history_gate_scope.py \
  tests/test_init.py \
  -q
```

- [ ] **Step 2: Run full verification**

```bash
.venv/bin/python -m pytest
.venv/bin/python -m compileall -q src tests
git diff --check
```

- [ ] **Step 3: Review with OpenCode**

Create a staged or branch diff artifact under `.superpowers/sdd/`, then run:

```bash
opencode run "Review the paper research packet operator-flow DB history gate node. Check Phase 1 boundaries, CLI/env redaction, pure reducer validation, loader read-only behavior, tests, docs, and package exports. Return Critical/Important/Minor findings." \
  -f .superpowers/sdd/review-operator-flow-db-history-gate.diff \
  --dir /home/ubuntu/polymarket-alpha-lab \
  -m zhipuai-coding-plan/glm-5.2 \
  --variant max
```

Fix all Critical and Important findings, then re-run focused tests and re-review.

- [ ] **Step 4: Sync CodeGraph, commit, push, and update ledger**

```bash
codegraph sync
git add docs/superpowers/plans/2026-06-23-paper-research-packet-operator-flow-db-history-gate.md \
  src/polymarket_alpha_lab \
  tests \
  README.md
git commit -m "feat: add operator-flow DB history gate"
git push origin main
```

Append to `.superpowers/sdd/progress.md`:

```text
Paper research packet operator flow DB history gate: complete (commit <sha>, OpenCode review clean, full pytest <count> passed <skip-count> skipped, pushed origin/main).
```
