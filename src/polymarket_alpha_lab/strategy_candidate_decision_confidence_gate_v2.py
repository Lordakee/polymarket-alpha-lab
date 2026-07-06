"""Readonly Decimal gate for final candidate decision confidence."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_STRATEGY_CANDIDATE_DECISION_CONFIDENCE_GATE_V2_CONFIG_VERSION = (
    "strategy-candidate-decision-confidence-gate-v2"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

VALIDATION_STATUSES = ("pass", "watch", "blocked")
ROW_STATUS_RANK = {
    "blocked": Decimal("0"),
    "watch": Decimal("1"),
    "pass": Decimal("2"),
}
BENEFIT_SCORE_FIELD_NAMES = (
    "source_verified_edge_score",
    "specialist_signal_confidence",
    "research_readiness_score",
)
RISK_SCORE_FIELD_NAMES = (
    "recommendation_uncertainty_band",
    "liquidity_exit_risk_score",
    "resolution_ambiguity_score",
    "portfolio_impact_score",
)
ROW_REASON_CODES = (
    "decision_confidence_pass",
    "decision_confidence_watch",
    "decision_confidence_blocked",
    "source_verified_edge_strong",
    "source_verified_edge_watch",
    "source_verified_edge_weak",
    "recommendation_uncertainty_tight",
    "recommendation_uncertainty_watch",
    "recommendation_uncertainty_wide",
    "specialist_signal_confidence_strong",
    "specialist_signal_confidence_watch",
    "specialist_signal_confidence_weak",
    "liquidity_exit_risk_low",
    "liquidity_exit_risk_watch",
    "liquidity_exit_risk_high",
    "resolution_ambiguity_low",
    "resolution_ambiguity_watch",
    "resolution_ambiguity_high",
    "portfolio_impact_low",
    "portfolio_impact_watch",
    "portfolio_impact_high",
    "research_readiness_strong",
    "research_readiness_watch",
    "research_readiness_weak",
)
REPORT_REASON_CODES = (
    "decision_confidence_gate_passed",
    "decision_confidence_gate_watch_rows",
    "decision_confidence_gate_blocked_rows",
    "decision_confidence_gate_empty",
)
UNSAFE_PUBLIC_TEXT_FRAGMENTS = tuple(
    "".join(parts)
    for parts in (
        ("li", "ve"),
        ("au", "th"),
        ("wal", "let"),
        ("or", "der"),
        ("net", "work"),
        ("data", "base"),
        ("per", "sist"),
        ("sig", "ning"),
        ("muta", "tion"),
        ("b", "uy"),
        ("se", "ll"),
        ("tra", "de"),
    )
)

__all__ = (
    "DEFAULT_STRATEGY_CANDIDATE_DECISION_CONFIDENCE_GATE_V2_CONFIG_VERSION",
    "StrategyCandidateDecisionConfidenceGateV2Config",
    "StrategyCandidateDecisionConfidenceEvidenceV2",
    "StrategyCandidateDecisionConfidenceGateV2Row",
    "StrategyCandidateDecisionConfidenceGateV2Report",
    "build_strategy_candidate_decision_confidence_gate_v2",
)


@dataclass(frozen=True)
class StrategyCandidateDecisionConfidenceGateV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_CANDIDATE_DECISION_CONFIDENCE_GATE_V2_CONFIG_VERSION
    )
    pass_confidence_floor: Decimal = Decimal("0.850000")
    watch_confidence_floor: Decimal = Decimal("0.700000")
    critical_dimension_floor: Decimal = Decimal("0.650000")
    max_pass_uncertainty_band: Decimal = Decimal("0.060000")
    max_watch_uncertainty_band: Decimal = Decimal("0.120000")
    max_pass_risk_score: Decimal = Decimal("0.150000")
    max_watch_risk_score: Decimal = Decimal("0.350000")
    source_verified_edge_weight: Decimal = Decimal("0.250000")
    recommendation_uncertainty_weight: Decimal = Decimal("0.150000")
    specialist_signal_confidence_weight: Decimal = Decimal("0.200000")
    liquidity_exit_risk_weight: Decimal = Decimal("0.120000")
    resolution_ambiguity_weight: Decimal = Decimal("0.100000")
    portfolio_impact_weight: Decimal = Decimal("0.080000")
    research_readiness_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_non_empty_string("config_version", self.config_version),
        )
        for field_name in (
            "pass_confidence_floor",
            "watch_confidence_floor",
            "critical_dimension_floor",
            "max_pass_uncertainty_band",
            "max_watch_uncertainty_band",
            "max_pass_risk_score",
            "max_watch_risk_score",
            "source_verified_edge_weight",
            "recommendation_uncertainty_weight",
            "specialist_signal_confidence_weight",
            "liquidity_exit_risk_weight",
            "resolution_ambiguity_weight",
            "portfolio_impact_weight",
            "research_readiness_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("StrategyCandidateDecisionConfidenceGateV2Config", self)
        _reject_unsafe_public_payload(
            "StrategyCandidateDecisionConfidenceGateV2Config",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class StrategyCandidateDecisionConfidenceEvidenceV2:
    candidate_id: str
    market_slug: str
    event_id: str
    source_verified_edge_score: Decimal
    recommendation_uncertainty_band: Decimal
    specialist_signal_confidence: Decimal
    liquidity_exit_risk_score: Decimal
    resolution_ambiguity_score: Decimal
    portfolio_impact_score: Decimal
    research_readiness_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("candidate_id", "market_slug", "event_id"):
            object.__setattr__(
                self,
                field_name,
                _require_non_empty_string(field_name, getattr(self, field_name)),
            )
        for field_name in (*BENEFIT_SCORE_FIELD_NAMES, *RISK_SCORE_FIELD_NAMES):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("StrategyCandidateDecisionConfidenceEvidenceV2", self)
        _reject_unsafe_public_payload(
            "StrategyCandidateDecisionConfidenceEvidenceV2",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class StrategyCandidateDecisionConfidenceGateV2Row:
    candidate_id: str
    market_slug: str
    event_id: str
    source_verified_edge_score: Decimal
    recommendation_uncertainty_band: Decimal
    recommendation_uncertainty_confidence_score: Decimal
    specialist_signal_confidence: Decimal
    liquidity_exit_risk_score: Decimal
    liquidity_exit_confidence_score: Decimal
    resolution_ambiguity_score: Decimal
    resolution_clarity_score: Decimal
    portfolio_impact_score: Decimal
    portfolio_confidence_score: Decimal
    research_readiness_score: Decimal
    confidence_score: Decimal
    validation_status: str
    final_decision_blocked: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _reject_unsafe_public_payload(
            "StrategyCandidateDecisionConfidenceGateV2Row.raw",
            {"reason_codes": self.reason_codes},
        )
        for field_name in ("candidate_id", "market_slug", "event_id"):
            object.__setattr__(
                self,
                field_name,
                _require_non_empty_string(field_name, getattr(self, field_name)),
            )
        for field_name in (
            *BENEFIT_SCORE_FIELD_NAMES,
            *RISK_SCORE_FIELD_NAMES,
            "recommendation_uncertainty_confidence_score",
            "liquidity_exit_confidence_score",
            "resolution_clarity_score",
            "portfolio_confidence_score",
            "confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("validation_status", self.validation_status)
        _require_bool("final_decision_blocked", self.final_decision_blocked)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("StrategyCandidateDecisionConfidenceGateV2Row", self)
        _reject_unsafe_public_payload(
            "StrategyCandidateDecisionConfidenceGateV2Row",
            _payload_value(asdict(self)),
        )
        _validate_row_consistency(self)


@dataclass(frozen=True)
class StrategyCandidateDecisionConfidenceGateV2Report:
    generated_at: datetime
    config_version: str
    gate_status: str
    final_decision_blocked: bool
    candidate_count: Decimal
    pass_candidate_count: Decimal
    watch_candidate_count: Decimal
    blocked_candidate_count: Decimal
    average_confidence_score: Decimal
    top_confidence_score: Decimal
    bottom_confidence_score: Decimal
    rows: tuple[StrategyCandidateDecisionConfidenceGateV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_non_empty_string("config_version", self.config_version),
        )
        _require_status("gate_status", self.gate_status)
        _require_bool("final_decision_blocked", self.final_decision_blocked)
        for field_name in (
            "candidate_count",
            "pass_candidate_count",
            "watch_candidate_count",
            "blocked_candidate_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "average_confidence_score",
            "top_confidence_score",
            "bottom_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _require_sha256_digest(
            "derived_validation_digest",
            self.derived_validation_digest,
        )
        _require_hard_flags("StrategyCandidateDecisionConfidenceGateV2Report", self)
        _reject_unsafe_public_payload(
            "StrategyCandidateDecisionConfidenceGateV2Report",
            _payload_value(asdict(self)),
        )
        _validate_report_shape(self)
        _validate_report_digest(self)
        _validate_report_summary(self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload(
            "StrategyCandidateDecisionConfidenceGateV2Report.payload",
            payload,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_strategy_candidate_decision_confidence_gate_v2(
    candidate_confidence_evidence: object,
    *,
    config: StrategyCandidateDecisionConfidenceGateV2Config | None = None,
    generated_at: datetime,
) -> StrategyCandidateDecisionConfidenceGateV2Report:
    if config is None:
        config = StrategyCandidateDecisionConfidenceGateV2Config()
    if type(config) is not StrategyCandidateDecisionConfidenceGateV2Config:
        raise ValueError(
            "config must be a StrategyCandidateDecisionConfidenceGateV2Config",
        )
    _require_hard_flags("StrategyCandidateDecisionConfidenceGateV2Config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    evidence_items = _normalize_evidence_items(candidate_confidence_evidence)
    rows = tuple(
        sorted(
            (_row_for_evidence(item, config) for item in evidence_items),
            key=_row_sort_key,
        ),
    )
    status = _gate_status(rows)
    values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "gate_status": status,
        "final_decision_blocked": status != "pass",
        "candidate_count": Decimal(len(rows)).quantize(COUNT_QUANT),
        "pass_candidate_count": _status_count(rows, "pass"),
        "watch_candidate_count": _status_count(rows, "watch"),
        "blocked_candidate_count": _status_count(rows, "blocked"),
        "average_confidence_score": _average_score(rows),
        "top_confidence_score": _top_score(rows),
        "bottom_confidence_score": _bottom_score(rows),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows, status),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _derived_validation_digest(values)
    return StrategyCandidateDecisionConfidenceGateV2Report(**values)


def _row_for_evidence(
    item: StrategyCandidateDecisionConfidenceEvidenceV2,
    config: StrategyCandidateDecisionConfidenceGateV2Config,
) -> StrategyCandidateDecisionConfidenceGateV2Row:
    recommendation_confidence = _inverse_score(item.recommendation_uncertainty_band)
    liquidity_confidence = _inverse_score(item.liquidity_exit_risk_score)
    resolution_clarity = _inverse_score(item.resolution_ambiguity_score)
    portfolio_confidence = _inverse_score(item.portfolio_impact_score)
    score = _confidence_score(
        item,
        config,
        recommendation_confidence=recommendation_confidence,
        liquidity_confidence=liquidity_confidence,
        resolution_clarity=resolution_clarity,
        portfolio_confidence=portfolio_confidence,
    )
    status = _validation_status(item, score, config)
    return StrategyCandidateDecisionConfidenceGateV2Row(
        candidate_id=item.candidate_id,
        market_slug=item.market_slug,
        event_id=item.event_id,
        source_verified_edge_score=item.source_verified_edge_score,
        recommendation_uncertainty_band=item.recommendation_uncertainty_band,
        recommendation_uncertainty_confidence_score=recommendation_confidence,
        specialist_signal_confidence=item.specialist_signal_confidence,
        liquidity_exit_risk_score=item.liquidity_exit_risk_score,
        liquidity_exit_confidence_score=liquidity_confidence,
        resolution_ambiguity_score=item.resolution_ambiguity_score,
        resolution_clarity_score=resolution_clarity,
        portfolio_impact_score=item.portfolio_impact_score,
        portfolio_confidence_score=portfolio_confidence,
        research_readiness_score=item.research_readiness_score,
        confidence_score=score,
        validation_status=status,
        final_decision_blocked=status != "pass",
        reason_codes=_row_reason_codes(item, status, config),
    )


def _confidence_score(
    item: StrategyCandidateDecisionConfidenceEvidenceV2,
    config: StrategyCandidateDecisionConfidenceGateV2Config,
    *,
    recommendation_confidence: Decimal,
    liquidity_confidence: Decimal,
    resolution_clarity: Decimal,
    portfolio_confidence: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            item.source_verified_edge_score * config.source_verified_edge_weight
            + recommendation_confidence * config.recommendation_uncertainty_weight
            + item.specialist_signal_confidence * config.specialist_signal_confidence_weight
            + liquidity_confidence * config.liquidity_exit_risk_weight
            + resolution_clarity * config.resolution_ambiguity_weight
            + portfolio_confidence * config.portfolio_impact_weight
            + item.research_readiness_score * config.research_readiness_weight
        )
        return _clamp_ratio(score)


def _inverse_score(value: Decimal) -> Decimal:
    return _clamp_ratio(ONE - value)


def _validation_status(
    item: StrategyCandidateDecisionConfidenceEvidenceV2,
    score: Decimal,
    config: StrategyCandidateDecisionConfidenceGateV2Config,
) -> str:
    if _has_critical_dimension(item, config):
        return "blocked"
    if (
        score >= config.pass_confidence_floor
        and item.source_verified_edge_score >= config.pass_confidence_floor
        and item.specialist_signal_confidence >= config.pass_confidence_floor
        and item.research_readiness_score >= config.pass_confidence_floor
        and item.recommendation_uncertainty_band <= config.max_pass_uncertainty_band
        and item.liquidity_exit_risk_score <= config.max_pass_risk_score
        and item.resolution_ambiguity_score <= config.max_pass_risk_score
        and item.portfolio_impact_score <= config.max_pass_risk_score
    ):
        return "pass"
    if score >= config.watch_confidence_floor:
        return "watch"
    return "blocked"


def _has_critical_dimension(
    item: StrategyCandidateDecisionConfidenceEvidenceV2,
    config: StrategyCandidateDecisionConfidenceGateV2Config,
) -> bool:
    return (
        item.source_verified_edge_score < config.critical_dimension_floor
        or item.specialist_signal_confidence < config.critical_dimension_floor
        or item.research_readiness_score < config.critical_dimension_floor
        or item.recommendation_uncertainty_band > config.max_watch_uncertainty_band
        or item.liquidity_exit_risk_score > config.max_watch_risk_score
        or item.resolution_ambiguity_score > config.max_watch_risk_score
        or item.portfolio_impact_score > config.max_watch_risk_score
    )


def _row_reason_codes(
    item: StrategyCandidateDecisionConfidenceEvidenceV2,
    status: str,
    config: StrategyCandidateDecisionConfidenceGateV2Config,
) -> tuple[str, ...]:
    return (
        f"decision_confidence_{status}",
        _benefit_tier_reason(
            item.source_verified_edge_score,
            "source_verified_edge",
            config,
        ),
        _recommendation_uncertainty_reason(item.recommendation_uncertainty_band, config),
        _benefit_tier_reason(
            item.specialist_signal_confidence,
            "specialist_signal_confidence",
            config,
        ),
        _risk_tier_reason(item.liquidity_exit_risk_score, "liquidity_exit_risk", config),
        _risk_tier_reason(item.resolution_ambiguity_score, "resolution_ambiguity", config),
        _risk_tier_reason(item.portfolio_impact_score, "portfolio_impact", config),
        _benefit_tier_reason(
            item.research_readiness_score,
            "research_readiness",
            config,
        ),
    )


def _benefit_tier_reason(
    value: Decimal,
    prefix: str,
    config: StrategyCandidateDecisionConfidenceGateV2Config,
) -> str:
    if value >= config.pass_confidence_floor:
        return f"{prefix}_strong"
    if value >= config.critical_dimension_floor:
        return f"{prefix}_watch"
    return f"{prefix}_weak"


def _recommendation_uncertainty_reason(
    value: Decimal,
    config: StrategyCandidateDecisionConfidenceGateV2Config,
) -> str:
    if value <= config.max_pass_uncertainty_band:
        return "recommendation_uncertainty_tight"
    if value <= config.max_watch_uncertainty_band:
        return "recommendation_uncertainty_watch"
    return "recommendation_uncertainty_wide"


def _risk_tier_reason(
    value: Decimal,
    prefix: str,
    config: StrategyCandidateDecisionConfidenceGateV2Config,
) -> str:
    if value <= config.max_pass_risk_score:
        return f"{prefix}_low"
    if value <= config.max_watch_risk_score:
        return f"{prefix}_watch"
    return f"{prefix}_high"


def _gate_status(
    rows: tuple[StrategyCandidateDecisionConfidenceGateV2Row, ...],
) -> str:
    if not rows:
        return "blocked"
    if any(row.validation_status == "blocked" for row in rows):
        return "blocked"
    if any(row.validation_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[StrategyCandidateDecisionConfidenceGateV2Row, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("decision_confidence_gate_empty",)
    if status == "pass":
        return ("decision_confidence_gate_passed",)
    reasons: list[str] = []
    if any(row.validation_status == "watch" for row in rows):
        reasons.append("decision_confidence_gate_watch_rows")
    if any(row.validation_status == "blocked" for row in rows):
        reasons.append("decision_confidence_gate_blocked_rows")
    return tuple(reasons)


def _status_count(
    rows: tuple[StrategyCandidateDecisionConfidenceGateV2Row, ...],
    status: str,
) -> Decimal:
    return Decimal(sum(1 for row in rows if row.validation_status == status)).quantize(
        COUNT_QUANT,
    )


def _average_score(rows: tuple[StrategyCandidateDecisionConfidenceGateV2Row, ...]) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            sum((row.confidence_score for row in rows), ZERO) / Decimal(len(rows)),
        )


def _top_score(rows: tuple[StrategyCandidateDecisionConfidenceGateV2Row, ...]) -> Decimal:
    if not rows:
        return ZERO
    return max(row.confidence_score for row in rows)


def _bottom_score(rows: tuple[StrategyCandidateDecisionConfidenceGateV2Row, ...]) -> Decimal:
    if not rows:
        return ZERO
    return min(row.confidence_score for row in rows)


def _row_sort_key(
    row: StrategyCandidateDecisionConfidenceGateV2Row,
) -> tuple[Decimal, str, str, str]:
    return (ROW_STATUS_RANK[row.validation_status], row.candidate_id, row.market_slug, row.event_id)


def _normalize_evidence_items(
    candidate_confidence_evidence: object,
) -> tuple[StrategyCandidateDecisionConfidenceEvidenceV2, ...]:
    if isinstance(candidate_confidence_evidence, (str, bytes)):
        raise ValueError("candidate confidence evidence must be an iterable")
    try:
        items = tuple(candidate_confidence_evidence)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("candidate confidence evidence must be an iterable") from exc
    for item in items:
        if type(item) is not StrategyCandidateDecisionConfidenceEvidenceV2:
            raise ValueError(
                "candidate confidence evidence items must be "
                "StrategyCandidateDecisionConfidenceEvidenceV2",
            )
    seen: set[tuple[str, str, str]] = set()
    for item in items:
        key = (item.candidate_id, item.market_slug, item.event_id)
        if key in seen:
            raise ValueError("duplicate candidate_id, market_slug, and event_id")
        seen.add(key)
    return items


def _normalize_rows(rows: object) -> tuple[StrategyCandidateDecisionConfidenceGateV2Row, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not StrategyCandidateDecisionConfidenceGateV2Row:
            raise ValueError(
                "rows must contain StrategyCandidateDecisionConfidenceGateV2Row",
            )
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted by status and candidate_id")
    return normalized


def _normalize_reason_codes(
    field_name: str,
    values: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        normalized = tuple(values)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    for value in normalized:
        _require_non_empty_string(field_name, value)
    _reject_unsafe_public_payload(field_name, normalized)
    for value in normalized:
        if value not in allowed:
            raise ValueError(f"{field_name} contains an unsupported reason code")
    return normalized


def _validate_config(config: StrategyCandidateDecisionConfidenceGateV2Config) -> None:
    if config.watch_confidence_floor > config.pass_confidence_floor:
        raise ValueError("watch_confidence_floor must not exceed pass_confidence_floor")
    if config.critical_dimension_floor > config.watch_confidence_floor:
        raise ValueError("critical_dimension_floor must not exceed watch_confidence_floor")
    if config.max_pass_uncertainty_band > config.max_watch_uncertainty_band:
        raise ValueError("max_pass_uncertainty_band must not exceed max_watch_uncertainty_band")
    if config.max_pass_risk_score > config.max_watch_risk_score:
        raise ValueError("max_pass_risk_score must not exceed max_watch_risk_score")
    total = (
        config.source_verified_edge_weight
        + config.recommendation_uncertainty_weight
        + config.specialist_signal_confidence_weight
        + config.liquidity_exit_risk_weight
        + config.resolution_ambiguity_weight
        + config.portfolio_impact_weight
        + config.research_readiness_weight
    )
    with localcontext(DECIMAL_CONTEXT):
        if total.quantize(SCORE_QUANT) != ONE:
            raise ValueError("score weights must sum to 1.000000")


def _validate_row_consistency(row: StrategyCandidateDecisionConfidenceGateV2Row) -> None:
    if row.recommendation_uncertainty_confidence_score != _inverse_score(
        row.recommendation_uncertainty_band,
    ):
        raise ValueError("recommendation_uncertainty_confidence_score must match band")
    if row.liquidity_exit_confidence_score != _inverse_score(row.liquidity_exit_risk_score):
        raise ValueError("liquidity_exit_confidence_score must match risk score")
    if row.resolution_clarity_score != _inverse_score(row.resolution_ambiguity_score):
        raise ValueError("resolution_clarity_score must match ambiguity score")
    if row.portfolio_confidence_score != _inverse_score(row.portfolio_impact_score):
        raise ValueError("portfolio_confidence_score must match impact score")
    if row.final_decision_blocked is not (row.validation_status != "pass"):
        raise ValueError("final_decision_blocked must match validation_status")
    if not row.reason_codes or row.reason_codes[0] != f"decision_confidence_{row.validation_status}":
        raise ValueError("reason_codes must match validation_status")


def _validate_report_shape(report: StrategyCandidateDecisionConfidenceGateV2Report) -> None:
    if report.candidate_count != Decimal(len(report.rows)).quantize(COUNT_QUANT):
        raise ValueError("candidate_count must match rows")
    if (
        report.pass_candidate_count != _status_count(report.rows, "pass")
        or report.watch_candidate_count != _status_count(report.rows, "watch")
        or report.blocked_candidate_count != _status_count(report.rows, "blocked")
    ):
        raise ValueError("status counts must match rows")
    expected_status = _gate_status(report.rows)
    if report.gate_status != expected_status:
        raise ValueError("gate_status must match rows")
    if report.final_decision_blocked is not (report.gate_status != "pass"):
        raise ValueError("final_decision_blocked must match gate_status")
    if report.reason_codes != _report_reason_codes(report.rows, report.gate_status):
        raise ValueError("reason_codes must match gate_status")


def _validate_report_summary(report: StrategyCandidateDecisionConfidenceGateV2Report) -> None:
    if report.average_confidence_score != _average_score(report.rows):
        raise ValueError("average_confidence_score must match rows")
    if report.top_confidence_score != _top_score(report.rows):
        raise ValueError("top_confidence_score must match rows")
    if report.bottom_confidence_score != _bottom_score(report.rows):
        raise ValueError("bottom_confidence_score must match rows")


def _validate_report_digest(report: StrategyCandidateDecisionConfidenceGateV2Report) -> None:
    if report.derived_validation_digest != _derived_validation_digest(
        _report_digest_fields(report),
    ):
        raise ValueError("derived_validation_digest must match report fields")


def _report_digest_fields(report: StrategyCandidateDecisionConfidenceGateV2Report) -> dict[str, object]:
    return {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "gate_status": report.gate_status,
        "final_decision_blocked": report.final_decision_blocked,
        "candidate_count": report.candidate_count,
        "pass_candidate_count": report.pass_candidate_count,
        "watch_candidate_count": report.watch_candidate_count,
        "blocked_candidate_count": report.blocked_candidate_count,
        "average_confidence_score": report.average_confidence_score,
        "top_confidence_score": report.top_confidence_score,
        "bottom_confidence_score": report.bottom_confidence_score,
        "rows": report.rows,
        "reason_codes": report.reason_codes,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _derived_validation_digest(values: dict[str, object]) -> str:
    digest_values = dict(values)
    digest_values.pop("derived_validation_digest", None)
    ready = _payload_value(digest_values)
    _reject_unsafe_public_payload("derived validation digest fields", ready)
    encoded = json.dumps(
        ready,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _payload_value(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal values must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) is float or type(value) is int:
        raise ValueError("payload values must use Decimal strings")
    if type(value) in (str, bool):
        return value
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            ready[key] = _payload_value(item)
        return ready
    if type(value) in (list, tuple):
        return [_payload_value(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    for text in _iter_public_text(payload):
        lowered = text.lower()
        if any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
            raise ValueError(f"unsafe public payload in {label}")


def _iter_public_text(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_public_text(asdict(value))
    if type(value) is dict:
        text_values: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            text_values.append(key)
            text_values.extend(_iter_public_text(item))
        return tuple(text_values)
    if type(value) in (list, tuple):
        text_values = []
        for item in value:
            text_values.extend(_iter_public_text(item))
        return tuple(text_values)
    if type(value) is str:
        return (value,)
    return ()


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(SCORE_QUANT)
    if value != quantized:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(COUNT_QUANT)
    if value != quantized:
        raise ValueError(f"{field_name} must be an integral Decimal")
    return quantized


def _clamp_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        if value < ZERO:
            value = ZERO
        if value > ONE:
            value = ONE
        return value.quantize(SCORE_QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_non_empty_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_unsafe_public_payload(field_name, value)
    return value


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in VALIDATION_STATUSES:
        raise ValueError(f"{field_name} must be one of {VALIDATION_STATUSES!r}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
