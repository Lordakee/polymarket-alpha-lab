"""Report-only cross-team memory decay router scorecard."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any, final


DEFAULT_RESEARCH_STRATEGY_CROSS_TEAM_MEMORY_DECAY_ROUTER_REPORT_CONFIG_VERSION = (
    "research-strategy-cross-team-memory-decay-router-report-v0"
)
RESEARCH_STRATEGY_CROSS_TEAM_MEMORY_DECAY_ROUTER_STATUSES = (
    "pass",
    "watch",
    "block",
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

REASON_CROSS_TEAM_MEMORY_SNAPSHOT_READY = "cross_team_memory_snapshot_ready"
REASON_CROSS_GROUP_MEMORY_REVIEW_REQUESTED = "cross_group_memory_review_requested"
REASON_MEMORY_DECAY_ROUTER_REVIEW_REQUESTED = (
    "memory_decay_router_review_requested"
)
REASON_ROW_PASS = "cross_team_memory_decay_router_pass"
REASON_MEMORY_HEALTH_BLOCK = "memory_health_block"
REASON_MEMORY_HEALTH_WATCH = "memory_health_watch"
REASON_MEMORY_RETENTION_BLOCK = "memory_retention_block"
REASON_MEMORY_RETENTION_WATCH = "memory_retention_watch"
REASON_MEMORY_AGE_BLOCK = "memory_age_block"
REASON_MEMORY_AGE_WATCH = "memory_age_watch"
REASON_MEMORY_DECAY_BLOCK = "memory_decay_block"
REASON_MEMORY_DECAY_WATCH = "memory_decay_watch"
REASON_DECAY_PRESSURE_BLOCK = "decay_pressure_block"
REASON_DECAY_PRESSURE_WATCH = "decay_pressure_watch"
REASON_CROSS_GROUP_ALIGNMENT_BLOCK = "cross_group_alignment_block"
REASON_CROSS_GROUP_ALIGNMENT_WATCH = "cross_group_alignment_watch"
REASON_REUSE_CONFIDENCE_BLOCK = "reuse_confidence_block"
REASON_REUSE_CONFIDENCE_WATCH = "reuse_confidence_watch"
REASON_HANDOFF_GAP_BLOCK = "handoff_gap_block"
REASON_HANDOFF_GAP_WATCH = "handoff_gap_watch"
REASON_REPORT_PASS = "cross_team_memory_decay_router_report_pass"
REASON_REPORT_WATCH = "cross_team_memory_decay_router_report_watch"
REASON_REPORT_BLOCK = "cross_team_memory_decay_router_report_block"
REASON_NO_SNAPSHOTS = "cross_team_memory_decay_router_no_snapshots"

UPSTREAM_REASON_CODES = (
    REASON_CROSS_TEAM_MEMORY_SNAPSHOT_READY,
    REASON_CROSS_GROUP_MEMORY_REVIEW_REQUESTED,
    REASON_MEMORY_DECAY_ROUTER_REVIEW_REQUESTED,
)
ROW_REASON_CODES = (
    REASON_ROW_PASS,
    REASON_CROSS_TEAM_MEMORY_SNAPSHOT_READY,
    REASON_CROSS_GROUP_MEMORY_REVIEW_REQUESTED,
    REASON_MEMORY_DECAY_ROUTER_REVIEW_REQUESTED,
    REASON_MEMORY_HEALTH_BLOCK,
    REASON_MEMORY_HEALTH_WATCH,
    REASON_MEMORY_RETENTION_BLOCK,
    REASON_MEMORY_RETENTION_WATCH,
    REASON_MEMORY_AGE_BLOCK,
    REASON_MEMORY_AGE_WATCH,
    REASON_MEMORY_DECAY_BLOCK,
    REASON_MEMORY_DECAY_WATCH,
    REASON_DECAY_PRESSURE_BLOCK,
    REASON_DECAY_PRESSURE_WATCH,
    REASON_CROSS_GROUP_ALIGNMENT_BLOCK,
    REASON_CROSS_GROUP_ALIGNMENT_WATCH,
    REASON_REUSE_CONFIDENCE_BLOCK,
    REASON_REUSE_CONFIDENCE_WATCH,
    REASON_HANDOFF_GAP_BLOCK,
    REASON_HANDOFF_GAP_WATCH,
)
REPORT_REASON_CODES = (
    REASON_REPORT_PASS,
    REASON_REPORT_WATCH,
    REASON_REPORT_BLOCK,
    REASON_NO_SNAPSHOTS,
    *ROW_REASON_CODES,
)
ROW_REASON_PRIORITY = (
    REASON_MEMORY_HEALTH_BLOCK,
    REASON_MEMORY_RETENTION_BLOCK,
    REASON_MEMORY_AGE_BLOCK,
    REASON_MEMORY_DECAY_BLOCK,
    REASON_DECAY_PRESSURE_BLOCK,
    REASON_CROSS_GROUP_ALIGNMENT_BLOCK,
    REASON_REUSE_CONFIDENCE_BLOCK,
    REASON_HANDOFF_GAP_BLOCK,
    REASON_MEMORY_HEALTH_WATCH,
    REASON_MEMORY_RETENTION_WATCH,
    REASON_MEMORY_AGE_WATCH,
    REASON_MEMORY_DECAY_WATCH,
    REASON_DECAY_PRESSURE_WATCH,
    REASON_CROSS_GROUP_ALIGNMENT_WATCH,
    REASON_REUSE_CONFIDENCE_WATCH,
    REASON_HANDOFF_GAP_WATCH,
    REASON_ROW_PASS,
    *UPSTREAM_REASON_CODES,
)
ROW_REASON_CANONICAL_PRIORITY = (
    REASON_ROW_PASS,
    *UPSTREAM_REASON_CODES,
    REASON_MEMORY_HEALTH_BLOCK,
    REASON_MEMORY_RETENTION_BLOCK,
    REASON_MEMORY_AGE_BLOCK,
    REASON_MEMORY_DECAY_BLOCK,
    REASON_DECAY_PRESSURE_BLOCK,
    REASON_CROSS_GROUP_ALIGNMENT_BLOCK,
    REASON_REUSE_CONFIDENCE_BLOCK,
    REASON_HANDOFF_GAP_BLOCK,
    REASON_MEMORY_HEALTH_WATCH,
    REASON_MEMORY_RETENTION_WATCH,
    REASON_MEMORY_AGE_WATCH,
    REASON_MEMORY_DECAY_WATCH,
    REASON_DECAY_PRESSURE_WATCH,
    REASON_CROSS_GROUP_ALIGNMENT_WATCH,
    REASON_REUSE_CONFIDENCE_WATCH,
    REASON_HANDOFF_GAP_WATCH,
)

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANT = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
MEMORY_DECAY_WATCH_RATIO = Decimal("0.200000")
MEMORY_DECAY_BLOCK_RATIO = Decimal("0.450000")
MEMORY_RETENTION_WEIGHT = Decimal("0.350000")
CROSS_GROUP_ALIGNMENT_WEIGHT = Decimal("0.200000")
REUSE_CONFIDENCE_WEIGHT = Decimal("0.150000")
MEMORY_FRESHNESS_WEIGHT = Decimal("0.200000")
HANDOFF_RELIEF_WEIGHT = Decimal("0.100000")
MEMORY_DECAY_PRESSURE_WEIGHT = Decimal("0.400000")
MEMORY_AGE_PRESSURE_WEIGHT = Decimal("0.300000")
HANDOFF_GAP_PRESSURE_WEIGHT = Decimal("0.300000")
DIGEST_FIELD = "derived_validation_digest"
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
PRIVATE_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
PUBLIC_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,159}$")
STATUS_VALUES = frozenset(RESEARCH_STRATEGY_CROSS_TEAM_MEMORY_DECAY_ROUTER_STATUSES)
FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
UNSAFE_PUBLIC_FRAGMENTS = (
    "raw",
    "candidate",
    "market",
    "slug",
    "question",
    "source",
    "url",
    "text",
    "dsn",
    "database",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "trading",
    "live",
    "position",
    "sizing",
    "recommend",
    "secret",
    "credential",
    "private",
    "http://",
    "https://",
    "://",
)

__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_CROSS_TEAM_MEMORY_DECAY_ROUTER_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_CROSS_TEAM_MEMORY_DECAY_ROUTER_STATUSES",
    "ResearchStrategyCrossTeamMemoryDecayRouterConfig",
    "ResearchStrategyCrossTeamMemoryDecayRouterReasonCount",
    "ResearchStrategyCrossTeamMemoryDecayRouterReport",
    "ResearchStrategyCrossTeamMemoryDecayRouterRow",
    "ResearchStrategyCrossTeamMemoryDecayRouterSnapshot",
    "build_research_strategy_cross_team_memory_decay_router_report",
    "research_strategy_cross_team_memory_decay_router_report_digest",
    "research_strategy_cross_team_memory_decay_router_report_payload",
    "validate_research_strategy_cross_team_memory_decay_router_report_public_payload",
)


class _FinalPublicDataclass:
    __slots__ = ()

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategyCrossTeamMemoryDecayRouterConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_CROSS_TEAM_MEMORY_DECAY_ROUTER_REPORT_CONFIG_VERSION
    )
    fresh_memory_age_seconds: Decimal = Decimal("3600.000000")
    stale_memory_age_seconds: Decimal = Decimal("86400.000000")
    min_pass_memory_health_score: Decimal = Decimal("0.700000")
    min_watch_memory_health_score: Decimal = Decimal("0.500000")
    min_pass_memory_retention_score: Decimal = Decimal("0.750000")
    min_watch_memory_retention_score: Decimal = Decimal("0.500000")
    min_pass_cross_group_alignment_score: Decimal = Decimal("0.700000")
    min_watch_cross_group_alignment_score: Decimal = Decimal("0.500000")
    min_pass_reuse_confidence_score: Decimal = Decimal("0.700000")
    min_watch_reuse_confidence_score: Decimal = Decimal("0.500000")
    max_pass_decay_pressure_score: Decimal = Decimal("0.200000")
    max_watch_decay_pressure_score: Decimal = Decimal("0.450000")
    max_pass_handoff_gap_score: Decimal = Decimal("0.200000")
    max_watch_handoff_gap_score: Decimal = Decimal("0.450000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyCrossTeamMemoryDecayRouterConfig,
            "config",
        )
        raw_fresh_memory_age_seconds = self.fresh_memory_age_seconds
        raw_stale_memory_age_seconds = self.stale_memory_age_seconds
        raw_thresholds = {
            name: getattr(self, name)
            for name in (
                "min_pass_memory_health_score",
                "min_watch_memory_health_score",
                "min_pass_memory_retention_score",
                "min_watch_memory_retention_score",
                "min_pass_cross_group_alignment_score",
                "min_watch_cross_group_alignment_score",
                "min_pass_reuse_confidence_score",
                "min_watch_reuse_confidence_score",
                "max_pass_decay_pressure_score",
                "max_watch_decay_pressure_score",
                "max_pass_handoff_gap_score",
                "max_watch_handoff_gap_score",
            )
        }
        object.__setattr__(
            self,
            "config_version",
            _require_public_id("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_CROSS_TEAM_MEMORY_DECAY_ROUTER_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for name in ("fresh_memory_age_seconds", "stale_memory_age_seconds"):
            object.__setattr__(
                self,
                name,
                _require_positive_decimal(name, getattr(self, name)),
            )
        for name in (
            "min_pass_memory_health_score",
            "min_watch_memory_health_score",
            "min_pass_memory_retention_score",
            "min_watch_memory_retention_score",
            "min_pass_cross_group_alignment_score",
            "min_watch_cross_group_alignment_score",
            "min_pass_reuse_confidence_score",
            "min_watch_reuse_confidence_score",
            "max_pass_decay_pressure_score",
            "max_watch_decay_pressure_score",
            "max_pass_handoff_gap_score",
            "max_watch_handoff_gap_score",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        if raw_fresh_memory_age_seconds > raw_stale_memory_age_seconds:
            raise ValueError(
                "fresh_memory_age_seconds must not exceed stale_memory_age_seconds",
            )
        _require_floor_pair(
            "min_pass_memory_health_score",
            raw_thresholds["min_pass_memory_health_score"],
            "min_watch_memory_health_score",
            raw_thresholds["min_watch_memory_health_score"],
        )
        _require_floor_pair(
            "min_pass_memory_retention_score",
            raw_thresholds["min_pass_memory_retention_score"],
            "min_watch_memory_retention_score",
            raw_thresholds["min_watch_memory_retention_score"],
        )
        _require_floor_pair(
            "min_pass_cross_group_alignment_score",
            raw_thresholds["min_pass_cross_group_alignment_score"],
            "min_watch_cross_group_alignment_score",
            raw_thresholds["min_watch_cross_group_alignment_score"],
        )
        _require_floor_pair(
            "min_pass_reuse_confidence_score",
            raw_thresholds["min_pass_reuse_confidence_score"],
            "min_watch_reuse_confidence_score",
            raw_thresholds["min_watch_reuse_confidence_score"],
        )
        _require_ceiling_pair(
            "max_pass_decay_pressure_score",
            raw_thresholds["max_pass_decay_pressure_score"],
            "max_watch_decay_pressure_score",
            raw_thresholds["max_watch_decay_pressure_score"],
        )
        _require_ceiling_pair(
            "max_pass_handoff_gap_score",
            raw_thresholds["max_pass_handoff_gap_score"],
            "max_watch_handoff_gap_score",
            raw_thresholds["max_watch_handoff_gap_score"],
        )
        if self.fresh_memory_age_seconds > self.stale_memory_age_seconds:
            raise ValueError(
                "fresh_memory_age_seconds must not exceed stale_memory_age_seconds",
            )
        _require_floor_pair(
            "min_pass_memory_health_score",
            self.min_pass_memory_health_score,
            "min_watch_memory_health_score",
            self.min_watch_memory_health_score,
        )
        _require_floor_pair(
            "min_pass_memory_retention_score",
            self.min_pass_memory_retention_score,
            "min_watch_memory_retention_score",
            self.min_watch_memory_retention_score,
        )
        _require_floor_pair(
            "min_pass_cross_group_alignment_score",
            self.min_pass_cross_group_alignment_score,
            "min_watch_cross_group_alignment_score",
            self.min_watch_cross_group_alignment_score,
        )
        _require_floor_pair(
            "min_pass_reuse_confidence_score",
            self.min_pass_reuse_confidence_score,
            "min_watch_reuse_confidence_score",
            self.min_watch_reuse_confidence_score,
        )
        _require_ceiling_pair(
            "max_pass_decay_pressure_score",
            self.max_pass_decay_pressure_score,
            "max_watch_decay_pressure_score",
            self.max_watch_decay_pressure_score,
        )
        _require_ceiling_pair(
            "max_pass_handoff_gap_score",
            self.max_pass_handoff_gap_score,
            "max_watch_handoff_gap_score",
            self.max_watch_handoff_gap_score,
        )
        _require_hard_flags("config", self)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategyCrossTeamMemoryDecayRouterSnapshot(_FinalPublicDataclass):
    route_ref: str
    lead_group_ref: str
    peer_group_ref: str
    observed_at: datetime
    last_memory_refresh_at: datetime
    baseline_memory_score: Decimal
    current_memory_score: Decimal
    cross_group_alignment_score: Decimal
    reuse_confidence_score: Decimal
    handoff_gap_score: Decimal
    reason_codes: tuple[str, ...] = (REASON_CROSS_TEAM_MEMORY_SNAPSHOT_READY,)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyCrossTeamMemoryDecayRouterSnapshot,
            "snapshot",
        )
        raw_baseline_memory_score = self.baseline_memory_score
        raw_current_memory_score = self.current_memory_score
        for name in ("route_ref", "lead_group_ref", "peer_group_ref"):
            _require_private_ref(name, getattr(self, name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "last_memory_refresh_at",
            _as_utc("last_memory_refresh_at", self.last_memory_refresh_at),
        )
        object.__setattr__(
            self,
            "baseline_memory_score",
            _require_positive_ratio_decimal(
                "baseline_memory_score",
                self.baseline_memory_score,
            ),
        )
        object.__setattr__(
            self,
            "current_memory_score",
            _require_ratio_decimal("current_memory_score", self.current_memory_score),
        )
        if raw_current_memory_score > raw_baseline_memory_score:
            raise ValueError("current_memory_score must not exceed baseline_memory_score")
        if self.current_memory_score > self.baseline_memory_score:
            raise ValueError("current_memory_score must not exceed baseline_memory_score")
        for name in (
            "cross_group_alignment_score",
            "reuse_confidence_score",
            "handoff_gap_score",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        reason_codes = _require_reason_codes(
            "reason_codes",
            self.reason_codes,
            UPSTREAM_REASON_CODES,
            require_nonempty=True,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _canonical_reason_codes(reason_codes, UPSTREAM_REASON_CODES),
        )
        _require_hard_flags("snapshot", self)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategyCrossTeamMemoryDecayRouterRow(_FinalPublicDataclass):
    aggregate_row_number: Decimal
    route_digest: str
    lead_group_digest: str
    peer_group_digest: str
    status: str
    baseline_memory_score: Decimal
    current_memory_score: Decimal
    memory_retention_score: Decimal
    memory_decay_ratio: Decimal
    memory_age_seconds: Decimal
    memory_age_pressure_score: Decimal
    decay_pressure_score: Decimal
    cross_group_alignment_score: Decimal
    reuse_confidence_score: Decimal
    handoff_gap_score: Decimal
    memory_health_score: Decimal
    observed_at: datetime
    last_memory_refresh_at: datetime
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyCrossTeamMemoryDecayRouterRow,
            "row",
        )
        raw_baseline_memory_score = self.baseline_memory_score
        raw_current_memory_score = self.current_memory_score
        object.__setattr__(
            self,
            "aggregate_row_number",
            _require_count_decimal("aggregate_row_number", self.aggregate_row_number),
        )
        for name in ("route_digest", "lead_group_digest", "peer_group_digest"):
            _require_private_digest(name, getattr(self, name))
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "baseline_memory_score",
            _require_positive_ratio_decimal(
                "baseline_memory_score",
                self.baseline_memory_score,
            ),
        )
        object.__setattr__(
            self,
            "current_memory_score",
            _require_ratio_decimal("current_memory_score", self.current_memory_score),
        )
        if raw_current_memory_score > raw_baseline_memory_score:
            raise ValueError("current_memory_score must not exceed baseline_memory_score")
        if self.current_memory_score > self.baseline_memory_score:
            raise ValueError("current_memory_score must not exceed baseline_memory_score")
        for name in (
            "memory_retention_score",
            "memory_decay_ratio",
            "memory_age_pressure_score",
            "decay_pressure_score",
            "cross_group_alignment_score",
            "reuse_confidence_score",
            "handoff_gap_score",
            "memory_health_score",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        object.__setattr__(
            self,
            "memory_age_seconds",
            _require_nonnegative_decimal("memory_age_seconds", self.memory_age_seconds),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "last_memory_refresh_at",
            _as_utc("last_memory_refresh_at", self.last_memory_refresh_at),
        )
        reason_codes = _require_reason_codes(
            "reason_codes",
            self.reason_codes,
            ROW_REASON_CODES,
            require_nonempty=True,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _canonical_reason_codes(
                reason_codes,
                ROW_REASON_CANONICAL_PRIORITY,
            ),
        )
        _validate_row_source_derivations(self)
        _validate_row_reason_status(self)
        _require_hard_flags("row", self)
        expected_digest = _payload_digest(_row_payload(self, include_digest=False))
        if self.derived_validation_digest:
            _require_digest(DIGEST_FIELD, self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match row payload")
        object.__setattr__(self, DIGEST_FIELD, expected_digest)
        _reject_unsafe_public_payload(
            "row",
            _row_payload(self, include_digest=True),
        )

    @property
    def public_payload(self) -> dict[str, Any]:
        return _validated_row_public_payload(self)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategyCrossTeamMemoryDecayRouterReasonCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyCrossTeamMemoryDecayRouterReasonCount,
            "reason_count",
        )
        object.__setattr__(
            self,
            "reason_code",
            _require_reason_code("reason_code", self.reason_code, REPORT_REASON_CODES),
        )
        object.__setattr__(self, "count", _require_count_decimal("count", self.count))
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason_count", self)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategyCrossTeamMemoryDecayRouterReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    config: ResearchStrategyCrossTeamMemoryDecayRouterConfig
    status: str
    snapshot_count: Decimal
    route_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_memory_health_score: Decimal
    lowest_memory_health_score: Decimal
    highest_memory_decay_ratio: Decimal
    highest_memory_age_seconds: Decimal
    highest_decay_pressure_score: Decimal
    lowest_cross_group_alignment_score: Decimal
    lowest_reuse_confidence_score: Decimal
    highest_handoff_gap_score: Decimal
    reason_codes: tuple[str, ...]
    reason_counts: tuple[ResearchStrategyCrossTeamMemoryDecayRouterReasonCount, ...]
    rows: tuple[ResearchStrategyCrossTeamMemoryDecayRouterRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyCrossTeamMemoryDecayRouterReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_id("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_CROSS_TEAM_MEMORY_DECAY_ROUTER_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_exact_type(
            self.config,
            ResearchStrategyCrossTeamMemoryDecayRouterConfig,
            "config",
        )
        _require_hard_flags("config", self.config)
        if self.config_version != self.config.config_version:
            raise ValueError("config_version must match config")
        _require_status("status", self.status)
        for name in (
            "snapshot_count",
            "route_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(self, name, _require_count_decimal(name, getattr(self, name)))
        for name in (
            "average_memory_health_score",
            "lowest_memory_health_score",
            "highest_memory_decay_ratio",
            "highest_decay_pressure_score",
            "lowest_cross_group_alignment_score",
            "lowest_reuse_confidence_score",
            "highest_handoff_gap_score",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        object.__setattr__(
            self,
            "highest_memory_age_seconds",
            _require_nonnegative_decimal(
                "highest_memory_age_seconds",
                self.highest_memory_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
                require_nonempty=True,
            ),
        )
        object.__setattr__(self, "rows", _require_rows(self.rows))
        object.__setattr__(
            self,
            "reason_counts",
            _require_reason_counts(self.reason_counts),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        expected_digest = _payload_digest(_report_payload(self, include_digest=False))
        if self.derived_validation_digest:
            _require_digest(DIGEST_FIELD, self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report payload")
        object.__setattr__(self, DIGEST_FIELD, expected_digest)
        _reject_unsafe_public_payload(
            "report",
            _report_payload(self, include_digest=True),
        )

    @property
    def public_payload(self) -> dict[str, Any]:
        return _validated_report_public_payload(self)


def build_research_strategy_cross_team_memory_decay_router_report(
    snapshots: Iterable[ResearchStrategyCrossTeamMemoryDecayRouterSnapshot],
    *,
    config: ResearchStrategyCrossTeamMemoryDecayRouterConfig,
    generated_at: datetime,
) -> ResearchStrategyCrossTeamMemoryDecayRouterReport:
    _revalidate_config_for_build(config)
    generated_at = _as_utc("generated_at", generated_at)
    items = _normalize_snapshots(snapshots)
    row_parts = tuple(_row_part_from_snapshot(item, config, generated_at) for item in items)
    sorted_parts = sorted(row_parts, key=_row_part_sort_key)
    rows = tuple(
        _row_from_part(part, row_number=index)
        for index, part in enumerate(sorted_parts, start=1)
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchStrategyCrossTeamMemoryDecayRouterReport(
        generated_at=generated_at,
        config_version=config.config_version,
        config=config,
        status=_report_status(rows),
        snapshot_count=_count_decimal(len(rows)),
        route_count=_count_decimal(len({row.route_digest for row in rows})),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        average_memory_health_score=_average_decimal(
            tuple(row.memory_health_score for row in rows),
        ),
        lowest_memory_health_score=_min_decimal(tuple(row.memory_health_score for row in rows)),
        highest_memory_decay_ratio=_max_decimal(tuple(row.memory_decay_ratio for row in rows)),
        highest_memory_age_seconds=_max_decimal(tuple(row.memory_age_seconds for row in rows)),
        highest_decay_pressure_score=_max_decimal(
            tuple(row.decay_pressure_score for row in rows),
        ),
        lowest_cross_group_alignment_score=_min_decimal(
            tuple(row.cross_group_alignment_score for row in rows),
        ),
        lowest_reuse_confidence_score=_min_decimal(
            tuple(row.reuse_confidence_score for row in rows),
        ),
        highest_handoff_gap_score=_max_decimal(tuple(row.handoff_gap_score for row in rows)),
        reason_codes=reason_codes,
        reason_counts=_reason_counts(rows),
        rows=rows,
    )


def research_strategy_cross_team_memory_decay_router_report_payload(
    report: ResearchStrategyCrossTeamMemoryDecayRouterReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyCrossTeamMemoryDecayRouterReport:
        payload = report.public_payload
    elif type(report) is dict:
        payload = _validate_payload_dict(report)
    else:
        raise ValueError(
            "report must be a ResearchStrategyCrossTeamMemoryDecayRouterReport",
        )
    validate_research_strategy_cross_team_memory_decay_router_report_public_payload(
        payload,
    )
    return payload


def validate_research_strategy_cross_team_memory_decay_router_report_public_payload(
    payload: dict[str, Any],
) -> None:
    _validate_report_public_payload_dict(payload)


def _validate_report_public_payload_dict(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _require_public_schema_fields(
        "payload",
        payload,
        ResearchStrategyCrossTeamMemoryDecayRouterReport,
    )
    _reject_raw_numeric_payload_values(payload)
    _reject_unsafe_public_payload("payload", payload)
    _validate_payload_digest(payload)
    canonical_payload = _report_payload(
        _report_from_public_payload(payload),
        include_digest=True,
    )
    if payload != canonical_payload:
        raise ValueError("public payload must use canonical schema values")


def research_strategy_cross_team_memory_decay_router_report_digest(
    report: ResearchStrategyCrossTeamMemoryDecayRouterReport,
) -> str:
    if type(report) is not ResearchStrategyCrossTeamMemoryDecayRouterReport:
        raise ValueError("report must be a ResearchStrategyCrossTeamMemoryDecayRouterReport")
    _revalidate_report_for_payload(report)
    return report.derived_validation_digest


def _row_part_from_snapshot(
    snapshot: ResearchStrategyCrossTeamMemoryDecayRouterSnapshot,
    config: ResearchStrategyCrossTeamMemoryDecayRouterConfig,
    generated_at: datetime,
) -> dict[str, Any]:
    if snapshot.observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    if snapshot.last_memory_refresh_at > generated_at:
        raise ValueError("last_memory_refresh_at must not be after generated_at")
    memory_age_seconds = _seconds_between(snapshot.last_memory_refresh_at, generated_at)
    memory_retention_score = _divide_decimal(
        snapshot.current_memory_score,
        snapshot.baseline_memory_score,
    )
    memory_decay_ratio = _subtract_decimal(ONE, memory_retention_score)
    memory_age_pressure_score = _memory_age_pressure_score(memory_age_seconds, config)
    decay_pressure_score = _decay_pressure_score(
        memory_decay_ratio=memory_decay_ratio,
        memory_age_pressure_score=memory_age_pressure_score,
        handoff_gap_score=snapshot.handoff_gap_score,
    )
    memory_health_score = _memory_health_score(
        memory_retention_score=memory_retention_score,
        cross_group_alignment_score=snapshot.cross_group_alignment_score,
        reuse_confidence_score=snapshot.reuse_confidence_score,
        memory_age_pressure_score=memory_age_pressure_score,
        handoff_gap_score=snapshot.handoff_gap_score,
    )
    status = _row_status(
        memory_health_score=memory_health_score,
        memory_retention_score=memory_retention_score,
        memory_age_seconds=memory_age_seconds,
        memory_decay_ratio=memory_decay_ratio,
        decay_pressure_score=decay_pressure_score,
        cross_group_alignment_score=snapshot.cross_group_alignment_score,
        reuse_confidence_score=snapshot.reuse_confidence_score,
        handoff_gap_score=snapshot.handoff_gap_score,
        config=config,
    )
    return {
        "route_digest": _digest_ref(snapshot.route_ref),
        "lead_group_digest": _digest_ref(snapshot.lead_group_ref),
        "peer_group_digest": _digest_ref(snapshot.peer_group_ref),
        "status": status,
        "baseline_memory_score": snapshot.baseline_memory_score,
        "current_memory_score": snapshot.current_memory_score,
        "memory_retention_score": memory_retention_score,
        "memory_decay_ratio": memory_decay_ratio,
        "memory_age_seconds": memory_age_seconds,
        "memory_age_pressure_score": memory_age_pressure_score,
        "decay_pressure_score": decay_pressure_score,
        "cross_group_alignment_score": snapshot.cross_group_alignment_score,
        "reuse_confidence_score": snapshot.reuse_confidence_score,
        "handoff_gap_score": snapshot.handoff_gap_score,
        "memory_health_score": memory_health_score,
        "observed_at": snapshot.observed_at,
        "last_memory_refresh_at": snapshot.last_memory_refresh_at,
        "reason_codes": _row_reason_codes(
            status=status,
            snapshot=snapshot,
            memory_health_score=memory_health_score,
            memory_retention_score=memory_retention_score,
            memory_age_seconds=memory_age_seconds,
            memory_decay_ratio=memory_decay_ratio,
            decay_pressure_score=decay_pressure_score,
            config=config,
        ),
    }


def _row_from_part(part: dict[str, Any], *, row_number: int) -> ResearchStrategyCrossTeamMemoryDecayRouterRow:
    return ResearchStrategyCrossTeamMemoryDecayRouterRow(
        aggregate_row_number=_count_decimal(row_number),
        route_digest=part["route_digest"],
        lead_group_digest=part["lead_group_digest"],
        peer_group_digest=part["peer_group_digest"],
        status=part["status"],
        baseline_memory_score=part["baseline_memory_score"],
        current_memory_score=part["current_memory_score"],
        memory_retention_score=part["memory_retention_score"],
        memory_decay_ratio=part["memory_decay_ratio"],
        memory_age_seconds=part["memory_age_seconds"],
        memory_age_pressure_score=part["memory_age_pressure_score"],
        decay_pressure_score=part["decay_pressure_score"],
        cross_group_alignment_score=part["cross_group_alignment_score"],
        reuse_confidence_score=part["reuse_confidence_score"],
        handoff_gap_score=part["handoff_gap_score"],
        memory_health_score=part["memory_health_score"],
        observed_at=part["observed_at"],
        last_memory_refresh_at=part["last_memory_refresh_at"],
        reason_codes=part["reason_codes"],
    )


def _row_part_sort_key(part: dict[str, Any]) -> tuple[object, ...]:
    return (
        {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[part["status"]],
        part["memory_health_score"],
        part["route_digest"],
        part["lead_group_digest"],
        part["peer_group_digest"],
        part["baseline_memory_score"],
        part["current_memory_score"],
        part["observed_at"],
        part["last_memory_refresh_at"],
        part["memory_retention_score"],
        part["memory_decay_ratio"],
        part["memory_age_seconds"],
        part["memory_age_pressure_score"],
        part["decay_pressure_score"],
        part["cross_group_alignment_score"],
        part["reuse_confidence_score"],
        part["handoff_gap_score"],
        part["reason_codes"],
    )


def _row_sort_key(
    row: ResearchStrategyCrossTeamMemoryDecayRouterRow,
) -> tuple[object, ...]:
    return (
        {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[row.status],
        row.memory_health_score,
        row.route_digest,
        row.lead_group_digest,
        row.peer_group_digest,
        row.baseline_memory_score,
        row.current_memory_score,
        row.observed_at,
        row.last_memory_refresh_at,
        row.memory_retention_score,
        row.memory_decay_ratio,
        row.memory_age_seconds,
        row.memory_age_pressure_score,
        row.decay_pressure_score,
        row.cross_group_alignment_score,
        row.reuse_confidence_score,
        row.handoff_gap_score,
        row.reason_codes,
    )


def _row_status(
    *,
    memory_health_score: Decimal,
    memory_retention_score: Decimal,
    memory_age_seconds: Decimal,
    memory_decay_ratio: Decimal,
    decay_pressure_score: Decimal,
    cross_group_alignment_score: Decimal,
    reuse_confidence_score: Decimal,
    handoff_gap_score: Decimal,
    config: ResearchStrategyCrossTeamMemoryDecayRouterConfig,
) -> str:
    if (
        memory_health_score < config.min_watch_memory_health_score
        or memory_retention_score < config.min_watch_memory_retention_score
        or memory_age_seconds >= config.stale_memory_age_seconds
        or memory_decay_ratio > MEMORY_DECAY_BLOCK_RATIO
        or decay_pressure_score > config.max_watch_decay_pressure_score
        or cross_group_alignment_score < config.min_watch_cross_group_alignment_score
        or reuse_confidence_score < config.min_watch_reuse_confidence_score
        or handoff_gap_score > config.max_watch_handoff_gap_score
    ):
        return STATUS_BLOCK
    if (
        memory_health_score < config.min_pass_memory_health_score
        or memory_retention_score < config.min_pass_memory_retention_score
        or memory_age_seconds > config.fresh_memory_age_seconds
        or memory_decay_ratio > MEMORY_DECAY_WATCH_RATIO
        or decay_pressure_score > config.max_pass_decay_pressure_score
        or cross_group_alignment_score < config.min_pass_cross_group_alignment_score
        or reuse_confidence_score < config.min_pass_reuse_confidence_score
        or handoff_gap_score > config.max_pass_handoff_gap_score
    ):
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    *,
    status: str,
    snapshot: ResearchStrategyCrossTeamMemoryDecayRouterSnapshot,
    memory_health_score: Decimal,
    memory_retention_score: Decimal,
    memory_age_seconds: Decimal,
    memory_decay_ratio: Decimal,
    decay_pressure_score: Decimal,
    config: ResearchStrategyCrossTeamMemoryDecayRouterConfig,
) -> tuple[str, ...]:
    return _row_reason_codes_from_values(
        status=status,
        upstream_reason_codes=snapshot.reason_codes,
        memory_health_score=memory_health_score,
        memory_retention_score=memory_retention_score,
        memory_age_seconds=memory_age_seconds,
        memory_decay_ratio=memory_decay_ratio,
        decay_pressure_score=decay_pressure_score,
        cross_group_alignment_score=snapshot.cross_group_alignment_score,
        reuse_confidence_score=snapshot.reuse_confidence_score,
        handoff_gap_score=snapshot.handoff_gap_score,
        config=config,
    )


def _row_reason_codes_from_values(
    *,
    status: str,
    upstream_reason_codes: tuple[str, ...],
    memory_health_score: Decimal,
    memory_retention_score: Decimal,
    memory_age_seconds: Decimal,
    memory_decay_ratio: Decimal,
    decay_pressure_score: Decimal,
    cross_group_alignment_score: Decimal,
    reuse_confidence_score: Decimal,
    handoff_gap_score: Decimal,
    config: ResearchStrategyCrossTeamMemoryDecayRouterConfig,
) -> tuple[str, ...]:
    if status == STATUS_PASS:
        return _unique_reason_codes((REASON_ROW_PASS, *upstream_reason_codes))
    reasons = list(upstream_reason_codes)
    if memory_health_score < config.min_watch_memory_health_score:
        reasons.append(REASON_MEMORY_HEALTH_BLOCK)
    elif memory_health_score < config.min_pass_memory_health_score:
        reasons.append(REASON_MEMORY_HEALTH_WATCH)
    if memory_retention_score < config.min_watch_memory_retention_score:
        reasons.append(REASON_MEMORY_RETENTION_BLOCK)
    elif memory_retention_score < config.min_pass_memory_retention_score:
        reasons.append(REASON_MEMORY_RETENTION_WATCH)
    if memory_age_seconds >= config.stale_memory_age_seconds:
        reasons.append(REASON_MEMORY_AGE_BLOCK)
    elif memory_age_seconds > config.fresh_memory_age_seconds:
        reasons.append(REASON_MEMORY_AGE_WATCH)
    if memory_decay_ratio > MEMORY_DECAY_BLOCK_RATIO:
        reasons.append(REASON_MEMORY_DECAY_BLOCK)
    elif memory_decay_ratio > MEMORY_DECAY_WATCH_RATIO:
        reasons.append(REASON_MEMORY_DECAY_WATCH)
    if decay_pressure_score > config.max_watch_decay_pressure_score:
        reasons.append(REASON_DECAY_PRESSURE_BLOCK)
    elif decay_pressure_score > config.max_pass_decay_pressure_score:
        reasons.append(REASON_DECAY_PRESSURE_WATCH)
    if cross_group_alignment_score < config.min_watch_cross_group_alignment_score:
        reasons.append(REASON_CROSS_GROUP_ALIGNMENT_BLOCK)
    elif cross_group_alignment_score < config.min_pass_cross_group_alignment_score:
        reasons.append(REASON_CROSS_GROUP_ALIGNMENT_WATCH)
    if reuse_confidence_score < config.min_watch_reuse_confidence_score:
        reasons.append(REASON_REUSE_CONFIDENCE_BLOCK)
    elif reuse_confidence_score < config.min_pass_reuse_confidence_score:
        reasons.append(REASON_REUSE_CONFIDENCE_WATCH)
    if handoff_gap_score > config.max_watch_handoff_gap_score:
        reasons.append(REASON_HANDOFF_GAP_BLOCK)
    elif handoff_gap_score > config.max_pass_handoff_gap_score:
        reasons.append(REASON_HANDOFF_GAP_WATCH)
    return _unique_reason_codes(tuple(reasons))


def _memory_age_pressure_score(
    memory_age_seconds: Decimal,
    config: ResearchStrategyCrossTeamMemoryDecayRouterConfig,
) -> Decimal:
    if memory_age_seconds <= config.fresh_memory_age_seconds:
        return ZERO
    if memory_age_seconds >= config.stale_memory_age_seconds:
        return ONE
    return _divide_decimal(
        _subtract_decimal(memory_age_seconds, config.fresh_memory_age_seconds),
        _subtract_decimal(
            config.stale_memory_age_seconds,
            config.fresh_memory_age_seconds,
        ),
    )


def _decay_pressure_score(
    *,
    memory_decay_ratio: Decimal,
    memory_age_pressure_score: Decimal,
    handoff_gap_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(
            (memory_decay_ratio * MEMORY_DECAY_PRESSURE_WEIGHT)
            + (memory_age_pressure_score * MEMORY_AGE_PRESSURE_WEIGHT)
            + (handoff_gap_score * HANDOFF_GAP_PRESSURE_WEIGHT),
        )


def _memory_health_score(
    *,
    memory_retention_score: Decimal,
    cross_group_alignment_score: Decimal,
    reuse_confidence_score: Decimal,
    memory_age_pressure_score: Decimal,
    handoff_gap_score: Decimal,
) -> Decimal:
    memory_freshness_score = _subtract_decimal(ONE, memory_age_pressure_score)
    handoff_relief_score = _subtract_decimal(ONE, handoff_gap_score)
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(
            (memory_retention_score * MEMORY_RETENTION_WEIGHT)
            + (cross_group_alignment_score * CROSS_GROUP_ALIGNMENT_WEIGHT)
            + (reuse_confidence_score * REUSE_CONFIDENCE_WEIGHT)
            + (memory_freshness_score * MEMORY_FRESHNESS_WEIGHT)
            + (handoff_relief_score * HANDOFF_RELIEF_WEIGHT),
        )


def _report_status(rows: tuple[ResearchStrategyCrossTeamMemoryDecayRouterRow, ...]) -> str:
    if not rows or any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchStrategyCrossTeamMemoryDecayRouterRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (REASON_REPORT_BLOCK, REASON_NO_SNAPSHOTS)
    status_reason = {
        STATUS_PASS: REASON_REPORT_PASS,
        STATUS_WATCH: REASON_REPORT_WATCH,
        STATUS_BLOCK: REASON_REPORT_BLOCK,
    }[_report_status(rows)]
    present = Counter(reason for row in rows for reason in row.reason_codes)
    ordered = [status_reason]
    ordered.extend(reason for reason in ROW_REASON_PRIORITY if present[reason] > 0)
    return _unique_reason_codes(tuple(ordered))


def _reason_counts(
    rows: tuple[ResearchStrategyCrossTeamMemoryDecayRouterRow, ...],
) -> tuple[ResearchStrategyCrossTeamMemoryDecayRouterReasonCount, ...]:
    if not rows:
        return (
            ResearchStrategyCrossTeamMemoryDecayRouterReasonCount(
                reason_code=REASON_NO_SNAPSHOTS,
                count=_count_decimal(1),
                row_ratio=ONE,
            ),
        )
    row_count = _count_decimal(len(rows))
    counter = Counter(reason for row in rows for reason in row.reason_codes)
    ordered_codes = tuple(
        reason
        for reason in ROW_REASON_PRIORITY
        if counter[reason] > 0
    ) + tuple(
        reason
        for reason in sorted(counter)
        if reason not in ROW_REASON_PRIORITY
    )
    return tuple(
        ResearchStrategyCrossTeamMemoryDecayRouterReasonCount(
            reason_code=reason,
            count=_count_decimal(counter[reason]),
            row_ratio=_divide_decimal(_count_decimal(counter[reason]), row_count),
        )
        for reason in ordered_codes
    )


def _status_count(
    rows: tuple[ResearchStrategyCrossTeamMemoryDecayRouterRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _normalize_snapshots(
    snapshots: Iterable[ResearchStrategyCrossTeamMemoryDecayRouterSnapshot],
) -> tuple[ResearchStrategyCrossTeamMemoryDecayRouterSnapshot, ...]:
    if isinstance(snapshots, (str, bytes)):
        raise ValueError("snapshots must be an iterable of snapshots")
    normalized = tuple(snapshots)
    for item in normalized:
        _revalidate_snapshot_for_build(item)
    return normalized


def _revalidate_config_for_build(
    config: ResearchStrategyCrossTeamMemoryDecayRouterConfig,
) -> None:
    _require_exact_type(
        config,
        ResearchStrategyCrossTeamMemoryDecayRouterConfig,
        "config",
    )
    _require_public_id("config_version", config.config_version)
    if (
        config.config_version
        != DEFAULT_RESEARCH_STRATEGY_CROSS_TEAM_MEMORY_DECAY_ROUTER_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")

    for name in ("fresh_memory_age_seconds", "stale_memory_age_seconds"):
        _require_canonical_decimal(name, getattr(config, name), _require_positive_decimal)
    for name in (
        "min_pass_memory_health_score",
        "min_watch_memory_health_score",
        "min_pass_memory_retention_score",
        "min_watch_memory_retention_score",
        "min_pass_cross_group_alignment_score",
        "min_watch_cross_group_alignment_score",
        "min_pass_reuse_confidence_score",
        "min_watch_reuse_confidence_score",
        "max_pass_decay_pressure_score",
        "max_watch_decay_pressure_score",
        "max_pass_handoff_gap_score",
        "max_watch_handoff_gap_score",
    ):
        _require_canonical_decimal(name, getattr(config, name), _require_ratio_decimal)
    _require_floor_pair(
        "min_pass_memory_health_score",
        config.min_pass_memory_health_score,
        "min_watch_memory_health_score",
        config.min_watch_memory_health_score,
    )
    _require_floor_pair(
        "min_pass_memory_retention_score",
        config.min_pass_memory_retention_score,
        "min_watch_memory_retention_score",
        config.min_watch_memory_retention_score,
    )
    _require_floor_pair(
        "min_pass_cross_group_alignment_score",
        config.min_pass_cross_group_alignment_score,
        "min_watch_cross_group_alignment_score",
        config.min_watch_cross_group_alignment_score,
    )
    _require_floor_pair(
        "min_pass_reuse_confidence_score",
        config.min_pass_reuse_confidence_score,
        "min_watch_reuse_confidence_score",
        config.min_watch_reuse_confidence_score,
    )
    _require_ceiling_pair(
        "max_pass_decay_pressure_score",
        config.max_pass_decay_pressure_score,
        "max_watch_decay_pressure_score",
        config.max_watch_decay_pressure_score,
    )
    _require_ceiling_pair(
        "max_pass_handoff_gap_score",
        config.max_pass_handoff_gap_score,
        "max_watch_handoff_gap_score",
        config.max_watch_handoff_gap_score,
    )
    if config.fresh_memory_age_seconds > config.stale_memory_age_seconds:
        raise ValueError("fresh_memory_age_seconds must not exceed stale_memory_age_seconds")
    _require_hard_flags("config", config)


def _revalidate_snapshot_for_build(
    snapshot: ResearchStrategyCrossTeamMemoryDecayRouterSnapshot,
) -> None:
    _require_exact_type(
        snapshot,
        ResearchStrategyCrossTeamMemoryDecayRouterSnapshot,
        "snapshot",
    )
    raw_baseline_memory_score = snapshot.baseline_memory_score
    raw_current_memory_score = snapshot.current_memory_score
    for name in ("route_ref", "lead_group_ref", "peer_group_ref"):
        _require_private_ref(name, getattr(snapshot, name))
    for name in ("observed_at", "last_memory_refresh_at"):
        _require_canonical_utc_datetime(name, getattr(snapshot, name))
    _require_canonical_decimal(
        "baseline_memory_score",
        raw_baseline_memory_score,
        _require_positive_ratio_decimal,
    )
    _require_canonical_decimal(
        "current_memory_score",
        raw_current_memory_score,
        _require_ratio_decimal,
    )
    if raw_current_memory_score > raw_baseline_memory_score:
        raise ValueError("current_memory_score must not exceed baseline_memory_score")
    if snapshot.current_memory_score > snapshot.baseline_memory_score:
        raise ValueError("current_memory_score must not exceed baseline_memory_score")
    for name in (
        "cross_group_alignment_score",
        "reuse_confidence_score",
        "handoff_gap_score",
    ):
        _require_canonical_decimal(name, getattr(snapshot, name), _require_ratio_decimal)
    reason_codes = _require_reason_codes(
        "reason_codes",
        snapshot.reason_codes,
        UPSTREAM_REASON_CODES,
        require_nonempty=True,
    )
    if reason_codes != _canonical_reason_codes(reason_codes, UPSTREAM_REASON_CODES):
        raise ValueError("reason_codes must be canonical")
    _require_hard_flags("snapshot", snapshot)


def _require_rows(value: object) -> tuple[ResearchStrategyCrossTeamMemoryDecayRouterRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for item in value:
        if type(item) is not ResearchStrategyCrossTeamMemoryDecayRouterRow:
            raise ValueError("rows must contain ResearchStrategyCrossTeamMemoryDecayRouterRow")
        _require_hard_flags("row", item)
    return value


def _require_reason_counts(
    value: object,
) -> tuple[ResearchStrategyCrossTeamMemoryDecayRouterReasonCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_counts must be a tuple")
    for item in value:
        if type(item) is not ResearchStrategyCrossTeamMemoryDecayRouterReasonCount:
            raise ValueError(
                "reason_counts must contain ResearchStrategyCrossTeamMemoryDecayRouterReasonCount",
            )
        _require_hard_flags("reason_count", item)
    return value


def _validate_report(report: ResearchStrategyCrossTeamMemoryDecayRouterReport) -> None:
    rows = report.rows
    row_count = _count_decimal(len(rows))
    for index, row in enumerate(rows, start=1):
        _validate_row_source_derivations(row)
        _validate_row_reason_status(row)
        if row.aggregate_row_number != _count_decimal(index):
            raise ValueError("rows must use sequential aggregate_row_number values")
        if row.observed_at > report.generated_at:
            raise ValueError("row observed_at must not be after generated_at")
        if row.last_memory_refresh_at > report.generated_at:
            raise ValueError("row last_memory_refresh_at must not be after generated_at")
        if row.memory_age_seconds != _seconds_between(
            row.last_memory_refresh_at,
            report.generated_at,
        ):
            raise ValueError("row memory_age_seconds must match generated_at")
        if row.memory_decay_ratio != _subtract_decimal(
            ONE,
            row.memory_retention_score,
        ):
            raise ValueError("row memory_decay_ratio must match memory_retention_score")
        if row.memory_age_pressure_score != _memory_age_pressure_score(
            row.memory_age_seconds,
            report.config,
        ):
            raise ValueError("row memory_age_pressure_score must match memory_age_seconds")
        if row.decay_pressure_score != _decay_pressure_score(
            memory_decay_ratio=row.memory_decay_ratio,
            memory_age_pressure_score=row.memory_age_pressure_score,
            handoff_gap_score=row.handoff_gap_score,
        ):
            raise ValueError("row decay_pressure_score must match row inputs")
        if row.memory_health_score != _memory_health_score(
            memory_retention_score=row.memory_retention_score,
            cross_group_alignment_score=row.cross_group_alignment_score,
            reuse_confidence_score=row.reuse_confidence_score,
            memory_age_pressure_score=row.memory_age_pressure_score,
            handoff_gap_score=row.handoff_gap_score,
        ):
            raise ValueError("row memory_health_score must match row inputs")
        expected_status = _row_status(
            memory_health_score=row.memory_health_score,
            memory_retention_score=row.memory_retention_score,
            memory_age_seconds=row.memory_age_seconds,
            memory_decay_ratio=row.memory_decay_ratio,
            decay_pressure_score=row.decay_pressure_score,
            cross_group_alignment_score=row.cross_group_alignment_score,
            reuse_confidence_score=row.reuse_confidence_score,
            handoff_gap_score=row.handoff_gap_score,
            config=report.config,
        )
        if row.status != expected_status:
            raise ValueError("row status must match row policy")
        upstream_reason_codes = tuple(
            reason for reason in row.reason_codes if reason in UPSTREAM_REASON_CODES
        )
        expected_reason_codes = _row_reason_codes_from_values(
            status=expected_status,
            upstream_reason_codes=upstream_reason_codes,
            memory_health_score=row.memory_health_score,
            memory_retention_score=row.memory_retention_score,
            memory_age_seconds=row.memory_age_seconds,
            memory_decay_ratio=row.memory_decay_ratio,
            decay_pressure_score=row.decay_pressure_score,
            cross_group_alignment_score=row.cross_group_alignment_score,
            reuse_confidence_score=row.reuse_confidence_score,
            handoff_gap_score=row.handoff_gap_score,
            config=report.config,
        )
        if row.reason_codes != expected_reason_codes:
            raise ValueError("row reason_codes must match row policy")
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use canonical report ordering")
    if report.snapshot_count != row_count:
        raise ValueError("snapshot_count must match row count")
    if report.route_count != _count_decimal(len({row.route_digest for row in rows})):
        raise ValueError("route_count must match unique routed row count")
    if report.pass_count != _status_count(rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match row severities")
    if report.average_memory_health_score != _average_decimal(
        tuple(row.memory_health_score for row in rows),
    ):
        raise ValueError("average_memory_health_score must match rows")
    if report.lowest_memory_health_score != _min_decimal(
        tuple(row.memory_health_score for row in rows),
    ):
        raise ValueError("lowest_memory_health_score must match rows")
    if report.highest_memory_decay_ratio != _max_decimal(
        tuple(row.memory_decay_ratio for row in rows),
    ):
        raise ValueError("highest_memory_decay_ratio must match rows")
    if report.highest_memory_age_seconds != _max_decimal(
        tuple(row.memory_age_seconds for row in rows),
    ):
        raise ValueError("highest_memory_age_seconds must match rows")
    if report.highest_decay_pressure_score != _max_decimal(
        tuple(row.decay_pressure_score for row in rows),
    ):
        raise ValueError("highest_decay_pressure_score must match rows")
    if report.lowest_cross_group_alignment_score != _min_decimal(
        tuple(row.cross_group_alignment_score for row in rows),
    ):
        raise ValueError("lowest_cross_group_alignment_score must match rows")
    if report.lowest_reuse_confidence_score != _min_decimal(
        tuple(row.reuse_confidence_score for row in rows),
    ):
        raise ValueError("lowest_reuse_confidence_score must match rows")
    if report.highest_handoff_gap_score != _max_decimal(
        tuple(row.handoff_gap_score for row in rows),
    ):
        raise ValueError("highest_handoff_gap_score must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_counts != _reason_counts(rows):
        raise ValueError("reason_counts must match rows")


def _validate_row_reason_status(
    row: ResearchStrategyCrossTeamMemoryDecayRouterRow,
) -> None:
    has_block = any(reason.endswith("_block") for reason in row.reason_codes)
    has_watch = any(reason.endswith("_watch") for reason in row.reason_codes)
    expected_status = (
        STATUS_BLOCK
        if has_block
        else STATUS_WATCH
        if has_watch
        else STATUS_PASS
    )
    if row.status != expected_status:
        raise ValueError("status must match reason_codes")
    if row.status == STATUS_PASS:
        if row.reason_codes[0] != REASON_ROW_PASS:
            raise ValueError("reason_codes must match status")
    elif REASON_ROW_PASS in row.reason_codes:
        raise ValueError("reason_codes must match status")


def _validate_row_source_derivations(
    row: ResearchStrategyCrossTeamMemoryDecayRouterRow,
) -> None:
    expected_retention = _divide_decimal(
        row.current_memory_score,
        row.baseline_memory_score,
    )
    if row.memory_retention_score != expected_retention:
        raise ValueError(
            "memory_retention_score must match baseline_memory_score "
            "and current_memory_score",
        )
    if row.memory_decay_ratio != _subtract_decimal(
        ONE,
        row.memory_retention_score,
    ):
        raise ValueError("memory_decay_ratio must match memory_retention_score")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_private_ref(name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    if len(value) > 2048:
        raise ValueError(f"{name} is too long")
    return value


def _require_public_id(name: str, value: object) -> str:
    if type(value) is not str or not PUBLIC_ID_RE.fullmatch(value):
        raise ValueError(f"{name} must be a public id")
    _reject_unsafe_public_text(name, value)
    return value


def _require_status(name: str, value: object) -> str:
    if type(value) is not str or value not in STATUS_VALUES:
        raise ValueError(f"{name} must be one of pass/watch/block")
    return value


def _require_reason_code(
    name: str,
    value: object,
    allowed_codes: Iterable[str],
) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{name} must be a non-empty reason code")
    _reject_unsafe_public_text(name, value)
    if value not in frozenset(allowed_codes):
        raise ValueError(f"{name} is not supported")
    return value


def _require_reason_codes(
    name: str,
    value: object,
    allowed_codes: Iterable[str],
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be a tuple of reason codes")
    codes = value
    if require_nonempty and not codes:
        raise ValueError(f"{name} must not be empty")
    allowed = frozenset(allowed_codes)
    for code in codes:
        _require_reason_code(name, code, allowed)
    if len(codes) != len(frozenset(codes)):
        raise ValueError(f"{name} must not contain duplicates")
    return codes


def _unique_reason_codes(codes: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for code in codes:
        if code not in seen:
            seen.add(code)
            ordered.append(code)
    return tuple(ordered)


def _canonical_reason_codes(
    codes: tuple[str, ...],
    priority: tuple[str, ...],
) -> tuple[str, ...]:
    present = frozenset(codes)
    ordered = tuple(code for code in priority if code in present)
    if len(ordered) != len(codes):
        raise ValueError("reason_codes must use canonical priority")
    return ordered


def _require_private_digest(name: str, value: object) -> str:
    if type(value) is not str or not PRIVATE_DIGEST_RE.fullmatch(value):
        raise ValueError(f"{name} must be a private sha256 digest")
    return value


def _require_digest(name: str, value: object) -> str:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{name} must be a SHA-256 hex digest")
    return value


def _require_raw_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be a finite Decimal")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{name} must not use signed zero")
    return value


def _require_canonical_decimal(
    name: str,
    value: object,
    validator: Any,
) -> Decimal:
    normalized = validator(name, value)
    if type(value) is not Decimal or value.as_tuple() != normalized.as_tuple():
        raise ValueError(f"{name} must use canonical Decimal precision")
    return normalized


def _require_decimal(name: str, value: object) -> Decimal:
    return _quantize_decimal(_require_raw_decimal(name, value))


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    raw_value = _require_raw_decimal(name, value)
    if raw_value < ZERO or raw_value > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return _quantize_decimal(raw_value)


def _require_positive_ratio_decimal(name: str, value: object) -> Decimal:
    raw_value = _require_raw_decimal(name, value)
    if raw_value <= ZERO or raw_value > ONE:
        raise ValueError(f"{name} must be greater than 0 and at most 1")
    decimal_value = _quantize_decimal(raw_value)
    if decimal_value <= ZERO:
        raise ValueError(f"{name} must be greater than 0")
    return decimal_value


def _require_nonnegative_decimal(name: str, value: object) -> Decimal:
    raw_value = _require_raw_decimal(name, value)
    if raw_value < ZERO:
        raise ValueError(f"{name} must be non-negative")
    return _quantize_decimal(raw_value)


def _require_positive_decimal(name: str, value: object) -> Decimal:
    raw_value = _require_raw_decimal(name, value)
    if raw_value <= ZERO:
        raise ValueError(f"{name} must be positive")
    decimal_value = _quantize_decimal(raw_value)
    if decimal_value <= ZERO:
        raise ValueError(f"{name} must be positive after quantization")
    return decimal_value


def _require_count_decimal(name: str, value: object) -> Decimal:
    raw_value = _require_raw_decimal(name, value)
    if raw_value < ZERO:
        raise ValueError(f"{name} must be non-negative")
    with localcontext(DECIMAL_CONTEXT):
        if raw_value != raw_value.to_integral_value():
            raise ValueError(f"{name} must be an integral Decimal count")
    decimal_value = _quantize_decimal(raw_value)
    if decimal_value != raw_value:
        raise ValueError(f"{name} must be an integral Decimal count")
    return decimal_value


def _require_floor_pair(
    pass_name: str,
    pass_value: Decimal,
    watch_name: str,
    watch_value: Decimal,
) -> None:
    if pass_value < watch_value:
        raise ValueError(f"{pass_name} must be greater than or equal to {watch_name}")


def _require_ceiling_pair(
    pass_name: str,
    pass_value: Decimal,
    watch_name: str,
    watch_value: Decimal,
) -> None:
    if pass_value > watch_value:
        raise ValueError(f"{pass_name} must be less than or equal to {watch_name}")


def _require_hard_flags(label: str, value: object) -> None:
    for name in FLAG_FIELDS:
        item = getattr(value, name, None)
        if type(item) is not bool or item is not True:
            raise ValueError(f"{label}.{name} must be True")


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_utc_datetime(name: str, value: object) -> datetime:
    normalized = _as_utc(name, value)
    if value.tzinfo is not UTC:
        raise ValueError(f"{name} must be a canonical UTC datetime")
    return normalized


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(
            (Decimal(delta.days) * SECONDS_PER_DAY)
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND),
        )


def _divide_decimal(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        raise ValueError("denominator must not be zero")
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(numerator / denominator)


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(left - right)


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return sum(values, ZERO)


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _divide_decimal(_sum_decimals(values), _count_decimal(len(values)))


def _min_decimal(values: tuple[Decimal, ...]) -> Decimal:
    return min(values) if values else ZERO


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    return max(values) if values else ZERO


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _quantize_decimal(value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError("value must be a Decimal")
    if not value.is_finite():
        raise ValueError("Decimal must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError("Decimal must not use signed zero")
    with localcontext(DECIMAL_CONTEXT):
        try:
            quantized = value.quantize(QUANT)
        except InvalidOperation as exc:
            raise ValueError("Decimal must fit canonical precision") from exc
    if quantized.is_zero() and quantized.is_signed():
        raise ValueError("Decimal must not quantize to signed zero")
    if quantized.is_zero():
        return ZERO
    return quantized


def _digest_ref(value: str) -> str:
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()


def _row_payload(
    row: ResearchStrategyCrossTeamMemoryDecayRouterRow,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    return _dataclass_payload(row, include_digest=include_digest)


def _report_payload(
    report: ResearchStrategyCrossTeamMemoryDecayRouterReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    return _dataclass_payload(report, include_digest=include_digest)


def _dataclass_payload(value: object, *, include_digest: bool) -> dict[str, Any]:
    if not is_dataclass(value):
        raise ValueError("payload value must be a dataclass")
    payload: dict[str, Any] = {}
    for field in fields(value):
        if field.name == DIGEST_FIELD and not include_digest:
            continue
        payload[field.name] = _to_payload(getattr(value, field.name))
    return payload


def _to_payload(value: object) -> Any:
    if isinstance(value, Decimal):
        if (
            type(value) is not Decimal
            or not value.is_finite()
            or (value.is_zero() and value.is_signed())
        ):
            raise ValueError("payload Decimal values must be finite Decimal instances")
        return format(value, "f")
    if isinstance(value, datetime):
        return _as_utc("payload datetime", value).isoformat()
    if is_dataclass(value):
        return _dataclass_payload(value, include_digest=True)
    if isinstance(value, tuple):
        return [_to_payload(item) for item in value]
    if isinstance(value, list):
        return [_to_payload(item) for item in value]
    if isinstance(value, dict):
        if any(type(key) is not str for key in value):
            raise ValueError("payload object keys must be strings")
        ready: dict[str, Any] = {}
        for key in sorted(value):
            ready[key] = _to_payload(value[key])
        return ready
    if value is None or type(value) in (str, bool):
        return value
    if type(value) in (int, float):
        raise ValueError("payload numerics must use Decimal")
    raise ValueError("value is not JSON serializable")


def _payload_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _validate_payload_dict(payload: dict[str, Any]) -> dict[str, Any]:
    validate_research_strategy_cross_team_memory_decay_router_report_public_payload(
        payload,
    )
    return payload


def _report_from_public_payload(
    payload: dict[str, Any],
) -> ResearchStrategyCrossTeamMemoryDecayRouterReport:
    config = _config_from_public_payload(payload["config"])
    rows_value = _require_public_list("payload.rows", payload["rows"])
    rows = tuple(
        _row_from_public_payload(item, index=index)
        for index, item in enumerate(rows_value)
    )
    reason_counts_value = _require_public_list(
        "payload.reason_counts",
        payload["reason_counts"],
    )
    reason_counts = tuple(
        _reason_count_from_public_payload(item, index=index)
        for index, item in enumerate(reason_counts_value)
    )
    return ResearchStrategyCrossTeamMemoryDecayRouterReport(
        generated_at=_require_public_datetime_string(
            "payload.generated_at",
            payload["generated_at"],
        ),
        config_version=_require_public_string(
            "payload.config_version",
            payload["config_version"],
        ),
        config=config,
        status=_require_public_string("payload.status", payload["status"]),
        snapshot_count=_require_public_decimal_string(
            "payload.snapshot_count",
            payload["snapshot_count"],
        ),
        route_count=_require_public_decimal_string(
            "payload.route_count",
            payload["route_count"],
        ),
        pass_count=_require_public_decimal_string(
            "payload.pass_count",
            payload["pass_count"],
        ),
        watch_count=_require_public_decimal_string(
            "payload.watch_count",
            payload["watch_count"],
        ),
        block_count=_require_public_decimal_string(
            "payload.block_count",
            payload["block_count"],
        ),
        average_memory_health_score=_require_public_decimal_string(
            "payload.average_memory_health_score",
            payload["average_memory_health_score"],
        ),
        lowest_memory_health_score=_require_public_decimal_string(
            "payload.lowest_memory_health_score",
            payload["lowest_memory_health_score"],
        ),
        highest_memory_decay_ratio=_require_public_decimal_string(
            "payload.highest_memory_decay_ratio",
            payload["highest_memory_decay_ratio"],
        ),
        highest_memory_age_seconds=_require_public_decimal_string(
            "payload.highest_memory_age_seconds",
            payload["highest_memory_age_seconds"],
        ),
        highest_decay_pressure_score=_require_public_decimal_string(
            "payload.highest_decay_pressure_score",
            payload["highest_decay_pressure_score"],
        ),
        lowest_cross_group_alignment_score=_require_public_decimal_string(
            "payload.lowest_cross_group_alignment_score",
            payload["lowest_cross_group_alignment_score"],
        ),
        lowest_reuse_confidence_score=_require_public_decimal_string(
            "payload.lowest_reuse_confidence_score",
            payload["lowest_reuse_confidence_score"],
        ),
        highest_handoff_gap_score=_require_public_decimal_string(
            "payload.highest_handoff_gap_score",
            payload["highest_handoff_gap_score"],
        ),
        reason_codes=_require_public_string_list(
            "payload.reason_codes",
            payload["reason_codes"],
        ),
        reason_counts=reason_counts,
        rows=rows,
        paper_only=_require_public_true(
            "payload.paper_only",
            payload["paper_only"],
        ),
        report_only=_require_public_true(
            "payload.report_only",
            payload["report_only"],
        ),
        readonly=_require_public_true("payload.readonly", payload["readonly"]),
    )


def _config_from_public_payload(
    value: object,
) -> ResearchStrategyCrossTeamMemoryDecayRouterConfig:
    label = "payload.config"
    config = _require_public_object(label, value)
    _require_public_schema_fields(
        label,
        config,
        ResearchStrategyCrossTeamMemoryDecayRouterConfig,
    )
    return ResearchStrategyCrossTeamMemoryDecayRouterConfig(
        config_version=_require_public_string(
            f"{label}.config_version",
            config["config_version"],
        ),
        fresh_memory_age_seconds=_require_public_decimal_string(
            f"{label}.fresh_memory_age_seconds",
            config["fresh_memory_age_seconds"],
        ),
        stale_memory_age_seconds=_require_public_decimal_string(
            f"{label}.stale_memory_age_seconds",
            config["stale_memory_age_seconds"],
        ),
        min_pass_memory_health_score=_require_public_decimal_string(
            f"{label}.min_pass_memory_health_score",
            config["min_pass_memory_health_score"],
        ),
        min_watch_memory_health_score=_require_public_decimal_string(
            f"{label}.min_watch_memory_health_score",
            config["min_watch_memory_health_score"],
        ),
        min_pass_memory_retention_score=_require_public_decimal_string(
            f"{label}.min_pass_memory_retention_score",
            config["min_pass_memory_retention_score"],
        ),
        min_watch_memory_retention_score=_require_public_decimal_string(
            f"{label}.min_watch_memory_retention_score",
            config["min_watch_memory_retention_score"],
        ),
        min_pass_cross_group_alignment_score=_require_public_decimal_string(
            f"{label}.min_pass_cross_group_alignment_score",
            config["min_pass_cross_group_alignment_score"],
        ),
        min_watch_cross_group_alignment_score=_require_public_decimal_string(
            f"{label}.min_watch_cross_group_alignment_score",
            config["min_watch_cross_group_alignment_score"],
        ),
        min_pass_reuse_confidence_score=_require_public_decimal_string(
            f"{label}.min_pass_reuse_confidence_score",
            config["min_pass_reuse_confidence_score"],
        ),
        min_watch_reuse_confidence_score=_require_public_decimal_string(
            f"{label}.min_watch_reuse_confidence_score",
            config["min_watch_reuse_confidence_score"],
        ),
        max_pass_decay_pressure_score=_require_public_decimal_string(
            f"{label}.max_pass_decay_pressure_score",
            config["max_pass_decay_pressure_score"],
        ),
        max_watch_decay_pressure_score=_require_public_decimal_string(
            f"{label}.max_watch_decay_pressure_score",
            config["max_watch_decay_pressure_score"],
        ),
        max_pass_handoff_gap_score=_require_public_decimal_string(
            f"{label}.max_pass_handoff_gap_score",
            config["max_pass_handoff_gap_score"],
        ),
        max_watch_handoff_gap_score=_require_public_decimal_string(
            f"{label}.max_watch_handoff_gap_score",
            config["max_watch_handoff_gap_score"],
        ),
        paper_only=_require_public_true(
            f"{label}.paper_only",
            config["paper_only"],
        ),
        report_only=_require_public_true(
            f"{label}.report_only",
            config["report_only"],
        ),
        readonly=_require_public_true(
            f"{label}.readonly",
            config["readonly"],
        ),
    )


def _row_from_public_payload(
    value: object,
    *,
    index: int,
) -> ResearchStrategyCrossTeamMemoryDecayRouterRow:
    label = f"payload.rows[{index}]"
    row = _require_public_object(label, value)
    _require_public_schema_fields(
        label,
        row,
        ResearchStrategyCrossTeamMemoryDecayRouterRow,
    )
    return ResearchStrategyCrossTeamMemoryDecayRouterRow(
        aggregate_row_number=_require_public_decimal_string(
            f"{label}.aggregate_row_number",
            row["aggregate_row_number"],
        ),
        route_digest=_require_public_string(
            f"{label}.route_digest",
            row["route_digest"],
        ),
        lead_group_digest=_require_public_string(
            f"{label}.lead_group_digest",
            row["lead_group_digest"],
        ),
        peer_group_digest=_require_public_string(
            f"{label}.peer_group_digest",
            row["peer_group_digest"],
        ),
        status=_require_public_string(f"{label}.status", row["status"]),
        baseline_memory_score=_require_public_decimal_string(
            f"{label}.baseline_memory_score",
            row["baseline_memory_score"],
        ),
        current_memory_score=_require_public_decimal_string(
            f"{label}.current_memory_score",
            row["current_memory_score"],
        ),
        memory_retention_score=_require_public_decimal_string(
            f"{label}.memory_retention_score",
            row["memory_retention_score"],
        ),
        memory_decay_ratio=_require_public_decimal_string(
            f"{label}.memory_decay_ratio",
            row["memory_decay_ratio"],
        ),
        memory_age_seconds=_require_public_decimal_string(
            f"{label}.memory_age_seconds",
            row["memory_age_seconds"],
        ),
        memory_age_pressure_score=_require_public_decimal_string(
            f"{label}.memory_age_pressure_score",
            row["memory_age_pressure_score"],
        ),
        decay_pressure_score=_require_public_decimal_string(
            f"{label}.decay_pressure_score",
            row["decay_pressure_score"],
        ),
        cross_group_alignment_score=_require_public_decimal_string(
            f"{label}.cross_group_alignment_score",
            row["cross_group_alignment_score"],
        ),
        reuse_confidence_score=_require_public_decimal_string(
            f"{label}.reuse_confidence_score",
            row["reuse_confidence_score"],
        ),
        handoff_gap_score=_require_public_decimal_string(
            f"{label}.handoff_gap_score",
            row["handoff_gap_score"],
        ),
        memory_health_score=_require_public_decimal_string(
            f"{label}.memory_health_score",
            row["memory_health_score"],
        ),
        observed_at=_require_public_datetime_string(
            f"{label}.observed_at",
            row["observed_at"],
        ),
        last_memory_refresh_at=_require_public_datetime_string(
            f"{label}.last_memory_refresh_at",
            row["last_memory_refresh_at"],
        ),
        reason_codes=_require_public_string_list(
            f"{label}.reason_codes",
            row["reason_codes"],
        ),
        derived_validation_digest=_require_public_string(
            f"{label}.{DIGEST_FIELD}",
            row[DIGEST_FIELD],
        ),
        paper_only=_require_public_true(
            f"{label}.paper_only",
            row["paper_only"],
        ),
        report_only=_require_public_true(
            f"{label}.report_only",
            row["report_only"],
        ),
        readonly=_require_public_true(f"{label}.readonly", row["readonly"]),
    )


def _reason_count_from_public_payload(
    value: object,
    *,
    index: int,
) -> ResearchStrategyCrossTeamMemoryDecayRouterReasonCount:
    label = f"payload.reason_counts[{index}]"
    reason_count = _require_public_object(label, value)
    _require_public_schema_fields(
        label,
        reason_count,
        ResearchStrategyCrossTeamMemoryDecayRouterReasonCount,
    )
    return ResearchStrategyCrossTeamMemoryDecayRouterReasonCount(
        reason_code=_require_public_string(
            f"{label}.reason_code",
            reason_count["reason_code"],
        ),
        count=_require_public_decimal_string(
            f"{label}.count",
            reason_count["count"],
        ),
        row_ratio=_require_public_decimal_string(
            f"{label}.row_ratio",
            reason_count["row_ratio"],
        ),
        paper_only=_require_public_true(
            f"{label}.paper_only",
            reason_count["paper_only"],
        ),
        report_only=_require_public_true(
            f"{label}.report_only",
            reason_count["report_only"],
        ),
        readonly=_require_public_true(
            f"{label}.readonly",
            reason_count["readonly"],
        ),
    )


def _require_public_schema_fields(
    label: str,
    payload: dict[str, Any],
    expected_type: type[object],
) -> None:
    expected_fields = tuple(field.name for field in fields(expected_type))
    if tuple(payload) != expected_fields:
        raise ValueError(
            f"{label} fields must exactly match the public schema "
            "in canonical field order",
        )


def _require_public_object(label: str, value: object) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError(f"{label} must be a JSON object")
    return value


def _require_public_list(label: str, value: object) -> list[Any]:
    if type(value) is not list:
        raise ValueError(f"{label} must be a list")
    return value


def _require_public_string(label: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{label} must be a string")
    return value


def _require_public_string_list(label: str, value: object) -> tuple[str, ...]:
    items = _require_public_list(label, value)
    for item in items:
        if type(item) is not str:
            raise ValueError(f"{label} must contain strings")
    return tuple(items)


def _require_public_true(label: str, value: object) -> bool:
    if type(value) is not bool or value is not True:
        raise ValueError(f"{label} must be True")
    return True


def _require_public_decimal_string(label: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{label} must be a Decimal string")
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{label} must be a Decimal string") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{label} must be a finite Decimal string")
    if decimal_value.is_zero() and decimal_value.is_signed():
        raise ValueError(
            f"{label} must be a canonical Decimal string without signed zero",
        )
    try:
        normalized = _quantize_decimal(decimal_value)
        canonical = format(normalized, "f")
    except ValueError as exc:
        raise ValueError(f"{label} must be a valid Decimal string") from exc
    if value != canonical:
        raise ValueError(f"{label} must be a canonical Decimal string")
    return normalized


def _require_public_datetime_string(label: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{label} must be a datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{label} must be an ISO datetime string") from exc
    canonical = _as_utc(label, parsed)
    if value != canonical.isoformat():
        raise ValueError(f"{label} must be a canonical UTC datetime string")
    return canonical


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = _require_digest(DIGEST_FIELD, payload.get(DIGEST_FIELD))
    unsigned = dict(payload)
    unsigned.pop(DIGEST_FIELD, None)
    if _payload_digest(unsigned) != digest:
        raise ValueError("derived_validation_digest must match report payload")


def _revalidate_report_for_payload(
    report: ResearchStrategyCrossTeamMemoryDecayRouterReport,
) -> None:
    _require_exact_type(
        report,
        ResearchStrategyCrossTeamMemoryDecayRouterReport,
        "report",
    )
    _require_hard_flags("report", report)
    _require_exact_type(
        report.config,
        ResearchStrategyCrossTeamMemoryDecayRouterConfig,
        "config",
    )
    _revalidate_config_for_build(report.config)
    _require_rows(report.rows)
    _require_reason_counts(report.reason_counts)
    for row in report.rows:
        _revalidate_row_for_payload(row)
    _validate_report(report)
    expected_report_digest = _payload_digest(
        _report_payload(report, include_digest=False),
    )
    if report.derived_validation_digest != expected_report_digest:
        raise ValueError("derived_validation_digest must match report payload")


def _revalidate_row_for_payload(
    row: ResearchStrategyCrossTeamMemoryDecayRouterRow,
) -> None:
    _require_exact_type(
        row,
        ResearchStrategyCrossTeamMemoryDecayRouterRow,
        "row",
    )
    _require_hard_flags("row", row)
    _require_canonical_utc_datetime("observed_at", row.observed_at)
    _require_canonical_utc_datetime(
        "last_memory_refresh_at",
        row.last_memory_refresh_at,
    )
    replace(row)
    _validate_row_source_derivations(row)
    _validate_row_reason_status(row)
    expected_digest = _payload_digest(_row_payload(row, include_digest=False))
    if row.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match row payload")


def _validated_row_public_payload(
    row: ResearchStrategyCrossTeamMemoryDecayRouterRow,
) -> dict[str, Any]:
    _revalidate_row_for_payload(row)
    payload = _row_payload(row, include_digest=True)
    _reject_raw_numeric_payload_values(payload)
    _reject_unsafe_public_payload("row", payload)
    canonical_payload = _row_payload(
        _row_from_public_payload(payload, index=0),
        include_digest=True,
    )
    if payload != canonical_payload:
        raise ValueError("row public payload must use canonical schema values")
    return payload


def _validated_report_public_payload(
    report: ResearchStrategyCrossTeamMemoryDecayRouterReport,
) -> dict[str, Any]:
    _revalidate_report_for_payload(report)
    payload = _report_payload(report, include_digest=True)
    _validate_report_public_payload_dict(payload)
    return payload


def _reject_raw_numeric_payload_values(value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise ValueError("public payload must encode numerics as strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_raw_numeric_payload_values(item)
    elif isinstance(value, list):
        for item in value:
            _reject_raw_numeric_payload_values(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_public_text(label, str(key))
            _reject_unsafe_public_payload(label, item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
    elif isinstance(value, str):
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{label} contains unsafe public payload text")
