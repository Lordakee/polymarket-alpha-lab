# Paper Autonomous Allocation Proposal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a paper-only/report-only/read-only autonomous allocation proposal stage that wraps a passed autonomous screening gate and already-produced action-gated queue reports into auditable paper allocation proposals.

**Architecture:** The pure reducer is the source of truth: it validates a screening gate report, latest priority/risk reports, source action-gated queue reports, and a reusable `PaperRecommendationAllocationReport`. It does not perform I/O, live trading, auth, wallet, exchange, or order work. Persistence is append-only report storage; CLI integration is env-only and read-only for this node.

**Tech Stack:** Python frozen dataclasses, `Decimal` only, existing action-gated queue reports, existing `paper_recommendation_allocation` reducer, DB-API store pattern, psycopg read/write adapters, Supabase SQL migration, pytest, CodeGraph.

## Global Constraints

- Preserve Phase 1 boundary: no live trading, no auth, no key handling, no wallet handling, no account reads, no order construction, no order signing, no order submission, no order cancellation, no order replacement, no exchange mutation.
- The proposal is paper-only/report-only/read-only; it is not a trade instruction, not execution authorization, not investment ranking, and not financial advice.
- Use `Decimal` only for numeric finance/probability/notional values; reject floats recursively in payload JSON.
- Use frozen dataclasses for public report/config/row types.
- Reuse `PaperRecommendationAllocationReport`; do not reimplement allocation cap logic.
- Pass-only v0: if the autonomous screening gate is `watch` or `blocked`, or queue risk is not `pass`, proposal status must not be `pass` and allocation rows must not be treated as executable.
- Source queue reports are required for per-market rows; the decision-support DB snapshot alone is insufficient because it does not contain market-level allocation rows.
- Default CLI path is env-only and read-only; it accepts only `--limit`, constructs no client, and writes no proposal reports.
- Persistence modules may exist for append-only DB storage, but the new CLI command must not write by default.
- Reviews go to local OpenCode with model `zhipuai-coding-plan/glm-5.2`, variant `max`.
- Do not use fast mode.
- Use `.venv/bin/python -m pytest`, not bare `pytest`.

---

### Task 1: Pure Proposal Reducer

**Files:**
- Create: `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal.py`
- Test: `tests/test_paper_autonomous_allocation_proposal.py`
- Test: `tests/test_paper_autonomous_allocation_proposal_scope.py`
- Modify: `src/polymarket_alpha_lab/__init__.py`
- Modify: `tests/test_init.py`

**Interfaces:**
- Consumes:
  - `PaperAutonomousScreeningDecisionSupportGateReport`
  - `PaperActionGatedStrategyRecommendationQueuePriorityReport`
  - `PaperActionGatedStrategyRecommendationQueueRiskReport`
  - `PaperActionGatedStrategyRecommendationQueueReport`
  - `PaperRecommendationAllocationConfig`
  - `PaperRecommendationAllocationInput`
  - `PaperRecommendationAllocationReport`
  - `build_paper_recommendation_allocation_report`
- Produces:
  - `DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_CONFIG_VERSION`
  - `PaperAutonomousAllocationProposalConfig`
  - `PaperAutonomousAllocationProposalReasonCodeCount`
  - `PaperAutonomousAllocationProposalSourceQueueSummary`
  - `PaperAutonomousAllocationProposalReport`
  - `build_paper_autonomous_allocation_proposal_report(...)`

- [ ] **Step 1: Write failing reducer tests**

Create tests that prove:

```python
def test_pass_gate_builds_allocation_proposal_from_ready_source_queue_rows():
    report = build_paper_autonomous_allocation_proposal_report(
        screening_gate_report=gate_report(gate_status="pass"),
        priority_report=priority_report_for_source_queues(...),
        risk_report=risk_report(status="pass"),
        source_queue_reports=(source_queue_report_with_ready_rows(...),),
        config=PaperAutonomousAllocationProposalConfig(
            config_version="paper-autonomous-allocation-proposal-v0",
            allocation_config=PaperRecommendationAllocationConfig(
                config_version="allocation-v0",
                total_paper_budget=Decimal("100.000000"),
                max_paper_notional_per_market=Decimal("50.000000"),
                max_paper_notional_per_event=Decimal("50.000000"),
                max_paper_notional_per_theme=Decimal("50.000000"),
                max_paper_notional_per_correlation_group=Decimal("50.000000"),
            ),
        ),
        generated_at=GENERATED_AT,
    )

    assert report.proposal_status == "pass"
    assert report.recommended_next_step == "review_paper_autonomous_allocation_proposal"
    assert report.allocation_report.paper_only is True
    assert report.allocation_report.report_only is True
    assert report.allocation_report.readonly is True
    assert report.allocation_report.allocated_count == 1
    assert report.reason_codes == ("paper_autonomous_allocation_proposal_passed",)
```

