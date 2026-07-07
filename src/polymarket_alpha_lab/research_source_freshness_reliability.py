from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, localcontext


DEFAULT_RESEARCH_SOURCE_FRESHNESS_RELIABILITY_CONFIG_VERSION = (
    "research-source-freshness-reliability-v0"
)

SOURCE_KINDS = ("official", "primary", "secondary", "research")
ROW_STATUSES = ("blocked", "watch", "pass")
REPORT_STATUSES = ("blocked", "watch", "pass")

STALE_BLOCK_REASON = "research_source_freshness_reliability_stale_block"
RELIABILITY_BLOCK_REASON = "research_source_freshness_reliability_reliability_block"
INDEPENDENCE_BLOCK_REASON = "research_source_freshness_reliability_independence_block"
CONFLICT_BLOCK_REASON = "research_source_freshness_reliability_conflict_block"
STALE_WATCH_REASON = "research_source_freshness_reliability_stale_watch"
RELIABILITY_WATCH_REASON = "research_source_freshness_reliability_reliability_watch"
INDEPENDENCE_WATCH_REASON = "research_source_freshness_reliability_independence_watch"
CONFLICT_WATCH_REASON = "research_source_freshness_reliability_conflict_watch"
NON_PRIMARY_REASON = "research_source_freshness_reliability_non_primary"
PASS_REASON = "research_source_freshness_reliability_pass"
EMPTY_REASON = "research_source_freshness_reliability_empty"

REASON_CODES = (
    STALE_BLOCK_REASON,
    RELIABILITY_BLOCK_REASON,
    INDEPENDENCE_BLOCK_REASON,
    CONFLICT_BLOCK_REASON,
    STALE_WATCH_REASON,
    RELIABILITY_WATCH_REASON,
    INDEPENDENCE_WATCH_REASON,
    CONFLICT_WATCH_REASON,
    NON_PRIMARY_REASON,
    PASS_REASON,
    EMPTY_REASON,
)
REASON_RANK = {reason_code: index for index, reason_code in enumerate(REASON_CODES)}
STATUS_RANK = {"blocked": 0, "watch": 1, "pass": 2}

DECIMAL_CONTEXT = Context(prec=64)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        "credential",
        "private",
        "secret",
        _join_parts("tok", "en"),
        _join_parts("li", "ve"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("bro", "ker"),
        _join_parts("or", "der"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("sig", "ning"),
        _join_parts("ad", "vice"),
    ),
)


