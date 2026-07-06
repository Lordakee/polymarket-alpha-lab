"""Pure typed market selection explainability v2 reports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal


__all__ = (
    "MarketSelectionDecisionInputV2",
    "MarketSelectionExplainabilityV2Config",
    "MarketSelectionExplainabilityV2Report",
    "MarketSelectionExplanationV2Row",
    "build_market_selection_explainability_v2_report",
)


ZERO = Decimal("0")
ONE = Decimal("1")
QUANTUM = Decimal("0.000001")
DECISIONS = ("selected", "skipped", "not_selected")
SELECTED_SIDES = ("yes", "no", "none")
READY_REASON_CODE = "market_selection_explainability_v2_ready"


@dataclass(frozen=True)
class MarketSelectionExplainabilityV2Config:
    config_version: str
    low_confidence_threshold: Decimal
    high_resolution_risk_threshold: Decimal
    high_spread_threshold: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "low_confidence_threshold",
            _quantize_score("low_confidence_threshold", self.low_confidence_threshold),
        )
        object.__setattr__(
            self,
            "high_resolution_risk_threshold",
            _quantize_score(
                "high_resolution_risk_threshold",
                self.high_resolution_risk_threshold,
            ),
        )
        object.__setattr__(
            self,
            "high_spread_threshold",
            _quantize_nonnegative_decimal(
                "high_spread_threshold",
                self.high_spread_threshold,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketSelectionDecisionInputV2:
    market_slug: str
    question: str
    screening_status: str
    decision: str
    selected_side: str
    recommendation_score: Decimal
    readiness_score: Decimal
    selection_score: Decimal
    expected_edge_per_share: Decimal | None
    total_cost_per_share: Decimal | None
    liquidity_score: Decimal | None
    confidence: Decimal | None
    spread: Decimal | None
    resolution_risk: Decimal | None
    screening_reason_codes: tuple[str, ...]
    decision_reason_codes: tuple[str, ...]
    evidence_gap_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("question", self.question)
        _require_canonical_string("screening_status", self.screening_status)
        _require_decision("decision", self.decision)
        _require_selected_side("selected_side", self.selected_side)
        object.__setattr__(
            self,
            "recommendation_score",
            _quantize_score("recommendation_score", self.recommendation_score),
        )
        object.__setattr__(
            self,
            "readiness_score",
            _quantize_score("readiness_score", self.readiness_score),
        )
        object.__setattr__(
            self,
            "selection_score",
            _quantize_score("selection_score", self.selection_score),
        )
        object.__setattr__(
            self,
            "expected_edge_per_share",
            _quantize_optional_decimal(
                "expected_edge_per_share",
                self.expected_edge_per_share,
            ),
        )
        object.__setattr__(
            self,
            "total_cost_per_share",
            _quantize_optional_nonnegative_decimal(
                "total_cost_per_share",
                self.total_cost_per_share,
            ),
        )
        object.__setattr__(
            self,
            "liquidity_score",
            _quantize_optional_score("liquidity_score", self.liquidity_score),
        )
        object.__setattr__(
            self,
            "confidence",
            _quantize_optional_score("confidence", self.confidence),
        )
        object.__setattr__(
            self,
            "spread",
            _quantize_optional_nonnegative_decimal("spread", self.spread),
        )
        object.__setattr__(
            self,
            "resolution_risk",
            _quantize_optional_score("resolution_risk", self.resolution_risk),
        )
        object.__setattr__(
            self,
            "screening_reason_codes",
            _normalize_nonempty_reason_codes(
                "screening_reason_codes",
                self.screening_reason_codes,
            ),
        )
        object.__setattr__(
            self,
            "decision_reason_codes",
            _normalize_nonempty_reason_codes(
                "decision_reason_codes",
                self.decision_reason_codes,
            ),
        )
        object.__setattr__(
            self,
            "evidence_gap_codes",
            _normalize_reason_codes("evidence_gap_codes", self.evidence_gap_codes),
        )
        _validate_decision_input_consistency(self)
        _require_hard_flags("decision_input", self)


@dataclass(frozen=True)
class MarketSelectionExplanationV2Row:
    market_slug: str
    question: str
    screening_status: str
    decision: str
    selected_side: str
    explanation_bullets: tuple[str, ...]
    positive_drivers: tuple[str, ...]
    negative_drivers: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    human_review_notes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("question", self.question)
        _require_canonical_string("screening_status", self.screening_status)
        _require_decision("decision", self.decision)
        _require_selected_side("selected_side", self.selected_side)
        object.__setattr__(
            self,
            "explanation_bullets",
            _normalize_nonempty_texts("explanation_bullets", self.explanation_bullets),
        )
        object.__setattr__(
            self,
            "positive_drivers",
            _normalize_texts("positive_drivers", self.positive_drivers),
        )
        object.__setattr__(
            self,
            "negative_drivers",
            _normalize_texts("negative_drivers", self.negative_drivers),
        )
        object.__setattr__(
            self,
            "missing_evidence",
            _normalize_reason_codes("missing_evidence", self.missing_evidence),
        )
        object.__setattr__(
            self,
            "human_review_notes",
            _normalize_texts("human_review_notes", self.human_review_notes),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_nonempty_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("explanation_row", self)


@dataclass(frozen=True)
class MarketSelectionExplainabilityV2Report:
    generated_at: datetime
    config_version: str
    row_count: int
    selected_count: int
    human_review_required_count: int
    explanation_rows: tuple[MarketSelectionExplanationV2Row, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int("row_count", self.row_count)
        _require_nonnegative_int("selected_count", self.selected_count)
        _require_nonnegative_int(
            "human_review_required_count",
            self.human_review_required_count,
        )
        object.__setattr__(
            self,
            "explanation_rows",
            _normalize_explanation_rows(self.explanation_rows),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_nonempty_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report_consistency(self)
        _require_hard_flags("explainability_report", self)


def build_market_selection_explainability_v2_report(
    decision_inputs: tuple[MarketSelectionDecisionInputV2, ...],
    *,
    config: MarketSelectionExplainabilityV2Config,
    generated_at: datetime,
) -> MarketSelectionExplainabilityV2Report:
    if type(config) is not MarketSelectionExplainabilityV2Config:
        raise ValueError("config must be a MarketSelectionExplainabilityV2Config")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    _require_hard_flags("config", config)
    rows = tuple(
        _explanation_row(decision_input, config)
        for decision_input in _normalize_decision_inputs(decision_inputs)
    )
    return MarketSelectionExplainabilityV2Report(
        generated_at=generated_at,
        config_version=config.config_version,
        row_count=len(rows),
        selected_count=_decision_count(rows, "selected"),
        human_review_required_count=sum(
            1 for row in rows if len(row.human_review_notes) > 0
        ),
        explanation_rows=rows,
        reason_codes=(READY_REASON_CODE,),
    )


def _explanation_row(
    decision_input: MarketSelectionDecisionInputV2,
    config: MarketSelectionExplainabilityV2Config,
) -> MarketSelectionExplanationV2Row:
    missing_evidence = _missing_evidence(decision_input)
    return MarketSelectionExplanationV2Row(
        market_slug=decision_input.market_slug,
        question=decision_input.question,
        screening_status=decision_input.screening_status,
        decision=decision_input.decision,
        selected_side=decision_input.selected_side,
        explanation_bullets=_explanation_bullets(decision_input, missing_evidence),
        positive_drivers=_positive_drivers(decision_input, config, missing_evidence),
        negative_drivers=_negative_drivers(decision_input, config),
        missing_evidence=missing_evidence,
        human_review_notes=_human_review_notes(decision_input, config, missing_evidence),
        reason_codes=decision_input.screening_reason_codes
        + decision_input.decision_reason_codes,
    )


def _explanation_bullets(
    decision_input: MarketSelectionDecisionInputV2,
    missing_evidence: tuple[str, ...],
) -> tuple[str, ...]:
    decision_text = (
        f"selected {decision_input.selected_side}"
        if decision_input.decision == "selected"
        else f"decision {decision_input.decision}"
    )
    bullets = [
        "Market "
        f"{decision_input.market_slug} screened {decision_input.screening_status} "
        f"and {decision_text}.",
        "Screening inputs: "
        f"recommendation {_format_decimal(decision_input.recommendation_score)}, "
        f"readiness {_format_decimal(decision_input.readiness_score)}, "
        f"selection {_format_decimal(decision_input.selection_score)}.",
        _economics_bullet(decision_input),
        "Risk inputs: "
        f"confidence {_format_optional_decimal(decision_input.confidence)}, "
        f"liquidity {_format_optional_decimal(decision_input.liquidity_score)}, "
        f"spread {_format_optional_decimal(decision_input.spread)}, "
        "resolution risk "
        f"{_format_optional_decimal(decision_input.resolution_risk)}.",
        f"Screening reasons: {', '.join(decision_input.screening_reason_codes)}.",
        f"Decision reasons: {', '.join(decision_input.decision_reason_codes)}.",
    ]
    if missing_evidence:
        bullets.append(f"Evidence gaps: {', '.join(missing_evidence)}.")
    return tuple(bullets)


def _economics_bullet(decision_input: MarketSelectionDecisionInputV2) -> str:
    if (
        decision_input.expected_edge_per_share is None
        and decision_input.total_cost_per_share is None
    ):
        return "Decision economics: edge unavailable and total cost unavailable."
    if decision_input.expected_edge_per_share is None:
        return (
            "Decision economics: edge unavailable after "
            f"{_format_decimal(decision_input.total_cost_per_share)} total cost."
        )
    if decision_input.total_cost_per_share is None:
        return (
            "Decision economics: edge "
            f"{_format_decimal(decision_input.expected_edge_per_share)} per share "
            "and total cost unavailable."
        )
    return (
        "Decision economics: edge "
        f"{_format_decimal(decision_input.expected_edge_per_share)} per share after "
        f"{_format_decimal(decision_input.total_cost_per_share)} total cost."
    )


def _positive_drivers(
    decision_input: MarketSelectionDecisionInputV2,
    config: MarketSelectionExplainabilityV2Config,
    missing_evidence: tuple[str, ...],
) -> tuple[str, ...]:
    drivers: list[str] = []
    if decision_input.decision == "selected":
        drivers.append(f"Selected {decision_input.selected_side} by decision policy.")
    if (
        decision_input.expected_edge_per_share is not None
        and decision_input.expected_edge_per_share > ZERO
    ):
        drivers.append(
            "Positive expected edge per share: "
            f"{_format_decimal(decision_input.expected_edge_per_share)}.",
        )
    if decision_input.recommendation_score > ZERO:
        drivers.append(
            "Recommendation score "
            f"{_format_decimal(decision_input.recommendation_score)} "
            "supports prioritization.",
        )
    if decision_input.readiness_score > ZERO:
        drivers.append(
            f"Readiness score {_format_decimal(decision_input.readiness_score)} "
            "supports operational readiness.",
        )
    if (
        decision_input.liquidity_score is not None
        and decision_input.liquidity_score > ZERO
    ):
        drivers.append(
            f"Liquidity score {_format_decimal(decision_input.liquidity_score)} "
            "supports execution quality.",
        )
    if (
        decision_input.confidence is not None
        and decision_input.confidence >= config.low_confidence_threshold
    ):
        drivers.append(
            f"Confidence {_format_decimal(decision_input.confidence)} is at or above "
            f"the review threshold {_format_decimal(config.low_confidence_threshold)}.",
        )
    if missing_evidence:
        return ()
    if decision_input.decision != "selected":
        return ()
    return tuple(drivers)


def _negative_drivers(
    decision_input: MarketSelectionDecisionInputV2,
    config: MarketSelectionExplainabilityV2Config,
) -> tuple[str, ...]:
    drivers: list[str] = []
    if decision_input.decision != "selected":
        drivers.append(f"Decision {decision_input.decision} prevented selection.")
    if decision_input.selected_side == "none":
        drivers.append("No selected side is available.")
    if decision_input.expected_edge_per_share is None:
        drivers.append("Expected edge per share is unavailable.")
    elif decision_input.expected_edge_per_share <= ZERO:
        drivers.append(
            "Expected edge per share is not positive: "
            f"{_format_decimal(decision_input.expected_edge_per_share)}.",
        )
    if decision_input.total_cost_per_share is not None:
        drivers.append(
            f"Total cost per share: {_format_decimal(decision_input.total_cost_per_share)}.",
        )
    if decision_input.liquidity_score is None:
        drivers.append("Liquidity score is unavailable.")
    if decision_input.confidence is None:
        drivers.append("Confidence is unavailable.")
    elif decision_input.confidence < config.low_confidence_threshold:
        drivers.append(
            f"Confidence {_format_decimal(decision_input.confidence)} is below the "
            f"review threshold {_format_decimal(config.low_confidence_threshold)}.",
        )
    if decision_input.spread is None:
        drivers.append("Spread is unavailable.")
    elif decision_input.spread > config.high_spread_threshold:
        drivers.append(
            f"Spread {_format_decimal(decision_input.spread)} is above the "
            f"review threshold {_format_decimal(config.high_spread_threshold)}.",
        )
    else:
        drivers.append(f"Spread: {_format_decimal(decision_input.spread)}.")
    if decision_input.resolution_risk is None:
        drivers.append("Resolution risk is unavailable.")
    elif decision_input.resolution_risk > config.high_resolution_risk_threshold:
        drivers.append(
            "Resolution risk "
            f"{_format_decimal(decision_input.resolution_risk)} is above the "
            "review threshold "
            f"{_format_decimal(config.high_resolution_risk_threshold)}.",
        )
    else:
        drivers.append(
            f"Resolution risk: {_format_decimal(decision_input.resolution_risk)}.",
        )
    return tuple(drivers)


def _missing_evidence(
    decision_input: MarketSelectionDecisionInputV2,
) -> tuple[str, ...]:
    gaps = list(decision_input.evidence_gap_codes)
    if decision_input.expected_edge_per_share is None:
        gaps.append("expected_edge_per_share_unavailable")
    if decision_input.liquidity_score is None:
        gaps.append("liquidity_score_unavailable")
    if decision_input.confidence is None:
        gaps.append("confidence_unavailable")
    if decision_input.spread is None:
        gaps.append("spread_unavailable")
    if decision_input.resolution_risk is None:
        gaps.append("resolution_risk_unavailable")
    return tuple(dict.fromkeys(gaps))


def _human_review_notes(
    decision_input: MarketSelectionDecisionInputV2,
    config: MarketSelectionExplainabilityV2Config,
    missing_evidence: tuple[str, ...],
) -> tuple[str, ...]:
    notes: list[str] = []
    if missing_evidence:
        notes.append(
            "Review evidence gaps before promotion: "
            f"{', '.join(missing_evidence)}.",
        )
    if (
        decision_input.confidence is not None
        and decision_input.confidence < config.low_confidence_threshold
    ):
        notes.append(
            "Review low confidence before selection: "
            f"{_format_decimal(decision_input.confidence)}.",
        )
    if (
        decision_input.spread is not None
        and decision_input.spread > config.high_spread_threshold
    ):
        notes.append(
            "Review elevated spread before selection: "
            f"{_format_decimal(decision_input.spread)}.",
        )
    if (
        decision_input.resolution_risk is not None
        and decision_input.resolution_risk > config.high_resolution_risk_threshold
    ):
        notes.append(
            "Review elevated resolution risk before selection: "
            f"{_format_decimal(decision_input.resolution_risk)}.",
        )
    if decision_input.decision != "selected":
        notes.append(
            "Review non-selected decision before any manual override: "
            f"{decision_input.decision}.",
        )
    return tuple(notes)


def _normalize_decision_inputs(
    value: object,
) -> tuple[MarketSelectionDecisionInputV2, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("decision_inputs must be an iterable")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("decision_inputs must be an iterable") from exc
    for row in rows:
        if type(row) is not MarketSelectionDecisionInputV2:
            raise ValueError("decision_inputs must contain MarketSelectionDecisionInputV2 rows")
    return rows


def _normalize_explanation_rows(
    value: object,
) -> tuple[MarketSelectionExplanationV2Row, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("explanation_rows must be an iterable")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("explanation_rows must be an iterable") from exc
    for row in rows:
        if type(row) is not MarketSelectionExplanationV2Row:
            raise ValueError(
                "explanation_rows must contain MarketSelectionExplanationV2Row rows",
            )
    return rows


def _validate_decision_input_consistency(
    decision_input: MarketSelectionDecisionInputV2,
) -> None:
    if decision_input.decision == "selected":
        if decision_input.selected_side == "none":
            raise ValueError("selected rows must have a selected side")
    elif decision_input.selected_side != "none":
        raise ValueError("unselected rows must use selected_side none")


def _validate_report_consistency(report: MarketSelectionExplainabilityV2Report) -> None:
    if report.row_count != len(report.explanation_rows):
        raise ValueError("row_count must match explanation_rows")
    if report.selected_count != _decision_count(report.explanation_rows, "selected"):
        raise ValueError("selected_count must match explanation_rows")
    human_review_required_count = sum(
        1 for row in report.explanation_rows if len(row.human_review_notes) > 0
    )
    if report.human_review_required_count != human_review_required_count:
        raise ValueError("human_review_required_count must match explanation_rows")


def _decision_count(
    rows: tuple[MarketSelectionExplanationV2Row, ...],
    decision: str,
) -> int:
    return sum(1 for row in rows if row.decision == decision)


def _as_utc(value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        raise ValueError("generated_at must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be canonical")


def _require_decision(field_name: str, value: object) -> None:
    if value not in DECISIONS:
        raise ValueError(f"{field_name} must be one of {DECISIONS}")


def _require_selected_side(field_name: str, value: object) -> None:
    if value not in SELECTED_SIDES:
        raise ValueError(f"{field_name} must be one of {SELECTED_SIDES}")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _quantize_decimal(field_name: str, value: Decimal) -> Decimal:
    _require_decimal(field_name, value)
    return value.quantize(QUANTUM)


def _quantize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    _require_nonnegative_decimal(field_name, value)
    return value.quantize(QUANTUM)


def _quantize_score(field_name: str, value: Decimal) -> Decimal:
    score = _quantize_nonnegative_decimal(field_name, value)
    if score > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return score


def _quantize_optional_decimal(
    field_name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    return _quantize_decimal(field_name, value)


def _quantize_optional_nonnegative_decimal(
    field_name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    return _quantize_nonnegative_decimal(field_name, value)


def _quantize_optional_score(
    field_name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    return _quantize_score(field_name, value)


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _normalize_texts(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    for item in items:
        _require_canonical_string(field_name, item)
    return items


def _normalize_nonempty_texts(field_name: str, value: object) -> tuple[str, ...]:
    items = _normalize_texts(field_name, value)
    if not items:
        raise ValueError(f"{field_name} must contain at least one value")
    return items


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    return _normalize_texts(field_name, value)


def _normalize_nonempty_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    items = _normalize_reason_codes(field_name, value)
    if not items:
        raise ValueError(f"{field_name} must contain at least one value")
    return items


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


def _format_optional_decimal(value: Decimal | None) -> str:
    if value is None:
        return "unavailable"
    return _format_decimal(value)


def _format_decimal(value: Decimal) -> str:
    return str(value.quantize(QUANTUM))
