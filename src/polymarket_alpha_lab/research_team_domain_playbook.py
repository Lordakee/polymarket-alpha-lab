"""Pure readonly domain research playbooks for paper-only team review."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
import re
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_RESEARCH_TEAM_DOMAIN_PLAYBOOK_CONFIG_VERSION = "research-team-domain-playbook-v1"
REQUIRED_RESEARCH_TEAM_DOMAIN_IDS = (
    "politics",
    "macro",
    "crypto",
    "equity_index",
    "gold",
    "soccer",
    "basketball",
)
PUBLIC_PLAYBOOK_STATUSES = ("pass", "watch", "block")

COMMON_RESEARCH_STEP_IDS = (
    "scope_public_event",
    "collect_public_evidence",
    "summarize_scenario_drivers",
)
DOMAIN_RESEARCH_STEP_IDS = (
    "compare_polling_and_turnout_context",
    "release_calendar_review",
    "review_protocol_and_etf_catalysts",
    "map_index_calendar_and_close_window",
    "map_real_rate_and_usd_context",
    "map_fixture_and_competition_rules",
    "review_injury_and_rotation_context",
)
RESEARCH_TEAM_DOMAIN_STEP_IDS = COMMON_RESEARCH_STEP_IDS + DOMAIN_RESEARCH_STEP_IDS
RESEARCH_TEAM_DOMAIN_RISK_CHECK_IDS = (
    "resolution_rule_clarity",
    "evidence_freshness",
    "no_execution_language",
    "data_timing_risk",
    "cross_signal_conflict",
)


@dataclass(frozen=True)
class ResearchTeamDomainPlaybookConfig:
    config_version: str = DEFAULT_RESEARCH_TEAM_DOMAIN_PLAYBOOK_CONFIG_VERSION
    required_domain_ids: tuple[str, ...] = REQUIRED_RESEARCH_TEAM_DOMAIN_IDS
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_public_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "required_domain_ids",
            _normalize_domain_ids("required_domain_ids", self.required_domain_ids),
        )
        require_paper_only_flags("ResearchTeamDomainPlaybookConfig", self)
        _reject_unsafe_public_payload("ResearchTeamDomainPlaybookConfig", self)


@dataclass(frozen=True)
class ResearchTeamDomainPlaybookStep:
    step_id: str
    description: str
    public_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "step_id", _require_step_id("step_id", self.step_id))
        _require_canonical_public_string("description", self.description)
        object.__setattr__(
            self,
            "public_status",
            _require_public_status("public_status", self.public_status),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_nonempty_public_string_tuple("reason_codes", self.reason_codes),
        )
        require_paper_only_flags("ResearchTeamDomainPlaybookStep", self)
        _reject_unsafe_public_payload("ResearchTeamDomainPlaybookStep", self)


@dataclass(frozen=True)
class ResearchTeamDomainRiskCheck:
    check_id: str
    description: str
    public_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "check_id", _require_check_id("check_id", self.check_id))
        _require_canonical_public_string("description", self.description)
        object.__setattr__(
            self,
            "public_status",
            _require_public_status("public_status", self.public_status),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_nonempty_public_string_tuple("reason_codes", self.reason_codes),
        )
        require_paper_only_flags("ResearchTeamDomainRiskCheck", self)
        _reject_unsafe_public_payload("ResearchTeamDomainRiskCheck", self)


@dataclass(frozen=True)
class ResearchTeamDomainPlaybook:
    domain_id: str
    team_name: str
    public_status: str
    research_steps: tuple[ResearchTeamDomainPlaybookStep, ...]
    risk_checks: tuple[ResearchTeamDomainRiskCheck, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "domain_id", _require_domain_id("domain_id", self.domain_id))
        _require_canonical_public_string("team_name", self.team_name)
        _require_public_status("public_status", self.public_status)
        object.__setattr__(
            self,
            "research_steps",
            _normalize_steps(self.research_steps),
        )
        object.__setattr__(self, "risk_checks", _normalize_risk_checks(self.risk_checks))
        _normalize_nonempty_public_string_tuple("reason_codes", self.reason_codes)
        computed_status, computed_reason_codes = _playbook_status_and_reasons(
            self.research_steps,
            self.risk_checks,
        )
        if self.public_status != computed_status:
            raise ValueError("public_status must match playbook coverage")
        object.__setattr__(self, "reason_codes", computed_reason_codes)
        require_paper_only_flags("ResearchTeamDomainPlaybook", self)
        _reject_unsafe_public_payload("ResearchTeamDomainPlaybook", self)


@dataclass(frozen=True)
class ResearchTeamDomainPlaybookReport:
    config_version: str
    public_status: str
    domain_count: int
    playbooks: tuple[ResearchTeamDomainPlaybook, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_public_string("config_version", self.config_version)
        _require_public_status("public_status", self.public_status)
        object.__setattr__(self, "domain_count", _require_nonnegative_int("domain_count", self.domain_count))
        object.__setattr__(self, "playbooks", _normalize_playbooks(self.playbooks))
        _normalize_nonempty_public_string_tuple("reason_codes", self.reason_codes)
        if self.domain_count != len(self.playbooks):
            raise ValueError("domain_count must match playbooks")
        computed_status, computed_reason_codes = _report_status_and_reasons(self.playbooks)
        if self.public_status != computed_status:
            raise ValueError("public_status must match playbook coverage")
        object.__setattr__(self, "reason_codes", computed_reason_codes)
        require_paper_only_flags("ResearchTeamDomainPlaybookReport", self)
        _reject_unsafe_public_payload("ResearchTeamDomainPlaybookReport", self)


def build_research_team_domain_playbook(domain_id: str) -> ResearchTeamDomainPlaybook:
    normalized_domain_id = _require_domain_id("domain_id", domain_id)
    team_name, domain_step = _DOMAIN_PLAYBOOK_SPECS[normalized_domain_id]
    research_steps = tuple(
        _default_step(step_id)
        for step_id in COMMON_RESEARCH_STEP_IDS + (domain_step,)
    )
    risk_checks = tuple(_default_risk_check(check_id) for check_id in RESEARCH_TEAM_DOMAIN_RISK_CHECK_IDS)
    return ResearchTeamDomainPlaybook(
        domain_id=normalized_domain_id,
        team_name=team_name,
        public_status="pass",
        research_steps=research_steps,
        risk_checks=risk_checks,
        reason_codes=("domain_playbook_complete",),
    )


def build_default_research_team_domain_playbook_report(
    *,
    config: ResearchTeamDomainPlaybookConfig,
) -> ResearchTeamDomainPlaybookReport:
    if type(config) is not ResearchTeamDomainPlaybookConfig:
        raise ValueError("config must be a ResearchTeamDomainPlaybookConfig")
    require_paper_only_flags("ResearchTeamDomainPlaybookConfig", config)
    playbooks = tuple(build_research_team_domain_playbook(domain_id) for domain_id in config.required_domain_ids)
    return ResearchTeamDomainPlaybookReport(
        config_version=config.config_version,
        public_status="pass",
        domain_count=len(playbooks),
        playbooks=playbooks,
        reason_codes=("research_team_domain_playbook_complete",),
    )


def research_team_domain_playbook_public_payload(
    report: ResearchTeamDomainPlaybookReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamDomainPlaybookReport:
        require_paper_only_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchTeamDomainPlaybookReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_payload_flags("payload", payload)
    _reject_unsafe_public_payload("payload", payload)
    return payload


def _default_step(step_id: str) -> ResearchTeamDomainPlaybookStep:
    return ResearchTeamDomainPlaybookStep(
        step_id=_require_step_id("step_id", step_id),
        description=_STEP_DESCRIPTIONS[step_id],
        public_status="pass",
        reason_codes=(f"{step_id}_ready",),
    )


def _default_risk_check(check_id: str) -> ResearchTeamDomainRiskCheck:
    return ResearchTeamDomainRiskCheck(
        check_id=_require_check_id("check_id", check_id),
        description=_RISK_CHECK_DESCRIPTIONS[check_id],
        public_status="pass",
        reason_codes=(f"{check_id}_ready",),
    )


def _playbook_status_and_reasons(
    research_steps: tuple[ResearchTeamDomainPlaybookStep, ...],
    risk_checks: tuple[ResearchTeamDomainRiskCheck, ...],
) -> tuple[str, tuple[str, ...]]:
    blocked_steps = tuple(step.step_id for step in research_steps if step.public_status == "block")
    blocked_checks = tuple(check.check_id for check in risk_checks if check.public_status == "block")
    watch_steps = tuple(step.step_id for step in research_steps if step.public_status == "watch")
    watch_checks = tuple(check.check_id for check in risk_checks if check.public_status == "watch")

    if blocked_steps or blocked_checks:
        status = "block"
    elif watch_steps or watch_checks:
        status = "watch"
    else:
        status = "pass"

    reason_codes = tuple(f"step_blocked_{step_id}" for step_id in blocked_steps)
    reason_codes += tuple(f"risk_blocked_{check_id}" for check_id in blocked_checks)
    reason_codes += tuple(f"step_watch_{step_id}" for step_id in watch_steps)
    reason_codes += tuple(f"risk_watch_{check_id}" for check_id in watch_checks)
    if not reason_codes:
        reason_codes = ("domain_playbook_complete",)
    return status, reason_codes


def _report_status_and_reasons(
    playbooks: tuple[ResearchTeamDomainPlaybook, ...],
) -> tuple[str, tuple[str, ...]]:
    present_domain_ids = tuple(playbook.domain_id for playbook in playbooks)
    missing_domain_ids = tuple(
        domain_id for domain_id in REQUIRED_RESEARCH_TEAM_DOMAIN_IDS if domain_id not in present_domain_ids
    )
    blocked_domain_ids = tuple(
        playbook.domain_id for playbook in playbooks if playbook.public_status == "block"
    )
    watch_domain_ids = tuple(
        playbook.domain_id for playbook in playbooks if playbook.public_status == "watch"
    )

    if blocked_domain_ids:
        status = "block"
    elif missing_domain_ids or watch_domain_ids:
        status = "watch"
    else:
        status = "pass"

    reason_codes = tuple(f"domain_blocked_{domain_id}" for domain_id in blocked_domain_ids)
    reason_codes += tuple(f"missing_required_domain_{domain_id}" for domain_id in missing_domain_ids)
    reason_codes += tuple(f"domain_watch_{domain_id}" for domain_id in watch_domain_ids)
    if not reason_codes:
        reason_codes = ("research_team_domain_playbook_complete",)
    return status, reason_codes


def _normalize_domain_ids(field_name: str, value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must be nonempty")
    for item in value:
        _require_domain_id(field_name, item)
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} must not contain duplicates")
    expected_order = tuple(domain_id for domain_id in REQUIRED_RESEARCH_TEAM_DOMAIN_IDS if domain_id in value)
    if value != expected_order:
        raise ValueError(f"{field_name} must follow required domain order")
    return value


def _normalize_steps(
    research_steps: tuple[ResearchTeamDomainPlaybookStep, ...],
) -> tuple[ResearchTeamDomainPlaybookStep, ...]:
    if type(research_steps) is not tuple:
        raise ValueError("research_steps must be a tuple")
    if not research_steps:
        raise ValueError("research_steps must be nonempty")
    step_ids = tuple(step.step_id for step in research_steps)
    if len(set(step_ids)) != len(step_ids):
        raise ValueError("research_steps must not contain duplicates")
    for step in research_steps:
        if type(step) is not ResearchTeamDomainPlaybookStep:
            raise ValueError("research_steps must contain ResearchTeamDomainPlaybookStep values")
        require_paper_only_flags("ResearchTeamDomainPlaybookStep", step)
    return research_steps


def _normalize_risk_checks(
    risk_checks: tuple[ResearchTeamDomainRiskCheck, ...],
) -> tuple[ResearchTeamDomainRiskCheck, ...]:
    if type(risk_checks) is not tuple:
        raise ValueError("risk_checks must be a tuple")
    if not risk_checks:
        raise ValueError("risk_checks must be nonempty")
    check_ids = tuple(check.check_id for check in risk_checks)
    if len(set(check_ids)) != len(check_ids):
        raise ValueError("risk_checks must not contain duplicates")
    for check in risk_checks:
        if type(check) is not ResearchTeamDomainRiskCheck:
            raise ValueError("risk_checks must contain ResearchTeamDomainRiskCheck values")
        require_paper_only_flags("ResearchTeamDomainRiskCheck", check)
    return risk_checks


def _normalize_playbooks(
    playbooks: tuple[ResearchTeamDomainPlaybook, ...],
) -> tuple[ResearchTeamDomainPlaybook, ...]:
    if type(playbooks) is not tuple:
        raise ValueError("playbooks must be a tuple")
    domain_ids = tuple(playbook.domain_id for playbook in playbooks)
    if len(set(domain_ids)) != len(domain_ids):
        raise ValueError("playbooks must not contain duplicates")
    expected_order = tuple(domain_id for domain_id in REQUIRED_RESEARCH_TEAM_DOMAIN_IDS if domain_id in domain_ids)
    if domain_ids != expected_order:
        raise ValueError("playbooks must follow required domain order")
    for playbook in playbooks:
        if type(playbook) is not ResearchTeamDomainPlaybook:
            raise ValueError("playbooks must contain ResearchTeamDomainPlaybook values")
        require_paper_only_flags("ResearchTeamDomainPlaybook", playbook)
    return playbooks


def _normalize_nonempty_public_string_tuple(
    field_name: str,
    value: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must be nonempty")
    normalized = tuple(_require_canonical_public_string(field_name, item) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    return normalized


def _require_domain_id(field_name: str, value: object) -> str:
    if type(value) is not str or value not in REQUIRED_RESEARCH_TEAM_DOMAIN_IDS:
        raise ValueError(f"{field_name} must be a required research domain")
    return value


def _require_step_id(field_name: str, value: object) -> str:
    if type(value) is not str or value not in RESEARCH_TEAM_DOMAIN_STEP_IDS:
        raise ValueError(f"{field_name} must be a known research step")
    return value


def _require_check_id(field_name: str, value: object) -> str:
    if type(value) is not str or value not in RESEARCH_TEAM_DOMAIN_RISK_CHECK_IDS:
        raise ValueError(f"{field_name} must be a known risk check")
    return value


def _require_public_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in PUBLIC_PLAYBOOK_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_nonnegative_int(field_name: str, value: object) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field_name} must be a nonnegative int")
    return value


def _require_canonical_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")
    _reject_unsafe_public_text(field_name, value)
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
            _reject_unsafe_public_key(key)
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
            _reject_unsafe_public_key(key)
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


def _reject_unsafe_public_key(value: str) -> None:
    normalized = value.casefold()
    if any(fragment in normalized for fragment in _FORBIDDEN_PUBLIC_KEY_FRAGMENTS):
        raise ValueError(f"unsafe public field in payload: {value}")


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.casefold()
    if any(pattern.search(normalized) for pattern in _FORBIDDEN_PUBLIC_VALUE_PATTERNS):
        raise ValueError(f"{label} has unsafe public playbook text")


def _require_payload_flags(label: str, payload: dict[str, Any]) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if flag_name not in payload or payload[flag_name] is not True:
            raise ValueError(f"{flag_name} must be True for {label}")


_DOMAIN_PLAYBOOK_SPECS: dict[str, tuple[str, str]] = {
    "politics": ("Politics Research Team", "compare_polling_and_turnout_context"),
    "macro": ("Macro Research Team", "release_calendar_review"),
    "crypto": ("Crypto Research Team", "review_protocol_and_etf_catalysts"),
    "equity_index": ("Equity Index Research Team", "map_index_calendar_and_close_window"),
    "gold": ("Gold Research Team", "map_real_rate_and_usd_context"),
    "soccer": ("Soccer Research Team", "map_fixture_and_competition_rules"),
    "basketball": ("Basketball Research Team", "review_injury_and_rotation_context"),
}

_STEP_DESCRIPTIONS = {
    "scope_public_event": "Define the public event boundary and settlement timing.",
    "collect_public_evidence": "Collect public evidence families with freshness notes.",
    "summarize_scenario_drivers": "Summarize base, upside, and downside research drivers.",
    "compare_polling_and_turnout_context": "Compare polling, turnout, and institutional timing context.",
    "release_calendar_review": "Review macro release timing and consensus dispersion.",
    "review_protocol_and_etf_catalysts": "Review protocol, ETF, and liquidity catalyst context.",
    "map_index_calendar_and_close_window": "Map index calendar, volatility, and closing-window context.",
    "map_real_rate_and_usd_context": "Map real-rate, USD, and precious-metal context.",
    "map_fixture_and_competition_rules": "Map fixture timing, competition rules, and squad context.",
    "review_injury_and_rotation_context": "Review injury, rest, and rotation context.",
}

_RISK_CHECK_DESCRIPTIONS = {
    "resolution_rule_clarity": "Verify settlement rules are clear and externally checkable.",
    "evidence_freshness": "Flag stale public evidence or thin coverage.",
    "no_execution_language": "Verify the output remains research-only and action-neutral.",
    "data_timing_risk": "Check timing mismatches across published datasets.",
    "cross_signal_conflict": "Surface material conflicts across independent public signals.",
}

_FORBIDDEN_PUBLIC_KEY_FRAGMENTS = frozenset(
    (
        "raw",
        "candidate",
        "condition",
        "market",
        "slug",
        "question",
        "source",
        "ref",
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
    )
)

_FORBIDDEN_PUBLIC_VALUE_PATTERNS = tuple(
    re.compile(pattern)
    for pattern in (
        r"\braw\b",
        r"\bcandidate(?:[-_ ]?id|\b)",
        r"\bcondition[-_ ]?id\b",
        r"\bmarket(?:[-_ ]?(?:id|slug)|\s+slug|\b)",
        r"\bslug\b",
        r"\bquestion\b",
        r"\bsource[-_ ]?(?:ref|url|text)\b",
        r"https?://",
        r"\burl\b",
        r"\bdsn\b",
        r"\btable\b",
        r"\btoken\b",
        r"\bwallet\b",
        r"\bauth\b",
        r"\border\b",
        r"\btrade\b",
        r"\bposition\b",
        r"\bnotional\b",
        r"\bbuy\b",
        r"\bsell\b",
        r"\brecommend(?:ation|ed|ing)?\b",
    )
)


__all__ = (
    "COMMON_RESEARCH_STEP_IDS",
    "DEFAULT_RESEARCH_TEAM_DOMAIN_PLAYBOOK_CONFIG_VERSION",
    "DOMAIN_RESEARCH_STEP_IDS",
    "PUBLIC_PLAYBOOK_STATUSES",
    "REQUIRED_RESEARCH_TEAM_DOMAIN_IDS",
    "RESEARCH_TEAM_DOMAIN_RISK_CHECK_IDS",
    "RESEARCH_TEAM_DOMAIN_STEP_IDS",
    "ResearchTeamDomainPlaybook",
    "ResearchTeamDomainPlaybookConfig",
    "ResearchTeamDomainPlaybookReport",
    "ResearchTeamDomainPlaybookStep",
    "ResearchTeamDomainRiskCheck",
    "build_default_research_team_domain_playbook_report",
    "build_research_team_domain_playbook",
    "research_team_domain_playbook_public_payload",
)
