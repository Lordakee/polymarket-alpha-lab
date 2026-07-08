"""Pure report-only queue snapshots for public cost recheck signals."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_MARKET_EVENT_COST_RECHECK_QUEUE_CONFIG_VERSION = (
    "research-market-event-cost-recheck-queue-report-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0")
_ONE = Decimal("1")
_STATUS_VALUES = frozenset(("pass", "watch", "block"))
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_UNSAFE_PUBLIC_TERMS = (
    "http://",
    "https://",
    "database",
    "network",
    "persist",
    "mutation",
    "credential",
    "secret",
    "token",
    "wal" + "let",
    "au" + "th",
    "private" + "_key",
    "or" + "der",
    "tra" + "de",
    "tra" + "ding",
    "li" + "ve",
    "b" + "uy",
    "se" + "ll",
    "rec" + "ommend",
    "siz" + "ing",
)
_PUBLIC_PAYLOAD_FIELD_DENYLIST = frozenset(
    (
        "event_bucket",
        "cost_surface_bucket",
        "candidate" + "_id",
        "condition" + "_id",
        "market" + "_id",
        "market" + "_slug",
        "question",
        "source" + "_id",
        "source" + "_url",
        "source" + "_ref",
        "source" + "_text",
    ),
)
_KNOWN_REASON_CODES = frozenset(
    (
        "no_cost_recheck_candidates",
        "spread_drift_block",
        "spread_drift_watch",
        "depth_fade_block",
        "depth_fade_watch",
        "quote_age_block",
        "quote_age_watch",
        "fee_friction_block",
        "fee_friction_watch",
        "catalyst_pressure_block",
        "catalyst_pressure_watch",
        "aggregate_recheck_pressure_block",
        "aggregate_recheck_pressure_watch",
        "aggregate_recheck_pressure_pass",
    ),
)
_REPORT_PUBLIC_PAYLOAD_FIELDS = (
    "generated_at",
    "config_version",
    "item_count",
    "queued_recheck_count",
    "pass_count",
    "watch_count",
    "block_count",
    "average_aggregate_recheck_pressure",
    "max_aggregate_recheck_pressure",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
_ROW_PUBLIC_PAYLOAD_FIELDS = (
    "queue_item_digest",
    "observed_at",
    "spread_drift_bps",
    "depth_fade_ratio",
    "quote_age_seconds",
    "fee_friction_bps",
    "catalyst_pressure_score",
    "spread_drift_pressure",
    "depth_fade_pressure",
    "quote_age_pressure",
    "fee_friction_pressure",
    "aggregate_recheck_pressure",
    "recheck_required",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
_REASON_COUNT_PUBLIC_PAYLOAD_FIELDS = (
    "reason_code",
    "count",
    "paper_only",
    "report_only",
    "readonly",
)

__all__ = (
    "DEFAULT_RESEARCH_MARKET_EVENT_COST_RECHECK_QUEUE_CONFIG_VERSION",
    "ResearchMarketEventCostRecheckObservation",
    "ResearchMarketEventCostRecheckQueueConfig",
    "ResearchMarketEventCostRecheckQueueReasonCodeCount",
    "ResearchMarketEventCostRecheckQueueReport",
    "ResearchMarketEventCostRecheckQueueRow",
    "build_research_market_event_cost_recheck_queue_report",
    "research_market_event_cost_recheck_queue_report_payload",
)


class _Missing:
    pass


_MISSING = _Missing()


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchMarketEventCostRecheckQueueConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_RESEARCH_MARKET_EVENT_COST_RECHECK_QUEUE_CONFIG_VERSION
    watch_spread_drift_bps: Decimal = Decimal("10.000000")
    block_spread_drift_bps: Decimal = Decimal("50.000000")
    watch_depth_fade_ratio: Decimal = Decimal("0.150000")
    block_depth_fade_ratio: Decimal = Decimal("0.600000")
    watch_quote_age_seconds: Decimal = Decimal("300.000000")
    block_quote_age_seconds: Decimal = Decimal("900.000000")
    watch_fee_friction_bps: Decimal = Decimal("5.000000")
    block_fee_friction_bps: Decimal = Decimal("25.000000")
    watch_catalyst_pressure: Decimal = Decimal("0.350000")
    block_catalyst_pressure: Decimal = Decimal("0.850000")
    watch_aggregate_recheck_pressure: Decimal = Decimal("0.350000")
    block_aggregate_recheck_pressure: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketEventCostRecheckQueueConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_EVENT_COST_RECHECK_QUEUE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_spread_drift_bps",
            "block_spread_drift_bps",
            "watch_quote_age_seconds",
            "block_quote_age_seconds",
            "watch_fee_friction_bps",
            "block_fee_friction_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_depth_fade_ratio",
            "block_depth_fade_ratio",
            "watch_catalyst_pressure",
            "block_catalyst_pressure",
            "watch_aggregate_recheck_pressure",
            "block_aggregate_recheck_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_threshold_pair(
            "watch_spread_drift_bps",
            self.watch_spread_drift_bps,
            "block_spread_drift_bps",
            self.block_spread_drift_bps,
        )
        _require_threshold_pair(
            "watch_depth_fade_ratio",
            self.watch_depth_fade_ratio,
            "block_depth_fade_ratio",
            self.block_depth_fade_ratio,
        )
        _require_threshold_pair(
            "watch_quote_age_seconds",
            self.watch_quote_age_seconds,
            "block_quote_age_seconds",
            self.block_quote_age_seconds,
        )
        _require_threshold_pair(
            "watch_fee_friction_bps",
            self.watch_fee_friction_bps,
            "block_fee_friction_bps",
            self.block_fee_friction_bps,
        )
        _require_threshold_pair(
            "watch_catalyst_pressure",
            self.watch_catalyst_pressure,
            "block_catalyst_pressure",
            self.block_catalyst_pressure,
        )
        _require_threshold_pair(
            "watch_aggregate_recheck_pressure",
            self.watch_aggregate_recheck_pressure,
            "block_aggregate_recheck_pressure",
            self.block_aggregate_recheck_pressure,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_constructor_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketEventCostRecheckObservation(_FinalPublicDataclass):
    event_bucket: str
    cost_surface_bucket: str
    observed_at: datetime
    spread_drift_bps: Decimal
    depth_fade_ratio: Decimal
    quote_age_seconds: Decimal
    fee_friction_bps: Decimal
    catalyst_pressure: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketEventCostRecheckObservation, "observation")
        for field_name in ("event_bucket", "cost_surface_bucket"):
            object.__setattr__(
                self,
                field_name,
                _require_public_identifier(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("spread_drift_bps", "quote_age_seconds", "fee_friction_bps"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("depth_fade_ratio", "catalyst_pressure"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_input_reason_codes(self.reason_codes),
        )
        _require_hard_flags("observation", self)
        _reject_unsafe_constructor_payload("observation", self)


@dataclass(frozen=True)
class ResearchMarketEventCostRecheckQueueRow(_FinalPublicDataclass):
    event_bucket: str
    cost_surface_bucket: str
    queue_item_digest: str
    observed_at: datetime
    spread_drift_bps: Decimal
    depth_fade_ratio: Decimal
    quote_age_seconds: Decimal
    fee_friction_bps: Decimal
    catalyst_pressure_score: Decimal
    spread_drift_pressure: Decimal
    depth_fade_pressure: Decimal
    quote_age_pressure: Decimal
    fee_friction_pressure: Decimal
    aggregate_recheck_pressure: Decimal
    recheck_required: bool
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketEventCostRecheckQueueRow, "row")
        for field_name in ("event_bucket", "cost_surface_bucket"):
            object.__setattr__(
                self,
                field_name,
                _require_public_identifier(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "queue_item_digest",
            _require_sha256_digest("queue_item_digest", self.queue_item_digest),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("spread_drift_bps", "quote_age_seconds", "fee_friction_bps"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "depth_fade_ratio",
            "catalyst_pressure_score",
            "spread_drift_pressure",
            "depth_fade_pressure",
            "quote_age_pressure",
            "fee_friction_pressure",
            "aggregate_recheck_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "recheck_required",
            _require_bool("recheck_required", self.recheck_required),
        )
        object.__setattr__(self, "status", _require_status("status", self.status))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags("row", self)
        _reject_unsafe_constructor_payload("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchMarketEventCostRecheckQueueReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketEventCostRecheckQueueReasonCodeCount,
            "reason_code_count",
        )
        object.__setattr__(self, "reason_code", _require_reason_code(self.reason_code))
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_constructor_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketEventCostRecheckQueueReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    item_count: Decimal
    queued_recheck_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_aggregate_recheck_pressure: Decimal | None
    max_aggregate_recheck_pressure: Decimal | None
    status: str
    rows: tuple[ResearchMarketEventCostRecheckQueueRow, ...]
    reason_code_counts: tuple[ResearchMarketEventCostRecheckQueueReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketEventCostRecheckQueueReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_EVENT_COST_RECHECK_QUEUE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "item_count",
            "queued_recheck_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_aggregate_recheck_pressure",
            "max_aggregate_recheck_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_optional_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "status", _require_status("status", self.status))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "payload_digest",
            _require_sha256_digest("payload_digest", self.payload_digest),
        )
        _require_hard_flags("report", self)
        _reject_unsafe_constructor_payload("report", self)
        _validate_report_consistency(self)
        expected_digest = _payload_digest(_public_report_payload(self, include_digest=False))
        if self.payload_digest != expected_digest:
            raise ValueError("payload_digest must match report payload")


def build_research_market_event_cost_recheck_queue_report(
    observations: Iterable[object],
    *,
    config: ResearchMarketEventCostRecheckQueueConfig,
    generated_at: datetime,
) -> ResearchMarketEventCostRecheckQueueReport:
    if type(config) is not ResearchMarketEventCostRecheckQueueConfig:
        raise ValueError("config must be a ResearchMarketEventCostRecheckQueueConfig")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (_row_from_observation(observation, config=config) for observation in normalized_observations),
            key=lambda row: row.queue_item_digest,
        ),
    )
    reason_codes = _summary_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "item_count": _decimal_count(len(rows)),
        "queued_recheck_count": _decimal_count(
            sum(1 for row in rows if row.recheck_required),
        ),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_aggregate_recheck_pressure": _average_aggregate_recheck_pressure(rows),
        "max_aggregate_recheck_pressure": _max_aggregate_recheck_pressure(rows),
        "status": _summary_status(reason_codes),
        "rows": rows,
        "reason_code_counts": _reason_code_counts(rows, reason_codes),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    digest = _payload_digest(_public_report_payload_from_values(values, include_digest=False))
    return ResearchMarketEventCostRecheckQueueReport(**values, payload_digest=digest)


def research_market_event_cost_recheck_queue_report_payload(
    report: ResearchMarketEventCostRecheckQueueReport | Mapping[str, object],
) -> dict[str, Any]:
    if type(report) is ResearchMarketEventCostRecheckQueueReport:
        _require_hard_flags("report", report)
        payload = _public_report_payload(report, include_digest=True)
    elif isinstance(report, Mapping):
        payload = _payload_value(report)
    else:
        raise ValueError(
            "report must be a ResearchMarketEventCostRecheckQueueReport or payload mapping",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload(payload)
    _require_payload_flags(payload)
    if "payload_digest" in payload:
        expected_digest = _payload_digest(_payload_without_digest(payload))
        if payload["payload_digest"] != expected_digest:
            raise ValueError("payload_digest must match report payload")
    return payload


def _row_from_observation(
    observation: ResearchMarketEventCostRecheckObservation,
    *,
    config: ResearchMarketEventCostRecheckQueueConfig,
) -> ResearchMarketEventCostRecheckQueueRow:
    spread_pressure = _pressure(observation.spread_drift_bps, config.block_spread_drift_bps)
    depth_pressure = _pressure(observation.depth_fade_ratio, config.block_depth_fade_ratio)
    quote_pressure = _pressure(observation.quote_age_seconds, config.block_quote_age_seconds)
    fee_pressure = _pressure(observation.fee_friction_bps, config.block_fee_friction_bps)
    catalyst_pressure = _pressure(
        observation.catalyst_pressure,
        config.block_catalyst_pressure,
    )
    aggregate_pressure = _average(
        (
            spread_pressure,
            depth_pressure,
            quote_pressure,
            fee_pressure,
            catalyst_pressure,
        ),
    )
    status = _row_status(
        spread_drift_bps=observation.spread_drift_bps,
        depth_fade_ratio=observation.depth_fade_ratio,
        quote_age_seconds=observation.quote_age_seconds,
        fee_friction_bps=observation.fee_friction_bps,
        catalyst_pressure=observation.catalyst_pressure,
        aggregate_recheck_pressure=aggregate_pressure,
        config=config,
    )
    return ResearchMarketEventCostRecheckQueueRow(
        event_bucket=observation.event_bucket,
        cost_surface_bucket=observation.cost_surface_bucket,
        queue_item_digest=_queue_item_digest(observation),
        observed_at=observation.observed_at,
        spread_drift_bps=observation.spread_drift_bps,
        depth_fade_ratio=observation.depth_fade_ratio,
        quote_age_seconds=observation.quote_age_seconds,
        fee_friction_bps=observation.fee_friction_bps,
        catalyst_pressure_score=catalyst_pressure,
        spread_drift_pressure=spread_pressure,
        depth_fade_pressure=depth_pressure,
        quote_age_pressure=quote_pressure,
        fee_friction_pressure=fee_pressure,
        aggregate_recheck_pressure=aggregate_pressure,
        recheck_required=status != "pass",
        status=status,
        reason_codes=_row_reason_codes(
            observation=observation,
            aggregate_recheck_pressure=aggregate_pressure,
            status=status,
            config=config,
        ),
    )


def _row_status(
    *,
    spread_drift_bps: Decimal,
    depth_fade_ratio: Decimal,
    quote_age_seconds: Decimal,
    fee_friction_bps: Decimal,
    catalyst_pressure: Decimal,
    aggregate_recheck_pressure: Decimal,
    config: ResearchMarketEventCostRecheckQueueConfig,
) -> str:
    if (
        spread_drift_bps >= config.block_spread_drift_bps
        or depth_fade_ratio >= config.block_depth_fade_ratio
        or quote_age_seconds >= config.block_quote_age_seconds
        or fee_friction_bps >= config.block_fee_friction_bps
        or catalyst_pressure >= config.block_catalyst_pressure
        or aggregate_recheck_pressure >= config.block_aggregate_recheck_pressure
    ):
        return "block"
    if (
        spread_drift_bps >= config.watch_spread_drift_bps
        or depth_fade_ratio >= config.watch_depth_fade_ratio
        or quote_age_seconds >= config.watch_quote_age_seconds
        or fee_friction_bps >= config.watch_fee_friction_bps
        or catalyst_pressure >= config.watch_catalyst_pressure
        or aggregate_recheck_pressure >= config.watch_aggregate_recheck_pressure
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    observation: ResearchMarketEventCostRecheckObservation,
    aggregate_recheck_pressure: Decimal,
    status: str,
    config: ResearchMarketEventCostRecheckQueueConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    _append_threshold_reason(
        codes,
        "spread_drift",
        observation.spread_drift_bps,
        config.watch_spread_drift_bps,
        config.block_spread_drift_bps,
    )
    _append_threshold_reason(
        codes,
        "depth_fade",
        observation.depth_fade_ratio,
        config.watch_depth_fade_ratio,
        config.block_depth_fade_ratio,
    )
    _append_threshold_reason(
        codes,
        "quote_age",
        observation.quote_age_seconds,
        config.watch_quote_age_seconds,
        config.block_quote_age_seconds,
    )
    _append_threshold_reason(
        codes,
        "fee_friction",
        observation.fee_friction_bps,
        config.watch_fee_friction_bps,
        config.block_fee_friction_bps,
    )
    _append_threshold_reason(
        codes,
        "catalyst_pressure",
        observation.catalyst_pressure,
        config.watch_catalyst_pressure,
        config.block_catalyst_pressure,
    )
    codes.append(f"aggregate_recheck_pressure_{status}")
    for reason_code in observation.reason_codes:
        codes.append(f"input_{reason_code}")
    return _normalize_reason_codes(tuple(codes))


def _append_threshold_reason(
    codes: list[str],
    label: str,
    value: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> None:
    if value >= block_threshold:
        codes.append(f"{label}_block")
    elif value >= watch_threshold:
        codes.append(f"{label}_watch")


def _summary_reason_codes(
    rows: tuple[ResearchMarketEventCostRecheckQueueRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_cost_recheck_candidates",)
    return tuple(sorted({code for row in rows for code in row.reason_codes}))


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("no_cost_recheck_candidates",):
        return "block"
    if "aggregate_recheck_pressure_block" in reason_codes:
        return "block"
    if any(code.endswith("_block") for code in reason_codes):
        return "block"
    if "aggregate_recheck_pressure_watch" in reason_codes:
        return "watch"
    if any(code.endswith("_watch") for code in reason_codes):
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchMarketEventCostRecheckQueueRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchMarketEventCostRecheckQueueReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketEventCostRecheckQueueReasonCodeCount(
                reason_code=reason_codes[0],
                count=_ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchMarketEventCostRecheckQueueReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _normalize_observations(
    observations: Iterable[object],
) -> tuple[ResearchMarketEventCostRecheckObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        values = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    normalized = tuple(_coerce_observation(value) for value in values)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.event_bucket,
                item.cost_surface_bucket,
                item.observed_at,
            ),
        ),
    )


def _coerce_observation(value: object) -> ResearchMarketEventCostRecheckObservation:
    if type(value) is ResearchMarketEventCostRecheckObservation:
        _require_hard_flags("observation", value)
        return value
    _require_hard_flags("observation", value)
    return ResearchMarketEventCostRecheckObservation(
        event_bucket=_field_value(value, "event_bucket"),
        cost_surface_bucket=_field_value(value, "cost_surface_bucket"),
        observed_at=_field_value(value, "observed_at"),
        spread_drift_bps=_field_value(value, "spread_drift_bps"),
        depth_fade_ratio=_field_value(value, "depth_fade_ratio"),
        quote_age_seconds=_field_value(value, "quote_age_seconds"),
        fee_friction_bps=_field_value(value, "fee_friction_bps"),
        catalyst_pressure=_field_value(value, "catalyst_pressure"),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _normalize_rows(
    rows: tuple[ResearchMarketEventCostRecheckQueueRow, ...],
) -> tuple[ResearchMarketEventCostRecheckQueueRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketEventCostRecheckQueueRow:
            raise ValueError("rows must contain ResearchMarketEventCostRecheckQueueRow values")
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.queue_item_digest))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by queue_item_digest")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchMarketEventCostRecheckQueueReasonCodeCount, ...],
) -> tuple[ResearchMarketEventCostRecheckQueueReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchMarketEventCostRecheckQueueReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketEventCostRecheckQueueReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row_consistency(row: ResearchMarketEventCostRecheckQueueRow) -> None:
    if row.recheck_required is not (row.status != "pass"):
        raise ValueError("recheck_required must match status")
    if f"aggregate_recheck_pressure_{row.status}" not in row.reason_codes:
        raise ValueError("reason_codes must include aggregate status code")
    expected_digest = _queue_item_digest(row)
    if row.queue_item_digest != expected_digest:
        raise ValueError("queue_item_digest must match row inputs")


def _validate_report_consistency(report: ResearchMarketEventCostRecheckQueueReport) -> None:
    if report.item_count != _decimal_count(len(report.rows)):
        raise ValueError("item_count must match rows")
    if report.queued_recheck_count != _decimal_count(
        sum(1 for row in report.rows if row.recheck_required),
    ):
        raise ValueError("queued_recheck_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_aggregate_recheck_pressure != _average_aggregate_recheck_pressure(
        report.rows,
    ):
        raise ValueError("average_aggregate_recheck_pressure must match rows")
    if report.max_aggregate_recheck_pressure != _max_aggregate_recheck_pressure(report.rows):
        raise ValueError("max_aggregate_recheck_pressure must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")
    if report.status != _summary_status(report.reason_codes):
        raise ValueError("status must match reason_codes")


def _status_count(
    rows: tuple[ResearchMarketEventCostRecheckQueueRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _average_aggregate_recheck_pressure(
    rows: tuple[ResearchMarketEventCostRecheckQueueRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _average(tuple(row.aggregate_recheck_pressure for row in rows))


def _max_aggregate_recheck_pressure(
    rows: tuple[ResearchMarketEventCostRecheckQueueRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return max(row.aggregate_recheck_pressure for row in rows)


def _queue_item_digest(value: object) -> str:
    digest_payload = {
        "event_bucket": _payload_value(_field_value(value, "event_bucket")),
        "cost_surface_bucket": _payload_value(_field_value(value, "cost_surface_bucket")),
        "observed_at": _payload_value(_field_value(value, "observed_at")),
    }
    return _internal_digest(digest_payload)


def _public_report_payload(
    report: ResearchMarketEventCostRecheckQueueReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    values: dict[str, object] = {
        field_name: getattr(report, field_name)
        for field_name in _REPORT_PUBLIC_PAYLOAD_FIELDS
    }
    values["rows"] = report.rows
    values["reason_code_counts"] = report.reason_code_counts
    if include_digest:
        values["payload_digest"] = report.payload_digest
    return _public_report_payload_from_values(values, include_digest=include_digest)


def _public_report_payload_from_values(
    values: Mapping[str, object],
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload = {
        field_name: _payload_value(values[field_name])
        for field_name in _REPORT_PUBLIC_PAYLOAD_FIELDS
    }
    payload["rows"] = [
        _public_dataclass_payload(row, _ROW_PUBLIC_PAYLOAD_FIELDS)
        for row in values["rows"]  # type: ignore[index]
    ]
    payload["reason_code_counts"] = [
        _public_dataclass_payload(count, _REASON_COUNT_PUBLIC_PAYLOAD_FIELDS)
        for count in values["reason_code_counts"]  # type: ignore[index]
    ]
    if include_digest:
        payload["payload_digest"] = _payload_value(values["payload_digest"])
    return payload


def _public_dataclass_payload(
    value: object,
    field_names: tuple[str, ...],
) -> dict[str, Any]:
    return {
        field_name: _payload_value(getattr(value, field_name))
        for field_name in field_names
    }


def _payload_without_digest(payload: Mapping[str, object]) -> dict[str, Any]:
    return {str(key): item for key, item in payload.items() if key != "payload_digest"}


def _payload_digest(payload: Mapping[str, object]) -> str:
    ready_payload = _payload_value(payload)
    _reject_unsafe_public_payload(ready_payload)
    return _internal_digest(ready_payload)


def _internal_digest(payload: Mapping[str, object]) -> str:
    ready_payload = _payload_value(payload)
    canonical = json.dumps(
        ready_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _payload_value(value: object) -> Any:
    if value is None:
        return None
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or type(value) is float:
        raise ValueError("numeric payload values must use Decimal strings")
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): _payload_value(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_payload_value(item) for item in value]
    raise ValueError("payload value is not JSON safe")


def _reject_unsafe_public_payload(value: object) -> None:
    if type(value) is str:
        _reject_unsafe_public_text("payload", value)
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            if key in _PUBLIC_PAYLOAD_FIELD_DENYLIST:
                raise ValueError(f"public payload must not include {key}")
            _reject_unsafe_public_text("payload key", key)
            _reject_unsafe_public_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if value is None or type(value) is bool:
        return
    raise ValueError("payload contains a non-public value")


def _reject_unsafe_constructor_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_constructor_payload(f"{label}.{field.name}", getattr(value, field.name))
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)
        return
    if isinstance(value, tuple):
        for item in value:
            _reject_unsafe_constructor_payload(label, item)
        return
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    raise ValueError(f"{label} contains an unsupported public value")


def _require_payload_flags(payload: Mapping[str, object]) -> None:
    for flag_name in _PHASE_FLAG_FIELDS:
        if payload.get(flag_name) is not True:
            raise ValueError(f"{flag_name} must be True")
    for row in payload.get("rows", ()):
        if isinstance(row, Mapping):
            for flag_name in _PHASE_FLAG_FIELDS:
                if row.get(flag_name) is not True:
                    raise ValueError(f"{flag_name} must be True")
    for count in payload.get("reason_code_counts", ()):
        if isinstance(count, Mapping):
            for flag_name in _PHASE_FLAG_FIELDS:
                if count.get(flag_name) is not True:
                    raise ValueError(f"{flag_name} must be True")


def _field_value(value: object, field_name: str, *, default: object = _MISSING) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{field_name} is required")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUS_VALUES:
        raise ValueError(f"{field_name} must be one of pass/watch/block")
    return value


def _require_reason_code(value: object) -> str:
    if type(value) is not str:
        raise ValueError("reason_code must be a string")
    _require_public_identifier("reason_code", value)
    if value not in _KNOWN_REASON_CODES and not value.startswith("input_"):
        raise ValueError("reason_code must be supported")
    return value


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    for reason_code in reason_codes:
        valid_reason_code = _require_reason_code(reason_code)
        if valid_reason_code not in normalized:
            normalized.append(valid_reason_code)
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    return tuple(normalized)


def _normalize_input_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    for reason_code in reason_codes:
        valid_reason_code = _require_public_identifier("reason_codes", reason_code)
        if valid_reason_code.startswith("input_"):
            raise ValueError("reason_codes must not use reserved prefixes")
        if valid_reason_code in _KNOWN_REASON_CODES:
            raise ValueError("reason_codes must be caller-specific")
        if valid_reason_code not in normalized:
            normalized.append(valid_reason_code)
    return tuple(normalized)


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_text(field_name, value)
    return value


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return value.quantize(_QUANT, rounding=ROUND_HALF_UP)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_optional_probability_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(field_name, value)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole number")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole number")
    return normalized


def _require_threshold_pair(
    watch_name: str,
    watch_value: Decimal,
    block_name: str,
    block_value: Decimal,
) -> None:
    if block_value <= watch_value:
        raise ValueError(f"{block_name} must exceed {watch_name}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _pressure(value: Decimal, block_threshold: Decimal) -> Decimal:
    if block_threshold <= _ZERO:
        raise ValueError("block threshold must be positive")
    return _clamp_probability(value / block_threshold)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _clamp_probability(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO.quantize(_QUANT)
    if normalized > _ONE:
        return _ONE.quantize(_QUANT)
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT)
