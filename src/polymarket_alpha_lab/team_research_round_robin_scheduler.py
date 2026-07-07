"""Readonly Decimal scheduler for sanitized team research task routing."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json


DEFAULT_TEAM_RESEARCH_ROUND_ROBIN_SCHEDULER_CONFIG_VERSION = (
    "team-research-round-robin-scheduler-v1"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANT = Decimal("0.000001")
SECONDS_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
SECONDS_PER_DAY = Decimal("86400")

PUBLIC_STATUSES = ("pass", "watch", "block")
ROW_REASON_CODES = (
    "task_assignment_pass",
    "task_assignment_watch",
    "task_assignment_block",
    "queue_pressure_low",
    "queue_pressure_watch",
    "queue_pressure_high",
    "sla_low",
    "sla_watch",
    "sla_high",
    "specialist_coverage_strong",
    "specialist_coverage_weak",
    "domain_gap",
    "capacity_gap",
    "round_robin_balanced",
    "team_load_watch",
)
REPORT_REASON_CODES = (
    "team_research_round_robin_pass",
    "team_research_round_robin_watch",
    "team_research_round_robin_block",
    "team_research_round_robin_empty",
)
UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "candidate",
    "market",
    "slug",
    "question",
    "source",
    " ref",
    "ref:",
    "url",
    "dsn",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "position",
    "buy",
    "sell",
    "recommend",
    "database",
    "postgres",
    "supabase",
    "persist",
    "mutation",
    "network",
    "signing",
)

__all__ = (
    "DEFAULT_TEAM_RESEARCH_ROUND_ROBIN_SCHEDULER_CONFIG_VERSION",
    "TeamResearchRoundRobinSchedulerConfig",
    "TeamResearchRoundRobinTaskInput",
    "TeamResearchRoundRobinTeamCoverageInput",
    "TeamResearchRoundRobinSchedulerRow",
    "TeamResearchRoundRobinSchedulerReport",
    "build_team_research_round_robin_scheduler",
)


@dataclass(frozen=True)
class TeamResearchRoundRobinSchedulerConfig:
    config_version: str = DEFAULT_TEAM_RESEARCH_ROUND_ROBIN_SCHEDULER_CONFIG_VERSION
    queue_priority_weight: Decimal = Decimal("0.550000")
    sla_priority_weight: Decimal = Decimal("0.450000")
    sla_watch_window_seconds: Decimal = Decimal("86400.000000")
    watch_queue_pressure_score: Decimal = Decimal("0.500000")
    high_queue_pressure_score: Decimal = Decimal("0.850000")
    watch_sla_risk_score: Decimal = Decimal("0.500000")
    high_sla_risk_score: Decimal = Decimal("0.850000")
    watch_priority_floor: Decimal = Decimal("0.500000")
    watch_team_load_ratio: Decimal = Decimal("0.750000")
    min_specialist_coverage_score: Decimal = Decimal("0.600000")
    strong_specialist_coverage_score: Decimal = Decimal("0.800000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("TeamResearchRoundRobinSchedulerConfig does not support subclassing")

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        for field_name in (
            "queue_priority_weight",
            "sla_priority_weight",
            "watch_queue_pressure_score",
            "high_queue_pressure_score",
            "watch_sla_risk_score",
            "high_sla_risk_score",
            "watch_priority_floor",
            "watch_team_load_ratio",
            "min_specialist_coverage_score",
            "strong_specialist_coverage_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "sla_watch_window_seconds",
            _normalize_positive_seconds(
                "sla_watch_window_seconds",
                self.sla_watch_window_seconds,
            ),
        )
        _validate_config(self)
        _require_hard_flags("TeamResearchRoundRobinSchedulerConfig", self)
        _reject_unsafe_public_payload(
            "TeamResearchRoundRobinSchedulerConfig",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamResearchRoundRobinTaskInput:
    work_item_id: str
    domain_id: str
    queued_at: datetime
    due_at: datetime
    queue_pressure_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("TeamResearchRoundRobinTaskInput does not support subclassing")

    def __post_init__(self) -> None:
        for field_name in ("work_item_id", "domain_id"):
            object.__setattr__(
                self,
                field_name,
                _require_public_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "queued_at", _as_utc("queued_at", self.queued_at))
        object.__setattr__(self, "due_at", _as_utc("due_at", self.due_at))
        if self.due_at < self.queued_at:
            raise ValueError("due_at must not be before queued_at")
        object.__setattr__(
            self,
            "queue_pressure_score",
            _normalize_ratio("queue_pressure_score", self.queue_pressure_score),
        )
        _require_hard_flags("TeamResearchRoundRobinTaskInput", self)
        _reject_unsafe_public_payload(
            "TeamResearchRoundRobinTaskInput",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamResearchRoundRobinTeamCoverageInput:
    team_id: str
    domain_id: str
    specialist_coverage_score: Decimal
    specialist_coverage_count: Decimal
    active_work_count: Decimal
    max_work_count: Decimal
    rotation_rank: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "TeamResearchRoundRobinTeamCoverageInput does not support subclassing",
        )

    def __post_init__(self) -> None:
        for field_name in ("team_id", "domain_id"):
            object.__setattr__(
                self,
                field_name,
                _require_public_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "specialist_coverage_score",
            _normalize_ratio("specialist_coverage_score", self.specialist_coverage_score),
        )
        for field_name in (
            "specialist_coverage_count",
            "active_work_count",
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
            "max_work_count",
            _normalize_positive_integral_decimal("max_work_count", self.max_work_count),
        )
        object.__setattr__(
            self,
            "rotation_rank",
            _normalize_positive_integral_decimal("rotation_rank", self.rotation_rank),
        )
        if self.active_work_count > self.max_work_count:
            raise ValueError("active_work_count must not exceed max_work_count")
        _require_hard_flags("TeamResearchRoundRobinTeamCoverageInput", self)
        _reject_unsafe_public_payload(
            "TeamResearchRoundRobinTeamCoverageInput",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamResearchRoundRobinSchedulerRow:
    rank: Decimal
    work_item_id: str
    domain_id: str
    assigned_team_id: str | None
    assignment_status: str
    queue_age_seconds: Decimal
    queue_pressure_score: Decimal
    sla_seconds_remaining: Decimal
    sla_risk_score: Decimal
    task_priority_score: Decimal
    specialist_coverage_score: Decimal
    specialist_coverage_count: Decimal
    team_load_ratio: Decimal
    team_remaining_capacity_count: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("TeamResearchRoundRobinSchedulerRow does not support subclassing")

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "rank",
            _normalize_positive_integral_decimal("rank", self.rank),
        )
        for field_name in ("work_item_id", "domain_id"):
            object.__setattr__(
                self,
                field_name,
                _require_public_string(field_name, getattr(self, field_name)),
            )
        if self.assigned_team_id is not None:
            object.__setattr__(
                self,
                "assigned_team_id",
                _require_public_string("assigned_team_id", self.assigned_team_id),
            )
        _require_public_status("assignment_status", self.assignment_status)
        for field_name in (
            "queue_pressure_score",
            "sla_risk_score",
            "task_priority_score",
            "specialist_coverage_score",
            "team_load_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("queue_age_seconds", "sla_seconds_remaining"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_seconds(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "specialist_coverage_count",
            "team_remaining_capacity_count",
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
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        if self.assignment_status == "block" and self.assigned_team_id is not None:
            raise ValueError("assigned_team_id must be omitted for block rows")
        if self.assignment_status != "block" and self.assigned_team_id is None:
            raise ValueError("assigned_team_id is required for assigned rows")
        _require_hard_flags("TeamResearchRoundRobinSchedulerRow", self)
        _reject_unsafe_public_payload(
            "TeamResearchRoundRobinSchedulerRow",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamResearchRoundRobinSchedulerReport:
    generated_at: datetime
    config_version: str
    report_status: str
    work_item_count: Decimal
    assigned_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    team_count: Decimal
    domain_count: Decimal
    rows: tuple[TeamResearchRoundRobinSchedulerRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("TeamResearchRoundRobinSchedulerReport does not support subclassing")

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        _require_public_status("report_status", self.report_status)
        for field_name in (
            "work_item_count",
            "assigned_count",
            "pass_count",
            "watch_count",
            "block_count",
            "team_count",
            "domain_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _require_sha256_digest(
            "derived_validation_digest",
            self.derived_validation_digest,
        )
        _require_hard_flags("TeamResearchRoundRobinSchedulerReport", self)
        _reject_unsafe_public_payload(
            "TeamResearchRoundRobinSchedulerReport",
            _payload_value(asdict(self)),
        )
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload("TeamResearchRoundRobinSchedulerReport.payload", payload)
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_team_research_round_robin_scheduler(
    work_items: object,
    *,
    team_coverages: object,
    config: TeamResearchRoundRobinSchedulerConfig,
    generated_at: datetime,
) -> TeamResearchRoundRobinSchedulerReport:
    if type(config) is not TeamResearchRoundRobinSchedulerConfig:
        raise ValueError("config must be a TeamResearchRoundRobinSchedulerConfig")
    _require_hard_flags("TeamResearchRoundRobinSchedulerConfig", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    items = _normalize_work_items(work_items)
    coverages = _normalize_team_coverages(team_coverages)
    rows = _build_rows(
        items=items,
        coverages=coverages,
        config=config,
        generated_at=generated_at_utc,
    )
    values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "report_status": _report_status(rows),
        "work_item_count": _count(len(items)),
        "assigned_count": _count(sum(1 for row in rows if row.assigned_team_id is not None)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "team_count": _count(len({coverage.team_id for coverage in coverages})),
        "domain_count": _count(
            len({item.domain_id for item in items} | {coverage.domain_id for coverage in coverages}),
        ),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _derived_validation_digest(values)
    return TeamResearchRoundRobinSchedulerReport(**values)


def _build_rows(
    *,
    items: tuple[TeamResearchRoundRobinTaskInput, ...],
    coverages: tuple[TeamResearchRoundRobinTeamCoverageInput, ...],
    config: TeamResearchRoundRobinSchedulerConfig,
    generated_at: datetime,
) -> tuple[TeamResearchRoundRobinSchedulerRow, ...]:
    assigned_counts: dict[tuple[str, str], Decimal] = {}
    rows: list[TeamResearchRoundRobinSchedulerRow] = []
    for item in _sorted_work_items(items, config, generated_at):
        if item.queued_at > generated_at:
            raise ValueError("queued_at must not be after generated_at")
        rows.append(
            _row_for_item(
                rank=_count(len(rows) + 1),
                item=item,
                coverages=coverages,
                assigned_counts=assigned_counts,
                config=config,
                generated_at=generated_at,
            ),
        )
    return tuple(rows)


def _row_for_item(
    *,
    rank: Decimal,
    item: TeamResearchRoundRobinTaskInput,
    coverages: tuple[TeamResearchRoundRobinTeamCoverageInput, ...],
    assigned_counts: dict[tuple[str, str], Decimal],
    config: TeamResearchRoundRobinSchedulerConfig,
    generated_at: datetime,
) -> TeamResearchRoundRobinSchedulerRow:
    domain_coverages = tuple(
        coverage for coverage in coverages if coverage.domain_id == item.domain_id
    )
    eligible = tuple(
        coverage
        for coverage in domain_coverages
        if _has_expert_coverage(coverage, config)
        and _remaining_capacity(coverage, assigned_counts) > ZERO
    )
    queue_age_seconds = _seconds_between(item.queued_at, generated_at)
    sla_seconds_remaining = _seconds_remaining(generated_at, item.due_at)
    sla_risk_score = _sla_risk_score(sla_seconds_remaining, config)
    priority_score = _task_priority_score(item, sla_risk_score, config)
    if not eligible:
        best = _best_block_context(domain_coverages, assigned_counts)
        reasons = _blocked_reason_codes(
            item=item,
            best=best,
            priority_score=priority_score,
            sla_risk_score=sla_risk_score,
            config=config,
        )
        return TeamResearchRoundRobinSchedulerRow(
            rank=rank,
            work_item_id=item.work_item_id,
            domain_id=item.domain_id,
            assigned_team_id=None,
            assignment_status="block",
            queue_age_seconds=queue_age_seconds,
            queue_pressure_score=item.queue_pressure_score,
            sla_seconds_remaining=sla_seconds_remaining,
            sla_risk_score=sla_risk_score,
            task_priority_score=priority_score,
            specialist_coverage_score=ZERO if best is None else best.specialist_coverage_score,
            specialist_coverage_count=ZERO if best is None else best.specialist_coverage_count,
            team_load_ratio=ZERO if best is None else _load_ratio(best, assigned_counts),
            team_remaining_capacity_count=ZERO,
            reason_codes=reasons,
        )
    assigned = _select_team(eligible, assigned_counts)
    key = (assigned.team_id, assigned.domain_id)
    assigned_counts[key] = assigned_counts.get(key, ZERO) + _count(1)
    status = _assignment_status(
        priority_score=priority_score,
        coverage=assigned,
        load_ratio=_load_ratio(assigned, assigned_counts),
        config=config,
    )
    return TeamResearchRoundRobinSchedulerRow(
        rank=rank,
        work_item_id=item.work_item_id,
        domain_id=item.domain_id,
        assigned_team_id=assigned.team_id,
        assignment_status=status,
        queue_age_seconds=queue_age_seconds,
        queue_pressure_score=item.queue_pressure_score,
        sla_seconds_remaining=sla_seconds_remaining,
        sla_risk_score=sla_risk_score,
        task_priority_score=priority_score,
        specialist_coverage_score=assigned.specialist_coverage_score,
        specialist_coverage_count=assigned.specialist_coverage_count,
        team_load_ratio=_load_ratio_before_latest(assigned, assigned_counts),
        team_remaining_capacity_count=_remaining_capacity(assigned, assigned_counts),
        reason_codes=_assigned_reason_codes(
            item=item,
            status=status,
            coverage=assigned,
            eligible_count=_count(len(eligible)),
            priority_score=priority_score,
            sla_risk_score=sla_risk_score,
            load_ratio=_load_ratio(assigned, assigned_counts),
            config=config,
        ),
    )


def _sorted_work_items(
    items: tuple[TeamResearchRoundRobinTaskInput, ...],
    config: TeamResearchRoundRobinSchedulerConfig,
    generated_at: datetime,
) -> tuple[TeamResearchRoundRobinTaskInput, ...]:
    return tuple(
        sorted(
            items,
            key=lambda item: (
                -_task_priority_score(item, _sla_risk_score(_seconds_remaining(generated_at, item.due_at), config), config),
                item.domain_id,
                item.work_item_id,
            ),
        ),
    )


def _select_team(
    coverages: tuple[TeamResearchRoundRobinTeamCoverageInput, ...],
    assigned_counts: dict[tuple[str, str], Decimal],
) -> TeamResearchRoundRobinTeamCoverageInput:
    return min(
        coverages,
        key=lambda coverage: (
            _load_ratio(coverage, assigned_counts),
            -coverage.specialist_coverage_score,
            coverage.rotation_rank,
            coverage.team_id,
        ),
    )


def _best_block_context(
    coverages: tuple[TeamResearchRoundRobinTeamCoverageInput, ...],
    assigned_counts: dict[tuple[str, str], Decimal],
) -> TeamResearchRoundRobinTeamCoverageInput | None:
    if not coverages:
        return None
    return min(
        coverages,
        key=lambda coverage: (
            -coverage.specialist_coverage_score,
            _load_ratio(coverage, assigned_counts),
            coverage.rotation_rank,
            coverage.team_id,
        ),
    )


def _has_expert_coverage(
    coverage: TeamResearchRoundRobinTeamCoverageInput,
    config: TeamResearchRoundRobinSchedulerConfig,
) -> bool:
    return (
        coverage.specialist_coverage_count > ZERO
        and coverage.specialist_coverage_score >= config.min_specialist_coverage_score
    )


def _remaining_capacity(
    coverage: TeamResearchRoundRobinTeamCoverageInput,
    assigned_counts: dict[tuple[str, str], Decimal],
) -> Decimal:
    key = (coverage.team_id, coverage.domain_id)
    used = coverage.active_work_count + assigned_counts.get(key, ZERO)
    remaining = coverage.max_work_count - used
    if remaining < ZERO:
        return ZERO
    return remaining.quantize(COUNT_QUANT)


def _load_ratio(
    coverage: TeamResearchRoundRobinTeamCoverageInput,
    assigned_counts: dict[tuple[str, str], Decimal],
) -> Decimal:
    key = (coverage.team_id, coverage.domain_id)
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            (coverage.active_work_count + assigned_counts.get(key, ZERO))
            / coverage.max_work_count,
        )


def _load_ratio_before_latest(
    coverage: TeamResearchRoundRobinTeamCoverageInput,
    assigned_counts: dict[tuple[str, str], Decimal],
) -> Decimal:
    key = (coverage.team_id, coverage.domain_id)
    latest = assigned_counts.get(key, ZERO)
    previous = latest - _count(1)
    if previous < ZERO:
        previous = ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio((coverage.active_work_count + previous) / coverage.max_work_count)


def _assignment_status(
    *,
    priority_score: Decimal,
    coverage: TeamResearchRoundRobinTeamCoverageInput,
    load_ratio: Decimal,
    config: TeamResearchRoundRobinSchedulerConfig,
) -> str:
    if (
        priority_score >= config.watch_priority_floor
        or coverage.specialist_coverage_score < config.strong_specialist_coverage_score
        or load_ratio >= config.watch_team_load_ratio
    ):
        return "watch"
    return "pass"


def _assigned_reason_codes(
    *,
    item: TeamResearchRoundRobinTaskInput,
    status: str,
    coverage: TeamResearchRoundRobinTeamCoverageInput,
    eligible_count: Decimal,
    priority_score: Decimal,
    sla_risk_score: Decimal,
    load_ratio: Decimal,
    config: TeamResearchRoundRobinSchedulerConfig,
) -> tuple[str, ...]:
    reasons = [
        f"task_assignment_{status}",
        _queue_pressure_reason(item.queue_pressure_score, config),
        _sla_reason(sla_risk_score, config),
        _coverage_reason(coverage.specialist_coverage_score, config),
    ]
    if eligible_count > ONE:
        reasons.append("round_robin_balanced")
    if load_ratio >= config.watch_team_load_ratio or priority_score >= config.watch_priority_floor:
        reasons.append("team_load_watch")
    return _dedupe_reasons(tuple(reasons), ROW_REASON_CODES)


def _blocked_reason_codes(
    *,
    item: TeamResearchRoundRobinTaskInput,
    best: TeamResearchRoundRobinTeamCoverageInput | None,
    priority_score: Decimal,
    sla_risk_score: Decimal,
    config: TeamResearchRoundRobinSchedulerConfig,
) -> tuple[str, ...]:
    reasons = [
        "task_assignment_block",
        _queue_pressure_reason(item.queue_pressure_score, config),
        _sla_reason(sla_risk_score, config),
    ]
    if best is None or not _has_expert_coverage(best, config):
        reasons.append("domain_gap")
    else:
        reasons.append("capacity_gap")
    if priority_score >= config.watch_priority_floor:
        reasons.append("team_load_watch")
    return _dedupe_reasons(tuple(reasons), ROW_REASON_CODES)


def _queue_pressure_reason(
    queue_pressure_score: Decimal,
    config: TeamResearchRoundRobinSchedulerConfig,
) -> str:
    if queue_pressure_score >= config.high_queue_pressure_score:
        return "queue_pressure_high"
    if queue_pressure_score >= config.watch_queue_pressure_score:
        return "queue_pressure_watch"
    return "queue_pressure_low"


def _sla_reason(sla_risk_score: Decimal, config: TeamResearchRoundRobinSchedulerConfig) -> str:
    if sla_risk_score >= config.high_sla_risk_score:
        return "sla_high"
    if sla_risk_score >= config.watch_sla_risk_score:
        return "sla_watch"
    return "sla_low"


def _coverage_reason(
    specialist_coverage_score: Decimal,
    config: TeamResearchRoundRobinSchedulerConfig,
) -> str:
    if specialist_coverage_score >= config.strong_specialist_coverage_score:
        return "specialist_coverage_strong"
    return "specialist_coverage_weak"


def _task_priority_score(
    item: TeamResearchRoundRobinTaskInput,
    sla_risk_score: Decimal,
    config: TeamResearchRoundRobinSchedulerConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            item.queue_pressure_score * config.queue_priority_weight
            + sla_risk_score * config.sla_priority_weight,
        )


def _sla_risk_score(
    sla_seconds_remaining: Decimal,
    config: TeamResearchRoundRobinSchedulerConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        if sla_seconds_remaining <= ZERO:
            return ONE
        return _clamp_ratio(ONE - sla_seconds_remaining / config.sla_watch_window_seconds)


def _seconds_remaining(start: datetime, due_at: datetime) -> Decimal:
    if due_at <= start:
        return ZERO
    return _seconds_between(start, due_at)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    total_microseconds = (
        (delta.days * int(SECONDS_PER_DAY) + delta.seconds) * int(MICROSECONDS_PER_SECOND)
        + delta.microseconds
    )
    if total_microseconds < 0:
        raise ValueError("datetime range must not be negative")
    with localcontext(DECIMAL_CONTEXT):
        return (Decimal(total_microseconds) / MICROSECONDS_PER_SECOND).quantize(
            SECONDS_QUANT,
        )


def _report_status(rows: tuple[TeamResearchRoundRobinSchedulerRow, ...]) -> str:
    if any(row.assignment_status == "block" for row in rows):
        return "block"
    if any(row.assignment_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[TeamResearchRoundRobinSchedulerRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("team_research_round_robin_empty",)
    candidate_codes = {
        "team_research_round_robin_pass": any(row.assignment_status == "pass" for row in rows),
        "team_research_round_robin_watch": any(row.assignment_status == "watch" for row in rows),
        "team_research_round_robin_block": any(row.assignment_status == "block" for row in rows),
    }
    return tuple(code for code in REPORT_REASON_CODES[:-1] if candidate_codes.get(code, False))


def _status_count(rows: tuple[TeamResearchRoundRobinSchedulerRow, ...], status: str) -> Decimal:
    return _count(sum(1 for row in rows if row.assignment_status == status))


def _normalize_work_items(value: object) -> tuple[TeamResearchRoundRobinTaskInput, ...]:
    if isinstance(value, (str, bytes)) or not hasattr(value, "__iter__"):
        raise ValueError("work_items must be an iterable")
    items = tuple(value)
    seen_ids: set[str] = set()
    for item in items:
        if type(item) is not TeamResearchRoundRobinTaskInput:
            raise ValueError("work_items must contain TeamResearchRoundRobinTaskInput")
        _require_hard_flags("TeamResearchRoundRobinTaskInput", item)
        if item.work_item_id in seen_ids:
            raise ValueError("work_items must not contain duplicate work_item_id")
        seen_ids.add(item.work_item_id)
    return items


def _normalize_team_coverages(
    value: object,
) -> tuple[TeamResearchRoundRobinTeamCoverageInput, ...]:
    if isinstance(value, (str, bytes)) or not hasattr(value, "__iter__"):
        raise ValueError("team_coverages must be an iterable")
    coverages = tuple(value)
    seen_keys: set[tuple[str, str]] = set()
    for coverage in coverages:
        if type(coverage) is not TeamResearchRoundRobinTeamCoverageInput:
            raise ValueError(
                "team_coverages must contain TeamResearchRoundRobinTeamCoverageInput",
            )
        _require_hard_flags("TeamResearchRoundRobinTeamCoverageInput", coverage)
        key = (coverage.team_id, coverage.domain_id)
        if key in seen_keys:
            raise ValueError("team_coverages must not contain duplicate team/domain")
        seen_keys.add(key)
    return tuple(
        sorted(
            coverages,
            key=lambda coverage: (
                coverage.domain_id,
                coverage.rotation_rank,
                coverage.team_id,
            ),
        ),
    )


def _normalize_rows(value: object) -> tuple[TeamResearchRoundRobinSchedulerRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    seen_ids: set[str] = set()
    for row in value:
        if type(row) is not TeamResearchRoundRobinSchedulerRow:
            raise ValueError("rows must contain TeamResearchRoundRobinSchedulerRow")
        _require_hard_flags("TeamResearchRoundRobinSchedulerRow", row)
        if row.work_item_id in seen_ids:
            raise ValueError("rows must not contain duplicate work_item_id")
        seen_ids.add(row.work_item_id)
    return value


def _validate_config(config: TeamResearchRoundRobinSchedulerConfig) -> None:
    with localcontext(DECIMAL_CONTEXT):
        weights_total = (
            config.queue_priority_weight + config.sla_priority_weight
        ).quantize(SCORE_QUANT)
    if weights_total != ONE:
        raise ValueError("scheduler weights must sum to 1.000000")
    if config.watch_queue_pressure_score > config.high_queue_pressure_score:
        raise ValueError("watch_queue_pressure_score must not exceed high_queue_pressure_score")
    if config.watch_sla_risk_score > config.high_sla_risk_score:
        raise ValueError("watch_sla_risk_score must not exceed high_sla_risk_score")
    if config.min_specialist_coverage_score > config.strong_specialist_coverage_score:
        raise ValueError(
            "min_specialist_coverage_score must not exceed strong_specialist_coverage_score",
        )


def _validate_report_consistency(report: TeamResearchRoundRobinSchedulerReport) -> None:
    rows = report.rows
    if report.work_item_count != _count(len(rows)):
        raise ValueError("work_item_count must match rows")
    if report.assigned_count != _count(sum(1 for row in rows if row.assigned_team_id is not None)):
        raise ValueError("assigned_count must match rows")
    if (
        report.pass_count != _status_count(rows, "pass")
        or report.watch_count != _status_count(rows, "watch")
        or report.block_count != _status_count(rows, "block")
    ):
        raise ValueError("status counts must match rows")
    if report.pass_count + report.watch_count + report.block_count != report.work_item_count:
        raise ValueError("status counts must sum to work_item_count")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    _validate_rows_ranked(rows)
    if report.derived_validation_digest != _derived_validation_digest(asdict(report)):
        raise ValueError("derived_validation_digest must match report fields")


def _validate_rows_ranked(rows: tuple[TeamResearchRoundRobinSchedulerRow, ...]) -> None:
    expected_ranks = tuple(_count(index) for index in range(1, len(rows) + 1))
    actual_ranks = tuple(row.rank for row in rows)
    if actual_ranks != expected_ranks:
        raise ValueError("rows must have sequential ranks")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    normalized = value.strip()
    _reject_unsafe_public_text(field_name, normalized)
    return normalized


def _require_public_status(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if value not in PUBLIC_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    normalized = tuple(_require_public_string(field_name, item) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    if any(item not in allowed for item in normalized):
        raise ValueError(f"{field_name} must contain known reason codes")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(SCORE_QUANT)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _normalize_nonnegative_seconds(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(SECONDS_QUANT)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _normalize_positive_seconds(field_name: str, value: object) -> Decimal:
    value = _normalize_nonnegative_seconds(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return value.quantize(COUNT_QUANT)


def _normalize_positive_integral_decimal(field_name: str, value: object) -> Decimal:
    value = _normalize_nonnegative_integral_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANT)


def _clamp_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return min(ONE, max(ZERO, value)).quantize(SCORE_QUANT)


def _dedupe_reasons(
    reason_codes: tuple[str, ...],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    selected = tuple(code for code in allowed if code in reason_codes)
    if not selected:
        raise ValueError("reason_codes must not be empty")
    return selected


def _require_sha256_digest(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {field_name}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {field_name}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {field_name}")


def _payload_value(value: object) -> object:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _payload_value(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if value is None or type(value) in (str, int, bool):
        return value
    raise ValueError("payload contains unsupported value")


def _derived_validation_digest(values: dict[str, object]) -> str:
    digest_payload = {
        key: _payload_value(item)
        for key, item in values.items()
        if key != "derived_validation_digest"
    }
    _reject_unsafe_public_payload("derived validation digest payload", digest_payload)
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public payload in {label}")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is float:
        raise ValueError(f"unsafe public payload in {label}")
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"unsafe public payload in {label}")
