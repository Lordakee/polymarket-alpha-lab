"""Pure public report for settlement cost refresh pressure."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Iterable, Mapping


DEFAULT_RESEARCH_MARKET_SETTLEMENT_COST_REFRESH_CONFIG_VERSION = (
    "research-market-settlement-cost-refresh-report-v0"
)

STATUSES = ("pass", "watch", "block")
STATUS_RANKS = {"block": 0, "watch": 1, "pass": 2}

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
PASS_REFRESH_PRESSURE_SCORE = Decimal("0.125000")
WATCH_REFRESH_PRESSURE_SCORE = Decimal("0.388889")
BLOCK_REFRESH_PRESSURE_SCORE = Decimal("1.000000")

CLEAR_REASON = "settlement_cost_refresh_clear"
FEE_WATCH_REASON = "sanitized_fee_watch"
FEE_BLOCK_REASON = "sanitized_fee_block"
SPREAD_WATCH_REASON = "sanitized_spread_watch"
SPREAD_BLOCK_REASON = "sanitized_spread_block"
SLIPPAGE_WATCH_REASON = "sanitized_slippage_watch"
SLIPPAGE_BLOCK_REASON = "sanitized_slippage_block"
FRICTION_WATCH_REASON = "settlement_friction_watch"
FRICTION_BLOCK_REASON = "settlement_friction_block"
QUOTE_AGE_WATCH_REASON = "quote_age_freshness_watch"
QUOTE_AGE_BLOCK_REASON = "quote_age_freshness_block"
COMPOSITE_WATCH_REASON = "composite_refresh_pressure_watch"
COMPOSITE_BLOCK_REASON = "composite_refresh_pressure_block"
EMPTY_INPUT_REASON = "settlement_cost_refresh_no_inputs"

FEE_REPORT_REASON = "sanitized_fee_pressure"
SPREAD_REPORT_REASON = "sanitized_spread_pressure"
SLIPPAGE_REPORT_REASON = "sanitized_slippage_pressure"
FRICTION_REPORT_REASON = "settlement_friction_pressure"
QUOTE_AGE_REPORT_REASON = "quote_age_freshness_pressure"
COMPOSITE_REPORT_REASON = "composite_refresh_pressure"

ROW_REASON_CODES = (
    CLEAR_REASON,
    FEE_WATCH_REASON,
    FEE_BLOCK_REASON,
    SPREAD_WATCH_REASON,
    SPREAD_BLOCK_REASON,
    SLIPPAGE_WATCH_REASON,
    SLIPPAGE_BLOCK_REASON,
    FRICTION_WATCH_REASON,
    FRICTION_BLOCK_REASON,
    QUOTE_AGE_WATCH_REASON,
    QUOTE_AGE_BLOCK_REASON,
    COMPOSITE_WATCH_REASON,
    COMPOSITE_BLOCK_REASON,
)
REPORT_REASON_CODES = (
    EMPTY_INPUT_REASON,
    FEE_REPORT_REASON,
    SPREAD_REPORT_REASON,
    SLIPPAGE_REPORT_REASON,
    FRICTION_REPORT_REASON,
    QUOTE_AGE_REPORT_REASON,
    COMPOSITE_REPORT_REASON,
)

PUBLIC_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "raw",
        "candidate_id",
        "condition_id",
        "market_id",
        "market-slug",
        "market_slug",
        "slug",
        "question",
        "url",
        "source_id",
        "source-ref",
        "source_ref",
        "source-url",
        "source_url",
        "source_text",
        _join_parts("d", "sn"),
        _join_parts("ta", "ble"),
        _join_parts("to", "ken"),
        "secret",
        "credential",
        "private_key",
        _join_parts("wal", "let"),
        _join_parts("au", "th"),
        _join_parts("or", "der"),
        _join_parts("tra", "de"),
        _join_parts("bu", "y"),
        _join_parts("se", "ll"),
        _join_parts("rec", "ommend"),
        _join_parts("siz", "ing"),
        _join_parts("li", "ve"),
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_MARKET_SETTLEMENT_COST_REFRESH_CONFIG_VERSION",
    "STATUSES",
    "ResearchMarketSettlementCostRefreshConfig",
    "ResearchMarketSettlementCostRefreshInput",
    "ResearchMarketSettlementCostRefreshReasonCodeCount",
    "ResearchMarketSettlementCostRefreshReport",
    "ResearchMarketSettlementCostRefreshRow",
    "build_research_market_settlement_cost_refresh_report",
    "research_market_settlement_cost_refresh_report_digest",
    "research_market_settlement_cost_refresh_report_payload",
)


class _NoSubclass:
    def __init_subclass__(cls) -> None:
        if _NoSubclass not in cls.__bases__:
            raise TypeError(f"{cls.__name__} does not support subclassing")


@dataclass(frozen=True)
class ResearchMarketSettlementCostRefreshConfig(_NoSubclass):
    config_version: str = DEFAULT_RESEARCH_MARKET_SETTLEMENT_COST_REFRESH_CONFIG_VERSION
    sanitized_fee_watch_ratio: Decimal = Decimal("0.010000")
    sanitized_fee_block_ratio: Decimal = Decimal("0.025000")
    sanitized_spread_watch_ratio: Decimal = Decimal("0.020000")
    sanitized_spread_block_ratio: Decimal = Decimal("0.050000")
    sanitized_slippage_watch_ratio: Decimal = Decimal("0.010000")
    sanitized_slippage_block_ratio: Decimal = Decimal("0.025000")
    settlement_friction_watch_ratio: Decimal = Decimal("0.010000")
    settlement_friction_block_ratio: Decimal = Decimal("0.030000")
    quote_age_watch_seconds: Decimal = Decimal("120.000000")
    quote_age_block_seconds: Decimal = Decimal("300.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketSettlementCostRefreshConfig, "config")
        _require_public_label("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_MARKET_SETTLEMENT_COST_REFRESH_CONFIG_VERSION:
            raise ValueError("config_version must match the supported value")
        for field_name in (
            "sanitized_fee_watch_ratio",
            "sanitized_fee_block_ratio",
            "sanitized_spread_watch_ratio",
            "sanitized_spread_block_ratio",
            "sanitized_slippage_watch_ratio",
            "sanitized_slippage_block_ratio",
            "settlement_friction_watch_ratio",
            "settlement_friction_block_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("quote_age_watch_seconds", "quote_age_block_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_threshold_pair(
            "sanitized_fee_watch_ratio",
            self.sanitized_fee_watch_ratio,
            "sanitized_fee_block_ratio",
            self.sanitized_fee_block_ratio,
        )
        _require_threshold_pair(
            "sanitized_spread_watch_ratio",
            self.sanitized_spread_watch_ratio,
            "sanitized_spread_block_ratio",
            self.sanitized_spread_block_ratio,
        )
        _require_threshold_pair(
            "sanitized_slippage_watch_ratio",
            self.sanitized_slippage_watch_ratio,
            "sanitized_slippage_block_ratio",
            self.sanitized_slippage_block_ratio,
        )
        _require_threshold_pair(
            "settlement_friction_watch_ratio",
            self.settlement_friction_watch_ratio,
            "settlement_friction_block_ratio",
            self.settlement_friction_block_ratio,
        )
        _require_threshold_pair(
            "quote_age_watch_seconds",
            self.quote_age_watch_seconds,
            "quote_age_block_seconds",
            self.quote_age_block_seconds,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketSettlementCostRefreshInput(_NoSubclass):
    public_cost_key: str
    sanitized_fee_ratio: Decimal
    sanitized_spread_ratio: Decimal
    sanitized_slippage_ratio: Decimal
    sanitized_settlement_friction_ratio: Decimal
    quote_age_seconds: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketSettlementCostRefreshInput, "input")
        _require_public_label("public_cost_key", self.public_cost_key)
        for field_name in (
            "sanitized_fee_ratio",
            "sanitized_spread_ratio",
            "sanitized_slippage_ratio",
            "sanitized_settlement_friction_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "quote_age_seconds",
            _require_nonnegative_decimal("quote_age_seconds", self.quote_age_seconds),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchMarketSettlementCostRefreshRow(_NoSubclass):
    public_cost_key: str
    sanitized_fee_ratio: Decimal
    sanitized_spread_ratio: Decimal
    sanitized_slippage_ratio: Decimal
    sanitized_settlement_friction_ratio: Decimal
    quote_age_seconds: Decimal
    refresh_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketSettlementCostRefreshRow, "row")
        _require_public_label("public_cost_key", self.public_cost_key)
        for field_name in (
            "sanitized_fee_ratio",
            "sanitized_spread_ratio",
            "sanitized_slippage_ratio",
            "sanitized_settlement_friction_ratio",
            "refresh_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "quote_age_seconds",
            _require_nonnegative_decimal("quote_age_seconds", self.quote_age_seconds),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                ROW_REASON_CODES,
            ),
        )
        _require_hard_flags("row", self)
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != _row_digest(self):
                raise ValueError("derived_validation_digest does not match row payload")
        else:
            object.__setattr__(self, "derived_validation_digest", _row_digest(self))
        _validate_row(self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchMarketSettlementCostRefreshReasonCodeCount(_NoSubclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketSettlementCostRefreshReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code(
            "reason_code",
            self.reason_code,
            ROW_REASON_CODES + REPORT_REASON_CODES,
        )
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketSettlementCostRefreshReport(_NoSubclass):
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    fee_pressure_count: Decimal
    spread_pressure_count: Decimal
    slippage_pressure_count: Decimal
    settlement_friction_pressure_count: Decimal
    quote_age_pressure_count: Decimal
    mean_sanitized_fee_ratio: Decimal
    mean_sanitized_spread_ratio: Decimal
    mean_sanitized_slippage_ratio: Decimal
    mean_sanitized_settlement_friction_ratio: Decimal
    mean_quote_age_seconds: Decimal
    mean_refresh_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchMarketSettlementCostRefreshReasonCodeCount, ...]
    rows: tuple[ResearchMarketSettlementCostRefreshRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketSettlementCostRefreshReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_MARKET_SETTLEMENT_COST_REFRESH_CONFIG_VERSION:
            raise ValueError("config_version must match the supported value")
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "fee_pressure_count",
            "spread_pressure_count",
            "slippage_pressure_count",
            "settlement_friction_pressure_count",
            "quote_age_pressure_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_sanitized_fee_ratio",
            "mean_sanitized_spread_ratio",
            "mean_sanitized_slippage_ratio",
            "mean_sanitized_settlement_friction_ratio",
            "mean_refresh_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "mean_quote_age_seconds",
            _require_nonnegative_decimal(
                "mean_quote_age_seconds",
                self.mean_quote_age_seconds,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != _report_digest(self):
                raise ValueError("derived_validation_digest does not match report payload")
        else:
            object.__setattr__(self, "derived_validation_digest", _report_digest(self))
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)

    @property
    def payload(self) -> dict[str, object]:
        return research_market_settlement_cost_refresh_report_payload(self)


def build_research_market_settlement_cost_refresh_report(
    inputs: Iterable[ResearchMarketSettlementCostRefreshInput],
    *,
    config: ResearchMarketSettlementCostRefreshConfig | None = None,
    generated_at: datetime,
) -> ResearchMarketSettlementCostRefreshReport:
    if config is None:
        config = ResearchMarketSettlementCostRefreshConfig()
    _require_exact_type(config, ResearchMarketSettlementCostRefreshConfig, "config")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (_row_from_input(item, config) for item in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchMarketSettlementCostRefreshReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=_decimal_count(len(normalized_inputs)),
        row_count=_decimal_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        fee_pressure_count=_reason_family_count(
            rows,
            (FEE_WATCH_REASON, FEE_BLOCK_REASON),
        ),
        spread_pressure_count=_reason_family_count(
            rows,
            (SPREAD_WATCH_REASON, SPREAD_BLOCK_REASON),
        ),
        slippage_pressure_count=_reason_family_count(
            rows,
            (SLIPPAGE_WATCH_REASON, SLIPPAGE_BLOCK_REASON),
        ),
        settlement_friction_pressure_count=_reason_family_count(
            rows,
            (FRICTION_WATCH_REASON, FRICTION_BLOCK_REASON),
        ),
        quote_age_pressure_count=_reason_family_count(
            rows,
            (QUOTE_AGE_WATCH_REASON, QUOTE_AGE_BLOCK_REASON),
        ),
        mean_sanitized_fee_ratio=_average(row.sanitized_fee_ratio for row in rows),
        mean_sanitized_spread_ratio=_average(row.sanitized_spread_ratio for row in rows),
        mean_sanitized_slippage_ratio=_average(
            row.sanitized_slippage_ratio for row in rows
        ),
        mean_sanitized_settlement_friction_ratio=_average(
            row.sanitized_settlement_friction_ratio for row in rows
        ),
        mean_quote_age_seconds=_average(row.quote_age_seconds for row in rows),
        mean_refresh_pressure_score=_average(row.refresh_pressure_score for row in rows),
        status=_report_status(rows),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        rows=rows,
    )


def research_market_settlement_cost_refresh_report_payload(
    report: ResearchMarketSettlementCostRefreshReport | Mapping[str, Any],
) -> dict[str, object]:
    if type(report) is ResearchMarketSettlementCostRefreshReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _report_payload(report, include_digest=True)
    elif isinstance(report, Mapping):
        _reject_unsafe_public_payload("payload", report, allow_json_containers=True)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchMarketSettlementCostRefreshReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    return payload


def research_market_settlement_cost_refresh_report_digest(
    report: ResearchMarketSettlementCostRefreshReport | Mapping[str, Any],
) -> str:
    return _payload_digest(research_market_settlement_cost_refresh_report_payload(report))


@dataclass(frozen=True)
class _DictFlags:
    value: Mapping[str, object]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _row_from_input(
    item: ResearchMarketSettlementCostRefreshInput,
    config: ResearchMarketSettlementCostRefreshConfig,
) -> ResearchMarketSettlementCostRefreshRow:
    reason_codes = _row_reason_codes(item, config)
    status = _status_from_reason_codes(reason_codes)
    return ResearchMarketSettlementCostRefreshRow(
        public_cost_key=item.public_cost_key,
        sanitized_fee_ratio=item.sanitized_fee_ratio,
        sanitized_spread_ratio=item.sanitized_spread_ratio,
        sanitized_slippage_ratio=item.sanitized_slippage_ratio,
        sanitized_settlement_friction_ratio=item.sanitized_settlement_friction_ratio,
        quote_age_seconds=item.quote_age_seconds,
        refresh_pressure_score=_refresh_pressure_score(status),
        status=status,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: ResearchMarketSettlementCostRefreshInput,
    config: ResearchMarketSettlementCostRefreshConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    reason_codes.append(
        _tiered_high_reason(
            item.sanitized_fee_ratio,
            watch_threshold=config.sanitized_fee_watch_ratio,
            block_threshold=config.sanitized_fee_block_ratio,
            watch_reason=FEE_WATCH_REASON,
            block_reason=FEE_BLOCK_REASON,
        ),
    )
    reason_codes.append(
        _tiered_high_reason(
            item.sanitized_spread_ratio,
            watch_threshold=config.sanitized_spread_watch_ratio,
            block_threshold=config.sanitized_spread_block_ratio,
            watch_reason=SPREAD_WATCH_REASON,
            block_reason=SPREAD_BLOCK_REASON,
        ),
    )
    reason_codes.append(
        _tiered_high_reason(
            item.sanitized_slippage_ratio,
            watch_threshold=config.sanitized_slippage_watch_ratio,
            block_threshold=config.sanitized_slippage_block_ratio,
            watch_reason=SLIPPAGE_WATCH_REASON,
            block_reason=SLIPPAGE_BLOCK_REASON,
        ),
    )
    reason_codes.append(
        _tiered_high_reason(
            item.sanitized_settlement_friction_ratio,
            watch_threshold=config.settlement_friction_watch_ratio,
            block_threshold=config.settlement_friction_block_ratio,
            watch_reason=FRICTION_WATCH_REASON,
            block_reason=FRICTION_BLOCK_REASON,
        ),
    )
    reason_codes.append(
        _tiered_high_reason(
            item.quote_age_seconds,
            watch_threshold=config.quote_age_watch_seconds,
            block_threshold=config.quote_age_block_seconds,
            watch_reason=QUOTE_AGE_WATCH_REASON,
            block_reason=QUOTE_AGE_BLOCK_REASON,
        ),
    )
    filtered = tuple(reason_code for reason_code in reason_codes if reason_code)
    if any(reason_code.endswith("_block") for reason_code in filtered):
        return filtered + (COMPOSITE_BLOCK_REASON,)
    if any(reason_code.endswith("_watch") for reason_code in filtered):
        return filtered + (COMPOSITE_WATCH_REASON,)
    return (CLEAR_REASON,)


def _tiered_high_reason(
    value: Decimal,
    *,
    watch_threshold: Decimal,
    block_threshold: Decimal,
    watch_reason: str,
    block_reason: str,
) -> str:
    if value >= block_threshold:
        return block_reason
    if value >= watch_threshold:
        return watch_reason
    return ""


def _refresh_pressure_score(status: str) -> Decimal:
    if status == "block":
        return BLOCK_REFRESH_PRESSURE_SCORE
    if status == "watch":
        return WATCH_REFRESH_PRESSURE_SCORE
    return PASS_REFRESH_PRESSURE_SCORE


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchMarketSettlementCostRefreshRow, ...]) -> str:
    if not rows:
        return "block"
    return min((row.status for row in rows), key=lambda status: STATUS_RANKS[status])


def _report_reason_codes(
    rows: tuple[ResearchMarketSettlementCostRefreshRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_INPUT_REASON,)
    reason_codes: list[str] = []
    if _reason_family_count(rows, (FEE_WATCH_REASON, FEE_BLOCK_REASON)) > ZERO:
        reason_codes.append(FEE_REPORT_REASON)
    if _reason_family_count(rows, (SPREAD_WATCH_REASON, SPREAD_BLOCK_REASON)) > ZERO:
        reason_codes.append(SPREAD_REPORT_REASON)
    if _reason_family_count(rows, (SLIPPAGE_WATCH_REASON, SLIPPAGE_BLOCK_REASON)) > ZERO:
        reason_codes.append(SLIPPAGE_REPORT_REASON)
    if _reason_family_count(rows, (FRICTION_WATCH_REASON, FRICTION_BLOCK_REASON)) > ZERO:
        reason_codes.append(FRICTION_REPORT_REASON)
    if (
        _reason_family_count(rows, (QUOTE_AGE_WATCH_REASON, QUOTE_AGE_BLOCK_REASON))
        > ZERO
    ):
        reason_codes.append(QUOTE_AGE_REPORT_REASON)
    if _reason_family_count(rows, (COMPOSITE_WATCH_REASON, COMPOSITE_BLOCK_REASON)) > ZERO:
        reason_codes.append(COMPOSITE_REPORT_REASON)
    return tuple(reason_codes) or (EMPTY_INPUT_REASON,)


def _reason_code_counts(
    rows: tuple[ResearchMarketSettlementCostRefreshRow, ...],
    report_reason_codes: tuple[str, ...],
) -> tuple[ResearchMarketSettlementCostRefreshReasonCodeCount, ...]:
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    counts.update(report_reason_codes)
    denominator = _decimal_count(len(rows)) if rows else ONE
    reason_sequence = REPORT_REASON_CODES + ROW_REASON_CODES
    return tuple(
        ResearchMarketSettlementCostRefreshReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
            row_ratio=_ratio(_decimal_count(counts[reason_code]), denominator),
        )
        for reason_code in reason_sequence
        if counts[reason_code]
    )


def _row_sort_key(row: ResearchMarketSettlementCostRefreshRow) -> tuple[int, str]:
    return (STATUS_RANKS[row.status], row.public_cost_key)


def _validate_row(row: ResearchMarketSettlementCostRefreshRow) -> None:
    expected_status = _status_from_reason_codes(row.reason_codes)
    if row.status != expected_status:
        raise ValueError("status must match reason_codes")
    if row.refresh_pressure_score != _refresh_pressure_score(row.status):
        raise ValueError("refresh_pressure_score must match status")
    if row.status == "pass" and row.reason_codes != (CLEAR_REASON,):
        raise ValueError("pass rows must use the clear reason")
    if row.status != "pass" and CLEAR_REASON in row.reason_codes:
        raise ValueError("non-pass rows must not use the clear reason")


def _validate_report(report: ResearchMarketSettlementCostRefreshReport) -> None:
    if report.input_count != _decimal_count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    for field_name, status in (
        ("pass_count", "pass"),
        ("watch_count", "watch"),
        ("block_count", "block"),
    ):
        if getattr(report, field_name) != _status_count(report.rows, status):
            raise ValueError(f"{field_name} must match rows")
    for field_name, reason_family in (
        ("fee_pressure_count", (FEE_WATCH_REASON, FEE_BLOCK_REASON)),
        ("spread_pressure_count", (SPREAD_WATCH_REASON, SPREAD_BLOCK_REASON)),
        ("slippage_pressure_count", (SLIPPAGE_WATCH_REASON, SLIPPAGE_BLOCK_REASON)),
        (
            "settlement_friction_pressure_count",
            (FRICTION_WATCH_REASON, FRICTION_BLOCK_REASON),
        ),
        ("quote_age_pressure_count", (QUOTE_AGE_WATCH_REASON, QUOTE_AGE_BLOCK_REASON)),
    ):
        if getattr(report, field_name) != _reason_family_count(report.rows, reason_family):
            raise ValueError(f"{field_name} must match rows")
    for field_name, row_field in (
        ("mean_sanitized_fee_ratio", "sanitized_fee_ratio"),
        ("mean_sanitized_spread_ratio", "sanitized_spread_ratio"),
        ("mean_sanitized_slippage_ratio", "sanitized_slippage_ratio"),
        (
            "mean_sanitized_settlement_friction_ratio",
            "sanitized_settlement_friction_ratio",
        ),
        ("mean_quote_age_seconds", "quote_age_seconds"),
        ("mean_refresh_pressure_score", "refresh_pressure_score"),
    ):
        if getattr(report, field_name) != _average(
            getattr(row, row_field) for row in report.rows
        ):
            raise ValueError(f"{field_name} must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _normalize_inputs(
    inputs: Iterable[ResearchMarketSettlementCostRefreshInput],
) -> tuple[ResearchMarketSettlementCostRefreshInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Iterable):
        raise ValueError("inputs must be an iterable")
    normalized: list[ResearchMarketSettlementCostRefreshInput] = []
    seen_keys: set[str] = set()
    for item in inputs:
        _require_exact_type(item, ResearchMarketSettlementCostRefreshInput, "input")
        if item.public_cost_key in seen_keys:
            raise ValueError("public_cost_key values must be unique")
        seen_keys.add(item.public_cost_key)
        normalized.append(item)
    return tuple(normalized)


def _normalize_rows(
    rows: tuple[ResearchMarketSettlementCostRefreshRow, ...],
) -> tuple[ResearchMarketSettlementCostRefreshRow, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    for row in rows:
        _require_exact_type(row, ResearchMarketSettlementCostRefreshRow, "row")
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be in deterministic public sort")
    return rows


def _normalize_reason_code_counts(
    reason_code_counts: tuple[ResearchMarketSettlementCostRefreshReasonCodeCount, ...],
) -> tuple[ResearchMarketSettlementCostRefreshReasonCodeCount, ...]:
    if not isinstance(reason_code_counts, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    for item in reason_code_counts:
        _require_exact_type(
            item,
            ResearchMarketSettlementCostRefreshReasonCodeCount,
            "reason_code_count",
        )
    return reason_code_counts


def _normalize_reason_codes(
    name: str,
    reason_codes: tuple[str, ...],
    allowed_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if not isinstance(reason_codes, tuple) or not reason_codes:
        raise ValueError(f"{name} must be a non-empty tuple")
    normalized: list[str] = []
    seen_codes: set[str] = set()
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code, allowed_reason_codes)
        if reason_code not in seen_codes:
            normalized.append(reason_code)
            seen_codes.add(reason_code)
    return tuple(normalized)


def _require_reason_code(
    name: str,
    value: str,
    allowed_reason_codes: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_reason_codes:
        raise ValueError(f"{name} must be supported")


def _require_status(name: str, value: str) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{name} must be one of pass, watch, block")


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be {expected_type.__name__}")


def _require_public_label(name: str, value: str) -> None:
    if type(value) is not str or not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{name} must be a public label")
    if any(fragment in value.lower() for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{name} contains unsafe public text")


def _require_threshold_pair(
    watch_name: str,
    watch_value: Decimal,
    block_name: str,
    block_value: Decimal,
) -> None:
    if block_value <= watch_value:
        raise ValueError(f"{block_name} must exceed {watch_name}")


def _require_decimal(name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _require_nonnegative_decimal(name: str, value: Decimal) -> Decimal:
    value = _require_decimal(name, value)
    if value < ZERO:
        raise ValueError(f"{name} must be non-negative")
    return value


def _require_ratio_decimal(name: str, value: Decimal) -> Decimal:
    value = _require_decimal(name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{name} must be between 0.000000 and 1.000000")
    return value


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} must be readonly")


def _as_utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_digest(name: str, value: str) -> None:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{name} must be a sha256 hex digest")


def _status_count(
    rows: tuple[ResearchMarketSettlementCostRefreshRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _reason_family_count(
    rows: tuple[ResearchMarketSettlementCostRefreshRow, ...],
    reason_family: tuple[str, ...],
) -> Decimal:
    return _decimal_count(
        sum(1 for row in rows if any(reason in row.reason_codes for reason in reason_family)),
    )


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return (numerator / denominator).quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _average(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return (sum(items, ZERO) / _decimal_count(len(items))).quantize(
        QUANTUM,
        rounding=ROUND_HALF_UP,
    )


def _row_digest(row: ResearchMarketSettlementCostRefreshRow) -> str:
    return _payload_digest(_dataclass_payload(row, exclude=("derived_validation_digest",)))


def _report_digest(report: ResearchMarketSettlementCostRefreshReport) -> str:
    return _payload_digest(_report_payload(report, include_digest=False))


def _payload_digest(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(
        _json_ready(payload),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _report_payload(
    report: ResearchMarketSettlementCostRefreshReport,
    *,
    include_digest: bool,
) -> dict[str, object]:
    payload: dict[str, object] = {}
    for field in fields(report):
        if field.name == "derived_validation_digest" and not include_digest:
            continue
        value = getattr(report, field.name)
        if field.name == "reason_code_counts":
            payload[field.name] = [
                _dataclass_payload(item) for item in report.reason_code_counts
            ]
        elif field.name == "rows":
            payload[field.name] = [_dataclass_payload(row) for row in report.rows]
        else:
            payload[field.name] = _json_ready(value)
    return payload


def _dataclass_payload(
    value: object,
    *,
    exclude: tuple[str, ...] = (),
) -> dict[str, object]:
    if not is_dataclass(value) or isinstance(value, type):
        raise ValueError("value must be a dataclass instance")
    excluded = set(exclude)
    payload: dict[str, object] = {}
    for field in fields(value):
        if field.name in excluded:
            continue
        payload[field.name] = _json_ready(getattr(value, field.name))
    return payload


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _dataclass_payload(value)
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(value.quantize(QUANTUM, rounding=ROUND_HALF_UP))
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int:
        raise ValueError("JSON value must not be an int")
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(
            label,
            asdict(value),
            allow_json_containers=True,
        )
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} keys must be strings")
            if any(fragment in key.lower() for fragment in UNSAFE_PUBLIC_FRAGMENTS):
                raise ValueError(f"{label} contains unsafe public field")
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        if any(fragment in value.lower() for fragment in UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError(f"{label} contains unsafe public text")
        return
    if allow_json_containers and (value is None or type(value) is bool):
        return
    if isinstance(value, (Decimal, datetime)) or value is None or type(value) is bool:
        return
    if allow_json_containers and (type(value) is int or isinstance(value, float)):
        return
    raise ValueError(f"{label} contains unsupported public value")
