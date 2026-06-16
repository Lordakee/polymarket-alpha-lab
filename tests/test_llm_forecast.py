import json
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import patch

import pytest

from polymarket_alpha_lab.domain import (
    MarketSnapshot,
    NormalizedMarket,
    OutcomeToken,
)
from polymarket_alpha_lab.llm_forecast import (
    BASIS_VALUES,
    PaperLLMForecast,
    PaperLLMForecastConfig,
    PaperLLMForecastLog,
    _ProbabilityModelResult,
    build_paper_llm_forecast,
)
from polymarket_alpha_lab.llm_research_transport import (
    GLMChatTransport,
    ProbabilityModelResult,
)


GENERATED_AT = datetime(2026, 6, 16, 13, 0, tzinfo=UTC)


# ---------------------------------------------------------------------------
# Fakes / fixtures
# ---------------------------------------------------------------------------


class FakeResult:
    """A minimal object satisfying the leaf-local _ProbabilityModelResult
    Protocol (duck-typed, NOT a transport import). Proves I1: the leaf accepts
    any structurally-compatible result without importing the transport."""

    def __init__(
        self,
        *,
        raw_p_yes=None,
        raw_confidence=None,
        raw_content="",
        model_name="glm-4-flash",
        finish_reason="stop",
        reasoning="",
    ):
        self.raw_p_yes = raw_p_yes
        self.raw_confidence = raw_confidence
        self.raw_content = raw_content
        self.model_name = model_name
        self.finish_reason = finish_reason
        self.reasoning = reasoning


def forecast_config(**overrides):
    values = {}
    values.update(overrides)
    return PaperLLMForecastConfig(**values)


def normalized_market(**overrides):
    values = {
        "condition_id": "0xcondition",
        "market_slug": "fed-cut-june-2026",
        "question": "Will the Fed cut rates by June 2026?",
        "active": True,
        "closed": False,
        "accepting_orders": True,
        "end_time": None,
        "volume_24h": Decimal("1000.0000"),
        "liquidity": Decimal("500.0000"),
        "captured_at": GENERATED_AT,
        "tokens": (
            OutcomeToken(
                condition_id="0xcondition",
                token_id="yes-token",
                outcome_index=0,
                outcome_name="Yes",
            ),
            OutcomeToken(
                condition_id="0xcondition",
                token_id="no-token",
                outcome_index=1,
                outcome_name="No",
            ),
        ),
        "rules_text": "Market resolves according to the public source.",
        "resolution_source": "public-source",
    }
    values.update(overrides)
    return NormalizedMarket(
        market=MarketSnapshot(
            condition_id=values["condition_id"],
            market_slug=values["market_slug"],
            question=values["question"],
            active=values["active"],
            closed=values["closed"],
            accepting_orders=values["accepting_orders"],
            end_time=values["end_time"],
            volume_24h=values["volume_24h"],
            liquidity=values["liquidity"],
            captured_at=values["captured_at"],
        ),
        tokens=values["tokens"],
        rules_text=values["rules_text"],
        resolution_source=values["resolution_source"],
    )


def build(market=None, result=None, config=None, generated_at=GENERATED_AT):
    return build_paper_llm_forecast(
        market or normalized_market(),
        result=result or FakeResult(
            raw_p_yes=Decimal("0.65"),
            raw_confidence=Decimal("0.6"),
            raw_content='{"p_yes": 0.65, "confidence": 0.6}',
        ),
        config=config or forecast_config(),
        generated_at=generated_at,
    )


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_llm_happy_path_carries_raw_p_yes_as_fair_probability():
    result = FakeResult(
        raw_p_yes=Decimal("0.65"),
        raw_confidence=Decimal("0.6"),
        raw_content='{"p_yes": 0.65, "confidence": 0.6}',
    )

    forecast = build(result=result)

    assert isinstance(forecast, PaperLLMForecast)
    assert forecast.paper_only is True
    assert forecast.report_only is True
    assert forecast.basis == "llm_glm_v0"
    assert forecast.fair_probability_yes == Decimal("0.650000")
    assert forecast.confidence == Decimal("0.600000")
    assert forecast.raw_p_yes == Decimal("0.65")
    assert forecast.model_name == "glm-4-flash"
    assert forecast.market_slug == "fed-cut-june-2026"
    assert forecast.question == "Will the Fed cut rates by June 2026?"
    assert forecast.config_version == "llm-forecast-v1"
    assert forecast.reason_codes == ("llm_probability_estimated",)


