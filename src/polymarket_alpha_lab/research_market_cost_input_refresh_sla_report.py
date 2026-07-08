"""Pure aggregate refresh SLA report for market cost inputs."""

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
    "COST_INPUT_REFRESH_SLA_STATUSES",
    "DEFAULT_RESEARCH_MARKET_COST_INPUT_REFRESH_SLA_REPORT_CONFIG_VERSION",
    "ResearchMarketCostInputRefreshSlaConfig",
    "ResearchMarketCostInputRefreshSlaInput",
    "ResearchMarketCostInputRefreshSlaReasonCodeCount",
    "ResearchMarketCostInputRefreshSlaReport",
    "ResearchMarketCostInputRefreshSlaRow",
    "build_research_market_cost_input_refresh_sla_report",
    "research_market_cost_input_refresh_sla_report_digest",
    "research_market_cost_input_refresh_sla_report_payload",
)


DEFAULT_RESEARCH_MARKET_COST_INPUT_REFRESH_SLA_REPORT_CONFIG_VERSION = (
    "research-market-cost-input-refresh-sla-report-v0"
)
COST_INPUT_REFRESH_SLA_STATUSES = ("pass", "watch", "block")
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
    "source_id",
    "source_ref",
    "source_url",
    "source_text",
    "token",
    "secret",
    "credential",
    "private_key",
)
COMPONENT_REASON_PRIORITY = (
    "fee_freshness_block",
    "spread_observation_age_block",
    "depth_confidence_block",
    "settlement_friction_block",
    "manual_recheck_urgency_block",
    "fee_freshness_watch",
    "spread_observation_age_watch",
    "depth_confidence_watch",
    "settlement_friction_watch",
    "manual_recheck_urgency_watch",
)


class _Missing:
    pass


MISSING = _Missing()


@dataclass(frozen=True)
class ResearchMarketCostInputRefreshSlaConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_COST_INPUT_REFRESH_SLA_REPORT_CONFIG_VERSION
    )
    max_pass_fee_age_seconds: Decimal = Decimal("3600.000000")
    max_watch_fee_age_seconds: Decimal = Decimal("14400.000000")
    max_pass_spread_observation_age_seconds: Decimal = Decimal("300.000000")
    max_watch_spread_observation_age_seconds: Decimal = Decimal("1200.000000")
    min_pass_depth_confidence: Decimal = Decimal("0.800000")
    min_watch_depth_confidence: Decimal = Decimal("0.550000")
    max_pass_settlement_friction_rate: Decimal = Decimal("0.005000")
    max_watch_settlement_friction_rate: Decimal = Decimal("0.020000")
    max_pass_manual_recheck_urgency: Decimal = Decimal("0.300000")
    max_watch_manual_recheck_urgency: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketCostInputRefreshSlaConfig, "config")
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_COST_INPUT_REFRESH_SLA_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match the supported value")
        for field_name in (
            "max_pass_fee_age_seconds",
            "max_watch_fee_age_seconds",
            "max_pass_spread_observation_age_seconds",
            "max_watch_spread_observation_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_depth_confidence",
            "min_watch_depth_confidence",
            "max_pass_settlement_friction_rate",
            "max_watch_settlement_friction_rate",
            "max_pass_manual_recheck_urgency",
            "max_watch_manual_recheck_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.max_pass_fee_age_seconds > self.max_watch_fee_age_seconds:
            raise ValueError("max_pass_fee_age_seconds must not exceed watch")
        if (
            self.max_pass_spread_observation_age_seconds
            > self.max_watch_spread_observation_age_seconds
        ):
            raise ValueError(
                "max_pass_spread_observation_age_seconds must not exceed watch",
            )
        if self.min_watch_depth_confidence > self.min_pass_depth_confidence:
            raise ValueError("min_watch_depth_confidence must not exceed pass")
        if (
            self.max_pass_settlement_friction_rate
            > self.max_watch_settlement_friction_rate
        ):
            raise ValueError("max_pass_settlement_friction_rate must not exceed watch")
        if (
            self.max_pass_manual_recheck_urgency
            > self.max_watch_manual_recheck_urgency
        ):
            raise ValueError("max_pass_manual_recheck_urgency must not exceed watch")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketCostInputRefreshSlaInput:
    research_key: str
    fee_age_seconds: Decimal
    spread_observation_age_seconds: Decimal
    depth_confidence: Decimal
    settlement_friction_rate: Decimal
    manual_recheck_urgency: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketCostInputRefreshSlaInput, "input")
        _require_public_label("research_key", self.research_key)
        for field_name in ("fee_age_seconds", "spread_observation_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "depth_confidence",
            "settlement_friction_rate",
            "manual_recheck_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchMarketCostInputRefreshSlaRow:
    research_key: str
    fee_age_seconds: Decimal
    spread_observation_age_seconds: Decimal
    depth_confidence: Decimal
    settlement_friction_rate: Decimal
    manual_recheck_urgency: Decimal
    fee_freshness_score: Decimal
    spread_observation_freshness_score: Decimal
    settlement_friction_score: Decimal
    manual_recheck_score: Decimal
    refresh_sla_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketCostInputRefreshSlaRow, "row")
        _require_public_label("research_key", self.research_key)
        for field_name in ("fee_age_seconds", "spread_observation_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "depth_confidence",
            "settlement_friction_rate",
            "manual_recheck_urgency",
            "fee_freshness_score",
            "spread_observation_freshness_score",
            "settlement_friction_score",
            "manual_recheck_score",
            "refresh_sla_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
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
class ResearchMarketCostInputRefreshSlaReasonCodeCount:
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
class ResearchMarketCostInputRefreshSlaReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_refresh_sla_score: Decimal | None
    max_fee_age_seconds: Decimal
    max_spread_observation_age_seconds: Decimal
    min_depth_confidence: Decimal
    max_settlement_friction_rate: Decimal
    max_manual_recheck_urgency: Decimal
    status: str
    rows: tuple[ResearchMarketCostInputRefreshSlaRow, ...]
    reason_code_counts: tuple[ResearchMarketCostInputRefreshSlaReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketCostInputRefreshSlaReport, "report")
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
            "average_refresh_sla_score",
            _require_optional_ratio_decimal(
                "average_refresh_sla_score",
                self.average_refresh_sla_score,
            ),
        )
        for field_name in (
            "max_fee_age_seconds",
            "max_spread_observation_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_depth_confidence",
            "max_settlement_friction_rate",
            "max_manual_recheck_urgency",
        ):
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


