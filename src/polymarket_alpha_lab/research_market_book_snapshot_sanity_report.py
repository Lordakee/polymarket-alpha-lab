"""Pure aggregate book snapshot sanity report for manual research."""

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
    "BOOK_SNAPSHOT_SANITY_STATUSES",
    "DEFAULT_RESEARCH_MARKET_BOOK_SNAPSHOT_SANITY_REPORT_CONFIG_VERSION",
    "ResearchMarketBookSnapshotSanityConfig",
    "ResearchMarketBookSnapshotSanityInput",
    "ResearchMarketBookSnapshotSanityReasonCodeCount",
    "ResearchMarketBookSnapshotSanityReport",
    "ResearchMarketBookSnapshotSanityRow",
    "build_research_market_book_snapshot_sanity_report",
    "research_market_book_snapshot_sanity_report_digest",
    "research_market_book_snapshot_sanity_report_payload",
)


DEFAULT_RESEARCH_MARKET_BOOK_SNAPSHOT_SANITY_REPORT_CONFIG_VERSION = (
    "research-market-book-snapshot-sanity-report-v0"
)
BOOK_SNAPSHOT_SANITY_STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
PUBLIC_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
REASON_CODE_RE = re.compile(r"^[a-z0-9][a-z0-9_]{0,127}$")
COMPONENT_REASON_PRIORITY = (
    "depth_freshness_block",
    "spread_plausibility_block",
    "stale_quote_pressure_block",
    "fee_cost_freshness_block",
    "manual_recheck_urgency_block",
    "depth_freshness_watch",
    "spread_plausibility_watch",
    "stale_quote_pressure_watch",
    "fee_cost_freshness_watch",
    "manual_recheck_urgency_watch",
)


class _Missing:
    pass


MISSING = _Missing()


