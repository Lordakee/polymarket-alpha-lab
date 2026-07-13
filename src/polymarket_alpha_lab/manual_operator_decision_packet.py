"""Pure manual-operator decision support packet reducer.

The packet produced here is report-only checklist material for human review.
It only summarizes redacted review support for a human checklist.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Iterable, Mapping

from .team_paper_guard import require_paper_only_flags


DEFAULT_MANUAL_OPERATOR_DECISION_PACKET_CONFIG_VERSION = (
    "manual-operator-decision-packet-v0"
)

CHECKLIST_AREAS = (
    "research",
    "evidence",
    "source_authority",
    "microstructure",
    "cost",
    "timing",
    "team_memory",
)
SUPPORT_STATUSES = ("pass", "watch", "block")
NEXT_MANUAL_REVIEW_ACTIONS = (
    "manual_review_read_packet",
    "manual_review_complete_checklist",
    "manual_review_resolve_blockers",
)
GO_NO_GO_STATUSES = ("go", "no_go")
GO_NO_GO_REVIEW_STATUSES = ("pass", "watch", "block")
GO_NO_GO_SOURCE_NAMES = (
    "manual_decision_packet",
    "ready_queue_rollup",
    "audit_trail",
    "public_output_safety",
)
MANUAL_OPERATOR_DECISION_PAYLOAD_FIELDS = (
    "generated_at",
    "config_version",
    "research_status",
    "evidence_status",
    "source_authority_status",
    "microstructure_status",
    "cost_status",
    "timing_status",
    "team_memory_status",
    "reason_summaries",
    "unresolved_blockers",
    "next_manual_review_action",
    "paper_only",
    "report_only",
    "readonly",
)
REASON_SUMMARY_PAYLOAD_FIELDS = (
    "checklist_area",
    "support_status",
    "reason_summary",
)
SOURCE_PAYLOAD_DIGEST_FIELDS = ("source_name", "payload_digest")
GO_NO_GO_PAYLOAD_FIELDS = (
    "generated_at",
    "config_version",
    "go_no_go_status",
    "manual_next_step",
    "reason_codes",
    "manual_packet_review_status",
    "ready_queue_review_status",
    "audit_trail_review_status",
    "public_output_safety_review_status",
    "source_payload_digests",
    "manual_packet_payload_digest",
    "ready_queue_payload_digest",
    "audit_trail_payload_digest",
    "public_output_payload_digest",
    "paper_only",
    "report_only",
    "readonly",
    "payload_digest",
)
GO_NO_GO_READY_REASON = "manual_operator_go_no_go_ready"
GO_NO_GO_MANUAL_PACKET_REASON = (
    "manual_operator_go_no_go_manual_packet_not_ready"
)
GO_NO_GO_READY_QUEUE_REASON = "manual_operator_go_no_go_ready_queue_not_ready"
GO_NO_GO_AUDIT_TRAIL_REASON = "manual_operator_go_no_go_audit_trail_not_ready"
GO_NO_GO_PUBLIC_OUTPUT_REASON = "manual_operator_go_no_go_public_output_not_safe"
GO_NO_GO_REASON_CODES = (
    GO_NO_GO_READY_REASON,
    GO_NO_GO_MANUAL_PACKET_REASON,
    GO_NO_GO_READY_QUEUE_REASON,
    GO_NO_GO_AUDIT_TRAIL_REASON,
    GO_NO_GO_PUBLIC_OUTPUT_REASON,
)
GO_NO_GO_NEXT_STEPS = (
    "manual_review_read_packet",
    "manual_review_complete_checklist",
    "manual_review_resolve_blockers",
    "manual_review_resolve_ready_queue",
    "manual_review_resolve_audit_trail",
    "manual_review_resolve_public_output_safety",
)

_STATUS_FIELD_BY_AREA = {
    "research": "research_status",
    "evidence": "evidence_status",
    "source_authority": "source_authority_status",
    "microstructure": "microstructure_status",
    "cost": "cost_status",
    "timing": "timing_status",
    "team_memory": "team_memory_status",
}
_STATUS_RANK = {
    "pass": 0,
    "watch": 1,
    "block": 2,
}
_NO_REDACTED_FACT_SUMMARY = "no redacted support fact provided"
_UNSAFE_TEXT_TOKENS = frozenset(
    (
        "account",
        "accounts",
        "auth",
        "authentication",
        "authorize",
        "authorized",
        "authorizing",
        "buying",
        "buys",
        "cancel",
        "cancelled",
        "canceling",
        "cancelling",
        "cancels",
        "credential",
        "credentials",
        "execute",
        "executed",
        "executing",
        "execution",
        "executes",
        "api",
        "bearer",
        "blocked",
        "database",
        "dsn",
        "dsns",
        "key",
        "keys",
        "mnemonic",
        "order",
        "ordered",
        "ordering",
        "orders",
        "password",
        "passwords",
        "postgres",
        "private",
        "privkey",
        "question",
        "questions",
        "recommend",
        "recommended",
        "recommending",
        "recommendation",
        "recommendations",
        "recommends",
        "replace",
        "replaced",
        "replacing",
        "replaces",
        "secret",
        "secrets",
        "seed",
        "sizing",
        "sign",
        "signed",
        "signing",
        "sold",
        "submit",
        "submitted",
        "submitting",
        "submits",
        "table",
        "tables",
        "token",
        "tokens",
        "trade",
        "traded",
        "trading",
        "wallet",
        "wallets",
        "buy",
        "sell",
        "selling",
        "sells",
        "position",
        "positions",
    ),
)
_UNSAFE_TEXT_PHRASES = frozenset(
    (
        "candidate id",
        "candidate digest",
        "candidate reference",
        "private key",
        "seed phrase",
        "position size",
        "market id",
        "market link",
        "market reference",
        "market record",
        "market slug",
        "market url",
        "exchange mutation",
        "raw archive",
        "raw candidate",
        "raw market",
        "raw source",
        "source archive",
        "source digest",
        "source id",
        "source link",
        "source path",
        "source ref",
        "source refs",
        "source record",
        "source reference",
        "source text",
        "source url",
    ),
)
_UNSAFE_TEXT_REFERENCE_RE = re.compile(
    r"(?i)(?:\b[a-z0-9-]+\.[a-z]{2,}\b|(?:^|\s)[~/]?[\w.-]+/[\w./-]+)",
)
_UNSAFE_TEXT_HASH_RE = re.compile(r"(?i)\b(?:0x)?[0-9a-f]{16,}\b")


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ManualOperatorDecisionPacketConfig(_FinalDataclass):
    config_version: str = DEFAULT_MANUAL_OPERATOR_DECISION_PACKET_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ManualOperatorDecisionPacketConfig,
        )
        _require_public_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MANUAL_OPERATOR_DECISION_PACKET_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the known config version")
        require_paper_only_flags("manual operator decision packet config", self)


@dataclass(frozen=True)
class ManualOperatorDecisionFact(_FinalDataclass):
    checklist_area: str
    support_status: str
    reason_summary: str
    blocker_summary: str | None = None
    support_weight: Decimal = Decimal("1")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("fact", self, ManualOperatorDecisionFact)
        _require_member("checklist_area", self.checklist_area, CHECKLIST_AREAS)
        _require_member("support_status", self.support_status, SUPPORT_STATUSES)
        _require_public_text("reason_summary", self.reason_summary)
        if self.blocker_summary is not None:
            _require_public_text("blocker_summary", self.blocker_summary)
        if self.support_status == "block" and self.blocker_summary is None:
            raise ValueError(
                "blocker_summary is required when support_status is block",
            )
        if self.support_status != "block" and self.blocker_summary is not None:
            raise ValueError(
                "blocker_summary is only allowed when support_status is block",
            )
        object.__setattr__(
            self,
            "support_weight",
            _require_nonnegative_decimal("support_weight", self.support_weight),
        )
        require_paper_only_flags("manual operator decision fact", self)


@dataclass(frozen=True)
class ManualOperatorDecisionReasonSummary(_FinalDataclass):
    checklist_area: str
    support_status: str
    reason_summary: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "reason summary",
            self,
            ManualOperatorDecisionReasonSummary,
        )
        _require_member("checklist_area", self.checklist_area, CHECKLIST_AREAS)
        _require_member("support_status", self.support_status, SUPPORT_STATUSES)
        _require_public_text("reason_summary", self.reason_summary)
        require_paper_only_flags("manual operator decision reason summary", self)


@dataclass(frozen=True)
class ManualOperatorDecisionPacket(_FinalDataclass):
    generated_at: datetime
    config_version: str
    research_status: str
    evidence_status: str
    source_authority_status: str
    microstructure_status: str
    cost_status: str
    timing_status: str
    team_memory_status: str
    reason_summaries: tuple[ManualOperatorDecisionReasonSummary, ...]
    unresolved_blockers: tuple[str, ...]
    next_manual_review_action: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("packet", self, ManualOperatorDecisionPacket)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MANUAL_OPERATOR_DECISION_PACKET_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the known config version")
        for field_name in _STATUS_FIELD_BY_AREA.values():
            _require_member(field_name, getattr(self, field_name), SUPPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_summaries",
            _normalize_reason_summaries(self.reason_summaries),
        )
        object.__setattr__(
            self,
            "unresolved_blockers",
            _normalize_public_text_tuple(
                "unresolved_blockers",
                self.unresolved_blockers,
            ),
        )
        _require_member(
            "next_manual_review_action",
            self.next_manual_review_action,
            NEXT_MANUAL_REVIEW_ACTIONS,
        )
        require_paper_only_flags("manual operator decision packet", self)
        _validate_packet_consistency(self)

    @property
    def payload(self) -> "FrozenJsonObject":
        return manual_operator_decision_packet_payload(self)


@dataclass(frozen=True)
class ManualOperatorGoNoGoPacket(_FinalDataclass):
    generated_at: datetime
    go_no_go_status: str
    manual_next_step: str
    reason_codes: tuple[str, ...]
    manual_packet_review_status: str
    ready_queue_review_status: str
    audit_trail_review_status: str
    public_output_safety_review_status: str
    source_payload_digests: tuple[Mapping[str, object], ...]
    manual_packet_payload_digest: str
    ready_queue_payload_digest: str
    audit_trail_payload_digest: str
    public_output_payload_digest: str
    payload_digest: str
    config_version: str = DEFAULT_MANUAL_OPERATOR_DECISION_PACKET_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("go/no-go packet", self, ManualOperatorGoNoGoPacket)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        if self.config_version != DEFAULT_MANUAL_OPERATOR_DECISION_PACKET_CONFIG_VERSION:
            raise ValueError("config_version must be the known config version")
        _require_member("go_no_go_status", self.go_no_go_status, GO_NO_GO_STATUSES)
        _require_member("manual_next_step", self.manual_next_step, GO_NO_GO_NEXT_STEPS)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_go_no_go_reason_codes(self.reason_codes),
        )
        for field_name in (
            "manual_packet_review_status",
            "ready_queue_review_status",
            "audit_trail_review_status",
            "public_output_safety_review_status",
        ):
            _require_member(field_name, getattr(self, field_name), GO_NO_GO_REVIEW_STATUSES)
        object.__setattr__(
            self,
            "source_payload_digests",
            _normalize_source_payload_digests(self.source_payload_digests),
        )
        for field_name in (
            "manual_packet_payload_digest",
            "ready_queue_payload_digest",
            "audit_trail_payload_digest",
            "public_output_payload_digest",
            "payload_digest",
        ):
            _require_payload_digest(field_name, getattr(self, field_name))
        require_paper_only_flags("manual operator go/no-go packet", self)
        _validate_go_no_go_packet_consistency(self)

    @property
    def payload(self) -> "FrozenJsonObject":
        return manual_operator_go_no_go_packet_payload(self)


def build_manual_operator_decision_packet(
    facts: Iterable[ManualOperatorDecisionFact],
    *,
    generated_at: datetime,
    config: ManualOperatorDecisionPacketConfig | None = None,
) -> ManualOperatorDecisionPacket:
    if config is None:
        config = ManualOperatorDecisionPacketConfig()
    if type(config) is not ManualOperatorDecisionPacketConfig:
        raise ValueError("config must be exactly ManualOperatorDecisionPacketConfig")
    _validate_config_object(config)
    fact_items = _normalize_facts(facts)
    grouped_facts = {area: [] for area in CHECKLIST_AREAS}
    for fact in fact_items:
        grouped_facts[fact.checklist_area].append(fact)

    area_statuses: dict[str, str] = {}
    reason_summaries: list[ManualOperatorDecisionReasonSummary] = []
    unresolved_blockers: list[str] = []
    for area in CHECKLIST_AREAS:
        area_facts = tuple(grouped_facts[area])
        if not area_facts:
            area_statuses[area] = "block"
            reason_summary = _NO_REDACTED_FACT_SUMMARY
            unresolved_blockers.append(f"{area}: {_NO_REDACTED_FACT_SUMMARY}")
        else:
            area_statuses[area] = _reduced_status(area_facts)
            reason_summary = "; ".join(
                _unique_text(fact.reason_summary for fact in area_facts),
            )
            for fact in area_facts:
                if fact.support_status == "block":
                    if fact.blocker_summary is None:
                        raise ValueError(
                            "blocker_summary is required when support_status is block",
                        )
                    unresolved_blockers.append(f"{area}: {fact.blocker_summary}")
        reason_summaries.append(
            ManualOperatorDecisionReasonSummary(
                checklist_area=area,
                support_status=area_statuses[area],
                reason_summary=reason_summary,
            ),
        )

    blocker_tuple = tuple(_unique_text(unresolved_blockers))
    return ManualOperatorDecisionPacket(
        generated_at=generated_at,
        config_version=config.config_version,
        research_status=area_statuses["research"],
        evidence_status=area_statuses["evidence"],
        source_authority_status=area_statuses["source_authority"],
        microstructure_status=area_statuses["microstructure"],
        cost_status=area_statuses["cost"],
        timing_status=area_statuses["timing"],
        team_memory_status=area_statuses["team_memory"],
        reason_summaries=tuple(reason_summaries),
        unresolved_blockers=blocker_tuple,
        next_manual_review_action=_next_manual_review_action(
            area_statuses.values(),
            blocker_tuple,
        ),
        paper_only=config.paper_only,
        report_only=config.report_only,
        readonly=config.readonly,
    )


def build_manual_operator_go_no_go_packet(
    *,
    manual_packet: ManualOperatorDecisionPacket,
    ready_queue_status: str,
    ready_queue_payload_digest: str,
    audit_trail_status: str,
    audit_trail_payload_digest: str,
    public_output_safe_for_operator_display: bool,
    public_output_payload_digest: str,
) -> ManualOperatorGoNoGoPacket:
    if type(manual_packet) is not ManualOperatorDecisionPacket:
        raise ValueError("manual_packet must be exactly ManualOperatorDecisionPacket")
    _validate_decision_packet_object(manual_packet)
    _require_member("ready_queue_status", ready_queue_status, ("ready", "watch", "blocked"))
    _require_member("audit_trail_status", audit_trail_status, ("pass", "watch", "blocked"))
    if type(public_output_safe_for_operator_display) is not bool:
        raise ValueError("public_output_safe_for_operator_display must be a bool")
    for field_name, digest in (
        ("ready_queue_payload_digest", ready_queue_payload_digest),
        ("audit_trail_payload_digest", audit_trail_payload_digest),
        ("public_output_payload_digest", public_output_payload_digest),
    ):
        _require_payload_digest(field_name, digest)

    manual_packet_payload_digest = manual_operator_decision_packet_payload_digest(
        manual_packet,
    )
    manual_packet_review_status = _manual_packet_review_status(manual_packet)
    ready_queue_review_status = _ready_queue_review_status(ready_queue_status)
    audit_trail_review_status = _audit_trail_review_status(audit_trail_status)
    public_output_safety_review_status = (
        "pass" if public_output_safe_for_operator_display else "block"
    )
    review_statuses = (
        manual_packet_review_status,
        ready_queue_review_status,
        audit_trail_review_status,
        public_output_safety_review_status,
    )
    reason_codes = _go_no_go_reason_codes(
        manual_packet_review_status=manual_packet_review_status,
        ready_queue_review_status=ready_queue_review_status,
        audit_trail_review_status=audit_trail_review_status,
        public_output_safety_review_status=public_output_safety_review_status,
    )
    values: dict[str, object] = {
        "generated_at": manual_packet.generated_at,
        "config_version": manual_packet.config_version,
        "go_no_go_status": "go" if all(status == "pass" for status in review_statuses) else "no_go",
        "manual_next_step": _go_no_go_next_step(
            manual_packet=manual_packet,
            manual_packet_review_status=manual_packet_review_status,
            ready_queue_review_status=ready_queue_review_status,
            audit_trail_review_status=audit_trail_review_status,
            public_output_safety_review_status=public_output_safety_review_status,
        ),
        "reason_codes": reason_codes,
        "manual_packet_review_status": manual_packet_review_status,
        "ready_queue_review_status": ready_queue_review_status,
        "audit_trail_review_status": audit_trail_review_status,
        "public_output_safety_review_status": public_output_safety_review_status,
        "source_payload_digests": _source_payload_digest_entries(
            manual_packet_payload_digest=manual_packet_payload_digest,
            ready_queue_payload_digest=ready_queue_payload_digest,
            audit_trail_payload_digest=audit_trail_payload_digest,
            public_output_payload_digest=public_output_payload_digest,
        ),
        "manual_packet_payload_digest": manual_packet_payload_digest,
        "ready_queue_payload_digest": ready_queue_payload_digest,
        "audit_trail_payload_digest": audit_trail_payload_digest,
        "public_output_payload_digest": public_output_payload_digest,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ManualOperatorGoNoGoPacket(
        **values,
        payload_digest=_go_no_go_payload_digest_from_values(values, payload_digest=""),
    )


def manual_operator_decision_packet_payload(
    packet: ManualOperatorDecisionPacket,
) -> "FrozenJsonObject":
    return _freeze_json_object(_materialize_decision_packet_payload(packet))


def manual_operator_decision_packet_payload_digest(
    packet: ManualOperatorDecisionPacket | Mapping[str, object],
) -> str:
    if type(packet) is ManualOperatorDecisionPacket:
        payload = _materialize_decision_packet_payload(packet)
    elif isinstance(packet, Mapping):
        payload = _materialize_decision_public_payload(packet)
    else:
        raise ValueError("packet must be a ManualOperatorDecisionPacket or public payload")
    return hashlib.sha256(
        json.dumps(
            _json_ready_public_payload(payload),
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode(),
    ).hexdigest()


def manual_operator_go_no_go_packet_payload(
    packet: ManualOperatorGoNoGoPacket | Mapping[str, object],
) -> "FrozenJsonObject":
    if type(packet) is ManualOperatorGoNoGoPacket:
        payload = _materialize_go_no_go_packet_payload(packet)
    elif isinstance(packet, Mapping):
        payload = _materialize_go_no_go_public_payload(packet)
    else:
        raise ValueError("packet must be a ManualOperatorGoNoGoPacket or public payload")
    return _freeze_json_object(payload)


def manual_operator_go_no_go_packet_payload_digest(
    packet: ManualOperatorGoNoGoPacket | Mapping[str, object],
) -> str:
    if type(packet) is ManualOperatorGoNoGoPacket:
        return _materialize_go_no_go_packet_payload(packet)["payload_digest"]
    if isinstance(packet, Mapping):
        return _materialize_go_no_go_public_payload(packet)["payload_digest"]
    raise ValueError("packet must be a ManualOperatorGoNoGoPacket or public payload")


class FrozenJsonObject(dict[str, Any]):
    __slots__ = ("__sealed",)

    def __init__(self, value: dict[str, Any]) -> None:
        if getattr(self, "_FrozenJsonObject__sealed", False):
            raise TypeError("payload is immutable")
        super().__init__(value)
        self.__sealed = True

    def __setitem__(self, key: str, value: Any) -> None:
        raise TypeError("payload is immutable")

    def __delitem__(self, key: str) -> None:
        raise TypeError("payload is immutable")

    def clear(self) -> None:
        raise TypeError("payload is immutable")

    def pop(self, key: str, default: Any = None) -> Any:
        raise TypeError("payload is immutable")

    def popitem(self) -> tuple[str, Any]:
        raise TypeError("payload is immutable")

    def setdefault(self, key: str, default: Any = None) -> Any:
        raise TypeError("payload is immutable")

    def update(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("payload is immutable")

    def __ior__(self, other: object) -> "FrozenJsonObject":
        raise TypeError("payload is immutable")


class FrozenJsonArray(tuple[Any, ...]):
    def __eq__(self, other: object) -> bool:
        if isinstance(other, (list, tuple)):
            return tuple(self) == tuple(other)
        return False

    def append(self, value: Any) -> None:
        raise TypeError("payload is immutable")

    def extend(self, values: Any) -> None:
        raise TypeError("payload is immutable")


def _validate_config_object(config: ManualOperatorDecisionPacketConfig) -> None:
    _require_exact_type("config", config, ManualOperatorDecisionPacketConfig)
    _require_public_text("config_version", config.config_version)
    if config.config_version != DEFAULT_MANUAL_OPERATOR_DECISION_PACKET_CONFIG_VERSION:
        raise ValueError("config_version must be the known config version")
    require_paper_only_flags("manual operator decision packet config", config)


def _validate_fact_object(fact: ManualOperatorDecisionFact) -> None:
    _require_exact_type("fact", fact, ManualOperatorDecisionFact)
    _require_member("checklist_area", fact.checklist_area, CHECKLIST_AREAS)
    _require_member("support_status", fact.support_status, SUPPORT_STATUSES)
    _require_public_text("reason_summary", fact.reason_summary)
    if fact.blocker_summary is not None:
        _require_public_text("blocker_summary", fact.blocker_summary)
    if fact.support_status == "block" and fact.blocker_summary is None:
        raise ValueError("blocker_summary is required when support_status is block")
    if fact.support_status != "block" and fact.blocker_summary is not None:
        raise ValueError("blocker_summary is only allowed when support_status is block")
    _require_nonnegative_decimal("support_weight", fact.support_weight)
    require_paper_only_flags("manual operator decision fact", fact)


def _validate_reason_summary_object(
    summary: ManualOperatorDecisionReasonSummary,
) -> None:
    _require_exact_type(
        "reason summary",
        summary,
        ManualOperatorDecisionReasonSummary,
    )
    _require_member("checklist_area", summary.checklist_area, CHECKLIST_AREAS)
    _require_member("support_status", summary.support_status, SUPPORT_STATUSES)
    _require_public_text("reason_summary", summary.reason_summary)
    require_paper_only_flags("manual operator decision reason summary", summary)


def _validate_decision_packet_object(packet: ManualOperatorDecisionPacket) -> None:
    _require_exact_type("packet", packet, ManualOperatorDecisionPacket)
    _require_stored_utc_datetime("generated_at", packet.generated_at)
    _require_public_text("config_version", packet.config_version)
    if packet.config_version != DEFAULT_MANUAL_OPERATOR_DECISION_PACKET_CONFIG_VERSION:
        raise ValueError("config_version must be the known config version")
    for field_name in _STATUS_FIELD_BY_AREA.values():
        _require_member(field_name, getattr(packet, field_name), SUPPORT_STATUSES)
    if type(packet.reason_summaries) is not tuple:
        raise ValueError("reason_summaries must be exactly tuple")
    for summary in packet.reason_summaries:
        _validate_reason_summary_object(summary)
    if type(packet.unresolved_blockers) is not tuple:
        raise ValueError("unresolved_blockers must be exactly tuple")
    for blocker in packet.unresolved_blockers:
        _require_public_text("unresolved_blockers", blocker)
    _require_member(
        "next_manual_review_action",
        packet.next_manual_review_action,
        NEXT_MANUAL_REVIEW_ACTIONS,
    )
    require_paper_only_flags("manual operator decision packet", packet)
    _validate_packet_consistency(packet)


def _decision_payload_items(
    packet: ManualOperatorDecisionPacket,
) -> dict[str, object]:
    return {
        "generated_at": packet.generated_at.isoformat(),
        "config_version": packet.config_version,
        "research_status": packet.research_status,
        "evidence_status": packet.evidence_status,
        "source_authority_status": packet.source_authority_status,
        "microstructure_status": packet.microstructure_status,
        "cost_status": packet.cost_status,
        "timing_status": packet.timing_status,
        "team_memory_status": packet.team_memory_status,
        "reason_summaries": tuple(
            {
                "checklist_area": summary.checklist_area,
                "support_status": summary.support_status,
                "reason_summary": summary.reason_summary,
            }
            for summary in packet.reason_summaries
        ),
        "unresolved_blockers": packet.unresolved_blockers,
        "next_manual_review_action": packet.next_manual_review_action,
        "paper_only": packet.paper_only,
        "report_only": packet.report_only,
        "readonly": packet.readonly,
    }


def _materialize_decision_packet_payload(
    packet: ManualOperatorDecisionPacket,
) -> dict[str, object]:
    _validate_decision_packet_object(packet)
    payload = _decision_payload_items(packet)
    _validate_json_ready_public_payload(payload)
    return payload


def _materialize_decision_public_payload(
    payload: Mapping[str, object],
) -> dict[str, object]:
    _require_public_mapping_schema(
        "manual operator decision packet",
        payload,
        MANUAL_OPERATOR_DECISION_PAYLOAD_FIELDS,
    )
    generated_at = _parse_canonical_utc_timestamp("generated_at", payload["generated_at"])
    summaries: list[ManualOperatorDecisionReasonSummary] = []
    for item in _require_public_json_array("reason_summaries", payload["reason_summaries"]):
        _require_public_mapping_schema(
            "reason_summaries entry",
            item,
            REASON_SUMMARY_PAYLOAD_FIELDS,
        )
        summaries.append(
            ManualOperatorDecisionReasonSummary(
                checklist_area=item["checklist_area"],
                support_status=item["support_status"],
                reason_summary=item["reason_summary"],
            ),
        )
    blockers = _require_public_json_array(
        "unresolved_blockers",
        payload["unresolved_blockers"],
    )
    for blocker in blockers:
        _require_public_text("unresolved_blockers", blocker)
    _require_bool_flag("paper_only", payload["paper_only"])
    _require_bool_flag("report_only", payload["report_only"])
    _require_bool_flag("readonly", payload["readonly"])
    reconstructed = ManualOperatorDecisionPacket(
        generated_at=generated_at,
        config_version=payload["config_version"],
        research_status=payload["research_status"],
        evidence_status=payload["evidence_status"],
        source_authority_status=payload["source_authority_status"],
        microstructure_status=payload["microstructure_status"],
        cost_status=payload["cost_status"],
        timing_status=payload["timing_status"],
        team_memory_status=payload["team_memory_status"],
        reason_summaries=tuple(summaries),
        unresolved_blockers=tuple(blockers),
        next_manual_review_action=payload["next_manual_review_action"],
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )
    return _materialize_decision_packet_payload(reconstructed)


def _normalize_facts(
    facts: Iterable[ManualOperatorDecisionFact],
) -> tuple[ManualOperatorDecisionFact, ...]:
    if isinstance(facts, (str, bytes)):
        raise ValueError("facts must be an iterable of ManualOperatorDecisionFact values")
    try:
        fact_items = tuple(facts)
    except TypeError as exc:
        raise ValueError(
            "facts must be an iterable of ManualOperatorDecisionFact values",
        ) from exc
    for fact in fact_items:
        if type(fact) is not ManualOperatorDecisionFact:
            raise ValueError("facts must contain ManualOperatorDecisionFact values")
        _validate_fact_object(fact)
    return fact_items


def _normalize_reason_summaries(
    summaries: object,
) -> tuple[ManualOperatorDecisionReasonSummary, ...]:
    if isinstance(summaries, (str, bytes)):
        raise ValueError(
            "reason_summaries must be ManualOperatorDecisionReasonSummary values",
        )
    try:
        items = tuple(summaries)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(
            "reason_summaries must be ManualOperatorDecisionReasonSummary values",
        ) from exc
    for item in items:
        if type(item) is not ManualOperatorDecisionReasonSummary:
            raise ValueError(
                "reason_summaries must contain ManualOperatorDecisionReasonSummary values",
            )
        require_paper_only_flags("manual operator decision reason summary", item)
    return items


def _normalize_public_text_tuple(field_name: str, values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be a tuple of strings")
    try:
        items = tuple(values)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be a tuple of strings") from exc
    for item in items:
        _require_public_text(field_name, item)
    return items


def _reduced_status(facts: tuple[ManualOperatorDecisionFact, ...]) -> str:
    return max((fact.support_status for fact in facts), key=_STATUS_RANK.__getitem__)


def _next_manual_review_action(
    statuses: Iterable[str],
    unresolved_blockers: tuple[str, ...],
) -> str:
    status_tuple = tuple(statuses)
    if unresolved_blockers:
        return "manual_review_resolve_blockers"
    if any(status == "block" for status in status_tuple):
        return "manual_review_resolve_blockers"
    if any(status == "watch" for status in status_tuple):
        return "manual_review_complete_checklist"
    return "manual_review_read_packet"


def _validate_packet_consistency(packet: ManualOperatorDecisionPacket) -> None:
    summary_areas = tuple(
        summary.checklist_area for summary in packet.reason_summaries
    )
    if summary_areas != CHECKLIST_AREAS:
        raise ValueError("reason_summaries must cover each checklist area in order")
    summaries_by_area = {
        summary.checklist_area: summary for summary in packet.reason_summaries
    }
    for area, field_name in _STATUS_FIELD_BY_AREA.items():
        if summaries_by_area[area].support_status != getattr(packet, field_name):
            raise ValueError(f"{field_name} must match reason_summaries")
    if packet.unresolved_blockers and (
        packet.next_manual_review_action != "manual_review_resolve_blockers"
    ):
        raise ValueError("next_manual_review_action must resolve blockers")
    if not packet.unresolved_blockers and "block" in (
        packet.research_status,
        packet.evidence_status,
        packet.source_authority_status,
        packet.microstructure_status,
        packet.cost_status,
        packet.timing_status,
        packet.team_memory_status,
    ):
        raise ValueError("block statuses require unresolved_blockers")
    expected_action = _next_manual_review_action(
        (
            packet.research_status,
            packet.evidence_status,
            packet.source_authority_status,
            packet.microstructure_status,
            packet.cost_status,
            packet.timing_status,
            packet.team_memory_status,
        ),
        packet.unresolved_blockers,
    )
    if packet.next_manual_review_action != expected_action:
        raise ValueError("next_manual_review_action must match packet state")


def _validate_json_ready_public_payload(value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            _require_public_text("payload key", key)
            _validate_json_ready_public_payload(item)
        return
    if type(value) is tuple:
        for item in value:
            _validate_json_ready_public_payload(item)
        return
    if type(value) is str:
        _require_public_text("payload value", value)
        return
    if value is None or type(value) is bool:
        return
    raise ValueError("manual operator decision packet payload is not JSON-ready")


def _validate_go_no_go_packet_object(packet: ManualOperatorGoNoGoPacket) -> None:
    _require_exact_type("go/no-go packet", packet, ManualOperatorGoNoGoPacket)
    _require_stored_utc_datetime("generated_at", packet.generated_at)
    _require_public_text("config_version", packet.config_version)
    if packet.config_version != DEFAULT_MANUAL_OPERATOR_DECISION_PACKET_CONFIG_VERSION:
        raise ValueError("config_version must be the known config version")
    _require_member("go_no_go_status", packet.go_no_go_status, GO_NO_GO_STATUSES)
    _require_member("manual_next_step", packet.manual_next_step, GO_NO_GO_NEXT_STEPS)
    if type(packet.reason_codes) is not tuple:
        raise ValueError("reason_codes must be exactly tuple")
    _normalize_go_no_go_reason_codes(packet.reason_codes)
    for field_name in (
        "manual_packet_review_status",
        "ready_queue_review_status",
        "audit_trail_review_status",
        "public_output_safety_review_status",
    ):
        _require_member(field_name, getattr(packet, field_name), GO_NO_GO_REVIEW_STATUSES)
    if type(packet.source_payload_digests) is not tuple:
        raise ValueError("source_payload_digests must be exactly tuple")
    for entry in packet.source_payload_digests:
        if type(entry) is not dict:
            raise ValueError("source_payload_digests must contain exact dict values")
        if tuple(entry) != SOURCE_PAYLOAD_DIGEST_FIELDS:
            raise ValueError("source_payload_digests entries must use the public schema")
    _normalize_source_payload_digests(packet.source_payload_digests)
    for field_name in (
        "manual_packet_payload_digest",
        "ready_queue_payload_digest",
        "audit_trail_payload_digest",
        "public_output_payload_digest",
        "payload_digest",
    ):
        _require_payload_digest(field_name, getattr(packet, field_name))
    require_paper_only_flags("manual operator go/no-go packet", packet)
    _validate_go_no_go_packet_consistency(packet)


def _validate_go_no_go_packet_consistency(packet: ManualOperatorGoNoGoPacket) -> None:
    expected_entries = _source_payload_digest_entries(
        manual_packet_payload_digest=packet.manual_packet_payload_digest,
        ready_queue_payload_digest=packet.ready_queue_payload_digest,
        audit_trail_payload_digest=packet.audit_trail_payload_digest,
        public_output_payload_digest=packet.public_output_payload_digest,
    )
    if packet.source_payload_digests != expected_entries:
        raise ValueError("source_payload_digests must match source digest fields")
    expected_reasons = _go_no_go_reason_codes(
        manual_packet_review_status=packet.manual_packet_review_status,
        ready_queue_review_status=packet.ready_queue_review_status,
        audit_trail_review_status=packet.audit_trail_review_status,
        public_output_safety_review_status=packet.public_output_safety_review_status,
    )
    if packet.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match review statuses")
    expected_status = (
        "go"
        if all(
            status == "pass"
            for status in (
                packet.manual_packet_review_status,
                packet.ready_queue_review_status,
                packet.audit_trail_review_status,
                packet.public_output_safety_review_status,
            )
        )
        else "no_go"
    )
    if packet.go_no_go_status != expected_status:
        raise ValueError("go_no_go_status must match review statuses")
    expected_next_step = _go_no_go_next_step_from_review_statuses(
        manual_packet_review_status=packet.manual_packet_review_status,
        ready_queue_review_status=packet.ready_queue_review_status,
        audit_trail_review_status=packet.audit_trail_review_status,
        public_output_safety_review_status=packet.public_output_safety_review_status,
    )
    if packet.manual_next_step != expected_next_step:
        raise ValueError("manual_next_step must match review statuses")
    payload = _go_no_go_payload_items(packet, payload_digest=packet.payload_digest)
    if packet.payload_digest != _go_no_go_public_payload_digest(payload):
        raise ValueError("payload_digest must match public payload")


def _materialize_go_no_go_packet_payload(
    packet: ManualOperatorGoNoGoPacket,
) -> dict[str, object]:
    _validate_go_no_go_packet_object(packet)
    return _go_no_go_payload_items(packet, payload_digest=packet.payload_digest)


def _materialize_go_no_go_public_payload(
    payload: Mapping[str, object],
) -> dict[str, object]:
    _require_public_mapping_schema(
        "go/no-go payload",
        payload,
        GO_NO_GO_PAYLOAD_FIELDS,
    )
    generated_at = _parse_canonical_utc_timestamp("generated_at", payload["generated_at"])
    reason_codes = _require_public_json_array("reason_codes", payload["reason_codes"])
    source_entries: list[dict[str, object]] = []
    for entry in _require_public_json_array(
        "source_payload_digests",
        payload["source_payload_digests"],
    ):
        _require_public_mapping_schema(
            "source_payload_digests entry",
            entry,
            SOURCE_PAYLOAD_DIGEST_FIELDS,
        )
        source_entries.append(
            {
                "source_name": entry["source_name"],
                "payload_digest": entry["payload_digest"],
            },
        )
    _require_bool_flag("paper_only", payload["paper_only"])
    _require_bool_flag("report_only", payload["report_only"])
    _require_bool_flag("readonly", payload["readonly"])
    reconstructed = ManualOperatorGoNoGoPacket(
        generated_at=generated_at,
        config_version=payload["config_version"],
        go_no_go_status=payload["go_no_go_status"],
        manual_next_step=payload["manual_next_step"],
        reason_codes=tuple(reason_codes),
        manual_packet_review_status=payload["manual_packet_review_status"],
        ready_queue_review_status=payload["ready_queue_review_status"],
        audit_trail_review_status=payload["audit_trail_review_status"],
        public_output_safety_review_status=payload[
            "public_output_safety_review_status"
        ],
        source_payload_digests=tuple(source_entries),
        manual_packet_payload_digest=payload["manual_packet_payload_digest"],
        ready_queue_payload_digest=payload["ready_queue_payload_digest"],
        audit_trail_payload_digest=payload["audit_trail_payload_digest"],
        public_output_payload_digest=payload["public_output_payload_digest"],
        payload_digest=payload["payload_digest"],
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )
    return _materialize_go_no_go_packet_payload(reconstructed)


def _validate_go_no_go_public_payload(payload: Mapping[str, object]) -> None:
    _materialize_go_no_go_public_payload(payload)


def _freeze_json_object(value: dict[str, Any]) -> FrozenJsonObject:
    return FrozenJsonObject(
        {key: _freeze_json_value(item) for key, item in value.items()},
    )


def _freeze_json_value(value: Any) -> Any:
    if type(value) is dict:
        return _freeze_json_object(value)
    if type(value) is tuple or type(value) is list:
        return FrozenJsonArray(_freeze_json_value(item) for item in value)
    return value


def _unique_text(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    unique_values: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            unique_values.append(value)
    return tuple(unique_values)


def _require_public_text(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{field_name} must be canonical")
    if any(ord(character) < 32 for character in value):
        raise ValueError(f"{field_name} must not contain control characters")
    _reject_unsafe_manual_operator_packet_text(field_name, value)


def _normalize_go_no_go_reason_codes(values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not values:
        raise ValueError("reason_codes must be nonempty")
    for value in values:
        _require_member("reason_codes", value, GO_NO_GO_REASON_CODES)
    return values


def _normalize_source_payload_digests(
    values: object,
) -> tuple[dict[str, str], ...]:
    if type(values) is not tuple:
        raise ValueError("source_payload_digests must be a tuple")
    normalized: list[dict[str, str]] = []
    for value in values:
        if not isinstance(value, Mapping):
            raise ValueError("source_payload_digests must contain mappings")
        if tuple(value) != ("source_name", "payload_digest"):
            raise ValueError("source_payload_digests entries must use the public schema")
        source_name = value["source_name"]
        _require_member("source_name", source_name, GO_NO_GO_SOURCE_NAMES)
        payload_digest = _require_payload_digest(
            "payload_digest",
            value["payload_digest"],
        )
        normalized.append(
            {"source_name": source_name, "payload_digest": payload_digest},
        )
    expected_names = tuple(item["source_name"] for item in normalized)
    if expected_names != GO_NO_GO_SOURCE_NAMES:
        raise ValueError("source_payload_digests must cover each source in order")
    return tuple(normalized)


def _source_payload_digest_entries(
    *,
    manual_packet_payload_digest: object,
    ready_queue_payload_digest: object,
    audit_trail_payload_digest: object,
    public_output_payload_digest: object,
) -> tuple[dict[str, str], ...]:
    return (
        {
            "source_name": "manual_decision_packet",
            "payload_digest": _require_payload_digest(
                "manual_packet_payload_digest",
                manual_packet_payload_digest,
            ),
        },
        {
            "source_name": "ready_queue_rollup",
            "payload_digest": _require_payload_digest(
                "ready_queue_payload_digest",
                ready_queue_payload_digest,
            ),
        },
        {
            "source_name": "audit_trail",
            "payload_digest": _require_payload_digest(
                "audit_trail_payload_digest",
                audit_trail_payload_digest,
            ),
        },
        {
            "source_name": "public_output_safety",
            "payload_digest": _require_payload_digest(
                "public_output_payload_digest",
                public_output_payload_digest,
            ),
        },
    )


def _manual_packet_review_status(packet: ManualOperatorDecisionPacket) -> str:
    statuses = (
        packet.research_status,
        packet.evidence_status,
        packet.source_authority_status,
        packet.microstructure_status,
        packet.cost_status,
        packet.timing_status,
        packet.team_memory_status,
    )
    if any(status == "block" for status in statuses):
        return "block"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _ready_queue_review_status(value: str) -> str:
    if value == "ready":
        return "pass"
    if value == "watch":
        return "watch"
    return "block"


def _audit_trail_review_status(value: str) -> str:
    if value == "blocked":
        return "block"
    return value


def _go_no_go_reason_codes(
    *,
    manual_packet_review_status: object,
    ready_queue_review_status: object,
    audit_trail_review_status: object,
    public_output_safety_review_status: object,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if manual_packet_review_status != "pass":
        reasons.append(GO_NO_GO_MANUAL_PACKET_REASON)
    if ready_queue_review_status != "pass":
        reasons.append(GO_NO_GO_READY_QUEUE_REASON)
    if audit_trail_review_status != "pass":
        reasons.append(GO_NO_GO_AUDIT_TRAIL_REASON)
    if public_output_safety_review_status != "pass":
        reasons.append(GO_NO_GO_PUBLIC_OUTPUT_REASON)
    if not reasons:
        reasons.append(GO_NO_GO_READY_REASON)
    return tuple(reasons)


def _go_no_go_next_step(
    *,
    manual_packet: ManualOperatorDecisionPacket,
    manual_packet_review_status: str,
    ready_queue_review_status: str,
    audit_trail_review_status: str,
    public_output_safety_review_status: str,
) -> str:
    expected_next_step = _go_no_go_next_step_from_review_statuses(
        manual_packet_review_status=manual_packet_review_status,
        ready_queue_review_status=ready_queue_review_status,
        audit_trail_review_status=audit_trail_review_status,
        public_output_safety_review_status=public_output_safety_review_status,
    )
    if (
        manual_packet_review_status != "pass"
        and ready_queue_review_status == "pass"
        and audit_trail_review_status == "pass"
        and public_output_safety_review_status == "pass"
        and manual_packet.next_manual_review_action != expected_next_step
    ):
        raise ValueError("manual packet next step must match review status")
    return expected_next_step


def _go_no_go_next_step_from_review_statuses(
    *,
    manual_packet_review_status: object,
    ready_queue_review_status: object,
    audit_trail_review_status: object,
    public_output_safety_review_status: object,
) -> str:
    if public_output_safety_review_status != "pass":
        return "manual_review_resolve_public_output_safety"
    if ready_queue_review_status != "pass":
        return "manual_review_resolve_ready_queue"
    if audit_trail_review_status != "pass":
        return "manual_review_resolve_audit_trail"
    if manual_packet_review_status == "block":
        return "manual_review_resolve_blockers"
    if manual_packet_review_status == "watch":
        return "manual_review_complete_checklist"
    return "manual_review_read_packet"


def _go_no_go_payload_items(
    packet: ManualOperatorGoNoGoPacket,
    *,
    payload_digest: str,
) -> dict[str, object]:
    return {
        "generated_at": packet.generated_at.isoformat(),
        "config_version": packet.config_version,
        "go_no_go_status": packet.go_no_go_status,
        "manual_next_step": packet.manual_next_step,
        "reason_codes": packet.reason_codes,
        "manual_packet_review_status": packet.manual_packet_review_status,
        "ready_queue_review_status": packet.ready_queue_review_status,
        "audit_trail_review_status": packet.audit_trail_review_status,
        "public_output_safety_review_status": packet.public_output_safety_review_status,
        "source_payload_digests": packet.source_payload_digests,
        "manual_packet_payload_digest": packet.manual_packet_payload_digest,
        "ready_queue_payload_digest": packet.ready_queue_payload_digest,
        "audit_trail_payload_digest": packet.audit_trail_payload_digest,
        "public_output_payload_digest": packet.public_output_payload_digest,
        "paper_only": packet.paper_only,
        "report_only": packet.report_only,
        "readonly": packet.readonly,
        "payload_digest": payload_digest,
    }


def _go_no_go_payload_digest_from_values(
    values: Mapping[str, object],
    *,
    payload_digest: str,
) -> str:
    payload = {
        field_name: (
            payload_digest
            if field_name == "payload_digest"
            else values[field_name].isoformat()
            if field_name == "generated_at"
            and type(values[field_name]) is datetime
            else values[field_name]
        )
        for field_name in GO_NO_GO_PAYLOAD_FIELDS
    }
    return _go_no_go_public_payload_digest(payload)


def _go_no_go_public_payload_digest(payload: Mapping[str, object]) -> str:
    digest_payload = dict(payload)
    digest_payload["payload_digest"] = ""
    return hashlib.sha256(
        json.dumps(
            _json_ready_public_payload(digest_payload),
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode(),
    ).hexdigest()


def _json_ready_public_payload(value: object) -> object:
    if isinstance(value, FrozenJsonObject):
        value = dict(value)
    if isinstance(value, FrozenJsonArray):
        value = tuple(value)
    if type(value) is dict:
        return {key: _json_ready_public_payload(item) for key, item in value.items()}
    if type(value) is tuple or type(value) is list:
        return [_json_ready_public_payload(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("manual operator decision packet payload is not JSON-ready")


def _require_public_mapping_schema(
    label: str,
    value: object,
    fields: tuple[str, ...],
) -> Mapping[str, object]:
    if type(value) not in {dict, FrozenJsonObject}:
        raise ValueError(f"{label} must use the supported public schema")
    if tuple(value) != fields:
        raise ValueError(f"{label} must use the supported public schema")
    return value


def _require_public_json_array(
    field_name: str,
    value: object,
) -> tuple[object, ...]:
    if type(value) is not list and type(value) is not FrozenJsonArray:
        raise ValueError(f"{field_name} must be an exact JSON array")
    return tuple(value)


def _require_stored_utc_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime in UTC")
    if value.tzinfo is not UTC or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(f"{field_name} must be exactly UTC")
    return value


def _parse_canonical_utc_timestamp(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            f"{field_name} must be a canonical UTC timestamp",
        ) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field_name} must be a canonical UTC timestamp")
    canonical = parsed.astimezone(UTC)
    if parsed.utcoffset() != UTC.utcoffset(canonical) or canonical.isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical UTC timestamp")
    return canonical


def _require_bool_flag(field_name: str, value: object) -> None:
    if value is not True:
        raise ValueError(f"{field_name} must be True")


def _require_payload_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a payload_digest string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 payload_digest")
    return value


def _reject_unsafe_manual_operator_packet_text(field_name: str, value: str) -> None:
    tokens = _public_text_tokens(value)
    normalized = " ".join(tokens)
    if any(token in _UNSAFE_TEXT_TOKENS for token in tokens):
        raise ValueError(f"unsafe manual operator packet text in {field_name}")
    if any(phrase in normalized for phrase in _UNSAFE_TEXT_PHRASES):
        raise ValueError(f"unsafe manual operator packet text in {field_name}")
    if (
        "://" in value
        or "?" in value
        or _UNSAFE_TEXT_REFERENCE_RE.search(value)
        or _UNSAFE_TEXT_HASH_RE.search(value)
    ):
        raise ValueError(f"unsafe manual operator packet text in {field_name}")


def _public_text_tokens(value: str) -> tuple[str, ...]:
    normalized_characters = [
        character.lower() if character.isalnum() else " " for character in value
    ]
    return tuple("".join(normalized_characters).split())


def _require_member(field_name: str, value: object, choices: tuple[str, ...]) -> None:
    if type(value) is not str or value not in choices:
        raise ValueError(f"{field_name} must be one of {choices}")


def _require_exact_type(
    field_name: str,
    value: object,
    expected_type: type[object],
) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


__all__ = (
    "CHECKLIST_AREAS",
    "DEFAULT_MANUAL_OPERATOR_DECISION_PACKET_CONFIG_VERSION",
    "NEXT_MANUAL_REVIEW_ACTIONS",
    "SUPPORT_STATUSES",
    "FrozenJsonArray",
    "FrozenJsonObject",
    "ManualOperatorDecisionFact",
    "ManualOperatorDecisionPacket",
    "ManualOperatorDecisionPacketConfig",
    "ManualOperatorDecisionReasonSummary",
    "ManualOperatorGoNoGoPacket",
    "build_manual_operator_decision_packet",
    "build_manual_operator_go_no_go_packet",
    "manual_operator_decision_packet_payload",
    "manual_operator_decision_packet_payload_digest",
    "manual_operator_go_no_go_packet_payload",
    "manual_operator_go_no_go_packet_payload_digest",
)
