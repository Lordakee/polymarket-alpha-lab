# Research-to-paper scenario assembly (WP-05)

## Delivered boundary

`ProjectResearchSession.evaluate_paper_research(scenarios=..., **evaluation_options)`
connects the ORIGINAL complete-history evaluator and first-attempt selection to
the existing cost-aware event strategy and order-book fill simulator. It reads
only the same project-private native PostgreSQL instance. No network, model,
portfolio, allocation, new scoring system, migration or durable paper-trade
journal is created. The pure `ResearchPaperEvaluation` accepts detached typed
receipts; it does not authenticate their origin or establish database completeness.
Only the managed path invokes the existing complete-visible-execution-history gate.

**These are retrospective hypothetical scenarios, NOT forward paper-trade evidence,
a fee quote, realized P&L or strategy validation.** Supplied historical timestamps
are checked for consistency, not authenticated. Later market/outcome knowledge
could influence an operator's scenario choices. G5 remains open until prospective
inputs, costs, rejected attempts and simulated executions are retained in the
project database and linked to actual reviewed outcomes. No legacy JSONL or file
archive writer is invoked by this assembly.

Every original research decision remains in the output. Missing inputs, research
failures, later attempts and not-yet-visible records are not silently dropped.
The original evaluator decides which first attempt is eligible, and keeps its
probability diagnostics unchanged. Scenarios attach only to eligible `scored` or
`outcome_pending` records. No new pooled probability score is computed. A changed
outcome cannot change the scenario's selected side or cost decision.

## Explicit inputs and existing methods

An authorized application supplies a tuple of `ResearchPaperScenario` objects.
This is developer assembly, not a new stdin/file loader or a configured model.
Example names below are already reviewed in-memory values, not discovered files
or permission to read the user's database:

```python
from pathlib import Path
from polymarket_alpha_lab.project_postgres.server import ProjectPostgres
from polymarket_alpha_lab.research_paper_inputs import ResearchPaperBook, ResearchPaperScenario

# market: existing GammaMarketSnapshot with the historical open market payload.
# costs: existing PaperCostAwareEventCostAssumptions with ALL six explicit values.
# gates: existing PaperCostAwareEventStrategyConfig with explicit thresholds.
scenario = ResearchPaperScenario(
    record_id=original_record.record_id,
    record_sha256=original_record.content_sha256,
    decision_at=reviewed_decision_time,
    market=reviewed_market_snapshot,
    yes_book=ResearchPaperBook(yes_capture_time, original_yes_book_bytes),
    no_book=ResearchPaperBook(no_capture_time, original_no_book_bytes),
    requested_size=explicit_hypothetical_share_count,
    costs=explicit_cost_assumptions,
    gates=explicit_risk_thresholds,
    resolution_risk=explicit_resolution_risk,
    assumptions_id=reviewed_assumption_identifier,
    max_age_seconds=explicit_freshness_limit,
)
with ProjectPostgres(Path(actual_project_root)).session() as research:
    result = research.evaluate_paper_research(scenarios=(scenario,)).to_dict()
```

Evaluation options are the original evaluator's historical cutoff, record bound
and diagnostic settings; the new entry cannot disable execution completeness.
An incomplete visible claim blocks the whole managed evaluation before book
simulation. No fallback loader, age-based reclaim or model retry is permitted.
Original claim/result lookups are separate snapshots over immutable rows. Exact
record equality with the evaluated snapshot is required; missing or foreign
claims abort rather than being adopted. A scenario for an unknown/changed record,
duplicate scenario or extra/mismatched execution is invalid, not silently ignored.

The method returns a recomputable in-memory composition. It does not keep raw
scenario inputs after the caller discards them, and its metadata hashes are not
substitutes for durable source bytes. Do not redirect output to a new business
file journal. Future persistence must use the same project PostgreSQL with a
reviewed versioned provenance design; no such persistence is claimed here.

## Market, time, token and depth checks

Each scenario must reference its exact saved research record hash. Its decision
time is no earlier than the saved forecast and no later than the evaluation
cutoff; it must precede the original request cutoff and supported observation.
The ORIGINAL terminal contract and observation-time gates are reused. Historical
Gamma question/rules must exactly match the original task; changed rules and
path-dependent/unknown contracts are not silently approved.

Market `active`, `acceptingOrders` and `enableOrderBook` must be exact true and
`closed` exact false. Missing/ambiguous status is rejected. Explicit positive
`orderMinSize` and supported `orderPriceMinTickSize` are required. Supported tick
values here are 0.1, 0.01, 0.001 and 0.0001; other values stay unsupported. Requested
size must meet the market minimum. Exactly named Yes/No tokens and distinct
numeric string token IDs are required; reversed label order is supported but
alias/index fallback is not. Token labels remain supplied metadata, not on-chain
authentication.

