"""Public-safe specialist team assignment conflict resolution report."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_SPECIALIST_TEAM_ASSIGNMENT_CONFLICT_RESOLUTION_CONFIG_VERSION = (
    "specialist-team-assignment-conflict-resolution-report-v0"
)
ASSIGNMENT_CONFLICT_RESOLUTION_STATUSES = ("pass", "watch", "blocked")

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PUBLIC_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
HEX_CHARS = frozenset("0123456789abcdef")

POLICY_STATUSES = frozenset(("pass", "watch", "blocked"))
MANUAL_NEXT_STEP_BY_STATUS = {
    "pass": "paper_assignment_monitor",
    "watch": "paper_assignment_conflict_review",
    "blocked": "paper_assignment_conflict_block_review",
}

REASON_SEQUENCE = (
    "assignment_source_quorum_blocked",
    "assignment_memory_policy_blocked",
    "assignment_primary_confidence_blocked",
    "assignment_primary_confidence_watch",
    "assignment_primary_margin_conflict_watch",
    "assignment_memory_policy_watch",
    "assignment_source_quorum_watch",
    "assignment_conflict_clear",
)
REPORT_REASON_SEQUENCE = (
    "assignment_conflict_no_candidates",
    *REASON_SEQUENCE,
)

UNSAFE_LABEL_FRAGMENTS = frozenset(
    (
        "candidate",
        "market",
        "slug",
        "question",
        "raw",
        "http",
        "url",
        "dsn",
        "table",
        "token",
        "secret",
        "credential",
        "api_key",
        "wallet",
        "order",
        "trade",
        "live",
        "buy",
        "sell",
        "sizing",
        "recommendation",
    ),
)
UNSAFE_PAYLOAD_KEYS = frozenset(
    (
        "candidate_id",
        "candidate_key",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "raw_source",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "order_ticket",
        "trade",
        "sizing",
        "recommendation",
        "live",
    ),
)
COMPACT_UNSAFE_PAYLOAD_KEYS = frozenset(
    "".join(char for char in key.lower() if char.isalnum())
    for key in UNSAFE_PAYLOAD_KEYS
)
UNSAFE_PAYLOAD_KEY_FRAGMENTS = frozenset(
    "".join(char for char in key.lower() if char.isalnum())
    for key in UNSAFE_LABEL_FRAGMENTS
) | frozenset(("auth", "execute", "execution"))
UNSAFE_PAYLOAD_VALUE_FRAGMENTS = frozenset(
    (
        "candidate",
        "market",
        "slug",
        "question",
        "https://",
        "http://",
        "source_url",
        "source_text",
        "postgres://",
        "dsn",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommendation",
        " live ",
    ),
)

REPORT_PAYLOAD_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "assignment_count",
        "pass_count",
        "watch_count",
        "blocked_count",
        "manual_review_count",
        "max_primary_route_confidence",
        "min_primary_route_confidence",
        "max_domain_overlap_count",
        "status",
        "manual_next_step",
        "reason_codes",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
REPORT_COUNT_PAYLOAD_FIELDS = frozenset(
    (
        "assignment_count",
        "pass_count",
        "watch_count",
        "blocked_count",
        "manual_review_count",
        "max_domain_overlap_count",
    ),
)
REPORT_RATIO_PAYLOAD_FIELDS = frozenset(
    ("max_primary_route_confidence", "min_primary_route_confidence"),
)
ROW_PAYLOAD_FIELDS = frozenset(
    (
        "assignment_rank",
        "assignment_ref",
        "assignment_status",
        "selected_primary_team",
        "advisory_teams",
        "primary_route_confidence",
        "advisory_route_confidence",
        "domain_overlap_count",
        "memory_policy_status",
        "source_quorum_status",
        "manual_next_step",
        "observed_at",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
ROW_COUNT_PAYLOAD_FIELDS = frozenset(("assignment_rank", "domain_overlap_count"))
ROW_RATIO_PAYLOAD_FIELDS = frozenset(
    ("primary_route_confidence", "advisory_route_confidence"),
)

__all__ = (
    "DEFAULT_SPECIALIST_TEAM_ASSIGNMENT_CONFLICT_RESOLUTION_CONFIG_VERSION",
    "ASSIGNMENT_CONFLICT_RESOLUTION_STATUSES",
    "SpecialistTeamAssignmentConflictResolutionConfig",
    "SpecialistTeamAssignmentConflictResolutionReport",
    "SpecialistTeamAssignmentConflictResolutionRow",
    "SpecialistTeamAssignmentRouteCandidate",
    "build_specialist_team_assignment_conflict_resolution_report",
    "specialist_team_assignment_conflict_resolution_report_digest",
    "specialist_team_assignment_conflict_resolution_report_payload",
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class SpecialistTeamAssignmentConflictResolutionConfig(_FinalDataclass):
    config_version: str = (
        DEFAULT_SPECIALIST_TEAM_ASSIGNMENT_CONFLICT_RESOLUTION_CONFIG_VERSION
    )
    min_pass_primary_route_confidence: Decimal = Decimal("0.800000")
    min_watch_primary_route_confidence: Decimal = Decimal("0.600000")
    min_advisory_route_confidence: Decimal = Decimal("0.600000")
    max_watch_primary_margin: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            SpecialistTeamAssignmentConflictResolutionConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_SPECIALIST_TEAM_ASSIGNMENT_CONFLICT_RESOLUTION_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_primary_route_confidence",
            "min_watch_primary_route_confidence",
            "min_advisory_route_confidence",
            "max_watch_primary_margin",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.min_watch_primary_route_confidence
            > self.min_pass_primary_route_confidence
        ):
            raise ValueError(
                "min_pass_primary_route_confidence must be at least "
                "min_watch_primary_route_confidence",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class SpecialistTeamAssignmentRouteCandidate(_FinalDataclass):
    candidate_key: str
    team_label: str
    primary_route_confidence: Decimal
    advisory_route_confidence: Decimal
    domain_overlap_count: Decimal
    memory_policy_status: str
    source_quorum_status: str
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, SpecialistTeamAssignmentRouteCandidate, "route")
        _require_candidate_key("candidate_key", self.candidate_key)
        _require_public_label("team_label", self.team_label)
        for field_name in (
            "primary_route_confidence",
            "advisory_route_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "domain_overlap_count",
            _require_count_decimal("domain_overlap_count", self.domain_overlap_count),
        )
        _require_policy_status("memory_policy_status", self.memory_policy_status)
        _require_policy_status("source_quorum_status", self.source_quorum_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("route", self)


@dataclass(frozen=True)
class SpecialistTeamAssignmentConflictResolutionRow(_FinalDataclass):
    assignment_rank: Decimal
    assignment_ref: str
    assignment_status: str
    selected_primary_team: str
    advisory_teams: tuple[str, ...]
    primary_route_confidence: Decimal
    advisory_route_confidence: Decimal
    domain_overlap_count: Decimal
    memory_policy_status: str
    source_quorum_status: str
    manual_next_step: str
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            SpecialistTeamAssignmentConflictResolutionRow,
            "row",
        )
        object.__setattr__(
            self,
            "assignment_rank",
            _require_count_decimal("assignment_rank", self.assignment_rank),
        )
        _require_assignment_ref("assignment_ref", self.assignment_ref)
        _require_assignment_status("assignment_status", self.assignment_status)
        _require_public_label("selected_primary_team", self.selected_primary_team)
        object.__setattr__(
            self,
            "advisory_teams",
            _require_team_labels("advisory_teams", self.advisory_teams),
        )
        for field_name in (
            "primary_route_confidence",
            "advisory_route_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "domain_overlap_count",
            _require_count_decimal("domain_overlap_count", self.domain_overlap_count),
        )
        _require_policy_status("memory_policy_status", self.memory_policy_status)
        _require_policy_status("source_quorum_status", self.source_quorum_status)
        _require_public_string("manual_next_step", self.manual_next_step)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class SpecialistTeamAssignmentConflictResolutionReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    assignment_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    manual_review_count: Decimal
    max_primary_route_confidence: Decimal
    min_primary_route_confidence: Decimal
    max_domain_overlap_count: Decimal
    status: str
    manual_next_step: str
    reason_codes: tuple[str, ...]
    rows: tuple[SpecialistTeamAssignmentConflictResolutionRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            SpecialistTeamAssignmentConflictResolutionReport,
            "report",
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_SPECIALIST_TEAM_ASSIGNMENT_CONFLICT_RESOLUTION_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "assignment_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "manual_review_count",
            "max_domain_overlap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_primary_route_confidence",
            "min_primary_route_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_assignment_status("status", self.status)
        _require_public_string("manual_next_step", self.manual_next_step)
        object.__setattr__(
            self,
            "reason_codes",
            _require_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "rows", _require_rows(self.rows))
        _require_sha256("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")


def build_specialist_team_assignment_conflict_resolution_report(
    routes: Iterable[SpecialistTeamAssignmentRouteCandidate],
    *,
    config: SpecialistTeamAssignmentConflictResolutionConfig,
    generated_at: datetime,
) -> SpecialistTeamAssignmentConflictResolutionReport:
    _require_exact_type(
        config,
        SpecialistTeamAssignmentConflictResolutionConfig,
        "config",
    )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    route_rows = _normalize_routes(routes)
    grouped: dict[str, list[SpecialistTeamAssignmentRouteCandidate]] = defaultdict(list)
    for route in route_rows:
        grouped[route.candidate_key].append(route)
    base_rows = tuple(
        _row_from_routes(candidate_routes, config)
        for _, candidate_routes in sorted(grouped.items())
    )
    rows = tuple(
        _with_rank(row, rank)
        for rank, row in enumerate(sorted(base_rows, key=_row_sort_key), start=1)
    )
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "assignment_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "blocked_count": _status_count(rows, "blocked"),
        "manual_review_count": _manual_review_count(rows),
        "max_primary_route_confidence": _max_decimal(
            tuple(row.primary_route_confidence for row in rows),
        ),
        "min_primary_route_confidence": _min_decimal(
            tuple(row.primary_route_confidence for row in rows),
        ),
        "max_domain_overlap_count": _max_decimal(
            tuple(row.domain_overlap_count for row in rows),
        ),
        "status": _report_status(rows),
        "manual_next_step": MANUAL_NEXT_STEP_BY_STATUS[_report_status(rows)],
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return SpecialistTeamAssignmentConflictResolutionReport(
        **values,
        derived_validation_digest=_digest_from_values(values),
    )


def specialist_team_assignment_conflict_resolution_report_payload(
    report: SpecialistTeamAssignmentConflictResolutionReport | Mapping[str, object],
) -> dict[str, object]:
    if type(report) is SpecialistTeamAssignmentConflictResolutionReport:
        _require_hard_flags("report", report)
        payload = _json_ready(asdict(report))
    elif isinstance(report, Mapping):
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a SpecialistTeamAssignmentConflictResolutionReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("report payload", _MappingFlags(payload))
    expected_digest = _digest_from_payload(payload)
    if payload.get("derived_validation_digest") != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    _reject_unsafe_public_payload("report payload", payload, allow_json_containers=True)
    _require_public_payload_schema(payload)
    return payload


def specialist_team_assignment_conflict_resolution_report_digest(
    report: SpecialistTeamAssignmentConflictResolutionReport | Mapping[str, object],
) -> str:
    payload = specialist_team_assignment_conflict_resolution_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


@dataclass(frozen=True)
class _MappingFlags:
    value: Mapping[str, object]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _row_from_routes(
    routes: list[SpecialistTeamAssignmentRouteCandidate],
    config: SpecialistTeamAssignmentConflictResolutionConfig,
) -> SpecialistTeamAssignmentConflictResolutionRow:
    sorted_routes = tuple(sorted(routes, key=_route_sort_key))
    primary = sorted_routes[0]
    runner_up = sorted_routes[1] if len(sorted_routes) > 1 else None
    advisory_teams = tuple(
        item.team_label
        for item in sorted_routes
        if item is not primary
        and item.advisory_route_confidence >= config.min_advisory_route_confidence
    )
    reason_codes = _row_reason_codes(
        primary=primary,
        runner_up=runner_up,
        config=config,
    )
    status = _row_status(reason_codes)
    return SpecialistTeamAssignmentConflictResolutionRow(
        assignment_rank=ONE,
        assignment_ref=_assignment_ref(primary.candidate_key),
        assignment_status=status,
        selected_primary_team=primary.team_label,
        advisory_teams=advisory_teams,
        primary_route_confidence=primary.primary_route_confidence,
        advisory_route_confidence=primary.advisory_route_confidence,
        domain_overlap_count=primary.domain_overlap_count,
        memory_policy_status=primary.memory_policy_status,
        source_quorum_status=primary.source_quorum_status,
        manual_next_step=_manual_next_step_for_row(status, reason_codes),
        observed_at=primary.observed_at,
        reason_codes=reason_codes,
    )


def _with_rank(
    row: SpecialistTeamAssignmentConflictResolutionRow,
    rank: int,
) -> SpecialistTeamAssignmentConflictResolutionRow:
    return SpecialistTeamAssignmentConflictResolutionRow(
        assignment_rank=_count(rank),
        assignment_ref=row.assignment_ref,
        assignment_status=row.assignment_status,
        selected_primary_team=row.selected_primary_team,
        advisory_teams=row.advisory_teams,
        primary_route_confidence=row.primary_route_confidence,
        advisory_route_confidence=row.advisory_route_confidence,
        domain_overlap_count=row.domain_overlap_count,
        memory_policy_status=row.memory_policy_status,
        source_quorum_status=row.source_quorum_status,
        manual_next_step=row.manual_next_step,
        observed_at=row.observed_at,
        reason_codes=row.reason_codes,
    )


def _route_sort_key(
    route: SpecialistTeamAssignmentRouteCandidate,
) -> tuple[Decimal, Decimal, Decimal, str]:
    return (
        -route.primary_route_confidence,
        -route.domain_overlap_count,
        -route.advisory_route_confidence,
        route.team_label,
    )


def _row_reason_codes(
    *,
    primary: SpecialistTeamAssignmentRouteCandidate,
    runner_up: SpecialistTeamAssignmentRouteCandidate | None,
    config: SpecialistTeamAssignmentConflictResolutionConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if primary.source_quorum_status == "blocked":
        reasons.append("assignment_source_quorum_blocked")
    if primary.memory_policy_status == "blocked":
        reasons.append("assignment_memory_policy_blocked")
    if primary.primary_route_confidence < config.min_watch_primary_route_confidence:
        reasons.append("assignment_primary_confidence_blocked")
    elif primary.primary_route_confidence < config.min_pass_primary_route_confidence:
        reasons.append("assignment_primary_confidence_watch")
    if _has_primary_margin_conflict(primary, runner_up, config):
        reasons.append("assignment_primary_margin_conflict_watch")
    if primary.memory_policy_status == "watch":
        reasons.append("assignment_memory_policy_watch")
    if primary.source_quorum_status == "watch":
        reasons.append("assignment_source_quorum_watch")
    if not reasons:
        reasons.append("assignment_conflict_clear")
    return _require_reason_codes(tuple(reasons), require_nonempty=True)


def _has_primary_margin_conflict(
    primary: SpecialistTeamAssignmentRouteCandidate,
    runner_up: SpecialistTeamAssignmentRouteCandidate | None,
    config: SpecialistTeamAssignmentConflictResolutionConfig,
) -> bool:
    if runner_up is None:
        return False
    with localcontext(DECIMAL_CONTEXT):
        margin = primary.primary_route_confidence - runner_up.primary_route_confidence
    return margin <= config.max_watch_primary_margin


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_blocked") for reason_code in reason_codes):
        return "blocked"
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "blocked"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _manual_next_step_for_row(status: str, reason_codes: tuple[str, ...]) -> str:
    if "assignment_source_quorum_blocked" in reason_codes:
        return "paper_assignment_source_quorum_review"
    if "assignment_memory_policy_blocked" in reason_codes:
        return "paper_assignment_memory_policy_review"
    if status == "blocked":
        return "paper_assignment_conflict_block_review"
    if status == "watch":
        return "paper_assignment_conflict_review"
    return "paper_assignment_monitor"


def _row_sort_key(
    row: SpecialistTeamAssignmentConflictResolutionRow,
) -> tuple[int, Decimal, str]:
    return (
        _status_rank(row.assignment_status),
        -row.primary_route_confidence,
        row.assignment_ref,
    )


def _status_rank(status: str) -> int:
    return {"blocked": 0, "watch": 1, "pass": 2}[status]


def _report_status(rows: tuple[SpecialistTeamAssignmentConflictResolutionRow, ...]) -> str:
    if any(row.assignment_status == "blocked" for row in rows):
        return "blocked"
    if any(row.assignment_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _status_count(
    rows: tuple[SpecialistTeamAssignmentConflictResolutionRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.assignment_status == status))


def _manual_review_count(
    rows: tuple[SpecialistTeamAssignmentConflictResolutionRow, ...],
) -> Decimal:
    return _count(
        sum(1 for row in rows if row.assignment_status in {"watch", "blocked"}),
    )


def _report_reason_codes(
    rows: tuple[SpecialistTeamAssignmentConflictResolutionRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("assignment_conflict_no_candidates",)
    reason_codes = frozenset(
        reason_code for row in rows for reason_code in row.reason_codes
    )
    return tuple(
        reason_code for reason_code in REASON_SEQUENCE if reason_code in reason_codes
    )


def _normalize_routes(
    routes: Iterable[SpecialistTeamAssignmentRouteCandidate],
) -> tuple[SpecialistTeamAssignmentRouteCandidate, ...]:
    if isinstance(routes, (str, bytes)):
        raise ValueError("routes must be an iterable")
    try:
        items = tuple(routes)
    except TypeError as exc:
        raise ValueError("routes must be an iterable") from exc
    seen: set[tuple[str, str]] = set()
    for item in items:
        if type(item) is not SpecialistTeamAssignmentRouteCandidate:
            raise ValueError("routes must contain SpecialistTeamAssignmentRouteCandidate")
        _require_hard_flags("route", item)
        key = (item.candidate_key, item.team_label)
        if key in seen:
            raise ValueError("duplicate team route for candidate")
        seen.add(key)
    return items


def _require_rows(
    rows: tuple[SpecialistTeamAssignmentConflictResolutionRow, ...],
) -> tuple[SpecialistTeamAssignmentConflictResolutionRow, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    assignment_refs: set[str] = set()
    for row in normalized:
        if type(row) is not SpecialistTeamAssignmentConflictResolutionRow:
            raise ValueError(
                "rows must contain SpecialistTeamAssignmentConflictResolutionRow",
            )
        _require_hard_flags("row", row)
        if row.assignment_ref in assignment_refs:
            raise ValueError("assignment_ref values must be unique")
        assignment_refs.add(row.assignment_ref)
    return normalized


def _validate_row(row: SpecialistTeamAssignmentConflictResolutionRow) -> None:
    if row.selected_primary_team in row.advisory_teams:
        raise ValueError("selected_primary_team must not be advisory")
    if row.manual_next_step != _manual_next_step_for_row(
        row.assignment_status,
        row.reason_codes,
    ):
        raise ValueError("manual_next_step must match assignment_status")
    if row.assignment_status != _row_status(row.reason_codes):
        raise ValueError("assignment_status must match reason_codes")


def _validate_report(report: SpecialistTeamAssignmentConflictResolutionReport) -> None:
    rows = report.rows
    if report.assignment_count != _count(len(rows)):
        raise ValueError("assignment_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.manual_review_count != _manual_review_count(rows):
        raise ValueError("manual_review_count must match rows")
    if report.max_primary_route_confidence != _max_decimal(
        tuple(row.primary_route_confidence for row in rows),
    ):
        raise ValueError("max_primary_route_confidence must match rows")
    if report.min_primary_route_confidence != _min_decimal(
        tuple(row.primary_route_confidence for row in rows),
    ):
        raise ValueError("min_primary_route_confidence must match rows")
    if report.max_domain_overlap_count != _max_decimal(
        tuple(row.domain_overlap_count for row in rows),
    ):
        raise ValueError("max_domain_overlap_count must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.manual_next_step != MANUAL_NEXT_STEP_BY_STATUS[report.status]:
        raise ValueError("manual_next_step must match status")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _require_public_payload_schema(payload: Mapping[str, object]) -> None:
    _require_payload_fields("report payload", payload, REPORT_PAYLOAD_FIELDS)
    _require_utc_datetime_payload("generated_at", payload["generated_at"])
    _require_public_string("config_version", payload["config_version"])
    if (
        payload["config_version"]
        != DEFAULT_SPECIALIST_TEAM_ASSIGNMENT_CONFLICT_RESOLUTION_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    for field_name in REPORT_COUNT_PAYLOAD_FIELDS:
        _require_decimal_payload(field_name, payload[field_name], maximum=None)
    for field_name in REPORT_RATIO_PAYLOAD_FIELDS:
        _require_decimal_payload(field_name, payload[field_name], maximum=ONE)
    _require_assignment_status("status", payload["status"])
    _require_public_string("manual_next_step", payload["manual_next_step"])
    _require_reason_code_payload_list(
        "reason_codes",
        payload["reason_codes"],
        report_level=True,
    )
    _require_row_payloads(payload["rows"])
    _require_sha256("derived_validation_digest", payload["derived_validation_digest"])
    _require_hard_flags("report payload", _MappingFlags(payload))


def _require_payload_fields(
    label: str,
    payload: Mapping[str, object],
    expected_fields: frozenset[str],
) -> None:
    keys = frozenset(payload)
    extra = sorted(keys - expected_fields)
    if extra:
        raise ValueError(f"unexpected public payload field in {label}: {extra[0]}")
    missing = sorted(expected_fields - keys)
    if missing:
        raise ValueError(f"missing public payload field in {label}: {missing[0]}")


def _require_row_payloads(value: object) -> None:
    if not isinstance(value, list):
        raise ValueError("rows must be a list")
    for item in value:
        if type(item) is not dict:
            raise ValueError("rows must contain JSON objects")
        _require_payload_fields("row payload", item, ROW_PAYLOAD_FIELDS)
        _require_assignment_ref_payload(item["assignment_ref"])
        _require_assignment_status("assignment_status", item["assignment_status"])
        _require_public_label("selected_primary_team", item["selected_primary_team"])
        _require_team_label_payloads(item["advisory_teams"])
        for field_name in ROW_COUNT_PAYLOAD_FIELDS:
            _require_decimal_payload(field_name, item[field_name], maximum=None)
        for field_name in ROW_RATIO_PAYLOAD_FIELDS:
            _require_decimal_payload(field_name, item[field_name], maximum=ONE)
        _require_policy_status("memory_policy_status", item["memory_policy_status"])
        _require_policy_status("source_quorum_status", item["source_quorum_status"])
        _require_public_string("manual_next_step", item["manual_next_step"])
        _require_utc_datetime_payload("observed_at", item["observed_at"])
        _require_reason_code_payload_list(
            "reason_codes",
            item["reason_codes"],
            report_level=False,
        )
        _require_hard_flags("row payload", _MappingFlags(item))


def _require_reason_code_payload_list(
    name: str,
    value: object,
    *,
    report_level: bool,
) -> None:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a list")
    reason_codes = tuple(value)
    if report_level:
        _require_report_reason_codes(reason_codes)
        return
    _require_reason_codes(reason_codes, require_nonempty=True)


def _require_team_label_payloads(value: object) -> None:
    if not isinstance(value, list):
        raise ValueError("advisory_teams must be a list")
    _require_team_labels("advisory_teams", tuple(value))


def _require_report_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    reason_codes = _require_reason_codes(value, require_nonempty=True)
    expected = tuple(
        reason_code
        for reason_code in REPORT_REASON_SEQUENCE
        if reason_code in reason_codes
    )
    if reason_codes != expected:
        raise ValueError("reason_codes must be sorted deterministically")
    return reason_codes


def _require_reason_codes(
    value: tuple[str, ...],
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise ValueError("reason_codes must be a tuple")
    if require_nonempty and not value:
        raise ValueError("reason_codes must be nonempty")
    allowed = frozenset(REPORT_REASON_SEQUENCE)
    for reason_code in value:
        _require_public_string("reason_code", reason_code)
        if reason_code not in allowed:
            raise ValueError(f"unsupported reason_code: {reason_code}")
    if len(set(value)) != len(value):
        raise ValueError("reason_codes must be unique")
    expected = tuple(
        reason_code for reason_code in REPORT_REASON_SEQUENCE if reason_code in value
    )
    if value != expected:
        raise ValueError("reason_codes must be sorted deterministically")
    return value


def _report_values_without_digest(
    report: SpecialistTeamAssignmentConflictResolutionReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest")
    return values


def _digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    return _digest_from_payload(payload)


def _digest_from_payload(payload: Mapping[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(value.quantize(QUANTUM))
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int:
        return value
    if type(value) is float:
        raise ValueError("public payload must not contain floats")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(QUANTUM)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values).quantize(QUANTUM)


def _min_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return min(values).quantize(QUANTUM)


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be {expected_type.__name__}")


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return decimal_value


def _require_count_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return decimal_value


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value.quantize(QUANTUM)


def _require_decimal_payload(
    name: str,
    value: object,
    *,
    maximum: Decimal | None,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{name} must be a Decimal string")
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{name} must be a Decimal string") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{name} must be finite")
    quantized = decimal_value.quantize(QUANTUM)
    if value != str(quantized):
        raise ValueError(f"{name} must be a canonical Decimal string")
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if maximum is not None and decimal_value > maximum:
        raise ValueError(f"{name} must be between 0 and 1")
    return quantized


def _require_candidate_key(name: str, value: object) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{name} must be a string")


def _require_public_string(name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{name} must be a nonempty string")
    _reject_unsafe_public_text(name, value)


def _require_public_label(name: str, value: object) -> None:
    _require_public_string(name, value)
    if PUBLIC_LABEL_RE.fullmatch(value) is None:
        raise ValueError(f"{name} must be a public label")


def _require_team_labels(name: str, value: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise ValueError(f"{name} must be a tuple")
    for team_label in value:
        _require_public_label(name, team_label)
    if len(set(value)) != len(value):
        raise ValueError(f"{name} must be unique")
    if value != tuple(sorted(value)):
        raise ValueError(f"{name} must be sorted deterministically")
    return value


def _require_policy_status(name: str, value: object) -> None:
    if type(value) is not str or value not in POLICY_STATUSES:
        raise ValueError(f"{name} must be pass, watch, or blocked")


def _require_assignment_status(name: str, value: object) -> None:
    if type(value) is not str or value not in ASSIGNMENT_CONFLICT_RESOLUTION_STATUSES:
        raise ValueError(f"{name} must be pass, watch, or blocked")


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{name} must be UTC-aware")
    if value.utcoffset() != ZERO_TIMEDELTA:
        raise ValueError(f"{name} must be UTC")
    return value.astimezone(UTC)


ZERO_TIMEDELTA = datetime(2026, 1, 1, tzinfo=UTC).utcoffset()


def _require_utc_datetime_payload(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a UTC datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a UTC datetime string") from exc
    _as_utc(name, parsed)


def _assignment_ref(candidate_key: str) -> str:
    digest = sha256(candidate_key.encode("utf-8")).hexdigest()
    return f"assignment_ref_{digest}"


def _require_assignment_ref(name: str, value: object) -> None:
    if type(value) is not str or not value.startswith("assignment_ref_"):
        raise ValueError(f"{name} must be a hashed assignment reference")
    _require_sha256(name, value.removeprefix("assignment_ref_"))


def _require_assignment_ref_payload(value: object) -> None:
    if type(value) is not str:
        raise ValueError("assignment_ref must be a hashed assignment reference")
    if not value.startswith("assignment_ref_"):
        raise ValueError("assignment_ref must be a hashed assignment reference")
    _require_sha256("assignment_ref", value.removeprefix("assignment_ref_"))


def _require_sha256(name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{name} must be a sha256 hex digest")
    if any(char not in HEX_CHARS for char in value):
        raise ValueError(f"{name} must be a sha256 hex digest")


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field_name, field_value in asdict(value).items():
            _reject_unsafe_public_key(field_name)
            _reject_unsafe_public_payload(
                f"{label}.{field_name}",
                field_value,
                allow_json_containers=True,
            )
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe non-string payload key in {label}")
            _reject_unsafe_public_key(key)
            _reject_unsafe_public_payload(
                f"{label}.{key}",
                item,
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if not allow_json_containers and isinstance(value, list):
            raise ValueError(f"unsafe list payload in {label}")
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_key(key: str) -> None:
    compact = "".join(char for char in key.lower() if char.isalnum())
    if compact in COMPACT_UNSAFE_PAYLOAD_KEYS:
        raise ValueError(f"unsafe public payload key: {key}")
    if any(fragment in compact for fragment in UNSAFE_PAYLOAD_KEY_FRAGMENTS):
        if key != "assignment_ref":
            raise ValueError(f"unsafe public payload key: {key}")


def _reject_unsafe_public_text(name: str, value: str) -> None:
    lowered = value.lower()
    if name.endswith("assignment_ref") and value.startswith("assignment_ref_"):
        return
    if value.startswith("assignment_") or value.startswith("paper_assignment_"):
        return
    compact = "".join(char for char in lowered if char.isalnum())
    if any(fragment in lowered for fragment in UNSAFE_PAYLOAD_VALUE_FRAGMENTS):
        raise ValueError(f"unsafe public text in {name}")
    if any(fragment in compact for fragment in UNSAFE_LABEL_FRAGMENTS):
        raise ValueError(f"unsafe public text in {name}")
