# Team Forecast Persistence Foundation

Date: 2026-07-01

## Goal

Build the local Supabase/Postgres foundation required for long-lived specialist
team memory. This node closes the immediate persistence gaps in the team
forecast slice without changing the Phase 1 boundary.

## Binding Rules

- Persistence is local Supabase/Postgres only.
- No SQLite, JSONL/file journals, Redis, Mongo, SQLAlchemy, hosted DB
  assumptions, or generic persistence abstraction.
- Raw DSNs must be validated through `validate_local_postgres_dsn` before
  psycopg connection use.
- Phase 1 remains paper-only, report-only, and readonly. Do not add live
  trading, auth, wallet, private-key, account-read, order-signing, order-submit,
  cancel, replace, or exchange mutation paths.
- Reviews go directly to local Claude Code only, using
  `claude-opus-4-8` with thinking level `max`. Review prompts are read-only.
- Fast mode is forbidden.
- Use CodeGraph first for code navigation.
- Use TDD for behavior changes.

## Context

The team framework already has taxonomy, routing, forecast packets, forecast DB
row codecs, and specialist team modules. Exploratory agents found the following
blocking gaps for durable team memory:

- No Supabase migration creates `team_profiles`, `team_market_routes`,
  `team_forecasts`, `team_forecast_evidence`, or `team_forecast_outcomes`.
- `team_forecast_store.py` can insert evidence but cannot load evidence back.
- `team_forecast_psycopg.py` exposes only forecast insert/load wrappers.
- `insert_team_forecast_with_psycopg` currently accepts a forecast packet while
  the DB-API store requires a `TeamForecastDbRow`; this contract should be
  tested and fixed before future CLI/write paths rely on it.
- `.env.example` does not list the team forecast DB env vars.

## Scope

Implement this node:

1. Add schema coverage for the five team forecast tables in one Supabase
   migration under `supabase/migrations/`.
2. Add `load_team_forecast_evidence(...)` to `team_forecast_store.py`.
3. Fix and extend `team_forecast_psycopg.py`:
   - convert forecast packets to DB rows before calling the store insert;
   - add evidence insert/load wrappers;
   - add outcome insert/load wrappers;
   - use explicit insert signatures for codec context that is not stored on the
     packet objects:
     - `insert_team_forecast_evidence_with_psycopg(dsn: str, packet: TeamForecastEvidencePacket, *, forecast_id: str, config_version: str, generated_at: datetime, table_name: str) -> TeamForecastEvidenceDbRow`
     - `insert_team_forecast_outcome_with_psycopg(dsn: str, outcome: TeamForecastOutcome, *, config_version: str, generated_at: datetime, table_name: str) -> TeamForecastOutcomeDbRow`
   - use this explicit evidence load wrapper signature:
     - `load_team_forecast_evidence_with_psycopg(dsn: str, *, forecast_id: str | None = None, team_id: str | None = None, market_slug: str | None = None, limit: int | None = None, table_name: str) -> tuple[TeamForecastEvidencePacket, ...]`
   - extend the missing-store fallback stubs for every imported store helper;
   - export every new wrapper through `__all__`;
   - keep local DSN validation before importing/connecting psycopg.
4. Update `.env.example` and env coverage tests for team forecast DB config.
5. Add or update focused tests for SQL shape, record restoration, psycopg
   delegation, cleanup behavior, schema text, and boundary scope.

Out of scope:

- No CLI command in this node.
- No autonomous candidate-selection reducer in this node.
- No team memory synthesis module in this node.
- No changes to strategy allocation or execution flows.
- No live trading/auth/order/account/wallet paths.

## Expected File Ownership

Primary implementation files:

- `src/polymarket_alpha_lab/team_forecast_store.py`
- `src/polymarket_alpha_lab/team_forecast_psycopg.py`
- `supabase/migrations/20260701000000_team_forecast_tables.sql`
- `.env.example`

Primary tests:

- `tests/test_team_forecast_store.py`
- `tests/test_team_forecast_psycopg.py`
- `tests/test_psycopg_adapter_cleanup.py`
- `tests/test_env_example_coverage.py`
- `tests/test_team_forecast_schema.py`

Do not assign two writers to the same file concurrently.

## TDD Plan

