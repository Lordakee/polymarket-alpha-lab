"""Report-only domain-team memory alpha decay scorecard."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_STRATEGY_DOMAIN_TEAM_MEMORY_ALPHA_DECAY_REPORT_CONFIG_VERSION = (
    "research-strategy-domain-team-memory-alpha-decay-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
RESEARCH_STRATEGY_DOMAIN_TEAM_MEMORY_ALPHA_DECAY_STATUSES = (
    STATUS_PASS,
    STATUS_WATCH,
    STATUS_BLOCK,
)
STATUS_SORT_SEQUENCE = (STATUS_BLOCK, STATUS_WATCH, STATUS_PASS)

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_UP)

NO_SNAPSHOTS_REASON = "memory_alpha_decay_no_snapshots"
MEMORY_SNAPSHOT_READY_REASON = "memory_snapshot_ready"
CALIBRATION_MEMORY_OBSERVED_REASON = "calibration_memory_observed"
EVIDENCE_MEMORY_OBSERVED_REASON = "evidence_memory_observed"
ALPHA_DECAY_BLOCK_REASON = "alpha_decay_block"
ALPHA_DECAY_WATCH_REASON = "alpha_decay_watch"
ALPHA_SIGNAL_AGE_BLOCK_REASON = "alpha_signal_age_block"
ALPHA_SIGNAL_AGE_WATCH_REASON = "alpha_signal_age_watch"
MEMORY_REUSE_BLOCK_REASON = "memory_reuse_block"
MEMORY_REUSE_WATCH_REASON = "memory_reuse_watch"
CALIBRATION_MEMORY_BLOCK_REASON = "calibration_memory_block"
CALIBRATION_MEMORY_WATCH_REASON = "calibration_memory_watch"
EVIDENCE_MEMORY_BLOCK_REASON = "evidence_memory_block"
EVIDENCE_MEMORY_WATCH_REASON = "evidence_memory_watch"
STALE_MEMORY_PRESSURE_BLOCK_REASON = "stale_memory_pressure_block"
STALE_MEMORY_PRESSURE_WATCH_REASON = "stale_memory_pressure_watch"
MEMORY_ALPHA_DECAY_SCORE_BLOCK_REASON = "memory_alpha_decay_score_block"
MEMORY_ALPHA_DECAY_SCORE_WATCH_REASON = "memory_alpha_decay_score_watch"
MEMORY_ALPHA_DECAY_PASS_REASON = "memory_alpha_decay_pass"

ROW_REASON_CODE_SEQUENCE = (
    MEMORY_SNAPSHOT_READY_REASON,
    CALIBRATION_MEMORY_OBSERVED_REASON,
    EVIDENCE_MEMORY_OBSERVED_REASON,
    ALPHA_DECAY_BLOCK_REASON,
    ALPHA_DECAY_WATCH_REASON,
    ALPHA_SIGNAL_AGE_BLOCK_REASON,
    ALPHA_SIGNAL_AGE_WATCH_REASON,
    MEMORY_REUSE_BLOCK_REASON,
    MEMORY_REUSE_WATCH_REASON,
    CALIBRATION_MEMORY_BLOCK_REASON,
    CALIBRATION_MEMORY_WATCH_REASON,
    EVIDENCE_MEMORY_BLOCK_REASON,
    EVIDENCE_MEMORY_WATCH_REASON,
    STALE_MEMORY_PRESSURE_BLOCK_REASON,
    STALE_MEMORY_PRESSURE_WATCH_REASON,
    MEMORY_ALPHA_DECAY_SCORE_BLOCK_REASON,
    MEMORY_ALPHA_DECAY_SCORE_WATCH_REASON,
    MEMORY_ALPHA_DECAY_PASS_REASON,
)
UPSTREAM_ROW_REASON_CODE_SEQUENCE = (
    MEMORY_SNAPSHOT_READY_REASON,
    CALIBRATION_MEMORY_OBSERVED_REASON,
    EVIDENCE_MEMORY_OBSERVED_REASON,
)
COUNT_REASON_CODE_SEQUENCE = (NO_SNAPSHOTS_REASON,) + ROW_REASON_CODE_SEQUENCE

REPORT_CLEAR_REASON = "memory_alpha_decay_report_clear"
REPORT_BLOCK_PRESENT_REASON = "memory_alpha_decay_block_present"
REPORT_WATCH_PRESENT_REASON = "memory_alpha_decay_watch_present"
REPORT_ALPHA_DECAY_GAP_REASON = "alpha_decay_gap_present"
REPORT_ALPHA_SIGNAL_AGE_GAP_REASON = "alpha_signal_age_gap_present"
REPORT_MEMORY_REUSE_GAP_REASON = "memory_reuse_gap_present"
REPORT_CALIBRATION_MEMORY_GAP_REASON = "calibration_memory_gap_present"
REPORT_EVIDENCE_MEMORY_GAP_REASON = "evidence_memory_gap_present"
REPORT_STALE_MEMORY_PRESSURE_REASON = "stale_memory_pressure_present"
REPORT_REASON_CODE_SEQUENCE = (
    NO_SNAPSHOTS_REASON,
    REPORT_BLOCK_PRESENT_REASON,
    REPORT_WATCH_PRESENT_REASON,
    REPORT_ALPHA_DECAY_GAP_REASON,
    REPORT_ALPHA_SIGNAL_AGE_GAP_REASON,
    REPORT_MEMORY_REUSE_GAP_REASON,
    REPORT_CALIBRATION_MEMORY_GAP_REASON,
    REPORT_EVIDENCE_MEMORY_GAP_REASON,
    REPORT_STALE_MEMORY_PRESSURE_REASON,
    REPORT_CLEAR_REASON,
)

CONFIG_DECIMAL_FIELD_NAMES = (
    "max_pass_alpha_signal_age_seconds",
    "max_watch_alpha_signal_age_seconds",
    "max_pass_alpha_decay_ratio",
    "max_watch_alpha_decay_ratio",
    "min_pass_memory_reuse_score",
    "min_watch_memory_reuse_score",
    "min_pass_calibration_memory_score",
    "min_watch_calibration_memory_score",
    "min_pass_evidence_memory_score",
    "min_watch_evidence_memory_score",
    "max_pass_stale_memory_pressure_score",
    "max_watch_stale_memory_pressure_score",
    "min_pass_memory_alpha_decay_score",
    "min_watch_memory_alpha_decay_score",
    "alpha_retention_weight",
    "memory_reuse_weight",
    "calibration_memory_weight",
    "evidence_memory_weight",
    "signal_freshness_weight",
    "stale_memory_relief_weight",
)

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
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "trading",
    "live",
    "database",
    "network",
    "recommend",
    "sizing",
    "secret",
    "credential",
    "private",
)

__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_DOMAIN_TEAM_MEMORY_ALPHA_DECAY_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_DOMAIN_TEAM_MEMORY_ALPHA_DECAY_STATUSES",
    "ResearchStrategyDomainTeamMemoryAlphaDecayConfig",
    "ResearchStrategyDomainTeamMemoryAlphaDecayReasonCount",
    "ResearchStrategyDomainTeamMemoryAlphaDecayReport",
    "ResearchStrategyDomainTeamMemoryAlphaDecayRow",
    "ResearchStrategyDomainTeamMemoryAlphaDecaySnapshot",
    "build_research_strategy_domain_team_memory_alpha_decay_report",
    "research_strategy_domain_team_memory_alpha_decay_report_digest",
    "research_strategy_domain_team_memory_alpha_decay_report_payload",
)


@dataclass(frozen=True, slots=True)
class ResearchStrategyDomainTeamMemoryAlphaDecayConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_DOMAIN_TEAM_MEMORY_ALPHA_DECAY_REPORT_CONFIG_VERSION
    )
    max_pass_alpha_signal_age_seconds: Decimal = Decimal("604800.000000")
    max_watch_alpha_signal_age_seconds: Decimal = Decimal("2592000.000000")
    max_pass_alpha_decay_ratio: Decimal = Decimal("0.200000")
    max_watch_alpha_decay_ratio: Decimal = Decimal("0.450000")
    min_pass_memory_reuse_score: Decimal = Decimal("0.750000")
    min_watch_memory_reuse_score: Decimal = Decimal("0.500000")
    min_pass_calibration_memory_score: Decimal = Decimal("0.750000")
    min_watch_calibration_memory_score: Decimal = Decimal("0.500000")
    min_pass_evidence_memory_score: Decimal = Decimal("0.700000")
    min_watch_evidence_memory_score: Decimal = Decimal("0.450000")
    max_pass_stale_memory_pressure_score: Decimal = Decimal("0.200000")
    max_watch_stale_memory_pressure_score: Decimal = Decimal("0.450000")
    min_pass_memory_alpha_decay_score: Decimal = Decimal("0.750000")
    min_watch_memory_alpha_decay_score: Decimal = Decimal("0.500000")
    alpha_retention_weight: Decimal = Decimal("0.300000")
    memory_reuse_weight: Decimal = Decimal("0.200000")
    calibration_memory_weight: Decimal = Decimal("0.200000")
    evidence_memory_weight: Decimal = Decimal("0.150000")
    signal_freshness_weight: Decimal = Decimal("0.100000")
    stale_memory_relief_weight: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super(ResearchStrategyDomainTeamMemoryAlphaDecayConfig, cls).__init_subclass__(
            **kwargs,
        )
        if cls is not ResearchStrategyDomainTeamMemoryAlphaDecayConfig:
            raise TypeError(
                "ResearchStrategyDomainTeamMemoryAlphaDecayConfig rejects subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDomainTeamMemoryAlphaDecayConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_label("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_DOMAIN_TEAM_MEMORY_ALPHA_DECAY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match the supported config version")
        for name in (
            "max_pass_alpha_signal_age_seconds",
            "max_watch_alpha_signal_age_seconds",
        ):
            object.__setattr__(self, name, _require_positive_decimal(name, getattr(self, name)))
        for name in (
            "max_pass_alpha_decay_ratio",
            "max_watch_alpha_decay_ratio",
            "min_pass_memory_reuse_score",
            "min_watch_memory_reuse_score",
            "min_pass_calibration_memory_score",
            "min_watch_calibration_memory_score",
            "min_pass_evidence_memory_score",
            "min_watch_evidence_memory_score",
            "max_pass_stale_memory_pressure_score",
            "max_watch_stale_memory_pressure_score",
            "min_pass_memory_alpha_decay_score",
            "min_watch_memory_alpha_decay_score",
            "alpha_retention_weight",
            "memory_reuse_weight",
            "calibration_memory_weight",
            "evidence_memory_weight",
            "signal_freshness_weight",
            "stale_memory_relief_weight",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        if (
            self.max_pass_alpha_signal_age_seconds
            > self.max_watch_alpha_signal_age_seconds
        ):
            raise ValueError("max_pass_alpha_signal_age_seconds must not exceed watch")
        _require_ceiling_pair(
            "max_pass_alpha_decay_ratio",
            self.max_pass_alpha_decay_ratio,
            "max_watch_alpha_decay_ratio",
            self.max_watch_alpha_decay_ratio,
        )
        _require_floor_pair(
            "min_pass_memory_reuse_score",
            self.min_pass_memory_reuse_score,
            "min_watch_memory_reuse_score",
            self.min_watch_memory_reuse_score,
        )
        _require_floor_pair(
            "min_pass_calibration_memory_score",
            self.min_pass_calibration_memory_score,
            "min_watch_calibration_memory_score",
            self.min_watch_calibration_memory_score,
        )
        _require_floor_pair(
            "min_pass_evidence_memory_score",
            self.min_pass_evidence_memory_score,
            "min_watch_evidence_memory_score",
            self.min_watch_evidence_memory_score,
        )
        _require_ceiling_pair(
            "max_pass_stale_memory_pressure_score",
            self.max_pass_stale_memory_pressure_score,
            "max_watch_stale_memory_pressure_score",
            self.max_watch_stale_memory_pressure_score,
        )
        _require_floor_pair(
            "min_pass_memory_alpha_decay_score",
            self.min_pass_memory_alpha_decay_score,
            "min_watch_memory_alpha_decay_score",
            self.min_watch_memory_alpha_decay_score,
        )
        weight_total = _sum_decimal(
            (
                self.alpha_retention_weight,
                self.memory_reuse_weight,
                self.calibration_memory_weight,
                self.evidence_memory_weight,
                self.signal_freshness_weight,
                self.stale_memory_relief_weight,
            ),
        )
        if weight_total != ONE:
            raise ValueError("weights must sum to one")
        _require_hard_flags("config", self)


@dataclass(frozen=True, slots=True)
class ResearchStrategyDomainTeamMemoryAlphaDecaySnapshot:
    domain_ref: str
    team_ref: str
    observed_at: datetime
    last_alpha_signal_at: datetime
    baseline_alpha_score: Decimal
    current_alpha_score: Decimal
    memory_reuse_score: Decimal
    calibration_memory_score: Decimal
    evidence_memory_score: Decimal
    stale_memory_pressure_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super(ResearchStrategyDomainTeamMemoryAlphaDecaySnapshot, cls).__init_subclass__(
            **kwargs,
        )
        if cls is not ResearchStrategyDomainTeamMemoryAlphaDecaySnapshot:
            raise TypeError(
                "ResearchStrategyDomainTeamMemoryAlphaDecaySnapshot rejects subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDomainTeamMemoryAlphaDecaySnapshot, "snapshot")
        object.__setattr__(self, "domain_ref", _require_private_ref("domain_ref", self.domain_ref))
        object.__setattr__(self, "team_ref", _require_private_ref("team_ref", self.team_ref))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "last_alpha_signal_at",
            _as_utc("last_alpha_signal_at", self.last_alpha_signal_at),
        )
        for name in (
            "baseline_alpha_score",
            "current_alpha_score",
            "memory_reuse_score",
            "calibration_memory_score",
            "evidence_memory_score",
            "stale_memory_pressure_score",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, ROW_REASON_CODE_SEQUENCE, allow_empty=True),
        )
        _require_hard_flags("snapshot", self)


@dataclass(frozen=True, slots=True)
class ResearchStrategyDomainTeamMemoryAlphaDecayRow:
    rank: Decimal
    domain_ref_digest: str
    team_ref_digest: str
    observed_at: datetime
    alpha_signal_age_seconds: Decimal
    baseline_alpha_score: Decimal
    current_alpha_score: Decimal
    alpha_decay_ratio: Decimal
    alpha_retention_score: Decimal
    memory_reuse_score: Decimal
    calibration_memory_score: Decimal
    evidence_memory_score: Decimal
    stale_memory_pressure_score: Decimal
    signal_freshness_score: Decimal
    stale_memory_relief_score: Decimal
    memory_alpha_decay_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super(ResearchStrategyDomainTeamMemoryAlphaDecayRow, cls).__init_subclass__(
            **kwargs,
        )
        if cls is not ResearchStrategyDomainTeamMemoryAlphaDecayRow:
            raise TypeError("ResearchStrategyDomainTeamMemoryAlphaDecayRow rejects subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDomainTeamMemoryAlphaDecayRow, "row")
        object.__setattr__(
            self,
            "rank",
            _require_positive_count_decimal("rank", self.rank),
        )
        object.__setattr__(
            self,
            "domain_ref_digest",
            _require_digest_ref("domain_ref_digest", self.domain_ref_digest),
        )
        object.__setattr__(
            self,
            "team_ref_digest",
            _require_digest_ref("team_ref_digest", self.team_ref_digest),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "alpha_signal_age_seconds",
            _require_nonnegative_decimal(
                "alpha_signal_age_seconds",
                self.alpha_signal_age_seconds,
            ),
        )
        for name in (
            "baseline_alpha_score",
            "current_alpha_score",
            "alpha_decay_ratio",
            "alpha_retention_score",
            "memory_reuse_score",
            "calibration_memory_score",
            "evidence_memory_score",
            "stale_memory_pressure_score",
            "signal_freshness_score",
            "stale_memory_relief_score",
            "memory_alpha_decay_score",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        object.__setattr__(self, "status", _require_member("status", self.status, STATUS_SORT_SEQUENCE))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, ROW_REASON_CODE_SEQUENCE, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", _row_payload(self))


@dataclass(frozen=True, slots=True)
class ResearchStrategyDomainTeamMemoryAlphaDecayReasonCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super(ResearchStrategyDomainTeamMemoryAlphaDecayReasonCount, cls).__init_subclass__(
            **kwargs,
        )
        if cls is not ResearchStrategyDomainTeamMemoryAlphaDecayReasonCount:
            raise TypeError(
                "ResearchStrategyDomainTeamMemoryAlphaDecayReasonCount rejects subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDomainTeamMemoryAlphaDecayReasonCount, "reason_count")
        object.__setattr__(
            self,
            "reason_code",
            _require_member("reason_code", self.reason_code, COUNT_REASON_CODE_SEQUENCE),
        )
        object.__setattr__(self, "count", _require_nonnegative_decimal("count", self.count))
        object.__setattr__(self, "row_ratio", _require_ratio_decimal("row_ratio", self.row_ratio))
        _require_hard_flags("reason_count", self)
        _reject_unsafe_public_payload("reason_count", _reason_count_payload(self))


@dataclass(frozen=True, slots=True)
class ResearchStrategyDomainTeamMemoryAlphaDecayReport:
    generated_at: datetime
    config_version: str
    max_pass_alpha_signal_age_seconds: Decimal
    max_watch_alpha_signal_age_seconds: Decimal
    max_pass_alpha_decay_ratio: Decimal
    max_watch_alpha_decay_ratio: Decimal
    min_pass_memory_reuse_score: Decimal
    min_watch_memory_reuse_score: Decimal
    min_pass_calibration_memory_score: Decimal
    min_watch_calibration_memory_score: Decimal
    min_pass_evidence_memory_score: Decimal
    min_watch_evidence_memory_score: Decimal
    max_pass_stale_memory_pressure_score: Decimal
    max_watch_stale_memory_pressure_score: Decimal
    min_pass_memory_alpha_decay_score: Decimal
    min_watch_memory_alpha_decay_score: Decimal
    alpha_retention_weight: Decimal
    memory_reuse_weight: Decimal
    calibration_memory_weight: Decimal
    evidence_memory_weight: Decimal
    signal_freshness_weight: Decimal
    stale_memory_relief_weight: Decimal
    status: str
    snapshot_count: Decimal
    domain_count: Decimal
    team_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_memory_alpha_decay_score: Decimal
    min_memory_alpha_decay_score: Decimal
    max_alpha_decay_ratio: Decimal
    max_alpha_signal_age_seconds: Decimal
    min_memory_reuse_score: Decimal
    min_calibration_memory_score: Decimal
    min_evidence_memory_score: Decimal
    max_stale_memory_pressure_score: Decimal
    rows: tuple[ResearchStrategyDomainTeamMemoryAlphaDecayRow, ...]
    reason_codes: tuple[str, ...]
    reason_counts: tuple[ResearchStrategyDomainTeamMemoryAlphaDecayReasonCount, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super(ResearchStrategyDomainTeamMemoryAlphaDecayReport, cls).__init_subclass__(
            **kwargs,
        )
        if cls is not ResearchStrategyDomainTeamMemoryAlphaDecayReport:
            raise TypeError("ResearchStrategyDomainTeamMemoryAlphaDecayReport rejects subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDomainTeamMemoryAlphaDecayReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_label("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_DOMAIN_TEAM_MEMORY_ALPHA_DECAY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match the supported config version")
        normalized_config = _config_from_report(self)
        for name in CONFIG_DECIMAL_FIELD_NAMES:
            object.__setattr__(self, name, getattr(normalized_config, name))
        object.__setattr__(self, "status", _require_member("status", self.status, STATUS_SORT_SEQUENCE))
        for name in (
            "snapshot_count",
            "domain_count",
            "team_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(self, name, _require_count_decimal(name, getattr(self, name)))
        for name in (
            "average_memory_alpha_decay_score",
            "min_memory_alpha_decay_score",
            "max_alpha_decay_ratio",
            "min_memory_reuse_score",
            "min_calibration_memory_score",
            "min_evidence_memory_score",
            "max_stale_memory_pressure_score",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        object.__setattr__(
            self,
            "max_alpha_signal_age_seconds",
            _require_nonnegative_decimal(
                "max_alpha_signal_age_seconds",
                self.max_alpha_signal_age_seconds,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, REPORT_REASON_CODE_SEQUENCE, allow_empty=False),
        )
        object.__setattr__(
            self,
            "reason_counts",
            _normalize_reason_counts(self.reason_counts),
        )
        _require_hard_flags("report", self)
        _validate_report(self)
        expected_digest = research_strategy_domain_team_memory_alpha_decay_report_digest(self)
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report payload")
        object.__setattr__(self, "derived_validation_digest", expected_digest)
        _reject_unsafe_public_payload("report", self.public_payload)

    @property
    def public_payload(self) -> dict[str, Any]:
        expected_digest = research_strategy_domain_team_memory_alpha_decay_report_digest(self)
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report payload")
        return _report_payload(self, include_digest=True)


def build_research_strategy_domain_team_memory_alpha_decay_report(
    snapshots: tuple[ResearchStrategyDomainTeamMemoryAlphaDecaySnapshot, ...],
    *,
    config: ResearchStrategyDomainTeamMemoryAlphaDecayConfig,
    generated_at: datetime,
) -> ResearchStrategyDomainTeamMemoryAlphaDecayReport:
    if type(config) is not ResearchStrategyDomainTeamMemoryAlphaDecayConfig:
        raise ValueError("config must be a ResearchStrategyDomainTeamMemoryAlphaDecayConfig")
    _require_hard_flags("config", config)
    config = replace(config)
    generated_at = _as_utc("generated_at", generated_at)
    items = _normalize_snapshots(snapshots)
    sorted_rows = tuple(
        sorted(
            (_row_from_snapshot(item, config, generated_at) for item in items),
            key=_row_sort_key,
        ),
    )
    rows = tuple(
        replace(row, rank=_count_decimal(index))
        for index, row in enumerate(sorted_rows, start=1)
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchStrategyDomainTeamMemoryAlphaDecayReport(
        generated_at=generated_at,
        config_version=config.config_version,
        max_pass_alpha_signal_age_seconds=config.max_pass_alpha_signal_age_seconds,
        max_watch_alpha_signal_age_seconds=config.max_watch_alpha_signal_age_seconds,
        max_pass_alpha_decay_ratio=config.max_pass_alpha_decay_ratio,
        max_watch_alpha_decay_ratio=config.max_watch_alpha_decay_ratio,
        min_pass_memory_reuse_score=config.min_pass_memory_reuse_score,
        min_watch_memory_reuse_score=config.min_watch_memory_reuse_score,
        min_pass_calibration_memory_score=config.min_pass_calibration_memory_score,
        min_watch_calibration_memory_score=config.min_watch_calibration_memory_score,
        min_pass_evidence_memory_score=config.min_pass_evidence_memory_score,
        min_watch_evidence_memory_score=config.min_watch_evidence_memory_score,
        max_pass_stale_memory_pressure_score=config.max_pass_stale_memory_pressure_score,
        max_watch_stale_memory_pressure_score=config.max_watch_stale_memory_pressure_score,
        min_pass_memory_alpha_decay_score=config.min_pass_memory_alpha_decay_score,
        min_watch_memory_alpha_decay_score=config.min_watch_memory_alpha_decay_score,
        alpha_retention_weight=config.alpha_retention_weight,
        memory_reuse_weight=config.memory_reuse_weight,
        calibration_memory_weight=config.calibration_memory_weight,
        evidence_memory_weight=config.evidence_memory_weight,
        signal_freshness_weight=config.signal_freshness_weight,
        stale_memory_relief_weight=config.stale_memory_relief_weight,
        status=_report_status(rows),
        snapshot_count=_count_decimal(len(rows)),
        domain_count=_count_decimal(len({row.domain_ref_digest for row in rows})),
        team_count=_count_decimal(len({row.team_ref_digest for row in rows})),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        average_memory_alpha_decay_score=_average_decimal(
            tuple(row.memory_alpha_decay_score for row in rows),
        ),
        min_memory_alpha_decay_score=_min_decimal(
            tuple(row.memory_alpha_decay_score for row in rows),
        ),
        max_alpha_decay_ratio=_max_decimal(tuple(row.alpha_decay_ratio for row in rows)),
        max_alpha_signal_age_seconds=_max_decimal(
            tuple(row.alpha_signal_age_seconds for row in rows),
        ),
        min_memory_reuse_score=_min_decimal(tuple(row.memory_reuse_score for row in rows)),
        min_calibration_memory_score=_min_decimal(
            tuple(row.calibration_memory_score for row in rows),
        ),
        min_evidence_memory_score=_min_decimal(tuple(row.evidence_memory_score for row in rows)),
        max_stale_memory_pressure_score=_max_decimal(
            tuple(row.stale_memory_pressure_score for row in rows),
        ),
        rows=rows,
        reason_codes=reason_codes,
        reason_counts=_reason_counts(rows),
    )


def research_strategy_domain_team_memory_alpha_decay_report_payload(
    report: ResearchStrategyDomainTeamMemoryAlphaDecayReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyDomainTeamMemoryAlphaDecayReport:
        _require_hard_flags("report", report)
        _validate_report(report)
        if (
            report.derived_validation_digest
            != research_strategy_domain_team_memory_alpha_decay_report_digest(report)
        ):
            raise ValueError("derived_validation_digest must match report payload")
        payload = report.public_payload
    elif type(report) is dict:
        return _validate_payload_dict(report)
    else:
        raise ValueError(
            "report must be a ResearchStrategyDomainTeamMemoryAlphaDecayReport",
        )
    _reject_unsafe_public_payload("payload", payload)
    _validate_payload_digest(payload)
    return _copy_json_object(payload)


def research_strategy_domain_team_memory_alpha_decay_report_digest(
    report: ResearchStrategyDomainTeamMemoryAlphaDecayReport,
) -> str:
    if type(report) is not ResearchStrategyDomainTeamMemoryAlphaDecayReport:
        raise ValueError("report must be a ResearchStrategyDomainTeamMemoryAlphaDecayReport")
    _require_hard_flags("report", report)
    _validate_report(report)
    expected_digest = _payload_digest(_report_payload(report, include_digest=False))
    if report.derived_validation_digest:
        _require_digest("derived_validation_digest", report.derived_validation_digest)
        if report.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report payload")
    return expected_digest


def _row_from_snapshot(
    snapshot: ResearchStrategyDomainTeamMemoryAlphaDecaySnapshot,
    config: ResearchStrategyDomainTeamMemoryAlphaDecayConfig,
    generated_at: datetime,
) -> ResearchStrategyDomainTeamMemoryAlphaDecayRow:
    if snapshot.last_alpha_signal_at > generated_at:
        raise ValueError("last_alpha_signal_at must not be after generated_at")
    if snapshot.observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    alpha_signal_age_seconds = _seconds_between(snapshot.last_alpha_signal_at, generated_at)
    alpha_decay_ratio = _alpha_decay_ratio(
        snapshot.baseline_alpha_score,
        snapshot.current_alpha_score,
    )
    alpha_retention_score = _subtract_decimal(ONE, alpha_decay_ratio)
    signal_freshness_score = _signal_freshness_score(
        alpha_signal_age_seconds,
        config.max_watch_alpha_signal_age_seconds,
    )
    stale_memory_relief_score = _subtract_decimal(ONE, snapshot.stale_memory_pressure_score)
    memory_alpha_decay_score = _memory_alpha_decay_score(
        alpha_retention_score=alpha_retention_score,
        memory_reuse_score=snapshot.memory_reuse_score,
        calibration_memory_score=snapshot.calibration_memory_score,
        evidence_memory_score=snapshot.evidence_memory_score,
        signal_freshness_score=signal_freshness_score,
        stale_memory_relief_score=stale_memory_relief_score,
        config=config,
    )
    status = _row_status(
        alpha_decay_ratio=alpha_decay_ratio,
        alpha_signal_age_seconds=alpha_signal_age_seconds,
        memory_reuse_score=snapshot.memory_reuse_score,
        calibration_memory_score=snapshot.calibration_memory_score,
        evidence_memory_score=snapshot.evidence_memory_score,
        stale_memory_pressure_score=snapshot.stale_memory_pressure_score,
        memory_alpha_decay_score=memory_alpha_decay_score,
        config=config,
    )
    return ResearchStrategyDomainTeamMemoryAlphaDecayRow(
        rank=ONE,
        domain_ref_digest=_digest_ref(snapshot.domain_ref),
        team_ref_digest=_digest_ref(snapshot.team_ref),
        observed_at=snapshot.observed_at,
        alpha_signal_age_seconds=alpha_signal_age_seconds,
        baseline_alpha_score=snapshot.baseline_alpha_score,
        current_alpha_score=snapshot.current_alpha_score,
        alpha_decay_ratio=alpha_decay_ratio,
        alpha_retention_score=alpha_retention_score,
        memory_reuse_score=snapshot.memory_reuse_score,
        calibration_memory_score=snapshot.calibration_memory_score,
        evidence_memory_score=snapshot.evidence_memory_score,
        stale_memory_pressure_score=snapshot.stale_memory_pressure_score,
        signal_freshness_score=signal_freshness_score,
        stale_memory_relief_score=stale_memory_relief_score,
        memory_alpha_decay_score=memory_alpha_decay_score,
        status=status,
        reason_codes=_row_reason_codes(
            upstream_reason_codes=snapshot.reason_codes,
            alpha_decay_ratio=alpha_decay_ratio,
            alpha_signal_age_seconds=alpha_signal_age_seconds,
            memory_reuse_score=snapshot.memory_reuse_score,
            calibration_memory_score=snapshot.calibration_memory_score,
            evidence_memory_score=snapshot.evidence_memory_score,
            stale_memory_pressure_score=snapshot.stale_memory_pressure_score,
            memory_alpha_decay_score=memory_alpha_decay_score,
            config=config,
        ),
    )


def _row_reason_codes(
    *,
    upstream_reason_codes: tuple[str, ...],
    alpha_decay_ratio: Decimal,
    alpha_signal_age_seconds: Decimal,
    memory_reuse_score: Decimal,
    calibration_memory_score: Decimal,
    evidence_memory_score: Decimal,
    stale_memory_pressure_score: Decimal,
    memory_alpha_decay_score: Decimal,
    config: ResearchStrategyDomainTeamMemoryAlphaDecayConfig,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    if alpha_decay_ratio > config.max_watch_alpha_decay_ratio:
        reason_codes.append(ALPHA_DECAY_BLOCK_REASON)
    elif alpha_decay_ratio > config.max_pass_alpha_decay_ratio:
        reason_codes.append(ALPHA_DECAY_WATCH_REASON)
    if alpha_signal_age_seconds > config.max_watch_alpha_signal_age_seconds:
        reason_codes.append(ALPHA_SIGNAL_AGE_BLOCK_REASON)
    elif alpha_signal_age_seconds > config.max_pass_alpha_signal_age_seconds:
        reason_codes.append(ALPHA_SIGNAL_AGE_WATCH_REASON)
    if memory_reuse_score < config.min_watch_memory_reuse_score:
        reason_codes.append(MEMORY_REUSE_BLOCK_REASON)
    elif memory_reuse_score < config.min_pass_memory_reuse_score:
        reason_codes.append(MEMORY_REUSE_WATCH_REASON)
    if calibration_memory_score < config.min_watch_calibration_memory_score:
        reason_codes.append(CALIBRATION_MEMORY_BLOCK_REASON)
    elif calibration_memory_score < config.min_pass_calibration_memory_score:
        reason_codes.append(CALIBRATION_MEMORY_WATCH_REASON)
    if evidence_memory_score < config.min_watch_evidence_memory_score:
        reason_codes.append(EVIDENCE_MEMORY_BLOCK_REASON)
    elif evidence_memory_score < config.min_pass_evidence_memory_score:
        reason_codes.append(EVIDENCE_MEMORY_WATCH_REASON)
    if stale_memory_pressure_score > config.max_watch_stale_memory_pressure_score:
        reason_codes.append(STALE_MEMORY_PRESSURE_BLOCK_REASON)
    elif stale_memory_pressure_score > config.max_pass_stale_memory_pressure_score:
        reason_codes.append(STALE_MEMORY_PRESSURE_WATCH_REASON)
    if memory_alpha_decay_score < config.min_watch_memory_alpha_decay_score:
        reason_codes.append(MEMORY_ALPHA_DECAY_SCORE_BLOCK_REASON)
    elif memory_alpha_decay_score < config.min_pass_memory_alpha_decay_score:
        reason_codes.append(MEMORY_ALPHA_DECAY_SCORE_WATCH_REASON)
    if len(reason_codes) == len(upstream_reason_codes):
        reason_codes.append(MEMORY_ALPHA_DECAY_PASS_REASON)
    return _normalize_reason_codes(tuple(reason_codes), ROW_REASON_CODE_SEQUENCE, allow_empty=False)


def _row_status(
    *,
    alpha_decay_ratio: Decimal,
    alpha_signal_age_seconds: Decimal,
    memory_reuse_score: Decimal,
    calibration_memory_score: Decimal,
    evidence_memory_score: Decimal,
    stale_memory_pressure_score: Decimal,
    memory_alpha_decay_score: Decimal,
    config: ResearchStrategyDomainTeamMemoryAlphaDecayConfig,
) -> str:
    if (
        alpha_decay_ratio > config.max_watch_alpha_decay_ratio
        or alpha_signal_age_seconds > config.max_watch_alpha_signal_age_seconds
        or memory_reuse_score < config.min_watch_memory_reuse_score
        or calibration_memory_score < config.min_watch_calibration_memory_score
        or evidence_memory_score < config.min_watch_evidence_memory_score
        or stale_memory_pressure_score > config.max_watch_stale_memory_pressure_score
        or memory_alpha_decay_score < config.min_watch_memory_alpha_decay_score
    ):
        return STATUS_BLOCK
    if (
        alpha_decay_ratio > config.max_pass_alpha_decay_ratio
        or alpha_signal_age_seconds > config.max_pass_alpha_signal_age_seconds
        or memory_reuse_score < config.min_pass_memory_reuse_score
        or calibration_memory_score < config.min_pass_calibration_memory_score
        or evidence_memory_score < config.min_pass_evidence_memory_score
        or stale_memory_pressure_score > config.max_pass_stale_memory_pressure_score
        or memory_alpha_decay_score < config.min_pass_memory_alpha_decay_score
    ):
        return STATUS_WATCH
    return STATUS_PASS


def _report_status(rows: tuple[ResearchStrategyDomainTeamMemoryAlphaDecayRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchStrategyDomainTeamMemoryAlphaDecayRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_SNAPSHOTS_REASON,)
    found = {reason_code for row in rows for reason_code in row.reason_codes}
    reason_codes: list[str] = []
    if any(row.status == STATUS_BLOCK for row in rows):
        reason_codes.append(REPORT_BLOCK_PRESENT_REASON)
    if any(row.status == STATUS_WATCH for row in rows):
        reason_codes.append(REPORT_WATCH_PRESENT_REASON)
    if ALPHA_DECAY_BLOCK_REASON in found or ALPHA_DECAY_WATCH_REASON in found:
        reason_codes.append(REPORT_ALPHA_DECAY_GAP_REASON)
    if ALPHA_SIGNAL_AGE_BLOCK_REASON in found or ALPHA_SIGNAL_AGE_WATCH_REASON in found:
        reason_codes.append(REPORT_ALPHA_SIGNAL_AGE_GAP_REASON)
    if MEMORY_REUSE_BLOCK_REASON in found or MEMORY_REUSE_WATCH_REASON in found:
        reason_codes.append(REPORT_MEMORY_REUSE_GAP_REASON)
    if CALIBRATION_MEMORY_BLOCK_REASON in found or CALIBRATION_MEMORY_WATCH_REASON in found:
        reason_codes.append(REPORT_CALIBRATION_MEMORY_GAP_REASON)
    if EVIDENCE_MEMORY_BLOCK_REASON in found or EVIDENCE_MEMORY_WATCH_REASON in found:
        reason_codes.append(REPORT_EVIDENCE_MEMORY_GAP_REASON)
    if (
        STALE_MEMORY_PRESSURE_BLOCK_REASON in found
        or STALE_MEMORY_PRESSURE_WATCH_REASON in found
    ):
        reason_codes.append(REPORT_STALE_MEMORY_PRESSURE_REASON)
    if not reason_codes:
        reason_codes.append(REPORT_CLEAR_REASON)
    return _normalize_reason_codes(tuple(reason_codes), REPORT_REASON_CODE_SEQUENCE, allow_empty=False)


def _reason_counts(
    rows: tuple[ResearchStrategyDomainTeamMemoryAlphaDecayRow, ...],
) -> tuple[ResearchStrategyDomainTeamMemoryAlphaDecayReasonCount, ...]:
    if not rows:
        return (
            ResearchStrategyDomainTeamMemoryAlphaDecayReasonCount(
                reason_code=NO_SNAPSHOTS_REASON,
                count=ONE,
                row_ratio=ONE,
            ),
        )
    counts = Counter(reason_code for row in rows for reason_code in row.reason_codes)
    row_count = _count_decimal(len(rows))
    return tuple(
        ResearchStrategyDomainTeamMemoryAlphaDecayReasonCount(
            reason_code=reason_code,
            count=_count_decimal(counts[reason_code]),
            row_ratio=_ratio_decimal(_count_decimal(counts[reason_code]), row_count),
        )
        for reason_code in COUNT_REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _normalize_snapshots(
    snapshots: tuple[ResearchStrategyDomainTeamMemoryAlphaDecaySnapshot, ...],
) -> tuple[ResearchStrategyDomainTeamMemoryAlphaDecaySnapshot, ...]:
    if isinstance(snapshots, (str, bytes)):
        raise ValueError("snapshots must be an iterable")
    try:
        items = tuple(snapshots)
    except TypeError as exc:
        raise ValueError("snapshots must be an iterable") from exc
    normalized: list[ResearchStrategyDomainTeamMemoryAlphaDecaySnapshot] = []
    for item in items:
        if type(item) is not ResearchStrategyDomainTeamMemoryAlphaDecaySnapshot:
            raise ValueError(
                "snapshots must contain ResearchStrategyDomainTeamMemoryAlphaDecaySnapshot values",
            )
        _require_hard_flags("snapshot", item)
        normalized.append(replace(item))
    return tuple(normalized)


def _normalize_rows(
    rows: tuple[ResearchStrategyDomainTeamMemoryAlphaDecayRow, ...],
) -> tuple[ResearchStrategyDomainTeamMemoryAlphaDecayRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchStrategyDomainTeamMemoryAlphaDecayRow:
            raise ValueError("rows must contain ResearchStrategyDomainTeamMemoryAlphaDecayRow values")
        _require_hard_flags("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return rows


def _normalize_reason_counts(
    counts: tuple[ResearchStrategyDomainTeamMemoryAlphaDecayReasonCount, ...],
) -> tuple[ResearchStrategyDomainTeamMemoryAlphaDecayReasonCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_counts must be a tuple")
    for item in counts:
        if type(item) is not ResearchStrategyDomainTeamMemoryAlphaDecayReasonCount:
            raise ValueError(
                "reason_counts must contain ResearchStrategyDomainTeamMemoryAlphaDecayReasonCount values",
            )
        _require_hard_flags("reason_count", item)
    if counts != tuple(sorted(counts, key=lambda item: _reason_sort_key(item.reason_code))):
        raise ValueError("reason_counts must be deterministically sorted")
    return counts


def _row_sort_key(
    row: ResearchStrategyDomainTeamMemoryAlphaDecayRow,
) -> tuple[Any, ...]:
    return (
        STATUS_SORT_SEQUENCE.index(row.status),
        row.memory_alpha_decay_score,
        -row.alpha_decay_ratio,
        row.domain_ref_digest,
        row.team_ref_digest,
        row.observed_at,
        row.alpha_signal_age_seconds,
        row.baseline_alpha_score,
        row.current_alpha_score,
        row.alpha_retention_score,
        row.memory_reuse_score,
        row.calibration_memory_score,
        row.evidence_memory_score,
        row.stale_memory_pressure_score,
        row.signal_freshness_score,
        row.stale_memory_relief_score,
        row.reason_codes,
    )


def _status_count(
    rows: tuple[ResearchStrategyDomainTeamMemoryAlphaDecayRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _validate_report(report: ResearchStrategyDomainTeamMemoryAlphaDecayReport) -> None:
    config = _config_from_report(report)
    for row in report.rows:
        _validate_row_against_config(row, config)
    expected_ranks = tuple(_count_decimal(index) for index in range(1, len(report.rows) + 1))
    if tuple(row.rank for row in report.rows) != expected_ranks:
        raise ValueError("rank must match row order")
    if report.snapshot_count != _count_decimal(len(report.rows)):
        raise ValueError("snapshot_count must match rows")
    if report.domain_count != _count_decimal(len({row.domain_ref_digest for row in report.rows})):
        raise ValueError("domain_count must match rows")
    if report.team_count != _count_decimal(len({row.team_ref_digest for row in report.rows})):
        raise ValueError("team_count must match rows")
    if report.pass_count != _status_count(report.rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.average_memory_alpha_decay_score != _average_decimal(
        tuple(row.memory_alpha_decay_score for row in report.rows),
    ):
        raise ValueError("average_memory_alpha_decay_score must match rows")
    if report.min_memory_alpha_decay_score != _min_decimal(
        tuple(row.memory_alpha_decay_score for row in report.rows),
    ):
        raise ValueError("min_memory_alpha_decay_score must match rows")
    if report.max_alpha_decay_ratio != _max_decimal(tuple(row.alpha_decay_ratio for row in report.rows)):
        raise ValueError("max_alpha_decay_ratio must match rows")
    if report.max_alpha_signal_age_seconds != _max_decimal(
        tuple(row.alpha_signal_age_seconds for row in report.rows),
    ):
        raise ValueError("max_alpha_signal_age_seconds must match rows")
    if report.min_memory_reuse_score != _min_decimal(tuple(row.memory_reuse_score for row in report.rows)):
        raise ValueError("min_memory_reuse_score must match rows")
    if report.min_calibration_memory_score != _min_decimal(
        tuple(row.calibration_memory_score for row in report.rows),
    ):
        raise ValueError("min_calibration_memory_score must match rows")
    if report.min_evidence_memory_score != _min_decimal(
        tuple(row.evidence_memory_score for row in report.rows),
    ):
        raise ValueError("min_evidence_memory_score must match rows")
    if report.max_stale_memory_pressure_score != _max_decimal(
        tuple(row.stale_memory_pressure_score for row in report.rows),
    ):
        raise ValueError("max_stale_memory_pressure_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_counts != _reason_counts(report.rows):
        raise ValueError("reason_counts must match rows")


def _config_from_report(
    report: ResearchStrategyDomainTeamMemoryAlphaDecayReport,
) -> ResearchStrategyDomainTeamMemoryAlphaDecayConfig:
    return ResearchStrategyDomainTeamMemoryAlphaDecayConfig(
        config_version=report.config_version,
        max_pass_alpha_signal_age_seconds=report.max_pass_alpha_signal_age_seconds,
        max_watch_alpha_signal_age_seconds=report.max_watch_alpha_signal_age_seconds,
        max_pass_alpha_decay_ratio=report.max_pass_alpha_decay_ratio,
        max_watch_alpha_decay_ratio=report.max_watch_alpha_decay_ratio,
        min_pass_memory_reuse_score=report.min_pass_memory_reuse_score,
        min_watch_memory_reuse_score=report.min_watch_memory_reuse_score,
        min_pass_calibration_memory_score=report.min_pass_calibration_memory_score,
        min_watch_calibration_memory_score=report.min_watch_calibration_memory_score,
        min_pass_evidence_memory_score=report.min_pass_evidence_memory_score,
        min_watch_evidence_memory_score=report.min_watch_evidence_memory_score,
        max_pass_stale_memory_pressure_score=report.max_pass_stale_memory_pressure_score,
        max_watch_stale_memory_pressure_score=report.max_watch_stale_memory_pressure_score,
        min_pass_memory_alpha_decay_score=report.min_pass_memory_alpha_decay_score,
        min_watch_memory_alpha_decay_score=report.min_watch_memory_alpha_decay_score,
        alpha_retention_weight=report.alpha_retention_weight,
        memory_reuse_weight=report.memory_reuse_weight,
        calibration_memory_weight=report.calibration_memory_weight,
        evidence_memory_weight=report.evidence_memory_weight,
        signal_freshness_weight=report.signal_freshness_weight,
        stale_memory_relief_weight=report.stale_memory_relief_weight,
    )


def _validate_row_against_config(
    row: ResearchStrategyDomainTeamMemoryAlphaDecayRow,
    config: ResearchStrategyDomainTeamMemoryAlphaDecayConfig,
) -> None:
    expected_alpha_decay_ratio = _alpha_decay_ratio(
        row.baseline_alpha_score,
        row.current_alpha_score,
    )
    if row.alpha_decay_ratio != expected_alpha_decay_ratio:
        raise ValueError("alpha_decay_ratio must match row metrics")
    expected_alpha_retention_score = _subtract_decimal(ONE, expected_alpha_decay_ratio)
    if row.alpha_retention_score != expected_alpha_retention_score:
        raise ValueError("alpha_retention_score must match row metrics")
    expected_signal_freshness_score = _signal_freshness_score(
        row.alpha_signal_age_seconds,
        config.max_watch_alpha_signal_age_seconds,
    )
    if row.signal_freshness_score != expected_signal_freshness_score:
        raise ValueError("signal_freshness_score must match row metrics")
    expected_stale_memory_relief_score = _subtract_decimal(
        ONE,
        row.stale_memory_pressure_score,
    )
    if row.stale_memory_relief_score != expected_stale_memory_relief_score:
        raise ValueError("stale_memory_relief_score must match row metrics")
    expected_memory_alpha_decay_score = _memory_alpha_decay_score(
        alpha_retention_score=expected_alpha_retention_score,
        memory_reuse_score=row.memory_reuse_score,
        calibration_memory_score=row.calibration_memory_score,
        evidence_memory_score=row.evidence_memory_score,
        signal_freshness_score=expected_signal_freshness_score,
        stale_memory_relief_score=expected_stale_memory_relief_score,
        config=config,
    )
    if row.memory_alpha_decay_score != expected_memory_alpha_decay_score:
        raise ValueError("memory_alpha_decay_score must match row metrics")
    expected_status = _row_status(
        alpha_decay_ratio=expected_alpha_decay_ratio,
        alpha_signal_age_seconds=row.alpha_signal_age_seconds,
        memory_reuse_score=row.memory_reuse_score,
        calibration_memory_score=row.calibration_memory_score,
        evidence_memory_score=row.evidence_memory_score,
        stale_memory_pressure_score=row.stale_memory_pressure_score,
        memory_alpha_decay_score=expected_memory_alpha_decay_score,
        config=config,
    )
    if row.status != expected_status:
        raise ValueError("status must match row metrics")
    upstream_reason_codes = tuple(
        reason_code
        for reason_code in row.reason_codes
        if reason_code in UPSTREAM_ROW_REASON_CODE_SEQUENCE
    )
    expected_reason_codes = _row_reason_codes(
        upstream_reason_codes=upstream_reason_codes,
        alpha_decay_ratio=expected_alpha_decay_ratio,
        alpha_signal_age_seconds=row.alpha_signal_age_seconds,
        memory_reuse_score=row.memory_reuse_score,
        calibration_memory_score=row.calibration_memory_score,
        evidence_memory_score=row.evidence_memory_score,
        stale_memory_pressure_score=row.stale_memory_pressure_score,
        memory_alpha_decay_score=expected_memory_alpha_decay_score,
        config=config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row metrics")


def _report_payload(
    report: ResearchStrategyDomainTeamMemoryAlphaDecayReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "max_pass_alpha_signal_age_seconds": _decimal_payload(
            report.max_pass_alpha_signal_age_seconds,
        ),
        "max_watch_alpha_signal_age_seconds": _decimal_payload(
            report.max_watch_alpha_signal_age_seconds,
        ),
        "max_pass_alpha_decay_ratio": _decimal_payload(report.max_pass_alpha_decay_ratio),
        "max_watch_alpha_decay_ratio": _decimal_payload(report.max_watch_alpha_decay_ratio),
        "min_pass_memory_reuse_score": _decimal_payload(report.min_pass_memory_reuse_score),
        "min_watch_memory_reuse_score": _decimal_payload(
            report.min_watch_memory_reuse_score,
        ),
        "min_pass_calibration_memory_score": _decimal_payload(
            report.min_pass_calibration_memory_score,
        ),
        "min_watch_calibration_memory_score": _decimal_payload(
            report.min_watch_calibration_memory_score,
        ),
        "min_pass_evidence_memory_score": _decimal_payload(
            report.min_pass_evidence_memory_score,
        ),
        "min_watch_evidence_memory_score": _decimal_payload(
            report.min_watch_evidence_memory_score,
        ),
        "max_pass_stale_memory_pressure_score": _decimal_payload(
            report.max_pass_stale_memory_pressure_score,
        ),
        "max_watch_stale_memory_pressure_score": _decimal_payload(
            report.max_watch_stale_memory_pressure_score,
        ),
        "min_pass_memory_alpha_decay_score": _decimal_payload(
            report.min_pass_memory_alpha_decay_score,
        ),
        "min_watch_memory_alpha_decay_score": _decimal_payload(
            report.min_watch_memory_alpha_decay_score,
        ),
        "alpha_retention_weight": _decimal_payload(report.alpha_retention_weight),
        "memory_reuse_weight": _decimal_payload(report.memory_reuse_weight),
        "calibration_memory_weight": _decimal_payload(report.calibration_memory_weight),
        "evidence_memory_weight": _decimal_payload(report.evidence_memory_weight),
        "signal_freshness_weight": _decimal_payload(report.signal_freshness_weight),
        "stale_memory_relief_weight": _decimal_payload(report.stale_memory_relief_weight),
        "status": report.status,
        "snapshot_count": _decimal_payload(report.snapshot_count),
        "domain_count": _decimal_payload(report.domain_count),
        "team_count": _decimal_payload(report.team_count),
        "pass_count": _decimal_payload(report.pass_count),
        "watch_count": _decimal_payload(report.watch_count),
        "block_count": _decimal_payload(report.block_count),
        "average_memory_alpha_decay_score": _decimal_payload(
            report.average_memory_alpha_decay_score,
        ),
        "min_memory_alpha_decay_score": _decimal_payload(report.min_memory_alpha_decay_score),
        "max_alpha_decay_ratio": _decimal_payload(report.max_alpha_decay_ratio),
        "max_alpha_signal_age_seconds": _decimal_payload(report.max_alpha_signal_age_seconds),
        "min_memory_reuse_score": _decimal_payload(report.min_memory_reuse_score),
        "min_calibration_memory_score": _decimal_payload(report.min_calibration_memory_score),
        "min_evidence_memory_score": _decimal_payload(report.min_evidence_memory_score),
        "max_stale_memory_pressure_score": _decimal_payload(
            report.max_stale_memory_pressure_score,
        ),
        "rows": [_row_payload(row) for row in report.rows],
        "reason_codes": list(report.reason_codes),
        "reason_counts": [_reason_count_payload(item) for item in report.reason_counts],
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    if include_digest:
        payload["derived_validation_digest"] = report.derived_validation_digest
    return payload


def _row_payload(row: ResearchStrategyDomainTeamMemoryAlphaDecayRow) -> dict[str, Any]:
    return {
        "rank": _decimal_payload(row.rank),
        "domain_ref_digest": row.domain_ref_digest,
        "team_ref_digest": row.team_ref_digest,
        "observed_at": row.observed_at.isoformat(),
        "alpha_signal_age_seconds": _decimal_payload(row.alpha_signal_age_seconds),
        "baseline_alpha_score": _decimal_payload(row.baseline_alpha_score),
        "current_alpha_score": _decimal_payload(row.current_alpha_score),
        "alpha_decay_ratio": _decimal_payload(row.alpha_decay_ratio),
        "alpha_retention_score": _decimal_payload(row.alpha_retention_score),
        "memory_reuse_score": _decimal_payload(row.memory_reuse_score),
        "calibration_memory_score": _decimal_payload(row.calibration_memory_score),
        "evidence_memory_score": _decimal_payload(row.evidence_memory_score),
        "stale_memory_pressure_score": _decimal_payload(row.stale_memory_pressure_score),
        "signal_freshness_score": _decimal_payload(row.signal_freshness_score),
        "stale_memory_relief_score": _decimal_payload(row.stale_memory_relief_score),
        "memory_alpha_decay_score": _decimal_payload(row.memory_alpha_decay_score),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _reason_count_payload(
    item: ResearchStrategyDomainTeamMemoryAlphaDecayReasonCount,
) -> dict[str, Any]:
    return {
        "reason_code": item.reason_code,
        "count": _decimal_payload(item.count),
        "row_ratio": _decimal_payload(item.row_ratio),
        "paper_only": item.paper_only,
        "report_only": item.report_only,
        "readonly": item.readonly,
    }


def _validate_payload_dict(payload: dict[str, Any]) -> dict[str, Any]:
    _require_exact_payload_schema(
        "report",
        payload,
        ResearchStrategyDomainTeamMemoryAlphaDecayReport,
    )
    _reject_unsafe_public_payload("payload", payload)
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_raw_numeric_payload_values(payload)
    _validate_payload_digest(payload)
    reconstructed = _report_from_payload(payload)
    canonical_payload = reconstructed.public_payload
    if payload != canonical_payload:
        raise ValueError("payload must use canonical report payload schema")
    return _copy_json_object(canonical_payload)


def _report_from_payload(
    payload: dict[str, Any],
) -> ResearchStrategyDomainTeamMemoryAlphaDecayReport:
    rows = tuple(
        _row_from_payload(item, index=index)
        for index, item in enumerate(_payload_list("rows", payload["rows"]))
    )
    reason_counts = tuple(
        _reason_count_from_payload(item, index=index)
        for index, item in enumerate(
            _payload_list("reason_counts", payload["reason_counts"]),
        )
    )
    return ResearchStrategyDomainTeamMemoryAlphaDecayReport(
        generated_at=_datetime_from_payload("generated_at", payload["generated_at"]),
        config_version=_string_from_payload("config_version", payload["config_version"]),
        max_pass_alpha_signal_age_seconds=_decimal_from_payload(
            "max_pass_alpha_signal_age_seconds",
            payload["max_pass_alpha_signal_age_seconds"],
        ),
        max_watch_alpha_signal_age_seconds=_decimal_from_payload(
            "max_watch_alpha_signal_age_seconds",
            payload["max_watch_alpha_signal_age_seconds"],
        ),
        max_pass_alpha_decay_ratio=_decimal_from_payload(
            "max_pass_alpha_decay_ratio",
            payload["max_pass_alpha_decay_ratio"],
        ),
        max_watch_alpha_decay_ratio=_decimal_from_payload(
            "max_watch_alpha_decay_ratio",
            payload["max_watch_alpha_decay_ratio"],
        ),
        min_pass_memory_reuse_score=_decimal_from_payload(
            "min_pass_memory_reuse_score",
            payload["min_pass_memory_reuse_score"],
        ),
        min_watch_memory_reuse_score=_decimal_from_payload(
            "min_watch_memory_reuse_score",
            payload["min_watch_memory_reuse_score"],
        ),
        min_pass_calibration_memory_score=_decimal_from_payload(
            "min_pass_calibration_memory_score",
            payload["min_pass_calibration_memory_score"],
        ),
        min_watch_calibration_memory_score=_decimal_from_payload(
            "min_watch_calibration_memory_score",
            payload["min_watch_calibration_memory_score"],
        ),
        min_pass_evidence_memory_score=_decimal_from_payload(
            "min_pass_evidence_memory_score",
            payload["min_pass_evidence_memory_score"],
        ),
        min_watch_evidence_memory_score=_decimal_from_payload(
            "min_watch_evidence_memory_score",
            payload["min_watch_evidence_memory_score"],
        ),
        max_pass_stale_memory_pressure_score=_decimal_from_payload(
            "max_pass_stale_memory_pressure_score",
            payload["max_pass_stale_memory_pressure_score"],
        ),
        max_watch_stale_memory_pressure_score=_decimal_from_payload(
            "max_watch_stale_memory_pressure_score",
            payload["max_watch_stale_memory_pressure_score"],
        ),
        min_pass_memory_alpha_decay_score=_decimal_from_payload(
            "min_pass_memory_alpha_decay_score",
            payload["min_pass_memory_alpha_decay_score"],
        ),
        min_watch_memory_alpha_decay_score=_decimal_from_payload(
            "min_watch_memory_alpha_decay_score",
            payload["min_watch_memory_alpha_decay_score"],
        ),
        alpha_retention_weight=_decimal_from_payload(
            "alpha_retention_weight",
            payload["alpha_retention_weight"],
        ),
        memory_reuse_weight=_decimal_from_payload(
            "memory_reuse_weight",
            payload["memory_reuse_weight"],
        ),
        calibration_memory_weight=_decimal_from_payload(
            "calibration_memory_weight",
            payload["calibration_memory_weight"],
        ),
        evidence_memory_weight=_decimal_from_payload(
            "evidence_memory_weight",
            payload["evidence_memory_weight"],
        ),
        signal_freshness_weight=_decimal_from_payload(
            "signal_freshness_weight",
            payload["signal_freshness_weight"],
        ),
        stale_memory_relief_weight=_decimal_from_payload(
            "stale_memory_relief_weight",
            payload["stale_memory_relief_weight"],
        ),
        status=_string_from_payload("status", payload["status"]),
        snapshot_count=_decimal_from_payload("snapshot_count", payload["snapshot_count"]),
        domain_count=_decimal_from_payload("domain_count", payload["domain_count"]),
        team_count=_decimal_from_payload("team_count", payload["team_count"]),
        pass_count=_decimal_from_payload("pass_count", payload["pass_count"]),
        watch_count=_decimal_from_payload("watch_count", payload["watch_count"]),
        block_count=_decimal_from_payload("block_count", payload["block_count"]),
        average_memory_alpha_decay_score=_decimal_from_payload(
            "average_memory_alpha_decay_score",
            payload["average_memory_alpha_decay_score"],
        ),
        min_memory_alpha_decay_score=_decimal_from_payload(
            "min_memory_alpha_decay_score",
            payload["min_memory_alpha_decay_score"],
        ),
        max_alpha_decay_ratio=_decimal_from_payload(
            "max_alpha_decay_ratio",
            payload["max_alpha_decay_ratio"],
        ),
        max_alpha_signal_age_seconds=_decimal_from_payload(
            "max_alpha_signal_age_seconds",
            payload["max_alpha_signal_age_seconds"],
        ),
        min_memory_reuse_score=_decimal_from_payload(
            "min_memory_reuse_score",
            payload["min_memory_reuse_score"],
        ),
        min_calibration_memory_score=_decimal_from_payload(
            "min_calibration_memory_score",
            payload["min_calibration_memory_score"],
        ),
        min_evidence_memory_score=_decimal_from_payload(
            "min_evidence_memory_score",
            payload["min_evidence_memory_score"],
        ),
        max_stale_memory_pressure_score=_decimal_from_payload(
            "max_stale_memory_pressure_score",
            payload["max_stale_memory_pressure_score"],
        ),
        rows=rows,
        reason_codes=_string_tuple_from_payload(
            "reason_codes",
            payload["reason_codes"],
        ),
        reason_counts=reason_counts,
        derived_validation_digest="",
        paper_only=_bool_from_payload("paper_only", payload["paper_only"]),
        report_only=_bool_from_payload("report_only", payload["report_only"]),
        readonly=_bool_from_payload("readonly", payload["readonly"]),
    )


def _row_from_payload(
    value: object,
    *,
    index: int,
) -> ResearchStrategyDomainTeamMemoryAlphaDecayRow:
    label = f"rows[{index}]"
    payload = _mapping_from_payload(label, value)
    _require_exact_payload_schema(
        "row",
        payload,
        ResearchStrategyDomainTeamMemoryAlphaDecayRow,
    )
    return ResearchStrategyDomainTeamMemoryAlphaDecayRow(
        rank=_decimal_from_payload(f"{label}.rank", payload["rank"]),
        domain_ref_digest=_string_from_payload(
            f"{label}.domain_ref_digest",
            payload["domain_ref_digest"],
        ),
        team_ref_digest=_string_from_payload(
            f"{label}.team_ref_digest",
            payload["team_ref_digest"],
        ),
        observed_at=_datetime_from_payload(
            f"{label}.observed_at",
            payload["observed_at"],
        ),
        alpha_signal_age_seconds=_decimal_from_payload(
            f"{label}.alpha_signal_age_seconds",
            payload["alpha_signal_age_seconds"],
        ),
        baseline_alpha_score=_decimal_from_payload(
            f"{label}.baseline_alpha_score",
            payload["baseline_alpha_score"],
        ),
        current_alpha_score=_decimal_from_payload(
            f"{label}.current_alpha_score",
            payload["current_alpha_score"],
        ),
        alpha_decay_ratio=_decimal_from_payload(
            f"{label}.alpha_decay_ratio",
            payload["alpha_decay_ratio"],
        ),
        alpha_retention_score=_decimal_from_payload(
            f"{label}.alpha_retention_score",
            payload["alpha_retention_score"],
        ),
        memory_reuse_score=_decimal_from_payload(
            f"{label}.memory_reuse_score",
            payload["memory_reuse_score"],
        ),
        calibration_memory_score=_decimal_from_payload(
            f"{label}.calibration_memory_score",
            payload["calibration_memory_score"],
        ),
        evidence_memory_score=_decimal_from_payload(
            f"{label}.evidence_memory_score",
            payload["evidence_memory_score"],
        ),
        stale_memory_pressure_score=_decimal_from_payload(
            f"{label}.stale_memory_pressure_score",
            payload["stale_memory_pressure_score"],
        ),
        signal_freshness_score=_decimal_from_payload(
            f"{label}.signal_freshness_score",
            payload["signal_freshness_score"],
        ),
        stale_memory_relief_score=_decimal_from_payload(
            f"{label}.stale_memory_relief_score",
            payload["stale_memory_relief_score"],
        ),
        memory_alpha_decay_score=_decimal_from_payload(
            f"{label}.memory_alpha_decay_score",
            payload["memory_alpha_decay_score"],
        ),
        status=_string_from_payload(f"{label}.status", payload["status"]),
        reason_codes=_string_tuple_from_payload(
            f"{label}.reason_codes",
            payload["reason_codes"],
        ),
        paper_only=_bool_from_payload(f"{label}.paper_only", payload["paper_only"]),
        report_only=_bool_from_payload(f"{label}.report_only", payload["report_only"]),
        readonly=_bool_from_payload(f"{label}.readonly", payload["readonly"]),
    )


def _reason_count_from_payload(
    value: object,
    *,
    index: int,
) -> ResearchStrategyDomainTeamMemoryAlphaDecayReasonCount:
    label = f"reason_counts[{index}]"
    payload = _mapping_from_payload(label, value)
    _require_exact_payload_schema(
        "reason_count",
        payload,
        ResearchStrategyDomainTeamMemoryAlphaDecayReasonCount,
    )
    return ResearchStrategyDomainTeamMemoryAlphaDecayReasonCount(
        reason_code=_string_from_payload(
            f"{label}.reason_code",
            payload["reason_code"],
        ),
        count=_decimal_from_payload(f"{label}.count", payload["count"]),
        row_ratio=_decimal_from_payload(f"{label}.row_ratio", payload["row_ratio"]),
        paper_only=_bool_from_payload(f"{label}.paper_only", payload["paper_only"]),
        report_only=_bool_from_payload(f"{label}.report_only", payload["report_only"]),
        readonly=_bool_from_payload(f"{label}.readonly", payload["readonly"]),
    )


def _require_exact_payload_schema(
    label: str,
    payload: dict[str, Any],
    dataclass_type: type[object],
) -> None:
    if set(payload) != {field.name for field in fields(dataclass_type)}:
        raise ValueError(f"{label} must use canonical {label} payload schema")


def _mapping_from_payload(field_name: str, value: object) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError(f"{field_name} must be a JSON object")
    return value


def _payload_list(field_name: str, value: object) -> list[Any]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a JSON array")
    return value


def _string_tuple_from_payload(field_name: str, value: object) -> tuple[str, ...]:
    return tuple(
        _string_from_payload(f"{field_name}[{index}]", item)
        for index, item in enumerate(_payload_list(field_name, value))
    )


def _string_from_payload(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _bool_from_payload(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _decimal_from_payload(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        raw = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    if not raw.is_finite() or raw.is_signed() and raw.is_zero():
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    normalized = _quantize(raw)
    if _decimal_payload(normalized) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _datetime_from_payload(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a JSON datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a datetime string") from exc
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return normalized


def _copy_json_object(value: dict[str, Any]) -> dict[str, Any]:
    copied = _copy_json_value("payload", value)
    if type(copied) is not dict:
        raise ValueError("payload must be a JSON object")
    return copied


def _copy_json_value(field_name: str, value: object) -> Any:
    if value is None or type(value) in (str, bool):
        return value
    if type(value) is dict:
        copied: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            copied[key] = _copy_json_value(f"{field_name}.{key}", item)
        return copied
    if type(value) is list:
        return [
            _copy_json_value(f"{field_name}[{index}]", item)
            for index, item in enumerate(value)
        ]
    if type(value) in (int, float, Decimal):
        raise ValueError("public payload numeric values must be strings")
    raise ValueError(f"{field_name} must contain JSON values")


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


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be present")
    _require_digest("derived_validation_digest", digest)
    if digest != _payload_digest(payload):
        raise ValueError("derived_validation_digest must match report payload")


def _payload_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    try:
        encoded = json.dumps(
            unsigned,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("payload must contain canonical JSON values") from exc
    return sha256(encoded.encode("utf-8")).hexdigest()


def _alpha_decay_ratio(baseline_alpha_score: Decimal, current_alpha_score: Decimal) -> Decimal:
    if baseline_alpha_score <= ZERO:
        return ZERO
    decay = _ratio_decimal(
        _max_decimal((ZERO, _subtract_decimal(baseline_alpha_score, current_alpha_score))),
        baseline_alpha_score,
    )
    if decay > ONE:
        return ONE
    return decay


def _signal_freshness_score(age_seconds: Decimal, max_watch_age_seconds: Decimal) -> Decimal:
    if age_seconds >= max_watch_age_seconds:
        return ZERO
    return _subtract_decimal(ONE, _ratio_decimal(age_seconds, max_watch_age_seconds))


def _memory_alpha_decay_score(
    *,
    alpha_retention_score: Decimal,
    memory_reuse_score: Decimal,
    calibration_memory_score: Decimal,
    evidence_memory_score: Decimal,
    signal_freshness_score: Decimal,
    stale_memory_relief_score: Decimal,
    config: ResearchStrategyDomainTeamMemoryAlphaDecayConfig,
) -> Decimal:
    return _sum_decimal(
        (
            _multiply_decimal(alpha_retention_score, config.alpha_retention_weight),
            _multiply_decimal(memory_reuse_score, config.memory_reuse_weight),
            _multiply_decimal(
                calibration_memory_score,
                config.calibration_memory_weight,
            ),
            _multiply_decimal(evidence_memory_score, config.evidence_memory_weight),
            _multiply_decimal(signal_freshness_score, config.signal_freshness_weight),
            _multiply_decimal(stale_memory_relief_score, config.stale_memory_relief_weight),
        ),
    )


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    with localcontext(DECIMAL_CONTEXT):
        seconds = (
            Decimal(delta.days) * Decimal(86400)
            + Decimal(delta.seconds)
            + Decimal(delta.microseconds) / Decimal(1000000)
        )
        return _quantize(seconds)


def _count_decimal(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _ratio_decimal(_sum_decimal(values), _count_decimal(len(values)))


def _min_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return min(values)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    for value in values:
        total = _add_decimal(total, value)
    return total


def _add_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (left + right).quantize(DECIMAL_QUANTUM)


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (left - right).quantize(DECIMAL_QUANTUM)


def _multiply_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (left * right).quantize(DECIMAL_QUANTUM)


def _ratio_decimal(left: Decimal, right: Decimal) -> Decimal:
    if right == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (left / right).quantize(DECIMAL_QUANTUM)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(DECIMAL_QUANTUM)
    if normalized == ZERO:
        return ZERO
    return normalized


def _decimal_payload(value: Decimal) -> str:
    return format(_quantize(value), "f")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not be signed zero")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_decimal(field_name, value)
    if raw < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    normalized = _quantize(raw)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_decimal(field_name, value)
    if raw <= ZERO:
        raise ValueError(f"{field_name} must be > 0.000000")
    normalized = _quantize(raw)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be > 0.000000")
    return normalized


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_decimal(field_name, value)
    if raw < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if raw != raw.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    normalized = _quantize(raw)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be > 0.000000")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_decimal(field_name, value)
    if raw < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if raw > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    normalized = _quantize(raw)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if normalized > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    return normalized


def _require_floor_pair(
    pass_name: str,
    pass_value: Decimal,
    watch_name: str,
    watch_value: Decimal,
) -> None:
    if watch_value > pass_value:
        raise ValueError(f"{watch_name} must not exceed pass")


def _require_ceiling_pair(
    pass_name: str,
    pass_value: Decimal,
    watch_name: str,
    watch_value: Decimal,
) -> None:
    if pass_value > watch_value:
        raise ValueError(f"{pass_name} must not exceed watch")


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")
    _require_safe_public_text(field_name, value)
    return value


def _require_private_ref(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")
    return value


def _require_digest_ref(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 71 or not value.startswith("sha256:"):
        raise ValueError(f"{field_name} must be a sha256 digest reference")
    _require_digest(field_name, value.removeprefix("sha256:"))
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed:
        raise ValueError(f"{field_name} must be one of {', '.join(allowed)}")
    return value


def _normalize_reason_codes(
    reason_codes: tuple[str, ...],
    allowed: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not allow_empty and not reason_codes:
        raise ValueError("reason_codes must not be empty")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_member("reason_code", reason_code, allowed)
        _require_safe_public_text("reason_code", reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(sorted(normalized, key=_reason_sort_key))


def _reason_sort_key(reason_code: str) -> tuple[int, str]:
    if reason_code in COUNT_REASON_CODE_SEQUENCE:
        return (COUNT_REASON_CODE_SEQUENCE.index(reason_code), reason_code)
    if reason_code in REPORT_REASON_CODE_SEQUENCE:
        return (REPORT_REASON_CODE_SEQUENCE.index(reason_code), reason_code)
    return (len(COUNT_REASON_CODE_SEQUENCE) + len(REPORT_REASON_CODE_SEQUENCE), reason_code)


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    _reject_unsafe_public_keys(label, payload)
    _reject_unsafe_public_values(label, payload)


def _reject_unsafe_public_keys(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_keys(label, _public_dataclass_dict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _require_safe_public_text(f"{label} key", key)
            _reject_unsafe_public_keys(label, item)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_public_keys(label, item)


def _reject_unsafe_public_values(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_values(label, _public_dataclass_dict(value))
        return
    if type(value) is str:
        _require_safe_public_text(label, value)
        return
    if isinstance(value, dict):
        for item in value.values():
            _reject_unsafe_public_values(label, item)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_public_values(label, item)


def _public_dataclass_dict(value: object) -> dict[str, object]:
    return {field.name: getattr(value, field.name) for field in fields(value)}


def _require_safe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} must not contain sensitive content")


def _reject_raw_numeric_payload_values(value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise ValueError("public payload numeric values must be strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_raw_numeric_payload_values(item)
    elif isinstance(value, list):
        for item in value:
            _reject_raw_numeric_payload_values(item)


def _digest_ref(value: str) -> str:
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()}"
