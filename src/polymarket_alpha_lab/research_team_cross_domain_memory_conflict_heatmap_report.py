"""Pure report-only cross-domain team memory conflict heatmap."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any, Iterable

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


__all__ = (
    "DEFAULT_RESEARCH_TEAM_CROSS_DOMAIN_MEMORY_CONFLICT_HEATMAP_CONFIG_VERSION",
    "PUBLIC_STATUSES",
    "ResearchTeamCrossDomainMemoryConflictCell",
    "ResearchTeamCrossDomainMemoryConflictHeatmapConfig",
    "ResearchTeamCrossDomainMemoryConflictHeatmapReport",
    "ResearchTeamCrossDomainMemoryConflictObservation",
    "ResearchTeamCrossDomainMemoryConflictReasonCodeCount",
    "build_research_team_cross_domain_memory_conflict_heatmap_report",
    "research_team_cross_domain_memory_conflict_heatmap_report_payload",
)


DEFAULT_RESEARCH_TEAM_CROSS_DOMAIN_MEMORY_CONFLICT_HEATMAP_CONFIG_VERSION = (
    "research-team-cross-domain-memory-conflict-heatmap-report-v0"
)

PUBLIC_STATUSES = ("pass", "watch", "block")
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
HEX_CHARS = frozenset("0123456789abcdef")
STATUS_WEIGHT = {
    "block": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}

EMPTY_REPORT_REASON_CODE = "cross_domain_memory_conflict_heatmap_empty"
PASS_CELL_REASON_CODE = "cross_domain_memory_conflict_clear"
BLOCK_REASON_CODES = (
    "memory_freshness_pressure_block",
    "memory_contradiction_pressure_block",
    "calibration_feedback_pressure_block",
    "unresolved_review_age_pressure_block",
)
WATCH_REASON_CODES = (
    "memory_freshness_pressure_watch",
    "memory_contradiction_pressure_watch",
    "calibration_feedback_pressure_watch",
    "unresolved_review_age_pressure_watch",
)
CELL_STATUS_REASON_CODES = (
    "cross_domain_memory_conflict_heatmap_block",
    "cross_domain_memory_conflict_heatmap_watch",
)
CELL_REASON_CODES = (
    CELL_STATUS_REASON_CODES
    + BLOCK_REASON_CODES
    + WATCH_REASON_CODES
    + (PASS_CELL_REASON_CODE,)
)
REPORT_REASON_PRIORITY = (
    "cross_domain_memory_conflict_heatmap_block",
    *BLOCK_REASON_CODES,
    *WATCH_REASON_CODES,
)
UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "source",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "trading",
        "live",
        "network",
        "database",
        "persist",
        "private_key",
        "private-key",
        "signing",
        "position",
        "buy",
        "sell",
        "sizing",
        "recommendation",
    ),
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchTeamCrossDomainMemoryConflictHeatmapConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_CROSS_DOMAIN_MEMORY_CONFLICT_HEATMAP_CONFIG_VERSION
    )
    watch_conflict_pressure_score: Decimal = Decimal("0.250000")
    block_conflict_pressure_score: Decimal = Decimal("0.700000")
    block_unresolved_review_age_hours: Decimal = Decimal("72.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamCrossDomainMemoryConflictHeatmapConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_CROSS_DOMAIN_MEMORY_CONFLICT_HEATMAP_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_conflict_pressure_score",
            "block_conflict_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "block_unresolved_review_age_hours",
            _require_positive_decimal(
                "block_unresolved_review_age_hours",
                self.block_unresolved_review_age_hours,
            ),
        )
        if self.block_conflict_pressure_score <= self.watch_conflict_pressure_score:
            raise ValueError(
                "block_conflict_pressure_score must exceed "
                "watch_conflict_pressure_score",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchTeamCrossDomainMemoryConflictObservation(_FinalPublicDataclass):
    domain_a: str
    domain_b: str
    memory_freshness_score: Decimal
    contradiction_score: Decimal
    calibration_feedback_score: Decimal
    unresolved_review_age_hours: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamCrossDomainMemoryConflictObservation,
            "observation",
        )
        _require_safe_label("domain_a", self.domain_a)
        _require_safe_label("domain_b", self.domain_b)
        if self.domain_a == self.domain_b:
            raise ValueError("domain pair must contain two distinct domains")
        for field_name in (
            "memory_freshness_score",
            "contradiction_score",
            "calibration_feedback_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "unresolved_review_age_hours",
            _require_nonnegative_decimal(
                "unresolved_review_age_hours",
                self.unresolved_review_age_hours,
            ),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchTeamCrossDomainMemoryConflictCell(_FinalPublicDataclass):
    domain_a: str
    domain_b: str
    status: str
    observation_count: Decimal
    average_memory_freshness_score: Decimal
    freshness_pressure_score: Decimal
    average_contradiction_score: Decimal
    average_calibration_feedback_score: Decimal
    max_unresolved_review_age_hours: Decimal
    unresolved_review_age_pressure_score: Decimal
    conflict_pressure_score: Decimal
    latest_observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamCrossDomainMemoryConflictCell, "cell")
        _require_safe_label("domain_a", self.domain_a)
        _require_safe_label("domain_b", self.domain_b)
        if self.domain_a == self.domain_b:
            raise ValueError("domain pair must contain two distinct domains")
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "observation_count",
            _require_count_decimal("observation_count", self.observation_count),
        )
        if self.observation_count <= ZERO_COUNT:
            raise ValueError("observation_count must be positive")
        for field_name in (
            "average_memory_freshness_score",
            "freshness_pressure_score",
            "average_contradiction_score",
            "average_calibration_feedback_score",
            "unresolved_review_age_pressure_score",
            "conflict_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_unresolved_review_age_hours",
            _require_nonnegative_decimal(
                "max_unresolved_review_age_hours",
                self.max_unresolved_review_age_hours,
            ),
        )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _require_cell_reason_codes(self.reason_codes),
        )
        _validate_cell(self)
        _require_hard_flags("cell", self)
        _reject_unsafe_public_payload("cell", self)


@dataclass(frozen=True)
class ResearchTeamCrossDomainMemoryConflictReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    domain_pair_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamCrossDomainMemoryConflictReasonCodeCount,
            "reason_code_count",
        )
        _require_public_string("reason_code", self.reason_code)
        if self.reason_code not in CELL_REASON_CODES:
            raise ValueError("reason_code must be supported")
        object.__setattr__(self, "count", _require_count_decimal("count", self.count))
        if self.count <= ZERO_COUNT:
            raise ValueError("count must be positive")
        object.__setattr__(
            self,
            "domain_pair_ratio",
            _require_ratio_decimal("domain_pair_ratio", self.domain_pair_ratio),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamCrossDomainMemoryConflictHeatmapReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    domain_pair_count: Decimal
    observation_count: Decimal
    domain_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    freshness_pressure_count: Decimal
    contradiction_pressure_count: Decimal
    calibration_feedback_pressure_count: Decimal
    unresolved_review_age_pressure_count: Decimal
    max_conflict_pressure_score: Decimal
    average_conflict_pressure_score: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchTeamCrossDomainMemoryConflictReasonCodeCount, ...]
    cells: tuple[ResearchTeamCrossDomainMemoryConflictCell, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamCrossDomainMemoryConflictHeatmapReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_CROSS_DOMAIN_MEMORY_CONFLICT_HEATMAP_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in (
            "domain_pair_count",
            "observation_count",
            "domain_count",
            "pass_count",
            "watch_count",
            "block_count",
            "freshness_pressure_count",
            "contradiction_pressure_count",
            "calibration_feedback_pressure_count",
            "unresolved_review_age_pressure_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_conflict_pressure_score",
            "average_conflict_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _require_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _require_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "cells", _require_cells(self.cells))
        if self.derived_validation_digest:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != _derived_validation_digest(self):
                raise ValueError("derived_validation_digest does not match report payload")
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _derived_validation_digest(self),
            )
        _validate_report_materialized_fields(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)


def build_research_team_cross_domain_memory_conflict_heatmap_report(
    observations: Iterable[ResearchTeamCrossDomainMemoryConflictObservation],
    *,
    config: ResearchTeamCrossDomainMemoryConflictHeatmapConfig,
    generated_at: datetime,
) -> ResearchTeamCrossDomainMemoryConflictHeatmapReport:
    if type(config) is not ResearchTeamCrossDomainMemoryConflictHeatmapConfig:
        raise ValueError(
            "config must be a ResearchTeamCrossDomainMemoryConflictHeatmapConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_observations(observations)
    for item in inputs:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be in the future")

    grouped: dict[tuple[str, str], list[ResearchTeamCrossDomainMemoryConflictObservation]]
    grouped = {}
    for item in inputs:
        grouped.setdefault(_domain_pair_key(item), []).append(item)

    cells = tuple(
        sorted(
            (
                _cell_from_observations(
                    key=key,
                    observations=tuple(items),
                    config=config,
                )
                for key, items in grouped.items()
            ),
            key=_cell_sort_key,
        ),
    )
    domains = frozenset(
        domain
        for item in inputs
        for domain in (item.domain_a, item.domain_b)
    )
    status = _rollup_status(tuple(cell.status for cell in cells))
    return ResearchTeamCrossDomainMemoryConflictHeatmapReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=status,
        domain_pair_count=_count(len(cells)),
        observation_count=_count(len(inputs)),
        domain_count=_count(len(domains)),
        pass_count=_status_count(cells, "pass"),
        watch_count=_status_count(cells, "watch"),
        block_count=_status_count(cells, "block"),
        freshness_pressure_count=_component_pressure_count(
            cells,
            ("memory_freshness_pressure_block", "memory_freshness_pressure_watch"),
        ),
        contradiction_pressure_count=_component_pressure_count(
            cells,
            (
                "memory_contradiction_pressure_block",
                "memory_contradiction_pressure_watch",
            ),
        ),
        calibration_feedback_pressure_count=_component_pressure_count(
            cells,
            (
                "calibration_feedback_pressure_block",
                "calibration_feedback_pressure_watch",
            ),
        ),
        unresolved_review_age_pressure_count=_component_pressure_count(
            cells,
            (
                "unresolved_review_age_pressure_block",
                "unresolved_review_age_pressure_watch",
            ),
        ),
        max_conflict_pressure_score=_max_decimal(
            tuple(cell.conflict_pressure_score for cell in cells),
        ),
        average_conflict_pressure_score=_average(
            tuple(cell.conflict_pressure_score for cell in cells),
        ),
        reason_codes=_report_reason_codes(cells),
        reason_code_counts=_reason_code_counts(cells),
        cells=cells,
    )


def research_team_cross_domain_memory_conflict_heatmap_report_payload(
    report: ResearchTeamCrossDomainMemoryConflictHeatmapReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamCrossDomainMemoryConflictHeatmapReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        if report.derived_validation_digest != _derived_validation_digest(report):
            raise ValueError("derived_validation_digest does not match report payload")
        _validate_report_materialized_fields(report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be an object")
        _reject_unsafe_public_payload("payload", payload)
        _reject_public_numeric_values(payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _reject_public_numeric_values(report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be an object")
        _require_hard_flags("payload", _PayloadFlags(payload))
        if "derived_validation_digest" not in payload:
            raise ValueError("derived_validation_digest is required")
        supplied_digest = payload["derived_validation_digest"]
        _require_sha256("derived_validation_digest", supplied_digest)
        if supplied_digest != _payload_validation_digest(payload):
            raise ValueError("derived_validation_digest does not match report payload")
        return payload
    raise ValueError("report must be a ResearchTeamCrossDomainMemoryConflictHeatmapReport")


@dataclass(frozen=True)
class _PayloadFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        if "paper_only" not in self.value:
            return None
        return self.value["paper_only"]

    @property
    def report_only(self) -> object:
        if "report_only" not in self.value:
            return None
        return self.value["report_only"]

    @property
    def readonly(self) -> object:
        if "readonly" not in self.value:
            return None
        return self.value["readonly"]


def _normalize_observations(
    observations: Iterable[ResearchTeamCrossDomainMemoryConflictObservation],
) -> tuple[ResearchTeamCrossDomainMemoryConflictObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        items = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    for item in items:
        if type(item) is not ResearchTeamCrossDomainMemoryConflictObservation:
            raise ValueError(
                "observations must contain "
                "ResearchTeamCrossDomainMemoryConflictObservation",
            )
        _require_hard_flags("observation", item)
    return items


def _domain_pair_key(
    item: ResearchTeamCrossDomainMemoryConflictObservation,
) -> tuple[str, str]:
    return tuple(sorted((item.domain_a, item.domain_b)))


def _cell_from_observations(
    *,
    key: tuple[str, str],
    observations: tuple[ResearchTeamCrossDomainMemoryConflictObservation, ...],
    config: ResearchTeamCrossDomainMemoryConflictHeatmapConfig,
) -> ResearchTeamCrossDomainMemoryConflictCell:
    domain_a, domain_b = key
    memory_freshness = _average(tuple(item.memory_freshness_score for item in observations))
    freshness_pressure = _quantize_ratio(ONE_RATIO - memory_freshness)
    contradiction = _average(tuple(item.contradiction_score for item in observations))
    calibration_feedback = _average(
        tuple(item.calibration_feedback_score for item in observations),
    )
    max_review_age = _max_decimal(
        tuple(item.unresolved_review_age_hours for item in observations),
    )
    review_age_pressure = _ratio_capped(
        max_review_age,
        config.block_unresolved_review_age_hours,
    )
    conflict_pressure = _average(
        (
            freshness_pressure,
            contradiction,
            calibration_feedback,
            review_age_pressure,
        ),
    )
    reason_codes = _cell_reason_codes(
        conflict_pressure_score=conflict_pressure,
        freshness_pressure_score=freshness_pressure,
        contradiction_score=contradiction,
        calibration_feedback_score=calibration_feedback,
        unresolved_review_age_pressure_score=review_age_pressure,
        config=config,
    )
    return ResearchTeamCrossDomainMemoryConflictCell(
        domain_a=domain_a,
        domain_b=domain_b,
        status=_row_status(reason_codes),
        observation_count=_count(len(observations)),
        average_memory_freshness_score=memory_freshness,
        freshness_pressure_score=freshness_pressure,
        average_contradiction_score=contradiction,
        average_calibration_feedback_score=calibration_feedback,
        max_unresolved_review_age_hours=max_review_age,
        unresolved_review_age_pressure_score=review_age_pressure,
        conflict_pressure_score=conflict_pressure,
        latest_observed_at=max(item.observed_at for item in observations),
        reason_codes=reason_codes,
    )


def _cell_reason_codes(
    *,
    conflict_pressure_score: Decimal,
    freshness_pressure_score: Decimal,
    contradiction_score: Decimal,
    calibration_feedback_score: Decimal,
    unresolved_review_age_pressure_score: Decimal,
    config: ResearchTeamCrossDomainMemoryConflictHeatmapConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if conflict_pressure_score >= config.block_conflict_pressure_score:
        reason_codes.append("cross_domain_memory_conflict_heatmap_block")
    elif conflict_pressure_score >= config.watch_conflict_pressure_score:
        reason_codes.append("cross_domain_memory_conflict_heatmap_watch")

    reason_codes.extend(
        _component_reason_codes(
            value=freshness_pressure_score,
            watch_reason_code="memory_freshness_pressure_watch",
            block_reason_code="memory_freshness_pressure_block",
            config=config,
        ),
    )
    reason_codes.extend(
        _component_reason_codes(
            value=contradiction_score,
            watch_reason_code="memory_contradiction_pressure_watch",
            block_reason_code="memory_contradiction_pressure_block",
            config=config,
        ),
    )
    reason_codes.extend(
        _component_reason_codes(
            value=calibration_feedback_score,
            watch_reason_code="calibration_feedback_pressure_watch",
            block_reason_code="calibration_feedback_pressure_block",
            config=config,
        ),
    )
    reason_codes.extend(
        _component_reason_codes(
            value=unresolved_review_age_pressure_score,
            watch_reason_code="unresolved_review_age_pressure_watch",
            block_reason_code="unresolved_review_age_pressure_block",
            config=config,
        ),
    )
    if not reason_codes:
        reason_codes.append(PASS_CELL_REASON_CODE)
    return tuple(reason_codes)


def _component_reason_codes(
    *,
    value: Decimal,
    watch_reason_code: str,
    block_reason_code: str,
    config: ResearchTeamCrossDomainMemoryConflictHeatmapConfig,
) -> tuple[str, ...]:
    if value >= config.block_conflict_pressure_score:
        return (block_reason_code,)
    if value >= config.watch_conflict_pressure_score:
        return (watch_reason_code,)
    return ()


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    if "cross_domain_memory_conflict_heatmap_block" in reason_codes:
        return "block"
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    if "cross_domain_memory_conflict_heatmap_watch" in reason_codes:
        return "watch"
    return "pass"


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if any(status == "block" for status in statuses):
        return "block"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _report_reason_codes(
    cells: tuple[ResearchTeamCrossDomainMemoryConflictCell, ...],
) -> tuple[str, ...]:
    if not cells:
        return (EMPTY_REPORT_REASON_CODE,)
    status = _rollup_status(tuple(cell.status for cell in cells))
    if status == "pass":
        return (PASS_CELL_REASON_CODE,)
    cell_reasons = frozenset(
        reason_code
        for cell in cells
        for reason_code in cell.reason_codes
        if reason_code != PASS_CELL_REASON_CODE
    )
    reason_codes: list[str] = []
    rollup_reason = f"cross_domain_memory_conflict_heatmap_{status}"
    reason_codes.append(rollup_reason)
    for reason_code in REPORT_REASON_PRIORITY:
        if reason_code == rollup_reason:
            continue
        if reason_code in cell_reasons:
            reason_codes.append(reason_code)
    return tuple(reason_codes)


def _reason_code_counts(
    cells: tuple[ResearchTeamCrossDomainMemoryConflictCell, ...],
) -> tuple[ResearchTeamCrossDomainMemoryConflictReasonCodeCount, ...]:
    if not cells:
        return ()
    counter: Counter[str] = Counter()
    for cell in cells:
        counter.update(cell.reason_codes)
    denominator = _count(len(cells))
    priority = {
        reason_code: index
        for index, reason_code in enumerate(
            (PASS_CELL_REASON_CODE,)
            + CELL_STATUS_REASON_CODES
            + BLOCK_REASON_CODES
            + WATCH_REASON_CODES,
        )
    }
    return tuple(
        ResearchTeamCrossDomainMemoryConflictReasonCodeCount(
            reason_code=reason_code,
            count=count,
            domain_pair_ratio=_ratio(count, denominator),
        )
        for count, reason_code in sorted(
            ((_count(count), reason_code) for reason_code, count in counter.items()),
            key=lambda item: (
                -item[0],
                priority[item[1]] if item[1] in priority else 999,
                item[1],
            ),
        )
    )


def _cell_sort_key(
    cell: ResearchTeamCrossDomainMemoryConflictCell,
) -> tuple[Decimal, Decimal, str, str]:
    return (
        -STATUS_WEIGHT[cell.status],
        -cell.conflict_pressure_score,
        cell.domain_a,
        cell.domain_b,
    )


def _status_count(
    cells: tuple[ResearchTeamCrossDomainMemoryConflictCell, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for cell in cells if cell.status == status))


def _component_pressure_count(
    cells: tuple[ResearchTeamCrossDomainMemoryConflictCell, ...],
    reason_codes: tuple[str, str],
) -> Decimal:
    return _count(
        sum(
            1
            for cell in cells
            if reason_codes[0] in cell.reason_codes or reason_codes[1] in cell.reason_codes
        ),
    )


def _validate_cell(cell: ResearchTeamCrossDomainMemoryConflictCell) -> None:
    if cell.status != _row_status(cell.reason_codes):
        raise ValueError("status must match reason_codes")
    if cell.status == "pass" and cell.reason_codes != (PASS_CELL_REASON_CODE,):
        raise ValueError("pass cells require cross_domain_memory_conflict_clear")
    if cell.status != "pass" and PASS_CELL_REASON_CODE in cell.reason_codes:
        raise ValueError("conflict cells must not include clear reason_codes")
    if cell.status == "block" and not any(
        reason_code in cell.reason_codes
        for reason_code in BLOCK_REASON_CODES + ("cross_domain_memory_conflict_heatmap_block",)
    ):
        raise ValueError("block cells require block reason_codes")


def _validate_report_materialized_fields(
    report: ResearchTeamCrossDomainMemoryConflictHeatmapReport,
) -> None:
    cells = report.cells
    checks = {
        "domain_pair_count": _count(len(cells)),
        "pass_count": _status_count(cells, "pass"),
        "watch_count": _status_count(cells, "watch"),
        "block_count": _status_count(cells, "block"),
        "freshness_pressure_count": _component_pressure_count(
            cells,
            ("memory_freshness_pressure_block", "memory_freshness_pressure_watch"),
        ),
        "contradiction_pressure_count": _component_pressure_count(
            cells,
            (
                "memory_contradiction_pressure_block",
                "memory_contradiction_pressure_watch",
            ),
        ),
        "calibration_feedback_pressure_count": _component_pressure_count(
            cells,
            (
                "calibration_feedback_pressure_block",
                "calibration_feedback_pressure_watch",
            ),
        ),
        "unresolved_review_age_pressure_count": _component_pressure_count(
            cells,
            (
                "unresolved_review_age_pressure_block",
                "unresolved_review_age_pressure_watch",
            ),
        ),
        "max_conflict_pressure_score": _max_decimal(
            tuple(cell.conflict_pressure_score for cell in cells),
        ),
        "average_conflict_pressure_score": _average(
            tuple(cell.conflict_pressure_score for cell in cells),
        ),
    }
    for field_name, expected in checks.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match cells")
    expected_status = _rollup_status(tuple(cell.status for cell in cells))
    if report.status != expected_status:
        raise ValueError("status must match cells")
    if report.reason_codes != _report_reason_codes(cells):
        raise ValueError("reason_codes must match cells")
    if report.reason_code_counts != _reason_code_counts(cells):
        raise ValueError("reason_code_counts must match cells")


def _require_cells(
    cells: tuple[ResearchTeamCrossDomainMemoryConflictCell, ...],
) -> tuple[ResearchTeamCrossDomainMemoryConflictCell, ...]:
    if isinstance(cells, (str, bytes)):
        raise ValueError("cells must be an iterable")
    try:
        normalized = tuple(cells)
    except TypeError as exc:
        raise ValueError("cells must be an iterable") from exc
    seen: set[tuple[str, str]] = set()
    for cell in normalized:
        if type(cell) is not ResearchTeamCrossDomainMemoryConflictCell:
            raise ValueError(
                "cells must contain ResearchTeamCrossDomainMemoryConflictCell",
            )
        _require_hard_flags("cell", cell)
        key = (cell.domain_a, cell.domain_b)
        if key in seen:
            raise ValueError("cells must contain unique domain pairs")
        seen.add(key)
    if normalized != tuple(sorted(normalized, key=_cell_sort_key)):
        raise ValueError("cells must be sorted by status and conflict pressure")
    return normalized


def _require_reason_code_counts(
    rows: tuple[ResearchTeamCrossDomainMemoryConflictReasonCodeCount, ...],
) -> tuple[ResearchTeamCrossDomainMemoryConflictReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for row in normalized:
        if type(row) is not ResearchTeamCrossDomainMemoryConflictReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTeamCrossDomainMemoryConflictReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", row)
    if len({row.reason_code for row in normalized}) != len(normalized):
        raise ValueError("reason_code_counts reason_code values must be unique")
    return normalized


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    require_paper_only_flags(label, value)


def _require_safe_label(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be lowercase snake case")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical non-empty string")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")
    _reject_unsafe_public_text(field_name, value)


def _require_cell_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not normalized:
        raise ValueError("reason_codes must be non-empty")
    for reason_code in normalized:
        _require_public_string("reason_code", reason_code)
        if reason_code not in CELL_REASON_CODES:
            raise ValueError("reason_code must be supported")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    return normalized


def _require_report_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not normalized:
        raise ValueError("reason_codes must be non-empty")
    for reason_code in normalized:
        _require_public_string("reason_code", reason_code)
        if not (
            reason_code == EMPTY_REPORT_REASON_CODE
            or reason_code == PASS_CELL_REASON_CODE
            or reason_code in CELL_STATUS_REASON_CODES
            or reason_code in REPORT_REASON_PRIORITY
        ):
            raise ValueError("reason_code must be supported")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    return normalized


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in PUBLIC_STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if value.is_nan() or value.is_infinite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be non-negative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return normalized.quantize(COUNT_QUANTUM)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be non-negative")
    return _quantize_ratio(normalized)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO_RATIO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must be no greater than 1")
    return normalized


def _quantize_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (sum(values, ZERO_RATIO) / Decimal(len(values))).quantize(RATIO_QUANTUM)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    return max(values).quantize(RATIO_QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO_COUNT:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(RATIO_QUANTUM)


def _ratio_capped(numerator: Decimal, denominator: Decimal) -> Decimal:
    value = _ratio(numerator, denominator)
    if value > ONE_RATIO:
        return ONE_RATIO
    return value


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if len(value) != 64 or any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _derived_validation_digest(
    report: ResearchTeamCrossDomainMemoryConflictHeatmapReport,
) -> str:
    payload = _json_ready_without_digest(report)
    return _payload_validation_digest(payload)


def _payload_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = _strip_digest(payload)
    canonical = json.dumps(digest_payload, sort_keys=True, separators=(",", ":"))
    return sha256(canonical.encode("utf-8")).hexdigest()


def _strip_digest(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _strip_digest(item)
            for key, item in sorted(value.items())
            if key != "derived_validation_digest"
        }
    if isinstance(value, list):
        return [_strip_digest(item) for item in value]
    return value


def _json_ready_without_digest(
    report: ResearchTeamCrossDomainMemoryConflictHeatmapReport,
) -> dict[str, Any]:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be an object")
    payload.pop("derived_validation_digest", None)
    return payload


def _json_ready(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) is Decimal:
        return str(value)
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return {str(key): _json_ready(item) for key, item in value.items()}
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported payload value type: {type(value).__name__}")


def _reject_public_numeric_values(value: object) -> None:
    if type(value) in (int, float):
        raise ValueError("public payload numeric values must be Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_numeric_values(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_text(f"{label}.{field.name}", field.name)
            _reject_unsafe_public_payload(
                f"{label}.{field.name}",
                getattr(value, field.name),
            )
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_public_text(f"{label}.key", str(key))
            _reject_unsafe_public_payload(f"{label}.{key}", item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public value for {field_name}")
    if "://" in lowered:
        raise ValueError(f"unsafe public value for {field_name}")
    if "@" in lowered:
        raise ValueError(f"unsafe public value for {field_name}")
