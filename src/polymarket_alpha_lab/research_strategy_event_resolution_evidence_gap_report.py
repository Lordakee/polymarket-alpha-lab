from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_STRATEGY_EVENT_RESOLUTION_EVIDENCE_GAP_CONFIG_VERSION = (
    "research-strategy-event-resolution-evidence-gap-v1"
)

_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0")
_ONE = Decimal("1")
_HOURS_IN_MICROSECOND = Decimal("3600000000")
_STATUS_ORDER = {"block": 0, "watch": 1, "pass": 2}
_REASON_CODE_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
_PUBLIC_ROW_ID_PATTERN = re.compile(r"^event_resolution_evidence_gap_[0-9]{6}$")
_CONFIG_PAYLOAD_KEYS = (
    "config_version",
    "freshness_target_hours",
    "pass_min_evidence_coverage_ratio",
    "watch_min_evidence_coverage_ratio",
    "pass_min_source_authority_ratio",
    "watch_min_source_authority_ratio",
    "pass_min_evidence_freshness_score",
    "watch_min_evidence_freshness_score",
    "pass_max_conflict_ratio",
    "watch_max_conflict_ratio",
    "coverage_gap_weight",
    "authority_gap_weight",
    "freshness_gap_weight",
    "conflict_weight",
    "paper_only",
    "report_only",
    "readonly",
)
_ROW_PAYLOAD_KEYS = (
    "public_row_id",
    "manual_review_rank",
    "source_count",
    "required_evidence_count",
    "verifiable_evidence_count",
    "authoritative_source_count",
    "fresh_source_count",
    "conflicting_source_count",
    "latest_evidence_at",
    "latest_evidence_age_hours",
    "evidence_coverage_ratio",
    "source_authority_ratio",
    "fresh_source_ratio",
    "latest_evidence_recency_score",
    "evidence_freshness_score",
    "conflict_ratio",
    "manual_review_priority_score",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
_REASON_COUNT_PAYLOAD_KEYS = (
    "reason_code",
    "count",
    "row_ratio",
    "paper_only",
    "report_only",
    "readonly",
)
_REPORT_PAYLOAD_KEYS = (
    "generated_at",
    "config_version",
    "config",
    "status",
    "event_count",
    "pass_count",
    "watch_count",
    "block_count",
    "review_required_count",
    "average_evidence_coverage_ratio",
    "average_source_authority_ratio",
    "average_evidence_freshness_score",
    "average_conflict_ratio",
    "average_manual_review_priority_score",
    "max_manual_review_priority_score",
    "total_conflicting_source_count",
    "reason_codes",
    "reason_code_counts",
    "rows",
    "paper_only",
    "report_only",
    "readonly",
    "derived_validation_digest",
)


def _quantize(field_name: str, value: Decimal) -> Decimal:
    try:
        with localcontext() as context:
            context.prec = 50
            return value.quantize(_QUANTUM, rounding=ROUND_HALF_EVEN)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} cannot be quantized to six decimals") from exc


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not be signed zero")
    return value


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    raw = _require_decimal(field_name, value)
    if raw < _ZERO or raw > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return _quantize(field_name, raw)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_decimal(field_name, value)
    if raw < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(field_name, raw)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_decimal(field_name, value)
    if raw <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return _quantize(field_name, raw)


def _normalize_count(field_name: str, value: object, *, positive: bool = False) -> Decimal:
    raw = _require_decimal(field_name, value)
    if raw < _ZERO or (positive and raw <= _ZERO):
        qualifier = "positive" if positive else "nonnegative"
        raise ValueError(f"{field_name} must be {qualifier}")
    if raw != raw.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return _quantize(field_name, raw)


def _decimal_count(value: int) -> Decimal:
    return _quantize("count", Decimal(value))


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{field_name} must be non-empty and stripped")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise ValueError(f"{field_name} must not contain control characters")
    return value


def _require_config_version(value: object) -> str:
    normalized = _require_canonical_string("config_version", value)
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", normalized):
        raise ValueError("config_version must be canonical")
    return normalized


def _normalize_private_source_refs(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("private_source_refs must be a tuple")
    normalized = tuple(
        _require_canonical_string("private_source_ref", item) for item in value
    )
    if len(normalized) != len(set(normalized)):
        raise ValueError("private_source_refs must be unique")
    return tuple(sorted(normalized))


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError("reason_codes must be a non-empty tuple")
    if any(type(item) is not str or not _REASON_CODE_PATTERN.fullmatch(item) for item in value):
        raise ValueError("reason_codes must contain canonical reason codes")
    if len(value) != len(set(value)):
        raise ValueError("reason_codes must be unique")
    return value


def _require_status(value: object, *, allow_no_inputs: bool = False) -> str:
    allowed = frozenset(_STATUS_ORDER) | ({"no_inputs"} if allow_no_inputs else set())
    if type(value) is not str or value not in allowed:
        suffix = ", no_inputs" if allow_no_inputs else ""
        raise ValueError(f"status must be one of: block, watch, pass{suffix}")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} hard flags must all be true")


def _require_exact_keys(
    label: str,
    value: object,
    expected_keys: tuple[str, ...],
) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError(f"{label} must be a dict")
    actual_keys = tuple(value)
    if actual_keys != expected_keys:
        expected_key_set = set(expected_keys)
        actual_key_set = set(actual_keys)
        missing = sorted(expected_key_set - actual_key_set)
        extra = sorted(actual_key_set - expected_key_set)
        raise ValueError(
            f"{label} must use exact schema and key order; "
            f"missing={missing}, extra={extra}"
        )
    return value


