from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from decimal import Decimal, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_TEAM_SPECIALIST_CASE_MIX_DRIFT_SCORE_CONFIG_VERSION = (
    "team_specialist_case_mix_drift_score.v1"
)
DIGEST_VERSION = "team_specialist_case_mix_drift_score.digest.v1"
SIX_PLACES = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT_PRECISION = 28

_STATUS_VALUES = frozenset(("pass", "watch", "block"))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "market_id",
        "candidate_id",
        "market_slug",
        "question",
        "url",
        "source_ref",
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
        "position_sizing",
    ),
)
_REASON_CODES = frozenset(
    (
        "case_mix_drift_pass",
        "case_mix_drift_watch",
        "case_mix_drift_block",
        "category_drift_clear",
        "category_drift_watch",
        "category_drift_high",
        "difficulty_drift_clear",
        "difficulty_drift_watch",
        "difficulty_drift_high",
        "calibration_decay_clear",
        "calibration_decay_watch",
        "calibration_decay_high",
        "recent_accuracy_stable",
        "recent_accuracy_watch",
        "recent_accuracy_weak",
        "historical_depth_sufficient",
        "historical_depth_low",
        "recent_depth_sufficient",
        "recent_depth_low",
        "hard_flag_clear",
        "hard_flag_present",
    ),
)


