"""Pure public-safe research evidence-chain integrity audit report."""

from __future__ import annotations

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

DEFAULT_CONFIG_VERSION = "research-evidence-chain-integrity-audit-report-v1"

AUDIT_STATUSES = ("pass", "watch", "block")

PASS_REASON = "evidence_chain_integrity_pass"
INSUFFICIENT_AGGREGATE_REASON = "insufficient_aggregate_evidence"
FRESHNESS_BLOCK_REASON = "freshness_block"
FRESHNESS_WATCH_REASON = "freshness_watch"
CONTRADICTION_BLOCK_REASON = "contradiction_block"
CONTRADICTION_WATCH_REASON = "contradiction_watch"
INSUFFICIENT_SOURCE_CLASS_REASON = "insufficient_source_class_diversity"
RULE_CLARITY_BLOCK_REASON = "rule_clarity_block"
RULE_CLARITY_WATCH_REASON = "rule_clarity_watch"
CUSTODY_COMPLETENESS_BLOCK_REASON = "custody_completeness_block"
CUSTODY_COMPLETENESS_WATCH_REASON = "custody_completeness_watch"

REASON_CODE_PRIORITY = (
    PASS_REASON,
    INSUFFICIENT_AGGREGATE_REASON,
    FRESHNESS_BLOCK_REASON,
    FRESHNESS_WATCH_REASON,
    CONTRADICTION_BLOCK_REASON,
    CONTRADICTION_WATCH_REASON,
    INSUFFICIENT_SOURCE_CLASS_REASON,
    RULE_CLARITY_BLOCK_REASON,
    RULE_CLARITY_WATCH_REASON,
    CUSTODY_COMPLETENESS_BLOCK_REASON,
    CUSTODY_COMPLETENESS_WATCH_REASON,
)
REASON_CODES = frozenset(REASON_CODE_PRIORITY)

UNSAFE_PUBLIC_FRAGMENTS = (
    "http://",
    "https://",
    "source_url",
    "source text",
    "source_text",
    "raw source",
    "source_ref",
    "source reference",
    "source_reference",
    "candidate_id",
    "candidate identifier",
    "candidate_identifier",
    "candidate_slug",
    "market_id",
    "market identifier",
    "market_identifier",
    "market_slug",
    "wallet",
    "auth",
    "order",
    "trade",
    "private_key",
    "private key",
    "private-key",
    "live",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "recommend",
    "sizing",
    "size allocation",
    "position_size",
    "position",
    "notional",
    "allocation",
)


