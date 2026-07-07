"""Paper-only reducer for candidate decision team memory inputs."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)
from polymarket_alpha_lab.team_taxonomy import require_team_id


DEFAULT_CANDIDATE_DECISION_TEAM_MEMORY_ADAPTER_CONFIG_VERSION = (
    "candidate-decision-team-memory-adapter-v0"
)
MEMORY_USE_POLICIES = ("allow", "throttle", "block")
TEAM_MEMORY_POLICIES = MEMORY_USE_POLICIES

QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

REASON_CODE_ORDER = (
    "team_memory_adapter_allow",
    "team_memory_adapter_throttle",
    "team_memory_adapter_block",
    "team_memory_policy_allow",
    "team_memory_policy_throttle",
    "team_memory_policy_block",
    "settled_sample_count_sufficient",
    "settled_sample_count_sparse",
    "calibration_score_healthy",
    "calibration_score_watch",
    "calibration_score_blocking",
    "source_memory_score_healthy",
    "source_memory_score_watch",
    "capacity_score_healthy",
    "capacity_score_watch",
    "team_memory_score_below_allow_threshold",
)


@dataclass(frozen=True)
class CandidateDecisionTeamMemoryAdapterConfig:
    config_version: str = DEFAULT_CANDIDATE_DECISION_TEAM_MEMORY_ADAPTER_CONFIG_VERSION
    min_settled_sample_count: Decimal = Decimal("10")
    calibration_block_score: Decimal = Decimal("0.300000")
    calibration_throttle_score: Decimal = Decimal("0.600000")
    source_memory_throttle_score: Decimal = Decimal("0.500000")
    capacity_throttle_score: Decimal = Decimal("0.500000")
    min_team_memory_score_for_allow: Decimal = Decimal("0.650000")
    throttle_score_cap: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionTeamMemoryAdapterConfig:
            raise ValueError(
                "config must be exactly CandidateDecisionTeamMemoryAdapterConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_settled_sample_count",
            _normalize_nonnegative_count_decimal(
                "min_settled_sample_count",
                self.min_settled_sample_count,
            ),
        )
        for field_name in (
            "calibration_block_score",
            "calibration_throttle_score",
            "source_memory_throttle_score",
            "capacity_throttle_score",
            "min_team_memory_score_for_allow",
            "throttle_score_cap",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        require_paper_only_flags("CandidateDecisionTeamMemoryAdapterConfig", self)
        reject_unsafe_surface_fields("candidate decision team memory adapter config", self)


@dataclass(frozen=True)
class CandidateDecisionTeamMemoryAdapterInput:
    primary_team_id: str
    secondary_team_ids: tuple[str, ...]
    memory_use_policy: str
    calibration_score: Decimal
    settled_sample_count: Decimal
    source_memory_score: Decimal
    capacity_score: Decimal
    source_report_refs: tuple[str, ...]
    source_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionTeamMemoryAdapterInput:
            raise ValueError(
                "input_value must be exactly CandidateDecisionTeamMemoryAdapterInput",
            )
        object.__setattr__(
            self,
            "primary_team_id",
            require_team_id("primary_team_id", self.primary_team_id),
        )
        object.__setattr__(
            self,
            "secondary_team_ids",
            _normalize_secondary_team_ids(self.secondary_team_ids, self.primary_team_id),
        )
        _require_policy("memory_use_policy", self.memory_use_policy)
        for field_name in (
            "calibration_score",
            "source_memory_score",
            "capacity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "settled_sample_count",
            _normalize_nonnegative_count_decimal(
                "settled_sample_count",
                self.settled_sample_count,
            ),
        )
        object.__setattr__(
            self,
            "source_report_refs",
            _normalize_string_tuple("source_report_refs", self.source_report_refs),
        )
        object.__setattr__(
            self,
            "source_reason_codes",
            _normalize_string_tuple("source_reason_codes", self.source_reason_codes),
        )
        require_paper_only_flags("CandidateDecisionTeamMemoryAdapterInput", self)
        reject_unsafe_surface_fields("candidate decision team memory adapter input", self)


@dataclass(frozen=True)
class CandidateDecisionTeamMemoryAdapterResult:
    primary_team_id: str
    secondary_team_ids: tuple[str, ...]
    memory_use_policy: str
    calibration_score: Decimal
    settled_sample_count: Decimal
    source_memory_score: Decimal
    capacity_score: Decimal
    team_memory_score: Decimal
    team_memory_policy: str
    source_report_refs: tuple[str, ...]
    source_reason_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CandidateDecisionTeamMemoryAdapterResult:
            raise ValueError(
                "result must be exactly CandidateDecisionTeamMemoryAdapterResult",
            )
        object.__setattr__(
            self,
            "primary_team_id",
            require_team_id("primary_team_id", self.primary_team_id),
        )
        object.__setattr__(
            self,
            "secondary_team_ids",
            _normalize_secondary_team_ids(self.secondary_team_ids, self.primary_team_id),
        )
        _require_policy("memory_use_policy", self.memory_use_policy)
        for field_name in (
            "calibration_score",
            "source_memory_score",
            "capacity_score",
            "team_memory_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "settled_sample_count",
            _normalize_nonnegative_count_decimal(
                "settled_sample_count",
                self.settled_sample_count,
            ),
        )
        _require_policy("team_memory_policy", self.team_memory_policy)
        object.__setattr__(
            self,
            "source_report_refs",
            _normalize_string_tuple("source_report_refs", self.source_report_refs),
        )
        object.__setattr__(
            self,
            "source_reason_codes",
            _normalize_string_tuple("source_reason_codes", self.source_reason_codes),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        require_paper_only_flags("CandidateDecisionTeamMemoryAdapterResult", self)
        reject_unsafe_surface_fields("candidate decision team memory adapter result", self)
        _validate_result(self)


def build_candidate_decision_team_memory_adapter(
    input_value: CandidateDecisionTeamMemoryAdapterInput,
    *,
    config: CandidateDecisionTeamMemoryAdapterConfig | None = None,
) -> CandidateDecisionTeamMemoryAdapterResult:
    if type(input_value) is not CandidateDecisionTeamMemoryAdapterInput:
        raise ValueError(
            "input_value must be a CandidateDecisionTeamMemoryAdapterInput",
        )
    if config is None:
        config = CandidateDecisionTeamMemoryAdapterConfig()
    if type(config) is not CandidateDecisionTeamMemoryAdapterConfig:
        raise ValueError(
            "config must be a CandidateDecisionTeamMemoryAdapterConfig",
        )
    require_paper_only_flags("CandidateDecisionTeamMemoryAdapterInput", input_value)
    require_paper_only_flags("CandidateDecisionTeamMemoryAdapterConfig", config)

    raw_score = _raw_team_memory_score(input_value)
    policy = _team_memory_policy(input_value, raw_score, config)
    score = _team_memory_score(raw_score, policy, config)
    reason_codes = _reason_codes(input_value, raw_score, policy, config)
    return CandidateDecisionTeamMemoryAdapterResult(
        primary_team_id=input_value.primary_team_id,
        secondary_team_ids=input_value.secondary_team_ids,
        memory_use_policy=input_value.memory_use_policy,
        calibration_score=input_value.calibration_score,
        settled_sample_count=input_value.settled_sample_count,
        source_memory_score=input_value.source_memory_score,
        capacity_score=input_value.capacity_score,
        team_memory_score=score,
        team_memory_policy=policy,
        source_report_refs=input_value.source_report_refs,
        source_reason_codes=input_value.source_reason_codes,
        reason_codes=reason_codes,
    )


def candidate_decision_team_memory_adapter_payload(
    result: CandidateDecisionTeamMemoryAdapterResult | dict[str, Any],
) -> dict[str, Any]:
    if type(result) is CandidateDecisionTeamMemoryAdapterResult:
        require_paper_only_flags("CandidateDecisionTeamMemoryAdapterResult", result)
        reject_unsafe_surface_fields("candidate decision team memory adapter result", result)
        payload = json_ready_no_floats(result)
    elif type(result) is dict:
        reject_unsafe_surface_fields("candidate decision team memory adapter payload", result)
        payload = json_ready_no_floats(result)
    else:
        raise ValueError(
            "result must be a CandidateDecisionTeamMemoryAdapterResult or payload",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _require_payload_flags(payload)
    reject_unsafe_surface_fields("candidate decision team memory adapter payload", payload)
    return payload


def _raw_team_memory_score(
    input_value: CandidateDecisionTeamMemoryAdapterInput | CandidateDecisionTeamMemoryAdapterResult,
) -> Decimal:
    return _normalize_unit_decimal(
        "team_memory_score",
        (
            input_value.calibration_score
            + input_value.source_memory_score
            + input_value.capacity_score
        )
        / Decimal("3"),
    )


def _team_memory_policy(
    input_value: CandidateDecisionTeamMemoryAdapterInput,
    raw_score: Decimal,
    config: CandidateDecisionTeamMemoryAdapterConfig,
) -> str:
    if (
        input_value.memory_use_policy == "block"
        or input_value.calibration_score <= config.calibration_block_score
    ):
        return "block"
    if (
        input_value.memory_use_policy == "throttle"
        or input_value.settled_sample_count < config.min_settled_sample_count
        or input_value.calibration_score < config.calibration_throttle_score
        or input_value.source_memory_score < config.source_memory_throttle_score
        or input_value.capacity_score < config.capacity_throttle_score
        or raw_score < config.min_team_memory_score_for_allow
    ):
        return "throttle"
    return "allow"


def _team_memory_score(
    raw_score: Decimal,
    policy: str,
    config: CandidateDecisionTeamMemoryAdapterConfig,
) -> Decimal:
    if policy == "block":
        return ZERO
    if policy == "throttle":
        return min(raw_score, config.throttle_score_cap).quantize(QUANT)
    return raw_score


def _reason_codes(
    input_value: CandidateDecisionTeamMemoryAdapterInput,
    raw_score: Decimal,
    policy: str,
    config: CandidateDecisionTeamMemoryAdapterConfig,
) -> tuple[str, ...]:
    codes = [
        f"team_memory_adapter_{policy}",
        f"team_memory_policy_{input_value.memory_use_policy}",
    ]
    if input_value.settled_sample_count < config.min_settled_sample_count:
        codes.append("settled_sample_count_sparse")
    else:
        codes.append("settled_sample_count_sufficient")
    if input_value.calibration_score <= config.calibration_block_score:
        codes.append("calibration_score_blocking")
    elif input_value.calibration_score < config.calibration_throttle_score:
        codes.append("calibration_score_watch")
    else:
        codes.append("calibration_score_healthy")
    if input_value.source_memory_score < config.source_memory_throttle_score:
        codes.append("source_memory_score_watch")
    else:
        codes.append("source_memory_score_healthy")
    if input_value.capacity_score < config.capacity_throttle_score:
        codes.append("capacity_score_watch")
    else:
        codes.append("capacity_score_healthy")
    if raw_score < config.min_team_memory_score_for_allow:
        codes.append("team_memory_score_below_allow_threshold")
    return _normalize_reason_codes(tuple(codes))


def _validate_config(config: CandidateDecisionTeamMemoryAdapterConfig) -> None:
    if config.calibration_block_score > config.calibration_throttle_score:
        raise ValueError("calibration_block_score must not exceed calibration_throttle_score")
    if config.throttle_score_cap > config.min_team_memory_score_for_allow:
        raise ValueError("throttle_score_cap must not exceed min_team_memory_score_for_allow")


def _validate_result(result: CandidateDecisionTeamMemoryAdapterResult) -> None:
    if result.team_memory_policy == "block" and result.team_memory_score != ZERO:
        raise ValueError("blocked team memory must have zero score")
    if result.team_memory_policy == "throttle" and (
        result.team_memory_score > Decimal("0.600000")
    ):
        raise ValueError("throttled team memory score must be capped")
    if result.reason_codes[0] != f"team_memory_adapter_{result.team_memory_policy}":
        raise ValueError("reason_codes must start with adapter policy")


def _normalize_secondary_team_ids(
    value: object,
    primary_team_id: str,
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("secondary_team_ids must be a list or tuple")
    team_ids = tuple(require_team_id("secondary_team_ids", item) for item in value)
    if primary_team_id in team_ids:
        raise ValueError("secondary_team_ids must not include primary_team_id")
    if len(set(team_ids)) != len(team_ids):
        raise ValueError("secondary_team_ids must be unique")
    return team_ids


def _normalize_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    items = tuple(value)
    for item in items:
        _require_canonical_string(field_name, item)
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} must be unique")
    return tuple(sorted(items))


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    codes = tuple(value)
    if not codes:
        raise ValueError("reason_codes must not be empty")
    for code in codes:
        _require_reason_code("reason_codes", code)
    if len(set(codes)) != len(codes):
        raise ValueError("reason_codes must be unique")
    return tuple(code for code in REASON_CODE_ORDER if code in codes)


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be no greater than 1")
    return normalized


def _normalize_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized.quantize(COUNT_QUANT) != normalized:
        raise ValueError(f"{field_name} must be a whole number")
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
    return value.quantize(QUANT)


def _require_policy(field_name: str, value: object) -> None:
    if type(value) is not str or value not in MEMORY_USE_POLICIES:
        raise ValueError(f"{field_name} must be allow, throttle, or block")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODE_ORDER:
        raise ValueError(f"{field_name} must contain supported adapter reasons")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for payload")


__all__ = (
    "DEFAULT_CANDIDATE_DECISION_TEAM_MEMORY_ADAPTER_CONFIG_VERSION",
    "MEMORY_USE_POLICIES",
    "TEAM_MEMORY_POLICIES",
    "CandidateDecisionTeamMemoryAdapterConfig",
    "CandidateDecisionTeamMemoryAdapterInput",
    "CandidateDecisionTeamMemoryAdapterResult",
    "build_candidate_decision_team_memory_adapter",
    "candidate_decision_team_memory_adapter_payload",
)
