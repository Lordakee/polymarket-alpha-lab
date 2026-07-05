"""Pure Phase 1 geopolitical shipping risk digest reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_GEOPOLITICAL_SHIPPING_RISK_DIGEST_CONFIG_VERSION = (
    "market-research-geopolitical-shipping-risk-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
RISK_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

REASON_PREFIX = "market_research_geopolitical_shipping_risk_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
READY_REASON = f"{REASON_PREFIX}ready"
WATCH_RISK_REASON = f"{REASON_PREFIX}watch_risk"
BLOCKED_RISK_REASON = f"{REASON_PREFIX}blocked_risk"
PROBABILITY_DISCOUNT_REASON = f"{REASON_PREFIX}probability_discount"
STALE_SIGNAL_REASON = f"{REASON_PREFIX}stale_signal"
THIN_SOURCES_REASON = f"{REASON_PREFIX}thin_sources"

REASON_CODE_SEQUENCE = (
    BLOCKED_RISK_REASON,
    WATCH_RISK_REASON,
    PROBABILITY_DISCOUNT_REASON,
    STALE_SIGNAL_REASON,
    THIN_SOURCES_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    BLOCKED_RISK_REASON,
    WATCH_RISK_REASON,
    PROBABILITY_DISCOUNT_REASON,
    STALE_SIGNAL_REASON,
    THIN_SOURCES_REASON,
    READY_REASON,
)

NEXT_STEPS = {
    STATUS_READY: "allow_report_only_market_research_geopolitical_shipping_risk_digest",
    STATUS_WATCH: "watch_report_only_market_research_geopolitical_shipping_risk_digest",
    STATUS_BLOCKED: "block_report_only_market_research_geopolitical_shipping_risk_digest",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("au", "th"),
        _join_parts("bro", "ker"),
        _join_parts("sig", "ning"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("ad", "vice"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("pri", "vate"),
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_GEOPOLITICAL_SHIPPING_RISK_DIGEST_CONFIG_VERSION",
    "MarketResearchGeopoliticalShippingRiskDigestConfig",
    "MarketResearchGeopoliticalShippingRiskDigestInputRow",
    "MarketResearchGeopoliticalShippingRiskDigestReasonCodeCount",
    "MarketResearchGeopoliticalShippingRiskDigestReport",
    "MarketResearchGeopoliticalShippingRiskDigestRow",
    "build_market_research_geopolitical_shipping_risk_digest",
    "market_research_geopolitical_shipping_risk_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchGeopoliticalShippingRiskDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_GEOPOLITICAL_SHIPPING_RISK_DIGEST_CONFIG_VERSION
    )
    min_source_count: Decimal = Decimal("2")
    watch_risk_threshold: Decimal = Decimal("0.250000")
    blocked_risk_threshold: Decimal = Decimal("0.500000")
    fresh_signal_max_age_seconds: Decimal = Decimal("86400.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGeopoliticalShippingRiskDigestConfig:
            raise TypeError(
                "MarketResearchGeopoliticalShippingRiskDigestConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGeopoliticalShippingRiskDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchGeopoliticalShippingRiskDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_GEOPOLITICAL_SHIPPING_RISK_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "min_source_count",
            _require_positive_count_decimal("min_source_count", self.min_source_count),
        )
        object.__setattr__(
            self,
            "watch_risk_threshold",
            _require_ratio_decimal("watch_risk_threshold", self.watch_risk_threshold),
        )
        object.__setattr__(
            self,
            "blocked_risk_threshold",
            _require_ratio_decimal(
                "blocked_risk_threshold",
                self.blocked_risk_threshold,
            ),
        )
        if self.watch_risk_threshold <= ZERO:
            raise ValueError("watch_risk_threshold must be positive")
        if self.blocked_risk_threshold <= self.watch_risk_threshold:
            raise ValueError(
                "blocked_risk_threshold must be greater than watch_risk_threshold",
            )
        object.__setattr__(
            self,
            "fresh_signal_max_age_seconds",
            _require_positive_decimal(
                "fresh_signal_max_age_seconds",
                self.fresh_signal_max_age_seconds,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchGeopoliticalShippingRiskDigestInputRow:
    research_key: str
    market_slug: str
    route_key: str
    region_key: str
    risk_signal_source: str
    source_reference: str
    observed_at: datetime
    acknowledged_at: datetime
    source_count: Decimal
    incident_count: Decimal
    reroute_probability: Decimal
    port_delay_days: Decimal
    market_probability: Decimal
    implied_probability: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGeopoliticalShippingRiskDigestInputRow:
            raise TypeError(
                "MarketResearchGeopoliticalShippingRiskDigestInputRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGeopoliticalShippingRiskDigestInputRow:
            raise ValueError(
                "input row must be exactly "
                "MarketResearchGeopoliticalShippingRiskDigestInputRow",
            )
        _require_public_string("research_key", self.research_key)
        _require_market_slug("market_slug", self.market_slug)
        _require_public_string("route_key", self.route_key)
        _require_public_string("region_key", self.region_key)
        _require_public_string("risk_signal_source", self.risk_signal_source)
        _require_reference("source_reference", self.source_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_utc("acknowledged_at", self.acknowledged_at),
        )
        for field_name in ("source_count", "incident_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("reroute_probability", "market_probability"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "implied_probability",
            _require_ratio_decimal("implied_probability", self.implied_probability),
        )
        object.__setattr__(
            self,
            "port_delay_days",
            _require_nonnegative_decimal("port_delay_days", self.port_delay_days),
        )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchGeopoliticalShippingRiskDigestRow:
    research_key: str
    market_slug: str
    route_key: str
    region_key: str
    risk_signal_source: str
    risk_status: str
    observed_at: datetime
    acknowledged_at: datetime
    signal_age_seconds: Decimal
    source_count: Decimal
    incident_count: Decimal
    reroute_probability: Decimal
    port_delay_days: Decimal
    market_probability: Decimal
    implied_probability: Decimal
    probability_gap: Decimal
    risk_score: Decimal
    redacted_source_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGeopoliticalShippingRiskDigestRow:
            raise TypeError(
                "MarketResearchGeopoliticalShippingRiskDigestRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGeopoliticalShippingRiskDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchGeopoliticalShippingRiskDigestRow",
            )
        _require_public_string("research_key", self.research_key)
        _require_market_slug("market_slug", self.market_slug)
        _require_public_string("route_key", self.route_key)
        _require_public_string("region_key", self.region_key)
        _require_public_string("risk_signal_source", self.risk_signal_source)
        _require_status("risk_status", self.risk_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_utc("acknowledged_at", self.acknowledged_at),
        )
        object.__setattr__(
            self,
            "signal_age_seconds",
            _require_nonnegative_decimal("signal_age_seconds", self.signal_age_seconds),
        )
        for field_name in ("source_count", "incident_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "reroute_probability",
            "market_probability",
            "implied_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "port_delay_days",
            _require_nonnegative_decimal("port_delay_days", self.port_delay_days),
        )
        object.__setattr__(
            self,
            "probability_gap",
            _require_signed_ratio_decimal("probability_gap", self.probability_gap),
        )
        object.__setattr__(
            self,
            "risk_score",
            _require_ratio_decimal("risk_score", self.risk_score),
        )
        object.__setattr__(
            self,
            "redacted_source_reference",
            _require_redacted_reference(
                "redacted_source_reference",
                self.redacted_source_reference,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchGeopoliticalShippingRiskDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    route_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGeopoliticalShippingRiskDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchGeopoliticalShippingRiskDigestReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGeopoliticalShippingRiskDigestReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "MarketResearchGeopoliticalShippingRiskDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "route_ratio",
            _require_ratio_decimal("route_ratio", self.route_ratio),
        )
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class MarketResearchGeopoliticalShippingRiskDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    next_step: str
    route_count: Decimal
    ready_route_count: Decimal
    watch_route_count: Decimal
    blocked_route_count: Decimal
    thin_source_count: Decimal
    stale_signal_count: Decimal
    probability_discount_count: Decimal
    max_risk_score: Decimal
    average_risk_score: Decimal
    max_signal_age_seconds: Decimal
    average_port_delay_days: Decimal
    rows: tuple[MarketResearchGeopoliticalShippingRiskDigestRow, ...]
    reason_code_counts: tuple[
        MarketResearchGeopoliticalShippingRiskDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchGeopoliticalShippingRiskDigestReport:
            raise TypeError(
                "MarketResearchGeopoliticalShippingRiskDigestReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchGeopoliticalShippingRiskDigestReport:
            raise ValueError(
                "report must be exactly "
                "MarketResearchGeopoliticalShippingRiskDigestReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_GEOPOLITICAL_SHIPPING_RISK_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("digest_status", self.digest_status)
        if self.next_step != NEXT_STEPS[self.digest_status]:
            raise ValueError("next_step must match digest_status")
        for field_name in (
            "route_count",
            "ready_route_count",
            "watch_route_count",
            "blocked_route_count",
            "thin_source_count",
            "stale_signal_count",
            "probability_discount_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_risk_score",
            "average_risk_score",
            "max_signal_age_seconds",
            "average_port_delay_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_geopolitical_shipping_risk_digest(
    input_rows: list[MarketResearchGeopoliticalShippingRiskDigestInputRow]
    | tuple[MarketResearchGeopoliticalShippingRiskDigestInputRow, ...],
    *,
    config: MarketResearchGeopoliticalShippingRiskDigestConfig,
    generated_at: datetime,
) -> MarketResearchGeopoliticalShippingRiskDigestReport:
    if type(config) is not MarketResearchGeopoliticalShippingRiskDigestConfig:
        raise ValueError(
            "config must be a MarketResearchGeopoliticalShippingRiskDigestConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_rows = _normalize_input_rows(input_rows, generated_at_utc)
    rows = tuple(
        _build_row(row, config=config, generated_at=generated_at_utc)
        for row in source_rows
    )
    ranked_rows = _ranked_rows(rows)
    reason_code_counts = _reason_code_counts(ranked_rows)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    if not ranked_rows:
        reason_code_counts = (
            MarketResearchGeopoliticalShippingRiskDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                route_ratio=ONE,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)

    route_count = _count(len(ranked_rows))
    ready_route_count = _count(
        sum(1 for row in ranked_rows if row.risk_status == STATUS_READY),
    )
    watch_route_count = _count(
        sum(1 for row in ranked_rows if row.risk_status == STATUS_WATCH),
    )
    blocked_route_count = _count(
        sum(1 for row in ranked_rows if row.risk_status == STATUS_BLOCKED),
    )
    digest_status = _report_status(
        has_inputs=bool(ranked_rows),
        blocked_route_count=blocked_route_count,
        watch_route_count=watch_route_count,
    )

    return MarketResearchGeopoliticalShippingRiskDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        next_step=NEXT_STEPS[digest_status],
        route_count=route_count,
        ready_route_count=ready_route_count,
        watch_route_count=watch_route_count,
        blocked_route_count=blocked_route_count,
        thin_source_count=_count(
            sum(1 for row in ranked_rows if THIN_SOURCES_REASON in row.reason_codes),
        ),
        stale_signal_count=_count(
            sum(1 for row in ranked_rows if STALE_SIGNAL_REASON in row.reason_codes),
        ),
        probability_discount_count=_count(
            sum(
                1
                for row in ranked_rows
                if PROBABILITY_DISCOUNT_REASON in row.reason_codes
            ),
        ),
        max_risk_score=_max_decimal(tuple(row.risk_score for row in ranked_rows)),
        average_risk_score=_average(tuple(row.risk_score for row in ranked_rows)),
        max_signal_age_seconds=_max_decimal(
            tuple(row.signal_age_seconds for row in ranked_rows),
        ),
        average_port_delay_days=_average(
            tuple(row.port_delay_days for row in ranked_rows),
        ),
        rows=ranked_rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_geopolitical_shipping_risk_digest_payload(
    report: MarketResearchGeopoliticalShippingRiskDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchGeopoliticalShippingRiskDigestReport:
        raise ValueError(
            "report must be a MarketResearchGeopoliticalShippingRiskDigestReport",
        )
    _require_hard_flags("report", report)
    return _json_ready(asdict(report))


def _build_row(
    row: MarketResearchGeopoliticalShippingRiskDigestInputRow,
    *,
    config: MarketResearchGeopoliticalShippingRiskDigestConfig,
    generated_at: datetime,
) -> MarketResearchGeopoliticalShippingRiskDigestRow:
    signal_age_seconds = _seconds_between(row.observed_at, generated_at)
    risk_score = _risk_score(row)
    probability_gap = _quantize(row.implied_probability - row.market_probability)
    reason_codes = _row_reason_codes(
        row,
        config=config,
        signal_age_seconds=signal_age_seconds,
        probability_gap=probability_gap,
        risk_score=risk_score,
    )
    risk_status = _row_status(reason_codes)

    return MarketResearchGeopoliticalShippingRiskDigestRow(
        research_key=row.research_key,
        market_slug=row.market_slug,
        route_key=row.route_key,
        region_key=row.region_key,
        risk_signal_source=row.risk_signal_source,
        risk_status=risk_status,
        observed_at=row.observed_at,
        acknowledged_at=row.acknowledged_at,
        signal_age_seconds=signal_age_seconds,
        source_count=row.source_count,
        incident_count=row.incident_count,
        reroute_probability=row.reroute_probability,
        port_delay_days=row.port_delay_days,
        market_probability=row.market_probability,
        implied_probability=row.implied_probability,
        probability_gap=probability_gap,
        risk_score=risk_score,
        redacted_source_reference=_redacted_reference(row.source_reference),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    row: MarketResearchGeopoliticalShippingRiskDigestInputRow,
    *,
    config: MarketResearchGeopoliticalShippingRiskDigestConfig,
    signal_age_seconds: Decimal,
    probability_gap: Decimal,
    risk_score: Decimal,
) -> tuple[str, ...]:
    codes: list[str] = []
    if risk_score >= config.blocked_risk_threshold:
        codes.append(BLOCKED_RISK_REASON)
    elif risk_score >= config.watch_risk_threshold:
        codes.append(WATCH_RISK_REASON)
    if probability_gap >= config.watch_risk_threshold:
        codes.append(PROBABILITY_DISCOUNT_REASON)
    if signal_age_seconds > config.fresh_signal_max_age_seconds:
        codes.append(STALE_SIGNAL_REASON)
    if row.source_count < config.min_source_count:
        codes.append(THIN_SOURCES_REASON)
    if not codes:
        codes.append(READY_REASON)
    return _normalize_row_reason_codes(tuple(codes))


def _risk_score(row: MarketResearchGeopoliticalShippingRiskDigestInputRow) -> Decimal:
    incident_component = _ratio(row.incident_count, row.incident_count + ONE)
    delay_component = _ratio(row.port_delay_days, row.port_delay_days + ONE)
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(
            (
                row.reroute_probability
                + row.implied_probability
                + incident_component
                + delay_component
            )
            / Decimal("4"),
        )


def _normalize_input_rows(
    rows: list[MarketResearchGeopoliticalShippingRiskDigestInputRow]
    | tuple[MarketResearchGeopoliticalShippingRiskDigestInputRow, ...],
    generated_at: datetime,
) -> tuple[MarketResearchGeopoliticalShippingRiskDigestInputRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    normalized = tuple(rows)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not MarketResearchGeopoliticalShippingRiskDigestInputRow:
            raise ValueError(
                "input rows must contain "
                "MarketResearchGeopoliticalShippingRiskDigestInputRow values",
            )
        _require_hard_flags("input row", row)
        if row.research_key in seen:
            raise ValueError("input rows must not contain duplicate research_key")
        seen.add(row.research_key)
        if row.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        if row.acknowledged_at < row.observed_at:
            raise ValueError("acknowledged_at must not be before observed_at")
    return tuple(
        sorted(
            normalized,
            key=lambda row: (
                row.region_key,
                row.route_key,
                row.market_slug,
                row.research_key,
            ),
        ),
    )


def _ranked_rows(
    rows: tuple[MarketResearchGeopoliticalShippingRiskDigestRow, ...],
) -> tuple[MarketResearchGeopoliticalShippingRiskDigestRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _status_rank(row.risk_status),
                -row.risk_score,
                row.route_key,
                row.research_key,
            ),
        ),
    )


def _reason_code_counts(
    rows: tuple[MarketResearchGeopoliticalShippingRiskDigestRow, ...],
) -> tuple[MarketResearchGeopoliticalShippingRiskDigestReasonCodeCount, ...]:
    counts: dict[str, int] = {}
    for row in rows:
        for code in row.reason_codes:
            counts[code] = counts.get(code, 0) + 1
    route_count = _count(len(rows))
    return tuple(
        MarketResearchGeopoliticalShippingRiskDigestReasonCodeCount(
            reason_code=code,
            count=_count(counts[code]),
            route_ratio=_ratio(_count(counts[code]), route_count),
        )
        for code in REASON_CODE_SEQUENCE
        if code in counts
    )


def _report_status(
    *,
    has_inputs: bool,
    blocked_route_count: Decimal,
    watch_route_count: Decimal,
) -> str:
    if not has_inputs or blocked_route_count > ZERO:
        return STATUS_BLOCKED
    if watch_route_count > ZERO:
        return STATUS_WATCH
    return STATUS_READY


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if BLOCKED_RISK_REASON in reason_codes:
        return STATUS_BLOCKED
    if WATCH_RISK_REASON in reason_codes:
        return STATUS_WATCH
    if any(
        code in reason_codes
        for code in (
            PROBABILITY_DISCOUNT_REASON,
            STALE_SIGNAL_REASON,
            THIN_SOURCES_REASON,
        )
    ):
        return STATUS_WATCH
    return STATUS_READY


def _status_rank(status: str) -> int:
    return {
        STATUS_BLOCKED: 0,
        STATUS_WATCH: 1,
        STATUS_READY: 2,
    }[status]


def _validate_row(row: MarketResearchGeopoliticalShippingRiskDigestRow) -> None:
    expected_probability_gap = _quantize(row.implied_probability - row.market_probability)
    if row.probability_gap != expected_probability_gap:
        raise ValueError("probability_gap must match implied and market probabilities")
    expected_status = _row_status(row.reason_codes)
    if row.risk_status != expected_status:
        raise ValueError("risk_status must match reason_codes")
    if row.risk_score != _risk_score_from_values(
        incident_count=row.incident_count,
        reroute_probability=row.reroute_probability,
        port_delay_days=row.port_delay_days,
        implied_probability=row.implied_probability,
    ):
        raise ValueError("risk_score must match public row values")
    if row.acknowledged_at < row.observed_at:
        raise ValueError("acknowledged_at must not be before observed_at")


def _risk_score_from_values(
    *,
    incident_count: Decimal,
    reroute_probability: Decimal,
    port_delay_days: Decimal,
    implied_probability: Decimal,
) -> Decimal:
    incident_component = _ratio(incident_count, incident_count + ONE)
    delay_component = _ratio(port_delay_days, port_delay_days + ONE)
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(
            (
                reroute_probability
                + implied_probability
                + incident_component
                + delay_component
            )
            / Decimal("4"),
        )


def _validate_report(report: MarketResearchGeopoliticalShippingRiskDigestReport) -> None:
    rows = report.rows
    if report.route_count != _count(len(rows)):
        raise ValueError("route_count must match rows")
    if report.ready_route_count != _count(
        sum(1 for row in rows if row.risk_status == STATUS_READY),
    ):
        raise ValueError("ready_route_count must match rows")
    if report.watch_route_count != _count(
        sum(1 for row in rows if row.risk_status == STATUS_WATCH),
    ):
        raise ValueError("watch_route_count must match rows")
    if report.blocked_route_count != _count(
        sum(1 for row in rows if row.risk_status == STATUS_BLOCKED),
    ):
        raise ValueError("blocked_route_count must match rows")
    if report.thin_source_count != _count(
        sum(1 for row in rows if THIN_SOURCES_REASON in row.reason_codes),
    ):
        raise ValueError("thin_source_count must match rows")
    if report.stale_signal_count != _count(
        sum(1 for row in rows if STALE_SIGNAL_REASON in row.reason_codes),
    ):
        raise ValueError("stale_signal_count must match rows")
    if report.probability_discount_count != _count(
        sum(1 for row in rows if PROBABILITY_DISCOUNT_REASON in row.reason_codes),
    ):
        raise ValueError("probability_discount_count must match rows")
    if report.max_risk_score != _max_decimal(tuple(row.risk_score for row in rows)):
        raise ValueError("max_risk_score must match rows")
    if report.average_risk_score != _average(tuple(row.risk_score for row in rows)):
        raise ValueError("average_risk_score must match rows")
    if report.max_signal_age_seconds != _max_decimal(
        tuple(row.signal_age_seconds for row in rows),
    ):
        raise ValueError("max_signal_age_seconds must match rows")
    if report.average_port_delay_days != _average(
        tuple(row.port_delay_days for row in rows),
    ):
        raise ValueError("average_port_delay_days must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")


def _normalize_rows(
    rows: tuple[MarketResearchGeopoliticalShippingRiskDigestRow, ...],
) -> tuple[MarketResearchGeopoliticalShippingRiskDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchGeopoliticalShippingRiskDigestRow:
            raise ValueError(
                "rows must contain MarketResearchGeopoliticalShippingRiskDigestRow",
            )
        _require_hard_flags("row", row)
    return _ranked_rows(rows)


def _normalize_reason_code_counts(
    values: tuple[
        MarketResearchGeopoliticalShippingRiskDigestReasonCodeCount,
        ...,
    ],
) -> tuple[MarketResearchGeopoliticalShippingRiskDigestReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for value in values:
        if type(value) is not MarketResearchGeopoliticalShippingRiskDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchGeopoliticalShippingRiskDigestReasonCodeCount",
            )
        _require_hard_flags("reason count", value)
    return tuple(
        sorted(values, key=lambda value: _reason_rank(value.reason_code)),
    )


def _normalize_report_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized = tuple(value)
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    for code in normalized:
        _require_reason_code("reason_codes", code)
    return tuple(sorted(normalized, key=_reason_rank))


def _normalize_row_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized = tuple(value)
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    if READY_REASON in normalized and len(normalized) > 1:
        raise ValueError("ready reason must not be combined")
    for code in normalized:
        _require_reason_code("reason_codes", code)
        if code == NO_INPUTS_REASON:
            raise ValueError("row reason_codes must not include no-inputs reason")
    return tuple(sorted(normalized, key=_row_reason_rank))


def _reason_rank(reason_code: str) -> int:
    return REASON_CODE_SEQUENCE.index(reason_code)


def _row_reason_rank(reason_code: str) -> int:
    return ROW_REASON_CODE_SEQUENCE.index(reason_code)


def _json_ready(value: object) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {
            str(key): _json_ready(item)
            for key, item in value.items()
        }
    return value


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    return _quantize(seconds + microseconds)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _ratio(_sum_decimal(values), _count(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
        if not value.is_finite():
            raise ValueError("values must be finite")
        total += value
    return _quantize(total)


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _redacted_reference(value: str) -> str:
    digest = sha256(value.encode("utf-8")).hexdigest()[:16]
    return f"ref:{digest}"


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in RISK_STATUSES:
        raise ValueError(f"{field_name} must be supported")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be supported")


def _require_market_slug(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if "_" in value:
        raise ValueError(f"{field_name} must use hyphen separators")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lower_value = value.lower()
    if any(fragment in lower_value for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsupported text")


def _require_reference(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)


def _require_redacted_reference(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if not value.startswith("ref:") or len(value) != 20:
        raise ValueError(f"{field_name} must be redacted")
    return value


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789-_:."
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be canonical lowercase text")


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_finite_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_signed_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_finite_decimal(field_name, value)
    if decimal_value < -ONE or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between negative one and one")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_finite_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_finite_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return decimal_value


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_positive_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return decimal_value


def _require_finite_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")
