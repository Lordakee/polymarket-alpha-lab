"""Pure Phase 1 gold CFTC managed-money squeeze risk digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import re
from typing import Any


DEFAULT_GOLD_CFTC_MANAGED_MONEY_SQUEEZE_DIGEST_CONFIG_VERSION = (
    "market-research-gold-cftc-managed-money-squeeze-digest-v0"
)

SQUEEZE_STATUSES = ("pass", "watch", "blocked")
ROW_REASON_CODES = (
    "gold_cftc_managed_money_crowded_short",
    "gold_cftc_managed_money_four_week_rally",
    "gold_cftc_managed_money_high_short_open_interest",
    "gold_cftc_managed_money_inline",
    "gold_cftc_managed_money_price_rally",
    "gold_cftc_managed_money_short_squeeze_blocked",
    "gold_cftc_managed_money_short_squeeze_watch",
)
REPORT_REASON_CODES = (
    "gold_cftc_managed_money_squeeze_blocked_present",
    "gold_cftc_managed_money_crowded_short_present",
    "gold_cftc_managed_money_price_rally_present",
    "gold_cftc_managed_money_high_short_open_interest_present",
    "gold_cftc_managed_money_squeeze_digest_clear",
    "gold_cftc_managed_money_squeeze_digest_empty",
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
    "DEFAULT_GOLD_CFTC_MANAGED_MONEY_SQUEEZE_DIGEST_CONFIG_VERSION",
    "GoldCftcManagedMoneySqueezeDigestConfig",
    "GoldCftcManagedMoneySqueezeObservation",
    "GoldCftcManagedMoneySqueezeDigestRow",
    "GoldCftcManagedMoneySqueezeReasonCodeCount",
    "GoldCftcManagedMoneySqueezeDigestReport",
    "build_market_research_gold_cftc_managed_money_squeeze_digest",
    "market_research_gold_cftc_managed_money_squeeze_digest_payload",
)


@dataclass(frozen=True)
class GoldCftcManagedMoneySqueezeDigestConfig:
    config_version: str = DEFAULT_GOLD_CFTC_MANAGED_MONEY_SQUEEZE_DIGEST_CONFIG_VERSION
    watch_net_position_percentile: Decimal = Decimal("0.200000")
    blocked_net_position_percentile: Decimal = Decimal("0.100000")
    weekly_rally_confirmation_pct: Decimal = Decimal("2.000000")
    four_week_rally_confirmation_pct: Decimal = Decimal("5.000000")
    high_short_open_interest_share: Decimal = Decimal("0.350000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, GoldCftcManagedMoneySqueezeDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_GOLD_CFTC_MANAGED_MONEY_SQUEEZE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_net_position_percentile",
            "blocked_net_position_percentile",
            "high_short_open_interest_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "weekly_rally_confirmation_pct",
            "four_week_rally_confirmation_pct",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.blocked_net_position_percentile > self.watch_net_position_percentile:
            raise ValueError(
                "blocked_net_position_percentile must not exceed "
                "watch_net_position_percentile",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class GoldCftcManagedMoneySqueezeObservation:
    source_id: str
    market_slug: str
    managed_money_long_contracts: Decimal
    managed_money_short_contracts: Decimal
    managed_money_net_contracts: Decimal
    open_interest_contracts: Decimal
    net_position_percentile: Decimal
    weekly_gold_return_pct: Decimal
    four_week_gold_return_pct: Decimal
    data_timestamp: datetime
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, GoldCftcManagedMoneySqueezeObservation, "observation")
        for field_name in ("source_id", "market_slug"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "managed_money_long_contracts",
            "managed_money_short_contracts",
            "open_interest_contracts",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "managed_money_net_contracts",
            "weekly_gold_return_pct",
            "four_week_gold_return_pct",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "net_position_percentile",
            _require_ratio("net_position_percentile", self.net_position_percentile),
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
        _validate_position_identity(
            self.managed_money_long_contracts,
            self.managed_money_short_contracts,
            self.managed_money_net_contracts,
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class GoldCftcManagedMoneySqueezeDigestRow:
    source_id: str
    market_slug: str
    managed_money_long_contracts: Decimal
    managed_money_short_contracts: Decimal
    managed_money_net_contracts: Decimal
    open_interest_contracts: Decimal
    net_position_share: Decimal
    short_open_interest_share: Decimal
    net_position_percentile: Decimal
    weekly_gold_return_pct: Decimal
    four_week_gold_return_pct: Decimal
    data_timestamp: datetime
    squeeze_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, GoldCftcManagedMoneySqueezeDigestRow, "row")
        for field_name in ("source_id", "market_slug"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "managed_money_long_contracts",
            "managed_money_short_contracts",
            "open_interest_contracts",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "managed_money_net_contracts",
            "weekly_gold_return_pct",
            "four_week_gold_return_pct",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "net_position_share",
            "short_open_interest_share",
            "net_position_percentile",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_or_signed_share(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "net_position_percentile",
            _require_ratio("net_position_percentile", self.net_position_percentile),
        )
        object.__setattr__(
            self,
            "data_timestamp",
            _as_utc("data_timestamp", self.data_timestamp),
        )
        _require_member("squeeze_status", self.squeeze_status, SQUEEZE_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class GoldCftcManagedMoneySqueezeReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            GoldCftcManagedMoneySqueezeReasonCodeCount,
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
class GoldCftcManagedMoneySqueezeDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    crowded_short_count: Decimal
    rally_confirmation_count: Decimal
    high_short_open_interest_count: Decimal
    max_short_open_interest_share: Decimal
    average_short_open_interest_share: Decimal
    squeeze_risk_score: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[GoldCftcManagedMoneySqueezeDigestRow, ...]
    reason_code_counts: tuple[GoldCftcManagedMoneySqueezeReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, GoldCftcManagedMoneySqueezeDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_GOLD_CFTC_MANAGED_MONEY_SQUEEZE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "crowded_short_count",
            "rally_confirmation_count",
            "high_short_open_interest_count",
            "max_short_open_interest_share",
            "average_short_open_interest_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "squeeze_risk_score",
            _require_ratio("squeeze_risk_score", self.squeeze_risk_score),
        )
        _require_member("digest_status", self.digest_status, SQUEEZE_STATUSES)
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


def build_market_research_gold_cftc_managed_money_squeeze_digest(
    observations: Iterable[GoldCftcManagedMoneySqueezeObservation],
    *,
    config: GoldCftcManagedMoneySqueezeDigestConfig,
    generated_at: datetime,
) -> GoldCftcManagedMoneySqueezeDigestReport:
    if type(config) is not GoldCftcManagedMoneySqueezeDigestConfig:
        raise ValueError("config must be exactly GoldCftcManagedMoneySqueezeDigestConfig")
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

    return GoldCftcManagedMoneySqueezeDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=row_count,
        blocked_count=_status_count(rows, "blocked"),
        watch_count=_status_count(rows, "watch"),
        pass_count=_status_count(rows, "pass"),
        crowded_short_count=_reason_count(
            rows,
            "gold_cftc_managed_money_crowded_short",
        ),
        rally_confirmation_count=_any_reason_count(
            rows,
            (
                "gold_cftc_managed_money_price_rally",
                "gold_cftc_managed_money_four_week_rally",
            ),
        ),
        high_short_open_interest_count=_reason_count(
            rows,
            "gold_cftc_managed_money_high_short_open_interest",
        ),
        max_short_open_interest_share=_max_row_decimal(
            rows,
            "short_open_interest_share",
        ),
        average_short_open_interest_share=_ratio(
            _sum_decimal(row.short_open_interest_share for row in rows),
            row_count,
        ),
        squeeze_risk_score=_squeeze_risk_score(rows),
        digest_status=digest_status,
        recommended_next_step=_recommended_next_step(digest_status),
        rows=rows,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        reason_codes=reason_codes,
    )


def market_research_gold_cftc_managed_money_squeeze_digest_payload(
    report: GoldCftcManagedMoneySqueezeDigestReport,
) -> dict[str, Any]:
    if type(report) is not GoldCftcManagedMoneySqueezeDigestReport:
        raise ValueError("report must be exactly GoldCftcManagedMoneySqueezeDigestReport")
    return _payload_value(report)


def _row_from_observation(
    observation: GoldCftcManagedMoneySqueezeObservation,
    *,
    config: GoldCftcManagedMoneySqueezeDigestConfig,
) -> GoldCftcManagedMoneySqueezeDigestRow:
    net_position_share = _ratio(
        observation.managed_money_net_contracts,
        observation.open_interest_contracts,
    )
    short_open_interest_share = _ratio(
        observation.managed_money_short_contracts,
        observation.open_interest_contracts,
    )
    squeeze_status = _squeeze_status(
        observation,
        short_open_interest_share=short_open_interest_share,
        config=config,
    )
    return GoldCftcManagedMoneySqueezeDigestRow(
        source_id=observation.source_id,
        market_slug=observation.market_slug,
        managed_money_long_contracts=observation.managed_money_long_contracts,
        managed_money_short_contracts=observation.managed_money_short_contracts,
        managed_money_net_contracts=observation.managed_money_net_contracts,
        open_interest_contracts=observation.open_interest_contracts,
        net_position_share=net_position_share,
        short_open_interest_share=short_open_interest_share,
        net_position_percentile=observation.net_position_percentile,
        weekly_gold_return_pct=observation.weekly_gold_return_pct,
        four_week_gold_return_pct=observation.four_week_gold_return_pct,
        data_timestamp=observation.data_timestamp,
        squeeze_status=squeeze_status,
        reason_codes=_row_reason_codes(
            observation,
            squeeze_status=squeeze_status,
            short_open_interest_share=short_open_interest_share,
            config=config,
        ),
    )


def _squeeze_status(
    observation: GoldCftcManagedMoneySqueezeObservation,
    *,
    short_open_interest_share: Decimal,
    config: GoldCftcManagedMoneySqueezeDigestConfig,
) -> str:
    crowded_short = _is_crowded_short(observation, config=config)
    rally_confirmed = _has_rally_confirmation(observation, config=config)
    high_short_share = short_open_interest_share >= config.high_short_open_interest_share
    if (
        observation.managed_money_net_contracts < ZERO
        and observation.net_position_percentile <= config.blocked_net_position_percentile
        and rally_confirmed
        and high_short_share
    ):
        return "blocked"
    if crowded_short or (rally_confirmed and high_short_share):
        return "watch"
    return "pass"


def _row_reason_codes(
    observation: GoldCftcManagedMoneySqueezeObservation,
    *,
    squeeze_status: str,
    short_open_interest_share: Decimal,
    config: GoldCftcManagedMoneySqueezeDigestConfig,
) -> tuple[str, ...]:
    if squeeze_status == "blocked":
        reason_codes = ["gold_cftc_managed_money_short_squeeze_blocked"]
    elif squeeze_status == "watch":
        reason_codes = ["gold_cftc_managed_money_short_squeeze_watch"]
    else:
        reason_codes = ["gold_cftc_managed_money_inline"]

    if squeeze_status != "pass" and _is_crowded_short(observation, config=config):
        reason_codes.append("gold_cftc_managed_money_crowded_short")
    if (
        squeeze_status != "pass"
        and observation.weekly_gold_return_pct >= config.weekly_rally_confirmation_pct
    ):
        reason_codes.append("gold_cftc_managed_money_price_rally")
    if (
        squeeze_status != "pass"
        and observation.four_week_gold_return_pct >= config.four_week_rally_confirmation_pct
    ):
        reason_codes.append("gold_cftc_managed_money_four_week_rally")
    if squeeze_status != "pass" and (
        short_open_interest_share >= config.high_short_open_interest_share
    ):
        reason_codes.append("gold_cftc_managed_money_high_short_open_interest")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), ROW_REASON_CODES)


def _report_reason_codes(
    rows: tuple[GoldCftcManagedMoneySqueezeDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("gold_cftc_managed_money_squeeze_digest_empty",)
    reason_codes: list[str] = []
    if any(row.squeeze_status == "blocked" for row in rows):
        reason_codes.append("gold_cftc_managed_money_squeeze_blocked_present")
    if _reason_count(rows, "gold_cftc_managed_money_crowded_short") > ZERO:
        reason_codes.append("gold_cftc_managed_money_crowded_short_present")
    if _any_reason_count(
        rows,
        (
            "gold_cftc_managed_money_price_rally",
            "gold_cftc_managed_money_four_week_rally",
        ),
    ) > ZERO:
        reason_codes.append("gold_cftc_managed_money_price_rally_present")
    if _reason_count(rows, "gold_cftc_managed_money_high_short_open_interest") > ZERO:
        reason_codes.append("gold_cftc_managed_money_high_short_open_interest_present")
    if not reason_codes:
        reason_codes.append("gold_cftc_managed_money_squeeze_digest_clear")
    return tuple(reason for reason in REPORT_REASON_CODES if reason in reason_codes)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[GoldCftcManagedMoneySqueezeDigestRow, ...],
) -> tuple[GoldCftcManagedMoneySqueezeReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if reason_codes == ("gold_cftc_managed_money_squeeze_digest_empty",):
        return (
            GoldCftcManagedMoneySqueezeReasonCodeCount(
                reason_code="gold_cftc_managed_money_squeeze_digest_empty",
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        GoldCftcManagedMoneySqueezeReasonCodeCount(
            reason_code=reason_code,
            count=_report_reason_row_count(reason_code, rows),
            row_ratio=_ratio(_report_reason_row_count(reason_code, rows), row_count),
        )
        for reason_code in reason_codes
    )


def _report_reason_row_count(
    reason_code: str,
    rows: tuple[GoldCftcManagedMoneySqueezeDigestRow, ...],
) -> Decimal:
    if reason_code == "gold_cftc_managed_money_squeeze_blocked_present":
        return _status_count(rows, "blocked")
    if reason_code == "gold_cftc_managed_money_crowded_short_present":
        return _reason_count(rows, "gold_cftc_managed_money_crowded_short")
    if reason_code == "gold_cftc_managed_money_price_rally_present":
        return _any_reason_count(
            rows,
            (
                "gold_cftc_managed_money_price_rally",
                "gold_cftc_managed_money_four_week_rally",
            ),
        )
    if reason_code == "gold_cftc_managed_money_high_short_open_interest_present":
        return _reason_count(
            rows,
            "gold_cftc_managed_money_high_short_open_interest",
        )
    return _reason_count(rows, "gold_cftc_managed_money_inline")


def _digest_status(rows: tuple[GoldCftcManagedMoneySqueezeDigestRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.squeeze_status == "blocked" for row in rows):
        return "blocked"
    if any(row.squeeze_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _recommended_next_step(status: str) -> str:
    if status == "pass":
        return "allow_report_only_gold_cftc_managed_money_squeeze_screening"
    if status == "watch":
        return "monitor_report_only_gold_cftc_managed_money_squeeze_screening"
    return "block_report_only_gold_cftc_managed_money_squeeze_screening"


def _squeeze_risk_score(rows: tuple[GoldCftcManagedMoneySqueezeDigestRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    if _digest_status(rows) == "blocked":
        return ONE
    if _digest_status(rows) == "watch":
        return WATCH_RISK_SCORE
    return ZERO


def _is_crowded_short(
    observation: GoldCftcManagedMoneySqueezeObservation,
    *,
    config: GoldCftcManagedMoneySqueezeDigestConfig,
) -> bool:
    return (
        observation.managed_money_net_contracts < ZERO
        and observation.net_position_percentile <= config.watch_net_position_percentile
    )


def _has_rally_confirmation(
    observation: GoldCftcManagedMoneySqueezeObservation,
    *,
    config: GoldCftcManagedMoneySqueezeDigestConfig,
) -> bool:
    return (
        observation.weekly_gold_return_pct >= config.weekly_rally_confirmation_pct
        or observation.four_week_gold_return_pct >= config.four_week_rally_confirmation_pct
    )


def _validate_position_identity(
    long_contracts: Decimal,
    short_contracts: Decimal,
    net_contracts: Decimal,
) -> None:
    if _quantize_decimal(long_contracts - short_contracts) != net_contracts:
        raise ValueError(
            "managed_money_net_contracts must equal "
            "managed_money_long_contracts minus managed_money_short_contracts",
        )


def _validate_row(row: GoldCftcManagedMoneySqueezeDigestRow) -> None:
    _validate_position_identity(
        row.managed_money_long_contracts,
        row.managed_money_short_contracts,
        row.managed_money_net_contracts,
    )
    if row.net_position_share != _ratio(
        row.managed_money_net_contracts,
        row.open_interest_contracts,
    ):
        raise ValueError("net_position_share must match managed_money_net_contracts")
    if row.short_open_interest_share != _ratio(
        row.managed_money_short_contracts,
        row.open_interest_contracts,
    ):
        raise ValueError(
            "short_open_interest_share must match managed_money_short_contracts",
        )
    if row.squeeze_status == "pass":
        if row.reason_codes != ("gold_cftc_managed_money_inline",):
            raise ValueError("reason_codes must match squeeze_status")
        return
    if row.squeeze_status == "watch":
        if "gold_cftc_managed_money_short_squeeze_watch" not in row.reason_codes:
            raise ValueError("reason_codes must match squeeze_status")
        if "gold_cftc_managed_money_short_squeeze_blocked" in row.reason_codes:
            raise ValueError("reason_codes must match squeeze_status")
    if row.squeeze_status == "blocked":
        if "gold_cftc_managed_money_short_squeeze_blocked" not in row.reason_codes:
            raise ValueError("reason_codes must match squeeze_status")
        if "gold_cftc_managed_money_short_squeeze_watch" in row.reason_codes:
            raise ValueError("reason_codes must match squeeze_status")


def _validate_report(report: GoldCftcManagedMoneySqueezeDigestReport) -> None:
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
    if report.crowded_short_count != _reason_count(
        report.rows,
        "gold_cftc_managed_money_crowded_short",
    ):
        raise ValueError("crowded_short_count must match rows")
    if report.rally_confirmation_count != _any_reason_count(
        report.rows,
        (
            "gold_cftc_managed_money_price_rally",
            "gold_cftc_managed_money_four_week_rally",
        ),
    ):
        raise ValueError("rally_confirmation_count must match rows")
    if report.high_short_open_interest_count != _reason_count(
        report.rows,
        "gold_cftc_managed_money_high_short_open_interest",
    ):
        raise ValueError("high_short_open_interest_count must match rows")
    if report.max_short_open_interest_share != _max_row_decimal(
        report.rows,
        "short_open_interest_share",
    ):
        raise ValueError("max_short_open_interest_share must match rows")
    if report.average_short_open_interest_share != _ratio(
        _sum_decimal(row.short_open_interest_share for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_short_open_interest_share must match rows")
    if report.squeeze_risk_score != _squeeze_risk_score(report.rows):
        raise ValueError("squeeze_risk_score must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, report.rows):
        raise ValueError("reason_code_counts must match reason_codes")


def _normalize_observations(
    observations: Iterable[GoldCftcManagedMoneySqueezeObservation],
) -> tuple[GoldCftcManagedMoneySqueezeObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError(
            "observations must contain GoldCftcManagedMoneySqueezeObservation",
        )
    normalized = tuple(observations)
    seen_source_ids: set[str] = set()
    for observation in normalized:
        if type(observation) is not GoldCftcManagedMoneySqueezeObservation:
            raise ValueError(
                "observations must contain GoldCftcManagedMoneySqueezeObservation",
            )
        _require_hard_flags("observation", observation)
        if observation.source_id in seen_source_ids:
            raise ValueError("observations must not contain duplicate source_id values")
        seen_source_ids.add(observation.source_id)
    return normalized


def _normalize_rows(
    rows: Iterable[GoldCftcManagedMoneySqueezeDigestRow],
) -> tuple[GoldCftcManagedMoneySqueezeDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must contain GoldCftcManagedMoneySqueezeDigestRow")
    normalized = tuple(rows)
    seen_source_ids: set[str] = set()
    for row in normalized:
        if type(row) is not GoldCftcManagedMoneySqueezeDigestRow:
            raise ValueError("rows must contain GoldCftcManagedMoneySqueezeDigestRow")
        _require_hard_flags("row", row)
        if row.source_id in seen_source_ids:
            raise ValueError("rows must not contain duplicate source_id values")
        seen_source_ids.add(row.source_id)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    values: Iterable[GoldCftcManagedMoneySqueezeReasonCodeCount],
) -> tuple[GoldCftcManagedMoneySqueezeReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError("reason_code_counts must contain reason code counts")
    normalized = tuple(values)
    for value in normalized:
        if type(value) is not GoldCftcManagedMoneySqueezeReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "GoldCftcManagedMoneySqueezeReasonCodeCount",
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
    row: GoldCftcManagedMoneySqueezeDigestRow,
) -> tuple[Decimal, Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.squeeze_status],
        row.net_position_percentile,
        -row.short_open_interest_share,
        row.market_slug,
        row.source_id,
    )


def _status_count(
    rows: tuple[GoldCftcManagedMoneySqueezeDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.squeeze_status == status))


def _reason_count(
    rows: tuple[GoldCftcManagedMoneySqueezeDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _any_reason_count(
    rows: tuple[GoldCftcManagedMoneySqueezeDigestRow, ...],
    reason_codes: tuple[str, ...],
) -> Decimal:
    return _count_decimal(
        sum(1 for row in rows if any(reason in row.reason_codes for reason in reason_codes)),
    )


def _max_row_decimal(
    rows: tuple[GoldCftcManagedMoneySqueezeDigestRow, ...],
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


def _require_ratio_or_signed_share(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < -ONE or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between negative one and one")
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
