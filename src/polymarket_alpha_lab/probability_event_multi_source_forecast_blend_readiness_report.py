"""Read-only multi-source forecast blend readiness report."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from typing import Mapping

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


PROBABILITY_EVENT_MULTI_SOURCE_FORECAST_BLEND_READINESS_REPORT_VERSION = (
    "probability-event-multi-source-forecast-blend-readiness-v0"
)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MODEL_WEIGHT = Decimal("0.300000")
SPECIALIST_WEIGHT = Decimal("0.300000")
MARKET_WEIGHT = Decimal("0.200000")
SOURCE_QUALITY_WEIGHT = Decimal("0.200000")

QUALITY_BLOCKED_THRESHOLD = Decimal("0.500000")
QUALITY_WATCH_THRESHOLD = Decimal("0.600000")
DISAGREEMENT_WATCH_THRESHOLD = Decimal("0.100000")
DISAGREEMENT_BLOCKED_THRESHOLD = Decimal("0.200000")

BLEND_STATUSES = ("ready", "watch", "blocked")
READY_REASON_CODE = "multi_source_forecast_blend_ready"
QUALITY_WATCH_REASON_CODE = "multi_source_forecast_quality_watch"
QUALITY_BLOCKED_REASON_CODE = "multi_source_forecast_quality_blocked"
DISAGREEMENT_WATCH_REASON_CODE = "multi_source_forecast_disagreement_watch"
DISAGREEMENT_BLOCKED_REASON_CODE = "multi_source_forecast_disagreement_blocked"

REASON_CODE_SEQUENCE = (
    QUALITY_BLOCKED_REASON_CODE,
    DISAGREEMENT_BLOCKED_REASON_CODE,
    QUALITY_WATCH_REASON_CODE,
    DISAGREEMENT_WATCH_REASON_CODE,
    READY_REASON_CODE,
)
PAYLOAD_KEYS = (
    "config_version",
    "model_forecast_probability",
    "specialist_forecast_probability",
    "market_implied_probability",
    "source_quality_probability",
    "blend_disagreement_probability",
    "blend_status",
    "blended_probability",
    "reason_codes",
    "manual_next_step",
    "paper_only",
    "report_only",
    "readonly",
)
PROBABILITY_FIELDS = (
    "model_forecast_probability",
    "specialist_forecast_probability",
    "market_implied_probability",
    "source_quality_probability",
    "blend_disagreement_probability",
)

READY_NEXT_STEP = (
    "Record blended probability in the manual review packet; no programmatic "
    "execution is permitted."
)
WATCH_NEXT_STEP = (
    "Review source quality and forecast disagreement before using the blend "
    "in paper-only decision support."
)
BLOCKED_NEXT_STEP = (
    "Escalate to manual review and gather corroborating source evidence; do "
    "not use this blend for execution."
)


class _BlendReadinessPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _BlendReadinessPublicDataclass and issubclass(
                base,
                _BlendReadinessPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} does not support subclassing")


@dataclass(frozen=True)
class ProbabilityEventMultiSourceForecastBlendReadinessInput(
    _BlendReadinessPublicDataclass,
):
    model_forecast_probability: Decimal
    specialist_forecast_probability: Decimal
    market_implied_probability: Decimal
    source_quality_probability: Decimal
    blend_disagreement_probability: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventMultiSourceForecastBlendReadinessInput,
            "blend readiness input",
        )
        for field_name in PROBABILITY_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("blend readiness input", self)


@dataclass(frozen=True)
class ProbabilityEventMultiSourceForecastBlendReadinessReport(
    _BlendReadinessPublicDataclass,
):
    config_version: str
    model_forecast_probability: Decimal
    specialist_forecast_probability: Decimal
    market_implied_probability: Decimal
    source_quality_probability: Decimal
    blend_disagreement_probability: Decimal
    blend_status: str
    blended_probability: Decimal
    reason_codes: tuple[str, ...]
    manual_next_step: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventMultiSourceForecastBlendReadinessReport,
            "blend readiness report",
        )
        _require_config_version(self.config_version)
        for field_name in PROBABILITY_FIELDS + ("blended_probability",):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "blend_status",
            _normalize_status("blend_status", self.blend_status),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_text("manual_next_step", self.manual_next_step)
        _validate_report(self)
        _require_hard_flags("blend readiness report", self)

    @property
    def public_payload(self) -> dict[str, object]:
        return probability_event_multi_source_forecast_blend_readiness_report_to_payload(
            self,
        )

    @property
    def payload_digest(self) -> str:
        return probability_event_multi_source_forecast_blend_readiness_report_digest(
            self,
        )


def build_probability_event_multi_source_forecast_blend_readiness_report(
    forecast_input: ProbabilityEventMultiSourceForecastBlendReadinessInput,
) -> ProbabilityEventMultiSourceForecastBlendReadinessReport:
    if type(forecast_input) is not ProbabilityEventMultiSourceForecastBlendReadinessInput:
        raise ValueError(
            "forecast_input must be a "
            "ProbabilityEventMultiSourceForecastBlendReadinessInput",
        )
    _require_hard_flags("blend readiness input", forecast_input)
    blend_status, reason_codes = _blend_findings(
        forecast_input.source_quality_probability,
        forecast_input.blend_disagreement_probability,
    )
    return ProbabilityEventMultiSourceForecastBlendReadinessReport(
        config_version=(
            PROBABILITY_EVENT_MULTI_SOURCE_FORECAST_BLEND_READINESS_REPORT_VERSION
        ),
        model_forecast_probability=forecast_input.model_forecast_probability,
        specialist_forecast_probability=forecast_input.specialist_forecast_probability,
        market_implied_probability=forecast_input.market_implied_probability,
        source_quality_probability=forecast_input.source_quality_probability,
        blend_disagreement_probability=forecast_input.blend_disagreement_probability,
        blend_status=blend_status,
        blended_probability=_blend_probability(forecast_input),
        reason_codes=reason_codes,
        manual_next_step=_manual_next_step(blend_status),
        paper_only=forecast_input.paper_only,
        report_only=forecast_input.report_only,
        readonly=forecast_input.readonly,
    )


def probability_event_multi_source_forecast_blend_readiness_report_to_payload(
    report: ProbabilityEventMultiSourceForecastBlendReadinessReport,
) -> dict[str, object]:
    if type(report) is not ProbabilityEventMultiSourceForecastBlendReadinessReport:
        raise ValueError(
            "report must be a "
            "ProbabilityEventMultiSourceForecastBlendReadinessReport",
        )
    _require_hard_flags("blend readiness report", report)
    _validate_report(report)
    payload = json_ready_no_floats(
        {
            "config_version": report.config_version,
            "model_forecast_probability": report.model_forecast_probability,
            "specialist_forecast_probability": report.specialist_forecast_probability,
            "market_implied_probability": report.market_implied_probability,
            "source_quality_probability": report.source_quality_probability,
            "blend_disagreement_probability": report.blend_disagreement_probability,
            "blend_status": report.blend_status,
            "blended_probability": report.blended_probability,
            "reason_codes": report.reason_codes,
            "manual_next_step": report.manual_next_step,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    validate_probability_event_multi_source_forecast_blend_readiness_public_payload(
        payload,
    )
    return payload


def probability_event_multi_source_forecast_blend_readiness_report_digest(
    report: ProbabilityEventMultiSourceForecastBlendReadinessReport,
) -> str:
    payload = probability_event_multi_source_forecast_blend_readiness_report_to_payload(
        report,
    )
    return _digest_payload(payload)


def validate_probability_event_multi_source_forecast_blend_readiness_public_payload(
    payload: Mapping[str, object],
) -> Mapping[str, object]:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    if tuple(payload.keys()) != PAYLOAD_KEYS:
        raise ValueError("payload must match the canonical blend readiness schema")
    reject_unsafe_surface_fields("blend readiness public payload", payload)
    _require_config_version(payload["config_version"])
    for field_name in PROBABILITY_FIELDS + ("blended_probability",):
        value = payload[field_name]
        if type(value) is not str:
            raise ValueError(f"{field_name} must be serialized as a string")
        _normalize_probability(field_name, Decimal(value))
    _normalize_status("blend_status", payload["blend_status"])
    _require_text("manual_next_step", payload["manual_next_step"])
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    reason_codes = _normalize_payload_reason_codes(payload["reason_codes"])
    source = ProbabilityEventMultiSourceForecastBlendReadinessInput(
        model_forecast_probability=Decimal(
            str(payload["model_forecast_probability"]),
        ),
        specialist_forecast_probability=Decimal(
            str(payload["specialist_forecast_probability"]),
        ),
        market_implied_probability=Decimal(str(payload["market_implied_probability"])),
        source_quality_probability=Decimal(str(payload["source_quality_probability"])),
        blend_disagreement_probability=Decimal(
            str(payload["blend_disagreement_probability"]),
        ),
    )
    expected_status, expected_reasons = _blend_findings(
        source.source_quality_probability,
        source.blend_disagreement_probability,
    )
    if payload["blend_status"] != expected_status:
        raise ValueError("blend_status must match forecast inputs")
    if reason_codes != expected_reasons:
        raise ValueError("reason_codes must match forecast inputs")
    if Decimal(str(payload["blended_probability"])) != _blend_probability(source):
        raise ValueError("blended_probability must match forecast inputs")
    if payload["manual_next_step"] != _manual_next_step(expected_status):
        raise ValueError("manual_next_step must match blend_status")
    return payload


def _blend_probability(
    forecast_input: ProbabilityEventMultiSourceForecastBlendReadinessInput,
) -> Decimal:
    return _quantize(
        forecast_input.model_forecast_probability * MODEL_WEIGHT
        + forecast_input.specialist_forecast_probability * SPECIALIST_WEIGHT
        + forecast_input.market_implied_probability * MARKET_WEIGHT
        + forecast_input.source_quality_probability * SOURCE_QUALITY_WEIGHT,
    )


def _blend_findings(
    source_quality_probability: Decimal,
    blend_disagreement_probability: Decimal,
) -> tuple[str, tuple[str, ...]]:
    blocked: list[str] = []
    watch: list[str] = []
    if source_quality_probability < QUALITY_BLOCKED_THRESHOLD:
        blocked.append(QUALITY_BLOCKED_REASON_CODE)
    elif source_quality_probability < QUALITY_WATCH_THRESHOLD:
        watch.append(QUALITY_WATCH_REASON_CODE)
    if blend_disagreement_probability >= DISAGREEMENT_BLOCKED_THRESHOLD:
        blocked.append(DISAGREEMENT_BLOCKED_REASON_CODE)
    elif blend_disagreement_probability >= DISAGREEMENT_WATCH_THRESHOLD:
        watch.append(DISAGREEMENT_WATCH_REASON_CODE)
    if blocked:
        return "blocked", _normalize_reason_codes(tuple(blocked))
    if watch:
        return "watch", _normalize_reason_codes(tuple(watch))
    return "ready", (READY_REASON_CODE,)


def _manual_next_step(blend_status: str) -> str:
    if blend_status == "blocked":
        return BLOCKED_NEXT_STEP
    if blend_status == "watch":
        return WATCH_NEXT_STEP
    return READY_NEXT_STEP


def _validate_report(
    report: ProbabilityEventMultiSourceForecastBlendReadinessReport,
) -> None:
    source = ProbabilityEventMultiSourceForecastBlendReadinessInput(
        model_forecast_probability=report.model_forecast_probability,
        specialist_forecast_probability=report.specialist_forecast_probability,
        market_implied_probability=report.market_implied_probability,
        source_quality_probability=report.source_quality_probability,
        blend_disagreement_probability=report.blend_disagreement_probability,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )
    expected_status, expected_reasons = _blend_findings(
        source.source_quality_probability,
        source.blend_disagreement_probability,
    )
    if report.blend_status != expected_status:
        raise ValueError("blend_status must match forecast inputs")
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match forecast inputs")
    if report.blended_probability != _blend_probability(source):
        raise ValueError("blended_probability must match forecast inputs")
    if report.manual_next_step != _manual_next_step(expected_status):
        raise ValueError("manual_next_step must match blend_status")


def _normalize_probability(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize(value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _normalize_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in BLEND_STATUSES:
        raise ValueError(f"{field_name} must be a supported blend status")
    return value


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    seen: set[str] = set()
    for reason_code in value:
        if type(reason_code) is not str or reason_code not in REASON_CODE_SEQUENCE:
            raise ValueError("reason_codes contains unsupported reason code")
        if reason_code in seen:
            raise ValueError("reason_codes must not contain duplicates")
        seen.add(reason_code)
    canonical = tuple(
        reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in seen
    )
    if value != canonical:
        raise ValueError("reason_codes must use canonical sequence")
    return canonical


def _normalize_payload_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is list:
        return _normalize_reason_codes(tuple(value))
    if type(value) is tuple:
        return _normalize_reason_codes(value)
    raise ValueError("reason_codes must be a list")


def _require_config_version(value: object) -> None:
    if value != PROBABILITY_EVENT_MULTI_SOURCE_FORECAST_BLEND_READINESS_REPORT_VERSION:
        raise ValueError("config_version must match blend readiness report version")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_text(field_name: str, value: object) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be non-empty text")


def _require_hard_flags(label: str, value: object) -> None:
    require_paper_only_flags(label, value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _digest_payload(payload: Mapping[str, object]) -> str:
    return sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()


__all__ = (
    "PROBABILITY_EVENT_MULTI_SOURCE_FORECAST_BLEND_READINESS_REPORT_VERSION",
    "BLEND_STATUSES",
    "ProbabilityEventMultiSourceForecastBlendReadinessInput",
    "ProbabilityEventMultiSourceForecastBlendReadinessReport",
    "build_probability_event_multi_source_forecast_blend_readiness_report",
    "probability_event_multi_source_forecast_blend_readiness_report_digest",
    "probability_event_multi_source_forecast_blend_readiness_report_to_payload",
    "validate_probability_event_multi_source_forecast_blend_readiness_public_payload",
)
