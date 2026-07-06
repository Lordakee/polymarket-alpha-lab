"""Pure paper report reducer for candidate evidence freshness matrices."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal


DEFAULT_STRATEGY_CANDIDATE_EVIDENCE_FRESHNESS_MATRIX_V10_CONFIG_VERSION = (
    "strategy-candidate-evidence-freshness-matrix-v10"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

MATRIX_STATUSES = ("fresh", "watch", "stale")
ROW_STATUSES = ("fresh", "watch", "stale")
CONFIRMATION_ROLES = ("primary", "confirming", "context")

_BASE_FRESH_LIMIT_MINUTES = Decimal("60.000000")
_BASE_STALE_LIMIT_MINUTES = Decimal("180.000000")
_TIME_PRESSURE_ACTIVATION = Decimal("0.500000")
_TIME_PRESSURE_DISCOUNT = Decimal("0.500000")
_TIME_PRESSURE_FLOOR = Decimal("0.500000")
_HIGH_TIME_SENSITIVITY = Decimal("0.750000")
_HIGH_RESOLUTION_URGENCY_MINUTES = Decimal("120.000000")
_HIGH_RELIABILITY = Decimal("0.750000")
_MEDIUM_RELIABILITY = Decimal("0.500000")

_STATUS_SORT = {
    "stale": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "fresh": Decimal("2.000000"),
}

_REASON_PRIORITY = (
    "evidence_age_stale",
    "source_reliability_low",
    "confirmation_role_context",
    "time_sensitivity_high",
    "resolution_urgency_high",
    "evidence_age_watch",
    "source_reliability_high",
    "source_reliability_medium",
    "confirmation_role_confirming",
    "confirmation_role_primary",
    "row_status_stale",
    "row_status_watch",
    "row_status_fresh",
    "freshness_matrix_empty",
    "matrix_status_stale",
    "matrix_status_watch",
    "matrix_status_fresh",
)

__all__ = (
    "CONFIRMATION_ROLES",
    "DEFAULT_STRATEGY_CANDIDATE_EVIDENCE_FRESHNESS_MATRIX_V10_CONFIG_VERSION",
    "MATRIX_STATUSES",
    "ROW_STATUSES",
    "StrategyCandidateEvidenceFreshnessMatrixV10Config",
    "StrategyCandidateEvidenceFreshnessMatrixV10Input",
    "StrategyCandidateEvidenceFreshnessMatrixV10Result",
    "StrategyCandidateEvidenceFreshnessMatrixV10Row",
    "build_strategy_candidate_evidence_freshness_matrix_v10",
    "strategy_candidate_evidence_freshness_matrix_v10_payload",
)


@dataclass(frozen=True)
class StrategyCandidateEvidenceFreshnessMatrixV10Config:
    config_version: str = (
        DEFAULT_STRATEGY_CANDIDATE_EVIDENCE_FRESHNESS_MATRIX_V10_CONFIG_VERSION
    )
    base_fresh_limit_minutes: Decimal = _BASE_FRESH_LIMIT_MINUTES
    base_stale_limit_minutes: Decimal = _BASE_STALE_LIMIT_MINUTES
    time_pressure_activation: Decimal = _TIME_PRESSURE_ACTIVATION
    time_pressure_discount: Decimal = _TIME_PRESSURE_DISCOUNT
    time_pressure_floor: Decimal = _TIME_PRESSURE_FLOOR
    high_time_sensitivity_threshold: Decimal = _HIGH_TIME_SENSITIVITY
    high_resolution_urgency_minutes: Decimal = _HIGH_RESOLUTION_URGENCY_MINUTES
    high_reliability_threshold: Decimal = _HIGH_RELIABILITY
    medium_reliability_threshold: Decimal = _MEDIUM_RELIABILITY
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "base_fresh_limit_minutes",
            "base_stale_limit_minutes",
            "high_resolution_urgency_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "time_pressure_activation",
            "time_pressure_discount",
            "time_pressure_floor",
            "high_time_sensitivity_threshold",
            "high_reliability_threshold",
            "medium_reliability_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyCandidateEvidenceFreshnessMatrixV10Input:
    market_id: str
    source_family: str
    evidence_age_minutes: Decimal
    source_reliability_score: Decimal
    confirmation_role: str
    market_time_sensitivity: Decimal
    time_to_resolution_minutes: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        _require_canonical_string("source_family", self.source_family)
        object.__setattr__(
            self,
            "evidence_age_minutes",
            _normalize_nonnegative_decimal(
                "evidence_age_minutes",
                self.evidence_age_minutes,
            ),
        )
        object.__setattr__(
            self,
            "source_reliability_score",
            _normalize_unit_decimal(
                "source_reliability_score",
                self.source_reliability_score,
            ),
        )
        _require_member("confirmation_role", self.confirmation_role, CONFIRMATION_ROLES)
        object.__setattr__(
            self,
            "market_time_sensitivity",
            _normalize_unit_decimal(
                "market_time_sensitivity",
                self.market_time_sensitivity,
            ),
        )
        object.__setattr__(
            self,
            "time_to_resolution_minutes",
            _normalize_nonnegative_decimal(
                "time_to_resolution_minutes",
                self.time_to_resolution_minutes,
            ),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class StrategyCandidateEvidenceFreshnessMatrixV10Row:
    market_id: str
    source_family: str
    evidence_age_minutes: Decimal
    source_reliability_score: Decimal
    confirmation_role: str
    market_time_sensitivity: Decimal
    time_to_resolution_minutes: Decimal
    effective_fresh_limit_minutes: Decimal
    effective_stale_limit_minutes: Decimal
    freshness_score: Decimal
    row_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        _require_canonical_string("source_family", self.source_family)
        for field_name in (
            "evidence_age_minutes",
            "time_to_resolution_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_reliability_score",
            "market_time_sensitivity",
            "freshness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("confirmation_role", self.confirmation_role, CONFIRMATION_ROLES)
        for field_name in (
            "effective_fresh_limit_minutes",
            "effective_stale_limit_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.effective_stale_limit_minutes < self.effective_fresh_limit_minutes:
            raise ValueError(
                "effective_stale_limit_minutes must be at least effective_fresh_limit_minutes",
            )
        _require_member("row_status", self.row_status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class StrategyCandidateEvidenceFreshnessMatrixV10Result:
    config_version: str
    matrix_status: str
    freshness_rows: tuple[StrategyCandidateEvidenceFreshnessMatrixV10Row, ...]
    stale_source_families: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_member("matrix_status", self.matrix_status, MATRIX_STATUSES)
        object.__setattr__(
            self,
            "freshness_rows",
            _normalize_rows(self.freshness_rows),
        )
        object.__setattr__(
            self,
            "stale_source_families",
            _normalize_source_families(self.stale_source_families),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_result(self)
        _require_hard_flags("result", self)

    @property
    def payload(self) -> dict[str, object]:
        return strategy_candidate_evidence_freshness_matrix_v10_payload(self)


def build_strategy_candidate_evidence_freshness_matrix_v10(
    evidence_rows: Iterable[StrategyCandidateEvidenceFreshnessMatrixV10Input],
    *,
    config: StrategyCandidateEvidenceFreshnessMatrixV10Config
    | None = None,
) -> StrategyCandidateEvidenceFreshnessMatrixV10Result:
    active_config = (
        StrategyCandidateEvidenceFreshnessMatrixV10Config()
        if config is None
        else config
    )
    if type(active_config) is not StrategyCandidateEvidenceFreshnessMatrixV10Config:
        raise ValueError(
            "config must be a StrategyCandidateEvidenceFreshnessMatrixV10Config",
        )
    _require_hard_flags("config", active_config)

    rows = tuple(_row_from_input(row, active_config) for row in _normalize_inputs(evidence_rows))
    ordered_rows = _sort_rows(rows)
    matrix_status = _matrix_status(ordered_rows)
    return StrategyCandidateEvidenceFreshnessMatrixV10Result(
        config_version=active_config.config_version,
        matrix_status=matrix_status,
        freshness_rows=ordered_rows,
        stale_source_families=_stale_source_families(ordered_rows),
        reason_codes=_matrix_reason_codes(ordered_rows, matrix_status),
    )


def strategy_candidate_evidence_freshness_matrix_v10_payload(
    result: StrategyCandidateEvidenceFreshnessMatrixV10Result,
) -> dict[str, object]:
    if type(result) is not StrategyCandidateEvidenceFreshnessMatrixV10Result:
        raise ValueError(
            "result must be a StrategyCandidateEvidenceFreshnessMatrixV10Result",
        )
    _require_hard_flags("result", result)
    return {
        "config_version": result.config_version,
        "matrix_status": result.matrix_status,
        "freshness_rows": [_row_payload(row) for row in result.freshness_rows],
        "stale_source_families": list(result.stale_source_families),
        "reason_codes": list(result.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_from_input(
    row: StrategyCandidateEvidenceFreshnessMatrixV10Input,
    config: StrategyCandidateEvidenceFreshnessMatrixV10Config,
) -> StrategyCandidateEvidenceFreshnessMatrixV10Row:
    if type(row) is not StrategyCandidateEvidenceFreshnessMatrixV10Input:
        raise ValueError(
            "evidence rows must contain StrategyCandidateEvidenceFreshnessMatrixV10Input",
        )
    _require_hard_flags("input", row)
    fresh_limit = _effective_limit(
        config.base_fresh_limit_minutes,
        row.market_time_sensitivity,
        config,
    )
    stale_limit = _effective_limit(
        config.base_stale_limit_minutes,
        row.market_time_sensitivity,
        config,
    )
    row_status = _row_status(row.evidence_age_minutes, fresh_limit, stale_limit)
    freshness_score = _freshness_score(
        row.evidence_age_minutes,
        stale_limit,
        row.source_reliability_score,
    )
    return StrategyCandidateEvidenceFreshnessMatrixV10Row(
        market_id=row.market_id,
        source_family=row.source_family,
        evidence_age_minutes=row.evidence_age_minutes,
        source_reliability_score=row.source_reliability_score,
        confirmation_role=row.confirmation_role,
        market_time_sensitivity=row.market_time_sensitivity,
        time_to_resolution_minutes=row.time_to_resolution_minutes,
        effective_fresh_limit_minutes=fresh_limit,
        effective_stale_limit_minutes=stale_limit,
        freshness_score=freshness_score,
        row_status=row_status,
        reason_codes=_row_reason_codes(
            row.evidence_age_minutes,
            row.source_reliability_score,
            row.confirmation_role,
            row.market_time_sensitivity,
            row.time_to_resolution_minutes,
            row_status,
            config,
        ),
    )


def _row_payload(row: StrategyCandidateEvidenceFreshnessMatrixV10Row) -> dict[str, object]:
    _require_hard_flags("row", row)
    return {
        "market_id": row.market_id,
        "source_family": row.source_family,
        "evidence_age_minutes": _decimal_payload(row.evidence_age_minutes),
        "source_reliability_score": _decimal_payload(row.source_reliability_score),
        "confirmation_role": row.confirmation_role,
        "market_time_sensitivity": _decimal_payload(row.market_time_sensitivity),
        "time_to_resolution_minutes": _decimal_payload(row.time_to_resolution_minutes),
        "effective_fresh_limit_minutes": _decimal_payload(
            row.effective_fresh_limit_minutes,
        ),
        "effective_stale_limit_minutes": _decimal_payload(
            row.effective_stale_limit_minutes,
        ),
        "freshness_score": _decimal_payload(row.freshness_score),
        "row_status": row.row_status,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _effective_limit(
    base_limit: Decimal,
    market_time_sensitivity: Decimal,
    config: StrategyCandidateEvidenceFreshnessMatrixV10Config,
) -> Decimal:
    pressure_factor = ONE
    if market_time_sensitivity >= config.time_pressure_activation:
        pressure_factor = ONE - (market_time_sensitivity * config.time_pressure_discount)
    if pressure_factor < config.time_pressure_floor:
        pressure_factor = config.time_pressure_floor
    return _quantize(base_limit * pressure_factor)


def _freshness_score(
    evidence_age_minutes: Decimal,
    effective_stale_limit_minutes: Decimal,
    source_reliability_score: Decimal,
) -> Decimal:
    if evidence_age_minutes >= effective_stale_limit_minutes:
        return ZERO
    age_weight = ONE - (evidence_age_minutes / effective_stale_limit_minutes)
    return _normalize_unit_decimal(
        "freshness_score",
        _quantize(age_weight * source_reliability_score),
    )


def _row_status(
    evidence_age_minutes: Decimal,
    effective_fresh_limit_minutes: Decimal,
    effective_stale_limit_minutes: Decimal,
) -> str:
    if evidence_age_minutes > effective_stale_limit_minutes:
        return "stale"
    if evidence_age_minutes > effective_fresh_limit_minutes:
        return "watch"
    return "fresh"


def _row_reason_codes(
    evidence_age_minutes: Decimal,
    source_reliability_score: Decimal,
    confirmation_role: str,
    market_time_sensitivity: Decimal,
    time_to_resolution_minutes: Decimal,
    row_status: str,
    config: StrategyCandidateEvidenceFreshnessMatrixV10Config,
) -> tuple[str, ...]:
    codes: list[str] = []
    if market_time_sensitivity >= config.high_time_sensitivity_threshold:
        codes.append("time_sensitivity_high")
    if time_to_resolution_minutes <= config.high_resolution_urgency_minutes:
        codes.append("resolution_urgency_high")
    if row_status == "stale":
        codes.append("evidence_age_stale")
    elif row_status == "watch":
        codes.append("evidence_age_watch")

    if source_reliability_score >= config.high_reliability_threshold:
        codes.append("source_reliability_high")
    elif source_reliability_score >= config.medium_reliability_threshold:
        codes.append("source_reliability_medium")
    else:
        codes.append("source_reliability_low")

    codes.append(f"confirmation_role_{confirmation_role}")
    codes.append(f"row_status_{row_status}")
    return _ordered_reason_codes(codes)


def _matrix_reason_codes(
    rows: tuple[StrategyCandidateEvidenceFreshnessMatrixV10Row, ...],
    matrix_status: str,
) -> tuple[str, ...]:
    codes: list[str] = []
    if not rows:
        codes.append("freshness_matrix_empty")
    for row in rows:
        codes.extend(row.reason_codes)
    codes.append(f"matrix_status_{matrix_status}")
    return _ordered_reason_codes(codes)


def _ordered_reason_codes(codes: Iterable[str]) -> tuple[str, ...]:
    present = frozenset(codes)
    return tuple(code for code in _REASON_PRIORITY if code in present)


def _matrix_status(
    rows: tuple[StrategyCandidateEvidenceFreshnessMatrixV10Row, ...],
) -> str:
    if not rows:
        return "stale"
    if any(row.row_status == "stale" for row in rows):
        return "stale"
    if any(row.row_status == "watch" for row in rows):
        return "watch"
    return "fresh"


def _sort_rows(
    rows: tuple[StrategyCandidateEvidenceFreshnessMatrixV10Row, ...],
) -> tuple[StrategyCandidateEvidenceFreshnessMatrixV10Row, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _STATUS_SORT[row.row_status],
                row.freshness_score,
                row.market_id,
                row.source_family,
            ),
        ),
    )


def _stale_source_families(
    rows: tuple[StrategyCandidateEvidenceFreshnessMatrixV10Row, ...],
) -> tuple[str, ...]:
    families = {
        row.source_family
        for row in rows
        if row.row_status == "stale"
    }
    return tuple(sorted(families))


def _normalize_inputs(
    rows: Iterable[StrategyCandidateEvidenceFreshnessMatrixV10Input],
) -> tuple[StrategyCandidateEvidenceFreshnessMatrixV10Input, ...]:
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not StrategyCandidateEvidenceFreshnessMatrixV10Input:
            raise ValueError(
                "evidence rows must contain StrategyCandidateEvidenceFreshnessMatrixV10Input",
            )
        _require_hard_flags("input", row)
    return normalized


def _normalize_rows(
    rows: tuple[StrategyCandidateEvidenceFreshnessMatrixV10Row, ...],
) -> tuple[StrategyCandidateEvidenceFreshnessMatrixV10Row, ...]:
    if type(rows) is not tuple:
        raise ValueError("freshness_rows must be a tuple")
    for row in rows:
        if type(row) is not StrategyCandidateEvidenceFreshnessMatrixV10Row:
            raise ValueError(
                "freshness_rows must contain StrategyCandidateEvidenceFreshnessMatrixV10Row",
            )
        _require_hard_flags("row", row)
    return rows


def _normalize_source_families(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("stale_source_families must be a tuple")
    for value in values:
        _require_canonical_string("stale_source_family", value)
    return values


def _normalize_reason_codes(name: str, values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    seen: set[str] = set()
    normalized: list[str] = []
    for value in values:
        _require_canonical_string(name, value)
        if value in seen:
            raise ValueError(f"{name} must not contain duplicates")
        seen.add(value)
        normalized.append(value)
    return tuple(normalized)


def _validate_config(config: StrategyCandidateEvidenceFreshnessMatrixV10Config) -> None:
    if config.base_stale_limit_minutes < config.base_fresh_limit_minutes:
        raise ValueError("base_stale_limit_minutes must be at least base_fresh_limit_minutes")
    if config.high_reliability_threshold < config.medium_reliability_threshold:
        raise ValueError(
            "high_reliability_threshold must be at least medium_reliability_threshold",
        )


def _validate_row(row: StrategyCandidateEvidenceFreshnessMatrixV10Row) -> None:
    expected_status = _row_status(
        row.evidence_age_minutes,
        row.effective_fresh_limit_minutes,
        row.effective_stale_limit_minutes,
    )
    if row.row_status != expected_status:
        raise ValueError("row_status must match evidence age limits")
    expected_score = _freshness_score(
        row.evidence_age_minutes,
        row.effective_stale_limit_minutes,
        row.source_reliability_score,
    )
    if row.freshness_score != expected_score:
        raise ValueError("freshness_score must match evidence age and reliability")


def _validate_result(result: StrategyCandidateEvidenceFreshnessMatrixV10Result) -> None:
    ordered_rows = _sort_rows(result.freshness_rows)
    if result.freshness_rows != ordered_rows:
        raise ValueError("freshness_rows must be sorted by status and freshness")
    expected_status = _matrix_status(result.freshness_rows)
    if result.matrix_status != expected_status:
        raise ValueError("matrix_status must match freshness_rows")
    expected_stale_source_families = _stale_source_families(result.freshness_rows)
    if result.stale_source_families != expected_stale_source_families:
        raise ValueError("stale_source_families must match stale rows")
    expected_reason_codes = _matrix_reason_codes(
        result.freshness_rows,
        result.matrix_status,
    )
    if result.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match freshness_rows")


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    decimal = _require_decimal(name, value)
    if decimal < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize(decimal)


def _normalize_positive_decimal(name: str, value: object) -> Decimal:
    decimal = _require_decimal(name, value)
    if decimal <= ZERO:
        raise ValueError(f"{name} must be greater than zero")
    return _quantize(decimal)


def _normalize_unit_decimal(name: str, value: object) -> Decimal:
    decimal = _require_decimal(name, value)
    if decimal < ZERO or decimal > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return _quantize(decimal)


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)


def _decimal_payload(value: Decimal) -> str:
    return str(_quantize(value))


def _require_canonical_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")


def _require_member(name: str, value: str, allowed: tuple[str, ...]) -> None:
    if value not in allowed:
        raise ValueError(f"{name} must be one of {', '.join(allowed)}")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError(f"{label} must be paper_only")
    if getattr(value, "report_only") is not True:
        raise ValueError(f"{label} must be report_only")
    if getattr(value, "readonly") is not True:
        raise ValueError(f"{label} must be readonly")