def test_llm_basis_values_pin_llm_glm_v0():
    assert BASIS_VALUES == ("llm_glm_v0",)
    forecast = build()
    assert forecast.basis in BASIS_VALUES


# ---------------------------------------------------------------------------
# Reasoning forwarding (chain-of-thought audit trail)
# ---------------------------------------------------------------------------


def test_llm_result_with_reasoning_produces_forecast_with_that_reasoning():
    # A result carrying chain-of-thought reasoning forwards it verbatim onto
    # the forecast (audit trail + calibration evidence).
    result = FakeResult(
        raw_p_yes=Decimal("0.65"),
        raw_confidence=Decimal("0.6"),
        raw_content='{"reasoning": "Base rate favors NO; volume is high.", '
        '"p_yes": 0.65, "confidence": 0.6}',
        reasoning="Base rate favors NO; volume is high.",
    )

    forecast = build(result=result)

    assert forecast.reasoning == "Base rate favors NO; volume is high."
    assert isinstance(forecast.reasoning, str)


def test_llm_result_without_reasoning_defaults_to_empty_string():
    # Backward compat: a result that omits reasoning (pre-existing callers)
    # yields an empty-string forecast reasoning, never None.
    result = FakeResult(
        raw_p_yes=Decimal("0.65"),
        raw_confidence=Decimal("0.6"),
        raw_content='{"p_yes": 0.65, "confidence": 0.6}',
    )

    forecast = build(result=result)

    assert forecast.reasoning == ""
    assert isinstance(forecast.reasoning, str)


def test_llm_parse_fail_result_carries_empty_reasoning():
    # A parse-failed result has no reasoning; the forecast keeps "" so the
    # audit trail is well-formed even when the LLM produced nothing usable.
    result = FakeResult(
        raw_p_yes=None,
        raw_confidence=None,
        raw_content="not json",
    )

    forecast = build(result=result)

    assert forecast.reasoning == ""
    assert forecast.reason_codes == ("llm_parse_failed",)


# ---------------------------------------------------------------------------
# I2: parse-fail fallback + is-not-None guards
# ---------------------------------------------------------------------------


def test_llm_parse_fail_falls_back_to_low_confidence_with_reason_code():
    result = FakeResult(
        raw_p_yes=None,
        raw_confidence=None,
        raw_content="not json",
    )

    forecast = build(result=result, config=forecast_config())

    assert forecast.fair_probability_yes == Decimal("0.500000")
    assert forecast.confidence == Decimal("0.500000")
    assert forecast.raw_p_yes is None
    assert forecast.reason_codes == ("llm_parse_failed",)


def test_llm_zero_raw_p_yes_is_not_treated_as_missing():
    # I2 (CRITICAL): Decimal("0") is falsy but valid. Must NOT fall back.
    result = FakeResult(
        raw_p_yes=Decimal("0"),
        raw_confidence=Decimal("0"),
        raw_content='{"p_yes": 0, "confidence": 0}',
    )

    forecast = build(result=result)

    assert forecast.fair_probability_yes == Decimal("0.000000")
    assert forecast.confidence == Decimal("0.000000")
    assert forecast.reason_codes == ("llm_probability_estimated",)


