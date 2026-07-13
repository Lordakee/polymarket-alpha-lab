# Phase 1 Research Decision Objects Data Dictionary

This dictionary documents the read-only Phase 1 objects that move a paper
market candidate from research intake through human decision review and
settlement feedback. It is a documentation-only contract; it does not create a
new runtime surface, migration, CLI option, Supabase table, or execution path.

All objects in this dictionary are paper-only, report-only, and readonly:

```text
paper_only = true
report_only = true
readonly = true
```

Those flags are part of the object contract and must be preserved on nested
rows, payloads, DB rows, and recovered reports when the object is persisted to
local Supabase/Postgres.

## Common Field Rules

- Identifiers are canonical nonblank strings unless the owning reducer narrows
  them to public identifiers or a fixed enum.
- Timestamps are timezone-aware `datetime` values normalized to UTC before
  payload or DB materialization. JSON payloads use ISO-8601 strings.
- Decimal values are Python `Decimal` values. JSON payloads and persisted JSONB
  store Decimal values as canonical strings, never floats.
- Fixed-six Decimal fields use quantum `0.000001`. Count Decimals use integral
  values where noted.
- Digest/hash fields are lowercase SHA-256 hex strings computed from canonical
  JSON using sorted keys and compact separators unless the object defines a
  derived validation digest over a narrowed public payload.
- Nullable fields keep `null` distinct from zero. Unknown probabilities, costs,
  timestamps, and settlement timing fields must remain `null`, not `0`.
- Reason-code arrays are deterministic, de-duplicated where the reducer
  enforces uniqueness, and must use canonical nonblank strings or known enums.

## Candidate Market

Canonical paper candidate market data is represented by
`PaperStrategyCandidateResearchQueueRow` and persisted as part of
`PaperStrategyCandidateResearchQueueReport`.

| Field | Type | Precision / Shape | Contract |
| --- | --- | --- | --- |
| `research_rank` | int | positive, contiguous | Rank inside the research queue. |
| `queue_rank` | int | positive, contiguous | Source queue rank; report validation requires contiguous ordering. |
| `market_slug` | string | canonical | Candidate market key and join key across candidate reports. |
| `question` | string | canonical | Public market question text. |
| `selected_side` | enum | `yes`, `no`, `none` | Side selected by upstream paper selection policy. |
| `scoring_side` | enum/string | canonical side value | Side used for candidate assessment scoring. |
| `source_action` | enum | `recommend`, `watch`, `reject` | Upstream action from the paper queue. |
| `decision` | enum | `selected`, `skipped`, `not_selected` | Paper selection decision. |
| `queue_status` | enum | `ready`, `watch`, `blocked` | Upstream queue status. |
| `research_status` | enum | `ready`, `watch`, `blocked` | Derived from `queue_status`; must match. |
| `research_bucket` | string | canonical | Research grouping from candidate assessment. |
| `assessment_status` | enum | `ready`, `watch`, `blocked` | Candidate assessment status. |
| `source_status` | string | canonical | Source evidence status from assessment. |
| `readiness_status` | string | canonical | Recommendation readiness status. |
| `recommendation_score` | Decimal | fixed-six score | Upstream recommendation score. |
| `readiness_score` | Decimal | fixed-six score | Readiness score. |
| `screening_score` | Decimal | fixed-six nonnegative | Screening score. |
| `net_edge_per_share` | Decimal or null | fixed-six signed | Candidate edge before total cost; nullable when evidence is missing. |
| `total_cost_per_share` | Decimal or null | fixed-six nonnegative | Total paper cost per share; nullable when no cost report exists. |
| `confidence` | Decimal or null | fixed-six score | Assessment confidence. |
| `spread` | Decimal or null | fixed-six nonnegative | Market spread evidence. |
| `resolution_risk` | Decimal or null | fixed-six nonnegative | Resolution-risk score. |
| `suggested_notional` | Decimal | fixed-six nonnegative | Paper notional suggested by upstream queue. |
| `selected_position_notional` | Decimal | fixed-six nonnegative | Equals `suggested_notional` only when `decision=selected`; otherwise zero. |
| `primary_reason_code` | string | canonical | Primary explanation code; must appear in `reason_codes`. |
| `research_priority_score` | Decimal | fixed-six score | Average of recommendation and readiness scores. |
| `evidence_gap_codes` | tuple[string] | canonical reason codes | Subset of `reason_codes` representing research evidence gaps. |
| `reason_codes` | tuple[string] | canonical reason codes | Combined upstream assessment, recommendation, selection, and explanation codes. |
| `explanation` | string | canonical | Public explanation text. |
| `paper_only`, `report_only`, `readonly` | bool | all true | Required hard safety flags. |

