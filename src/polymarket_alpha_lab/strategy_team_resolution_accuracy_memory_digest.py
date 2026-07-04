"""Pure Phase 1 report reducer for team resolution accuracy memory."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_TEAM_RESOLUTION_ACCURACY_MEMORY_DIGEST_CONFIG_VERSION = (
    "strategy-team-resolution-accuracy-memory-digest-v0"
)
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0").quantize(COUNT_QUANTUM)
ZERO_RATIO = Decimal("0").quantize(RATIO_QUANTUM)
ONE_RATIO = Decimal("1").quantize(RATIO_QUANTUM)

STATUSES = ("pass", "watch", "blocked")
STATUS_SORT_PRIORITY = {"blocked": 0, "watch": 1, "pass": 2}
EMPTY_REASON_CODE = "strategy_team_resolution_accuracy_memory_digest_empty"
REASON_CODES = (
    "resolution_accuracy_memory_blocked",
    "resolution_accuracy_memory_watch",
    "resolution_accuracy_memory_pass",
    "resolved_accuracy_below_watch",
    "resolved_accuracy_below_pass",
    "miss_severity_above_watch",
    "miss_severity_above_pass",
    "severe_miss_ratio_high",
    "source_reliability_below_min",
)
REPORT_REASON_CODES = (EMPTY_REASON_CODE, *REASON_CODES)
REF_DENYLIST = (
    "0x",
    "@",
    "api" "_" "key",
    "au" "th",
    "bearer ",
    "private",
    "se" "cret",
    "to" "ken",
    "wal" "let",
    "://",
)

__all__ = (
    "DEFAULT_STRATEGY_TEAM_RESOLUTION_ACCURACY_MEMORY_DIGEST_CONFIG_VERSION",
    "StrategyTeamResolutionAccuracyMemoryDigestConfig",
    "StrategyTeamResolutionAccuracyMemoryRecord",
    "StrategyTeamResolutionAccuracyMemoryReasonCodeCount",
    "StrategyTeamResolutionAccuracyMemoryReport",
    "StrategyTeamResolutionAccuracyMemoryRow",
    "build_strategy_team_resolution_accuracy_memory_digest",
    "strategy_team_resolution_accuracy_memory_digest_payload",
)


@dataclass(frozen=True)
class StrategyTeamResolutionAccuracyMemoryDigestConfig:
    config_version: str = (
        DEFAULT_STRATEGY_TEAM_RESOLUTION_ACCURACY_MEMORY_DIGEST_CONFIG_VERSION
    )
    min_pass_accuracy_rate: Decimal = Decimal("0.750000")
    min_watch_accuracy_rate: Decimal = Decimal("0.500000")
    max_pass_average_miss_severity: Decimal = Decimal("0.250000")
    max_watch_average_miss_severity: Decimal = Decimal("0.500000")
    severe_miss_threshold: Decimal = Decimal("0.500000")
    max_severe_miss_ratio: Decimal = Decimal("0.250000")
    min_source_reliability_score: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "min_pass_accuracy_rate",
            "min_watch_accuracy_rate",
            "max_pass_average_miss_severity",
            "max_watch_average_miss_severity",
            "severe_miss_threshold",
            "max_severe_miss_ratio",
            "min_source_reliability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.min_pass_accuracy_rate < self.min_watch_accuracy_rate:
            raise ValueError("min_pass_accuracy_rate must not be below watch")
        if self.max_pass_average_miss_severity > self.max_watch_average_miss_severity:
            raise ValueError("max_pass_average_miss_severity must not exceed watch")
        require_paper_only_flags("StrategyTeamResolutionAccuracyMemoryDigestConfig", self)


@dataclass(frozen=True)
class StrategyTeamResolutionAccuracyMemoryRecord:
    team_id: str
    category_id: str
    event_ref: str
    source_ref: str
    resolved_at: datetime
    predicted_probability: Decimal
    resolved_outcome: bool
    accuracy_hit: bool
    miss_severity: Decimal
    source_reliability_score: Decimal
    source_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", _safe_public_string("team_id", self.team_id))
        object.__setattr__(
            self,
            "category_id",
            _safe_public_string("category_id", self.category_id),
        )
        object.__setattr__(
            self,
            "event_ref",
            _redacted_ref("event_ref", "event_ref", self.event_ref),
        )
        object.__setattr__(
            self,
            "source_ref",
            _redacted_ref("source_ref", "source_ref", self.source_ref),
        )
        object.__setattr__(self, "resolved_at", _as_utc("resolved_at", self.resolved_at))
        object.__setattr__(
            self,
            "predicted_probability",
            _normalize_probability("predicted_probability", self.predicted_probability),
        )
        _require_bool("resolved_outcome", self.resolved_outcome)
        _require_bool("accuracy_hit", self.accuracy_hit)
        object.__setattr__(
            self,
            "miss_severity",
            _normalize_probability("miss_severity", self.miss_severity),
        )
        object.__setattr__(
            self,
            "source_reliability_score",
            _normalize_probability(
                "source_reliability_score",
                self.source_reliability_score,
            ),
        )
        object.__setattr__(
            self,
            "source_count",
            _normalize_positive_count("source_count", self.source_count),
        )
        reject_unsafe_surface_fields("resolution accuracy memory record", self)
        require_paper_only_flags("StrategyTeamResolutionAccuracyMemoryRecord", self)


@dataclass(frozen=True)
class StrategyTeamResolutionAccuracyMemoryRow:
    team_id: str
    category_id: str
    resolved_event_count: Decimal
    correct_event_count: Decimal
    miss_event_count: Decimal
    severe_miss_count: Decimal
    source_count: Decimal
    accuracy_rate: Decimal
    average_miss_severity: Decimal
    severe_miss_ratio: Decimal
    average_source_reliability_score: Decimal
    paper_weight_adjustment: Decimal
    latest_resolved_at: datetime
    status: str
    reason_codes: tuple[str, ...]
    event_refs: tuple[str, ...]
    source_refs: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", _safe_public_string("team_id", self.team_id))
        object.__setattr__(
            self,
            "category_id",
            _safe_public_string("category_id", self.category_id),
        )
        for field_name in (
            "resolved_event_count",
            "correct_event_count",
            "miss_event_count",
            "severe_miss_count",
            "source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "accuracy_rate",
            "average_miss_severity",
            "severe_miss_ratio",
            "average_source_reliability_score",
            "paper_weight_adjustment",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_resolved_at",
            _as_utc("latest_resolved_at", self.latest_resolved_at),
        )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REASON_CODES),
        )
        object.__setattr__(
            self,
            "event_refs",
            _normalize_ref_tuple("event_refs", self.event_refs, "event_ref"),
        )
        object.__setattr__(
            self,
            "source_refs",
            _normalize_ref_tuple("source_refs", self.source_refs, "source_ref"),
        )
        _validate_row(self)
        reject_unsafe_surface_fields("resolution accuracy memory row", self)
        require_paper_only_flags("StrategyTeamResolutionAccuracyMemoryRow", self)


@dataclass(frozen=True)
class StrategyTeamResolutionAccuracyMemoryReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_member("reason_code", self.reason_code, REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_count("count", self.count),
        )
        require_paper_only_flags(
            "StrategyTeamResolutionAccuracyMemoryReasonCodeCount",
            self,
        )


@dataclass(frozen=True)
class StrategyTeamResolutionAccuracyMemoryReport:
    generated_at: datetime
    config_version: str
    source_record_count: Decimal
    team_category_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    resolved_event_count: Decimal
    correct_event_count: Decimal
    miss_event_count: Decimal
    severe_miss_count: Decimal
    source_count: Decimal
    accuracy_rate: Decimal
    average_miss_severity: Decimal
    average_source_reliability_score: Decimal
    average_paper_weight_adjustment: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[StrategyTeamResolutionAccuracyMemoryReasonCodeCount, ...]
    rows: tuple[StrategyTeamResolutionAccuracyMemoryRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "source_record_count",
            "team_category_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "resolved_event_count",
            "correct_event_count",
            "miss_event_count",
            "severe_miss_count",
            "source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "accuracy_rate",
            "average_miss_severity",
            "average_source_reliability_score",
            "average_paper_weight_adjustment",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        reject_unsafe_surface_fields("resolution accuracy memory report", self)
        require_paper_only_flags("StrategyTeamResolutionAccuracyMemoryReport", self)


def build_strategy_team_resolution_accuracy_memory_digest(
    records: Iterable[object],
    *,
    config: StrategyTeamResolutionAccuracyMemoryDigestConfig,
    generated_at: datetime,
) -> StrategyTeamResolutionAccuracyMemoryReport:
    if type(config) is not StrategyTeamResolutionAccuracyMemoryDigestConfig:
        raise ValueError(
            "config must be a StrategyTeamResolutionAccuracyMemoryDigestConfig",
        )
    require_paper_only_flags("StrategyTeamResolutionAccuracyMemoryDigestConfig", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_records = _normalize_records(records)
    for record in source_records:
        if record.resolved_at > generated_at_utc:
            raise ValueError("resolved_at must not be in the future")

    rows = _digest_rows(source_records, config=config)
    return StrategyTeamResolutionAccuracyMemoryReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_record_count=_count(len(source_records)),
        team_category_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        resolved_event_count=_sum_counts(
            tuple(row.resolved_event_count for row in rows),
        ),
        correct_event_count=_sum_counts(tuple(row.correct_event_count for row in rows)),
        miss_event_count=_sum_counts(tuple(row.miss_event_count for row in rows)),
        severe_miss_count=_sum_counts(tuple(row.severe_miss_count for row in rows)),
        source_count=_sum_counts(tuple(row.source_count for row in rows)),
        accuracy_rate=_accuracy_rate(rows),
        average_miss_severity=_weighted_row_average(
            tuple(
                (row.average_miss_severity, row.resolved_event_count)
                for row in rows
            ),
        ),
        average_source_reliability_score=_weighted_row_average(
            tuple(
                (row.average_source_reliability_score, row.source_count)
                for row in rows
            ),
        ),
        average_paper_weight_adjustment=_weighted_row_average(
            tuple(
                (row.paper_weight_adjustment, row.resolved_event_count)
                for row in rows
            ),
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def strategy_team_resolution_accuracy_memory_digest_payload(
    report: StrategyTeamResolutionAccuracyMemoryReport,
) -> dict[str, Any]:
    if type(report) is not StrategyTeamResolutionAccuracyMemoryReport:
        raise ValueError(
            "report must be a StrategyTeamResolutionAccuracyMemoryReport",
        )
    require_paper_only_flags("StrategyTeamResolutionAccuracyMemoryReport", report)
    reject_unsafe_surface_fields("resolution accuracy memory report", report)
    payload = json_ready_no_floats(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    reject_unsafe_surface_fields("resolution accuracy memory payload", payload)
    return payload


def _normalize_records(
    records: Iterable[object],
) -> tuple[StrategyTeamResolutionAccuracyMemoryRecord, ...]:
    if isinstance(records, (str, bytes)):
        raise ValueError("records must be an iterable")
    try:
        normalized = tuple(records)
    except TypeError as exc:
        raise ValueError("records must be an iterable") from exc
    seen_keys: set[tuple[str, str, str]] = set()
    result: list[StrategyTeamResolutionAccuracyMemoryRecord] = []
    for record in normalized:
        if type(record) is not StrategyTeamResolutionAccuracyMemoryRecord:
            raise ValueError(
                "records must contain StrategyTeamResolutionAccuracyMemoryRecord values",
            )
        require_paper_only_flags("StrategyTeamResolutionAccuracyMemoryRecord", record)
        key = (record.team_id, record.category_id, record.event_ref)
        if key in seen_keys:
            raise ValueError("records must be unique by team, category, and event ref")
        seen_keys.add(key)
        result.append(record)
    return tuple(result)


def _digest_rows(
    records: tuple[StrategyTeamResolutionAccuracyMemoryRecord, ...],
    *,
    config: StrategyTeamResolutionAccuracyMemoryDigestConfig,
) -> tuple[StrategyTeamResolutionAccuracyMemoryRow, ...]:
    grouped: dict[tuple[str, str], list[StrategyTeamResolutionAccuracyMemoryRecord]] = {}
    for record in records:
        grouped.setdefault((record.team_id, record.category_id), []).append(record)
    rows = tuple(
        _digest_row(team_id=team_id, category_id=category_id, records=tuple(group), config=config)
        for (team_id, category_id), group in grouped.items()
    )
    return tuple(sorted(rows, key=_row_sort_key))


def _digest_row(
    *,
    team_id: str,
    category_id: str,
    records: tuple[StrategyTeamResolutionAccuracyMemoryRecord, ...],
    config: StrategyTeamResolutionAccuracyMemoryDigestConfig,
) -> StrategyTeamResolutionAccuracyMemoryRow:
    resolved_event_count = _count(len(records))
    correct_event_count = _count(sum(1 for record in records if record.accuracy_hit))
    miss_event_count = resolved_event_count - correct_event_count
    severe_miss_count = _count(
        sum(1 for record in records if record.miss_severity >= config.severe_miss_threshold),
    )
    source_count = _sum_counts(tuple(record.source_count for record in records))
    accuracy_rate = _safe_ratio(correct_event_count, resolved_event_count)
    average_miss_severity = _safe_ratio(
        sum((record.miss_severity for record in records), ZERO_RATIO),
        resolved_event_count,
    )
    severe_miss_ratio = _safe_ratio(severe_miss_count, resolved_event_count)
    average_source_reliability_score = _weighted_average(
        tuple((record.source_reliability_score, record.source_count) for record in records),
    )
    paper_weight_adjustment = _paper_weight_adjustment(
        accuracy_rate=accuracy_rate,
        average_miss_severity=average_miss_severity,
        average_source_reliability_score=average_source_reliability_score,
    )
    reason_codes = _row_reason_codes(
        accuracy_rate=accuracy_rate,
        average_miss_severity=average_miss_severity,
        severe_miss_ratio=severe_miss_ratio,
        average_source_reliability_score=average_source_reliability_score,
        config=config,
    )
    return StrategyTeamResolutionAccuracyMemoryRow(
        team_id=team_id,
        category_id=category_id,
        resolved_event_count=resolved_event_count,
        correct_event_count=correct_event_count,
        miss_event_count=miss_event_count,
        severe_miss_count=severe_miss_count,
        source_count=source_count,
        accuracy_rate=accuracy_rate,
        average_miss_severity=average_miss_severity,
        severe_miss_ratio=severe_miss_ratio,
        average_source_reliability_score=average_source_reliability_score,
        paper_weight_adjustment=paper_weight_adjustment,
        latest_resolved_at=max(record.resolved_at for record in records),
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
        event_refs=tuple(sorted({record.event_ref for record in records})),
        source_refs=tuple(sorted({record.source_ref for record in records})),
    )


def _row_reason_codes(
    *,
    accuracy_rate: Decimal,
    average_miss_severity: Decimal,
    severe_miss_ratio: Decimal,
    average_source_reliability_score: Decimal,
    config: StrategyTeamResolutionAccuracyMemoryDigestConfig,
) -> tuple[str, ...]:
    issue_codes: list[str] = []
    if accuracy_rate < config.min_watch_accuracy_rate:
        issue_codes.append("resolved_accuracy_below_watch")
    elif accuracy_rate < config.min_pass_accuracy_rate:
        issue_codes.append("resolved_accuracy_below_pass")
    if average_miss_severity > config.max_watch_average_miss_severity:
        issue_codes.append("miss_severity_above_watch")
    elif average_miss_severity > config.max_pass_average_miss_severity:
        issue_codes.append("miss_severity_above_pass")
    if severe_miss_ratio > config.max_severe_miss_ratio:
        issue_codes.append("severe_miss_ratio_high")
    if average_source_reliability_score < config.min_source_reliability_score:
        issue_codes.append("source_reliability_below_min")

    if (
        "resolved_accuracy_below_watch" in issue_codes
        or "miss_severity_above_watch" in issue_codes
        or "severe_miss_ratio_high" in issue_codes
    ):
        terminal = "resolution_accuracy_memory_blocked"
    elif issue_codes:
        terminal = "resolution_accuracy_memory_watch"
    else:
        terminal = "resolution_accuracy_memory_pass"
    return _normalize_reason_codes("reason_codes", (terminal, *issue_codes), REASON_CODES)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if "resolution_accuracy_memory_blocked" in reason_codes:
        return "blocked"
    if "resolution_accuracy_memory_watch" in reason_codes:
        return "watch"
    return "pass"


def _report_status(rows: tuple[StrategyTeamResolutionAccuracyMemoryRow, ...]) -> str:
    if any(row.status == "blocked" for row in rows):
        return "blocked"
    if any(row.status == "watch" for row in rows) or not rows:
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[StrategyTeamResolutionAccuracyMemoryRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    observed: set[str] = set()
    for row in rows:
        observed.update(row.reason_codes)
    return tuple(code for code in REPORT_REASON_CODES[1:] if code in observed)


def _reason_code_counts(
    rows: tuple[StrategyTeamResolutionAccuracyMemoryRow, ...],
) -> tuple[StrategyTeamResolutionAccuracyMemoryReasonCodeCount, ...]:
    if not rows:
        return ()
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        sorted(
            (
                StrategyTeamResolutionAccuracyMemoryReasonCodeCount(
                    reason_code=reason_code,
                    count=_count(count),
                )
                for reason_code, count in counts.items()
            ),
            key=_reason_count_sort_key,
        ),
    )


def _reason_count_sort_key(
    item: StrategyTeamResolutionAccuracyMemoryReasonCodeCount,
) -> tuple[Decimal, int, str]:
    return (-item.count, _reason_priority(item.reason_code), item.reason_code)


def _reason_priority(reason_code: str) -> int:
    try:
        return REASON_CODES.index(reason_code)
    except ValueError:
        return len(REASON_CODES)


def _row_sort_key(row: StrategyTeamResolutionAccuracyMemoryRow) -> tuple[int, Decimal, str, str]:
    return (
        STATUS_SORT_PRIORITY[row.status],
        -row.severe_miss_ratio,
        row.team_id,
        row.category_id,
    )


def _status_count(
    rows: tuple[StrategyTeamResolutionAccuracyMemoryRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _accuracy_rate(rows: tuple[StrategyTeamResolutionAccuracyMemoryRow, ...]) -> Decimal:
    return _safe_ratio(
        _sum_counts(tuple(row.correct_event_count for row in rows)),
        _sum_counts(tuple(row.resolved_event_count for row in rows)),
    )


def _weighted_row_average(values: tuple[tuple[Decimal, Decimal], ...]) -> Decimal:
    return _weighted_average(values)


def _weighted_average(values: tuple[tuple[Decimal, Decimal], ...]) -> Decimal:
    total_weight = _sum_counts(tuple(weight for _, weight in values))
    if total_weight == ZERO_COUNT:
        return ZERO_RATIO
    numerator = sum((value * weight for value, weight in values), ZERO_RATIO)
    return _safe_ratio(numerator, total_weight)


def _paper_weight_adjustment(
    *,
    accuracy_rate: Decimal,
    average_miss_severity: Decimal,
    average_source_reliability_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_ratio(
            accuracy_rate
            * average_source_reliability_score
            * (ONE_RATIO - average_miss_severity),
        )


def _validate_row(row: StrategyTeamResolutionAccuracyMemoryRow) -> None:
    if row.resolved_event_count <= ZERO_COUNT:
        raise ValueError("resolved_event_count must be positive")
    if row.resolved_event_count != row.correct_event_count + row.miss_event_count:
        raise ValueError("resolved_event_count must match hit and miss counts")
    if row.severe_miss_count > row.resolved_event_count:
        raise ValueError("severe_miss_count must not exceed resolved_event_count")
    if row.accuracy_rate != _safe_ratio(row.correct_event_count, row.resolved_event_count):
        raise ValueError("accuracy_rate must match counts")
    if row.severe_miss_ratio != _safe_ratio(
        row.severe_miss_count,
        row.resolved_event_count,
    ):
        raise ValueError("severe_miss_ratio must match counts")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report(report: StrategyTeamResolutionAccuracyMemoryReport) -> None:
    if report.source_record_count != _sum_counts(
        tuple(row.resolved_event_count for row in report.rows),
    ):
        raise ValueError("source_record_count must match rows")
    if report.team_category_count != _count(len(report.rows)):
        raise ValueError("team_category_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    expected_counts = {
        "resolved_event_count": _sum_counts(
            tuple(row.resolved_event_count for row in report.rows),
        ),
        "correct_event_count": _sum_counts(
            tuple(row.correct_event_count for row in report.rows),
        ),
        "miss_event_count": _sum_counts(tuple(row.miss_event_count for row in report.rows)),
        "severe_miss_count": _sum_counts(
            tuple(row.severe_miss_count for row in report.rows),
        ),
        "source_count": _sum_counts(tuple(row.source_count for row in report.rows)),
    }
    for field_name, expected in expected_counts.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.accuracy_rate != _accuracy_rate(report.rows):
        raise ValueError("accuracy_rate must match rows")
    if report.average_miss_severity != _weighted_row_average(
        tuple((row.average_miss_severity, row.resolved_event_count) for row in report.rows),
    ):
        raise ValueError("average_miss_severity must match rows")
    if report.average_source_reliability_score != _weighted_row_average(
        tuple((row.average_source_reliability_score, row.source_count) for row in report.rows),
    ):
        raise ValueError("average_source_reliability_score must match rows")
    if report.average_paper_weight_adjustment != _weighted_row_average(
        tuple((row.paper_weight_adjustment, row.resolved_event_count) for row in report.rows),
    ):
        raise ValueError("average_paper_weight_adjustment must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _normalize_rows(
    value: object,
) -> tuple[StrategyTeamResolutionAccuracyMemoryRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(value)
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not StrategyTeamResolutionAccuracyMemoryRow:
            raise ValueError(
                "rows must contain StrategyTeamResolutionAccuracyMemoryRow values",
            )
        require_paper_only_flags("StrategyTeamResolutionAccuracyMemoryRow", row)
        key = (row.team_id, row.category_id)
        if key in seen_keys:
            raise ValueError("rows must be unique by team and category")
        seen_keys.add(key)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[StrategyTeamResolutionAccuracyMemoryReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    items = tuple(value)
    seen_codes: set[str] = set()
    for item in items:
        if type(item) is not StrategyTeamResolutionAccuracyMemoryReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain StrategyTeamResolutionAccuracyMemoryReasonCodeCount values",
            )
        require_paper_only_flags("StrategyTeamResolutionAccuracyMemoryReasonCodeCount", item)
        if item.reason_code in seen_codes:
            raise ValueError("reason_code_counts values must be unique")
        seen_codes.add(item.reason_code)
    if items != tuple(sorted(items, key=_reason_count_sort_key)):
        raise ValueError("reason_code_counts must be deterministically sorted")
    return items


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    codes = tuple(value)
    if not codes:
        raise ValueError(f"{field_name} must not be empty")
    for code in codes:
        _require_member(field_name, code, allowed_codes)
    if len(set(codes)) != len(codes):
        raise ValueError(f"{field_name} values must be unique")
    expected = tuple(code for code in allowed_codes if code in codes)
    if codes != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return codes


def _normalize_ref_tuple(field_name: str, value: object, prefix: str) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    refs = tuple(value)
    for ref in refs:
        _require_redacted_ref(field_name, ref, prefix)
    if len(set(refs)) != len(refs):
        raise ValueError(f"{field_name} values must be unique")
    if refs != tuple(sorted(refs)):
        raise ValueError(f"{field_name} must be sorted")
    return refs


def _require_redacted_ref(field_name: str, value: object, prefix: str) -> None:
    _require_canonical_string(field_name, value)
    if not value.startswith(f"{prefix}_"):
        raise ValueError(f"{field_name} must be redacted")
    if _has_ref_marker(value):
        raise ValueError(f"{field_name} must be redacted")


def _redacted_ref(field_name: str, prefix: str, value: object) -> str:
    raw_value = _canonical_string(field_name, value)
    digest = hashlib.sha256(raw_value.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{digest}"


def _safe_public_string(field_name: str, value: object) -> str:
    text = _canonical_string(field_name, value)
    if _has_ref_marker(text):
        raise ValueError(f"{field_name} must not contain sensitive material")
    return text


def _require_canonical_string(field_name: str, value: object) -> None:
    _canonical_string(field_name, value)


def _canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    return value


def _has_ref_marker(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in REF_DENYLIST)


def _require_member(field_name: str, value: object, choices: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in choices:
        raise ValueError(f"{field_name} must be a known value")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_RATIO or decimal_value > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize_ratio(decimal_value)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        normalized = decimal_value.quantize(COUNT_QUANTUM)
    if normalized != decimal_value:
        raise ValueError(f"{field_name} must be integral")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO_COUNT:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_ratio(numerator / denominator)


def _sum_counts(values: tuple[Decimal, ...]) -> Decimal:
    return sum(values, ZERO_COUNT).quantize(COUNT_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _quantize_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)