def test_llm_confidence_none_falls_back_to_low_confidence_independently():
    # raw_p_yes present, raw_confidence None: p_estimated reason, low conf.
    result = FakeResult(
        raw_p_yes=Decimal("0.7"),
        raw_confidence=None,
        raw_content='{"p_yes": 0.7}',
    )

    forecast = build(result=result)

    assert forecast.fair_probability_yes == Decimal("0.700000")
    assert forecast.confidence == Decimal("0.500000")
    assert forecast.reason_codes == ("llm_probability_estimated",)


def test_llm_clamps_raw_p_yes_above_one_to_one():
    result = FakeResult(raw_p_yes=Decimal("1.5"), raw_confidence=Decimal("0.9"))
    forecast = build(result=result)
    assert forecast.fair_probability_yes == Decimal("1.000000")


def test_llm_clamps_raw_p_yes_below_zero_to_zero():
    result = FakeResult(raw_p_yes=Decimal("-0.25"), raw_confidence=Decimal("0.9"))
    forecast = build(result=result)
    assert forecast.fair_probability_yes == Decimal("0.000000")


def test_llm_clamps_confidence_above_one_and_below_zero():
    high = build(
        result=FakeResult(raw_p_yes=Decimal("0.5"), raw_confidence=Decimal("2.0")),
    )
    assert high.confidence == Decimal("1.000000")

    low = build(
        result=FakeResult(raw_p_yes=Decimal("0.5"), raw_confidence=Decimal("-1.0")),
    )
    assert low.confidence == Decimal("0.000000")


def test_llm_low_confidence_value_override_changes_fallback():
    config = forecast_config(low_confidence_value=Decimal("0.4000"))
    result = FakeResult(raw_p_yes=None, raw_confidence=None)
    forecast = build(result=result, config=config)
    assert forecast.fair_probability_yes == Decimal("0.400000")
    assert forecast.confidence == Decimal("0.400000")


# ---------------------------------------------------------------------------
# I1: leaf-local Protocol guard
# ---------------------------------------------------------------------------


def test_llm_transport_concrete_result_satisfies_leaf_protocol():
    # I1: the transport's ProbabilityModelResult is structurally accepted by the
    # leaf's leaf-local Protocol (no transport import edge in the leaf).
    transport_result = ProbabilityModelResult(
        raw_p_yes=Decimal("0.35"),
        raw_confidence=Decimal("0.6"),
        raw_content='{"reasoning": "Historical base rate ~0.35.", '
        '"p_yes": 0.35, "confidence": 0.6}',
        model_name="glm-4-flash",
        finish_reason="stop",
        token_usage=125,
        elapsed_seconds=Decimal("1.0"),
        reasoning="Historical base rate ~0.35.",
    )
    assert isinstance(transport_result, _ProbabilityModelResult)

    forecast = build(result=transport_result)
    assert forecast.fair_probability_yes == Decimal("0.350000")
    assert forecast.confidence == Decimal("0.600000")
    assert forecast.reasoning == "Historical base rate ~0.35."
    assert forecast.reason_codes == ("llm_probability_estimated",)


def test_llm_build_rejects_result_that_does_not_satisfy_protocol():
    with pytest.raises(ValueError, match="result must be a _ProbabilityModelResult"):
        build_paper_llm_forecast(
            normalized_market(),
            result="not-a-result",  # type: ignore[arg-type]
            config=forecast_config(),
            generated_at=GENERATED_AT,
        )


