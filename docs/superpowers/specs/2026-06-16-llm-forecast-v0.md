# LLM Forecast Provider v0 Design (Stage 8)

## Purpose

The book_imbalance forecast is a microstructure heuristic, not a real probability —
it structurally cannot pass `forecast_evidence.py`'s calibration gate
(mean_probability_loss / worst_bucket_error), so only ~2/20 markets reach
`paper_review_ready`. An LLM forecast produces an actual epistemic P(YES) estimate
that CAN be calibrated and judged — this is the "self-judge" primitive.

Two-module split (mirrors api.py + forecast_provider.py pattern):
- `llm_research_transport.py` — network layer (GLM REST via stdlib urllib, like api.py)
- `llm_forecast.py` — pure transform leaf (takes already-fetched LLM result → forecast)

No live orders/auth/wallets/credentials/exchange writes. LLM API call is read-only
outbound HTTPS for research (same class as api.py's Polymarket fetch).

## Module A — llm_research_transport.py (network layer)

```text
__all__ = ("ProbabilityModelTransport", "GLMChatTransport", "ProbabilityModelResult")

ProbabilityModelTransport (Protocol): estimate(market_question: str, outcome_names: tuple[str, ...]) -> ProbabilityModelResult

GLMChatTransport (frozen dataclass):
    endpoint_url: str = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    api_token: str              # caller-supplied (NEVER read from env/disk here)
    model: str = "glm-4-flash"  # non-reasoning; glm-4.5-air needs thinking:disabled
    temperature: Decimal = 0.3
    max_tokens: int = 256
    timeout_seconds: Decimal = 15.0
    # uses urllib.request.Request + urlopen (POST, Bearer header, JSON body)
    # response_format: {"type": "json_object"} forces structured output
    # prompt: "Estimate P(YES) for: {question}. Outcomes: {outcome_names}. Return JSON: {\"p_yes\": <0-1>, \"confidence\": <0-1>}"

ProbabilityModelResult (frozen dataclass):
    raw_p_yes: Decimal | None     # parsed from LLM JSON; None on parse fail
    raw_confidence: Decimal | None
    raw_content: str              # full LLM response text (audit)
    model_name: str
    finish_reason: str
    token_usage: int              # total tokens
    elapsed_seconds: Decimal
```

NO scope test (like api.py — network modules are unrestricted on urllib import).
Forbidden name fragments: NOT `client`/`fetch`/`sdk`/`credential` → use `Transport`/`estimate`.

## Module B — llm_forecast.py (pure transform leaf)

```text
__all__ = ("PaperLLMForecastConfig", "PaperLLMForecast", "PaperLLMForecastLog", "build_paper_llm_forecast")

BASIS_VALUES = ("llm_glm_v0",)

PaperLLMForecastConfig (frozen):
    config_version: str = "llm-forecast-v1"
    model_name: str = "glm-4-flash"
    low_confidence_value: Decimal = 0.5000
    high_confidence_value: Decimal = 0.7500
    max_question_chars: int = 500

PaperLLMForecast (frozen, paper_only=True, report_only=True):
    generated_at, config_version, market_slug, question
    fair_probability_yes: Decimal       # ∈ [0,1] quantized; = clamp(raw_p_yes, 0, 1) or low_confidence on parse fail
    confidence: Decimal                 # = raw_confidence or low_confidence
    basis: str = "llm_glm_v0"
    model_name: str
    raw_p_yes: Decimal | None           # audit (pre-clamp)
    reason_codes: tuple[str, ...]       # e.g. ("llm_probability_estimated",) or ("llm_parse_failed",)
    paper_only: bool = True
    report_only: bool = True

build_paper_llm_forecast(
    market: NormalizedMarket,
    *,
    result: ProbabilityModelResult,     # already-fetched LLM output (DI pattern)
    config: PaperLLMForecastConfig,
    generated_at: datetime,
) -> PaperLLMForecast
```

Satisfies `_CostAwareForecast` Protocol structurally (has fair_probability_yes + confidence).
Parse-fail/None → low_confidence_value + reason_code "llm_parse_failed". Clamp to [0,1].

Scope test: FORBIDS urllib/http/socket/os (network-free leaf, like book_imbalance).
ALLOWED: stdlib + domain only.

## strategy_cycle integration

`forecast_provider` selector tuple: `("naive", "book_imbalance", "llm")`.
When "llm": strategy_cycle calls GLMChatTransport.estimate(question, outcomes) →
ProbabilityModelResult → build_paper_llm_forecast(market, result=result, ...).
GLMChatTransport config on PaperStrategyCycleConfig (optional, like book_imbalance_config).

## Validation / scope / non-goals / risks

- paper_only/report_only with `is`; Decimal-only; no float; BASIS_VALUES enforced.
- Phase 1: read-only HTTPS research (same class as api.py). Token caller-supplied.
- Risk: hallucination → clamp + parse-fail fallback + calibration gate measures over time.
- Risk: glm-4.5-air empty content → default glm-4-flash (non-reasoning).
- Non-goals: no async (synchronous estimate); no caching (later stage); no ASXS fallback endpoint (v0 Zhipu only).
