# Claude Code Review: Team-Agent Architecture

Date: 2026-07-01
Reviewer model requested: `claude-opus-4-8`
Effort requested: `max`
Reviewed report: `docs/superpowers/specs/2026-07-01-team-agent-architecture-review-report.md`
Verdict: approve with changes

## Critical Issues

### 1. Phase 1 readonly enforcement is metadata, not an invariant

The forecast packet includes `paper_only`, `report_only`, and `readonly` fields, and the `polymarket_microstructure` agent is annotated as readonly. Neither is enforcement. The review recommends a `PaperOnlyGuard` or equivalent boundary layer that asserts all paper/report/readonly flags at construction time and requires all Polymarket access to go through a read-only wrapper that structurally cannot reach order-mutation endpoints.

Decision: adopt. This is a hard requirement for the first implementation slice.

### 2. No integration interface to the existing pipeline is specified

The report says team forecasts sit above the cost-aware and recommendation layers, but it does not specify exactly which existing dataclass or function consumes `TeamForecastPacket`.

Decision: adopt. The revised report must include a concrete interface contract before implementation.

### 3. Memory lessons lack minimum-sample gates

The review warns that lessons extracted from too few settled forecasts can contaminate future forecasts.

Decision: adopt. Use staged candidate lessons first, and require a minimum sample gate before promotion to retrievable memory lessons.

## Important Improvements

### 4. Promote `team_forecast_evidence`

The priority table list omitted `team_forecast_evidence`. Without it, postmortems cannot reconstruct the evidence behind a forecast.

Decision: adopt. Evidence persistence is required in Slice 1.

### 5. Scope global memory retrieval

The review warns that a global retrieval agent could leak cross-team lessons into unrelated domains.

Decision: adopt. Retrieval defaults to `team_id + category`. Cross-team analogs require explicit `cross_team=True` and lower weight.

### 6. Add regime and staleness metadata to memory lessons

Lessons can decay or become invalid under different market regimes.

Decision: adopt. Add regime, validity, and decay fields to memory lesson design.

### 7. Add routing correction path

Misrouted markets can corrupt team calibration.

Decision: adopt. Routes need confidence, reason codes, and a correction/reconciliation path.

### 8. Gate trust-score adjustment behind hard settled-sample minimums

The report had "enough settled samples" but no threshold.

Decision: adopt. Trust adjustments remain neutral until hard minimums are reached.

### 9. Centralize Polymarket microstructure reads

Team agents should interpret microstructure snapshots, not refetch Polymarket data themselves.

Decision: adopt. This reduces readonly risk and snapshot inconsistency.

## Minor Suggestions

- Keep the 10-team granularity.
- Treat `commodities_oil` and `sports_other` as expansion teams with split triggers.
- Defer steps 7-10 until after enough settled forecasts exist.
- Run Phase 1 boundary audit checks even in triage.
- Create a minimal `team_postmortems` path early.

Decision: adopt the first four. For `team_postmortems`, include it as a minimal settlement-time artifact, but do not make it a blocker for the first code slice unless the persistence shape stays small.

## Required Tests and Invariants From Review

Accepted required test categories:

- forecast packet construction guards,
- router coverage and exactly-one-primary-team invariant,
- memory lesson sample gate,
- no float in durable JSON payloads,
- DSN validation before psycopg connection setup,
- Phase 1 live-surface boundary guard,
- Brier score consistency,
- outcome idempotency,
- memory lesson scope,
- router correction reconciliation.

## Revised First Implementation Slice

The review recommended narrowing the first implementation slice to prove the architecture end to end:

1. Team taxonomy dataclasses.
2. `PaperOnlyGuard`.
3. `TeamForecastPacket` dataclass and explicit interface contract.
4. Supabase-backed persistence for:
   - `team_profiles`,
   - `team_market_routes`,
   - `team_forecasts`,
   - `team_forecast_evidence`,
   - `team_forecast_outcomes`.
5. Market router.
6. One concrete team first: `crypto_btc`, with lead forecaster, one evidence path, and postmortem/outcome path.
7. Outcome feedback loader for `crypto_btc`.
8. Performance summary with sample-count gating.

Decision: adopt with one adjustment. The first slice should build generic team dataclasses and persistence that can support all 10 teams, but only wire a runnable domain workflow for `crypto_btc`. This avoids hardcoding BTC while keeping runtime scope small.

## Final Decision

Adopt Claude's review with changes. The original architecture remains directionally correct:

- medium 10-team granularity,
- team forecasts and evidence,
- central cost/edge/recommendation/risk/outcome layer,
- local Supabase-only memory,
- paper-only Phase 1 boundary.

The plan must be tightened before implementation:

- add structural readonly/paper-only guardrails,
- define the exact interface into the existing cost-aware pipeline,
- promote forecast evidence persistence,
- scope memory retrieval to team/category by default,
- gate lessons and trust scores by hard sample counts,
- centralize Polymarket microstructure snapshots,
- shrink the first runnable slice to a generic framework plus `crypto_btc`.
