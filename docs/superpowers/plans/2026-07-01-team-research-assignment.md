# Team Research Assignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Phase 1 paper-only report that assigns existing strategy candidate research queue rows to specialist teams and states whether each assigned team may use long-term memory.

**Architecture:** Add a pure reducer that joins `PaperStrategyCandidateResearchQueueReport`, `TeamMarketRouteReport`, and `TeamMemoryReadinessDigestReport` by `market_slug` and `team_id`. Add a small stdout formatter and, only where inputs are already available through env-only local Supabase/Postgres readers, a pure DB-source composer and CLI command. The node is a research operations report: it preserves queue ordering and must not rank investments, recommend trades, size positions, or mutate external systems.

**Tech Stack:** Python 3.11+, frozen dataclasses, Decimal-only numeric values, pytest, local Supabase/Postgres env modules for durable reads, CodeGraph for code navigation.

## Global Constraints

- Reviews must use Claude Code only: model `claude-opus-4-8`, thinking `max`; do not use opencode.
- Codex subagents use model `gpt-5.5`, reasoning effort `xhigh`; fast mode is forbidden.
- Use CodeGraph before grep/find/read because `.codegraph/` exists.
- Use TDD: write failing tests before production code and verify the failure.
- Durable data must use local Supabase/Postgres only.
- Do not add SQLite, Redis, Mongo, SQLAlchemy, hosted DB assumptions, generic DB layers, or file durable substitutes.
- Preserve Phase 1 boundary: `paper_only=True`, `report_only=True`, `readonly=True`.
- No live trading/auth/wallet/private keys/account reads/order signing/submission/cancel/replace/exchange mutation.
- This node must not output investment recommendations, trade instructions, strategy weight tuning, or position sizing.
- CLI must not add `--dsn` or `--table`; DB config must come from env modules.
- DB/CLI errors must redact DSNs, table names, market slugs/questions/payload/hash/raw_filter details.
- Push completed verified nodes to GitHub.

---

### Task 1: Core Team Research Assignment Reducer

**Files:**
- Create: `src/polymarket_alpha_lab/team_research_assignment.py`
- Create: `tests/test_team_research_assignment.py`
- Modify only if needed for exports: `src/polymarket_alpha_lab/__init__.py`

**Interfaces:**
- Consumes: `PaperStrategyCandidateResearchQueueReport` from `polymarket_alpha_lab.strategy_candidate_research_queue`.
- Consumes: `TeamMarketRouteReport` and `TeamMarketRouteRow` from `polymarket_alpha_lab.team_market_router`.
- Consumes: `TeamMemoryReadinessDigestReport` from `polymarket_alpha_lab.team_memory_readiness_digest`.
- Produces:
  - `DEFAULT_TEAM_RESEARCH_ASSIGNMENT_CONFIG_VERSION = "team-research-assignment-v0"`
  - `TeamResearchAssignmentConfig(config_version: str = DEFAULT..., paper_only: bool = True, report_only: bool = True, readonly: bool = True)`
  - `TeamResearchAssignmentRow(research_rank: int, market_slug: str, question: str, selected_side: str, scoring_side: str, team_id: str, category_id: str, routing_confidence: Decimal, secondary_team_ids: tuple[str, ...], queue_research_status: str, queue_research_bucket: str, queue_readiness_status: str, memory_readiness_status: str, memory_use_policy: str, assignment_status: str, assignment_reason_codes: tuple[str, ...], evidence_gap_codes: tuple[str, ...], source_reason_codes: tuple[str, ...], paper_only: bool = True, report_only: bool = True, readonly: bool = True)`
  - `TeamResearchAssignmentTeamSummary(team_id: str, assignment_count: int, assigned_count: int, watch_count: int, blocked_count: int, memory_readiness_status: str, memory_use_policy: str, paper_only: bool = True, report_only: bool = True, readonly: bool = True)`
  - `TeamResearchAssignmentReport(generated_at: datetime, config_version: str, source_queue_config_version: str, source_route_config_version: str, source_memory_config_version: str, assignment_status: str, recommended_next_step: str, assignment_count: int, assigned_count: int, watch_count: int, blocked_count: int, team_summaries: tuple[TeamResearchAssignmentTeamSummary, ...], rows: tuple[TeamResearchAssignmentRow, ...], reason_codes: tuple[str, ...], paper_only: bool = True, report_only: bool = True, readonly: bool = True)`
  - `build_team_research_assignment_report(queue_report, route_report, memory_readiness_report, *, config: TeamResearchAssignmentConfig, generated_at: datetime) -> TeamResearchAssignmentReport`

