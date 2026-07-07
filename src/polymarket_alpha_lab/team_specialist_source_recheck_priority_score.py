"""Pure source recheck priority report score."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal
from hashlib import sha256
from typing import Any


QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
TEN = Decimal("10.000000")
TWENTY = Decimal("20.000000")
TWENTY_FIVE = Decimal("25.000000")
FIFTY = Decimal("50.000000")
HUNDRED = Decimal("100.000000")
SCORE_STATUSES = ("pass", "watch", "block")
_UNSAFE_TERM_PARTS = (
    ("raw", "_candidate", "_id"),
    ("market", "_id"),
    ("market", "_slug"),
    ("ques", "tion"),
    ("source", "_ref"),
    ("source", "_url"),
    ("source", "_text"),
    ("d", "sn"),
    ("ta", "ble"),
    ("to", "ken"),
    ("wal", "let"),
    ("au", "th"),
    ("or", "der"),
    ("tra", "de"),
    ("posi", "tion"),
    ("b", "uy"),
    ("se", "ll"),
    ("recommenda", "tion"),
)
_UNSAFE_TERMS = tuple("".join(parts) for parts in _UNSAFE_TERM_PARTS)
_DIGEST_FIELDS = (
    "source_age_hours",
    "stale_after_hours",
    "screening_dependency_count",
    "conflicting_observation_count",
    "failed_recheck_count",
    "available_recheck_capacity_count",
    "staleness_ratio",
    "age_pressure_bps",
    "dependency_pressure_bps",
    "conflict_pressure_bps",
    "failed_recheck_pressure_bps",
    "capacity_relief_bps",
    "paper_priority_score_bps",
    "watch_threshold_bps",
    "block_threshold_bps",
    "score_status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class TeamSpecialistSourceRecheckPriorityScoreInput:
    source_age_hours: Decimal
    stale_after_hours: Decimal
    screening_dependency_count: Decimal
    conflicting_observation_count: Decimal
    failed_recheck_count: Decimal
    available_recheck_capacity_count: Decimal
    watch_threshold_bps: Decimal
    block_threshold_bps: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "source_age_hours",
            "watch_threshold_bps",
            "block_threshold_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "stale_after_hours",
            _normalize_positive_decimal("stale_after_hours", self.stale_after_hours),
        )
        for field_name in (
            "screening_dependency_count",
            "conflicting_observation_count",
            "failed_recheck_count",
            "available_recheck_capacity_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_input_thresholds(self)
        reject_team_specialist_source_recheck_priority_score_unsafe_payload(
            "source recheck priority score input",
            self,
        )
        _require_hard_flags("source recheck priority score input", self)


@dataclass(frozen=True)
class TeamSpecialistSourceRecheckPriorityScoreResult:
    source_age_hours: Decimal
    stale_after_hours: Decimal
    screening_dependency_count: Decimal
    conflicting_observation_count: Decimal
    failed_recheck_count: Decimal
    available_recheck_capacity_count: Decimal
    staleness_ratio: Decimal
    age_pressure_bps: Decimal
    dependency_pressure_bps: Decimal
    conflict_pressure_bps: Decimal
    failed_recheck_pressure_bps: Decimal
    capacity_relief_bps: Decimal
    paper_priority_score_bps: Decimal
    watch_threshold_bps: Decimal
    block_threshold_bps: Decimal
    score_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "source_age_hours",
            "stale_after_hours",
            "staleness_ratio",
            "age_pressure_bps",
            "dependency_pressure_bps",
            "conflict_pressure_bps",
            "failed_recheck_pressure_bps",
            "capacity_relief_bps",
            "paper_priority_score_bps",
            "watch_threshold_bps",
            "block_threshold_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "screening_dependency_count",
            "conflicting_observation_count",
            "failed_recheck_count",
            "available_recheck_capacity_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        _require_choice("score_status", self.score_status, SCORE_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_result_consistency(self)
        reject_team_specialist_source_recheck_priority_score_unsafe_payload(
            "source recheck priority score result",
            self,
        )
        _require_hard_flags("source recheck priority score result", self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest:
            _require_canonical_digest(self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match result fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return team_specialist_source_recheck_priority_score_payload(self)


def estimate_team_specialist_source_recheck_priority_score(
    score_input: TeamSpecialistSourceRecheckPriorityScoreInput,
) -> TeamSpecialistSourceRecheckPriorityScoreResult:
    if type(score_input) is not TeamSpecialistSourceRecheckPriorityScoreInput:
        raise ValueError(
            "score_input must be a TeamSpecialistSourceRecheckPriorityScoreInput",
        )
    reject_team_specialist_source_recheck_priority_score_unsafe_payload(
        "source recheck priority score input",
        score_input,
    )
    _require_hard_flags("source recheck priority score input", score_input)

    staleness_ratio = _safe_ratio(
        score_input.source_age_hours,
        score_input.stale_after_hours,
    )
    age_pressure_bps = _minimum(staleness_ratio * FIFTY, HUNDRED)
    dependency_pressure_bps = _normalize_nonnegative_decimal(
        "dependency_pressure_bps",
        score_input.screening_dependency_count * TWENTY,
    )
    conflict_pressure_bps = _normalize_nonnegative_decimal(
        "conflict_pressure_bps",
        score_input.conflicting_observation_count * TWENTY_FIVE,
    )
    failed_recheck_pressure_bps = _normalize_nonnegative_decimal(
        "failed_recheck_pressure_bps",
        score_input.failed_recheck_count * TWENTY_FIVE,
    )
    capacity_relief_bps = _normalize_nonnegative_decimal(
        "capacity_relief_bps",
        score_input.available_recheck_capacity_count * TEN,
    )
    paper_priority_score_bps = _normalize_nonnegative_decimal(
        "paper_priority_score_bps",
        _maximum(
            ZERO,
            age_pressure_bps
            + dependency_pressure_bps
            + conflict_pressure_bps
            + failed_recheck_pressure_bps
            - capacity_relief_bps,
        ),
    )
    score_status = _score_status(
        paper_priority_score_bps,
        watch_threshold_bps=score_input.watch_threshold_bps,
        block_threshold_bps=score_input.block_threshold_bps,
    )

    return TeamSpecialistSourceRecheckPriorityScoreResult(
        source_age_hours=score_input.source_age_hours,
        stale_after_hours=score_input.stale_after_hours,
        screening_dependency_count=score_input.screening_dependency_count,
        conflicting_observation_count=score_input.conflicting_observation_count,
        failed_recheck_count=score_input.failed_recheck_count,
        available_recheck_capacity_count=score_input.available_recheck_capacity_count,
        staleness_ratio=staleness_ratio,
        age_pressure_bps=age_pressure_bps,
        dependency_pressure_bps=dependency_pressure_bps,
        conflict_pressure_bps=conflict_pressure_bps,
        failed_recheck_pressure_bps=failed_recheck_pressure_bps,
        capacity_relief_bps=capacity_relief_bps,
        paper_priority_score_bps=paper_priority_score_bps,
        watch_threshold_bps=score_input.watch_threshold_bps,
        block_threshold_bps=score_input.block_threshold_bps,
        score_status=score_status,
        reason_codes=_reason_codes(
            score_input.reason_codes,
            age_pressure_bps=age_pressure_bps,
            dependency_pressure_bps=dependency_pressure_bps,
            conflict_pressure_bps=conflict_pressure_bps,
            failed_recheck_pressure_bps=failed_recheck_pressure_bps,
            capacity_relief_bps=capacity_relief_bps,
            score_status=score_status,
        ),
    )


def team_specialist_source_recheck_priority_score_payload(
    result: TeamSpecialistSourceRecheckPriorityScoreResult,
) -> dict[str, Any]:
    if type(result) is not TeamSpecialistSourceRecheckPriorityScoreResult:
        raise ValueError(
            "result must be a TeamSpecialistSourceRecheckPriorityScoreResult",
        )
    _require_hard_flags("source recheck priority score result", result)
    if result.derived_validation_digest != _derived_validation_digest(result):
        raise ValueError("derived_validation_digest must match result fields")
    reject_team_specialist_source_recheck_priority_score_unsafe_payload(
        "source recheck priority score result",
        result,
    )
    return _json_ready(asdict(result))


def reject_team_specialist_source_recheck_priority_score_unsafe_payload(
    label: str,
    payload: object,
) -> None:
    for item in _iter_public_strings(payload):
        lowered = item.lower()
        if any(term in lowered for term in _UNSAFE_TERMS):
            raise ValueError(f"unsafe public payload entry in {label}")


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _normalize_nonnegative_decimal("ratio", numerator / denominator)


def _minimum(first: Decimal, second: Decimal) -> Decimal:
    if first <= second:
        return _normalize_nonnegative_decimal("minimum", first)
    return _normalize_nonnegative_decimal("minimum", second)


def _maximum(first: Decimal, second: Decimal) -> Decimal:
    if first >= second:
        return _normalize_nonnegative_decimal("maximum", first)
    return _normalize_nonnegative_decimal("maximum", second)


def _score_status(
    paper_priority_score_bps: Decimal,
    *,
    watch_threshold_bps: Decimal,
    block_threshold_bps: Decimal,
) -> str:
    if paper_priority_score_bps >= block_threshold_bps:
        return "block"
    if paper_priority_score_bps >= watch_threshold_bps:
        return "watch"
    return "pass"


def _reason_codes(
    existing: tuple[str, ...],
    *,
    age_pressure_bps: Decimal,
    dependency_pressure_bps: Decimal,
    conflict_pressure_bps: Decimal,
    failed_recheck_pressure_bps: Decimal,
    capacity_relief_bps: Decimal,
    score_status: str,
) -> tuple[str, ...]:
    additions = [
        "team_specialist_source_recheck_priority_score",
        f"score_{score_status}",
    ]
    if age_pressure_bps > ZERO:
        additions.append("age_pressure_present")
    if dependency_pressure_bps > ZERO:
        additions.append("dependency_pressure_present")
    if conflict_pressure_bps > ZERO:
        additions.append("conflict_pressure_present")
    if failed_recheck_pressure_bps > ZERO:
        additions.append("failed_recheck_pressure_present")
    if capacity_relief_bps > ZERO:
        additions.append("capacity_relief_applied")
    if score_status == "block":
        additions.append("block_threshold_met")
    elif score_status == "watch":
        additions.append("watch_threshold_met")
    else:
        additions.append("below_watch_threshold")
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


def _validate_input_thresholds(
    value: TeamSpecialistSourceRecheckPriorityScoreInput,
) -> None:
    if value.block_threshold_bps <= value.watch_threshold_bps:
        raise ValueError("block_threshold_bps must be greater than watch_threshold_bps")


def _validate_result_consistency(
    result: TeamSpecialistSourceRecheckPriorityScoreResult,
) -> None:
    _validate_input_thresholds(result)
    if result.staleness_ratio != _safe_ratio(
        result.source_age_hours,
        result.stale_after_hours,
    ):
        raise ValueError("staleness_ratio must match source_age_hours")
    if result.age_pressure_bps != _minimum(result.staleness_ratio * FIFTY, HUNDRED):
        raise ValueError("age_pressure_bps must match staleness_ratio")
    if result.dependency_pressure_bps != _normalize_nonnegative_decimal(
        "dependency_pressure_bps",
        result.screening_dependency_count * TWENTY,
    ):
        raise ValueError("dependency_pressure_bps must match dependency count")
    if result.conflict_pressure_bps != _normalize_nonnegative_decimal(
        "conflict_pressure_bps",
        result.conflicting_observation_count * TWENTY_FIVE,
    ):
        raise ValueError("conflict_pressure_bps must match conflict count")
    if result.failed_recheck_pressure_bps != _normalize_nonnegative_decimal(
        "failed_recheck_pressure_bps",
        result.failed_recheck_count * TWENTY_FIVE,
    ):
        raise ValueError("failed_recheck_pressure_bps must match failed recheck count")
    if result.capacity_relief_bps != _normalize_nonnegative_decimal(
        "capacity_relief_bps",
        result.available_recheck_capacity_count * TEN,
    ):
        raise ValueError("capacity_relief_bps must match capacity count")
    if result.paper_priority_score_bps != _normalize_nonnegative_decimal(
        "paper_priority_score_bps",
        _maximum(
            ZERO,
            result.age_pressure_bps
            + result.dependency_pressure_bps
            + result.conflict_pressure_bps
            + result.failed_recheck_pressure_bps
            - result.capacity_relief_bps,
        ),
    ):
        raise ValueError("paper_priority_score_bps must match score parts")
    if result.score_status != _score_status(
        result.paper_priority_score_bps,
        watch_threshold_bps=result.watch_threshold_bps,
        block_threshold_bps=result.block_threshold_bps,
    ):
        raise ValueError("score_status must match paper_priority_score_bps")


def _derived_validation_digest(
    result: TeamSpecialistSourceRecheckPriorityScoreResult,
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


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
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
    "SCORE_STATUSES",
    "TeamSpecialistSourceRecheckPriorityScoreInput",
    "TeamSpecialistSourceRecheckPriorityScoreResult",
    "estimate_team_specialist_source_recheck_priority_score",
    "team_specialist_source_recheck_priority_score_payload",
    "reject_team_specialist_source_recheck_priority_score_unsafe_payload",
)
