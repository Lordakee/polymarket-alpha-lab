"""Pure Phase 1 gold mint premium spread digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import re
from typing import Any


DEFAULT_GOLD_MINT_PREMIUM_SPREAD_DIGEST_CONFIG_VERSION = (
    "market-research-gold-mint-premium-spread-digest-v0"
)

SPREAD_STATUSES = ("pass", "watch", "blocked")
ROW_REASON_CODES = (
    "gold_mint_premium_low_confidence",
    "gold_mint_premium_low_inventory",
    "gold_mint_premium_primary_premium_elevated",
    "gold_mint_premium_primary_premium_extreme",
    "gold_mint_premium_spread_blocked",
    "gold_mint_premium_spread_extreme",
    "gold_mint_premium_spread_inline",
    "gold_mint_premium_spread_watch",
    "gold_mint_premium_spread_wide",
    "gold_mint_premium_stale_quote",
)
REPORT_REASON_CODES = (
    "gold_mint_premium_spread_blocked_present",
    "gold_mint_premium_spread_wide_present",
    "gold_mint_premium_primary_premium_elevated_present",
    "gold_mint_premium_low_inventory_present",
    "gold_mint_premium_stale_quote_present",
    "gold_mint_premium_low_confidence_present",
    "gold_mint_premium_spread_digest_clear",
    "gold_mint_premium_spread_digest_empty",
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
    "DEFAULT_GOLD_MINT_PREMIUM_SPREAD_DIGEST_CONFIG_VERSION",
    "GoldMintPremiumSpreadDigestConfig",
    "GoldMintPremiumSpreadObservation",
    "GoldMintPremiumSpreadDigestRow",
    "GoldMintPremiumSpreadReasonCodeCount",
    "GoldMintPremiumSpreadDigestReport",
    "build_market_research_gold_mint_premium_spread_digest",
    "market_research_gold_mint_premium_spread_digest_payload",
)


@dataclass(frozen=True)
class GoldMintPremiumSpreadDigestConfig:
    config_version: str = DEFAULT_GOLD_MINT_PREMIUM_SPREAD_DIGEST_CONFIG_VERSION
    watch_premium_spread_pct: Decimal = Decimal("5.000000")
    blocked_premium_spread_pct: Decimal = Decimal("10.000000")
    watch_primary_mint_premium_pct: Decimal = Decimal("12.000000")
    blocked_primary_mint_premium_pct: Decimal = Decimal("18.000000")
    low_inventory_units: Decimal = Decimal("1000.000000")
    stale_price_update_days: Decimal = Decimal("7.000000")
    low_confidence_score: Decimal = Decimal("0.550000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, GoldMintPremiumSpreadDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_GOLD_MINT_PREMIUM_SPREAD_DIGEST_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_premium_spread_pct",
            "blocked_premium_spread_pct",
            "watch_primary_mint_premium_pct",
            "blocked_primary_mint_premium_pct",
            "low_inventory_units",
            "stale_price_update_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "low_confidence_score",
            _require_ratio("low_confidence_score", self.low_confidence_score),
        )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class GoldMintPremiumSpreadObservation:
    source_id: str
    market_slug: str
    mint_product_id: str
    primary_mint_premium_pct: Decimal
    secondary_market_premium_pct: Decimal
    premium_spread_pct: Decimal
    available_inventory_units: Decimal
    days_since_last_mint_price_update: Decimal
    confidence_score: Decimal
    observed_at: datetime
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, GoldMintPremiumSpreadObservation, "observation")
        for field_name in ("source_id", "market_slug", "mint_product_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "primary_mint_premium_pct",
            "secondary_market_premium_pct",
            "available_inventory_units",
            "days_since_last_mint_price_update",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "premium_spread_pct",
            _require_decimal("premium_spread_pct", self.premium_spread_pct),
        )
        object.__setattr__(
            self,
            "confidence_score",
            _require_ratio("confidence_score", self.confidence_score),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_open_reason_codes("upstream_reason_codes", self.upstream_reason_codes),
        )
        _validate_premium_spread_identity(
            self.primary_mint_premium_pct,
            self.secondary_market_premium_pct,
            self.premium_spread_pct,
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class GoldMintPremiumSpreadDigestRow:
    source_id: str
    market_slug: str
    mint_product_id: str
    primary_mint_premium_pct: Decimal
    secondary_market_premium_pct: Decimal
    premium_spread_pct: Decimal
    available_inventory_units: Decimal
    days_since_last_mint_price_update: Decimal
    confidence_score: Decimal
    observed_at: datetime
    spread_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, GoldMintPremiumSpreadDigestRow, "row")
        for field_name in ("source_id", "market_slug", "mint_product_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "primary_mint_premium_pct",
            "secondary_market_premium_pct",
            "available_inventory_units",
            "days_since_last_mint_price_update",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "premium_spread_pct",
            _require_decimal("premium_spread_pct", self.premium_spread_pct),
        )
        object.__setattr__(
            self,
            "confidence_score",
            _require_ratio("confidence_score", self.confidence_score),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_member("spread_status", self.spread_status, SPREAD_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class GoldMintPremiumSpreadReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, GoldMintPremiumSpreadReasonCodeCount, "reason code count")
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODES)
        object.__setattr__(self, "count", _require_nonnegative_decimal("count", self.count))
        object.__setattr__(self, "row_ratio", _require_ratio("row_ratio", self.row_ratio))
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class GoldMintPremiumSpreadDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    wide_spread_count: Decimal
    elevated_mint_premium_count: Decimal
    low_inventory_count: Decimal
    stale_quote_count: Decimal
    low_confidence_count: Decimal
    max_premium_spread_pct: Decimal
    average_premium_spread_pct: Decimal
    max_primary_mint_premium_pct: Decimal
    mint_premium_spread_risk_score: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[GoldMintPremiumSpreadDigestRow, ...]
    reason_code_counts: tuple[GoldMintPremiumSpreadReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, GoldMintPremiumSpreadDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_GOLD_MINT_PREMIUM_SPREAD_DIGEST_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "wide_spread_count",
            "elevated_mint_premium_count",
            "low_inventory_count",
            "stale_quote_count",
            "low_confidence_count",
            "max_primary_mint_premium_pct",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_premium_spread_pct",
            "average_premium_spread_pct",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "mint_premium_spread_risk_score",
            _require_ratio(
                "mint_premium_spread_risk_score",
                self.mint_premium_spread_risk_score,
            ),
        )
        _require_member("digest_status", self.digest_status, SPREAD_STATUSES)
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


def build_market_research_gold_mint_premium_spread_digest(
    observations: Iterable[GoldMintPremiumSpreadObservation],
    *,
    config: GoldMintPremiumSpreadDigestConfig,
    generated_at: datetime,
) -> GoldMintPremiumSpreadDigestReport:
    if type(config) is not GoldMintPremiumSpreadDigestConfig:
        raise ValueError("config must be exactly GoldMintPremiumSpreadDigestConfig")
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
    reason_codes = _report_reason_codes(rows)
    digest_status = _digest_status(rows)
    row_count = _count_decimal(len(rows))

    return GoldMintPremiumSpreadDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=row_count,
        blocked_count=_status_count(rows, "blocked"),
        watch_count=_status_count(rows, "watch"),
        pass_count=_status_count(rows, "pass"),
        wide_spread_count=_any_reason_count(
            rows,
            (
                "gold_mint_premium_spread_wide",
                "gold_mint_premium_spread_extreme",
            ),
        ),
        elevated_mint_premium_count=_any_reason_count(
            rows,
            (
                "gold_mint_premium_primary_premium_elevated",
                "gold_mint_premium_primary_premium_extreme",
            ),
        ),
        low_inventory_count=_reason_count(rows, "gold_mint_premium_low_inventory"),
        stale_quote_count=_reason_count(rows, "gold_mint_premium_stale_quote"),
        low_confidence_count=_reason_count(rows, "gold_mint_premium_low_confidence"),
        max_premium_spread_pct=_max_row_decimal(rows, "premium_spread_pct"),
        average_premium_spread_pct=_ratio(
            _sum_decimal(row.premium_spread_pct for row in rows),
            row_count,
        ),
        max_primary_mint_premium_pct=_max_row_decimal(rows, "primary_mint_premium_pct"),
        mint_premium_spread_risk_score=_mint_premium_spread_risk_score(rows),
        digest_status=digest_status,
        recommended_next_step=_recommended_next_step(digest_status),
        rows=rows,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        reason_codes=reason_codes,
    )


def market_research_gold_mint_premium_spread_digest_payload(
    report: GoldMintPremiumSpreadDigestReport,
) -> dict[str, Any]:
    if type(report) is not GoldMintPremiumSpreadDigestReport:
        raise ValueError("report must be exactly GoldMintPremiumSpreadDigestReport")
    return _payload_value(report)


def _row_from_observation(
    observation: GoldMintPremiumSpreadObservation,
    *,
    config: GoldMintPremiumSpreadDigestConfig,
) -> GoldMintPremiumSpreadDigestRow:
    spread_status = _spread_status(observation, config=config)
    return GoldMintPremiumSpreadDigestRow(
        source_id=observation.source_id,
        market_slug=observation.market_slug,
        mint_product_id=observation.mint_product_id,
        primary_mint_premium_pct=observation.primary_mint_premium_pct,
        secondary_market_premium_pct=observation.secondary_market_premium_pct,
        premium_spread_pct=observation.premium_spread_pct,
        available_inventory_units=observation.available_inventory_units,
        days_since_last_mint_price_update=observation.days_since_last_mint_price_update,
        confidence_score=observation.confidence_score,
        observed_at=observation.observed_at,
        spread_status=spread_status,
        reason_codes=_row_reason_codes(
            observation,
            spread_status=spread_status,
            config=config,
        ),
    )


def _spread_status(
    observation: GoldMintPremiumSpreadObservation,
    *,
    config: GoldMintPremiumSpreadDigestConfig,
) -> str:
    extreme_spread = observation.premium_spread_pct >= config.blocked_premium_spread_pct
    extreme_primary = (
        observation.primary_mint_premium_pct >= config.blocked_primary_mint_premium_pct
    )
    low_inventory = observation.available_inventory_units <= config.low_inventory_units
    if (
        (extreme_spread and (extreme_primary or low_inventory))
        or (extreme_primary and low_inventory)
    ):
        return "blocked"
    if (
        observation.premium_spread_pct >= config.watch_premium_spread_pct
        or observation.primary_mint_premium_pct >= config.watch_primary_mint_premium_pct
        or low_inventory
        or observation.days_since_last_mint_price_update >= config.stale_price_update_days
        or observation.confidence_score <= config.low_confidence_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    observation: GoldMintPremiumSpreadObservation,
    *,
    spread_status: str,
    config: GoldMintPremiumSpreadDigestConfig,
) -> tuple[str, ...]:
    if spread_status == "blocked":
        reason_codes = ["gold_mint_premium_spread_blocked"]
    elif spread_status == "watch":
        reason_codes = ["gold_mint_premium_spread_watch"]
    else:
        reason_codes = ["gold_mint_premium_spread_inline"]

    if spread_status != "pass":
        if observation.premium_spread_pct >= config.blocked_premium_spread_pct:
            reason_codes.append("gold_mint_premium_spread_extreme")
        elif observation.premium_spread_pct >= config.watch_premium_spread_pct:
            reason_codes.append("gold_mint_premium_spread_wide")
        if (
            observation.primary_mint_premium_pct
            >= config.blocked_primary_mint_premium_pct
        ):
            reason_codes.append("gold_mint_premium_primary_premium_extreme")
        elif (
            observation.primary_mint_premium_pct
            >= config.watch_primary_mint_premium_pct
        ):
            reason_codes.append("gold_mint_premium_primary_premium_elevated")
        if observation.available_inventory_units <= config.low_inventory_units:
            reason_codes.append("gold_mint_premium_low_inventory")
        if observation.days_since_last_mint_price_update >= config.stale_price_update_days:
            reason_codes.append("gold_mint_premium_stale_quote")
        if observation.confidence_score <= config.low_confidence_score:
            reason_codes.append("gold_mint_premium_low_confidence")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), ROW_REASON_CODES)


def _report_reason_codes(
    rows: tuple[GoldMintPremiumSpreadDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("gold_mint_premium_spread_digest_empty",)
    reason_codes: list[str] = []
    if any(row.spread_status == "blocked" for row in rows):
        reason_codes.append("gold_mint_premium_spread_blocked_present")
    if _any_reason_count(
        rows,
        (
            "gold_mint_premium_spread_wide",
            "gold_mint_premium_spread_extreme",
        ),
    ) > ZERO:
        reason_codes.append("gold_mint_premium_spread_wide_present")
    if _any_reason_count(
        rows,
        (
            "gold_mint_premium_primary_premium_elevated",
            "gold_mint_premium_primary_premium_extreme",
        ),
    ) > ZERO:
        reason_codes.append("gold_mint_premium_primary_premium_elevated_present")
    if _reason_count(rows, "gold_mint_premium_low_inventory") > ZERO:
        reason_codes.append("gold_mint_premium_low_inventory_present")
    if _reason_count(rows, "gold_mint_premium_stale_quote") > ZERO:
        reason_codes.append("gold_mint_premium_stale_quote_present")
    if _reason_count(rows, "gold_mint_premium_low_confidence") > ZERO:
        reason_codes.append("gold_mint_premium_low_confidence_present")
    if not reason_codes:
        reason_codes.append("gold_mint_premium_spread_digest_clear")
    return tuple(reason for reason in REPORT_REASON_CODES if reason in reason_codes)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[GoldMintPremiumSpreadDigestRow, ...],
) -> tuple[GoldMintPremiumSpreadReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if reason_codes == ("gold_mint_premium_spread_digest_empty",):
        return (
            GoldMintPremiumSpreadReasonCodeCount(
                reason_code="gold_mint_premium_spread_digest_empty",
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        GoldMintPremiumSpreadReasonCodeCount(
            reason_code=reason_code,
            count=_report_reason_row_count(reason_code, rows),
            row_ratio=_ratio(_report_reason_row_count(reason_code, rows), row_count),
        )
        for reason_code in reason_codes
    )


def _report_reason_row_count(
    reason_code: str,
    rows: tuple[GoldMintPremiumSpreadDigestRow, ...],
) -> Decimal:
    if reason_code == "gold_mint_premium_spread_blocked_present":
        return _status_count(rows, "blocked")
    if reason_code == "gold_mint_premium_spread_wide_present":
        return _any_reason_count(
            rows,
            (
                "gold_mint_premium_spread_wide",
                "gold_mint_premium_spread_extreme",
            ),
        )
    if reason_code == "gold_mint_premium_primary_premium_elevated_present":
        return _any_reason_count(
            rows,
            (
                "gold_mint_premium_primary_premium_elevated",
                "gold_mint_premium_primary_premium_extreme",
            ),
        )
    if reason_code == "gold_mint_premium_low_inventory_present":
        return _reason_count(rows, "gold_mint_premium_low_inventory")
    if reason_code == "gold_mint_premium_stale_quote_present":
        return _reason_count(rows, "gold_mint_premium_stale_quote")
    if reason_code == "gold_mint_premium_low_confidence_present":
        return _reason_count(rows, "gold_mint_premium_low_confidence")
    return _reason_count(rows, "gold_mint_premium_spread_inline")


def _digest_status(rows: tuple[GoldMintPremiumSpreadDigestRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.spread_status == "blocked" for row in rows):
        return "blocked"
    if any(row.spread_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _recommended_next_step(status: str) -> str:
    if status == "pass":
        return "allow_report_only_gold_mint_premium_spread_screening"
    if status == "watch":
        return "monitor_report_only_gold_mint_premium_spread_screening"
    return "block_report_only_gold_mint_premium_spread_screening"


def _mint_premium_spread_risk_score(
    rows: tuple[GoldMintPremiumSpreadDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    if _digest_status(rows) == "blocked":
        return ONE
    if _digest_status(rows) == "watch":
        return WATCH_RISK_SCORE
    return ZERO


def _validate_config(config: GoldMintPremiumSpreadDigestConfig) -> None:
    if config.blocked_premium_spread_pct < config.watch_premium_spread_pct:
        raise ValueError(
            "blocked_premium_spread_pct must be at least watch_premium_spread_pct",
        )
    if (
        config.blocked_primary_mint_premium_pct
        < config.watch_primary_mint_premium_pct
    ):
        raise ValueError(
            "blocked_primary_mint_premium_pct must be at least "
            "watch_primary_mint_premium_pct",
        )


def _validate_premium_spread_identity(
    primary_mint_premium_pct: Decimal,
    secondary_market_premium_pct: Decimal,
    premium_spread_pct: Decimal,
) -> None:
    if _quantize_decimal(primary_mint_premium_pct - secondary_market_premium_pct) != (
        premium_spread_pct
    ):
        raise ValueError(
            "premium_spread_pct must equal primary_mint_premium_pct less "
            "secondary_market_premium_pct",
        )


def _validate_row(row: GoldMintPremiumSpreadDigestRow) -> None:
    _validate_premium_spread_identity(
        row.primary_mint_premium_pct,
        row.secondary_market_premium_pct,
        row.premium_spread_pct,
    )
    if row.spread_status == "pass":
        if row.reason_codes != ("gold_mint_premium_spread_inline",):
            raise ValueError("reason_codes must match spread_status")
        return
    if row.spread_status == "watch":
        if "gold_mint_premium_spread_watch" not in row.reason_codes:
            raise ValueError("reason_codes must match spread_status")
        if "gold_mint_premium_spread_blocked" in row.reason_codes:
            raise ValueError("reason_codes must match spread_status")
        if "gold_mint_premium_spread_inline" in row.reason_codes:
            raise ValueError("reason_codes must match spread_status")
    if row.spread_status == "blocked":
        if "gold_mint_premium_spread_blocked" not in row.reason_codes:
            raise ValueError("reason_codes must match spread_status")
        if "gold_mint_premium_spread_watch" in row.reason_codes:
            raise ValueError("reason_codes must match spread_status")
        if "gold_mint_premium_spread_inline" in row.reason_codes:
            raise ValueError("reason_codes must match spread_status")


def _validate_report(report: GoldMintPremiumSpreadDigestReport) -> None:
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
    if report.wide_spread_count != _any_reason_count(
        report.rows,
        (
            "gold_mint_premium_spread_wide",
            "gold_mint_premium_spread_extreme",
        ),
    ):
        raise ValueError("wide_spread_count must match rows")
    if report.elevated_mint_premium_count != _any_reason_count(
        report.rows,
        (
            "gold_mint_premium_primary_premium_elevated",
            "gold_mint_premium_primary_premium_extreme",
        ),
    ):
        raise ValueError("elevated_mint_premium_count must match rows")
    if report.low_inventory_count != _reason_count(
        report.rows,
        "gold_mint_premium_low_inventory",
    ):
        raise ValueError("low_inventory_count must match rows")
    if report.stale_quote_count != _reason_count(
        report.rows,
        "gold_mint_premium_stale_quote",
    ):
        raise ValueError("stale_quote_count must match rows")
    if report.low_confidence_count != _reason_count(
        report.rows,
        "gold_mint_premium_low_confidence",
    ):
        raise ValueError("low_confidence_count must match rows")
    if report.max_premium_spread_pct != _max_row_decimal(
        report.rows,
        "premium_spread_pct",
    ):
        raise ValueError("max_premium_spread_pct must match rows")
    if report.average_premium_spread_pct != _ratio(
        _sum_decimal(row.premium_spread_pct for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_premium_spread_pct must match rows")
    if report.max_primary_mint_premium_pct != _max_row_decimal(
        report.rows,
        "primary_mint_premium_pct",
    ):
        raise ValueError("max_primary_mint_premium_pct must match rows")
    if report.mint_premium_spread_risk_score != _mint_premium_spread_risk_score(
        report.rows,
    ):
        raise ValueError("mint_premium_spread_risk_score must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, report.rows):
        raise ValueError("reason_code_counts must match reason_codes")


def _normalize_observations(
    observations: Iterable[GoldMintPremiumSpreadObservation],
) -> tuple[GoldMintPremiumSpreadObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must contain GoldMintPremiumSpreadObservation")
    normalized = tuple(observations)
    seen_source_ids: set[str] = set()
    for observation in normalized:
        if type(observation) is not GoldMintPremiumSpreadObservation:
            raise ValueError("observations must contain GoldMintPremiumSpreadObservation")
        _require_hard_flags("observation", observation)
        if observation.source_id in seen_source_ids:
            raise ValueError("observations must not contain duplicate source_id values")
        seen_source_ids.add(observation.source_id)
    return normalized


def _normalize_rows(
    rows: Iterable[GoldMintPremiumSpreadDigestRow],
) -> tuple[GoldMintPremiumSpreadDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must contain GoldMintPremiumSpreadDigestRow")
    normalized = tuple(rows)
    seen_source_ids: set[str] = set()
    for row in normalized:
        if type(row) is not GoldMintPremiumSpreadDigestRow:
            raise ValueError("rows must contain GoldMintPremiumSpreadDigestRow")
        _require_hard_flags("row", row)
        if row.source_id in seen_source_ids:
            raise ValueError("rows must not contain duplicate source_id values")
        seen_source_ids.add(row.source_id)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    values: Iterable[GoldMintPremiumSpreadReasonCodeCount],
) -> tuple[GoldMintPremiumSpreadReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError("reason_code_counts must contain reason code counts")
    normalized = tuple(values)
    for value in normalized:
        if type(value) is not GoldMintPremiumSpreadReasonCodeCount:
            raise ValueError("reason_code_counts must contain GoldMintPremiumSpreadReasonCodeCount")
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
    row: GoldMintPremiumSpreadDigestRow,
) -> tuple[Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.spread_status],
        -row.premium_spread_pct,
        row.market_slug,
        row.source_id,
    )


def _status_count(
    rows: tuple[GoldMintPremiumSpreadDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.spread_status == status))


def _reason_count(
    rows: tuple[GoldMintPremiumSpreadDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _any_reason_count(
    rows: tuple[GoldMintPremiumSpreadDigestRow, ...],
    reason_codes: tuple[str, ...],
) -> Decimal:
    return _count_decimal(
        sum(1 for row in rows if any(reason in row.reason_codes for reason in reason_codes)),
    )


def _max_row_decimal(
    rows: tuple[GoldMintPremiumSpreadDigestRow, ...],
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
