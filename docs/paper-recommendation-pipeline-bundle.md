# Paper Recommendation Pipeline Bundle

This document defines the next pure paper recommendation pipeline and bundle
stage. It is a reducer contract for assembling already-built paper reports into
a complete cycle artifact. It does not introduce CLI wiring, file loading,
live market access, account access, wallet access, signing, order construction,
order placement, order cancellation, relayer calls, exchange mutation, network
mutation, or client mutation.

The stage consumes supplied in-memory inputs only: dataclass rows, report rows,
or report-shaped local objects passed by a caller that already owns data
collection and persistence. Every output remains `paper_only=True`,
`report_only=True`, and `readonly=True`. A recommendation, selected side,
queue row, gate pass, allocated paper notional, readiness state, bundle status,
or trend status is a research/report artifact only. It is not a live trading
instruction, approval, order intent, or exchange-ready payload.

## Purpose

The pipeline/bundle layer gives later wiring one deterministic way to assemble
the recommendation reducers:

```text
side-edge
-> queue
-> cost/liquidity/settlement/outcome/calibration/threshold gates
-> gate summary
-> allocation
-> research packet
-> manifest/consistency/health/readiness
-> pipeline report
-> cycle bundle
-> trend
```

The important boundary is that this layer reports how supplied paper artifacts
fit together. It does not fetch missing artifacts and does not decide whether a
real trade can be sent anywhere. If a required upstream report is missing, stale,
or blocked, the correct output is a blocked or watch paper report with reason
codes, not an attempt to recover by reading live systems.

## Stage Contract

