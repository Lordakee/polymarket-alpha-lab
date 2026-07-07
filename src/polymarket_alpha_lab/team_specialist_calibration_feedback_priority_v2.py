"""Readonly Decimal priority report for specialist calibration feedback."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json


DEFAULT_TEAM_SPECIALIST_CALIBRATION_FEEDBACK_PRIORITY_V2_CONFIG_VERSION = (
    "team-specialist-calibration-feedback-priority-v2"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

PRIORITY_TIERS = ("high", "medium", "low")
ROW_STATUSES = ("pass", "watch", "block")
REPORT_STATUSES = ("empty", "pass", "watch", "block")
ROW_REASON_CODES = (
    "calibration_gap_high",
    "calibration_gap_medium",
    "calibration_gap_low",
    "miscalibration_rate_high",
    "miscalibration_rate_watch",
    "miscalibration_rate_clear",
    "probability_error_high",
    "probability_error_watch",
    "probability_error_clear",
    "unresolved_feedback_block",
    "unresolved_feedback_watch",
    "unresolved_feedback_clear",
    "feedback_stale",
    "forecast_outcome_gap_open",
    "forecast_outcome_gap_closed",
)
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)

__all__ = (
    "DEFAULT_TEAM_SPECIALIST_CALIBRATION_FEEDBACK_PRIORITY_V2_CONFIG_VERSION",
    "TeamSpecialistCalibrationFeedbackPriorityV2Config",
    "TeamSpecialistCalibrationFeedbackPriorityV2Input",
    "TeamSpecialistCalibrationFeedbackPriorityV2Row",
    "TeamSpecialistCalibrationFeedbackPriorityV2Report",
    "TeamSpecialistCalibrationFeedbackReasonCodeCount",
    "build_team_specialist_calibration_feedback_priority_v2",
)


@dataclass(frozen=True)
class TeamSpecialistCalibrationFeedbackPriorityV2Config:
    config_version: str = (
        DEFAULT_TEAM_SPECIALIST_CALIBRATION_FEEDBACK_PRIORITY_V2_CONFIG_VERSION
    )
    miscalibrated_rate_weight: Decimal = Decimal("0.450000")
    probability_error_weight: Decimal = Decimal("0.350000")
    unresolved_feedback_weight: Decimal = Decimal("0.100000")
    feedback_staleness_weight: Decimal = Decimal("0.100000")
    max_unresolved_feedback_count: Decimal = Decimal("5")
    stale_feedback_after_seconds: Decimal = Decimal("86400.000000")
    high_priority_floor: Decimal = Decimal("0.700000")
    medium_priority_floor: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_non_empty_string("config_version", self.config_version),
        )
        for field_name in (
            "miscalibrated_rate_weight",
            "probability_error_weight",
            "unresolved_feedback_weight",
            "feedback_staleness_weight",
            "high_priority_floor",
            "medium_priority_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_unresolved_feedback_count",
            _normalize_positive_integral_decimal(
                "max_unresolved_feedback_count",
                self.max_unresolved_feedback_count,
            ),
        )
        object.__setattr__(
            self,
            "stale_feedback_after_seconds",
            _normalize_positive_decimal(
                "stale_feedback_after_seconds",
                self.stale_feedback_after_seconds,
            ),
        )
        _validate_config(self)
        _require_hard_flags("TeamSpecialistCalibrationFeedbackPriorityV2Config", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistCalibrationFeedbackPriorityV2Config",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistCalibrationFeedbackPriorityV2Input:
    team_id: str
    domain: str
    forecast_count: Decimal
    resolved_count: Decimal
    miscalibrated_count: Decimal
    average_probability_error: Decimal
    latest_feedback_at: datetime
    unresolved_feedback_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("team_id", "domain"):
            object.__setattr__(
                self,
                field_name,
                _require_non_empty_string(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "forecast_count",
            "resolved_count",
            "miscalibrated_count",
            "unresolved_feedback_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "average_probability_error",
            _normalize_ratio(
                "average_probability_error",
                self.average_probability_error,
            ),
        )
        object.__setattr__(
            self,
            "latest_feedback_at",
            _as_utc("latest_feedback_at", self.latest_feedback_at),
        )
        _validate_count_consistency(
            forecast_count=self.forecast_count,
            resolved_count=self.resolved_count,
            miscalibrated_count=self.miscalibrated_count,
        )
        _require_hard_flags("TeamSpecialistCalibrationFeedbackPriorityV2Input", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistCalibrationFeedbackPriorityV2Input",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistCalibrationFeedbackPriorityV2Row:
    rank: Decimal
    team_id: str
    domain: str
    forecast_count: Decimal
    resolved_count: Decimal
    miscalibrated_count: Decimal
    average_probability_error: Decimal
    latest_feedback_at: datetime
    unresolved_feedback_count: Decimal
    calibration_gap_score: Decimal
    feedback_age_seconds: Decimal
    priority_tier: str
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "rank",
            _normalize_positive_integral_decimal("rank", self.rank),
        )
        for field_name in ("team_id", "domain"):
            object.__setattr__(
                self,
                field_name,
                _require_non_empty_string(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "forecast_count",
            "resolved_count",
            "miscalibrated_count",
            "unresolved_feedback_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "average_probability_error",
            _normalize_ratio(
                "average_probability_error",
                self.average_probability_error,
            ),
        )
        object.__setattr__(
            self,
            "latest_feedback_at",
            _as_utc("latest_feedback_at", self.latest_feedback_at),
        )
        object.__setattr__(
            self,
            "calibration_gap_score",
            _normalize_ratio("calibration_gap_score", self.calibration_gap_score),
        )
        object.__setattr__(
            self,
            "feedback_age_seconds",
            _normalize_nonnegative_decimal(
                "feedback_age_seconds",
                self.feedback_age_seconds,
            ),
        )
        _require_priority_tier("priority_tier", self.priority_tier)
        _require_row_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_count_consistency(
            forecast_count=self.forecast_count,
            resolved_count=self.resolved_count,
            miscalibrated_count=self.miscalibrated_count,
        )
        _validate_row_consistency(self)
        _require_hard_flags("TeamSpecialistCalibrationFeedbackPriorityV2Row", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistCalibrationFeedbackPriorityV2Row",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistCalibrationFeedbackReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "reason_code",
            _require_reason_code("reason_code", self.reason_code),
        )
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_integral_decimal("count", self.count),
        )
        _require_hard_flags("TeamSpecialistCalibrationFeedbackReasonCodeCount", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistCalibrationFeedbackReasonCodeCount",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistCalibrationFeedbackPriorityV2Report:
    generated_at: datetime
    config_version: str
    report_status: str
    team_count: Decimal
    high_priority_count: Decimal
    medium_priority_count: Decimal
    low_priority_count: Decimal
    blocked_feedback_count: Decimal
    stale_feedback_count: Decimal
    max_calibration_gap_score: Decimal
    rows: tuple[TeamSpecialistCalibrationFeedbackPriorityV2Row, ...]
    reason_code_counts: tuple[TeamSpecialistCalibrationFeedbackReasonCodeCount, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_non_empty_string("config_version", self.config_version),
        )
        _require_report_status("report_status", self.report_status)
        for field_name in (
            "team_count",
            "high_priority_count",
            "medium_priority_count",
            "low_priority_count",
            "blocked_feedback_count",
            "stale_feedback_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "max_calibration_gap_score",
            _normalize_ratio(
                "max_calibration_gap_score",
                self.max_calibration_gap_score,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("TeamSpecialistCalibrationFeedbackPriorityV2Report", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistCalibrationFeedbackPriorityV2Report",
            _payload_value(asdict(self)),
        )
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload(
            "TeamSpecialistCalibrationFeedbackPriorityV2Report.payload",
            payload,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_team_specialist_calibration_feedback_priority_v2(
    feedback_items: object,
    *,
    config: TeamSpecialistCalibrationFeedbackPriorityV2Config | None = None,
    generated_at: datetime,
) -> TeamSpecialistCalibrationFeedbackPriorityV2Report:
    if config is None:
        config = TeamSpecialistCalibrationFeedbackPriorityV2Config()
    if type(config) is not TeamSpecialistCalibrationFeedbackPriorityV2Config:
        raise ValueError(
            "config must be a TeamSpecialistCalibrationFeedbackPriorityV2Config",
        )
    _require_hard_flags("TeamSpecialistCalibrationFeedbackPriorityV2Config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    items = _normalize_feedback_items(feedback_items)
    for item in items:
        if item.latest_feedback_at > generated_at_utc:
            raise ValueError("latest_feedback_at must not be after generated_at")
    sorted_items = _sorted_items(items, generated_at_utc, config)
    rows = tuple(
        _row_for_item(
            rank=Decimal(index).quantize(COUNT_QUANT),
            item=item,
            config=config,
            generated_at=generated_at_utc,
        )
        for index, item in enumerate(sorted_items, start=1)
    )
    values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "report_status": _report_status(rows),
        "team_count": Decimal(len(rows)).quantize(COUNT_QUANT),
        "high_priority_count": _tier_count(rows, "high"),
        "medium_priority_count": _tier_count(rows, "medium"),
        "low_priority_count": _tier_count(rows, "low"),
        "blocked_feedback_count": _status_count(rows, "block"),
        "stale_feedback_count": _stale_count(rows, config),
        "max_calibration_gap_score": _max_calibration_gap_score(rows),
        "rows": rows,
        "reason_code_counts": _reason_code_counts(rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _derived_validation_digest(values)
    return TeamSpecialistCalibrationFeedbackPriorityV2Report(**values)


def _sorted_items(
    items: tuple[TeamSpecialistCalibrationFeedbackPriorityV2Input, ...],
    generated_at: datetime,
    config: TeamSpecialistCalibrationFeedbackPriorityV2Config,
) -> tuple[TeamSpecialistCalibrationFeedbackPriorityV2Input, ...]:
    return tuple(
        sorted(
            items,
            key=lambda item: (
                -_calibration_gap_score(item, generated_at, config),
                -_feedback_age_seconds(generated_at, item.latest_feedback_at),
                item.team_id,
                item.domain,
            ),
        ),
    )


def _row_for_item(
    *,
    rank: Decimal,
    item: TeamSpecialistCalibrationFeedbackPriorityV2Input,
    config: TeamSpecialistCalibrationFeedbackPriorityV2Config,
    generated_at: datetime,
) -> TeamSpecialistCalibrationFeedbackPriorityV2Row:
    feedback_age_seconds = _feedback_age_seconds(generated_at, item.latest_feedback_at)
    calibration_gap_score = _calibration_gap_score(item, generated_at, config)
    priority_tier = _priority_tier(calibration_gap_score, config)
    status = _status_for_priority_tier(priority_tier)
    return TeamSpecialistCalibrationFeedbackPriorityV2Row(
        rank=rank,
        team_id=item.team_id,
        domain=item.domain,
        forecast_count=item.forecast_count,
        resolved_count=item.resolved_count,
        miscalibrated_count=item.miscalibrated_count,
        average_probability_error=item.average_probability_error,
        latest_feedback_at=item.latest_feedback_at,
        unresolved_feedback_count=item.unresolved_feedback_count,
        calibration_gap_score=calibration_gap_score,
        feedback_age_seconds=feedback_age_seconds,
        priority_tier=priority_tier,
        status=status,
        reason_codes=_row_reason_codes(
            item=item,
            calibration_gap_score=calibration_gap_score,
            feedback_age_seconds=feedback_age_seconds,
            config=config,
        ),
    )


def _calibration_gap_score(
    item: TeamSpecialistCalibrationFeedbackPriorityV2Input,
    generated_at: datetime,
    config: TeamSpecialistCalibrationFeedbackPriorityV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            _miscalibration_rate(item) * config.miscalibrated_rate_weight
            + item.average_probability_error * config.probability_error_weight
            + _unresolved_feedback_score(item, config) * config.unresolved_feedback_weight
            + _feedback_staleness_score(item, generated_at, config)
            * config.feedback_staleness_weight
        )
        return _clamp_ratio(score)


def _miscalibration_rate(
    item: TeamSpecialistCalibrationFeedbackPriorityV2Input,
) -> Decimal:
    if item.resolved_count == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(item.miscalibrated_count / item.resolved_count)


def _unresolved_feedback_score(
    item: TeamSpecialistCalibrationFeedbackPriorityV2Input,
    config: TeamSpecialistCalibrationFeedbackPriorityV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            item.unresolved_feedback_count / config.max_unresolved_feedback_count,
        )


def _feedback_staleness_score(
    item: TeamSpecialistCalibrationFeedbackPriorityV2Input,
    generated_at: datetime,
    config: TeamSpecialistCalibrationFeedbackPriorityV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            _feedback_age_seconds(generated_at, item.latest_feedback_at)
            / config.stale_feedback_after_seconds,
        )


def _feedback_age_seconds(generated_at: datetime, latest_feedback_at: datetime) -> Decimal:
    delta = generated_at - latest_feedback_at
    with localcontext(DECIMAL_CONTEXT):
        seconds = (
            Decimal(delta.days * 86400)
            + Decimal(delta.seconds)
            + Decimal(delta.microseconds) / Decimal(1000000)
        )
        return seconds.quantize(SCORE_QUANT)


def _priority_tier(
    score: Decimal,
    config: TeamSpecialistCalibrationFeedbackPriorityV2Config,
) -> str:
    if score >= config.high_priority_floor:
        return "high"
    if score >= config.medium_priority_floor:
        return "medium"
    return "low"


def _status_for_priority_tier(priority_tier: str) -> str:
    if priority_tier == "high":
        return "block"
    if priority_tier == "medium":
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[TeamSpecialistCalibrationFeedbackPriorityV2Row, ...],
) -> str:
    if not rows:
        return "empty"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    item: TeamSpecialistCalibrationFeedbackPriorityV2Input,
    calibration_gap_score: Decimal,
    feedback_age_seconds: Decimal,
    config: TeamSpecialistCalibrationFeedbackPriorityV2Config,
) -> tuple[str, ...]:
    reason_codes = [
        _calibration_gap_reason(calibration_gap_score, config),
        _miscalibration_rate_reason(_miscalibration_rate(item)),
        _probability_error_reason(item.average_probability_error),
        _unresolved_feedback_reason(item.unresolved_feedback_count, config),
    ]
    if feedback_age_seconds >= config.stale_feedback_after_seconds:
        reason_codes.append("feedback_stale")
    if item.resolved_count < item.forecast_count:
        reason_codes.append("forecast_outcome_gap_open")
    else:
        reason_codes.append("forecast_outcome_gap_closed")
    return tuple(reason_codes)


def _calibration_gap_reason(
    score: Decimal,
    config: TeamSpecialistCalibrationFeedbackPriorityV2Config,
) -> str:
    if score >= config.high_priority_floor:
        return "calibration_gap_high"
    if score >= config.medium_priority_floor:
        return "calibration_gap_medium"
    return "calibration_gap_low"


def _miscalibration_rate_reason(rate: Decimal) -> str:
    if rate >= Decimal("0.500000"):
        return "miscalibration_rate_high"
    if rate >= Decimal("0.200000"):
        return "miscalibration_rate_watch"
    return "miscalibration_rate_clear"


def _probability_error_reason(value: Decimal) -> str:
    if value >= Decimal("0.500000"):
        return "probability_error_high"
    if value >= Decimal("0.100000"):
        return "probability_error_watch"
    return "probability_error_clear"


def _unresolved_feedback_reason(
    count: Decimal,
    config: TeamSpecialistCalibrationFeedbackPriorityV2Config,
) -> str:
    if count >= config.max_unresolved_feedback_count:
        return "unresolved_feedback_block"
    if count > ZERO:
        return "unresolved_feedback_watch"
    return "unresolved_feedback_clear"


def _tier_count(
    rows: tuple[TeamSpecialistCalibrationFeedbackPriorityV2Row, ...],
    tier: str,
) -> Decimal:
    return Decimal(sum(1 for row in rows if row.priority_tier == tier)).quantize(
        COUNT_QUANT,
    )


def _status_count(
    rows: tuple[TeamSpecialistCalibrationFeedbackPriorityV2Row, ...],
    status: str,
) -> Decimal:
    return Decimal(sum(1 for row in rows if row.status == status)).quantize(COUNT_QUANT)


def _stale_count(
    rows: tuple[TeamSpecialistCalibrationFeedbackPriorityV2Row, ...],
    config: TeamSpecialistCalibrationFeedbackPriorityV2Config,
) -> Decimal:
    return Decimal(
        sum(
            1
            for row in rows
            if row.feedback_age_seconds >= config.stale_feedback_after_seconds
        ),
    ).quantize(COUNT_QUANT)


def _max_calibration_gap_score(
    rows: tuple[TeamSpecialistCalibrationFeedbackPriorityV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.calibration_gap_score for row in rows)


def _reason_code_counts(
    rows: tuple[TeamSpecialistCalibrationFeedbackPriorityV2Row, ...],
) -> tuple[TeamSpecialistCalibrationFeedbackReasonCodeCount, ...]:
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + Decimal("1")
    return tuple(
        TeamSpecialistCalibrationFeedbackReasonCodeCount(
            reason_code=reason_code,
            count=counts[reason_code].quantize(COUNT_QUANT),
        )
        for reason_code in sorted(counts)
    )


def _normalize_feedback_items(
    value: object,
) -> tuple[TeamSpecialistCalibrationFeedbackPriorityV2Input, ...]:
    if isinstance(value, (str, bytes)) or not hasattr(value, "__iter__"):
        raise ValueError("feedback_items must be an iterable")
    items = tuple(value)
    for item in items:
        if type(item) is not TeamSpecialistCalibrationFeedbackPriorityV2Input:
            raise ValueError(
                "feedback items must be "
                "TeamSpecialistCalibrationFeedbackPriorityV2Input",
            )
        _require_hard_flags(
            "TeamSpecialistCalibrationFeedbackPriorityV2Input",
            item,
        )
    keys = tuple((item.team_id, item.domain) for item in items)
    if len(set(keys)) != len(keys):
        raise ValueError("feedback items must not contain duplicate team/domain")
    return items


def _normalize_rows(
    value: object,
) -> tuple[TeamSpecialistCalibrationFeedbackPriorityV2Row, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not TeamSpecialistCalibrationFeedbackPriorityV2Row:
            raise ValueError(
                "rows must contain TeamSpecialistCalibrationFeedbackPriorityV2Row",
            )
    return value


def _normalize_reason_code_counts(
    value: object,
) -> tuple[TeamSpecialistCalibrationFeedbackReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for item in value:
        if type(item) is not TeamSpecialistCalibrationFeedbackReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "TeamSpecialistCalibrationFeedbackReasonCodeCount",
            )
    return value


def _validate_config(
    config: TeamSpecialistCalibrationFeedbackPriorityV2Config,
) -> None:
    with localcontext(DECIMAL_CONTEXT):
        weights_total = (
            config.miscalibrated_rate_weight
            + config.probability_error_weight
            + config.unresolved_feedback_weight
            + config.feedback_staleness_weight
        ).quantize(SCORE_QUANT)
    if weights_total != ONE:
        raise ValueError("priority weights must sum to 1.000000")
    if config.medium_priority_floor > config.high_priority_floor:
        raise ValueError("medium_priority_floor must not exceed high_priority_floor")


def _validate_count_consistency(
    *,
    forecast_count: Decimal,
    resolved_count: Decimal,
    miscalibrated_count: Decimal,
) -> None:
    if resolved_count > forecast_count:
        raise ValueError("resolved_count must not exceed forecast_count")
    if miscalibrated_count > resolved_count:
        raise ValueError("miscalibrated_count must not exceed resolved_count")


def _validate_row_consistency(
    row: TeamSpecialistCalibrationFeedbackPriorityV2Row,
) -> None:
    expected_status = _status_for_priority_tier(row.priority_tier)
    if row.status != expected_status:
        raise ValueError("status must match priority_tier")
    expected_gap_reason = {
        "high": "calibration_gap_high",
        "medium": "calibration_gap_medium",
        "low": "calibration_gap_low",
    }[row.priority_tier]
    if row.reason_codes[0] != expected_gap_reason:
        raise ValueError("reason_codes must match priority_tier")


def _validate_report_consistency(
    report: TeamSpecialistCalibrationFeedbackPriorityV2Report,
) -> None:
    rows = report.rows
    if report.team_count != Decimal(len(rows)).quantize(COUNT_QUANT):
        raise ValueError("team_count must match rows")
    if (
        report.high_priority_count != _tier_count(rows, "high")
        or report.medium_priority_count != _tier_count(rows, "medium")
        or report.low_priority_count != _tier_count(rows, "low")
    ):
        raise ValueError("priority counts must match rows")
    if (
        report.high_priority_count
        + report.medium_priority_count
        + report.low_priority_count
        != report.team_count
    ):
        raise ValueError("priority counts must sum to team_count")
    if report.blocked_feedback_count != _status_count(rows, "block"):
        raise ValueError("blocked_feedback_count must match rows")
    if report.stale_feedback_count != _reason_count(rows, "feedback_stale"):
        raise ValueError("stale_feedback_count must match rows")
    if report.max_calibration_gap_score != _max_calibration_gap_score(rows):
        raise ValueError("max_calibration_gap_score must match rows")
    _validate_rows_sorted(rows)
    expected_status = _report_status(rows)
    if report.report_status != expected_status:
        raise ValueError("report_status must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    if report.derived_validation_digest != _derived_validation_digest(asdict(report)):
        raise ValueError("derived_validation_digest must match report fields")


def _validate_rows_sorted(
    rows: tuple[TeamSpecialistCalibrationFeedbackPriorityV2Row, ...],
) -> None:
    expected = tuple(
        sorted(
            rows,
            key=lambda row: (
                -row.calibration_gap_score,
                -row.feedback_age_seconds,
                row.team_id,
                row.domain,
            ),
        ),
    )
    expected_ranks = tuple(
        Decimal(index).quantize(COUNT_QUANT) for index in range(1, len(rows) + 1)
    )
    actual_ranks = tuple(row.rank for row in rows)
    if rows != expected or actual_ranks != expected_ranks:
        raise ValueError("rows must be sorted by calibration gap and rank")


def _reason_count(
    rows: tuple[TeamSpecialistCalibrationFeedbackPriorityV2Row, ...],
    reason_code: str,
) -> Decimal:
    return Decimal(
        sum(1 for row in rows if reason_code in row.reason_codes),
    ).quantize(COUNT_QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_non_empty_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    normalized = value.strip()
    _reject_unsafe_public_payload(field_name, normalized)
    return normalized


def _require_priority_tier(field_name: str, value: object) -> None:
    _require_non_empty_string(field_name, value)
    if value not in PRIORITY_TIERS:
        raise ValueError(f"{field_name} must be high, medium, or low")


def _require_row_status(field_name: str, value: object) -> None:
    _require_non_empty_string(field_name, value)
    if value not in ROW_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_report_status(field_name: str, value: object) -> None:
    _require_non_empty_string(field_name, value)
    if value not in REPORT_STATUSES:
        raise ValueError(f"{field_name} must be empty, pass, watch, or block")


def _require_reason_code(field_name: str, value: object) -> str:
    normalized = _require_non_empty_string(field_name, value)
    if normalized not in ROW_REASON_CODES:
        raise ValueError(f"{field_name} must contain a known reason code")
    return normalized


def _normalize_reason_codes(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    normalized = tuple(_require_reason_code(field_name, item) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(SCORE_QUANT)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(SCORE_QUANT)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    value = _normalize_nonnegative_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return value.quantize(COUNT_QUANT)


def _normalize_positive_integral_decimal(field_name: str, value: object) -> Decimal:
    value = _normalize_nonnegative_integral_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _clamp_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return min(ONE, max(ZERO, value)).quantize(SCORE_QUANT)


def _require_sha256_digest(field_name: str, value: object) -> None:
    _require_non_empty_string(field_name, value)
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {field_name}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {field_name}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {field_name}")


def _payload_value(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    if type(value) in (int, float):
        raise ValueError("payload numeric values must be Decimal")
    raise ValueError("payload contains unsupported value")


def _derived_validation_digest(values: dict[str, object]) -> str:
    digest_payload = {
        key: _payload_value(item)
        for key, item in values.items()
        if key != "derived_validation_digest"
    }
    _reject_unsafe_public_payload("derived validation digest payload", digest_payload)
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_text(label, field.name)
            item = getattr(value, field.name)
            if field.name in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"unsafe public payload in {label}")
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public payload in {label}")
            _reject_unsafe_public_text(label, key)
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"unsafe public payload in {label}")
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"unsafe public payload in {label}")
        return
    if type(value) in (int, float):
        raise ValueError(f"unsafe public payload in {label}")
    if type(value) is str:
        _reject_unsafe_public_text(label, value)
        return
    if type(value) is datetime:
        _as_utc("public payload datetime", value)
        return
    raise ValueError(f"unsafe public payload in {label}")


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if value.strip() != value:
        raise ValueError(f"unsafe public payload in {label}")
    if "://" in normalized or "?" in normalized:
        raise ValueError(f"unsafe public payload in {label}")
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"unsafe public payload in {label}")
