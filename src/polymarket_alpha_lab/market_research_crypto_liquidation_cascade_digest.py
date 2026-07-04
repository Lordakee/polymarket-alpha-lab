from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal


DEFAULT_MARKET_RESEARCH_CRYPTO_LIQUIDATION_CASCADE_DIGEST_CONFIG_VERSION = (
    "market-research-crypto-liquidation-cascade-digest-v0"
)

DIGEST_STATUSES = ("pass", "blocked")
SEVERITIES = ("severe", "elevated", "normal")
REASON_CODES = (
    "crypto_liquidation_cascade_digest_passed",
    "crypto_liquidation_cascade_digest_empty",
    "crypto_liquidation_cascade_severe_notional",
    "crypto_liquidation_cascade_severe_price_move",
    "crypto_liquidation_cascade_open_interest_flush",
    "crypto_liquidation_cascade_elevated_notional",
    "crypto_liquidation_cascade_elevated_price_move",
)
NEXT_STEP = "review_crypto_liquidation_cascade_risk"
RATIO_QUANT = Decimal("0.000001")
ZERO = Decimal("0")

__all__ = (
    "DEFAULT_MARKET_RESEARCH_CRYPTO_LIQUIDATION_CASCADE_DIGEST_CONFIG_VERSION",
    "MarketResearchCryptoLiquidationCascadeDigestConfig",
    "MarketResearchCryptoLiquidationCascadeDigestReport",
    "MarketResearchCryptoLiquidationCascadeEvent",
    "MarketResearchCryptoLiquidationCascadeSeverity",
    "build_market_research_crypto_liquidation_cascade_digest",
)


@dataclass(frozen=True)
class MarketResearchCryptoLiquidationCascadeDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_CRYPTO_LIQUIDATION_CASCADE_DIGEST_CONFIG_VERSION
    )
    severe_liquidation_notional_usd: Decimal = Decimal("100000000")
    elevated_liquidation_notional_usd: Decimal = Decimal("25000000")
    severe_price_move_ratio: Decimal = Decimal("0.050000")
    elevated_price_move_ratio: Decimal = Decimal("0.020000")
    open_interest_drop_usd: Decimal = Decimal("50000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "severe_liquidation_notional_usd",
            "elevated_liquidation_notional_usd",
            "severe_price_move_ratio",
            "elevated_price_move_ratio",
            "open_interest_drop_usd",
        ):
            _require_positive_decimal(field_name, getattr(self, field_name))
        if self.elevated_liquidation_notional_usd > self.severe_liquidation_notional_usd:
            raise ValueError("elevated_liquidation_notional_usd must not exceed severe threshold")
        if self.elevated_price_move_ratio > self.severe_price_move_ratio:
            raise ValueError("elevated_price_move_ratio must not exceed severe threshold")
        _require_hard_flags("MarketResearchCryptoLiquidationCascadeDigestConfig", self)


@dataclass(frozen=True)
class MarketResearchCryptoLiquidationCascadeEvent:
    venue: str
    asset_symbol: str
    observed_at: datetime
    long_liquidation_usd: Decimal
    short_liquidation_usd: Decimal
    open_interest_change_usd: Decimal
    price_change_ratio: Decimal
    liquidation_notional_usd: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("venue", self.venue)
        _require_canonical_string("asset_symbol", self.asset_symbol)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "long_liquidation_usd",
            "short_liquidation_usd",
            "liquidation_notional_usd",
        ):
            _require_nonnegative_decimal(field_name, getattr(self, field_name))
        _require_decimal("open_interest_change_usd", self.open_interest_change_usd)
        _require_decimal("price_change_ratio", self.price_change_ratio)
        if self.long_liquidation_usd + self.short_liquidation_usd != self.liquidation_notional_usd:
            raise ValueError("liquidation_notional_usd must equal long plus short liquidations")
        _require_hard_flags("MarketResearchCryptoLiquidationCascadeEvent", self)


@dataclass(frozen=True)
class MarketResearchCryptoLiquidationCascadeSeverity:
    severity: str
    event_count: Decimal
    liquidation_notional_usd: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_severity("severity", self.severity)
        _require_nonnegative_decimal("event_count", self.event_count)
        _require_nonnegative_decimal(
            "liquidation_notional_usd",
            self.liquidation_notional_usd,
        )
        _require_hard_flags("MarketResearchCryptoLiquidationCascadeSeverity", self)


