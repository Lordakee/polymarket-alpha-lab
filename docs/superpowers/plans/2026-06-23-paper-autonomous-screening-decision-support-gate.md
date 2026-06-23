# Paper Autonomous Screening Decision Support Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Combine upstream paper-only/read-only readiness signals into a final paper autonomous screening decision-support gate.

**Architecture:** The core node is a pure reducer over already-built reports: operator-flow DB history gate, action-gated queue priority, action-gated queue risk, optional decision-support trend/history, and optional project screening rank stability. Persistence is append-only local Supabase/Postgres report storage/readback around the final gate report, and CLI wiring stays at the process boundary with injectable loaders for tests.

**Tech Stack:** Python 3, frozen dataclasses, `datetime`, `Decimal`, existing report validation patterns, local Supabase/Postgres through psycopg at the boundary, argparse CLI wiring, pytest, CodeGraph-first navigation, local OpenCode review.

## Global Constraints

- Do not use fast mode.
- Use CodeGraph before grep/file reads because `.codegraph/` exists.
- Phase 1 only: paper-only, report-only, readonly decision support.
- No live trading, authenticated exchange flow, auth, wallet, private key, signing, relayer, account, account reads, balances, exchange positions, order construction, order submission, order cancellation, order replacement, exchange mutation, or live execution.
- Do not trigger `strategy_cycle` execution.
- Do not run project screening from this node.
- Do not add commands or helpers that mutate Polymarket, exchange state, wallets, accounts, orders, or strategy-cycle state.
- Supabase/Postgres is allowed only for local persisted report storage/readback.
- DB persistence for this node must be append-only report storage; no update, delete, upsert mutation semantics, migrations that rewrite data, or exchange/network mutation.
- Do not add command-line DSN arguments and do not print raw DSNs, credentials, `.env` contents, private keys, full payload JSON, Supabase secrets, or local database credentials.
- The pure reducer must not import DB/env/psycopg/network clients, CLI modules, exchange clients, wallet/account modules, order modules, or strategy-cycle runners.
- Use exact-type validation for public config/report inputs; reject subclasses where nearby modules do.
- Dataclasses must be frozen and must hard-enforce `paper_only is True`, `report_only is True`, and `readonly is True` on all public report/config/row objects that carry hard flags.
- Keep output deterministic: reason code counts sort by count descending, then reason code ascending.
- Keep Decimal-only posture for money, score, utilization, and notional values; do not introduce floats.
- Run tests with `.venv/bin/python -m pytest`, not bare `pytest`.
- Review completed plan/code changes with local OpenCode using model `zhipuai-coding-plan/glm-5.2` and `--variant max`.
- Push completed, reviewed commits to GitHub.

---

## Prerequisites

- Upstream operator-flow DB history gate is implemented and pushed:
  - `PaperResearchPacketOperatorFlowDbHistoryGateReport`
  - `build_paper_research_packet_operator_flow_db_history_gate_report(...)`
- Upstream action-gated queue decision-support reports are implemented and pushed:
  - `PaperActionGatedStrategyRecommendationQueuePriorityReport`
  - `PaperActionGatedStrategyRecommendationQueueRiskReport`
  - optional `PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendReport`
- Optional project screening rank stability report is implemented and pushed:
  - `PaperProjectScreeningRankStabilityReport`
- Workers start from current branch state, run `codegraph sync && codegraph status .` before broad source navigation, and stop if another active worker owns a needed file.

## Parallel Work Partition

These nodes can run in parallel after the prerequisites above are available. File ownership is intentionally non-overlapping.

