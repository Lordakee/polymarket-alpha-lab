"""Pure fee-regime change watch report for prior screening cost assumptions."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_MARKET_FEE_REGIME_CHANGE_WATCH_CONFIG_VERSION = (
    "research-market-fee-regime-change-watch-report-v0"
)

STATUSES = ("pass", "watch", "block")
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

EMPTY_REASON = "fee_regime_change_watch_empty"
PASS_REASON = "fee_regime_change_clear"
TAKER_FEE_WATCH_REASON = "taker_fee_change_watch"
TAKER_FEE_BLOCK_REASON = "taker_fee_change_block"
SPREAD_COST_WATCH_REASON = "spread_cost_drift_watch"
SPREAD_COST_BLOCK_REASON = "spread_cost_drift_block"
SETTLEMENT_FRICTION_WATCH_REASON = "settlement_friction_drift_watch"
SETTLEMENT_FRICTION_BLOCK_REASON = "settlement_friction_drift_block"
COST_AGE_WATCH_REASON = "cost_timestamp_age_watch"
COST_AGE_BLOCK_REASON = "cost_timestamp_age_block"
MANUAL_RECHECK_WATCH_REASON = "manual_recheck_urgency_watch"
MANUAL_RECHECK_BLOCK_REASON = "manual_recheck_urgency_block"

BLOCK_REASON_CODES = (
    TAKER_FEE_BLOCK_REASON,
    SPREAD_COST_BLOCK_REASON,
    SETTLEMENT_FRICTION_BLOCK_REASON,
    COST_AGE_BLOCK_REASON,
    MANUAL_RECHECK_BLOCK_REASON,
)
WATCH_REASON_CODES = (
    TAKER_FEE_WATCH_REASON,
    SPREAD_COST_WATCH_REASON,
    SETTLEMENT_FRICTION_WATCH_REASON,
    COST_AGE_WATCH_REASON,
    MANUAL_RECHECK_WATCH_REASON,
)
ROW_REASON_CODES = BLOCK_REASON_CODES + WATCH_REASON_CODES + (PASS_REASON,)
REPORT_REASON_CODES = BLOCK_REASON_CODES + WATCH_REASON_CODES + (PASS_REASON, EMPTY_REASON)
STATUS_WEIGHT = {
    "block": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
SAFE_TEXT_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789._:-")
HEX_CHARS = frozenset("0123456789abcdef")
UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "au" + "th",
        "bro" + "ker",
        "data" + "base",
        "net" + "work",
        "or" + "der",
        "private" + "_" + "key",
        "recom" + "mendation",
        "sign" + "ing",
        "siz" + "ing",
        "tra" + "de",
        "wal" + "let",
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_MARKET_FEE_REGIME_CHANGE_WATCH_CONFIG_VERSION",
    "STATUSES",
    "ResearchMarketFeeRegimeChangeWatchConfig",
    "ResearchMarketFeeRegimeChangeWatchInput",
    "ResearchMarketFeeRegimeChangeWatchReasonCodeCount",
    "ResearchMarketFeeRegimeChangeWatchReport",
    "ResearchMarketFeeRegimeChangeWatchRow",
    "build_research_market_fee_regime_change_watch_report",
    "research_market_fee_regime_change_watch_report_payload",
)


@dataclass(frozen=True)
class ResearchMarketFeeRegimeChangeWatchConfig:
    config_version: str = DEFAULT_RESEARCH_MARKET_FEE_REGIME_CHANGE_WATCH_CONFIG_VERSION
    taker_fee_watch_delta_bps: Decimal = Decimal("1.000000")
    taker_fee_block_delta_bps: Decimal = Decimal("3.000000")
    spread_cost_watch_drift: Decimal = Decimal("0.005000")
    spread_cost_block_drift: Decimal = Decimal("0.015000")
    settlement_friction_watch_drift: Decimal = Decimal("0.005000")
    settlement_friction_block_drift: Decimal = Decimal("0.015000")
    cost_age_watch_seconds: Decimal = Decimal("3600.000000")
    cost_age_block_seconds: Decimal = Decimal("14400.000000")
    manual_recheck_watch_urgency: Decimal = Decimal("0.500000")
    manual_recheck_block_urgency: Decimal = Decimal("0.800000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketFeeRegimeChangeWatchConfig, "config")
        _require_public_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_FEE_REGIME_CHANGE_WATCH_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "taker_fee_watch_delta_bps",
            "taker_fee_block_delta_bps",
            "spread_cost_watch_drift",
            "spread_cost_block_drift",
            "settlement_friction_watch_drift",
            "settlement_friction_block_drift",
            "cost_age_watch_seconds",
            "cost_age_block_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "manual_recheck_watch_urgency",
            "manual_recheck_block_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketFeeRegimeChangeWatchInput:
    screening_key: str
    prior_taker_fee_bps: Decimal
    current_taker_fee_bps: Decimal
    prior_spread_cost: Decimal
    current_spread_cost: Decimal
    prior_settlement_friction: Decimal
    current_settlement_friction: Decimal
    cost_observed_at: datetime
    manual_recheck_urgency: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketFeeRegimeChangeWatchInput, "input")
        _require_public_text("screening_key", self.screening_key)
        for field_name in (
            "prior_taker_fee_bps",
            "current_taker_fee_bps",
            "prior_spread_cost",
            "current_spread_cost",
            "prior_settlement_friction",
            "current_settlement_friction",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "manual_recheck_urgency",
            _require_ratio_decimal(
                "manual_recheck_urgency",
                self.manual_recheck_urgency,
            ),
        )
        object.__setattr__(
            self,
            "cost_observed_at",
            _as_utc("cost_observed_at", self.cost_observed_at),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchMarketFeeRegimeChangeWatchRow:
    screening_key: str
    status: str
    prior_taker_fee_bps: Decimal
    current_taker_fee_bps: Decimal
    taker_fee_delta_bps: Decimal
    prior_spread_cost: Decimal
    current_spread_cost: Decimal
    spread_cost_drift: Decimal
    prior_settlement_friction: Decimal
    current_settlement_friction: Decimal
    settlement_friction_drift: Decimal
    cost_observed_at: datetime
    cost_age_seconds: Decimal
    manual_recheck_urgency: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketFeeRegimeChangeWatchRow, "row")
        _require_public_text("screening_key", self.screening_key)
        _require_status("status", self.status)
        for field_name in (
            "prior_taker_fee_bps",
            "current_taker_fee_bps",
            "taker_fee_delta_bps",
            "prior_spread_cost",
            "current_spread_cost",
            "spread_cost_drift",
            "prior_settlement_friction",
            "current_settlement_friction",
            "settlement_friction_drift",
            "cost_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "manual_recheck_urgency",
            _require_ratio_decimal(
                "manual_recheck_urgency",
                self.manual_recheck_urgency,
            ),
        )
        object.__setattr__(
            self,
            "cost_observed_at",
            _as_utc("cost_observed_at", self.cost_observed_at),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchMarketFeeRegimeChangeWatchReasonCodeCount:
    reason_code: str
    count: Decimal
    screening_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketFeeRegimeChangeWatchReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code, REPORT_REASON_CODES)
        object.__setattr__(self, "count", _require_count_decimal("count", self.count))
        object.__setattr__(
            self,
            "screening_ratio",
            _require_ratio_decimal("screening_ratio", self.screening_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketFeeRegimeChangeWatchReport:
    generated_at: datetime
    config_version: str
    screening_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_taker_fee_delta_bps: Decimal
    max_spread_cost_drift: Decimal
    max_settlement_friction_drift: Decimal
    max_cost_age_seconds: Decimal
    max_manual_recheck_urgency: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchMarketFeeRegimeChangeWatchReasonCodeCount, ...]
    rows: tuple[ResearchMarketFeeRegimeChangeWatchRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketFeeRegimeChangeWatchReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_FEE_REGIME_CHANGE_WATCH_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "screening_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_taker_fee_delta_bps",
            "max_spread_cost_drift",
            "max_settlement_friction_drift",
            "max_cost_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_manual_recheck_urgency",
            _require_ratio_decimal(
                "max_manual_recheck_urgency",
                self.max_manual_recheck_urgency,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _require_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _require_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)
        if self.derived_validation_digest:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != _derived_validation_digest(self):
                raise ValueError("derived_validation_digest does not match report payload")
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _derived_validation_digest(self),
            )
        _reject_unsafe_public_text("report", self)


def build_research_market_fee_regime_change_watch_report(
    inputs: tuple[ResearchMarketFeeRegimeChangeWatchInput, ...]
    | list[ResearchMarketFeeRegimeChangeWatchInput],
    *,
    config: ResearchMarketFeeRegimeChangeWatchConfig,
    generated_at: datetime,
) -> ResearchMarketFeeRegimeChangeWatchReport:
    if type(config) is not ResearchMarketFeeRegimeChangeWatchConfig:
        raise ValueError("config must be a ResearchMarketFeeRegimeChangeWatchConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (
                _row_from_input(item, config=config, generated_at=generated_at_utc)
                for item in _normalize_inputs(inputs)
            ),
            key=_row_sort_key,
        ),
    )
    status = _rollup_status(tuple(row.status for row in rows))
    return ResearchMarketFeeRegimeChangeWatchReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        screening_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        max_taker_fee_delta_bps=_max_decimal(
            tuple(row.taker_fee_delta_bps for row in rows),
        ),
        max_spread_cost_drift=_max_decimal(
            tuple(row.spread_cost_drift for row in rows),
        ),
        max_settlement_friction_drift=_max_decimal(
            tuple(row.settlement_friction_drift for row in rows),
        ),
        max_cost_age_seconds=_max_decimal(tuple(row.cost_age_seconds for row in rows)),
        max_manual_recheck_urgency=_max_decimal(
            tuple(row.manual_recheck_urgency for row in rows),
        ),
        status=status,
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_market_fee_regime_change_watch_report_payload(
    report: ResearchMarketFeeRegimeChangeWatchReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchMarketFeeRegimeChangeWatchReport:
        _require_hard_flags("report", report)
        _validate_report(report)
        if report.derived_validation_digest != _derived_validation_digest(report):
            raise ValueError("derived_validation_digest does not match report payload")
        _reject_unsafe_public_text("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _require_public_payload_schema(report)
        _reject_public_numerics(report)
        _reject_unsafe_public_text("public payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchMarketFeeRegimeChangeWatchReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_public_payload_schema(payload)
    _reject_public_numerics(payload)
    _require_hard_flags("public payload", _PayloadFlags(payload))
    supplied_digest = payload.get("derived_validation_digest")
    if type(supplied_digest) is not str:
        raise ValueError("derived_validation_digest is required")
    _require_sha256("derived_validation_digest", supplied_digest)
    if supplied_digest != _payload_validation_digest(payload):
        raise ValueError("derived_validation_digest does not match public payload")
    _reject_unsafe_public_text("public payload", payload)
    return payload


@dataclass(frozen=True)
class _PayloadFlags:
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


def _normalize_inputs(
    value: object,
) -> tuple[ResearchMarketFeeRegimeChangeWatchInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    items = tuple(value)
    seen: set[str] = set()
    for item in items:
        if type(item) is not ResearchMarketFeeRegimeChangeWatchInput:
            raise ValueError(
                "inputs must contain ResearchMarketFeeRegimeChangeWatchInput",
            )
        _require_hard_flags("input", item)
        if item.screening_key in seen:
            raise ValueError("screening_key values must be unique")
        seen.add(item.screening_key)
    return items


def _row_from_input(
    item: ResearchMarketFeeRegimeChangeWatchInput,
    *,
    config: ResearchMarketFeeRegimeChangeWatchConfig,
    generated_at: datetime,
) -> ResearchMarketFeeRegimeChangeWatchRow:
    if item.cost_observed_at >= generated_at:
        raise ValueError("cost_observed_at must not be in the future")
    taker_fee_delta_bps = _abs_decimal(item.current_taker_fee_bps - item.prior_taker_fee_bps)
    spread_cost_drift = _abs_decimal(item.current_spread_cost - item.prior_spread_cost)
    settlement_friction_drift = _abs_decimal(
        item.current_settlement_friction - item.prior_settlement_friction,
    )
    cost_age_seconds = _seconds_between(item.cost_observed_at, generated_at)
    reason_codes = _row_reason_codes(
        taker_fee_delta_bps=taker_fee_delta_bps,
        spread_cost_drift=spread_cost_drift,
        settlement_friction_drift=settlement_friction_drift,
        cost_age_seconds=cost_age_seconds,
        manual_recheck_urgency=item.manual_recheck_urgency,
        config=config,
    )
    return ResearchMarketFeeRegimeChangeWatchRow(
        screening_key=item.screening_key,
        status=_status_from_reason_codes(reason_codes),
        prior_taker_fee_bps=item.prior_taker_fee_bps,
        current_taker_fee_bps=item.current_taker_fee_bps,
        taker_fee_delta_bps=taker_fee_delta_bps,
        prior_spread_cost=item.prior_spread_cost,
        current_spread_cost=item.current_spread_cost,
        spread_cost_drift=spread_cost_drift,
        prior_settlement_friction=item.prior_settlement_friction,
        current_settlement_friction=item.current_settlement_friction,
        settlement_friction_drift=settlement_friction_drift,
        cost_observed_at=item.cost_observed_at,
        cost_age_seconds=cost_age_seconds,
        manual_recheck_urgency=item.manual_recheck_urgency,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    taker_fee_delta_bps: Decimal,
    spread_cost_drift: Decimal,
    settlement_friction_drift: Decimal,
    cost_age_seconds: Decimal,
    manual_recheck_urgency: Decimal,
    config: ResearchMarketFeeRegimeChangeWatchConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if taker_fee_delta_bps >= config.taker_fee_block_delta_bps:
        reason_codes.append(TAKER_FEE_BLOCK_REASON)
    elif taker_fee_delta_bps >= config.taker_fee_watch_delta_bps:
        reason_codes.append(TAKER_FEE_WATCH_REASON)
    if spread_cost_drift >= config.spread_cost_block_drift:
        reason_codes.append(SPREAD_COST_BLOCK_REASON)
    elif spread_cost_drift >= config.spread_cost_watch_drift:
        reason_codes.append(SPREAD_COST_WATCH_REASON)
    if settlement_friction_drift >= config.settlement_friction_block_drift:
        reason_codes.append(SETTLEMENT_FRICTION_BLOCK_REASON)
    elif settlement_friction_drift >= config.settlement_friction_watch_drift:
        reason_codes.append(SETTLEMENT_FRICTION_WATCH_REASON)
    if cost_age_seconds >= config.cost_age_block_seconds:
        reason_codes.append(COST_AGE_BLOCK_REASON)
    elif cost_age_seconds >= config.cost_age_watch_seconds:
        reason_codes.append(COST_AGE_WATCH_REASON)
    if manual_recheck_urgency >= config.manual_recheck_block_urgency:
        reason_codes.append(MANUAL_RECHECK_BLOCK_REASON)
    elif manual_recheck_urgency >= config.manual_recheck_watch_urgency:
        reason_codes.append(MANUAL_RECHECK_WATCH_REASON)
    if not reason_codes:
        return (PASS_REASON,)
    return tuple(reason_codes)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "pass"


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if any(status == "block" for status in statuses):
        return "block"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _row_sort_key(row: ResearchMarketFeeRegimeChangeWatchRow) -> tuple[Decimal, str]:
    return (-STATUS_WEIGHT[row.status], row.screening_key)


def _status_count(
    rows: tuple[ResearchMarketFeeRegimeChangeWatchRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(row.status == status for row in rows))


def _report_reason_codes(
    rows: tuple[ResearchMarketFeeRegimeChangeWatchRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    present = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != PASS_REASON
    }
    if not present:
        return (PASS_REASON,)
    return tuple(reason_code for reason_code in BLOCK_REASON_CODES + WATCH_REASON_CODES if reason_code in present)


def _reason_code_counts(
    rows: tuple[ResearchMarketFeeRegimeChangeWatchRow, ...],
) -> tuple[ResearchMarketFeeRegimeChangeWatchReasonCodeCount, ...]:
    report_reason_codes = _report_reason_codes(rows)
    total_count = _count(len(rows))
    counts = Counter(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code in report_reason_codes
    )
    if not rows:
        counts = Counter({EMPTY_REASON: Decimal("1")})
    return tuple(
        ResearchMarketFeeRegimeChangeWatchReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
            screening_ratio=_ratio(_count(counts[reason_code]), total_count),
        )
        for reason_code in report_reason_codes
    )


def _validate_config(config: ResearchMarketFeeRegimeChangeWatchConfig) -> None:
    _require_greater(
        "taker_fee_block_delta_bps",
        config.taker_fee_block_delta_bps,
        "taker_fee_watch_delta_bps",
        config.taker_fee_watch_delta_bps,
    )
    _require_greater(
        "spread_cost_block_drift",
        config.spread_cost_block_drift,
        "spread_cost_watch_drift",
        config.spread_cost_watch_drift,
    )
    _require_greater(
        "settlement_friction_block_drift",
        config.settlement_friction_block_drift,
        "settlement_friction_watch_drift",
        config.settlement_friction_watch_drift,
    )
    _require_greater(
        "cost_age_block_seconds",
        config.cost_age_block_seconds,
        "cost_age_watch_seconds",
        config.cost_age_watch_seconds,
    )
    _require_greater(
        "manual_recheck_block_urgency",
        config.manual_recheck_block_urgency,
        "manual_recheck_watch_urgency",
        config.manual_recheck_watch_urgency,
    )


def _validate_row(row: ResearchMarketFeeRegimeChangeWatchRow) -> None:
    if row.taker_fee_delta_bps != _abs_decimal(
        row.current_taker_fee_bps - row.prior_taker_fee_bps,
    ):
        raise ValueError("taker_fee_delta_bps must match fee inputs")
    if row.spread_cost_drift != _abs_decimal(row.current_spread_cost - row.prior_spread_cost):
        raise ValueError("spread_cost_drift must match cost inputs")
    if row.settlement_friction_drift != _abs_decimal(
        row.current_settlement_friction - row.prior_settlement_friction,
    ):
        raise ValueError("settlement_friction_drift must match cost inputs")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchMarketFeeRegimeChangeWatchReport) -> None:
    if report.screening_count != _count(len(report.rows)):
        raise ValueError("screening_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.max_taker_fee_delta_bps != _max_decimal(
        tuple(row.taker_fee_delta_bps for row in report.rows),
    ):
        raise ValueError("max_taker_fee_delta_bps must match rows")
    if report.max_spread_cost_drift != _max_decimal(
        tuple(row.spread_cost_drift for row in report.rows),
    ):
        raise ValueError("max_spread_cost_drift must match rows")
    if report.max_settlement_friction_drift != _max_decimal(
        tuple(row.settlement_friction_drift for row in report.rows),
    ):
        raise ValueError("max_settlement_friction_drift must match rows")
    if report.max_cost_age_seconds != _max_decimal(
        tuple(row.cost_age_seconds for row in report.rows),
    ):
        raise ValueError("max_cost_age_seconds must match rows")
    if report.max_manual_recheck_urgency != _max_decimal(
        tuple(row.manual_recheck_urgency for row in report.rows),
    ):
        raise ValueError("max_manual_recheck_urgency must match rows")
    if report.status != _rollup_status(tuple(row.status for row in report.rows)):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _require_rows(
    value: object,
) -> tuple[ResearchMarketFeeRegimeChangeWatchRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchMarketFeeRegimeChangeWatchRow:
            raise ValueError("rows must contain ResearchMarketFeeRegimeChangeWatchRow")
        _require_hard_flags("row", row)
        if row.screening_key in seen:
            raise ValueError("rows screening_key values must be unique")
        seen.add(row.screening_key)
    if tuple(row.screening_key for row in rows) != tuple(row.screening_key for row in sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted by status and screening_key")
    return rows


def _require_reason_code_counts(
    value: object,
) -> tuple[ResearchMarketFeeRegimeChangeWatchReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchMarketFeeRegimeChangeWatchReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason code count rows")
        _require_hard_flags("reason_code_count", row)
        if row.reason_code in seen:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen.add(row.reason_code)
    return rows


def _require_reason_codes(
    value: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not value:
        raise ValueError("reason_codes must be nonempty")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in value:
        _require_reason_code("reason_code", reason_code, allowed_values)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
        normalized.append(reason_code)
    return tuple(normalized)


def _require_reason_code(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> str:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a supported reason code")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")
    return value


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _is_safe_public_text(value):
        raise ValueError(f"{field_name} must be a safe public identifier")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains an unsafe public fragment")
    return value


def _is_safe_public_text(value: str) -> bool:
    if not value or len(value) > 96:
        return False
    if value[0] not in "abcdefghijklmnopqrstuvwxyz0123456789":
        return False
    return all(character in SAFE_TEXT_CHARS for character in value)


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole number")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most 1.000000")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _quantize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _quantize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANT)


def _require_greater(
    greater_field_name: str,
    greater_value: Decimal,
    lower_field_name: str,
    lower_value: Decimal,
) -> None:
    if greater_value <= lower_value:
        raise ValueError(f"{greater_field_name} must exceed {lower_field_name}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    return Decimal(str(delta.total_seconds())).quantize(QUANT)


def _abs_decimal(value: Decimal) -> Decimal:
    return abs(value).quantize(QUANT)


def _count(value: object) -> Decimal:
    return Decimal(str(value)).quantize(QUANT)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values).quantize(QUANT)


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be a Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return format(value, "f")
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal-derived strings")
    if type(value) is bool or value is None or type(value) is str:
        return value
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _derived_validation_digest(
    report: ResearchMarketFeeRegimeChangeWatchReport,
) -> str:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return _payload_validation_digest(payload)


def _payload_validation_digest(payload: dict[str, Any]) -> str:
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned_payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _require_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _reject_public_numerics(value: object) -> None:
    if isinstance(value, float) or type(value) is int:
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numerics(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numerics(item)


def _reject_unsafe_public_text(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_text(label, asdict(value))
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public field in {label}")
            _reject_unsafe_public_text(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_text(label, item)


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _require_public_payload_schema(payload: dict[str, Any]) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _require_exact_keys(
        "public payload",
        payload,
        (
            "generated_at",
            "config_version",
            "screening_count",
            "pass_count",
            "watch_count",
            "block_count",
            "max_taker_fee_delta_bps",
            "max_spread_cost_drift",
            "max_settlement_friction_drift",
            "max_cost_age_seconds",
            "max_manual_recheck_urgency",
            "status",
            "reason_codes",
            "reason_code_counts",
            "rows",
            "derived_validation_digest",
            "paper_only",
            "report_only",
            "readonly",
        ),
    )
    _require_public_row_schema(payload.get("rows"))
    _require_public_reason_code_count_schema(payload.get("reason_code_counts"))


def _require_public_row_schema(rows: object) -> None:
    if type(rows) is not list:
        raise ValueError("public payload rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("public payload rows must contain JSON objects")
        _require_exact_keys(
            "public payload row",
            row,
            (
                "screening_key",
                "status",
                "prior_taker_fee_bps",
                "current_taker_fee_bps",
                "taker_fee_delta_bps",
                "prior_spread_cost",
                "current_spread_cost",
                "spread_cost_drift",
                "prior_settlement_friction",
                "current_settlement_friction",
                "settlement_friction_drift",
                "cost_observed_at",
                "cost_age_seconds",
                "manual_recheck_urgency",
                "reason_codes",
                "paper_only",
                "report_only",
                "readonly",
            ),
        )


def _require_public_reason_code_count_schema(rows: object) -> None:
    if type(rows) is not list:
        raise ValueError("public payload reason_code_counts must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError(
                "public payload reason_code_counts must contain JSON objects",
            )
        _require_exact_keys(
            "public payload reason_code_count",
            row,
            (
                "reason_code",
                "count",
                "screening_ratio",
                "paper_only",
                "report_only",
                "readonly",
            ),
        )


def _require_exact_keys(
    label: str,
    value: dict[str, Any],
    expected_keys: tuple[str, ...],
) -> None:
    expected = set(expected_keys)
    actual = set(value)
    if actual != expected:
        raise ValueError(f"unexpected public payload field in {label}")
