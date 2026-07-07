"""Pure report-only screen for prediction-event arbitration risk.

Callers supply already-collected event risk facts. This module performs no
network, database, wallet, authentication, or execution work; it only returns
deterministic public report payloads.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


__all__ = (
    "ResearchArbitrationRiskScreenConfig",
    "ResearchArbitrationRiskScreenEvent",
    "ResearchArbitrationRiskScreenReasonCodeCount",
    "ResearchArbitrationRiskScreenReport",
    "ResearchArbitrationRiskScreenRow",
    "build_research_arbitration_risk_screen_report",
    "research_arbitration_risk_screen_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-arbitration-risk-screen-report-v0"
STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
DEFAULT_PASS_MAX_RISK_SCORE = Decimal("0.300000")
DEFAULT_WATCH_MAX_RISK_SCORE = Decimal("0.600000")
DEFAULT_COMPONENT_WATCH_SCORE = Decimal("0.500000")
DEFAULT_RULE_CLEAR_SCORE = Decimal("0.750000")
_SAFE_FLAG_KEYS = ("paper_only", "report_only", "readonly")
_UNSAFE_PUBLIC_FRAGMENTS = (
    "wallet",
    "auth",
    "order",
    "api_key",
    "secret",
    "token",
    "private_key",
    "signature",
    "trade",
    "buy",
    "sell",
)


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class ResearchArbitrationRiskScreenConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    pass_max_risk_score: Decimal = DEFAULT_PASS_MAX_RISK_SCORE
    watch_max_risk_score: Decimal = DEFAULT_WATCH_MAX_RISK_SCORE
    min_rule_clarity_score: Decimal = Decimal("0.250000")
    max_source_dependency_score: Decimal = Decimal("0.850000")
    max_human_adjudication_score: Decimal = Decimal("0.850000")
    max_dispute_history_score: Decimal = Decimal("0.850000")
    component_watch_score: Decimal = DEFAULT_COMPONENT_WATCH_SCORE
    rule_clear_score: Decimal = DEFAULT_RULE_CLEAR_SCORE
    rule_clarity_weight: Decimal = Decimal("0.350000")
    source_dependency_weight: Decimal = Decimal("0.250000")
    human_adjudication_weight: Decimal = Decimal("0.200000")
    dispute_history_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchArbitrationRiskScreenConfig:
            raise TypeError(
                "ResearchArbitrationRiskScreenConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchArbitrationRiskScreenConfig:
            raise ValueError(
                "config must be exactly ResearchArbitrationRiskScreenConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_max_risk_score",
            "watch_max_risk_score",
            "min_rule_clarity_score",
            "max_source_dependency_score",
            "max_human_adjudication_score",
            "max_dispute_history_score",
            "component_watch_score",
            "rule_clear_score",
            "rule_clarity_weight",
            "source_dependency_weight",
            "human_adjudication_weight",
            "dispute_history_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_max_risk_score >= self.watch_max_risk_score:
            raise ValueError("pass_max_risk_score must be below watch_max_risk_score")
        if self.min_rule_clarity_score >= self.rule_clear_score:
            raise ValueError("min_rule_clarity_score must be below rule_clear_score")
        weight_sum = _quantize(
            self.rule_clarity_weight
            + self.source_dependency_weight
            + self.human_adjudication_weight
            + self.dispute_history_weight,
        )
        if weight_sum != ONE:
            raise ValueError("risk component weights must sum to 1")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchArbitrationRiskScreenEvent:
    event_id: str
    market_slug: str
    rule_clarity_score: Decimal
    source_dependency_score: Decimal
    human_adjudication_score: Decimal
    dispute_history_score: Decimal
    resolution_source_count: Decimal = Decimal("1")
    prior_dispute_count: Decimal = Decimal("0")
    human_adjudication_required: bool = False
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchArbitrationRiskScreenEvent:
            raise TypeError(
                "ResearchArbitrationRiskScreenEvent does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchArbitrationRiskScreenEvent:
            raise ValueError(
                "event must be exactly ResearchArbitrationRiskScreenEvent",
            )
        _require_canonical_string("event_id", self.event_id)
        _require_canonical_string("market_slug", self.market_slug)
        for field_name in (
            "rule_clarity_score",
            "source_dependency_score",
            "human_adjudication_score",
            "dispute_history_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("resolution_source_count", "prior_dispute_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.resolution_source_count <= ZERO:
            raise ValueError("resolution_source_count must be positive")
        if type(self.human_adjudication_required) is not bool:
            raise ValueError("human_adjudication_required must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("event", self)
        _reject_unsafe_public_payload("event", self)


@dataclass(frozen=True)
class ResearchArbitrationRiskScreenRow:
    event_id: str
    market_slug: str
    rule_clarity_score: Decimal
    rule_ambiguity_score: Decimal
    source_dependency_score: Decimal
    human_adjudication_score: Decimal
    dispute_history_score: Decimal
    resolution_source_count: Decimal
    prior_dispute_count: Decimal
    human_adjudication_required: bool
    arbitration_risk_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchArbitrationRiskScreenRow:
            raise TypeError(
                "ResearchArbitrationRiskScreenRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchArbitrationRiskScreenRow:
            raise ValueError("row must be exactly ResearchArbitrationRiskScreenRow")
        _require_canonical_string("event_id", self.event_id)
        _require_canonical_string("market_slug", self.market_slug)
        for field_name in (
            "rule_clarity_score",
            "rule_ambiguity_score",
            "source_dependency_score",
            "human_adjudication_score",
            "dispute_history_score",
            "arbitration_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("resolution_source_count", "prior_dispute_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.resolution_source_count <= ZERO:
            raise ValueError("resolution_source_count must be positive")
        if type(self.human_adjudication_required) is not bool:
            raise ValueError("human_adjudication_required must be a bool")
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchArbitrationRiskScreenReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchArbitrationRiskScreenReasonCodeCount:
            raise TypeError(
                "ResearchArbitrationRiskScreenReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchArbitrationRiskScreenReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchArbitrationRiskScreenReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchArbitrationRiskScreenReport:
    generated_at: datetime
    config_version: str
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_arbitration_risk_score: Decimal | None
    status: str
    rows: tuple[ResearchArbitrationRiskScreenRow, ...]
    reason_code_counts: tuple[ResearchArbitrationRiskScreenReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchArbitrationRiskScreenReport:
            raise TypeError(
                "ResearchArbitrationRiskScreenReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchArbitrationRiskScreenReport:
            raise ValueError(
                "report must be exactly ResearchArbitrationRiskScreenReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in ("event_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_arbitration_risk_score",
            _require_optional_probability_decimal(
                "average_arbitration_risk_score",
                self.average_arbitration_risk_score,
            ),
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
        _reject_unsafe_public_payload("report", self)
        _validate_report_consistency(self)


def build_research_arbitration_risk_screen_report(
    events: Iterable[object],
    *,
    config: ResearchArbitrationRiskScreenConfig | None = None,
    generated_at: datetime | None = None,
) -> ResearchArbitrationRiskScreenReport:
    cfg = config or ResearchArbitrationRiskScreenConfig()
    if type(cfg) is not ResearchArbitrationRiskScreenConfig:
        raise ValueError("config must be exactly ResearchArbitrationRiskScreenConfig")
    _require_hard_flags("config", cfg)
    _reject_unsafe_public_payload("config", cfg)
    generated = _as_utc("generated_at", generated_at or datetime.now(UTC))
    normalized_events = _normalize_events(events)
    rows = tuple(
        _build_row(event, cfg)
        for event in sorted(
            normalized_events,
            key=lambda event: (event.event_id, event.market_slug),
        )
    )
    reason_codes = _summary_reason_codes(rows)

    return ResearchArbitrationRiskScreenReport(
        generated_at=generated,
        config_version=cfg.config_version,
        event_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_arbitration_risk_score=_average_arbitration_risk_score(rows),
        status=_summary_status(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_arbitration_risk_screen_report_payload(
    report: ResearchArbitrationRiskScreenReport,
) -> dict[str, Any]:
    if type(report) is not ResearchArbitrationRiskScreenReport:
        raise ValueError("report must be exactly ResearchArbitrationRiskScreenReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    _reject_unsafe_public_payload("report payload", payload)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    return payload


def _build_row(
    event: ResearchArbitrationRiskScreenEvent,
    config: ResearchArbitrationRiskScreenConfig,
) -> ResearchArbitrationRiskScreenRow:
    rule_ambiguity_score = _quantize(ONE - event.rule_clarity_score)
    risk_score = _quantize(
        (rule_ambiguity_score * config.rule_clarity_weight)
        + (event.source_dependency_score * config.source_dependency_weight)
        + (event.human_adjudication_score * config.human_adjudication_weight)
        + (event.dispute_history_score * config.dispute_history_weight),
    )
    has_block_component = _has_block_component(event, config)
    has_watch_component = _has_watch_component(event, config)
    status = _row_status(
        risk_score=risk_score,
        has_block_component=has_block_component,
        has_watch_component=has_watch_component,
        config=config,
    )
    reason_codes = _row_reason_codes(
        event=event,
        rule_ambiguity_score=rule_ambiguity_score,
        risk_score=risk_score,
        status=status,
        has_block_component=has_block_component,
        has_watch_component=has_watch_component,
        config=config,
    )

    return ResearchArbitrationRiskScreenRow(
        event_id=event.event_id,
        market_slug=event.market_slug,
        rule_clarity_score=event.rule_clarity_score,
        rule_ambiguity_score=rule_ambiguity_score,
        source_dependency_score=event.source_dependency_score,
        human_adjudication_score=event.human_adjudication_score,
        dispute_history_score=event.dispute_history_score,
        resolution_source_count=event.resolution_source_count,
        prior_dispute_count=event.prior_dispute_count,
        human_adjudication_required=event.human_adjudication_required,
        arbitration_risk_score=risk_score,
        status=status,
        reason_codes=reason_codes,
    )


def _has_block_component(
    event: ResearchArbitrationRiskScreenEvent,
    config: ResearchArbitrationRiskScreenConfig,
) -> bool:
    return (
        event.rule_clarity_score < config.min_rule_clarity_score
        or event.source_dependency_score >= config.max_source_dependency_score
        or event.human_adjudication_score >= config.max_human_adjudication_score
        or event.dispute_history_score >= config.max_dispute_history_score
    )


def _has_watch_component(
    event: ResearchArbitrationRiskScreenEvent,
    config: ResearchArbitrationRiskScreenConfig,
) -> bool:
    return (
        event.rule_clarity_score < config.rule_clear_score
        or event.source_dependency_score > config.component_watch_score
        or event.human_adjudication_score > config.component_watch_score
        or event.dispute_history_score > config.component_watch_score
        or event.resolution_source_count == ONE
        or event.prior_dispute_count > ZERO
        or event.human_adjudication_required
    )


def _row_status(
    *,
    risk_score: Decimal,
    has_block_component: bool,
    has_watch_component: bool,
    config: ResearchArbitrationRiskScreenConfig,
) -> str:
    if has_block_component or risk_score > config.watch_max_risk_score:
        return "block"
    if risk_score <= config.pass_max_risk_score and not has_watch_component:
        return "pass"
    return "watch"


def _row_reason_codes(
    *,
    event: ResearchArbitrationRiskScreenEvent,
    rule_ambiguity_score: Decimal,
    risk_score: Decimal,
    status: str,
    has_block_component: bool,
    has_watch_component: bool,
    config: ResearchArbitrationRiskScreenConfig,
) -> tuple[str, ...]:
    reason_codes: set[str] = {f"research_arbitration_risk_{status}"}
    reason_codes.add(
        "rules_clear"
        if event.rule_clarity_score >= config.rule_clear_score
        else "rules_ambiguous",
    )
    reason_codes.add(
        "source_dependency_low"
        if event.source_dependency_score <= config.pass_max_risk_score
        else "source_dependency_elevated",
    )
    reason_codes.add(
        "human_adjudication_low"
        if event.human_adjudication_score <= config.pass_max_risk_score
        else "human_adjudication_elevated",
    )
    reason_codes.add(
        "dispute_history_low"
        if event.dispute_history_score <= config.pass_max_risk_score
        else "dispute_history_elevated",
    )
    reason_codes.add(
        "multiple_resolution_sources"
        if event.resolution_source_count > ONE
        else "single_resolution_source",
    )
    if event.human_adjudication_required:
        reason_codes.add("human_adjudication_required")
    if event.prior_dispute_count > ZERO:
        reason_codes.add("prior_disputes_present")
    if rule_ambiguity_score > config.component_watch_score:
        reason_codes.add("high_rule_ambiguity")
    if risk_score > config.watch_max_risk_score:
        reason_codes.add("aggregate_risk_above_watch_threshold")
    if has_block_component:
        reason_codes.add("hard_component_block")
    elif has_watch_component:
        reason_codes.add("component_watch")
    for reason_code in event.reason_codes:
        reason_codes.add(f"input_{reason_code}")
    return tuple(sorted(reason_codes))


def _normalize_events(
    events: Iterable[object],
) -> tuple[ResearchArbitrationRiskScreenEvent, ...]:
    if isinstance(events, (str, bytes)):
        raise ValueError("events must be an iterable")
    try:
        values = tuple(events)
    except TypeError as exc:
        raise ValueError("events must be an iterable") from exc
    return tuple(_coerce_event(value) for value in values)


def _coerce_event(value: object) -> ResearchArbitrationRiskScreenEvent:
    _reject_unsafe_surface_fields("event", value)
    if type(value) is ResearchArbitrationRiskScreenEvent:
        _require_hard_flags("event", value)
        _reject_unsafe_public_payload("event", value)
        return value
    _require_hard_flags("event", value)
    return ResearchArbitrationRiskScreenEvent(
        event_id=_field_value(value, "event_id"),
        market_slug=_field_value(value, "market_slug"),
        rule_clarity_score=_field_value(value, "rule_clarity_score"),
        source_dependency_score=_field_value(value, "source_dependency_score"),
        human_adjudication_score=_field_value(value, "human_adjudication_score"),
        dispute_history_score=_field_value(value, "dispute_history_score"),
        resolution_source_count=_field_value(
            value,
            "resolution_source_count",
            default=ONE,
        ),
        prior_dispute_count=_field_value(value, "prior_dispute_count", default=ZERO),
        human_adjudication_required=_field_value(
            value,
            "human_adjudication_required",
            default=False,
        ),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _summary_reason_codes(
    rows: tuple[ResearchArbitrationRiskScreenRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_arbitration_risk_events",)
    if any(row.status == "block" for row in rows):
        return tuple(sorted({code for row in rows for code in row.reason_codes}))
    if all(row.status == "pass" for row in rows):
        return ("research_arbitration_risk_pass",)
    return tuple(sorted({code for row in rows for code in row.reason_codes}))


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("no_arbitration_risk_events",):
        return "block"
    if "research_arbitration_risk_block" in reason_codes:
        return "block"
    if "research_arbitration_risk_watch" in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchArbitrationRiskScreenRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchArbitrationRiskScreenReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchArbitrationRiskScreenReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchArbitrationRiskScreenReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _average_arbitration_risk_score(
    rows: tuple[ResearchArbitrationRiskScreenRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(
        sum((row.arbitration_risk_score for row in rows), ZERO) / Decimal(len(rows)),
    )


def _status_count(rows: tuple[ResearchArbitrationRiskScreenRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_rows(
    rows: tuple[ResearchArbitrationRiskScreenRow, ...],
) -> tuple[ResearchArbitrationRiskScreenRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchArbitrationRiskScreenRow:
            raise ValueError("rows must contain ResearchArbitrationRiskScreenRow values")
        _require_hard_flags("row", row)
        _reject_unsafe_public_payload("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: (row.event_id, row.market_slug)))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by event_id and market_slug")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchArbitrationRiskScreenReasonCodeCount, ...],
) -> tuple[ResearchArbitrationRiskScreenReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchArbitrationRiskScreenReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchArbitrationRiskScreenReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
        _reject_unsafe_public_payload("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row_consistency(row: ResearchArbitrationRiskScreenRow) -> None:
    if row.rule_ambiguity_score != _quantize(ONE - row.rule_clarity_score):
        raise ValueError("rule_ambiguity_score must match rule_clarity_score")
    if f"research_arbitration_risk_{row.status}" not in row.reason_codes:
        raise ValueError("reason_codes must include status reason code")


def _validate_report_consistency(report: ResearchArbitrationRiskScreenReport) -> None:
    if report.event_count != _decimal_count(len(report.rows)):
        raise ValueError("event_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_arbitration_risk_score != _average_arbitration_risk_score(
        report.rows,
    ):
        raise ValueError("average_arbitration_risk_score must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(report.reason_codes):
        raise ValueError("status must match reason_codes")


def _field_value(
    value: object,
    field_name: str,
    *,
    default: object = _MISSING,
) -> object:
    if isinstance(value, Mapping):
        if field_name in value:
            return value[field_name]
        if default is not _MISSING:
            return default
        raise ValueError(f"{field_name} is required")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{field_name} is required")


def _payload_value(value: object) -> object:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("payload Decimal values must be exact Decimal")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("payload datetime values must be exact datetime")
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_optional_probability_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(field_name, value)


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_whole_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_reason_code(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value.lower() != value:
        raise ValueError(f"{field_name} must be lowercase")
    if not all(char.isalnum() or char in ("_", "-") for char in value):
        raise ValueError(f"{field_name} must be machine-readable")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in _SAFE_FLAG_KEYS:
        if _field_value(value, flag_name, default=None) is not True:
            raise ValueError(f"{field_name} must be {flag_name}")


def _reject_unsafe_surface_fields(label: str, value: object) -> None:
    if isinstance(value, Mapping):
        names = tuple(str(key) for key in value.keys())
    elif is_dataclass(value) and not isinstance(value, type):
        names = tuple(field.name for field in fields(value))
    else:
        names = tuple(vars(value)) if hasattr(value, "__dict__") else ()
    for name in names:
        if _has_unsafe_fragment(name):
            raise ValueError(f"{label} has unsafe public field")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or label} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if type(value) is float:
        raise ValueError(f"{path or label} must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if type(value) is str:
        if _has_unsafe_fragment(value):
            raise ValueError(f"{path or label} has unsafe value")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if key not in _SAFE_FLAG_KEYS and _has_unsafe_fragment(key):
                raise ValueError(f"unsafe public field in {label}")
            if key in _SAFE_FLAG_KEYS and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError(f"{path or label} is not JSON serializable")


def _has_unsafe_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS)
