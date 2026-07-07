"""Pure specialist calibration drift report score."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal
from hashlib import sha256
from typing import Any


QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
REPORT_STATUSES = ("pass", "watch", "block")
_UNSAFE_TERM_PARTS = (
    ("raw", "_", "candidate", "_", "id"),
    ("candidate", "_", "id"),
    ("market", "_", "id"),
    ("market", "_", "slug"),
    ("question",),
    ("source", "_", "ref"),
    ("source", "_", "url"),
    ("source", "_", "text"),
    ("dsn",),
    ("table",),
    ("token",),
    ("wal", "let"),
    ("au", "th"),
    ("or", "der"),
    ("tra", "de"),
    ("position",),
    ("b", "uy"),
    ("se", "ll"),
    ("recommendation",),
    ("li", "ve"),
    ("tra", "ding"),
)
_UNSAFE_TERMS = tuple("".join(parts) for parts in _UNSAFE_TERM_PARTS)
_DIGEST_FIELDS = (
    "team_key",
    "specialist_key",
    "long_term_sample_count",
    "recent_sample_count",
    "long_term_calibration_error_bps",
    "recent_calibration_error_bps",
    "calibration_drift_bps",
    "absolute_calibration_drift_bps",
    "recent_sample_coverage_ratio",
    "drift_watch_threshold_bps",
    "drift_block_threshold_bps",
    "minimum_recent_sample_count",
    "report_status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class TeamSpecialistCalibrationDriftScoreInput:
    team_key: str
    specialist_key: str
    long_term_sample_count: Decimal
    recent_sample_count: Decimal
    long_term_calibration_error_bps: Decimal
    recent_calibration_error_bps: Decimal
    drift_watch_threshold_bps: Decimal
    drift_block_threshold_bps: Decimal
    minimum_recent_sample_count: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("team_key", self.team_key)
        _require_canonical_string("specialist_key", self.specialist_key)
        for field_name in (
            "long_term_sample_count",
            "recent_sample_count",
            "minimum_recent_sample_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "long_term_calibration_error_bps",
            "recent_calibration_error_bps",
            "drift_watch_threshold_bps",
            "drift_block_threshold_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _validate_input_consistency(self)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        reject_team_specialist_calibration_drift_score_unsafe_payload(
            "calibration drift score input",
            self,
        )
        _require_hard_flags("calibration drift score input", self)


@dataclass(frozen=True)
class TeamSpecialistCalibrationDriftScoreResult:
    team_key: str
    specialist_key: str
    long_term_sample_count: Decimal
    recent_sample_count: Decimal
    long_term_calibration_error_bps: Decimal
    recent_calibration_error_bps: Decimal
    calibration_drift_bps: Decimal
    absolute_calibration_drift_bps: Decimal
    recent_sample_coverage_ratio: Decimal
    drift_watch_threshold_bps: Decimal
    drift_block_threshold_bps: Decimal
    minimum_recent_sample_count: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("team_key", self.team_key)
        _require_canonical_string("specialist_key", self.specialist_key)
        for field_name in (
            "long_term_sample_count",
            "recent_sample_count",
            "minimum_recent_sample_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "long_term_calibration_error_bps",
            "recent_calibration_error_bps",
            "absolute_calibration_drift_bps",
            "recent_sample_coverage_ratio",
            "drift_watch_threshold_bps",
            "drift_block_threshold_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "calibration_drift_bps",
            _normalize_decimal("calibration_drift_bps", self.calibration_drift_bps),
        )
        _require_choice("report_status", self.report_status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_result_consistency(self)
        reject_team_specialist_calibration_drift_score_unsafe_payload(
            "calibration drift score result",
            self,
        )
        _require_hard_flags("calibration drift score result", self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest:
            _require_canonical_digest(self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match result fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return team_specialist_calibration_drift_score_payload(self)


def estimate_team_specialist_calibration_drift_score(
    score_input: TeamSpecialistCalibrationDriftScoreInput,
) -> TeamSpecialistCalibrationDriftScoreResult:
    if type(score_input) is not TeamSpecialistCalibrationDriftScoreInput:
        raise ValueError(
            "score_input must be a TeamSpecialistCalibrationDriftScoreInput",
        )
    _require_hard_flags("calibration drift score input", score_input)
    reject_team_specialist_calibration_drift_score_unsafe_payload(
        "calibration drift score input",
        score_input,
    )

    calibration_drift_bps = _normalize_decimal(
        "calibration_drift_bps",
        score_input.recent_calibration_error_bps
        - score_input.long_term_calibration_error_bps,
    )
    absolute_calibration_drift_bps = _normalize_nonnegative_decimal(
        "absolute_calibration_drift_bps",
        abs(calibration_drift_bps),
    )
    recent_sample_coverage_ratio = _safe_ratio(
        score_input.recent_sample_count,
        score_input.long_term_sample_count,
    )
    report_status = _report_status(
        recent_sample_count=score_input.recent_sample_count,
        minimum_recent_sample_count=score_input.minimum_recent_sample_count,
        absolute_calibration_drift_bps=absolute_calibration_drift_bps,
        drift_watch_threshold_bps=score_input.drift_watch_threshold_bps,
        drift_block_threshold_bps=score_input.drift_block_threshold_bps,
    )

    return TeamSpecialistCalibrationDriftScoreResult(
        team_key=score_input.team_key,
        specialist_key=score_input.specialist_key,
        long_term_sample_count=score_input.long_term_sample_count,
        recent_sample_count=score_input.recent_sample_count,
        long_term_calibration_error_bps=score_input.long_term_calibration_error_bps,
        recent_calibration_error_bps=score_input.recent_calibration_error_bps,
        calibration_drift_bps=calibration_drift_bps,
        absolute_calibration_drift_bps=absolute_calibration_drift_bps,
        recent_sample_coverage_ratio=recent_sample_coverage_ratio,
        drift_watch_threshold_bps=score_input.drift_watch_threshold_bps,
        drift_block_threshold_bps=score_input.drift_block_threshold_bps,
        minimum_recent_sample_count=score_input.minimum_recent_sample_count,
        report_status=report_status,
        reason_codes=_reason_codes(
            score_input.reason_codes,
            calibration_drift_bps=calibration_drift_bps,
            report_status=report_status,
            recent_sample_count=score_input.recent_sample_count,
            minimum_recent_sample_count=score_input.minimum_recent_sample_count,
        ),
    )


def team_specialist_calibration_drift_score_payload(
    result: TeamSpecialistCalibrationDriftScoreResult,
) -> dict[str, Any]:
    if type(result) is not TeamSpecialistCalibrationDriftScoreResult:
        raise ValueError("result must be a TeamSpecialistCalibrationDriftScoreResult")
    _require_hard_flags("calibration drift score result", result)
    if result.derived_validation_digest != _derived_validation_digest(result):
        raise ValueError("derived_validation_digest must match result fields")
    reject_team_specialist_calibration_drift_score_unsafe_payload(
        "calibration drift score result",
        result,
    )
    return _json_ready(asdict(result))


def reject_team_specialist_calibration_drift_score_unsafe_payload(
    label: str,
    payload: object,
) -> None:
    for item in _iter_public_strings(payload):
        lowered = item.lower()
        if any(term in lowered for term in _UNSAFE_TERMS):
            raise ValueError(f"unsafe public payload entry in {label}")


def _report_status(
    *,
    recent_sample_count: Decimal,
    minimum_recent_sample_count: Decimal,
    absolute_calibration_drift_bps: Decimal,
    drift_watch_threshold_bps: Decimal,
    drift_block_threshold_bps: Decimal,
) -> str:
    if recent_sample_count < minimum_recent_sample_count:
        return "block"
    if absolute_calibration_drift_bps >= drift_block_threshold_bps:
        return "block"
    if absolute_calibration_drift_bps >= drift_watch_threshold_bps:
        return "watch"
    return "pass"


def _reason_codes(
    existing: tuple[str, ...],
    *,
    calibration_drift_bps: Decimal,
    report_status: str,
    recent_sample_count: Decimal,
    minimum_recent_sample_count: Decimal,
) -> tuple[str, ...]:
    additions = [
        "team_specialist_calibration_drift_score",
        f"drift_{report_status}",
    ]
    if recent_sample_count < minimum_recent_sample_count:
        additions.append("recent_sample_insufficient")
    else:
        additions.append("recent_sample_sufficient")
    if calibration_drift_bps > ZERO:
        additions.append("recent_error_worse")
    elif calibration_drift_bps < ZERO:
        additions.append("recent_error_better")
    else:
        additions.append("recent_error_unchanged")
    if report_status == "block":
        additions.append("drift_block_threshold_met")
    elif report_status == "watch":
        additions.append("drift_watch_threshold_met")
    else:
        additions.append("drift_below_watch_threshold")
    return _append_reason_codes(existing, tuple(additions))


def _append_reason_codes(
    existing: tuple[str, ...],
    additions: tuple[str, ...],
) -> tuple[str, ...]:
    values = list(existing)
    for addition in additions:
        if addition not in values:
            values.append(addition)
    return tuple(values)


def _validate_input_consistency(
    value: TeamSpecialistCalibrationDriftScoreInput,
) -> None:
    if value.long_term_sample_count <= COUNT_QUANTUM - COUNT_QUANTUM:
        raise ValueError("long_term_sample_count must be positive")
    if value.recent_sample_count > value.long_term_sample_count:
        raise ValueError("recent_sample_count must not exceed long_term_sample_count")
    if value.drift_block_threshold_bps < value.drift_watch_threshold_bps:
        raise ValueError("drift_block_threshold_bps must be at least drift_watch_threshold_bps")


def _validate_result_consistency(
    result: TeamSpecialistCalibrationDriftScoreResult,
) -> None:
    if result.long_term_sample_count <= COUNT_QUANTUM - COUNT_QUANTUM:
        raise ValueError("long_term_sample_count must be positive")
    if result.recent_sample_count > result.long_term_sample_count:
        raise ValueError("recent_sample_count must not exceed long_term_sample_count")
    if result.drift_block_threshold_bps < result.drift_watch_threshold_bps:
        raise ValueError("drift_block_threshold_bps must be at least drift_watch_threshold_bps")
    expected_drift = _normalize_decimal(
        "calibration_drift_bps",
        result.recent_calibration_error_bps
        - result.long_term_calibration_error_bps,
    )
    if result.calibration_drift_bps != expected_drift:
        raise ValueError("calibration_drift_bps must match calibration error inputs")
    expected_absolute_drift = _normalize_nonnegative_decimal(
        "absolute_calibration_drift_bps",
        abs(result.calibration_drift_bps),
    )
    if result.absolute_calibration_drift_bps != expected_absolute_drift:
        raise ValueError("absolute_calibration_drift_bps must match calibration_drift_bps")
    if result.recent_sample_coverage_ratio != _safe_ratio(
        result.recent_sample_count,
        result.long_term_sample_count,
    ):
        raise ValueError("recent_sample_coverage_ratio must match sample counts")
    if result.report_status != _report_status(
        recent_sample_count=result.recent_sample_count,
        minimum_recent_sample_count=result.minimum_recent_sample_count,
        absolute_calibration_drift_bps=result.absolute_calibration_drift_bps,
        drift_watch_threshold_bps=result.drift_watch_threshold_bps,
        drift_block_threshold_bps=result.drift_block_threshold_bps,
    ):
        raise ValueError("report_status must match drift thresholds")


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _normalize_nonnegative_decimal("ratio", numerator / denominator)


def _derived_validation_digest(
    result: TeamSpecialistCalibrationDriftScoreResult,
) -> str:
    parts = tuple(
        f"{field_name}={_digest_value(getattr(result, field_name))}"
        for field_name in _DIGEST_FIELDS
    )
    return sha256("|".join(parts).encode("utf-8")).hexdigest()


def _digest_value(value: object) -> str:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, tuple):
        return "[" + ",".join(_digest_value(item) for item in value) + "]"
    if type(value) is bool:
        return "true" if value else "false"
    if type(value) is str:
        return value
    raise ValueError("digest value must be public scalar data")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    for reason_code in value:
        _require_canonical_string(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    return value


def _normalize_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return normalized.quantize(COUNT_QUANTUM)


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
    return value.quantize(QUANTUM)


def _require_choice(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values!r}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_canonical_digest(value: object) -> None:
    _require_canonical_string("derived_validation_digest", value)
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError("derived_validation_digest must be lowercase hex")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _iter_public_strings(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_public_strings(asdict(value))
    if isinstance(value, dict):
        items: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            items.append(key)
            items.extend(_iter_public_strings(item))
        return tuple(items)
    if type(value) is str:
        return (value,)
    if isinstance(value, (list, tuple)):
        items = []
        for item in value:
            items.extend(_iter_public_strings(item))
        return tuple(items)
    return ()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, int) and not isinstance(value, bool):
        raise ValueError("JSON value must not be an int")
    if isinstance(value, (str, bool)):
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


__all__ = (
    "REPORT_STATUSES",
    "TeamSpecialistCalibrationDriftScoreInput",
    "TeamSpecialistCalibrationDriftScoreResult",
    "estimate_team_specialist_calibration_drift_score",
    "team_specialist_calibration_drift_score_payload",
    "reject_team_specialist_calibration_drift_score_unsafe_payload",
)