- **Worker A, pure final gate reducer:** owns only `src/polymarket_alpha_lab/paper_autonomous_screening_decision_support_gate.py` and `tests/test_paper_autonomous_screening_decision_support_gate.py`.
- **Worker B, DB row codec:** owns only `src/polymarket_alpha_lab/paper_autonomous_screening_decision_support_gate_db_row.py` and `tests/test_paper_autonomous_screening_decision_support_gate_db_row.py`.
- **Worker C, local store/config:** owns only `src/polymarket_alpha_lab/supabase_paper_autonomous_screening_decision_support_gate_config.py`, `src/polymarket_alpha_lab/paper_autonomous_screening_decision_support_gate_store.py`, `tests/test_supabase_paper_autonomous_screening_decision_support_gate_config.py`, and `tests/test_paper_autonomous_screening_decision_support_gate_store.py`.
- **Worker D, read-only input composition:** owns only `src/polymarket_alpha_lab/paper_autonomous_screening_decision_support_gate_load.py` and `tests/test_paper_autonomous_screening_decision_support_gate_load.py`.
- **Worker E, CLI process boundary:** owns only `src/polymarket_alpha_lab/cli.py`, `tests/test_cli.py`, and `tests/test_cli_paper_autonomous_screening_decision_support_gate_scope.py`.
- **Worker F, package exports and docs:** owns only `src/polymarket_alpha_lab/__init__.py`, `tests/test_init.py`, `docs/paper-autonomous-screening-decision-support-gate.md`, and `tests/test_docs_paper_autonomous_screening_decision_support_gate_scope.py`.

Workers must not edit another worker's files. If a task needs another owned file, stop and report the dependency rather than crossing ownership. CLI and package export work should start after Worker A's public symbols are stable.

## Target Decision Semantics

The final report status is `pass`, `watch`, or `blocked`.

Recommended next step mapping:

```python
NEXT_STEP_BY_STATUS = {
    "pass": "advance_paper_autonomous_screening_recommendations",
    "watch": "throttle_paper_autonomous_screening_recommendations",
    "blocked": "block_paper_autonomous_screening_recommendations",
}
```

Blocked precedence:

- Any blocked reason makes `gate_status == "blocked"`.
- Otherwise any watch reason makes `gate_status == "watch"`.
- Otherwise `gate_status == "pass"`.
- The pass reason must not be mixed with watch or blocked reasons.

Blocked reason codes:

- `operator_flow_db_history_gate_blocked`
- `queue_risk_blocked`
- `queue_decision_support_trend_latest_risk_blocked`
- `queue_decision_support_trend_consecutive_latest_blocked`
- `project_screening_rank_stability_blocked`

Watch reason codes:

- `operator_flow_db_history_gate_watch`
- `queue_risk_watch`
- `queue_decision_support_trend_latest_risk_watch`
- `queue_decision_support_trend_consecutive_latest_watch`
- `queue_decision_support_trend_duplicate_generated_at`
- `project_screening_rank_stability_watch`

Required pass reason code:

- `paper_autonomous_screening_decision_support_gate_passed`

Optional inputs:

- Missing trend/history report does not degrade status in this v0 node.
- Missing rank stability report does not degrade status in this v0 node.
- If an optional input is present, validate and use it.

---

### Task 1: Pure Final Gate Reducer

**Files:**
- Create: `src/polymarket_alpha_lab/paper_autonomous_screening_decision_support_gate.py`
- Create: `tests/test_paper_autonomous_screening_decision_support_gate.py`

**Interfaces:**
- Consumes:
  - `PaperResearchPacketOperatorFlowDbHistoryGateReport`
  - `PaperActionGatedStrategyRecommendationQueuePriorityReport`
  - `PaperActionGatedStrategyRecommendationQueueRiskReport`
  - optional `PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendReport`
  - optional `PaperProjectScreeningRankStabilityReport`
- Produces:
  - `DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_CONFIG_VERSION`
  - `PaperAutonomousScreeningDecisionSupportGateReasonCodeCount`
  - `PaperAutonomousScreeningDecisionSupportGateReport`
  - `build_paper_autonomous_screening_decision_support_gate_report(...)`

- [ ] **Step 1: Write reducer tests first**

Cover these cases in `tests/test_paper_autonomous_screening_decision_support_gate.py`:

```python
def test_final_gate_passes_clean_required_inputs_without_optional_reports():
    report = build_paper_autonomous_screening_decision_support_gate_report(
        operator_flow_gate_report=_operator_flow_gate_report(gate_status="pass"),
        priority_report=_queue_priority_report(
            research_ready_count=2,
            watch_count=0,
            blocked_count=0,
        ),
        risk_report=_queue_risk_report(status="pass"),
        trend_report=None,
        rank_stability_report=None,
        generated_at=GENERATED_AT,
    )

    assert report.gate_status == "pass"
    assert report.recommended_next_step == (
        "advance_paper_autonomous_screening_recommendations"
    )
    assert report.reason_codes == (
        "paper_autonomous_screening_decision_support_gate_passed",
    )
```

