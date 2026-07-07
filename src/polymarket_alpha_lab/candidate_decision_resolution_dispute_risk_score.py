"""Pure report-only resolution dispute risk score for candidate decisions."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_CANDIDATE_DECISION_RESOLUTION_DISPUTE_RISK_SCORE_CONFIG_VERSION = (
    "candidate-decision-resolution-dispute-risk-score-v0"
)
RESOLUTION_DISPUTE_RISK_STATUSES = ("pass", "watch", "block")

QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT_PRECISION = 64

_RAW_MARKET_OR_CANDIDATE_PUBLIC_TERMS = (
    "candidate_id",
    "candidate_slug",
    "condition_id",
    "market_id",
    "market_slug",
    "normalized_market_question",
    "question",
    "raw_candidate",
)
_SOURCE_REFERENCE_PUBLIC_TERMS = (
    "source_ref",
    "source_refs",
    "source_url",
    "source_uri",
    "source_text",
    "source_excerpt",
    "source_title",
    "raw_text",
    "url",
    "http://",
    "https://",
    "www.",
    "://",
    "source-ref:",
    "source_ref:",
    "source-url:",
)
_UNSAFE_LIVE_PUBLIC_TERMS = (
    "api_key",
    "auth",
    "bearer",
    "buy",
    "connection_string",
    "credential",
    "database",
    "dsn",
    "jwt",
    "oauth",
    "order",
    "password",
    "position size",
    "position sizing",
    "position-size",
    "position-sizing",
    "position_size",
    "private_key",
    "recommendation",
    "secret",
    "sell",
    "session",
    "table",
    "token",
    "trade",
    "trading",
    "wallet",
)
_PUBLIC_STATUS_ALIASES = ("ready", "blocked", "matched", "supported")


@dataclass(frozen=True)
class CandidateDecisionResolutionDisputeRiskScoreConfig:
    config_version: str = (
        DEFAULT_CANDIDATE_DECISION_RESOLUTION_DISPUTE_RISK_SCORE_CONFIG_VERSION
    )
    max_pass_resolution_dispute_risk_score: Decimal = Decimal("0.300000")
    max_watch_resolution_dispute_risk_score: Decimal = Decimal("0.600000")
    max_ambiguous_clause_count_for_component: Decimal = Decimal("5")
    max_subjective_term_count_for_component: Decimal = Decimal("8")
    max_precedent_dispute_count_for_component: Decimal = Decimal("4")
    ambiguous_clause_block_count: Decimal = Decimal("5")
    subjective_term_block_count: Decimal = Decimal("8")
    precedent_dispute_block_count: Decimal = Decimal("4")
    source_conflict_block_score: Decimal = Decimal("0.750000")
    rule_clarity_block_score: Decimal = Decimal("0.300000")
    adjudication_readiness_block_score: Decimal = Decimal("0.300000")
    ambiguous_clause_weight: Decimal = Decimal("0.200000")
    subjective_term_weight: Decimal = Decimal("0.150000")
    precedent_dispute_weight: Decimal = Decimal("0.200000")
    source_conflict_weight: Decimal = Decimal("0.200000")
    rule_uncertainty_weight: Decimal = Decimal("0.125000")
    adjudication_unreadiness_weight: Decimal = Decimal("0.125000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionResolutionDisputeRiskScoreConfig:
            raise TypeError(
                "CandidateDecisionResolutionDisputeRiskScoreConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            CandidateDecisionResolutionDisputeRiskScoreConfig,
        )
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_CANDIDATE_DECISION_RESOLUTION_DISPUTE_RISK_SCORE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported version")
        for field_name in (
            "max_pass_resolution_dispute_risk_score",
            "max_watch_resolution_dispute_risk_score",
            "source_conflict_block_score",
            "rule_clarity_block_score",
            "adjudication_readiness_block_score",
            "ambiguous_clause_weight",
            "subjective_term_weight",
            "precedent_dispute_weight",
            "source_conflict_weight",
            "rule_uncertainty_weight",
            "adjudication_unreadiness_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_ambiguous_clause_count_for_component",
            "max_subjective_term_count_for_component",
            "max_precedent_dispute_count_for_component",
            "ambiguous_clause_block_count",
            "subjective_term_block_count",
            "precedent_dispute_block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _validate_config(self)
        _require_phase_flags("config", self)
        reject_candidate_decision_resolution_dispute_risk_score_unsafe_payload(
            "resolution dispute risk config",
            self,
        )


@dataclass(frozen=True)
class CandidateDecisionResolutionDisputeRiskScoreInput:
    generated_at: datetime
    redacted_candidate_ref: str
    ambiguous_clause_count: Decimal
    subjective_term_count: Decimal
    precedent_dispute_count: Decimal
    source_conflict_score: Decimal
    rule_clarity_score: Decimal
    adjudication_readiness_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionResolutionDisputeRiskScoreInput:
            raise TypeError(
                "CandidateDecisionResolutionDisputeRiskScoreInput does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "input",
            self,
            CandidateDecisionResolutionDisputeRiskScoreInput,
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "redacted_candidate_ref",
            _require_redacted_candidate_ref(self.redacted_candidate_ref),
        )
        for field_name in (
            "ambiguous_clause_count",
            "subjective_term_count",
            "precedent_dispute_count",
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
            "source_conflict_score",
            "rule_clarity_score",
            "adjudication_readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_phase_flags("input", self)
        reject_candidate_decision_resolution_dispute_risk_score_unsafe_payload(
            "resolution dispute risk input",
            self,
        )


@dataclass(frozen=True)
class CandidateDecisionResolutionDisputeRiskScoreReport:
    generated_at: datetime
    config_version: str
    max_pass_resolution_dispute_risk_score: Decimal
    max_watch_resolution_dispute_risk_score: Decimal
    max_ambiguous_clause_count_for_component: Decimal
    max_subjective_term_count_for_component: Decimal
    max_precedent_dispute_count_for_component: Decimal
    ambiguous_clause_block_count: Decimal
    subjective_term_block_count: Decimal
    precedent_dispute_block_count: Decimal
    source_conflict_block_score: Decimal
    rule_clarity_block_score: Decimal
    adjudication_readiness_block_score: Decimal
    ambiguous_clause_weight: Decimal
    subjective_term_weight: Decimal
    precedent_dispute_weight: Decimal
    source_conflict_weight: Decimal
    rule_uncertainty_weight: Decimal
    adjudication_unreadiness_weight: Decimal
    redacted_candidate_ref: str
    ambiguous_clause_count: Decimal
    subjective_term_count: Decimal
    precedent_dispute_count: Decimal
    source_conflict_score: Decimal
    rule_clarity_score: Decimal
    adjudication_readiness_score: Decimal
    ambiguous_clause_component: Decimal
    subjective_term_component: Decimal
    precedent_dispute_component: Decimal
    source_conflict_component: Decimal
    rule_uncertainty_component: Decimal
    adjudication_unreadiness_component: Decimal
    resolution_dispute_risk_score: Decimal
    resolution_dispute_risk_status: str
    hard_blocker_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionResolutionDisputeRiskScoreReport:
            raise TypeError(
                "CandidateDecisionResolutionDisputeRiskScoreReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "report",
            self,
            CandidateDecisionResolutionDisputeRiskScoreReport,
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_CANDIDATE_DECISION_RESOLUTION_DISPUTE_RISK_SCORE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported version")
        object.__setattr__(
            self,
            "redacted_candidate_ref",
            _require_redacted_candidate_ref(self.redacted_candidate_ref),
        )
        for field_name in (
            "max_pass_resolution_dispute_risk_score",
            "max_watch_resolution_dispute_risk_score",
            "source_conflict_block_score",
            "rule_clarity_block_score",
            "adjudication_readiness_block_score",
            "ambiguous_clause_weight",
            "subjective_term_weight",
            "precedent_dispute_weight",
            "source_conflict_weight",
            "rule_uncertainty_weight",
            "adjudication_unreadiness_weight",
            "source_conflict_score",
            "rule_clarity_score",
            "adjudication_readiness_score",
            "ambiguous_clause_component",
            "subjective_term_component",
            "precedent_dispute_component",
            "source_conflict_component",
            "rule_uncertainty_component",
            "adjudication_unreadiness_component",
            "resolution_dispute_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_ambiguous_clause_count_for_component",
            "max_subjective_term_count_for_component",
            "max_precedent_dispute_count_for_component",
            "ambiguous_clause_block_count",
            "subjective_term_block_count",
            "precedent_dispute_block_count",
            "ambiguous_clause_count",
            "subjective_term_count",
            "precedent_dispute_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _require_choice(
            "resolution_dispute_risk_status",
            self.resolution_dispute_risk_status,
            RESOLUTION_DISPUTE_RISK_STATUSES,
        )
        object.__setattr__(
            self,
            "hard_blocker_codes",
            _normalize_reason_codes(
                "hard_blocker_codes",
                self.hard_blocker_codes,
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _validate_config_like_report(self)
        _validate_report(self)
        _require_phase_flags("report", self)
        reject_candidate_decision_resolution_dispute_risk_score_unsafe_payload(
            "resolution dispute risk report",
            self,
        )
        expected_digest = _report_digest(self)
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return candidate_decision_resolution_dispute_risk_score_payload(self)


def build_candidate_decision_resolution_dispute_risk_score_report(
    score_input: CandidateDecisionResolutionDisputeRiskScoreInput,
    *,
    config: CandidateDecisionResolutionDisputeRiskScoreConfig | None = None,
) -> CandidateDecisionResolutionDisputeRiskScoreReport:
    if type(score_input) is not CandidateDecisionResolutionDisputeRiskScoreInput:
        raise ValueError(
            "score_input must be a CandidateDecisionResolutionDisputeRiskScoreInput",
        )
    report_config = config or CandidateDecisionResolutionDisputeRiskScoreConfig()
    if type(report_config) is not CandidateDecisionResolutionDisputeRiskScoreConfig:
        raise ValueError(
            "config must be a CandidateDecisionResolutionDisputeRiskScoreConfig",
        )
    _require_phase_flags("input", score_input)
    _require_phase_flags("config", report_config)
    reject_candidate_decision_resolution_dispute_risk_score_unsafe_payload(
        "resolution dispute risk input",
        score_input,
    )
    reject_candidate_decision_resolution_dispute_risk_score_unsafe_payload(
        "resolution dispute risk config",
        report_config,
    )
    return CandidateDecisionResolutionDisputeRiskScoreReport(
        **_report_values(score_input, report_config),
    )


def candidate_decision_resolution_dispute_risk_score_payload(
    report: CandidateDecisionResolutionDisputeRiskScoreReport,
) -> dict[str, Any]:
    if type(report) is not CandidateDecisionResolutionDisputeRiskScoreReport:
        raise ValueError(
            "report must be a CandidateDecisionResolutionDisputeRiskScoreReport",
        )
    _require_phase_flags("report", report)
    _validate_report(report)
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest must match report fields")
    reject_candidate_decision_resolution_dispute_risk_score_unsafe_payload(
        "resolution dispute risk report",
        report,
    )
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    validate_candidate_decision_resolution_dispute_risk_score_public_payload(payload)
    return payload


def validate_candidate_decision_resolution_dispute_risk_score_public_payload(
    payload: object,
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_public_numbers(payload)
    _reject_public_status_aliases(payload)
    reject_candidate_decision_resolution_dispute_risk_score_unsafe_payload(
        "resolution dispute risk public payload",
        payload,
    )


def reject_candidate_decision_resolution_dispute_risk_score_unsafe_payload(
    label: str,
    payload: object,
) -> None:
    for path, item in _iter_public_strings(payload):
        lowered = item.lower()
        if any(term in lowered for term in _RAW_MARKET_OR_CANDIDATE_PUBLIC_TERMS):
            raise ValueError(f"raw market or candidate public payload entry in {label}: {path}")
        if any(term in lowered for term in _SOURCE_REFERENCE_PUBLIC_TERMS):
            raise ValueError(f"source references public payload entry in {label}: {path}")
        if any(term in lowered for term in _UNSAFE_LIVE_PUBLIC_TERMS):
            raise ValueError(f"unsafe live surface public payload entry in {label}: {path}")


def _report_values(
    score_input: CandidateDecisionResolutionDisputeRiskScoreInput,
    config: CandidateDecisionResolutionDisputeRiskScoreConfig,
) -> dict[str, object]:
    ambiguous_clause_component_raw = _ratio(
        score_input.ambiguous_clause_count,
        config.max_ambiguous_clause_count_for_component,
    )
    subjective_term_component_raw = _ratio(
        score_input.subjective_term_count,
        config.max_subjective_term_count_for_component,
    )
    precedent_dispute_component_raw = _ratio(
        score_input.precedent_dispute_count,
        config.max_precedent_dispute_count_for_component,
    )
    rule_uncertainty_component_raw = _subtract_nonnegative(
        "rule_uncertainty_component",
        ONE,
        score_input.rule_clarity_score,
    )
    adjudication_unreadiness_component_raw = _subtract_nonnegative(
        "adjudication_unreadiness_component",
        ONE,
        score_input.adjudication_readiness_score,
    )
    score = _weighted_score(
        ambiguous_clause_component_raw,
        subjective_term_component_raw,
        precedent_dispute_component_raw,
        score_input.source_conflict_score,
        rule_uncertainty_component_raw,
        adjudication_unreadiness_component_raw,
        config,
    )
    hard_blockers = _hard_blocker_codes(score_input, score, config)
    status = _status(score, hard_blockers, config)
    reason_codes = _reason_codes(score_input, score, status, config)
    return {
        "generated_at": score_input.generated_at,
        "config_version": config.config_version,
        "max_pass_resolution_dispute_risk_score": (
            config.max_pass_resolution_dispute_risk_score
        ),
        "max_watch_resolution_dispute_risk_score": (
            config.max_watch_resolution_dispute_risk_score
        ),
        "max_ambiguous_clause_count_for_component": (
            config.max_ambiguous_clause_count_for_component
        ),
        "max_subjective_term_count_for_component": (
            config.max_subjective_term_count_for_component
        ),
        "max_precedent_dispute_count_for_component": (
            config.max_precedent_dispute_count_for_component
        ),
        "ambiguous_clause_block_count": config.ambiguous_clause_block_count,
        "subjective_term_block_count": config.subjective_term_block_count,
        "precedent_dispute_block_count": config.precedent_dispute_block_count,
        "source_conflict_block_score": config.source_conflict_block_score,
        "rule_clarity_block_score": config.rule_clarity_block_score,
        "adjudication_readiness_block_score": (
            config.adjudication_readiness_block_score
        ),
        "ambiguous_clause_weight": config.ambiguous_clause_weight,
        "subjective_term_weight": config.subjective_term_weight,
        "precedent_dispute_weight": config.precedent_dispute_weight,
        "source_conflict_weight": config.source_conflict_weight,
        "rule_uncertainty_weight": config.rule_uncertainty_weight,
        "adjudication_unreadiness_weight": (
            config.adjudication_unreadiness_weight
        ),
        "redacted_candidate_ref": score_input.redacted_candidate_ref,
        "ambiguous_clause_count": score_input.ambiguous_clause_count,
        "subjective_term_count": score_input.subjective_term_count,
        "precedent_dispute_count": score_input.precedent_dispute_count,
        "source_conflict_score": score_input.source_conflict_score,
        "rule_clarity_score": score_input.rule_clarity_score,
        "adjudication_readiness_score": score_input.adjudication_readiness_score,
        "ambiguous_clause_component": _quantize_unit(ambiguous_clause_component_raw),
        "subjective_term_component": _quantize_unit(subjective_term_component_raw),
        "precedent_dispute_component": _quantize_unit(precedent_dispute_component_raw),
        "source_conflict_component": score_input.source_conflict_score,
        "rule_uncertainty_component": _quantize_unit(rule_uncertainty_component_raw),
        "adjudication_unreadiness_component": _quantize_unit(
            adjudication_unreadiness_component_raw,
        ),
        "resolution_dispute_risk_score": score,
        "resolution_dispute_risk_status": status,
        "hard_blocker_codes": hard_blockers,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _weighted_score(
    ambiguous_clause_component: Decimal,
    subjective_term_component: Decimal,
    precedent_dispute_component: Decimal,
    source_conflict_component: Decimal,
    rule_uncertainty_component: Decimal,
    adjudication_unreadiness_component: Decimal,
    config: CandidateDecisionResolutionDisputeRiskScoreConfig,
) -> Decimal:
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        weighted = (
            ambiguous_clause_component * config.ambiguous_clause_weight
            + subjective_term_component * config.subjective_term_weight
            + precedent_dispute_component * config.precedent_dispute_weight
            + source_conflict_component * config.source_conflict_weight
            + rule_uncertainty_component * config.rule_uncertainty_weight
            + adjudication_unreadiness_component
            * config.adjudication_unreadiness_weight
        )
        return _quantize_unit(weighted)


def _hard_blocker_codes(
    score_input: CandidateDecisionResolutionDisputeRiskScoreInput,
    resolution_dispute_risk_score: Decimal,
    config: CandidateDecisionResolutionDisputeRiskScoreConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if score_input.ambiguous_clause_count >= config.ambiguous_clause_block_count:
        codes.append("ambiguous_clause_count_block")
    if score_input.subjective_term_count >= config.subjective_term_block_count:
        codes.append("subjective_term_count_block")
    if score_input.precedent_dispute_count >= config.precedent_dispute_block_count:
        codes.append("precedent_dispute_count_block")
    if score_input.source_conflict_score >= config.source_conflict_block_score:
        codes.append("source_conflict_block")
    if score_input.rule_clarity_score <= config.rule_clarity_block_score:
        codes.append("rule_clarity_block")
    if (
        score_input.adjudication_readiness_score
        <= config.adjudication_readiness_block_score
    ):
        codes.append("adjudication_readiness_block")
    if resolution_dispute_risk_score > config.max_watch_resolution_dispute_risk_score:
        codes.append("resolution_dispute_risk_score_block")
    return tuple(codes)


def _status(
    resolution_dispute_risk_score: Decimal,
    hard_blocker_codes: tuple[str, ...],
    config: CandidateDecisionResolutionDisputeRiskScoreConfig,
) -> str:
    if (
        hard_blocker_codes
        or resolution_dispute_risk_score > config.max_watch_resolution_dispute_risk_score
    ):
        return "block"
    if resolution_dispute_risk_score > config.max_pass_resolution_dispute_risk_score:
        return "watch"
    return "pass"


def _reason_codes(
    score_input: CandidateDecisionResolutionDisputeRiskScoreInput,
    resolution_dispute_risk_score: Decimal,
    status: str,
    config: CandidateDecisionResolutionDisputeRiskScoreConfig,
) -> tuple[str, ...]:
    codes = list(score_input.reason_codes)
    codes.append(f"resolution_dispute_risk_{status}")
    codes.append(
        _count_reason(
            "ambiguous_clause_count",
            score_input.ambiguous_clause_count,
            config.ambiguous_clause_block_count,
            _ratio(
                score_input.ambiguous_clause_count,
                config.max_ambiguous_clause_count_for_component,
            ),
            config.max_pass_resolution_dispute_risk_score,
        ),
    )
    codes.append(
        _count_reason(
            "subjective_term_count",
            score_input.subjective_term_count,
            config.subjective_term_block_count,
            _ratio(
                score_input.subjective_term_count,
                config.max_subjective_term_count_for_component,
            ),
            config.max_pass_resolution_dispute_risk_score,
        ),
    )
    codes.append(
        _count_reason(
            "precedent_dispute_count",
            score_input.precedent_dispute_count,
            config.precedent_dispute_block_count,
            _ratio(
                score_input.precedent_dispute_count,
                config.max_precedent_dispute_count_for_component,
            ),
            config.max_pass_resolution_dispute_risk_score,
        ),
    )
    codes.append(
        _component_reason(
            "source_conflict",
            score_input.source_conflict_score,
            config.max_pass_resolution_dispute_risk_score,
            config.source_conflict_block_score,
        ),
    )
    rule_uncertainty = _subtract_nonnegative(
        "rule_uncertainty_component",
        ONE,
        score_input.rule_clarity_score,
    )
    if score_input.rule_clarity_score <= config.rule_clarity_block_score:
        codes.append("rule_clarity_block")
    elif rule_uncertainty > config.max_pass_resolution_dispute_risk_score:
        codes.append("rule_clarity_watch")
    else:
        codes.append("rule_clarity_pass")
    adjudication_unreadiness = _subtract_nonnegative(
        "adjudication_unreadiness_component",
        ONE,
        score_input.adjudication_readiness_score,
    )
    if (
        score_input.adjudication_readiness_score
        <= config.adjudication_readiness_block_score
    ):
        codes.append("adjudication_readiness_block")
    elif adjudication_unreadiness > config.max_pass_resolution_dispute_risk_score:
        codes.append("adjudication_readiness_watch")
    else:
        codes.append("adjudication_readiness_pass")
    if resolution_dispute_risk_score > config.max_watch_resolution_dispute_risk_score:
        codes.append("resolution_dispute_risk_score_block")
    return tuple(codes)


def _count_reason(
    prefix: str,
    count: Decimal,
    block_count: Decimal,
    component: Decimal,
    pass_threshold: Decimal,
) -> str:
    if count >= block_count:
        return f"{prefix}_block"
    if component > pass_threshold:
        return f"{prefix}_watch"
    return f"{prefix}_pass"


def _component_reason(
    prefix: str,
    component: Decimal,
    pass_threshold: Decimal,
    block_threshold: Decimal,
) -> str:
    if component >= block_threshold:
        return f"{prefix}_block"
    if component > pass_threshold:
        return f"{prefix}_watch"
    return f"{prefix}_pass"


def _validate_config(
    config: CandidateDecisionResolutionDisputeRiskScoreConfig,
) -> None:
    if (
        config.max_pass_resolution_dispute_risk_score
        > config.max_watch_resolution_dispute_risk_score
    ):
        raise ValueError("pass threshold must not exceed watch threshold")
    for field_name in (
        "max_ambiguous_clause_count_for_component",
        "max_subjective_term_count_for_component",
        "max_precedent_dispute_count_for_component",
        "ambiguous_clause_block_count",
        "subjective_term_block_count",
        "precedent_dispute_block_count",
    ):
        if getattr(config, field_name) <= ZERO:
            raise ValueError(f"{field_name} must be positive")
    _validate_weight_sum(
        (
            config.ambiguous_clause_weight,
            config.subjective_term_weight,
            config.precedent_dispute_weight,
            config.source_conflict_weight,
            config.rule_uncertainty_weight,
            config.adjudication_unreadiness_weight,
        ),
    )


def _validate_config_like_report(
    report: CandidateDecisionResolutionDisputeRiskScoreReport,
) -> None:
    if (
        report.max_pass_resolution_dispute_risk_score
        > report.max_watch_resolution_dispute_risk_score
    ):
        raise ValueError("pass threshold must not exceed watch threshold")
    for field_name in (
        "max_ambiguous_clause_count_for_component",
        "max_subjective_term_count_for_component",
        "max_precedent_dispute_count_for_component",
        "ambiguous_clause_block_count",
        "subjective_term_block_count",
        "precedent_dispute_block_count",
    ):
        if getattr(report, field_name) <= ZERO:
            raise ValueError(f"{field_name} must be positive")
    _validate_weight_sum(
        (
            report.ambiguous_clause_weight,
            report.subjective_term_weight,
            report.precedent_dispute_weight,
            report.source_conflict_weight,
            report.rule_uncertainty_weight,
            report.adjudication_unreadiness_weight,
        ),
    )


def _validate_report(
    report: CandidateDecisionResolutionDisputeRiskScoreReport,
) -> None:
    pseudo_input = CandidateDecisionResolutionDisputeRiskScoreInput(
        generated_at=report.generated_at,
        redacted_candidate_ref=report.redacted_candidate_ref,
        ambiguous_clause_count=report.ambiguous_clause_count,
        subjective_term_count=report.subjective_term_count,
        precedent_dispute_count=report.precedent_dispute_count,
        source_conflict_score=report.source_conflict_score,
        rule_clarity_score=report.rule_clarity_score,
        adjudication_readiness_score=report.adjudication_readiness_score,
        reason_codes=_base_reason_codes(report.reason_codes),
    )
    pseudo_config = CandidateDecisionResolutionDisputeRiskScoreConfig(
        config_version=report.config_version,
        max_pass_resolution_dispute_risk_score=(
            report.max_pass_resolution_dispute_risk_score
        ),
        max_watch_resolution_dispute_risk_score=(
            report.max_watch_resolution_dispute_risk_score
        ),
        max_ambiguous_clause_count_for_component=(
            report.max_ambiguous_clause_count_for_component
        ),
        max_subjective_term_count_for_component=(
            report.max_subjective_term_count_for_component
        ),
        max_precedent_dispute_count_for_component=(
            report.max_precedent_dispute_count_for_component
        ),
        ambiguous_clause_block_count=report.ambiguous_clause_block_count,
        subjective_term_block_count=report.subjective_term_block_count,
        precedent_dispute_block_count=report.precedent_dispute_block_count,
        source_conflict_block_score=report.source_conflict_block_score,
        rule_clarity_block_score=report.rule_clarity_block_score,
        adjudication_readiness_block_score=(
            report.adjudication_readiness_block_score
        ),
        ambiguous_clause_weight=report.ambiguous_clause_weight,
        subjective_term_weight=report.subjective_term_weight,
        precedent_dispute_weight=report.precedent_dispute_weight,
        source_conflict_weight=report.source_conflict_weight,
        rule_uncertainty_weight=report.rule_uncertainty_weight,
        adjudication_unreadiness_weight=report.adjudication_unreadiness_weight,
    )
    expected = _report_values(pseudo_input, pseudo_config)
    for field_name in (
        "ambiguous_clause_component",
        "subjective_term_component",
        "precedent_dispute_component",
        "source_conflict_component",
        "rule_uncertainty_component",
        "adjudication_unreadiness_component",
        "resolution_dispute_risk_score",
        "resolution_dispute_risk_status",
        "hard_blocker_codes",
        "reason_codes",
    ):
        if getattr(report, field_name) != expected[field_name]:
            raise ValueError(
                f"{field_name} must match resolution dispute risk calculation",
            )


def _base_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    generated_prefixes = (
        "resolution_dispute_risk_",
        "ambiguous_clause_count_",
        "subjective_term_count_",
        "precedent_dispute_count_",
        "source_conflict_",
        "rule_clarity_",
        "adjudication_readiness_",
    )
    return tuple(
        code
        for code in reason_codes
        if not any(code.startswith(prefix) for prefix in generated_prefixes)
    )


def _validate_weight_sum(weights: tuple[Decimal, ...]) -> None:
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        if sum(weights, ZERO).quantize(QUANTUM, rounding=ROUND_HALF_EVEN) != ONE:
            raise ValueError("weights must sum to one")


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("ratio denominator must be positive")
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        value = numerator / denominator
        if value > ONE:
            return ONE
        if value < ZERO:
            return ZERO
        return value


def _subtract_nonnegative(field_name: str, left: Decimal, right: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        value = left - right
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _quantize_unit(value: Decimal) -> Decimal:
    if value <= ZERO:
        return ZERO
    if value >= ONE:
        return ONE
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        return value.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    decimal = _normalize_decimal(field_name, value)
    if decimal < ZERO or decimal > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal = _normalize_decimal(field_name, value)
    if decimal < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    decimal = _normalize_nonnegative_decimal(field_name, value)
    integral = decimal.quantize(COUNT_QUANTUM, rounding=ROUND_HALF_EVEN)
    if decimal != integral:
        raise ValueError(f"{field_name} must be integral")
    return integral


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        return value.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_redacted_candidate_ref(value: object) -> str:
    if type(value) is not str:
        raise ValueError("redacted_candidate_ref must be a string")
    if not value or value.strip() != value:
        raise ValueError("redacted_candidate_ref must be canonical text")
    prefix = "candidate_ref_"
    digest = value.removeprefix(prefix)
    if not value.startswith(prefix) or len(digest) != 16:
        raise ValueError("redacted_candidate_ref must be redacted")
    if any(character not in "0123456789abcdef" for character in digest):
        raise ValueError("redacted_candidate_ref must be redacted")
    return value


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for item in value:
        normalized.append(_require_reason_code(field_name, item))
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must not be empty")
    if len(tuple(normalized)) != len(set(normalized)):
        raise ValueError(f"{field_name} must not contain duplicates")
    return tuple(normalized)


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    return value


def _require_choice(field_name: str, value: object, choices: tuple[str, ...]) -> None:
    if type(value) is not str or value not in choices:
        raise ValueError(f"{field_name} must be one of {', '.join(choices)}")


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical text")
    return value


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")


def _require_phase_flags(label: str, value: object) -> None:
    require_paper_only_flags(label, value)


def _report_digest(
    report: CandidateDecisionResolutionDisputeRiskScoreReport,
) -> str:
    values = {
        key: value
        for key, value in asdict(report).items()
        if key != "derived_validation_digest"
    }
    payload = json_ready_no_floats(values)
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _reject_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        raise ValueError("public payload must use decimal strings")
    if type(value) is int:
        raise ValueError("public payload must use decimal strings")
    if isinstance(value, float):
        raise ValueError("public payload must use decimal strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numbers(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numbers(item)


def _reject_public_status_aliases(value: object) -> None:
    if type(value) is str:
        if value.lower() in _PUBLIC_STATUS_ALIASES:
            raise ValueError("public status must be pass, watch, or block")
        return
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_status_aliases(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_status_aliases(item)


def _iter_public_strings(value: object, path: str = "") -> tuple[tuple[str, str], ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_public_strings(asdict(value), path)
    if type(value) is str:
        return ((path, value),)
    if isinstance(value, dict):
        strings: list[tuple[str, str]] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            strings.append((nested_path, key))
            strings.extend(_iter_public_strings(item, nested_path))
        return tuple(strings)
    if isinstance(value, (list, tuple)):
        strings = []
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"[{index}]"
            strings.extend(_iter_public_strings(item, nested_path))
        return tuple(strings)
    return ()


__all__ = (
    "DEFAULT_CANDIDATE_DECISION_RESOLUTION_DISPUTE_RISK_SCORE_CONFIG_VERSION",
    "RESOLUTION_DISPUTE_RISK_STATUSES",
    "CandidateDecisionResolutionDisputeRiskScoreConfig",
    "CandidateDecisionResolutionDisputeRiskScoreInput",
    "CandidateDecisionResolutionDisputeRiskScoreReport",
    "build_candidate_decision_resolution_dispute_risk_score_report",
    "candidate_decision_resolution_dispute_risk_score_payload",
    "validate_candidate_decision_resolution_dispute_risk_score_public_payload",
    "reject_candidate_decision_resolution_dispute_risk_score_unsafe_payload",
)
