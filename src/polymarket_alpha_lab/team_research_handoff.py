"""Immutable Phase 1 research-only handoff summaries between specialist teams."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_TEAM_RESEARCH_HANDOFF_CONFIG_VERSION = "team-research-handoff-v0"
HANDOFF_STATUSES = ("ready", "watch", "blocked")
NEXT_STEPS = {
    "ready": "archive_ready_research_handoffs",
    "watch": "review_watch_research_handoffs",
    "blocked": "resolve_blocked_research_handoffs",
}
REASON_CODES = {
    "ready": "team_research_handoff_ready",
    "watch": "team_research_handoff_watch",
    "blocked": "team_research_handoff_blocked",
}
SAFETY_FLAG_NAMES = ("paper_only", "report_only", "readonly")
SENSITIVE_FIELD_FRAGMENTS = frozenset(
    (
        "account",
        "api_key",
        "auth",
        "balance",
        "cancel",
        "credential",
        "dsn",
        "email",
        "exchange_mutation",
        "key",
        "live_trading",
        "network",
        "order",
        "password",
        "persistence",
        "private",
        "replace",
        "secret",
        "sign",
        "token",
        "wallet",
    ),
)
TRADE_INSTRUCTION_FRAGMENTS = frozenset(
    (
        "buy",
        "close position",
        "execute trade",
        "investment recommendation",
        "limit order",
        "market order",
        "open position",
        "place order",
        "position sizing",
        "position_sizing",
        "sell",
        "submit order",
        "trade execution",
    ),
)


@dataclass(frozen=True)
class TeamResearchHandoffConfig:
    config_version: str = DEFAULT_TEAM_RESEARCH_HANDOFF_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        require_paper_only_flags("TeamResearchHandoffConfig", self)


@dataclass(frozen=True)
class TeamResearchHandoffItem:
    source_team_id: str
    target_team_id: str
    handoff_status: str
    updated_at: datetime
    missing_evidence: tuple[str, ...]
    stale_sources: tuple[str, ...]
    blockers: tuple[str, ...]
    next_research_actions: tuple[str, ...]
    public_notes: str
    sensitive_fields: dict[str, object]
    reason_codes: tuple[str, ...]
    derived_validation: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("source_team_id", "target_team_id", "public_notes"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "public_notes", _redact_public_text(self.public_notes))
        _require_member("handoff_status", self.handoff_status, HANDOFF_STATUSES)
        object.__setattr__(self, "updated_at", _as_utc("updated_at", self.updated_at))
        object.__setattr__(
            self,
            "missing_evidence",
            _normalize_string_tuple("missing_evidence", self.missing_evidence, allow_empty=True),
        )
        object.__setattr__(
            self,
            "stale_sources",
            _normalize_string_tuple("stale_sources", self.stale_sources, allow_empty=True),
        )
        object.__setattr__(
            self,
            "blockers",
            _normalize_string_tuple("blockers", self.blockers, allow_empty=True),
        )
        object.__setattr__(
            self,
            "next_research_actions",
            _normalize_string_tuple(
                "next_research_actions",
                self.next_research_actions,
                allow_empty=False,
            ),
        )
        object.__setattr__(
            self,
            "sensitive_fields",
            _redact_sensitive_payload(
                _normalize_sensitive_fields(self.sensitive_fields),
                force=True,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_string_tuple("reason_codes", self.reason_codes, allow_empty=False),
        )
        _validate_item_consistency(self)
        _reject_trade_or_investment_instructions(self)
        _reject_unsafe_public_payload("TeamResearchHandoffItem", self)
        require_paper_only_flags("TeamResearchHandoffItem", self)
        object.__setattr__(
            self,
            "derived_validation",
            _validated_or_computed_derived_validation(self),
        )


@dataclass(frozen=True)
class TeamResearchHandoffSummary:
    generated_at: datetime
    config_version: str
    handoff_status: str
    recommended_next_step: str
    handoff_count: Decimal
    ready_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    missing_evidence_count: Decimal
    stale_source_count: Decimal
    blocker_count: Decimal
    items: tuple[TeamResearchHandoffItem, ...]
    reason_codes: tuple[str, ...]
    derived_validation: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_member("handoff_status", self.handoff_status, HANDOFF_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "handoff_count",
            "ready_count",
            "watch_count",
            "blocked_count",
            "missing_evidence_count",
            "stale_source_count",
            "blocker_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "items", _normalize_items(self.items))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_string_tuple("reason_codes", self.reason_codes, allow_empty=False),
        )
        _validate_summary_consistency(self)
        _reject_unsafe_public_payload("TeamResearchHandoffSummary", self)
        require_paper_only_flags("TeamResearchHandoffSummary", self)
        object.__setattr__(
            self,
            "derived_validation",
            _validated_or_computed_derived_validation(self),
        )


def build_team_research_handoff_summary(
    items: list[TeamResearchHandoffItem] | tuple[TeamResearchHandoffItem, ...],
    *,
    config: TeamResearchHandoffConfig,
    generated_at: datetime,
) -> TeamResearchHandoffSummary:
    if type(config) is not TeamResearchHandoffConfig:
        raise ValueError("config must be a TeamResearchHandoffConfig")
    require_paper_only_flags("TeamResearchHandoffConfig", config)
    normalized_items = _normalize_items(items)
    status = _summary_status(normalized_items)

    return TeamResearchHandoffSummary(
        generated_at=generated_at,
        config_version=config.config_version,
        handoff_status=status,
        recommended_next_step=NEXT_STEPS[status],
        handoff_count=_count_decimal(len(normalized_items)),
        ready_count=_status_count(normalized_items, "ready"),
        watch_count=_status_count(normalized_items, "watch"),
        blocked_count=_status_count(normalized_items, "blocked"),
        missing_evidence_count=_count_decimal(
            sum(len(item.missing_evidence) for item in normalized_items),
        ),
        stale_source_count=_count_decimal(sum(len(item.stale_sources) for item in normalized_items)),
        blocker_count=_count_decimal(sum(len(item.blockers) for item in normalized_items)),
        items=normalized_items,
        reason_codes=(REASON_CODES[status],),
    )


def team_research_handoff_payload(value: object) -> dict[str, Any]:
    if isinstance(value, (TeamResearchHandoffSummary, TeamResearchHandoffItem)):
        require_paper_only_flags("team research handoff payload", value)
    elif not isinstance(value, dict):
        raise ValueError("value must be a TeamResearchHandoffSummary, item, or JSON object")

    _reject_payload_trade_or_investment_instructions(value)
    _reject_unsafe_public_payload("team research handoff payload", value)
    payload = _json_ready_decimal_strings(value)
    if not isinstance(payload, dict):
        raise ValueError("team research handoff payload must be a JSON object")
    _validate_payload_safety_flags(payload, "payload", require_current_flags=True)
    _validate_payload_derived_validation(payload)
    _reject_unsafe_public_payload("team research handoff payload", payload)
    _reject_payload_trade_or_investment_instructions(payload)
    return payload


def format_team_research_handoff_summary(summary: TeamResearchHandoffSummary) -> str:
    if type(summary) is not TeamResearchHandoffSummary:
        raise ValueError("summary must be a TeamResearchHandoffSummary")
    require_paper_only_flags("TeamResearchHandoffSummary", summary)
    return (
        "team-research-handoff: "
        f"generated_at={summary.generated_at.isoformat()} "
        f"status={summary.handoff_status} "
        f"handoff_count={summary.handoff_count} "
        f"ready={summary.ready_count} "
        f"watch={summary.watch_count} "
        f"blocked={summary.blocked_count} "
        f"missing_evidence={summary.missing_evidence_count} "
        f"stale_sources={summary.stale_source_count} "
        f"blockers={summary.blocker_count} "
        f"next_step={summary.recommended_next_step} "
        f"items={_items_value(summary.items)} "
        f"reason_codes={_codes_value(summary.reason_codes)} "
        f"derived_validation={summary.derived_validation} "
        f"paper_only={summary.paper_only} "
        f"report_only={summary.report_only} "
        f"readonly={summary.readonly}\n"
    )


def _items_value(items: tuple[TeamResearchHandoffItem, ...]) -> str:
    if not items:
        return "none"
    return "|".join(_item_value(item) for item in items)


def _item_value(item: TeamResearchHandoffItem) -> str:
    return (
        f"{item.source_team_id}>{item.target_team_id}:"
        f"{item.handoff_status}:"
        f"{item.updated_at.isoformat()}:"
        f"missing={_codes_value(item.missing_evidence)}:"
        f"stale={_codes_value(item.stale_sources)}:"
        f"blockers={_codes_value(item.blockers)}:"
        f"actions={_codes_value(item.next_research_actions)}:"
        f"reasons={_codes_value(item.reason_codes)}:"
        f"validation={item.derived_validation}"
    )


def _codes_value(codes: tuple[str, ...]) -> str:
    if not codes:
        return "none"
    return ",".join(codes)


def _normalize_items(
    items: list[TeamResearchHandoffItem] | tuple[TeamResearchHandoffItem, ...],
) -> tuple[TeamResearchHandoffItem, ...]:
    if type(items) not in (list, tuple):
        raise ValueError("items must be a list or tuple")
    normalized = tuple(items)
    for item in normalized:
        if type(item) is not TeamResearchHandoffItem:
            raise ValueError("items must contain TeamResearchHandoffItem values")
        require_paper_only_flags("TeamResearchHandoffItem", item)
    return tuple(sorted(normalized, key=lambda item: (item.source_team_id, item.target_team_id)))


def _summary_status(items: tuple[TeamResearchHandoffItem, ...]) -> str:
    if any(item.handoff_status == "blocked" for item in items):
        return "blocked"
    if any(item.handoff_status == "watch" for item in items):
        return "watch"
    if any(item.handoff_status == "ready" for item in items):
        return "ready"
    return "blocked"


def _status_count(items: tuple[TeamResearchHandoffItem, ...], status: str) -> Decimal:
    return _count_decimal(sum(1 for item in items if item.handoff_status == status))


def _validate_item_consistency(item: TeamResearchHandoffItem) -> None:
    if item.handoff_status == "ready" and (
        item.missing_evidence or item.stale_sources or item.blockers
    ):
        raise ValueError("ready handoffs require no missing evidence, stale sources, or blockers")
    if item.handoff_status != "blocked" and item.blockers:
        raise ValueError("blockers require blocked handoff_status")
    if item.handoff_status == "blocked" and not item.blockers:
        raise ValueError("blocked handoffs require blockers")


def _validate_summary_consistency(summary: TeamResearchHandoffSummary) -> None:
    if summary.handoff_count != _count_decimal(len(summary.items)):
        raise ValueError("handoff_count must match items")
    if summary.ready_count != _status_count(summary.items, "ready"):
        raise ValueError("ready_count must match items")
    if summary.watch_count != _status_count(summary.items, "watch"):
        raise ValueError("watch_count must match items")
    if summary.blocked_count != _status_count(summary.items, "blocked"):
        raise ValueError("blocked_count must match items")
    if summary.missing_evidence_count != _count_decimal(
        sum(len(item.missing_evidence) for item in summary.items),
    ):
        raise ValueError("missing_evidence_count must match items")
    if summary.stale_source_count != _count_decimal(
        sum(len(item.stale_sources) for item in summary.items),
    ):
        raise ValueError("stale_source_count must match items")
    if summary.blocker_count != _count_decimal(sum(len(item.blockers) for item in summary.items)):
        raise ValueError("blocker_count must match items")
    if summary.handoff_status != _summary_status(summary.items):
        raise ValueError("handoff_status must match items")
    if summary.recommended_next_step != NEXT_STEPS[summary.handoff_status]:
        raise ValueError("recommended_next_step must match handoff_status")
    if summary.reason_codes != (REASON_CODES[summary.handoff_status],):
        raise ValueError("reason_codes must match handoff_status")


def _normalize_sensitive_fields(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("sensitive_fields must be a JSON object")
    return _normalize_sensitive_dict(value)


def _normalize_sensitive_dict(value: dict[object, object]) -> dict[str, object]:
    normalized: dict[str, object] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError("sensitive_fields keys must be strings")
        if isinstance(item, dict):
            normalized[key] = _normalize_sensitive_dict(item)
        elif isinstance(item, (list, tuple)):
            normalized[key] = tuple(_normalize_sensitive_sequence(item))
        elif item is None or isinstance(item, (str, int, bool)):
            normalized[key] = item
        else:
            raise ValueError("sensitive_fields values must be JSON primitives")
    return normalized


def _normalize_sensitive_sequence(value: list[object] | tuple[object, ...]) -> list[object]:
    normalized = []
    for item in value:
        if isinstance(item, dict):
            normalized.append(_normalize_sensitive_dict(item))
        elif isinstance(item, (list, tuple)):
            normalized.append(tuple(_normalize_sensitive_sequence(item)))
        elif item is None or isinstance(item, (str, int, bool)):
            normalized.append(item)
        else:
            raise ValueError("sensitive_fields values must be JSON primitives")
    return normalized


def _redact_sensitive_payload(value: object, *, force: bool = False) -> object:
    if isinstance(value, dict):
        redacted: dict[str, object] = {}
        redacted_index = 1
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            should_redact = force or _is_sensitive_key(key)
            redacted_key = key
            if should_redact:
                redacted_key = f"redacted_field_{redacted_index}"
                redacted_index += 1
            redacted[redacted_key] = (
                "<redacted>"
                if should_redact and not isinstance(item, (dict, list, tuple))
                else _redact_sensitive_payload(item, force=should_redact)
            )
        return redacted
    if isinstance(value, list):
        return [_redact_sensitive_payload(item, force=force) for item in value]
    if isinstance(value, tuple):
        return tuple(_redact_sensitive_payload(item, force=force) for item in value)
    if force:
        return "<redacted>"
    if type(value) is str and _is_sensitive_text(value):
        return "<redacted>"
    return value


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower()
    return any(fragment in normalized for fragment in SENSITIVE_FIELD_FRAGMENTS)


def _redact_public_text(value: str) -> str:
    if _is_sensitive_text(value):
        return "<redacted>"
    return value


def _is_sensitive_text(value: str) -> bool:
    normalized = value.lower()
    return any(
        fragment in normalized
        for fragment in (
            "postgres://",
            "postgresql://",
            "database_url=",
            "dsn=",
            "password=",
            "secret=",
            "token=",
            "api_key=",
            "private_key=",
            "authorization=",
            "credential=",
        )
    )


def _reject_trade_or_investment_instructions(value: object) -> None:
    for text in _iter_public_strings(value):
        normalized = text.lower()
        if any(fragment in normalized for fragment in TRADE_INSTRUCTION_FRAGMENTS):
            raise ValueError("handoff must not contain trade or investment instruction")


def _reject_payload_trade_or_investment_instructions(value: object) -> None:
    _reject_trade_or_investment_instructions(_redact_sensitive_payload(value))


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
    if type(value) is float:
        raise ValueError(f"{path or label} must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if type(value) is str:
        if _is_sensitive_text(value):
            raise ValueError(f"{path or label} has unsafe value")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _is_sensitive_key(key):
                raise ValueError(f"unsafe field in {label}: {item_path}")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError(f"{path or label} is not JSON serializable")


def _iter_public_strings(value: object) -> tuple[str, ...]:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        strings: list[str] = []
        for field_name in value.__dataclass_fields__:
            if field_name == "sensitive_fields":
                continue
            strings.extend(_iter_public_strings(getattr(value, field_name)))
        return tuple(strings)
    if isinstance(value, dict):
        strings = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _is_sensitive_key(key):
                continue
            strings.extend(_iter_public_strings(item))
        return tuple(strings)
    if isinstance(value, (list, tuple)):
        strings = []
        for item in value:
            strings.extend(_iter_public_strings(item))
        return tuple(strings)
    if type(value) is str:
        return (value,)
    return ()


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
            _validate_payload_safety_flags(item, f"{field_path} {key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _validate_payload_safety_flags(item, f"{field_path} {index}")


def _validate_payload_derived_validation(payload: dict[str, Any]) -> None:
    if type(payload.get("derived_validation")) is not str:
        raise ValueError("payload derived_validation must be present")
    expected = _derived_validation_for_payload(payload)
    if payload["derived_validation"] != expected:
        raise ValueError("payload derived_validation must match payload")
    items = payload.get("items")
    if isinstance(items, list):
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                raise ValueError("payload items must be JSON objects")
            if type(item.get("derived_validation")) is not str:
                raise ValueError(f"payload items {index} derived_validation must be present")
            expected_item_validation = _derived_validation_for_payload(item)
            if item["derived_validation"] != expected_item_validation:
                raise ValueError(f"payload items {index} derived_validation must match payload")


def _validated_or_computed_derived_validation(value: object) -> str:
    expected = _derived_validation_for_payload(_validation_payload(value))
    current = getattr(value, "derived_validation")
    if current == "":
        return expected
    _require_canonical_string("derived_validation", current)
    if current != expected:
        raise ValueError("derived_validation must match derived payload")
    return current


def _derived_validation_for_payload(payload: dict[str, Any]) -> str:
    canonical_payload = dict(payload)
    canonical_payload.pop("derived_validation", None)
    encoded = json.dumps(
        canonical_payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _validation_payload(value: object) -> dict[str, Any]:
    payload = _json_ready_decimal_strings(value)
    if not isinstance(payload, dict):
        raise ValueError("derived_validation payload must be a JSON object")
    return payload


def _json_ready_decimal_strings(value: Any, path: str = "") -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {
            key: _json_ready_decimal_strings(nested_value, key if not path else f"{path}.{key}")
            for key, nested_value in asdict(value).items()
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
    if type(value) is float:
        raise ValueError(f"{path or 'value'} must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or 'value'} must use Decimal-derived string values")
    if type(value) is str:
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            ready[key] = _json_ready_decimal_strings(item, item_path)
        return ready
    if isinstance(value, (list, tuple)):
        return [
            _json_ready_decimal_strings(item, f"{path}[{index}]" if path else f"value[{index}]")
            for index, item in enumerate(value)
        ]
    raise ValueError(f"{path or 'value'} is not JSON serializable")


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


def _count_decimal(value: int) -> Decimal:
    return Decimal(value)


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is int:
        normalized = Decimal(value)
    elif type(value) is Decimal:
        normalized = value
    else:
        raise ValueError(f"{field_name} must be a Decimal count")
    if not normalized.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if normalized < 0:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-number Decimal")
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


__all__ = (
    "DEFAULT_TEAM_RESEARCH_HANDOFF_CONFIG_VERSION",
    "TeamResearchHandoffConfig",
    "TeamResearchHandoffItem",
    "TeamResearchHandoffSummary",
    "build_team_research_handoff_summary",
    "format_team_research_handoff_summary",
    "team_research_handoff_payload",
)