def test_llm_build_rejects_invalid_inputs():
    market = normalized_market()
    result = FakeResult(raw_p_yes=Decimal("0.5"))
    config = forecast_config()
    with pytest.raises(ValueError, match="market must be a NormalizedMarket"):
        build_paper_llm_forecast(
            "not-a-market",  # type: ignore[arg-type]
            result=result,
            config=config,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config must be a PaperLLMForecastConfig"):
        build_paper_llm_forecast(
            market,
            result=result,
            config="not-a-config",  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        build_paper_llm_forecast(
            market,
            result=result,
            config=config,
            generated_at="not-a-datetime",  # type: ignore[arg-type]
        )


# ---------------------------------------------------------------------------
# Config validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"config_version": ""}, "config_version must be a canonical"),
        ({"config_version": " x "}, "config_version must be a canonical"),
        ({"model_name": ""}, "model_name must be a canonical"),
        ({"low_confidence_value": Decimal("-0.1")}, "low_confidence_value must be"),
        ({"low_confidence_value": Decimal("1.1")}, "low_confidence_value must be"),
        ({"high_confidence_value": Decimal("2")}, "high_confidence_value must be"),
        ({"max_question_chars": 0}, "max_question_chars must be positive"),
        ({"max_question_chars": True}, "max_question_chars must be an int"),
    ),
)
def test_llm_config_rejects_invalid_inputs(overrides, message):
    with pytest.raises(ValueError, match=message):
        forecast_config(**overrides)


def test_llm_forecast_rejects_invalid_basis():
    forecast = build()
    with pytest.raises(ValueError, match="basis must be a known"):
        PaperLLMForecast(
            generated_at=forecast.generated_at,
            config_version=forecast.config_version,
            market_slug=forecast.market_slug,
            question=forecast.question,
            fair_probability_yes=forecast.fair_probability_yes,
            confidence=forecast.confidence,
            basis="not-a-real-basis",
            model_name=forecast.model_name,
            raw_p_yes=forecast.raw_p_yes,
            reason_codes=forecast.reason_codes,
        )


# ---------------------------------------------------------------------------
# Immutability
# ---------------------------------------------------------------------------


def test_llm_forecast_is_frozen():
    forecast = build()
    with pytest.raises(FrozenInstanceError):
        forecast.fair_probability_yes = Decimal("0.9999")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        forecast.paper_only = False  # type: ignore[misc]


def test_llm_forecast_rejects_non_paper_flags():
    base = build()
    fields = {
        "generated_at": base.generated_at,
        "config_version": base.config_version,
        "market_slug": base.market_slug,
        "question": base.question,
        "fair_probability_yes": base.fair_probability_yes,
        "confidence": base.confidence,
        "basis": base.basis,
        "model_name": base.model_name,
        "raw_p_yes": base.raw_p_yes,
        "reason_codes": base.reason_codes,
    }
    with pytest.raises(ValueError, match="paper_only must be True"):
        PaperLLMForecast(**{**fields, "paper_only": False})
    with pytest.raises(ValueError, match="report_only must be True"):
        PaperLLMForecast(**{**fields, "report_only": False})


# ---------------------------------------------------------------------------
# JSONL round-trip
# ---------------------------------------------------------------------------


def test_llm_log_append_writes_valid_jsonl_round_trip(tmp_path):
    log_path = tmp_path / "llm-forecasts.jsonl"
    log = PaperLLMForecastLog(log_path)

    forecast = build(
        result=FakeResult(
            raw_p_yes=Decimal("0.65"),
            raw_confidence=Decimal("0.6"),
            raw_content='{"p_yes": 0.65, "confidence": 0.6}',
        ),
    )
    log.append(forecast)

    assert log_path.exists()
    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    row = json.loads(lines[0])
    # Frozen Decimals serialize as strings; float must never appear.
    assert row["fair_probability_yes"] == "0.650000"
    assert row["confidence"] == "0.600000"
    assert row["basis"] == "llm_glm_v0"
    assert row["reason_codes"] == ["llm_probability_estimated"]
    assert row["paper_only"] is True
    assert row["report_only"] is True
    assert "api_token" not in row
    # Re-constructing from the row must succeed (round-trip safety).
    rebuilt = PaperLLMForecast(
        generated_at=datetime.fromisoformat(row["generated_at"]),
        config_version=row["config_version"],
        market_slug=row["market_slug"],
        question=row["question"],
        fair_probability_yes=Decimal(row["fair_probability_yes"]),
        confidence=Decimal(row["confidence"]),
        basis=row["basis"],
        model_name=row["model_name"],
        raw_p_yes=Decimal(row["raw_p_yes"]) if row["raw_p_yes"] else None,
        reason_codes=tuple(row["reason_codes"]),
    )
    assert rebuilt.fair_probability_yes == forecast.fair_probability_yes