Also cover:

- operator-flow gate `blocked` produces `blocked`
- queue risk `blocked` produces `blocked`
- operator-flow gate `watch` produces `watch`
- queue risk `watch` produces `watch`
- optional trend missing does not degrade pass
- latest trend risk `blocked` produces `blocked`
- latest trend risk `watch` produces `watch`
- any positive consecutive latest blocked count produces `blocked`
- otherwise any positive consecutive latest watch count produces `watch`
- any duplicate trend generated-at count produces `watch`
- optional rank stability missing does not degrade pass
- rank stability `blocked` produces `blocked`
- rank stability `watch` produces `watch`
- reason-code counts are unique and always use `report_count == 1`
- subclasses and false hard flags are rejected for every public source input
- direct constructor corruption is rejected for report/status/next-step/reason consistency
- optional trend/rank fields must be present together when their source is present
- module source has no `psycopg`, `supabase`, `os.environ`, public client, wallet, signing, exchange, account, order, or strategy-cycle execution surface

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_autonomous_screening_decision_support_gate.py -q
```

Expected before implementation: fails because the module or symbols do not exist.

- [ ] **Step 2: Implement the pure reducer**

Implement these public symbols:

```python
DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_CONFIG_VERSION = (
    "paper-autonomous-screening-decision-support-gate-v0"
)

@dataclass(frozen=True)
class PaperAutonomousScreeningDecisionSupportGateReasonCodeCount:
    reason_code: str
    report_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
```

Implement the report with at least these fields:

```python
@dataclass(frozen=True)
class PaperAutonomousScreeningDecisionSupportGateReport:
    generated_at: datetime
    config_version: str
    gate_status: str
    recommended_next_step: str
    reason_code_counts: tuple[
        PaperAutonomousScreeningDecisionSupportGateReasonCodeCount,
        ...
    ]
    reason_codes: tuple[str, ...]
    operator_flow_gate_config_version: str
    operator_flow_gate_generated_at: datetime
    operator_flow_gate_status: str
    operator_flow_recommended_next_step: str
    queue_priority_generated_at: datetime
    queue_risk_generated_at: datetime
    queue_risk_config_version: str
    queue_risk_status: str
    queue_risk_recommended_next_step: str
    queue_source_report_count: int
    queue_research_ready_count: int
    queue_watch_count: int
    queue_blocked_count: int
    queue_candidate_count: int
    queue_ready_count: int
    queue_candidate_watch_count: int
    queue_candidate_blocked_count: int
    queue_total_ready_notional: Decimal
    queue_largest_ready_notional: Decimal
    queue_top_research_priority_score: Decimal
    queue_average_research_priority_score: Decimal
    trend_source_snapshot_count: int | None
    trend_latest_risk_status: str | None
    trend_consecutive_latest_watch_count: int | None
    trend_consecutive_latest_blocked_count: int | None
    trend_duplicate_generated_at_count: int | None
    rank_stability_status: str | None
    rank_stable_ready_count: int | None
    rank_unstable_ready_count: int | None
    rank_blocked_count: int | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
```

Implement the builder signature:

```python
def build_paper_autonomous_screening_decision_support_gate_report(
    *,
    operator_flow_gate_report: PaperResearchPacketOperatorFlowDbHistoryGateReport,
    priority_report: PaperActionGatedStrategyRecommendationQueuePriorityReport,
    risk_report: PaperActionGatedStrategyRecommendationQueueRiskReport,
    generated_at: datetime,
    trend_report: (
        PaperActionGatedStrategyRecommendationQueueDecisionSupportTrendReport | None
    ) = None,
    rank_stability_report: PaperProjectScreeningRankStabilityReport | None = None,
    config_version: str = (
        DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_CONFIG_VERSION
    ),
) -> PaperAutonomousScreeningDecisionSupportGateReport:
    ...