@dataclass(frozen=True)
class TeamSpecialistCaseMixDriftScoreConfig:
    config_version: str = DEFAULT_TEAM_SPECIALIST_CASE_MIX_DRIFT_SCORE_CONFIG_VERSION
    category_drift_weight: Decimal = Decimal("0.340000")
    difficulty_drift_weight: Decimal = Decimal("0.240000")
    calibration_decay_weight: Decimal = Decimal("0.220000")
    recent_accuracy_gap_weight: Decimal = Decimal("0.200000")
    score_watch_floor: Decimal = Decimal("0.250000")
    score_block_floor: Decimal = Decimal("0.650000")
    category_watch_floor: Decimal = Decimal("0.250000")
    category_block_floor: Decimal = Decimal("0.650000")
    difficulty_watch_floor: Decimal = Decimal("0.200000")
    difficulty_block_floor: Decimal = Decimal("0.650000")
    calibration_watch_floor: Decimal = Decimal("0.200000")
    calibration_block_floor: Decimal = Decimal("0.650000")
    recent_accuracy_gap_watch_floor: Decimal = Decimal("0.150000")
    recent_accuracy_gap_block_floor: Decimal = Decimal("0.400000")
    minimum_historical_case_count: Decimal = Decimal("30")
    minimum_recent_case_count: Decimal = Decimal("5")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistCaseMixDriftScoreConfig:
            raise TypeError(
                "TeamSpecialistCaseMixDriftScoreConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistCaseMixDriftScoreConfig:
            raise ValueError(
                "config must be exactly TeamSpecialistCaseMixDriftScoreConfig",
            )
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if self.config_version != DEFAULT_TEAM_SPECIALIST_CASE_MIX_DRIFT_SCORE_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "category_drift_weight",
            "difficulty_drift_weight",
            "calibration_decay_weight",
            "recent_accuracy_gap_weight",
            "score_watch_floor",
            "score_block_floor",
            "category_watch_floor",
            "category_block_floor",
            "difficulty_watch_floor",
            "difficulty_block_floor",
            "calibration_watch_floor",
            "calibration_block_floor",
            "recent_accuracy_gap_watch_floor",
            "recent_accuracy_gap_block_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "minimum_historical_case_count",
            "minimum_recent_case_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class TeamSpecialistCaseMixDriftScoreInput:
    team_id: str
    specialist_id: str
    historical_case_count: Decimal
    recent_case_count: Decimal
    category_drift_score: Decimal
    difficulty_drift_score: Decimal
    calibration_decay_score: Decimal
    recent_accuracy_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistCaseMixDriftScoreInput:
            raise TypeError(
                "TeamSpecialistCaseMixDriftScoreInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistCaseMixDriftScoreInput:
            raise ValueError("input must be exactly TeamSpecialistCaseMixDriftScoreInput")
        for field_name in ("team_id", "specialist_id"):
            object.__setattr__(
                self,
                field_name,
                _require_public_identifier(field_name, getattr(self, field_name)),
            )
        for field_name in ("historical_case_count", "recent_case_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "category_drift_score",
            "difficulty_drift_score",
            "calibration_decay_score",
            "recent_accuracy_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class TeamSpecialistCaseMixDriftScoreReport:
    config_version: str
    team_id: str
    specialist_id: str
    historical_case_count: Decimal
    recent_case_count: Decimal
    category_drift_score: Decimal
    difficulty_drift_score: Decimal
    calibration_decay_score: Decimal
    recent_accuracy_score: Decimal
    recent_accuracy_gap_score: Decimal
    case_mix_drift_score: Decimal
    case_mix_drift_status: str
    report_status: str
    hard_flag: bool
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistCaseMixDriftScoreReport:
            raise TypeError(
                "TeamSpecialistCaseMixDriftScoreReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistCaseMixDriftScoreReport:
            raise ValueError("report must be exactly TeamSpecialistCaseMixDriftScoreReport")
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if self.config_version != DEFAULT_TEAM_SPECIALIST_CASE_MIX_DRIFT_SCORE_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in ("team_id", "specialist_id"):
            object.__setattr__(
                self,
                field_name,
                _require_public_identifier(field_name, getattr(self, field_name)),
            )
        for field_name in ("historical_case_count", "recent_case_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "category_drift_score",
            "difficulty_drift_score",
            "calibration_decay_score",
            "recent_accuracy_score",
            "recent_accuracy_gap_score",
            "case_mix_drift_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("case_mix_drift_status", self.case_mix_drift_status)
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
            "TeamSpecialistCaseMixDriftScoreReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def score_team_specialist_case_mix_drift(
    signal: TeamSpecialistCaseMixDriftScoreInput,
    *,
    config: TeamSpecialistCaseMixDriftScoreConfig | None = None,
) -> TeamSpecialistCaseMixDriftScoreReport:
    if config is None:
        config = TeamSpecialistCaseMixDriftScoreConfig()
    if type(config) is not TeamSpecialistCaseMixDriftScoreConfig:
        raise ValueError("config must be a TeamSpecialistCaseMixDriftScoreConfig")
    if type(signal) is not TeamSpecialistCaseMixDriftScoreInput:
        raise ValueError("signal must be a TeamSpecialistCaseMixDriftScoreInput")
    _require_hard_flags("config", config)
    _require_hard_flags("signal", signal)

    recent_accuracy_gap_score = _recent_accuracy_gap_score(signal.recent_accuracy_score)
    drift_score = _case_mix_drift_score(signal, recent_accuracy_gap_score, config)
    drift_status = _score_status(drift_score, config)
    hard_flag = _hard_flag(signal, config)
    report_status = "block" if hard_flag else drift_status
    values: dict[str, object] = {
        "config_version": config.config_version,
        "team_id": signal.team_id,
        "specialist_id": signal.specialist_id,
        "historical_case_count": signal.historical_case_count,
        "recent_case_count": signal.recent_case_count,
        "category_drift_score": signal.category_drift_score,
        "difficulty_drift_score": signal.difficulty_drift_score,
        "calibration_decay_score": signal.calibration_decay_score,
        "recent_accuracy_score": signal.recent_accuracy_score,
        "recent_accuracy_gap_score": recent_accuracy_gap_score,
        "case_mix_drift_score": drift_score,
        "case_mix_drift_status": drift_status,
        "report_status": report_status,
        "hard_flag": hard_flag,
        "reason_codes": _reason_codes(signal, drift_status, hard_flag, config),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return TeamSpecialistCaseMixDriftScoreReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def team_specialist_case_mix_drift_score_payload(
    payload: object,
) -> dict[str, object]:
    _reject_unsafe_public_payload(
        "team_specialist_case_mix_drift_score_payload",
        payload,
        allow_json_containers=True,
    )
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def _case_mix_drift_score(
    signal: TeamSpecialistCaseMixDriftScoreInput,
    recent_accuracy_gap_score: Decimal,
    config: TeamSpecialistCaseMixDriftScoreConfig,
) -> Decimal:
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        score = (
            signal.category_drift_score * config.category_drift_weight
            + signal.difficulty_drift_score * config.difficulty_drift_weight
            + signal.calibration_decay_score * config.calibration_decay_weight
            + recent_accuracy_gap_score * config.recent_accuracy_gap_weight
        )
    return _quantize(score)


def _recent_accuracy_gap_score(recent_accuracy_score: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        return _quantize(ONE - recent_accuracy_score)


def _score_status(
    score: Decimal,
    config: TeamSpecialistCaseMixDriftScoreConfig,
) -> str:
    if score >= config.score_block_floor:
        return "block"
    if score >= config.score_watch_floor:
        return "watch"
    return "pass"


def _hard_flag(
    signal: TeamSpecialistCaseMixDriftScoreInput,
    config: TeamSpecialistCaseMixDriftScoreConfig,
) -> bool:
    return (
        signal.historical_case_count < config.minimum_historical_case_count
        or signal.recent_case_count < config.minimum_recent_case_count
    )


def _reason_codes(
    signal: TeamSpecialistCaseMixDriftScoreInput,
    drift_status: str,
    hard_flag: bool,
    config: TeamSpecialistCaseMixDriftScoreConfig,
) -> tuple[str, ...]:
    recent_accuracy_gap_score = _recent_accuracy_gap_score(signal.recent_accuracy_score)
    return (
        f"case_mix_drift_{drift_status}",
        _tier_reason(
            signal.category_drift_score,
            watch_floor=config.category_watch_floor,
            block_floor=config.category_block_floor,
            clear_reason="category_drift_clear",
            watch_reason="category_drift_watch",
            block_reason="category_drift_high",
        ),
        _tier_reason(
            signal.difficulty_drift_score,
            watch_floor=config.difficulty_watch_floor,
            block_floor=config.difficulty_block_floor,
            clear_reason="difficulty_drift_clear",
            watch_reason="difficulty_drift_watch",
            block_reason="difficulty_drift_high",
        ),
        _tier_reason(
            signal.calibration_decay_score,
            watch_floor=config.calibration_watch_floor,
            block_floor=config.calibration_block_floor,
            clear_reason="calibration_decay_clear",
            watch_reason="calibration_decay_watch",
            block_reason="calibration_decay_high",
        ),
        _tier_reason(
            recent_accuracy_gap_score,
            watch_floor=config.recent_accuracy_gap_watch_floor,
            block_floor=config.recent_accuracy_gap_block_floor,
            clear_reason="recent_accuracy_stable",
            watch_reason="recent_accuracy_watch",
            block_reason="recent_accuracy_weak",
        ),
        (
            "historical_depth_low"
            if signal.historical_case_count < config.minimum_historical_case_count
            else "historical_depth_sufficient"
        ),
        (
            "recent_depth_low"
            if signal.recent_case_count < config.minimum_recent_case_count
            else "recent_depth_sufficient"
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


def _validate_config(config: TeamSpecialistCaseMixDriftScoreConfig) -> None:
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        weight_sum = _quantize(
            config.category_drift_weight
            + config.difficulty_drift_weight
            + config.calibration_decay_weight
            + config.recent_accuracy_gap_weight,
        )
    if weight_sum != ONE:
        raise ValueError("score weights must sum to 1.000000")
    _validate_threshold_pair(
        "score",
        config.score_watch_floor,
        config.score_block_floor,
    )
    _validate_threshold_pair(
        "category drift",
        config.category_watch_floor,
        config.category_block_floor,
    )
    _validate_threshold_pair(
        "difficulty drift",
        config.difficulty_watch_floor,
        config.difficulty_block_floor,
    )
    _validate_threshold_pair(
        "calibration decay",
        config.calibration_watch_floor,
        config.calibration_block_floor,
    )
    _validate_threshold_pair(
        "recent accuracy gap",
        config.recent_accuracy_gap_watch_floor,
        config.recent_accuracy_gap_block_floor,
    )


def _validate_threshold_pair(
    label: str,
    watch_floor: Decimal,
    block_floor: Decimal,
) -> None:
    if watch_floor > block_floor:
        raise ValueError(f"{label} watch threshold must not exceed block threshold")


def _validate_report_consistency(report: TeamSpecialistCaseMixDriftScoreReport) -> None:
    config = TeamSpecialistCaseMixDriftScoreConfig(config_version=report.config_version)
    expected_accuracy_gap = _recent_accuracy_gap_score(report.recent_accuracy_score)
    if report.recent_accuracy_gap_score != expected_accuracy_gap:
        raise ValueError("recent_accuracy_gap_score does not match recent_accuracy_score")
    signal = TeamSpecialistCaseMixDriftScoreInput(
        team_id=report.team_id,
        specialist_id=report.specialist_id,
        historical_case_count=report.historical_case_count,
        recent_case_count=report.recent_case_count,
        category_drift_score=report.category_drift_score,
        difficulty_drift_score=report.difficulty_drift_score,
        calibration_decay_score=report.calibration_decay_score,
        recent_accuracy_score=report.recent_accuracy_score,
    )
    expected_score = _case_mix_drift_score(signal, expected_accuracy_gap, config)
    if report.case_mix_drift_score != expected_score:
        raise ValueError("case_mix_drift_score does not match inputs")
    expected_drift_status = _score_status(report.case_mix_drift_score, config)
    if report.case_mix_drift_status != expected_drift_status:
        raise ValueError("case_mix_drift_status does not match drift score")
    expected_hard_flag = _hard_flag(signal, config)
    if report.hard_flag is not expected_hard_flag:
        raise ValueError("hard_flag does not match case depth thresholds")
    expected_report_status = "block" if expected_hard_flag else expected_drift_status
    if report.report_status != expected_report_status:
        raise ValueError("report_status must match hard flag and drift status")
    expected_reasons = _reason_codes(signal, expected_drift_status, expected_hard_flag, config)
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes do not match report inputs")


def _report_values_without_digest(
    report: TeamSpecialistCaseMixDriftScoreReport,
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
            TeamSpecialistCaseMixDriftScoreConfig,
            TeamSpecialistCaseMixDriftScoreInput,
            TeamSpecialistCaseMixDriftScoreReport,
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
    "DEFAULT_TEAM_SPECIALIST_CASE_MIX_DRIFT_SCORE_CONFIG_VERSION",
    "TeamSpecialistCaseMixDriftScoreConfig",
    "TeamSpecialistCaseMixDriftScoreInput",
    "TeamSpecialistCaseMixDriftScoreReport",
    "score_team_specialist_case_mix_drift",
    "team_specialist_case_mix_drift_score_payload",
]
