# Team Evidence Aggregation Migration Safety

This note defines the safety policy for
`supabase/migrations/20260714000000_team_evidence_aggregation_tables.sql` and
later team-evidence aggregation migration work. Operational apply and
verification commands belong in
[docs/team-evidence-aggregation-supabase-runbook.md](team-evidence-aggregation-supabase-runbook.md);
this safety note is policy only.

Polymarket is a probability event market. Phase 1 supports automatic
screening, research, and paper execution only; no live trading, no investment
advice, no trade instruction, no position advice, and no position sizing.
Costs and fees are research factors only.

## Policy

- Applied migrations are append-only and forward-only.
- Do not edit an applied migration after it has been shared, reviewed, or
  applied to a local Supabase/Postgres database.
- Corrective changes must ship through new timestamped migrations.
- Use local Supabase/Postgres only.
- Local Supabase/Postgres is the only durable persistence target.
- Make no hosted DB assumptions.
- Include no raw DSN examples and no credential-shaped placeholders.
- Do no auth/RLS/role policy work in Phase 1.
- Keep team-evidence aggregation persistence paper-only/report-only/readonly.

## Current Migration Surface

The current migration establishes the local team-evidence aggregation schema:

- `supabase/migrations/20260714000000_team_evidence_aggregation_tables.sql`

It introduces exactly one relation, `team_evaluation_attempts`, with:

- identity: `tea_id` (primary key, supplied by the attempt envelope)
- run reference: `tfr_id`
- evaluation scalars: `attempted_at`, `status`, `hard_flag`,
  `diagnostic_record_count`, `arithmetic_record_count`
- scope identity: `scope_version`, `scope_key`
- evaluated-config identity: `config_version`, `config_digest`
- integrity and evidence: `payload_sha256`, `evaluation_scope_payload` (the
  complete eight-key Node 3 payload), `created_at`
- hard flags: `paper_only`, `report_only`, `readonly`, each boolean not null
  default true with `CHECK (... IS TRUE)` constraints

The `status` domain is exactly `ready`, `watch`, `blocked`; `pass` is
rejected. The default table name exported by
`supabase_team_evidence_aggregation_config` matches this relation:
`team_evaluation_attempts`.

## Preflight Review Checklist

Before an authorized local apply, the operator confirms:

- The user has explicitly authorized the apply task for the local instance;
  no service is started, created, or installed for it.
- The filename is exactly `20260714000000_team_evidence_aggregation_tables.sql`
  and sorts after `20260713000000_team_forecast_probability_yes_contract.sql`.
- Both partial-index names, key column orders, and predicates match the
  pinned definitions below.
- The migration text contains none of the forbidden alternate-backend,
  hosted-URL, or hosted-client tokens pinned by the schema tests.
- No credentials, DSN values, or secrets appear in the migration, the docs,
  or the operator notes.
- Every runtime DSN passes `validate_local_postgres_dsn` (loopback only)
  before any connection or persistence adapter is constructed.
- Post-apply verification is catalog-read-only, as written in the runbook.

## Transaction and Lock Expectations

The migration runs as one forward-only transaction:

- The relation-creation statement takes an `ACCESS EXCLUSIVE` lock on the new
  relation for its duration. Because the relation is new, no existing reader
  or writer contends for it.
- `CREATE INDEX` uses the default non-concurrent form, which takes the same
  lock class on the new relation; concurrent-writer disruption is not a
  concern while the relation is new in the same transaction.
- Apply with `psql --single-transaction` and `ON_ERROR_STOP=1` so any failure
  aborts the whole transaction without leaving a partial relation; the
  migration file itself carries no `BEGIN`/`COMMIT`, and the single-transaction
  guarantee comes from the apply command.
- The migration adds no auth, RLS, or role-policy statement; Phase 1 does no
  such work, and access-control changes would require their own reviewed node.
- Run the authorized apply in a quiet window; do not stack it with unrelated
  schema work against the same database.

## Exact Index Predicates

Two partial indexes are pinned. Any change to their names, key column orders,
or predicates fails review. Both share the identical partial predicate,
restated exactly:

