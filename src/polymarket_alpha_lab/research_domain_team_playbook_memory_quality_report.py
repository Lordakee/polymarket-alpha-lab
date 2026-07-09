"""Pure domain-team playbook memory quality report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_DOMAIN_TEAM_PLAYBOOK_MEMORY_QUALITY_CONFIG_VERSION = (
    "research-domain-team-playbook-memory-quality-report-v1"
)

PLAYBOOK_MEMORY_QUALITY_STATUSES = ("pass", "watch", "block")
STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}

EMPTY_REASON = "playbook_memory_quality_empty"
CLEAR_REASON = "playbook_memory_quality_clear"
VALIDATED_LESSONS_BLOCK_REASON = "playbook_memory_validated_lessons_block"
RECENT_FEEDBACK_BLOCK_REASON = "playbook_memory_recent_feedback_block"
CALIBRATION_NOTES_BLOCK_REASON = "playbook_memory_calibration_notes_block"
UNRESOLVED_CAVEATS_BLOCK_REASON = "playbook_memory_unresolved_caveats_block"
VALIDATED_LESSONS_WATCH_REASON = "playbook_memory_validated_lessons_watch"
RECENT_FEEDBACK_WATCH_REASON = "playbook_memory_recent_feedback_watch"
CALIBRATION_NOTES_WATCH_REASON = "playbook_memory_calibration_notes_watch"
UNRESOLVED_CAVEATS_WATCH_REASON = "playbook_memory_unresolved_caveats_watch"

REASON_CODE_SEQUENCE = (
    EMPTY_REASON,
    VALIDATED_LESSONS_BLOCK_REASON,
    RECENT_FEEDBACK_BLOCK_REASON,
    CALIBRATION_NOTES_BLOCK_REASON,
    UNRESOLVED_CAVEATS_BLOCK_REASON,
    VALIDATED_LESSONS_WATCH_REASON,
    RECENT_FEEDBACK_WATCH_REASON,
    CALIBRATION_NOTES_WATCH_REASON,
    UNRESOLVED_CAVEATS_WATCH_REASON,
    CLEAR_REASON,
)
BLOCK_REASONS = frozenset(reason for reason in REASON_CODE_SEQUENCE if reason.endswith("_block"))
WATCH_REASONS = frozenset(reason for reason in REASON_CODE_SEQUENCE if reason.endswith("_watch"))

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
SECONDS_PER_DAY = Decimal("86400.000000")
WATCH_REASON_PENALTY = Decimal("0.075000")
BLOCK_REASON_PENALTY = Decimal("0.200000")

PUBLIC_LABEL_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_.-")
SHA256_HEX_LENGTH = 64


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "://",
    "http",
    "url",
    "raw",
    "candidate",
    "market",
    "slug",
    "question",
    "source",
    "text",
    "dsn",
    "table",
    "private",
    "token",
    "secret",
    "credential",
    "auth",
    "api_key",
    "apikey",
    "key",
    _join_parts("wal", "let"),
    _join_parts("acc", "ount"),
    _join_parts("bro", "ker"),
    _join_parts("or", "der"),
    _join_parts("sub", "mit"),
    _join_parts("can", "cel"),
    _join_parts("tra", "de"),
    _join_parts("recom", "mendation"),
    _join_parts("siz", "ing"),
    _join_parts("li", "ve"),
    _join_parts("net", "work"),
    _join_parts("data", "base"),
    _join_parts("b", "uy"),
    _join_parts("s", "ell"),
)


@dataclass(frozen=True)
class ResearchDomainTeamPlaybookMemoryQualityConfig:
    config_version: str = (
        DEFAULT_RESEARCH_DOMAIN_TEAM_PLAYBOOK_MEMORY_QUALITY_CONFIG_VERSION
    )
    validated_lesson_pass_count: Decimal = Decimal("5.000000")
    validated_lesson_watch_count: Decimal = Decimal("3.000000")
    feedback_pass_age_seconds: Decimal = Decimal("604800.000000")
    feedback_watch_age_seconds: Decimal = Decimal("1209600.000000")
    calibration_note_pass_count: Decimal = Decimal("3.000000")
    calibration_note_watch_count: Decimal = Decimal("1.000000")
    unresolved_caveat_watch_count: Decimal = Decimal("1.000000")
    unresolved_caveat_block_count: Decimal = Decimal("3.000000")
    triage_readiness_pass_score: Decimal = Decimal("0.800000")
    triage_readiness_watch_score: Decimal = Decimal("0.550000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchDomainTeamPlaybookMemoryQualityConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_DOMAIN_TEAM_PLAYBOOK_MEMORY_QUALITY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "validated_lesson_pass_count",
            "validated_lesson_watch_count",
            "feedback_pass_age_seconds",
            "feedback_watch_age_seconds",
            "calibration_note_pass_count",
            "calibration_note_watch_count",
            "unresolved_caveat_watch_count",
            "unresolved_caveat_block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "triage_readiness_pass_score",
            "triage_readiness_watch_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.validated_lesson_pass_count < self.validated_lesson_watch_count:
            raise ValueError("validated_lesson_pass_count must not be below watch count")
        if self.feedback_pass_age_seconds > self.feedback_watch_age_seconds:
            raise ValueError("feedback_watch_age_seconds must not be below pass age")
        if self.calibration_note_pass_count < self.calibration_note_watch_count:
            raise ValueError("calibration_note_pass_count must not be below watch count")
        if self.unresolved_caveat_watch_count > self.unresolved_caveat_block_count:
            raise ValueError("unresolved_caveat_block_count must not be below watch count")
        if self.triage_readiness_pass_score < self.triage_readiness_watch_score:
            raise ValueError("triage_readiness_pass_score must not be below watch score")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchDomainTeamPlaybookMemoryQualityInput:
    domain_team_label: str
    specialist_team_label: str
    validated_lesson_count: Decimal
    latest_feedback_at: datetime | None
    calibration_note_count: Decimal
    unresolved_caveat_count: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchDomainTeamPlaybookMemoryQualityInput, "input row")
        object.__setattr__(
            self,
            "domain_team_label",
            _require_public_label("domain_team_label", self.domain_team_label),
        )
        object.__setattr__(
            self,
            "specialist_team_label",
            _require_public_label("specialist_team_label", self.specialist_team_label),
        )
        for field_name in (
            "validated_lesson_count",
            "calibration_note_count",
            "unresolved_caveat_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_feedback_at",
            _as_optional_utc("latest_feedback_at", self.latest_feedback_at),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        if self.latest_feedback_at is not None and self.latest_feedback_at > self.observed_at:
            raise ValueError("latest_feedback_at must not follow observed_at")
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class ResearchDomainTeamPlaybookMemoryQualityRow:
    domain_team_label: str
    specialist_team_label: str
    status: str
    validated_lesson_count: Decimal
    feedback_age_seconds: Decimal
    calibration_note_count: Decimal
    unresolved_caveat_count: Decimal
    triage_readiness_score: Decimal
    observed_at: datetime
    latest_feedback_at: datetime | None
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchDomainTeamPlaybookMemoryQualityRow, "row")
        object.__setattr__(
            self,
            "domain_team_label",
            _require_public_label("domain_team_label", self.domain_team_label),
        )
        object.__setattr__(
            self,
            "specialist_team_label",
            _require_public_label("specialist_team_label", self.specialist_team_label),
        )
        object.__setattr__(self, "status", _require_status("status", self.status))
        for field_name in (
            "validated_lesson_count",
            "feedback_age_seconds",
            "calibration_note_count",
            "unresolved_caveat_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "triage_readiness_score",
            _require_ratio_decimal("triage_readiness_score", self.triage_readiness_score),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "latest_feedback_at",
            _as_optional_utc("latest_feedback_at", self.latest_feedback_at),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchDomainTeamPlaybookMemoryQualityReport:
    generated_at: datetime
    config_version: str
    report_status: str
    domain_team_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    total_validated_lesson_count: Decimal
    total_calibration_note_count: Decimal
    total_unresolved_caveat_count: Decimal
    max_feedback_age_seconds: Decimal
    min_triage_readiness_score: Decimal
    rows: tuple[ResearchDomainTeamPlaybookMemoryQualityRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchDomainTeamPlaybookMemoryQualityReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        object.__setattr__(
            self,
            "report_status",
            _require_status("report_status", self.report_status),
        )
        for field_name in (
            "domain_team_count",
            "pass_count",
            "watch_count",
            "block_count",
            "total_validated_lesson_count",
            "total_calibration_note_count",
            "total_unresolved_caveat_count",
            "max_feedback_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_triage_readiness_score",
            _require_ratio_decimal(
                "min_triage_readiness_score",
                self.min_triage_readiness_score,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report(self)
        expected_digest = _derived_validation_digest(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        _reject_unsafe_public_payload("report payload", payload)
        return payload


def build_research_domain_team_playbook_memory_quality_report(
    input_rows: object,
    *,
    config: ResearchDomainTeamPlaybookMemoryQualityConfig | None = None,
    generated_at: datetime,
) -> ResearchDomainTeamPlaybookMemoryQualityReport:
    if config is None:
        config = ResearchDomainTeamPlaybookMemoryQualityConfig()
    if type(config) is not ResearchDomainTeamPlaybookMemoryQualityConfig:
        raise ValueError("config must be a ResearchDomainTeamPlaybookMemoryQualityConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _rows_for_inputs(
        _normalize_input_rows(input_rows, generated_at=generated_at_utc),
        config=config,
        generated_at=generated_at_utc,
    )
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "report_status": _report_status(rows),
        "domain_team_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "total_validated_lesson_count": _sum_decimal(
            tuple(row.validated_lesson_count for row in rows),
        ),
        "total_calibration_note_count": _sum_decimal(
            tuple(row.calibration_note_count for row in rows),
        ),
        "total_unresolved_caveat_count": _sum_decimal(
            tuple(row.unresolved_caveat_count for row in rows),
        ),
        "max_feedback_age_seconds": max(
            (row.feedback_age_seconds for row in rows),
            default=ZERO,
        ),
        "min_triage_readiness_score": min(
            (row.triage_readiness_score for row in rows),
            default=ZERO,
        ),
        "rows": rows,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchDomainTeamPlaybookMemoryQualityReport(
        **values,
        derived_validation_digest=_derived_validation_digest(values),
    )


def research_domain_team_playbook_memory_quality_report_payload(
    value: object,
) -> dict[str, object]:
    if type(value) is ResearchDomainTeamPlaybookMemoryQualityReport:
        return value.payload
    if type(value) is not dict:
        raise ValueError("payload source must be a report or dict")
    _require_payload_hard_flags(value)
    _reject_unsafe_public_payload("report payload", value)
    digest = value.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    if digest != _derived_validation_digest(value):
        raise ValueError("derived_validation_digest does not match report payload")
    payload = _payload_value(value)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def research_domain_team_playbook_memory_quality_report_digest(value: object) -> str:
    payload = research_domain_team_playbook_memory_quality_report_payload(value)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


def _rows_for_inputs(
    input_rows: tuple[ResearchDomainTeamPlaybookMemoryQualityInput, ...],
    *,
    config: ResearchDomainTeamPlaybookMemoryQualityConfig,
    generated_at: datetime,
) -> tuple[ResearchDomainTeamPlaybookMemoryQualityRow, ...]:
    rows = tuple(
        _row_from_input(row, config=config, generated_at=generated_at)
        for row in input_rows
    )
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                STATUS_RANK[row.status],
                row.triage_readiness_score,
                row.domain_team_label,
                row.specialist_team_label,
            ),
        ),
    )


def _row_from_input(
    row: ResearchDomainTeamPlaybookMemoryQualityInput,
    *,
    config: ResearchDomainTeamPlaybookMemoryQualityConfig,
    generated_at: datetime,
) -> ResearchDomainTeamPlaybookMemoryQualityRow:
    feedback_age_seconds = _feedback_age_seconds(row, generated_at)
    reason_codes = _row_reason_codes(
        validated_lesson_count=row.validated_lesson_count,
        feedback_age_seconds=feedback_age_seconds,
        latest_feedback_at=row.latest_feedback_at,
        calibration_note_count=row.calibration_note_count,
        unresolved_caveat_count=row.unresolved_caveat_count,
        config=config,
    )
    return ResearchDomainTeamPlaybookMemoryQualityRow(
        domain_team_label=row.domain_team_label,
        specialist_team_label=row.specialist_team_label,
        status=_status_from_reason_codes(reason_codes),
        validated_lesson_count=row.validated_lesson_count,
        feedback_age_seconds=feedback_age_seconds,
        calibration_note_count=row.calibration_note_count,
        unresolved_caveat_count=row.unresolved_caveat_count,
        triage_readiness_score=_triage_readiness_score(reason_codes),
        observed_at=row.observed_at,
        latest_feedback_at=row.latest_feedback_at,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    validated_lesson_count: Decimal,
    feedback_age_seconds: Decimal,
    latest_feedback_at: datetime | None,
    calibration_note_count: Decimal,
    unresolved_caveat_count: Decimal,
    config: ResearchDomainTeamPlaybookMemoryQualityConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if validated_lesson_count < config.validated_lesson_watch_count:
        reasons.append(VALIDATED_LESSONS_BLOCK_REASON)
    elif validated_lesson_count < config.validated_lesson_pass_count:
        reasons.append(VALIDATED_LESSONS_WATCH_REASON)
    if latest_feedback_at is None or feedback_age_seconds > config.feedback_watch_age_seconds:
        reasons.append(RECENT_FEEDBACK_BLOCK_REASON)
    elif feedback_age_seconds > config.feedback_pass_age_seconds:
        reasons.append(RECENT_FEEDBACK_WATCH_REASON)
    if calibration_note_count < config.calibration_note_watch_count:
        reasons.append(CALIBRATION_NOTES_BLOCK_REASON)
    elif calibration_note_count < config.calibration_note_pass_count:
        reasons.append(CALIBRATION_NOTES_WATCH_REASON)
    if unresolved_caveat_count >= config.unresolved_caveat_block_count:
        reasons.append(UNRESOLVED_CAVEATS_BLOCK_REASON)
    elif unresolved_caveat_count >= config.unresolved_caveat_watch_count:
        reasons.append(UNRESOLVED_CAVEATS_WATCH_REASON)
    if not reasons:
        reasons.append(CLEAR_REASON)
    return _normalize_reason_codes(tuple(reasons))


def _report_reason_codes(
    rows: tuple[ResearchDomainTeamPlaybookMemoryQualityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    present = {reason for row in rows for reason in row.reason_codes}
    reasons = tuple(
        reason
        for reason in REASON_CODE_SEQUENCE
        if reason not in (EMPTY_REASON, CLEAR_REASON) and reason in present
    )
    if reasons:
        return reasons
    return (CLEAR_REASON,)


def _report_status(rows: tuple[ResearchDomainTeamPlaybookMemoryQualityRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason in BLOCK_REASONS for reason in reason_codes) or EMPTY_REASON in reason_codes:
        return "block"
    if any(reason in WATCH_REASONS for reason in reason_codes):
        return "watch"
    return "pass"


def _triage_readiness_score(reason_codes: tuple[str, ...]) -> Decimal:
    block_count = _count(sum(reason in BLOCK_REASONS for reason in reason_codes))
    watch_count = _count(sum(reason in WATCH_REASONS for reason in reason_codes))
    with localcontext(DECIMAL_CONTEXT):
        score = ONE - (block_count * BLOCK_REASON_PENALTY) - (
            watch_count * WATCH_REASON_PENALTY
        )
    if score < ZERO:
        return ZERO
    return _quantize(score)


def _feedback_age_seconds(
    row: ResearchDomainTeamPlaybookMemoryQualityInput,
    generated_at: datetime,
) -> Decimal:
    if row.latest_feedback_at is None:
        return _seconds_between(generated_at, row.observed_at)
    return _seconds_between(generated_at, row.latest_feedback_at)


def _normalize_input_rows(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[ResearchDomainTeamPlaybookMemoryQualityInput, ...]:
    if isinstance(value, (str, bytes)) or not hasattr(value, "__iter__"):
        raise ValueError("input rows must be an iterable")
    rows = tuple(value)
    seen_labels: set[str] = set()
    for row in rows:
        if type(row) is not ResearchDomainTeamPlaybookMemoryQualityInput:
            raise ValueError(
                "input rows must contain ResearchDomainTeamPlaybookMemoryQualityInput",
            )
        _require_hard_flags("input row", row)
        if row.domain_team_label in seen_labels:
            raise ValueError("domain_team_label values must be unique")
        seen_labels.add(row.domain_team_label)
        if row.observed_at > generated_at:
            raise ValueError("observed_at must not be in the future")
        if row.latest_feedback_at is not None and row.latest_feedback_at > generated_at:
            raise ValueError("latest_feedback_at must not be in the future")
    return tuple(sorted(rows, key=lambda row: (row.domain_team_label, row.specialist_team_label)))


def _normalize_rows(
    value: object,
) -> tuple[ResearchDomainTeamPlaybookMemoryQualityRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_labels: set[str] = set()
    previous_key: tuple[int, Decimal, str, str] | None = None
    for row in rows:
        if type(row) is not ResearchDomainTeamPlaybookMemoryQualityRow:
            raise ValueError("rows must contain ResearchDomainTeamPlaybookMemoryQualityRow")
        _require_hard_flags("row", row)
        if row.domain_team_label in seen_labels:
            raise ValueError("rows must contain unique domain_team_label values")
        seen_labels.add(row.domain_team_label)
        key = (
            STATUS_RANK[row.status],
            row.triage_readiness_score,
            row.domain_team_label,
            row.specialist_team_label,
        )
        if previous_key is not None and key <= previous_key:
            raise ValueError("rows must follow deterministic sequence")
        previous_key = key
    return rows


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    previous_index = -1
    for reason_code in reason_codes:
        _require_public_string("reason_code", reason_code)
        if reason_code not in REASON_CODE_SEQUENCE:
            raise ValueError("reason_codes must contain known values")
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        index = REASON_CODE_SEQUENCE.index(reason_code)
        if index <= previous_index:
            raise ValueError("reason_codes must follow deterministic sequence")
        seen.add(reason_code)
        previous_index = index
    return reason_codes


def _validate_row(row: ResearchDomainTeamPlaybookMemoryQualityRow) -> None:
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.triage_readiness_score != _triage_readiness_score(row.reason_codes):
        raise ValueError("triage_readiness_score must match reason_codes")
    if row.latest_feedback_at is not None and row.latest_feedback_at > row.observed_at:
        raise ValueError("latest_feedback_at must not follow observed_at")


def _validate_report(report: ResearchDomainTeamPlaybookMemoryQualityReport) -> None:
    if report.domain_team_count != _count(len(report.rows)):
        raise ValueError("domain_team_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.total_validated_lesson_count != _sum_decimal(
        tuple(row.validated_lesson_count for row in report.rows),
    ):
        raise ValueError("total_validated_lesson_count must match rows")
    if report.total_calibration_note_count != _sum_decimal(
        tuple(row.calibration_note_count for row in report.rows),
    ):
        raise ValueError("total_calibration_note_count must match rows")
    if report.total_unresolved_caveat_count != _sum_decimal(
        tuple(row.unresolved_caveat_count for row in report.rows),
    ):
        raise ValueError("total_unresolved_caveat_count must match rows")
    if report.max_feedback_age_seconds != max(
        (row.feedback_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_feedback_age_seconds must match rows")
    if report.min_triage_readiness_score != min(
        (row.triage_readiness_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("min_triage_readiness_score must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _status_count(
    rows: tuple[ResearchDomainTeamPlaybookMemoryQualityRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(row.status == status for row in rows))


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO))


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize(Decimal(value))


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    if later < earlier:
        raise ValueError("datetime values must not be in the future")
    delta = later - earlier
    with localcontext(DECIMAL_CONTEXT):
        seconds = (
            Decimal(delta.days) * SECONDS_PER_DAY
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
        )
    return _quantize(seconds)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in PLAYBOOK_MEMORY_QUALITY_STATUSES:
        raise ValueError(f"{field_name} must be one of pass/watch/block")
    return value


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a public label")
    if _has_unsafe_public_text(value):
        raise ValueError(f"{field_name} must be a public label")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a public label")
    if any(character not in PUBLIC_LABEL_CHARS for character in value):
        raise ValueError(f"{field_name} must be a public label")
    return value


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _reject_unsafe_public_text(field_name, value)
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be whole")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_payload_hard_flags(payload: dict[str, object]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if len(value) != SHA256_HEX_LENGTH:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _derived_validation_digest(value: object) -> str:
    payload = _payload_value(value)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a dict")
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    _reject_unsafe_public_payload("digest payload", digest_payload)
    canonical = json.dumps(
        digest_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _report_values_without_digest(
    report: ResearchDomainTeamPlaybookMemoryQualityReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _payload_value(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime value", value).isoformat()
    if value is None or type(value) in (str, bool):
        return value
    if type(value) in (int, float):
        raise ValueError("numeric payload values must use Decimal strings")
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_payload_value(item) for item in value]
    raise ValueError("payload value is not JSON compatible")


def _reject_unsafe_public_payload(label: str, value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_public_text(label, str(key))
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    if _has_unsafe_public_text(value):
        raise ValueError(f"{field_name} contains unsafe public text")


def _has_unsafe_public_text(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS)


__all__ = (
    "DEFAULT_RESEARCH_DOMAIN_TEAM_PLAYBOOK_MEMORY_QUALITY_CONFIG_VERSION",
    "PLAYBOOK_MEMORY_QUALITY_STATUSES",
    "ResearchDomainTeamPlaybookMemoryQualityConfig",
    "ResearchDomainTeamPlaybookMemoryQualityInput",
    "ResearchDomainTeamPlaybookMemoryQualityReport",
    "ResearchDomainTeamPlaybookMemoryQualityRow",
    "build_research_domain_team_playbook_memory_quality_report",
    "research_domain_team_playbook_memory_quality_report_digest",
    "research_domain_team_playbook_memory_quality_report_payload",
)
