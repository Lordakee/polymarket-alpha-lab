"""Report-only cost-friction priority scoring for probability event research.

The module is deterministic and side-effect free. Callers provide local,
already-collected friction inputs; the output is a readonly research report
with pass/watch/blocked priority statuses and explanatory reason codes.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


__all__ = (
    "DEFAULT_RESEARCH_COST_FRICTION_PRIORITY_REPORT_CONFIG_VERSION",
    "ResearchCostFrictionPriorityConfig",
    "ResearchCostFrictionPriorityInput",
    "ResearchCostFrictionPriorityReasonCodeCount",
    "ResearchCostFrictionPriorityReport",
    "ResearchCostFrictionPriorityRow",
    "build_research_cost_friction_priority_report",
    "research_cost_friction_priority_report_payload",
)


DEFAULT_RESEARCH_COST_FRICTION_PRIORITY_REPORT_CONFIG_VERSION = (
    "research-cost-friction-priority-report-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUSES = ("pass", "watch", "blocked")
STATUS_WEIGHT = {
    "blocked": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
SUMMARY_EXPLANATION_BY_STATUS = {
    "pass": "pass: cost friction within research limits",
    "watch": "watch: cost friction requires research review",
    "blocked": "blocked: one or more cost friction rows exceed research limits",
}
ROW_EXPLANATION_BY_STATUS = {
    "pass": "pass: cost friction within research limits",
    "watch": "watch: cost friction is elevated; keep under research review",
    "blocked": "blocked: cost friction exceeds research limits; keep in research queue",
}
REPORT_REASON_PRIORITY = (
    "cost_total_friction_blocked",
    "cost_spread_blocked",
    "cost_settlement_delay_blocked",
    "cost_resolution_friction_blocked",
    "cost_liquidity_thin_blocked",
    "cost_total_friction_watch",
    "cost_spread_watch",
    "cost_settlement_delay_watch",
    "cost_resolution_friction_watch",
    "cost_liquidity_thin_watch",
)
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
UNSAFE_PUBLIC_FRAGMENTS = (
    "market",
    "source",
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
    "position",
    "recommendation",
)
HEX_CHARS = frozenset("0123456789abcdef")


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise ValueError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchCostFrictionPriorityConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_RESEARCH_COST_FRICTION_PRIORITY_REPORT_CONFIG_VERSION
    max_pass_total_friction_rate: Decimal = Decimal("0.030000")
    max_watch_total_friction_rate: Decimal = Decimal("0.060000")
    max_pass_spread_rate: Decimal = Decimal("0.020000")
    max_watch_spread_rate: Decimal = Decimal("0.040000")
    max_pass_settlement_delay_days: Decimal = Decimal("7.000000")
    max_watch_settlement_delay_days: Decimal = Decimal("30.000000")
    max_pass_resolution_dispute_risk: Decimal = Decimal("0.200000")
    max_watch_resolution_dispute_risk: Decimal = Decimal("0.500000")
    min_pass_liquidity_score: Decimal = Decimal("0.600000")
    min_watch_liquidity_score: Decimal = Decimal("0.300000")
    settlement_delay_cost_per_day: Decimal = Decimal("0.000100")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchCostFrictionPriorityConfig, "config")
        _require_private_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_COST_FRICTION_PRIORITY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_pass_total_friction_rate",
            "max_watch_total_friction_rate",
            "max_pass_spread_rate",
            "max_watch_spread_rate",
            "max_pass_resolution_dispute_risk",
            "max_watch_resolution_dispute_risk",
            "min_pass_liquidity_score",
            "min_watch_liquidity_score",
            "settlement_delay_cost_per_day",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_settlement_delay_days",
            "max_watch_settlement_delay_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.max_pass_total_friction_rate > self.max_watch_total_friction_rate:
            raise ValueError("total friction threshold ordering is invalid")
        if self.max_pass_spread_rate > self.max_watch_spread_rate:
            raise ValueError("spread threshold ordering is invalid")
        if self.max_pass_settlement_delay_days > self.max_watch_settlement_delay_days:
            raise ValueError("settlement delay threshold ordering is invalid")
        if (
            self.max_pass_resolution_dispute_risk
            > self.max_watch_resolution_dispute_risk
        ):
            raise ValueError("resolution dispute threshold ordering is invalid")
        if self.min_pass_liquidity_score < self.min_watch_liquidity_score:
            raise ValueError("liquidity threshold ordering is invalid")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchCostFrictionPriorityInput(_FinalPublicDataclass):
    event_id: str
    market_slug: str
    source_label: str
    fee_rate: Decimal
    spread_rate: Decimal
    slippage_rate: Decimal
    settlement_delay_days: Decimal
    resolution_dispute_risk: Decimal
    liquidity_score: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchCostFrictionPriorityInput, "input")
        for field_name in ("event_id", "market_slug", "source_label"):
            _require_private_string(field_name, getattr(self, field_name))
        for field_name in (
            "fee_rate",
            "spread_rate",
            "slippage_rate",
            "resolution_dispute_risk",
            "liquidity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "settlement_delay_days",
            _require_nonnegative_decimal(
                "settlement_delay_days",
                self.settlement_delay_days,
            ),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchCostFrictionPriorityRow(_FinalPublicDataclass):
    event_id: str
    market_slug: str
    source_label: str
    public_event_ref: str
    priority_status: str
    priority_score: Decimal
    fee_rate: Decimal
    spread_rate: Decimal
    slippage_rate: Decimal
    settlement_delay_days: Decimal
    settlement_friction_rate: Decimal
    total_friction_rate: Decimal
    resolution_dispute_risk: Decimal
    liquidity_score: Decimal
    observed_at: datetime
    friction_explanation: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchCostFrictionPriorityRow, "row")
        for field_name in ("event_id", "market_slug", "source_label"):
            _require_private_string(field_name, getattr(self, field_name))
        _require_public_ref("public_event_ref", self.public_event_ref)
        _require_status("priority_status", self.priority_status)
        for field_name in (
            "priority_score",
            "fee_rate",
            "spread_rate",
            "slippage_rate",
            "settlement_friction_rate",
            "total_friction_rate",
            "resolution_dispute_risk",
            "liquidity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "settlement_delay_days",
            _require_nonnegative_decimal(
                "settlement_delay_days",
                self.settlement_delay_days,
            ),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_public_string("friction_explanation", self.friction_explanation)
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchCostFrictionPriorityReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    event_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchCostFrictionPriorityReasonCodeCount,
            "reason_code_count",
        )
        _require_public_string("reason_code", self.reason_code)
        object.__setattr__(self, "count", _require_count_decimal("count", self.count))
        object.__setattr__(
            self,
            "event_ratio",
            _require_ratio_decimal("event_ratio", self.event_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchCostFrictionPriorityReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    max_total_friction_rate: Decimal
    max_spread_rate: Decimal
    max_settlement_delay_days: Decimal
    max_resolution_dispute_risk: Decimal
    min_liquidity_score: Decimal
    status: str
    summary_explanation: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchCostFrictionPriorityReasonCodeCount, ...]
    rows: tuple[ResearchCostFrictionPriorityRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchCostFrictionPriorityReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_COST_FRICTION_PRIORITY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "event_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_total_friction_rate",
            "max_spread_rate",
            "max_resolution_dispute_risk",
            "min_liquidity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_settlement_delay_days",
            _require_nonnegative_decimal(
                "max_settlement_delay_days",
                self.max_settlement_delay_days,
            ),
        )
        _require_status("status", self.status)
        _require_public_string("summary_explanation", self.summary_explanation)
        object.__setattr__(
            self,
            "reason_codes",
            _require_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _require_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _require_rows(self.rows))
        _validate_report_materialized_fields(self)
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
        _require_hard_flags("report", self)


def build_research_cost_friction_priority_report(
    events: Iterable[ResearchCostFrictionPriorityInput],
    *,
    config: ResearchCostFrictionPriorityConfig,
    generated_at: datetime,
) -> ResearchCostFrictionPriorityReport:
    if type(config) is not ResearchCostFrictionPriorityConfig:
        raise ValueError("config must be a ResearchCostFrictionPriorityConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(events)
    for item in inputs:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be in the future")
    rows_without_public_refs = tuple(
        sorted(
            (_row_from_input(item, config=config) for item in inputs),
            key=_row_sort_key,
        ),
    )
    rows = tuple(
        _copy_row_with_public_ref(row, index)
        for index, row in enumerate(rows_without_public_refs, start=1)
    )
    status = _rollup_status(tuple(row.priority_status for row in rows))
    return ResearchCostFrictionPriorityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        event_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        max_total_friction_rate=_max_decimal(
            tuple(row.total_friction_rate for row in rows),
        ),
        max_spread_rate=_max_decimal(tuple(row.spread_rate for row in rows)),
        max_settlement_delay_days=_max_decimal(
            tuple(row.settlement_delay_days for row in rows),
        ),
        max_resolution_dispute_risk=_max_decimal(
            tuple(row.resolution_dispute_risk for row in rows),
        ),
        min_liquidity_score=_min_decimal(tuple(row.liquidity_score for row in rows)),
        status=status,
        summary_explanation=_summary_explanation(status, rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_cost_friction_priority_report_payload(
    report: ResearchCostFrictionPriorityReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchCostFrictionPriorityReport:
        _require_hard_flags("report", report)
        payload = _public_payload_from_report(report, include_digest=True)
        _reject_unsafe_public_payload("payload", payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _reject_public_numeric_values(report)
        payload = _json_ready(report)
        if not isinstance(payload, dict):
            raise ValueError("report payload must be an object")
        _require_hard_flags("payload", _PayloadFlags(payload))
        supplied_digest = payload.get("derived_validation_digest")
        if type(supplied_digest) is not str:
            raise ValueError("derived_validation_digest is required")
        _require_sha256("derived_validation_digest", supplied_digest)
        if supplied_digest != _payload_validation_digest(payload):
            raise ValueError("derived_validation_digest does not match report payload")
        return payload
    raise ValueError("report must be a ResearchCostFrictionPriorityReport")


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
    events: Iterable[ResearchCostFrictionPriorityInput],
) -> tuple[ResearchCostFrictionPriorityInput, ...]:
    if isinstance(events, (str, bytes)):
        raise ValueError("events must be an iterable")
    try:
        values = tuple(events)
    except TypeError as exc:
        raise ValueError("events must be an iterable") from exc
    normalized: list[ResearchCostFrictionPriorityInput] = []
    seen_event_ids: set[str] = set()
    for value in values:
        if type(value) is not ResearchCostFrictionPriorityInput:
            raise ValueError("events must contain ResearchCostFrictionPriorityInput")
        _require_hard_flags("input", value)
        if value.event_id in seen_event_ids:
            raise ValueError("event_id values must be unique")
        seen_event_ids.add(value.event_id)
        normalized.append(value)
    return tuple(normalized)


def _row_from_input(
    item: ResearchCostFrictionPriorityInput,
    *,
    config: ResearchCostFrictionPriorityConfig,
) -> ResearchCostFrictionPriorityRow:
    settlement_friction_rate = _quantize(
        item.settlement_delay_days * config.settlement_delay_cost_per_day,
    )
    total_friction_rate = _quantize(
        item.fee_rate
        + item.spread_rate
        + item.slippage_rate
        + settlement_friction_rate,
    )
    status = _row_status(
        total_friction_rate=total_friction_rate,
        spread_rate=item.spread_rate,
        settlement_delay_days=item.settlement_delay_days,
        resolution_dispute_risk=item.resolution_dispute_risk,
        liquidity_score=item.liquidity_score,
        config=config,
    )
    return ResearchCostFrictionPriorityRow(
        event_id=item.event_id,
        market_slug=item.market_slug,
        source_label=item.source_label,
        public_event_ref="event_000000",
        priority_status=status,
        priority_score=STATUS_WEIGHT[status] / Decimal("2.000000"),
        fee_rate=item.fee_rate,
        spread_rate=item.spread_rate,
        slippage_rate=item.slippage_rate,
        settlement_delay_days=item.settlement_delay_days,
        settlement_friction_rate=settlement_friction_rate,
        total_friction_rate=total_friction_rate,
        resolution_dispute_risk=item.resolution_dispute_risk,
        liquidity_score=item.liquidity_score,
        observed_at=item.observed_at,
        friction_explanation=ROW_EXPLANATION_BY_STATUS[status],
        reason_codes=_row_reason_codes(
            item,
            total_friction_rate=total_friction_rate,
            config=config,
        ),
    )


def _copy_row_with_public_ref(
    row: ResearchCostFrictionPriorityRow,
    index: int,
) -> ResearchCostFrictionPriorityRow:
    return ResearchCostFrictionPriorityRow(
        event_id=row.event_id,
        market_slug=row.market_slug,
        source_label=row.source_label,
        public_event_ref=f"event_{index:06d}",
        priority_status=row.priority_status,
        priority_score=row.priority_score,
        fee_rate=row.fee_rate,
        spread_rate=row.spread_rate,
        slippage_rate=row.slippage_rate,
        settlement_delay_days=row.settlement_delay_days,
        settlement_friction_rate=row.settlement_friction_rate,
        total_friction_rate=row.total_friction_rate,
        resolution_dispute_risk=row.resolution_dispute_risk,
        liquidity_score=row.liquidity_score,
        observed_at=row.observed_at,
        friction_explanation=row.friction_explanation,
        reason_codes=row.reason_codes,
    )


def _row_status(
    *,
    total_friction_rate: Decimal,
    spread_rate: Decimal,
    settlement_delay_days: Decimal,
    resolution_dispute_risk: Decimal,
    liquidity_score: Decimal,
    config: ResearchCostFrictionPriorityConfig,
) -> str:
    if (
        total_friction_rate > config.max_watch_total_friction_rate
        or spread_rate > config.max_watch_spread_rate
        or settlement_delay_days > config.max_watch_settlement_delay_days
        or resolution_dispute_risk > config.max_watch_resolution_dispute_risk
        or liquidity_score < config.min_watch_liquidity_score
    ):
        return "blocked"
    if (
        total_friction_rate > config.max_pass_total_friction_rate
        or spread_rate > config.max_pass_spread_rate
        or settlement_delay_days > config.max_pass_settlement_delay_days
        or resolution_dispute_risk > config.max_pass_resolution_dispute_risk
        or liquidity_score < config.min_pass_liquidity_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    item: ResearchCostFrictionPriorityInput,
    *,
    total_friction_rate: Decimal,
    config: ResearchCostFrictionPriorityConfig,
) -> tuple[str, ...]:
    reason_codes = list(item.reason_codes)
    if total_friction_rate > config.max_watch_total_friction_rate:
        reason_codes.append("cost_total_friction_blocked")
    elif total_friction_rate > config.max_pass_total_friction_rate:
        reason_codes.append("cost_total_friction_watch")

    if item.spread_rate > config.max_watch_spread_rate:
        reason_codes.append("cost_spread_blocked")
    elif item.spread_rate > config.max_pass_spread_rate:
        reason_codes.append("cost_spread_watch")

    if item.settlement_delay_days > config.max_watch_settlement_delay_days:
        reason_codes.append("cost_settlement_delay_blocked")
    elif item.settlement_delay_days > config.max_pass_settlement_delay_days:
        reason_codes.append("cost_settlement_delay_watch")

    if item.resolution_dispute_risk > config.max_watch_resolution_dispute_risk:
        reason_codes.append("cost_resolution_friction_blocked")
    elif item.resolution_dispute_risk > config.max_pass_resolution_dispute_risk:
        reason_codes.append("cost_resolution_friction_watch")

    if item.liquidity_score < config.min_watch_liquidity_score:
        reason_codes.append("cost_liquidity_thin_blocked")
    elif item.liquidity_score < config.min_pass_liquidity_score:
        reason_codes.append("cost_liquidity_thin_watch")

    if len(reason_codes) == len(item.reason_codes):
        reason_codes.append("cost_friction_clear")
    return tuple(reason_codes)


def _row_sort_key(row: ResearchCostFrictionPriorityRow) -> tuple[Decimal, Decimal, str]:
    return (-STATUS_WEIGHT[row.priority_status], -row.total_friction_rate, row.event_id)


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if "blocked" in statuses:
        return "blocked"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _summary_explanation(
    status: str,
    rows: tuple[ResearchCostFrictionPriorityRow, ...],
) -> str:
    if not rows:
        return "pass: no cost friction rows supplied"
    return SUMMARY_EXPLANATION_BY_STATUS[status]


def _report_reason_codes(
    rows: tuple[ResearchCostFrictionPriorityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("cost_friction_report_empty",)
    status = _rollup_status(tuple(row.priority_status for row in rows))
    row_reason_set = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code in REPORT_REASON_PRIORITY
    }
    ordered = tuple(
        reason_code
        for reason_code in REPORT_REASON_PRIORITY
        if reason_code in row_reason_set
    )
    return (f"cost_friction_report_{status}", *ordered)


def _reason_code_counts(
    rows: tuple[ResearchCostFrictionPriorityRow, ...],
) -> tuple[ResearchCostFrictionPriorityReasonCodeCount, ...]:
    if not rows:
        return ()
    counter: Counter[str] = Counter(
        reason_code for row in rows for reason_code in row.reason_codes
    )
    denominator = Decimal(len(rows))
    return tuple(
        ResearchCostFrictionPriorityReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
            event_ratio=_quantize(Decimal(count) / denominator),
        )
        for reason_code, count in sorted(
            counter.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _status_count(rows: tuple[ResearchCostFrictionPriorityRow, ...], status: str) -> Decimal:
    return _count(sum(1 for row in rows if row.priority_status == status))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _min_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return min(values)


def _validate_row(row: ResearchCostFrictionPriorityRow) -> None:
    settlement_friction_rate = _quantize(
        row.settlement_delay_days * Decimal("0.000100"),
    )
    if row.settlement_friction_rate != settlement_friction_rate:
        raise ValueError("settlement_friction_rate must match settlement delay")
    total_friction_rate = _quantize(
        row.fee_rate
        + row.spread_rate
        + row.slippage_rate
        + row.settlement_friction_rate,
    )
    if row.total_friction_rate != total_friction_rate:
        raise ValueError("total_friction_rate must match component friction rates")
    if row.priority_score != STATUS_WEIGHT[row.priority_status] / Decimal("2.000000"):
        raise ValueError("priority_score must match priority_status")
    if row.friction_explanation != ROW_EXPLANATION_BY_STATUS[row.priority_status]:
        raise ValueError("friction_explanation must match priority_status")


def _validate_report_materialized_fields(
    report: ResearchCostFrictionPriorityReport,
) -> None:
    rows = report.rows
    if report.event_count != _count(len(rows)):
        raise ValueError("event_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.max_total_friction_rate != _max_decimal(
        tuple(row.total_friction_rate for row in rows),
    ):
        raise ValueError("max_total_friction_rate must match rows")
    if report.max_spread_rate != _max_decimal(tuple(row.spread_rate for row in rows)):
        raise ValueError("max_spread_rate must match rows")
    if report.max_settlement_delay_days != _max_decimal(
        tuple(row.settlement_delay_days for row in rows),
    ):
        raise ValueError("max_settlement_delay_days must match rows")
    if report.max_resolution_dispute_risk != _max_decimal(
        tuple(row.resolution_dispute_risk for row in rows),
    ):
        raise ValueError("max_resolution_dispute_risk must match rows")
    if report.min_liquidity_score != _min_decimal(tuple(row.liquidity_score for row in rows)):
        raise ValueError("min_liquidity_score must match rows")
    expected_status = _rollup_status(tuple(row.priority_status for row in rows))
    if report.status != expected_status:
        raise ValueError("status must match rows")
    if report.summary_explanation != _summary_explanation(expected_status, rows):
        raise ValueError("summary_explanation must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _public_payload_from_report(
    report: ResearchCostFrictionPriorityReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "event_count": _decimal_payload(report.event_count),
        "pass_count": _decimal_payload(report.pass_count),
        "watch_count": _decimal_payload(report.watch_count),
        "blocked_count": _decimal_payload(report.blocked_count),
        "max_total_friction_rate": _decimal_payload(report.max_total_friction_rate),
        "max_spread_rate": _decimal_payload(report.max_spread_rate),
        "max_settlement_delay_days": _decimal_payload(report.max_settlement_delay_days),
        "max_resolution_dispute_risk": _decimal_payload(
            report.max_resolution_dispute_risk,
        ),
        "min_liquidity_score": _decimal_payload(report.min_liquidity_score),
        "status": report.status,
        "summary_explanation": report.summary_explanation,
        "reason_codes": list(report.reason_codes),
        "reason_code_counts": [
            {
                "reason_code": item.reason_code,
                "count": _decimal_payload(item.count),
                "event_ratio": _decimal_payload(item.event_ratio),
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            }
            for item in report.reason_code_counts
        ],
        "rows": [_public_payload_from_row(row) for row in report.rows],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    if include_digest:
        payload["derived_validation_digest"] = report.derived_validation_digest
    return payload


def _public_payload_from_row(row: ResearchCostFrictionPriorityRow) -> dict[str, Any]:
    return {
        "public_event_ref": row.public_event_ref,
        "priority_status": row.priority_status,
        "priority_score": _decimal_payload(row.priority_score),
        "fee_rate": _decimal_payload(row.fee_rate),
        "spread_rate": _decimal_payload(row.spread_rate),
        "slippage_rate": _decimal_payload(row.slippage_rate),
        "settlement_delay_days": _decimal_payload(row.settlement_delay_days),
        "settlement_friction_rate": _decimal_payload(row.settlement_friction_rate),
        "total_friction_rate": _decimal_payload(row.total_friction_rate),
        "resolution_dispute_risk": _decimal_payload(row.resolution_dispute_risk),
        "liquidity_score": _decimal_payload(row.liquidity_score),
        "observed_at": row.observed_at.isoformat(),
        "friction_explanation": row.friction_explanation,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _derived_validation_digest(report: ResearchCostFrictionPriorityReport) -> str:
    return _payload_validation_digest(
        _public_payload_from_report(report, include_digest=False),
    )


def _payload_validation_digest(payload: Mapping[str, Any]) -> str:
    public_payload = dict(payload)
    public_payload.pop("derived_validation_digest", None)
    normalized = _json_ready(public_payload)
    canonical = json.dumps(
        normalized,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if type(value) is Decimal:
        return _decimal_payload(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _reject_unsafe_public_payload(context: str, value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{context} contains unsafe public key")
            _reject_unsafe_public_text(context, key, is_key=True)
            _reject_unsafe_public_payload(context, item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(context, item)
    elif type(value) is str:
        _reject_unsafe_public_text(context, value, is_key=False)
    elif type(value) is Decimal:
        raise ValueError(f"{context} contains unsafe public numeric Decimal")
    elif type(value) in (int, float):
        raise ValueError(f"{context} contains unsafe public numeric value")


def _reject_unsafe_public_text(context: str, value: str, *, is_key: bool) -> None:
    lowered = value.lower()
    if is_key and value in PHASE_FLAG_FIELDS:
        return
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{context} contains unsafe public payload details")


def _reject_public_numeric_values(value: Any) -> None:
    if type(value) in (int, float, Decimal):
        raise ValueError("public payload numeric values must be strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_numeric_values(item)


def _require_rows(
    value: object,
) -> tuple[ResearchCostFrictionPriorityRow, ...]:
    if not isinstance(value, tuple):
        raise ValueError("rows must be a tuple")
    for item in value:
        if type(item) is not ResearchCostFrictionPriorityRow:
            raise ValueError("rows must contain ResearchCostFrictionPriorityRow")
        _require_hard_flags("row", item)
    return value


def _require_reason_code_counts(
    value: object,
) -> tuple[ResearchCostFrictionPriorityReasonCodeCount, ...]:
    if not isinstance(value, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    for item in value:
        if type(item) is not ResearchCostFrictionPriorityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchCostFrictionPriorityReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", item)
    return value


def _require_report_reason_codes(value: object) -> tuple[str, ...]:
    return _require_reason_codes(value, require_nonempty=True)


def _require_reason_codes(
    value: object,
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise ValueError("reason_codes must be a tuple")
    if require_nonempty and not value:
        raise ValueError("reason_codes must not be empty")
    normalized = tuple(_require_public_identifier("reason_code", item) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    return normalized


def _require_public_ref(field_name: str, value: object) -> str:
    text = _require_public_identifier(field_name, value)
    if not text.startswith("event_") or len(text) != len("event_000000"):
        raise ValueError(f"{field_name} must be a public event reference")
    suffix = text.removeprefix("event_")
    if not suffix.isdigit():
        raise ValueError(f"{field_name} must be a public event reference")
    return text


def _require_public_identifier(field_name: str, value: object) -> str:
    text = _require_public_string(field_name, value)
    allowed_chars = set("abcdefghijklmnopqrstuvwxyz0123456789_-")
    if any(char not in allowed_chars for char in text):
        raise ValueError(f"{field_name} must be a public identifier")
    return text


def _require_private_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    if any(ord(char) < 32 or ord(char) > 126 for char in value):
        raise ValueError(f"{field_name} must be printable ASCII")
    return value


def _require_public_string(field_name: str, value: object) -> str:
    text = _require_private_string(field_name, value)
    _reject_unsafe_public_text(field_name, text, is_key=False)
    return text


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")
    return value


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be less than or equal to 1")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    return _quantize(value)


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _decimal_payload(value: Decimal) -> str:
    return format(_quantize(value), "f")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], context: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{context} must be exactly {expected_type.__name__}")


def _require_hard_flags(context: str, value: object) -> None:
    require_paper_only_flags(context, value)
    for field_name in PHASE_FLAG_FIELDS:
        if type(getattr(value, field_name, None)) is not bool:
            raise ValueError(f"{context}.{field_name} must be a bool")
        if getattr(value, field_name) is not True:
            raise ValueError(f"{context}.{field_name} must be True")


def _require_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if len(value) != 64 or any(char not in HEX_CHARS for char in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value