Also test gate `watch` -> proposal `watch`, gate `blocked` -> proposal `blocked`, risk `watch/blocked` precedence, empty source queue reports blocked, priority/risk/source consistency mismatch, hard-flag rejection, frozen dataclasses, Decimal quantization, exact type rejection, and reason-code count consistency.

- [ ] **Step 2: Write failing scope tests**

Use the `tests/test_paper_recommendation_allocation_scope.py` pattern. Allow only imports from:

```python
{
    "__future__",
    "collections",
    "collections.abc",
    "dataclasses",
    "datetime",
    "decimal",
    "polymarket_alpha_lab.action_gated_strategy_recommendation_queue",
    "polymarket_alpha_lab.action_gated_strategy_recommendation_queue_priority",
    "polymarket_alpha_lab.action_gated_strategy_recommendation_queue_risk",
    "polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate",
    "polymarket_alpha_lab.paper_recommendation_allocation",
}
```

Forbid network/client/auth/wallet/order/trading imports, `open`, `read`, `write`, `print`, `eval`, `exec`, `input`, and public names containing live/order/wallet/auth/client fragments except `readonly`.

- [ ] **Step 3: Implement the reducer**

Implement v0 semantics:

```python
NEXT_STEP_BY_STATUS = {
    "pass": "review_paper_autonomous_allocation_proposal",
    "watch": "hold_paper_autonomous_allocation_proposal",
    "blocked": "block_paper_autonomous_allocation_proposal",
}
PASS_REASON_CODE = "paper_autonomous_allocation_proposal_passed"
```

Build allocation inputs only from ready source queue rows:

```python
PaperRecommendationAllocationInput(
    market_slug=queue_row.market_slug,
    side=queue_row.selected_side,
    action=queue_row.action,
    recommendation_score=queue_row.recommendation_score,
    net_probability_edge=None,
    executable_paper_shares=queue_row.suggested_notional / price,
    side_price=price,
    reason_codes=(queue_row.primary_reason_code,),
)
```

Use a conservative v0 price recovery helper:
- If the matching selection row exposes `selected_position_notional > 0` and queue row `suggested_notional > 0`, use `price = selected_position_notional / executable_paper_shares` only if source row exposes shares.
- If no reliable share/price source exists, use `side_price=Decimal("1.000000")` and `executable_paper_shares=queue_row.suggested_notional` so allocation preserves paper notional without claiming executable order sizing.

Then call `build_paper_recommendation_allocation_report(inputs, config=config.allocation_config, generated_at=generated_at)`.

Proposal status:
- `blocked` if screening gate is `blocked`, queue risk is `blocked`, no source queue reports, no allocation inputs, or allocation report has zero allocated/capped rows.
- `watch` if screening gate is `watch`, queue risk is `watch`, or allocation report has any capped/no_budget/skipped/non_recommend rows.
- `pass` only if screening gate and queue risk pass and allocation report has at least one allocated row with no caps.

- [ ] **Step 4: Export public reducer API**

Add only the public reducer types/functions to `src/polymarket_alpha_lab/__init__.py` and assert them in `tests/test_init.py`. Do not export CLI-only or DB config types from package root.

