# Phase 1 Node Pre-Commit Test Manifest

Date: 2026-07-12
Status: active pre-commit test checklist for the Phase 1 baseline/direct-tests node
Scope: targeted test matrix, compile gates, full-suite triggers, collection blockers, and review-artifact hygiene

## Purpose

This manifest defines the tests to run before committing the current Phase 1
node. It is intentionally scoped to paper-only, report-only, readonly behavior
and local Supabase/Postgres configuration contracts. It does not authorize or
test live trading, account authentication, hosted-account access, wallet
handling, order signing, order submission, order cancellation, order
replacement, exchange mutation, or execution behavior.

## Changed Surface Covered By This Manifest

The current node introduces or updates Phase 1 readiness reducers, report
discovery, local Supabase/Postgres DSN validation, strategy-screening examples,
and documentation contracts. The pre-commit test set must cover these changed
surfaces directly:

- new Phase 1 report modules under `src/polymarket_alpha_lab/*_readiness_report.py`;
- updated manual operator decision packet and final go/no-go packet reports;
- market discovery candidate pool and strategy Phase 1 readiness aggregation;
- report discovery registry and CLI discovery output;
- local Supabase/Postgres-only DSN and strategy-screening config contracts;
- docs-only Phase 1 boundary language and link/term consistency tests.

## Exact Changed-File Catalog

This node contains exactly 76 changed files: 23 documentation files, 19 source
files, 33 test files, and one strategy example config. Every changed source
file is paired with a direct test in the module index, and every changed test
is included in the targeted commands or catalog/integration command below.

```text
docs/acceptance/phase-1-development-node-acceptance-checklist.md
docs/cli/phase1-report-discovery.md
docs/config/phase-1-strategy-screening-schema.md
docs/contracts/phase1-data-field-contracts.md
docs/data_dictionary/phase1-research-decision-objects.md
docs/index/phase1-module-index.md
docs/maintenance/phase1-agent-concurrency-and-review-rules.md
docs/operators/phase1-probability-event-go-no-go-runbook.md
docs/operators/phase1-strategy-stack-walkthrough.md
docs/phase1/probability-event-readonly-supabase-principles.md
docs/phases/2026-07-12-phase-1-capability-baseline.md
docs/playbooks/phase1-specialist-team-playbooks.md
docs/quality/phase-1-development-node-quality-gates.md
docs/recommendations/phase1-recommendation-explainability.md
docs/reports/phase1-report-registry.md
docs/research/source-acquisition-quality-policy.md
docs/review/2026-07-12-operating-review-rules.md
docs/review/phase1-claude-review-handoff.md
docs/risk/phase1-risk-capital-settlement-policy.md
docs/roadmap/2026-07-12-project-progress-roadmap.md
docs/strategy/phase1-probability-event-filtering-workflow.md
docs/supabase/local-supabase-operations.md
docs/testing/phase1-node-test-manifest.md
src/polymarket_alpha_lab/category_playbook_category_threshold_domain_policy_readiness.py
src/polymarket_alpha_lab/cli.py
src/polymarket_alpha_lab/forecast_context_readiness_report.py
src/polymarket_alpha_lab/information_freshness_refresh_sla_readiness_report.py
src/polymarket_alpha_lab/input_failure_degradation_readiness_report.py
src/polymarket_alpha_lab/manual_operator_decision_packet.py
src/polymarket_alpha_lab/market_discovery_candidate_pool.py
src/polymarket_alpha_lab/operator_final_go_no_go_packet_readiness_report.py
src/polymarket_alpha_lab/outcome_resolution_evidence_readiness_report.py
src/polymarket_alpha_lab/portfolio_probability_event_readiness_report.py
src/polymarket_alpha_lab/post_settlement_calibration_experience_feedback_report.py
src/polymarket_alpha_lab/probability_event_cost_adjusted_position_recommendation_report.py
src/polymarket_alpha_lab/probability_event_market_signal_risk_readiness_report.py
src/polymarket_alpha_lab/probability_event_recommendation_rank_explainability_report.py
src/polymarket_alpha_lab/report_discovery.py
src/polymarket_alpha_lab/source_scraping_tool_coverage_readiness_report.py
src/polymarket_alpha_lab/specialist_team_routing_taxonomy_readiness_report.py
src/polymarket_alpha_lab/strategy_phase1_readiness_aggregator.py
src/polymarket_alpha_lab/supabase_local_dsn.py
strategy.example.phase1-screening.json
tests/test_category_playbook_category_threshold_domain_policy_readiness.py
tests/test_cli_report_discovery.py
tests/test_forecast_context_readiness_report.py
tests/test_information_freshness_refresh_sla_readiness_report.py
tests/test_input_failure_degradation_readiness_report.py
tests/test_manual_operator_decision_packet.py
tests/test_market_discovery_candidate_pool.py
tests/test_operator_final_go_no_go_packet_readiness_report.py
tests/test_outcome_resolution_evidence_readiness_report.py
tests/test_phase1_config_no_execution_fields.py
tests/test_phase1_docs_links_and_terms.py
tests/test_phase1_docs_module_index_matches_files.py
tests/test_phase1_docs_no_secret_tokens.py
tests/test_phase1_docs_required_terms.py
tests/test_phase1_local_supabase_config_contract.py
tests/test_phase1_manual_packet_no_live_execution_terms.py
tests/test_phase1_merge_readiness_file_set.py
tests/test_phase1_no_review_scratch_references.py
tests/test_phase1_public_payload_digest_smoke.py
tests/test_phase1_readonly_boundary_scan.py
tests/test_phase1_report_discovery_smoke.py
tests/test_phase1_report_modules_import_no_io.py
tests/test_phase1_strategy_stack_smoke.py
tests/test_phase1_targeted_test_manifest.py
tests/test_portfolio_probability_event_readiness_report.py
tests/test_post_settlement_calibration_experience_feedback_report.py
tests/test_probability_event_cost_adjusted_position_recommendation_report.py
tests/test_probability_event_market_signal_risk_readiness_report.py
tests/test_probability_event_recommendation_rank_explainability_report.py
tests/test_source_scraping_tool_coverage_readiness_report.py
tests/test_specialist_team_routing_taxonomy_readiness_report.py
tests/test_strategy_phase1_readiness_aggregator.py
tests/test_supabase_local_dsn.py
```