def build_research_market_cost_input_refresh_sla_report(
    inputs: Iterable[object],
    *,
    config: ResearchMarketCostInputRefreshSlaConfig,
    generated_at: datetime,
) -> ResearchMarketCostInputRefreshSlaReport:
    if type(config) is not ResearchMarketCostInputRefreshSlaConfig:
        raise ValueError("config must be a ResearchMarketCostInputRefreshSlaConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_items = _normalize_inputs(inputs)
    rows = tuple(
        _row_from_input(item, config=config)
        for item in sorted(input_items, key=lambda item: item.research_key)
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchMarketCostInputRefreshSlaReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_refresh_sla_score=_average_refresh_sla_score(rows),
        max_fee_age_seconds=_maximum_row_value(rows, "fee_age_seconds"),
        max_spread_observation_age_seconds=_maximum_row_value(
            rows,
            "spread_observation_age_seconds",
        ),
        min_depth_confidence=_minimum_row_value(rows, "depth_confidence"),
        max_settlement_friction_rate=_maximum_row_value(
            rows,
            "settlement_friction_rate",
        ),
        max_manual_recheck_urgency=_maximum_row_value(rows, "manual_recheck_urgency"),
        status=_summary_status(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_market_cost_input_refresh_sla_report_payload(
    report: ResearchMarketCostInputRefreshSlaReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketCostInputRefreshSlaReport:
        raise ValueError("report must be a ResearchMarketCostInputRefreshSlaReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    return payload


def research_market_cost_input_refresh_sla_report_digest(
    report: ResearchMarketCostInputRefreshSlaReport,
) -> str:
    payload = research_market_cost_input_refresh_sla_report_payload(report)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _row_from_input(
    item: ResearchMarketCostInputRefreshSlaInput,
    *,
    config: ResearchMarketCostInputRefreshSlaConfig,
) -> ResearchMarketCostInputRefreshSlaRow:
    fee_freshness_score = _freshness_score(
        item.fee_age_seconds,
        config.max_watch_fee_age_seconds,
    )
    spread_observation_freshness_score = _freshness_score(
        item.spread_observation_age_seconds,
        config.max_watch_spread_observation_age_seconds,
    )
    settlement_friction_score = _inverse_ratio_score(
        item.settlement_friction_rate,
        config.max_watch_settlement_friction_rate,
    )
    manual_recheck_score = _quantize(ONE - item.manual_recheck_urgency)
    refresh_sla_score = _average(
        (
            fee_freshness_score,
            spread_observation_freshness_score,
            item.depth_confidence,
            settlement_friction_score,
            manual_recheck_score,
        ),
    )
    status = _row_status(item, config=config)
    return ResearchMarketCostInputRefreshSlaRow(
        research_key=item.research_key,
        fee_age_seconds=item.fee_age_seconds,
        spread_observation_age_seconds=item.spread_observation_age_seconds,
        depth_confidence=item.depth_confidence,
        settlement_friction_rate=item.settlement_friction_rate,
        manual_recheck_urgency=item.manual_recheck_urgency,
        fee_freshness_score=fee_freshness_score,
        spread_observation_freshness_score=spread_observation_freshness_score,
        settlement_friction_score=settlement_friction_score,
        manual_recheck_score=manual_recheck_score,
        refresh_sla_score=refresh_sla_score,
        status=status,
        reason_codes=_row_reason_codes(item, status=status, config=config),
    )


def _freshness_score(value: Decimal, watch_value: Decimal) -> Decimal:
    return _inverse_ratio_score(value, watch_value)


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
    item: ResearchMarketCostInputRefreshSlaInput,
    *,
    config: ResearchMarketCostInputRefreshSlaConfig,
) -> str:
    if (
        item.fee_age_seconds > config.max_watch_fee_age_seconds
        or item.spread_observation_age_seconds
        > config.max_watch_spread_observation_age_seconds
        or item.depth_confidence < config.min_watch_depth_confidence
        or item.settlement_friction_rate > config.max_watch_settlement_friction_rate
        or item.manual_recheck_urgency > config.max_watch_manual_recheck_urgency
    ):
        return "block"
    if (
        item.fee_age_seconds > config.max_pass_fee_age_seconds
        or item.spread_observation_age_seconds
        > config.max_pass_spread_observation_age_seconds
        or item.depth_confidence < config.min_pass_depth_confidence
        or item.settlement_friction_rate > config.max_pass_settlement_friction_rate
        or item.manual_recheck_urgency > config.max_pass_manual_recheck_urgency
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    item: ResearchMarketCostInputRefreshSlaInput,
    *,
    status: str,
    config: ResearchMarketCostInputRefreshSlaConfig,
) -> tuple[str, ...]:
    codes = {
        f"cost_input_refresh_sla_{status}",
        f"manual_refresh_recheck_{status}",
        f"fee_freshness_{_fee_age_status(item.fee_age_seconds, config)}",
        (
            "spread_observation_age_"
            f"{_spread_age_status(item.spread_observation_age_seconds, config)}"
        ),
        f"depth_confidence_{_depth_status(item.depth_confidence, config)}",
        (
            "settlement_friction_"
            f"{_settlement_status(item.settlement_friction_rate, config)}"
        ),
        (
            "manual_recheck_urgency_"
            f"{_manual_status(item.manual_recheck_urgency, config)}"
        ),
    }
    for code in item.reason_codes:
        codes.add(f"input_{code}")
    return tuple(sorted(codes))


def _fee_age_status(
    value: Decimal,
    config: ResearchMarketCostInputRefreshSlaConfig,
) -> str:
    return _max_threshold_status(
        value,
        pass_value=config.max_pass_fee_age_seconds,
        watch_value=config.max_watch_fee_age_seconds,
    )


def _spread_age_status(
    value: Decimal,
    config: ResearchMarketCostInputRefreshSlaConfig,
) -> str:
    return _max_threshold_status(
        value,
        pass_value=config.max_pass_spread_observation_age_seconds,
        watch_value=config.max_watch_spread_observation_age_seconds,
    )


def _settlement_status(
    value: Decimal,
    config: ResearchMarketCostInputRefreshSlaConfig,
) -> str:
    return _max_threshold_status(
        value,
        pass_value=config.max_pass_settlement_friction_rate,
        watch_value=config.max_watch_settlement_friction_rate,
    )


def _manual_status(
    value: Decimal,
    config: ResearchMarketCostInputRefreshSlaConfig,
) -> str:
    return _max_threshold_status(
        value,
        pass_value=config.max_pass_manual_recheck_urgency,
        watch_value=config.max_watch_manual_recheck_urgency,
    )


def _max_threshold_status(value: Decimal, *, pass_value: Decimal, watch_value: Decimal) -> str:
    if value > watch_value:
        return "block"
    if value > pass_value:
        return "watch"
    return "pass"


def _depth_status(
    value: Decimal,
    config: ResearchMarketCostInputRefreshSlaConfig,
) -> str:
    if value < config.min_watch_depth_confidence:
        return "block"
    if value < config.min_pass_depth_confidence:
        return "watch"
    return "pass"


def _normalize_inputs(
    inputs: Iterable[object],
) -> tuple[ResearchMarketCostInputRefreshSlaInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        values = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    return tuple(_coerce_input(value) for value in values)


def _coerce_input(value: object) -> ResearchMarketCostInputRefreshSlaInput:
    if type(value) is ResearchMarketCostInputRefreshSlaInput:
        _require_hard_flags("input", value)
        return value
    _require_hard_flags("input", value)
    return ResearchMarketCostInputRefreshSlaInput(
        research_key=_field_value(value, "research_key"),
        fee_age_seconds=_field_value(value, "fee_age_seconds"),
        spread_observation_age_seconds=_field_value(
            value,
            "spread_observation_age_seconds",
        ),
        depth_confidence=_field_value(value, "depth_confidence"),
        settlement_friction_rate=_field_value(value, "settlement_friction_rate"),
        manual_recheck_urgency=_field_value(value, "manual_recheck_urgency"),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _summary_reason_codes(
    rows: tuple[ResearchMarketCostInputRefreshSlaRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_cost_input_refresh_sla_inputs",)
    if all(row.status == "pass" for row in rows):
        return ("cost_input_refresh_sla_pass",)
    codes: list[str] = []
    if any(row.status == "block" for row in rows):
        codes.append("cost_input_refresh_sla_block")
    elif any(row.status == "watch" for row in rows):
        codes.append("cost_input_refresh_sla_watch")
    row_codes = {code for row in rows for code in row.reason_codes}
    for code in COMPONENT_REASON_PRIORITY:
        if code in row_codes:
            codes.append(code)
    return tuple(codes)


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("no_cost_input_refresh_sla_inputs",):
        return "block"
    if "cost_input_refresh_sla_block" in reason_codes:
        return "block"
    if "cost_input_refresh_sla_watch" in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchMarketCostInputRefreshSlaRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchMarketCostInputRefreshSlaReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketCostInputRefreshSlaReasonCodeCount(
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
        ResearchMarketCostInputRefreshSlaReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            row_ratio=_quantize(Decimal(count) / row_count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: item[0])
    )


def _average_refresh_sla_score(
    rows: tuple[ResearchMarketCostInputRefreshSlaRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(
        sum((row.refresh_sla_score for row in rows), ZERO) / Decimal(len(rows)),
    )


def _minimum_row_value(
    rows: tuple[ResearchMarketCostInputRefreshSlaRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return min(getattr(row, field_name) for row in rows)


def _maximum_row_value(
    rows: tuple[ResearchMarketCostInputRefreshSlaRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _status_count(rows: tuple[ResearchMarketCostInputRefreshSlaRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _validate_row_consistency(row: ResearchMarketCostInputRefreshSlaRow) -> None:
    expected_score = _average(
        (
            row.fee_freshness_score,
            row.spread_observation_freshness_score,
            row.depth_confidence,
            row.settlement_friction_score,
            row.manual_recheck_score,
        ),
    )
    if row.refresh_sla_score != expected_score:
        raise ValueError("refresh_sla_score must match component scores")
    if f"cost_input_refresh_sla_{row.status}" not in row.reason_codes:
        raise ValueError("reason_codes must include row status")


def _validate_report_consistency(report: ResearchMarketCostInputRefreshSlaReport) -> None:
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
    if report.average_refresh_sla_score != _average_refresh_sla_score(report.rows):
        raise ValueError("average_refresh_sla_score must match rows")
    if report.max_fee_age_seconds != _maximum_row_value(report.rows, "fee_age_seconds"):
        raise ValueError("max_fee_age_seconds must match rows")
    if report.max_spread_observation_age_seconds != _maximum_row_value(
        report.rows,
        "spread_observation_age_seconds",
    ):
        raise ValueError("max_spread_observation_age_seconds must match rows")
    if report.min_depth_confidence != _minimum_row_value(report.rows, "depth_confidence"):
        raise ValueError("min_depth_confidence must match rows")
    if report.max_settlement_friction_rate != _maximum_row_value(
        report.rows,
        "settlement_friction_rate",
    ):
        raise ValueError("max_settlement_friction_rate must match rows")
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
    rows: tuple[ResearchMarketCostInputRefreshSlaRow, ...],
) -> tuple[ResearchMarketCostInputRefreshSlaRow, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketCostInputRefreshSlaRow:
            raise ValueError("rows must contain ResearchMarketCostInputRefreshSlaRow")
        _require_hard_flags("row", row)
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchMarketCostInputRefreshSlaReasonCodeCount, ...],
) -> tuple[ResearchMarketCostInputRefreshSlaReasonCodeCount, ...]:
    if not isinstance(counts, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchMarketCostInputRefreshSlaReasonCodeCount:
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
    if type(value) is not str or value not in COST_INPUT_REFRESH_SLA_STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")
    return value


def _require_public_label(name: str, value: object) -> str:
    if type(value) is not str or not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{name} must be a public label")
    if any(fragment in value.lower() for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{name} has unsafe public text")
    return value


def _require_reason_code(name: str, value: object) -> str:
    if type(value) is not str or not REASON_CODE_RE.fullmatch(value):
        raise ValueError(f"{name} must be a reason code")
    if any(fragment in value.lower() for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{name} has unsafe public text")
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
