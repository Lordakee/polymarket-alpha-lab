# DB Row Decimal Canonicalization Inventory

Date: 2026-06-26

## Compatibility Policy

- New writes should prefer six-place canonical Decimal strings (`0.000001`) when the codec stores Decimal values as JSON strings.
- Existing rows must remain readable unless this document marks a codec as requiring an explicit hash migration.
- `from_db_row` may accept legacy payload strings only when the raw stored hash matches the raw stored `payload_json` exactly and recovered report validation proves the payload is semantically safe.
- Do not normalize raw stored `payload_json` before checking its persisted hash.
- The matrix below must contain one row for every tracked `src/polymarket_alpha_lab/*_db_row.py` file.
- Do not add any persistence backend while doing this work; DB persistence remains local Supabase/Postgres only.
- Phase boundary remains paper-only/report-only/readonly.
- Do not introduce live trading, auth, wallet/private-key reads, order placement, signing, submission, cancel, replace, or exchange mutation.

## Group Legend

- Group A: known non-six-place or mixed-scale payload strings with high snapshot/hash churn.
- Group B: low fixture churn but persisted hash risk for equivalent Decimal exponents.
- Group C: nested, payload-only, or latent Decimal branch requiring family-level compatibility review.
- Group F: already enforces fixed six-place Decimal width (`0.000001`) somewhere in the codec.
- Group N: no Decimal fields or Decimal handling in the codec.

## Codec Matrix

