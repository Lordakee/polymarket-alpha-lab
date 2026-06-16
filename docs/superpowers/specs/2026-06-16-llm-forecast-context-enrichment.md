# LLM Forecast Market Context Enrichment (Stage 10)

## Purpose

The LLM forecast (Stage 8) currently sends ONLY the market question to GLM-4-flash.
Adding market metadata (volume, liquidity, spread, end_time, rules_text) gives the
LLM crucial context for probability estimation. This is a focused prompt enhancement
— no new module, just a richer prompt in the existing transport + a context dict
passed through the dispatch.

No new boundary crossings. No new modules. Modify 3 files.

## Changes

### 1. llm_research_transport.py — accept optional market_context

```python
class ProbabilityModelTransport(Protocol):
    def estimate(
        self, *, market_question: str, outcome_names: tuple[str, ...],
        market_context: dict[str, str] | None = None,  # NEW
    ) -> ProbabilityModelResult: ...

class GLMChatTransport:
    def estimate(self, *, market_question, outcome_names, market_context=None):
        prompt = f"Question: {market_question}\nOutcomes: {', '.join(outcome_names)}"
        if market_context:
            for key, value in market_context.items():
                prompt += f"\n{key}: {value}"
        prompt += "\n\nEstimate P(YES). Return JSON: {\"p_yes\": <0-1>, \"confidence\": <0-1>}"
        # ... rest unchanged
```

### 2. strategy_cycle.py — build market_context from NormalizedMarket + dispatch

In the "llm" dispatch branch:
```python
market_context = {
    "volume_24h": str(nm.market.volume_24h) if nm.market.volume_24h else "unknown",
    "liquidity": str(nm.market.liquidity) if nm.market.liquidity else "unknown",
    "spread": str(snapshot_attempt.snapshot.spread) if attempt.status == "snapshot_ready" else "unknown",
    "end_time": nm.market.end_time.isoformat() if nm.market.end_time else "unknown",
    "rules": nm.rules_text[:500] if nm.rules_text else "unknown",
}
result = transport.estimate(market_question=nm.market.question, outcome_names=..., market_context=market_context)
```

### 3. Tests — update mock to verify context in prompt

## Non-goals

No web search (separate API, complexity). No multi-outcome. No new modules. No scope
test changes (transport has no strict scope). strategy_cycle scope unchanged (no new
imports).
