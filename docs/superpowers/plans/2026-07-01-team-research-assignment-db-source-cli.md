# Team Research Assignment DB-Source CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a read-only team research assignment DB-source composer and CLI command that builds assignment reports from local Supabase/Postgres queue, route, and team-memory inputs.

**Architecture:** Keep composition pure in `team_research_assignment_db_source.py`: injected queue/route/memory loaders produce typed source reports, then the existing reducer builds the report. Keep env, psycopg, formatting, and redaction in `cli.py`, matching the existing `team-memory-readiness-digest` command shape. Route readback returns persisted one-row route reports, so the DB-source must merge them into one `TeamMarketRouteReport` before assignment.

**Tech Stack:** Python 3.11+, dataclasses, pytest, argparse, local Supabase/Postgres via existing env config modules, psycopg adapter helpers already present.

**Current checkout status:** The DB-source module, CLI command, and focused tests are present in this in-progress branch. Historical "verify red" expectations below describe the initial TDD sequence before those files existed; they are not current expected results in this checkout. Current behavior is env-only DB config, no CLI DSN/table/persist flags, positive CLI limit validation before env reads, exactly one queue report, nonempty one-row route reports, and runtime source/runner redaction after env gates pass.

## Global Constraints

- Use TDD: every behavior change starts with a failing pytest test.
- Use CodeGraph before grep/find/raw source reads because `.codegraph/` exists.
- Durable project data must use local Supabase/Postgres only.
- Do not add SQLite, Redis, Mongo, SQLAlchemy, hosted DB assumptions, generic DB layers, JSONL durable substitutes, or file-backed durable caches.
- Preserve Phase 1 only: `paper_only=True`, `report_only=True`, `readonly=True`.
- Do not add live trading, auth, wallet/key material, account reads, order signing/submission/cancel/replace, exchange mutation, investment recommendations, investment ranking, trade instructions, strategy-weight tuning, or position sizing.
- CLI must not expose `--dsn`, `--table`, `--persist`, `--live`, `--auth`, `--wallet`, `--private-key`, `--api-key`, `--account`, `--order`, `--trade`, `--execute`, or `--submit`.
- CLI DB config must come from existing env modules only.
- Runtime source/runner errors after env gates pass must redact DSNs, hostnames, table names, market slugs/questions, raw filters, payloads, report hashes, credentials, wallet/account/auth/key/order-like fields. Argparse usage errors and env-gate failures are fail-closed validation surfaces; rejected CLI flags are not a secret transport.
- All review is Claude Code only: `claude-opus-4-8`, effort/thinking `max`. Do not use opencode.
- Subagents are Codex `gpt-5.5` with reasoning `xhigh`; fast mode is forbidden.

---

### Task 1: Pure Team Research Assignment DB-Source

**Files:**
- Create: `src/polymarket_alpha_lab/team_research_assignment_db_source.py`
- Create: `tests/test_team_research_assignment_db_source.py`

**Interfaces:**
- Consumes:
  - `PaperStrategyCandidateResearchQueueReport`
  - `TeamMarketRouteReport`
  - `TeamMemoryReadinessDigestReport`
  - `TeamResearchAssignmentConfig`
  - `build_team_research_assignment_report`
- Produces:
  - `load_team_research_assignment_report(...) -> object`
  - `merge_team_market_route_reports(route_reports) -> TeamMarketRouteReport`

- [ ] **Step 1: Write failing DB-source tests**

Add tests proving:

```python
def test_loads_queue_routes_memory_then_builds_assignment() -> None:
    report = module.load_team_research_assignment_report(
        queue_loader=queue_loader,
        route_loader=route_loader,
        memory_loader=memory_loader,
        assignment_builder=assignment_builder,
        assignment_config=TeamResearchAssignmentConfig(),
        generated_at=GENERATED_AT,
        team_ids=("crypto_btc", "macro_rates"),
        queue_source_config_version="queue-source-v1",
        queue_limit=1,
        route_limit=25,
        memory_config_version="snapshot-v1",
        memory_limit=50,
    )
    assert report is assignment_report
```

Also test empty/multiple queue reports fail before route/memory/builder, empty route readback fails closed, route readback reports must each contain exactly one route row, duplicate route market slugs fail, non-callable loaders/builders fail, exact config type is required, hard flags are enforced on returned report, and the module AST has no psycopg/env/cli/store/connection/write surface.

- [ ] **Step 2: Run tests and verify red**

Run:

```bash
pytest tests/test_team_research_assignment_db_source.py -q
```

Historical red expectation: before implementation existed, this failed because
`polymarket_alpha_lab.team_research_assignment_db_source` did not exist. In the
current checkout, use this command as focused verification instead.

- [ ] **Step 3: Implement minimal pure composer**

Implement:

```python
def load_team_research_assignment_report(
    *,
    queue_loader: Callable[..., tuple[object, ...]],
    route_loader: Callable[..., tuple[object, ...]],
    memory_loader: Callable[..., object],
    assignment_builder: Callable[..., object],
    assignment_config: object,
    generated_at: object,
    team_ids: tuple[str, ...],
    queue_source_config_version: str | None = None,
    queue_limit: int = 1,
    route_limit: int | None = None,
    memory_config_version: str | None = None,
    memory_limit: int | None = None,
) -> object:
    ...
```

