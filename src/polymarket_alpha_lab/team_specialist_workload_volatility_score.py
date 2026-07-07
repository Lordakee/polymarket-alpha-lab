"""Pure readonly report for specialist workload volatility score."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any
import json


DEFAULT_TEAM_SPECIALIST_WORKLOAD_VOLATILITY_SCORE_CONFIG_VERSION = (
    "team-specialist-workload-volatility-score-v1"
)
TEAM_SPECIALIST_WORKLOAD_VOLATILITY_SCORE_STATUSES = ("pass", "watch", "block")

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

REASON_CODES = (
    "workload_volatility_pass",
    "workload_volatility_watch",
    "workload_volatility_block",
    "open_count_change_pass",
    "open_count_change_watch",
    "open_count_change_block",
    "urgent_ratio_clear",
    "urgent_ratio_watch",
    "urgent_ratio_pressure",
    "completion_variability_clear",
    "completion_variability_watch",
    "completion_variability_pressure",
    "stale_item_ratio_clear",
    "stale_item_ratio_watch",
    "stale_item_ratio_pressure",
    "capacity_utilization_clear",
    "capacity_utilization_watch",
    "capacity_utilization_pressure",
)
UNSAFE_PUBLIC_FRAGMENTS = tuple(
    bytes.fromhex(value).decode("ascii")
    for value in (
        "3a2f2f",
        "68747470",
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
    "DEFAULT_TEAM_SPECIALIST_WORKLOAD_VOLATILITY_SCORE_CONFIG_VERSION",
    "TEAM_SPECIALIST_WORKLOAD_VOLATILITY_SCORE_STATUSES",
    "TeamSpecialistWorkloadVolatilityScoreConfig",
    "TeamSpecialistWorkloadVolatilityScoreInput",
    "TeamSpecialistWorkloadVolatilityScoreReport",
    "score_team_specialist_workload_volatility",
    "team_specialist_workload_volatility_score_payload",
)


@dataclass(frozen=True)
class TeamSpecialistWorkloadVolatilityScoreConfig:
    config_version: str = (
        DEFAULT_TEAM_SPECIALIST_WORKLOAD_VOLATILITY_SCORE_CONFIG_VERSION
    )
    open_count_change_weight: Decimal = Decimal("0.300000")
    urgent_ratio_weight: Decimal = Decimal("0.180000")
    completion_variability_weight: Decimal = Decimal("0.220000")
    stale_item_ratio_weight: Decimal = Decimal("0.140000")
    capacity_utilization_weight: Decimal = Decimal("0.160000")
    open_count_change_watch_ratio: Decimal = Decimal("0.250000")
    open_count_change_block_ratio: Decimal = Decimal("0.750000")
    urgent_ratio_watch_floor: Decimal = Decimal("0.200000")
    urgent_ratio_block_floor: Decimal = Decimal("0.500000")
    completion_variability_watch_floor: Decimal = Decimal("0.250000")
    completion_variability_block_floor: Decimal = Decimal("0.650000")
    stale_item_ratio_watch_floor: Decimal = Decimal("0.200000")
    stale_item_ratio_block_floor: Decimal = Decimal("0.500000")
    capacity_utilization_watch_floor: Decimal = Decimal("0.750000")
    capacity_utilization_block_floor: Decimal = Decimal("0.950000")
    score_watch_floor: Decimal = Decimal("0.250000")
    score_block_floor: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistWorkloadVolatilityScoreConfig:
            raise ValueError(
                "config must be exactly TeamSpecialistWorkloadVolatilityScoreConfig",
            )
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        for field_name in (
            "open_count_change_weight",
            "urgent_ratio_weight",
            "completion_variability_weight",
            "stale_item_ratio_weight",
            "capacity_utilization_weight",
            "open_count_change_watch_ratio",
            "open_count_change_block_ratio",
            "urgent_ratio_watch_floor",
            "urgent_ratio_block_floor",
            "completion_variability_watch_floor",
            "completion_variability_block_floor",
            "stale_item_ratio_watch_floor",
            "stale_item_ratio_block_floor",
            "capacity_utilization_watch_floor",
            "capacity_utilization_block_floor",
            "score_watch_floor",
            "score_block_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("TeamSpecialistWorkloadVolatilityScoreConfig", self)
        _reject_public_payload(
            "TeamSpecialistWorkloadVolatilityScoreConfig",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistWorkloadVolatilityScoreInput:
    team_id: str
    specialist_id: str
    current_open_count: Decimal
    prior_open_count: Decimal
    urgent_ratio: Decimal
    completion_variability_score: Decimal
    stale_item_ratio: Decimal
    capacity_utilization_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistWorkloadVolatilityScoreInput:
            raise ValueError(
                "input must be exactly TeamSpecialistWorkloadVolatilityScoreInput",
            )
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
        for field_name in ("current_open_count", "prior_open_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "urgent_ratio",
            "completion_variability_score",
            "stale_item_ratio",
            "capacity_utilization_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("TeamSpecialistWorkloadVolatilityScoreInput", self)
        _reject_public_payload(
            "TeamSpecialistWorkloadVolatilityScoreInput",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistWorkloadVolatilityScoreReport:
    config: TeamSpecialistWorkloadVolatilityScoreConfig
    team_id: str
    specialist_id: str
    current_open_count: Decimal
    prior_open_count: Decimal
    urgent_ratio: Decimal
    completion_variability_score: Decimal
    stale_item_ratio: Decimal
    capacity_utilization_score: Decimal
    open_count_delta: Decimal
    absolute_open_count_delta: Decimal
    open_count_volatility_ratio: Decimal
    workload_volatility_score: Decimal
    workload_volatility_status: str
    routing_priority_status: str
    report_status: str
    reduce_new_research_routing_priority: bool
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistWorkloadVolatilityScoreReport:
            raise ValueError(
                "report must be exactly TeamSpecialistWorkloadVolatilityScoreReport",
            )
        if type(self.config) is not TeamSpecialistWorkloadVolatilityScoreConfig:
            raise ValueError(
                "config must be a TeamSpecialistWorkloadVolatilityScoreConfig",
            )
        _require_hard_flags("TeamSpecialistWorkloadVolatilityScoreConfig", self.config)
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
        for field_name in ("current_open_count", "prior_open_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "open_count_delta",
            _normalize_decimal("open_count_delta", self.open_count_delta),
        )
        for field_name in (
            "urgent_ratio",
            "completion_variability_score",
            "stale_item_ratio",
            "capacity_utilization_score",
            "absolute_open_count_delta",
            "open_count_volatility_ratio",
            "workload_volatility_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_or_nonnegative(field_name, getattr(self, field_name)),
            )
        _require_status("workload_volatility_status", self.workload_volatility_status)
        _require_status("routing_priority_status", self.routing_priority_status)
        _require_status("report_status", self.report_status)
        if type(self.reduce_new_research_routing_priority) is not bool:
            raise ValueError("reduce_new_research_routing_priority must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("TeamSpecialistWorkloadVolatilityScoreReport", self)
        _reject_public_payload(
            "TeamSpecialistWorkloadVolatilityScoreReport",
            _payload_value(asdict(self)),
        )
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, Any]:
        payload = _payload_value(asdict(self))
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        _reject_public_payload(
            "TeamSpecialistWorkloadVolatilityScoreReport.payload",
            payload,
        )
        _verify_payload_digest(payload)
        return payload


def score_team_specialist_workload_volatility(
    workload_signal: TeamSpecialistWorkloadVolatilityScoreInput,
    *,
    config: TeamSpecialistWorkloadVolatilityScoreConfig | None = None,
) -> TeamSpecialistWorkloadVolatilityScoreReport:
    if type(workload_signal) is not TeamSpecialistWorkloadVolatilityScoreInput:
        raise ValueError(
            "workload_signal must be a TeamSpecialistWorkloadVolatilityScoreInput",
        )
    if config is None:
        config = TeamSpecialistWorkloadVolatilityScoreConfig()
    if type(config) is not TeamSpecialistWorkloadVolatilityScoreConfig:
        raise ValueError("config must be a TeamSpecialistWorkloadVolatilityScoreConfig")
    _require_hard_flags("TeamSpecialistWorkloadVolatilityScoreInput", workload_signal)
    _require_hard_flags("TeamSpecialistWorkloadVolatilityScoreConfig", config)

    open_count_delta = _open_count_delta(workload_signal)
    absolute_open_count_delta = _absolute_decimal(open_count_delta)
    open_count_volatility_ratio = _open_count_volatility_ratio(
        workload_signal,
        absolute_open_count_delta,
    )
    volatility_score = _workload_volatility_score(
        config=config,
        open_count_volatility_ratio=open_count_volatility_ratio,
        urgent_ratio=workload_signal.urgent_ratio,
        completion_variability_score=workload_signal.completion_variability_score,
        stale_item_ratio=workload_signal.stale_item_ratio,
        capacity_utilization_score=workload_signal.capacity_utilization_score,
    )
    volatility_status = _workload_volatility_status(
        config=config,
        open_count_volatility_ratio=open_count_volatility_ratio,
        urgent_ratio=workload_signal.urgent_ratio,
        completion_variability_score=workload_signal.completion_variability_score,
        stale_item_ratio=workload_signal.stale_item_ratio,
        capacity_utilization_score=workload_signal.capacity_utilization_score,
        workload_volatility_score=volatility_score,
    )
    routing_status = _routing_priority_status(volatility_status)
    values: dict[str, object] = {
        "config": config,
        "team_id": workload_signal.team_id,
        "specialist_id": workload_signal.specialist_id,
        "current_open_count": workload_signal.current_open_count,
        "prior_open_count": workload_signal.prior_open_count,
        "urgent_ratio": workload_signal.urgent_ratio,
        "completion_variability_score": workload_signal.completion_variability_score,
        "stale_item_ratio": workload_signal.stale_item_ratio,
        "capacity_utilization_score": workload_signal.capacity_utilization_score,
        "open_count_delta": open_count_delta,
        "absolute_open_count_delta": absolute_open_count_delta,
        "open_count_volatility_ratio": open_count_volatility_ratio,
        "workload_volatility_score": volatility_score,
        "workload_volatility_status": volatility_status,
        "routing_priority_status": routing_status,
        "report_status": routing_status,
        "reduce_new_research_routing_priority": routing_status != "pass",
        "reason_codes": _reason_codes(
            config=config,
            workload_volatility_status=volatility_status,
            open_count_volatility_ratio=open_count_volatility_ratio,
            urgent_ratio=workload_signal.urgent_ratio,
            completion_variability_score=workload_signal.completion_variability_score,
            stale_item_ratio=workload_signal.stale_item_ratio,
            capacity_utilization_score=workload_signal.capacity_utilization_score,
        ),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _derived_validation_digest(values)
    return TeamSpecialistWorkloadVolatilityScoreReport(**values)


def team_specialist_workload_volatility_score_payload(
    report: TeamSpecialistWorkloadVolatilityScoreReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is TeamSpecialistWorkloadVolatilityScoreReport:
        _require_hard_flags("TeamSpecialistWorkloadVolatilityScoreReport", report)
        return report.payload
    if type(report) is dict:
        payload = _payload_value(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a dict")
        _reject_public_payload(
            "TeamSpecialistWorkloadVolatilityScoreReport.payload",
            payload,
        )
        _require_hard_flags("payload", _DictFlags(payload))
        _verify_payload_digest(payload)
        return payload
    raise ValueError("report must be a TeamSpecialistWorkloadVolatilityScoreReport")


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


def _open_count_delta(
    workload_signal: TeamSpecialistWorkloadVolatilityScoreInput,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (
            workload_signal.current_open_count - workload_signal.prior_open_count
        ).quantize(SCORE_QUANT)


def _absolute_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return abs(value).quantize(SCORE_QUANT)


def _open_count_volatility_ratio(
    workload_signal: TeamSpecialistWorkloadVolatilityScoreInput,
    absolute_open_count_delta: Decimal,
) -> Decimal:
    if workload_signal.prior_open_count == ZERO:
        if workload_signal.current_open_count == ZERO:
            return ZERO
        return ONE
    return _clamp_ratio(_ratio(absolute_open_count_delta, workload_signal.prior_open_count))


def _workload_volatility_score(
    *,
    config: TeamSpecialistWorkloadVolatilityScoreConfig,
    open_count_volatility_ratio: Decimal,
    urgent_ratio: Decimal,
    completion_variability_score: Decimal,
    stale_item_ratio: Decimal,
    capacity_utilization_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            open_count_volatility_ratio * config.open_count_change_weight
            + urgent_ratio * config.urgent_ratio_weight
            + completion_variability_score * config.completion_variability_weight
            + stale_item_ratio * config.stale_item_ratio_weight
            + capacity_utilization_score * config.capacity_utilization_weight,
        )


def _workload_volatility_status(
    *,
    config: TeamSpecialistWorkloadVolatilityScoreConfig,
    open_count_volatility_ratio: Decimal,
    urgent_ratio: Decimal,
    completion_variability_score: Decimal,
    stale_item_ratio: Decimal,
    capacity_utilization_score: Decimal,
    workload_volatility_score: Decimal,
) -> str:
    if (
        workload_volatility_score >= config.score_block_floor
        or open_count_volatility_ratio >= config.open_count_change_block_ratio
        or urgent_ratio >= config.urgent_ratio_block_floor
        or completion_variability_score >= config.completion_variability_block_floor
        or stale_item_ratio >= config.stale_item_ratio_block_floor
        or capacity_utilization_score >= config.capacity_utilization_block_floor
    ):
        return "block"
    if (
        workload_volatility_score >= config.score_watch_floor
        or open_count_volatility_ratio >= config.open_count_change_watch_ratio
        or urgent_ratio >= config.urgent_ratio_watch_floor
        or completion_variability_score >= config.completion_variability_watch_floor
        or stale_item_ratio >= config.stale_item_ratio_watch_floor
        or capacity_utilization_score >= config.capacity_utilization_watch_floor
    ):
        return "watch"
    return "pass"


def _routing_priority_status(workload_volatility_status: str) -> str:
    _require_status("workload_volatility_status", workload_volatility_status)
    return workload_volatility_status


def _reason_codes(
    *,
    config: TeamSpecialistWorkloadVolatilityScoreConfig,
    workload_volatility_status: str,
    open_count_volatility_ratio: Decimal,
    urgent_ratio: Decimal,
    completion_variability_score: Decimal,
    stale_item_ratio: Decimal,
    capacity_utilization_score: Decimal,
) -> tuple[str, ...]:
    reasons = [
        f"workload_volatility_{workload_volatility_status}",
        _component_reason_code(
            "open_count_change",
            open_count_volatility_ratio,
            config.open_count_change_watch_ratio,
            config.open_count_change_block_ratio,
        ),
        _component_reason_code(
            "urgent_ratio",
            urgent_ratio,
            config.urgent_ratio_watch_floor,
            config.urgent_ratio_block_floor,
        ),
        _component_reason_code(
            "completion_variability",
            completion_variability_score,
            config.completion_variability_watch_floor,
            config.completion_variability_block_floor,
        ),
        _component_reason_code(
            "stale_item_ratio",
            stale_item_ratio,
            config.stale_item_ratio_watch_floor,
            config.stale_item_ratio_block_floor,
        ),
        _component_reason_code(
            "capacity_utilization",
            capacity_utilization_score,
            config.capacity_utilization_watch_floor,
            config.capacity_utilization_block_floor,
        ),
    ]
    return _normalize_reason_codes("reason_codes", tuple(reasons))


def _component_reason_code(
    prefix: str,
    value: Decimal,
    watch_floor: Decimal,
    block_floor: Decimal,
) -> str:
    if prefix == "open_count_change":
        if value >= block_floor:
            return "open_count_change_block"
        if value >= watch_floor:
            return "open_count_change_watch"
        return "open_count_change_pass"
    if value >= block_floor:
        return f"{prefix}_pressure"
    if value >= watch_floor:
        return f"{prefix}_watch"
    return f"{prefix}_clear"


def _validate_config(config: TeamSpecialistWorkloadVolatilityScoreConfig) -> None:
    with localcontext(DECIMAL_CONTEXT):
        weights_total = (
            config.open_count_change_weight
            + config.urgent_ratio_weight
            + config.completion_variability_weight
            + config.stale_item_ratio_weight
            + config.capacity_utilization_weight
        ).quantize(SCORE_QUANT)
    if weights_total != ONE:
        raise ValueError("score weights must sum to 1.000000")
    _require_threshold_sequence(
        "open_count_change",
        config.open_count_change_watch_ratio,
        config.open_count_change_block_ratio,
    )
    _require_threshold_sequence(
        "urgent_ratio",
        config.urgent_ratio_watch_floor,
        config.urgent_ratio_block_floor,
    )
    _require_threshold_sequence(
        "completion_variability",
        config.completion_variability_watch_floor,
        config.completion_variability_block_floor,
    )
    _require_threshold_sequence(
        "stale_item_ratio",
        config.stale_item_ratio_watch_floor,
        config.stale_item_ratio_block_floor,
    )
    _require_threshold_sequence(
        "capacity_utilization",
        config.capacity_utilization_watch_floor,
        config.capacity_utilization_block_floor,
    )
    _require_threshold_sequence(
        "score",
        config.score_watch_floor,
        config.score_block_floor,
    )


def _require_threshold_sequence(
    label: str,
    watch_floor: Decimal,
    block_floor: Decimal,
) -> None:
    if watch_floor > block_floor:
        raise ValueError(f"{label} watch threshold must not exceed block threshold")


def _validate_report_consistency(
    report: TeamSpecialistWorkloadVolatilityScoreReport,
) -> None:
    expected_delta = _open_count_delta(report)
    if report.open_count_delta != expected_delta:
        raise ValueError("open_count_delta must match input fields")
    expected_absolute_delta = _absolute_decimal(expected_delta)
    if report.absolute_open_count_delta != expected_absolute_delta:
        raise ValueError("absolute_open_count_delta must match input fields")
    expected_open_volatility = _open_count_volatility_ratio(
        report,
        expected_absolute_delta,
    )
    if report.open_count_volatility_ratio != expected_open_volatility:
        raise ValueError("open_count_volatility_ratio must match input fields")
    expected_score = _workload_volatility_score(
        config=report.config,
        open_count_volatility_ratio=report.open_count_volatility_ratio,
        urgent_ratio=report.urgent_ratio,
        completion_variability_score=report.completion_variability_score,
        stale_item_ratio=report.stale_item_ratio,
        capacity_utilization_score=report.capacity_utilization_score,
    )
    if report.workload_volatility_score != expected_score:
        raise ValueError("workload_volatility_score must match components")
    expected_status = _workload_volatility_status(
        config=report.config,
        open_count_volatility_ratio=report.open_count_volatility_ratio,
        urgent_ratio=report.urgent_ratio,
        completion_variability_score=report.completion_variability_score,
        stale_item_ratio=report.stale_item_ratio,
        capacity_utilization_score=report.capacity_utilization_score,
        workload_volatility_score=report.workload_volatility_score,
    )
    if report.workload_volatility_status != expected_status:
        raise ValueError("workload_volatility_status must match components")
    expected_routing = _routing_priority_status(report.workload_volatility_status)
    if report.routing_priority_status != expected_routing:
        raise ValueError("routing_priority_status must match volatility status")
    if report.report_status != report.routing_priority_status:
        raise ValueError("report_status must match routing_priority_status")
    if report.reduce_new_research_routing_priority is not (
        report.routing_priority_status != "pass"
    ):
        raise ValueError("reduce_new_research_routing_priority must match status")
    expected_reasons = _reason_codes(
        config=report.config,
        workload_volatility_status=report.workload_volatility_status,
        open_count_volatility_ratio=report.open_count_volatility_ratio,
        urgent_ratio=report.urgent_ratio,
        completion_variability_score=report.completion_variability_score,
        stale_item_ratio=report.stale_item_ratio,
        capacity_utilization_score=report.capacity_utilization_score,
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
    if (
        type(value) is not str
        or value not in TEAM_SPECIALIST_WORKLOAD_VOLATILITY_SCORE_STATUSES
    ):
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


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    quantized = decimal_value.quantize(SCORE_QUANT)
    if quantized != decimal_value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    return decimal_value


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    return decimal_value


def _normalize_ratio_or_nonnegative(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if field_name in {
        "urgent_ratio",
        "completion_variability_score",
        "stale_item_ratio",
        "capacity_utilization_score",
        "open_count_volatility_ratio",
        "workload_volatility_score",
    } and decimal_value > ONE:
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
