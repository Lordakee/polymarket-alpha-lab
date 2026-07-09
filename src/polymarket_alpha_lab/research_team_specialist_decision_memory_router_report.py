"""Pure report-only team specialist decision memory router."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
from typing import Any, Mapping

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_RESEARCH_TEAM_SPECIALIST_DECISION_MEMORY_ROUTER_REPORT_CONFIG_VERSION = (
    "research-team-specialist-decision-memory-router-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
TEAM_SPECIALIST_DECISION_MEMORY_ROUTER_STATUSES = (
    STATUS_PASS,
    STATUS_WATCH,
    STATUS_BLOCK,
)

ZERO = Decimal("0")
ONE = Decimal("1")
QUANT = Decimal("0.000001")
DIGEST_HEX_LENGTH = 64

MEMORY_MATCH_BLOCK_REASON = (
    "team_specialist_decision_memory_router_memory_match_block"
)
DECISION_CONTEXT_BLOCK_REASON = (
    "team_specialist_decision_memory_router_decision_context_block"
)
CONTRADICTION_BLOCK_REASON = (
    "team_specialist_decision_memory_router_contradiction_block"
)
FRESHNESS_BLOCK_REASON = "team_specialist_decision_memory_router_freshness_block"
REVIEW_LOAD_BLOCK_REASON = "team_specialist_decision_memory_router_review_load_block"
MEMORY_MATCH_WATCH_REASON = (
    "team_specialist_decision_memory_router_memory_match_watch"
)
DECISION_CONTEXT_WATCH_REASON = (
    "team_specialist_decision_memory_router_decision_context_watch"
)
CONTRADICTION_WATCH_REASON = (
    "team_specialist_decision_memory_router_contradiction_watch"
)
FRESHNESS_WATCH_REASON = "team_specialist_decision_memory_router_freshness_watch"
REVIEW_LOAD_WATCH_REASON = "team_specialist_decision_memory_router_review_load_watch"
READY_REASON = "team_specialist_decision_memory_router_ready"
EMPTY_REASON = "team_specialist_decision_memory_router_empty"
BLOCK_PRESENT_REASON = (
    "team_specialist_decision_memory_router_block_specialists_present"
)
WATCH_PRESENT_REASON = (
    "team_specialist_decision_memory_router_watch_specialists_present"
)

ROW_REASON_SEQUENCE = (
    MEMORY_MATCH_BLOCK_REASON,
    DECISION_CONTEXT_BLOCK_REASON,
    CONTRADICTION_BLOCK_REASON,
    FRESHNESS_BLOCK_REASON,
    REVIEW_LOAD_BLOCK_REASON,
    MEMORY_MATCH_WATCH_REASON,
    DECISION_CONTEXT_WATCH_REASON,
    CONTRADICTION_WATCH_REASON,
    FRESHNESS_WATCH_REASON,
    REVIEW_LOAD_WATCH_REASON,
    READY_REASON,
)
REPORT_REASON_SEQUENCE = (
    BLOCK_PRESENT_REASON,
    WATCH_PRESENT_REASON,
    READY_REASON,
    EMPTY_REASON,
)


def _join(*parts: str) -> str:
    return "".join(parts)


PUBLIC_LABEL_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_.-")
UNSAFE_PUBLIC_PARTS = frozenset(
    (
        _join("ra", "w"),
        _join("can", "didate"),
        _join("mar", "ket"),
        _join("s", "lug"),
        _join("ques", "tion"),
        _join("source", "_", "u", "r", "l"),
        _join("source", "_", "text"),
        _join("h", "t", "t", "p", "://"),
        _join("h", "t", "t", "p", "s", "://"),
        _join("d", "s", "n"),
        _join("ta", "ble"),
        _join("to", "ken"),
        _join("wal", "let"),
        _join("or", "der"),
        _join("tra", "de"),
        _join("li", "ve"),
        _join("siz", "ing"),
        _join("reco", "mmendation"),
        _join("sec", "ret"),
        _join("cred", "ential"),
        _join("priv", "ate"),
        _join("data", "base"),
        _join("net", "work"),
        _join("au", "th"),
        _join("b", "uy"),
        _join("s", "ell"),
    ),
)


__all__ = (
    "DEFAULT_RESEARCH_TEAM_SPECIALIST_DECISION_MEMORY_ROUTER_REPORT_CONFIG_VERSION",
    "ResearchTeamSpecialistDecisionMemoryRouterConfig",
    "ResearchTeamSpecialistDecisionMemoryRouterInput",
    "ResearchTeamSpecialistDecisionMemoryRouterReasonCodeCount",
    "ResearchTeamSpecialistDecisionMemoryRouterReport",
    "ResearchTeamSpecialistDecisionMemoryRouterRow",
    "build_research_team_specialist_decision_memory_router_report",
    "research_team_specialist_decision_memory_router_report_payload",
)


@dataclass(frozen=True)
class ResearchTeamSpecialistDecisionMemoryRouterConfig:
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_SPECIALIST_DECISION_MEMORY_ROUTER_REPORT_CONFIG_VERSION
    )
    min_pass_memory_match_score: Decimal = Decimal("0.750000")
    min_watch_memory_match_score: Decimal = Decimal("0.500000")
    min_pass_decision_context_score: Decimal = Decimal("0.750000")
    min_watch_decision_context_score: Decimal = Decimal("0.500000")
    max_pass_contradiction_pressure: Decimal = Decimal("0.500000")
    max_watch_contradiction_pressure: Decimal = Decimal("0.600000")
    min_pass_freshness_score: Decimal = Decimal("0.600000")
    min_watch_freshness_score: Decimal = Decimal("0.500000")
    max_pass_review_load_ratio: Decimal = Decimal("0.500000")
    max_watch_review_load_ratio: Decimal = Decimal("0.900000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistDecisionMemoryRouterConfig,
            "config",
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_label("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_SPECIALIST_DECISION_MEMORY_ROUTER_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "min_pass_memory_match_score",
            "min_watch_memory_match_score",
            "min_pass_decision_context_score",
            "min_watch_decision_context_score",
            "max_pass_contradiction_pressure",
            "max_watch_contradiction_pressure",
            "min_pass_freshness_score",
            "min_watch_freshness_score",
            "max_pass_review_load_ratio",
            "max_watch_review_load_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_watch_memory_match_score > self.min_pass_memory_match_score:
            raise ValueError("min_watch_memory_match_score must not exceed pass")
        if self.min_watch_decision_context_score > self.min_pass_decision_context_score:
            raise ValueError("min_watch_decision_context_score must not exceed pass")
        if self.max_pass_contradiction_pressure > self.max_watch_contradiction_pressure:
            raise ValueError("max_pass_contradiction_pressure must not exceed watch")
        if self.min_watch_freshness_score > self.min_pass_freshness_score:
            raise ValueError("min_watch_freshness_score must not exceed pass")
        if self.max_pass_review_load_ratio > self.max_watch_review_load_ratio:
            raise ValueError("max_pass_review_load_ratio must not exceed watch")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistDecisionMemoryRouterInput:
    specialist_label: str
    memory_match_score: Decimal
    decision_context_score: Decimal
    contradiction_pressure: Decimal
    freshness_score: Decimal
    pending_review_load: Decimal
    review_capacity: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistDecisionMemoryRouterInput,
            "router_input",
        )
        object.__setattr__(
            self,
            "specialist_label",
            _require_public_label("specialist_label", self.specialist_label),
        )
        for field_name in (
            "memory_match_score",
            "decision_context_score",
            "contradiction_pressure",
            "freshness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "pending_review_load",
            _require_nonnegative_decimal(
                "pending_review_load",
                self.pending_review_load,
            ),
        )
        object.__setattr__(
            self,
            "review_capacity",
            _require_positive_decimal("review_capacity", self.review_capacity),
        )
        _validate_capacity_bounds(self)
        _require_hard_flags("router_input", self)
        _reject_unsafe_public_payload("router_input", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistDecisionMemoryRouterRow:
    specialist_label: str
    memory_match_score: Decimal
    decision_context_score: Decimal
    contradiction_pressure: Decimal
    freshness_score: Decimal
    pending_review_load: Decimal
    review_capacity: Decimal
    review_load_ratio: Decimal
    router_score: Decimal
    router_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSpecialistDecisionMemoryRouterRow, "row")
        object.__setattr__(
            self,
            "specialist_label",
            _require_public_label("specialist_label", self.specialist_label),
        )
        for field_name in (
            "memory_match_score",
            "decision_context_score",
            "contradiction_pressure",
            "freshness_score",
            "review_load_ratio",
            "router_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "pending_review_load",
            _require_nonnegative_decimal(
                "pending_review_load",
                self.pending_review_load,
            ),
        )
        object.__setattr__(
            self,
            "review_capacity",
            _require_positive_decimal("review_capacity", self.review_capacity),
        )
        _require_status("router_status", self.router_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, ROW_REASON_SEQUENCE),
        )
        _validate_capacity_bounds(self)
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistDecisionMemoryRouterReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistDecisionMemoryRouterReasonCodeCount,
            "reason_code_count",
        )
        object.__setattr__(
            self,
            "reason_code",
            _require_public_label("reason_code", self.reason_code),
        )
        if self.reason_code not in ROW_REASON_SEQUENCE:
            raise ValueError("reason_code must be supported")
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistDecisionMemoryRouterReport:
    generated_at: datetime
    config_version: str
    router_status: str
    specialist_count: Decimal
    pass_specialist_count: Decimal
    watch_specialist_count: Decimal
    block_specialist_count: Decimal
    average_router_score: Decimal
    lowest_router_score: Decimal
    lowest_memory_match_score: Decimal
    lowest_decision_context_score: Decimal
    max_contradiction_pressure: Decimal
    lowest_freshness_score: Decimal
    max_review_load_ratio: Decimal
    rows: tuple[ResearchTeamSpecialistDecisionMemoryRouterRow, ...]
    reason_code_counts: tuple[
        ResearchTeamSpecialistDecisionMemoryRouterReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_label("config_version", self.config_version),
        )
        _require_status("router_status", self.router_status)
        for field_name in (
            "specialist_count",
            "pass_specialist_count",
            "watch_specialist_count",
            "block_specialist_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_router_score",
            "lowest_router_score",
            "lowest_memory_match_score",
            "lowest_decision_context_score",
            "max_contradiction_pressure",
            "lowest_freshness_score",
            "max_review_load_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, REPORT_REASON_SEQUENCE),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, Any]:
        payload = _json_ready(asdict(self))
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        _require_payload_hard_flags(payload)
        _validate_payload_digest(payload)
        _reject_unsafe_public_payload("payload", payload)
        return payload


def build_research_team_specialist_decision_memory_router_report(
    router_inputs: list[ResearchTeamSpecialistDecisionMemoryRouterInput]
    | tuple[ResearchTeamSpecialistDecisionMemoryRouterInput, ...],
    *,
    config: ResearchTeamSpecialistDecisionMemoryRouterConfig,
    generated_at: datetime,
) -> ResearchTeamSpecialistDecisionMemoryRouterReport:
    if type(config) is not ResearchTeamSpecialistDecisionMemoryRouterConfig:
        raise ValueError(
            "config must be a ResearchTeamSpecialistDecisionMemoryRouterConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(router_inputs)
    rows = tuple(_row_for_input(row, config) for row in inputs)
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "router_status": _status_from_report_reason_codes(reason_codes),
        "specialist_count": _decimal_count(len(rows)),
        "pass_specialist_count": _status_count(rows, STATUS_PASS),
        "watch_specialist_count": _status_count(rows, STATUS_WATCH),
        "block_specialist_count": _status_count(rows, STATUS_BLOCK),
        "average_router_score": _average(rows, "router_score"),
        "lowest_router_score": _minimum(rows, "router_score"),
        "lowest_memory_match_score": _minimum(rows, "memory_match_score"),
        "lowest_decision_context_score": _minimum(rows, "decision_context_score"),
        "max_contradiction_pressure": _maximum(rows, "contradiction_pressure"),
        "lowest_freshness_score": _minimum(rows, "freshness_score"),
        "max_review_load_ratio": _maximum(rows, "review_load_ratio"),
        "rows": rows,
        "reason_code_counts": _reason_code_counts(rows),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchTeamSpecialistDecisionMemoryRouterReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_team_specialist_decision_memory_router_report_payload(
    report: ResearchTeamSpecialistDecisionMemoryRouterReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamSpecialistDecisionMemoryRouterReport:
        _require_hard_flags("report", report)
        payload = report.payload
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchTeamSpecialistDecisionMemoryRouterReport or payload",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _require_payload_hard_flags(payload)
    _validate_payload_digest(payload)
    _reject_unsafe_public_payload("payload", payload)
    return payload


def _row_for_input(
    row: ResearchTeamSpecialistDecisionMemoryRouterInput,
    config: ResearchTeamSpecialistDecisionMemoryRouterConfig,
) -> ResearchTeamSpecialistDecisionMemoryRouterRow:
    review_load_ratio = _ratio(row.pending_review_load, row.review_capacity)
    router_score = (
        row.memory_match_score
        + row.decision_context_score
        + (ONE - row.contradiction_pressure)
        + row.freshness_score
        + (ONE - review_load_ratio)
    ) / Decimal("5")
    reason_codes = _row_reason_codes(row, review_load_ratio, config)
    return ResearchTeamSpecialistDecisionMemoryRouterRow(
        specialist_label=row.specialist_label,
        memory_match_score=row.memory_match_score,
        decision_context_score=row.decision_context_score,
        contradiction_pressure=row.contradiction_pressure,
        freshness_score=row.freshness_score,
        pending_review_load=row.pending_review_load,
        review_capacity=row.review_capacity,
        review_load_ratio=review_load_ratio,
        router_score=router_score.quantize(QUANT),
        router_status=_status_from_row_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    row: ResearchTeamSpecialistDecisionMemoryRouterInput,
    review_load_ratio: Decimal,
    config: ResearchTeamSpecialistDecisionMemoryRouterConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if row.memory_match_score < config.min_watch_memory_match_score:
        reason_codes.append(MEMORY_MATCH_BLOCK_REASON)
    if row.decision_context_score < config.min_watch_decision_context_score:
        reason_codes.append(DECISION_CONTEXT_BLOCK_REASON)
    if row.contradiction_pressure > config.max_watch_contradiction_pressure:
        reason_codes.append(CONTRADICTION_BLOCK_REASON)
    if row.freshness_score < config.min_watch_freshness_score:
        reason_codes.append(FRESHNESS_BLOCK_REASON)
    if review_load_ratio > config.max_watch_review_load_ratio:
        reason_codes.append(REVIEW_LOAD_BLOCK_REASON)
    if reason_codes:
        return tuple(reason_codes)
    if row.memory_match_score < config.min_pass_memory_match_score:
        reason_codes.append(MEMORY_MATCH_WATCH_REASON)
    if row.decision_context_score < config.min_pass_decision_context_score:
        reason_codes.append(DECISION_CONTEXT_WATCH_REASON)
    if row.contradiction_pressure > config.max_pass_contradiction_pressure:
        reason_codes.append(CONTRADICTION_WATCH_REASON)
    if row.freshness_score < config.min_pass_freshness_score:
        reason_codes.append(FRESHNESS_WATCH_REASON)
    if review_load_ratio > config.max_pass_review_load_ratio:
        reason_codes.append(REVIEW_LOAD_WATCH_REASON)
    if reason_codes:
        return tuple(reason_codes)
    return (READY_REASON,)


def _report_reason_codes(
    rows: tuple[ResearchTeamSpecialistDecisionMemoryRouterRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    reason_codes: list[str] = []
    if any(row.router_status == STATUS_BLOCK for row in rows):
        reason_codes.append(BLOCK_PRESENT_REASON)
    if any(row.router_status == STATUS_WATCH for row in rows):
        reason_codes.append(WATCH_PRESENT_REASON)
    if not reason_codes:
        reason_codes.append(READY_REASON)
    return tuple(reason_codes)


def _status_from_row_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return STATUS_BLOCK
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return STATUS_WATCH
    return STATUS_PASS


def _status_from_report_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if BLOCK_PRESENT_REASON in reason_codes or EMPTY_REASON in reason_codes:
        return STATUS_BLOCK
    if WATCH_PRESENT_REASON in reason_codes:
        return STATUS_WATCH
    return STATUS_PASS


def _reason_code_counts(
    rows: tuple[ResearchTeamSpecialistDecisionMemoryRouterRow, ...],
) -> tuple[ResearchTeamSpecialistDecisionMemoryRouterReasonCodeCount, ...]:
    all_reason_codes = tuple(reason_code for row in rows for reason_code in row.reason_codes)
    return tuple(
        ResearchTeamSpecialistDecisionMemoryRouterReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(all_reason_codes.count(reason_code)),
        )
        for reason_code in ROW_REASON_SEQUENCE
        if reason_code in all_reason_codes
    )


def _normalize_inputs(
    value: object,
) -> tuple[ResearchTeamSpecialistDecisionMemoryRouterInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("router_inputs must be a list or tuple")
    rows = tuple(value)
    seen_labels: set[str] = set()
    for row in rows:
        if type(row) is not ResearchTeamSpecialistDecisionMemoryRouterInput:
            raise ValueError("router_inputs must contain router input values")
        _require_hard_flags("router_input", row)
        if row.specialist_label in seen_labels:
            raise ValueError("specialist_label values must be unique")
        seen_labels.add(row.specialist_label)
    return tuple(sorted(rows, key=lambda row: row.specialist_label))


def _normalize_rows(
    value: object,
) -> tuple[ResearchTeamSpecialistDecisionMemoryRouterRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_labels: set[str] = set()
    for row in rows:
        if type(row) is not ResearchTeamSpecialistDecisionMemoryRouterRow:
            raise ValueError("rows must contain row values")
        _require_hard_flags("row", row)
        if row.specialist_label in seen_labels:
            raise ValueError("specialist_label values must be unique")
        seen_labels.add(row.specialist_label)
    return tuple(sorted(rows, key=lambda row: row.specialist_label))


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchTeamSpecialistDecisionMemoryRouterReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    rows = tuple(value)
    seen_reason_codes: set[str] = set()
    for row in rows:
        if type(row) is not ResearchTeamSpecialistDecisionMemoryRouterReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count values")
        if row.reason_code in seen_reason_codes:
            raise ValueError("reason_code values must be unique")
        seen_reason_codes.add(row.reason_code)
        _require_hard_flags("reason_code_count", row)
    expected = tuple(row for code in ROW_REASON_SEQUENCE for row in rows if row.reason_code == code)
    if rows != expected:
        raise ValueError("reason_code_counts must be deterministic")
    return rows


def _normalize_reason_codes(
    value: object,
    supported_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must contain at least one value")
    for reason_code in reason_codes:
        _require_public_label("reason_code", reason_code)
        if reason_code not in supported_reason_codes:
            raise ValueError("reason_codes must contain supported values")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    expected = tuple(code for code in supported_reason_codes if code in reason_codes)
    if reason_codes != expected:
        raise ValueError("reason_codes must be deterministic")
    return reason_codes


def _validate_capacity_bounds(
    value: ResearchTeamSpecialistDecisionMemoryRouterInput
    | ResearchTeamSpecialistDecisionMemoryRouterRow,
) -> None:
    if value.pending_review_load > value.review_capacity:
        raise ValueError("pending_review_load must not exceed review_capacity")


def _validate_row_consistency(
    row: ResearchTeamSpecialistDecisionMemoryRouterRow,
) -> None:
    if row.review_load_ratio != _ratio(row.pending_review_load, row.review_capacity):
        raise ValueError("review_load_ratio must match review values")
    expected_score = (
        row.memory_match_score
        + row.decision_context_score
        + (ONE - row.contradiction_pressure)
        + row.freshness_score
        + (ONE - row.review_load_ratio)
    ) / Decimal("5")
    if row.router_score != expected_score.quantize(QUANT):
        raise ValueError("router_score must match component values")
    if row.router_status != _status_from_row_reason_codes(row.reason_codes):
        raise ValueError("router_status must match reason_codes")


def _validate_report_consistency(
    report: ResearchTeamSpecialistDecisionMemoryRouterReport,
) -> None:
    if report.specialist_count != _decimal_count(len(report.rows)):
        raise ValueError("specialist_count must match rows")
    if report.pass_specialist_count != _status_count(report.rows, STATUS_PASS):
        raise ValueError("pass_specialist_count must match rows")
    if report.watch_specialist_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_specialist_count must match rows")
    if report.block_specialist_count != _status_count(report.rows, STATUS_BLOCK):
        raise ValueError("block_specialist_count must match rows")
    if report.average_router_score != _average(report.rows, "router_score"):
        raise ValueError("average_router_score must match rows")
    if report.lowest_router_score != _minimum(report.rows, "router_score"):
        raise ValueError("lowest_router_score must match rows")
    if report.lowest_memory_match_score != _minimum(report.rows, "memory_match_score"):
        raise ValueError("lowest_memory_match_score must match rows")
    if report.lowest_decision_context_score != _minimum(
        report.rows,
        "decision_context_score",
    ):
        raise ValueError("lowest_decision_context_score must match rows")
    if report.max_contradiction_pressure != _maximum(
        report.rows,
        "contradiction_pressure",
    ):
        raise ValueError("max_contradiction_pressure must match rows")
    if report.lowest_freshness_score != _minimum(report.rows, "freshness_score"):
        raise ValueError("lowest_freshness_score must match rows")
    if report.max_review_load_ratio != _maximum(report.rows, "review_load_ratio"):
        raise ValueError("max_review_load_ratio must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.router_status != _status_from_report_reason_codes(report.reason_codes):
        raise ValueError("router_status must match reason_codes")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _status_count(
    rows: tuple[ResearchTeamSpecialistDecisionMemoryRouterRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.router_status == status))


def _average(
    rows: tuple[ResearchTeamSpecialistDecisionMemoryRouterRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO.quantize(QUANT)
    return (
        sum((getattr(row, field_name) for row in rows), ZERO) / Decimal(len(rows))
    ).quantize(QUANT)


def _minimum(
    rows: tuple[ResearchTeamSpecialistDecisionMemoryRouterRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO.quantize(QUANT)
    return min(getattr(row, field_name) for row in rows).quantize(QUANT)


def _maximum(
    rows: tuple[ResearchTeamSpecialistDecisionMemoryRouterRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO.quantize(QUANT)
    return max(getattr(row, field_name) for row in rows).quantize(QUANT)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("ratio denominator must be positive")
    return (numerator / denominator).quantize(QUANT)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in TEAM_SPECIALIST_DECISION_MEMORY_ROUTER_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    lowered = value.lower()
    if any(character not in PUBLIC_LABEL_CHARS for character in lowered):
        raise ValueError(f"{field_name} must be public")
    if any(part in lowered for part in UNSAFE_PUBLIC_PARTS):
        raise ValueError(f"{field_name} must be public")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANT)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    if len(value) != DIGEST_HEX_LENGTH:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")


def _require_hard_flags(label: str, value: object) -> None:
    require_paper_only_flags(label, value)
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label}.report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label}.readonly must be True")


def _require_payload_hard_flags(value: object, path: str = "payload") -> None:
    if type(value) is dict:
        has_any_flag = any(key in value for key in ("paper_only", "report_only", "readonly"))
        if has_any_flag:
            for key in ("paper_only", "report_only", "readonly"):
                if value.get(key) is not True:
                    raise ValueError(f"{path}.{key} must be True")
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _require_payload_hard_flags(nested_value, f"{path}.{key}")
    elif type(value) is list:
        for index, nested_value in enumerate(value):
            _require_payload_hard_flags(nested_value, f"{path}[{index}]")


def _report_values_without_digest(
    report: ResearchTeamSpecialistDecisionMemoryRouterReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload("digest_payload", payload)
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    if digest != _report_digest_from_values(digest_payload):
        raise ValueError("derived_validation_digest must match payload")


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value.quantize(QUANT))
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if value is None:
        return None
    if type(value) is bool:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(nested_value)
        return ready
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        if not _is_public_datetime_string(value):
            _require_public_label(path or label, value)
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
        if value.tzinfo is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal")
    if isinstance(value, dict):
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            _require_public_label(item_path, key)
            _reject_unsafe_public_payload(label, nested_value, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, nested_value in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, nested_value, item_path)
        return
    raise ValueError("value is not JSON serializable")


def _is_public_datetime_string(value: str) -> bool:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.astimezone(UTC).isoformat() == value
