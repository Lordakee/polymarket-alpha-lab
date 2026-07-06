"""Pure Phase 1 equity single-stock gap risk digest reducer."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_MARKET_RESEARCH_EQUITY_SINGLE_STOCK_GAP_RISK_DIGEST_CONFIG_VERSION = (
    "market-research-equity-single-stock-gap-risk-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)
GAP_DIRECTIONS = ("gap_up", "gap_down", "flat")

REASON_PREFIX = "market_research_equity_single_stock_gap_risk_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
READY_REASON = f"{REASON_PREFIX}ready"
MATERIAL_GAP_REASON = f"{REASON_PREFIX}material_gap"
HIGH_EVENT_SENSITIVITY_REASON = f"{REASON_PREFIX}high_event_sensitivity"
THIN_SOURCES_REASON = f"{REASON_PREFIX}thin_sources"
MISSING_CONFIRMATION_REASON = f"{REASON_PREFIX}missing_confirmation"
MISSING_ACKNOWLEDGEMENT_REASON = f"{REASON_PREFIX}missing_acknowledgement"
SLOW_ACKNOWLEDGEMENT_REASON = f"{REASON_PREFIX}slow_acknowledgement"
STALE_SOURCE_REASON = f"{REASON_PREFIX}stale_source"
CONTRADICTION_PRESENT_REASON = f"{REASON_PREFIX}contradiction_present"

ROW_REASON_CODE_SEQUENCE = (
    MATERIAL_GAP_REASON,
    HIGH_EVENT_SENSITIVITY_REASON,
    THIN_SOURCES_REASON,
    MISSING_CONFIRMATION_REASON,
    MISSING_ACKNOWLEDGEMENT_REASON,
    SLOW_ACKNOWLEDGEMENT_REASON,
    STALE_SOURCE_REASON,
    CONTRADICTION_PRESENT_REASON,
    READY_REASON,
)
REPORT_REASON_CODE_SEQUENCE = (
    MATERIAL_GAP_REASON,
    HIGH_EVENT_SENSITIVITY_REASON,
    THIN_SOURCES_REASON,
    MISSING_CONFIRMATION_REASON,
    MISSING_ACKNOWLEDGEMENT_REASON,
    SLOW_ACKNOWLEDGEMENT_REASON,
    STALE_SOURCE_REASON,
    CONTRADICTION_PRESENT_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
BLOCKING_REASON_CODES = (
    MISSING_CONFIRMATION_REASON,
    MISSING_ACKNOWLEDGEMENT_REASON,
    STALE_SOURCE_REASON,
    CONTRADICTION_PRESENT_REASON,
)

NEXT_STEPS = {
    STATUS_READY: "allow_report_only_market_research_equity_single_stock_gap_risk_digest",
    STATUS_WATCH: "watch_report_only_market_research_equity_single_stock_gap_risk_digest",
    STATUS_BLOCKED: "block_report_only_market_research_equity_single_stock_gap_risk_digest",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
SECONDS_PER_DAY = 86400


__all__ = (
    "DEFAULT_MARKET_RESEARCH_EQUITY_SINGLE_STOCK_GAP_RISK_DIGEST_CONFIG_VERSION",
    "MarketResearchEquitySingleStockGapRiskDigestConfig",
    "MarketResearchEquitySingleStockGapRiskObservation",
    "MarketResearchEquitySingleStockGapRiskReasonCodeCount",
    "MarketResearchEquitySingleStockGapRiskReport",
    "MarketResearchEquitySingleStockGapRiskRow",
    "build_market_research_equity_single_stock_gap_risk_digest",
    "market_research_equity_single_stock_gap_risk_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchEquitySingleStockGapRiskDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_EQUITY_SINGLE_STOCK_GAP_RISK_DIGEST_CONFIG_VERSION
    )
    max_source_age_seconds: Decimal = Decimal("7200.000000")
    min_source_count: Decimal = Decimal("2.000000")
    min_confirmation_count: Decimal = Decimal("1.000000")
    material_gap_pct: Decimal = Decimal("0.050000")
    min_event_sensitivity_score: Decimal = Decimal("0.650000")
    max_acknowledgement_lag_seconds: Decimal = Decimal("900.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEquitySingleStockGapRiskDigestConfig:
            raise TypeError(
                "MarketResearchEquitySingleStockGapRiskDigestConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            MarketResearchEquitySingleStockGapRiskDigestConfig,
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_EQUITY_SINGLE_STOCK_GAP_RISK_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "max_source_age_seconds",
            "max_acknowledgement_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("min_source_count", "min_confirmation_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("material_gap_pct", "min_event_sensitivity_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
            if getattr(self, field_name) <= ZERO:
                raise ValueError(f"{field_name} must be positive")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchEquitySingleStockGapRiskObservation:
    research_key: str
    condition_id: str
    equity_symbol: str
    gap_event_id: str
    observed_at: datetime
    acknowledged_at: datetime | None
    source_count: Decimal
    confirmation_count: Decimal
    gap_pct: Decimal
    intraday_volatility_pct: Decimal
    event_sensitivity_score: Decimal
    contradiction_count: Decimal
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEquitySingleStockGapRiskObservation:
            raise TypeError(
                "MarketResearchEquitySingleStockGapRiskObservation does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "observation",
            self,
            MarketResearchEquitySingleStockGapRiskObservation,
        )
        for field_name in (
            "research_key",
            "condition_id",
            "gap_event_id",
            "source_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_equity_symbol("equity_symbol", self.equity_symbol)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_optional_utc("acknowledged_at", self.acknowledged_at),
        )
        for field_name in ("source_count", "confirmation_count", "contradiction_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "gap_pct", _require_signed_ratio_decimal("gap_pct", self.gap_pct))
        for field_name in ("intraday_volatility_pct", "event_sensitivity_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class MarketResearchEquitySingleStockGapRiskRow:
    research_key: str
    condition_id: str
    equity_symbol: str
    gap_event_id: str
    digest_status: str
    gap_direction: str
    observed_at: datetime
    acknowledged_at: datetime | None
    source_age_seconds: Decimal
    acknowledgement_lag_seconds: Decimal | None
    source_count: Decimal
    confirmation_count: Decimal
    gap_pct: Decimal
    gap_abs_pct: Decimal
    intraday_volatility_pct: Decimal
    event_sensitivity_score: Decimal
    contradiction_count: Decimal
    source_config_version: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEquitySingleStockGapRiskRow:
            raise TypeError(
                "MarketResearchEquitySingleStockGapRiskRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, MarketResearchEquitySingleStockGapRiskRow)
        for field_name in (
            "research_key",
            "condition_id",
            "gap_event_id",
            "source_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_equity_symbol("equity_symbol", self.equity_symbol)
        _require_status("digest_status", self.digest_status)
        _require_member("gap_direction", self.gap_direction, GAP_DIRECTIONS)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_optional_utc("acknowledged_at", self.acknowledged_at),
        )
        object.__setattr__(
            self,
            "source_age_seconds",
            _require_nonnegative_decimal("source_age_seconds", self.source_age_seconds),
        )
        object.__setattr__(
            self,
            "acknowledgement_lag_seconds",
            _require_optional_nonnegative_decimal(
                "acknowledgement_lag_seconds",
                self.acknowledgement_lag_seconds,
            ),
        )
        for field_name in ("source_count", "confirmation_count", "contradiction_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "gap_pct", _require_signed_ratio_decimal("gap_pct", self.gap_pct))
        for field_name in (
            "gap_abs_pct",
            "intraday_volatility_pct",
            "event_sensitivity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                ROW_REASON_CODE_SEQUENCE,
            ),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchEquitySingleStockGapRiskReasonCodeCount:
    reason_code: str
    count: Decimal
    event_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEquitySingleStockGapRiskReasonCodeCount:
            raise TypeError(
                "MarketResearchEquitySingleStockGapRiskReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "reason code count",
            self,
            MarketResearchEquitySingleStockGapRiskReasonCodeCount,
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "event_ratio",
            _require_ratio_decimal("event_ratio", self.event_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchEquitySingleStockGapRiskReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    event_count: Decimal
    ready_event_count: Decimal
    watch_event_count: Decimal
    blocked_event_count: Decimal
    material_gap_count: Decimal
    high_event_sensitivity_count: Decimal
    thin_source_count: Decimal
    missing_confirmation_count: Decimal
    missing_acknowledgement_count: Decimal
    slow_acknowledgement_count: Decimal
    stale_source_count: Decimal
    contradiction_event_count: Decimal
    average_gap_abs_pct: Decimal
    max_gap_abs_pct: Decimal
    average_event_sensitivity_score: Decimal
    max_source_age_seconds: Decimal
    rows: tuple[MarketResearchEquitySingleStockGapRiskRow, ...]
    reason_code_counts: tuple[MarketResearchEquitySingleStockGapRiskReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchEquitySingleStockGapRiskReport:
            raise TypeError(
                "MarketResearchEquitySingleStockGapRiskReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, MarketResearchEquitySingleStockGapRiskReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_EQUITY_SINGLE_STOCK_GAP_RISK_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        _require_status("digest_status", self.digest_status)
        _require_public_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "event_count",
            "ready_event_count",
            "watch_event_count",
            "blocked_event_count",
            "material_gap_count",
            "high_event_sensitivity_count",
            "thin_source_count",
            "missing_confirmation_count",
            "missing_acknowledgement_count",
            "slow_acknowledgement_count",
            "stale_source_count",
            "contradiction_event_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_source_age_seconds",
            _require_nonnegative_decimal(
                "max_source_age_seconds",
                self.max_source_age_seconds,
            ),
        )
        for field_name in (
            "average_gap_abs_pct",
            "max_gap_abs_pct",
            "average_event_sensitivity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
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
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODE_SEQUENCE,
            ),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


_PUBLIC_DATACLASS_TYPES = (
    MarketResearchEquitySingleStockGapRiskDigestConfig,
    MarketResearchEquitySingleStockGapRiskObservation,
    MarketResearchEquitySingleStockGapRiskRow,
    MarketResearchEquitySingleStockGapRiskReasonCodeCount,
    MarketResearchEquitySingleStockGapRiskReport,
)


def build_market_research_equity_single_stock_gap_risk_digest(
    observations: tuple[MarketResearchEquitySingleStockGapRiskObservation, ...],
    *,
    config: MarketResearchEquitySingleStockGapRiskDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchEquitySingleStockGapRiskReport:
    cfg = config or MarketResearchEquitySingleStockGapRiskDigestConfig()
    if type(cfg) is not MarketResearchEquitySingleStockGapRiskDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchEquitySingleStockGapRiskDigestConfig",
        )
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations, generated_at_utc)
    rows = tuple(
        _row_for_observation(
            observation,
            config=cfg,
            generated_at=generated_at_utc,
        )
        for observation in normalized_observations
    )
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    event_count = _count(len(sorted_rows))
    reason_codes = _report_reason_codes(sorted_rows)
    digest_status = _report_status(sorted_rows)

    return MarketResearchEquitySingleStockGapRiskReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        event_count=event_count,
        ready_event_count=_status_count(sorted_rows, STATUS_READY),
        watch_event_count=_status_count(sorted_rows, STATUS_WATCH),
        blocked_event_count=_status_count(sorted_rows, STATUS_BLOCKED),
        material_gap_count=_reason_event_count(sorted_rows, MATERIAL_GAP_REASON),
        high_event_sensitivity_count=_reason_event_count(
            sorted_rows,
            HIGH_EVENT_SENSITIVITY_REASON,
        ),
        thin_source_count=_reason_event_count(sorted_rows, THIN_SOURCES_REASON),
        missing_confirmation_count=_reason_event_count(
            sorted_rows,
            MISSING_CONFIRMATION_REASON,
        ),
        missing_acknowledgement_count=_reason_event_count(
            sorted_rows,
            MISSING_ACKNOWLEDGEMENT_REASON,
        ),
        slow_acknowledgement_count=_reason_event_count(
            sorted_rows,
            SLOW_ACKNOWLEDGEMENT_REASON,
        ),
        stale_source_count=_reason_event_count(sorted_rows, STALE_SOURCE_REASON),
        contradiction_event_count=_reason_event_count(
            sorted_rows,
            CONTRADICTION_PRESENT_REASON,
        ),
        average_gap_abs_pct=_ratio(
            _decimal_sum(row.gap_abs_pct for row in sorted_rows),
            event_count,
        ),
        max_gap_abs_pct=max((row.gap_abs_pct for row in sorted_rows), default=ZERO),
        average_event_sensitivity_score=_ratio(
            _decimal_sum(row.event_sensitivity_score for row in sorted_rows),
            event_count,
        ),
        max_source_age_seconds=max(
            (row.source_age_seconds for row in sorted_rows),
            default=ZERO,
        ),
        rows=sorted_rows,
        reason_code_counts=_reason_code_counts(sorted_rows, reason_codes, event_count),
        reason_codes=reason_codes,
    )


def market_research_equity_single_stock_gap_risk_digest_payload(
    report: MarketResearchEquitySingleStockGapRiskReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchEquitySingleStockGapRiskReport:
        raise ValueError(
            "report must be exactly MarketResearchEquitySingleStockGapRiskReport",
        )
    _revalidate_public_dataclass(report)
    public_value = _payload_value(report)
    if type(public_value) is not dict:
        raise ValueError("payload must be a mapping")
    return public_value


def _normalize_observations(
    observations: object,
    generated_at: datetime,
) -> tuple[MarketResearchEquitySingleStockGapRiskObservation, ...]:
    if type(observations) is not tuple:
        raise ValueError("observations must be a tuple")
    seen: set[tuple[str, str, str]] = set()
    for observation in observations:
        if type(observation) is not MarketResearchEquitySingleStockGapRiskObservation:
            raise ValueError(
                "observations must contain "
                "MarketResearchEquitySingleStockGapRiskObservation",
            )
        _revalidate_public_dataclass(observation)
        key = (observation.research_key, observation.condition_id, observation.gap_event_id)
        if key in seen:
            raise ValueError("observations must use unique research condition event ids")
        seen.add(key)
        if observation.observed_at > generated_at:
            raise ValueError("observed_at cannot be after generated_at")
        if observation.acknowledged_at is not None:
            if observation.acknowledged_at > generated_at:
                raise ValueError("acknowledged_at cannot be after generated_at")
            if observation.acknowledged_at < observation.observed_at:
                raise ValueError("acknowledged_at cannot be before observed_at")
    return tuple(
        sorted(
            observations,
            key=lambda observation: (
                observation.research_key,
                observation.condition_id,
                observation.gap_event_id,
            ),
        ),
    )


def _row_for_observation(
    observation: MarketResearchEquitySingleStockGapRiskObservation,
    *,
    config: MarketResearchEquitySingleStockGapRiskDigestConfig,
    generated_at: datetime,
) -> MarketResearchEquitySingleStockGapRiskRow:
    source_age_seconds = _seconds_between(observation.observed_at, generated_at)
    acknowledgement_lag_seconds = (
        None
        if observation.acknowledged_at is None
        else _seconds_between(observation.observed_at, observation.acknowledged_at)
    )
    gap_abs_pct = _decimal_abs(observation.gap_pct)
    reason_codes = _row_reason_codes(
        source_age_seconds=source_age_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        source_count=observation.source_count,
        confirmation_count=observation.confirmation_count,
        gap_abs_pct=gap_abs_pct,
        event_sensitivity_score=observation.event_sensitivity_score,
        contradiction_count=observation.contradiction_count,
        config=config,
    )
    return MarketResearchEquitySingleStockGapRiskRow(
        research_key=observation.research_key,
        condition_id=observation.condition_id,
        equity_symbol=observation.equity_symbol,
        gap_event_id=observation.gap_event_id,
        digest_status=_row_status(reason_codes),
        gap_direction=_gap_direction(observation.gap_pct),
        observed_at=observation.observed_at,
        acknowledged_at=observation.acknowledged_at,
        source_age_seconds=source_age_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        source_count=observation.source_count,
        confirmation_count=observation.confirmation_count,
        gap_pct=observation.gap_pct,
        gap_abs_pct=gap_abs_pct,
        intraday_volatility_pct=observation.intraday_volatility_pct,
        event_sensitivity_score=observation.event_sensitivity_score,
        contradiction_count=observation.contradiction_count,
        source_config_version=observation.source_config_version,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    source_age_seconds: Decimal,
    acknowledgement_lag_seconds: Decimal | None,
    source_count: Decimal,
    confirmation_count: Decimal,
    gap_abs_pct: Decimal,
    event_sensitivity_score: Decimal,
    contradiction_count: Decimal,
    config: MarketResearchEquitySingleStockGapRiskDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if gap_abs_pct >= config.material_gap_pct:
        reasons.append(MATERIAL_GAP_REASON)
    if event_sensitivity_score >= config.min_event_sensitivity_score:
        reasons.append(HIGH_EVENT_SENSITIVITY_REASON)
    if source_count < config.min_source_count:
        reasons.append(THIN_SOURCES_REASON)
    if confirmation_count < config.min_confirmation_count:
        reasons.append(MISSING_CONFIRMATION_REASON)
    if acknowledgement_lag_seconds is None:
        reasons.append(MISSING_ACKNOWLEDGEMENT_REASON)
    elif acknowledgement_lag_seconds > config.max_acknowledgement_lag_seconds:
        reasons.append(SLOW_ACKNOWLEDGEMENT_REASON)
    if source_age_seconds > config.max_source_age_seconds:
        reasons.append(STALE_SOURCE_REASON)
    if contradiction_count > ZERO:
        reasons.append(CONTRADICTION_PRESENT_REASON)
    if not reasons:
        return (READY_REASON,)
    return tuple(reason for reason in ROW_REASON_CODE_SEQUENCE if reason in reasons)


def _gap_direction(gap_pct: Decimal) -> str:
    if gap_pct > ZERO:
        return "gap_up"
    if gap_pct < ZERO:
        return "gap_down"
    return "flat"


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    if any(reason_code in reason_codes for reason_code in BLOCKING_REASON_CODES):
        return STATUS_BLOCKED
    return STATUS_WATCH


def _report_status(rows: tuple[MarketResearchEquitySingleStockGapRiskRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_READY


def _report_reason_codes(
    rows: tuple[MarketResearchEquitySingleStockGapRiskRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    observed = {reason_code for row in rows for reason_code in row.reason_codes}
    non_ready = observed - {READY_REASON}
    if non_ready:
        return tuple(
            reason_code
            for reason_code in REPORT_REASON_CODE_SEQUENCE
            if reason_code in non_ready
        )
    return (READY_REASON,)


def _reason_code_counts(
    rows: tuple[MarketResearchEquitySingleStockGapRiskRow, ...],
    reason_codes: tuple[str, ...],
    event_count: Decimal,
) -> tuple[MarketResearchEquitySingleStockGapRiskReasonCodeCount, ...]:
    if reason_codes == (NO_INPUTS_REASON,):
        return (
            MarketResearchEquitySingleStockGapRiskReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                event_ratio=ZERO,
            ),
        )
    included_reason_codes = set(reason_codes)
    counts = Counter(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code in included_reason_codes
    )
    return tuple(
        MarketResearchEquitySingleStockGapRiskReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
            event_ratio=_ratio(_count(count), event_count),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], REPORT_REASON_CODE_SEQUENCE.index(item[0])),
        )
    )


def _status_count(
    rows: tuple[MarketResearchEquitySingleStockGapRiskRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.digest_status == status))


def _reason_event_count(
    rows: tuple[MarketResearchEquitySingleStockGapRiskRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _row_sort_key(
    row: MarketResearchEquitySingleStockGapRiskRow,
) -> tuple[int, Decimal, Decimal, str, str, str, str]:
    return (
        {STATUS_BLOCKED: 0, STATUS_WATCH: 1, STATUS_READY: 2}[row.digest_status],
        -row.gap_abs_pct,
        -row.event_sensitivity_score,
        row.equity_symbol,
        row.gap_event_id,
        row.condition_id,
        row.research_key,
    )


def _normalize_rows(value: object) -> tuple[MarketResearchEquitySingleStockGapRiskRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    seen: set[tuple[str, str, str]] = set()
    for row in value:
        if type(row) is not MarketResearchEquitySingleStockGapRiskRow:
            raise ValueError("rows must contain MarketResearchEquitySingleStockGapRiskRow")
        _revalidate_public_dataclass(row)
        key = (row.research_key, row.condition_id, row.gap_event_id)
        if key in seen:
            raise ValueError("rows must use unique research condition event ids")
        seen.add(key)
    if value != tuple(sorted(value, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    return value


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketResearchEquitySingleStockGapRiskReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    seen: set[str] = set()
    for row in value:
        if type(row) is not MarketResearchEquitySingleStockGapRiskReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchEquitySingleStockGapRiskReasonCodeCount",
            )
        _revalidate_public_dataclass(row)
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(row.reason_code)
    if value != tuple(
        sorted(
            value,
            key=lambda row: (
                -row.count,
                REPORT_REASON_CODE_SEQUENCE.index(row.reason_code),
            ),
        ),
    ):
        raise ValueError("reason_code_counts must use deterministic sequence")
    return value


def _normalize_reason_codes(
    field_name: str,
    value: object,
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must contain at least one value")
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} must not contain duplicates")
    for reason_code in value:
        _require_member(field_name, reason_code, sequence)
    if READY_REASON in value and len(value) != 1:
        raise ValueError(f"{field_name} ready cannot be combined")
    if NO_INPUTS_REASON in value and len(value) != 1:
        raise ValueError(f"{field_name} no_inputs cannot be combined")
    deterministic = tuple(reason_code for reason_code in sequence if reason_code in value)
    if value != deterministic:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return value


def _validate_row(row: MarketResearchEquitySingleStockGapRiskRow) -> None:
    if row.gap_abs_pct != _decimal_abs(row.gap_pct):
        raise ValueError("gap_abs_pct must match gap_pct")
    if row.gap_direction != _gap_direction(row.gap_pct):
        raise ValueError("gap_direction must match gap_pct")
    if row.digest_status != _row_status(row.reason_codes):
        raise ValueError("digest_status must match reason_codes")
    if row.acknowledged_at is None:
        if row.acknowledgement_lag_seconds is not None:
            raise ValueError("acknowledgement_lag_seconds must be absent without acknowledgement")
    else:
        if row.acknowledged_at < row.observed_at:
            raise ValueError("acknowledged_at cannot be before observed_at")
        if row.acknowledgement_lag_seconds != _seconds_between(
            row.observed_at,
            row.acknowledged_at,
        ):
            raise ValueError("acknowledgement_lag_seconds must match timestamps")


def _validate_report(report: MarketResearchEquitySingleStockGapRiskReport) -> None:
    if report.event_count != _count(len(report.rows)):
        raise ValueError("event_count must match rows")
    for status, field_name in (
        (STATUS_READY, "ready_event_count"),
        (STATUS_WATCH, "watch_event_count"),
        (STATUS_BLOCKED, "blocked_event_count"),
    ):
        if getattr(report, field_name) != _status_count(report.rows, status):
            raise ValueError(f"{field_name} must match rows")
    for reason_code, field_name in (
        (MATERIAL_GAP_REASON, "material_gap_count"),
        (HIGH_EVENT_SENSITIVITY_REASON, "high_event_sensitivity_count"),
        (THIN_SOURCES_REASON, "thin_source_count"),
        (MISSING_CONFIRMATION_REASON, "missing_confirmation_count"),
        (MISSING_ACKNOWLEDGEMENT_REASON, "missing_acknowledgement_count"),
        (SLOW_ACKNOWLEDGEMENT_REASON, "slow_acknowledgement_count"),
        (STALE_SOURCE_REASON, "stale_source_count"),
        (CONTRADICTION_PRESENT_REASON, "contradiction_event_count"),
    ):
        if getattr(report, field_name) != _reason_event_count(report.rows, reason_code):
            raise ValueError(f"{field_name} must match rows")
    if report.average_gap_abs_pct != _ratio(
        _decimal_sum(row.gap_abs_pct for row in report.rows),
        report.event_count,
    ):
        raise ValueError("average_gap_abs_pct must match rows")
    if report.max_gap_abs_pct != max((row.gap_abs_pct for row in report.rows), default=ZERO):
        raise ValueError("max_gap_abs_pct must match rows")
    if report.average_event_sensitivity_score != _ratio(
        _decimal_sum(row.event_sensitivity_score for row in report.rows),
        report.event_count,
    ):
        raise ValueError("average_event_sensitivity_score must match rows")
    if report.max_source_age_seconds != max(
        (row.source_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_source_age_seconds must match rows")
    if report.digest_status != _report_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    expected_reason_codes = _report_reason_codes(report.rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(
        report.rows,
        report.reason_codes,
        report.event_count,
    ):
        raise ValueError("reason_code_counts must match rows")


def _revalidate_public_dataclass(value: object) -> None:
    if type(value) not in _PUBLIC_DATACLASS_TYPES:
        raise ValueError("value must be a public equity single-stock gap risk dataclass")
    for field in fields(value):
        _prevalidate_public_value(field.name, getattr(value, field.name))
    type(value)(**{field.name: getattr(value, field.name) for field in fields(value)})


def _prevalidate_public_value(field_name: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _revalidate_public_dataclass(value)
        return
    if type(value) is tuple:
        for item in value:
            _prevalidate_public_value(field_name, item)
        return
    if type(value) is Decimal:
        _require_six_decimal(field_name, value)
        return
    if type(value) is datetime:
        _require_utc_datetime(field_name, value)
        return
    if value is None or type(value) in (str, bool):
        return
    raise ValueError(f"{field_name} contains an unsupported public value")


def _payload_value(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        _revalidate_public_dataclass(value)
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is Decimal:
        _require_six_decimal("decimal", value)
        return format(value, "f")
    if type(value) is datetime:
        _require_utc_datetime("datetime", value)
        return value.isoformat()
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload contains an unsupported value")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_utc_datetime(field_name: str, value: object) -> None:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is not UTC:
        raise ValueError(f"{field_name} must be UTC")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_equity_symbol(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if value.upper() != value:
        raise ValueError(f"{field_name} must be uppercase")
    if not all(character.isalnum() or character in {".", "-"} for character in value):
        raise ValueError(f"{field_name} must be a public equity symbol")


def _require_status(field_name: str, value: object) -> None:
    _require_member(field_name, value, DIGEST_STATUSES)


def _require_reason_code(field_name: str, value: object) -> None:
    _require_member(field_name, value, REPORT_REASON_CODE_SEQUENCE)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of the supported values")


def _require_six_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must use exactly six decimal places")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not use negative zero")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_six_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_six_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer count")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most 1.000000")
    return normalized


def _require_signed_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_six_decimal(field_name, value)
    if normalized < -ONE or normalized > ONE:
        raise ValueError(f"{field_name} must be between -1.000000 and 1.000000")
    return normalized


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = getattr(value, field_name)
        if type(flag) is not bool:
            raise ValueError(f"{label} {field_name} must be a bool")
        if flag is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_exact_type(label: str, value: object, expected_type: type) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _count(value: int) -> Decimal:
    return _six(Decimal(value))


def _decimal_sum(values: object) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _six(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _six(numerator / denominator)


def _decimal_abs(value: Decimal) -> Decimal:
    return _six(abs(value))


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    total_microseconds = (
        ((delta.days * SECONDS_PER_DAY) + delta.seconds) * 1_000_000
    ) + delta.microseconds
    with localcontext(DECIMAL_CONTEXT):
        return _six(Decimal(total_microseconds) / MICROSECONDS_PER_SECOND)


def _six(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)
