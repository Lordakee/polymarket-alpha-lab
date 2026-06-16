"""Paper-only LLM forecast provider reports (pure transform leaf).

This is the pure transform half of the LLM forecast provider. It takes an
already-fetched probability-model result and turns it into a paper-only /
report-only ``PaperLLMForecast`` -- a real epistemic P(YES) estimate that can
be calibrated and judged (unlike the microstructure ``yes_ask_naive_v0`` /
``book_imbalance_v0`` heuristics).

It is a NETWORK-FREE leaf: it does NOT import the transport module and does
NOT perform any I/O. The already-fetched result is injected via the builder's
``result`` parameter (DI pattern, mirroring how the strategy cycle injects
order books into ``build_paper_book_imbalance_forecast``).

I1 (leaf-local Protocol): ``build_paper_llm_forecast`` types its ``result``
parameter against a leaf-local ``_ProbabilityModelResult`` runtime-checkable
Protocol, NOT the transport's ``ProbabilityModelResult``. This keeps the leaf
network-free -- it has no import edge to ``llm_research_transport``. The
transport's concrete result satisfies this Protocol structurally.

I2 (is-not-None clamp): ``fair_probability_yes`` and ``confidence`` use
``is not None`` guards, NEVER truthiness -- ``Decimal("0")`` is falsy but is a
valid probability. Values are clamped to ``[0, 1]``. A ``None`` ``raw_p_yes``
falls back to ``low_confidence_value`` and records ``("llm_parse_failed",)``.

The forecast is research-triage only; it is not a trade instruction,
investment ranking, recommendation, financial advice, or live-execution
signal. ``paper_only is True`` / ``report_only is True`` are hard-enforced
with ``is``.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from polymarket_alpha_lab.domain import NormalizedMarket


__all__ = (
    "PaperLLMForecastConfig",
    "PaperLLMForecast",
    "PaperLLMForecastLog",
    "build_paper_llm_forecast",
)


ZERO = Decimal("0")
ONE = Decimal("1")
COST_QUANTUM = Decimal("0.000001")

BASIS_VALUES = ("llm_glm_v0",)


@runtime_checkable
class _ProbabilityModelResult(Protocol):
    """Leaf-local structural contract for an injected probability-model result.

    I1: defined HERE (not imported from ``llm_research_transport``) so the leaf
    stays network-free. The transport's ``ProbabilityModelResult`` dataclass
    satisfies this Protocol structurally (it exposes all five attributes). The
    leaf guards ``build_paper_llm_forecast`` with ``isinstance(result,
    _ProbabilityModelResult)`` so only a structurally-compatible result is
    accepted, without any transport import edge.
    """

    @property
    def raw_p_yes(self) -> Decimal | None: ...

    @property
    def raw_confidence(self) -> Decimal | None: ...

    @property
    def raw_content(self) -> str: ...

    @property
    def model_name(self) -> str: ...

    @property
    def finish_reason(self) -> str: ...


@dataclass(frozen=True)
class PaperLLMForecastConfig:
    """Configuration for the LLM forecast model."""

    config_version: str = "llm-forecast-v1"
    model_name: str = "glm-4-flash"
    # M1: every Decimal default is string-constructed (never a float literal).
    low_confidence_value: Decimal = Decimal("0.5000")
    high_confidence_value: Decimal = Decimal("0.7500")
    max_question_chars: int = 500

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("model_name", self.model_name)
        _require_probability_decimal("low_confidence_value", self.low_confidence_value)
        _require_probability_decimal(
            "high_confidence_value",
            self.high_confidence_value,
        )
        _require_positive_int("max_question_chars", self.max_question_chars)


@dataclass(frozen=True)
class PaperLLMForecast:
    """A paper-only / report-only LLM forecast for one market."""

    generated_at: datetime
    config_version: str
    market_slug: str
    question: str
    fair_probability_yes: Decimal
    confidence: Decimal
    basis: str
    model_name: str
    raw_p_yes: Decimal | None
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("question", self.question)
        _require_finite_decimal("fair_probability_yes", self.fair_probability_yes)
        object.__setattr__(
            self,
            "fair_probability_yes",
            _quantize(self.fair_probability_yes),
        )
        _require_probability_decimal(
            "fair_probability_yes",
            self.fair_probability_yes,
        )
        _require_finite_decimal("confidence", self.confidence)
        object.__setattr__(self, "confidence", _quantize(self.confidence))
        _require_probability_decimal("confidence", self.confidence)
        _require_canonical_string("basis", self.basis)
        if self.basis not in BASIS_VALUES:
            raise ValueError("basis must be a known paper forecast basis")
        _require_canonical_string("model_name", self.model_name)
        if self.raw_p_yes is not None:
            _require_optional_finite_decimal("raw_p_yes", self.raw_p_yes)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_string_tuple("reason_codes", self.reason_codes),
        )
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")


@dataclass(frozen=True)
class PaperLLMForecastLog:
    """Append-only JSONL log for LLM forecast reports."""

    path: Path | str

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _normalize_log_path(self.path))

    def append(self, forecast: PaperLLMForecast) -> None:
        if not isinstance(forecast, PaperLLMForecast):
            raise ValueError("forecast must be a PaperLLMForecast")
        _validate_report_tree(forecast)
        line = (
            json.dumps(_json_ready(asdict(forecast)), allow_nan=False, sort_keys=True)
            + "\n"
        )
        path = _normalize_log_path(self.path)
        _validate_log_parent(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line)


def build_paper_llm_forecast(
    market: NormalizedMarket,
    *,
    result: _ProbabilityModelResult,
    config: PaperLLMForecastConfig,
    generated_at: datetime,
) -> PaperLLMForecast:
    """Build a paper-only LLM forecast from a caller-supplied result.

    I1: ``result`` is guarded by the leaf-local ``_ProbabilityModelResult``
    Protocol, so the transport's concrete ``ProbabilityModelResult`` is
    accepted structurally WITHOUT importing the transport module.

    I2: ``raw_p_yes`` / ``raw_confidence`` use ``is not None`` (never
    truthiness -- ``Decimal("0")`` is falsy but valid). A ``None`` ``raw_p_yes``
    yields ``low_confidence_value`` and the ``llm_parse_failed`` reason code;
    otherwise the value is clamped to ``[0, 1]`` and ``llm_probability_estimated``
    is recorded. ``confidence`` is clamped independently (also ``is not None``).
    """
    if not isinstance(market, NormalizedMarket):
        raise ValueError("market must be a NormalizedMarket")
    if not isinstance(result, _ProbabilityModelResult):
        raise ValueError("result must be a _ProbabilityModelResult")
    if not isinstance(config, PaperLLMForecastConfig):
        raise ValueError("config must be a PaperLLMForecastConfig")
    if not isinstance(generated_at, datetime):
        raise ValueError("generated_at must be a datetime")

    raw_p_yes = result.raw_p_yes
    raw_confidence = result.raw_confidence

    # I2: ``is not None`` -- never truthiness. Decimal("0") is falsy but valid.
    if raw_p_yes is not None:
        fair_probability_yes = _clamp(raw_p_yes, ZERO, ONE)
        primary_reason = "llm_probability_estimated"
    else:
        fair_probability_yes = config.low_confidence_value
        primary_reason = "llm_parse_failed"

    if raw_confidence is not None:
        confidence = _clamp(raw_confidence, ZERO, ONE)
    else:
        confidence = config.low_confidence_value

    model_name = (
        result.model_name
        if isinstance(result.model_name, str) and result.model_name.strip()
        else config.model_name
    )

    return PaperLLMForecast(
        generated_at=generated_at,
        config_version=config.config_version,
        market_slug=market.market.market_slug,
        question=market.market.question,
        fair_probability_yes=fair_probability_yes,
        confidence=confidence,
        basis="llm_glm_v0",
        model_name=model_name,
        raw_p_yes=raw_p_yes,
        reason_codes=(primary_reason,),
        paper_only=True,
        report_only=True,
    )


def _clamp(value: Decimal, low: Decimal, high: Decimal) -> Decimal:
    _require_finite_decimal("clamp", value)
    clamped = low if value < low else high if value > high else value
    return clamped.quantize(COST_QUANTUM)


def _quantize(value: Decimal) -> Decimal:
    _require_finite_decimal("quantize", value)
    return value.quantize(COST_QUANTUM)


def _as_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError("datetime value is required")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: str) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_decimal(field_name: str, value: Decimal) -> None:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")


def _require_finite_decimal(field_name: str, value: Decimal) -> None:
    _require_decimal(field_name, value)
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_optional_finite_decimal(field_name: str, value: Decimal | None) -> None:
    if value is not None:
        _require_finite_decimal(field_name, value)


def _require_probability_decimal(field_name: str, value: Decimal) -> None:
    _require_finite_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")


def _require_positive_int(field_name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _normalize_string_tuple(field_name: str, value: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    if not items:
        raise ValueError(f"{field_name} must contain at least one value")
    for item in items:
        _require_canonical_string(field_name, item)
    return items


def _validate_report_tree(forecast: PaperLLMForecast) -> None:
    PaperLLMForecast(
        generated_at=forecast.generated_at,
        config_version=forecast.config_version,
        market_slug=forecast.market_slug,
        question=forecast.question,
        fair_probability_yes=forecast.fair_probability_yes,
        confidence=forecast.confidence,
        basis=forecast.basis,
        model_name=forecast.model_name,
        raw_p_yes=forecast.raw_p_yes,
        reason_codes=forecast.reason_codes,
        paper_only=forecast.paper_only,
        report_only=forecast.report_only,
    )


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        _require_finite_decimal("JSON Decimal value", value)
        return str(value)
    if isinstance(value, datetime):
        return _as_utc(value).isoformat()
    if isinstance(value, bool) or value is None or isinstance(value, (int, str)):
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for item_key, item_value in value.items():
            if not isinstance(item_key, str):
                raise ValueError("JSON object keys must be strings")
            ready[item_key] = _json_ready(item_value)
        return ready
    raise ValueError("value is not JSON serializable")


def _normalize_log_path(value: Path | str) -> Path:
    if isinstance(value, str):
        if not value.strip():
            raise ValueError("path must be nonblank")
        path = Path(value)
    elif isinstance(value, Path):
        path = value
    else:
        raise ValueError("path must be a Path or string")
    if path.exists() and path.is_dir():
        raise ValueError("path must not be an existing directory")
    _validate_log_parent(path)
    return path


def _validate_log_parent(path: Path) -> None:
    parent = path.parent
    while not parent.exists():
        if parent == parent.parent:
            break
        parent = parent.parent
    if parent.exists() and not parent.is_dir():
        raise ValueError("parent path must be a directory")
