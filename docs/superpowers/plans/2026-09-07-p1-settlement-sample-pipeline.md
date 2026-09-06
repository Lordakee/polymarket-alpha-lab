# P1 Stage Plan: Settlement-Sample Pipeline

Date: 2026-09-07
Stage: P1 of the [Project Completion Plan](../../roadmap/2026-09-07-project-completion-plan.md)
Status: plan review completed; findings dispositioned (see the final section)
Depends on: accepted M0-M6 delivery (`72d0a23a..8b2025f0`) and the
completion plan (`26c7948b`); branch pushed to origin before this node.

## Parent-Plan Traceability

This stage implements the P1 milestone: recurring persisted forecast
collection with an accountable procedure, resolution of the baseline
provenance defect, auditable settled-outcome import, and the read-only
local-DB export feeding `settlement-evaluation --samples`. P2 evaluation,
P3 second families, P4 waves and P5 arms stay out of scope. The stage
follows the mandatory review loop (stage plan -> Claude Code plan review
-> disposition -> implement -> verify -> hard review until PASS ->
commit -> push before the next node).

## Current-Code Facts (verified at HEAD `26c7948b`)

- Baseline provenance defect: `crypto_btc_team.py:166` copies
  `config.market_implied_probability_hint` into the persisted
  `market_implied_probability_observed`; the hint defaults to
  `0.500000` (`crypto_btc_team.py:33`, ETH identical); the CLI
  constructs configs without overriding it
  (`crypto_research_cycle_cli.py:193`). The cycle's actual base comes
  from the YES-book midpoint, so persisted "observed" baselines are
  0.5 regardless of the market.
- The Gamma adapter extracts conditionId/question/slug/outcomes/
  outcomePrices/clobTokenIds/active/closed/endDate but not
  volume24hr/liquidity, which cohort ranking needs. Verified against a
  live response on 2026-09-07: the fields are exactly `volume24hr` (a
  JSON number) and `liquidity` (a decimal string); extraction
  normalizes both through the adapter's Decimal helper.
- `team_forecast_store` persists forecasts/evidence; outcome rows
  (`TeamForecastOutcome`) require paper-cost fields and must not be
  fabricated for forecast-only outcomes.
- `settlement_evaluation.load_samples_document` defines the export
  JSON contract; the evaluator checks only the forecast cutoff and
  sample invariants.
- No real forecasts have been persisted yet (cycles began 2026-09-05,
  persistence optional and unused in recorded operation), so no
  historical rows need baseline reconstruction; if surprise default-hint
  rows exist, config-version gating excludes them with reason
  `baseline_hint_default`. `research-inventory` must confirm the actual
  counts before the config-version bump lands.

## Design Decisions

1. Baseline fix at the reducer boundary: inside
   `run_crypto_research_cycle`, immediately after `base_probability` is
   derived from the YES-book midpoint and before the `build_forecast`
   call, the reducer rebuilds the team config via
   `dataclasses.replace(config, market_implied_probability_hint=
   base_probability)`, so the persisted
   `market_implied_probability_observed` is the contemporaneous midpoint
   that actually produced the forecast. A focused test asserts the
   persisted observed value equals the book midpoint and never the 0.5
   default, for both teams. Documented semantics change: under the zero-impact
   control, `selected_side` becomes a tie ("yes" via the existing
   `>=` rule) because forecast == midpoint; this is honest for a
   control slice and is pinned by tests. Config-version stamping: the
   CLI wiring bumps config versions to `m5-{team}-v1` -> `p1-{team}-v1`
   so exported cohorts can require provenance (`config_version`
   starting `p1-`) and exclude any older default-hint rows with reason
   `baseline_hint_default`.
2. Cohort selection is frozen before outcomes: the collection filter is
   a pure, tested function over Gamma metadata — binary (exactly two
   clob token ids), `active=true`, `closed=false`, question-or-slug
   matches the team keyword pattern (`btc|bitcoin` / `eth|ethereum`,
   case-insensitive), ranked by liquidity desc then condition_id asc,
   capped by `--limit`. The rule lives in one module and is identical
   for both teams; changing it later starts a new config cohort.
