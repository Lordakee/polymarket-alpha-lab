"""Pure deterministic research decision change-log reducer."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_RESEARCH_DECISION_CHANGE_LOG_CONFIG_VERSION = (
    "research-decision-change-log-v0"
)

CHANGE_STATUSES = ("pass", "watch", "block")
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_WEIGHT = {
    "block": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}

NO_RECORDS_REASON = "research_decision_change_no_records"
SCORE_DELTA_BLOCK_REASON = "score_delta_block"
TEAM_REVIEW_STATE_BLOCK_REASON = "team_review_state_block"
EVIDENCE_QUALITY_DELTA_BLOCK_REASON = "evidence_quality_delta_block"
SCORE_DELTA_WATCH_REASON = "score_delta_watch"
TEAM_REVIEW_STATE_WATCH_REASON = "team_review_state_watch"
EVIDENCE_QUALITY_DELTA_WATCH_REASON = "evidence_quality_delta_watch"
STABLE_REASON = "research_decision_change_stable"

REASON_CODE_SEQUENCE = (
    NO_RECORDS_REASON,
    SCORE_DELTA_BLOCK_REASON,
    TEAM_REVIEW_STATE_BLOCK_REASON,
    EVIDENCE_QUALITY_DELTA_BLOCK_REASON,
    SCORE_DELTA_WATCH_REASON,
    TEAM_REVIEW_STATE_WATCH_REASON,
    EVIDENCE_QUALITY_DELTA_WATCH_REASON,
    STABLE_REASON,
)
BLOCK_REASON_CODES = frozenset(
    (
        SCORE_DELTA_BLOCK_REASON,
        TEAM_REVIEW_STATE_BLOCK_REASON,
        EVIDENCE_QUALITY_DELTA_BLOCK_REASON,
    ),
)
WATCH_REASON_CODES = frozenset(
    (
        SCORE_DELTA_WATCH_REASON,
        TEAM_REVIEW_STATE_WATCH_REASON,
        EVIDENCE_QUALITY_DELTA_WATCH_REASON,
    ),
)

SAFE_PUBLIC_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "candidate_count",
        "pass_count",
        "watch_count",
        "block_count",
        "max_abs_score_delta",
        "max_abs_evidence_quality_delta",
        "status",
        "reason_codes",
        "reason_code_counts",
        "rows",
        "redacted_candidate_ref",
        "score_before",
        "score_after",
        "score_delta",
        "abs_score_delta",
        "team_review_before_state",
        "team_review_after_state",
        "evidence_quality_before",
        "evidence_quality_after",
        "evidence_quality_delta",
        "abs_evidence_quality_delta",
        "reason_code",
        "count",
        "candidate_ratio",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
RAW_CANDIDATE_KEY_COMPACTS = frozenset(
    (
        "candidateid",
        "rawcandidateid",
        "rawcandidateref",
        "candidatereference",
        "candidateslug",
    ),
)
MARKET_KEY_COMPACTS = frozenset(
    (
        "marketid",
        "rawmarketid",
        "marketslug",
        "marketquestion",
        "question",
        "slug",
    ),
)
SOURCE_KEY_COMPACTS = frozenset(
    (
        "dsn",
        "sourceref",
        "sourcerefs",
        "sourceurl",
        "sourceurls",
        "sourceuri",
        "sourceuris",
        "sourcetext",
        "sourceexcerpt",
        "sourcetitle",
        "url",
        "uri",
    ),
)
UNSAFE_KEY_COMPACTS = frozenset(
    (
        "au" + "th",
        "api" + "key",
        "private" + "key",
        "sec" + "ret",
        "to" + "ken",
        "wal" + "let",
        "or" + "der",
        "tr" + "ade",
        "b" + "uy",
        "s" + "ell",
        "rec" + "ommend",
        "rec" + "ommendation",
        "position",
        "positionsizing",
        "positionsize",
        "table",
        "tablename",
    ),
)
STATUS_ALIAS_VALUES = frozenset(("ready", "block" + "ed", "match" + "ed", "support" + "ed"))
UNSAFE_VALUE_TERMS = (
    "au" + "th",
    "api" + "_key",
    "api" + "-key",
    "api " + "key",
    "private" + "_key",
    "private" + "-key",
    "private " + "key",
    "sec" + "ret",
    "to" + "ken",
    "wal" + "let",
    "or" + "der",
    "tr" + "ade",
    "b" + "uy",
    "s" + "ell",
    "rec" + "ommend",
    "position" + "_size",
    "position" + "-size",
    "position" + " size",
    "position" + " sizing",
    " table",
    "table ",
)
SOURCE_VALUE_TERMS = (
    "http://",
    "https://",
    "www.",
    "://",
    ".com",
    ".org",
    ".net",
    ".io",
    ".co",
    ".test",
    ".app",
    ".dev",
    ".ai",
    ".gov",
    ".edu",
    "source_ref:",
    "source:",
    "source-report:",
    "dsn=",
    "postgres://",
    "postgresql://",
    "mysql://",
    "sqlite://",
    "supa" + "base",
)


@dataclass(frozen=True)
class ResearchDecisionChangeLogConfig:
    config_version: str = DEFAULT_RESEARCH_DECISION_CHANGE_LOG_CONFIG_VERSION
    watch_abs_score_delta: Decimal = Decimal("0.050000")
    block_abs_score_delta: Decimal = Decimal("0.200000")
    watch_abs_evidence_quality_delta: Decimal = Decimal("0.100000")
    block_abs_evidence_quality_delta: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchDecisionChangeLogConfig:
            raise ValueError("config must be a ResearchDecisionChangeLogConfig")
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_DECISION_CHANGE_LOG_CONFIG_VERSION:
            raise ValueError("config_version must be the supported version")
        for field_name in (
            "watch_abs_score_delta",
            "block_abs_score_delta",
            "watch_abs_evidence_quality_delta",
            "block_abs_evidence_quality_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_abs_score_delta < self.watch_abs_score_delta:
            raise ValueError("block_abs_score_delta must be at least watch_abs_score_delta")
        if (
            self.block_abs_evidence_quality_delta
            < self.watch_abs_evidence_quality_delta
        ):
            raise ValueError(
                "block_abs_evidence_quality_delta must be at least "
                "watch_abs_evidence_quality_delta",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchDecisionChangeLogRecord:
    redacted_candidate_ref: str
    score_before: Decimal
    score_after: Decimal
    team_review_before_state: str
    team_review_after_state: str
    evidence_quality_before: Decimal
    evidence_quality_after: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchDecisionChangeLogRecord:
            raise ValueError("record must be a ResearchDecisionChangeLogRecord")
        object.__setattr__(
            self,
            "redacted_candidate_ref",
            _require_redacted_candidate_ref(self.redacted_candidate_ref),
        )
        for field_name in (
            "score_before",
            "score_after",
            "evidence_quality_before",
            "evidence_quality_after",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("team_review_before_state", self.team_review_before_state)
        _require_status("team_review_after_state", self.team_review_after_state)
        _require_hard_flags("record", self)


@dataclass(frozen=True)
class ResearchDecisionChangeLogRow:
    generated_at: datetime
    redacted_candidate_ref: str
    score_before: Decimal
    score_after: Decimal
    score_delta: Decimal
    abs_score_delta: Decimal
    team_review_before_state: str
    team_review_after_state: str
    evidence_quality_before: Decimal
    evidence_quality_after: Decimal
    evidence_quality_delta: Decimal
    abs_evidence_quality_delta: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchDecisionChangeLogRow:
            raise ValueError("row must be a ResearchDecisionChangeLogRow")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "redacted_candidate_ref",
            _require_redacted_candidate_ref(self.redacted_candidate_ref),
        )
        for field_name in (
            "score_before",
            "score_after",
            "abs_score_delta",
            "evidence_quality_before",
            "evidence_quality_after",
            "abs_evidence_quality_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("score_delta", "evidence_quality_delta"):
            object.__setattr__(
                self,
                field_name,
                _normalize_signed_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("team_review_before_state", self.team_review_before_state)
        _require_status("team_review_after_state", self.team_review_after_state)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row(self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _digest_from_values(_row_payload_without_digest(self)),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _normalize_sha256("derived_validation_digest", self.derived_validation_digest),
            )
        if self.derived_validation_digest != _digest_from_values(
            _row_payload_without_digest(self),
        ):
            raise ValueError("derived_validation_digest must match row payload")


@dataclass(frozen=True)
class ResearchDecisionChangeLogReasonCodeCount:
    reason_code: str
    count: Decimal
    candidate_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchDecisionChangeLogReasonCodeCount:
            raise ValueError(
                "reason code count must be a ResearchDecisionChangeLogReasonCodeCount",
            )
        object.__setattr__(self, "reason_code", _require_reason_code(self.reason_code))
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_whole_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "candidate_ratio",
            _normalize_unit_decimal("candidate_ratio", self.candidate_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchDecisionChangeLogReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_abs_score_delta: Decimal
    max_abs_evidence_quality_delta: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchDecisionChangeLogReasonCodeCount, ...]
    rows: tuple[ResearchDecisionChangeLogRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchDecisionChangeLogReport:
            raise ValueError("report must be a ResearchDecisionChangeLogReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("candidate_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_abs_score_delta", "max_abs_evidence_quality_delta"):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _validate_report(self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _digest_from_values(_report_payload_without_digest(self)),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _normalize_sha256("derived_validation_digest", self.derived_validation_digest),
            )
        if self.derived_validation_digest != _digest_from_values(
            _report_payload_without_digest(self),
        ):
            raise ValueError("derived_validation_digest must match report payload")


def build_research_decision_change_log(
    records: Iterable[object],
    *,
    config: ResearchDecisionChangeLogConfig,
    generated_at: datetime,
) -> ResearchDecisionChangeLogReport:
    if isinstance(records, (str, bytes)):
        raise ValueError("records must be an iterable")
    try:
        record_rows = tuple(records)
    except TypeError as exc:
        raise ValueError("records must be an iterable") from exc
    if type(config) is not ResearchDecisionChangeLogConfig:
        raise ValueError("config must be a ResearchDecisionChangeLogConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)

    seen_refs: set[str] = set()
    rows: list[ResearchDecisionChangeLogRow] = []
    for record in record_rows:
        if type(record) is not ResearchDecisionChangeLogRecord:
            raise ValueError("records must contain ResearchDecisionChangeLogRecord values")
        _require_hard_flags("record", record)
        if record.redacted_candidate_ref in seen_refs:
            raise ValueError("duplicate redacted_candidate_ref")
        seen_refs.add(record.redacted_candidate_ref)
        rows.append(_row_from_record(record, config=config, generated_at=generated_at_utc))

    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    return ResearchDecisionChangeLogReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=_count_decimal(len(sorted_rows)),
        pass_count=_status_count(sorted_rows, "pass"),
        watch_count=_status_count(sorted_rows, "watch"),
        block_count=_status_count(sorted_rows, "block"),
        max_abs_score_delta=_max_abs_score_delta(sorted_rows),
        max_abs_evidence_quality_delta=_max_abs_evidence_quality_delta(sorted_rows),
        status=_report_status(sorted_rows),
        reason_codes=_report_reason_codes(sorted_rows),
        reason_code_counts=_reason_code_counts(sorted_rows),
        rows=sorted_rows,
    )


def research_decision_change_log_payload(
    report: ResearchDecisionChangeLogReport,
) -> dict[str, Any]:
    if type(report) is not ResearchDecisionChangeLogReport:
        raise ValueError("report must be a ResearchDecisionChangeLogReport")
    _require_hard_flags("report", report)
    _validate_report(report)
    if report.derived_validation_digest != _digest_from_values(
        _report_payload_without_digest(report),
    ):
        raise ValueError("derived_validation_digest must match report payload")
    payload = _report_payload(report)
    validate_research_decision_change_log_public_payload(payload)
    return payload


def validate_research_decision_change_log_public_payload(payload: dict[str, Any]) -> bool:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_payload(payload)
    _require_public_payload_flags(payload)
    return True


def _row_from_record(
    record: ResearchDecisionChangeLogRecord,
    *,
    config: ResearchDecisionChangeLogConfig,
    generated_at: datetime,
) -> ResearchDecisionChangeLogRow:
    score_delta = _quantize_signed(record.score_after - record.score_before)
    evidence_quality_delta = _quantize_signed(
        record.evidence_quality_after - record.evidence_quality_before,
    )
    abs_score_delta = abs(score_delta).quantize(QUANTUM)
    abs_evidence_quality_delta = abs(evidence_quality_delta).quantize(QUANTUM)
    reason_codes = _row_reason_codes(
        record,
        abs_score_delta=abs_score_delta,
        abs_evidence_quality_delta=abs_evidence_quality_delta,
        config=config,
    )
    return ResearchDecisionChangeLogRow(
        generated_at=generated_at,
        redacted_candidate_ref=record.redacted_candidate_ref,
        score_before=record.score_before,
        score_after=record.score_after,
        score_delta=score_delta,
        abs_score_delta=abs_score_delta,
        team_review_before_state=record.team_review_before_state,
        team_review_after_state=record.team_review_after_state,
        evidence_quality_before=record.evidence_quality_before,
        evidence_quality_after=record.evidence_quality_after,
        evidence_quality_delta=evidence_quality_delta,
        abs_evidence_quality_delta=abs_evidence_quality_delta,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    record: ResearchDecisionChangeLogRecord,
    *,
    abs_score_delta: Decimal,
    abs_evidence_quality_delta: Decimal,
    config: ResearchDecisionChangeLogConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if abs_score_delta >= config.block_abs_score_delta:
        reason_codes.append(SCORE_DELTA_BLOCK_REASON)
    elif abs_score_delta >= config.watch_abs_score_delta:
        reason_codes.append(SCORE_DELTA_WATCH_REASON)

    if record.team_review_after_state == "block":
        reason_codes.append(TEAM_REVIEW_STATE_BLOCK_REASON)
    elif (
        record.team_review_after_state == "watch"
        or record.team_review_after_state != record.team_review_before_state
    ):
        reason_codes.append(TEAM_REVIEW_STATE_WATCH_REASON)

    if abs_evidence_quality_delta >= config.block_abs_evidence_quality_delta:
        reason_codes.append(EVIDENCE_QUALITY_DELTA_BLOCK_REASON)
    elif abs_evidence_quality_delta >= config.watch_abs_evidence_quality_delta:
        reason_codes.append(EVIDENCE_QUALITY_DELTA_WATCH_REASON)

    if not reason_codes:
        reason_codes.append(STABLE_REASON)
    return _sort_reason_codes(tuple(dict.fromkeys(reason_codes)))


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchDecisionChangeLogRow, ...]) -> str:
    if not rows:
        return "watch"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(rows: tuple[ResearchDecisionChangeLogRow, ...]) -> tuple[str, ...]:
    if not rows:
        return (NO_RECORDS_REASON,)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _sort_reason_codes(tuple(dict.fromkeys(reason_codes)))


def _reason_code_counts(
    rows: tuple[ResearchDecisionChangeLogRow, ...],
) -> tuple[ResearchDecisionChangeLogReasonCodeCount, ...]:
    if not rows:
        return ()
    candidate_count = _count_decimal(len(rows))
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        ResearchDecisionChangeLogReasonCodeCount(
            reason_code=reason_code,
            count=count,
            candidate_ratio=_quantize(count / candidate_count),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: _reason_code_sort_key(item[0]),
        )
    )


def _status_count(rows: tuple[ResearchDecisionChangeLogRow, ...], status: str) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _max_abs_score_delta(rows: tuple[ResearchDecisionChangeLogRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    return max(row.abs_score_delta for row in rows)


def _max_abs_evidence_quality_delta(
    rows: tuple[ResearchDecisionChangeLogRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.abs_evidence_quality_delta for row in rows)


def _row_sort_key(row: ResearchDecisionChangeLogRow) -> tuple[Decimal, str]:
    return (STATUS_WEIGHT[row.status], row.redacted_candidate_ref)


def _validate_row(row: ResearchDecisionChangeLogRow) -> None:
    if row.score_delta != _quantize_signed(row.score_after - row.score_before):
        raise ValueError("score_delta must match score_before and score_after")
    if row.abs_score_delta != abs(row.score_delta).quantize(QUANTUM):
        raise ValueError("abs_score_delta must match score_delta")
    if row.evidence_quality_delta != _quantize_signed(
        row.evidence_quality_after - row.evidence_quality_before,
    ):
        raise ValueError(
            "evidence_quality_delta must match evidence_quality_before and "
            "evidence_quality_after",
        )
    if row.abs_evidence_quality_delta != abs(row.evidence_quality_delta).quantize(
        QUANTUM,
    ):
        raise ValueError("abs_evidence_quality_delta must match evidence_quality_delta")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchDecisionChangeLogReport) -> None:
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    if report.candidate_count != _count_decimal(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.max_abs_score_delta != _max_abs_score_delta(report.rows):
        raise ValueError("max_abs_score_delta must match rows")
    if report.max_abs_evidence_quality_delta != _max_abs_evidence_quality_delta(
        report.rows,
    ):
        raise ValueError("max_abs_evidence_quality_delta must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if len({row.redacted_candidate_ref for row in report.rows}) != len(report.rows):
        raise ValueError("rows must be unique by redacted_candidate_ref")


def _normalize_rows(value: object) -> tuple[ResearchDecisionChangeLogRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_refs: set[str] = set()
    for row in rows:
        if type(row) is not ResearchDecisionChangeLogRow:
            raise ValueError("rows must contain ResearchDecisionChangeLogRow values")
        _require_hard_flags("row", row)
        if row.redacted_candidate_ref in seen_refs:
            raise ValueError("rows must be unique by redacted_candidate_ref")
        seen_refs.add(row.redacted_candidate_ref)
    return tuple(sorted(rows, key=_row_sort_key))


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchDecisionChangeLogReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    reason_code_counts = tuple(value)
    for item in reason_code_counts:
        if type(item) is not ResearchDecisionChangeLogReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchDecisionChangeLogReasonCodeCount",
            )
    return tuple(
        sorted(reason_code_counts, key=lambda item: _reason_code_sort_key(item.reason_code)),
    )


def _sort_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted(reason_codes, key=_reason_code_sort_key))


def _reason_code_sort_key(reason_code: str) -> tuple[Decimal, str]:
    if reason_code in REASON_CODE_SEQUENCE:
        return (Decimal(REASON_CODE_SEQUENCE.index(reason_code)), reason_code)
    return (Decimal(len(REASON_CODE_SEQUENCE)), reason_code)


def _normalize_reason_codes(
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not allow_empty and not reason_codes:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_reason_code(reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
    if reason_codes != _sort_reason_codes(reason_codes):
        raise ValueError("reason_codes must be deterministic")
    return reason_codes


def _require_reason_code(reason_code: object) -> str:
    if type(reason_code) is not str:
        raise ValueError("reason_code must be a string")
    if reason_code not in REASON_CODE_SEQUENCE:
        raise ValueError("reason_code must be supported")
    return reason_code


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be at most 1.000000")
    return decimal_value


def _normalize_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.quantize(Decimal("1")):
        raise ValueError(f"{field_name} must be integral")
    return decimal_value


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_signed_decimal(field_name: str, value: object) -> Decimal:
    return _require_decimal(field_name, value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        with localcontext(DECIMAL_CONTEXT):
            decimal_value = value.quantize(QUANTUM)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc
    if decimal_value != value:
        raise ValueError(f"{field_name} must use no more than six decimal places")
    return ZERO if decimal_value == ZERO else decimal_value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        decimal_value = value.quantize(QUANTUM)
    return ZERO if decimal_value == ZERO else decimal_value


def _quantize_signed(value: Decimal) -> Decimal:
    return _quantize(value)


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in CHANGE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical nonblank text")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")


def _require_redacted_candidate_ref(value: object) -> str:
    if type(value) is not str:
        raise ValueError("redacted_candidate_ref must be a string")
    if not _is_redacted_candidate_ref(value):
        raise ValueError("redacted_candidate_ref must be a redacted candidate digest")
    return value


def _is_redacted_candidate_ref(value: str) -> bool:
    prefix = "candidate_ref_"
    if not value.startswith(prefix) or len(value) != len(prefix) + 64:
        return False
    digest = value[len(prefix) :]
    return all(character in "0123456789abcdef" for character in digest)


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if not all(character in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _row_payload_without_digest(row: ResearchDecisionChangeLogRow) -> dict[str, Any]:
    return {
        "generated_at": _json_ready(row.generated_at),
        "redacted_candidate_ref": row.redacted_candidate_ref,
        "score_before": _json_ready(row.score_before),
        "score_after": _json_ready(row.score_after),
        "score_delta": _json_ready(row.score_delta),
        "abs_score_delta": _json_ready(row.abs_score_delta),
        "team_review_before_state": row.team_review_before_state,
        "team_review_after_state": row.team_review_after_state,
        "evidence_quality_before": _json_ready(row.evidence_quality_before),
        "evidence_quality_after": _json_ready(row.evidence_quality_after),
        "evidence_quality_delta": _json_ready(row.evidence_quality_delta),
        "abs_evidence_quality_delta": _json_ready(row.abs_evidence_quality_delta),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _row_payload(row: ResearchDecisionChangeLogRow) -> dict[str, Any]:
    payload = _row_payload_without_digest(row)
    payload["derived_validation_digest"] = row.derived_validation_digest
    return payload


def _reason_code_count_payload(
    item: ResearchDecisionChangeLogReasonCodeCount,
) -> dict[str, Any]:
    return {
        "reason_code": item.reason_code,
        "count": _json_ready(item.count),
        "candidate_ratio": _json_ready(item.candidate_ratio),
        "paper_only": item.paper_only,
        "report_only": item.report_only,
        "readonly": item.readonly,
    }


def _report_payload_without_digest(
    report: ResearchDecisionChangeLogReport,
) -> dict[str, Any]:
    return {
        "generated_at": _json_ready(report.generated_at),
        "config_version": report.config_version,
        "candidate_count": _json_ready(report.candidate_count),
        "pass_count": _json_ready(report.pass_count),
        "watch_count": _json_ready(report.watch_count),
        "block_count": _json_ready(report.block_count),
        "max_abs_score_delta": _json_ready(report.max_abs_score_delta),
        "max_abs_evidence_quality_delta": _json_ready(
            report.max_abs_evidence_quality_delta,
        ),
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "reason_code_counts": [
            _reason_code_count_payload(item) for item in report.reason_code_counts
        ],
        "rows": [_row_payload(row) for row in report.rows],
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _report_payload(report: ResearchDecisionChangeLogReport) -> dict[str, Any]:
    return {
        "generated_at": _json_ready(report.generated_at),
        "config_version": report.config_version,
        "candidate_count": _json_ready(report.candidate_count),
        "pass_count": _json_ready(report.pass_count),
        "watch_count": _json_ready(report.watch_count),
        "block_count": _json_ready(report.block_count),
        "max_abs_score_delta": _json_ready(report.max_abs_score_delta),
        "max_abs_evidence_quality_delta": _json_ready(
            report.max_abs_evidence_quality_delta,
        ),
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "reason_code_counts": [
            _reason_code_count_payload(item) for item in report.reason_code_counts
        ],
        "rows": [_row_payload(row) for row in report.rows],
        "derived_validation_digest": report.derived_validation_digest,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _json_ready(value: Any) -> Any:
    if type(value) is Decimal:
        return format(value.quantize(QUANTUM), "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if type(value) in (str, bool) or value is None:
        return value
    if type(value) in (int, float):
        raise ValueError("payload contains non-Decimal numeric value")
    return value


def _digest_from_values(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _reject_unsafe_public_payload(payload: dict[str, Any]) -> None:
    _walk_public_value(payload, parent_key="")


def _walk_public_value(value: Any, *, parent_key: str) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _walk_public_value(asdict(value), parent_key=parent_key)
        return
    if isinstance(value, dict):
        for key, child in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _walk_public_value(child, parent_key=key)
            _reject_unsafe_public_key(key)
        return
    if isinstance(value, list):
        for child in value:
            _walk_public_value(child, parent_key=parent_key)
        return
    if type(value) in (int, float) and type(value) is not bool:
        raise ValueError("public payload numeric values must be decimal strings")
    if type(value) is str:
        _reject_unsafe_public_string(parent_key, value)


def _reject_unsafe_public_key(key: str) -> None:
    compact = _compact_key(key)
    if compact not in _compact_key_set(SAFE_PUBLIC_KEYS):
        if compact in RAW_CANDIDATE_KEY_COMPACTS:
            raise ValueError("public payload leaks raw candidate identity")
        if compact in MARKET_KEY_COMPACTS:
            raise ValueError("public payload leaks market identity")
        if compact in SOURCE_KEY_COMPACTS:
            raise ValueError("public payload leaks source material")
        if compact in UNSAFE_KEY_COMPACTS:
            raise ValueError("public payload contains unsafe live surface field")
        raise ValueError(f"public payload contains unsupported key: {key}")
    if compact in RAW_CANDIDATE_KEY_COMPACTS:
        raise ValueError("public payload leaks raw candidate identity")
    if compact in MARKET_KEY_COMPACTS:
        raise ValueError("public payload leaks market identity")
    if compact in SOURCE_KEY_COMPACTS:
        raise ValueError("public payload leaks source material")
    if compact in UNSAFE_KEY_COMPACTS:
        raise ValueError("public payload contains unsafe live surface field")


def _reject_unsafe_public_string(parent_key: str, value: str) -> None:
    lowered = value.lower()
    if lowered in STATUS_ALIAS_VALUES:
        raise ValueError("public payload uses unsupported status alias")
    if parent_key == "redacted_candidate_ref" and not _is_redacted_candidate_ref(value):
        raise ValueError("public payload leaks raw candidate identity")
    if any(term in lowered for term in SOURCE_VALUE_TERMS):
        raise ValueError("public payload leaks source material")
    if any(term in lowered for term in UNSAFE_VALUE_TERMS):
        raise ValueError("public payload contains unsafe live surface language")


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for public payload")


def _compact_key(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def _compact_key_set(values: frozenset[str]) -> frozenset[str]:
    return frozenset(_compact_key(value) for value in values)


__all__ = (
    "CHANGE_STATUSES",
    "DEFAULT_RESEARCH_DECISION_CHANGE_LOG_CONFIG_VERSION",
    "ResearchDecisionChangeLogConfig",
    "ResearchDecisionChangeLogRecord",
    "ResearchDecisionChangeLogRow",
    "ResearchDecisionChangeLogReasonCodeCount",
    "ResearchDecisionChangeLogReport",
    "build_research_decision_change_log",
    "research_decision_change_log_payload",
    "validate_research_decision_change_log_public_payload",
)
