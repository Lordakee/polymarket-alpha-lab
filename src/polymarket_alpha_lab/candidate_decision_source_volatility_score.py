"""Pure paper-only source narrative volatility score for candidate decisions."""

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


DEFAULT_CANDIDATE_DECISION_SOURCE_VOLATILITY_SCORE_CONFIG_VERSION = (
    "candidate-decision-source-volatility-score-v0"
)
SOURCE_VOLATILITY_STATUSES = ("pass", "watch", "block")

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
    "raw_market",
)
_SOURCE_REFERENCE_PUBLIC_TERMS = (
    "source" + "_ref",
    "source" + "_refs",
    "source" + "_url",
    "source" + "_uri",
    "source" + "_text",
    "source" + "_excerpt",
    "source" + "_title",
    "raw" + "_text",
    "url",
    "http" + "://",
    "https" + "://",
    "www.",
    "://",
)
_UNSAFE_PUBLIC_TERMS = (
    "api" + "_key",
    "au" + "th",
    "bear" + "er",
    "b" + "uy",
    "connection" + "_string",
    "credential",
    "database",
    "d" + "sn",
    "jwt",
    "oauth",
    "or" + "der",
    "pass" + "word",
    "pos" + "ition",
    "pos" + "ition_size",
    "pos" + "ition-sizing",
    "private" + "_key",
    "recommen" + "dation",
    "sec" + "ret",
    "s" + "ell",
    "session",
    "ta" + "ble",
    "ta" + "ble_name",
    "to" + "ken",
    "tra" + "de",
    "tra" + "ding",
    "wal" + "let",
)
_PUBLIC_STATUS_ALIASES = ("ready", "blocked", "matched", "supported")
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")


