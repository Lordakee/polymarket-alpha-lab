"""Pure Phase 1 specialist source reliability decay watch report."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_TEAM_SPECIALIST_SOURCE_RELIABILITY_DECAY_WATCH_V2_CONFIG_VERSION = (
    "team-specialist-source-reliability-decay-watch-v2-phase-1"
)
TEAM_SPECIALIST_SOURCE_RELIABILITY_DECAY_WATCH_V2_STATUSES = (
    "clear",
    "watch",
    "critical",
)

RECENT_SOURCE_MISSES_REASON = "recent_source_misses"
STALE_SOURCE_USE_REASON = "stale_source_use"
CONTRADICTION_MISSES_REASON = "contradiction_misses"
OFFICIAL_SOURCE_LAG_REASON = "official_source_lag"
CATEGORY_MISMATCH_REASON = "category_mismatch"
LOW_SOURCE_SAMPLE_SIZE_REASON = "low_source_sample_size"
SOURCE_RELIABILITY_DECAY_CLEAR_REASON = "source_reliability_decay_clear"
REPORT_CRITICAL_REASON = "source_reliability_decay_watch_critical"
REPORT_WATCH_REASON = "source_reliability_decay_watch_active"
EMPTY_SOURCES_REASON = "source_reliability_decay_watch_empty_sources"

ROW_REASON_CODES = (
    RECENT_SOURCE_MISSES_REASON,
    STALE_SOURCE_USE_REASON,
    CONTRADICTION_MISSES_REASON,
    OFFICIAL_SOURCE_LAG_REASON,
    CATEGORY_MISMATCH_REASON,
    LOW_SOURCE_SAMPLE_SIZE_REASON,
    SOURCE_RELIABILITY_DECAY_CLEAR_REASON,
)
REPORT_REASON_CODES = (
    REPORT_CRITICAL_REASON,
    REPORT_WATCH_REASON,
    RECENT_SOURCE_MISSES_REASON,
    STALE_SOURCE_USE_REASON,
    CONTRADICTION_MISSES_REASON,
    OFFICIAL_SOURCE_LAG_REASON,
    CATEGORY_MISMATCH_REASON,
    LOW_SOURCE_SAMPLE_SIZE_REASON,
    SOURCE_RELIABILITY_DECAY_CLEAR_REASON,
    EMPTY_SOURCES_REASON,
)

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SAFE_REF_PREFIXES = (
    "public:",
    "source:",
    "official:",
    "reliability:",
    "calibration:",
    "lesson:",
)
PUBLIC_TEXT_HEXES = (
    "6c697665",
    "61757468",
    "77616c6c6574",
    "6f72646572",
    "6e6574776f726b",
    "6461746162617365",
    "70657273697374",
    "7369676e696e67",
    "6d75746174696f6e",
    "627579",
    "73656c6c",
    "7472616465",
)
PUBLIC_TEXT_BLOCKS = tuple(bytes.fromhex(value).decode("ascii") for value in PUBLIC_TEXT_HEXES)


@dataclass(frozen=True)
class TeamSpecialistSourceReliabilityDecayWatchV2Config:
    config_version: str = (
        DEFAULT_TEAM_SPECIALIST_SOURCE_RELIABILITY_DECAY_WATCH_V2_CONFIG_VERSION
    )
    recent_miss_weight: Decimal = Decimal("0.300000")
    stale_source_use_weight: Decimal = Decimal("0.200000")
    contradiction_miss_weight: Decimal = Decimal("0.200000")
    official_source_lag_weight: Decimal = Decimal("0.150000")
    category_mismatch_weight: Decimal = Decimal("0.100000")
    sample_size_weight: Decimal = Decimal("0.050000")
    stale_source_use_threshold_seconds: Decimal = Decimal("604800.000000")
    max_stale_source_use_seconds: Decimal = Decimal("2419200.000000")
    official_source_lag_threshold_seconds: Decimal = Decimal("86400.000000")
    max_official_source_lag_seconds: Decimal = Decimal("604800.000000")
    min_sample_count: Decimal = Decimal("5")
    watch_decay_score: Decimal = Decimal("0.250000")
    critical_decay_score: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "recent_miss_weight",
            "stale_source_use_weight",
            "contradiction_miss_weight",
            "official_source_lag_weight",
            "category_mismatch_weight",
            "sample_size_weight",
            "watch_decay_score",
            "critical_decay_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "stale_source_use_threshold_seconds",
            "max_stale_source_use_seconds",
            "official_source_lag_threshold_seconds",
            "max_official_source_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_sample_count",
            _normalize_positive_count("min_sample_count", self.min_sample_count),
        )
        _require_ratio_total(
            self.recent_miss_weight,
            self.stale_source_use_weight,
            self.contradiction_miss_weight,
            self.official_source_lag_weight,
            self.category_mismatch_weight,
            self.sample_size_weight,
        )
        if self.stale_source_use_threshold_seconds >= self.max_stale_source_use_seconds:
            raise ValueError(
                "stale_source_use_threshold_seconds must be less than "
                "max_stale_source_use_seconds",
            )
        if (
            self.official_source_lag_threshold_seconds
            >= self.max_official_source_lag_seconds
        ):
            raise ValueError(
                "official_source_lag_threshold_seconds must be less than "
                "max_official_source_lag_seconds",
            )
        if self.watch_decay_score > self.critical_decay_score:
            raise ValueError(
                "watch_decay_score must be less than or equal to critical_decay_score",
            )
        require_paper_only_flags("source reliability decay watch config", self)


@dataclass(frozen=True)
class TeamSpecialistSourceReliabilityDecayWatchInputV2:
    team_id: str
    specialist_id: str
    source_id: str
    source_family: str
    category_id: str
    expected_category_id: str
    observed_at: datetime
    source_last_verified_at: datetime
    official_source_last_checked_at: datetime
    recent_miss_count: Decimal
    contradiction_miss_count: Decimal
    sample_count: Decimal
    public_source_refs: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "team_id",
            "specialist_id",
            "source_id",
            "source_family",
            "category_id",
            "expected_category_id",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "observed_at",
            "source_last_verified_at",
            "official_source_last_checked_at",
        ):
            object.__setattr__(self, field_name, _as_utc(field_name, getattr(self, field_name)))
        for field_name in (
            "recent_miss_count",
            "contradiction_miss_count",
            "sample_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        if self.recent_miss_count > self.sample_count:
            raise ValueError("recent_miss_count must not exceed sample_count")
        if self.contradiction_miss_count > self.sample_count:
            raise ValueError("contradiction_miss_count must not exceed sample_count")
        object.__setattr__(
            self,
            "public_source_refs",
            _normalize_public_refs("public_source_refs", self.public_source_refs),
        )
        require_paper_only_flags("source reliability decay watch input", self)


@dataclass(frozen=True)
class TeamSpecialistSourceReliabilityDecayWatchRowV2:
    team_id: str
    specialist_id: str
    source_id: str
    source_family: str
    category_id: str
    expected_category_id: str
    observation_count: Decimal
    latest_observed_at: datetime
    oldest_source_last_verified_at: datetime
    oldest_official_source_last_checked_at: datetime
    recent_miss_count: Decimal
    contradiction_miss_count: Decimal
    sample_count: Decimal
    recent_miss_ratio: Decimal
    contradiction_miss_ratio: Decimal
    source_verification_age_seconds: Decimal
    official_source_lag_seconds: Decimal
    stale_source_use_component: Decimal
    official_source_lag_component: Decimal
    sample_size_gap: Decimal
    decay_score: Decimal
    category_mismatch: bool
    row_status: str
    public_source_refs: tuple[str, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "team_id",
            "specialist_id",
            "source_id",
            "source_family",
            "category_id",
            "expected_category_id",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "observation_count",
            "recent_miss_count",
            "contradiction_miss_count",
            "sample_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "latest_observed_at",
            "oldest_source_last_verified_at",
            "oldest_official_source_last_checked_at",
        ):
            object.__setattr__(self, field_name, _as_utc(field_name, getattr(self, field_name)))
        for field_name in (
            "recent_miss_ratio",
            "contradiction_miss_ratio",
            "stale_source_use_component",
            "official_source_lag_component",
            "sample_size_gap",
            "decay_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_verification_age_seconds",
            "official_source_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if type(self.category_mismatch) is not bool:
            raise ValueError("category_mismatch must be a bool")
        _require_status("row_status", self.row_status)
        object.__setattr__(
            self,
            "public_source_refs",
            _normalize_public_refs("public_source_refs", self.public_source_refs),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        if self.derived_validation_digest != _row_digest(self):
            raise ValueError("derived_validation_digest must match watch row fields")
        _validate_row(self)
        require_paper_only_flags("source reliability decay watch row", self)


@dataclass(frozen=True)
class TeamSpecialistSourceReliabilityDecayWatchReportV2:
    generated_at: datetime
    config_version: str
    team_count: Decimal
    specialist_team_count: Decimal
    source_count: Decimal
    observation_count: Decimal
    critical_count: Decimal
    watch_count: Decimal
    clear_count: Decimal
    recent_miss_source_count: Decimal
    stale_source_use_count: Decimal
    contradiction_miss_source_count: Decimal
    official_source_lag_count: Decimal
    category_mismatch_count: Decimal
    low_sample_size_count: Decimal
    average_decay_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[TeamSpecialistSourceReliabilityDecayWatchRowV2, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "team_count",
            "specialist_team_count",
            "source_count",
            "observation_count",
            "critical_count",
            "watch_count",
            "clear_count",
            "recent_miss_source_count",
            "stale_source_use_count",
            "contradiction_miss_source_count",
            "official_source_lag_count",
            "category_mismatch_count",
            "low_sample_size_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_decay_score",
            _normalize_ratio("average_decay_score", self.average_decay_score),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        if self.derived_validation_digest != _report_digest(self):
            raise ValueError("derived_validation_digest must match report fields")
        _validate_report(self)
        require_paper_only_flags("source reliability decay watch report", self)


def build_team_specialist_source_reliability_decay_watch_v2(
    inputs: list[TeamSpecialistSourceReliabilityDecayWatchInputV2]
    | tuple[TeamSpecialistSourceReliabilityDecayWatchInputV2, ...],
    *,
    config: TeamSpecialistSourceReliabilityDecayWatchV2Config,
    generated_at: datetime,
) -> TeamSpecialistSourceReliabilityDecayWatchReportV2:
    if type(config) is not TeamSpecialistSourceReliabilityDecayWatchV2Config:
        raise ValueError(
            "config must be a TeamSpecialistSourceReliabilityDecayWatchV2Config",
        )
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_rows = _normalize_inputs(inputs)
    _validate_input_dates(source_rows, generated_at_utc)
    rows = tuple(
        sorted(
            (
                _watch_row(
                    team_id,
                    specialist_id,
                    source_id,
                    source_family,
                    category_id,
                    expected_category_id,
                    group,
                    config,
                    generated_at_utc,
                )
                for (
                    team_id,
                    specialist_id,
                    source_id,
                    source_family,
                    category_id,
                    expected_category_id,
                    group,
                ) in _input_groups(source_rows)
            ),
            key=_row_sort_key,
        ),
    )
    report_parts = dict(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        team_count=_count(len({row.team_id for row in rows})),
        specialist_team_count=_count(
            len({(row.team_id, row.specialist_id) for row in rows}),
        ),
        source_count=_count(len({row.source_id for row in rows})),
        observation_count=_sum_rows(rows, "observation_count"),
        critical_count=_status_count(rows, "critical"),
        watch_count=_status_count(rows, "watch"),
        clear_count=_status_count(rows, "clear"),
        recent_miss_source_count=_reason_count(rows, RECENT_SOURCE_MISSES_REASON),
        stale_source_use_count=_reason_count(rows, STALE_SOURCE_USE_REASON),
        contradiction_miss_source_count=_reason_count(rows, CONTRADICTION_MISSES_REASON),
        official_source_lag_count=_reason_count(rows, OFFICIAL_SOURCE_LAG_REASON),
        category_mismatch_count=_reason_count(rows, CATEGORY_MISMATCH_REASON),
        low_sample_size_count=_reason_count(rows, LOW_SOURCE_SAMPLE_SIZE_REASON),
        average_decay_score=_average_decay_score(rows),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
        paper_only=True,
        report_only=True,
        readonly=True,
    )
    return TeamSpecialistSourceReliabilityDecayWatchReportV2(
        **report_parts,
        derived_validation_digest=_digest_public(report_parts),
    )


def team_specialist_source_reliability_decay_watch_v2_payload(
    report: TeamSpecialistSourceReliabilityDecayWatchReportV2,
) -> dict[str, Any]:
    if type(report) is not TeamSpecialistSourceReliabilityDecayWatchReportV2:
        raise ValueError(
            "report must be a TeamSpecialistSourceReliabilityDecayWatchReportV2",
        )
    require_paper_only_flags("report", report)
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest must match report fields")
    payload = json_ready_no_floats(report)
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")
    _reject_public_payload("source reliability decay watch payload", payload)
    return _tupleify_payload_collections(payload)


def _normalize_inputs(
    inputs: list[TeamSpecialistSourceReliabilityDecayWatchInputV2]
    | tuple[TeamSpecialistSourceReliabilityDecayWatchInputV2, ...],
) -> tuple[TeamSpecialistSourceReliabilityDecayWatchInputV2, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(inputs)
    for row in rows:
        if type(row) is not TeamSpecialistSourceReliabilityDecayWatchInputV2:
            raise ValueError(
                "inputs must contain TeamSpecialistSourceReliabilityDecayWatchInputV2 values",
            )
        require_paper_only_flags("input", row)
    return rows


def _validate_input_dates(
    rows: tuple[TeamSpecialistSourceReliabilityDecayWatchInputV2, ...],
    generated_at: datetime,
) -> None:
    for row in rows:
        if row.observed_at > generated_at:
            raise ValueError("observed_at must be on or before generated_at")
        if row.source_last_verified_at > generated_at:
            raise ValueError("source_last_verified_at must be on or before generated_at")
        if row.official_source_last_checked_at > generated_at:
            raise ValueError(
                "official_source_last_checked_at must be on or before generated_at",
            )


def _input_groups(
    rows: tuple[TeamSpecialistSourceReliabilityDecayWatchInputV2, ...],
) -> tuple[
    tuple[
        str,
        str,
        str,
        str,
        str,
        str,
        tuple[TeamSpecialistSourceReliabilityDecayWatchInputV2, ...],
    ],
    ...,
]:
    keys = tuple(
        sorted(
            {
                (
                    row.team_id,
                    row.specialist_id,
                    row.source_id,
                    row.source_family,
                    row.category_id,
                    row.expected_category_id,
                )
                for row in rows
            },
        ),
    )
    return tuple(
        (
            team_id,
            specialist_id,
            source_id,
            source_family,
            category_id,
            expected_category_id,
            tuple(
                row
                for row in rows
                if (
                    row.team_id,
                    row.specialist_id,
                    row.source_id,
                    row.source_family,
                    row.category_id,
                    row.expected_category_id,
                )
                == (
                    team_id,
                    specialist_id,
                    source_id,
                    source_family,
                    category_id,
                    expected_category_id,
                )
            ),
        )
        for (
            team_id,
            specialist_id,
            source_id,
            source_family,
            category_id,
            expected_category_id,
        ) in keys
    )


def _watch_row(
    team_id: str,
    specialist_id: str,
    source_id: str,
    source_family: str,
    category_id: str,
    expected_category_id: str,
    rows: tuple[TeamSpecialistSourceReliabilityDecayWatchInputV2, ...],
    config: TeamSpecialistSourceReliabilityDecayWatchV2Config,
    generated_at: datetime,
) -> TeamSpecialistSourceReliabilityDecayWatchRowV2:
    recent_miss_count = _sum_inputs(rows, "recent_miss_count")
    contradiction_miss_count = _sum_inputs(rows, "contradiction_miss_count")
    sample_count = _sum_inputs(rows, "sample_count")
    latest_observed_at = max(row.observed_at for row in rows)
    oldest_source_last_verified_at = min(row.source_last_verified_at for row in rows)
    oldest_official_source_last_checked_at = min(
        row.official_source_last_checked_at for row in rows
    )
    source_age = _age_seconds(generated_at, oldest_source_last_verified_at)
    official_lag = _age_seconds(generated_at, oldest_official_source_last_checked_at)
    recent_miss_ratio = _ratio(recent_miss_count, sample_count)
    contradiction_miss_ratio = _ratio(contradiction_miss_count, sample_count)
    stale_component = _age_component(
        source_age,
        config.stale_source_use_threshold_seconds,
        config.max_stale_source_use_seconds,
    )
    official_lag_component = _age_component(
        official_lag,
        config.official_source_lag_threshold_seconds,
        config.max_official_source_lag_seconds,
    )
    sample_size_gap = _sample_size_gap(sample_count, config)
    category_mismatch = category_id != expected_category_id
    decay_score = _decay_score(
        recent_miss_ratio,
        stale_component,
        contradiction_miss_ratio,
        official_lag_component,
        category_mismatch,
        sample_size_gap,
        config,
    )
    reason_codes = _row_reason_codes(
        recent_miss_ratio,
        stale_component,
        contradiction_miss_ratio,
        official_lag_component,
        category_mismatch,
        sample_size_gap,
    )
    row_status = _row_status(reason_codes, decay_score, category_mismatch, config)
    public_source_refs = tuple(
        sorted({reference for row in rows for reference in row.public_source_refs}),
    )
    row_parts = dict(
        team_id=team_id,
        specialist_id=specialist_id,
        source_id=source_id,
        source_family=source_family,
        category_id=category_id,
        expected_category_id=expected_category_id,
        observation_count=_count(len(rows)),
        latest_observed_at=latest_observed_at,
        oldest_source_last_verified_at=oldest_source_last_verified_at,
        oldest_official_source_last_checked_at=oldest_official_source_last_checked_at,
        recent_miss_count=recent_miss_count,
        contradiction_miss_count=contradiction_miss_count,
        sample_count=sample_count,
        recent_miss_ratio=recent_miss_ratio,
        contradiction_miss_ratio=contradiction_miss_ratio,
        source_verification_age_seconds=source_age,
        official_source_lag_seconds=official_lag,
        stale_source_use_component=stale_component,
        official_source_lag_component=official_lag_component,
        sample_size_gap=sample_size_gap,
        decay_score=decay_score,
        category_mismatch=category_mismatch,
        row_status=row_status,
        public_source_refs=public_source_refs,
        reason_codes=reason_codes,
        paper_only=True,
        report_only=True,
        readonly=True,
    )
    return TeamSpecialistSourceReliabilityDecayWatchRowV2(
        **row_parts,
        derived_validation_digest=_digest_public(row_parts),
    )


def _age_component(
    age_seconds: Decimal,
    threshold_seconds: Decimal,
    max_seconds: Decimal,
) -> Decimal:
    if age_seconds <= threshold_seconds:
        return ZERO_RATIO
    if age_seconds >= max_seconds:
        return ONE_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            (age_seconds - threshold_seconds) / (max_seconds - threshold_seconds),
        )


def _sample_size_gap(
    sample_count: Decimal,
    config: TeamSpecialistSourceReliabilityDecayWatchV2Config,
) -> Decimal:
    if sample_count >= config.min_sample_count:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio((config.min_sample_count - sample_count) / config.min_sample_count)


def _decay_score(
    recent_miss_ratio: Decimal,
    stale_component: Decimal,
    contradiction_miss_ratio: Decimal,
    official_lag_component: Decimal,
    category_mismatch: bool,
    sample_size_gap: Decimal,
    config: TeamSpecialistSourceReliabilityDecayWatchV2Config,
) -> Decimal:
    category_component = ONE_RATIO if category_mismatch else ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            recent_miss_ratio * config.recent_miss_weight
            + stale_component * config.stale_source_use_weight
            + contradiction_miss_ratio * config.contradiction_miss_weight
            + official_lag_component * config.official_source_lag_weight
            + category_component * config.category_mismatch_weight
            + sample_size_gap * config.sample_size_weight,
        )


def _row_reason_codes(
    recent_miss_ratio: Decimal,
    stale_component: Decimal,
    contradiction_miss_ratio: Decimal,
    official_lag_component: Decimal,
    category_mismatch: bool,
    sample_size_gap: Decimal,
) -> tuple[str, ...]:
    codes: set[str] = set()
    if recent_miss_ratio > ZERO_RATIO:
        codes.add(RECENT_SOURCE_MISSES_REASON)
    if stale_component > ZERO_RATIO:
        codes.add(STALE_SOURCE_USE_REASON)
    if contradiction_miss_ratio > ZERO_RATIO:
        codes.add(CONTRADICTION_MISSES_REASON)
    if official_lag_component > ZERO_RATIO:
        codes.add(OFFICIAL_SOURCE_LAG_REASON)
    if category_mismatch:
        codes.add(CATEGORY_MISMATCH_REASON)
    if sample_size_gap > ZERO_RATIO:
        codes.add(LOW_SOURCE_SAMPLE_SIZE_REASON)
    if not codes:
        codes.add(SOURCE_RELIABILITY_DECAY_CLEAR_REASON)
    return tuple(code for code in ROW_REASON_CODES if code in codes)


def _row_status(
    reason_codes: tuple[str, ...],
    decay_score: Decimal,
    category_mismatch: bool,
    config: TeamSpecialistSourceReliabilityDecayWatchV2Config,
) -> str:
    if category_mismatch or decay_score >= config.critical_decay_score:
        return "critical"
    if reason_codes != (SOURCE_RELIABILITY_DECAY_CLEAR_REASON,):
        return "watch"
    if decay_score >= config.watch_decay_score:
        return "watch"
    return "clear"


def _report_reason_codes(
    rows: tuple[TeamSpecialistSourceReliabilityDecayWatchRowV2, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_SOURCES_REASON,)
    codes = {
        code
        for row in rows
        if row.row_status != "clear"
        for code in row.reason_codes
    }
    status = _report_status(rows)
    if status == "critical":
        codes.add(REPORT_CRITICAL_REASON)
    elif status == "watch":
        codes.add(REPORT_WATCH_REASON)
    if not codes:
        codes.add(SOURCE_RELIABILITY_DECAY_CLEAR_REASON)
    return tuple(code for code in REPORT_REASON_CODES if code in codes)


def _report_status(rows: tuple[TeamSpecialistSourceReliabilityDecayWatchRowV2, ...]) -> str:
    if not rows:
        return "watch"
    if any(row.row_status == "critical" for row in rows):
        return "critical"
    if any(row.row_status == "watch" for row in rows):
        return "watch"
    return "clear"


def _row_sort_key(
    row: TeamSpecialistSourceReliabilityDecayWatchRowV2,
) -> tuple[int, Decimal, str, str, str]:
    return (
        -_status_rank(row.row_status),
        -row.decay_score,
        row.team_id,
        row.specialist_id,
        row.source_id,
    )


def _status_rank(status: str) -> int:
    if status == "critical":
        return 2
    if status == "watch":
        return 1
    return 0


def _age_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    with localcontext(DECIMAL_CONTEXT):
        return (
            Decimal(delta.days) * SECONDS_PER_DAY
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / Decimal("1000000"))
        ).quantize(RATIO_QUANTUM)


def _sum_inputs(
    rows: tuple[TeamSpecialistSourceReliabilityDecayWatchInputV2, ...],
    field_name: str,
) -> Decimal:
    return _normalize_count(
        field_name,
        sum((getattr(row, field_name) for row in rows), ZERO_COUNT),
    )


def _sum_rows(
    rows: tuple[TeamSpecialistSourceReliabilityDecayWatchRowV2, ...],
    field_name: str,
) -> Decimal:
    return _normalize_count(
        field_name,
        sum((getattr(row, field_name) for row in rows), ZERO_COUNT),
    )


def _status_count(
    rows: tuple[TeamSpecialistSourceReliabilityDecayWatchRowV2, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.row_status == status))


def _reason_count(
    rows: tuple[TeamSpecialistSourceReliabilityDecayWatchRowV2, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _average_decay_score(
    rows: tuple[TeamSpecialistSourceReliabilityDecayWatchRowV2, ...],
) -> Decimal:
    if not rows:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            sum((row.decay_score for row in rows), ZERO_RATIO) / Decimal(len(rows)),
        )


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO_COUNT:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(numerator / denominator)


def _validate_row(row: TeamSpecialistSourceReliabilityDecayWatchRowV2) -> None:
    if row.observation_count <= ZERO_COUNT:
        raise ValueError("observation_count must be positive")
    if row.recent_miss_count > row.sample_count:
        raise ValueError("recent_miss_count must not exceed sample_count")
    if row.contradiction_miss_count > row.sample_count:
        raise ValueError("contradiction_miss_count must not exceed sample_count")
    if row.recent_miss_ratio != _ratio(row.recent_miss_count, row.sample_count):
        raise ValueError("recent_miss_ratio must match counts")
    if row.contradiction_miss_ratio != _ratio(
        row.contradiction_miss_count,
        row.sample_count,
    ):
        raise ValueError("contradiction_miss_ratio must match counts")
    if row.category_mismatch != (row.category_id != row.expected_category_id):
        raise ValueError("category_mismatch must match category fields")
    if row.reason_codes != _row_reason_codes(
        row.recent_miss_ratio,
        row.stale_source_use_component,
        row.contradiction_miss_ratio,
        row.official_source_lag_component,
        row.category_mismatch,
        row.sample_size_gap,
    ):
        raise ValueError("reason_codes must match watch row fields")
    if row.reason_codes == (SOURCE_RELIABILITY_DECAY_CLEAR_REASON,) and row.row_status != "clear":
        raise ValueError("clear reason requires clear status")
    if row.row_status == "clear" and row.reason_codes != (SOURCE_RELIABILITY_DECAY_CLEAR_REASON,):
        raise ValueError("clear status requires clear reason")
    if CATEGORY_MISMATCH_REASON in row.reason_codes and row.row_status != "critical":
        raise ValueError("category mismatch requires critical status")


def _validate_report(report: TeamSpecialistSourceReliabilityDecayWatchReportV2) -> None:
    if report.team_count != _count(len({row.team_id for row in report.rows})):
        raise ValueError("team_count must match rows")
    if report.specialist_team_count != _count(
        len({(row.team_id, row.specialist_id) for row in report.rows}),
    ):
        raise ValueError("specialist_team_count must match rows")
    if report.source_count != _count(len({row.source_id for row in report.rows})):
        raise ValueError("source_count must match rows")
    if report.observation_count != _sum_rows(report.rows, "observation_count"):
        raise ValueError("observation_count must match rows")
    if report.critical_count != _status_count(report.rows, "critical"):
        raise ValueError("critical_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.clear_count != _status_count(report.rows, "clear"):
        raise ValueError("clear_count must match rows")
    expected_counts = {
        "recent_miss_source_count": _reason_count(report.rows, RECENT_SOURCE_MISSES_REASON),
        "stale_source_use_count": _reason_count(report.rows, STALE_SOURCE_USE_REASON),
        "contradiction_miss_source_count": _reason_count(
            report.rows,
            CONTRADICTION_MISSES_REASON,
        ),
        "official_source_lag_count": _reason_count(report.rows, OFFICIAL_SOURCE_LAG_REASON),
        "category_mismatch_count": _reason_count(report.rows, CATEGORY_MISMATCH_REASON),
        "low_sample_size_count": _reason_count(report.rows, LOW_SOURCE_SAMPLE_SIZE_REASON),
    }
    for field_name, expected_count in expected_counts.items():
        if getattr(report, field_name) != expected_count:
            raise ValueError(f"{field_name} must match rows")
    if report.average_decay_score != _average_decay_score(report.rows):
        raise ValueError("average_decay_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")


def _normalize_rows(
    rows: tuple[TeamSpecialistSourceReliabilityDecayWatchRowV2, ...],
) -> tuple[TeamSpecialistSourceReliabilityDecayWatchRowV2, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not TeamSpecialistSourceReliabilityDecayWatchRowV2:
            raise ValueError(
                "rows must contain TeamSpecialistSourceReliabilityDecayWatchRowV2 values",
            )
        require_paper_only_flags("row", row)
    return rows


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain reason code strings")
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    normalized: list[str] = []
    for item in value:
        if type(item) is not str or item not in allowed_reason_codes:
            raise ValueError(f"{field_name} contains an unknown reason code")
        if item in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        normalized.append(item)
        seen.add(item)
    expected = tuple(code for code in allowed_reason_codes if code in seen)
    if tuple(normalized) != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return tuple(normalized)


def _normalize_public_refs(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain strings")
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    normalized: list[str] = []
    for item in value:
        _require_public_string(field_name, item)
        if not item.startswith(SAFE_REF_PREFIXES):
            raise ValueError(f"{field_name} contains an unsupported public reference")
        normalized.append(item)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    return tuple(normalized)


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return value.quantize(COUNT_QUANTUM)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    value = _normalize_count(field_name, value)
    if value <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return value


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    value = _normalize_nonnegative_decimal(field_name, value)
    if value <= ZERO_RATIO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value.quantize(RATIO_QUANTUM)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_RATIO or value > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return value.quantize(RATIO_QUANTUM)


def _clamp_ratio(value: Decimal) -> Decimal:
    if value < ZERO_RATIO:
        value = ZERO_RATIO
    if value > ONE_RATIO:
        value = ONE_RATIO
    return value.quantize(RATIO_QUANTUM)


def _require_ratio_total(*values: Decimal) -> None:
    with localcontext(DECIMAL_CONTEXT):
        if sum(values, ZERO_RATIO).quantize(RATIO_QUANTUM) != ONE_RATIO:
            raise ValueError("decay weights must sum to 1")


def _require_status(field_name: str, value: object) -> None:
    if value not in TEAM_SPECIALIST_SOURCE_RELIABILITY_DECAY_WATCH_V2_STATUSES:
        raise ValueError(f"{field_name} must be clear, watch, or critical")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_public_text(field_name, value)


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")


def _row_digest(row: TeamSpecialistSourceReliabilityDecayWatchRowV2) -> str:
    return _digest_public(_row_digest_parts(row))


def _report_digest(report: TeamSpecialistSourceReliabilityDecayWatchReportV2) -> str:
    return _digest_public(_report_digest_parts(report))


def _row_digest_parts(row: TeamSpecialistSourceReliabilityDecayWatchRowV2) -> dict[str, object]:
    return {
        "team_id": row.team_id,
        "specialist_id": row.specialist_id,
        "source_id": row.source_id,
        "source_family": row.source_family,
        "category_id": row.category_id,
        "expected_category_id": row.expected_category_id,
        "observation_count": row.observation_count,
        "latest_observed_at": row.latest_observed_at,
        "oldest_source_last_verified_at": row.oldest_source_last_verified_at,
        "oldest_official_source_last_checked_at": row.oldest_official_source_last_checked_at,
        "recent_miss_count": row.recent_miss_count,
        "contradiction_miss_count": row.contradiction_miss_count,
        "sample_count": row.sample_count,
        "recent_miss_ratio": row.recent_miss_ratio,
        "contradiction_miss_ratio": row.contradiction_miss_ratio,
        "source_verification_age_seconds": row.source_verification_age_seconds,
        "official_source_lag_seconds": row.official_source_lag_seconds,
        "stale_source_use_component": row.stale_source_use_component,
        "official_source_lag_component": row.official_source_lag_component,
        "sample_size_gap": row.sample_size_gap,
        "decay_score": row.decay_score,
        "category_mismatch": row.category_mismatch,
        "row_status": row.row_status,
        "public_source_refs": row.public_source_refs,
        "reason_codes": row.reason_codes,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _report_digest_parts(
    report: TeamSpecialistSourceReliabilityDecayWatchReportV2,
) -> dict[str, object]:
    return {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "team_count": report.team_count,
        "specialist_team_count": report.specialist_team_count,
        "source_count": report.source_count,
        "observation_count": report.observation_count,
        "critical_count": report.critical_count,
        "watch_count": report.watch_count,
        "clear_count": report.clear_count,
        "recent_miss_source_count": report.recent_miss_source_count,
        "stale_source_use_count": report.stale_source_use_count,
        "contradiction_miss_source_count": report.contradiction_miss_source_count,
        "official_source_lag_count": report.official_source_lag_count,
        "category_mismatch_count": report.category_mismatch_count,
        "low_sample_size_count": report.low_sample_size_count,
        "average_decay_score": report.average_decay_score,
        "status": report.status,
        "reason_codes": report.reason_codes,
        "rows": report.rows,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _digest_public(value: object) -> str:
    ready = _digest_ready(value)
    _reject_public_payload("derived validation digest", ready)
    return hashlib.sha256(
        json.dumps(ready, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()


def _digest_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _digest_ready(asdict(value))
    return json_ready_no_floats(value)


def _reject_public_payload(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public key in {label}")
            if _public_text_has_block(key):
                raise ValueError(f"unsafe public key in {label}")
            _reject_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_payload(label, item)
        return
    if type(value) is float:
        raise ValueError(f"unsafe public value in {label}")
    if type(value) is str:
        _reject_public_text(label, value)


def _reject_public_text(field_name: str, value: str) -> None:
    if _public_text_has_block(value):
        raise ValueError(f"unsafe public value in {field_name}")


def _public_text_has_block(value: str) -> bool:
    normalized = "".join(character for character in value.lower() if character.isalnum())
    return any(block in normalized for block in PUBLIC_TEXT_BLOCKS)


def _tupleify_payload_collections(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _tupleify_payload_collections(item) for key, item in value.items()}
    if isinstance(value, list):
        return tuple(_tupleify_payload_collections(item) for item in value)
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


__all__ = (
    "DEFAULT_TEAM_SPECIALIST_SOURCE_RELIABILITY_DECAY_WATCH_V2_CONFIG_VERSION",
    "TEAM_SPECIALIST_SOURCE_RELIABILITY_DECAY_WATCH_V2_STATUSES",
    "TeamSpecialistSourceReliabilityDecayWatchV2Config",
    "TeamSpecialistSourceReliabilityDecayWatchInputV2",
    "TeamSpecialistSourceReliabilityDecayWatchRowV2",
    "TeamSpecialistSourceReliabilityDecayWatchReportV2",
    "build_team_specialist_source_reliability_decay_watch_v2",
    "team_specialist_source_reliability_decay_watch_v2_payload",
)
