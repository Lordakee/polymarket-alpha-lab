# Paper Recommendation Cycle Integration As-Built Plan

> **For agentic workers:** this file is now an as-built reference plus future-only integration checklist. The bundle and JSONL log modules exist; do not use this document as a module-creation plan.

**Goal:** Keep the paper-only recommendation orchestration layer aligned with the current reducer API and prepare the next cycle/runner integration stage.

**Architecture:** The implemented integration step is pure reducers plus append-only JSONL storage. It consumes already-built paper-only assessment/readiness reports and produces recommendation, selection-policy, and explanation reports with strict readonly/report-only flags. It still performs no live trading, auth, wallet, private-key handling, exchange writes, or executable order placement.

**Tech Stack:** Python dataclasses, `Decimal` math, pytest, existing JSON recovery patterns, CodeGraph for code navigation.

---

## As-Built File Structure

- `src/polymarket_alpha_lab/strategy_recommendation_bundle.py`
  - Owns `PaperStrategyRecommendationBundleConfig`, `PaperStrategyRecommendationBundleReport`, and `build_paper_strategy_recommendation_bundle_report`.
  - Bundles recommendation, selection policy, and explanation outputs.
- `tests/test_strategy_recommendation_bundle.py`
  - Covers bundle construction, strict types, hard flags, timestamp normalization, and nested consistency.
- `src/polymarket_alpha_lab/strategy_recommendation_log.py`
  - Owns append/read helpers for recommendation bundle JSONL logs.
  - Uses JSON recovery/from-jsonable patterns and preserves `Decimal` and `datetime` values.
- `tests/test_strategy_recommendation_log.py`
  - Covers append/read, empty logs, missing log behavior, corrupt row recovery, strict bundle type checks, and hard flags.
- `src/polymarket_alpha_lab/strategy_recommendation_history.py`
  - Owns readonly history summaries across recommendation reports.
- `tests/test_strategy_recommendation_history.py`
  - Covers empty/nonempty history summaries, ordering, strict source types, flags, and direct-constructor consistency.
- `docs/strategy-recommendation-layer.md`
  - Documents the bundle/log/history flow as paper-only/report-only/readonly.
- `tests/test_strategy_recommendation_layer_scope.py`
  - Keeps recommendation-layer modules inside no-live-trading boundary checks.

## As-Built API

### Bundle Reducer

`PaperStrategyRecommendationBundleConfig` fields:

- `config_version`
- `recommendation_config`
- `selection_policy_config`

`PaperStrategyRecommendationBundleReport` fields:

- `generated_at`
- `config_version`
- `candidate_count`
- `recommend_count`
- `selected_count`
- the aggregate selected-position notional field
- `recommendation_report`
- `selection_policy_report`
- `explanation_report`
- `paper_only`
- `report_only`
- `readonly`

Public builder:

```python
build_paper_strategy_recommendation_bundle_report(
    assessment_report,
    readiness_report,
    *,
    config,
    generated_at,
)
```

Current behavior:

- Validates exact bundle config type and `datetime`.
- Calls the recommendation, selection policy, and explanation builders.
- Requires nested report timestamps to match the bundle timestamp.
- Requires bundle `candidate_count` to match recommendation `candidate_count`, selection `row_count`, and explanation `recommendation_count`.
- Requires selection rows and explanation rows to align position-by-position with recommendation rows.
- Enforces `paper_only`, `report_only`, and `readonly` on the bundle and nested reports.

### Bundle JSONL Log

Public helpers:

```python
append_paper_strategy_recommendation_bundle_log(path, report)
read_paper_strategy_recommendation_bundle_log(path)
```

Current behavior:

- Appends one `PaperStrategyRecommendationBundleReport` per JSONL row.
- Serializes `Decimal` values as strings and normalizes datetimes to UTC ISO strings.
- Rejects floats and non-finite Decimal values.
- Reconstructs typed nested dataclasses with `from_jsonable`.
- Skips blank lines when reading.
- Returns an empty tuple for an empty existing file.
- Propagates `FileNotFoundError` when the requested log path does not exist.
- Fails fast on invalid JSON or malformed report rows with line-numbered `ValueError` messages.

### Recommendation History Reducer

`PaperStrategyRecommendationHistorySourceSummary` fields:

- `generated_at`
- `config_version`
- `candidate_count`
- `recommend_count`
- `watch_count`
- `reject_count`

`PaperStrategyRecommendationHistoryReport` fields:

- `generated_at`
- `config_version`
- `source_report_count`
- `total_candidate_count`
- `total_recommend_count`
- `total_watch_count`
- `total_reject_count`
- `first_generated_at`
- `latest_generated_at`
- `latest_config_version`
- `latest_candidate_count`
- `latest_recommend_count`
- `latest_watch_count`
- `latest_reject_count`
- `source_summaries`
- `paper_only`
- `report_only`
- `readonly`

Public builder:

```python
build_paper_strategy_recommendation_history_report(
    recommendation_reports,
    *,
    config_version,
    generated_at,
)
```

Current behavior:

- Reduces paper-only recommendation reports into deterministic readonly history summaries.
- Sorts source summaries by generated timestamp and config version.
- Tracks total and latest action counts.
- Validates empty-history and nonempty-history consistency through direct constructors.

## Historical Implementation Notes

The original cycle integration plan described failing tests for modules that had not been created yet. That was valid only before `strategy_recommendation_bundle.py` and `strategy_recommendation_log.py` existed. Both modules now exist, and the remaining work is integration, documentation, and hardening.

## Future Tasks Only

- [ ] **Cycle/runner integration:** decide whether bundle creation belongs inside `run_strategy_cycle` while assessment/readiness reports are in scope, or in a wrapper that receives those reports explicitly.
- [ ] **CLI integration:** wire any future command surface to existing bundle/log/history builders without package-root exports or live execution terminology.
- [ ] **Documentation hardening:** keep `docs/strategy-recommendation-layer.md` synchronized with the current bundle, log, history, recommendation, selection, and explanation field names.
- [ ] **Test hardening:** add regression tests for cycle/runner handoff once recommendation reports are produced as part of a broader run.
- [ ] **Boundary hardening:** extend `tests/test_strategy_recommendation_layer_scope.py` when new integration files are added so forbidden live-trading/auth/key/wallet/order-placement language stays out.
- [ ] **Verification:** for future patches, run focused bundle/log/history/scope tests, relevant CLI/cycle tests, `compileall`, full pytest, `git diff --check`, and `codegraph sync`.
