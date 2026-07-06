"""Pure read-only team memory prior for strategy matrix use."""

from dataclasses import dataclass
from decimal import Decimal

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags
from polymarket_alpha_lab.team_taxonomy import require_team_id


DEFAULT_STRATEGY_TEAM_MEMORY_DECISION_PRIOR_CONFIG_VERSION = (
    "strategy-team-memory-decision-prior-v0"
)
STRATEGY_TEAM_MEMORY_DECISION_PRIOR_STATUSES = ("pass", "watch", "blocked")
STRATEGY_TEAM_MEMORY_DECISION_PRIOR_REASON_CODES = (
    "strategy_team_memory_prior_ready",
    "strategy_team_memory_prior_team_memory_score_low",
    "strategy_team_memory_prior_calibration_score_low",
    "strategy_team_memory_prior_sample_size_low",
    "strategy_team_memory_prior_recent_error_score_high",
    "strategy_team_memory_prior_domain_experience_score_low",
    "strategy_team_memory_prior_aggregate_score_low",
)
DECIMAL_ZERO = Decimal("0")
DECIMAL_ONE = Decimal("1.000000")
COUNT_QUANT = Decimal("1")
SCORE_QUANT = Decimal("0.000001")
PRIOR_COMPONENT_COUNT = Decimal("5")