def test_llm_log_rejects_non_forecast(tmp_path):
    log = PaperLLMForecastLog(tmp_path / "llm-forecasts.jsonl")
    with pytest.raises(ValueError, match="forecast must be a PaperLLMForecast"):
        log.append("not-a-forecast")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# I3 + M2: transport-level guarantees (mocked urlopen)
# ---------------------------------------------------------------------------


def _zhipu_envelope(content: str, *, total_tokens: int = 125) -> dict:
    return {
        "id": "chatcmpl-test",
        "model": "glm-4-flash",
        "choices": [
            {
                "finish_reason": "stop",
                "message": {"role": "assistant", "content": content},
            }
        ],
        "usage": {"completion_tokens": 50, "prompt_tokens": 75, "total_tokens": total_tokens},
    }


class _FakeResponse:
    def __init__(self, payload: bytes):
        self._payload = payload

    def read(self) -> bytes:
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_transport_estimate_parses_decimals_never_float():
    # I3 (CRITICAL): p_yes/confidence parsed as Decimal, never float.
    transport = GLMChatTransport(api_token="secret-token")
    envelope = _zhipu_envelope('{"p_yes": 0.35, "confidence": 0.6}')

    with patch(
        "polymarket_alpha_lab.llm_research_transport.urlopen",
        return_value=_FakeResponse(json.dumps(envelope).encode("utf-8")),
    ):
        result = transport.estimate(
            market_question="Will X happen?",
            outcome_names=("Yes", "No"),
        )

    assert isinstance(result, ProbabilityModelResult)
    assert result.raw_p_yes == Decimal("0.35")
    assert result.raw_confidence == Decimal("0.6")
    assert isinstance(result.raw_p_yes, Decimal)
    assert isinstance(result.raw_confidence, Decimal)
    assert result.finish_reason == "stop"
    assert result.token_usage == 125
    assert result.model_name == "glm-4-flash"
    assert isinstance(result.elapsed_seconds, Decimal)


def test_transport_estimate_parse_fail_yields_none_decimals():
    transport = GLMChatTransport(api_token="secret-token")
    envelope = _zhipu_envelope("this is not json at all")

    with patch(
        "polymarket_alpha_lab.llm_research_transport.urlopen",
        return_value=_FakeResponse(json.dumps(envelope).encode("utf-8")),
    ):
        result = transport.estimate(
            market_question="Will X happen?",
            outcome_names=("Yes", "No"),
        )

    assert result.raw_p_yes is None
    assert result.raw_confidence is None
    assert result.raw_content == "this is not json at all"
    assert result.reasoning == ""
    assert result.token_usage == 125


def test_transport_estimate_parses_reasoning_from_content():
    # Chain-of-thought reasoning appears in the LLM JSON content alongside
    # p_yes/confidence and is parsed verbatim onto ProbabilityModelResult.
    transport = GLMChatTransport(api_token="secret-token")
    envelope = _zhipu_envelope(
        '{"reasoning": "Base rate 0.3; high volume supports current price.", '
        '"p_yes": 0.4, "confidence": 0.7}'
    )

    with patch(
        "polymarket_alpha_lab.llm_research_transport.urlopen",
        return_value=_FakeResponse(json.dumps(envelope).encode("utf-8")),
    ):
        result = transport.estimate(
            market_question="Will X happen?",
            outcome_names=("Yes", "No"),
        )

    assert result.reasoning == "Base rate 0.3; high volume supports current price."
    assert result.raw_p_yes == Decimal("0.4")
    assert result.raw_confidence == Decimal("0.7")