| Codec | Group | Current Decimal Format | Hash Field | Compatibility Choice | Required Tests |
|---|---|---|---|---|---|
| `action_gated_strategy_recommendation_queue_db_row.py` | A | `total_ready_notional` and nested payload Decimal values use `str(decimal)`; nested fixtures include four-place strings. | `report_sha256` | Defer until nested queue/bundle/candidate payload compatibility is reviewed. | nested legacy payload read, new top-level six-place write, candidate cost/share compatibility |
| `action_gated_strategy_recommendation_queue_decision_support_db_row.py` | F | fixed six-place `0.000001` formatting via `Decimal("0.000001")`. | `snapshot_sha256` | Already canonical at six places; keep strict payload/hash validation. | exact six-place snapshot write, stale hash rejection, malformed Decimal rejection |
| `action_gated_strategy_recommendation_queue_decision_support_trend_db_row.py` | F | fixed six-place `0.000001` trend/source-window formatting. | `trend_sha256`, `source_window_sha256`, `snapshot_sha256` | Already canonical at six places across multiple digest surfaces; preserve all digest checks. | trend/source-window/snapshot hash mismatch rejection, six-place trend write |
| `action_gated_strategy_recommendation_queue_history_db_row.py` | B | materialized totals currently use `str(decimal)` despite six-place fixtures. | `report_sha256` | First implementation slice for new-write six-place canonicalization. | equivalent Decimal new-write hash equality, self-hashed noncanonical payload rejection, legacy payload read guard |
| `autonomous_market_scorer_db_row.py` | F | fixed six-place `0.000001` formatting via `QUANTUM = Decimal("0.000001")`. | `report_sha256` | Already canonical at six places; keep strict score row Decimal checks. | six-place score/report write, stale hash rejection, noncanonical Decimal string rejection |
| `local_observability_trends_db_row.py` | C | no materialized Decimal fields; JSON Decimal branch uses `str(decimal)`. | `report_sha256` | Defer until nested trend payload sources are reviewed together. | nested trend old-read, new-write canonicalization for each nested trend type, raw Decimal payload rejection |
| `outcome_tracking_db_row.py` | A | payload Decimal branch uses `str(decimal)`; direct tests include non-six-place strings such as `"0.6000"` and `"1"`. | `report_sha256` | Defer until Group A compatibility-reader design lands. | old non-six-place row read, new six-place write, recovered canonical report check |
| `paper_autonomous_allocation_proposal_db_history_health_db_row.py` | F | fixed six-place `0.000001` optional Decimal formatting via `_DECIMAL_QUANTUM`. | `report_sha256` | Already canonical at six places; preserve nullable semantics. | explicit null versus missing key, six-place optional Decimal write, stale hash rejection |
| `paper_autonomous_allocation_proposal_db_history_metrics_evaluation_db_row.py` | C | no materialized Decimal fields; JSON Decimal branch uses `str(decimal)`. | `report_sha256`, `payload_sha256` helper in tests/logic | Defer until metrics diagnostics payload compatibility is reviewed. | diagnostics equivalent Decimal hash equality, raw Decimal payload rejection, raw hash guard |
| `paper_autonomous_allocation_proposal_db_row.py` | B | allocation and budget Decimal fields use `str(decimal)`. | `report_sha256` | Candidate after history/metrics codecs; inspect nested allocation rows before change. | requested/allocated budget new-write canonicalization, old raw hash read, nested allocation compatibility |
| `paper_autonomous_investment_ledger_db_history_health_db_row.py` | F | fixed six-place `0.000001` optional Decimal formatting via `_DECIMAL_QUANTUM`. | `report_sha256` | Already canonical at six places; preserve ledger health nullability. | six-place optional Decimal write, nullable missing-key rejection, stale hash rejection |
| `paper_autonomous_investment_ledger_db_row.py` | F | fixed six-place `0.000001` validation/formatting for `total_submitted_notional`. | `report_sha256` | Already canonical at six places; preserve ledger paper-only boundaries. | six-place submitted-notional write, noncanonical payload rejection, paper-only flag enforcement |
| `paper_autonomous_readiness_gate_db_row.py` | C | no materialized Decimal fields; defensive JSON Decimal branch uses `str(decimal)`. | `report_sha256` | No formatter change until a real Decimal field or payload source needs it. | latent branch remains no-float/no-raw-Decimal safe |
| `paper_autonomous_screening_decision_support_gate_db_row.py` | F | fixed six-place `0.000001` formatting for queue/score fields. | `report_sha256` | Already canonical at six places after screening gate hardening; preserve strict reason-count payload checks. | six-place score write, reason-count hard flags, self-hashed noncanonical rejection |
| `paper_autonomous_screening_decision_support_gate_transition_db_row.py` | N | no Decimal fields. | `report_sha256` | No Decimal migration action. | none / no Decimal surface |
| `paper_broker_db_row.py` | F | fixed six-place `0.000001` validation/formatting for notional fields; rejects seven-place bypasses. | `record_sha256` | Already canonical at six places; preserve over-precision rejection. | seven-place rejection remains, equivalent six-place new writes match, record hash mismatch protection |
| `paper_execution_reconciliation_db_row.py` | F | fixed six-place `0.000001` validation for PnL/notional fields; payload branch still emits `str(decimal)`. | `report_sha256` | Treat as partially canonical; audit before changing payload branch so invalid precision stays rejected. | seven-place rejection remains, execution notional new-write canonicalization, nullable Decimal guard |
| `paper_nav_snapshot_db_row.py` | A | NAV/cash Decimal fields use `str(decimal)`; direct tests assert non-six-place payload strings such as `"100.00"` and `"96.00"`. | `snapshot_sha256` | Defer until Group A compatibility-reader design lands. | old non-six-place row read, new six-place write, hash mismatch protection |
| `paper_order_lifecycle_db_row.py` | C | `source_execution_notional` and `fill_notional` use `str(decimal)`; pure paper/order-lifecycle reporting only with no live order placement/cancel/replace surface. | `report_sha256` | Defer formatter change until paper lifecycle reports define a compatibility reader; do not expand beyond report-only codec work. | paper-only/report-only/readonly enforcement, no live mutation surface, lifecycle notional old-read/new-write compatibility |
| `paper_probability_recommendation_queue_db_row.py` | C | no materialized Decimal fields; nested recommendation queue payloads use JSON Decimal branch with `str(decimal)`. | `report_sha256` | Defer until probability recommendation payload family is grouped. | queue row equivalent Decimal hash equality, legacy payload read, raw Decimal payload rejection |
| `paper_probability_selection_summary_db_row.py` | C | no materialized Decimal fields; nested selection rows use JSON Decimal branch with `str(decimal)`. | `report_sha256` | Defer with probability summary history. | selected row canonical write, old raw hash read, nested payload mismatch rejection |
| `paper_probability_selection_summary_history_db_row.py` | B | `latest_selected_share` and `average_selected_share` use `str(decimal)`; bounded by `0` and `1` but no fixed six-place width. | `report_sha256` | Candidate after action-gated history; probability shares need exact legacy read guard. | selected share canonical write, self-hashed noncanonical rejection, probability bound preservation |
| `paper_project_screening_rank_stability_db_row.py` | C | no materialized Decimal fields; nested screening scores/deltas use JSON Decimal branch with `str(decimal)`. | `report_sha256` | Defer until rank-stability payload family is reviewed. | score delta canonical write, legacy read, nested payload mismatch rejection |
| `paper_recommendation_consistency_db_row.py` | F | fixed six-place `0.000001` validation for `max_edge_spread` and `max_score_spread`; payload branch emits `str(decimal)`. | `report_sha256` | Treat as partially canonical; audit payload branch before changing digest output. | six-place spread validation, equivalent Decimal payload hash behavior, stale hash rejection |
| `paper_recommendation_cycle_snapshot_db_row.py` | C | no materialized Decimal fields; defensive JSON Decimal branch uses `str(decimal)`. | `snapshot_sha256` | No formatter change until a Decimal payload source is identified. | latent branch remains no-float/no-raw-Decimal safe, snapshot hash guard |
| `paper_recommendation_health_db_row.py` | F | fixed six-place `0.000001` validation for score/cost/share fields; payload branch emits `str(decimal)`. | `report_sha256` | Treat as partially canonical; preserve ratio bounds and health thresholds. | six-place health metric validation, equivalent Decimal payload hash behavior, threshold mismatch rejection |
| `paper_recommendation_quality_history_db_row.py` | C | no materialized Decimal fields; defensive JSON Decimal branch uses `str(decimal)`. | `report_sha256` | No formatter change until a Decimal payload source is identified. | latent branch remains no-float/no-raw-Decimal safe |
| `paper_recommendation_quality_summary_db_row.py` | C | no materialized Decimal fields; defensive JSON Decimal branch uses `str(decimal)`. | `report_sha256` | No formatter change until a Decimal payload source is identified. | latent branch remains no-float/no-raw-Decimal safe |
| `paper_recommendation_readiness_db_row.py` | F | fixed six-place `0.000001` validation for readiness Decimal fields; payload branch emits `str(decimal)`. | `report_sha256` | Treat as partially canonical; audit before changing digest output. | six-place readiness validation, equivalent Decimal payload hash behavior, stale hash rejection |
| `paper_recommendation_reason_trend_db_row.py` | N | no Decimal fields. | `report_sha256` | No Decimal migration action. | none / no Decimal surface |
| `paper_recommendation_reason_trend_health_db_row.py` | F | fixed six-place `0.000001` probability share validation with half-even quantization. | `report_sha256` | Already canonical for share validation; preserve rounding and nullable fields. | six-place share write, nullable share guard, stale hash rejection |
| `paper_recommendation_risk_budget_db_row.py` | F | fixed six-place `0.000001` notional and ratio validation via notional/ratio quantums. | `report_sha256` | Already canonical at six places; preserve budget utilization bounds. | six-place notional/share write, utilization bounds, stale hash rejection |
| `paper_research_packet_db_row.py` | C | no materialized Decimal fields; nested recommendation scores/edge/notionals use JSON Decimal branch with `str(decimal)`. | `report_sha256` | Defer until research packet family is grouped. | packet old-read, new-write canonical payload, nested row mismatch rejection |
| `paper_research_packet_operator_flow_db_row.py` | C | no materialized Decimal fields; included/skipped share payloads use JSON Decimal branch with `str(decimal)`. | `report_sha256` | Defer with research packet quality/operator-flow family. | share canonical write, old raw hash read, flow count/share consistency |
| `paper_research_packet_quality_db_row.py` | F | fixed six-place `0.000001` validation for included/skipped shares and observed/threshold values. | `report_sha256` | Already canonical at six places; preserve quality threshold semantics. | check observed/threshold canonical write, old raw hash read, quality flag mismatch rejection |
| `paper_trade_cost_audit_db_row.py` | A | mixed Decimal domains: size/notional/price/cost/edge fields use `str(decimal)`, while ratio quantum is six-place. | `report_sha256` | Defer broad formatter changes; first separate ratio fields from share/size fields. | size old-read, ratio six-place new-write, no rounding of cost/edge values |
| `paper_trade_journal_db_row.py` | A | trade size, price, and equity Decimal fields use `str(decimal)`; direct tests assert values such as `"0.56"`, `"0.60"`, and `"0.514"`. | `record_sha256` | Defer until Group A compatibility-reader design lands. | old non-six-place row read, new six-place write, raw record hash check |
| `strategy_candidate_research_queue_db_row.py` | B | notional/score Decimal fields use `str(decimal)`. | `report_sha256` | Candidate after action-gated history; watch nested candidate rows. | equivalent notional/score new-write hash equality, malformed string rejection, old raw hash read |
| `strategy_candidate_research_queue_history_db_row.py` | B | notional/score/delta Decimal fields use `str(decimal)`. | `report_sha256` | Candidate after strategy candidate queue. | equivalent Decimal new-write hash equality, self-hashed noncanonical payload rejection, history delta guard |
| `strategy_recommendation_rank_stability_db_row.py` | C | no materialized Decimal fields; nested scores/deltas/notionals use JSON Decimal branch with `str(decimal)`. | `report_sha256` | Defer until strategy rank-stability family is reviewed. | rank score canonical write, legacy read, nested payload mismatch rejection |
| `strategy_recommendation_reason_trend_db_row.py` | F | fixed six-place `0.000001` ratio share validation via `RATIO_QUANTUM`. | `report_sha256` | Already canonical for ratios; preserve optional share nullability. | six-place ratio write, nullable share guard, stale hash rejection |
| `strategy_risk_audit_db_row.py` | C | no materialized Decimal fields; nested gate observed/threshold values use JSON Decimal branch with `str(decimal)`. | `report_sha256` | Defer until risk audit gate value semantics are reviewed. | gate value canonical write, legacy read, threshold mismatch rejection |

