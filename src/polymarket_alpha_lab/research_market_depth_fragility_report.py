from __future__ import annotations

from dataclasses import InitVar, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from hashlib import sha256
from json import dumps
from typing import Any, Iterable


DEFAULT_RESEARCH_MARKET_DEPTH_FRAGILITY_REPORT_CONFIG_VERSION = (
    "research-market-depth-fragility-report-v0"
)

MARKET_DEPTH_FRAGILITY_STATUSES = ("pass", "watch", "block")
STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANT = Decimal("0.000001")

PASS_REASON = "market_depth_fragility_pass"
NO_INPUT_REASON = "no_market_depth_fragility_inputs"

AGGREGATE_DEPTH_WATCH_REASON = "aggregate_depth_fragility_watch"
AGGREGATE_DEPTH_BLOCK_REASON = "aggregate_depth_fragility_block"
SPREAD_WATCH_REASON = "spread_instability_watch"
SPREAD_BLOCK_REASON = "spread_instability_block"
COST_WATCH_REASON = "cost_pressure_watch"
COST_BLOCK_REASON = "cost_pressure_block"
SETTLEMENT_WATCH_REASON = "settlement_friction_watch"
SETTLEMENT_BLOCK_REASON = "settlement_friction_block"
COMPOSITE_WATCH_REASON = "composite_fragility_watch"
COMPOSITE_BLOCK_REASON = "composite_fragility_block"

AGGREGATE_DEPTH_PRESENT_REASON = "aggregate_depth_fragility_present"
SPREAD_PRESENT_REASON = "spread_instability_present"
COST_PRESENT_REASON = "cost_pressure_present"
SETTLEMENT_PRESENT_REASON = "settlement_friction_present"
COMPOSITE_PRESENT_REASON = "composite_fragility_present"

ROW_TO_REPORT_REASON = {
    AGGREGATE_DEPTH_WATCH_REASON: AGGREGATE_DEPTH_PRESENT_REASON,
    AGGREGATE_DEPTH_BLOCK_REASON: AGGREGATE_DEPTH_PRESENT_REASON,
    SPREAD_WATCH_REASON: SPREAD_PRESENT_REASON,
    SPREAD_BLOCK_REASON: SPREAD_PRESENT_REASON,
    COST_WATCH_REASON: COST_PRESENT_REASON,
    COST_BLOCK_REASON: COST_PRESENT_REASON,
    SETTLEMENT_WATCH_REASON: SETTLEMENT_PRESENT_REASON,
    SETTLEMENT_BLOCK_REASON: SETTLEMENT_PRESENT_REASON,
    COMPOSITE_WATCH_REASON: COMPOSITE_PRESENT_REASON,
    COMPOSITE_BLOCK_REASON: COMPOSITE_PRESENT_REASON,
}
REPORT_REASON_CODES = (
    AGGREGATE_DEPTH_PRESENT_REASON,
    SPREAD_PRESENT_REASON,
    COST_PRESENT_REASON,
    SETTLEMENT_PRESENT_REASON,
    COMPOSITE_PRESENT_REASON,
    PASS_REASON,
    NO_INPUT_REASON,
)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        "raw_market",
        "market_id",
        "market-id",
        "condition_id",
        "condition-id",
        "source_id",
        "source-id",
        "credential",
        "secret",
        "token",
        "api_key",
        "session",
        "cookie",
        "bearer",
        "account",
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("private", "_", "key"),
        _join_parts("bro", "ker"),
        _join_parts("ord", "er"),
        _join_parts("tra", "de"),
        _join_parts("tra", "ding"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("sig", "ning"),
        _join_parts("bu", "y"),
        _join_parts("se", "ll"),
        _join_parts("pos", "ition"),
    ),
)
HARD_FLAG_FIELDS = ("paper_only", "report_only", "readonly")