- [ ] **Step 5: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest -q tests/test_paper_autonomous_allocation_proposal.py tests/test_paper_autonomous_allocation_proposal_scope.py tests/test_init.py
```

---

### Task 2: Append-Only Proposal Persistence Foundation

**Files:**
- Create: `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_row.py`
- Create: `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_store.py`
- Create: `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_psycopg.py`
- Create: `src/polymarket_alpha_lab/supabase_paper_autonomous_allocation_proposal_config.py`
- Create: `supabase/migrations/20260623000003_paper_autonomous_allocation_proposal_reports.sql`
- Test: `tests/test_paper_autonomous_allocation_proposal_db_row.py`
- Test: `tests/test_paper_autonomous_allocation_proposal_store.py`
- Test: `tests/test_paper_autonomous_allocation_proposal_psycopg.py`
- Test: `tests/test_supabase_paper_autonomous_allocation_proposal_config.py`

**Interfaces:**
- Consumes Task 1 report type.
- Produces append-only storage and env config for `paper_autonomous_allocation_proposal_reports`.

- [ ] **Step 1: Write failing DB row tests**

Tests must assert deterministic hash, full payload round trip, Decimal-as-string JSON, recursive float rejection, exact type rejection, frozen row, hard-flag rejection in nested allocation rows, materialized scalar mismatch rejection, and source status/next-step consistency.

- [ ] **Step 2: Implement DB row codec**

Use full payload hash:

```python
report_sha256 = sha256(json.dumps(payload_json, allow_nan=False, separators=(",", ":"), sort_keys=True).encode("utf-8")).hexdigest()
```

Materialize proposal status, screening gate fields, allocation summary fields, reason code JSON, allocation rows JSON, payload JSON, and hard flags.

- [ ] **Step 3: Write failing store tests**

Tests must assert parameterized insert, `InsertResult(row, inserted)`, `rowcount in (0, 1)`, newest-first read order, filters for `config_version`, `proposal_status`, `screening_gate_status`, `allocation_config_version`, safe table validation, dict/namedtuple/row readback, no commit/rollback, cursor close.

- [ ] **Step 4: Implement store**

Implement `_SELECT_COLUMNS`, insert, load, table validation, and DB row normalization. Exclude `inserted_at` from `_SELECT_COLUMNS` and use it only for ordering.

- [ ] **Step 5: Implement psycopg writer and env config**

Psycopg writer wraps dict/list params with `Jsonb`, commits on success, rollbacks on exception, closes exactly once. Env config is frozen, redacts DSN in `repr`, imports the default table from the store, and accepts strict enabled values.

- [ ] **Step 6: Implement migration**

Create `20260623000003_paper_autonomous_allocation_proposal_reports.sql` with the columns and checks from the DB exploration summary. Include indexes on generated time, proposal status, config version, screening gate status, allocation config version, and GIN indexes for JSON columns.

- [ ] **Step 7: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest -q tests/test_paper_autonomous_allocation_proposal_db_row.py tests/test_paper_autonomous_allocation_proposal_store.py tests/test_paper_autonomous_allocation_proposal_psycopg.py tests/test_supabase_paper_autonomous_allocation_proposal_config.py
```

---

### Task 3: Read-Only Loader And CLI Command

**Files:**
- Create: `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_load.py`
- Create: `src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_psycopg_read.py`
- Modify: `src/polymarket_alpha_lab/cli.py`
- Test: `tests/test_paper_autonomous_allocation_proposal_load.py`
- Test: `tests/test_paper_autonomous_allocation_proposal_psycopg_read.py`
- Test: `tests/test_cli_paper_autonomous_allocation_proposal_scope.py`
- Modify: `tests/test_cli.py`

**Interfaces:**
- Consumes Task 1 reducer.
- Reads latest persisted screening gate report, action-gated queue decision-support reports, and source action-gated queue reports.
- Produces CLI command `paper-autonomous-allocation-proposal --limit 25`.

- [ ] **Step 1: Write failing loader tests**

Tests must prove:
- loader rejects non-paper/report/readonly inputs before reducer
- action-gated queue source reports are loaded newest-first but passed to reducer as tuple
- decision-support latest pair and source queue reports are both required
- no cursor/commit/rollback/write calls inside the pure loader
- injected reducer must return exact proposal report type

- [ ] **Step 2: Implement loader**

Default loader reads:
- latest autonomous screening decision-support gate report
- latest action-gated queue decision-support priority/risk pair
- all source action-gated queue reports in the requested window; the reducer builds
  allocation inputs only from reports with `action_status="research_ready"`

It builds a default `PaperAutonomousAllocationProposalConfig` with a conservative `PaperRecommendationAllocationConfig`:

```python
total_paper_budget=Decimal("100.000000")
max_paper_notional_per_market=Decimal("25.000000")
max_paper_notional_per_event=Decimal("25.000000")
max_paper_notional_per_theme=Decimal("25.000000")
max_paper_notional_per_correlation_group=Decimal("25.000000")
```

- [ ] **Step 3: Write failing psycopg read tests**

Tests must assert frozen options, limit validation and cap, `psycopg.connect(dsn, autocommit=True)`, close exactly once on success and error, and no commit/rollback/write SQL.

- [ ] **Step 4: Implement psycopg read adapter**

Mirror `paper_autonomous_screening_decision_support_gate_psycopg_read.py`, but connect to one DSN and pass table names to the loader.

- [ ] **Step 5: Write failing CLI tests**

Add `paper-autonomous-allocation-proposal --limit`. It must:
- validate limit before env reads/runner/connect
- require env-enabled screening gate DB, action-gated queue decision-support DB, and action-gated queue DB
- enforce same DSN in default single-connection path
- use injected runner before psycopg import
- reject `--dsn`, `--table`, `--persist`, `--fast`, `--live`, `--auth`, `--wallet`, `--private-key`, `--api-key`, `--account`, `--order`, `--trade`, `--execute`, `--submit`, `--approve`
- never construct `client_factory`
- print aggregate-only summary without market slugs, questions, payload JSON, hashes, DSNs, or table names
- redact all DSNs/tables/payload/question/hash-like data on failures

