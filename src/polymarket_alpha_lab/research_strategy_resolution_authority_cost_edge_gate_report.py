"""Report-only resolution authority cost-adjusted edge gate."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any, Iterable


DEFAULT_RESEARCH_STRATEGY_RESOLUTION_AUTHORITY_COST_EDGE_GATE_REPORT_CONFIG_VERSION = (
    "research-strategy-resolution-authority-cost-edge-gate-report-v0"
)
RESEARCH_STRATEGY_RESOLUTION_AUTHORITY_COST_EDGE_GATE_STATUSES = (
    "pass",
    "watch",
    "block",
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
DECIMAL_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

ROW_REASON_CODES = (
    "cost_adjusted_edge_block",
    "cost_adjusted_edge_watch",
    "resolution_authority_block",
    "resolution_authority_cost_edge_gate_pass",
    "resolution_authority_watch",
    "total_cost_drag_block",
    "total_cost_drag_watch",
)
REPORT_REASON_CODES = (
    "cost_adjusted_edge_review",
    "resolution_authority_cost_edge_gate_report_block",
    "resolution_authority_cost_edge_gate_report_empty",
    "resolution_authority_cost_edge_gate_report_pass",
    "resolution_authority_cost_edge_gate_report_watch",
    "resolution_authority_review",
    "total_cost_drag_review",
)
_REPORT_REVIEW_ORDER = (
    "cost_adjusted_edge_review",
    "total_cost_drag_review",
    "resolution_authority_review",
)
_UNSAFE_PUBLIC_FRAGMENTS = (
    "api" + "_key",
    "candidate" + "_id",
    "credential",
    "data" + "base",
    "dsn",
    "market" + "_id",
    "market" + "_slug",
    "market" + "_ques" + "tion",
    "private" + "_key",
    "ques" + "tion",
    "secret",
    "slug",
    "source" + "_text",
    "source" + "_url",
    "table",
    "token",
    "wal" + "let",
    "or" + "der",
    "li" + "ve",
    "trad" + "e",
    "trad" + "ing",
    "net" + "work",
    "persist",
    "signing",
    "mutation",
    "b" + "uy",
    "se" + "ll",
    "reco" + "mmendation",
    "siz" + "ing",
)
_REPORT_PUBLIC_PAYLOAD_KEYS = frozenset(
    {
        "config_version",
        "generated_at",
        "source_row_count",
        "pass_count",
        "watch_count",
        "block_count",
        "mean_cost_adjusted_edge_probability",
        "mean_total_cost_drag_probability",
        "mean_resolution_authority_score",
        "status",
        "reason_codes",
        "reason_code_counts",
        "rows",
        "paper_only",
        "report_only",
        "readonly",
        "derived_validation_digest",
    },
)
_REASON_CODE_COUNT_PUBLIC_PAYLOAD_KEYS = frozenset(
    {
        "reason_code",
        "count",
        "input_ratio",
        "paper_only",
        "report_only",
        "readonly",
    },
)
_ROW_PUBLIC_PAYLOAD_KEYS = frozenset(
    {
        "row_number",
        "row_digest",
        "observed_at",
        "raw_forecast_edge_probability",
        "total_cost_drag_probability",
        "cost_adjusted_edge_probability",
        "resolution_authority_score",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    },
)


@dataclass(frozen=True)
class ResearchStrategyResolutionAuthorityCostEdgeGateConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_RESOLUTION_AUTHORITY_COST_EDGE_GATE_REPORT_CONFIG_VERSION
    )
    cost_adjusted_edge_pass_floor: Decimal = Decimal("0.020000")
    cost_adjusted_edge_watch_floor: Decimal = Decimal("0.000000")
    total_cost_drag_pass_ceiling: Decimal = Decimal("0.030000")
    total_cost_drag_watch_ceiling: Decimal = Decimal("0.060000")
    resolution_authority_pass_floor: Decimal = Decimal("0.800000")
    resolution_authority_watch_floor: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyResolutionAuthorityCostEdgeGateConfig:
            raise TypeError(
                "ResearchStrategyResolutionAuthorityCostEdgeGateConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchStrategyResolutionAuthorityCostEdgeGateConfig,
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_RESOLUTION_AUTHORITY_COST_EDGE_GATE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "cost_adjusted_edge_pass_floor",
            "cost_adjusted_edge_watch_floor",
            "total_cost_drag_pass_ceiling",
            "total_cost_drag_watch_ceiling",
            "resolution_authority_pass_floor",
            "resolution_authority_watch_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_floor_pair(
            "cost_adjusted_edge",
            self.cost_adjusted_edge_pass_floor,
            self.cost_adjusted_edge_watch_floor,
        )
        _require_ceiling_pair(
            "total_cost_drag",
            self.total_cost_drag_pass_ceiling,
            self.total_cost_drag_watch_ceiling,
        )
        _require_floor_pair(
            "resolution_authority",
            self.resolution_authority_pass_floor,
            self.resolution_authority_watch_floor,
        )
        _require_report_only_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyResolutionAuthorityCostEdgeGateInput:
    candidate_id: str
    market_id: str
    market_slug: str
    market_question: str
    source_url: str
    source_text: str
    observed_at: datetime
    forecast_probability: Decimal
    market_probability: Decimal
    fee_probability_drag: Decimal
    spread_probability_drag: Decimal
    liquidity_probability_drag: Decimal
    resolution_cost_probability_drag: Decimal
    resolution_authority_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyResolutionAuthorityCostEdgeGateInput:
            raise TypeError(
                "ResearchStrategyResolutionAuthorityCostEdgeGateInput "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "input",
            self,
            ResearchStrategyResolutionAuthorityCostEdgeGateInput,
        )
        for field_name in (
            "candidate_id",
            "market_id",
            "market_slug",
            "market_question",
            "source_url",
            "source_text",
        ):
            _require_private_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "forecast_probability",
            "market_probability",
            "fee_probability_drag",
            "spread_probability_drag",
            "liquidity_probability_drag",
            "resolution_cost_probability_drag",
            "resolution_authority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_report_only_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyResolutionAuthorityCostEdgeGateReasonCodeCount:
    reason_code: str
    count: Decimal
    input_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyResolutionAuthorityCostEdgeGateReasonCodeCount:
            raise TypeError(
                "ResearchStrategyResolutionAuthorityCostEdgeGateReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "reason_code_count",
            self,
            ResearchStrategyResolutionAuthorityCostEdgeGateReasonCodeCount,
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "input_ratio",
            _normalize_probability("input_ratio", self.input_ratio),
        )
        _require_report_only_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyResolutionAuthorityCostEdgeGateRow:
    row_digest: str
    candidate_id: str
    market_id: str
    market_slug: str
    market_question: str
    source_url: str
    source_text: str
    observed_at: datetime
    forecast_probability: Decimal
    market_probability: Decimal
    raw_forecast_edge_probability: Decimal
    fee_probability_drag: Decimal
    spread_probability_drag: Decimal
    liquidity_probability_drag: Decimal
    resolution_cost_probability_drag: Decimal
    total_cost_drag_probability: Decimal
    cost_adjusted_edge_probability: Decimal
    resolution_authority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyResolutionAuthorityCostEdgeGateRow:
            raise TypeError(
                "ResearchStrategyResolutionAuthorityCostEdgeGateRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchStrategyResolutionAuthorityCostEdgeGateRow)
        _require_digest("row_digest", self.row_digest)
        for field_name in (
            "candidate_id",
            "market_id",
            "market_slug",
            "market_question",
            "source_url",
            "source_text",
        ):
            _require_private_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "forecast_probability",
            "market_probability",
            "fee_probability_drag",
            "spread_probability_drag",
            "liquidity_probability_drag",
            "resolution_cost_probability_drag",
            "total_cost_drag_probability",
            "resolution_authority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "raw_forecast_edge_probability",
            _normalize_decimal(
                "raw_forecast_edge_probability",
                self.raw_forecast_edge_probability,
            ),
        )
        object.__setattr__(
            self,
            "cost_adjusted_edge_probability",
            _normalize_decimal(
                "cost_adjusted_edge_probability",
                self.cost_adjusted_edge_probability,
            ),
        )
        _require_member(
            "status",
            self.status,
            RESEARCH_STRATEGY_RESOLUTION_AUTHORITY_COST_EDGE_GATE_STATUSES,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_report_only_flags("row", self)


@dataclass(frozen=True)
class ResearchStrategyResolutionAuthorityCostEdgeGateReport:
    generated_at: datetime
    config_version: str
    source_row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_cost_adjusted_edge_probability: Decimal
    mean_total_cost_drag_probability: Decimal
    mean_resolution_authority_score: Decimal
    status: str
    rows: tuple[ResearchStrategyResolutionAuthorityCostEdgeGateRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyResolutionAuthorityCostEdgeGateReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyResolutionAuthorityCostEdgeGateReport:
            raise TypeError(
                "ResearchStrategyResolutionAuthorityCostEdgeGateReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "report",
            self,
            ResearchStrategyResolutionAuthorityCostEdgeGateReport,
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "source_row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "mean_cost_adjusted_edge_probability",
            "mean_total_cost_drag_probability",
            "mean_resolution_authority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name))
                if not field_name.startswith("mean_cost_adjusted")
                else _normalize_decimal(field_name, getattr(self, field_name)),
            )
        _require_member(
            "status",
            self.status,
            RESEARCH_STRATEGY_RESOLUTION_AUTHORITY_COST_EDGE_GATE_STATUSES,
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _require_report_only_flags("report", self)
        expected_digest = _payload_digest(
            _report_public_payload(self, include_digest=False),
        )
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        else:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, Any]:
        return research_strategy_resolution_authority_cost_edge_gate_report_payload(self)


def build_research_strategy_resolution_authority_cost_edge_gate_report(
    inputs: Iterable[ResearchStrategyResolutionAuthorityCostEdgeGateInput],
    *,
    config: ResearchStrategyResolutionAuthorityCostEdgeGateConfig | None = None,
    generated_at: datetime | None = None,
) -> ResearchStrategyResolutionAuthorityCostEdgeGateReport:
    cfg = config or ResearchStrategyResolutionAuthorityCostEdgeGateConfig()
    if type(cfg) is not ResearchStrategyResolutionAuthorityCostEdgeGateConfig:
        raise ValueError(
            "config must be a ResearchStrategyResolutionAuthorityCostEdgeGateConfig",
        )
    _require_report_only_flags("config", cfg)
    materialized_inputs = tuple(inputs)
    rows = tuple(_row_for_input(item, cfg) for item in materialized_inputs)
    rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                _status_sort_key(row.status),
                row.cost_adjusted_edge_probability,
                row.row_digest,
            ),
        ),
    )
    source_row_count = _count_decimal(len(materialized_inputs))
    pass_count = _count_decimal(sum(1 for row in rows if row.status == "pass"))
    watch_count = _count_decimal(sum(1 for row in rows if row.status == "watch"))
    block_count = _count_decimal(sum(1 for row in rows if row.status == "block"))
    report_status = _report_status(source_row_count, block_count, watch_count)
    reason_counts = _reason_code_counts(rows, source_row_count)
    return ResearchStrategyResolutionAuthorityCostEdgeGateReport(
        generated_at=_as_utc("generated_at", generated_at or datetime.now(UTC)),
        config_version=cfg.config_version,
        source_row_count=source_row_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        mean_cost_adjusted_edge_probability=_mean(
            tuple(row.cost_adjusted_edge_probability for row in rows),
        ),
        mean_total_cost_drag_probability=_mean(
            tuple(row.total_cost_drag_probability for row in rows),
        ),
        mean_resolution_authority_score=_mean(
            tuple(row.resolution_authority_score for row in rows),
        ),
        status=report_status,
        rows=rows,
        reason_code_counts=reason_counts,
        reason_codes=_report_reason_codes(report_status, rows),
    )


def research_strategy_resolution_authority_cost_edge_gate_report_payload(
    report: ResearchStrategyResolutionAuthorityCostEdgeGateReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is dict:
        _reject_unsafe_public_payload(
            "research_strategy_resolution_authority_cost_edge_gate_report_payload",
            report,
        )
        _validate_public_payload_structure(report)
        _validate_payload_digest(report)
        _validate_public_payload_semantics(report)
        return report
    if type(report) is not ResearchStrategyResolutionAuthorityCostEdgeGateReport:
        raise ValueError(
            "report must be a ResearchStrategyResolutionAuthorityCostEdgeGateReport",
        )
    _require_report_only_flags("report", report)
    payload = _report_public_payload(report, include_digest=True)
    _reject_unsafe_public_payload(
        "research_strategy_resolution_authority_cost_edge_gate_report_payload",
        payload,
    )
    _validate_public_payload_structure(payload)
    _validate_payload_digest(payload)
    _validate_public_payload_semantics(payload)
    return payload


def research_strategy_resolution_authority_cost_edge_gate_report_digest(
    report: ResearchStrategyResolutionAuthorityCostEdgeGateReport,
) -> str:
    if type(report) is not ResearchStrategyResolutionAuthorityCostEdgeGateReport:
        raise ValueError(
            "report must be a ResearchStrategyResolutionAuthorityCostEdgeGateReport",
        )
    payload = _report_public_payload(report, include_digest=False)
    return _payload_digest(payload)


def validate_research_strategy_resolution_authority_cost_edge_gate_report_digest(
    report: ResearchStrategyResolutionAuthorityCostEdgeGateReport,
) -> None:
    if (
        report.derived_validation_digest
        != research_strategy_resolution_authority_cost_edge_gate_report_digest(report)
    ):
        raise ValueError("derived_validation_digest does not match report payload")


def _row_for_input(
    item: ResearchStrategyResolutionAuthorityCostEdgeGateInput,
    config: ResearchStrategyResolutionAuthorityCostEdgeGateConfig,
) -> ResearchStrategyResolutionAuthorityCostEdgeGateRow:
    if type(item) is not ResearchStrategyResolutionAuthorityCostEdgeGateInput:
        raise ValueError(
            "input must be a ResearchStrategyResolutionAuthorityCostEdgeGateInput",
        )
    _require_report_only_flags("input", item)
    with localcontext(DECIMAL_CONTEXT):
        raw_edge = _normalize_decimal(
            "raw_forecast_edge_probability",
            item.forecast_probability - item.market_probability,
        )
        total_cost = _normalize_nonnegative_decimal(
            "total_cost_drag_probability",
            item.fee_probability_drag
            + item.spread_probability_drag
            + item.liquidity_probability_drag
            + item.resolution_cost_probability_drag,
        )
        adjusted_edge = _normalize_decimal(
            "cost_adjusted_edge_probability",
            raw_edge - total_cost,
        )
    status = _row_status(
        adjusted_edge,
        total_cost,
        item.resolution_authority_score,
        config,
    )
    return ResearchStrategyResolutionAuthorityCostEdgeGateRow(
        row_digest=_input_digest(item),
        candidate_id=item.candidate_id,
        market_id=item.market_id,
        market_slug=item.market_slug,
        market_question=item.market_question,
        source_url=item.source_url,
        source_text=item.source_text,
        observed_at=item.observed_at,
        forecast_probability=item.forecast_probability,
        market_probability=item.market_probability,
        raw_forecast_edge_probability=raw_edge,
        fee_probability_drag=item.fee_probability_drag,
        spread_probability_drag=item.spread_probability_drag,
        liquidity_probability_drag=item.liquidity_probability_drag,
        resolution_cost_probability_drag=item.resolution_cost_probability_drag,
        total_cost_drag_probability=total_cost,
        cost_adjusted_edge_probability=adjusted_edge,
        resolution_authority_score=item.resolution_authority_score,
        status=status,
        reason_codes=_row_reason_codes(
            adjusted_edge,
            total_cost,
            item.resolution_authority_score,
            status,
            config,
        ),
    )


def _row_status(
    adjusted_edge: Decimal,
    total_cost: Decimal,
    authority_score: Decimal,
    config: ResearchStrategyResolutionAuthorityCostEdgeGateConfig,
) -> str:
    if (
        adjusted_edge < config.cost_adjusted_edge_watch_floor
        or total_cost > config.total_cost_drag_watch_ceiling
        or authority_score < config.resolution_authority_watch_floor
    ):
        return "block"
    if (
        adjusted_edge >= config.cost_adjusted_edge_pass_floor
        and total_cost <= config.total_cost_drag_pass_ceiling
        and authority_score >= config.resolution_authority_pass_floor
    ):
        return "pass"
    return "watch"


def _row_reason_codes(
    adjusted_edge: Decimal,
    total_cost: Decimal,
    authority_score: Decimal,
    status: str,
    config: ResearchStrategyResolutionAuthorityCostEdgeGateConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if adjusted_edge < config.cost_adjusted_edge_watch_floor:
        codes.append("cost_adjusted_edge_block")
    elif adjusted_edge < config.cost_adjusted_edge_pass_floor:
        codes.append("cost_adjusted_edge_watch")
    if authority_score < config.resolution_authority_watch_floor:
        codes.append("resolution_authority_block")
    elif authority_score < config.resolution_authority_pass_floor:
        codes.append("resolution_authority_watch")
    if total_cost > config.total_cost_drag_watch_ceiling:
        codes.append("total_cost_drag_block")
    elif total_cost > config.total_cost_drag_pass_ceiling:
        codes.append("total_cost_drag_watch")
    if not codes and status == "pass":
        return ("resolution_authority_cost_edge_gate_pass",)
    return tuple(codes)


def _report_status(
    source_row_count: Decimal,
    block_count: Decimal,
    watch_count: Decimal,
) -> str:
    if source_row_count == ZERO or block_count > ZERO:
        return "block"
    if watch_count > ZERO:
        return "watch"
    return "pass"


def _report_reason_codes(
    status: str,
    rows: tuple[ResearchStrategyResolutionAuthorityCostEdgeGateRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("resolution_authority_cost_edge_gate_report_empty",)
    codes = [f"resolution_authority_cost_edge_gate_report_{status}"]
    row_reason_codes = {code for row in rows for code in row.reason_codes}
    if any(code.startswith("cost_adjusted_edge_") for code in row_reason_codes):
        codes.append("cost_adjusted_edge_review")
    if any(code.startswith("total_cost_drag_") for code in row_reason_codes):
        codes.append("total_cost_drag_review")
    if any(code.startswith("resolution_authority_") for code in row_reason_codes):
        codes.append("resolution_authority_review")
    return tuple(code for code in codes if code in REPORT_REASON_CODES)


def _reason_code_counts(
    rows: tuple[ResearchStrategyResolutionAuthorityCostEdgeGateRow, ...],
    source_row_count: Decimal,
) -> tuple[ResearchStrategyResolutionAuthorityCostEdgeGateReasonCodeCount, ...]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    if source_row_count == ZERO:
        return ()
    return tuple(
        ResearchStrategyResolutionAuthorityCostEdgeGateReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(count),
            input_ratio=_ratio_decimal(_count_decimal(count), source_row_count),
        )
        for reason_code, count in sorted(counter.items())
    )


def _report_public_payload(
    report: ResearchStrategyResolutionAuthorityCostEdgeGateReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "config_version": report.config_version,
        "generated_at": report.generated_at.isoformat(),
        "source_row_count": _decimal_payload(report.source_row_count),
        "pass_count": _decimal_payload(report.pass_count),
        "watch_count": _decimal_payload(report.watch_count),
        "block_count": _decimal_payload(report.block_count),
        "mean_cost_adjusted_edge_probability": _decimal_payload(
            report.mean_cost_adjusted_edge_probability,
        ),
        "mean_total_cost_drag_probability": _decimal_payload(
            report.mean_total_cost_drag_probability,
        ),
        "mean_resolution_authority_score": _decimal_payload(
            report.mean_resolution_authority_score,
        ),
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "reason_code_counts": [
            {
                "reason_code": item.reason_code,
                "count": _decimal_payload(item.count),
                "input_ratio": _decimal_payload(item.input_ratio),
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            }
            for item in report.reason_code_counts
        ],
        "rows": [
            _row_public_payload(row_number, row)
            for row_number, row in enumerate(report.rows, start=1)
        ],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    if include_digest:
        payload["derived_validation_digest"] = report.derived_validation_digest
    return payload


def _row_public_payload(
    row_number: int,
    row: ResearchStrategyResolutionAuthorityCostEdgeGateRow,
) -> dict[str, Any]:
    return {
        "row_number": _decimal_payload(_count_decimal(row_number)),
        "row_digest": row.row_digest,
        "observed_at": row.observed_at.isoformat(),
        "raw_forecast_edge_probability": _decimal_payload(
            row.raw_forecast_edge_probability,
        ),
        "total_cost_drag_probability": _decimal_payload(
            row.total_cost_drag_probability,
        ),
        "cost_adjusted_edge_probability": _decimal_payload(
            row.cost_adjusted_edge_probability,
        ),
        "resolution_authority_score": _decimal_payload(row.resolution_authority_score),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _payload_digest(payload: dict[str, Any]) -> str:
    encoded = dumps(payload, allow_nan=False, separators=(",", ":"), sort_keys=True)
    return sha256(encoded.encode("utf-8")).hexdigest()


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be present")
    _require_digest("derived_validation_digest", digest)
    payload_without_digest = {
        key: value for key, value in payload.items() if key != "derived_validation_digest"
    }
    if _payload_digest(payload_without_digest) != digest:
        raise ValueError("derived_validation_digest does not match report payload")


def _validate_public_payload_structure(payload: dict[str, Any]) -> None:
    _require_public_payload_keys("report", payload, _REPORT_PUBLIC_PAYLOAD_KEYS)
    if (
        payload["config_version"]
        != DEFAULT_RESEARCH_STRATEGY_RESOLUTION_AUTHORITY_COST_EDGE_GATE_REPORT_CONFIG_VERSION
    ):
        _raise_payload_schema("config_version is unsupported")
    _require_public_payload_datetime("generated_at", payload["generated_at"])
    for field_name in (
        "source_row_count",
        "pass_count",
        "watch_count",
        "block_count",
    ):
        _require_public_payload_decimal(field_name, payload[field_name], "count")
    _require_public_payload_decimal(
        "mean_cost_adjusted_edge_probability",
        payload["mean_cost_adjusted_edge_probability"],
        "decimal",
    )
    _require_public_payload_decimal(
        "mean_total_cost_drag_probability",
        payload["mean_total_cost_drag_probability"],
        "nonnegative",
    )
    _require_public_payload_decimal(
        "mean_resolution_authority_score",
        payload["mean_resolution_authority_score"],
        "probability",
    )
    _require_public_payload_member(
        "status",
        payload["status"],
        RESEARCH_STRATEGY_RESOLUTION_AUTHORITY_COST_EDGE_GATE_STATUSES,
    )
    _require_public_payload_reason_codes(
        "reason_codes",
        payload["reason_codes"],
        REPORT_REASON_CODES,
    )
    _require_public_payload_flags("report", payload)

    reason_code_counts = payload["reason_code_counts"]
    if type(reason_code_counts) is not list:
        _raise_payload_schema("reason_code_counts must be a list")
    seen_reason_codes: set[str] = set()
    for index, item in enumerate(reason_code_counts, start=1):
        label = f"reason_code_counts[{index}]"
        _require_public_payload_keys(
            label,
            item,
            _REASON_CODE_COUNT_PUBLIC_PAYLOAD_KEYS,
        )
        reason_code = item["reason_code"]
        _require_public_payload_member(
            f"{label}.reason_code",
            reason_code,
            ROW_REASON_CODES,
        )
        if reason_code in seen_reason_codes:
            _raise_payload_schema("reason_code_counts must not contain duplicates")
        seen_reason_codes.add(reason_code)
        _require_public_payload_decimal(f"{label}.count", item["count"], "positive_count")
        _require_public_payload_decimal(
            f"{label}.input_ratio",
            item["input_ratio"],
            "probability",
        )
        _require_public_payload_flags(label, item)

    rows = payload["rows"]
    if type(rows) is not list:
        _raise_payload_schema("rows must be a list")
    for index, item in enumerate(rows, start=1):
        label = f"rows[{index}]"
        _require_public_payload_keys(label, item, _ROW_PUBLIC_PAYLOAD_KEYS)
        _require_public_payload_decimal(
            f"{label}.row_number",
            item["row_number"],
            "positive_count",
        )
        try:
            _require_digest(f"{label}.row_digest", item["row_digest"])
        except ValueError as exc:
            raise ValueError("payload schema violation: row_digest is invalid") from exc
        _require_public_payload_datetime(f"{label}.observed_at", item["observed_at"])
        _require_public_payload_decimal(
            f"{label}.raw_forecast_edge_probability",
            item["raw_forecast_edge_probability"],
            "decimal",
        )
        _require_public_payload_decimal(
            f"{label}.total_cost_drag_probability",
            item["total_cost_drag_probability"],
            "nonnegative",
        )
        _require_public_payload_decimal(
            f"{label}.cost_adjusted_edge_probability",
            item["cost_adjusted_edge_probability"],
            "decimal",
        )
        _require_public_payload_decimal(
            f"{label}.resolution_authority_score",
            item["resolution_authority_score"],
            "probability",
        )
        _require_public_payload_member(
            f"{label}.status",
            item["status"],
            RESEARCH_STRATEGY_RESOLUTION_AUTHORITY_COST_EDGE_GATE_STATUSES,
        )
        _require_public_payload_reason_codes(
            f"{label}.reason_codes",
            item["reason_codes"],
            ROW_REASON_CODES,
        )
        _require_public_payload_flags(label, item)


def _validate_public_payload_semantics(payload: dict[str, Any]) -> None:
    config = ResearchStrategyResolutionAuthorityCostEdgeGateConfig()
    rows = payload["rows"]
    row_values: list[tuple[str, Decimal, str, tuple[str, ...]]] = []
    for index, item in enumerate(rows, start=1):
        row_number = _require_public_payload_decimal(
            f"rows[{index}].row_number",
            item["row_number"],
            "positive_count",
        )
        if row_number != _count_decimal(index):
            _raise_payload_schema("row_number must be sequential")
        adjusted_edge = _require_public_payload_decimal(
            f"rows[{index}].cost_adjusted_edge_probability",
            item["cost_adjusted_edge_probability"],
            "decimal",
        )
        total_cost = _require_public_payload_decimal(
            f"rows[{index}].total_cost_drag_probability",
            item["total_cost_drag_probability"],
            "nonnegative",
        )
        authority_score = _require_public_payload_decimal(
            f"rows[{index}].resolution_authority_score",
            item["resolution_authority_score"],
            "probability",
        )
        expected_status = _row_status(
            adjusted_edge,
            total_cost,
            authority_score,
            config,
        )
        if item["status"] != expected_status:
            _raise_payload_schema("row status is inconsistent")
        expected_reason_codes = _row_reason_codes(
            adjusted_edge,
            total_cost,
            authority_score,
            expected_status,
            config,
        )
        if tuple(item["reason_codes"]) != expected_reason_codes:
            _raise_payload_schema("row reason_codes are inconsistent")
        row_values.append(
            (
                expected_status,
                adjusted_edge,
                item["row_digest"],
                expected_reason_codes,
            ),
        )

    if row_values != sorted(
        row_values,
        key=lambda item: (_status_sort_key(item[0]), item[1], item[2]),
    ):
        _raise_payload_schema("rows must use canonical ordering")

    source_row_count = _require_public_payload_decimal(
        "source_row_count",
        payload["source_row_count"],
        "count",
    )
    pass_count = _require_public_payload_decimal(
        "pass_count",
        payload["pass_count"],
        "count",
    )
    watch_count = _require_public_payload_decimal(
        "watch_count",
        payload["watch_count"],
        "count",
    )
    block_count = _require_public_payload_decimal(
        "block_count",
        payload["block_count"],
        "count",
    )
    expected_source_row_count = _count_decimal(len(row_values))
    expected_pass_count = _count_decimal(
        sum(1 for status, _, _, _ in row_values if status == "pass"),
    )
    expected_watch_count = _count_decimal(
        sum(1 for status, _, _, _ in row_values if status == "watch"),
    )
    expected_block_count = _count_decimal(
        sum(1 for status, _, _, _ in row_values if status == "block"),
    )
    if (
        source_row_count != expected_source_row_count
        or pass_count != expected_pass_count
        or watch_count != expected_watch_count
        or block_count != expected_block_count
    ):
        _raise_payload_schema("report counts are inconsistent")

    adjusted_edges = tuple(item[1] for item in row_values)
    total_costs = tuple(
        _require_public_payload_decimal(
            f"rows[{index}].total_cost_drag_probability",
            item["total_cost_drag_probability"],
            "nonnegative",
        )
        for index, item in enumerate(rows, start=1)
    )
    authority_scores = tuple(
        _require_public_payload_decimal(
            f"rows[{index}].resolution_authority_score",
            item["resolution_authority_score"],
            "probability",
        )
        for index, item in enumerate(rows, start=1)
    )
    if _require_public_payload_decimal(
        "mean_cost_adjusted_edge_probability",
        payload["mean_cost_adjusted_edge_probability"],
        "decimal",
    ) != _mean(adjusted_edges):
        _raise_payload_schema("mean_cost_adjusted_edge_probability is inconsistent")
    if _require_public_payload_decimal(
        "mean_total_cost_drag_probability",
        payload["mean_total_cost_drag_probability"],
        "nonnegative",
    ) != _mean(total_costs):
        _raise_payload_schema("mean_total_cost_drag_probability is inconsistent")
    if _require_public_payload_decimal(
        "mean_resolution_authority_score",
        payload["mean_resolution_authority_score"],
        "probability",
    ) != _mean(authority_scores):
        _raise_payload_schema("mean_resolution_authority_score is inconsistent")

    expected_report_status = _report_status(
        expected_source_row_count,
        expected_block_count,
        expected_watch_count,
    )
    if payload["status"] != expected_report_status:
        _raise_payload_schema("report status is inconsistent")
    expected_report_reason_codes = _public_payload_report_reason_codes(
        expected_report_status,
        tuple(item[3] for item in row_values),
    )
    if tuple(payload["reason_codes"]) != expected_report_reason_codes:
        _raise_payload_schema("report reason_codes are inconsistent")

    counter: Counter[str] = Counter(
        reason_code
        for _, _, _, reason_codes in row_values
        for reason_code in reason_codes
    )
    expected_reason_code_counts = [
        {
            "reason_code": reason_code,
            "count": _decimal_payload(_count_decimal(count)),
            "input_ratio": _decimal_payload(
                _ratio_decimal(_count_decimal(count), expected_source_row_count),
            ),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        }
        for reason_code, count in sorted(counter.items())
    ]
    if payload["reason_code_counts"] != expected_reason_code_counts:
        _raise_payload_schema("reason_code_counts are inconsistent")


def _public_payload_report_reason_codes(
    status: str,
    row_reason_codes: tuple[tuple[str, ...], ...],
) -> tuple[str, ...]:
    if not row_reason_codes:
        return ("resolution_authority_cost_edge_gate_report_empty",)
    codes = [f"resolution_authority_cost_edge_gate_report_{status}"]
    flattened = {code for reason_codes in row_reason_codes for code in reason_codes}
    if any(code.startswith("cost_adjusted_edge_") for code in flattened):
        codes.append("cost_adjusted_edge_review")
    if any(code.startswith("total_cost_drag_") for code in flattened):
        codes.append("total_cost_drag_review")
    if any(code.startswith("resolution_authority_") for code in flattened):
        codes.append("resolution_authority_review")
    return tuple(codes)


def _require_public_payload_keys(
    label: str,
    value: object,
    expected_keys: frozenset[str],
) -> None:
    if type(value) is not dict or set(value) != expected_keys:
        _raise_payload_schema(f"{label} has unexpected fields")


def _require_public_payload_flags(label: str, value: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if value[field_name] is not True:
            _raise_payload_schema(f"{label}.{field_name} must be True")


def _require_public_payload_member(
    label: str,
    value: object,
    allowed: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed:
        _raise_payload_schema(f"{label} is invalid")


def _require_public_payload_reason_codes(
    label: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not list or any(type(item) is not str for item in value):
        _raise_payload_schema(f"{label} must be a string list")
    normalized = tuple(value)
    if len(set(normalized)) != len(normalized) or any(
        reason_code not in allowed for reason_code in normalized
    ):
        _raise_payload_schema(f"{label} is invalid")
    return normalized


def _require_public_payload_datetime(label: str, value: object) -> datetime:
    if type(value) is not str:
        _raise_payload_schema(f"{label} must be a datetime string")
    try:
        parsed = datetime.fromisoformat(value)
        normalized = _as_utc(label, parsed)
    except ValueError as exc:
        raise ValueError(f"payload schema violation: {label} is invalid") from exc
    if normalized.isoformat() != value:
        _raise_payload_schema(f"{label} must use canonical UTC format")
    return normalized


def _require_public_payload_decimal(
    label: str,
    value: object,
    decimal_kind: str,
) -> Decimal:
    if type(value) is not str:
        _raise_payload_schema(f"{label} must be a decimal string")
    try:
        parsed = Decimal(value)
        if decimal_kind in ("count", "positive_count"):
            normalized = _normalize_nonnegative_decimal(label, parsed)
            if normalized != normalized.to_integral_value():
                _raise_payload_schema(f"{label} must be a whole decimal")
            if decimal_kind == "positive_count" and normalized == ZERO:
                _raise_payload_schema(f"{label} must be positive")
        elif decimal_kind == "probability":
            normalized = _normalize_probability(label, parsed)
        elif decimal_kind == "nonnegative":
            normalized = _normalize_nonnegative_decimal(label, parsed)
        elif decimal_kind == "decimal":
            normalized = _normalize_decimal(label, parsed)
        else:
            _raise_payload_schema("decimal validator is unsupported")
    except (InvalidOperation, ValueError) as exc:
        if "payload schema" in str(exc):
            raise
        raise ValueError(f"payload schema violation: {label} is invalid") from exc
    if _decimal_payload(normalized) != value:
        _raise_payload_schema(f"{label} must be canonical")
    return normalized


def _raise_payload_schema(detail: str) -> None:
    raise ValueError(f"payload schema violation: {detail}")


def _input_digest(item: ResearchStrategyResolutionAuthorityCostEdgeGateInput) -> str:
    payload = {
        "candidate_id": item.candidate_id,
        "market_id": item.market_id,
        "market_slug": item.market_slug,
        "market_question": item.market_question,
        "source_url": item.source_url,
        "source_text": item.source_text,
        "observed_at": item.observed_at.isoformat(),
        "forecast_probability": _decimal_payload(item.forecast_probability),
        "market_probability": _decimal_payload(item.market_probability),
        "fee_probability_drag": _decimal_payload(item.fee_probability_drag),
        "spread_probability_drag": _decimal_payload(item.spread_probability_drag),
        "liquidity_probability_drag": _decimal_payload(item.liquidity_probability_drag),
        "resolution_cost_probability_drag": _decimal_payload(
            item.resolution_cost_probability_drag,
        ),
        "resolution_authority_score": _decimal_payload(item.resolution_authority_score),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return _payload_digest(payload)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_decimal("mean", sum(values, ZERO) / _count_decimal(len(values)))


def _ratio_decimal(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability("input_ratio", numerator / denominator)


def _status_sort_key(status: str) -> Decimal:
    if status == "block":
        return Decimal("0")
    if status == "watch":
        return Decimal("1")
    return Decimal("2")


def _count_decimal(value: int) -> Decimal:
    return _normalize_nonnegative_decimal("count", Decimal(str(value)))


def _decimal_payload(value: Decimal) -> str:
    return format(value, "f")


def _normalize_rows(
    rows: tuple[ResearchStrategyResolutionAuthorityCostEdgeGateRow, ...],
) -> tuple[ResearchStrategyResolutionAuthorityCostEdgeGateRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchStrategyResolutionAuthorityCostEdgeGateRow:
            raise ValueError("rows must contain exact row records")
        _require_report_only_flags("row", row)
    return rows


def _normalize_reason_code_counts(
    values: tuple[
        ResearchStrategyResolutionAuthorityCostEdgeGateReasonCodeCount,
        ...,
    ],
) -> tuple[ResearchStrategyResolutionAuthorityCostEdgeGateReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for value in values:
        if type(value) is not ResearchStrategyResolutionAuthorityCostEdgeGateReasonCodeCount:
            raise ValueError("reason_code_counts must contain exact count records")
        _require_report_only_flags("reason_code_count", value)
    return values


def _normalize_reason_codes(
    label: str,
    values: tuple[str, ...],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{label} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_member(label, value, allowed)
        if value not in normalized:
            normalized.append(value)
    return tuple(normalized)


def _require_reason_code(label: str, value: str) -> None:
    if value not in ROW_REASON_CODES and value not in REPORT_REASON_CODES:
        raise ValueError(f"{label} is not a supported reason code")


def _require_report_only_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_floor_pair(label: str, pass_floor: Decimal, watch_floor: Decimal) -> None:
    if pass_floor < watch_floor:
        raise ValueError(f"{label}_pass_floor must be greater than or equal to watch floor")


def _require_ceiling_pair(label: str, pass_ceiling: Decimal, watch_ceiling: Decimal) -> None:
    if pass_ceiling > watch_ceiling:
        raise ValueError(
            f"{label}_pass_ceiling must be less than or equal to watch ceiling",
        )


def _require_member(label: str, value: str, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(label, value)
    if value not in allowed:
        raise ValueError(f"{label} must be one of {allowed}")


def _require_private_string(label: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{label} must be a string")
    if not value.strip():
        raise ValueError(f"{label} must not be blank")


def _require_canonical_string(label: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{label} must be a string")
    if value == "" or value != value.strip() or any(ord(character) < 32 for character in value):
        raise ValueError(f"{label} must be a canonical string")


def _require_digest(label: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{label} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{label} must be a lowercase sha256 digest")


def _as_utc(label: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{label} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{label} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_probability(label: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(label, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{label} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_decimal(label: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(label, value)
    if normalized < ZERO:
        raise ValueError(f"{label} must be nonnegative")
    return normalized


def _normalize_decimal(label: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{label} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{label} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(DECIMAL_QUANTUM)


def _require_exact_type(label: str, value: object, expected: type[object]) -> None:
    if type(value) is not expected:
        raise ValueError(f"{label} must be exact")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe non-string key in {label}")
            _reject_unsafe_fragment(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_fragment(label, value)
        return
    if type(value) in (bool, type(None)):
        return
    raise ValueError(f"unsafe public payload value in {label}")


def _reject_unsafe_fragment(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public payload field in {label}")


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_RESOLUTION_AUTHORITY_COST_EDGE_GATE_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_RESOLUTION_AUTHORITY_COST_EDGE_GATE_STATUSES",
    "ResearchStrategyResolutionAuthorityCostEdgeGateConfig",
    "ResearchStrategyResolutionAuthorityCostEdgeGateInput",
    "ResearchStrategyResolutionAuthorityCostEdgeGateReasonCodeCount",
    "ResearchStrategyResolutionAuthorityCostEdgeGateReport",
    "ResearchStrategyResolutionAuthorityCostEdgeGateRow",
    "build_research_strategy_resolution_authority_cost_edge_gate_report",
    "research_strategy_resolution_authority_cost_edge_gate_report_digest",
    "research_strategy_resolution_authority_cost_edge_gate_report_payload",
    "validate_research_strategy_resolution_authority_cost_edge_gate_report_digest",
)