Report-level candidate fields include `generated_at`, `config_version`,
`source_config_version`, `action_status`, `recommended_next_step`,
`source_reason_code_counts`, `research_status`, candidate/status/decision count
fields, notional totals, score rollups, `primary_reason_code_counts`, `rows`,
`reason_codes`, and the hard safety flags.

## Research Evidence

Research evidence covers source observations and settlement evidence packets
used to justify paper decisions. The narrow settlement evidence packet shape is
represented by `ResearchSettlementEvidenceItem`,
`ResearchSettlementRuleMapping`, `ResearchSettlementAmbiguityPoint`, and
`ResearchSettlementEvidencePacketRow`.

| Object / Field | Type | Precision / Shape | Contract |
| --- | --- | --- | --- |
| `packet_id` | string | public identifier | Stable packet key joining evidence, mapping, ambiguity, and packet rows. |
| `event_id` | string | public identifier | Event key for settlement research. |
| `evidence_id` | string | public identifier | Evidence item key. |
| `source_id` | string | public identifier | Public source key; raw source text, URLs, credentials, and paths are not persisted in this contract. |
| `source_family` | string | public identifier | Source-family grouping for independence checks. |
| `evidence_type` | enum | `official_result`, `resolution_rule`, `settlement_time` and configured types | Type of settlement evidence. |
| `observed_at` | datetime | UTC | Time the evidence was observed. |
| `relevance_score` | Decimal | fixed-six ratio | Evidence relevance ratio. |
| `supports_resolution` | bool | exact bool | Whether the evidence supports settlement resolution. |
| `public_note` | string or null | normalized public text | Optional redacted note only; no raw evidence payloads. |
| `rule_id` | string | public identifier | Resolution rule key. |
| `mapping_status` | enum | known mapping statuses | Status linking a rule to evidence. |
| `ambiguity_id` | string | public identifier | Ambiguity row key. |
| `severity_score` | Decimal | fixed-six ratio | Ambiguity severity. |
| `resolved` | bool | exact bool | Whether the ambiguity is resolved. |
| `paper_only`, `report_only`, `readonly` | bool | all true | Required hard safety flags. |

Research evidence payloads must reject unsafe live-surface fields and must not
carry account, wallet, private key, auth, order, execution, or exchange mutation
material.

## Prediction Output

Prediction output is documented through the forecast-source blend digest and
the probability sanity report. These objects are diagnostics for paper
decisioning, not live forecasts for execution.

### Forecast Source Blend