Both raw books must identify the same condition and the correct outcome token.
They require a 13-digit millisecond timestamp and complete bid/ask arrays. The
normalizer orders valid levels, but invalid/zero/nonfinite/duplicate-price or
off-tick levels are rejected BEFORE normalization; they cannot be silently
converted to zero and discarded. Empty, crossed or locked books are rejected.
Market/books must be captured after the forecast and within the explicit 1..300
second age window at the decision time. Exchange timestamps must not be later
than capture or outside that age window. Clock consistency does not prove source
truth or practical fillability.

The existing fill simulator walks BOTH ask books for the EXACT requested share
count. A NO purchase is still a BUY of the NO token, never a short sale. Partial
walks retain filled/unfilled/requested quantities, but are not eligible in this
complete-size-only slice. There is no automatic size reduction or partial trade
credit. Observed depth is a snapshot assumption, not a queue-position, latency,
IOC or guaranteed-fill model.

## Cost/risk composition and conservative amounts

All six original cost assumptions are mandatory: quadratic taker fee coefficient,
additional slippage, funding, finalization, time and risk cost per share. None are
inferred from a historical default. Zero is a declared scenario assumption, not
proof that a cost is absent. Unknown cost inputs cannot be passed as zero by this
code. Each cost is bounded to [0,1] in this supported scenario slice. Requested
shares are positive and at most 1,000,000; bounded finite decimal inputs have at
most 18 significant digits and nine fractional places. Raw books are at most
128 KiB each and 200 levels per side; at most 100 scenarios and 8 MiB total raw
scenario input are accepted.

The existing strategy receives the original probability/confidence and actual
quoted spreads. Its executable ask input is the WORST consumed ask for that
requested size, not midpoint or displayed average. This is a conservative
full-size entry-price bound. Its original confidence, spread, resolution-risk,
depth and net-edge decisions remain visible.

The legacy fill's average price is display-rounded to 0.001. It is NEVER multiplied
by size to calculate monetary totals here. For the chosen candidate, the adapter
uses conservative arithmetic under a private Decimal context:

- Entry upper bound: requested shares times worst consumed ask.
- Fee upper bound: the maximum of the explicit quadratic `r*p*(1-p)` scenario
  over the consumed price range, rounded UP to six decimals per share, times
  requested shares. The maximum can lie near 0.5 INSIDE the range; fee at the
  worst ask alone is not necessarily an upper bound.
- Non-fee upper bound: the sum of the five explicit extra per-share costs, rounded
  UP to six decimals, times shares. Extra slippage is additional to book-walk
  depth, not a claim about observed latency.
- Expected net-edge lower bound: original side probability minus worst ask,
  fee upper bound and non-fee upper bound, rounded DOWN per share, times shares.

A legacy rounded cost decision can slightly overstate a threshold-edge case. If
this conservative lower bound misses the ORIGINAL minimum net-edge threshold,
the candidate is rejected as `conservative_cost_bound_rejected`; the original
strategy result is retained and no alternative side is reranked into acceptance.
Costs/thresholds and both decisions remain visible. These bounds are mathematical
bounds only WITHIN the stated scenario model, not bounds on real exchange bills.

Official fee documentation says fee parameters are market-specific. This adapter
never fetches a tariff or claims the assumed rate matches one. References checked
2026-09-15: https://docs.polymarket.com/trading/fees and
https://docs.python.org/3/library/decimal.html . Existing generic cost defaults
are left compatible but are not used in this entry.

## Output and acceptance

`history` is the original evaluator's output. `paper_attempts` has one row for
every original decision, original group/condition IDs, reason and source binding.
Eligible inputs expose the existing strategy gates, both hypothetical book walks
and conservative assumed totals. Known invalid market inputs remain explicit
rejections; structural binding/history corruption aborts. Output includes no raw
source bodies, prompts or model summaries; business IDs/hashes still are not
anonymous data.

The hard output boundaries are `retrospective_scenarios_only=true`,
`paper_trades_created=0`, `durable_paper_evidence_created=false`,
`realized_pnl=null`, `actual_billed_fees=null`, `tariff_verified=false` and
`strategy_validation_performed=false`. `paper_scenario_ready` means ONLY that
this explicit hypothetical input clears these existing component checks.

Unit tests and separately designed same-assistant adversarial tests are
`tests/test_research_paper.py` and `tests/test_research_paper_review.py`.
`tests/test_project_postgres_paper_native.py` uses an isolated fresh PostgreSQL,
synthetic BTC/ETH forecasts, missing/failed attempts, exact read replay/restart,
unchanged records and the original incomplete-history block. No user data,
credentials or real provider are used. The dedicated native CI runs on a separate
runner so it does not extend the existing long native job or relax its timeout.
Final revision/first failures/actual CI evidence belong to the implementation PR.

WP-05 remains PARTIAL; G5 requires durable prospective simulation inputs/execution,
reviewed real outcomes and cost-aware realized evaluation. Original statistical
promotion thresholds, D1-D3 and the existing WP-06 reliability issue are unchanged.
