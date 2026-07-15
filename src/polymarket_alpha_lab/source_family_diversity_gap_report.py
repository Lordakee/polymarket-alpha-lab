"""Pure Phase 1 source-family diversity gap report."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_SOURCE_FAMILY_DIVERSITY_GAP_REPORT_VERSION = (
    "source-family-diversity-gap-report-v0"
)

SUFFICIENT_REASON = "source_family_diversity_sufficient"
FAMILY_COUNT_BELOW_REQUIRED_BLOCKER = "source_family_count_below_required_blocker"
INDEPENDENT_SOURCE_COUNT_BELOW_REQUIRED_BLOCKER = (
    "independent_source_count_below_required_blocker"
)
OFFICIAL_SOURCE_MISSING_ATTENTION = "official_source_missing_attention"
SINGLE_FAMILY_DOMINANCE_PROBABILITY_ATTENTION = (
    "single_family_dominance_probability_attention"
)

REASON_CODES = (
    FAMILY_COUNT_BELOW_REQUIRED_BLOCKER,
    INDEPENDENT_SOURCE_COUNT_BELOW_REQUIRED_BLOCKER,
    OFFICIAL_SOURCE_MISSING_ATTENTION,
    SINGLE_FAMILY_DOMINANCE_PROBABILITY_ATTENTION,
    SUFFICIENT_REASON,
)
DIVERSITY_STATUSES = ("sufficient", "watch", "blocked")
MANUAL_NEXT_STEPS = (
    "no_manual_review_required",
    "manual_source_family_diversity_review",
    "add_independent_source_family_review",
)

_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DOMINANCE_ATTENTION_THRESHOLD = Decimal("0.750000")


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class SourceFamilyDiversityGapInput(_FinalDataclass):
    independent_source_count: Decimal
    source_family_count: Decimal
    official_source_count: Decimal
    single_family_dominance_probability: Decimal
    required_family_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, SourceFamilyDiversityGapInput, "input")
        for field_name in (
            "independent_source_count",
            "source_family_count",
            "official_source_count",
            "required_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "single_family_dominance_probability",
            _require_ratio(
                "single_family_dominance_probability",
                self.single_family_dominance_probability,
            ),
        )
        _validate_input(self)
        require_paper_only_flags("source family diversity gap input", self)


@dataclass(frozen=True)
class SourceFamilyDiversityGapReport(_FinalDataclass):
    config_version: str
    diversity_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    independent_source_count: Decimal
    source_family_count: Decimal
    official_source_count: Decimal
    single_family_dominance_probability: Decimal
    required_family_count: Decimal
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, SourceFamilyDiversityGapReport, "report")
        _require_public_string("config_version", self.config_version)
        _require_diversity_status("diversity_status", self.diversity_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_manual_next_step("manual_next_step", self.manual_next_step)
        for field_name in (
            "independent_source_count",
            "source_family_count",
            "official_source_count",
            "required_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "single_family_dominance_probability",
            _require_ratio(
                "single_family_dominance_probability",
                self.single_family_dominance_probability,
            ),
        )
        _validate_report(self)
        require_paper_only_flags("source family diversity gap report", self)
        if self.payload_digest != "pending":
            if not _is_sha256(self.payload_digest):
                raise ValueError("payload_digest must be a sha256 hex digest")
            if self.payload_digest != source_family_diversity_gap_payload_digest(self):
                raise ValueError("payload_digest does not match report payload")


def build_source_family_diversity_gap_report(
    diversity_input: SourceFamilyDiversityGapInput,
    *,
    config_version: str = DEFAULT_SOURCE_FAMILY_DIVERSITY_GAP_REPORT_VERSION,
) -> SourceFamilyDiversityGapReport:
    if type(diversity_input) is not SourceFamilyDiversityGapInput:
        raise ValueError("diversity_input must be a SourceFamilyDiversityGapInput")
    _require_public_string("config_version", config_version)
    require_paper_only_flags("source family diversity gap input", diversity_input)

    reason_codes = _reason_codes(diversity_input)
    diversity_status = _diversity_status(reason_codes)
    manual_next_step = _manual_next_step(diversity_status)
    report = SourceFamilyDiversityGapReport(
        config_version=config_version,
        diversity_status=diversity_status,
        reason_codes=reason_codes,
        manual_next_step=manual_next_step,
        independent_source_count=diversity_input.independent_source_count,
        source_family_count=diversity_input.source_family_count,
        official_source_count=diversity_input.official_source_count,
        single_family_dominance_probability=(
            diversity_input.single_family_dominance_probability
        ),
        required_family_count=diversity_input.required_family_count,
        payload_digest="pending",
    )
    return SourceFamilyDiversityGapReport(
        config_version=report.config_version,
        diversity_status=report.diversity_status,
        reason_codes=report.reason_codes,
        manual_next_step=report.manual_next_step,
        independent_source_count=report.independent_source_count,
        source_family_count=report.source_family_count,
        official_source_count=report.official_source_count,
        single_family_dominance_probability=(
            report.single_family_dominance_probability
        ),
        required_family_count=report.required_family_count,
        payload_digest=source_family_diversity_gap_payload_digest(report),
    )


def source_family_diversity_gap_payload(
    report: SourceFamilyDiversityGapReport,
) -> dict[str, Any]:
    if type(report) is not SourceFamilyDiversityGapReport:
        raise ValueError("report must be a SourceFamilyDiversityGapReport")
    require_paper_only_flags("source family diversity gap report", report)
    _validate_report(report)
    expected_digest = source_family_diversity_gap_payload_digest(report)
    if report.payload_digest != expected_digest:
        raise ValueError("payload_digest does not match report payload")
    payload = _public_payload_for_digest(report)
    payload["payload_digest"] = expected_digest
    reject_unsafe_surface_fields("source family diversity gap payload", payload)
    return payload


def source_family_diversity_gap_payload_digest(
    report: SourceFamilyDiversityGapReport,
) -> str:
    if type(report) is not SourceFamilyDiversityGapReport:
        raise ValueError("report must be a SourceFamilyDiversityGapReport")
    payload = _public_payload_for_digest(report)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _is_sha256(value: object) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _reason_codes(
    diversity_input: SourceFamilyDiversityGapInput,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if diversity_input.source_family_count < diversity_input.required_family_count:
        reason_codes.append(FAMILY_COUNT_BELOW_REQUIRED_BLOCKER)
    if diversity_input.independent_source_count < diversity_input.required_family_count:
        reason_codes.append(INDEPENDENT_SOURCE_COUNT_BELOW_REQUIRED_BLOCKER)
    if diversity_input.official_source_count == _ZERO:
        reason_codes.append(OFFICIAL_SOURCE_MISSING_ATTENTION)
    if (
        diversity_input.single_family_dominance_probability
        >= _DOMINANCE_ATTENTION_THRESHOLD
    ):
        reason_codes.append(SINGLE_FAMILY_DOMINANCE_PROBABILITY_ATTENTION)
    if not reason_codes:
        reason_codes.append(SUFFICIENT_REASON)
    return _normalize_reason_codes(tuple(reason_codes))


def _diversity_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_blocker") for reason_code in reason_codes):
        return "blocked"
    if reason_codes != (SUFFICIENT_REASON,):
        return "watch"
    return "sufficient"


def _manual_next_step(diversity_status: str) -> str:
    if diversity_status == "blocked":
        return "add_independent_source_family_review"
    if diversity_status == "watch":
        return "manual_source_family_diversity_review"
    return "no_manual_review_required"


def _public_payload_for_digest(report: SourceFamilyDiversityGapReport) -> dict[str, Any]:
    payload = json_ready_no_floats(
        {
            "config_version": report.config_version,
            "diversity_status": report.diversity_status,
            "reason_codes": report.reason_codes,
            "manual_next_step": report.manual_next_step,
            "independent_source_count": report.independent_source_count,
            "source_family_count": report.source_family_count,
            "official_source_count": report.official_source_count,
            "single_family_dominance_probability": (
                report.single_family_dominance_probability
            ),
            "required_family_count": report.required_family_count,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    reject_unsafe_surface_fields("source family diversity gap payload", payload)
    return payload


def _validate_input(diversity_input: SourceFamilyDiversityGapInput) -> None:
    if diversity_input.source_family_count > diversity_input.independent_source_count:
        raise ValueError("source_family_count must not exceed independent_source_count")
    if diversity_input.official_source_count > diversity_input.independent_source_count:
        raise ValueError("official_source_count must not exceed independent_source_count")
    if diversity_input.required_family_count <= _ZERO:
        raise ValueError("required_family_count must be positive")


def _validate_report(report: SourceFamilyDiversityGapReport) -> None:
    if report.source_family_count > report.independent_source_count:
        raise ValueError("source_family_count must not exceed independent_source_count")
    if report.official_source_count > report.independent_source_count:
        raise ValueError("official_source_count must not exceed independent_source_count")
    if report.required_family_count <= _ZERO:
        raise ValueError("required_family_count must be positive")
    expected_reason_codes = _reason_codes(
        SourceFamilyDiversityGapInput(
            independent_source_count=report.independent_source_count,
            source_family_count=report.source_family_count,
            official_source_count=report.official_source_count,
            single_family_dominance_probability=(
                report.single_family_dominance_probability
            ),
            required_family_count=report.required_family_count,
        ),
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match diversity inputs")
    if report.diversity_status != _diversity_status(report.reason_codes):
        raise ValueError("diversity_status must match reason_codes")
    if report.manual_next_step != _manual_next_step(report.diversity_status):
        raise ValueError("manual_next_step must match diversity_status")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANT)


def _require_ratio(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > _ONE:
        raise ValueError(f"{field_name} must be less than or equal to 1")
    return normalized


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    allowed = set(REASON_CODES)
    for reason_code in reason_codes:
        _require_public_string("reason_code", reason_code)
        if reason_code not in allowed:
            raise ValueError(f"unknown reason_code: {reason_code}")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(sorted(normalized, key=REASON_CODES.index))


def _require_diversity_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in DIVERSITY_STATUSES:
        raise ValueError(f"{field_name} must be sufficient, watch, or blocked")


def _require_manual_next_step(field_name: str, value: object) -> None:
    if type(value) is not str or value not in MANUAL_NEXT_STEPS:
        raise ValueError(f"{field_name} must be a known manual next step")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    lowered = value.lower()
    for unsafe_fragment in (
        "live",
        "auth",
        "wallet",
        "order",
        "keys",
        "sign",
        "execute",
    ):
        if unsafe_fragment in lowered:
            raise ValueError(f"{field_name} must not contain unsafe public text")


__all__ = (
    "DEFAULT_SOURCE_FAMILY_DIVERSITY_GAP_REPORT_VERSION",
    "DIVERSITY_STATUSES",
    "MANUAL_NEXT_STEPS",
    "REASON_CODES",
    "SourceFamilyDiversityGapInput",
    "SourceFamilyDiversityGapReport",
    "build_source_family_diversity_gap_report",
    "source_family_diversity_gap_payload",
    "source_family_diversity_gap_payload_digest",
)
