"""Read-only resolution source confidence weight report."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from typing import Mapping

from polymarket_alpha_lab.team_paper_guard import json_ready_no_floats


__all__ = (
    "CONFIDENCE_WEIGHT_STATUSES",
    "ProbabilityEventResolutionSourceConfidenceWeightInput",
    "ProbabilityEventResolutionSourceConfidenceWeightReport",
    "build_probability_event_resolution_source_confidence_weight_report",
    "probability_event_resolution_source_confidence_weight_report_digest",
    "probability_event_resolution_source_confidence_weight_report_to_payload",
    "validate_probability_event_resolution_source_confidence_weight_public_payload",
)


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

OFFICIAL_SOURCE_FACTOR = Decimal("0.500000")
INDEPENDENT_SOURCE_FACTOR = Decimal("0.300000")
MARKET_SIGNAL_FACTOR = Decimal("0.200000")
SOURCE_CONFLICT_FACTOR = Decimal("0.900000")
FRESHNESS_PENALTY_FACTOR = Decimal("0.100000")

REVIEW_CONFIDENCE_FLOOR = Decimal("0.200000")
HIGH_CONFIDENCE_FLOOR = Decimal("0.500000")
MATERIAL_CONFLICT_FLOOR = Decimal("0.200000")
CRITICAL_CONFLICT_FLOOR = Decimal("0.750000")
MATERIAL_FRESHNESS_FLOOR = Decimal("0.250000")
CRITICAL_FRESHNESS_FLOOR = Decimal("0.500000")

CONFIDENCE_WEIGHT_STATUSES = ("high_confidence", "review", "blocked")

READY_REASON_CODE = "resolution_source_confidence_weight_high"
REVIEW_REASON_CODE = "resolution_source_confidence_weight_review"
BLOCKED_REASON_CODE = "resolution_source_confidence_weight_blocked"
MATERIAL_CONFLICT_REASON_CODE = "resolution_source_conflict_material"
CRITICAL_CONFLICT_REASON_CODE = "resolution_source_conflict_critical"
MATERIAL_FRESHNESS_REASON_CODE = "resolution_source_freshness_penalty_material"
CRITICAL_FRESHNESS_REASON_CODE = "resolution_source_freshness_penalty_critical"

REASON_CODE_SEQUENCE = (
    READY_REASON_CODE,
    REVIEW_REASON_CODE,
    BLOCKED_REASON_CODE,
    MATERIAL_CONFLICT_REASON_CODE,
    CRITICAL_CONFLICT_REASON_CODE,
    MATERIAL_FRESHNESS_REASON_CODE,
    CRITICAL_FRESHNESS_REASON_CODE,
)

MANUAL_NEXT_STEP = (
    "Manual review: compare official resolution source, independent confirmation, "
    "and market signal before any separate decision process."
)

PAYLOAD_KEYS = (
    "official_source_weight_probability",
    "independent_source_weight_probability",
    "market_signal_weight_probability",
    "source_conflict_probability",
    "freshness_penalty_probability",
    "confidence_weight_status",
    "weighted_confidence_probability",
    "reason_codes",
    "manual_next_step",
    "paper_only",
    "report_only",
    "readonly",
)

PROBABILITY_FIELDS = (
    "official_source_weight_probability",
    "independent_source_weight_probability",
    "market_signal_weight_probability",
    "source_conflict_probability",
    "freshness_penalty_probability",
)


class _ResolutionSourceConfidencePublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _ResolutionSourceConfidencePublicDataclass and issubclass(
                base,
                _ResolutionSourceConfidencePublicDataclass,
            ):
                raise TypeError(f"{base.__name__} does not support subclassing")


@dataclass(frozen=True)
class ProbabilityEventResolutionSourceConfidenceWeightInput(
    _ResolutionSourceConfidencePublicDataclass,
):
    official_source_weight_probability: Decimal
    independent_source_weight_probability: Decimal
    market_signal_weight_probability: Decimal
    source_conflict_probability: Decimal
    freshness_penalty_probability: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventResolutionSourceConfidenceWeightInput,
            "resolution source confidence weight input",
        )
        for field_name in PROBABILITY_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_true_flags(self)


@dataclass(frozen=True)
class ProbabilityEventResolutionSourceConfidenceWeightReport(
    _ResolutionSourceConfidencePublicDataclass,
):
    official_source_weight_probability: Decimal
    independent_source_weight_probability: Decimal
    market_signal_weight_probability: Decimal
    source_conflict_probability: Decimal
    freshness_penalty_probability: Decimal
    confidence_weight_status: str
    weighted_confidence_probability: Decimal
    reason_codes: tuple[str, ...]
    manual_next_step: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventResolutionSourceConfidenceWeightReport,
            "resolution source confidence weight report",
        )
        for field_name in PROBABILITY_FIELDS + ("weighted_confidence_probability",):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "confidence_weight_status",
            _normalize_status(self.confidence_weight_status),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.manual_next_step != MANUAL_NEXT_STEP:
            raise ValueError("manual_next_step must match source confidence state")
        _require_true_flags(self)
        _validate_report(self)

    @property
    def public_payload(self) -> dict[str, object]:
        return probability_event_resolution_source_confidence_weight_report_to_payload(
            self,
        )

    @property
    def payload_digest(self) -> str:
        return probability_event_resolution_source_confidence_weight_report_digest(self)


def build_probability_event_resolution_source_confidence_weight_report(
    source: ProbabilityEventResolutionSourceConfidenceWeightInput,
) -> ProbabilityEventResolutionSourceConfidenceWeightReport:
    if type(source) is not ProbabilityEventResolutionSourceConfidenceWeightInput:
        raise ValueError(
            "source must be a ProbabilityEventResolutionSourceConfidenceWeightInput",
        )

    weighted_confidence_probability = _weighted_confidence_probability(source)
    confidence_weight_status = _confidence_weight_status(
        weighted_confidence_probability,
        source.source_conflict_probability,
        source.freshness_penalty_probability,
    )

    return ProbabilityEventResolutionSourceConfidenceWeightReport(
        official_source_weight_probability=source.official_source_weight_probability,
        independent_source_weight_probability=(
            source.independent_source_weight_probability
        ),
        market_signal_weight_probability=source.market_signal_weight_probability,
        source_conflict_probability=source.source_conflict_probability,
        freshness_penalty_probability=source.freshness_penalty_probability,
        confidence_weight_status=confidence_weight_status,
        weighted_confidence_probability=weighted_confidence_probability,
        reason_codes=_reason_codes(
            confidence_weight_status,
            source.source_conflict_probability,
            source.freshness_penalty_probability,
        ),
        manual_next_step=MANUAL_NEXT_STEP,
        paper_only=source.paper_only,
        report_only=source.report_only,
        readonly=source.readonly,
    )


def probability_event_resolution_source_confidence_weight_report_to_payload(
    report: ProbabilityEventResolutionSourceConfidenceWeightReport,
) -> dict[str, object]:
    if type(report) is not ProbabilityEventResolutionSourceConfidenceWeightReport:
        raise ValueError(
            "report must be a ProbabilityEventResolutionSourceConfidenceWeightReport",
        )
    _validate_report(report)
    payload = json_ready_no_floats(
        {
            "official_source_weight_probability": (
                report.official_source_weight_probability
            ),
            "independent_source_weight_probability": (
                report.independent_source_weight_probability
            ),
            "market_signal_weight_probability": report.market_signal_weight_probability,
            "source_conflict_probability": report.source_conflict_probability,
            "freshness_penalty_probability": report.freshness_penalty_probability,
            "confidence_weight_status": report.confidence_weight_status,
            "weighted_confidence_probability": (
                report.weighted_confidence_probability
            ),
            "reason_codes": report.reason_codes,
            "manual_next_step": report.manual_next_step,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    validate_probability_event_resolution_source_confidence_weight_public_payload(
        payload,
    )
    return payload


def probability_event_resolution_source_confidence_weight_report_digest(
    report: ProbabilityEventResolutionSourceConfidenceWeightReport,
) -> str:
    payload = probability_event_resolution_source_confidence_weight_report_to_payload(
        report,
    )
    return _digest_payload(payload)


def validate_probability_event_resolution_source_confidence_weight_public_payload(
    payload: Mapping[str, object],
) -> Mapping[str, object]:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    if tuple(payload.keys()) != PAYLOAD_KEYS:
        raise ValueError(
            "payload must match the canonical source confidence weight schema",
        )

    for field_name in PROBABILITY_FIELDS + ("weighted_confidence_probability",):
        value = payload[field_name]
        if type(value) is not str:
            raise ValueError(f"{field_name} must be serialized as a string")
        _normalize_probability(field_name, Decimal(value))

    for field_name in ("paper_only", "report_only", "readonly"):
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")

    status = _normalize_status(payload["confidence_weight_status"])
    reason_codes = _normalize_payload_reason_codes(
        "reason_codes",
        payload["reason_codes"],
    )
    if payload["manual_next_step"] != MANUAL_NEXT_STEP:
        raise ValueError("manual_next_step must match source confidence state")

    source = _source_from_payload(payload)
    expected_weighted_confidence_probability = _weighted_confidence_probability(source)
    weighted_confidence_probability = _normalize_probability(
        "weighted_confidence_probability",
        Decimal(payload["weighted_confidence_probability"]),
    )
    if weighted_confidence_probability != expected_weighted_confidence_probability:
        raise ValueError(
            "weighted_confidence_probability must match source confidence inputs",
        )
    expected_status = _confidence_weight_status(
        expected_weighted_confidence_probability,
        source.source_conflict_probability,
        source.freshness_penalty_probability,
    )
    if status != expected_status:
        raise ValueError("confidence_weight_status must match source confidence inputs")
    if reason_codes != _reason_codes(
        expected_status,
        source.source_conflict_probability,
        source.freshness_penalty_probability,
    ):
        raise ValueError("reason_codes must match source confidence inputs")
    return payload


def _source_from_payload(
    payload: Mapping[str, object],
) -> ProbabilityEventResolutionSourceConfidenceWeightInput:
    return ProbabilityEventResolutionSourceConfidenceWeightInput(
        official_source_weight_probability=Decimal(
            payload["official_source_weight_probability"],
        ),
        independent_source_weight_probability=Decimal(
            payload["independent_source_weight_probability"],
        ),
        market_signal_weight_probability=Decimal(
            payload["market_signal_weight_probability"],
        ),
        source_conflict_probability=Decimal(payload["source_conflict_probability"]),
        freshness_penalty_probability=Decimal(
            payload["freshness_penalty_probability"],
        ),
        paper_only=payload["paper_only"],  # type: ignore[arg-type]
        report_only=payload["report_only"],  # type: ignore[arg-type]
        readonly=payload["readonly"],  # type: ignore[arg-type]
    )


def _validate_report(
    report: ProbabilityEventResolutionSourceConfidenceWeightReport,
) -> None:
    source = ProbabilityEventResolutionSourceConfidenceWeightInput(
        official_source_weight_probability=report.official_source_weight_probability,
        independent_source_weight_probability=report.independent_source_weight_probability,
        market_signal_weight_probability=report.market_signal_weight_probability,
        source_conflict_probability=report.source_conflict_probability,
        freshness_penalty_probability=report.freshness_penalty_probability,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )
    expected_weighted_confidence_probability = _weighted_confidence_probability(source)
    if report.weighted_confidence_probability != expected_weighted_confidence_probability:
        raise ValueError(
            "weighted_confidence_probability must match source confidence inputs",
        )
    expected_status = _confidence_weight_status(
        expected_weighted_confidence_probability,
        report.source_conflict_probability,
        report.freshness_penalty_probability,
    )
    if report.confidence_weight_status != expected_status:
        raise ValueError("confidence_weight_status must match source confidence inputs")
    if report.reason_codes != _reason_codes(
        expected_status,
        report.source_conflict_probability,
        report.freshness_penalty_probability,
    ):
        raise ValueError("reason_codes must match source confidence inputs")


def _weighted_confidence_probability(
    source: ProbabilityEventResolutionSourceConfidenceWeightInput,
) -> Decimal:
    weighted = (
        source.official_source_weight_probability * OFFICIAL_SOURCE_FACTOR
        + source.independent_source_weight_probability * INDEPENDENT_SOURCE_FACTOR
        + source.market_signal_weight_probability * MARKET_SIGNAL_FACTOR
        - source.source_conflict_probability * SOURCE_CONFLICT_FACTOR
        - source.freshness_penalty_probability * FRESHNESS_PENALTY_FACTOR
    )
    return _normalize_probability("weighted_confidence_probability", max(weighted, ZERO))


def _confidence_weight_status(
    weighted_confidence_probability: Decimal,
    source_conflict_probability: Decimal,
    freshness_penalty_probability: Decimal,
) -> str:
    if (
        weighted_confidence_probability < REVIEW_CONFIDENCE_FLOOR
        or source_conflict_probability >= CRITICAL_CONFLICT_FLOOR
        or freshness_penalty_probability >= CRITICAL_FRESHNESS_FLOOR
    ):
        return "blocked"
    if (
        weighted_confidence_probability < HIGH_CONFIDENCE_FLOOR
        or source_conflict_probability >= MATERIAL_CONFLICT_FLOOR
        or freshness_penalty_probability >= MATERIAL_FRESHNESS_FLOOR
    ):
        return "review"
    return "high_confidence"


def _reason_codes(
    confidence_weight_status: str,
    source_conflict_probability: Decimal,
    freshness_penalty_probability: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if confidence_weight_status == "high_confidence":
        reason_codes.append(READY_REASON_CODE)
    elif confidence_weight_status == "review":
        reason_codes.append(REVIEW_REASON_CODE)
    elif confidence_weight_status == "blocked":
        reason_codes.append(BLOCKED_REASON_CODE)
    else:
        raise ValueError("confidence_weight_status must be supported")

    if source_conflict_probability >= CRITICAL_CONFLICT_FLOOR:
        reason_codes.append(CRITICAL_CONFLICT_REASON_CODE)
    elif source_conflict_probability >= MATERIAL_CONFLICT_FLOOR:
        reason_codes.append(MATERIAL_CONFLICT_REASON_CODE)

    if freshness_penalty_probability >= CRITICAL_FRESHNESS_FLOOR:
        reason_codes.append(CRITICAL_FRESHNESS_REASON_CODE)
    elif freshness_penalty_probability >= MATERIAL_FRESHNESS_FLOOR:
        reason_codes.append(MATERIAL_FRESHNESS_REASON_CODE)

    return tuple(
        reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in reason_codes
    )


def _normalize_probability(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(QUANTUM, rounding=ROUND_HALF_UP)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_status(value: object) -> str:
    if type(value) is not str or value not in CONFIDENCE_WEIGHT_STATUSES:
        raise ValueError("confidence_weight_status must be supported")
    return value


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    return _normalize_reason_code_items(field_name, value)


def _normalize_payload_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is list:
        return _normalize_reason_code_items(field_name, tuple(value))
    if type(value) is tuple:
        return _normalize_reason_code_items(field_name, value)
    raise ValueError(f"{field_name} must be a list")


def _normalize_reason_code_items(
    field_name: str,
    reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    seen: set[str] = set()
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in REASON_CODE_SEQUENCE:
            raise ValueError(f"{field_name} contains unsupported reason code")
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(reason_code)
    ordered = tuple(
        reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in seen
    )
    if reason_codes != ordered:
        raise ValueError(f"{field_name} must use canonical order")
    return ordered


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_true_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _digest_payload(payload: dict[str, object]) -> str:
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