| Stage | Supplied Inputs | Paper Outputs | Status Meaning |
| --- | --- | --- | --- |
| Side-edge | Supplied strategy-like side rows or canonical side-edge inputs with market slug, question, YES/NO side, forecast probability, executable side price, cost components, freshness fields, executable depth, settlement context, and source reason codes. | Canonical side-edge report with side probability, gross edge, total cost per share, net probability edge, recommendation score, action counts, sorted side rows, and hard paper/report/readonly flags. | `recommend` means the supplied paper row clears the side-edge scorer. `watch` means the paper row needs review or fresher context. `reject` means the supplied row is not eligible for the paper recommendation path. None of these statuses is an execution instruction. |
| Queue | Supplied canonical side-edge rows or a side-edge report, plus queue capacity and eligibility configuration. | Bounded paper recommendation queue with ranked rows, counts for research-review/watch/skip/excluded paths, recommended review next steps, and source reason codes. | Queue status is review status only. A queued row means "include in paper research workflow"; skipped or excluded rows remain report artifacts. |
| Cost gates | Supplied queued recommendation rows and explicit paper cost inputs such as taker fee, spread, slippage, shallow-depth penalty, funding/carrying cost, finalization/time/risk/capital-cost fields, or stress scenarios. | Cost gate rows and reports that adjust or test net edge against supplied per-share cost assumptions. | `pass` means modeled costs still leave the paper row within configured limits. `watch` means cost sensitivity needs review. `blocked` means supplied costs remove eligibility for this paper cycle. |
| Liquidity/depth gates | Supplied recommendation rows with requested paper shares, executable paper shares, maximum executable depth, side price, and spread cost. | Liquidity/depth gate report with fill ratio, liquidity cost per share, pass/watch/blocked counts, sorted gate rows, and reason codes. | `pass` means supplied executable depth and spread meet the paper gate. `watch` means depth or spread is marginal. `blocked` means supplied depth/action cannot support even paper allocation. |
| Settlement gates | Supplied recommendation rows with resolution timing, settlement context age, finalization buffer, and settlement-status evidence. | Settlement timing rows that apply supplied timing penalties and emit adjusted edge, status, counts, and timing reason codes. | `pass` means supplied timing evidence is acceptable. `watch` means timing/freshness is uncertain or near limits. `blocked` means unknown, overdue, excessive-horizon, or otherwise disqualifying supplied timing. |
| Outcome gates | Supplied recommendation rows with outcome-definition clarity, resolution-source evidence, ambiguity score, missing-source markers, and source reason codes. | Outcome uncertainty rows that apply ambiguity or missing-source penalties and summarize clear/watch/blocked outcome status. | `pass` means supplied outcome evidence is clear enough for paper review. `watch` means ambiguity needs analyst review. `blocked` means the supplied outcome definition is too ambiguous or unsupported. |
| Calibration gates | Supplied recommendation rows joined with supplied forecaster calibration metrics such as sample size, Brier score, calibration status, and forecast segment. | Calibration gate report with adjusted edge, pass/watch/blocked calibration rows, counts, and calibration reason codes. | `pass` means supplied calibration metrics clear the configured thresholds. `watch` means weak but not disqualifying calibration evidence. `blocked` means supplied calibration evidence is insufficient for this paper cycle. |
| Threshold gates | Supplied recommendation rows with net edge, score, executable paper shares, and total cost per share. | Threshold report applying explicit minimum edge, minimum score, minimum executable shares, and maximum cost constraints. | `pass` means configured paper thresholds are met. `watch` means marginal threshold pressure. `blocked` means one or more required paper thresholds fail. |
| Gate summary | Supplied gate rows from cost, liquidity/depth, settlement, outcome, calibration, threshold, and any later paper-only gates. | Gate summary report grouped by gate name, with pass/watch/blocked counts, total gate cost, primary status, sorted summary rows, and reason-code counts. | `primary_status` is the most severe supplied gate state: blocked dominates watch, watch dominates pass. It summarizes paper gate health only. |
| Allocation | Supplied eligible recommendation/readiness/queue rows, supplied paper budget limits, and grouping fields such as market, event, theme, and correlation group. | Paper allocation report with requested/allocated notional, paper shares, cap usage, zero/reduced allocation rows, counts, and allocation reason codes. | Allocated notional is paper sizing only. `pass` means allocation fits supplied paper caps; `watch` means reduced or constrained sizing; `blocked` means no paper allocation should be included in this cycle. |
| Research packet | Supplied recommendation, queue, readiness, or allocation rows with score, net edge, notional fields, and reason codes. | Ranked research packet with high/medium/low/skip priority, required checks, included/skipped counts, packet rank, and paper-only row flags. | Packet priority is analyst-review priority only. Required checks describe review work such as outcome definition, liquidity/depth, cost sensitivity, settlement timing, or calibration review. |
| Manifest | Supplied report-shaped artifacts and an explicit required-report-name list. | Manifest report with item rows, missing required reports, pass/watch/blocked counts, manifest status, and reason codes. | `pass` means all required supplied reports are present and passing. `watch` means at least one supplied report is watch. `blocked` means a required report is missing or any supplied report is blocked. |
| Consistency | Supplied facts for the same market side from multiple reducer reports, such as edge, score, action/status, costs, and reason codes. | Consistency report that compares source facts, flags missing/disagreeing sources, and blocks excessive edge or score spread. | `pass` means supplied facts agree within configured paper tolerances. `watch` means non-blocking disagreement. `blocked` means required sources are missing or disagreement exceeds paper tolerances. |
| Health | Supplied recommendation/action rows with net probability edge, total cost per share, score, action, and reason codes. | Health report with action counts, average edge, average cost, top score, reason-code counts, health status, and hard safety flags. | `pass` means the supplied cycle looks healthy under configured aggregate limits. `watch` means aggregate quality is marginal. `blocked` means aggregate paper health fails configured limits. |
| Readiness | Supplied gate inputs for each market side with gate status, adjusted edge, cost per share, and reason codes. | Readiness report with ready/watch/blocked rows, pass/watch/blocked gate counts per side, top adjusted edge, total gate cost, and reason codes. | `ready` means supplied gates clear the paper readiness contract. `watch` means analyst review or fresher context is needed. `blocked` means at least one required gate blocks the market side. |
| Pipeline report | Supplied `PaperRecommendationPipelineStage` values or stage-shaped objects for the completed reducers in this cycle. | Pipeline report with ordered stages, pass/watch/blocked counts, final status, input/output counts per stage, and hard safety flags. | `final_status` is a stage rollup: any blocked stage makes the pipeline blocked; otherwise any watch stage makes it watch; otherwise it passes. It records reducer completion and paper status only. |
| Cycle bundle | Supplied paper artifacts for one cycle, including pipeline, gate summary, allocation, packet, manifest, consistency, health, readiness, and related reports. | Cycle bundle report with artifact names, artifact count, ready/blocked artifact counts, final status, generated-at consistency checks, and the original supplied artifacts. | The bundle status is artifact health for the paper cycle. A blocked bundle means the paper report set is incomplete, stale, inconsistent, or blocked; it does not trigger recovery against live systems. |
| Trend | Supplied historical pipeline/bundle/reason/status reports from prior paper cycles. | Trend report summarizing status movement, reason-code movement, new or persistent blockers, and latest cycle health. | Trend status describes report quality over time. It is for observability and prioritization of future paper work, not for trading. |

