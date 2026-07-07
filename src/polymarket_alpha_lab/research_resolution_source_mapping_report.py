"""Pure report for resolution source mapping coverage."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any


ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
VALUE_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

DEFAULT_CONFIG_VERSION = "research-resolution-source-mapping-report-v0"

SOURCE_ROLES = ("official", "alternate", "ambiguous")
REVIEW_STATUSES = ("reviewed", "pending_review", "escalated_review")
REPORT_STATUSES = ("pass", "watch", "block")

PASS_REASON = "resolution_source_mapping_pass"
NO_SOURCES_REASON = "no_resolution_sources"
AMBIGUOUS_REASON = "ambiguous_sources_present"
EVIDENCE_GAP_REASON = "evidence_gap_present"
MISSING_OFFICIAL_REASON = "missing_official_source"
REVIEW_ESCALATED_REASON = "review_escalated"
REVIEW_PENDING_REASON = "review_pending"
REVIEW_COVERAGE_REASON = "review_coverage_gap"

REASON_CODE_PRIORITY = (
    PASS_REASON,
    NO_SOURCES_REASON,
    AMBIGUOUS_REASON,
    EVIDENCE_GAP_REASON,
    MISSING_OFFICIAL_REASON,
    REVIEW_ESCALATED_REASON,
    REVIEW_PENDING_REASON,
    REVIEW_COVERAGE_REASON,
)
REASON_CODES = frozenset(REASON_CODE_PRIORITY)
BLOCK_REASONS = frozenset(
    (
        EVIDENCE_GAP_REASON,
        MISSING_OFFICIAL_REASON,
        REVIEW_ESCALATED_REASON,
        NO_SOURCES_REASON,
    ),
)

UNSAFE_PUBLIC_FRAGMENTS = (
    "http://",
    "https://",
    "www.",
    "url",
    "raw_market",
    "market_id",
    "market-",
    "market_",
    "raw market",
    "reference",
    " ref ",
    "\n",
    "\r",
    "\t",
)


@dataclass(frozen=True)
class ResearchResolutionSourceMappingConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    min_official_source_count: Decimal = Decimal("1")
    min_reviewed_source_count: Decimal = Decimal("1")
    max_ambiguous_source_count: Decimal = Decimal("0")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchResolutionSourceMappingConfig:
            raise TypeError(
                "ResearchResolutionSourceMappingConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ResearchResolutionSourceMappingConfig)
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported version")
        for field_name in (
            "min_official_source_count",
            "min_reviewed_source_count",
            "max_ambiguous_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", _payload_value(self))


@dataclass(frozen=True)
class ResearchResolutionSourceMappingEvidence:
    event_key: str
    source_key: str
    source_family: str
    source_role: str
    observed_at: datetime
    evidence_score: Decimal
    review_status: str
    evidence_gap: bool = False
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchResolutionSourceMappingEvidence:
            raise TypeError(
                "ResearchResolutionSourceMappingEvidence does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("evidence", self, ResearchResolutionSourceMappingEvidence)
        for field_name in ("event_key", "source_key", "source_family"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_member("source_role", self.source_role, SOURCE_ROLES)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "evidence_score",
            _normalize_probability("evidence_score", self.evidence_score),
        )
        _require_member("review_status", self.review_status, REVIEW_STATUSES)
        _require_bool("evidence_gap", self.evidence_gap)
        _require_hard_flags("evidence", self)
        _reject_unsafe_public_payload("evidence", _payload_value(self))


@dataclass(frozen=True)
class ResearchResolutionSourceMappingRow:
    event_key: str
    source_count: Decimal
    official_source_count: Decimal
    alternate_source_count: Decimal
    ambiguous_source_count: Decimal
    evidence_gap_count: Decimal
    reviewed_source_count: Decimal
    pending_review_count: Decimal
    escalated_review_count: Decimal
    average_evidence_score: Decimal
    latest_observed_at: datetime
    latest_source_age_seconds: Decimal
    review_status: str
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchResolutionSourceMappingRow:
            raise TypeError(
                "ResearchResolutionSourceMappingRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchResolutionSourceMappingRow)
        _require_public_string("event_key", self.event_key)
        for field_name in (
            "source_count",
            "official_source_count",
            "alternate_source_count",
            "ambiguous_source_count",
            "evidence_gap_count",
            "reviewed_source_count",
            "pending_review_count",
            "escalated_review_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_evidence_score",
            _normalize_probability("average_evidence_score", self.average_evidence_score),
        )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        object.__setattr__(
            self,
            "latest_source_age_seconds",
            _normalize_nonnegative_decimal(
                "latest_source_age_seconds",
                self.latest_source_age_seconds,
            ),
        )
        _require_member("review_status", self.review_status, REVIEW_STATUSES)
        _require_member("status", self.status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)
        _validate_row(self)
        _reject_unsafe_public_payload("row", _payload_value(self))


@dataclass(frozen=True)
class ResearchResolutionSourceMappingReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchResolutionSourceMappingReasonCodeCount:
            raise TypeError(
                "ResearchResolutionSourceMappingReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "reason_code_count",
            self,
            ResearchResolutionSourceMappingReasonCodeCount,
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_count("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", _payload_value(self))


@dataclass(frozen=True)
class ResearchResolutionSourceMappingReport:
    generated_at: datetime
    config_version: str
    event_count: Decimal
    source_count: Decimal
    official_source_count: Decimal
    alternate_source_count: Decimal
    ambiguous_source_count: Decimal
    evidence_gap_count: Decimal
    reviewed_source_count: Decimal
    pending_review_count: Decimal
    escalated_review_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_evidence_score: Decimal | None
    status: str
    rows: tuple[ResearchResolutionSourceMappingRow, ...]
    reason_code_counts: tuple[ResearchResolutionSourceMappingReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchResolutionSourceMappingReport:
            raise TypeError(
                "ResearchResolutionSourceMappingReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchResolutionSourceMappingReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "event_count",
            "source_count",
            "official_source_count",
            "alternate_source_count",
            "ambiguous_source_count",
            "evidence_gap_count",
            "reviewed_source_count",
            "pending_review_count",
            "escalated_review_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_evidence_score",
            _normalize_optional_probability(
                "average_evidence_score",
                self.average_evidence_score,
            ),
        )
        _require_member("status", self.status, REPORT_STATUSES)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("report", _payload_value(self))
        _set_or_validate_derived_validation_digest(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_resolution_source_mapping_report_payload(self)


def build_research_resolution_source_mapping_report(
    evidence_sources: Iterable[ResearchResolutionSourceMappingEvidence],
    *,
    config: ResearchResolutionSourceMappingConfig,
    generated_at: datetime,
) -> ResearchResolutionSourceMappingReport:
    if type(config) is not ResearchResolutionSourceMappingConfig:
        raise ValueError("config must be a ResearchResolutionSourceMappingConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    evidence_rows = _normalize_evidence_sources(
        evidence_sources,
        generated_at=generated_at_utc,
    )
    grouped: dict[str, list[ResearchResolutionSourceMappingEvidence]] = {}
    for evidence in evidence_rows:
        grouped.setdefault(evidence.event_key, []).append(evidence)

    rows = tuple(
        _row_for_event(
            event_key,
            tuple(grouped[event_key]),
            config=config,
            generated_at=generated_at_utc,
        )
        for event_key in sorted(grouped)
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchResolutionSourceMappingReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        event_count=_count(len(rows)),
        source_count=sum((row.source_count for row in rows), ZERO),
        official_source_count=sum((row.official_source_count for row in rows), ZERO),
        alternate_source_count=sum((row.alternate_source_count for row in rows), ZERO),
        ambiguous_source_count=sum((row.ambiguous_source_count for row in rows), ZERO),
        evidence_gap_count=sum((row.evidence_gap_count for row in rows), ZERO),
        reviewed_source_count=sum((row.reviewed_source_count for row in rows), ZERO),
        pending_review_count=sum((row.pending_review_count for row in rows), ZERO),
        escalated_review_count=sum((row.escalated_review_count for row in rows), ZERO),
        pass_count=_count(_status_count(rows, "pass")),
        watch_count=_count(_status_count(rows, "watch")),
        block_count=_count(_status_count(rows, "block")),
        average_evidence_score=_average_report_score(evidence_rows),
        status=_status_from_reason_codes(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_resolution_source_mapping_report_payload(
    report: ResearchResolutionSourceMappingReport,
) -> dict[str, Any]:
    if type(report) is not ResearchResolutionSourceMappingReport:
        raise ValueError("report must be a ResearchResolutionSourceMappingReport")
    _validate_report(report)
    _validate_derived_validation_digest(report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a dict")
    validate_research_resolution_source_mapping_public_payload(payload)
    return dict(payload)


def validate_research_resolution_source_mapping_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("public payload", payload)
    _require_public_payload_flags(payload)
    digest = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    if digest != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    return True


def _row_for_event(
    event_key: str,
    evidence_rows: tuple[ResearchResolutionSourceMappingEvidence, ...],
    *,
    config: ResearchResolutionSourceMappingConfig,
    generated_at: datetime,
) -> ResearchResolutionSourceMappingRow:
    latest_observed_at = max(evidence.observed_at for evidence in evidence_rows)
    reason_codes = _row_reason_codes(evidence_rows, config=config)
    review_status = _review_status(evidence_rows)
    return ResearchResolutionSourceMappingRow(
        event_key=event_key,
        source_count=_count(len(evidence_rows)),
        official_source_count=_count(
            sum(1 for evidence in evidence_rows if evidence.source_role == "official"),
        ),
        alternate_source_count=_count(
            sum(1 for evidence in evidence_rows if evidence.source_role == "alternate"),
        ),
        ambiguous_source_count=_count(
            sum(1 for evidence in evidence_rows if evidence.source_role == "ambiguous"),
        ),
        evidence_gap_count=_count(sum(1 for evidence in evidence_rows if evidence.evidence_gap)),
        reviewed_source_count=_count(
            sum(1 for evidence in evidence_rows if evidence.review_status == "reviewed"),
        ),
        pending_review_count=_count(
            sum(1 for evidence in evidence_rows if evidence.review_status == "pending_review"),
        ),
        escalated_review_count=_count(
            sum(
                1
                for evidence in evidence_rows
                if evidence.review_status == "escalated_review"
            ),
        ),
        average_evidence_score=_average_evidence_score(evidence_rows),
        latest_observed_at=latest_observed_at,
        latest_source_age_seconds=_seconds_between(latest_observed_at, generated_at),
        review_status=review_status,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    evidence_rows: tuple[ResearchResolutionSourceMappingEvidence, ...],
    *,
    config: ResearchResolutionSourceMappingConfig,
) -> tuple[str, ...]:
    official_count = _count(
        sum(1 for evidence in evidence_rows if evidence.source_role == "official"),
    )
    ambiguous_count = _count(
        sum(1 for evidence in evidence_rows if evidence.source_role == "ambiguous"),
    )
    reviewed_count = _count(
        sum(1 for evidence in evidence_rows if evidence.review_status == "reviewed"),
    )
    pending_count = _count(
        sum(1 for evidence in evidence_rows if evidence.review_status == "pending_review"),
    )
    escalated_count = _count(
        sum(1 for evidence in evidence_rows if evidence.review_status == "escalated_review"),
    )
    gap_count = _count(sum(1 for evidence in evidence_rows if evidence.evidence_gap))

    reasons: list[str] = []
    if ambiguous_count > config.max_ambiguous_source_count:
        reasons.append(AMBIGUOUS_REASON)
    if gap_count > ZERO:
        reasons.append(EVIDENCE_GAP_REASON)
    if official_count < config.min_official_source_count:
        reasons.append(MISSING_OFFICIAL_REASON)
    if escalated_count > ZERO:
        reasons.append(REVIEW_ESCALATED_REASON)
    if pending_count > ZERO:
        reasons.append(REVIEW_PENDING_REASON)
    if (
        reviewed_count < config.min_reviewed_source_count
        and pending_count == ZERO
        and escalated_count == ZERO
    ):
        reasons.append(REVIEW_COVERAGE_REASON)
    if not reasons:
        return (PASS_REASON,)
    return _normalize_reason_codes("reason_codes", tuple(reasons))


def _review_status(
    evidence_rows: tuple[ResearchResolutionSourceMappingEvidence, ...],
) -> str:
    if any(evidence.review_status == "escalated_review" for evidence in evidence_rows):
        return "escalated_review"
    if any(evidence.review_status == "pending_review" for evidence in evidence_rows):
        return "pending_review"
    return "reviewed"


def _report_reason_codes(
    rows: tuple[ResearchResolutionSourceMappingRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_SOURCES_REASON,)
    active_reasons: list[str] = []
    for row in rows:
        active_reasons.extend(
            reason for reason in row.reason_codes if reason != PASS_REASON
        )
    if not active_reasons:
        return (PASS_REASON,)
    return _normalize_reason_codes("reason_codes", tuple(active_reasons))


def _reason_code_counts(
    rows: tuple[ResearchResolutionSourceMappingRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchResolutionSourceMappingReasonCodeCount, ...]:
    if reason_codes == (NO_SOURCES_REASON,):
        return (
            ResearchResolutionSourceMappingReasonCodeCount(
                reason_code=NO_SOURCES_REASON,
                count=_count(1),
            ),
        )
    active_reasons: list[str] = []
    for row in rows:
        active_reasons.extend(
            reason for reason in row.reason_codes if reason != PASS_REASON
        )
    if not active_reasons:
        return (
            ResearchResolutionSourceMappingReasonCodeCount(
                reason_code=PASS_REASON,
                count=_count(len(rows)),
            ),
        )
    return tuple(
        ResearchResolutionSourceMappingReasonCodeCount(
            reason_code=reason_code,
            count=_count(active_reasons.count(reason_code)),
        )
        for reason_code in _normalize_reason_codes("reason_codes", tuple(active_reasons))
    )


def _normalize_evidence_sources(
    value: Iterable[ResearchResolutionSourceMappingEvidence],
    *,
    generated_at: datetime,
) -> tuple[ResearchResolutionSourceMappingEvidence, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("evidence_sources must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("evidence_sources must be an iterable") from exc
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchResolutionSourceMappingEvidence:
            raise ValueError(
                "evidence_sources must contain ResearchResolutionSourceMappingEvidence values",
            )
        _require_hard_flags("evidence", row)
        if row.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        key = (row.event_key, row.source_key)
        if key in seen_keys:
            raise ValueError("event_key and source_key pairs must be unique")
        seen_keys.add(key)
    return tuple(sorted(rows, key=_evidence_sort_key))


def _normalize_rows(
    value: Iterable[ResearchResolutionSourceMappingRow],
) -> tuple[ResearchResolutionSourceMappingRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_keys: set[str] = set()
    for row in rows:
        if type(row) is not ResearchResolutionSourceMappingRow:
            raise ValueError("rows must contain ResearchResolutionSourceMappingRow values")
        _require_hard_flags("row", row)
        if row.event_key in seen_keys:
            raise ValueError("row event_key values must be unique")
        seen_keys.add(row.event_key)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.event_key))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted deterministically")
    return rows


def _normalize_reason_code_counts(
    value: Iterable[ResearchResolutionSourceMappingReasonCodeCount],
) -> tuple[ResearchResolutionSourceMappingReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen_codes: set[str] = set()
    for row in rows:
        if type(row) is not ResearchResolutionSourceMappingReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchResolutionSourceMappingReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", row)
        if row.reason_code in seen_codes:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen_codes.add(row.reason_code)
    sorted_rows = tuple(sorted(rows, key=lambda row: REASON_CODE_PRIORITY.index(row.reason_code)))
    if rows != sorted_rows:
        raise ValueError("reason_code_counts must be sorted deterministically")
    return rows


def _validate_row(row: ResearchResolutionSourceMappingRow) -> None:
    source_sum = (
        row.official_source_count
        + row.alternate_source_count
        + row.ambiguous_source_count
    )
    if row.source_count != source_sum:
        raise ValueError("source_count must match source role counts")
    review_sum = (
        row.reviewed_source_count
        + row.pending_review_count
        + row.escalated_review_count
    )
    if row.source_count != review_sum:
        raise ValueError("source_count must match review counts")
    if row.evidence_gap_count > row.source_count:
        raise ValueError("evidence_gap_count must not exceed source_count")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.review_status == "reviewed" and row.pending_review_count + row.escalated_review_count:
        raise ValueError("review_status must match review counts")
    if row.review_status == "pending_review" and row.pending_review_count == ZERO:
        raise ValueError("review_status must match pending_review_count")
    if row.review_status == "escalated_review" and row.escalated_review_count == ZERO:
        raise ValueError("review_status must match escalated_review_count")


def _validate_report(report: ResearchResolutionSourceMappingReport) -> None:
    rows = report.rows
    if report.event_count != _count(len(rows)):
        raise ValueError("event_count must match rows")
    for field_name in (
        "source_count",
        "official_source_count",
        "alternate_source_count",
        "ambiguous_source_count",
        "evidence_gap_count",
        "reviewed_source_count",
        "pending_review_count",
        "escalated_review_count",
    ):
        if getattr(report, field_name) != sum(
            (getattr(row, field_name) for row in rows),
            ZERO,
        ):
            raise ValueError(f"{field_name} must match rows")
    if report.pass_count != _count(_status_count(rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(_status_count(rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(_status_count(rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_evidence_score != _average_rows_score(rows):
        raise ValueError("average_evidence_score must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _status_from_reason_codes(report.reason_codes):
        raise ValueError("status must match reason_codes")
    if report.reason_code_counts != _reason_code_counts(rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _average_evidence_score(
    rows: tuple[ResearchResolutionSourceMappingEvidence, ...],
) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability(
            "average_evidence_score",
            sum((row.evidence_score for row in rows), ZERO) / Decimal(len(rows)),
        )


def _average_report_score(
    rows: tuple[ResearchResolutionSourceMappingEvidence, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _average_evidence_score(rows)


def _average_rows_score(
    rows: tuple[ResearchResolutionSourceMappingRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    total_sources = sum((row.source_count for row in rows), ZERO)
    if total_sources == ZERO:
        return None
    with localcontext(DECIMAL_CONTEXT):
        weighted = sum(
            (row.average_evidence_score * row.source_count for row in rows),
            ZERO,
        )
        return _normalize_probability("average_evidence_score", weighted / total_sources)


def _status_count(
    rows: tuple[ResearchResolutionSourceMappingRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (PASS_REASON,):
        return "pass"
    if any(reason in BLOCK_REASONS for reason in reason_codes):
        return "block"
    return "watch"


def _set_or_validate_derived_validation_digest(
    report: ResearchResolutionSourceMappingReport,
) -> None:
    current = report.derived_validation_digest
    expected = _derived_validation_digest(report)
    if current == "":
        object.__setattr__(report, "derived_validation_digest", expected)
        return
    _require_sha256_digest("derived_validation_digest", current)
    if current != expected:
        raise ValueError("derived_validation_digest must match report fields")


def _validate_derived_validation_digest(
    report: ResearchResolutionSourceMappingReport,
) -> None:
    current = _require_sha256_digest(
        "derived_validation_digest",
        report.derived_validation_digest,
    )
    if current != _derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _derived_validation_digest(value: object) -> str:
    payload = _without_derived_validation_digest(_payload_value(value))
    encoded = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _without_derived_validation_digest(value: object) -> object:
    if type(value) is dict:
        return {
            key: _without_derived_validation_digest(item)
            for key, item in value.items()
            if key != "derived_validation_digest"
        }
    if type(value) is list:
        return [_without_derived_validation_digest(item) for item in value]
    return value


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload values must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is tuple or type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    return value


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    current_path = path or label
    if value is None or type(value) is bool:
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if isinstance(value, (Decimal, int, float)):
        raise ValueError(f"{current_path} must use Decimal strings, not numeric values")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            item_path = key if not path else f"{path}.{key}"
            if key in ("paper_only", "report_only", "readonly") and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) is list:
        for index, item in enumerate(value):
            item_path = f"{current_path}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError(f"{current_path} is not public JSON serializable")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    if _has_unsafe_public_fragment(key):
        raise ValueError(f"unsafe public payload key in {path}: {key}")


def _reject_unsafe_public_string(path: str, value: str) -> None:
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"unsafe public payload value in {path}")


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    return _normalize_nonnegative_decimal(
        "latest_source_age_seconds",
        Decimal(str((end - start).total_seconds())),
    )


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(VALUE_QUANTUM)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return normalized


def _normalize_optional_probability(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_probability(field_name, value)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal count")
    normalized = value.quantize(COUNT_QUANTUM)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_reason_codes(field_name: str, value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of reason codes")
    try:
        codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of reason codes") from exc
    if not codes:
        raise ValueError(f"{field_name} must not be empty")
    for code in codes:
        _require_reason_code(field_name, code)
    active_codes = [code for code in codes if code != PASS_REASON]
    if PASS_REASON in codes and active_codes:
        raise ValueError(f"{field_name} pass reason must stand alone")
    if NO_SOURCES_REASON in codes and len(codes) != 1:
        raise ValueError(f"{field_name} no-source reason must stand alone")
    return tuple(sorted(set(codes), key=REASON_CODE_PRIORITY.index))


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODES:
        raise ValueError(f"{field_name} must contain known reason codes")


def _require_member(field_name: str, value: object, members: tuple[str, ...]) -> None:
    if type(value) is not str or value not in members:
        raise ValueError(f"{field_name} must be one of {members}")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{field_name} must be a canonical string")
    _reject_unsafe_public_string(field_name, value)


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _evidence_sort_key(
    evidence: ResearchResolutionSourceMappingEvidence,
) -> tuple[str, str, str, str]:
    return (
        evidence.event_key,
        evidence.source_family,
        evidence.source_role,
        evidence.source_key,
    )


__all__ = (
    "ResearchResolutionSourceMappingConfig",
    "ResearchResolutionSourceMappingEvidence",
    "ResearchResolutionSourceMappingReasonCodeCount",
    "ResearchResolutionSourceMappingReport",
    "ResearchResolutionSourceMappingRow",
    "build_research_resolution_source_mapping_report",
    "research_resolution_source_mapping_report_payload",
    "validate_research_resolution_source_mapping_public_payload",
)