@dataclass(frozen=True)
class StrategyTeamMemoryDecisionPriorConfig:
    config_version: str = DEFAULT_STRATEGY_TEAM_MEMORY_DECISION_PRIOR_CONFIG_VERSION
    pass_threshold: Decimal = Decimal("0.800000")
    watch_threshold: Decimal = Decimal("0.600000")
    component_watch_threshold: Decimal = Decimal("0.700000")
    target_sample_size: Decimal = Decimal("30")
    minimum_sample_size: Decimal = Decimal("10")
    max_recent_error_score: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "pass_threshold",
            "watch_threshold",
            "component_watch_threshold",
            "max_recent_error_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_score(field_name, getattr(self, field_name)),
            )
        for field_name in ("target_sample_size", "minimum_sample_size"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        if self.watch_threshold > self.pass_threshold:
            raise ValueError("watch_threshold must not exceed pass_threshold")
        if self.minimum_sample_size > self.target_sample_size:
            raise ValueError("minimum_sample_size must not exceed target_sample_size")
        if self.target_sample_size == DECIMAL_ZERO:
            raise ValueError("target_sample_size must be positive")
        require_paper_only_flags("StrategyTeamMemoryDecisionPriorConfig", self)


@dataclass(frozen=True)
class StrategyTeamMemoryDecisionPriorInput:
    team_id: str
    team_memory_score: Decimal
    calibration_score: Decimal
    sample_size: Decimal
    recent_error_score: Decimal
    domain_experience_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        for field_name in (
            "team_memory_score",
            "calibration_score",
            "recent_error_score",
            "domain_experience_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_score(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "sample_size",
            _normalize_nonnegative_integral_decimal("sample_size", self.sample_size),
        )
        require_paper_only_flags("StrategyTeamMemoryDecisionPriorInput", self)


@dataclass(frozen=True)
class StrategyTeamMemoryDecisionPrior:
    config_version: str
    team_id: str
    team_memory_score: Decimal
    calibration_score: Decimal
    sample_size: Decimal
    recent_error_score: Decimal
    domain_experience_score: Decimal
    sample_size_score: Decimal
    recent_error_component_score: Decimal
    prior_score: Decimal
    prior_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        for field_name in (
            "team_memory_score",
            "calibration_score",
            "recent_error_score",
            "domain_experience_score",
            "sample_size_score",
            "recent_error_component_score",
            "prior_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_score(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "sample_size",
            _normalize_nonnegative_integral_decimal("sample_size", self.sample_size),
        )
        _require_prior_status("prior_status", self.prior_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        require_paper_only_flags("StrategyTeamMemoryDecisionPrior", self)
        _validate_prior_consistency(self)


def build_strategy_team_memory_decision_prior(
    *,
    memory: StrategyTeamMemoryDecisionPriorInput,
    config: StrategyTeamMemoryDecisionPriorConfig,
) -> StrategyTeamMemoryDecisionPrior:
    if type(memory) is not StrategyTeamMemoryDecisionPriorInput:
        raise ValueError("memory must be a StrategyTeamMemoryDecisionPriorInput")
    if type(config) is not StrategyTeamMemoryDecisionPriorConfig:
        raise ValueError("config must be a StrategyTeamMemoryDecisionPriorConfig")
    require_paper_only_flags("StrategyTeamMemoryDecisionPriorInput", memory)
    require_paper_only_flags("StrategyTeamMemoryDecisionPriorConfig", config)

    sample_size_score = _sample_size_score(memory.sample_size, config.target_sample_size)
    recent_error_component_score = _recent_error_component_score(
        memory.recent_error_score,
    )
    prior_score = _prior_score(
        team_memory_score=memory.team_memory_score,
        calibration_score=memory.calibration_score,
        sample_size_score=sample_size_score,
        recent_error_component_score=recent_error_component_score,
        domain_experience_score=memory.domain_experience_score,
    )
    reason_codes = _reason_codes(
        memory=memory,
        sample_size_score=sample_size_score,
        prior_score=prior_score,
        config=config,
    )
    return StrategyTeamMemoryDecisionPrior(
        config_version=config.config_version,
        team_id=memory.team_id,
        team_memory_score=memory.team_memory_score,
        calibration_score=memory.calibration_score,
        sample_size=memory.sample_size,
        recent_error_score=memory.recent_error_score,
        domain_experience_score=memory.domain_experience_score,
        sample_size_score=sample_size_score,
        recent_error_component_score=recent_error_component_score,
        prior_score=prior_score,
        prior_status=_prior_status(
            memory=memory,
            prior_score=prior_score,
            config=config,
        ),
        reason_codes=reason_codes,
    )


def _sample_size_score(sample_size: Decimal, target_sample_size: Decimal) -> Decimal:
    if target_sample_size == DECIMAL_ZERO:
        raise ValueError("target_sample_size must be positive")
    return min(DECIMAL_ONE, sample_size / target_sample_size).quantize(SCORE_QUANT)


def _recent_error_component_score(recent_error_score: Decimal) -> Decimal:
    return max(DECIMAL_ZERO, DECIMAL_ONE - recent_error_score).quantize(SCORE_QUANT)


def _prior_score(
    *,
    team_memory_score: Decimal,
    calibration_score: Decimal,
    sample_size_score: Decimal,
    recent_error_component_score: Decimal,
    domain_experience_score: Decimal,
) -> Decimal:
    return (
        (
            team_memory_score
            + calibration_score
            + sample_size_score
            + recent_error_component_score
            + domain_experience_score
        )
        / PRIOR_COMPONENT_COUNT
    ).quantize(SCORE_QUANT)


def _prior_status(
    *,
    memory: StrategyTeamMemoryDecisionPriorInput,
    prior_score: Decimal,
    config: StrategyTeamMemoryDecisionPriorConfig,
) -> str:
    if (
        memory.sample_size < config.minimum_sample_size
        or memory.recent_error_score > config.max_recent_error_score
        or prior_score < config.watch_threshold
    ):
        return "blocked"
    if prior_score < config.pass_threshold:
        return "watch"
    return "pass"


def _reason_codes(
    *,
    memory: StrategyTeamMemoryDecisionPriorInput,
    sample_size_score: Decimal,
    prior_score: Decimal,
    config: StrategyTeamMemoryDecisionPriorConfig,
) -> tuple[str, ...]:
    reason_codes: tuple[str, ...] = ()
    if memory.team_memory_score < config.component_watch_threshold:
        reason_codes += ("strategy_team_memory_prior_team_memory_score_low",)
    if memory.calibration_score < config.component_watch_threshold:
        reason_codes += ("strategy_team_memory_prior_calibration_score_low",)
    if sample_size_score < DECIMAL_ONE:
        reason_codes += ("strategy_team_memory_prior_sample_size_low",)
    if memory.recent_error_score > config.max_recent_error_score:
        reason_codes += ("strategy_team_memory_prior_recent_error_score_high",)
    if memory.domain_experience_score < config.component_watch_threshold:
        reason_codes += ("strategy_team_memory_prior_domain_experience_score_low",)
    if prior_score < config.pass_threshold:
        reason_codes += ("strategy_team_memory_prior_aggregate_score_low",)
    if not reason_codes:
        return ("strategy_team_memory_prior_ready",)
    return reason_codes


def _validate_prior_consistency(prior: StrategyTeamMemoryDecisionPrior) -> None:
    expected_recent_error_component_score = _recent_error_component_score(
        prior.recent_error_score,
    )
    if prior.recent_error_component_score != expected_recent_error_component_score:
        raise ValueError("recent_error_component_score must match recent_error_score")
    expected_prior_score = _prior_score(
        team_memory_score=prior.team_memory_score,
        calibration_score=prior.calibration_score,
        sample_size_score=prior.sample_size_score,
        recent_error_component_score=prior.recent_error_component_score,
        domain_experience_score=prior.domain_experience_score,
    )
    if prior.prior_score != expected_prior_score:
        raise ValueError("prior_score must match component mean")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not value:
        raise ValueError("reason_codes must contain at least one value")
    for reason_code in value:
        _require_canonical_string("reason_codes", reason_code)
        if reason_code not in STRATEGY_TEAM_MEMORY_DECISION_PRIOR_REASON_CODES:
            raise ValueError("reason_codes must contain known reason codes")
    if len(set(value)) != len(value):
        raise ValueError("reason_codes must be unique")
    expected = tuple(
        reason_code
        for reason_code in STRATEGY_TEAM_MEMORY_DECISION_PRIOR_REASON_CODES
        if reason_code in value
    )
    if expected != value:
        raise ValueError("reason_codes must be deterministic")
    return value


def _require_prior_status(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or value not in STRATEGY_TEAM_MEMORY_DECISION_PRIOR_STATUSES
    ):
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _normalize_score(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(SCORE_QUANT)
    if quantized < DECIMAL_ZERO or quantized > DECIMAL_ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return quantized


def _normalize_integral_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(COUNT_QUANT)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    return quantized


def _normalize_nonnegative_integral_decimal(
    field_name: str,
    value: object,
) -> Decimal:
    quantized = _normalize_integral_decimal(field_name, value)
    if quantized < DECIMAL_ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


__all__ = (
    "DEFAULT_STRATEGY_TEAM_MEMORY_DECISION_PRIOR_CONFIG_VERSION",
    "STRATEGY_TEAM_MEMORY_DECISION_PRIOR_REASON_CODES",
    "STRATEGY_TEAM_MEMORY_DECISION_PRIOR_STATUSES",
    "StrategyTeamMemoryDecisionPrior",
    "StrategyTeamMemoryDecisionPriorConfig",
    "StrategyTeamMemoryDecisionPriorInput",
    "build_strategy_team_memory_decision_prior",
)
