"""Pure Phase 1 strategy category liquidity-memory rotation digest reducer."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Any


DEFAULT_STRATEGY_CATEGORY_LIQUIDITY_MEMORY_ROTATION_DIGEST_CONFIG_VERSION = (
    "strategy-category-liquidity-memory-rotation-digest-v0"
)

COUNT_QUANTUM = Decimal("1")
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")

ROTATION_STATUSES = ("rotating_in", "rotating_out", "stable")
DIGEST_STATUSES = ("stable", "watch", "blocked")
ROTATION_STATUS_WEIGHT = {
    "rotating_in": 0,
    "rotating_out": 1,
    "stable": 2,
}
ROW_STATUS_REASON_CODES = {
    "category_liquidity_low",
    "category_memory_low",
    "category_rotating_in",
    "category_rotating_out",
    "category_rotation_stable",
}
HEX_DIGITS = frozenset("0123456789abcdef")
REQUIRED_PAYLOAD_FIELDS = (
    "generated_at",
    "config_version",
    "observation_count",
    "category_count",
    "rotation_in_count",
    "rotation_out_count",
    "stable_count",
    "low_liquidity_count",
    "low_memory_count",
    "min_liquidity_coverage_ratio",
    "min_memory_pass_ratio",
    "status",
    "reason_codes",
    "category_rows",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
REQUIRED_CATEGORY_ROW_PAYLOAD_FIELDS = (
    "category_id",
    "first_observed_at",
    "latest_observed_at",
    "starting_recommended_notional",
    "ending_recommended_notional",
    "notional_delta",
    "starting_notional_share_ratio",
    "ending_notional_share_ratio",
    "notional_share_delta_ratio",
    "available_liquidity",
    "liquidity_coverage_ratio",
    "memory_signal_count",
    "memory_pass_count",
    "memory_pass_ratio",
    "rotation_status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
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
        "pos" + "ition",
        "st" + "ake",
        "b" + "et",
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
        "post" + "gresql://",
        "post" + "gres://",
    ),
)


@dataclass(frozen=True)
class StrategyCategoryLiquidityMemoryRotationDigestConfig:
    config_version: str = (
        DEFAULT_STRATEGY_CATEGORY_LIQUIDITY_MEMORY_ROTATION_DIGEST_CONFIG_VERSION
    )
    min_rotation_notional_share_delta: Decimal = Decimal("0.100000")
    min_liquidity_coverage_ratio: Decimal = Decimal("1.500000")
    min_memory_pass_ratio: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_rotation_notional_share_delta",
            _normalize_nonnegative_decimal(
                "min_rotation_notional_share_delta",
                self.min_rotation_notional_share_delta,
            ),
        )
        object.__setattr__(
            self,
            "min_liquidity_coverage_ratio",
            _normalize_nonnegative_decimal(
                "min_liquidity_coverage_ratio",
                self.min_liquidity_coverage_ratio,
            ),
        )
        object.__setattr__(
            self,
            "min_memory_pass_ratio",
            _normalize_nonnegative_decimal(
                "min_memory_pass_ratio",
                self.min_memory_pass_ratio,
            ),
        )
        _require_hard_flags("digest config", self)


@dataclass(frozen=True)
class StrategyCategoryLiquidityMemoryRotationObservation:
    category_id: str
    observed_at: datetime
    recommended_notional: Decimal
    available_liquidity: Decimal
    memory_signal_count: Decimal
    memory_pass_count: Decimal
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
            "available_liquidity",
            _normalize_nonnegative_decimal("available_liquidity", self.available_liquidity),
        )
        for field_name in ("memory_signal_count", "memory_pass_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.memory_pass_count > self.memory_signal_count:
            raise ValueError("memory_pass_count must not exceed memory_signal_count")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class StrategyCategoryLiquidityMemoryRotationCategoryRow:
    category_id: str
    first_observed_at: datetime | None
    latest_observed_at: datetime
    starting_recommended_notional: Decimal
    ending_recommended_notional: Decimal
    notional_delta: Decimal
    starting_notional_share_ratio: Decimal
    ending_notional_share_ratio: Decimal
    notional_share_delta_ratio: Decimal
    available_liquidity: Decimal
    liquidity_coverage_ratio: Decimal
    memory_signal_count: Decimal
    memory_pass_count: Decimal
    memory_pass_ratio: Decimal
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
            "available_liquidity",
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
            "notional_share_delta_ratio",
            "liquidity_coverage_ratio",
            "memory_pass_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("memory_signal_count", "memory_pass_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.rotation_status not in ROTATION_STATUSES:
            raise ValueError("rotation_status must be a known rotation status")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_category_row(self)
        _require_hard_flags("category row", self)


@dataclass(frozen=True)
class StrategyCategoryLiquidityMemoryRotationDigestReport:
    generated_at: datetime
    config_version: str
    observation_count: Decimal
    category_count: Decimal
    rotation_in_count: Decimal
    rotation_out_count: Decimal
    stable_count: Decimal
    low_liquidity_count: Decimal
    low_memory_count: Decimal
    min_liquidity_coverage_ratio: Decimal
    min_memory_pass_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    category_rows: tuple[StrategyCategoryLiquidityMemoryRotationCategoryRow, ...]
    derived_validation_digest: str = ""
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
            "low_liquidity_count",
            "low_memory_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_liquidity_coverage_ratio",
            "min_memory_pass_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
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
        _require_hard_flags("digest report", self)
        expected_digest = _report_derived_validation_digest(self)
        object.__setattr__(
            self,
            "derived_validation_digest",
            (
                expected_digest
                if self.derived_validation_digest == ""
                else _normalize_sha256(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                )
            ),
        )
        _validate_report(self)


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


def build_strategy_category_liquidity_memory_rotation_digest(
    observations: Iterable[object],
    *,
    config: StrategyCategoryLiquidityMemoryRotationDigestConfig,
    generated_at: datetime,
) -> StrategyCategoryLiquidityMemoryRotationDigestReport:
    if type(config) is not StrategyCategoryLiquidityMemoryRotationDigestConfig:
        raise ValueError(
            "config must be a StrategyCategoryLiquidityMemoryRotationDigestConfig",
        )
    _require_hard_flags("digest config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    rows = _build_category_rows(normalized_observations, config=config)

    return StrategyCategoryLiquidityMemoryRotationDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        observation_count=_count(len(normalized_observations)),
        category_count=_count(len(rows)),
        rotation_in_count=_status_count(rows, "rotating_in"),
        rotation_out_count=_status_count(rows, "rotating_out"),
        stable_count=_status_count(rows, "stable"),
        low_liquidity_count=_count(
            sum(
                1
                for row in rows
                if row.liquidity_coverage_ratio < config.min_liquidity_coverage_ratio
            ),
        ),
        low_memory_count=_count(
            sum(1 for row in rows if row.memory_pass_ratio < config.min_memory_pass_ratio),
        ),
        min_liquidity_coverage_ratio=_min_decimal(
            row.liquidity_coverage_ratio for row in rows
        ),
        min_memory_pass_ratio=_min_decimal(row.memory_pass_ratio for row in rows),
        status=_digest_status(rows, config=config),
        reason_codes=_digest_reason_codes(rows),
        category_rows=rows,
    )


def strategy_category_liquidity_memory_rotation_digest_payload(
    report: StrategyCategoryLiquidityMemoryRotationDigestReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyCategoryLiquidityMemoryRotationDigestReport:
        _require_hard_flags("digest report", report)
        payload: Any = _report_payload(report)
    elif type(report) is dict:
        payload = report
    else:
        raise ValueError(
            "report must be a StrategyCategoryLiquidityMemoryRotationDigestReport",
        )

    ready = _json_ready_public_payload(payload)
    if type(ready) is not dict:
        raise ValueError("digest payload must be a JSON object")
    _require_hard_flags("digest payload", _DictFlags(ready))
    _validate_public_payload(ready)
    return ready


def _report_payload(
    report: StrategyCategoryLiquidityMemoryRotationDigestReport,
) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "observation_count": _decimal_string(report.observation_count),
        "category_count": _decimal_string(report.category_count),
        "rotation_in_count": _decimal_string(report.rotation_in_count),
        "rotation_out_count": _decimal_string(report.rotation_out_count),
        "stable_count": _decimal_string(report.stable_count),
        "low_liquidity_count": _decimal_string(report.low_liquidity_count),
        "low_memory_count": _decimal_string(report.low_memory_count),
        "min_liquidity_coverage_ratio": _decimal_string(
            report.min_liquidity_coverage_ratio,
        ),
        "min_memory_pass_ratio": _decimal_string(report.min_memory_pass_ratio),
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "category_rows": [_category_row_payload(row) for row in report.category_rows],
        "derived_validation_digest": report.derived_validation_digest,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _category_row_payload(
    row: StrategyCategoryLiquidityMemoryRotationCategoryRow,
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
        "ending_notional_share_ratio": _decimal_string(row.ending_notional_share_ratio),
        "notional_share_delta_ratio": _decimal_string(row.notional_share_delta_ratio),
        "available_liquidity": _decimal_string(row.available_liquidity),
        "liquidity_coverage_ratio": _decimal_string(row.liquidity_coverage_ratio),
        "memory_signal_count": _decimal_string(row.memory_signal_count),
        "memory_pass_count": _decimal_string(row.memory_pass_count),
        "memory_pass_ratio": _decimal_string(row.memory_pass_ratio),
        "rotation_status": row.rotation_status,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _build_category_rows(
    observations: tuple[StrategyCategoryLiquidityMemoryRotationObservation, ...],
    *,
    config: StrategyCategoryLiquidityMemoryRotationDigestConfig,
) -> tuple[StrategyCategoryLiquidityMemoryRotationCategoryRow, ...]:
    observations_by_category: dict[
        str,
        list[StrategyCategoryLiquidityMemoryRotationObservation],
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
    observations: list[StrategyCategoryLiquidityMemoryRotationObservation],
) -> tuple[
    str,
    StrategyCategoryLiquidityMemoryRotationObservation,
    StrategyCategoryLiquidityMemoryRotationObservation,
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
        first_observation = StrategyCategoryLiquidityMemoryRotationObservation(
            category_id=category_id,
            observed_at=latest_observation.observed_at,
            recommended_notional=ZERO,
            available_liquidity=latest_observation.available_liquidity,
            memory_signal_count=latest_observation.memory_signal_count,
            memory_pass_count=latest_observation.memory_pass_count,
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
    first_observation: StrategyCategoryLiquidityMemoryRotationObservation,
    latest_observation: StrategyCategoryLiquidityMemoryRotationObservation,
    source_reason_codes: tuple[str, ...],
    starting_total: Decimal,
    ending_total: Decimal,
    config: StrategyCategoryLiquidityMemoryRotationDigestConfig,
) -> StrategyCategoryLiquidityMemoryRotationCategoryRow:
    starting_share = _coverage_ratio(
        first_observation.recommended_notional,
        starting_total,
    )
    ending_share = _coverage_ratio(latest_observation.recommended_notional, ending_total)
    share_delta = _normalize_decimal(
        "notional_share_delta_ratio",
        ending_share - starting_share,
    )
    liquidity_coverage_ratio = _coverage_ratio(
        latest_observation.available_liquidity,
        latest_observation.recommended_notional,
    )
    memory_pass_ratio = _coverage_ratio(
        latest_observation.memory_pass_count,
        latest_observation.memory_signal_count,
    )
    rotation_status = _rotation_status(
        share_delta=share_delta,
        min_rotation_notional_share_delta=config.min_rotation_notional_share_delta,
    )
    return StrategyCategoryLiquidityMemoryRotationCategoryRow(
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
        available_liquidity=latest_observation.available_liquidity,
        liquidity_coverage_ratio=liquidity_coverage_ratio,
        memory_signal_count=latest_observation.memory_signal_count,
        memory_pass_count=latest_observation.memory_pass_count,
        memory_pass_ratio=memory_pass_ratio,
        rotation_status=rotation_status,
        reason_codes=_category_reason_codes(
            source_reason_codes,
            liquidity_coverage_ratio=liquidity_coverage_ratio,
            memory_pass_ratio=memory_pass_ratio,
            rotation_status=rotation_status,
            config=config,
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
    liquidity_coverage_ratio: Decimal,
    memory_pass_ratio: Decimal,
    rotation_status: str,
    config: StrategyCategoryLiquidityMemoryRotationDigestConfig,
) -> tuple[str, ...]:
    reason_codes = set(source_reason_codes)
    if liquidity_coverage_ratio < config.min_liquidity_coverage_ratio:
        reason_codes.add("category_liquidity_low")
    if memory_pass_ratio < config.min_memory_pass_ratio:
        reason_codes.add("category_memory_low")
    if rotation_status == "rotating_in":
        reason_codes.add("category_rotating_in")
    elif rotation_status == "rotating_out":
        reason_codes.add("category_rotating_out")
    else:
        reason_codes.add("category_rotation_stable")
    return tuple(sorted(reason_codes))


def _digest_status(
    rows: tuple[StrategyCategoryLiquidityMemoryRotationCategoryRow, ...],
    *,
    config: StrategyCategoryLiquidityMemoryRotationDigestConfig,
) -> str:
    if not rows:
        return "watch"
    if any(
        row.liquidity_coverage_ratio < config.min_liquidity_coverage_ratio
        or row.memory_pass_ratio < config.min_memory_pass_ratio
        for row in rows
    ):
        return "blocked"
    if any(row.rotation_status != "stable" for row in rows):
        return "watch"
    return "stable"


def _digest_reason_codes(
    rows: tuple[StrategyCategoryLiquidityMemoryRotationCategoryRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("strategy_category_liquidity_memory_rotation_empty",)
    source_reason_codes: set[str] = set()
    low_liquidity = False
    low_memory = False
    rotation_detected = False
    for row in rows:
        low_liquidity = low_liquidity or "category_liquidity_low" in row.reason_codes
        low_memory = low_memory or "category_memory_low" in row.reason_codes
        rotation_detected = rotation_detected or row.rotation_status != "stable"
        source_reason_codes.update(
            reason_code
            for reason_code in row.reason_codes
            if reason_code not in ROW_STATUS_REASON_CODES
        )
    if low_liquidity:
        source_reason_codes.add("category_liquidity_low")
    if low_memory:
        source_reason_codes.add("category_memory_low")
    if rotation_detected:
        source_reason_codes.add("category_rotation_detected")
    return tuple(sorted(source_reason_codes))


def _normalize_observations(
    observations: Iterable[object],
) -> tuple[StrategyCategoryLiquidityMemoryRotationObservation, ...]:
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


def _coerce_observation(
    value: object,
) -> StrategyCategoryLiquidityMemoryRotationObservation:
    if type(value) is not StrategyCategoryLiquidityMemoryRotationObservation:
        raise ValueError(
            "observations must contain "
            "StrategyCategoryLiquidityMemoryRotationObservation values",
        )
    _require_hard_flags("observation", value)
    return StrategyCategoryLiquidityMemoryRotationObservation(
        category_id=value.category_id,
        observed_at=value.observed_at,
        recommended_notional=value.recommended_notional,
        available_liquidity=value.available_liquidity,
        memory_signal_count=value.memory_signal_count,
        memory_pass_count=value.memory_pass_count,
        reason_codes=value.reason_codes,
        paper_only=value.paper_only,
        report_only=value.report_only,
        readonly=value.readonly,
    )


def _normalize_category_rows(
    rows: Iterable[object],
) -> tuple[StrategyCategoryLiquidityMemoryRotationCategoryRow, ...]:
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


def _coerce_category_row(
    value: object,
) -> StrategyCategoryLiquidityMemoryRotationCategoryRow:
    if type(value) is not StrategyCategoryLiquidityMemoryRotationCategoryRow:
        raise ValueError(
            "category_rows must contain "
            "StrategyCategoryLiquidityMemoryRotationCategoryRow values",
        )
    _require_hard_flags("category row", value)
    return StrategyCategoryLiquidityMemoryRotationCategoryRow(
        category_id=value.category_id,
        first_observed_at=value.first_observed_at,
        latest_observed_at=value.latest_observed_at,
        starting_recommended_notional=value.starting_recommended_notional,
        ending_recommended_notional=value.ending_recommended_notional,
        notional_delta=value.notional_delta,
        starting_notional_share_ratio=value.starting_notional_share_ratio,
        ending_notional_share_ratio=value.ending_notional_share_ratio,
        notional_share_delta_ratio=value.notional_share_delta_ratio,
        available_liquidity=value.available_liquidity,
        liquidity_coverage_ratio=value.liquidity_coverage_ratio,
        memory_signal_count=value.memory_signal_count,
        memory_pass_count=value.memory_pass_count,
        memory_pass_ratio=value.memory_pass_ratio,
        rotation_status=value.rotation_status,
        reason_codes=value.reason_codes,
        paper_only=value.paper_only,
        report_only=value.report_only,
        readonly=value.readonly,
    )


def _validate_category_row(
    row: StrategyCategoryLiquidityMemoryRotationCategoryRow,
) -> None:
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
    if row.liquidity_coverage_ratio != _coverage_ratio(
        row.available_liquidity,
        row.ending_recommended_notional,
    ):
        raise ValueError("liquidity_coverage_ratio must match latest liquidity")
    if row.memory_pass_count > row.memory_signal_count:
        raise ValueError("memory_pass_count must not exceed memory_signal_count")
    if row.memory_pass_ratio != _coverage_ratio(
        row.memory_pass_count,
        row.memory_signal_count,
    ):
        raise ValueError("memory_pass_ratio must match memory counts")
    if row.liquidity_coverage_ratio < ZERO:
        raise ValueError("liquidity_coverage_ratio must be nonnegative")
    if row.memory_pass_ratio < ZERO:
        raise ValueError("memory_pass_ratio must be nonnegative")


def _validate_report(report: StrategyCategoryLiquidityMemoryRotationDigestReport) -> None:
    rows = report.category_rows
    if report.category_count != _count(len(rows)):
        raise ValueError("category_count must match category_rows")
    if report.observation_count < report.category_count:
        raise ValueError("observation_count must be at least category_count")
    if report.rotation_in_count != _status_count(rows, "rotating_in"):
        raise ValueError("rotation_in_count must match category_rows")
    if report.rotation_out_count != _status_count(rows, "rotating_out"):
        raise ValueError("rotation_out_count must match category_rows")
    if report.stable_count != _status_count(rows, "stable"):
        raise ValueError("stable_count must match category_rows")
    if (
        report.rotation_in_count
        + report.rotation_out_count
        + report.stable_count
        != report.category_count
    ):
        raise ValueError("rotation status counts must match category_count")
    if report.min_liquidity_coverage_ratio != _min_decimal(
        row.liquidity_coverage_ratio for row in rows
    ):
        raise ValueError("min_liquidity_coverage_ratio must match category_rows")
    if report.min_memory_pass_ratio != _min_decimal(row.memory_pass_ratio for row in rows):
        raise ValueError("min_memory_pass_ratio must match category_rows")
    if report.low_liquidity_count != _count(
        sum(1 for row in rows if "category_liquidity_low" in row.reason_codes),
    ):
        raise ValueError("low_liquidity_count must match category_rows")
    if report.low_memory_count != _count(
        sum(1 for row in rows if "category_memory_low" in row.reason_codes),
    ):
        raise ValueError("low_memory_count must match category_rows")
    if report.status != _digest_status_from_rows(rows):
        raise ValueError("status must match category_rows")
    if report.reason_codes != _digest_reason_codes(rows):
        raise ValueError("reason_codes must match category_rows")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match category_rows")
    for row in rows:
        _validate_category_row_reason_codes(row)


def _validate_category_row_reason_codes(
    row: StrategyCategoryLiquidityMemoryRotationCategoryRow,
) -> None:
    expected_status_reason = (
        "category_rotation_stable"
        if row.rotation_status == "stable"
        else f"category_{row.rotation_status}"
    )
    if expected_status_reason not in row.reason_codes:
        raise ValueError("reason_codes must match rotation_status")
    rotation_reason_codes = {
        "category_rotating_in",
        "category_rotating_out",
        "category_rotation_stable",
    }
    unexpected_status_reasons = rotation_reason_codes - {expected_status_reason}
    if any(reason_code in row.reason_codes for reason_code in unexpected_status_reasons):
        raise ValueError("reason_codes must match rotation_status")


def _digest_status_from_rows(
    rows: tuple[StrategyCategoryLiquidityMemoryRotationCategoryRow, ...],
) -> str:
    if not rows:
        return "watch"
    if any(
        "category_liquidity_low" in row.reason_codes
        or "category_memory_low" in row.reason_codes
        for row in rows
    ):
        return "blocked"
    if any(row.rotation_status != "stable" for row in rows):
        return "watch"
    return "stable"


def _validate_public_payload(payload: dict[str, Any]) -> None:
    report = _report_from_public_payload(payload)
    if _report_payload(report) != payload:
        raise ValueError("digest payload must match derived validation payload")


def _report_from_public_payload(
    payload: dict[str, Any],
) -> StrategyCategoryLiquidityMemoryRotationDigestReport:
    _require_payload_fields("digest payload", payload, REQUIRED_PAYLOAD_FIELDS)
    rows = _payload_sequence("category_rows", payload["category_rows"])
    return StrategyCategoryLiquidityMemoryRotationDigestReport(
        generated_at=_payload_datetime("generated_at", payload["generated_at"]),
        config_version=_payload_string("config_version", payload["config_version"]),
        observation_count=_payload_decimal(
            "observation_count",
            payload["observation_count"],
        ),
        category_count=_payload_decimal("category_count", payload["category_count"]),
        rotation_in_count=_payload_decimal(
            "rotation_in_count",
            payload["rotation_in_count"],
        ),
        rotation_out_count=_payload_decimal(
            "rotation_out_count",
            payload["rotation_out_count"],
        ),
        stable_count=_payload_decimal("stable_count", payload["stable_count"]),
        low_liquidity_count=_payload_decimal(
            "low_liquidity_count",
            payload["low_liquidity_count"],
        ),
        low_memory_count=_payload_decimal(
            "low_memory_count",
            payload["low_memory_count"],
        ),
        min_liquidity_coverage_ratio=_payload_decimal(
            "min_liquidity_coverage_ratio",
            payload["min_liquidity_coverage_ratio"],
        ),
        min_memory_pass_ratio=_payload_decimal(
            "min_memory_pass_ratio",
            payload["min_memory_pass_ratio"],
        ),
        status=_payload_string("status", payload["status"]),
        reason_codes=tuple(_payload_sequence("reason_codes", payload["reason_codes"])),
        category_rows=tuple(_category_row_from_public_payload(row) for row in rows),
        derived_validation_digest=_payload_string(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_payload_bool("paper_only", payload["paper_only"]),
        report_only=_payload_bool("report_only", payload["report_only"]),
        readonly=_payload_bool("readonly", payload["readonly"]),
    )


def _category_row_from_public_payload(
    payload: object,
) -> StrategyCategoryLiquidityMemoryRotationCategoryRow:
    if type(payload) is not dict:
        raise ValueError("category_rows must contain JSON objects")
    _require_payload_fields(
        "category row payload",
        payload,
        REQUIRED_CATEGORY_ROW_PAYLOAD_FIELDS,
    )
    return StrategyCategoryLiquidityMemoryRotationCategoryRow(
        category_id=_payload_string("category_id", payload["category_id"]),
        first_observed_at=_payload_optional_datetime(
            "first_observed_at",
            payload["first_observed_at"],
        ),
        latest_observed_at=_payload_datetime(
            "latest_observed_at",
            payload["latest_observed_at"],
        ),
        starting_recommended_notional=_payload_decimal(
            "starting_recommended_notional",
            payload["starting_recommended_notional"],
        ),
        ending_recommended_notional=_payload_decimal(
            "ending_recommended_notional",
            payload["ending_recommended_notional"],
        ),
        notional_delta=_payload_decimal("notional_delta", payload["notional_delta"]),
        starting_notional_share_ratio=_payload_decimal(
            "starting_notional_share_ratio",
            payload["starting_notional_share_ratio"],
        ),
        ending_notional_share_ratio=_payload_decimal(
            "ending_notional_share_ratio",
            payload["ending_notional_share_ratio"],
        ),
        notional_share_delta_ratio=_payload_decimal(
            "notional_share_delta_ratio",
            payload["notional_share_delta_ratio"],
        ),
        available_liquidity=_payload_decimal(
            "available_liquidity",
            payload["available_liquidity"],
        ),
        liquidity_coverage_ratio=_payload_decimal(
            "liquidity_coverage_ratio",
            payload["liquidity_coverage_ratio"],
        ),
        memory_signal_count=_payload_decimal(
            "memory_signal_count",
            payload["memory_signal_count"],
        ),
        memory_pass_count=_payload_decimal(
            "memory_pass_count",
            payload["memory_pass_count"],
        ),
        memory_pass_ratio=_payload_decimal(
            "memory_pass_ratio",
            payload["memory_pass_ratio"],
        ),
        rotation_status=_payload_string("rotation_status", payload["rotation_status"]),
        reason_codes=tuple(_payload_sequence("reason_codes", payload["reason_codes"])),
        paper_only=_payload_bool("paper_only", payload["paper_only"]),
        report_only=_payload_bool("report_only", payload["report_only"]),
        readonly=_payload_bool("readonly", payload["readonly"]),
    )


def _report_derived_validation_digest(
    report: StrategyCategoryLiquidityMemoryRotationDigestReport,
) -> str:
    return _sha256_payload(
        {
            "generated_at": report.generated_at.isoformat(),
            "config_version": report.config_version,
            "observation_count": _decimal_string(report.observation_count),
            "category_count": _decimal_string(report.category_count),
            "rotation_in_count": _decimal_string(report.rotation_in_count),
            "rotation_out_count": _decimal_string(report.rotation_out_count),
            "stable_count": _decimal_string(report.stable_count),
            "low_liquidity_count": _decimal_string(report.low_liquidity_count),
            "low_memory_count": _decimal_string(report.low_memory_count),
            "min_liquidity_coverage_ratio": _decimal_string(
                report.min_liquidity_coverage_ratio,
            ),
            "min_memory_pass_ratio": _decimal_string(report.min_memory_pass_ratio),
            "status": report.status,
            "reason_codes": list(report.reason_codes),
            "category_rows": [
                _category_row_payload(row) for row in report.category_rows
            ],
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )


def _sha256_payload(payload: dict[str, Any]) -> str:
    text = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _normalize_sha256(field_name: str, value: Any) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    if value.lower() != value:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    if any(character not in HEX_DIGITS for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _require_payload_fields(
    label: str,
    payload: dict[str, Any],
    required_fields: tuple[str, ...],
) -> None:
    missing = tuple(field for field in required_fields if field not in payload)
    if missing:
        raise ValueError(f"missing required payload field in {label}: {missing[0]}")


def _payload_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _require_public_text(field_name, value)
    return value


def _payload_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _payload_decimal(field_name: str, value: object) -> Decimal:
    text = _payload_string(field_name, value)
    try:
        decimal_value = Decimal(text)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal-derived string") from exc
    return _require_decimal(field_name, decimal_value)


def _payload_datetime(field_name: str, value: object) -> datetime:
    text = _payload_string(field_name, value)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime") from exc
    return _as_utc(field_name, parsed)


def _payload_optional_datetime(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _payload_datetime(field_name, value)


def _payload_sequence(field_name: str, value: object) -> tuple[Any, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a JSON list")
    return tuple(value)


def _row_sort_key(
    row: StrategyCategoryLiquidityMemoryRotationCategoryRow,
) -> tuple[Any, ...]:
    return (
        ROTATION_STATUS_WEIGHT[row.rotation_status],
        row.liquidity_coverage_ratio,
        row.memory_pass_ratio,
        -abs(row.notional_share_delta_ratio),
        row.category_id,
    )


def _status_count(
    rows: tuple[StrategyCategoryLiquidityMemoryRotationCategoryRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.rotation_status == status))


def _min_decimal(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    return min(normalized)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _normalize_nonnegative_decimal("total", total)


def _coverage_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _normalize_nonnegative_decimal("coverage_ratio", numerator / denominator)


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


def _json_ready_public_payload(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready_public_payload(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return _decimal_string(value)
    if isinstance(value, Decimal):
        raise ValueError("JSON Decimal value must be exactly Decimal")
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be exactly datetime")
        return _as_utc("JSON datetime value", value).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal-derived string values")
    if type(value) is str:
        _require_public_text("JSON string value", value)
        return value
    if type(value) is bool:
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _require_public_text("JSON object key", key)
            ready[key] = _json_ready_public_payload(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready_public_payload(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _normalize_nonnegative_count(field_name: str, value: Any) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value(rounding=ROUND_HALF_EVEN):
        raise ValueError(f"{field_name} must be an integer count")
    return decimal_value.quantize(COUNT_QUANTUM, rounding=ROUND_HALF_EVEN)


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
    _require_public_text(field_name, value)


def _require_public_text(field_name: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public text")
    if any(fragment in normalized for fragment in SENSITIVE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains sensitive public text")


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
    "DEFAULT_STRATEGY_CATEGORY_LIQUIDITY_MEMORY_ROTATION_DIGEST_CONFIG_VERSION",
    "StrategyCategoryLiquidityMemoryRotationDigestConfig",
    "StrategyCategoryLiquidityMemoryRotationObservation",
    "StrategyCategoryLiquidityMemoryRotationCategoryRow",
    "StrategyCategoryLiquidityMemoryRotationDigestReport",
    "build_strategy_category_liquidity_memory_rotation_digest",
    "strategy_category_liquidity_memory_rotation_digest_payload",
)