### Task 1: Team Schema Migration

RED:

- Add `tests/test_team_forecast_schema.py`.
- Assert migration file exists.
- Assert all five tables are created under `public`.
- Assert `team_profiles` uses `team_id` as its primary key.
- Assert forecast, evidence, route, and outcome tables have materialized
  columns matching `team_forecast_store.py`.
- Assert `payload_json jsonb not null`, `paper_only`, `report_only`,
  `readonly`, and `inserted_at` are present.
- Assert hard safety checks enforce paper/report/readonly flags.
- Assert JSON payload field checks tie materialized fields to payload fields
  where practical.
- Assert load-order indexes exist for forecast/evidence/outcome history.

GREEN:

- Add `supabase/migrations/20260701000000_team_forecast_tables.sql`.
- Use `create table if not exists public.<table>`.
- Use primary/unique keys compatible with existing store conflict keys:
  `payload_sha256` for route/forecast/evidence, `outcome_id` for outcomes.
- Use `team_id` as the primary key for `team_profiles`.
- `team_profiles` and `team_market_routes` are insert-oriented foundations in
  this node; readback/history helpers are intentionally deferred to a later
  read-only team history CLI/memory node.

### Task 2: Evidence Load Store

RED:

- First extend the `store_module` fixture to provide a fake
  `team_forecast_evidence_from_db_row` converter so the module can import after
  the production import is added.
- Extend `tests/test_team_forecast_store.py` with a fake
  `team_forecast_evidence_from_db_row` converter.
- Add test for `load_team_forecast_evidence(...)` filtering by `forecast_id`,
  `team_id`, `market_slug`, and `limit`, ordered newest first by
  `generated_at DESC, inserted_at DESC, payload_sha256 DESC`.
- Add tests for mapping, namedtuple, and positional row shapes if not already
  covered by existing load helpers.
- Add invalid input tests for bad `forecast_id`, bad `team_id`, bad
  `market_slug`, invalid `limit`, and unsafe table names.
- Assert cursor cleanup mirrors forecast/outcome loaders.
- Assert both `load_team_forecasts(...)` and
  `load_team_forecast_outcomes(...)` SQL and params remain unchanged after
  extending the shared filter helper with optional `forecast_id` support.

GREEN:

- Import `team_forecast_evidence_from_db_row`.
- Add `load_team_forecast_evidence` to `__all__`.
- Add `forecast_id` support to the load filter helper without breaking existing
  forecast/outcome query signatures.

### Task 3: Psycopg Contract and Wrappers

RED:

- Update `tests/test_team_forecast_psycopg.py` so
  `insert_team_forecast_with_psycopg` converts a packet with
  `team_forecast_to_db_row` before calling the store.
- Add tests for:
  - `insert_team_forecast_with_psycopg` converting `TeamForecastPacket` via
    `team_forecast_to_db_row(packet)`;
  - `insert_team_forecast_evidence_with_psycopg`;
  - `load_team_forecast_evidence_with_psycopg`;
  - `insert_team_forecast_outcome_with_psycopg`;
  - `load_team_forecast_outcomes_with_psycopg`.
- The exact new insert wrapper signatures are:
  - `insert_team_forecast_evidence_with_psycopg(dsn: str, packet: TeamForecastEvidencePacket, *, forecast_id: str, config_version: str, generated_at: datetime, table_name: str) -> TeamForecastEvidenceDbRow`
  - `insert_team_forecast_outcome_with_psycopg(dsn: str, outcome: TeamForecastOutcome, *, config_version: str, generated_at: datetime, table_name: str) -> TeamForecastOutcomeDbRow`
- The exact new evidence load wrapper signature is:
  - `load_team_forecast_evidence_with_psycopg(dsn: str, *, forecast_id: str | None = None, team_id: str | None = None, market_slug: str | None = None, limit: int | None = None, table_name: str) -> tuple[TeamForecastEvidencePacket, ...]`
- The fallback store stub signatures must match the underlying store helper
  signatures, while the public wrapper signatures must match the two signatures
  above and must fail cleanly with the store-required `RuntimeError` if the
  store module is absent.