```

Implementation rules:

- Require exact input types.
- Validate hard flags recursively enough to catch false flags on source report rows where upstream reports expose rows.
- Normalize datetimes to UTC.
- Validate priority/risk reports describe the same source snapshot.
- Validate source recommended-next-step fields match their statuses.
- Use blocked-over-watch-over-pass precedence exactly.
- Use deterministic unique reason code counts with each `report_count` equal to `1`.
- Do not preserve source report payloads inside the final report; store only scalar summary fields.

- [ ] **Step 3: Run focused reducer tests**

```bash
.venv/bin/python -m pytest tests/test_paper_autonomous_screening_decision_support_gate.py -q
```

Expected: all tests in the file pass.

---

### Task 2: DB Row Codec For Final Gate Reports

**Files:**
- Create: `src/polymarket_alpha_lab/paper_autonomous_screening_decision_support_gate_db_row.py`
- Create: `tests/test_paper_autonomous_screening_decision_support_gate_db_row.py`

**Interfaces:**
- Consumes: `PaperAutonomousScreeningDecisionSupportGateReport`
- Produces:
  - `PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_SCHEMA_VERSION`
  - `PaperAutonomousScreeningDecisionSupportGateDbRow`
  - `paper_autonomous_screening_decision_support_gate_to_db_row(report: PaperAutonomousScreeningDecisionSupportGateReport) -> PaperAutonomousScreeningDecisionSupportGateDbRow`
  - `paper_autonomous_screening_decision_support_gate_from_db_row(row: PaperAutonomousScreeningDecisionSupportGateDbRow) -> PaperAutonomousScreeningDecisionSupportGateReport`
  - aliases `to_db_row(...)` and `from_db_row(...)`

- [ ] **Step 1: Write DB row codec tests first**

Cover:

- exact report type is required
- false hard flags on the report are rejected
- row scalar fields match report scalar fields
- `payload_json` round-trips into the exact report type
- `report_sha256` is deterministic for equivalent reports
- JSON conversion rejects floats anywhere in payload/count maps
- `reason_code_counts_json` is a dict sorted by deterministic JSON serialization
- row rejects mismatched `payload_json`, `report_sha256`, `schema_version`, scalar status fields, timestamps, and reason code counts
- module source has no exchange/auth/wallet/account/order/signing/live-trading imports

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_autonomous_screening_decision_support_gate_db_row.py -q
```

Expected before implementation: fails because the module or symbols do not exist.

- [ ] **Step 2: Implement the DB row codec**

Use the local style from existing report row codecs. The row must include these scalar columns:

```python
PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_SCHEMA_VERSION = (
    "paper-autonomous-screening-decision-support-gate-db-row-v0"
)

@dataclass(frozen=True)
class PaperAutonomousScreeningDecisionSupportGateDbRow:
    report_sha256: str
    schema_version: str
    generated_at: datetime
    config_version: str
    gate_status: str
    recommended_next_step: str
    reason_code_counts_json: dict[str, int]
    operator_flow_gate_status: str
    queue_risk_status: str
    queue_priority_source_report_count: int
    queue_priority_research_ready_count: int
    queue_risk_source_queue_count: int
    queue_risk_ready_count: int
    decision_support_trend_present: bool
    decision_support_trend_latest_risk_status: str | None
    rank_stability_present: bool
    rank_stability_status: str | None
    payload_json: dict[str, object]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
```

Implementation rules:

- Serialize `datetime` as UTC ISO strings in `payload_json`.
- Serialize `Decimal` values as strings if any are later added to the final report.
- Reject floats before hashing and before recovery.
- Compute `report_sha256` with `json.dumps(..., sort_keys=True, separators=(",", ":"), allow_nan=False)`.
- Rebuild the report through the existing JSON dataclass helper used by nearby DB row modules.
- Validate the rebuilt report equals the row's scalar columns.

- [ ] **Step 3: Run focused DB row tests**

```bash
.venv/bin/python -m pytest tests/test_paper_autonomous_screening_decision_support_gate_db_row.py -q
```

Expected: all tests in the file pass.

---

### Task 3: Local Supabase/Postgres Store And Env Config

**Files:**
- Create: `src/polymarket_alpha_lab/supabase_paper_autonomous_screening_decision_support_gate_config.py`
- Create: `src/polymarket_alpha_lab/paper_autonomous_screening_decision_support_gate_store.py`
- Create: `tests/test_supabase_paper_autonomous_screening_decision_support_gate_config.py`
- Create: `tests/test_paper_autonomous_screening_decision_support_gate_store.py`

