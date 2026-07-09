"""Aggregate report-only quorum checks for resolution source memory."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
from typing import Any, Final


QUORUM_STATUSES: Final[tuple[str, str, str]] = ("pass", "watch", "block")

_ZERO: Final = Decimal("0")
_ONE: Final = Decimal("1")
_RATIO_QUANTUM: Final = Decimal("0.000001")
_DIGEST_FIELD: Final = "derived_validation_digest"

_DECIMAL_FIELDS: Final = (
    "observed_memory_count",
    "agreeing_memory_count",
    "independent_memory_count",
    "stale_memory_count",
    "conflict_memory_count",
    "required_quorum_count",
    "min_independent_memory_count",
    "max_stale_memory_count",
    "max_conflict_memory_count",
    "quorum_margin",
    "agreement_ratio",
)

_COUNT_FIELDS: Final = (
    "observed_memory_count",
    "agreeing_memory_count",
    "independent_memory_count",
    "stale_memory_count",
    "conflict_memory_count",
    "required_quorum_count",
    "min_independent_memory_count",
    "max_stale_memory_count",
    "max_conflict_memory_count",
)

_PUBLIC_PAYLOAD_KEYS: Final = frozenset(
    (
        *_DECIMAL_FIELDS,
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
        _DIGEST_FIELD,
    ),
)

_REASON_CODES: Final = frozenset(
    (
        "aggregate_memory_clean",
        "conflict_limit_exceeded",
        "conflict_memory_present",
        "independence_floor_met",
        "independence_floor_unmet",
        "minimum_quorum_edge",
        "quorum_margin_positive",
        "quorum_shortfall",
        "stale_limit_exceeded",
        "stale_memory_present",
    ),
)

_UNSAFE_PUBLIC_FRAGMENTS: Final = frozenset(
    (
        "://",
        "account",
        "api_key",
        "auth",
        "balance",
        "cancel",
        "candidate",
        "clob",
        "database",
        "dsn",
        "live",
        "market",
        "order",
        "position",
        "private",
        "question",
        "recommendation",
        "replace",
        "secret",
        "sign",
        "sizing",
        "slug",
        "source_text",
        "source_url",
        "table",
        "token",
        "trade",
        "url",
        "wallet",
        "www.",
    ),
)


@dataclass(frozen=True)
class ResearchTeamResolutionSourceMemoryQuorumInput:
    observed_memory_count: Decimal
    agreeing_memory_count: Decimal
    independent_memory_count: Decimal
    stale_memory_count: Decimal
    conflict_memory_count: Decimal
    required_quorum_count: Decimal
    min_independent_memory_count: Decimal
    max_stale_memory_count: Decimal
    max_conflict_memory_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in _COUNT_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                    allow_negative=False,
                ),
            )
        _require_positive(
            "required_quorum_count",
            self.required_quorum_count,
        )
        _require_positive(
            "min_independent_memory_count",
            self.min_independent_memory_count,
        )
        _validate_count_relationships(self)
        _require_flags("input", self)


@dataclass(frozen=True)
class ResearchTeamResolutionSourceMemoryQuorumReport:
    observed_memory_count: Decimal
    agreeing_memory_count: Decimal
    independent_memory_count: Decimal
    stale_memory_count: Decimal
    conflict_memory_count: Decimal
    required_quorum_count: Decimal
    min_independent_memory_count: Decimal
    max_stale_memory_count: Decimal
    max_conflict_memory_count: Decimal
    quorum_margin: Decimal
    agreement_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in _COUNT_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                    allow_negative=False,
                ),
            )
        object.__setattr__(
            self,
            "quorum_margin",
            _normalize_integral_decimal(
                "quorum_margin",
                self.quorum_margin,
                allow_negative=True,
            ),
        )
        object.__setattr__(
            self,
            "agreement_ratio",
            _normalize_ratio("agreement_ratio", self.agreement_ratio),
        )
        _require_positive(
            "required_quorum_count",
            self.required_quorum_count,
        )
        _require_positive(
            "min_independent_memory_count",
            self.min_independent_memory_count,
        )
        _validate_count_relationships(self)
        _require_status(self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        if self.quorum_margin != self.agreeing_memory_count - self.required_quorum_count:
            raise ValueError("quorum_margin must match quorum counts")
        if self.agreement_ratio != _agreement_ratio(
            self.agreeing_memory_count,
            self.observed_memory_count,
        ):
            raise ValueError("agreement_ratio must match memory counts")
        if self.status != _status_for(self):
            raise ValueError("status must match quorum counts")
        if self.reason_codes != _reason_codes_for(self):
            raise ValueError("reason_codes must match quorum counts")
        _require_flags("report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_team_resolution_source_memory_quorum_report_payload(self)


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


def build_research_team_resolution_source_memory_quorum_report(
    *,
    observed_memory_count: Decimal,
    agreeing_memory_count: Decimal,
    independent_memory_count: Decimal,
    stale_memory_count: Decimal,
    conflict_memory_count: Decimal,
    required_quorum_count: Decimal,
    min_independent_memory_count: Decimal,
    max_stale_memory_count: Decimal,
    max_conflict_memory_count: Decimal,
) -> ResearchTeamResolutionSourceMemoryQuorumReport:
    inputs = ResearchTeamResolutionSourceMemoryQuorumInput(
        observed_memory_count=observed_memory_count,
        agreeing_memory_count=agreeing_memory_count,
        independent_memory_count=independent_memory_count,
        stale_memory_count=stale_memory_count,
        conflict_memory_count=conflict_memory_count,
        required_quorum_count=required_quorum_count,
        min_independent_memory_count=min_independent_memory_count,
        max_stale_memory_count=max_stale_memory_count,
        max_conflict_memory_count=max_conflict_memory_count,
    )
    return ResearchTeamResolutionSourceMemoryQuorumReport(
        observed_memory_count=inputs.observed_memory_count,
        agreeing_memory_count=inputs.agreeing_memory_count,
        independent_memory_count=inputs.independent_memory_count,
        stale_memory_count=inputs.stale_memory_count,
        conflict_memory_count=inputs.conflict_memory_count,
        required_quorum_count=inputs.required_quorum_count,
        min_independent_memory_count=inputs.min_independent_memory_count,
        max_stale_memory_count=inputs.max_stale_memory_count,
        max_conflict_memory_count=inputs.max_conflict_memory_count,
        quorum_margin=inputs.agreeing_memory_count - inputs.required_quorum_count,
        agreement_ratio=_agreement_ratio(
            inputs.agreeing_memory_count,
            inputs.observed_memory_count,
        ),
        status=_status_for(inputs),
        reason_codes=_reason_codes_for(inputs),
    )


def research_team_resolution_source_memory_quorum_report_payload(
    report: ResearchTeamResolutionSourceMemoryQuorumReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamResolutionSourceMemoryQuorumReport:
        _require_flags("report", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        payload[_DIGEST_FIELD] = _validation_digest(payload)
        _validate_public_payload(payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _validate_public_payload(payload)
        return payload
    raise ValueError("report must be a ResearchTeamResolutionSourceMemoryQuorumReport")


def research_team_resolution_source_memory_quorum_report_json(
    report: ResearchTeamResolutionSourceMemoryQuorumReport | dict[str, Any],
) -> str:
    return _canonical_json(
        research_team_resolution_source_memory_quorum_report_payload(report),
    )


def _validate_public_payload(payload: dict[str, Any]) -> None:
    _reject_unsafe_public_payload("payload", payload)
    _require_flags("payload", _DictFlags(payload))
    _require_payload_keys(payload)
    _require_payload_status(payload)
    _require_payload_reason_codes(payload)
    _require_payload_decimal_strings(payload)
    _require_payload_digest(payload)


def _require_payload_keys(payload: dict[str, Any]) -> None:
    keys = frozenset(payload)
    missing = _PUBLIC_PAYLOAD_KEYS - keys
    if missing:
        raise ValueError("public payload is missing required fields")
    unexpected = keys - _PUBLIC_PAYLOAD_KEYS
    if unexpected:
        raise ValueError("public payload contains unexpected fields")


def _require_payload_status(payload: dict[str, Any]) -> None:
    status = payload.get("status")
    if type(status) is not str:
        raise ValueError("status must be a string")
    _require_status(status)


def _require_payload_reason_codes(payload: dict[str, Any]) -> None:
    reason_codes = payload.get("reason_codes")
    if type(reason_codes) is not list or not reason_codes:
        raise ValueError("reason_codes must be a non-empty list")
    seen: set[str] = set()
    for code in reason_codes:
        if type(code) is not str or code not in _REASON_CODES:
            raise ValueError("reason_codes contains unsupported code")
        if code in seen:
            raise ValueError("reason_codes must not contain duplicates")
        seen.add(code)


def _require_payload_decimal_strings(payload: dict[str, Any]) -> None:
    for field_name in _DECIMAL_FIELDS:
        value = payload.get(field_name)
        if type(value) is not str:
            raise ValueError(f"{field_name} must be a Decimal-derived string")
        decimal_value = _parse_decimal_string(field_name, value)
        if field_name == "agreement_ratio":
            _normalize_ratio(field_name, decimal_value)
        elif field_name == "quorum_margin":
            _normalize_integral_decimal(
                field_name,
                decimal_value,
                allow_negative=True,
            )
        else:
            _normalize_integral_decimal(
                field_name,
                decimal_value,
                allow_negative=False,
            )


def _require_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get(_DIGEST_FIELD)
    if type(digest) is not str or len(digest) != 64:
        raise ValueError("derived_validation_digest is required")
    if any(character not in "0123456789abcdef" for character in digest):
        raise ValueError("derived_validation_digest must be lowercase sha256 hex")
    if digest != _validation_digest(payload):
        raise ValueError("derived_validation_digest mismatch")


def _validation_digest(payload: dict[str, Any]) -> str:
    unsigned_payload = dict(payload)
    unsigned_payload.pop(_DIGEST_FIELD, None)
    return sha256(_canonical_json(unsigned_payload).encode("utf-8")).hexdigest()


def _canonical_json(payload: object) -> str:
    return json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )


def _status_for(value: object) -> str:
    if (
        getattr(value, "agreeing_memory_count") < getattr(value, "required_quorum_count")
        or getattr(value, "independent_memory_count")
        < getattr(value, "min_independent_memory_count")
        or getattr(value, "stale_memory_count")
        > getattr(value, "max_stale_memory_count")
        or getattr(value, "conflict_memory_count")
        > getattr(value, "max_conflict_memory_count")
    ):
        return "block"
    if (
        getattr(value, "agreeing_memory_count")
        == getattr(value, "required_quorum_count")
        or getattr(value, "stale_memory_count") > _ZERO
        or getattr(value, "conflict_memory_count") > _ZERO
    ):
        return "watch"
    return "pass"


def _reason_codes_for(value: object) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if getattr(value, "agreeing_memory_count") < getattr(value, "required_quorum_count"):
        reason_codes.append("quorum_shortfall")
    elif (
        getattr(value, "agreeing_memory_count")
        == getattr(value, "required_quorum_count")
    ):
        reason_codes.append("minimum_quorum_edge")
    else:
        reason_codes.append("quorum_margin_positive")
    if (
        getattr(value, "independent_memory_count")
        < getattr(value, "min_independent_memory_count")
    ):
        reason_codes.append("independence_floor_unmet")
    else:
        reason_codes.append("independence_floor_met")
    if getattr(value, "stale_memory_count") > getattr(value, "max_stale_memory_count"):
        reason_codes.append("stale_limit_exceeded")
    elif getattr(value, "stale_memory_count") > _ZERO:
        reason_codes.append("stale_memory_present")
    if (
        getattr(value, "conflict_memory_count")
        > getattr(value, "max_conflict_memory_count")
    ):
        reason_codes.append("conflict_limit_exceeded")
    elif getattr(value, "conflict_memory_count") > _ZERO:
        reason_codes.append("conflict_memory_present")
    if (
        getattr(value, "stale_memory_count") == _ZERO
        and getattr(value, "conflict_memory_count") == _ZERO
    ):
        reason_codes.append("aggregate_memory_clean")
    return tuple(reason_codes)


def _agreement_ratio(agreeing_memory_count: Decimal, observed_memory_count: Decimal) -> Decimal:
    if observed_memory_count == _ZERO:
        return _ZERO.quantize(_RATIO_QUANTUM)
    with localcontext() as context:
        context.prec = 28
        return (agreeing_memory_count / observed_memory_count).quantize(
            _RATIO_QUANTUM,
            rounding=ROUND_HALF_UP,
        )


def _normalize_integral_decimal(
    field_name: str,
    value: object,
    *,
    allow_negative: bool,
) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if not allow_negative and value < _ZERO:
        raise ValueError(f"{field_name} must be non-negative")
    integral_value = value.to_integral_value()
    if value != integral_value:
        raise ValueError(f"{field_name} must be an integral Decimal")
    return integral_value


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < _ZERO or value > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return value.quantize(_RATIO_QUANTUM, rounding=ROUND_HALF_UP)


def _parse_decimal_string(field_name: str, value: str) -> Decimal:
    try:
        parsed = Decimal(value)
    except Exception as exc:  # pragma: no cover - Decimal exception type varies.
        raise ValueError(f"{field_name} must be a Decimal-derived string") from exc
    if not parsed.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return parsed


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError("reason_codes must be a non-empty tuple")
    normalized: list[str] = []
    seen: set[str] = set()
    for code in value:
        if type(code) is not str or code not in _REASON_CODES:
            raise ValueError("reason_codes contains unsupported code")
        if code in seen:
            raise ValueError("reason_codes must not contain duplicates")
        normalized.append(code)
        seen.add(code)
    return tuple(normalized)


def _validate_count_relationships(value: object) -> None:
    observed_memory_count = getattr(value, "observed_memory_count")
    if getattr(value, "agreeing_memory_count") > observed_memory_count:
        raise ValueError("agreeing_memory_count must not exceed observed_memory_count")
    if getattr(value, "independent_memory_count") > observed_memory_count:
        raise ValueError("independent_memory_count must not exceed observed_memory_count")
    if getattr(value, "stale_memory_count") > observed_memory_count:
        raise ValueError("stale_memory_count must not exceed observed_memory_count")
    if getattr(value, "conflict_memory_count") > observed_memory_count:
        raise ValueError("conflict_memory_count must not exceed observed_memory_count")


def _require_positive(field_name: str, value: Decimal) -> None:
    if value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")


def _require_status(value: object) -> None:
    if value not in QUORUM_STATUSES:
        raise ValueError("status must be pass, watch, or block")


def _require_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"unsafe value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe field in {label}")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in _UNSAFE_PUBLIC_FRAGMENTS)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be a Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, bool):
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


__all__ = (
    "QUORUM_STATUSES",
    "ResearchTeamResolutionSourceMemoryQuorumInput",
    "ResearchTeamResolutionSourceMemoryQuorumReport",
    "build_research_team_resolution_source_memory_quorum_report",
    "research_team_resolution_source_memory_quorum_report_json",
    "research_team_resolution_source_memory_quorum_report_payload",
)