## Python Command Convention

Use the repository's active Python environment. In this worktree,
`python -m pytest --collect-only -q` failed because `python` was not available
on `PATH`, while `python3 -m pytest --collect-only -q` collected successfully.

Pre-commit evidence may therefore use either command form:

```bash
python -m <tool>
python3 -m <tool>
```

Record the exact command used. If a virtual environment supplies `python`, use
the project-standard `python` form from the quality gates. If it does not,
`python3` is the equivalent command for this node.

## Targeted Test Matrix

Run the smallest targeted set that covers the changed behavior before full
suite escalation. The recommended targeted command for this node is:

```bash
python3 -m pytest \
  tests/test_category_playbook_category_threshold_domain_policy_readiness.py \
  tests/test_forecast_context_readiness_report.py \
  tests/test_information_freshness_refresh_sla_readiness_report.py \
  tests/test_input_failure_degradation_readiness_report.py \
  tests/test_manual_operator_decision_packet.py \
  tests/test_market_discovery_candidate_pool.py \
  tests/test_operator_final_go_no_go_packet_readiness_report.py \
  tests/test_outcome_resolution_evidence_readiness_report.py \
  tests/test_portfolio_probability_event_readiness_report.py \
  tests/test_post_settlement_calibration_experience_feedback_report.py \
  tests/test_probability_event_cost_adjusted_position_recommendation_report.py \
  tests/test_probability_event_market_signal_risk_readiness_report.py \
  tests/test_probability_event_recommendation_rank_explainability_report.py \
  tests/test_source_scraping_tool_coverage_readiness_report.py \
  tests/test_specialist_team_routing_taxonomy_readiness_report.py \
  tests/test_strategy_phase1_readiness_aggregator.py
```

