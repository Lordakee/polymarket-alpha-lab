"""Report-only specialist team resolution playbook gap assessment."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_MIN_RESOLUTION_RULE_EXAMPLES = Decimal("3.000000")
_MIN_POST_SETTLEMENT_NOTES = Decimal("1.000000")
_MAX_REVIEW_AGE_HOURS = Decimal("72.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_STATUS_VALUES = frozenset(("pass", "watch", "blocked"))
_REASON_CODE_SEQUENCE = (
    "resolution_rule_examples_gap",
    "ambiguous_resolution_rule_examples_present",
    "post_settlement_notes_gap",
    "playbook_review_stale",
    "specialist_team_resolution_playbook_gap_passed",
)
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_UNSAFE_PUBLIC_TERMS = (
    "live",
    "auth",
    "wallet",
    "key",
    "sign",
    "execute",
    "database",
    "db",
    "jsonl",
    "persist",
    "write",
    "order",
    "trade",
)


@dataclass(frozen=True)
class SpecialistTeamResolutionPlaybookGapReport:
    team_id: str
    category_id: str
    resolution_rule_examples_count: Decimal
    ambiguous_rule_examples_count: Decimal
    post_settlement_notes_count: Decimal
    last_playbook_review_age_hours: Decimal
    playbook_gap_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "SpecialistTeamResolutionPlaybookGapReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not SpecialistTeamResolutionPlaybookGapReport:
            raise ValueError(
                "report must be exactly SpecialistTeamResolutionPlaybookGapReport",
            )
        object.__setattr__(self, "team_id", _require_public_identifier("team_id", self.team_id))
        object.__setattr__(
            self,
            "category_id",
            _require_public_identifier("category_id", self.category_id),
        )
        for field_name in (
            "resolution_rule_examples_count",
            "ambiguous_rule_examples_count",
            "post_settlement_notes_count",
            "last_playbook_review_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "playbook_gap_status",
            _require_status("playbook_gap_status", self.playbook_gap_status),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "manual_next_step",
            _require_manual_next_step("manual_next_step", self.manual_next_step),
        )
        if self.playbook_gap_status != _status_from_reason_codes(self.reason_codes):
            raise ValueError("playbook_gap_status must match reason_codes")
        if self.manual_next_step != _manual_next_step(self.reason_codes):
            raise ValueError("manual_next_step must match reason_codes")
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)

    @property
    def public_payload(self) -> dict[str, Any]:
        values = _report_values(self)
        payload = _json_ready(values)
        if type(payload) is not dict:
            raise ValueError("public_payload must be a JSON object")
        _reject_unsafe_public_payload("public_payload", payload, allow_json_containers=True)
        return payload

    @property
    def payload_digest(self) -> str:
        return _payload_digest(self.public_payload)


def build_specialist_team_resolution_playbook_gap_report(
    *,
    team_id: str,
    category_id: str,
    resolution_rule_examples_count: Decimal,
    ambiguous_rule_examples_count: Decimal,
    post_settlement_notes_count: Decimal,
    last_playbook_review_age_hours: Decimal,
) -> SpecialistTeamResolutionPlaybookGapReport:
    """Build a deterministic report-only specialist resolution playbook gap snapshot."""

    reason_codes = _reason_codes(
        resolution_rule_examples_count=resolution_rule_examples_count,
        ambiguous_rule_examples_count=ambiguous_rule_examples_count,
        post_settlement_notes_count=post_settlement_notes_count,
        last_playbook_review_age_hours=last_playbook_review_age_hours,
    )
    return SpecialistTeamResolutionPlaybookGapReport(
        team_id=team_id,
        category_id=category_id,
        resolution_rule_examples_count=resolution_rule_examples_count,
        ambiguous_rule_examples_count=ambiguous_rule_examples_count,
        post_settlement_notes_count=post_settlement_notes_count,
        last_playbook_review_age_hours=last_playbook_review_age_hours,
        playbook_gap_status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
        manual_next_step=_manual_next_step(reason_codes),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _reason_codes(
    *,
    resolution_rule_examples_count: Decimal,
    ambiguous_rule_examples_count: Decimal,
    post_settlement_notes_count: Decimal,
    last_playbook_review_age_hours: Decimal,
) -> tuple[str, ...]:
    resolution_count = _require_nonnegative_decimal(
        "resolution_rule_examples_count",
        resolution_rule_examples_count,
    )
    ambiguous_count = _require_nonnegative_decimal(
        "ambiguous_rule_examples_count",
        ambiguous_rule_examples_count,
    )
    notes_count = _require_nonnegative_decimal(
        "post_settlement_notes_count",
        post_settlement_notes_count,
    )
    review_age = _require_nonnegative_decimal(
        "last_playbook_review_age_hours",
        last_playbook_review_age_hours,
    )

    reason_codes: list[str] = []
    if resolution_count < _MIN_RESOLUTION_RULE_EXAMPLES:
        reason_codes.append("resolution_rule_examples_gap")
    if ambiguous_count > _ZERO:
        reason_codes.append("ambiguous_resolution_rule_examples_present")
    if notes_count < _MIN_POST_SETTLEMENT_NOTES:
        reason_codes.append("post_settlement_notes_gap")
    if review_age > _MAX_REVIEW_AGE_HOURS:
        reason_codes.append("playbook_review_stale")
    if not reason_codes:
        return ("specialist_team_resolution_playbook_gap_passed",)
    return _normalize_reason_codes(tuple(reason_codes))


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("specialist_team_resolution_playbook_gap_passed",):
        return "pass"
    if (
        "resolution_rule_examples_gap" in reason_codes
        or "ambiguous_resolution_rule_examples_present" in reason_codes
    ):
        return "blocked"
    return "watch"


def _manual_next_step(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("specialist_team_resolution_playbook_gap_passed",):
        return "continue scheduled review cadence"
    if (
        "resolution_rule_examples_gap" in reason_codes
        or "ambiguous_resolution_rule_examples_present" in reason_codes
    ):
        return "manually add deterministic resolution rule examples and adjudicate ambiguous rules"
    return "manually refresh settlement notes and schedule specialist playbook review"


def _report_values(report: SpecialistTeamResolutionPlaybookGapReport) -> dict[str, object]:
    return {
        "team_id": report.team_id,
        "category_id": report.category_id,
        "resolution_rule_examples_count": report.resolution_rule_examples_count,
        "ambiguous_rule_examples_count": report.ambiguous_rule_examples_count,
        "post_settlement_notes_count": report.post_settlement_notes_count,
        "last_playbook_review_age_hours": report.last_playbook_review_age_hours,
        "playbook_gap_status": report.playbook_gap_status,
        "reason_codes": report.reason_codes,
        "manual_next_step": report.manual_next_step,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str or not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_manual_next_step(field_name: str, value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a nonblank string")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUS_VALUES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(_QUANT, rounding=ROUND_HALF_UP)
    if normalized != value:
        raise ValueError(f"{field_name} must have six-decimal precision")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_codes must contain supported codes")
        if reason_code not in normalized:
            normalized.append(reason_code)
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    return tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _payload_digest(payload: Mapping[str, object]) -> str:
    _reject_unsafe_public_payload("payload_digest", payload, allow_json_containers=True)
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if value is None or type(value) is bool or type(value) is Decimal:
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


__all__ = (
    "SpecialistTeamResolutionPlaybookGapReport",
    "build_specialist_team_resolution_playbook_gap_report",
)
