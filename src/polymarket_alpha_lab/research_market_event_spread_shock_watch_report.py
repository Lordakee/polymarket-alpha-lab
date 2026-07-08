"""Public-safe report-only event-domain spread shock watch report."""

from __future__ import annotations

from dataclasses import InitVar, asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from hashlib import sha256
from json import dumps
import re
from typing import Any, Iterable


DEFAULT_RESEARCH_MARKET_EVENT_SPREAD_SHOCK_WATCH_CONFIG_VERSION = (
    "research-market-event-spread-shock-watch-report-v0"
)

ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
SPREAD_SHOCK_WATCH_STATUSES = ("pass", "watch", "block")
HARD_FLAG_FIELDS = ("paper_only", "report_only", "readonly")

_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_UNSAFE_PUBLIC_FRAGMENTS = (
    "raw_market",
    "market_id",
    "condition_id",
    "source_id",
    "raw_source",
    "auth",
    "token",
    "api_key",
    "secret",
    "credential",
    "wallet",
    "private_key",
    "session",
    "cookie",
    "bearer",
    "order",
    "trade",
    "trading",
    "position",
    "recommend",
    "recommendation",
    "sizing",
    "database",
    "network",
    "live_execution",
)


@dataclass(frozen=True)
class ResearchMarketEventSpreadShockWatchConfig:
    config_version: str = DEFAULT_RESEARCH_MARKET_EVENT_SPREAD_SHOCK_WATCH_CONFIG_VERSION
    watch_shock_score: Decimal = Decimal("0.250000")
    block_shock_score: Decimal = Decimal("0.750000")
    pass_spread_widening_bps: Decimal = Decimal("50.000000")
    block_spread_widening_bps: Decimal = Decimal("230.000000")
    pass_depth_fade_ratio: Decimal = Decimal("0.100000")
    block_depth_fade_ratio: Decimal = Decimal("0.700000")
    pass_quote_staleness_seconds: Decimal = Decimal("120.000000")
    block_quote_staleness_seconds: Decimal = Decimal("900.000000")
    pass_catalyst_pressure_score: Decimal = Decimal("0.300000")
    block_catalyst_pressure_score: Decimal = Decimal("0.800000")
    pass_cost_friction_score: Decimal = Decimal("0.150000")
    block_cost_friction_score: Decimal = Decimal("0.650000")
    spread_widening_weight: Decimal = Decimal("0.300000")
    depth_fade_weight: Decimal = Decimal("0.250000")
    quote_staleness_weight: Decimal = Decimal("0.150000")
    catalyst_pressure_weight: Decimal = Decimal("0.200000")
    cost_friction_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketEventSpreadShockWatchConfig:
            raise TypeError(
                "ResearchMarketEventSpreadShockWatchConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketEventSpreadShockWatchConfig:
            raise ValueError(
                "config must be exactly ResearchMarketEventSpreadShockWatchConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        for field_name in (
            "watch_shock_score",
            "block_shock_score",
            "pass_depth_fade_ratio",
            "block_depth_fade_ratio",
            "pass_catalyst_pressure_score",
            "block_catalyst_pressure_score",
            "pass_cost_friction_score",
            "block_cost_friction_score",
            "spread_widening_weight",
            "depth_fade_weight",
            "quote_staleness_weight",
            "catalyst_pressure_weight",
            "cost_friction_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pass_spread_widening_bps",
            "block_spread_widening_bps",
            "pass_quote_staleness_seconds",
            "block_quote_staleness_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_shock_score <= self.watch_shock_score:
            raise ValueError("block_shock_score must exceed watch_shock_score")
        if self.block_spread_widening_bps <= self.pass_spread_widening_bps:
            raise ValueError(
                "block_spread_widening_bps must exceed pass_spread_widening_bps",
            )
        if self.block_depth_fade_ratio <= self.pass_depth_fade_ratio:
            raise ValueError("block_depth_fade_ratio must exceed pass_depth_fade_ratio")
        if self.block_quote_staleness_seconds <= self.pass_quote_staleness_seconds:
            raise ValueError(
                "block_quote_staleness_seconds must exceed "
                "pass_quote_staleness_seconds",
            )
        if self.block_catalyst_pressure_score <= self.pass_catalyst_pressure_score:
            raise ValueError(
                "block_catalyst_pressure_score must exceed "
                "pass_catalyst_pressure_score",
            )
        if self.block_cost_friction_score <= self.pass_cost_friction_score:
            raise ValueError(
                "block_cost_friction_score must exceed pass_cost_friction_score",
            )
        if (
            self.spread_widening_weight
            + self.depth_fade_weight
            + self.quote_staleness_weight
            + self.catalyst_pressure_weight
            + self.cost_friction_weight
        ) != ONE:
            raise ValueError("spread shock component weights must sum to 1.000000")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketEventSpreadShockObservation:
    event_domain: str
    observed_at: datetime
    spread_widening_bps: Decimal
    depth_fade_ratio: Decimal
    quote_staleness_seconds: Decimal
    catalyst_pressure_score: Decimal
    cost_friction_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketEventSpreadShockObservation:
            raise TypeError(
                "ResearchMarketEventSpreadShockObservation does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketEventSpreadShockObservation:
            raise ValueError(
                "observation must be exactly ResearchMarketEventSpreadShockObservation",
            )
        _require_public_identifier("event_domain", self.event_domain)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("spread_widening_bps", "quote_staleness_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "depth_fade_ratio",
            "catalyst_pressure_score",
            "cost_friction_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchMarketEventSpreadShockWatchItem:
    event_domain: str
    first_observed_at: datetime
    last_observed_at: datetime
    observation_count: Decimal
    average_spread_widening_bps: Decimal
    max_spread_widening_bps: Decimal
    average_depth_fade_ratio: Decimal
    max_depth_fade_ratio: Decimal
    max_quote_staleness_seconds: Decimal
    average_catalyst_pressure_score: Decimal
    max_catalyst_pressure_score: Decimal
    average_cost_friction_score: Decimal
    max_cost_friction_score: Decimal
    spread_widening_pressure: Decimal
    depth_fade_pressure: Decimal
    quote_staleness_pressure: Decimal
    catalyst_pressure_component: Decimal
    cost_friction_pressure: Decimal
    shock_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[
        ResearchMarketEventSpreadShockWatchConfig | None
    ] = None

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketEventSpreadShockWatchItem:
            raise TypeError(
                "ResearchMarketEventSpreadShockWatchItem does not support subclassing",
            )

    def __post_init__(
        self,
        validation_config: ResearchMarketEventSpreadShockWatchConfig | None,
    ) -> None:
        if type(self) is not ResearchMarketEventSpreadShockWatchItem:
            raise ValueError("item must be exactly ResearchMarketEventSpreadShockWatchItem")
        _require_public_identifier("event_domain", self.event_domain)
        object.__setattr__(
            self,
            "first_observed_at",
            _as_utc("first_observed_at", self.first_observed_at),
        )
        object.__setattr__(
            self,
            "last_observed_at",
            _as_utc("last_observed_at", self.last_observed_at),
        )
        if self.first_observed_at > self.last_observed_at:
            raise ValueError("first_observed_at must be on or before last_observed_at")
        for field_name in (
            "observation_count",
            "average_spread_widening_bps",
            "max_spread_widening_bps",
            "max_quote_staleness_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_depth_fade_ratio",
            "max_depth_fade_ratio",
            "average_catalyst_pressure_score",
            "max_catalyst_pressure_score",
            "average_cost_friction_score",
            "max_cost_friction_score",
            "spread_widening_pressure",
            "depth_fade_pressure",
            "quote_staleness_pressure",
            "catalyst_pressure_component",
            "cost_friction_pressure",
            "shock_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _validate_item_consistency(
            self,
            config=validation_config or ResearchMarketEventSpreadShockWatchConfig(),
        )
        _require_hard_flags("item", self)


@dataclass(frozen=True)
class ResearchMarketEventSpreadShockReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketEventSpreadShockReasonCodeCount:
            raise TypeError(
                "ResearchMarketEventSpreadShockReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketEventSpreadShockReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchMarketEventSpreadShockReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchMarketEventSpreadShockWatchReport:
    generated_at: datetime
    config_version: str
    domain_count: Decimal
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    spread_widening_count: Decimal
    depth_fade_count: Decimal
    quote_staleness_count: Decimal
    catalyst_pressure_count: Decimal
    cost_friction_count: Decimal
    average_shock_score: Decimal | None
    max_shock_score: Decimal
    status: str
    items: tuple[ResearchMarketEventSpreadShockWatchItem, ...]
    reason_code_counts: tuple[ResearchMarketEventSpreadShockReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketEventSpreadShockWatchReport:
            raise TypeError(
                "ResearchMarketEventSpreadShockWatchReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketEventSpreadShockWatchReport:
            raise ValueError(
                "report must be exactly ResearchMarketEventSpreadShockWatchReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_identifier("config_version", self.config_version)
        for field_name in (
            "domain_count",
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
            "spread_widening_count",
            "depth_fade_count",
            "quote_staleness_count",
            "catalyst_pressure_count",
            "cost_friction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_shock_score",
            _require_optional_ratio_decimal(
                "average_shock_score",
                self.average_shock_score,
            ),
        )
        object.__setattr__(
            self,
            "max_shock_score",
            _require_ratio_decimal("max_shock_score", self.max_shock_score),
        )
        _require_status("status", self.status)
        object.__setattr__(self, "items", _normalize_items(self.items))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, Any]:
        return research_market_event_spread_shock_watch_payload(self)


def build_research_market_event_spread_shock_watch_report(
    observations: Iterable[ResearchMarketEventSpreadShockObservation],
    *,
    generated_at: datetime,
    config: ResearchMarketEventSpreadShockWatchConfig | None = None,
) -> ResearchMarketEventSpreadShockWatchReport:
    """Build a deterministic local report of event-domain spread shock watch items."""

    if config is None:
        config = ResearchMarketEventSpreadShockWatchConfig()
    if type(config) is not ResearchMarketEventSpreadShockWatchConfig:
        raise ValueError(
            "config must be a ResearchMarketEventSpreadShockWatchConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    for observation in normalized_observations:
        if observation.observed_at > generated_at_utc:
            raise ValueError("observed_at must be on or before generated_at")
    items = _build_items(normalized_observations, config=config)
    reason_codes = _report_reason_codes(items)
    values: dict[str, Any] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "domain_count": _count(len(items)),
        "observation_count": _count(len(normalized_observations)),
        "pass_count": _count(_status_count(items, "pass")),
        "watch_count": _count(_status_count(items, "watch")),
        "block_count": _count(_status_count(items, "block")),
        "spread_widening_count": _count(
            _item_reason_count(items, "aggregate_spread_widening_watch")
            + _item_reason_count(items, "aggregate_spread_widening_block"),
        ),
        "depth_fade_count": _count(
            _item_reason_count(items, "depth_fade_watch")
            + _item_reason_count(items, "depth_fade_block"),
        ),
        "quote_staleness_count": _count(
            _item_reason_count(items, "quote_staleness_watch")
            + _item_reason_count(items, "quote_staleness_block"),
        ),
        "catalyst_pressure_count": _count(
            _item_reason_count(items, "catalyst_pressure_watch")
            + _item_reason_count(items, "catalyst_pressure_block"),
        ),
        "cost_friction_count": _count(
            _item_reason_count(items, "cost_friction_watch")
            + _item_reason_count(items, "cost_friction_block"),
        ),
        "average_shock_score": _average_shock_score(items),
        "max_shock_score": _max_ratio(tuple(item.shock_score for item in items)),
        "status": _report_status(items),
        "items": items,
        "reason_code_counts": _reason_code_counts(items, reason_codes),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchMarketEventSpreadShockWatchReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_market_event_spread_shock_watch_payload(
    report: ResearchMarketEventSpreadShockWatchReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchMarketEventSpreadShockWatchReport:
        _require_hard_flags("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchMarketEventSpreadShockWatchReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("payload", payload)
    _require_hard_flags("payload", _DictFlags(payload))
    return payload


def research_market_event_spread_shock_watch_digest(
    report: ResearchMarketEventSpreadShockWatchReport | dict[str, Any],
) -> str:
    if type(report) is ResearchMarketEventSpreadShockWatchReport:
        return report.derived_validation_digest
    payload = research_market_event_spread_shock_watch_payload(report)
    encoded = dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(encoded.encode("utf-8")).hexdigest()


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


def _build_items(
    observations: tuple[ResearchMarketEventSpreadShockObservation, ...],
    *,
    config: ResearchMarketEventSpreadShockWatchConfig,
) -> tuple[ResearchMarketEventSpreadShockWatchItem, ...]:
    by_domain: dict[str, list[ResearchMarketEventSpreadShockObservation]] = {}
    for observation in observations:
        by_domain.setdefault(observation.event_domain, []).append(observation)
    items = tuple(
        _item_from_domain_rows(event_domain, tuple(domain_rows), config=config)
        for event_domain, domain_rows in by_domain.items()
    )
    return tuple(sorted(items, key=_item_sort_key))


def _item_from_domain_rows(
    event_domain: str,
    observations: tuple[ResearchMarketEventSpreadShockObservation, ...],
    *,
    config: ResearchMarketEventSpreadShockWatchConfig,
) -> ResearchMarketEventSpreadShockWatchItem:
    average_spread = _average_decimal(
        tuple(observation.spread_widening_bps for observation in observations),
    )
    average_depth = _average_ratio(
        tuple(observation.depth_fade_ratio for observation in observations),
    )
    max_quote_staleness = _max_decimal(
        tuple(observation.quote_staleness_seconds for observation in observations),
    )
    average_catalyst = _average_ratio(
        tuple(observation.catalyst_pressure_score for observation in observations),
    )
    average_cost = _average_ratio(
        tuple(observation.cost_friction_score for observation in observations),
    )
    spread_pressure = _threshold_pressure(
        average_spread,
        pass_value=config.pass_spread_widening_bps,
        block_value=config.block_spread_widening_bps,
    )
    depth_pressure = _threshold_pressure(
        average_depth,
        pass_value=config.pass_depth_fade_ratio,
        block_value=config.block_depth_fade_ratio,
    )
    quote_pressure = _threshold_pressure(
        max_quote_staleness,
        pass_value=config.pass_quote_staleness_seconds,
        block_value=config.block_quote_staleness_seconds,
    )
    catalyst_pressure = _threshold_pressure(
        average_catalyst,
        pass_value=config.pass_catalyst_pressure_score,
        block_value=config.block_catalyst_pressure_score,
    )
    cost_pressure = _threshold_pressure(
        average_cost,
        pass_value=config.pass_cost_friction_score,
        block_value=config.block_cost_friction_score,
    )
    shock_score = _shock_score(
        spread_widening_pressure=spread_pressure,
        depth_fade_pressure=depth_pressure,
        quote_staleness_pressure=quote_pressure,
        catalyst_pressure_component=catalyst_pressure,
        cost_friction_pressure=cost_pressure,
        config=config,
    )
    status = _item_status(shock_score, config=config)
    return ResearchMarketEventSpreadShockWatchItem(
        event_domain=event_domain,
        first_observed_at=min(observation.observed_at for observation in observations),
        last_observed_at=max(observation.observed_at for observation in observations),
        observation_count=_count(len(observations)),
        average_spread_widening_bps=average_spread,
        max_spread_widening_bps=_max_decimal(
            tuple(observation.spread_widening_bps for observation in observations),
        ),
        average_depth_fade_ratio=average_depth,
        max_depth_fade_ratio=_max_ratio(
            tuple(observation.depth_fade_ratio for observation in observations),
        ),
        max_quote_staleness_seconds=max_quote_staleness,
        average_catalyst_pressure_score=average_catalyst,
        max_catalyst_pressure_score=_max_ratio(
            tuple(observation.catalyst_pressure_score for observation in observations),
        ),
        average_cost_friction_score=average_cost,
        max_cost_friction_score=_max_ratio(
            tuple(observation.cost_friction_score for observation in observations),
        ),
        spread_widening_pressure=spread_pressure,
        depth_fade_pressure=depth_pressure,
        quote_staleness_pressure=quote_pressure,
        catalyst_pressure_component=catalyst_pressure,
        cost_friction_pressure=cost_pressure,
        shock_score=shock_score,
        status=status,
        reason_codes=_item_reason_codes(
            observations,
            spread_widening_pressure=spread_pressure,
            depth_fade_pressure=depth_pressure,
            quote_staleness_pressure=quote_pressure,
            catalyst_pressure_component=catalyst_pressure,
            cost_friction_pressure=cost_pressure,
            status=status,
        ),
        validation_config=config,
    )


def _item_reason_codes(
    observations: tuple[ResearchMarketEventSpreadShockObservation, ...],
    *,
    spread_widening_pressure: Decimal,
    depth_fade_pressure: Decimal,
    quote_staleness_pressure: Decimal,
    catalyst_pressure_component: Decimal,
    cost_friction_pressure: Decimal,
    status: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = [f"spread_shock_{status}"]
    _append_pressure_reason(
        reason_codes,
        prefix="aggregate_spread_widening",
        pressure=spread_widening_pressure,
    )
    _append_pressure_reason(reason_codes, prefix="depth_fade", pressure=depth_fade_pressure)
    _append_pressure_reason(
        reason_codes,
        prefix="quote_staleness",
        pressure=quote_staleness_pressure,
    )
    _append_pressure_reason(
        reason_codes,
        prefix="catalyst_pressure",
        pressure=catalyst_pressure_component,
    )
    _append_pressure_reason(
        reason_codes,
        prefix="cost_friction",
        pressure=cost_friction_pressure,
    )
    for observation in observations:
        for reason_code in observation.reason_codes:
            reason_codes.append(f"input_{reason_code}")
    return tuple(sorted(set(reason_codes)))


def _append_pressure_reason(
    reason_codes: list[str],
    *,
    prefix: str,
    pressure: Decimal,
) -> None:
    if pressure >= ONE:
        reason_codes.append(f"{prefix}_block")
    elif pressure > ZERO:
        reason_codes.append(f"{prefix}_watch")


def _validate_item_consistency(
    item: ResearchMarketEventSpreadShockWatchItem,
    *,
    config: ResearchMarketEventSpreadShockWatchConfig,
) -> None:
    expected_spread_pressure = _threshold_pressure(
        item.average_spread_widening_bps,
        pass_value=config.pass_spread_widening_bps,
        block_value=config.block_spread_widening_bps,
    )
    expected_depth_pressure = _threshold_pressure(
        item.average_depth_fade_ratio,
        pass_value=config.pass_depth_fade_ratio,
        block_value=config.block_depth_fade_ratio,
    )
    expected_quote_pressure = _threshold_pressure(
        item.max_quote_staleness_seconds,
        pass_value=config.pass_quote_staleness_seconds,
        block_value=config.block_quote_staleness_seconds,
    )
    expected_catalyst_pressure = _threshold_pressure(
        item.average_catalyst_pressure_score,
        pass_value=config.pass_catalyst_pressure_score,
        block_value=config.block_catalyst_pressure_score,
    )
    expected_cost_pressure = _threshold_pressure(
        item.average_cost_friction_score,
        pass_value=config.pass_cost_friction_score,
        block_value=config.block_cost_friction_score,
    )
    expected_shock_score = _shock_score(
        spread_widening_pressure=expected_spread_pressure,
        depth_fade_pressure=expected_depth_pressure,
        quote_staleness_pressure=expected_quote_pressure,
        catalyst_pressure_component=expected_catalyst_pressure,
        cost_friction_pressure=expected_cost_pressure,
        config=config,
    )
    if item.spread_widening_pressure != expected_spread_pressure:
        raise ValueError("spread_widening_pressure must match item aggregates")
    if item.depth_fade_pressure != expected_depth_pressure:
        raise ValueError("depth_fade_pressure must match item aggregates")
    if item.quote_staleness_pressure != expected_quote_pressure:
        raise ValueError("quote_staleness_pressure must match item aggregates")
    if item.catalyst_pressure_component != expected_catalyst_pressure:
        raise ValueError("catalyst_pressure_component must match item aggregates")
    if item.cost_friction_pressure != expected_cost_pressure:
        raise ValueError("cost_friction_pressure must match item aggregates")
    if item.shock_score != expected_shock_score:
        raise ValueError("shock_score must match item pressures")
    if item.status != _item_status(item.shock_score, config=config):
        raise ValueError("status must match shock_score")


def _validate_report_consistency(
    report: ResearchMarketEventSpreadShockWatchReport,
) -> None:
    items = report.items
    if report.domain_count != _count(len(items)):
        raise ValueError("domain_count must match items")
    if report.observation_count != sum((item.observation_count for item in items), ZERO):
        raise ValueError("observation_count must match items")
    for field_name, status in (
        ("pass_count", "pass"),
        ("watch_count", "watch"),
        ("block_count", "block"),
    ):
        if getattr(report, field_name) != _count(_status_count(items, status)):
            raise ValueError(f"{field_name} must match items")
    for field_name, watch_code, block_code in (
        (
            "spread_widening_count",
            "aggregate_spread_widening_watch",
            "aggregate_spread_widening_block",
        ),
        ("depth_fade_count", "depth_fade_watch", "depth_fade_block"),
        ("quote_staleness_count", "quote_staleness_watch", "quote_staleness_block"),
        (
            "catalyst_pressure_count",
            "catalyst_pressure_watch",
            "catalyst_pressure_block",
        ),
        ("cost_friction_count", "cost_friction_watch", "cost_friction_block"),
    ):
        if getattr(report, field_name) != _count(
            _item_reason_count(items, watch_code) + _item_reason_count(items, block_code),
        ):
            raise ValueError(f"{field_name} must match items")
    if report.average_shock_score != _average_shock_score(items):
        raise ValueError("average_shock_score must match items")
    if report.max_shock_score != _max_ratio(tuple(item.shock_score for item in items)):
        raise ValueError("max_shock_score must match items")
    if report.status != _report_status(items):
        raise ValueError("status must match items")
    if report.reason_codes != _report_reason_codes(items):
        raise ValueError("reason_codes must match items")
    if report.reason_code_counts != _reason_code_counts(items, report.reason_codes):
        raise ValueError("reason_code_counts must match items")
    if items != tuple(sorted(items, key=_item_sort_key)):
        raise ValueError("items must use deterministic sorting")


def _normalize_observations(
    observations: Iterable[ResearchMarketEventSpreadShockObservation],
) -> tuple[ResearchMarketEventSpreadShockObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must be an iterable")
    normalized = tuple(observations)
    for observation in normalized:
        if type(observation) is not ResearchMarketEventSpreadShockObservation:
            raise ValueError(
                "observations must contain ResearchMarketEventSpreadShockObservation",
            )
        _require_hard_flags("observation", observation)
    return normalized


def _normalize_items(
    items: object,
) -> tuple[ResearchMarketEventSpreadShockWatchItem, ...]:
    if type(items) is not tuple:
        raise ValueError("items must be a tuple")
    for item in items:
        if type(item) is not ResearchMarketEventSpreadShockWatchItem:
            raise ValueError("items must contain ResearchMarketEventSpreadShockWatchItem")
        _require_hard_flags("item", item)
    return items


def _normalize_reason_code_counts(
    rows: object,
) -> tuple[ResearchMarketEventSpreadShockReasonCodeCount, ...]:
    if type(rows) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketEventSpreadShockReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketEventSpreadShockReasonCodeCount",
            )
        _require_hard_flags("reason code count", row)
    return rows


def _threshold_pressure(
    value: Decimal,
    *,
    pass_value: Decimal,
    block_value: Decimal,
) -> Decimal:
    if value <= pass_value:
        return ZERO.quantize(RATIO_QUANTUM)
    if value >= block_value:
        return ONE.quantize(RATIO_QUANTUM)
    return _quantize((value - pass_value) / (block_value - pass_value))


def _shock_score(
    *,
    spread_widening_pressure: Decimal,
    depth_fade_pressure: Decimal,
    quote_staleness_pressure: Decimal,
    catalyst_pressure_component: Decimal,
    cost_friction_pressure: Decimal,
    config: ResearchMarketEventSpreadShockWatchConfig,
) -> Decimal:
    return _quantize(
        spread_widening_pressure * config.spread_widening_weight
        + depth_fade_pressure * config.depth_fade_weight
        + quote_staleness_pressure * config.quote_staleness_weight
        + catalyst_pressure_component * config.catalyst_pressure_weight
        + cost_friction_pressure * config.cost_friction_weight,
    )


def _item_status(
    shock_score: Decimal,
    *,
    config: ResearchMarketEventSpreadShockWatchConfig,
) -> str:
    if shock_score >= config.block_shock_score:
        return "block"
    if shock_score >= config.watch_shock_score:
        return "watch"
    return "pass"


def _item_sort_key(
    item: ResearchMarketEventSpreadShockWatchItem,
) -> tuple[int, str]:
    return (SPREAD_SHOCK_WATCH_STATUSES.index(item.status), item.event_domain)


def _status_count(
    items: tuple[ResearchMarketEventSpreadShockWatchItem, ...],
    status: str,
) -> int:
    return sum(1 for item in items if item.status == status)


def _item_reason_count(
    items: tuple[ResearchMarketEventSpreadShockWatchItem, ...],
    reason_code: str,
) -> int:
    return sum(1 for item in items if reason_code in item.reason_codes)


def _average_shock_score(
    items: tuple[ResearchMarketEventSpreadShockWatchItem, ...],
) -> Decimal | None:
    if not items:
        return None
    return _quantize(sum((item.shock_score for item in items), ZERO) / Decimal(len(items)))


def _report_status(items: tuple[ResearchMarketEventSpreadShockWatchItem, ...]) -> str:
    if not items:
        return "block"
    if any(item.status == "block" for item in items):
        return "block"
    if any(item.status == "watch" for item in items):
        return "watch"
    return "pass"


def _report_reason_codes(
    items: tuple[ResearchMarketEventSpreadShockWatchItem, ...],
) -> tuple[str, ...]:
    if not items:
        return ("no_event_domain_observations",)
    reason_codes: set[str] = set()
    for item in items:
        reason_codes.update(item.reason_codes)
    return tuple(sorted(reason_codes))


def _reason_code_counts(
    items: tuple[ResearchMarketEventSpreadShockWatchItem, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchMarketEventSpreadShockReasonCodeCount, ...]:
    if not items:
        return (
            ResearchMarketEventSpreadShockReasonCodeCount(
                reason_code="no_event_domain_observations",
                count=Decimal("1"),
            ),
        )
    return tuple(
        ResearchMarketEventSpreadShockReasonCodeCount(
            reason_code=reason_code,
            count=_count(sum(1 for item in items if reason_code in item.reason_codes)),
        )
        for reason_code in reason_codes
    )


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    return _require_ratio_decimal("average_ratio", _average_decimal(values))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _max_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(RATIO_QUANTUM)
    return _quantize(max(values))


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count source must be a nonnegative int")
    return Decimal(value)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_optional_ratio_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_ratio_decimal(field_name, value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM, rounding=ROUND_HALF_UP)


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    if _has_unsafe_fragment(value):
        raise ValueError(f"{field_name} has unsafe value")
    return value


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must contain reason code strings")
    if value.strip() != value or value.lower() != value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    if any(character not in "abcdefghijklmnopqrstuvwxyz0123456789_" for character in value):
        raise ValueError(f"{field_name} must contain canonical reason codes")
    if _has_unsafe_fragment(value):
        raise ValueError(f"{field_name} has unsafe value")


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_reason_code(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SPREAD_SHOCK_WATCH_STATUSES:
        raise ValueError(f"{field_name} must be one of {SPREAD_SHOCK_WATCH_STATUSES}")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_fragment(key):
                raise ValueError(f"unsafe field in {label}")
            item_path = key if not path else f"{path}.{key}"
            if key in HARD_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) is str and _has_unsafe_fragment(value):
        raise ValueError(f"{path or label} has unsafe value")
    if type(value) in (float, int):
        raise ValueError(f"{path or label} must use Decimal-derived string values")


def _has_unsafe_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in _UNSAFE_PUBLIC_FRAGMENTS)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal or not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON value must not be an int")
    if type(value) in (str, bool):
        return value
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _report_values_without_digest(
    report: ResearchMarketEventSpreadShockWatchReport,
) -> dict[str, Any]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: dict[str, Any]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload("report digest payload", payload)
    encoded = dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(encoded.encode("utf-8")).hexdigest()


__all__ = (
    "DEFAULT_RESEARCH_MARKET_EVENT_SPREAD_SHOCK_WATCH_CONFIG_VERSION",
    "SPREAD_SHOCK_WATCH_STATUSES",
    "ResearchMarketEventSpreadShockObservation",
    "ResearchMarketEventSpreadShockReasonCodeCount",
    "ResearchMarketEventSpreadShockWatchConfig",
    "ResearchMarketEventSpreadShockWatchItem",
    "ResearchMarketEventSpreadShockWatchReport",
    "build_research_market_event_spread_shock_watch_report",
    "research_market_event_spread_shock_watch_digest",
    "research_market_event_spread_shock_watch_payload",
)
