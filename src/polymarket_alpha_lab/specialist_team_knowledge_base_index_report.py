"""Readonly specialist team knowledge-base index readiness report."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
RATIO_QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
REQUIRED_SIGNAL_COUNT = Decimal("8")

READY_BAND = "ready"
ATTENTION_BAND = "attention"
BLOCKED_BAND = "blocked"
INDEX_BANDS = (READY_BAND, ATTENTION_BAND, BLOCKED_BAND)

READINESS_FIELDS = (
    "playbook_ready",
    "risk_register_ready",
    "memory_quality_ready",
    "postmortem_ready",
    "learning_dashboard_ready",
    "source_family_feedback_ready",
    "supabase_memory_ready",
    "public_payload_safety_ready",
)

BLOCKER_REASON_BY_FIELD = {
    "playbook_ready": "specialist_team_playbook_index_blocked",
    "risk_register_ready": "specialist_team_risk_register_index_blocked",
    "memory_quality_ready": "specialist_team_memory_quality_index_blocked",
    "supabase_memory_ready": "specialist_team_supabase_memory_index_blocked",
    "public_payload_safety_ready": "specialist_team_public_payload_safety_index_blocked",
}

ATTENTION_REASON_BY_FIELD = {
    "postmortem_ready": "specialist_team_postmortem_index_attention",
    "learning_dashboard_ready": "specialist_team_learning_dashboard_index_attention",
    "source_family_feedback_ready": "specialist_team_source_family_feedback_index_attention",
}

BLOCKED_REASON_CODES = tuple(BLOCKER_REASON_BY_FIELD.values())
ATTENTION_REASON_CODES = tuple(ATTENTION_REASON_BY_FIELD.values())

UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "auth",
    "buy",
    "database",
    "execution",
    "live",
    "mutation",
    "network",
    "order",
    "persist",
    "sell",
    "signing",
    "trade",
    "wallet",
)

__all__ = (
    "ATTENTION_REASON_CODES",
    "BLOCKED_REASON_CODES",
    "INDEX_BANDS",
    "SpecialistTeamKnowledgeBaseIndexReport",
    "build_specialist_team_knowledge_base_index_report",
)


@dataclass(frozen=True)
class SpecialistTeamKnowledgeBaseIndexReport:
    playbook_ready: bool
    risk_register_ready: bool
    memory_quality_ready: bool
    postmortem_ready: bool
    learning_dashboard_ready: bool
    source_family_feedback_ready: bool
    supabase_memory_ready: bool
    public_payload_safety_ready: bool
    knowledge_base_index_ready: bool
    index_band: str
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    ready_ratio: Decimal
    digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not SpecialistTeamKnowledgeBaseIndexReport:
            raise ValueError(
                "report must be exactly SpecialistTeamKnowledgeBaseIndexReport",
            )
        for field_name in READINESS_FIELDS:
            _require_bool(field_name, getattr(self, field_name))
        _require_bool("knowledge_base_index_ready", self.knowledge_base_index_ready)
        _require_index_band("index_band", self.index_band)
        object.__setattr__(
            self,
            "blocked_reason_codes",
            _normalize_reason_codes(
                "blocked_reason_codes",
                self.blocked_reason_codes,
                BLOCKED_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "attention_reason_codes",
            _normalize_reason_codes(
                "attention_reason_codes",
                self.attention_reason_codes,
                ATTENTION_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "ready_ratio",
            _require_ratio_decimal("ready_ratio", self.ready_ratio),
        )
        _require_hard_flags("report", self)
        _require_sha256_digest("digest", self.digest)
        _validate_report_consistency(self)
        if self.digest != _digest_for_report(self):
            raise ValueError("digest must match report payload")
        _reject_unsafe_public_payload("report", _payload_value(asdict(self)))

    @property
    def public_payload(self) -> dict[str, object]:
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        if self.digest != _digest_for_report(self):
            raise ValueError("digest must match report payload")
        payload = _payload_value(asdict(self))
        if type(payload) is not dict:
            raise ValueError("public_payload must be a dict")
        _reject_unsafe_public_payload("public_payload", payload)
        return payload


def build_specialist_team_knowledge_base_index_report(
    *,
    playbook_ready: bool,
    risk_register_ready: bool,
    memory_quality_ready: bool,
    postmortem_ready: bool,
    learning_dashboard_ready: bool,
    source_family_feedback_ready: bool,
    supabase_memory_ready: bool,
    public_payload_safety_ready: bool,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> SpecialistTeamKnowledgeBaseIndexReport:
    values: dict[str, object] = {
        "playbook_ready": playbook_ready,
        "risk_register_ready": risk_register_ready,
        "memory_quality_ready": memory_quality_ready,
        "postmortem_ready": postmortem_ready,
        "learning_dashboard_ready": learning_dashboard_ready,
        "source_family_feedback_ready": source_family_feedback_ready,
        "supabase_memory_ready": supabase_memory_ready,
        "public_payload_safety_ready": public_payload_safety_ready,
        "paper_only": paper_only,
        "report_only": report_only,
        "readonly": readonly,
    }
    for field_name in READINESS_FIELDS:
        _require_bool(field_name, values[field_name])
    _require_hard_flags("report", _HardFlagView(paper_only, report_only, readonly))

    blocked_reason_codes = _blocked_reason_codes(values)
    attention_reason_codes = _attention_reason_codes(values, blocked_reason_codes)
    values["knowledge_base_index_ready"] = (
        blocked_reason_codes == () and attention_reason_codes == ()
    )
    values["index_band"] = _index_band(blocked_reason_codes, attention_reason_codes)
    values["blocked_reason_codes"] = blocked_reason_codes
    values["attention_reason_codes"] = attention_reason_codes
    values["ready_ratio"] = _ready_ratio(values)
    values["digest"] = _digest_for_values(values)
    return SpecialistTeamKnowledgeBaseIndexReport(**values)  # type: ignore[arg-type]


@dataclass(frozen=True)
class _HardFlagView:
    paper_only: bool
    report_only: bool
    readonly: bool


def _blocked_reason_codes(values: dict[str, object]) -> tuple[str, ...]:
    return tuple(
        reason_code
        for field_name, reason_code in BLOCKER_REASON_BY_FIELD.items()
        if values[field_name] is False
    )


def _attention_reason_codes(
    values: dict[str, object],
    blocked_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if blocked_reason_codes:
        return ()
    return tuple(
        reason_code
        for field_name, reason_code in ATTENTION_REASON_BY_FIELD.items()
        if values[field_name] is False
    )


def _index_band(
    blocked_reason_codes: tuple[str, ...],
    attention_reason_codes: tuple[str, ...],
) -> str:
    if blocked_reason_codes:
        return BLOCKED_BAND
    if attention_reason_codes:
        return ATTENTION_BAND
    return READY_BAND


def _ready_ratio(values: dict[str, object]) -> Decimal:
    ready_count = Decimal(
        sum(1 for field_name in READINESS_FIELDS if values[field_name] is True),
    )
    with localcontext(DECIMAL_CONTEXT):
        return (ready_count / REQUIRED_SIGNAL_COUNT).quantize(RATIO_QUANT)


def _payload_value(value: object) -> object:
    if type(value) is Decimal:
        return format(value, "f")
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _payload_value(item) for key, item in value.items()}
    return value


def _digest_for_report(report: SpecialistTeamKnowledgeBaseIndexReport) -> str:
    return _digest_for_values(asdict(report))


def _digest_for_values(values: dict[str, object]) -> str:
    payload = {
        key: value
        for key, value in values.items()
        if key != "digest"
    }
    encoded = json.dumps(
        _payload_value(payload),
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _validate_report_consistency(
    report: SpecialistTeamKnowledgeBaseIndexReport,
) -> None:
    values = asdict(report)
    expected_blocked = _blocked_reason_codes(values)
    if report.blocked_reason_codes != expected_blocked:
        raise ValueError("blocked_reason_codes must match readiness inputs")
    expected_attention = _attention_reason_codes(values, expected_blocked)
    if report.attention_reason_codes != expected_attention:
        raise ValueError("attention_reason_codes must match readiness inputs")
    expected_ready = expected_blocked == () and expected_attention == ()
    if report.knowledge_base_index_ready is not expected_ready:
        raise ValueError("knowledge_base_index_ready must match reason codes")
    expected_band = _index_band(expected_blocked, expected_attention)
    if report.index_band != expected_band:
        raise ValueError("index_band must match reason codes")
    if report.ready_ratio != _ready_ratio(values):
        raise ValueError("ready_ratio must match readiness inputs")


def _normalize_reason_codes(
    name: str,
    value: object,
    allowed_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise ValueError(f"{name} must be a tuple")
    if any(type(reason_code) is not str for reason_code in value):
        raise ValueError(f"{name} must contain strings")
    if tuple(dict.fromkeys(value)) != value:
        raise ValueError(f"{name} must not contain duplicates")
    unknown_reason_codes = tuple(
        reason_code for reason_code in value if reason_code not in allowed_reason_codes
    )
    if unknown_reason_codes:
        raise ValueError(f"{name} must contain known reason codes")
    return value


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be exactly Decimal")
    if value < ZERO:
        raise ValueError(f"{name} must be >= 0.000000")
    if value > ONE:
        raise ValueError(f"{name} must be <= 1.000000")
    if value != value.quantize(RATIO_QUANT):
        raise ValueError(f"{name} must use six decimal places or fewer")
    return value.quantize(RATIO_QUANT)


def _require_index_band(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if value not in INDEX_BANDS:
        raise ValueError(f"{name} must be one of {INDEX_BANDS}")


def _require_bool(name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{name} must be a bool")


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


def _require_sha256_digest(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a sha256 hex digest")


def _reject_unsafe_public_payload(name: str, value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            _reject_unsafe_public_payload(name, item)
    elif isinstance(value, list | tuple):
        for item in value:
            _reject_unsafe_public_payload(name, item)
    elif type(value) is str:
        lowered = value.lower()
        if any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
            raise ValueError(f"{name} contains unsafe public payload text")
