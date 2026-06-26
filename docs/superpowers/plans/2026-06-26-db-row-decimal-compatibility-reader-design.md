# DB Row Decimal Compatibility Reader Design

Date: 2026-06-26

## Decision

Use a dual-canonicality reader for Group A DB row codecs.

The reader must preserve raw historical digest semantics while allowing a codec to move new writes to fixed six-place Decimal strings (`0.000001`):

- Stored hash fields must match the raw stored `payload_json` before any compatibility normalization.
- Raw stored `payload_json` must remain canonical JSON: no floats, no raw `Decimal` objects, no non-string object keys, no unsafe hard flags, no bool/int confusion.
- Recovered reports must be semantically valid through the existing dataclass and `from_jsonable` validation path.
- New writes must emit six-place Decimal strings for fields selected by that codec's migration.
- Legacy non-six-place Decimal payload strings may be accepted only for an explicit per-codec field allowlist and only when the recovered canonical report payload matches the stored row after Decimal-aware comparison.
- Materialized row fields must remain consistent with the raw stored payload before the reader returns a report.

This is a reader compatibility design, not a SQL migration design. It allows old paper/report rows to be read without mutating historical payload bytes or historical hash values.

Group A implementation remains blocked until this design document is reviewed, committed, and pushed under the project thread's explicit push authorization.

For this document, "raw stored hash" means the codec's existing hash helper recomputed over the parsed raw `payload_json` using the codec's canonical JSON serializer, before any Decimal compatibility normalization. It does not require byte-for-byte access to original Postgres `jsonb` storage bytes.

## Non-Goals

- No live migration SQL in this task.
- No database backend changes; all DB persistence remains local Supabase/Postgres only.
- No SQLite, file DB, hosted/generic DB abstraction, SQLAlchemy, Redis, or Mongo.
- Phase remains `paper_only`, `report_only`, and `readonly`.
- No live trading, auth, wallet/private-key/account reads, order placement, signing, submission, cancel, replace, or exchange mutation.
- No network mutation surface.
- No shared Decimal utility extraction before at least one Group A codec proves the design in production code and tests.
- No broad rewrite of all DB row codecs in a single change.

## Scope

Group A codecs:

- `paper_nav_snapshot_db_row.py`
- `paper_trade_journal_db_row.py`
- `outcome_tracking_db_row.py`
- `paper_trade_cost_audit_db_row.py`
- `action_gated_strategy_recommendation_queue_db_row.py`

The first implementation should update exactly one Group A codec and its matching tests.

## Reader Contract

Each migrated Group A `from_db_row` path must enforce this order:

1. Validate row type and raw row shape.
2. Reject floats and raw `Decimal` objects anywhere inside `payload_json` before any helper calls `_json_ready` or otherwise normalizes payload values.
3. Validate `paper_only`, `report_only`, and `readonly` hard flags on the row and inside nested payload objects.
4. Verify the stored hash field against the raw stored `payload_json` exactly as stored.
5. Verify materialized fields against the raw stored `payload_json`.
6. Recover the report from raw `payload_json`.
7. Validate the recovered report tree and hard flags.
8. Build the canonical new-write payload from the recovered report.
9. Compare the raw payload to the canonical payload with a codec-local Decimal compatibility comparison.
10. Return the recovered report only when every prior check passes.

The constructor path should enforce the same raw payload and materialized-field checks so `object.__new__` bypass tests cannot sneak malformed rows through `from_db_row`.

Implementation warning: some existing `_normalize_json_object()` helpers call `_json_ready()` on `payload_json`, which can convert raw in-memory `Decimal` objects to strings. A migrated Group A codec must add an explicit raw-payload rejection pass before any such normalization.

The `from_db_row` path must not assume `__post_init__` already ran. It must independently re-run the raw hash, raw-payload type, materialized-field, and flag checks on the supplied row, including rows built with `object.__new__`.

## Decimal Compatibility Comparison

The compatibility comparison should be codec-local in the first Group A implementation.

Allowed legacy differences:

- A field path explicitly listed by the codec.
- Both raw and canonical values are strings.
- Both strings parse to finite `Decimal` values.
- Both parsed Decimal values are numerically equal.
- The canonical value is exactly the codec's new six-place output for that field.

Rejected differences:

- Any unlisted field differs.
- Any value has type drift other than the listed Decimal string compatibility case.
- Either side is a float or raw `Decimal` object.
- Raw legacy strings are non-finite, negative where the domain forbids negative values, or otherwise invalid under the codec's existing field rules.
- Raw strings differ by value, not only by Decimal exponent/scale.
- Payload is missing a key that the new canonical payload contains, or contains an unexpected key not accepted by the existing recovered report validation path.

The comparison should not normalize the raw stored payload before the hash check. Hash validation must always use the raw stored bytes-as-JSON value.

For materialized Decimal columns, compare raw payload fields by numeric Decimal equality only when that field path is explicitly allowlisted. Continue exact type-and-value comparison for non-Decimal fields.

Boolean fields must use identity checks, not `==`, so `1` cannot pass as `True`. Non-bool integer fields must reject bool values before equality checks.

## New-Write Contract

For the selected Group A codec:

