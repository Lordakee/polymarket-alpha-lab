"""Read-only Phase 1 outcome freshness SLA recheck report."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_CONFIG_VERSION = "market-outcome-freshness-sla-recheck-v0"
ZERO = Decimal("0")
ONE = Decimal("1")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
COUNT_ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
SECOND_QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64)
CONTRADICTION_STATES = ("none", "open", "resolved")
SOURCE_FRESHNESS_STATUSES = ("recovered", "stale", "missing")
ACKNOWLEDGEMENT_STATUSES = ("acknowledged", "late", "missing")
RECHECK_STATUSES = ("recovered", "watch", "breached")
REPORT_STATUSES = ("empty", "recovered", "watch", "breached")
ROW_REASON_CODES = (
    "source_not_recovered",
    "acknowledgement_missing",
    "acknowledgement_late",
    "contradiction_open",
    "contradiction_resolved",
    "repeated_team_category_miss",
    "sla_recovered",
)
GROUP_REASON_CODES = ("repeated_team_category_miss", "no_repeated_miss")
REPORT_REASON_CODES = (
    "no_rechecks",
    "all_rechecks_recovered",
    "source_not_recovered",
    "acknowledgement_missing",
    "acknowledgement_late",
    "contradiction_open",
    "contradiction_resolved",
    "repeated_team_category_miss",
)
RECHECK_STATUS_PRIORITY = {"breached": 0, "watch": 1, "recovered": 2}
REPORT_STATUS_PRIORITY = {"breached": 0, "watch": 1, "recovered": 2}


@dataclass(frozen=True, slots=True)
class MarketOutcomeFreshnessSlaRecheckConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    max_source_age_seconds: Decimal = Decimal("300")
    max_acknowledgement_lag_seconds: Decimal = Decimal("600")
    repeated_team_category_miss_threshold: Decimal = Decimal("2")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "max_source_age_seconds",
            _normalize_positive_seconds(
                "max_source_age_seconds",
                self.max_source_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "max_acknowledgement_lag_seconds",
            _normalize_positive_seconds(
                "max_acknowledgement_lag_seconds",
                self.max_acknowledgement_lag_seconds,
            ),
        )
        object.__setattr__(
            self,
            "repeated_team_category_miss_threshold",
            _normalize_positive_integral_decimal(
                "repeated_team_category_miss_threshold",
                self.repeated_team_category_miss_threshold,
            ),
        )
        require_paper_only_flags("MarketOutcomeFreshnessSlaRecheckConfig", self)


@dataclass(frozen=True, slots=True)
class MarketOutcomeFreshnessSlaRecheckObservation:
    market_id: str
    outcome_id: str
    team_id: str
    category_id: str
    prior_breach_detected_at: datetime
    rechecked_at: datetime
    source_updated_at: datetime | None
    acknowledged_at: datetime | None
    contradiction_state: str
    prior_team_category_miss_count: Decimal = ZERO
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("market_id", "outcome_id", "team_id", "category_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "prior_breach_detected_at",
            _as_utc("prior_breach_detected_at", self.prior_breach_detected_at),
        )
        object.__setattr__(
            self,
            "rechecked_at",
            _as_utc("rechecked_at", self.rechecked_at),
        )
        object.__setattr__(
            self,
            "source_updated_at",
            _as_optional_utc("source_updated_at", self.source_updated_at),
        )
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_optional_utc("acknowledged_at", self.acknowledged_at),
        )
        _require_known_value(
            "contradiction_state",
            self.contradiction_state,
            CONTRADICTION_STATES,
        )
        object.__setattr__(
            self,
            "prior_team_category_miss_count",
            _normalize_nonnegative_integral_decimal(
                "prior_team_category_miss_count",
                self.prior_team_category_miss_count,
            ),
        )
        _validate_observation_timeline(self)
        require_paper_only_flags("MarketOutcomeFreshnessSlaRecheckObservation", self)


@dataclass(frozen=True, slots=True)
class MarketOutcomeFreshnessSlaRecheckRow:
    market_id: str
    outcome_id: str
    team_id: str
    category_id: str
    prior_breach_detected_at: datetime
    rechecked_at: datetime
    source_updated_at: datetime | None
    acknowledged_at: datetime | None
    breach_age_seconds: Decimal
    source_age_seconds: Decimal | None
    acknowledgement_lag_seconds: Decimal | None
    source_freshness_status: str
    acknowledgement_status: str
    contradiction_state: str
    recheck_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("market_id", "outcome_id", "team_id", "category_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "prior_breach_detected_at",
            _as_utc("prior_breach_detected_at", self.prior_breach_detected_at),
        )
        object.__setattr__(
            self,
            "rechecked_at",
            _as_utc("rechecked_at", self.rechecked_at),
        )
        object.__setattr__(
            self,
            "source_updated_at",
            _as_optional_utc("source_updated_at", self.source_updated_at),
        )
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_optional_utc("acknowledged_at", self.acknowledged_at),
        )
        object.__setattr__(
            self,
            "breach_age_seconds",
            _normalize_nonnegative_seconds(
                "breach_age_seconds",
                self.breach_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "source_age_seconds",
            _normalize_optional_nonnegative_seconds(
                "source_age_seconds",
                self.source_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "acknowledgement_lag_seconds",
            _normalize_optional_nonnegative_seconds(
                "acknowledgement_lag_seconds",
                self.acknowledgement_lag_seconds,
            ),
        )
        _require_known_value(
            "source_freshness_status",
            self.source_freshness_status,
            SOURCE_FRESHNESS_STATUSES,
        )
        _require_known_value(
            "acknowledgement_status",
            self.acknowledgement_status,
            ACKNOWLEDGEMENT_STATUSES,
        )
        _require_known_value(
            "contradiction_state",
            self.contradiction_state,
            CONTRADICTION_STATES,
        )
        _require_known_value("recheck_status", self.recheck_status, RECHECK_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                ROW_REASON_CODES,
            ),
        )
        _validate_row_consistency(self)
        require_paper_only_flags("MarketOutcomeFreshnessSlaRecheckRow", self)


@dataclass(frozen=True, slots=True)
class MarketOutcomeFreshnessSlaRecheckTeamCategoryMissRow:
    team_id: str
    category_id: str
    miss_count: Decimal
    repeated_miss: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("team_id", self.team_id)
        _require_canonical_string("category_id", self.category_id)
        object.__setattr__(
            self,
            "miss_count",
            _normalize_nonnegative_integral_decimal("miss_count", self.miss_count),
        )
        if type(self.repeated_miss) is not bool:
            raise ValueError("repeated_miss must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                GROUP_REASON_CODES,
            ),
        )
        _validate_team_category_miss_row_consistency(self)
        require_paper_only_flags(
            "MarketOutcomeFreshnessSlaRecheckTeamCategoryMissRow",
            self,
        )


@dataclass(frozen=True, slots=True)
class MarketOutcomeFreshnessSlaRecheckReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    recovered_count: Decimal
    watch_count: Decimal
    breached_count: Decimal
    source_recovered_count: Decimal
    source_stale_count: Decimal
    source_missing_count: Decimal
    acknowledged_count: Decimal
    acknowledgement_late_count: Decimal
    acknowledgement_missing_count: Decimal
    contradiction_open_count: Decimal
    repeated_team_category_miss_count: Decimal
    recovery_ratio: Decimal | None
    oldest_breach_age_seconds: Decimal | None
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[MarketOutcomeFreshnessSlaRecheckRow, ...]
    team_category_miss_rows: tuple[MarketOutcomeFreshnessSlaRecheckTeamCategoryMissRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "input_count",
            "row_count",
            "recovered_count",
            "watch_count",
            "breached_count",
            "source_recovered_count",
            "source_stale_count",
            "source_missing_count",
            "acknowledged_count",
            "acknowledgement_late_count",
            "acknowledgement_missing_count",
            "contradiction_open_count",
            "repeated_team_category_miss_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "recovery_ratio",
            _normalize_optional_ratio("recovery_ratio", self.recovery_ratio),
        )
        object.__setattr__(
            self,
            "oldest_breach_age_seconds",
            _normalize_optional_nonnegative_seconds(
                "oldest_breach_age_seconds",
                self.oldest_breach_age_seconds,
            ),
        )
        _require_known_value("status", self.status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "team_category_miss_rows",
            _normalize_team_category_miss_rows(self.team_category_miss_rows),
        )
        _validate_report_consistency(self)
        require_paper_only_flags("MarketOutcomeFreshnessSlaRecheckReport", self)


def build_market_outcome_freshness_sla_recheck_report(
    observations: Iterable[MarketOutcomeFreshnessSlaRecheckObservation],
    *,
    config: MarketOutcomeFreshnessSlaRecheckConfig,
    generated_at: datetime,
) -> MarketOutcomeFreshnessSlaRecheckReport:
    if type(config) is not MarketOutcomeFreshnessSlaRecheckConfig:
        raise ValueError("config must be a MarketOutcomeFreshnessSlaRecheckConfig")
    generated_at_utc = _as_utc("generated_at", generated_at)
    require_paper_only_flags("MarketOutcomeFreshnessSlaRecheckConfig", config)

    normalized_observations = _normalize_observations(observations)
    base_rows = tuple(
        _row_from_observation(
            observation,
            config=config,
            repeated_team_category_miss=False,
        )
        for observation in normalized_observations
    )
    miss_counts = _team_category_miss_counts(normalized_observations, base_rows)
    group_rows = _team_category_miss_rows(miss_counts, config=config)
    repeated_keys = frozenset(
        (row.team_id, row.category_id)
        for row in group_rows
        if row.repeated_miss
    )
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    observation,
                    config=config,
                    repeated_team_category_miss=(
                        (observation.team_id, observation.category_id) in repeated_keys
                        and _base_row_has_miss(row)
                    ),
                )
                for observation, row in zip(normalized_observations, base_rows, strict=True)
            ),
            key=_row_sort_key,
        ),
    )

    return MarketOutcomeFreshnessSlaRecheckReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_decimal_count(normalized_observations),
        row_count=_decimal_count(rows),
        recovered_count=_row_status_count(rows, "recovered"),
        watch_count=_row_status_count(rows, "watch"),
        breached_count=_row_status_count(rows, "breached"),
        source_recovered_count=_source_status_count(rows, "recovered"),
        source_stale_count=_source_status_count(rows, "stale"),
        source_missing_count=_source_status_count(rows, "missing"),
        acknowledged_count=_acknowledgement_status_count(rows, "acknowledged"),
        acknowledgement_late_count=_acknowledgement_status_count(rows, "late"),
        acknowledgement_missing_count=_acknowledgement_status_count(rows, "missing"),
        contradiction_open_count=_contradiction_state_count(rows, "open"),
        repeated_team_category_miss_count=_decimal_count(
            tuple(row for row in group_rows if row.repeated_miss),
        ),
        recovery_ratio=_recovery_ratio(rows),
        oldest_breach_age_seconds=_oldest_breach_age_seconds(rows),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
        team_category_miss_rows=group_rows,
    )


def market_outcome_freshness_sla_recheck_report_payload(
    report: MarketOutcomeFreshnessSlaRecheckReport,
) -> dict[str, Any]:
    if type(report) is not MarketOutcomeFreshnessSlaRecheckReport:
        raise ValueError("report must be a MarketOutcomeFreshnessSlaRecheckReport")
    require_paper_only_flags("MarketOutcomeFreshnessSlaRecheckReport", report)
    reject_unsafe_surface_fields("MarketOutcomeFreshnessSlaRecheckReport", report)
    ready = json_ready_no_floats(report)
    if type(ready) is not dict:
        raise ValueError("report JSON value must be an object")
    reject_unsafe_surface_fields("market outcome freshness SLA recheck payload", ready)
    return ready


def _row_from_observation(
    observation: MarketOutcomeFreshnessSlaRecheckObservation,
    *,
    config: MarketOutcomeFreshnessSlaRecheckConfig,
    repeated_team_category_miss: bool,
) -> MarketOutcomeFreshnessSlaRecheckRow:
    breach_age_seconds = _seconds_between(
        observation.prior_breach_detected_at,
        observation.rechecked_at,
    )
    source_age_seconds = (
        None
        if observation.source_updated_at is None
        else _seconds_between(observation.source_updated_at, observation.rechecked_at)
    )
    acknowledgement_lag_seconds = (
        None
        if observation.acknowledged_at is None
        else _seconds_between(
            observation.prior_breach_detected_at,
            observation.acknowledged_at,
        )
    )
    source_freshness_status = _source_freshness_status(
        observation,
        source_age_seconds=source_age_seconds,
        config=config,
    )
    acknowledgement_status = _acknowledgement_status(
        acknowledgement_lag_seconds,
        config=config,
    )
    reason_codes = _row_reason_codes(
        source_freshness_status=source_freshness_status,
        acknowledgement_status=acknowledgement_status,
        contradiction_state=observation.contradiction_state,
        repeated_team_category_miss=repeated_team_category_miss,
    )

    return MarketOutcomeFreshnessSlaRecheckRow(
        market_id=observation.market_id,
        outcome_id=observation.outcome_id,
        team_id=observation.team_id,
        category_id=observation.category_id,
        prior_breach_detected_at=observation.prior_breach_detected_at,
        rechecked_at=observation.rechecked_at,
        source_updated_at=observation.source_updated_at,
        acknowledged_at=observation.acknowledged_at,
        breach_age_seconds=breach_age_seconds,
        source_age_seconds=source_age_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        source_freshness_status=source_freshness_status,
        acknowledgement_status=acknowledgement_status,
        contradiction_state=observation.contradiction_state,
        recheck_status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _normalize_observations(
    values: Iterable[MarketOutcomeFreshnessSlaRecheckObservation],
) -> tuple[MarketOutcomeFreshnessSlaRecheckObservation, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        observations = tuple(values)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    for value in observations:
        if type(value) is not MarketOutcomeFreshnessSlaRecheckObservation:
            raise ValueError(
                "observations must contain MarketOutcomeFreshnessSlaRecheckObservation values",
            )
        require_paper_only_flags("MarketOutcomeFreshnessSlaRecheckObservation", value)
    return observations


def _team_category_miss_counts(
    observations: tuple[MarketOutcomeFreshnessSlaRecheckObservation, ...],
    base_rows: tuple[MarketOutcomeFreshnessSlaRecheckRow, ...],
) -> dict[tuple[str, str], Decimal]:
    counts: dict[tuple[str, str], Decimal] = {}
    for observation, row in zip(observations, base_rows, strict=True):
        key = (observation.team_id, observation.category_id)
        current_miss_count = COUNT_ONE if _base_row_has_miss(row) else ZERO
        counts[key] = (
            counts.get(key, ZERO)
            + observation.prior_team_category_miss_count
            + current_miss_count
        )
    return counts


def _team_category_miss_rows(
    miss_counts: dict[tuple[str, str], Decimal],
    *,
    config: MarketOutcomeFreshnessSlaRecheckConfig,
) -> tuple[MarketOutcomeFreshnessSlaRecheckTeamCategoryMissRow, ...]:
    return tuple(
        sorted(
            (
                MarketOutcomeFreshnessSlaRecheckTeamCategoryMissRow(
                    team_id=team_id,
                    category_id=category_id,
                    miss_count=miss_count,
                    repeated_miss=(
                        miss_count >= config.repeated_team_category_miss_threshold
                    ),
                    reason_codes=(
                        ("repeated_team_category_miss",)
                        if miss_count >= config.repeated_team_category_miss_threshold
                        else ("no_repeated_miss",)
                    ),
                )
                for (team_id, category_id), miss_count in miss_counts.items()
            ),
            key=_team_category_miss_row_sort_key,
        ),
    )


def _source_freshness_status(
    observation: MarketOutcomeFreshnessSlaRecheckObservation,
    *,
    source_age_seconds: Decimal | None,
    config: MarketOutcomeFreshnessSlaRecheckConfig,
) -> str:
    if observation.source_updated_at is None or source_age_seconds is None:
        return "missing"
    if (
        observation.source_updated_at >= observation.prior_breach_detected_at
        and source_age_seconds <= config.max_source_age_seconds
    ):
        return "recovered"
    return "stale"


def _acknowledgement_status(
    acknowledgement_lag_seconds: Decimal | None,
    *,
    config: MarketOutcomeFreshnessSlaRecheckConfig,
) -> str:
    if acknowledgement_lag_seconds is None:
        return "missing"
    if acknowledgement_lag_seconds <= config.max_acknowledgement_lag_seconds:
        return "acknowledged"
    return "late"


def _row_reason_codes(
    *,
    source_freshness_status: str,
    acknowledgement_status: str,
    contradiction_state: str,
    repeated_team_category_miss: bool,
) -> tuple[str, ...]:
    requested_codes = (
        ("source_not_recovered",)
        if source_freshness_status != "recovered"
        else ()
    )
    requested_codes += (
        ("acknowledgement_missing",)
        if acknowledgement_status == "missing"
        else ()
    )
    requested_codes += (
        ("acknowledgement_late",)
        if acknowledgement_status == "late"
        else ()
    )
    requested_codes += (
        ("contradiction_open",)
        if contradiction_state == "open"
        else ()
    )
    requested_codes += (
        ("contradiction_resolved",)
        if contradiction_state == "resolved"
        else ()
    )
    requested_codes += (
        ("repeated_team_category_miss",)
        if repeated_team_category_miss
        else ()
    )
    if not requested_codes:
        requested_codes = ("sla_recovered",)
    return tuple(code for code in ROW_REASON_CODES if code in requested_codes)


def _base_row_has_miss(row: MarketOutcomeFreshnessSlaRecheckRow) -> bool:
    return (
        row.source_freshness_status != "recovered"
        or row.acknowledgement_status == "missing"
        or row.contradiction_state == "open"
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(
        code in reason_codes
        for code in (
            "source_not_recovered",
            "acknowledgement_missing",
            "contradiction_open",
        )
    ):
        return "breached"
    if reason_codes == ("sla_recovered",):
        return "recovered"
    return "watch"


def _report_status(rows: tuple[MarketOutcomeFreshnessSlaRecheckRow, ...]) -> str:
    if not rows:
        return "empty"
    return min(
        (row.recheck_status for row in rows),
        key=lambda status: REPORT_STATUS_PRIORITY[status],
    )


def _report_reason_codes(
    rows: tuple[MarketOutcomeFreshnessSlaRecheckRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_rechecks",)
    requested_codes = tuple(
        code
        for row in rows
        for code in row.reason_codes
        if code != "sla_recovered"
    )
    if not requested_codes:
        return ("all_rechecks_recovered",)
    return tuple(code for code in REPORT_REASON_CODES if code in requested_codes)


def _normalize_rows(
    values: Iterable[MarketOutcomeFreshnessSlaRecheckRow],
) -> tuple[MarketOutcomeFreshnessSlaRecheckRow, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in rows:
        if type(row) is not MarketOutcomeFreshnessSlaRecheckRow:
            raise ValueError("rows must contain MarketOutcomeFreshnessSlaRecheckRow values")
        require_paper_only_flags("MarketOutcomeFreshnessSlaRecheckRow", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    return rows


def _normalize_team_category_miss_rows(
    values: Iterable[MarketOutcomeFreshnessSlaRecheckTeamCategoryMissRow],
) -> tuple[MarketOutcomeFreshnessSlaRecheckTeamCategoryMissRow, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("team_category_miss_rows must be an iterable")
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError("team_category_miss_rows must be an iterable") from exc
    for row in rows:
        if type(row) is not MarketOutcomeFreshnessSlaRecheckTeamCategoryMissRow:
            raise ValueError(
                "team_category_miss_rows must contain team category miss rows",
            )
        require_paper_only_flags(
            "MarketOutcomeFreshnessSlaRecheckTeamCategoryMissRow",
            row,
        )
    if rows != tuple(sorted(rows, key=_team_category_miss_row_sort_key)):
        raise ValueError("team_category_miss_rows must be sorted")
    return rows


def _validate_observation_timeline(
    observation: MarketOutcomeFreshnessSlaRecheckObservation,
) -> None:
    if observation.prior_breach_detected_at > observation.rechecked_at:
        raise ValueError("prior_breach_detected_at must be at or before rechecked_at")
    if (
        observation.source_updated_at is not None
        and observation.source_updated_at > observation.rechecked_at
    ):
        raise ValueError("source_updated_at must be at or before rechecked_at")
    if observation.acknowledged_at is not None:
        if observation.acknowledged_at < observation.prior_breach_detected_at:
            raise ValueError(
                "acknowledged_at must be at or after prior_breach_detected_at",
            )
        if observation.acknowledged_at > observation.rechecked_at:
            raise ValueError("acknowledged_at must be at or before rechecked_at")


def _validate_row_consistency(row: MarketOutcomeFreshnessSlaRecheckRow) -> None:
    _validate_row_timeline(row)
    if row.breach_age_seconds != _seconds_between(
        row.prior_breach_detected_at,
        row.rechecked_at,
    ):
        raise ValueError("breach_age_seconds must match the recheck timeline")
    if row.source_updated_at is None:
        if row.source_age_seconds is not None:
            raise ValueError("source_age_seconds must be absent without source_updated_at")
        if row.source_freshness_status != "missing":
            raise ValueError("source_freshness_status must be missing")
    else:
        if row.source_age_seconds != _seconds_between(
            row.source_updated_at,
            row.rechecked_at,
        ):
            raise ValueError("source_age_seconds must match source_updated_at")
        if row.source_freshness_status == "missing":
            raise ValueError("source_freshness_status must not be missing")
    if row.acknowledged_at is None:
        if row.acknowledgement_lag_seconds is not None:
            raise ValueError(
                "acknowledgement_lag_seconds must be absent without acknowledged_at",
            )
        if row.acknowledgement_status != "missing":
            raise ValueError("acknowledgement_status must be missing")
    else:
        if row.acknowledgement_lag_seconds != _seconds_between(
            row.prior_breach_detected_at,
            row.acknowledged_at,
        ):
            raise ValueError("acknowledgement_lag_seconds must match acknowledged_at")
        if row.acknowledgement_status == "missing":
            raise ValueError("acknowledgement_status must not be missing")
    expected_codes = _expected_row_reason_codes(row)
    if row.reason_codes != expected_codes:
        raise ValueError(
            "reason_codes must match source_freshness_status, "
            "acknowledgement_status, contradiction_state, and repeated state",
        )
    if row.recheck_status != _row_status(row.reason_codes):
        raise ValueError("recheck_status must match reason_codes")


def _validate_row_timeline(row: MarketOutcomeFreshnessSlaRecheckRow) -> None:
    if row.prior_breach_detected_at > row.rechecked_at:
        raise ValueError("prior_breach_detected_at must be at or before rechecked_at")
    if row.source_updated_at is not None and row.source_updated_at > row.rechecked_at:
        raise ValueError("source_updated_at must be at or before rechecked_at")
    if row.acknowledged_at is not None:
        if row.acknowledged_at < row.prior_breach_detected_at:
            raise ValueError(
                "acknowledged_at must be at or after prior_breach_detected_at",
            )
        if row.acknowledged_at > row.rechecked_at:
            raise ValueError("acknowledged_at must be at or before rechecked_at")


def _expected_row_reason_codes(
    row: MarketOutcomeFreshnessSlaRecheckRow,
) -> tuple[str, ...]:
    repeated_team_category_miss = "repeated_team_category_miss" in row.reason_codes
    return _row_reason_codes(
        source_freshness_status=row.source_freshness_status,
        acknowledgement_status=row.acknowledgement_status,
        contradiction_state=row.contradiction_state,
        repeated_team_category_miss=repeated_team_category_miss,
    )


def _validate_team_category_miss_row_consistency(
    row: MarketOutcomeFreshnessSlaRecheckTeamCategoryMissRow,
) -> None:
    expected_codes = (
        ("repeated_team_category_miss",)
        if row.repeated_miss
        else ("no_repeated_miss",)
    )
    if row.reason_codes != expected_codes:
        raise ValueError("reason_codes must match repeated_miss")


def _validate_report_consistency(
    report: MarketOutcomeFreshnessSlaRecheckReport,
) -> None:
    if report.input_count != _decimal_count(report.rows):
        raise ValueError("input_count must match rows")
    if report.row_count != _decimal_count(report.rows):
        raise ValueError("row_count must match rows")
    if report.recovered_count != _row_status_count(report.rows, "recovered"):
        raise ValueError("recovered_count must match rows")
    if report.watch_count != _row_status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.breached_count != _row_status_count(report.rows, "breached"):
        raise ValueError("breached_count must match rows")
    if report.source_recovered_count != _source_status_count(report.rows, "recovered"):
        raise ValueError("source_recovered_count must match rows")
    if report.source_stale_count != _source_status_count(report.rows, "stale"):
        raise ValueError("source_stale_count must match rows")
    if report.source_missing_count != _source_status_count(report.rows, "missing"):
        raise ValueError("source_missing_count must match rows")
    if report.acknowledged_count != _acknowledgement_status_count(
        report.rows,
        "acknowledged",
    ):
        raise ValueError("acknowledged_count must match rows")
    if report.acknowledgement_late_count != _acknowledgement_status_count(
        report.rows,
        "late",
    ):
        raise ValueError("acknowledgement_late_count must match rows")
    if report.acknowledgement_missing_count != _acknowledgement_status_count(
        report.rows,
        "missing",
    ):
        raise ValueError("acknowledgement_missing_count must match rows")
    if report.contradiction_open_count != _contradiction_state_count(report.rows, "open"):
        raise ValueError("contradiction_open_count must match rows")
    if report.repeated_team_category_miss_count != _decimal_count(
        tuple(row for row in report.team_category_miss_rows if row.repeated_miss),
    ):
        raise ValueError("repeated_team_category_miss_count must match rows")
    if report.recovery_ratio != _recovery_ratio(report.rows):
        raise ValueError("recovery_ratio must match rows")
    if report.oldest_breach_age_seconds != _oldest_breach_age_seconds(report.rows):
        raise ValueError("oldest_breach_age_seconds must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _row_sort_key(
    row: MarketOutcomeFreshnessSlaRecheckRow,
) -> tuple[int, str, str, str, str]:
    return (
        RECHECK_STATUS_PRIORITY[row.recheck_status],
        row.team_id,
        row.category_id,
        row.market_id,
        row.outcome_id,
    )


def _team_category_miss_row_sort_key(
    row: MarketOutcomeFreshnessSlaRecheckTeamCategoryMissRow,
) -> tuple[int, Decimal, str, str]:
    return (
        0 if row.repeated_miss else 1,
        -row.miss_count,
        row.team_id,
        row.category_id,
    )


def _row_status_count(
    rows: tuple[MarketOutcomeFreshnessSlaRecheckRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(tuple(row for row in rows if row.recheck_status == status))


def _source_status_count(
    rows: tuple[MarketOutcomeFreshnessSlaRecheckRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(
        tuple(row for row in rows if row.source_freshness_status == status),
    )


def _acknowledgement_status_count(
    rows: tuple[MarketOutcomeFreshnessSlaRecheckRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(
        tuple(row for row in rows if row.acknowledgement_status == status),
    )


def _contradiction_state_count(
    rows: tuple[MarketOutcomeFreshnessSlaRecheckRow, ...],
    state: str,
) -> Decimal:
    return _decimal_count(tuple(row for row in rows if row.contradiction_state == state))


def _recovery_ratio(
    rows: tuple[MarketOutcomeFreshnessSlaRecheckRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    with localcontext(DECIMAL_CONTEXT):
        return (
            _row_status_count(rows, "recovered") / _decimal_count(rows)
        ).quantize(RATIO_QUANTUM)


def _oldest_breach_age_seconds(
    rows: tuple[MarketOutcomeFreshnessSlaRecheckRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return max(row.breach_age_seconds for row in rows)


def _decimal_count(values: tuple[object, ...]) -> Decimal:
    return Decimal(len(values))


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    if delta < timedelta(0):
        raise ValueError("datetime range must be nonnegative")
    seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    return _quantize_seconds(seconds)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_known_value(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be known")


def _require_finite_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _normalize_nonnegative_integral_decimal(
    field_name: str,
    value: object,
) -> Decimal:
    _require_finite_decimal(field_name, value)
    decimal_value = value
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return decimal_value


def _normalize_positive_integral_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_integral_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_nonnegative_seconds(field_name: str, value: object) -> Decimal:
    _require_finite_decimal(field_name, value)
    decimal_value = value
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize_seconds(decimal_value)


def _normalize_optional_nonnegative_seconds(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_seconds(field_name, value)


def _normalize_positive_seconds(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_seconds(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_optional_ratio(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    _require_finite_decimal(field_name, value)
    decimal_value = value
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value.quantize(RATIO_QUANTUM)


def _normalize_reason_codes(
    field_name: str,
    values: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        reason_codes = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in allowed_values:
            raise ValueError(f"{field_name} must contain known reason codes")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    expected_codes = tuple(code for code in allowed_values if code in reason_codes)
    if expected_codes != reason_codes:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _quantize_seconds(value: Decimal) -> Decimal:
    if not value.is_finite():
        raise ValueError("seconds value must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(SECOND_QUANTUM)


__all__ = (
    "MarketOutcomeFreshnessSlaRecheckConfig",
    "MarketOutcomeFreshnessSlaRecheckObservation",
    "MarketOutcomeFreshnessSlaRecheckRow",
    "MarketOutcomeFreshnessSlaRecheckTeamCategoryMissRow",
    "MarketOutcomeFreshnessSlaRecheckReport",
    "build_market_outcome_freshness_sla_recheck_report",
    "market_outcome_freshness_sla_recheck_report_payload",
)
