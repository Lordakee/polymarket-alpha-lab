"""Manual research priority report for fast-moving probability events."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any


DEFAULT_RESEARCH_STRATEGY_EVENT_VOLATILITY_PRIORITY_CONFIG_VERSION = (
    "research-strategy-event-volatility-priority-report"
)

STATUSES = ("pass", "watch", "block")

_QUANT = Decimal("0.000001")
_COUNT_QUANT = Decimal("1")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_TEXT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_HARD_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_UNSAFE_PUBLIC_KEY_TERMS = tuple(
    "".join(parts)
    for parts in (
        ("raw",),
        ("candidate",),
        ("market",),
        ("slug",),
        ("question",),
        ("url",),
        ("text",),
        ("dsn",),
        ("data", "source"),
        ("table",),
        ("token",),
        ("wa", "llet"),
        ("ord", "er"),
        ("trad", "e"),
        ("li", "ve"),
    )
)
_UNSAFE_PUBLIC_VALUE_TERMS = _UNSAFE_PUBLIC_KEY_TERMS + tuple(
    "".join(parts)
    for parts in (
        ("http://",),
        ("https://",),
        ("://",),
        ("secret",),
        ("auth",),
        ("private",),
        ("postgres",),
        ("sqlite",),
    )
)
_REASON_CODE_SEQUENCE = (
    "event_volatility_priority_empty",
    "event_volatility_priority_probability_volatility_block",
    "event_volatility_priority_evidence_churn_block",
    "event_volatility_priority_liquidity_reliability_block",
    "event_volatility_priority_cost_drag_block",
    "event_volatility_priority_resolution_proximity_block",
    "event_volatility_priority_probability_volatility_watch",
    "event_volatility_priority_evidence_churn_watch",
    "event_volatility_priority_liquidity_reliability_watch",
    "event_volatility_priority_cost_drag_watch",
    "event_volatility_priority_resolution_proximity_watch",
    "event_volatility_priority_clear",
)
_ROOT_PUBLIC_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "status",
        "event_count",
        "block_event_count",
        "watch_event_count",
        "pass_event_count",
        "manual_research_event_count",
        "manual_research_event_ratio",
        "max_manual_research_priority_score",
        "max_probability_volatility_score",
        "max_evidence_churn_score",
        "max_liquidity_reliability_gap_ratio",
        "max_cost_drag_ratio",
        "max_resolution_proximity_score",
        "rows",
        "reason_codes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_ROW_PUBLIC_FIELDS = frozenset(
    (
        "priority_rank",
        "event_reference_digest",
        "domain_id",
        "status",
        "manual_research_priority_score",
        "observed_at",
        "probability_previous",
        "probability_current",
        "probability_move",
        "probability_move_abs",
        "probability_velocity_24h",
        "probability_volatility_score",
        "evidence_update_count_24h",
        "conflicting_evidence_count_24h",
        "evidence_churn_score",
        "liquidity_depth_ratio",
        "liquidity_reliability_gap_ratio",
        "spread_cost_ratio",
        "fee_cost_ratio",
        "cost_drag_ratio",
        "resolution_at",
        "seconds_to_resolution",
        "resolution_proximity_score",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_COUNT_PUBLIC_FIELDS = frozenset(
    (
        "event_count",
        "block_event_count",
        "watch_event_count",
        "pass_event_count",
        "manual_research_event_count",
        "evidence_update_count_24h",
        "conflicting_evidence_count_24h",
    ),
)
_POSITIVE_DECIMAL_PUBLIC_FIELDS = frozenset(("priority_rank",))
_RATIO_PUBLIC_FIELDS = frozenset(
    (
        "manual_research_event_ratio",
        "max_manual_research_priority_score",
        "max_probability_volatility_score",
        "max_evidence_churn_score",
        "max_liquidity_reliability_gap_ratio",
        "max_cost_drag_ratio",
        "max_resolution_proximity_score",
        "manual_research_priority_score",
        "probability_previous",
        "probability_current",
        "probability_move_abs",
        "probability_volatility_score",
        "evidence_churn_score",
        "liquidity_depth_ratio",
        "liquidity_reliability_gap_ratio",
        "spread_cost_ratio",
        "fee_cost_ratio",
        "cost_drag_ratio",
        "resolution_proximity_score",
    ),
)
_SIGNED_RATIO_PUBLIC_FIELDS = frozenset(
    ("probability_move", "probability_velocity_24h"),
)
_NONNEGATIVE_DECIMAL_PUBLIC_FIELDS = frozenset(("seconds_to_resolution",))


@dataclass(frozen=True)
class ResearchStrategyEventVolatilityPriorityConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_EVENT_VOLATILITY_PRIORITY_CONFIG_VERSION
    )
    volatility_watch_ratio: Decimal = Decimal("0.050000")
    volatility_block_ratio: Decimal = Decimal("0.150000")
    evidence_churn_watch_score: Decimal = Decimal("0.250000")
    evidence_churn_block_score: Decimal = Decimal("0.750000")
    evidence_churn_block_count: Decimal = Decimal("8")
    liquidity_gap_watch_ratio: Decimal = Decimal("0.200000")
    liquidity_gap_block_ratio: Decimal = Decimal("0.500000")
    cost_drag_watch_ratio: Decimal = Decimal("0.030000")
    cost_drag_block_ratio: Decimal = Decimal("0.080000")
    resolution_proximity_watch_score: Decimal = Decimal("0.500000")
    resolution_proximity_block_score: Decimal = Decimal("0.900000")
    resolution_proximity_horizon_seconds: Decimal = Decimal("604800.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyEventVolatilityPriorityConfig:
            raise TypeError(
                "ResearchStrategyEventVolatilityPriorityConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyEventVolatilityPriorityConfig:
            raise ValueError(
                "config must be exactly ResearchStrategyEventVolatilityPriorityConfig",
            )
        _require_public_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_EVENT_VOLATILITY_PRIORITY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "volatility_watch_ratio",
            "volatility_block_ratio",
            "evidence_churn_watch_score",
            "evidence_churn_block_score",
            "liquidity_gap_watch_ratio",
            "liquidity_gap_block_ratio",
            "cost_drag_watch_ratio",
            "cost_drag_block_ratio",
            "resolution_proximity_watch_score",
            "resolution_proximity_block_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_churn_block_count",
            _normalize_positive_decimal(
                "evidence_churn_block_count",
                self.evidence_churn_block_count,
            ),
        )
        object.__setattr__(
            self,
            "resolution_proximity_horizon_seconds",
            _normalize_positive_decimal(
                "resolution_proximity_horizon_seconds",
                self.resolution_proximity_horizon_seconds,
            ),
        )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyEventVolatilityPriorityInput:
    private_event_reference: str
    domain_id: str
    observed_at: datetime
    probability_previous: Decimal
    probability_current: Decimal
    probability_velocity_24h: Decimal
    evidence_update_count_24h: Decimal
    conflicting_evidence_count_24h: Decimal
    liquidity_depth_ratio: Decimal
    spread_cost_ratio: Decimal
    fee_cost_ratio: Decimal
    resolution_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyEventVolatilityPriorityInput:
            raise TypeError(
                "ResearchStrategyEventVolatilityPriorityInput does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyEventVolatilityPriorityInput:
            raise ValueError(
                "event must be exactly ResearchStrategyEventVolatilityPriorityInput",
            )
        _require_private_reference("private_event_reference", self.private_event_reference)
        _require_public_text("domain_id", self.domain_id)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "resolution_at",
            _as_utc("resolution_at", self.resolution_at),
        )
        for field_name in ("probability_previous", "probability_current"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "probability_velocity_24h",
            _normalize_signed_ratio(
                "probability_velocity_24h",
                self.probability_velocity_24h,
            ),
        )
        for field_name in (
            "evidence_update_count_24h",
            "conflicting_evidence_count_24h",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("liquidity_depth_ratio", "spread_cost_ratio", "fee_cost_ratio"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("event", self)


@dataclass(frozen=True)
class ResearchStrategyEventVolatilityPriorityRow:
    priority_rank: Decimal
    event_reference_digest: str
    domain_id: str
    status: str
    manual_research_priority_score: Decimal
    observed_at: datetime
    probability_previous: Decimal
    probability_current: Decimal
    probability_move: Decimal
    probability_move_abs: Decimal
    probability_velocity_24h: Decimal
    probability_volatility_score: Decimal
    evidence_update_count_24h: Decimal
    conflicting_evidence_count_24h: Decimal
    evidence_churn_score: Decimal
    liquidity_depth_ratio: Decimal
    liquidity_reliability_gap_ratio: Decimal
    spread_cost_ratio: Decimal
    fee_cost_ratio: Decimal
    cost_drag_ratio: Decimal
    resolution_at: datetime
    seconds_to_resolution: Decimal
    resolution_proximity_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyEventVolatilityPriorityRow:
            raise TypeError(
                "ResearchStrategyEventVolatilityPriorityRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyEventVolatilityPriorityRow:
            raise ValueError("row must be exactly ResearchStrategyEventVolatilityPriorityRow")
        object.__setattr__(
            self,
            "priority_rank",
            _normalize_positive_decimal("priority_rank", self.priority_rank),
        )
        _require_sha256("event_reference_digest", self.event_reference_digest)
        _require_public_text("domain_id", self.domain_id)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "manual_research_priority_score",
            _normalize_ratio(
                "manual_research_priority_score",
                self.manual_research_priority_score,
            ),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "resolution_at",
            _as_utc("resolution_at", self.resolution_at),
        )
        for field_name in ("probability_previous", "probability_current"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("probability_move", "probability_velocity_24h"):
            object.__setattr__(
                self,
                field_name,
                _normalize_signed_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "probability_move_abs",
            "probability_volatility_score",
            "evidence_churn_score",
            "liquidity_depth_ratio",
            "liquidity_reliability_gap_ratio",
            "spread_cost_ratio",
            "fee_cost_ratio",
            "cost_drag_ratio",
            "resolution_proximity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "evidence_update_count_24h",
            "conflicting_evidence_count_24h",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "seconds_to_resolution",
            _normalize_nonnegative_decimal(
                "seconds_to_resolution",
                self.seconds_to_resolution,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchStrategyEventVolatilityPriorityReport:
    generated_at: datetime
    config_version: str
    status: str
    event_count: Decimal
    block_event_count: Decimal
    watch_event_count: Decimal
    pass_event_count: Decimal
    manual_research_event_count: Decimal
    manual_research_event_ratio: Decimal
    max_manual_research_priority_score: Decimal
    max_probability_volatility_score: Decimal
    max_evidence_churn_score: Decimal
    max_liquidity_reliability_gap_ratio: Decimal
    max_cost_drag_ratio: Decimal
    max_resolution_proximity_score: Decimal
    rows: tuple[ResearchStrategyEventVolatilityPriorityRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyEventVolatilityPriorityReport:
            raise TypeError(
                "ResearchStrategyEventVolatilityPriorityReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyEventVolatilityPriorityReport:
            raise ValueError(
                "report must be exactly ResearchStrategyEventVolatilityPriorityReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_generated_at_utc("generated_at", self.generated_at),
        )
        _require_public_text("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "event_count",
            "block_event_count",
            "watch_event_count",
            "pass_event_count",
            "manual_research_event_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "manual_research_event_ratio",
            "max_manual_research_priority_score",
            "max_probability_volatility_score",
            "max_evidence_churn_score",
            "max_liquidity_reliability_gap_ratio",
            "max_cost_drag_ratio",
            "max_resolution_proximity_score",
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
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_sha256("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")


def build_research_strategy_event_volatility_priority_report(
    events: Iterable[ResearchStrategyEventVolatilityPriorityInput],
    *,
    config: ResearchStrategyEventVolatilityPriorityConfig,
    generated_at: datetime,
) -> ResearchStrategyEventVolatilityPriorityReport:
    if type(config) is not ResearchStrategyEventVolatilityPriorityConfig:
        raise ValueError(
            "config must be a ResearchStrategyEventVolatilityPriorityConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_generated_at_utc("generated_at", generated_at)
    inputs = _normalize_inputs(events)
    _validate_input_times(inputs, generated_at_utc)
    base_rows = tuple(_row_from_event(event, config, generated_at_utc) for event in inputs)
    rows = tuple(
        _with_priority_rank(row, rank)
        for rank, row in enumerate(sorted(base_rows, key=_row_sort_key), start=1)
    )
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "event_count": _count(len(rows)),
        "block_event_count": _status_count(rows, "block"),
        "watch_event_count": _status_count(rows, "watch"),
        "pass_event_count": _status_count(rows, "pass"),
        "manual_research_event_count": _count(
            sum(1 for row in rows if row.status != "pass"),
        ),
        "manual_research_event_ratio": _ratio(
            _count(sum(1 for row in rows if row.status != "pass")),
            _count(len(rows)),
        ),
        "max_manual_research_priority_score": _max_ratio(
            tuple(row.manual_research_priority_score for row in rows),
        ),
        "max_probability_volatility_score": _max_ratio(
            tuple(row.probability_volatility_score for row in rows),
        ),
        "max_evidence_churn_score": _max_ratio(
            tuple(row.evidence_churn_score for row in rows),
        ),
        "max_liquidity_reliability_gap_ratio": _max_ratio(
            tuple(row.liquidity_reliability_gap_ratio for row in rows),
        ),
        "max_cost_drag_ratio": _max_ratio(tuple(row.cost_drag_ratio for row in rows)),
        "max_resolution_proximity_score": _max_ratio(
            tuple(row.resolution_proximity_score for row in rows),
        ),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyEventVolatilityPriorityReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_strategy_event_volatility_priority_report_payload(
    report: ResearchStrategyEventVolatilityPriorityReport | Mapping[str, object],
) -> dict[str, object]:
    if type(report) is ResearchStrategyEventVolatilityPriorityReport:
        _require_hard_flags("report", report)
        payload = _json_ready(asdict(report))
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _reject_unsafe_public_payload(
            "report payload",
            payload,
            allow_json_containers=True,
        )
        expected_digest = _digest_from_payload(payload)
        if payload.get("derived_validation_digest") != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")
        _validate_public_payload_shape(payload)
        return payload
    if isinstance(report, Mapping):
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _reject_unsafe_public_payload(
            "report payload",
            payload,
            allow_json_containers=True,
        )
        _require_hard_flags("report payload", _MappingFlags(payload))
        expected_digest = _digest_from_payload(payload)
        if payload.get("derived_validation_digest") != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")
        _validate_public_payload_shape(payload)
        return payload
    raise ValueError("report must be a ResearchStrategyEventVolatilityPriorityReport")


def research_strategy_event_volatility_priority_report_digest(
    report: ResearchStrategyEventVolatilityPriorityReport | Mapping[str, object],
) -> str:
    payload = research_strategy_event_volatility_priority_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


@dataclass(frozen=True)
class _MappingFlags:
    value: Mapping[str, object]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _row_from_event(
    event: ResearchStrategyEventVolatilityPriorityInput,
    config: ResearchStrategyEventVolatilityPriorityConfig,
    generated_at: datetime,
) -> ResearchStrategyEventVolatilityPriorityRow:
    probability_move = _quantize(event.probability_current - event.probability_previous)
    probability_move_abs = _clamp_ratio(abs(probability_move))
    probability_volatility_score = _max_ratio(
        (probability_move_abs, abs(event.probability_velocity_24h)),
    )
    evidence_churn_score = _evidence_churn_score(event, config)
    liquidity_reliability_gap_ratio = _clamp_ratio(_ONE - event.liquidity_depth_ratio)
    cost_drag_ratio = _clamp_ratio(event.spread_cost_ratio + event.fee_cost_ratio)
    seconds_to_resolution = _age_seconds(generated_at, event.resolution_at)
    resolution_proximity_score = _resolution_proximity_score(
        seconds_to_resolution,
        config.resolution_proximity_horizon_seconds,
    )
    reason_codes = _row_reason_codes(
        probability_volatility_score=probability_volatility_score,
        evidence_churn_score=evidence_churn_score,
        liquidity_reliability_gap_ratio=liquidity_reliability_gap_ratio,
        cost_drag_ratio=cost_drag_ratio,
        resolution_proximity_score=resolution_proximity_score,
        config=config,
    )
    return ResearchStrategyEventVolatilityPriorityRow(
        priority_rank=_ONE,
        event_reference_digest=_digest_private_reference(event.private_event_reference),
        domain_id=event.domain_id,
        status=_row_status(reason_codes),
        manual_research_priority_score=_priority_score(
            probability_volatility_score=probability_volatility_score,
            evidence_churn_score=evidence_churn_score,
            liquidity_reliability_gap_ratio=liquidity_reliability_gap_ratio,
            cost_drag_ratio=cost_drag_ratio,
            resolution_proximity_score=resolution_proximity_score,
            config=config,
        ),
        observed_at=event.observed_at,
        probability_previous=event.probability_previous,
        probability_current=event.probability_current,
        probability_move=probability_move,
        probability_move_abs=probability_move_abs,
        probability_velocity_24h=event.probability_velocity_24h,
        probability_volatility_score=probability_volatility_score,
        evidence_update_count_24h=event.evidence_update_count_24h,
        conflicting_evidence_count_24h=event.conflicting_evidence_count_24h,
        evidence_churn_score=evidence_churn_score,
        liquidity_depth_ratio=event.liquidity_depth_ratio,
        liquidity_reliability_gap_ratio=liquidity_reliability_gap_ratio,
        spread_cost_ratio=event.spread_cost_ratio,
        fee_cost_ratio=event.fee_cost_ratio,
        cost_drag_ratio=cost_drag_ratio,
        resolution_at=event.resolution_at,
        seconds_to_resolution=seconds_to_resolution,
        resolution_proximity_score=resolution_proximity_score,
        reason_codes=reason_codes,
    )


def _with_priority_rank(
    row: ResearchStrategyEventVolatilityPriorityRow,
    rank: int,
) -> ResearchStrategyEventVolatilityPriorityRow:
    return ResearchStrategyEventVolatilityPriorityRow(
        priority_rank=_count(rank),
        event_reference_digest=row.event_reference_digest,
        domain_id=row.domain_id,
        status=row.status,
        manual_research_priority_score=row.manual_research_priority_score,
        observed_at=row.observed_at,
        probability_previous=row.probability_previous,
        probability_current=row.probability_current,
        probability_move=row.probability_move,
        probability_move_abs=row.probability_move_abs,
        probability_velocity_24h=row.probability_velocity_24h,
        probability_volatility_score=row.probability_volatility_score,
        evidence_update_count_24h=row.evidence_update_count_24h,
        conflicting_evidence_count_24h=row.conflicting_evidence_count_24h,
        evidence_churn_score=row.evidence_churn_score,
        liquidity_depth_ratio=row.liquidity_depth_ratio,
        liquidity_reliability_gap_ratio=row.liquidity_reliability_gap_ratio,
        spread_cost_ratio=row.spread_cost_ratio,
        fee_cost_ratio=row.fee_cost_ratio,
        cost_drag_ratio=row.cost_drag_ratio,
        resolution_at=row.resolution_at,
        seconds_to_resolution=row.seconds_to_resolution,
        resolution_proximity_score=row.resolution_proximity_score,
        reason_codes=row.reason_codes,
    )


def _row_reason_codes(
    *,
    probability_volatility_score: Decimal,
    evidence_churn_score: Decimal,
    liquidity_reliability_gap_ratio: Decimal,
    cost_drag_ratio: Decimal,
    resolution_proximity_score: Decimal,
    config: ResearchStrategyEventVolatilityPriorityConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    _append_threshold_reason(
        reason_codes,
        metric=probability_volatility_score,
        watch=config.volatility_watch_ratio,
        block=config.volatility_block_ratio,
        watch_code="event_volatility_priority_probability_volatility_watch",
        block_code="event_volatility_priority_probability_volatility_block",
    )
    _append_threshold_reason(
        reason_codes,
        metric=evidence_churn_score,
        watch=config.evidence_churn_watch_score,
        block=config.evidence_churn_block_score,
        watch_code="event_volatility_priority_evidence_churn_watch",
        block_code="event_volatility_priority_evidence_churn_block",
    )
    _append_threshold_reason(
        reason_codes,
        metric=liquidity_reliability_gap_ratio,
        watch=config.liquidity_gap_watch_ratio,
        block=config.liquidity_gap_block_ratio,
        watch_code="event_volatility_priority_liquidity_reliability_watch",
        block_code="event_volatility_priority_liquidity_reliability_block",
    )
    _append_threshold_reason(
        reason_codes,
        metric=cost_drag_ratio,
        watch=config.cost_drag_watch_ratio,
        block=config.cost_drag_block_ratio,
        watch_code="event_volatility_priority_cost_drag_watch",
        block_code="event_volatility_priority_cost_drag_block",
    )
    _append_threshold_reason(
        reason_codes,
        metric=resolution_proximity_score,
        watch=config.resolution_proximity_watch_score,
        block=config.resolution_proximity_block_score,
        watch_code="event_volatility_priority_resolution_proximity_watch",
        block_code="event_volatility_priority_resolution_proximity_block",
    )
    if not reason_codes:
        reason_codes.append("event_volatility_priority_clear")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _append_threshold_reason(
    reason_codes: list[str],
    *,
    metric: Decimal,
    watch: Decimal,
    block: Decimal,
    watch_code: str,
    block_code: str,
) -> None:
    if metric >= block:
        reason_codes.append(block_code)
        return
    if metric >= watch:
        reason_codes.append(watch_code)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchStrategyEventVolatilityPriorityRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyEventVolatilityPriorityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("event_volatility_priority_empty",)
    seen_codes: set[str] = set()
    for row in rows:
        for code in row.reason_codes:
            if code != "event_volatility_priority_clear":
                seen_codes.add(code)
    if not seen_codes:
        return ("event_volatility_priority_clear",)
    reason_codes = tuple(code for code in _REASON_CODE_SEQUENCE if code in seen_codes)
    return _normalize_reason_codes("reason_codes", reason_codes)


def _priority_score(
    *,
    probability_volatility_score: Decimal,
    evidence_churn_score: Decimal,
    liquidity_reliability_gap_ratio: Decimal,
    cost_drag_ratio: Decimal,
    resolution_proximity_score: Decimal,
    config: ResearchStrategyEventVolatilityPriorityConfig,
) -> Decimal:
    return _max_ratio(
        (
            _ratio_to_cap(probability_volatility_score, config.volatility_block_ratio),
            _ratio_to_cap(evidence_churn_score, config.evidence_churn_block_score),
            _ratio_to_cap(
                liquidity_reliability_gap_ratio,
                config.liquidity_gap_block_ratio,
            ),
            _ratio_to_cap(cost_drag_ratio, config.cost_drag_block_ratio),
            _ratio_to_cap(
                resolution_proximity_score,
                config.resolution_proximity_block_score,
            ),
        ),
    )


def _row_sort_key(row: ResearchStrategyEventVolatilityPriorityRow) -> tuple[object, ...]:
    return (
        -_status_rank(row.status),
        -row.manual_research_priority_score,
        -row.probability_volatility_score,
        -row.evidence_churn_score,
        -row.liquidity_reliability_gap_ratio,
        -row.cost_drag_ratio,
        -row.resolution_proximity_score,
        row.domain_id,
        row.event_reference_digest,
    )


def _status_rank(status: str) -> int:
    if status == "block":
        return 2
    if status == "watch":
        return 1
    return 0


def _status_count(
    rows: tuple[ResearchStrategyEventVolatilityPriorityRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _evidence_churn_score(
    event: ResearchStrategyEventVolatilityPriorityInput,
    config: ResearchStrategyEventVolatilityPriorityConfig,
) -> Decimal:
    churn_units = event.evidence_update_count_24h + event.conflicting_evidence_count_24h
    return _ratio_to_cap(churn_units, config.evidence_churn_block_count)


def _resolution_proximity_score(
    seconds_to_resolution: Decimal,
    horizon_seconds: Decimal,
) -> Decimal:
    if seconds_to_resolution >= horizon_seconds:
        return _ZERO
    return _clamp_ratio(_ONE - (seconds_to_resolution / horizon_seconds))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == Decimal("0"):
        return _ZERO
    return _clamp_ratio(numerator / denominator)


def _ratio_to_cap(value: Decimal, cap: Decimal) -> Decimal:
    if cap <= _ZERO:
        raise ValueError("cap must be positive")
    return _clamp_ratio(value / cap)


def _normalize_inputs(
    events: Iterable[ResearchStrategyEventVolatilityPriorityInput],
) -> tuple[ResearchStrategyEventVolatilityPriorityInput, ...]:
    if isinstance(events, (str, bytes)) or not isinstance(events, Iterable):
        raise ValueError("events must be an iterable")
    normalized: list[ResearchStrategyEventVolatilityPriorityInput] = []
    seen_references: set[str] = set()
    for event in events:
        if type(event) is not ResearchStrategyEventVolatilityPriorityInput:
            raise ValueError(
                "events must contain ResearchStrategyEventVolatilityPriorityInput",
            )
        if event.private_event_reference in seen_references:
            raise ValueError("private_event_reference values must be unique")
        seen_references.add(event.private_event_reference)
        normalized.append(event)
    return tuple(
        sorted(
            normalized,
            key=lambda event: (
                _digest_private_reference(event.private_event_reference),
                event.domain_id,
            ),
        ),
    )


def _normalize_rows(
    rows: Sequence[ResearchStrategyEventVolatilityPriorityRow],
) -> tuple[ResearchStrategyEventVolatilityPriorityRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchStrategyEventVolatilityPriorityRow] = []
    seen_digests: set[str] = set()
    for row in rows:
        if type(row) is not ResearchStrategyEventVolatilityPriorityRow:
            raise ValueError("rows must contain ResearchStrategyEventVolatilityPriorityRow")
        if row.event_reference_digest in seen_digests:
            raise ValueError("event_reference_digest values must be unique")
        seen_digests.add(row.event_reference_digest)
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: row.priority_rank))


def _validate_config(config: ResearchStrategyEventVolatilityPriorityConfig) -> None:
    _require_watch_below_block(
        "volatility_watch_ratio",
        config.volatility_watch_ratio,
        "volatility_block_ratio",
        config.volatility_block_ratio,
    )
    _require_watch_below_block(
        "evidence_churn_watch_score",
        config.evidence_churn_watch_score,
        "evidence_churn_block_score",
        config.evidence_churn_block_score,
    )
    _require_watch_below_block(
        "liquidity_gap_watch_ratio",
        config.liquidity_gap_watch_ratio,
        "liquidity_gap_block_ratio",
        config.liquidity_gap_block_ratio,
    )
    _require_watch_below_block(
        "cost_drag_watch_ratio",
        config.cost_drag_watch_ratio,
        "cost_drag_block_ratio",
        config.cost_drag_block_ratio,
    )
    _require_watch_below_block(
        "resolution_proximity_watch_score",
        config.resolution_proximity_watch_score,
        "resolution_proximity_block_score",
        config.resolution_proximity_block_score,
    )


def _require_watch_below_block(
    watch_name: str,
    watch_value: Decimal,
    block_name: str,
    block_value: Decimal,
) -> None:
    if block_value <= watch_value:
        raise ValueError(f"{block_name} must exceed {watch_name}")


def _validate_input_times(
    events: tuple[ResearchStrategyEventVolatilityPriorityInput, ...],
    generated_at: datetime,
) -> None:
    for event in events:
        if event.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        if event.resolution_at < generated_at:
            raise ValueError("resolution_at must not be before generated_at")


def _validate_row(row: ResearchStrategyEventVolatilityPriorityRow) -> None:
    if row.probability_move != _quantize(row.probability_current - row.probability_previous):
        raise ValueError("probability_move must match probabilities")
    if row.probability_move_abs != abs(row.probability_move):
        raise ValueError("probability_move_abs must match probability_move")
    if row.probability_volatility_score != _max_ratio(
        (row.probability_move_abs, abs(row.probability_velocity_24h)),
    ):
        raise ValueError("probability_volatility_score must match probability movement")
    if row.liquidity_reliability_gap_ratio != _clamp_ratio(
        _ONE - row.liquidity_depth_ratio,
    ):
        raise ValueError("liquidity_reliability_gap_ratio must match liquidity depth")
    if row.cost_drag_ratio != _clamp_ratio(row.spread_cost_ratio + row.fee_cost_ratio):
        raise ValueError("cost_drag_ratio must match cost ratios")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchStrategyEventVolatilityPriorityReport) -> None:
    if report.event_count != _count(len(report.rows)):
        raise ValueError("event_count must match rows")
    if report.block_event_count != _status_count(report.rows, "block"):
        raise ValueError("block_event_count must match rows")
    if report.watch_event_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_event_count must match rows")
    if report.pass_event_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_event_count must match rows")
    if report.manual_research_event_count != _count(
        sum(1 for row in report.rows if row.status != "pass"),
    ):
        raise ValueError("manual_research_event_count must match rows")
    if report.manual_research_event_ratio != _ratio(
        report.manual_research_event_count,
        report.event_count,
    ):
        raise ValueError("manual_research_event_ratio must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    expected_ranks = tuple(_count(rank) for rank in range(1, len(report.rows) + 1))
    if tuple(row.priority_rank for row in report.rows) != expected_ranks:
        raise ValueError("priority_rank values must be sequential")
    if report.max_manual_research_priority_score != _max_ratio(
        tuple(row.manual_research_priority_score for row in report.rows),
    ):
        raise ValueError("max_manual_research_priority_score must match rows")
    if report.max_probability_volatility_score != _max_ratio(
        tuple(row.probability_volatility_score for row in report.rows),
    ):
        raise ValueError("max_probability_volatility_score must match rows")
    if report.max_evidence_churn_score != _max_ratio(
        tuple(row.evidence_churn_score for row in report.rows),
    ):
        raise ValueError("max_evidence_churn_score must match rows")
    if report.max_liquidity_reliability_gap_ratio != _max_ratio(
        tuple(row.liquidity_reliability_gap_ratio for row in report.rows),
    ):
        raise ValueError("max_liquidity_reliability_gap_ratio must match rows")
    if report.max_cost_drag_ratio != _max_ratio(
        tuple(row.cost_drag_ratio for row in report.rows),
    ):
        raise ValueError("max_cost_drag_ratio must match rows")
    if report.max_resolution_proximity_score != _max_ratio(
        tuple(row.resolution_proximity_score for row in report.rows),
    ):
        raise ValueError("max_resolution_proximity_score must match rows")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _HARD_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_private_reference(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    return value


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_TEXT_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")
    return value


def _require_sha256(field_name: str, value: object) -> str:
    if type(value) is not str or not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal = _normalize_decimal(field_name, value)
    normalized = decimal.quantize(_COUNT_QUANT)
    if normalized < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != decimal:
        raise ValueError(f"{field_name} must be a whole number")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized > _ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return normalized


def _normalize_signed_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < -_ONE:
        raise ValueError(f"{field_name} must be at least -1")
    if normalized > _ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return normalized


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _max_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _clamp_ratio(max(values))


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(_COUNT_QUANT)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _as_generated_at_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is not UTC:
        raise ValueError(f"{field_name} must be UTC")
    return value


def _age_seconds(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    seconds = Decimal(delta.days * 86_400 + delta.seconds)
    fractional_seconds = Decimal(delta.microseconds) / Decimal("1000000")
    return _normalize_nonnegative_decimal("seconds", seconds + fractional_seconds)


def _digest_private_reference(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _report_values_without_digest(
    report: ResearchStrategyEventVolatilityPriorityReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest")
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    return _digest_from_payload(_json_ready(values))


def _digest_from_payload(payload: Mapping[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _validate_public_payload_shape(payload: Mapping[str, object]) -> None:
    _require_known_public_fields("report payload", payload, _ROOT_PUBLIC_FIELDS)
    _require_datetime_payload("generated_at", payload.get("generated_at"))
    _require_public_text("config_version", payload.get("config_version"))
    _require_status("status", payload.get("status"))
    _require_sha256("derived_validation_digest", payload.get("derived_validation_digest"))
    _require_hard_flags("report payload", _MappingFlags(payload))
    _require_public_decimal_fields(payload)
    _normalize_reason_codes("reason_codes", payload.get("reason_codes"))
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ValueError("rows must be a JSON array")
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise ValueError("rows must contain JSON objects")
        _validate_public_row_payload(f"rows[{index}]", row)
    _validate_public_payload_consistency(payload)


def _validate_public_row_payload(label: str, row: Mapping[str, object]) -> None:
    _require_known_public_fields(label, row, _ROW_PUBLIC_FIELDS)
    _require_sha256("event_reference_digest", row.get("event_reference_digest"))
    _require_public_text("domain_id", row.get("domain_id"))
    _require_status("status", row.get("status"))
    _require_datetime_payload("observed_at", row.get("observed_at"))
    _require_datetime_payload("resolution_at", row.get("resolution_at"))
    _require_hard_flags(label, _MappingFlags(row))
    _require_public_decimal_fields(row)
    _normalize_reason_codes("reason_codes", row.get("reason_codes"))
    _validate_public_row_consistency(label, row)


def _validate_public_row_consistency(label: str, row: Mapping[str, object]) -> None:
    probability_previous = _public_decimal(row, "probability_previous")
    probability_current = _public_decimal(row, "probability_current")
    probability_move = _public_decimal(row, "probability_move")
    probability_move_abs = _public_decimal(row, "probability_move_abs")
    probability_velocity_24h = _public_decimal(row, "probability_velocity_24h")
    liquidity_depth_ratio = _public_decimal(row, "liquidity_depth_ratio")
    spread_cost_ratio = _public_decimal(row, "spread_cost_ratio")
    fee_cost_ratio = _public_decimal(row, "fee_cost_ratio")
    if probability_move != _quantize(probability_current - probability_previous):
        raise ValueError(f"probability_move must match probabilities in {label}")
    if probability_move_abs != abs(probability_move):
        raise ValueError(f"probability_move_abs must match probability_move in {label}")
    if _public_decimal(row, "probability_volatility_score") != _max_ratio(
        (probability_move_abs, abs(probability_velocity_24h)),
    ):
        raise ValueError(
            f"probability_volatility_score must match probability movement in {label}",
        )
    if _public_decimal(row, "liquidity_reliability_gap_ratio") != _clamp_ratio(
        _ONE - liquidity_depth_ratio,
    ):
        raise ValueError(
            f"liquidity_reliability_gap_ratio must match liquidity depth in {label}",
        )
    if _public_decimal(row, "cost_drag_ratio") != _clamp_ratio(
        spread_cost_ratio + fee_cost_ratio,
    ):
        raise ValueError(f"cost_drag_ratio must match cost ratios in {label}")
    reason_codes = _public_reason_codes(row)
    if row.get("status") != _row_status(reason_codes):
        raise ValueError(f"status must match reason_codes in {label}")


def _validate_public_payload_consistency(payload: Mapping[str, object]) -> None:
    rows = _public_rows(payload)
    if payload.get("event_count") != str(_count(len(rows))):
        raise ValueError("event_count must match rows")
    for status, field_name in (
        ("block", "block_event_count"),
        ("watch", "watch_event_count"),
        ("pass", "pass_event_count"),
    ):
        if payload.get(field_name) != str(_count(sum(1 for row in rows if row.get("status") == status))):
            raise ValueError(f"{field_name} must match rows")
    manual_research_count = _count(sum(1 for row in rows if row.get("status") != "pass"))
    if payload.get("manual_research_event_count") != str(manual_research_count):
        raise ValueError("manual_research_event_count must match rows")
    if payload.get("manual_research_event_ratio") != str(
        _ratio(manual_research_count, _count(len(rows))),
    ):
        raise ValueError("manual_research_event_ratio must match rows")
    if payload.get("status") != _public_report_status(rows):
        raise ValueError("status must match rows")
    if tuple(payload.get("reason_codes", ())) != _public_report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    expected_ranks = tuple(
        str(_normalize_positive_decimal("priority_rank", _count(rank)))
        for rank in range(1, len(rows) + 1)
    )
    if tuple(row.get("priority_rank") for row in rows) != expected_ranks:
        raise ValueError("priority_rank values must be sequential")
    for field_name, row_field_name in (
        ("max_manual_research_priority_score", "manual_research_priority_score"),
        ("max_probability_volatility_score", "probability_volatility_score"),
        ("max_evidence_churn_score", "evidence_churn_score"),
        ("max_liquidity_reliability_gap_ratio", "liquidity_reliability_gap_ratio"),
        ("max_cost_drag_ratio", "cost_drag_ratio"),
        ("max_resolution_proximity_score", "resolution_proximity_score"),
    ):
        if payload.get(field_name) != str(_public_max_ratio(rows, row_field_name)):
            raise ValueError(f"{field_name} must match rows")


def _public_rows(payload: Mapping[str, object]) -> tuple[Mapping[str, object], ...]:
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ValueError("rows must be a JSON array")
    return tuple(row for row in rows if isinstance(row, Mapping))


def _public_decimal(payload: Mapping[str, object], field_name: str) -> Decimal:
    return _decimal_from_public_payload(field_name, payload.get(field_name))


def _public_reason_codes(payload: Mapping[str, object]) -> tuple[str, ...]:
    return _normalize_reason_codes("reason_codes", payload.get("reason_codes"))


def _public_report_status(rows: tuple[Mapping[str, object], ...]) -> str:
    if any(row.get("status") == "block" for row in rows):
        return "block"
    if any(row.get("status") == "watch" for row in rows):
        return "watch"
    return "pass"


def _public_report_reason_codes(
    rows: tuple[Mapping[str, object], ...],
) -> tuple[str, ...]:
    if not rows:
        return ("event_volatility_priority_empty",)
    seen_codes: set[str] = set()
    for row in rows:
        for code in _public_reason_codes(row):
            if code != "event_volatility_priority_clear":
                seen_codes.add(code)
    if not seen_codes:
        return ("event_volatility_priority_clear",)
    reason_codes = tuple(code for code in _REASON_CODE_SEQUENCE if code in seen_codes)
    return _normalize_reason_codes("reason_codes", reason_codes)


def _public_max_ratio(
    rows: tuple[Mapping[str, object], ...],
    field_name: str,
) -> Decimal:
    return _max_ratio(tuple(_public_decimal(row, field_name) for row in rows))


def _require_known_public_fields(
    label: str,
    payload: Mapping[str, object],
    allowed_fields: frozenset[str],
) -> None:
    missing_fields = allowed_fields.difference(payload)
    if missing_fields:
        missing = sorted(missing_fields)[0]
        raise ValueError(f"{missing} missing from {label}")
    extra_fields = frozenset(payload).difference(allowed_fields)
    if extra_fields:
        extra = sorted(extra_fields)[0]
        raise ValueError(f"unexpected public field in {label}: {extra}")


def _require_public_decimal_fields(payload: Mapping[str, object]) -> None:
    for field_name, value in payload.items():
        if field_name in _COUNT_PUBLIC_FIELDS:
            _require_count_payload(field_name, value)
        elif field_name in _POSITIVE_DECIMAL_PUBLIC_FIELDS:
            _require_positive_decimal_payload(field_name, value)
        elif field_name in _RATIO_PUBLIC_FIELDS:
            _require_ratio_payload(field_name, value)
        elif field_name in _SIGNED_RATIO_PUBLIC_FIELDS:
            _require_signed_ratio_payload(field_name, value)
        elif field_name in _NONNEGATIVE_DECIMAL_PUBLIC_FIELDS:
            _require_nonnegative_decimal_payload(field_name, value)


def _require_count_payload(field_name: str, value: object) -> None:
    decimal = _decimal_from_public_payload(field_name, value)
    normalized = _normalize_nonnegative_count(field_name, decimal)
    if str(normalized) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")


def _require_positive_decimal_payload(field_name: str, value: object) -> None:
    decimal = _decimal_from_public_payload(field_name, value)
    normalized = _normalize_positive_decimal(field_name, decimal)
    if str(normalized) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")


def _require_ratio_payload(field_name: str, value: object) -> None:
    decimal = _decimal_from_public_payload(field_name, value)
    normalized = _normalize_ratio(field_name, decimal)
    if str(normalized) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")


def _require_signed_ratio_payload(field_name: str, value: object) -> None:
    decimal = _decimal_from_public_payload(field_name, value)
    normalized = _normalize_signed_ratio(field_name, decimal)
    if str(normalized) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")


def _require_nonnegative_decimal_payload(field_name: str, value: object) -> None:
    decimal = _decimal_from_public_payload(field_name, value)
    normalized = _normalize_nonnegative_decimal(field_name, decimal)
    if str(normalized) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")


def _decimal_from_public_payload(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        decimal = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    if not decimal.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return decimal


def _require_datetime_payload(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime string") from exc
    canonical = _as_utc(field_name, parsed).isoformat()
    if value != canonical:
        raise ValueError(f"{field_name} must be a canonical UTC ISO datetime string")


def _json_ready(value: object) -> object:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) in (str, bool, int):
        return value
    if isinstance(value, Mapping):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    raise ValueError("value is not JSON serializable")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError(f"{field_name} must be a sequence")
    codes = tuple(value)
    if not codes:
        raise ValueError(f"{field_name} must not be empty")
    for code in codes:
        if type(code) is not str or code not in _REASON_CODE_SEQUENCE:
            raise ValueError(f"{field_name} must be known")
    unique_codes = tuple(code for code in _REASON_CODE_SEQUENCE if code in codes)
    if unique_codes != codes:
        raise ValueError(f"{field_name} must be deterministic")
    if len(set(codes)) != len(codes):
        raise ValueError(f"{field_name} must be unique")
    for clear_code in (
        "event_volatility_priority_empty",
        "event_volatility_priority_clear",
    ):
        if clear_code in codes and len(codes) != 1:
            raise ValueError(f"{clear_code} must be alone")
    return codes


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        value = asdict(value)
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(label, key)
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, (list, tuple)):
        if not allow_json_containers and not isinstance(value, tuple):
            raise ValueError(f"unsafe public container in {label}")
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) in (float, int):
        raise ValueError(f"public numeric values must be Decimal strings in {label}")
    if type(value) is str:
        _reject_unsafe_public_string(label, value)


def _reject_unsafe_public_key(label: str, key: str) -> None:
    lowered = key.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_KEY_TERMS):
        if key != "event_reference_digest":
            raise ValueError(f"unsafe public field in {label}: {key}")


def _reject_unsafe_public_string(label: str, value: str) -> None:
    lowered = value.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_VALUE_TERMS):
        raise ValueError(f"unsafe public value in {label}")


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_EVENT_VOLATILITY_PRIORITY_CONFIG_VERSION",
    "STATUSES",
    "ResearchStrategyEventVolatilityPriorityConfig",
    "ResearchStrategyEventVolatilityPriorityInput",
    "ResearchStrategyEventVolatilityPriorityReport",
    "ResearchStrategyEventVolatilityPriorityRow",
    "build_research_strategy_event_volatility_priority_report",
    "research_strategy_event_volatility_priority_report_digest",
    "research_strategy_event_volatility_priority_report_payload",
)
