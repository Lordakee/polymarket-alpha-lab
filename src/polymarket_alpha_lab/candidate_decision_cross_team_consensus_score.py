"""Pure paper-only cross-team consensus pressure score."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from .team_taxonomy import require_team_id


DEFAULT_CANDIDATE_DECISION_CROSS_TEAM_CONSENSUS_SCORE_CONFIG_VERSION = (
    "candidate-decision-cross-team-consensus-score-v0"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

CONSENSUS_STATUSES = ("pass", "watch", "block")
HARD_FLAG_CODES = (
    "specialist_count_block",
    "dissent_pressure_block",
)
REASON_CODE_SEQUENCE = (
    "cross_team_consensus_pass",
    "cross_team_consensus_watch",
    "cross_team_consensus_block",
    "specialist_count_pass",
    "specialist_count_watch",
    "specialist_count_block",
    "agreement_ratio_pass",
    "agreement_ratio_watch",
    "dissent_pressure_pass",
    "dissent_pressure_watch",
    "dissent_pressure_block",
    "historical_calibration_pass",
    "historical_calibration_watch",
    "consensus_score_pass",
    "consensus_score_watch",
    "consensus_score_block",
)
UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate" "_id",
    "mar" "ket",
    "sl" "ug",
    "ques" "tion",
    "u" "rl",
    "://",
    "?",
    "#",
    "sou" "rce",
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
    "te" "xt",
)


@dataclass(frozen=True)
class CandidateDecisionCrossTeamConsensusScoreConfig:
    config_version: str = (
        DEFAULT_CANDIDATE_DECISION_CROSS_TEAM_CONSENSUS_SCORE_CONFIG_VERSION
    )
    min_specialist_count_for_watch: Decimal = Decimal("2")
    min_specialist_count_for_pass: Decimal = Decimal("3")
    min_agreement_ratio_for_pass: Decimal = Decimal("0.666667")
    max_dissent_pressure_for_pass: Decimal = Decimal("0.200000")
    block_dissent_severity_score: Decimal = Decimal("0.900000")
    block_consensus_score_floor: Decimal = Decimal("0.300000")
    pass_consensus_score_floor: Decimal = Decimal("0.700000")
    min_historical_calibration_score_for_pass: Decimal = Decimal("0.500000")
    agreement_weight: Decimal = Decimal("0.400000")
    confidence_weight: Decimal = Decimal("0.200000")
    calibration_weight: Decimal = Decimal("0.250000")
    dissent_resistance_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionCrossTeamConsensusScoreConfig:
            raise TypeError(
                "CandidateDecisionCrossTeamConsensusScoreConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionCrossTeamConsensusScoreConfig:
            raise ValueError(
                "config must be exactly "
                "CandidateDecisionCrossTeamConsensusScoreConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "min_specialist_count_for_watch",
            "min_specialist_count_for_pass",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
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
class CandidateDecisionCrossTeamConsensusScoreInput:
    redacted_candidate_ref: str
    primary_team_id: str
    specialist_count: Decimal
    agreeing_team_count: Decimal
    dissenting_team_count: Decimal
    average_confidence_score: Decimal
    dissent_severity_score: Decimal
    historical_calibration_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionCrossTeamConsensusScoreInput:
            raise TypeError(
                "CandidateDecisionCrossTeamConsensusScoreInput "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionCrossTeamConsensusScoreInput:
            raise ValueError(
                "input_value must be exactly "
                "CandidateDecisionCrossTeamConsensusScoreInput",
            )
        _require_canonical_string("redacted_candidate_ref", self.redacted_candidate_ref)
        _require_redacted_candidate_ref(self.redacted_candidate_ref)
        object.__setattr__(
            self,
            "primary_team_id",
            require_team_id("primary_team_id", self.primary_team_id),
        )
        for field_name in (
            "specialist_count",
            "agreeing_team_count",
            "dissenting_team_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "average_confidence_score",
            "dissent_severity_score",
            "historical_calibration_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _validate_count_values(self)
        _require_hard_flags("input_value", self)
        _reject_unsafe_public_payload("input_value", self)


@dataclass(frozen=True)
class CandidateDecisionCrossTeamConsensusScoreReport:
    generated_at: datetime
    config_version: str
    redacted_candidate_ref: str
    primary_team_id: str
    specialist_count: Decimal
    agreeing_team_count: Decimal
    dissenting_team_count: Decimal
    agreement_ratio: Decimal
    dissent_ratio: Decimal
    average_confidence_score: Decimal
    dissent_severity_score: Decimal
    historical_calibration_score: Decimal
    dissent_pressure_score: Decimal
    dissent_resistance_score: Decimal
    consensus_score: Decimal
    consensus_status: str
    hard_flag_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    min_specialist_count_for_watch: Decimal
    min_specialist_count_for_pass: Decimal
    min_agreement_ratio_for_pass: Decimal
    max_dissent_pressure_for_pass: Decimal
    block_dissent_severity_score: Decimal
    block_consensus_score_floor: Decimal
    pass_consensus_score_floor: Decimal
    min_historical_calibration_score_for_pass: Decimal
    agreement_weight: Decimal
    confidence_weight: Decimal
    calibration_weight: Decimal
    dissent_resistance_weight: Decimal
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionCrossTeamConsensusScoreReport:
            raise TypeError(
                "CandidateDecisionCrossTeamConsensusScoreReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionCrossTeamConsensusScoreReport:
            raise ValueError(
                "report must be exactly "
                "CandidateDecisionCrossTeamConsensusScoreReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("redacted_candidate_ref", self.redacted_candidate_ref)
        _require_redacted_candidate_ref(self.redacted_candidate_ref)
        object.__setattr__(
            self,
            "primary_team_id",
            require_team_id("primary_team_id", self.primary_team_id),
        )
        for field_name in (
            "specialist_count",
            "agreeing_team_count",
            "dissenting_team_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in _REPORT_RATIO_FIELD_NAMES:
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_specialist_count_for_watch",
            "min_specialist_count_for_pass",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _require_consensus_status("consensus_status", self.consensus_status)
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
        _validate_count_values(self)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")


def build_candidate_decision_cross_team_consensus_score_report(
    input_value: CandidateDecisionCrossTeamConsensusScoreInput,
    *,
    generated_at: datetime,
    config: CandidateDecisionCrossTeamConsensusScoreConfig | None = None,
) -> CandidateDecisionCrossTeamConsensusScoreReport:
    if type(input_value) is not CandidateDecisionCrossTeamConsensusScoreInput:
        raise ValueError(
            "input_value must be a CandidateDecisionCrossTeamConsensusScoreInput",
        )
    if config is None:
        config = CandidateDecisionCrossTeamConsensusScoreConfig()
    if type(config) is not CandidateDecisionCrossTeamConsensusScoreConfig:
        raise ValueError(
            "config must be a CandidateDecisionCrossTeamConsensusScoreConfig",
        )
    _require_hard_flags("input_value", input_value)
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    agreement_ratio = _ratio(input_value.agreeing_team_count, input_value.specialist_count)
    dissent_ratio = _ratio(input_value.dissenting_team_count, input_value.specialist_count)
    dissent_pressure_score = _dissent_pressure_score(
        dissent_ratio,
        input_value.dissent_severity_score,
    )
    dissent_resistance_score = _normalize_unit_decimal(
        "dissent_resistance_score",
        ONE - dissent_pressure_score,
    )
    consensus_score = _consensus_score(
        agreement_ratio=agreement_ratio,
        average_confidence_score=input_value.average_confidence_score,
        historical_calibration_score=input_value.historical_calibration_score,
        dissent_resistance_score=dissent_resistance_score,
        agreement_weight=config.agreement_weight,
        confidence_weight=config.confidence_weight,
        calibration_weight=config.calibration_weight,
        dissent_resistance_weight=config.dissent_resistance_weight,
    )
    hard_flag_codes = _hard_flag_codes_for_values(
        specialist_count=input_value.specialist_count,
        dissenting_team_count=input_value.dissenting_team_count,
        dissent_severity_score=input_value.dissent_severity_score,
        min_specialist_count_for_watch=config.min_specialist_count_for_watch,
        block_dissent_severity_score=config.block_dissent_severity_score,
    )
    consensus_status = _consensus_status_for_values(
        specialist_count=input_value.specialist_count,
        agreement_ratio=agreement_ratio,
        dissent_pressure_score=dissent_pressure_score,
        historical_calibration_score=input_value.historical_calibration_score,
        consensus_score=consensus_score,
        hard_flag_codes=hard_flag_codes,
        min_specialist_count_for_pass=config.min_specialist_count_for_pass,
        min_agreement_ratio_for_pass=config.min_agreement_ratio_for_pass,
        max_dissent_pressure_for_pass=config.max_dissent_pressure_for_pass,
        min_historical_calibration_score_for_pass=(
            config.min_historical_calibration_score_for_pass
        ),
        block_consensus_score_floor=config.block_consensus_score_floor,
        pass_consensus_score_floor=config.pass_consensus_score_floor,
    )
    reason_codes = _reason_codes_for_values(
        consensus_status=consensus_status,
        specialist_count=input_value.specialist_count,
        agreement_ratio=agreement_ratio,
        dissent_pressure_score=dissent_pressure_score,
        historical_calibration_score=input_value.historical_calibration_score,
        consensus_score=consensus_score,
        hard_flag_codes=hard_flag_codes,
        min_specialist_count_for_watch=config.min_specialist_count_for_watch,
        min_specialist_count_for_pass=config.min_specialist_count_for_pass,
        min_agreement_ratio_for_pass=config.min_agreement_ratio_for_pass,
        max_dissent_pressure_for_pass=config.max_dissent_pressure_for_pass,
        min_historical_calibration_score_for_pass=(
            config.min_historical_calibration_score_for_pass
        ),
        block_consensus_score_floor=config.block_consensus_score_floor,
        pass_consensus_score_floor=config.pass_consensus_score_floor,
    )
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "redacted_candidate_ref": input_value.redacted_candidate_ref,
        "primary_team_id": input_value.primary_team_id,
        "specialist_count": input_value.specialist_count,
        "agreeing_team_count": input_value.agreeing_team_count,
        "dissenting_team_count": input_value.dissenting_team_count,
        "agreement_ratio": agreement_ratio,
        "dissent_ratio": dissent_ratio,
        "average_confidence_score": input_value.average_confidence_score,
        "dissent_severity_score": input_value.dissent_severity_score,
        "historical_calibration_score": input_value.historical_calibration_score,
        "dissent_pressure_score": dissent_pressure_score,
        "dissent_resistance_score": dissent_resistance_score,
        "consensus_score": consensus_score,
        "consensus_status": consensus_status,
        "hard_flag_codes": hard_flag_codes,
        "reason_codes": reason_codes,
        "min_specialist_count_for_watch": config.min_specialist_count_for_watch,
        "min_specialist_count_for_pass": config.min_specialist_count_for_pass,
        "min_agreement_ratio_for_pass": config.min_agreement_ratio_for_pass,
        "max_dissent_pressure_for_pass": config.max_dissent_pressure_for_pass,
        "block_dissent_severity_score": config.block_dissent_severity_score,
        "block_consensus_score_floor": config.block_consensus_score_floor,
        "pass_consensus_score_floor": config.pass_consensus_score_floor,
        "min_historical_calibration_score_for_pass": (
            config.min_historical_calibration_score_for_pass
        ),
        "agreement_weight": config.agreement_weight,
        "confidence_weight": config.confidence_weight,
        "calibration_weight": config.calibration_weight,
        "dissent_resistance_weight": config.dissent_resistance_weight,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return CandidateDecisionCrossTeamConsensusScoreReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def candidate_decision_cross_team_consensus_score_payload(
    report: CandidateDecisionCrossTeamConsensusScoreReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is CandidateDecisionCrossTeamConsensusScoreReport:
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
            "report must be a CandidateDecisionCrossTeamConsensusScoreReport "
            "or payload",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _validate_payload(payload)
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    return payload


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_ratio(numerator / denominator)


def _dissent_pressure_score(
    dissent_ratio: Decimal,
    dissent_severity_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_unit_decimal(
            "dissent_pressure_score",
            dissent_ratio * dissent_severity_score,
        )


def _consensus_score(
    *,
    agreement_ratio: Decimal,
    average_confidence_score: Decimal,
    historical_calibration_score: Decimal,
    dissent_resistance_score: Decimal,
    agreement_weight: Decimal,
    confidence_weight: Decimal,
    calibration_weight: Decimal,
    dissent_resistance_weight: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            agreement_ratio * agreement_weight
            + average_confidence_score * confidence_weight
            + historical_calibration_score * calibration_weight
            + dissent_resistance_score * dissent_resistance_weight
        )
    return _normalize_unit_decimal("consensus_score", score)


def _hard_flag_codes_for_values(
    *,
    specialist_count: Decimal,
    dissenting_team_count: Decimal,
    dissent_severity_score: Decimal,
    min_specialist_count_for_watch: Decimal,
    block_dissent_severity_score: Decimal,
) -> tuple[str, ...]:
    codes: list[str] = []
    if specialist_count < min_specialist_count_for_watch:
        codes.append("specialist_count_block")
    if (
        dissenting_team_count > ZERO
        and dissent_severity_score >= block_dissent_severity_score
    ):
        codes.append("dissent_pressure_block")
    return _normalize_hard_flag_codes(tuple(codes), allow_empty=True)


def _consensus_status_for_values(
    *,
    specialist_count: Decimal,
    agreement_ratio: Decimal,
    dissent_pressure_score: Decimal,
    historical_calibration_score: Decimal,
    consensus_score: Decimal,
    hard_flag_codes: tuple[str, ...],
    min_specialist_count_for_pass: Decimal,
    min_agreement_ratio_for_pass: Decimal,
    max_dissent_pressure_for_pass: Decimal,
    min_historical_calibration_score_for_pass: Decimal,
    block_consensus_score_floor: Decimal,
    pass_consensus_score_floor: Decimal,
) -> str:
    if hard_flag_codes:
        return "block"
    if consensus_score <= block_consensus_score_floor:
        return "block"
    if specialist_count < min_specialist_count_for_pass:
        return "watch"
    if agreement_ratio < min_agreement_ratio_for_pass:
        return "watch"
    if dissent_pressure_score > max_dissent_pressure_for_pass:
        return "watch"
    if historical_calibration_score < min_historical_calibration_score_for_pass:
        return "watch"
    if consensus_score >= pass_consensus_score_floor:
        return "pass"
    return "watch"


def _reason_codes_for_values(
    *,
    consensus_status: str,
    specialist_count: Decimal,
    agreement_ratio: Decimal,
    dissent_pressure_score: Decimal,
    historical_calibration_score: Decimal,
    consensus_score: Decimal,
    hard_flag_codes: tuple[str, ...],
    min_specialist_count_for_watch: Decimal,
    min_specialist_count_for_pass: Decimal,
    min_agreement_ratio_for_pass: Decimal,
    max_dissent_pressure_for_pass: Decimal,
    min_historical_calibration_score_for_pass: Decimal,
    block_consensus_score_floor: Decimal,
    pass_consensus_score_floor: Decimal,
) -> tuple[str, ...]:
    codes = [f"cross_team_consensus_{consensus_status}"]
    if specialist_count < min_specialist_count_for_watch:
        codes.append("specialist_count_block")
    elif specialist_count < min_specialist_count_for_pass:
        codes.append("specialist_count_watch")
    else:
        codes.append("specialist_count_pass")
    if agreement_ratio >= min_agreement_ratio_for_pass:
        codes.append("agreement_ratio_pass")
    else:
        codes.append("agreement_ratio_watch")
    if "dissent_pressure_block" in hard_flag_codes:
        codes.append("dissent_pressure_block")
    elif dissent_pressure_score <= max_dissent_pressure_for_pass:
        codes.append("dissent_pressure_pass")
    else:
        codes.append("dissent_pressure_watch")
    if historical_calibration_score >= min_historical_calibration_score_for_pass:
        codes.append("historical_calibration_pass")
    else:
        codes.append("historical_calibration_watch")
    if consensus_score <= block_consensus_score_floor:
        codes.append("consensus_score_block")
    elif consensus_score >= pass_consensus_score_floor:
        codes.append("consensus_score_pass")
    else:
        codes.append("consensus_score_watch")
    return _normalize_reason_codes(tuple(codes))


def _validate_config_values(
    value: (
        CandidateDecisionCrossTeamConsensusScoreConfig
        | CandidateDecisionCrossTeamConsensusScoreReport
    ),
) -> None:
    if value.min_specialist_count_for_watch > value.min_specialist_count_for_pass:
        raise ValueError(
            "min_specialist_count_for_watch must not exceed "
            "min_specialist_count_for_pass",
        )
    if value.block_consensus_score_floor > value.pass_consensus_score_floor:
        raise ValueError(
            "block_consensus_score_floor must not exceed pass_consensus_score_floor",
        )
    weight_total = _normalize_unit_decimal(
        "weight_total",
        (
            value.agreement_weight
            + value.confidence_weight
            + value.calibration_weight
            + value.dissent_resistance_weight
        ),
    )
    if weight_total != ONE:
        raise ValueError("score weights must sum to 1.000000")


def _validate_count_values(
    value: (
        CandidateDecisionCrossTeamConsensusScoreInput
        | CandidateDecisionCrossTeamConsensusScoreReport
    ),
) -> None:
    if value.agreeing_team_count + value.dissenting_team_count > value.specialist_count:
        raise ValueError(
            "agreeing_team_count plus dissenting_team_count must not exceed "
            "specialist_count",
        )


def _validate_report_consistency(
    report: CandidateDecisionCrossTeamConsensusScoreReport,
) -> None:
    expected_agreement_ratio = _ratio(report.agreeing_team_count, report.specialist_count)
    expected_dissent_ratio = _ratio(report.dissenting_team_count, report.specialist_count)
    expected_dissent_pressure_score = _dissent_pressure_score(
        expected_dissent_ratio,
        report.dissent_severity_score,
    )
    expected_dissent_resistance_score = _normalize_unit_decimal(
        "dissent_resistance_score",
        ONE - expected_dissent_pressure_score,
    )
    expected_consensus_score = _consensus_score(
        agreement_ratio=expected_agreement_ratio,
        average_confidence_score=report.average_confidence_score,
        historical_calibration_score=report.historical_calibration_score,
        dissent_resistance_score=expected_dissent_resistance_score,
        agreement_weight=report.agreement_weight,
        confidence_weight=report.confidence_weight,
        calibration_weight=report.calibration_weight,
        dissent_resistance_weight=report.dissent_resistance_weight,
    )
    expected_hard_flag_codes = _hard_flag_codes_for_values(
        specialist_count=report.specialist_count,
        dissenting_team_count=report.dissenting_team_count,
        dissent_severity_score=report.dissent_severity_score,
        min_specialist_count_for_watch=report.min_specialist_count_for_watch,
        block_dissent_severity_score=report.block_dissent_severity_score,
    )
    expected_consensus_status = _consensus_status_for_values(
        specialist_count=report.specialist_count,
        agreement_ratio=expected_agreement_ratio,
        dissent_pressure_score=expected_dissent_pressure_score,
        historical_calibration_score=report.historical_calibration_score,
        consensus_score=expected_consensus_score,
        hard_flag_codes=expected_hard_flag_codes,
        min_specialist_count_for_pass=report.min_specialist_count_for_pass,
        min_agreement_ratio_for_pass=report.min_agreement_ratio_for_pass,
        max_dissent_pressure_for_pass=report.max_dissent_pressure_for_pass,
        min_historical_calibration_score_for_pass=(
            report.min_historical_calibration_score_for_pass
        ),
        block_consensus_score_floor=report.block_consensus_score_floor,
        pass_consensus_score_floor=report.pass_consensus_score_floor,
    )
    expected_reason_codes = _reason_codes_for_values(
        consensus_status=expected_consensus_status,
        specialist_count=report.specialist_count,
        agreement_ratio=expected_agreement_ratio,
        dissent_pressure_score=expected_dissent_pressure_score,
        historical_calibration_score=report.historical_calibration_score,
        consensus_score=expected_consensus_score,
        hard_flag_codes=expected_hard_flag_codes,
        min_specialist_count_for_watch=report.min_specialist_count_for_watch,
        min_specialist_count_for_pass=report.min_specialist_count_for_pass,
        min_agreement_ratio_for_pass=report.min_agreement_ratio_for_pass,
        max_dissent_pressure_for_pass=report.max_dissent_pressure_for_pass,
        min_historical_calibration_score_for_pass=(
            report.min_historical_calibration_score_for_pass
        ),
        block_consensus_score_floor=report.block_consensus_score_floor,
        pass_consensus_score_floor=report.pass_consensus_score_floor,
    )
    if report.agreement_ratio != expected_agreement_ratio:
        raise ValueError("agreement_ratio must match team counts")
    if report.dissent_ratio != expected_dissent_ratio:
        raise ValueError("dissent_ratio must match team counts")
    if report.dissent_pressure_score != expected_dissent_pressure_score:
        raise ValueError("dissent_pressure_score must match dissent inputs")
    if report.dissent_resistance_score != expected_dissent_resistance_score:
        raise ValueError("dissent_resistance_score must match dissent pressure")
    if report.consensus_score != expected_consensus_score:
        raise ValueError("consensus_score must match weighted components")
    if report.hard_flag_codes != expected_hard_flag_codes:
        raise ValueError("hard_flag_codes must match report fields")
    if report.hard_flag_codes and report.consensus_status != "block":
        raise ValueError("hard_flag_codes require block status")
    if report.consensus_status != expected_consensus_status:
        raise ValueError("consensus_status must match report fields")
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match report fields")


def _report_values_without_digest(
    report: CandidateDecisionCrossTeamConsensusScoreReport,
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
    expected_keys = {field.name for field in fields(CandidateDecisionCrossTeamConsensusScoreReport)}
    if set(payload) != expected_keys:
        raise ValueError("payload must contain exactly report fields")
    _require_hard_flags("payload", _PayloadFlags(payload))
    _require_consensus_status("consensus_status", payload["consensus_status"])
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
    status_reasons = tuple(code for code in codes if code.startswith("cross_team_consensus_"))
    if len(status_reasons) != 1:
        raise ValueError("reason_codes must contain one consensus status reason")
    return tuple(code for code in REASON_CODE_SEQUENCE if code in codes)


def _normalize_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized.quantize(COUNT_QUANT) != normalized:
        raise ValueError(f"{field_name} must be a whole number")
    return normalized.quantize(COUNT_QUANT, rounding=ROUND_HALF_EVEN)


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
        raise ValueError(f"{field_name} must be timezone-aware")
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


def _require_consensus_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in CONSENSUS_STATUSES:
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
            CandidateDecisionCrossTeamConsensusScoreConfig,
            CandidateDecisionCrossTeamConsensusScoreInput,
            CandidateDecisionCrossTeamConsensusScoreReport,
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
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is str or type(value) is bool:
        return value
    if type(value) is dict:
        return _json_dict(value)
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    if type(value) in (int, float):
        raise ValueError("JSON value must use Decimal-derived strings")
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
    paper_only: bool
    report_only: bool
    readonly: bool

    def __init__(self, payload: dict[str, Any]) -> None:
        object.__setattr__(self, "paper_only", payload.get("paper_only"))
        object.__setattr__(self, "report_only", payload.get("report_only"))
        object.__setattr__(self, "readonly", payload.get("readonly"))


_CONFIG_RATIO_FIELD_NAMES = (
    "min_agreement_ratio_for_pass",
    "max_dissent_pressure_for_pass",
    "block_dissent_severity_score",
    "block_consensus_score_floor",
    "pass_consensus_score_floor",
    "min_historical_calibration_score_for_pass",
    "agreement_weight",
    "confidence_weight",
    "calibration_weight",
    "dissent_resistance_weight",
)
_REPORT_RATIO_FIELD_NAMES = (
    "agreement_ratio",
    "dissent_ratio",
    "average_confidence_score",
    "dissent_severity_score",
    "historical_calibration_score",
    "dissent_pressure_score",
    "dissent_resistance_score",
    "consensus_score",
) + _CONFIG_RATIO_FIELD_NAMES

__all__ = (
    "DEFAULT_CANDIDATE_DECISION_CROSS_TEAM_CONSENSUS_SCORE_CONFIG_VERSION",
    "CONSENSUS_STATUSES",
    "CandidateDecisionCrossTeamConsensusScoreConfig",
    "CandidateDecisionCrossTeamConsensusScoreInput",
    "CandidateDecisionCrossTeamConsensusScoreReport",
    "build_candidate_decision_cross_team_consensus_score_report",
    "candidate_decision_cross_team_consensus_score_payload",
)
