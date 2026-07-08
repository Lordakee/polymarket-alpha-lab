"""Pure report-only reducer for research-team review quality exceptions."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any, Iterable


DEFAULT_RESEARCH_TEAM_REVIEW_QUALITY_EXCEPTION_REPORT_CONFIG_VERSION = (
    "research-team-review-quality-exception-report-v0"
)

_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_QUANT = Decimal("0.000001")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[a-z][a-z0-9_]{2,63}$")
_PUBLIC_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_STATUSES = ("pass", "watch", "block")
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_UNSAFE_PUBLIC_TERMS = (
    "raw",
    "event",
    "market",
    "source",
    "question",
    "slug",
    "url",
    "dsn",
    "table",
    "token",
    "secret",
    "auth",
    "wallet",
    "order",
    "trade",
    "buy",
    "sell",
    "recommendation",
    "sizing",
    "position",
)
_UNSAFE_PRIVATE_REFERENCE_TERMS = (
    "://",
    "postgres:",
    "postgresql:",
    "wallet",
    "auth",
    "order",
    "trade",
    "sizing",
    "recommendation",
    "token",
    "secret",
    "private_key",
    "dsn",
    "table",
)

PASS_REASON = "review_quality_exception_pass"
EMPTY_REASON = "review_quality_exception_report_empty"
LATE_WATCH_REASON = "review_quality_exception_late_watch"
LATE_BLOCK_REASON = "review_quality_exception_late_block"
RATIONALE_WATCH_REASON = "review_quality_exception_rationale_watch"
RATIONALE_BLOCK_REASON = "review_quality_exception_rationale_block"
OUTCOME_CONFLICT_BLOCK_REASON = "review_quality_exception_outcome_conflict_block"
MEMORY_WRITEBACK_WATCH_REASON = "review_quality_exception_memory_writeback_watch"
MEMORY_WRITEBACK_BLOCK_REASON = "review_quality_exception_memory_writeback_block"
MANUAL_ESCALATION_WATCH_REASON = "review_quality_exception_manual_escalation_watch"
MANUAL_ESCALATION_BLOCK_REASON = "review_quality_exception_manual_escalation_block"

ROW_REASON_PRIORITY = (
    LATE_BLOCK_REASON,
    RATIONALE_BLOCK_REASON,
    OUTCOME_CONFLICT_BLOCK_REASON,
    MEMORY_WRITEBACK_BLOCK_REASON,
    MANUAL_ESCALATION_BLOCK_REASON,
    LATE_WATCH_REASON,
    RATIONALE_WATCH_REASON,
    MEMORY_WRITEBACK_WATCH_REASON,
    MANUAL_ESCALATION_WATCH_REASON,
    PASS_REASON,
)
REPORT_REASON_PRIORITY = (
    LATE_BLOCK_REASON,
    RATIONALE_BLOCK_REASON,
    OUTCOME_CONFLICT_BLOCK_REASON,
    MEMORY_WRITEBACK_BLOCK_REASON,
    MANUAL_ESCALATION_BLOCK_REASON,
    LATE_WATCH_REASON,
    RATIONALE_WATCH_REASON,
    MEMORY_WRITEBACK_WATCH_REASON,
    MANUAL_ESCALATION_WATCH_REASON,
    PASS_REASON,
    EMPTY_REASON,
)
BLOCK_REASONS = frozenset(
    (
        LATE_BLOCK_REASON,
        RATIONALE_BLOCK_REASON,
        OUTCOME_CONFLICT_BLOCK_REASON,
        MEMORY_WRITEBACK_BLOCK_REASON,
        MANUAL_ESCALATION_BLOCK_REASON,
    ),
)
WATCH_REASONS = frozenset(
    (
        LATE_WATCH_REASON,
        RATIONALE_WATCH_REASON,
        MEMORY_WRITEBACK_WATCH_REASON,
        MANUAL_ESCALATION_WATCH_REASON,
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_REVIEW_QUALITY_EXCEPTION_REPORT_CONFIG_VERSION",
    "ResearchTeamReviewQualityExceptionConfig",
    "ResearchTeamReviewQualityExceptionReasonCodeCount",
    "ResearchTeamReviewQualityExceptionReport",
    "ResearchTeamReviewQualityExceptionRow",
    "ResearchTeamReviewQualitySnapshot",
    "build_research_team_review_quality_exception_report",
    "research_team_review_quality_exception_report_digest",
    "research_team_review_quality_exception_report_payload",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchTeamReviewQualityExceptionConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_RESEARCH_TEAM_REVIEW_QUALITY_EXCEPTION_REPORT_CONFIG_VERSION
    late_review_watch_seconds: Decimal = Decimal("7200.000000")
    late_review_block_seconds: Decimal = Decimal("86400.000000")
    min_rationale_watch_score: Decimal = Decimal("0.700000")
    min_rationale_block_score: Decimal = Decimal("0.400000")
    memory_writeback_block_seconds: Decimal = Decimal("172800.000000")
    manual_escalation_watch_seconds: Decimal = Decimal("7200.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamReviewQualityExceptionConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_label("config_version", self.config_version),
        )
        for field_name in (
            "late_review_watch_seconds",
            "late_review_block_seconds",
            "memory_writeback_block_seconds",
            "manual_escalation_watch_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_rationale_watch_score",
            "min_rationale_block_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.late_review_watch_seconds >= self.late_review_block_seconds:
            raise ValueError(
                "late_review_watch_seconds must be less than late_review_block_seconds",
            )
        if self.min_rationale_block_score >= self.min_rationale_watch_score:
            raise ValueError(
                "min_rationale_block_score must be less than min_rationale_watch_score",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchTeamReviewQualitySnapshot(_FinalPublicDataclass):
    review_reference: str
    team_key: str
    review_due_at: datetime
    reviewed_at: datetime | None
    primary_outcome: str
    secondary_outcome: str
    rationale_score: Decimal
    memory_writeback_completed: bool
    manual_escalation_required: bool
    manual_escalation_due_at: datetime | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamReviewQualitySnapshot, "snapshot")
        _require_private_reference("review_reference", self.review_reference)
        object.__setattr__(
            self,
            "review_reference",
            _redacted_marker("review_marker_", self.review_reference),
        )
        object.__setattr__(
            self,
            "team_key",
            _require_public_identifier("team_key", self.team_key),
        )
        object.__setattr__(
            self,
            "review_due_at",
            _as_utc("review_due_at", self.review_due_at),
        )
        object.__setattr__(
            self,
            "reviewed_at",
            _as_optional_utc("reviewed_at", self.reviewed_at),
        )
        _require_status("primary_outcome", self.primary_outcome)
        _require_status("secondary_outcome", self.secondary_outcome)
        object.__setattr__(
            self,
            "rationale_score",
            _require_ratio_decimal("rationale_score", self.rationale_score),
        )
        _require_bool("memory_writeback_completed", self.memory_writeback_completed)
        _require_bool("manual_escalation_required", self.manual_escalation_required)
        object.__setattr__(
            self,
            "manual_escalation_due_at",
            _as_optional_utc("manual_escalation_due_at", self.manual_escalation_due_at),
        )
        if self.manual_escalation_required and self.manual_escalation_due_at is None:
            raise ValueError("manual_escalation_due_at is required")
        _require_hard_flags("snapshot", self)
        _reject_unsafe_public_payload("snapshot", self)


@dataclass(frozen=True)
class ResearchTeamReviewQualityExceptionRow(_FinalPublicDataclass):
    review_marker: str
    team_key: str
    review_due_at: datetime
    reviewed_at: datetime | None
    primary_outcome: str
    secondary_outcome: str
    rationale_score: Decimal
    late_review_seconds: Decimal
    outcome_conflict_count: Decimal
    memory_writeback_omission_count: Decimal
    memory_writeback_age_seconds: Decimal
    manual_escalation_required: bool
    manual_escalation_due_at: datetime | None
    manual_escalation_due_in_seconds: Decimal
    manual_escalation_urgency_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamReviewQualityExceptionRow, "row")
        _require_public_marker("review_marker", self.review_marker)
        object.__setattr__(
            self,
            "team_key",
            _require_public_identifier("team_key", self.team_key),
        )
        object.__setattr__(
            self,
            "review_due_at",
            _as_utc("review_due_at", self.review_due_at),
        )
        object.__setattr__(
            self,
            "reviewed_at",
            _as_optional_utc("reviewed_at", self.reviewed_at),
        )
        _require_status("primary_outcome", self.primary_outcome)
        _require_status("secondary_outcome", self.secondary_outcome)
        object.__setattr__(
            self,
            "rationale_score",
            _require_ratio_decimal("rationale_score", self.rationale_score),
        )
        for field_name in (
            "late_review_seconds",
            "outcome_conflict_count",
            "memory_writeback_omission_count",
            "memory_writeback_age_seconds",
            "manual_escalation_due_in_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_measure_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "manual_escalation_urgency_score",
            _require_ratio_decimal(
                "manual_escalation_urgency_score",
                self.manual_escalation_urgency_score,
            ),
        )
        _require_bool("manual_escalation_required", self.manual_escalation_required)
        object.__setattr__(
            self,
            "manual_escalation_due_at",
            _as_optional_utc("manual_escalation_due_at", self.manual_escalation_due_at),
        )
        if self.manual_escalation_required and self.manual_escalation_due_at is None:
            raise ValueError("manual_escalation_due_at is required")
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allowed=ROW_REASON_PRIORITY,
                allow_empty=False,
            ),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchTeamReviewQualityExceptionReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamReviewQualityExceptionReasonCodeCount, "count")
        object.__setattr__(
            self,
            "reason_code",
            _require_choice("reason_code", self.reason_code, REPORT_REASON_PRIORITY),
        )
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamReviewQualityExceptionReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    review_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    late_review_count: Decimal
    missing_rationale_count: Decimal
    conflicting_outcome_count: Decimal
    memory_writeback_omission_count: Decimal
    manual_escalation_urgent_count: Decimal
    max_late_review_seconds: Decimal
    max_memory_writeback_age_seconds: Decimal
    max_manual_escalation_urgency_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchTeamReviewQualityExceptionReasonCodeCount, ...]
    rows: tuple[ResearchTeamReviewQualityExceptionRow, ...]
    public_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamReviewQualityExceptionReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_label("config_version", self.config_version),
        )
        for field_name in (
            "review_count",
            "pass_count",
            "watch_count",
            "block_count",
            "late_review_count",
            "missing_rationale_count",
            "conflicting_outcome_count",
            "memory_writeback_omission_count",
            "manual_escalation_urgent_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_late_review_seconds",
            "max_memory_writeback_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_measure_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_manual_escalation_urgency_score",
            _require_ratio_decimal(
                "max_manual_escalation_urgency_score",
                self.max_manual_escalation_urgency_score,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allowed=REPORT_REASON_PRIORITY,
                allow_empty=False,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _digest_from_values(_report_values_without_digest(self))
        if self.public_digest:
            _require_sha256_digest("public_digest", self.public_digest)
            if self.public_digest != expected_digest:
                raise ValueError("public_digest must match report fields")
        object.__setattr__(self, "public_digest", expected_digest)

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        _reject_unsafe_public_payload("payload", payload)
        _require_hard_flags("payload", _DictFlags(payload))
        _validate_payload_digest(payload)
        return payload


def build_research_team_review_quality_exception_report(
    snapshots: Iterable[ResearchTeamReviewQualitySnapshot],
    *,
    generated_at: datetime,
    config: ResearchTeamReviewQualityExceptionConfig | None = None,
) -> ResearchTeamReviewQualityExceptionReport:
    if config is None:
        config = ResearchTeamReviewQualityExceptionConfig()
    if type(config) is not ResearchTeamReviewQualityExceptionConfig:
        raise ValueError("config must be a ResearchTeamReviewQualityExceptionConfig")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_snapshots = _normalize_snapshots(snapshots)
    rows = _sort_rows(
        tuple(
            _row_from_snapshot(item, config=config, generated_at=generated_at)
            for item in normalized_snapshots
        ),
    )
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "review_count": _count(len(rows)),
        "pass_count": _count(_status_count(rows, "pass")),
        "watch_count": _count(_status_count(rows, "watch")),
        "block_count": _count(_status_count(rows, "block")),
        "late_review_count": _count(
            _reason_count(rows, LATE_WATCH_REASON)
            + _reason_count(rows, LATE_BLOCK_REASON),
        ),
        "missing_rationale_count": _count(
            _reason_count(rows, RATIONALE_WATCH_REASON)
            + _reason_count(rows, RATIONALE_BLOCK_REASON),
        ),
        "conflicting_outcome_count": _count(
            _reason_count(rows, OUTCOME_CONFLICT_BLOCK_REASON),
        ),
        "memory_writeback_omission_count": _count(
            _reason_count(rows, MEMORY_WRITEBACK_WATCH_REASON)
            + _reason_count(rows, MEMORY_WRITEBACK_BLOCK_REASON),
        ),
        "manual_escalation_urgent_count": _count(
            _reason_count(rows, MANUAL_ESCALATION_WATCH_REASON)
            + _reason_count(rows, MANUAL_ESCALATION_BLOCK_REASON),
        ),
        "max_late_review_seconds": _max_row_decimal(rows, "late_review_seconds"),
        "max_memory_writeback_age_seconds": _max_row_decimal(
            rows,
            "memory_writeback_age_seconds",
        ),
        "max_manual_escalation_urgency_score": _max_row_decimal(
            rows,
            "manual_escalation_urgency_score",
        ),
        "status": _report_status(rows),
        "reason_codes": reason_codes,
        "reason_code_counts": (),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["reason_code_counts"] = _reason_code_counts(reason_codes, rows)
    return ResearchTeamReviewQualityExceptionReport(
        **values,
        public_digest=_digest_from_values(values),
    )


def research_team_review_quality_exception_report_payload(
    report: ResearchTeamReviewQualityExceptionReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamReviewQualityExceptionReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        return report.payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        _require_hard_flags("payload", _DictFlags(payload))
        _validate_payload_digest(payload)
        _reject_unsafe_public_payload("payload", payload)
        return payload
    raise ValueError(
        "report must be a ResearchTeamReviewQualityExceptionReport or payload",
    )


def research_team_review_quality_exception_report_digest(
    report: ResearchTeamReviewQualityExceptionReport | dict[str, Any],
) -> str:
    payload = research_team_review_quality_exception_report_payload(report)
    return _payload_digest(payload)


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        if "paper_only" not in self.value:
            return None
        return self.value["paper_only"]

    @property
    def report_only(self) -> object:
        if "report_only" not in self.value:
            return None
        return self.value["report_only"]

    @property
    def readonly(self) -> object:
        if "readonly" not in self.value:
            return None
        return self.value["readonly"]


def _row_from_snapshot(
    item: ResearchTeamReviewQualitySnapshot,
    *,
    config: ResearchTeamReviewQualityExceptionConfig,
    generated_at: datetime,
) -> ResearchTeamReviewQualityExceptionRow:
    if item.reviewed_at is not None and item.reviewed_at > generated_at:
        raise ValueError("reviewed_at must be <= generated_at")
    if item.review_due_at > generated_at and item.reviewed_at is None:
        late_review_seconds = _ZERO
    else:
        review_completed_at = item.reviewed_at if item.reviewed_at is not None else generated_at
        late_review_seconds = _duration_seconds(item.review_due_at, review_completed_at)
    memory_age_seconds = _memory_writeback_age_seconds(item, generated_at)
    due_in_seconds = _manual_escalation_due_in_seconds(item, generated_at)
    urgency_score = _manual_escalation_urgency_score(
        required=item.manual_escalation_required,
        due_in_seconds=due_in_seconds,
        config=config,
    )
    reason_codes = _row_reason_codes(
        late_review_seconds=late_review_seconds,
        rationale_score=item.rationale_score,
        primary_outcome=item.primary_outcome,
        secondary_outcome=item.secondary_outcome,
        memory_writeback_completed=item.memory_writeback_completed,
        memory_writeback_age_seconds=memory_age_seconds,
        manual_escalation_required=item.manual_escalation_required,
        manual_escalation_due_in_seconds=due_in_seconds,
        config=config,
    )
    return ResearchTeamReviewQualityExceptionRow(
        review_marker=item.review_reference,
        team_key=item.team_key,
        review_due_at=item.review_due_at,
        reviewed_at=item.reviewed_at,
        primary_outcome=item.primary_outcome,
        secondary_outcome=item.secondary_outcome,
        rationale_score=item.rationale_score,
        late_review_seconds=late_review_seconds,
        outcome_conflict_count=_count(1 if item.primary_outcome != item.secondary_outcome else 0),
        memory_writeback_omission_count=_count(
            0 if item.memory_writeback_completed else 1,
        ),
        memory_writeback_age_seconds=memory_age_seconds,
        manual_escalation_required=item.manual_escalation_required,
        manual_escalation_due_at=item.manual_escalation_due_at,
        manual_escalation_due_in_seconds=due_in_seconds,
        manual_escalation_urgency_score=urgency_score,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    late_review_seconds: Decimal,
    rationale_score: Decimal,
    primary_outcome: str,
    secondary_outcome: str,
    memory_writeback_completed: bool,
    memory_writeback_age_seconds: Decimal,
    manual_escalation_required: bool,
    manual_escalation_due_in_seconds: Decimal,
    config: ResearchTeamReviewQualityExceptionConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if late_review_seconds >= config.late_review_block_seconds:
        reasons.append(LATE_BLOCK_REASON)
    elif late_review_seconds >= config.late_review_watch_seconds:
        reasons.append(LATE_WATCH_REASON)
    if rationale_score < config.min_rationale_block_score:
        reasons.append(RATIONALE_BLOCK_REASON)
    elif rationale_score < config.min_rationale_watch_score:
        reasons.append(RATIONALE_WATCH_REASON)
    if primary_outcome != secondary_outcome:
        reasons.append(OUTCOME_CONFLICT_BLOCK_REASON)
    if not memory_writeback_completed:
        if memory_writeback_age_seconds >= config.memory_writeback_block_seconds:
            reasons.append(MEMORY_WRITEBACK_BLOCK_REASON)
        else:
            reasons.append(MEMORY_WRITEBACK_WATCH_REASON)
    if manual_escalation_required:
        if manual_escalation_due_in_seconds <= _ZERO:
            reasons.append(MANUAL_ESCALATION_BLOCK_REASON)
        elif manual_escalation_due_in_seconds <= config.manual_escalation_watch_seconds:
            reasons.append(MANUAL_ESCALATION_WATCH_REASON)
    if not reasons:
        return (PASS_REASON,)
    return tuple(reason for reason in ROW_REASON_PRIORITY if reason in reasons)


def _memory_writeback_age_seconds(
    item: ResearchTeamReviewQualitySnapshot,
    generated_at: datetime,
) -> Decimal:
    if item.memory_writeback_completed:
        return _ZERO
    age_start = item.reviewed_at if item.reviewed_at is not None else item.review_due_at
    return _duration_seconds(age_start, generated_at)


def _manual_escalation_due_in_seconds(
    item: ResearchTeamReviewQualitySnapshot,
    generated_at: datetime,
) -> Decimal:
    if not item.manual_escalation_required or item.manual_escalation_due_at is None:
        return _ZERO
    if item.manual_escalation_due_at <= generated_at:
        return _ZERO
    return _duration_seconds(generated_at, item.manual_escalation_due_at)


def _manual_escalation_urgency_score(
    *,
    required: bool,
    due_in_seconds: Decimal,
    config: ResearchTeamReviewQualityExceptionConfig,
) -> Decimal:
    if not required:
        return _ZERO
    if due_in_seconds <= _ZERO:
        return _ONE
    if due_in_seconds >= config.manual_escalation_watch_seconds:
        return _ZERO
    ratio = _ONE - _safe_ratio(due_in_seconds, config.manual_escalation_watch_seconds)
    return _clamp_ratio(ratio)


def _report_reason_codes(
    rows: tuple[ResearchTeamReviewQualityExceptionRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    reasons = {reason for row in rows for reason in row.reason_codes if reason != PASS_REASON}
    if not reasons:
        return (PASS_REASON,)
    return tuple(reason for reason in REPORT_REASON_PRIORITY if reason in reasons)


def _report_status(rows: tuple[ResearchTeamReviewQualityExceptionRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason in BLOCK_REASONS for reason in reason_codes):
        return "block"
    if any(reason in WATCH_REASONS for reason in reason_codes):
        return "watch"
    return "pass"


def _status_count(rows: tuple[ResearchTeamReviewQualityExceptionRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _reason_count(
    rows: tuple[ResearchTeamReviewQualityExceptionRow, ...],
    reason_code: str,
) -> int:
    return sum(1 for row in rows if reason_code in row.reason_codes)


def _reason_code_counts(
    report_reason_codes: tuple[str, ...],
    rows: tuple[ResearchTeamReviewQualityExceptionRow, ...],
) -> tuple[ResearchTeamReviewQualityExceptionReasonCodeCount, ...]:
    counts: list[ResearchTeamReviewQualityExceptionReasonCodeCount] = []
    for reason_code in report_reason_codes:
        if reason_code == EMPTY_REASON:
            count = _count(1)
        elif reason_code == PASS_REASON:
            count = _count(_status_count(rows, "pass"))
        else:
            count = _count(_reason_count(rows, reason_code))
        if count > _ZERO:
            counts.append(
                ResearchTeamReviewQualityExceptionReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                ),
            )
    return tuple(counts)


def _normalize_snapshots(
    snapshots: Iterable[ResearchTeamReviewQualitySnapshot],
) -> tuple[ResearchTeamReviewQualitySnapshot, ...]:
    if isinstance(snapshots, (str, bytes)):
        raise ValueError("snapshots must be an iterable of snapshots")
    normalized: list[ResearchTeamReviewQualitySnapshot] = []
    for item in snapshots:
        if type(item) is ResearchTeamReviewQualitySnapshot:
            normalized.append(item)
            continue
        if type(item) is dict:
            normalized.append(ResearchTeamReviewQualitySnapshot(**item))
            continue
        raise ValueError("snapshots must contain ResearchTeamReviewQualitySnapshot values")
    return tuple(normalized)


def _normalize_rows(
    rows: Iterable[ResearchTeamReviewQualityExceptionRow],
) -> tuple[ResearchTeamReviewQualityExceptionRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable of rows")
    normalized: list[ResearchTeamReviewQualityExceptionRow] = []
    for row in rows:
        if type(row) is not ResearchTeamReviewQualityExceptionRow:
            raise ValueError("rows must contain ResearchTeamReviewQualityExceptionRow values")
        normalized.append(row)
    normalized_rows = tuple(normalized)
    row_keys = tuple(_row_sort_key(row) for row in normalized_rows)
    if any(left >= right for left, right in zip(row_keys, row_keys[1:])):
        raise ValueError("rows must be sorted")
    return normalized_rows


def _sort_rows(
    rows: tuple[ResearchTeamReviewQualityExceptionRow, ...],
) -> tuple[ResearchTeamReviewQualityExceptionRow, ...]:
    return tuple(sorted(rows, key=_row_sort_key))


def _row_sort_key(row: ResearchTeamReviewQualityExceptionRow) -> tuple[int, str, str]:
    return (_status_rank(row.status), row.team_key, row.review_marker)


def _status_rank(status: str) -> int:
    if status == "block":
        return 0
    if status == "watch":
        return 1
    return 2


def _normalize_reason_code_counts(
    counts: Iterable[ResearchTeamReviewQualityExceptionReasonCodeCount],
) -> tuple[ResearchTeamReviewQualityExceptionReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    normalized: list[ResearchTeamReviewQualityExceptionReasonCodeCount] = []
    for count in counts:
        if type(count) is not ResearchTeamReviewQualityExceptionReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTeamReviewQualityExceptionReasonCodeCount values",
            )
        normalized.append(count)
    rank = {reason: index for index, reason in enumerate(REPORT_REASON_PRIORITY)}
    sorted_counts = tuple(sorted(normalized, key=lambda item: rank[item.reason_code]))
    if tuple(normalized) != sorted_counts:
        raise ValueError("reason_code_counts must be sorted")
    reason_codes = tuple(count.reason_code for count in sorted_counts)
    if len(reason_codes) != len(frozenset(reason_codes)):
        raise ValueError("reason_code_counts must be unique")
    return sorted_counts


def _validate_row(row: ResearchTeamReviewQualityExceptionRow) -> None:
    expected_status = _status_from_reason_codes(row.reason_codes)
    if row.status != expected_status:
        raise ValueError("status must match reason_codes")
    expected_conflict_count = _count(
        1 if row.primary_outcome != row.secondary_outcome else 0,
    )
    if row.outcome_conflict_count != expected_conflict_count:
        raise ValueError("outcome_conflict_count must match outcomes")
    if row.memory_writeback_omission_count not in (_ZERO, _ONE):
        raise ValueError("memory_writeback_omission_count must be 0 or 1")
    if row.outcome_conflict_count not in (_ZERO, _ONE):
        raise ValueError("outcome_conflict_count must be 0 or 1")
    if row.status == "pass" and row.reason_codes != (PASS_REASON,):
        raise ValueError("pass rows must include only the pass reason")
    if row.status != "pass" and PASS_REASON in row.reason_codes:
        raise ValueError("exception rows must not include the pass reason")


def _validate_report(report: ResearchTeamReviewQualityExceptionReport) -> None:
    rows = report.rows
    if report.review_count != _count(len(rows)):
        raise ValueError("review_count must match rows")
    if report.pass_count != _count(_status_count(rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(_status_count(rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(_status_count(rows, "block")):
        raise ValueError("block_count must match rows")
    if report.late_review_count != _count(
        _reason_count(rows, LATE_WATCH_REASON) + _reason_count(rows, LATE_BLOCK_REASON),
    ):
        raise ValueError("late_review_count must match rows")
    if report.missing_rationale_count != _count(
        _reason_count(rows, RATIONALE_WATCH_REASON)
        + _reason_count(rows, RATIONALE_BLOCK_REASON),
    ):
        raise ValueError("missing_rationale_count must match rows")
    if report.conflicting_outcome_count != _count(
        _reason_count(rows, OUTCOME_CONFLICT_BLOCK_REASON),
    ):
        raise ValueError("conflicting_outcome_count must match rows")
    if report.memory_writeback_omission_count != _count(
        _reason_count(rows, MEMORY_WRITEBACK_WATCH_REASON)
        + _reason_count(rows, MEMORY_WRITEBACK_BLOCK_REASON),
    ):
        raise ValueError("memory_writeback_omission_count must match rows")
    if report.manual_escalation_urgent_count != _count(
        _reason_count(rows, MANUAL_ESCALATION_WATCH_REASON)
        + _reason_count(rows, MANUAL_ESCALATION_BLOCK_REASON),
    ):
        raise ValueError("manual_escalation_urgent_count must match rows")
    if report.max_late_review_seconds != _max_row_decimal(rows, "late_review_seconds"):
        raise ValueError("max_late_review_seconds must match rows")
    if report.max_memory_writeback_age_seconds != _max_row_decimal(
        rows,
        "memory_writeback_age_seconds",
    ):
        raise ValueError("max_memory_writeback_age_seconds must match rows")
    if report.max_manual_escalation_urgency_score != _max_row_decimal(
        rows,
        "manual_escalation_urgency_score",
    ):
        raise ValueError("max_manual_escalation_urgency_score must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    expected_counts = _reason_code_counts(report.reason_codes, rows)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")


def _max_row_decimal(
    rows: tuple[ResearchTeamReviewQualityExceptionRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return _ZERO
    return max(getattr(row, field_name) for row in rows)


def _duration_seconds(start: datetime, end: datetime) -> Decimal:
    if end <= start:
        return _ZERO
    delta = end - start
    total_microseconds = (
        Decimal(delta.days) * Decimal("86400") * Decimal("1000000")
        + Decimal(delta.seconds) * Decimal("1000000")
        + Decimal(delta.microseconds)
    )
    return _quantize(total_microseconds / Decimal("1000000"))


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= _ZERO:
        return _ZERO
    return _quantize(numerator / denominator)


def _clamp_ratio(value: Decimal) -> Decimal:
    if value < _ZERO:
        return _ZERO
    if value > _ONE:
        return _ONE
    return _quantize(value)


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize(Decimal(value))


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_label(field_name: str, value: str) -> str:
    if type(value) is not str or not _PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public label")
    _reject_unsafe_public_text(field_name, value)
    return value


def _require_public_identifier(field_name: str, value: str) -> str:
    if type(value) is not str or not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_text(field_name, value)
    return value


def _require_public_marker(field_name: str, value: str) -> None:
    if type(value) is not str or not value.startswith("review_marker_"):
        raise ValueError(f"{field_name} must be a public review marker")
    _reject_unsafe_public_text(field_name, value)


def _require_private_reference(field_name: str, value: str) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a private reference")
    normalized = value.lower()
    if any(fragment in normalized for fragment in _UNSAFE_PRIVATE_REFERENCE_TERMS):
        raise ValueError("unsafe private reference")


def _redacted_marker(prefix: str, value: str) -> str:
    digest = sha256(value.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}{digest}"


def _require_status(field_name: str, value: str) -> None:
    _require_choice(field_name, value, _STATUSES)


def _require_choice(field_name: str, value: str, allowed: tuple[str, ...]) -> str:
    if type(value) is not str or value not in allowed:
        if allowed == _STATUSES:
            raise ValueError(f"{field_name} must be pass, watch, or block")
        raise ValueError(f"{field_name} must be supported")
    return value


def _require_bool(field_name: str, value: bool) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent < -6:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return _quantize(value)


def _require_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_measure_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_measure_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole number")
    return normalized


def _require_positive_count_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _normalize_reason_codes(
    field_name: str,
    values: Iterable[str],
    *,
    allowed: tuple[str, ...],
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be a sequence")
    seen: set[str] = set()
    normalized: list[str] = []
    for value in values:
        if type(value) is not str or value not in allowed:
            raise ValueError(f"{field_name} contains an unsupported reason code")
        if value in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must not be empty")
    rank = {reason: index for index, reason in enumerate(allowed)}
    sorted_values = tuple(sorted(normalized, key=lambda reason: rank[reason]))
    if tuple(normalized) != sorted_values:
        raise ValueError(f"{field_name} must be sorted")
    return sorted_values


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_term(key):
                raise ValueError(f"unsafe public payload in {label}")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    if _has_unsafe_public_term(value):
        raise ValueError(f"unsafe public value in {label}")


def _has_unsafe_public_term(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in _UNSAFE_PUBLIC_TERMS)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(_quantize(value))
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) is float or type(value) is int:
        raise ValueError("payload numeric values must be Decimal-derived strings")
    if type(value) is str or type(value) is bool:
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _report_values_without_digest(
    report: ResearchTeamReviewQualityExceptionReport,
) -> dict[str, object]:
    values = asdict(report)
    if "public_digest" in values:
        del values["public_digest"]
    return values


def _digest_from_values(values: dict[str, object]) -> str:
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a dict")
    return _payload_digest(payload)


def _payload_digest(payload: dict[str, Any]) -> str:
    payload_without_digest = dict(payload)
    if "public_digest" in payload_without_digest:
        del payload_without_digest["public_digest"]
    rendered = json.dumps(
        payload_without_digest,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(rendered.encode("utf-8")).hexdigest()


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    if "public_digest" not in payload:
        raise ValueError("public_digest is required")
    digest = payload["public_digest"]
    if type(digest) is not str:
        raise ValueError("public_digest must be a SHA-256 digest")
    _require_sha256_digest("public_digest", digest)
    if digest != _payload_digest(payload):
        raise ValueError("public_digest must match payload fields")


def _require_sha256_digest(field_name: str, value: str) -> None:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a SHA-256 digest")
