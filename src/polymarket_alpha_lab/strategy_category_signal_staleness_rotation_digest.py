"""Pure Phase 1 strategy category signal-staleness rotation digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Any


DEFAULT_STRATEGY_CATEGORY_SIGNAL_STALENESS_ROTATION_DIGEST_CONFIG_VERSION = (
    "strategy-category-signal-staleness-rotation-digest-v0"
)

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
MICROSECONDS_PER_SECOND = Decimal("1000000")

ROW_STATUSES = ("rotate_out", "watch", "hold")
REPORT_STATUSES = ("pass", "watch", "blocked")
ROW_STATUS_WEIGHT = {"rotate_out": 0, "watch": 1, "hold": 2}

EMPTY_REASON_CODE = "strategy_category_signal_staleness_rotation_empty"
REPORT_REASON_SEQUENCE = (
    "category_signal_staleness_rotate_out",
    "category_signal_staleness_watch",
    "category_signal_staleness_hold",
    "category_rotation_decrease",
    "category_rotation_increase",
    "category_rotation_stable",
    "stale_signal_age",
    "fresh_signal_age",
    "low_signal_quality",
    "healthy_signal_quality",
    "category_signal_rotation_detected",
)
UNSAFE_PUBLIC_TEXT_FRAGMENTS = frozenset(
    (
        "au" + "th",
        "private" + "_key",
        "api" + "_key",
        "wal" + "let",
        "acco" + "unt",
        "bala" + "nce",
        "or" + "der",
        "can" + "cel",
        "rep" + "lace",
        "sign" + "ing",
        "exchange" + "_mutation",
        "bro" + "ker",
        "li" + "ve" + "_" + "tr" + "ading",
        "li" + "ve",
        "tr" + "ading",
        "tr" + "ade",
        "cli" + "ent",
        "req" + "uest",
        "ht" + "tp",
        "soc" + "ket",
    ),
)
SENSITIVE_PUBLIC_TEXT_FRAGMENTS = frozenset(
    (
        "sec" + "ret",
        "tok" + "en",
        "bear" + "er",
        "pass" + "word",
        "pass" + "wd",
        "pwd=",
        "dsn=",
        "sk" + "_live",
        "post" + "gresql://",
        "post" + "gres://",
    ),
)

__all__ = (
    "DEFAULT_STRATEGY_CATEGORY_SIGNAL_STALENESS_ROTATION_DIGEST_CONFIG_VERSION",
    "StrategyCategorySignalStalenessRotationDigestConfig",
    "StrategyCategorySignalStalenessRotationObservation",
    "StrategyCategorySignalStalenessRotationCategoryRow",
    "StrategyCategorySignalStalenessRotationDigestReport",
    "build_strategy_category_signal_staleness_rotation_digest",
    "strategy_category_signal_staleness_rotation_digest_payload",
)


@dataclass(frozen=True)
class StrategyCategorySignalStalenessRotationDigestConfig:
    config_version: str = (
        DEFAULT_STRATEGY_CATEGORY_SIGNAL_STALENESS_ROTATION_DIGEST_CONFIG_VERSION
    )
    stale_signal_after_seconds: Decimal = Decimal("3600.000000")
    rotate_out_signal_age_seconds: Decimal = Decimal("7200.000000")
    minimum_signal_quality_ratio: Decimal = Decimal("0.500000")
    minimum_rotation_share_delta_ratio: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyCategorySignalStalenessRotationDigestConfig:
            raise ValueError(
                "config must be exactly "
                "StrategyCategorySignalStalenessRotationDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "stale_signal_after_seconds",
            "rotate_out_signal_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "minimum_signal_quality_ratio",
            "minimum_rotation_share_delta_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.stale_signal_after_seconds >= self.rotate_out_signal_age_seconds:
            raise ValueError(
                "stale_signal_after_seconds must be below rotate_out_signal_age_seconds",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyCategorySignalStalenessRotationObservation:
    category_id: str
    observed_at: datetime
    signal_generated_at: datetime
    signal_quality_ratio: Decimal
    recommended_signal_weight: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyCategorySignalStalenessRotationObservation:
            raise ValueError(
                "observation must be exactly "
                "StrategyCategorySignalStalenessRotationObservation",
            )
        _require_canonical_string("category_id", self.category_id)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "signal_generated_at",
            _as_utc("signal_generated_at", self.signal_generated_at),
        )
        object.__setattr__(
            self,
            "signal_quality_ratio",
            _normalize_ratio("signal_quality_ratio", self.signal_quality_ratio),
        )
        object.__setattr__(
            self,
            "recommended_signal_weight",
            _normalize_nonnegative_decimal(
                "recommended_signal_weight",
                self.recommended_signal_weight,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class StrategyCategorySignalStalenessRotationCategoryRow:
    category_id: str
    first_observed_at: datetime
    latest_observed_at: datetime
    latest_signal_generated_at: datetime
    starting_signal_weight: Decimal
    ending_signal_weight: Decimal
    signal_weight_delta: Decimal
    starting_signal_share_ratio: Decimal
    ending_signal_share_ratio: Decimal
    signal_share_delta_ratio: Decimal
    latest_signal_age_seconds: Decimal
    signal_quality_ratio: Decimal
    signal_quality_gap_ratio: Decimal
    rotation_direction: str
    rotation_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyCategorySignalStalenessRotationCategoryRow:
            raise ValueError(
                "category row must be exactly "
                "StrategyCategorySignalStalenessRotationCategoryRow",
            )
        _require_canonical_string("category_id", self.category_id)
        for field_name in (
            "first_observed_at",
            "latest_observed_at",
            "latest_signal_generated_at",
        ):
            object.__setattr__(self, field_name, _as_utc(field_name, getattr(self, field_name)))
        for field_name in ("starting_signal_weight", "ending_signal_weight"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "signal_weight_delta",
            _normalize_decimal("signal_weight_delta", self.signal_weight_delta),
        )
        for field_name in (
            "starting_signal_share_ratio",
            "ending_signal_share_ratio",
            "signal_quality_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("signal_share_delta_ratio", "signal_quality_gap_ratio"):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_signal_age_seconds",
            _normalize_nonnegative_decimal(
                "latest_signal_age_seconds",
                self.latest_signal_age_seconds,
            ),
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
class StrategyCategorySignalStalenessRotationDigestReport:
    generated_at: datetime
    config_version: str
    observation_count: Decimal
    category_count: Decimal
    rotate_out_count: Decimal
    watch_count: Decimal
    hold_count: Decimal
    stale_category_count: Decimal
    low_quality_category_count: Decimal
    max_signal_age_seconds: Decimal
    average_signal_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    category_rows: tuple[StrategyCategorySignalStalenessRotationCategoryRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyCategorySignalStalenessRotationDigestReport:
            raise ValueError(
                "report must be exactly StrategyCategorySignalStalenessRotationDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "observation_count",
            "category_count",
            "rotate_out_count",
            "watch_count",
            "hold_count",
            "stale_category_count",
            "low_quality_category_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_signal_age_seconds", "average_signal_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
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


def build_strategy_category_signal_staleness_rotation_digest(
    observations: Iterable[object],
    *,
    config: StrategyCategorySignalStalenessRotationDigestConfig,
    generated_at: datetime,
) -> StrategyCategorySignalStalenessRotationDigestReport:
    if type(config) is not StrategyCategorySignalStalenessRotationDigestConfig:
        raise ValueError(
            "config must be a StrategyCategorySignalStalenessRotationDigestConfig",
        )
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    for observation in normalized_observations:
        if observation.observed_at > generated_at_utc:
            raise ValueError("observed_at must be <= generated_at")
        if observation.signal_generated_at > generated_at_utc:
            raise ValueError("signal_generated_at must be <= generated_at")
    rows = _build_category_rows(
        normalized_observations,
        config=config,
        generated_at=generated_at_utc,
    )
    status = _digest_status(rows)
    return StrategyCategorySignalStalenessRotationDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        observation_count=_count(len(normalized_observations)),
        category_count=_count(len(rows)),
        rotate_out_count=_status_count(rows, "rotate_out"),
        watch_count=_status_count(rows, "watch"),
        hold_count=_status_count(rows, "hold"),
        stale_category_count=_count(
            sum(1 for row in rows if row.latest_signal_age_seconds > config.stale_signal_after_seconds),
        ),
        low_quality_category_count=_count(
            sum(1 for row in rows if row.signal_quality_ratio < config.minimum_signal_quality_ratio),
        ),
        max_signal_age_seconds=_max_decimal(row.latest_signal_age_seconds for row in rows),
        average_signal_age_seconds=_average_decimal(row.latest_signal_age_seconds for row in rows),
        status=status,
        reason_codes=_digest_reason_codes(rows),
        category_rows=rows,
    )


def strategy_category_signal_staleness_rotation_digest_payload(
    report: StrategyCategorySignalStalenessRotationDigestReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is not StrategyCategorySignalStalenessRotationDigestReport:
        if type(report) is dict:
            _reject_payload_values("digest payload", report)
            _require_hard_flags("payload", _DictFlags(report))
            payload = _json_ready(report)
            if type(payload) is not dict:
                raise ValueError("report payload must be a JSON object")
            _reject_payload_values("digest payload", payload)
            _require_hard_flags("payload", _DictFlags(payload))
            return payload
        raise ValueError(
            "report must be a StrategyCategorySignalStalenessRotationDigestReport",
        )
    _require_hard_flags("digest report", report)
    _reject_payload_values("digest report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_payload_values("digest payload", payload)
    return payload


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _build_category_rows(
    observations: tuple[StrategyCategorySignalStalenessRotationObservation, ...],
    *,
    config: StrategyCategorySignalStalenessRotationDigestConfig,
    generated_at: datetime,
) -> tuple[StrategyCategorySignalStalenessRotationCategoryRow, ...]:
    observations_by_category: dict[
        str,
        list[StrategyCategorySignalStalenessRotationObservation],
    ] = {}
    for observation in observations:
        observations_by_category.setdefault(observation.category_id, []).append(
            observation,
        )
    category_points = tuple(
        _category_points(category_id, category_observations)
        for category_id, category_observations in observations_by_category.items()
    )
    starting_total = _sum_decimal(point[1].recommended_signal_weight for point in category_points)
    ending_total = _sum_decimal(point[2].recommended_signal_weight for point in category_points)
    rows = tuple(
        _category_row(
            category_id=category_id,
            first_observation=first_observation,
            latest_observation=latest_observation,
            source_reason_codes=source_reason_codes,
            starting_total=starting_total,
            ending_total=ending_total,
            config=config,
            generated_at=generated_at,
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
    observations: list[StrategyCategorySignalStalenessRotationObservation],
) -> tuple[
    str,
    StrategyCategorySignalStalenessRotationObservation,
    StrategyCategorySignalStalenessRotationObservation,
    tuple[str, ...],
]:
    timeline = sorted(observations, key=lambda item: (item.observed_at, item.category_id))
    source_reason_codes = _normalize_reason_codes(
        "reason_codes",
        tuple(reason for item in timeline for reason in item.reason_codes),
    )
    return category_id, timeline[0], timeline[-1], source_reason_codes


def _category_row(
    *,
    category_id: str,
    first_observation: StrategyCategorySignalStalenessRotationObservation,
    latest_observation: StrategyCategorySignalStalenessRotationObservation,
    source_reason_codes: tuple[str, ...],
    starting_total: Decimal,
    ending_total: Decimal,
    config: StrategyCategorySignalStalenessRotationDigestConfig,
    generated_at: datetime,
) -> StrategyCategorySignalStalenessRotationCategoryRow:
    starting_share = _ratio(first_observation.recommended_signal_weight, starting_total)
    ending_share = _ratio(latest_observation.recommended_signal_weight, ending_total)
    share_delta = _normalize_decimal("signal_share_delta_ratio", ending_share - starting_share)
    age_seconds = _age_seconds(latest_observation.signal_generated_at, generated_at)
    quality_gap = _normalize_decimal(
        "signal_quality_gap_ratio",
        latest_observation.signal_quality_ratio - config.minimum_signal_quality_ratio,
    )
    rotation_status = _rotation_status(
        age_seconds=age_seconds,
        quality_gap=quality_gap,
        config=config,
    )
    rotation_direction = _rotation_direction(
        share_delta=share_delta,
        minimum_rotation_share_delta_ratio=config.minimum_rotation_share_delta_ratio,
    )
    rotation_reason = _rotation_reason(
        share_delta=share_delta,
        minimum_rotation_share_delta_ratio=config.minimum_rotation_share_delta_ratio,
    )
    return StrategyCategorySignalStalenessRotationCategoryRow(
        category_id=category_id,
        first_observed_at=first_observation.observed_at,
        latest_observed_at=latest_observation.observed_at,
        latest_signal_generated_at=latest_observation.signal_generated_at,
        starting_signal_weight=first_observation.recommended_signal_weight,
        ending_signal_weight=latest_observation.recommended_signal_weight,
        signal_weight_delta=(
            latest_observation.recommended_signal_weight
            - first_observation.recommended_signal_weight
        ),
        starting_signal_share_ratio=starting_share,
        ending_signal_share_ratio=ending_share,
        signal_share_delta_ratio=share_delta,
        latest_signal_age_seconds=age_seconds,
        signal_quality_ratio=latest_observation.signal_quality_ratio,
        signal_quality_gap_ratio=quality_gap,
        rotation_direction=rotation_direction,
        rotation_status=rotation_status,
        reason_codes=_category_reason_codes(
            source_reason_codes,
            age_seconds=age_seconds,
            quality_gap=quality_gap,
            rotation_reason=rotation_reason,
            rotation_status=rotation_status,
            config=config,
        ),
    )


def _rotation_status(
    *,
    age_seconds: Decimal,
    quality_gap: Decimal,
    config: StrategyCategorySignalStalenessRotationDigestConfig,
) -> str:
    if age_seconds >= config.rotate_out_signal_age_seconds:
        return "rotate_out"
    if age_seconds > config.stale_signal_after_seconds or quality_gap < ZERO:
        return "watch"
    return "hold"


def _rotation_direction(
    *,
    share_delta: Decimal,
    minimum_rotation_share_delta_ratio: Decimal,
) -> str:
    if share_delta < ZERO:
        return "decrease"
    if share_delta > ZERO:
        return "increase"
    return "hold"


def _rotation_reason(
    *,
    share_delta: Decimal,
    minimum_rotation_share_delta_ratio: Decimal,
) -> str:
    if share_delta < -minimum_rotation_share_delta_ratio:
        return "decrease"
    if share_delta > minimum_rotation_share_delta_ratio:
        return "increase"
    return "hold"


def _category_reason_codes(
    source_reason_codes: tuple[str, ...],
    *,
    age_seconds: Decimal,
    quality_gap: Decimal,
    rotation_reason: str,
    rotation_status: str,
    config: StrategyCategorySignalStalenessRotationDigestConfig,
) -> tuple[str, ...]:
    reasons = set(source_reason_codes)
    if rotation_status == "rotate_out":
        reasons.add("category_signal_staleness_rotate_out")
    elif rotation_status == "watch":
        reasons.add("category_signal_staleness_watch")
    else:
        reasons.add("category_signal_staleness_hold")
    if rotation_reason == "decrease":
        reasons.add("category_rotation_decrease")
    elif rotation_reason == "increase":
        reasons.add("category_rotation_increase")
    else:
        reasons.add("category_rotation_stable")
    if age_seconds > config.stale_signal_after_seconds:
        reasons.add("stale_signal_age")
    else:
        reasons.add("fresh_signal_age")
    if quality_gap < ZERO:
        reasons.add("low_signal_quality")
    else:
        reasons.add("healthy_signal_quality")
    return tuple(sorted(reasons, key=_reason_sort_key))


def _digest_status(
    rows: tuple[StrategyCategorySignalStalenessRotationCategoryRow, ...],
) -> str:
    if any(row.rotation_status == "rotate_out" for row in rows):
        return "blocked"
    if any(row.rotation_status == "watch" for row in rows):
        return "watch"
    return "pass" if rows else "watch"


def _digest_reason_codes(
    rows: tuple[StrategyCategorySignalStalenessRotationCategoryRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    reasons: set[str] = set()
    rotation_detected = False
    for row in rows:
        rotation_detected = rotation_detected or row.rotation_direction != "hold"
        reasons.update(
            reason
            for reason in row.reason_codes
            if reason != "category_rotation_stable"
        )
    if rotation_detected:
        reasons.add("category_signal_rotation_detected")
    return tuple(sorted(reasons, key=_reason_sort_key))


def _normalize_observations(
    observations: Iterable[object],
) -> tuple[StrategyCategorySignalStalenessRotationObservation, ...]:
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
            raise ValueError("observations must not contain duplicate category_id/observed_at")
        seen.add(key)
    return normalized


def _coerce_observation(
    value: object,
) -> StrategyCategorySignalStalenessRotationObservation:
    if type(value) is StrategyCategorySignalStalenessRotationObservation:
        return value
    raise ValueError(
        "observations must contain StrategyCategorySignalStalenessRotationObservation",
    )


def _normalize_category_rows(
    rows: object,
) -> tuple[StrategyCategorySignalStalenessRotationCategoryRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("category_rows must contain category rows")
    try:
        items = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("category_rows must contain category rows") from exc
    for item in items:
        if type(item) is not StrategyCategorySignalStalenessRotationCategoryRow:
            raise ValueError("category_rows must contain category rows")
    return items


def _validate_category_row(
    row: StrategyCategorySignalStalenessRotationCategoryRow,
) -> None:
    if row.latest_observed_at < row.first_observed_at:
        raise ValueError("latest_observed_at must be >= first_observed_at")
    if row.signal_weight_delta != _normalize_decimal(
        "signal_weight_delta",
        row.ending_signal_weight - row.starting_signal_weight,
    ):
        raise ValueError("signal_weight_delta must match signal weights")
    if row.signal_share_delta_ratio != _normalize_decimal(
        "signal_share_delta_ratio",
        row.ending_signal_share_ratio - row.starting_signal_share_ratio,
    ):
        raise ValueError("signal_share_delta_ratio must match signal shares")
    if row.rotation_direction != _direction_from_delta(row.signal_share_delta_ratio):
        raise ValueError("rotation_direction must match signal_share_delta_ratio")
    if row.signal_quality_gap_ratio < ZERO and row.rotation_status == "hold":
        raise ValueError("rotation_status must reflect low signal quality")
    _validate_category_row_reason_codes(row)


def _validate_report(report: StrategyCategorySignalStalenessRotationDigestReport) -> None:
    rows = report.category_rows
    if report.category_count != _count(len(rows)):
        raise ValueError("category_count must match category_rows")
    if report.rotate_out_count != _status_count(rows, "rotate_out"):
        raise ValueError("rotate_out_count must match category_rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match category_rows")
    if report.hold_count != _status_count(rows, "hold"):
        raise ValueError("hold_count must match category_rows")
    if tuple(sorted(rows, key=_row_sort_key)) != rows:
        raise ValueError("category_rows must be sorted deterministically")
    if report.stale_category_count != _count(
        sum(1 for row in rows if "stale_signal_age" in row.reason_codes),
    ):
        raise ValueError("stale_category_count must match category_rows")
    if report.low_quality_category_count != _count(
        sum(1 for row in rows if row.signal_quality_gap_ratio < ZERO),
    ):
        raise ValueError("low_quality_category_count must match category_rows")
    if report.max_signal_age_seconds != _max_decimal(row.latest_signal_age_seconds for row in rows):
        raise ValueError("max_signal_age_seconds must match category_rows")
    if report.average_signal_age_seconds != _average_decimal(
        row.latest_signal_age_seconds for row in rows
    ):
        raise ValueError("average_signal_age_seconds must match category_rows")
    if report.status != _digest_status(rows):
        raise ValueError("status must match category_rows")
    if report.reason_codes != _digest_reason_codes(rows):
        raise ValueError("reason_codes must match category_rows")
    for row in rows:
        if row.latest_observed_at > report.generated_at:
            raise ValueError("latest_observed_at must be <= generated_at")
        if row.latest_signal_generated_at > report.generated_at:
            raise ValueError("latest_signal_generated_at must be <= generated_at")
        if row.latest_signal_age_seconds != _age_seconds(
            row.latest_signal_generated_at,
            report.generated_at,
        ):
            raise ValueError("latest_signal_age_seconds must match generated_at")


def _validate_category_row_reason_codes(
    row: StrategyCategorySignalStalenessRotationCategoryRow,
) -> None:
    expected_status_reason = {
        "rotate_out": "category_signal_staleness_rotate_out",
        "watch": "category_signal_staleness_watch",
        "hold": "category_signal_staleness_hold",
    }[row.rotation_status]
    status_reasons = {
        "category_signal_staleness_rotate_out",
        "category_signal_staleness_watch",
        "category_signal_staleness_hold",
    }
    if expected_status_reason not in row.reason_codes:
        raise ValueError("reason_codes must match rotation_status")
    if len(status_reasons.intersection(row.reason_codes)) != 1:
        raise ValueError("reason_codes must contain one rotation status reason")

    quality_reason = (
        "low_signal_quality"
        if row.signal_quality_gap_ratio < ZERO
        else "healthy_signal_quality"
    )
    if quality_reason not in row.reason_codes:
        raise ValueError("reason_codes must match signal_quality_gap_ratio")
    if {"low_signal_quality", "healthy_signal_quality"}.issubset(row.reason_codes):
        raise ValueError("reason_codes must contain one signal quality reason")

    if not (
        {"stale_signal_age", "fresh_signal_age"}.intersection(row.reason_codes)
    ):
        raise ValueError("reason_codes must contain a signal age reason")
    if {"stale_signal_age", "fresh_signal_age"}.issubset(row.reason_codes):
        raise ValueError("reason_codes must contain one signal age reason")

    direction_reason = {
        "decrease": "category_rotation_decrease",
        "increase": "category_rotation_increase",
        "hold": "category_rotation_stable",
    }[row.rotation_direction]
    direction_reasons = {
        "category_rotation_decrease",
        "category_rotation_increase",
        "category_rotation_stable",
    }
    if row.rotation_direction == "hold" and direction_reason not in row.reason_codes:
        raise ValueError("reason_codes must match rotation_direction")
    if len(direction_reasons.intersection(row.reason_codes)) != 1:
        raise ValueError("reason_codes must contain one rotation direction reason")


def _direction_from_delta(value: Decimal) -> str:
    if value < ZERO:
        return "decrease"
    if value > ZERO:
        return "increase"
    return "hold"


def _row_sort_key(row: StrategyCategorySignalStalenessRotationCategoryRow) -> tuple[object, ...]:
    return (
        ROW_STATUS_WEIGHT[row.rotation_status],
        -row.latest_signal_age_seconds,
        row.category_id,
    )


def _reason_sort_key(reason_code: str) -> tuple[int, str]:
    try:
        return REPORT_REASON_SEQUENCE.index(reason_code), reason_code
    except ValueError:
        return len(REPORT_REASON_SEQUENCE), reason_code


def _age_seconds(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    seconds += (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    return _normalize_nonnegative_decimal("latest_signal_age_seconds", seconds)


def _status_count(
    rows: tuple[StrategyCategorySignalStalenessRotationCategoryRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.rotation_status == status))


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return max(items).quantize(QUANTUM)


def _average_decimal(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return (sum(items, ZERO) / _count(len(items))).quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return (numerator / denominator).quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    return sum(values, ZERO).quantize(QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain reason code strings")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must contain reason code strings") from exc
    normalized: list[str] = []
    seen: set[str] = set()
    for item in items:
        _require_canonical_string(field_name, item)
        assert isinstance(item, str)
        if item in seen:
            continue
        normalized.append(item)
        seen.add(item)
    return tuple(sorted(normalized, key=_reason_sort_key))


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
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
    return value.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _require_public_text(field_name, value)


def _require_public_text(field_name: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public text")
    if any(fragment in normalized for fragment in SENSITIVE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains sensitive public text")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _reject_payload_values(label: str, value: object, path: str = "") -> None:
    if value is None or type(value) is bool:
        return
    if type(value) in (int, float):
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            field_path = field.name if not path else f"{path}.{field.name}"
            _reject_payload_values(label, getattr(value, field.name), field_path)
        return
    if type(value) is str:
        _require_public_text(path or label, value)
        return
    if isinstance(value, tuple):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_payload_values(label, item, item_path)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_payload_values(label, item, item_path)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _require_public_text("JSON object key", key)
            item_path = key if not path else f"{path}.{key}"
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_payload_values(label, item, item_path)
        return
    raise ValueError(f"{path or label} is not JSON serializable")


def _json_ready(value: Any) -> Any:
    if value is None or type(value) is bool:
        return value
    if isinstance(value, Decimal):
        return _decimal_string(value)
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _require_public_text("JSON object key", key)
            ready[key] = _json_ready(item)
        return ready
    if type(value) is str:
        _require_public_text("JSON string value", value)
        return value
    if type(value) in (int, float):
        raise ValueError("JSON value must use Decimal-derived string values")
    return value


def _decimal_string(value: Decimal) -> str:
    if value == value.to_integral_value() and value.as_tuple().exponent >= 0:
        return str(value.quantize(COUNT_QUANTUM))
    return format(value.quantize(QUANTUM), "f")