def test_transport_estimate_content_without_reasoning_yields_empty_string():
    # Backward compat: older LLM content that omits the reasoning key yields
    # reasoning="" (never None) so downstream code can rely on a str type.
    transport = GLMChatTransport(api_token="secret-token")
    envelope = _zhipu_envelope('{"p_yes": 0.5, "confidence": 0.5}')

    with patch(
        "polymarket_alpha_lab.llm_research_transport.urlopen",
        return_value=_FakeResponse(json.dumps(envelope).encode("utf-8")),
    ):
        result = transport.estimate(
            market_question="Will X happen?",
            outcome_names=("Yes", "No"),
        )

    assert result.reasoning == ""
    assert isinstance(result.reasoning, str)
    assert result.raw_p_yes == Decimal("0.5")


def test_transport_estimate_non_string_reasoning_yields_empty_string():
    # Defensive: a malformed reasoning value (number/list) is coerced to ""
    # rather than propagated as a non-string type.
    transport = GLMChatTransport(api_token="secret-token")
    envelope = _zhipu_envelope(
        '{"reasoning": 12345, "p_yes": 0.5, "confidence": 0.5}'
    )

    with patch(
        "polymarket_alpha_lab.llm_research_transport.urlopen",
        return_value=_FakeResponse(json.dumps(envelope).encode("utf-8")),
    ):
        result = transport.estimate(
            market_question="Will X happen?",
            outcome_names=("Yes", "No"),
        )

    assert result.reasoning == ""
    assert isinstance(result.reasoning, str)


def test_transport_network_failure_yields_empty_result_not_exception():
    transport = GLMChatTransport(api_token="secret-token")

    with patch(
        "polymarket_alpha_lab.llm_research_transport.urlopen",
        side_effect=OSError("connection refused"),
    ):
        result = transport.estimate(
            market_question="Will X happen?",
            outcome_names=("Yes", "No"),
        )

    assert result.raw_p_yes is None
    assert result.raw_confidence is None
    assert result.raw_content == ""
    assert result.token_usage == 0


def test_transport_result_carries_no_api_token_field():
    # M2: api_token stays on GLMChatTransport only; ProbabilityModelResult has
    # no credential field and no api_token attribute anywhere.
    result = ProbabilityModelResult(
        raw_p_yes=Decimal("0.35"),
        raw_confidence=Decimal("0.6"),
        raw_content="{}",
        model_name="glm-4-flash",
        finish_reason="stop",
        token_usage=125,
        elapsed_seconds=Decimal("1.0"),
    )
    assert not hasattr(result, "api_token")
    serialized = json.dumps(result.__dict__, default=str)
    assert "secret" not in serialized
    assert "api_token" not in serialized


def test_transport_defaults_use_string_decimals():
    # M1: all Decimal defaults are string-constructed.
    transport = GLMChatTransport(api_token="x")
    assert transport.temperature == Decimal("0.3")
    assert isinstance(transport.temperature, Decimal)
    assert transport.timeout_seconds == Decimal("15.0")
    assert isinstance(transport.timeout_seconds, Decimal)


def test_transport_rejects_blank_api_token():
    with pytest.raises(ValueError, match="api_token must be a nonblank string"):
        GLMChatTransport(api_token="")
    with pytest.raises(ValueError, match="api_token must be a nonblank string"):
        GLMChatTransport(api_token="   ")


# ---------------------------------------------------------------------------
# Stage 10: market_context prompt enrichment
# ---------------------------------------------------------------------------


