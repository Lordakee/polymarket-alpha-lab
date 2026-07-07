from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from decimal import Decimal, localcontext
from hashlib import sha256
import json


DEFAULT_TEAM_SPECIALIST_MEMORY_CONFLICT_SCORE_CONFIG_VERSION = (
    "team_specialist_memory_conflict_score.v1"
)
DIGEST_VERSION = "team_specialist_memory_conflict_score.digest.v1"
SIX_PLACES = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT_PRECISION = 28

_STATUS_VALUES = frozenset(("pass", "watch", "block"))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "raw_candidate_id",
        "candidate_id",
        "candidate",
        "market_id",
        "market_slug",
        "market",
        "question",
        "source_ref",
        "source_text",
        "source",
        "http://",
        "https://",
        "url",
        "dsn",
        "table_name",
        "table",
        "token",
        "secret",
        "auth",
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "recommendation",
        "position_sizing",
        "position",
    ),
)
_REASON_CODES = frozenset(
    (
        "memory_conflict_pass",
        "memory_conflict_watch",
        "memory_conflict_block",
        "conflict_ratio_clear",
        "conflict_ratio_watch",
        "conflict_ratio_high",
        "conclusion_diversity_clear",
        "conclusion_diversity_watch",
        "conclusion_diversity_high",
        "contradiction_severity_clear",
        "contradiction_severity_watch",
        "contradiction_severity_high",
        "unresolved_conflict_clear",
        "unresolved_conflict_watch",
        "unresolved_conflict_high",
        "resolution_recency_clear",
        "resolution_recency_watch",
        "resolution_recency_stale",
        "memory_depth_sufficient",
        "memory_depth_low",
        "hard_flag_clear",
        "hard_flag_present",
    ),
)


