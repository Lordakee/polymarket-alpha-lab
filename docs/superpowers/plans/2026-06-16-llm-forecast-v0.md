# LLM Forecast Provider v0 Plan (Stage 8)

**Goal:** Real P(YES) probability from LLM (Zhipu GLM-4-flash via stdlib urllib). Two-module split: transport (network) + forecast (pure leaf). Satisfies _CostAwareForecast Protocol.

## Pre-stage gate
- [ ] 0. Claude pre-stage (claude-opus-4-8 / effort max). Codex fallback after 2 failures.

## Tasks
- [ ] 1. `llm_research_transport.py` (NEW network layer): `ProbabilityModelTransport` Protocol + `GLMChatTransport` (urllib POST to Zhipu endpoint, Bearer auth, response_format json_object) + `ProbabilityModelResult`. RED+GREEN (fake transport; real GLM call optional in integration test).
- [ ] 2. `llm_forecast.py` (NEW pure leaf): `PaperLLMForecastConfig/Forecast/Log` + `build_paper_llm_forecast(market, *, result, config, generated_at)`. basis="llm_glm_v0". Parse-fail→low_confidence fallback. RED+GREEN.
- [ ] 3. `test_llm_forecast_scope.py` (NEW): leaf scope (stdlib+domain only; NO urllib/http; forbidden fragments).
- [ ] 4. strategy_cycle selector: add "llm" + `llm_transport_config` on PaperStrategyCycleConfig. Dispatch: call transport.estimate → build_paper_llm_forecast.
- [ ] 5. CLI strategy-cycle: --forecast-provider llm + --llm-api-token (caller-supplied).
- [ ] 6. Wiring: __init__ + test_init + README + scope.
- [ ] 7. Full verify.

## Post-stage gate
- [ ] 8. Claude post-stage (Phase 1; no float; parse-fail fallback; Protocol satisfaction).

## Commit (user-authorized)
- [ ] 9. `feat: add llm forecast provider v0`.
