"""Pure Phase 1 rates inflation-swap breakout risk digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import re
from typing import Any


DEFAULT_RATES_INFLATION_SWAP_BREAKOUT_DIGEST_CONFIG_VERSION = (
    "market-research-rates-inflation-swap-breakout-digest-v0"
)

BREAKOUT_STATUSES = ("pass", "watch", "blocked")
ROW_REASON_CODES = (
    "rates_inflation_swap_breakout_blocked",
    "rates_inflation_swap_breakout_breakeven_premium",
    "rates_inflation_swap_breakout_consensus_gap",
    "rates_inflation_swap_breakout_inline",
    "rates_inflation_swap_breakout_momentum",
    "rates_inflation_swap_breakout_volume_confirmed",
    "rates_inflation_swap_breakout_watch",
)
REPORT_REASON_CODES = (
    "rates_inflation_swap_breakout_blocked_present",
    "rates_inflation_swap_breakout_momentum_present",
    "rates_inflation_swap_breakout_breakeven_premium_present",
    "rates_inflation_swap_breakout_consensus_gap_present",
    "rates_inflation_swap_breakout_volume_confirmed_present",
    "rates_inflation_swap_breakout_digest_clear",
    "rates_inflation_swap_breakout_digest_empty",
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
WATCH_RISK_SCORE = Decimal("0.500000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_RANK = {
    "blocked": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}
_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


__all__ = (
    "DEFAULT_RATES_INFLATION_SWAP_BREAKOUT_DIGEST_CONFIG_VERSION",
    "RatesInflationSwapBreakoutDigestConfig",
    "RatesInflationSwapBreakoutObservation",
    "RatesInflationSwapBreakoutDigestRow",
    "RatesInflationSwapBreakoutReasonCodeCount",
    "RatesInflationSwapBreakoutDigestReport",
    "build_market_research_rates_inflation_swap_breakout_digest",
    "market_research_rates_inflation_swap_breakout_digest_payload",
)


@dataclass(frozen=True)
class RatesInflationSwapBreakoutDigestConfig:
    config_version: str = DEFAULT_RATES_INFLATION_SWAP_BREAKOUT_DIGEST_CONFIG_VERSION
    watch_swap_change_bp: Decimal = Decimal("25.000000")
    blocked_swap_change_bp: Decimal = Decimal("40.000000")
    breakeven_premium_pct: Decimal = Decimal("0.250000")
    consensus_gap_pct: Decimal = Decimal("0.500000")
    volume_confirmation_usd_m: Decimal = Decimal("800.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, RatesInflationSwapBreakoutDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RATES_INFLATION_SWAP_BREAKOUT_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_swap_change_bp",
            "blocked_swap_change_bp",
            "breakeven_premium_pct",
            "consensus_gap_pct",
            "volume_confirmation_usd_m",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_swap_change_bp > self.blocked_swap_change_bp:
            raise ValueError("watch_swap_change_bp must not exceed blocked_swap_change_bp")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class RatesInflationSwapBreakoutObservation:
    source_id: str
    market_slug: str
    swap_tenor: str
    inflation_swap_rate_pct: Decimal
    prior_inflation_swap_rate_pct: Decimal
    breakeven_rate_pct: Decimal
    consensus_inflation_rate_pct: Decimal
    five_day_swap_change_bp: Decimal
    volume_notional_usd_m: Decimal
    data_timestamp: datetime
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, RatesInflationSwapBreakoutObservation, "observation")
        for field_name in ("source_id", "market_slug", "swap_tenor"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "inflation_swap_rate_pct",
            "prior_inflation_swap_rate_pct",
            "breakeven_rate_pct",
            "consensus_inflation_rate_pct",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "five_day_swap_change_bp",
            _require_nonnegative_decimal(
                "five_day_swap_change_bp",
                self.five_day_swap_change_bp,
            ),
        )
        object.__setattr__(
            self,
            "volume_notional_usd_m",
            _require_positive_decimal("volume_notional_usd_m", self.volume_notional_usd_m),
        )
        object.__setattr__(
            self,
            "data_timestamp",
            _as_utc("data_timestamp", self.data_timestamp),
        )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_open_reason_codes("upstream_reason_codes", self.upstream_reason_codes),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class RatesInflationSwapBreakoutDigestRow:
    source_id: str
    market_slug: str
    swap_tenor: str
    inflation_swap_rate_pct: Decimal
    prior_inflation_swap_rate_pct: Decimal
    swap_rate_delta_pct: Decimal
    breakeven_rate_pct: Decimal
    swap_breakeven_spread_pct: Decimal
    consensus_inflation_rate_pct: Decimal
    swap_consensus_gap_pct: Decimal
    five_day_swap_change_bp: Decimal
    volume_notional_usd_m: Decimal
    data_timestamp: datetime
    breakout_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, RatesInflationSwapBreakoutDigestRow, "row")
        for field_name in ("source_id", "market_slug", "swap_tenor"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "inflation_swap_rate_pct",
            "prior_inflation_swap_rate_pct",
            "swap_rate_delta_pct",
            "breakeven_rate_pct",
            "swap_breakeven_spread_pct",
            "consensus_inflation_rate_pct",
            "swap_consensus_gap_pct",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "five_day_swap_change_bp",
            _require_nonnegative_decimal(
                "five_day_swap_change_bp",
                self.five_day_swap_change_bp,
            ),
        )
        object.__setattr__(
            self,
            "volume_notional_usd_m",
            _require_positive_decimal("volume_notional_usd_m", self.volume_notional_usd_m),
        )
        object.__setattr__(
            self,
            "data_timestamp",
            _as_utc("data_timestamp", self.data_timestamp),
        )
        _require_member("breakout_status", self.breakout_status, BREAKOUT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class RatesInflationSwapBreakoutReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            RatesInflationSwapBreakoutReasonCodeCount,
            "reason code count",
        )
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODES)
        object.__setattr__(self, "count", _require_nonnegative_decimal("count", self.count))
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class RatesInflationSwapBreakoutDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    breakout_count: Decimal
    breakeven_premium_count: Decimal
    consensus_gap_count: Decimal
    volume_confirmation_count: Decimal
    max_swap_change_bp: Decimal
    average_swap_rate_pct: Decimal
    breakout_risk_score: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[RatesInflationSwapBreakoutDigestRow, ...]
    reason_code_counts: tuple[RatesInflationSwapBreakoutReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, RatesInflationSwapBreakoutDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RATES_INFLATION_SWAP_BREAKOUT_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "breakout_count",
            "breakeven_premium_count",
            "consensus_gap_count",
            "volume_confirmation_count",
            "max_swap_change_bp",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_swap_rate_pct",
            _require_decimal("average_swap_rate_pct", self.average_swap_rate_pct),
        )
        object.__setattr__(
            self,
            "breakout_risk_score",
            _require_ratio("breakout_risk_score", self.breakout_risk_score),
        )
        _require_member("digest_status", self.digest_status, BREAKOUT_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_rates_inflation_swap_breakout_digest(
    observations: Iterable[RatesInflationSwapBreakoutObservation],
    *,
    config: RatesInflationSwapBreakoutDigestConfig,
    generated_at: datetime,
) -> RatesInflationSwapBreakoutDigestReport:
    if type(config) is not RatesInflationSwapBreakoutDigestConfig:
        raise ValueError("config must be exactly RatesInflationSwapBreakoutDigestConfig")
    generated_at_utc = _as_utc("generated_at", generated_at)
    _require_hard_flags("config", config)
    normalized = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (
                _row_from_observation(observation, config=config)
                for observation in normalized
            ),
            key=_row_sort_key,
        ),
    )
    row_count = _count_decimal(len(rows))
    reason_codes = _report_reason_codes(rows)
    digest_status = _digest_status(rows)

    return RatesInflationSwapBreakoutDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=row_count,
        blocked_count=_status_count(rows, "blocked"),
        watch_count=_status_count(rows, "watch"),
        pass_count=_status_count(rows, "pass"),
        breakout_count=_reason_count(
            rows,
            "rates_inflation_swap_breakout_momentum",
        ),
        breakeven_premium_count=_reason_count(
            rows,
            "rates_inflation_swap_breakout_breakeven_premium",
        ),
        consensus_gap_count=_reason_count(
            rows,
            "rates_inflation_swap_breakout_consensus_gap",
        ),
        volume_confirmation_count=_reason_count(
            rows,
            "rates_inflation_swap_breakout_volume_confirmed",
        ),
        max_swap_change_bp=_max_row_decimal(rows, "five_day_swap_change_bp"),
        average_swap_rate_pct=_ratio(
            _sum_decimal(row.inflation_swap_rate_pct for row in rows),
            row_count,
        ),
        breakout_risk_score=_breakout_risk_score(rows),
        digest_status=digest_status,
        recommended_next_step=_recommended_next_step(digest_status),
        rows=rows,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        reason_codes=reason_codes,
    )


def market_research_rates_inflation_swap_breakout_digest_payload(
    report: RatesInflationSwapBreakoutDigestReport,
) -> dict[str, Any]:
    if type(report) is not RatesInflationSwapBreakoutDigestReport:
        raise ValueError("report must be exactly RatesInflationSwapBreakoutDigestReport")
    return _payload_value(report)


def _row_from_observation(
    observation: RatesInflationSwapBreakoutObservation,
    *,
    config: RatesInflationSwapBreakoutDigestConfig,
) -> RatesInflationSwapBreakoutDigestRow:
    swap_rate_delta_pct = _quantize_decimal(
        observation.inflation_swap_rate_pct - observation.prior_inflation_swap_rate_pct,
    )
    swap_breakeven_spread_pct = _quantize_decimal(
        observation.inflation_swap_rate_pct - observation.breakeven_rate_pct,
    )
    swap_consensus_gap_pct = _quantize_decimal(
        observation.inflation_swap_rate_pct - observation.consensus_inflation_rate_pct,
    )
    breakout_status = _breakout_status(
        observation,
        swap_breakeven_spread_pct=swap_breakeven_spread_pct,
        swap_consensus_gap_pct=swap_consensus_gap_pct,
        config=config,
    )
    return RatesInflationSwapBreakoutDigestRow(
        source_id=observation.source_id,
        market_slug=observation.market_slug,
        swap_tenor=observation.swap_tenor,
        inflation_swap_rate_pct=observation.inflation_swap_rate_pct,
        prior_inflation_swap_rate_pct=observation.prior_inflation_swap_rate_pct,
        swap_rate_delta_pct=swap_rate_delta_pct,
        breakeven_rate_pct=observation.breakeven_rate_pct,
        swap_breakeven_spread_pct=swap_breakeven_spread_pct,
        consensus_inflation_rate_pct=observation.consensus_inflation_rate_pct,
        swap_consensus_gap_pct=swap_consensus_gap_pct,
        five_day_swap_change_bp=observation.five_day_swap_change_bp,
        volume_notional_usd_m=observation.volume_notional_usd_m,
        data_timestamp=observation.data_timestamp,
        breakout_status=breakout_status,
        reason_codes=_row_reason_codes(
            observation,
            breakout_status=breakout_status,
            swap_breakeven_spread_pct=swap_breakeven_spread_pct,
            swap_consensus_gap_pct=swap_consensus_gap_pct,
            config=config,
        ),
    )


def _breakout_status(
    observation: RatesInflationSwapBreakoutObservation,
    *,
    swap_breakeven_spread_pct: Decimal,
    swap_consensus_gap_pct: Decimal,
    config: RatesInflationSwapBreakoutDigestConfig,
) -> str:
    momentum = observation.five_day_swap_change_bp >= config.watch_swap_change_bp
    blocked_momentum = (
        observation.five_day_swap_change_bp >= config.blocked_swap_change_bp
    )
    breakeven_premium = swap_breakeven_spread_pct >= config.breakeven_premium_pct
    consensus_gap = swap_consensus_gap_pct >= config.consensus_gap_pct
    volume_confirmed = (
        observation.volume_notional_usd_m >= config.volume_confirmation_usd_m
    )
    if blocked_momentum and breakeven_premium and consensus_gap and volume_confirmed:
        return "blocked"
    if momentum or breakeven_premium or consensus_gap:
        return "watch"
    return "pass"


def _row_reason_codes(
    observation: RatesInflationSwapBreakoutObservation,
    *,
    breakout_status: str,
    swap_breakeven_spread_pct: Decimal,
    swap_consensus_gap_pct: Decimal,
    config: RatesInflationSwapBreakoutDigestConfig,
) -> tuple[str, ...]:
    if breakout_status == "blocked":
        reason_codes = ["rates_inflation_swap_breakout_blocked"]
    elif breakout_status == "watch":
        reason_codes = ["rates_inflation_swap_breakout_watch"]
    else:
        reason_codes = ["rates_inflation_swap_breakout_inline"]

    if breakout_status != "pass":
        if observation.five_day_swap_change_bp >= config.watch_swap_change_bp:
            reason_codes.append("rates_inflation_swap_breakout_momentum")
        if swap_breakeven_spread_pct >= config.breakeven_premium_pct:
            reason_codes.append("rates_inflation_swap_breakout_breakeven_premium")
        if swap_consensus_gap_pct >= config.consensus_gap_pct:
            reason_codes.append("rates_inflation_swap_breakout_consensus_gap")
        if observation.volume_notional_usd_m >= config.volume_confirmation_usd_m:
            reason_codes.append("rates_inflation_swap_breakout_volume_confirmed")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), ROW_REASON_CODES)


def _report_reason_codes(
    rows: tuple[RatesInflationSwapBreakoutDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("rates_inflation_swap_breakout_digest_empty",)
    reason_codes: list[str] = []
    if any(row.breakout_status == "blocked" for row in rows):
        reason_codes.append("rates_inflation_swap_breakout_blocked_present")
    if _reason_count(rows, "rates_inflation_swap_breakout_momentum") > ZERO:
        reason_codes.append("rates_inflation_swap_breakout_momentum_present")
    if _reason_count(rows, "rates_inflation_swap_breakout_breakeven_premium") > ZERO:
        reason_codes.append("rates_inflation_swap_breakout_breakeven_premium_present")
    if _reason_count(rows, "rates_inflation_swap_breakout_consensus_gap") > ZERO:
        reason_codes.append("rates_inflation_swap_breakout_consensus_gap_present")
    if _reason_count(rows, "rates_inflation_swap_breakout_volume_confirmed") > ZERO:
        reason_codes.append("rates_inflation_swap_breakout_volume_confirmed_present")
    if not reason_codes:
        reason_codes.append("rates_inflation_swap_breakout_digest_clear")
    return tuple(reason for reason in REPORT_REASON_CODES if reason in reason_codes)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[RatesInflationSwapBreakoutDigestRow, ...],
) -> tuple[RatesInflationSwapBreakoutReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if reason_codes == ("rates_inflation_swap_breakout_digest_empty",):
        return (
            RatesInflationSwapBreakoutReasonCodeCount(
                reason_code="rates_inflation_swap_breakout_digest_empty",
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        RatesInflationSwapBreakoutReasonCodeCount(
            reason_code=reason_code,
            count=_report_reason_row_count(reason_code, rows),
            row_ratio=_ratio(_report_reason_row_count(reason_code, rows), row_count),
        )
        for reason_code in reason_codes
    )


def _report_reason_row_count(
    reason_code: str,
    rows: tuple[RatesInflationSwapBreakoutDigestRow, ...],
) -> Decimal:
    if reason_code == "rates_inflation_swap_breakout_blocked_present":
        return _status_count(rows, "blocked")
    row_reason_code = {
        "rates_inflation_swap_breakout_momentum_present": (
            "rates_inflation_swap_breakout_momentum"
        ),
        "rates_inflation_swap_breakout_breakeven_premium_present": (
            "rates_inflation_swap_breakout_breakeven_premium"
        ),
        "rates_inflation_swap_breakout_consensus_gap_present": (
            "rates_inflation_swap_breakout_consensus_gap"
        ),
        "rates_inflation_swap_breakout_volume_confirmed_present": (
            "rates_inflation_swap_breakout_volume_confirmed"
        ),
        "rates_inflation_swap_breakout_digest_clear": (
            "rates_inflation_swap_breakout_inline"
        ),
    }[reason_code]
    return _reason_count(rows, row_reason_code)


def _digest_status(rows: tuple[RatesInflationSwapBreakoutDigestRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.breakout_status == "blocked" for row in rows):
        return "blocked"
    if any(row.breakout_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _recommended_next_step(status: str) -> str:
    if status == "pass":
        return "allow_report_only_rates_inflation_swap_breakout_screening"
    if status == "watch":
        return "monitor_report_only_rates_inflation_swap_breakout_screening"
    return "block_report_only_rates_inflation_swap_breakout_screening"


def _breakout_risk_score(
    rows: tuple[RatesInflationSwapBreakoutDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    if _digest_status(rows) == "blocked":
        return ONE
    if _digest_status(rows) == "watch":
        return WATCH_RISK_SCORE
    return ZERO


def _validate_row(row: RatesInflationSwapBreakoutDigestRow) -> None:
    if row.swap_rate_delta_pct != _quantize_decimal(
        row.inflation_swap_rate_pct - row.prior_inflation_swap_rate_pct,
    ):
        raise ValueError("swap_rate_delta_pct must match inflation_swap_rate_pct")
    if row.swap_breakeven_spread_pct != _quantize_decimal(
        row.inflation_swap_rate_pct - row.breakeven_rate_pct,
    ):
        raise ValueError("swap_breakeven_spread_pct must match breakeven_rate_pct")
    if row.swap_consensus_gap_pct != _quantize_decimal(
        row.inflation_swap_rate_pct - row.consensus_inflation_rate_pct,
    ):
        raise ValueError("swap_consensus_gap_pct must match consensus_inflation_rate_pct")
    if row.breakout_status == "pass":
        if row.reason_codes != ("rates_inflation_swap_breakout_inline",):
            raise ValueError("reason_codes must match breakout_status")
        return
    if row.breakout_status == "watch":
        if "rates_inflation_swap_breakout_watch" not in row.reason_codes:
            raise ValueError("reason_codes must match breakout_status")
        if "rates_inflation_swap_breakout_blocked" in row.reason_codes:
            raise ValueError("reason_codes must match breakout_status")
    if row.breakout_status == "blocked":
        if "rates_inflation_swap_breakout_blocked" not in row.reason_codes:
            raise ValueError("reason_codes must match breakout_status")
        if "rates_inflation_swap_breakout_watch" in row.reason_codes:
            raise ValueError("reason_codes must match breakout_status")


def _validate_report(report: RatesInflationSwapBreakoutDigestReport) -> None:
    if report.row_count != _count_decimal(len(report.rows)):
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
    if report.breakout_count != _reason_count(
        report.rows,
        "rates_inflation_swap_breakout_momentum",
    ):
        raise ValueError("breakout_count must match rows")
    if report.breakeven_premium_count != _reason_count(
        report.rows,
        "rates_inflation_swap_breakout_breakeven_premium",
    ):
        raise ValueError("breakeven_premium_count must match rows")
    if report.consensus_gap_count != _reason_count(
        report.rows,
        "rates_inflation_swap_breakout_consensus_gap",
    ):
        raise ValueError("consensus_gap_count must match rows")
    if report.volume_confirmation_count != _reason_count(
        report.rows,
        "rates_inflation_swap_breakout_volume_confirmed",
    ):
        raise ValueError("volume_confirmation_count must match rows")
    if report.max_swap_change_bp != _max_row_decimal(
        report.rows,
        "five_day_swap_change_bp",
    ):
        raise ValueError("max_swap_change_bp must match rows")
    if report.average_swap_rate_pct != _ratio(
        _sum_decimal(row.inflation_swap_rate_pct for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_swap_rate_pct must match rows")
    if report.breakout_risk_score != _breakout_risk_score(report.rows):
        raise ValueError("breakout_risk_score must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, report.rows):
        raise ValueError("reason_code_counts must match reason_codes")


def _normalize_observations(
    observations: Iterable[RatesInflationSwapBreakoutObservation],
) -> tuple[RatesInflationSwapBreakoutObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError(
            "observations must contain RatesInflationSwapBreakoutObservation",
        )
    normalized = tuple(observations)
    seen_source_ids: set[str] = set()
    for observation in normalized:
        if type(observation) is not RatesInflationSwapBreakoutObservation:
            raise ValueError(
                "observations must contain RatesInflationSwapBreakoutObservation",
            )
        _require_hard_flags("observation", observation)
        if observation.source_id in seen_source_ids:
            raise ValueError("observations must not contain duplicate source_id values")
        seen_source_ids.add(observation.source_id)
    return normalized


def _normalize_rows(
    rows: Iterable[RatesInflationSwapBreakoutDigestRow],
) -> tuple[RatesInflationSwapBreakoutDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must contain RatesInflationSwapBreakoutDigestRow")
    normalized = tuple(rows)
    seen_source_ids: set[str] = set()
    for row in normalized:
        if type(row) is not RatesInflationSwapBreakoutDigestRow:
            raise ValueError("rows must contain RatesInflationSwapBreakoutDigestRow")
        _require_hard_flags("row", row)
        if row.source_id in seen_source_ids:
            raise ValueError("rows must not contain duplicate source_id values")
        seen_source_ids.add(row.source_id)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    values: Iterable[RatesInflationSwapBreakoutReasonCodeCount],
) -> tuple[RatesInflationSwapBreakoutReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError("reason_code_counts must contain reason code counts")
    normalized = tuple(values)
    for value in normalized:
        if type(value) is not RatesInflationSwapBreakoutReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain RatesInflationSwapBreakoutReasonCodeCount",
            )
        _require_hard_flags("reason code count", value)
    return tuple(
        sorted(normalized, key=lambda value: REPORT_REASON_CODES.index(value.reason_code)),
    )


def _normalize_open_reason_codes(
    field_name: str,
    values: Iterable[str],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError(f"{field_name} must contain reason code strings")
    normalized: list[str] = []
    for value in values:
        _require_canonical_string("reason_code", value)
        if value not in normalized:
            normalized.append(value)
    return tuple(sorted(normalized))


def _normalize_reason_codes(
    field_name: str,
    values: Iterable[str],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError(f"{field_name} must contain reason code strings")
    normalized = tuple(values)
    for value in normalized:
        _require_member("reason_code", value, allowed)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    return tuple(sorted(normalized, key=lambda value: allowed.index(value)))


def _row_sort_key(
    row: RatesInflationSwapBreakoutDigestRow,
) -> tuple[Decimal, Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.breakout_status],
        -row.five_day_swap_change_bp,
        -row.swap_breakeven_spread_pct,
        row.market_slug,
        row.source_id,
    )


def _status_count(
    rows: tuple[RatesInflationSwapBreakoutDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.breakout_status == status))


def _reason_count(
    rows: tuple[RatesInflationSwapBreakoutDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_row_decimal(
    rows: tuple[RatesInflationSwapBreakoutDigestRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
        total += value
    return _quantize_decimal(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(numerator / denominator)


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


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
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
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
    if isinstance(value, Decimal):
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    return value