- Assert delegation passes wrapped connections, query filters, and table names.
- Replace the existing fake-packet assertion for
  `insert_team_forecast_with_psycopg`. Because `team_forecast_to_db_row`
  requires an exact `TeamForecastPacket`, do not pass the old `FakePacket`
  through the real converter. Either:
  - monkeypatch `team_forecast_to_db_row` to return a fake `TeamForecastDbRow`
    and assert the store receives that row; or
  - build a real `TeamForecastPacket` fixture and assert the store receives the
    real converted row.
  Prefer monkeypatching the converter in adapter-delegation tests so the test
  remains focused on adapter orchestration rather than DB-row codec behavior.
- Assert DSN rejection happens before psycopg import/connect.
- Add tests that simulate a missing `team_forecast_store` module and assert
  every public wrapper fails with the clean
  `RuntimeError("team forecast store module is required")` instead of
  `NameError`.
- Add `polymarket_alpha_lab.team_forecast_psycopg` unconditionally to
  `tests/test_psycopg_adapter_cleanup.py` transactional module coverage for
  `_with_owned_connection`.
- Extend fake psycopg connections with rollback counters where needed for the
  rollback path tests.

GREEN:

- Import codec/store helpers explicitly.
- Convert packets/outcomes/evidence packets to DB rows before insert store calls.
- Use `team_forecast_evidence_to_db_row(packet, forecast_id=forecast_id, config_version=config_version, generated_at=generated_at)` for evidence inserts.
- Use `team_forecast_outcome_to_db_row(outcome, config_version=config_version, generated_at=generated_at)` for outcome inserts.
- Reuse existing `_with_owned_connection` and JSONB adapter behavior.
- Keep error messages DSN-redacted.
- Extend the missing-store fallback block for `insert_team_forecast_evidence`,
  `load_team_forecast_evidence`, `insert_team_forecast_outcome`, and
  `load_team_forecast_outcomes`.
- Update `team_forecast_psycopg.__all__` with all public wrappers.
- Add a direct test that `__all__` contains:
  `insert_team_forecast_with_psycopg`,
  `load_team_forecasts_with_psycopg`,
  `insert_team_forecast_evidence_with_psycopg`,
  `load_team_forecast_evidence_with_psycopg`,
  `insert_team_forecast_outcome_with_psycopg`, and
  `load_team_forecast_outcomes_with_psycopg`.
- Correct fallback stub annotations while the module is being touched.
- Keep the existing single `_with_owned_connection` helper in this node and
  treat commits-after-loads as an accepted current-module convention; splitting
  read/write helpers can be handled in a later consistency cleanup.

### Task 4: Env Example Coverage

RED:

- Extend `tests/test_env_example_coverage.py` to require every public team
  forecast DB env var from `supabase_team_forecast_config.py` in `.env.example`.

GREEN:

- Add disabled-by-default local Supabase/Postgres team forecast env entries.
- Do not include secrets or real credentials.

## Review Plan

Pre-stage:

```bash
claude -p --model claude-opus-4-8 --effort max --permission-mode dontAsk --tools "" "<read-only plan review prompt>"
```

Post-stage:

```bash
claude -p --model claude-opus-4-8 --effort max --permission-mode dontAsk --tools "" "<read-only code review prompt>"
```

Reviewers may inspect plans, diffs, and files only. They must not modify,
create, or delete files.

## Verification

Focused:

```bash
python3 -m pytest -q \
  tests/test_team_forecast_store.py \
  tests/test_team_forecast_psycopg.py \
  tests/test_psycopg_adapter_cleanup.py \
  tests/test_env_example_coverage.py \
  tests/test_team_forecast_schema.py
```

Full:

```bash
python3 -m pytest -q
python3 -m compileall -q src/polymarket_alpha_lab tests
git diff --check
codegraph sync
```

Also run a tracked-content/diff-only secret scan before commit/push.

## Follow-Up Nodes

After this lands, the recommended next nodes are:

1. Add a pure team memory synthesis module that reads forecasts, evidence, and
   outcomes and emits versioned, paper-only memory references.
2. Add a row-level autonomous candidate-selection reducer between
   `PaperStrategyCandidateResearchQueueReport` and
   `PaperAutonomousAllocationProposalReport`.
3. Add a read-only team forecast DB history CLI once persistence foundations
   are stable.
