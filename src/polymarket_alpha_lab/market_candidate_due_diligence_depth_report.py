"""Read-only due diligence depth report for sanitized market candidates."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
from typing import Any


CONFIG_VERSION = "market-candidate-due-diligence-depth-report-v0"
DECIMAL_QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

MIN_OFFICIAL_SOURCE_COUNT = Decimal("2.000000")
MIN_INDEPENDENT_SOURCE_COUNT = Decimal("3.000000")
MIN_DOMAIN_SPECIALIST_REVIEW_COUNT = Decimal("2.000000")
MISSING_REVIEW_INDEPENDENT_SOURCE_TARGET = Decimal("2.000000")

OFFICIAL_SOURCE_SCORE_WEIGHT = Decimal("0.200000")
INDEPENDENT_SOURCE_SCORE_WEIGHT = Decimal("0.300000")
DOMAIN_SPECIALIST_SCORE_WEIGHT = Decimal("0.200000")
BOOLEAN_GATE_SCORE_WEIGHT = Decimal("0.100000")

DEPTH_BANDS = frozenset(("blocked", "thin", "watch", "deep"))

_REPORT_PAYLOAD_KEYS = frozenset(
    (
        "config_version",
        "official_source_count",
        "independent_source_count",
        "domain_specialist_review_count",
        "resolution_rule_clarity_ready",
        "source_conflict_resolved",
        "cost_model_checked",
        "team_memory_checked",
        "manual_review_notes_redacted",
        "diligence_depth_score",
        "depth_band",
        "missing_review_count",
        "blocked_reason_codes",
        "attention_reason_codes",
        "ready_ratio",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)

_DECIMAL_REPORT_FIELDS = frozenset(
    (
        "official_source_count",
        "independent_source_count",
        "domain_specialist_review_count",
        "diligence_depth_score",
        "missing_review_count",
        "ready_ratio",
    ),
)

_FIELD_DENY_FRAGMENTS = frozenset(
    (
        "candidate_id",
        "raw_candidate",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "database",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "bu" + "y",
        "se" + "ll",
        "rec" + "ommend",
    ),
)

_VALUE_DENY_FRAGMENTS = frozenset(
    (
        "candidate_id",
        "market_id",
        "market_slug",
        "source_ref",
        "source_url",
        "source_text",
        "http://",
        "https://",
        "database",
        "dsn",
        "table:",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "bu" + "y",
        "se" + "ll",
        "rec" + "ommend",
    ),
)


@dataclass(frozen=True)
class MarketCandidateDueDiligenceDepthReport:
    config_version: str
    official_source_count: Decimal
    independent_source_count: Decimal
    domain_specialist_review_count: Decimal
    resolution_rule_clarity_ready: bool
    source_conflict_resolved: bool
    cost_model_checked: bool
    team_memory_checked: bool
    manual_review_notes_redacted: bool
    diligence_depth_score: Decimal
    depth_band: str
    missing_review_count: Decimal
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    ready_ratio: Decimal
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    @property
    def public_payload(self) -> dict[str, Any]:
        return market_candidate_due_diligence_depth_report_payload(self)

    @property
    def digest(self) -> str:
        return self.derived_validation_digest

    def __post_init__(self) -> None:
        _require_hard_flags("report", self)
        _require_public_string("config_version", self.config_version)
        if self.config_version != CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in _DECIMAL_REPORT_FIELDS:
            _require_canonical_decimal(field_name, getattr(self, field_name))
        for field_name in (
            "resolution_rule_clarity_ready",
            "source_conflict_resolved",
            "cost_model_checked",
            "team_memory_checked",
            "manual_review_notes_redacted",
        ):
            if type(getattr(self, field_name)) is not bool:
                raise ValueError(f"{field_name} must be a bool")
        if self.diligence_depth_score < ZERO or self.diligence_depth_score > ONE:
            raise ValueError("diligence_depth_score must be between 0.000000 and 1.000000")
        if self.ready_ratio < ZERO or self.ready_ratio > ONE:
            raise ValueError("ready_ratio must be between 0.000000 and 1.000000")
        _require_member("depth_band", self.depth_band, DEPTH_BANDS)
        _require_reason_codes("blocked_reason_codes", self.blocked_reason_codes)
        _require_reason_codes("attention_reason_codes", self.attention_reason_codes)
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _reject_unsafe_public_surface("report", self)
        if self.derived_validation_digest != _report_derived_validation_digest(self):
            raise ValueError("derived_validation_digest must match report values")


def build_market_candidate_due_diligence_depth_report(
    *,
    official_source_count: Decimal,
    independent_source_count: Decimal,
    domain_specialist_review_count: Decimal,
    resolution_rule_clarity_ready: bool,
    source_conflict_resolved: bool,
    cost_model_checked: bool,
    team_memory_checked: bool,
    manual_review_notes_redacted: bool,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketCandidateDueDiligenceDepthReport:
    values = {
        "paper_only": paper_only,
        "report_only": report_only,
        "readonly": readonly,
    }
    _require_hard_flags("builder", _DictFlags(values))

    official_count = _require_canonical_decimal(
        "official_source_count",
        official_source_count,
    )
    independent_count = _require_canonical_decimal(
        "independent_source_count",
        independent_source_count,
    )
    specialist_count = _require_canonical_decimal(
        "domain_specialist_review_count",
        domain_specialist_review_count,
    )
    for field_name, field_value in (
        ("resolution_rule_clarity_ready", resolution_rule_clarity_ready),
        ("source_conflict_resolved", source_conflict_resolved),
        ("cost_model_checked", cost_model_checked),
        ("team_memory_checked", team_memory_checked),
        ("manual_review_notes_redacted", manual_review_notes_redacted),
    ):
        if type(field_value) is not bool:
            raise ValueError(f"{field_name} must be a bool")

    blocked_reason_codes = _blocked_reason_codes(
        resolution_rule_clarity_ready=resolution_rule_clarity_ready,
        source_conflict_resolved=source_conflict_resolved,
        manual_review_notes_redacted=manual_review_notes_redacted,
    )
    attention_reason_codes = _attention_reason_codes(
        official_source_count=official_count,
        independent_source_count=independent_count,
        domain_specialist_review_count=specialist_count,
        cost_model_checked=cost_model_checked,
        team_memory_checked=team_memory_checked,
        has_blocked_reasons=bool(blocked_reason_codes),
    )
    ready_ratio = _readiness_score(
        official_source_count=official_count,
        independent_source_count=independent_count,
        domain_specialist_review_count=specialist_count,
        resolution_rule_clarity_ready=resolution_rule_clarity_ready,
        source_conflict_resolved=source_conflict_resolved,
        manual_review_notes_redacted=manual_review_notes_redacted,
    )
    missing_review_count = _missing_review_count(
        official_source_count=official_count,
        independent_source_count=independent_count,
        domain_specialist_review_count=specialist_count,
        resolution_rule_clarity_ready=resolution_rule_clarity_ready,
        source_conflict_resolved=source_conflict_resolved,
        manual_review_notes_redacted=manual_review_notes_redacted,
    )
    diligence_depth_score = ready_ratio
    depth_band = _depth_band(
        diligence_depth_score,
        blocked_reason_codes=blocked_reason_codes,
        attention_reason_codes=attention_reason_codes,
    )

    report_values = {
        "config_version": CONFIG_VERSION,
        "official_source_count": official_count,
        "independent_source_count": independent_count,
        "domain_specialist_review_count": specialist_count,
        "resolution_rule_clarity_ready": resolution_rule_clarity_ready,
        "source_conflict_resolved": source_conflict_resolved,
        "cost_model_checked": cost_model_checked,
        "team_memory_checked": team_memory_checked,
        "manual_review_notes_redacted": manual_review_notes_redacted,
        "diligence_depth_score": diligence_depth_score,
        "depth_band": depth_band,
        "missing_review_count": missing_review_count,
        "blocked_reason_codes": blocked_reason_codes,
        "attention_reason_codes": attention_reason_codes,
        "ready_ratio": ready_ratio,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    digest = _digest_payload(_json_ready(report_values))
    return MarketCandidateDueDiligenceDepthReport(
        **report_values,
        derived_validation_digest=digest,
    )


def market_candidate_due_diligence_depth_report_payload(
    report: MarketCandidateDueDiligenceDepthReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is MarketCandidateDueDiligenceDepthReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_surface("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_surface("payload", report)
        _reject_public_numerics(report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a MarketCandidateDueDiligenceDepthReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload(payload)
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_surface("payload", payload)
    return payload


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


def _blocked_reason_codes(
    *,
    resolution_rule_clarity_ready: bool,
    source_conflict_resolved: bool,
    manual_review_notes_redacted: bool,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if not resolution_rule_clarity_ready:
        reason_codes.append("resolution_rule_clarity_not_ready")
    if not source_conflict_resolved:
        reason_codes.append("source_conflict_unresolved")
    if not manual_review_notes_redacted:
        reason_codes.append("manual_review_notes_not_redacted")
    return tuple(reason_codes)


def _attention_reason_codes(
    *,
    official_source_count: Decimal,
    independent_source_count: Decimal,
    domain_specialist_review_count: Decimal,
    cost_model_checked: bool,
    team_memory_checked: bool,
    has_blocked_reasons: bool,
) -> tuple[str, ...]:
    if has_blocked_reasons:
        return ()
    reason_codes: list[str] = []
    if official_source_count < MIN_OFFICIAL_SOURCE_COUNT:
        reason_codes.append("official_source_depth_below_target")
    if independent_source_count < MIN_INDEPENDENT_SOURCE_COUNT:
        reason_codes.append("independent_source_depth_below_target")
    if domain_specialist_review_count < MIN_DOMAIN_SPECIALIST_REVIEW_COUNT:
        reason_codes.append("domain_specialist_review_missing")
    if not cost_model_checked:
        reason_codes.append("cost_model_unchecked")
    if not team_memory_checked:
        reason_codes.append("team_memory_unchecked")
    if not reason_codes:
        reason_codes.append("diligence_depth_ready")
    return tuple(reason_codes)


def _depth_band(
    diligence_depth_score: Decimal,
    *,
    blocked_reason_codes: tuple[str, ...],
    attention_reason_codes: tuple[str, ...],
) -> str:
    if blocked_reason_codes:
        return "blocked"
    if diligence_depth_score >= Decimal("0.900000") and attention_reason_codes == (
        "diligence_depth_ready",
    ):
        return "deep"
    if diligence_depth_score >= Decimal("0.500000"):
        return "watch"
    return "thin"


def _readiness_score(
    *,
    official_source_count: Decimal,
    independent_source_count: Decimal,
    domain_specialist_review_count: Decimal,
    resolution_rule_clarity_ready: bool,
    source_conflict_resolved: bool,
    manual_review_notes_redacted: bool,
) -> Decimal:
    score = (
        _coverage_ratio(official_source_count, MIN_OFFICIAL_SOURCE_COUNT)
        * OFFICIAL_SOURCE_SCORE_WEIGHT
        + _coverage_ratio(independent_source_count, MIN_INDEPENDENT_SOURCE_COUNT)
        * INDEPENDENT_SOURCE_SCORE_WEIGHT
        + _coverage_ratio(
            domain_specialist_review_count,
            MIN_DOMAIN_SPECIALIST_REVIEW_COUNT,
        )
        * DOMAIN_SPECIALIST_SCORE_WEIGHT
        + _bool_score(resolution_rule_clarity_ready)
        + _bool_score(source_conflict_resolved)
        + _bool_score(manual_review_notes_redacted)
    )
    return _quantize_decimal(min(score, ONE))


def _coverage_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    return _quantize_decimal(min(numerator, denominator) / denominator)


def _bool_score(value: bool) -> Decimal:
    return BOOLEAN_GATE_SCORE_WEIGHT if value else ZERO


def _missing_review_count(
    *,
    official_source_count: Decimal,
    independent_source_count: Decimal,
    domain_specialist_review_count: Decimal,
    resolution_rule_clarity_ready: bool,
    source_conflict_resolved: bool,
    manual_review_notes_redacted: bool,
) -> Decimal:
    missing_count = (
        max(MIN_OFFICIAL_SOURCE_COUNT - official_source_count, ZERO)
        + max(
            MISSING_REVIEW_INDEPENDENT_SOURCE_TARGET - independent_source_count,
            ZERO,
        )
        + max(MIN_DOMAIN_SPECIALIST_REVIEW_COUNT - domain_specialist_review_count, ZERO)
        + (ZERO if resolution_rule_clarity_ready else ONE)
        + (ZERO if source_conflict_resolved else ONE)
        + (ZERO if manual_review_notes_redacted else ONE)
    )
    return _quantize_decimal(missing_count)


def _quantize_decimal(value: Decimal) -> Decimal:
    return value.quantize(DECIMAL_QUANT, rounding=ROUND_HALF_UP)


def _require_canonical_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must use six decimal places")
    if value < ZERO:
        raise ValueError(f"{field_name} must be non-negative")
    return value


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    for item in value:
        _require_public_string(field_name, item)
    if tuple(dict.fromkeys(value)) != value:
        raise ValueError(f"{field_name} must be unique")
    return value


def _require_member(field_name: str, value: object, allowed_values: frozenset[str]) -> str:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a supported value")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, Decimal):
        raise ValueError("JSON Decimal value must be a Decimal")
    if isinstance(value, float) or type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) in (str, bool):
        return value
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _validate_public_payload(payload: dict[str, Any]) -> None:
    _reject_unknown_keys("payload", payload, _REPORT_PAYLOAD_KEYS)
    _require_public_string("config_version", payload["config_version"])
    if payload["config_version"] != CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")
    for field_name in _DECIMAL_REPORT_FIELDS:
        _require_decimal_string(field_name, payload[field_name])
    for field_name in (
        "resolution_rule_clarity_ready",
        "source_conflict_resolved",
        "cost_model_checked",
        "team_memory_checked",
        "manual_review_notes_redacted",
        "paper_only",
        "report_only",
        "readonly",
    ):
        if payload[field_name] is not True and field_name in (
            "paper_only",
            "report_only",
            "readonly",
        ):
            raise ValueError(f"{field_name} must be True")
        if field_name not in ("paper_only", "report_only", "readonly") and type(
            payload[field_name],
        ) is not bool:
            raise ValueError(f"{field_name} must be a bool")
    _require_member("depth_band", payload["depth_band"], DEPTH_BANDS)
    _validate_public_string_list(
        "blocked_reason_codes",
        payload["blocked_reason_codes"],
    )
    _validate_public_string_list(
        "attention_reason_codes",
        payload["attention_reason_codes"],
    )
    _require_digest("derived_validation_digest", payload["derived_validation_digest"])
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    if payload["derived_validation_digest"] != _digest_payload(unsigned_payload):
        raise ValueError("derived_validation_digest must match payload values")


def _validate_public_string_list(field_name: str, value: object) -> None:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    for item in value:
        _require_public_string(field_name, item)
    if list(dict.fromkeys(value)) != value:
        raise ValueError(f"{field_name} must be unique")


def _require_decimal_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal-derived string")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:  # pragma: no cover
        raise ValueError(f"{field_name} must be a Decimal-derived string") from exc
    if not decimal_value.is_finite() or decimal_value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must be a six-place Decimal-derived string")
    return decimal_value


def _reject_unknown_keys(
    label: str,
    payload: dict[str, Any],
    allowed_keys: frozenset[str],
) -> None:
    for key in payload:
        if key not in allowed_keys:
            raise ValueError(f"unknown public field in {label}: {key}")


def _reject_public_numerics(value: object) -> None:
    if isinstance(value, Decimal):
        raise ValueError("public payload values must be Decimal-derived strings")
    if isinstance(value, float) or type(value) is int:
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if type(value) is dict:
        for item in value.values():
            _reject_public_numerics(item)
        return
    if type(value) is list:
        for item in value:
            _reject_public_numerics(item)


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_surface(label, asdict(value))
        return
    if type(value) is str:
        _reject_unsafe_public_string(label, value)
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            normalized_key = key.lower()
            if any(fragment in normalized_key for fragment in _FIELD_DENY_FRAGMENTS):
                raise ValueError(f"unsafe public field in {label}: {key}")
            _reject_unsafe_public_surface(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_surface(label, item)


def _reject_unsafe_public_string(label: str, value: str) -> None:
    normalized_value = value.lower()
    if any(fragment in normalized_value for fragment in _VALUE_DENY_FRAGMENTS):
        raise ValueError(f"unsafe public value in {label}")


def _digest_payload(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return sha256(encoded).hexdigest()


def _report_derived_validation_digest(
    report: MarketCandidateDueDiligenceDepthReport,
) -> str:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return _digest_payload(payload)


__all__ = (
    "CONFIG_VERSION",
    "DECIMAL_QUANT",
    "DEPTH_BANDS",
    "MarketCandidateDueDiligenceDepthReport",
    "build_market_candidate_due_diligence_depth_report",
    "market_candidate_due_diligence_depth_report_payload",
)