## Inventory Check

Run this before committing any change to the inventory:

```bash
python3 - <<'PY'
from pathlib import Path
import subprocess

path = Path("docs/superpowers/plans/2026-06-26-db-row-decimal-canonicalization-inventory.md")
tracked = subprocess.check_output(
    ["git", "ls-files", "src/polymarket_alpha_lab/*_db_row.py"],
    text=True,
).splitlines()
matrix_rows = [
    line for line in path.read_text(encoding="utf-8").splitlines()
    if line.startswith("| `") and line.endswith("|")
]
if len(matrix_rows) != len(tracked):
    raise SystemExit(f"matrix row count {len(matrix_rows)} != tracked DB row count {len(tracked)}")
print(f"inventory rows: {len(matrix_rows)}; tracked DB row codecs: {len(tracked)}")
PY
```

Current expected output:

```text
inventory rows: 42; tracked DB row codecs: 42
```

## First Implementation Slice

Use `action_gated_strategy_recommendation_queue_history_db_row.py` first because:

- The Decimal fields are top-level materialized fields.
- The blast radius is smaller than Group A snapshot/journal/outcome codecs.
- The change can prove new-write six-place canonicalization plus a legacy payload read guard before touching high-churn Group A codecs.

Do not implement Group A until `docs/superpowers/plans/2026-06-26-db-row-decimal-compatibility-reader-design.md` exists and has been reviewed.