Call `queue_loader(source_config_version=queue_source_config_version, action_status="research_ready", research_status="ready", limit=queue_limit)`, require exactly one queue report, call `route_loader(limit=route_limit)`, merge one-row route reports, call `memory_loader(team_ids=normalized_team_ids, config_version=memory_config_version, limit=memory_limit)`, then call `assignment_builder(queue_report, merged_route_report, memory_report, config=assignment_config, generated_at=generated_at)`.

- [ ] **Step 4: Run focused tests and refine**

Run:

```bash
pytest tests/test_team_research_assignment_db_source.py tests/test_team_research_assignment.py tests/test_team_research_assignment_cli_format.py -q
```

Expected: all pass.

### Task 2: Env-Only CLI Command

**Files:**
- Modify: `src/polymarket_alpha_lab/cli.py`
- Create: `tests/test_cli_team_research_assignment.py`

**Interfaces:**
- Consumes:
  - `team_research_assignment_db_source.load_team_research_assignment_report`
  - `team_research_assignment.build_team_research_assignment_report`
  - `team_research_assignment_cli_format.format_team_research_assignment_cli_stdout`
  - `strategy_candidate_research_queue_psycopg_read.PaperStrategyCandidateResearchQueueReadOptions`
  - `team_forecast_psycopg.load_team_market_routes_with_psycopg`
  - existing memory digest/history/gate DB-source loaders
- Produces:
  - CLI command `team-research-assignment`
  - `main(..., team_research_assignment_runner: TeamResearchAssignmentRunner | None = None)`

- [ ] **Step 1: Write failing CLI tests**

Add tests proving help lists `team-research-assignment`; command help contains `--team-id`, `--queue-source-config-version`, `--memory-config-version`, `--queue-limit`, `--route-limit`, `--memory-limit`; forbidden flags are rejected by argparse before env reads; disabled/missing queue DB, team forecast DB, and snapshot DB fail closed; invalid limits fail before env reads; injected runner receives env DSNs/tables/config objects/team ids/generated_at; default path wires queue/route/memory loaders into the DB-source composer; runner errors redact all three DSNs and table names plus market/payload/hash details; returned hard flags are required.

- [ ] **Step 2: Run tests and verify red**

Run:

```bash
pytest tests/test_cli_team_research_assignment.py -q
```

Historical red expectation: before implementation existed, this failed because
the command and runner injection were missing. In the current checkout, use this
command as focused verification instead.

- [ ] **Step 3: Implement CLI command**

Add:

```python
TeamResearchAssignmentRunner = Callable[..., object]
```

Add parser:

```python
team_research_assignment = subparsers.add_parser(
    "team-research-assignment",
    allow_abbrev=False,
    description="Build a read-only, report-only team research assignment report from local Supabase/Postgres queue, route, and memory sources.",
    help="read-only report-only team research assignment from local Supabase/Postgres",
)
```

Use env-only config from `from_strategy_candidate_research_queue_db_env`, `from_team_forecast_db_env`, and `from_team_diagnostics_snapshot_db_env`. Do not expose DSN/table flags.

- [ ] **Step 4: Run focused CLI tests**

Run:

```bash
pytest tests/test_cli_team_research_assignment.py tests/test_cli_team_memory_readiness_digest.py -q
```

Expected: all pass.

### Task 3: Docs and Project Ledger

**Files:**
- Modify: `README.md`
- Modify: `docs/team-research-assignment.md`
- Modify: `docs/team-research-assignment-db-source-gap.md`
- Modify: `.superpowers/sdd/progress.md` after commit hash exists

**Interfaces:**
- Consumes: implemented CLI and DB-source behavior.
- Produces: operator-facing documentation only.

- [ ] **Step 1: Write docs update after code lands**

Update docs to say the DB-source/CLI gap is closed, list env vars for queue, team forecast route, and diagnostics snapshot DBs, and restate Phase 1/no live trading/no recommendation/no sizing boundaries.

- [ ] **Step 2: Run docs sanity checks**

Run:

```bash
git diff --check
```

Expected: no whitespace errors.

### Task 4: Verification, Claude Review, Commit, Push

**Files:**
- No feature files owned; integration only.

- [ ] **Step 1: Run focused verification**

Run:

```bash
python3 -m compileall -q src/polymarket_alpha_lab tests
pytest tests/test_team_research_assignment_db_source.py tests/test_cli_team_research_assignment.py tests/test_team_research_assignment.py tests/test_team_research_assignment_cli_format.py tests/test_cli_team_memory_readiness_digest.py tests/test_team_forecast_store.py tests/test_team_forecast_psycopg_routes.py -q
```

- [ ] **Step 2: Run full verification**

Run:

```bash
pytest -q
codegraph sync
git diff --check
```

- [ ] **Step 3: Claude Code review**

Run Claude Code only:

```bash
claude -p --model claude-opus-4-8 --effort max "<review prompt>"
```

Fix Critical/Important findings and re-run focused verification plus Claude re-review.

- [ ] **Step 4: Secret scan, commit, push**

Run staged added-line scan for credential/token-like strings, commit with:

```bash
git commit -m "feat: add team research assignment db source"
git push origin main
```

Append the commit hash and verification summary to `.superpowers/sdd/progress.md`.
