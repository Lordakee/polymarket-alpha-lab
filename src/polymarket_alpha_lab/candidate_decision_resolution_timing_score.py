"""Pure paper-only resolution/finalization timing score for candidates."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_CANDIDATE_DECISION_RESOLUTION_TIMING_SCORE_CONFIG_VERSION = (
    "candidate-decision-resolution-timing-score-v0"
)
BOUNDARY_STATEMENT = (
    "Paper-only report-only readonly candidate resolution timing score; "
    "decision-support gates only."
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
BASE_CLEAR_TIMING_SCORE = Decimal("0.850000")
TIME_TO_CLOSE_WATCH_PENALTY = Decimal("0.100000")
EXPECTED_RESOLUTION_LAG_WATCH_PENALTY = Decimal("0.150000")
DISPUTE_WINDOW_WATCH_PENALTY = Decimal("0.150000")
CASH_LOCKUP_WATCH_PENALTY = Decimal("0.200000")
EVENT_CLOCK_CONFIDENCE_WATCH_PENALTY = Decimal("0.150000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

TIMING_STATUSES = ("pass", "watch", "block")

NO_CANDIDATES_REASON = "resolution_timing_no_candidates"
PASS_REASON = "resolution_timing_pass"
FINALIZATION_TIME_UNCLEAR_BLOCK_REASON = "finalization_time_unclear_block"
TIME_TO_CLOSE_BLOCK_REASON = "time_to_close_days_block"
EXPECTED_RESOLUTION_LAG_BLOCK_REASON = "expected_resolution_lag_days_block"
DISPUTE_WINDOW_BLOCK_REASON = "dispute_window_days_block"
CASH_LOCKUP_BLOCK_REASON = "cash_lockup_days_block"
OFFICIAL_RESULT_UNAVAILABLE_BLOCK_REASON = "official_result_unavailable_block"
EVENT_CLOCK_CONFIDENCE_MISSING_REASON = "event_clock_confidence_missing"
EVENT_CLOCK_CONFIDENCE_BLOCK_REASON = "event_clock_confidence_block"
TIMING_SCORE_BLOCK_REASON = "timing_score_below_watch_threshold"
TIME_TO_CLOSE_WATCH_REASON = "time_to_close_days_watch"
EXPECTED_RESOLUTION_LAG_WATCH_REASON = "expected_resolution_lag_days_watch"
DISPUTE_WINDOW_WATCH_REASON = "dispute_window_days_watch"
CASH_LOCKUP_WATCH_REASON = "cash_lockup_days_watch"
EVENT_CLOCK_CONFIDENCE_WATCH_REASON = "event_clock_confidence_watch"
TIMING_SCORE_WATCH_REASON = "timing_score_below_pass_threshold"

REASON_CODE_SEQUENCE = (
    NO_CANDIDATES_REASON,
    FINALIZATION_TIME_UNCLEAR_BLOCK_REASON,
    TIME_TO_CLOSE_BLOCK_REASON,
    EXPECTED_RESOLUTION_LAG_BLOCK_REASON,
    DISPUTE_WINDOW_BLOCK_REASON,
    CASH_LOCKUP_BLOCK_REASON,
    OFFICIAL_RESULT_UNAVAILABLE_BLOCK_REASON,
    EVENT_CLOCK_CONFIDENCE_MISSING_REASON,
    EVENT_CLOCK_CONFIDENCE_BLOCK_REASON,
    TIMING_SCORE_BLOCK_REASON,
    TIME_TO_CLOSE_WATCH_REASON,
    EXPECTED_RESOLUTION_LAG_WATCH_REASON,
    DISPUTE_WINDOW_WATCH_REASON,
    CASH_LOCKUP_WATCH_REASON,
    EVENT_CLOCK_CONFIDENCE_WATCH_REASON,
    TIMING_SCORE_WATCH_REASON,
    PASS_REASON,
)
BLOCK_REASON_CODES = frozenset(
    (
        NO_CANDIDATES_REASON,
        FINALIZATION_TIME_UNCLEAR_BLOCK_REASON,
        EVENT_CLOCK_CONFIDENCE_MISSING_REASON,
        TIME_TO_CLOSE_BLOCK_REASON,
        EXPECTED_RESOLUTION_LAG_BLOCK_REASON,
        DISPUTE_WINDOW_BLOCK_REASON,
        CASH_LOCKUP_BLOCK_REASON,
        OFFICIAL_RESULT_UNAVAILABLE_BLOCK_REASON,
        EVENT_CLOCK_CONFIDENCE_BLOCK_REASON,
        TIMING_SCORE_BLOCK_REASON,
    ),
)
WATCH_REASON_CODES = frozenset(
    (
        TIME_TO_CLOSE_WATCH_REASON,
        EXPECTED_RESOLUTION_LAG_WATCH_REASON,
        DISPUTE_WINDOW_WATCH_REASON,
        CASH_LOCKUP_WATCH_REASON,
        EVENT_CLOCK_CONFIDENCE_WATCH_REASON,
        TIMING_SCORE_WATCH_REASON,
    ),
)
UNSAFE_PUBLIC_VALUE_TERMS = (
    "live",
    "a" + "uth",
    "acc" + "ount",
    "balance",
    "or" + "der",
    "submit " + "order",
    "can" + "cel",
    "rep" + "lace",
    "sig" + "ning",
    "ex" + "change " + "mutation",
    "private " + "key",
    "private" + "_key",
    "private" + "-" + "key",
    "api " + "key",
    "api" + "_key",
    "api" + "-" + "key",
    "secret",
    "token",
    "wal" + "let",
    "http://",
    "https://",
    "www.",
    "://",
    "dsn=",
    "table:",
    "b" + "uy",
    "s" + "ell",
    "tra" + "de",
    "position" + "_size",
    "position" + " sizing",
    "position" + "-size",
    "position" + " size",
    "reco" + "mmendation",
    "reco" + "mmend ",
)
RAW_CANDIDATE_SURFACE_TERMS = (
    "candidate" + "_id",
    "candidate" + ":",
    "raw_" + "candidate" + "_id",
    "candidate" + "_slug",
)
RAW_MARKET_SURFACE_TERMS = (
    "market_id",
    "condition_id",
    "question",
    "0x",
)
SOURCE_REFERENCE_VALUE_TERMS = (
    "http://",
    "https://",
    "www.",
    "://",
    "dsn=",
    "table:",
    "schema:",
    "select ",
    " from ",
    "postgres://",
    "postgresql://",
    "mysql://",
    "supa" + "base",
)
RAW_CANDIDATE_PUBLIC_PAYLOAD_KEY_TERMS = (
    "candidate" + "_id",
    "raw_" + "candidate" + "_id",
    "raw_" + "candidate" + "_ref",
    "candidate" + "_slug",
    "candidate" + "_reference",
)
UNSAFE_PUBLIC_PAYLOAD_KEY_TERMS = (
    "source_report_refs",
    "source_ref",
    "source_refs",
    "source_url",
    "source_uri",
    "source_" + "text",
    "source_excerpt",
    "source_title",
    "raw_" + "text",
    "market_" + "text",
    "url",
    "market_id",
    "condition_id",
    "market_slug",
    "question",
    "dsn",
    "table",
    "pri" + "vate" + "_key",
    "position" + "_size",
)
STRICT_PUBLIC_SOURCE_VALUE_TERMS = (
    "resolution-calendar:",
    "official-result-check:",
    "source-report:",
    "source_ref:",
    "source:",
    "market:",
    "market_slug:",
    "condition:",
    "question:",
    "dsn=",
    "table:",
    "table=",
    "_table",
    " table ",
)
URLISH_PUBLIC_VALUE_TERMS = (
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
)


@dataclass(frozen=True)
class CandidateDecisionResolutionTimingScoreConfig:
    config_version: str = (
        DEFAULT_CANDIDATE_DECISION_RESOLUTION_TIMING_SCORE_CONFIG_VERSION
    )
    min_pass_timing_score: Decimal = Decimal("0.750000")
    min_watch_timing_score: Decimal = Decimal("0.500000")
    max_pass_time_to_close_days: Decimal = Decimal("14.000000")
    max_watch_time_to_close_days: Decimal = Decimal("30.000000")
    max_pass_expected_resolution_lag_days: Decimal = Decimal("2.000000")
    max_watch_expected_resolution_lag_days: Decimal = Decimal("7.000000")
    max_pass_dispute_window_days: Decimal = Decimal("1.000000")
    max_watch_dispute_window_days: Decimal = Decimal("3.000000")
    max_pass_cash_lockup_days: Decimal = Decimal("7.000000")
    max_watch_cash_lockup_days: Decimal = Decimal("21.000000")
    min_pass_event_clock_confidence: Decimal = Decimal("0.800000")
    min_watch_event_clock_confidence: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionResolutionTimingScoreConfig:
            raise ValueError(
                "config must be a CandidateDecisionResolutionTimingScoreConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_CANDIDATE_DECISION_RESOLUTION_TIMING_SCORE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported version")
        for field_name in (
            "min_pass_timing_score",
            "min_watch_timing_score",
            "min_pass_event_clock_confidence",
            "min_watch_event_clock_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_time_to_close_days",
            "max_watch_time_to_close_days",
            "max_pass_expected_resolution_lag_days",
            "max_watch_expected_resolution_lag_days",
            "max_pass_dispute_window_days",
            "max_watch_dispute_window_days",
            "max_pass_cash_lockup_days",
            "max_watch_cash_lockup_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        reject_unsafe_surface_fields("resolution timing score config", self)
        _reject_unsafe_public_values("resolution timing score config", self)
        require_paper_only_flags("CandidateDecisionResolutionTimingScoreConfig", self)


@dataclass(frozen=True)
class CandidateDecisionResolutionTimingScoreInput:
    redacted_candidate_ref: str
    time_to_close_days: Decimal
    expected_resolution_lag_days: Decimal
    dispute_window_days: Decimal
    cash_lockup_days: Decimal
    event_clock_confidence: Decimal | None
    source_report_refs: tuple[str, ...]
    finalization_time_is_clear: bool = True
    official_result_available: bool = True
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionResolutionTimingScoreInput:
            raise ValueError(
                "input must be a CandidateDecisionResolutionTimingScoreInput",
            )
        object.__setattr__(
            self,
            "redacted_candidate_ref",
            _require_redacted_candidate_ref(self.redacted_candidate_ref),
        )
        for field_name in (
            "time_to_close_days",
            "expected_resolution_lag_days",
            "dispute_window_days",
            "cash_lockup_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "finalization_time_is_clear",
            "official_result_available",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_bool(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "event_clock_confidence",
            _normalize_optional_unit_decimal(
                "event_clock_confidence",
                self.event_clock_confidence,
            ),
        )
        object.__setattr__(
            self,
            "source_report_refs",
            _normalize_public_reference_tuple(
                "source_report_refs",
                self.source_report_refs,
            ),
        )
        reject_unsafe_surface_fields("resolution timing score input", self)
        _reject_unsafe_public_values("resolution timing score input", self)
        require_paper_only_flags("CandidateDecisionResolutionTimingScoreInput", self)


@dataclass(frozen=True)
class CandidateDecisionResolutionTimingScoreRow:
    generated_at: datetime
    redacted_candidate_ref: str
    time_to_close_days: Decimal
    expected_resolution_lag_days: Decimal
    dispute_window_days: Decimal
    cash_lockup_days: Decimal
    finalization_time_is_clear: bool
    official_result_available: bool
    event_clock_confidence: Decimal | None
    timing_score: Decimal
    timing_status: str
    hard_blocker_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    source_report_refs: tuple[str, ...]
    derived_validation_digest: str
    boundary_statement: str = BOUNDARY_STATEMENT
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionResolutionTimingScoreRow:
            raise ValueError("row must be a CandidateDecisionResolutionTimingScoreRow")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "redacted_candidate_ref",
            _require_redacted_candidate_ref(self.redacted_candidate_ref),
        )
        for field_name in (
            "time_to_close_days",
            "expected_resolution_lag_days",
            "dispute_window_days",
            "cash_lockup_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "finalization_time_is_clear",
            "official_result_available",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_bool(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "event_clock_confidence",
            _normalize_optional_unit_decimal(
                "event_clock_confidence",
                self.event_clock_confidence,
            ),
        )
        object.__setattr__(
            self,
            "timing_score",
            _normalize_unit_decimal("timing_score", self.timing_score),
        )
        _require_member("timing_status", self.timing_status, TIMING_STATUSES)
        object.__setattr__(
            self,
            "hard_blocker_codes",
            _normalize_reason_codes(self.hard_blocker_codes, allow_empty=True),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "source_report_refs",
            _normalize_public_reference_tuple(
                "source_report_refs",
                self.source_report_refs,
            ),
        )
        _require_validation_digest(self.derived_validation_digest)
        if self.boundary_statement != BOUNDARY_STATEMENT:
            raise ValueError("boundary_statement must match paper-only scope")
        reject_unsafe_surface_fields("resolution timing score row", self)
        _reject_unsafe_public_values("resolution timing score row", self)
        require_paper_only_flags("CandidateDecisionResolutionTimingScoreRow", self)
        _validate_row(self)
        if self.derived_validation_digest != _row_digest_from_values(
            _row_values_without_digest(self),
        ):
            raise ValueError("derived_validation_digest must match row payload")


@dataclass(frozen=True)
class CandidateDecisionResolutionTimingReasonCodeCount:
    reason_code: str
    count: Decimal
    candidate_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionResolutionTimingReasonCodeCount:
            raise ValueError(
                "reason code count must be a "
                "CandidateDecisionResolutionTimingReasonCodeCount",
            )
        object.__setattr__(
            self,
            "reason_code",
            _require_reason_code(self.reason_code),
        )
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
        reject_unsafe_surface_fields("resolution timing reason count", self)
        _reject_unsafe_public_values("resolution timing reason count", self)
        require_paper_only_flags(
            "CandidateDecisionResolutionTimingReasonCodeCount",
            self,
        )


@dataclass(frozen=True)
class CandidateDecisionResolutionTimingScoreReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    max_timing_score: Decimal
    min_timing_score: Decimal
    timing_status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[CandidateDecisionResolutionTimingReasonCodeCount, ...]
    rows: tuple[CandidateDecisionResolutionTimingScoreRow, ...]
    derived_validation_digest: str
    boundary_statement: str = BOUNDARY_STATEMENT
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionResolutionTimingScoreReport:
            raise ValueError("report must be a CandidateDecisionResolutionTimingScoreReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in ("max_timing_score", "min_timing_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("timing_status", self.timing_status, TIMING_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_validation_digest(self.derived_validation_digest)
        if self.boundary_statement != BOUNDARY_STATEMENT:
            raise ValueError("boundary_statement must match paper-only scope")
        reject_unsafe_surface_fields("resolution timing score report", self)
        _reject_unsafe_public_values("resolution timing score report", self)
        require_paper_only_flags("CandidateDecisionResolutionTimingScoreReport", self)
        _validate_report(self)
        if self.derived_validation_digest != _report_digest_from_values(
            _report_values_without_digest(self),
        ):
            raise ValueError("derived_validation_digest must match report payload")


def build_candidate_decision_resolution_timing_score_report(
    candidates: Iterable[CandidateDecisionResolutionTimingScoreInput],
    *,
    config: CandidateDecisionResolutionTimingScoreConfig,
    generated_at: datetime,
) -> CandidateDecisionResolutionTimingScoreReport:
    if type(config) is not CandidateDecisionResolutionTimingScoreConfig:
        raise ValueError(
            "config must be a CandidateDecisionResolutionTimingScoreConfig",
        )
    require_paper_only_flags("CandidateDecisionResolutionTimingScoreConfig", config)
    reject_unsafe_surface_fields("resolution timing score config", config)
    _reject_unsafe_public_values("resolution timing score config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_candidates = _normalize_candidates(candidates)
    rows = tuple(
        sorted(
            (
                _row_for_candidate(
                    candidate,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for candidate in normalized_candidates
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    timing_status = _status_from_reason_codes(reason_codes)
    report_values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "candidate_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "blocked_count": _status_count(rows, "block"),
        "max_timing_score": _max_timing_score(rows),
        "min_timing_score": _min_timing_score(rows),
        "timing_status": timing_status,
        "reason_codes": reason_codes,
        "reason_code_counts": _reason_code_counts(rows, reason_codes),
        "rows": rows,
        "boundary_statement": BOUNDARY_STATEMENT,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return CandidateDecisionResolutionTimingScoreReport(
        **report_values,
        derived_validation_digest=_report_digest_from_values(report_values),
    )


def candidate_decision_resolution_timing_score_payload(
    report: CandidateDecisionResolutionTimingScoreReport,
) -> dict[str, Any]:
    if type(report) is not CandidateDecisionResolutionTimingScoreReport:
        raise ValueError(
            "report must be a CandidateDecisionResolutionTimingScoreReport",
        )
    require_paper_only_flags("CandidateDecisionResolutionTimingScoreReport", report)
    reject_unsafe_surface_fields("resolution timing score report", report)
    _reject_unsafe_public_values("resolution timing score report", report)
    payload = json_ready_no_floats(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    payload = _redact_public_payload_source_refs(payload)
    validate_candidate_decision_resolution_timing_score_public_payload(payload)
    return payload


def validate_candidate_decision_resolution_timing_score_public_payload(
    payload: object,
) -> None:
    if not isinstance(payload, dict):
        raise ValueError("public payload must be a JSON object")
    reject_unsafe_surface_fields("resolution timing score public payload", payload)
    _reject_unsafe_public_payload_keys(
        "resolution timing score public payload",
        payload,
    )
    _reject_unsupported_public_status_values(
        "resolution timing score public payload",
        payload,
    )
    _reject_public_numeric_values(
        "resolution timing score public payload",
        payload,
    )
    _reject_unsafe_public_values("resolution timing score public payload", payload)
    _reject_strict_public_payload_values(
        "resolution timing score public payload",
        payload,
    )


def _redact_public_payload_source_refs(payload: dict[str, Any]) -> dict[str, Any]:
    redacted = dict(payload)
    rows = redacted.get("rows")
    if isinstance(rows, list):
        redacted["rows"] = [
            _row_payload_without_source_refs(row) for row in rows
        ]
    return redacted


def _row_payload_without_source_refs(row: object) -> object:
    if not isinstance(row, dict):
        return row
    redacted = dict(row)
    redacted.pop("source_report_refs", None)
    return redacted


def _row_for_candidate(
    candidate: CandidateDecisionResolutionTimingScoreInput,
    *,
    config: CandidateDecisionResolutionTimingScoreConfig,
    generated_at: datetime,
) -> CandidateDecisionResolutionTimingScoreRow:
    initial_reason_codes = _field_reason_codes(candidate, config)
    initial_hard_blockers = _hard_blocker_codes(initial_reason_codes)
    if initial_hard_blockers:
        timing_score = ZERO
    else:
        timing_score = _timing_score(candidate, config)
    reason_codes = _reason_codes_with_score(
        initial_reason_codes,
        timing_score=timing_score,
        config=config,
    )
    hard_blockers = _hard_blocker_codes(reason_codes)
    timing_status = _status_from_reason_codes(reason_codes)
    if timing_status == "block":
        timing_score = ZERO
    row_values: dict[str, object] = {
        "generated_at": generated_at,
        "redacted_candidate_ref": candidate.redacted_candidate_ref,
        "time_to_close_days": candidate.time_to_close_days,
        "expected_resolution_lag_days": candidate.expected_resolution_lag_days,
        "dispute_window_days": candidate.dispute_window_days,
        "cash_lockup_days": candidate.cash_lockup_days,
        "finalization_time_is_clear": candidate.finalization_time_is_clear,
        "official_result_available": candidate.official_result_available,
        "event_clock_confidence": candidate.event_clock_confidence,
        "timing_score": timing_score,
        "timing_status": timing_status,
        "hard_blocker_codes": hard_blockers,
        "reason_codes": reason_codes,
        "source_report_refs": candidate.source_report_refs,
        "boundary_statement": BOUNDARY_STATEMENT,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return CandidateDecisionResolutionTimingScoreRow(
        **row_values,
        derived_validation_digest=_row_digest_from_values(row_values),
    )


def _field_reason_codes(
    candidate: CandidateDecisionResolutionTimingScoreInput,
    config: CandidateDecisionResolutionTimingScoreConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if not candidate.finalization_time_is_clear:
        reason_codes.append(FINALIZATION_TIME_UNCLEAR_BLOCK_REASON)
    _append_maximum_reason(
        reason_codes,
        candidate.time_to_close_days,
        pass_threshold=config.max_pass_time_to_close_days,
        watch_threshold=config.max_watch_time_to_close_days,
        watch_reason=TIME_TO_CLOSE_WATCH_REASON,
        block_reason=TIME_TO_CLOSE_BLOCK_REASON,
    )
    _append_maximum_reason(
        reason_codes,
        candidate.expected_resolution_lag_days,
        pass_threshold=config.max_pass_expected_resolution_lag_days,
        watch_threshold=config.max_watch_expected_resolution_lag_days,
        watch_reason=EXPECTED_RESOLUTION_LAG_WATCH_REASON,
        block_reason=EXPECTED_RESOLUTION_LAG_BLOCK_REASON,
    )
    _append_maximum_reason(
        reason_codes,
        candidate.dispute_window_days,
        pass_threshold=config.max_pass_dispute_window_days,
        watch_threshold=config.max_watch_dispute_window_days,
        watch_reason=DISPUTE_WINDOW_WATCH_REASON,
        block_reason=DISPUTE_WINDOW_BLOCK_REASON,
    )
    _append_maximum_reason(
        reason_codes,
        candidate.cash_lockup_days,
        pass_threshold=config.max_pass_cash_lockup_days,
        watch_threshold=config.max_watch_cash_lockup_days,
        watch_reason=CASH_LOCKUP_WATCH_REASON,
        block_reason=CASH_LOCKUP_BLOCK_REASON,
    )
    if not candidate.official_result_available:
        reason_codes.append(OFFICIAL_RESULT_UNAVAILABLE_BLOCK_REASON)
    if candidate.event_clock_confidence is None:
        reason_codes.append(EVENT_CLOCK_CONFIDENCE_MISSING_REASON)
    elif candidate.event_clock_confidence < config.min_watch_event_clock_confidence:
        reason_codes.append(EVENT_CLOCK_CONFIDENCE_BLOCK_REASON)
    elif candidate.event_clock_confidence < config.min_pass_event_clock_confidence:
        reason_codes.append(EVENT_CLOCK_CONFIDENCE_WATCH_REASON)
    return _normalize_reason_codes(tuple(reason_codes), allow_empty=True)


def _append_maximum_reason(
    reason_codes: list[str],
    value: Decimal,
    *,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
    watch_reason: str,
    block_reason: str,
) -> None:
    if value > watch_threshold:
        reason_codes.append(block_reason)
    elif value > pass_threshold:
        reason_codes.append(watch_reason)


def _reason_codes_with_score(
    reason_codes: tuple[str, ...],
    *,
    timing_score: Decimal,
    config: CandidateDecisionResolutionTimingScoreConfig,
) -> tuple[str, ...]:
    codes = list(reason_codes)
    if (
        not _hard_blocker_codes(reason_codes)
        and timing_score < config.min_watch_timing_score
    ):
        codes.append(TIMING_SCORE_BLOCK_REASON)
    elif not codes and timing_score < config.min_pass_timing_score:
        codes.append(TIMING_SCORE_WATCH_REASON)
    if not codes:
        codes.append(PASS_REASON)
    return _normalize_reason_codes(
        tuple(reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in codes),
    )


def _timing_score(
    candidate: CandidateDecisionResolutionTimingScoreInput,
    config: CandidateDecisionResolutionTimingScoreConfig,
) -> Decimal:
    score = BASE_CLEAR_TIMING_SCORE
    score -= _maximum_watch_penalty(
        candidate.time_to_close_days,
        pass_threshold=config.max_pass_time_to_close_days,
        watch_threshold=config.max_watch_time_to_close_days,
        max_penalty=TIME_TO_CLOSE_WATCH_PENALTY,
    )
    score -= _maximum_watch_penalty(
        candidate.expected_resolution_lag_days,
        pass_threshold=config.max_pass_expected_resolution_lag_days,
        watch_threshold=config.max_watch_expected_resolution_lag_days,
        max_penalty=EXPECTED_RESOLUTION_LAG_WATCH_PENALTY,
    )
    score -= _maximum_watch_penalty(
        candidate.dispute_window_days,
        pass_threshold=config.max_pass_dispute_window_days,
        watch_threshold=config.max_watch_dispute_window_days,
        max_penalty=DISPUTE_WINDOW_WATCH_PENALTY,
    )
    score -= _maximum_watch_penalty(
        candidate.cash_lockup_days,
        pass_threshold=config.max_pass_cash_lockup_days,
        watch_threshold=config.max_watch_cash_lockup_days,
        max_penalty=CASH_LOCKUP_WATCH_PENALTY,
    )
    if candidate.event_clock_confidence is not None:
        score -= _minimum_watch_penalty(
            candidate.event_clock_confidence,
            pass_threshold=config.min_pass_event_clock_confidence,
            watch_threshold=config.min_watch_event_clock_confidence,
            max_penalty=EVENT_CLOCK_CONFIDENCE_WATCH_PENALTY,
        )
    return _normalize_unit_decimal("timing_score", min(max(score, ZERO), ONE))


def _maximum_watch_penalty(
    value: Decimal,
    *,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
    max_penalty: Decimal,
) -> Decimal:
    if value <= pass_threshold:
        return ZERO
    if watch_threshold == pass_threshold:
        return max_penalty
    return _normalize_nonnegative_decimal(
        "watch_penalty",
        max_penalty * _ratio(value - pass_threshold, watch_threshold - pass_threshold),
    )


def _minimum_watch_penalty(
    value: Decimal,
    *,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
    max_penalty: Decimal,
) -> Decimal:
    if value >= pass_threshold:
        return ZERO
    if pass_threshold == watch_threshold:
        return max_penalty
    return _normalize_nonnegative_decimal(
        "watch_penalty",
        max_penalty * _ratio(pass_threshold - value, pass_threshold - watch_threshold),
    )


def _hard_blocker_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(code for code in reason_codes if code in BLOCK_REASON_CODES)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[CandidateDecisionResolutionTimingScoreRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_CANDIDATES_REASON,)
    reason_codes = tuple(
        reason_code
        for reason_code in REASON_CODE_SEQUENCE
        if any(reason_code in row.reason_codes for row in rows)
    )
    if reason_codes != (PASS_REASON,):
        return tuple(reason for reason in reason_codes if reason != PASS_REASON)
    return reason_codes


def _reason_code_counts(
    rows: tuple[CandidateDecisionResolutionTimingScoreRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[CandidateDecisionResolutionTimingReasonCodeCount, ...]:
    candidate_count = _count(len(rows))
    if not rows:
        return (
            CandidateDecisionResolutionTimingReasonCodeCount(
                reason_code=NO_CANDIDATES_REASON,
                count=ZERO,
                candidate_ratio=ZERO,
            ),
        )
    return tuple(
        CandidateDecisionResolutionTimingReasonCodeCount(
            reason_code=reason_code,
            count=count,
            candidate_ratio=_ratio(count, candidate_count),
        )
        for reason_code in reason_codes
        for count in (_count(sum(reason_code in row.reason_codes for row in rows)),)
        if count > ZERO
    )


def _status_count(
    rows: tuple[CandidateDecisionResolutionTimingScoreRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(row.timing_status == status for row in rows))


def _max_timing_score(
    rows: tuple[CandidateDecisionResolutionTimingScoreRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.timing_score for row in rows)


def _min_timing_score(
    rows: tuple[CandidateDecisionResolutionTimingScoreRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return min(row.timing_score for row in rows)


def _normalize_candidates(
    candidates: Iterable[CandidateDecisionResolutionTimingScoreInput],
) -> tuple[CandidateDecisionResolutionTimingScoreInput, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable of timing score inputs")
    try:
        normalized = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable of timing score inputs") from exc
    seen_refs: set[str] = set()
    for candidate in normalized:
        if type(candidate) is not CandidateDecisionResolutionTimingScoreInput:
            raise ValueError(
                "candidates must contain "
                "CandidateDecisionResolutionTimingScoreInput values",
            )
        require_paper_only_flags("CandidateDecisionResolutionTimingScoreInput", candidate)
        reject_unsafe_surface_fields("resolution timing score input", candidate)
        _reject_unsafe_public_values("resolution timing score input", candidate)
        if candidate.redacted_candidate_ref in seen_refs:
            raise ValueError("duplicate redacted_candidate_ref")
        seen_refs.add(candidate.redacted_candidate_ref)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[CandidateDecisionResolutionTimingScoreRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    seen_refs: set[str] = set()
    for row in normalized:
        if type(row) is not CandidateDecisionResolutionTimingScoreRow:
            raise ValueError("rows must contain CandidateDecisionResolutionTimingScoreRow values")
        require_paper_only_flags("CandidateDecisionResolutionTimingScoreRow", row)
        reject_unsafe_surface_fields("resolution timing score row", row)
        _reject_unsafe_public_values("resolution timing score row", row)
        if row.redacted_candidate_ref in seen_refs:
            raise ValueError("duplicate redacted_candidate_ref")
        seen_refs.add(row.redacted_candidate_ref)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    return normalized


def _normalize_reason_code_counts(
    values: object,
) -> tuple[CandidateDecisionResolutionTimingReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized = tuple(values)
    seen_codes: set[str] = set()
    for value in normalized:
        if type(value) is not CandidateDecisionResolutionTimingReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "CandidateDecisionResolutionTimingReasonCodeCount values",
            )
        require_paper_only_flags("CandidateDecisionResolutionTimingReasonCodeCount", value)
        reject_unsafe_surface_fields("resolution timing reason count", value)
        _reject_unsafe_public_values("resolution timing reason count", value)
        if value.reason_code in seen_codes:
            raise ValueError("reason_code_counts must contain unique reason codes")
        seen_codes.add(value.reason_code)
    expected = tuple(
        reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in seen_codes
    )
    if tuple(value.reason_code for value in normalized) != expected:
        raise ValueError("reason_code_counts must use deterministic reason order")
    return normalized


def _row_sort_key(row: CandidateDecisionResolutionTimingScoreRow) -> tuple[object, ...]:
    return (
        _status_rank(row.timing_status),
        row.timing_score,
        _first_reason_rank(row.reason_codes),
        row.redacted_candidate_ref,
    )


def _status_rank(status: str) -> Decimal:
    if status == "block":
        return Decimal("0")
    if status == "watch":
        return Decimal("1")
    if status == "pass":
        return Decimal("2")
    raise ValueError("timing_status must be supported")


def _first_reason_rank(reason_codes: tuple[str, ...]) -> Decimal:
    return Decimal(REASON_CODE_SEQUENCE.index(reason_codes[0]))


def _validate_config(config: CandidateDecisionResolutionTimingScoreConfig) -> None:
    if config.min_pass_timing_score < config.min_watch_timing_score:
        raise ValueError("min_pass_timing_score must be at least min_watch_timing_score")
    _require_maximum_thresholds(
        "time_to_close_days",
        config.max_pass_time_to_close_days,
        config.max_watch_time_to_close_days,
    )
    _require_maximum_thresholds(
        "expected_resolution_lag_days",
        config.max_pass_expected_resolution_lag_days,
        config.max_watch_expected_resolution_lag_days,
    )
    _require_maximum_thresholds(
        "dispute_window_days",
        config.max_pass_dispute_window_days,
        config.max_watch_dispute_window_days,
    )
    _require_maximum_thresholds(
        "cash_lockup_days",
        config.max_pass_cash_lockup_days,
        config.max_watch_cash_lockup_days,
    )
    if config.min_pass_event_clock_confidence < config.min_watch_event_clock_confidence:
        raise ValueError(
            "min_pass_event_clock_confidence must be at least "
            "min_watch_event_clock_confidence",
        )


def _require_maximum_thresholds(
    field_name: str,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> None:
    if pass_threshold > watch_threshold:
        raise ValueError(f"max_pass_{field_name} must not exceed max_watch_{field_name}")


def _validate_row(row: CandidateDecisionResolutionTimingScoreRow) -> None:
    if row.hard_blocker_codes != _hard_blocker_codes(row.reason_codes):
        raise ValueError("hard_blocker_codes must match reason_codes")
    if row.timing_status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("timing_status must match reason_codes")
    if row.timing_status == "pass" and row.reason_codes != (PASS_REASON,):
        raise ValueError("pass rows must use only pass reason")
    if row.timing_status != "pass" and PASS_REASON in row.reason_codes:
        raise ValueError("non-pass rows must not include pass reason")
    if row.timing_status == "block" and not row.hard_blocker_codes:
        raise ValueError("block rows must include hard_blocker_codes")
    if row.timing_status == "block" and row.timing_score != ZERO:
        raise ValueError("block rows must have zero timing_score")


def _validate_report(report: CandidateDecisionResolutionTimingScoreReport) -> None:
    rows = report.rows
    if report.candidate_count != _count(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(rows, "block"):
        raise ValueError("blocked_count must match rows")
    if report.max_timing_score != _max_timing_score(rows):
        raise ValueError("max_timing_score must match rows")
    if report.min_timing_score != _min_timing_score(rows):
        raise ValueError("min_timing_score must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.timing_status != _status_from_reason_codes(report.reason_codes):
        raise ValueError("timing_status must match reason_codes")
    if tuple(row.reason_code for row in report.reason_code_counts) != report.reason_codes:
        raise ValueError("reason_code_counts must match reason_codes")
    expected_counts = _reason_code_counts(rows, report.reason_codes)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")


def _row_values_without_digest(
    row: CandidateDecisionResolutionTimingScoreRow,
) -> dict[str, object]:
    values = asdict(row)
    values.pop("derived_validation_digest", None)
    return values


def _report_values_without_digest(
    report: CandidateDecisionResolutionTimingScoreReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _row_digest_from_values(values: Mapping[str, object]) -> str:
    return _digest_from_values(values)


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    return _digest_from_values(values)


def _digest_from_values(values: Mapping[str, object]) -> str:
    payload = json_ready_no_floats(values)
    reject_unsafe_surface_fields("resolution timing score digest payload", payload)
    _reject_unsafe_public_values("resolution timing score digest payload", payload)
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _normalize_public_reference_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    refs = tuple(_require_public_reference(field_name, item) for item in value)
    if len(set(refs)) != len(refs):
        raise ValueError(f"{field_name} must contain unique refs")
    return tuple(sorted(refs))


def _require_redacted_candidate_ref(value: object) -> str:
    _require_public_reference("redacted_candidate_ref", value)
    candidate_ref = str(value)
    if not _is_redacted_candidate_ref(candidate_ref):
        raise ValueError("redacted_candidate_ref must be a redacted candidate ref")
    return candidate_ref


def _is_redacted_candidate_ref(value: str) -> bool:
    prefix = "candidate_ref_"
    if not value.startswith(prefix):
        return False
    digest = value[len(prefix):]
    return len(digest) == 64 and all(char in "0123456789abcdef" for char in digest)


def _require_public_reference(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    lowered = str(value).lower()
    if any(term in lowered for term in SOURCE_REFERENCE_VALUE_TERMS):
        raise ValueError(f"{field_name} must not expose source refs/URLs")
    if "?" in lowered or any(term in lowered for term in RAW_MARKET_SURFACE_TERMS):
        raise ValueError(f"{field_name} must not expose raw market ids/questions")
    return str(value)


def _normalize_reason_codes(
    value: object,
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes and not allow_empty:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_reason_code(reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must contain unique reason codes")
        seen.add(reason_code)
    expected = tuple(reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in seen)
    if reason_codes != expected:
        raise ValueError("reason_codes must use deterministic sequence")
    if PASS_REASON in seen and len(seen) != 1:
        raise ValueError("pass reason_code must be exclusive")
    if NO_CANDIDATES_REASON in seen and len(seen) != 1:
        raise ValueError("no candidate reason_code must be exclusive")
    return reason_codes


def _normalize_optional_unit_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_unit_decimal(field_name, value)


def _normalize_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be no greater than 1")
    return normalized


def _normalize_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM)


def _count(value: int | Decimal) -> Decimal:
    if type(value) is Decimal:
        return _normalize_nonnegative_whole_decimal("count", value)
    return _normalize_nonnegative_whole_decimal("count", Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_unit_decimal("ratio", numerator / denominator)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")


def _require_reason_code(value: object) -> str:
    _require_canonical_string("reason_code", value)
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError("reason_code must be supported")
    return str(value)


def _require_validation_digest(value: object) -> None:
    if type(value) is not str:
        raise ValueError("derived_validation_digest must be a string")
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError("derived_validation_digest must be a lowercase sha256 digest")


def _reject_unsafe_public_values(label: str, value: object) -> None:
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_unsafe_public_values(label, item)
        return
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        _reject_unsafe_public_values(label, asdict(value))
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_values(label, item)
        return
    if type(value) is str:
        lowered = value.lower()
        if any(term in lowered for term in SOURCE_REFERENCE_VALUE_TERMS):
            raise ValueError(f"source refs/URLs value in {label}")
        if any(term in lowered for term in RAW_CANDIDATE_SURFACE_TERMS):
            raise ValueError(f"raw candidate ids value in {label}")
        if "?" in lowered or any(term in lowered for term in RAW_MARKET_SURFACE_TERMS):
            raise ValueError(f"raw market ids/questions value in {label}")
        if any(term in lowered for term in UNSAFE_PUBLIC_VALUE_TERMS):
            raise ValueError(f"unsafe live surface value in {label}")


def _reject_unsafe_public_payload_keys(label: str, value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            lowered = key.lower()
            if lowered == "redacted_candidate_ref":
                _require_redacted_candidate_ref(item)
            if any(
                term in lowered
                for term in RAW_CANDIDATE_PUBLIC_PAYLOAD_KEY_TERMS
            ):
                raise ValueError(f"raw candidate id field in {label}: {key}")
            if any(term in lowered for term in UNSAFE_PUBLIC_PAYLOAD_KEY_TERMS):
                raise ValueError(f"unsafe public source refs field in {label}: {key}")
            _reject_unsafe_public_payload_keys(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload_keys(label, item)


def _reject_unsupported_public_status_values(label: str, value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if "status" in key.lower() and item not in TIMING_STATUSES:
                raise ValueError(
                    f"{key} must use pass/watch/block public status in {label}",
                )
            _reject_unsupported_public_status_values(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsupported_public_status_values(label, item)


def _reject_public_numeric_values(label: str, value: object) -> None:
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_public_numeric_values(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_public_numeric_values(label, item)
        return
    if type(value) in (Decimal, float, int):
        raise ValueError(f"public payload numeric values must be decimal strings in {label}")


def _reject_strict_public_payload_values(label: str, value: object) -> None:
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_strict_public_payload_values(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_strict_public_payload_values(label, item)
        return
    if type(value) is str:
        lowered = value.lower()
        if "candidate_ref_" in lowered and not _is_redacted_candidate_ref(value):
            raise ValueError(f"raw candidate ids value in {label}")
        if any(term in lowered for term in STRICT_PUBLIC_SOURCE_VALUE_TERMS):
            raise ValueError(f"source refs/URLs value in {label}")
        if any(term in lowered for term in URLISH_PUBLIC_VALUE_TERMS):
            raise ValueError(f"source refs/URLs value in {label}")


__all__ = (
    "DEFAULT_CANDIDATE_DECISION_RESOLUTION_TIMING_SCORE_CONFIG_VERSION",
    "BOUNDARY_STATEMENT",
    "CandidateDecisionResolutionTimingScoreConfig",
    "CandidateDecisionResolutionTimingScoreInput",
    "CandidateDecisionResolutionTimingScoreRow",
    "CandidateDecisionResolutionTimingReasonCodeCount",
    "CandidateDecisionResolutionTimingScoreReport",
    "build_candidate_decision_resolution_timing_score_report",
    "candidate_decision_resolution_timing_score_payload",
    "validate_candidate_decision_resolution_timing_score_public_payload",
)