- [ ] **Step 6: Implement CLI integration**

Add runner alias, injected `main(...)` parameter, subparser, branch, helper, redaction helper, and summary helper. The CLI command must not write proposal reports.

- [ ] **Step 7: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest -q tests/test_paper_autonomous_allocation_proposal_load.py tests/test_paper_autonomous_allocation_proposal_psycopg_read.py tests/test_cli_paper_autonomous_allocation_proposal_scope.py tests/test_cli.py
```

---

### Task 4: Operator Documentation And README Scope Guards

**Files:**
- Create: `docs/paper-autonomous-allocation-proposal.md`
- Test: `tests/test_docs_paper_autonomous_allocation_proposal_scope.py`
- Modify: `README.md`

**Interfaces:**
- Documents Task 1/3 operator behavior.
- Keeps wording inside paper-only/report-only/read-only boundary.

- [ ] **Step 1: Write failing docs tests**

Required headings:

```python
(
    "# Paper Autonomous Allocation Proposal",
    "## Scope",
    "## Source Reports",
    "## Operator Flow",
    "## Allocation Proposal Status and Next Step",
    "## Paper Allocation and Shadow NAV",
    "## Transaction and Cost Awareness",
    "## CLI Contract",
    "## Review Boundaries",
)
```

Required phrases:

```python
(
    "paper-only/report-only/read-only autonomous allocation proposal",
    "Polymarket probability-event allocation review",
    "already-produced and persisted upstream paper reports",
    "combines upstream paper reports into an allocation proposal status and recommended next step",
    "moves toward autonomous investing only by preparing paper allocation proposals",
    "operator review aids, not approvals",
    "paper notional is paper sizing, not capital commitment",
    "paper allocation proposal rows are not order tickets",
    "a pass status is not permission to trade",
    "not financial advice",
    "not investment ranking",
    "not automatic live investing",
    "not order instruction",
    "not execution authorization",
    "not an approval workflow",
    "not a live-execution signal",
    "no live trading",
    "no auth",
    "no key handling",
    "no wallet handling",
    "no account handling",
    "no account reads",
    "no order construction",
    "no order signing",
    "no order submission",
    "no order cancellation",
    "no order replacement",
    "no exchange mutation",
    "transaction/cost awareness is upstream evidence",
    "no live fee estimation",
)
```

- [ ] **Step 2: Write docs and README**

README placement: inside `## Paper Research Packet Operator Commands`, immediately after the Paper Autonomous Screening Decision Support Gate block and before `## Level 1B Node 1 Status`.

Document:

```bash
.venv/bin/polymarket-alpha-lab paper-autonomous-allocation-proposal --limit 25
```

State env-only, reads already-persisted upstream reports, accepts only `--limit`, does not accept DSN/table/persist flags, and does not write reports.

- [ ] **Step 3: Run focused docs tests**

Run:

```bash
.venv/bin/python -m pytest -q tests/test_docs_paper_autonomous_allocation_proposal_scope.py
```

---

### Final Verification

- [ ] Run all new focused tests:

```bash
.venv/bin/python -m pytest -q \
  tests/test_paper_autonomous_allocation_proposal.py \
  tests/test_paper_autonomous_allocation_proposal_scope.py \
  tests/test_paper_autonomous_allocation_proposal_db_row.py \
  tests/test_paper_autonomous_allocation_proposal_store.py \
  tests/test_paper_autonomous_allocation_proposal_psycopg.py \
  tests/test_supabase_paper_autonomous_allocation_proposal_config.py \
  tests/test_paper_autonomous_allocation_proposal_load.py \
  tests/test_paper_autonomous_allocation_proposal_psycopg_read.py \
  tests/test_cli_paper_autonomous_allocation_proposal_scope.py \
  tests/test_docs_paper_autonomous_allocation_proposal_scope.py \
  tests/test_cli.py \
  tests/test_init.py
```

- [ ] Run full verification:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m compileall -q src tests
git diff --check
codegraph sync
codegraph status .
```

- [ ] Request OpenCode review:

```bash
opencode run --model zhipuai-coding-plan/glm-5.2 --variant max --dir /home/ubuntu/polymarket-alpha-lab -- "<review prompt>"
```

- [ ] Fix Critical/Important findings, rerun focused/full verification, commit, push `origin main`, and append evidence to `.superpowers/sdd/progress.md`.