@dataclass(frozen=True)
class CandidateDecisionSourceVolatilityScoreConfig:
    config_version: str = (
        DEFAULT_CANDIDATE_DECISION_SOURCE_VOLATILITY_SCORE_CONFIG_VERSION
    )
    max_pass_source_volatility_score: Decimal = Decimal("0.300000")
    max_watch_source_volatility_score: Decimal = Decimal("0.600000")
    max_narrative_change_count_for_component: Decimal = Decimal("5")
    max_retraction_count_for_component: Decimal = Decimal("4")
    max_contradiction_count_for_component: Decimal = Decimal("4")
    narrative_flip_block_ratio: Decimal = Decimal("0.500000")
    claim_volatility_block_score: Decimal = Decimal("0.800000")
    min_source_consensus_block_score: Decimal = Decimal("0.200000")
    min_pass_observation_window_days: Decimal = Decimal("7.000000")
    min_watch_observation_window_days: Decimal = Decimal("1.000000")
    narrative_change_weight: Decimal = Decimal("0.150000")
    retraction_weight: Decimal = Decimal("0.200000")
    contradiction_weight: Decimal = Decimal("0.200000")
    narrative_flip_weight: Decimal = Decimal("0.150000")
    claim_volatility_weight: Decimal = Decimal("0.150000")
    source_disagreement_weight: Decimal = Decimal("0.100000")
    short_observation_window_weight: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionSourceVolatilityScoreConfig:
            raise TypeError(
                "CandidateDecisionSourceVolatilityScoreConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, CandidateDecisionSourceVolatilityScoreConfig)
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_CANDIDATE_DECISION_SOURCE_VOLATILITY_SCORE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported version")
        for field_name in (
            "max_pass_source_volatility_score",
            "max_watch_source_volatility_score",
            "narrative_flip_block_ratio",
            "claim_volatility_block_score",
            "min_source_consensus_block_score",
            "narrative_change_weight",
            "retraction_weight",
            "contradiction_weight",
            "narrative_flip_weight",
            "claim_volatility_weight",
            "source_disagreement_weight",
            "short_observation_window_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_narrative_change_count_for_component",
            "max_retraction_count_for_component",
            "max_contradiction_count_for_component",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "min_pass_observation_window_days",
            "min_watch_observation_window_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_phase_flags("config", self)
        reject_candidate_decision_source_volatility_score_unsafe_payload(
            "source volatility config",
            self,
        )


@dataclass(frozen=True)
class CandidateDecisionSourceVolatilityScoreInput:
    generated_at: datetime
    redacted_candidate_ref: str
    narrative_change_count: Decimal
    retraction_count: Decimal
    contradiction_count: Decimal
    narrative_flip_ratio: Decimal
    claim_volatility_score: Decimal
    source_consensus_score: Decimal
    observation_window_days: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionSourceVolatilityScoreInput:
            raise TypeError(
                "CandidateDecisionSourceVolatilityScoreInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("input", self, CandidateDecisionSourceVolatilityScoreInput)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "redacted_candidate_ref",
            _require_redacted_candidate_ref(self.redacted_candidate_ref),
        )
        for field_name in (
            "narrative_change_count",
            "retraction_count",
            "contradiction_count",
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
            "narrative_flip_ratio",
            "claim_volatility_score",
            "source_consensus_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "observation_window_days",
            _normalize_nonnegative_decimal(
                "observation_window_days",
                self.observation_window_days,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_phase_flags("input", self)
        reject_candidate_decision_source_volatility_score_unsafe_payload(
            "source volatility input",
            self,
        )


@dataclass(frozen=True)
class CandidateDecisionSourceVolatilityScoreReport:
    generated_at: datetime
    config_version: str
    max_pass_source_volatility_score: Decimal
    max_watch_source_volatility_score: Decimal
    max_narrative_change_count_for_component: Decimal
    max_retraction_count_for_component: Decimal
    max_contradiction_count_for_component: Decimal
    narrative_flip_block_ratio: Decimal
    claim_volatility_block_score: Decimal
    min_source_consensus_block_score: Decimal
    min_pass_observation_window_days: Decimal
    min_watch_observation_window_days: Decimal
    narrative_change_weight: Decimal
    retraction_weight: Decimal
    contradiction_weight: Decimal
    narrative_flip_weight: Decimal
    claim_volatility_weight: Decimal
    source_disagreement_weight: Decimal
    short_observation_window_weight: Decimal
    redacted_candidate_ref: str
    narrative_change_count: Decimal
    retraction_count: Decimal
    contradiction_count: Decimal
    narrative_flip_ratio: Decimal
    claim_volatility_score: Decimal
    source_consensus_score: Decimal
    observation_window_days: Decimal
    narrative_change_component: Decimal
    retraction_component: Decimal
    contradiction_component: Decimal
    narrative_flip_component: Decimal
    claim_volatility_component: Decimal
    source_disagreement_component: Decimal
    short_observation_window_component: Decimal
    source_volatility_score: Decimal
    source_volatility_status: str
    hard_blocker_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionSourceVolatilityScoreReport:
            raise TypeError(
                "CandidateDecisionSourceVolatilityScoreReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, CandidateDecisionSourceVolatilityScoreReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_CANDIDATE_DECISION_SOURCE_VOLATILITY_SCORE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported version")
        object.__setattr__(
            self,
            "redacted_candidate_ref",
            _require_redacted_candidate_ref(self.redacted_candidate_ref),
        )
        for field_name in (
            "max_pass_source_volatility_score",
            "max_watch_source_volatility_score",
            "narrative_flip_block_ratio",
            "claim_volatility_block_score",
            "min_source_consensus_block_score",
            "narrative_change_weight",
            "retraction_weight",
            "contradiction_weight",
            "narrative_flip_weight",
            "claim_volatility_weight",
            "source_disagreement_weight",
            "short_observation_window_weight",
            "narrative_flip_ratio",
            "claim_volatility_score",
            "source_consensus_score",
            "narrative_change_component",
            "retraction_component",
            "contradiction_component",
            "narrative_flip_component",
            "claim_volatility_component",
            "source_disagreement_component",
            "short_observation_window_component",
            "source_volatility_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_narrative_change_count_for_component",
            "max_retraction_count_for_component",
            "max_contradiction_count_for_component",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "narrative_change_count",
            "retraction_count",
            "contradiction_count",
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
            "min_pass_observation_window_days",
            "min_watch_observation_window_days",
            "observation_window_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_choice(
            "source_volatility_status",
            self.source_volatility_status,
            SOURCE_VOLATILITY_STATUSES,
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
        reject_candidate_decision_source_volatility_score_unsafe_payload(
            "source volatility report",
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
        return candidate_decision_source_volatility_score_payload(self)


def build_candidate_decision_source_volatility_score_report(
    score_input: CandidateDecisionSourceVolatilityScoreInput,
    *,
    config: CandidateDecisionSourceVolatilityScoreConfig | None = None,
) -> CandidateDecisionSourceVolatilityScoreReport:
    if type(score_input) is not CandidateDecisionSourceVolatilityScoreInput:
        raise ValueError(
            "score_input must be a CandidateDecisionSourceVolatilityScoreInput",
        )
    report_config = config or CandidateDecisionSourceVolatilityScoreConfig()
    if type(report_config) is not CandidateDecisionSourceVolatilityScoreConfig:
        raise ValueError(
            "config must be a CandidateDecisionSourceVolatilityScoreConfig",
        )
    _require_phase_flags("input", score_input)
    _require_phase_flags("config", report_config)
    reject_candidate_decision_source_volatility_score_unsafe_payload(
        "source volatility input",
        score_input,
    )
    reject_candidate_decision_source_volatility_score_unsafe_payload(
        "source volatility config",
        report_config,
    )
    return CandidateDecisionSourceVolatilityScoreReport(
        **_report_values(score_input, report_config),
    )


def candidate_decision_source_volatility_score_payload(
    report: CandidateDecisionSourceVolatilityScoreReport,
) -> dict[str, Any]:
    if type(report) is not CandidateDecisionSourceVolatilityScoreReport:
        raise ValueError(
            "report must be a CandidateDecisionSourceVolatilityScoreReport",
        )
    _require_phase_flags("report", report)
    _validate_report(report)
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest must match report fields")
    reject_candidate_decision_source_volatility_score_unsafe_payload(
        "source volatility report",
        report,
    )
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    validate_candidate_decision_source_volatility_score_public_payload(payload)
    return payload


def validate_candidate_decision_source_volatility_score_public_payload(
    payload: object,
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_public_numbers(payload)
    _reject_public_status_aliases(payload)
    reject_candidate_decision_source_volatility_score_unsafe_payload(
        "source volatility public payload",
        payload,
    )
    _require_public_flags(payload)


def reject_candidate_decision_source_volatility_score_unsafe_payload(
    label: str,
    payload: object,
) -> None:
    for path, item in _iter_public_strings(payload):
        lowered = item.lower()
        if any(term in lowered for term in _RAW_MARKET_OR_CANDIDATE_PUBLIC_TERMS):
            raise ValueError(f"raw market or candidate public payload entry in {label}: {path}")
        if any(term in lowered for term in _SOURCE_REFERENCE_PUBLIC_TERMS):
            raise ValueError(f"source references public payload entry in {label}: {path}")
        if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
            raise ValueError(f"unsafe live surface public payload entry in {label}: {path}")


def _report_values(
    score_input: CandidateDecisionSourceVolatilityScoreInput,
    config: CandidateDecisionSourceVolatilityScoreConfig,
) -> dict[str, object]:
    narrative_change_component_raw = _ratio(
        score_input.narrative_change_count,
        config.max_narrative_change_count_for_component,
    )
    retraction_component_raw = _ratio(
        score_input.retraction_count,
        config.max_retraction_count_for_component,
    )
    contradiction_component_raw = _ratio(
        score_input.contradiction_count,
        config.max_contradiction_count_for_component,
    )
    source_disagreement_component_raw = _subtract_nonnegative(
        "source_disagreement_component",
        ONE,
        score_input.source_consensus_score,
    )
    short_observation_window_component_raw = _short_observation_window_component(
        score_input.observation_window_days,
        config.min_pass_observation_window_days,
        config.min_watch_observation_window_days,
    )
    score = _weighted_score(
        narrative_change_component_raw,
        retraction_component_raw,
        contradiction_component_raw,
        score_input.narrative_flip_ratio,
        score_input.claim_volatility_score,
        source_disagreement_component_raw,
        short_observation_window_component_raw,
        config,
    )
    hard_blockers = _hard_blocker_codes(score_input, score, config)
    status = _status(score, hard_blockers, config)
    reason_codes = _reason_codes(score_input, score, status, config)
    return {
        "generated_at": score_input.generated_at,
        "config_version": config.config_version,
        "max_pass_source_volatility_score": config.max_pass_source_volatility_score,
        "max_watch_source_volatility_score": config.max_watch_source_volatility_score,
        "max_narrative_change_count_for_component": (
            config.max_narrative_change_count_for_component
        ),
        "max_retraction_count_for_component": config.max_retraction_count_for_component,
        "max_contradiction_count_for_component": (
            config.max_contradiction_count_for_component
        ),
        "narrative_flip_block_ratio": config.narrative_flip_block_ratio,
        "claim_volatility_block_score": config.claim_volatility_block_score,
        "min_source_consensus_block_score": config.min_source_consensus_block_score,
        "min_pass_observation_window_days": config.min_pass_observation_window_days,
        "min_watch_observation_window_days": config.min_watch_observation_window_days,
        "narrative_change_weight": config.narrative_change_weight,
        "retraction_weight": config.retraction_weight,
        "contradiction_weight": config.contradiction_weight,
        "narrative_flip_weight": config.narrative_flip_weight,
        "claim_volatility_weight": config.claim_volatility_weight,
        "source_disagreement_weight": config.source_disagreement_weight,
        "short_observation_window_weight": config.short_observation_window_weight,
        "redacted_candidate_ref": score_input.redacted_candidate_ref,
        "narrative_change_count": score_input.narrative_change_count,
        "retraction_count": score_input.retraction_count,
        "contradiction_count": score_input.contradiction_count,
        "narrative_flip_ratio": score_input.narrative_flip_ratio,
        "claim_volatility_score": score_input.claim_volatility_score,
        "source_consensus_score": score_input.source_consensus_score,
        "observation_window_days": score_input.observation_window_days,
        "narrative_change_component": _quantize_unit(narrative_change_component_raw),
        "retraction_component": _quantize_unit(retraction_component_raw),
        "contradiction_component": _quantize_unit(contradiction_component_raw),
        "narrative_flip_component": score_input.narrative_flip_ratio,
        "claim_volatility_component": score_input.claim_volatility_score,
        "source_disagreement_component": _quantize_unit(
            source_disagreement_component_raw,
        ),
        "short_observation_window_component": _quantize_unit(
            short_observation_window_component_raw,
        ),
        "source_volatility_score": score,
        "source_volatility_status": status,
        "hard_blocker_codes": hard_blockers,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _weighted_score(
    narrative_change_component: Decimal,
    retraction_component: Decimal,
    contradiction_component: Decimal,
    narrative_flip_component: Decimal,
    claim_volatility_component: Decimal,
    source_disagreement_component: Decimal,
    short_observation_window_component: Decimal,
    config: CandidateDecisionSourceVolatilityScoreConfig,
) -> Decimal:
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        weighted = (
            narrative_change_component * config.narrative_change_weight
            + retraction_component * config.retraction_weight
            + contradiction_component * config.contradiction_weight
            + narrative_flip_component * config.narrative_flip_weight
            + claim_volatility_component * config.claim_volatility_weight
            + source_disagreement_component * config.source_disagreement_weight
            + short_observation_window_component
            * config.short_observation_window_weight
        )
        return _quantize_unit(weighted)


def _short_observation_window_component(
    observation_window_days: Decimal,
    pass_days: Decimal,
    watch_days: Decimal,
) -> Decimal:
    if observation_window_days >= pass_days:
        return ZERO
    if observation_window_days <= watch_days:
        return ONE
    numerator = _subtract_nonnegative(
        "short_observation_window_component_numerator",
        pass_days,
        observation_window_days,
    )
    denominator = _subtract_nonnegative(
        "short_observation_window_component_denominator",
        pass_days,
        watch_days,
    )
    return _safe_unit_ratio(numerator, denominator)


def _hard_blocker_codes(
    score_input: CandidateDecisionSourceVolatilityScoreInput,
    source_volatility_score: Decimal,
    config: CandidateDecisionSourceVolatilityScoreConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if score_input.retraction_count >= config.max_retraction_count_for_component:
        codes.append("retraction_count_block")
    if score_input.contradiction_count >= config.max_contradiction_count_for_component:
        codes.append("contradiction_count_block")
    if score_input.narrative_flip_ratio >= config.narrative_flip_block_ratio:
        codes.append("narrative_flip_ratio_block")
    if score_input.claim_volatility_score >= config.claim_volatility_block_score:
        codes.append("claim_volatility_block")
    if score_input.source_consensus_score <= config.min_source_consensus_block_score:
        codes.append("source_consensus_block")
    if score_input.observation_window_days <= config.min_watch_observation_window_days:
        codes.append("short_observation_window_block")
    if source_volatility_score > config.max_watch_source_volatility_score:
        codes.append("source_volatility_score_block")
    return tuple(codes)


def _status(
    source_volatility_score: Decimal,
    hard_blocker_codes: tuple[str, ...],
    config: CandidateDecisionSourceVolatilityScoreConfig,
) -> str:
    if hard_blocker_codes or source_volatility_score > config.max_watch_source_volatility_score:
        return "block"
    if source_volatility_score > config.max_pass_source_volatility_score:
        return "watch"
    return "pass"


def _reason_codes(
    score_input: CandidateDecisionSourceVolatilityScoreInput,
    source_volatility_score: Decimal,
    status: str,
    config: CandidateDecisionSourceVolatilityScoreConfig,
) -> tuple[str, ...]:
    codes = list(score_input.reason_codes)
    codes.append(f"source_volatility_{status}")
    codes.append(
        _component_reason(
            "narrative_change",
            _ratio(
                score_input.narrative_change_count,
                config.max_narrative_change_count_for_component,
            ),
            config.max_pass_source_volatility_score,
        ),
    )
    codes.append(
        _count_reason(
            "retraction_count",
            score_input.retraction_count,
            config.max_retraction_count_for_component,
            source_volatility_score,
            config.max_pass_source_volatility_score,
        ),
    )
    codes.append(
        _count_reason(
            "contradiction_count",
            score_input.contradiction_count,
            config.max_contradiction_count_for_component,
            source_volatility_score,
            config.max_pass_source_volatility_score,
        ),
    )
    codes.append(
        _component_reason(
            "narrative_flip_ratio",
            score_input.narrative_flip_ratio,
            config.max_pass_source_volatility_score,
            config.narrative_flip_block_ratio,
        ),
    )
    codes.append(
        _component_reason(
            "claim_volatility",
            score_input.claim_volatility_score,
            config.max_pass_source_volatility_score,
            config.claim_volatility_block_score,
        ),
    )
    if score_input.source_consensus_score <= config.min_source_consensus_block_score:
        codes.append("source_consensus_block")
    elif score_input.source_consensus_score < (
        ONE - config.max_pass_source_volatility_score
    ):
        codes.append("source_consensus_watch")
    else:
        codes.append("source_consensus_pass")
    if score_input.observation_window_days <= config.min_watch_observation_window_days:
        codes.append("short_observation_window_block")
    elif score_input.observation_window_days < config.min_pass_observation_window_days:
        codes.append("short_observation_window_watch")
    else:
        codes.append("short_observation_window_pass")
    return tuple(codes)


def _count_reason(
    prefix: str,
    count: Decimal,
    block_count: Decimal,
    source_volatility_score: Decimal,
    pass_threshold: Decimal,
) -> str:
    if count >= block_count:
        return f"{prefix}_block"
    if source_volatility_score > pass_threshold and count > ZERO:
        return f"{prefix}_watch"
    return f"{prefix}_pass"


def _component_reason(
    prefix: str,
    component: Decimal,
    pass_threshold: Decimal,
    block_threshold: Decimal | None = None,
) -> str:
    if block_threshold is not None and component >= block_threshold:
        return f"{prefix}_block"
    if component > pass_threshold:
        return f"{prefix}_watch"
    return f"{prefix}_pass"


def _validate_config(config: CandidateDecisionSourceVolatilityScoreConfig) -> None:
    if config.max_pass_source_volatility_score > config.max_watch_source_volatility_score:
        raise ValueError("pass threshold must not exceed watch threshold")
    if (
        config.min_watch_observation_window_days
        > config.min_pass_observation_window_days
    ):
        raise ValueError("watch observation window must not exceed pass observation window")
    _validate_weight_sum(
        (
            config.narrative_change_weight,
            config.retraction_weight,
            config.contradiction_weight,
            config.narrative_flip_weight,
            config.claim_volatility_weight,
            config.source_disagreement_weight,
            config.short_observation_window_weight,
        ),
    )


def _validate_config_like_report(report: CandidateDecisionSourceVolatilityScoreReport) -> None:
    if report.max_pass_source_volatility_score > report.max_watch_source_volatility_score:
        raise ValueError("pass threshold must not exceed watch threshold")
    if report.min_watch_observation_window_days > report.min_pass_observation_window_days:
        raise ValueError("watch observation window must not exceed pass observation window")
    _validate_weight_sum(
        (
            report.narrative_change_weight,
            report.retraction_weight,
            report.contradiction_weight,
            report.narrative_flip_weight,
            report.claim_volatility_weight,
            report.source_disagreement_weight,
            report.short_observation_window_weight,
        ),
    )


def _validate_report(report: CandidateDecisionSourceVolatilityScoreReport) -> None:
    pseudo_input = CandidateDecisionSourceVolatilityScoreInput(
        generated_at=report.generated_at,
        redacted_candidate_ref=report.redacted_candidate_ref,
        narrative_change_count=report.narrative_change_count,
        retraction_count=report.retraction_count,
        contradiction_count=report.contradiction_count,
        narrative_flip_ratio=report.narrative_flip_ratio,
        claim_volatility_score=report.claim_volatility_score,
        source_consensus_score=report.source_consensus_score,
        observation_window_days=report.observation_window_days,
        reason_codes=_base_reason_codes(report.reason_codes),
    )
    pseudo_config = CandidateDecisionSourceVolatilityScoreConfig(
        config_version=report.config_version,
        max_pass_source_volatility_score=report.max_pass_source_volatility_score,
        max_watch_source_volatility_score=report.max_watch_source_volatility_score,
        max_narrative_change_count_for_component=(
            report.max_narrative_change_count_for_component
        ),
        max_retraction_count_for_component=report.max_retraction_count_for_component,
        max_contradiction_count_for_component=(
            report.max_contradiction_count_for_component
        ),
        narrative_flip_block_ratio=report.narrative_flip_block_ratio,
        claim_volatility_block_score=report.claim_volatility_block_score,
        min_source_consensus_block_score=report.min_source_consensus_block_score,
        min_pass_observation_window_days=report.min_pass_observation_window_days,
        min_watch_observation_window_days=report.min_watch_observation_window_days,
        narrative_change_weight=report.narrative_change_weight,
        retraction_weight=report.retraction_weight,
        contradiction_weight=report.contradiction_weight,
        narrative_flip_weight=report.narrative_flip_weight,
        claim_volatility_weight=report.claim_volatility_weight,
        source_disagreement_weight=report.source_disagreement_weight,
        short_observation_window_weight=report.short_observation_window_weight,
    )
    expected = _report_values(pseudo_input, pseudo_config)
    for field_name in (
        "narrative_change_component",
        "retraction_component",
        "contradiction_component",
        "narrative_flip_component",
        "claim_volatility_component",
        "source_disagreement_component",
        "short_observation_window_component",
        "source_volatility_score",
        "source_volatility_status",
        "hard_blocker_codes",
        "reason_codes",
    ):
        if getattr(report, field_name) != expected[field_name]:
            raise ValueError(f"{field_name} must match source volatility calculation")


def _base_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    generated_prefixes = (
        "source_volatility_",
        "narrative_change_",
        "retraction_count_",
        "contradiction_count_",
        "narrative_flip_ratio_",
        "claim_volatility_",
        "source_consensus_",
        "short_observation_window_",
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


def _safe_unit_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        return ZERO
    return _ratio(numerator, denominator)


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


def _normalize_positive_integral_decimal(field_name: str, value: object) -> Decimal:
    decimal = _normalize_nonnegative_integral_decimal(field_name, value)
    if decimal <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal


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


def _require_public_flags(payload: dict[str, object]) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for public payload")


def _report_digest(report: CandidateDecisionSourceVolatilityScoreReport) -> str:
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
    "DEFAULT_CANDIDATE_DECISION_SOURCE_VOLATILITY_SCORE_CONFIG_VERSION",
    "SOURCE_VOLATILITY_STATUSES",
    "CandidateDecisionSourceVolatilityScoreConfig",
    "CandidateDecisionSourceVolatilityScoreInput",
    "CandidateDecisionSourceVolatilityScoreReport",
    "build_candidate_decision_source_volatility_score_report",
    "candidate_decision_source_volatility_score_payload",
    "validate_candidate_decision_source_volatility_score_public_payload",
    "reject_candidate_decision_source_volatility_score_unsafe_payload",
)
