"""Pure in-memory cost drag sensitivity report for research rows."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import blake2b
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_STRATEGY_COST_DRAG_SENSITIVITY_CONFIG_VERSION = (
    "research-strategy-cost-drag-sensitivity-report-v0"
)

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"
STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCK_STATUS)

TOTAL_COST_DRAG_BLOCK_REASON = "total_cost_drag_block"
TOTAL_COST_DRAG_WATCH_REASON = "total_cost_drag_watch"
COST_TO_EDGE_BLOCK_REASON = "cost_to_edge_block"
COST_TO_EDGE_WATCH_REASON = "cost_to_edge_watch"
SETTLEMENT_WAIT_BLOCK_REASON = "settlement_wait_block"
SETTLEMENT_WAIT_WATCH_REASON = "settlement_wait_watch"
NET_EDGE_DEPLETED_BLOCK_REASON = "net_edge_depleted_block"
PASSED_REASON = "cost_drag_sensitivity_passed"
CLEAR_REPORT_REASON = "cost_drag_sensitivity_clear"
WATCH_REPORT_REASON = "cost_drag_sensitivity_watch_present"

BLOCK_REASONS = (
    TOTAL_COST_DRAG_BLOCK_REASON,
    COST_TO_EDGE_BLOCK_REASON,
    SETTLEMENT_WAIT_BLOCK_REASON,
    NET_EDGE_DEPLETED_BLOCK_REASON,
)
RISK_REASON_SEQUENCE = (
    TOTAL_COST_DRAG_BLOCK_REASON,
    COST_TO_EDGE_BLOCK_REASON,
    SETTLEMENT_WAIT_BLOCK_REASON,
    NET_EDGE_DEPLETED_BLOCK_REASON,
    TOTAL_COST_DRAG_WATCH_REASON,
    COST_TO_EDGE_WATCH_REASON,
    SETTLEMENT_WAIT_WATCH_REASON,
)
ROW_REASON_CODES = (*RISK_REASON_SEQUENCE, PASSED_REASON)
REPORT_REASON_BY_ROW_REASON = {
    TOTAL_COST_DRAG_BLOCK_REASON: "total_cost_drag_block_present",
    COST_TO_EDGE_BLOCK_REASON: "cost_to_edge_block_present",
    SETTLEMENT_WAIT_BLOCK_REASON: "settlement_wait_block_present",
    NET_EDGE_DEPLETED_BLOCK_REASON: "net_edge_depleted_block_present",
    TOTAL_COST_DRAG_WATCH_REASON: "total_cost_drag_watch_present",
    COST_TO_EDGE_WATCH_REASON: "cost_to_edge_watch_present",
    SETTLEMENT_WAIT_WATCH_REASON: "settlement_wait_watch_present",
}
REPORT_REASON_CODES = (
    CLEAR_REPORT_REASON,
    *tuple(REPORT_REASON_BY_ROW_REASON[reason] for reason in RISK_REASON_SEQUENCE),
    WATCH_REPORT_REASON,
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MAX_COST_TO_EDGE_RATIO = Decimal("999999.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

UNSAFE_PUBLIC_FIELD_FRAGMENTS = (
    "candidate",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "source_ref",
    "source_url",
    "source_text",
    "url",
    "dsn",
    "table",
    "token",
    "wal" + "let",
    "au" + "th",
    "or" + "der",
    "tra" + "de",
    "po" + "sition",
    "b" + "uy",
    "s" + "ell",
    "recom" + "mend",
    "li" + "ve",
)


@dataclass(frozen=True)
class ResearchStrategyCostDragSensitivityConfig:
    config_version: str = DEFAULT_RESEARCH_STRATEGY_COST_DRAG_SENSITIVITY_CONFIG_VERSION
    watch_total_cost_drag_ratio: Decimal = Decimal("0.020000")
    block_total_cost_drag_ratio: Decimal = Decimal("0.050000")
    watch_cost_to_edge_ratio: Decimal = Decimal("0.500000")
    block_cost_to_edge_ratio: Decimal = Decimal("1.000000")
    watch_settlement_wait_days: Decimal = Decimal("3.000000")
    block_settlement_wait_days: Decimal = Decimal("7.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_plain_canonical_string("config_version", self.config_version)
        for field_name in (
            "watch_total_cost_drag_ratio",
            "block_total_cost_drag_ratio",
            "watch_cost_to_edge_ratio",
            "block_cost_to_edge_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("watch_settlement_wait_days", "block_settlement_wait_days"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyCostDragSensitivityInput:
    research_reference: str
    evaluated_at: datetime
    gross_edge_ratio: Decimal
    fee_ratio: Decimal
    spread_ratio: Decimal
    slippage_ratio: Decimal
    settlement_wait_days: Decimal
    daily_wait_cost_ratio: Decimal
    upstream_reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_plain_canonical_string("research_reference", self.research_reference)
        object.__setattr__(self, "evaluated_at", _as_utc("evaluated_at", self.evaluated_at))
        for field_name in (
            "gross_edge_ratio",
            "fee_ratio",
            "spread_ratio",
            "slippage_ratio",
            "settlement_wait_days",
            "daily_wait_cost_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_upstream_reason_codes(self.upstream_reason_codes),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyCostDragSensitivityRow:
    public_rank: Decimal
    public_research_reference: str
    evaluated_at: datetime
    gross_edge_ratio: Decimal
    fee_ratio: Decimal
    spread_ratio: Decimal
    slippage_ratio: Decimal
    settlement_wait_days: Decimal
    daily_wait_cost_ratio: Decimal
    settlement_wait_drag_ratio: Decimal
    total_cost_drag_ratio: Decimal
    net_edge_ratio: Decimal
    cost_to_edge_ratio: Decimal
    risk_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "public_rank",
            _normalize_positive_decimal("public_rank", self.public_rank),
        )
        _require_plain_canonical_string(
            "public_research_reference",
            self.public_research_reference,
        )
        object.__setattr__(self, "evaluated_at", _as_utc("evaluated_at", self.evaluated_at))
        for field_name in (
            "gross_edge_ratio",
            "fee_ratio",
            "spread_ratio",
            "slippage_ratio",
            "settlement_wait_days",
            "daily_wait_cost_ratio",
            "settlement_wait_drag_ratio",
            "total_cost_drag_ratio",
            "cost_to_edge_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "net_edge_ratio",
            _normalize_decimal("net_edge_ratio", self.net_edge_ratio),
        )
        _require_member("risk_status", self.risk_status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchStrategyCostDragSensitivityDigest:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_total_cost_drag_ratio: Decimal
    max_cost_to_edge_ratio: Decimal
    min_net_edge_ratio: Decimal
    max_settlement_wait_days: Decimal
    risk_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_plain_canonical_string("config_version", self.config_version)
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_total_cost_drag_ratio",
            "max_cost_to_edge_ratio",
            "max_settlement_wait_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_net_edge_ratio",
            _normalize_decimal("min_net_edge_ratio", self.min_net_edge_ratio),
        )
        _require_member("risk_status", self.risk_status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _require_hard_flags("digest", self)


@dataclass(frozen=True)
class ResearchStrategyCostDragSensitivityReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_total_cost_drag_ratio: Decimal
    max_cost_to_edge_ratio: Decimal
    min_net_edge_ratio: Decimal
    max_settlement_wait_days: Decimal
    risk_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchStrategyCostDragSensitivityRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_plain_canonical_string("config_version", self.config_version)
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_total_cost_drag_ratio",
            "max_cost_to_edge_ratio",
            "max_settlement_wait_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_net_edge_ratio",
            _normalize_decimal("min_net_edge_ratio", self.min_net_edge_ratio),
        )
        _require_member("risk_status", self.risk_status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)


def build_research_strategy_cost_drag_sensitivity_report(
    rows: object,
    *,
    config: ResearchStrategyCostDragSensitivityConfig,
    generated_at: datetime,
) -> ResearchStrategyCostDragSensitivityReport:
    if type(config) is not ResearchStrategyCostDragSensitivityConfig:
        raise ValueError("config must be a ResearchStrategyCostDragSensitivityConfig")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(rows, generated_at)
    row_drafts = tuple(
        _row_draft(input_row, config=config) for input_row in inputs
    )
    report_rows = tuple(
        _row_from_draft(rank, draft)
        for rank, draft in enumerate(sorted(row_drafts, key=_draft_sort_key), start=1)
    )

    return ResearchStrategyCostDragSensitivityReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=_count(len(inputs)),
        row_count=_count(len(report_rows)),
        pass_count=_status_count(report_rows, PASS_STATUS),
        watch_count=_status_count(report_rows, WATCH_STATUS),
        block_count=_status_count(report_rows, BLOCK_STATUS),
        max_total_cost_drag_ratio=_max_nonnegative(
            row.total_cost_drag_ratio for row in report_rows
        ),
        max_cost_to_edge_ratio=_max_nonnegative(
            row.cost_to_edge_ratio for row in report_rows
        ),
        min_net_edge_ratio=_min_decimal(row.net_edge_ratio for row in report_rows),
        max_settlement_wait_days=_max_nonnegative(
            row.settlement_wait_days for row in report_rows
        ),
        risk_status=_report_status(report_rows),
        reason_codes=_report_reason_codes(report_rows),
        rows=report_rows,
    )


def build_research_strategy_cost_drag_sensitivity_digest(
    report: ResearchStrategyCostDragSensitivityReport,
) -> ResearchStrategyCostDragSensitivityDigest:
    if type(report) is not ResearchStrategyCostDragSensitivityReport:
        raise ValueError("report must be a ResearchStrategyCostDragSensitivityReport")
    _require_report_surface_flags(report)
    return ResearchStrategyCostDragSensitivityDigest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        input_count=report.input_count,
        row_count=report.row_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        max_total_cost_drag_ratio=report.max_total_cost_drag_ratio,
        max_cost_to_edge_ratio=report.max_cost_to_edge_ratio,
        min_net_edge_ratio=report.min_net_edge_ratio,
        max_settlement_wait_days=report.max_settlement_wait_days,
        risk_status=report.risk_status,
        reason_codes=report.reason_codes,
    )


def research_strategy_cost_drag_sensitivity_report_to_jsonable(
    report: ResearchStrategyCostDragSensitivityReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyCostDragSensitivityReport:
        raise ValueError("report must be a ResearchStrategyCostDragSensitivityReport")
    _require_report_surface_flags(report)
    return _guarded_json_payload(
        "research strategy cost drag sensitivity report",
        asdict(report),
    )


def research_strategy_cost_drag_sensitivity_report_to_json(
    report: ResearchStrategyCostDragSensitivityReport,
) -> dict[str, Any]:
    return research_strategy_cost_drag_sensitivity_report_to_jsonable(report)


def research_strategy_cost_drag_sensitivity_digest_to_jsonable(
    digest: ResearchStrategyCostDragSensitivityDigest,
) -> dict[str, Any]:
    if type(digest) is not ResearchStrategyCostDragSensitivityDigest:
        raise ValueError("digest must be a ResearchStrategyCostDragSensitivityDigest")
    require_paper_only_flags("ResearchStrategyCostDragSensitivityDigest", digest)
    return _guarded_json_payload(
        "research strategy cost drag sensitivity digest",
        asdict(digest),
    )


def research_strategy_cost_drag_sensitivity_digest_to_json(
    digest: ResearchStrategyCostDragSensitivityDigest,
) -> dict[str, Any]:
    return research_strategy_cost_drag_sensitivity_digest_to_jsonable(digest)


def research_strategy_cost_drag_sensitivity_report_digest_to_jsonable(
    report: ResearchStrategyCostDragSensitivityReport,
) -> dict[str, Any]:
    return research_strategy_cost_drag_sensitivity_digest_to_jsonable(
        build_research_strategy_cost_drag_sensitivity_digest(report),
    )


def _row_draft(
    input_row: ResearchStrategyCostDragSensitivityInput,
    *,
    config: ResearchStrategyCostDragSensitivityConfig,
) -> tuple[
    ResearchStrategyCostDragSensitivityInput,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    str,
    tuple[str, ...],
]:
    settlement_wait_drag_ratio = _multiply_decimal(
        input_row.settlement_wait_days,
        input_row.daily_wait_cost_ratio,
    )
    total_cost_drag_ratio = _add_decimal(
        input_row.fee_ratio,
        input_row.spread_ratio,
        input_row.slippage_ratio,
        settlement_wait_drag_ratio,
    )
    net_edge_ratio = _subtract_decimal(input_row.gross_edge_ratio, total_cost_drag_ratio)
    cost_to_edge_ratio = _cost_to_edge_ratio(
        total_cost_drag_ratio,
        input_row.gross_edge_ratio,
    )
    risk_reasons = _risk_reason_codes(
        total_cost_drag_ratio=total_cost_drag_ratio,
        cost_to_edge_ratio=cost_to_edge_ratio,
        settlement_wait_days=input_row.settlement_wait_days,
        net_edge_ratio=net_edge_ratio,
        config=config,
    )
    status = _row_status(risk_reasons)
    reason_codes = _row_reason_codes(input_row.upstream_reason_codes, risk_reasons)
    return (
        input_row,
        settlement_wait_drag_ratio,
        total_cost_drag_ratio,
        net_edge_ratio,
        cost_to_edge_ratio,
        status,
        reason_codes,
    )


def _row_from_draft(
    rank: int,
    draft: tuple[
        ResearchStrategyCostDragSensitivityInput,
        Decimal,
        Decimal,
        Decimal,
        Decimal,
        str,
        tuple[str, ...],
    ],
) -> ResearchStrategyCostDragSensitivityRow:
    (
        input_row,
        settlement_wait_drag_ratio,
        total_cost_drag_ratio,
        net_edge_ratio,
        cost_to_edge_ratio,
        status,
        reason_codes,
    ) = draft
    return ResearchStrategyCostDragSensitivityRow(
        public_rank=_count(rank),
        public_research_reference=_public_research_reference(rank),
        evaluated_at=input_row.evaluated_at,
        gross_edge_ratio=input_row.gross_edge_ratio,
        fee_ratio=input_row.fee_ratio,
        spread_ratio=input_row.spread_ratio,
        slippage_ratio=input_row.slippage_ratio,
        settlement_wait_days=input_row.settlement_wait_days,
        daily_wait_cost_ratio=input_row.daily_wait_cost_ratio,
        settlement_wait_drag_ratio=settlement_wait_drag_ratio,
        total_cost_drag_ratio=total_cost_drag_ratio,
        net_edge_ratio=net_edge_ratio,
        cost_to_edge_ratio=cost_to_edge_ratio,
        risk_status=status,
        reason_codes=reason_codes,
    )


def _draft_sort_key(
    draft: tuple[
        ResearchStrategyCostDragSensitivityInput,
        Decimal,
        Decimal,
        Decimal,
        Decimal,
        str,
        tuple[str, ...],
    ],
) -> tuple[int, Decimal, Decimal, Decimal, Decimal, datetime, str]:
    (
        input_row,
        _settlement_wait_drag_ratio,
        total_cost_drag_ratio,
        net_edge_ratio,
        cost_to_edge_ratio,
        status,
        _reason_codes,
    ) = draft
    return (
        _status_sort_value(status),
        -cost_to_edge_ratio,
        -total_cost_drag_ratio,
        net_edge_ratio,
        -input_row.settlement_wait_days,
        input_row.evaluated_at,
        _reference_digest(input_row.research_reference),
    )


def _row_sort_key(
    row: ResearchStrategyCostDragSensitivityRow,
) -> tuple[int, Decimal, Decimal, Decimal, Decimal, datetime, str]:
    return (
        _status_sort_value(row.risk_status),
        -row.cost_to_edge_ratio,
        -row.total_cost_drag_ratio,
        row.net_edge_ratio,
        -row.settlement_wait_days,
        row.evaluated_at,
        row.public_research_reference,
    )


def _risk_reason_codes(
    *,
    total_cost_drag_ratio: Decimal,
    cost_to_edge_ratio: Decimal,
    settlement_wait_days: Decimal,
    net_edge_ratio: Decimal,
    config: ResearchStrategyCostDragSensitivityConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if total_cost_drag_ratio >= config.block_total_cost_drag_ratio:
        reason_codes.append(TOTAL_COST_DRAG_BLOCK_REASON)
    elif total_cost_drag_ratio >= config.watch_total_cost_drag_ratio:
        reason_codes.append(TOTAL_COST_DRAG_WATCH_REASON)

    if cost_to_edge_ratio >= config.block_cost_to_edge_ratio:
        reason_codes.append(COST_TO_EDGE_BLOCK_REASON)
    elif cost_to_edge_ratio >= config.watch_cost_to_edge_ratio:
        reason_codes.append(COST_TO_EDGE_WATCH_REASON)

    if settlement_wait_days >= config.block_settlement_wait_days:
        reason_codes.append(SETTLEMENT_WAIT_BLOCK_REASON)
    elif settlement_wait_days >= config.watch_settlement_wait_days:
        reason_codes.append(SETTLEMENT_WAIT_WATCH_REASON)

    if net_edge_ratio <= ZERO:
        reason_codes.append(NET_EDGE_DEPLETED_BLOCK_REASON)

    return _canonical_risk_reasons(tuple(reason_codes))


def _row_reason_codes(
    upstream_reason_codes: tuple[str, ...],
    risk_reasons: tuple[str, ...],
) -> tuple[str, ...]:
    if not risk_reasons:
        return (PASSED_REASON,)
    return (*upstream_reason_codes, *risk_reasons)


def _row_status(risk_reasons: tuple[str, ...]) -> str:
    if any(reason in BLOCK_REASONS for reason in risk_reasons):
        return BLOCK_STATUS
    if risk_reasons:
        return WATCH_STATUS
    return PASS_STATUS


def _report_status(
    rows: tuple[ResearchStrategyCostDragSensitivityRow, ...],
) -> str:
    if any(row.risk_status == BLOCK_STATUS for row in rows):
        return BLOCK_STATUS
    if any(row.risk_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    rows: tuple[ResearchStrategyCostDragSensitivityRow, ...],
) -> tuple[str, ...]:
    if not rows or all(row.risk_status == PASS_STATUS for row in rows):
        return (CLEAR_REPORT_REASON,)
    row_reason_codes = {
        reason for row in rows for reason in row.reason_codes if reason in RISK_REASON_SEQUENCE
    }
    reason_codes = [
        REPORT_REASON_BY_ROW_REASON[reason]
        for reason in RISK_REASON_SEQUENCE
        if reason in row_reason_codes
    ]
    if any(row.risk_status == WATCH_STATUS for row in rows):
        reason_codes.append(WATCH_REPORT_REASON)
    return tuple(reason_codes)


def _normalize_inputs(
    value: object,
    generated_at: datetime,
) -> tuple[ResearchStrategyCostDragSensitivityInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for input_row in rows:
        if type(input_row) is not ResearchStrategyCostDragSensitivityInput:
            raise ValueError(
                "rows must contain ResearchStrategyCostDragSensitivityInput values",
            )
        _require_hard_flags("input", input_row)
        if input_row.evaluated_at > generated_at:
            raise ValueError("evaluated_at must not be after generated_at")
        if input_row.research_reference in seen:
            raise ValueError("duplicate research_reference")
        seen.add(input_row.research_reference)
    return rows


def _normalize_rows(
    value: object,
) -> tuple[ResearchStrategyCostDragSensitivityRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(value)
    for index, row in enumerate(rows, start=1):
        if type(row) is not ResearchStrategyCostDragSensitivityRow:
            raise ValueError("rows must contain ResearchStrategyCostDragSensitivityRow")
        _require_hard_flags("row", row)
        if row.public_rank != _count(index):
            raise ValueError("public_rank must match row sequence")
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sorting")
    return rows


def _validate_config(config: ResearchStrategyCostDragSensitivityConfig) -> None:
    if config.block_total_cost_drag_ratio < config.watch_total_cost_drag_ratio:
        raise ValueError("block_total_cost_drag_ratio must be at least watch threshold")
    if config.block_cost_to_edge_ratio < config.watch_cost_to_edge_ratio:
        raise ValueError("block_cost_to_edge_ratio must be at least watch threshold")
    if config.block_settlement_wait_days < config.watch_settlement_wait_days:
        raise ValueError("block_settlement_wait_days must be at least watch threshold")


def _validate_row(row: ResearchStrategyCostDragSensitivityRow) -> None:
    if row.settlement_wait_drag_ratio != _multiply_decimal(
        row.settlement_wait_days,
        row.daily_wait_cost_ratio,
    ):
        raise ValueError("settlement_wait_drag_ratio must match wait inputs")
    if row.total_cost_drag_ratio != _add_decimal(
        row.fee_ratio,
        row.spread_ratio,
        row.slippage_ratio,
        row.settlement_wait_drag_ratio,
    ):
        raise ValueError("total_cost_drag_ratio must match cost inputs")
    if row.net_edge_ratio != _subtract_decimal(
        row.gross_edge_ratio,
        row.total_cost_drag_ratio,
    ):
        raise ValueError("net_edge_ratio must match edge and cost inputs")
    if row.cost_to_edge_ratio != _cost_to_edge_ratio(
        row.total_cost_drag_ratio,
        row.gross_edge_ratio,
    ):
        raise ValueError("cost_to_edge_ratio must match edge and cost inputs")
    risk_reasons = tuple(
        reason for reason in row.reason_codes if reason in RISK_REASON_SEQUENCE
    )
    if row.risk_status != _row_status(risk_reasons):
        raise ValueError("risk_status must match reason_codes")
    if row.risk_status == PASS_STATUS and row.reason_codes != (PASSED_REASON,):
        raise ValueError("pass rows must use passed reason")
    if row.risk_status != PASS_STATUS and not risk_reasons:
        raise ValueError("risk rows must include risk reason_codes")
    if risk_reasons != _canonical_risk_reasons(risk_reasons):
        raise ValueError("risk reason_codes must use canonical sequence")


def _validate_report(report: ResearchStrategyCostDragSensitivityReport) -> None:
    if report.row_count != _count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match rows")
    if report.pass_count != _status_count(report.rows, PASS_STATUS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, WATCH_STATUS):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, BLOCK_STATUS):
        raise ValueError("block_count must match rows")
    if report.max_total_cost_drag_ratio != _max_nonnegative(
        row.total_cost_drag_ratio for row in report.rows
    ):
        raise ValueError("max_total_cost_drag_ratio must match rows")
    if report.max_cost_to_edge_ratio != _max_nonnegative(
        row.cost_to_edge_ratio for row in report.rows
    ):
        raise ValueError("max_cost_to_edge_ratio must match rows")
    if report.min_net_edge_ratio != _min_decimal(row.net_edge_ratio for row in report.rows):
        raise ValueError("min_net_edge_ratio must match rows")
    if report.max_settlement_wait_days != _max_nonnegative(
        row.settlement_wait_days for row in report.rows
    ):
        raise ValueError("max_settlement_wait_days must match rows")
    if report.risk_status != _report_status(report.rows):
        raise ValueError("risk_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _require_report_surface_flags(
    report: ResearchStrategyCostDragSensitivityReport,
) -> None:
    require_paper_only_flags("ResearchStrategyCostDragSensitivityReport", report)
    for row in report.rows:
        require_paper_only_flags("ResearchStrategyCostDragSensitivityRow", row)


def _guarded_json_payload(label: str, payload: object) -> dict[str, Any]:
    _reject_unsafe_public_surface_fields(label, payload)
    _reject_unsafe_public_surface_values(label, payload)
    ready = json_ready_no_floats(payload)
    if type(ready) is not dict:
        raise ValueError("payload must be a JSON object")
    _reject_unsafe_public_surface_fields(label, ready)
    _reject_unsafe_public_surface_values(label, ready)
    return ready


def _reject_unsafe_public_surface_fields(label: str, payload: object) -> None:
    for key in _iter_payload_keys(payload):
        normalized_key = key.lower()
        if any(fragment in normalized_key for fragment in UNSAFE_PUBLIC_FIELD_FRAGMENTS):
            raise ValueError(f"unsafe public surface field in {label}: {key}")


def _reject_unsafe_public_surface_values(label: str, payload: object) -> None:
    for value in _iter_payload_string_values(payload):
        normalized_value = value.lower()
        if any(fragment in normalized_value for fragment in UNSAFE_PUBLIC_FIELD_FRAGMENTS):
            raise ValueError(f"unsafe public surface value in {label}")


def _iter_payload_keys(value: object) -> tuple[str, ...]:
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            keys.append(key)
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    if isinstance(value, list):
        keys = []
        for item in value:
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    return ()


def _iter_payload_string_values(value: object) -> tuple[str, ...]:
    if isinstance(value, dict):
        values: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            values.extend(_iter_payload_string_values(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(_iter_payload_string_values(item))
        return tuple(values)
    if type(value) is str:
        return (value,)
    return ()


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_hard_flags(label: str, value: object) -> None:
    require_paper_only_flags(label, value)


def _require_plain_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a plain str")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be canonical text")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _normalize_upstream_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("upstream_reason_codes must be a tuple")
    reason_codes: list[str] = []
    seen: set[str] = set()
    for reason_code in value:
        _require_plain_canonical_string("upstream_reason_code", reason_code)
        if reason_code in ROW_REASON_CODES:
            raise ValueError("upstream_reason_codes must not reuse local reason codes")
        if reason_code not in seen:
            reason_codes.append(reason_code)
            seen.add(reason_code)
    return tuple(reason_codes)


def _normalize_row_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    reason_codes: list[str] = []
    seen: set[str] = set()
    for reason_code in value:
        _require_plain_canonical_string("reason_code", reason_code)
        if reason_code in seen:
            continue
        reason_codes.append(reason_code)
        seen.add(reason_code)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    return tuple(reason_codes)


def _normalize_report_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    reason_codes: list[str] = []
    seen: set[str] = set()
    for reason_code in value:
        _require_plain_canonical_string("reason_code", reason_code)
        if reason_code not in REPORT_REASON_CODES:
            raise ValueError("reason_codes must be known report reason codes")
        if reason_code not in seen:
            reason_codes.append(reason_code)
            seen.add(reason_code)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    return tuple(reason_codes)


def _canonical_risk_reasons(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(reason for reason in RISK_REASON_SEQUENCE if reason in reason_codes)


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a count Decimal")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent < QUANTUM.as_tuple().exponent:
        raise ValueError(f"{field_name} must not exceed six decimal places")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _add_decimal(*values: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        total = ZERO
        for value in values:
            total += value
        return total.quantize(QUANTUM)


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (left - right).quantize(QUANTUM)


def _multiply_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (left * right).quantize(QUANTUM)


def _cost_to_edge_ratio(total_cost_drag_ratio: Decimal, gross_edge_ratio: Decimal) -> Decimal:
    if gross_edge_ratio == ZERO:
        if total_cost_drag_ratio == ZERO:
            return ZERO
        return MAX_COST_TO_EDGE_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (total_cost_drag_ratio / gross_edge_ratio).quantize(QUANTUM)


def _count(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(QUANTUM)


def _status_count(
    rows: tuple[ResearchStrategyCostDragSensitivityRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.risk_status == status))


def _max_nonnegative(values: object) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    return max(normalized)


def _min_decimal(values: object) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    return min(normalized)


def _status_sort_value(status: str) -> int:
    return {BLOCK_STATUS: 0, WATCH_STATUS: 1, PASS_STATUS: 2}[status]


def _public_research_reference(rank: int) -> str:
    return f"research_ref_{rank:06d}"


def _reference_digest(value: str) -> str:
    return blake2b(value.encode("utf-8"), digest_size=12).hexdigest()


__all__ = (
    "ResearchStrategyCostDragSensitivityConfig",
    "ResearchStrategyCostDragSensitivityDigest",
    "ResearchStrategyCostDragSensitivityInput",
    "ResearchStrategyCostDragSensitivityReport",
    "ResearchStrategyCostDragSensitivityRow",
    "build_research_strategy_cost_drag_sensitivity_digest",
    "build_research_strategy_cost_drag_sensitivity_report",
    "research_strategy_cost_drag_sensitivity_digest_to_json",
    "research_strategy_cost_drag_sensitivity_digest_to_jsonable",
    "research_strategy_cost_drag_sensitivity_report_digest_to_jsonable",
    "research_strategy_cost_drag_sensitivity_report_to_json",
    "research_strategy_cost_drag_sensitivity_report_to_jsonable",
)