3. Gamma adapter gains `volume24hr` and `liquidity` as Decimal strings
   additively (embedded-JSON handling unchanged); existing extracted
   fields and tests are untouched.
4. Outcomes get their own small, auditable home: one migration adds
   schema `research_settlement` with table `research_settled_outcomes`
   (condition_id, outcome `yes`/`no`, resolution_source
   `polymarket_gamma`, outcome_prices_snapshot jsonb, payload_sha256,
   observed_at, dispute_flag default false, paper/report/readonly true,
   inserted_at; PK (condition_id, observed_at) so corrections are
   additive rows and "current" is latest observed_at). Derivation rule
   is explicit: only `closed=true` markets whose final outcomePrices
   decode to exactly `1`/`0` on the YES token index produce an
   outcome; anything else (not closed, ambiguous prices, missing YES
   label) is refused with a reason and never guessed. The table joins
   nothing at the SQL level; lineage is enforced by the exporter.
5. Three bounded new commands (plus one read-only census), all following
   the established env-gated persistence pattern:
   - `research-inventory`: read-only counts of team forecasts/evidence,
     central raw/normalized rows, settled outcomes, retention health,
     and the env-gate states. Inventory 80 -> 81.
   - `collect-research-cycles --team {crypto_btc,crypto_eth} [--limit N]
     [--offset M]`: applies the frozen filter to a Gamma page, runs the
     existing per-market cycle path for each selected market under an
     `flock` overlap guard (transient lockfile, not durable state),
     prints one structured status line per attempted market plus a
     summary (attempted/ready/blocked/persisted-or-not), and exits
     nonzero only on infrastructure failure — blocked markets are
     recorded outcomes, not command failures. Inventory 81 -> 82.
   - `import-settled-outcomes [--condition-id ...]`: reads persisted
     forecast condition_ids (team-forecast DSN), re-fetches Gamma
     metadata per condition through the registered source, applies the
     derivation rule, persists outcome rows (central-data DSN), and
     prints per-condition results with reasons. Inventory 82 -> 83.
   - `export-settlement-samples --cutoff ISO8601 --out FILE`: read-only
     join of forecast rows and current settled outcomes; selection =
     earliest eligible forecast per (condition_id, team_id,
     config_version) generated before the cutoff with baseline
     provenance; pending = eligible forecasts without a current settled
     outcome; deterministic ordering (condition_id asc, team_id asc,
     generated_at asc, forecast_id asc as the final tie-breaker);
     writes the samples JSON plus `FILE.manifest.json`
     (query rules, source-row identities, exclusion counts, export
     identity hash). Inventory 83 -> 84. All four inventory changes are
     one documented compatibility decision.
6. Collection is an accountable manual procedure first: the runbook
   records the operator cadence guidance (run daily while markets are
   live, re-run after interruptions is safe due to row-level
   idempotency), the recovery path, and the stop condition. No daemon
   or cron is introduced in P1; a supervised schedule may be a later
   reviewed change once the manual procedure has audit evidence.

## Work Items

1. `crypto_research_cycle.py` (edit): baseline provenance fix +
   config-version note; tests for persisted observed baseline and the
   tie-side semantics.
2. `crypto_research_cycle_cli.py` + `cli.py` (edit): config-version
   bump to `p1-{team}-v1`; the four commands with their shared env-gate
   and flock logic; pure cohort filter module `research_cohort.py`
   (new) so selection is testable without I/O.
3. `central_data_source_adapters.py` (edit): additive
   volume24hr/liquidity extraction + tests.
4. `supabase/migrations/20260907000000_research_settlement.sql` (new):
   the outcomes table with constraints mirroring the central-data
   discipline (canonical checks, paper/report/readonly true).
5. `settlement_export.py` (new): pure exporter over injected row
   suppliers (forecast rows, outcome rows) producing the samples
   document and manifest; provenance/exclusion rules enforced here.
6. Tests: cohort filter matrix; outcome derivation matrix
   (closed+final-price, closed+ambiguous, open, missing label);
   exporter selection/pending/exclusion/determinism (fake suppliers);
   opt-in DB lifecycle extension covering the new schema (same env
   gates as M0); CLI registration/inventory; reducer baseline tests.
