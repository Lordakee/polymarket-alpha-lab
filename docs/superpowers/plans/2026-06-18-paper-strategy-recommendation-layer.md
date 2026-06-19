# Paper Strategy Recommendation Layer As-Built Plan

> **For agentic workers:** this file is now an as-built reference plus future-only follow-up checklist. The original test-first implementation tasks have landed; do not treat this document as instructions to recreate modules, tests, or CLI surfaces.

**Goal:** Keep the paper-only recommendation and selection layer aligned with the current reducer API. The layer turns candidate assessment and readiness gates into auditable ranked recommendations, paper sizing suggestions, and deterministic explanations without live trading or order placement.

**Architecture:** Reducer-only modules use frozen dataclasses, `Decimal` math, direct-constructor validation, deterministic ordering, and hard `paper_only`, `report_only`, and `readonly` flags. The selection policy emits paper sizing suggestions only; it never emits executable orders.

**Tech Stack:** Python dataclasses, `Decimal`, pytest, CodeGraph, existing `polymarket_alpha_lab` paper-only reducers.

---

## As-Built File Ownership

- `src/polymarket_alpha_lab/strategy_candidate_recommendation.py`: recommendation ranking reducer.
- `tests/test_strategy_candidate_recommendation.py`: recommendation ranking and validation coverage.
- `src/polymarket_alpha_lab/paper_strategy_selection_policy.py`: paper-only sizing and selection policy reducer.
- `tests/test_paper_strategy_selection_policy.py`: selection caps and validation coverage.
- `src/polymarket_alpha_lab/strategy_recommendation_explain.py`: deterministic explanation reducer.
- `tests/test_strategy_recommendation_explain.py`: explanation output and validation coverage.
- `src/polymarket_alpha_lab/settlement_freshness_gate.py`: direct-constructor semantic hardening.
- `tests/test_settlement_freshness_gate.py`: settlement hardening coverage.
- Core recommendation reducers remain module-level APIs. The bundle and log
  helpers are intentionally imported directly from their defining modules by
  the read-only CLI and artifact recovery surface; they are not package-root
  exports.

## As-Built API

### Recommendation Reducer

`PaperStrategyCandidateRecommendationConfig` fields:

- `config_version`
- `min_recommendation_score`

`PaperStrategyCandidateRecommendationRow` fields:

- `market_slug`
- `question`
- `action`
- `assessment_status`
- `readiness_status`
- `selected_side`
- `scoring_side`
- `recommendation_score`
- `reason_codes`

`PaperStrategyCandidateRecommendationReport` fields:

- `generated_at`
- `config_version`
- `readiness_overall_status`
- `candidate_count`
- `recommend_count`
- `watch_count`
- `reject_count`
- `recommendation_rows`
- `paper_only`
- `report_only`
- `readonly`

Public builder:

```python
build_paper_strategy_candidate_recommendation_report(
    assessment_report,
    readiness_report,
    *,
    config,
    generated_at,
)
```

Current behavior:

- Validates exact assessment/readiness report types and paper/report/readonly flags.
- Builds one recommendation row per assessment row.
- Uses assessment `selected_side` and `scoring_side`.
- Quantizes `recommendation_score` to `0.000001`.
- Emits actions `recommend`, `watch`, or `reject`.
- Orders rows by action priority, descending `recommendation_score`, then `market_slug`.
- Validates report counts and deterministic row order through direct constructors.

### Selection Policy Reducer

`PaperStrategySelectionPolicyConfig` fields:

- `config_version`
- `base_position_notional`
- `max_position_notional`
- `max_total_notional`

`PaperStrategySelectionPolicyRow` fields:

- `market_slug`
- `question`
- `source_action`
- `selected_side`
- `recommendation_score`
- `decision`
- `suggested_position_notional`
- `selected_position_notional`
- `reason_codes`

`PaperStrategySelectionPolicyReport` fields:

- `generated_at`
- `config_version`
- `row_count`
- `selected_count`
- `skipped_count`
- `not_selected_count`
- the aggregate selected-position notional field
- `selection_rows`
- `paper_only`
- `report_only`
- `readonly`

Public builder:

```python
build_paper_strategy_selection_policy_report(
    recommendation_report,
    *,
    config,
    generated_at,
)
```

Current behavior:

- Accepts only `PaperStrategyCandidateRecommendationReport` input.
- Converts non-`recommend` source rows into `not_selected` rows.
- Calculates `suggested_position_notional` from score-weighted base notional capped per position.
- Emits `selected_position_notional` only for selected rows, otherwise quantized zero.
- Enforces total cap behavior with `skipped` rows once the cap is reached.
- Uses `row_count` to match `selection_rows`; the recommendation report owns `candidate_count`.

### Recommendation Explanation Reducer

`PaperStrategyRecommendationExplanationRow` fields:

- `market_slug`
- `action`
- `selected_side`
- `recommendation_score`
- `primary_reason_code`
- `reason_codes`
- `explanation`

`PaperStrategyRecommendationExplanationReport` fields:

- `generated_at`
- `source_config_version`
- `recommendation_count`
- `recommend_count`
- `watch_count`
- `reject_count`
- `explanation_rows`
- `paper_only`
- `report_only`
- `readonly`

Public builder:

```python
build_paper_strategy_recommendation_explanation_report(
    recommendation_report,
    *,
    generated_at,
)
```

Current behavior:

- Accepts only `PaperStrategyCandidateRecommendationReport` input.
- Preserves recommendation row order.
- Uses the first reason code as `primary_reason_code`, or `no_reason_code` when absent.
- Requires canonical explanation text of the form `"{action} {selected_side} because {primary_reason_code} (score {recommendation_score})"`.

### Settlement Constructor Hardening

Current behavior:

- Settlement freshness reports reject pending counts and stale pending counts when no source reports exist.
- Row-level semantic validation requires canonical reason strings that match observed gate values and status.

## Historical Implementation Notes

The first implementation pass followed the original plan:

- Add failing tests for recommendation, selection, explanation, and settlement hardening.
- Implement the reducers with direct-constructor validation.
- Run focused tests, compile checks, full suite, diff checks, CodeGraph sync, and review before merge.

Those steps are historical. Future workers should not leave implementation tasks open for these modules unless they are adding new behavior.

## Future Tasks Only

- [ ] **Cycle integration:** map where recommendation bundles should be built relative to `strategy_cycle`, `runner`, and CLI entry points while source assessment/readiness reports are still available.
- [ ] **Documentation hardening:** keep user-facing strategy recommendation docs synchronized with the current dataclass field names, especially `scoring_side`, `row_count`, `suggested_position_notional`, and `selected_position_notional`.
- [ ] **Test hardening:** add focused regression coverage for cross-report field alignment when cycle/runner integration starts passing recommendation outputs between reducers.
- [ ] **Scope hardening:** keep no-live-trading boundary tests aligned with any new recommendation-layer modules or CLI surfaces.
- [ ] **Operational verification:** when future integration changes land, run focused recommendation tests, relevant CLI/cycle tests, `compileall`, full pytest, `git diff --check`, and `codegraph sync`.
