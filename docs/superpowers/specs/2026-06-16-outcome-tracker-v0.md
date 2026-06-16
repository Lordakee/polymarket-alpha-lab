# Outcome Tracker v0 Design (Stage 9)

## Purpose

Close the "self-judge verification" loop: read paper-traded markets → re-fetch
from Gamma → check if resolved → build PaperForecastEvidenceObservation records
→ feed forecast_evidence calibration report. This tells the user whether the LLM
forecast's probability estimates are actually accurate over time.

No live orders/auth/wallets. Read-only Gamma re-fetch + pure computation.

## Architecture

```text
outcome_tracker.py (NEW live-layer)
  check_outcomes(
    *, client: MarketDataClient, journal_path, config, generated_at
  ) -> OutcomeTrackingReport

  per paper-trade record:
    1. PaperTradeJournal.read(journal_path) → tuple[PaperTradeRecord]
    2. group by condition_id (dedupe YES/NO legs)
    3. for each unique market: client.list_markets → find by condition_id → normalize_gamma_market
    4. if market.closed AND resolution_status is not None: RESOLVED
       - actual_outcome_value = Decimal("1") if outcome_name == "Yes" AND resolved YES
                                 (derive from resolution_status + outcome)
       - predicted_probability = from trade record (research_fair_value_estimate or model_probability)
       - build PaperForecastEvidenceObservation
    5. if not closed: PENDING (skip observation)
  6. collect observations → build_paper_forecast_evidence_report(observations, config, generated_at)
     (IF >= 1 observation; empty → None)
```

## Public API

```text
__all__ = ("OutcomeTrackingConfig", "OutcomeTrackingReport", "check_outcomes")

OutcomeTrackingConfig (frozen):
    config_version: str = "outcome-tracker-v1"
    forecast_evidence_config: PaperForecastEvidenceConfig

OutcomeTrackingReport (frozen, paper_only=True, report_only=True):
    generated_at: datetime
    config_version: str
    total_markets_checked: int
    resolved_count: int
    pending_count: int
    observations: tuple[PaperForecastEvidenceObservation, ...]
    forecast_evidence_report: PaperForecastEvidenceReport | None  # None if 0 observations
    paper_only: bool = True
    report_only: bool = True

check_outcomes(
    *, client: MarketDataClient, journal_path: Path | str,
    config: OutcomeTrackingConfig, generated_at: datetime,
) -> OutcomeTrackingReport
```

## Outcome derivation

For a resolved binary market:
- normalize_gamma_market gives resolution_status (e.g. "Yes", "No", "Canceled")
- If resolution_status matches the trade's outcome_name (e.g. trade was BUY YES, market resolved "Yes"):
  actual_outcome_value = Decimal("1")  (the trade's side won)
- If opposite:
  actual_outcome_value = Decimal("0")  (the trade's side lost)
- If "Canceled" or ambiguous: skip (pending)

predicted_probability comes from PaperTradeRecord.research_fair_value_estimate
(the LLM forecast's fair_probability_yes, journaled at trade time).

## Validation

- paper_only/report_only with `is`.
- resolved_count + pending_count == total_markets_checked.
- len(observations) == resolved_count (only resolved markets produce observations).
- forecast_evidence_report is None iff len(observations) == 0.

## Scope tests

- Live-layer (imports api client Protocol + normalize + journal + forecast_evidence + domain).
- ALLOWED: stdlib + {domain, normalize, journal, forecast_evidence}. NO api (Protocol-only).
- Forbidden execution fragments.

## Non-goals

No live orders/auth/wallets. No multi-outcome market support (binary only). No
historical backfill (checks current resolution state only). No scheduling.

## CLI

`check-outcomes --journal <path> [--evidence-log <path>]` → check_outcomes → print summary.
