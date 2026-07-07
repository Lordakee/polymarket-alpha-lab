"""Pure readonly report for specialist backlog pressure score."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any
import json


DEFAULT_TEAM_SPECIALIST_BACKLOG_PRESSURE_SCORE_CONFIG_VERSION = (
    "team-specialist-backlog-pressure-score-v1"
)
TEAM_SPECIALIST_BACKLOG_PRESSURE_SCORE_STATUSES = ("pass", "watch", "block")

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

REASON_CODES = (
    "backlog_pressure_pass",
    "backlog_pressure_watch",
    "backlog_pressure_block",
    "capacity_load_pass",
    "capacity_load_watch",
    "capacity_load_block",
    "urgent_item_pressure",
    "stale_item_pressure",
    "average_age_pressure",
    "completion_flow_clear",
    "completion_flow_watch",
    "completion_gap_pressure",
    "calibration_clear",
    "calibration_watch",
    "calibration_pressure",
)
UNSAFE_PUBLIC_FRAGMENTS = tuple(
    bytes.fromhex(value).decode("ascii")
    for value in (
        "3a2f2f",
        "40",
        "3f",
        "6d61726b65745f6964",
        "63616e6469646174655f6964",
        "6d61726b65745f736c7567",
        "7175657374696f6e",
        "75726c",
        "736f757263655f726566",
        "736f757263655f74657874",
        "64736e",
        "7461626c655f6e616d65",
        "746f6b656e",
        "736563726574",
        "61757468",
        "77616c6c6574",
        "6f72646572",
        "7472616465",
        "627579",
        "73656c6c",
        "7265636f6d6d656e646174696f6e",
        "706f736974696f6e5f73697a65",
        "706f736974696f6e2d73697a696e67",
        "7265616479",
        "626c6f636b6564",
        "6d617463686564",
        "737570706f72746564",
        "6c697665",
        "6e6574776f726b",
        "6461746162617365",
        "70657273697374",
        "7375706162617365",
    )
)

__all__ = (
    "DEFAULT_TEAM_SPECIALIST_BACKLOG_PRESSURE_SCORE_CONFIG_VERSION",
    "TEAM_SPECIALIST_BACKLOG_PRESSURE_SCORE_STATUSES",
    "TeamSpecialistBacklogPressureScoreConfig",
    "TeamSpecialistBacklogPressureScoreInput",
    "TeamSpecialistBacklogPressureScoreReport",
    "score_team_specialist_backlog_pressure",
    "team_specialist_backlog_pressure_score_payload",
)


@dataclass(frozen=True)
class TeamSpecialistBacklogPressureScoreConfig:
    config_version: str = DEFAULT_TEAM_SPECIALIST_BACKLOG_PRESSURE_SCORE_CONFIG_VERSION
    backlog_load_weight: Decimal = Decimal("0.350000")
    urgent_share_weight: Decimal = Decimal("0.200000")
    stale_share_weight: Decimal = Decimal("0.150000")
    average_age_weight: Decimal = Decimal("0.100000")
    completion_gap_weight: Decimal = Decimal("0.100000")
    calibration_weight: Decimal = Decimal("0.100000")
    capacity_watch_ratio: Decimal = Decimal("0.750000")
    capacity_block_ratio: Decimal = Decimal("1.000000")
    score_watch_floor: Decimal = Decimal("0.250000")
    score_block_floor: Decimal = Decimal("0.650000")
    stale_age_hours: Decimal = Decimal("72.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        for field_name in (
            "backlog_load_weight",
            "urgent_share_weight",
            "stale_share_weight",
            "average_age_weight",
            "completion_gap_weight",
            "calibration_weight",
            "capacity_watch_ratio",
            "capacity_block_ratio",
            "score_watch_floor",
            "score_block_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "stale_age_hours",
            _normalize_positive_decimal("stale_age_hours", self.stale_age_hours),
        )
        _validate_config(self)
        _require_hard_flags("TeamSpecialistBacklogPressureScoreConfig", self)
        _reject_public_payload(
            "TeamSpecialistBacklogPressureScoreConfig",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistBacklogPressureScoreInput:
    team_id: str
    specialist_id: str
    open_item_count: Decimal
    urgent_item_count: Decimal
    stale_item_count: Decimal
    average_age_hours: Decimal
    capacity_per_day: Decimal
    recent_completion_count: Decimal
    calibration_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "team_id",
            _require_public_string("team_id", self.team_id),
        )
        object.__setattr__(
            self,
            "specialist_id",
            _require_public_string("specialist_id", self.specialist_id),
        )
        for field_name in (
            "open_item_count",
            "urgent_item_count",
            "stale_item_count",
            "recent_completion_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_age_hours",):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "capacity_per_day",
            _normalize_positive_decimal("capacity_per_day", self.capacity_per_day),
        )
        object.__setattr__(
            self,
            "calibration_score",
            _normalize_ratio("calibration_score", self.calibration_score),
        )
        if self.urgent_item_count > self.open_item_count:
            raise ValueError("urgent_item_count must not exceed open_item_count")
        if self.stale_item_count > self.open_item_count:
            raise ValueError("stale_item_count must not exceed open_item_count")
        _require_hard_flags("TeamSpecialistBacklogPressureScoreInput", self)
        _reject_public_payload(
            "TeamSpecialistBacklogPressureScoreInput",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistBacklogPressureScoreReport:
    config: TeamSpecialistBacklogPressureScoreConfig
    team_id: str
    specialist_id: str
    open_item_count: Decimal
    urgent_item_count: Decimal
    stale_item_count: Decimal
    average_age_hours: Decimal
    capacity_per_day: Decimal
    recent_completion_count: Decimal
    calibration_score: Decimal
    raw_backlog_to_capacity_ratio: Decimal
    backlog_to_capacity_ratio: Decimal
    urgent_item_ratio: Decimal
    stale_item_ratio: Decimal
    average_age_pressure: Decimal
    completion_gap_ratio: Decimal
    calibration_pressure: Decimal
    backlog_pressure_score: Decimal
    overload_status: str
    routing_priority_status: str
    report_status: str
    overloaded: bool
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self.config) is not TeamSpecialistBacklogPressureScoreConfig:
            raise ValueError(
                "config must be a TeamSpecialistBacklogPressureScoreConfig",
            )
        _require_hard_flags("TeamSpecialistBacklogPressureScoreConfig", self.config)
        object.__setattr__(
            self,
            "team_id",
            _require_public_string("team_id", self.team_id),
        )
        object.__setattr__(
            self,
            "specialist_id",
            _require_public_string("specialist_id", self.specialist_id),
        )
        for field_name in (
            "open_item_count",
            "urgent_item_count",
            "stale_item_count",
            "recent_completion_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_age_hours",
            "capacity_per_day",
            "raw_backlog_to_capacity_ratio",
            "backlog_to_capacity_ratio",
            "urgent_item_ratio",
            "stale_item_ratio",
            "average_age_pressure",
            "completion_gap_ratio",
            "calibration_pressure",
            "backlog_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.capacity_per_day <= ZERO:
            raise ValueError("capacity_per_day must be positive")
        object.__setattr__(
            self,
            "calibration_score",
            _normalize_ratio("calibration_score", self.calibration_score),
        )
        _require_status("overload_status", self.overload_status)
        _require_status("routing_priority_status", self.routing_priority_status)
        _require_status("report_status", self.report_status)
        if type(self.overloaded) is not bool:
            raise ValueError("overloaded must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        if self.urgent_item_count > self.open_item_count:
            raise ValueError("urgent_item_count must not exceed open_item_count")
        if self.stale_item_count > self.open_item_count:
            raise ValueError("stale_item_count must not exceed open_item_count")
        _require_hard_flags("TeamSpecialistBacklogPressureScoreReport", self)
        _reject_public_payload(
            "TeamSpecialistBacklogPressureScoreReport",
            _payload_value(asdict(self)),
        )
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, Any]:
        payload = _payload_value(asdict(self))
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        _reject_public_payload("TeamSpecialistBacklogPressureScoreReport.payload", payload)
        _verify_payload_digest(payload)
        return payload


def score_team_specialist_backlog_pressure(
    backlog_signal: TeamSpecialistBacklogPressureScoreInput,
    *,
    config: TeamSpecialistBacklogPressureScoreConfig | None = None,
) -> TeamSpecialistBacklogPressureScoreReport:
    if type(backlog_signal) is not TeamSpecialistBacklogPressureScoreInput:
        raise ValueError(
            "backlog_signal must be a TeamSpecialistBacklogPressureScoreInput",
        )
    if config is None:
        config = TeamSpecialistBacklogPressureScoreConfig()
    if type(config) is not TeamSpecialistBacklogPressureScoreConfig:
        raise ValueError("config must be a TeamSpecialistBacklogPressureScoreConfig")
    _require_hard_flags("TeamSpecialistBacklogPressureScoreInput", backlog_signal)
    _require_hard_flags("TeamSpecialistBacklogPressureScoreConfig", config)

    raw_load = _raw_backlog_to_capacity_ratio(backlog_signal)
    capped_load = _clamp_ratio(raw_load)
    urgent_share = _item_share(backlog_signal.urgent_item_count, backlog_signal)
    stale_share = _item_share(backlog_signal.stale_item_count, backlog_signal)
    age_pressure = _age_pressure(backlog_signal, config)
    completion_gap = _completion_gap_ratio(backlog_signal)
    calibration_pressure = _calibration_pressure(backlog_signal)
    pressure_score = _backlog_pressure_score(
        config=config,
        backlog_to_capacity_ratio=capped_load,
        urgent_item_ratio=urgent_share,
        stale_item_ratio=stale_share,
        average_age_pressure=age_pressure,
        completion_gap_ratio=completion_gap,
        calibration_pressure=calibration_pressure,
    )
    overload = _overload_status(raw_load, config)
    routing = _routing_priority_status(
        overload_status=overload,
        backlog_pressure_score=pressure_score,
        config=config,
    )
    values: dict[str, object] = {
        "config": config,
        "team_id": backlog_signal.team_id,
        "specialist_id": backlog_signal.specialist_id,
        "open_item_count": backlog_signal.open_item_count,
        "urgent_item_count": backlog_signal.urgent_item_count,
        "stale_item_count": backlog_signal.stale_item_count,
        "average_age_hours": backlog_signal.average_age_hours,
        "capacity_per_day": backlog_signal.capacity_per_day,
        "recent_completion_count": backlog_signal.recent_completion_count,
        "calibration_score": backlog_signal.calibration_score,
        "raw_backlog_to_capacity_ratio": raw_load,
        "backlog_to_capacity_ratio": capped_load,
        "urgent_item_ratio": urgent_share,
        "stale_item_ratio": stale_share,
        "average_age_pressure": age_pressure,
        "completion_gap_ratio": completion_gap,
        "calibration_pressure": calibration_pressure,
        "backlog_pressure_score": pressure_score,
        "overload_status": overload,
        "routing_priority_status": routing,
        "report_status": routing,
        "overloaded": overload == "block",
        "reason_codes": _reason_codes(
            overload_status=overload,
            routing_priority_status=routing,
            urgent_item_ratio=urgent_share,
            stale_item_ratio=stale_share,
            average_age_pressure=age_pressure,
            completion_gap_ratio=completion_gap,
            calibration_pressure=calibration_pressure,
        ),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _derived_validation_digest(values)
    return TeamSpecialistBacklogPressureScoreReport(**values)


def team_specialist_backlog_pressure_score_payload(
    report: TeamSpecialistBacklogPressureScoreReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is TeamSpecialistBacklogPressureScoreReport:
        _require_hard_flags("TeamSpecialistBacklogPressureScoreReport", report)
        return report.payload
    if type(report) is dict:
        payload = _payload_value(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a dict")
        _reject_public_payload("TeamSpecialistBacklogPressureScoreReport.payload", payload)
        _require_hard_flags("payload", _DictFlags(payload))
        _verify_payload_digest(payload)
        return payload
    raise ValueError("report must be a TeamSpecialistBacklogPressureScoreReport")


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


def _raw_backlog_to_capacity_ratio(
    backlog_signal: TeamSpecialistBacklogPressureScoreInput,
) -> Decimal:
    return _ratio(backlog_signal.open_item_count, backlog_signal.capacity_per_day)


def _item_share(
    count: Decimal,
    backlog_signal: TeamSpecialistBacklogPressureScoreInput,
) -> Decimal:
    if backlog_signal.open_item_count == ZERO:
        return ZERO
    return _clamp_ratio(_ratio(count, backlog_signal.open_item_count))


def _age_pressure(
    backlog_signal: TeamSpecialistBacklogPressureScoreInput,
    config: TeamSpecialistBacklogPressureScoreConfig,
) -> Decimal:
    return _clamp_ratio(_ratio(backlog_signal.average_age_hours, config.stale_age_hours))


def _completion_gap_ratio(
    backlog_signal: TeamSpecialistBacklogPressureScoreInput,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        gap = backlog_signal.capacity_per_day - backlog_signal.recent_completion_count
    if gap <= ZERO:
        return ZERO
    return _clamp_ratio(_ratio(gap, backlog_signal.capacity_per_day))


def _calibration_pressure(
    backlog_signal: TeamSpecialistBacklogPressureScoreInput,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (ONE - backlog_signal.calibration_score).quantize(SCORE_QUANT)


def _backlog_pressure_score(
    *,
    config: TeamSpecialistBacklogPressureScoreConfig,
    backlog_to_capacity_ratio: Decimal,
    urgent_item_ratio: Decimal,
    stale_item_ratio: Decimal,
    average_age_pressure: Decimal,
    completion_gap_ratio: Decimal,
    calibration_pressure: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            backlog_to_capacity_ratio * config.backlog_load_weight
            + urgent_item_ratio * config.urgent_share_weight
            + stale_item_ratio * config.stale_share_weight
            + average_age_pressure * config.average_age_weight
            + completion_gap_ratio * config.completion_gap_weight
            + calibration_pressure * config.calibration_weight,
        )


def _overload_status(
    raw_backlog_to_capacity_ratio: Decimal,
    config: TeamSpecialistBacklogPressureScoreConfig,
) -> str:
    if raw_backlog_to_capacity_ratio >= config.capacity_block_ratio:
        return "block"
    if raw_backlog_to_capacity_ratio >= config.capacity_watch_ratio:
        return "watch"
    return "pass"


def _routing_priority_status(
    *,
    overload_status: str,
    backlog_pressure_score: Decimal,
    config: TeamSpecialistBacklogPressureScoreConfig,
) -> str:
    if overload_status == "block" or backlog_pressure_score >= config.score_block_floor:
        return "block"
    if overload_status == "watch" or backlog_pressure_score >= config.score_watch_floor:
        return "watch"
    return "pass"


def _reason_codes(
    *,
    overload_status: str,
    routing_priority_status: str,
    urgent_item_ratio: Decimal,
    stale_item_ratio: Decimal,
    average_age_pressure: Decimal,
    completion_gap_ratio: Decimal,
    calibration_pressure: Decimal,
) -> tuple[str, ...]:
    reasons = [
        f"backlog_pressure_{routing_priority_status}",
        f"capacity_load_{overload_status}",
    ]
    if urgent_item_ratio > ZERO:
        reasons.append("urgent_item_pressure")
    if stale_item_ratio > ZERO:
        reasons.append("stale_item_pressure")
    if average_age_pressure >= ONE:
        reasons.append("average_age_pressure")
    if completion_gap_ratio == ZERO:
        reasons.append("completion_flow_clear")
    elif completion_gap_ratio >= Decimal("0.500000"):
        reasons.append("completion_gap_pressure")
    else:
        reasons.append("completion_flow_watch")
    if calibration_pressure >= Decimal("0.500000"):
        reasons.append("calibration_pressure")
    elif calibration_pressure >= Decimal("0.250000"):
        reasons.append("calibration_watch")
    else:
        reasons.append("calibration_clear")
    return _normalize_reason_codes("reason_codes", tuple(reasons))


def _validate_config(config: TeamSpecialistBacklogPressureScoreConfig) -> None:
    with localcontext(DECIMAL_CONTEXT):
        weights_total = (
            config.backlog_load_weight
            + config.urgent_share_weight
            + config.stale_share_weight
            + config.average_age_weight
            + config.completion_gap_weight
            + config.calibration_weight
        ).quantize(SCORE_QUANT)
    if weights_total != ONE:
        raise ValueError("score weights must sum to 1.000000")
    if config.capacity_watch_ratio > config.capacity_block_ratio:
        raise ValueError("capacity_watch_ratio must not exceed capacity_block_ratio")
    if config.score_watch_floor > config.score_block_floor:
        raise ValueError("score_watch_floor must not exceed score_block_floor")


def _validate_report_consistency(
    report: TeamSpecialistBacklogPressureScoreReport,
) -> None:
    expected_raw_load = _raw_backlog_to_capacity_ratio(report)
    if report.raw_backlog_to_capacity_ratio != expected_raw_load:
        raise ValueError("raw_backlog_to_capacity_ratio must match input fields")
    expected_capped_load = _clamp_ratio(expected_raw_load)
    if report.backlog_to_capacity_ratio != expected_capped_load:
        raise ValueError("backlog_to_capacity_ratio must match input fields")
    expected_urgent_share = _item_share(report.urgent_item_count, report)
    if report.urgent_item_ratio != expected_urgent_share:
        raise ValueError("urgent_item_ratio must match input fields")
    expected_stale_share = _item_share(report.stale_item_count, report)
    if report.stale_item_ratio != expected_stale_share:
        raise ValueError("stale_item_ratio must match input fields")
    expected_age_pressure = _age_pressure(report, report.config)
    if report.average_age_pressure != expected_age_pressure:
        raise ValueError("average_age_pressure must match input fields")
    expected_completion_gap = _completion_gap_ratio(report)
    if report.completion_gap_ratio != expected_completion_gap:
        raise ValueError("completion_gap_ratio must match input fields")
    expected_calibration_pressure = _calibration_pressure(report)
    if report.calibration_pressure != expected_calibration_pressure:
        raise ValueError("calibration_pressure must match input fields")
    expected_score = _backlog_pressure_score(
        config=report.config,
        backlog_to_capacity_ratio=report.backlog_to_capacity_ratio,
        urgent_item_ratio=report.urgent_item_ratio,
        stale_item_ratio=report.stale_item_ratio,
        average_age_pressure=report.average_age_pressure,
        completion_gap_ratio=report.completion_gap_ratio,
        calibration_pressure=report.calibration_pressure,
    )
    if report.backlog_pressure_score != expected_score:
        raise ValueError("backlog_pressure_score must match components")
    expected_overload = _overload_status(
        report.raw_backlog_to_capacity_ratio,
        report.config,
    )
    if report.overload_status != expected_overload:
        raise ValueError("overload_status must match capacity load")
    expected_routing = _routing_priority_status(
        overload_status=report.overload_status,
        backlog_pressure_score=report.backlog_pressure_score,
        config=report.config,
    )
    if report.routing_priority_status != expected_routing:
        raise ValueError("routing_priority_status must match score and overload")
    if report.report_status != report.routing_priority_status:
        raise ValueError("report_status must match routing_priority_status")
    if report.overloaded is not (report.overload_status == "block"):
        raise ValueError("overloaded must match overload_status")
    expected_reasons = _reason_codes(
        overload_status=report.overload_status,
        routing_priority_status=report.routing_priority_status,
        urgent_item_ratio=report.urgent_item_ratio,
        stale_item_ratio=report.stale_item_ratio,
        average_age_pressure=report.average_age_pressure,
        completion_gap_ratio=report.completion_gap_ratio,
        calibration_pressure=report.calibration_pressure,
    )
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match report fields")
    if report.derived_validation_digest != _derived_validation_digest(asdict(report)):
        raise ValueError("derived_validation_digest must match report fields")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a public non-empty string")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be a public non-empty string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be a public non-empty string")
    _reject_public_text("value", value)
    return value


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in TEAM_SPECIALIST_BACKLOG_PRESSURE_SCORE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    normalized = tuple(_require_public_string(field_name, item) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    if any(item not in REASON_CODES for item in normalized):
        raise ValueError(f"{field_name} must contain known reason codes")
    return normalized


def _normalize_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return decimal_value.quantize(COUNT_QUANT)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    quantized = decimal_value.quantize(SCORE_QUANT)
    if quantized != decimal_value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return quantized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    quantized = decimal_value.quantize(SCORE_QUANT)
    if quantized != decimal_value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(SCORE_QUANT)


def _clamp_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return min(ONE, max(ZERO, value)).quantize(SCORE_QUANT)


def _require_digest(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _payload_value(value: object) -> object:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _payload_value(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal must be finite")
        return str(value)
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload contains unsupported value")


def _derived_validation_digest(values: dict[str, object]) -> str:
    digest_payload = {
        key: _payload_value(item)
        for key, item in values.items()
        if key != "derived_validation_digest"
    }
    _reject_public_payload("digest payload", digest_payload)
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _verify_payload_digest(payload: dict[str, Any]) -> None:
    _reject_public_payload("public payload", payload)
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest is required")
    _require_digest("derived_validation_digest", digest)
    if digest != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")


def _reject_public_payload(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public key in {label}")
            _reject_public_key(label, key)
            _reject_public_payload(label, item)
        return
    if type(value) is str:
        _reject_public_text(label, value)
        return
    if type(value) is list or type(value) is tuple:
        for item in value:
            _reject_public_payload(label, item)
        return
    if value is None or type(value) in (Decimal, bool):
        return
    raise ValueError(f"unsafe public payload in {label}")


def _reject_public_key(label: str, value: str) -> None:
    if _has_unsafe_fragment(value):
        raise ValueError(f"unsafe public key in {label}")


def _reject_public_text(label: str, value: str) -> None:
    if _has_unsafe_fragment(value):
        raise ValueError(f"unsafe public value in {label}")


def _has_unsafe_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)