@dataclass(frozen=True)
class ResearchMarketBookSnapshotSanityConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_BOOK_SNAPSHOT_SANITY_REPORT_CONFIG_VERSION
    )
    max_pass_depth_age_seconds: Decimal = Decimal("120.000000")
    max_watch_depth_age_seconds: Decimal = Decimal("600.000000")
    max_pass_spread: Decimal = Decimal("0.030000")
    max_watch_spread: Decimal = Decimal("0.080000")
    max_pass_stale_quote_pressure: Decimal = Decimal("0.250000")
    max_watch_stale_quote_pressure: Decimal = Decimal("0.650000")
    max_pass_fee_cost_age_seconds: Decimal = Decimal("3600.000000")
    max_watch_fee_cost_age_seconds: Decimal = Decimal("14400.000000")
    max_pass_manual_recheck_urgency: Decimal = Decimal("0.300000")
    max_watch_manual_recheck_urgency: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketBookSnapshotSanityConfig, "config")
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_BOOK_SNAPSHOT_SANITY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match the supported value")
        for field_name in (
            "max_pass_depth_age_seconds",
            "max_watch_depth_age_seconds",
            "max_pass_spread",
            "max_watch_spread",
            "max_pass_fee_cost_age_seconds",
            "max_watch_fee_cost_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_stale_quote_pressure",
            "max_watch_stale_quote_pressure",
            "max_pass_manual_recheck_urgency",
            "max_watch_manual_recheck_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.max_pass_depth_age_seconds > self.max_watch_depth_age_seconds:
            raise ValueError("max_pass_depth_age_seconds must not exceed watch")
        if self.max_pass_spread > self.max_watch_spread:
            raise ValueError("max_pass_spread must not exceed watch")
        if self.max_pass_stale_quote_pressure > self.max_watch_stale_quote_pressure:
            raise ValueError("max_pass_stale_quote_pressure must not exceed watch")
        if self.max_pass_fee_cost_age_seconds > self.max_watch_fee_cost_age_seconds:
            raise ValueError("max_pass_fee_cost_age_seconds must not exceed watch")
        if self.max_pass_manual_recheck_urgency > self.max_watch_manual_recheck_urgency:
            raise ValueError("max_pass_manual_recheck_urgency must not exceed watch")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketBookSnapshotSanityInput:
    research_key: str
    depth_age_seconds: Decimal
    best_bid_price: Decimal
    best_ask_price: Decimal
    stale_quote_pressure: Decimal
    fee_cost_age_seconds: Decimal
    manual_recheck_urgency: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketBookSnapshotSanityInput, "input")
        _require_public_label("research_key", self.research_key)
        for field_name in ("depth_age_seconds", "fee_cost_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "best_bid_price",
            "best_ask_price",
            "stale_quote_pressure",
            "manual_recheck_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.best_ask_price <= self.best_bid_price:
            raise ValueError("best_ask_price must exceed best_bid_price")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchMarketBookSnapshotSanityRow:
    research_key: str
    depth_age_seconds: Decimal
    best_bid_price: Decimal
    best_ask_price: Decimal
    spread: Decimal
    stale_quote_pressure: Decimal
    fee_cost_age_seconds: Decimal
    manual_recheck_urgency: Decimal
    depth_freshness_score: Decimal
    spread_plausibility_score: Decimal
    stale_quote_pressure_score: Decimal
    fee_cost_freshness_score: Decimal
    manual_recheck_score: Decimal
    snapshot_sanity_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketBookSnapshotSanityRow, "row")
        _require_public_label("research_key", self.research_key)
        for field_name in ("depth_age_seconds", "fee_cost_age_seconds", "spread"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "best_bid_price",
            "best_ask_price",
            "stale_quote_pressure",
            "manual_recheck_urgency",
            "depth_freshness_score",
            "spread_plausibility_score",
            "stale_quote_pressure_score",
            "fee_cost_freshness_score",
            "manual_recheck_score",
            "snapshot_sanity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.best_ask_price <= self.best_bid_price:
            raise ValueError("best_ask_price must exceed best_bid_price")
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchMarketBookSnapshotSanityReasonCodeCount:
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
class ResearchMarketBookSnapshotSanityReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_snapshot_sanity_score: Decimal | None
    max_depth_age_seconds: Decimal
    max_spread: Decimal
    max_stale_quote_pressure: Decimal
    max_fee_cost_age_seconds: Decimal
    max_manual_recheck_urgency: Decimal
    status: str
    rows: tuple[ResearchMarketBookSnapshotSanityRow, ...]
    reason_code_counts: tuple[ResearchMarketBookSnapshotSanityReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketBookSnapshotSanityReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        for field_name in ("input_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_snapshot_sanity_score",
            _require_optional_ratio_decimal(
                "average_snapshot_sanity_score",
                self.average_snapshot_sanity_score,
            ),
        )
        for field_name in (
            "max_depth_age_seconds",
            "max_spread",
            "max_fee_cost_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_stale_quote_pressure", "max_manual_recheck_urgency"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
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


def build_research_market_book_snapshot_sanity_report(
    inputs: Iterable[object],
    *,
    config: ResearchMarketBookSnapshotSanityConfig,
    generated_at: datetime,
) -> ResearchMarketBookSnapshotSanityReport:
    if type(config) is not ResearchMarketBookSnapshotSanityConfig:
        raise ValueError("config must be a ResearchMarketBookSnapshotSanityConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_items = _normalize_inputs(inputs)
    rows = tuple(
        _row_from_input(item, config=config)
        for item in sorted(input_items, key=lambda item: item.research_key)
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchMarketBookSnapshotSanityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_snapshot_sanity_score=_average_snapshot_sanity_score(rows),
        max_depth_age_seconds=_maximum_row_value(rows, "depth_age_seconds"),
        max_spread=_maximum_row_value(rows, "spread"),
        max_stale_quote_pressure=_maximum_row_value(rows, "stale_quote_pressure"),
        max_fee_cost_age_seconds=_maximum_row_value(rows, "fee_cost_age_seconds"),
        max_manual_recheck_urgency=_maximum_row_value(rows, "manual_recheck_urgency"),
        status=_summary_status(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_market_book_snapshot_sanity_report_payload(
    report: ResearchMarketBookSnapshotSanityReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketBookSnapshotSanityReport:
        raise ValueError("report must be a ResearchMarketBookSnapshotSanityReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    return payload


def research_market_book_snapshot_sanity_report_digest(
    report: ResearchMarketBookSnapshotSanityReport,
) -> str:
    payload = research_market_book_snapshot_sanity_report_payload(report)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _row_from_input(
    item: ResearchMarketBookSnapshotSanityInput,
    *,
    config: ResearchMarketBookSnapshotSanityConfig,
) -> ResearchMarketBookSnapshotSanityRow:
    spread = _quantize(item.best_ask_price - item.best_bid_price)
    depth_freshness_score = _inverse_ratio_score(
        item.depth_age_seconds,
        config.max_watch_depth_age_seconds,
    )
    spread_plausibility_score = _inverse_ratio_score(spread, config.max_watch_spread)
    stale_quote_pressure_score = _quantize(ONE - item.stale_quote_pressure)
    fee_cost_freshness_score = _inverse_ratio_score(
        item.fee_cost_age_seconds,
        config.max_watch_fee_cost_age_seconds,
    )
    manual_recheck_score = _quantize(ONE - item.manual_recheck_urgency)
    snapshot_sanity_score = _average(
        (
            depth_freshness_score,
            spread_plausibility_score,
            stale_quote_pressure_score,
            fee_cost_freshness_score,
            manual_recheck_score,
        ),
    )
    status = _row_status(item, spread=spread, config=config)
    return ResearchMarketBookSnapshotSanityRow(
        research_key=item.research_key,
        depth_age_seconds=item.depth_age_seconds,
        best_bid_price=item.best_bid_price,
        best_ask_price=item.best_ask_price,
        spread=spread,
        stale_quote_pressure=item.stale_quote_pressure,
        fee_cost_age_seconds=item.fee_cost_age_seconds,
        manual_recheck_urgency=item.manual_recheck_urgency,
        depth_freshness_score=depth_freshness_score,
        spread_plausibility_score=spread_plausibility_score,
        stale_quote_pressure_score=stale_quote_pressure_score,
        fee_cost_freshness_score=fee_cost_freshness_score,
        manual_recheck_score=manual_recheck_score,
        snapshot_sanity_score=snapshot_sanity_score,
        status=status,
        reason_codes=_row_reason_codes(item, spread=spread, status=status, config=config),
    )


def _inverse_ratio_score(value: Decimal, watch_value: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = 28
        score = ONE - (value / watch_value)
    if score < ZERO:
        return ZERO
    if score > ONE:
        return ONE
    return _quantize(score)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _row_status(
    item: ResearchMarketBookSnapshotSanityInput,
    *,
    spread: Decimal,
    config: ResearchMarketBookSnapshotSanityConfig,
) -> str:
    if (
        item.depth_age_seconds > config.max_watch_depth_age_seconds
        or spread > config.max_watch_spread
        or item.stale_quote_pressure > config.max_watch_stale_quote_pressure
        or item.fee_cost_age_seconds > config.max_watch_fee_cost_age_seconds
        or item.manual_recheck_urgency > config.max_watch_manual_recheck_urgency
    ):
        return "block"
    if (
        item.depth_age_seconds > config.max_pass_depth_age_seconds
        or spread > config.max_pass_spread
        or item.stale_quote_pressure > config.max_pass_stale_quote_pressure
        or item.fee_cost_age_seconds > config.max_pass_fee_cost_age_seconds
        or item.manual_recheck_urgency > config.max_pass_manual_recheck_urgency
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    item: ResearchMarketBookSnapshotSanityInput,
    *,
    spread: Decimal,
    status: str,
    config: ResearchMarketBookSnapshotSanityConfig,
) -> tuple[str, ...]:
    codes = {
        f"book_snapshot_sanity_{status}",
        f"manual_snapshot_recheck_{status}",
        f"depth_freshness_{_max_threshold_status(item.depth_age_seconds, config.max_pass_depth_age_seconds, config.max_watch_depth_age_seconds)}",
        f"spread_plausibility_{_max_threshold_status(spread, config.max_pass_spread, config.max_watch_spread)}",
        f"stale_quote_pressure_{_max_threshold_status(item.stale_quote_pressure, config.max_pass_stale_quote_pressure, config.max_watch_stale_quote_pressure)}",
        f"fee_cost_freshness_{_max_threshold_status(item.fee_cost_age_seconds, config.max_pass_fee_cost_age_seconds, config.max_watch_fee_cost_age_seconds)}",
        f"manual_recheck_urgency_{_max_threshold_status(item.manual_recheck_urgency, config.max_pass_manual_recheck_urgency, config.max_watch_manual_recheck_urgency)}",
    }
    for code in item.reason_codes:
        codes.add(f"input_{code}")
    return tuple(sorted(codes))


def _max_threshold_status(
    value: Decimal,
    pass_value: Decimal,
    watch_value: Decimal,
) -> str:
    if value > watch_value:
        return "block"
    if value > pass_value:
        return "watch"
    return "pass"


def _normalize_inputs(
    inputs: Iterable[object],
) -> tuple[ResearchMarketBookSnapshotSanityInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        values = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    return tuple(_coerce_input(value) for value in values)


def _coerce_input(value: object) -> ResearchMarketBookSnapshotSanityInput:
    if type(value) is ResearchMarketBookSnapshotSanityInput:
        _require_hard_flags("input", value)
        return value
    _require_hard_flags("input", value)
    return ResearchMarketBookSnapshotSanityInput(
        research_key=_field_value(value, "research_key"),
        depth_age_seconds=_field_value(value, "depth_age_seconds"),
        best_bid_price=_field_value(value, "best_bid_price"),
        best_ask_price=_field_value(value, "best_ask_price"),
        stale_quote_pressure=_field_value(value, "stale_quote_pressure"),
        fee_cost_age_seconds=_field_value(value, "fee_cost_age_seconds"),
        manual_recheck_urgency=_field_value(value, "manual_recheck_urgency"),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _summary_reason_codes(
    rows: tuple[ResearchMarketBookSnapshotSanityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_book_snapshot_sanity_inputs",)
    if all(row.status == "pass" for row in rows):
        return ("book_snapshot_sanity_pass",)
    codes: list[str] = []
    if any(row.status == "block" for row in rows):
        codes.append("book_snapshot_sanity_block")
    elif any(row.status == "watch" for row in rows):
        codes.append("book_snapshot_sanity_watch")
    row_codes = {code for row in rows for code in row.reason_codes}
    for code in COMPONENT_REASON_PRIORITY:
        if code in row_codes:
            codes.append(code)
    return tuple(codes)


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("no_book_snapshot_sanity_inputs",):
        return "block"
    if "book_snapshot_sanity_block" in reason_codes:
        return "block"
    if "book_snapshot_sanity_watch" in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchMarketBookSnapshotSanityRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchMarketBookSnapshotSanityReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketBookSnapshotSanityReasonCodeCount(
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
        ResearchMarketBookSnapshotSanityReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            row_ratio=_quantize(Decimal(count) / row_count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: item[0])
    )


def _average_snapshot_sanity_score(
    rows: tuple[ResearchMarketBookSnapshotSanityRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(
        sum((row.snapshot_sanity_score for row in rows), ZERO) / Decimal(len(rows)),
    )


def _maximum_row_value(
    rows: tuple[ResearchMarketBookSnapshotSanityRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _status_count(rows: tuple[ResearchMarketBookSnapshotSanityRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _validate_row_consistency(row: ResearchMarketBookSnapshotSanityRow) -> None:
    if row.spread != _quantize(row.best_ask_price - row.best_bid_price):
        raise ValueError("spread must match price gap")
    expected_score = _average(
        (
            row.depth_freshness_score,
            row.spread_plausibility_score,
            row.stale_quote_pressure_score,
            row.fee_cost_freshness_score,
            row.manual_recheck_score,
        ),
    )
    if row.snapshot_sanity_score != expected_score:
        raise ValueError("snapshot_sanity_score must match component scores")
    if f"book_snapshot_sanity_{row.status}" not in row.reason_codes:
        raise ValueError("reason_codes must include row status")


def _validate_report_consistency(report: ResearchMarketBookSnapshotSanityReport) -> None:
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
    if report.average_snapshot_sanity_score != _average_snapshot_sanity_score(report.rows):
        raise ValueError("average_snapshot_sanity_score must match rows")
    if report.max_depth_age_seconds != _maximum_row_value(report.rows, "depth_age_seconds"):
        raise ValueError("max_depth_age_seconds must match rows")
    if report.max_spread != _maximum_row_value(report.rows, "spread"):
        raise ValueError("max_spread must match rows")
    if report.max_stale_quote_pressure != _maximum_row_value(
        report.rows,
        "stale_quote_pressure",
    ):
        raise ValueError("max_stale_quote_pressure must match rows")
    if report.max_fee_cost_age_seconds != _maximum_row_value(
        report.rows,
        "fee_cost_age_seconds",
    ):
        raise ValueError("max_fee_cost_age_seconds must match rows")
    if report.max_manual_recheck_urgency != _maximum_row_value(
        report.rows,
        "manual_recheck_urgency",
    ):
        raise ValueError("max_manual_recheck_urgency must match rows")
    expected_reasons = _summary_reason_codes(report.rows)
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(expected_reasons):
        raise ValueError("status must match rows")


def _normalize_rows(
    rows: tuple[ResearchMarketBookSnapshotSanityRow, ...],
) -> tuple[ResearchMarketBookSnapshotSanityRow, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketBookSnapshotSanityRow:
            raise ValueError("rows must contain ResearchMarketBookSnapshotSanityRow")
        _require_hard_flags("row", row)
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchMarketBookSnapshotSanityReasonCodeCount, ...],
) -> tuple[ResearchMarketBookSnapshotSanityReasonCodeCount, ...]:
    if not isinstance(counts, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchMarketBookSnapshotSanityReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count rows")
        _require_hard_flags("reason_code_count", count)
    return counts


def _field_value(value: object, field_name: str, *, default: object = MISSING) -> Any:
    if isinstance(value, dict):
        if field_name in value:
            return value[field_name]
    elif hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not MISSING:
        return default
    raise ValueError(f"input missing {field_name}")


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
    if type(value) is not str or value not in BOOK_SNAPSHOT_SANITY_STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")
    return value


def _require_public_label(name: str, value: object) -> str:
    if type(value) is not str or not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{name} must be a public label")
    return value


def _require_reason_code(name: str, value: object) -> str:
    if type(value) is not str or not REASON_CODE_RE.fullmatch(value):
        raise ValueError(f"{name} must be a reason code")
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