@dataclass(frozen=True)
class ResearchEvidenceChainIntegrityAuditConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    min_aggregate_evidence_count: Decimal = Decimal("3")
    min_freshness_ratio: Decimal = Decimal("0.900000")
    block_freshness_ratio: Decimal = Decimal("0.500000")
    max_pass_contradiction_count: Decimal = Decimal("0")
    max_watch_contradiction_count: Decimal = Decimal("1")
    min_source_class_count: Decimal = Decimal("2")
    min_rule_clarity_score: Decimal = Decimal("0.800000")
    block_rule_clarity_score: Decimal = Decimal("0.600000")
    min_custody_completeness_score: Decimal = Decimal("0.900000")
    block_custody_completeness_score: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "min_aggregate_evidence_count",
            "max_pass_contradiction_count",
            "max_watch_contradiction_count",
            "min_source_class_count",
        ):
            object.__setattr__(self, field_name, _normalize_count(field_name, getattr(self, field_name)))
        for field_name in (
            "min_freshness_ratio",
            "block_freshness_ratio",
            "min_rule_clarity_score",
            "block_rule_clarity_score",
            "min_custody_completeness_score",
            "block_custody_completeness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.block_freshness_ratio > self.min_freshness_ratio:
            raise ValueError("block_freshness_ratio must be <= min_freshness_ratio")
        if self.max_pass_contradiction_count > self.max_watch_contradiction_count:
            raise ValueError(
                "max_pass_contradiction_count must be <= max_watch_contradiction_count",
            )
        if self.block_rule_clarity_score > self.min_rule_clarity_score:
            raise ValueError("block_rule_clarity_score must be <= min_rule_clarity_score")
        if self.block_custody_completeness_score > self.min_custody_completeness_score:
            raise ValueError(
                "block_custody_completeness_score must be <= min_custody_completeness_score",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", _payload_value(self))


@dataclass(frozen=True)
class ResearchEvidenceChainIntegrityAuditMetrics:
    aggregate_evidence_count: Decimal
    fresh_evidence_count: Decimal
    contradiction_count: Decimal
    source_class_count: Decimal
    rule_clarity_score: Decimal
    custody_completeness_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "aggregate_evidence_count",
            "fresh_evidence_count",
            "contradiction_count",
            "source_class_count",
        ):
            object.__setattr__(self, field_name, _normalize_count(field_name, getattr(self, field_name)))
        for field_name in ("rule_clarity_score", "custody_completeness_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.fresh_evidence_count > self.aggregate_evidence_count:
            raise ValueError("fresh_evidence_count must be <= aggregate_evidence_count")
        _require_hard_flags("metrics", self)
        _reject_unsafe_public_payload("metrics", _payload_value(self))


@dataclass(frozen=True)
class ResearchEvidenceChainIntegrityAuditReport:
    generated_at: datetime
    config_version: str
    aggregate_evidence_count: Decimal
    fresh_evidence_count: Decimal
    freshness_ratio: Decimal
    contradiction_count: Decimal
    source_class_count: Decimal
    rule_clarity_score: Decimal
    custody_completeness_score: Decimal
    min_aggregate_evidence_count: Decimal
    min_freshness_ratio: Decimal
    block_freshness_ratio: Decimal
    max_pass_contradiction_count: Decimal
    max_watch_contradiction_count: Decimal
    min_source_class_count: Decimal
    min_rule_clarity_score: Decimal
    block_rule_clarity_score: Decimal
    min_custody_completeness_score: Decimal
    block_custody_completeness_score: Decimal
    audit_status: str
    audit_next_step: str
    reason_codes: tuple[str, ...]
    payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "aggregate_evidence_count",
            "fresh_evidence_count",
            "contradiction_count",
            "source_class_count",
            "min_aggregate_evidence_count",
            "max_pass_contradiction_count",
            "max_watch_contradiction_count",
            "min_source_class_count",
        ):
            object.__setattr__(self, field_name, _normalize_count(field_name, getattr(self, field_name)))
        for field_name in (
            "freshness_ratio",
            "rule_clarity_score",
            "custody_completeness_score",
            "min_freshness_ratio",
            "block_freshness_ratio",
            "min_rule_clarity_score",
            "block_rule_clarity_score",
            "min_custody_completeness_score",
            "block_custody_completeness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("audit_status", self.audit_status, AUDIT_STATUSES)
        _require_public_string("audit_next_step", self.audit_next_step)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("report", _payload_value(self))
        _set_or_validate_payload_digest(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_evidence_chain_integrity_audit_public_payload(self)


def build_research_evidence_chain_integrity_audit_report(
    metrics: ResearchEvidenceChainIntegrityAuditMetrics,
    *,
    config: ResearchEvidenceChainIntegrityAuditConfig,
    generated_at: datetime,
) -> ResearchEvidenceChainIntegrityAuditReport:
    if type(metrics) is not ResearchEvidenceChainIntegrityAuditMetrics:
        raise ValueError("metrics must be a ResearchEvidenceChainIntegrityAuditMetrics")
    if type(config) is not ResearchEvidenceChainIntegrityAuditConfig:
        raise ValueError("config must be a ResearchEvidenceChainIntegrityAuditConfig")
    _require_hard_flags("metrics", metrics)
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    freshness_ratio = _ratio(metrics.fresh_evidence_count, metrics.aggregate_evidence_count)
    reason_codes = _report_reason_codes(
        aggregate_evidence_count=metrics.aggregate_evidence_count,
        freshness_ratio=freshness_ratio,
        contradiction_count=metrics.contradiction_count,
        source_class_count=metrics.source_class_count,
        rule_clarity_score=metrics.rule_clarity_score,
        custody_completeness_score=metrics.custody_completeness_score,
        min_aggregate_evidence_count=config.min_aggregate_evidence_count,
        min_freshness_ratio=config.min_freshness_ratio,
        block_freshness_ratio=config.block_freshness_ratio,
        max_pass_contradiction_count=config.max_pass_contradiction_count,
        max_watch_contradiction_count=config.max_watch_contradiction_count,
        min_source_class_count=config.min_source_class_count,
        min_rule_clarity_score=config.min_rule_clarity_score,
        block_rule_clarity_score=config.block_rule_clarity_score,
        min_custody_completeness_score=config.min_custody_completeness_score,
        block_custody_completeness_score=config.block_custody_completeness_score,
    )
    audit_status = _audit_status_from_reason_codes(reason_codes)
    return ResearchEvidenceChainIntegrityAuditReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        aggregate_evidence_count=metrics.aggregate_evidence_count,
        fresh_evidence_count=metrics.fresh_evidence_count,
        freshness_ratio=freshness_ratio,
        contradiction_count=metrics.contradiction_count,
        source_class_count=metrics.source_class_count,
        rule_clarity_score=metrics.rule_clarity_score,
        custody_completeness_score=metrics.custody_completeness_score,
        min_aggregate_evidence_count=config.min_aggregate_evidence_count,
        min_freshness_ratio=config.min_freshness_ratio,
        block_freshness_ratio=config.block_freshness_ratio,
        max_pass_contradiction_count=config.max_pass_contradiction_count,
        max_watch_contradiction_count=config.max_watch_contradiction_count,
        min_source_class_count=config.min_source_class_count,
        min_rule_clarity_score=config.min_rule_clarity_score,
        block_rule_clarity_score=config.block_rule_clarity_score,
        min_custody_completeness_score=config.min_custody_completeness_score,
        block_custody_completeness_score=config.block_custody_completeness_score,
        audit_status=audit_status,
        audit_next_step=_audit_next_step(audit_status),
        reason_codes=reason_codes,
    )


def research_evidence_chain_integrity_audit_public_payload(
    value: ResearchEvidenceChainIntegrityAuditReport | dict[str, Any],
) -> dict[str, Any]:
    if type(value) is ResearchEvidenceChainIntegrityAuditReport:
        _validate_report(value)
        _validate_payload_digest(value)
        payload = _payload_value(value)
    elif type(value) is dict:
        payload = value
    else:
        raise ValueError(
            "value must be a ResearchEvidenceChainIntegrityAuditReport or dict",
        )
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    validate_research_evidence_chain_integrity_audit_public_payload(payload)
    return dict(payload)


def validate_research_evidence_chain_integrity_audit_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("public payload", payload)
    _require_public_payload_flags(payload)
    audit_status = _payload_required_string(payload, "audit_status")
    _require_member("audit_status", audit_status, AUDIT_STATUSES)
    audit_next_step = _payload_required_string(payload, "audit_next_step")
    _require_public_string("audit_next_step", audit_next_step)
    reason_codes = _normalize_reason_codes(
        "reason_codes",
        _payload_required_string_list(payload, "reason_codes"),
    )
    if audit_status != _audit_status_from_reason_codes(reason_codes):
        raise ValueError("audit_status must match reason_codes")
    if audit_next_step != _audit_next_step(audit_status):
        raise ValueError("audit_next_step must match audit_status")
    digest_value = _payload_required_string(payload, "payload_digest")
    _require_sha256_digest("payload_digest", digest_value)
    if digest_value != _payload_digest(payload):
        raise ValueError("payload_digest must match public payload")
    return True


def _validate_report(report: ResearchEvidenceChainIntegrityAuditReport) -> None:
    if report.fresh_evidence_count > report.aggregate_evidence_count:
        raise ValueError("fresh_evidence_count must be <= aggregate_evidence_count")
    expected_freshness_ratio = _ratio(
        report.fresh_evidence_count,
        report.aggregate_evidence_count,
    )
    if report.freshness_ratio != expected_freshness_ratio:
        raise ValueError("freshness_ratio must match evidence counts")
    expected_reason_codes = _report_reason_codes(
        aggregate_evidence_count=report.aggregate_evidence_count,
        freshness_ratio=report.freshness_ratio,
        contradiction_count=report.contradiction_count,
        source_class_count=report.source_class_count,
        rule_clarity_score=report.rule_clarity_score,
        custody_completeness_score=report.custody_completeness_score,
        min_aggregate_evidence_count=report.min_aggregate_evidence_count,
        min_freshness_ratio=report.min_freshness_ratio,
        block_freshness_ratio=report.block_freshness_ratio,
        max_pass_contradiction_count=report.max_pass_contradiction_count,
        max_watch_contradiction_count=report.max_watch_contradiction_count,
        min_source_class_count=report.min_source_class_count,
        min_rule_clarity_score=report.min_rule_clarity_score,
        block_rule_clarity_score=report.block_rule_clarity_score,
        min_custody_completeness_score=report.min_custody_completeness_score,
        block_custody_completeness_score=report.block_custody_completeness_score,
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match audit metrics")
    if report.audit_status != _audit_status_from_reason_codes(report.reason_codes):
        raise ValueError("audit_status must match reason_codes")
    if report.audit_next_step != _audit_next_step(report.audit_status):
        raise ValueError("audit_next_step must match audit_status")


def _report_reason_codes(
    *,
    aggregate_evidence_count: Decimal,
    freshness_ratio: Decimal,
    contradiction_count: Decimal,
    source_class_count: Decimal,
    rule_clarity_score: Decimal,
    custody_completeness_score: Decimal,
    min_aggregate_evidence_count: Decimal,
    min_freshness_ratio: Decimal,
    block_freshness_ratio: Decimal,
    max_pass_contradiction_count: Decimal,
    max_watch_contradiction_count: Decimal,
    min_source_class_count: Decimal,
    min_rule_clarity_score: Decimal,
    block_rule_clarity_score: Decimal,
    min_custody_completeness_score: Decimal,
    block_custody_completeness_score: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if aggregate_evidence_count < min_aggregate_evidence_count:
        reasons.append(INSUFFICIENT_AGGREGATE_REASON)
    if freshness_ratio < block_freshness_ratio:
        reasons.append(FRESHNESS_BLOCK_REASON)
    elif freshness_ratio < min_freshness_ratio:
        reasons.append(FRESHNESS_WATCH_REASON)
    if contradiction_count > max_watch_contradiction_count:
        reasons.append(CONTRADICTION_BLOCK_REASON)
    elif contradiction_count > max_pass_contradiction_count:
        reasons.append(CONTRADICTION_WATCH_REASON)
    if source_class_count < min_source_class_count:
        reasons.append(INSUFFICIENT_SOURCE_CLASS_REASON)
    if rule_clarity_score < block_rule_clarity_score:
        reasons.append(RULE_CLARITY_BLOCK_REASON)
    elif rule_clarity_score < min_rule_clarity_score:
        reasons.append(RULE_CLARITY_WATCH_REASON)
    if custody_completeness_score < block_custody_completeness_score:
        reasons.append(CUSTODY_COMPLETENESS_BLOCK_REASON)
    elif custody_completeness_score < min_custody_completeness_score:
        reasons.append(CUSTODY_COMPLETENESS_WATCH_REASON)
    if not reasons:
        return (PASS_REASON,)
    return _normalize_reason_codes("reason_codes", tuple(reasons))


def _audit_status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (PASS_REASON,):
        return "pass"
    if any(_is_block_reason(reason_code) for reason_code in reason_codes):
        return "block"
    return "watch"


def _is_block_reason(reason_code: str) -> bool:
    return reason_code in (
        INSUFFICIENT_AGGREGATE_REASON,
        FRESHNESS_BLOCK_REASON,
        CONTRADICTION_BLOCK_REASON,
        INSUFFICIENT_SOURCE_CLASS_REASON,
        RULE_CLARITY_BLOCK_REASON,
        CUSTODY_COMPLETENESS_BLOCK_REASON,
    )


def _audit_next_step(audit_status: str) -> str:
    if audit_status == "pass":
        return "continue_public_research_review"
    if audit_status == "watch":
        return "refresh_public_evidence_chain"
    return "repair_public_evidence_chain"


def _set_or_validate_payload_digest(
    report: ResearchEvidenceChainIntegrityAuditReport,
) -> None:
    current = report.payload_digest
    expected = _payload_digest(report)
    if current == "":
        object.__setattr__(report, "payload_digest", expected)
        return
    _require_sha256_digest("payload_digest", current)
    if current != expected:
        raise ValueError("payload_digest must match report fields")


def _validate_payload_digest(report: ResearchEvidenceChainIntegrityAuditReport) -> None:
    current = _require_sha256_digest("payload_digest", report.payload_digest)
    if current != _payload_digest(report):
        raise ValueError("payload_digest must match report fields")


def _payload_digest(value: object) -> str:
    payload = _without_payload_digest(_payload_value(value))
    encoded = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _without_payload_digest(value: object) -> object:
    if type(value) is dict:
        return {
            key: _without_payload_digest(item)
            for key, item in value.items()
            if key != "payload_digest"
        }
    if type(value) is list:
        return [_without_payload_digest(item) for item in value]
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
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) is list:
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError(f"{path or label} is not public JSON serializable")


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _payload_required_string_list(payload: dict[str, Any], field_name: str) -> tuple[str, ...]:
    value = payload.get(field_name)
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    if any(type(item) is not str for item in value):
        raise ValueError(f"{field_name} must contain strings")
    return tuple(value)


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(VALUE_QUANTUM)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
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


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        value = numerator / denominator
    return _normalize_probability("freshness_ratio", value)


def _normalize_reason_codes(field_name: str, value: tuple[str, ...]) -> tuple[str, ...]:
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


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


__all__ = (
    "ResearchEvidenceChainIntegrityAuditConfig",
    "ResearchEvidenceChainIntegrityAuditMetrics",
    "ResearchEvidenceChainIntegrityAuditReport",
    "build_research_evidence_chain_integrity_audit_report",
    "research_evidence_chain_integrity_audit_public_payload",
    "validate_research_evidence_chain_integrity_audit_public_payload",
)