- Add a local Decimal quantum constant only after confirming the chosen constant name is unused.
- New `to_db_row` writes emit six-place fixed-notation Decimal strings for the migrated fields.
- Equivalent Decimal exponents, such as `Decimal("42")` and `Decimal("42.000000")`, produce identical `payload_json` and identical hash values.
- Value-changing over-precision, such as `Decimal("42.0000004")`, is rejected instead of rounded into acceptance.
- The formatter must use quantize plus fixed notation, such as `format(quantized, "f")`, so `Decimal("0")` writes as `"0.000000"` and never leaks exponent notation such as `"0E-6"`.
- Existing non-Decimal JSON validation remains strict.

## First Group A Candidate

Recommended first candidate: `paper_nav_snapshot_db_row.py`.

Reasoning:

- It is a pure paper NAV snapshot codec with `snapshot_sha256`, not an execution journal.
- It has direct non-six-place Decimal payload examples such as `"100.00"` and `"96.00"`.
- NAV/cash Decimal fields are easy to identify and are materialized on the row.
- It should prove the compatibility-reader pattern with a smaller operational blast radius than trade journal or action-gated queue payloads.

Initial NAV materialized Decimal allowlist candidates:

- `starting_cash`
- `cash_balance`
- `exit_nav`
- `midpoint_nav`
- `total_cost_basis`
- `unrealized_exit_pnl`

NAV fields that still require exact non-Decimal matching:

- `snapshot_sha256`
- `marked_at`
- `mark_count`
- `paper_only`

NAV does not currently carry `report_only` or `readonly` fields. For this first candidate, require `paper_only is True`; reject unsafe `report_only` or `readonly` if they appear inside nested payload objects, but do not require absent row fields to exist.

NAV payload-only Decimal paths, such as `realized_pnl` and per-position mark Decimal fields, should be reviewed explicitly before inclusion in the allowlist. Do not accept all nested Decimal-looking strings by default. `realized_pnl` is deferred from the initial materialized allowlist because it can be negative and is payload-only, so sign/domain validation should be specified separately from NAV/cash materialized fields.

Defer these until after the NAV pattern is reviewed and pushed:

- `paper_trade_journal_db_row.py`, because execution journal compatibility has higher audit sensitivity.
- `paper_trade_cost_audit_db_row.py`, because ratio fields and size/notional fields have mixed Decimal semantics.
- `action_gated_strategy_recommendation_queue_db_row.py`, because nested queue/bundle/candidate payloads broaden the allowlist.
- `outcome_tracking_db_row.py`, unless outcome history readability becomes a higher priority than NAV snapshots.

## Required Tests For First Group A Implementation

For `paper_nav_snapshot_db_row.py`, add RED tests before production changes:

- New writes canonicalize equivalent Decimal exponents to six-place strings and stable `snapshot_sha256`.
- New writes use fixed notation for zero and large values, including `Decimal("0")`, `Decimal("0.000000")`, `Decimal("42")`, `Decimal("42.000000")`, and a large NAV value.
- A self-hashed legacy row with raw non-six-place Decimal strings reads successfully when:
  - the raw `snapshot_sha256` matches raw `payload_json`
  - the only payload differences are explicitly allowed Decimal string paths
  - recovered report validation succeeds
  - materialized row Decimal values match the raw legacy payload numerically
- A stale hash with the same legacy payload is rejected.
- A self-hashed legacy row with value-changing Decimal strings is rejected.
- A raw payload containing floats or raw `Decimal` objects is rejected.
- Missing nullable keys remain distinct from explicit `null`.
- Bool/int confusion remains rejected, including `paper_only: 1` and `mark_count: True`.
- `object.__new__` bypassed rows cannot evade constructor or `from_db_row` validation; `from_db_row` must independently reject malformed bypassed rows even when `__post_init__` did not run.
- Over-precision new-write Decimal values are rejected rather than rounded.
- The codec remains within its current paper-only scope and imports no auth, wallet, exchange, live trading, SQL, or network mutation surface.

## Opencode Review Gate

Before committing the first Group A implementation, run read-only opencode review with model `zhipuai-coding-plan/glm-5.2 --variant max`.

The review prompt must ask opencode to verify:

- raw hash checks happen before compatibility normalization
- the legacy allowlist is explicit and codec-local
- raw `Decimal` objects are rejected before any `_json_ready` normalization of raw payloads
- new writes emit six-place Decimal strings
- new writes use fixed notation and do not emit exponent notation for zero
- over-precision is rejected rather than rounded
- stale hashes and value-changing legacy payloads are rejected
- bool/int comparisons use identity/type checks where required
- hard flags, bool/int checks, float/raw Decimal rejection, and missing-vs-null semantics remain intact
- no live trading/auth/wallet/account/order/signing/submission/cancel/replace/exchange mutation is introduced
- no persistence backend beyond local Supabase/Postgres is introduced

## Rollout Rule

After the first Group A codec lands:

- Run its focused tests, affected DB row tests, full suite, compileall, diff hygiene, credential-pattern scan, opencode review, and `codegraph sync`.
- Commit and push only when explicitly authorized. This project thread currently has explicit user authorization to push verified nodes.
- Write a handoff doc with the selected legacy allowlist, tests, review verdict, and any remaining Group A risks.
- Revisit whether to extract a shared helper only after two Group A codecs use the same compatibility shape without divergence.
