"""Pure readonly report for specialist queue SLA score."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any
import json


DEFAULT_TEAM_SPECIALIST_QUEUE_SLA_SCORE_CONFIG_VERSION = (
    "team-specialist-queue-sla-score-v1"
)
TEAM_SPECIALIST_QUEUE_SLA_SCORE_STATUSES = ("pass", "watch", "block")

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

REASON_CODES = (
    "queue_sla_pass",
    "queue_sla_watch",
    "queue_sla_block",
    "oldest_age_clear",
    "oldest_age_watch",
    "oldest_age_over_sla",
    "over_sla_items_clear",
    "over_sla_items_watch",
    "over_sla_items_block",
    "average_age_clear",
    "average_age_watch",
    "average_age_over_sla",
    "manual_capacity_clear",
    "manual_capacity_watch",
    "manual_capacity_block",
)
UNSAFE_PUBLIC_FRAGMENTS = tuple(
    bytes.fromhex(value).decode("ascii")
    for value in (
        "3a2f2f",
        "40",
        "3f",
        "7261775f63616e6469646174655f6964",
        "63616e6469646174655f6964",
        "6d61726b65745f6964",
        "6d61726b65745f736c7567",
        "7175657374696f6e",
        "736f757263655f726566",
        "75726c",
        "736f757263655f74657874",
        "64736e",
        "7461626c65",
        "746f6b656e",
        "736563726574",
        "77616c6c6574",
        "61757468",
        "6f72646572",
        "7472616465",
        "706f736974696f6e",
        "627579",
        "73656c6c",
        "7265636f6d6d656e646174696f6e",
        "6c697665",
        "6e6574776f726b",
        "6461746162617365",
        "70657273697374",
        "7375706162617365",
        "626c6f636b6564",
    )
)

__all__ = (
    "DEFAULT_TEAM_SPECIALIST_QUEUE_SLA_SCORE_CONFIG_VERSION",
    "TEAM_SPECIALIST_QUEUE_SLA_SCORE_STATUSES",
    "TeamSpecialistQueueSlaScoreConfig",
    "TeamSpecialistQueueSlaScoreInput",
    "TeamSpecialistQueueSlaScoreReport",
    "score_team_specialist_queue_sla",
    "team_specialist_queue_sla_score_payload",
)


@dataclass(frozen=True)
class TeamSpecialistQueueSlaScoreConfig:
    config_version: str = DEFAULT_TEAM_SPECIALIST_QUEUE_SLA_SCORE_CONFIG_VERSION
    research_sla_hours: Decimal = Decimal("24.000000")
    oldest_age_weight: Decimal = Decimal("0.300000")
    over_sla_share_weight: Decimal = Decimal("0.250000")
    average_age_weight: Decimal = Decimal("0.350000")
    queue_load_weight: Decimal = Decimal("0.100000")
    watch_sla_ratio: Decimal = Decimal("0.750000")
    block_sla_ratio: Decimal = Decimal("1.000000")
    over_sla_share_watch_floor: Decimal = Decimal("0.100000")
    over_sla_share_block_floor: Decimal = Decimal("0.500000")
    score_watch_floor: Decimal = Decimal("0.500000")
    score_block_floor: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        object.__setattr__(
            self,
            "research_sla_hours",
            _normalize_positive_decimal("research_sla_hours", self.research_sla_hours),
        )
        for field_name in (
            "oldest_age_weight",
            "over_sla_share_weight",
            "average_age_weight",
            "queue_load_weight",
            "watch_sla_ratio",
            "block_sla_ratio",
            "over_sla_share_watch_floor",
            "over_sla_share_block_floor",
            "score_watch_floor",
            "score_block_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("TeamSpecialistQueueSlaScoreConfig", self)
        _reject_public_payload(
            "TeamSpecialistQueueSlaScoreConfig",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistQueueSlaScoreInput:
    team_id: str
    specialist_id: str
    open_research_item_count: Decimal
    items_over_sla_count: Decimal
    oldest_item_age_hours: Decimal
    average_item_age_hours: Decimal
    manual_research_capacity_per_day: Decimal
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
        for field_name in ("open_research_item_count", "items_over_sla_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("oldest_item_age_hours", "average_item_age_hours"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "manual_research_capacity_per_day",
            _normalize_positive_decimal(
                "manual_research_capacity_per_day",
                self.manual_research_capacity_per_day,
            ),
        )
        if self.items_over_sla_count > self.open_research_item_count:
            raise ValueError(
                "items_over_sla_count must not exceed open_research_item_count",
            )
        _require_hard_flags("TeamSpecialistQueueSlaScoreInput", self)
        _reject_public_payload(
            "TeamSpecialistQueueSlaScoreInput",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistQueueSlaScoreReport:
    config: TeamSpecialistQueueSlaScoreConfig
    team_id: str
    specialist_id: str
    open_research_item_count: Decimal
    items_over_sla_count: Decimal
    oldest_item_age_hours: Decimal
    average_item_age_hours: Decimal
    manual_research_capacity_per_day: Decimal
    uncapped_queue_load_ratio: Decimal
    queue_load_ratio: Decimal
    over_sla_item_ratio: Decimal
    oldest_age_sla_ratio: Decimal
    average_age_sla_ratio: Decimal
    queue_sla_score: Decimal
    sla_status: str
    manual_research_priority_status: str
    report_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self.config) is not TeamSpecialistQueueSlaScoreConfig:
            raise ValueError("config must be a TeamSpecialistQueueSlaScoreConfig")
        _require_hard_flags("TeamSpecialistQueueSlaScoreConfig", self.config)
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
        for field_name in ("open_research_item_count", "items_over_sla_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "oldest_item_age_hours",
            "average_item_age_hours",
            "manual_research_capacity_per_day",
            "uncapped_queue_load_ratio",
            "queue_load_ratio",
            "over_sla_item_ratio",
            "oldest_age_sla_ratio",
            "average_age_sla_ratio",
            "queue_sla_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.manual_research_capacity_per_day <= ZERO:
            raise ValueError("manual_research_capacity_per_day must be positive")
        if self.items_over_sla_count > self.open_research_item_count:
            raise ValueError(
                "items_over_sla_count must not exceed open_research_item_count",
            )
        _require_status("sla_status", self.sla_status)
        _require_status(
            "manual_research_priority_status",
            self.manual_research_priority_status,
        )
        _require_status("report_status", self.report_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("TeamSpecialistQueueSlaScoreReport", self)
        _reject_public_payload(
            "TeamSpecialistQueueSlaScoreReport",
            _payload_value(asdict(self)),
        )
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, Any]:
        payload = _payload_value(asdict(self))
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        _reject_public_payload("TeamSpecialistQueueSlaScoreReport.payload", payload)
        _verify_payload_digest(payload)
        return payload


def score_team_specialist_queue_sla(
    queue_signal: TeamSpecialistQueueSlaScoreInput,
    *,
    config: TeamSpecialistQueueSlaScoreConfig | None = None,
) -> TeamSpecialistQueueSlaScoreReport:
    if type(queue_signal) is not TeamSpecialistQueueSlaScoreInput:
        raise ValueError("queue_signal must be a TeamSpecialistQueueSlaScoreInput")
    if config is None:
        config = TeamSpecialistQueueSlaScoreConfig()
    if type(config) is not TeamSpecialistQueueSlaScoreConfig:
        raise ValueError("config must be a TeamSpecialistQueueSlaScoreConfig")
    _require_hard_flags("TeamSpecialistQueueSlaScoreInput", queue_signal)
    _require_hard_flags("TeamSpecialistQueueSlaScoreConfig", config)

    uncapped_load = _uncapped_queue_load_ratio(queue_signal)
    capped_load = _clamp_ratio(uncapped_load)
    over_sla_share = _over_sla_item_ratio(queue_signal)
    oldest_ratio = _oldest_age_sla_ratio(queue_signal, config)
    average_ratio = _average_age_sla_ratio(queue_signal, config)
    score = _queue_sla_score(
        config=config,
        queue_load_ratio=capped_load,
        over_sla_item_ratio=over_sla_share,
        oldest_age_sla_ratio=oldest_ratio,
        average_age_sla_ratio=average_ratio,
    )
    sla_status = _sla_status(
        config=config,
        uncapped_queue_load_ratio=uncapped_load,
        over_sla_item_ratio=over_sla_share,
        oldest_age_sla_ratio=oldest_ratio,
        average_age_sla_ratio=average_ratio,
        queue_sla_score=score,
    )
    manual_priority = _manual_research_priority_status(sla_status)
    values: dict[str, object] = {
        "config": config,
        "team_id": queue_signal.team_id,
        "specialist_id": queue_signal.specialist_id,
        "open_research_item_count": queue_signal.open_research_item_count,
        "items_over_sla_count": queue_signal.items_over_sla_count,
        "oldest_item_age_hours": queue_signal.oldest_item_age_hours,
        "average_item_age_hours": queue_signal.average_item_age_hours,
        "manual_research_capacity_per_day": (
            queue_signal.manual_research_capacity_per_day
        ),
        "uncapped_queue_load_ratio": uncapped_load,
        "queue_load_ratio": capped_load,
        "over_sla_item_ratio": over_sla_share,
        "oldest_age_sla_ratio": oldest_ratio,
        "average_age_sla_ratio": average_ratio,
        "queue_sla_score": score,
        "sla_status": sla_status,
        "manual_research_priority_status": manual_priority,
        "report_status": manual_priority,
        "reason_codes": _reason_codes(
            config=config,
            sla_status=sla_status,
            uncapped_queue_load_ratio=uncapped_load,
            over_sla_item_ratio=over_sla_share,
            oldest_age_sla_ratio=oldest_ratio,
            average_age_sla_ratio=average_ratio,
        ),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _derived_validation_digest(values)
    return TeamSpecialistQueueSlaScoreReport(**values)


def team_specialist_queue_sla_score_payload(
    report: TeamSpecialistQueueSlaScoreReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is TeamSpecialistQueueSlaScoreReport:
        _require_hard_flags("TeamSpecialistQueueSlaScoreReport", report)
        return report.payload
    if type(report) is dict:
        payload = _payload_value(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a dict")
        _reject_public_payload("TeamSpecialistQueueSlaScoreReport.payload", payload)
        _require_hard_flags("payload", _DictFlags(payload))
        _verify_payload_digest(payload)
        return payload
    raise ValueError("report must be a TeamSpecialistQueueSlaScoreReport")


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


def _uncapped_queue_load_ratio(queue_signal: TeamSpecialistQueueSlaScoreInput) -> Decimal:
    return _ratio(
        queue_signal.open_research_item_count,
        queue_signal.manual_research_capacity_per_day,
    )


def _over_sla_item_ratio(queue_signal: TeamSpecialistQueueSlaScoreInput) -> Decimal:
    if queue_signal.open_research_item_count == ZERO:
        return ZERO
    return _clamp_ratio(
        _ratio(queue_signal.items_over_sla_count, queue_signal.open_research_item_count),
    )


def _oldest_age_sla_ratio(
    queue_signal: TeamSpecialistQueueSlaScoreInput,
    config: TeamSpecialistQueueSlaScoreConfig,
) -> Decimal:
    return _clamp_ratio(_ratio(queue_signal.oldest_item_age_hours, config.research_sla_hours))


def _average_age_sla_ratio(
    queue_signal: TeamSpecialistQueueSlaScoreInput,
    config: TeamSpecialistQueueSlaScoreConfig,
) -> Decimal:
    return _clamp_ratio(_ratio(queue_signal.average_item_age_hours, config.research_sla_hours))


def _queue_sla_score(
    *,
    config: TeamSpecialistQueueSlaScoreConfig,
    queue_load_ratio: Decimal,
    over_sla_item_ratio: Decimal,
    oldest_age_sla_ratio: Decimal,
    average_age_sla_ratio: Decimal,
) -> Decimal:
    if (
        queue_load_ratio >= config.block_sla_ratio
        and oldest_age_sla_ratio >= config.block_sla_ratio
        and average_age_sla_ratio >= config.block_sla_ratio
        and over_sla_item_ratio >= config.over_sla_share_block_floor
    ):
        return ONE
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            oldest_age_sla_ratio * config.oldest_age_weight
            + over_sla_item_ratio * config.over_sla_share_weight
            + average_age_sla_ratio * config.average_age_weight
            + queue_load_ratio * config.queue_load_weight,
        )


def _sla_status(
    *,
    config: TeamSpecialistQueueSlaScoreConfig,
    uncapped_queue_load_ratio: Decimal,
    over_sla_item_ratio: Decimal,
    oldest_age_sla_ratio: Decimal,
    average_age_sla_ratio: Decimal,
    queue_sla_score: Decimal,
) -> str:
    if (
        queue_sla_score >= config.score_block_floor
        or uncapped_queue_load_ratio >= config.block_sla_ratio
        or over_sla_item_ratio >= config.over_sla_share_block_floor
        or oldest_age_sla_ratio >= config.block_sla_ratio
        or average_age_sla_ratio >= config.block_sla_ratio
    ):
        return "block"
    if (
        queue_sla_score >= config.score_watch_floor
        or uncapped_queue_load_ratio >= config.watch_sla_ratio
        or over_sla_item_ratio >= config.over_sla_share_watch_floor
        or oldest_age_sla_ratio >= config.watch_sla_ratio
        or average_age_sla_ratio >= config.watch_sla_ratio
    ):
        return "watch"
    return "pass"


def _manual_research_priority_status(sla_status: str) -> str:
    return sla_status


def _reason_codes(
    *,
    config: TeamSpecialistQueueSlaScoreConfig,
    sla_status: str,
    uncapped_queue_load_ratio: Decimal,
    over_sla_item_ratio: Decimal,
    oldest_age_sla_ratio: Decimal,
    average_age_sla_ratio: Decimal,
) -> tuple[str, ...]:
    reasons = [
        f"queue_sla_{sla_status}",
        _age_reason(
            oldest_age_sla_ratio,
            config=config,
            clear_reason="oldest_age_clear",
            watch_reason="oldest_age_watch",
            block_reason="oldest_age_over_sla",
        ),
        _over_sla_share_reason(over_sla_item_ratio, config),
        _age_reason(
            average_age_sla_ratio,
            config=config,
            clear_reason="average_age_clear",
            watch_reason="average_age_watch",
            block_reason="average_age_over_sla",
        ),
        _manual_capacity_reason(uncapped_queue_load_ratio, config),
    ]
    return _normalize_reason_codes("reason_codes", tuple(reasons))


def _age_reason(
    value: Decimal,
    *,
    config: TeamSpecialistQueueSlaScoreConfig,
    clear_reason: str,
    watch_reason: str,
    block_reason: str,
) -> str:
    if value >= config.block_sla_ratio:
        return block_reason
    if value >= config.watch_sla_ratio:
        return watch_reason
    return clear_reason


def _over_sla_share_reason(
    over_sla_item_ratio: Decimal,
    config: TeamSpecialistQueueSlaScoreConfig,
) -> str:
    if over_sla_item_ratio >= config.over_sla_share_block_floor:
        return "over_sla_items_block"
    if over_sla_item_ratio > ZERO:
        return "over_sla_items_watch"
    return "over_sla_items_clear"


def _manual_capacity_reason(
    uncapped_queue_load_ratio: Decimal,
    config: TeamSpecialistQueueSlaScoreConfig,
) -> str:
    if uncapped_queue_load_ratio >= config.block_sla_ratio:
        return "manual_capacity_block"
    if uncapped_queue_load_ratio >= config.watch_sla_ratio:
        return "manual_capacity_watch"
    return "manual_capacity_clear"


def _validate_config(config: TeamSpecialistQueueSlaScoreConfig) -> None:
    with localcontext(DECIMAL_CONTEXT):
        weights_total = (
            config.oldest_age_weight
            + config.over_sla_share_weight
            + config.average_age_weight
            + config.queue_load_weight
        ).quantize(SCORE_QUANT)
    if weights_total != ONE:
        raise ValueError("score weights must sum to 1.000000")
    if config.watch_sla_ratio > config.block_sla_ratio:
        raise ValueError("watch_sla_ratio must not exceed block_sla_ratio")
    if config.over_sla_share_watch_floor > config.over_sla_share_block_floor:
        raise ValueError(
            "over_sla_share_watch_floor must not exceed over_sla_share_block_floor",
        )
    if config.score_watch_floor > config.score_block_floor:
        raise ValueError("score_watch_floor must not exceed score_block_floor")


def _validate_report_consistency(report: TeamSpecialistQueueSlaScoreReport) -> None:
    expected_uncapped_load = _uncapped_queue_load_ratio(report)
    if report.uncapped_queue_load_ratio != expected_uncapped_load:
        raise ValueError("uncapped_queue_load_ratio must match input fields")
    expected_capped_load = _clamp_ratio(expected_uncapped_load)
    if report.queue_load_ratio != expected_capped_load:
        raise ValueError("queue_load_ratio must match input fields")
    expected_over_sla_share = _over_sla_item_ratio(report)
    if report.over_sla_item_ratio != expected_over_sla_share:
        raise ValueError("over_sla_item_ratio must match input fields")
    expected_oldest_ratio = _oldest_age_sla_ratio(report, report.config)
    if report.oldest_age_sla_ratio != expected_oldest_ratio:
        raise ValueError("oldest_age_sla_ratio must match input fields")
    expected_average_ratio = _average_age_sla_ratio(report, report.config)
    if report.average_age_sla_ratio != expected_average_ratio:
        raise ValueError("average_age_sla_ratio must match input fields")
    expected_score = _queue_sla_score(
        config=report.config,
        queue_load_ratio=report.queue_load_ratio,
        over_sla_item_ratio=report.over_sla_item_ratio,
        oldest_age_sla_ratio=report.oldest_age_sla_ratio,
        average_age_sla_ratio=report.average_age_sla_ratio,
    )
    if report.queue_sla_score != expected_score:
        raise ValueError("queue_sla_score must match components")
    expected_sla_status = _sla_status(
        config=report.config,
        uncapped_queue_load_ratio=report.uncapped_queue_load_ratio,
        over_sla_item_ratio=report.over_sla_item_ratio,
        oldest_age_sla_ratio=report.oldest_age_sla_ratio,
        average_age_sla_ratio=report.average_age_sla_ratio,
        queue_sla_score=report.queue_sla_score,
    )
    if report.sla_status != expected_sla_status:
        raise ValueError("sla_status must match score")
    expected_manual_priority = _manual_research_priority_status(report.sla_status)
    if report.manual_research_priority_status != expected_manual_priority:
        raise ValueError("manual_research_priority_status must match score")
    if report.report_status != report.manual_research_priority_status:
        raise ValueError("report_status must match manual_research_priority_status")
    expected_reasons = _reason_codes(
        config=report.config,
        sla_status=report.sla_status,
        uncapped_queue_load_ratio=report.uncapped_queue_load_ratio,
        over_sla_item_ratio=report.over_sla_item_ratio,
        oldest_age_sla_ratio=report.oldest_age_sla_ratio,
        average_age_sla_ratio=report.average_age_sla_ratio,
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
    if type(value) is not str or value not in TEAM_SPECIALIST_QUEUE_SLA_SCORE_STATUSES:
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
