from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal, localcontext
from hashlib import sha256
import json


DEFAULT_TEAM_SPECIALIST_DOMAIN_ROTATION_SCORE_CONFIG_VERSION = (
    "team_specialist_domain_rotation_score.v1"
)
DIGEST_VERSION = "team_specialist_domain_rotation_score.digest.v1"
SIX_PLACES = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT_PRECISION = 28

_STATUS_VALUES = frozenset(("pass", "watch", "block"))
_UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "market_id",
        "candidate_id",
        "market_slug",
        "question",
        "source_ref",
        "url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "secret",
        "auth",
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "recommendation",
        "position",
    ),
)
_REASON_CODES = frozenset(
    (
        "domain_rotation_pass",
        "domain_rotation_watch",
        "domain_rotation_block",
        "primary_domain_concentration_clear",
        "primary_domain_concentration_watch",
        "primary_domain_concentration_high",
        "rotation_gap_clear",
        "rotation_gap_watch",
        "rotation_gap_high",
        "undercovered_domain_clear",
        "undercovered_domain_watch",
        "undercovered_domain_high",
        "rotation_completion_met",
        "rotation_completion_partial",
        "rotation_completion_low",
        "category_coverage_strong",
        "category_coverage_watch",
        "category_coverage_weak",
        "domain_depth_sufficient",
        "domain_depth_low",
        "case_depth_sufficient",
        "case_depth_low",
        "hard_flag_clear",
        "hard_flag_present",
    ),
)

__all__ = (
    "DEFAULT_TEAM_SPECIALIST_DOMAIN_ROTATION_SCORE_CONFIG_VERSION",
    "TeamSpecialistDomainRotationScoreConfig",
    "TeamSpecialistDomainRotationScoreInput",
    "TeamSpecialistDomainRotationScoreReport",
    "score_team_specialist_domain_rotation",
    "team_specialist_domain_rotation_score_payload",
)