Acceptance requirements:

- every changed report/reducer module has direct tests for pass/watch/block or
  equivalent status transitions;
- dataclasses remain frozen, exact-type guarded, Decimal-normalized where
  applicable, and hard-flag guarded with `paper_only=True`,
  `report_only=True`, and `readonly=True`;
- payload and digest tests remain deterministic;
- module scope tests confirm there are no IO, network, live-trading,
  execution, account, wallet, credential, or order-mutation surfaces.

## Discovery, CLI, And Boundary Tests

Run these targeted tests whenever report discovery, CLI discovery output,
documentation links, strategy example config, local Supabase/Postgres
contracts, or Phase 1 readonly terms changed:

```bash
python3 -m pytest \
  tests/test_cli_report_discovery.py \
  tests/test_phase1_config_no_execution_fields.py \
  tests/test_phase1_docs_links_and_terms.py \
  tests/test_phase1_docs_required_terms.py \
  tests/test_phase1_local_supabase_config_contract.py \
  tests/test_phase1_manual_packet_no_live_execution_terms.py \
  tests/test_phase1_readonly_boundary_scan.py \
  tests/test_phase1_report_discovery_smoke.py \
  tests/test_phase1_report_modules_import_no_io.py \
  tests/test_supabase_local_dsn.py
```

Acceptance requirements:

- report discovery imports new modules without IO side effects;
- discoverable builders, public dataclasses, and hard flags remain visible;
- CLI discovery remains report-only and does not add DSN, account, wallet,
  order, execution, or live-trading flags;
- docs and example config preserve local Supabase/Postgres-only persistence;
- docs use placeholders for DSNs and secrets;
- readonly boundary scans still reject live execution language outside explicit
  forbidden-field tests or policy exclusions.

## Focused Smoke Commands

Use focused commands for fast iteration before running the full targeted matrix:

```bash
python3 -m pytest tests/test_phase1_report_discovery_smoke.py
python3 -m pytest tests/test_phase1_report_modules_import_no_io.py
python3 -m pytest tests/test_phase1_readonly_boundary_scan.py
python3 -m pytest tests/test_phase1_local_supabase_config_contract.py
python3 -m pytest tests/test_strategy_phase1_readiness_aggregator.py
```

These commands do not replace the targeted matrix. They are intended to isolate
failures in registry import behavior, readonly boundaries, local persistence
contracts, and aggregation logic.

## Catalog And Integration Tests

Run the seven catalog/integration tests that close the changed-test manifest
and protect reverse coverage of the current node:

```bash
python3 -m pytest \
  tests/test_phase1_docs_module_index_matches_files.py \
  tests/test_phase1_docs_no_secret_tokens.py \
  tests/test_phase1_merge_readiness_file_set.py \
  tests/test_phase1_no_review_scratch_references.py \
  tests/test_phase1_public_payload_digest_smoke.py \
  tests/test_phase1_strategy_stack_smoke.py \
  tests/test_phase1_targeted_test_manifest.py
```

These tests are part of the 33-file changed-test set. They are required even
when the report-specific and discovery/boundary commands already pass.

## Compileall Scope

For this node, compile the changed source and test surfaces plus any imported
Phase 1 package modules:

```bash
python3 -m compileall \
  src/polymarket_alpha_lab \
  tests/test_category_playbook_category_threshold_domain_policy_readiness.py \
  tests/test_cli_report_discovery.py \
  tests/test_forecast_context_readiness_report.py \
  tests/test_information_freshness_refresh_sla_readiness_report.py \
  tests/test_input_failure_degradation_readiness_report.py \
  tests/test_manual_operator_decision_packet.py \
  tests/test_market_discovery_candidate_pool.py \
  tests/test_operator_final_go_no_go_packet_readiness_report.py \
  tests/test_outcome_resolution_evidence_readiness_report.py \
  tests/test_phase1_config_no_execution_fields.py \
  tests/test_phase1_docs_links_and_terms.py \
  tests/test_phase1_docs_required_terms.py \
  tests/test_phase1_local_supabase_config_contract.py \
  tests/test_phase1_manual_packet_no_live_execution_terms.py \
  tests/test_phase1_readonly_boundary_scan.py \
  tests/test_phase1_report_discovery_smoke.py \
  tests/test_phase1_report_modules_import_no_io.py \
  tests/test_portfolio_probability_event_readiness_report.py \
  tests/test_post_settlement_calibration_experience_feedback_report.py \
  tests/test_probability_event_cost_adjusted_position_recommendation_report.py \
  tests/test_probability_event_market_signal_risk_readiness_report.py \
  tests/test_probability_event_recommendation_rank_explainability_report.py \
  tests/test_source_scraping_tool_coverage_readiness_report.py \
  tests/test_specialist_team_routing_taxonomy_readiness_report.py \
  tests/test_strategy_phase1_readiness_aggregator.py \
  tests/test_supabase_local_dsn.py
```

If time permits or if any import path uncertainty remains, use the broader gate:

```bash
python3 -m compileall src tests
```

Do not commit generated `__pycache__` or bytecode artifacts.

## Full Pytest Trigger Conditions

Run full `pytest` before the node is considered commit-ready when any of these
conditions are true:

- report discovery, CLI discovery, import-time behavior, or shared registry
  behavior changed;
- a changed module is imported by an existing public report, aggregator,
  packet, or docs contract test outside the targeted matrix;
- local Supabase/Postgres config validation, DSN validation, or persistence
  boundary language changed;
- docs terms changed in a way that could affect existing docs tests;
- targeted tests fail at least once and the fix touches shared helpers,
  shared constants, public dataclasses, or payload/digest format;
- `pytest --collect-only` exposes new collection warnings, import errors, or
  deselected/renamed tests that were not part of the node plan;
- the review packet is being prepared for commit or push eligibility.

Recommended full-suite command:

```bash
python3 -m pytest
```

Record the exit code and summary. Do not treat a targeted pass as a substitute
for full-suite evidence when one of the trigger conditions applies.

## Known Collection Blockers And Handling

Known collection status for this worktree:

- `python -m pytest --collect-only -q` fails when `python` is absent from
  `PATH`;
- `python3 -m pytest --collect-only -q` collects successfully under Python
  3.12.3.

Handling rule:

- if collection fails because the executable is missing, rerun with the active
  environment's Python executable and document the substitution;
- if collection fails because of an import error, syntax error, fixture error,
  or test discovery error, stop and fix the root cause before running targeted
  tests;
- if collection succeeds but emits unexpected warnings or missing-test signals,
  document them in the review packet and either resolve them or mark the node
  blocked;
- do not skip, xfail, rename, or deselect tests only to get collection green.

## Review Artifact Hygiene

Local scratch review artifacts are temporary output for review packets, review
prompts, generated diffs, status files, and reviewer transcripts. They must not
be committed as part of this node.

Before commit:

```bash
git status --short --untracked-files=all
git diff --check
git diff --name-only --cached
```

Acceptance requirements:

- local scratch review artifacts remain untracked or otherwise excluded from
  the commit;
- generated review files are summarized in the handoff instead of added to the
  repository;
- no review artifact exposes raw DSNs, credentials, private source payloads,
  account details, wallet material, order ids, or live-account data;
- if a review summary is needed in-tree, place only sanitized documentation
  under the relevant `docs/` path.

## Minimum Pre-Commit Evidence Record

The handoff for this node should record:

- exact Python executable used;
- targeted test matrix command and result;
- discovery/boundary targeted command and result;
- compileall command and result;
- full `python3 -m pytest` result or the explicit trigger analysis if not run;
- `python3 -m pytest --collect-only -q` result;
- `git diff --check` result;
- confirmation that local scratch review artifacts are not staged or committed;
- confirmation that changed behavior remains paper-only, report-only,
  readonly, and local Supabase/Postgres-only where persistence is involved.