| Field | Type | Precision / Shape | Contract |
| --- | --- | --- | --- |
| `candidate_id` | string | canonical | Candidate key. |
| `source_id` | string | canonical | Forecast source key inside a candidate. |
| `source_kind` | enum | `model`, `team`, `market`, `research`, `other` | Source category. |
| `probability` | Decimal | fixed-six ratio | Source probability. |
| `reliability_weight` | Decimal | fixed-six nonnegative | Source weighting value. |
| `observed_at` | datetime | UTC | Observation time for the source probability. |
| `reference` | string or null | redacted if sensitive | Optional public reference; sensitive fragments are replaced by `<redacted>`. |
| `model_forecast`, `team_forecast`, `market_price` | Decimal or null | fixed-six ratio | Candidate-level forecast inputs. |
| `source_weighted_probability` | Decimal or null | fixed-six ratio | Weighted source probability. |
| `blended_probability` | Decimal or null | fixed-six ratio | Weighted blend of model, team, market, and source inputs. |
| `disagreement_gap` | Decimal or null | fixed-six ratio delta | Max-min probability disagreement. |
| `applied_disagreement_cap` | Decimal | fixed-six ratio delta | Cap applied when disagreement exceeds thresholds. |
| `candidate_probability` | Decimal or null | fixed-six ratio | Final paper candidate probability after cap. |
| `source_count` | Decimal | integral count | Number of source rows. |
| `source_reliability_weight` | Decimal | fixed-six nonnegative | Sum of source reliability weights. |
| `latest_observed_at` | datetime or null | UTC | Latest nested source observation time. |
| `status` | enum | `clear`, `watch`, `blocked` | Derived from row reason codes. |
| `reason_codes` | tuple[string] | known reason codes | Deterministic row or report reasons. |
| `paper_only`, `report_only`, `readonly` | bool | all true | Required hard safety flags. |

### Probability Sanity

forecast_probability always denotes canonical Decimal P(YES), regardless of selected_side; selected_side identifies the paper-review side being evaluated and never reorients forecast_probability; P(NO) is 1 - P(YES).

| Field | Type | Precision / Shape | Contract |
| --- | --- | --- | --- |
| `forecast_probability` | Decimal | fixed-six ratio | Canonical event `P(YES)`. |
| `market_probability` | Decimal | fixed-six ratio | Market implied probability. |
| `bid_implied_probability` | Decimal | fixed-six ratio | Bid implied probability. |
| `ask_implied_probability` | Decimal | fixed-six ratio | Ask implied probability. |
| `bid_ask_mid_probability` | Decimal | fixed-six ratio | Derived bid/ask midpoint probability. |
| `cost_adjusted_threshold` | Decimal | fixed-six ratio | Cost-adjusted threshold probability. |
| `edge_to_threshold` | Decimal | fixed-six signed | Edge versus threshold. |
| `probability_gap` | Decimal | fixed-six signed | Forecast minus market probability. |
| `bid_ask_mid_gap` | Decimal | fixed-six signed | Market minus bid/ask midpoint. |
| `threshold_probability_gap` | Decimal | fixed-six signed | Forecast minus threshold. |
| `sanity_status` | enum | `ready`, `blocked` | Sanity gate result. |
| `inconsistency_reasons`, `blocker_reasons`, `reason_codes` | tuple[string] | canonical reason codes | Deterministic reason arrays. |

## Cost Snapshot

Cost snapshots use `PaperTradeCostAuditReport` and
`PaperTradeCostAuditReportDbRow` for local Supabase/Postgres history.

| Field | Type | Precision / Shape | Contract |
| --- | --- | --- | --- |
| `report_sha256` | string | lowercase SHA-256 | Digest of canonical `payload_json`. |
| `generated_at` | datetime | UTC | Report generation timestamp. |
| `config_version` | string | canonical | Cost audit configuration version. |
| `trade_count` | int | nonnegative | Number of paper trade records in the snapshot. |
| `total_filled_size` | Decimal | canonical nonnegative | Filled paper size total. |
| `total_requested_size` | Decimal | canonical nonnegative | Requested paper size total. |
| `fill_rate` | Decimal or null | ratio | Fill rate; null when unavailable. |
| `mean_theoretical_edge` | Decimal or null | signed | Mean theoretical edge. |
| `mean_cost_adjusted_edge` | Decimal or null | signed | Mean edge after costs. |
| `mean_edge_cost_drag` | Decimal or null | nonnegative | Mean cost drag. |
| `total_edge_cost_drag` | Decimal or null | nonnegative | Total cost drag. |
| `mean_research_slippage` | Decimal or null | nonnegative | Mean research slippage. |
| `mean_fill_slippage` | Decimal or null | nonnegative | Mean fill slippage. |
| `partial_fill_count` | int | nonnegative | Count of partial fills. |
| `negative_cost_adjusted_edge_count` | int | nonnegative | Count of rows where costs erased edge. |
| `largest_single_trade_cost_drag` | Decimal or null | nonnegative | Largest single paper-trade cost drag. |
| `payload_json` | JSON object | canonical payload | Full report payload; Decimal values are strings. |
| `paper_only`, `report_only`, `readonly` | bool | all true | Required hard safety flags. |