@dataclass(frozen=True)
class MarketResearchCryptoLiquidationCascadeDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    digest_next_step: str
    event_count: Decimal
    asset_count: Decimal
    venue_count: Decimal
    severe_event_count: Decimal
    elevated_event_count: Decimal
    normal_event_count: Decimal
    total_liquidation_notional_usd: Decimal
    total_long_liquidation_usd: Decimal
    total_short_liquidation_usd: Decimal
    net_long_liquidation_usd: Decimal
    max_liquidation_notional_usd: Decimal
    max_abs_price_change_ratio: Decimal
    long_liquidation_share_ratio: Decimal | None
    severe_event_ratio: Decimal | None
    severity_rows: tuple[MarketResearchCryptoLiquidationCascadeSeverity, ...]
    top_events: tuple[MarketResearchCryptoLiquidationCascadeEvent, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_digest_status("digest_status", self.digest_status)
        _require_canonical_string("digest_next_step", self.digest_next_step)
        for field_name in (
            "event_count",
            "asset_count",
            "venue_count",
            "severe_event_count",
            "elevated_event_count",
            "normal_event_count",
            "total_liquidation_notional_usd",
            "total_long_liquidation_usd",
            "total_short_liquidation_usd",
            "max_liquidation_notional_usd",
            "max_abs_price_change_ratio",
        ):
            _require_nonnegative_decimal(field_name, getattr(self, field_name))
        _require_decimal("net_long_liquidation_usd", self.net_long_liquidation_usd)
        for field_name in ("long_liquidation_share_ratio", "severe_event_ratio"):
            value = getattr(self, field_name)
            if value is not None:
                _require_ratio(field_name, value)
        object.__setattr__(self, "severity_rows", _normalize_severity_rows(self.severity_rows))
        object.__setattr__(self, "top_events", _normalize_top_events(self.top_events))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags("MarketResearchCryptoLiquidationCascadeDigestReport", self)
        _validate_report_consistency(self)


def build_market_research_crypto_liquidation_cascade_digest(
    events: list[MarketResearchCryptoLiquidationCascadeEvent]
    | tuple[MarketResearchCryptoLiquidationCascadeEvent, ...],
    *,
    config: MarketResearchCryptoLiquidationCascadeDigestConfig,
    generated_at: datetime,
) -> MarketResearchCryptoLiquidationCascadeDigestReport:
    if type(config) is not MarketResearchCryptoLiquidationCascadeDigestConfig:
        raise ValueError(
            "config must be a MarketResearchCryptoLiquidationCascadeDigestConfig",
        )
    _require_hard_flags("MarketResearchCryptoLiquidationCascadeDigestConfig", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_events = _normalize_events(events)
    event_severities = tuple(
        _event_severity(event, config) for event in normalized_events
    )
    severe_event_count = _decimal_count(
        severity == "severe" for severity in event_severities
    )
    elevated_event_count = _decimal_count(
        severity == "elevated" for severity in event_severities
    )
    normal_event_count = _decimal_count(
        severity == "normal" for severity in event_severities
    )
    total_liquidation_notional_usd = sum(
        (event.liquidation_notional_usd for event in normalized_events),
        ZERO,
    )
    total_long_liquidation_usd = sum(
        (event.long_liquidation_usd for event in normalized_events),
        ZERO,
    )
    total_short_liquidation_usd = sum(
        (event.short_liquidation_usd for event in normalized_events),
        ZERO,
    )
    reason_codes = _reason_codes(normalized_events, config)

    return MarketResearchCryptoLiquidationCascadeDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=_digest_status(reason_codes),
        digest_next_step=NEXT_STEP,
        event_count=Decimal(len(normalized_events)),
        asset_count=Decimal(len({event.asset_symbol for event in normalized_events})),
        venue_count=Decimal(len({event.venue for event in normalized_events})),
        severe_event_count=severe_event_count,
        elevated_event_count=elevated_event_count,
        normal_event_count=normal_event_count,
        total_liquidation_notional_usd=total_liquidation_notional_usd,
        total_long_liquidation_usd=total_long_liquidation_usd,
        total_short_liquidation_usd=total_short_liquidation_usd,
        net_long_liquidation_usd=total_long_liquidation_usd - total_short_liquidation_usd,
        max_liquidation_notional_usd=max(
            (event.liquidation_notional_usd for event in normalized_events),
            default=ZERO,
        ),
        max_abs_price_change_ratio=max(
            (abs(event.price_change_ratio) for event in normalized_events),
            default=ZERO,
        ).quantize(RATIO_QUANT) if normalized_events else ZERO,
        long_liquidation_share_ratio=_ratio(
            total_long_liquidation_usd,
            total_liquidation_notional_usd,
        ),
        severe_event_ratio=_ratio(severe_event_count, Decimal(len(normalized_events))),
        severity_rows=_severity_rows(normalized_events, event_severities),
        top_events=_top_events(normalized_events),
        reason_codes=reason_codes,
    )


def _normalize_events(
    events: list[MarketResearchCryptoLiquidationCascadeEvent]
    | tuple[MarketResearchCryptoLiquidationCascadeEvent, ...],
) -> tuple[MarketResearchCryptoLiquidationCascadeEvent, ...]:
    if type(events) not in (list, tuple):
        raise ValueError("events must be a list or tuple")
    normalized = tuple(events)
    for event in normalized:
        if type(event) is not MarketResearchCryptoLiquidationCascadeEvent:
            raise ValueError(
                "events must contain MarketResearchCryptoLiquidationCascadeEvent values",
            )
        _require_hard_flags("MarketResearchCryptoLiquidationCascadeEvent", event)
    return normalized


def _event_severity(
    event: MarketResearchCryptoLiquidationCascadeEvent,
    config: MarketResearchCryptoLiquidationCascadeDigestConfig,
) -> str:
    if (
        event.liquidation_notional_usd >= config.severe_liquidation_notional_usd
        or abs(event.price_change_ratio) >= config.severe_price_move_ratio
        or event.open_interest_change_usd <= -config.open_interest_drop_usd
    ):
        return "severe"
    if (
        event.liquidation_notional_usd >= config.elevated_liquidation_notional_usd
        or abs(event.price_change_ratio) >= config.elevated_price_move_ratio
    ):
        return "elevated"
    return "normal"


def _reason_codes(
    events: tuple[MarketResearchCryptoLiquidationCascadeEvent, ...],
    config: MarketResearchCryptoLiquidationCascadeDigestConfig,
) -> tuple[str, ...]:
    if not events:
        return ("crypto_liquidation_cascade_digest_empty",)
    codes: list[str] = []
    if any(event.liquidation_notional_usd >= config.severe_liquidation_notional_usd for event in events):
        codes.append("crypto_liquidation_cascade_severe_notional")
    if any(abs(event.price_change_ratio) >= config.severe_price_move_ratio for event in events):
        codes.append("crypto_liquidation_cascade_severe_price_move")
    if any(event.open_interest_change_usd <= -config.open_interest_drop_usd for event in events):
        codes.append("crypto_liquidation_cascade_open_interest_flush")
    if not codes and any(event.liquidation_notional_usd >= config.elevated_liquidation_notional_usd for event in events):
        codes.append("crypto_liquidation_cascade_elevated_notional")
    if not codes and any(abs(event.price_change_ratio) >= config.elevated_price_move_ratio for event in events):
        codes.append("crypto_liquidation_cascade_elevated_price_move")
    if not codes:
        return ("crypto_liquidation_cascade_digest_passed",)
    return tuple(codes)


def _digest_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("crypto_liquidation_cascade_digest_passed",):
        return "pass"
    return "blocked"


def _severity_rows(
    events: tuple[MarketResearchCryptoLiquidationCascadeEvent, ...],
    event_severities: tuple[str, ...],
) -> tuple[MarketResearchCryptoLiquidationCascadeSeverity, ...]:
    rows: list[MarketResearchCryptoLiquidationCascadeSeverity] = []
    for severity in SEVERITIES:
        matching_events = tuple(
            event
            for event, event_severity in zip(events, event_severities, strict=True)
            if event_severity == severity
        )
        if not matching_events:
            continue
        rows.append(
            MarketResearchCryptoLiquidationCascadeSeverity(
                severity=severity,
                event_count=Decimal(len(matching_events)),
                liquidation_notional_usd=sum(
                    (event.liquidation_notional_usd for event in matching_events),
                    ZERO,
                ),
            ),
        )
    return tuple(rows)


def _top_events(
    events: tuple[MarketResearchCryptoLiquidationCascadeEvent, ...],
) -> tuple[MarketResearchCryptoLiquidationCascadeEvent, ...]:
    return tuple(
        sorted(
            events,
            key=lambda event: (
                -event.liquidation_notional_usd,
                event.asset_symbol,
                event.venue,
                event.observed_at,
            ),
        ),
    )


def _decimal_count(values: object) -> Decimal:
    return Decimal(sum(1 for value in values if value))


def _ratio(value: Decimal, total: Decimal) -> Decimal | None:
    if total == ZERO:
        return None
    return (value / total).quantize(RATIO_QUANT)


def _validate_report_consistency(
    report: MarketResearchCryptoLiquidationCascadeDigestReport,
) -> None:
    if (
        report.severe_event_count
        + report.elevated_event_count
        + report.normal_event_count
        != report.event_count
    ):
        raise ValueError("event counts must reconcile")
    if report.digest_status != _digest_status(report.reason_codes):
        raise ValueError("digest_status must match reason_codes")
    if report.digest_next_step != NEXT_STEP:
        raise ValueError("digest_next_step must match digest reducer")
    if report.total_long_liquidation_usd + report.total_short_liquidation_usd != report.total_liquidation_notional_usd:
        raise ValueError("total liquidation amounts must reconcile")
    if sum((row.event_count for row in report.severity_rows), ZERO) != report.event_count:
        raise ValueError("severity_rows event_count must match event_count")
    if sum((row.liquidation_notional_usd for row in report.severity_rows), ZERO) != report.total_liquidation_notional_usd:
        raise ValueError("severity_rows liquidation_notional_usd must match total")
    if report.event_count == ZERO and report.top_events:
        raise ValueError("empty event_count requires no top_events")
    if report.reason_codes == ("crypto_liquidation_cascade_digest_empty",) and report.event_count != ZERO:
        raise ValueError("empty reason requires zero events")
    if report.reason_codes == ("crypto_liquidation_cascade_digest_passed",) and report.event_count == ZERO:
        raise ValueError("passed reason requires events")


def _normalize_severity_rows(
    rows: tuple[MarketResearchCryptoLiquidationCascadeSeverity, ...],
) -> tuple[MarketResearchCryptoLiquidationCascadeSeverity, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("severity_rows must be a list or tuple")
    normalized = tuple(rows)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not MarketResearchCryptoLiquidationCascadeSeverity:
            raise ValueError(
                "severity_rows must contain MarketResearchCryptoLiquidationCascadeSeverity values",
            )
        _require_hard_flags("MarketResearchCryptoLiquidationCascadeSeverity", row)
        if row.severity in seen:
            raise ValueError("severity_rows severity values must be unique")
        seen.add(row.severity)
    if tuple(row.severity for row in normalized) != tuple(
        severity for severity in SEVERITIES if severity in seen
    ):
        raise ValueError("severity_rows must use canonical severity sequence")
    return normalized


def _normalize_top_events(
    events: tuple[MarketResearchCryptoLiquidationCascadeEvent, ...],
) -> tuple[MarketResearchCryptoLiquidationCascadeEvent, ...]:
    if type(events) not in (list, tuple):
        raise ValueError("top_events must be a list or tuple")
    normalized = tuple(events)
    for event in normalized:
        if type(event) is not MarketResearchCryptoLiquidationCascadeEvent:
            raise ValueError(
                "top_events must contain MarketResearchCryptoLiquidationCascadeEvent values",
            )
        _require_hard_flags("MarketResearchCryptoLiquidationCascadeEvent", event)
    if normalized != _top_events(normalized):
        raise ValueError("top_events must use deterministic event sequence")
    return normalized


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    normalized = tuple(reason_codes)
    if not normalized:
        raise ValueError("reason_codes must contain at least one value")
    for reason_code in normalized:
        _require_reason_code("reason_codes", reason_code)
    if normalized != tuple(reason_code for reason_code in REASON_CODES if reason_code in normalized):
        raise ValueError("reason_codes must use canonical reason code sequence")
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_digest_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be pass or blocked")


def _require_severity(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in SEVERITIES:
        raise ValueError(f"{field_name} must contain known severities")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODES:
        raise ValueError(f"{field_name} must contain known reason codes")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_positive_decimal(field_name: str, value: object) -> None:
    _require_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")


def _require_nonnegative_decimal(field_name: str, value: object) -> None:
    _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_ratio(field_name: str, value: object) -> None:
    _require_nonnegative_decimal(field_name, value)
    if value > Decimal("1"):
        raise ValueError(f"{field_name} must be at most one")


def _require_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")
