"""Pure report-only specificity digest for probability-event markets."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import UNSAFE_SURFACE_FIELD_FRAGMENTS


DEFAULT_PROBABILITY_EVENT_MARKET_SPECIFICITY_DIGEST_CONFIG_VERSION = (
    "probability-event-market-specificity-digest-v0"
)
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUSES = ("pass", "watch", "blocked")
STATUS_WEIGHT = {
    "blocked": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
REDACTED_REFERENCE_MARKERS = ("redacted", "masked", "anon", "synthetic", "sample")
SENSITIVE_REFERENCE_MARKERS = ("0x", "email", "credential", "secret", "token")
UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    fragment for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS if fragment != "sign"
)

PASS_REASON = "probability_event_market_specificity_passed"
NO_INPUTS_REASON = "probability_event_market_specificity_no_inputs_blocked"
QUESTION_VAGUE_WATCH_REASON = (
    "probability_event_market_specificity_question_vague_watch"
)
QUESTION_UNSPECIFIC_BLOCKED_REASON = (
    "probability_event_market_specificity_question_unspecific_blocked"
)
RESOLUTION_SOURCE_MISSING_REASON = (
    "probability_event_market_specificity_resolution_source_missing_blocked"
)
OUTCOME_LABELS_MISSING_REASON = (
    "probability_event_market_specificity_outcome_labels_missing_blocked"
)
CLOSE_TIME_UNCLEAR_WATCH_REASON = (
    "probability_event_market_specificity_close_time_unclear_watch"
)
CLOSE_TIME_UNCLEAR_BLOCKED_REASON = (
    "probability_event_market_specificity_close_time_unclear_blocked"
)
RESOLUTION_TIME_UNCLEAR_WATCH_REASON = (
    "probability_event_market_specificity_resolution_time_unclear_watch"
)
RESOLUTION_TIME_UNCLEAR_BLOCKED_REASON = (
    "probability_event_market_specificity_resolution_time_unclear_blocked"
)
THRESHOLD_UNCLEAR_WATCH_REASON = (
    "probability_event_market_specificity_threshold_unclear_watch"
)
THRESHOLD_NOT_MEASURABLE_REASON = (
    "probability_event_market_specificity_threshold_not_measurable_blocked"
)
AMBIGUITY_FLAGGED_REASON = (
    "probability_event_market_specificity_ambiguity_flagged_blocked"
)
REVISION_RISK_WATCH_REASON = (
    "probability_event_market_specificity_revision_risk_watch"
)
REVISION_RISK_BLOCKED_REASON = (
    "probability_event_market_specificity_revision_risk_blocked"
)
DISPUTE_RISK_WATCH_REASON = (
    "probability_event_market_specificity_dispute_risk_watch"
)
DISPUTE_RISK_BLOCKED_REASON = (
    "probability_event_market_specificity_dispute_risk_blocked"
)
REASON_CODES = (
    PASS_REASON,
    NO_INPUTS_REASON,
    QUESTION_VAGUE_WATCH_REASON,
    QUESTION_UNSPECIFIC_BLOCKED_REASON,
    RESOLUTION_SOURCE_MISSING_REASON,
    OUTCOME_LABELS_MISSING_REASON,
    CLOSE_TIME_UNCLEAR_WATCH_REASON,
    CLOSE_TIME_UNCLEAR_BLOCKED_REASON,
    RESOLUTION_TIME_UNCLEAR_WATCH_REASON,
    RESOLUTION_TIME_UNCLEAR_BLOCKED_REASON,
    THRESHOLD_UNCLEAR_WATCH_REASON,
    THRESHOLD_NOT_MEASURABLE_REASON,
    AMBIGUITY_FLAGGED_REASON,
    REVISION_RISK_WATCH_REASON,
    REVISION_RISK_BLOCKED_REASON,
    DISPUTE_RISK_WATCH_REASON,
    DISPUTE_RISK_BLOCKED_REASON,
)
BLOCKED_REASONS = frozenset(
    reason_code for reason_code in REASON_CODES if reason_code.endswith("_blocked")
)
WATCH_REASONS = frozenset(
    reason_code for reason_code in REASON_CODES if reason_code.endswith("_watch")
)
RISK_REASONS = frozenset(
    (
        REVISION_RISK_WATCH_REASON,
        REVISION_RISK_BLOCKED_REASON,
        DISPUTE_RISK_WATCH_REASON,
        DISPUTE_RISK_BLOCKED_REASON,
    ),
)

__all__ = (
    "DEFAULT_PROBABILITY_EVENT_MARKET_SPECIFICITY_DIGEST_CONFIG_VERSION",
    "ProbabilityEventMarketSpecificityDigestConfig",
    "ProbabilityEventMarketSpecificityDigestFacts",
    "ProbabilityEventMarketSpecificityDigestReasonCodeCount",
    "ProbabilityEventMarketSpecificityDigestReport",
    "ProbabilityEventMarketSpecificityDigestRow",
    "build_probability_event_market_specificity_digest",
    "probability_event_market_specificity_digest_payload",
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
class ProbabilityEventMarketSpecificityDigestConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_PROBABILITY_EVENT_MARKET_SPECIFICITY_DIGEST_CONFIG_VERSION
    )
    question_specificity_pass_score: Decimal = Decimal("0.800000")
    question_specificity_block_score: Decimal = Decimal("0.500000")
    time_clarity_pass_score: Decimal = Decimal("0.800000")
    time_clarity_block_score: Decimal = Decimal("0.500000")
    measurable_threshold_pass_score: Decimal = Decimal("0.800000")
    measurable_threshold_block_score: Decimal = Decimal("0.500000")
    revision_risk_watch_score: Decimal = Decimal("0.500000")
    revision_risk_block_score: Decimal = Decimal("0.800000")
    dispute_risk_watch_score: Decimal = Decimal("0.500000")
    dispute_risk_block_score: Decimal = Decimal("0.800000")
    min_exact_outcome_label_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventMarketSpecificityDigestConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "question_specificity_pass_score",
            "question_specificity_block_score",
            "time_clarity_pass_score",
            "time_clarity_block_score",
            "measurable_threshold_pass_score",
            "measurable_threshold_block_score",
            "revision_risk_watch_score",
            "revision_risk_block_score",
            "dispute_risk_watch_score",
            "dispute_risk_block_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_exact_outcome_label_count",
            _normalize_positive_count(
                "min_exact_outcome_label_count",
                self.min_exact_outcome_label_count,
            ),
        )
        _require_at_most(
            "question_specificity_block_score",
            self.question_specificity_block_score,
            self.question_specificity_pass_score,
        )
        _require_at_most(
            "time_clarity_block_score",
            self.time_clarity_block_score,
            self.time_clarity_pass_score,
        )
        _require_at_most(
            "measurable_threshold_block_score",
            self.measurable_threshold_block_score,
            self.measurable_threshold_pass_score,
        )
        _require_at_most(
            "revision_risk_watch_score",
            self.revision_risk_watch_score,
            self.revision_risk_block_score,
        )
        _require_at_most(
            "dispute_risk_watch_score",
            self.dispute_risk_watch_score,
            self.dispute_risk_block_score,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ProbabilityEventMarketSpecificityDigestFacts(_FinalPublicDataclass):
    redacted_public_reference: str
    question_specificity_score: Decimal
    resolution_source_reference: str | None
    outcome_labels: tuple[str, ...]
    close_time_clarity_score: Decimal
    resolution_time_clarity_score: Decimal
    measurable_threshold_score: Decimal
    ambiguity_flags: tuple[str, ...]
    revision_risk_score: Decimal
    dispute_risk_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventMarketSpecificityDigestFacts,
            "facts",
        )
        _require_public_reference(
            "redacted_public_reference",
            self.redacted_public_reference,
        )
        object.__setattr__(
            self,
            "resolution_source_reference",
            _normalize_optional_public_reference(
                "resolution_source_reference",
                self.resolution_source_reference,
            ),
        )
        object.__setattr__(
            self,
            "outcome_labels",
            _normalize_public_string_tuple(
                "outcome_labels",
                self.outcome_labels,
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "ambiguity_flags",
            _normalize_public_string_tuple(
                "ambiguity_flags",
                self.ambiguity_flags,
                allow_empty=True,
            ),
        )
        for field_name in (
            "question_specificity_score",
            "close_time_clarity_score",
            "resolution_time_clarity_score",
            "measurable_threshold_score",
            "revision_risk_score",
            "dispute_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("facts", self)


@dataclass(frozen=True)
class ProbabilityEventMarketSpecificityDigestRow(_FinalPublicDataclass):
    redacted_public_reference: str
    status: str
    question_specificity_score: Decimal
    resolution_source_reference: str | None
    outcome_labels: tuple[str, ...]
    outcome_label_count: Decimal
    close_time_clarity_score: Decimal
    resolution_time_clarity_score: Decimal
    measurable_threshold_score: Decimal
    ambiguity_flags: tuple[str, ...]
    ambiguity_flag_count: Decimal
    revision_risk_score: Decimal
    dispute_risk_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventMarketSpecificityDigestRow,
            "row",
        )
        _require_public_reference(
            "redacted_public_reference",
            self.redacted_public_reference,
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "resolution_source_reference",
            _normalize_optional_public_reference(
                "resolution_source_reference",
                self.resolution_source_reference,
            ),
        )
        object.__setattr__(
            self,
            "outcome_labels",
            _normalize_public_string_tuple(
                "outcome_labels",
                self.outcome_labels,
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "ambiguity_flags",
            _normalize_public_string_tuple(
                "ambiguity_flags",
                self.ambiguity_flags,
                allow_empty=True,
            ),
        )
        for field_name in (
            "question_specificity_score",
            "close_time_clarity_score",
            "resolution_time_clarity_score",
            "measurable_threshold_score",
            "revision_risk_score",
            "dispute_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "outcome_label_count",
            _normalize_nonnegative_count(
                "outcome_label_count",
                self.outcome_label_count,
            ),
        )
        object.__setattr__(
            self,
            "ambiguity_flag_count",
            _normalize_nonnegative_count(
                "ambiguity_flag_count",
                self.ambiguity_flag_count,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ProbabilityEventMarketSpecificityDigestReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventMarketSpecificityDigestReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_count("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ProbabilityEventMarketSpecificityDigestReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    market_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    missing_outcome_label_count: Decimal
    missing_resolution_source_count: Decimal
    ambiguity_flag_count: Decimal
    revision_or_dispute_risk_count: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ProbabilityEventMarketSpecificityDigestReasonCodeCount, ...]
    market_rows: tuple[ProbabilityEventMarketSpecificityDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventMarketSpecificityDigestReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "market_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "missing_outcome_label_count",
            "missing_resolution_source_count",
            "ambiguity_flag_count",
            "revision_or_dispute_risk_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "market_rows", _normalize_rows(self.market_rows))
        _validate_report(self)
        _require_hard_flags("report", self)


_PUBLIC_DATACLASS_TYPES = (
    ProbabilityEventMarketSpecificityDigestConfig,
    ProbabilityEventMarketSpecificityDigestFacts,
    ProbabilityEventMarketSpecificityDigestReasonCodeCount,
    ProbabilityEventMarketSpecificityDigestReport,
    ProbabilityEventMarketSpecificityDigestRow,
)


def build_probability_event_market_specificity_digest(
    observations: Iterable[ProbabilityEventMarketSpecificityDigestFacts],
    *,
    config: ProbabilityEventMarketSpecificityDigestConfig,
    generated_at: datetime,
) -> ProbabilityEventMarketSpecificityDigestReport:
    if type(config) is not ProbabilityEventMarketSpecificityDigestConfig:
        raise ValueError(
            "config must be a ProbabilityEventMarketSpecificityDigestConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    facts_rows = _normalize_facts(observations)
    market_rows = tuple(
        sorted(
            (
                _evaluate_facts(row, config=config)
                for row in facts_rows
            ),
            key=_row_sort_key,
        ),
    )
    return ProbabilityEventMarketSpecificityDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_rollup_status(tuple(row.status for row in market_rows)),
        market_count=_count(len(market_rows)),
        pass_count=_status_count(market_rows, "pass"),
        watch_count=_status_count(market_rows, "watch"),
        blocked_count=_status_count(market_rows, "blocked"),
        missing_outcome_label_count=_count_reason_rows(
            market_rows,
            OUTCOME_LABELS_MISSING_REASON,
        ),
        missing_resolution_source_count=_count_reason_rows(
            market_rows,
            RESOLUTION_SOURCE_MISSING_REASON,
        ),
        ambiguity_flag_count=_count_reason_rows(
            market_rows,
            AMBIGUITY_FLAGGED_REASON,
        ),
        revision_or_dispute_risk_count=_count_rows_with_any_reason(
            market_rows,
            RISK_REASONS,
        ),
        reason_codes=_rollup_reason_codes(market_rows),
        reason_code_counts=_reason_code_counts(market_rows),
        market_rows=market_rows,
    )


def probability_event_market_specificity_digest_payload(
    report: ProbabilityEventMarketSpecificityDigestReport,
) -> dict[str, Any]:
    if type(report) is not ProbabilityEventMarketSpecificityDigestReport:
        raise ValueError(
            "report must be a ProbabilityEventMarketSpecificityDigestReport",
        )
    _require_payload_safe_value("report", report)
    _reject_unsafe_public_payload("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _evaluate_facts(
    row: ProbabilityEventMarketSpecificityDigestFacts,
    *,
    config: ProbabilityEventMarketSpecificityDigestConfig,
) -> ProbabilityEventMarketSpecificityDigestRow:
    reason_codes: list[str] = []
    if row.question_specificity_score < config.question_specificity_block_score:
        reason_codes.append(QUESTION_UNSPECIFIC_BLOCKED_REASON)
    elif row.question_specificity_score < config.question_specificity_pass_score:
        reason_codes.append(QUESTION_VAGUE_WATCH_REASON)
    if row.resolution_source_reference is None:
        reason_codes.append(RESOLUTION_SOURCE_MISSING_REASON)
    outcome_label_count = _count(len(row.outcome_labels))
    if outcome_label_count < config.min_exact_outcome_label_count:
        reason_codes.append(OUTCOME_LABELS_MISSING_REASON)
    if row.close_time_clarity_score < config.time_clarity_block_score:
        reason_codes.append(CLOSE_TIME_UNCLEAR_BLOCKED_REASON)
    elif row.close_time_clarity_score < config.time_clarity_pass_score:
        reason_codes.append(CLOSE_TIME_UNCLEAR_WATCH_REASON)
    if row.resolution_time_clarity_score < config.time_clarity_block_score:
        reason_codes.append(RESOLUTION_TIME_UNCLEAR_BLOCKED_REASON)
    elif row.resolution_time_clarity_score < config.time_clarity_pass_score:
        reason_codes.append(RESOLUTION_TIME_UNCLEAR_WATCH_REASON)
    if row.measurable_threshold_score < config.measurable_threshold_block_score:
        reason_codes.append(THRESHOLD_NOT_MEASURABLE_REASON)
    elif row.measurable_threshold_score < config.measurable_threshold_pass_score:
        reason_codes.append(THRESHOLD_UNCLEAR_WATCH_REASON)
    if row.ambiguity_flags:
        reason_codes.append(AMBIGUITY_FLAGGED_REASON)
    if row.revision_risk_score >= config.revision_risk_block_score:
        reason_codes.append(REVISION_RISK_BLOCKED_REASON)
    elif row.revision_risk_score >= config.revision_risk_watch_score:
        reason_codes.append(REVISION_RISK_WATCH_REASON)
    if row.dispute_risk_score >= config.dispute_risk_block_score:
        reason_codes.append(DISPUTE_RISK_BLOCKED_REASON)
    elif row.dispute_risk_score >= config.dispute_risk_watch_score:
        reason_codes.append(DISPUTE_RISK_WATCH_REASON)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    normalized_reason_codes = tuple(sorted(reason_codes))
    return ProbabilityEventMarketSpecificityDigestRow(
        redacted_public_reference=row.redacted_public_reference,
        status=_row_status(normalized_reason_codes),
        question_specificity_score=row.question_specificity_score,
        resolution_source_reference=row.resolution_source_reference,
        outcome_labels=row.outcome_labels,
        outcome_label_count=outcome_label_count,
        close_time_clarity_score=row.close_time_clarity_score,
        resolution_time_clarity_score=row.resolution_time_clarity_score,
        measurable_threshold_score=row.measurable_threshold_score,
        ambiguity_flags=row.ambiguity_flags,
        ambiguity_flag_count=_count(len(row.ambiguity_flags)),
        revision_risk_score=row.revision_risk_score,
        dispute_risk_score=row.dispute_risk_score,
        reason_codes=normalized_reason_codes,
    )


def _normalize_facts(
    observations: Iterable[ProbabilityEventMarketSpecificityDigestFacts],
) -> tuple[ProbabilityEventMarketSpecificityDigestFacts, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        values = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    seen_references: set[str] = set()
    for row in values:
        if type(row) is not ProbabilityEventMarketSpecificityDigestFacts:
            raise ValueError(
                "observations must contain ProbabilityEventMarketSpecificityDigestFacts",
            )
        _require_hard_flags("facts", row)
        if row.redacted_public_reference in seen_references:
            raise ValueError("observations must not contain duplicate references")
        seen_references.add(row.redacted_public_reference)
    return values


def _normalize_rows(
    rows: Iterable[ProbabilityEventMarketSpecificityDigestRow],
) -> tuple[ProbabilityEventMarketSpecificityDigestRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("market_rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("market_rows must be an iterable") from exc
    seen_references: set[str] = set()
    for row in values:
        if type(row) is not ProbabilityEventMarketSpecificityDigestRow:
            raise ValueError(
                "market_rows must contain ProbabilityEventMarketSpecificityDigestRow",
            )
        _require_hard_flags("row", row)
        if row.redacted_public_reference in seen_references:
            raise ValueError("market_rows must not contain duplicate references")
        seen_references.add(row.redacted_public_reference)
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("market_rows must use canonical sequence")
    return values


def _normalize_reason_code_counts(
    rows: Iterable[ProbabilityEventMarketSpecificityDigestReasonCodeCount],
) -> tuple[ProbabilityEventMarketSpecificityDigestReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen_reason_codes: set[str] = set()
    for row in values:
        if type(row) is not ProbabilityEventMarketSpecificityDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ProbabilityEventMarketSpecificityDigestReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", row)
        if row.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts must not contain duplicate reason_codes")
        seen_reason_codes.add(row.reason_code)
    if values != tuple(sorted(values, key=lambda item: (-item.count, item.reason_code))):
        raise ValueError("reason_code_counts must be sorted by count then reason_code")
    return values


def _normalize_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        values = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not values:
        raise ValueError("reason_codes must not be empty")
    for reason_code in values:
        _require_reason_code("reason_codes", reason_code)
    if len(set(values)) != len(values):
        raise ValueError("reason_codes must not contain duplicate values")
    if values != tuple(sorted(values)):
        raise ValueError("reason_codes must use canonical sequence")
    return values


def _normalize_report_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    return _normalize_reason_codes(reason_codes)


def _normalize_optional_public_reference(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    _require_public_reference(field_name, value)
    return value


def _normalize_public_string_tuple(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or type(values) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    normalized = tuple(values)
    if not normalized and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    seen_values: set[str] = set()
    for value in normalized:
        _require_canonical_string(field_name, value)
        if value in seen_values:
            raise ValueError(f"{field_name} must not contain duplicate values")
        seen_values.add(value)
    if normalized != tuple(sorted(normalized)):
        raise ValueError(f"{field_name} must use canonical sequence")
    return normalized


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if not statuses:
        return "blocked"
    if any(status == "blocked" for status in statuses):
        return "blocked"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _rollup_reason_codes(
    rows: tuple[ProbabilityEventMarketSpecificityDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    reason_codes = sorted(
        {
            reason_code
            for row in rows
            for reason_code in row.reason_codes
        },
    )
    if len(reason_codes) > 1 and PASS_REASON in reason_codes:
        reason_codes.remove(PASS_REASON)
    return tuple(reason_codes)


def _reason_code_counts(
    rows: tuple[ProbabilityEventMarketSpecificityDigestRow, ...],
) -> tuple[ProbabilityEventMarketSpecificityDigestReasonCodeCount, ...]:
    if not rows:
        return (
            ProbabilityEventMarketSpecificityDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=COUNT_QUANTUM,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ProbabilityEventMarketSpecificityDigestReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKED_REASONS for reason_code in reason_codes):
        return "blocked"
    if any(reason_code in WATCH_REASONS for reason_code in reason_codes):
        return "watch"
    if reason_codes == (PASS_REASON,):
        return "pass"
    raise ValueError("reason_codes must resolve to a known status")


def _row_sort_key(
    row: ProbabilityEventMarketSpecificityDigestRow,
) -> tuple[Decimal, Decimal, str]:
    return (
        -STATUS_WEIGHT[row.status],
        -_readiness_gap_count(row),
        row.redacted_public_reference,
    )


def _readiness_gap_count(row: ProbabilityEventMarketSpecificityDigestRow) -> Decimal:
    return _count(sum(1 for reason_code in row.reason_codes if reason_code != PASS_REASON))


def _status_count(
    rows: tuple[ProbabilityEventMarketSpecificityDigestRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _count_reason_rows(
    rows: tuple[ProbabilityEventMarketSpecificityDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _count_rows_with_any_reason(
    rows: tuple[ProbabilityEventMarketSpecificityDigestRow, ...],
    reason_codes: frozenset[str],
) -> Decimal:
    return _count(
        sum(1 for row in rows if any(reason_code in reason_codes for reason_code in row.reason_codes)),
    )


def _validate_row(row: ProbabilityEventMarketSpecificityDigestRow) -> None:
    if row.outcome_label_count != _count(len(row.outcome_labels)):
        raise ValueError("outcome_label_count must match outcome_labels")
    if row.ambiguity_flag_count != _count(len(row.ambiguity_flags)):
        raise ValueError("ambiguity_flag_count must match ambiguity_flags")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report(report: ProbabilityEventMarketSpecificityDigestReport) -> None:
    rows = report.market_rows
    if report.market_count != _count(len(rows)):
        raise ValueError("market_count must match market_rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match market_rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match market_rows")
    if report.blocked_count != _status_count(rows, "blocked"):
        raise ValueError("blocked_count must match market_rows")
    if report.missing_outcome_label_count != _count_reason_rows(
        rows,
        OUTCOME_LABELS_MISSING_REASON,
    ):
        raise ValueError("missing_outcome_label_count must match market_rows")
    if report.missing_resolution_source_count != _count_reason_rows(
        rows,
        RESOLUTION_SOURCE_MISSING_REASON,
    ):
        raise ValueError("missing_resolution_source_count must match market_rows")
    if report.ambiguity_flag_count != _count_reason_rows(rows, AMBIGUITY_FLAGGED_REASON):
        raise ValueError("ambiguity_flag_count must match market_rows")
    if report.revision_or_dispute_risk_count != _count_rows_with_any_reason(
        rows,
        RISK_REASONS,
    ):
        raise ValueError("revision_or_dispute_risk_count must match market_rows")
    if report.status != _rollup_status(tuple(row.status for row in rows)):
        raise ValueError("status must match market_rows")
    if report.reason_codes != _rollup_reason_codes(rows):
        raise ValueError("reason_codes must match market_rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match market_rows")


def _json_ready(value: Any) -> Any:
    if type(value) is Decimal:
        _require_six_decimal_decimal("JSON Decimal value", value)
        return format(value, "f")
    if type(value) is datetime:
        _require_utc_datetime("JSON datetime value", value)
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        _require_payload_safe_value("JSON value", value)
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if value is None:
        return None
    if type(value) is bool:
        return value
    if type(value) is str:
        _require_canonical_string("JSON string value", value)
        return value
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, (list, dict, set)):
        raise ValueError("JSON value must come from public dataclass fields")
    raise ValueError("value is not JSON serializable")


def _require_payload_safe_value(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{label} contains unsupported dataclass")
        for field in fields(value):
            _require_payload_safe_value(f"{label}.{field.name}", getattr(value, field.name))
        _rebuild_public_dataclass(label, value)
        return
    if type(value) is Decimal:
        _require_six_decimal_decimal(label, value)
        return
    if type(value) is datetime:
        _require_utc_datetime(label, value)
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _require_payload_safe_value(f"{label}[{index}]", item)
        return
    if value is None or type(value) in (bool, str):
        if type(value) is str:
            _require_canonical_string(label, value)
        return
    if isinstance(value, float):
        raise ValueError(f"{label} must not be a float")
    if type(value) is int:
        raise ValueError(f"{label} must use Decimal values")
    if isinstance(value, (list, dict, set)):
        raise ValueError(f"{label} must come from public dataclass fields")
    raise ValueError(f"{label} contains unsupported value")


def _rebuild_public_dataclass(label: str, value: object) -> None:
    kwargs = {field.name: getattr(value, field.name) for field in fields(value)}
    try:
        type(value)(**kwargs)
    except Exception as exc:
        raise ValueError(f"{label} failed payload revalidation") from exc


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{path or label} contains unsupported dataclass")
        for field in fields(value):
            item_path = field.name if not path else f"{path}.{field.name}"
            _reject_unsafe_public_payload(label, getattr(value, field.name), item_path)
        return
    if type(value) is str:
        if _has_unsafe_fragment(value):
            raise ValueError(f"{path or label} has unsafe value")
        return
    if type(value) is Decimal:
        _require_six_decimal_decimal(path or label, value)
        return
    if type(value) is datetime:
        _require_utc_datetime(path or label, value)
        return
    if value is None or type(value) is bool:
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_fragment(key):
                raise ValueError(f"unsafe field in {label}: {key}")
            item_path = key if not path else f"{path}.{key}"
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, float):
        raise ValueError(f"{path or label} must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal values")
    raise ValueError(f"{path or label} is not JSON serializable")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_utc_datetime(field_name: str, value: object) -> None:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is not UTC or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-number Decimal")
    return normalized.quantize(COUNT_QUANTUM)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_six_decimal_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must use six decimal places")


def _count(value: int) -> Decimal:
    if isinstance(value, bool) or type(value) is not int or value < 0:
        raise ValueError("count source must be a nonnegative integer")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_at_most(field_name: str, lower: Decimal, upper: Decimal) -> None:
    if lower > upper:
        raise ValueError(f"{field_name} must be less than or equal to paired threshold")


def _require_public_reference(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(marker in lowered for marker in SENSITIVE_REFERENCE_MARKERS):
        raise ValueError(f"{field_name} must be redacted")
    if not any(marker in lowered for marker in REDACTED_REFERENCE_MARKERS):
        raise ValueError(f"{field_name} must be redacted")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    if _has_unsafe_fragment(value):
        raise ValueError(f"{field_name} has unsafe value")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODES:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _has_unsafe_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)
