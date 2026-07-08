"""Pure report-only router for human cross-validation of research sources.

The module accepts caller-supplied source review candidates, derives safe human
team routing, and returns deterministic public payloads suitable for local
storage by the caller. It performs no I/O and exposes no market/source raw text.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any


ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
VALUE_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

DEFAULT_CONFIG_VERSION = "research-source-cross-validation-router-v0"

PUBLIC_STATUSES = ("pass", "watch", "block")
ASSIGNED_TEAMS = ("evidence_operations", "rules_research", "legal_research")

PASS_REASON = "cross_validation_pass"
WATCH_REASON = "cross_validation_watch"
BLOCK_REASON = "cross_validation_block"
NEEDS_INDEPENDENT_SOURCES_REASON = "needs_independent_sources"
NEEDS_FAMILY_DIVERSITY_REASON = "needs_evidence_family_diversity"
STALE_SOURCE_REASON = "stale_source_review"
MISSING_PRIMARY_REASON = "missing_primary_source"
POLICY_UNCERTAINTY_REASON = "policy_uncertainty_review"
RULES_REVIEW_REASON = "rules_research_review"
LEGAL_REVIEW_REASON = "legal_research_review"
CONTRADICTION_REASON = "contradiction_review_required"
SENSITIVE_SOURCE_REASON = "sensitive_source_manual_review"
RESOLUTION_RISK_REASON = "resolution_risk_review"

REASON_CODE_PRIORITY = (
    PASS_REASON,
    CONTRADICTION_REASON,
    BLOCK_REASON,
    WATCH_REASON,
    MISSING_PRIMARY_REASON,
    NEEDS_FAMILY_DIVERSITY_REASON,
    NEEDS_INDEPENDENT_SOURCES_REASON,
    POLICY_UNCERTAINTY_REASON,
    RESOLUTION_RISK_REASON,
    SENSITIVE_SOURCE_REASON,
    STALE_SOURCE_REASON,
    RULES_REVIEW_REASON,
    LEGAL_REVIEW_REASON,
)
REASON_CODES = frozenset(REASON_CODE_PRIORITY)

UNSAFE_PUBLIC_FRAGMENTS = (
    "raw_candidate",
    "candidate_id",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "source_ref",
    "source_url",
    "source_text",
    "source_refs",
    "source snippet",
    "http://",
    "https://",
    "dsn",
    "table",
    "token",
    "secret",
    "credential",
    "wallet",
    "order",
    "trade",
    "trading",
    "position",
    "buy",
    "sell",
    "recommend",
    "live",
    "auth",
)


@dataclass(frozen=True)
class ResearchSourceCrossValidationConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    min_independent_source_count: Decimal = Decimal("2")
    min_evidence_family_count: Decimal = Decimal("2")
    watch_policy_uncertainty_score: Decimal = Decimal("0.600000")
    block_policy_uncertainty_score: Decimal = Decimal("0.900000")
    block_resolution_risk_score: Decimal = Decimal("0.850000")
    high_urgency_score: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in ("min_independent_source_count", "min_evidence_family_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_policy_uncertainty_score",
            "block_policy_uncertainty_score",
            "block_resolution_risk_score",
            "high_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.block_policy_uncertainty_score <= self.watch_policy_uncertainty_score:
            raise ValueError(
                "block_policy_uncertainty_score must exceed watch_policy_uncertainty_score",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", _payload_value(self))


@dataclass(frozen=True)
class ResearchSourceCrossValidationCandidate:
    raw_candidate_id: str
    raw_market_id: str
    raw_market_slug: str
    raw_market_question: str
    raw_source_refs: tuple[str, ...]
    submitted_at: datetime
    evidence_family_count: Decimal
    independent_source_count: Decimal
    stale_source_count: Decimal = ZERO
    contradiction_count: Decimal = ZERO
    sensitive_source_count: Decimal = ZERO
    policy_uncertainty_score: Decimal = ZERO
    resolution_risk_score: Decimal = ZERO
    urgency_score: Decimal = ZERO
    has_primary_source: bool = True
    needs_legal_review: bool = False
    needs_rules_review: bool = False
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "raw_candidate_id",
            "raw_market_id",
            "raw_market_slug",
            "raw_market_question",
        ):
            _require_private_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "raw_source_refs",
            _normalize_private_strings("raw_source_refs", self.raw_source_refs),
        )
        object.__setattr__(self, "submitted_at", _as_utc("submitted_at", self.submitted_at))
        for field_name in (
            "evidence_family_count",
            "independent_source_count",
            "stale_source_count",
            "contradiction_count",
            "sensitive_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "policy_uncertainty_score",
            "resolution_risk_score",
            "urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "has_primary_source",
            "needs_legal_review",
            "needs_rules_review",
        ):
            if type(getattr(self, field_name)) is not bool:
                raise ValueError(f"{field_name} must be a bool")
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class ResearchSourceCrossValidationRoute:
    route_key: str
    assigned_team: str
    status: str
    reason_codes: tuple[str, ...]
    submitted_age_seconds: Decimal
    evidence_family_count: Decimal
    independent_source_count: Decimal
    stale_source_count: Decimal
    contradiction_count: Decimal
    sensitive_source_count: Decimal
    policy_uncertainty_score: Decimal
    resolution_risk_score: Decimal
    urgency_score: Decimal
    public_note: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("route_key", self.route_key)
        _require_member("assigned_team", self.assigned_team, ASSIGNED_TEAMS)
        _require_member("status", self.status, PUBLIC_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        for field_name in (
            "submitted_age_seconds",
            "evidence_family_count",
            "independent_source_count",
            "stale_source_count",
            "contradiction_count",
            "sensitive_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "policy_uncertainty_score",
            "resolution_risk_score",
            "urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_public_string("public_note", self.public_note)
        if self.status != _status_from_reason_codes(self.reason_codes):
            raise ValueError("status must match reason_codes")
        _require_hard_flags("route", self)
        _reject_unsafe_public_payload("route", _payload_value(self))


@dataclass(frozen=True)
class ResearchSourceCrossValidationReport:
    generated_at: datetime
    config_version: str
    task_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    routes: tuple[ResearchSourceCrossValidationRoute, ...]
    public_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in ("task_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, PUBLIC_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "routes", _normalize_routes(self.routes))
        _require_hard_flags("report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("report", _payload_value(self))
        _set_or_validate_public_digest(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_source_cross_validation_public_payload(self)


def build_research_source_cross_validation_report(
    candidates: Iterable[ResearchSourceCrossValidationCandidate],
    *,
    config: ResearchSourceCrossValidationConfig,
    generated_at: datetime,
) -> ResearchSourceCrossValidationReport:
    if type(config) is not ResearchSourceCrossValidationConfig:
        raise ValueError("config must be a ResearchSourceCrossValidationConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_candidates = _normalize_candidates(candidates, generated_at=generated_at_utc)
    routes = tuple(
        _route_for_candidate(
            candidate,
            route_key=f"route-{index:03d}",
            config=config,
            generated_at=generated_at_utc,
        )
        for index, candidate in enumerate(normalized_candidates, start=1)
    )
    reason_codes = _report_reason_codes(routes)
    return ResearchSourceCrossValidationReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        task_count=_count(len(routes)),
        pass_count=_count(sum(1 for route in routes if route.status == "pass")),
        watch_count=_count(sum(1 for route in routes if route.status == "watch")),
        block_count=_count(sum(1 for route in routes if route.status == "block")),
        status=_report_status(reason_codes),
        reason_codes=reason_codes,
        routes=routes,
    )


def research_source_cross_validation_public_payload(
    value: ResearchSourceCrossValidationReport | dict[str, Any],
) -> dict[str, Any]:
    if type(value) is ResearchSourceCrossValidationReport:
        _validate_report(value)
        _validate_public_digest(value)
        payload = _payload_value(value)
    elif type(value) is dict:
        payload = value
    else:
        raise ValueError("value must be a ResearchSourceCrossValidationReport or dict")
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    validate_research_source_cross_validation_public_payload(payload)
    return dict(payload)


def research_source_cross_validation_supabase_summary(
    value: ResearchSourceCrossValidationReport,
) -> dict[str, Any]:
    payload = research_source_cross_validation_public_payload(value)
    return {
        "generated_at": payload["generated_at"],
        "config_version": payload["config_version"],
        "status": payload["status"],
        "task_count": payload["task_count"],
        "pass_count": payload["pass_count"],
        "watch_count": payload["watch_count"],
        "block_count": payload["block_count"],
        "reason_codes": payload["reason_codes"],
        "routes": payload["routes"],
        "public_digest": payload["public_digest"],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def validate_research_source_cross_validation_public_payload(payload: dict[str, Any]) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("public payload", payload)
    _require_public_payload_flags(payload)
    status = _payload_required_string(payload, "status")
    _require_member("status", status, PUBLIC_STATUSES)
    public_digest = _payload_required_string(payload, "public_digest")
    _require_sha256_digest("public_digest", public_digest)
    if public_digest != _public_digest(payload):
        raise ValueError("public_digest must match public payload")
    return True


def _route_for_candidate(
    candidate: ResearchSourceCrossValidationCandidate,
    *,
    route_key: str,
    config: ResearchSourceCrossValidationConfig,
    generated_at: datetime,
) -> ResearchSourceCrossValidationRoute:
    reason_codes = _route_reason_codes(candidate, config=config)
    return ResearchSourceCrossValidationRoute(
        route_key=route_key,
        assigned_team=_assigned_team(candidate, reason_codes),
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
        submitted_age_seconds=_seconds_between(candidate.submitted_at, generated_at),
        evidence_family_count=candidate.evidence_family_count,
        independent_source_count=candidate.independent_source_count,
        stale_source_count=candidate.stale_source_count,
        contradiction_count=candidate.contradiction_count,
        sensitive_source_count=candidate.sensitive_source_count,
        policy_uncertainty_score=candidate.policy_uncertainty_score,
        resolution_risk_score=candidate.resolution_risk_score,
        urgency_score=candidate.urgency_score,
        public_note=_public_note(reason_codes),
    )


def _route_reason_codes(
    candidate: ResearchSourceCrossValidationCandidate,
    *,
    config: ResearchSourceCrossValidationConfig,
) -> tuple[str, ...]:
    block_reasons: list[str] = []
    watch_reasons: list[str] = []
    if candidate.contradiction_count > ZERO:
        block_reasons.append(CONTRADICTION_REASON)
    if candidate.sensitive_source_count > ZERO:
        block_reasons.append(SENSITIVE_SOURCE_REASON)
    if candidate.resolution_risk_score >= config.block_resolution_risk_score:
        block_reasons.append(RESOLUTION_RISK_REASON)
    if candidate.policy_uncertainty_score >= config.block_policy_uncertainty_score:
        block_reasons.append(POLICY_UNCERTAINTY_REASON)
    if candidate.needs_legal_review:
        block_reasons.append(LEGAL_REVIEW_REASON)
    if block_reasons:
        return _normalize_reason_codes("reason_codes", tuple(block_reasons))

    if candidate.independent_source_count < config.min_independent_source_count:
        watch_reasons.append(NEEDS_INDEPENDENT_SOURCES_REASON)
    if candidate.evidence_family_count < config.min_evidence_family_count:
        watch_reasons.append(NEEDS_FAMILY_DIVERSITY_REASON)
    if candidate.stale_source_count > ZERO:
        watch_reasons.append(STALE_SOURCE_REASON)
    if not candidate.has_primary_source:
        watch_reasons.append(MISSING_PRIMARY_REASON)
    if candidate.policy_uncertainty_score >= config.watch_policy_uncertainty_score:
        watch_reasons.append(POLICY_UNCERTAINTY_REASON)
    if candidate.needs_rules_review:
        watch_reasons.append(RULES_REVIEW_REASON)
    if watch_reasons:
        return _normalize_reason_codes("reason_codes", tuple(watch_reasons))
    return (PASS_REASON,)


def _assigned_team(
    candidate: ResearchSourceCrossValidationCandidate,
    reason_codes: tuple[str, ...],
) -> str:
    if candidate.needs_legal_review or any(
        reason in reason_codes
        for reason in (LEGAL_REVIEW_REASON, SENSITIVE_SOURCE_REASON, RESOLUTION_RISK_REASON)
    ):
        return "legal_research"
    if candidate.needs_rules_review or RULES_REVIEW_REASON in reason_codes:
        return "rules_research"
    return "evidence_operations"


def _public_note(reason_codes: tuple[str, ...]) -> str:
    status = _status_from_reason_codes(reason_codes)
    if status == "pass":
        return "paper_review_ready"
    if status == "watch":
        return "human_cross_validation_watch"
    return "human_cross_validation_required"


def _normalize_candidates(
    value: Iterable[ResearchSourceCrossValidationCandidate],
    *,
    generated_at: datetime,
) -> tuple[ResearchSourceCrossValidationCandidate, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        candidates = tuple(value)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    seen_ids: set[str] = set()
    for candidate in candidates:
        if type(candidate) is not ResearchSourceCrossValidationCandidate:
            raise ValueError(
                "candidates must contain ResearchSourceCrossValidationCandidate values",
            )
        _require_hard_flags("candidate", candidate)
        if candidate.raw_candidate_id in seen_ids:
            raise ValueError("raw_candidate_id values must be unique")
        seen_ids.add(candidate.raw_candidate_id)
        if candidate.submitted_at > generated_at:
            raise ValueError("submitted_at must not be after generated_at")
    return tuple(sorted(candidates, key=_candidate_sort_key))


def _normalize_routes(
    value: Iterable[ResearchSourceCrossValidationRoute],
) -> tuple[ResearchSourceCrossValidationRoute, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("routes must be an iterable")
    try:
        routes = tuple(value)
    except TypeError as exc:
        raise ValueError("routes must be an iterable") from exc
    seen_keys: set[str] = set()
    for route in routes:
        if type(route) is not ResearchSourceCrossValidationRoute:
            raise ValueError(
                "routes must contain ResearchSourceCrossValidationRoute values",
            )
        _require_hard_flags("route", route)
        if route.route_key in seen_keys:
            raise ValueError("route_key values must be unique")
        seen_keys.add(route.route_key)
    sorted_routes = tuple(sorted(routes, key=lambda item: item.route_key))
    if routes != sorted_routes:
        raise ValueError("routes must be sorted by route_key")
    return routes


def _validate_report(report: ResearchSourceCrossValidationReport) -> None:
    routes = report.routes
    if report.task_count != _count(len(routes)):
        raise ValueError("task_count must match routes")
    if report.pass_count != _count(sum(1 for route in routes if route.status == "pass")):
        raise ValueError("pass_count must match routes")
    if report.watch_count != _count(sum(1 for route in routes if route.status == "watch")):
        raise ValueError("watch_count must match routes")
    if report.block_count != _count(sum(1 for route in routes if route.status == "block")):
        raise ValueError("block_count must match routes")
    if report.reason_codes != _report_reason_codes(routes):
        raise ValueError("reason_codes must match routes")
    if report.status != _report_status(report.reason_codes):
        raise ValueError("status must match reason_codes")


def _report_reason_codes(
    routes: tuple[ResearchSourceCrossValidationRoute, ...],
) -> tuple[str, ...]:
    if not routes:
        return (BLOCK_REASON,)
    reasons: set[str] = set()
    for route in routes:
        if route.status == "watch":
            reasons.add(WATCH_REASON)
        if route.status == "block":
            reasons.add(BLOCK_REASON)
        if route.status != "pass":
            for reason_code in route.reason_codes:
                reasons.add(reason_code)
    if not reasons:
        return (PASS_REASON,)
    return tuple(sorted(reasons, key=REASON_CODE_PRIORITY.index))


def _report_status(reason_codes: tuple[str, ...]) -> str:
    if BLOCK_REASON in reason_codes:
        return "block"
    if WATCH_REASON in reason_codes:
        return "watch"
    return "pass"


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (PASS_REASON,):
        return "pass"
    if any(
        reason in reason_codes
        for reason in (
            BLOCK_REASON,
            LEGAL_REVIEW_REASON,
            CONTRADICTION_REASON,
            SENSITIVE_SOURCE_REASON,
            RESOLUTION_RISK_REASON,
        )
    ):
        return "block"
    return "watch"


def _set_or_validate_public_digest(report: ResearchSourceCrossValidationReport) -> None:
    current = report.public_digest
    expected = _public_digest(report)
    if current == "":
        object.__setattr__(report, "public_digest", expected)
        return
    _require_sha256_digest("public_digest", current)
    if current != expected:
        raise ValueError("public_digest must match report fields")


def _validate_public_digest(report: ResearchSourceCrossValidationReport) -> None:
    current = _require_sha256_digest("public_digest", report.public_digest)
    if current != _public_digest(report):
        raise ValueError("public_digest must match report fields")


def _public_digest(value: object) -> str:
    payload = _without_public_digest(_payload_value(value))
    encoded = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _without_public_digest(value: object) -> object:
    if type(value) is dict:
        return {
            key: _without_public_digest(item)
            for key, item in value.items()
            if key != "public_digest"
        }
    if type(value) is list:
        return [_without_public_digest(item) for item in value]
    return value


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload values must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
            if not field.name.startswith("raw_")
        }
    if type(value) is tuple or type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    return value


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if value is None or type(value) is bool:
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"unsafe public payload value in {path or label}")
        return
    if isinstance(value, (Decimal, int, float)):
        raise ValueError(f"{path or label} must use Decimal strings, not numeric values")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public payload key in {label}: {key}")
            item_path = key if not path else f"{path}.{key}"
            if key in ("paper_only", "report_only", "readonly") and item is not True:
                raise ValueError(f"{item_path} must be True")
            if key == "status":
                _require_member("status", item, PUBLIC_STATUSES)
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) is list:
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError(f"{path or label} is not public JSON serializable")


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    return _normalize_nonnegative_decimal(
        "submitted_age_seconds",
        Decimal(str((end - start).total_seconds())),
    )


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(VALUE_QUANTUM)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return normalized


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal count")
    normalized = value.quantize(COUNT_QUANTUM)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count source must be a nonnegative int")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_reason_codes(field_name: str, value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of reason codes")
    try:
        codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of reason codes") from exc
    if not codes:
        raise ValueError(f"{field_name} must not be empty")
    for code in codes:
        if type(code) is not str or not code:
            raise ValueError(f"{field_name} must contain non-empty strings")
        if code not in REASON_CODES:
            raise ValueError(f"{field_name} contains an unknown reason code")
    active_codes = [code for code in codes if code != PASS_REASON]
    if PASS_REASON in codes and active_codes:
        raise ValueError(f"{field_name} pass reason must stand alone")
    return tuple(sorted(set(codes), key=REASON_CODE_PRIORITY.index))


def _require_member(field_name: str, value: object, members: tuple[str, ...]) -> None:
    if type(value) is not str or value not in members:
        raise ValueError(f"{field_name} must be one of {members}")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip() or "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be a canonical string")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} has unsafe public content")


def _require_private_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip() or "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be a canonical string")


def _normalize_private_strings(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    for item in value:
        _require_private_string(field_name, item)
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _candidate_sort_key(
    candidate: ResearchSourceCrossValidationCandidate,
) -> tuple[str, str, str]:
    return (
        candidate.raw_candidate_id,
        candidate.raw_market_id,
        candidate.raw_market_slug,
    )


__all__ = (
    "ResearchSourceCrossValidationCandidate",
    "ResearchSourceCrossValidationConfig",
    "ResearchSourceCrossValidationReport",
    "ResearchSourceCrossValidationRoute",
    "build_research_source_cross_validation_report",
    "research_source_cross_validation_public_payload",
    "research_source_cross_validation_supabase_summary",
    "validate_research_source_cross_validation_public_payload",
)
