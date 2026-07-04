"""Pure Phase 1 strategy category cost-drag rotation digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Any

from polymarket_alpha_lab.team_paper_guard import reject_unsafe_surface_fields


DEFAULT_STRATEGY_CATEGORY_COST_DRAG_ROTATION_DIGEST_CONFIG_VERSION = (
    "strategy-category-cost-drag-rotation-digest-v0"
)

COUNT_QUANTUM = Decimal("1")
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

ROTATION_STATUSES = ("rotating_in", "rotating_out", "stable")
DIGEST_STATUSES = ("stable", "watch", "blocked")
ROTATION_STATUS_WEIGHT = {
    "rotating_in": 0,
    "rotating_out": 1,
    "stable": 2,
}
UNSAFE_PUBLIC_TEXT_PARTS = (
    ("sec", "ret"),
    ("tok", "en"),
    ("pass", "word"),
    ("api", "_key"),
    ("priv", "ate_key"),
    ("wal", "let"),
    ("au", "th"),
    ("acc", "ount"),
    ("ord", "er"),
    ("can", "cel"),
    ("rep", "lace"),
    ("bro", "ker"),
    ("tra", "de"),
    ("ht", "tp"),
    ("reque", "sts"),
    (":", "//"),
    ("?",),
    ("#",),
    ("@",),
)
UNSAFE_PUBLIC_TEXT_FRAGMENTS = tuple(
    "".join(parts) for parts in UNSAFE_PUBLIC_TEXT_PARTS
)


@dataclass(frozen=True)
class StrategyCategoryCostDragRotationDigestConfig:
    config_version: str = (
        DEFAULT_STRATEGY_CATEGORY_COST_DRAG_ROTATION_DIGEST_CONFIG_VERSION
    )
    max_cost_drag_ratio: Decimal = Decimal("0.050000")
    min_rotation_notional_share_delta: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "max_cost_drag_ratio",
            _normalize_ratio("max_cost_drag_ratio", self.max_cost_drag_ratio),
        )
        object.__setattr__(
            self,
            "min_rotation_notional_share_delta",
            _normalize_ratio(
                "min_rotation_notional_share_delta",
                self.min_rotation_notional_share_delta,
            ),
        )
        reject_unsafe_surface_fields("digest config", self)
        _require_hard_flags("digest config", self)


@dataclass(frozen=True)
class StrategyCategoryCostDragRotationObservation:
    category_id: str
    observed_at: datetime
    recommended_notional: Decimal
    realized_cost_drag: Decimal
    baseline_cost_drag: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("category_id", self.category_id)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "recommended_notional",
            _normalize_nonnegative_decimal(
                "recommended_notional",
                self.recommended_notional,
            ),
        )
        object.__setattr__(
            self,
            "realized_cost_drag",
            _normalize_ratio("realized_cost_drag", self.realized_cost_drag),
        )
        object.__setattr__(
            self,
            "baseline_cost_drag",
            _normalize_ratio("baseline_cost_drag", self.baseline_cost_drag),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        reject_unsafe_surface_fields("observation", self)
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class StrategyCategoryCostDragRotationCategoryRow:
    category_id: str
    first_observed_at: datetime | None
    latest_observed_at: datetime
    starting_recommended_notional: Decimal
    ending_recommended_notional: Decimal
    notional_delta: Decimal
    starting_notional_share_ratio: Decimal
    ending_notional_share_ratio: Decimal
    notional_share_delta_ratio: Decimal
    baseline_cost_drag_ratio: Decimal
    cost_drag_ratio: Decimal
    cost_drag_delta_ratio: Decimal
    cost_drag_excess_ratio: Decimal
    rotation_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("category_id", self.category_id)
        object.__setattr__(
            self,
            "first_observed_at",
            _as_optional_utc("first_observed_at", self.first_observed_at),
        )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        for field_name in (
            "starting_recommended_notional",
            "ending_recommended_notional",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "notional_delta",
            _normalize_decimal("notional_delta", self.notional_delta),
        )
        for field_name in (
            "starting_notional_share_ratio",
            "ending_notional_share_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "notional_share_delta_ratio",
            "cost_drag_delta_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "baseline_cost_drag_ratio",
            "cost_drag_ratio",
            "cost_drag_excess_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.rotation_status not in ROTATION_STATUSES:
            raise ValueError("rotation_status must be a known rotation status")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_category_row(self)
        reject_unsafe_surface_fields("category row", self)
        _require_hard_flags("category row", self)


@dataclass(frozen=True)
class StrategyCategoryCostDragRotationDigestReport:
    generated_at: datetime
    config_version: str
    observation_count: Decimal
    category_count: Decimal
    rotation_in_count: Decimal
    rotation_out_count: Decimal
    stable_count: Decimal
    high_cost_drag_count: Decimal
    max_cost_drag_ratio: Decimal
    max_cost_drag_excess_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    category_rows: tuple[StrategyCategoryCostDragRotationCategoryRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "observation_count",
            "category_count",
            "rotation_in_count",
            "rotation_out_count",
            "stable_count",
            "high_cost_drag_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_cost_drag_ratio",
            "max_cost_drag_excess_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.status not in DIGEST_STATUSES:
            raise ValueError("status must be a known digest status")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "category_rows",
            _normalize_category_rows(self.category_rows),
        )
        _validate_report(self)
        reject_unsafe_surface_fields("digest report", self)
        _require_hard_flags("digest report", self)


def build_strategy_category_cost_drag_rotation_digest(
    observations: Iterable[object],
    *,
    config: StrategyCategoryCostDragRotationDigestConfig,
    generated_at: datetime,
) -> StrategyCategoryCostDragRotationDigestReport:
    if type(config) is not StrategyCategoryCostDragRotationDigestConfig:
        raise ValueError(
            "config must be a StrategyCategoryCostDragRotationDigestConfig",
        )
    _require_hard_flags("digest config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    rows = _build_category_rows(normalized_observations, config=config)

    return StrategyCategoryCostDragRotationDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        observation_count=_count(len(normalized_observations)),
        category_count=_count(len(rows)),
        rotation_in_count=_status_count(rows, "rotating_in"),
        rotation_out_count=_status_count(rows, "rotating_out"),
        stable_count=_status_count(rows, "stable"),
        high_cost_drag_count=_count(
            sum(1 for row in rows if row.cost_drag_excess_ratio > ZERO),
        ),
        max_cost_drag_ratio=_max_ratio(row.cost_drag_ratio for row in rows),
        max_cost_drag_excess_ratio=_max_ratio(
            row.cost_drag_excess_ratio for row in rows
        ),
        status=_digest_status(rows),
        reason_codes=_digest_reason_codes(rows),
        category_rows=rows,
    )


def strategy_category_cost_drag_rotation_digest_payload(
    report: StrategyCategoryCostDragRotationDigestReport,
) -> dict[str, Any]:
    if type(report) is not StrategyCategoryCostDragRotationDigestReport:
        raise ValueError(
            "report must be a StrategyCategoryCostDragRotationDigestReport",
        )
    _require_hard_flags("digest report", report)
    payload = {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "observation_count": _decimal_string(report.observation_count),
        "category_count": _decimal_string(report.category_count),
        "rotation_in_count": _decimal_string(report.rotation_in_count),
        "rotation_out_count": _decimal_string(report.rotation_out_count),
        "stable_count": _decimal_string(report.stable_count),
        "high_cost_drag_count": _decimal_string(report.high_cost_drag_count),
        "max_cost_drag_ratio": _decimal_string(report.max_cost_drag_ratio),
        "max_cost_drag_excess_ratio": _decimal_string(
            report.max_cost_drag_excess_ratio,
        ),
        "status": report.status,
        "reason_codes": report.reason_codes,
        "category_rows": tuple(_category_row_payload(row) for row in report.category_rows),
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    reject_unsafe_surface_fields("digest payload", payload)
    return payload


def _category_row_payload(
    row: StrategyCategoryCostDragRotationCategoryRow,
) -> dict[str, Any]:
    return {
        "category_id": row.category_id,
        "first_observed_at": (
            None if row.first_observed_at is None else row.first_observed_at.isoformat()
        ),
        "latest_observed_at": row.latest_observed_at.isoformat(),
        "starting_recommended_notional": _decimal_string(
            row.starting_recommended_notional,
        ),
        "ending_recommended_notional": _decimal_string(
            row.ending_recommended_notional,
        ),
        "notional_delta": _decimal_string(row.notional_delta),
        "starting_notional_share_ratio": _decimal_string(
            row.starting_notional_share_ratio,
        ),
        "ending_notional_share_ratio": _decimal_string(
            row.ending_notional_share_ratio,
        ),
        "notional_share_delta_ratio": _decimal_string(
            row.notional_share_delta_ratio,
        ),
        "baseline_cost_drag_ratio": _decimal_string(row.baseline_cost_drag_ratio),
        "cost_drag_ratio": _decimal_string(row.cost_drag_ratio),
        "cost_drag_delta_ratio": _decimal_string(row.cost_drag_delta_ratio),
        "cost_drag_excess_ratio": _decimal_string(row.cost_drag_excess_ratio),
        "rotation_status": row.rotation_status,
        "reason_codes": row.reason_codes,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _build_category_rows(
    observations: tuple[StrategyCategoryCostDragRotationObservation, ...],
    *,
    config: StrategyCategoryCostDragRotationDigestConfig,
) -> tuple[StrategyCategoryCostDragRotationCategoryRow, ...]:
    observations_by_category: dict[
        str,
        list[StrategyCategoryCostDragRotationObservation],
    ] = {}
    for observation in observations:
        observations_by_category.setdefault(observation.category_id, []).append(
            observation,
        )

    category_points = tuple(
        _category_points(category_id, category_observations)
        for category_id, category_observations in observations_by_category.items()
    )
    starting_total = _sum_decimal(point[1].recommended_notional for point in category_points)
    ending_total = _sum_decimal(point[2].recommended_notional for point in category_points)

    rows = tuple(
        _category_row(
            category_id=category_id,
            first_observation=first_observation,
            latest_observation=latest_observation,
            source_reason_codes=source_reason_codes,
            starting_total=starting_total,
            ending_total=ending_total,
            config=config,
        )
        for (
            category_id,
            first_observation,
            latest_observation,
            source_reason_codes,
        ) in category_points
    )
    return tuple(sorted(rows, key=_row_sort_key))


def _category_points(
    category_id: str,
    observations: list[StrategyCategoryCostDragRotationObservation],
) -> tuple[
    str,
    StrategyCategoryCostDragRotationObservation,
    StrategyCategoryCostDragRotationObservation,
    tuple[str, ...],
]:
    chronological = sorted(
        observations,
        key=lambda observation: (
            observation.observed_at,
            observation.category_id,
        ),
    )
    latest_observation = chronological[-1]
    if len(chronological) == 1:
        first_observation = StrategyCategoryCostDragRotationObservation(
            category_id=category_id,
            observed_at=latest_observation.observed_at,
            recommended_notional=ZERO,
            realized_cost_drag=latest_observation.baseline_cost_drag,
            baseline_cost_drag=latest_observation.baseline_cost_drag,
            reason_codes=(),
        )
    else:
        first_observation = chronological[0]
    source_reason_codes = _normalize_reason_codes(
        "reason_codes",
        tuple(
            reason_code
            for observation in chronological
            for reason_code in observation.reason_codes
        ),
    )
    return category_id, first_observation, latest_observation, source_reason_codes


def _category_row(
    *,
    category_id: str,
    first_observation: StrategyCategoryCostDragRotationObservation,
    latest_observation: StrategyCategoryCostDragRotationObservation,
    source_reason_codes: tuple[str, ...],
    starting_total: Decimal,
    ending_total: Decimal,
    config: StrategyCategoryCostDragRotationDigestConfig,
) -> StrategyCategoryCostDragRotationCategoryRow:
    starting_share = _ratio(first_observation.recommended_notional, starting_total)
    ending_share = _ratio(latest_observation.recommended_notional, ending_total)
    share_delta = _normalize_decimal(
        "notional_share_delta_ratio",
        ending_share - starting_share,
    )
    cost_drag_delta = _normalize_decimal(
        "cost_drag_delta_ratio",
        latest_observation.realized_cost_drag - latest_observation.baseline_cost_drag,
    )
    cost_drag_excess = max(
        ZERO,
        _normalize_decimal(
            "cost_drag_excess_ratio",
            latest_observation.realized_cost_drag - config.max_cost_drag_ratio,
        ),
    )
    rotation_status = _rotation_status(
        share_delta=share_delta,
        min_rotation_notional_share_delta=config.min_rotation_notional_share_delta,
    )
    return StrategyCategoryCostDragRotationCategoryRow(
        category_id=category_id,
        first_observed_at=first_observation.observed_at,
        latest_observed_at=latest_observation.observed_at,
        starting_recommended_notional=first_observation.recommended_notional,
        ending_recommended_notional=latest_observation.recommended_notional,
        notional_delta=latest_observation.recommended_notional
        - first_observation.recommended_notional,
        starting_notional_share_ratio=starting_share,
        ending_notional_share_ratio=ending_share,
        notional_share_delta_ratio=share_delta,
        baseline_cost_drag_ratio=latest_observation.baseline_cost_drag,
        cost_drag_ratio=latest_observation.realized_cost_drag,
        cost_drag_delta_ratio=cost_drag_delta,
        cost_drag_excess_ratio=cost_drag_excess,
        rotation_status=rotation_status,
        reason_codes=_category_reason_codes(
            source_reason_codes,
            cost_drag_excess=cost_drag_excess,
            rotation_status=rotation_status,
        ),
    )


def _rotation_status(
    *,
    share_delta: Decimal,
    min_rotation_notional_share_delta: Decimal,
) -> str:
    if share_delta > min_rotation_notional_share_delta:
        return "rotating_in"
    if share_delta < -min_rotation_notional_share_delta:
        return "rotating_out"
    return "stable"


def _category_reason_codes(
    source_reason_codes: tuple[str, ...],
    *,
    cost_drag_excess: Decimal,
    rotation_status: str,
) -> tuple[str, ...]:
    reason_codes = set(source_reason_codes)
    if cost_drag_excess > ZERO:
        reason_codes.add("category_cost_drag_high")
    if rotation_status == "rotating_in":
        reason_codes.add("category_rotating_in")
    elif rotation_status == "rotating_out":
        reason_codes.add("category_rotating_out")
    else:
        reason_codes.add("category_rotation_stable")
    return tuple(sorted(reason_codes))


def _digest_status(
    rows: tuple[StrategyCategoryCostDragRotationCategoryRow, ...],
) -> str:
    if not rows:
        return "watch"
    if any(row.cost_drag_excess_ratio > ZERO for row in rows):
        return "blocked"
    if any(row.rotation_status != "stable" for row in rows):
        return "watch"
    return "stable"


def _digest_reason_codes(
    rows: tuple[StrategyCategoryCostDragRotationCategoryRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("strategy_category_cost_drag_rotation_empty",)
    source_reason_codes: set[str] = set()
    high_cost_drag = False
    rotation_detected = False
    for row in rows:
        high_cost_drag = high_cost_drag or row.cost_drag_excess_ratio > ZERO
        rotation_detected = rotation_detected or row.rotation_status != "stable"
        source_reason_codes.update(
            reason_code
            for reason_code in row.reason_codes
            if reason_code
            not in {
                "category_cost_drag_high",
                "category_rotating_in",
                "category_rotating_out",
                "category_rotation_stable",
            }
        )
    if high_cost_drag:
        source_reason_codes.add("category_cost_drag_high")
    if rotation_detected:
        source_reason_codes.add("category_rotation_detected")
    return tuple(sorted(source_reason_codes))


def _normalize_observations(
    observations: Iterable[object],
) -> tuple[StrategyCategoryCostDragRotationObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        items = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    normalized = tuple(_coerce_observation(item) for item in items)
    seen: set[tuple[str, datetime]] = set()
    for observation in normalized:
        key = (observation.category_id, observation.observed_at)
        if key in seen:
            raise ValueError("duplicate category_id/observed_at observations")
        seen.add(key)
    return normalized


def _coerce_observation(value: object) -> StrategyCategoryCostDragRotationObservation:
    if type(value) is not StrategyCategoryCostDragRotationObservation:
        raise ValueError(
            "observations must contain StrategyCategoryCostDragRotationObservation values",
        )
    _require_hard_flags("observation", value)
    return StrategyCategoryCostDragRotationObservation(
        category_id=value.category_id,
        observed_at=value.observed_at,
        recommended_notional=value.recommended_notional,
        realized_cost_drag=value.realized_cost_drag,
        baseline_cost_drag=value.baseline_cost_drag,
        reason_codes=value.reason_codes,
        paper_only=value.paper_only,
        report_only=value.report_only,
        readonly=value.readonly,
    )


def _normalize_category_rows(
    rows: Iterable[object],
) -> tuple[StrategyCategoryCostDragRotationCategoryRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("category_rows must be an iterable")
    try:
        items = tuple(rows)
    except TypeError as exc:
        raise ValueError("category_rows must be an iterable") from exc
    normalized = tuple(_coerce_category_row(item) for item in items)
    category_ids = [row.category_id for row in normalized]
    if len(category_ids) != len(set(category_ids)):
        raise ValueError("category_rows must not contain duplicate category_id values")
    return tuple(sorted(normalized, key=_row_sort_key))


def _coerce_category_row(value: object) -> StrategyCategoryCostDragRotationCategoryRow:
    if type(value) is not StrategyCategoryCostDragRotationCategoryRow:
        raise ValueError(
            "category_rows must contain StrategyCategoryCostDragRotationCategoryRow values",
        )
    _require_hard_flags("category row", value)
    return StrategyCategoryCostDragRotationCategoryRow(
        category_id=value.category_id,
        first_observed_at=value.first_observed_at,
        latest_observed_at=value.latest_observed_at,
        starting_recommended_notional=value.starting_recommended_notional,
        ending_recommended_notional=value.ending_recommended_notional,
        notional_delta=value.notional_delta,
        starting_notional_share_ratio=value.starting_notional_share_ratio,
        ending_notional_share_ratio=value.ending_notional_share_ratio,
        notional_share_delta_ratio=value.notional_share_delta_ratio,
        baseline_cost_drag_ratio=value.baseline_cost_drag_ratio,
        cost_drag_ratio=value.cost_drag_ratio,
        cost_drag_delta_ratio=value.cost_drag_delta_ratio,
        cost_drag_excess_ratio=value.cost_drag_excess_ratio,
        rotation_status=value.rotation_status,
        reason_codes=value.reason_codes,
        paper_only=value.paper_only,
        report_only=value.report_only,
        readonly=value.readonly,
    )


def _validate_category_row(row: StrategyCategoryCostDragRotationCategoryRow) -> None:
    if row.notional_delta != _normalize_decimal(
        "notional_delta",
        row.ending_recommended_notional - row.starting_recommended_notional,
    ):
        raise ValueError("notional_delta must match recommended notional endpoints")
    if row.notional_share_delta_ratio != _normalize_decimal(
        "notional_share_delta_ratio",
        row.ending_notional_share_ratio - row.starting_notional_share_ratio,
    ):
        raise ValueError("notional_share_delta_ratio must match share endpoints")
    if row.cost_drag_delta_ratio != _normalize_decimal(
        "cost_drag_delta_ratio",
        row.cost_drag_ratio - row.baseline_cost_drag_ratio,
    ):
        raise ValueError("cost_drag_delta_ratio must match cost drag endpoints")
    if row.cost_drag_excess_ratio < ZERO:
        raise ValueError("cost_drag_excess_ratio must be nonnegative")


def _validate_report(report: StrategyCategoryCostDragRotationDigestReport) -> None:
    rows = report.category_rows
    if report.category_count != _count(len(rows)):
        raise ValueError("category_count must match category_rows")
    if (
        report.rotation_in_count
        + report.rotation_out_count
        + report.stable_count
        != report.category_count
    ):
        raise ValueError("rotation status counts must match category_count")
    if report.high_cost_drag_count != _count(
        sum(1 for row in rows if row.cost_drag_excess_ratio > ZERO),
    ):
        raise ValueError("high_cost_drag_count must match category_rows")
    if report.max_cost_drag_ratio != _max_ratio(row.cost_drag_ratio for row in rows):
        raise ValueError("max_cost_drag_ratio must match category_rows")
    if report.max_cost_drag_excess_ratio != _max_ratio(
        row.cost_drag_excess_ratio for row in rows
    ):
        raise ValueError("max_cost_drag_excess_ratio must match category_rows")
    if report.status != _digest_status(rows):
        raise ValueError("status must match category_rows")
    if report.reason_codes != _digest_reason_codes(rows):
        raise ValueError("reason_codes must match category_rows")


def _row_sort_key(row: StrategyCategoryCostDragRotationCategoryRow) -> tuple[Any, ...]:
    return (
        ROTATION_STATUS_WEIGHT[row.rotation_status],
        -row.cost_drag_excess_ratio,
        -abs(row.notional_share_delta_ratio),
        row.category_id,
    )


def _status_count(
    rows: tuple[StrategyCategoryCostDragRotationCategoryRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.rotation_status == status))


def _max_ratio(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    return max(normalized)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _normalize_nonnegative_decimal("total", total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _normalize_ratio("ratio", numerator / denominator)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_reason_codes(field_name: str, values: Iterable[object]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        reason_codes = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    for reason_code in reason_codes:
        _require_canonical_string(field_name, reason_code)
    return tuple(sorted(set(reason_codes)))


def _normalize_nonnegative_count(field_name: str, value: Any) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value(rounding=ROUND_HALF_EVEN):
        raise ValueError(f"{field_name} must be an integer count")
    return decimal_value.quantize(COUNT_QUANTUM, rounding=ROUND_HALF_EVEN)


def _normalize_ratio(field_name: str, value: Any) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _normalize_nonnegative_decimal(field_name: str, value: Any) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_decimal(field_name: str, value: Any) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    return decimal_value.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _require_decimal(field_name: str, value: Any) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _as_utc(field_name: str, value: Any) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_canonical_string(field_name: str, value: Any) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_unsafe_public_text(field_name, value)


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must not contain unsafe public text")


def _require_hard_flags(label: str, value: Any) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _decimal_string(value: Decimal) -> str:
    return format(value, "f")


__all__ = (
    "DEFAULT_STRATEGY_CATEGORY_COST_DRAG_ROTATION_DIGEST_CONFIG_VERSION",
    "StrategyCategoryCostDragRotationDigestConfig",
    "StrategyCategoryCostDragRotationObservation",
    "StrategyCategoryCostDragRotationCategoryRow",
    "StrategyCategoryCostDragRotationDigestReport",
    "build_strategy_category_cost_drag_rotation_digest",
    "strategy_category_cost_drag_rotation_digest_payload",
)