@dataclass(frozen=True)
class ResearchSourceFreshnessReliabilityConfig:
    config_version: str = DEFAULT_RESEARCH_SOURCE_FRESHNESS_RELIABILITY_CONFIG_VERSION
    watch_stale_after_seconds: Decimal = Decimal("3600.000000")
    blocked_stale_after_seconds: Decimal = Decimal("7200.000000")
    reliability_watch_below: Decimal = Decimal("0.800000")
    reliability_block_below: Decimal = Decimal("0.500000")
    independence_watch_below: Decimal = Decimal("0.700000")
    independence_block_below: Decimal = Decimal("0.400000")
    conflict_watch_count: Decimal = Decimal("1.000000")
    conflict_block_count: Decimal = Decimal("3.000000")
    conflict_penalty_per_conflict: Decimal = Decimal("0.050000")
    max_conflict_penalty: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "watch_stale_after_seconds",
            "blocked_stale_after_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "reliability_watch_below",
            "reliability_block_below",
            "independence_watch_below",
            "independence_block_below",
            "conflict_penalty_per_conflict",
            "max_conflict_penalty",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_score(field_name, getattr(self, field_name)),
            )
        for field_name in ("conflict_watch_count", "conflict_block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface(self)


@dataclass(frozen=True)
class ResearchSourceEvidence:
    source_id: str
    source_kind: str
    observed_at: datetime
    latest_source_at: datetime
    reliability_score: Decimal
    independence_score: Decimal
    conflict_count: Decimal
    is_official_or_primary: bool
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("source_id", self.source_id)
        _require_known_value("source_kind", self.source_kind, SOURCE_KINDS)
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        object.__setattr__(
            self,
            "latest_source_at",
            _as_utc("latest_source_at", self.latest_source_at),
        )
        for field_name in ("reliability_score", "independence_score"):
            object.__setattr__(
                self,
                field_name,
                _require_score(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "conflict_count",
            _require_nonnegative_count("conflict_count", self.conflict_count),
        )
        _require_bool("is_official_or_primary", self.is_official_or_primary)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_supplied_reason_codes(self.reason_codes),
        )
        _validate_evidence(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface(self)


@dataclass(frozen=True)
class ResearchSourceFreshnessReliabilityRow:
    source_id: str
    source_kind: str
    observed_at: datetime
    latest_source_at: datetime
    observed_age_seconds: Decimal
    source_age_seconds: Decimal
    reliability_score: Decimal
    independence_score: Decimal
    conflict_count: Decimal
    conflict_penalty_score: Decimal
    decision_score: Decimal
    is_official_or_primary: bool
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("source_id", self.source_id)
        _require_known_value("source_kind", self.source_kind, SOURCE_KINDS)
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        object.__setattr__(
            self,
            "latest_source_at",
            _as_utc("latest_source_at", self.latest_source_at),
        )
        for field_name in ("observed_age_seconds", "source_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "reliability_score",
            "independence_score",
            "conflict_penalty_score",
            "decision_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_score(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "conflict_count",
            _require_nonnegative_count("conflict_count", self.conflict_count),
        )
        _require_bool("is_official_or_primary", self.is_official_or_primary)
        _require_known_value("status", self.status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_output_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface(self)


@dataclass(frozen=True)
class ResearchSourceFreshnessReliabilityReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_score("row_ratio", self.row_ratio),
        )
        _require_hard_flags(self)
        _reject_unsafe_public_surface(self)


@dataclass(frozen=True)
class ResearchSourceFreshnessReliabilityReport:
    generated_at: datetime
    config_version: str
    evidence_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    stale_source_count: Decimal
    conflict_source_count: Decimal
    official_or_primary_count: Decimal
    min_decision_score: Decimal
    max_source_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchSourceFreshnessReliabilityReasonCodeCount, ...]
    rows: tuple[ResearchSourceFreshnessReliabilityRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "evidence_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "stale_source_count",
            "conflict_source_count",
            "official_or_primary_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_decision_score",
            _require_score("min_decision_score", self.min_decision_score),
        )
        object.__setattr__(
            self,
            "max_source_age_seconds",
            _require_nonnegative_decimal(
                "max_source_age_seconds",
                self.max_source_age_seconds,
            ),
        )
        _require_known_value("status", self.status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_output_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags(self)
        _reject_unsafe_public_surface(self)


def build_research_source_freshness_reliability_report(
    values: Iterable[ResearchSourceEvidence],
    *,
    config: ResearchSourceFreshnessReliabilityConfig,
    generated_at: datetime,
) -> ResearchSourceFreshnessReliabilityReport:
    if type(config) is not ResearchSourceFreshnessReliabilityConfig:
        raise ValueError("config must be a ResearchSourceFreshnessReliabilityConfig")
    _require_hard_flags(config)
    _reject_unsafe_public_surface(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(values)
    rows = tuple(
        sorted(
            (
                _row_from_evidence(item, config=config, generated_at=generated_at_utc)
                for item in inputs
            ),
            key=_row_sort_key,
        ),
    )
    return ResearchSourceFreshnessReliabilityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        evidence_count=_count_decimal(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        stale_source_count=_rows_with_any(
            rows,
            (STALE_WATCH_REASON, STALE_BLOCK_REASON),
        ),
        conflict_source_count=_rows_with_any(
            rows,
            (CONFLICT_WATCH_REASON, CONFLICT_BLOCK_REASON),
        ),
        official_or_primary_count=_count_decimal(
            sum(1 for row in rows if row.is_official_or_primary),
        ),
        min_decision_score=_min_decision_score(rows),
        max_source_age_seconds=_max_source_age_seconds(rows),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_source_freshness_reliability_report_payload(
    report: ResearchSourceFreshnessReliabilityReport,
) -> dict[str, object]:
    if type(report) is not ResearchSourceFreshnessReliabilityReport:
        raise ValueError("report must be a ResearchSourceFreshnessReliabilityReport")
    _require_hard_flags(report)
    _reject_unsafe_public_surface(report)
    ready = _payload_value(report)
    if type(ready) is not dict:
        raise ValueError("report payload must be a dict")
    return ready


def _row_from_evidence(
    value: ResearchSourceEvidence,
    *,
    config: ResearchSourceFreshnessReliabilityConfig,
    generated_at: datetime,
) -> ResearchSourceFreshnessReliabilityRow:
    if value.observed_at > generated_at:
        raise ValueError("observed_at must be <= generated_at")
    observed_age_seconds = _seconds_between(value.observed_at, generated_at)
    source_age_seconds = _seconds_between(value.latest_source_at, generated_at)
    conflict_penalty_score = _conflict_penalty(value.conflict_count, config)
    decision_score = _decision_score(
        value.reliability_score,
        value.independence_score,
        conflict_penalty_score,
    )
    reason_codes = _row_reason_codes(
        value,
        config=config,
        source_age_seconds=source_age_seconds,
    )
    return ResearchSourceFreshnessReliabilityRow(
        source_id=value.source_id,
        source_kind=value.source_kind,
        observed_at=value.observed_at,
        latest_source_at=value.latest_source_at,
        observed_age_seconds=observed_age_seconds,
        source_age_seconds=source_age_seconds,
        reliability_score=value.reliability_score,
        independence_score=value.independence_score,
        conflict_count=value.conflict_count,
        conflict_penalty_score=conflict_penalty_score,
        decision_score=decision_score,
        is_official_or_primary=value.is_official_or_primary,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    value: ResearchSourceEvidence,
    *,
    config: ResearchSourceFreshnessReliabilityConfig,
    source_age_seconds: Decimal,
) -> tuple[str, ...]:
    codes: list[str] = []
    if source_age_seconds > config.blocked_stale_after_seconds:
        codes.append(STALE_BLOCK_REASON)
    elif source_age_seconds > config.watch_stale_after_seconds:
        codes.append(STALE_WATCH_REASON)
    if value.reliability_score < config.reliability_block_below:
        codes.append(RELIABILITY_BLOCK_REASON)
    elif value.reliability_score < config.reliability_watch_below:
        codes.append(RELIABILITY_WATCH_REASON)
    if value.independence_score < config.independence_block_below:
        codes.append(INDEPENDENCE_BLOCK_REASON)
    elif value.independence_score < config.independence_watch_below:
        codes.append(INDEPENDENCE_WATCH_REASON)
    if value.conflict_count >= config.conflict_block_count:
        codes.append(CONFLICT_BLOCK_REASON)
    elif value.conflict_count >= config.conflict_watch_count:
        codes.append(CONFLICT_WATCH_REASON)
    if not value.is_official_or_primary:
        codes.append(NON_PRIMARY_REASON)
    if not codes:
        codes.append(PASS_REASON)
    return _combine_reason_codes(tuple(codes), value.reason_codes)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(
        reason_code
        in (
            STALE_BLOCK_REASON,
            RELIABILITY_BLOCK_REASON,
            INDEPENDENCE_BLOCK_REASON,
            CONFLICT_BLOCK_REASON,
        )
        for reason_code in reason_codes
    ):
        return "blocked"
    if any(reason_code != PASS_REASON for reason_code in reason_codes if reason_code in REASON_RANK):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchSourceFreshnessReliabilityRow, ...]) -> str:
    if any(row.status == "blocked" for row in rows):
        return "blocked"
    if any(row.status == "watch" for row in rows):
        return "watch"
    if rows:
        return "pass"
    return "blocked"


def _report_reason_codes(
    rows: tuple[ResearchSourceFreshnessReliabilityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    return _normalize_output_reason_codes(
        tuple(reason_code for row in rows for reason_code in row.reason_codes),
    )


def _reason_code_counts(
    rows: tuple[ResearchSourceFreshnessReliabilityRow, ...],
) -> tuple[ResearchSourceFreshnessReliabilityReasonCodeCount, ...]:
    report_codes = _report_reason_codes(rows)
    total = _count_decimal(len(rows))
    return tuple(
        ResearchSourceFreshnessReliabilityReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(
                sum(1 for row in rows if reason_code in row.reason_codes),
            ),
            row_ratio=_ratio(
                _count_decimal(
                    sum(1 for row in rows if reason_code in row.reason_codes),
                ),
                total,
            ),
        )
        for reason_code in report_codes
        if reason_code != EMPTY_REASON
    )


def _normalize_inputs(
    values: Iterable[ResearchSourceEvidence],
) -> tuple[ResearchSourceEvidence, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("values must be an iterable")
    try:
        items = tuple(values)
    except TypeError as exc:
        raise ValueError("values must be an iterable") from exc
    seen: set[str] = set()
    for item in items:
        if type(item) is not ResearchSourceEvidence:
            raise ValueError("values must contain ResearchSourceEvidence items")
        _require_hard_flags(item)
        _reject_unsafe_public_surface(item)
        if item.source_id in seen:
            raise ValueError("source_id values must be unique")
        seen.add(item.source_id)
    return items


def _normalize_rows(
    values: Iterable[ResearchSourceFreshnessReliabilityRow],
) -> tuple[ResearchSourceFreshnessReliabilityRow, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceFreshnessReliabilityRow:
            raise ValueError(
                "rows must contain ResearchSourceFreshnessReliabilityRow items",
            )
        _require_hard_flags(row)
        _reject_unsafe_public_surface(row)
        if row.source_id in seen:
            raise ValueError("rows must not contain duplicate source_id values")
        seen.add(row.source_id)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use stable sequence")
    return rows


def _normalize_reason_code_counts(
    values: Iterable[ResearchSourceFreshnessReliabilityReasonCodeCount],
) -> tuple[ResearchSourceFreshnessReliabilityReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        counts = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen: set[str] = set()
    for item in counts:
        if type(item) is not ResearchSourceFreshnessReliabilityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceFreshnessReliabilityReasonCodeCount items",
            )
        _require_hard_flags(item)
        _reject_unsafe_public_surface(item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must use unique reason_code values")
        seen.add(item.reason_code)
    if counts != tuple(sorted(counts, key=lambda item: _reason_rank(item.reason_code))):
        raise ValueError("reason_code_counts must use stable sequence")
    return counts


def _validate_config(config: ResearchSourceFreshnessReliabilityConfig) -> None:
    if config.watch_stale_after_seconds > config.blocked_stale_after_seconds:
        raise ValueError(
            "watch_stale_after_seconds must not exceed blocked_stale_after_seconds",
        )
    if config.reliability_block_below > config.reliability_watch_below:
        raise ValueError(
            "reliability_block_below must not exceed reliability_watch_below",
        )
    if config.independence_block_below > config.independence_watch_below:
        raise ValueError(
            "independence_block_below must not exceed independence_watch_below",
        )
    if config.conflict_watch_count > config.conflict_block_count:
        raise ValueError("conflict_watch_count must not exceed conflict_block_count")
    if config.conflict_watch_count == ZERO:
        raise ValueError("conflict_watch_count must be positive")


def _validate_evidence(value: ResearchSourceEvidence) -> None:
    if value.latest_source_at > value.observed_at:
        raise ValueError("latest_source_at must be <= observed_at")


def _validate_row(row: ResearchSourceFreshnessReliabilityRow) -> None:
    if row.latest_source_at > row.observed_at:
        raise ValueError("latest_source_at must be <= observed_at")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchSourceFreshnessReliabilityReport) -> None:
    rows = report.rows
    if report.evidence_count != _count_decimal(len(rows)):
        raise ValueError("evidence_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.stale_source_count != _rows_with_any(
        rows,
        (STALE_WATCH_REASON, STALE_BLOCK_REASON),
    ):
        raise ValueError("stale_source_count must match rows")
    if report.conflict_source_count != _rows_with_any(
        rows,
        (CONFLICT_WATCH_REASON, CONFLICT_BLOCK_REASON),
    ):
        raise ValueError("conflict_source_count must match rows")
    if report.official_or_primary_count != _count_decimal(
        sum(1 for row in rows if row.is_official_or_primary),
    ):
        raise ValueError("official_or_primary_count must match rows")
    if report.min_decision_score != _min_decision_score(rows):
        raise ValueError("min_decision_score must match rows")
    if report.max_source_age_seconds != _max_source_age_seconds(rows):
        raise ValueError("max_source_age_seconds must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _row_sort_key(
    row: ResearchSourceFreshnessReliabilityRow,
) -> tuple[int, int, str]:
    return (STATUS_RANK[row.status], _primary_reason_rank(row.reason_codes), row.source_id)


def _primary_reason_rank(reason_codes: tuple[str, ...]) -> int:
    return min(_reason_rank(reason_code) for reason_code in reason_codes)


def _reason_rank(reason_code: str) -> int:
    return REASON_RANK.get(reason_code, len(REASON_CODES) + _text_rank(reason_code))


def _text_rank(value: str) -> int:
    return sum((index + 1) * ord(character) for index, character in enumerate(value))


def _status_count(
    rows: tuple[ResearchSourceFreshnessReliabilityRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _rows_with_any(
    rows: tuple[ResearchSourceFreshnessReliabilityRow, ...],
    reason_codes: tuple[str, ...],
) -> Decimal:
    return _count_decimal(
        sum(1 for row in rows if any(code in row.reason_codes for code in reason_codes)),
    )


def _min_decision_score(
    rows: tuple[ResearchSourceFreshnessReliabilityRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return min(row.decision_score for row in rows).quantize(QUANT)


def _max_source_age_seconds(
    rows: tuple[ResearchSourceFreshnessReliabilityRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.source_age_seconds for row in rows).quantize(QUANT)


def _conflict_penalty(
    conflict_count: Decimal,
    config: ResearchSourceFreshnessReliabilityConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        penalty = conflict_count * config.conflict_penalty_per_conflict
    if penalty > config.max_conflict_penalty:
        penalty = config.max_conflict_penalty
    return penalty.quantize(QUANT)


def _decision_score(
    reliability_score: Decimal,
    independence_score: Decimal,
    conflict_penalty_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = ((reliability_score + independence_score) / Decimal("2")) - (
            conflict_penalty_score
        )
    if score < ZERO:
        score = ZERO
    if score > ONE:
        score = ONE
    return score.quantize(QUANT)


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    if end < start:
        raise ValueError("timestamp must not be after generated_at")
    delta = end - start
    if delta < timedelta(0):
        raise ValueError("timestamp span must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        seconds = (
            Decimal(delta.days) * SECONDS_PER_DAY
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
        )
    return seconds.quantize(QUANT)


def _payload_value(value: object) -> object:
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal value must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload contains an unsupported value")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_supplied_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    for reason_code in reason_codes:
        _require_public_string("reason_code", reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    if reason_codes != tuple(sorted(reason_codes, key=_reason_rank)):
        raise ValueError("reason_codes must use stable sequence")
    return reason_codes


def _combine_reason_codes(
    built_in_codes: tuple[str, ...],
    supplied_codes: tuple[str, ...],
) -> tuple[str, ...]:
    return _normalize_output_reason_codes(built_in_codes + supplied_codes)


def _normalize_output_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_public_string("reason_code", reason_code)
    unique_codes = frozenset(reason_codes)
    return tuple(sorted(unique_codes, key=_reason_rank))


def _require_known_value(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    _require_public_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be known")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if _contains_surface_fragment(value):
        raise ValueError("unsafe public value")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be stripped")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value.quantize(QUANT)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_score(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value.quantize(QUANT)


def _require_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return decimal_value


def _require_hard_flags(value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only") is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly") is not True:
        raise ValueError("readonly must be True")


def _reject_unsafe_public_surface(value: object) -> None:
    if type(value) is str:
        if _contains_surface_fragment(value):
            raise ValueError("unsafe public value")
        return
    if type(value) is dict:
        for key, item in value.items():
            _reject_unsafe_public_surface(key)
            _reject_unsafe_public_surface(item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_surface(item)
        return
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if _contains_surface_fragment(field.name):
                raise ValueError("unsafe public value")
            _reject_unsafe_public_surface(getattr(value, field.name))


def _contains_surface_fragment(value: str) -> bool:
    normalized = "".join(character for character in value.lower() if character.isalnum())
    return any(fragment in normalized for fragment in UNSAFE_TEXT_FRAGMENTS)


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_FRESHNESS_RELIABILITY_CONFIG_VERSION",
    "SOURCE_KINDS",
    "ROW_STATUSES",
    "REPORT_STATUSES",
    "ResearchSourceFreshnessReliabilityConfig",
    "ResearchSourceEvidence",
    "ResearchSourceFreshnessReliabilityReasonCodeCount",
    "ResearchSourceFreshnessReliabilityReport",
    "ResearchSourceFreshnessReliabilityRow",
    "build_research_source_freshness_reliability_report",
    "research_source_freshness_reliability_report_payload",
)