def test_transport_estimate_none_market_context_omits_context_lines_and_includes_system_prompt():
    # Backward-compat: market_context=None must still produce a working estimate.
    # The user prompt carries Question/Outcomes + the Estimate instruction with
    # NO market-context lines, and a superforecaster system prompt is attached.
    captured: dict = {}

    def _capture(request, timeout):  # noqa: ARG001
        payload = json.loads(request.data.decode("utf-8"))
        captured["messages"] = payload["messages"]
        return _FakeResponse(
            json.dumps(_zhipu_envelope('{"p_yes": 0.5, "confidence": 0.5}')).encode(
                "utf-8"
            )
        )

    transport = GLMChatTransport(api_token="secret-token")
    with patch("polymarket_alpha_lab.llm_research_transport.urlopen", side_effect=_capture):
        transport.estimate(
            market_question="Will X happen?",
            outcome_names=("Yes", "No"),
        )
    messages = captured["messages"]
    # A superforecaster system prompt leads the messages list.
    assert messages[0]["role"] == "system"
    assert "superforecaster" in messages[0]["content"]
    assert "Base rate" in messages[0]["content"]
    # The user prompt has the new structured format and no context lines.
    user_prompt = messages[-1]["content"]
    assert user_prompt == (
        "Question: Will X happen?\n"
        "Outcomes: Yes, No\n"
        "\n"
        "Think step by step: first write a brief explanation of your reasoning "
        "(base rate, evidence, time horizon, market efficiency, rules clarity), "
        "then commit to your probability. Return JSON: "
        '{"reasoning": "<brief explanation>", '
        '"p_yes": <number 0-1>, "confidence": <number 0-1>}'
    )
    assert "volume_24h" not in user_prompt


def test_transport_estimate_appends_market_context_to_prompt_before_instruction():
    # Stage 10: each key/value pair appears in the USER prompt, positioned
    # BEFORE the "Estimate P(YES)" instruction. Decimal values are
    # str()-coerced upstream.
    captured: dict = {}

    def _capture(request, timeout):  # noqa: ARG001
        payload = json.loads(request.data.decode("utf-8"))
        captured["messages"] = payload["messages"]
        return _FakeResponse(
            json.dumps(_zhipu_envelope('{"p_yes": 0.5, "confidence": 0.5}')).encode(
                "utf-8"
            )
        )

    transport = GLMChatTransport(api_token="secret-token")
    market_context = {
        "volume_24h": "1000",
        "liquidity": "500",
        "end_time": "2026-12-31T00:00:00+00:00",
        "rules": "Resolves per public source.",
    }
    with patch("polymarket_alpha_lab.llm_research_transport.urlopen", side_effect=_capture):
        transport.estimate(
            market_question="Will X happen?",
            outcome_names=("Yes", "No"),
            market_context=market_context,
        )

    # The user message is the last message in the list.
    user_prompt = captured["messages"][-1]["content"]
    # Question/outcomes header still leads the user prompt.
    assert user_prompt.startswith("Question: Will X happen?\nOutcomes: Yes, No")
    # Every context pair is present.
    for key, value in market_context.items():
        assert f"{key}: {value}" in user_prompt, key
    # All context lines precede the "Think step by step" instruction block.
    estimate_idx = user_prompt.index("Think step by step")
    for key, value in market_context.items():
        assert user_prompt.index(f"{key}: {value}") < estimate_idx, key


def test_transport_estimate_empty_market_context_omits_context_lines():
    # Empty dict is falsy -> behaves like None (no context lines appended).
    captured: dict = {}

    def _capture(request, timeout):  # noqa: ARG001
        payload = json.loads(request.data.decode("utf-8"))
        captured["messages"] = payload["messages"]
        return _FakeResponse(
            json.dumps(_zhipu_envelope('{"p_yes": 0.5, "confidence": 0.5}')).encode(
                "utf-8"
            )
        )

    transport = GLMChatTransport(api_token="secret-token")
    with patch("polymarket_alpha_lab.llm_research_transport.urlopen", side_effect=_capture):
        transport.estimate(
            market_question="Will X happen?",
            outcome_names=("Yes", "No"),
            market_context={},
        )
    user_prompt = captured["messages"][-1]["content"]
    assert "volume_24h" not in user_prompt
    assert user_prompt.endswith(
        "then commit to your probability. Return JSON: "
        '{"reasoning": "<brief explanation>", '
        '"p_yes": <number 0-1>, "confidence": <number 0-1>}'
    )
