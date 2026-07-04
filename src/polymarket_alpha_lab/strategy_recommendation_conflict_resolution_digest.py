"""Pure Phase 1 digest for strategy recommendation conflict resolution."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    UNSAFE_SURFACE_FIELD_FRAGMENTS,
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_RECOMMENDATION_CONFLICT_RESOLUTION_DIGEST_CONFIG_VERSION = (
    "strategy-recommendation-conflict-resolution-digest-v0"
)

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
SECONDS_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ZERO_SECONDS = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

RECOMMENDATIONS = ("recommend", "watch", "avoid")
SOURCE_CONFLICT_STATUSES = ("resolved", "unresolved")
REVIEWER_RESOLUTIONS = ("approve", "override", "defer", "reject")
ROW_STATUSES = ("clear", "watch", "blocked")
REPORT_STATUSES = ("clear", "watch", "blocked")
POSITIVE_REASON_CODES = frozenset(
    (
        "positive_edge",
        "market_context_supportive",
    ),
)
NEGATIVE_REASON_CODES = frozenset(
    (
        "negative_edge",
        "market_context_adverse",
    ),
)
ALLOWED_INPUT_REASON_CODES = tuple(
    sorted(POSITIVE_REASON_CODES | NEGATIVE_REASON_CODES),
)
ROW_REASON_CODES = (
    "forecast_market_context_disagreement",
    "contradictory_reason_codes",
    "unresolved_source_conflict",
    "stale_conflict_acknowledgement",
    "missing_reviewer_resolution",
    "conflict_resolution_clear",
)
REPORT_REASON_CODES = (
    "forecast_market_context_disagreement",
    "contradictory_reason_codes",
    "unresolved_source_conflict",
    "stale_conflict_acknowledgement",
    "missing_reviewer_resolution",
    "conflict_resolution_digest_clear",
)
BLOCKING_REASON_CODES = (
    "forecast_market_context_disagreement",
    "contradictory_reason_codes",
    "unresolved_source_conflict",
    "missing_reviewer_resolution",
)
STATUS_WEIGHT = {
    "blocked": Decimal("2"),
    "watch": Decimal("1"),
    "clear": Decimal("0"),
}
TEXT_VALUE_FRAGMENTS = frozenset(
    (
        *UNSAFE_SURFACE_FIELD_FRAGMENTS,
        "sec" "ret",
        "tok" "en",
        "cred" "ential",
        "api" "_" "key",
        "pass" "word",
        "bearer",
        "dsn",
        "database" "_" "url",
        "sk" "_",
    ),
)


@dataclass(frozen=True)
class StrategyRecommendationConflictResolutionDigestConfig:
    config_version: str = (
        DEFAULT_STRATEGY_RECOMMENDATION_CONFLICT_RESOLUTION_DIGEST_CONFIG_VERSION
    )
    stale_acknowledgement_age_seconds: Decimal = Decimal("7200.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationConflictResolutionDigestConfig:
            raise ValueError(
                "config must be a StrategyRecommendationConflictResolutionDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "stale_acknowledgement_age_seconds",
            _normalize_positive_seconds(
                "stale_acknowledgement_age_seconds",
                self.stale_acknowledgement_age_seconds,
            ),
        )
        require_paper_only_flags("config", self)
        reject_unsafe_surface_fields("config", self)


@dataclass(frozen=True)
class StrategyRecommendationConflictResolutionInput:
    recommendation_id: str
    candidate_id: str
    forecast_recommendation: str
    market_context_recommendation: str
    forecast_reason_codes: tuple[str, ...]
    market_reason_codes: tuple[str, ...]
    source_conflict_status: str
    conflict_acknowledged_at: datetime | None
    reviewer_resolution: str | None
    reviewer_id: str | None
    observed_at: datetime
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationConflictResolutionInput:
            raise ValueError(
                "input row must be a StrategyRecommendationConflictResolutionInput",
            )
        for field_name in (
            "recommendation_id",
            "candidate_id",
            "source_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member(
            "forecast_recommendation",
            self.forecast_recommendation,
            RECOMMENDATIONS,
        )
        _require_member(
            "market_context_recommendation",
            self.market_context_recommendation,
            RECOMMENDATIONS,
        )
        object.__setattr__(
            self,
            "forecast_reason_codes",
            _normalize_input_reason_codes(
                "forecast_reason_codes",
                self.forecast_reason_codes,
            ),
        )
        object.__setattr__(
            self,
            "market_reason_codes",
            _normalize_input_reason_codes(
                "market_reason_codes",
                self.market_reason_codes,
            ),
        )
        _require_member(
            "source_conflict_status",
            self.source_conflict_status,
            SOURCE_CONFLICT_STATUSES,
        )
        object.__setattr__(
            self,
            "conflict_acknowledged_at",
            _as_optional_utc(
                "conflict_acknowledged_at",
                self.conflict_acknowledged_at,
            ),
        )
        object.__setattr__(
            self,
            "reviewer_resolution",
            _normalize_optional_member(
                "reviewer_resolution",
                self.reviewer_resolution,
                REVIEWER_RESOLUTIONS,
            ),
        )
        object.__setattr__(
            self,
            "reviewer_id",
            _normalize_optional_string("reviewer_id", self.reviewer_id),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        require_paper_only_flags("input row", self)
        reject_unsafe_surface_fields("input row", self)


@dataclass(frozen=True)
class StrategyRecommendationConflictResolutionDigestRow:
    recommendation_id: str
    candidate_id: str
    status: str
    forecast_recommendation: str
    market_context_recommendation: str
    forecast_reason_codes: tuple[str, ...]
    market_reason_codes: tuple[str, ...]
    source_conflict_status: str
    conflict_acknowledged: bool
    reviewer_resolution: str | None
    reviewer_id: str | None
    observed_age_seconds: Decimal
    acknowledgement_age_seconds: Decimal | None
    contradictory_reason_code_count: Decimal
    reason_codes: tuple[str, ...]
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationConflictResolutionDigestRow:
            raise ValueError(
                "digest row must be a StrategyRecommendationConflictResolutionDigestRow",
            )
        for field_name in (
            "recommendation_id",
            "candidate_id",
            "source_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member("status", self.status, ROW_STATUSES)
        _require_member(
            "forecast_recommendation",
            self.forecast_recommendation,
            RECOMMENDATIONS,
        )
        _require_member(
            "market_context_recommendation",
            self.market_context_recommendation,
            RECOMMENDATIONS,
        )
        object.__setattr__(
            self,
            "forecast_reason_codes",
            _normalize_input_reason_codes(
                "forecast_reason_codes",
                self.forecast_reason_codes,
            ),
        )
        object.__setattr__(
            self,
            "market_reason_codes",
            _normalize_input_reason_codes(
                "market_reason_codes",
                self.market_reason_codes,
            ),
        )
        _require_member(
            "source_conflict_status",
            self.source_conflict_status,
            SOURCE_CONFLICT_STATUSES,
        )
        if type(self.conflict_acknowledged) is not bool:
            raise ValueError("conflict_acknowledged must be a bool")
        object.__setattr__(
            self,
            "reviewer_resolution",
            _normalize_optional_member(
                "reviewer_resolution",
                self.reviewer_resolution,
                REVIEWER_RESOLUTIONS,
            ),
        )
        object.__setattr__(
            self,
            "reviewer_id",
            _normalize_optional_string("reviewer_id", self.reviewer_id),
        )
        object.__setattr__(
            self,
            "observed_age_seconds",
            _normalize_seconds("observed_age_seconds", self.observed_age_seconds),
        )
        object.__setattr__(
            self,
            "acknowledgement_age_seconds",
            _normalize_optional_seconds(
                "acknowledgement_age_seconds",
                self.acknowledgement_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "contradictory_reason_code_count",
            _normalize_nonnegative_count(
                "contradictory_reason_code_count",
                self.contradictory_reason_code_count,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        require_paper_only_flags("digest row", self)
        reject_unsafe_surface_fields("digest row", self)


@dataclass(frozen=True)
class StrategyRecommendationConflictResolutionDigestReport:
    generated_at: datetime
    config_version: str
    status: str
    reason_codes: tuple[str, ...]
    input_count: Decimal
    row_count: Decimal
    clear_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    contradictory_reason_code_count: Decimal
    forecast_market_disagreement_count: Decimal
    unresolved_source_conflict_count: Decimal
    stale_acknowledgement_count: Decimal
    missing_reviewer_resolution_count: Decimal
    blocked_ratio: Decimal
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    rows: tuple[StrategyRecommendationConflictResolutionDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationConflictResolutionDigestReport:
            raise ValueError(
                "report must be a StrategyRecommendationConflictResolutionDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_member("status", self.status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        for field_name in (
            "input_count",
            "row_count",
            "clear_count",
            "watch_count",
            "blocked_count",
            "contradictory_reason_code_count",
            "forecast_market_disagreement_count",
            "unresolved_source_conflict_count",
            "stale_acknowledgement_count",
            "missing_reviewer_resolution_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "blocked_ratio",
            _normalize_ratio("blocked_ratio", self.blocked_ratio),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        require_paper_only_flags("report", self)
        reject_unsafe_surface_fields("report", self)


def build_strategy_recommendation_conflict_resolution_digest(
    inputs: object,
    *,
    config: StrategyRecommendationConflictResolutionDigestConfig,
    generated_at: datetime,
) -> StrategyRecommendationConflictResolutionDigestReport:
    if type(config) is not StrategyRecommendationConflictResolutionDigestConfig:
        raise ValueError(
            "config must be a StrategyRecommendationConflictResolutionDigestConfig",
        )
    require_paper_only_flags("config", config)
    reject_unsafe_surface_fields("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _normalize_inputs(inputs, generated_at_utc)
    digest_rows = tuple(
        sorted(
            (
                _digest_row(row, generated_at=generated_at_utc, config=config)
                for row in rows
            ),
            key=_row_sort_key,
        ),
    )
    reason_code_counts = _reason_code_counts(digest_rows)
    return StrategyRecommendationConflictResolutionDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(digest_rows),
        reason_codes=_report_reason_codes(digest_rows),
        input_count=_count(len(rows)),
        row_count=_count(len(digest_rows)),
        clear_count=_status_count(digest_rows, "clear"),
        watch_count=_status_count(digest_rows, "watch"),
        blocked_count=_status_count(digest_rows, "blocked"),
        contradictory_reason_code_count=_row_reason_count(
            digest_rows,
            "contradictory_reason_codes",
        ),
        forecast_market_disagreement_count=_row_reason_count(
            digest_rows,
            "forecast_market_context_disagreement",
        ),
        unresolved_source_conflict_count=_row_reason_count(
            digest_rows,
            "unresolved_source_conflict",
        ),
        stale_acknowledgement_count=_row_reason_count(
            digest_rows,
            "stale_conflict_acknowledgement",
        ),
        missing_reviewer_resolution_count=_row_reason_count(
            digest_rows,
            "missing_reviewer_resolution",
        ),
        blocked_ratio=_ratio(len(tuple(row for row in digest_rows if row.status == "blocked")), len(digest_rows)),
        reason_code_counts=reason_code_counts,
        rows=digest_rows,
    )


def strategy_recommendation_conflict_resolution_digest_payload(
    report: StrategyRecommendationConflictResolutionDigestReport,
) -> dict[str, Any]:
    if type(report) is not StrategyRecommendationConflictResolutionDigestReport:
        raise ValueError(
            "report must be a StrategyRecommendationConflictResolutionDigestReport",
        )
    require_paper_only_flags("report", report)
    reject_unsafe_surface_fields("report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("report must convert to a JSON object")
    reject_unsafe_surface_fields("report payload", payload)
    _reject_unsafe_text_values("report payload", payload)
    return payload


def _digest_row(
    row: StrategyRecommendationConflictResolutionInput,
    *,
    generated_at: datetime,
    config: StrategyRecommendationConflictResolutionDigestConfig,
) -> StrategyRecommendationConflictResolutionDigestRow:
    observed_age_seconds = _age_seconds(generated_at, row.observed_at)
    acknowledgement_age_seconds = (
        None
        if row.conflict_acknowledged_at is None
        else _age_seconds(generated_at, row.conflict_acknowledged_at)
    )
    contradictory_count = _contradictory_reason_code_count(
        row.forecast_reason_codes,
        row.market_reason_codes,
    )
    reason_codes = _row_reason_codes(
        row,
        contradictory_count=contradictory_count,
        acknowledgement_age_seconds=acknowledgement_age_seconds,
        config=config,
    )
    return StrategyRecommendationConflictResolutionDigestRow(
        recommendation_id=row.recommendation_id,
        candidate_id=row.candidate_id,
        status=_row_status(reason_codes),
        forecast_recommendation=row.forecast_recommendation,
        market_context_recommendation=row.market_context_recommendation,
        forecast_reason_codes=row.forecast_reason_codes,
        market_reason_codes=row.market_reason_codes,
        source_conflict_status=row.source_conflict_status,
        conflict_acknowledged=row.conflict_acknowledged_at is not None,
        reviewer_resolution=row.reviewer_resolution,
        reviewer_id=row.reviewer_id,
        observed_age_seconds=observed_age_seconds,
        acknowledgement_age_seconds=acknowledgement_age_seconds,
        contradictory_reason_code_count=contradictory_count,
        reason_codes=reason_codes,
        source_config_version=row.source_config_version,
    )


def _row_reason_codes(
    row: StrategyRecommendationConflictResolutionInput,
    *,
    contradictory_count: Decimal,
    acknowledgement_age_seconds: Decimal | None,
    config: StrategyRecommendationConflictResolutionDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if row.forecast_recommendation != row.market_context_recommendation:
        reasons.append("forecast_market_context_disagreement")
    if contradictory_count > ZERO_COUNT:
        reasons.append("contradictory_reason_codes")
    if row.source_conflict_status == "unresolved":
        reasons.append("unresolved_source_conflict")
    if (
        acknowledgement_age_seconds is not None
        and acknowledgement_age_seconds >= config.stale_acknowledgement_age_seconds
    ):
        reasons.append("stale_conflict_acknowledgement")
    if row.reviewer_resolution is None:
        reasons.append("missing_reviewer_resolution")
    if not reasons:
        reasons.append("conflict_resolution_clear")
    return _normalize_reason_codes("reason_codes", tuple(reasons), ROW_REASON_CODES)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKING_REASON_CODES for reason_code in reason_codes):
        return "blocked"
    if "stale_conflict_acknowledgement" in reason_codes:
        return "watch"
    return "clear"


def _report_status(
    rows: tuple[StrategyRecommendationConflictResolutionDigestRow, ...],
) -> str:
    if not rows:
        return "clear"
    if any(row.status == "blocked" for row in rows):
        return "blocked"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "clear"


def _report_reason_codes(
    rows: tuple[StrategyRecommendationConflictResolutionDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("conflict_resolution_digest_clear",)
    row_codes = tuple(reason_code for row in rows for reason_code in row.reason_codes)
    reasons = tuple(
        reason_code
        for reason_code in REPORT_REASON_CODES
        if reason_code != "conflict_resolution_digest_clear"
        and reason_code in row_codes
    )
    if reasons:
        return _normalize_reason_codes("reason_codes", reasons, REPORT_REASON_CODES)
    return ("conflict_resolution_digest_clear",)


def _reason_code_counts(
    rows: tuple[StrategyRecommendationConflictResolutionDigestRow, ...],
) -> tuple[tuple[str, Decimal], ...]:
    counts = []
    for reason_code in ROW_REASON_CODES:
        if reason_code == "conflict_resolution_clear":
            continue
        count = _row_reason_count(rows, reason_code)
        if count > ZERO_COUNT:
            counts.append((reason_code, count))
    return tuple(counts)


def _contradictory_reason_code_count(
    forecast_reason_codes: tuple[str, ...],
    market_reason_codes: tuple[str, ...],
) -> Decimal:
    input_sets = (
        set(forecast_reason_codes),
        set(market_reason_codes),
    )
    return _count(
        sum(
            1
            for reason_codes in input_sets
            if reason_codes & POSITIVE_REASON_CODES
            and reason_codes & NEGATIVE_REASON_CODES
        ),
    )


def _normalize_inputs(
    value: object,
    generated_at: datetime,
) -> tuple[StrategyRecommendationConflictResolutionInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(value)
    seen_ids: set[str] = set()
    for row in rows:
        if type(row) is not StrategyRecommendationConflictResolutionInput:
            raise ValueError(
                "inputs must contain StrategyRecommendationConflictResolutionInput values",
            )
        require_paper_only_flags("input row", row)
        reject_unsafe_surface_fields("input row", row)
        if row.observed_at > generated_at:
            raise ValueError("observed_at must not be in the future")
        if (
            row.conflict_acknowledged_at is not None
            and row.conflict_acknowledged_at > generated_at
        ):
            raise ValueError("conflict_acknowledged_at must not be in the future")
        if row.recommendation_id in seen_ids:
            raise ValueError("inputs must not contain duplicate recommendation_id values")
        seen_ids.add(row.recommendation_id)
    return tuple(sorted(rows, key=lambda row: row.recommendation_id))


def _normalize_rows(
    value: object,
) -> tuple[StrategyRecommendationConflictResolutionDigestRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_ids: set[str] = set()
    for row in rows:
        if type(row) is not StrategyRecommendationConflictResolutionDigestRow:
            raise ValueError(
                "rows must contain StrategyRecommendationConflictResolutionDigestRow values",
            )
        require_paper_only_flags("digest row", row)
        reject_unsafe_surface_fields("digest row", row)
        if row.recommendation_id in seen_ids:
            raise ValueError("rows must not contain duplicate recommendation_id values")
        seen_ids.add(row.recommendation_id)
    return rows


def _row_sort_key(
    row: StrategyRecommendationConflictResolutionDigestRow,
) -> tuple[Decimal, Decimal, Decimal, str, str]:
    return (
        -STATUS_WEIGHT[row.status],
        -_count(len(tuple(code for code in row.reason_codes if code != "conflict_resolution_clear"))),
        -row.observed_age_seconds,
        row.candidate_id,
        row.recommendation_id,
    )


def _validate_row(row: StrategyRecommendationConflictResolutionDigestRow) -> None:
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.conflict_acknowledged != (row.acknowledgement_age_seconds is not None):
        raise ValueError("conflict_acknowledged must match acknowledgement age")
    if (
        "conflict_resolution_clear" in row.reason_codes
        and len(row.reason_codes) != 1
    ):
        raise ValueError("clear reason must not be mixed with conflicts")
    expected_contradictions = _contradictory_reason_code_count(
        row.forecast_reason_codes,
        row.market_reason_codes,
    )
    if row.contradictory_reason_code_count != expected_contradictions:
        raise ValueError("contradictory_reason_code_count must match inputs")
    if (
        "contradictory_reason_codes" in row.reason_codes
        and row.contradictory_reason_code_count == ZERO_COUNT
    ):
        raise ValueError("contradictory reason requires count")
    if (
        "forecast_market_context_disagreement" in row.reason_codes
        and row.forecast_recommendation == row.market_context_recommendation
    ):
        raise ValueError("forecast-market reason requires different recommendations")
    if (
        "unresolved_source_conflict" in row.reason_codes
        and row.source_conflict_status != "unresolved"
    ):
        raise ValueError("source conflict reason requires unresolved status")
    if (
        "missing_reviewer_resolution" in row.reason_codes
        and row.reviewer_resolution is not None
    ):
        raise ValueError("missing reviewer reason requires no resolution")


def _validate_report(report: StrategyRecommendationConflictResolutionDigestReport) -> None:
    if report.row_count != _count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.clear_count != _status_count(report.rows, "clear"):
        raise ValueError("clear_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.contradictory_reason_code_count != _row_reason_count(
        report.rows,
        "contradictory_reason_codes",
    ):
        raise ValueError("contradictory_reason_code_count must match rows")
    if report.forecast_market_disagreement_count != _row_reason_count(
        report.rows,
        "forecast_market_context_disagreement",
    ):
        raise ValueError("forecast_market_disagreement_count must match rows")
    if report.unresolved_source_conflict_count != _row_reason_count(
        report.rows,
        "unresolved_source_conflict",
    ):
        raise ValueError("unresolved_source_conflict_count must match rows")
    if report.stale_acknowledgement_count != _row_reason_count(
        report.rows,
        "stale_conflict_acknowledgement",
    ):
        raise ValueError("stale_acknowledgement_count must match rows")
    if report.missing_reviewer_resolution_count != _row_reason_count(
        report.rows,
        "missing_reviewer_resolution",
    ):
        raise ValueError("missing_reviewer_resolution_count must match rows")
    if report.blocked_ratio != _ratio(int(report.blocked_count), int(report.row_count)):
        raise ValueError("blocked_ratio must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use stable sort")


def _status_count(
    rows: tuple[StrategyRecommendationConflictResolutionDigestRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _row_reason_count(
    rows: tuple[StrategyRecommendationConflictResolutionDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _ratio(numerator: int, denominator: int) -> Decimal:
    if denominator == 0:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_ratio("ratio", Decimal(numerator) / Decimal(denominator))


def _age_seconds(generated_at: datetime, earlier_at: datetime) -> Decimal:
    delta = _as_utc("generated_at", generated_at) - _as_utc("earlier_at", earlier_at)
    with localcontext(DECIMAL_CONTEXT):
        age_seconds = (
            Decimal(delta.days) * SECONDS_PER_DAY
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
        )
    if age_seconds < ZERO_SECONDS:
        raise ValueError("timestamp must not be in the future")
    return _normalize_seconds("age_seconds", age_seconds)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_positive_seconds(field_name: str, value: object) -> Decimal:
    normalized = _normalize_seconds(field_name, value)
    if normalized <= ZERO_SECONDS:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_optional_seconds(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_seconds(field_name, value)


def _normalize_seconds(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(SECONDS_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    if quantized < ZERO_SECONDS:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    if quantized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_RATIO or value > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0 and 1")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _normalize_reason_code_counts(
    value: object,
) -> tuple[tuple[str, Decimal], ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    normalized: list[tuple[str, Decimal]] = []
    for item in counts:
        if type(item) not in (list, tuple) or len(item) != 2:
            raise ValueError("reason_code_counts items must be pairs")
        reason_code = item[0]
        _require_member("reason_code_counts", reason_code, ROW_REASON_CODES)
        if reason_code == "conflict_resolution_clear":
            raise ValueError("reason_code_counts must not include clear reason")
        normalized.append(
            (
                reason_code,
                _normalize_nonnegative_count("reason_code_counts", item[1]),
            ),
        )
    if tuple(reason_code for reason_code, _count_value in normalized) != tuple(
        reason_code
        for reason_code in ROW_REASON_CODES
        if reason_code != "conflict_resolution_clear"
        and reason_code in tuple(code for code, _count_value in normalized)
    ):
        raise ValueError("reason_code_counts must be deterministic")
    return tuple(normalized)


def _normalize_input_reason_codes(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_member(field_name, reason_code, ALLOWED_INPUT_REASON_CODES)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    return tuple(
        reason_code
        for reason_code in ALLOWED_INPUT_REASON_CODES
        if reason_code in reason_codes
    )


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_member(field_name, reason_code, allowed)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    if tuple(code for code in allowed if code in reason_codes) != reason_codes:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _normalize_optional_member(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> str | None:
    if value is None:
        return None
    _require_member(field_name, value, allowed)
    return value


def _normalize_optional_string(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    _require_canonical_string(field_name, value)
    return value


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_unsafe_text_value(field_name, value)


def _reject_unsafe_text_values(label: str, value: object) -> None:
    if type(value) is str:
        _reject_unsafe_text_value(label, value)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_text_values(key, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_text_values(label, item)


def _reject_unsafe_text_value(field_name: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in TEXT_VALUE_FRAGMENTS):
        raise ValueError(f"{field_name} must not contain unsafe text")


__all__ = (
    "DEFAULT_STRATEGY_RECOMMENDATION_CONFLICT_RESOLUTION_DIGEST_CONFIG_VERSION",
    "StrategyRecommendationConflictResolutionDigestConfig",
    "StrategyRecommendationConflictResolutionInput",
    "StrategyRecommendationConflictResolutionDigestReport",
    "StrategyRecommendationConflictResolutionDigestRow",
    "build_strategy_recommendation_conflict_resolution_digest",
    "strategy_recommendation_conflict_resolution_digest_payload",
)