**Interfaces:**
- Produces:
  - `SupabasePaperAutonomousScreeningDecisionSupportGateConfig`
  - `from_paper_autonomous_screening_decision_support_gate_db_env(env: Mapping[str, str] | None = None) -> SupabasePaperAutonomousScreeningDecisionSupportGateConfig`
  - `insert_paper_autonomous_screening_decision_support_gate_report(connection: object, *, report: PaperAutonomousScreeningDecisionSupportGateReport, table_name: str) -> PaperAutonomousScreeningDecisionSupportGateDbRow`
  - `load_paper_autonomous_screening_decision_support_gate_reports(connection: object, *, table_name: str, limit: int) -> tuple[PaperAutonomousScreeningDecisionSupportGateReport, ...]`
  - `insert_paper_autonomous_screening_decision_support_gate_report_with_psycopg(dsn: str, *, report: PaperAutonomousScreeningDecisionSupportGateReport, table_name: str) -> PaperAutonomousScreeningDecisionSupportGateDbRow`
  - `load_paper_autonomous_screening_decision_support_gate_reports_with_psycopg(dsn: str, *, table_name: str, limit: int) -> tuple[PaperAutonomousScreeningDecisionSupportGateReport, ...]`

- [ ] **Step 1: Write env config tests first**

Use env vars:

```python
POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_ENABLED
POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_DSN
POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_TABLE
```

Default table:

```python
DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_TABLE = (
    "paper_autonomous_screening_decision_support_gate_reports"
)
```

Cover:

- disabled config accepts absent DSN
- enabled config requires DSN without echoing it
- padded DSNs are treated as absent or invalid without echoing secret text
- enabled accepts only strict true values `1` and `true`
- disabled accepts `""`, `0`, and `false`
- table name accepts simple lowercase identifiers and optional `schema.table` if nearby decision-support configs allow schema-qualified names
- `repr(config)` redacts DSN

- [ ] **Step 2: Write store tests first**

Cover:

- insert uses only `INSERT INTO ...` for one report row and returns the exact DB row
- load uses only `SELECT ... ORDER BY generated_at DESC, report_sha256 DESC LIMIT %s`
- load recovers exact report objects through the DB row codec
- table name is validated before SQL formatting
- `limit` must be positive
- psycopg wrappers own and close their connections
- connection-level helpers do not close caller-owned connections
- no update, delete, upsert, commit, rollback, exchange, auth, wallet, account, order, signing, or live-trading surface appears in the store module

Run:

```bash
.venv/bin/python -m pytest \
  tests/test_supabase_paper_autonomous_screening_decision_support_gate_config.py \
  tests/test_paper_autonomous_screening_decision_support_gate_store.py \
  -q
```

Expected before implementation: fails because the modules or symbols do not exist.

- [ ] **Step 3: Implement env config and local store**

Implementation rules:

- Keep env parsing in the config module only.
- Keep psycopg imports inside wrapper functions or at the store boundary.
- Store rows by converting the final report through `paper_autonomous_screening_decision_support_gate_to_db_row(...)`.
- Do not add migrations or table-creation behavior in this node.
- Do not print DSNs or payload JSON.

- [ ] **Step 4: Run focused store/config tests**

```bash
.venv/bin/python -m pytest \
  tests/test_supabase_paper_autonomous_screening_decision_support_gate_config.py \
  tests/test_paper_autonomous_screening_decision_support_gate_store.py \
  -q
```

Expected: all tests in the two files pass.

---

### Task 4: Read-Only Input Composition

**Files:**
- Create: `src/polymarket_alpha_lab/paper_autonomous_screening_decision_support_gate_load.py`
- Create: `tests/test_paper_autonomous_screening_decision_support_gate_load.py`

**Interfaces:**
- Produces:
  - `load_paper_autonomous_screening_decision_support_gate_report(connection, *, ...) -> PaperAutonomousScreeningDecisionSupportGateReport`

- [ ] **Step 1: Write read-only loader composition tests first**

Cover:

- exact operator-flow config types are enforced before source loading
- optional trend and rank stability readbacks may be omitted
- rank filters are rejected when no rank table is configured
- false hard flags on any loaded report are rejected
- injected final gate builder output must be an exact final gate report with hard flags true
- composition delegates to the pure final gate builder with the loaded latest source objects
- module has no psycopg, env, exchange, auth, wallet, account, order, signing, strategy-cycle, project-screening-run, insert, update, delete, commit, or rollback surface

