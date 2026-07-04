"""Pure Phase 1 LNG storage constraint digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_LNG_STORAGE_CONSTRAINT_DIGEST_CONFIG_VERSION = (
    "market-research-energy-lng-storage-constraint-digest-v0"
)

ROW_STATUSES = ("pass", "watch", "blocked")
DIGEST_STATUSES = ("pass", "watch", "blocked")
STATUS_RANK = {"blocked": 0, "watch": 1, "pass": 2}

ROW_REASON_CODES = (
    "lng_storage_constraint_all_sources_stale",
    "lng_storage_constraint_source_quorum_gap",
    "lng_storage_constraint_high_storage_utilization",
    "lng_storage_constraint_elevated_storage_utilization",
    "lng_storage_constraint_sendout_constrained",
    "lng_storage_constraint_sendout_tight",
    "lng_storage_constraint_cargo_queue_blocked",
    "lng_storage_constraint_cargo_queue_watch",
    "lng_storage_constraint_feedgas_drop_blocked",
    "lng_storage_constraint_feedgas_drop_watch",
    "lng_storage_constraint_weather_demand_pressure",
    "lng_storage_constraint_weather_demand_watch",
    "lng_storage_constraint_upstream_source_correction",
    "lng_storage_constraint_inline",
)

REPORT_REASON_CODES = (
    "lng_storage_constraint_digest_empty",
    "lng_storage_constraint_clear",
    "lng_storage_constraint_blocked_present",
    "lng_storage_constraint_watch_present",
    "lng_storage_constraint_source_quorum_gap_present",
    "lng_storage_constraint_all_sources_stale_present",
    "lng_storage_constraint_high_storage_utilization_present",
    "lng_storage_constraint_elevated_storage_utilization_present",
    "lng_storage_constraint_sendout_constrained_present",
    "lng_storage_constraint_sendout_tight_present",
    "lng_storage_constraint_cargo_queue_blocked_present",
    "lng_storage_constraint_cargo_queue_watch_present",
    "lng_storage_constraint_feedgas_drop_blocked_present",
    "lng_storage_constraint_feedgas_drop_watch_present",
    "lng_storage_constraint_weather_demand_pressure_present",
    "lng_storage_constraint_weather_demand_watch_present",
    "lng_storage_constraint_upstream_source_correction_present",
)

REPORT_REASON_TO_ROW_REASON = {
    "lng_storage_constraint_source_quorum_gap_present": (
        "lng_storage_constraint_source_quorum_gap"
    ),
    "lng_storage_constraint_all_sources_stale_present": (
        "lng_storage_constraint_all_sources_stale"
    ),
    "lng_storage_constraint_high_storage_utilization_present": (
        "lng_storage_constraint_high_storage_utilization"
    ),
    "lng_storage_constraint_elevated_storage_utilization_present": (
        "lng_storage_constraint_elevated_storage_utilization"
    ),
    "lng_storage_constraint_sendout_constrained_present": (
        "lng_storage_constraint_sendout_constrained"
    ),
    "lng_storage_constraint_sendout_tight_present": (
        "lng_storage_constraint_sendout_tight"
    ),
    "lng_storage_constraint_cargo_queue_blocked_present": (
        "lng_storage_constraint_cargo_queue_blocked"
    ),
    "lng_storage_constraint_cargo_queue_watch_present": (
        "lng_storage_constraint_cargo_queue_watch"
    ),
    "lng_storage_constraint_feedgas_drop_blocked_present": (
        "lng_storage_constraint_feedgas_drop_blocked"
    ),
    "lng_storage_constraint_feedgas_drop_watch_present": (
        "lng_storage_constraint_feedgas_drop_watch"
    ),
    "lng_storage_constraint_weather_demand_pressure_present": (
        "lng_storage_constraint_weather_demand_pressure"
    ),
    "lng_storage_constraint_weather_demand_watch_present": (
        "lng_storage_constraint_weather_demand_watch"
    ),
    "lng_storage_constraint_upstream_source_correction_present": (
        "lng_storage_constraint_upstream_source_correction"
    ),
}

QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
HALF = Decimal("0.500000")
SECONDS_PER_DAY = Decimal("86400.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)


@dataclass(frozen=True)
class LNGStorageConstraintDigestConfig:
    config_version: str = DEFAULT_LNG_STORAGE_CONSTRAINT_DIGEST_CONFIG_VERSION
    watch_risk_score: Decimal = Decimal("0.500000")
    blocked_risk_score: Decimal = Decimal("0.800000")
    watch_storage_utilization: Decimal = Decimal("0.700000")
    blocked_storage_utilization: Decimal = Decimal("0.900000")
    watch_sendout_constraint_ratio: Decimal = Decimal("0.500000")
    blocked_sendout_constraint_ratio: Decimal = Decimal("0.800000")
    watch_cargo_queue_length: Decimal = Decimal("3.000000")
    blocked_cargo_queue_length: Decimal = Decimal("8.000000")
    watch_feedgas_drop_bcf_d: Decimal = Decimal("0.500000")
    blocked_feedgas_drop_bcf_d: Decimal = Decimal("1.500000")
    watch_weather_demand_pressure: Decimal = Decimal("0.400000")
    blocked_weather_demand_pressure: Decimal = Decimal("0.700000")
    max_source_age_seconds: Decimal = Decimal("21600.000000")
    min_source_quorum: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_text("config_version", self.config_version),
        )
        if self.config_version != DEFAULT_LNG_STORAGE_CONSTRAINT_DIGEST_CONFIG_VERSION:
            raise ValueError("config_version must be supported")
        for field_name in (
            "watch_risk_score",
            "blocked_risk_score",
            "watch_storage_utilization",
            "blocked_storage_utilization",
            "watch_sendout_constraint_ratio",
            "blocked_sendout_constraint_ratio",
            "watch_weather_demand_pressure",
            "blocked_weather_demand_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_cargo_queue_length",
            "blocked_cargo_queue_length",
            "watch_feedgas_drop_bcf_d",
            "blocked_feedgas_drop_bcf_d",
            "max_source_age_seconds",
            "min_source_quorum",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        _require_at_least(
            "blocked_risk_score",
            self.blocked_risk_score,
            "watch_risk_score",
            self.watch_risk_score,
        )
        _require_at_least(
            "blocked_storage_utilization",
            self.blocked_storage_utilization,
            "watch_storage_utilization",
            self.watch_storage_utilization,
        )
        _require_at_least(
            "blocked_sendout_constraint_ratio",
            self.blocked_sendout_constraint_ratio,
            "watch_sendout_constraint_ratio",
            self.watch_sendout_constraint_ratio,
        )
        _require_at_least(
            "blocked_cargo_queue_length",
            self.blocked_cargo_queue_length,
            "watch_cargo_queue_length",
            self.watch_cargo_queue_length,
        )
        _require_at_least(
            "blocked_feedgas_drop_bcf_d",
            self.blocked_feedgas_drop_bcf_d,
            "watch_feedgas_drop_bcf_d",
            self.watch_feedgas_drop_bcf_d,
        )
        _require_at_least(
            "blocked_weather_demand_pressure",
            self.blocked_weather_demand_pressure,
            "watch_weather_demand_pressure",
            self.watch_weather_demand_pressure,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class LNGStorageConstraintObservation:
    source_id: str
    terminal_id: str
    region_id: str
    market_slug: str
    storage_utilization: Decimal
    sendout_constraint_ratio: Decimal
    cargo_queue_length: Decimal
    feedgas_delta_bcf_d: Decimal
    weather_demand_pressure: Decimal
    source_observed_at: datetime
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("source_id", "terminal_id", "region_id", "market_slug"):
            object.__setattr__(
                self,
                field_name,
                _require_text(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "storage_utilization",
            "sendout_constraint_ratio",
            "weather_demand_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "cargo_queue_length",
            _require_nonnegative_decimal("cargo_queue_length", self.cargo_queue_length),
        )
        object.__setattr__(
            self,
            "feedgas_delta_bcf_d",
            _require_decimal("feedgas_delta_bcf_d", self.feedgas_delta_bcf_d),
        )
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_upstream_reason_codes(self.upstream_reason_codes),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class LNGStorageConstraintReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "reason_code",
            _require_member("reason_code", self.reason_code, REPORT_REASON_CODES),
        )
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class LNGStorageConstraintDigestRow:
    terminal_id: str
    region_id: str
    market_slug: str
    storage_utilization: Decimal
    sendout_constraint_ratio: Decimal
    cargo_queue_length: Decimal
    feedgas_delta_bcf_d: Decimal
    weather_demand_pressure: Decimal
    metric_pressure_score: Decimal
    evidence_pressure_score: Decimal
    constraint_risk_score: Decimal
    source_count: Decimal
    fresh_source_count: Decimal
    stale_source_count: Decimal
    source_quorum_met: bool
    latest_source_observed_at: datetime
    max_source_age_seconds: Decimal
    constraint_status: str
    source_ids: tuple[str, ...]
    upstream_reason_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("terminal_id", "region_id", "market_slug"):
            object.__setattr__(
                self,
                field_name,
                _require_text(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "storage_utilization",
            "sendout_constraint_ratio",
            "weather_demand_pressure",
            "metric_pressure_score",
            "evidence_pressure_score",
            "constraint_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "cargo_queue_length",
            _require_nonnegative_decimal("cargo_queue_length", self.cargo_queue_length),
        )
        object.__setattr__(
            self,
            "feedgas_delta_bcf_d",
            _require_decimal("feedgas_delta_bcf_d", self.feedgas_delta_bcf_d),
        )
        for field_name in (
            "source_count",
            "fresh_source_count",
            "stale_source_count",
            "max_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if type(self.source_quorum_met) is not bool:
            raise ValueError("source_quorum_met must be a bool")
        object.__setattr__(
            self,
            "latest_source_observed_at",
            _as_utc("latest_source_observed_at", self.latest_source_observed_at),
        )
        object.__setattr__(
            self,
            "constraint_status",
            _require_member("constraint_status", self.constraint_status, ROW_STATUSES),
        )
        object.__setattr__(
            self,
            "source_ids",
            _normalize_text_tuple("source_ids", self.source_ids),
        )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_upstream_reason_codes(self.upstream_reason_codes),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class LNGStorageConstraintDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    input_count: Decimal
    row_count: Decimal
    terminal_count: Decimal
    source_count: Decimal
    fresh_source_count: Decimal
    stale_source_count: Decimal
    source_quorum_gap_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    risk_score: Decimal
    max_storage_utilization: Decimal
    max_sendout_constraint_ratio: Decimal
    max_cargo_queue_length: Decimal
    min_feedgas_delta_bcf_d: Decimal
    max_weather_demand_pressure: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[LNGStorageConstraintDigestRow, ...]
    reason_code_counts: tuple[LNGStorageConstraintReasonCodeCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_text("config_version", self.config_version),
        )
        if self.config_version != DEFAULT_LNG_STORAGE_CONSTRAINT_DIGEST_CONFIG_VERSION:
            raise ValueError("config_version must be supported")
        object.__setattr__(
            self,
            "digest_status",
            _require_member("digest_status", self.digest_status, DIGEST_STATUSES),
        )
        object.__setattr__(
            self,
            "recommended_next_step",
            _require_text("recommended_next_step", self.recommended_next_step),
        )
        for field_name in (
            "input_count",
            "row_count",
            "terminal_count",
            "source_count",
            "fresh_source_count",
            "stale_source_count",
            "source_quorum_gap_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "max_cargo_queue_length",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "risk_score",
            "max_storage_utilization",
            "max_sendout_constraint_ratio",
            "max_weather_demand_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_feedgas_delta_bcf_d",
            _require_decimal("min_feedgas_delta_bcf_d", self.min_feedgas_delta_bcf_d),
        )
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
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_energy_lng_storage_constraint_digest(
    observations: Iterable[LNGStorageConstraintObservation],
    *,
    config: LNGStorageConstraintDigestConfig,
    generated_at: datetime,
) -> LNGStorageConstraintDigestReport:
    if type(config) is not LNGStorageConstraintDigestConfig:
        raise ValueError("config must be an LNGStorageConstraintDigestConfig")
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_observations(observations)
    for observation in input_rows:
        if observation.source_observed_at > generated_at_utc:
            raise ValueError("source_observed_at must not be after generated_at")

    if not input_rows:
        return LNGStorageConstraintDigestReport(
            generated_at=generated_at_utc,
            config_version=config.config_version,
            digest_status="blocked",
            recommended_next_step=_next_step("blocked"),
            input_count=ZERO,
            row_count=ZERO,
            terminal_count=ZERO,
            source_count=ZERO,
            fresh_source_count=ZERO,
            stale_source_count=ZERO,
            source_quorum_gap_count=ZERO,
            blocked_count=ZERO,
            watch_count=ZERO,
            pass_count=ZERO,
            risk_score=ZERO,
            max_storage_utilization=ZERO,
            max_sendout_constraint_ratio=ZERO,
            max_cargo_queue_length=ZERO,
            min_feedgas_delta_bcf_d=ZERO,
            max_weather_demand_pressure=ZERO,
            reason_codes=("lng_storage_constraint_digest_empty",),
            rows=(),
            reason_code_counts=(
                LNGStorageConstraintReasonCodeCount(
                    reason_code="lng_storage_constraint_digest_empty",
                    count=ONE,
                    row_ratio=ZERO,
                ),
            ),
        )

    grouped: dict[tuple[str, str, str], list[LNGStorageConstraintObservation]] = {}
    for observation in input_rows:
        group_id = (
            observation.terminal_id,
            observation.region_id,
            observation.market_slug,
        )
        grouped.setdefault(group_id, []).append(observation)

    rows = tuple(
        sorted(
            (
                _row_from_observations(
                    terminal_id,
                    region_id,
                    market_slug,
                    tuple(group_rows),
                    config=config,
                    generated_at=generated_at_utc,
                )
                for (terminal_id, region_id, market_slug), group_rows in grouped.items()
            ),
            key=_row_sort_value,
        )
    )
    row_count = _count(len(rows))
    reason_codes = _report_reasons(rows)
    return LNGStorageConstraintDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=_report_status(rows),
        recommended_next_step=_next_step(_report_status(rows)),
        input_count=_count(len(input_rows)),
        row_count=row_count,
        terminal_count=_count(len({row.terminal_id for row in rows})),
        source_count=_sum_decimal(row.source_count for row in rows),
        fresh_source_count=_sum_decimal(row.fresh_source_count for row in rows),
        stale_source_count=_sum_decimal(row.stale_source_count for row in rows),
        source_quorum_gap_count=_count(
            sum(1 for row in rows if not row.source_quorum_met)
        ),
        blocked_count=_count(sum(1 for row in rows if row.constraint_status == "blocked")),
        watch_count=_count(sum(1 for row in rows if row.constraint_status == "watch")),
        pass_count=_count(sum(1 for row in rows if row.constraint_status == "pass")),
        risk_score=max((row.constraint_risk_score for row in rows), default=ZERO),
        max_storage_utilization=max(
            (row.storage_utilization for row in rows),
            default=ZERO,
        ),
        max_sendout_constraint_ratio=max(
            (row.sendout_constraint_ratio for row in rows),
            default=ZERO,
        ),
        max_cargo_queue_length=max((row.cargo_queue_length for row in rows), default=ZERO),
        min_feedgas_delta_bcf_d=min(
            (row.feedgas_delta_bcf_d for row in rows),
            default=ZERO,
        ),
        max_weather_demand_pressure=max(
            (row.weather_demand_pressure for row in rows),
            default=ZERO,
        ),
        reason_codes=reason_codes,
        rows=rows,
        reason_code_counts=_reason_counts(rows, reason_codes, row_count),
    )


def market_research_energy_lng_storage_constraint_digest_payload(
    digest: LNGStorageConstraintDigestReport,
) -> dict[str, Any]:
    if type(digest) is not LNGStorageConstraintDigestReport:
        raise ValueError("digest must be an LNGStorageConstraintDigestReport")
    return _json_ready(digest)


def _row_from_observations(
    terminal_id: str,
    region_id: str,
    market_slug: str,
    observations: tuple[LNGStorageConstraintObservation, ...],
    *,
    config: LNGStorageConstraintDigestConfig,
    generated_at: datetime,
) -> LNGStorageConstraintDigestRow:
    storage_utilization = max(row.storage_utilization for row in observations)
    sendout_constraint_ratio = max(row.sendout_constraint_ratio for row in observations)
    cargo_queue_length = max(row.cargo_queue_length for row in observations)
    feedgas_delta_bcf_d = min(row.feedgas_delta_bcf_d for row in observations)
    weather_demand_pressure = max(row.weather_demand_pressure for row in observations)
    source_ages = tuple(
        _source_age_seconds(generated_at, row.source_observed_at) for row in observations
    )
    fresh_source_count = _count(
        sum(1 for age in source_ages if age <= config.max_source_age_seconds)
    )
    stale_source_count = _count(len(source_ages)) - fresh_source_count
    source_quorum_met = fresh_source_count >= config.min_source_quorum
    metric_pressure_score = _metric_pressure_score(
        storage_utilization=storage_utilization,
        sendout_constraint_ratio=sendout_constraint_ratio,
        cargo_queue_length=cargo_queue_length,
        feedgas_delta_bcf_d=feedgas_delta_bcf_d,
        weather_demand_pressure=weather_demand_pressure,
        config=config,
    )
    evidence_pressure_score = _evidence_pressure_score(
        fresh_source_count,
        config=config,
    )
    constraint_risk_score = max(metric_pressure_score, evidence_pressure_score)
    return LNGStorageConstraintDigestRow(
        terminal_id=terminal_id,
        region_id=region_id,
        market_slug=market_slug,
        storage_utilization=storage_utilization,
        sendout_constraint_ratio=sendout_constraint_ratio,
        cargo_queue_length=cargo_queue_length,
        feedgas_delta_bcf_d=feedgas_delta_bcf_d,
        weather_demand_pressure=weather_demand_pressure,
        metric_pressure_score=metric_pressure_score,
        evidence_pressure_score=evidence_pressure_score,
        constraint_risk_score=constraint_risk_score,
        source_count=_count(len(observations)),
        fresh_source_count=fresh_source_count,
        stale_source_count=stale_source_count,
        source_quorum_met=source_quorum_met,
        latest_source_observed_at=max(row.source_observed_at for row in observations),
        max_source_age_seconds=max(source_ages),
        constraint_status=_status_from_risk(constraint_risk_score, config=config),
        source_ids=tuple(row.source_id for row in observations),
        upstream_reason_codes=tuple(
            reason
            for row in observations
            for reason in row.upstream_reason_codes
        ),
        reason_codes=_row_reasons(
            storage_utilization=storage_utilization,
            sendout_constraint_ratio=sendout_constraint_ratio,
            cargo_queue_length=cargo_queue_length,
            feedgas_delta_bcf_d=feedgas_delta_bcf_d,
            weather_demand_pressure=weather_demand_pressure,
            fresh_source_count=fresh_source_count,
            upstream_reason_codes=tuple(
                reason
                for row in observations
                for reason in row.upstream_reason_codes
            ),
            config=config,
        ),
    )


def _metric_pressure_score(
    *,
    storage_utilization: Decimal,
    sendout_constraint_ratio: Decimal,
    cargo_queue_length: Decimal,
    feedgas_delta_bcf_d: Decimal,
    weather_demand_pressure: Decimal,
    config: LNGStorageConstraintDigestConfig,
) -> Decimal:
    feedgas_drop = -feedgas_delta_bcf_d if feedgas_delta_bcf_d < ZERO else ZERO
    return max(
        storage_utilization,
        sendout_constraint_ratio,
        _capped_ratio(cargo_queue_length, config.blocked_cargo_queue_length),
        _capped_ratio(feedgas_drop, config.blocked_feedgas_drop_bcf_d),
        weather_demand_pressure,
    ).quantize(QUANT, rounding=ROUND_HALF_EVEN)


def _evidence_pressure_score(
    fresh_source_count: Decimal,
    *,
    config: LNGStorageConstraintDigestConfig,
) -> Decimal:
    if fresh_source_count == ZERO:
        return ONE
    if fresh_source_count < config.min_source_quorum:
        return HALF
    return ZERO


def _status_from_risk(
    risk_score: Decimal,
    *,
    config: LNGStorageConstraintDigestConfig,
) -> str:
    if risk_score >= config.blocked_risk_score:
        return "blocked"
    if risk_score >= config.watch_risk_score:
        return "watch"
    return "pass"


def _row_reasons(
    *,
    storage_utilization: Decimal,
    sendout_constraint_ratio: Decimal,
    cargo_queue_length: Decimal,
    feedgas_delta_bcf_d: Decimal,
    weather_demand_pressure: Decimal,
    fresh_source_count: Decimal,
    upstream_reason_codes: tuple[str, ...],
    config: LNGStorageConstraintDigestConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if fresh_source_count == ZERO:
        reasons.append("lng_storage_constraint_all_sources_stale")
    elif fresh_source_count < config.min_source_quorum:
        reasons.append("lng_storage_constraint_source_quorum_gap")
    if storage_utilization >= config.blocked_storage_utilization:
        reasons.append("lng_storage_constraint_high_storage_utilization")
    elif storage_utilization >= config.watch_storage_utilization:
        reasons.append("lng_storage_constraint_elevated_storage_utilization")
    if sendout_constraint_ratio >= config.blocked_sendout_constraint_ratio:
        reasons.append("lng_storage_constraint_sendout_constrained")
    elif sendout_constraint_ratio >= config.watch_sendout_constraint_ratio:
        reasons.append("lng_storage_constraint_sendout_tight")
    if cargo_queue_length >= config.blocked_cargo_queue_length:
        reasons.append("lng_storage_constraint_cargo_queue_blocked")
    elif cargo_queue_length >= config.watch_cargo_queue_length:
        reasons.append("lng_storage_constraint_cargo_queue_watch")
    feedgas_drop = -feedgas_delta_bcf_d if feedgas_delta_bcf_d < ZERO else ZERO
    if feedgas_drop >= config.blocked_feedgas_drop_bcf_d:
        reasons.append("lng_storage_constraint_feedgas_drop_blocked")
    elif feedgas_drop >= config.watch_feedgas_drop_bcf_d:
        reasons.append("lng_storage_constraint_feedgas_drop_watch")
    if weather_demand_pressure >= config.blocked_weather_demand_pressure:
        reasons.append("lng_storage_constraint_weather_demand_pressure")
    elif weather_demand_pressure >= config.watch_weather_demand_pressure:
        reasons.append("lng_storage_constraint_weather_demand_watch")
    if "lng_storage_source_correction" in upstream_reason_codes:
        reasons.append("lng_storage_constraint_upstream_source_correction")
    if not reasons:
        reasons.append("lng_storage_constraint_inline")
    return _normalize_reason_codes("reason_codes", tuple(reasons), ROW_REASON_CODES)


def _report_status(rows: tuple[LNGStorageConstraintDigestRow, ...]) -> str:
    if any(row.constraint_status == "blocked" for row in rows):
        return "blocked"
    if any(row.constraint_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reasons(rows: tuple[LNGStorageConstraintDigestRow, ...]) -> tuple[str, ...]:
    if not rows:
        return ("lng_storage_constraint_digest_empty",)
    reasons: list[str] = []
    if all(row.constraint_status == "pass" for row in rows):
        reasons.append("lng_storage_constraint_clear")
    if any(row.constraint_status == "blocked" for row in rows):
        reasons.append("lng_storage_constraint_blocked_present")
    if any(row.constraint_status == "watch" for row in rows):
        reasons.append("lng_storage_constraint_watch_present")
    for report_reason, row_reason in REPORT_REASON_TO_ROW_REASON.items():
        if any(row_reason in row.reason_codes for row in rows):
            reasons.append(report_reason)
    return _normalize_reason_codes("reason_codes", tuple(reasons), REPORT_REASON_CODES)


def _reason_counts(
    rows: tuple[LNGStorageConstraintDigestRow, ...],
    report_reasons: tuple[str, ...],
    row_count: Decimal,
) -> tuple[LNGStorageConstraintReasonCodeCount, ...]:
    if report_reasons == ("lng_storage_constraint_digest_empty",):
        return (
            LNGStorageConstraintReasonCodeCount(
                reason_code="lng_storage_constraint_digest_empty",
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        sorted(
            (
                LNGStorageConstraintReasonCodeCount(
                    reason_code=reason,
                    count=_count(_report_reason_count(rows, reason)),
                    row_ratio=_ratio(_count(_report_reason_count(rows, reason)), row_count),
                )
                for reason in report_reasons
            ),
            key=_reason_count_sort_value,
        )
    )


def _report_reason_count(
    rows: tuple[LNGStorageConstraintDigestRow, ...],
    reason: str,
) -> int:
    if reason == "lng_storage_constraint_clear":
        return sum(1 for row in rows if row.constraint_status == "pass")
    if reason == "lng_storage_constraint_blocked_present":
        return sum(1 for row in rows if row.constraint_status == "blocked")
    if reason == "lng_storage_constraint_watch_present":
        return sum(1 for row in rows if row.constraint_status == "watch")
    row_reason = REPORT_REASON_TO_ROW_REASON.get(reason)
    if row_reason is None:
        return 0
    return sum(1 for row in rows if row_reason in row.reason_codes)


def _next_step(status: str) -> str:
    if status == "blocked":
        return "block_report_only_market_research_energy_lng_storage_constraint_digest"
    if status == "watch":
        return "monitor_report_only_market_research_energy_lng_storage_constraint_digest"
    return "allow_report_only_market_research_energy_lng_storage_constraint_digest"


def _normalize_observations(
    observations: Iterable[LNGStorageConstraintObservation],
) -> tuple[LNGStorageConstraintObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must contain LNG storage constraint observations")
    try:
        normalized = tuple(observations)
    except TypeError as exc:
        raise ValueError(
            "observations must contain LNG storage constraint observations",
        ) from exc
    seen: set[str] = set()
    for observation in normalized:
        if type(observation) is not LNGStorageConstraintObservation:
            raise ValueError("observations must contain LNGStorageConstraintObservation")
        if observation.source_id in seen:
            raise ValueError("observations must not contain duplicate source_id values")
        seen.add(observation.source_id)
    return normalized


def _normalize_rows(value: object) -> tuple[LNGStorageConstraintDigestRow, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, tuple):
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not LNGStorageConstraintDigestRow:
            raise ValueError("rows must contain LNGStorageConstraintDigestRow")
    if value != tuple(sorted(value, key=_row_sort_value)):
        raise ValueError("rows must be sorted deterministically")
    row_ids = tuple((row.terminal_id, row.region_id, row.market_slug) for row in value)
    if len(set(row_ids)) != len(row_ids):
        raise ValueError("rows must not contain duplicate terminal region market records")
    return value


def _normalize_reason_code_counts(
    value: object,
) -> tuple[LNGStorageConstraintReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    for row in value:
        if type(row) is not LNGStorageConstraintReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain LNGStorageConstraintReasonCodeCount",
            )
    if value != tuple(sorted(value, key=_reason_count_sort_value)):
        raise ValueError("reason_code_counts must be sorted deterministically")
    return value


def _normalize_text_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    return tuple(sorted({_require_text(field_name, item) for item in value}))


def _normalize_upstream_reason_codes(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, tuple):
        raise ValueError("upstream_reason_codes must be a tuple")
    return tuple(sorted({_require_reason_text("upstream_reason_codes", item) for item in value}))


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    return tuple(
        sorted(
            {_require_member("reason_code", item, allowed) for item in value},
            key=allowed.index,
        )
    )


def _row_sort_value(row: LNGStorageConstraintDigestRow) -> tuple[int, Decimal, str, str, str]:
    return (
        STATUS_RANK[row.constraint_status],
        -row.constraint_risk_score,
        row.terminal_id,
        row.region_id,
        row.market_slug,
    )


def _reason_count_sort_value(
    row: LNGStorageConstraintReasonCodeCount,
) -> tuple[Decimal, int]:
    return (-row.count, REPORT_REASON_CODES.index(row.reason_code))


def _validate_row(row: LNGStorageConstraintDigestRow) -> None:
    if row.constraint_risk_score != max(
        row.metric_pressure_score,
        row.evidence_pressure_score,
    ):
        raise ValueError("constraint_risk_score must match row inputs")
    if row.source_count != row.fresh_source_count + row.stale_source_count:
        raise ValueError("source_count must match fresh and stale source counts")
    if row.source_count != _count(len(row.source_ids)):
        raise ValueError("source_count must match source_ids")
    if row.source_count <= ZERO:
        raise ValueError("source_count must be positive")
    if row.source_quorum_met != (row.evidence_pressure_score == ZERO):
        raise ValueError("source_quorum_met must match evidence_pressure_score")
    if row.reason_codes == ("lng_storage_constraint_inline",) and (
        row.constraint_status != "pass"
    ):
        raise ValueError("inline reason_codes must describe passing rows")


def _validate_report(report: LNGStorageConstraintDigestReport) -> None:
    if report.row_count != _count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.terminal_count != _count(len({row.terminal_id for row in report.rows})):
        raise ValueError("terminal_count must match rows")
    if report.source_count != _sum_decimal(row.source_count for row in report.rows):
        raise ValueError("source_count must match rows")
    if report.fresh_source_count != _sum_decimal(
        row.fresh_source_count for row in report.rows
    ):
        raise ValueError("fresh_source_count must match rows")
    if report.stale_source_count != _sum_decimal(
        row.stale_source_count for row in report.rows
    ):
        raise ValueError("stale_source_count must match rows")
    if report.source_quorum_gap_count != _count(
        sum(1 for row in report.rows if not row.source_quorum_met)
    ):
        raise ValueError("source_quorum_gap_count must match rows")
    if report.blocked_count != _count(
        sum(1 for row in report.rows if row.constraint_status == "blocked")
    ):
        raise ValueError("blocked_count must match rows")
    if report.watch_count != _count(
        sum(1 for row in report.rows if row.constraint_status == "watch")
    ):
        raise ValueError("watch_count must match rows")
    if report.pass_count != _count(
        sum(1 for row in report.rows if row.constraint_status == "pass")
    ):
        raise ValueError("pass_count must match rows")
    if report.rows:
        if report.digest_status != _report_status(report.rows):
            raise ValueError("digest_status must match rows")
        if report.risk_score != max(row.constraint_risk_score for row in report.rows):
            raise ValueError("risk_score must match rows")
        if report.max_storage_utilization != max(
            row.storage_utilization for row in report.rows
        ):
            raise ValueError("max_storage_utilization must match rows")
        if report.max_sendout_constraint_ratio != max(
            row.sendout_constraint_ratio for row in report.rows
        ):
            raise ValueError("max_sendout_constraint_ratio must match rows")
        if report.max_cargo_queue_length != max(
            row.cargo_queue_length for row in report.rows
        ):
            raise ValueError("max_cargo_queue_length must match rows")
        if report.min_feedgas_delta_bcf_d != min(
            row.feedgas_delta_bcf_d for row in report.rows
        ):
            raise ValueError("min_feedgas_delta_bcf_d must match rows")
        if report.max_weather_demand_pressure != max(
            row.weather_demand_pressure for row in report.rows
        ):
            raise ValueError("max_weather_demand_pressure must match rows")
    else:
        if report.digest_status != "blocked":
            raise ValueError("empty digest_status must be blocked")
        for field_name in (
            "risk_score",
            "max_storage_utilization",
            "max_sendout_constraint_ratio",
            "max_cargo_queue_length",
            "min_feedgas_delta_bcf_d",
            "max_weather_demand_pressure",
        ):
            if getattr(report, field_name) != ZERO:
                raise ValueError(f"{field_name} must be zero when rows are empty")
    if report.recommended_next_step != _next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_codes != _report_reasons(report.rows):
        raise ValueError("reason_codes must match rows")
    expected_reason_counts = _reason_counts(
        report.rows,
        report.reason_codes,
        report.row_count,
    )
    if report.reason_code_counts != expected_reason_counts:
        raise ValueError("reason_code_counts must match rows")


def _require_at_least(
    field_name: str,
    value: Decimal,
    minimum_name: str,
    minimum: Decimal,
) -> None:
    if value < minimum:
        raise ValueError(f"{field_name} must be at least {minimum_name}")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> str:
    text = _require_text(field_name, value)
    if text not in allowed:
        raise ValueError(f"{field_name} must be supported")
    return text


def _require_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    text = value.strip()
    if not text:
        raise ValueError(f"{field_name} must be nonempty")
    if any(character.isspace() for character in text):
        raise ValueError(f"{field_name} must not contain whitespace")
    return text


def _require_reason_text(field_name: str, value: object) -> str:
    text = _require_text(field_name, value)
    for character in text:
        if not (
            character.isascii()
            and (character.islower() or character.isdigit() or character == "_")
        ):
            raise ValueError(f"{field_name} must contain lowercase reason codes")
    return text


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANT, rounding=ROUND_HALF_EVEN)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be no greater than one")
    return decimal_value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _source_age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    value = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    return value.quantize(QUANT, rounding=ROUND_HALF_EVEN)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
        total += value
    return total.quantize(QUANT, rounding=ROUND_HALF_EVEN)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    return min(_ratio(numerator, denominator), ONE)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT, rounding=ROUND_HALF_EVEN)


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(name): _json_ready(item) for name, item in value.items()}
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


__all__ = (
    "DEFAULT_LNG_STORAGE_CONSTRAINT_DIGEST_CONFIG_VERSION",
    "LNGStorageConstraintDigestConfig",
    "LNGStorageConstraintObservation",
    "LNGStorageConstraintReasonCodeCount",
    "LNGStorageConstraintDigestRow",
    "LNGStorageConstraintDigestReport",
    "build_market_research_energy_lng_storage_constraint_digest",
    "market_research_energy_lng_storage_constraint_digest_payload",
)