@dataclass(frozen=True)
class TeamSpecialistMemoryConflictScoreConfig:
    config_version: str = DEFAULT_TEAM_SPECIALIST_MEMORY_CONFLICT_SCORE_CONFIG_VERSION
    conflict_ratio_weight: Decimal = Decimal("0.350000")
    conclusion_diversity_weight: Decimal = Decimal("0.200000")
    contradiction_severity_weight: Decimal = Decimal("0.250000")
    unresolved_conflict_weight: Decimal = Decimal("0.200000")
    stale_resolution_weight: Decimal = Decimal("0.000000")
    score_watch_floor: Decimal = Decimal("0.250000")
    score_block_floor: Decimal = Decimal("0.650000")
    conflict_ratio_watch_floor: Decimal = Decimal("0.250000")
    conflict_ratio_block_floor: Decimal = Decimal("0.650000")
    conclusion_diversity_watch_floor: Decimal = Decimal("0.250000")
    conclusion_diversity_block_floor: Decimal = Decimal("0.650000")
    contradiction_severity_watch_floor: Decimal = Decimal("0.200000")
    contradiction_severity_block_floor: Decimal = Decimal("0.650000")
    unresolved_conflict_watch_floor: Decimal = Decimal("0.150000")
    unresolved_conflict_block_floor: Decimal = Decimal("0.650000")
    stale_resolution_watch_floor: Decimal = Decimal("0.300000")
    stale_resolution_block_floor: Decimal = Decimal("0.600000")
    minimum_similar_case_count: Decimal = Decimal("5")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistMemoryConflictScoreConfig:
            raise TypeError(
                "TeamSpecialistMemoryConflictScoreConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistMemoryConflictScoreConfig:
            raise ValueError(
                "config must be exactly TeamSpecialistMemoryConflictScoreConfig",
            )
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if self.config_version != DEFAULT_TEAM_SPECIALIST_MEMORY_CONFLICT_SCORE_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "conflict_ratio_weight",
            "conclusion_diversity_weight",
            "contradiction_severity_weight",
            "unresolved_conflict_weight",
            "stale_resolution_weight",
            "score_watch_floor",
            "score_block_floor",
            "conflict_ratio_watch_floor",
            "conflict_ratio_block_floor",
            "conclusion_diversity_watch_floor",
            "conclusion_diversity_block_floor",
            "contradiction_severity_watch_floor",
            "contradiction_severity_block_floor",
            "unresolved_conflict_watch_floor",
            "unresolved_conflict_block_floor",
            "stale_resolution_watch_floor",
            "stale_resolution_block_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "minimum_similar_case_count",
            _require_positive_integral_decimal(
                "minimum_similar_case_count",
                self.minimum_similar_case_count,
            ),
        )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class TeamSpecialistMemoryConflictScoreInput:
    team_id: str
    specialist_id: str
    memory_case_family: str
    similar_case_count: Decimal
    conflicting_case_count: Decimal
    conclusion_diversity_score: Decimal
    contradiction_severity_score: Decimal
    stale_resolution_ratio: Decimal
    unresolved_conflict_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistMemoryConflictScoreInput:
            raise TypeError(
                "TeamSpecialistMemoryConflictScoreInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistMemoryConflictScoreInput:
            raise ValueError("input must be exactly TeamSpecialistMemoryConflictScoreInput")
        for field_name in ("team_id", "specialist_id", "memory_case_family"):
            object.__setattr__(
                self,
                field_name,
                _require_public_identifier(field_name, getattr(self, field_name)),
            )
        for field_name in ("similar_case_count", "conflicting_case_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "conclusion_diversity_score",
            "contradiction_severity_score",
            "stale_resolution_ratio",
            "unresolved_conflict_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.conflicting_case_count > self.similar_case_count:
            raise ValueError("conflicting_case_count must not exceed similar_case_count")
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class TeamSpecialistMemoryConflictScoreReport:
    config_version: str
    team_id: str
    specialist_id: str
    memory_case_family: str
    similar_case_count: Decimal
    conflicting_case_count: Decimal
    conflict_case_ratio: Decimal
    conclusion_diversity_score: Decimal
    contradiction_severity_score: Decimal
    stale_resolution_ratio: Decimal
    unresolved_conflict_ratio: Decimal
    memory_conflict_score: Decimal
    memory_conflict_status: str
    report_status: str
    hard_flag: bool
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistMemoryConflictScoreReport:
            raise TypeError(
                "TeamSpecialistMemoryConflictScoreReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistMemoryConflictScoreReport:
            raise ValueError("report must be exactly TeamSpecialistMemoryConflictScoreReport")
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if self.config_version != DEFAULT_TEAM_SPECIALIST_MEMORY_CONFLICT_SCORE_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in ("team_id", "specialist_id", "memory_case_family"):
            object.__setattr__(
                self,
                field_name,
                _require_public_identifier(field_name, getattr(self, field_name)),
            )
        for field_name in ("similar_case_count", "conflicting_case_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "conflict_case_ratio",
            "conclusion_diversity_score",
            "contradiction_severity_score",
            "stale_resolution_ratio",
            "unresolved_conflict_ratio",
            "memory_conflict_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.conflicting_case_count > self.similar_case_count:
            raise ValueError("conflicting_case_count must not exceed similar_case_count")
        _require_status("memory_conflict_status", self.memory_conflict_status)
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
            "TeamSpecialistMemoryConflictScoreReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def score_team_specialist_memory_conflict(
    signal: TeamSpecialistMemoryConflictScoreInput,
    *,
    config: TeamSpecialistMemoryConflictScoreConfig | None = None,
) -> TeamSpecialistMemoryConflictScoreReport:
    if config is None:
        config = TeamSpecialistMemoryConflictScoreConfig()
    if type(config) is not TeamSpecialistMemoryConflictScoreConfig:
        raise ValueError("config must be a TeamSpecialistMemoryConflictScoreConfig")
    if type(signal) is not TeamSpecialistMemoryConflictScoreInput:
        raise ValueError("signal must be a TeamSpecialistMemoryConflictScoreInput")
    _require_hard_flags("config", config)
    _require_hard_flags("signal", signal)

    conflict_case_ratio = _conflict_case_ratio(signal)
    conflict_score = _memory_conflict_score(signal, conflict_case_ratio, config)
    conflict_status = _score_status(conflict_score, config)
    hard_flag = _hard_flag(signal, conflict_case_ratio, config)
    report_status = "block" if hard_flag else conflict_status
    values: dict[str, object] = {
        "config_version": config.config_version,
        "team_id": signal.team_id,
        "specialist_id": signal.specialist_id,
        "memory_case_family": signal.memory_case_family,
        "similar_case_count": signal.similar_case_count,
        "conflicting_case_count": signal.conflicting_case_count,
        "conflict_case_ratio": conflict_case_ratio,
        "conclusion_diversity_score": signal.conclusion_diversity_score,
        "contradiction_severity_score": signal.contradiction_severity_score,
        "stale_resolution_ratio": signal.stale_resolution_ratio,
        "unresolved_conflict_ratio": signal.unresolved_conflict_ratio,
        "memory_conflict_score": conflict_score,
        "memory_conflict_status": conflict_status,
        "report_status": report_status,
        "hard_flag": hard_flag,
        "reason_codes": _reason_codes(signal, conflict_case_ratio, conflict_status, hard_flag, config),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return TeamSpecialistMemoryConflictScoreReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def team_specialist_memory_conflict_score_payload(
    payload: object,
) -> dict[str, object]:
    _reject_unsafe_public_payload(
        "team_specialist_memory_conflict_score_payload",
        payload,
        allow_json_containers=True,
    )
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def _conflict_case_ratio(signal: TeamSpecialistMemoryConflictScoreInput) -> Decimal:
    if signal.similar_case_count == ZERO:
        return ZERO
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        return _quantize(signal.conflicting_case_count / signal.similar_case_count)


def _memory_conflict_score(
    signal: TeamSpecialistMemoryConflictScoreInput,
    conflict_case_ratio: Decimal,
    config: TeamSpecialistMemoryConflictScoreConfig,
) -> Decimal:
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        score = (
            conflict_case_ratio * config.conflict_ratio_weight
            + signal.conclusion_diversity_score * config.conclusion_diversity_weight
            + signal.contradiction_severity_score * config.contradiction_severity_weight
            + signal.unresolved_conflict_ratio * config.unresolved_conflict_weight
            + signal.stale_resolution_ratio * config.stale_resolution_weight
        )
    return _quantize(score)


def _score_status(
    score: Decimal,
    config: TeamSpecialistMemoryConflictScoreConfig,
) -> str:
    if score >= config.score_block_floor:
        return "block"
    if score >= config.score_watch_floor:
        return "watch"
    return "pass"


def _hard_flag(
    signal: TeamSpecialistMemoryConflictScoreInput,
    conflict_case_ratio: Decimal,
    config: TeamSpecialistMemoryConflictScoreConfig,
) -> bool:
    return (
        signal.similar_case_count < config.minimum_similar_case_count
        or conflict_case_ratio >= config.conflict_ratio_block_floor
        or signal.conclusion_diversity_score >= config.conclusion_diversity_block_floor
        or signal.contradiction_severity_score >= config.contradiction_severity_block_floor
        or signal.unresolved_conflict_ratio >= config.unresolved_conflict_block_floor
        or signal.stale_resolution_ratio >= config.stale_resolution_block_floor
    )


def _reason_codes(
    signal: TeamSpecialistMemoryConflictScoreInput,
    conflict_case_ratio: Decimal,
    conflict_status: str,
    hard_flag: bool,
    config: TeamSpecialistMemoryConflictScoreConfig,
) -> tuple[str, ...]:
    return (
        f"memory_conflict_{conflict_status}",
        _tier_reason(
            conflict_case_ratio,
            watch_floor=config.conflict_ratio_watch_floor,
            block_floor=config.conflict_ratio_block_floor,
            clear_reason="conflict_ratio_clear",
            watch_reason="conflict_ratio_watch",
            block_reason="conflict_ratio_high",
        ),
        _tier_reason(
            signal.conclusion_diversity_score,
            watch_floor=config.conclusion_diversity_watch_floor,
            block_floor=config.conclusion_diversity_block_floor,
            clear_reason="conclusion_diversity_clear",
            watch_reason="conclusion_diversity_watch",
            block_reason="conclusion_diversity_high",
        ),
        _tier_reason(
            signal.contradiction_severity_score,
            watch_floor=config.contradiction_severity_watch_floor,
            block_floor=config.contradiction_severity_block_floor,
            clear_reason="contradiction_severity_clear",
            watch_reason="contradiction_severity_watch",
            block_reason="contradiction_severity_high",
        ),
        _tier_reason(
            signal.unresolved_conflict_ratio,
            watch_floor=config.unresolved_conflict_watch_floor,
            block_floor=config.unresolved_conflict_block_floor,
            clear_reason="unresolved_conflict_clear",
            watch_reason="unresolved_conflict_watch",
            block_reason="unresolved_conflict_high",
        ),
        _tier_reason(
            signal.stale_resolution_ratio,
            watch_floor=config.stale_resolution_watch_floor,
            block_floor=config.stale_resolution_block_floor,
            clear_reason="resolution_recency_clear",
            watch_reason="resolution_recency_watch",
            block_reason="resolution_recency_stale",
        ),
        (
            "memory_depth_low"
            if signal.similar_case_count < config.minimum_similar_case_count
            else "memory_depth_sufficient"
        ),
        "hard_flag_present" if hard_flag else "hard_flag_clear",
    )


def _tier_reason(
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


def _validate_config(config: TeamSpecialistMemoryConflictScoreConfig) -> None:
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        weight_sum = _quantize(
            config.conflict_ratio_weight
            + config.conclusion_diversity_weight
            + config.contradiction_severity_weight
            + config.unresolved_conflict_weight
            + config.stale_resolution_weight,
        )
    if weight_sum != ONE:
        raise ValueError("score weights must sum to 1.000000")
    _validate_threshold_pair(
        "score",
        config.score_watch_floor,
        config.score_block_floor,
    )
    _validate_threshold_pair(
        "conflict ratio",
        config.conflict_ratio_watch_floor,
        config.conflict_ratio_block_floor,
    )
    _validate_threshold_pair(
        "conclusion diversity",
        config.conclusion_diversity_watch_floor,
        config.conclusion_diversity_block_floor,
    )
    _validate_threshold_pair(
        "contradiction severity",
        config.contradiction_severity_watch_floor,
        config.contradiction_severity_block_floor,
    )
    _validate_threshold_pair(
        "unresolved conflict",
        config.unresolved_conflict_watch_floor,
        config.unresolved_conflict_block_floor,
    )
    _validate_threshold_pair(
        "stale resolution",
        config.stale_resolution_watch_floor,
        config.stale_resolution_block_floor,
    )


def _validate_threshold_pair(
    label: str,
    watch_floor: Decimal,
    block_floor: Decimal,
) -> None:
    if watch_floor > block_floor:
        raise ValueError(f"{label} watch threshold must not exceed block threshold")


def _validate_report_consistency(report: TeamSpecialistMemoryConflictScoreReport) -> None:
    config = TeamSpecialistMemoryConflictScoreConfig(config_version=report.config_version)
    signal = TeamSpecialistMemoryConflictScoreInput(
        team_id=report.team_id,
        specialist_id=report.specialist_id,
        memory_case_family=report.memory_case_family,
        similar_case_count=report.similar_case_count,
        conflicting_case_count=report.conflicting_case_count,
        conclusion_diversity_score=report.conclusion_diversity_score,
        contradiction_severity_score=report.contradiction_severity_score,
        stale_resolution_ratio=report.stale_resolution_ratio,
        unresolved_conflict_ratio=report.unresolved_conflict_ratio,
    )
    expected_conflict_ratio = _conflict_case_ratio(signal)
    if report.conflict_case_ratio != expected_conflict_ratio:
        raise ValueError("conflict_case_ratio does not match case counts")
    expected_score = _memory_conflict_score(signal, expected_conflict_ratio, config)
    if report.memory_conflict_score != expected_score:
        raise ValueError("memory_conflict_score does not match inputs")
    expected_conflict_status = _score_status(report.memory_conflict_score, config)
    if report.memory_conflict_status != expected_conflict_status:
        raise ValueError("memory_conflict_status does not match conflict score")
    expected_hard_flag = _hard_flag(signal, expected_conflict_ratio, config)
    if report.hard_flag is not expected_hard_flag:
        raise ValueError("hard_flag does not match conflict thresholds")
    expected_report_status = "block" if expected_hard_flag else expected_conflict_status
    if report.report_status != expected_report_status:
        raise ValueError("report_status must match hard flag and conflict status")
    expected_reasons = _reason_codes(
        signal,
        expected_conflict_ratio,
        expected_conflict_status,
        expected_hard_flag,
        config,
    )
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes do not match report inputs")


def _report_values_without_digest(
    report: TeamSpecialistMemoryConflictScoreReport,
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


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be exactly str")
    if value not in _STATUS_VALUES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if normalized > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    return normalized


def _require_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return normalized


def _require_positive_integral_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_integral_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent < -6:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(SIX_PLACES)


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be exactly tuple")
    normalized: list[str] = []
    for reason in value:
        if type(reason) is not str:
            raise ValueError("reason_codes must contain exactly str values")
        if reason not in _REASON_CODES:
            raise ValueError("reason_codes contains unsupported reason")
        if _has_unsafe_public_fragment(reason):
            raise ValueError("reason_codes has unsafe public value")
        normalized.append(reason)
    return tuple(normalized)


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be exactly str")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    for character in value:
        if character not in "0123456789abcdef":
            raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if not hasattr(value, field_name):
            raise ValueError(f"{label}.{field_name} is required")
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in (
            TeamSpecialistMemoryConflictScoreConfig,
            TeamSpecialistMemoryConflictScoreInput,
            TeamSpecialistMemoryConflictScoreReport,
        ):
            raise ValueError(f"{current_path} must be a supported public dataclass")
        for field in fields(value):
            if _has_unsafe_public_fragment(field.name):
                raise ValueError(f"{field.name} has unsafe public field")
            field_path = field.name if not path else f"{path}.{field.name}"
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field_path,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{current_path} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{current_path} must be finite")
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
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
                raise ValueError(f"{item_path} has unsafe public key")
            if key in _PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True")
            if key.endswith("_status"):
                _require_status(item_path, item)
            _reject_unsafe_public_payload(
                label,
                item,
                item_path,
                allow_json_containers=True,
            )
        return
    if type(value) is list:
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=True,
            )
        return
    if type(value) is str:
        if value.strip() != value:
            raise ValueError(f"{current_path} has unsafe public value")
        if "://" in value or "?" in value:
            raise ValueError(f"{current_path} has unsafe public value")
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"{current_path} has unsafe public value")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float) or type(value) is int:
        raise ValueError(f"{current_path} must use Decimal-derived string values")
    raise ValueError(f"{current_path} is not JSON-ready")


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower().replace("-", "_")
    return any(fragment in normalized for fragment in _UNSAFE_PUBLIC_FRAGMENTS)


__all__ = [
    "DEFAULT_TEAM_SPECIALIST_MEMORY_CONFLICT_SCORE_CONFIG_VERSION",
    "TeamSpecialistMemoryConflictScoreConfig",
    "TeamSpecialistMemoryConflictScoreInput",
    "TeamSpecialistMemoryConflictScoreReport",
    "score_team_specialist_memory_conflict",
    "team_specialist_memory_conflict_score_payload",
]
