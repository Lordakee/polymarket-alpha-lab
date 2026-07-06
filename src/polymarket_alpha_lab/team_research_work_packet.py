"""Pure paper-only team research operations packets."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)
from polymarket_alpha_lab.team_research_assignment import (
    TeamResearchAssignmentReport,
    TeamResearchAssignmentRow,
)


DEFAULT_TEAM_RESEARCH_WORK_PACKET_CONFIG_VERSION = "team-research-work-packet-v0"
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"

PACKET_STATUSES = ("assigned", "watch", "blocked")
REPORT_REASON_CODES = {
    "assigned": "team_research_work_packet_assigned",
    "watch": "team_research_work_packet_watch",
    "blocked": "team_research_work_packet_blocked",
}
MEMORY_STATUSES = ("pass", "watch", "blocked", "missing")
MEMORY_POLICIES = ("allow", "throttle", "block")
ASSIGNMENT_STATUSES = ("assigned", "watch", "blocked")
RESEARCH_DOMAINS = ("finance", "politics", "sports", "general")
RESEARCH_HORIZONS = ("long_term",)
RESEARCH_MODES = ("phase_1_report_only",)
BASE_RESEARCH_TASK_CODES = (
    "resolution_criteria_review",
    "source_map_update",
    "base_rate_context",
    "uncertainty_log",
    "counterevidence_scan",
)
DOMAIN_RESEARCH_TASK_CODES = {
    "finance": ("filing_calendar_scan",),
    "politics": ("polling_method_review",),
    "sports": ("availability_report_review",),
    "general": (),
}
SAFETY_FLAG_NAMES = ("paper_only", "report_only", "readonly")
UNSAFE_WORK_PACKET_FIELD_FRAGMENTS = frozenset(
    (
        "auth",
        "private_key",
        "wallet",
        "account",
        "balance",
        "order",
        "cancel",
        "replace",
        "exchange_mutation",
        "trade",
        "trading",
        "recommend",
        "recommendation",
        "position",
        "sizing",
        "notional",
        "shares",
        "buy",
        "sell",
    ),
)
UNSAFE_WORK_PACKET_VALUE_FRAGMENTS = frozenset(
    (
        "submit order",
        "place order",
        "market order",
        "limit order",
        "open position",
        "close position",
        "position sizing",
        "position_sizing",
        "buy signal",
        "sell signal",
        "investment recommendation",
        "trade execution",
    ),
)
HIDDEN_WORK_PACKET_FIELD_NAMES = frozenset(
    (
        "research_rank",
        "market_slug",
        "question",
        "selected_side",
        "scoring_side",
    ),
)
REDACTED_SENSITIVE_VALUE = "<redacted-sensitive>"
SENSITIVE_WORK_PACKET_KEY_FRAGMENTS = frozenset(
    (
        "database_url",
        "dsn",
        "payload_json",
        "payload",
        "password",
        "secret",
        "token",
        "api_key",
        "private_key",
        "authorization",
        "credential",
        "condition_id",
    ),
)
SENSITIVE_WORK_PACKET_VALUE_FRAGMENTS = frozenset(
    (
        "postgres://",
        "postgresql://",
        "database_url=",
        "password=",
        "secret=",
        "token=",
        "api_key=",
        "private_key=",
        "authorization=",
        "credential=",
    ),
)


@dataclass(frozen=True)
class TeamResearchWorkPacketConfig:
    config_version: str = DEFAULT_TEAM_RESEARCH_WORK_PACKET_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        require_paper_only_flags("TeamResearchWorkPacketConfig", self)


@dataclass(frozen=True)
class TeamResearchWorkPacketRow:
    research_rank: int
    market_slug: str
    question: str
    selected_side: str
    scoring_side: str
    category_id: str
    queue_research_status: str
    queue_research_bucket: str
    queue_readiness_status: str
    memory_readiness_status: str
    memory_use_policy: str
    research_domain: str
    research_horizon: str
    research_mode: str
    research_task_codes: tuple[str, ...]
    assignment_status: str
    assignment_reason_codes: tuple[str, ...]
    evidence_gap_codes: tuple[str, ...]
    source_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_positive_int("research_rank", self.research_rank)
        for field_name in (
            "market_slug",
            "question",
            "selected_side",
            "scoring_side",
            "category_id",
            "queue_research_status",
            "queue_research_bucket",
            "queue_readiness_status",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member(
            "memory_readiness_status",
            self.memory_readiness_status,
            MEMORY_STATUSES,
        )
        _require_member("memory_use_policy", self.memory_use_policy, MEMORY_POLICIES)
        _require_member("research_domain", self.research_domain, RESEARCH_DOMAINS)
        _require_member("research_horizon", self.research_horizon, RESEARCH_HORIZONS)
        _require_member("research_mode", self.research_mode, RESEARCH_MODES)
        object.__setattr__(
            self,
            "research_task_codes",
            _normalize_string_tuple(
                "research_task_codes",
                self.research_task_codes,
                allow_empty=False,
            ),
        )
        _require_member("assignment_status", self.assignment_status, ASSIGNMENT_STATUSES)
        object.__setattr__(
            self,
            "assignment_reason_codes",
            _normalize_string_tuple(
                "assignment_reason_codes",
                self.assignment_reason_codes,
                allow_empty=False,
            ),
        )
        object.__setattr__(
            self,
            "evidence_gap_codes",
            _normalize_string_tuple(
                "evidence_gap_codes",
                self.evidence_gap_codes,
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "source_reason_codes",
            _normalize_string_tuple(
                "source_reason_codes",
                self.source_reason_codes,
                allow_empty=True,
            ),
        )
        _validate_memory_policy(
            self.memory_readiness_status,
            self.memory_use_policy,
        )
        require_paper_only_flags("TeamResearchWorkPacketRow", self)


@dataclass(frozen=True)
class TeamResearchTeamWorkPacket:
    team_id: str
    packet_status: str
    memory_readiness_status: str
    memory_use_policy: str
    assignment_count: int
    assigned_count: int
    watch_count: int
    blocked_count: int
    evidence_gap_codes: tuple[str, ...]
    assignment_reason_codes: tuple[str, ...]
    source_reason_codes: tuple[str, ...]
    rows: tuple[TeamResearchWorkPacketRow, ...]
    research_domains: tuple[str, ...]
    research_horizons: tuple[str, ...]
    research_modes: tuple[str, ...]
    research_task_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("team_id", self.team_id)
        _require_member("packet_status", self.packet_status, PACKET_STATUSES)
        _require_member(
            "memory_readiness_status",
            self.memory_readiness_status,
            MEMORY_STATUSES,
        )
        _require_member("memory_use_policy", self.memory_use_policy, MEMORY_POLICIES)
        for field_name in (
            "assignment_count",
            "assigned_count",
            "watch_count",
            "blocked_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "evidence_gap_codes",
            _normalize_string_tuple(
                "evidence_gap_codes",
                self.evidence_gap_codes,
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "assignment_reason_codes",
            _normalize_string_tuple(
                "assignment_reason_codes",
                self.assignment_reason_codes,
                allow_empty=False,
            ),
        )
        object.__setattr__(
            self,
            "source_reason_codes",
            _normalize_string_tuple(
                "source_reason_codes",
                self.source_reason_codes,
                allow_empty=True,
            ),
        )
        object.__setattr__(self, "rows", _normalize_work_rows(self.rows))
        object.__setattr__(
            self,
            "research_domains",
            _normalize_member_tuple(
                "research_domains",
                self.research_domains,
                RESEARCH_DOMAINS,
                allow_empty=False,
            ),
        )
        object.__setattr__(
            self,
            "research_horizons",
            _normalize_member_tuple(
                "research_horizons",
                self.research_horizons,
                RESEARCH_HORIZONS,
                allow_empty=False,
            ),
        )
        object.__setattr__(
            self,
            "research_modes",
            _normalize_member_tuple(
                "research_modes",
                self.research_modes,
                RESEARCH_MODES,
                allow_empty=False,
            ),
        )
        object.__setattr__(
            self,
            "research_task_codes",
            _normalize_string_tuple(
                "research_task_codes",
                self.research_task_codes,
                allow_empty=False,
            ),
        )
        _validate_team_packet_consistency(self)
        require_paper_only_flags("TeamResearchTeamWorkPacket", self)


@dataclass(frozen=True)
class TeamResearchWorkPacketReport:
    generated_at: datetime
    config_version: str
    source_assignment_config_version: str
    packet_status: str
    team_packet_count: int
    research_assignment_count: int
    assigned_count: int
    watch_count: int
    blocked_count: int
    team_packets: tuple[TeamResearchTeamWorkPacket, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string(
            "source_assignment_config_version",
            self.source_assignment_config_version,
        )
        _require_member("packet_status", self.packet_status, PACKET_STATUSES)
        for field_name in (
            "team_packet_count",
            "research_assignment_count",
            "assigned_count",
            "watch_count",
            "blocked_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "team_packets",
            _normalize_team_packets(self.team_packets),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_string_tuple(
                "reason_codes",
                self.reason_codes,
                allow_empty=False,
            ),
        )
        _validate_report_consistency(self)
        require_paper_only_flags("TeamResearchWorkPacketReport", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _normalize_sha256(
                    DERIVED_VALIDATION_DIGEST_FIELD,
                    self.derived_validation_digest,
                ),
            )
        _validate_report_derived_validation_digest(self)


def build_team_research_work_packet_report(
    assignment_report: TeamResearchAssignmentReport,
    *,
    config: TeamResearchWorkPacketConfig,
    generated_at: datetime,
) -> TeamResearchWorkPacketReport:
    if type(assignment_report) is not TeamResearchAssignmentReport:
        raise ValueError("assignment_report must be a TeamResearchAssignmentReport")
    if type(config) is not TeamResearchWorkPacketConfig:
        raise ValueError("config must be a TeamResearchWorkPacketConfig")
    require_paper_only_flags("assignment_report", assignment_report)
    require_paper_only_flags("config", config)

    rows = _normalize_assignment_rows(assignment_report.rows)
    team_packets = _build_team_packets(rows)
    packet_status = _report_packet_status(team_packets)
    return TeamResearchWorkPacketReport(
        generated_at=generated_at,
        config_version=config.config_version,
        source_assignment_config_version=assignment_report.config_version,
        packet_status=packet_status,
        team_packet_count=len(team_packets),
        research_assignment_count=len(rows),
        assigned_count=_work_status_count(
            tuple(row for packet in team_packets for row in packet.rows),
            "assigned",
        ),
        watch_count=_work_status_count(
            tuple(row for packet in team_packets for row in packet.rows),
            "watch",
        ),
        blocked_count=_work_status_count(
            tuple(row for packet in team_packets for row in packet.rows),
            "blocked",
        ),
        team_packets=team_packets,
        reason_codes=(REPORT_REASON_CODES[packet_status],),
    )


def team_research_work_packet_payload(value: object) -> dict[str, Any]:
    is_report = type(value) is TeamResearchWorkPacketReport
    if isinstance(
        value,
        (
            TeamResearchWorkPacketReport,
            TeamResearchTeamWorkPacket,
            TeamResearchWorkPacketRow,
        ),
    ):
        require_paper_only_flags("team research work packet payload", value)
        if is_report:
            _validate_report_derived_validation_digest(value)
    elif not isinstance(value, dict):
        raise ValueError(
            "value must be a TeamResearchWorkPacketReport, packet row, or JSON object",
        )

    _reject_unsafe_work_packet_fields("team research work packet payload", value)
    payload = _work_packet_public_payload_without_digest(value)
    if not isinstance(payload, dict):
        raise ValueError("team research work packet payload must be a JSON object")

    if is_report:
        payload[DERIVED_VALIDATION_DIGEST_FIELD] = value.derived_validation_digest
    elif isinstance(value, dict) and _is_work_packet_report_payload(value):
        has_digest = DERIVED_VALIDATION_DIGEST_FIELD in value
        was_raw_internal_payload = _contains_hidden_work_packet_fields(value)
        if has_digest:
            payload[DERIVED_VALIDATION_DIGEST_FIELD] = _normalize_sha256(
                DERIVED_VALIDATION_DIGEST_FIELD,
                value[DERIVED_VALIDATION_DIGEST_FIELD],
            )
        elif was_raw_internal_payload:
            payload[DERIVED_VALIDATION_DIGEST_FIELD] = _derived_validation_digest(
                payload,
            )

    _validate_payload_safety_flags(payload, "payload", require_current_flags=True)
    if is_report or (
        isinstance(value, dict) and _is_work_packet_report_payload(value)
    ):
        if DERIVED_VALIDATION_DIGEST_FIELD not in payload:
            raise ValueError(f"{DERIVED_VALIDATION_DIGEST_FIELD} is required")
        _validate_payload_derived_validation_digest(payload)
    _reject_unsafe_work_packet_fields("team research work packet payload", payload)
    return payload


def _work_packet_public_payload_without_digest(value: object) -> object:
    payload = json_ready_no_floats(value)
    payload = _strip_derived_validation_digest(payload)
    payload = _decimalize_public_numerics(payload)
    payload = _add_work_packet_public_ids(payload)
    payload = _redact_sensitive_work_packet_values(payload)
    return _strip_hidden_work_packet_fields(payload)


def _report_derived_validation_digest(report: TeamResearchWorkPacketReport) -> str:
    payload = _work_packet_public_payload_without_digest(report)
    if not isinstance(payload, dict):
        raise ValueError("team research work packet report payload must be a JSON object")
    return _derived_validation_digest(payload)


def _validate_report_derived_validation_digest(
    report: TeamResearchWorkPacketReport,
) -> None:
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _validate_payload_derived_validation_digest(payload: dict[str, Any]) -> None:
    provided_digest = _normalize_sha256(
        DERIVED_VALIDATION_DIGEST_FIELD,
        payload[DERIVED_VALIDATION_DIGEST_FIELD],
    )
    payload_without_digest = _strip_derived_validation_digest(payload)
    if not isinstance(payload_without_digest, dict):
        raise ValueError("team research work packet payload must be a JSON object")
    if provided_digest != _derived_validation_digest(payload_without_digest):
        raise ValueError("derived_validation_digest must match payload fields")


def _derived_validation_digest(payload: dict[str, Any]) -> str:
    rendered_payload = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(
        f"team_research_work_packet_derived|{rendered_payload}".encode("utf-8"),
    ).hexdigest()


def _strip_derived_validation_digest(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: _strip_derived_validation_digest(item)
            for key, item in value.items()
            if key != DERIVED_VALIDATION_DIGEST_FIELD
        }
    if isinstance(value, list):
        return [_strip_derived_validation_digest(item) for item in value]
    return value


def _decimalize_public_numerics(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: _decimalize_public_numerics(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_decimalize_public_numerics(item) for item in value]
    if type(value) is int:
        return str(Decimal(value))
    return value


def _is_work_packet_report_payload(value: dict[str, object]) -> bool:
    return all(
        key in value
        for key in (
            "packet_status",
            "team_packet_count",
            "research_assignment_count",
            "team_packets",
            "reason_codes",
        )
    )


def _contains_hidden_work_packet_fields(value: object) -> bool:
    if isinstance(value, dict):
        return any(
            key in HIDDEN_WORK_PACKET_FIELD_NAMES
            or _contains_hidden_work_packet_fields(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_hidden_work_packet_fields(item) for item in value)
    return False


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _build_team_packets(
    rows: tuple[TeamResearchAssignmentRow, ...],
) -> tuple[TeamResearchTeamWorkPacket, ...]:
    team_ids = tuple(sorted({row.team_id for row in rows}))
    packets: list[TeamResearchTeamWorkPacket] = []
    for team_id in team_ids:
        team_assignment_rows = tuple(row for row in rows if row.team_id == team_id)
        work_rows = tuple(_work_row(row) for row in team_assignment_rows)
        packet_status = _team_packet_status(work_rows)
        packets.append(
            TeamResearchTeamWorkPacket(
                team_id=team_id,
                packet_status=packet_status,
                memory_readiness_status=_summary_memory_status(
                    tuple(row.memory_readiness_status for row in work_rows),
                ),
                memory_use_policy=_summary_memory_policy(
                    tuple(row.memory_use_policy for row in work_rows),
                ),
                assignment_count=len(work_rows),
                assigned_count=_work_status_count(work_rows, "assigned"),
                watch_count=_work_status_count(work_rows, "watch"),
                blocked_count=_work_status_count(work_rows, "blocked"),
                research_domains=_collect_codes(
                    (row.research_domain,) for row in work_rows
                ),
                research_horizons=_collect_codes(
                    (row.research_horizon,) for row in work_rows
                ),
                research_modes=_collect_codes((row.research_mode,) for row in work_rows),
                research_task_codes=_collect_codes(
                    row.research_task_codes for row in work_rows
                ),
                evidence_gap_codes=_collect_codes(
                    row.evidence_gap_codes for row in work_rows
                ),
                assignment_reason_codes=_collect_codes(
                    row.assignment_reason_codes for row in work_rows
                ),
                source_reason_codes=_collect_codes(
                    row.source_reason_codes for row in work_rows
                ),
                rows=work_rows,
            ),
        )
    return tuple(packets)


def _work_row(row: TeamResearchAssignmentRow) -> TeamResearchWorkPacketRow:
    require_paper_only_flags("assignment row", row)
    assignment_status = _work_assignment_status(
        memory_readiness_status=row.memory_readiness_status,
        memory_use_policy=row.memory_use_policy,
        assignment_status=row.assignment_status,
    )
    research_domain = _research_domain(row)
    return TeamResearchWorkPacketRow(
        research_rank=row.research_rank,
        market_slug=row.market_slug,
        question=row.question,
        selected_side=row.selected_side,
        scoring_side=row.scoring_side,
        category_id=row.category_id,
        queue_research_status=row.queue_research_status,
        queue_research_bucket=row.queue_research_bucket,
        queue_readiness_status=row.queue_readiness_status,
        memory_readiness_status=row.memory_readiness_status,
        memory_use_policy=row.memory_use_policy,
        research_domain=research_domain,
        research_horizon="long_term",
        research_mode="phase_1_report_only",
        research_task_codes=_research_task_codes(research_domain),
        assignment_status=assignment_status,
        assignment_reason_codes=row.assignment_reason_codes,
        evidence_gap_codes=row.evidence_gap_codes,
        source_reason_codes=row.source_reason_codes,
    )


def _normalize_assignment_rows(
    rows: tuple[TeamResearchAssignmentRow, ...],
) -> tuple[TeamResearchAssignmentRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("assignment rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not TeamResearchAssignmentRow:
            raise ValueError("assignment rows must contain TeamResearchAssignmentRow")
        require_paper_only_flags("assignment row", row)
    return normalized


def _normalize_work_rows(
    rows: tuple[TeamResearchWorkPacketRow, ...],
) -> tuple[TeamResearchWorkPacketRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not TeamResearchWorkPacketRow:
            raise ValueError("rows must contain TeamResearchWorkPacketRow")
        require_paper_only_flags("work packet row", row)
    return normalized


def _normalize_team_packets(
    team_packets: tuple[TeamResearchTeamWorkPacket, ...],
) -> tuple[TeamResearchTeamWorkPacket, ...]:
    if type(team_packets) not in (list, tuple):
        raise ValueError("team_packets must be a list or tuple")
    packets = tuple(team_packets)
    team_ids = tuple(packet.team_id for packet in packets)
    if team_ids != tuple(sorted(team_ids)):
        raise ValueError("team_packets must be sorted by team_id")
    if len(set(team_ids)) != len(team_ids):
        raise ValueError("team_packets must have unique team_id values")
    for packet in packets:
        if type(packet) is not TeamResearchTeamWorkPacket:
            raise ValueError("team_packets must contain TeamResearchTeamWorkPacket")
        require_paper_only_flags("team packet", packet)
    return packets


def _validate_team_packet_consistency(packet: TeamResearchTeamWorkPacket) -> None:
    if packet.assignment_count != len(packet.rows):
        raise ValueError("assignment_count must match rows")
    if packet.assigned_count != _work_status_count(packet.rows, "assigned"):
        raise ValueError("assigned_count must match rows")
    if packet.watch_count != _work_status_count(packet.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if packet.blocked_count != _work_status_count(packet.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if packet.packet_status != _team_packet_status(packet.rows):
        raise ValueError("packet_status must match rows")
    if packet.memory_readiness_status != _summary_memory_status(
        tuple(row.memory_readiness_status for row in packet.rows),
    ):
        raise ValueError("memory_readiness_status must match rows")
    if packet.memory_use_policy != _summary_memory_policy(
        tuple(row.memory_use_policy for row in packet.rows),
    ):
        raise ValueError("memory_use_policy must match rows")
    if packet.research_domains != _collect_codes(
        (row.research_domain,) for row in packet.rows
    ):
        raise ValueError("research_domains must match rows")
    if packet.research_horizons != _collect_codes(
        (row.research_horizon,) for row in packet.rows
    ):
        raise ValueError("research_horizons must match rows")
    if packet.research_modes != _collect_codes(
        (row.research_mode,) for row in packet.rows
    ):
        raise ValueError("research_modes must match rows")
    if packet.research_task_codes != _collect_codes(
        row.research_task_codes for row in packet.rows
    ):
        raise ValueError("research_task_codes must match rows")
    if packet.evidence_gap_codes != _collect_codes(
        row.evidence_gap_codes for row in packet.rows
    ):
        raise ValueError("evidence_gap_codes must match rows")
    if packet.assignment_reason_codes != _collect_codes(
        row.assignment_reason_codes for row in packet.rows
    ):
        raise ValueError("assignment_reason_codes must match rows")
    if packet.source_reason_codes != _collect_codes(
        row.source_reason_codes for row in packet.rows
    ):
        raise ValueError("source_reason_codes must match rows")


def _validate_report_consistency(report: TeamResearchWorkPacketReport) -> None:
    if report.team_packet_count != len(report.team_packets):
        raise ValueError("team_packet_count must match team_packets")
    rows = tuple(row for packet in report.team_packets for row in packet.rows)
    if report.research_assignment_count != len(rows):
        raise ValueError("research_assignment_count must match team packet rows")
    if report.assigned_count != _work_status_count(rows, "assigned"):
        raise ValueError("assigned_count must match team packet rows")
    if report.watch_count != _work_status_count(rows, "watch"):
        raise ValueError("watch_count must match team packet rows")
    if report.blocked_count != _work_status_count(rows, "blocked"):
        raise ValueError("blocked_count must match team packet rows")
    if report.packet_status != _report_packet_status(report.team_packets):
        raise ValueError("packet_status must match team_packets")
    if report.reason_codes != (REPORT_REASON_CODES[report.packet_status],):
        raise ValueError("reason_codes must match packet_status")


def _validate_payload_safety_flags(
    value: object,
    field_path: str,
    *,
    require_current_flags: bool = False,
) -> None:
    if isinstance(value, dict):
        for flag_name in SAFETY_FLAG_NAMES:
            if require_current_flags and flag_name not in value:
                raise ValueError(f"{field_path} {flag_name} must be True")
            if flag_name in value and value[flag_name] is not True:
                raise ValueError(f"{field_path} {flag_name} must be True")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _validate_payload_safety_flags(
                item,
                f"{field_path} {key}",
                require_current_flags=require_current_flags,
            )
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _validate_payload_safety_flags(
                item,
                f"{field_path} {index}",
                require_current_flags=require_current_flags,
            )


def _reject_unsafe_work_packet_fields(label: str, payload: object) -> None:
    for key in _iter_keys(payload):
        if key in HIDDEN_WORK_PACKET_FIELD_NAMES:
            continue
        normalized_key = key.lower()
        if any(
            fragment in normalized_key
            for fragment in UNSAFE_WORK_PACKET_FIELD_FRAGMENTS
        ):
            raise ValueError(f"unsafe live surface field in {label}: {key}")
    for value in _iter_string_values(payload):
        normalized_value = value.lower()
        if any(
            fragment in normalized_value
            for fragment in UNSAFE_WORK_PACKET_VALUE_FRAGMENTS
        ):
            raise ValueError(f"unsafe live surface value in {label}")


def _strip_hidden_work_packet_fields(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: _strip_hidden_work_packet_fields(item)
            for key, item in value.items()
            if key not in HIDDEN_WORK_PACKET_FIELD_NAMES
        }
    if isinstance(value, list):
        return [_strip_hidden_work_packet_fields(item) for item in value]
    return value


def _redact_sensitive_work_packet_values(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: (
                REDACTED_SENSITIVE_VALUE
                if _is_sensitive_work_packet_key(key)
                else _redact_sensitive_work_packet_values(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact_sensitive_work_packet_values(item) for item in value]
    if type(value) is str and _is_sensitive_work_packet_value(value):
        return REDACTED_SENSITIVE_VALUE
    return value


def _is_sensitive_work_packet_key(key: str) -> bool:
    normalized_key = key.lower()
    return any(
        fragment in normalized_key
        for fragment in SENSITIVE_WORK_PACKET_KEY_FRAGMENTS
    )


def _is_sensitive_work_packet_value(value: str) -> bool:
    normalized_value = value.lower()
    return any(
        fragment in normalized_value
        for fragment in SENSITIVE_WORK_PACKET_VALUE_FRAGMENTS
    )


def _add_work_packet_public_ids(value: object) -> object:
    if isinstance(value, dict):
        enriched = {
            key: _add_work_packet_public_ids(item)
            for key, item in value.items()
        }
        if _is_work_packet_row_payload(enriched) and "public_id" not in enriched:
            enriched["public_id"] = _stable_work_packet_public_id(enriched)
        return enriched
    if isinstance(value, list):
        return [_add_work_packet_public_ids(item) for item in value]
    return value


def _is_work_packet_row_payload(value: dict[str, object]) -> bool:
    return all(
        key in value
        for key in (
            "market_slug",
            "question",
            "category_id",
            "research_domain",
            "research_horizon",
            "research_mode",
            "assignment_status",
        )
    )


def _stable_work_packet_public_id(value: dict[str, object]) -> str:
    public_parts = (
        _public_id_part(value, "market_slug"),
        _public_id_part(value, "category_id"),
        _public_id_part(value, "research_domain"),
        _public_id_part(value, "research_horizon"),
        _public_id_part(value, "research_mode"),
    )
    digest = sha256("|".join(public_parts).encode("utf-8")).hexdigest()[:16]
    return f"work-packet-row-{digest}"


def _public_id_part(value: dict[str, object], field_name: str) -> str:
    field_value = value.get(field_name)
    _require_canonical_string(field_name, field_value)
    return field_value


def _iter_keys(value: object) -> tuple[str, ...]:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        keys: list[str] = []
        for field_name in value.__dataclass_fields__:
            keys.append(field_name)
            keys.extend(_iter_keys(getattr(value, field_name)))
        return tuple(keys)
    if isinstance(value, dict):
        keys = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            keys.append(key)
            keys.extend(_iter_keys(item))
        return tuple(keys)
    if isinstance(value, (list, tuple)):
        keys = []
        for item in value:
            keys.extend(_iter_keys(item))
        return tuple(keys)
    return ()


def _iter_string_values(value: object) -> tuple[str, ...]:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        values: list[str] = []
        for field_name in value.__dataclass_fields__:
            values.extend(_iter_string_values(getattr(value, field_name)))
        return tuple(values)
    if isinstance(value, dict):
        values = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            values.extend(_iter_string_values(item))
        return tuple(values)
    if isinstance(value, (list, tuple)):
        values = []
        for item in value:
            values.extend(_iter_string_values(item))
        return tuple(values)
    if type(value) is str:
        return (value,)
    return ()


def _validate_memory_policy(
    memory_readiness_status: str,
    memory_use_policy: str,
) -> None:
    expected_policy = {
        "pass": "allow",
        "watch": "throttle",
        "blocked": "block",
        "missing": "block",
    }[memory_readiness_status]
    if memory_use_policy != expected_policy:
        raise ValueError("memory_use_policy must match memory_readiness_status")


def _report_packet_status(
    team_packets: tuple[TeamResearchTeamWorkPacket, ...],
) -> str:
    if any(packet.packet_status == "blocked" for packet in team_packets):
        return "blocked"
    if any(packet.packet_status == "watch" for packet in team_packets):
        return "watch"
    if any(packet.packet_status == "assigned" for packet in team_packets):
        return "assigned"
    return "blocked"


def _team_packet_status(rows: tuple[TeamResearchWorkPacketRow, ...]) -> str:
    if any(
        row.memory_use_policy == "block"
        or row.memory_readiness_status in ("blocked", "missing")
        for row in rows
    ):
        return "blocked"
    if any(row.assignment_status == "blocked" for row in rows):
        return "blocked"
    if any(row.assignment_status == "watch" for row in rows):
        return "watch"
    return "assigned"


def _summary_memory_status(memory_statuses: tuple[str, ...]) -> str:
    if any(status in ("missing", "blocked") for status in memory_statuses):
        return "blocked" if "blocked" in memory_statuses else "missing"
    if "watch" in memory_statuses:
        return "watch"
    return "pass"


def _summary_memory_policy(memory_policies: tuple[str, ...]) -> str:
    if "block" in memory_policies:
        return "block"
    if "throttle" in memory_policies:
        return "throttle"
    return "allow"


def _work_assignment_status(
    *,
    memory_readiness_status: str,
    memory_use_policy: str,
    assignment_status: str,
) -> str:
    if memory_use_policy == "block" or memory_readiness_status in ("blocked", "missing"):
        return "blocked"
    return assignment_status


def _research_domain(row: TeamResearchAssignmentRow) -> str:
    text = " ".join((row.category_id, row.team_id, row.market_slug)).lower()
    if any(fragment in text for fragment in ("politics", "election", "congress")):
        return "politics"
    if any(
        fragment in text
        for fragment in (
            "sports",
            "basketball",
            "baseball",
            "football",
            "soccer",
            "nba",
            "mlb",
            "nfl",
            "nhl",
        )
    ):
        return "sports"
    if any(
        fragment in text
        for fragment in (
            "finance",
            "crypto",
            "macro",
            "rates",
            "equity",
            "earnings",
            "fed",
        )
    ):
        return "finance"
    return "general"


def _research_task_codes(research_domain: str) -> tuple[str, ...]:
    return _collect_codes(
        (
            BASE_RESEARCH_TASK_CODES,
            DOMAIN_RESEARCH_TASK_CODES[research_domain],
        ),
    )


def _collect_codes(values: object) -> tuple[str, ...]:
    codes: list[str] = []
    for value in values:  # type: ignore[assignment]
        for item in value:
            _require_canonical_string("reason_codes", item)
            if item not in codes:
                codes.append(item)
    return tuple(codes)


def _normalize_member_tuple(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    items = _normalize_string_tuple(field_name, value, allow_empty=allow_empty)
    for item in items:
        _require_member(field_name, item, allowed_values)
    return items


def _assignment_status_count(
    rows: tuple[TeamResearchAssignmentRow, ...],
    assignment_status: str,
) -> int:
    return sum(1 for row in rows if row.assignment_status == assignment_status)


def _work_status_count(
    rows: tuple[TeamResearchWorkPacketRow, ...],
    assignment_status: str,
) -> int:
    return sum(1 for row in rows if row.assignment_status == assignment_status)


def _normalize_string_tuple(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a tuple of canonical strings")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be a tuple of canonical strings") from exc
    if not allow_empty and not items:
        raise ValueError(f"{field_name} must contain at least one value")
    normalized: list[str] = []
    for item in items:
        _require_canonical_string(field_name, item)
        if item not in normalized:
            normalized.append(item)
    return tuple(normalized)


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {', '.join(allowed_values)}")


def _require_canonical_string(field_name: str, value: Any) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


__all__ = (
    "DEFAULT_TEAM_RESEARCH_WORK_PACKET_CONFIG_VERSION",
    "TeamResearchTeamWorkPacket",
    "TeamResearchWorkPacketConfig",
    "TeamResearchWorkPacketReport",
    "TeamResearchWorkPacketRow",
    "build_team_research_work_packet_report",
    "team_research_work_packet_payload",
)
