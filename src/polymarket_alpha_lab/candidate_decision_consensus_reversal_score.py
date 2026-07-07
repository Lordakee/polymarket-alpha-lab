"""Pure paper-only consensus reversal risk score."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_CANDIDATE_DECISION_CONSENSUS_REVERSAL_SCORE_CONFIG_VERSION = (
    "candidate-decision-consensus-reversal-score-v0"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

REVERSAL_STATUSES = ("pass", "watch", "block")
HARD_FLAG_CODES = (
    "reversal_velocity_block",
    "weak_evidence_reversal_block",
)
REASON_CODE_SEQUENCE = (
    "consensus_reversal_pass",
    "consensus_reversal_watch",
    "consensus_reversal_block",
    "consensus_delta_pass",
    "consensus_delta_watch",
    "consensus_delta_block",
    "reversal_velocity_pass",
    "reversal_velocity_watch",
    "reversal_velocity_block",
    "evidence_support_pass",
    "evidence_support_watch",
    "evidence_support_block",
    "source_quality_pass",
    "source_quality_watch",
    "source_quality_block",
    "volatility_pass",
    "volatility_watch",
    "volatility_block",
    "consensus_reversal_score_pass",
    "consensus_reversal_score_watch",
    "consensus_reversal_score_block",
)
UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate" "_id",
    "mar" "ket" "_id",
    "mar" "ket" "_sl" "ug",
    "ques" "tion",
    "u" "rl",
    "://",
    "?",
    "#",
    "sou" "rce" "_ref",
    "sou" "rce" "_report",
    "sou" "rce" "_te" "xt",
    "sou" "rce" "_u" "rl",
    "d" "sn",
    "tab" "le",
    "tok" "en",
    "sec" "ret",
    "au" "th",
    "wal" "let",
    "or" "der",
    "tra" "de",
    "b" "uy",
    "se" "ll",
    "recom" "mend",
    "pos" "ition",
)


@dataclass(frozen=True)
class CandidateDecisionConsensusReversalScoreConfig:
    config_version: str = (
        DEFAULT_CANDIDATE_DECISION_CONSENSUS_REVERSAL_SCORE_CONFIG_VERSION
    )
    watch_consensus_delta: Decimal = Decimal("0.150000")
    block_consensus_delta: Decimal = Decimal("0.350000")
    watch_reversal_velocity_score: Decimal = Decimal("0.400000")
    block_reversal_velocity_score: Decimal = Decimal("0.850000")
    min_evidence_support_score_for_pass: Decimal = Decimal("0.650000")
    block_evidence_support_score_floor: Decimal = Decimal("0.250000")
    min_source_quality_score_for_pass: Decimal = Decimal("0.550000")
    block_source_quality_score_floor: Decimal = Decimal("0.300000")
    watch_volatility_score: Decimal = Decimal("0.500000")
    block_volatility_score: Decimal = Decimal("0.750000")
    watch_consensus_reversal_score: Decimal = Decimal("0.350000")
    block_consensus_reversal_score: Decimal = Decimal("0.750000")
    consensus_delta_weight: Decimal = Decimal("0.000000")
    reversal_velocity_weight: Decimal = Decimal("0.450000")
    evidence_gap_weight: Decimal = Decimal("0.250000")
    source_quality_gap_weight: Decimal = Decimal("0.150000")
    volatility_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionConsensusReversalScoreConfig:
            raise TypeError(
                "CandidateDecisionConsensusReversalScoreConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionConsensusReversalScoreConfig:
            raise ValueError(
                "config must be exactly "
                "CandidateDecisionConsensusReversalScoreConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in _CONFIG_RATIO_FIELD_NAMES:
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config_values(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class CandidateDecisionConsensusReversalScoreInput:
    redacted_candidate_ref: str
    current_consensus_score: Decimal
    prior_consensus_score: Decimal
    reversal_velocity_score: Decimal
    evidence_support_score: Decimal
    source_quality_score: Decimal
    volatility_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionConsensusReversalScoreInput:
            raise TypeError(
                "CandidateDecisionConsensusReversalScoreInput "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionConsensusReversalScoreInput:
            raise ValueError(
                "input_value must be exactly "
                "CandidateDecisionConsensusReversalScoreInput",
            )
        _require_canonical_string("redacted_candidate_ref", self.redacted_candidate_ref)
        _require_redacted_candidate_ref(self.redacted_candidate_ref)
        for field_name in _INPUT_RATIO_FIELD_NAMES:
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input_value", self)
        _reject_unsafe_public_payload("input_value", self)


@dataclass(frozen=True)
class CandidateDecisionConsensusReversalScoreReport:
    generated_at: datetime
    config_version: str
    redacted_candidate_ref: str
    current_consensus_score: Decimal
    prior_consensus_score: Decimal
    consensus_delta: Decimal
    absolute_consensus_delta: Decimal
    reversal_velocity_score: Decimal
    evidence_support_score: Decimal
    evidence_gap_score: Decimal
    source_quality_score: Decimal
    source_quality_gap_score: Decimal
    volatility_score: Decimal
    consensus_reversal_score: Decimal
    reversal_status: str
    hard_flag_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    watch_consensus_delta: Decimal
    block_consensus_delta: Decimal
    watch_reversal_velocity_score: Decimal
    block_reversal_velocity_score: Decimal
    min_evidence_support_score_for_pass: Decimal
    block_evidence_support_score_floor: Decimal
    min_source_quality_score_for_pass: Decimal
    block_source_quality_score_floor: Decimal
    watch_volatility_score: Decimal
    block_volatility_score: Decimal
    watch_consensus_reversal_score: Decimal
    block_consensus_reversal_score: Decimal
    consensus_delta_weight: Decimal
    reversal_velocity_weight: Decimal
    evidence_gap_weight: Decimal
    source_quality_gap_weight: Decimal
    volatility_weight: Decimal
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionConsensusReversalScoreReport:
            raise TypeError(
                "CandidateDecisionConsensusReversalScoreReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionConsensusReversalScoreReport:
            raise ValueError(
                "report must be exactly "
                "CandidateDecisionConsensusReversalScoreReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("redacted_candidate_ref", self.redacted_candidate_ref)
        _require_redacted_candidate_ref(self.redacted_candidate_ref)
        for field_name in _REPORT_RATIO_FIELD_NAMES:
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "consensus_delta",
            _normalize_decimal("consensus_delta", self.consensus_delta),
        )
        _require_reversal_status("reversal_status", self.reversal_status)
        object.__setattr__(
            self,
            "hard_flag_codes",
            _normalize_hard_flag_codes(self.hard_flag_codes),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_validation_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_config_values(self)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")


def build_candidate_decision_consensus_reversal_score_report(
    input_value: CandidateDecisionConsensusReversalScoreInput,
    *,
    generated_at: datetime,
    config: CandidateDecisionConsensusReversalScoreConfig | None = None,
) -> CandidateDecisionConsensusReversalScoreReport:
    if type(input_value) is not CandidateDecisionConsensusReversalScoreInput:
        raise ValueError(
            "input_value must be a CandidateDecisionConsensusReversalScoreInput",
        )
    if config is None:
        config = CandidateDecisionConsensusReversalScoreConfig()
    if type(config) is not CandidateDecisionConsensusReversalScoreConfig:
        raise ValueError(
            "config must be a CandidateDecisionConsensusReversalScoreConfig",
        )
    _require_hard_flags("input_value", input_value)
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    consensus_delta = _consensus_delta(
        input_value.current_consensus_score,
        input_value.prior_consensus_score,
    )
    absolute_consensus_delta = _absolute_decimal(consensus_delta)
    evidence_gap_score = _unit_gap(
        "evidence_gap_score",
        input_value.evidence_support_score,
    )
    source_quality_gap_score = _unit_gap(
        "source_quality_gap_score",
        input_value.source_quality_score,
    )
    consensus_reversal_score = _consensus_reversal_score(
        absolute_consensus_delta=absolute_consensus_delta,
        reversal_velocity_score=input_value.reversal_velocity_score,
        evidence_gap_score=evidence_gap_score,
        source_quality_gap_score=source_quality_gap_score,
        volatility_score=input_value.volatility_score,
        consensus_delta_weight=config.consensus_delta_weight,
        reversal_velocity_weight=config.reversal_velocity_weight,
        evidence_gap_weight=config.evidence_gap_weight,
        source_quality_gap_weight=config.source_quality_gap_weight,
        volatility_weight=config.volatility_weight,
    )
    hard_flag_codes = _hard_flag_codes_for_values(
        absolute_consensus_delta=absolute_consensus_delta,
        reversal_velocity_score=input_value.reversal_velocity_score,
        evidence_support_score=input_value.evidence_support_score,
        block_consensus_delta=config.block_consensus_delta,
        block_reversal_velocity_score=config.block_reversal_velocity_score,
        block_evidence_support_score_floor=config.block_evidence_support_score_floor,
    )
    reversal_status = _reversal_status_for_values(
        absolute_consensus_delta=absolute_consensus_delta,
        reversal_velocity_score=input_value.reversal_velocity_score,
        evidence_support_score=input_value.evidence_support_score,
        source_quality_score=input_value.source_quality_score,
        volatility_score=input_value.volatility_score,
        consensus_reversal_score=consensus_reversal_score,
        hard_flag_codes=hard_flag_codes,
        watch_consensus_delta=config.watch_consensus_delta,
        block_consensus_delta=config.block_consensus_delta,
        watch_reversal_velocity_score=config.watch_reversal_velocity_score,
        block_reversal_velocity_score=config.block_reversal_velocity_score,
        min_evidence_support_score_for_pass=(
            config.min_evidence_support_score_for_pass
        ),
        block_evidence_support_score_floor=config.block_evidence_support_score_floor,
        min_source_quality_score_for_pass=config.min_source_quality_score_for_pass,
        block_source_quality_score_floor=config.block_source_quality_score_floor,
        watch_volatility_score=config.watch_volatility_score,
        block_volatility_score=config.block_volatility_score,
        watch_consensus_reversal_score=config.watch_consensus_reversal_score,
        block_consensus_reversal_score=config.block_consensus_reversal_score,
    )
    reason_codes = _reason_codes_for_values(
        reversal_status=reversal_status,
        absolute_consensus_delta=absolute_consensus_delta,
        reversal_velocity_score=input_value.reversal_velocity_score,
        evidence_support_score=input_value.evidence_support_score,
        source_quality_score=input_value.source_quality_score,
        volatility_score=input_value.volatility_score,
        consensus_reversal_score=consensus_reversal_score,
        watch_consensus_delta=config.watch_consensus_delta,
        block_consensus_delta=config.block_consensus_delta,
        watch_reversal_velocity_score=config.watch_reversal_velocity_score,
        block_reversal_velocity_score=config.block_reversal_velocity_score,
        min_evidence_support_score_for_pass=(
            config.min_evidence_support_score_for_pass
        ),
        block_evidence_support_score_floor=config.block_evidence_support_score_floor,
        min_source_quality_score_for_pass=config.min_source_quality_score_for_pass,
        block_source_quality_score_floor=config.block_source_quality_score_floor,
        watch_volatility_score=config.watch_volatility_score,
        block_volatility_score=config.block_volatility_score,
        watch_consensus_reversal_score=config.watch_consensus_reversal_score,
        block_consensus_reversal_score=config.block_consensus_reversal_score,
    )
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "redacted_candidate_ref": input_value.redacted_candidate_ref,
        "current_consensus_score": input_value.current_consensus_score,
        "prior_consensus_score": input_value.prior_consensus_score,
        "consensus_delta": consensus_delta,
        "absolute_consensus_delta": absolute_consensus_delta,
        "reversal_velocity_score": input_value.reversal_velocity_score,
        "evidence_support_score": input_value.evidence_support_score,
        "evidence_gap_score": evidence_gap_score,
        "source_quality_score": input_value.source_quality_score,
        "source_quality_gap_score": source_quality_gap_score,
        "volatility_score": input_value.volatility_score,
        "consensus_reversal_score": consensus_reversal_score,
        "reversal_status": reversal_status,
        "hard_flag_codes": hard_flag_codes,
        "reason_codes": reason_codes,
        "watch_consensus_delta": config.watch_consensus_delta,
        "block_consensus_delta": config.block_consensus_delta,
        "watch_reversal_velocity_score": config.watch_reversal_velocity_score,
        "block_reversal_velocity_score": config.block_reversal_velocity_score,
        "min_evidence_support_score_for_pass": (
            config.min_evidence_support_score_for_pass
        ),
        "block_evidence_support_score_floor": config.block_evidence_support_score_floor,
        "min_source_quality_score_for_pass": config.min_source_quality_score_for_pass,
        "block_source_quality_score_floor": config.block_source_quality_score_floor,
        "watch_volatility_score": config.watch_volatility_score,
        "block_volatility_score": config.block_volatility_score,
        "watch_consensus_reversal_score": config.watch_consensus_reversal_score,
        "block_consensus_reversal_score": config.block_consensus_reversal_score,
        "consensus_delta_weight": config.consensus_delta_weight,
        "reversal_velocity_weight": config.reversal_velocity_weight,
        "evidence_gap_weight": config.evidence_gap_weight,
        "source_quality_gap_weight": config.source_quality_gap_weight,
        "volatility_weight": config.volatility_weight,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return CandidateDecisionConsensusReversalScoreReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def candidate_decision_consensus_reversal_score_payload(
    report: CandidateDecisionConsensusReversalScoreReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is CandidateDecisionConsensusReversalScoreReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        _validate_report_consistency(report)
        if report.derived_validation_digest != _report_digest_from_values(
            _report_values_without_digest(report),
        ):
            raise ValueError("derived_validation_digest must match report fields")
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report, allow_json_containers=True)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a CandidateDecisionConsensusReversalScoreReport "
            "or payload",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _validate_payload(payload)
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    return payload


def _consensus_delta(current_score: Decimal, prior_score: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_decimal("consensus_delta", current_score - prior_score)


def _absolute_decimal(value: Decimal) -> Decimal:
    if value < ZERO:
        return _normalize_unit_decimal("absolute_consensus_delta", -value)
    return _normalize_unit_decimal("absolute_consensus_delta", value)


def _unit_gap(field_name: str, value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_unit_decimal(field_name, ONE - value)


def _consensus_reversal_score(
    *,
    absolute_consensus_delta: Decimal,
    reversal_velocity_score: Decimal,
    evidence_gap_score: Decimal,
    source_quality_gap_score: Decimal,
    volatility_score: Decimal,
    consensus_delta_weight: Decimal,
    reversal_velocity_weight: Decimal,
    evidence_gap_weight: Decimal,
    source_quality_gap_weight: Decimal,
    volatility_weight: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            absolute_consensus_delta * consensus_delta_weight
            + reversal_velocity_score * reversal_velocity_weight
            + evidence_gap_score * evidence_gap_weight
            + source_quality_gap_score * source_quality_gap_weight
            + volatility_score * volatility_weight
        )
    return _normalize_unit_decimal("consensus_reversal_score", score)


def _hard_flag_codes_for_values(
    *,
    absolute_consensus_delta: Decimal,
    reversal_velocity_score: Decimal,
    evidence_support_score: Decimal,
    block_consensus_delta: Decimal,
    block_reversal_velocity_score: Decimal,
    block_evidence_support_score_floor: Decimal,
) -> tuple[str, ...]:
    codes: list[str] = []
    if reversal_velocity_score >= block_reversal_velocity_score:
        codes.append("reversal_velocity_block")
    if (
        absolute_consensus_delta >= block_consensus_delta
        and evidence_support_score <= block_evidence_support_score_floor
    ):
        codes.append("weak_evidence_reversal_block")
    return _normalize_hard_flag_codes(tuple(codes), allow_empty=True)


def _reversal_status_for_values(
    *,
    absolute_consensus_delta: Decimal,
    reversal_velocity_score: Decimal,
    evidence_support_score: Decimal,
    source_quality_score: Decimal,
    volatility_score: Decimal,
    consensus_reversal_score: Decimal,
    hard_flag_codes: tuple[str, ...],
    watch_consensus_delta: Decimal,
    block_consensus_delta: Decimal,
    watch_reversal_velocity_score: Decimal,
    block_reversal_velocity_score: Decimal,
    min_evidence_support_score_for_pass: Decimal,
    block_evidence_support_score_floor: Decimal,
    min_source_quality_score_for_pass: Decimal,
    block_source_quality_score_floor: Decimal,
    watch_volatility_score: Decimal,
    block_volatility_score: Decimal,
    watch_consensus_reversal_score: Decimal,
    block_consensus_reversal_score: Decimal,
) -> str:
    if hard_flag_codes:
        return "block"
    if consensus_reversal_score >= block_consensus_reversal_score:
        return "block"
    if absolute_consensus_delta >= block_consensus_delta:
        return "block"
    if reversal_velocity_score >= block_reversal_velocity_score:
        return "block"
    if evidence_support_score <= block_evidence_support_score_floor:
        return "block"
    if source_quality_score <= block_source_quality_score_floor:
        return "block"
    if volatility_score >= block_volatility_score:
        return "block"
    if consensus_reversal_score >= watch_consensus_reversal_score:
        return "watch"
    if absolute_consensus_delta >= watch_consensus_delta:
        return "watch"
    if reversal_velocity_score >= watch_reversal_velocity_score:
        return "watch"
    if evidence_support_score < min_evidence_support_score_for_pass:
        return "watch"
    if source_quality_score < min_source_quality_score_for_pass:
        return "watch"
    if volatility_score >= watch_volatility_score:
        return "watch"
    return "pass"


def _reason_codes_for_values(
    *,
    reversal_status: str,
    absolute_consensus_delta: Decimal,
    reversal_velocity_score: Decimal,
    evidence_support_score: Decimal,
    source_quality_score: Decimal,
    volatility_score: Decimal,
    consensus_reversal_score: Decimal,
    watch_consensus_delta: Decimal,
    block_consensus_delta: Decimal,
    watch_reversal_velocity_score: Decimal,
    block_reversal_velocity_score: Decimal,
    min_evidence_support_score_for_pass: Decimal,
    block_evidence_support_score_floor: Decimal,
    min_source_quality_score_for_pass: Decimal,
    block_source_quality_score_floor: Decimal,
    watch_volatility_score: Decimal,
    block_volatility_score: Decimal,
    watch_consensus_reversal_score: Decimal,
    block_consensus_reversal_score: Decimal,
) -> tuple[str, ...]:
    codes = [f"consensus_reversal_{reversal_status}"]
    if absolute_consensus_delta >= block_consensus_delta:
        codes.append("consensus_delta_block")
    elif absolute_consensus_delta >= watch_consensus_delta:
        codes.append("consensus_delta_watch")
    else:
        codes.append("consensus_delta_pass")
    if reversal_velocity_score >= block_reversal_velocity_score:
        codes.append("reversal_velocity_block")
    elif reversal_velocity_score >= watch_reversal_velocity_score:
        codes.append("reversal_velocity_watch")
    else:
        codes.append("reversal_velocity_pass")
    if evidence_support_score <= block_evidence_support_score_floor:
        codes.append("evidence_support_block")
    elif evidence_support_score < min_evidence_support_score_for_pass:
        codes.append("evidence_support_watch")
    else:
        codes.append("evidence_support_pass")
    if source_quality_score <= block_source_quality_score_floor:
        codes.append("source_quality_block")
    elif source_quality_score < min_source_quality_score_for_pass:
        codes.append("source_quality_watch")
    else:
        codes.append("source_quality_pass")
    if volatility_score >= block_volatility_score:
        codes.append("volatility_block")
    elif volatility_score >= watch_volatility_score:
        codes.append("volatility_watch")
    else:
        codes.append("volatility_pass")
    if consensus_reversal_score >= block_consensus_reversal_score:
        codes.append("consensus_reversal_score_block")
    elif consensus_reversal_score >= watch_consensus_reversal_score:
        codes.append("consensus_reversal_score_watch")
    else:
        codes.append("consensus_reversal_score_pass")
    return _normalize_reason_codes(tuple(codes))


def _validate_config_values(
    value: (
        CandidateDecisionConsensusReversalScoreConfig
        | CandidateDecisionConsensusReversalScoreReport
    ),
) -> None:
    if value.watch_consensus_delta > value.block_consensus_delta:
        raise ValueError("watch_consensus_delta must not exceed block_consensus_delta")
    if value.watch_reversal_velocity_score > value.block_reversal_velocity_score:
        raise ValueError(
            "watch_reversal_velocity_score must not exceed "
            "block_reversal_velocity_score",
        )
    if (
        value.block_evidence_support_score_floor
        > value.min_evidence_support_score_for_pass
    ):
        raise ValueError(
            "block_evidence_support_score_floor must not exceed "
            "min_evidence_support_score_for_pass",
        )
    if value.block_source_quality_score_floor > value.min_source_quality_score_for_pass:
        raise ValueError(
            "block_source_quality_score_floor must not exceed "
            "min_source_quality_score_for_pass",
        )
    if value.watch_volatility_score > value.block_volatility_score:
        raise ValueError("watch_volatility_score must not exceed block_volatility_score")
    if value.watch_consensus_reversal_score > value.block_consensus_reversal_score:
        raise ValueError(
            "watch_consensus_reversal_score must not exceed "
            "block_consensus_reversal_score",
        )
    weight_total = _normalize_unit_decimal(
        "weight_total",
        (
            value.consensus_delta_weight
            + value.reversal_velocity_weight
            + value.evidence_gap_weight
            + value.source_quality_gap_weight
            + value.volatility_weight
        ),
    )
    if weight_total != ONE:
        raise ValueError("score weights must sum to 1.000000")


def _validate_report_consistency(
    report: CandidateDecisionConsensusReversalScoreReport,
) -> None:
    expected_consensus_delta = _consensus_delta(
        report.current_consensus_score,
        report.prior_consensus_score,
    )
    expected_absolute_consensus_delta = _absolute_decimal(expected_consensus_delta)
    expected_evidence_gap_score = _unit_gap(
        "evidence_gap_score",
        report.evidence_support_score,
    )
    expected_source_quality_gap_score = _unit_gap(
        "source_quality_gap_score",
        report.source_quality_score,
    )
    expected_consensus_reversal_score = _consensus_reversal_score(
        absolute_consensus_delta=expected_absolute_consensus_delta,
        reversal_velocity_score=report.reversal_velocity_score,
        evidence_gap_score=expected_evidence_gap_score,
        source_quality_gap_score=expected_source_quality_gap_score,
        volatility_score=report.volatility_score,
        consensus_delta_weight=report.consensus_delta_weight,
        reversal_velocity_weight=report.reversal_velocity_weight,
        evidence_gap_weight=report.evidence_gap_weight,
        source_quality_gap_weight=report.source_quality_gap_weight,
        volatility_weight=report.volatility_weight,
    )
    expected_hard_flag_codes = _hard_flag_codes_for_values(
        absolute_consensus_delta=expected_absolute_consensus_delta,
        reversal_velocity_score=report.reversal_velocity_score,
        evidence_support_score=report.evidence_support_score,
        block_consensus_delta=report.block_consensus_delta,
        block_reversal_velocity_score=report.block_reversal_velocity_score,
        block_evidence_support_score_floor=report.block_evidence_support_score_floor,
    )
    expected_reversal_status = _reversal_status_for_values(
        absolute_consensus_delta=expected_absolute_consensus_delta,
        reversal_velocity_score=report.reversal_velocity_score,
        evidence_support_score=report.evidence_support_score,
        source_quality_score=report.source_quality_score,
        volatility_score=report.volatility_score,
        consensus_reversal_score=expected_consensus_reversal_score,
        hard_flag_codes=expected_hard_flag_codes,
        watch_consensus_delta=report.watch_consensus_delta,
        block_consensus_delta=report.block_consensus_delta,
        watch_reversal_velocity_score=report.watch_reversal_velocity_score,
        block_reversal_velocity_score=report.block_reversal_velocity_score,
        min_evidence_support_score_for_pass=(
            report.min_evidence_support_score_for_pass
        ),
        block_evidence_support_score_floor=report.block_evidence_support_score_floor,
        min_source_quality_score_for_pass=report.min_source_quality_score_for_pass,
        block_source_quality_score_floor=report.block_source_quality_score_floor,
        watch_volatility_score=report.watch_volatility_score,
        block_volatility_score=report.block_volatility_score,
        watch_consensus_reversal_score=report.watch_consensus_reversal_score,
        block_consensus_reversal_score=report.block_consensus_reversal_score,
    )
    expected_reason_codes = _reason_codes_for_values(
        reversal_status=expected_reversal_status,
        absolute_consensus_delta=expected_absolute_consensus_delta,
        reversal_velocity_score=report.reversal_velocity_score,
        evidence_support_score=report.evidence_support_score,
        source_quality_score=report.source_quality_score,
        volatility_score=report.volatility_score,
        consensus_reversal_score=expected_consensus_reversal_score,
        watch_consensus_delta=report.watch_consensus_delta,
        block_consensus_delta=report.block_consensus_delta,
        watch_reversal_velocity_score=report.watch_reversal_velocity_score,
        block_reversal_velocity_score=report.block_reversal_velocity_score,
        min_evidence_support_score_for_pass=(
            report.min_evidence_support_score_for_pass
        ),
        block_evidence_support_score_floor=report.block_evidence_support_score_floor,
        min_source_quality_score_for_pass=report.min_source_quality_score_for_pass,
        block_source_quality_score_floor=report.block_source_quality_score_floor,
        watch_volatility_score=report.watch_volatility_score,
        block_volatility_score=report.block_volatility_score,
        watch_consensus_reversal_score=report.watch_consensus_reversal_score,
        block_consensus_reversal_score=report.block_consensus_reversal_score,
    )
    if report.consensus_delta != expected_consensus_delta:
        raise ValueError("consensus_delta must match consensus inputs")
    if report.absolute_consensus_delta != expected_absolute_consensus_delta:
        raise ValueError("absolute_consensus_delta must match consensus_delta")
    if report.evidence_gap_score != expected_evidence_gap_score:
        raise ValueError("evidence_gap_score must match evidence_support_score")
    if report.source_quality_gap_score != expected_source_quality_gap_score:
        raise ValueError("source_quality_gap_score must match source_quality_score")
    if report.consensus_reversal_score != expected_consensus_reversal_score:
        raise ValueError("consensus_reversal_score must match weighted components")
    if report.hard_flag_codes != expected_hard_flag_codes:
        raise ValueError("hard_flag_codes must match report fields")
    if report.hard_flag_codes and report.reversal_status != "block":
        raise ValueError("hard_flag_codes require block status")
    if report.reversal_status != expected_reversal_status:
        raise ValueError("reversal_status must match report fields")
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match report fields")


def _report_values_without_digest(
    report: CandidateDecisionConsensusReversalScoreReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(dict(values))
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    _reject_unsafe_public_payload(
        "digest payload",
        payload,
        allow_json_containers=True,
    )
    return _json_payload_digest(payload)


def _validate_payload(payload: dict[str, Any]) -> None:
    expected_keys = {
        field.name for field in fields(CandidateDecisionConsensusReversalScoreReport)
    }
    if set(payload) != expected_keys:
        raise ValueError("payload must contain exactly report fields")
    _require_hard_flags("payload", _PayloadFlags(payload))
    _require_reversal_status("reversal_status", payload["reversal_status"])
    _require_validation_digest(
        "derived_validation_digest",
        payload["derived_validation_digest"],
    )
    if payload["derived_validation_digest"] != _json_payload_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")


def _json_payload_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    canonical = json.dumps(
        digest_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _normalize_hard_flag_codes(
    value: object,
    *,
    allow_empty: bool = True,
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("hard_flag_codes must be a list or tuple")
    codes = tuple(value)
    if not codes and not allow_empty:
        raise ValueError("hard_flag_codes must not be empty")
    for code in codes:
        _require_canonical_string("hard_flag_codes", code)
        if code not in HARD_FLAG_CODES:
            raise ValueError("hard_flag_codes must contain supported hard flags")
    if len(set(codes)) != len(codes):
        raise ValueError("hard_flag_codes must be unique")
    return tuple(code for code in HARD_FLAG_CODES if code in codes)


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    codes = tuple(value)
    if not codes:
        raise ValueError("reason_codes must not be empty")
    for code in codes:
        _require_canonical_string("reason_codes", code)
        if code not in REASON_CODE_SEQUENCE:
            raise ValueError("reason_codes must contain supported reasons")
    if len(set(codes)) != len(codes):
        raise ValueError("reason_codes must be unique")
    status_reasons = tuple(
        code for code in codes if code in REVERSAL_STATUS_REASON_CODES
    )
    if len(status_reasons) != 1:
        raise ValueError("reason_codes must contain one reversal status reason")
    return tuple(code for code in REASON_CODE_SEQUENCE if code in codes)


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
    return _quantize_ratio(value)


def _quantize_ratio(value: Decimal) -> Decimal:
    return value.quantize(SCORE_QUANT, rounding=ROUND_HALF_EVEN)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be a datetime")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_redacted_candidate_ref(value: str) -> None:
    if not value.startswith("redacted:"):
        raise ValueError("redacted_candidate_ref must be redacted")
    suffix = value.removeprefix("redacted:")
    if not suffix:
        raise ValueError("redacted_candidate_ref must be redacted")
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_:")
    if any(char not in allowed for char in suffix):
        raise ValueError("redacted_candidate_ref has unsafe public value")


def _require_reversal_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REVERSAL_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_validation_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
    path: str = "",
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in (
            CandidateDecisionConsensusReversalScoreConfig,
            CandidateDecisionConsensusReversalScoreInput,
            CandidateDecisionConsensusReversalScoreReport,
        ):
            raise ValueError(f"{current_path} must be a supported public dataclass")
        for field in fields(value):
            if _has_unsafe_public_fragment(field.name):
                raise ValueError(f"{field.name} has unsafe public field")
            field_path = field.name if not path else f"{path}.{field.name}"
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                allow_json_containers=allow_json_containers,
                path=field_path,
            )
        return
    if type(value) is dict:
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"{item_path} has unsafe public field")
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=True,
                path=item_path,
            )
        return
    if type(value) is list:
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=True,
                path=f"{current_path}[{index}]",
            )
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
                path=f"{current_path}[{index}]",
            )
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{current_path} must be finite")
        return
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{current_path} must be timezone-aware")
        return
    if type(value) is str:
        if value.strip() != value:
            raise ValueError(f"{current_path} has unsafe public value")
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"{current_path} has unsafe public value")
        return
    if value is None or type(value) is bool:
        return
    if type(value) in (int, float):
        raise ValueError(f"{current_path} must use Decimal-derived string values")
    raise ValueError(f"{current_path} is not JSON-ready")


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC).isoformat()
        return value.astimezone(UTC).isoformat()
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, dict):
        return _json_dict(value)
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _json_dict(value: dict[Any, Any]) -> dict[str, Any]:
    ready: dict[str, Any] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError("JSON object keys must be strings")
        ready[key] = _json_ready(item)
    return ready


@dataclass(frozen=True)
class _PayloadFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


_CONFIG_RATIO_FIELD_NAMES = (
    "watch_consensus_delta",
    "block_consensus_delta",
    "watch_reversal_velocity_score",
    "block_reversal_velocity_score",
    "min_evidence_support_score_for_pass",
    "block_evidence_support_score_floor",
    "min_source_quality_score_for_pass",
    "block_source_quality_score_floor",
    "watch_volatility_score",
    "block_volatility_score",
    "watch_consensus_reversal_score",
    "block_consensus_reversal_score",
    "consensus_delta_weight",
    "reversal_velocity_weight",
    "evidence_gap_weight",
    "source_quality_gap_weight",
    "volatility_weight",
)
_INPUT_RATIO_FIELD_NAMES = (
    "current_consensus_score",
    "prior_consensus_score",
    "reversal_velocity_score",
    "evidence_support_score",
    "source_quality_score",
    "volatility_score",
)
_REPORT_RATIO_FIELD_NAMES = (
    "current_consensus_score",
    "prior_consensus_score",
    "absolute_consensus_delta",
    "reversal_velocity_score",
    "evidence_support_score",
    "evidence_gap_score",
    "source_quality_score",
    "source_quality_gap_score",
    "volatility_score",
    "consensus_reversal_score",
    *_CONFIG_RATIO_FIELD_NAMES,
)
REVERSAL_STATUS_REASON_CODES = (
    "consensus_reversal_pass",
    "consensus_reversal_watch",
    "consensus_reversal_block",
)


__all__ = (
    "DEFAULT_CANDIDATE_DECISION_CONSENSUS_REVERSAL_SCORE_CONFIG_VERSION",
    "CandidateDecisionConsensusReversalScoreConfig",
    "CandidateDecisionConsensusReversalScoreInput",
    "CandidateDecisionConsensusReversalScoreReport",
    "build_candidate_decision_consensus_reversal_score_report",
    "candidate_decision_consensus_reversal_score_payload",
)
