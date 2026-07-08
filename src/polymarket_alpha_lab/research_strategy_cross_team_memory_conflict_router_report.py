"""Pure public strategy memory conflict routing report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_CROSS_TEAM_MEMORY_CONFLICT_ROUTER_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_CROSS_TEAM_MEMORY_CONFLICT_ROUTER_STATUSES",
    "ResearchStrategyCrossTeamMemoryConflictInput",
    "ResearchStrategyCrossTeamMemoryConflictRouterConfig",
    "ResearchStrategyCrossTeamMemoryConflictRouterReasonCodeCount",
    "ResearchStrategyCrossTeamMemoryConflictRouterReport",
    "ResearchStrategyCrossTeamMemoryConflictRouterRow",
    "build_research_strategy_cross_team_memory_conflict_router_report",
    "research_strategy_cross_team_memory_conflict_router_report_payload",
)


DEFAULT_RESEARCH_STRATEGY_CROSS_TEAM_MEMORY_CONFLICT_ROUTER_REPORT_CONFIG_VERSION = (
    "research-strategy-cross-team-memory-conflict-router-report-v0"
)

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
RESEARCH_STRATEGY_CROSS_TEAM_MEMORY_CONFLICT_ROUTER_STATUSES = (
    "pass",
    "watch",
    "block",
)
PAPER_ACTION_BY_STATUS = {
    "pass": "paper_cross_team_memory_conflict_route_monitor",
    "watch": "paper_cross_team_memory_conflict_route_watch",
    "block": "paper_cross_team_memory_conflict_route_block",
}
MANUAL_QUEUE_BY_STATUS = {
    "pass": "manual_research_queue_monitor",
    "watch": "manual_research_queue_watch",
    "block": "manual_research_queue_block",
}

PASS_ROW_REASON_CODE = "cross_team_memory_conflict_route_clear"
EMPTY_REPORT_REASON_CODE = "cross_team_memory_conflict_router_empty"
BLOCK_REASON_CODES = (
    "disagreement_severity_block",
    "memory_freshness_block",
    "unresolved_disagreement_block",
    "domain_overlap_block",
    "route_priority_block",
)
WATCH_REASON_CODES = (
    "disagreement_severity_watch",
    "memory_freshness_watch",
    "unresolved_disagreement_watch",
    "domain_overlap_watch",
    "route_priority_watch",
)
ROW_REASON_CODES = (
    PASS_ROW_REASON_CODE,
    *BLOCK_REASON_CODES,
    *WATCH_REASON_CODES,
)
REPORT_REASON_PRIORITY = (*BLOCK_REASON_CODES, *WATCH_REASON_CODES)
HEX_CHARS = frozenset("0123456789abcdef")
UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "cand" + "idate",
        "mar" + "ket",
        "sl" + "ug",
        "ques" + "tion",
        "u" + "rl",
        "sou" + "rce",
        "tex" + "t",
        "d" + "sn",
        "tok" + "en",
        "wa" + "llet",
        "au" + "th",
        "ord" + "er",
        "tra" + "de",
        "b" + "uy",
        "se" + "ll",
        "recom" + "mend",
        "siz" + "ing",
        "data" + "base",
        "net" + "work",
        "li" + "ve",
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
                raise TypeError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchStrategyCrossTeamMemoryConflictRouterConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_CROSS_TEAM_MEMORY_CONFLICT_ROUTER_REPORT_CONFIG_VERSION
    )
    watch_disagreement_severity_score: Decimal = Decimal("0.250000")
    block_disagreement_severity_score: Decimal = Decimal("0.700000")
    watch_memory_freshness_lag_hours: Decimal = Decimal("24.000000")
    block_memory_freshness_lag_hours: Decimal = Decimal("72.000000")
    watch_unresolved_disagreement_count: Decimal = Decimal("1")
    block_unresolved_disagreement_count: Decimal = Decimal("3")
    watch_domain_overlap_score: Decimal = Decimal("0.500000")
    block_domain_overlap_score: Decimal = Decimal("0.850000")
    watch_route_priority_score: Decimal = Decimal("0.350000")
    block_route_priority_score: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyCrossTeamMemoryConflictRouterConfig)
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_CROSS_TEAM_MEMORY_CONFLICT_ROUTER_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "watch_disagreement_severity_score",
            "block_disagreement_severity_score",
            "watch_domain_overlap_score",
            "block_domain_overlap_score",
            "watch_route_priority_score",
            "block_route_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_memory_freshness_lag_hours",
            "block_memory_freshness_lag_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_unresolved_disagreement_count",
            "block_unresolved_disagreement_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyCrossTeamMemoryConflictInput(_FinalPublicDataclass):
    conflict_group_label: str
    primary_team_label: str
    secondary_team_label: str
    disagreement_severity_score: Decimal
    memory_freshness_lag_hours: Decimal
    unresolved_disagreement_count: Decimal
    domain_overlap_score: Decimal
    detected_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyCrossTeamMemoryConflictInput)
        for field_name in (
            "conflict_group_label",
            "primary_team_label",
            "secondary_team_label",
        ):
            _require_safe_label(field_name, getattr(self, field_name))
        for field_name in ("disagreement_severity_score", "domain_overlap_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "memory_freshness_lag_hours",
            _require_nonnegative_decimal(
                "memory_freshness_lag_hours",
                self.memory_freshness_lag_hours,
            ),
        )
        object.__setattr__(
            self,
            "unresolved_disagreement_count",
            _require_count_decimal(
                "unresolved_disagreement_count",
                self.unresolved_disagreement_count,
            ),
        )
        object.__setattr__(self, "detected_at", _as_utc("detected_at", self.detected_at))
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyCrossTeamMemoryConflictRouterRow(_FinalPublicDataclass):
    conflict_group_label: str
    primary_team_label: str
    secondary_team_label: str
    manual_queue_label: str
    route_status: str
    disagreement_severity_score: Decimal
    memory_freshness_lag_hours: Decimal
    freshness_pressure_score: Decimal
    unresolved_disagreement_count: Decimal
    domain_overlap_score: Decimal
    route_priority_score: Decimal
    detected_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyCrossTeamMemoryConflictRouterRow)
        for field_name in (
            "conflict_group_label",
            "primary_team_label",
            "secondary_team_label",
            "manual_queue_label",
        ):
            _require_safe_label(field_name, getattr(self, field_name))
        _require_status("route_status", self.route_status)
        for field_name in (
            "disagreement_severity_score",
            "freshness_pressure_score",
            "domain_overlap_score",
            "route_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "memory_freshness_lag_hours",
            _require_nonnegative_decimal(
                "memory_freshness_lag_hours",
                self.memory_freshness_lag_hours,
            ),
        )
        object.__setattr__(
            self,
            "unresolved_disagreement_count",
            _require_count_decimal(
                "unresolved_disagreement_count",
                self.unresolved_disagreement_count,
            ),
        )
        object.__setattr__(self, "detected_at", _as_utc("detected_at", self.detected_at))
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchStrategyCrossTeamMemoryConflictRouterReasonCodeCount(
    _FinalPublicDataclass,
):
    reason_code: str
    count: Decimal
    routed_conflict_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyCrossTeamMemoryConflictRouterReasonCodeCount,
        )
        _require_public_string("reason_code", self.reason_code)
        object.__setattr__(self, "count", _require_count_decimal("count", self.count))
        object.__setattr__(
            self,
            "routed_conflict_ratio",
            _require_ratio_decimal("routed_conflict_ratio", self.routed_conflict_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyCrossTeamMemoryConflictRouterReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    routed_conflict_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    unresolved_disagreement_total: Decimal
    freshness_stale_count: Decimal
    max_route_priority_score: Decimal
    oldest_memory_freshness_lag_hours: Decimal
    status: str
    paper_route_action: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchStrategyCrossTeamMemoryConflictRouterReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchStrategyCrossTeamMemoryConflictRouterRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyCrossTeamMemoryConflictRouterReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_CROSS_TEAM_MEMORY_CONFLICT_ROUTER_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "routed_conflict_count",
            "pass_count",
            "watch_count",
            "block_count",
            "unresolved_disagreement_total",
            "freshness_stale_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_route_priority_score",
            _require_ratio_decimal(
                "max_route_priority_score",
                self.max_route_priority_score,
            ),
        )
        object.__setattr__(
            self,
            "oldest_memory_freshness_lag_hours",
            _require_nonnegative_decimal(
                "oldest_memory_freshness_lag_hours",
                self.oldest_memory_freshness_lag_hours,
            ),
        )
        _require_status("status", self.status)
        _require_public_string("paper_route_action", self.paper_route_action)
        if self.paper_route_action != PAPER_ACTION_BY_STATUS[self.status]:
            raise ValueError("paper_route_action must match status")
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
        object.__setattr__(self, "rows", _require_rows(self.rows))
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
        _reject_unsafe_public_payload("report", self)
        _require_hard_flags("report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_strategy_cross_team_memory_conflict_router_report_payload(self)


def build_research_strategy_cross_team_memory_conflict_router_report(
    conflicts: Iterable[ResearchStrategyCrossTeamMemoryConflictInput],
    *,
    config: ResearchStrategyCrossTeamMemoryConflictRouterConfig,
    generated_at: datetime,
) -> ResearchStrategyCrossTeamMemoryConflictRouterReport:
    if type(config) is not ResearchStrategyCrossTeamMemoryConflictRouterConfig:
        raise ValueError("config must be a ResearchStrategyCrossTeamMemoryConflictRouterConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(conflicts)
    rows = tuple(
        sorted(
            (
                _row_from_input(item, config=config, generated_at=generated_at_utc)
                for item in inputs
            ),
            key=_row_sort_key,
        ),
    )
    status = _rollup_status(tuple(row.route_status for row in rows))
    return ResearchStrategyCrossTeamMemoryConflictRouterReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        routed_conflict_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        unresolved_disagreement_total=_sum_counts(
            tuple(row.unresolved_disagreement_count for row in rows),
        ),
        freshness_stale_count=_count(
            sum(
                1
                for row in rows
                if (
                    "memory_freshness_watch" in row.reason_codes
                    or "memory_freshness_block" in row.reason_codes
                )
            ),
        ),
        max_route_priority_score=_max_decimal(
            tuple(row.route_priority_score for row in rows),
        ),
        oldest_memory_freshness_lag_hours=_max_decimal(
            tuple(row.memory_freshness_lag_hours for row in rows),
        ),
        status=status,
        paper_route_action=PAPER_ACTION_BY_STATUS[status],
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_strategy_cross_team_memory_conflict_router_report_payload(
    report: ResearchStrategyCrossTeamMemoryConflictRouterReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyCrossTeamMemoryConflictRouterReport:
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
    raise ValueError("report must be a ResearchStrategyCrossTeamMemoryConflictRouterReport")


@dataclass(frozen=True)
class _PayloadFlags:
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


def _normalize_inputs(
    conflicts: Iterable[ResearchStrategyCrossTeamMemoryConflictInput],
) -> tuple[ResearchStrategyCrossTeamMemoryConflictInput, ...]:
    if isinstance(conflicts, (str, bytes)):
        raise ValueError("conflicts must be an iterable")
    try:
        items = tuple(conflicts)
    except TypeError as exc:
        raise ValueError("conflicts must be an iterable") from exc
    seen: set[tuple[str, str, str]] = set()
    for item in items:
        if type(item) is not ResearchStrategyCrossTeamMemoryConflictInput:
            raise ValueError(
                "conflicts must contain ResearchStrategyCrossTeamMemoryConflictInput",
            )
        _require_hard_flags("input", item)
        key = (
            item.conflict_group_label,
            item.primary_team_label,
            item.secondary_team_label,
        )
        if key in seen:
            raise ValueError("conflicts must contain unique team disagreement labels")
        seen.add(key)
    return items


def _row_from_input(
    item: ResearchStrategyCrossTeamMemoryConflictInput,
    *,
    config: ResearchStrategyCrossTeamMemoryConflictRouterConfig,
    generated_at: datetime,
) -> ResearchStrategyCrossTeamMemoryConflictRouterRow:
    if item.detected_at > generated_at:
        raise ValueError("detected_at must not be in the future")
    freshness_pressure_score = _ratio_capped(
        item.memory_freshness_lag_hours,
        config.block_memory_freshness_lag_hours,
    )
    route_priority_score = _max_decimal(
        (
            item.disagreement_severity_score,
            freshness_pressure_score,
            item.domain_overlap_score,
        ),
    )
    reason_codes = _row_reason_codes(
        item,
        config=config,
        route_priority_score=route_priority_score,
    )
    route_status = _row_status(reason_codes)
    return ResearchStrategyCrossTeamMemoryConflictRouterRow(
        conflict_group_label=item.conflict_group_label,
        primary_team_label=item.primary_team_label,
        secondary_team_label=item.secondary_team_label,
        manual_queue_label=MANUAL_QUEUE_BY_STATUS[route_status],
        route_status=route_status,
        disagreement_severity_score=item.disagreement_severity_score,
        memory_freshness_lag_hours=item.memory_freshness_lag_hours,
        freshness_pressure_score=freshness_pressure_score,
        unresolved_disagreement_count=item.unresolved_disagreement_count,
        domain_overlap_score=item.domain_overlap_score,
        route_priority_score=route_priority_score,
        detected_at=item.detected_at,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: ResearchStrategyCrossTeamMemoryConflictInput,
    *,
    config: ResearchStrategyCrossTeamMemoryConflictRouterConfig,
    route_priority_score: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if item.disagreement_severity_score >= config.block_disagreement_severity_score:
        reason_codes.append("disagreement_severity_block")
    elif item.disagreement_severity_score >= config.watch_disagreement_severity_score:
        reason_codes.append("disagreement_severity_watch")

    if item.memory_freshness_lag_hours >= config.block_memory_freshness_lag_hours:
        reason_codes.append("memory_freshness_block")
    elif item.memory_freshness_lag_hours >= config.watch_memory_freshness_lag_hours:
        reason_codes.append("memory_freshness_watch")

    if item.unresolved_disagreement_count >= config.block_unresolved_disagreement_count:
        reason_codes.append("unresolved_disagreement_block")
    elif item.unresolved_disagreement_count >= config.watch_unresolved_disagreement_count:
        reason_codes.append("unresolved_disagreement_watch")

    if item.domain_overlap_score >= config.block_domain_overlap_score:
        reason_codes.append("domain_overlap_block")
    elif item.domain_overlap_score >= config.watch_domain_overlap_score:
        reason_codes.append("domain_overlap_watch")

    if route_priority_score >= config.block_route_priority_score:
        reason_codes.append("route_priority_block")
    elif route_priority_score >= config.watch_route_priority_score:
        reason_codes.append("route_priority_watch")

    if not reason_codes:
        reason_codes.append(PASS_ROW_REASON_CODE)
    return tuple(reason_codes)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "pass"


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if any(status == "block" for status in statuses):
        return "block"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyCrossTeamMemoryConflictRouterRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REPORT_REASON_CODE,)
    status = _rollup_status(tuple(row.route_status for row in rows))
    reason_codes = [
        f"cross_team_memory_conflict_route_{'clear' if status == 'pass' else status}",
    ]
    present = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != PASS_ROW_REASON_CODE
    }
    reason_codes.extend(
        reason_code for reason_code in REPORT_REASON_PRIORITY if reason_code in present
    )
    return tuple(reason_codes)


def _reason_code_counts(
    rows: tuple[ResearchStrategyCrossTeamMemoryConflictRouterRow, ...],
) -> tuple[ResearchStrategyCrossTeamMemoryConflictRouterReasonCodeCount, ...]:
    if not rows:
        return ()
    counts = Counter(reason_code for row in rows for reason_code in row.reason_codes)
    total = _count(len(rows))
    return tuple(
        ResearchStrategyCrossTeamMemoryConflictRouterReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
            routed_conflict_ratio=_ratio(Decimal(count), total),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: _reason_code_sort_key(item[0]),
        )
    )


def _reason_code_sort_key(reason_code: str) -> tuple[int, str]:
    try:
        return (ROW_REASON_CODES.index(reason_code), reason_code)
    except ValueError:
        return (len(ROW_REASON_CODES), reason_code)


def _row_sort_key(
    row: ResearchStrategyCrossTeamMemoryConflictRouterRow,
) -> tuple[Decimal, Decimal, Decimal, str, str, str]:
    status_rank = {
        "block": Decimal("0"),
        "watch": Decimal("1"),
        "pass": Decimal("2"),
    }
    return (
        status_rank[row.route_status],
        -row.route_priority_score,
        -row.memory_freshness_lag_hours,
        row.conflict_group_label,
        row.primary_team_label,
        row.secondary_team_label,
    )


def _status_count(
    rows: tuple[ResearchStrategyCrossTeamMemoryConflictRouterRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.route_status == status))


def _sum_counts(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return sum(values, ZERO_COUNT).quantize(COUNT_QUANTUM)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    return max(values)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO_COUNT:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(RATIO_QUANTUM)


def _ratio_capped(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO_COUNT:
        raise ValueError("denominator must be positive")
    value = _ratio(numerator, denominator)
    if value > ONE_RATIO:
        return ONE_RATIO
    if value < ZERO_RATIO:
        return ZERO_RATIO
    return value


def _validate_config(
    config: ResearchStrategyCrossTeamMemoryConflictRouterConfig,
) -> None:
    if (
        config.block_disagreement_severity_score
        < config.watch_disagreement_severity_score
    ):
        raise ValueError("block_disagreement_severity_score must be at least watch")
    if (
        config.block_memory_freshness_lag_hours
        < config.watch_memory_freshness_lag_hours
    ):
        raise ValueError("block_memory_freshness_lag_hours must be at least watch")
    if (
        config.block_unresolved_disagreement_count
        < config.watch_unresolved_disagreement_count
    ):
        raise ValueError("block_unresolved_disagreement_count must be at least watch")
    if config.block_domain_overlap_score < config.watch_domain_overlap_score:
        raise ValueError("block_domain_overlap_score must be at least watch")
    if config.block_route_priority_score < config.watch_route_priority_score:
        raise ValueError("block_route_priority_score must be at least watch")


def _validate_row(row: ResearchStrategyCrossTeamMemoryConflictRouterRow) -> None:
    if row.primary_team_label == row.secondary_team_label:
        raise ValueError("team labels must be distinct")
    if row.manual_queue_label != MANUAL_QUEUE_BY_STATUS[row.route_status]:
        raise ValueError("manual_queue_label must match route_status")
    if row.route_status != _row_status(row.reason_codes):
        raise ValueError("route_status must match reason_codes")


def _validate_report_materialized_fields(
    report: ResearchStrategyCrossTeamMemoryConflictRouterReport,
) -> None:
    rows = report.rows
    if report.routed_conflict_count != _count(len(rows)):
        raise ValueError("routed_conflict_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.unresolved_disagreement_total != _sum_counts(
        tuple(row.unresolved_disagreement_count for row in rows),
    ):
        raise ValueError("unresolved_disagreement_total must match rows")
    stale_count = _count(
        sum(
            1
            for row in rows
            if (
                "memory_freshness_watch" in row.reason_codes
                or "memory_freshness_block" in row.reason_codes
            )
        ),
    )
    if report.freshness_stale_count != stale_count:
        raise ValueError("freshness_stale_count must match rows")
    if report.max_route_priority_score != _max_decimal(
        tuple(row.route_priority_score for row in rows),
    ):
        raise ValueError("max_route_priority_score must match rows")
    if report.oldest_memory_freshness_lag_hours != _max_decimal(
        tuple(row.memory_freshness_lag_hours for row in rows),
    ):
        raise ValueError("oldest_memory_freshness_lag_hours must match rows")
    if report.status != _rollup_status(tuple(row.route_status for row in rows)):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _require_rows(
    rows: Iterable[ResearchStrategyCrossTeamMemoryConflictRouterRow],
) -> tuple[ResearchStrategyCrossTeamMemoryConflictRouterRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must contain row values")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must contain row values") from exc
    for row in values:
        if type(row) is not ResearchStrategyCrossTeamMemoryConflictRouterRow:
            raise ValueError("rows must contain row values")
        _require_hard_flags("row", row)
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sort")
    seen: set[tuple[str, str, str]] = set()
    for row in values:
        key = (
            row.conflict_group_label,
            row.primary_team_label,
            row.secondary_team_label,
        )
        if key in seen:
            raise ValueError("rows must be unique")
        seen.add(key)
    return values


def _require_reason_code_counts(
    values: Iterable[ResearchStrategyCrossTeamMemoryConflictRouterReasonCodeCount],
) -> tuple[ResearchStrategyCrossTeamMemoryConflictRouterReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_code_counts must contain count values")
    try:
        counts = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_code_counts must contain count values") from exc
    for value in counts:
        if type(value) is not ResearchStrategyCrossTeamMemoryConflictRouterReasonCodeCount:
            raise ValueError("reason_code_counts must contain count values")
        _require_hard_flags("reason_code_count", value)
    if counts != tuple(sorted(counts, key=lambda item: _reason_code_sort_key(item.reason_code))):
        raise ValueError("reason_code_counts must use deterministic sort")
    return counts


def _require_report_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be a tuple of strings")
    try:
        values = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be a tuple of strings") from exc
    if not values:
        raise ValueError("reason_codes must not be empty")
    for reason_code in values:
        _require_public_string("reason_code", reason_code)
    allowed_prefixes = {
        EMPTY_REPORT_REASON_CODE,
        "cross_team_memory_conflict_route_clear",
        "cross_team_memory_conflict_route_watch",
        "cross_team_memory_conflict_route_block",
    }
    for index, reason_code in enumerate(values):
        if index == 0:
            if reason_code not in allowed_prefixes:
                raise ValueError("reason_codes contain unsupported report reason")
        elif reason_code not in REPORT_REASON_PRIORITY:
            raise ValueError("reason_codes contain unsupported report reason")
    if len(values) != len(set(values)):
        raise ValueError("reason_codes must be unique")
    return values


def _require_reason_codes(
    reason_codes: Iterable[str],
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be a tuple of strings")
    try:
        values = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be a tuple of strings") from exc
    if require_nonempty and not values:
        raise ValueError("reason_codes must not be empty")
    for reason_code in values:
        _require_public_string("reason_code", reason_code)
    if len(values) != len(set(values)):
        raise ValueError("reason_codes must be unique")
    for reason_code in values:
        if reason_code not in ROW_REASON_CODES:
            raise ValueError("reason_codes contain unsupported row reason")
    return values


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(COUNT_QUANTUM)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != value:
        raise ValueError(f"{field_name} must be integral")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(RATIO_QUANTUM)
    if normalized < ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(RATIO_QUANTUM)
    if normalized < ZERO_RATIO or normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    with localcontext(DECIMAL_CONTEXT):
        return +value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in (
        RESEARCH_STRATEGY_CROSS_TEAM_MEMORY_CONFLICT_ROUTER_STATUSES
    ):
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_safe_label(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if _contains_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} must be public-safe")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")


def _require_exact_type(value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"value must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")


def _derived_validation_digest(
    report: ResearchStrategyCrossTeamMemoryConflictRouterReport,
) -> str:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be an object")
    return _payload_validation_digest(payload)


def _payload_validation_digest(payload: dict[str, Any]) -> str:
    material = _strip_digest(payload)
    encoded = json.dumps(
        material,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _strip_digest(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _strip_digest(item)
            for key, item in value.items()
            if key != "derived_validation_digest"
        }
    if isinstance(value, list):
        return [_strip_digest(item) for item in value]
    return value


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _reject_public_numeric_values(value: Any) -> None:
    if type(value) in (int, float) or type(value) is Decimal:
        raise ValueError("public payload contains numeric values")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
    elif isinstance(value, list):
        for item in value:
            _reject_public_numeric_values(item)


def _reject_unsafe_public_payload(label: str, value: Any) -> None:
    payload = _json_ready(value)
    if _contains_unsafe_public_payload(payload):
        raise ValueError(f"{label} contains unsafe public payload")


def _contains_unsafe_public_payload(value: Any) -> bool:
    if isinstance(value, dict):
        return any(
            _contains_unsafe_public_fragment(str(key))
            or _contains_unsafe_public_payload(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_unsafe_public_payload(item) for item in value)
    if type(value) is str:
        return _contains_unsafe_public_fragment(value)
    return False


def _contains_unsafe_public_fragment(value: object) -> bool:
    if type(value) is not str:
        return False
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)
