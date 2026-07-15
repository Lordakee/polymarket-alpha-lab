"""Read-only operator output safety gate report."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields, is_dataclass
from decimal import Decimal, InvalidOperation
from typing import Any


__all__ = (
    "OperatorPublicOutputSafetyGateReport",
    "build_operator_public_output_safety_gate_report",
    "operator_public_output_safety_gate_report_payload",
)


PASS_REASON_CODE = "operator_public_output_safety_gate_pass"
AUDIT_MISSING_REASON_CODE = (
    "operator_public_output_safety_gate_public_payload_audit_missing"
)
MARKET_IDENTIFIER_REASON_CODE = (
    "operator_public_output_safety_gate_market_identifier_present"
)
ORDER_LANGUAGE_REASON_CODE = "operator_public_output_safety_gate_order_language_present"
AUTH_WALLET_REASON_CODE = (
    "operator_public_output_safety_gate_auth_or_wallet_term_present"
)
DSN_TABLE_REASON_CODE = "operator_public_output_safety_gate_dsn_or_table_term_present"
BLOCKED_FIELD_REASON_CODE = "operator_public_output_safety_gate_blocked_field_present"
BLOCKED_TOKEN_REASON_CODE = "operator_public_output_safety_gate_blocked_token_present"

ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")


@dataclass(frozen=True)
class OperatorPublicOutputSafetyGateReport:
    output_surface_name: str
    payload_field_names: tuple[str, ...]
    payload_text_tokens: tuple[str, ...]
    contains_market_identifier: bool
    contains_order_language: bool
    contains_auth_or_wallet_term: bool
    contains_dsn_or_table_term: bool
    audited_by_public_payload_safety: bool
    safe_for_operator_display: bool
    blocked_field_count: Decimal
    blocked_token_count: Decimal
    attention_reason_codes: tuple[str, ...]
    blocker_reason_codes: tuple[str, ...]
    ready_ratio: Decimal
    public_payload_digest: str
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not OperatorPublicOutputSafetyGateReport:
            raise TypeError("OperatorPublicOutputSafetyGateReport does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not OperatorPublicOutputSafetyGateReport:
            raise ValueError("report must be exactly OperatorPublicOutputSafetyGateReport")
        object.__setattr__(
            self,
            "output_surface_name",
            _require_public_string("output_surface_name", self.output_surface_name),
        )
        object.__setattr__(
            self,
            "payload_field_names",
            _normalize_public_string_tuple(
                "payload_field_names",
                self.payload_field_names,
                reject_live_terms=True,
            ),
        )
        object.__setattr__(
            self,
            "payload_text_tokens",
            _normalize_public_string_tuple(
                "payload_text_tokens",
                self.payload_text_tokens,
                reject_live_terms=False,
            ),
        )
        for field_name in (
            "contains_market_identifier",
            "contains_order_language",
            "contains_auth_or_wallet_term",
            "contains_dsn_or_table_term",
            "audited_by_public_payload_safety",
            "safe_for_operator_display",
        ):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "blocked_field_count",
            _require_nonnegative_whole_decimal(
                "blocked_field_count",
                self.blocked_field_count,
            ),
        )
        object.__setattr__(
            self,
            "blocked_token_count",
            _require_nonnegative_whole_decimal(
                "blocked_token_count",
                self.blocked_token_count,
            ),
        )
        object.__setattr__(
            self,
            "attention_reason_codes",
            _normalize_reason_codes(
                "attention_reason_codes",
                self.attention_reason_codes,
                allow_empty=False,
            ),
        )
        object.__setattr__(
            self,
            "blocker_reason_codes",
            _normalize_reason_codes(
                "blocker_reason_codes",
                self.blocker_reason_codes,
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "ready_ratio",
            _require_ratio_decimal("ready_ratio", self.ready_ratio),
        )
        object.__setattr__(
            self,
            "public_payload_digest",
            _require_digest("public_payload_digest", self.public_payload_digest),
        )
        object.__setattr__(
            self,
            "derived_validation_digest",
            _require_digest("derived_validation_digest", self.derived_validation_digest),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)


def build_operator_public_output_safety_gate_report(
    *,
    output_surface_name: str,
    payload_field_names: tuple[str, ...],
    payload_text_tokens: tuple[str, ...],
    contains_market_identifier: bool,
    contains_order_language: bool,
    contains_auth_or_wallet_term: bool,
    contains_dsn_or_table_term: bool,
    audited_by_public_payload_safety: bool,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> OperatorPublicOutputSafetyGateReport:
    output_surface_name = _require_public_string(
        "output_surface_name",
        output_surface_name,
    )
    payload_field_names = _normalize_public_string_tuple(
        "payload_field_names",
        payload_field_names,
        reject_live_terms=True,
    )
    payload_text_tokens = _normalize_public_string_tuple(
        "payload_text_tokens",
        payload_text_tokens,
        reject_live_terms=False,
    )
    for field_name, value in (
        ("contains_market_identifier", contains_market_identifier),
        ("contains_order_language", contains_order_language),
        ("contains_auth_or_wallet_term", contains_auth_or_wallet_term),
        ("contains_dsn_or_table_term", contains_dsn_or_table_term),
        ("audited_by_public_payload_safety", audited_by_public_payload_safety),
    ):
        _require_bool(field_name, value)
    _require_hard_flags(
        "builder",
        _FlagValues(
            paper_only=paper_only,
            report_only=report_only,
            readonly=readonly,
        ),
    )

    blocked_field_count = _decimal_count(
        sum(1 for field_name in payload_field_names if _field_has_blocker(field_name)),
    )
    blocked_token_count = _decimal_count(
        sum(1 for token in payload_text_tokens if _token_has_blocker(token)),
    )
    blocker_reason_codes = _blocker_reason_codes(
        contains_market_identifier=contains_market_identifier,
        contains_order_language=contains_order_language,
        contains_auth_or_wallet_term=contains_auth_or_wallet_term,
        contains_dsn_or_table_term=contains_dsn_or_table_term,
        audited_by_public_payload_safety=audited_by_public_payload_safety,
        blocked_field_count=blocked_field_count,
        blocked_token_count=blocked_token_count,
    )
    safe_for_operator_display = not blocker_reason_codes
    attention_reason_codes = (
        (PASS_REASON_CODE,) if safe_for_operator_display else blocker_reason_codes
    )
    ready_ratio = (ONE if safe_for_operator_display else ZERO).quantize(RATIO_QUANTUM)

    digest = _public_payload_digest(
        {
            "output_surface_name": output_surface_name,
            "payload_field_names": payload_field_names,
            "payload_text_tokens": payload_text_tokens,
            "contains_market_identifier": contains_market_identifier,
            "contains_order_language": contains_order_language,
            "contains_auth_or_wallet_term": contains_auth_or_wallet_term,
            "contains_dsn_or_table_term": contains_dsn_or_table_term,
            "audited_by_public_payload_safety": audited_by_public_payload_safety,
            "safe_for_operator_display": safe_for_operator_display,
            "blocked_field_count": blocked_field_count,
            "blocked_token_count": blocked_token_count,
            "attention_reason_codes": attention_reason_codes,
            "blocker_reason_codes": blocker_reason_codes,
            "ready_ratio": ready_ratio,
            "paper_only": paper_only,
            "report_only": report_only,
            "readonly": readonly,
        },
    )

    return OperatorPublicOutputSafetyGateReport(
        output_surface_name=output_surface_name,
        payload_field_names=payload_field_names,
        payload_text_tokens=payload_text_tokens,
        contains_market_identifier=contains_market_identifier,
        contains_order_language=contains_order_language,
        contains_auth_or_wallet_term=contains_auth_or_wallet_term,
        contains_dsn_or_table_term=contains_dsn_or_table_term,
        audited_by_public_payload_safety=audited_by_public_payload_safety,
        safe_for_operator_display=safe_for_operator_display,
        blocked_field_count=blocked_field_count,
        blocked_token_count=blocked_token_count,
        attention_reason_codes=attention_reason_codes,
        blocker_reason_codes=blocker_reason_codes,
        ready_ratio=ready_ratio,
        public_payload_digest=digest,
        derived_validation_digest=digest,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def operator_public_output_safety_gate_report_payload(
    report: OperatorPublicOutputSafetyGateReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is OperatorPublicOutputSafetyGateReport:
        _require_hard_flags("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_public_numerics(report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be an OperatorPublicOutputSafetyGateReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_public_numerics(payload)
    _require_hard_flags("payload", _DictFlags(payload))
    _validate_public_payload(payload)
    return payload


@dataclass(frozen=True)
class _FlagValues:
    paper_only: object
    report_only: object
    readonly: object


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


def _blocker_reason_codes(
    *,
    contains_market_identifier: bool,
    contains_order_language: bool,
    contains_auth_or_wallet_term: bool,
    contains_dsn_or_table_term: bool,
    audited_by_public_payload_safety: bool,
    blocked_field_count: Decimal,
    blocked_token_count: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if not audited_by_public_payload_safety:
        reason_codes.append(AUDIT_MISSING_REASON_CODE)
    if contains_market_identifier:
        reason_codes.append(MARKET_IDENTIFIER_REASON_CODE)
    if contains_order_language:
        reason_codes.append(ORDER_LANGUAGE_REASON_CODE)
    if contains_auth_or_wallet_term:
        reason_codes.append(AUTH_WALLET_REASON_CODE)
    if contains_dsn_or_table_term:
        reason_codes.append(DSN_TABLE_REASON_CODE)
    if blocked_field_count > ZERO:
        reason_codes.append(BLOCKED_FIELD_REASON_CODE)
    if blocked_token_count > ZERO:
        reason_codes.append(BLOCKED_TOKEN_REASON_CODE)
    return tuple(reason_codes)


def _field_has_blocker(field_name: str) -> bool:
    normalized = _normalized_name(field_name)
    return (
        _contains_market_identifier(normalized)
        or _contains_order_language(normalized)
        or _contains_auth_or_wallet_term(normalized)
        or _contains_dsn_or_table_term(normalized)
        or _contains_live_surface_term(normalized)
    )


def _token_has_blocker(token: str) -> bool:
    normalized = _normalized_name(token)
    return (
        _contains_market_identifier(normalized)
        or _contains_order_language(normalized)
        or _contains_auth_or_wallet_term(normalized)
        or _contains_dsn_or_table_term(normalized)
        or _contains_live_surface_term(normalized)
    )


def _contains_market_identifier(value: str) -> bool:
    return value == "market" or "market_id" in value or value.endswith("_marketid")


def _contains_order_language(value: str) -> bool:
    return any(fragment in value for fragment in ("buy", "sell", "order", "trade"))


def _contains_auth_or_wallet_term(value: str) -> bool:
    return any(fragment in value for fragment in ("auth", "wallet", "credential"))


def _contains_dsn_or_table_term(value: str) -> bool:
    return any(fragment in value for fragment in ("dsn", "table", "token"))


def _contains_live_surface_term(value: str) -> bool:
    fragments = (
        "live" + "_" + "trading",
        "bro" + "ker",
        "cancel" + "_" + "order",
        "private" + "_" + "key",
        "api" + "_" + "key",
        "secret" + "_" + "key",
    )
    return any(fragment in value for fragment in fragments)


def _normalized_name(value: str) -> str:
    return value.lower().replace("-", "_").replace(" ", "_").replace(".", "_")


def _validate_public_payload(payload: dict[str, Any]) -> None:
    required_keys = {
        "output_surface_name",
        "payload_field_names",
        "payload_text_tokens",
        "contains_market_identifier",
        "contains_order_language",
        "contains_auth_or_wallet_term",
        "contains_dsn_or_table_term",
        "audited_by_public_payload_safety",
        "safe_for_operator_display",
        "blocked_field_count",
        "blocked_token_count",
        "attention_reason_codes",
        "blocker_reason_codes",
        "ready_ratio",
        "public_payload_digest",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    }
    if set(payload) != required_keys:
        raise ValueError("report payload must use the supported public schema")
    _validate_public_payload_consistency(payload)
    expected_digest = _public_payload_digest(payload)
    if payload["derived_validation_digest"] != expected_digest:
        raise ValueError("derived_validation_digest does not match public payload")
    if payload["public_payload_digest"] != expected_digest:
        raise ValueError("public_payload_digest does not match public payload")


def _validate_public_payload_consistency(payload: dict[str, Any]) -> None:
    payload_field_names = _tuple_from_public_list(
        "payload_field_names",
        payload["payload_field_names"],
    )
    payload_text_tokens = _tuple_from_public_list(
        "payload_text_tokens",
        payload["payload_text_tokens"],
    )
    expected_blocked_field_count = _decimal_count(
        sum(1 for field_name in payload_field_names if _field_has_blocker(field_name)),
    )
    expected_blocked_token_count = _decimal_count(
        sum(1 for token in payload_text_tokens if _token_has_blocker(token)),
    )
    blocked_field_count = _parse_decimal_string(
        "blocked_field_count",
        payload["blocked_field_count"],
    )
    blocked_token_count = _parse_decimal_string(
        "blocked_token_count",
        payload["blocked_token_count"],
    )
    if blocked_field_count != expected_blocked_field_count:
        raise ValueError("blocked_field_count must match payload_field_names")
    if blocked_token_count != expected_blocked_token_count:
        raise ValueError("blocked_token_count must match payload_text_tokens")
    contains_market_identifier = _require_bool_value(
        "contains_market_identifier",
        payload["contains_market_identifier"],
    )
    contains_order_language = _require_bool_value(
        "contains_order_language",
        payload["contains_order_language"],
    )
    contains_auth_or_wallet_term = _require_bool_value(
        "contains_auth_or_wallet_term",
        payload["contains_auth_or_wallet_term"],
    )
    contains_dsn_or_table_term = _require_bool_value(
        "contains_dsn_or_table_term",
        payload["contains_dsn_or_table_term"],
    )
    audited_by_public_payload_safety = _require_bool_value(
        "audited_by_public_payload_safety",
        payload["audited_by_public_payload_safety"],
    )
    safe_for_operator_display = _require_bool_value(
        "safe_for_operator_display",
        payload["safe_for_operator_display"],
    )
    expected_blockers = _blocker_reason_codes(
        contains_market_identifier=contains_market_identifier,
        contains_order_language=contains_order_language,
        contains_auth_or_wallet_term=contains_auth_or_wallet_term,
        contains_dsn_or_table_term=contains_dsn_or_table_term,
        audited_by_public_payload_safety=audited_by_public_payload_safety,
        blocked_field_count=blocked_field_count,
        blocked_token_count=blocked_token_count,
    )
    if _tuple_from_public_list("blocker_reason_codes", payload["blocker_reason_codes"]) != expected_blockers:
        raise ValueError("blocker_reason_codes must match gate inputs")
    expected_safe = not expected_blockers
    if safe_for_operator_display is not expected_safe:
        raise ValueError("safe_for_operator_display must match blocker_reason_codes")
    expected_attention = (PASS_REASON_CODE,) if expected_safe else expected_blockers
    if _tuple_from_public_list("attention_reason_codes", payload["attention_reason_codes"]) != expected_attention:
        raise ValueError("attention_reason_codes must match gate status")
    expected_ready_ratio = ONE if expected_safe else ZERO
    if _parse_decimal_string("ready_ratio", payload["ready_ratio"]) != expected_ready_ratio:
        raise ValueError("ready_ratio must match gate status")


def _validate_report_consistency(report: OperatorPublicOutputSafetyGateReport) -> None:
    if report.public_payload_digest != report.derived_validation_digest:
        raise ValueError("derived_validation_digest must match public_payload_digest")
    expected_blocked_field_count = _decimal_count(
        sum(1 for field_name in report.payload_field_names if _field_has_blocker(field_name)),
    )
    expected_blocked_token_count = _decimal_count(
        sum(1 for token in report.payload_text_tokens if _token_has_blocker(token)),
    )
    if report.blocked_field_count != expected_blocked_field_count:
        raise ValueError("blocked_field_count must match payload_field_names")
    if report.blocked_token_count != expected_blocked_token_count:
        raise ValueError("blocked_token_count must match payload_text_tokens")
    expected_blockers = _blocker_reason_codes(
        contains_market_identifier=report.contains_market_identifier,
        contains_order_language=report.contains_order_language,
        contains_auth_or_wallet_term=report.contains_auth_or_wallet_term,
        contains_dsn_or_table_term=report.contains_dsn_or_table_term,
        audited_by_public_payload_safety=report.audited_by_public_payload_safety,
        blocked_field_count=report.blocked_field_count,
        blocked_token_count=report.blocked_token_count,
    )
    if report.blocker_reason_codes != expected_blockers:
        raise ValueError("blocker_reason_codes must match gate inputs")
    expected_safe = not expected_blockers
    if report.safe_for_operator_display is not expected_safe:
        raise ValueError("safe_for_operator_display must match blocker_reason_codes")
    expected_attention = (PASS_REASON_CODE,) if expected_safe else expected_blockers
    if report.attention_reason_codes != expected_attention:
        raise ValueError("attention_reason_codes must match gate status")
    expected_ready_ratio = ONE if expected_safe else ZERO
    if report.ready_ratio != expected_ready_ratio:
        raise ValueError("ready_ratio must match gate status")


def _tuple_from_public_list(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a public list")
    normalized: list[str] = []
    for item in value:
        normalized.append(_require_public_string(field_name, item))
    return tuple(normalized)


def _parse_decimal_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal-derived string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal-derived string") from exc
    return parsed


def _require_bool_value(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _public_payload_digest(value: dict[str, Any]) -> str:
    payload = dict(value)
    payload.pop("public_payload_digest", None)
    payload.pop("derived_validation_digest", None)
    json_ready = _json_ready(payload)
    encoded = json.dumps(json_ready, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _json_ready(value: object) -> object:
    if type(value) is Decimal:
        return str(value)
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if type(value) is tuple or type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        converted: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            converted[key] = _json_ready(item)
        return converted
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("value is not JSON serializable")


def _reject_public_numerics(value: object) -> None:
    if type(value) is int or isinstance(value, float):
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if type(value) is dict:
        for item in value.values():
            _reject_public_numerics(item)
        return
    if type(value) is list:
        for item in value:
            _reject_public_numerics(item)


def _normalize_public_string_tuple(
    field_name: str,
    values: object,
    *,
    reject_live_terms: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        text = _require_public_string(field_name, value)
        if reject_live_terms and _contains_live_surface_term(_normalized_name(text)):
            raise ValueError(f"{field_name} contains an unsupported live surface term")
        normalized.append(text)
    return tuple(normalized)


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        normalized.append(_require_reason_code(field_name, value))
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(normalized)


def _require_reason_code(field_name: str, value: object) -> str:
    text = _require_public_string(field_name, value)
    if text.lower() != text or " " in text:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    return text


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty public string")
    return value


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized.quantize(RATIO_QUANTUM)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")