- [ ] **Step 1: Write failing tests for the successful join**

Create `tests/test_team_research_assignment.py` with helper rows built from the exact production dataclasses. The first test must build two queue rows, two route rows, and memory statuses for `crypto_btc` and `politics`, then assert:

```python
report = build_team_research_assignment_report(
    queue_report,
    route_report,
    memory_report,
    config=TeamResearchAssignmentConfig(),
    generated_at=GENERATED_AT,
)
assert report.assignment_status == "ready"
assert report.recommended_next_step == "assign_team_research_work"
assert report.assignment_count == 2
assert report.assigned_count == 2
assert tuple(row.market_slug for row in report.rows) == ("btc-alpha", "politics-alpha")
assert report.rows[0].team_id == "crypto_btc"
assert report.rows[0].category_id == "finance.crypto.btc"
assert report.rows[0].memory_readiness_status == "pass"
assert report.rows[0].memory_use_policy == "allow"
assert report.rows[0].assignment_status == "assigned"
assert "team_research_assignment_assigned" in report.rows[0].assignment_reason_codes
assert report.paper_only is True
assert report.report_only is True
assert report.readonly is True
```

Run: `pytest tests/test_team_research_assignment.py::test_assigns_queue_rows_to_routed_teams_with_memory_readiness -q`

Expected: FAIL because `polymarket_alpha_lab.team_research_assignment` does not exist.

- [ ] **Step 2: Write failing tests for blocked/watch cases**

Add tests asserting:
- Missing route for a queue row yields row `assignment_status == "blocked"`, `memory_use_policy == "block"`, reason code `missing_team_market_route`, and report `assignment_status == "blocked"`.
- Missing memory readiness for a routed team yields row `assignment_status == "blocked"`, `memory_use_policy == "block"`, reason code `missing_team_memory_readiness`.
- Queue row with `research_status == "watch"` yields row `assignment_status == "watch"` even when memory readiness passes.
- Memory status `watch` yields policy `throttle` and row `assignment_status == "watch"`.
- Memory status `blocked` yields policy `block` and row `assignment_status == "blocked"`.

Run: `pytest tests/test_team_research_assignment.py -q`

Expected: FAIL because the module does not exist.

- [ ] **Step 3: Implement the pure reducer**

Implement only the reducer module. Required constants and semantics:

```python
NEXT_STEPS = {
    "ready": "assign_team_research_work",
    "watch": "review_team_research_assignments",
    "blocked": "block_team_research_assignment",
}
MEMORY_POLICY_BY_STATUS = {
    "pass": "allow",
    "watch": "throttle",
    "blocked": "block",
}
```

Join behavior:
- Match `route_report.rows` to queue rows by `market_slug`.
- Use `route_row.routing_corrected_team_id` when present; otherwise `route_row.primary_team_id`.
- Match `memory_readiness_report.source_statuses` by `team_id`.
- Preserve queue row order exactly.
- Copy queue `evidence_gap_codes` and `reason_codes` into the assignment row.
- Do not use `research_priority_score`, `recommendation_score`, `suggested_notional`, `selected_position_notional`, or any investment-ranking fields in assignment status.
- If queue row `research_status == "blocked"`, assignment is `blocked`.
- If queue row `research_status == "watch"`, assignment is `watch` unless a harder block exists.
- If route is missing, assignment is `blocked`.
- If memory readiness is missing or `blocked`, assignment is `blocked`.
- If memory readiness is `watch`, assignment is `watch`.
- Otherwise assignment is `assigned`.

