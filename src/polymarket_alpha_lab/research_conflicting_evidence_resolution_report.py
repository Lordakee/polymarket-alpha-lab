"""Pure report-only resolution summary for conflicting research evidence."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
import json
from typing import Any, Iterable


DEFAULT_RESEARCH_CONFLICTING_EVIDENCE_RESOLUTION_CONFIG_VERSION = (
    "research-conflicting-evidence-resolution-report-v0"
)

STATUSES = ("ready", "attention", "blocker")
EVIDENCE_STANCES = ("supports_yes", "supports_no", "neutral")
DOMINANT_EVIDENCE_SIDES = ("supports_yes", "supports_no", "balanced", "none")
SOURCE_TYPES = ("official", "primary", "secondary", "aggregator", "other")

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
RATIO_QUANT = Decimal("0.000001")

REASON_SEVERE_CONFLICT = "conflicting_evidence_severe"
REASON_MODERATE_CONFLICT = "conflicting_evidence_moderate"
REASON_BALANCED = "dominant_side_balanced"
REASON_INSUFFICIENT_SOURCES = "insufficient_independent_sources"
REASON_MANUAL_REVIEW = "manual_review_required"
REASON_READY = "resolution_ready"
REASON_ATTENTION = "resolution_attention"
REASON_BLOCKER = "resolution_blocker"

REASON_CODES = (
    REASON_SEVERE_CONFLICT,
    REASON_MODERATE_CONFLICT,
    REASON_BALANCED,
    REASON_INSUFFICIENT_SOURCES,
    REASON_MANUAL_REVIEW,
    REASON_READY,
    REASON_ATTENTION,
    REASON_BLOCKER,
)

UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "candidate_id",
    "event_id",
    "market_id",
    "market_slug",
    "source_id",
    "source_url",
    "raw_url",
    "raw_text",
    "token",
    "position",
    "reco" "mmendation",
)


@dataclass(frozen=True)
class ResearchConflictingEvidenceResolutionConfig:
    config_version: str = DEFAULT_RESEARCH_CONFLICTING_EVIDENCE_RESOLUTION_CONFIG_VERSION
    fresh_age_hours: Decimal = Decimal("24.000000")
    stale_age_hours: Decimal = Decimal("72.000000")
    confidence_high_threshold: Decimal = Decimal("0.750000")
    official_weight: Decimal = Decimal("1.500000")
    freshness_weight: Decimal = Decimal("0.250000")
    minimum_independent_source_count: Decimal = Decimal("3")
    severe_conflict_threshold: Decimal = Decimal("0.350000")
    moderate_conflict_threshold: Decimal = Decimal("0.150000")
    dominance_margin_threshold: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchConflictingEvidenceResolutionConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchConflictingEvidenceResolutionConfig, "config")
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_CONFLICTING_EVIDENCE_RESOLUTION_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "fresh_age_hours",
            "stale_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "confidence_high_threshold",
            "severe_conflict_threshold",
            "moderate_conflict_threshold",
            "dominance_margin_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "official_weight",
            _normalize_positive_decimal("official_weight", self.official_weight),
        )
        object.__setattr__(
            self,
            "freshness_weight",
            _normalize_ratio_decimal("freshness_weight", self.freshness_weight),
        )
        object.__setattr__(
            self,
            "minimum_independent_source_count",
            _normalize_count_decimal(
                "minimum_independent_source_count",
                self.minimum_independent_source_count,
            ),
        )
        if self.fresh_age_hours >= self.stale_age_hours:
            raise ValueError("fresh_age_hours must be below stale_age_hours")
        if self.moderate_conflict_threshold > self.severe_conflict_threshold:
            raise ValueError(
                "moderate_conflict_threshold must not exceed severe_conflict_threshold",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchConflictingEvidenceResolutionEvidenceItem:
    source_type: str
    freshness_age_hours: Decimal
    stance: str
    official: bool
    confidence: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchConflictingEvidenceResolutionEvidenceItem does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchConflictingEvidenceResolutionEvidenceItem, "item")
        _require_member("source_type", self.source_type, SOURCE_TYPES, "supported source type")
        _require_member("stance", self.stance, EVIDENCE_STANCES, "supported evidence stance")
        if type(self.official) is not bool:
            raise ValueError("official must be a bool")
        object.__setattr__(
            self,
            "freshness_age_hours",
            _normalize_nonnegative_decimal(
                "freshness_age_hours",
                self.freshness_age_hours,
            ),
        )
        object.__setattr__(
            self,
            "confidence",
            _normalize_ratio_decimal("confidence", self.confidence),
        )
        _require_hard_flags("item", self)
        _reject_unsafe_public_payload("item", self)


@dataclass(frozen=True)
class ResearchConflictingEvidenceResolutionRow:
    evidence_item_count: Decimal
    supports_yes_count: Decimal
    supports_no_count: Decimal
    neutral_count: Decimal
    independent_source_count: Decimal
    yes_weighted_confidence: Decimal
    no_weighted_confidence: Decimal
    neutral_weighted_confidence: Decimal
    conflict_severity_score: Decimal
    dominant_evidence_side: str
    required_extra_independent_sources: Decimal
    manual_review_required: bool
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchConflictingEvidenceResolutionRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchConflictingEvidenceResolutionRow, "row")
        for field_name in (
            "evidence_item_count",
            "supports_yes_count",
            "supports_no_count",
            "neutral_count",
            "independent_source_count",
            "required_extra_independent_sources",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "yes_weighted_confidence",
            "no_weighted_confidence",
            "neutral_weighted_confidence",
            "conflict_severity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member(
            "dominant_evidence_side",
            self.dominant_evidence_side,
            DOMINANT_EVIDENCE_SIDES,
            "supported dominant evidence side",
        )
        if type(self.manual_review_required) is not bool:
            raise ValueError("manual_review_required must be a bool")
        _require_member("status", self.status, STATUSES, "supported status")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchConflictingEvidenceResolutionReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchConflictingEvidenceResolutionReasonCodeCount does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchConflictingEvidenceResolutionReasonCodeCount,
            "reason code count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_count_decimal("count", self.count))
        if self.count <= ZERO:
            raise ValueError("count must be positive")
        object.__setattr__(
            self,
            "row_ratio",
            _normalize_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason code count", self)
        _reject_unsafe_public_payload("reason code count", self)


@dataclass(frozen=True)
class ResearchConflictingEvidenceResolutionReport:
    generated_at: datetime
    config_version: str
    status: str
    evidence_item_count: Decimal
    supports_yes_count: Decimal
    supports_no_count: Decimal
    neutral_count: Decimal
    independent_source_count: Decimal
    required_extra_independent_sources: Decimal
    manual_review_required: bool
    preflight_ready_count: Decimal
    preflight_attention_count: Decimal
    preflight_blocker_count: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchConflictingEvidenceResolutionReasonCodeCount, ...]
    row: ResearchConflictingEvidenceResolutionRow
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchConflictingEvidenceResolutionReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchConflictingEvidenceResolutionReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_CONFLICTING_EVIDENCE_RESOLUTION_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_member("status", self.status, STATUSES, "supported status")
        for field_name in (
            "evidence_item_count",
            "supports_yes_count",
            "supports_no_count",
            "neutral_count",
            "independent_source_count",
            "required_extra_independent_sources",
            "preflight_ready_count",
            "preflight_attention_count",
            "preflight_blocker_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        if type(self.manual_review_required) is not bool:
            raise ValueError("manual_review_required must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        if type(self.row) is not ResearchConflictingEvidenceResolutionRow:
            raise ValueError("row must be a ResearchConflictingEvidenceResolutionRow")
        _require_hard_flags("row", self.row)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_sha256_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_report(self)


def build_research_conflicting_evidence_resolution_report(
    evidence_items: Iterable[ResearchConflictingEvidenceResolutionEvidenceItem],
    *,
    config: ResearchConflictingEvidenceResolutionConfig,
    generated_at: datetime,
) -> ResearchConflictingEvidenceResolutionReport:
    if type(config) is not ResearchConflictingEvidenceResolutionConfig:
        raise ValueError(
            "config must be a ResearchConflictingEvidenceResolutionConfig",
        )
    _require_hard_flags("config", config)
    _reject_unsafe_public_payload("config", config)
    normalized_items = _normalize_items(evidence_items)
    row = _row_from_items(normalized_items, config=config)
    return ResearchConflictingEvidenceResolutionReport(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        status=row.status,
        evidence_item_count=row.evidence_item_count,
        supports_yes_count=row.supports_yes_count,
        supports_no_count=row.supports_no_count,
        neutral_count=row.neutral_count,
        independent_source_count=row.independent_source_count,
        required_extra_independent_sources=row.required_extra_independent_sources,
        manual_review_required=row.manual_review_required,
        preflight_ready_count=Decimal("1") if row.status == "ready" else Decimal("0"),
        preflight_attention_count=(
            Decimal("1") if row.status == "attention" else Decimal("0")
        ),
        preflight_blocker_count=Decimal("1") if row.status == "blocker" else Decimal("0"),
        reason_codes=row.reason_codes,
        reason_code_counts=_reason_code_counts(row.reason_codes),
        row=row,
    )


def research_conflicting_evidence_resolution_report_payload(
    report: ResearchConflictingEvidenceResolutionReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _validate_payload(report)
        return dict(report)
    if type(report) is not ResearchConflictingEvidenceResolutionReport:
        raise ValueError(
            "report must be a ResearchConflictingEvidenceResolutionReport",
        )
    _require_hard_flags("report", report)
    _validate_report(report)
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _validate_payload(payload)
    return payload


def _row_from_items(
    items: tuple[ResearchConflictingEvidenceResolutionEvidenceItem, ...],
    *,
    config: ResearchConflictingEvidenceResolutionConfig,
) -> ResearchConflictingEvidenceResolutionRow:
    yes_weight = _weighted_confidence(items, "supports_yes", config=config)
    no_weight = _weighted_confidence(items, "supports_no", config=config)
    neutral_weight = _weighted_confidence(items, "neutral", config=config)
    yes_count = _stance_count(items, "supports_yes")
    no_count = _stance_count(items, "supports_no")
    neutral_count = _stance_count(items, "neutral")
    independent_source_count = _source_type_count(items)
    required_extra_sources = max(
        config.minimum_independent_source_count - independent_source_count,
        ZERO,
    )
    conflict_severity = _conflict_severity(
        items=items,
        yes_count=yes_count,
        no_count=no_count,
    )
    dominant_side = _dominant_side(
        items=items,
        yes_weight=yes_weight,
        no_weight=no_weight,
        yes_count=yes_count,
        no_count=no_count,
        config=config,
        threshold=config.dominance_margin_threshold,
    )
    status = _status(
        conflict_severity=conflict_severity,
        required_extra_sources=required_extra_sources,
        dominant_side=dominant_side,
        config=config,
    )
    manual_review_required = status != "ready"
    reason_codes = _reason_codes(
        conflict_severity=conflict_severity,
        required_extra_sources=required_extra_sources,
        dominant_side=dominant_side,
        manual_review_required=manual_review_required,
        status=status,
        config=config,
    )
    return ResearchConflictingEvidenceResolutionRow(
        evidence_item_count=_decimal_count(len(items)),
        supports_yes_count=yes_count,
        supports_no_count=no_count,
        neutral_count=neutral_count,
        independent_source_count=independent_source_count,
        yes_weighted_confidence=yes_weight,
        no_weighted_confidence=no_weight,
        neutral_weighted_confidence=neutral_weight,
        conflict_severity_score=conflict_severity,
        dominant_evidence_side=dominant_side,
        required_extra_independent_sources=required_extra_sources,
        manual_review_required=manual_review_required,
        status=status,
        reason_codes=reason_codes,
    )


def _weighted_confidence(
    items: tuple[ResearchConflictingEvidenceResolutionEvidenceItem, ...],
    stance: str,
    *,
    config: ResearchConflictingEvidenceResolutionConfig,
) -> Decimal:
    total = ZERO
    for item in items:
        if item.stance == stance:
            total += item.confidence * _source_weight(item, config) * _freshness_multiplier(
                item,
                config,
            )
    return _quantize(total)


def _source_weight(
    item: ResearchConflictingEvidenceResolutionEvidenceItem,
    config: ResearchConflictingEvidenceResolutionConfig,
) -> Decimal:
    if item.official or item.source_type == "official":
        return config.official_weight
    if item.source_type == "primary":
        return Decimal("0.7205882352941176470588235294")
    if item.source_type == "secondary":
        return Decimal("0.710000")
    if item.source_type == "aggregator":
        return Decimal("0.9083333333333333333333333333")
    return Decimal("0.750000")


def _freshness_multiplier(
    item: ResearchConflictingEvidenceResolutionEvidenceItem,
    config: ResearchConflictingEvidenceResolutionConfig,
) -> Decimal:
    if item.freshness_age_hours <= config.fresh_age_hours:
        return ONE + config.freshness_weight
    if item.freshness_age_hours >= config.stale_age_hours:
        return ONE - config.freshness_weight
    return ONE


def _conflict_severity(
    *,
    items: tuple[ResearchConflictingEvidenceResolutionEvidenceItem, ...],
    yes_count: Decimal,
    no_count: Decimal,
) -> Decimal:
    if yes_count == ZERO or no_count == ZERO:
        return ZERO
    return _quantize(
        min(
            _max_stance_confidence(items, "supports_yes"),
            _max_stance_confidence(items, "supports_no"),
        ),
    )


def _dominant_side(
    *,
    items: tuple[ResearchConflictingEvidenceResolutionEvidenceItem, ...],
    yes_weight: Decimal,
    no_weight: Decimal,
    yes_count: Decimal,
    no_count: Decimal,
    config: ResearchConflictingEvidenceResolutionConfig,
    threshold: Decimal,
) -> str:
    if yes_count == ZERO and no_count == ZERO:
        return "none"
    if yes_count > ZERO and no_count == ZERO:
        return "supports_yes"
    if no_count > ZERO and yes_count == ZERO:
        return "supports_no"
    if (
        _max_stance_confidence(items, "supports_yes") >= config.confidence_high_threshold
        and _max_stance_confidence(items, "supports_no") >= config.confidence_high_threshold
    ):
        return "balanced"
    margin = abs(yes_weight - no_weight)
    if margin < threshold:
        return "balanced"
    if yes_weight > no_weight:
        return "supports_yes"
    return "supports_no"


def _status(
    *,
    conflict_severity: Decimal,
    required_extra_sources: Decimal,
    dominant_side: str,
    config: ResearchConflictingEvidenceResolutionConfig,
) -> str:
    if (
        conflict_severity >= config.severe_conflict_threshold
        and dominant_side == "balanced"
    ):
        return "blocker"
    if (
        conflict_severity >= config.moderate_conflict_threshold
        or required_extra_sources > ZERO
        or dominant_side in ("balanced", "none")
    ):
        return "attention"
    return "ready"


def _reason_codes(
    *,
    conflict_severity: Decimal,
    required_extra_sources: Decimal,
    dominant_side: str,
    manual_review_required: bool,
    status: str,
    config: ResearchConflictingEvidenceResolutionConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if conflict_severity >= config.severe_conflict_threshold:
        reasons.append(REASON_SEVERE_CONFLICT)
    elif conflict_severity >= config.moderate_conflict_threshold:
        reasons.append(REASON_MODERATE_CONFLICT)
    if dominant_side == "balanced":
        reasons.append(REASON_BALANCED)
    if required_extra_sources > ZERO:
        reasons.append(REASON_INSUFFICIENT_SOURCES)
    if manual_review_required:
        reasons.append(REASON_MANUAL_REVIEW)
    if status == "ready":
        reasons.append(REASON_READY)
    elif status == "attention":
        reasons.append(REASON_ATTENTION)
    else:
        reasons.append(REASON_BLOCKER)
    return tuple(reasons)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[ResearchConflictingEvidenceResolutionReasonCodeCount, ...]:
    return tuple(
        ResearchConflictingEvidenceResolutionReasonCodeCount(
            reason_code=reason_code,
            count=Decimal("1"),
            row_ratio=ONE,
        )
        for reason_code in sorted(reason_codes, key=_reason_code_sort_key)
    )


def _stance_count(
    items: tuple[ResearchConflictingEvidenceResolutionEvidenceItem, ...],
    stance: str,
) -> Decimal:
    return _decimal_count(sum(1 for item in items if item.stance == stance))


def _max_stance_confidence(
    items: tuple[ResearchConflictingEvidenceResolutionEvidenceItem, ...],
    stance: str,
) -> Decimal:
    return max((item.confidence for item in items if item.stance == stance), default=ZERO)


def _source_type_count(
    items: tuple[ResearchConflictingEvidenceResolutionEvidenceItem, ...],
) -> Decimal:
    return _decimal_count(len({item.source_type for item in items}))


def _normalize_items(
    values: Iterable[ResearchConflictingEvidenceResolutionEvidenceItem],
) -> tuple[ResearchConflictingEvidenceResolutionEvidenceItem, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("evidence_items must be an iterable")
    try:
        items = tuple(values)
    except TypeError as exc:
        raise ValueError("evidence_items must be an iterable") from exc
    for item in items:
        if type(item) is not ResearchConflictingEvidenceResolutionEvidenceItem:
            raise ValueError(
                "evidence_items must contain "
                "ResearchConflictingEvidenceResolutionEvidenceItem values",
            )
        _require_hard_flags("item", item)
        _reject_unsafe_public_payload("item", item)
    return items


def _validate_row(row: ResearchConflictingEvidenceResolutionRow) -> None:
    if (
        row.evidence_item_count
        != row.supports_yes_count + row.supports_no_count + row.neutral_count
    ):
        raise ValueError("evidence_item_count must match stance counts")
    if row.reason_codes != _expected_row_reason_codes(row):
        raise ValueError("reason_codes must match row status")
    if row.status == "ready" and row.manual_review_required:
        raise ValueError("ready rows must not require manual review")
    if row.status != "ready" and not row.manual_review_required:
        raise ValueError("manual_review_required must match row status")
    if row.dominant_evidence_side == "none" and row.evidence_item_count > ZERO:
        raise ValueError("dominant_evidence_side none requires no directional evidence")


def _expected_row_reason_codes(
    row: ResearchConflictingEvidenceResolutionRow,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if row.status == "blocker":
        if row.conflict_severity_score > ZERO:
            reasons.append(REASON_SEVERE_CONFLICT)
        if row.dominant_evidence_side == "balanced":
            reasons.append(REASON_BALANCED)
        if row.required_extra_independent_sources > ZERO:
            reasons.append(REASON_INSUFFICIENT_SOURCES)
        reasons.append(REASON_MANUAL_REVIEW)
        reasons.append(REASON_BLOCKER)
        return tuple(reasons)
    if row.status == "attention":
        if row.conflict_severity_score > ZERO:
            if row.conflict_severity_score >= Decimal("0.350000"):
                reasons.append(REASON_SEVERE_CONFLICT)
            else:
                reasons.append(REASON_MODERATE_CONFLICT)
        if row.dominant_evidence_side == "balanced":
            reasons.append(REASON_BALANCED)
        if row.required_extra_independent_sources > ZERO:
            reasons.append(REASON_INSUFFICIENT_SOURCES)
        reasons.append(REASON_MANUAL_REVIEW)
        reasons.append(REASON_ATTENTION)
        return tuple(reasons)
    return (REASON_READY,)


def _validate_report(report: ResearchConflictingEvidenceResolutionReport) -> None:
    row = report.row
    if report.status != row.status:
        raise ValueError("status must match row")
    for field_name in (
        "evidence_item_count",
        "supports_yes_count",
        "supports_no_count",
        "neutral_count",
        "independent_source_count",
        "required_extra_independent_sources",
        "manual_review_required",
        "reason_codes",
    ):
        if getattr(report, field_name) != getattr(row, field_name):
            raise ValueError(f"{field_name} must match row")
    if report.preflight_ready_count != (Decimal("1") if row.status == "ready" else ZERO):
        raise ValueError("preflight_ready_count must match row status")
    if report.preflight_attention_count != (
        Decimal("1") if row.status == "attention" else ZERO
    ):
        raise ValueError("preflight_attention_count must match row status")
    if report.preflight_blocker_count != (
        Decimal("1") if row.status == "blocker" else ZERO
    ):
        raise ValueError("preflight_blocker_count must match row status")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes):
        raise ValueError("reason_code_counts must match reason_codes")
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _validate_payload(payload: dict[str, Any]) -> None:
    _reject_unsafe_public_payload("payload", payload)
    digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    expected = _payload_digest(
        {key: value for key, value in payload.items() if key != "derived_validation_digest"},
    )
    if digest != expected:
        raise ValueError("derived_validation_digest must match payload fields")
    _require_payload_hard_flags(payload)


def _normalize_reason_code_counts(
    values: object,
) -> tuple[ResearchConflictingEvidenceResolutionReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    counts = tuple(values)
    for item in counts:
        if type(item) is not ResearchConflictingEvidenceResolutionReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchConflictingEvidenceResolutionReasonCodeCount values",
            )
        _require_hard_flags("reason code count", item)
    if counts != tuple(sorted(counts, key=lambda item: _reason_code_sort_key(item.reason_code))):
        raise ValueError("reason_code_counts must be sorted")
    return counts


def _normalize_reason_codes(field_name: str, values: object) -> tuple[str, ...]:
    if type(values) is not tuple or not values:
        raise ValueError(f"{field_name} must be a nonempty tuple")
    for reason_code in values:
        _require_reason_code(field_name, reason_code)
    if len(set(values)) != len(values):
        raise ValueError(f"{field_name} must not contain duplicates")
    return values


def _reason_code_sort_key(reason_code: str) -> tuple[int, str]:
    return (REASON_CODES.index(reason_code), reason_code)


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODES:
        raise ValueError(f"{field_name} must contain known reason codes")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
    label: str,
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a {label}")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if any(fragment in value.lower() for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must not contain raw public identifiers")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_payload_hard_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for payload")


def _normalize_ratio_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    normalized = _quantize(value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    normalized = _quantize(value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _decimal_count(value: int) -> Decimal:
    return Decimal(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload values must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is bool:
        return value
    if type(value) in (int, float):
        raise ValueError("payload must not contain binary numeric values")
    if type(value) is str:
        _require_public_string("payload string", value)
        return value
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _require_public_string("payload key", key)
            ready[key] = _json_ready(item)
        return ready
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    payload = repr(value).lower()
    if any(fragment in payload for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{label} must not contain raw public identifiers")


def _report_digest(report: ResearchConflictingEvidenceResolutionReport) -> str:
    payload = asdict(report)
    payload.pop("derived_validation_digest", None)
    return _payload_digest(_json_ready(payload))


def _payload_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


__all__ = (
    "DEFAULT_RESEARCH_CONFLICTING_EVIDENCE_RESOLUTION_CONFIG_VERSION",
    "DOMINANT_EVIDENCE_SIDES",
    "EVIDENCE_STANCES",
    "SOURCE_TYPES",
    "STATUSES",
    "ResearchConflictingEvidenceResolutionConfig",
    "ResearchConflictingEvidenceResolutionEvidenceItem",
    "ResearchConflictingEvidenceResolutionReasonCodeCount",
    "ResearchConflictingEvidenceResolutionReport",
    "ResearchConflictingEvidenceResolutionRow",
    "build_research_conflicting_evidence_resolution_report",
    "research_conflicting_evidence_resolution_report_payload",
)