The scalar columns are query aids only. `payload_json` remains the canonical
read-only report payload and must recover a compatible report.

## Expert Team Memory

Expert team memory is documented through team memory readiness and specialist
memory conflict scoring.

| Object / Field | Type | Precision / Shape | Contract |
| --- | --- | --- | --- |
| `team_id` | string | team identifier | Team key. |
| `specialist_id` | string | public identifier | Specialist key. |
| `memory_case_family` | string | public identifier | Family of comparable memory cases. |
| `similar_case_count` | Decimal | nonnegative integral | Count of similar cases. |
| `conflicting_case_count` | Decimal | nonnegative integral | Count of conflicting cases; must not exceed similar cases. |
| `conclusion_diversity_score` | Decimal | fixed-six ratio | Diversity of prior conclusions. |
| `contradiction_severity_score` | Decimal | fixed-six ratio | Severity of contradictions. |
| `stale_resolution_ratio` | Decimal | fixed-six ratio | Share of stale resolutions. |
| `unresolved_conflict_ratio` | Decimal | fixed-six ratio | Share of unresolved conflicts. |
| `memory_conflict_score` | Decimal | fixed-six ratio | Derived memory conflict score. |
| `memory_conflict_status` | enum | pass/watch/block style status | Derived conflict status. |
| `hard_flag` | bool | exact bool | Whether memory conflict creates a hard stop. |
| `digest_status` | enum | pass/watch/blocked digest status | Team memory readiness report status. |
| `recommended_next_step` | string | canonical | Operator next step for memory readiness. |
| `team_count`, `pass_count`, `watch_count`, `blocked_count` | int | nonnegative | Team memory readiness rollups. |
| `source_statuses` | tuple[object] | deterministic rows | Per-team diagnostic source status rows. |
| `source_config_versions` | tuple[tuple[string,string]] | deterministic | Source config version readback by team. |
| `reason_code_counts`, `reason_codes` | tuple | deterministic | Memory readiness reasons and counts. |
| `paper_only`, `report_only`, `readonly` | bool | all true | Required hard safety flags. |

## Human Decision Package

Human decision packages use `ManualOperatorDecisionPacket`, the optional
go/no-go wrapper, and final boundary reports. They are public, redacted,
operator-review payloads only.

| Field | Type | Precision / Shape | Contract |
| --- | --- | --- | --- |
| `generated_at` | datetime | UTC | Packet generation timestamp. |
| `config_version` | string | fixed known version | Manual decision packet schema version. |
| `checklist_area` | enum | `research`, `evidence`, `source_authority`, `microstructure`, `cost`, `timing`, `team_memory` | Fact or summary area. |
| `support_status` | enum | `pass`, `watch`, `block` | Area support status. |
| `reason_summary` | string | public redacted text | Public reason summary; unsafe tokens are rejected. |
| `blocker_summary` | string or null | public redacted text | Required only when `support_status=block`. |
| `support_weight` | Decimal | nonnegative | Fact support weight. |
| `research_status`, `evidence_status`, `source_authority_status`, `microstructure_status`, `cost_status`, `timing_status`, `team_memory_status` | enum | `pass`, `watch`, `block` | Reduced area statuses. |
| `reason_summaries` | tuple[object] | one per checklist area | Ordered area summaries. |
| `unresolved_blockers` | tuple[string] | public redacted text | Distinct blocker summaries. |
| `next_manual_review_action` | enum | known manual review actions | Derived from statuses and blockers. |
| `manual_packet_payload_digest`, `ready_queue_payload_digest`, `audit_trail_payload_digest`, `public_output_payload_digest`, `payload_digest` | string | lowercase SHA-256 | Payload digests in go/no-go package. |
| `source_payload_digests` | tuple[mapping] | public digest entries | Digest references for source review surfaces. |
| `go_no_go_status` | enum | `go`, `no_go` | Final public operator packet status. |
| `paper_review_only` | bool | true where present | Manual review-only flag for final boundary reports. |
| `boundary_check_count`, `pass_check_count`, `watch_check_count`, `blocked_check_count` | Decimal | integral count | Final boundary check counts. |
| `ready_ratio` | Decimal | fixed-six ratio | Final boundary readiness ratio. |
| `derived_validation_digest` | string | lowercase SHA-256 | Digest of final boundary public payload. |
| `paper_only`, `report_only`, `readonly` | bool | all true | Required hard safety flags. |