Report behavior:
- `assignment_status == "blocked"` if any row is blocked.
- Else `assignment_status == "watch"` if any row is watch.
- Else `assignment_status == "ready"` if at least one row is assigned.
- Else `assignment_status == "blocked"` with reason `team_research_assignment_empty_queue`.
- `team_summaries` must be sorted by `team_id`.
- Validate all hard flags on input reports and nested rows.
- Datetimes must be timezone-aware and normalized to UTC.
- Use `Decimal` for `routing_confidence` and quantize to six places by reusing the route row value.

- [ ] **Step 4: Run focused reducer tests**

Run: `pytest tests/test_team_research_assignment.py -q`

Expected: PASS.

- [ ] **Step 5: Add export coverage if `__init__.py` exports comparable team modules**

If existing team modules are exported from `src/polymarket_alpha_lab/__init__.py`, add the new public classes/functions and corresponding `tests/test_init.py` assertion. If this file does not follow that pattern for reports, do not modify it.

Run: `pytest tests/test_init.py tests/test_team_research_assignment.py -q`

Expected: PASS.

---

### Task 2: CLI Stdout Formatter

**Files:**
- Create: `src/polymarket_alpha_lab/team_research_assignment_cli_format.py`
- Create: `tests/test_team_research_assignment_cli_format.py`

**Interfaces:**
- Consumes: any object with the fields produced by `TeamResearchAssignmentReport`.
- Produces: `format_team_research_assignment_cli_stdout(report: object) -> str`

- [ ] **Step 1: Write failing formatter tests**

Create tests with `types.SimpleNamespace` reports and rows. Assert exact single-line output:

```text
team-research-assignment: assignment_status=watch recommended_next_step=review_team_research_assignments assignment_count=2 assigned_count=1 watch_count=1 blocked_count=0 team_summaries=crypto_btc:1:1/0/0:pass:allow,politics:1:0/1/0:watch:throttle rows=1:btc-alpha:crypto_btc:finance.crypto.btc:assigned:allow,2:politics-alpha:politics:politics:watch:throttle reason_codes=team_research_assignment_watch paper_only=True report_only=True readonly=True
```

Also assert `rows=none`, `team_summaries=none`, and `reason_codes=none` for empty values.

Run: `pytest tests/test_team_research_assignment_cli_format.py -q`

Expected: FAIL because the formatter module does not exist.

- [ ] **Step 2: Implement formatter**

Implement a pure formatter with no DB/env/CLI imports. Keep behavior aligned with existing `team_memory_readiness_digest_cli_format.py`.

- [ ] **Step 3: Run formatter tests**

Run: `pytest tests/test_team_research_assignment_cli_format.py -q`

Expected: PASS.

---

### Task 3: Pure DB-Source Composer Feasibility and Implementation

**Files:**
- Create if feasible: `src/polymarket_alpha_lab/team_research_assignment_db_source.py`
- Create if feasible: `tests/test_team_research_assignment_db_source.py`
- If not feasible, create: `docs/team-research-assignment-db-source-gap.md`

**Interfaces:**
- Preferred producer: `load_team_research_assignment_report(*, queue_loader, route_loader, memory_loader, assignment_builder, assignment_config, generated_at, queue_limit: int | None = None, team_ids: tuple[str, ...] | None = None) -> object`
- This module must remain pure: no `psycopg`, no env modules, no CLI, no store lifecycle, no connection/cursor/execute/commit/rollback/open/write calls.

- [ ] **Step 1: Determine whether persisted route inputs are available**

Use CodeGraph, not raw grep, to answer whether there is an existing local Supabase/Postgres read path for team market routes or specialist assignment metadata that can be composed without adding new durable surfaces.

Acceptable outcomes:
- If an existing env-only local Supabase/Postgres route read path exists, implement the pure composer and tests.
- If no route read path exists, do not invent one in this task. Create `docs/team-research-assignment-db-source-gap.md` explaining that the pure reducer can be used by callers that already provide queue, route, and memory reports, and that a future node should persist/read specialist route metadata.

- [ ] **Step 2: If feasible, write failing DB-source tests**

Tests must inject all loaders/builders and assert:
- Queue, route, and memory loaders are called once with the supplied limits/team filters.
- Assignment builder receives the exact returned reports and `generated_at`.
- Returned report must have `paper_only`, `report_only`, and `readonly` set to `True`.
- Invalid non-callable loaders/builders or missing hard flags fail before returning.
- AST guard blocks DB/env/CLI/store imports and write lifecycle calls.

