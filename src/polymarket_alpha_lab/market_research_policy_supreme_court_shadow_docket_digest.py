"""Pure Supreme Court shadow-docket timing screen digest."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import re
from typing import Any


SHADOW_DOCKET_REASON_CODES = (
    "shadow_docket_inventory_empty",
    "shadow_docket_emergency_application_pending",
    "shadow_docket_administrative_stay_active",
    "shadow_docket_expedited_response_requested",
    "shadow_docket_market_deadline_imminent",
    "shadow_docket_court_signal_near_market_deadline",
    "shadow_docket_court_signal_after_market_deadline",
    "shadow_docket_no_scheduled_court_signal",
    "shadow_docket_stale_observation",
    "shadow_docket_timing_low_risk",
)

RISK_CODES = ("high_risk", "watch", "low")
DIGEST_STATUSES = ("empty", "high_risk", "watch", "low")

COUNT_QUANTUM = Decimal("1")
HOUR_QUANTUM = Decimal("0.000001")
SCORE_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_SCORE = Decimal("0.000000")
ZERO_HOURS = Decimal("0.000000")
DEFAULT_HIGH_RISK_SCORE_THRESHOLD = Decimal("7.000000")
DEFAULT_WATCH_RISK_SCORE_THRESHOLD = Decimal("3.000000")
DEFAULT_MARKET_DEADLINE_IMMINENT_HOURS = Decimal("24.000000")
DEFAULT_COURT_SIGNAL_HIGH_RISK_WINDOW_HOURS = Decimal("72.000000")
DEFAULT_STALE_OBSERVATION_HOURS = Decimal("168.000000")

_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_HOUR_MICROSECONDS = Decimal("3600000000")
_DAY_MICROSECONDS = Decimal("86400000000")
_SECOND_MICROSECONDS = Decimal("1000000")
_MARKET_SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{1,160}[a-z0-9]$")
_PAPER_SOURCE_PREFIX = "paper:"
_RISK_RANK = {"high_risk": 0, "watch": 1, "low": 2}
_SENSITIVE_MARKERS = (
    "api_key",
    "password",
    "token",
    "private" "_key",
    "bearer",
)


@dataclass(frozen=True)
class SupremeCourtShadowDocketMarketObservation:
    market_slug: str
    case_label: str
    question: str
    observed_at: datetime
    market_deadline_at: datetime
    court_signal_at: datetime | None
    emergency_application_pending: bool
    administrative_stay_active: bool
    expedited_response_requested: bool
    source_label: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_market_slug("market_slug", self.market_slug)
        object.__setattr__(
            self,
            "case_label",
            _normalize_text("case_label", self.case_label, max_length=240),
        )
        object.__setattr__(
            self,
            "question",
            _normalize_text("question", self.question, max_length=320),
        )
        observed_at = _as_utc("observed_at", self.observed_at)
        market_deadline_at = _as_utc("market_deadline_at", self.market_deadline_at)
        object.__setattr__(self, "observed_at", observed_at)
        object.__setattr__(self, "market_deadline_at", market_deadline_at)
        if market_deadline_at <= observed_at:
            raise ValueError("market_deadline_at must be after observed_at")
        if self.court_signal_at is not None:
            court_signal_at = _as_utc("court_signal_at", self.court_signal_at)
            if court_signal_at < observed_at:
                raise ValueError("court_signal_at must not be before observed_at")
            object.__setattr__(self, "court_signal_at", court_signal_at)
        for field_name in (
            "emergency_application_pending",
            "administrative_stay_active",
            "expedited_response_requested",
        ):
            if type(getattr(self, field_name)) is not bool:
                raise ValueError(f"{field_name} must be a bool")
        object.__setattr__(
            self,
            "source_label",
            _normalize_source_label(self.source_label),
        )
        _require_hard_flags("SupremeCourtShadowDocketMarketObservation", self)


@dataclass(frozen=True)
class SupremeCourtShadowDocketMarketRiskRow:
    market_slug: str
    case_label: str
    question: str
    observed_at: datetime
    market_deadline_at: datetime
    court_signal_at: datetime | None
    source_label: str
    hours_until_market_deadline: Decimal
    court_signal_to_market_deadline_hours: Decimal
    timing_risk_score: Decimal
    risk_code: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_market_slug("market_slug", self.market_slug)
        object.__setattr__(
            self,
            "case_label",
            _normalize_text("case_label", self.case_label, max_length=240),
        )
        object.__setattr__(
            self,
            "question",
            _normalize_text("question", self.question, max_length=320),
        )
        observed_at = _as_utc("observed_at", self.observed_at)
        market_deadline_at = _as_utc("market_deadline_at", self.market_deadline_at)
        object.__setattr__(self, "observed_at", observed_at)
        object.__setattr__(self, "market_deadline_at", market_deadline_at)
        if market_deadline_at <= observed_at:
            raise ValueError("market_deadline_at must be after observed_at")
        if self.court_signal_at is not None:
            object.__setattr__(
                self,
                "court_signal_at",
                _as_utc("court_signal_at", self.court_signal_at),
            )
        object.__setattr__(self, "source_label", _normalize_source_label(self.source_label))
        object.__setattr__(
            self,
            "hours_until_market_deadline",
            _normalize_hours(
                "hours_until_market_deadline",
                self.hours_until_market_deadline,
                allow_negative=False,
            ),
        )
        object.__setattr__(
            self,
            "court_signal_to_market_deadline_hours",
            _normalize_hours(
                "court_signal_to_market_deadline_hours",
                self.court_signal_to_market_deadline_hours,
                allow_negative=True,
            ),
        )
        object.__setattr__(
            self,
            "timing_risk_score",
            _normalize_score("timing_risk_score", self.timing_risk_score),
        )
        _require_member("risk_code", self.risk_code, RISK_CODES)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_market_row(self)
        _require_hard_flags("SupremeCourtShadowDocketMarketRiskRow", self)


@dataclass(frozen=True)
class SupremeCourtShadowDocketTimingRiskDigest:
    generated_at: datetime
    digest_status: str
    market_count: Decimal
    high_risk_market_count: Decimal
    watch_market_count: Decimal
    low_risk_market_count: Decimal
    stale_observation_count: Decimal
    unresolved_court_signal_count: Decimal
    high_risk_score_threshold: Decimal
    watch_risk_score_threshold: Decimal
    market_deadline_imminent_hours: Decimal
    court_signal_high_risk_window_hours: Decimal
    stale_observation_hours: Decimal
    max_timing_risk_score: Decimal
    average_timing_risk_score: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    summary: tuple[str, ...]
    market_rows: tuple[SupremeCourtShadowDocketMarketRiskRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_member("digest_status", self.digest_status, DIGEST_STATUSES)
        for field_name in (
            "market_count",
            "high_risk_market_count",
            "watch_market_count",
            "low_risk_market_count",
            "stale_observation_count",
            "unresolved_court_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "high_risk_score_threshold",
            "watch_risk_score_threshold",
            "market_deadline_imminent_hours",
            "court_signal_high_risk_window_hours",
            "stale_observation_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        _require_thresholds(
            self.high_risk_score_threshold,
            self.watch_risk_score_threshold,
        )
        object.__setattr__(
            self,
            "max_timing_risk_score",
            _normalize_score("max_timing_risk_score", self.max_timing_risk_score),
        )
        object.__setattr__(
            self,
            "average_timing_risk_score",
            _normalize_score(
                "average_timing_risk_score",
                self.average_timing_risk_score,
            ),
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "summary", _normalize_summary(self.summary))
        object.__setattr__(self, "market_rows", _normalize_market_rows(self.market_rows))
        _validate_digest(self)
        _require_hard_flags("SupremeCourtShadowDocketTimingRiskDigest", self)


def build_market_research_policy_supreme_court_shadow_docket_digest(
    observations: list[SupremeCourtShadowDocketMarketObservation]
    | tuple[SupremeCourtShadowDocketMarketObservation, ...],
    *,
    generated_at: datetime,
    high_risk_score_threshold: Decimal = DEFAULT_HIGH_RISK_SCORE_THRESHOLD,
    watch_risk_score_threshold: Decimal = DEFAULT_WATCH_RISK_SCORE_THRESHOLD,
    market_deadline_imminent_hours: Decimal = DEFAULT_MARKET_DEADLINE_IMMINENT_HOURS,
    court_signal_high_risk_window_hours: Decimal = (
        DEFAULT_COURT_SIGNAL_HIGH_RISK_WINDOW_HOURS
    ),
    stale_observation_hours: Decimal = DEFAULT_STALE_OBSERVATION_HOURS,
) -> SupremeCourtShadowDocketTimingRiskDigest:
    generated_at_utc = _as_utc("generated_at", generated_at)
    high_threshold = _normalize_positive_decimal(
        "high_risk_score_threshold",
        high_risk_score_threshold,
    )
    watch_threshold = _normalize_positive_decimal(
        "watch_risk_score_threshold",
        watch_risk_score_threshold,
    )
    imminent_hours = _normalize_positive_decimal(
        "market_deadline_imminent_hours",
        market_deadline_imminent_hours,
    )
    court_window_hours = _normalize_positive_decimal(
        "court_signal_high_risk_window_hours",
        court_signal_high_risk_window_hours,
    )
    stale_hours = _normalize_positive_decimal(
        "stale_observation_hours",
        stale_observation_hours,
    )
    _require_thresholds(high_threshold, watch_threshold)
    normalized_observations = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (
                _market_row(
                    observation,
                    generated_at=generated_at_utc,
                    high_risk_score_threshold=high_threshold,
                    watch_risk_score_threshold=watch_threshold,
                    market_deadline_imminent_hours=imminent_hours,
                    court_signal_high_risk_window_hours=court_window_hours,
                    stale_observation_hours=stale_hours,
                )
                for observation in normalized_observations
            ),
            key=_market_row_sort_key,
        ),
    )
    reason_code_counts = _reason_code_counts(rows)
    return SupremeCourtShadowDocketTimingRiskDigest(
        generated_at=generated_at_utc,
        digest_status=_digest_status(rows),
        market_count=_count(len(rows)),
        high_risk_market_count=_risk_count(rows, "high_risk"),
        watch_market_count=_risk_count(rows, "watch"),
        low_risk_market_count=_risk_count(rows, "low"),
        stale_observation_count=_rows_with_reason(
            rows,
            "shadow_docket_stale_observation",
        ),
        unresolved_court_signal_count=_rows_with_reason(
            rows,
            "shadow_docket_no_scheduled_court_signal",
        ),
        high_risk_score_threshold=high_threshold,
        watch_risk_score_threshold=watch_threshold,
        market_deadline_imminent_hours=imminent_hours,
        court_signal_high_risk_window_hours=court_window_hours,
        stale_observation_hours=stale_hours,
        max_timing_risk_score=_max_score(rows),
        average_timing_risk_score=_average_score(rows),
        reason_codes=tuple(reason_code for reason_code, _value in reason_code_counts),
        reason_code_counts=reason_code_counts,
        summary=_summary(rows),
        market_rows=rows,
    )


def market_research_policy_supreme_court_shadow_docket_digest_payload(
    digest: SupremeCourtShadowDocketTimingRiskDigest,
) -> dict[str, Any]:
    if type(digest) is not SupremeCourtShadowDocketTimingRiskDigest:
        raise ValueError("digest must be a SupremeCourtShadowDocketTimingRiskDigest")
    _require_hard_flags("digest", digest)
    return _json_ready(digest)


def _normalize_observations(
    observations: list[SupremeCourtShadowDocketMarketObservation]
    | tuple[SupremeCourtShadowDocketMarketObservation, ...],
) -> tuple[SupremeCourtShadowDocketMarketObservation, ...]:
    if type(observations) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    normalized = tuple(observations)
    seen: set[str] = set()
    for observation in normalized:
        if type(observation) is not SupremeCourtShadowDocketMarketObservation:
            raise ValueError(
                "observations must contain SupremeCourtShadowDocketMarketObservation values",
            )
        _require_hard_flags("observation", observation)
        if observation.market_slug in seen:
            raise ValueError("observations must not contain duplicate market slugs")
        seen.add(observation.market_slug)
    return normalized


def _market_row(
    observation: SupremeCourtShadowDocketMarketObservation,
    *,
    generated_at: datetime,
    high_risk_score_threshold: Decimal,
    watch_risk_score_threshold: Decimal,
    market_deadline_imminent_hours: Decimal,
    court_signal_high_risk_window_hours: Decimal,
    stale_observation_hours: Decimal,
) -> SupremeCourtShadowDocketMarketRiskRow:
    if observation.observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    hours_until_deadline = _datetime_delta_hours(
        observation.observed_at,
        observation.market_deadline_at,
    )
    court_signal_gap = ZERO_HOURS
    if observation.court_signal_at is not None:
        court_signal_gap = _datetime_delta_hours(
            observation.court_signal_at,
            observation.market_deadline_at,
        )
    reason_codes = _row_reason_codes(
        observation=observation,
        generated_at=generated_at,
        hours_until_market_deadline=hours_until_deadline,
        court_signal_to_market_deadline_hours=court_signal_gap,
        market_deadline_imminent_hours=market_deadline_imminent_hours,
        court_signal_high_risk_window_hours=court_signal_high_risk_window_hours,
        stale_observation_hours=stale_observation_hours,
    )
    score = _score(reason_codes)
    return SupremeCourtShadowDocketMarketRiskRow(
        market_slug=observation.market_slug,
        case_label=observation.case_label,
        question=observation.question,
        observed_at=observation.observed_at,
        market_deadline_at=observation.market_deadline_at,
        court_signal_at=observation.court_signal_at,
        source_label=observation.source_label,
        hours_until_market_deadline=hours_until_deadline,
        court_signal_to_market_deadline_hours=court_signal_gap,
        timing_risk_score=score,
        risk_code=_risk_code(
            score,
            high_risk_score_threshold=high_risk_score_threshold,
            watch_risk_score_threshold=watch_risk_score_threshold,
        ),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    observation: SupremeCourtShadowDocketMarketObservation,
    generated_at: datetime,
    hours_until_market_deadline: Decimal,
    court_signal_to_market_deadline_hours: Decimal,
    market_deadline_imminent_hours: Decimal,
    court_signal_high_risk_window_hours: Decimal,
    stale_observation_hours: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if observation.emergency_application_pending:
        reason_codes.append("shadow_docket_emergency_application_pending")
    if observation.administrative_stay_active:
        reason_codes.append("shadow_docket_administrative_stay_active")
    if observation.expedited_response_requested:
        reason_codes.append("shadow_docket_expedited_response_requested")
    if hours_until_market_deadline <= market_deadline_imminent_hours:
        reason_codes.append("shadow_docket_market_deadline_imminent")
    if observation.court_signal_at is None:
        reason_codes.append("shadow_docket_no_scheduled_court_signal")
    elif court_signal_to_market_deadline_hours < ZERO_HOURS:
        reason_codes.append("shadow_docket_court_signal_after_market_deadline")
    elif court_signal_to_market_deadline_hours <= court_signal_high_risk_window_hours:
        reason_codes.append("shadow_docket_court_signal_near_market_deadline")
    if _datetime_delta_hours(observation.observed_at, generated_at) > stale_observation_hours:
        reason_codes.append("shadow_docket_stale_observation")
    if not reason_codes:
        reason_codes.append("shadow_docket_timing_low_risk")
    return _normalize_reason_codes(reason_codes)


def _score(reason_codes: tuple[str, ...]) -> Decimal:
    score = ZERO_SCORE
    score_values = {
        "shadow_docket_emergency_application_pending": Decimal("4.000000"),
        "shadow_docket_administrative_stay_active": Decimal("3.000000"),
        "shadow_docket_expedited_response_requested": Decimal("2.000000"),
        "shadow_docket_market_deadline_imminent": Decimal("3.000000"),
        "shadow_docket_court_signal_near_market_deadline": Decimal("3.000000"),
        "shadow_docket_court_signal_after_market_deadline": Decimal("2.000000"),
        "shadow_docket_no_scheduled_court_signal": Decimal("1.000000"),
        "shadow_docket_stale_observation": Decimal("1.000000"),
        "shadow_docket_inventory_empty": Decimal("0.000000"),
        "shadow_docket_timing_low_risk": Decimal("0.000000"),
    }
    for reason_code in reason_codes:
        score += score_values[reason_code]
    return _normalize_score("timing_risk_score", score)


def _risk_code(
    score: Decimal,
    *,
    high_risk_score_threshold: Decimal,
    watch_risk_score_threshold: Decimal,
) -> str:
    if score >= high_risk_score_threshold:
        return "high_risk"
    if score >= watch_risk_score_threshold:
        return "watch"
    return "low"


def _market_row_sort_key(
    row: SupremeCourtShadowDocketMarketRiskRow,
) -> tuple[int, Decimal, datetime, str]:
    return (
        _RISK_RANK[row.risk_code],
        -row.timing_risk_score,
        row.market_deadline_at,
        row.market_slug,
    )


def _digest_status(rows: tuple[SupremeCourtShadowDocketMarketRiskRow, ...]) -> str:
    if not rows:
        return "empty"
    if any(row.risk_code == "high_risk" for row in rows):
        return "high_risk"
    if any(row.risk_code == "watch" for row in rows):
        return "watch"
    return "low"


def _risk_count(
    rows: tuple[SupremeCourtShadowDocketMarketRiskRow, ...],
    risk_code: str,
) -> Decimal:
    _require_member("risk_code", risk_code, RISK_CODES)
    return _count(sum(1 for row in rows if row.risk_code == risk_code))


def _rows_with_reason(
    rows: tuple[SupremeCourtShadowDocketMarketRiskRow, ...],
    reason_code: str,
) -> Decimal:
    _require_member("reason_code", reason_code, SHADOW_DOCKET_REASON_CODES)
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _reason_code_counts(
    rows: tuple[SupremeCourtShadowDocketMarketRiskRow, ...],
) -> tuple[tuple[str, Decimal], ...]:
    if not rows:
        return (("shadow_docket_inventory_empty", _count(1)),)
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO_COUNT) + _count(1)
    return tuple(
        (reason_code, counts[reason_code])
        for reason_code in SHADOW_DOCKET_REASON_CODES
        if reason_code in counts
    )


def _max_score(rows: tuple[SupremeCourtShadowDocketMarketRiskRow, ...]) -> Decimal:
    if not rows:
        return ZERO_SCORE
    return _normalize_score(
        "max_timing_risk_score",
        max(row.timing_risk_score for row in rows),
    )


def _average_score(rows: tuple[SupremeCourtShadowDocketMarketRiskRow, ...]) -> Decimal:
    if not rows:
        return ZERO_SCORE
    total = ZERO_SCORE
    for row in rows:
        total += row.timing_risk_score
    with localcontext(_CONTEXT):
        return (total / Decimal(len(rows))).quantize(SCORE_QUANTUM)


def _summary(rows: tuple[SupremeCourtShadowDocketMarketRiskRow, ...]) -> tuple[str, ...]:
    if not rows:
        return ("Supreme Court shadow-docket timing inventory is empty",)
    status = _digest_status(rows)
    if status == "high_risk":
        return ("Supreme Court shadow-docket timing screen has high-risk markets",)
    if status == "watch":
        return ("Supreme Court shadow-docket timing screen has watch markets",)
    return ("Supreme Court shadow-docket timing screen has low timing risk",)


def _validate_market_row(row: SupremeCourtShadowDocketMarketRiskRow) -> None:
    expected_hours = _datetime_delta_hours(row.observed_at, row.market_deadline_at)
    if row.hours_until_market_deadline != expected_hours:
        raise ValueError("hours_until_market_deadline must match datetimes")
    expected_gap = ZERO_HOURS
    if row.court_signal_at is not None:
        expected_gap = _datetime_delta_hours(row.court_signal_at, row.market_deadline_at)
    if row.court_signal_to_market_deadline_hours != expected_gap:
        raise ValueError("court_signal_to_market_deadline_hours must match datetimes")


def _validate_digest(report: SupremeCourtShadowDocketTimingRiskDigest) -> None:
    if report.market_count != _count(len(report.market_rows)):
        raise ValueError("market_count must match market rows")
    if report.high_risk_market_count != _risk_count(report.market_rows, "high_risk"):
        raise ValueError("high_risk_market_count must match market rows")
    if report.watch_market_count != _risk_count(report.market_rows, "watch"):
        raise ValueError("watch_market_count must match market rows")
    if report.low_risk_market_count != _risk_count(report.market_rows, "low"):
        raise ValueError("low_risk_market_count must match market rows")
    if report.stale_observation_count != _rows_with_reason(
        report.market_rows,
        "shadow_docket_stale_observation",
    ):
        raise ValueError("stale_observation_count must match market rows")
    if report.unresolved_court_signal_count != _rows_with_reason(
        report.market_rows,
        "shadow_docket_no_scheduled_court_signal",
    ):
        raise ValueError("unresolved_court_signal_count must match market rows")
    if report.digest_status != _digest_status(report.market_rows):
        raise ValueError("digest_status must match market rows")
    if report.max_timing_risk_score != _max_score(report.market_rows):
        raise ValueError("max_timing_risk_score must match market rows")
    if report.average_timing_risk_score != _average_score(report.market_rows):
        raise ValueError("average_timing_risk_score must match market rows")
    expected_counts = _reason_code_counts(report.market_rows)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match market rows")
    if report.reason_codes != tuple(reason_code for reason_code, _value in expected_counts):
        raise ValueError("reason_codes must match reason_code_counts")
    if report.summary != _summary(report.market_rows):
        raise ValueError("summary must match market rows")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _datetime_delta_hours(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    microseconds = (
        Decimal(delta.days) * _DAY_MICROSECONDS
        + Decimal(delta.seconds) * _SECOND_MICROSECONDS
        + Decimal(delta.microseconds)
    )
    with localcontext(_CONTEXT):
        return (microseconds / _HOUR_MICROSECONDS).quantize(HOUR_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.quantize(COUNT_QUANTUM):
        raise ValueError(f"{field_name} must be an integral Decimal count")
    return value


def _normalize_hours(
    field_name: str,
    value: object,
    *,
    allow_negative: bool,
) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(HOUR_QUANTUM)
    if not allow_negative and normalized < ZERO_HOURS:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_score(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(SCORE_QUANTUM)
    if normalized < ZERO_SCORE:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(SCORE_QUANTUM)
    if normalized <= ZERO_SCORE:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_thresholds(high_threshold: Decimal, watch_threshold: Decimal) -> None:
    if watch_threshold >= high_threshold:
        raise ValueError("watch_risk_score_threshold must be less than high threshold")


def _require_market_slug(field_name: str, value: object) -> None:
    if type(value) is not str or _MARKET_SLUG_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a lowercase market slug")


def _normalize_text(field_name: str, value: object, *, max_length: int) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    normalized = " ".join(value.strip().split())
    if normalized == "":
        raise ValueError(f"{field_name} must be non-empty")
    if len(normalized) > max_length:
        raise ValueError(f"{field_name} is too long")
    lowered = normalized.lower()
    for marker in _SENSITIVE_MARKERS:
        if marker in lowered:
            raise ValueError(f"{field_name} must not contain sensitive markers")
    return normalized


def _normalize_source_label(value: object) -> str:
    normalized = _normalize_text("source_label", value, max_length=180)
    if not normalized.startswith(_PAPER_SOURCE_PREFIX):
        raise ValueError("source_label must start with paper:")
    return normalized


def _require_member(field_name: str, value: object, members: tuple[str, ...]) -> None:
    if value not in members:
        raise ValueError(f"{field_name} must be one of {members}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must not contain duplicates")
    for reason_code in reason_codes:
        _require_member("reason_codes", reason_code, SHADOW_DOCKET_REASON_CODES)
    return tuple(
        reason_code
        for reason_code in SHADOW_DOCKET_REASON_CODES
        if reason_code in reason_codes
    )


def _normalize_reason_code_counts(
    value: object,
) -> tuple[tuple[str, Decimal], ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    seen: set[str] = set()
    normalized: list[tuple[str, Decimal]] = []
    for item in counts:
        if type(item) not in (list, tuple) or len(item) != 2:
            raise ValueError("reason_code_counts entries must be reason/count pairs")
        reason_code, count_value = item
        _require_member("reason_code_counts", reason_code, SHADOW_DOCKET_REASON_CODES)
        if reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicates")
        seen.add(reason_code)
        normalized.append((reason_code, _normalize_count("reason_code_counts", count_value)))
    return tuple(
        (reason_code, count_value)
        for reason_code in SHADOW_DOCKET_REASON_CODES
        for item_reason_code, count_value in normalized
        if item_reason_code == reason_code
    )


def _normalize_summary(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("summary must be a list or tuple")
    summary = tuple(value)
    for item in summary:
        if type(item) is not str or not item.startswith("Supreme Court shadow-docket"):
            raise ValueError("summary values must use Supreme Court shadow-docket wording")
    return summary


def _normalize_market_rows(
    value: object,
) -> tuple[SupremeCourtShadowDocketMarketRiskRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("market_rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not SupremeCourtShadowDocketMarketRiskRow:
            raise ValueError("market_rows must contain SupremeCourtShadowDocketMarketRiskRow")
    if rows != tuple(sorted(rows, key=_market_row_sort_key)):
        raise ValueError("market_rows must be sorted deterministically")
    return rows


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, datetime):
        text = _as_utc("datetime", value).isoformat()
        if text.endswith("+00:00"):
            return f"{text[:-6]}Z"
        return text
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if isinstance(value, float):
        raise ValueError("payload value must not be a float")
    if isinstance(value, (str, bool)):
        return value
    if isinstance(value, dict):
        for key in value:
            if type(key) is not str:
                raise ValueError("payload object keys must be strings")
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("shadow-docket digest values must be payload serializable")


__all__ = (
    "SHADOW_DOCKET_REASON_CODES",
    "SupremeCourtShadowDocketMarketObservation",
    "SupremeCourtShadowDocketMarketRiskRow",
    "SupremeCourtShadowDocketTimingRiskDigest",
    "build_market_research_policy_supreme_court_shadow_docket_digest",
    "market_research_policy_supreme_court_shadow_docket_digest_payload",
)