## Status Vocabulary

Use `pass`, `watch`, and `blocked` for gate, manifest, consistency, health,
pipeline, bundle, and trend rollups. Use reducer-local row statuses only where
they already exist:

- Side-edge actions: `recommend`, `watch`, `reject`.
- Readiness rows: `ready`, `watch`, `blocked`.
- Research packet priorities: `high`, `medium`, `low`, `skip`.

When converting row-level status into pipeline stages, normalize to
`pass`/`watch`/`blocked` before building the pipeline report. A typical mapping
is:

- all eligible rows clear the reducer: `pass`
- any marginal, stale, reduced, or analyst-review row exists without a blocker:
  `watch`
- any required input is missing, unsafe, inconsistent, or blocked: `blocked`

The pipeline report should preserve stage order exactly as supplied. It should
not sort stages, infer missing stages, or call reducers. The cycle bundle should
preserve the supplied artifacts and fail closed when artifact flags,
generated-at values, or names are inconsistent.

## Cost Boundary

Costs that change paper recommendation quality should be modeled before paper
allocation when the caller supplies the inputs. In the next bundle order, taker
fees, spread costs, executable depth, shallow-depth penalties, slippage,
liquidity/depth effects, settlement timing penalties, finalization/time/risk
costs, funding/carrying costs, and capital-cost fields all feed the cost and
gate reports before the allocation reducer assigns paper notional.

Deposits, withdrawals, settlement/network costs, chain fees, bridge costs,
relayer fees, gas costs, wallet/account funding state, and exchange-specific
operational costs remain outside this pure reducer layer unless a caller has
already converted them into explicit paper input fields. This layer must never
query a wallet, exchange, relayer, chain, account, or client to discover those
values.

If a future caller supplies deposit, withdrawal, settlement, network, or gas
costs as plain paper inputs, they should enter through a cost gate as immutable
Decimal fields and remain report-only. Their presence still must not imply that
the reducer can execute, settle, or fund anything.

## Verification Checklist For Future Wiring

Before any future CLI, persistence, or orchestration wiring is accepted, verify
the following:

- The entry point consumes only caller-supplied local paper inputs or prior
  paper reports.
- No reducer imports or constructs HTTP clients, exchange clients, relayer
  clients, wallet adapters, signers, private-key readers, account readers, or
  order builders.
- No reducer reads live markets, balances, positions, allowances, order books,
  wallets, private keys, network state, or exchange state.
- No reducer writes exchange-facing artifacts, order tickets, order intents,
  signed payloads, client mutation requests, or recovery commands.
- Every generated report and row that crosses a stage boundary has
  `paper_only=True`, `report_only=True`, and `readonly=True`.
- Stage statuses are normalized to `pass`, `watch`, or `blocked` before they
  enter the pipeline report.
- Pipeline stage order is supplied explicitly and matches the bundle order:
  side-edge, queue, gates, gate summary, allocation, research packet,
  manifest/consistency/health/readiness, pipeline report, cycle bundle, trend.
- Cost gates run before allocation, and allocation consumes already-modeled
  net edge/cost/gate outputs rather than discovering costs itself.
- Manifest configuration includes every report that the cycle bundle considers
  required for readiness.
- Consistency checks compare market-side facts across supplied reports and
  block excessive disagreement before the cycle bundle is marked usable.
- Health and readiness reports are included as independent supplied artifacts;
  neither should override a blocked manifest or consistency report.
- The cycle bundle rejects missing hard flags, duplicate artifact names, and
  generated-at mismatches for artifacts that expose `generated_at`.
- Trend reducers consume completed paper reports only and do not scan
  repositories, logs, wallets, networks, exchanges, or live services by
  themselves.
- Tests cover the readonly boundary by checking imports and source text for
  forbidden live/auth/wallet/private-key/account/order/signing/client/network
  surfaces.
- Documentation and command help describe the output as paper-only,
  report-only, readonly research infrastructure.

## Future Wiring Notes

The next wiring layer should be a thin orchestrator over these pure reducers.
It may adapt local files or in-memory objects into supplied inputs only after a
separate plan approves that surface. Until then, this document should be read as
the contract for how reducers are composed, not as evidence that CLI commands,
cycle-bundle source, or trend source are fully wired.

When a stage cannot produce an artifact from supplied inputs, record a blocked
stage with a clear message and reason code in the paper report set. Do not
fallback to live fetching, account inspection, wallet inspection, order status
lookup, or network reads.