Run: `pytest tests/test_team_research_assignment_db_source.py -q`

Expected: FAIL because the module does not exist.

- [ ] **Step 3: Implement only the pure composer or the gap doc**

If implementing the composer, expose only `load_team_research_assignment_report` in `__all__`.

- [ ] **Step 4: Run DB-source or doc validation**

Run whichever applies:
- `pytest tests/test_team_research_assignment_db_source.py -q`
- `python3 -m compileall -q src/polymarket_alpha_lab`

Expected: PASS.

---

### Task 4: CLI Command and Documentation

**Files:**
- Modify if data path is feasible: `src/polymarket_alpha_lab/cli.py`
- Create if CLI is added: `tests/test_cli_team_research_assignment.py`
- Modify: `README.md`
- Modify: `docs/strategy-recommendation-layer.md`

**Interfaces:**
- CLI command name: `team-research-assignment`
- Formatter: `format_team_research_assignment_cli_stdout`
- No `--dsn`; no `--table`.

- [ ] **Step 1: Write failing CLI tests only if Task 3 found a feasible data path**

The CLI test must use injected runner/module stubs where existing CLI tests use that pattern. Assert:
- Command invokes env-only configuration modules.
- `--limit` and optional `--team-id` are passed through if added.
- Output uses `format_team_research_assignment_cli_stdout`.
- Runner errors redact DSNs, table names, market slugs/questions/payload/hash/raw_filter details.
- `polymarket-alpha-lab team-research-assignment --help` has no `--dsn` or `--table`.

Run: `pytest tests/test_cli_team_research_assignment.py -q`

Expected: FAIL before implementation.

- [ ] **Step 2: Implement CLI only if feasible**

Keep CLI lifecycle-owned. Do not import DB/env/psycopg into pure modules. Fail closed if DB prerequisites are disabled or unavailable.

- [ ] **Step 3: Update docs**

Document:
- This report assigns research responsibility to specialist teams.
- It gates long-term team memory use with `allow`, `throttle`, or `block`.
- It is not an investment recommendation and does not size or submit orders.
- All durable data comes from local Supabase/Postgres.

- [ ] **Step 4: Run focused docs/CLI tests**

Run:
- `pytest tests/test_cli_team_research_assignment.py tests/test_team_research_assignment_cli_format.py -q` if CLI exists.
- `python3 -m compileall -q src/polymarket_alpha_lab` if CLI is deferred.

Expected: PASS.

---

### Task 5: Integration Verification, Claude Review, Commit, Push

**Files:**
- Modify: `.superpowers/sdd/progress.md`

- [ ] **Step 1: Run focused test suite**

Run:

```bash
pytest tests/test_team_research_assignment.py tests/test_team_research_assignment_cli_format.py tests/test_team_research_assignment_db_source.py tests/test_cli_team_research_assignment.py tests/test_init.py -q
```

If a listed test file does not exist because the plan intentionally deferred that surface, omit only that file and state why.

- [ ] **Step 2: Run full verification**

Run:

```bash
python3 -m compileall -q src/polymarket_alpha_lab tests
pytest -q
codegraph sync
git diff --cached --check
```

Also run a staged credential/token scan over added lines before committing.

- [ ] **Step 3: Claude Code review**

Run Claude Code review with model `claude-opus-4-8`, thinking `max`. Required review scope:
- plan compliance
- Phase 1 boundary
- no live trading/auth/order mutation
- local Supabase/Postgres-only durable data
- no `--dsn`/`--table`
- no investment ranking/recommendation/sizing in assignment logic
- tests are meaningful and include red/green evidence where available

Fix Critical/Important findings, rerun focused tests, and re-review until Critical 0 and Important 0.

- [ ] **Step 4: Commit and push**

Commit message:

```bash
git commit -m "feat: add team research assignment report"
git push origin main
```

- [ ] **Step 5: Update progress ledger and final handoff**

Append a completed node entry to `.superpowers/sdd/progress.md` with:
- commit SHA
- plan path
- changed modules
- focused and full verification results
- Claude review result
- GitHub push range

Final handoff must include repo status, verified commands, uncommitted files, next step.