def _decimal_from_payload(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a canonical Decimal string") from exc
    normalized = _require_decimal(field_name, parsed)
    if value != str(normalized):
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _datetime_from_payload(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a canonical datetime string") from exc
    normalized = _as_utc(field_name, parsed)
    if value != normalized.isoformat():
        raise ValueError(f"{field_name} must be canonical UTC")
    return normalized


def _optional_datetime_from_payload(
    field_name: str,
    value: object,
) -> datetime | None:
    if value is None:
        return None
    return _datetime_from_payload(field_name, value)


def _optional_decimal_from_payload(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _decimal_from_payload(field_name, value)


def _true_from_payload(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be true")
    return True


def _reason_codes_from_payload(value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError("reason_codes must be a list")
    return _normalize_reason_codes(tuple(value))


def _raw_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    with localcontext() as context:
        context.prec = 50
        raw = numerator / denominator
    if raw < _ZERO or raw > _ONE:
        raise ValueError("derived ratio must be between zero and one")
    return raw


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    raw = _raw_ratio(numerator, denominator)
    return _normalize_ratio("ratio", raw)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _quantize("average", _ZERO)
    with localcontext() as context:
        context.prec = 50
        raw = sum(values, _ZERO) / Decimal(len(values))
    return _normalize_ratio("average", raw)


def _raw_age_hours(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    total_microseconds = (
        delta.days * 86_400_000_000
        + delta.seconds * 1_000_000
        + delta.microseconds
    )
    raw = Decimal(total_microseconds) / _HOURS_IN_MICROSECOND
    if raw < _ZERO:
        raise ValueError("latest_evidence_age_hours must be nonnegative")
    return raw


def _age_hours(generated_at: datetime, observed_at: datetime) -> Decimal:
    raw = _raw_age_hours(generated_at, observed_at)
    return _normalize_nonnegative_decimal("latest_evidence_age_hours", raw)


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )


@dataclass(frozen=True)
class ResearchStrategyEventResolutionEvidenceGapConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_EVENT_RESOLUTION_EVIDENCE_GAP_CONFIG_VERSION
    )
    freshness_target_hours: Decimal = Decimal("24")
    pass_min_evidence_coverage_ratio: Decimal = Decimal("0.800000")
    watch_min_evidence_coverage_ratio: Decimal = Decimal("0.500000")
    pass_min_source_authority_ratio: Decimal = Decimal("0.600000")
    watch_min_source_authority_ratio: Decimal = Decimal("0.300000")
    pass_min_evidence_freshness_score: Decimal = Decimal("0.700000")
    watch_min_evidence_freshness_score: Decimal = Decimal("0.400000")
    pass_max_conflict_ratio: Decimal = Decimal("0.100000")
    watch_max_conflict_ratio: Decimal = Decimal("0.300000")
    coverage_gap_weight: Decimal = Decimal("0.350000")
    authority_gap_weight: Decimal = Decimal("0.250000")
    freshness_gap_weight: Decimal = Decimal("0.250000")
    conflict_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyEventResolutionEvidenceGapConfig does not support subclassing"
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyEventResolutionEvidenceGapConfig:
            raise ValueError(
                "config must be exactly ResearchStrategyEventResolutionEvidenceGapConfig"
            )
        object.__setattr__(self, "config_version", _require_config_version(self.config_version))
        raw_freshness_target = _require_decimal(
            "freshness_target_hours",
            self.freshness_target_hours,
        )
        if raw_freshness_target <= _ZERO:
            raise ValueError("freshness_target_hours must be positive")
        object.__setattr__(
            self,
            "freshness_target_hours",
            _normalize_positive_decimal(
                "freshness_target_hours",
                raw_freshness_target,
            ),
        )
        ratio_field_names = (
            "pass_min_evidence_coverage_ratio",
            "watch_min_evidence_coverage_ratio",
            "pass_min_source_authority_ratio",
            "watch_min_source_authority_ratio",
            "pass_min_evidence_freshness_score",
            "watch_min_evidence_freshness_score",
            "pass_max_conflict_ratio",
            "watch_max_conflict_ratio",
            "coverage_gap_weight",
            "authority_gap_weight",
            "freshness_gap_weight",
            "conflict_weight",
        )
        raw_ratios = {
            field_name: _require_decimal(field_name, getattr(self, field_name))
            for field_name in ratio_field_names
        }
        for field_name, raw_value in raw_ratios.items():
            if raw_value < _ZERO or raw_value > _ONE:
                raise ValueError(f"{field_name} must be between zero and one")
        if (
            raw_ratios["pass_min_evidence_coverage_ratio"]
            < raw_ratios["watch_min_evidence_coverage_ratio"]
        ):
            raise ValueError("coverage pass threshold must be at least watch threshold")
        if (
            raw_ratios["pass_min_source_authority_ratio"]
            < raw_ratios["watch_min_source_authority_ratio"]
        ):
            raise ValueError("authority pass threshold must be at least watch threshold")
        if (
            raw_ratios["pass_min_evidence_freshness_score"]
            < raw_ratios["watch_min_evidence_freshness_score"]
        ):
            raise ValueError("freshness pass threshold must be at least watch threshold")
        if (
            raw_ratios["watch_max_conflict_ratio"]
            < raw_ratios["pass_max_conflict_ratio"]
        ):
            raise ValueError("conflict watch threshold must be at least pass threshold")
        if (
            raw_ratios["coverage_gap_weight"]
            + raw_ratios["authority_gap_weight"]
            + raw_ratios["freshness_gap_weight"]
            + raw_ratios["conflict_weight"]
            != _ONE
        ):
            raise ValueError("priority weights must sum to one before quantization")
        for field_name in ratio_field_names:
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, raw_ratios[field_name]),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyEventResolutionEvidenceGapInput:
    private_event_ref: str = field(repr=False)
    private_source_refs: tuple[str, ...] = field(repr=False)
    required_evidence_count: Decimal
    verifiable_evidence_count: Decimal
    authoritative_source_count: Decimal
    fresh_source_count: Decimal
    conflicting_source_count: Decimal
    latest_evidence_at: datetime | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyEventResolutionEvidenceGapInput does not support subclassing"
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyEventResolutionEvidenceGapInput:
            raise ValueError(
                "input must be exactly ResearchStrategyEventResolutionEvidenceGapInput"
            )
        object.__setattr__(
            self,
            "private_event_ref",
            _require_canonical_string("private_event_ref", self.private_event_ref),
        )
        object.__setattr__(
            self,
            "private_source_refs",
            _normalize_private_source_refs(self.private_source_refs),
        )
        object.__setattr__(
            self,
            "required_evidence_count",
            _normalize_count(
                "required_evidence_count",
                self.required_evidence_count,
                positive=True,
            ),
        )
        for field_name in (
            "verifiable_evidence_count",
            "authoritative_source_count",
            "fresh_source_count",
            "conflicting_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        source_count = _decimal_count(len(self.private_source_refs))
        if self.verifiable_evidence_count > source_count:
            raise ValueError(
                "verifiable_evidence_count must not exceed private source count"
            )
        for field_name in (
            "authoritative_source_count",
            "fresh_source_count",
            "conflicting_source_count",
        ):
            if getattr(self, field_name) > self.verifiable_evidence_count:
                raise ValueError(
                    f"{field_name} must not exceed verifiable_evidence_count"
                )
        if source_count == _ZERO:
            if self.latest_evidence_at is not None:
                raise ValueError(
                    "latest_evidence_at must be None when source count is zero"
                )
        else:
            if self.latest_evidence_at is None:
                raise ValueError(
                    "latest_evidence_at is required when source count is positive"
                )
            object.__setattr__(
                self,
                "latest_evidence_at",
                _as_utc("latest_evidence_at", self.latest_evidence_at),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyEventResolutionEvidenceGapRow:
    public_row_id: str
    manual_review_rank: Decimal
    source_count: Decimal
    required_evidence_count: Decimal
    verifiable_evidence_count: Decimal
    authoritative_source_count: Decimal
    fresh_source_count: Decimal
    conflicting_source_count: Decimal
    latest_evidence_at: datetime | None
    latest_evidence_age_hours: Decimal | None
    evidence_coverage_ratio: Decimal
    source_authority_ratio: Decimal
    fresh_source_ratio: Decimal
    latest_evidence_recency_score: Decimal
    evidence_freshness_score: Decimal
    conflict_ratio: Decimal
    manual_review_priority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyEventResolutionEvidenceGapRow does not support subclassing"
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyEventResolutionEvidenceGapRow:
            raise ValueError(
                "row must be exactly ResearchStrategyEventResolutionEvidenceGapRow"
            )
        if (
            type(self.public_row_id) is not str
            or not _PUBLIC_ROW_ID_PATTERN.fullmatch(self.public_row_id)
        ):
            raise ValueError("public_row_id must be canonical")
        object.__setattr__(
            self,
            "manual_review_rank",
            _normalize_count("manual_review_rank", self.manual_review_rank, positive=True),
        )
        for field_name in (
            "source_count",
            "required_evidence_count",
            "verifiable_evidence_count",
            "authoritative_source_count",
            "fresh_source_count",
            "conflicting_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(
                    field_name,
                    getattr(self, field_name),
                    positive=field_name == "required_evidence_count",
                ),
            )
        if self.source_count == _ZERO:
            if self.latest_evidence_at is not None:
                raise ValueError(
                    "latest_evidence_at must be None when source_count is zero"
                )
            if self.latest_evidence_age_hours is not None:
                raise ValueError(
                    "latest_evidence_age_hours must be None when source_count is zero"
                )
        else:
            if self.latest_evidence_at is None:
                raise ValueError(
                    "latest_evidence_at is required when source_count is positive"
                )
            if self.latest_evidence_age_hours is None:
                raise ValueError(
                    "latest_evidence_age_hours is required when source_count is positive"
                )
            object.__setattr__(
                self,
                "latest_evidence_at",
                _as_utc("latest_evidence_at", self.latest_evidence_at),
            )
            object.__setattr__(
                self,
                "latest_evidence_age_hours",
                _normalize_nonnegative_decimal(
                    "latest_evidence_age_hours",
                    self.latest_evidence_age_hours,
                ),
            )
        for field_name in (
            "evidence_coverage_ratio",
            "source_authority_ratio",
            "fresh_source_ratio",
            "latest_evidence_recency_score",
            "evidence_freshness_score",
            "conflict_ratio",
            "manual_review_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "status",
            _require_status(self.status),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchStrategyEventResolutionEvidenceGapReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyEventResolutionEvidenceGapReasonCodeCount "
            "does not support subclassing"
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyEventResolutionEvidenceGapReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "ResearchStrategyEventResolutionEvidenceGapReasonCodeCount"
            )
        if (
            type(self.reason_code) is not str
            or not _REASON_CODE_PATTERN.fullmatch(self.reason_code)
        ):
            raise ValueError("reason_code must be canonical")
        object.__setattr__(
            self,
            "count",
            _normalize_count("count", self.count, positive=True),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _normalize_ratio("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class ResearchStrategyEventResolutionEvidenceGapReport:
    generated_at: datetime
    config: ResearchStrategyEventResolutionEvidenceGapConfig
    status: str
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    review_required_count: Decimal
    average_evidence_coverage_ratio: Decimal
    average_source_authority_ratio: Decimal
    average_evidence_freshness_score: Decimal
    average_conflict_ratio: Decimal
    average_manual_review_priority_score: Decimal
    max_manual_review_priority_score: Decimal
    total_conflicting_source_count: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchStrategyEventResolutionEvidenceGapReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchStrategyEventResolutionEvidenceGapRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyEventResolutionEvidenceGapReport does not support subclassing"
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyEventResolutionEvidenceGapReport:
            raise ValueError(
                "report must be exactly ResearchStrategyEventResolutionEvidenceGapReport"
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        if type(self.config) is not ResearchStrategyEventResolutionEvidenceGapConfig:
            raise ValueError(
                "config must be exactly ResearchStrategyEventResolutionEvidenceGapConfig"
            )
        _require_canonical_config_instance(self.config)
        object.__setattr__(
            self,
            "status",
            _require_status(self.status, allow_no_inputs=True),
        )
        for field_name in (
            "event_count",
            "pass_count",
            "watch_count",
            "block_count",
            "review_required_count",
            "total_conflicting_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_evidence_coverage_ratio",
            "average_source_authority_ratio",
            "average_evidence_freshness_score",
            "average_conflict_ratio",
            "average_manual_review_priority_score",
            "max_manual_review_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        if type(self.reason_code_counts) is not tuple or any(
            type(item)
            is not ResearchStrategyEventResolutionEvidenceGapReasonCodeCount
            for item in self.reason_code_counts
        ):
            raise ValueError("reason_code_counts must contain exact reason count types")
        for reason_count in self.reason_code_counts:
            _require_canonical_reason_count_instance(reason_count)
        if type(self.rows) is not tuple or any(
            type(item) is not ResearchStrategyEventResolutionEvidenceGapRow
            for item in self.rows
        ):
            raise ValueError("rows must contain exact row types")
        for row in self.rows:
            _require_canonical_row_instance(row)
        _require_hard_flags("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                research_strategy_event_resolution_evidence_gap_report_digest(self),
            )
        if (
            type(self.derived_validation_digest) is not str
            or not re.fullmatch(r"[0-9a-f]{64}", self.derived_validation_digest)
        ):
            raise ValueError("derived_validation_digest must be a SHA-256 digest")
        _validate_report_consistency(self)
        expected_digest = (
            research_strategy_event_resolution_evidence_gap_report_digest(self)
        )
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def config_version(self) -> str:
        return self.config.config_version

    @property
    def payload(self) -> dict[str, Any]:
        return research_strategy_event_resolution_evidence_gap_report_payload(self)


def _row_status(
    *,
    coverage_ratio: Decimal,
    authority_ratio: Decimal,
    freshness_score: Decimal,
    conflict_ratio: Decimal,
    config: ResearchStrategyEventResolutionEvidenceGapConfig,
) -> str:
    if (
        coverage_ratio < config.watch_min_evidence_coverage_ratio
        or authority_ratio < config.watch_min_source_authority_ratio
        or freshness_score < config.watch_min_evidence_freshness_score
        or conflict_ratio > config.watch_max_conflict_ratio
    ):
        return "block"
    if (
        coverage_ratio < config.pass_min_evidence_coverage_ratio
        or authority_ratio < config.pass_min_source_authority_ratio
        or freshness_score < config.pass_min_evidence_freshness_score
        or conflict_ratio > config.pass_max_conflict_ratio
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    coverage_ratio: Decimal,
    authority_ratio: Decimal,
    freshness_score: Decimal,
    conflict_ratio: Decimal,
    config: ResearchStrategyEventResolutionEvidenceGapConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if coverage_ratio < config.watch_min_evidence_coverage_ratio:
        reasons.append("verifiable_evidence_coverage_block")
    elif coverage_ratio < config.pass_min_evidence_coverage_ratio:
        reasons.append("verifiable_evidence_coverage_watch")
    if authority_ratio < config.watch_min_source_authority_ratio:
        reasons.append("source_authority_block")
    elif authority_ratio < config.pass_min_source_authority_ratio:
        reasons.append("source_authority_watch")
    if freshness_score < config.watch_min_evidence_freshness_score:
        reasons.append("evidence_freshness_block")
    elif freshness_score < config.pass_min_evidence_freshness_score:
        reasons.append("evidence_freshness_watch")
    if conflict_ratio > config.watch_max_conflict_ratio:
        reasons.append("source_conflict_block")
    elif conflict_ratio > config.pass_max_conflict_ratio:
        reasons.append("source_conflict_watch")
    if not reasons:
        reasons.append("event_resolution_evidence_sufficient")
    return tuple(reasons)


def _priority_score(
    *,
    coverage_ratio: Decimal,
    authority_ratio: Decimal,
    freshness_score: Decimal,
    conflict_ratio: Decimal,
    config: ResearchStrategyEventResolutionEvidenceGapConfig,
) -> Decimal:
    with localcontext() as context:
        context.prec = 50
        raw = (
            (_ONE - coverage_ratio) * config.coverage_gap_weight
            + (_ONE - authority_ratio) * config.authority_gap_weight
            + (_ONE - freshness_score) * config.freshness_gap_weight
            + conflict_ratio * config.conflict_weight
        )
    return _normalize_ratio("manual_review_priority_score", raw)


def _assert_derived(field_name: str, actual: object, expected: object) -> None:
    if actual != expected:
        raise ValueError(f"{field_name} does not match derived value")


def _datetime_signature(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _config_canonical_signature(
    config: ResearchStrategyEventResolutionEvidenceGapConfig,
) -> tuple[object, ...]:
    return (
        config.config_version,
        str(config.freshness_target_hours),
        str(config.pass_min_evidence_coverage_ratio),
        str(config.watch_min_evidence_coverage_ratio),
        str(config.pass_min_source_authority_ratio),
        str(config.watch_min_source_authority_ratio),
        str(config.pass_min_evidence_freshness_score),
        str(config.watch_min_evidence_freshness_score),
        str(config.pass_max_conflict_ratio),
        str(config.watch_max_conflict_ratio),
        str(config.coverage_gap_weight),
        str(config.authority_gap_weight),
        str(config.freshness_gap_weight),
        str(config.conflict_weight),
        config.paper_only,
        config.report_only,
        config.readonly,
    )


def _require_canonical_config_instance(
    config: object,
) -> ResearchStrategyEventResolutionEvidenceGapConfig:
    if type(config) is not ResearchStrategyEventResolutionEvidenceGapConfig:
        raise ValueError(
            "config must be exactly ResearchStrategyEventResolutionEvidenceGapConfig"
        )
    rebuilt = ResearchStrategyEventResolutionEvidenceGapConfig(
        config_version=config.config_version,
        freshness_target_hours=config.freshness_target_hours,
        pass_min_evidence_coverage_ratio=config.pass_min_evidence_coverage_ratio,
        watch_min_evidence_coverage_ratio=config.watch_min_evidence_coverage_ratio,
        pass_min_source_authority_ratio=config.pass_min_source_authority_ratio,
        watch_min_source_authority_ratio=config.watch_min_source_authority_ratio,
        pass_min_evidence_freshness_score=config.pass_min_evidence_freshness_score,
        watch_min_evidence_freshness_score=config.watch_min_evidence_freshness_score,
        pass_max_conflict_ratio=config.pass_max_conflict_ratio,
        watch_max_conflict_ratio=config.watch_max_conflict_ratio,
        coverage_gap_weight=config.coverage_gap_weight,
        authority_gap_weight=config.authority_gap_weight,
        freshness_gap_weight=config.freshness_gap_weight,
        conflict_weight=config.conflict_weight,
        paper_only=config.paper_only,
        report_only=config.report_only,
        readonly=config.readonly,
    )
    if _config_canonical_signature(config) != _config_canonical_signature(rebuilt):
        raise ValueError("config must match canonical validation")
    return config


def _input_canonical_signature(
    item: ResearchStrategyEventResolutionEvidenceGapInput,
) -> tuple[object, ...]:
    return (
        item.private_event_ref,
        item.private_source_refs,
        str(item.required_evidence_count),
        str(item.verifiable_evidence_count),
        str(item.authoritative_source_count),
        str(item.fresh_source_count),
        str(item.conflicting_source_count),
        _datetime_signature(item.latest_evidence_at),
        item.paper_only,
        item.report_only,
        item.readonly,
    )


def _require_canonical_input_instance(
    item: object,
) -> ResearchStrategyEventResolutionEvidenceGapInput:
    if type(item) is not ResearchStrategyEventResolutionEvidenceGapInput:
        raise ValueError("inputs must contain exact input types")
    rebuilt = ResearchStrategyEventResolutionEvidenceGapInput(
        private_event_ref=item.private_event_ref,
        private_source_refs=item.private_source_refs,
        required_evidence_count=item.required_evidence_count,
        verifiable_evidence_count=item.verifiable_evidence_count,
        authoritative_source_count=item.authoritative_source_count,
        fresh_source_count=item.fresh_source_count,
        conflicting_source_count=item.conflicting_source_count,
        latest_evidence_at=item.latest_evidence_at,
        paper_only=item.paper_only,
        report_only=item.report_only,
        readonly=item.readonly,
    )
    if _input_canonical_signature(item) != _input_canonical_signature(rebuilt):
        raise ValueError("input must match canonical validation")
    return item


def _row_canonical_signature(
    row: ResearchStrategyEventResolutionEvidenceGapRow,
) -> tuple[object, ...]:
    return (
        row.public_row_id,
        str(row.manual_review_rank),
        str(row.source_count),
        str(row.required_evidence_count),
        str(row.verifiable_evidence_count),
        str(row.authoritative_source_count),
        str(row.fresh_source_count),
        str(row.conflicting_source_count),
        _datetime_signature(row.latest_evidence_at),
        None
        if row.latest_evidence_age_hours is None
        else str(row.latest_evidence_age_hours),
        str(row.evidence_coverage_ratio),
        str(row.source_authority_ratio),
        str(row.fresh_source_ratio),
        str(row.latest_evidence_recency_score),
        str(row.evidence_freshness_score),
        str(row.conflict_ratio),
        str(row.manual_review_priority_score),
        row.status,
        row.reason_codes,
        row.paper_only,
        row.report_only,
        row.readonly,
    )


def _require_canonical_row_instance(
    row: object,
) -> ResearchStrategyEventResolutionEvidenceGapRow:
    if type(row) is not ResearchStrategyEventResolutionEvidenceGapRow:
        raise ValueError("rows must contain exact row types")
    rebuilt = ResearchStrategyEventResolutionEvidenceGapRow(
        public_row_id=row.public_row_id,
        manual_review_rank=row.manual_review_rank,
        source_count=row.source_count,
        required_evidence_count=row.required_evidence_count,
        verifiable_evidence_count=row.verifiable_evidence_count,
        authoritative_source_count=row.authoritative_source_count,
        fresh_source_count=row.fresh_source_count,
        conflicting_source_count=row.conflicting_source_count,
        latest_evidence_at=row.latest_evidence_at,
        latest_evidence_age_hours=row.latest_evidence_age_hours,
        evidence_coverage_ratio=row.evidence_coverage_ratio,
        source_authority_ratio=row.source_authority_ratio,
        fresh_source_ratio=row.fresh_source_ratio,
        latest_evidence_recency_score=row.latest_evidence_recency_score,
        evidence_freshness_score=row.evidence_freshness_score,
        conflict_ratio=row.conflict_ratio,
        manual_review_priority_score=row.manual_review_priority_score,
        status=row.status,
        reason_codes=row.reason_codes,
        paper_only=row.paper_only,
        report_only=row.report_only,
        readonly=row.readonly,
    )
    if _row_canonical_signature(row) != _row_canonical_signature(rebuilt):
        raise ValueError("row must match canonical validation")
    return row


def _reason_count_canonical_signature(
    reason_count: ResearchStrategyEventResolutionEvidenceGapReasonCodeCount,
) -> tuple[object, ...]:
    return (
        reason_count.reason_code,
        str(reason_count.count),
        str(reason_count.row_ratio),
        reason_count.paper_only,
        reason_count.report_only,
        reason_count.readonly,
    )


def _require_canonical_reason_count_instance(
    reason_count: object,
) -> ResearchStrategyEventResolutionEvidenceGapReasonCodeCount:
    if type(reason_count) is not ResearchStrategyEventResolutionEvidenceGapReasonCodeCount:
        raise ValueError("reason_code_counts must contain exact reason count types")
    rebuilt = ResearchStrategyEventResolutionEvidenceGapReasonCodeCount(
        reason_code=reason_count.reason_code,
        count=reason_count.count,
        row_ratio=reason_count.row_ratio,
        paper_only=reason_count.paper_only,
        report_only=reason_count.report_only,
        readonly=reason_count.readonly,
    )
    if _reason_count_canonical_signature(
        reason_count
    ) != _reason_count_canonical_signature(rebuilt):
        raise ValueError("reason count must match canonical validation")
    return reason_count


def _decimal_order_value(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} order value must be a Decimal")
    return value


def _optional_decimal_order_value(
    field_name: str,
    value: object,
) -> tuple[int, Decimal]:
    if value is None:
        return (0, _ZERO)
    return (1, _decimal_order_value(field_name, value))


def _optional_datetime_order_value(
    field_name: str,
    value: object,
) -> tuple[int, str]:
    if value is None:
        return (0, "")
    if type(value) is not datetime:
        raise ValueError(f"{field_name} order value must be a datetime")
    return (1, value.isoformat())


def _reason_codes_order_value(value: object) -> tuple[str, ...]:
    if type(value) is not tuple or any(type(item) is not str for item in value):
        raise ValueError("reason_codes order value must be a tuple of strings")
    return value


def _draft_row_order_key(
    private_event_ref: str,
    values: dict[str, object],
) -> tuple[object, ...]:
    status = str(values["status"])
    return (
        _STATUS_ORDER[status],
        -_decimal_order_value(
            "manual_review_priority_score",
            values["manual_review_priority_score"],
        ),
        _decimal_order_value("source_count", values["source_count"]),
        _decimal_order_value(
            "required_evidence_count",
            values["required_evidence_count"],
        ),
        _decimal_order_value(
            "verifiable_evidence_count",
            values["verifiable_evidence_count"],
        ),
        _decimal_order_value(
            "authoritative_source_count",
            values["authoritative_source_count"],
        ),
        _decimal_order_value("fresh_source_count", values["fresh_source_count"]),
        _decimal_order_value(
            "conflicting_source_count",
            values["conflicting_source_count"],
        ),
        _optional_datetime_order_value(
            "latest_evidence_at",
            values["latest_evidence_at"],
        ),
        _optional_decimal_order_value(
            "latest_evidence_age_hours",
            values["latest_evidence_age_hours"],
        ),
        _decimal_order_value(
            "evidence_coverage_ratio",
            values["evidence_coverage_ratio"],
        ),
        _decimal_order_value(
            "source_authority_ratio",
            values["source_authority_ratio"],
        ),
        _decimal_order_value("fresh_source_ratio", values["fresh_source_ratio"]),
        _decimal_order_value(
            "latest_evidence_recency_score",
            values["latest_evidence_recency_score"],
        ),
        _decimal_order_value(
            "evidence_freshness_score",
            values["evidence_freshness_score"],
        ),
        _decimal_order_value("conflict_ratio", values["conflict_ratio"]),
        _reason_codes_order_value(values["reason_codes"]),
        private_event_ref,
    )


def _row_public_order_key(
    row: ResearchStrategyEventResolutionEvidenceGapRow,
) -> tuple[object, ...]:
    return (
        _STATUS_ORDER[row.status],
        -row.manual_review_priority_score,
        row.source_count,
        row.required_evidence_count,
        row.verifiable_evidence_count,
        row.authoritative_source_count,
        row.fresh_source_count,
        row.conflicting_source_count,
        _optional_datetime_order_value(
            "latest_evidence_at",
            row.latest_evidence_at,
        ),
        _optional_decimal_order_value(
            "latest_evidence_age_hours",
            row.latest_evidence_age_hours,
        ),
        row.evidence_coverage_ratio,
        row.source_authority_ratio,
        row.fresh_source_ratio,
        row.latest_evidence_recency_score,
        row.evidence_freshness_score,
        row.conflict_ratio,
        row.reason_codes,
        row.public_row_id,
    )


def _validate_row_consistency(
    row: ResearchStrategyEventResolutionEvidenceGapRow,
    *,
    generated_at: datetime,
    config: ResearchStrategyEventResolutionEvidenceGapConfig,
    expected_index: int,
) -> None:
    expected_rank = _decimal_count(expected_index)
    _assert_derived("manual_review_rank", row.manual_review_rank, expected_rank)
    _assert_derived(
        "public_row_id",
        row.public_row_id,
        f"event_resolution_evidence_gap_{expected_index:06d}",
    )
    if row.verifiable_evidence_count > row.source_count:
        raise ValueError("verifiable_evidence_count must not exceed source_count")
    for field_name in (
        "authoritative_source_count",
        "fresh_source_count",
        "conflicting_source_count",
    ):
        if getattr(row, field_name) > row.verifiable_evidence_count:
            raise ValueError(
                f"{field_name} must not exceed verifiable_evidence_count"
            )
    if row.source_count == _ZERO:
        if row.latest_evidence_at is not None:
            raise ValueError(
                "latest_evidence_at must be None when source_count is zero"
            )
        if row.latest_evidence_age_hours is not None:
            raise ValueError(
                "latest_evidence_age_hours must be None when source_count is zero"
            )
        raw_age: Decimal | None = None
        expected_age: Decimal | None = None
    else:
        if row.latest_evidence_at is None:
            raise ValueError(
                "latest_evidence_at is required when source_count is positive"
            )
        if row.latest_evidence_at > generated_at:
            raise ValueError("latest_evidence_at must not be after generated_at")
        raw_age = _raw_age_hours(generated_at, row.latest_evidence_at)
        expected_age = _normalize_nonnegative_decimal(
            "latest_evidence_age_hours",
            raw_age,
        )
    raw_coverage = min(
        _ONE,
        _raw_ratio(
            row.verifiable_evidence_count,
            row.required_evidence_count,
        ),
    )
    expected_coverage = _normalize_ratio(
        "evidence_coverage_ratio",
        raw_coverage,
    )
    raw_authority = _raw_ratio(
        row.authoritative_source_count,
        row.verifiable_evidence_count,
    )
    expected_authority = _normalize_ratio(
        "source_authority_ratio",
        raw_authority,
    )
    raw_fresh_source_ratio = _raw_ratio(
        row.fresh_source_count,
        row.verifiable_evidence_count,
    )
    expected_fresh_source_ratio = _normalize_ratio(
        "fresh_source_ratio",
        raw_fresh_source_ratio,
    )
    raw_recency = (
        _ZERO
        if raw_age is None
        else max(
            _ZERO,
            _ONE - raw_age / config.freshness_target_hours,
        )
    )
    expected_recency = _normalize_ratio(
        "latest_evidence_recency_score",
        raw_recency,
    )
    raw_freshness = min(raw_fresh_source_ratio, raw_recency)
    expected_freshness = _normalize_ratio(
        "evidence_freshness_score",
        raw_freshness,
    )
    raw_conflict = _raw_ratio(
        row.conflicting_source_count,
        row.verifiable_evidence_count,
    )
    expected_conflict = _normalize_ratio("conflict_ratio", raw_conflict)
    expected_status = _row_status(
        coverage_ratio=raw_coverage,
        authority_ratio=raw_authority,
        freshness_score=raw_freshness,
        conflict_ratio=raw_conflict,
        config=config,
    )
    expected_reasons = _row_reason_codes(
        coverage_ratio=raw_coverage,
        authority_ratio=raw_authority,
        freshness_score=raw_freshness,
        conflict_ratio=raw_conflict,
        config=config,
    )
    expected_score = _priority_score(
        coverage_ratio=raw_coverage,
        authority_ratio=raw_authority,
        freshness_score=raw_freshness,
        conflict_ratio=raw_conflict,
        config=config,
    )
    for field_name, expected in (
        ("latest_evidence_age_hours", expected_age),
        ("evidence_coverage_ratio", expected_coverage),
        ("source_authority_ratio", expected_authority),
        ("fresh_source_ratio", expected_fresh_source_ratio),
        ("latest_evidence_recency_score", expected_recency),
        ("evidence_freshness_score", expected_freshness),
        ("conflict_ratio", expected_conflict),
        ("manual_review_priority_score", expected_score),
        ("status", expected_status),
        ("reason_codes", expected_reasons),
    ):
        _assert_derived(field_name, getattr(row, field_name), expected)


def _report_status(rows: tuple[ResearchStrategyEventResolutionEvidenceGapRow, ...]) -> str:
    if not rows:
        return "no_inputs"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyEventResolutionEvidenceGapRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("event_resolution_evidence_gap_no_inputs",)
    reasons = [
        {
            "block": "event_resolution_evidence_gap_blocked",
            "watch": "event_resolution_evidence_gap_watch",
            "pass": "event_resolution_evidence_gap_passed",
        }[_report_status(rows)]
    ]
    row_reasons = {reason for row in rows for reason in row.reason_codes}
    if any(reason.startswith("verifiable_evidence_coverage_") for reason in row_reasons):
        reasons.append("verifiable_evidence_coverage_gap_detected")
    if any(reason.startswith("source_authority_") for reason in row_reasons):
        reasons.append("source_authority_gap_detected")
    if any(reason.startswith("evidence_freshness_") for reason in row_reasons):
        reasons.append("evidence_freshness_gap_detected")
    if any(reason.startswith("source_conflict_") for reason in row_reasons):
        reasons.append("source_conflict_detected")
    return tuple(reasons)


def _reason_code_counts(
    rows: tuple[ResearchStrategyEventResolutionEvidenceGapRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchStrategyEventResolutionEvidenceGapReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyEventResolutionEvidenceGapReasonCodeCount(
                reason_code=reason_codes[0],
                count=_decimal_count(1),
                row_ratio=_quantize("row_ratio", _ZERO),
            ),
        )
    counts: list[ResearchStrategyEventResolutionEvidenceGapReasonCodeCount] = []
    for reason_code in reason_codes:
        if reason_code == "event_resolution_evidence_gap_blocked":
            count = sum(row.status == "block" for row in rows)
        elif reason_code == "event_resolution_evidence_gap_watch":
            count = sum(row.status == "watch" for row in rows)
        elif reason_code == "event_resolution_evidence_gap_passed":
            count = sum(row.status == "pass" for row in rows)
        elif reason_code == "verifiable_evidence_coverage_gap_detected":
            count = sum(
                any(
                    reason.startswith("verifiable_evidence_coverage_")
                    for reason in row.reason_codes
                )
                for row in rows
            )
        elif reason_code == "source_authority_gap_detected":
            count = sum(
                any(reason.startswith("source_authority_") for reason in row.reason_codes)
                for row in rows
            )
        elif reason_code == "evidence_freshness_gap_detected":
            count = sum(
                any(reason.startswith("evidence_freshness_") for reason in row.reason_codes)
                for row in rows
            )
        else:
            count = sum(
                any(reason.startswith("source_conflict_") for reason in row.reason_codes)
                for row in rows
            )
        counts.append(
            ResearchStrategyEventResolutionEvidenceGapReasonCodeCount(
                reason_code=reason_code,
                count=_decimal_count(count),
                row_ratio=_ratio(Decimal(count), Decimal(len(rows))),
            )
        )
    return tuple(counts)


def _validate_report_consistency(
    report: ResearchStrategyEventResolutionEvidenceGapReport,
) -> None:
    for index, row in enumerate(report.rows, start=1):
        _validate_row_consistency(
            row,
            generated_at=report.generated_at,
            config=report.config,
            expected_index=index,
        )
    expected_order = tuple(
        sorted(
            report.rows,
            key=_row_public_order_key,
        )
    )
    _assert_derived("rows", report.rows, expected_order)

    pass_count = sum(row.status == "pass" for row in report.rows)
    watch_count = sum(row.status == "watch" for row in report.rows)
    block_count = sum(row.status == "block" for row in report.rows)
    scores = tuple(row.manual_review_priority_score for row in report.rows)
    expected_reason_codes = _report_reason_codes(report.rows)
    expected_reason_code_counts = _reason_code_counts(
        report.rows,
        expected_reason_codes,
    )
    expected_values: tuple[tuple[str, object], ...] = (
        ("status", _report_status(report.rows)),
        ("event_count", _decimal_count(len(report.rows))),
        ("pass_count", _decimal_count(pass_count)),
        ("watch_count", _decimal_count(watch_count)),
        ("block_count", _decimal_count(block_count)),
        (
            "review_required_count",
            _decimal_count(watch_count + block_count),
        ),
        (
            "average_evidence_coverage_ratio",
            _average(tuple(row.evidence_coverage_ratio for row in report.rows)),
        ),
        (
            "average_source_authority_ratio",
            _average(tuple(row.source_authority_ratio for row in report.rows)),
        ),
        (
            "average_evidence_freshness_score",
            _average(tuple(row.evidence_freshness_score for row in report.rows)),
        ),
        (
            "average_conflict_ratio",
            _average(tuple(row.conflict_ratio for row in report.rows)),
        ),
        (
            "average_manual_review_priority_score",
            _average(scores),
        ),
        (
            "max_manual_review_priority_score",
            max(
                scores,
                default=_quantize("max_manual_review_priority_score", _ZERO),
            ),
        ),
        (
            "total_conflicting_source_count",
            sum(
                (row.conflicting_source_count for row in report.rows),
                _quantize("total_conflicting_source_count", _ZERO),
            ),
        ),
        ("reason_codes", expected_reason_codes),
        ("reason_code_counts", expected_reason_code_counts),
    )
    for field_name, expected in expected_values:
        _assert_derived(field_name, getattr(report, field_name), expected)


def build_research_strategy_event_resolution_evidence_gap_report(
    inputs: list[ResearchStrategyEventResolutionEvidenceGapInput]
    | tuple[ResearchStrategyEventResolutionEvidenceGapInput, ...],
    *,
    config: ResearchStrategyEventResolutionEvidenceGapConfig,
    generated_at: datetime,
) -> ResearchStrategyEventResolutionEvidenceGapReport:
    if type(config) is not ResearchStrategyEventResolutionEvidenceGapConfig:
        raise ValueError(
            "config must be exactly ResearchStrategyEventResolutionEvidenceGapConfig"
        )
    _require_canonical_config_instance(config)
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    normalized_inputs = tuple(inputs)
    if any(
        type(item) is not ResearchStrategyEventResolutionEvidenceGapInput
        for item in normalized_inputs
    ):
        raise ValueError("inputs must contain exact input types")
    for item in normalized_inputs:
        _require_canonical_input_instance(item)
    generated_at_utc = _as_utc("generated_at", generated_at)
    private_event_refs = tuple(item.private_event_ref for item in normalized_inputs)
    if len(private_event_refs) != len(set(private_event_refs)):
        raise ValueError("private_event_ref values must be unique")

    draft_rows: list[tuple[str, dict[str, object]]] = []
    for item in normalized_inputs:
        source_count = _decimal_count(len(item.private_source_refs))
        raw_coverage_ratio = min(
            _ONE,
            _raw_ratio(
                item.verifiable_evidence_count,
                item.required_evidence_count,
            ),
        )
        coverage_ratio = _normalize_ratio(
            "evidence_coverage_ratio",
            raw_coverage_ratio,
        )
        raw_authority_ratio = _raw_ratio(
            item.authoritative_source_count,
            item.verifiable_evidence_count,
        )
        authority_ratio = _normalize_ratio(
            "source_authority_ratio",
            raw_authority_ratio,
        )
        raw_fresh_source_ratio = _raw_ratio(
            item.fresh_source_count,
            item.verifiable_evidence_count,
        )
        fresh_source_ratio = _normalize_ratio(
            "fresh_source_ratio",
            raw_fresh_source_ratio,
        )
        if item.latest_evidence_at is None:
            raw_latest_evidence_age_hours: Decimal | None = None
            latest_evidence_age_hours: Decimal | None = None
            recency_raw = _ZERO
        else:
            if item.latest_evidence_at > generated_at_utc:
                raise ValueError("latest_evidence_at must not be after generated_at")
            raw_latest_evidence_age_hours = _raw_age_hours(
                generated_at_utc,
                item.latest_evidence_at,
            )
            latest_evidence_age_hours = _normalize_nonnegative_decimal(
                "latest_evidence_age_hours",
                raw_latest_evidence_age_hours,
            )
            recency_raw = max(
                _ZERO,
                _ONE
                - raw_latest_evidence_age_hours / config.freshness_target_hours,
            )
        recency_score = _normalize_ratio(
            "latest_evidence_recency_score",
            recency_raw,
        )
        raw_freshness_score = min(raw_fresh_source_ratio, recency_raw)
        freshness_score = _normalize_ratio(
            "evidence_freshness_score",
            raw_freshness_score,
        )
        raw_conflict_ratio = _raw_ratio(
            item.conflicting_source_count,
            item.verifiable_evidence_count,
        )
        conflict_ratio = _normalize_ratio("conflict_ratio", raw_conflict_ratio)
        status = _row_status(
            coverage_ratio=raw_coverage_ratio,
            authority_ratio=raw_authority_ratio,
            freshness_score=raw_freshness_score,
            conflict_ratio=raw_conflict_ratio,
            config=config,
        )
        reason_codes = _row_reason_codes(
            coverage_ratio=raw_coverage_ratio,
            authority_ratio=raw_authority_ratio,
            freshness_score=raw_freshness_score,
            conflict_ratio=raw_conflict_ratio,
            config=config,
        )
        priority_score = _priority_score(
            coverage_ratio=raw_coverage_ratio,
            authority_ratio=raw_authority_ratio,
            freshness_score=raw_freshness_score,
            conflict_ratio=raw_conflict_ratio,
            config=config,
        )
        draft_rows.append(
            (
                item.private_event_ref,
                {
                    "source_count": source_count,
                    "required_evidence_count": item.required_evidence_count,
                    "verifiable_evidence_count": item.verifiable_evidence_count,
                    "authoritative_source_count": item.authoritative_source_count,
                    "fresh_source_count": item.fresh_source_count,
                    "conflicting_source_count": item.conflicting_source_count,
                    "latest_evidence_at": item.latest_evidence_at,
                    "latest_evidence_age_hours": latest_evidence_age_hours,
                    "evidence_coverage_ratio": coverage_ratio,
                    "source_authority_ratio": authority_ratio,
                    "fresh_source_ratio": fresh_source_ratio,
                    "latest_evidence_recency_score": recency_score,
                    "evidence_freshness_score": freshness_score,
                    "conflict_ratio": conflict_ratio,
                    "manual_review_priority_score": priority_score,
                    "status": status,
                    "reason_codes": reason_codes,
                },
            )
        )
    draft_rows.sort(
        key=lambda item: _draft_row_order_key(item[0], item[1])
    )
    rows = tuple(
        ResearchStrategyEventResolutionEvidenceGapRow(
            public_row_id=f"event_resolution_evidence_gap_{index:06d}",
            manual_review_rank=_decimal_count(index),
            **values,
        )
        for index, (_, values) in enumerate(draft_rows, start=1)
    )
    reason_codes = _report_reason_codes(rows)
    pass_count = sum(row.status == "pass" for row in rows)
    watch_count = sum(row.status == "watch" for row in rows)
    block_count = sum(row.status == "block" for row in rows)
    scores = tuple(row.manual_review_priority_score for row in rows)

    return ResearchStrategyEventResolutionEvidenceGapReport(
        generated_at=generated_at_utc,
        config=config,
        status=_report_status(rows),
        event_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(pass_count),
        watch_count=_decimal_count(watch_count),
        block_count=_decimal_count(block_count),
        review_required_count=_decimal_count(watch_count + block_count),
        average_evidence_coverage_ratio=_average(
            tuple(row.evidence_coverage_ratio for row in rows)
        ),
        average_source_authority_ratio=_average(
            tuple(row.source_authority_ratio for row in rows)
        ),
        average_evidence_freshness_score=_average(
            tuple(row.evidence_freshness_score for row in rows)
        ),
        average_conflict_ratio=_average(tuple(row.conflict_ratio for row in rows)),
        average_manual_review_priority_score=_average(scores),
        max_manual_review_priority_score=max(
            scores,
            default=_quantize("max_manual_review_priority_score", _ZERO),
        ),
        total_conflicting_source_count=sum(
            (row.conflicting_source_count for row in rows),
            _quantize("total_conflicting_source_count", _ZERO),
        ),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        rows=rows,
    )


def _config_payload(
    config: ResearchStrategyEventResolutionEvidenceGapConfig,
) -> dict[str, object]:
    return {
        "config_version": config.config_version,
        "freshness_target_hours": str(config.freshness_target_hours),
        "pass_min_evidence_coverage_ratio": str(
            config.pass_min_evidence_coverage_ratio
        ),
        "watch_min_evidence_coverage_ratio": str(
            config.watch_min_evidence_coverage_ratio
        ),
        "pass_min_source_authority_ratio": str(
            config.pass_min_source_authority_ratio
        ),
        "watch_min_source_authority_ratio": str(
            config.watch_min_source_authority_ratio
        ),
        "pass_min_evidence_freshness_score": str(
            config.pass_min_evidence_freshness_score
        ),
        "watch_min_evidence_freshness_score": str(
            config.watch_min_evidence_freshness_score
        ),
        "pass_max_conflict_ratio": str(config.pass_max_conflict_ratio),
        "watch_max_conflict_ratio": str(config.watch_max_conflict_ratio),
        "coverage_gap_weight": str(config.coverage_gap_weight),
        "authority_gap_weight": str(config.authority_gap_weight),
        "freshness_gap_weight": str(config.freshness_gap_weight),
        "conflict_weight": str(config.conflict_weight),
        "paper_only": config.paper_only,
        "report_only": config.report_only,
        "readonly": config.readonly,
    }


def _row_payload(
    row: ResearchStrategyEventResolutionEvidenceGapRow,
) -> dict[str, object]:
    return {
        "public_row_id": row.public_row_id,
        "manual_review_rank": str(row.manual_review_rank),
        "source_count": str(row.source_count),
        "required_evidence_count": str(row.required_evidence_count),
        "verifiable_evidence_count": str(row.verifiable_evidence_count),
        "authoritative_source_count": str(row.authoritative_source_count),
        "fresh_source_count": str(row.fresh_source_count),
        "conflicting_source_count": str(row.conflicting_source_count),
        "latest_evidence_at": (
            None
            if row.latest_evidence_at is None
            else row.latest_evidence_at.isoformat()
        ),
        "latest_evidence_age_hours": (
            None
            if row.latest_evidence_age_hours is None
            else str(row.latest_evidence_age_hours)
        ),
        "evidence_coverage_ratio": str(row.evidence_coverage_ratio),
        "source_authority_ratio": str(row.source_authority_ratio),
        "fresh_source_ratio": str(row.fresh_source_ratio),
        "latest_evidence_recency_score": str(
            row.latest_evidence_recency_score
        ),
        "evidence_freshness_score": str(row.evidence_freshness_score),
        "conflict_ratio": str(row.conflict_ratio),
        "manual_review_priority_score": str(
            row.manual_review_priority_score
        ),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _reason_count_payload(
    reason_count: ResearchStrategyEventResolutionEvidenceGapReasonCodeCount,
) -> dict[str, object]:
    return {
        "reason_code": reason_count.reason_code,
        "count": str(reason_count.count),
        "row_ratio": str(reason_count.row_ratio),
        "paper_only": reason_count.paper_only,
        "report_only": reason_count.report_only,
        "readonly": reason_count.readonly,
    }


def _report_payload_without_digest(
    report: ResearchStrategyEventResolutionEvidenceGapReport,
) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "config": _config_payload(report.config),
        "status": report.status,
        "event_count": str(report.event_count),
        "pass_count": str(report.pass_count),
        "watch_count": str(report.watch_count),
        "block_count": str(report.block_count),
        "review_required_count": str(report.review_required_count),
        "average_evidence_coverage_ratio": str(
            report.average_evidence_coverage_ratio
        ),
        "average_source_authority_ratio": str(
            report.average_source_authority_ratio
        ),
        "average_evidence_freshness_score": str(
            report.average_evidence_freshness_score
        ),
        "average_conflict_ratio": str(report.average_conflict_ratio),
        "average_manual_review_priority_score": str(
            report.average_manual_review_priority_score
        ),
        "max_manual_review_priority_score": str(
            report.max_manual_review_priority_score
        ),
        "total_conflicting_source_count": str(
            report.total_conflicting_source_count
        ),
        "reason_codes": list(report.reason_codes),
        "reason_code_counts": [
            _reason_count_payload(item) for item in report.reason_code_counts
        ],
        "rows": [_row_payload(row) for row in report.rows],
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def research_strategy_event_resolution_evidence_gap_report_digest(
    report: ResearchStrategyEventResolutionEvidenceGapReport | dict[str, Any],
) -> str:
    if type(report) is ResearchStrategyEventResolutionEvidenceGapReport:
        payload = _report_payload_without_digest(report)
    elif type(report) is dict:
        payload_with_digest = _require_exact_keys(
            "report payload",
            report,
            _REPORT_PAYLOAD_KEYS,
        )
        payload = {
            key: value
            for key, value in payload_with_digest.items()
            if key != "derived_validation_digest"
        }
    else:
        raise ValueError(
            "report must be an exact report or exact payload dict"
        )
    canonical = _canonical_json(payload)
    return sha256(canonical.encode("utf-8")).hexdigest()


def research_strategy_event_resolution_evidence_gap_report_payload(
    report: ResearchStrategyEventResolutionEvidenceGapReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is dict:
        report = research_strategy_event_resolution_evidence_gap_report_from_payload(
            report
        )
    if type(report) is not ResearchStrategyEventResolutionEvidenceGapReport:
        raise ValueError(
            "report must be exactly ResearchStrategyEventResolutionEvidenceGapReport"
        )
    _require_hard_flags("report", report)
    _require_canonical_config_instance(report.config)
    for reason_count in report.reason_code_counts:
        _require_canonical_reason_count_instance(reason_count)
    for row in report.rows:
        _require_canonical_row_instance(row)
    _validate_report_consistency(report)
    expected_digest = research_strategy_event_resolution_evidence_gap_report_digest(
        report
    )
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    payload = _report_payload_without_digest(report)
    payload["derived_validation_digest"] = report.derived_validation_digest
    return payload


def _config_from_payload(
    value: object,
) -> ResearchStrategyEventResolutionEvidenceGapConfig:
    payload = _require_exact_keys("config payload", value, _CONFIG_PAYLOAD_KEYS)
    return ResearchStrategyEventResolutionEvidenceGapConfig(
        config_version=_require_config_version(payload["config_version"]),
        freshness_target_hours=_decimal_from_payload(
            "freshness_target_hours",
            payload["freshness_target_hours"],
        ),
        pass_min_evidence_coverage_ratio=_decimal_from_payload(
            "pass_min_evidence_coverage_ratio",
            payload["pass_min_evidence_coverage_ratio"],
        ),
        watch_min_evidence_coverage_ratio=_decimal_from_payload(
            "watch_min_evidence_coverage_ratio",
            payload["watch_min_evidence_coverage_ratio"],
        ),
        pass_min_source_authority_ratio=_decimal_from_payload(
            "pass_min_source_authority_ratio",
            payload["pass_min_source_authority_ratio"],
        ),
        watch_min_source_authority_ratio=_decimal_from_payload(
            "watch_min_source_authority_ratio",
            payload["watch_min_source_authority_ratio"],
        ),
        pass_min_evidence_freshness_score=_decimal_from_payload(
            "pass_min_evidence_freshness_score",
            payload["pass_min_evidence_freshness_score"],
        ),
        watch_min_evidence_freshness_score=_decimal_from_payload(
            "watch_min_evidence_freshness_score",
            payload["watch_min_evidence_freshness_score"],
        ),
        pass_max_conflict_ratio=_decimal_from_payload(
            "pass_max_conflict_ratio",
            payload["pass_max_conflict_ratio"],
        ),
        watch_max_conflict_ratio=_decimal_from_payload(
            "watch_max_conflict_ratio",
            payload["watch_max_conflict_ratio"],
        ),
        coverage_gap_weight=_decimal_from_payload(
            "coverage_gap_weight",
            payload["coverage_gap_weight"],
        ),
        authority_gap_weight=_decimal_from_payload(
            "authority_gap_weight",
            payload["authority_gap_weight"],
        ),
        freshness_gap_weight=_decimal_from_payload(
            "freshness_gap_weight",
            payload["freshness_gap_weight"],
        ),
        conflict_weight=_decimal_from_payload(
            "conflict_weight",
            payload["conflict_weight"],
        ),
        paper_only=_true_from_payload("config.paper_only", payload["paper_only"]),
        report_only=_true_from_payload(
            "config.report_only",
            payload["report_only"],
        ),
        readonly=_true_from_payload("config.readonly", payload["readonly"]),
    )


def _row_from_payload(
    value: object,
) -> ResearchStrategyEventResolutionEvidenceGapRow:
    payload = _require_exact_keys("row payload", value, _ROW_PAYLOAD_KEYS)
    return ResearchStrategyEventResolutionEvidenceGapRow(
        public_row_id=_require_canonical_string(
            "public_row_id",
            payload["public_row_id"],
        ),
        manual_review_rank=_decimal_from_payload(
            "manual_review_rank",
            payload["manual_review_rank"],
        ),
        source_count=_decimal_from_payload("source_count", payload["source_count"]),
        required_evidence_count=_decimal_from_payload(
            "required_evidence_count",
            payload["required_evidence_count"],
        ),
        verifiable_evidence_count=_decimal_from_payload(
            "verifiable_evidence_count",
            payload["verifiable_evidence_count"],
        ),
        authoritative_source_count=_decimal_from_payload(
            "authoritative_source_count",
            payload["authoritative_source_count"],
        ),
        fresh_source_count=_decimal_from_payload(
            "fresh_source_count",
            payload["fresh_source_count"],
        ),
        conflicting_source_count=_decimal_from_payload(
            "conflicting_source_count",
            payload["conflicting_source_count"],
        ),
        latest_evidence_at=_optional_datetime_from_payload(
            "latest_evidence_at",
            payload["latest_evidence_at"],
        ),
        latest_evidence_age_hours=_optional_decimal_from_payload(
            "latest_evidence_age_hours",
            payload["latest_evidence_age_hours"],
        ),
        evidence_coverage_ratio=_decimal_from_payload(
            "evidence_coverage_ratio",
            payload["evidence_coverage_ratio"],
        ),
        source_authority_ratio=_decimal_from_payload(
            "source_authority_ratio",
            payload["source_authority_ratio"],
        ),
        fresh_source_ratio=_decimal_from_payload(
            "fresh_source_ratio",
            payload["fresh_source_ratio"],
        ),
        latest_evidence_recency_score=_decimal_from_payload(
            "latest_evidence_recency_score",
            payload["latest_evidence_recency_score"],
        ),
        evidence_freshness_score=_decimal_from_payload(
            "evidence_freshness_score",
            payload["evidence_freshness_score"],
        ),
        conflict_ratio=_decimal_from_payload(
            "conflict_ratio",
            payload["conflict_ratio"],
        ),
        manual_review_priority_score=_decimal_from_payload(
            "manual_review_priority_score",
            payload["manual_review_priority_score"],
        ),
        status=_require_status(payload["status"]),
        reason_codes=_reason_codes_from_payload(payload["reason_codes"]),
        paper_only=_true_from_payload("row.paper_only", payload["paper_only"]),
        report_only=_true_from_payload("row.report_only", payload["report_only"]),
        readonly=_true_from_payload("row.readonly", payload["readonly"]),
    )


def _reason_count_from_payload(
    value: object,
) -> ResearchStrategyEventResolutionEvidenceGapReasonCodeCount:
    payload = _require_exact_keys(
        "reason count payload",
        value,
        _REASON_COUNT_PAYLOAD_KEYS,
    )
    return ResearchStrategyEventResolutionEvidenceGapReasonCodeCount(
        reason_code=_require_canonical_string(
            "reason_code",
            payload["reason_code"],
        ),
        count=_decimal_from_payload("count", payload["count"]),
        row_ratio=_decimal_from_payload("row_ratio", payload["row_ratio"]),
        paper_only=_true_from_payload(
            "reason_count.paper_only",
            payload["paper_only"],
        ),
        report_only=_true_from_payload(
            "reason_count.report_only",
            payload["report_only"],
        ),
        readonly=_true_from_payload(
            "reason_count.readonly",
            payload["readonly"],
        ),
    )


def research_strategy_event_resolution_evidence_gap_report_from_payload(
    value: object,
) -> ResearchStrategyEventResolutionEvidenceGapReport:
    payload = _require_exact_keys("report payload", value, _REPORT_PAYLOAD_KEYS)
    supplied_digest = payload["derived_validation_digest"]
    if type(supplied_digest) is not str or not re.fullmatch(
        r"[0-9a-f]{64}",
        supplied_digest,
    ):
        raise ValueError("derived_validation_digest must be a SHA-256 digest")
    expected_digest = research_strategy_event_resolution_evidence_gap_report_digest(
        payload
    )
    if supplied_digest != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    config = _config_from_payload(payload["config"])
    config_version = _require_config_version(payload["config_version"])
    if config_version != config.config_version:
        raise ValueError("config_version does not match config payload")
    if type(payload["rows"]) is not list:
        raise ValueError("rows must be a list")
    if type(payload["reason_code_counts"]) is not list:
        raise ValueError("reason_code_counts must be a list")
    return ResearchStrategyEventResolutionEvidenceGapReport(
        generated_at=_datetime_from_payload(
            "generated_at",
            payload["generated_at"],
        ),
        config=config,
        status=_require_status(payload["status"], allow_no_inputs=True),
        event_count=_decimal_from_payload("event_count", payload["event_count"]),
        pass_count=_decimal_from_payload("pass_count", payload["pass_count"]),
        watch_count=_decimal_from_payload("watch_count", payload["watch_count"]),
        block_count=_decimal_from_payload("block_count", payload["block_count"]),
        review_required_count=_decimal_from_payload(
            "review_required_count",
            payload["review_required_count"],
        ),
        average_evidence_coverage_ratio=_decimal_from_payload(
            "average_evidence_coverage_ratio",
            payload["average_evidence_coverage_ratio"],
        ),
        average_source_authority_ratio=_decimal_from_payload(
            "average_source_authority_ratio",
            payload["average_source_authority_ratio"],
        ),
        average_evidence_freshness_score=_decimal_from_payload(
            "average_evidence_freshness_score",
            payload["average_evidence_freshness_score"],
        ),
        average_conflict_ratio=_decimal_from_payload(
            "average_conflict_ratio",
            payload["average_conflict_ratio"],
        ),
        average_manual_review_priority_score=_decimal_from_payload(
            "average_manual_review_priority_score",
            payload["average_manual_review_priority_score"],
        ),
        max_manual_review_priority_score=_decimal_from_payload(
            "max_manual_review_priority_score",
            payload["max_manual_review_priority_score"],
        ),
        total_conflicting_source_count=_decimal_from_payload(
            "total_conflicting_source_count",
            payload["total_conflicting_source_count"],
        ),
        reason_codes=_reason_codes_from_payload(payload["reason_codes"]),
        reason_code_counts=tuple(
            _reason_count_from_payload(item)
            for item in payload["reason_code_counts"]
        ),
        rows=tuple(_row_from_payload(item) for item in payload["rows"]),
        derived_validation_digest=supplied_digest,
        paper_only=_true_from_payload("paper_only", payload["paper_only"]),
        report_only=_true_from_payload("report_only", payload["report_only"]),
        readonly=_true_from_payload("readonly", payload["readonly"]),
    )


__all__ = [
    "DEFAULT_RESEARCH_STRATEGY_EVENT_RESOLUTION_EVIDENCE_GAP_CONFIG_VERSION",
    "ResearchStrategyEventResolutionEvidenceGapConfig",
    "ResearchStrategyEventResolutionEvidenceGapInput",
    "ResearchStrategyEventResolutionEvidenceGapReasonCodeCount",
    "ResearchStrategyEventResolutionEvidenceGapReport",
    "ResearchStrategyEventResolutionEvidenceGapRow",
    "build_research_strategy_event_resolution_evidence_gap_report",
    "research_strategy_event_resolution_evidence_gap_report_digest",
    "research_strategy_event_resolution_evidence_gap_report_from_payload",
    "research_strategy_event_resolution_evidence_gap_report_payload",
]
