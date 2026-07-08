"""Pure fee drag threshold breach report for sanitized research cost inputs."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, localcontext
import hashlib
import json
import re
from typing import Any


__all__ = (
    "FEE_DRAG_THRESHOLD_BREACH_STATUSES",
    "DEFAULT_RESEARCH_MARKET_FEE_DRAG_THRESHOLD_BREACH_REPORT_CONFIG_VERSION",
    "ResearchMarketFeeDragThresholdBreachConfig",
    "ResearchMarketFeeDragThresholdBreachInput",
    "ResearchMarketFeeDragThresholdBreachReasonCodeCount",
    "ResearchMarketFeeDragThresholdBreachReport",
    "ResearchMarketFeeDragThresholdBreachRow",
    "build_research_market_fee_drag_threshold_breach_report",
    "research_market_fee_drag_threshold_breach_report_digest",
    "research_market_fee_drag_threshold_breach_report_payload",
    "validate_research_market_fee_drag_threshold_breach_report_payload",
)


DEFAULT_RESEARCH_MARKET_FEE_DRAG_THRESHOLD_BREACH_REPORT_CONFIG_VERSION = (
    "research-market-fee-drag-threshold-breach-report-v0"
)
FEE_DRAG_THRESHOLD_BREACH_STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
PUBLIC_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
REASON_CODE_RE = re.compile(r"^[a-z0-9][a-z0-9_]{0,127}$")
UNSAFE_PUBLIC_FRAGMENTS = (
    "raw",
    "candidate_id",
    "condition_id",
    "market_id",
    "market_slug",
    "question",
    "url",
    "source",
    "dsn",
    "table_name",
    "tok" + "en",
    "secret",
    "credential",
    "private_key",
    "data" + "base",
    "net" + "work",
    "au" + "th",
    "wal" + "let",
    "or" + "der",
    "tra" + "de",
    "li" + "ve",
    "reco" + "mmend",
    "siz" + "ing",
    "b" + "uy",
    "s" + "ell",
)
COMPONENT_REASON_PRIORITY = (
    "total_fee_drag_block",
    "fee_component_drag_block",
    "spread_component_drag_block",
    "settlement_cost_block",
    "transfer_cost_block",
    "fee_cost_freshness_block",
    "spread_cost_freshness_block",
    "settlement_cost_freshness_block",
    "transfer_cost_freshness_block",
    "total_fee_drag_watch",
    "fee_component_drag_watch",
    "spread_component_drag_watch",
    "settlement_cost_watch",
    "transfer_cost_watch",
    "fee_cost_freshness_watch",
    "spread_cost_freshness_watch",
    "settlement_cost_freshness_watch",
    "transfer_cost_freshness_watch",
)
PAYLOAD_STATUS_KEYS = frozenset(("status",))
PAYLOAD_FLAG_KEYS = frozenset(("paper_only", "report_only", "readonly"))


class _Missing:
    pass


MISSING = _Missing()


@dataclass(frozen=True)
class ResearchMarketFeeDragThresholdBreachConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_FEE_DRAG_THRESHOLD_BREACH_REPORT_CONFIG_VERSION
    )
    max_pass_total_fee_drag_rate: Decimal = Decimal("0.020000")
    max_watch_total_fee_drag_rate: Decimal = Decimal("0.060000")
    max_pass_fee_drag_rate: Decimal = Decimal("0.010000")
    max_watch_fee_drag_rate: Decimal = Decimal("0.030000")
    max_pass_spread_drag_rate: Decimal = Decimal("0.005000")
    max_watch_spread_drag_rate: Decimal = Decimal("0.020000")
    max_pass_settlement_cost_rate: Decimal = Decimal("0.003000")
    max_watch_settlement_cost_rate: Decimal = Decimal("0.010000")
    max_pass_transfer_cost_rate: Decimal = Decimal("0.002000")
    max_watch_transfer_cost_rate: Decimal = Decimal("0.008000")
    max_pass_fee_quote_age_seconds: Decimal = Decimal("3600.000000")
    max_watch_fee_quote_age_seconds: Decimal = Decimal("14400.000000")
    max_pass_spread_quote_age_seconds: Decimal = Decimal("300.000000")
    max_watch_spread_quote_age_seconds: Decimal = Decimal("1200.000000")
    max_pass_settlement_quote_age_seconds: Decimal = Decimal("86400.000000")
    max_watch_settlement_quote_age_seconds: Decimal = Decimal("172800.000000")
    max_pass_transfer_quote_age_seconds: Decimal = Decimal("86400.000000")
    max_watch_transfer_quote_age_seconds: Decimal = Decimal("172800.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketFeeDragThresholdBreachConfig, "config")
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_FEE_DRAG_THRESHOLD_BREACH_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match the active value")
        for name in (
            "max_pass_total_fee_drag_rate",
            "max_watch_total_fee_drag_rate",
            "max_pass_fee_drag_rate",
            "max_watch_fee_drag_rate",
            "max_pass_spread_drag_rate",
            "max_watch_spread_drag_rate",
            "max_pass_settlement_cost_rate",
            "max_watch_settlement_cost_rate",
            "max_pass_transfer_cost_rate",
            "max_watch_transfer_cost_rate",
        ):
            object.__setattr__(
                self,
                name,
                _require_ratio_decimal(name, getattr(self, name)),
            )
        for name in (
            "max_pass_fee_quote_age_seconds",
            "max_watch_fee_quote_age_seconds",
            "max_pass_spread_quote_age_seconds",
            "max_watch_spread_quote_age_seconds",
            "max_pass_settlement_quote_age_seconds",
            "max_watch_settlement_quote_age_seconds",
            "max_pass_transfer_quote_age_seconds",
            "max_watch_transfer_quote_age_seconds",
        ):
            object.__setattr__(
                self,
                name,
                _require_positive_decimal(name, getattr(self, name)),
            )
        _require_not_above(
            "max_pass_total_fee_drag_rate",
            self.max_pass_total_fee_drag_rate,
            self.max_watch_total_fee_drag_rate,
        )
        _require_not_above(
            "max_pass_fee_drag_rate",
            self.max_pass_fee_drag_rate,
            self.max_watch_fee_drag_rate,
        )
        _require_not_above(
            "max_pass_spread_drag_rate",
            self.max_pass_spread_drag_rate,
            self.max_watch_spread_drag_rate,
        )
        _require_not_above(
            "max_pass_settlement_cost_rate",
            self.max_pass_settlement_cost_rate,
            self.max_watch_settlement_cost_rate,
        )
        _require_not_above(
            "max_pass_transfer_cost_rate",
            self.max_pass_transfer_cost_rate,
            self.max_watch_transfer_cost_rate,
        )
        _require_not_above(
            "max_pass_fee_quote_age_seconds",
            self.max_pass_fee_quote_age_seconds,
            self.max_watch_fee_quote_age_seconds,
        )
        _require_not_above(
            "max_pass_spread_quote_age_seconds",
            self.max_pass_spread_quote_age_seconds,
            self.max_watch_spread_quote_age_seconds,
        )
        _require_not_above(
            "max_pass_settlement_quote_age_seconds",
            self.max_pass_settlement_quote_age_seconds,
            self.max_watch_settlement_quote_age_seconds,
        )
        _require_not_above(
            "max_pass_transfer_quote_age_seconds",
            self.max_pass_transfer_quote_age_seconds,
            self.max_watch_transfer_quote_age_seconds,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketFeeDragThresholdBreachInput:
    research_key: str
    fee_drag_rate: Decimal
    spread_drag_rate: Decimal
    settlement_cost_rate: Decimal
    transfer_cost_rate: Decimal
    fee_quote_age_seconds: Decimal
    spread_quote_age_seconds: Decimal
    settlement_quote_age_seconds: Decimal
    transfer_quote_age_seconds: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketFeeDragThresholdBreachInput, "input")
        _require_public_label("research_key", self.research_key)
        for name in (
            "fee_drag_rate",
            "spread_drag_rate",
            "settlement_cost_rate",
            "transfer_cost_rate",
        ):
            object.__setattr__(
                self,
                name,
                _require_ratio_decimal(name, getattr(self, name)),
            )
        for name in (
            "fee_quote_age_seconds",
            "spread_quote_age_seconds",
            "settlement_quote_age_seconds",
            "transfer_quote_age_seconds",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchMarketFeeDragThresholdBreachRow:
    research_key: str
    fee_drag_rate: Decimal
    spread_drag_rate: Decimal
    settlement_cost_rate: Decimal
    transfer_cost_rate: Decimal
    total_fee_drag_rate: Decimal
    fee_quote_age_seconds: Decimal
    spread_quote_age_seconds: Decimal
    settlement_quote_age_seconds: Decimal
    transfer_quote_age_seconds: Decimal
    fee_component_pressure_score: Decimal
    spread_component_pressure_score: Decimal
    settlement_cost_pressure_score: Decimal
    transfer_cost_pressure_score: Decimal
    fee_cost_freshness_pressure_score: Decimal
    spread_cost_freshness_pressure_score: Decimal
    settlement_cost_freshness_pressure_score: Decimal
    transfer_cost_freshness_pressure_score: Decimal
    fee_drag_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketFeeDragThresholdBreachRow, "row")
        _require_public_label("research_key", self.research_key)
        for name in (
            "fee_drag_rate",
            "spread_drag_rate",
            "settlement_cost_rate",
            "transfer_cost_rate",
        ):
            object.__setattr__(
                self,
                name,
                _require_ratio_decimal(name, getattr(self, name)),
            )
        object.__setattr__(
            self,
            "total_fee_drag_rate",
            _require_nonnegative_decimal("total_fee_drag_rate", self.total_fee_drag_rate),
        )
        for name in (
            "fee_component_pressure_score",
            "spread_component_pressure_score",
            "settlement_cost_pressure_score",
            "transfer_cost_pressure_score",
            "fee_cost_freshness_pressure_score",
            "spread_cost_freshness_pressure_score",
            "settlement_cost_freshness_pressure_score",
            "transfer_cost_freshness_pressure_score",
            "fee_drag_pressure_score",
        ):
            object.__setattr__(
                self,
                name,
                _require_ratio_decimal(name, getattr(self, name)),
            )
        for name in (
            "fee_quote_age_seconds",
            "spread_quote_age_seconds",
            "settlement_quote_age_seconds",
            "transfer_quote_age_seconds",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchMarketFeeDragThresholdBreachReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketFeeDragThresholdBreachReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_fee_drag_pressure_score: Decimal | None
    max_total_fee_drag_rate: Decimal
    max_fee_drag_rate: Decimal
    max_spread_drag_rate: Decimal
    max_settlement_cost_rate: Decimal
    max_transfer_cost_rate: Decimal
    max_fee_quote_age_seconds: Decimal
    max_spread_quote_age_seconds: Decimal
    max_settlement_quote_age_seconds: Decimal
    max_transfer_quote_age_seconds: Decimal
    status: str
    rows: tuple[ResearchMarketFeeDragThresholdBreachRow, ...]
    reason_code_counts: tuple[ResearchMarketFeeDragThresholdBreachReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketFeeDragThresholdBreachReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        for name in ("input_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_whole_decimal(name, getattr(self, name)),
            )
        object.__setattr__(
            self,
            "average_fee_drag_pressure_score",
            _require_optional_ratio_decimal(
                "average_fee_drag_pressure_score",
                self.average_fee_drag_pressure_score,
            ),
        )
        for name in (
            "max_fee_drag_rate",
            "max_spread_drag_rate",
            "max_settlement_cost_rate",
            "max_transfer_cost_rate",
        ):
            object.__setattr__(
                self,
                name,
                _require_ratio_decimal(name, getattr(self, name)),
            )
        object.__setattr__(
            self,
            "max_total_fee_drag_rate",
            _require_nonnegative_decimal(
                "max_total_fee_drag_rate",
                self.max_total_fee_drag_rate,
            ),
        )
        for name in (
            "max_fee_quote_age_seconds",
            "max_spread_quote_age_seconds",
            "max_settlement_quote_age_seconds",
            "max_transfer_quote_age_seconds",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)


def build_research_market_fee_drag_threshold_breach_report(
    inputs: Iterable[object],
    *,
    config: ResearchMarketFeeDragThresholdBreachConfig,
    generated_at: datetime,
) -> ResearchMarketFeeDragThresholdBreachReport:
    if type(config) is not ResearchMarketFeeDragThresholdBreachConfig:
        raise ValueError("config must be a ResearchMarketFeeDragThresholdBreachConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_items = _normalize_inputs(inputs)
    rows = tuple(
        _row_from_input(item, config=config)
        for item in sorted(input_items, key=lambda item: item.research_key)
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchMarketFeeDragThresholdBreachReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_fee_drag_pressure_score=_average_fee_drag_pressure_score(rows),
        max_total_fee_drag_rate=_maximum_row_value(rows, "total_fee_drag_rate"),
        max_fee_drag_rate=_maximum_row_value(rows, "fee_drag_rate"),
        max_spread_drag_rate=_maximum_row_value(rows, "spread_drag_rate"),
        max_settlement_cost_rate=_maximum_row_value(rows, "settlement_cost_rate"),
        max_transfer_cost_rate=_maximum_row_value(rows, "transfer_cost_rate"),
        max_fee_quote_age_seconds=_maximum_row_value(rows, "fee_quote_age_seconds"),
        max_spread_quote_age_seconds=_maximum_row_value(
            rows,
            "spread_quote_age_seconds",
        ),
        max_settlement_quote_age_seconds=_maximum_row_value(
            rows,
            "settlement_quote_age_seconds",
        ),
        max_transfer_quote_age_seconds=_maximum_row_value(
            rows,
            "transfer_quote_age_seconds",
        ),
        status=_summary_status(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_market_fee_drag_threshold_breach_report_payload(
    report: ResearchMarketFeeDragThresholdBreachReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketFeeDragThresholdBreachReport:
        raise ValueError("report must be a ResearchMarketFeeDragThresholdBreachReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    return validate_research_market_fee_drag_threshold_breach_report_payload(payload)


def research_market_fee_drag_threshold_breach_report_digest(
    report: ResearchMarketFeeDragThresholdBreachReport,
) -> str:
    payload = research_market_fee_drag_threshold_breach_report_payload(report)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def validate_research_market_fee_drag_threshold_breach_report_payload(
    payload: dict[str, Any],
    *,
    expected_digest: str | None = None,
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")
    _validate_payload_value(payload)
    if expected_digest is not None:
        if type(expected_digest) is not str or not re.fullmatch(
            r"[0-9a-f]{64}",
            expected_digest,
        ):
            raise ValueError("expected_digest must be a SHA-256 hex digest")
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
        if digest != expected_digest:
            raise ValueError("payload digest mismatch")
    return payload


def _row_from_input(
    item: ResearchMarketFeeDragThresholdBreachInput,
    *,
    config: ResearchMarketFeeDragThresholdBreachConfig,
) -> ResearchMarketFeeDragThresholdBreachRow:
    total_fee_drag_rate = _quantize(
        item.fee_drag_rate
        + item.spread_drag_rate
        + item.settlement_cost_rate
        + item.transfer_cost_rate,
    )
    pressure_scores = _fee_drag_pressure_scores(item, config=config)
    return ResearchMarketFeeDragThresholdBreachRow(
        research_key=item.research_key,
        fee_drag_rate=item.fee_drag_rate,
        spread_drag_rate=item.spread_drag_rate,
        settlement_cost_rate=item.settlement_cost_rate,
        transfer_cost_rate=item.transfer_cost_rate,
        total_fee_drag_rate=total_fee_drag_rate,
        fee_quote_age_seconds=item.fee_quote_age_seconds,
        spread_quote_age_seconds=item.spread_quote_age_seconds,
        settlement_quote_age_seconds=item.settlement_quote_age_seconds,
        transfer_quote_age_seconds=item.transfer_quote_age_seconds,
        fee_component_pressure_score=pressure_scores[0],
        spread_component_pressure_score=pressure_scores[1],
        settlement_cost_pressure_score=pressure_scores[2],
        transfer_cost_pressure_score=pressure_scores[3],
        fee_cost_freshness_pressure_score=pressure_scores[4],
        spread_cost_freshness_pressure_score=pressure_scores[5],
        settlement_cost_freshness_pressure_score=pressure_scores[6],
        transfer_cost_freshness_pressure_score=pressure_scores[7],
        fee_drag_pressure_score=_average(pressure_scores),
        status=_row_status(item, total_fee_drag_rate, config=config),
        reason_codes=_row_reason_codes(item, total_fee_drag_rate, config=config),
    )


def _fee_drag_pressure_scores(
    item: ResearchMarketFeeDragThresholdBreachInput,
    *,
    config: ResearchMarketFeeDragThresholdBreachConfig,
) -> tuple[Decimal, ...]:
    return (
        _pressure_ratio(item.fee_drag_rate, config.max_watch_fee_drag_rate),
        _pressure_ratio(item.spread_drag_rate, config.max_watch_spread_drag_rate),
        _pressure_ratio(
            item.settlement_cost_rate,
            config.max_watch_settlement_cost_rate,
        ),
        _pressure_ratio(
            item.transfer_cost_rate,
            config.max_watch_transfer_cost_rate,
        ),
        _pressure_ratio(
            item.fee_quote_age_seconds,
            config.max_watch_fee_quote_age_seconds,
        ),
        _pressure_ratio(
            item.spread_quote_age_seconds,
            config.max_watch_spread_quote_age_seconds,
        ),
        _pressure_ratio(
            item.settlement_quote_age_seconds,
            config.max_watch_settlement_quote_age_seconds,
        ),
        _pressure_ratio(
            item.transfer_quote_age_seconds,
            config.max_watch_transfer_quote_age_seconds,
        ),
    )


def _pressure_ratio(value: Decimal, watch_value: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = 28
        score = value / watch_value
    if score < ZERO:
        return ZERO
    if score > ONE:
        return ONE
    return _quantize(score)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _row_status(
    item: ResearchMarketFeeDragThresholdBreachInput,
    total_fee_drag_rate: Decimal,
    *,
    config: ResearchMarketFeeDragThresholdBreachConfig,
) -> str:
    statuses = _dimension_statuses(item, total_fee_drag_rate, config=config)
    if "block" in statuses:
        return "block"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _dimension_statuses(
    item: ResearchMarketFeeDragThresholdBreachInput,
    total_fee_drag_rate: Decimal,
    *,
    config: ResearchMarketFeeDragThresholdBreachConfig,
) -> tuple[str, ...]:
    return (
        _max_threshold_status(
            total_fee_drag_rate,
            pass_value=config.max_pass_total_fee_drag_rate,
            watch_value=config.max_watch_total_fee_drag_rate,
        ),
        _max_threshold_status(
            item.fee_drag_rate,
            pass_value=config.max_pass_fee_drag_rate,
            watch_value=config.max_watch_fee_drag_rate,
        ),
        _max_threshold_status(
            item.spread_drag_rate,
            pass_value=config.max_pass_spread_drag_rate,
            watch_value=config.max_watch_spread_drag_rate,
        ),
        _max_threshold_status(
            item.settlement_cost_rate,
            pass_value=config.max_pass_settlement_cost_rate,
            watch_value=config.max_watch_settlement_cost_rate,
        ),
        _max_threshold_status(
            item.transfer_cost_rate,
            pass_value=config.max_pass_transfer_cost_rate,
            watch_value=config.max_watch_transfer_cost_rate,
        ),
        _max_threshold_status(
            item.fee_quote_age_seconds,
            pass_value=config.max_pass_fee_quote_age_seconds,
            watch_value=config.max_watch_fee_quote_age_seconds,
        ),
        _max_threshold_status(
            item.spread_quote_age_seconds,
            pass_value=config.max_pass_spread_quote_age_seconds,
            watch_value=config.max_watch_spread_quote_age_seconds,
        ),
        _max_threshold_status(
            item.settlement_quote_age_seconds,
            pass_value=config.max_pass_settlement_quote_age_seconds,
            watch_value=config.max_watch_settlement_quote_age_seconds,
        ),
        _max_threshold_status(
            item.transfer_quote_age_seconds,
            pass_value=config.max_pass_transfer_quote_age_seconds,
            watch_value=config.max_watch_transfer_quote_age_seconds,
        ),
    )


def _row_reason_codes(
    item: ResearchMarketFeeDragThresholdBreachInput,
    total_fee_drag_rate: Decimal,
    *,
    config: ResearchMarketFeeDragThresholdBreachConfig,
) -> tuple[str, ...]:
    status = _row_status(item, total_fee_drag_rate, config=config)
    (
        total_status,
        fee_status,
        spread_status,
        settlement_status,
        transfer_status,
        fee_age_status,
        spread_age_status,
        settlement_age_status,
        transfer_age_status,
    ) = _dimension_statuses(item, total_fee_drag_rate, config=config)
    codes = {
        f"fee_drag_threshold_breach_{status}",
        f"total_fee_drag_{total_status}",
        f"fee_component_drag_{fee_status}",
        f"spread_component_drag_{spread_status}",
        f"settlement_cost_{settlement_status}",
        f"transfer_cost_{transfer_status}",
        f"fee_cost_freshness_{fee_age_status}",
        f"spread_cost_freshness_{spread_age_status}",
        f"settlement_cost_freshness_{settlement_age_status}",
        f"transfer_cost_freshness_{transfer_age_status}",
    }
    for code in item.reason_codes:
        codes.add(f"input_{code}")
    return tuple(sorted(codes))


def _max_threshold_status(value: Decimal, *, pass_value: Decimal, watch_value: Decimal) -> str:
    if value > watch_value:
        return "block"
    if value > pass_value:
        return "watch"
    return "pass"


def _normalize_inputs(
    inputs: Iterable[object],
) -> tuple[ResearchMarketFeeDragThresholdBreachInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        values = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    return tuple(_coerce_input(value) for value in values)


def _coerce_input(value: object) -> ResearchMarketFeeDragThresholdBreachInput:
    if type(value) is ResearchMarketFeeDragThresholdBreachInput:
        _require_hard_flags("input", value)
        return value
    _require_hard_flags("input", value)
    return ResearchMarketFeeDragThresholdBreachInput(
        research_key=_field_value(value, "research_key"),
        fee_drag_rate=_field_value(value, "fee_drag_rate"),
        spread_drag_rate=_field_value(value, "spread_drag_rate"),
        settlement_cost_rate=_field_value(value, "settlement_cost_rate"),
        transfer_cost_rate=_field_value(value, "transfer_cost_rate"),
        fee_quote_age_seconds=_field_value(value, "fee_quote_age_seconds"),
        spread_quote_age_seconds=_field_value(value, "spread_quote_age_seconds"),
        settlement_quote_age_seconds=_field_value(
            value,
            "settlement_quote_age_seconds",
        ),
        transfer_quote_age_seconds=_field_value(value, "transfer_quote_age_seconds"),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _summary_reason_codes(
    rows: tuple[ResearchMarketFeeDragThresholdBreachRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_fee_drag_threshold_breach_inputs",)
    if all(row.status == "pass" for row in rows):
        return ("fee_drag_threshold_breach_pass",)
    codes: list[str] = []
    if any(row.status == "block" for row in rows):
        codes.append("fee_drag_threshold_breach_block")
    elif any(row.status == "watch" for row in rows):
        codes.append("fee_drag_threshold_breach_watch")
    row_codes = {code for row in rows for code in row.reason_codes}
    for code in COMPONENT_REASON_PRIORITY:
        if code in row_codes:
            codes.append(code)
    return tuple(codes)


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("no_fee_drag_threshold_breach_inputs",):
        return "block"
    if "fee_drag_threshold_breach_block" in reason_codes:
        return "block"
    if "fee_drag_threshold_breach_watch" in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchMarketFeeDragThresholdBreachRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchMarketFeeDragThresholdBreachReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketFeeDragThresholdBreachReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    row_count = Decimal(len(rows))
    return tuple(
        ResearchMarketFeeDragThresholdBreachReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            row_ratio=_quantize(Decimal(count) / row_count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: item[0])
    )


def _average_fee_drag_pressure_score(
    rows: tuple[ResearchMarketFeeDragThresholdBreachRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(
        sum((row.fee_drag_pressure_score for row in rows), ZERO) / Decimal(len(rows)),
    )


def _maximum_row_value(
    rows: tuple[ResearchMarketFeeDragThresholdBreachRow, ...],
    name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, name) for row in rows)


def _status_count(
    rows: tuple[ResearchMarketFeeDragThresholdBreachRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _validate_row_consistency(row: ResearchMarketFeeDragThresholdBreachRow) -> None:
    total_fee_drag_rate = _quantize(
        row.fee_drag_rate
        + row.spread_drag_rate
        + row.settlement_cost_rate
        + row.transfer_cost_rate,
    )
    if row.total_fee_drag_rate != total_fee_drag_rate:
        raise ValueError("total_fee_drag_rate must match fee components")
    expected_score = _average(
        (
            row.fee_component_pressure_score,
            row.spread_component_pressure_score,
            row.settlement_cost_pressure_score,
            row.transfer_cost_pressure_score,
            row.fee_cost_freshness_pressure_score,
            row.spread_cost_freshness_pressure_score,
            row.settlement_cost_freshness_pressure_score,
            row.transfer_cost_freshness_pressure_score,
        ),
    )
    if row.fee_drag_pressure_score != expected_score:
        raise ValueError("fee_drag_pressure_score must match component scores")
    if f"fee_drag_threshold_breach_{row.status}" not in row.reason_codes:
        raise ValueError("reason_codes must include row status")
    if row.status == "pass" and any(code.endswith("_block") for code in row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and any(code.endswith("_watch") for code in row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(
    report: ResearchMarketFeeDragThresholdBreachReport,
) -> None:
    if report.rows != tuple(sorted(report.rows, key=lambda row: row.research_key)):
        raise ValueError("rows must be sorted by research_key")
    if report.input_count != _decimal_count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_fee_drag_pressure_score != _average_fee_drag_pressure_score(
        report.rows,
    ):
        raise ValueError("average_fee_drag_pressure_score must match rows")
    for name in (
        "max_total_fee_drag_rate",
        "max_fee_drag_rate",
        "max_spread_drag_rate",
        "max_settlement_cost_rate",
        "max_transfer_cost_rate",
        "max_fee_quote_age_seconds",
        "max_spread_quote_age_seconds",
        "max_settlement_quote_age_seconds",
        "max_transfer_quote_age_seconds",
    ):
        row_name = name.removeprefix("max_")
        if getattr(report, name) != _maximum_row_value(report.rows, row_name):
            raise ValueError(f"{name} must match rows")
    expected_reasons = _summary_reason_codes(report.rows)
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(expected_reasons):
        raise ValueError("status must match rows")


def _normalize_rows(
    rows: tuple[ResearchMarketFeeDragThresholdBreachRow, ...],
) -> tuple[ResearchMarketFeeDragThresholdBreachRow, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketFeeDragThresholdBreachRow:
            raise ValueError("rows must contain fee drag rows")
        _require_hard_flags("row", row)
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchMarketFeeDragThresholdBreachReasonCodeCount, ...],
) -> tuple[ResearchMarketFeeDragThresholdBreachReasonCodeCount, ...]:
    if not isinstance(counts, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchMarketFeeDragThresholdBreachReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count rows")
        _require_hard_flags("reason_code_count", count)
    return counts


def _field_value(value: object, name: str, *, default: object = MISSING) -> Any:
    if isinstance(value, dict) and name in value:
        return value[name]
    if hasattr(value, name):
        return getattr(value, name)
    if default is not MISSING:
        return default
    raise ValueError(f"input missing {name}")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_status(name: str, value: object) -> str:
    if type(value) is not str or value not in FEE_DRAG_THRESHOLD_BREACH_STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")
    return value


def _require_public_label(name: str, value: object) -> str:
    if type(value) is not str or not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{name} must be a public label")
    _reject_unsafe_public_text(name, value)
    return value


def _require_reason_code(name: str, value: object) -> str:
    if type(value) is not str or not REASON_CODE_RE.fullmatch(value):
        raise ValueError(f"{name} must be a reason code")
    _reject_unsafe_public_text(name, value)
    return value


def _normalize_reason_codes(
    name: str,
    values: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise ValueError(f"{name} must be a tuple")
    normalized = tuple(_require_reason_code(name, value) for value in values)
    if not allow_empty and not normalized:
        raise ValueError(f"{name} must not be empty")
    return normalized


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{name} must be positive")
    return decimal_value


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(name, value)
    if decimal_value > ONE:
        raise ValueError(f"{name} must be at most one")
    return decimal_value


def _require_optional_ratio_decimal(name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_ratio_decimal(name, value)


def _require_nonnegative_whole_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{name} must be a whole Decimal")
    return decimal_value


def _require_positive_whole_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_positive_decimal(name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{name} must be a whole Decimal")
    return decimal_value


def _require_not_above(name: str, pass_value: Decimal, watch_value: Decimal) -> None:
    if pass_value > watch_value:
        raise ValueError(f"{name} must not exceed watch")


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _payload_value(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime payload value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            ready[key] = _payload_value(item)
        return ready
    if type(value) is float:
        raise ValueError("payload value must not be a float")
    if type(value) in (str, bool):
        return value
    raise ValueError("payload value is not supported")


def _validate_payload_value(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _validate_payload_key(key)
            _validate_payload_named_value(key, item)
            _validate_payload_value(item)
        return
    if isinstance(value, list):
        for item in value:
            _validate_payload_value(item)
        return
    if type(value) is float or isinstance(value, Decimal):
        raise ValueError("payload value must not be numeric unsafe")
    if type(value) is str:
        _reject_unsafe_payload_text(value)
        return
    if value is None or type(value) is bool:
        return
    raise ValueError("payload value is not supported")


def _validate_payload_key(key: str) -> None:
    lowered = key.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public payload key: {key}")


def _validate_payload_named_value(key: str, value: Any) -> None:
    if key in PAYLOAD_FLAG_KEYS and value is not True:
        raise ValueError(f"{key} must be True")
    if key in PAYLOAD_STATUS_KEYS:
        _require_status(key, value)


def _reject_unsafe_public_text(name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{name} has unsafe public text")


def _reject_unsafe_payload_text(value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError("unsafe public payload value")
