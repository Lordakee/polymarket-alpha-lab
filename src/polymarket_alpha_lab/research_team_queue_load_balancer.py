"""Deterministic research queue load reports for specialist teams."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any


DEFAULT_RESEARCH_TEAM_QUEUE_LOAD_BALANCER_CONFIG_VERSION = (
    "research-team-queue-load-balancer-v0"
)
DEFAULT_RESEARCH_TEAM_IDS = (
    "politics",
    "crypto",
    "macro",
    "gold",
    "soccer",
    "basketball",
)
PUBLIC_STATUSES = ("pass", "watch", "block")
NEXT_STEPS = {
    "pass": "archive_pass_research_team_queue_load",
    "watch": "review_watch_research_team_queue_load",
    "block": "block_research_team_queue_load",
}
REASON_CODES = {
    "pass": "research_team_queue_load_balancer_load_pass",
    "watch": "research_team_queue_load_balancer_load_watch",
    "block": "research_team_queue_load_balancer_load_block",
}
ROUTE_REASON_CODE = "research_team_queue_load_balancer_route_assigned"
THIN_EVIDENCE_REASON_CODE = "research_team_queue_load_balancer_thin_evidence"
STALE_QUEUE_REASON_CODE = "research_team_queue_load_balancer_stale_queue"
UNKNOWN_GROUP_REASON_CODE = "research_team_queue_load_balancer_unknown_group"
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DEFAULT_CAPACITY_POINTS = Decimal("10.000000")
SIX_PLACES = Decimal("0.000001")
FLAG_NAMES = ("paper_only", "report_only", "readonly")
UNSAFE_TEXT_FRAGMENTS = (
    "raw" + "_" + "candidate" + "_" + "id",
    "raw" + "-" + "candidate",
    "raw" + "-" + "crypto",
    "raw" + "-" + "politics",
    "raw" + "-" + "macro",
    "raw" + "-" + "gold",
    "raw" + "-" + "soccer",
    "raw" + "-" + "basketball",
    "abc123",
    "0xabc",
    "market" + "_" + "id",
    "market" + "_" + "slug",
    "secret" + "-" + "que" + "stion",
    "source" + "_" + "ref",
    "source" + "_" + "url",
    "source" + "_" + "text",
    "source.example",
    "https://",
    "http://",
    "postgres://",
    "postgresql://",
    "data" + "base" + "_" + "url",
    "d" + "sn",
    "ta" + "ble",
    "to" + "ken",
    "wal" + "let",
    "or" + "der",
    "tra" + "de",
    "po" + "sition",
    "b" + "uy",
    "s" + "ell",
    "rec" + "ommend",
    "credential",
    "secret",
    "password",
    "private_key",
    "api_key",
)


@dataclass(frozen=True)
class ResearchTeamQueueLoadBalancerConfig:
    config_version: str = DEFAULT_RESEARCH_TEAM_QUEUE_LOAD_BALANCER_CONFIG_VERSION
    team_ids: tuple[str, ...] = DEFAULT_RESEARCH_TEAM_IDS
    pass_load_ratio_threshold: Decimal = Decimal("0.800000")
    block_load_ratio_threshold: Decimal = Decimal("1.000000")
    min_evidence_count: Decimal = Decimal("2.000000")
    stale_queue_seconds: Decimal = Decimal("7200.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamQueueLoadBalancerConfig:
            raise TypeError("ResearchTeamQueueLoadBalancerConfig does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamQueueLoadBalancerConfig:
            raise ValueError("config must be exactly ResearchTeamQueueLoadBalancerConfig")
        _require_public_string("config_version", self.config_version)
        object.__setattr__(self, "team_ids", _normalize_team_ids("team_ids", self.team_ids))
        object.__setattr__(
            self,
            "pass_load_ratio_threshold",
            _require_nonnegative_decimal(
                "pass_load_ratio_threshold",
                self.pass_load_ratio_threshold,
            ),
        )
        object.__setattr__(
            self,
            "block_load_ratio_threshold",
            _require_nonnegative_decimal(
                "block_load_ratio_threshold",
                self.block_load_ratio_threshold,
            ),
        )
        if self.pass_load_ratio_threshold > self.block_load_ratio_threshold:
            raise ValueError(
                "block_load_ratio_threshold must be at least pass_load_ratio_threshold",
            )
        object.__setattr__(
            self,
            "min_evidence_count",
            _require_nonnegative_count_decimal("min_evidence_count", self.min_evidence_count),
        )
        object.__setattr__(
            self,
            "stale_queue_seconds",
            _require_nonnegative_decimal("stale_queue_seconds", self.stale_queue_seconds),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamQueueLoadBalancerTeamLoad:
    team_id: str
    open_load_points: Decimal
    capacity_points: Decimal
    open_item_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamQueueLoadBalancerTeamLoad:
            raise TypeError("ResearchTeamQueueLoadBalancerTeamLoad does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamQueueLoadBalancerTeamLoad:
            raise ValueError("team load must be exactly ResearchTeamQueueLoadBalancerTeamLoad")
        object.__setattr__(self, "team_id", _require_team_id("team_id", self.team_id))
        for field_name in ("open_load_points", "capacity_points", "open_item_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "open_item_count",
            _require_nonnegative_count_decimal("open_item_count", self.open_item_count),
        )
        if self.capacity_points <= ZERO:
            raise ValueError("capacity_points must be positive")
        _require_hard_flags("team load", self)


@dataclass(frozen=True)
class ResearchTeamQueueLoadBalancerInputRow:
    private_queue_key: str
    research_group: str
    queued_at: datetime
    effort_points: Decimal
    priority_score: Decimal
    evidence_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamQueueLoadBalancerInputRow:
            raise TypeError("ResearchTeamQueueLoadBalancerInputRow does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamQueueLoadBalancerInputRow:
            raise ValueError("input row must be exactly ResearchTeamQueueLoadBalancerInputRow")
        _require_private_key("private_queue_key", self.private_queue_key)
        object.__setattr__(self, "research_group", _require_team_id("research_group", self.research_group))
        object.__setattr__(self, "queued_at", _as_utc("queued_at", self.queued_at))
        object.__setattr__(
            self,
            "effort_points",
            _require_nonnegative_decimal("effort_points", self.effort_points),
        )
        if self.effort_points <= ZERO:
            raise ValueError("effort_points must be positive")
        object.__setattr__(
            self,
            "priority_score",
            _require_ratio_decimal("priority_score", self.priority_score),
        )
        object.__setattr__(
            self,
            "evidence_count",
            _require_nonnegative_count_decimal("evidence_count", self.evidence_count),
        )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class ResearchTeamQueueLoadBalancerTeamRow:
    team_id: str
    open_load_points: Decimal
    open_item_count: Decimal
    assigned_item_count: Decimal
    assigned_load_points: Decimal
    projected_load_points: Decimal
    projected_load_ratio: Decimal
    team_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamQueueLoadBalancerTeamRow:
            raise TypeError("ResearchTeamQueueLoadBalancerTeamRow does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamQueueLoadBalancerTeamRow:
            raise ValueError("team row must be exactly ResearchTeamQueueLoadBalancerTeamRow")
        object.__setattr__(self, "team_id", _require_team_id("team_id", self.team_id))
        for field_name in (
            "open_load_points",
            "open_item_count",
            "assigned_item_count",
            "assigned_load_points",
            "projected_load_points",
            "projected_load_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("open_item_count", "assigned_item_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("team_status", self.team_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.projected_load_points != _decimal(self.open_load_points + self.assigned_load_points):
            raise ValueError("projected_load_points must match load points")
        _require_hard_flags("team row", self)
        _reject_unsafe_public_payload("team row", self)


@dataclass(frozen=True)
class ResearchTeamQueueLoadBalancerRoutedRow:
    public_queue_key: str
    research_group: str
    routed_team_id: str
    queued_age_seconds: Decimal
    effort_points: Decimal
    priority_score: Decimal
    evidence_count: Decimal
    assignment_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamQueueLoadBalancerRoutedRow:
            raise TypeError("ResearchTeamQueueLoadBalancerRoutedRow does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamQueueLoadBalancerRoutedRow:
            raise ValueError("routed row must be exactly ResearchTeamQueueLoadBalancerRoutedRow")
        _require_public_digest("public_queue_key", self.public_queue_key)
        object.__setattr__(self, "research_group", _require_team_id("research_group", self.research_group))
        object.__setattr__(self, "routed_team_id", _require_team_id("routed_team_id", self.routed_team_id))
        for field_name in (
            "queued_age_seconds",
            "effort_points",
            "priority_score",
            "evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "priority_score",
            _require_ratio_decimal("priority_score", self.priority_score),
        )
        object.__setattr__(
            self,
            "evidence_count",
            _require_nonnegative_count_decimal("evidence_count", self.evidence_count),
        )
        _require_status("assignment_status", self.assignment_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("routed row", self)
        _reject_unsafe_public_payload("routed row", self)


@dataclass(frozen=True)
class ResearchTeamQueueLoadBalancerReport:
    generated_at: datetime
    config_version: str
    report_status: str
    next_step: str
    team_count: Decimal
    queued_item_count: Decimal
    pass_team_count: Decimal
    watch_team_count: Decimal
    block_team_count: Decimal
    total_open_load_points: Decimal
    total_assigned_load_points: Decimal
    max_projected_load_ratio: Decimal
    team_rows: tuple[ResearchTeamQueueLoadBalancerTeamRow, ...]
    routed_rows: tuple[ResearchTeamQueueLoadBalancerRoutedRow, ...]
    reason_codes: tuple[str, ...]
    public_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamQueueLoadBalancerReport:
            raise TypeError("ResearchTeamQueueLoadBalancerReport does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamQueueLoadBalancerReport:
            raise ValueError("report must be exactly ResearchTeamQueueLoadBalancerReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_status("report_status", self.report_status)
        _require_public_string("next_step", self.next_step)
        for field_name in (
            "team_count",
            "queued_item_count",
            "pass_team_count",
            "watch_team_count",
            "block_team_count",
            "total_open_load_points",
            "total_assigned_load_points",
            "max_projected_load_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "team_count",
            "queued_item_count",
            "pass_team_count",
            "watch_team_count",
            "block_team_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "team_rows", _normalize_team_rows(self.team_rows))
        object.__setattr__(self, "routed_rows", _normalize_routed_rows(self.routed_rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _public_digest_for_report(self)
        if self.public_digest == "":
            object.__setattr__(self, "public_digest", expected_digest)
        elif self.public_digest != expected_digest:
            raise ValueError("public_digest must match report payload")


def build_research_team_queue_load_balancer_report(
    team_loads: list[ResearchTeamQueueLoadBalancerTeamLoad]
    | tuple[ResearchTeamQueueLoadBalancerTeamLoad, ...],
    input_rows: list[ResearchTeamQueueLoadBalancerInputRow]
    | tuple[ResearchTeamQueueLoadBalancerInputRow, ...],
    *,
    config: ResearchTeamQueueLoadBalancerConfig | None = None,
    generated_at: datetime,
) -> ResearchTeamQueueLoadBalancerReport:
    cfg = config or ResearchTeamQueueLoadBalancerConfig()
    if type(cfg) is not ResearchTeamQueueLoadBalancerConfig:
        raise ValueError("config must be a ResearchTeamQueueLoadBalancerConfig")
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    loads = _normalize_loads(team_loads, cfg)
    rows = _normalize_input_rows(input_rows)
    state = {
        team_id: {
            "open": loads[team_id].open_load_points,
            "capacity": loads[team_id].capacity_points,
            "open_items": loads[team_id].open_item_count,
            "assigned": ZERO,
            "assigned_items": ZERO,
        }
        for team_id in cfg.team_ids
    }
    routed_rows: list[ResearchTeamQueueLoadBalancerRoutedRow] = []
    for row in _rank_input_rows(rows):
        routed_team_id = _route_team_id(row, state, cfg)
        state[routed_team_id]["assigned"] = _decimal(
            state[routed_team_id]["assigned"] + row.effort_points,
        )
        state[routed_team_id]["assigned_items"] = _decimal(
            state[routed_team_id]["assigned_items"] + ONE,
        )
        routed_rows.append(_build_routed_row(row, routed_team_id, state, cfg, report_time))

    team_rows = tuple(_build_team_row(team_id, state[team_id], cfg) for team_id in cfg.team_ids)
    report_status = _report_status(team_rows)
    return ResearchTeamQueueLoadBalancerReport(
        generated_at=report_time,
        config_version=cfg.config_version,
        report_status=report_status,
        next_step=NEXT_STEPS[report_status],
        team_count=_count(len(team_rows)),
        queued_item_count=_count(len(routed_rows)),
        pass_team_count=_count(sum(1 for row in team_rows if row.team_status == "pass")),
        watch_team_count=_count(sum(1 for row in team_rows if row.team_status == "watch")),
        block_team_count=_count(sum(1 for row in team_rows if row.team_status == "block")),
        total_open_load_points=_sum_decimal(row.open_load_points for row in team_rows),
        total_assigned_load_points=_sum_decimal(row.assigned_load_points for row in team_rows),
        max_projected_load_ratio=max(
            (row.projected_load_ratio for row in team_rows),
            default=ZERO,
        ),
        team_rows=team_rows,
        routed_rows=tuple(routed_rows),
        reason_codes=(REASON_CODES[report_status],),
    )


def research_team_queue_load_balancer_payload(
    report: ResearchTeamQueueLoadBalancerReport,
) -> dict[str, Any]:
    if type(report) is not ResearchTeamQueueLoadBalancerReport:
        raise ValueError("report must be a ResearchTeamQueueLoadBalancerReport")
    _require_hard_flags("report", report)
    _reject_unsafe_public_payload("report", report)
    payload = _json_ready_decimal_strings(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_payload_flags(payload)
    _validate_payload_digest(payload)
    _reject_unsafe_public_payload("payload", payload)
    return payload


def format_research_team_queue_load_balancer_digest(
    report: ResearchTeamQueueLoadBalancerReport,
) -> str:
    if type(report) is not ResearchTeamQueueLoadBalancerReport:
        raise ValueError("report must be a ResearchTeamQueueLoadBalancerReport")
    _require_hard_flags("report", report)
    _reject_unsafe_public_payload("report", report)
    return (
        "research-team-queue-load-balancer: "
        f"generated_at={report.generated_at.isoformat()} "
        f"status={report.report_status} "
        f"teams={report.team_count} "
        f"queued_items={report.queued_item_count} "
        f"pass={report.pass_team_count} "
        f"watch={report.watch_team_count} "
        f"block={report.block_team_count} "
        f"open_load={report.total_open_load_points} "
        f"assigned_load={report.total_assigned_load_points} "
        f"max_ratio={report.max_projected_load_ratio} "
        f"next_step={report.next_step} "
        f"reason_codes={_codes_value(report.reason_codes)} "
        f"public_digest={report.public_digest} "
        f"paper_only={report.paper_only} "
        f"report_only={report.report_only} "
        f"readonly={report.readonly}\n"
    )


def _build_routed_row(
    row: ResearchTeamQueueLoadBalancerInputRow,
    routed_team_id: str,
    state: dict[str, dict[str, Decimal]],
    cfg: ResearchTeamQueueLoadBalancerConfig,
    generated_at: datetime,
) -> ResearchTeamQueueLoadBalancerRoutedRow:
    projected_ratio = _load_ratio(
        state[routed_team_id]["open"] + state[routed_team_id]["assigned"],
        state[routed_team_id]["capacity"],
    )
    reason_codes = [ROUTE_REASON_CODE]
    if row.evidence_count < cfg.min_evidence_count:
        reason_codes.append(THIN_EVIDENCE_REASON_CODE)
    queued_age_seconds = _seconds_between(generated_at, row.queued_at)
    if queued_age_seconds > cfg.stale_queue_seconds:
        reason_codes.append(STALE_QUEUE_REASON_CODE)
    if row.research_group != routed_team_id:
        reason_codes.append("research_team_queue_load_balancer_rebalanced")
    return ResearchTeamQueueLoadBalancerRoutedRow(
        public_queue_key=_public_queue_key(row.private_queue_key),
        research_group=row.research_group,
        routed_team_id=routed_team_id,
        queued_age_seconds=queued_age_seconds,
        effort_points=row.effort_points,
        priority_score=row.priority_score,
        evidence_count=row.evidence_count,
        assignment_status=_status_from_ratio(projected_ratio, cfg),
        reason_codes=tuple(reason_codes),
    )


def _build_team_row(
    team_id: str,
    values: dict[str, Decimal],
    cfg: ResearchTeamQueueLoadBalancerConfig,
) -> ResearchTeamQueueLoadBalancerTeamRow:
    projected_load_points = _decimal(values["open"] + values["assigned"])
    projected_load_ratio = _load_ratio(projected_load_points, values["capacity"])
    team_status = _status_from_ratio(projected_load_ratio, cfg)
    return ResearchTeamQueueLoadBalancerTeamRow(
        team_id=team_id,
        open_load_points=values["open"],
        open_item_count=values["open_items"],
        assigned_item_count=values["assigned_items"],
        assigned_load_points=values["assigned"],
        projected_load_points=projected_load_points,
        projected_load_ratio=projected_load_ratio,
        team_status=team_status,
        reason_codes=(REASON_CODES[team_status],),
    )


def _route_team_id(
    row: ResearchTeamQueueLoadBalancerInputRow,
    state: dict[str, dict[str, Decimal]],
    cfg: ResearchTeamQueueLoadBalancerConfig,
) -> str:
    if row.research_group in state:
        own_ratio = _load_ratio(
            state[row.research_group]["open"]
            + state[row.research_group]["assigned"]
            + row.effort_points,
            state[row.research_group]["capacity"],
        )
        if own_ratio <= cfg.pass_load_ratio_threshold:
            return row.research_group
    ranked = sorted(
        cfg.team_ids,
        key=lambda team_id: (
            _load_ratio(
                state[team_id]["open"] + state[team_id]["assigned"] + row.effort_points,
                state[team_id]["capacity"],
            ),
            state[team_id]["assigned_items"],
            team_id,
        ),
    )
    return ranked[0]


def _rank_input_rows(
    rows: tuple[ResearchTeamQueueLoadBalancerInputRow, ...],
) -> tuple[ResearchTeamQueueLoadBalancerInputRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                -row.priority_score,
                row.queued_at,
                row.research_group,
                _public_queue_key(row.private_queue_key),
            ),
        ),
    )


def _normalize_loads(
    team_loads: list[ResearchTeamQueueLoadBalancerTeamLoad]
    | tuple[ResearchTeamQueueLoadBalancerTeamLoad, ...],
    cfg: ResearchTeamQueueLoadBalancerConfig,
) -> dict[str, ResearchTeamQueueLoadBalancerTeamLoad]:
    if type(team_loads) not in (list, tuple):
        raise ValueError("team loads must be a list or tuple")
    by_team: dict[str, ResearchTeamQueueLoadBalancerTeamLoad] = {}
    for row in team_loads:
        if type(row) is not ResearchTeamQueueLoadBalancerTeamLoad:
            raise ValueError("team loads must contain ResearchTeamQueueLoadBalancerTeamLoad")
        _require_hard_flags("team load", row)
        if row.team_id not in cfg.team_ids:
            raise ValueError("team loads must use configured team_ids")
        if row.team_id in by_team:
            raise ValueError("team loads must not contain duplicate team_id values")
        by_team[row.team_id] = row
    missing = tuple(team_id for team_id in cfg.team_ids if team_id not in by_team)
    for team_id in missing:
        by_team[team_id] = ResearchTeamQueueLoadBalancerTeamLoad(
            team_id=team_id,
            open_load_points=ZERO,
            capacity_points=DEFAULT_CAPACITY_POINTS,
            open_item_count=ZERO,
        )
    return by_team


def _normalize_input_rows(
    input_rows: list[ResearchTeamQueueLoadBalancerInputRow]
    | tuple[ResearchTeamQueueLoadBalancerInputRow, ...],
) -> tuple[ResearchTeamQueueLoadBalancerInputRow, ...]:
    if type(input_rows) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    rows = tuple(input_rows)
    seen_keys: set[str] = set()
    for row in rows:
        if type(row) is not ResearchTeamQueueLoadBalancerInputRow:
            raise ValueError("input rows must contain ResearchTeamQueueLoadBalancerInputRow")
        _require_hard_flags("input row", row)
        public_key = _public_queue_key(row.private_queue_key)
        if public_key in seen_keys:
            raise ValueError("input rows must not contain duplicate public keys")
        seen_keys.add(public_key)
    return rows


def _normalize_team_rows(
    rows: tuple[ResearchTeamQueueLoadBalancerTeamRow, ...],
) -> tuple[ResearchTeamQueueLoadBalancerTeamRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("team_rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchTeamQueueLoadBalancerTeamRow:
            raise ValueError("team_rows must contain ResearchTeamQueueLoadBalancerTeamRow")
        _require_hard_flags("team row", row)
    return tuple(sorted(rows, key=lambda row: row.team_id))


def _normalize_routed_rows(
    rows: tuple[ResearchTeamQueueLoadBalancerRoutedRow, ...],
) -> tuple[ResearchTeamQueueLoadBalancerRoutedRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("routed_rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchTeamQueueLoadBalancerRoutedRow:
            raise ValueError("routed_rows must contain ResearchTeamQueueLoadBalancerRoutedRow")
        _require_hard_flags("routed row", row)
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                -row.priority_score,
                row.research_group,
                row.routed_team_id,
                row.public_queue_key,
            ),
        ),
    )


def _validate_report(report: ResearchTeamQueueLoadBalancerReport) -> None:
    if report.team_count != _count(len(report.team_rows)):
        raise ValueError("team_count must match team_rows")
    if report.queued_item_count != _count(len(report.routed_rows)):
        raise ValueError("queued_item_count must match routed_rows")
    if report.pass_team_count != _count(sum(1 for row in report.team_rows if row.team_status == "pass")):
        raise ValueError("pass_team_count must match team_rows")
    if report.watch_team_count != _count(sum(1 for row in report.team_rows if row.team_status == "watch")):
        raise ValueError("watch_team_count must match team_rows")
    if report.block_team_count != _count(sum(1 for row in report.team_rows if row.team_status == "block")):
        raise ValueError("block_team_count must match team_rows")
    if report.total_open_load_points != _sum_decimal(row.open_load_points for row in report.team_rows):
        raise ValueError("total_open_load_points must match team_rows")
    if report.total_assigned_load_points != _sum_decimal(
        row.assigned_load_points for row in report.team_rows
    ):
        raise ValueError("total_assigned_load_points must match team_rows")
    expected_max = max((row.projected_load_ratio for row in report.team_rows), default=ZERO)
    if report.max_projected_load_ratio != expected_max:
        raise ValueError("max_projected_load_ratio must match team_rows")
    if report.report_status != _report_status(report.team_rows):
        raise ValueError("report_status must match team_rows")
    if report.next_step != NEXT_STEPS[report.report_status]:
        raise ValueError("next_step must match report_status")
    if report.reason_codes != (REASON_CODES[report.report_status],):
        raise ValueError("reason_codes must match report_status")


def _report_status(rows: tuple[ResearchTeamQueueLoadBalancerTeamRow, ...]) -> str:
    if any(row.team_status == "block" for row in rows):
        return "block"
    if any(row.team_status == "watch" for row in rows):
        return "watch"
    if rows:
        return "pass"
    return "block"


def _status_from_ratio(
    load_ratio: Decimal,
    cfg: ResearchTeamQueueLoadBalancerConfig,
) -> str:
    if load_ratio > cfg.block_load_ratio_threshold:
        return "block"
    if load_ratio > cfg.pass_load_ratio_threshold:
        return "watch"
    return "pass"


def _load_ratio(load_points: Decimal, capacity_points: Decimal) -> Decimal:
    if capacity_points <= ZERO:
        raise ValueError("capacity_points must be positive")
    return _decimal(load_points / capacity_points)


def _sum_decimal(values: Any) -> Decimal:
    total = ZERO
    for value in values:
        total = _decimal(total + value)
    return total


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    return _decimal(Decimal(str((later - earlier).total_seconds())))


def _count(value: int) -> Decimal:
    return _decimal(Decimal(value))


def _decimal(value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError("value must be exactly Decimal")
    if not value.is_finite():
        raise ValueError("value must be finite")
    return value.quantize(SIX_PLACES, rounding=ROUND_HALF_UP)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    normalized = _decimal(value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-number Decimal")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_team_ids(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a tuple")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be a tuple") from exc
    if not items:
        raise ValueError(f"{field_name} must not be empty")
    normalized: list[str] = []
    for item in items:
        team_id = _require_team_id(field_name, item)
        if team_id in normalized:
            raise ValueError(f"{field_name} must not contain duplicates")
        normalized.append(team_id)
    return tuple(sorted(normalized))


def _require_team_id(field_name: str, value: object) -> str:
    _require_public_string(field_name, value)
    if value not in DEFAULT_RESEARCH_TEAM_IDS:
        raise ValueError(f"{field_name} must be a known research team")
    return value


def _require_private_key(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if _contains_unsafe_text(value):
        raise ValueError(f"{field_name} has unsafe text")


def _require_public_digest(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if not value.startswith("sha256:"):
        raise ValueError(f"{field_name} must be a sha256 digest")
    digest = value.removeprefix("sha256:")
    if len(digest) not in (12, 64):
        raise ValueError(f"{field_name} must be a sha256 digest")
    if any(character not in "0123456789abcdef" for character in digest):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in PUBLIC_STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a tuple")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be a tuple") from exc
    if not items:
        raise ValueError(f"{field_name} must not be empty")
    normalized: list[str] = []
    for item in items:
        _require_public_string(field_name, item)
        if item not in normalized:
            normalized.append(item)
    return tuple(normalized)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_hard_flags(label: str, value: object) -> None:
    for flag_name in FLAG_NAMES:
        if getattr(value, flag_name) is not True:
            raise ValueError(f"{label} {flag_name} must be True")


def _validate_payload_flags(value: object) -> None:
    if isinstance(value, dict):
        for flag_name in FLAG_NAMES:
            if value.get(flag_name) is not True:
                raise ValueError(f"payload {flag_name} must be True")
        for item in value.values():
            _validate_payload_flags(item)
    elif isinstance(value, list):
        for item in value:
            _validate_payload_flags(item)


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    if type(payload.get("public_digest")) is not str:
        raise ValueError("payload public_digest must be present")
    if payload["public_digest"] != _public_digest_for_payload(payload):
        raise ValueError("payload public_digest must match payload")


def _public_digest_for_report(report: ResearchTeamQueueLoadBalancerReport) -> str:
    return _public_digest_for_payload(_json_ready_decimal_strings(report))


def _public_digest_for_payload(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("public_digest", None)
    encoded = json.dumps(
        digest_payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _public_queue_key(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def _json_ready_decimal_strings(value: Any, path: str = "") -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready_decimal_strings(getattr(value, field.name), field.name)
            for field in fields(value)
        }
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or 'value'} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or 'value'} must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or 'value'} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or 'value'} must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is bool:
        return value
    if type(value) is int:
        raise ValueError(f"{path or 'value'} must use Decimal string values")
    if type(value) is float:
        raise ValueError(f"{path or 'value'} must not be a float")
    if type(value) is str:
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready_decimal_strings(item, key if not path else f"{path}.{key}")
        return ready
    if isinstance(value, (list, tuple)):
        return [
            _json_ready_decimal_strings(item, f"{path}[{index}]" if path else f"value[{index}]")
            for index, item in enumerate(value)
        ]
    raise ValueError(f"{path or 'value'} is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or label} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal string values")
    if type(value) is float:
        raise ValueError(f"{path or label} must not be a float")
    if type(value) is str:
        if _contains_unsafe_text(value):
            raise ValueError(f"{path or label} has unsafe text")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _contains_unsafe_text(key):
                raise ValueError(f"unsafe field in {label}: {item_path}")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError(f"{path or label} is not JSON serializable")


def _contains_unsafe_text(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS)


def _codes_value(codes: tuple[str, ...]) -> str:
    return ",".join(codes) if codes else "none"


__all__ = (
    "DEFAULT_RESEARCH_TEAM_QUEUE_LOAD_BALANCER_CONFIG_VERSION",
    "ResearchTeamQueueLoadBalancerConfig",
    "ResearchTeamQueueLoadBalancerInputRow",
    "ResearchTeamQueueLoadBalancerReport",
    "ResearchTeamQueueLoadBalancerRoutedRow",
    "ResearchTeamQueueLoadBalancerTeamLoad",
    "ResearchTeamQueueLoadBalancerTeamRow",
    "build_research_team_queue_load_balancer_report",
    "format_research_team_queue_load_balancer_digest",
    "research_team_queue_load_balancer_payload",
)
