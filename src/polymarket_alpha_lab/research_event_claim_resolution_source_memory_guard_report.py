"""Pure report-only claim resolution memory guard."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_EVENT_CLAIM_RESOLUTION_SOURCE_MEMORY_GUARD_CONFIG_VERSION = (
    "research-event-claim-resolution-memory-guard-report"
)
STATUSES = ("pass", "watch", "block")

_COUNT_QUANTUM = Decimal("0.000001")
_RATIO_QUANTUM = Decimal("0.000001")
_ZERO_COUNT = Decimal("0")
_ZERO_RATIO = Decimal("0.000000")
_ONE_RATIO = Decimal("1.000000")
_DIGEST_PREFIX = "recsmg-v0:"
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_UP)
_STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
_REASON_RANK = {
    "resolution_memory_guard_report_empty": 0,
    "resolution_memory_guard_report_block": 1,
    "resolution_memory_guard_report_watch": 2,
    "resolution_memory_guard_report_pass": 3,
    "resolution_memory_guard_block": 4,
    "resolution_memory_guard_watch": 5,
    "resolution_memory_guard_pass": 6,
    "evidence_conflict_present": 7,
    "stale_memory_present": 8,
    "unverified_memory_present": 9,
    "memory_gap_present": 10,
}
_PUBLIC_BLOCKED_FRAGMENTS = frozenset(
    "".join(parts)
    for parts in (
        ("can", "didate"),
        ("mar", "ket"),
        ("ques", "tion"),
        ("sou", "rce"),
        ("u", "rl"),
        ("te", "xt"),
        ("d", "sn"),
        ("ta", "ble"),
        ("to", "ken"),
        ("wa", "llet"),
        ("or", "der"),
        ("tra", "de"),
        ("live", " trading"),
        ("live", "_trading"),
        ("live", "-trading"),
        ("si", "zing"),
        ("recommen", "dation"),
        ("net", "work"),
        ("data", "base"),
        ("private", "_key"),
        ("b", "uy"),
        ("se", "ll"),
    )
)


@dataclass(frozen=True)
class ResearchEventClaimResolutionSourceMemoryGuardReportConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_CLAIM_RESOLUTION_SOURCE_MEMORY_GUARD_CONFIG_VERSION
    )
    watch_guard_pressure_score: Decimal = Decimal("0.250000")
    block_guard_pressure_score: Decimal = Decimal("0.750000")
    minimum_evidence_record_count: Decimal = Decimal("2")
    conflict_weight: Decimal = Decimal("0.400000")
    stale_weight: Decimal = Decimal("0.200000")
    unverified_weight: Decimal = Decimal("0.200000")
    memory_gap_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventClaimResolutionSourceMemoryGuardReportConfig:
            raise ValueError(
                "config must be a "
                "ResearchEventClaimResolutionSourceMemoryGuardReportConfig",
            )
        _require_public_text("config_version", self.config_version)
        for field_name in (
            "watch_guard_pressure_score",
            "block_guard_pressure_score",
            "conflict_weight",
            "stale_weight",
            "unverified_weight",
            "memory_gap_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "minimum_evidence_record_count",
            _normalize_positive_count(
                "minimum_evidence_record_count",
                self.minimum_evidence_record_count,
            ),
        )
        if self.watch_guard_pressure_score > self.block_guard_pressure_score:
            raise ValueError("watch_guard_pressure_score must not exceed block threshold")
        weight_total = _quantize_ratio(
            self.conflict_weight
            + self.stale_weight
            + self.unverified_weight
            + self.memory_gap_weight,
        )
        if weight_total != _ONE_RATIO:
            raise ValueError("guard weights must sum to one")
        _require_flags(self)


@dataclass(frozen=True)
class ResearchEventClaimResolutionSourceMemoryGuardInput:
    private_claim_ref: str
    private_event_ref: str
    private_rule_ref: str
    private_evidence_locator: str
    private_evidence_excerpt: str
    private_store_locator: str
    private_set_name: str
    private_secret_marker: str
    claim_observed_at: datetime
    resolution_observed_at: datetime
    memory_recorded_at: datetime
    evidence_record_count: Decimal
    confirmed_record_count: Decimal
    conflicting_record_count: Decimal
    stale_record_count: Decimal
    unverified_record_count: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventClaimResolutionSourceMemoryGuardInput:
            raise ValueError(
                "input must be a ResearchEventClaimResolutionSourceMemoryGuardInput",
            )
        for field_name in (
            "private_claim_ref",
            "private_event_ref",
            "private_rule_ref",
            "private_evidence_locator",
            "private_evidence_excerpt",
            "private_store_locator",
            "private_set_name",
            "private_secret_marker",
        ):
            _require_private_text(field_name, getattr(self, field_name))
        for field_name in (
            "claim_observed_at",
            "resolution_observed_at",
            "memory_recorded_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_utc(field_name, getattr(self, field_name)),
            )
        if self.resolution_observed_at < self.claim_observed_at:
            raise ValueError(
                "resolution_observed_at must not be before claim_observed_at",
            )
        if self.memory_recorded_at < self.resolution_observed_at:
            raise ValueError(
                "memory_recorded_at must not be before resolution_observed_at",
            )
        for field_name in (
            "evidence_record_count",
            "confirmed_record_count",
            "conflicting_record_count",
            "stale_record_count",
            "unverified_record_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        _validate_input_count_shape(self)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_flags(self)


@dataclass(frozen=True)
class ResearchEventClaimResolutionSourceMemoryGuardRow:
    row_ref: str
    claim_observed_at: datetime
    resolution_observed_at: datetime
    memory_recorded_at: datetime
    evidence_record_count: Decimal
    confirmed_record_count: Decimal
    conflicting_record_count: Decimal
    stale_record_count: Decimal
    unverified_record_count: Decimal
    confirmation_ratio: Decimal
    conflict_ratio: Decimal
    stale_ratio: Decimal
    unverified_ratio: Decimal
    memory_gap_ratio: Decimal
    guard_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventClaimResolutionSourceMemoryGuardRow:
            raise ValueError(
                "row must be a ResearchEventClaimResolutionSourceMemoryGuardRow",
            )
        _require_public_text("row_ref", self.row_ref)
        for field_name in (
            "claim_observed_at",
            "resolution_observed_at",
            "memory_recorded_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_utc(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "evidence_record_count",
            "confirmed_record_count",
            "conflicting_record_count",
            "stale_record_count",
            "unverified_record_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "confirmation_ratio",
            "conflict_ratio",
            "stale_ratio",
            "unverified_ratio",
            "memory_gap_ratio",
            "guard_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status(self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row_shape(self)
        _set_or_require_digest(self, _digest_dataclass(self))
        _reject_unsafe_public_payload("row", self)
        _require_flags(self)


@dataclass(frozen=True)
class ResearchEventClaimResolutionSourceMemoryGuardReport:
    generated_at: datetime
    config_version: str
    claim_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    conflict_claim_count: Decimal
    stale_claim_count: Decimal
    unverified_claim_count: Decimal
    memory_gap_claim_count: Decimal
    max_guard_pressure_score: Decimal
    average_guard_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchEventClaimResolutionSourceMemoryGuardRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventClaimResolutionSourceMemoryGuardReport:
            raise ValueError(
                "report must be a ResearchEventClaimResolutionSourceMemoryGuardReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        for field_name in (
            "claim_count",
            "pass_count",
            "watch_count",
            "block_count",
            "conflict_claim_count",
            "stale_claim_count",
            "unverified_claim_count",
            "memory_gap_claim_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_guard_pressure_score",
            "average_guard_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status(self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        rows = tuple(self.rows)
        for row in rows:
            if type(row) is not ResearchEventClaimResolutionSourceMemoryGuardRow:
                raise ValueError("rows must contain memory guard rows")
            _require_flags(row)
            _require_dataclass_digest(row)
        object.__setattr__(self, "rows", rows)
        _validate_report_rollup(self)
        _set_or_require_digest(self, _digest_dataclass(self))
        _reject_unsafe_public_payload("report", self)
        _require_flags(self)


def build_research_event_claim_resolution_source_memory_guard_report(
    claims: tuple[ResearchEventClaimResolutionSourceMemoryGuardInput, ...]
    | list[ResearchEventClaimResolutionSourceMemoryGuardInput],
    *,
    config: ResearchEventClaimResolutionSourceMemoryGuardReportConfig | None = None,
    generated_at: datetime,
) -> ResearchEventClaimResolutionSourceMemoryGuardReport:
    cfg = config or ResearchEventClaimResolutionSourceMemoryGuardReportConfig()
    if type(cfg) is not ResearchEventClaimResolutionSourceMemoryGuardReportConfig:
        raise ValueError(
            "config must be a ResearchEventClaimResolutionSourceMemoryGuardReportConfig",
        )
    _require_flags(cfg)
    generated_at = _as_utc("generated_at", generated_at)
    rows: list[ResearchEventClaimResolutionSourceMemoryGuardRow] = []
    row_refs: set[str] = set()
    for claim in tuple(claims):
        if type(claim) is not ResearchEventClaimResolutionSourceMemoryGuardInput:
            raise ValueError("claims must contain memory guard inputs")
        _require_flags(claim)
        if claim.claim_observed_at > generated_at:
            raise ValueError("claim_observed_at must not be after generated_at")
        if claim.resolution_observed_at > generated_at:
            raise ValueError("resolution_observed_at must not be after generated_at")
        if claim.memory_recorded_at > generated_at:
            raise ValueError("memory_recorded_at must not be after generated_at")
        row = _row_for_claim(claim, cfg)
        if row.row_ref in row_refs:
            raise ValueError("claims must not contain duplicate private references")
        row_refs.add(row.row_ref)
        rows.append(row)
    rows_tuple = tuple(sorted(rows, key=_row_sort_key))
    return _report_for_rows(rows_tuple, cfg, generated_at)


def research_event_claim_resolution_source_memory_guard_report_payload(
    report: ResearchEventClaimResolutionSourceMemoryGuardReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchEventClaimResolutionSourceMemoryGuardReport:
        _require_flags(report)
        _require_dataclass_digest(report)
        for row in report.rows:
            _require_dataclass_digest(row)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _reject_unsafe_public_payload("report payload", payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("report payload", report)
        _require_payload_flags(report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _require_payload_digest_if_present(payload)
        return payload
    raise ValueError("report must be a ResearchEventClaimResolutionSourceMemoryGuardReport")


def _row_for_claim(
    claim: ResearchEventClaimResolutionSourceMemoryGuardInput,
    config: ResearchEventClaimResolutionSourceMemoryGuardReportConfig,
) -> ResearchEventClaimResolutionSourceMemoryGuardRow:
    confirmation_ratio = _ratio(
        claim.confirmed_record_count,
        claim.evidence_record_count,
    )
    conflict_ratio = _ratio(
        claim.conflicting_record_count,
        claim.evidence_record_count,
    )
    stale_ratio = _ratio(claim.stale_record_count, claim.evidence_record_count)
    unverified_ratio = _ratio(
        claim.unverified_record_count,
        claim.evidence_record_count,
    )
    memory_gap_ratio = _memory_gap_ratio(
        claim.evidence_record_count,
        config.minimum_evidence_record_count,
    )
    guard_pressure_score = _quantize_ratio(
        conflict_ratio * config.conflict_weight
        + stale_ratio * config.stale_weight
        + unverified_ratio * config.unverified_weight
        + memory_gap_ratio * config.memory_gap_weight,
    )
    status = _status_for_score(
        guard_pressure_score,
        config.watch_guard_pressure_score,
        config.block_guard_pressure_score,
    )
    return ResearchEventClaimResolutionSourceMemoryGuardRow(
        row_ref=_row_ref(claim),
        claim_observed_at=claim.claim_observed_at,
        resolution_observed_at=claim.resolution_observed_at,
        memory_recorded_at=claim.memory_recorded_at,
        evidence_record_count=claim.evidence_record_count,
        confirmed_record_count=claim.confirmed_record_count,
        conflicting_record_count=claim.conflicting_record_count,
        stale_record_count=claim.stale_record_count,
        unverified_record_count=claim.unverified_record_count,
        confirmation_ratio=confirmation_ratio,
        conflict_ratio=conflict_ratio,
        stale_ratio=stale_ratio,
        unverified_ratio=unverified_ratio,
        memory_gap_ratio=memory_gap_ratio,
        guard_pressure_score=guard_pressure_score,
        status=status,
        reason_codes=_row_reason_codes(
            status,
            conflict_ratio,
            stale_ratio,
            unverified_ratio,
            memory_gap_ratio,
        ),
    )


def _report_for_rows(
    rows: tuple[ResearchEventClaimResolutionSourceMemoryGuardRow, ...],
    config: ResearchEventClaimResolutionSourceMemoryGuardReportConfig,
    generated_at: datetime,
) -> ResearchEventClaimResolutionSourceMemoryGuardReport:
    claim_count = _count_decimal(len(rows))
    pass_count = _count_status(rows, "pass")
    watch_count = _count_status(rows, "watch")
    block_count = _count_status(rows, "block")
    if rows:
        status = min((row.status for row in rows), key=lambda item: _STATUS_RANK[item])
        max_score = max(row.guard_pressure_score for row in rows)
        average_score = _quantize_ratio(
            sum((row.guard_pressure_score for row in rows), _ZERO_RATIO) / claim_count,
        )
        reason_codes = _report_reason_codes(status, rows)
    else:
        status = "block"
        max_score = _ZERO_RATIO
        average_score = _ZERO_RATIO
        reason_codes = ("resolution_memory_guard_report_empty",)
    return ResearchEventClaimResolutionSourceMemoryGuardReport(
        generated_at=generated_at,
        config_version=config.config_version,
        claim_count=claim_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        conflict_claim_count=_count_matching(
            rows,
            lambda row: row.conflict_ratio > _ZERO_RATIO,
        ),
        stale_claim_count=_count_matching(rows, lambda row: row.stale_ratio > _ZERO_RATIO),
        unverified_claim_count=_count_matching(
            rows,
            lambda row: row.unverified_ratio > _ZERO_RATIO,
        ),
        memory_gap_claim_count=_count_matching(
            rows,
            lambda row: row.memory_gap_ratio > _ZERO_RATIO,
        ),
        max_guard_pressure_score=max_score,
        average_guard_pressure_score=average_score,
        status=status,
        reason_codes=reason_codes,
        rows=rows,
    )


def _row_reason_codes(
    status: str,
    conflict_ratio: Decimal,
    stale_ratio: Decimal,
    unverified_ratio: Decimal,
    memory_gap_ratio: Decimal,
) -> tuple[str, ...]:
    reason_codes = [f"resolution_memory_guard_{status}"]
    if conflict_ratio > _ZERO_RATIO:
        reason_codes.append("evidence_conflict_present")
    if stale_ratio > _ZERO_RATIO:
        reason_codes.append("stale_memory_present")
    if unverified_ratio > _ZERO_RATIO:
        reason_codes.append("unverified_memory_present")
    if memory_gap_ratio > _ZERO_RATIO:
        reason_codes.append("memory_gap_present")
    return _sort_reason_codes(reason_codes)


def _report_reason_codes(
    status: str,
    rows: tuple[ResearchEventClaimResolutionSourceMemoryGuardRow, ...],
) -> tuple[str, ...]:
    reason_codes = [f"resolution_memory_guard_report_{status}"]
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _sort_reason_codes(reason_codes)


def _row_ref(claim: ResearchEventClaimResolutionSourceMemoryGuardInput) -> str:
    private_payload = {
        "private_claim_ref": claim.private_claim_ref,
        "private_event_ref": claim.private_event_ref,
        "private_rule_ref": claim.private_rule_ref,
        "private_evidence_locator": claim.private_evidence_locator,
        "private_evidence_excerpt": claim.private_evidence_excerpt,
        "private_store_locator": claim.private_store_locator,
        "private_set_name": claim.private_set_name,
        "private_secret_marker": claim.private_secret_marker,
    }
    encoded = json.dumps(
        private_payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return f"{_DIGEST_PREFIX}{sha256(encoded).hexdigest()}"


def _row_sort_key(row: ResearchEventClaimResolutionSourceMemoryGuardRow) -> tuple[int, Decimal, str]:
    return (_STATUS_RANK[row.status], -row.guard_pressure_score, row.row_ref)


def _validate_input_count_shape(
    claim: ResearchEventClaimResolutionSourceMemoryGuardInput,
) -> None:
    for field_name in (
        "confirmed_record_count",
        "conflicting_record_count",
        "stale_record_count",
        "unverified_record_count",
    ):
        if getattr(claim, field_name) > claim.evidence_record_count:
            raise ValueError(f"{field_name} must not exceed evidence_record_count")


def _validate_row_shape(row: ResearchEventClaimResolutionSourceMemoryGuardRow) -> None:
    if row.resolution_observed_at < row.claim_observed_at:
        raise ValueError("resolution_observed_at must not be before claim_observed_at")
    if row.memory_recorded_at < row.resolution_observed_at:
        raise ValueError("memory_recorded_at must not be before resolution_observed_at")
    for field_name in (
        "confirmed_record_count",
        "conflicting_record_count",
        "stale_record_count",
        "unverified_record_count",
    ):
        if getattr(row, field_name) > row.evidence_record_count:
            raise ValueError(f"{field_name} must not exceed evidence_record_count")


def _validate_report_rollup(
    report: ResearchEventClaimResolutionSourceMemoryGuardReport,
) -> None:
    rows = report.rows
    expected_count = _count_decimal(len(rows))
    if report.claim_count != expected_count:
        raise ValueError("claim_count must match rows")
    status_counts = {
        "pass": _count_status(rows, "pass"),
        "watch": _count_status(rows, "watch"),
        "block": _count_status(rows, "block"),
    }
    if report.pass_count != status_counts["pass"]:
        raise ValueError("pass_count must match rows")
    if report.watch_count != status_counts["watch"]:
        raise ValueError("watch_count must match rows")
    if report.block_count != status_counts["block"]:
        raise ValueError("block_count must match rows")
    if report.conflict_claim_count != _count_matching(
        rows,
        lambda row: row.conflict_ratio > _ZERO_RATIO,
    ):
        raise ValueError("conflict_claim_count must match rows")
    if report.stale_claim_count != _count_matching(
        rows,
        lambda row: row.stale_ratio > _ZERO_RATIO,
    ):
        raise ValueError("stale_claim_count must match rows")
    if report.unverified_claim_count != _count_matching(
        rows,
        lambda row: row.unverified_ratio > _ZERO_RATIO,
    ):
        raise ValueError("unverified_claim_count must match rows")
    if report.memory_gap_claim_count != _count_matching(
        rows,
        lambda row: row.memory_gap_ratio > _ZERO_RATIO,
    ):
        raise ValueError("memory_gap_claim_count must match rows")
    if tuple(sorted(rows, key=_row_sort_key)) != rows:
        raise ValueError("rows must be sorted deterministically")
    if rows:
        expected_status = min(
            (row.status for row in rows),
            key=lambda item: _STATUS_RANK[item],
        )
        expected_max = max(row.guard_pressure_score for row in rows)
        expected_average = _quantize_ratio(
            sum((row.guard_pressure_score for row in rows), _ZERO_RATIO)
            / report.claim_count,
        )
        expected_reasons = _report_reason_codes(expected_status, rows)
    else:
        expected_status = "block"
        expected_max = _ZERO_RATIO
        expected_average = _ZERO_RATIO
        expected_reasons = ("resolution_memory_guard_report_empty",)
    if report.status != expected_status:
        raise ValueError("status must match rows")
    if report.max_guard_pressure_score != expected_max:
        raise ValueError("max_guard_pressure_score must match rows")
    if report.average_guard_pressure_score != expected_average:
        raise ValueError("average_guard_pressure_score must match rows")
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match rows")


def _count_status(
    rows: tuple[ResearchEventClaimResolutionSourceMemoryGuardRow, ...],
    status: str,
) -> Decimal:
    return _count_matching(rows, lambda row: row.status == status)


def _count_matching(
    rows: tuple[ResearchEventClaimResolutionSourceMemoryGuardRow, ...],
    predicate: Any,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if predicate(row)))


def _count_decimal(value: int) -> Decimal:
    return Decimal(str(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO_COUNT:
        return _ZERO_RATIO
    return _quantize_ratio(numerator / denominator)


def _memory_gap_ratio(evidence_count: Decimal, minimum_count: Decimal) -> Decimal:
    if evidence_count >= minimum_count:
        return _ZERO_RATIO
    return _quantize_ratio((minimum_count - evidence_count) / minimum_count)


def _status_for_score(score: Decimal, watch_threshold: Decimal, block_threshold: Decimal) -> str:
    if score >= block_threshold:
        return "block"
    if score >= watch_threshold:
        return "watch"
    return "pass"


def _normalize_count(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value < _ZERO_COUNT:
        raise ValueError(f"{name} must be non-negative")
    if value != _quantize_count(value):
        raise ValueError(f"{name} must use no more than six decimal places")
    return value


def _normalize_positive_count(name: str, value: object) -> Decimal:
    normalized = _normalize_count(name, value)
    if normalized <= _ZERO_COUNT:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_ratio(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value < _ZERO_RATIO or value > _ONE_RATIO:
        raise ValueError(f"{name} must be between zero and one")
    return _quantize_ratio(value)


def _quantize_count(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_COUNT_QUANTUM)


def _quantize_ratio(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_RATIO_QUANTUM)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_private_text(name: str, value: object) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")


def _require_public_text(name: str, value: object) -> None:
    _require_private_text(name, value)
    if _has_blocked_public_fragment(value):
        raise ValueError(f"{name} contains unsafe public text")


def _normalize_reason_codes(name: str, value: object) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise ValueError(f"{name} must be a tuple")
    if not value:
        raise ValueError(f"{name} must not be empty")
    normalized: list[str] = []
    seen: set[str] = set()
    for item in value:
        if type(item) is not str or not item.strip():
            raise ValueError(f"{name} must contain non-empty strings")
        if item in seen:
            raise ValueError(f"{name} must not contain duplicate values")
        if _has_blocked_public_fragment(item):
            raise ValueError(f"{name} contains unsafe public text")
        seen.add(item)
        normalized.append(item)
    return tuple(normalized)


def _sort_reason_codes(reason_codes: list[str]) -> tuple[str, ...]:
    return tuple(
        sorted(
            set(reason_codes),
            key=lambda item: (_REASON_RANK.get(item, 999), item),
        ),
    )


def _require_status(value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError("status must be pass, watch, or block")


def _require_flags(value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError("readonly must be True")


def _require_payload_flags(payload: dict[str, Any]) -> None:
    if payload.get("paper_only") is not True:
        raise ValueError("paper_only must be True")
    if payload.get("report_only") is not True:
        raise ValueError("report_only must be True")
    if payload.get("readonly") is not True:
        raise ValueError("readonly must be True")


def _set_or_require_digest(value: object, computed: str) -> None:
    actual = getattr(value, "derived_validation_digest")
    if actual == "":
        object.__setattr__(value, "derived_validation_digest", computed)
        return
    if actual != computed:
        raise ValueError("derived_validation_digest mismatch")


def _require_dataclass_digest(value: object) -> None:
    expected = _digest_dataclass(value)
    actual = getattr(value, "derived_validation_digest", None)
    if actual != expected:
        raise ValueError("derived_validation_digest mismatch")


def _require_payload_digest_if_present(payload: dict[str, Any]) -> None:
    rows = payload.get("rows")
    if isinstance(rows, list):
        for row in rows:
            if isinstance(row, dict) and "derived_validation_digest" in row:
                expected_row_digest = _digest_payload(row)
                if row["derived_validation_digest"] != expected_row_digest:
                    raise ValueError("derived_validation_digest mismatch")
    if "derived_validation_digest" in payload:
        expected_report_digest = _digest_payload(payload)
        if payload["derived_validation_digest"] != expected_report_digest:
            raise ValueError("derived_validation_digest mismatch")


def _digest_dataclass(value: object) -> str:
    if not is_dataclass(value) or isinstance(value, type):
        raise ValueError("digest value must be a dataclass instance")
    payload = _json_ready(asdict(value))
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    return _digest_payload(payload)


def _digest_payload(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(
        digest_payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return f"{_DIGEST_PREFIX}{sha256(encoded).hexdigest()}"


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("public numeric value must be a Decimal")
        if not value.is_finite():
            raise ValueError("public numeric value must be finite")
        return str(value)
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("public datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is bool:
        return value
    if type(value) in (float, int):
        raise ValueError("public numeric value must be a Decimal")
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


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_blocked_public_fragment(key):
                raise ValueError(f"unsafe public field in {label}")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str and _has_blocked_public_fragment(value):
        raise ValueError(f"unsafe public value in {label}")


def _has_blocked_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in _PUBLIC_BLOCKED_FRAGMENTS)


__all__ = (
    "DEFAULT_RESEARCH_EVENT_CLAIM_RESOLUTION_SOURCE_MEMORY_GUARD_CONFIG_VERSION",
    "STATUSES",
    "ResearchEventClaimResolutionSourceMemoryGuardReportConfig",
    "ResearchEventClaimResolutionSourceMemoryGuardInput",
    "ResearchEventClaimResolutionSourceMemoryGuardRow",
    "ResearchEventClaimResolutionSourceMemoryGuardReport",
    "build_research_event_claim_resolution_source_memory_guard_report",
    "research_event_claim_resolution_source_memory_guard_report_payload",
)
