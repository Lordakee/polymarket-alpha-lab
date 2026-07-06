"""Readonly Decimal priority report for specialist resolution feedback."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json


DEFAULT_TEAM_SPECIALIST_RESOLUTION_FEEDBACK_PRIORITY_V2_CONFIG_VERSION = (
    "team-specialist-resolution-feedback-priority-v2"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

PRIORITY_TIERS = ("high", "medium", "low")
REPORT_STATUSES = ("high", "watch", "blocked")
ROW_REASON_CODES = (
    "priority_high",
    "priority_medium",
    "priority_low",
    "resolution_feedback_high",
    "resolution_feedback_medium",
    "resolution_feedback_low",
    "missed_learning_penalty_clear",
    "missed_learning_penalty_watch",
    "missed_learning_penalty_high",
    "calibration_impact_high",
    "calibration_impact_medium",
    "calibration_impact_low",
)
REPORT_REASON_CODES = (
    "feedback_priority_high_rows",
    "feedback_priority_medium_rows",
    "feedback_priority_low_rows",
    "feedback_priority_empty",
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
    "DEFAULT_TEAM_SPECIALIST_RESOLUTION_FEEDBACK_PRIORITY_V2_CONFIG_VERSION",
    "TeamSpecialistResolutionFeedbackPriorityV2Config",
    "TeamSpecialistResolutionFeedbackV2Input",
    "TeamSpecialistResolutionFeedbackPriorityV2Row",
    "TeamSpecialistResolutionFeedbackPriorityV2Report",
    "build_team_specialist_resolution_feedback_priority_v2",
)


@dataclass(frozen=True)
class TeamSpecialistResolutionFeedbackPriorityV2Config:
    config_version: str = (
        DEFAULT_TEAM_SPECIALIST_RESOLUTION_FEEDBACK_PRIORITY_V2_CONFIG_VERSION
    )
    resolution_feedback_weight: Decimal = Decimal("0.500000")
    missed_learning_weight: Decimal = Decimal("0.250000")
    calibration_impact_weight: Decimal = Decimal("0.250000")
    max_missed_learning_count: Decimal = Decimal("5")
    high_priority_floor: Decimal = Decimal("0.800000")
    medium_priority_floor: Decimal = Decimal("0.550000")
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
            "resolution_feedback_weight",
            "missed_learning_weight",
            "calibration_impact_weight",
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
            "max_missed_learning_count",
            _normalize_positive_integral_decimal(
                "max_missed_learning_count",
                self.max_missed_learning_count,
            ),
        )
        _validate_config(self)
        _require_hard_flags("TeamSpecialistResolutionFeedbackPriorityV2Config", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistResolutionFeedbackPriorityV2Config",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistResolutionFeedbackV2Input:
    team_id: str
    specialist_id: str
    resolution_id: str
    resolution_feedback_score: Decimal
    missed_learning_count: Decimal
    calibration_impact_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("team_id", "specialist_id", "resolution_id"):
            object.__setattr__(
                self,
                field_name,
                _require_non_empty_string(field_name, getattr(self, field_name)),
            )
        for field_name in ("resolution_feedback_score", "calibration_impact_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "missed_learning_count",
            _normalize_nonnegative_integral_decimal(
                "missed_learning_count",
                self.missed_learning_count,
            ),
        )
        _require_hard_flags("TeamSpecialistResolutionFeedbackV2Input", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistResolutionFeedbackV2Input",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistResolutionFeedbackPriorityV2Row:
    rank: Decimal
    team_id: str
    specialist_id: str
    resolution_id: str
    resolution_feedback_score: Decimal
    missed_learning_count: Decimal
    missed_learning_health_score: Decimal
    calibration_impact_score: Decimal
    priority_score: Decimal
    priority_tier: str
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
        for field_name in ("team_id", "specialist_id", "resolution_id"):
            object.__setattr__(
                self,
                field_name,
                _require_non_empty_string(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "resolution_feedback_score",
            "missed_learning_health_score",
            "calibration_impact_score",
            "priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "missed_learning_count",
            _normalize_nonnegative_integral_decimal(
                "missed_learning_count",
                self.missed_learning_count,
            ),
        )
        _require_priority_tier("priority_tier", self.priority_tier)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("TeamSpecialistResolutionFeedbackPriorityV2Row", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistResolutionFeedbackPriorityV2Row",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistResolutionFeedbackPriorityV2Report:
    generated_at: datetime
    config_version: str
    priority_status: str
    item_count: Decimal
    high_priority_count: Decimal
    medium_priority_count: Decimal
    low_priority_count: Decimal
    average_priority_score: Decimal
    top_priority_score: Decimal
    bottom_priority_score: Decimal
    rows: tuple[TeamSpecialistResolutionFeedbackPriorityV2Row, ...]
    reason_codes: tuple[str, ...]
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
        _require_report_status("priority_status", self.priority_status)
        for field_name in (
            "item_count",
            "high_priority_count",
            "medium_priority_count",
            "low_priority_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "average_priority_score",
            "top_priority_score",
            "bottom_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("TeamSpecialistResolutionFeedbackPriorityV2Report", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistResolutionFeedbackPriorityV2Report",
            _payload_value(asdict(self)),
        )
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload(
            "TeamSpecialistResolutionFeedbackPriorityV2Report.payload",
            payload,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_team_specialist_resolution_feedback_priority_v2(
    feedback_items: object,
    *,
    config: TeamSpecialistResolutionFeedbackPriorityV2Config | None = None,
    generated_at: datetime,
) -> TeamSpecialistResolutionFeedbackPriorityV2Report:
    if config is None:
        config = TeamSpecialistResolutionFeedbackPriorityV2Config()
    if type(config) is not TeamSpecialistResolutionFeedbackPriorityV2Config:
        raise ValueError(
            "config must be a TeamSpecialistResolutionFeedbackPriorityV2Config",
        )
    _require_hard_flags("TeamSpecialistResolutionFeedbackPriorityV2Config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    items = _normalize_feedback_items(feedback_items)
    rows = tuple(
        _row_for_item(rank=Decimal(index).quantize(COUNT_QUANT), item=item, config=config)
        for index, item in enumerate(_sorted_items(items, config), start=1)
    )
    status = _report_status(rows)
    values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "priority_status": status,
        "item_count": Decimal(len(rows)).quantize(COUNT_QUANT),
        "high_priority_count": _tier_count(rows, "high"),
        "medium_priority_count": _tier_count(rows, "medium"),
        "low_priority_count": _tier_count(rows, "low"),
        "average_priority_score": _average_score(rows),
        "top_priority_score": _top_score(rows),
        "bottom_priority_score": _bottom_score(rows),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows, status),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _derived_validation_digest(values)
    return TeamSpecialistResolutionFeedbackPriorityV2Report(**values)


def _sorted_items(
    items: tuple[TeamSpecialistResolutionFeedbackV2Input, ...],
    config: TeamSpecialistResolutionFeedbackPriorityV2Config,
) -> tuple[TeamSpecialistResolutionFeedbackV2Input, ...]:
    return tuple(
        sorted(
            items,
            key=lambda item: (
                -_priority_score(item, config),
                item.team_id,
                item.specialist_id,
                item.resolution_id,
            ),
        ),
    )


def _row_for_item(
    *,
    rank: Decimal,
    item: TeamSpecialistResolutionFeedbackV2Input,
    config: TeamSpecialistResolutionFeedbackPriorityV2Config,
) -> TeamSpecialistResolutionFeedbackPriorityV2Row:
    score = _priority_score(item, config)
    tier = _priority_tier(score, config)
    return TeamSpecialistResolutionFeedbackPriorityV2Row(
        rank=rank,
        team_id=item.team_id,
        specialist_id=item.specialist_id,
        resolution_id=item.resolution_id,
        resolution_feedback_score=item.resolution_feedback_score,
        missed_learning_count=item.missed_learning_count,
        missed_learning_health_score=_missed_learning_health_score(
            item.missed_learning_count,
            config.max_missed_learning_count,
        ),
        calibration_impact_score=item.calibration_impact_score,
        priority_score=score,
        priority_tier=tier,
        reason_codes=_row_reason_codes(item, tier, config),
    )


def _priority_score(
    item: TeamSpecialistResolutionFeedbackV2Input,
    config: TeamSpecialistResolutionFeedbackPriorityV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            item.resolution_feedback_score * config.resolution_feedback_weight
            + _missed_learning_health_score(
                item.missed_learning_count,
                config.max_missed_learning_count,
            )
            * config.missed_learning_weight
            + item.calibration_impact_score * config.calibration_impact_weight
        )
        return _clamp_ratio(score)


def _missed_learning_health_score(count: Decimal, maximum: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(ONE - count / maximum)


def _priority_tier(
    score: Decimal,
    config: TeamSpecialistResolutionFeedbackPriorityV2Config,
) -> str:
    if score >= config.high_priority_floor:
        return "high"
    if score >= config.medium_priority_floor:
        return "medium"
    return "low"


def _report_status(
    rows: tuple[TeamSpecialistResolutionFeedbackPriorityV2Row, ...],
) -> str:
    if not rows:
        return "blocked"
    if any(row.priority_tier == "low" for row in rows):
        return "blocked"
    if any(row.priority_tier == "medium" for row in rows):
        return "watch"
    return "high"


def _row_reason_codes(
    item: TeamSpecialistResolutionFeedbackV2Input,
    tier: str,
    config: TeamSpecialistResolutionFeedbackPriorityV2Config,
) -> tuple[str, ...]:
    return (
        f"priority_{tier}",
        _tier_reason(
            item.resolution_feedback_score,
            high=Decimal("0.800000"),
            medium=Decimal("0.550000"),
            high_reason="resolution_feedback_high",
            medium_reason="resolution_feedback_medium",
            low_reason="resolution_feedback_low",
        ),
        _missed_learning_reason(item.missed_learning_count, config),
        _tier_reason(
            item.calibration_impact_score,
            high=Decimal("0.750000"),
            medium=Decimal("0.400000"),
            high_reason="calibration_impact_high",
            medium_reason="calibration_impact_medium",
            low_reason="calibration_impact_low",
        ),
    )


def _tier_reason(
    value: Decimal,
    *,
    high: Decimal,
    medium: Decimal,
    high_reason: str,
    medium_reason: str,
    low_reason: str,
) -> str:
    if value >= high:
        return high_reason
    if value >= medium:
        return medium_reason
    return low_reason


def _missed_learning_reason(
    count: Decimal,
    config: TeamSpecialistResolutionFeedbackPriorityV2Config,
) -> str:
    if count == ZERO:
        return "missed_learning_penalty_clear"
    if count < config.max_missed_learning_count:
        return "missed_learning_penalty_watch"
    return "missed_learning_penalty_high"


def _report_reason_codes(
    rows: tuple[TeamSpecialistResolutionFeedbackPriorityV2Row, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("feedback_priority_empty",)
    reasons: list[str] = []
    if any(row.priority_tier == "low" for row in rows):
        reasons.append("feedback_priority_low_rows")
    if any(row.priority_tier == "medium" for row in rows):
        reasons.append("feedback_priority_medium_rows")
    if not reasons and status == "high":
        reasons.append("feedback_priority_high_rows")
    return tuple(reasons)


def _tier_count(
    rows: tuple[TeamSpecialistResolutionFeedbackPriorityV2Row, ...],
    tier: str,
) -> Decimal:
    return Decimal(sum(1 for row in rows if row.priority_tier == tier)).quantize(
        COUNT_QUANT,
    )


def _average_score(
    rows: tuple[TeamSpecialistResolutionFeedbackPriorityV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(sum(row.priority_score for row in rows) / Decimal(len(rows)))


def _top_score(
    rows: tuple[TeamSpecialistResolutionFeedbackPriorityV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.priority_score for row in rows)


def _bottom_score(
    rows: tuple[TeamSpecialistResolutionFeedbackPriorityV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return min(row.priority_score for row in rows)


def _normalize_feedback_items(
    value: object,
) -> tuple[TeamSpecialistResolutionFeedbackV2Input, ...]:
    if isinstance(value, (str, bytes)) or not hasattr(value, "__iter__"):
        raise ValueError("feedback_items must be an iterable")
    items = tuple(value)
    for item in items:
        if type(item) is not TeamSpecialistResolutionFeedbackV2Input:
            raise ValueError(
                "feedback items must be TeamSpecialistResolutionFeedbackV2Input",
            )
        _require_hard_flags("TeamSpecialistResolutionFeedbackV2Input", item)
    keys = tuple((item.team_id, item.specialist_id, item.resolution_id) for item in items)
    if len(set(keys)) != len(keys):
        raise ValueError("feedback items must not contain duplicate identities")
    return items


def _normalize_rows(
    value: object,
) -> tuple[TeamSpecialistResolutionFeedbackPriorityV2Row, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not TeamSpecialistResolutionFeedbackPriorityV2Row:
            raise ValueError(
                "rows must contain TeamSpecialistResolutionFeedbackPriorityV2Row",
            )
    return value


def _validate_config(config: TeamSpecialistResolutionFeedbackPriorityV2Config) -> None:
    with localcontext(DECIMAL_CONTEXT):
        weights_total = (
            config.resolution_feedback_weight
            + config.missed_learning_weight
            + config.calibration_impact_weight
        ).quantize(SCORE_QUANT)
    if weights_total != ONE:
        raise ValueError("priority weights must sum to 1.000000")
    if config.medium_priority_floor > config.high_priority_floor:
        raise ValueError("medium_priority_floor must not exceed high_priority_floor")


def _validate_report_consistency(
    report: TeamSpecialistResolutionFeedbackPriorityV2Report,
) -> None:
    rows = report.rows
    if report.item_count != Decimal(len(rows)).quantize(COUNT_QUANT):
        raise ValueError("item_count must match rows")
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
        != report.item_count
    ):
        raise ValueError("priority counts must sum to item_count")
    _validate_rows_sorted(rows)
    expected_status = _report_status(rows)
    if report.priority_status != expected_status:
        raise ValueError("priority_status must match rows")
    if report.reason_codes != _report_reason_codes(rows, report.priority_status):
        raise ValueError("reason_codes must match priority_status")
    if report.derived_validation_digest != _derived_validation_digest(asdict(report)):
        raise ValueError("derived_validation_digest must match report fields")
    if report.average_priority_score != _average_score(rows):
        raise ValueError("average_priority_score must match rows")
    if report.top_priority_score != _top_score(rows):
        raise ValueError("top_priority_score must match rows")
    if report.bottom_priority_score != _bottom_score(rows):
        raise ValueError("bottom_priority_score must match rows")


def _validate_rows_sorted(
    rows: tuple[TeamSpecialistResolutionFeedbackPriorityV2Row, ...],
) -> None:
    expected = tuple(
        sorted(
            rows,
            key=lambda row: (
                -row.priority_score,
                row.team_id,
                row.specialist_id,
                row.resolution_id,
            ),
        ),
    )
    expected_ranks = tuple(
        Decimal(index).quantize(COUNT_QUANT) for index in range(1, len(rows) + 1)
    )
    actual_ranks = tuple(row.rank for row in rows)
    if rows != expected or actual_ranks != expected_ranks:
        raise ValueError("rows must be sorted by priority score and rank")


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


def _require_report_status(field_name: str, value: object) -> None:
    _require_non_empty_string(field_name, value)
    if value not in REPORT_STATUSES:
        raise ValueError(f"{field_name} must be high, watch, or blocked")


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    normalized = tuple(_require_non_empty_string(field_name, item) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    if any(item not in allowed for item in normalized):
        raise ValueError(f"{field_name} must contain known reason codes")
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
