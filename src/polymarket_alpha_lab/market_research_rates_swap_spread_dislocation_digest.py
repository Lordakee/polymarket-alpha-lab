"""Pure Phase 1 rates swap-spread dislocation report reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import re
from typing import Any


DEFAULT_MARKET_RESEARCH_RATES_SWAP_SPREAD_DISLOCATION_DIGEST_CONFIG_VERSION = (
    "market-research-rates-swap-spread-dislocation-digest-v0"
)

DISLOCATION_STATUSES = ("pass", "watch", "blocked")
DISLOCATION_DIRECTIONS = ("neutral", "positive_widening", "negative_inversion")
ROW_REASON_CODE_SEQUENCE = (
    "rates_swap_spread_dislocation_digest_pass",
    "rates_swap_spread_dislocation_digest_watch_spread",
    "rates_swap_spread_dislocation_digest_blocked_spread",
    "rates_swap_spread_dislocation_digest_spread_shock",
    "rates_swap_spread_dislocation_digest_persistent",
    "rates_swap_spread_dislocation_digest_thin_sources",
    "rates_swap_spread_dislocation_digest_stale_observation",
    "rates_swap_spread_dislocation_digest_confidence_gap",
)
REPORT_REASON_CODE_SEQUENCE = (
    "rates_swap_spread_dislocation_digest_blocked_spread_present",
    "rates_swap_spread_dislocation_digest_watch_spread_present",
    "rates_swap_spread_dislocation_digest_spread_shock_present",
    "rates_swap_spread_dislocation_digest_persistent_present",
    "rates_swap_spread_dislocation_digest_data_quality_gap_present",
    "rates_swap_spread_dislocation_digest_clear",
    "rates_swap_spread_dislocation_digest_no_inputs",
)

NEXT_STEPS = {
    "pass": "allow_report_only_rates_swap_spread_dislocation_screening",
    "watch": "monitor_report_only_rates_swap_spread_dislocation_screening",
    "blocked": "block_report_only_rates_swap_spread_dislocation_screening",
}
STATUS_SORT_RANK = {
    "blocked": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}
QUALITY_ROW_REASON_CODES = (
    "rates_swap_spread_dislocation_digest_thin_sources",
    "rates_swap_spread_dislocation_digest_stale_observation",
    "rates_swap_spread_dislocation_digest_confidence_gap",
)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")

__all__ = (
    "DEFAULT_MARKET_RESEARCH_RATES_SWAP_SPREAD_DISLOCATION_DIGEST_CONFIG_VERSION",
    "MarketResearchRatesSwapSpreadDislocationDigestConfig",
    "MarketResearchRatesSwapSpreadDislocationObservation",
    "MarketResearchRatesSwapSpreadDislocationDigestRow",
    "MarketResearchRatesSwapSpreadDislocationReasonCodeCount",
    "MarketResearchRatesSwapSpreadDislocationDigestReport",
    "build_market_research_rates_swap_spread_dislocation_digest",
    "market_research_rates_swap_spread_dislocation_digest_payload",
)


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
class MarketResearchRatesSwapSpreadDislocationDigestConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_RATES_SWAP_SPREAD_DISLOCATION_DIGEST_CONFIG_VERSION
    )
    max_observation_age_seconds: Decimal = Decimal("7200.000000")
    min_source_count: Decimal = Decimal("2.000000")
    watch_swap_spread_bps_abs: Decimal = Decimal("15.000000")
    blocked_swap_spread_bps_abs: Decimal = Decimal("30.000000")
    spread_change_shock_bps_abs: Decimal = Decimal("10.000000")
    min_dislocation_persistence_hours: Decimal = Decimal("4.000000")
    min_confidence: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchRatesSwapSpreadDislocationDigestConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_RATES_SWAP_SPREAD_DISLOCATION_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("max_observation_age_seconds", "min_source_count"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_swap_spread_bps_abs",
            "blocked_swap_spread_bps_abs",
            "spread_change_shock_bps_abs",
            "min_dislocation_persistence_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_confidence",
            _require_ratio_decimal("min_confidence", self.min_confidence),
        )
        if self.watch_swap_spread_bps_abs > self.blocked_swap_spread_bps_abs:
            raise ValueError(
                "watch_swap_spread_bps_abs must not exceed blocked_swap_spread_bps_abs",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchRatesSwapSpreadDislocationObservation(_FinalPublicDataclass):
    research_id: str
    instrument_id: str
    curve_tenor: str
    observed_at: datetime
    source_count: Decimal
    swap_spread_bps: Decimal
    prior_swap_spread_bps: Decimal
    dislocation_persistence_hours: Decimal
    confidence: Decimal
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchRatesSwapSpreadDislocationObservation,
            "observation",
        )
        for field_name in ("research_id", "instrument_id", "curve_tenor"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        for field_name in ("swap_spread_bps", "prior_swap_spread_bps"):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "dislocation_persistence_hours",
            _require_nonnegative_decimal(
                "dislocation_persistence_hours",
                self.dislocation_persistence_hours,
            ),
        )
        object.__setattr__(
            self,
            "confidence",
            _require_ratio_decimal("confidence", self.confidence),
        )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_open_reason_codes(
                "upstream_reason_codes",
                self.upstream_reason_codes,
            ),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class MarketResearchRatesSwapSpreadDislocationDigestRow(_FinalPublicDataclass):
    research_id: str
    instrument_id: str
    curve_tenor: str
    dislocation_status: str
    dislocation_direction: str
    observed_at: datetime
    observation_age_seconds: Decimal
    source_count: Decimal
    swap_spread_bps: Decimal
    prior_swap_spread_bps: Decimal
    absolute_swap_spread_bps: Decimal
    spread_change_bps: Decimal
    absolute_spread_change_bps: Decimal
    dislocation_persistence_hours: Decimal
    confidence: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchRatesSwapSpreadDislocationDigestRow,
            "row",
        )
        for field_name in ("research_id", "instrument_id", "curve_tenor"):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member("dislocation_status", self.dislocation_status, DISLOCATION_STATUSES)
        _require_member(
            "dislocation_direction",
            self.dislocation_direction,
            DISLOCATION_DIRECTIONS,
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "observation_age_seconds",
            _require_nonnegative_count_decimal(
                "observation_age_seconds",
                self.observation_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        for field_name in ("swap_spread_bps", "prior_swap_spread_bps", "spread_change_bps"):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "absolute_swap_spread_bps",
            "absolute_spread_change_bps",
            "dislocation_persistence_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "confidence",
            _require_ratio_decimal("confidence", self.confidence),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _require_canonical_reason_codes(
                "reason_codes",
                self.reason_codes,
                ROW_REASON_CODE_SEQUENCE,
            ),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchRatesSwapSpreadDislocationReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchRatesSwapSpreadDislocationReasonCodeCount,
            "reason code count",
        )
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODE_SEQUENCE)
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchRatesSwapSpreadDislocationDigestReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    input_count: Decimal
    row_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    spread_dislocation_count: Decimal
    spread_shock_count: Decimal
    persistent_dislocation_count: Decimal
    data_quality_gap_count: Decimal
    average_swap_spread_bps: Decimal
    average_absolute_swap_spread_bps: Decimal
    max_absolute_swap_spread_bps: Decimal
    average_dislocation_persistence_hours: Decimal
    rows: tuple[MarketResearchRatesSwapSpreadDislocationDigestRow, ...]
    reason_code_counts: tuple[
        MarketResearchRatesSwapSpreadDislocationReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchRatesSwapSpreadDislocationDigestReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_RATES_SWAP_SPREAD_DISLOCATION_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_member("digest_status", self.digest_status, DISLOCATION_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "input_count",
            "row_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "spread_dislocation_count",
            "spread_shock_count",
            "persistent_dislocation_count",
            "data_quality_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_absolute_swap_spread_bps",
            "max_absolute_swap_spread_bps",
            "average_dislocation_persistence_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_swap_spread_bps",
            _require_decimal("average_swap_spread_bps", self.average_swap_spread_bps),
        )
        object.__setattr__(self, "rows", _require_canonical_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _require_canonical_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _require_canonical_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODE_SEQUENCE,
            ),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


_PUBLIC_DATACLASS_TYPES = (
    MarketResearchRatesSwapSpreadDislocationDigestConfig,
    MarketResearchRatesSwapSpreadDislocationObservation,
    MarketResearchRatesSwapSpreadDislocationDigestRow,
    MarketResearchRatesSwapSpreadDislocationReasonCodeCount,
    MarketResearchRatesSwapSpreadDislocationDigestReport,
)


def build_market_research_rates_swap_spread_dislocation_digest(
    observations: Iterable[MarketResearchRatesSwapSpreadDislocationObservation],
    *,
    config: MarketResearchRatesSwapSpreadDislocationDigestConfig,
    generated_at: datetime,
) -> MarketResearchRatesSwapSpreadDislocationDigestReport:
    if type(config) is not MarketResearchRatesSwapSpreadDislocationDigestConfig:
        raise ValueError(
            "config must be exactly MarketResearchRatesSwapSpreadDislocationDigestConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    observation,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for observation in input_rows
            ),
            key=_row_sort_key,
        ),
    )
    row_count = _decimal_count(len(rows))
    digest_status = _digest_status(rows)
    reason_codes = _report_reason_codes(rows)

    return MarketResearchRatesSwapSpreadDislocationDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        input_count=_decimal_count(len(input_rows)),
        row_count=row_count,
        blocked_count=_status_count(rows, "blocked"),
        watch_count=_status_count(rows, "watch"),
        pass_count=_status_count(rows, "pass"),
        spread_dislocation_count=_spread_dislocation_count(rows),
        spread_shock_count=_reason_count(
            rows,
            "rates_swap_spread_dislocation_digest_spread_shock",
        ),
        persistent_dislocation_count=_reason_count(
            rows,
            "rates_swap_spread_dislocation_digest_persistent",
        ),
        data_quality_gap_count=_quality_gap_count(rows),
        average_swap_spread_bps=_divide(
            _sum_decimal(row.swap_spread_bps for row in rows),
            row_count,
        ),
        average_absolute_swap_spread_bps=_divide(
            _sum_decimal(row.absolute_swap_spread_bps for row in rows),
            row_count,
        ),
        max_absolute_swap_spread_bps=max(
            (row.absolute_swap_spread_bps for row in rows),
            default=ZERO,
        ),
        average_dislocation_persistence_hours=_divide(
            _sum_decimal(row.dislocation_persistence_hours for row in rows),
            row_count,
        ),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes, row_count),
        reason_codes=reason_codes,
    )


def market_research_rates_swap_spread_dislocation_digest_payload(
    report: MarketResearchRatesSwapSpreadDislocationDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchRatesSwapSpreadDislocationDigestReport:
        raise ValueError(
            "report must be exactly MarketResearchRatesSwapSpreadDislocationDigestReport",
        )
    _require_payload_safe_value("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _row_from_observation(
    observation: MarketResearchRatesSwapSpreadDislocationObservation,
    *,
    config: MarketResearchRatesSwapSpreadDislocationDigestConfig,
    generated_at: datetime,
) -> MarketResearchRatesSwapSpreadDislocationDigestRow:
    if observation.observed_at > generated_at:
        raise ValueError("observed_at cannot be after generated_at")
    absolute_swap_spread_bps = _quantize(abs(observation.swap_spread_bps))
    spread_change_bps = _quantize(
        observation.swap_spread_bps - observation.prior_swap_spread_bps,
    )
    absolute_spread_change_bps = _quantize(abs(spread_change_bps))
    observation_age_seconds = _duration_seconds(generated_at - observation.observed_at)
    dislocation_status = _dislocation_status(
        absolute_swap_spread_bps,
        config=config,
    )
    return MarketResearchRatesSwapSpreadDislocationDigestRow(
        research_id=observation.research_id,
        instrument_id=observation.instrument_id,
        curve_tenor=observation.curve_tenor,
        dislocation_status=dislocation_status,
        dislocation_direction=_dislocation_direction(
            observation.swap_spread_bps,
            dislocation_status,
        ),
        observed_at=observation.observed_at,
        observation_age_seconds=observation_age_seconds,
        source_count=observation.source_count,
        swap_spread_bps=observation.swap_spread_bps,
        prior_swap_spread_bps=observation.prior_swap_spread_bps,
        absolute_swap_spread_bps=absolute_swap_spread_bps,
        spread_change_bps=spread_change_bps,
        absolute_spread_change_bps=absolute_spread_change_bps,
        dislocation_persistence_hours=observation.dislocation_persistence_hours,
        confidence=observation.confidence,
        reason_codes=_row_reason_codes(
            observation,
            dislocation_status=dislocation_status,
            absolute_spread_change_bps=absolute_spread_change_bps,
            observation_age_seconds=observation_age_seconds,
            config=config,
        ),
    )


def _dislocation_status(
    absolute_swap_spread_bps: Decimal,
    *,
    config: MarketResearchRatesSwapSpreadDislocationDigestConfig,
) -> str:
    if absolute_swap_spread_bps >= config.blocked_swap_spread_bps_abs:
        return "blocked"
    if absolute_swap_spread_bps >= config.watch_swap_spread_bps_abs:
        return "watch"
    return "pass"


def _dislocation_direction(swap_spread_bps: Decimal, dislocation_status: str) -> str:
    if dislocation_status == "pass" or swap_spread_bps == ZERO:
        return "neutral"
    if swap_spread_bps > ZERO:
        return "positive_widening"
    return "negative_inversion"


def _row_reason_codes(
    observation: MarketResearchRatesSwapSpreadDislocationObservation,
    *,
    dislocation_status: str,
    absolute_spread_change_bps: Decimal,
    observation_age_seconds: Decimal,
    config: MarketResearchRatesSwapSpreadDislocationDigestConfig,
) -> tuple[str, ...]:
    if dislocation_status == "blocked":
        reason_codes = ["rates_swap_spread_dislocation_digest_blocked_spread"]
    elif dislocation_status == "watch":
        reason_codes = ["rates_swap_spread_dislocation_digest_watch_spread"]
    else:
        reason_codes = ["rates_swap_spread_dislocation_digest_pass"]

    if dislocation_status != "pass":
        if absolute_spread_change_bps >= config.spread_change_shock_bps_abs:
            reason_codes.append("rates_swap_spread_dislocation_digest_spread_shock")
        if (
            observation.dislocation_persistence_hours
            >= config.min_dislocation_persistence_hours
        ):
            reason_codes.append("rates_swap_spread_dislocation_digest_persistent")
    if observation.source_count < config.min_source_count:
        reason_codes.append("rates_swap_spread_dislocation_digest_thin_sources")
    if observation_age_seconds > config.max_observation_age_seconds:
        reason_codes.append("rates_swap_spread_dislocation_digest_stale_observation")
    if observation.confidence < config.min_confidence:
        reason_codes.append("rates_swap_spread_dislocation_digest_confidence_gap")
    return _require_canonical_reason_codes(
        "reason_codes",
        tuple(reason_codes),
        ROW_REASON_CODE_SEQUENCE,
    )


def _report_reason_codes(
    rows: tuple[MarketResearchRatesSwapSpreadDislocationDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("rates_swap_spread_dislocation_digest_no_inputs",)
    reason_codes: list[str] = []
    if _reason_count(rows, "rates_swap_spread_dislocation_digest_blocked_spread") > ZERO:
        reason_codes.append("rates_swap_spread_dislocation_digest_blocked_spread_present")
    if _reason_count(rows, "rates_swap_spread_dislocation_digest_watch_spread") > ZERO:
        reason_codes.append("rates_swap_spread_dislocation_digest_watch_spread_present")
    if _reason_count(rows, "rates_swap_spread_dislocation_digest_spread_shock") > ZERO:
        reason_codes.append("rates_swap_spread_dislocation_digest_spread_shock_present")
    if _reason_count(rows, "rates_swap_spread_dislocation_digest_persistent") > ZERO:
        reason_codes.append("rates_swap_spread_dislocation_digest_persistent_present")
    if _quality_gap_count(rows) > ZERO:
        reason_codes.append("rates_swap_spread_dislocation_digest_data_quality_gap_present")
    if not reason_codes:
        reason_codes.append("rates_swap_spread_dislocation_digest_clear")
    return _require_canonical_reason_codes(
        "reason_codes",
        tuple(reason_codes),
        REPORT_REASON_CODE_SEQUENCE,
    )


def _reason_code_counts(
    rows: tuple[MarketResearchRatesSwapSpreadDislocationDigestRow, ...],
    reason_codes: tuple[str, ...],
    row_count: Decimal,
) -> tuple[MarketResearchRatesSwapSpreadDislocationReasonCodeCount, ...]:
    if reason_codes == ("rates_swap_spread_dislocation_digest_no_inputs",):
        return ()
    return tuple(
        MarketResearchRatesSwapSpreadDislocationReasonCodeCount(
            reason_code=reason_code,
            count=_report_reason_row_count(rows, reason_code),
            row_ratio=_divide(_report_reason_row_count(rows, reason_code), row_count),
        )
        for reason_code in reason_codes
    )


def _report_reason_row_count(
    rows: tuple[MarketResearchRatesSwapSpreadDislocationDigestRow, ...],
    reason_code: str,
) -> Decimal:
    row_reason_code_by_report_reason = {
        "rates_swap_spread_dislocation_digest_blocked_spread_present": (
            "rates_swap_spread_dislocation_digest_blocked_spread"
        ),
        "rates_swap_spread_dislocation_digest_watch_spread_present": (
            "rates_swap_spread_dislocation_digest_watch_spread"
        ),
        "rates_swap_spread_dislocation_digest_spread_shock_present": (
            "rates_swap_spread_dislocation_digest_spread_shock"
        ),
        "rates_swap_spread_dislocation_digest_persistent_present": (
            "rates_swap_spread_dislocation_digest_persistent"
        ),
        "rates_swap_spread_dislocation_digest_clear": (
            "rates_swap_spread_dislocation_digest_pass"
        ),
    }
    if reason_code == "rates_swap_spread_dislocation_digest_data_quality_gap_present":
        return _quality_gap_count(rows)
    return _reason_count(rows, row_reason_code_by_report_reason[reason_code])


def _digest_status(
    rows: tuple[MarketResearchRatesSwapSpreadDislocationDigestRow, ...],
) -> str:
    if not rows:
        return "blocked"
    if any(row.dislocation_status == "blocked" for row in rows):
        return "blocked"
    if any(row.dislocation_status == "watch" for row in rows):
        return "watch"
    if _quality_gap_count(rows) > ZERO:
        return "watch"
    return "pass"


def _validate_row(row: MarketResearchRatesSwapSpreadDislocationDigestRow) -> None:
    if row.absolute_swap_spread_bps != abs(row.swap_spread_bps):
        raise ValueError("absolute_swap_spread_bps must match swap_spread_bps")
    if row.spread_change_bps != _quantize(
        row.swap_spread_bps - row.prior_swap_spread_bps,
    ):
        raise ValueError("spread_change_bps must match swap spread inputs")
    if row.absolute_spread_change_bps != abs(row.spread_change_bps):
        raise ValueError("absolute_spread_change_bps must match spread_change_bps")
    if row.dislocation_status == "pass":
        if "rates_swap_spread_dislocation_digest_pass" not in row.reason_codes:
            raise ValueError("reason_codes must match dislocation_status")
        if any(
            reason_code in row.reason_codes
            for reason_code in (
                "rates_swap_spread_dislocation_digest_watch_spread",
                "rates_swap_spread_dislocation_digest_blocked_spread",
            )
        ):
            raise ValueError("reason_codes must match dislocation_status")
    if row.dislocation_status == "watch":
        if "rates_swap_spread_dislocation_digest_watch_spread" not in row.reason_codes:
            raise ValueError("reason_codes must match dislocation_status")
        if "rates_swap_spread_dislocation_digest_blocked_spread" in row.reason_codes:
            raise ValueError("reason_codes must match dislocation_status")
    if row.dislocation_status == "blocked":
        if "rates_swap_spread_dislocation_digest_blocked_spread" not in row.reason_codes:
            raise ValueError("reason_codes must match dislocation_status")
        if "rates_swap_spread_dislocation_digest_watch_spread" in row.reason_codes:
            raise ValueError("reason_codes must match dislocation_status")
    if row.dislocation_direction != _dislocation_direction(
        row.swap_spread_bps,
        row.dislocation_status,
    ):
        raise ValueError("dislocation_direction must match swap_spread_bps")


def _validate_report(report: MarketResearchRatesSwapSpreadDislocationDigestReport) -> None:
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.blocked_count + report.watch_count + report.pass_count != report.row_count:
        raise ValueError("status counts must match rows")
    if report.spread_dislocation_count != _spread_dislocation_count(report.rows):
        raise ValueError("spread_dislocation_count must match rows")
    if report.spread_shock_count != _reason_count(
        report.rows,
        "rates_swap_spread_dislocation_digest_spread_shock",
    ):
        raise ValueError("spread_shock_count must match rows")
    if report.persistent_dislocation_count != _reason_count(
        report.rows,
        "rates_swap_spread_dislocation_digest_persistent",
    ):
        raise ValueError("persistent_dislocation_count must match rows")
    if report.data_quality_gap_count != _quality_gap_count(report.rows):
        raise ValueError("data_quality_gap_count must match rows")
    if report.average_swap_spread_bps != _divide(
        _sum_decimal(row.swap_spread_bps for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_swap_spread_bps must match rows")
    if report.average_absolute_swap_spread_bps != _divide(
        _sum_decimal(row.absolute_swap_spread_bps for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_absolute_swap_spread_bps must match rows")
    if report.max_absolute_swap_spread_bps != max(
        (row.absolute_swap_spread_bps for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_absolute_swap_spread_bps must match rows")
    if report.average_dislocation_persistence_hours != _divide(
        _sum_decimal(row.dislocation_persistence_hours for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_dislocation_persistence_hours must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(
        report.rows,
        report.reason_codes,
        report.row_count,
    ):
        raise ValueError("reason_code_counts must match rows")


def _normalize_observations(
    observations: Iterable[MarketResearchRatesSwapSpreadDislocationObservation],
) -> tuple[MarketResearchRatesSwapSpreadDislocationObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError(
            "observations must contain MarketResearchRatesSwapSpreadDislocationObservation",
        )
    normalized = tuple(observations)
    seen_research_ids: set[str] = set()
    for observation in normalized:
        if type(observation) is not MarketResearchRatesSwapSpreadDislocationObservation:
            raise ValueError(
                "observations must contain "
                "MarketResearchRatesSwapSpreadDislocationObservation",
            )
        _require_hard_flags("observation", observation)
        if observation.research_id in seen_research_ids:
            raise ValueError("observations must not contain duplicate research_id values")
        seen_research_ids.add(observation.research_id)
    return normalized


def _require_canonical_rows(
    rows: object,
) -> tuple[MarketResearchRatesSwapSpreadDislocationDigestRow, ...]:
    if type(rows) is not tuple:
        raise TypeError("rows must be a tuple")
    normalized = []
    seen_research_ids: set[str] = set()
    previous_key: tuple[Decimal, Decimal, str, str] | None = None
    for row in rows:
        if type(row) is not MarketResearchRatesSwapSpreadDislocationDigestRow:
            raise ValueError(
                "rows must contain MarketResearchRatesSwapSpreadDislocationDigestRow",
            )
        _require_hard_flags("row", row)
        if row.research_id in seen_research_ids:
            raise ValueError("rows must contain unique research_id values")
        key = _row_sort_key(row)
        if previous_key is not None and previous_key > key:
            raise ValueError("rows must be a canonical sequence")
        previous_key = key
        seen_research_ids.add(row.research_id)
        normalized.append(row)
    return tuple(normalized)


def _require_canonical_reason_code_counts(
    rows: object,
) -> tuple[MarketResearchRatesSwapSpreadDislocationReasonCodeCount, ...]:
    if type(rows) is not tuple:
        raise TypeError("reason_code_counts must be a tuple")
    normalized = []
    seen_reason_codes: set[str] = set()
    previous_key: int | None = None
    for row in rows:
        if type(row) is not MarketResearchRatesSwapSpreadDislocationReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchRatesSwapSpreadDislocationReasonCodeCount",
            )
        _require_hard_flags("reason code count", row)
        if row.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts must be unique")
        key = REPORT_REASON_CODE_SEQUENCE.index(row.reason_code)
        if previous_key is not None and previous_key > key:
            raise ValueError("reason_code_counts must be a canonical sequence")
        previous_key = key
        seen_reason_codes.add(row.reason_code)
        normalized.append(row)
    return tuple(normalized)


def _normalize_open_reason_codes(field_name: str, values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise TypeError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_canonical_string("reason_code", value)
        if value not in normalized:
            normalized.append(value)
    return tuple(sorted(normalized))


def _require_canonical_reason_codes(
    field_name: str,
    values: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise TypeError(f"{field_name} must be a tuple")
    previous_index: int | None = None
    seen: set[str] = set()
    for value in values:
        _require_member("reason_code", value, allowed)
        if value in seen:
            raise ValueError(f"{field_name} must be unique")
        index = allowed.index(value)
        if previous_index is not None and previous_index > index:
            raise ValueError(f"{field_name} must be a canonical sequence")
        previous_index = index
        seen.add(value)
    return values


def _row_sort_key(
    row: MarketResearchRatesSwapSpreadDislocationDigestRow,
) -> tuple[Decimal, Decimal, str, str]:
    return (
        STATUS_SORT_RANK[row.dislocation_status],
        -row.absolute_swap_spread_bps,
        row.curve_tenor,
        row.research_id,
    )


def _status_count(
    rows: tuple[MarketResearchRatesSwapSpreadDislocationDigestRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.dislocation_status == status))


def _reason_count(
    rows: tuple[MarketResearchRatesSwapSpreadDislocationDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _spread_dislocation_count(
    rows: tuple[MarketResearchRatesSwapSpreadDislocationDigestRow, ...],
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.dislocation_status != "pass"))


def _quality_gap_count(
    rows: tuple[MarketResearchRatesSwapSpreadDislocationDigestRow, ...],
) -> Decimal:
    return _decimal_count(
        sum(
            1
            for row in rows
            if any(reason_code in row.reason_codes for reason_code in QUALITY_ROW_REASON_CODES)
        ),
    )


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
        total += value
    return _quantize(total)


def _divide(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _duration_seconds(delta: object) -> Decimal:
    days = getattr(delta, "days")
    seconds = getattr(delta, "seconds")
    microseconds = getattr(delta, "microseconds")
    total_microseconds = (
        Decimal(days) * SECONDS_PER_DAY * MICROSECONDS_PER_SECOND
        + Decimal(seconds) * MICROSECONDS_PER_SECOND
        + Decimal(microseconds)
    )
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(total_microseconds / MICROSECONDS_PER_SECOND)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_count_decimal(field_name, value)
    if decimal_value == ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integer count")
    return _quantize(decimal_value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be supported")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value or _CANONICAL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _payload_value(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if value is None or type(value) in (bool, str):
        return value
    raise ValueError("payload contains unsupported value")


def _require_payload_safe_value(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{label} contains unsupported dataclass")
        for field in fields(value):
            _require_payload_safe_value(f"{label}.{field.name}", getattr(value, field.name))
        _rebuild_public_dataclass(label, value)
        return
    if type(value) is Decimal:
        _require_six_decimal_decimal(label, value)
        return
    if type(value) is datetime:
        _require_utc_datetime(label, value)
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _require_payload_safe_value(f"{label}[{index}]", item)
        return
    if value is None or type(value) is bool:
        return
    if type(value) is str:
        _require_canonical_string(label, value)
        return
    raise ValueError(f"{label} contains unsupported value")


def _rebuild_public_dataclass(label: str, value: object) -> None:
    kwargs = {field.name: getattr(value, field.name) for field in fields(value)}
    try:
        type(value)(**kwargs)
    except Exception as exc:
        raise ValueError(f"{label} failed payload revalidation") from exc


def _require_six_decimal_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value != _quantize(value) or value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must be a six decimal Decimal")


def _require_utc_datetime(field_name: str, value: object) -> None:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is not UTC or value.utcoffset() != ZERO_TIME_OFFSET:
        raise ValueError(f"{field_name} must be UTC")


ZERO_TIME_OFFSET = datetime.min.replace(tzinfo=UTC).utcoffset()
