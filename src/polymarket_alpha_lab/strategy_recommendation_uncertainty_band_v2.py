"""Phase 1 paper-only uncertainty bands for candidate strategy recommendations."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, localcontext
import hashlib
import json
from typing import Any


DECIMAL_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SIDES = ("yes", "no")
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
REPORT_STATUSES = ("paper_recommendable", "paper_watch", "paper_reject")
EDGE_STATUSES = ("edge_pass", "edge_reject")
WIDTH_STATUSES = ("width_pass", "width_watch")
CONFIDENCE_STATUSES = ("confidence_pass", "confidence_watch")
LOCKUP_STATUSES = ("lockup_pass", "lockup_watch")
UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
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
)


@dataclass(frozen=True)
class StrategyRecommendationUncertaintyBandV2Config:
    config_version: str
    min_uncertainty_adjusted_edge: Decimal
    max_uncertainty_width: Decimal
    min_confidence: Decimal
    max_capital_lockup_ratio: Decimal
    forecast_dispersion_weight: Decimal
    source_reliability_weight: Decimal
    evidence_freshness_weight: Decimal
    contradiction_severity_weight: Decimal
    liquidity_exit_risk_weight: Decimal
    resolution_risk_weight: Decimal
    specialist_quorum_weight: Decimal
    capital_lockup_weight: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_public_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_uncertainty_adjusted_edge",
            _normalize_decimal(
                "min_uncertainty_adjusted_edge",
                self.min_uncertainty_adjusted_edge,
            ),
        )
        for field_name in (
            "max_uncertainty_width",
            "min_confidence",
            "max_capital_lockup_ratio",
            "forecast_dispersion_weight",
            "source_reliability_weight",
            "evidence_freshness_weight",
            "contradiction_severity_weight",
            "liquidity_exit_risk_weight",
            "resolution_risk_weight",
            "specialist_quorum_weight",
            "capital_lockup_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags(self)


@dataclass(frozen=True)
class CandidateRecommendationUncertaintyBandV2:
    candidate_id: str
    market_slug: str
    side: str
    forecast_probability: Decimal
    implied_probability: Decimal
    confidence: Decimal
    target_notional: Decimal
    forecast_dispersion: Decimal
    source_reliability: Decimal
    evidence_freshness: Decimal
    contradiction_severity: Decimal
    liquidity_exit_risk: Decimal
    resolution_risk: Decimal
    specialist_quorum: Decimal
    capital_lockup_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("candidate_id", "market_slug"):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        _require_side(self.side)
        for field_name in (
            "forecast_probability",
            "implied_probability",
            "confidence",
            "forecast_dispersion",
            "source_reliability",
            "evidence_freshness",
            "contradiction_severity",
            "liquidity_exit_risk",
            "resolution_risk",
            "specialist_quorum",
            "capital_lockup_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "target_notional",
            _normalize_positive_decimal("target_notional", self.target_notional),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyRecommendationUncertaintyBandV2Report:
    generated_at: datetime
    config_version: str
    candidate_id: str
    market_slug: str
    side: str
    forecast_probability: Decimal
    implied_probability: Decimal
    confidence: Decimal
    target_notional: Decimal
    forecast_dispersion: Decimal
    source_reliability: Decimal
    evidence_freshness: Decimal
    contradiction_severity: Decimal
    liquidity_exit_risk: Decimal
    resolution_risk: Decimal
    specialist_quorum: Decimal
    capital_lockup_ratio: Decimal
    min_uncertainty_adjusted_edge: Decimal
    max_uncertainty_width: Decimal
    min_confidence: Decimal
    max_capital_lockup_ratio: Decimal
    forecast_dispersion_weight: Decimal
    source_reliability_weight: Decimal
    evidence_freshness_weight: Decimal
    contradiction_severity_weight: Decimal
    liquidity_exit_risk_weight: Decimal
    resolution_risk_weight: Decimal
    specialist_quorum_weight: Decimal
    capital_lockup_weight: Decimal
    raw_edge: Decimal
    confidence_adjusted_edge: Decimal
    forecast_dispersion_penalty: Decimal
    source_reliability_penalty: Decimal
    evidence_freshness_penalty: Decimal
    contradiction_severity_penalty: Decimal
    liquidity_exit_risk_penalty: Decimal
    resolution_risk_penalty: Decimal
    specialist_quorum_penalty: Decimal
    capital_lockup_penalty: Decimal
    total_uncertainty_width: Decimal
    lower_probability_band: Decimal
    upper_probability_band: Decimal
    downside_edge: Decimal
    upside_edge: Decimal
    uncertainty_adjusted_edge: Decimal
    edge_status: str
    width_status: str
    confidence_status: str
    lockup_status: str
    report_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        for field_name in ("config_version", "candidate_id", "market_slug"):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        _require_side(self.side)
        for field_name in (
            "forecast_probability",
            "implied_probability",
            "confidence",
            "forecast_dispersion",
            "source_reliability",
            "evidence_freshness",
            "contradiction_severity",
            "liquidity_exit_risk",
            "resolution_risk",
            "specialist_quorum",
            "capital_lockup_ratio",
            "max_uncertainty_width",
            "min_confidence",
            "max_capital_lockup_ratio",
            "forecast_dispersion_weight",
            "source_reliability_weight",
            "evidence_freshness_weight",
            "contradiction_severity_weight",
            "liquidity_exit_risk_weight",
            "resolution_risk_weight",
            "specialist_quorum_weight",
            "capital_lockup_weight",
            "lower_probability_band",
            "upper_probability_band",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "target_notional",
            _normalize_positive_decimal("target_notional", self.target_notional),
        )
        for field_name in (
            "min_uncertainty_adjusted_edge",
            "raw_edge",
            "confidence_adjusted_edge",
            "forecast_dispersion_penalty",
            "source_reliability_penalty",
            "evidence_freshness_penalty",
            "contradiction_severity_penalty",
            "liquidity_exit_risk_penalty",
            "resolution_risk_penalty",
            "specialist_quorum_penalty",
            "capital_lockup_penalty",
            "total_uncertainty_width",
            "downside_edge",
            "upside_edge",
            "uncertainty_adjusted_edge",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        _require_choice("edge_status", self.edge_status, EDGE_STATUSES)
        _require_choice("width_status", self.width_status, WIDTH_STATUSES)
        _require_choice("confidence_status", self.confidence_status, CONFIDENCE_STATUSES)
        _require_choice("lockup_status", self.lockup_status, LOCKUP_STATUSES)
        _require_choice("report_status", self.report_status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags(self)
        _validate_report_consistency(self)
        expected_digest = _report_validation_digest(self)
        if self.derived_validation_digest:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest mismatch")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_strategy_recommendation_uncertainty_band_v2_report(
    candidate: CandidateRecommendationUncertaintyBandV2,
    *,
    config: StrategyRecommendationUncertaintyBandV2Config,
    generated_at: datetime,
) -> StrategyRecommendationUncertaintyBandV2Report:
    if type(candidate) is not CandidateRecommendationUncertaintyBandV2:
        raise ValueError("candidate must be a CandidateRecommendationUncertaintyBandV2")
    if type(config) is not StrategyRecommendationUncertaintyBandV2Config:
        raise ValueError("config must be a StrategyRecommendationUncertaintyBandV2Config")
    _require_hard_flags(candidate)
    _require_hard_flags(config)
    normalized_generated_at = _as_utc("generated_at", generated_at)

    raw_edge = _normalize_decimal(
        "raw_edge",
        candidate.forecast_probability - candidate.implied_probability,
    )
    confidence_adjusted_edge = _normalize_decimal(
        "confidence_adjusted_edge",
        raw_edge * candidate.confidence,
    )
    forecast_dispersion_penalty = _weighted_penalty(
        candidate.forecast_dispersion,
        config.forecast_dispersion_weight,
    )
    source_reliability_penalty = _weighted_penalty(
        ONE - candidate.source_reliability,
        config.source_reliability_weight,
    )
    evidence_freshness_penalty = _weighted_penalty(
        ONE - candidate.evidence_freshness,
        config.evidence_freshness_weight,
    )
    contradiction_severity_penalty = _weighted_penalty(
        candidate.contradiction_severity,
        config.contradiction_severity_weight,
    )
    liquidity_exit_risk_penalty = _weighted_penalty(
        candidate.liquidity_exit_risk,
        config.liquidity_exit_risk_weight,
    )
    resolution_risk_penalty = _weighted_penalty(
        candidate.resolution_risk,
        config.resolution_risk_weight,
    )
    specialist_quorum_penalty = _weighted_penalty(
        ONE - candidate.specialist_quorum,
        config.specialist_quorum_weight,
    )
    capital_lockup_penalty = _weighted_penalty(
        candidate.capital_lockup_ratio,
        config.capital_lockup_weight,
    )
    total_uncertainty_width = _cap_probability(
        _sum_decimals(
            (
                forecast_dispersion_penalty,
                source_reliability_penalty,
                evidence_freshness_penalty,
                contradiction_severity_penalty,
                liquidity_exit_risk_penalty,
                resolution_risk_penalty,
                specialist_quorum_penalty,
                capital_lockup_penalty,
            ),
        ),
    )
    lower_probability_band = _cap_probability(
        _normalize_decimal(
            "lower_probability_band",
            candidate.forecast_probability - total_uncertainty_width,
        ),
    )
    upper_probability_band = _cap_probability(
        _normalize_decimal(
            "upper_probability_band",
            candidate.forecast_probability + total_uncertainty_width,
        ),
    )
    downside_edge = _normalize_decimal(
        "downside_edge",
        lower_probability_band - candidate.implied_probability,
    )
    upside_edge = _normalize_decimal(
        "upside_edge",
        upper_probability_band - candidate.implied_probability,
    )
    uncertainty_adjusted_edge = _normalize_decimal(
        "uncertainty_adjusted_edge",
        confidence_adjusted_edge - total_uncertainty_width,
    )
    edge_status = (
        "edge_pass"
        if uncertainty_adjusted_edge >= config.min_uncertainty_adjusted_edge
        else "edge_reject"
    )
    width_status = (
        "width_pass"
        if total_uncertainty_width <= config.max_uncertainty_width
        else "width_watch"
    )
    confidence_status = (
        "confidence_pass"
        if candidate.confidence >= config.min_confidence
        else "confidence_watch"
    )
    lockup_status = (
        "lockup_pass"
        if candidate.capital_lockup_ratio <= config.max_capital_lockup_ratio
        else "lockup_watch"
    )
    report_status = _report_status(
        edge_status=edge_status,
        width_status=width_status,
        confidence_status=confidence_status,
        lockup_status=lockup_status,
    )

    return StrategyRecommendationUncertaintyBandV2Report(
        generated_at=normalized_generated_at,
        config_version=config.config_version,
        candidate_id=candidate.candidate_id,
        market_slug=candidate.market_slug,
        side=candidate.side,
        forecast_probability=candidate.forecast_probability,
        implied_probability=candidate.implied_probability,
        confidence=candidate.confidence,
        target_notional=candidate.target_notional,
        forecast_dispersion=candidate.forecast_dispersion,
        source_reliability=candidate.source_reliability,
        evidence_freshness=candidate.evidence_freshness,
        contradiction_severity=candidate.contradiction_severity,
        liquidity_exit_risk=candidate.liquidity_exit_risk,
        resolution_risk=candidate.resolution_risk,
        specialist_quorum=candidate.specialist_quorum,
        capital_lockup_ratio=candidate.capital_lockup_ratio,
        min_uncertainty_adjusted_edge=config.min_uncertainty_adjusted_edge,
        max_uncertainty_width=config.max_uncertainty_width,
        min_confidence=config.min_confidence,
        max_capital_lockup_ratio=config.max_capital_lockup_ratio,
        forecast_dispersion_weight=config.forecast_dispersion_weight,
        source_reliability_weight=config.source_reliability_weight,
        evidence_freshness_weight=config.evidence_freshness_weight,
        contradiction_severity_weight=config.contradiction_severity_weight,
        liquidity_exit_risk_weight=config.liquidity_exit_risk_weight,
        resolution_risk_weight=config.resolution_risk_weight,
        specialist_quorum_weight=config.specialist_quorum_weight,
        capital_lockup_weight=config.capital_lockup_weight,
        raw_edge=raw_edge,
        confidence_adjusted_edge=confidence_adjusted_edge,
        forecast_dispersion_penalty=forecast_dispersion_penalty,
        source_reliability_penalty=source_reliability_penalty,
        evidence_freshness_penalty=evidence_freshness_penalty,
        contradiction_severity_penalty=contradiction_severity_penalty,
        liquidity_exit_risk_penalty=liquidity_exit_risk_penalty,
        resolution_risk_penalty=resolution_risk_penalty,
        specialist_quorum_penalty=specialist_quorum_penalty,
        capital_lockup_penalty=capital_lockup_penalty,
        total_uncertainty_width=total_uncertainty_width,
        lower_probability_band=lower_probability_band,
        upper_probability_band=upper_probability_band,
        downside_edge=downside_edge,
        upside_edge=upside_edge,
        uncertainty_adjusted_edge=uncertainty_adjusted_edge,
        edge_status=edge_status,
        width_status=width_status,
        confidence_status=confidence_status,
        lockup_status=lockup_status,
        report_status=report_status,
        reason_codes=_reason_codes(
            edge_status=edge_status,
            width_status=width_status,
            confidence_status=confidence_status,
            lockup_status=lockup_status,
            candidate=candidate,
        ),
    )


def strategy_recommendation_uncertainty_band_v2_payload(
    report: StrategyRecommendationUncertaintyBandV2Report,
) -> dict[str, Any]:
    if type(report) is not StrategyRecommendationUncertaintyBandV2Report:
        raise ValueError("report must be a StrategyRecommendationUncertaintyBandV2Report")
    _require_hard_flags(report)
    expected_digest = _report_validation_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest mismatch")
    _validate_report_consistency(report)
    payload = _report_payload_without_digest(report)
    payload["derived_validation_digest"] = report.derived_validation_digest
    return validate_strategy_recommendation_uncertainty_band_v2_public_payload(payload)


def validate_strategy_recommendation_uncertainty_band_v2_public_payload(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(payload, Mapping) or isinstance(payload, (str, bytes)):
        raise ValueError("public payload must be a mapping")
    ready = _validate_public_payload_value(payload)
    if not isinstance(ready, dict):
        raise ValueError("public payload must be a JSON object")
    _require_payload_hard_flags(ready)
    digest = ready.get("derived_validation_digest")
    if digest is None:
        raise ValueError("derived_validation_digest must be present")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    _require_sha256("derived_validation_digest", digest)
    digest_source = dict(ready)
    digest_source.pop("derived_validation_digest")
    if digest != _public_payload_digest(digest_source):
        raise ValueError("derived_validation_digest mismatch")
    return ready


def _report_status(
    *,
    edge_status: str,
    width_status: str,
    confidence_status: str,
    lockup_status: str,
) -> str:
    if edge_status == "edge_reject":
        return "paper_reject"
    if (
        width_status == "width_watch"
        or confidence_status == "confidence_watch"
        or lockup_status == "lockup_watch"
    ):
        return "paper_watch"
    return "paper_recommendable"


def _reason_codes(
    *,
    edge_status: str,
    width_status: str,
    confidence_status: str,
    lockup_status: str,
    candidate: CandidateRecommendationUncertaintyBandV2,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if edge_status == "edge_pass":
        reason_codes.append("uncertainty_adjusted_edge_passed")
    else:
        reason_codes.append("uncertainty_adjusted_edge_below_minimum")
    if width_status == "width_pass":
        reason_codes.append("uncertainty_width_within_limit")
    else:
        reason_codes.append("uncertainty_width_above_limit")
    if confidence_status == "confidence_pass":
        reason_codes.append("confidence_passed")
    else:
        reason_codes.append("confidence_below_minimum")
    if lockup_status == "lockup_pass":
        reason_codes.append("capital_lockup_within_limit")
    else:
        reason_codes.append("capital_lockup_above_limit")
    if candidate.forecast_dispersion > ZERO:
        reason_codes.append("forecast_dispersion_penalty_applied")
    if candidate.source_reliability < ONE:
        reason_codes.append("source_reliability_penalty_applied")
    if candidate.evidence_freshness < ONE:
        reason_codes.append("evidence_freshness_penalty_applied")
    if candidate.contradiction_severity > ZERO:
        reason_codes.append("contradiction_severity_penalty_applied")
    if candidate.liquidity_exit_risk > ZERO:
        reason_codes.append("liquidity_exit_risk_penalty_applied")
    if candidate.resolution_risk > ZERO:
        reason_codes.append("resolution_risk_penalty_applied")
    if candidate.specialist_quorum < ONE:
        reason_codes.append("specialist_quorum_penalty_applied")
    if candidate.capital_lockup_ratio > ZERO:
        reason_codes.append("capital_lockup_penalty_applied")
    return tuple(reason_codes)


def _validate_report_consistency(
    report: StrategyRecommendationUncertaintyBandV2Report,
) -> None:
    if report.raw_edge != _normalize_decimal(
        "raw_edge",
        report.forecast_probability - report.implied_probability,
    ):
        raise ValueError("raw_edge must match probabilities")
    if report.confidence_adjusted_edge != _normalize_decimal(
        "confidence_adjusted_edge",
        report.raw_edge * report.confidence,
    ):
        raise ValueError("confidence_adjusted_edge must match confidence")
    expected_penalties = {
        "forecast_dispersion_penalty": _weighted_penalty(
            report.forecast_dispersion,
            report.forecast_dispersion_weight,
        ),
        "source_reliability_penalty": _weighted_penalty(
            ONE - report.source_reliability,
            report.source_reliability_weight,
        ),
        "evidence_freshness_penalty": _weighted_penalty(
            ONE - report.evidence_freshness,
            report.evidence_freshness_weight,
        ),
        "contradiction_severity_penalty": _weighted_penalty(
            report.contradiction_severity,
            report.contradiction_severity_weight,
        ),
        "liquidity_exit_risk_penalty": _weighted_penalty(
            report.liquidity_exit_risk,
            report.liquidity_exit_risk_weight,
        ),
        "resolution_risk_penalty": _weighted_penalty(
            report.resolution_risk,
            report.resolution_risk_weight,
        ),
        "specialist_quorum_penalty": _weighted_penalty(
            ONE - report.specialist_quorum,
            report.specialist_quorum_weight,
        ),
        "capital_lockup_penalty": _weighted_penalty(
            report.capital_lockup_ratio,
            report.capital_lockup_weight,
        ),
    }
    for field_name, expected in expected_penalties.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match weighted factor")
    if report.total_uncertainty_width != _cap_probability(
        _sum_decimals(tuple(expected_penalties.values())),
    ):
        raise ValueError("total_uncertainty_width must match penalties")
    if report.lower_probability_band != _cap_probability(
        _normalize_decimal(
            "lower_probability_band",
            report.forecast_probability - report.total_uncertainty_width,
        ),
    ):
        raise ValueError("lower_probability_band must match forecast and width")
    if report.upper_probability_band != _cap_probability(
        _normalize_decimal(
            "upper_probability_band",
            report.forecast_probability + report.total_uncertainty_width,
        ),
    ):
        raise ValueError("upper_probability_band must match forecast and width")
    if report.downside_edge != _normalize_decimal(
        "downside_edge",
        report.lower_probability_band - report.implied_probability,
    ):
        raise ValueError("downside_edge must match lower band")
    if report.upside_edge != _normalize_decimal(
        "upside_edge",
        report.upper_probability_band - report.implied_probability,
    ):
        raise ValueError("upside_edge must match upper band")
    if report.uncertainty_adjusted_edge != _normalize_decimal(
        "uncertainty_adjusted_edge",
        report.confidence_adjusted_edge - report.total_uncertainty_width,
    ):
        raise ValueError("uncertainty_adjusted_edge must reconcile")

    expected_edge_status = (
        "edge_pass"
        if report.uncertainty_adjusted_edge >= report.min_uncertainty_adjusted_edge
        else "edge_reject"
    )
    expected_width_status = (
        "width_pass"
        if report.total_uncertainty_width <= report.max_uncertainty_width
        else "width_watch"
    )
    expected_confidence_status = (
        "confidence_pass" if report.confidence >= report.min_confidence else "confidence_watch"
    )
    expected_lockup_status = (
        "lockup_pass"
        if report.capital_lockup_ratio <= report.max_capital_lockup_ratio
        else "lockup_watch"
    )
    if report.edge_status != expected_edge_status:
        raise ValueError("edge_status must match thresholds")
    if report.width_status != expected_width_status:
        raise ValueError("width_status must match thresholds")
    if report.confidence_status != expected_confidence_status:
        raise ValueError("confidence_status must match thresholds")
    if report.lockup_status != expected_lockup_status:
        raise ValueError("lockup_status must match thresholds")
    expected_report_status = _report_status(
        edge_status=report.edge_status,
        width_status=report.width_status,
        confidence_status=report.confidence_status,
        lockup_status=report.lockup_status,
    )
    if report.report_status != expected_report_status:
        raise ValueError("report_status must match component statuses")


def _report_payload_without_digest(
    report: StrategyRecommendationUncertaintyBandV2Report,
) -> dict[str, Any]:
    return {
        "generated_at": _payload_value(report.generated_at),
        "config_version": report.config_version,
        "candidate_id": report.candidate_id,
        "market_slug": report.market_slug,
        "side": report.side,
        "forecast_probability": _payload_value(report.forecast_probability),
        "implied_probability": _payload_value(report.implied_probability),
        "confidence": _payload_value(report.confidence),
        "target_notional": _payload_value(report.target_notional),
        "forecast_dispersion": _payload_value(report.forecast_dispersion),
        "source_reliability": _payload_value(report.source_reliability),
        "evidence_freshness": _payload_value(report.evidence_freshness),
        "contradiction_severity": _payload_value(report.contradiction_severity),
        "liquidity_exit_risk": _payload_value(report.liquidity_exit_risk),
        "resolution_risk": _payload_value(report.resolution_risk),
        "specialist_quorum": _payload_value(report.specialist_quorum),
        "capital_lockup_ratio": _payload_value(report.capital_lockup_ratio),
        "min_uncertainty_adjusted_edge": _payload_value(
            report.min_uncertainty_adjusted_edge,
        ),
        "max_uncertainty_width": _payload_value(report.max_uncertainty_width),
        "min_confidence": _payload_value(report.min_confidence),
        "max_capital_lockup_ratio": _payload_value(report.max_capital_lockup_ratio),
        "forecast_dispersion_weight": _payload_value(report.forecast_dispersion_weight),
        "source_reliability_weight": _payload_value(report.source_reliability_weight),
        "evidence_freshness_weight": _payload_value(report.evidence_freshness_weight),
        "contradiction_severity_weight": _payload_value(
            report.contradiction_severity_weight,
        ),
        "liquidity_exit_risk_weight": _payload_value(report.liquidity_exit_risk_weight),
        "resolution_risk_weight": _payload_value(report.resolution_risk_weight),
        "specialist_quorum_weight": _payload_value(report.specialist_quorum_weight),
        "capital_lockup_weight": _payload_value(report.capital_lockup_weight),
        "raw_edge": _payload_value(report.raw_edge),
        "confidence_adjusted_edge": _payload_value(report.confidence_adjusted_edge),
        "forecast_dispersion_penalty": _payload_value(
            report.forecast_dispersion_penalty,
        ),
        "source_reliability_penalty": _payload_value(report.source_reliability_penalty),
        "evidence_freshness_penalty": _payload_value(report.evidence_freshness_penalty),
        "contradiction_severity_penalty": _payload_value(
            report.contradiction_severity_penalty,
        ),
        "liquidity_exit_risk_penalty": _payload_value(
            report.liquidity_exit_risk_penalty,
        ),
        "resolution_risk_penalty": _payload_value(report.resolution_risk_penalty),
        "specialist_quorum_penalty": _payload_value(report.specialist_quorum_penalty),
        "capital_lockup_penalty": _payload_value(report.capital_lockup_penalty),
        "total_uncertainty_width": _payload_value(report.total_uncertainty_width),
        "lower_probability_band": _payload_value(report.lower_probability_band),
        "upper_probability_band": _payload_value(report.upper_probability_band),
        "downside_edge": _payload_value(report.downside_edge),
        "upside_edge": _payload_value(report.upside_edge),
        "uncertainty_adjusted_edge": _payload_value(report.uncertainty_adjusted_edge),
        "edge_status": report.edge_status,
        "width_status": report.width_status,
        "confidence_status": report.confidence_status,
        "lockup_status": report.lockup_status,
        "report_status": report.report_status,
        "reason_codes": list(report.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _report_validation_digest(report: StrategyRecommendationUncertaintyBandV2Report) -> str:
    return _public_payload_digest(_report_payload_without_digest(report))


def _public_payload_digest(payload_without_digest: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            payload_without_digest,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()


def _payload_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(_normalize_decimal("payload decimal", value), "f")
    if isinstance(value, datetime):
        return _payload_datetime(value)
    if type(value) is str:
        _require_canonical_public_string("public payload value", value)
        return value
    if type(value) is bool:
        return value
    if type(value) in (int, float):
        raise ValueError("public payload value must use Decimal strings")
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    raise ValueError("public payload value is not JSON serializable")


def _validate_public_payload_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload key must be a string")
            _require_canonical_public_string("public payload key", key)
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{key} must be True")
            ready[key] = _validate_public_payload_value(item)
        return ready
    if isinstance(value, tuple):
        return [_validate_public_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_validate_public_payload_value(item) for item in value]
    if type(value) is str:
        _require_canonical_public_string("public payload value", value)
        return value
    if type(value) is bool:
        return value
    if value is None:
        return None
    if isinstance(value, Decimal):
        return _payload_value(value)
    if type(value) in (int, float):
        raise ValueError("public payload value must not use native numeric types")
    raise ValueError("public payload value is not JSON serializable")


def _payload_datetime(value: datetime) -> str:
    text = _as_utc("payload datetime", value).isoformat()
    if text.endswith("+00:00"):
        return f"{text[:-6]}Z"
    return text


def _require_payload_hard_flags(payload: Mapping[str, Any]) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _normalize_reason_codes(field_name: str, values: Iterable[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        items = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if not items:
        raise ValueError(f"{field_name} must contain at least one value")
    for item in items:
        _require_canonical_public_string("reason_code", item)
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} must not contain duplicates")
    return tuple(sorted(items))


def _weighted_penalty(value: Decimal, weight: Decimal) -> Decimal:
    value = _normalize_ratio("penalty value", value)
    weight = _normalize_ratio("penalty weight", weight)
    with localcontext() as context:
        context.prec = 28
        return _normalize_decimal("weighted_penalty", value * weight)


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    return _normalize_decimal("sum", sum(values, Decimal("0")))


def _cap_probability(value: Decimal) -> Decimal:
    value = _normalize_decimal("probability", value)
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return value


def _normalize_ratio(field_name: str, value: Decimal) -> Decimal:
    value = _normalize_nonnegative_decimal(field_name, value)
    if value > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return value


def _normalize_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _normalize_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _normalize_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext() as context:
        context.prec = 28
        return value.quantize(DECIMAL_QUANTUM)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_side(value: str) -> None:
    _require_canonical_public_string("side", value)
    if value not in SIDES:
        raise ValueError("side must be yes or no")


def _require_choice(field_name: str, value: str, choices: tuple[str, ...]) -> None:
    _require_canonical_public_string(field_name, value)
    if value not in choices:
        raise ValueError(f"{field_name} must be a known status")


def _require_hard_flags(value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_sha256(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_canonical_public_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must be non-empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must be canonical")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe value")


__all__ = (
    "CandidateRecommendationUncertaintyBandV2",
    "StrategyRecommendationUncertaintyBandV2Config",
    "StrategyRecommendationUncertaintyBandV2Report",
    "build_strategy_recommendation_uncertainty_band_v2_report",
    "strategy_recommendation_uncertainty_band_v2_payload",
    "validate_strategy_recommendation_uncertainty_band_v2_public_payload",
)
