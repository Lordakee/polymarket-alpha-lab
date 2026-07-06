"""Paper-only adapter from research queue rows to decision matrix inputs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.strategy_candidate_decision_matrix import (
    PaperStrategyCandidateDecisionInput,
)
from polymarket_alpha_lab.strategy_candidate_research_queue import (
    PaperStrategyCandidateResearchQueueReport,
    PaperStrategyCandidateResearchQueueRow,
)


__all__ = (
    "PaperStrategyCandidateDecisionResearchQueueSupplement",
    "PaperStrategyCandidateDecisionResearchQueueSupplementRow",
    "paper_strategy_candidate_decision_inputs_from_research_queue",
)


ZERO = Decimal("0")
ONE = Decimal("1")
QUANTUM = Decimal("0.000001")
ADAPTER_REASON_CODE = "decision_matrix_research_queue_adapter"


@dataclass(frozen=True)
class PaperStrategyCandidateDecisionResearchQueueSupplementRow:
    market_slug: str
    question: str
    selected_side: str
    team_id: str
    category: str
    forecast_probability: Decimal
    market_probability: Decimal
    liquidity_score: Decimal
    information_quality_score: Decimal
    source_count: Decimal
    freshness_minutes: Decimal
    resolution_risk_score: Decimal
    team_memory_score: Decimal
    calibration_score: Decimal
    reason_codes: tuple[str, ...] = ()
    evidence_gap_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "PaperStrategyCandidateDecisionResearchQueueSupplementRow "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not PaperStrategyCandidateDecisionResearchQueueSupplementRow:
            raise ValueError("supplement row must be exactly the supplement row type")
        for field_name in ("market_slug", "question", "team_id", "category"):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_side("selected_side", self.selected_side)
        for field_name in (
            "forecast_probability",
            "market_probability",
            "liquidity_score",
            "information_quality_score",
            "resolution_risk_score",
            "team_memory_score",
            "calibration_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("source_count", "freshness_minutes"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "evidence_gap_codes",
            _normalize_reason_codes("evidence_gap_codes", self.evidence_gap_codes),
        )
        _require_hard_flags("supplement row", self)


@dataclass(frozen=True)
class PaperStrategyCandidateDecisionResearchQueueSupplement:
    generated_at: datetime
    config_version: str
    source_queue_config_version: str
    rows: tuple[PaperStrategyCandidateDecisionResearchQueueSupplementRow, ...]
    reason_codes: tuple[str, ...] = ("decision_matrix_research_queue_supplement",)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "PaperStrategyCandidateDecisionResearchQueueSupplement "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not PaperStrategyCandidateDecisionResearchQueueSupplement:
            raise ValueError("supplement must be exactly the supplement type")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string(
            "source_queue_config_version",
            self.source_queue_config_version,
        )
        object.__setattr__(self, "rows", _normalize_supplement_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if not self.reason_codes:
            raise ValueError("supplement reason_codes must be nonempty")
        _require_hard_flags("supplement", self)


def paper_strategy_candidate_decision_inputs_from_research_queue(
    source_report: object,
    *,
    supplement: object,
) -> tuple[PaperStrategyCandidateDecisionInput, ...]:
    if type(source_report) is not PaperStrategyCandidateResearchQueueReport:
        raise ValueError("source_report must be exactly PaperStrategyCandidateResearchQueueReport")
    if type(supplement) is not PaperStrategyCandidateDecisionResearchQueueSupplement:
        raise ValueError(
            "supplement must be exactly "
            "PaperStrategyCandidateDecisionResearchQueueSupplement",
        )
    _require_hard_flags("source_report", source_report)
    _require_hard_flags("supplement", supplement)
    if supplement.source_queue_config_version != source_report.config_version:
        raise ValueError("source_queue_config_version must match source report config_version")

    source_rows_by_slug = _source_rows_by_market_slug(source_report.rows)
    supplement_rows_by_slug = _supplement_rows_by_market_slug(supplement.rows)
    _validate_slug_coverage(
        source_market_slugs=tuple(source_rows_by_slug),
        supplement_market_slugs=tuple(supplement_rows_by_slug),
    )

    return tuple(
        _decision_input_from_rows(
            source_row=source_row,
            supplement_row=supplement_rows_by_slug[source_row.market_slug],
            supplement=supplement,
        )
        for source_row in source_report.rows
    )


def _decision_input_from_rows(
    *,
    source_row: PaperStrategyCandidateResearchQueueRow,
    supplement_row: PaperStrategyCandidateDecisionResearchQueueSupplementRow,
    supplement: PaperStrategyCandidateDecisionResearchQueueSupplement,
) -> PaperStrategyCandidateDecisionInput:
    _validate_row_identity(source_row, supplement_row)
    net_edge_per_share = _required_decimal(
        "net_edge_per_share",
        source_row.net_edge_per_share,
    )
    total_cost_per_share = _required_nonnegative_decimal(
        "total_cost_per_share",
        source_row.total_cost_per_share,
    )
    forecast_edge = _q(supplement_row.forecast_probability - supplement_row.market_probability)
    if forecast_edge != net_edge_per_share:
        raise ValueError("forecast edge must match net_edge_per_share")
    if source_row.resolution_risk is not None:
        source_resolution_risk = _normalize_nonnegative_decimal(
            "resolution_risk",
            source_row.resolution_risk,
        )
        if source_resolution_risk != supplement_row.resolution_risk_score:
            raise ValueError("resolution_risk_score must match source row resolution_risk")

    return PaperStrategyCandidateDecisionInput(
        market_slug=source_row.market_slug,
        question=source_row.question,
        team_id=supplement_row.team_id,
        category=supplement_row.category,
        forecast_probability=supplement_row.forecast_probability,
        market_probability=supplement_row.market_probability,
        net_edge_per_share=net_edge_per_share,
        total_cost_per_share=total_cost_per_share,
        liquidity_score=supplement_row.liquidity_score,
        information_quality_score=supplement_row.information_quality_score,
        source_count=supplement_row.source_count,
        freshness_minutes=supplement_row.freshness_minutes,
        resolution_risk_score=supplement_row.resolution_risk_score,
        team_memory_score=supplement_row.team_memory_score,
        calibration_score=supplement_row.calibration_score,
        reason_codes=(
            ADAPTER_REASON_CODE,
            *supplement.reason_codes,
            *source_row.reason_codes,
            *supplement_row.reason_codes,
        ),
        evidence_gap_codes=(
            *source_row.evidence_gap_codes,
            *supplement_row.evidence_gap_codes,
        ),
    )


def _validate_row_identity(
    source_row: PaperStrategyCandidateResearchQueueRow,
    supplement_row: PaperStrategyCandidateDecisionResearchQueueSupplementRow,
) -> None:
    if supplement_row.question != source_row.question:
        raise ValueError("question must match source row")
    if supplement_row.selected_side != source_row.selected_side:
        raise ValueError("selected_side must match source row")
    if supplement_row.category != source_row.research_bucket:
        raise ValueError("category must match source row research_bucket")
    if supplement_row.selected_side == "none":
        raise ValueError("selected_side must be yes or no")


def _source_rows_by_market_slug(
    rows: tuple[PaperStrategyCandidateResearchQueueRow, ...],
) -> dict[str, PaperStrategyCandidateResearchQueueRow]:
    result: dict[str, PaperStrategyCandidateResearchQueueRow] = {}
    for row in rows:
        if type(row) is not PaperStrategyCandidateResearchQueueRow:
            raise ValueError("source report rows must be exact research queue rows")
        _require_hard_flags("source row", row)
        if row.market_slug in result:
            raise ValueError("source report must not contain duplicate market_slug values")
        result[row.market_slug] = row
    return result


def _supplement_rows_by_market_slug(
    rows: tuple[PaperStrategyCandidateDecisionResearchQueueSupplementRow, ...],
) -> dict[str, PaperStrategyCandidateDecisionResearchQueueSupplementRow]:
    result: dict[str, PaperStrategyCandidateDecisionResearchQueueSupplementRow] = {}
    for row in rows:
        if type(row) is not PaperStrategyCandidateDecisionResearchQueueSupplementRow:
            raise ValueError("supplement rows must be exact supplement row values")
        _require_hard_flags("supplement row", row)
        if row.market_slug in result:
            raise ValueError("supplement must not contain duplicate market_slug values")
        result[row.market_slug] = row
    return result


def _validate_slug_coverage(
    *,
    source_market_slugs: tuple[str, ...],
    supplement_market_slugs: tuple[str, ...],
) -> None:
    source = set(source_market_slugs)
    supplement = set(supplement_market_slugs)
    if source - supplement:
        raise ValueError("supplement missing market_slug coverage")
    if supplement - source:
        raise ValueError("supplement has extra market_slug coverage")


def _normalize_supplement_rows(
    rows: object,
) -> tuple[PaperStrategyCandidateDecisionResearchQueueSupplementRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple of supplement row values")
    for row in rows:
        if type(row) is not PaperStrategyCandidateDecisionResearchQueueSupplementRow:
            raise ValueError("rows must contain exact supplement row values")
        _require_hard_flags("supplement row", row)
    return rows


def _required_decimal(field_name: str, value: object) -> Decimal:
    if value is None:
        raise ValueError(f"{field_name} is required")
    return _normalize_nonnegative_decimal(field_name, value)


def _required_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if value is None:
        raise ValueError(f"{field_name} is required")
    return _normalize_nonnegative_decimal(field_name, value)


def _normalize_reason_codes(field_name: str, values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple of strings")
    for value in values:
        _require_canonical_string(field_name, value)
    return tuple(sorted(dict.fromkeys(values)))


def _require_side(field_name: str, value: object) -> None:
    if value not in ("yes", "no"):
        raise ValueError(f"{field_name} must be yes or no")


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
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
    return _q(value)


def _q(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must be nonempty")
    if value != value.strip():
        raise ValueError(f"{field_name} must be canonical")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} must be readonly")
