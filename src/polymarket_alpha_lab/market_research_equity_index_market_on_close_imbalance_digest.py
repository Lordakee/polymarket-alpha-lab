"""Pure in-memory equity index market-on-close imbalance digest."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Any


DEFAULT_MARKET_RESEARCH_EQUITY_INDEX_MARKET_ON_CLOSE_IMBALANCE_DIGEST_CONFIG_VERSION = (
    "market-research-equity-index-market-on-close-imbalance-digest-v0"
)

_ZERO = Decimal("0")
_ONE = Decimal("1")
_COUNT_QUANTUM = Decimal("1")
_RATIO_QUANTUM = Decimal("0.000001")
_MICROSECONDS_PER_SECOND = Decimal("1000000")

_RISK_STATUSES = ("pass", "watch", "blocked")
_RISK_STATUS_WEIGHT = {"blocked": 0, "watch": 1, "pass": 2}
_CLOSE_TIME_STATUSES = ("open", "near", "imminent", "elapsed")
_FRESHNESS_STATUSES = ("fresh", "aging", "stale", "missing")
_IMBALANCE_STATUSES = ("clear", "watch", "blocked")
_IMBALANCE_SIDES = ("buy", "sell", "flat", "unknown")

_PASS_REASON = "equity_index_moc_imbalance_digest_passed"
_EMPTY_REASON = "equity_index_moc_imbalance_digest_empty"
_REASON_CODE_SEQUENCE = (
    "market_close_elapsed",
    "market_close_imminent",
    "imbalance_missing",
    "imbalance_stale",
    "imbalance_notional_blocked",
    "imbalance_ratio_blocked",
    "indicative_move_blocked",
    "market_close_near",
    "imbalance_aging",
    "imbalance_notional_watch",
    "imbalance_ratio_watch",
    "indicative_move_watch",
    _EMPTY_REASON,
    _PASS_REASON,
)
_NEXT_STEPS = {
    "pass": "allow_equity_index_close_event_screening",
    "watch": "refresh_equity_index_close_imbalance_research",
    "blocked": "defer_equity_index_close_event_screening",
}
_NONPUBLIC_TEXT_MARKERS = (
    "token",
    "password",
    "api_key",
    "apikey",
    "private" "_key",
    "bearer",
    "credential",
)


__all__ = (
    "DEFAULT_MARKET_RESEARCH_EQUITY_INDEX_MARKET_ON_CLOSE_IMBALANCE_DIGEST_CONFIG_VERSION",
    "MarketResearchEquityIndexMarketOnCloseImbalanceDigestConfig",
    "MarketResearchEquityIndexMarketOnCloseImbalanceDigestInputRow",
    "MarketResearchEquityIndexMarketOnCloseImbalanceDigestReasonCodeCount",
    "MarketResearchEquityIndexMarketOnCloseImbalanceDigestReport",
    "MarketResearchEquityIndexMarketOnCloseImbalanceDigestRow",
    "build_market_research_equity_index_market_on_close_imbalance_digest",
    "market_research_equity_index_market_on_close_imbalance_digest_to_json",
)


@dataclass(frozen=True)
class MarketResearchEquityIndexMarketOnCloseImbalanceDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_EQUITY_INDEX_MARKET_ON_CLOSE_IMBALANCE_DIGEST_CONFIG_VERSION
    )
    watch_close_delta_seconds: Decimal = Decimal("1800")
    blocked_close_delta_seconds: Decimal = Decimal("300")
    watch_imbalance_age_seconds: Decimal = Decimal("60")
    max_imbalance_age_seconds: Decimal = Decimal("180")
    watch_abs_imbalance_notional_usd: Decimal = Decimal("500000000")
    max_abs_imbalance_notional_usd: Decimal = Decimal("1500000000")
    watch_imbalance_ratio: Decimal = Decimal("0.020000")
    max_imbalance_ratio: Decimal = Decimal("0.050000")
    watch_abs_indicative_move_bps: Decimal = Decimal("10")
    max_abs_indicative_move_bps: Decimal = Decimal("25")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "watch_close_delta_seconds",
            "blocked_close_delta_seconds",
            "watch_imbalance_age_seconds",
            "max_imbalance_age_seconds",
            "watch_abs_imbalance_notional_usd",
            "max_abs_imbalance_notional_usd",
            "watch_abs_indicative_move_bps",
            "max_abs_indicative_move_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "watch_imbalance_ratio",
            _normalize_ratio("watch_imbalance_ratio", self.watch_imbalance_ratio),
        )
        object.__setattr__(
            self,
            "max_imbalance_ratio",
            _normalize_ratio("max_imbalance_ratio", self.max_imbalance_ratio),
        )
        _validate_config_thresholds(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchEquityIndexMarketOnCloseImbalanceDigestInputRow:
    event_slug: str
    index_symbol: str
    market_close_at: datetime
    imbalance_observed_at: datetime | None
    imbalance_side: str
    imbalance_notional_usd: Decimal
    reference_close_notional_usd: Decimal
    indicative_move_bps: Decimal
    source_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("event_slug", self.event_slug)
        _require_public_string("index_symbol", self.index_symbol)
        object.__setattr__(
            self,
            "market_close_at",
            _as_utc("market_close_at", self.market_close_at),
        )
        object.__setattr__(
            self,
            "imbalance_observed_at",
            _as_optional_utc("imbalance_observed_at", self.imbalance_observed_at),
        )
        _require_member("imbalance_side", self.imbalance_side, _IMBALANCE_SIDES)
        object.__setattr__(
            self,
            "imbalance_notional_usd",
            _normalize_decimal("imbalance_notional_usd", self.imbalance_notional_usd),
        )
        object.__setattr__(
            self,
            "reference_close_notional_usd",
            _normalize_positive_decimal(
                "reference_close_notional_usd",
                self.reference_close_notional_usd,
            ),
        )
        object.__setattr__(
            self,
            "indicative_move_bps",
            _normalize_decimal("indicative_move_bps", self.indicative_move_bps),
        )
        object.__setattr__(
            self,
            "source_reason_codes",
            _normalize_source_reason_codes(self.source_reason_codes),
        )
        _require_hard_flags("input_row", self)


@dataclass(frozen=True)
class MarketResearchEquityIndexMarketOnCloseImbalanceDigestRow:
    event_slug: str
    index_symbol: str
    market_close_at: datetime
    imbalance_observed_at: datetime | None
    imbalance_side: str
    imbalance_notional_usd: Decimal
    abs_imbalance_notional_usd: Decimal
    reference_close_notional_usd: Decimal
    imbalance_ratio: Decimal
    indicative_move_bps: Decimal
    abs_indicative_move_bps: Decimal
    close_time_delta_seconds: Decimal
    imbalance_age_seconds: Decimal | None
    close_time_status: str
    imbalance_freshness_status: str
    imbalance_notional_status: str
    imbalance_ratio_status: str
    indicative_move_status: str
    risk_status: str
    reason_codes: tuple[str, ...]
    source_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("event_slug", self.event_slug)
        _require_public_string("index_symbol", self.index_symbol)
        object.__setattr__(
            self,
            "market_close_at",
            _as_utc("market_close_at", self.market_close_at),
        )
        object.__setattr__(
            self,
            "imbalance_observed_at",
            _as_optional_utc("imbalance_observed_at", self.imbalance_observed_at),
        )
        _require_member("imbalance_side", self.imbalance_side, _IMBALANCE_SIDES)
        for field_name in (
            "imbalance_notional_usd",
            "indicative_move_bps",
            "close_time_delta_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "abs_imbalance_notional_usd",
            "reference_close_notional_usd",
            "abs_indicative_move_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_or_zero_decimal(field_name, getattr(self, field_name)),
            )
        if self.reference_close_notional_usd <= _ZERO:
            raise ValueError("reference_close_notional_usd must be positive")
        object.__setattr__(
            self,
            "imbalance_ratio",
            _normalize_ratio("imbalance_ratio", self.imbalance_ratio),
        )
        object.__setattr__(
            self,
            "imbalance_age_seconds",
            _normalize_optional_nonnegative_decimal(
                "imbalance_age_seconds",
                self.imbalance_age_seconds,
            ),
        )
        _require_member("close_time_status", self.close_time_status, _CLOSE_TIME_STATUSES)
        _require_member(
            "imbalance_freshness_status",
            self.imbalance_freshness_status,
            _FRESHNESS_STATUSES,
        )
        _require_member(
            "imbalance_notional_status",
            self.imbalance_notional_status,
            _IMBALANCE_STATUSES,
        )
        _require_member(
            "imbalance_ratio_status",
            self.imbalance_ratio_status,
            _IMBALANCE_STATUSES,
        )
        _require_member(
            "indicative_move_status",
            self.indicative_move_status,
            _IMBALANCE_STATUSES,
        )
        _require_risk_status("risk_status", self.risk_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_digest_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "source_reason_codes",
            _normalize_source_reason_codes(self.source_reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags("digest_row", self)


@dataclass(frozen=True)
class MarketResearchEquityIndexMarketOnCloseImbalanceDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_digest_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_count_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchEquityIndexMarketOnCloseImbalanceDigestReport:
    generated_at: datetime
    config_version: str
    risk_status: str
    recommended_next_step: str
    row_count: Decimal
    pass_row_count: Decimal
    watch_row_count: Decimal
    blocked_row_count: Decimal
    max_abs_imbalance_notional_usd_observed: Decimal | None
    max_imbalance_ratio_observed: Decimal | None
    max_abs_indicative_move_bps_observed: Decimal | None
    rows: tuple[MarketResearchEquityIndexMarketOnCloseImbalanceDigestRow, ...]
    reason_code_counts: tuple[
        MarketResearchEquityIndexMarketOnCloseImbalanceDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        _require_risk_status("risk_status", self.risk_status)
        if self.recommended_next_step != _NEXT_STEPS[self.risk_status]:
            raise ValueError("recommended_next_step must match risk_status")
        for field_name in (
            "row_count",
            "pass_row_count",
            "watch_row_count",
            "blocked_row_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_abs_imbalance_notional_usd_observed",
            "max_abs_indicative_move_bps_observed",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_nonnegative_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "max_imbalance_ratio_observed",
            _normalize_optional_ratio(
                "max_imbalance_ratio_observed",
                self.max_imbalance_ratio_observed,
            ),
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
            _normalize_digest_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)


def build_market_research_equity_index_market_on_close_imbalance_digest(
    rows: tuple[
        MarketResearchEquityIndexMarketOnCloseImbalanceDigestInputRow,
        ...,
    ]
    | list[MarketResearchEquityIndexMarketOnCloseImbalanceDigestInputRow],
    *,
    config: MarketResearchEquityIndexMarketOnCloseImbalanceDigestConfig,
    generated_at: datetime,
) -> MarketResearchEquityIndexMarketOnCloseImbalanceDigestReport:
    if type(config) is not MarketResearchEquityIndexMarketOnCloseImbalanceDigestConfig:
        raise ValueError(
            "config must be a "
            "MarketResearchEquityIndexMarketOnCloseImbalanceDigestConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    input_rows = _normalize_input_rows(rows)
    digest_rows = tuple(
        _build_row(row, config=config, generated_at=generated_at) for row in input_rows
    )
    sorted_rows = tuple(sorted(digest_rows, key=_row_sort_key))
    reason_code_counts = _build_reason_code_counts(sorted_rows)
    reason_codes = tuple(count.reason_code for count in reason_code_counts)
    if not sorted_rows:
        reason_code_counts = (
            MarketResearchEquityIndexMarketOnCloseImbalanceDigestReasonCodeCount(
                reason_code=_EMPTY_REASON,
                count=Decimal("1"),
            ),
        )
        reason_codes = (_EMPTY_REASON,)
    elif not reason_code_counts:
        reason_code_counts = (
            MarketResearchEquityIndexMarketOnCloseImbalanceDigestReasonCodeCount(
                reason_code=_PASS_REASON,
                count=_count_decimal(len(sorted_rows)),
            ),
        )
        reason_codes = (_PASS_REASON,)
    risk_status = _report_status(sorted_rows, reason_codes)
    return MarketResearchEquityIndexMarketOnCloseImbalanceDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        risk_status=risk_status,
        recommended_next_step=_NEXT_STEPS[risk_status],
        row_count=_count_decimal(len(sorted_rows)),
        pass_row_count=_count_decimal(
            sum(1 for row in sorted_rows if row.risk_status == "pass"),
        ),
        watch_row_count=_count_decimal(
            sum(1 for row in sorted_rows if row.risk_status == "watch"),
        ),
        blocked_row_count=_count_decimal(
            sum(1 for row in sorted_rows if row.risk_status == "blocked"),
        ),
        max_abs_imbalance_notional_usd_observed=_max_optional(
            row.abs_imbalance_notional_usd for row in sorted_rows
        ),
        max_imbalance_ratio_observed=_max_optional(
            row.imbalance_ratio for row in sorted_rows
        ),
        max_abs_indicative_move_bps_observed=_max_optional(
            row.abs_indicative_move_bps for row in sorted_rows
        ),
        rows=sorted_rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_equity_index_market_on_close_imbalance_digest_to_json(
    report: MarketResearchEquityIndexMarketOnCloseImbalanceDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchEquityIndexMarketOnCloseImbalanceDigestReport:
        raise ValueError(
            "report must be a "
            "MarketResearchEquityIndexMarketOnCloseImbalanceDigestReport",
        )
    return _json_ready(report)


def _build_row(
    row: MarketResearchEquityIndexMarketOnCloseImbalanceDigestInputRow,
    *,
    config: MarketResearchEquityIndexMarketOnCloseImbalanceDigestConfig,
    generated_at: datetime,
) -> MarketResearchEquityIndexMarketOnCloseImbalanceDigestRow:
    if row.imbalance_observed_at is not None and row.imbalance_observed_at > generated_at:
        raise ValueError("imbalance_observed_at must not be in the future")
    close_time_delta_seconds = _seconds_between(row.market_close_at, generated_at)
    imbalance_age_seconds = (
        None
        if row.imbalance_observed_at is None
        else _nonnegative_seconds_between(generated_at, row.imbalance_observed_at)
    )
    abs_imbalance_notional_usd = abs(row.imbalance_notional_usd)
    imbalance_ratio = _normalize_ratio(
        "imbalance_ratio",
        abs_imbalance_notional_usd / row.reference_close_notional_usd,
    )
    abs_indicative_move_bps = abs(row.indicative_move_bps)

    close_time_status = _close_time_status(close_time_delta_seconds, config)
    imbalance_freshness_status = _freshness_status(imbalance_age_seconds, config)
    imbalance_notional_status = _threshold_status(
        abs_imbalance_notional_usd,
        watch_threshold=config.watch_abs_imbalance_notional_usd,
        max_threshold=config.max_abs_imbalance_notional_usd,
    )
    imbalance_ratio_status = _threshold_status(
        imbalance_ratio,
        watch_threshold=config.watch_imbalance_ratio,
        max_threshold=config.max_imbalance_ratio,
    )
    indicative_move_status = _threshold_status(
        abs_indicative_move_bps,
        watch_threshold=config.watch_abs_indicative_move_bps,
        max_threshold=config.max_abs_indicative_move_bps,
    )
    reason_codes = _row_reason_codes(
        close_time_status=close_time_status,
        imbalance_freshness_status=imbalance_freshness_status,
        imbalance_notional_status=imbalance_notional_status,
        imbalance_ratio_status=imbalance_ratio_status,
        indicative_move_status=indicative_move_status,
    )
    risk_status = _status_from_reason_codes(reason_codes)

    return MarketResearchEquityIndexMarketOnCloseImbalanceDigestRow(
        event_slug=row.event_slug,
        index_symbol=row.index_symbol,
        market_close_at=row.market_close_at,
        imbalance_observed_at=row.imbalance_observed_at,
        imbalance_side=row.imbalance_side,
        imbalance_notional_usd=row.imbalance_notional_usd,
        abs_imbalance_notional_usd=abs_imbalance_notional_usd,
        reference_close_notional_usd=row.reference_close_notional_usd,
        imbalance_ratio=imbalance_ratio,
        indicative_move_bps=row.indicative_move_bps,
        abs_indicative_move_bps=abs_indicative_move_bps,
        close_time_delta_seconds=close_time_delta_seconds,
        imbalance_age_seconds=imbalance_age_seconds,
        close_time_status=close_time_status,
        imbalance_freshness_status=imbalance_freshness_status,
        imbalance_notional_status=imbalance_notional_status,
        imbalance_ratio_status=imbalance_ratio_status,
        indicative_move_status=indicative_move_status,
        risk_status=risk_status,
        reason_codes=reason_codes,
        source_reason_codes=row.source_reason_codes,
    )


def _row_reason_codes(
    *,
    close_time_status: str,
    imbalance_freshness_status: str,
    imbalance_notional_status: str,
    imbalance_ratio_status: str,
    indicative_move_status: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if close_time_status == "elapsed":
        reason_codes.append("market_close_elapsed")
    elif close_time_status == "imminent":
        reason_codes.append("market_close_imminent")
    elif close_time_status == "near":
        reason_codes.append("market_close_near")
    if imbalance_freshness_status == "missing":
        reason_codes.append("imbalance_missing")
    elif imbalance_freshness_status == "stale":
        reason_codes.append("imbalance_stale")
    elif imbalance_freshness_status == "aging":
        reason_codes.append("imbalance_aging")
    if imbalance_notional_status == "blocked":
        reason_codes.append("imbalance_notional_blocked")
    elif imbalance_notional_status == "watch":
        reason_codes.append("imbalance_notional_watch")
    if imbalance_ratio_status == "blocked":
        reason_codes.append("imbalance_ratio_blocked")
    elif imbalance_ratio_status == "watch":
        reason_codes.append("imbalance_ratio_watch")
    if indicative_move_status == "blocked":
        reason_codes.append("indicative_move_blocked")
    elif indicative_move_status == "watch":
        reason_codes.append("indicative_move_watch")
    if not reason_codes:
        reason_codes.append(_PASS_REASON)
    return tuple(
        sorted(
            reason_codes,
            key=lambda reason_code: _REASON_CODE_SEQUENCE.index(reason_code),
        ),
    )


def _build_reason_code_counts(
    rows: tuple[MarketResearchEquityIndexMarketOnCloseImbalanceDigestRow, ...],
) -> tuple[MarketResearchEquityIndexMarketOnCloseImbalanceDigestReasonCodeCount, ...]:
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code == _PASS_REASON:
                continue
            counts[reason_code] = counts.get(reason_code, _ZERO) + _ONE
    return tuple(
        MarketResearchEquityIndexMarketOnCloseImbalanceDigestReasonCodeCount(
            reason_code=reason_code,
            count=counts[reason_code],
        )
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _report_status(
    rows: tuple[MarketResearchEquityIndexMarketOnCloseImbalanceDigestRow, ...],
    reason_codes: tuple[str, ...],
) -> str:
    if not rows:
        return "blocked"
    if any(_is_blocking_reason(reason_code) for reason_code in reason_codes):
        return "blocked"
    if any(_is_watch_reason(reason_code) for reason_code in reason_codes):
        return "watch"
    return "pass"


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(_is_blocking_reason(reason_code) for reason_code in reason_codes):
        return "blocked"
    if any(_is_watch_reason(reason_code) for reason_code in reason_codes):
        return "watch"
    return "pass"


def _is_blocking_reason(reason_code: str) -> bool:
    return reason_code in {
        "market_close_elapsed",
        "market_close_imminent",
        "imbalance_missing",
        "imbalance_stale",
        "imbalance_notional_blocked",
        "imbalance_ratio_blocked",
        "indicative_move_blocked",
        _EMPTY_REASON,
    }


def _is_watch_reason(reason_code: str) -> bool:
    return reason_code in {
        "market_close_near",
        "imbalance_aging",
        "imbalance_notional_watch",
        "imbalance_ratio_watch",
        "indicative_move_watch",
    }


def _row_sort_key(
    row: MarketResearchEquityIndexMarketOnCloseImbalanceDigestRow,
) -> tuple[int, int, str, str, str]:
    primary_reason = row.reason_codes[0]
    return (
        _RISK_STATUS_WEIGHT[row.risk_status],
        _REASON_CODE_SEQUENCE.index(primary_reason),
        row.event_slug,
        row.index_symbol,
        row.imbalance_side,
    )


def _close_time_status(
    close_time_delta_seconds: Decimal,
    config: MarketResearchEquityIndexMarketOnCloseImbalanceDigestConfig,
) -> str:
    if close_time_delta_seconds < _ZERO:
        return "elapsed"
    if close_time_delta_seconds <= config.blocked_close_delta_seconds:
        return "imminent"
    if close_time_delta_seconds <= config.watch_close_delta_seconds:
        return "near"
    return "open"


def _freshness_status(
    age_seconds: Decimal | None,
    config: MarketResearchEquityIndexMarketOnCloseImbalanceDigestConfig,
) -> str:
    if age_seconds is None:
        return "missing"
    if age_seconds >= config.max_imbalance_age_seconds:
        return "stale"
    if age_seconds >= config.watch_imbalance_age_seconds:
        return "aging"
    return "fresh"


def _threshold_status(
    value: Decimal,
    *,
    watch_threshold: Decimal,
    max_threshold: Decimal,
) -> str:
    if value >= max_threshold:
        return "blocked"
    if value >= watch_threshold:
        return "watch"
    return "clear"


def _validate_config_thresholds(
    config: MarketResearchEquityIndexMarketOnCloseImbalanceDigestConfig,
) -> None:
    if config.blocked_close_delta_seconds >= config.watch_close_delta_seconds:
        raise ValueError(
            "watch_close_delta_seconds must exceed blocked_close_delta_seconds",
        )
    for watch_name, max_name in (
        ("watch_imbalance_age_seconds", "max_imbalance_age_seconds"),
        (
            "watch_abs_imbalance_notional_usd",
            "max_abs_imbalance_notional_usd",
        ),
        ("watch_imbalance_ratio", "max_imbalance_ratio"),
        ("watch_abs_indicative_move_bps", "max_abs_indicative_move_bps"),
    ):
        if getattr(config, max_name) <= getattr(config, watch_name):
            raise ValueError(f"{max_name} must exceed {watch_name}")


def _validate_row_consistency(
    row: MarketResearchEquityIndexMarketOnCloseImbalanceDigestRow,
) -> None:
    if row.abs_imbalance_notional_usd != abs(row.imbalance_notional_usd):
        raise ValueError("abs_imbalance_notional_usd must match imbalance_notional_usd")
    if row.abs_indicative_move_bps != abs(row.indicative_move_bps):
        raise ValueError("abs_indicative_move_bps must match indicative_move_bps")
    expected_ratio = _normalize_ratio(
        "imbalance_ratio",
        row.abs_imbalance_notional_usd / row.reference_close_notional_usd,
    )
    if row.imbalance_ratio != expected_ratio:
        raise ValueError("imbalance_ratio must match notional inputs")
    if row.risk_status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("risk_status must match reason_codes")


def _validate_report_consistency(
    report: MarketResearchEquityIndexMarketOnCloseImbalanceDigestReport,
) -> None:
    rows = report.rows
    if report.row_count != _count_decimal(len(rows)):
        raise ValueError("row_count must match rows")
    if report.pass_row_count != _count_decimal(
        sum(1 for row in rows if row.risk_status == "pass"),
    ):
        raise ValueError("pass_row_count must match rows")
    if report.watch_row_count != _count_decimal(
        sum(1 for row in rows if row.risk_status == "watch"),
    ):
        raise ValueError("watch_row_count must match rows")
    if report.blocked_row_count != _count_decimal(
        sum(1 for row in rows if row.risk_status == "blocked"),
    ):
        raise ValueError("blocked_row_count must match rows")
    expected_reason_code_counts = _build_reason_code_counts(rows)
    if not rows:
        expected_reason_code_counts = (
            MarketResearchEquityIndexMarketOnCloseImbalanceDigestReasonCodeCount(
                reason_code=_EMPTY_REASON,
                count=Decimal("1"),
            ),
        )
    elif not expected_reason_code_counts:
        expected_reason_code_counts = (
            MarketResearchEquityIndexMarketOnCloseImbalanceDigestReasonCodeCount(
                reason_code=_PASS_REASON,
                count=_count_decimal(len(rows)),
            ),
        )
    if report.reason_code_counts != expected_reason_code_counts:
        raise ValueError("reason_code_counts must match rows")
    expected_reason_codes = tuple(count.reason_code for count in expected_reason_code_counts)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match reason_code_counts")
    expected_status = _report_status(rows, report.reason_codes)
    if report.risk_status != expected_status:
        raise ValueError("risk_status must match reason_codes")
    if report.recommended_next_step != _NEXT_STEPS[report.risk_status]:
        raise ValueError("recommended_next_step must match risk_status")
    if report.max_abs_imbalance_notional_usd_observed != _max_optional(
        row.abs_imbalance_notional_usd for row in rows
    ):
        raise ValueError("max_abs_imbalance_notional_usd_observed must match rows")
    if report.max_imbalance_ratio_observed != _max_optional(
        row.imbalance_ratio for row in rows
    ):
        raise ValueError("max_imbalance_ratio_observed must match rows")
    if report.max_abs_indicative_move_bps_observed != _max_optional(
        row.abs_indicative_move_bps for row in rows
    ):
        raise ValueError("max_abs_indicative_move_bps_observed must match rows")


def _normalize_input_rows(
    rows: tuple[
        MarketResearchEquityIndexMarketOnCloseImbalanceDigestInputRow,
        ...,
    ]
    | list[MarketResearchEquityIndexMarketOnCloseImbalanceDigestInputRow],
) -> tuple[MarketResearchEquityIndexMarketOnCloseImbalanceDigestInputRow, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not MarketResearchEquityIndexMarketOnCloseImbalanceDigestInputRow:
            raise ValueError(
                "rows must contain "
                "MarketResearchEquityIndexMarketOnCloseImbalanceDigestInputRow",
            )
    return normalized


def _normalize_rows(
    rows: tuple[MarketResearchEquityIndexMarketOnCloseImbalanceDigestRow, ...],
) -> tuple[MarketResearchEquityIndexMarketOnCloseImbalanceDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchEquityIndexMarketOnCloseImbalanceDigestRow:
            raise ValueError(
                "rows must contain "
                "MarketResearchEquityIndexMarketOnCloseImbalanceDigestRow",
            )
    return rows


def _normalize_reason_code_counts(
    counts: tuple[
        MarketResearchEquityIndexMarketOnCloseImbalanceDigestReasonCodeCount,
        ...,
    ],
) -> tuple[MarketResearchEquityIndexMarketOnCloseImbalanceDigestReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    previous_index = -1
    for count in counts:
        if (
            type(count)
            is not MarketResearchEquityIndexMarketOnCloseImbalanceDigestReasonCodeCount
        ):
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchEquityIndexMarketOnCloseImbalanceDigestReasonCodeCount",
            )
        index = _REASON_CODE_SEQUENCE.index(count.reason_code)
        if index <= previous_index:
            raise ValueError("reason_code_counts must be in deterministic sequence")
        previous_index = index
    return counts


def _normalize_digest_reason_codes(
    field_name: str,
    value: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    if not reason_codes:
        raise ValueError(f"{field_name} must contain at least one value")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must not contain duplicates")
    previous_index = -1
    for reason_code in reason_codes:
        _require_digest_reason_code(field_name, reason_code)
        index = _REASON_CODE_SEQUENCE.index(reason_code)
        if index <= previous_index:
            raise ValueError(f"{field_name} must be in deterministic sequence")
        previous_index = index
    return reason_codes


def _normalize_source_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("source_reason_codes must be an iterable of strings")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError("source_reason_codes must be an iterable of strings") from exc
    if not reason_codes:
        raise ValueError("source_reason_codes must contain at least one value")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("source_reason_codes must not contain duplicates")
    for reason_code in reason_codes:
        _require_public_string("source_reason_codes", reason_code)
    return reason_codes


def _require_digest_reason_code(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if value not in _REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name) is not True:
            raise ValueError(f"{field_name} must be {flag_name}")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _require_risk_status(field_name: str, value: object) -> None:
    _require_member(field_name, value, _RISK_STATUSES)


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical nonblank text")
    lowered = value.lower()
    if any(marker in lowered for marker in _NONPUBLIC_TEXT_MARKERS):
        raise ValueError(f"{field_name} must be public text")


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(_RATIO_QUANTUM, rounding=ROUND_HALF_EVEN).normalize()


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_or_zero_decimal(field_name: str, value: object) -> Decimal:
    return _normalize_nonnegative_decimal(field_name, value)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_optional_nonnegative_decimal(
    field_name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_decimal(field_name, value)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    return normalized.quantize(_RATIO_QUANTUM)


def _normalize_optional_ratio(field_name: str, value: Decimal | None) -> Decimal | None:
    if value is None:
        return None
    return _normalize_ratio(field_name, value)


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.quantize(_COUNT_QUANTUM):
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized.quantize(_COUNT_QUANTUM)


def _normalize_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_count_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(_COUNT_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is not UTC:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value


def _as_optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    return _seconds_from_timedelta(later - earlier)


def _nonnegative_seconds_between(later: datetime, earlier: datetime) -> Decimal:
    value = _seconds_between(later, earlier)
    if value < _ZERO:
        return _ZERO
    return value


def _seconds_from_timedelta(value: timedelta) -> Decimal:
    total_microseconds = (
        Decimal(value.days) * Decimal("86400") * _MICROSECONDS_PER_SECOND
        + Decimal(value.seconds) * _MICROSECONDS_PER_SECOND
        + Decimal(value.microseconds)
    )
    return (total_microseconds / _MICROSECONDS_PER_SECOND).quantize(
        _RATIO_QUANTUM,
        rounding=ROUND_HALF_EVEN,
    ).normalize()


def _max_optional(values: object) -> Decimal | None:
    observed = tuple(value for value in values if value is not None)
    if not observed:
        return None
    return max(observed)


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value