@dataclass(frozen=True)
class TeamSpecialistDomainRotationScoreConfig:
    config_version: str = DEFAULT_TEAM_SPECIALIST_DOMAIN_ROTATION_SCORE_CONFIG_VERSION
    concentration_weight: Decimal = Decimal("0.300000")
    rotation_gap_weight: Decimal = Decimal("0.150000")
    undercovered_domain_weight: Decimal = Decimal("0.150000")
    rotation_deficit_weight: Decimal = Decimal("0.200000")
    category_coverage_gap_weight: Decimal = Decimal("0.200000")
    score_watch_floor: Decimal = Decimal("0.350000")
    score_block_floor: Decimal = Decimal("0.750000")
    concentration_watch_floor: Decimal = Decimal("0.500000")
    concentration_block_floor: Decimal = Decimal("0.800000")
    rotation_gap_watch_floor: Decimal = Decimal("0.250000")
    rotation_gap_block_floor: Decimal = Decimal("0.750000")
    undercovered_watch_floor: Decimal = Decimal("0.250000")
    undercovered_block_floor: Decimal = Decimal("0.750000")
    rotation_completion_watch_floor: Decimal = Decimal("0.750000")
    rotation_completion_block_floor: Decimal = Decimal("0.250000")
    category_coverage_watch_floor: Decimal = Decimal("0.800000")
    category_coverage_block_floor: Decimal = Decimal("0.500000")
    minimum_covered_domain_count: Decimal = Decimal("3")
    minimum_total_case_count: Decimal = Decimal("10")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistDomainRotationScoreConfig:
            raise TypeError(
                "TeamSpecialistDomainRotationScoreConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistDomainRotationScoreConfig:
            raise ValueError(
                "config must be exactly TeamSpecialistDomainRotationScoreConfig",
            )
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if self.config_version != DEFAULT_TEAM_SPECIALIST_DOMAIN_ROTATION_SCORE_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "concentration_weight",
            "rotation_gap_weight",
            "undercovered_domain_weight",
            "rotation_deficit_weight",
            "category_coverage_gap_weight",
            "score_watch_floor",
            "score_block_floor",
            "concentration_watch_floor",
            "concentration_block_floor",
            "rotation_gap_watch_floor",
            "rotation_gap_block_floor",
            "undercovered_watch_floor",
            "undercovered_block_floor",
            "rotation_completion_watch_floor",
            "rotation_completion_block_floor",
            "category_coverage_watch_floor",
            "category_coverage_block_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "minimum_covered_domain_count",
            "minimum_total_case_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_integral_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class TeamSpecialistDomainRotationScoreInput:
    team_id: str
    specialist_id: str
    primary_domain_id: str
    covered_domain_count: Decimal
    primary_domain_case_count: Decimal
    total_case_count: Decimal
    rotation_gap_count: Decimal
    undercovered_domain_count: Decimal
    recent_rotation_count: Decimal
    target_rotation_count: Decimal
    category_coverage_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistDomainRotationScoreInput:
            raise TypeError(
                "TeamSpecialistDomainRotationScoreInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistDomainRotationScoreInput:
            raise ValueError("input must be exactly TeamSpecialistDomainRotationScoreInput")
        for field_name in ("team_id", "specialist_id", "primary_domain_id"):
            object.__setattr__(
                self,
                field_name,
                _require_public_identifier(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "covered_domain_count",
            "primary_domain_case_count",
            "total_case_count",
            "rotation_gap_count",
            "undercovered_domain_count",
            "recent_rotation_count",
            "target_rotation_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_integral_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "category_coverage_score",
            _require_ratio_decimal("category_coverage_score", self.category_coverage_score),
        )
        _validate_input(self)
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class TeamSpecialistDomainRotationScoreReport:
    config_version: str
    team_id: str
    specialist_id: str
    primary_domain_id: str
    covered_domain_count: Decimal
    primary_domain_case_count: Decimal
    total_case_count: Decimal
    rotation_gap_count: Decimal
    undercovered_domain_count: Decimal
    recent_rotation_count: Decimal
    target_rotation_count: Decimal
    category_coverage_score: Decimal
    primary_domain_concentration_score: Decimal
    rotation_gap_score: Decimal
    undercovered_domain_score: Decimal
    rotation_completion_score: Decimal
    domain_rotation_risk_score: Decimal
    domain_rotation_status: str
    report_status: str
    hard_flag: bool
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistDomainRotationScoreReport:
            raise TypeError(
                "TeamSpecialistDomainRotationScoreReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistDomainRotationScoreReport:
            raise ValueError("report must be exactly TeamSpecialistDomainRotationScoreReport")
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if self.config_version != DEFAULT_TEAM_SPECIALIST_DOMAIN_ROTATION_SCORE_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in ("team_id", "specialist_id", "primary_domain_id"):
            object.__setattr__(
                self,
                field_name,
                _require_public_identifier(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "covered_domain_count",
            "primary_domain_case_count",
            "total_case_count",
            "rotation_gap_count",
            "undercovered_domain_count",
            "recent_rotation_count",
            "target_rotation_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_integral_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "category_coverage_score",
            "primary_domain_concentration_score",
            "rotation_gap_score",
            "undercovered_domain_score",
            "rotation_completion_score",
            "domain_rotation_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("domain_rotation_status", self.domain_rotation_status)
        _require_status("report_status", self.report_status)
        if type(self.hard_flag) is not bool:
            raise ValueError("hard_flag must be exactly bool")
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload(
            "TeamSpecialistDomainRotationScoreReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def score_team_specialist_domain_rotation(
    signal: TeamSpecialistDomainRotationScoreInput,
    *,
    config: TeamSpecialistDomainRotationScoreConfig | None = None,
) -> TeamSpecialistDomainRotationScoreReport:
    if config is None:
        config = TeamSpecialistDomainRotationScoreConfig()
    if type(config) is not TeamSpecialistDomainRotationScoreConfig:
        raise ValueError("config must be a TeamSpecialistDomainRotationScoreConfig")
    if type(signal) is not TeamSpecialistDomainRotationScoreInput:
        raise ValueError("signal must be a TeamSpecialistDomainRotationScoreInput")
    _require_hard_flags("config", config)
    _require_hard_flags("signal", signal)

    concentration_score = _primary_domain_concentration_score(signal)
    rotation_gap_score = _rotation_gap_score(signal)
    undercovered_score = _undercovered_domain_score(signal)
    completion_score = _rotation_completion_score(signal)
    risk_score = _domain_rotation_risk_score(
        concentration_score,
        rotation_gap_score,
        undercovered_score,
        completion_score,
        signal.category_coverage_score,
        config,
    )
    rotation_status = _score_status(risk_score, config)
    hard_flag = _hard_flag(signal, config)
    report_status = "block" if hard_flag else rotation_status
    values: dict[str, object] = {
        "config_version": config.config_version,
        "team_id": signal.team_id,
        "specialist_id": signal.specialist_id,
        "primary_domain_id": signal.primary_domain_id,
        "covered_domain_count": signal.covered_domain_count,
        "primary_domain_case_count": signal.primary_domain_case_count,
        "total_case_count": signal.total_case_count,
        "rotation_gap_count": signal.rotation_gap_count,
        "undercovered_domain_count": signal.undercovered_domain_count,
        "recent_rotation_count": signal.recent_rotation_count,
        "target_rotation_count": signal.target_rotation_count,
        "category_coverage_score": signal.category_coverage_score,
        "primary_domain_concentration_score": concentration_score,
        "rotation_gap_score": rotation_gap_score,
        "undercovered_domain_score": undercovered_score,
        "rotation_completion_score": completion_score,
        "domain_rotation_risk_score": risk_score,
        "domain_rotation_status": rotation_status,
        "report_status": report_status,
        "hard_flag": hard_flag,
        "reason_codes": _reason_codes(
            signal,
            concentration_score,
            rotation_gap_score,
            undercovered_score,
            completion_score,
            rotation_status,
            hard_flag,
            config,
        ),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return TeamSpecialistDomainRotationScoreReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def team_specialist_domain_rotation_score_payload(
    payload: object,
) -> dict[str, object]:
    if type(payload) is TeamSpecialistDomainRotationScoreReport:
        return payload.payload
    _reject_unsafe_public_payload(
        "team_specialist_domain_rotation_score_payload",
        payload,
        allow_json_containers=True,
    )
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def _primary_domain_concentration_score(
    signal: TeamSpecialistDomainRotationScoreInput,
) -> Decimal:
    return _ratio(signal.primary_domain_case_count, signal.total_case_count)


def _rotation_gap_score(signal: TeamSpecialistDomainRotationScoreInput) -> Decimal:
    return _ratio(signal.rotation_gap_count, signal.covered_domain_count)


def _undercovered_domain_score(signal: TeamSpecialistDomainRotationScoreInput) -> Decimal:
    return _ratio(signal.undercovered_domain_count, signal.covered_domain_count)


def _rotation_completion_score(signal: TeamSpecialistDomainRotationScoreInput) -> Decimal:
    return _ratio(signal.recent_rotation_count, signal.target_rotation_count)


def _domain_rotation_risk_score(
    concentration_score: Decimal,
    rotation_gap_score: Decimal,
    undercovered_score: Decimal,
    completion_score: Decimal,
    category_coverage_score: Decimal,
    config: TeamSpecialistDomainRotationScoreConfig,
) -> Decimal:
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        score = (
            concentration_score * config.concentration_weight
            + rotation_gap_score * config.rotation_gap_weight
            + undercovered_score * config.undercovered_domain_weight
            + (ONE - completion_score) * config.rotation_deficit_weight
            + (ONE - category_coverage_score) * config.category_coverage_gap_weight
        )
    return _quantize(score)


def _score_status(
    score: Decimal,
    config: TeamSpecialistDomainRotationScoreConfig,
) -> str:
    if score >= config.score_block_floor:
        return "block"
    if score >= config.score_watch_floor:
        return "watch"
    return "pass"


def _hard_flag(
    signal: TeamSpecialistDomainRotationScoreInput,
    config: TeamSpecialistDomainRotationScoreConfig,
) -> bool:
    return (
        signal.covered_domain_count < config.minimum_covered_domain_count
        or signal.total_case_count < config.minimum_total_case_count
    )


def _reason_codes(
    signal: TeamSpecialistDomainRotationScoreInput,
    concentration_score: Decimal,
    rotation_gap_score: Decimal,
    undercovered_score: Decimal,
    completion_score: Decimal,
    rotation_status: str,
    hard_flag: bool,
    config: TeamSpecialistDomainRotationScoreConfig,
) -> tuple[str, ...]:
    return (
        f"domain_rotation_{rotation_status}",
        _tier_high_reason(
            concentration_score,
            watch_floor=config.concentration_watch_floor,
            block_floor=config.concentration_block_floor,
            clear_reason="primary_domain_concentration_clear",
            watch_reason="primary_domain_concentration_watch",
            block_reason="primary_domain_concentration_high",
        ),
        _tier_high_reason(
            rotation_gap_score,
            watch_floor=config.rotation_gap_watch_floor,
            block_floor=config.rotation_gap_block_floor,
            clear_reason="rotation_gap_clear",
            watch_reason="rotation_gap_watch",
            block_reason="rotation_gap_high",
        ),
        _tier_high_reason(
            undercovered_score,
            watch_floor=config.undercovered_watch_floor,
            block_floor=config.undercovered_block_floor,
            clear_reason="undercovered_domain_clear",
            watch_reason="undercovered_domain_watch",
            block_reason="undercovered_domain_high",
        ),
        _completion_reason(completion_score, config),
        _category_coverage_reason(signal.category_coverage_score, config),
        (
            "domain_depth_low"
            if signal.covered_domain_count < config.minimum_covered_domain_count
            else "domain_depth_sufficient"
        ),
        (
            "case_depth_low"
            if signal.total_case_count < config.minimum_total_case_count
            else "case_depth_sufficient"
        ),
        "hard_flag_present" if hard_flag else "hard_flag_clear",
    )


def _tier_high_reason(
    value: Decimal,
    *,
    watch_floor: Decimal,
    block_floor: Decimal,
    clear_reason: str,
    watch_reason: str,
    block_reason: str,
) -> str:
    if value >= block_floor:
        return block_reason
    if value >= watch_floor:
        return watch_reason
    return clear_reason


def _completion_reason(
    value: Decimal,
    config: TeamSpecialistDomainRotationScoreConfig,
) -> str:
    if value <= config.rotation_completion_block_floor:
        return "rotation_completion_low"
    if value < config.rotation_completion_watch_floor:
        return "rotation_completion_partial"
    return "rotation_completion_met"


def _category_coverage_reason(
    value: Decimal,
    config: TeamSpecialistDomainRotationScoreConfig,
) -> str:
    if value < config.category_coverage_block_floor:
        return "category_coverage_weak"
    if value < config.category_coverage_watch_floor:
        return "category_coverage_watch"
    return "category_coverage_strong"


def _validate_config(config: TeamSpecialistDomainRotationScoreConfig) -> None:
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        weight_sum = _quantize(
            config.concentration_weight
            + config.rotation_gap_weight
            + config.undercovered_domain_weight
            + config.rotation_deficit_weight
            + config.category_coverage_gap_weight,
        )
    if weight_sum != ONE:
        raise ValueError("score weights must sum to 1.000000")
    _validate_threshold_pair("score", config.score_watch_floor, config.score_block_floor)
    _validate_threshold_pair(
        "concentration",
        config.concentration_watch_floor,
        config.concentration_block_floor,
    )
    _validate_threshold_pair(
        "rotation gap",
        config.rotation_gap_watch_floor,
        config.rotation_gap_block_floor,
    )
    _validate_threshold_pair(
        "undercovered",
        config.undercovered_watch_floor,
        config.undercovered_block_floor,
    )
    if config.rotation_completion_block_floor > config.rotation_completion_watch_floor:
        raise ValueError(
            "rotation completion block threshold must not exceed watch threshold",
        )
    if config.category_coverage_block_floor > config.category_coverage_watch_floor:
        raise ValueError("category coverage block threshold must not exceed watch threshold")


def _validate_threshold_pair(
    label: str,
    watch_floor: Decimal,
    block_floor: Decimal,
) -> None:
    if watch_floor > block_floor:
        raise ValueError(f"{label} watch threshold must not exceed block threshold")


def _validate_input(signal: TeamSpecialistDomainRotationScoreInput) -> None:
    if signal.covered_domain_count <= ZERO:
        raise ValueError("covered_domain_count must be positive")
    if signal.total_case_count <= ZERO:
        raise ValueError("total_case_count must be positive")
    if signal.target_rotation_count <= ZERO:
        raise ValueError("target_rotation_count must be positive")
    if signal.primary_domain_case_count > signal.total_case_count:
        raise ValueError("primary_domain_case_count must not exceed total_case_count")


def _validate_report_consistency(report: TeamSpecialistDomainRotationScoreReport) -> None:
    config = TeamSpecialistDomainRotationScoreConfig(config_version=report.config_version)
    signal = TeamSpecialistDomainRotationScoreInput(
        team_id=report.team_id,
        specialist_id=report.specialist_id,
        primary_domain_id=report.primary_domain_id,
        covered_domain_count=report.covered_domain_count,
        primary_domain_case_count=report.primary_domain_case_count,
        total_case_count=report.total_case_count,
        rotation_gap_count=report.rotation_gap_count,
        undercovered_domain_count=report.undercovered_domain_count,
        recent_rotation_count=report.recent_rotation_count,
        target_rotation_count=report.target_rotation_count,
        category_coverage_score=report.category_coverage_score,
    )
    expected_concentration = _primary_domain_concentration_score(signal)
    if report.primary_domain_concentration_score != expected_concentration:
        raise ValueError("primary_domain_concentration_score does not match inputs")
    expected_gap = _rotation_gap_score(signal)
    if report.rotation_gap_score != expected_gap:
        raise ValueError("rotation_gap_score does not match inputs")
    expected_undercovered = _undercovered_domain_score(signal)
    if report.undercovered_domain_score != expected_undercovered:
        raise ValueError("undercovered_domain_score does not match inputs")
    expected_completion = _rotation_completion_score(signal)
    if report.rotation_completion_score != expected_completion:
        raise ValueError("rotation_completion_score does not match inputs")
    expected_risk = _domain_rotation_risk_score(
        expected_concentration,
        expected_gap,
        expected_undercovered,
        expected_completion,
        report.category_coverage_score,
        config,
    )
    if report.domain_rotation_risk_score != expected_risk:
        raise ValueError("domain_rotation_risk_score does not match inputs")
    expected_rotation_status = _score_status(report.domain_rotation_risk_score, config)
    if report.domain_rotation_status != expected_rotation_status:
        raise ValueError("domain_rotation_status does not match risk score")
    expected_hard_flag = _hard_flag(signal, config)
    if report.hard_flag is not expected_hard_flag:
        raise ValueError("hard_flag does not match domain rotation thresholds")
    expected_report_status = "block" if expected_hard_flag else expected_rotation_status
    if report.report_status != expected_report_status:
        raise ValueError("report_status must match hard flag and domain rotation status")
    expected_reasons = _reason_codes(
        signal,
        expected_concentration,
        expected_gap,
        expected_undercovered,
        expected_completion,
        expected_rotation_status,
        expected_hard_flag,
        config,
    )
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes do not match report inputs")


def _report_values_without_digest(
    report: TeamSpecialistDomainRotationScoreReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest")
    return values


def _report_digest_from_values(values: dict[str, object]) -> str:
    digest_payload = {
        "digest_version": DIGEST_VERSION,
        "values": _digest_ready(values),
    }
    canonical_payload = json.dumps(
        digest_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical_payload.encode("utf-8")).hexdigest()


def _digest_ready(value: object) -> object:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("digest decimal must be exactly Decimal")
        return _decimal_string(value)
    if is_dataclass(value) and not isinstance(value, type):
        return _digest_ready(asdict(value))
    if type(value) is dict:
        return {str(key): _digest_ready(item) for key, item in value.items()}
    if type(value) in (list, tuple):
        return [_digest_ready(item) for item in value]
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("digest payload is not JSON-ready")


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("payload decimal must be exactly Decimal")
        return _decimal_string(value)
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return {str(key): _json_ready(item) for key, item in value.items()}
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("payload is not JSON-ready")


def _decimal_string(value: Decimal) -> str:
    return format(_quantize(value), "f")


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("ratio denominator must be positive")
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        value = numerator / denominator
    return _clamp_ratio(value)


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be exactly str")
    if not value:
        raise ValueError(f"{field_name} must be non-empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} has unsafe public value")
    if "://" in value or "?" in value:
        raise ValueError(f"{field_name} has unsafe public value")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} has unsafe public value")
    return value


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _STATUS_VALUES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError("reason_codes must be a non-empty tuple")
    for item in value:
        if type(item) is not str:
            raise ValueError("reason_codes must contain str values")
        if item not in _REASON_CODES:
            raise ValueError("reason_codes must contain known values")
        if _has_unsafe_public_fragment(item):
            raise ValueError("reason_codes has unsafe public value")
    if len(set(value)) != len(value):
        raise ValueError("reason_codes must not contain duplicates")
    return value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    return _quantize_input_decimal(field_name, value)


def _require_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return _quantize(value)


def _require_positive_integral_decimal(field_name: str, value: object) -> Decimal:
    value = _require_nonnegative_integral_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _quantize_input_decimal(field_name: str, value: Decimal) -> Decimal:
    quantized = _quantize(value)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _quantize(value: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        return value.quantize(SIX_PLACES)


def _clamp_ratio(value: Decimal) -> Decimal:
    return min(ONE, max(ZERO, _quantize(value)))


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be exactly str")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {field_name}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {field_name}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {field_name}")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), allow_json_containers=True)
        return
    if type(value) is dict:
        if not allow_json_containers:
            raise ValueError(f"{label} has unsafe public value")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} has unsafe public key")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"{label} has unsafe public key")
            _reject_unsafe_public_payload(label, item, allow_json_containers=True)
        return
    if type(value) in (list, tuple):
        if not allow_json_containers:
            raise ValueError(f"{label} has unsafe public value")
        for item in value:
            _reject_unsafe_public_payload(label, item, allow_json_containers=True)
        return
    if type(value) is float or type(value) is int:
        raise ValueError(f"{label} has unsafe public value")
    if type(value) is str and _has_unsafe_public_fragment(value):
        raise ValueError(f"{label} has unsafe public value")


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in _UNSAFE_PUBLIC_FRAGMENTS)
