"""Pure report-only event resolution authority claim tail reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_EVENT_RESOLUTION_AUTHORITY_CLAIM_TAIL_REPORT_CONFIG_VERSION = (
    "research-event-resolution-authority-claim-tail-report-v0"
)
RESEARCH_EVENT_RESOLUTION_AUTHORITY_CLAIM_TAIL_REPORT_STATUSES = (
    "pass",
    "watch",
    "block",
)

SIX = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SHA256_HEX_LENGTH = 64

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUS_RANK = {
    STATUS_BLOCK: Decimal("0.000000"),
    STATUS_WATCH: Decimal("1.000000"),
    STATUS_PASS: Decimal("2.000000"),
}

EMPTY_REASON = "research_event_resolution_authority_claim_tail_empty"
PASS_REASON = "authority_claim_tail_pass"
WATCH_REASON = "authority_claim_tail_watch"
BLOCK_REASON = "authority_claim_tail_block"
CLAIM_AGE_WATCH_REASON = "claim_age_tail_watch"
CLAIM_AGE_BLOCK_REASON = "claim_age_tail_block"
AUTHORITY_DELAY_WATCH_REASON = "authority_delay_tail_watch"
AUTHORITY_DELAY_BLOCK_REASON = "authority_delay_tail_block"
AUTHORITY_CONFIDENCE_WATCH_REASON = "authority_confidence_tail_watch"
AUTHORITY_CONFIDENCE_BLOCK_REASON = "authority_confidence_tail_block"
CLAIM_CONFLICT_WATCH_REASON = "claim_conflict_tail_watch"
CLAIM_CONFLICT_BLOCK_REASON = "claim_conflict_tail_block"
AUTHORITY_QUORUM_WATCH_REASON = "authority_quorum_tail_watch"
AUTHORITY_QUORUM_BLOCK_REASON = "authority_quorum_tail_block"

REPORT_REASON_CODES = (EMPTY_REASON, BLOCK_REASON, WATCH_REASON, PASS_REASON)
ROW_REASON_CODES = (
    PASS_REASON,
    WATCH_REASON,
    BLOCK_REASON,
    CLAIM_AGE_WATCH_REASON,
    CLAIM_AGE_BLOCK_REASON,
    AUTHORITY_DELAY_WATCH_REASON,
    AUTHORITY_DELAY_BLOCK_REASON,
    AUTHORITY_CONFIDENCE_WATCH_REASON,
    AUTHORITY_CONFIDENCE_BLOCK_REASON,
    CLAIM_CONFLICT_WATCH_REASON,
    CLAIM_CONFLICT_BLOCK_REASON,
    AUTHORITY_QUORUM_WATCH_REASON,
    AUTHORITY_QUORUM_BLOCK_REASON,
)
ROW_REASON_INDEX = {reason: index for index, reason in enumerate(ROW_REASON_CODES)}


def _j(*parts: str) -> str:
    return "".join(parts)


BAD_PUBLIC_FRAGMENTS = (
    _j("raw", "_id"),
    _j("cand", "idate"),
    _j("mark", "et"),
    _j("sl", "ug"),
    _j("que", "stion"),
    _j("sour", "ce"),
    _j("ur", "l"),
    _j("te", "xt"),
    _j("d", "sn"),
    _j("ta", "ble"),
    _j("to", "ken"),
    _j("sec", "ret"),
    _j("cre", "den", "tial"),
    _j("wal", "let"),
    _j("ord", "er"),
    _j("tra", "de"),
    _j("li", "ve"),
    _j("siz", "ing"),
    _j("recomm", "endation"),
    _j("h", "tt", "p"),
    _j("w", "ww", "."),
    _j(":", "//"),
    _j("post", "gres", "://"),
    _j("my", "sql", "://"),
    _j("j", "d", "b", "c", ":"),
)

__all__ = (
    "DEFAULT_RESEARCH_EVENT_RESOLUTION_AUTHORITY_CLAIM_TAIL_REPORT_CONFIG_VERSION",
    "RESEARCH_EVENT_RESOLUTION_AUTHORITY_CLAIM_TAIL_REPORT_STATUSES",
    "ResearchEventResolutionAuthorityClaimTailConfig",
    "ResearchEventResolutionAuthorityClaimTailObservation",
    "ResearchEventResolutionAuthorityClaimTailReasonCodeCount",
    "ResearchEventResolutionAuthorityClaimTailRow",
    "ResearchEventResolutionAuthorityClaimTailReport",
    "build_research_event_resolution_authority_claim_tail_report",
    "research_event_resolution_authority_claim_tail_report_digest",
    "research_event_resolution_authority_claim_tail_report_payload",
    "validate_research_event_resolution_authority_claim_tail_report_digest",
    "validate_research_event_resolution_authority_claim_tail_report_payload",
)


@dataclass(frozen=True)
class ResearchEventResolutionAuthorityClaimTailConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_RESOLUTION_AUTHORITY_CLAIM_TAIL_REPORT_CONFIG_VERSION
    )
    pass_claim_age_seconds: Decimal = Decimal("3600.000000")
    watch_claim_age_seconds: Decimal = Decimal("14400.000000")
    pass_authority_delay_seconds: Decimal = Decimal("1800.000000")
    watch_authority_delay_seconds: Decimal = Decimal("7200.000000")
    min_pass_authority_confidence: Decimal = Decimal("0.800000")
    min_watch_authority_confidence: Decimal = Decimal("0.600000")
    max_pass_claim_conflict_pressure: Decimal = Decimal("0.100000")
    max_watch_claim_conflict_pressure: Decimal = Decimal("0.300000")
    min_pass_authority_quorum_ratio: Decimal = Decimal("1.000000")
    min_watch_authority_quorum_ratio: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionAuthorityClaimTailConfig:
            raise TypeError(
                "ResearchEventResolutionAuthorityClaimTailConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventResolutionAuthorityClaimTailConfig,
            "config",
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_AUTHORITY_CLAIM_TAIL_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_claim_age_seconds",
            "watch_claim_age_seconds",
            "pass_authority_delay_seconds",
            "watch_authority_delay_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_authority_confidence",
            "min_watch_authority_confidence",
            "max_pass_claim_conflict_pressure",
            "max_watch_claim_conflict_pressure",
            "min_pass_authority_quorum_ratio",
            "min_watch_authority_quorum_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_lower_ceiling(
            "pass_claim_age_seconds",
            self.pass_claim_age_seconds,
            "watch_claim_age_seconds",
            self.watch_claim_age_seconds,
        )
        _require_lower_ceiling(
            "pass_authority_delay_seconds",
            self.pass_authority_delay_seconds,
            "watch_authority_delay_seconds",
            self.watch_authority_delay_seconds,
        )
        _require_higher_floor(
            "min_pass_authority_confidence",
            self.min_pass_authority_confidence,
            "min_watch_authority_confidence",
            self.min_watch_authority_confidence,
        )
        _require_lower_ceiling(
            "max_pass_claim_conflict_pressure",
            self.max_pass_claim_conflict_pressure,
            "max_watch_claim_conflict_pressure",
            self.max_watch_claim_conflict_pressure,
        )
        _require_higher_floor(
            "min_pass_authority_quorum_ratio",
            self.min_pass_authority_quorum_ratio,
            "min_watch_authority_quorum_ratio",
            self.min_watch_authority_quorum_ratio,
        )
        _require_hard_flags("config", self)
        _reject_bad_public("config", _payload_value(self))


@dataclass(frozen=True)
class ResearchEventResolutionAuthorityClaimTailObservation:
    private_event_ref: str
    private_claim_ref: str
    private_authority_ref: str
    claim_age_seconds: Decimal
    authority_delay_seconds: Decimal
    authority_confidence: Decimal
    claim_conflict_pressure: Decimal
    matched_authority_count: Decimal
    required_authority_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionAuthorityClaimTailObservation:
            raise TypeError(
                "ResearchEventResolutionAuthorityClaimTailObservation does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventResolutionAuthorityClaimTailObservation,
            "observation",
        )
        for field_name in (
            "private_event_ref",
            "private_claim_ref",
            "private_authority_ref",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_private_string(field_name, getattr(self, field_name)),
            )
        for field_name in ("claim_age_seconds", "authority_delay_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("authority_confidence", "claim_conflict_pressure"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "matched_authority_count",
            _require_nonnegative_count(
                "matched_authority_count",
                self.matched_authority_count,
            ),
        )
        object.__setattr__(
            self,
            "required_authority_count",
            _require_positive_count(
                "required_authority_count",
                self.required_authority_count,
            ),
        )
        if self.matched_authority_count > self.required_authority_count:
            raise ValueError(
                "matched_authority_count must not exceed required_authority_count",
            )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchEventResolutionAuthorityClaimTailReasonCodeCount:
    reason_code: str
    count: Decimal
    input_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionAuthorityClaimTailReasonCodeCount:
            raise TypeError(
                "ResearchEventResolutionAuthorityClaimTailReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventResolutionAuthorityClaimTailReasonCodeCount,
            "reason_code_count",
        )
        object.__setattr__(
            self,
            "reason_code",
            _require_reason_code("reason_code", self.reason_code, ROW_REASON_CODES),
        )
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count("count", self.count),
        )
        object.__setattr__(
            self,
            "input_ratio",
            _require_ratio_decimal("input_ratio", self.input_ratio),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_bad_public("reason_code_count", _payload_value(self))


@dataclass(frozen=True)
class ResearchEventResolutionAuthorityClaimTailRow:
    rank: Decimal
    event_trace_hash: str
    claim_trace_hash: str
    authority_trace_hash: str
    claim_age_seconds: Decimal
    authority_delay_seconds: Decimal
    authority_confidence: Decimal
    claim_conflict_pressure: Decimal
    matched_authority_count: Decimal
    required_authority_count: Decimal
    authority_quorum_ratio: Decimal
    claim_age_tail_pressure: Decimal
    authority_delay_tail_pressure: Decimal
    confidence_gap_tail_pressure: Decimal
    authority_quorum_tail_pressure: Decimal
    authority_claim_tail_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionAuthorityClaimTailRow:
            raise TypeError(
                "ResearchEventResolutionAuthorityClaimTailRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventResolutionAuthorityClaimTailRow, "row")
        object.__setattr__(self, "rank", _require_positive_decimal("rank", self.rank))
        for field_name in (
            "event_trace_hash",
            "claim_trace_hash",
            "authority_trace_hash",
        ):
            _require_sha256(field_name, getattr(self, field_name))
        for field_name in (
            "claim_age_seconds",
            "authority_delay_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "authority_confidence",
            "claim_conflict_pressure",
            "authority_quorum_ratio",
            "claim_age_tail_pressure",
            "authority_delay_tail_pressure",
            "confidence_gap_tail_pressure",
            "authority_quorum_tail_pressure",
            "authority_claim_tail_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "matched_authority_count",
            "required_authority_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.required_authority_count <= ZERO:
            raise ValueError("required_authority_count must be positive")
        if self.matched_authority_count > self.required_authority_count:
            raise ValueError(
                "matched_authority_count must not exceed required_authority_count",
            )
        _require_status(self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        if self.status != _status_from_row_reasons(self.reason_codes):
            raise ValueError("status must match reason_codes")
        _require_hard_flags("row", self)
        _reject_bad_public("row", _payload_value(self))


@dataclass(frozen=True)
class ResearchEventResolutionAuthorityClaimTailReport:
    generated_at: datetime
    config_version: str
    status: str
    claim_count: Decimal
    pass_claim_count: Decimal
    watch_claim_count: Decimal
    block_claim_count: Decimal
    tail_claim_count: Decimal
    maximum_authority_claim_tail_score: Decimal
    average_authority_claim_tail_score: Decimal
    average_authority_confidence: Decimal
    minimum_authority_quorum_ratio: Decimal
    rows: tuple[ResearchEventResolutionAuthorityClaimTailRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchEventResolutionAuthorityClaimTailReasonCodeCount, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionAuthorityClaimTailReport:
            raise TypeError(
                "ResearchEventResolutionAuthorityClaimTailReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventResolutionAuthorityClaimTailReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        _require_status(self.status)
        for field_name in (
            "claim_count",
            "pass_claim_count",
            "watch_claim_count",
            "block_claim_count",
            "tail_claim_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "maximum_authority_claim_tail_score",
            "average_authority_claim_tail_score",
            "average_authority_confidence",
            "minimum_authority_quorum_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _require_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _require_reason_code_counts(self.reason_code_counts),
        )
        _require_sha256("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report(self)
        _reject_bad_public("report", _payload_value(self))
        _require_matching_digest(_payload_value(self))

    @property
    def payload(self) -> dict[str, Any]:
        return research_event_resolution_authority_claim_tail_report_payload(self)


def build_research_event_resolution_authority_claim_tail_report(
    observations: Iterable[ResearchEventResolutionAuthorityClaimTailObservation],
    *,
    config: ResearchEventResolutionAuthorityClaimTailConfig | None = None,
    generated_at: datetime,
) -> ResearchEventResolutionAuthorityClaimTailReport:
    cfg = config or ResearchEventResolutionAuthorityClaimTailConfig()
    _require_exact_type(cfg, ResearchEventResolutionAuthorityClaimTailConfig, "config")
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    rows = tuple(_row_for_observation(item, cfg) for item in normalized)
    rows = tuple(_ranked_row(index, row) for index, row in enumerate(_sorted_rows(rows), 1))
    values: dict[str, Any] = {
        "generated_at": generated_at_utc,
        "config_version": cfg.config_version,
        "status": _report_status(rows),
        "claim_count": _count_decimal(len(rows)),
        "pass_claim_count": _status_count(rows, STATUS_PASS),
        "watch_claim_count": _status_count(rows, STATUS_WATCH),
        "block_claim_count": _status_count(rows, STATUS_BLOCK),
        "tail_claim_count": _tail_count(rows),
        "maximum_authority_claim_tail_score": max(
            (row.authority_claim_tail_score for row in rows),
            default=ZERO,
        ),
        "average_authority_claim_tail_score": _average(
            row.authority_claim_tail_score for row in rows
        ),
        "average_authority_confidence": _average(
            row.authority_confidence for row in rows
        ),
        "minimum_authority_quorum_ratio": min(
            (row.authority_quorum_ratio for row in rows),
            default=ZERO,
        ),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "reason_code_counts": _reason_code_counts(rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    payload = _payload_value(values)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    values["derived_validation_digest"] = _derived_validation_digest(payload)
    return ResearchEventResolutionAuthorityClaimTailReport(**values)


def research_event_resolution_authority_claim_tail_report_digest(
    report: ResearchEventResolutionAuthorityClaimTailReport,
) -> str:
    _require_exact_type(
        report,
        ResearchEventResolutionAuthorityClaimTailReport,
        "report",
    )
    _require_hard_flags("report", report)
    return _derived_validation_digest(_payload_value(report))


def validate_research_event_resolution_authority_claim_tail_report_digest(
    report: ResearchEventResolutionAuthorityClaimTailReport,
) -> bool:
    _require_exact_type(
        report,
        ResearchEventResolutionAuthorityClaimTailReport,
        "report",
    )
    _require_hard_flags("report", report)
    _require_matching_digest(_payload_value(report))
    return True


def research_event_resolution_authority_claim_tail_report_payload(
    report: ResearchEventResolutionAuthorityClaimTailReport,
) -> dict[str, Any]:
    _require_exact_type(
        report,
        ResearchEventResolutionAuthorityClaimTailReport,
        "report",
    )
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_bad_public("payload", payload)
    _require_matching_digest(payload)
    return payload


def validate_research_event_resolution_authority_claim_tail_report_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    _reject_bad_public("public payload", payload)
    _require_payload_hard_flags(payload)
    _require_payload_status_values(payload)
    _require_matching_digest(payload)
    return True


def _row_for_observation(
    observation: ResearchEventResolutionAuthorityClaimTailObservation,
    config: ResearchEventResolutionAuthorityClaimTailConfig,
) -> ResearchEventResolutionAuthorityClaimTailRow:
    authority_quorum_ratio = _clamp_ratio(
        observation.matched_authority_count / observation.required_authority_count,
    )
    claim_age_tail_pressure = _clamp_ratio(
        observation.claim_age_seconds / config.watch_claim_age_seconds,
    )
    authority_delay_tail_pressure = _clamp_ratio(
        observation.authority_delay_seconds / config.watch_authority_delay_seconds,
    )
    confidence_gap_tail_pressure = _clamp_ratio(ONE - observation.authority_confidence)
    authority_quorum_tail_pressure = _clamp_ratio(ONE - authority_quorum_ratio)
    reason_codes = _row_reason_codes(
        observation=observation,
        authority_quorum_ratio=authority_quorum_ratio,
        config=config,
    )
    return ResearchEventResolutionAuthorityClaimTailRow(
        rank=ONE,
        event_trace_hash=_private_hash(observation.private_event_ref),
        claim_trace_hash=_private_hash(observation.private_claim_ref),
        authority_trace_hash=_private_hash(observation.private_authority_ref),
        claim_age_seconds=observation.claim_age_seconds,
        authority_delay_seconds=observation.authority_delay_seconds,
        authority_confidence=observation.authority_confidence,
        claim_conflict_pressure=observation.claim_conflict_pressure,
        matched_authority_count=observation.matched_authority_count,
        required_authority_count=observation.required_authority_count,
        authority_quorum_ratio=authority_quorum_ratio,
        claim_age_tail_pressure=claim_age_tail_pressure,
        authority_delay_tail_pressure=authority_delay_tail_pressure,
        confidence_gap_tail_pressure=confidence_gap_tail_pressure,
        authority_quorum_tail_pressure=authority_quorum_tail_pressure,
        authority_claim_tail_score=_average(
            (
                claim_age_tail_pressure,
                authority_delay_tail_pressure,
                confidence_gap_tail_pressure,
                observation.claim_conflict_pressure,
                authority_quorum_tail_pressure,
            ),
        ),
        status=_status_from_row_reasons(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    observation: ResearchEventResolutionAuthorityClaimTailObservation,
    authority_quorum_ratio: Decimal,
    config: ResearchEventResolutionAuthorityClaimTailConfig,
) -> tuple[str, ...]:
    details: list[str] = []
    _append_ceiling_reason(
        details,
        observation.claim_age_seconds,
        config.pass_claim_age_seconds,
        config.watch_claim_age_seconds,
        CLAIM_AGE_WATCH_REASON,
        CLAIM_AGE_BLOCK_REASON,
    )
    _append_ceiling_reason(
        details,
        observation.authority_delay_seconds,
        config.pass_authority_delay_seconds,
        config.watch_authority_delay_seconds,
        AUTHORITY_DELAY_WATCH_REASON,
        AUTHORITY_DELAY_BLOCK_REASON,
    )
    _append_floor_reason(
        details,
        observation.authority_confidence,
        config.min_pass_authority_confidence,
        config.min_watch_authority_confidence,
        AUTHORITY_CONFIDENCE_WATCH_REASON,
        AUTHORITY_CONFIDENCE_BLOCK_REASON,
    )
    _append_ceiling_reason(
        details,
        observation.claim_conflict_pressure,
        config.max_pass_claim_conflict_pressure,
        config.max_watch_claim_conflict_pressure,
        CLAIM_CONFLICT_WATCH_REASON,
        CLAIM_CONFLICT_BLOCK_REASON,
    )
    _append_floor_reason(
        details,
        authority_quorum_ratio,
        config.min_pass_authority_quorum_ratio,
        config.min_watch_authority_quorum_ratio,
        AUTHORITY_QUORUM_WATCH_REASON,
        AUTHORITY_QUORUM_BLOCK_REASON,
    )
    if any(reason.endswith("_block") for reason in details):
        return (BLOCK_REASON, *tuple(details))
    if details:
        return (WATCH_REASON, *tuple(details))
    return (PASS_REASON,)


def _append_ceiling_reason(
    details: list[str],
    value: Decimal,
    pass_ceiling: Decimal,
    watch_ceiling: Decimal,
    watch_reason: str,
    block_reason: str,
) -> None:
    if value > watch_ceiling:
        details.append(block_reason)
        return
    if value > pass_ceiling:
        details.append(watch_reason)


def _append_floor_reason(
    details: list[str],
    value: Decimal,
    pass_floor: Decimal,
    watch_floor: Decimal,
    watch_reason: str,
    block_reason: str,
) -> None:
    if value < watch_floor:
        details.append(block_reason)
        return
    if value < pass_floor:
        details.append(watch_reason)


def _normalize_observations(
    observations: Iterable[ResearchEventResolutionAuthorityClaimTailObservation],
) -> tuple[ResearchEventResolutionAuthorityClaimTailObservation, ...]:
    items = tuple(observations)
    seen: set[tuple[str, str, str]] = set()
    for item in items:
        _require_exact_type(
            item,
            ResearchEventResolutionAuthorityClaimTailObservation,
            "observation",
        )
        _require_hard_flags("observation", item)
        key = (
            _private_hash(item.private_event_ref),
            _private_hash(item.private_claim_ref),
            _private_hash(item.private_authority_ref),
        )
        if key in seen:
            raise ValueError("duplicate authority claim traces are not allowed")
        seen.add(key)
    return items


def _sorted_rows(
    rows: tuple[ResearchEventResolutionAuthorityClaimTailRow, ...],
) -> tuple[ResearchEventResolutionAuthorityClaimTailRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                STATUS_RANK[row.status],
                -row.authority_claim_tail_score,
                row.event_trace_hash,
                row.claim_trace_hash,
                row.authority_trace_hash,
            ),
        ),
    )


def _ranked_row(
    index: int,
    row: ResearchEventResolutionAuthorityClaimTailRow,
) -> ResearchEventResolutionAuthorityClaimTailRow:
    return ResearchEventResolutionAuthorityClaimTailRow(
        rank=_count_decimal(index),
        event_trace_hash=row.event_trace_hash,
        claim_trace_hash=row.claim_trace_hash,
        authority_trace_hash=row.authority_trace_hash,
        claim_age_seconds=row.claim_age_seconds,
        authority_delay_seconds=row.authority_delay_seconds,
        authority_confidence=row.authority_confidence,
        claim_conflict_pressure=row.claim_conflict_pressure,
        matched_authority_count=row.matched_authority_count,
        required_authority_count=row.required_authority_count,
        authority_quorum_ratio=row.authority_quorum_ratio,
        claim_age_tail_pressure=row.claim_age_tail_pressure,
        authority_delay_tail_pressure=row.authority_delay_tail_pressure,
        confidence_gap_tail_pressure=row.confidence_gap_tail_pressure,
        authority_quorum_tail_pressure=row.authority_quorum_tail_pressure,
        authority_claim_tail_score=row.authority_claim_tail_score,
        status=row.status,
        reason_codes=row.reason_codes,
    )


def _reason_code_counts(
    rows: tuple[ResearchEventResolutionAuthorityClaimTailRow, ...],
) -> tuple[ResearchEventResolutionAuthorityClaimTailReasonCodeCount, ...]:
    if not rows:
        return ()
    totals: dict[str, Decimal] = {}
    for row in rows:
        for reason in row.reason_codes:
            totals[reason] = totals.get(reason, ZERO) + ONE
    denominator = Decimal(len(rows))
    return tuple(
        ResearchEventResolutionAuthorityClaimTailReasonCodeCount(
            reason_code=reason,
            count=_six(count),
            input_ratio=_six(count / denominator),
        )
        for reason, count in sorted(
            totals.items(),
            key=lambda item: ROW_REASON_INDEX[item[0]],
        )
    )


def _report_status(rows: tuple[ResearchEventResolutionAuthorityClaimTailRow, ...]) -> str:
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchEventResolutionAuthorityClaimTailRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    reasons: list[str] = []
    if any(row.status == STATUS_BLOCK for row in rows):
        reasons.append(BLOCK_REASON)
    if any(row.status == STATUS_WATCH for row in rows):
        reasons.append(WATCH_REASON)
    if any(row.status == STATUS_PASS for row in rows):
        reasons.append(PASS_REASON)
    return tuple(reasons)


def _status_count(
    rows: tuple[ResearchEventResolutionAuthorityClaimTailRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _tail_count(rows: tuple[ResearchEventResolutionAuthorityClaimTailRow, ...]) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status != STATUS_PASS))


def _average(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return _six(sum(items, ZERO) / Decimal(len(items)))


def _validate_report(report: ResearchEventResolutionAuthorityClaimTailReport) -> None:
    rows = report.rows
    _require_decimal_equal("claim_count", report.claim_count, _count_decimal(len(rows)))
    _require_decimal_equal(
        "pass_claim_count",
        report.pass_claim_count,
        _status_count(rows, STATUS_PASS),
    )
    _require_decimal_equal(
        "watch_claim_count",
        report.watch_claim_count,
        _status_count(rows, STATUS_WATCH),
    )
    _require_decimal_equal(
        "block_claim_count",
        report.block_claim_count,
        _status_count(rows, STATUS_BLOCK),
    )
    _require_decimal_equal(
        "tail_claim_count",
        report.tail_claim_count,
        _tail_count(rows),
    )
    _require_decimal_equal(
        "maximum_authority_claim_tail_score",
        report.maximum_authority_claim_tail_score,
        max((row.authority_claim_tail_score for row in rows), default=ZERO),
    )
    _require_decimal_equal(
        "average_authority_claim_tail_score",
        report.average_authority_claim_tail_score,
        _average(row.authority_claim_tail_score for row in rows),
    )
    _require_decimal_equal(
        "average_authority_confidence",
        report.average_authority_confidence,
        _average(row.authority_confidence for row in rows),
    )
    _require_decimal_equal(
        "minimum_authority_quorum_ratio",
        report.minimum_authority_quorum_ratio,
        min((row.authority_quorum_ratio for row in rows), default=ZERO),
    )
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _require_decimal_equal(field_name: str, actual: Decimal, expected: Decimal) -> None:
    if actual != expected:
        raise ValueError(f"{field_name} must match rows")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _six(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _count_decimal(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _six(Decimal(value))


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _six(value)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _six(value: Decimal) -> Decimal:
    return value.quantize(SIX, rounding=ROUND_HALF_UP)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a str")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    _reject_bad_public(field_name, normalized)
    return normalized


def _require_private_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a str")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    return normalized


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_lower_ceiling(
    lower_name: str,
    lower_value: Decimal,
    upper_name: str,
    upper_value: Decimal,
) -> None:
    if lower_value >= upper_value:
        raise ValueError(f"{lower_name} must be less than {upper_name}")


def _require_higher_floor(
    higher_name: str,
    higher_value: Decimal,
    lower_name: str,
    lower_value: Decimal,
) -> None:
    if higher_value <= lower_value:
        raise ValueError(f"{higher_name} must exceed {lower_name}")


def _require_status(value: object) -> str:
    if type(value) is not str or value not in RESEARCH_EVENT_RESOLUTION_AUTHORITY_CLAIM_TAIL_REPORT_STATUSES:
        raise ValueError("status must be pass, watch, or block")
    return value


def _require_reason_code(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a str")
    if value not in allowed:
        raise ValueError(f"{field_name} is not allowed")
    return value


def _require_reason_codes(
    field_name: str,
    values: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not values:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(_require_reason_code(field_name, value, allowed) for value in values)


def _require_reason_code_counts(
    values: object,
) -> tuple[ResearchEventResolutionAuthorityClaimTailReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for value in values:
        _require_exact_type(
            value,
            ResearchEventResolutionAuthorityClaimTailReasonCodeCount,
            "reason_code_count",
        )
    return values


def _require_rows(
    values: object,
) -> tuple[ResearchEventResolutionAuthorityClaimTailRow, ...]:
    if type(values) is not tuple:
        raise ValueError("rows must be a tuple")
    for value in values:
        _require_exact_type(value, ResearchEventResolutionAuthorityClaimTailRow, "row")
    return values


def _status_from_row_reasons(reason_codes: tuple[str, ...]) -> str:
    if reason_codes[0] == BLOCK_REASON:
        return STATUS_BLOCK
    if reason_codes[0] == WATCH_REASON:
        return STATUS_WATCH
    if reason_codes[0] == PASS_REASON:
        return STATUS_PASS
    raise ValueError("reason_codes must start with a status reason")


def _require_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a str")
    if len(value) != SHA256_HEX_LENGTH:
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a SHA-256 hex digest") from exc
    if value.lower() != value:
        raise ValueError(f"{field_name} must be lowercase")
    return value


def _private_hash(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _payload_value(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("Decimal value must be exact")
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(_six(value))
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("datetime value must be exact")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or type(value) is float:
        raise ValueError("public payload must use Decimal-derived strings")
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            ready[key] = _payload_value(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_payload_value(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_bad_public(label: str, value: object) -> None:
    if type(value) is str:
        normalized = value.lower()
        if any(fragment in normalized for fragment in BAD_PUBLIC_FRAGMENTS):
            raise ValueError(f"unsafe public surface in {label}")
        return
    if type(value) is int or type(value) is float or type(value) is Decimal:
        raise ValueError(f"{label} must not contain numeric objects")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_bad_public(label, key)
            _reject_bad_public(label, item)
        return
    if isinstance(value, list) or isinstance(value, tuple):
        for item in value:
            _reject_bad_public(label, item)


def _require_payload_hard_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"payload {field_name} must be True")
    _require_nested_payload_hard_flags(payload)


def _require_nested_payload_hard_flags(payload: Any) -> None:
    if isinstance(payload, dict):
        for field_name in ("paper_only", "report_only", "readonly"):
            if field_name in payload and payload[field_name] is not True:
                raise ValueError(f"payload {field_name} must be True")
        for item in payload.values():
            _require_nested_payload_hard_flags(item)
        return
    if isinstance(payload, list):
        for item in payload:
            _require_nested_payload_hard_flags(item)


def _require_payload_status_values(payload: Any) -> None:
    if isinstance(payload, dict):
        if "status" in payload and payload["status"] not in (
            STATUS_PASS,
            STATUS_WATCH,
            STATUS_BLOCK,
        ):
            raise ValueError("payload status must be pass, watch, or block")
        for item in payload.values():
            _require_payload_status_values(item)
        return
    if isinstance(payload, list):
        for item in payload:
            _require_payload_status_values(item)


def _derived_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(
        digest_payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _require_matching_digest(payload: Any) -> None:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    expected = _derived_validation_digest(payload)
    actual = payload.get("derived_validation_digest")
    if actual != expected:
        raise ValueError("derived_validation_digest must match payload")
