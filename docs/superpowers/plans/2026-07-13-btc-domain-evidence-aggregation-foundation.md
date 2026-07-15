# BTC Domain Evidence Aggregation Foundation Roadmap

**Status:** Split into independently reviewed Phase 1 development nodes after read-only plan audits found the original 51-path implementation plan was not executable as one unit.

**Goal:** Build a replayable, fail-closed specialist-team evidence pipeline for Polymarket probability events, beginning with BTC, without crossing the Phase 1 paper-only/report-only/readonly boundary.

## Why This Is Split

The original plan combined probability semantics, aggregation arithmetic, replay identity, packet compatibility, schema changes, transaction enforcement, BTC resolution policy, and production service wiring. Independent audits found that one review could not reject or approve those contracts separately and that several interfaces were underspecified.

Each node below therefore has its own exact path allowlist, TDD cycle, focused tests, full suite, CodeGraph sync, read-only Claude Code review, commit, and GitHub push. A later node cannot consume an earlier contract until the earlier node is reviewed and pushed.

## Node Sequence

1. [Canonical Team Forecast P(YES) Contract](2026-07-13-team-forecast-probability-yes-contract.md)
   - Fix the packet, DB, calibration, migration-comment, and operator-documentation semantics.
   - Characterize the existing correct NO-side arithmetic end to end.

2. `2026-07-13-team-evidence-aggregation-core.md`
   - Pure reducer only: no database, domain adapter, CLI, export, or network code.
   - Define exact fixed-six arithmetic, result types, deterministic requirement witnesses, contradiction semantics, freshness, and status precedence.

3. `2026-07-13-team-forecast-build-envelope.md`
   - Add run identity, canonical evaluation-scope provenance, V1 replay evidence, and the ready-only build envelope.
   - Preserve legacy payload hashes byte for byte.

4. `2026-07-13-team-evidence-aggregation-schema.md`
   - Add the aggregation report schema, row codec, local configuration, exact-format partial indexes, and operator migration contract.

5. `2026-07-13-team-forecast-atomic-persistence.md`
   - Enforce the sole atomic write path at DB-API and psycopg boundaries.
   - Prove ready/watch/blocked, retry, orphan rejection, and rollback behavior against disposable local Postgres.

6. `2026-07-13-crypto-btc-evidence-policy.md`
   - Add the immutable approved BTC source registry, trusted source-record catalog, typed resolution contract, pure policy, and evaluator.

7. `2026-07-13-crypto-btc-forecast-service.md`
   - Add the evaluate-and-persist service, exports, final docs, and integration tests.
   - Strategy-cycle consumption remains a separately reviewed next node.

## Dependency Waves

- Node 1 can execute while Node 2's plan is finalized.
- Node 3 starts after Nodes 1 and 2.
- Nodes 4 and 6 may be prepared in parallel after Node 3.
- Node 5 starts after Node 4.
- Node 7 starts after Nodes 5 and 6.
- Pushes are sequential. If `origin/main` moves, the affected node is rebased and fully re-gated.

## Contracts Fixed By Audit

- `TeamForecastPacket.forecast_probability` always denotes canonical `P(YES)`, regardless of `selected_side`; `selected_side` identifies the paper-review side being evaluated and never reorients the probability.
- Evidence freshness cannot be refreshed by recapture. The pure core uses trusted effective content time; capture lag can only disqualify evidence.
- Release-vintage metadata comes from a trusted source-record catalog, not an evidence claim.
- Every accepted evaluator input is represented in a canonical evaluation-scope payload and digest.
- V1 evidence uses a nested replay record and an exact legacy projection; legacy serialization omits the V1 key.
- `tea:v1`, `tfr:v1`, and `tfe:v1` IDs are domain-separated and bind canonical provenance.
- Non-ready aggregation produces no forecast or forecast-evidence packets.
- Every successfully validated build result is persisted; invalid input fails before database activity.
- Public legacy store and psycopg insert APIs reject V1 IDs. The atomic writer uses a private transaction-scoped insertion path.
- The approved BTC registry and policy are immutable/version-bound. Callers cannot self-promote a source to official.
- BTC readiness requires an identity-bound resolution contract and incident gates, not only evidence quorum.
- Future strategy readers inspect the latest aggregation attempt before using a forecast and never fall back through a newer watch/blocked attempt.
- The future central cost engine owns final YES/NO/none selection; packet `selected_side` remains an auditable paper-review input but is not final strategy authority.

## Universal Node Gates

Every executable node records `NODE_BASE`, verifies it equals `origin/main`, stages an exact path allowlist, reviews `NODE_BASE..HEAD`, and runs:

```bash
.venv/bin/python -m pytest -q <focused tests>
.venv/bin/python -m compileall -q src tests
.venv/bin/python -m pytest -q
codegraph sync .
git diff --check
```

Every node also runs the Phase 1 readonly, local-Supabase-only, intended-path, and high-confidence secret scans required by `docs/quality/phase-1-development-node-quality-gates.md`. Claude Code review is read-only, uses `claude-opus-4-8` with effort `max`, has fast mode off, and must return an explicit `PASS`. Empty output is not approval.

All durable data remains in local Supabase/Postgres. Disposable-database tests may create and drop an isolated database inside the existing local `supabase-db` container; they never reset, migrate, or mutate the host `postgres` database.
