"""Read-only outbound HTTPS probability-model research transport.

This is the network layer for the LLM forecast provider (mirrors the
``api.py`` JsonTransport/UrlopenTransport DI pattern). It performs a single
read-only outbound HTTPS POST to the Zhipu GLM chat-completions endpoint to
estimate a market's P(YES). It is the same class of research fetch as
``api.py``'s public Polymarket reads -- it does not authenticate to an
exchange, read account/position state, handle wallets or private keys, place
orders, or write anywhere.

The transport is intentionally unrestricted on stdlib (like ``api.py``): no
scope test guards its imports. The pure transform leaf ``llm_forecast.py``
depends on a leaf-local Protocol so it never imports this module.

Decimal discipline (project-wide "NEVER float"):
- All stored numeric fields on ``ProbabilityModelResult`` are ``Decimal``.
- The LLM JSON content is parsed with ``json.loads(content, parse_float=Decimal)``
  so ``raw_p_yes`` / ``raw_confidence`` are ``Decimal`` (never ``float``). This
  is the I3 guarantee: a bare ``json.loads`` would silently yield ``float``.
- All Decimal defaults are string-constructed (``Decimal("0.3")``, never ``0.3``).
- ``temperature`` and ``timeout_seconds`` are serialized to ephemeral wire
  values only; the only numbers retained are Decimals.

Token isolation (M2): ``api_token`` lives ONLY on ``GLMChatTransport``. It is
never copied into ``ProbabilityModelResult``, never logged, and never archived.
``ProbabilityModelResult`` carries no credential material.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Protocol
from urllib.request import Request, urlopen


__all__ = (
    "ProbabilityModelTransport",
    "GLMChatTransport",
    "ProbabilityModelResult",
)


_ZERO = Decimal("0")
_ONE = Decimal("1")
_MICROSECONDS_PER_SECOND = Decimal("1000000")


# Superforecaster-style system prompt sent as the ``system`` role message.
# Surfaces base rate / evidence / time horizon / market efficiency / rules
# clarity as explicit reasoning factors to keep GLM-4-flash well-calibrated.
_SYSTEM_PROMPT = (
    "You are a superforecaster estimating the probability of a prediction market outcome. "
    "Consider these factors in your assessment:\n"
    "1. Base rate: How often do similar events occur historically?\n"
    "2. Evidence: What concrete evidence supports or contradicts each outcome?\n"
    "3. Time horizon: How much time remains, and does it favor YES or NO?\n"
    "4. Market efficiency: High volume/liquidity suggests the current price is informative; "
    "large spreads suggest uncertainty.\n"
    "5. Rules clarity: Clear resolution criteria increase confidence; ambiguous criteria decrease it.\n"
    "\n"
    "Use the provided market context (volume, liquidity, spread, end_time, rules) to inform your estimate. "
    "Be well-calibrated: avoid extreme confidence (0.0 or 1.0) without overwhelming evidence. "
    "Your output must be valid JSON."
)


class ProbabilityModelTransport(Protocol):
    """Read-only probability-estimation surface (Protocol-only DI contract).

    The concrete transport (a Zhipu GLM reader) is constructed by the caller
    and injected. ``estimate`` performs one outbound read-only HTTPS call and
    returns the parsed probability-model result. It never authenticates to an
    exchange, reads accounts, handles wallets, or places orders.
    """

    def estimate(
        self,
        *,
        market_question: str,
        outcome_names: tuple[str, ...],
        market_context: dict[str, str] | None = None,
    ) -> "ProbabilityModelResult":
        """Estimate P(YES) for one market question and return the raw result.

        ``market_context`` (optional) carries market metadata (volume,
        liquidity, end_time, rules, ...) that is appended to the user prompt so
        the model can produce a better-grounded probability estimate. When
        ``None`` (default) no market-context lines are appended to the user
        prompt.
        """
        ...


@dataclass(frozen=True)
class GLMChatTransport:
    """Concrete ``ProbabilityModelTransport`` over Zhipu GLM chat completions.

    Uses stdlib ``urllib.request`` (POST, Bearer header, JSON body) exactly
    like ``api.py``'s ``UrlopenTransport``. The request forces structured JSON
    output (``response_format: {"type": "json_object"}``) and asks the model
    for ``{"p_yes": <0-1>, "confidence": <0-1>}``.

    ``api_token`` is caller-supplied (never read from env/disk here) and is
    kept ONLY on this dataclass -- it never reaches ``ProbabilityModelResult``
    or any log/archive line (M2).
    """

    # ``api_token`` has no default (caller-supplied), so it must precede the
    # defaulted fields per frozen-dataclass field ordering.
    api_token: str
    endpoint_url: str = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    model: str = "glm-4-flash"
    # M1: every Decimal default is string-constructed (never a float literal).
    temperature: Decimal = Decimal("0.3")
    max_tokens: int = 256
    timeout_seconds: Decimal = Decimal("15.0")

    def __post_init__(self) -> None:
        if not isinstance(self.api_token, str) or not self.api_token.strip():
            raise ValueError("api_token must be a nonblank string")
        if not isinstance(self.endpoint_url, str) or not self.endpoint_url.strip():
            raise ValueError("endpoint_url must be a nonblank string")
        if not isinstance(self.model, str) or not self.model.strip():
            raise ValueError("model must be a nonblank string")
        if not isinstance(self.temperature, Decimal):
            raise ValueError("temperature must be a Decimal")
        if not self.temperature.is_finite() or self.temperature < _ZERO:
            raise ValueError("temperature must be a nonnegative finite Decimal")
        if isinstance(self.max_tokens, bool) or not isinstance(self.max_tokens, int):
            raise ValueError("max_tokens must be an int")
        if self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        if not isinstance(self.timeout_seconds, Decimal):
            raise ValueError("timeout_seconds must be a Decimal")
        if not self.timeout_seconds.is_finite() or self.timeout_seconds <= _ZERO:
            raise ValueError("timeout_seconds must be a positive finite Decimal")

    def estimate(
        self,
        *,
        market_question: str,
        outcome_names: tuple[str, ...],
        market_context: dict[str, str] | None = None,
    ) -> "ProbabilityModelResult":
        """Perform one read-only GLM estimate and return the parsed result.

        Never raises a custom exception type: network/HTTP/JSON failures are
        captured into a ``ProbabilityModelResult`` with ``raw_p_yes=None`` /
        ``raw_confidence=None`` so the caller's per-market isolation can turn a
        failed estimate into a low-confidence forecast rather than aborting.

        ``market_context`` (optional, Stage 10) carries market metadata that is
        appended to the user prompt for a better-grounded estimate. When
        ``None`` no market-context lines are appended (the estimate still works
        and returns a parsed result; the superforecaster system prompt is sent
        regardless).
        """
        user_prompt = _build_prompt(
            market_question, outcome_names, market_context=market_context
        )
        # temperature/max_tokens/timeout are ephemeral wire values (analogous to
        # api.py's float timeout); the only numbers RETAINED are Decimals.
        body = json.dumps(
            {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": float(self.temperature),
                "max_tokens": self.max_tokens,
                "response_format": {"type": "json_object"},
            }
        ).encode("utf-8")
        request = Request(
            self.endpoint_url,
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        started_at = datetime.now(UTC)
        raw_text = ""
        try:
            # urlopen's timeout is an ephemeral float seconds (api.py precedent).
            with urlopen(request, timeout=float(self.timeout_seconds)) as response:
                raw_text = response.read().decode("utf-8")
        except Exception:
            # Network/HTTP failure -> empty content -> parse fail downstream.
            raw_text = ""
        elapsed_seconds = _elapsed_decimal(started_at, datetime.now(UTC))

        if not raw_text:
            return ProbabilityModelResult(
                raw_p_yes=None,
                raw_confidence=None,
                raw_content="",
                model_name=self.model,
                finish_reason="",
                token_usage=0,
                elapsed_seconds=elapsed_seconds,
            )

        # I3: parse the OUTER envelope with parse_float=Decimal too (integer
        # literals like total_tokens stay int; only float literals become
        # Decimal). The inner LLM content is parsed separately below, also with
        # parse_float=Decimal -- NEVER bare json.loads.
        try:
            envelope = json.loads(raw_text, parse_float=Decimal)
        except (json.JSONDecodeError, ValueError):
            return ProbabilityModelResult(
                raw_p_yes=None,
                raw_confidence=None,
                raw_content=raw_text,
                model_name=self.model,
                finish_reason="",
                token_usage=0,
                elapsed_seconds=elapsed_seconds,
            )

        choices = envelope.get("choices") if isinstance(envelope, dict) else None
        choice = choices[0] if isinstance(choices, list) and choices else {}
        message = choice.get("message") if isinstance(choice, dict) else None
        content = (
            message.get("content") if isinstance(message, dict) else None
        )
        raw_content = content if isinstance(content, str) else ""
        finish_reason = choice.get("finish_reason") if isinstance(choice, dict) else ""
        finish_reason = finish_reason if isinstance(finish_reason, str) else ""
        usage = envelope.get("usage") if isinstance(envelope, dict) else None
        total_tokens = usage.get("total_tokens") if isinstance(usage, dict) else None
        token_usage = (
            total_tokens
            if isinstance(total_tokens, int) and not isinstance(total_tokens, bool)
            else 0
        )
        response_model = envelope.get("model") if isinstance(envelope, dict) else None
        model_name = (
            response_model
            if isinstance(response_model, str) and response_model.strip()
            else self.model
        )

        raw_p_yes, raw_confidence = _parse_probability_content(raw_content)
        return ProbabilityModelResult(
            raw_p_yes=raw_p_yes,
            raw_confidence=raw_confidence,
            raw_content=raw_content,
            model_name=model_name,
            finish_reason=finish_reason,
            token_usage=token_usage,
            elapsed_seconds=elapsed_seconds,
        )


@dataclass(frozen=True)
class ProbabilityModelResult:
    """Parsed probability-model output for one market (no credential material).

    ``raw_p_yes`` / ``raw_confidence`` are the pre-clamp Decimals parsed from
    the LLM's JSON content (or ``None`` on any parse failure). The pure leaf
    ``llm_forecast.py`` clamps these into ``[0, 1]`` and records reason codes.

    M2: this dataclass deliberately carries NO ``api_token`` / credential
    field. The token stays on ``GLMChatTransport`` only.
    """

    raw_p_yes: Decimal | None
    raw_confidence: Decimal | None
    raw_content: str
    model_name: str
    finish_reason: str
    token_usage: int
    elapsed_seconds: Decimal

    def __post_init__(self) -> None:
        if self.raw_p_yes is not None:
            if not isinstance(self.raw_p_yes, Decimal) or not self.raw_p_yes.is_finite():
                raise ValueError("raw_p_yes must be a finite Decimal or None")
        if self.raw_confidence is not None:
            if (
                not isinstance(self.raw_confidence, Decimal)
                or not self.raw_confidence.is_finite()
            ):
                raise ValueError("raw_confidence must be a finite Decimal or None")
        if not isinstance(self.raw_content, str):
            raise ValueError("raw_content must be a string")
        if not isinstance(self.model_name, str) or not self.model_name.strip():
            raise ValueError("model_name must be a nonblank string")
        if not isinstance(self.finish_reason, str):
            raise ValueError("finish_reason must be a string")
        if isinstance(self.token_usage, bool) or not isinstance(self.token_usage, int):
            raise ValueError("token_usage must be an int")
        if self.token_usage < 0:
            raise ValueError("token_usage must be nonnegative")
        if not isinstance(self.elapsed_seconds, Decimal):
            raise ValueError("elapsed_seconds must be a Decimal")
        if not self.elapsed_seconds.is_finite() or self.elapsed_seconds < _ZERO:
            raise ValueError("elapsed_seconds must be a nonnegative finite Decimal")


def _build_prompt(
    market_question: str,
    outcome_names: tuple[str, ...],
    market_context: dict[str, str] | None = None,
) -> str:
    question = market_question if isinstance(market_question, str) else ""
    names = ", ".join(outcome_names) if outcome_names else "Yes, No"
    lines = [f"Question: {question}", f"Outcomes: {names}"]
    # Stage 10: when market metadata is supplied, append each key/value pair to
    # the user prompt BEFORE the "Estimate P(YES)" instruction so the model
    # grounds its estimate in volume / liquidity / end_time / rules. An
    # empty/None context appends no context lines (the superforecaster system
    # prompt still describes how to use such context when present).
    if market_context:
        for key, value in market_context.items():
            lines.append(f"{key}: {value}")
    lines.append("")
    lines.append(
        'Estimate P(YES). Return JSON: '
        '{"p_yes": <number 0-1>, "confidence": <number 0-1>}'
    )
    return "\n".join(lines)


def _parse_probability_content(
    content: str,
) -> tuple[Decimal | None, Decimal | None]:
    """Parse the LLM JSON content into (p_yes, confidence) Decimals or Nones.

    I3: uses ``json.loads(content, parse_float=Decimal)`` so float literals
    become ``Decimal`` (never ``float``). Any parse/type failure yields
    ``(None, None)`` so the leaf records an ``llm_parse_failed`` reason.
    """
    if not content:
        return None, None
    try:
        data = json.loads(content, parse_float=Decimal)
    except (json.JSONDecodeError, ValueError):
        return None, None
    if not isinstance(data, dict):
        return None, None
    return _as_decimal_or_none(data.get("p_yes")), _as_decimal_or_none(
        data.get("confidence")
    )


def _as_decimal_or_none(value: object) -> Decimal | None:
    """Coerce a parsed JSON value to a finite Decimal or None.

    ``parse_float=Decimal`` already yields ``Decimal`` for float literals;
    integer literals stay ``int`` and are promoted to ``Decimal`` here. Booleans
    (an ``int`` subclass) are rejected, as are strings/None.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, Decimal):
        if not value.is_finite():
            return None
        return value
    if isinstance(value, int):
        return Decimal(value)
    return None


def _elapsed_decimal(started_at: datetime, ended_at: datetime) -> Decimal:
    """Compute elapsed seconds as a Decimal without any float intermediary.

    ``timedelta.total_seconds()`` returns ``float`` (forbidden project-wide), so
    the delta is decomposed into its int day/second/microsecond fields and
    assembled as a ``Decimal``.
    """
    delta = ended_at - started_at
    whole_seconds = Decimal(delta.days * 86400 + delta.seconds)
    fractional = Decimal(delta.microseconds) / _MICROSECONDS_PER_SECOND
    return whole_seconds + fractional
