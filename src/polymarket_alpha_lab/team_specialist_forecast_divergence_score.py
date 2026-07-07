"""Pure team specialist forecast divergence report score."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal
from hashlib import sha256
from typing import Any


QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
HUNDRED = Decimal("100.000000")
SCORE_STATUSES = ("pass", "watch", "block")
_UNSAFE_TERM_PARTS = (
    ("raw", "_", "candidate", "_", "id"),
    ("mar", "ket", "_", "id"),
    ("mar", "ket", "_", "slug"),
    ("mar", "ket", "_", "question"),
    ("source", "_", "ref"),
    ("source", "_", "url"),
    ("source", "_", "text"),
    ("d", "sn"),
    ("ta", "ble"),
    ("to", "ken"),
    ("wal", "let"),
    ("au", "th"),
    ("or", "der"),
    ("tra", "de"),
    ("po", "sition"),
    ("b", "uy"),
    ("se", "ll"),
    ("recom", "mendation"),
)
_UNSAFE_TERMS = tuple("".join(parts) for parts in _UNSAFE_TERM_PARTS)
_DIGEST_FIELDS = (
    "specialist_group_id",
    "forecast_scope_id",
    "specialist_forecast_count",
    "minimum_forecast_count",
    "minimum_forecast_probability",
    "maximum_forecast_probability",
    "mean_forecast_probability",
    "interquartile_range",
    "stdev_probability",
    "watch_divergence_threshold",
    "block_divergence_threshold",
    "forecast_range_ratio",
    "dispersion_pressure_ratio",
    "forecast_count_gap",
    "forecast_divergence_score",
    "report_status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class TeamSpecialistForecastDivergenceScoreInput:
    specialist_group_id: str
    forecast_scope_id: str
    specialist_forecast_count: Decimal
    minimum_forecast_count: Decimal
    minimum_forecast_probability: Decimal
    maximum_forecast_probability: Decimal
    mean_forecast_probability: Decimal
    interquartile_range: Decimal
    stdev_probability: Decimal
    watch_divergence_threshold: Decimal
    block_divergence_threshold: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("specialist_group_id", self.specialist_group_id)
        _require_canonical_string("forecast_scope_id", self.forecast_scope_id)
        for field_name in ("specialist_forecast_count", "minimum_forecast_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "minimum_forecast_probability",
            "maximum_forecast_probability",
            "mean_forecast_probability",
            "interquartile_range",
            "stdev_probability",
            "watch_divergence_threshold",
            "block_divergence_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_input_consistency(self)
        reject_team_specialist_forecast_divergence_score_unsafe_payload(
            "forecast divergence score input",
            self,
        )
        _require_paper_flags("forecast divergence score input", self)


@dataclass(frozen=True)
class TeamSpecialistForecastDivergenceScoreResult:
    specialist_group_id: str
    forecast_scope_id: str
    specialist_forecast_count: Decimal
    minimum_forecast_count: Decimal
    minimum_forecast_probability: Decimal
    maximum_forecast_probability: Decimal
    mean_forecast_probability: Decimal
    interquartile_range: Decimal
    stdev_probability: Decimal
    watch_divergence_threshold: Decimal
    block_divergence_threshold: Decimal
    forecast_range_ratio: Decimal
    dispersion_pressure_ratio: Decimal
    forecast_count_gap: Decimal
    forecast_divergence_score: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("specialist_group_id", self.specialist_group_id)
        _require_canonical_string("forecast_scope_id", self.forecast_scope_id)
        for field_name in ("specialist_forecast_count", "minimum_forecast_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "minimum_forecast_probability",
            "maximum_forecast_probability",
            "mean_forecast_probability",
            "interquartile_range",
            "stdev_probability",
            "watch_divergence_threshold",
            "block_divergence_threshold",
            "forecast_range_ratio",
            "dispersion_pressure_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "forecast_count_gap",
            _normalize_count("forecast_count_gap", self.forecast_count_gap),
        )
        object.__setattr__(
            self,
            "forecast_divergence_score",
            _normalize_nonnegative_decimal(
                "forecast_divergence_score",
                self.forecast_divergence_score,
            ),
        )
        _require_choice("report_status", self.report_status, SCORE_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_result_consistency(self)
        reject_team_specialist_forecast_divergence_score_unsafe_payload(
            "forecast divergence score result",
            self,
        )
        _require_paper_flags("forecast divergence score result", self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest:
            _require_canonical_digest(self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match result fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return team_specialist_forecast_divergence_score_payload(self)


def estimate_team_specialist_forecast_divergence_score(
    score_input: TeamSpecialistForecastDivergenceScoreInput,
) -> TeamSpecialistForecastDivergenceScoreResult:
    if type(score_input) is not TeamSpecialistForecastDivergenceScoreInput:
        raise ValueError(
            "score_input must be a TeamSpecialistForecastDivergenceScoreInput",
        )
    reject_team_specialist_forecast_divergence_score_unsafe_payload(
        "forecast divergence score input",
        score_input,
    )
    _require_paper_flags("forecast divergence score input", score_input)

    forecast_range_ratio = _forecast_range_ratio(score_input)
    dispersion_pressure_ratio = _dispersion_pressure_ratio(
        forecast_range_ratio=forecast_range_ratio,
        interquartile_range=score_input.interquartile_range,
        stdev_probability=score_input.stdev_probability,
    )
    forecast_count_gap = _forecast_count_gap(
        score_input.specialist_forecast_count,
        score_input.minimum_forecast_count,
    )
    forecast_divergence_score = _normalize_nonnegative_decimal(
        "forecast_divergence_score",
        dispersion_pressure_ratio * HUNDRED,
    )
    report_status = _report_status(
        forecast_count_gap=forecast_count_gap,
        dispersion_pressure_ratio=dispersion_pressure_ratio,
        watch_divergence_threshold=score_input.watch_divergence_threshold,
        block_divergence_threshold=score_input.block_divergence_threshold,
    )

    return TeamSpecialistForecastDivergenceScoreResult(
        specialist_group_id=score_input.specialist_group_id,
        forecast_scope_id=score_input.forecast_scope_id,
        specialist_forecast_count=score_input.specialist_forecast_count,
        minimum_forecast_count=score_input.minimum_forecast_count,
        minimum_forecast_probability=score_input.minimum_forecast_probability,
        maximum_forecast_probability=score_input.maximum_forecast_probability,
        mean_forecast_probability=score_input.mean_forecast_probability,
        interquartile_range=score_input.interquartile_range,
        stdev_probability=score_input.stdev_probability,
        watch_divergence_threshold=score_input.watch_divergence_threshold,
        block_divergence_threshold=score_input.block_divergence_threshold,
        forecast_range_ratio=forecast_range_ratio,
        dispersion_pressure_ratio=dispersion_pressure_ratio,
        forecast_count_gap=forecast_count_gap,
        forecast_divergence_score=forecast_divergence_score,
        report_status=report_status,
        reason_codes=_reason_codes(
            score_input.reason_codes,
            forecast_count_gap=forecast_count_gap,
            dispersion_pressure_ratio=dispersion_pressure_ratio,
            watch_divergence_threshold=score_input.watch_divergence_threshold,
            block_divergence_threshold=score_input.block_divergence_threshold,
            report_status=report_status,
        ),
    )


def team_specialist_forecast_divergence_score_payload(
    result: TeamSpecialistForecastDivergenceScoreResult,
) -> dict[str, Any]:
    if type(result) is not TeamSpecialistForecastDivergenceScoreResult:
        raise ValueError(
            "result must be a TeamSpecialistForecastDivergenceScoreResult",
        )
    _require_paper_flags("forecast divergence score result", result)
    if result.derived_validation_digest != _derived_validation_digest(result):
        raise ValueError("derived_validation_digest must match result fields")
    reject_team_specialist_forecast_divergence_score_unsafe_payload(
        "forecast divergence score result",
        result,
    )
    return _json_ready(asdict(result))


def reject_team_specialist_forecast_divergence_score_unsafe_payload(
    label: str,
    payload: object,
) -> None:
    for item in _iter_public_strings(payload):
        lowered = item.lower()
        if any(term in lowered for term in _UNSAFE_TERMS):
            raise ValueError(f"unsafe public payload entry in {label}")


def _forecast_range_ratio(
    score_input: TeamSpecialistForecastDivergenceScoreInput,
) -> Decimal:
    return _normalize_ratio(
        "forecast_range_ratio",
        score_input.maximum_forecast_probability
        - score_input.minimum_forecast_probability,
    )


def _dispersion_pressure_ratio(
    *,
    forecast_range_ratio: Decimal,
    interquartile_range: Decimal,
    stdev_probability: Decimal,
) -> Decimal:
    return max(forecast_range_ratio, interquartile_range, stdev_probability)


def _forecast_count_gap(
    specialist_forecast_count: Decimal,
    minimum_forecast_count: Decimal,
) -> Decimal:
    if specialist_forecast_count >= minimum_forecast_count:
        return COUNT_QUANTUM - COUNT_QUANTUM
    return (minimum_forecast_count - specialist_forecast_count).quantize(COUNT_QUANTUM)


def _report_status(
    *,
    forecast_count_gap: Decimal,
    dispersion_pressure_ratio: Decimal,
    watch_divergence_threshold: Decimal,
    block_divergence_threshold: Decimal,
) -> str:
    if forecast_count_gap > ZERO:
        return "block"
    if dispersion_pressure_ratio >= block_divergence_threshold:
        return "block"
    if dispersion_pressure_ratio >= watch_divergence_threshold:
        return "watch"
    return "pass"


def _reason_codes(
    existing: tuple[str, ...],
    *,
    forecast_count_gap: Decimal,
    dispersion_pressure_ratio: Decimal,
    watch_divergence_threshold: Decimal,
    block_divergence_threshold: Decimal,
    report_status: str,
) -> tuple[str, ...]:
    additions = [
        "team_specialist_forecast_divergence_score",
        f"score_{report_status}",
    ]
    if forecast_count_gap > ZERO:
        additions.append("forecast_count_below_minimum")
    if dispersion_pressure_ratio >= block_divergence_threshold:
        additions.append("divergence_block_threshold_met")
    elif dispersion_pressure_ratio >= watch_divergence_threshold:
        additions.append("divergence_watch_threshold_met")
    else:
        additions.append("divergence_below_watch_threshold")
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
    value: TeamSpecialistForecastDivergenceScoreInput,
) -> None:
    if value.minimum_forecast_count <= ZERO:
        raise ValueError("minimum_forecast_count must be positive")
    if value.minimum_forecast_probability > value.maximum_forecast_probability:
        raise ValueError(
            "minimum_forecast_probability must not exceed maximum_forecast_probability",
        )
    if not (
        value.minimum_forecast_probability
        <= value.mean_forecast_probability
        <= value.maximum_forecast_probability
    ):
        raise ValueError("mean_forecast_probability must be inside forecast range")
    if value.watch_divergence_threshold > value.block_divergence_threshold:
        raise ValueError(
            "watch_divergence_threshold must not exceed block_divergence_threshold",
        )


def _validate_result_consistency(
    result: TeamSpecialistForecastDivergenceScoreResult,
) -> None:
    _validate_result_input_fields(result)
    expected_range_ratio = _normalize_ratio(
        "forecast_range_ratio",
        result.maximum_forecast_probability - result.minimum_forecast_probability,
    )
    if result.forecast_range_ratio != expected_range_ratio:
        raise ValueError("forecast_range_ratio must match forecast probabilities")
    expected_pressure_ratio = _dispersion_pressure_ratio(
        forecast_range_ratio=result.forecast_range_ratio,
        interquartile_range=result.interquartile_range,
        stdev_probability=result.stdev_probability,
    )
    if result.dispersion_pressure_ratio != expected_pressure_ratio:
        raise ValueError("dispersion_pressure_ratio must match dispersion fields")
    expected_count_gap = _forecast_count_gap(
        result.specialist_forecast_count,
        result.minimum_forecast_count,
    )
    if result.forecast_count_gap != expected_count_gap:
        raise ValueError("forecast_count_gap must match forecast counts")
    expected_score = _normalize_nonnegative_decimal(
        "forecast_divergence_score",
        result.dispersion_pressure_ratio * HUNDRED,
    )
    if result.forecast_divergence_score != expected_score:
        raise ValueError("forecast_divergence_score must match dispersion pressure")
    expected_status = _report_status(
        forecast_count_gap=result.forecast_count_gap,
        dispersion_pressure_ratio=result.dispersion_pressure_ratio,
        watch_divergence_threshold=result.watch_divergence_threshold,
        block_divergence_threshold=result.block_divergence_threshold,
    )
    if result.report_status != expected_status:
        raise ValueError("report_status must match divergence thresholds")


def _validate_result_input_fields(
    value: TeamSpecialistForecastDivergenceScoreResult,
) -> None:
    if value.minimum_forecast_count <= ZERO:
        raise ValueError("minimum_forecast_count must be positive")
    if value.minimum_forecast_probability > value.maximum_forecast_probability:
        raise ValueError(
            "minimum_forecast_probability must not exceed maximum_forecast_probability",
        )
    if not (
        value.minimum_forecast_probability
        <= value.mean_forecast_probability
        <= value.maximum_forecast_probability
    ):
        raise ValueError("mean_forecast_probability must be inside forecast range")
    if value.watch_divergence_threshold > value.block_divergence_threshold:
        raise ValueError(
            "watch_divergence_threshold must not exceed block_divergence_threshold",
        )


def _derived_validation_digest(
    result: TeamSpecialistForecastDivergenceScoreResult,
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


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must not exceed 1.000000")
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


def _require_paper_flags(label: str, value: object) -> None:
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
    "SCORE_STATUSES",
    "TeamSpecialistForecastDivergenceScoreInput",
    "TeamSpecialistForecastDivergenceScoreResult",
    "estimate_team_specialist_forecast_divergence_score",
    "team_specialist_forecast_divergence_score_payload",
    "reject_team_specialist_forecast_divergence_score_unsafe_payload",
)
