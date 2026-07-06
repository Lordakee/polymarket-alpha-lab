"""Pure Phase 1 strategy category EV-decay rotation digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Any


DEFAULT_STRATEGY_CATEGORY_EV_DECAY_ROTATION_DIGEST_CONFIG_VERSION = (
    "strategy-category-ev-decay-rotation-digest-v0"
)

COUNT_QUANTUM = Decimal("1")
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

ROW_STATUSES = ("rotate_out", "watch", "hold")
REPORT_STATUSES = ("pass", "watch", "blocked")
EMPTY_REASON_CODE = "strategy_category_ev_decay_rotation_empty"
ROW_STATUS_WEIGHT = {"rotate_out": 0, "watch": 1, "hold": 2}
REPORT_REASON_ORDER = (
    "category_ev_decay_rotate_out",
    "category_ev_decay_watch",
    "category_ev_decay_hold",
    "category_rotation_decrease",
    "category_rotation_increase",
    "category_rotation_stable",
    "ev_decay_high",
    "ev_decay_moderate",
    "ev_decay_low",
    "category_rotation_detected",
    "current_ev_low",
    "current_ev_positive",
)
UNSAFE_PUBLIC_SURFACE_FIELD_FRAGMENTS = (
    "api",
    "auth",
    "clob",
    "commit",
    "connect",
    "credential",
    "cursor",
    "database",
    "db",
    "dsn",
    "env",
    "execute",
    "http",
    "insert",
    "key",
    "order",
    "persist",
    "private",
    "request",
    "response",
    "rollback",
    "secret",
    "session",
    "sign",
    "token",
    "trade",
    "url",
    "wallet",
)


@dataclass(frozen=True)
class StrategyCategoryEvDecayRotationDigestConfig:
    config_version: str = (
        DEFAULT_STRATEGY_CATEGORY_EV_DECAY_ROTATION_DIGEST_CONFIG_VERSION
    )
    rotate_out_decay_ratio: Decimal = Decimal("0.400000")
    watch_decay_ratio: Decimal = Decimal("0.200000")
    min_rotation_ev_share_delta: Decimal = Decimal("0.100000")
    minimum_current_ev_ratio: Decimal = Decimal("0.005000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "rotate_out_decay_ratio",
            "watch_decay_ratio",
            "min_rotation_ev_share_delta",
            "minimum_current_ev_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.watch_decay_ratio >= self.rotate_out_decay_ratio:
            raise ValueError("watch_decay_ratio must be below rotate_out_decay_ratio")
        _require_hard_flags("digest config", self)


@dataclass(frozen=True)
class StrategyCategoryEvDecayRotationObservation:
    category_id: str
    observed_at: datetime
    peak_expected_value: Decimal
    current_expected_value: Decimal
    recommended_ev: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("category_id", self.category_id)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "peak_expected_value",
            _normalize_positive_decimal("peak_expected_value", self.peak_expected_value),
        )
        object.__setattr__(
            self,
            "current_expected_value",
            _normalize_nonnegative_decimal(
                "current_expected_value",
                self.current_expected_value,
            ),
        )
        if self.current_expected_value > self.peak_expected_value:
            raise ValueError("current_expected_value must be <= peak_expected_value")
        object.__setattr__(
            self,
            "recommended_ev",
            _normalize_nonnegative_decimal("recommended_ev", self.recommended_ev),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class StrategyCategoryEvDecayRotationCategoryRow:
    category_id: str
    first_observed_at: datetime
    latest_observed_at: datetime
    starting_recommended_ev: Decimal
    ending_recommended_ev: Decimal
    recommended_ev_delta: Decimal
    starting_ev_share_ratio: Decimal
    ending_ev_share_ratio: Decimal
    ev_share_delta_ratio: Decimal
    peak_expected_value_ratio: Decimal
    current_expected_value_ratio: Decimal
    expected_value_delta_ratio: Decimal
    ev_decay_ratio: Decimal
    ev_retention_ratio: Decimal
    current_ev_buffer_ratio: Decimal
    rotation_direction: str
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
            _as_utc("first_observed_at", self.first_observed_at),
        )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        for field_name in ("starting_recommended_ev", "ending_recommended_ev"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "recommended_ev_delta",
            _normalize_decimal("recommended_ev_delta", self.recommended_ev_delta),
        )
        for field_name in (
            "starting_ev_share_ratio",
            "ending_ev_share_ratio",
            "peak_expected_value_ratio",
            "current_expected_value_ratio",
            "ev_decay_ratio",
            "ev_retention_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "ev_share_delta_ratio",
            "expected_value_delta_ratio",
            "current_ev_buffer_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        if self.rotation_direction not in ("decrease", "increase", "hold"):
            raise ValueError("rotation_direction must be a known rotation direction")
        if self.rotation_status not in ROW_STATUSES:
            raise ValueError("rotation_status must be a known rotation status")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_category_row(self)
        _require_hard_flags("category row", self)


@dataclass(frozen=True)
class StrategyCategoryEvDecayRotationDigestReport:
    generated_at: datetime
    config_version: str
    observation_count: Decimal
    category_count: Decimal
    rotate_out_count: Decimal
    watch_count: Decimal
    hold_count: Decimal
    decayed_category_count: Decimal
    low_current_ev_count: Decimal
    max_ev_decay_ratio: Decimal
    average_ev_decay_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    category_rows: tuple[StrategyCategoryEvDecayRotationCategoryRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "observation_count",
            "category_count",
            "rotate_out_count",
            "watch_count",
            "hold_count",
            "decayed_category_count",
            "low_current_ev_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_ev_decay_ratio", "average_ev_decay_ratio"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.status not in REPORT_STATUSES:
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
        _require_hard_flags("digest report", self)


def build_strategy_category_ev_decay_rotation_digest(
    observations: Iterable[object],
    *,
    config: StrategyCategoryEvDecayRotationDigestConfig,
    generated_at: datetime,
) -> StrategyCategoryEvDecayRotationDigestReport:
    if type(config) is not StrategyCategoryEvDecayRotationDigestConfig:
        raise ValueError(
            "config must be a StrategyCategoryEvDecayRotationDigestConfig",
        )
    _require_hard_flags("digest config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    rows = _build_category_rows(normalized_observations, config=config)

    return StrategyCategoryEvDecayRotationDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        observation_count=_count(len(normalized_observations)),
        category_count=_count(len(rows)),
        rotate_out_count=_status_count(rows, "rotate_out"),
        watch_count=_status_count(rows, "watch"),
        hold_count=_status_count(rows, "hold"),
        decayed_category_count=_count(
            sum(1 for row in rows if row.ev_decay_ratio >= config.rotate_out_decay_ratio),
        ),
        low_current_ev_count=_count(
            sum(1 for row in rows if row.current_ev_buffer_ratio < ZERO),
        ),
        max_ev_decay_ratio=_max_ratio(row.ev_decay_ratio for row in rows),
        average_ev_decay_ratio=_average_report_ev_decay_ratio(rows),
        status=_digest_status(rows),
        reason_codes=_digest_reason_codes(rows),
        category_rows=rows,
    )


def strategy_category_ev_decay_rotation_digest_payload(
    report: StrategyCategoryEvDecayRotationDigestReport,
) -> dict[str, Any]:
    if type(report) is not StrategyCategoryEvDecayRotationDigestReport:
        raise ValueError(
            "report must be a StrategyCategoryEvDecayRotationDigestReport",
        )
    _require_hard_flags("digest report", report)
    _validate_public_payload_source(report)
    payload = {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "observation_count": _decimal_string(report.observation_count),
        "category_count": _decimal_string(report.category_count),
        "rotate_out_count": _decimal_string(report.rotate_out_count),
        "watch_count": _decimal_string(report.watch_count),
        "hold_count": _decimal_string(report.hold_count),
        "decayed_category_count": _decimal_string(report.decayed_category_count),
        "low_current_ev_count": _decimal_string(report.low_current_ev_count),
        "max_ev_decay_ratio": _decimal_string(report.max_ev_decay_ratio),
        "average_ev_decay_ratio": _decimal_string(report.average_ev_decay_ratio),
        "status": report.status,
        "reason_codes": report.reason_codes,
        "category_rows": tuple(_category_row_payload(row) for row in report.category_rows),
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    _reject_unsafe_public_surface_fields("digest payload", payload)
    return payload


def _category_row_payload(
    row: StrategyCategoryEvDecayRotationCategoryRow,
) -> dict[str, Any]:
    return {
        "category_id": row.category_id,
        "first_observed_at": row.first_observed_at.isoformat(),
        "latest_observed_at": row.latest_observed_at.isoformat(),
        "starting_recommended_ev": _decimal_string(row.starting_recommended_ev),
        "ending_recommended_ev": _decimal_string(row.ending_recommended_ev),
        "recommended_ev_delta": _decimal_string(row.recommended_ev_delta),
        "starting_ev_share_ratio": _decimal_string(row.starting_ev_share_ratio),
        "ending_ev_share_ratio": _decimal_string(row.ending_ev_share_ratio),
        "ev_share_delta_ratio": _decimal_string(row.ev_share_delta_ratio),
        "peak_expected_value_ratio": _decimal_string(row.peak_expected_value_ratio),
        "current_expected_value_ratio": _decimal_string(
            row.current_expected_value_ratio,
        ),
        "expected_value_delta_ratio": _decimal_string(row.expected_value_delta_ratio),
        "ev_decay_ratio": _decimal_string(row.ev_decay_ratio),
        "ev_retention_ratio": _decimal_string(row.ev_retention_ratio),
        "current_ev_buffer_ratio": _decimal_string(row.current_ev_buffer_ratio),
        "rotation_direction": row.rotation_direction,
        "rotation_status": row.rotation_status,
        "reason_codes": row.reason_codes,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _build_category_rows(
    observations: tuple[StrategyCategoryEvDecayRotationObservation, ...],
    *,
    config: StrategyCategoryEvDecayRotationDigestConfig,
) -> tuple[StrategyCategoryEvDecayRotationCategoryRow, ...]:
    observations_by_category: dict[
        str,
        list[StrategyCategoryEvDecayRotationObservation],
    ] = {}
    for observation in observations:
        observations_by_category.setdefault(observation.category_id, []).append(
            observation,
        )

    category_points = tuple(
        _category_points(category_id, category_observations)
        for category_id, category_observations in observations_by_category.items()
    )
    starting_total = _sum_decimal(point[1].recommended_ev for point in category_points)
    ending_total = _sum_decimal(point[2].recommended_ev for point in category_points)
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
    observations: list[StrategyCategoryEvDecayRotationObservation],
) -> tuple[
    str,
    StrategyCategoryEvDecayRotationObservation,
    StrategyCategoryEvDecayRotationObservation,
    tuple[str, ...],
]:
    ordered = sorted(
        observations,
        key=lambda observation: (
            observation.observed_at,
            observation.category_id,
        ),
    )
    latest_observation = ordered[-1]
    if len(ordered) == 1:
        first_observation = StrategyCategoryEvDecayRotationObservation(
            category_id=category_id,
            observed_at=latest_observation.observed_at,
            peak_expected_value=latest_observation.peak_expected_value,
            current_expected_value=latest_observation.peak_expected_value,
            recommended_ev=ZERO,
            reason_codes=(),
        )
    else:
        first_observation = ordered[0]
    source_reason_codes = _normalize_reason_codes(
        "reason_codes",
        tuple(
            reason_code
            for observation in ordered
            for reason_code in observation.reason_codes
        ),
    )
    return category_id, first_observation, latest_observation, source_reason_codes


def _category_row(
    *,
    category_id: str,
    first_observation: StrategyCategoryEvDecayRotationObservation,
    latest_observation: StrategyCategoryEvDecayRotationObservation,
    source_reason_codes: tuple[str, ...],
    starting_total: Decimal,
    ending_total: Decimal,
    config: StrategyCategoryEvDecayRotationDigestConfig,
) -> StrategyCategoryEvDecayRotationCategoryRow:
    starting_share = _ratio(first_observation.recommended_ev, starting_total)
    ending_share = _ratio(latest_observation.recommended_ev, ending_total)
    share_delta = _normalize_decimal(
        "ev_share_delta_ratio",
        ending_share - starting_share,
    )
    expected_value_delta = _normalize_decimal(
        "expected_value_delta_ratio",
        latest_observation.current_expected_value
        - latest_observation.peak_expected_value,
    )
    ev_decay = _ratio(
        latest_observation.peak_expected_value
        - latest_observation.current_expected_value,
        latest_observation.peak_expected_value,
    )
    ev_retention = _normalize_ratio("ev_retention_ratio", ONE - ev_decay)
    current_ev_buffer = _normalize_decimal(
        "current_ev_buffer_ratio",
        latest_observation.current_expected_value - config.minimum_current_ev_ratio,
    )
    rotation_status = _rotation_status(ev_decay=ev_decay, config=config)
    rotation_direction = _rotation_direction(
        share_delta=share_delta,
        min_rotation_ev_share_delta=config.min_rotation_ev_share_delta,
    )
    rotation_reason = _rotation_reason(
        share_delta=share_delta,
        min_rotation_ev_share_delta=config.min_rotation_ev_share_delta,
    )
    return StrategyCategoryEvDecayRotationCategoryRow(
        category_id=category_id,
        first_observed_at=first_observation.observed_at,
        latest_observed_at=latest_observation.observed_at,
        starting_recommended_ev=first_observation.recommended_ev,
        ending_recommended_ev=latest_observation.recommended_ev,
        recommended_ev_delta=latest_observation.recommended_ev
        - first_observation.recommended_ev,
        starting_ev_share_ratio=starting_share,
        ending_ev_share_ratio=ending_share,
        ev_share_delta_ratio=share_delta,
        peak_expected_value_ratio=latest_observation.peak_expected_value,
        current_expected_value_ratio=latest_observation.current_expected_value,
        expected_value_delta_ratio=expected_value_delta,
        ev_decay_ratio=ev_decay,
        ev_retention_ratio=ev_retention,
        current_ev_buffer_ratio=current_ev_buffer,
        rotation_direction=rotation_direction,
        rotation_status=rotation_status,
        reason_codes=_category_reason_codes(
            source_reason_codes,
            current_ev_buffer=current_ev_buffer,
            ev_decay=ev_decay,
            rotation_reason=rotation_reason,
            rotation_status=rotation_status,
        ),
    )


def _rotation_status(
    *,
    ev_decay: Decimal,
    config: StrategyCategoryEvDecayRotationDigestConfig,
) -> str:
    if ev_decay >= config.rotate_out_decay_ratio:
        return "rotate_out"
    if ev_decay >= config.watch_decay_ratio:
        return "watch"
    return "hold"


def _rotation_direction(
    *,
    share_delta: Decimal,
    min_rotation_ev_share_delta: Decimal,
) -> str:
    if share_delta < -min_rotation_ev_share_delta:
        return "decrease"
    if share_delta > min_rotation_ev_share_delta:
        return "increase"
    return "hold"


def _rotation_reason(
    *,
    share_delta: Decimal,
    min_rotation_ev_share_delta: Decimal,
) -> str:
    if share_delta < -min_rotation_ev_share_delta:
        return "decrease"
    if share_delta > min_rotation_ev_share_delta:
        return "increase"
    return "hold"


def _category_reason_codes(
    source_reason_codes: tuple[str, ...],
    *,
    current_ev_buffer: Decimal,
    ev_decay: Decimal,
    rotation_reason: str,
    rotation_status: str,
) -> tuple[str, ...]:
    reason_codes = set(source_reason_codes)
    if rotation_status == "rotate_out":
        reason_codes.add("category_ev_decay_rotate_out")
        reason_codes.add("ev_decay_high")
    elif rotation_status == "watch":
        reason_codes.add("category_ev_decay_watch")
        reason_codes.add("ev_decay_moderate")
    else:
        reason_codes.add("category_ev_decay_hold")
        reason_codes.add("ev_decay_low")
    if rotation_reason == "decrease":
        reason_codes.add("category_rotation_decrease")
    elif rotation_reason == "increase":
        reason_codes.add("category_rotation_increase")
    else:
        reason_codes.add("category_rotation_stable")
    if current_ev_buffer < ZERO:
        reason_codes.add("current_ev_low")
    else:
        reason_codes.add("current_ev_positive")
    if ev_decay < ZERO:
        raise ValueError("ev_decay must be nonnegative")
    return tuple(sorted(reason_codes, key=_reason_sort_key))


def _digest_status(
    rows: tuple[StrategyCategoryEvDecayRotationCategoryRow, ...],
) -> str:
    if not rows:
        return "watch"
    if any(row.rotation_status == "rotate_out" for row in rows):
        return "blocked"
    if any(row.rotation_status == "watch" for row in rows):
        return "watch"
    if any(row.current_ev_buffer_ratio < ZERO for row in rows):
        return "watch"
    return "pass"


def _digest_reason_codes(
    rows: tuple[StrategyCategoryEvDecayRotationCategoryRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    reason_codes: set[str] = set()
    rotation_detected = False
    for row in rows:
        rotation_detected = rotation_detected or row.rotation_direction != "hold"
        reason_codes.update(
            reason_code
            for reason_code in row.reason_codes
            if reason_code
            not in {
                "category_rotation_decrease",
                "category_rotation_increase",
                "category_rotation_stable",
                "current_ev_positive",
                "current_ev_low",
            }
        )
    if rotation_detected:
        reason_codes.add("category_rotation_detected")
    return tuple(sorted(reason_codes, key=_reason_sort_key))


def _normalize_observations(
    observations: Iterable[object],
) -> tuple[StrategyCategoryEvDecayRotationObservation, ...]:
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


def _coerce_observation(value: object) -> StrategyCategoryEvDecayRotationObservation:
    if type(value) is not StrategyCategoryEvDecayRotationObservation:
        raise ValueError(
            "observations must contain StrategyCategoryEvDecayRotationObservation values",
        )
    _require_hard_flags("observation", value)
    return StrategyCategoryEvDecayRotationObservation(
        category_id=value.category_id,
        observed_at=value.observed_at,
        peak_expected_value=value.peak_expected_value,
        current_expected_value=value.current_expected_value,
        recommended_ev=value.recommended_ev,
        reason_codes=value.reason_codes,
        paper_only=value.paper_only,
        report_only=value.report_only,
        readonly=value.readonly,
    )


def _normalize_category_rows(
    rows: Iterable[object],
) -> tuple[StrategyCategoryEvDecayRotationCategoryRow, ...]:
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


def _coerce_category_row(value: object) -> StrategyCategoryEvDecayRotationCategoryRow:
    if type(value) is not StrategyCategoryEvDecayRotationCategoryRow:
        raise ValueError(
            "category_rows must contain StrategyCategoryEvDecayRotationCategoryRow values",
        )
    _require_hard_flags("category row", value)
    return StrategyCategoryEvDecayRotationCategoryRow(
        category_id=value.category_id,
        first_observed_at=value.first_observed_at,
        latest_observed_at=value.latest_observed_at,
        starting_recommended_ev=value.starting_recommended_ev,
        ending_recommended_ev=value.ending_recommended_ev,
        recommended_ev_delta=value.recommended_ev_delta,
        starting_ev_share_ratio=value.starting_ev_share_ratio,
        ending_ev_share_ratio=value.ending_ev_share_ratio,
        ev_share_delta_ratio=value.ev_share_delta_ratio,
        peak_expected_value_ratio=value.peak_expected_value_ratio,
        current_expected_value_ratio=value.current_expected_value_ratio,
        expected_value_delta_ratio=value.expected_value_delta_ratio,
        ev_decay_ratio=value.ev_decay_ratio,
        ev_retention_ratio=value.ev_retention_ratio,
        current_ev_buffer_ratio=value.current_ev_buffer_ratio,
        rotation_direction=value.rotation_direction,
        rotation_status=value.rotation_status,
        reason_codes=value.reason_codes,
        paper_only=value.paper_only,
        report_only=value.report_only,
        readonly=value.readonly,
    )


def _validate_category_row(row: StrategyCategoryEvDecayRotationCategoryRow) -> None:
    if row.recommended_ev_delta != _normalize_decimal(
        "recommended_ev_delta",
        row.ending_recommended_ev - row.starting_recommended_ev,
    ):
        raise ValueError("recommended_ev_delta must match recommended EV endpoints")
    if row.ev_share_delta_ratio != _normalize_decimal(
        "ev_share_delta_ratio",
        row.ending_ev_share_ratio - row.starting_ev_share_ratio,
    ):
        raise ValueError("ev_share_delta_ratio must match share endpoints")
    if row.expected_value_delta_ratio != _normalize_decimal(
        "expected_value_delta_ratio",
        row.current_expected_value_ratio - row.peak_expected_value_ratio,
    ):
        raise ValueError("expected_value_delta_ratio must match expected value endpoints")
    if row.ev_retention_ratio != _normalize_ratio(
        "ev_retention_ratio",
        ONE - row.ev_decay_ratio,
    ):
        raise ValueError("ev_retention_ratio must match ev_decay_ratio")


def _validate_report(report: StrategyCategoryEvDecayRotationDigestReport) -> None:
    rows = report.category_rows
    if report.category_count != _count(len(rows)):
        raise ValueError("category_count must match category_rows")
    if (
        report.rotate_out_count
        + report.watch_count
        + report.hold_count
        != report.category_count
    ):
        raise ValueError("rotation status counts must match category_count")
    if report.decayed_category_count != _count(
        sum(1 for row in rows if row.rotation_status == "rotate_out"),
    ):
        raise ValueError("decayed_category_count must match category_rows")
    if report.low_current_ev_count != _count(
        sum(1 for row in rows if row.current_ev_buffer_ratio < ZERO),
    ):
        raise ValueError("low_current_ev_count must match category_rows")
    if report.max_ev_decay_ratio != _max_ratio(row.ev_decay_ratio for row in rows):
        raise ValueError("max_ev_decay_ratio must match category_rows")
    if report.average_ev_decay_ratio != _average_report_ev_decay_ratio(rows):
        raise ValueError("average_ev_decay_ratio must match category_rows")
    if report.status != _digest_status(rows):
        raise ValueError("status must match category_rows")
    if report.reason_codes != _digest_reason_codes(rows):
        raise ValueError("reason_codes must match category_rows")


def _validate_public_payload_source(
    report: StrategyCategoryEvDecayRotationDigestReport,
) -> None:
    _reject_unsafe_public_surface_fields("digest report", report)
    normalized_rows = _normalize_category_rows(report.category_rows)
    if report.category_rows != normalized_rows:
        raise ValueError("category_rows must be canonical")
    _validate_report(report)


def _reject_unsafe_public_surface_fields(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        field_names = {field.name for field in fields(value)}
        for field_name in field_names:
            _reject_unsafe_public_field_name(label, field_name)
            _reject_unsafe_public_surface_fields(
                f"{label}.{field_name}",
                getattr(value, field_name),
            )
        for key, item in getattr(value, "__dict__", {}).items():
            if key in field_names:
                continue
            _reject_unsafe_public_field_name(label, key)
            _reject_unsafe_public_surface_fields(f"{label}.{key}", item)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_field_name(label, key)
            _reject_unsafe_public_surface_fields(f"{label}.{key}", item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_surface_fields(label, item)


def _reject_unsafe_public_field_name(label: str, field_name: str) -> None:
    normalized = field_name.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_SURFACE_FIELD_FRAGMENTS):
        raise ValueError(f"unsafe live surface field in {label}: {field_name}")


def _row_sort_key(row: StrategyCategoryEvDecayRotationCategoryRow) -> tuple[Any, ...]:
    return (
        ROW_STATUS_WEIGHT[row.rotation_status],
        -row.ev_decay_ratio,
        -abs(row.ev_share_delta_ratio),
        row.category_id,
    )


def _reason_sort_key(reason_code: str) -> tuple[int, str]:
    try:
        return REPORT_REASON_ORDER.index(reason_code), reason_code
    except ValueError:
        return len(REPORT_REASON_ORDER), reason_code


def _status_count(
    rows: tuple[StrategyCategoryEvDecayRotationCategoryRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.rotation_status == status))


def _max_ratio(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    return max(normalized)


def _mean_ratio(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    return _normalize_ratio("average_ev_decay_ratio", sum(normalized, ZERO) / len(normalized))


def _average_report_ev_decay_ratio(
    rows: tuple[StrategyCategoryEvDecayRotationCategoryRow, ...],
) -> Decimal:
    return _mean_ratio(
        ZERO
        if "category_rotation_increase" in row.reason_codes
        else row.ev_decay_ratio
        for row in rows
    )


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
    return tuple(sorted(set(reason_codes), key=_reason_sort_key))


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


def _normalize_positive_decimal(field_name: str, value: Any) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
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


def _require_canonical_string(field_name: str, value: Any) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


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
    "DEFAULT_STRATEGY_CATEGORY_EV_DECAY_ROTATION_DIGEST_CONFIG_VERSION",
    "StrategyCategoryEvDecayRotationDigestConfig",
    "StrategyCategoryEvDecayRotationObservation",
    "StrategyCategoryEvDecayRotationCategoryRow",
    "StrategyCategoryEvDecayRotationDigestReport",
    "build_strategy_category_ev_decay_rotation_digest",
    "strategy_category_ev_decay_rotation_digest_payload",
)
