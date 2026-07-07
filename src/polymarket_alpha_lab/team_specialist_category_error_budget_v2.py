"""Phase 1 readonly team specialist category error budget report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_TEAM_SPECIALIST_CATEGORY_ERROR_BUDGET_V2_CONFIG_VERSION = (
    "team-specialist-category-error-budget-v2"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_SECONDS_PER_DAY = Decimal("86400.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_ERROR_BUDGET_STATUSES = frozenset(("pass", "watch", "blocked"))
_RECOVERY_PRIORITIES = frozenset(("low", "medium", "high", "critical"))
_STATUS_SORT_WEIGHT = {"blocked": 0, "watch": 1, "pass": 2}
_RECOVERY_PRIORITY_SORT_WEIGHT = {"critical": 0, "high": 1, "medium": 2, "low": 3}
_UNSAFE_PUBLIC_TERMS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)
_ROW_REASON_CODE_SEQUENCE = (
    "error_budget_pass",
    "error_budget_watch",
    "error_budget_blocked",
    "sample_size_sufficient",
    "sample_size_thin",
    "recent_forecast_misses_clear",
    "recent_forecast_misses_watch",
    "recent_forecast_misses_blocked",
    "brier_like_error_low",
    "brier_like_error_watch",
    "brier_like_error_high",
    "category_importance_low",
    "category_importance_medium",
    "category_importance_high",
    "source_contradiction_misses_clear",
    "source_contradiction_misses_watch",
    "source_contradiction_misses_blocked",
    "recovery_priority_low",
    "recovery_priority_medium",
    "recovery_priority_high",
    "recovery_priority_critical",
)
_REPORT_REASON_CODE_SEQUENCE = (
    "empty_error_budget_observations",
    "category_error_budget_passed",
    "category_error_budget_watch_rows",
    "category_error_budget_blocked_rows",
    "category_error_budget_recovery_priority_high",
)


@dataclass(frozen=True)
class TeamSpecialistCategoryErrorBudgetV2Config:
    config_version: str = DEFAULT_TEAM_SPECIALIST_CATEGORY_ERROR_BUDGET_V2_CONFIG_VERSION
    recent_window_days: Decimal = Decimal("7.000000")
    minimum_sample_size: Decimal = Decimal("3.000000")
    recent_miss_absolute_error_threshold: Decimal = Decimal("0.250000")
    recent_miss_watch_threshold: Decimal = Decimal("1.000000")
    recent_miss_blocked_threshold: Decimal = Decimal("2.000000")
    watch_brier_like_error_threshold: Decimal = Decimal("0.100000")
    blocked_brier_like_error_threshold: Decimal = Decimal("0.250000")
    source_contradiction_watch_threshold: Decimal = Decimal("1.000000")
    source_contradiction_blocked_threshold: Decimal = Decimal("2.000000")
    medium_category_importance_threshold: Decimal = Decimal("0.300000")
    high_category_importance_threshold: Decimal = Decimal("0.800000")
    medium_recovery_priority_score_floor: Decimal = Decimal("0.200000")
    high_recovery_priority_score_floor: Decimal = Decimal("0.500000")
    critical_recovery_priority_score_floor: Decimal = Decimal("0.800000")
    brier_pressure_weight: Decimal = Decimal("0.450000")
    recent_miss_pressure_weight: Decimal = Decimal("0.200000")
    source_contradiction_pressure_weight: Decimal = Decimal("0.200000")
    sample_gap_pressure_weight: Decimal = Decimal("0.050000")
    category_importance_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistCategoryErrorBudgetV2Config:
            raise TypeError(
                "TeamSpecialistCategoryErrorBudgetV2Config does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistCategoryErrorBudgetV2Config:
            raise ValueError(
                "config must be exactly TeamSpecialistCategoryErrorBudgetV2Config",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_TEAM_SPECIALIST_CATEGORY_ERROR_BUDGET_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "recent_window_days",
            "minimum_sample_size",
            "recent_miss_watch_threshold",
            "recent_miss_blocked_threshold",
            "source_contradiction_watch_threshold",
            "source_contradiction_blocked_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "recent_miss_absolute_error_threshold",
            "watch_brier_like_error_threshold",
            "blocked_brier_like_error_threshold",
            "medium_category_importance_threshold",
            "high_category_importance_threshold",
            "medium_recovery_priority_score_floor",
            "high_recovery_priority_score_floor",
            "critical_recovery_priority_score_floor",
            "brier_pressure_weight",
            "recent_miss_pressure_weight",
            "source_contradiction_pressure_weight",
            "sample_gap_pressure_weight",
            "category_importance_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class TeamSpecialistCategoryErrorBudgetV2Observation:
    team_id: str
    specialist_id: str
    category_id: str
    market_id: str
    forecast_probability: Decimal
    resolved_probability: Decimal
    category_importance: Decimal
    source_contradiction_miss: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistCategoryErrorBudgetV2Observation:
            raise TypeError(
                "TeamSpecialistCategoryErrorBudgetV2Observation does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistCategoryErrorBudgetV2Observation:
            raise ValueError(
                "observation must be exactly "
                "TeamSpecialistCategoryErrorBudgetV2Observation",
            )
        for field_name in ("team_id", "specialist_id", "category_id", "market_id"):
            _require_public_identifier(field_name, getattr(self, field_name))
        for field_name in (
            "forecast_probability",
            "resolved_probability",
            "category_importance",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_contradiction_miss",
            _require_binary_decimal(
                "source_contradiction_miss",
                self.source_contradiction_miss,
            ),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class TeamSpecialistCategoryErrorBudgetV2Row:
    rank: Decimal
    team_id: str
    specialist_id: str
    category_id: str
    sample_size: Decimal
    recent_forecast_miss_count: Decimal
    brier_like_error: Decimal
    category_importance: Decimal
    source_contradiction_miss_count: Decimal
    recovery_priority_score: Decimal
    recovery_priority: str
    error_budget_status: str
    latest_observed_at: datetime
    market_ids: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistCategoryErrorBudgetV2Row:
            raise TypeError(
                "TeamSpecialistCategoryErrorBudgetV2Row does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistCategoryErrorBudgetV2Row:
            raise ValueError("row must be exactly TeamSpecialistCategoryErrorBudgetV2Row")
        for field_name in ("team_id", "specialist_id", "category_id"):
            _require_public_identifier(field_name, getattr(self, field_name))
        for field_name in (
            "rank",
            "sample_size",
            "recent_forecast_miss_count",
            "source_contradiction_miss_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "brier_like_error",
            "category_importance",
            "recovery_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_recovery_priority("recovery_priority", self.recovery_priority)
        _require_error_budget_status("error_budget_status", self.error_budget_status)
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        object.__setattr__(
            self,
            "market_ids",
            _normalize_public_identifiers("market_ids", self.market_ids),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, _ROW_REASON_CODE_SEQUENCE),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class TeamSpecialistCategoryErrorBudgetV2Report:
    generated_at: datetime
    config_version: str
    error_budget_status: str
    row_count: Decimal
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    recent_forecast_miss_count: Decimal
    source_contradiction_miss_count: Decimal
    average_brier_like_error: Decimal
    max_recovery_priority_score: Decimal
    rows: tuple[TeamSpecialistCategoryErrorBudgetV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistCategoryErrorBudgetV2Report:
            raise TypeError(
                "TeamSpecialistCategoryErrorBudgetV2Report does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistCategoryErrorBudgetV2Report:
            raise ValueError(
                "report must be exactly TeamSpecialistCategoryErrorBudgetV2Report",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_TEAM_SPECIALIST_CATEGORY_ERROR_BUDGET_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_error_budget_status("error_budget_status", self.error_budget_status)
        for field_name in (
            "row_count",
            "observation_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "recent_forecast_miss_count",
            "source_contradiction_miss_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_brier_like_error", "max_recovery_priority_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, _REPORT_REASON_CODE_SEQUENCE),
        )
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
            "TeamSpecialistCategoryErrorBudgetV2Report.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_team_specialist_category_error_budget_v2_report(
    observations: Sequence[TeamSpecialistCategoryErrorBudgetV2Observation],
    *,
    generated_at: datetime,
    config: TeamSpecialistCategoryErrorBudgetV2Config | None = None,
) -> TeamSpecialistCategoryErrorBudgetV2Report:
    """Build a local Phase 1 report-only team/category forecast-error budget."""

    if config is None:
        config = TeamSpecialistCategoryErrorBudgetV2Config()
    if type(config) is not TeamSpecialistCategoryErrorBudgetV2Config:
        raise ValueError("config must be a TeamSpecialistCategoryErrorBudgetV2Config")
    generated_at = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    for observation in normalized_observations:
        if observation.observed_at > generated_at:
            raise ValueError("observation observed_at must not be after generated_at")
    rows = _rank_rows(_build_rows(normalized_observations, generated_at, config))
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "error_budget_status": _report_status(rows),
        "row_count": _decimal_count(len(rows)),
        "observation_count": _decimal_count(len(normalized_observations)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "blocked_count": _decimal_count(_status_count(rows, "blocked")),
        "recent_forecast_miss_count": _sum_rows(
            rows,
            "recent_forecast_miss_count",
        ),
        "source_contradiction_miss_count": _sum_rows(
            rows,
            "source_contradiction_miss_count",
        ),
        "average_brier_like_error": _average(
            tuple(_brier_like_error(observation) for observation in normalized_observations),
        ),
        "max_recovery_priority_score": _max_score(rows),
        "rows": rows,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return TeamSpecialistCategoryErrorBudgetV2Report(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def team_specialist_category_error_budget_v2_payload(
    report: TeamSpecialistCategoryErrorBudgetV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is TeamSpecialistCategoryErrorBudgetV2Report:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = report.payload
        _require_hard_flags("payload", _DictFlags(payload))
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report, allow_json_containers=True)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        _require_hard_flags("payload", _DictFlags(payload))
        return payload
    raise ValueError(
        "report must be a TeamSpecialistCategoryErrorBudgetV2Report or payload",
    )


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


def _build_rows(
    observations: tuple[TeamSpecialistCategoryErrorBudgetV2Observation, ...],
    generated_at: datetime,
    config: TeamSpecialistCategoryErrorBudgetV2Config,
) -> tuple[TeamSpecialistCategoryErrorBudgetV2Row, ...]:
    grouped: dict[
        tuple[str, str, str],
        list[TeamSpecialistCategoryErrorBudgetV2Observation],
    ] = {}
    for observation in observations:
        grouped.setdefault(
            (observation.team_id, observation.specialist_id, observation.category_id),
            [],
        ).append(observation)
    return tuple(
        _row_without_rank(team_id, specialist_id, category_id, tuple(items), generated_at, config)
        for (team_id, specialist_id, category_id), items in sorted(grouped.items())
    )


def _row_without_rank(
    team_id: str,
    specialist_id: str,
    category_id: str,
    observations: tuple[TeamSpecialistCategoryErrorBudgetV2Observation, ...],
    generated_at: datetime,
    config: TeamSpecialistCategoryErrorBudgetV2Config,
) -> TeamSpecialistCategoryErrorBudgetV2Row:
    sample_size = _decimal_count(len(observations))
    brier_like_error = _average(
        tuple(_brier_like_error(observation) for observation in observations),
    )
    category_importance = _average(
        tuple(observation.category_importance for observation in observations),
    )
    recent_forecast_miss_count = _recent_forecast_miss_count(
        observations,
        generated_at,
        config,
    )
    source_contradiction_miss_count = _quantize(
        sum(
            (observation.source_contradiction_miss for observation in observations),
            _ZERO,
        ),
    )
    error_budget_status = _row_status(
        sample_size=sample_size,
        recent_forecast_miss_count=recent_forecast_miss_count,
        brier_like_error=brier_like_error,
        source_contradiction_miss_count=source_contradiction_miss_count,
        config=config,
    )
    recovery_priority_score = _recovery_priority_score(
        sample_size=sample_size,
        recent_forecast_miss_count=recent_forecast_miss_count,
        brier_like_error=brier_like_error,
        category_importance=category_importance,
        source_contradiction_miss_count=source_contradiction_miss_count,
        config=config,
    )
    recovery_priority = _recovery_priority(
        recovery_priority_score=recovery_priority_score,
        category_importance=category_importance,
        error_budget_status=error_budget_status,
        config=config,
    )
    return TeamSpecialistCategoryErrorBudgetV2Row(
        rank=_ZERO,
        team_id=team_id,
        specialist_id=specialist_id,
        category_id=category_id,
        sample_size=sample_size,
        recent_forecast_miss_count=recent_forecast_miss_count,
        brier_like_error=brier_like_error,
        category_importance=category_importance,
        source_contradiction_miss_count=source_contradiction_miss_count,
        recovery_priority_score=recovery_priority_score,
        recovery_priority=recovery_priority,
        error_budget_status=error_budget_status,
        latest_observed_at=max(observation.observed_at for observation in observations),
        market_ids=tuple(sorted({observation.market_id for observation in observations})),
        reason_codes=_row_reason_codes(
            sample_size=sample_size,
            recent_forecast_miss_count=recent_forecast_miss_count,
            brier_like_error=brier_like_error,
            category_importance=category_importance,
            source_contradiction_miss_count=source_contradiction_miss_count,
            recovery_priority=recovery_priority,
            error_budget_status=error_budget_status,
            config=config,
        ),
    )


def _rank_rows(
    rows: tuple[TeamSpecialistCategoryErrorBudgetV2Row, ...],
) -> tuple[TeamSpecialistCategoryErrorBudgetV2Row, ...]:
    ranked_rows = []
    for index, row in enumerate(sorted(rows, key=_row_sort_key), start=1):
        ranked_rows.append(replace(row, rank=_decimal_count(index)))
    return tuple(ranked_rows)


def _row_sort_key(
    row: TeamSpecialistCategoryErrorBudgetV2Row,
) -> tuple[Decimal, int, int, Decimal, Decimal, str, str, str]:
    return (
        -row.recovery_priority_score,
        _RECOVERY_PRIORITY_SORT_WEIGHT[row.recovery_priority],
        _STATUS_SORT_WEIGHT[row.error_budget_status],
        -row.category_importance,
        -row.brier_like_error,
        row.team_id,
        row.specialist_id,
        row.category_id,
    )


def _absolute_error(
    observation: TeamSpecialistCategoryErrorBudgetV2Observation,
) -> Decimal:
    return _quantize(abs(observation.forecast_probability - observation.resolved_probability))


def _brier_like_error(
    observation: TeamSpecialistCategoryErrorBudgetV2Observation,
) -> Decimal:
    error = observation.forecast_probability - observation.resolved_probability
    return _quantize(error * error)


def _recent_forecast_miss_count(
    observations: tuple[TeamSpecialistCategoryErrorBudgetV2Observation, ...],
    generated_at: datetime,
    config: TeamSpecialistCategoryErrorBudgetV2Config,
) -> Decimal:
    recent_seconds = config.recent_window_days * _SECONDS_PER_DAY
    miss_count = 0
    for observation in observations:
        age_seconds = Decimal(str((generated_at - observation.observed_at).total_seconds()))
        if age_seconds < _ZERO or age_seconds > recent_seconds:
            continue
        if _absolute_error(observation) >= config.recent_miss_absolute_error_threshold:
            miss_count += 1
    return _decimal_count(miss_count)


def _row_status(
    *,
    sample_size: Decimal,
    recent_forecast_miss_count: Decimal,
    brier_like_error: Decimal,
    source_contradiction_miss_count: Decimal,
    config: TeamSpecialistCategoryErrorBudgetV2Config,
) -> str:
    if (
        sample_size < config.minimum_sample_size
        or recent_forecast_miss_count >= config.recent_miss_blocked_threshold
        or brier_like_error >= config.blocked_brier_like_error_threshold
        or source_contradiction_miss_count
        >= config.source_contradiction_blocked_threshold
    ):
        return "blocked"
    if (
        recent_forecast_miss_count >= config.recent_miss_watch_threshold
        or brier_like_error >= config.watch_brier_like_error_threshold
        or source_contradiction_miss_count
        >= config.source_contradiction_watch_threshold
    ):
        return "watch"
    return "pass"


def _recovery_priority_score(
    *,
    sample_size: Decimal,
    recent_forecast_miss_count: Decimal,
    brier_like_error: Decimal,
    category_importance: Decimal,
    source_contradiction_miss_count: Decimal,
    config: TeamSpecialistCategoryErrorBudgetV2Config,
) -> Decimal:
    sample_gap_pressure = _ZERO
    if sample_size < config.minimum_sample_size:
        sample_gap_pressure = _clamp_ratio(
            (config.minimum_sample_size - sample_size) / config.minimum_sample_size,
        )
    score = (
        _clamp_ratio(brier_like_error / config.blocked_brier_like_error_threshold)
        * config.brier_pressure_weight
        + _ratio(recent_forecast_miss_count, sample_size)
        * config.recent_miss_pressure_weight
        + _ratio(source_contradiction_miss_count, sample_size)
        * config.source_contradiction_pressure_weight
        + sample_gap_pressure * config.sample_gap_pressure_weight
        + category_importance * config.category_importance_weight
    )
    return _clamp_ratio(score)


def _recovery_priority(
    *,
    recovery_priority_score: Decimal,
    category_importance: Decimal,
    error_budget_status: str,
    config: TeamSpecialistCategoryErrorBudgetV2Config,
) -> str:
    if (
        recovery_priority_score >= config.critical_recovery_priority_score_floor
        or (
            error_budget_status == "blocked"
            and category_importance >= config.high_category_importance_threshold
        )
    ):
        return "critical"
    if (
        recovery_priority_score >= config.high_recovery_priority_score_floor
        or error_budget_status == "blocked"
    ):
        return "high"
    if (
        recovery_priority_score >= config.medium_recovery_priority_score_floor
        or error_budget_status == "watch"
    ):
        return "medium"
    return "low"


def _row_reason_codes(
    *,
    sample_size: Decimal,
    recent_forecast_miss_count: Decimal,
    brier_like_error: Decimal,
    category_importance: Decimal,
    source_contradiction_miss_count: Decimal,
    recovery_priority: str,
    error_budget_status: str,
    config: TeamSpecialistCategoryErrorBudgetV2Config,
) -> tuple[str, ...]:
    return _normalize_reason_codes(
        (
            f"error_budget_{error_budget_status}",
            _sample_reason(sample_size, config),
            _recent_miss_reason(recent_forecast_miss_count, config),
            _brier_reason(brier_like_error, config),
            _category_importance_reason(category_importance, config),
            _source_contradiction_reason(source_contradiction_miss_count, config),
            f"recovery_priority_{recovery_priority}",
        ),
        _ROW_REASON_CODE_SEQUENCE,
    )


def _sample_reason(
    sample_size: Decimal,
    config: TeamSpecialistCategoryErrorBudgetV2Config,
) -> str:
    if sample_size < config.minimum_sample_size:
        return "sample_size_thin"
    return "sample_size_sufficient"


def _recent_miss_reason(
    recent_forecast_miss_count: Decimal,
    config: TeamSpecialistCategoryErrorBudgetV2Config,
) -> str:
    if recent_forecast_miss_count >= config.recent_miss_blocked_threshold:
        return "recent_forecast_misses_blocked"
    if recent_forecast_miss_count >= config.recent_miss_watch_threshold:
        return "recent_forecast_misses_watch"
    return "recent_forecast_misses_clear"


def _brier_reason(
    brier_like_error: Decimal,
    config: TeamSpecialistCategoryErrorBudgetV2Config,
) -> str:
    if brier_like_error >= config.blocked_brier_like_error_threshold:
        return "brier_like_error_high"
    if brier_like_error >= config.watch_brier_like_error_threshold:
        return "brier_like_error_watch"
    return "brier_like_error_low"


def _category_importance_reason(
    category_importance: Decimal,
    config: TeamSpecialistCategoryErrorBudgetV2Config,
) -> str:
    if category_importance >= config.high_category_importance_threshold:
        return "category_importance_high"
    if category_importance >= config.medium_category_importance_threshold:
        return "category_importance_medium"
    return "category_importance_low"


def _source_contradiction_reason(
    source_contradiction_miss_count: Decimal,
    config: TeamSpecialistCategoryErrorBudgetV2Config,
) -> str:
    if (
        source_contradiction_miss_count
        >= config.source_contradiction_blocked_threshold
    ):
        return "source_contradiction_misses_blocked"
    if (
        source_contradiction_miss_count
        >= config.source_contradiction_watch_threshold
    ):
        return "source_contradiction_misses_watch"
    return "source_contradiction_misses_clear"


def _report_status(rows: tuple[TeamSpecialistCategoryErrorBudgetV2Row, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.error_budget_status == "blocked" for row in rows):
        return "blocked"
    if any(row.error_budget_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[TeamSpecialistCategoryErrorBudgetV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_error_budget_observations",)
    reason_codes: list[str] = []
    if all(row.error_budget_status == "pass" for row in rows):
        reason_codes.append("category_error_budget_passed")
    if any(row.error_budget_status == "watch" for row in rows):
        reason_codes.append("category_error_budget_watch_rows")
    if any(row.error_budget_status == "blocked" for row in rows):
        reason_codes.append("category_error_budget_blocked_rows")
    if any(row.recovery_priority in ("high", "critical") for row in rows):
        reason_codes.append("category_error_budget_recovery_priority_high")
    return _normalize_reason_codes(tuple(reason_codes), _REPORT_REASON_CODE_SEQUENCE)


def _status_count(
    rows: tuple[TeamSpecialistCategoryErrorBudgetV2Row, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.error_budget_status == status)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= _ZERO:
        return _ZERO
    return _clamp_ratio(numerator / denominator)


def _sum_rows(
    rows: tuple[TeamSpecialistCategoryErrorBudgetV2Row, ...],
    field_name: str,
) -> Decimal:
    return _quantize(sum((getattr(row, field_name) for row in rows), _ZERO))


def _max_score(rows: tuple[TeamSpecialistCategoryErrorBudgetV2Row, ...]) -> Decimal:
    if not rows:
        return _ZERO
    return max(row.recovery_priority_score for row in rows)


def _validate_config(config: TeamSpecialistCategoryErrorBudgetV2Config) -> None:
    if config.recent_miss_watch_threshold > config.recent_miss_blocked_threshold:
        raise ValueError(
            "recent_miss_watch_threshold must not exceed "
            "recent_miss_blocked_threshold",
        )
    if config.watch_brier_like_error_threshold > config.blocked_brier_like_error_threshold:
        raise ValueError(
            "watch_brier_like_error_threshold must not exceed "
            "blocked_brier_like_error_threshold",
        )
    if (
        config.source_contradiction_watch_threshold
        > config.source_contradiction_blocked_threshold
    ):
        raise ValueError(
            "source_contradiction_watch_threshold must not exceed "
            "source_contradiction_blocked_threshold",
        )
    if config.medium_category_importance_threshold > config.high_category_importance_threshold:
        raise ValueError(
            "medium_category_importance_threshold must not exceed "
            "high_category_importance_threshold",
        )
    if (
        config.medium_recovery_priority_score_floor
        > config.high_recovery_priority_score_floor
        or config.high_recovery_priority_score_floor
        > config.critical_recovery_priority_score_floor
    ):
        raise ValueError("recovery priority score floors must be monotonic")
    weights_total = _quantize(
        config.brier_pressure_weight
        + config.recent_miss_pressure_weight
        + config.source_contradiction_pressure_weight
        + config.sample_gap_pressure_weight
        + config.category_importance_weight,
    )
    if weights_total != _ONE:
        raise ValueError("recovery priority weights must sum to 1.000000")


def _validate_row_consistency(row: TeamSpecialistCategoryErrorBudgetV2Row) -> None:
    if row.recent_forecast_miss_count > row.sample_size:
        raise ValueError("recent_forecast_miss_count must not exceed sample_size")
    if row.source_contradiction_miss_count > row.sample_size:
        raise ValueError("source_contradiction_miss_count must not exceed sample_size")
    status_reason = f"error_budget_{row.error_budget_status}"
    if status_reason not in row.reason_codes:
        raise ValueError("rows must include their error budget status reason")
    priority_reason = f"recovery_priority_{row.recovery_priority}"
    if priority_reason not in row.reason_codes:
        raise ValueError("rows must include their recovery priority reason")


def _validate_report_consistency(
    report: TeamSpecialistCategoryErrorBudgetV2Report,
) -> None:
    rows = report.rows
    if report.row_count != _decimal_count(len(rows)):
        raise ValueError("row_count must match rows")
    if report.observation_count != _sum_rows(rows, "sample_size"):
        raise ValueError("observation_count must match rows")
    if report.pass_count != _decimal_count(_status_count(rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _decimal_count(_status_count(rows, "blocked")):
        raise ValueError("blocked_count must match rows")
    if report.recent_forecast_miss_count != _sum_rows(
        rows,
        "recent_forecast_miss_count",
    ):
        raise ValueError("recent_forecast_miss_count must match rows")
    if report.source_contradiction_miss_count != _sum_rows(
        rows,
        "source_contradiction_miss_count",
    ):
        raise ValueError("source_contradiction_miss_count must match rows")
    if report.max_recovery_priority_score != _max_score(rows):
        raise ValueError("max_recovery_priority_score must match rows")
    if report.error_budget_status != _report_status(rows):
        raise ValueError("error_budget_status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    _validate_rows_sorted(rows)


def _validate_rows_sorted(
    rows: tuple[TeamSpecialistCategoryErrorBudgetV2Row, ...],
) -> None:
    expected = tuple(sorted(rows, key=_row_sort_key))
    expected_ranks = tuple(_decimal_count(index) for index in range(1, len(rows) + 1))
    if rows != expected or tuple(row.rank for row in rows) != expected_ranks:
        raise ValueError("rows must be sorted by recovery priority and rank")


def _normalize_observations(
    observations: Sequence[TeamSpecialistCategoryErrorBudgetV2Observation],
) -> tuple[TeamSpecialistCategoryErrorBudgetV2Observation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Sequence):
        raise ValueError("observations must be a sequence")
    normalized: list[TeamSpecialistCategoryErrorBudgetV2Observation] = []
    seen_keys: set[tuple[str, str, str, str, datetime]] = set()
    for observation in observations:
        if type(observation) is not TeamSpecialistCategoryErrorBudgetV2Observation:
            raise ValueError(
                "observations must contain "
                "TeamSpecialistCategoryErrorBudgetV2Observation",
            )
        key = (
            observation.team_id,
            observation.specialist_id,
            observation.category_id,
            observation.market_id,
            observation.observed_at,
        )
        if key in seen_keys:
            raise ValueError("duplicate team/specialist/category/market observation")
        seen_keys.add(key)
        normalized.append(observation)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.team_id,
                item.specialist_id,
                item.category_id,
                item.observed_at,
                item.market_id,
            ),
        ),
    )


def _normalize_rows(
    rows: Sequence[TeamSpecialistCategoryErrorBudgetV2Row],
) -> tuple[TeamSpecialistCategoryErrorBudgetV2Row, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[TeamSpecialistCategoryErrorBudgetV2Row] = []
    for row in rows:
        if type(row) is not TeamSpecialistCategoryErrorBudgetV2Row:
            raise ValueError("rows must contain TeamSpecialistCategoryErrorBudgetV2Row")
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: row.rank))


def _normalize_public_identifiers(
    field_name: str,
    values: Sequence[str],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError(f"{field_name} must be a sequence")
    normalized: list[str] = []
    for value in values:
        normalized.append(_require_public_identifier(field_name, value))
    return tuple(sorted(dict.fromkeys(normalized)))


def _normalize_reason_codes(
    reason_codes: Sequence[str],
    supported: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in supported:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(reason_code for reason_code in supported if reason_code in normalized)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _require_error_budget_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _ERROR_BUDGET_STATUSES:
        raise ValueError(f"{field_name} must be a known error budget status")
    return value


def _require_recovery_priority(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _RECOVERY_PRIORITIES:
        raise ValueError(f"{field_name} must be a known recovery priority")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = _quantize(value)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_binary_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_ratio_decimal(field_name, value)
    if normalized not in (_ZERO, _ONE):
        raise ValueError(f"{field_name} must be 0.000000 or 1.000000")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _report_values_without_digest(
    report: TeamSpecialistCategoryErrorBudgetV2Report,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        payload,
        allow_json_containers=True,
    )
    encoded = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: object) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int:
        raise ValueError("numeric payload values must be Decimal strings")
    if type(value) is float:
        raise ValueError("payload must not contain float values")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload contains unsupported value")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{current_path} must be finite")
        return
    if type(value) is datetime or value is None or type(value) is bool:
        return
    if type(value) is float:
        raise ValueError(f"{current_path} must not be a float")
    if type(value) is int:
        raise ValueError(f"{current_path} must use numeric Decimal-derived string values")
    raise ValueError(f"{current_path} is not a supported public payload value")


__all__ = (
    "DEFAULT_TEAM_SPECIALIST_CATEGORY_ERROR_BUDGET_V2_CONFIG_VERSION",
    "TeamSpecialistCategoryErrorBudgetV2Config",
    "TeamSpecialistCategoryErrorBudgetV2Observation",
    "TeamSpecialistCategoryErrorBudgetV2Report",
    "TeamSpecialistCategoryErrorBudgetV2Row",
    "build_team_specialist_category_error_budget_v2_report",
    "team_specialist_category_error_budget_v2_payload",
)
