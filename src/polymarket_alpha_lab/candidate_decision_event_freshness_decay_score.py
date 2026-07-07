"""Pure report-only event freshness decay score for candidate decisions."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_CANDIDATE_DECISION_EVENT_FRESHNESS_DECAY_SCORE_CONFIG_VERSION = (
    "candidate-decision-event-freshness-decay-score-v0"
)
EVENT_FRESHNESS_STATUSES = ("pass", "watch", "block")

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
EVENT_AGE_FINAL_WEIGHT = Decimal("0.250000")
RESEARCH_FINAL_WEIGHT = Decimal("0.750000")
DECIMAL_CONTEXT_PRECISION = 64

_RAW_MARKET_PUBLIC_TERMS = (
    "candidate_id",
    "candidate_slug",
    "condition_id",
    "market_id",
    "market_slug",
    "question",
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
class CandidateDecisionEventFreshnessDecayScoreConfig:
    config_version: str = (
        DEFAULT_CANDIDATE_DECISION_EVENT_FRESHNESS_DECAY_SCORE_CONFIG_VERSION
    )
    min_pass_event_freshness_decay_score: Decimal = Decimal("0.750000")
    min_watch_event_freshness_decay_score: Decimal = Decimal("0.500000")
    max_pass_latest_event_age_minutes: Decimal = Decimal("60.000000")
    max_watch_latest_event_age_minutes: Decimal = Decimal("240.000000")
    source_freshness_weight: Decimal = Decimal("0.250000")
    event_relevance_weight: Decimal = Decimal("0.250000")
    stale_context_weight: Decimal = Decimal("0.200000")
    update_frequency_weight: Decimal = Decimal("0.150000")
    evidence_quality_weight: Decimal = Decimal("0.150000")
    min_pass_source_freshness_score: Decimal = Decimal("0.700000")
    min_watch_source_freshness_score: Decimal = Decimal("0.400000")
    min_pass_event_relevance_score: Decimal = Decimal("0.700000")
    min_watch_event_relevance_score: Decimal = Decimal("0.400000")
    max_pass_stale_context_score: Decimal = Decimal("0.300000")
    max_watch_stale_context_score: Decimal = Decimal("0.700000")
    min_pass_update_frequency_score: Decimal = Decimal("0.600000")
    min_watch_update_frequency_score: Decimal = Decimal("0.300000")
    min_pass_evidence_quality_score: Decimal = Decimal("0.700000")
    min_watch_evidence_quality_score: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionEventFreshnessDecayScoreConfig:
            raise TypeError(
                "CandidateDecisionEventFreshnessDecayScoreConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            CandidateDecisionEventFreshnessDecayScoreConfig,
        )
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_CANDIDATE_DECISION_EVENT_FRESHNESS_DECAY_SCORE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported version")
        for field_name in (
            "min_pass_event_freshness_decay_score",
            "min_watch_event_freshness_decay_score",
            "source_freshness_weight",
            "event_relevance_weight",
            "stale_context_weight",
            "update_frequency_weight",
            "evidence_quality_weight",
            "min_pass_source_freshness_score",
            "min_watch_source_freshness_score",
            "min_pass_event_relevance_score",
            "min_watch_event_relevance_score",
            "max_pass_stale_context_score",
            "max_watch_stale_context_score",
            "min_pass_update_frequency_score",
            "min_watch_update_frequency_score",
            "min_pass_evidence_quality_score",
            "min_watch_evidence_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_latest_event_age_minutes",
            "max_watch_latest_event_age_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_phase_flags("config", self)
        reject_candidate_decision_event_freshness_decay_score_unsafe_payload(
            "event freshness decay config",
            self,
        )


@dataclass(frozen=True)
class CandidateDecisionEventFreshnessDecayScoreInput:
    redacted_candidate_ref: str
    latest_event_age_minutes: Decimal
    source_freshness_score: Decimal
    event_relevance_score: Decimal
    stale_context_score: Decimal
    update_frequency_score: Decimal
    evidence_quality_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionEventFreshnessDecayScoreInput:
            raise TypeError(
                "CandidateDecisionEventFreshnessDecayScoreInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "input",
            self,
            CandidateDecisionEventFreshnessDecayScoreInput,
        )
        object.__setattr__(
            self,
            "redacted_candidate_ref",
            _require_canonical_string("redacted_candidate_ref", self.redacted_candidate_ref),
        )
        object.__setattr__(
            self,
            "latest_event_age_minutes",
            _normalize_nonnegative_decimal(
                "latest_event_age_minutes",
                self.latest_event_age_minutes,
            ),
        )
        for field_name in (
            "source_freshness_score",
            "event_relevance_score",
            "stale_context_score",
            "update_frequency_score",
            "evidence_quality_score",
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
        reject_candidate_decision_event_freshness_decay_score_unsafe_payload(
            "event freshness decay input",
            self,
        )


@dataclass(frozen=True)
class CandidateDecisionEventFreshnessDecayScoreReport:
    config_version: str
    min_pass_event_freshness_decay_score: Decimal
    min_watch_event_freshness_decay_score: Decimal
    max_pass_latest_event_age_minutes: Decimal
    max_watch_latest_event_age_minutes: Decimal
    source_freshness_weight: Decimal
    event_relevance_weight: Decimal
    stale_context_weight: Decimal
    update_frequency_weight: Decimal
    evidence_quality_weight: Decimal
    min_pass_source_freshness_score: Decimal
    min_watch_source_freshness_score: Decimal
    min_pass_event_relevance_score: Decimal
    min_watch_event_relevance_score: Decimal
    max_pass_stale_context_score: Decimal
    max_watch_stale_context_score: Decimal
    min_pass_update_frequency_score: Decimal
    min_watch_update_frequency_score: Decimal
    min_pass_evidence_quality_score: Decimal
    min_watch_evidence_quality_score: Decimal
    redacted_candidate_ref: str
    latest_event_age_minutes: Decimal
    source_freshness_score: Decimal
    event_relevance_score: Decimal
    stale_context_score: Decimal
    update_frequency_score: Decimal
    evidence_quality_score: Decimal
    event_age_component: Decimal
    source_freshness_component: Decimal
    event_relevance_component: Decimal
    stale_context_component: Decimal
    update_frequency_component: Decimal
    evidence_quality_component: Decimal
    event_freshness_decay_score: Decimal
    event_freshness_status: str
    hard_flag_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionEventFreshnessDecayScoreReport:
            raise TypeError(
                "CandidateDecisionEventFreshnessDecayScoreReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "report",
            self,
            CandidateDecisionEventFreshnessDecayScoreReport,
        )
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_CANDIDATE_DECISION_EVENT_FRESHNESS_DECAY_SCORE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported version")
        object.__setattr__(
            self,
            "redacted_candidate_ref",
            _require_canonical_string("redacted_candidate_ref", self.redacted_candidate_ref),
        )
        for field_name in (
            "min_pass_event_freshness_decay_score",
            "min_watch_event_freshness_decay_score",
            "source_freshness_weight",
            "event_relevance_weight",
            "stale_context_weight",
            "update_frequency_weight",
            "evidence_quality_weight",
            "min_pass_source_freshness_score",
            "min_watch_source_freshness_score",
            "min_pass_event_relevance_score",
            "min_watch_event_relevance_score",
            "max_pass_stale_context_score",
            "max_watch_stale_context_score",
            "min_pass_update_frequency_score",
            "min_watch_update_frequency_score",
            "min_pass_evidence_quality_score",
            "min_watch_evidence_quality_score",
            "source_freshness_score",
            "event_relevance_score",
            "stale_context_score",
            "update_frequency_score",
            "evidence_quality_score",
            "event_age_component",
            "source_freshness_component",
            "event_relevance_component",
            "stale_context_component",
            "update_frequency_component",
            "evidence_quality_component",
            "event_freshness_decay_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_latest_event_age_minutes",
            "max_watch_latest_event_age_minutes",
            "latest_event_age_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_choice(
            "event_freshness_status",
            self.event_freshness_status,
            EVENT_FRESHNESS_STATUSES,
        )
        object.__setattr__(
            self,
            "hard_flag_codes",
            _normalize_reason_codes("hard_flag_codes", self.hard_flag_codes, allow_empty=True),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _validate_report(self)
        _require_phase_flags("report", self)
        reject_candidate_decision_event_freshness_decay_score_unsafe_payload(
            "event freshness decay report",
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
        return candidate_decision_event_freshness_decay_score_payload(self)


def build_candidate_decision_event_freshness_decay_score_report(
    score_input: CandidateDecisionEventFreshnessDecayScoreInput,
    *,
    config: CandidateDecisionEventFreshnessDecayScoreConfig | None = None,
) -> CandidateDecisionEventFreshnessDecayScoreReport:
    if type(score_input) is not CandidateDecisionEventFreshnessDecayScoreInput:
        raise ValueError(
            "score_input must be a CandidateDecisionEventFreshnessDecayScoreInput",
        )
    report_config = config or CandidateDecisionEventFreshnessDecayScoreConfig()
    if type(report_config) is not CandidateDecisionEventFreshnessDecayScoreConfig:
        raise ValueError(
            "config must be a CandidateDecisionEventFreshnessDecayScoreConfig",
        )
    _require_phase_flags("input", score_input)
    _require_phase_flags("config", report_config)
    reject_candidate_decision_event_freshness_decay_score_unsafe_payload(
        "event freshness decay input",
        score_input,
    )
    reject_candidate_decision_event_freshness_decay_score_unsafe_payload(
        "event freshness decay config",
        report_config,
    )
    return CandidateDecisionEventFreshnessDecayScoreReport(
        **_report_values(score_input, report_config),
    )


def candidate_decision_event_freshness_decay_score_payload(
    report: CandidateDecisionEventFreshnessDecayScoreReport,
) -> dict[str, Any]:
    if type(report) is not CandidateDecisionEventFreshnessDecayScoreReport:
        raise ValueError(
            "report must be a CandidateDecisionEventFreshnessDecayScoreReport",
        )
    _require_phase_flags("report", report)
    _validate_report(report)
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest must match report fields")
    reject_candidate_decision_event_freshness_decay_score_unsafe_payload(
        "event freshness decay report",
        report,
    )
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    validate_candidate_decision_event_freshness_decay_score_public_payload(payload)
    return payload


def validate_candidate_decision_event_freshness_decay_score_public_payload(
    payload: object,
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_public_numbers(payload)
    _reject_public_status_aliases(payload)
    reject_candidate_decision_event_freshness_decay_score_unsafe_payload(
        "event freshness decay public payload",
        payload,
    )


def reject_candidate_decision_event_freshness_decay_score_unsafe_payload(
    label: str,
    payload: object,
) -> None:
    for path, item in _iter_public_strings(payload):
        lowered = item.lower()
        if any(term in lowered for term in _RAW_MARKET_PUBLIC_TERMS):
            raise ValueError(f"raw market public payload entry in {label}: {path}")
        if any(term in lowered for term in _SOURCE_REFERENCE_PUBLIC_TERMS):
            raise ValueError(f"source refs public payload entry in {label}: {path}")
        if any(term in lowered for term in _UNSAFE_LIVE_PUBLIC_TERMS):
            raise ValueError(f"unsafe live surface public payload entry in {label}: {path}")


def _report_values(
    score_input: CandidateDecisionEventFreshnessDecayScoreInput,
    config: CandidateDecisionEventFreshnessDecayScoreConfig,
) -> dict[str, object]:
    event_age_component = _age_component(
        score_input.latest_event_age_minutes,
        config.max_pass_latest_event_age_minutes,
        config.max_watch_latest_event_age_minutes,
    )
    source_freshness_component = _minimum_score_component(
        score_input.source_freshness_score,
        config.min_watch_source_freshness_score,
        config.min_pass_source_freshness_score,
    )
    event_relevance_component = _minimum_score_component(
        score_input.event_relevance_score,
        config.min_watch_event_relevance_score,
        config.min_pass_event_relevance_score,
    )
    stale_context_component = _maximum_score_component(
        score_input.stale_context_score,
        config.max_pass_stale_context_score,
        config.max_watch_stale_context_score,
    )
    update_frequency_component = _minimum_score_component(
        score_input.update_frequency_score,
        config.min_watch_update_frequency_score,
        config.min_pass_update_frequency_score,
    )
    evidence_quality_component = _minimum_score_component(
        score_input.evidence_quality_score,
        config.min_watch_evidence_quality_score,
        config.min_pass_evidence_quality_score,
    )
    event_freshness_decay_score = _event_freshness_decay_score(
        event_age_component,
        source_freshness_component,
        event_relevance_component,
        stale_context_component,
        update_frequency_component,
        evidence_quality_component,
        config,
    )
    hard_flags = _hard_flag_codes(
        score_input.latest_event_age_minutes,
        score_input.source_freshness_score,
        score_input.event_relevance_score,
        score_input.stale_context_score,
        score_input.update_frequency_score,
        score_input.evidence_quality_score,
        event_freshness_decay_score,
        config,
    )
    event_freshness_status = _event_freshness_status(
        event_freshness_decay_score,
        hard_flags,
        config,
    )
    reason_codes = _reason_codes(
        score_input.reason_codes,
        score_input.latest_event_age_minutes,
        score_input.source_freshness_score,
        score_input.event_relevance_score,
        score_input.stale_context_score,
        score_input.update_frequency_score,
        score_input.evidence_quality_score,
        event_freshness_decay_score,
        event_freshness_status,
        config,
    )
    return {
        "config_version": config.config_version,
        "min_pass_event_freshness_decay_score": config.min_pass_event_freshness_decay_score,
        "min_watch_event_freshness_decay_score": config.min_watch_event_freshness_decay_score,
        "max_pass_latest_event_age_minutes": config.max_pass_latest_event_age_minutes,
        "max_watch_latest_event_age_minutes": config.max_watch_latest_event_age_minutes,
        "source_freshness_weight": config.source_freshness_weight,
        "event_relevance_weight": config.event_relevance_weight,
        "stale_context_weight": config.stale_context_weight,
        "update_frequency_weight": config.update_frequency_weight,
        "evidence_quality_weight": config.evidence_quality_weight,
        "min_pass_source_freshness_score": config.min_pass_source_freshness_score,
        "min_watch_source_freshness_score": config.min_watch_source_freshness_score,
        "min_pass_event_relevance_score": config.min_pass_event_relevance_score,
        "min_watch_event_relevance_score": config.min_watch_event_relevance_score,
        "max_pass_stale_context_score": config.max_pass_stale_context_score,
        "max_watch_stale_context_score": config.max_watch_stale_context_score,
        "min_pass_update_frequency_score": config.min_pass_update_frequency_score,
        "min_watch_update_frequency_score": config.min_watch_update_frequency_score,
        "min_pass_evidence_quality_score": config.min_pass_evidence_quality_score,
        "min_watch_evidence_quality_score": config.min_watch_evidence_quality_score,
        "redacted_candidate_ref": score_input.redacted_candidate_ref,
        "latest_event_age_minutes": score_input.latest_event_age_minutes,
        "source_freshness_score": score_input.source_freshness_score,
        "event_relevance_score": score_input.event_relevance_score,
        "stale_context_score": score_input.stale_context_score,
        "update_frequency_score": score_input.update_frequency_score,
        "evidence_quality_score": score_input.evidence_quality_score,
        "event_age_component": event_age_component,
        "source_freshness_component": source_freshness_component,
        "event_relevance_component": event_relevance_component,
        "stale_context_component": stale_context_component,
        "update_frequency_component": update_frequency_component,
        "evidence_quality_component": evidence_quality_component,
        "event_freshness_decay_score": event_freshness_decay_score,
        "event_freshness_status": event_freshness_status,
        "hard_flag_codes": hard_flags,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _age_component(
    age_minutes: Decimal,
    pass_age_minutes: Decimal,
    watch_age_minutes: Decimal,
) -> Decimal:
    if age_minutes <= pass_age_minutes:
        return ONE
    if age_minutes >= watch_age_minutes:
        return ZERO
    numerator = _subtract_nonnegative("age_component_numerator", watch_age_minutes, age_minutes)
    denominator = _subtract_nonnegative(
        "age_component_denominator",
        watch_age_minutes,
        pass_age_minutes,
    )
    return _safe_unit_ratio(numerator, denominator)


def _minimum_score_component(
    value: Decimal,
    watch_threshold: Decimal,
    pass_threshold: Decimal,
) -> Decimal:
    if value >= pass_threshold:
        return ONE
    if value < watch_threshold:
        return ZERO
    numerator = _subtract_nonnegative("score_component_numerator", value, watch_threshold)
    denominator = _subtract_nonnegative(
        "score_component_denominator",
        pass_threshold,
        watch_threshold,
    )
    return _safe_unit_ratio(numerator, denominator)


def _maximum_score_component(
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> Decimal:
    if value <= pass_threshold:
        return ONE
    if value > watch_threshold:
        return ZERO
    numerator = _subtract_nonnegative("score_component_numerator", watch_threshold, value)
    denominator = _subtract_nonnegative(
        "score_component_denominator",
        watch_threshold,
        pass_threshold,
    )
    return _safe_unit_ratio(numerator, denominator)


def _event_freshness_decay_score(
    event_age_component: Decimal,
    source_freshness_component: Decimal,
    event_relevance_component: Decimal,
    stale_context_component: Decimal,
    update_frequency_component: Decimal,
    evidence_quality_component: Decimal,
    config: CandidateDecisionEventFreshnessDecayScoreConfig
    | CandidateDecisionEventFreshnessDecayScoreReport,
) -> Decimal:
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        context.rounding = ROUND_HALF_EVEN
        return _normalize_unit_decimal(
            "event_freshness_decay_score",
            event_age_component * EVENT_AGE_FINAL_WEIGHT
            + (
                source_freshness_component * config.source_freshness_weight
                + event_relevance_component * config.event_relevance_weight
                + stale_context_component * config.stale_context_weight
                + update_frequency_component * config.update_frequency_weight
                + evidence_quality_component * config.evidence_quality_weight
            )
            * RESEARCH_FINAL_WEIGHT,
        )


def _hard_flag_codes(
    latest_event_age_minutes: Decimal,
    source_freshness_score: Decimal,
    event_relevance_score: Decimal,
    stale_context_score: Decimal,
    update_frequency_score: Decimal,
    evidence_quality_score: Decimal,
    event_freshness_decay_score: Decimal,
    config: CandidateDecisionEventFreshnessDecayScoreConfig
    | CandidateDecisionEventFreshnessDecayScoreReport,
) -> tuple[str, ...]:
    codes: list[str] = []
    if latest_event_age_minutes > config.max_watch_latest_event_age_minutes:
        codes.append("latest_event_age_block")
    if source_freshness_score < config.min_watch_source_freshness_score:
        codes.append("source_freshness_block")
    if event_relevance_score < config.min_watch_event_relevance_score:
        codes.append("event_relevance_block")
    if stale_context_score > config.max_watch_stale_context_score:
        codes.append("stale_context_block")
    if update_frequency_score < config.min_watch_update_frequency_score:
        codes.append("update_frequency_block")
    if evidence_quality_score < config.min_watch_evidence_quality_score:
        codes.append("evidence_quality_block")
    if event_freshness_decay_score < config.min_watch_event_freshness_decay_score:
        codes.append("event_freshness_decay_score_block")
    return tuple(codes)


def _event_freshness_status(
    event_freshness_decay_score: Decimal,
    hard_flag_codes: tuple[str, ...],
    config: CandidateDecisionEventFreshnessDecayScoreConfig
    | CandidateDecisionEventFreshnessDecayScoreReport,
) -> str:
    if hard_flag_codes:
        return "block"
    if event_freshness_decay_score < config.min_pass_event_freshness_decay_score:
        return "watch"
    return "pass"


def _reason_codes(
    existing_reason_codes: tuple[str, ...],
    latest_event_age_minutes: Decimal,
    source_freshness_score: Decimal,
    event_relevance_score: Decimal,
    stale_context_score: Decimal,
    update_frequency_score: Decimal,
    evidence_quality_score: Decimal,
    event_freshness_decay_score: Decimal,
    event_freshness_status: str,
    config: CandidateDecisionEventFreshnessDecayScoreConfig
    | CandidateDecisionEventFreshnessDecayScoreReport,
) -> tuple[str, ...]:
    codes = [
        *existing_reason_codes,
        f"event_freshness_decay_{event_freshness_status}",
        _maximum_reason(
            "latest_event_age",
            latest_event_age_minutes,
            config.max_pass_latest_event_age_minutes,
            config.max_watch_latest_event_age_minutes,
        ),
        _minimum_reason(
            "source_freshness",
            source_freshness_score,
            config.min_watch_source_freshness_score,
            config.min_pass_source_freshness_score,
        ),
        _minimum_reason(
            "event_relevance",
            event_relevance_score,
            config.min_watch_event_relevance_score,
            config.min_pass_event_relevance_score,
        ),
        _maximum_reason(
            "stale_context",
            stale_context_score,
            config.max_pass_stale_context_score,
            config.max_watch_stale_context_score,
        ),
        _minimum_reason(
            "update_frequency",
            update_frequency_score,
            config.min_watch_update_frequency_score,
            config.min_pass_update_frequency_score,
        ),
        _minimum_reason(
            "evidence_quality",
            evidence_quality_score,
            config.min_watch_evidence_quality_score,
            config.min_pass_evidence_quality_score,
        ),
        _score_reason(event_freshness_decay_score, config),
    ]
    return _normalize_reason_codes("reason_codes", tuple(codes), allow_empty=False)


def _minimum_reason(
    name: str,
    value: Decimal,
    watch_threshold: Decimal,
    pass_threshold: Decimal,
) -> str:
    if value >= pass_threshold:
        return f"{name}_pass"
    if value >= watch_threshold:
        return f"{name}_watch"
    return f"{name}_block"


def _maximum_reason(
    name: str,
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> str:
    if value <= pass_threshold:
        return f"{name}_pass"
    if value <= watch_threshold:
        return f"{name}_watch"
    return f"{name}_block"


def _score_reason(
    event_freshness_decay_score: Decimal,
    config: CandidateDecisionEventFreshnessDecayScoreConfig
    | CandidateDecisionEventFreshnessDecayScoreReport,
) -> str:
    if event_freshness_decay_score >= config.min_pass_event_freshness_decay_score:
        return "event_freshness_decay_score_pass"
    if event_freshness_decay_score >= config.min_watch_event_freshness_decay_score:
        return "event_freshness_decay_score_watch"
    return "event_freshness_decay_score_block"


def _validate_config(
    config: CandidateDecisionEventFreshnessDecayScoreConfig
    | CandidateDecisionEventFreshnessDecayScoreReport,
) -> None:
    if (
        config.min_watch_event_freshness_decay_score
        > config.min_pass_event_freshness_decay_score
    ):
        raise ValueError("min_watch_event_freshness_decay_score must not exceed pass threshold")
    if config.max_pass_latest_event_age_minutes > config.max_watch_latest_event_age_minutes:
        raise ValueError(
            "max_pass_latest_event_age_minutes must not exceed watch threshold",
        )
    if (
        config.min_watch_source_freshness_score
        > config.min_pass_source_freshness_score
    ):
        raise ValueError("source_freshness thresholds must be ordered")
    if config.min_watch_event_relevance_score > config.min_pass_event_relevance_score:
        raise ValueError("event_relevance thresholds must be ordered")
    if config.max_pass_stale_context_score > config.max_watch_stale_context_score:
        raise ValueError("stale_context thresholds must be ordered")
    if (
        config.min_watch_update_frequency_score
        > config.min_pass_update_frequency_score
    ):
        raise ValueError("update_frequency thresholds must be ordered")
    if config.min_watch_evidence_quality_score > config.min_pass_evidence_quality_score:
        raise ValueError("evidence_quality thresholds must be ordered")
    if _component_weight_total(config) != ONE:
        raise ValueError("weights must sum to 1.000000")


def _validate_report(report: CandidateDecisionEventFreshnessDecayScoreReport) -> None:
    _validate_config(report)
    expected_event_age_component = _age_component(
        report.latest_event_age_minutes,
        report.max_pass_latest_event_age_minutes,
        report.max_watch_latest_event_age_minutes,
    )
    if report.event_age_component != expected_event_age_component:
        raise ValueError("event_age_component must match age thresholds")
    expected_source_freshness_component = _minimum_score_component(
        report.source_freshness_score,
        report.min_watch_source_freshness_score,
        report.min_pass_source_freshness_score,
    )
    if report.source_freshness_component != expected_source_freshness_component:
        raise ValueError("source_freshness_component must match thresholds")
    expected_event_relevance_component = _minimum_score_component(
        report.event_relevance_score,
        report.min_watch_event_relevance_score,
        report.min_pass_event_relevance_score,
    )
    if report.event_relevance_component != expected_event_relevance_component:
        raise ValueError("event_relevance_component must match thresholds")
    expected_stale_context_component = _maximum_score_component(
        report.stale_context_score,
        report.max_pass_stale_context_score,
        report.max_watch_stale_context_score,
    )
    if report.stale_context_component != expected_stale_context_component:
        raise ValueError("stale_context_component must match thresholds")
    expected_update_frequency_component = _minimum_score_component(
        report.update_frequency_score,
        report.min_watch_update_frequency_score,
        report.min_pass_update_frequency_score,
    )
    if report.update_frequency_component != expected_update_frequency_component:
        raise ValueError("update_frequency_component must match thresholds")
    expected_evidence_quality_component = _minimum_score_component(
        report.evidence_quality_score,
        report.min_watch_evidence_quality_score,
        report.min_pass_evidence_quality_score,
    )
    if report.evidence_quality_component != expected_evidence_quality_component:
        raise ValueError("evidence_quality_component must match thresholds")
    expected_score = _event_freshness_decay_score(
        report.event_age_component,
        report.source_freshness_component,
        report.event_relevance_component,
        report.stale_context_component,
        report.update_frequency_component,
        report.evidence_quality_component,
        report,
    )
    if report.event_freshness_decay_score != expected_score:
        raise ValueError("event_freshness_decay_score must match component scores")
    expected_hard_flags = _hard_flag_codes(
        report.latest_event_age_minutes,
        report.source_freshness_score,
        report.event_relevance_score,
        report.stale_context_score,
        report.update_frequency_score,
        report.evidence_quality_score,
        report.event_freshness_decay_score,
        report,
    )
    if report.hard_flag_codes != expected_hard_flags:
        raise ValueError("hard_flag_codes must match thresholds")
    expected_status = _event_freshness_status(
        report.event_freshness_decay_score,
        expected_hard_flags,
        report,
    )
    if report.event_freshness_status != expected_status:
        raise ValueError("event_freshness_status must match thresholds")
    expected_generated_reason_codes = _reason_codes(
        (),
        report.latest_event_age_minutes,
        report.source_freshness_score,
        report.event_relevance_score,
        report.stale_context_score,
        report.update_frequency_score,
        report.evidence_quality_score,
        report.event_freshness_decay_score,
        report.event_freshness_status,
        report,
    )
    if (
        report.reason_codes[-len(expected_generated_reason_codes) :]
        != expected_generated_reason_codes
    ):
        raise ValueError("reason_codes must end with generated event freshness reasons")


def _safe_unit_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        return ONE if numerator >= ZERO else ZERO
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        context.rounding = ROUND_HALF_EVEN
        return _normalize_unit_decimal("ratio", numerator / denominator)


def _subtract_nonnegative(field_name: str, minuend: Decimal, subtrahend: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        context.rounding = ROUND_HALF_EVEN
        return _normalize_nonnegative_decimal(field_name, minuend - subtrahend)


def _component_weight_total(
    config: CandidateDecisionEventFreshnessDecayScoreConfig
    | CandidateDecisionEventFreshnessDecayScoreReport,
) -> Decimal:
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        context.rounding = ROUND_HALF_EVEN
        return _normalize_nonnegative_decimal(
            "component_weight_total",
            config.source_freshness_weight
            + config.event_relevance_weight
            + config.stale_context_weight
            + config.update_frequency_weight
            + config.evidence_quality_weight,
        )


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be no greater than 1")
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
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        context.rounding = ROUND_HALF_EVEN
        return value.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    codes: list[str] = []
    for item in value:
        codes.append(_require_canonical_string(field_name, item))
    if len(set(codes)) != len(codes):
        raise ValueError(f"{field_name} must be unique")
    return tuple(codes)


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _require_choice(
    field_name: str,
    value: object,
    choices: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in choices:
        raise ValueError(f"{field_name} must be one of {choices!r}")


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    return value


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_phase_flags(label: str, value: object) -> None:
    require_paper_only_flags(label, value)
    if getattr(value, "report_only") is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly") is not True:
        raise ValueError(f"readonly must be True for {label}")


def _report_digest(report: CandidateDecisionEventFreshnessDecayScoreReport) -> str:
    payload = _report_payload(report, include_digest=False)
    ready = json_ready_no_floats(payload)
    if type(ready) is not dict:
        raise ValueError("digest payload must be a JSON object")
    canonical_payload = json.dumps(
        ready,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()


def _report_payload(
    report: CandidateDecisionEventFreshnessDecayScoreReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload = asdict(report)
    if not include_digest:
        payload.pop("derived_validation_digest")
    return payload


def _reject_public_numbers(value: object) -> None:
    if isinstance(value, float):
        raise ValueError("public payload Decimals must be decimal strings")
    if isinstance(value, int) and not isinstance(value, bool):
        raise ValueError("public payload Decimals must be decimal strings")
    if isinstance(value, Decimal):
        raise ValueError("public payload Decimals must be decimal strings")
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_public_numbers(item)
    if isinstance(value, list):
        for item in value:
            _reject_public_numbers(item)


def _reject_public_status_aliases(value: object) -> None:
    for path, item in _iter_public_strings(value):
        if item.lower() in _PUBLIC_STATUS_ALIASES:
            raise ValueError(f"public status value is not allowed: {path}")


def _iter_public_strings(value: object, path: str = "$") -> tuple[tuple[str, str], ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_public_strings(asdict(value), path)
    if isinstance(value, Mapping):
        items: list[tuple[str, str]] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            key_path = f"{path}.{key}"
            items.append((key_path, key))
            items.extend(_iter_public_strings(item, key_path))
        return tuple(items)
    if type(value) is str:
        return ((path, value),)
    if isinstance(value, (list, tuple)):
        items = []
        for index, item in enumerate(value):
            items.extend(_iter_public_strings(item, f"{path}[{index}]"))
        return tuple(items)
    return ()


__all__ = (
    "DEFAULT_CANDIDATE_DECISION_EVENT_FRESHNESS_DECAY_SCORE_CONFIG_VERSION",
    "EVENT_FRESHNESS_STATUSES",
    "CandidateDecisionEventFreshnessDecayScoreConfig",
    "CandidateDecisionEventFreshnessDecayScoreInput",
    "CandidateDecisionEventFreshnessDecayScoreReport",
    "build_candidate_decision_event_freshness_decay_score_report",
    "candidate_decision_event_freshness_decay_score_payload",
    "validate_candidate_decision_event_freshness_decay_score_public_payload",
    "reject_candidate_decision_event_freshness_decay_score_unsafe_payload",
)
