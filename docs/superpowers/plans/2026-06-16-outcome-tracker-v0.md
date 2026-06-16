# Outcome Tracker v0 Plan (Stage 9)

**Goal:** Close "self-judge verification" loop. Read paper trades → re-fetch resolved markets → build calibration observations → forecast_evidence report. Read-only.

## Pre-stage gate
- [ ] 0. Claude pre-stage (claude-opus-4-8 / effort max). Codex fallback after 2 failures.

## Tasks
- [ ] 1. `outcome_tracker.py` (NEW live-layer): `check_outcomes(*, client, journal_path, config, generated_at) -> OutcomeTrackingReport`. Reads PaperTradeJournal → groups by condition_id → re-fetches each market via client.list_markets → normalize_gamma_market → checks closed/resolution_status → builds PaperForecastEvidenceObservation (predicted_probability from trade.research_fair_value_estimate, actual_outcome_value from resolution) → build_paper_forecast_evidence_report if >=1 obs. RED+GREEN (fake client; resolved market → observation; pending → skip; empty journal → empty report).
- [ ] 2. `test_outcome_tracker_scope.py` (NEW): ALLOWED stdlib + {domain, normalize, journal, forecast_evidence}. NO api. Forbidden execution fragments. Six canonical.
- [ ] 3. CLI `check-outcomes --journal <path>` + test_cli.
- [ ] 4. Wiring: __init__ + test_init + README + scope unskip.
- [ ] 5. Full verify.

## Post-stage gate
- [ ] 6. Claude post-stage (Phase 1; outcome derivation correctness; no float).

## Commit (user-authorized)
- [ ] 7. `feat: add outcome tracker v0`.
