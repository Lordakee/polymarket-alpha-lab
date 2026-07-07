"""Pure manual-operator decision support packet reducer.

The packet produced here is report-only checklist material for human review.
It only summarizes redacted review support for a human checklist.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Iterable

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


@dataclass(frozen=True)
class ManualOperatorDecisionPacketConfig:
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
class ManualOperatorDecisionFact:
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
class ManualOperatorDecisionReasonSummary:
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
class ManualOperatorDecisionPacket:
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
    require_paper_only_flags("manual operator decision packet config", config)
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


def manual_operator_decision_packet_payload(
    packet: ManualOperatorDecisionPacket,
) -> "FrozenJsonObject":
    if type(packet) is not ManualOperatorDecisionPacket:
        raise ValueError("packet must be exactly ManualOperatorDecisionPacket")
    require_paper_only_flags("manual operator decision packet", packet)
    payload = {
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
    _validate_json_ready_public_payload(payload)
    return _freeze_json_object(payload)


class FrozenJsonObject(dict[str, Any]):
    def __init__(self, value: dict[str, Any]) -> None:
        super().__init__(value)

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
        require_paper_only_flags("manual operator decision fact", fact)
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


def _freeze_json_object(value: dict[str, Any]) -> FrozenJsonObject:
    return FrozenJsonObject(
        {key: _freeze_json_value(item) for key, item in value.items()},
    )


def _freeze_json_value(value: Any) -> Any:
    if type(value) is dict:
        return _freeze_json_object(value)
    if type(value) is tuple:
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
    "build_manual_operator_decision_packet",
    "manual_operator_decision_packet_payload",
)
