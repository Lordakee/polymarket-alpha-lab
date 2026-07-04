"""Pure Phase 1 reducer for strategy team forecast calibration memory."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags
from polymarket_alpha_lab.team_taxonomy import require_team_category_pair


DEFAULT_STRATEGY_TEAM_FORECAST_CALIBRATION_MEMORY_DIGEST_CONFIG_VERSION = (
    "strategy-team-forecast-calibration-memory-digest-v0"
)

SOURCE_REASON = "source_forecast_calibration_observed"
EMPTY_REASON = "strategy_team_forecast_calibration_memory_digest_empty_sources"
INSUFFICIENT_RESOLVED_REASON = (
    "strategy_team_forecast_calibration_memory_digest_insufficient_resolved_observations"
)
HIGH_BRIER_REASON = "strategy_team_forecast_calibration_memory_digest_high_brier_score"
DIRECTIONAL_BIAS_REASON = (
    "strategy_team_forecast_calibration_memory_digest_directional_bias"
)
STALE_PENDING_REASON = (
    "strategy_team_forecast_calibration_memory_digest_stale_pending_observations"
)
PASS_REASON = "strategy_team_forecast_calibration_memory_digest_passed"

SOURCE_REASON_CODES = (SOURCE_REASON,)
REASON_CODES = (
    EMPTY_REASON,
    INSUFFICIENT_RESOLVED_REASON,
    HIGH_BRIER_REASON,
    DIRECTIONAL_BIAS_REASON,
    STALE_PENDING_REASON,
    PASS_REASON,
)
REASON_CODE_RANK = {reason_code: index for index, reason_code in enumerate(REASON_CODES)}
BLOCKED_REASONS = (EMPTY_REASON, INSUFFICIENT_RESOLVED_REASON, HIGH_BRIER_REASON)
WATCH_REASONS = (DIRECTIONAL_BIAS_REASON, STALE_PENDING_REASON)
STATUSES = ("pass", "watch", "blocked")
NEXT_REVIEW_STEPS = {
    "pass": "reuse_forecast_calibration_memory",
    "watch": "review_forecast_calibration_memory",
    "blocked": "pause_forecast_calibration_memory_use",
}

COUNT_QUANT = Decimal("1")
RATIO_QUANT = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
REDACTED_REFERENCE = "[REDACTED_REFERENCE]"
UNSAFE_KEY_FRAGMENTS = (
    "au" + "th",
    "priv" + "ate" + "_" + "key",
    "wall" + "et",
    "acc" + "ount",
    "ord" + "er",
    "can" + "cel",
    "rep" + "lace",
    "sig" + "ning",
    "sec" + "ret",
)

__all__ = (
    "DEFAULT_STRATEGY_TEAM_FORECAST_CALIBRATION_MEMORY_DIGEST_CONFIG_VERSION",
    "StrategyTeamForecastCalibrationMemoryDigestConfig",
    "StrategyTeamForecastCalibrationMemoryDigestReasonCodeCount",
    "StrategyTeamForecastCalibrationMemoryDigestReport",
    "StrategyTeamForecastCalibrationMemoryDigestRollup",
    "StrategyTeamForecastCalibrationMemoryDigestRow",
    "StrategyTeamForecastCalibrationMemoryDigestSource",
    "build_strategy_team_forecast_calibration_memory_digest",
    "strategy_team_forecast_calibration_memory_digest_payload",
)


@dataclass(frozen=True)
class StrategyTeamForecastCalibrationMemoryDigestConfig:
    config_version: str = (
        DEFAULT_STRATEGY_TEAM_FORECAST_CALIBRATION_MEMORY_DIGEST_CONFIG_VERSION
    )
    min_resolved_observation_count: Decimal = Decimal("2")
    high_brier_score_threshold: Decimal = Decimal("0.250000")
    signed_error_watch_threshold: Decimal = Decimal("0.250000")
    stale_pending_age_seconds: Decimal = Decimal("604800")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_resolved_observation_count",
            _normalize_positive_count(
                "min_resolved_observation_count",
                self.min_resolved_observation_count,
            ),
        )
        object.__setattr__(
            self,
            "high_brier_score_threshold",
            _normalize_ratio(
                "high_brier_score_threshold",
                self.high_brier_score_threshold,
            ),
        )
        object.__setattr__(
            self,
            "signed_error_watch_threshold",
            _normalize_ratio(
                "signed_error_watch_threshold",
                self.signed_error_watch_threshold,
            ),
        )
        object.__setattr__(
            self,
            "stale_pending_age_seconds",
            _normalize_positive_count(
                "stale_pending_age_seconds",
                self.stale_pending_age_seconds,
            ),
        )
        require_paper_only_flags("strategy team forecast calibration memory config", self)


@dataclass(frozen=True)
class StrategyTeamForecastCalibrationMemoryDigestSource:
    team_id: str
    category_id: str
    forecast_id: str
    forecast_probability: Decimal
    observed_at: datetime
    resolved_at: datetime | None
    resolved_outcome: Decimal | None
    forecast_reference: str = field(repr=False)
    reason_codes: tuple[str, ...] = (SOURCE_REASON,)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        team_id, category_id = require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        object.__setattr__(self, "team_id", team_id)
        object.__setattr__(self, "category_id", category_id)
        _require_canonical_string("forecast_id", self.forecast_id)
        object.__setattr__(
            self,
            "forecast_probability",
            _normalize_ratio("forecast_probability", self.forecast_probability),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "resolved_at",
            _as_optional_utc("resolved_at", self.resolved_at),
        )
        object.__setattr__(
            self,
            "resolved_outcome",
            _normalize_optional_ratio("resolved_outcome", self.resolved_outcome),
        )
        object.__setattr__(
            self,
            "forecast_reference",
            _normalize_reference("forecast_reference", self.forecast_reference),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, SOURCE_REASON_CODES),
        )
        if (self.resolved_at is None) != (self.resolved_outcome is None):
            raise ValueError("resolved_at and resolved_outcome must be provided together")
        if self.resolved_at is not None and self.resolved_at < self.observed_at:
            raise ValueError("resolved_at must not be before observed_at")
        require_paper_only_flags("strategy team forecast calibration memory source", self)


@dataclass(frozen=True)
class StrategyTeamForecastCalibrationMemoryDigestRow:
    team_id: str
    category_id: str
    readiness_status: str
    observation_count: Decimal
    resolved_count: Decimal
    pending_count: Decimal
    pending_ratio: Decimal
    high_brier_count: Decimal
    stale_pending_count: Decimal
    insufficient_resolved_count: Decimal
    mean_brier_score: Decimal | None
    mean_signed_error: Decimal | None
    latest_observed_at: datetime
    latest_resolved_at: datetime | None
    redacted_forecast_references: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        team_id, category_id = require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        object.__setattr__(self, "team_id", team_id)
        object.__setattr__(self, "category_id", category_id)
        _require_status("readiness_status", self.readiness_status)
        for field_name in (
            "observation_count",
            "resolved_count",
            "pending_count",
            "high_brier_count",
            "stale_pending_count",
            "insufficient_resolved_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "pending_ratio",
            _normalize_ratio("pending_ratio", self.pending_ratio),
        )
        object.__setattr__(
            self,
            "mean_brier_score",
            _normalize_optional_ratio("mean_brier_score", self.mean_brier_score),
        )
        object.__setattr__(
            self,
            "mean_signed_error",
            _normalize_optional_signed_ratio("mean_signed_error", self.mean_signed_error),
        )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        object.__setattr__(
            self,
            "latest_resolved_at",
            _as_optional_utc("latest_resolved_at", self.latest_resolved_at),
        )
        object.__setattr__(
            self,
            "redacted_forecast_references",
            _normalize_redacted_references(self.redacted_forecast_references),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, REASON_CODES),
        )
        _validate_row(self)
        require_paper_only_flags("strategy team forecast calibration memory row", self)


@dataclass(frozen=True)
class StrategyTeamForecastCalibrationMemoryDigestRollup:
    rollup_kind: str
    rollup_key: str
    readiness_status: str
    row_count: Decimal
    observation_count: Decimal
    resolved_count: Decimal
    pending_count: Decimal
    high_brier_count: Decimal
    stale_pending_count: Decimal
    insufficient_resolved_count: Decimal
    mean_brier_score: Decimal | None
    mean_signed_error: Decimal | None
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_member("rollup_kind", self.rollup_kind, ("category", "team"))
        _require_canonical_string("rollup_key", self.rollup_key)
        _require_status("readiness_status", self.readiness_status)
        for field_name in (
            "row_count",
            "observation_count",
            "resolved_count",
            "pending_count",
            "high_brier_count",
            "stale_pending_count",
            "insufficient_resolved_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "mean_brier_score",
            _normalize_optional_ratio("mean_brier_score", self.mean_brier_score),
        )
        object.__setattr__(
            self,
            "mean_signed_error",
            _normalize_optional_signed_ratio("mean_signed_error", self.mean_signed_error),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, REASON_CODES),
        )
        _validate_rollup(self)
        require_paper_only_flags("strategy team forecast calibration memory rollup", self)


@dataclass(frozen=True)
class StrategyTeamForecastCalibrationMemoryDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_member("reason_code", self.reason_code, REASON_CODES)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        require_paper_only_flags(
            "strategy team forecast calibration memory reason count",
            self,
        )


@dataclass(frozen=True)
class StrategyTeamForecastCalibrationMemoryDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    next_review_step: str
    source_count: Decimal
    row_count: Decimal
    resolved_count: Decimal
    pending_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    high_brier_count: Decimal
    stale_pending_count: Decimal
    insufficient_resolved_count: Decimal
    mean_brier_score: Decimal | None
    mean_signed_error: Decimal | None
    rows: tuple[StrategyTeamForecastCalibrationMemoryDigestRow, ...]
    rollups: tuple[StrategyTeamForecastCalibrationMemoryDigestRollup, ...]
    reason_code_counts: tuple[
        StrategyTeamForecastCalibrationMemoryDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("next_review_step", self.next_review_step)
        for field_name in (
            "source_count",
            "row_count",
            "resolved_count",
            "pending_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "high_brier_count",
            "stale_pending_count",
            "insufficient_resolved_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "mean_brier_score",
            _normalize_optional_ratio("mean_brier_score", self.mean_brier_score),
        )
        object.__setattr__(
            self,
            "mean_signed_error",
            _normalize_optional_signed_ratio("mean_signed_error", self.mean_signed_error),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "rollups", _normalize_rollups(self.rollups))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, REASON_CODES),
        )
        _validate_report(self)
        require_paper_only_flags("strategy team forecast calibration memory report", self)


def build_strategy_team_forecast_calibration_memory_digest(
    sources: list[StrategyTeamForecastCalibrationMemoryDigestSource]
    | tuple[StrategyTeamForecastCalibrationMemoryDigestSource, ...],
    *,
    config: StrategyTeamForecastCalibrationMemoryDigestConfig,
    generated_at: datetime,
) -> StrategyTeamForecastCalibrationMemoryDigestReport:
    if type(config) is not StrategyTeamForecastCalibrationMemoryDigestConfig:
        raise ValueError(
            "config must be a StrategyTeamForecastCalibrationMemoryDigestConfig",
        )
    require_paper_only_flags("strategy team forecast calibration memory config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_sources = _normalize_sources(sources, generated_at=generated_at_utc)
    rows = _build_rows(
        normalized_sources,
        config=config,
        generated_at=generated_at_utc,
    )
    rollups = _build_rollups(rows)
    reason_codes = _report_reason_codes(rows)
    digest_status = _status_for_reason_codes(reason_codes)

    return StrategyTeamForecastCalibrationMemoryDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        next_review_step=NEXT_REVIEW_STEPS[digest_status],
        source_count=_decimal_count(len(normalized_sources)),
        row_count=_decimal_count(len(rows)),
        resolved_count=sum((row.resolved_count for row in rows), ZERO),
        pending_count=sum((row.pending_count for row in rows), ZERO),
        pass_count=_decimal_count(
            sum(1 for row in rows if row.readiness_status == "pass"),
        ),
        watch_count=_decimal_count(
            sum(1 for row in rows if row.readiness_status == "watch"),
        ),
        blocked_count=_decimal_count(
            sum(1 for row in rows if row.readiness_status == "blocked"),
        ),
        high_brier_count=sum((row.high_brier_count for row in rows), ZERO),
        stale_pending_count=sum((row.stale_pending_count for row in rows), ZERO),
        insufficient_resolved_count=sum(
            (row.insufficient_resolved_count for row in rows),
            ZERO,
        ),
        mean_brier_score=_weighted_row_average(rows, "mean_brier_score"),
        mean_signed_error=_weighted_row_average(rows, "mean_signed_error"),
        rows=rows,
        rollups=rollups,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def strategy_team_forecast_calibration_memory_digest_payload(
    value: object,
) -> dict[str, Any]:
    if isinstance(
        value,
        (
            StrategyTeamForecastCalibrationMemoryDigestConfig,
            StrategyTeamForecastCalibrationMemoryDigestSource,
            StrategyTeamForecastCalibrationMemoryDigestRow,
            StrategyTeamForecastCalibrationMemoryDigestRollup,
            StrategyTeamForecastCalibrationMemoryDigestReasonCodeCount,
            StrategyTeamForecastCalibrationMemoryDigestReport,
        ),
    ):
        require_paper_only_flags("strategy team forecast calibration memory payload", value)
    elif type(value) is not dict:
        raise ValueError(
            "value must be a strategy team forecast calibration memory dataclass "
            "or JSON object",
        )

    _reject_unsafe_payload_keys(value)
    payload = _payload_value(value)
    if type(payload) is not dict:
        raise ValueError(
            "strategy team forecast calibration memory payload must be a JSON object",
        )
    _validate_payload_flags(payload, "payload")
    _reject_unsafe_payload_keys(payload)
    return payload


def _normalize_sources(
    sources: list[StrategyTeamForecastCalibrationMemoryDigestSource]
    | tuple[StrategyTeamForecastCalibrationMemoryDigestSource, ...],
    *,
    generated_at: datetime,
) -> tuple[StrategyTeamForecastCalibrationMemoryDigestSource, ...]:
    if type(sources) not in (list, tuple):
        raise ValueError("sources must be a list or tuple")
    normalized_sources = tuple(sources)
    seen_forecast_ids: set[str] = set()
    for source in normalized_sources:
        if type(source) is not StrategyTeamForecastCalibrationMemoryDigestSource:
            raise ValueError(
                "sources must contain StrategyTeamForecastCalibrationMemoryDigestSource",
            )
        require_paper_only_flags("strategy team forecast calibration memory source", source)
        if source.forecast_id in seen_forecast_ids:
            raise ValueError("forecast_id values must be unique")
        seen_forecast_ids.add(source.forecast_id)
        if source.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        if source.resolved_at is not None and source.resolved_at > generated_at:
            raise ValueError("resolved_at must not be after generated_at")
    return tuple(
        sorted(
            normalized_sources,
            key=lambda source: (source.team_id, source.category_id, source.forecast_id),
        )
    )


def _build_rows(
    sources: tuple[StrategyTeamForecastCalibrationMemoryDigestSource, ...],
    *,
    config: StrategyTeamForecastCalibrationMemoryDigestConfig,
    generated_at: datetime,
) -> tuple[StrategyTeamForecastCalibrationMemoryDigestRow, ...]:
    grouped: dict[tuple[str, str], list[StrategyTeamForecastCalibrationMemoryDigestSource]] = {}
    for source in sources:
        grouped.setdefault((source.team_id, source.category_id), []).append(source)
    return tuple(
        _build_row(
            team_id=team_id,
            category_id=category_id,
            sources=tuple(grouped[(team_id, category_id)]),
            config=config,
            generated_at=generated_at,
        )
        for team_id, category_id in sorted(grouped)
    )


def _build_row(
    *,
    team_id: str,
    category_id: str,
    sources: tuple[StrategyTeamForecastCalibrationMemoryDigestSource, ...],
    config: StrategyTeamForecastCalibrationMemoryDigestConfig,
    generated_at: datetime,
) -> StrategyTeamForecastCalibrationMemoryDigestRow:
    resolved_sources = tuple(source for source in sources if source.resolved_outcome is not None)
    pending_sources = tuple(source for source in sources if source.resolved_outcome is None)
    brier_scores = tuple(_brier_score(source) for source in resolved_sources)
    signed_errors = tuple(_signed_error(source) for source in resolved_sources)
    resolved_count = _decimal_count(len(resolved_sources))
    pending_count = _decimal_count(len(pending_sources))
    observation_count = _decimal_count(len(sources))
    high_brier_count = _decimal_count(
        sum(1 for score in brier_scores if score > config.high_brier_score_threshold),
    )
    stale_pending_count = _decimal_count(
        sum(
            1
            for source in pending_sources
            if _age_seconds(generated_at, source.observed_at)
            > config.stale_pending_age_seconds
        ),
    )
    insufficient_resolved_count = (
        ONE if resolved_count < config.min_resolved_observation_count else ZERO
    )
    mean_brier_score = _average_decimal(brier_scores)
    mean_signed_error = _average_decimal(signed_errors)
    pending_ratio = (pending_count / observation_count).quantize(
        RATIO_QUANT,
        rounding=ROUND_HALF_EVEN,
    )
    reason_codes = _row_reason_codes(
        high_brier_count=high_brier_count,
        stale_pending_count=stale_pending_count,
        insufficient_resolved_count=insufficient_resolved_count,
        mean_signed_error=mean_signed_error,
        config=config,
    )
    resolved_at_values = tuple(
        source.resolved_at for source in resolved_sources if source.resolved_at is not None
    )

    return StrategyTeamForecastCalibrationMemoryDigestRow(
        team_id=team_id,
        category_id=category_id,
        readiness_status=_status_for_reason_codes(reason_codes),
        observation_count=observation_count,
        resolved_count=resolved_count,
        pending_count=pending_count,
        pending_ratio=pending_ratio,
        high_brier_count=high_brier_count,
        stale_pending_count=stale_pending_count,
        insufficient_resolved_count=insufficient_resolved_count,
        mean_brier_score=mean_brier_score,
        mean_signed_error=mean_signed_error,
        latest_observed_at=max(source.observed_at for source in sources),
        latest_resolved_at=max(resolved_at_values, default=None),
        redacted_forecast_references=tuple(
            sorted(
                {
                    _redact_reference(source.forecast_reference)
                    for source in sources
                    if source.forecast_reference
                }
            )
        ),
        reason_codes=reason_codes,
    )


def _build_rollups(
    rows: tuple[StrategyTeamForecastCalibrationMemoryDigestRow, ...],
) -> tuple[StrategyTeamForecastCalibrationMemoryDigestRollup, ...]:
    rollups: list[StrategyTeamForecastCalibrationMemoryDigestRollup] = []
    for rollup_kind, key_getter in (
        ("category", lambda row: row.category_id),
        ("team", lambda row: row.team_id),
    ):
        grouped: dict[str, list[StrategyTeamForecastCalibrationMemoryDigestRow]] = {}
        for row in rows:
            grouped.setdefault(key_getter(row), []).append(row)
        for rollup_key in sorted(grouped):
            rollups.append(
                _build_rollup(
                    rollup_kind=rollup_kind,
                    rollup_key=rollup_key,
                    rows=tuple(grouped[rollup_key]),
                )
            )
    return tuple(rollups)


def _build_rollup(
    *,
    rollup_kind: str,
    rollup_key: str,
    rows: tuple[StrategyTeamForecastCalibrationMemoryDigestRow, ...],
) -> StrategyTeamForecastCalibrationMemoryDigestRollup:
    reason_codes = _combined_reason_codes(
        tuple(reason_code for row in rows for reason_code in row.reason_codes),
    )
    return StrategyTeamForecastCalibrationMemoryDigestRollup(
        rollup_kind=rollup_kind,
        rollup_key=rollup_key,
        readiness_status=_status_for_reason_codes(reason_codes),
        row_count=_decimal_count(len(rows)),
        observation_count=sum((row.observation_count for row in rows), ZERO),
        resolved_count=sum((row.resolved_count for row in rows), ZERO),
        pending_count=sum((row.pending_count for row in rows), ZERO),
        high_brier_count=sum((row.high_brier_count for row in rows), ZERO),
        stale_pending_count=sum((row.stale_pending_count for row in rows), ZERO),
        insufficient_resolved_count=sum(
            (row.insufficient_resolved_count for row in rows),
            ZERO,
        ),
        mean_brier_score=_weighted_row_average(rows, "mean_brier_score"),
        mean_signed_error=_weighted_row_average(rows, "mean_signed_error"),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    high_brier_count: Decimal,
    stale_pending_count: Decimal,
    insufficient_resolved_count: Decimal,
    mean_signed_error: Decimal | None,
    config: StrategyTeamForecastCalibrationMemoryDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if insufficient_resolved_count > ZERO:
        reason_codes.append(INSUFFICIENT_RESOLVED_REASON)
    if high_brier_count > ZERO:
        reason_codes.append(HIGH_BRIER_REASON)
    if (
        mean_signed_error is not None
        and abs(mean_signed_error) >= config.signed_error_watch_threshold
    ):
        reason_codes.append(DIRECTIONAL_BIAS_REASON)
    if stale_pending_count > ZERO:
        reason_codes.append(STALE_PENDING_REASON)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return _combined_reason_codes(tuple(reason_codes))


def _report_reason_codes(
    rows: tuple[StrategyTeamForecastCalibrationMemoryDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    return _combined_reason_codes(tuple(code for row in rows for code in row.reason_codes))


def _combined_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if any(reason_code != PASS_REASON for reason_code in reason_codes):
        reason_codes = tuple(
            reason_code for reason_code in reason_codes if reason_code != PASS_REASON
        )
    return tuple(
        sorted(
            set(reason_codes),
            key=lambda reason_code: REASON_CODE_RANK[reason_code],
        )
    )


def _reason_code_counts(
    rows: tuple[StrategyTeamForecastCalibrationMemoryDigestRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[StrategyTeamForecastCalibrationMemoryDigestReasonCodeCount, ...]:
    if reason_codes == (EMPTY_REASON,):
        return (
            StrategyTeamForecastCalibrationMemoryDigestReasonCodeCount(
                reason_code=EMPTY_REASON,
                count=ONE,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code in reason_codes:
                counter[reason_code] += 1
    return tuple(
        StrategyTeamForecastCalibrationMemoryDigestReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counter[reason_code]),
        )
        for reason_code in reason_codes
    )


def _status_for_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKED_REASONS for reason_code in reason_codes):
        return "blocked"
    if any(reason_code in WATCH_REASONS for reason_code in reason_codes):
        return "watch"
    return "pass"


def _validate_row(row: StrategyTeamForecastCalibrationMemoryDigestRow) -> None:
    if row.observation_count != row.resolved_count + row.pending_count:
        raise ValueError("observation_count must match resolved_count and pending_count")
    if row.observation_count <= ZERO:
        raise ValueError("observation_count must be positive")
    expected_pending_ratio = (row.pending_count / row.observation_count).quantize(
        RATIO_QUANT,
        rounding=ROUND_HALF_EVEN,
    )
    if row.pending_ratio != expected_pending_ratio:
        raise ValueError("pending_ratio must match row counts")
    for field_name in (
        "high_brier_count",
        "stale_pending_count",
        "insufficient_resolved_count",
    ):
        if getattr(row, field_name) > row.observation_count:
            raise ValueError(f"{field_name} cannot exceed observation_count")
    if row.resolved_count == ZERO:
        if row.mean_brier_score is not None or row.mean_signed_error is not None:
            raise ValueError("mean values require resolved observations")
    elif row.mean_brier_score is None or row.mean_signed_error is None:
        raise ValueError("mean values are required for resolved observations")
    _validate_reason_metrics(
        readiness_status=row.readiness_status,
        reason_codes=row.reason_codes,
        high_brier_count=row.high_brier_count,
        stale_pending_count=row.stale_pending_count,
        insufficient_resolved_count=row.insufficient_resolved_count,
        mean_signed_error=row.mean_signed_error,
    )


def _validate_rollup(rollup: StrategyTeamForecastCalibrationMemoryDigestRollup) -> None:
    if rollup.row_count <= ZERO:
        raise ValueError("row_count must be positive for rollups")
    if rollup.observation_count != rollup.resolved_count + rollup.pending_count:
        raise ValueError("observation_count must match resolved_count and pending_count")
    if rollup.readiness_status != _status_for_reason_codes(rollup.reason_codes):
        raise ValueError("readiness_status must match reason_codes")
    if rollup.resolved_count == ZERO:
        if rollup.mean_brier_score is not None or rollup.mean_signed_error is not None:
            raise ValueError("mean values require resolved observations")
    elif rollup.mean_brier_score is None or rollup.mean_signed_error is None:
        raise ValueError("mean values are required for resolved observations")


def _validate_report(report: StrategyTeamForecastCalibrationMemoryDigestReport) -> None:
    if report.source_count != sum((row.observation_count for row in report.rows), ZERO):
        raise ValueError("source_count must match rows")
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.resolved_count != sum((row.resolved_count for row in report.rows), ZERO):
        raise ValueError("resolved_count must match rows")
    if report.pending_count != sum((row.pending_count for row in report.rows), ZERO):
        raise ValueError("pending_count must match rows")
    if report.pass_count != _decimal_count(
        sum(1 for row in report.rows if row.readiness_status == "pass"),
    ):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(
        sum(1 for row in report.rows if row.readiness_status == "watch"),
    ):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _decimal_count(
        sum(1 for row in report.rows if row.readiness_status == "blocked"),
    ):
        raise ValueError("blocked_count must match rows")
    if report.high_brier_count != sum((row.high_brier_count for row in report.rows), ZERO):
        raise ValueError("high_brier_count must match rows")
    if report.stale_pending_count != sum(
        (row.stale_pending_count for row in report.rows),
        ZERO,
    ):
        raise ValueError("stale_pending_count must match rows")
    if report.insufficient_resolved_count != sum(
        (row.insufficient_resolved_count for row in report.rows),
        ZERO,
    ):
        raise ValueError("insufficient_resolved_count must match rows")
    if report.mean_brier_score != _weighted_row_average(report.rows, "mean_brier_score"):
        raise ValueError("mean_brier_score must match rows")
    if report.mean_signed_error != _weighted_row_average(report.rows, "mean_signed_error"):
        raise ValueError("mean_signed_error must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.digest_status != _status_for_reason_codes(report.reason_codes):
        raise ValueError("digest_status must match reason_codes")
    if report.next_review_step != NEXT_REVIEW_STEPS[report.digest_status]:
        raise ValueError("next_review_step must match digest_status")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")
    if report.rollups != _build_rollups(report.rows):
        raise ValueError("rollups must match rows")


def _validate_reason_metrics(
    *,
    readiness_status: str,
    reason_codes: tuple[str, ...],
    high_brier_count: Decimal,
    stale_pending_count: Decimal,
    insufficient_resolved_count: Decimal,
    mean_signed_error: Decimal | None,
) -> None:
    if readiness_status != _status_for_reason_codes(reason_codes):
        raise ValueError("readiness_status must match reason_codes")
    if high_brier_count > ZERO and HIGH_BRIER_REASON not in reason_codes:
        raise ValueError("reason_codes must include high brier reason")
    if stale_pending_count > ZERO and STALE_PENDING_REASON not in reason_codes:
        raise ValueError("reason_codes must include stale pending reason")
    if (
        insufficient_resolved_count > ZERO
        and INSUFFICIENT_RESOLVED_REASON not in reason_codes
    ):
        raise ValueError("reason_codes must include insufficient resolved reason")
    if reason_codes == (PASS_REASON,) and (
        high_brier_count > ZERO
        or stale_pending_count > ZERO
        or insufficient_resolved_count > ZERO
        or mean_signed_error is None
    ):
        raise ValueError("pass reason_codes must match clean resolved metrics")


def _normalize_rows(
    rows: tuple[StrategyTeamForecastCalibrationMemoryDigestRow, ...],
) -> tuple[StrategyTeamForecastCalibrationMemoryDigestRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized_rows = tuple(rows)
    seen_keys: set[tuple[str, str]] = set()
    for row in normalized_rows:
        if type(row) is not StrategyTeamForecastCalibrationMemoryDigestRow:
            raise ValueError(
                "rows must contain StrategyTeamForecastCalibrationMemoryDigestRow",
            )
        require_paper_only_flags("strategy team forecast calibration memory row", row)
        key = (row.team_id, row.category_id)
        if key in seen_keys:
            raise ValueError("rows team/category values must be unique")
        seen_keys.add(key)
    if normalized_rows != tuple(
        sorted(normalized_rows, key=lambda row: (row.team_id, row.category_id))
    ):
        raise ValueError("rows must be deterministically sorted")
    return normalized_rows


def _normalize_rollups(
    rollups: tuple[StrategyTeamForecastCalibrationMemoryDigestRollup, ...],
) -> tuple[StrategyTeamForecastCalibrationMemoryDigestRollup, ...]:
    if type(rollups) not in (list, tuple):
        raise ValueError("rollups must be a list or tuple")
    normalized_rollups = tuple(rollups)
    seen_keys: set[tuple[str, str]] = set()
    for rollup in normalized_rollups:
        if type(rollup) is not StrategyTeamForecastCalibrationMemoryDigestRollup:
            raise ValueError(
                "rollups must contain StrategyTeamForecastCalibrationMemoryDigestRollup",
            )
        require_paper_only_flags("strategy team forecast calibration memory rollup", rollup)
        key = (rollup.rollup_kind, rollup.rollup_key)
        if key in seen_keys:
            raise ValueError("rollups values must be unique")
        seen_keys.add(key)
    if normalized_rollups != tuple(
        sorted(
            normalized_rollups,
            key=lambda rollup: (rollup.rollup_kind, rollup.rollup_key),
        )
    ):
        raise ValueError("rollups must be deterministically sorted")
    return normalized_rollups


def _normalize_reason_code_counts(
    counts: tuple[StrategyTeamForecastCalibrationMemoryDigestReasonCodeCount, ...],
) -> tuple[StrategyTeamForecastCalibrationMemoryDigestReasonCodeCount, ...]:
    if type(counts) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized_counts = tuple(counts)
    seen_reason_codes: set[str] = set()
    for count in normalized_counts:
        if type(count) is not StrategyTeamForecastCalibrationMemoryDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "StrategyTeamForecastCalibrationMemoryDigestReasonCodeCount",
            )
        require_paper_only_flags(
            "strategy team forecast calibration memory reason count",
            count,
        )
        if count.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen_reason_codes.add(count.reason_code)
    if normalized_counts != tuple(
        sorted(
            normalized_counts,
            key=lambda count: REASON_CODE_RANK[count.reason_code],
        )
    ):
        raise ValueError("reason_code_counts must be deterministically sorted")
    return normalized_counts


def _normalize_reason_codes(value: object, allowed: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_member("reason_codes", reason_code, allowed)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    stable_codes = tuple(reason_code for reason_code in allowed if reason_code in reason_codes)
    if stable_codes != reason_codes:
        raise ValueError("reason_codes must be deterministic")
    return reason_codes


def _normalize_reference(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value and value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    return value


def _normalize_redacted_references(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("redacted_forecast_references must be a list or tuple")
    references = tuple(value)
    for reference in references:
        if reference != REDACTED_REFERENCE:
            raise ValueError("redacted_forecast_references must be redacted")
    if len(set(references)) != len(references):
        raise ValueError("redacted_forecast_references must be unique")
    if references != tuple(sorted(references)):
        raise ValueError("redacted_forecast_references must be sorted")
    return references


def _payload_value(value: object) -> object:
    if type(value) is bool or value is None or type(value) is str:
        return value
    if type(value) is int:
        raise ValueError("payload must not contain integer values")
    if type(value) is float:
        raise ValueError("payload must not contain float values")
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal values must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is StrategyTeamForecastCalibrationMemoryDigestSource:
        return _source_payload(value)
    if is_dataclass(value) and not isinstance(value, type):
        return {
            item.name: _payload_value(getattr(value, item.name))
            for item in fields(value)
        }
    if type(value) is dict:
        return _payload_dict(value)
    if type(value) in (list, tuple):
        return [_payload_value(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _source_payload(
    source: StrategyTeamForecastCalibrationMemoryDigestSource,
) -> dict[str, object]:
    return {
        "team_id": source.team_id,
        "category_id": source.category_id,
        "forecast_id": source.forecast_id,
        "forecast_probability": _payload_value(source.forecast_probability),
        "observed_at": _payload_value(source.observed_at),
        "resolved_at": _payload_value(source.resolved_at),
        "resolved_outcome": _payload_value(source.resolved_outcome),
        "redacted_forecast_reference": _redact_reference(source.forecast_reference),
        "reason_codes": _payload_value(source.reason_codes),
        "paper_only": source.paper_only,
        "report_only": source.report_only,
        "readonly": source.readonly,
    }


def _payload_dict(value: dict[Any, Any]) -> dict[str, object]:
    payload: dict[str, object] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError("payload keys must be strings")
        if key == "forecast_reference":
            payload["redacted_forecast_reference"] = _redact_payload_reference(item)
        elif key.endswith("_reference") and type(item) is str:
            payload[key] = _redact_reference(item)
        elif key.endswith("_references") and type(item) in (list, tuple):
            payload[key] = [_redact_payload_reference(reference) for reference in item]
        else:
            payload[key] = _payload_value(item)
    return payload


def _redact_payload_reference(value: object) -> str:
    if type(value) is not str:
        raise ValueError("reference payload values must be strings")
    return _redact_reference(value)


def _validate_payload_flags(value: object, field_path: str) -> None:
    if type(value) is dict:
        for flag in ("paper_only", "report_only", "readonly"):
            if flag not in value:
                raise ValueError(f"{field_path}.{flag} must be present")
            if value[flag] is not True:
                raise ValueError(f"{field_path}.{flag} must be True")
        for key, item in value.items():
            if type(item) is dict:
                _validate_payload_flags(item, f"{field_path}.{key}")
            elif type(item) is list:
                for index, nested_item in enumerate(item):
                    if type(nested_item) is dict:
                        _validate_payload_flags(nested_item, f"{field_path}.{key}.{index}")


def _reject_unsafe_payload_keys(value: object) -> None:
    for key in _iter_payload_keys(value):
        normalized_key = key.lower()
        if any(fragment in normalized_key for fragment in UNSAFE_KEY_FRAGMENTS):
            raise ValueError(f"unsafe surface field in payload: {key}")


def _iter_payload_keys(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        keys: list[str] = []
        for item in fields(value):
            keys.append(item.name)
            keys.extend(_iter_payload_keys(getattr(value, item.name)))
        return tuple(keys)
    if type(value) is dict:
        keys = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            keys.append(key)
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    if type(value) in (list, tuple):
        keys = []
        for item in value:
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    return ()


def _brier_score(source: StrategyTeamForecastCalibrationMemoryDigestSource) -> Decimal:
    if source.resolved_outcome is None:
        raise ValueError("resolved_outcome is required for brier score")
    return _quantize_ratio((source.forecast_probability - source.resolved_outcome) ** 2)


def _signed_error(source: StrategyTeamForecastCalibrationMemoryDigestSource) -> Decimal:
    if source.resolved_outcome is None:
        raise ValueError("resolved_outcome is required for signed error")
    return _quantize_ratio(source.forecast_probability - source.resolved_outcome)


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return _quantize_ratio(sum(values, ZERO) / _decimal_count(len(values)))


def _weighted_row_average(
    rows: tuple[
        StrategyTeamForecastCalibrationMemoryDigestRow
        | StrategyTeamForecastCalibrationMemoryDigestRollup,
        ...,
    ],
    field_name: str,
) -> Decimal | None:
    total = ZERO
    weight = ZERO
    for row in rows:
        value = getattr(row, field_name)
        if value is not None and row.resolved_count > ZERO:
            total += value * row.resolved_count
            weight += row.resolved_count
    if weight == ZERO:
        return None
    return _quantize_ratio(total / weight)


def _age_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    micros = (
        Decimal(delta.days * 86400 + delta.seconds) * MICROSECONDS_PER_SECOND
        + Decimal(delta.microseconds)
    )
    return _normalize_nonnegative_decimal(
        "age_seconds",
        (micros / MICROSECONDS_PER_SECOND).quantize(
            RATIO_QUANT,
            rounding=ROUND_HALF_EVEN,
        ),
    )


def _redact_reference(value: str) -> str:
    if not value:
        return ""
    return REDACTED_REFERENCE


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANT)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is float:
        raise ValueError(f"{field_name} must not be a float")
    if type(value) is int:
        raise ValueError(f"{field_name} must not be an integer")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(COUNT_QUANT)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    if quantized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is float:
        raise ValueError(f"{field_name} must not be a float")
    if type(value) is int:
        raise ValueError(f"{field_name} must not be an integer")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = _quantize_ratio(value)
    if quantized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is float:
        raise ValueError(f"{field_name} must not be a float")
    if type(value) is int:
        raise ValueError(f"{field_name} must not be an integer")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = _quantize_ratio(value)
    if quantized < ZERO or quantized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return quantized


def _normalize_optional_ratio(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_ratio(field_name, value)


def _normalize_optional_signed_ratio(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    if type(value) is float:
        raise ValueError(f"{field_name} must not be a float")
    if type(value) is int:
        raise ValueError(f"{field_name} must not be an integer")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = _quantize_ratio(value)
    if quantized < -ONE or quantized > ONE:
        raise ValueError(f"{field_name} must be between -1 and 1")
    return quantized


def _quantize_ratio(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANT, rounding=ROUND_HALF_EVEN)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")


def _require_status(field_name: str, value: object) -> None:
    _require_member(field_name, value, STATUSES)


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
