"""Report-only event cluster resolution dependency pressure snapshot."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Decimal
import hashlib
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


CONFIG_VERSION = "research_event_cluster_resolution_dependency_pressure_report_v1"
DECIMAL_QUANTUM = Decimal("0.0001")
ZERO = Decimal("0")
ONE = Decimal("1")

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
RESEARCH_EVENT_CLUSTER_RESOLUTION_DEPENDENCY_PRESSURE_STATUSES = (
    STATUS_PASS,
    STATUS_WATCH,
    STATUS_BLOCK,
)

REASON_UNRESOLVED_DEPENDENCY_PRESSURE = "unresolved_dependency_pressure"
REASON_UPSTREAM_BLOCKER_PRESSURE = "upstream_blocker_pressure"
REASON_STALE_DEPENDENCY_PRESSURE = "stale_dependency_pressure"
REASON_CONFLICT_DEPENDENCY_PRESSURE = "conflict_dependency_pressure"
REASON_DEPENDENCY_COVERAGE_GAP = "dependency_coverage_gap"
REASON_TIMING_BUFFER_PRESSURE = "timing_buffer_pressure"
REASON_REVIEW_ACKNOWLEDGEMENT_MISSING = "review_acknowledgement_missing"
REASON_DEPENDENCY_PRESSURE_ELEVATED = "dependency_pressure_elevated"

UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "auth",
        "candidate",
        "database",
        "dsn",
        "http",
        "live",
        "market",
        "network",
        "order",
        "question",
        "slug",
        "source",
        "table",
        "text",
        "token",
        "trade",
        "url",
        "wallet",
    ),
)

REPORT_DECIMAL_PAYLOAD_FIELDS = (
    "row_count",
    "pass_count",
    "watch_count",
    "block_count",
    "total_event_count",
    "total_dependent_resolution_count",
    "total_unresolved_dependency_count",
    "average_dependency_pressure_score",
    "highest_dependency_pressure_score",
    "weakest_dependency_coverage_score",
)
ROW_DECIMAL_PAYLOAD_FIELDS = (
    "event_count",
    "dependent_resolution_count",
    "unresolved_dependency_count",
    "upstream_blocker_count",
    "stale_dependency_count",
    "conflict_dependency_count",
    "dependency_density_score",
    "unresolved_dependency_ratio",
    "blocker_pressure_score",
    "stale_dependency_ratio",
    "conflict_dependency_ratio",
    "dependency_coverage_score",
    "longest_dependency_age_hours",
    "minimum_expected_resolution_buffer_hours",
    "timing_buffer_pressure_score",
    "dependency_pressure_score",
)
REPORT_PAYLOAD_KEYS = (
    "generated_at",
    "config_version",
    *REPORT_DECIMAL_PAYLOAD_FIELDS,
    "status",
    "rows",
    "reason_code_counts",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_PAYLOAD_KEYS = (
    "cluster_digest",
    "observed_at",
    *ROW_DECIMAL_PAYLOAD_FIELDS[:6],
    "dependency_density_score",
    "unresolved_dependency_ratio",
    "blocker_pressure_score",
    "stale_dependency_ratio",
    "conflict_dependency_ratio",
    "dependency_coverage_score",
    "longest_dependency_age_hours",
    "minimum_expected_resolution_buffer_hours",
    "timing_buffer_pressure_score",
    "review_acknowledged",
    "dependency_pressure_score",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class ResearchEventClusterResolutionDependencyPressureConfig:
    config_version: str = CONFIG_VERSION
    unresolved_dependency_pressure_weight: Decimal = Decimal("0.2500")
    upstream_blocker_pressure_weight: Decimal = Decimal("0.2000")
    stale_dependency_pressure_weight: Decimal = Decimal("0.0500")
    conflict_dependency_pressure_weight: Decimal = Decimal("0.2000")
    dependency_coverage_gap_weight: Decimal = Decimal("0.1500")
    timing_buffer_pressure_weight: Decimal = Decimal("0.1000")
    review_acknowledgement_gap_weight: Decimal = Decimal("0.0500")
    watch_pressure_threshold: Decimal = Decimal("0.2500")
    block_pressure_threshold: Decimal = Decimal("0.6000")
    watch_unresolved_dependency_ratio: Decimal = Decimal("0.5000")
    block_unresolved_dependency_ratio: Decimal = Decimal("0.7500")
    watch_blocker_pressure_score: Decimal = Decimal("0.3000")
    block_blocker_pressure_score: Decimal = Decimal("0.5000")
    watch_stale_dependency_ratio: Decimal = Decimal("0.5000")
    block_stale_dependency_ratio: Decimal = Decimal("0.7500")
    watch_conflict_dependency_ratio: Decimal = Decimal("0.3000")
    block_conflict_dependency_ratio: Decimal = Decimal("0.5000")
    watch_dependency_coverage_score: Decimal = Decimal("0.8000")
    block_dependency_coverage_score: Decimal = Decimal("0.5000")
    watch_timing_buffer_pressure_score: Decimal = Decimal("0.5000")
    block_timing_buffer_pressure_score: Decimal = Decimal("0.9000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventClusterResolutionDependencyPressureConfig:
            raise TypeError(
                "ResearchEventClusterResolutionDependencyPressureConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchEventClusterResolutionDependencyPressureConfig,
        )
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "unresolved_dependency_pressure_weight",
            "upstream_blocker_pressure_weight",
            "stale_dependency_pressure_weight",
            "conflict_dependency_pressure_weight",
            "dependency_coverage_gap_weight",
            "timing_buffer_pressure_weight",
            "review_acknowledgement_gap_weight",
            "watch_pressure_threshold",
            "block_pressure_threshold",
            "watch_unresolved_dependency_ratio",
            "block_unresolved_dependency_ratio",
            "watch_blocker_pressure_score",
            "block_blocker_pressure_score",
            "watch_stale_dependency_ratio",
            "block_stale_dependency_ratio",
            "watch_conflict_dependency_ratio",
            "block_conflict_dependency_ratio",
            "watch_dependency_coverage_score",
            "block_dependency_coverage_score",
            "watch_timing_buffer_pressure_score",
            "block_timing_buffer_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        require_paper_only_flags("cluster dependency pressure config", self)


@dataclass(frozen=True)
class ResearchEventClusterResolutionDependencyPressureInput:
    cluster_reference: str
    observed_at: datetime
    event_count: Decimal
    dependent_resolution_count: Decimal
    unresolved_dependency_count: Decimal
    upstream_blocker_count: Decimal
    stale_dependency_count: Decimal
    conflict_dependency_count: Decimal
    dependency_coverage_score: Decimal
    longest_dependency_age_hours: Decimal
    minimum_expected_resolution_buffer_hours: Decimal
    review_acknowledged: bool
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventClusterResolutionDependencyPressureInput:
            raise TypeError(
                "ResearchEventClusterResolutionDependencyPressureInput "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "input",
            self,
            ResearchEventClusterResolutionDependencyPressureInput,
        )
        _require_canonical_string("cluster_reference", self.cluster_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "event_count",
            "dependent_resolution_count",
            "unresolved_dependency_count",
            "upstream_blocker_count",
            "stale_dependency_count",
            "conflict_dependency_count",
            "longest_dependency_age_hours",
            "minimum_expected_resolution_buffer_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "dependency_coverage_score",
            _normalize_probability(
                "dependency_coverage_score",
                self.dependency_coverage_score,
            ),
        )
        if type(self.review_acknowledged) is not bool:
            raise ValueError("review_acknowledged must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=True),
        )
        _validate_input(self)
        require_paper_only_flags("cluster dependency pressure input", self)


@dataclass(frozen=True)
class ResearchEventClusterResolutionDependencyPressureRow:
    cluster_digest: str
    observed_at: datetime
    event_count: Decimal
    dependent_resolution_count: Decimal
    unresolved_dependency_count: Decimal
    upstream_blocker_count: Decimal
    stale_dependency_count: Decimal
    conflict_dependency_count: Decimal
    dependency_density_score: Decimal
    unresolved_dependency_ratio: Decimal
    blocker_pressure_score: Decimal
    stale_dependency_ratio: Decimal
    conflict_dependency_ratio: Decimal
    dependency_coverage_score: Decimal
    longest_dependency_age_hours: Decimal
    minimum_expected_resolution_buffer_hours: Decimal
    timing_buffer_pressure_score: Decimal
    review_acknowledged: bool
    dependency_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventClusterResolutionDependencyPressureRow:
            raise TypeError(
                "ResearchEventClusterResolutionDependencyPressureRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchEventClusterResolutionDependencyPressureRow)
        _require_sha256_digest("cluster_digest", self.cluster_digest)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "event_count",
            "dependent_resolution_count",
            "unresolved_dependency_count",
            "upstream_blocker_count",
            "stale_dependency_count",
            "conflict_dependency_count",
            "longest_dependency_age_hours",
            "minimum_expected_resolution_buffer_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "dependency_density_score",
            "unresolved_dependency_ratio",
            "blocker_pressure_score",
            "stale_dependency_ratio",
            "conflict_dependency_ratio",
            "dependency_coverage_score",
            "timing_buffer_pressure_score",
            "dependency_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if type(self.review_acknowledged) is not bool:
            raise ValueError("review_acknowledged must be a bool")
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row(self)
        require_paper_only_flags("cluster dependency pressure row", self)


@dataclass(frozen=True)
class ResearchEventClusterResolutionDependencyPressureReport:
    generated_at: datetime
    config_version: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    total_event_count: Decimal
    total_dependent_resolution_count: Decimal
    total_unresolved_dependency_count: Decimal
    average_dependency_pressure_score: Decimal
    highest_dependency_pressure_score: Decimal
    weakest_dependency_coverage_score: Decimal
    status: str
    rows: tuple[ResearchEventClusterResolutionDependencyPressureRow, ...]
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventClusterResolutionDependencyPressureReport:
            raise TypeError(
                "ResearchEventClusterResolutionDependencyPressureReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "report",
            self,
            ResearchEventClusterResolutionDependencyPressureReport,
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "total_event_count",
            "total_dependent_resolution_count",
            "total_unresolved_dependency_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_dependency_pressure_score",
            "highest_dependency_pressure_score",
            "weakest_dependency_coverage_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_validation_digest(self),
            )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report(self)
        require_paper_only_flags("cluster dependency pressure report", self)
        _require_report_validation_digest(self)
        _reject_unsafe_public_payload(
            "cluster dependency pressure report",
            _payload_value(asdict(self)),
        )


def build_research_event_cluster_resolution_dependency_pressure_report(
    clusters: tuple[ResearchEventClusterResolutionDependencyPressureInput, ...],
    *,
    generated_at: datetime,
    config: ResearchEventClusterResolutionDependencyPressureConfig,
) -> ResearchEventClusterResolutionDependencyPressureReport:
    """Build a deterministic, report-only dependency pressure snapshot."""

    if type(clusters) is not tuple:
        raise ValueError("clusters must be a tuple")
    if type(config) is not ResearchEventClusterResolutionDependencyPressureConfig:
        raise ValueError(
            "config must be a ResearchEventClusterResolutionDependencyPressureConfig",
        )
    normalized_generated_at = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (
                _build_row(cluster=cluster, config=config)
                for cluster in _normalize_inputs(clusters, normalized_generated_at)
            ),
            key=lambda row: row.cluster_digest,
        ),
    )
    return ResearchEventClusterResolutionDependencyPressureReport(
        generated_at=normalized_generated_at,
        config_version=config.config_version,
        row_count=Decimal(len(rows)),
        pass_count=_count_status(rows, STATUS_PASS),
        watch_count=_count_status(rows, STATUS_WATCH),
        block_count=_count_status(rows, STATUS_BLOCK),
        total_event_count=_sum_decimal(row.event_count for row in rows),
        total_dependent_resolution_count=_sum_decimal(
            row.dependent_resolution_count for row in rows
        ),
        total_unresolved_dependency_count=_sum_decimal(
            row.unresolved_dependency_count for row in rows
        ),
        average_dependency_pressure_score=_average(
            row.dependency_pressure_score for row in rows
        ),
        highest_dependency_pressure_score=_maximum_or_zero(
            row.dependency_pressure_score for row in rows
        ),
        weakest_dependency_coverage_score=_minimum_or_zero(
            row.dependency_coverage_score for row in rows
        ),
        status=_report_status(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows),
    )


def research_event_cluster_resolution_dependency_pressure_payload(
    report: ResearchEventClusterResolutionDependencyPressureReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchEventClusterResolutionDependencyPressureReport:
        require_paper_only_flags("cluster dependency pressure report", report)
        _require_report_validation_digest(report)
        payload = _payload_value(asdict(report))
    elif type(report) is dict:
        payload = report
    else:
        raise ValueError(
            "report must be a ResearchEventClusterResolutionDependencyPressureReport or dict",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _validate_public_payload(payload)
    return payload


def validate_research_event_cluster_resolution_dependency_pressure_digest(
    report: ResearchEventClusterResolutionDependencyPressureReport,
) -> None:
    if type(report) is not ResearchEventClusterResolutionDependencyPressureReport:
        raise ValueError(
            "report must be a ResearchEventClusterResolutionDependencyPressureReport",
        )
    _require_report_validation_digest(report)


def research_event_cluster_resolution_dependency_pressure_digest(
    report: ResearchEventClusterResolutionDependencyPressureReport,
) -> str:
    if type(report) is not ResearchEventClusterResolutionDependencyPressureReport:
        raise ValueError(
            "report must be a ResearchEventClusterResolutionDependencyPressureReport",
        )
    return _report_validation_digest(report)


def _normalize_inputs(
    clusters: tuple[ResearchEventClusterResolutionDependencyPressureInput, ...],
    generated_at: datetime,
) -> tuple[ResearchEventClusterResolutionDependencyPressureInput, ...]:
    normalized = tuple(clusters)
    seen: set[str] = set()
    for cluster in normalized:
        if type(cluster) is not ResearchEventClusterResolutionDependencyPressureInput:
            raise ValueError(
                "clusters must contain ResearchEventClusterResolutionDependencyPressureInput "
                "values",
            )
        if cluster.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        digest = _cluster_digest(cluster.cluster_reference)
        if digest in seen:
            raise ValueError("duplicate cluster references are not allowed")
        seen.add(digest)
        require_paper_only_flags("cluster dependency pressure input", cluster)
    return normalized


def _build_row(
    *,
    cluster: ResearchEventClusterResolutionDependencyPressureInput,
    config: ResearchEventClusterResolutionDependencyPressureConfig,
) -> ResearchEventClusterResolutionDependencyPressureRow:
    dependency_density_score = _capped_ratio(
        cluster.dependent_resolution_count,
        cluster.event_count,
    )
    unresolved_dependency_ratio = _dependency_ratio(
        cluster.unresolved_dependency_count,
        cluster.dependent_resolution_count,
    )
    blocker_pressure_score = _dependency_ratio(
        cluster.upstream_blocker_count,
        cluster.dependent_resolution_count,
    )
    stale_dependency_ratio = _dependency_ratio(
        cluster.stale_dependency_count,
        cluster.dependent_resolution_count,
    )
    conflict_dependency_ratio = _dependency_ratio(
        cluster.conflict_dependency_count,
        cluster.dependent_resolution_count,
    )
    timing_buffer_pressure_score = _capped_ratio(
        cluster.longest_dependency_age_hours,
        cluster.minimum_expected_resolution_buffer_hours,
    )
    dependency_pressure_score = _dependency_pressure_score(
        unresolved_dependency_ratio=unresolved_dependency_ratio,
        blocker_pressure_score=blocker_pressure_score,
        stale_dependency_ratio=stale_dependency_ratio,
        conflict_dependency_ratio=conflict_dependency_ratio,
        dependency_coverage_score=cluster.dependency_coverage_score,
        timing_buffer_pressure_score=timing_buffer_pressure_score,
        review_acknowledged=cluster.review_acknowledged,
        config=config,
    )
    status = _row_status(
        unresolved_dependency_ratio=unresolved_dependency_ratio,
        blocker_pressure_score=blocker_pressure_score,
        stale_dependency_ratio=stale_dependency_ratio,
        conflict_dependency_ratio=conflict_dependency_ratio,
        dependency_coverage_score=cluster.dependency_coverage_score,
        timing_buffer_pressure_score=timing_buffer_pressure_score,
        review_acknowledged=cluster.review_acknowledged,
        dependency_pressure_score=dependency_pressure_score,
        config=config,
    )
    return ResearchEventClusterResolutionDependencyPressureRow(
        cluster_digest=_cluster_digest(cluster.cluster_reference),
        observed_at=cluster.observed_at,
        event_count=cluster.event_count,
        dependent_resolution_count=cluster.dependent_resolution_count,
        unresolved_dependency_count=cluster.unresolved_dependency_count,
        upstream_blocker_count=cluster.upstream_blocker_count,
        stale_dependency_count=cluster.stale_dependency_count,
        conflict_dependency_count=cluster.conflict_dependency_count,
        dependency_density_score=dependency_density_score,
        unresolved_dependency_ratio=unresolved_dependency_ratio,
        blocker_pressure_score=blocker_pressure_score,
        stale_dependency_ratio=stale_dependency_ratio,
        conflict_dependency_ratio=conflict_dependency_ratio,
        dependency_coverage_score=cluster.dependency_coverage_score,
        longest_dependency_age_hours=cluster.longest_dependency_age_hours,
        minimum_expected_resolution_buffer_hours=(
            cluster.minimum_expected_resolution_buffer_hours
        ),
        timing_buffer_pressure_score=timing_buffer_pressure_score,
        review_acknowledged=cluster.review_acknowledged,
        dependency_pressure_score=dependency_pressure_score,
        status=status,
        reason_codes=_row_reason_codes(
            cluster.reason_codes,
            status=status,
            unresolved_dependency_ratio=unresolved_dependency_ratio,
            blocker_pressure_score=blocker_pressure_score,
            stale_dependency_ratio=stale_dependency_ratio,
            conflict_dependency_ratio=conflict_dependency_ratio,
            dependency_coverage_score=cluster.dependency_coverage_score,
            timing_buffer_pressure_score=timing_buffer_pressure_score,
            review_acknowledged=cluster.review_acknowledged,
            dependency_pressure_score=dependency_pressure_score,
            config=config,
        ),
    )


def _dependency_pressure_score(
    *,
    unresolved_dependency_ratio: Decimal,
    blocker_pressure_score: Decimal,
    stale_dependency_ratio: Decimal,
    conflict_dependency_ratio: Decimal,
    dependency_coverage_score: Decimal,
    timing_buffer_pressure_score: Decimal,
    review_acknowledged: bool,
    config: ResearchEventClusterResolutionDependencyPressureConfig,
) -> Decimal:
    acknowledgement_gap = ZERO if review_acknowledged else ONE
    return _quantize(
        unresolved_dependency_ratio * config.unresolved_dependency_pressure_weight
        + blocker_pressure_score * config.upstream_blocker_pressure_weight
        + stale_dependency_ratio * config.stale_dependency_pressure_weight
        + conflict_dependency_ratio * config.conflict_dependency_pressure_weight
        + (ONE - dependency_coverage_score) * config.dependency_coverage_gap_weight
        + timing_buffer_pressure_score * config.timing_buffer_pressure_weight
        + acknowledgement_gap * config.review_acknowledgement_gap_weight,
    )


def _row_status(
    *,
    unresolved_dependency_ratio: Decimal,
    blocker_pressure_score: Decimal,
    stale_dependency_ratio: Decimal,
    conflict_dependency_ratio: Decimal,
    dependency_coverage_score: Decimal,
    timing_buffer_pressure_score: Decimal,
    review_acknowledged: bool,
    dependency_pressure_score: Decimal,
    config: ResearchEventClusterResolutionDependencyPressureConfig,
) -> str:
    if (
        dependency_pressure_score >= config.block_pressure_threshold
        or unresolved_dependency_ratio >= config.block_unresolved_dependency_ratio
        or blocker_pressure_score >= config.block_blocker_pressure_score
        or stale_dependency_ratio >= config.block_stale_dependency_ratio
        or conflict_dependency_ratio >= config.block_conflict_dependency_ratio
        or dependency_coverage_score <= config.block_dependency_coverage_score
        or timing_buffer_pressure_score >= config.block_timing_buffer_pressure_score
        or not review_acknowledged
    ):
        return STATUS_BLOCK
    if (
        dependency_pressure_score >= config.watch_pressure_threshold
        or unresolved_dependency_ratio >= config.watch_unresolved_dependency_ratio
        or blocker_pressure_score >= config.watch_blocker_pressure_score
        or stale_dependency_ratio >= config.watch_stale_dependency_ratio
        or conflict_dependency_ratio >= config.watch_conflict_dependency_ratio
        or dependency_coverage_score < config.watch_dependency_coverage_score
        or timing_buffer_pressure_score >= config.watch_timing_buffer_pressure_score
    ):
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    existing_reason_codes: tuple[str, ...],
    *,
    status: str,
    unresolved_dependency_ratio: Decimal,
    blocker_pressure_score: Decimal,
    stale_dependency_ratio: Decimal,
    conflict_dependency_ratio: Decimal,
    dependency_coverage_score: Decimal,
    timing_buffer_pressure_score: Decimal,
    review_acknowledged: bool,
    dependency_pressure_score: Decimal,
    config: ResearchEventClusterResolutionDependencyPressureConfig,
) -> tuple[str, ...]:
    codes = set(existing_reason_codes)
    codes.add(status)
    if unresolved_dependency_ratio >= config.watch_unresolved_dependency_ratio:
        codes.add(REASON_UNRESOLVED_DEPENDENCY_PRESSURE)
    if blocker_pressure_score >= config.watch_blocker_pressure_score:
        codes.add(REASON_UPSTREAM_BLOCKER_PRESSURE)
    if stale_dependency_ratio >= config.watch_stale_dependency_ratio:
        codes.add(REASON_STALE_DEPENDENCY_PRESSURE)
    if conflict_dependency_ratio >= config.watch_conflict_dependency_ratio:
        codes.add(REASON_CONFLICT_DEPENDENCY_PRESSURE)
    if dependency_coverage_score < config.watch_dependency_coverage_score:
        codes.add(REASON_DEPENDENCY_COVERAGE_GAP)
    if timing_buffer_pressure_score >= config.watch_timing_buffer_pressure_score:
        codes.add(REASON_TIMING_BUFFER_PRESSURE)
    if not review_acknowledged:
        codes.add(REASON_REVIEW_ACKNOWLEDGEMENT_MISSING)
    if dependency_pressure_score >= config.watch_pressure_threshold:
        codes.add(REASON_DEPENDENCY_PRESSURE_ELEVATED)
    return _normalize_reason_codes(tuple(sorted(codes)))


def _dependency_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO.quantize(DECIMAL_QUANTUM)
    return _capped_ratio(numerator, denominator)


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    ratio = _quantize(numerator / denominator)
    if ratio > ONE:
        return ONE.quantize(DECIMAL_QUANTUM)
    return ratio


def _count_status(
    rows: tuple[ResearchEventClusterResolutionDependencyPressureRow, ...],
    status: str,
) -> Decimal:
    return Decimal(sum(ONE for row in rows if row.status == status)).quantize(
        DECIMAL_QUANTUM,
    )


def _report_status(
    rows: tuple[ResearchEventClusterResolutionDependencyPressureRow, ...],
) -> str:
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _reason_code_counts(
    rows: tuple[ResearchEventClusterResolutionDependencyPressureRow, ...],
) -> tuple[tuple[str, Decimal], ...]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        (reason_code, Decimal(count).quantize(DECIMAL_QUANTUM))
        for reason_code, count in sorted(counter.items())
    )


def _average(values: Any) -> Decimal:
    normalized_values = tuple(values)
    if not normalized_values:
        return ZERO.quantize(DECIMAL_QUANTUM)
    return _quantize(sum(normalized_values, ZERO) / Decimal(len(normalized_values)))


def _maximum_or_zero(values: Any) -> Decimal:
    normalized_values = tuple(values)
    if not normalized_values:
        return ZERO.quantize(DECIMAL_QUANTUM)
    return max(normalized_values).quantize(DECIMAL_QUANTUM)


def _minimum_or_zero(values: Any) -> Decimal:
    normalized_values = tuple(values)
    if not normalized_values:
        return ZERO.quantize(DECIMAL_QUANTUM)
    return min(normalized_values).quantize(DECIMAL_QUANTUM)


def _sum_decimal(values: Any) -> Decimal:
    return sum(tuple(values), ZERO).quantize(DECIMAL_QUANTUM)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(DECIMAL_QUANTUM, rounding=ROUND_HALF_EVEN)


def _cluster_digest(cluster_reference: str) -> str:
    return hashlib.sha256(cluster_reference.encode("utf-8")).hexdigest()


def _report_validation_digest(
    report: ResearchEventClusterResolutionDependencyPressureReport,
) -> str:
    payload = _payload_value(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return _payload_validation_digest(payload)


def _payload_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = {
        key: value for key, value in payload.items() if key != "derived_validation_digest"
    }
    encoded = json.dumps(digest_payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _require_report_validation_digest(
    report: ResearchEventClusterResolutionDependencyPressureReport,
) -> None:
    expected_digest = _report_validation_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report payload")


def _validate_public_payload(payload: dict[str, Any]) -> None:
    _reject_unsafe_public_payload("payload", payload)
    _reject_unknown_payload_keys("report payload", payload, REPORT_PAYLOAD_KEYS)
    _require_canonical_string("generated_at", payload["generated_at"])
    _require_canonical_string("config_version", payload["config_version"])
    if payload["config_version"] != CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")
    for field_name in REPORT_DECIMAL_PAYLOAD_FIELDS:
        _require_decimal_string(field_name, payload[field_name])
    _require_status("status", payload["status"])
    if type(payload["rows"]) is not list:
        raise ValueError("rows must be a list")
    for row in payload["rows"]:
        _validate_public_row_payload(row)
    _validate_public_reason_code_counts(payload["reason_code_counts"])
    digest = payload["derived_validation_digest"]
    _require_sha256_digest("derived_validation_digest", digest)
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    if digest != _payload_validation_digest(payload):
        raise ValueError("derived_validation_digest must match report payload")


def _validate_public_row_payload(value: object) -> None:
    if type(value) is not dict:
        raise ValueError("rows must contain JSON objects")
    _reject_unknown_payload_keys("row payload", value, ROW_PAYLOAD_KEYS)
    _require_sha256_digest("cluster_digest", value["cluster_digest"])
    _require_canonical_string("observed_at", value["observed_at"])
    for field_name in ROW_DECIMAL_PAYLOAD_FIELDS:
        _require_decimal_string(field_name, value[field_name])
    if type(value["review_acknowledged"]) is not bool:
        raise ValueError("review_acknowledged must be a bool")
    _require_status("status", value["status"])
    _normalize_reason_codes(value["reason_codes"])
    for field_name in ("paper_only", "report_only", "readonly"):
        if value[field_name] is not True:
            raise ValueError(f"{field_name} must be True")


def _validate_public_reason_code_counts(value: object) -> None:
    if type(value) is not list:
        raise ValueError("reason_code_counts must be a list")
    previous: str | None = None
    for item in value:
        if type(item) is not list or len(item) != 2:
            raise ValueError("reason_code_counts must contain pairs")
        reason_code = item[0]
        count_value = _require_decimal_string("reason_code_count", item[1])
        _require_safe_reason_code(reason_code)
        if count_value < ZERO:
            raise ValueError("reason_code_count must be nonnegative")
        if previous is not None and reason_code <= previous:
            raise ValueError("reason_code_counts must be deterministic")
        previous = reason_code


def _payload_value(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if isinstance(value, dict):
        return {key: _payload_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if type(value) is Decimal:
        return format(value.quantize(DECIMAL_QUANTUM), "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported payload value type: {type(value).__name__}")


def _validate_config(
    config: ResearchEventClusterResolutionDependencyPressureConfig,
) -> None:
    weights = (
        config.unresolved_dependency_pressure_weight
        + config.upstream_blocker_pressure_weight
        + config.stale_dependency_pressure_weight
        + config.conflict_dependency_pressure_weight
        + config.dependency_coverage_gap_weight
        + config.timing_buffer_pressure_weight
        + config.review_acknowledgement_gap_weight
    )
    if weights != ONE.quantize(DECIMAL_QUANTUM):
        raise ValueError("pressure weights must sum to 1.0000")
    if config.block_pressure_threshold <= config.watch_pressure_threshold:
        raise ValueError("block_pressure_threshold must exceed watch threshold")
    threshold_pairs = (
        (
            "unresolved_dependency_ratio",
            config.watch_unresolved_dependency_ratio,
            config.block_unresolved_dependency_ratio,
        ),
        (
            "blocker_pressure_score",
            config.watch_blocker_pressure_score,
            config.block_blocker_pressure_score,
        ),
        (
            "stale_dependency_ratio",
            config.watch_stale_dependency_ratio,
            config.block_stale_dependency_ratio,
        ),
        (
            "conflict_dependency_ratio",
            config.watch_conflict_dependency_ratio,
            config.block_conflict_dependency_ratio,
        ),
        (
            "timing_buffer_pressure_score",
            config.watch_timing_buffer_pressure_score,
            config.block_timing_buffer_pressure_score,
        ),
    )
    for label, watch_value, block_value in threshold_pairs:
        if block_value <= watch_value:
            raise ValueError(f"block {label} threshold must exceed watch threshold")
    if config.block_dependency_coverage_score >= config.watch_dependency_coverage_score:
        raise ValueError("block dependency coverage threshold must be below watch threshold")


def _validate_input(
    cluster: ResearchEventClusterResolutionDependencyPressureInput,
) -> None:
    if cluster.event_count <= ZERO:
        raise ValueError("event_count must be positive")
    if cluster.dependent_resolution_count > cluster.event_count:
        raise ValueError("dependent_resolution_count must not exceed event_count")
    for field_name in (
        "unresolved_dependency_count",
        "upstream_blocker_count",
        "stale_dependency_count",
        "conflict_dependency_count",
    ):
        if getattr(cluster, field_name) > cluster.dependent_resolution_count:
            raise ValueError(f"{field_name} must not exceed dependent_resolution_count")
    if cluster.minimum_expected_resolution_buffer_hours <= ZERO:
        raise ValueError("minimum_expected_resolution_buffer_hours must be positive")


def _validate_row(row: ResearchEventClusterResolutionDependencyPressureRow) -> None:
    if row.event_count <= ZERO:
        raise ValueError("event_count must be positive")
    if row.dependent_resolution_count > row.event_count:
        raise ValueError("dependent_resolution_count must not exceed event_count")
    for field_name in (
        "unresolved_dependency_count",
        "upstream_blocker_count",
        "stale_dependency_count",
        "conflict_dependency_count",
    ):
        if getattr(row, field_name) > row.dependent_resolution_count:
            raise ValueError(f"{field_name} must not exceed dependent_resolution_count")
    if row.minimum_expected_resolution_buffer_hours <= ZERO:
        raise ValueError("minimum_expected_resolution_buffer_hours must be positive")


def _validate_report(
    report: ResearchEventClusterResolutionDependencyPressureReport,
) -> None:
    rows = report.rows
    if report.row_count != Decimal(len(rows)).quantize(DECIMAL_QUANTUM):
        raise ValueError("row_count must equal rows length")
    expected_counts = {
        STATUS_PASS: report.pass_count,
        STATUS_WATCH: report.watch_count,
        STATUS_BLOCK: report.block_count,
    }
    for status, expected_count in expected_counts.items():
        if expected_count != _count_status(rows, status):
            raise ValueError(f"{status}_count must equal row status count")
    if report.total_event_count != _sum_decimal(row.event_count for row in rows):
        raise ValueError("total_event_count must equal row total")
    if report.total_dependent_resolution_count != _sum_decimal(
        row.dependent_resolution_count for row in rows
    ):
        raise ValueError("total_dependent_resolution_count must equal row total")
    if report.total_unresolved_dependency_count != _sum_decimal(
        row.unresolved_dependency_count for row in rows
    ):
        raise ValueError("total_unresolved_dependency_count must equal row total")
    if report.average_dependency_pressure_score != _average(
        row.dependency_pressure_score for row in rows
    ):
        raise ValueError("average_dependency_pressure_score must equal row average")
    if report.highest_dependency_pressure_score != _maximum_or_zero(
        row.dependency_pressure_score for row in rows
    ):
        raise ValueError("highest_dependency_pressure_score must equal row maximum")
    if report.weakest_dependency_coverage_score != _minimum_or_zero(
        row.dependency_coverage_score for row in rows
    ):
        raise ValueError("weakest_dependency_coverage_score must equal row minimum")
    if report.status != _report_status(rows):
        raise ValueError("status must reflect row statuses")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must equal row reason code counts")
    if rows != tuple(sorted(rows, key=lambda row: row.cluster_digest)):
        raise ValueError("rows must use deterministic sequence")


def _normalize_rows(
    rows: object,
) -> tuple[ResearchEventClusterResolutionDependencyPressureRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchEventClusterResolutionDependencyPressureRow:
            raise ValueError(
                "rows must contain ResearchEventClusterResolutionDependencyPressureRow "
                "values",
            )
        require_paper_only_flags("cluster dependency pressure row", row)
    return normalized


def _normalize_reason_code_counts(
    values: object,
) -> tuple[tuple[str, Decimal], ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized: list[tuple[str, Decimal]] = []
    previous: str | None = None
    for value in values:
        if type(value) is not tuple or len(value) != 2:
            raise ValueError("reason_code_counts must contain tuples")
        reason_code, count_value = value
        _require_safe_reason_code(reason_code)
        normalized_count = _normalize_nonnegative_decimal("reason_code_count", count_value)
        if previous is not None and reason_code <= previous:
            raise ValueError("reason_code_counts must be deterministic")
        previous = reason_code
        normalized.append((reason_code, normalized_count))
    return tuple(normalized)


def _normalize_reason_codes(
    values: object,
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(values)
    if not reason_codes and not allow_empty:
        raise ValueError("reason_codes must not be empty")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    for reason_code in reason_codes:
        _require_safe_reason_code(reason_code)
    if tuple(sorted(reason_codes)) != reason_codes:
        raise ValueError("reason_codes must be deterministic")
    return reason_codes


def _reject_unknown_payload_keys(
    label: str,
    payload: dict[str, Any],
    allowed_keys: tuple[str, ...],
) -> None:
    if tuple(payload.keys()) != allowed_keys:
        raise ValueError(f"{label} must use the public readonly schema")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public surface in {label}")


def _require_safe_reason_code(value: object) -> str:
    _require_canonical_string("reason_code", value)
    reason_code = str(value)
    if any(fragment in reason_code.lower() for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError("reason_code contains unsafe text")
    return reason_code


def _require_decimal_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must use Decimal-derived string values")
    decimal_value = Decimal(value)
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return decimal_value


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(decimal_value)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(decimal_value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in RESEARCH_EVENT_CLUSTER_RESOLUTION_DEPENDENCY_PRESSURE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exact")


__all__ = (
    "CONFIG_VERSION",
    "RESEARCH_EVENT_CLUSTER_RESOLUTION_DEPENDENCY_PRESSURE_STATUSES",
    "ResearchEventClusterResolutionDependencyPressureConfig",
    "ResearchEventClusterResolutionDependencyPressureInput",
    "ResearchEventClusterResolutionDependencyPressureReport",
    "ResearchEventClusterResolutionDependencyPressureRow",
    "build_research_event_cluster_resolution_dependency_pressure_report",
    "research_event_cluster_resolution_dependency_pressure_digest",
    "research_event_cluster_resolution_dependency_pressure_payload",
    "validate_research_event_cluster_resolution_dependency_pressure_digest",
)
