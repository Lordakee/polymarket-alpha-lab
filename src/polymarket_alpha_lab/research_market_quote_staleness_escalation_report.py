"""Pure public quote stale escalation digest."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any

from polymarket_alpha_lab.team_paper_guard import UNSAFE_SURFACE_FIELD_FRAGMENTS


DEFAULT_RESEARCH_MARKET_QUOTE_STALENESS_ESCALATION_CONFIG_VERSION = (
    "research-market-quote-staleness-escalation-report-v0"
)

STATUSES = ("pass", "watch", "block")
ROW_REASON_CODES = (
    "quote_staleness_escalation_clear",
    "aggregate_quote_age_stale",
    "aggregate_quote_age_blocking",
    "spread_widening_watch",
    "spread_widening_blocking",
    "depth_fade_watch",
    "depth_fade_blocking",
    "catalyst_pressure_watch",
    "catalyst_pressure_blocking",
    "fee_friction_watch",
    "fee_friction_blocking",
    "composite_escalation_watch",
    "composite_escalation_blocking",
)
REPORT_REASON_CODES = (
    "quote_staleness_escalation_report_clear",
    "aggregate_quote_age_stale",
    "spread_widening_detected",
    "depth_fade_detected",
    "catalyst_pressure_detected",
    "fee_friction_detected",
    "composite_escalation_detected",
)

REDACTED_MARKET_REFERENCE_PREFIX = "market_ref_"
REDACTED_SOURCE_REFERENCE_PREFIX = "source_ref_"
REDACTED_DIGEST_LENGTH = 16

COUNT_QUANTUM = Decimal("1")
VALUE_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_VALUE = Decimal("0.000000")
ONE_VALUE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)


@dataclass(frozen=True)
class ResearchMarketQuoteStalenessEscalationConfig:
    config_version: str = DEFAULT_RESEARCH_MARKET_QUOTE_STALENESS_ESCALATION_CONFIG_VERSION
    quote_age_watch_seconds: Decimal = Decimal("120.000000")
    quote_age_block_seconds: Decimal = Decimal("300.000000")
    spread_widening_watch_ratio: Decimal = Decimal("0.100000")
    spread_widening_block_ratio: Decimal = Decimal("0.250000")
    depth_fade_watch_ratio: Decimal = Decimal("0.250000")
    depth_fade_block_ratio: Decimal = Decimal("0.500000")
    catalyst_pressure_watch_score: Decimal = Decimal("0.500000")
    catalyst_pressure_block_score: Decimal = Decimal("0.800000")
    fee_friction_watch_ratio: Decimal = Decimal("0.020000")
    fee_friction_block_ratio: Decimal = Decimal("0.050000")
    watch_escalation_score: Decimal = Decimal("0.350000")
    block_escalation_score: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketQuoteStalenessEscalationConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "quote_age_watch_seconds",
            "quote_age_block_seconds",
            "spread_widening_watch_ratio",
            "spread_widening_block_ratio",
            "depth_fade_watch_ratio",
            "depth_fade_block_ratio",
            "catalyst_pressure_watch_score",
            "catalyst_pressure_block_score",
            "fee_friction_watch_ratio",
            "fee_friction_block_ratio",
            "watch_escalation_score",
            "block_escalation_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_value(field_name, getattr(self, field_name)),
            )
        _require_threshold_pair(
            "quote_age",
            self.quote_age_watch_seconds,
            self.quote_age_block_seconds,
        )
        _require_threshold_pair(
            "spread_widening",
            self.spread_widening_watch_ratio,
            self.spread_widening_block_ratio,
        )
        _require_threshold_pair(
            "depth_fade",
            self.depth_fade_watch_ratio,
            self.depth_fade_block_ratio,
        )
        _require_threshold_pair(
            "catalyst_pressure",
            self.catalyst_pressure_watch_score,
            self.catalyst_pressure_block_score,
        )
        _require_threshold_pair(
            "fee_friction",
            self.fee_friction_watch_ratio,
            self.fee_friction_block_ratio,
        )
        _require_threshold_pair(
            "escalation_score",
            self.watch_escalation_score,
            self.block_escalation_score,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketQuoteStalenessEscalationInput:
    research_bucket: str
    market_reference: str
    source_reference: str
    quote_age_seconds: Decimal
    spread_widening_ratio: Decimal
    depth_fade_ratio: Decimal
    catalyst_pressure_score: Decimal
    fee_friction_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketQuoteStalenessEscalationInput, "input")
        for field_name in ("research_bucket", "market_reference", "source_reference"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "quote_age_seconds",
            "spread_widening_ratio",
            "depth_fade_ratio",
            "catalyst_pressure_score",
            "fee_friction_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_value(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchMarketQuoteStalenessEscalationRow:
    research_bucket: str
    redacted_market_reference: str
    redacted_source_reference: str
    quote_age_seconds: Decimal
    spread_widening_ratio: Decimal
    depth_fade_ratio: Decimal
    catalyst_pressure_score: Decimal
    fee_friction_ratio: Decimal
    quote_age_pressure: Decimal
    spread_widening_pressure: Decimal
    depth_fade_pressure: Decimal
    catalyst_pressure_signal: Decimal
    fee_friction_pressure: Decimal
    escalation_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketQuoteStalenessEscalationRow, "row")
        _require_canonical_string("research_bucket", self.research_bucket)
        _require_redacted_reference(
            "redacted_market_reference",
            self.redacted_market_reference,
            REDACTED_MARKET_REFERENCE_PREFIX,
        )
        _require_redacted_reference(
            "redacted_source_reference",
            self.redacted_source_reference,
            REDACTED_SOURCE_REFERENCE_PREFIX,
        )
        for field_name in (
            "quote_age_seconds",
            "spread_widening_ratio",
            "depth_fade_ratio",
            "catalyst_pressure_score",
            "fee_friction_ratio",
            "quote_age_pressure",
            "spread_widening_pressure",
            "depth_fade_pressure",
            "catalyst_pressure_signal",
            "fee_friction_pressure",
            "escalation_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_value(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchMarketQuoteStalenessEscalationReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    bucket_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    stale_quote_count: Decimal
    spread_widening_count: Decimal
    depth_fade_count: Decimal
    catalyst_pressure_count: Decimal
    fee_friction_count: Decimal
    mean_quote_age_seconds: Decimal
    mean_spread_widening_ratio: Decimal
    mean_depth_fade_ratio: Decimal
    mean_catalyst_pressure_score: Decimal
    mean_fee_friction_ratio: Decimal
    mean_escalation_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    rows: tuple[ResearchMarketQuoteStalenessEscalationRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "input_count",
            "bucket_count",
            "watch_count",
            "block_count",
            "stale_quote_count",
            "spread_widening_count",
            "depth_fade_count",
            "catalyst_pressure_count",
            "fee_friction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_quote_age_seconds",
            "mean_spread_widening_ratio",
            "mean_depth_fade_ratio",
            "mean_catalyst_pressure_score",
            "mean_fee_friction_ratio",
            "mean_escalation_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_value(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
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
        _validate_report(self)
        _require_hard_flags("report", self)


def build_research_market_quote_staleness_escalation_report(
    inputs: list[ResearchMarketQuoteStalenessEscalationInput]
    | tuple[ResearchMarketQuoteStalenessEscalationInput, ...],
    *,
    config: ResearchMarketQuoteStalenessEscalationConfig,
    generated_at: datetime,
) -> ResearchMarketQuoteStalenessEscalationReport:
    if type(config) is not ResearchMarketQuoteStalenessEscalationConfig:
        raise ValueError("config must be a ResearchMarketQuoteStalenessEscalationConfig")
    _require_hard_flags("config", config)
    source_rows = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (_row_from_input(row, config) for row in source_rows),
            key=_row_sort_key,
        ),
    )
    return ResearchMarketQuoteStalenessEscalationReport(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        input_count=_count(len(source_rows)),
        bucket_count=_count(len({row.research_bucket for row in source_rows})),
        watch_count=_count(sum(1 for row in rows if row.status == "watch")),
        block_count=_count(sum(1 for row in rows if row.status == "block")),
        stale_quote_count=_count(
            sum(
                1
                for row in rows
                if _has_any_reason(
                    row,
                    ("aggregate_quote_age_stale", "aggregate_quote_age_blocking"),
                )
            ),
        ),
        spread_widening_count=_count(
            sum(
                1
                for row in rows
                if _has_any_reason(row, ("spread_widening_watch", "spread_widening_blocking"))
            ),
        ),
        depth_fade_count=_count(
            sum(
                1
                for row in rows
                if _has_any_reason(row, ("depth_fade_watch", "depth_fade_blocking"))
            ),
        ),
        catalyst_pressure_count=_count(
            sum(
                1
                for row in rows
                if _has_any_reason(
                    row,
                    ("catalyst_pressure_watch", "catalyst_pressure_blocking"),
                )
            ),
        ),
        fee_friction_count=_count(
            sum(
                1
                for row in rows
                if _has_any_reason(row, ("fee_friction_watch", "fee_friction_blocking"))
            ),
        ),
        mean_quote_age_seconds=_mean(tuple(row.quote_age_seconds for row in rows)),
        mean_spread_widening_ratio=_mean(tuple(row.spread_widening_ratio for row in rows)),
        mean_depth_fade_ratio=_mean(tuple(row.depth_fade_ratio for row in rows)),
        mean_catalyst_pressure_score=_mean(
            tuple(row.catalyst_pressure_score for row in rows),
        ),
        mean_fee_friction_ratio=_mean(tuple(row.fee_friction_ratio for row in rows)),
        mean_escalation_score=_mean(tuple(row.escalation_score for row in rows)),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts_from_rows(rows),
        rows=rows,
    )


def research_market_quote_staleness_escalation_payload(
    report: ResearchMarketQuoteStalenessEscalationReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchMarketQuoteStalenessEscalationReport:
        _require_hard_flags("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchMarketQuoteStalenessEscalationReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_payload_keys("quote staleness escalation payload", payload)
    _reject_unsafe_public_strings("quote staleness escalation payload", payload)
    return payload


def research_market_quote_staleness_escalation_digest(
    report: ResearchMarketQuoteStalenessEscalationReport | dict[str, Any],
) -> str:
    payload = research_market_quote_staleness_escalation_payload(report)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class _DictFlags:
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
    inputs: list[ResearchMarketQuoteStalenessEscalationInput]
    | tuple[ResearchMarketQuoteStalenessEscalationInput, ...],
) -> tuple[ResearchMarketQuoteStalenessEscalationInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(inputs)
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not ResearchMarketQuoteStalenessEscalationInput:
            raise ValueError(
                "inputs must contain ResearchMarketQuoteStalenessEscalationInput values",
            )
        _require_hard_flags("input", row)
        key = (row.research_bucket, row.market_reference, row.source_reference)
        if key in seen:
            raise ValueError("inputs must not contain duplicate public check values")
        seen.add(key)
    return rows


def _row_from_input(
    row: ResearchMarketQuoteStalenessEscalationInput,
    config: ResearchMarketQuoteStalenessEscalationConfig,
) -> ResearchMarketQuoteStalenessEscalationRow:
    quote_age_pressure = _pressure(row.quote_age_seconds, config.quote_age_block_seconds)
    spread_widening_pressure = _pressure(
        row.spread_widening_ratio,
        config.spread_widening_block_ratio,
    )
    depth_fade_pressure = _pressure(row.depth_fade_ratio, config.depth_fade_block_ratio)
    catalyst_pressure_signal = _pressure(
        row.catalyst_pressure_score,
        config.catalyst_pressure_block_score,
    )
    fee_friction_pressure = _pressure(row.fee_friction_ratio, config.fee_friction_block_ratio)
    escalation_score = _mean(
        (
            quote_age_pressure,
            spread_widening_pressure,
            depth_fade_pressure,
            catalyst_pressure_signal,
            fee_friction_pressure,
        ),
    )
    return ResearchMarketQuoteStalenessEscalationRow(
        research_bucket=row.research_bucket,
        redacted_market_reference=_redact_reference(
            row.market_reference,
            REDACTED_MARKET_REFERENCE_PREFIX,
        ),
        redacted_source_reference=_redact_reference(
            row.source_reference,
            REDACTED_SOURCE_REFERENCE_PREFIX,
        ),
        quote_age_seconds=row.quote_age_seconds,
        spread_widening_ratio=row.spread_widening_ratio,
        depth_fade_ratio=row.depth_fade_ratio,
        catalyst_pressure_score=row.catalyst_pressure_score,
        fee_friction_ratio=row.fee_friction_ratio,
        quote_age_pressure=quote_age_pressure,
        spread_widening_pressure=spread_widening_pressure,
        depth_fade_pressure=depth_fade_pressure,
        catalyst_pressure_signal=catalyst_pressure_signal,
        fee_friction_pressure=fee_friction_pressure,
        escalation_score=escalation_score,
        status=_row_status(row, escalation_score, config),
        reason_codes=_row_reason_codes(row, escalation_score, config),
    )


def _row_status(
    row: ResearchMarketQuoteStalenessEscalationInput,
    escalation_score: Decimal,
    config: ResearchMarketQuoteStalenessEscalationConfig,
) -> str:
    if (
        row.quote_age_seconds >= config.quote_age_block_seconds
        or row.spread_widening_ratio >= config.spread_widening_block_ratio
        or row.depth_fade_ratio >= config.depth_fade_block_ratio
        or row.catalyst_pressure_score >= config.catalyst_pressure_block_score
        or row.fee_friction_ratio >= config.fee_friction_block_ratio
        or escalation_score >= config.block_escalation_score
    ):
        return "block"
    if (
        row.quote_age_seconds >= config.quote_age_watch_seconds
        or row.spread_widening_ratio >= config.spread_widening_watch_ratio
        or row.depth_fade_ratio >= config.depth_fade_watch_ratio
        or row.catalyst_pressure_score >= config.catalyst_pressure_watch_score
        or row.fee_friction_ratio >= config.fee_friction_watch_ratio
        or escalation_score >= config.watch_escalation_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    row: ResearchMarketQuoteStalenessEscalationInput,
    escalation_score: Decimal,
    config: ResearchMarketQuoteStalenessEscalationConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    _append_threshold_code(
        codes,
        row.quote_age_seconds,
        config.quote_age_watch_seconds,
        config.quote_age_block_seconds,
        "aggregate_quote_age_stale",
        "aggregate_quote_age_blocking",
    )
    _append_threshold_code(
        codes,
        row.spread_widening_ratio,
        config.spread_widening_watch_ratio,
        config.spread_widening_block_ratio,
        "spread_widening_watch",
        "spread_widening_blocking",
    )
    _append_threshold_code(
        codes,
        row.depth_fade_ratio,
        config.depth_fade_watch_ratio,
        config.depth_fade_block_ratio,
        "depth_fade_watch",
        "depth_fade_blocking",
    )
    _append_threshold_code(
        codes,
        row.catalyst_pressure_score,
        config.catalyst_pressure_watch_score,
        config.catalyst_pressure_block_score,
        "catalyst_pressure_watch",
        "catalyst_pressure_blocking",
    )
    _append_threshold_code(
        codes,
        row.fee_friction_ratio,
        config.fee_friction_watch_ratio,
        config.fee_friction_block_ratio,
        "fee_friction_watch",
        "fee_friction_blocking",
    )
    _append_threshold_code(
        codes,
        escalation_score,
        config.watch_escalation_score,
        config.block_escalation_score,
        "composite_escalation_watch",
        "composite_escalation_blocking",
    )
    if not codes:
        return ("quote_staleness_escalation_clear",)
    return tuple(codes)


def _append_threshold_code(
    codes: list[str],
    value: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
    watch_code: str,
    block_code: str,
) -> None:
    if value >= block_threshold:
        codes.append(block_code)
    elif value >= watch_threshold:
        codes.append(watch_code)


def _report_status(
    rows: tuple[ResearchMarketQuoteStalenessEscalationRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchMarketQuoteStalenessEscalationRow, ...],
) -> tuple[str, ...]:
    if not rows or all(row.status == "pass" for row in rows):
        return ("quote_staleness_escalation_report_clear",)
    codes: list[str] = []
    if any(
        _has_any_reason(row, ("aggregate_quote_age_stale", "aggregate_quote_age_blocking"))
        for row in rows
    ):
        codes.append("aggregate_quote_age_stale")
    if any(
        _has_any_reason(row, ("spread_widening_watch", "spread_widening_blocking"))
        for row in rows
    ):
        codes.append("spread_widening_detected")
    if any(_has_any_reason(row, ("depth_fade_watch", "depth_fade_blocking")) for row in rows):
        codes.append("depth_fade_detected")
    if any(
        _has_any_reason(row, ("catalyst_pressure_watch", "catalyst_pressure_blocking"))
        for row in rows
    ):
        codes.append("catalyst_pressure_detected")
    if any(
        _has_any_reason(row, ("fee_friction_watch", "fee_friction_blocking"))
        for row in rows
    ):
        codes.append("fee_friction_detected")
    if any(
        _has_any_reason(
            row,
            ("composite_escalation_watch", "composite_escalation_blocking"),
        )
        for row in rows
    ):
        codes.append("composite_escalation_detected")
    return tuple(codes)


def _has_any_reason(
    row: ResearchMarketQuoteStalenessEscalationRow,
    reason_codes: tuple[str, ...],
) -> bool:
    return any(reason_code in row.reason_codes for reason_code in reason_codes)


def _row_sort_key(
    row: ResearchMarketQuoteStalenessEscalationRow,
) -> tuple[Decimal, Decimal, Decimal, str, str, str]:
    status_rank = {"block": Decimal("2"), "watch": Decimal("1"), "pass": Decimal("0")}[
        row.status
    ]
    return (
        -status_rank,
        -row.escalation_score,
        -row.quote_age_seconds,
        row.research_bucket,
        row.redacted_market_reference,
        row.redacted_source_reference,
    )


def _validate_row(row: ResearchMarketQuoteStalenessEscalationRow) -> None:
    if row.status == "pass" and row.reason_codes != ("quote_staleness_escalation_clear",):
        raise ValueError("pass row reason_codes must be clear")
    if row.status in ("watch", "block") and row.reason_codes == (
        "quote_staleness_escalation_clear",
    ):
        raise ValueError("escalated row reason_codes must not be clear")
    if row.status == "block" and not any(
        reason_code.endswith("_blocking") for reason_code in row.reason_codes
    ):
        raise ValueError("block row reason_codes must contain blocking checks")
    if row.status == "watch" and any(
        reason_code.endswith("_blocking") for reason_code in row.reason_codes
    ):
        raise ValueError("watch row reason_codes must not contain blocking checks")


def _validate_report(report: ResearchMarketQuoteStalenessEscalationReport) -> None:
    if report.input_count != _count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.bucket_count != _count(len({row.research_bucket for row in report.rows})):
        raise ValueError("bucket_count must match rows")
    if report.watch_count != _count(sum(1 for row in report.rows if row.status == "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(sum(1 for row in report.rows if row.status == "block")):
        raise ValueError("block_count must match rows")
    if report.stale_quote_count != _count(
        sum(
            1
            for row in report.rows
            if _has_any_reason(row, ("aggregate_quote_age_stale", "aggregate_quote_age_blocking"))
        ),
    ):
        raise ValueError("stale_quote_count must match rows")
    if report.spread_widening_count != _count(
        sum(
            1
            for row in report.rows
            if _has_any_reason(row, ("spread_widening_watch", "spread_widening_blocking"))
        ),
    ):
        raise ValueError("spread_widening_count must match rows")
    if report.depth_fade_count != _count(
        sum(
            1
            for row in report.rows
            if _has_any_reason(row, ("depth_fade_watch", "depth_fade_blocking"))
        ),
    ):
        raise ValueError("depth_fade_count must match rows")
    if report.catalyst_pressure_count != _count(
        sum(
            1
            for row in report.rows
            if _has_any_reason(row, ("catalyst_pressure_watch", "catalyst_pressure_blocking"))
        ),
    ):
        raise ValueError("catalyst_pressure_count must match rows")
    if report.fee_friction_count != _count(
        sum(
            1
            for row in report.rows
            if _has_any_reason(row, ("fee_friction_watch", "fee_friction_blocking"))
        ),
    ):
        raise ValueError("fee_friction_count must match rows")
    if report.mean_quote_age_seconds != _mean(tuple(row.quote_age_seconds for row in report.rows)):
        raise ValueError("mean_quote_age_seconds must match rows")
    if report.mean_spread_widening_ratio != _mean(
        tuple(row.spread_widening_ratio for row in report.rows),
    ):
        raise ValueError("mean_spread_widening_ratio must match rows")
    if report.mean_depth_fade_ratio != _mean(tuple(row.depth_fade_ratio for row in report.rows)):
        raise ValueError("mean_depth_fade_ratio must match rows")
    if report.mean_catalyst_pressure_score != _mean(
        tuple(row.catalyst_pressure_score for row in report.rows),
    ):
        raise ValueError("mean_catalyst_pressure_score must match rows")
    if report.mean_fee_friction_ratio != _mean(
        tuple(row.fee_friction_ratio for row in report.rows),
    ):
        raise ValueError("mean_fee_friction_ratio must match rows")
    if report.mean_escalation_score != _mean(tuple(row.escalation_score for row in report.rows)):
        raise ValueError("mean_escalation_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts_from_rows(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be deterministic")
    keys = tuple(
        (row.research_bucket, row.redacted_market_reference, row.redacted_source_reference)
        for row in report.rows
    )
    if len(set(keys)) != len(keys):
        raise ValueError("rows must contain unique public check values")


def _normalize_rows(
    value: object,
) -> tuple[ResearchMarketQuoteStalenessEscalationRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be a tuple")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be a tuple") from exc
    for row in rows:
        if type(row) is not ResearchMarketQuoteStalenessEscalationRow:
            raise ValueError(
                "rows must contain ResearchMarketQuoteStalenessEscalationRow values",
            )
        _require_hard_flags("row", row)
    return rows


def _reason_code_counts_from_rows(
    rows: tuple[ResearchMarketQuoteStalenessEscalationRow, ...],
) -> tuple[tuple[str, Decimal], ...]:
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        (reason_code, _count(count))
        for reason_code, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )


def _normalize_reason_code_counts(value: object) -> tuple[tuple[str, Decimal], ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be a tuple")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_code_counts must be a tuple") from exc
    normalized = []
    for row in rows:
        if type(row) is not tuple or len(row) != 2:
            raise ValueError("reason_code_counts must contain reason_code count tuples")
        reason_code, count = row
        _require_member("reason_code_counts reason_code", reason_code, ROW_REASON_CODES)
        normalized.append(
            (
                reason_code,
                _normalize_nonnegative_count("reason_code_counts count", count),
            ),
        )
    return tuple(normalized)


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a tuple")
    try:
        codes = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be a tuple") from exc
    for code in codes:
        _require_member(field_name, code, allowed)
    if len(set(codes)) != len(codes):
        raise ValueError(f"{field_name} must not contain duplicates")
    return codes


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, (str, bool)) or value is None:
        return value
    raise ValueError("value is not JSON serializable")


def _redact_reference(value: str, prefix: str) -> str:
    _require_canonical_string("reference", value)
    digest = sha256(value.encode("utf-8")).hexdigest()[:REDACTED_DIGEST_LENGTH]
    return f"{prefix}{digest}"


def _require_redacted_reference(field_name: str, value: object, prefix: str) -> None:
    _require_canonical_string(field_name, value)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if _contains_sensitive_text(value):
        raise ValueError(f"{field_name} must be redacted")
    if not value.startswith(prefix):
        raise ValueError(f"{field_name} must be redacted")
    digest = value.removeprefix(prefix)
    if len(digest) != REDACTED_DIGEST_LENGTH:
        raise ValueError(f"{field_name} must be redacted")
    if any(char not in "0123456789abcdef" for char in digest):
        raise ValueError(f"{field_name} must be redacted")


def _contains_sensitive_text(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in ("secret", "private", "token"))


def _reject_unsafe_public_strings(label: str, value: object) -> None:
    if type(value) is str:
        if _has_unsafe_surface_fragment(value):
            raise ValueError(f"unsafe surface value in {label}")
        if _contains_sensitive_text(value):
            raise ValueError(f"sensitive value in {label}")
        return
    if isinstance(value, dict):
        for item in value.values():
            _reject_unsafe_public_strings(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_strings(label, item)
        return


def _reject_unsafe_payload_keys(label: str, value: object) -> None:
    for key in _iter_payload_keys(value):
        if _has_unsafe_surface_fragment(key):
            raise ValueError(f"unsafe surface field in {label}: {key}")


def _iter_payload_keys(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_payload_keys(asdict(value))
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            keys.append(key)
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    if isinstance(value, (list, tuple)):
        keys = []
        for item in value:
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    return ()


def _has_unsafe_surface_fragment(value: str) -> bool:
    lowered = value.lower()
    tokens = tuple(
        part
        for part in "".join(char if char.isalnum() else "_" for char in lowered).split(
            "_",
        )
        if part
    )
    for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS:
        if "_" in fragment:
            if fragment in lowered:
                return True
            continue
        if fragment in tokens:
            return True
    return False


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed:
        raise ValueError(f"{field_name} is not supported")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


def _require_threshold_pair(field_name: str, watch_value: Decimal, block_value: Decimal) -> None:
    if watch_value <= ZERO_VALUE:
        raise ValueError(f"{field_name}_watch threshold must be positive")
    if block_value <= watch_value:
        if field_name == "quote_age":
            raise ValueError("quote_age_block_seconds must exceed quote_age_watch_seconds")
        raise ValueError(f"{field_name}_block threshold must exceed watch threshold")


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return decimal_value.quantize(COUNT_QUANTUM)


def _normalize_nonnegative_value(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_VALUE:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize_value(decimal_value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _pressure(value: Decimal, block_threshold: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        pressure = value / block_threshold
    if pressure > ONE_VALUE:
        return ONE_VALUE
    return _quantize_value(pressure)


def _quantize_value(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(VALUE_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_VALUE
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_value(sum(values, ZERO_VALUE) / Decimal(len(values)))