```text
WHERE hard_flag IS TRUE
  AND status IN ('ready', 'watch', 'blocked')
```

- `team_evaluation_attempts_hard_by_run_idx`: key columns
  `tfr_id, attempted_at DESC, tea_id DESC`.
- `team_evaluation_attempts_hard_by_scope_idx`: key columns
  `scope_version, scope_key, attempted_at DESC, tea_id DESC`.

The authoritative DDL lives in the migration; the runbook carries the operator
comparison copy.

## Forward-Only Rollback Posture

- There is no down-migration and no rollback script for this surface.
- If a defect is found after a local apply, leave the applied file unchanged
  and ship the correction as a new timestamped migration.
- Do not reset the local instance or remove rows to undo a migration; rows
  written by Node 5 writers are durable local paper evidence.

## Node 5 Handoff Boundary

Node 4 delivers the schema, the row codec, the fail-closed configuration, and
these docs only. Node 5 owns:

- the store and connection path behind
  `supabase_team_evidence_aggregation_config`;
- the writer that inserts attempts with `ON CONFLICT DO NOTHING` against the
  `tea_id` primary key;
- disposable-database writer proofs and read-back evidence.

No update, delete, or replacement path is planned for these rows in Phase 1.

## Node 5 Writer Safety Rules

Node 5 adds the sole V1 write path; these rules bind every later change:

- Sole atomic write path: `insert_team_evaluation_attempts_with_psycopg`
  validates batch shape, envelope type, orphan run binding, Node 4 row
  conversion, and the table identifier before DSN validation and before any
  connection, then executes the whole batch on one owned connection and one
  transaction with `ON CONFLICT (tea_id) DO NOTHING`, commits exactly once,
  rolls back on every failure, and returns one immutable write result per
  input in input order (`inserted=True` for a fresh row, `inserted=False`
  for a duplicate).
- V1 rejection fence: the legacy surfaces `insert_team_evaluation_attempt`
  and `insert_team_evaluation_attempt_with_psycopg` reject every `tea:v1:`,
  `tfr:v1:`, or `tfe:v1:` identifier before any cursor or connection
  activity and never call the private atomic writer. No other function may
  insert V1 rows.
- Retry contract: retrying the same envelope returns `inserted=False`
  without changing the stored row or the row count; stored attempts stay
  immutable, with no update, delete, or upsert path.
- Orphan contract: an envelope whose `tea_id` is not exactly
  `team_evidence_aggregation_id(evaluation_scope_payload)`, whose
  `run_metadata` is absent or malformed, or whose `tfr_id` is not exactly
  `team_forecast_run_id(tea_id, run_metadata)` is rejected before DSN
  validation, psycopg import, connection construction, or SQL.
- Rollback contract: any failure while inserting a batch rolls back the
  whole batch; zero partial rows remain.
- Dedicated-database cleanup rules: the gated disposable proof runs only
  against `polymarket_alpha_lab_node5_disposable`; the proof test deletes
  only the rows it inserted, by `tea_id`, and never creates or drops a
  database; the operator procedure drops the dedicated database with
  `(force)` in `finally`, refuses to reuse an existing database of that
  name, and touches no shared database.

## Disallowed Changes

Do not:

- Rewrite `20260714000000_team_evidence_aggregation_tables.sql` to correct a
  later finding.
- Assume a hosted database target exists or name one in docs.
- Document connection strings or credential-shaped placeholders.
- Add Phase 1 auth/RLS/role policy work.
- Add application behavior that depends on account, wallet, live trading, or
  order permissions.
- Move team-evidence aggregation data to SQLite, Redis, Mongo,
  SQLAlchemy-managed engines, file journals, or any hosted database target.
- Add a store, connection path, writer, or disposable-database test inside
  Node 4.

## Correction Procedure

When a schema issue is found after this migration has been applied locally:

1. Leave `20260714000000_team_evidence_aggregation_tables.sql` unchanged.
2. Add a new migration with the next canonical timestamped filename.
3. Keep the new migration scoped to local Supabase/Postgres.
4. Add or revise tests that describe the corrected contract.
5. Refresh `docs/team-evidence-aggregation-supabase-runbook.md` if the
   operator verification steps change.
