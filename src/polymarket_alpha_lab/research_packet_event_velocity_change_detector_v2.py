"""Read-only event velocity change report for supplied research packets."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_PACKET_EVENT_VELOCITY_CHANGE_CONFIG_VERSION = (
    "research-packet-event-velocity-change-v2"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
VALUE_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")

REPORT_STATUSES = ("pass", "watch", "blocked")
ROW_STATUSES = ("pass", "watch", "blocked")
ROW_REASON_CODES = (
    "probability_movement_material",
    "source_arrival_rate_increased",
    "official_source_update_missing",
    "official_source_update_lagged",
    "contradiction_delta_elevated",
    "resolution_horizon_compressed",
    "resolution_horizon_near",
    "liquidity_movement_material",
    "event_velocity_change_clear",
)
REPORT_REASON_CODES = (
    "event_velocity_change_clear",
    "event_velocity_change_watch",
    "event_velocity_change_blocked",
    "probability_movement_material",
    "source_arrival_rate_increased",
    "official_source_update_missing",
    "official_source_update_lagged",
    "contradiction_delta_elevated",
    "resolution_horizon_compressed",
    "resolution_horizon_near",
    "liquidity_movement_material",
)
UNSAFE_PUBLIC_TERMS = (
    "li" + "ve",
    "au" + "th",
    "wal" + "let",
    "or" + "der",
    "net" + "work",
    "data" + "base",
    "per" + "sist",
    "sign" + "ing",
    "mu" + "tation",
    "bu" + "y",
    "se" + "ll",
    "tra" + "de",
)
SAFETY_FLAG_NAMES = frozenset(("paper_only", "report_only", "readonly"))


@dataclass(frozen=True)
class ResearchPacketEventVelocityChangeConfig:
    config_version: str = DEFAULT_RESEARCH_PACKET_EVENT_VELOCITY_CHANGE_CONFIG_VERSION
    probability_movement_threshold: Decimal = Decimal("0.050000")
    source_arrival_delta_threshold: Decimal = Decimal("3")
    official_source_update_lag_threshold_seconds: Decimal = Decimal("1800")
    contradiction_delta_threshold: Decimal = Decimal("1")
    resolution_horizon_compression_threshold_seconds: Decimal = Decimal("21600")
    near_resolution_horizon_seconds: Decimal = Decimal("21600")
    liquidity_movement_threshold: Decimal = Decimal("1000.000000")
    blocked_score_threshold: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketEventVelocityChangeConfig:
            raise TypeError(
                "ResearchPacketEventVelocityChangeConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketEventVelocityChangeConfig:
            raise ValueError(
                "config must be exactly ResearchPacketEventVelocityChangeConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_PACKET_EVENT_VELOCITY_CHANGE_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "source_arrival_delta_threshold",
            "official_source_update_lag_threshold_seconds",
            "contradiction_delta_threshold",
            "resolution_horizon_compression_threshold_seconds",
            "near_resolution_horizon_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "probability_movement_threshold",
            "blocked_score_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "liquidity_movement_threshold",
            _normalize_positive_value(
                "liquidity_movement_threshold",
                self.liquidity_movement_threshold,
            ),
        )
        _require_hard_flags("ResearchPacketEventVelocityChangeConfig", self)


@dataclass(frozen=True)
class ResearchPacketEventVelocityChangeInput:
    packet_id: str
    event_title: str
    previous_probability: Decimal
    current_probability: Decimal
    previous_source_arrivals_24h: Decimal
    current_source_arrivals_24h: Decimal
    last_market_update_at: datetime | None
    latest_official_source_update_at: datetime | None
    previous_contradiction_count: Decimal
    current_contradiction_count: Decimal
    previous_resolution_horizon_seconds: Decimal
    current_resolution_horizon_seconds: Decimal
    previous_liquidity: Decimal
    current_liquidity: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketEventVelocityChangeInput:
            raise TypeError(
                "ResearchPacketEventVelocityChangeInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketEventVelocityChangeInput:
            raise ValueError(
                "input must be exactly ResearchPacketEventVelocityChangeInput",
            )
        for field_name in ("packet_id", "event_title"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in ("previous_probability", "current_probability"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "previous_source_arrivals_24h",
            "current_source_arrivals_24h",
            "previous_contradiction_count",
            "current_contradiction_count",
            "previous_resolution_horizon_seconds",
            "current_resolution_horizon_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("last_market_update_at", "latest_official_source_update_at"):
            object.__setattr__(
                self,
                field_name,
                _as_optional_utc(field_name, getattr(self, field_name)),
            )
        for field_name in ("previous_liquidity", "current_liquidity"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_value(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("ResearchPacketEventVelocityChangeInput", self)


@dataclass(frozen=True)
class ResearchPacketEventVelocityChangeRow:
    packet_id: str
    event_title: str
    previous_probability: Decimal
    current_probability: Decimal
    probability_move: Decimal
    absolute_probability_move: Decimal
    previous_source_arrivals_24h: Decimal
    current_source_arrivals_24h: Decimal
    source_arrival_delta_24h: Decimal
    last_market_update_at: datetime | None
    latest_official_source_update_at: datetime | None
    official_source_update_lag_seconds: Decimal | None
    previous_contradiction_count: Decimal
    current_contradiction_count: Decimal
    contradiction_delta: Decimal
    previous_resolution_horizon_seconds: Decimal
    current_resolution_horizon_seconds: Decimal
    resolution_horizon_compression_seconds: Decimal
    previous_liquidity: Decimal
    current_liquidity: Decimal
    liquidity_move: Decimal
    absolute_liquidity_move: Decimal
    event_velocity_change_score: Decimal
    velocity_change_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketEventVelocityChangeRow:
            raise TypeError(
                "ResearchPacketEventVelocityChangeRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketEventVelocityChangeRow:
            raise ValueError("row must be exactly ResearchPacketEventVelocityChangeRow")
        for field_name in ("packet_id", "event_title"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in ("previous_probability", "current_probability"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "probability_move",
            _normalize_probability_delta("probability_move", self.probability_move),
        )
        object.__setattr__(
            self,
            "absolute_probability_move",
            _normalize_probability("absolute_probability_move", self.absolute_probability_move),
        )
        for field_name in (
            "previous_source_arrivals_24h",
            "current_source_arrivals_24h",
            "previous_contradiction_count",
            "current_contradiction_count",
            "previous_resolution_horizon_seconds",
            "current_resolution_horizon_seconds",
            "resolution_horizon_compression_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("source_arrival_delta_24h", "contradiction_delta"):
            object.__setattr__(
                self,
                field_name,
                _normalize_signed_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("last_market_update_at", "latest_official_source_update_at"):
            object.__setattr__(
                self,
                field_name,
                _as_optional_utc(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "official_source_update_lag_seconds",
            _normalize_optional_nonnegative_count(
                "official_source_update_lag_seconds",
                self.official_source_update_lag_seconds,
            ),
        )
        for field_name in (
            "previous_liquidity",
            "current_liquidity",
            "absolute_liquidity_move",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_value(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "liquidity_move",
            _normalize_value("liquidity_move", self.liquidity_move),
        )
        object.__setattr__(
            self,
            "event_velocity_change_score",
            _normalize_probability(
                "event_velocity_change_score",
                self.event_velocity_change_score,
            ),
        )
        _require_member("velocity_change_status", self.velocity_change_status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("ResearchPacketEventVelocityChangeRow", self)
        _validate_digest(self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchPacketEventVelocityChangeReport:
    generated_at: datetime
    config_version: str
    packet_count: Decimal
    pass_packet_count: Decimal
    watch_packet_count: Decimal
    blocked_packet_count: Decimal
    probability_movement_count: Decimal
    source_arrival_rate_increase_count: Decimal
    official_source_update_lag_count: Decimal
    contradiction_delta_count: Decimal
    resolution_horizon_compression_count: Decimal
    near_resolution_horizon_count: Decimal
    liquidity_movement_count: Decimal
    max_event_velocity_change_score: Decimal
    max_official_source_update_lag_seconds: Decimal | None
    min_current_resolution_horizon_seconds: Decimal | None
    report_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchPacketEventVelocityChangeRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketEventVelocityChangeReport:
            raise TypeError(
                "ResearchPacketEventVelocityChangeReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketEventVelocityChangeReport:
            raise ValueError(
                "report must be exactly ResearchPacketEventVelocityChangeReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "packet_count",
            "pass_packet_count",
            "watch_packet_count",
            "blocked_packet_count",
            "probability_movement_count",
            "source_arrival_rate_increase_count",
            "official_source_update_lag_count",
            "contradiction_delta_count",
            "resolution_horizon_compression_count",
            "near_resolution_horizon_count",
            "liquidity_movement_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_event_velocity_change_score",
            _normalize_probability(
                "max_event_velocity_change_score",
                self.max_event_velocity_change_score,
            ),
        )
        for field_name in (
            "max_official_source_update_lag_seconds",
            "min_current_resolution_horizon_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_member("report_status", self.report_status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("ResearchPacketEventVelocityChangeReport", self)
        _validate_digest(self)
        _validate_report_counts(self)


def build_research_packet_event_velocity_change_report(
    inputs: list[ResearchPacketEventVelocityChangeInput]
    | tuple[ResearchPacketEventVelocityChangeInput, ...],
    *,
    config: ResearchPacketEventVelocityChangeConfig,
    generated_at: datetime,
) -> ResearchPacketEventVelocityChangeReport:
    if type(config) is not ResearchPacketEventVelocityChangeConfig:
        raise ValueError("config must be a ResearchPacketEventVelocityChangeConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    _validate_input_times(normalized_inputs, generated_at_utc)
    rows = tuple(
        sorted(
            (
                _row_from_input(
                    item,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for item in normalized_inputs
            ),
            key=_row_sort_key,
        ),
    )
    return ResearchPacketEventVelocityChangeReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        packet_count=_count(len(rows)),
        pass_packet_count=_status_count(rows, "pass"),
        watch_packet_count=_status_count(rows, "watch"),
        blocked_packet_count=_status_count(rows, "blocked"),
        probability_movement_count=_reason_count(
            rows,
            "probability_movement_material",
        ),
        source_arrival_rate_increase_count=_reason_count(
            rows,
            "source_arrival_rate_increased",
        ),
        official_source_update_lag_count=_reason_count(
            rows,
            "official_source_update_lagged",
        ),
        contradiction_delta_count=_reason_count(rows, "contradiction_delta_elevated"),
        resolution_horizon_compression_count=_reason_count(
            rows,
            "resolution_horizon_compressed",
        ),
        near_resolution_horizon_count=_reason_count(rows, "resolution_horizon_near"),
        liquidity_movement_count=_reason_count(rows, "liquidity_movement_material"),
        max_event_velocity_change_score=_max_score(rows),
        max_official_source_update_lag_seconds=_max_optional_count(
            tuple(row.official_source_update_lag_seconds for row in rows),
        ),
        min_current_resolution_horizon_seconds=_min_optional_count(
            tuple(row.current_resolution_horizon_seconds for row in rows),
        ),
        report_status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_packet_event_velocity_change_report_payload(
    report: ResearchPacketEventVelocityChangeReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchPacketEventVelocityChangeReport:
        _require_hard_flags("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchPacketEventVelocityChangeReport or payload")
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _require_payload_flags(payload)
    _reject_unsafe_public_payload("payload", payload)
    _validate_payload_digest(payload)
    return payload


def _normalize_inputs(
    inputs: list[ResearchPacketEventVelocityChangeInput]
    | tuple[ResearchPacketEventVelocityChangeInput, ...],
) -> tuple[ResearchPacketEventVelocityChangeInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    normalized = tuple(inputs)
    seen_packet_ids: set[str] = set()
    for item in normalized:
        if type(item) is not ResearchPacketEventVelocityChangeInput:
            raise ValueError(
                "inputs must contain ResearchPacketEventVelocityChangeInput values",
            )
        _require_hard_flags("input", item)
        if item.packet_id in seen_packet_ids:
            raise ValueError("inputs must not contain duplicate packet_id values")
        seen_packet_ids.add(item.packet_id)
    return normalized


def _validate_input_times(
    rows: tuple[ResearchPacketEventVelocityChangeInput, ...],
    generated_at: datetime,
) -> None:
    for row in rows:
        for value in (row.last_market_update_at, row.latest_official_source_update_at):
            if value is not None and value > generated_at:
                raise ValueError("timestamps must not be after generated_at")


def _row_from_input(
    item: ResearchPacketEventVelocityChangeInput,
    *,
    config: ResearchPacketEventVelocityChangeConfig,
    generated_at: datetime,
) -> ResearchPacketEventVelocityChangeRow:
    probability_move = _quantize_ratio(item.current_probability - item.previous_probability)
    source_arrival_delta = item.current_source_arrivals_24h - item.previous_source_arrivals_24h
    official_source_update_lag = _official_source_update_lag_seconds(
        item.last_market_update_at,
        item.latest_official_source_update_at,
        generated_at,
    )
    contradiction_delta = item.current_contradiction_count - item.previous_contradiction_count
    resolution_horizon_compression = _compression_seconds(
        item.previous_resolution_horizon_seconds,
        item.current_resolution_horizon_seconds,
    )
    liquidity_move = _quantize_value(item.current_liquidity - item.previous_liquidity)
    reason_codes = _row_reason_codes(
        item,
        config=config,
        absolute_probability_move=abs(probability_move),
        source_arrival_delta=source_arrival_delta,
        official_source_update_lag=official_source_update_lag,
        contradiction_delta=contradiction_delta,
        resolution_horizon_compression=resolution_horizon_compression,
        absolute_liquidity_move=abs(liquidity_move),
    )
    score = _event_velocity_change_score(reason_codes)
    return ResearchPacketEventVelocityChangeRow(
        packet_id=item.packet_id,
        event_title=item.event_title,
        previous_probability=item.previous_probability,
        current_probability=item.current_probability,
        probability_move=probability_move,
        absolute_probability_move=abs(probability_move),
        previous_source_arrivals_24h=item.previous_source_arrivals_24h,
        current_source_arrivals_24h=item.current_source_arrivals_24h,
        source_arrival_delta_24h=source_arrival_delta,
        last_market_update_at=item.last_market_update_at,
        latest_official_source_update_at=item.latest_official_source_update_at,
        official_source_update_lag_seconds=official_source_update_lag,
        previous_contradiction_count=item.previous_contradiction_count,
        current_contradiction_count=item.current_contradiction_count,
        contradiction_delta=contradiction_delta,
        previous_resolution_horizon_seconds=item.previous_resolution_horizon_seconds,
        current_resolution_horizon_seconds=item.current_resolution_horizon_seconds,
        resolution_horizon_compression_seconds=resolution_horizon_compression,
        previous_liquidity=item.previous_liquidity,
        current_liquidity=item.current_liquidity,
        liquidity_move=liquidity_move,
        absolute_liquidity_move=abs(liquidity_move),
        event_velocity_change_score=score,
        velocity_change_status=_row_status(score, reason_codes, config=config),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: ResearchPacketEventVelocityChangeInput,
    *,
    config: ResearchPacketEventVelocityChangeConfig,
    absolute_probability_move: Decimal,
    source_arrival_delta: Decimal,
    official_source_update_lag: Decimal | None,
    contradiction_delta: Decimal,
    resolution_horizon_compression: Decimal,
    absolute_liquidity_move: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if absolute_probability_move >= config.probability_movement_threshold:
        reason_codes.append("probability_movement_material")
    if source_arrival_delta >= config.source_arrival_delta_threshold:
        reason_codes.append("source_arrival_rate_increased")
    if item.latest_official_source_update_at is None:
        reason_codes.append("official_source_update_missing")
    elif (
        official_source_update_lag is not None
        and official_source_update_lag >= config.official_source_update_lag_threshold_seconds
    ):
        reason_codes.append("official_source_update_lagged")
    if contradiction_delta >= config.contradiction_delta_threshold:
        reason_codes.append("contradiction_delta_elevated")
    if resolution_horizon_compression >= config.resolution_horizon_compression_threshold_seconds:
        reason_codes.append("resolution_horizon_compressed")
    if item.current_resolution_horizon_seconds <= config.near_resolution_horizon_seconds:
        reason_codes.append("resolution_horizon_near")
    if absolute_liquidity_move >= config.liquidity_movement_threshold:
        reason_codes.append("liquidity_movement_material")
    if not reason_codes:
        reason_codes.append("event_velocity_change_clear")
    return tuple(reason_codes)


def _event_velocity_change_score(reason_codes: tuple[str, ...]) -> Decimal:
    if reason_codes == ("event_velocity_change_clear",):
        return ZERO_RATIO
    score = Decimal("0.050000")
    for reason_code in reason_codes:
        if reason_code == "probability_movement_material":
            score += Decimal("0.150000")
        elif reason_code == "source_arrival_rate_increased":
            score += Decimal("0.100000")
        elif reason_code in ("official_source_update_missing", "official_source_update_lagged"):
            score += Decimal("0.150000")
        elif reason_code == "contradiction_delta_elevated":
            score += Decimal("0.200000")
        elif reason_code == "resolution_horizon_compressed":
            score += Decimal("0.100000")
        elif reason_code == "resolution_horizon_near":
            score += Decimal("0.100000")
        elif reason_code == "liquidity_movement_material":
            score += Decimal("0.100000")
    if score > ONE_RATIO:
        return ONE_RATIO
    return _quantize_ratio(score)


def _row_status(
    score: Decimal,
    reason_codes: tuple[str, ...],
    *,
    config: ResearchPacketEventVelocityChangeConfig,
) -> str:
    if reason_codes == ("event_velocity_change_clear",):
        return "pass"
    if score >= config.blocked_score_threshold:
        return "blocked"
    return "watch"


def _row_sort_key(row: ResearchPacketEventVelocityChangeRow) -> tuple[Decimal, Decimal, Decimal, str]:
    status_weight = {
        "blocked": Decimal("0"),
        "watch": Decimal("1"),
        "pass": Decimal("2"),
    }[row.velocity_change_status]
    return (
        status_weight,
        ONE_RATIO - row.event_velocity_change_score,
        row.current_resolution_horizon_seconds,
        row.packet_id,
    )


def _status_count(
    rows: tuple[ResearchPacketEventVelocityChangeRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.velocity_change_status == status))


def _reason_count(
    rows: tuple[ResearchPacketEventVelocityChangeRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_score(rows: tuple[ResearchPacketEventVelocityChangeRow, ...]) -> Decimal:
    if not rows:
        return ZERO_RATIO
    return max(row.event_velocity_change_score for row in rows)


def _report_status(rows: tuple[ResearchPacketEventVelocityChangeRow, ...]) -> str:
    if any(row.velocity_change_status == "blocked" for row in rows):
        return "blocked"
    if any(row.velocity_change_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchPacketEventVelocityChangeRow, ...],
) -> tuple[str, ...]:
    status = _report_status(rows)
    reason_codes: list[str] = [
        "event_velocity_change_clear"
        if status == "pass"
        else f"event_velocity_change_{status}",
    ]
    for reason_code in ROW_REASON_CODES:
        if reason_code == "event_velocity_change_clear":
            continue
        if any(reason_code in row.reason_codes for row in rows):
            reason_codes.append(reason_code)
    return tuple(reason_codes)


def _normalize_rows(
    rows: tuple[ResearchPacketEventVelocityChangeRow, ...],
) -> tuple[ResearchPacketEventVelocityChangeRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen_packet_ids: set[str] = set()
    for row in rows:
        if type(row) is not ResearchPacketEventVelocityChangeRow:
            raise ValueError("rows must contain ResearchPacketEventVelocityChangeRow values")
        _require_hard_flags("row", row)
        if row.packet_id in seen_packet_ids:
            raise ValueError("rows must not contain duplicate packet_id values")
        seen_packet_ids.add(row.packet_id)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return rows


def _validate_row_consistency(row: ResearchPacketEventVelocityChangeRow) -> None:
    probability_move = _quantize_ratio(row.current_probability - row.previous_probability)
    if row.probability_move != probability_move:
        raise ValueError("probability_move must match current minus previous")
    if row.absolute_probability_move != abs(row.probability_move):
        raise ValueError("absolute_probability_move must match probability_move")
    if row.source_arrival_delta_24h != (
        row.current_source_arrivals_24h - row.previous_source_arrivals_24h
    ):
        raise ValueError("source_arrival_delta_24h must match source arrivals")
    if row.contradiction_delta != (
        row.current_contradiction_count - row.previous_contradiction_count
    ):
        raise ValueError("contradiction_delta must match contradiction counts")
    if row.resolution_horizon_compression_seconds != _compression_seconds(
        row.previous_resolution_horizon_seconds,
        row.current_resolution_horizon_seconds,
    ):
        raise ValueError("resolution_horizon_compression_seconds must match horizons")
    liquidity_move = _quantize_value(row.current_liquidity - row.previous_liquidity)
    if row.liquidity_move != liquidity_move:
        raise ValueError("liquidity_move must match current minus previous")
    if row.absolute_liquidity_move != abs(row.liquidity_move):
        raise ValueError("absolute_liquidity_move must match liquidity_move")


def _validate_report_counts(report: ResearchPacketEventVelocityChangeReport) -> None:
    if (
        report.pass_packet_count
        + report.watch_packet_count
        + report.blocked_packet_count
        != report.packet_count
    ):
        raise ValueError("status packet counts must equal packet_count")
    if report.packet_count != _count(len(report.rows)):
        raise ValueError("packet_count must equal row count")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _validate_digest(value: object) -> None:
    current_digest = getattr(value, "derived_validation_digest")
    if current_digest != "":
        _require_digest(current_digest)
    expected_digest = _derived_validation_digest(value)
    if current_digest == "":
        object.__setattr__(value, "derived_validation_digest", expected_digest)
        return
    if current_digest != expected_digest:
        raise ValueError("derived_validation_digest mismatch")


def _derived_validation_digest(value: object) -> str:
    payload = _json_ready(value, include_digest=False)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    if "derived_validation_digest" not in payload:
        raise ValueError("derived_validation_digest is required")
    current_digest = payload["derived_validation_digest"]
    if type(current_digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    _require_digest(current_digest)
    payload_without_digest = dict(payload)
    payload_without_digest["derived_validation_digest"] = ""
    expected_digest = _derived_validation_digest_from_payload(payload_without_digest)
    if current_digest != expected_digest:
        raise ValueError("derived_validation_digest mismatch")


def _derived_validation_digest_from_payload(payload: dict[str, Any]) -> str:
    canonical = _copy_without_digest(payload)
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _copy_without_digest(value: Any) -> Any:
    if isinstance(value, dict):
        copied: dict[str, Any] = {}
        for key, item in value.items():
            if key == "derived_validation_digest":
                continue
            copied[key] = _copy_without_digest(item)
        return copied
    if isinstance(value, list):
        return [_copy_without_digest(item) for item in value]
    return value


def _require_digest(value: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError("derived_validation_digest must be a lowercase sha256 hex string")


def _json_ready(value: Any, *, include_digest: bool = True) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        ready: dict[str, Any] = {}
        for field in fields(value):
            if not include_digest and field.name == "derived_validation_digest":
                continue
            ready[field.name] = _json_ready(
                getattr(value, field.name),
                include_digest=include_digest,
            )
        return ready
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return format(value, "f")
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, bool):
        return value
    if isinstance(value, (float, int)):
        raise ValueError("payload must not contain floats or ints")
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        ready = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            if not include_digest and key == "derived_validation_digest":
                continue
            ready[key] = _json_ready(item, include_digest=include_digest)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item, include_digest=include_digest) for item in value]
    if isinstance(value, list):
        return [_json_ready(item, include_digest=include_digest) for item in value]
    raise ValueError("payload contains unsupported value")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            if _contains_unsafe_public_term(key):
                raise ValueError(f"unsafe public key in {label}: {key}")
            item_path = key if path == "" else f"{path}.{key}"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(label, item, f"{path}[{index}]")
        return
    if isinstance(value, str) and _contains_unsafe_public_term(value):
        raise ValueError(f"unsafe public value in {label}: {path}")


def _contains_unsafe_public_term(value: str) -> bool:
    lowered = value.lower()
    return any(term in lowered for term in UNSAFE_PUBLIC_TERMS)


def _require_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in SAFETY_FLAG_NAMES:
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for payload")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in SAFETY_FLAG_NAMES:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_canonical_string(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() == "":
        raise ValueError(f"{field_name} must not be blank")
    if value != value.strip():
        raise ValueError(f"{field_name} must be canonical")
    if _contains_unsafe_public_term(value):
        raise ValueError(f"unsafe public value in {field_name}")
    return value


def _require_member(field_name: str, value: str, allowed_values: tuple[str, ...]) -> None:
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {', '.join(allowed_values)}")


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple or not values:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    normalized: list[str] = []
    seen_values: set[str] = set()
    for value in values:
        _require_canonical_string(field_name, value)
        _require_member(field_name, value, allowed_values)
        if value in seen_values:
            raise ValueError(f"{field_name} must not contain duplicates")
        normalized.append(value)
        seen_values.add(value)
    return tuple(normalized)


def _as_optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_probability(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value, RATIO_QUANTUM)
    if normalized < ZERO_RATIO or normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_positive_probability(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_probability(field_name, value)
    if normalized <= ZERO_RATIO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_probability_delta(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value, RATIO_QUANTUM)
    if normalized < -ONE_RATIO or normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must be between -1 and 1")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value, COUNT_QUANTUM)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_signed_count(field_name: str, value: Decimal) -> Decimal:
    return _normalize_decimal(field_name, value, COUNT_QUANTUM)


def _normalize_optional_nonnegative_count(
    field_name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_count(field_name, value)


def _normalize_nonnegative_value(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_value(field_name, value)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_value(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_value(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_value(field_name: str, value: Decimal) -> Decimal:
    return _normalize_decimal(field_name, value, VALUE_QUANTUM)


def _normalize_decimal(field_name: str, value: Decimal, quantum: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(quantum)
    if normalized != value:
        raise ValueError(f"{field_name} must align to {quantum}")
    return normalized


def _quantize_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _quantize_value(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(VALUE_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _official_source_update_lag_seconds(
    last_market_update_at: datetime | None,
    latest_official_source_update_at: datetime | None,
    generated_at: datetime,
) -> Decimal | None:
    if latest_official_source_update_at is None:
        return None
    if last_market_update_at is None:
        return _duration_seconds(latest_official_source_update_at, generated_at)
    if latest_official_source_update_at >= last_market_update_at:
        return ZERO_COUNT
    return _duration_seconds(latest_official_source_update_at, last_market_update_at)


def _duration_seconds(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    if delta.microseconds:
        seconds += Decimal(delta.microseconds) / Decimal("1000000")
    return _normalize_nonnegative_count("duration_seconds", seconds)


def _compression_seconds(previous: Decimal, current: Decimal) -> Decimal:
    compression = previous - current
    if compression < ZERO_COUNT:
        return ZERO_COUNT
    return _normalize_nonnegative_count("resolution_horizon_compression_seconds", compression)


def _max_optional_count(values: tuple[Decimal | None, ...]) -> Decimal | None:
    present = tuple(value for value in values if value is not None)
    if not present:
        return None
    return max(present)


def _min_optional_count(values: tuple[Decimal | None, ...]) -> Decimal | None:
    present = tuple(value for value in values if value is not None)
    if not present:
        return None
    return min(present)


__all__ = (
    "DEFAULT_RESEARCH_PACKET_EVENT_VELOCITY_CHANGE_CONFIG_VERSION",
    "ResearchPacketEventVelocityChangeConfig",
    "ResearchPacketEventVelocityChangeInput",
    "ResearchPacketEventVelocityChangeReport",
    "ResearchPacketEventVelocityChangeRow",
    "build_research_packet_event_velocity_change_report",
    "research_packet_event_velocity_change_report_payload",
)
