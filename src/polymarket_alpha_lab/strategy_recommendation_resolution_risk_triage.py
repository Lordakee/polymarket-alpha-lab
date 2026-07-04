"""Pure report-only triage for recommendation resolution-risk readiness."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from typing import Any, Iterable


QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0")
ONE = Decimal("1")
HOURS_PER_DAY = Decimal("24")
DECIMAL_CONTEXT = Context(prec=64)
ROW_STATUSES = ("clear", "watch", "blocked")
REPORT_STATUSES = ("empty", "clear", "watch", "blocked")
STATUS_RANK = {"blocked": 0, "watch": 1, "clear": 2}
NEXT_STEP_BY_STATUS = {
    "empty": "collect_resolution_risk_evidence",
    "clear": "ready_for_resolution_risk_review",
    "watch": "refresh_resolution_risk_evidence",
    "blocked": "block_until_resolution_risk_repaired",
}
BLOCKING_REASON_CODES = (
    "ambiguous_resolution_criteria",
    "unresolved_source_conflict",
)
WATCH_REASON_CODES = (
    "stale_outcome_evidence",
    "stale_source_evidence",
    "close_time_pressure",
)
PASS_REASON_CODE = "resolution_risk_clear"
UNSAFE_TEXT_FRAGMENTS = (
    "li" "ve",
    "trad" "ing",
    "au" "th",
    "wal" "let",
    "or" "der",
    "can" "cel",
    "rep" "lace",
    "pri" "vate" "_" "key",
    "pri" "vate" "-" "key",
    "bro" "ker",
    "submit" "_" "or" "der",
    "can" "cel" "_" "or" "der",
    "sign" "ing",
    "investment" "_" "advice",
    "sec" "ret",
    "tok" "en",
)


@dataclass(frozen=True)
class StrategyRecommendationResolutionRiskTriageConfig:
    config_version: str
    max_evidence_age_hours: Decimal
    close_pressure_window_hours: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "max_evidence_age_hours",
            _normalize_positive_decimal(
                "max_evidence_age_hours",
                self.max_evidence_age_hours,
            ),
        )
        object.__setattr__(
            self,
            "close_pressure_window_hours",
            _normalize_nonnegative_decimal(
                "close_pressure_window_hours",
                self.close_pressure_window_hours,
            ),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyRecommendationResolutionRiskCandidate:
    candidate_id: str
    market_slug: str
    team_key: str
    resolution_criteria: str
    resolution_criteria_ambiguous: bool
    outcome_evidence_at: datetime
    source_evidence_at: datetime
    unresolved_source_conflict: bool
    closes_at: datetime
    severity_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("team_key", self.team_key)
        _require_canonical_string("resolution_criteria", self.resolution_criteria)
        _require_bool(
            "resolution_criteria_ambiguous",
            self.resolution_criteria_ambiguous,
        )
        object.__setattr__(
            self,
            "outcome_evidence_at",
            _as_utc("outcome_evidence_at", self.outcome_evidence_at),
        )
        object.__setattr__(
            self,
            "source_evidence_at",
            _as_utc("source_evidence_at", self.source_evidence_at),
        )
        _require_bool("unresolved_source_conflict", self.unresolved_source_conflict)
        object.__setattr__(self, "closes_at", _as_utc("closes_at", self.closes_at))
        object.__setattr__(
            self,
            "severity_score",
            _normalize_nonnegative_decimal("severity_score", self.severity_score),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyRecommendationResolutionRiskReasonCodeCount:
    reason_code: str
    count: Decimal

    def __post_init__(self) -> None:
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_whole_decimal("count", self.count),
        )


@dataclass(frozen=True)
class StrategyRecommendationResolutionRiskTriageRow:
    candidate_id: str
    market_slug: str
    team_key: str
    status: str
    recommended_next_step: str
    severity_score: Decimal
    outcome_evidence_at: datetime
    source_evidence_at: datetime
    closes_at: datetime
    outcome_evidence_age_hours: Decimal
    source_evidence_age_hours: Decimal
    hours_until_close: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("team_key", self.team_key)
        _require_row_status("status", self.status)
        _require_next_step("recommended_next_step", self.recommended_next_step)
        if self.recommended_next_step != NEXT_STEP_BY_STATUS[self.status]:
            raise ValueError("recommended_next_step must match status")
        object.__setattr__(
            self,
            "severity_score",
            _normalize_nonnegative_decimal("severity_score", self.severity_score),
        )
        object.__setattr__(
            self,
            "outcome_evidence_at",
            _as_utc("outcome_evidence_at", self.outcome_evidence_at),
        )
        object.__setattr__(
            self,
            "source_evidence_at",
            _as_utc("source_evidence_at", self.source_evidence_at),
        )
        object.__setattr__(self, "closes_at", _as_utc("closes_at", self.closes_at))
        for field_name in (
            "outcome_evidence_age_hours",
            "source_evidence_age_hours",
            "hours_until_close",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.status != _status_from_reason_codes(self.reason_codes):
            raise ValueError("status must match reason_codes")
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyRecommendationResolutionRiskTriageReport:
    generated_at: datetime
    config_version: str
    triage_status: str
    recommended_next_step: str
    candidate_count: Decimal
    row_count: Decimal
    clear_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    clear_ratio: Decimal
    watch_ratio: Decimal
    blocked_ratio: Decimal
    reason_code_counts: tuple[StrategyRecommendationResolutionRiskReasonCodeCount, ...]
    rows: tuple[StrategyRecommendationResolutionRiskTriageRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_report_status("triage_status", self.triage_status)
        _require_next_step("recommended_next_step", self.recommended_next_step)
        if self.recommended_next_step != NEXT_STEP_BY_STATUS[self.triage_status]:
            raise ValueError("recommended_next_step must match triage_status")
        for field_name in (
            "candidate_count",
            "row_count",
            "clear_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("clear_ratio", "watch_ratio", "blocked_ratio"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags(self)


def build_strategy_recommendation_resolution_risk_triage_report(
    candidates: Iterable[StrategyRecommendationResolutionRiskCandidate],
    *,
    config: StrategyRecommendationResolutionRiskTriageConfig,
    generated_at: datetime,
) -> StrategyRecommendationResolutionRiskTriageReport:
    """Review candidates for resolution-risk readiness without side effects."""

    if type(config) is not StrategyRecommendationResolutionRiskTriageConfig:
        raise ValueError(
            "config must be a StrategyRecommendationResolutionRiskTriageConfig",
        )
    _require_hard_flags(config)
    normalized_generated_at = _as_utc("generated_at", generated_at)
    normalized_candidates = _normalize_candidates(candidates)
    rows = tuple(
        sorted(
            (
                _row_for_candidate(
                    candidate,
                    config=config,
                    generated_at=normalized_generated_at,
                )
                for candidate in normalized_candidates
            ),
            key=_row_sort_key,
        ),
    )
    reason_code_counts = _reason_code_counts(rows)
    candidate_count = Decimal(len(normalized_candidates))
    clear_count = Decimal(sum(1 for row in rows if row.status == "clear"))
    watch_count = Decimal(sum(1 for row in rows if row.status == "watch"))
    blocked_count = Decimal(sum(1 for row in rows if row.status == "blocked"))
    triage_status = _triage_status(rows)

    return StrategyRecommendationResolutionRiskTriageReport(
        generated_at=normalized_generated_at,
        config_version=config.config_version,
        triage_status=triage_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[triage_status],
        candidate_count=candidate_count,
        row_count=Decimal(len(rows)),
        clear_count=clear_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        clear_ratio=_ratio(clear_count, candidate_count),
        watch_ratio=_ratio(watch_count, candidate_count),
        blocked_ratio=_ratio(blocked_count, candidate_count),
        reason_code_counts=reason_code_counts,
        rows=rows,
    )


def strategy_recommendation_resolution_risk_triage_payload(
    report: StrategyRecommendationResolutionRiskTriageReport,
) -> dict[str, Any]:
    if type(report) is not StrategyRecommendationResolutionRiskTriageReport:
        raise ValueError(
            "report must be a StrategyRecommendationResolutionRiskTriageReport",
        )
    return _payload_value(asdict(report))


def _row_for_candidate(
    candidate: StrategyRecommendationResolutionRiskCandidate,
    *,
    config: StrategyRecommendationResolutionRiskTriageConfig,
    generated_at: datetime,
) -> StrategyRecommendationResolutionRiskTriageRow:
    outcome_age = _hours_between(generated_at, candidate.outcome_evidence_at)
    source_age = _hours_between(generated_at, candidate.source_evidence_at)
    hours_until_close = _hours_between(candidate.closes_at, generated_at)
    reason_codes = _reason_codes_for_candidate(
        candidate,
        outcome_age=outcome_age,
        source_age=source_age,
        hours_until_close=hours_until_close,
        config=config,
    )
    status = _status_from_reason_codes(reason_codes)

    return StrategyRecommendationResolutionRiskTriageRow(
        candidate_id=candidate.candidate_id,
        market_slug=candidate.market_slug,
        team_key=candidate.team_key,
        status=status,
        recommended_next_step=NEXT_STEP_BY_STATUS[status],
        severity_score=candidate.severity_score,
        outcome_evidence_at=candidate.outcome_evidence_at,
        source_evidence_at=candidate.source_evidence_at,
        closes_at=candidate.closes_at,
        outcome_evidence_age_hours=outcome_age,
        source_evidence_age_hours=source_age,
        hours_until_close=hours_until_close,
        reason_codes=reason_codes,
    )


def _reason_codes_for_candidate(
    candidate: StrategyRecommendationResolutionRiskCandidate,
    *,
    outcome_age: Decimal,
    source_age: Decimal,
    hours_until_close: Decimal,
    config: StrategyRecommendationResolutionRiskTriageConfig,
) -> tuple[str, ...]:
    blocking_reasons: list[str] = []
    watch_reasons: list[str] = []

    if candidate.resolution_criteria_ambiguous:
        blocking_reasons.append("ambiguous_resolution_criteria")
    if candidate.unresolved_source_conflict:
        blocking_reasons.append("unresolved_source_conflict")
    if outcome_age > config.max_evidence_age_hours:
        watch_reasons.append("stale_outcome_evidence")
    if source_age > config.max_evidence_age_hours:
        watch_reasons.append("stale_source_evidence")
    if ZERO <= hours_until_close <= config.close_pressure_window_hours:
        watch_reasons.append("close_time_pressure")

    if blocking_reasons:
        return tuple(blocking_reasons)
    if watch_reasons:
        return tuple(watch_reasons)
    return (PASS_REASON_CODE,)


def _reason_code_counts(
    rows: tuple[StrategyRecommendationResolutionRiskTriageRow, ...],
) -> tuple[StrategyRecommendationResolutionRiskReasonCodeCount, ...]:
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        StrategyRecommendationResolutionRiskReasonCodeCount(
            reason_code=reason_code,
            count=Decimal(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        if reason_code != PASS_REASON_CODE
    )


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKING_REASON_CODES for reason_code in reason_codes):
        return "blocked"
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "clear"


def _triage_status(
    rows: tuple[StrategyRecommendationResolutionRiskTriageRow, ...],
) -> str:
    if not rows:
        return "empty"
    if any(row.status == "blocked" for row in rows):
        return "blocked"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "clear"


def _row_sort_key(
    row: StrategyRecommendationResolutionRiskTriageRow,
) -> tuple[int, Decimal, str, str, str]:
    return (
        STATUS_RANK[row.status],
        -row.severity_score,
        row.market_slug,
        row.team_key,
        row.candidate_id,
    )


def _normalize_candidates(
    candidates: Iterable[StrategyRecommendationResolutionRiskCandidate],
) -> tuple[StrategyRecommendationResolutionRiskCandidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        items = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    for candidate in items:
        if type(candidate) is not StrategyRecommendationResolutionRiskCandidate:
            raise ValueError(
                "candidates must contain only "
                "StrategyRecommendationResolutionRiskCandidate values",
            )
    return items


def _normalize_rows(
    rows: Iterable[StrategyRecommendationResolutionRiskTriageRow],
) -> tuple[StrategyRecommendationResolutionRiskTriageRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        items = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in items:
        if type(row) is not StrategyRecommendationResolutionRiskTriageRow:
            raise ValueError(
                "rows must contain only StrategyRecommendationResolutionRiskTriageRow values",
            )
    if len({row.candidate_id for row in items}) != len(items):
        raise ValueError("rows must not contain duplicate candidate_id values")
    return tuple(sorted(items, key=_row_sort_key))


def _normalize_reason_code_counts(
    counts: Iterable[StrategyRecommendationResolutionRiskReasonCodeCount],
) -> tuple[StrategyRecommendationResolutionRiskReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        items = tuple(counts)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for item in items:
        if type(item) is not StrategyRecommendationResolutionRiskReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain only "
                "StrategyRecommendationResolutionRiskReasonCodeCount values",
            )
    if len({item.reason_code for item in items}) != len(items):
        raise ValueError("reason_code_counts must not contain duplicate reason codes")
    return tuple(sorted(items, key=lambda item: (-item.count, item.reason_code)))


def _normalize_reason_codes(field_name: str, values: Iterable[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        items = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if not items:
        raise ValueError(f"{field_name} must contain at least one value")
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} must not contain duplicates")
    allowed = set(BLOCKING_REASON_CODES) | set(WATCH_REASON_CODES) | {PASS_REASON_CODE}
    for item in items:
        _require_canonical_string("reason_code", item)
        if item not in allowed:
            raise ValueError(f"{field_name} must match resolution risk semantics")
    return tuple(items)


def _hours_between(later: datetime, earlier: datetime) -> Decimal:
    delta_seconds = Decimal(str((later - earlier).total_seconds()))
    with localcontext(DECIMAL_CONTEXT):
        return (delta_seconds / Decimal("3600")).quantize(QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO.quantize(QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    _require_decimal(field_name, value)
    return _quantize_decimal(value)


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _normalize_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _normalize_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _normalize_nonnegative_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _normalize_ratio(field_name: str, value: Decimal) -> Decimal:
    value = _normalize_nonnegative_decimal(field_name, value)
    if value > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return value


def _normalize_whole_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _normalize_nonnegative_decimal(field_name, value)
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return value.quantize(COUNT_QUANTUM)


def _normalize_positive_whole_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _normalize_whole_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_decimal(field_name: str, value: Decimal) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_bool(field_name: str, value: bool) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_row_status(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    if value not in ROW_STATUSES:
        raise ValueError(f"{field_name} must be clear, watch, or blocked")


def _require_report_status(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    if value not in REPORT_STATUSES:
        raise ValueError(f"{field_name} must be a known triage status")


def _require_next_step(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    if value not in set(NEXT_STEP_BY_STATUS.values()):
        raise ValueError(f"{field_name} must be a known next step")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must be non-empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must be canonical")
    _reject_unsafe_text(field_name, value)


def _reject_unsafe_text(field_name: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must not contain unsafe surface text")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _validate_report_consistency(
    report: StrategyRecommendationResolutionRiskTriageReport,
) -> None:
    if report.row_count != Decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.candidate_count != report.row_count:
        raise ValueError("candidate_count must match rows")
    if report.clear_count + report.watch_count + report.blocked_count != report.candidate_count:
        raise ValueError("candidate_count must match status counts")
    if report.clear_ratio != _ratio(report.clear_count, report.candidate_count):
        raise ValueError("clear_ratio must match counts")
    if report.watch_ratio != _ratio(report.watch_count, report.candidate_count):
        raise ValueError("watch_ratio must match counts")
    if report.blocked_ratio != _ratio(report.blocked_count, report.candidate_count):
        raise ValueError("blocked_ratio must match counts")
    if report.triage_status != _triage_status(report.rows):
        raise ValueError("triage_status must match rows")
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.triage_status]:
        raise ValueError("recommended_next_step must match triage_status")
    expected_reason_counts = _reason_code_counts(report.rows)
    if report.reason_code_counts != expected_reason_counts:
        raise ValueError("reason_code_counts must match rows")


def _payload_value(value: Any, *, field_name: str | None = None) -> Any:
    if isinstance(value, Decimal):
        if field_name is not None and field_name.endswith("count"):
            return str(value.quantize(COUNT_QUANTUM))
        return str(value)
    if isinstance(value, datetime):
        return _utc_text(value)
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {
            str(key): _payload_value(item, field_name=str(key))
            for key, item in value.items()
        }
    return value


def _utc_text(value: datetime) -> str:
    text = value.astimezone(UTC).isoformat()
    if text.endswith("+00:00"):
        return f"{text[:-6]}Z"
    raise ValueError("datetime must render in UTC")


__all__ = (
    "StrategyRecommendationResolutionRiskCandidate",
    "StrategyRecommendationResolutionRiskReasonCodeCount",
    "StrategyRecommendationResolutionRiskTriageConfig",
    "StrategyRecommendationResolutionRiskTriageReport",
    "StrategyRecommendationResolutionRiskTriageRow",
    "build_strategy_recommendation_resolution_risk_triage_report",
    "strategy_recommendation_resolution_risk_triage_payload",
)
