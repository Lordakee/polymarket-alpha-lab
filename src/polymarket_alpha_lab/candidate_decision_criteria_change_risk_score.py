"""Pure report-only criteria change risk score for candidate decisions."""

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


DEFAULT_CANDIDATE_DECISION_CRITERIA_CHANGE_RISK_SCORE_CONFIG_VERSION = (
    "candidate-decision-criteria-change-risk-score-v0"
)
CRITERIA_CHANGE_RISK_STATUSES = ("pass", "watch", "block")

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
class CandidateDecisionCriteriaChangeRiskScoreConfig:
    config_version: str = (
        DEFAULT_CANDIDATE_DECISION_CRITERIA_CHANGE_RISK_SCORE_CONFIG_VERSION
    )
    max_pass_criteria_change_risk_score: Decimal = Decimal("0.300000")
    max_watch_criteria_change_risk_score: Decimal = Decimal("0.600000")
    max_revision_signal_count_for_component: Decimal = Decimal("4")
    max_conflicting_precedent_count_for_component: Decimal = Decimal("3")
    conflicting_precedent_block_count: Decimal = Decimal("3")
    ambiguous_rule_block_ratio: Decimal = Decimal("0.800000")
    operator_discretion_block_score: Decimal = Decimal("0.750000")
    settlement_source_stability_block_score: Decimal = Decimal("0.250000")
    dispute_channel_activity_block_score: Decimal = Decimal("0.800000")
    revision_signal_weight: Decimal = Decimal("0.150000")
    conflicting_precedent_weight: Decimal = Decimal("0.150000")
    ambiguity_weight: Decimal = Decimal("0.200000")
    operator_discretion_weight: Decimal = Decimal("0.200000")
    source_instability_weight: Decimal = Decimal("0.150000")
    dispute_activity_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionCriteriaChangeRiskScoreConfig:
            raise TypeError(
                "CandidateDecisionCriteriaChangeRiskScoreConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, CandidateDecisionCriteriaChangeRiskScoreConfig)
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_CANDIDATE_DECISION_CRITERIA_CHANGE_RISK_SCORE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported version")
        for field_name in (
            "max_pass_criteria_change_risk_score",
            "max_watch_criteria_change_risk_score",
            "ambiguous_rule_block_ratio",
            "operator_discretion_block_score",
            "settlement_source_stability_block_score",
            "dispute_channel_activity_block_score",
            "revision_signal_weight",
            "conflicting_precedent_weight",
            "ambiguity_weight",
            "operator_discretion_weight",
            "source_instability_weight",
            "dispute_activity_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_revision_signal_count_for_component",
            "max_conflicting_precedent_count_for_component",
            "conflicting_precedent_block_count",
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
        reject_candidate_decision_criteria_change_risk_score_unsafe_payload(
            "criteria change risk config",
            self,
        )


@dataclass(frozen=True)
class CandidateDecisionCriteriaChangeRiskScoreInput:
    generated_at: datetime
    redacted_candidate_ref: str
    criteria_revision_signal_count: Decimal
    conflicting_resolution_precedent_count: Decimal
    ambiguous_rule_clause_ratio: Decimal
    operator_discretion_score: Decimal
    settlement_source_stability_score: Decimal
    dispute_channel_activity_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionCriteriaChangeRiskScoreInput:
            raise TypeError(
                "CandidateDecisionCriteriaChangeRiskScoreInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("input", self, CandidateDecisionCriteriaChangeRiskScoreInput)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "redacted_candidate_ref",
            _require_redacted_candidate_ref(self.redacted_candidate_ref),
        )
        for field_name in (
            "criteria_revision_signal_count",
            "conflicting_resolution_precedent_count",
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
            "ambiguous_rule_clause_ratio",
            "operator_discretion_score",
            "settlement_source_stability_score",
            "dispute_channel_activity_score",
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
        reject_candidate_decision_criteria_change_risk_score_unsafe_payload(
            "criteria change risk input",
            self,
        )


@dataclass(frozen=True)
class CandidateDecisionCriteriaChangeRiskScoreReport:
    generated_at: datetime
    config_version: str
    max_pass_criteria_change_risk_score: Decimal
    max_watch_criteria_change_risk_score: Decimal
    max_revision_signal_count_for_component: Decimal
    max_conflicting_precedent_count_for_component: Decimal
    conflicting_precedent_block_count: Decimal
    ambiguous_rule_block_ratio: Decimal
    operator_discretion_block_score: Decimal
    settlement_source_stability_block_score: Decimal
    dispute_channel_activity_block_score: Decimal
    revision_signal_weight: Decimal
    conflicting_precedent_weight: Decimal
    ambiguity_weight: Decimal
    operator_discretion_weight: Decimal
    source_instability_weight: Decimal
    dispute_activity_weight: Decimal
    redacted_candidate_ref: str
    criteria_revision_signal_count: Decimal
    conflicting_resolution_precedent_count: Decimal
    ambiguous_rule_clause_ratio: Decimal
    operator_discretion_score: Decimal
    settlement_source_stability_score: Decimal
    dispute_channel_activity_score: Decimal
    criteria_revision_component: Decimal
    conflicting_precedent_component: Decimal
    ambiguity_component: Decimal
    operator_discretion_component: Decimal
    source_instability_component: Decimal
    dispute_activity_component: Decimal
    criteria_change_risk_score: Decimal
    criteria_change_risk_status: str
    hard_blocker_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionCriteriaChangeRiskScoreReport:
            raise TypeError(
                "CandidateDecisionCriteriaChangeRiskScoreReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, CandidateDecisionCriteriaChangeRiskScoreReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_CANDIDATE_DECISION_CRITERIA_CHANGE_RISK_SCORE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported version")
        object.__setattr__(
            self,
            "redacted_candidate_ref",
            _require_redacted_candidate_ref(self.redacted_candidate_ref),
        )
        for field_name in (
            "max_pass_criteria_change_risk_score",
            "max_watch_criteria_change_risk_score",
            "ambiguous_rule_block_ratio",
            "operator_discretion_block_score",
            "settlement_source_stability_block_score",
            "dispute_channel_activity_block_score",
            "revision_signal_weight",
            "conflicting_precedent_weight",
            "ambiguity_weight",
            "operator_discretion_weight",
            "source_instability_weight",
            "dispute_activity_weight",
            "ambiguous_rule_clause_ratio",
            "operator_discretion_score",
            "settlement_source_stability_score",
            "dispute_channel_activity_score",
            "criteria_revision_component",
            "conflicting_precedent_component",
            "ambiguity_component",
            "operator_discretion_component",
            "source_instability_component",
            "dispute_activity_component",
            "criteria_change_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_revision_signal_count_for_component",
            "max_conflicting_precedent_count_for_component",
            "conflicting_precedent_block_count",
            "criteria_revision_signal_count",
            "conflicting_resolution_precedent_count",
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
            "criteria_change_risk_status",
            self.criteria_change_risk_status,
            CRITERIA_CHANGE_RISK_STATUSES,
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
        reject_candidate_decision_criteria_change_risk_score_unsafe_payload(
            "criteria change risk report",
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
        return candidate_decision_criteria_change_risk_score_payload(self)


def build_candidate_decision_criteria_change_risk_score_report(
    score_input: CandidateDecisionCriteriaChangeRiskScoreInput,
    *,
    config: CandidateDecisionCriteriaChangeRiskScoreConfig | None = None,
) -> CandidateDecisionCriteriaChangeRiskScoreReport:
    if type(score_input) is not CandidateDecisionCriteriaChangeRiskScoreInput:
        raise ValueError(
            "score_input must be a CandidateDecisionCriteriaChangeRiskScoreInput",
        )
    report_config = config or CandidateDecisionCriteriaChangeRiskScoreConfig()
    if type(report_config) is not CandidateDecisionCriteriaChangeRiskScoreConfig:
        raise ValueError(
            "config must be a CandidateDecisionCriteriaChangeRiskScoreConfig",
        )
    _require_phase_flags("input", score_input)
    _require_phase_flags("config", report_config)
    reject_candidate_decision_criteria_change_risk_score_unsafe_payload(
        "criteria change risk input",
        score_input,
    )
    reject_candidate_decision_criteria_change_risk_score_unsafe_payload(
        "criteria change risk config",
        report_config,
    )
    return CandidateDecisionCriteriaChangeRiskScoreReport(
        **_report_values(score_input, report_config),
    )


def candidate_decision_criteria_change_risk_score_payload(
    report: CandidateDecisionCriteriaChangeRiskScoreReport,
) -> dict[str, Any]:
    if type(report) is not CandidateDecisionCriteriaChangeRiskScoreReport:
        raise ValueError(
            "report must be a CandidateDecisionCriteriaChangeRiskScoreReport",
        )
    _require_phase_flags("report", report)
    _validate_report(report)
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest must match report fields")
    reject_candidate_decision_criteria_change_risk_score_unsafe_payload(
        "criteria change risk report",
        report,
    )
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    validate_candidate_decision_criteria_change_risk_score_public_payload(payload)
    return payload


def validate_candidate_decision_criteria_change_risk_score_public_payload(
    payload: object,
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_public_numbers(payload)
    _reject_public_status_aliases(payload)
    reject_candidate_decision_criteria_change_risk_score_unsafe_payload(
        "criteria change risk public payload",
        payload,
    )


def reject_candidate_decision_criteria_change_risk_score_unsafe_payload(
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
    score_input: CandidateDecisionCriteriaChangeRiskScoreInput,
    config: CandidateDecisionCriteriaChangeRiskScoreConfig,
) -> dict[str, object]:
    criteria_revision_component_raw = _ratio(
        score_input.criteria_revision_signal_count,
        config.max_revision_signal_count_for_component,
    )
    conflicting_precedent_component_raw = _ratio(
        score_input.conflicting_resolution_precedent_count,
        config.max_conflicting_precedent_count_for_component,
    )
    source_instability_component_raw = _subtract_nonnegative(
        "source_instability_component",
        ONE,
        score_input.settlement_source_stability_score,
    )
    score = _weighted_score(
        criteria_revision_component_raw,
        conflicting_precedent_component_raw,
        score_input.ambiguous_rule_clause_ratio,
        score_input.operator_discretion_score,
        source_instability_component_raw,
        score_input.dispute_channel_activity_score,
        config,
    )
    hard_blockers = _hard_blocker_codes(score_input, score, config)
    status = _status(score, hard_blockers, config)
    reason_codes = _reason_codes(score_input, score, status, config)
    return {
        "generated_at": score_input.generated_at,
        "config_version": config.config_version,
        "max_pass_criteria_change_risk_score": (
            config.max_pass_criteria_change_risk_score
        ),
        "max_watch_criteria_change_risk_score": (
            config.max_watch_criteria_change_risk_score
        ),
        "max_revision_signal_count_for_component": (
            config.max_revision_signal_count_for_component
        ),
        "max_conflicting_precedent_count_for_component": (
            config.max_conflicting_precedent_count_for_component
        ),
        "conflicting_precedent_block_count": config.conflicting_precedent_block_count,
        "ambiguous_rule_block_ratio": config.ambiguous_rule_block_ratio,
        "operator_discretion_block_score": config.operator_discretion_block_score,
        "settlement_source_stability_block_score": (
            config.settlement_source_stability_block_score
        ),
        "dispute_channel_activity_block_score": (
            config.dispute_channel_activity_block_score
        ),
        "revision_signal_weight": config.revision_signal_weight,
        "conflicting_precedent_weight": config.conflicting_precedent_weight,
        "ambiguity_weight": config.ambiguity_weight,
        "operator_discretion_weight": config.operator_discretion_weight,
        "source_instability_weight": config.source_instability_weight,
        "dispute_activity_weight": config.dispute_activity_weight,
        "redacted_candidate_ref": score_input.redacted_candidate_ref,
        "criteria_revision_signal_count": score_input.criteria_revision_signal_count,
        "conflicting_resolution_precedent_count": (
            score_input.conflicting_resolution_precedent_count
        ),
        "ambiguous_rule_clause_ratio": score_input.ambiguous_rule_clause_ratio,
        "operator_discretion_score": score_input.operator_discretion_score,
        "settlement_source_stability_score": (
            score_input.settlement_source_stability_score
        ),
        "dispute_channel_activity_score": score_input.dispute_channel_activity_score,
        "criteria_revision_component": _quantize_unit(criteria_revision_component_raw),
        "conflicting_precedent_component": _quantize_unit(
            conflicting_precedent_component_raw,
        ),
        "ambiguity_component": score_input.ambiguous_rule_clause_ratio,
        "operator_discretion_component": score_input.operator_discretion_score,
        "source_instability_component": _quantize_unit(
            source_instability_component_raw,
        ),
        "dispute_activity_component": score_input.dispute_channel_activity_score,
        "criteria_change_risk_score": score,
        "criteria_change_risk_status": status,
        "hard_blocker_codes": hard_blockers,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _weighted_score(
    criteria_revision_component: Decimal,
    conflicting_precedent_component: Decimal,
    ambiguity_component: Decimal,
    operator_discretion_component: Decimal,
    source_instability_component: Decimal,
    dispute_activity_component: Decimal,
    config: CandidateDecisionCriteriaChangeRiskScoreConfig,
) -> Decimal:
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        weighted = (
            criteria_revision_component * config.revision_signal_weight
            + conflicting_precedent_component * config.conflicting_precedent_weight
            + ambiguity_component * config.ambiguity_weight
            + operator_discretion_component * config.operator_discretion_weight
            + source_instability_component * config.source_instability_weight
            + dispute_activity_component * config.dispute_activity_weight
        )
        return _quantize_unit(weighted)


def _hard_blocker_codes(
    score_input: CandidateDecisionCriteriaChangeRiskScoreInput,
    criteria_change_risk_score: Decimal,
    config: CandidateDecisionCriteriaChangeRiskScoreConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if (
        score_input.conflicting_resolution_precedent_count
        >= config.conflicting_precedent_block_count
    ):
        codes.append("conflicting_precedent_block")
    if score_input.ambiguous_rule_clause_ratio >= config.ambiguous_rule_block_ratio:
        codes.append("ambiguous_rule_clause_block")
    if score_input.operator_discretion_score >= config.operator_discretion_block_score:
        codes.append("operator_discretion_block")
    if (
        score_input.settlement_source_stability_score
        <= config.settlement_source_stability_block_score
    ):
        codes.append("settlement_source_stability_block")
    if (
        score_input.dispute_channel_activity_score
        >= config.dispute_channel_activity_block_score
    ):
        codes.append("dispute_channel_activity_block")
    if criteria_change_risk_score > config.max_watch_criteria_change_risk_score:
        codes.append("criteria_change_risk_score_block")
    return tuple(codes)


def _status(
    criteria_change_risk_score: Decimal,
    hard_blocker_codes: tuple[str, ...],
    config: CandidateDecisionCriteriaChangeRiskScoreConfig,
) -> str:
    if (
        hard_blocker_codes
        or criteria_change_risk_score > config.max_watch_criteria_change_risk_score
    ):
        return "block"
    if criteria_change_risk_score > config.max_pass_criteria_change_risk_score:
        return "watch"
    return "pass"


def _reason_codes(
    score_input: CandidateDecisionCriteriaChangeRiskScoreInput,
    criteria_change_risk_score: Decimal,
    status: str,
    config: CandidateDecisionCriteriaChangeRiskScoreConfig,
) -> tuple[str, ...]:
    codes = list(score_input.reason_codes)
    codes.append(f"criteria_change_risk_{status}")
    codes.append(
        _component_reason(
            "criteria_revision_signals",
            _ratio(
                score_input.criteria_revision_signal_count,
                config.max_revision_signal_count_for_component,
            ),
            config.max_pass_criteria_change_risk_score,
        ),
    )
    codes.append(
        _component_reason(
            "conflicting_precedent",
            _ratio(
                score_input.conflicting_resolution_precedent_count,
                config.max_conflicting_precedent_count_for_component,
            ),
            config.max_pass_criteria_change_risk_score,
            config.conflicting_precedent_block_count,
            score_input.conflicting_resolution_precedent_count,
        ),
    )
    codes.append(
        _component_reason(
            "ambiguous_rule_clause",
            score_input.ambiguous_rule_clause_ratio,
            config.max_pass_criteria_change_risk_score,
            config.ambiguous_rule_block_ratio,
        ),
    )
    codes.append(
        _component_reason(
            "operator_discretion",
            score_input.operator_discretion_score,
            config.max_pass_criteria_change_risk_score,
            config.operator_discretion_block_score,
        ),
    )
    source_instability = _subtract_nonnegative(
        "source_instability_component",
        ONE,
        score_input.settlement_source_stability_score,
    )
    if (
        score_input.settlement_source_stability_score
        <= config.settlement_source_stability_block_score
    ):
        codes.append("settlement_source_stability_block")
    elif source_instability > config.max_pass_criteria_change_risk_score:
        codes.append("settlement_source_stability_watch")
    else:
        codes.append("settlement_source_stability_pass")
    codes.append(
        _component_reason(
            "dispute_channel_activity",
            score_input.dispute_channel_activity_score,
            config.max_pass_criteria_change_risk_score,
            config.dispute_channel_activity_block_score,
        ),
    )
    if criteria_change_risk_score > config.max_watch_criteria_change_risk_score:
        codes.append("criteria_change_risk_score_block")
    return tuple(codes)


def _component_reason(
    prefix: str,
    component: Decimal,
    pass_threshold: Decimal,
    block_threshold: Decimal | None = None,
    raw_count: Decimal | None = None,
) -> str:
    if block_threshold is not None:
        block_value = component if raw_count is None else raw_count
        if block_value >= block_threshold:
            return f"{prefix}_block"
    if component > pass_threshold:
        return f"{prefix}_watch"
    return f"{prefix}_pass"


def _validate_config(config: CandidateDecisionCriteriaChangeRiskScoreConfig) -> None:
    if (
        config.max_pass_criteria_change_risk_score
        > config.max_watch_criteria_change_risk_score
    ):
        raise ValueError("pass threshold must not exceed watch threshold")
    if config.max_revision_signal_count_for_component <= ZERO:
        raise ValueError("max_revision_signal_count_for_component must be positive")
    if config.max_conflicting_precedent_count_for_component <= ZERO:
        raise ValueError(
            "max_conflicting_precedent_count_for_component must be positive",
        )
    if config.conflicting_precedent_block_count <= ZERO:
        raise ValueError("conflicting_precedent_block_count must be positive")
    if (
        config.conflicting_precedent_block_count
        > config.max_conflicting_precedent_count_for_component
    ):
        raise ValueError("block count must not exceed component max")
    _validate_weight_sum(
        (
            config.revision_signal_weight,
            config.conflicting_precedent_weight,
            config.ambiguity_weight,
            config.operator_discretion_weight,
            config.source_instability_weight,
            config.dispute_activity_weight,
        ),
    )


def _validate_config_like_report(
    report: CandidateDecisionCriteriaChangeRiskScoreReport,
) -> None:
    if (
        report.max_pass_criteria_change_risk_score
        > report.max_watch_criteria_change_risk_score
    ):
        raise ValueError("pass threshold must not exceed watch threshold")
    if report.max_revision_signal_count_for_component <= ZERO:
        raise ValueError("max_revision_signal_count_for_component must be positive")
    if report.max_conflicting_precedent_count_for_component <= ZERO:
        raise ValueError(
            "max_conflicting_precedent_count_for_component must be positive",
        )
    if report.conflicting_precedent_block_count <= ZERO:
        raise ValueError("conflicting_precedent_block_count must be positive")
    if (
        report.conflicting_precedent_block_count
        > report.max_conflicting_precedent_count_for_component
    ):
        raise ValueError("block count must not exceed component max")
    _validate_weight_sum(
        (
            report.revision_signal_weight,
            report.conflicting_precedent_weight,
            report.ambiguity_weight,
            report.operator_discretion_weight,
            report.source_instability_weight,
            report.dispute_activity_weight,
        ),
    )


def _validate_report(report: CandidateDecisionCriteriaChangeRiskScoreReport) -> None:
    pseudo_input = CandidateDecisionCriteriaChangeRiskScoreInput(
        generated_at=report.generated_at,
        redacted_candidate_ref=report.redacted_candidate_ref,
        criteria_revision_signal_count=report.criteria_revision_signal_count,
        conflicting_resolution_precedent_count=(
            report.conflicting_resolution_precedent_count
        ),
        ambiguous_rule_clause_ratio=report.ambiguous_rule_clause_ratio,
        operator_discretion_score=report.operator_discretion_score,
        settlement_source_stability_score=report.settlement_source_stability_score,
        dispute_channel_activity_score=report.dispute_channel_activity_score,
        reason_codes=_base_reason_codes(report.reason_codes),
    )
    pseudo_config = CandidateDecisionCriteriaChangeRiskScoreConfig(
        config_version=report.config_version,
        max_pass_criteria_change_risk_score=(
            report.max_pass_criteria_change_risk_score
        ),
        max_watch_criteria_change_risk_score=(
            report.max_watch_criteria_change_risk_score
        ),
        max_revision_signal_count_for_component=(
            report.max_revision_signal_count_for_component
        ),
        max_conflicting_precedent_count_for_component=(
            report.max_conflicting_precedent_count_for_component
        ),
        conflicting_precedent_block_count=report.conflicting_precedent_block_count,
        ambiguous_rule_block_ratio=report.ambiguous_rule_block_ratio,
        operator_discretion_block_score=report.operator_discretion_block_score,
        settlement_source_stability_block_score=(
            report.settlement_source_stability_block_score
        ),
        dispute_channel_activity_block_score=(
            report.dispute_channel_activity_block_score
        ),
        revision_signal_weight=report.revision_signal_weight,
        conflicting_precedent_weight=report.conflicting_precedent_weight,
        ambiguity_weight=report.ambiguity_weight,
        operator_discretion_weight=report.operator_discretion_weight,
        source_instability_weight=report.source_instability_weight,
        dispute_activity_weight=report.dispute_activity_weight,
    )
    expected = _report_values(pseudo_input, pseudo_config)
    for field_name in (
        "criteria_revision_component",
        "conflicting_precedent_component",
        "ambiguity_component",
        "operator_discretion_component",
        "source_instability_component",
        "dispute_activity_component",
        "criteria_change_risk_score",
        "criteria_change_risk_status",
        "hard_blocker_codes",
        "reason_codes",
    ):
        if getattr(report, field_name) != expected[field_name]:
            raise ValueError(f"{field_name} must match criteria change risk calculation")


def _base_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    generated_prefixes = (
        "criteria_change_risk_",
        "criteria_revision_signals_",
        "conflicting_precedent_",
        "ambiguous_rule_clause_",
        "operator_discretion_",
        "settlement_source_stability_",
        "dispute_channel_activity_",
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


def _report_digest(report: CandidateDecisionCriteriaChangeRiskScoreReport) -> str:
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
    "DEFAULT_CANDIDATE_DECISION_CRITERIA_CHANGE_RISK_SCORE_CONFIG_VERSION",
    "CRITERIA_CHANGE_RISK_STATUSES",
    "CandidateDecisionCriteriaChangeRiskScoreConfig",
    "CandidateDecisionCriteriaChangeRiskScoreInput",
    "CandidateDecisionCriteriaChangeRiskScoreReport",
    "build_candidate_decision_criteria_change_risk_score_report",
    "candidate_decision_criteria_change_risk_score_payload",
    "validate_candidate_decision_criteria_change_risk_score_public_payload",
    "reject_candidate_decision_criteria_change_risk_score_unsafe_payload",
)