7. Runbook (edit): collection procedure, cadence, recovery, stop;
   import/export usage; census usage.

## Verification

`research-inventory` runs before the config-version bump and confirms
zero persisted forecasts (or only expected `m5-` rows). Focused
suites; full Python 3.11 regression; compile; `git diff --check`;
credential scan; CLI inventory 84 regenerated with the decision note;
one opt-in live collection run recorded (operator packet + statuses
only) if network and DSN gates permit; opt-in DB lifecycle green for
both schemas.

## Acceptance Criteria (mirrors completion-plan P1)

1. Recurring BTC/ETH collection is demonstrated with real persisted
   forecasts/evidence and independent readback, with visible
   blocked/missed attempts and interruption-safe re-runs.
2. Fixtures and local-DB integration prove selection, retry
   idempotency, snapshot/version handling, YES/NO orientation, paired
   baseline provenance, pending/disputed outcomes and timestamp guards.
3. The baseline wiring defect is resolved and regression-tested;
   forecasts are tested against their actual market control, not the
   default hint.
4. Exported counts reconcile with eligible selected rows, exclusions
   and pending rows; re-exporting an unchanged snapshot reproduces the
   same canonical file and manifest.
5. The exported file loads through the existing evaluator, replays
   offline after raw expiry, and contains no secrets or refused
   payloads.
6. The operator procedure covers both crypto commands, persistence
   gates, cohort selection, outcome refresh, export, recovery and
   stop; if nothing has settled, the export records that honestly.

## Rollback

Revert the work items; the new schema is additive (drop schema
`research_settlement` cascades only its own table); no existing data
depends on it.

## Plan Review Response (2026-09-07)

Claude Code reviewed this plan read-only (`claude-opus-5`, effort `max`)
and returned REQUEST_CHANGES: one CRITICAL, three MEDIUM, two LOW. All
six findings are accepted: the baseline fix now specifies its exact
insertion point and a focused persisted-observed test; the Gamma field
names are verified live (`volume24hr`, `liquidity`) with Decimal
normalization; the outcome importer reuses the YES-label mapping with
positional fallback still refused; the no-historical-rows assumption is
stated as operational with the inventory check; the export gains the
forecast_id final tie-breaker; and the inventory runs before the
config-version bump.

## Implementation Evidence (2026-09-07)

- The pre-change inventory confirmed zero team forecasts and evidence. The
  baseline reducer fix and BTC/ETH regression tests now bind the actual YES
  book midpoint to `market_implied_probability_observed`.
- Official Gamma documentation and live probes established the request
  contract: collection uses `closed=false` plus public tags Bitcoin `235` and
  Ethereum `39`; `/public-search?q=` is discovery-only and the unsupported
  `/markets?search=` parameter is not registered. Single-market list reads use
  `slug`; settlement refresh uses the verified plural `condition_ids`. Every
  response is identity-checked before downstream acquisition or persistence.
- The frozen local selector remains authoritative after tag prefiltering and
  requires exactly two token IDs and exactly two outcomes, `active=true`,
  `closed=false`, and the team keyword. Malformed metadata is counted and
  excluded per row without aborting the page.
- Real local-DB collection and independent readback produced BTC and ETH
  `p1-*` forecasts with three evidence rows each. An interruption-style rerun
  added auditable observation snapshots without overwriting earlier rows.
  Outcome refresh honestly imported zero rows because both markets remain
  unsettled.
- The deterministic export reconciled four forecast input rows to two earliest
  pending selections and zero settled samples. Its manifest includes selected
  forecast IDs, reason-coded non-earliest/excluded counts, and a SHA-256 over
  the exact newline-terminated sample bytes; the sample loads in the existing
  evaluator offline.
- CLI inventory is exactly 84 commands. The final focused suite passed 72 tests
  with four opt-in skips; the opt-in database lifecycle passed all four tests.
  Full Python 3.11 regression passed 34,308 tests with nine skips in 742.94
  seconds. Claude Code 2.1.232 (`opus`, effort `max`) completed the mandatory
  read-only hard review against this stage plan and the completion plan with
  `VERDICT: PASS` and no findings.