Run:

```bash
.venv/bin/python -m pytest tests/test_paper_autonomous_screening_decision_support_gate_load.py -q
```

Expected before implementation: fails because the module or symbols do not exist.

- [ ] **Step 2: Implement the read-only loader composition module**

The module is a DB-API composition layer over existing readback helpers. It
uses the supplied connection, does not manage connection lifecycle, does not
write, and reverses newest-first queue readbacks into chronological order for
trend generation while leaving the latest pair at `[-1]`.

- [ ] **Step 3: Run focused loader composition tests**

```bash
.venv/bin/python -m pytest tests/test_paper_autonomous_screening_decision_support_gate_load.py -q
```

Expected: all tests in the file pass.

---

### Task 5: CLI Process Boundary

**Files:**
- Modify: `src/polymarket_alpha_lab/cli.py`
- Create: `tests/test_cli_paper_autonomous_screening_decision_support_gate_scope.py`

**Command:**

`polymarket-alpha-lab paper-autonomous-screening-decision-support-gate --limit 25`

**Arguments:**

- `--limit`, positive integer, default `25`, used by the readback helper to select the upstream persisted report window.

Do not add command-line DB targets, persistence switches, wallet, account, exchange, order, strategy-cycle, project-screening, live, submit, cancel, or auth flags.

This node ships a read-only env-only CLI. The operator-flow DB and action-gated queue decision-support DB are required through env-backed config. The rank-stability DB is optional; when enabled, the default single-connection read path requires it to use the same DSN as the required upstream DBs.

**Runner seam:**

Add injectable runner support to `main(...)` for tests:

```python
PaperAutonomousScreeningDecisionSupportGateRunner = Callable[..., object]
```

The runner receives:

- `generated_at`
- final gate config
- readback limit
- operator-flow DB connection settings
- action-gated queue decision-support DB connection settings
- optional rank-stability DB connection settings only when that DB is enabled

- [ ] **Step 1: Write CLI tests first**

Cover:

- command rejects non-positive `--limit` before env, connection, or runner work
- no command-line DB or write flag exists
- runner injection receives deterministic `generated_at`, config booleans, readback limit, and required/optional DB settings
- default path builds and prints a report without requiring final gate DB env
- rank-stability DB is optional and omitted from runner/helper calls when disabled
- default helper uses one autocommit read connection and closes it without commit or rollback
- output first line starts with `paper-autonomous-screening-decision-support-gate:`
- output includes `gate_status`, `recommended_next_step`, `operator_flow_gate_status`, `queue_risk_status`, `queue_research_ready_count`, `trend_present`, and `rank_stability_present`
- output prints gate-signal counts and reason-code counts without payloads
- user-facing errors redact DSNs and do not print payload JSON
- command path does not call strategy-cycle execution, project screening execution, exchange mutation, wallet/account/auth/order/signing functions, or live trading functions

Run:

```bash
.venv/bin/python -m pytest tests/test_cli_paper_autonomous_screening_decision_support_gate_scope.py -q
```

Expected before implementation: fails because the command branch/helper does not exist.

- [ ] **Step 2: Implement CLI wiring**

Implementation rules:

- Keep report loading/building behind an injectable runner.
- Default CLI may read local persisted upstream reports only through existing local DB readback helpers when those helpers are available.
- If an upstream persisted source does not yet expose a read helper, fail with a clear message naming the missing local report source, not a fallback live run.
- Do not run strategy cycle or project screening to create missing inputs.
- Construct the private paper-only/report-only/read-only gate config at the process edge.
- Print compact scalar summary only.
- Do not require final gate DB config and do not write the final report in this CLI node.

- [ ] **Step 3: Run focused CLI tests**

```bash
.venv/bin/python -m pytest tests/test_cli_paper_autonomous_screening_decision_support_gate_scope.py -q
```

Expected: all tests in the file pass.

---

### Task 6: Public Exports And Operator Documentation

**Files:**
- Modify: `src/polymarket_alpha_lab/__init__.py`
- Modify: `tests/test_init.py`
- Create: `docs/paper-autonomous-screening-decision-support-gate.md`
- Create: `tests/test_docs_paper_autonomous_screening_decision_support_gate_scope.py`

- [ ] **Step 1: Write export tests first**

