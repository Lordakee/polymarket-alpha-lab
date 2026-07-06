"""Pure in-memory source crosscheck gate for research packet promotion."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, fields
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_PACKET_SOURCE_CROSSCHECK_GATE_V2_CONFIG_VERSION = (
    "research-packet-source-crosscheck-gate-v2-v0"
)

EVIDENCE_KINDS = ("official", "review", "resolution", "independent")
GATE_STATUSES = ("pass", "blocked")
PASS_NEXT_STEP = "promote_to_strategy_review"
BLOCKED_NEXT_STEP = "block_strategy_review_pending_source_crosscheck"

PASS_REASON = "source_crosscheck_gate_passed"
NO_EVIDENCE_REASON = "no_event_evidence"
INSUFFICIENT_INDEPENDENT_FAMILIES_REASON = "insufficient_independent_source_families"
MISSING_OFFICIAL_CONFIRMATION_REASON = "missing_official_confirmation"
INSUFFICIENT_FRESH_RECENCY_REASON = "insufficient_fresh_recency_coverage"
MISSING_CONTRADICTION_REVIEW_REASON = "missing_contradiction_review"
MISSING_RESOLUTION_TRACE_REASON = "missing_resolution_source_traceability"
UNRESOLVED_CONTRADICTION_REASON = "unresolved_evidence_contradiction"

REPORT_REASON_CODES = (
    PASS_REASON,
    NO_EVIDENCE_REASON,
    INSUFFICIENT_INDEPENDENT_FAMILIES_REASON,
    MISSING_OFFICIAL_CONFIRMATION_REASON,
    INSUFFICIENT_FRESH_RECENCY_REASON,
    MISSING_CONTRADICTION_REVIEW_REASON,
    MISSING_RESOLUTION_TRACE_REASON,
    UNRESOLVED_CONTRADICTION_REASON,
)
REASON_PRIORITY = {
    reason_code: index
    for index, reason_code in enumerate(
        (
            NO_EVIDENCE_REASON,
            INSUFFICIENT_INDEPENDENT_FAMILIES_REASON,
            MISSING_OFFICIAL_CONFIRMATION_REASON,
            INSUFFICIENT_FRESH_RECENCY_REASON,
            MISSING_CONTRADICTION_REVIEW_REASON,
            MISSING_RESOLUTION_TRACE_REASON,
            UNRESOLVED_CONTRADICTION_REASON,
            PASS_REASON,
        ),
    )
}
BLOCKING_REASONS = tuple(
    reason_code for reason_code in REPORT_REASON_CODES if reason_code != PASS_REASON
)
SOURCE_KIND_WEIGHT = {
    "official": 0,
    "review": 1,
    "resolution": 2,
    "independent": 3,
}
DECIMAL_CONTEXT = Context(prec=64)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANT = Decimal("0.000001")
DIGEST_PLACEHOLDER = "0" * 64
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
UNSAFE_PUBLIC_FRAGMENTS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
    "trading",
)


@dataclass(frozen=True)
class ResearchPacketSourceCrosscheckGateV2Config:
    config_version: str = DEFAULT_RESEARCH_PACKET_SOURCE_CROSSCHECK_GATE_V2_CONFIG_VERSION
    max_evidence_age_seconds: Decimal = Decimal("86400")
    min_independent_source_family_count: Decimal = Decimal("3")
    min_fresh_evidence_count: Decimal = Decimal("2")
    require_official_confirmation: bool = True
    require_contradiction_review: bool = True
    require_resolution_source_traceability: bool = True
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "max_evidence_age_seconds",
            _require_positive_decimal(
                "max_evidence_age_seconds",
                self.max_evidence_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "min_independent_source_family_count",
            _require_positive_decimal(
                "min_independent_source_family_count",
                self.min_independent_source_family_count,
            ),
        )
        object.__setattr__(
            self,
            "min_fresh_evidence_count",
            _require_positive_decimal(
                "min_fresh_evidence_count",
                self.min_fresh_evidence_count,
            ),
        )
        _require_bool(
            "require_official_confirmation",
            self.require_official_confirmation,
        )
        _require_bool(
            "require_contradiction_review",
            self.require_contradiction_review,
        )
        _require_bool(
            "require_resolution_source_traceability",
            self.require_resolution_source_traceability,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchPacketSourceCrosscheckEvidence:
    event_id: str
    evidence_id: str
    source_family: str
    source_kind: str
    evidence_outcome: str
    observed_at: datetime
    official_confirmation: bool = False
    contradiction_reviewed: bool = False
    resolution_source_traceable: bool = False
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("event_id", self.event_id)
        _require_canonical_string("evidence_id", self.evidence_id)
        _require_canonical_string("source_family", self.source_family)
        _require_source_kind("source_kind", self.source_kind)
        _require_canonical_string("evidence_outcome", self.evidence_outcome)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_bool("official_confirmation", self.official_confirmation)
        _require_bool("contradiction_reviewed", self.contradiction_reviewed)
        _require_bool("resolution_source_traceable", self.resolution_source_traceable)
        _require_hard_flags("evidence", self)


@dataclass(frozen=True)
class ResearchPacketSourceCrosscheckEventRow:
    event_id: str
    gate_status: str
    eligible_for_strategy_review: bool
    evidence_count: Decimal
    fresh_evidence_count: Decimal
    stale_evidence_count: Decimal
    independent_source_family_count: Decimal
    official_confirmation_count: Decimal
    contradiction_review_count: Decimal
    resolution_source_trace_count: Decimal
    contradicting_outcome_count: Decimal
    latest_evidence_age_seconds: Decimal | None
    oldest_evidence_age_seconds: Decimal | None
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("event_id", self.event_id)
        _require_gate_status("gate_status", self.gate_status)
        _require_bool("eligible_for_strategy_review", self.eligible_for_strategy_review)
        for field_name in (
            "evidence_count",
            "fresh_evidence_count",
            "stale_evidence_count",
            "independent_source_family_count",
            "official_confirmation_count",
            "contradiction_review_count",
            "resolution_source_trace_count",
            "contradicting_outcome_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_evidence_age_seconds",
            _normalize_optional_decimal(
                "latest_evidence_age_seconds",
                self.latest_evidence_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "oldest_evidence_age_seconds",
            _normalize_optional_decimal(
                "oldest_evidence_age_seconds",
                self.oldest_evidence_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_event_row(self)
        _require_hard_flags("event row", self)


@dataclass(frozen=True)
class ResearchPacketSourceCrosscheckGateV2Report:
    generated_at: datetime
    config_version: str
    gate_status: str
    recommended_next_step: str
    event_count: Decimal
    pass_event_count: Decimal
    blocked_event_count: Decimal
    evidence_count: Decimal
    fresh_evidence_count: Decimal
    stale_evidence_count: Decimal
    reason_codes: tuple[str, ...]
    event_rows: tuple[ResearchPacketSourceCrosscheckEventRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_gate_status("gate_status", self.gate_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        if self.recommended_next_step not in (PASS_NEXT_STEP, BLOCKED_NEXT_STEP):
            raise ValueError("recommended_next_step must be a known report-only action")
        for field_name in (
            "event_count",
            "pass_event_count",
            "blocked_event_count",
            "evidence_count",
            "fresh_evidence_count",
            "stale_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "event_rows",
            _normalize_event_rows(self.event_rows),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report(self)
        _require_hard_flags("report", self)


def build_research_packet_source_crosscheck_gate_v2(
    evidence_rows: object,
    *,
    config: ResearchPacketSourceCrosscheckGateV2Config,
    generated_at: datetime,
) -> ResearchPacketSourceCrosscheckGateV2Report:
    if type(config) is not ResearchPacketSourceCrosscheckGateV2Config:
        raise ValueError("config must be a ResearchPacketSourceCrosscheckGateV2Config")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    evidence = _normalize_evidence_rows(evidence_rows, generated_at=generated_at_utc)
    event_rows = _event_rows(evidence, config=config, generated_at=generated_at_utc)
    reason_codes = _report_reason_codes(event_rows)
    gate_status = _report_status(reason_codes)
    payload = _report_payload_without_digest(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        gate_status=gate_status,
        recommended_next_step=_next_step(gate_status),
        event_count=_decimal_count(len(event_rows)),
        pass_event_count=_event_status_count(event_rows, "pass"),
        blocked_event_count=_event_status_count(event_rows, "blocked"),
        evidence_count=sum((row.evidence_count for row in event_rows), ZERO),
        fresh_evidence_count=sum((row.fresh_evidence_count for row in event_rows), ZERO),
        stale_evidence_count=sum((row.stale_evidence_count for row in event_rows), ZERO),
        reason_codes=reason_codes,
        event_rows=event_rows,
        paper_only=True,
        report_only=True,
        readonly=True,
    )
    return ResearchPacketSourceCrosscheckGateV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        gate_status=gate_status,
        recommended_next_step=_next_step(gate_status),
        event_count=_decimal_count(len(event_rows)),
        pass_event_count=_event_status_count(event_rows, "pass"),
        blocked_event_count=_event_status_count(event_rows, "blocked"),
        evidence_count=sum((row.evidence_count for row in event_rows), ZERO),
        fresh_evidence_count=sum((row.fresh_evidence_count for row in event_rows), ZERO),
        stale_evidence_count=sum((row.stale_evidence_count for row in event_rows), ZERO),
        reason_codes=reason_codes,
        event_rows=event_rows,
        derived_validation_digest=_digest_payload(payload),
    )


def research_packet_source_crosscheck_gate_v2_payload(
    report: ResearchPacketSourceCrosscheckGateV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchPacketSourceCrosscheckGateV2Report:
        _require_hard_flags("report", report)
        _validate_report(report)
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchPacketSourceCrosscheckGateV2Report")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    _validate_public_payload_digest(payload)
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


def _normalize_evidence_rows(
    evidence_rows: object,
    *,
    generated_at: datetime,
) -> tuple[ResearchPacketSourceCrosscheckEvidence, ...]:
    if type(evidence_rows) not in (list, tuple):
        raise ValueError("evidence_rows must be a list or tuple")
    rows = tuple(evidence_rows)
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchPacketSourceCrosscheckEvidence:
            raise ValueError(
                "evidence_rows items must be ResearchPacketSourceCrosscheckEvidence",
            )
        _require_hard_flags("evidence row", row)
        observed_at = _as_utc("observed_at", row.observed_at)
        if observed_at > generated_at:
            raise ValueError("evidence observed_at must not be in the future")
        key = (row.event_id, row.evidence_id)
        if key in seen_keys:
            raise ValueError("evidence_id values must be unique per event")
        seen_keys.add(key)
    return tuple(sorted(rows, key=_evidence_input_key))


def _event_rows(
    evidence_rows: tuple[ResearchPacketSourceCrosscheckEvidence, ...],
    *,
    config: ResearchPacketSourceCrosscheckGateV2Config,
    generated_at: datetime,
) -> tuple[ResearchPacketSourceCrosscheckEventRow, ...]:
    rows = tuple(
        _event_row(
            event_id=event_id,
            evidence_rows=tuple(row for row in evidence_rows if row.event_id == event_id),
            config=config,
            generated_at=generated_at,
        )
        for event_id in sorted({row.event_id for row in evidence_rows})
    )
    return tuple(sorted(rows, key=_event_row_key))


def _event_row(
    *,
    event_id: str,
    evidence_rows: tuple[ResearchPacketSourceCrosscheckEvidence, ...],
    config: ResearchPacketSourceCrosscheckGateV2Config,
    generated_at: datetime,
) -> ResearchPacketSourceCrosscheckEventRow:
    ages = tuple(_age_seconds(generated_at, row.observed_at) for row in evidence_rows)
    fresh_count = _decimal_count(
        sum(1 for age in ages if age <= config.max_evidence_age_seconds),
    )
    evidence_count = _decimal_count(len(evidence_rows))
    stale_count = evidence_count - fresh_count
    family_count = _decimal_count({row.source_family for row in evidence_rows})
    official_count = _decimal_count(
        sum(1 for row in evidence_rows if row.official_confirmation),
    )
    review_count = _decimal_count(
        sum(1 for row in evidence_rows if row.contradiction_reviewed),
    )
    trace_count = _decimal_count(
        sum(1 for row in evidence_rows if row.resolution_source_traceable),
    )
    contradiction_count = _contradicting_outcome_count(evidence_rows)
    reason_codes = _event_reason_codes(
        family_count=family_count,
        official_count=official_count,
        fresh_count=fresh_count,
        review_count=review_count,
        trace_count=trace_count,
        contradiction_count=contradiction_count,
        config=config,
    )
    gate_status = "pass" if reason_codes == (PASS_REASON,) else "blocked"
    row_payload = _event_row_payload_without_digest(
        event_id=event_id,
        gate_status=gate_status,
        eligible_for_strategy_review=gate_status == "pass",
        evidence_count=evidence_count,
        fresh_evidence_count=fresh_count,
        stale_evidence_count=stale_count,
        independent_source_family_count=family_count,
        official_confirmation_count=official_count,
        contradiction_review_count=review_count,
        resolution_source_trace_count=trace_count,
        contradicting_outcome_count=contradiction_count,
        latest_evidence_age_seconds=min(ages) if ages else None,
        oldest_evidence_age_seconds=max(ages) if ages else None,
        reason_codes=reason_codes,
        paper_only=True,
        report_only=True,
        readonly=True,
    )
    return ResearchPacketSourceCrosscheckEventRow(
        event_id=event_id,
        gate_status=gate_status,
        eligible_for_strategy_review=gate_status == "pass",
        evidence_count=evidence_count,
        fresh_evidence_count=fresh_count,
        stale_evidence_count=stale_count,
        independent_source_family_count=family_count,
        official_confirmation_count=official_count,
        contradiction_review_count=review_count,
        resolution_source_trace_count=trace_count,
        contradicting_outcome_count=contradiction_count,
        latest_evidence_age_seconds=min(ages) if ages else None,
        oldest_evidence_age_seconds=max(ages) if ages else None,
        reason_codes=reason_codes,
        derived_validation_digest=_digest_payload(row_payload),
    )


def _event_reason_codes(
    *,
    family_count: Decimal,
    official_count: Decimal,
    fresh_count: Decimal,
    review_count: Decimal,
    trace_count: Decimal,
    contradiction_count: Decimal,
    config: ResearchPacketSourceCrosscheckGateV2Config,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if family_count < config.min_independent_source_family_count:
        reason_codes.append(INSUFFICIENT_INDEPENDENT_FAMILIES_REASON)
    if config.require_official_confirmation and official_count == ZERO:
        reason_codes.append(MISSING_OFFICIAL_CONFIRMATION_REASON)
    if fresh_count < config.min_fresh_evidence_count:
        reason_codes.append(INSUFFICIENT_FRESH_RECENCY_REASON)
    if config.require_contradiction_review and review_count == ZERO:
        reason_codes.append(MISSING_CONTRADICTION_REVIEW_REASON)
    if config.require_resolution_source_traceability and trace_count == ZERO:
        reason_codes.append(MISSING_RESOLUTION_TRACE_REASON)
    if contradiction_count > ZERO:
        reason_codes.append(UNRESOLVED_CONTRADICTION_REASON)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return tuple(reason_codes)


def _contradicting_outcome_count(
    evidence_rows: tuple[ResearchPacketSourceCrosscheckEvidence, ...],
) -> Decimal:
    outcome_counts = Counter(row.evidence_outcome for row in evidence_rows)
    if len(outcome_counts) <= 1:
        return ZERO
    return _decimal_count(sum(outcome_counts.values()) - max(outcome_counts.values()))


def _report_reason_codes(
    event_rows: tuple[ResearchPacketSourceCrosscheckEventRow, ...],
) -> tuple[str, ...]:
    if not event_rows:
        return (NO_EVIDENCE_REASON,)
    reason_codes = {
        reason_code
        for row in event_rows
        for reason_code in row.reason_codes
        if reason_code != PASS_REASON
    }
    if not reason_codes:
        return (PASS_REASON,)
    return tuple(sorted(reason_codes, key=lambda reason_code: REASON_PRIORITY[reason_code]))


def _report_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKING_REASONS for reason_code in reason_codes):
        return "blocked"
    return "pass"


def _next_step(gate_status: str) -> str:
    return PASS_NEXT_STEP if gate_status == "pass" else BLOCKED_NEXT_STEP


def _validate_event_row(row: ResearchPacketSourceCrosscheckEventRow) -> None:
    if row.fresh_evidence_count + row.stale_evidence_count != row.evidence_count:
        raise ValueError("evidence freshness counts must match evidence_count")
    if (row.evidence_count == ZERO) != (
        row.latest_evidence_age_seconds is None and row.oldest_evidence_age_seconds is None
    ):
        raise ValueError("evidence ages must match evidence_count")
    if (
        row.latest_evidence_age_seconds is not None
        and row.oldest_evidence_age_seconds is not None
        and row.latest_evidence_age_seconds > row.oldest_evidence_age_seconds
    ):
        raise ValueError("latest_evidence_age_seconds must be <= oldest_evidence_age_seconds")
    if row.gate_status != ("pass" if row.reason_codes == (PASS_REASON,) else "blocked"):
        raise ValueError("gate_status must match reason_codes")
    if row.eligible_for_strategy_review is not (row.gate_status == "pass"):
        raise ValueError("eligible_for_strategy_review must match gate_status")
    if row.derived_validation_digest != _event_row_digest(row):
        raise ValueError("derived_validation_digest mismatch")


def _validate_report(report: ResearchPacketSourceCrosscheckGateV2Report) -> None:
    if report.event_count != _decimal_count(len(report.event_rows)):
        raise ValueError("event_count must match event_rows")
    if report.pass_event_count != _event_status_count(report.event_rows, "pass"):
        raise ValueError("pass_event_count must match event_rows")
    if report.blocked_event_count != _event_status_count(report.event_rows, "blocked"):
        raise ValueError("blocked_event_count must match event_rows")
    if report.evidence_count != sum((row.evidence_count for row in report.event_rows), ZERO):
        raise ValueError("evidence_count must match event_rows")
    if report.fresh_evidence_count != sum(
        (row.fresh_evidence_count for row in report.event_rows),
        ZERO,
    ):
        raise ValueError("fresh_evidence_count must match event_rows")
    if report.stale_evidence_count != sum(
        (row.stale_evidence_count for row in report.event_rows),
        ZERO,
    ):
        raise ValueError("stale_evidence_count must match event_rows")
    expected_reason_codes = _report_reason_codes(report.event_rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match event_rows")
    expected_status = _report_status(report.reason_codes)
    if report.gate_status != expected_status:
        raise ValueError("gate_status must match reason_codes")
    if report.recommended_next_step != _next_step(report.gate_status):
        raise ValueError("recommended_next_step must match gate_status")
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest mismatch")


def _normalize_event_rows(
    rows: object,
) -> tuple[ResearchPacketSourceCrosscheckEventRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("event_rows must be a list or tuple")
    normalized = tuple(rows)
    seen_event_ids: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchPacketSourceCrosscheckEventRow:
            raise ValueError(
                "event_rows must contain ResearchPacketSourceCrosscheckEventRow",
            )
        _require_hard_flags("event row", row)
        if row.event_id in seen_event_ids:
            raise ValueError("event_rows event_id values must be unique")
        seen_event_ids.add(row.event_id)
    if normalized != tuple(sorted(normalized, key=_event_row_key)):
        raise ValueError("event_rows must be sorted deterministically")
    return normalized


def _normalize_reason_codes(name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{name} must contain at least one value")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{name} must be unique")
    for reason_code in reason_codes:
        _require_canonical_string(name, reason_code)
        if reason_code not in REPORT_REASON_CODES:
            raise ValueError(f"{name} must contain known reason codes")
    expected = tuple(
        sorted(reason_codes, key=lambda reason_code: REASON_PRIORITY[reason_code]),
    )
    if reason_codes != expected and reason_codes != (PASS_REASON,):
        raise ValueError(f"{name} must be sorted deterministically")
    return reason_codes


def _event_status_count(
    rows: tuple[ResearchPacketSourceCrosscheckEventRow, ...],
    gate_status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.gate_status == gate_status))


def _evidence_input_key(row: ResearchPacketSourceCrosscheckEvidence) -> tuple[str, int, str]:
    return (row.event_id, SOURCE_KIND_WEIGHT[row.source_kind], row.evidence_id)


def _event_row_key(row: ResearchPacketSourceCrosscheckEventRow) -> tuple[int, Decimal, str]:
    return (0 if row.gate_status == "blocked" else 1, -row.evidence_count, row.event_id)


def _age_seconds(later: datetime, earlier: datetime) -> Decimal:
    if earlier > later:
        raise ValueError("evidence observed_at must not be in the future")
    delta = later - earlier
    return _quantize(
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000")),
    )


def _decimal_count(value: object) -> Decimal:
    if type(value) is set:
        value = len(value)
    if type(value) is not int:
        raise ValueError("count source must be an int")
    return _quantize(Decimal(value))


def _normalize_optional_decimal(name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(name, value)


def _require_nonnegative_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize(value)


def _require_positive_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{name} must be positive")
    return decimal_value


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANT)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must be quantizable") from exc


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{name} contains unsafe detail")


def _require_bool(name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{name} must be a bool")


def _require_source_kind(name: str, value: object) -> None:
    if type(value) is not str or value not in EVIDENCE_KINDS:
        raise ValueError(f"{name} must be official, review, resolution, or independent")


def _require_gate_status(name: str, value: object) -> None:
    if type(value) is not str or value not in GATE_STATUSES:
        raise ValueError(f"{name} must be pass or blocked")


def _require_digest(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a lowercase sha256 hex digest")


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


def _event_row_payload_without_digest(
    *,
    event_id: str,
    gate_status: str,
    eligible_for_strategy_review: bool,
    evidence_count: Decimal,
    fresh_evidence_count: Decimal,
    stale_evidence_count: Decimal,
    independent_source_family_count: Decimal,
    official_confirmation_count: Decimal,
    contradiction_review_count: Decimal,
    resolution_source_trace_count: Decimal,
    contradicting_outcome_count: Decimal,
    latest_evidence_age_seconds: Decimal | None,
    oldest_evidence_age_seconds: Decimal | None,
    reason_codes: tuple[str, ...],
    paper_only: bool,
    report_only: bool,
    readonly: bool,
) -> dict[str, Any]:
    return {
        "event_id": event_id,
        "gate_status": gate_status,
        "eligible_for_strategy_review": eligible_for_strategy_review,
        "evidence_count": _json_ready(evidence_count),
        "fresh_evidence_count": _json_ready(fresh_evidence_count),
        "stale_evidence_count": _json_ready(stale_evidence_count),
        "independent_source_family_count": _json_ready(independent_source_family_count),
        "official_confirmation_count": _json_ready(official_confirmation_count),
        "contradiction_review_count": _json_ready(contradiction_review_count),
        "resolution_source_trace_count": _json_ready(resolution_source_trace_count),
        "contradicting_outcome_count": _json_ready(contradicting_outcome_count),
        "latest_evidence_age_seconds": _json_ready(latest_evidence_age_seconds),
        "oldest_evidence_age_seconds": _json_ready(oldest_evidence_age_seconds),
        "reason_codes": list(reason_codes),
        "paper_only": paper_only,
        "report_only": report_only,
        "readonly": readonly,
    }


def _event_row_payload(row: ResearchPacketSourceCrosscheckEventRow) -> dict[str, Any]:
    payload = _event_row_payload_without_digest(
        event_id=row.event_id,
        gate_status=row.gate_status,
        eligible_for_strategy_review=row.eligible_for_strategy_review,
        evidence_count=row.evidence_count,
        fresh_evidence_count=row.fresh_evidence_count,
        stale_evidence_count=row.stale_evidence_count,
        independent_source_family_count=row.independent_source_family_count,
        official_confirmation_count=row.official_confirmation_count,
        contradiction_review_count=row.contradiction_review_count,
        resolution_source_trace_count=row.resolution_source_trace_count,
        contradicting_outcome_count=row.contradicting_outcome_count,
        latest_evidence_age_seconds=row.latest_evidence_age_seconds,
        oldest_evidence_age_seconds=row.oldest_evidence_age_seconds,
        reason_codes=row.reason_codes,
        paper_only=row.paper_only,
        report_only=row.report_only,
        readonly=row.readonly,
    )
    payload[DERIVED_VALIDATION_DIGEST_FIELD] = row.derived_validation_digest
    return payload


def _report_payload_without_digest(
    *,
    generated_at: datetime,
    config_version: str,
    gate_status: str,
    recommended_next_step: str,
    event_count: Decimal,
    pass_event_count: Decimal,
    blocked_event_count: Decimal,
    evidence_count: Decimal,
    fresh_evidence_count: Decimal,
    stale_evidence_count: Decimal,
    reason_codes: tuple[str, ...],
    event_rows: tuple[ResearchPacketSourceCrosscheckEventRow, ...],
    paper_only: bool,
    report_only: bool,
    readonly: bool,
) -> dict[str, Any]:
    return {
        "generated_at": _json_ready(generated_at),
        "config_version": config_version,
        "gate_status": gate_status,
        "recommended_next_step": recommended_next_step,
        "event_count": _json_ready(event_count),
        "pass_event_count": _json_ready(pass_event_count),
        "blocked_event_count": _json_ready(blocked_event_count),
        "evidence_count": _json_ready(evidence_count),
        "fresh_evidence_count": _json_ready(fresh_evidence_count),
        "stale_evidence_count": _json_ready(stale_evidence_count),
        "reason_codes": list(reason_codes),
        "event_rows": [_event_row_payload(row) for row in event_rows],
        "paper_only": paper_only,
        "report_only": report_only,
        "readonly": readonly,
    }


def _event_row_digest(row: ResearchPacketSourceCrosscheckEventRow) -> str:
    return _digest_payload(
        _event_row_payload_without_digest(
            event_id=row.event_id,
            gate_status=row.gate_status,
            eligible_for_strategy_review=row.eligible_for_strategy_review,
            evidence_count=row.evidence_count,
            fresh_evidence_count=row.fresh_evidence_count,
            stale_evidence_count=row.stale_evidence_count,
            independent_source_family_count=row.independent_source_family_count,
            official_confirmation_count=row.official_confirmation_count,
            contradiction_review_count=row.contradiction_review_count,
            resolution_source_trace_count=row.resolution_source_trace_count,
            contradicting_outcome_count=row.contradicting_outcome_count,
            latest_evidence_age_seconds=row.latest_evidence_age_seconds,
            oldest_evidence_age_seconds=row.oldest_evidence_age_seconds,
            reason_codes=row.reason_codes,
            paper_only=row.paper_only,
            report_only=row.report_only,
            readonly=row.readonly,
        ),
    )


def _report_digest(report: ResearchPacketSourceCrosscheckGateV2Report) -> str:
    return _digest_payload(
        _report_payload_without_digest(
            generated_at=report.generated_at,
            config_version=report.config_version,
            gate_status=report.gate_status,
            recommended_next_step=report.recommended_next_step,
            event_count=report.event_count,
            pass_event_count=report.pass_event_count,
            blocked_event_count=report.blocked_event_count,
            evidence_count=report.evidence_count,
            fresh_evidence_count=report.fresh_evidence_count,
            stale_evidence_count=report.stale_evidence_count,
            reason_codes=report.reason_codes,
            event_rows=report.event_rows,
            paper_only=report.paper_only,
            report_only=report.report_only,
            readonly=report.readonly,
        ),
    )


def _validate_public_payload_digest(payload: dict[str, Any]) -> None:
    if DERIVED_VALIDATION_DIGEST_FIELD not in payload:
        raise ValueError("derived_validation_digest is required")
    _require_digest(
        DERIVED_VALIDATION_DIGEST_FIELD,
        payload[DERIVED_VALIDATION_DIGEST_FIELD],
    )
    digest_payload = dict(payload)
    digest_payload.pop(DERIVED_VALIDATION_DIGEST_FIELD)
    if payload[DERIVED_VALIDATION_DIGEST_FIELD] != _digest_payload(digest_payload):
        raise ValueError("derived_validation_digest mismatch")


def _digest_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: object) -> Any:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        if type(value) is ResearchPacketSourceCrosscheckEventRow:
            return _event_row_payload(value)
        if type(value) is ResearchPacketSourceCrosscheckGateV2Report:
            payload = _report_payload_without_digest(
                generated_at=value.generated_at,
                config_version=value.config_version,
                gate_status=value.gate_status,
                recommended_next_step=value.recommended_next_step,
                event_count=value.event_count,
                pass_event_count=value.pass_event_count,
                blocked_event_count=value.blocked_event_count,
                evidence_count=value.evidence_count,
                fresh_evidence_count=value.fresh_evidence_count,
                stale_evidence_count=value.stale_evidence_count,
                reason_codes=value.reason_codes,
                event_rows=value.event_rows,
                paper_only=value.paper_only,
                report_only=value.report_only,
                readonly=value.readonly,
            )
            payload[DERIVED_VALIDATION_DIGEST_FIELD] = value.derived_validation_digest
            return payload
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(nested_value)
        return ready
    if value is None or type(value) in (str, bool):
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal strings")
    raise ValueError("value is not JSON-ready")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if type(value) is dict:
        for key, nested_value in value.items():
            nested_path = key if not path else f"{path}.{key}"
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public field in {label}: {nested_path}")
            if key in {"paper_only", "report_only", "readonly"} and nested_value is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_public_payload(label, nested_value, nested_path)
        return
    if type(value) is list:
        for index, nested_value in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, nested_value, nested_path)
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"unsafe public value in {path or label}")
        return
    if value is None or type(value) is bool:
        return
    raise ValueError("public payload must be JSON-ready")


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)


__all__ = (
    "DEFAULT_RESEARCH_PACKET_SOURCE_CROSSCHECK_GATE_V2_CONFIG_VERSION",
    "ResearchPacketSourceCrosscheckGateV2Config",
    "ResearchPacketSourceCrosscheckEvidence",
    "ResearchPacketSourceCrosscheckEventRow",
    "ResearchPacketSourceCrosscheckGateV2Report",
    "build_research_packet_source_crosscheck_gate_v2",
    "research_packet_source_crosscheck_gate_v2_payload",
)