@dataclass(frozen=True)
class ResearchMarketDepthFragilityConfig:
    config_version: str = DEFAULT_RESEARCH_MARKET_DEPTH_FRAGILITY_REPORT_CONFIG_VERSION
    component_watch_score: Decimal = Decimal("0.350000")
    component_block_score: Decimal = Decimal("0.700000")
    composite_watch_score: Decimal = Decimal("0.350000")
    composite_block_score: Decimal = Decimal("0.700000")
    depth_weight: Decimal = Decimal("0.300000")
    spread_weight: Decimal = Decimal("0.250000")
    cost_weight: Decimal = Decimal("0.250000")
    settlement_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketDepthFragilityConfig:
            raise TypeError("ResearchMarketDepthFragilityConfig does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketDepthFragilityConfig:
            raise ValueError("config must be exactly ResearchMarketDepthFragilityConfig")
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_MARKET_DEPTH_FRAGILITY_REPORT_CONFIG_VERSION:
            raise ValueError("config_version must be supported")
        for field_name in (
            "component_watch_score",
            "component_block_score",
            "composite_watch_score",
            "composite_block_score",
            "depth_weight",
            "spread_weight",
            "cost_weight",
            "settlement_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_score_decimal(field_name, getattr(self, field_name)),
            )
        if self.component_block_score <= self.component_watch_score:
            raise ValueError("component_block_score must exceed component_watch_score")
        if self.composite_block_score <= self.composite_watch_score:
            raise ValueError("composite_block_score must exceed composite_watch_score")
        if (
            self.depth_weight
            + self.spread_weight
            + self.cost_weight
            + self.settlement_weight
        ) != ONE:
            raise ValueError(
                "depth_weight, spread_weight, cost_weight, and settlement_weight "
                "must sum to 1.000000",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketDepthFragilityInput:
    market_slug: str
    public_event_label: str
    observed_at: datetime
    aggregate_depth_fragility_score: Decimal
    spread_instability_score: Decimal
    cost_pressure_score: Decimal
    settlement_friction_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketDepthFragilityInput:
            raise TypeError("ResearchMarketDepthFragilityInput does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketDepthFragilityInput:
            raise ValueError("input must be exactly ResearchMarketDepthFragilityInput")
        for field_name in ("market_slug", "public_event_label"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "aggregate_depth_fragility_score",
            "spread_instability_score",
            "cost_pressure_score",
            "settlement_friction_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_score_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchMarketDepthFragilityRow:
    market_slug: str
    public_event_label: str
    observed_at: datetime
    aggregate_depth_fragility_score: Decimal
    spread_instability_score: Decimal
    cost_pressure_score: Decimal
    settlement_friction_score: Decimal
    composite_fragility_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[ResearchMarketDepthFragilityConfig | None] = None

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketDepthFragilityRow:
            raise TypeError("ResearchMarketDepthFragilityRow does not support subclassing")

    def __post_init__(self, validation_config: ResearchMarketDepthFragilityConfig | None) -> None:
        if type(self) is not ResearchMarketDepthFragilityRow:
            raise ValueError("row must be exactly ResearchMarketDepthFragilityRow")
        for field_name in ("market_slug", "public_event_label"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "aggregate_depth_fragility_score",
            "spread_instability_score",
            "cost_pressure_score",
            "settlement_friction_score",
            "composite_fragility_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_score_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _validate_row(
            self,
            config=validation_config or ResearchMarketDepthFragilityConfig(),
        )
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchMarketDepthFragilityReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketDepthFragilityReasonCodeCount:
            raise TypeError(
                "ResearchMarketDepthFragilityReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketDepthFragilityReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly ResearchMarketDepthFragilityReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _require_nonnegative_decimal("count", self.count))
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchMarketDepthFragilityReport:
    generated_at: datetime
    config_version: str
    status: str
    market_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    manual_review_count: Decimal
    aggregate_depth_fragility_count: Decimal
    spread_instability_count: Decimal
    cost_pressure_count: Decimal
    settlement_friction_count: Decimal
    composite_fragility_count: Decimal
    average_aggregate_depth_fragility_score: Decimal | None
    average_spread_instability_score: Decimal | None
    average_cost_pressure_score: Decimal | None
    average_settlement_friction_score: Decimal | None
    average_composite_fragility_score: Decimal | None
    rows: tuple[ResearchMarketDepthFragilityRow, ...]
    reason_code_counts: tuple[ResearchMarketDepthFragilityReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketDepthFragilityReport:
            raise TypeError("ResearchMarketDepthFragilityReport does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketDepthFragilityReport:
            raise ValueError("report must be exactly ResearchMarketDepthFragilityReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "market_count",
            "pass_count",
            "watch_count",
            "block_count",
            "manual_review_count",
            "aggregate_depth_fragility_count",
            "spread_instability_count",
            "cost_pressure_count",
            "settlement_friction_count",
            "composite_fragility_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_aggregate_depth_fragility_score",
            "average_spread_instability_score",
            "average_cost_pressure_score",
            "average_settlement_friction_score",
            "average_composite_fragility_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_optional_score_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_report_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_research_market_depth_fragility_report(
    rows: Iterable[object],
    *,
    config: ResearchMarketDepthFragilityConfig,
    generated_at: datetime,
) -> ResearchMarketDepthFragilityReport:
    if type(config) is not ResearchMarketDepthFragilityConfig:
        raise ValueError("config must be a ResearchMarketDepthFragilityConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    scored_rows = _sort_rows(
        tuple(_row_from_input(row, config=config) for row in _normalize_input_rows(rows)),
    )
    for row in scored_rows:
        if row.observed_at > generated_at_utc:
            raise ValueError("observed_at must be on or before generated_at")
    reason_codes = _report_reason_codes(scored_rows)
    return ResearchMarketDepthFragilityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(scored_rows),
        market_count=_count(len(scored_rows)),
        pass_count=_status_count(scored_rows, "pass"),
        watch_count=_status_count(scored_rows, "watch"),
        block_count=_status_count(scored_rows, "block"),
        manual_review_count=_count(sum(1 for row in scored_rows if row.status != "pass")),
        aggregate_depth_fragility_count=_reason_count(
            scored_rows,
            (AGGREGATE_DEPTH_WATCH_REASON, AGGREGATE_DEPTH_BLOCK_REASON),
        ),
        spread_instability_count=_reason_count(
            scored_rows,
            (SPREAD_WATCH_REASON, SPREAD_BLOCK_REASON),
        ),
        cost_pressure_count=_reason_count(scored_rows, (COST_WATCH_REASON, COST_BLOCK_REASON)),
        settlement_friction_count=_reason_count(
            scored_rows,
            (SETTLEMENT_WATCH_REASON, SETTLEMENT_BLOCK_REASON),
        ),
        composite_fragility_count=_reason_count(
            scored_rows,
            (COMPOSITE_WATCH_REASON, COMPOSITE_BLOCK_REASON),
        ),
        average_aggregate_depth_fragility_score=_average_score(
            row.aggregate_depth_fragility_score for row in scored_rows
        ),
        average_spread_instability_score=_average_score(
            row.spread_instability_score for row in scored_rows
        ),
        average_cost_pressure_score=_average_score(row.cost_pressure_score for row in scored_rows),
        average_settlement_friction_score=_average_score(
            row.settlement_friction_score for row in scored_rows
        ),
        average_composite_fragility_score=_average_score(
            row.composite_fragility_score for row in scored_rows
        ),
        rows=scored_rows,
        reason_code_counts=_reason_code_counts(scored_rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_market_depth_fragility_report_payload(
    report: ResearchMarketDepthFragilityReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchMarketDepthFragilityReport:
        _require_hard_flags("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchMarketDepthFragilityReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("payload", payload)
    _require_hard_flags("payload", _DictFlags(payload))
    return payload


def research_market_depth_fragility_report_digest(
    report: ResearchMarketDepthFragilityReport | dict[str, Any],
) -> str:
    payload = research_market_depth_fragility_report_payload(report)
    encoded = dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
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


def _normalize_input_rows(rows: Iterable[object]) -> tuple[object, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    seen: set[str] = set()
    for row in normalized:
        if type(row) not in (ResearchMarketDepthFragilityInput, ResearchMarketDepthFragilityRow):
            raise ValueError(
                "rows must contain ResearchMarketDepthFragilityInput or "
                "ResearchMarketDepthFragilityRow",
            )
        _require_hard_flags("row", row)
        if row.market_slug in seen:
            raise ValueError("duplicate market_slug values are not allowed")
        seen.add(row.market_slug)
    return normalized


def _row_from_input(
    row: object,
    *,
    config: ResearchMarketDepthFragilityConfig,
) -> ResearchMarketDepthFragilityRow:
    if type(row) is ResearchMarketDepthFragilityRow:
        _validate_row(row, config=config)
        return row
    if type(row) is not ResearchMarketDepthFragilityInput:
        raise ValueError("row must be a supported market depth fragility row")
    composite_score = _composite_fragility_score(row, config=config)
    status = _row_status(row, composite_score, config=config)
    return ResearchMarketDepthFragilityRow(
        market_slug=row.market_slug,
        public_event_label=row.public_event_label,
        observed_at=row.observed_at,
        aggregate_depth_fragility_score=row.aggregate_depth_fragility_score,
        spread_instability_score=row.spread_instability_score,
        cost_pressure_score=row.cost_pressure_score,
        settlement_friction_score=row.settlement_friction_score,
        composite_fragility_score=composite_score,
        status=status,
        reason_codes=_row_reason_codes(
            row,
            composite_score,
            status=status,
            config=config,
            input_reason_codes=row.reason_codes,
        ),
        validation_config=config,
    )


def _row_status(
    row: ResearchMarketDepthFragilityInput | ResearchMarketDepthFragilityRow,
    composite_score: Decimal,
    *,
    config: ResearchMarketDepthFragilityConfig,
) -> str:
    if (
        row.aggregate_depth_fragility_score >= config.component_block_score
        or row.spread_instability_score >= config.component_block_score
        or row.cost_pressure_score >= config.component_block_score
        or row.settlement_friction_score >= config.component_block_score
        or composite_score >= config.composite_block_score
    ):
        return "block"
    if (
        row.aggregate_depth_fragility_score >= config.component_watch_score
        or row.spread_instability_score >= config.component_watch_score
        or row.cost_pressure_score >= config.component_watch_score
        or row.settlement_friction_score >= config.component_watch_score
        or composite_score >= config.composite_watch_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    row: ResearchMarketDepthFragilityInput | ResearchMarketDepthFragilityRow,
    composite_score: Decimal,
    *,
    status: str,
    config: ResearchMarketDepthFragilityConfig,
    input_reason_codes: tuple[str, ...] = (),
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    _append_component_reason(
        reason_codes,
        row.aggregate_depth_fragility_score,
        watch_reason=AGGREGATE_DEPTH_WATCH_REASON,
        block_reason=AGGREGATE_DEPTH_BLOCK_REASON,
        config=config,
    )
    _append_component_reason(
        reason_codes,
        row.spread_instability_score,
        watch_reason=SPREAD_WATCH_REASON,
        block_reason=SPREAD_BLOCK_REASON,
        config=config,
    )
    _append_component_reason(
        reason_codes,
        row.cost_pressure_score,
        watch_reason=COST_WATCH_REASON,
        block_reason=COST_BLOCK_REASON,
        config=config,
    )
    _append_component_reason(
        reason_codes,
        row.settlement_friction_score,
        watch_reason=SETTLEMENT_WATCH_REASON,
        block_reason=SETTLEMENT_BLOCK_REASON,
        config=config,
    )
    if composite_score >= config.composite_block_score:
        reason_codes.append(COMPOSITE_BLOCK_REASON)
    elif composite_score >= config.composite_watch_score:
        reason_codes.append(COMPOSITE_WATCH_REASON)
    for reason_code in input_reason_codes:
        reason_codes.append(f"input_{reason_code}")
    if status == "pass" and not reason_codes:
        reason_codes.append(PASS_REASON)
    return tuple(sorted(reason_codes))


def _append_component_reason(
    reason_codes: list[str],
    value: Decimal,
    *,
    watch_reason: str,
    block_reason: str,
    config: ResearchMarketDepthFragilityConfig,
) -> None:
    if value >= config.component_block_score:
        reason_codes.append(block_reason)
    elif value >= config.component_watch_score:
        reason_codes.append(watch_reason)


def _composite_fragility_score(
    row: ResearchMarketDepthFragilityInput | ResearchMarketDepthFragilityRow,
    *,
    config: ResearchMarketDepthFragilityConfig,
) -> Decimal:
    return _quantize(
        row.aggregate_depth_fragility_score * config.depth_weight
        + row.spread_instability_score * config.spread_weight
        + row.cost_pressure_score * config.cost_weight
        + row.settlement_friction_score * config.settlement_weight,
    )


def _sort_rows(
    rows: tuple[ResearchMarketDepthFragilityRow, ...],
) -> tuple[ResearchMarketDepthFragilityRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                STATUS_RANK[row.status],
                -row.composite_fragility_score,
                -row.aggregate_depth_fragility_score,
                -row.spread_instability_score,
                -row.cost_pressure_score,
                -row.settlement_friction_score,
                row.market_slug,
            ),
        ),
    )


def _normalize_report_rows(
    value: object,
) -> tuple[ResearchMarketDepthFragilityRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchMarketDepthFragilityRow:
            raise ValueError("rows must contain ResearchMarketDepthFragilityRow")
        _require_hard_flags("row", row)
        if row.market_slug in seen:
            raise ValueError("rows must be unique by market_slug")
        seen.add(row.market_slug)
    if rows != _sort_rows(rows):
        raise ValueError("rows must be sorted deterministically")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchMarketDepthFragilityReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchMarketDepthFragilityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchMarketDepthFragilityReasonCodeCount",
            )
        _require_hard_flags("reason code count", row)
    if rows != tuple(sorted(rows, key=lambda row: row.reason_code)):
        raise ValueError("reason_code_counts must be sorted deterministically")
    return rows


def _report_reason_codes(
    rows: tuple[ResearchMarketDepthFragilityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUT_REASON,)
    present = {
        ROW_TO_REPORT_REASON[reason_code]
        for row in rows
        for reason_code in row.reason_codes
        if reason_code in ROW_TO_REPORT_REASON
    }
    reason_codes = tuple(
        reason_code for reason_code in REPORT_REASON_CODES if reason_code in present
    )
    if reason_codes:
        return reason_codes
    return (PASS_REASON,)


def _report_status(rows: tuple[ResearchMarketDepthFragilityRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _status_count(rows: tuple[ResearchMarketDepthFragilityRow, ...], status: str) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchMarketDepthFragilityRow, ...],
    reason_codes: tuple[str, ...],
) -> Decimal:
    return _count(
        sum(1 for row in rows if any(reason_code in row.reason_codes for reason_code in reason_codes)),
    )


def _reason_code_counts(
    rows: tuple[ResearchMarketDepthFragilityRow, ...],
    report_reason_codes: tuple[str, ...],
) -> tuple[ResearchMarketDepthFragilityReasonCodeCount, ...]:
    counts: dict[str, int] = {}
    for reason_code in report_reason_codes:
        counts[reason_code] = counts.get(reason_code, 0) + 1
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        ResearchMarketDepthFragilityReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(counts.items())
    )


def _validate_row(
    row: ResearchMarketDepthFragilityRow,
    *,
    config: ResearchMarketDepthFragilityConfig,
) -> None:
    expected_composite_score = _composite_fragility_score(row, config=config)
    if row.composite_fragility_score != expected_composite_score:
        raise ValueError("composite_fragility_score must match component scores")
    expected_status = _row_status(row, expected_composite_score, config=config)
    if row.status != expected_status:
        raise ValueError("status must match market depth fragility scores")
    expected_reason_codes = _row_reason_codes(
        row,
        expected_composite_score,
        status=expected_status,
        config=config,
        input_reason_codes=tuple(
            reason_code.removeprefix("input_")
            for reason_code in row.reason_codes
            if reason_code.startswith("input_")
        ),
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match market depth fragility scores")


def _validate_report(report: ResearchMarketDepthFragilityReport) -> None:
    rows = report.rows
    if report.status != _report_status(rows):
        raise ValueError("status must match report rows")
    if report.market_count != _count(len(rows)):
        raise ValueError("market_count must match rows")
    expected_counts = {
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "manual_review_count": _count(sum(1 for row in rows if row.status != "pass")),
        "aggregate_depth_fragility_count": _reason_count(
            rows,
            (AGGREGATE_DEPTH_WATCH_REASON, AGGREGATE_DEPTH_BLOCK_REASON),
        ),
        "spread_instability_count": _reason_count(
            rows,
            (SPREAD_WATCH_REASON, SPREAD_BLOCK_REASON),
        ),
        "cost_pressure_count": _reason_count(rows, (COST_WATCH_REASON, COST_BLOCK_REASON)),
        "settlement_friction_count": _reason_count(
            rows,
            (SETTLEMENT_WATCH_REASON, SETTLEMENT_BLOCK_REASON),
        ),
        "composite_fragility_count": _reason_count(
            rows,
            (COMPOSITE_WATCH_REASON, COMPOSITE_BLOCK_REASON),
        ),
    }
    for field_name, expected_value in expected_counts.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    expected_averages = {
        "average_aggregate_depth_fragility_score": _average_score(
            row.aggregate_depth_fragility_score for row in rows
        ),
        "average_spread_instability_score": _average_score(
            row.spread_instability_score for row in rows
        ),
        "average_cost_pressure_score": _average_score(row.cost_pressure_score for row in rows),
        "average_settlement_friction_score": _average_score(
            row.settlement_friction_score for row in rows
        ),
        "average_composite_fragility_score": _average_score(
            row.composite_fragility_score for row in rows
        ),
    }
    for field_name, expected_value in expected_averages.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match report rows")
    if report.reason_code_counts != _reason_code_counts(rows, report.reason_codes):
        raise ValueError("reason_code_counts must match report rows")


def _average_score(values: Iterable[Decimal]) -> Decimal | None:
    normalized = tuple(values)
    if not normalized:
        return None
    return _quantize(sum(normalized, ZERO) / _count(len(normalized)))


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    try:
        return value.quantize(QUANT, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("value must be a finite Decimal") from exc


def _require_score_decimal(name: str, value: object) -> Decimal:
    normalized = _require_decimal(name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{name} must be between 0.000000 and 1.000000")
    return normalized


def _require_optional_score_decimal(name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_score_decimal(name, value)


def _require_nonnegative_decimal(name: str, value: object) -> Decimal:
    normalized = _require_decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _quantize(value)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_status(name: str, value: object) -> None:
    if type(value) is not str or value not in MARKET_DEPTH_FRAGILITY_STATUSES:
        raise ValueError(f"{name} must be one of pass, watch, block")


def _require_public_string(name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{name} must not contain leading or trailing whitespace")
    lowered = value.lower()
    if lowered.startswith("0x") and len(lowered) >= 42:
        raise ValueError(f"{name} must not expose raw references")
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{name} contains unsafe public text")
    return value


def _require_reason_code(name: str, value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{name} must be a non-empty string")
    if value != value.lower():
        raise ValueError(f"{name} must be lowercase")
    if not value.replace("_", "").isalnum():
        raise ValueError(f"{name} must use lowercase letters, digits, or underscores")
    if any(fragment in value for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{name} contains unsafe public text")
    return value


def _normalize_reason_codes(
    name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{name} must be a list or tuple")
    normalized = tuple(_require_reason_code(name, item) for item in value)
    if not allow_empty and not normalized:
        raise ValueError(f"{name} must not be empty")
    return tuple(sorted(set(normalized)))


def _normalize_report_reason_codes(name: str, value: object) -> tuple[str, ...]:
    normalized = _normalize_reason_codes(name, value, allow_empty=False)
    unknown = tuple(reason_code for reason_code in normalized if reason_code not in REPORT_REASON_CODES)
    if unknown:
        raise ValueError(f"{name} contains unsupported report reason codes")
    return tuple(reason_code for reason_code in REPORT_REASON_CODES if reason_code in normalized)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in HARD_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _json_ready(value: object) -> Any:
    if is_dataclass(value):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is dict:
        return {str(key): _json_ready(child) for key, child in value.items()}
    if type(value) in (list, tuple):
        return [_json_ready(child) for child in value]
    if type(value) is Decimal:
        return format(_quantize(value), ".6f")
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    if isinstance(value, float):
        raise ValueError("payload must not contain floats")
    return value


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is dict:
        for key, child in value.items():
            _require_public_payload_text(label, str(key))
            _reject_unsafe_public_payload(label, child)
    elif type(value) is list:
        for child in value:
            _reject_unsafe_public_payload(label, child)
    elif type(value) is str:
        _require_public_payload_text(label, value)
    elif isinstance(value, float):
        raise ValueError(f"{label} contains unsafe float")


def _require_public_payload_text(label: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{label} contains unsafe public text")


__all__ = (
    "DEFAULT_RESEARCH_MARKET_DEPTH_FRAGILITY_REPORT_CONFIG_VERSION",
    "MARKET_DEPTH_FRAGILITY_STATUSES",
    "ResearchMarketDepthFragilityConfig",
    "ResearchMarketDepthFragilityInput",
    "ResearchMarketDepthFragilityReasonCodeCount",
    "ResearchMarketDepthFragilityReport",
    "ResearchMarketDepthFragilityRow",
    "build_research_market_depth_fragility_report",
    "research_market_depth_fragility_report_digest",
    "research_market_depth_fragility_report_payload",
)