Manual decision text must not include raw market/source references, account
state, credentials, DSNs, order/trade terms, private keys, wallet material, or
execution instructions.

## Settlement Feedback

Settlement feedback is represented by settlement evidence packets, settlement
delay risk rows, and NAV settlement risk overlay rows. The feedback objects
diagnose paper exposure and settlement timing only.

| Field | Type | Precision / Shape | Contract |
| --- | --- | --- | --- |
| `condition_id` | string | canonical | Polymarket condition key for paper NAV exposure. |
| `market_slug` | string | canonical | Market slug used to join NAV exposure to settlement timing. |
| `token_count` | int | positive | Number of tokens in the paper exposure row. |
| `open_size` | Decimal | fixed-six nonnegative | Open paper exposure size; must be positive. |
| `cost_basis` | Decimal | fixed-six nonnegative | Cost basis; must not exceed open size. |
| `exit_value` | Decimal | fixed-six nonnegative | Exit value; must not exceed open size. |
| `share_of_exit_nav` | Decimal or null | fixed-six ratio | Share of latest exit NAV. |
| `overlay_status` | enum | `acceptable`, `watch`, `blocked` | Settlement NAV overlay status. |
| `settlement_timing_status` | enum or null | `acceptable`, `watch`, `blocked`, null | Null means settlement timing is missing and row must be blocked. |
| `timing_cost_per_share` | Decimal or null | fixed-six nonnegative | Required when settlement timing exists; null when missing. |
| `adjusted_net_probability_edge` | Decimal or null | fixed-six signed | Required when settlement timing exists; null when missing. |
| `reason_codes` | tuple[string] | canonical reason codes | Settlement timing or missing-settlement reasons. |
| `generated_at` | datetime | UTC | Settlement feedback report timestamp. |
| `first_marked_at`, `last_marked_at` | datetime or null | UTC | NAV mark timestamp window; both present or both null. |
| `nav_snapshot_count`, `settlement_row_count`, `exposure_row_count` | int | nonnegative | Source row counts. |
| `acceptable_count`, `watch_count`, `blocked_count`, `missing_settlement_count` | int | nonnegative | Overlay status rollups. |
| `acceptable_exit_value`, `watch_exit_value`, `blocked_exit_value`, `missing_settlement_exit_value`, `blocked_or_missing_exit_value` | Decimal | fixed-six nonnegative | Exit-value rollups. |
| `blocked_or_missing_exit_nav_share` | Decimal or null | fixed-six ratio | Blocked/missing share of exit NAV. |
| `max_blocked_settlement_exposure_share` | Decimal | fixed-six ratio | Configured settlement exposure budget. |
| `status` | enum | known settlement overlay report statuses | Derived report status. |
| `paper_only`, `report_only`, `readonly` | bool | all true | Required hard safety flags. |

Settlement feedback must not mutate outcomes, NAV, balances, exchange state, or
orders. It only records paper/report evidence for review.
