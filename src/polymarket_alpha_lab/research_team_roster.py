"""Pure readonly research-team roster blueprint for paper strategy review."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from typing import Any

from polymarket_alpha_lab.strategy_team_taxonomy import (
    STRATEGY_TEAM_IDS,
    require_strategy_team_id,
)
from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_RESEARCH_TEAM_ROSTER_CONFIG_VERSION = "research-team-roster-v1"
RESEARCH_TEAM_ROSTER_ROLE_IDS = (
    "lead",
    "evidence_scout",
    "probability_analyst",
    "risk_reviewer",
    "memory_curator",
)
PUBLIC_ROSTER_STATUSES = ("pass", "watch", "block")


@dataclass(frozen=True)
class ResearchTeamRosterConfig:
    config_version: str = DEFAULT_RESEARCH_TEAM_ROSTER_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        require_paper_only_flags("ResearchTeamRosterConfig", self)


@dataclass(frozen=True)
class ResearchTeamRosterRole:
    role_id: str
    title: str
    status: str
    responsibilities: tuple[str, ...]
    audit_outputs: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "role_id", _require_roster_role_id("role_id", self.role_id))
        _require_canonical_string("title", self.title)
        object.__setattr__(self, "status", _require_status("status", self.status))
        object.__setattr__(
            self,
            "responsibilities",
            _normalize_nonempty_string_tuple(
                "responsibilities",
                self.responsibilities,
            ),
        )
        object.__setattr__(
            self,
            "audit_outputs",
            _normalize_nonempty_string_tuple("audit_outputs", self.audit_outputs),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_nonempty_string_tuple("reason_codes", self.reason_codes),
        )
        require_paper_only_flags("ResearchTeamRosterRole", self)


@dataclass(frozen=True)
class ResearchTeamRosterEntry:
    team_id: str
    display_name: str
    status: str
    roles: tuple[ResearchTeamRosterRole, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_strategy_team_id("team_id", self.team_id))
        _require_canonical_string("display_name", self.display_name)
        _require_status("status", self.status)
        object.__setattr__(self, "roles", _normalize_roles(self.roles))
        _normalize_nonempty_string_tuple("reason_codes", self.reason_codes)
        computed_status, computed_reason_codes = _entry_status_and_reasons(self.roles)
        if self.status != computed_status:
            raise ValueError("status must match role coverage")
        object.__setattr__(self, "reason_codes", computed_reason_codes)
        require_paper_only_flags("ResearchTeamRosterEntry", self)


@dataclass(frozen=True)
class ResearchTeamRoster:
    config_version: str
    status: str
    team_count: int
    role_count: int
    entries: tuple[ResearchTeamRosterEntry, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_status("status", self.status)
        object.__setattr__(self, "team_count", _require_positive_int("team_count", self.team_count))
        object.__setattr__(self, "role_count", _require_positive_int("role_count", self.role_count))
        object.__setattr__(self, "entries", _normalize_entries(self.entries))
        _normalize_nonempty_string_tuple("reason_codes", self.reason_codes)
        if self.team_count != len(self.entries):
            raise ValueError("team_count must match entries")
        if self.role_count != sum(len(entry.roles) for entry in self.entries):
            raise ValueError("role_count must match roles")
        computed_status, computed_reason_codes = _roster_status_and_reasons(self.entries)
        if self.status != computed_status:
            raise ValueError("status must match team coverage")
        object.__setattr__(self, "reason_codes", computed_reason_codes)
        require_paper_only_flags("ResearchTeamRoster", self)


def build_default_research_team_roster(
    *,
    config: ResearchTeamRosterConfig,
) -> ResearchTeamRoster:
    if type(config) is not ResearchTeamRosterConfig:
        raise ValueError("config must be a ResearchTeamRosterConfig")
    require_paper_only_flags("ResearchTeamRosterConfig", config)
    entries = tuple(_default_entry(team_id) for team_id in STRATEGY_TEAM_IDS)
    return ResearchTeamRoster(
        config_version=config.config_version,
        status="pass",
        team_count=len(entries),
        role_count=sum(len(entry.roles) for entry in entries),
        entries=entries,
        reason_codes=("research_team_roster_complete",),
    )


def research_team_roster_public_payload(
    report: ResearchTeamRoster | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamRoster:
        require_paper_only_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchTeamRoster")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_payload_flags("payload", payload)
    _reject_unsafe_public_payload("payload", payload)
    return payload


def _default_entry(team_id: str) -> ResearchTeamRosterEntry:
    normalized_team_id = require_strategy_team_id("team_id", team_id)
    roles = tuple(_default_role(role_id) for role_id in RESEARCH_TEAM_ROSTER_ROLE_IDS)
    return ResearchTeamRosterEntry(
        team_id=normalized_team_id,
        display_name=_TEAM_DISPLAY_NAMES[normalized_team_id],
        status="pass",
        roles=roles,
        reason_codes=("team_roster_complete",),
    )


def _default_role(role_id: str) -> ResearchTeamRosterRole:
    title, responsibilities, audit_outputs = _ROLE_SPECS[
        _require_roster_role_id("role_id", role_id)
    ]
    return ResearchTeamRosterRole(
        role_id=role_id,
        title=title,
        status="pass",
        responsibilities=responsibilities,
        audit_outputs=audit_outputs,
        reason_codes=(f"{role_id}_ready",),
    )


def _entry_status_and_reasons(
    roles: tuple[ResearchTeamRosterRole, ...],
) -> tuple[str, tuple[str, ...]]:
    present_role_ids = tuple(role.role_id for role in roles)
    missing_role_ids = tuple(
        role_id
        for role_id in RESEARCH_TEAM_ROSTER_ROLE_IDS
        if role_id not in present_role_ids
    )
    blocked_role_ids = tuple(
        role_id
        for role_id in RESEARCH_TEAM_ROSTER_ROLE_IDS
        if _role_status_for_id(roles, role_id) == "block"
    )
    watch_role_ids = tuple(
        role_id
        for role_id in RESEARCH_TEAM_ROSTER_ROLE_IDS
        if _role_status_for_id(roles, role_id) == "watch"
    )

    if blocked_role_ids:
        status = "block"
    elif missing_role_ids or watch_role_ids:
        status = "watch"
    else:
        status = "pass"

    reason_codes = tuple(f"role_blocked_{role_id}" for role_id in blocked_role_ids)
    reason_codes += tuple(
        f"missing_required_role_{role_id}" for role_id in missing_role_ids
    )
    reason_codes += tuple(f"role_watch_{role_id}" for role_id in watch_role_ids)
    if not reason_codes:
        reason_codes = ("team_roster_complete",)
    return status, reason_codes


def _roster_status_and_reasons(
    entries: tuple[ResearchTeamRosterEntry, ...],
) -> tuple[str, tuple[str, ...]]:
    present_team_ids = tuple(entry.team_id for entry in entries)
    missing_team_ids = tuple(
        team_id for team_id in STRATEGY_TEAM_IDS if team_id not in present_team_ids
    )
    blocked_team_ids = tuple(
        entry.team_id for entry in entries if entry.status == "block"
    )
    watch_team_ids = tuple(entry.team_id for entry in entries if entry.status == "watch")

    if blocked_team_ids:
        status = "block"
    elif missing_team_ids or watch_team_ids:
        status = "watch"
    else:
        status = "pass"

    reason_codes = tuple(f"team_blocked_{team_id}" for team_id in blocked_team_ids)
    reason_codes += tuple(
        f"missing_required_team_{team_id}" for team_id in missing_team_ids
    )
    reason_codes += tuple(f"team_watch_{team_id}" for team_id in watch_team_ids)
    if not reason_codes:
        reason_codes = ("research_team_roster_complete",)
    return status, reason_codes


def _role_status_for_id(
    roles: tuple[ResearchTeamRosterRole, ...],
    role_id: str,
) -> str | None:
    for role in roles:
        if role.role_id == role_id:
            return role.status
    return None


def _normalize_roles(
    roles: tuple[ResearchTeamRosterRole, ...],
) -> tuple[ResearchTeamRosterRole, ...]:
    if type(roles) is not tuple:
        raise ValueError("roles must be a tuple")
    role_ids = tuple(role.role_id for role in roles)
    if len(set(role_ids)) != len(role_ids):
        raise ValueError("roles must not contain duplicates")
    expected_order = tuple(
        role_id for role_id in RESEARCH_TEAM_ROSTER_ROLE_IDS if role_id in role_ids
    )
    if role_ids != expected_order:
        raise ValueError("roles must follow roster role order")
    for role in roles:
        if type(role) is not ResearchTeamRosterRole:
            raise ValueError("roles must contain ResearchTeamRosterRole values")
        require_paper_only_flags("ResearchTeamRosterRole", role)
    return roles


def _normalize_entries(
    entries: tuple[ResearchTeamRosterEntry, ...],
) -> tuple[ResearchTeamRosterEntry, ...]:
    if type(entries) is not tuple:
        raise ValueError("entries must be a tuple")
    team_ids = tuple(entry.team_id for entry in entries)
    if len(set(team_ids)) != len(team_ids):
        raise ValueError("entries must not contain duplicates")
    expected_order = tuple(team_id for team_id in STRATEGY_TEAM_IDS if team_id in team_ids)
    if team_ids != expected_order:
        raise ValueError("entries must follow strategy team order")
    for entry in entries:
        if type(entry) is not ResearchTeamRosterEntry:
            raise ValueError("entries must contain ResearchTeamRosterEntry values")
        require_paper_only_flags("ResearchTeamRosterEntry", entry)
    return entries


def _normalize_nonempty_string_tuple(
    field_name: str,
    value: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must be nonempty")
    normalized = tuple(_require_canonical_string(field_name, item) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    return normalized


def _require_roster_role_id(field_name: str, value: object) -> str:
    if type(value) is not str or value not in RESEARCH_TEAM_ROSTER_ROLE_IDS:
        raise ValueError(f"{field_name} must be a known research roster role")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in PUBLIC_ROSTER_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise ValueError(f"{field_name} must be a canonical string")
    return value


def _require_positive_int(field_name: str, value: object) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{field_name} must be a positive int")
    return value


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if value is None:
        return None
    if type(value) is bool:
        return value
    if type(value) is int:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is str:
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(nested_value)
        return ready
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        _reject_unsafe_public_text(path or label, value)
        return
    if value is None or type(value) in (bool, int):
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, dict):
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            _reject_unsafe_public_text(f"{label} field", key)
            if key in ("paper_only", "report_only", "readonly") and nested_value is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_public_payload(label, nested_value, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, nested_value in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, nested_value, nested_path)
        return
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.casefold()
    if any(fragment in normalized for fragment in _FORBIDDEN_PUBLIC_FRAGMENTS):
        raise ValueError(f"{label} has unsafe public roster text")


def _require_payload_flags(label: str, payload: dict[str, Any]) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if flag_name not in payload or payload[flag_name] is not True:
            raise ValueError(f"{flag_name} must be True for {label}")


_ROLE_SPECS: dict[str, tuple[str, tuple[str, ...], tuple[str, ...]]] = {
    "lead": (
        "Research Lead",
        (
            "coordinate_domain_research_review",
            "set_evidence_acceptance_criteria",
            "synthesize_audit_ready_findings",
        ),
        (
            "team_brief",
            "status_rationale",
            "review_handoff",
        ),
    ),
    "evidence_scout": (
        "Evidence Scout",
        (
            "collect_public_evidence",
            "verify_evidence_family_diversity",
            "flag_stale_or_unclear_evidence",
        ),
        (
            "evidence_summary",
            "freshness_notes",
            "coverage_gaps",
        ),
    ),
    "probability_analyst": (
        "Probability Analyst",
        (
            "calibrate_probability_range",
            "record_assumption_sensitivity",
            "compare_base_rate_to_current_view",
        ),
        (
            "probability_bridge",
            "assumption_log",
            "scenario_bounds",
        ),
    ),
    "risk_reviewer": (
        "Risk Reviewer",
        (
            "surface_resolution_and_data_risks",
            "challenge_evidence_quality",
            "verify_no_execution_language",
        ),
        (
            "risk_register",
            "blocker_notes",
            "guardrail_check",
        ),
    ),
    "memory_curator": (
        "Memory Curator",
        (
            "maintain_non_persistent_research_memory",
            "deduplicate_prior_findings",
            "preserve_audit_reason_codes",
        ),
        (
            "memory_snapshot",
            "prior_findings_index",
            "reason_code_map",
        ),
    ),
}

_TEAM_DISPLAY_NAMES = {
    "politics": "Politics Research Team",
    "crypto_btc": "Crypto BTC Research Team",
    "equity_index": "Equity Index Research Team",
    "commodities_gold": "Commodities Gold Research Team",
    "soccer": "Soccer Research Team",
    "basketball": "Basketball Research Team",
    "other_sports": "Other Sports Research Team",
    "general": "General Research Team",
}

_FORBIDDEN_PUBLIC_FRAGMENTS = frozenset(
    (
        "candidate",
        "condition_id",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "notional",
        "buy",
        "sell",
        "recommend",
        "recommendation",
    )
)


__all__ = (
    "DEFAULT_RESEARCH_TEAM_ROSTER_CONFIG_VERSION",
    "PUBLIC_ROSTER_STATUSES",
    "RESEARCH_TEAM_ROSTER_ROLE_IDS",
    "ResearchTeamRoster",
    "ResearchTeamRosterConfig",
    "ResearchTeamRosterEntry",
    "ResearchTeamRosterRole",
    "build_default_research_team_roster",
    "research_team_roster_public_payload",
)
