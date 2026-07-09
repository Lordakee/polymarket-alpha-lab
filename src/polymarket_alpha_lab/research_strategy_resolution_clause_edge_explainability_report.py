"""Report-only resolution clause edge explainability scorecard."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any, Iterable


DEFAULT_RESEARCH_STRATEGY_RESOLUTION_CLAUSE_EDGE_EXPLAINABILITY_REPORT_CONFIG_VERSION = (
    "research-strategy-resolution-clause-edge-explainability-report-v0"
)
RESEARCH_STRATEGY_RESOLUTION_CLAUSE_EDGE_EXPLAINABILITY_STATUSES = (
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
    "edge_explainability_block",
    "edge_explainability_watch",
    "resolution_clause_ambiguity_block",
    "resolution_clause_ambiguity_watch",
    "resolution_clause_edge_explainability_pass",
    "source_confidence_block",
    "source_confidence_watch",
)
REPORT_REASON_CODES = (
    "cost_adjusted_edge_review",
    "edge_explainability_review",
    "resolution_clause_ambiguity_review",
    "resolution_clause_edge_explainability_report_block",
    "resolution_clause_edge_explainability_report_empty",
    "resolution_clause_edge_explainability_report_pass",
    "resolution_clause_edge_explainability_report_watch",
    "source_confidence_review",
)
_UNSAFE_PUBLIC_FRAGMENTS = (
    "api" + "_key",
    "candidate" + "_id",
    "candidate",
    "credential",
    "data" + "base",
    "dsn",
    "market" + "_id",
    "market" + "_slug",
    "market" + "_ques" + "tion",
    "private" + "_key",
    "ques" + "tion",
    "raw" + "_text",
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
    "b" + "uy",
    "se" + "ll",
    "reco" + "mmendation",
    "siz" + "ing",
    "http://",
    "https://",
    "://",
)


@dataclass(frozen=True)
class ResearchStrategyResolutionClauseEdgeExplainabilityConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_RESOLUTION_CLAUSE_EDGE_EXPLAINABILITY_REPORT_CONFIG_VERSION
    )
    cost_adjusted_edge_pass_floor: Decimal = Decimal("0.030000")
    cost_adjusted_edge_watch_floor: Decimal = Decimal("0.000000")
    clause_ambiguity_pass_ceiling: Decimal = Decimal("0.200000")
    clause_ambiguity_watch_ceiling: Decimal = Decimal("0.500000")
    edge_explainability_pass_floor: Decimal = Decimal("0.750000")
    edge_explainability_watch_floor: Decimal = Decimal("0.550000")
    source_confidence_pass_floor: Decimal = Decimal("0.700000")
    source_confidence_watch_floor: Decimal = Decimal("0.500000")
    clause_clarity_weight: Decimal = Decimal("0.300000")
    edge_quality_weight: Decimal = Decimal("0.400000")
    source_confidence_weight: Decimal = Decimal("0.200000")
    cost_stability_weight: Decimal = Decimal("0.100000")
    total_cost_drag_watch_ceiling: Decimal = Decimal("0.080000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyResolutionClauseEdgeExplainabilityConfig:
            raise TypeError(
                "ResearchStrategyResolutionClauseEdgeExplainabilityConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchStrategyResolutionClauseEdgeExplainabilityConfig,
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_RESOLUTION_CLAUSE_EDGE_EXPLAINABILITY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "cost_adjusted_edge_pass_floor",
            "cost_adjusted_edge_watch_floor",
            "clause_ambiguity_pass_ceiling",
            "clause_ambiguity_watch_ceiling",
            "edge_explainability_pass_floor",
            "edge_explainability_watch_floor",
            "source_confidence_pass_floor",
            "source_confidence_watch_floor",
            "clause_clarity_weight",
            "edge_quality_weight",
            "source_confidence_weight",
            "cost_stability_weight",
            "total_cost_drag_watch_ceiling",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.total_cost_drag_watch_ceiling == ZERO:
            raise ValueError("total_cost_drag_watch_ceiling must be positive")
        _require_floor_pair(
            "cost_adjusted_edge",
            self.cost_adjusted_edge_pass_floor,
            self.cost_adjusted_edge_watch_floor,
        )
        _require_ceiling_pair(
            "clause_ambiguity",
            self.clause_ambiguity_pass_ceiling,
            self.clause_ambiguity_watch_ceiling,
        )
        _require_floor_pair(
            "edge_explainability",
            self.edge_explainability_pass_floor,
            self.edge_explainability_watch_floor,
        )
        _require_floor_pair(
            "source_confidence",
            self.source_confidence_pass_floor,
            self.source_confidence_watch_floor,
        )
        weight_sum = _normalize_probability(
            "weights",
            self.clause_clarity_weight
            + self.edge_quality_weight
            + self.source_confidence_weight
            + self.cost_stability_weight,
        )
        if weight_sum != ONE:
            raise ValueError("weights must sum to 1.000000")
        _require_report_only_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyResolutionClauseEdgeExplainabilityInput:
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
    clause_ambiguity_score: Decimal
    edge_explanation_quality_score: Decimal
    source_confidence_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyResolutionClauseEdgeExplainabilityInput:
            raise TypeError(
                "ResearchStrategyResolutionClauseEdgeExplainabilityInput "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "input",
            self,
            ResearchStrategyResolutionClauseEdgeExplainabilityInput,
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
            "clause_ambiguity_score",
            "edge_explanation_quality_score",
            "source_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_report_only_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyResolutionClauseEdgeExplainabilityReasonCodeCount:
    reason_code: str
    count: Decimal
    input_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyResolutionClauseEdgeExplainabilityReasonCodeCount:
            raise TypeError(
                "ResearchStrategyResolutionClauseEdgeExplainabilityReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "reason_code_count",
            self,
            ResearchStrategyResolutionClauseEdgeExplainabilityReasonCodeCount,
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
class ResearchStrategyResolutionClauseEdgeExplainabilityRow:
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
    clause_ambiguity_score: Decimal
    edge_explanation_quality_score: Decimal
    source_confidence_score: Decimal
    edge_explainability_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyResolutionClauseEdgeExplainabilityRow:
            raise TypeError(
                "ResearchStrategyResolutionClauseEdgeExplainabilityRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchStrategyResolutionClauseEdgeExplainabilityRow)
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
            "clause_ambiguity_score",
            "edge_explanation_quality_score",
            "source_confidence_score",
            "edge_explainability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
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
            RESEARCH_STRATEGY_RESOLUTION_CLAUSE_EDGE_EXPLAINABILITY_STATUSES,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_report_only_flags("row", self)


@dataclass(frozen=True)
class ResearchStrategyResolutionClauseEdgeExplainabilityReport:
    generated_at: datetime
    config_version: str
    source_row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_cost_adjusted_edge_probability: Decimal
    mean_clause_ambiguity_score: Decimal
    mean_edge_explainability_score: Decimal
    min_edge_explainability_score: Decimal
    status: str
    rows: tuple[ResearchStrategyResolutionClauseEdgeExplainabilityRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyResolutionClauseEdgeExplainabilityReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyResolutionClauseEdgeExplainabilityReport:
            raise TypeError(
                "ResearchStrategyResolutionClauseEdgeExplainabilityReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "report",
            self,
            ResearchStrategyResolutionClauseEdgeExplainabilityReport,
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_RESOLUTION_CLAUSE_EDGE_EXPLAINABILITY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "source_row_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_clause_ambiguity_score",
            "mean_edge_explainability_score",
            "min_edge_explainability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "mean_cost_adjusted_edge_probability",
            _normalize_decimal(
                "mean_cost_adjusted_edge_probability",
                self.mean_cost_adjusted_edge_probability,
            ),
        )
        _require_member(
            "status",
            self.status,
            RESEARCH_STRATEGY_RESOLUTION_CLAUSE_EDGE_EXPLAINABILITY_STATUSES,
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
        return research_strategy_resolution_clause_edge_explainability_report_payload(self)


def build_research_strategy_resolution_clause_edge_explainability_report(
    inputs: Iterable[ResearchStrategyResolutionClauseEdgeExplainabilityInput],
    *,
    config: ResearchStrategyResolutionClauseEdgeExplainabilityConfig | None = None,
    generated_at: datetime | None = None,
) -> ResearchStrategyResolutionClauseEdgeExplainabilityReport:
    cfg = config or ResearchStrategyResolutionClauseEdgeExplainabilityConfig()
    if type(cfg) is not ResearchStrategyResolutionClauseEdgeExplainabilityConfig:
        raise ValueError(
            "config must be a ResearchStrategyResolutionClauseEdgeExplainabilityConfig",
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
    return ResearchStrategyResolutionClauseEdgeExplainabilityReport(
        generated_at=_as_utc("generated_at", generated_at or datetime.now(UTC)),
        config_version=cfg.config_version,
        source_row_count=source_row_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        mean_cost_adjusted_edge_probability=_mean(
            tuple(row.cost_adjusted_edge_probability for row in rows),
        ),
        mean_clause_ambiguity_score=_mean(
            tuple(row.clause_ambiguity_score for row in rows),
        ),
        mean_edge_explainability_score=_mean(
            tuple(row.edge_explainability_score for row in rows),
        ),
        min_edge_explainability_score=min(
            (row.edge_explainability_score for row in rows),
            default=ZERO,
        ),
        status=report_status,
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, source_row_count),
        reason_codes=_report_reason_codes(report_status, rows),
    )


def research_strategy_resolution_clause_edge_explainability_report_payload(
    report: ResearchStrategyResolutionClauseEdgeExplainabilityReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is dict:
        _reject_unsafe_public_payload(
            "research_strategy_resolution_clause_edge_explainability_report_payload",
            report,
        )
        _validate_payload_digest(report)
        return report
    if type(report) is not ResearchStrategyResolutionClauseEdgeExplainabilityReport:
        raise ValueError(
            "report must be a ResearchStrategyResolutionClauseEdgeExplainabilityReport",
        )
    _require_report_only_flags("report", report)
    payload = _report_public_payload(report, include_digest=True)
    _reject_unsafe_public_payload(
        "research_strategy_resolution_clause_edge_explainability_report_payload",
        payload,
    )
    _validate_payload_digest(payload)
    return payload


def research_strategy_resolution_clause_edge_explainability_report_digest(
    report: ResearchStrategyResolutionClauseEdgeExplainabilityReport,
) -> str:
    if type(report) is not ResearchStrategyResolutionClauseEdgeExplainabilityReport:
        raise ValueError(
            "report must be a ResearchStrategyResolutionClauseEdgeExplainabilityReport",
        )
    return _payload_digest(_report_public_payload(report, include_digest=False))


def validate_research_strategy_resolution_clause_edge_explainability_report_digest(
    report: ResearchStrategyResolutionClauseEdgeExplainabilityReport,
) -> None:
    if (
        report.derived_validation_digest
        != research_strategy_resolution_clause_edge_explainability_report_digest(report)
    ):
        raise ValueError("derived_validation_digest does not match report payload")


def _row_for_input(
    item: ResearchStrategyResolutionClauseEdgeExplainabilityInput,
    config: ResearchStrategyResolutionClauseEdgeExplainabilityConfig,
) -> ResearchStrategyResolutionClauseEdgeExplainabilityRow:
    if type(item) is not ResearchStrategyResolutionClauseEdgeExplainabilityInput:
        raise ValueError(
            "input must be a ResearchStrategyResolutionClauseEdgeExplainabilityInput",
        )
    _require_report_only_flags("input", item)
    with localcontext(DECIMAL_CONTEXT):
        raw_edge = _normalize_decimal(
            "raw_forecast_edge_probability",
            item.forecast_probability - item.market_probability,
        )
        total_cost = _normalize_probability(
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
        edge_score = _edge_explainability_score(item, total_cost, config)
    status = _row_status(
        adjusted_edge,
        item.clause_ambiguity_score,
        edge_score,
        item.source_confidence_score,
        config,
    )
    return ResearchStrategyResolutionClauseEdgeExplainabilityRow(
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
        clause_ambiguity_score=item.clause_ambiguity_score,
        edge_explanation_quality_score=item.edge_explanation_quality_score,
        source_confidence_score=item.source_confidence_score,
        edge_explainability_score=edge_score,
        status=status,
        reason_codes=_row_reason_codes(
            adjusted_edge,
            item.clause_ambiguity_score,
            edge_score,
            item.source_confidence_score,
            status,
            config,
        ),
    )


def _edge_explainability_score(
    item: ResearchStrategyResolutionClauseEdgeExplainabilityInput,
    total_cost_drag: Decimal,
    config: ResearchStrategyResolutionClauseEdgeExplainabilityConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        clause_clarity_score = ONE - item.clause_ambiguity_score
        cost_stability_score = max(
            ZERO,
            ONE - (total_cost_drag / config.total_cost_drag_watch_ceiling),
        )
        return _normalize_probability(
            "edge_explainability_score",
            clause_clarity_score * config.clause_clarity_weight
            + item.edge_explanation_quality_score * config.edge_quality_weight
            + item.source_confidence_score * config.source_confidence_weight
            + cost_stability_score * config.cost_stability_weight,
        )


def _row_status(
    adjusted_edge: Decimal,
    clause_ambiguity: Decimal,
    edge_score: Decimal,
    source_confidence: Decimal,
    config: ResearchStrategyResolutionClauseEdgeExplainabilityConfig,
) -> str:
    if (
        adjusted_edge < config.cost_adjusted_edge_watch_floor
        or clause_ambiguity > config.clause_ambiguity_watch_ceiling
        or edge_score < config.edge_explainability_watch_floor
        or source_confidence < config.source_confidence_watch_floor
    ):
        return "block"
    if (
        adjusted_edge >= config.cost_adjusted_edge_pass_floor
        and clause_ambiguity <= config.clause_ambiguity_pass_ceiling
        and edge_score >= config.edge_explainability_pass_floor
        and source_confidence >= config.source_confidence_pass_floor
    ):
        return "pass"
    return "watch"


def _row_reason_codes(
    adjusted_edge: Decimal,
    clause_ambiguity: Decimal,
    edge_score: Decimal,
    source_confidence: Decimal,
    status: str,
    config: ResearchStrategyResolutionClauseEdgeExplainabilityConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if adjusted_edge < config.cost_adjusted_edge_watch_floor:
        codes.append("cost_adjusted_edge_block")
    elif adjusted_edge < config.cost_adjusted_edge_pass_floor:
        codes.append("cost_adjusted_edge_watch")
    if clause_ambiguity > config.clause_ambiguity_watch_ceiling:
        codes.append("resolution_clause_ambiguity_block")
    elif clause_ambiguity > config.clause_ambiguity_pass_ceiling:
        codes.append("resolution_clause_ambiguity_watch")
    if edge_score < config.edge_explainability_watch_floor:
        codes.append("edge_explainability_block")
    elif edge_score < config.edge_explainability_pass_floor:
        codes.append("edge_explainability_watch")
    if source_confidence < config.source_confidence_watch_floor:
        codes.append("source_confidence_block")
    elif source_confidence < config.source_confidence_pass_floor:
        codes.append("source_confidence_watch")
    if not codes and status == "pass":
        return ("resolution_clause_edge_explainability_pass",)
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
    rows: tuple[ResearchStrategyResolutionClauseEdgeExplainabilityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("resolution_clause_edge_explainability_report_empty",)
    codes = [f"resolution_clause_edge_explainability_report_{status}"]
    row_reason_codes = {code for row in rows for code in row.reason_codes}
    if any(code.startswith("cost_adjusted_edge_") for code in row_reason_codes):
        codes.append("cost_adjusted_edge_review")
    if any(code.startswith("resolution_clause_ambiguity_") for code in row_reason_codes):
        codes.append("resolution_clause_ambiguity_review")
    if any(code.startswith("edge_explainability_") for code in row_reason_codes):
        codes.append("edge_explainability_review")
    if any(code.startswith("source_confidence_") for code in row_reason_codes):
        codes.append("source_confidence_review")
    return tuple(code for code in codes if code in REPORT_REASON_CODES)


def _reason_code_counts(
    rows: tuple[ResearchStrategyResolutionClauseEdgeExplainabilityRow, ...],
    source_row_count: Decimal,
) -> tuple[ResearchStrategyResolutionClauseEdgeExplainabilityReasonCodeCount, ...]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    if source_row_count == ZERO:
        return ()
    return tuple(
        ResearchStrategyResolutionClauseEdgeExplainabilityReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(count),
            input_ratio=_ratio_decimal(_count_decimal(count), source_row_count),
        )
        for reason_code, count in sorted(counter.items())
    )


def _report_public_payload(
    report: ResearchStrategyResolutionClauseEdgeExplainabilityReport,
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
        "mean_clause_ambiguity_score": _decimal_payload(
            report.mean_clause_ambiguity_score,
        ),
        "mean_edge_explainability_score": _decimal_payload(
            report.mean_edge_explainability_score,
        ),
        "min_edge_explainability_score": _decimal_payload(
            report.min_edge_explainability_score,
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
    row: ResearchStrategyResolutionClauseEdgeExplainabilityRow,
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
        "clause_ambiguity_score": _decimal_payload(row.clause_ambiguity_score),
        "edge_explainability_score": _decimal_payload(row.edge_explainability_score),
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


def _input_digest(item: ResearchStrategyResolutionClauseEdgeExplainabilityInput) -> str:
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
        "clause_ambiguity_score": _decimal_payload(item.clause_ambiguity_score),
        "edge_explanation_quality_score": _decimal_payload(
            item.edge_explanation_quality_score,
        ),
        "source_confidence_score": _decimal_payload(item.source_confidence_score),
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
    rows: tuple[ResearchStrategyResolutionClauseEdgeExplainabilityRow, ...],
) -> tuple[ResearchStrategyResolutionClauseEdgeExplainabilityRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchStrategyResolutionClauseEdgeExplainabilityRow:
            raise ValueError("rows must contain exact row records")
        _require_report_only_flags("row", row)
    return rows


def _normalize_reason_code_counts(
    values: tuple[
        ResearchStrategyResolutionClauseEdgeExplainabilityReasonCodeCount,
        ...,
    ],
) -> tuple[ResearchStrategyResolutionClauseEdgeExplainabilityReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for value in values:
        if type(value) is not ResearchStrategyResolutionClauseEdgeExplainabilityReasonCodeCount:
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
    if type(value) is not str or not value.strip():
        raise ValueError(f"{label} unsafe private string")


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
    "DEFAULT_RESEARCH_STRATEGY_RESOLUTION_CLAUSE_EDGE_EXPLAINABILITY_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_RESOLUTION_CLAUSE_EDGE_EXPLAINABILITY_STATUSES",
    "ResearchStrategyResolutionClauseEdgeExplainabilityConfig",
    "ResearchStrategyResolutionClauseEdgeExplainabilityInput",
    "ResearchStrategyResolutionClauseEdgeExplainabilityReasonCodeCount",
    "ResearchStrategyResolutionClauseEdgeExplainabilityReport",
    "ResearchStrategyResolutionClauseEdgeExplainabilityRow",
    "build_research_strategy_resolution_clause_edge_explainability_report",
    "research_strategy_resolution_clause_edge_explainability_report_digest",
    "research_strategy_resolution_clause_edge_explainability_report_payload",
    "validate_research_strategy_resolution_clause_edge_explainability_report_digest",
)
