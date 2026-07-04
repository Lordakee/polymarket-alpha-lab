"""Pure Phase 1 equity-index dealer gamma digest reducer."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_EQUITY_INDEX_DEALER_GAMMA_DIGEST_CONFIG_VERSION = (
    "market-research-equity-index-dealer-gamma-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
GAMMA_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

PREFIX = "market_research_equity_index_dealer_gamma_digest_"
READY_REASON = f"{PREFIX}ready"
NO_INPUTS_REASON = f"{PREFIX}no_inputs"
MATERIAL_GAMMA_REASON = f"{PREFIX}material_gamma"
SHORT_GAMMA_REASON = f"{PREFIX}short_gamma"
NEAR_ZERO_GAMMA_REASON = f"{PREFIX}near_zero_gamma"
STALE_SURFACE_REASON = f"{PREFIX}stale_surface"
THIN_SOURCES_REASON = f"{PREFIX}thin_sources"
MISSING_ACKNOWLEDGEMENT_REASON = f"{PREFIX}missing_acknowledgement"
SLOW_ACKNOWLEDGEMENT_REASON = f"{PREFIX}slow_acknowledgement"
ELEVATED_SKEW_REASON = f"{PREFIX}elevated_skew"
CONTRADICTION_PRESENT_REASON = f"{PREFIX}contradiction_present"

ROW_REASON_CODE_SEQUENCE = (
    READY_REASON,
    MATERIAL_GAMMA_REASON,
    SHORT_GAMMA_REASON,
    NEAR_ZERO_GAMMA_REASON,
    STALE_SURFACE_REASON,
    THIN_SOURCES_REASON,
    MISSING_ACKNOWLEDGEMENT_REASON,
    SLOW_ACKNOWLEDGEMENT_REASON,
    ELEVATED_SKEW_REASON,
    CONTRADICTION_PRESENT_REASON,
)

REPORT_REASON_CODE_SEQUENCE = (
    MATERIAL_GAMMA_REASON,
    SHORT_GAMMA_REASON,
    NEAR_ZERO_GAMMA_REASON,
    STALE_SURFACE_REASON,
    THIN_SOURCES_REASON,
    MISSING_ACKNOWLEDGEMENT_REASON,
    SLOW_ACKNOWLEDGEMENT_REASON,
    ELEVATED_SKEW_REASON,
    CONTRADICTION_PRESENT_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)

REASON_CODE_SEQUENCE = tuple(
    dict.fromkeys((*ROW_REASON_CODE_SEQUENCE, NO_INPUTS_REASON)),
)

NEXT_STEPS = {
    STATUS_READY: "allow_report_only_market_research_equity_index_dealer_gamma_digest",
    STATUS_WATCH: "watch_report_only_market_research_equity_index_dealer_gamma_digest",
    STATUS_BLOCKED: "block_report_only_market_research_equity_index_dealer_gamma_digest",
}

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANT = Decimal("0.000001")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")


__all__ = (
    "DEFAULT_MARKET_RESEARCH_EQUITY_INDEX_DEALER_GAMMA_DIGEST_CONFIG_VERSION",
    "MarketResearchEquityIndexDealerGammaDigestConfig",
    "MarketResearchEquityIndexDealerGammaInputRow",
    "MarketResearchEquityIndexDealerGammaReasonCodeCount",
    "MarketResearchEquityIndexDealerGammaReport",
    "MarketResearchEquityIndexDealerGammaRow",
    "build_market_research_equity_index_dealer_gamma_digest",
    "market_research_equity_index_dealer_gamma_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchEquityIndexDealerGammaDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_EQUITY_INDEX_DEALER_GAMMA_DIGEST_CONFIG_VERSION
    )
    max_surface_age_seconds: Decimal = Decimal("1800.000000")
    min_abs_net_gamma_exposure_usd: Decimal = Decimal("250000000.000000")
    max_zero_gamma_distance_pct: Decimal = Decimal("0.015000")
    high_put_call_skew_score: Decimal = Decimal("0.700000")
    min_source_count: Decimal = Decimal("2.000000")
    max_acknowledgement_lag_seconds: Decimal = Decimal("900.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_EQUITY_INDEX_DEALER_GAMMA_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_surface_age_seconds",
            "min_abs_net_gamma_exposure_usd",
            "max_acknowledgement_lag_seconds",
        ):
            value = _require_nonnegative_decimal(field_name, getattr(self, field_name))
            if value <= ZERO:
                raise ValueError(f"{field_name} must be positive")
            object.__setattr__(self, field_name, value)
        for field_name in ("max_zero_gamma_distance_pct", "high_put_call_skew_score"):
            value = _require_ratio_decimal(field_name, getattr(self, field_name))
            if value <= ZERO:
                raise ValueError(f"{field_name} must be positive")
            object.__setattr__(self, field_name, value)
        object.__setattr__(
            self,
            "min_source_count",
            _require_positive_count_decimal("min_source_count", self.min_source_count),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchEquityIndexDealerGammaInputRow:
    research_key: str
    condition_id: str
    index_symbol: str
    gamma_surface_key: str
    source_reference: str
    observed_at: datetime
    acknowledged_at: datetime | None
    source_count: Decimal
    net_gamma_exposure_usd: Decimal
    zero_gamma_distance_pct: Decimal
    put_call_skew_score: Decimal
    spot_move_pct: Decimal
    contradiction_count: Decimal = ZERO
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "research_key",
            "condition_id",
            "index_symbol",
            "gamma_surface_key",
            "source_reference",
        ):
            _require_text(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_optional_utc("acknowledged_at", self.acknowledged_at),
        )
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        object.__setattr__(
            self,
            "net_gamma_exposure_usd",
            _require_decimal("net_gamma_exposure_usd", self.net_gamma_exposure_usd),
        )
        object.__setattr__(
            self,
            "zero_gamma_distance_pct",
            _require_ratio_decimal("zero_gamma_distance_pct", self.zero_gamma_distance_pct),
        )
        object.__setattr__(
            self,
            "put_call_skew_score",
            _require_ratio_decimal("put_call_skew_score", self.put_call_skew_score),
        )
        object.__setattr__(
            self,
            "spot_move_pct",
            _require_bounded_ratio_decimal("spot_move_pct", self.spot_move_pct),
        )
        object.__setattr__(
            self,
            "contradiction_count",
            _require_nonnegative_count_decimal(
                "contradiction_count",
                self.contradiction_count,
            ),
        )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchEquityIndexDealerGammaRow:
    research_key: str
    condition_id: str
    index_symbol: str
    gamma_surface_key: str
    gamma_status: str
    observed_at: datetime
    acknowledged_at: datetime | None
    surface_age_seconds: Decimal
    acknowledgement_lag_seconds: Decimal | None
    source_count: Decimal
    net_gamma_exposure_usd: Decimal
    gamma_abs_usd: Decimal
    zero_gamma_distance_pct: Decimal
    put_call_skew_score: Decimal
    spot_move_pct: Decimal
    contradiction_count: Decimal
    redacted_source_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "research_key",
            "condition_id",
            "index_symbol",
            "gamma_surface_key",
            "redacted_source_reference",
        ):
            _require_text(field_name, getattr(self, field_name))
        _require_gamma_status("gamma_status", self.gamma_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_optional_utc("acknowledged_at", self.acknowledged_at),
        )
        object.__setattr__(
            self,
            "surface_age_seconds",
            _require_nonnegative_decimal("surface_age_seconds", self.surface_age_seconds),
        )
        object.__setattr__(
            self,
            "acknowledgement_lag_seconds",
            _require_optional_nonnegative_decimal(
                "acknowledgement_lag_seconds",
                self.acknowledgement_lag_seconds,
            ),
        )
        for field_name in ("source_count", "contradiction_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("net_gamma_exposure_usd", "gamma_abs_usd"):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        if self.gamma_abs_usd < ZERO:
            raise ValueError("gamma_abs_usd must be nonnegative")
        object.__setattr__(
            self,
            "zero_gamma_distance_pct",
            _require_ratio_decimal("zero_gamma_distance_pct", self.zero_gamma_distance_pct),
        )
        object.__setattr__(
            self,
            "put_call_skew_score",
            _require_ratio_decimal("put_call_skew_score", self.put_call_skew_score),
        )
        object.__setattr__(
            self,
            "spot_move_pct",
            _require_bounded_ratio_decimal("spot_move_pct", self.spot_move_pct),
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
        _require_hard_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class MarketResearchEquityIndexDealerGammaReasonCodeCount:
    reason_code: str
    count: Decimal
    surface_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self.reason_code) is not str or self.reason_code not in REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be known")
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "surface_ratio",
            _require_ratio_decimal("surface_ratio", self.surface_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchEquityIndexDealerGammaReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    surface_count: Decimal
    ready_surface_count: Decimal
    watch_surface_count: Decimal
    blocked_surface_count: Decimal
    material_gamma_count: Decimal
    short_gamma_count: Decimal
    near_zero_gamma_count: Decimal
    stale_surface_count: Decimal
    thin_source_count: Decimal
    missing_acknowledgement_count: Decimal
    slow_acknowledgement_count: Decimal
    elevated_skew_count: Decimal
    contradiction_surface_count: Decimal
    net_gamma_exposure_usd: Decimal
    gross_gamma_exposure_usd: Decimal
    max_gamma_abs_usd: Decimal
    average_zero_gamma_distance_pct: Decimal
    average_put_call_skew_score: Decimal
    max_surface_age_seconds: Decimal
    rows: tuple[MarketResearchEquityIndexDealerGammaRow, ...]
    reason_code_counts: tuple[MarketResearchEquityIndexDealerGammaReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_EQUITY_INDEX_DEALER_GAMMA_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_gamma_status("digest_status", self.digest_status)
        if self.recommended_next_step != NEXT_STEPS[self.digest_status]:
            raise ValueError("recommended_next_step must match digest_status")
        for field_name in (
            "surface_count",
            "ready_surface_count",
            "watch_surface_count",
            "blocked_surface_count",
            "material_gamma_count",
            "short_gamma_count",
            "near_zero_gamma_count",
            "stale_surface_count",
            "thin_source_count",
            "missing_acknowledgement_count",
            "slow_acknowledgement_count",
            "elevated_skew_count",
            "contradiction_surface_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "net_gamma_exposure_usd",
            "gross_gamma_exposure_usd",
            "max_gamma_abs_usd",
            "max_surface_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        if self.gross_gamma_exposure_usd < ZERO:
            raise ValueError("gross_gamma_exposure_usd must be nonnegative")
        if self.max_gamma_abs_usd < ZERO:
            raise ValueError("max_gamma_abs_usd must be nonnegative")
        if self.max_surface_age_seconds < ZERO:
            raise ValueError("max_surface_age_seconds must be nonnegative")
        for field_name in (
            "average_zero_gamma_distance_pct",
            "average_put_call_skew_score",
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
        _require_hard_flags("report", self)
        _validate_report(self)


def build_market_research_equity_index_dealer_gamma_digest(
    rows: tuple[MarketResearchEquityIndexDealerGammaInputRow, ...],
    *,
    config: MarketResearchEquityIndexDealerGammaDigestConfig,
    generated_at: datetime,
) -> MarketResearchEquityIndexDealerGammaReport:
    if type(config) is not MarketResearchEquityIndexDealerGammaDigestConfig:
        raise ValueError(
            "config must be a MarketResearchEquityIndexDealerGammaDigestConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_input_rows(rows, generated_at=generated_at_utc)
    digest_rows = _rank_rows(
        tuple(_digest_row(row, config=config, generated_at=generated_at_utc) for row in input_rows),
    )
    reason_codes = _report_reason_codes(digest_rows)
    reason_code_counts = _reason_code_counts(
        digest_rows,
        reason_codes,
        _count(len(digest_rows)),
    )
    digest_status = _status_from_rows(digest_rows)
    return MarketResearchEquityIndexDealerGammaReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        surface_count=_count(len(digest_rows)),
        ready_surface_count=_count(
            sum(1 for row in digest_rows if row.gamma_status == STATUS_READY),
        ),
        watch_surface_count=_count(
            sum(1 for row in digest_rows if row.gamma_status == STATUS_WATCH),
        ),
        blocked_surface_count=_count(
            sum(1 for row in digest_rows if row.gamma_status == STATUS_BLOCKED),
        ),
        material_gamma_count=_reason_count(digest_rows, MATERIAL_GAMMA_REASON),
        short_gamma_count=_reason_count(digest_rows, SHORT_GAMMA_REASON),
        near_zero_gamma_count=_reason_count(digest_rows, NEAR_ZERO_GAMMA_REASON),
        stale_surface_count=_reason_count(digest_rows, STALE_SURFACE_REASON),
        thin_source_count=_reason_count(digest_rows, THIN_SOURCES_REASON),
        missing_acknowledgement_count=_reason_count(
            digest_rows,
            MISSING_ACKNOWLEDGEMENT_REASON,
        ),
        slow_acknowledgement_count=_reason_count(
            digest_rows,
            SLOW_ACKNOWLEDGEMENT_REASON,
        ),
        elevated_skew_count=_reason_count(digest_rows, ELEVATED_SKEW_REASON),
        contradiction_surface_count=_reason_count(
            digest_rows,
            CONTRADICTION_PRESENT_REASON,
        ),
        net_gamma_exposure_usd=sum(
            (row.net_gamma_exposure_usd for row in digest_rows),
            ZERO,
        ).quantize(QUANT),
        gross_gamma_exposure_usd=sum(
            (row.gamma_abs_usd for row in digest_rows),
            ZERO,
        ).quantize(QUANT),
        max_gamma_abs_usd=max((row.gamma_abs_usd for row in digest_rows), default=ZERO),
        average_zero_gamma_distance_pct=_average_row_decimal(
            digest_rows,
            "zero_gamma_distance_pct",
        ),
        average_put_call_skew_score=_average_row_decimal(
            digest_rows,
            "put_call_skew_score",
        ),
        max_surface_age_seconds=max(
            (row.surface_age_seconds for row in digest_rows),
            default=ZERO,
        ),
        rows=digest_rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_equity_index_dealer_gamma_digest_payload(
    report: MarketResearchEquityIndexDealerGammaReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchEquityIndexDealerGammaReport:
        raise ValueError("report must be a MarketResearchEquityIndexDealerGammaReport")
    _require_hard_flags("report", report)
    return _payload_value(report, _RedactionMap())


def _digest_row(
    row: MarketResearchEquityIndexDealerGammaInputRow,
    *,
    config: MarketResearchEquityIndexDealerGammaDigestConfig,
    generated_at: datetime,
) -> MarketResearchEquityIndexDealerGammaRow:
    surface_age_seconds = max(ZERO, _timedelta_seconds(generated_at - row.observed_at))
    acknowledgement_lag_seconds = (
        None
        if row.acknowledged_at is None
        else max(ZERO, _timedelta_seconds(row.acknowledged_at - row.observed_at))
    )
    gamma_abs_usd = abs(row.net_gamma_exposure_usd).quantize(QUANT)
    reason_codes = _row_reason_codes(
        net_gamma_exposure_usd=row.net_gamma_exposure_usd,
        gamma_abs_usd=gamma_abs_usd,
        zero_gamma_distance_pct=row.zero_gamma_distance_pct,
        put_call_skew_score=row.put_call_skew_score,
        source_count=row.source_count,
        surface_age_seconds=surface_age_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        contradiction_count=row.contradiction_count,
        config=config,
    )
    return MarketResearchEquityIndexDealerGammaRow(
        research_key=row.research_key,
        condition_id=row.condition_id,
        index_symbol=row.index_symbol,
        gamma_surface_key=row.gamma_surface_key,
        gamma_status=_row_status(reason_codes),
        observed_at=row.observed_at,
        acknowledged_at=row.acknowledged_at,
        surface_age_seconds=surface_age_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        source_count=row.source_count,
        net_gamma_exposure_usd=row.net_gamma_exposure_usd,
        gamma_abs_usd=gamma_abs_usd,
        zero_gamma_distance_pct=row.zero_gamma_distance_pct,
        put_call_skew_score=row.put_call_skew_score,
        spot_move_pct=row.spot_move_pct,
        contradiction_count=row.contradiction_count,
        redacted_source_reference=_redact_reference(row.source_reference),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    net_gamma_exposure_usd: Decimal,
    gamma_abs_usd: Decimal,
    zero_gamma_distance_pct: Decimal,
    put_call_skew_score: Decimal,
    source_count: Decimal,
    surface_age_seconds: Decimal,
    acknowledgement_lag_seconds: Decimal | None,
    contradiction_count: Decimal,
    config: MarketResearchEquityIndexDealerGammaDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if gamma_abs_usd >= config.min_abs_net_gamma_exposure_usd:
        reasons.append(MATERIAL_GAMMA_REASON)
        if net_gamma_exposure_usd < ZERO:
            reasons.append(SHORT_GAMMA_REASON)
    if zero_gamma_distance_pct <= config.max_zero_gamma_distance_pct:
        reasons.append(NEAR_ZERO_GAMMA_REASON)
    if surface_age_seconds > config.max_surface_age_seconds:
        reasons.append(STALE_SURFACE_REASON)
    if source_count < config.min_source_count:
        reasons.append(THIN_SOURCES_REASON)
    if acknowledgement_lag_seconds is None:
        reasons.append(MISSING_ACKNOWLEDGEMENT_REASON)
    elif acknowledgement_lag_seconds > config.max_acknowledgement_lag_seconds:
        reasons.append(SLOW_ACKNOWLEDGEMENT_REASON)
    if put_call_skew_score >= config.high_put_call_skew_score:
        reasons.append(ELEVATED_SKEW_REASON)
    if contradiction_count > ZERO:
        reasons.append(CONTRADICTION_PRESENT_REASON)
    if not reasons:
        return (READY_REASON,)
    if reasons == [MATERIAL_GAMMA_REASON]:
        return (READY_REASON, MATERIAL_GAMMA_REASON)
    return _normalize_reason_codes("reason_codes", tuple(reasons), ROW_REASON_CODE_SEQUENCE)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if (
        MISSING_ACKNOWLEDGEMENT_REASON in reason_codes
        or CONTRADICTION_PRESENT_REASON in reason_codes
    ):
        return STATUS_BLOCKED
    if reason_codes[0] == READY_REASON:
        return STATUS_READY
    return STATUS_WATCH


def _rank_rows(
    rows: tuple[MarketResearchEquityIndexDealerGammaRow, ...],
) -> tuple[MarketResearchEquityIndexDealerGammaRow, ...]:
    status_weight = {STATUS_BLOCKED: 0, STATUS_WATCH: 1, STATUS_READY: 2}
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                status_weight[row.gamma_status],
                row.research_key,
                row.condition_id,
            ),
        ),
    )


def _report_reason_codes(
    rows: tuple[MarketResearchEquityIndexDealerGammaRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    observed = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != READY_REASON
    }
    if not observed:
        return (READY_REASON,)
    return tuple(
        reason_code for reason_code in REPORT_REASON_CODE_SEQUENCE if reason_code in observed
    )


def _reason_code_counts(
    rows: tuple[MarketResearchEquityIndexDealerGammaRow, ...],
    reason_codes: tuple[str, ...],
    surface_count: Decimal,
) -> tuple[MarketResearchEquityIndexDealerGammaReasonCodeCount, ...]:
    if reason_codes == (NO_INPUTS_REASON,):
        return (
            MarketResearchEquityIndexDealerGammaReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                surface_ratio=ONE,
            ),
        )
    else:
        counts = Counter(
            reason_code
            for row in rows
            for reason_code in row.reason_codes
            if reason_code != READY_REASON
        )
        if not counts and reason_codes == (READY_REASON,):
            counts = Counter(reason_codes)
    return tuple(
        MarketResearchEquityIndexDealerGammaReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
            surface_ratio=_ratio(_count(count), surface_count),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: (
                -item[1],
                REPORT_REASON_CODE_SEQUENCE.index(item[0]),
            ),
        )
    )


def _status_from_rows(rows: tuple[MarketResearchEquityIndexDealerGammaRow, ...]) -> str:
    if not rows or any(row.gamma_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.gamma_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_READY


def _reason_count(
    rows: tuple[MarketResearchEquityIndexDealerGammaRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _average_row_decimal(
    rows: tuple[MarketResearchEquityIndexDealerGammaRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return _ratio(sum((getattr(row, field_name) for row in rows), ZERO), _count(len(rows)))


def _normalize_input_rows(
    rows: object,
    *,
    generated_at: datetime,
) -> tuple[MarketResearchEquityIndexDealerGammaInputRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen: set[tuple[str, str, str]] = set()
    for row in normalized:
        if type(row) is not MarketResearchEquityIndexDealerGammaInputRow:
            raise ValueError("rows must contain MarketResearchEquityIndexDealerGammaInputRow")
        _require_hard_flags("input row", row)
        key = (row.research_key, row.condition_id, row.gamma_surface_key)
        if key in seen:
            raise ValueError("rows must use unique research condition surface keys")
        seen.add(key)
        if row.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        if row.acknowledged_at is not None:
            if row.acknowledged_at > generated_at:
                raise ValueError("acknowledged_at must not be after generated_at")
            if row.acknowledged_at < row.observed_at:
                raise ValueError("acknowledged_at must not precede observed_at")
    return tuple(sorted(normalized, key=lambda row: (row.research_key, row.condition_id)))


def _normalize_rows(
    value: object,
) -> tuple[MarketResearchEquityIndexDealerGammaRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str, str]] = set()
    previous_key: tuple[int, str, str] | None = None
    status_weight = {STATUS_BLOCKED: 0, STATUS_WATCH: 1, STATUS_READY: 2}
    for row in rows:
        if type(row) is not MarketResearchEquityIndexDealerGammaRow:
            raise ValueError("rows must contain MarketResearchEquityIndexDealerGammaRow")
        _require_hard_flags("row", row)
        row_key = (row.research_key, row.condition_id, row.gamma_surface_key)
        if row_key in seen:
            raise ValueError("rows must use unique research condition surface keys")
        key = (status_weight[row.gamma_status], row.research_key, row.condition_id)
        if previous_key is not None and previous_key > key:
            raise ValueError("rows must use deterministic ranking")
        previous_key = key
        seen.add(row_key)
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketResearchEquityIndexDealerGammaReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    previous_key: tuple[Decimal, int] | None = None
    for row in rows:
        if type(row) is not MarketResearchEquityIndexDealerGammaReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchEquityIndexDealerGammaReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", row)
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        key = (-row.count, REPORT_REASON_CODE_SEQUENCE.index(row.reason_code))
        if previous_key is not None and previous_key > key:
            raise ValueError("reason_code_counts must use deterministic ranking")
        previous_key = key
        seen.add(row.reason_code)
    return rows


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    if any(type(reason_code) is not str for reason_code in reason_codes):
        raise ValueError(f"{field_name} must contain strings")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    if any(reason_code not in allowed_reason_codes for reason_code in reason_codes):
        raise ValueError(f"{field_name} must contain known reason codes")
    expected = tuple(
        reason_code for reason_code in allowed_reason_codes if reason_code in reason_codes
    )
    if reason_codes != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return reason_codes


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return value.quantize(QUANT)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        normalized = value.quantize(QUANT)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_bounded_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < -ONE or normalized > ONE:
        raise ValueError(f"{field_name} must be between negative one and one")
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _timedelta_seconds(value: timedelta) -> Decimal:
    with localcontext() as context:
        context.prec = 28
        total_microseconds = (
            (Decimal(value.days) * SECONDS_PER_DAY * MICROSECONDS_PER_SECOND)
            + (Decimal(value.seconds) * MICROSECONDS_PER_SECOND)
            + Decimal(value.microseconds)
        )
        return (total_microseconds / MICROSECONDS_PER_SECOND).quantize(QUANT)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext() as context:
        context.prec = 28
        return (numerator / denominator).quantize(QUANT)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT)


def _require_text(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_gamma_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in GAMMA_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _validate_row(row: MarketResearchEquityIndexDealerGammaRow) -> None:
    if row.gamma_abs_usd != abs(row.net_gamma_exposure_usd).quantize(QUANT):
        raise ValueError("gamma_abs_usd must match net_gamma_exposure_usd magnitude")
    has_blocking_reason = (
        MISSING_ACKNOWLEDGEMENT_REASON in row.reason_codes
        or CONTRADICTION_PRESENT_REASON in row.reason_codes
    )
    if row.gamma_status == STATUS_BLOCKED and not has_blocking_reason:
        raise ValueError("blocked rows require a blocking reason")
    if has_blocking_reason and row.gamma_status != STATUS_BLOCKED:
        raise ValueError("blocking reasons require blocked status")
    if row.reason_codes[0] == READY_REASON:
        if row.gamma_status != STATUS_READY:
            raise ValueError("ready rows require ready status")
    elif row.gamma_status != STATUS_WATCH and row.gamma_status != STATUS_BLOCKED:
        raise ValueError("watch reasons require watch or blocked status")


def _validate_report(report: MarketResearchEquityIndexDealerGammaReport) -> None:
    if report.surface_count != _count(len(report.rows)):
        raise ValueError("surface_count must match rows")
    if report.surface_count != (
        report.ready_surface_count + report.watch_surface_count + report.blocked_surface_count
    ):
        raise ValueError("surface_count must equal status counts")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(
        report.rows,
        report.reason_codes,
        report.surface_count,
    ):
        raise ValueError("reason_code_counts must match reason_codes")
    if report.digest_status != _status_from_rows(report.rows):
        raise ValueError("digest_status must match rows")
    if report.material_gamma_count != _reason_count(report.rows, MATERIAL_GAMMA_REASON):
        raise ValueError("material_gamma_count must match rows")
    if report.short_gamma_count != _reason_count(report.rows, SHORT_GAMMA_REASON):
        raise ValueError("short_gamma_count must match rows")
    if report.near_zero_gamma_count != _reason_count(report.rows, NEAR_ZERO_GAMMA_REASON):
        raise ValueError("near_zero_gamma_count must match rows")
    if report.stale_surface_count != _reason_count(report.rows, STALE_SURFACE_REASON):
        raise ValueError("stale_surface_count must match rows")
    if report.thin_source_count != _reason_count(report.rows, THIN_SOURCES_REASON):
        raise ValueError("thin_source_count must match rows")
    if report.missing_acknowledgement_count != _reason_count(
        report.rows,
        MISSING_ACKNOWLEDGEMENT_REASON,
    ):
        raise ValueError("missing_acknowledgement_count must match rows")
    if report.slow_acknowledgement_count != _reason_count(
        report.rows,
        SLOW_ACKNOWLEDGEMENT_REASON,
    ):
        raise ValueError("slow_acknowledgement_count must match rows")
    if report.elevated_skew_count != _reason_count(report.rows, ELEVATED_SKEW_REASON):
        raise ValueError("elevated_skew_count must match rows")
    if report.contradiction_surface_count != _reason_count(
        report.rows,
        CONTRADICTION_PRESENT_REASON,
    ):
        raise ValueError("contradiction_surface_count must match rows")


def _redact_reference(value: str) -> str:
    if value.startswith("public-"):
        return value
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()[:12]}"


class _RedactionMap:
    def __init__(self) -> None:
        self._values: dict[tuple[str, str], str] = {}
        self._counters: Counter[str] = Counter()

    def ref(self, kind: str, value: str) -> str:
        key = (kind, value)
        if key not in self._values:
            self._counters[kind] += 1
            self._values[key] = f"<redacted-{kind}-{self._counters[kind]:03d}>"
        return self._values[key]


def _payload_value(value: object, redaction_map: _RedactionMap) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, tuple):
        return [_payload_value(item, redaction_map) for item in value]
    if isinstance(value, list):
        return [_payload_value(item, redaction_map) for item in value]
    if is_dataclass(value) and not isinstance(value, type):
        result: dict[str, Any] = {}
        for field in fields(value):
            field_name = field.name
            if field_name == "condition_id":
                continue
            result[field_name] = _payload_value(getattr(value, field_name), redaction_map)
        if isinstance(value, MarketResearchEquityIndexDealerGammaRow):
            result["redacted_condition_ref"] = redaction_map.ref(
                "condition",
                value.condition_id,
            )
        return result
    if isinstance(value, dict):
        return {
            str(key): _payload_value(item, redaction_map) for key, item in value.items()
        }
    if isinstance(value, (str, bool)) or value is None:
        return value
    raise ValueError(f"unsupported payload value type: {type(value).__name__}")
