"""Decimal-only read-only report for event outcome claim timing."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_EVENT_RESOLUTION_CLAIM_MEMORY_LATENCY_REPORT_CONFIG_VERSION = (
    "research-event-resolution-claim-memory-latency-report"
)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROS_PER_SECOND = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_UP)
STATUSES = ("block", "watch", "pass")
STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
EMPTY_REASON = "claim_memory_latency_report_empty"
OWNED_REASON_CODES = frozenset(
    (
        "claim_memory_latency_block",
        "claim_memory_latency_watch",
        "claim_memory_latency_pass",
        "memory_seen_latency_block",
        "resolution_latency_block",
        "parser_confidence_block",
        "claim_strength_block",
        "memory_seen_latency_watch",
        "resolution_latency_watch",
        "parser_confidence_watch",
        "claim_strength_watch",
        EMPTY_REASON,
    ),
)
REASON_RANK = {
    "claim_memory_latency_block": 0,
    "claim_memory_latency_watch": 1,
    "claim_memory_latency_pass": 2,
    "memory_seen_latency_block": 3,
    "resolution_latency_block": 4,
    "parser_confidence_block": 5,
    "claim_strength_block": 6,
    "memory_seen_latency_watch": 7,
    "resolution_latency_watch": 8,
    "parser_confidence_watch": 9,
    "claim_strength_watch": 10,
    EMPTY_REASON: 11,
}
REPORT_KEYS = (
    "generated_at",
    "config_version",
    "claim_count",
    "pass_count",
    "watch_count",
    "block_count",
    "status",
    "reason_codes",
    "rows",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_KEYS = (
    "row_ref",
    "claim_observed_at",
    "memory_recorded_at",
    "resolved_at",
    "memory_latency_watch_seconds",
    "memory_latency_block_seconds",
    "resolution_latency_watch_seconds",
    "resolution_latency_block_seconds",
    "parser_confidence_watch_score",
    "parser_confidence_block_score",
    "claim_strength_watch_score",
    "claim_strength_block_score",
    "claim_memory_latency_seconds",
    "resolution_latency_seconds",
    "parser_confidence",
    "claim_strength",
    "latency_score",
    "claim_status",
    "reason_codes",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)


def _join(*pieces: str) -> str:
    return "".join(pieces)


UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        _join("candi", "date"),
        _join("mar", "ket"),
        _join("so", "urce"),
        _join("u", "rl"),
        _join("te", "xt"),
        _join("d", "sn"),
        _join("ta", "ble"),
        _join("to", "ken"),
        _join("d", "b"),
        _join("net", "work"),
        _join("wa", "llet"),
        _join("au", "th"),
        _join("or", "der"),
        _join("li", "ve", " tra", "ding"),
        _join("si", "zing"),
        _join("recommen", "dation"),
        _join("bro", "ker"),
        _join("data", "base"),
        _join("private", "_key"),
        _join("sup", "abase"),
        _join("sql", "ite"),
        _join("re", "quests"),
        _join("tra", "de"),
        _join("b", "uy"),
        _join("se", "ll"),
        _join("sign", "ing"),
        _join("mut", "ation"),
    ),
)


@dataclass(frozen=True)
class ResearchEventResolutionClaimMemoryLatencyReportConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_RESOLUTION_CLAIM_MEMORY_LATENCY_REPORT_CONFIG_VERSION
    )
    memory_latency_watch_seconds: Decimal = Decimal("300.000000")
    memory_latency_block_seconds: Decimal = Decimal("900.000000")
    resolution_latency_watch_seconds: Decimal = Decimal("3600.000000")
    resolution_latency_block_seconds: Decimal = Decimal("7200.000000")
    parser_confidence_watch_score: Decimal = Decimal("0.800000")
    parser_confidence_block_score: Decimal = Decimal("0.600000")
    claim_strength_watch_score: Decimal = Decimal("0.700000")
    claim_strength_block_score: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionClaimMemoryLatencyReportConfig:
            raise ValueError(
                "config must be a ResearchEventResolutionClaimMemoryLatencyReportConfig",
            )
        _require_text("config_version", self.config_version)
        for field_name in (
            "memory_latency_watch_seconds",
            "memory_latency_block_seconds",
            "resolution_latency_watch_seconds",
            "resolution_latency_block_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "parser_confidence_watch_score",
            "parser_confidence_block_score",
            "claim_strength_watch_score",
            "claim_strength_block_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_less_than(
            "memory_latency_watch_seconds",
            self.memory_latency_watch_seconds,
            self.memory_latency_block_seconds,
        )
        _require_less_than(
            "resolution_latency_watch_seconds",
            self.resolution_latency_watch_seconds,
            self.resolution_latency_block_seconds,
        )
        if self.parser_confidence_block_score > self.parser_confidence_watch_score:
            raise ValueError(
                "parser_confidence_block_score must not exceed watch threshold",
            )
        if self.claim_strength_block_score > self.claim_strength_watch_score:
            raise ValueError(
                "claim_strength_block_score must not exceed watch threshold",
            )
        _require_flags("config", self)


@dataclass(frozen=True)
class ResearchEventResolutionClaimMemoryLatencyInput:
    private_subject_ref: str
    private_event_ref: str
    private_evidence_locator: str
    private_evidence_excerpt: str
    private_store_locator: str
    private_set_name: str
    private_secret_marker: str
    claim_observed_at: datetime
    memory_recorded_at: datetime
    resolved_at: datetime | None
    parser_confidence: Decimal
    claim_strength: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionClaimMemoryLatencyInput:
            raise ValueError(
                "input must be a ResearchEventResolutionClaimMemoryLatencyInput",
            )
        for field_name in (
            "private_subject_ref",
            "private_event_ref",
            "private_evidence_locator",
            "private_evidence_excerpt",
            "private_store_locator",
            "private_set_name",
            "private_secret_marker",
        ):
            _require_text(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "claim_observed_at",
            _as_utc("claim_observed_at", self.claim_observed_at),
        )
        object.__setattr__(
            self,
            "memory_recorded_at",
            _as_utc("memory_recorded_at", self.memory_recorded_at),
        )
        object.__setattr__(self, "resolved_at", _as_optional_utc("resolved_at", self.resolved_at))
        if self.memory_recorded_at < self.claim_observed_at:
            raise ValueError("memory_recorded_at must not be before claim_observed_at")
        if self.resolved_at is not None and self.resolved_at < self.claim_observed_at:
            raise ValueError("resolved_at must not be before claim_observed_at")
        for field_name in ("parser_confidence", "claim_strength"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_flags("input", self)


@dataclass(frozen=True)
class ResearchEventResolutionClaimMemoryLatencyRow:
    row_ref: str
    claim_observed_at: datetime
    memory_recorded_at: datetime
    resolved_at: datetime | None
    memory_latency_watch_seconds: Decimal
    memory_latency_block_seconds: Decimal
    resolution_latency_watch_seconds: Decimal
    resolution_latency_block_seconds: Decimal
    parser_confidence_watch_score: Decimal
    parser_confidence_block_score: Decimal
    claim_strength_watch_score: Decimal
    claim_strength_block_score: Decimal
    claim_memory_latency_seconds: Decimal
    resolution_latency_seconds: Decimal
    parser_confidence: Decimal
    claim_strength: Decimal
    latency_score: Decimal
    claim_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionClaimMemoryLatencyRow:
            raise ValueError("row must be a ResearchEventResolutionClaimMemoryLatencyRow")
        _require_digest_text("row_ref", self.row_ref)
        object.__setattr__(
            self,
            "claim_observed_at",
            _as_utc("claim_observed_at", self.claim_observed_at),
        )
        object.__setattr__(
            self,
            "memory_recorded_at",
            _as_utc("memory_recorded_at", self.memory_recorded_at),
        )
        object.__setattr__(self, "resolved_at", _as_optional_utc("resolved_at", self.resolved_at))
        if self.memory_recorded_at < self.claim_observed_at:
            raise ValueError("memory_recorded_at must not be before claim_observed_at")
        if self.resolved_at is not None and self.resolved_at < self.claim_observed_at:
            raise ValueError("resolved_at must not be before claim_observed_at")
        for field_name in (
            "memory_latency_watch_seconds",
            "memory_latency_block_seconds",
            "resolution_latency_watch_seconds",
            "resolution_latency_block_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        _require_less_than(
            "memory_latency_watch_seconds",
            self.memory_latency_watch_seconds,
            self.memory_latency_block_seconds,
        )
        _require_less_than(
            "resolution_latency_watch_seconds",
            self.resolution_latency_watch_seconds,
            self.resolution_latency_block_seconds,
        )
        for field_name in (
            "parser_confidence_watch_score",
            "parser_confidence_block_score",
            "claim_strength_watch_score",
            "claim_strength_block_score",
            "parser_confidence",
            "claim_strength",
            "latency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.parser_confidence_block_score > self.parser_confidence_watch_score:
            raise ValueError(
                "parser_confidence_block_score must not exceed watch threshold",
            )
        if self.claim_strength_block_score > self.claim_strength_watch_score:
            raise ValueError(
                "claim_strength_block_score must not exceed watch threshold",
            )
        for field_name in ("claim_memory_latency_seconds", "resolution_latency_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("claim_status", self.claim_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_flags("row", self)
        _check_row(self)
        expected_digest = _row_digest(self)
        if self.derived_validation_digest:
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest mismatch")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


@dataclass(frozen=True)
class ResearchEventResolutionClaimMemoryLatencyReport:
    generated_at: datetime
    config_version: str
    claim_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchEventResolutionClaimMemoryLatencyRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionClaimMemoryLatencyReport:
            raise ValueError("report must be a ResearchEventResolutionClaimMemoryLatencyReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_text("config_version", self.config_version)
        for field_name in ("claim_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_flags("report", self)
        _check_report(self)
        for row in self.rows:
            _require_row_digest(row)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest:
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest mismatch")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_research_event_resolution_claim_memory_latency_report(
    claims: object,
    *,
    config: ResearchEventResolutionClaimMemoryLatencyReportConfig,
    generated_at: datetime,
) -> ResearchEventResolutionClaimMemoryLatencyReport:
    if type(config) is not ResearchEventResolutionClaimMemoryLatencyReportConfig:
        raise ValueError(
            "config must be a ResearchEventResolutionClaimMemoryLatencyReportConfig",
        )
    _require_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    items = _normalize_inputs(claims)
    seen = set()
    for item in items:
        if item.claim_observed_at > generated_at:
            raise ValueError("claim_observed_at must not be after generated_at")
        if item.memory_recorded_at > generated_at:
            raise ValueError("memory_recorded_at must not be after generated_at")
        if item.resolved_at is not None and item.resolved_at > generated_at:
            raise ValueError("resolved_at must not be after generated_at")
        item_key = (item.private_subject_ref, item.private_event_ref)
        if item_key in seen:
            raise ValueError("claims must not contain duplicate values")
        seen.add(item_key)
    rows = tuple(
        sorted(
            (
                _row_for_claim(
                    item,
                    config=config,
                    generated_at=generated_at,
                )
                for item in items
            ),
            key=_row_sort_key,
        ),
    )
    return ResearchEventResolutionClaimMemoryLatencyReport(
        generated_at=generated_at,
        config_version=config.config_version,
        claim_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_event_resolution_claim_memory_latency_report_payload(
    report: ResearchEventResolutionClaimMemoryLatencyReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchEventResolutionClaimMemoryLatencyReport:
        _require_flags("report", report)
        _require_report_digest(report)
        _reject_unsafe_public("report", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _verify_report_payload(payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_public("payload", report)
        _reject_raw_public_numbers("payload", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _verify_report_payload(payload)
        _reject_unsafe_public("payload", payload)
        return payload
    raise ValueError("report must be a ResearchEventResolutionClaimMemoryLatencyReport")


def _row_for_claim(
    item: ResearchEventResolutionClaimMemoryLatencyInput,
    *,
    config: ResearchEventResolutionClaimMemoryLatencyReportConfig,
    generated_at: datetime,
) -> ResearchEventResolutionClaimMemoryLatencyRow:
    memory_seconds = _age_seconds(
        "claim_observed_at",
        item.memory_recorded_at,
        item.claim_observed_at,
    )
    resolution_seconds = _age_seconds(
        "claim_observed_at",
        item.resolved_at or generated_at,
        item.claim_observed_at,
    )
    latency_score = _average(
        (
            _inverse_threshold_score(
                memory_seconds,
                config.memory_latency_block_seconds,
            ),
            _inverse_threshold_score(
                resolution_seconds,
                config.resolution_latency_watch_seconds,
            ),
        ),
    )
    reason_codes = _row_reason_codes(
        item,
        memory_seconds=memory_seconds,
        resolution_seconds=resolution_seconds,
        config=config,
    )
    return ResearchEventResolutionClaimMemoryLatencyRow(
        row_ref=_claim_ref(item),
        claim_observed_at=item.claim_observed_at,
        memory_recorded_at=item.memory_recorded_at,
        resolved_at=item.resolved_at,
        memory_latency_watch_seconds=config.memory_latency_watch_seconds,
        memory_latency_block_seconds=config.memory_latency_block_seconds,
        resolution_latency_watch_seconds=config.resolution_latency_watch_seconds,
        resolution_latency_block_seconds=config.resolution_latency_block_seconds,
        parser_confidence_watch_score=config.parser_confidence_watch_score,
        parser_confidence_block_score=config.parser_confidence_block_score,
        claim_strength_watch_score=config.claim_strength_watch_score,
        claim_strength_block_score=config.claim_strength_block_score,
        claim_memory_latency_seconds=memory_seconds,
        resolution_latency_seconds=resolution_seconds,
        parser_confidence=item.parser_confidence,
        claim_strength=item.claim_strength,
        latency_score=latency_score,
        claim_status=_status_for_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: ResearchEventResolutionClaimMemoryLatencyInput,
    *,
    memory_seconds: Decimal,
    resolution_seconds: Decimal,
    config: ResearchEventResolutionClaimMemoryLatencyReportConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    status = "pass"
    if (
        memory_seconds >= config.memory_latency_block_seconds
        or resolution_seconds >= config.resolution_latency_block_seconds
        or item.parser_confidence <= config.parser_confidence_block_score
        or item.claim_strength <= config.claim_strength_block_score
    ):
        status = "block"
    elif (
        memory_seconds >= config.memory_latency_watch_seconds
        or resolution_seconds >= config.resolution_latency_watch_seconds
        or item.parser_confidence <= config.parser_confidence_watch_score
        or item.claim_strength <= config.claim_strength_watch_score
    ):
        status = "watch"

    reasons.append(f"claim_memory_latency_{status}")
    if memory_seconds >= config.memory_latency_block_seconds:
        reasons.append("memory_seen_latency_block")
    elif memory_seconds >= config.memory_latency_watch_seconds:
        reasons.append("memory_seen_latency_watch")
    if resolution_seconds >= config.resolution_latency_block_seconds:
        reasons.append("resolution_latency_block")
    elif resolution_seconds >= config.resolution_latency_watch_seconds:
        reasons.append("resolution_latency_watch")
    if item.parser_confidence <= config.parser_confidence_block_score:
        reasons.append("parser_confidence_block")
    elif item.parser_confidence <= config.parser_confidence_watch_score:
        reasons.append("parser_confidence_watch")
    if item.claim_strength <= config.claim_strength_block_score:
        reasons.append("claim_strength_block")
    elif item.claim_strength <= config.claim_strength_watch_score:
        reasons.append("claim_strength_watch")
    reasons.extend(item.reason_codes)
    return _normalize_reason_codes(tuple(reasons))


def _status_for_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if "claim_memory_latency_block" in reason_codes:
        return "block"
    if "claim_memory_latency_watch" in reason_codes:
        return "watch"
    if "claim_memory_latency_pass" in reason_codes:
        return "pass"
    raise ValueError("reason_codes must include a claim status reason")


def _check_row(row: ResearchEventResolutionClaimMemoryLatencyRow) -> None:
    expected_memory_seconds = _age_seconds(
        "claim_observed_at",
        row.memory_recorded_at,
        row.claim_observed_at,
    )
    expected_resolution_seconds = _age_seconds(
        "claim_observed_at",
        row.resolved_at or row.memory_recorded_at,
        row.claim_observed_at,
    )
    if row.resolved_at is None:
        expected_resolution_seconds = row.resolution_latency_seconds
    if row.claim_memory_latency_seconds != expected_memory_seconds:
        raise ValueError("claim_memory_latency_seconds must match timestamps")
    if row.resolved_at is not None and row.resolution_latency_seconds != expected_resolution_seconds:
        raise ValueError("resolution_latency_seconds must match timestamps")
    expected_latency_score = _average(
        (
            _inverse_threshold_score(
                row.claim_memory_latency_seconds,
                row.memory_latency_block_seconds,
            ),
            _inverse_threshold_score(
                row.resolution_latency_seconds,
                row.resolution_latency_watch_seconds,
            ),
        ),
    )
    if row.latency_score != expected_latency_score:
        raise ValueError("latency_score must match latency inputs")
    expected_status = _row_status_from_fields(row)
    if row.claim_status != expected_status:
        raise ValueError("claim_status must match latency inputs")


def _row_status_from_fields(row: ResearchEventResolutionClaimMemoryLatencyRow) -> str:
    if (
        row.claim_memory_latency_seconds >= row.memory_latency_block_seconds
        or row.resolution_latency_seconds >= row.resolution_latency_block_seconds
        or row.parser_confidence <= row.parser_confidence_block_score
        or row.claim_strength <= row.claim_strength_block_score
    ):
        return "block"
    if (
        row.claim_memory_latency_seconds >= row.memory_latency_watch_seconds
        or row.resolution_latency_seconds >= row.resolution_latency_watch_seconds
        or row.parser_confidence <= row.parser_confidence_watch_score
        or row.claim_strength <= row.claim_strength_watch_score
    ):
        return "watch"
    return "pass"


def _check_report(report: ResearchEventResolutionClaimMemoryLatencyReport) -> None:
    expected_count = _count(len(report.rows))
    if report.claim_count != expected_count:
        raise ValueError("claim_count must match rows")
    expected_pass_count = _status_count(report.rows, "pass")
    if report.pass_count != expected_pass_count:
        raise ValueError("pass_count must match rows")
    expected_watch_count = _status_count(report.rows, "watch")
    if report.watch_count != expected_watch_count:
        raise ValueError("watch_count must match rows")
    expected_block_count = _status_count(report.rows, "block")
    if report.block_count != expected_block_count:
        raise ValueError("block_count must match rows")
    expected_status = _report_status(report.rows)
    if report.status != expected_status:
        raise ValueError("status must match rows")
    expected_reason_codes = _report_reason_codes(report.rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    if tuple(sorted(report.rows, key=_row_sort_key)) != report.rows:
        raise ValueError("rows must be sorted deterministically")
    for row in report.rows:
        if row.resolved_at is None:
            expected_resolution_seconds = _age_seconds(
                "claim_observed_at",
                report.generated_at,
                row.claim_observed_at,
            )
            if row.resolution_latency_seconds != expected_resolution_seconds:
                raise ValueError(
                    "resolution_latency_seconds must match generated_at for unresolved claims",
                )


def _report_status(rows: tuple[ResearchEventResolutionClaimMemoryLatencyRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.claim_status == "block" for row in rows):
        return "block"
    if any(row.claim_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchEventResolutionClaimMemoryLatencyRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    return tuple(
        sorted(
            {
                reason
                for row in rows
                for reason in row.reason_codes
                if reason in OWNED_REASON_CODES
            },
            key=lambda reason: REASON_RANK[reason],
        ),
    )


def _row_sort_key(row: ResearchEventResolutionClaimMemoryLatencyRow) -> tuple[int, str]:
    return (STATUS_RANK[row.claim_status], row.row_ref)


def _status_count(
    rows: tuple[ResearchEventResolutionClaimMemoryLatencyRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.claim_status == status))


def _claim_ref(item: ResearchEventResolutionClaimMemoryLatencyInput) -> str:
    material = {
        "a": item.private_subject_ref,
        "b": item.private_event_ref,
        "c": item.private_evidence_locator,
        "d": item.private_evidence_excerpt,
        "e": item.private_store_locator,
        "f": item.private_set_name,
        "g": item.private_secret_marker,
    }
    return sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()


def _normalize_inputs(claims: object) -> tuple[ResearchEventResolutionClaimMemoryLatencyInput, ...]:
    if claims is None:
        raise ValueError("claims must be a list or tuple")
    if not isinstance(claims, (list, tuple)):
        raise ValueError("claims must be a list or tuple")
    items = tuple(claims)
    for item in items:
        if type(item) is not ResearchEventResolutionClaimMemoryLatencyInput:
            raise ValueError(
                "claims must contain ResearchEventResolutionClaimMemoryLatencyInput items",
            )
    return items


def _normalize_rows(rows: object) -> tuple[ResearchEventResolutionClaimMemoryLatencyRow, ...]:
    if not isinstance(rows, (list, tuple)):
        raise ValueError("rows must be a list or tuple")
    result = tuple(rows)
    for row in result:
        if type(row) is not ResearchEventResolutionClaimMemoryLatencyRow:
            raise ValueError("rows must contain ResearchEventResolutionClaimMemoryLatencyRow items")
    return result


def _require_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_text(field_name: str, value: object) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def _require_digest_text(field_name: str, value: object) -> None:
    _require_text(field_name, value)
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex string")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex string")


def _require_status(field_name: str, value: object) -> None:
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_less_than(field_name: str, lower: Decimal, upper: Decimal) -> None:
    if lower >= upper:
        raise ValueError(f"{field_name} must be less than block threshold")


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return _quantize(value)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(value)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _age_seconds(field_name: str, later_at: datetime, earlier_at: datetime) -> Decimal:
    delta = later_at - earlier_at
    if delta.days < 0:
        raise ValueError(f"{field_name} must not be after comparison timestamp")
    return _quantize(
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + Decimal(delta.microseconds) / MICROS_PER_SECOND,
    )


def _inverse_threshold_score(value: Decimal, block_threshold: Decimal) -> Decimal:
    return _clamp_ratio(ONE - _clamp_ratio(value / block_threshold))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _clamp_ratio(value: Decimal) -> Decimal:
    value = _quantize(value)
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_text("reason_codes", reason_code)
    if len(reason_codes) != len(set(reason_codes)):
        raise ValueError("reason_codes must not contain duplicate values")
    return reason_codes


def _json_ready(value: object) -> object:
    if is_dataclass(value):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        return format(_quantize(value), "f")
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("payload values must be JSON primitives, Decimal|string, or containers")


def _row_digest(row: ResearchEventResolutionClaimMemoryLatencyRow) -> str:
    payload = _json_ready(row)
    if type(payload) is not dict:
        raise ValueError("row payload must be a JSON object")
    payload["derived_validation_digest"] = ""
    return _digest_payload(payload)


def _report_digest(report: ResearchEventResolutionClaimMemoryLatencyReport) -> str:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload["derived_validation_digest"] = ""
    return _digest_payload(payload)


def _digest_payload(payload: dict[str, object]) -> str:
    return sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8"),
    ).hexdigest()


def _require_row_digest(row: ResearchEventResolutionClaimMemoryLatencyRow) -> None:
    if row.derived_validation_digest != _row_digest(row):
        raise ValueError("derived_validation_digest mismatch")


def _require_report_digest(report: ResearchEventResolutionClaimMemoryLatencyReport) -> None:
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest mismatch")


def _verify_report_payload(payload: dict[str, Any]) -> None:
    _verify_keys("report", payload, REPORT_KEYS)
    _verify_payload_flags("report", payload)
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain objects")
        _verify_row_payload(row)
    expected_digest = _digest_payload({**payload, "derived_validation_digest": ""})
    if payload["derived_validation_digest"] != expected_digest:
        raise ValueError("derived_validation_digest mismatch")


def _verify_row_payload(payload: dict[str, Any]) -> None:
    _verify_keys("row", payload, ROW_KEYS)
    _verify_payload_flags("row", payload)
    expected_digest = _digest_payload({**payload, "derived_validation_digest": ""})
    if payload["derived_validation_digest"] != expected_digest:
        raise ValueError("derived_validation_digest mismatch")


def _verify_keys(label: str, payload: dict[str, Any], expected_keys: tuple[str, ...]) -> None:
    if tuple(payload.keys()) != expected_keys:
        raise ValueError(f"{label} payload keys must match schema")


def _verify_payload_flags(label: str, payload: dict[str, Any]) -> None:
    if payload.get("paper_only") is not True:
        raise ValueError(f"{label} paper_only must be True")
    if payload.get("report_only") is not True:
        raise ValueError(f"{label} report_only must be True")
    if payload.get("readonly") is not True:
        raise ValueError(f"{label} readonly must be True")


def _reject_raw_public_numbers(label: str, value: object) -> None:
    if type(value) in (float, int):
        raise ValueError(f"{label} payload values must use Decimal|string")
    if isinstance(value, dict):
        for item in value.values():
            _reject_raw_public_numbers(label, item)
    elif isinstance(value, list):
        for item in value:
            _reject_raw_public_numbers(label, item)


def _reject_unsafe_public(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_text(label, str(key))
            _reject_unsafe_public(label, item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public(label, item)
    elif isinstance(value, str):
        _reject_unsafe_text(label, value)


def _reject_unsafe_text(label: str, value: str) -> None:
    lowered = value.lower()
    if len(lowered) == 64 and all(character in "0123456789abcdef" for character in lowered):
        return
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{label} contains unsafe public payload content")
