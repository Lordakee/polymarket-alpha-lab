# Strategy Assessment Pre-Layer

This page documents the module-local assessment reducers that sit before any
live-execution surface. They are paper-only/report-only/readonly analysis over
caller-supplied typed in-memory inputs. They do not fetch market data, construct
clients, read accounts, touch wallets or private keys, place orders, or change
strategy behavior.

## Where This Fits

The repo already shows the surrounding workflow patterns in:

- [README.md](</home/ubuntu/polymarket-alpha-lab/README.md:344>) for
  `run_strategy_cycle(...)`, `PaperStrategyCycleReport`, and the paper-only
  strategy-cycle workflow.
- [README.md](</home/ubuntu/polymarket-alpha-lab/README.md:416>) for
  `run_strategy_loop(...)` and the optional strategy-audit preflight gate.
- [docs/research/validation-gates.md](</home/ubuntu/polymarket-alpha-lab/docs/research/validation-gates.md:9>)
  for the paper-only/report-only/read-only audit boundary.

This page narrows in on the new pre-layer modules themselves. The contract is
direct module import only. Package-root exports are not part of the surface.

## Module-Level API

Import these names from the module that defines them:

- `polymarket_alpha_lab.calibration_gate`
  - `PaperCalibrationGateConfig`
  - `PaperCalibrationGateReport`
  - `PaperCalibrationGateRow`
  - `build_paper_calibration_gate_report(...)`
- `polymarket_alpha_lab.cost_health_gate`
  - `PaperCostHealthGateConfig`
  - `PaperCostHealthGateReport`
  - `PaperCostHealthGateRow`
  - `PaperCostHealthSummaryRow`
  - `build_paper_cost_health_gate_report(...)`
- `polymarket_alpha_lab.liquidity_gate`
  - `PaperLiquidityGateConfig`
  - `PaperLiquidityGateReport`
  - `PaperLiquidityGateRow`
  - `build_paper_liquidity_gate_report(...)`
- `polymarket_alpha_lab.exposure_gate`
  - `PaperExposureGateConfig`
  - `PaperExposureGateReport`
  - `PaperExposureGateRow`
  - `build_paper_exposure_gate_report(...)`
- `polymarket_alpha_lab.market_context_freshness`
  - `PaperMarketContextFreshnessConfig`
  - `PaperMarketContextFreshnessReport`
  - `PaperMarketContextFreshnessRow`
  - `build_paper_market_context_freshness_report(...)`
- `polymarket_alpha_lab.settlement_freshness_gate`
  - `PaperSettlementFreshnessGateConfig`
  - `PaperSettlementFreshnessGateReport`
  - `PaperSettlementFreshnessGateRow`
  - `build_paper_settlement_freshness_gate_report(...)`
- `polymarket_alpha_lab.candidate_assessment`
  - `PaperCandidateAssessmentConfig`
  - `PaperCandidateAssessmentReport`
  - `PaperCandidateAssessmentRow`
  - `build_paper_candidate_assessment_report(...)`
- `polymarket_alpha_lab.cost_sensitivity`
  - `PaperCostSensitivityConfig`
  - `PaperCostSensitivityReport`
  - `PaperCostSensitivityRow`
  - `build_paper_cost_sensitivity_report(...)`
- `polymarket_alpha_lab.paper_trade_attribution`
  - `PaperTradeAttributionConfig`
  - `PaperTradeAttributionReport`
  - `PaperTradeAttributionRow`
  - `build_paper_trade_attribution_report(...)`
- `polymarket_alpha_lab.strategy_readiness_state`
  - `PaperStrategyReadinessSignal`
  - `PaperStrategyReadinessStateReport`
  - `build_paper_strategy_readiness_state_report(...)`
- `polymarket_alpha_lab.strategy_signal_adapter`
  - `build_paper_strategy_readiness_signals(...)`
  - `signals_from_calibration_gate_report(...)`
  - `signals_from_cost_health_gate_report(...)`
  - `signals_from_exposure_gate_report(...)`
  - `signals_from_liquidity_gate_report(...)`
  - `signals_from_market_context_freshness_report(...)`
  - `signals_from_nav_settlement_risk_overlay_report(...)`
  - `signals_from_settlement_freshness_gate_report(...)`

`signals_from_nav_settlement_risk_overlay_report(...)` adapts an existing
`PaperNavSettlementRiskOverlayReport` into the optional readiness signal source
`nav_settlement_risk_overlay`. This source is paper-only/report-only/readonly; it does not add live trading; does not add auth or wallet handling; does not add order submission, cancellation, or replacement; and does not add persistence, DB loaders, env reads, or CLI flags.

The shared pattern is the same in each module:

- accept caller-supplied typed in-memory inputs only
- preserve deterministic ordering for reproducible readiness and diagnostics
- hard-enforce `paper_only is True`, `report_only is True`, and where present
  `readonly is True`
- return frozen report or signal dataclasses, depending on the module
- expose the public surface through the module's own `__all__`

## Boundary

These modules are descriptive analysis only. They are not live execution, not
auth, not wallet handling, not private-key handling, not order placement, not
order cancellation, not ranking, not recommendation, and not financial advice.

They also do not add CLI commands, readers, writers, replay helpers, or
package-root re-exports. The intended import path is direct module import.
