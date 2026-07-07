"""Pure report-only audit for sanitized research team routing consistency."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal
from hashlib import sha256
import json
import re
from typing import Any, Sequence

from polymarket_alpha_lab.research_market_event_type_router import (
    ResearchMarketEventTypeRoute,
)
from polymarket_alpha_lab.research_team_capacity_planner import (
    ResearchTeamCapacityPlannerReport,
    ResearchTeamCapacityPlannerRow,
)
from polymarket_alpha_lab.research_team_domain_memory_summary import (
    ResearchTeamDomainMemorySummaryReport,
    ResearchTeamDomainMemorySummaryRow,
)
from polymarket_alpha_lab.research_team_domain_playbook import (
    ResearchTeamDomainPlaybook,
    ResearchTeamDomainPlaybookReport,
)


DEFAULT_RESEARCH_TEAM_ROUTING_AUDIT_CONFIG_VERSION = "research-team-routing-audit-v1"

ROUTING_AUDIT_STATUSES = ("pass", "watch", "block")
ROUTING_AUDIT_COMPONENT_CODES = (
    "sanitized_event_type",
    "domain_playbook",
    "team_capacity",
    "domain_memory",
)

_QUANT = Decimal("0.000001")
_COUNT_QUANT = Decimal("1")
_ZERO = Decimal("0.000000")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))

_QUEUE_TO_DOMAIN = {
    "politics": "politics",
    "macro": "macro",
    "crypto": "crypto",
    "equities": "equity_index",
    "equity_index": "equity_index",
    "metals": "gold",
    "gold": "gold",
    "football": "soccer",
    "soccer": "soccer",
    "basketball": "basketball",
}

_COMPONENT_REASON_CODE_SEQUENCE = (
    "sanitized_event_type_pass",
    "sanitized_event_type_watch",
    "sanitized_event_type_block",
    "routed_domain_mapped",
    "routed_domain_unassigned",
    "domain_playbook_pass",
    "domain_playbook_watch",
    "domain_playbook_block",
    "domain_playbook_missing",
    "domain_playbook_unassigned_domain",
    "team_capacity_pass",
    "team_capacity_watch",
    "team_capacity_block",
    "team_capacity_missing",
    "team_capacity_unassigned_domain",
    "domain_memory_pass",
    "domain_memory_watch",
    "domain_memory_block",
    "domain_memory_missing",
    "domain_memory_unassigned_domain",
)

_REPORT_REASON_CODE_SEQUENCE = (
    "routing_audit_pass",
    "routing_audit_watch_components",
    "routing_audit_block_components",
)

_UNSAFE_PUBLIC_KEY_FRAGMENTS = frozenset(
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
    ),
)

_UNSAFE_PUBLIC_VALUE_PATTERNS = tuple(
    re.compile(pattern)
    for pattern in (
        r"\braw\b",
        r"\bcandidate(?:[-_ ]?id|\b)",
        r"\bcondition[-_ ]?id\b",
        r"\bmarket[-_ ]?(?:id|slug|question)\b",
        r"\bmarket\s+slug\b",
        r"\bquestion\b",
        r"\bsource(?:[-_ ]?(?:ref|url|text))?\b",
        r"\bref\b",
        r"https?://",
        r"\burl\b",
        r"\bdsn\b",
        r"\bdatabase\b",
        r"\btable\b",
        r"\btoken\b",
        r"\bwallet\b",
        r"\bauth(?:entication|orization)?\b",
        r"\border\b",
        r"\btrade\b",
        r"\bposition\b",
        r"\bbuy\b",
        r"\bsell\b",
        r"\brecommend(?:ation|ed|ing)?\b",
    )
)


@dataclass(frozen=True)
class ResearchTeamRoutingAuditConfig:
    config_version: str = DEFAULT_RESEARCH_TEAM_ROUTING_AUDIT_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamRoutingAuditConfig:
            raise ValueError("config must be exactly ResearchTeamRoutingAuditConfig")
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchTeamRoutingAuditComponent:
    component_code: str
    audited_domain_code: str | None
    component_status: str
    observed_status: str | None
    row_count: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamRoutingAuditComponent:
            raise ValueError("component must be exactly ResearchTeamRoutingAuditComponent")
        object.__setattr__(
            self,
            "component_code",
            _require_component_code("component_code", self.component_code),
        )
        object.__setattr__(
            self,
            "audited_domain_code",
            _normalize_optional_domain_code(
                "audited_domain_code",
                self.audited_domain_code,
            ),
        )
        object.__setattr__(
            self,
            "component_status",
            _require_status("component_status", self.component_status),
        )
        object.__setattr__(
            self,
            "observed_status",
            _normalize_optional_status("observed_status", self.observed_status),
        )
        object.__setattr__(
            self,
            "row_count",
            _require_nonnegative_count_decimal("row_count", self.row_count),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_component_reason_codes(self.reason_codes),
        )
        _validate_component(self)
        _require_hard_flags("component", self)
        _reject_unsafe_public_payload("component", self)


@dataclass(frozen=True)
class ResearchTeamRoutingAuditReport:
    config_version: str
    audit_status: str
    public_event_type: str
    public_category_hint: str
    routed_domain_code: str | None
    audited_component_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    components: tuple[ResearchTeamRoutingAuditComponent, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamRoutingAuditReport:
            raise ValueError("report must be exactly ResearchTeamRoutingAuditReport")
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        object.__setattr__(
            self,
            "audit_status",
            _require_status("audit_status", self.audit_status),
        )
        object.__setattr__(
            self,
            "public_event_type",
            _require_public_text("public_event_type", self.public_event_type),
        )
        object.__setattr__(
            self,
            "public_category_hint",
            _require_public_text("public_category_hint", self.public_category_hint),
        )
        object.__setattr__(
            self,
            "routed_domain_code",
            _normalize_optional_domain_code("routed_domain_code", self.routed_domain_code),
        )
        for field_name in (
            "audited_component_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "components", _normalize_components(self.components))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _digest_public_value(_report_values_without_digest(self))
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report fields")
        object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        payload = _json_ready(asdict(self))
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        _require_hard_flags("payload", _DictFlags(payload))
        _reject_unsafe_public_payload("payload", payload)
        _validate_payload_digest(payload)
        return payload


def build_research_team_routing_audit_report(
    *,
    event_route: ResearchMarketEventTypeRoute,
    playbook_report: ResearchTeamDomainPlaybookReport,
    capacity_report: ResearchTeamCapacityPlannerReport,
    memory_report: ResearchTeamDomainMemorySummaryReport,
    config: ResearchTeamRoutingAuditConfig | None = None,
) -> ResearchTeamRoutingAuditReport:
    active_config = ResearchTeamRoutingAuditConfig() if config is None else config
    if type(active_config) is not ResearchTeamRoutingAuditConfig:
        raise ValueError("config must be exactly ResearchTeamRoutingAuditConfig")
    if type(event_route) is not ResearchMarketEventTypeRoute:
        raise ValueError("event_route must be exactly ResearchMarketEventTypeRoute")
    if type(playbook_report) is not ResearchTeamDomainPlaybookReport:
        raise ValueError("playbook_report must be exactly ResearchTeamDomainPlaybookReport")
    if type(capacity_report) is not ResearchTeamCapacityPlannerReport:
        raise ValueError("capacity_report must be exactly ResearchTeamCapacityPlannerReport")
    if type(memory_report) is not ResearchTeamDomainMemorySummaryReport:
        raise ValueError("memory_report must be exactly ResearchTeamDomainMemorySummaryReport")
    for label, value in (
        ("config", active_config),
        ("event_route", event_route),
        ("playbook_report", playbook_report),
        ("capacity_report", capacity_report),
        ("memory_report", memory_report),
    ):
        _require_hard_flags(label, value)
        _reject_external_unsafe_public_surface(label, value)

    routed_domain_code = _domain_code_from_route(event_route)
    components = (
        _event_type_component(event_route, routed_domain_code),
        _playbook_component(playbook_report, routed_domain_code, event_route.route_status),
        _capacity_component(capacity_report, routed_domain_code, event_route.route_status),
        _memory_component(memory_report, routed_domain_code, event_route.route_status),
    )
    values: dict[str, object] = {
        "config_version": active_config.config_version,
        "audit_status": _report_status(components),
        "public_event_type": event_route.public_event_type,
        "public_category_hint": event_route.public_category_hint,
        "routed_domain_code": routed_domain_code,
        "audited_component_count": _decimal_count(len(components)),
        "pass_count": _decimal_count(_status_count(components, "pass")),
        "watch_count": _decimal_count(_status_count(components, "watch")),
        "block_count": _decimal_count(_status_count(components, "block")),
        "components": components,
        "reason_codes": _report_reason_codes(components),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchTeamRoutingAuditReport(
        **values,
        derived_validation_digest=_digest_public_value(values),
    )


def research_team_routing_audit_report_payload(
    report: ResearchTeamRoutingAuditReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamRoutingAuditReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        return report.payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        _require_hard_flags("payload", _DictFlags(payload))
        _validate_payload_digest(payload)
        _reject_unsafe_public_payload("payload", payload)
        return payload
    raise ValueError("report must be a ResearchTeamRoutingAuditReport or payload")


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


def _event_type_component(
    route: ResearchMarketEventTypeRoute,
    routed_domain_code: str | None,
) -> ResearchTeamRoutingAuditComponent:
    reason_codes = [f"sanitized_event_type_{route.route_status}"]
    if routed_domain_code is None:
        reason_codes.append("routed_domain_unassigned")
    else:
        reason_codes.append("routed_domain_mapped")
    return ResearchTeamRoutingAuditComponent(
        component_code="sanitized_event_type",
        audited_domain_code=routed_domain_code,
        component_status=route.route_status,
        observed_status=route.route_status,
        row_count=_decimal_count(1),
        reason_codes=tuple(reason_codes),
    )


def _playbook_component(
    report: ResearchTeamDomainPlaybookReport,
    routed_domain_code: str | None,
    route_status: str,
) -> ResearchTeamRoutingAuditComponent:
    if routed_domain_code is None:
        status = "block" if route_status == "block" else "watch"
        return ResearchTeamRoutingAuditComponent(
            component_code="domain_playbook",
            audited_domain_code=None,
            component_status=status,
            observed_status=None,
            row_count=_ZERO,
            reason_codes=("domain_playbook_unassigned_domain",),
        )
    playbook = _playbook_for_domain(report.playbooks, routed_domain_code)
    if playbook is None:
        return ResearchTeamRoutingAuditComponent(
            component_code="domain_playbook",
            audited_domain_code=routed_domain_code,
            component_status="block",
            observed_status=None,
            row_count=_ZERO,
            reason_codes=("domain_playbook_missing",),
        )
    return ResearchTeamRoutingAuditComponent(
        component_code="domain_playbook",
        audited_domain_code=routed_domain_code,
        component_status=playbook.public_status,
        observed_status=playbook.public_status,
        row_count=_decimal_count(1),
        reason_codes=(f"domain_playbook_{playbook.public_status}",),
    )


def _capacity_component(
    report: ResearchTeamCapacityPlannerReport,
    routed_domain_code: str | None,
    route_status: str,
) -> ResearchTeamRoutingAuditComponent:
    if routed_domain_code is None:
        status = "block" if route_status == "block" else "watch"
        return ResearchTeamRoutingAuditComponent(
            component_code="team_capacity",
            audited_domain_code=None,
            component_status=status,
            observed_status=None,
            row_count=_ZERO,
            reason_codes=("team_capacity_unassigned_domain",),
        )
    rows = _capacity_rows_for_domain(report.rows, routed_domain_code)
    if not rows:
        return ResearchTeamRoutingAuditComponent(
            component_code="team_capacity",
            audited_domain_code=routed_domain_code,
            component_status="block",
            observed_status=None,
            row_count=_ZERO,
            reason_codes=("team_capacity_missing",),
        )
    status = _combined_status(tuple(row.status for row in rows))
    return ResearchTeamRoutingAuditComponent(
        component_code="team_capacity",
        audited_domain_code=routed_domain_code,
        component_status=status,
        observed_status=status,
        row_count=_decimal_count(len(rows)),
        reason_codes=(f"team_capacity_{status}",),
    )


def _memory_component(
    report: ResearchTeamDomainMemorySummaryReport,
    routed_domain_code: str | None,
    route_status: str,
) -> ResearchTeamRoutingAuditComponent:
    if routed_domain_code is None:
        status = "block" if route_status == "block" else "watch"
        return ResearchTeamRoutingAuditComponent(
            component_code="domain_memory",
            audited_domain_code=None,
            component_status=status,
            observed_status=None,
            row_count=_ZERO,
            reason_codes=("domain_memory_unassigned_domain",),
        )
    row = _memory_row_for_domain(report.rows, routed_domain_code)
    if row is None:
        return ResearchTeamRoutingAuditComponent(
            component_code="domain_memory",
            audited_domain_code=routed_domain_code,
            component_status="block",
            observed_status=None,
            row_count=_ZERO,
            reason_codes=("domain_memory_missing",),
        )
    return ResearchTeamRoutingAuditComponent(
        component_code="domain_memory",
        audited_domain_code=routed_domain_code,
        component_status=row.status,
        observed_status=row.status,
        row_count=_decimal_count(1),
        reason_codes=(f"domain_memory_{row.status}",),
    )


def _domain_code_from_route(route: ResearchMarketEventTypeRoute) -> str | None:
    if route.team_queue_id is None:
        return None
    return _normalize_domain_alias("team_queue_id", route.team_queue_id)


def _playbook_for_domain(
    playbooks: tuple[ResearchTeamDomainPlaybook, ...],
    domain_code: str,
) -> ResearchTeamDomainPlaybook | None:
    for playbook in playbooks:
        if _normalize_domain_alias("domain_id", playbook.domain_id) == domain_code:
            return playbook
    return None


def _capacity_rows_for_domain(
    rows: tuple[ResearchTeamCapacityPlannerRow, ...],
    domain_code: str,
) -> tuple[ResearchTeamCapacityPlannerRow, ...]:
    return tuple(
        row
        for row in rows
        if _normalize_domain_alias("domain_code", row.domain_code) == domain_code
    )


def _memory_row_for_domain(
    rows: tuple[ResearchTeamDomainMemorySummaryRow, ...],
    domain_code: str,
) -> ResearchTeamDomainMemorySummaryRow | None:
    for row in rows:
        if _normalize_domain_alias("domain_id", row.domain_id) == domain_code:
            return row
    return None


def _combined_status(statuses: tuple[str, ...]) -> str:
    if any(status == "block" for status in statuses):
        return "block"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _report_status(
    components: tuple[ResearchTeamRoutingAuditComponent, ...],
) -> str:
    return _combined_status(tuple(component.component_status for component in components))


def _report_reason_codes(
    components: tuple[ResearchTeamRoutingAuditComponent, ...],
) -> tuple[str, ...]:
    codes: list[str] = []
    if any(component.component_status == "block" for component in components):
        codes.append("routing_audit_block_components")
    if any(component.component_status == "watch" for component in components):
        codes.append("routing_audit_watch_components")
    if not codes:
        codes.append("routing_audit_pass")
    return _normalize_report_reason_codes(tuple(codes))


def _status_count(
    components: tuple[ResearchTeamRoutingAuditComponent, ...],
    status: str,
) -> int:
    return sum(1 for component in components if component.component_status == status)


def _normalize_components(
    components: Sequence[ResearchTeamRoutingAuditComponent],
) -> tuple[ResearchTeamRoutingAuditComponent, ...]:
    if isinstance(components, (str, bytes)) or not isinstance(components, Sequence):
        raise ValueError("components must be a sequence")
    normalized: list[ResearchTeamRoutingAuditComponent] = []
    seen_codes: set[str] = set()
    for component in components:
        if type(component) is not ResearchTeamRoutingAuditComponent:
            raise ValueError("components must contain ResearchTeamRoutingAuditComponent")
        _require_hard_flags("component", component)
        if component.component_code in seen_codes:
            raise ValueError("components must not contain duplicate component_code")
        seen_codes.add(component.component_code)
        normalized.append(component)
    return tuple(
        sorted(
            normalized,
            key=lambda item: ROUTING_AUDIT_COMPONENT_CODES.index(item.component_code),
        ),
    )


def _normalize_component_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    return _normalize_reason_codes(reason_codes, _COMPONENT_REASON_CODE_SEQUENCE)


def _normalize_report_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    return _normalize_reason_codes(reason_codes, _REPORT_REASON_CODE_SEQUENCE)


def _normalize_reason_codes(
    reason_codes: Sequence[str],
    known_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in known_reason_codes:
            raise ValueError("reason_codes must contain supported values")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(code for code in known_reason_codes if code in normalized)


def _validate_component(component: ResearchTeamRoutingAuditComponent) -> None:
    expected_status_reason = f"{component.component_code}_{component.component_status}"
    missing_or_unassigned = any(
        reason_code.endswith("_missing")
        or reason_code.endswith("_unassigned_domain")
        or reason_code == "routed_domain_unassigned"
        for reason_code in component.reason_codes
    )
    if expected_status_reason not in component.reason_codes:
        if not missing_or_unassigned:
            raise ValueError("component_status must match reason_codes")
    if component.audited_domain_code is None and not missing_or_unassigned:
        raise ValueError("unassigned components must explain the missing routed domain")
    if component.row_count == _ZERO and component.observed_status is not None:
        raise ValueError("observed_status must be None when row_count is zero")


def _validate_report(report: ResearchTeamRoutingAuditReport) -> None:
    components = report.components
    if report.audited_component_count != _decimal_count(len(components)):
        raise ValueError("audited_component_count must match components")
    if report.pass_count != _decimal_count(_status_count(components, "pass")):
        raise ValueError("pass_count must match components")
    if report.watch_count != _decimal_count(_status_count(components, "watch")):
        raise ValueError("watch_count must match components")
    if report.block_count != _decimal_count(_status_count(components, "block")):
        raise ValueError("block_count must match components")
    expected_status = _report_status(components)
    if report.audit_status != expected_status:
        raise ValueError("audit_status must match components")
    expected_reasons = _report_reason_codes(components)
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match components")
    for component in components:
        if component.audited_domain_code != report.routed_domain_code:
            raise ValueError("component audited_domain_code must match routed_domain_code")


def _normalize_domain_alias(field_name: str, value: object) -> str:
    identifier = _require_public_identifier(field_name, value)
    if identifier not in _QUEUE_TO_DOMAIN:
        raise ValueError(f"{field_name} must be a supported research domain")
    return _QUEUE_TO_DOMAIN[identifier]


def _normalize_optional_domain_code(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    return _normalize_domain_alias(field_name, value)


def _require_component_code(field_name: str, value: object) -> str:
    identifier = _require_public_identifier(field_name, value)
    if identifier not in ROUTING_AUDIT_COMPONENT_CODES:
        raise ValueError(f"{field_name} must be a supported audit component")
    return identifier


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in ROUTING_AUDIT_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _normalize_optional_status(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    return _require_status(field_name, value)


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str or not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_text(field_name, value)
    return value


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be public text")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")
    _reject_unsafe_public_text(field_name, value)
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent < -6:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return value.quantize(_QUANT)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.quantize(_COUNT_QUANT):
        raise ValueError(f"{field_name} must be a whole number")
    return normalized


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(_QUANT)


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if value is None:
        return None
    if type(value) is bool:
        return value
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value.quantize(_QUANT))
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal-derived strings")
    if type(value) is str:
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_key(key):
                raise ValueError(f"unsafe public field in payload: {key}")
            ready[key] = _json_ready(item)
        return ready
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        _reject_unsafe_public_text(path or label, value)
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or label} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            if _has_unsafe_public_key(key):
                raise ValueError(f"unsafe public field in {label}: {key}")
            if key in _FLAG_FIELDS and item is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    raise ValueError("value is not JSON serializable")


def _reject_external_unsafe_public_surface(
    label: str,
    value: object,
    path: str = "",
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_external_unsafe_public_surface(label, asdict(value), path)
        return
    if type(value) is str:
        _reject_unsafe_public_text(path or label, value)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            if _has_unsafe_public_key(key):
                raise ValueError(f"unsafe public field in {label}: {key}")
            if key in _FLAG_FIELDS and item is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_external_unsafe_public_surface(label, item, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_external_unsafe_public_surface(label, item, nested_path)


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    normalized = value.casefold()
    if any(pattern.search(normalized) for pattern in _UNSAFE_PUBLIC_VALUE_PATTERNS):
        raise ValueError(f"{field_name} has unsafe public value")


def _has_unsafe_public_key(value: str) -> bool:
    normalized = value.casefold()
    return any(fragment in normalized for fragment in _UNSAFE_PUBLIC_KEY_FRAGMENTS)


def _report_values_without_digest(
    report: ResearchTeamRoutingAuditReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _digest_public_value(value: object) -> str:
    ready = _json_ready(value)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest)
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    expected_digest = _digest_public_value(unsigned)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest must match payload fields")


__all__ = (
    "DEFAULT_RESEARCH_TEAM_ROUTING_AUDIT_CONFIG_VERSION",
    "ROUTING_AUDIT_COMPONENT_CODES",
    "ROUTING_AUDIT_STATUSES",
    "ResearchTeamRoutingAuditComponent",
    "ResearchTeamRoutingAuditConfig",
    "ResearchTeamRoutingAuditReport",
    "build_research_team_routing_audit_report",
    "research_team_routing_audit_report_payload",
)