Assert package-root exports include:

```python
DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_CONFIG_VERSION
PaperAutonomousScreeningDecisionSupportGateReasonCodeCount
PaperAutonomousScreeningDecisionSupportGateReport
build_paper_autonomous_screening_decision_support_gate_report
```

Run:

```bash
.venv/bin/python -m pytest tests/test_init.py -q
```

Expected before implementation: fails because the package root does not export these names.

- [ ] **Step 2: Write docs scope test first**

Assert the doc says:

- this is Phase 1 paper-only/report-only/readonly decision support
- final statuses are `pass`, `watch`, and `blocked`
- recommended next steps are advance, throttle, and block paper autonomous screening recommendations
- inputs are operator-flow DB history gate, action-gated queue priority, action-gated queue risk, optional trend/history, and optional project screening rank stability
- missing optional trend/rank-stability reports do not degrade status in this v0 node
- local Supabase/Postgres is used only for persisted report storage/readback
- no live trading, auth, wallet, keys, account reads, order signing, order submission, order cancellation, strategy-cycle execution, project screening run, or exchange mutation occurs

Run:

```bash
.venv/bin/python -m pytest tests/test_docs_paper_autonomous_screening_decision_support_gate_scope.py -q
```

Expected before implementation: fails because the doc does not exist.

- [ ] **Step 3: Implement exports and docs**

Add only the four package-root exports listed in Step 1. Keep docs concise and operator-facing:

1. Inputs.
2. Decision status semantics.
3. Local persistence/readback boundaries.
4. CLI usage without secrets.
5. Explicit non-goals and forbidden actions.

- [ ] **Step 4: Run focused export/docs tests**

```bash
.venv/bin/python -m pytest \
  tests/test_init.py \
  tests/test_docs_paper_autonomous_screening_decision_support_gate_scope.py \
  -q
```

Expected: focused export/docs tests pass.

---

## Integration Verification Checklist

Run after all workers' nodes are merged into one integration branch:

```bash
.venv/bin/python -m pytest \
  tests/test_paper_autonomous_screening_decision_support_gate.py \
  tests/test_paper_autonomous_screening_decision_support_gate_load.py \
  tests/test_paper_autonomous_screening_decision_support_gate_db_row.py \
  tests/test_supabase_paper_autonomous_screening_decision_support_gate_config.py \
  tests/test_paper_autonomous_screening_decision_support_gate_store.py \
  tests/test_paper_autonomous_screening_decision_support_gate_psycopg_read.py \
  tests/test_cli_paper_autonomous_screening_decision_support_gate_scope.py \
  tests/test_init.py \
  tests/test_docs_paper_autonomous_screening_decision_support_gate_scope.py \
  -q
.venv/bin/python -m pytest -q
.venv/bin/python -m compileall -q src tests
git diff --check
codegraph sync
codegraph status .
```

Run a staged-file ownership check before review:

```bash
git diff --cached --name-only
git diff --cached --check
```

No staged file should fall outside the implementing worker's assigned ownership unless the user explicitly reassigned that file.

## Review And Push Gates

Each worker must complete these gates before handing off:

```bash
.venv/bin/python -m pytest <focused test files for the worker> -q
.venv/bin/python -m compileall -q src tests
git diff --check
codegraph sync
codegraph status .
```

Then run local OpenCode audit from the repo root:

```bash
opencode run \
  --model zhipuai-coding-plan/glm-5.2 \
  --variant max \
  --dir /home/ubuntu/polymarket-alpha-lab \
  "Review the staged Paper Autonomous Screening Decision Support Gate changes for correctness, safety boundaries, test coverage, deterministic report semantics, local DB-only persistence/readback, secret redaction, and forbidden live trading/auth/wallet/account/order/strategy-cycle/project-screening behavior. Return Critical, Important, and Nice-to-have findings with file and line references."
```

Fix Critical and Important findings. If a finding requires another worker's owned file, stop and coordinate instead of crossing ownership.

Final push gate:

```bash
git status --short
git add <owned files only>
git commit -m "feat: add paper autonomous screening decision support gate <node>"
git push
```

Use a more specific commit subject for each worker, such as:

- `feat: add paper autonomous screening gate reducer`
- `feat: persist paper autonomous screening gate reports`
- `feat: wire paper autonomous screening gate cli`
