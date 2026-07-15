"""Report-only memory evidence edge watch snapshot."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_MEMORY_EVIDENCE_EDGE_WATCH_REPORT_CONFIG_VERSION",
    "ResearchStrategyMemoryEvidenceEdgeWatchConfig",
    "ResearchStrategyMemoryEvidenceEdgeWatchInput",
    "ResearchStrategyMemoryEvidenceEdgeWatchReasonCodeCount",
    "ResearchStrategyMemoryEvidenceEdgeWatchReport",
    "ResearchStrategyMemoryEvidenceEdgeWatchRow",
    "build_research_strategy_memory_evidence_edge_watch_report",
    "research_strategy_memory_evidence_edge_watch_report_digest",
    "research_strategy_memory_evidence_edge_watch_report_payload",
)


DEFAULT_RESEARCH_STRATEGY_MEMORY_EVIDENCE_EDGE_WATCH_REPORT_CONFIG_VERSION = (
    "research-strategy-memory-evidence-edge-watch-report-v0"
)
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
PUBLIC_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
STATUSES = ("pass", "watch", "block")
STATUS_WEIGHT = {
    "block": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
NO_INPUTS_REASON = "memory_evidence_edge_watch_no_inputs"
REPORT_REASON_PRIORITY = (
    "memory_reuse_block",
    "evidence_alignment_block",
    "edge_confidence_block",
    "stale_memory_pressure_block",
    "contradictory_evidence_pressure_block",
    "unresolved_edge_pressure_block",
    "memory_reuse_watch",
    "evidence_alignment_watch",
    "edge_confidence_watch",
    "stale_memory_pressure_watch",
    "contradictory_evidence_pressure_watch",
    "unresolved_edge_pressure_watch",
)
CONFIG_DECIMAL_FIELDS = (
    "memory_pass_floor",
    "memory_watch_floor",
    "evidence_pass_floor",
    "evidence_watch_floor",
    "edge_pass_floor",
    "edge_watch_floor",
    "stale_memory_pressure_watch",
    "stale_memory_pressure_block",
    "contradictory_evidence_pressure_watch",
    "contradictory_evidence_pressure_block",
    "unresolved_edge_pressure_watch",
    "unresolved_edge_pressure_block",
)
INPUT_DECIMAL_FIELDS = (
    "memory_reuse_score",
    "evidence_alignment_score",
    "edge_confidence_score",
    "stale_memory_pressure",
    "contradictory_evidence_pressure",
    "unresolved_edge_pressure",
)
ROW_DECIMAL_FIELDS = (
    "memory_reuse_score",
    "evidence_alignment_score",
    "edge_confidence_score",
    "stale_memory_pressure",
    "contradictory_evidence_pressure",
    "unresolved_edge_pressure",
    "edge_watch_readiness_score",
)
REPORT_COUNT_FIELDS = (
    "memory_edge_count",
    "pass_count",
    "watch_count",
    "block_count",
    "attention_count",
)
REPORT_PROBABILITY_FIELDS = (
    "mean_memory_reuse_score",
    "mean_evidence_alignment_score",
    "mean_edge_confidence_score",
    "mean_edge_watch_readiness_score",
    "max_stale_memory_pressure",
    "max_contradictory_evidence_pressure",
    "max_unresolved_edge_pressure",
)
REPORT_DIGEST_KEYS = (
    "generated_at",
    "config_version",
    "memory_edge_count",
    "pass_count",
    "watch_count",
    "block_count",
    "attention_count",
    "mean_memory_reuse_score",
    "mean_evidence_alignment_score",
    "mean_edge_confidence_score",
    "mean_edge_watch_readiness_score",
    "max_stale_memory_pressure",
    "max_contradictory_evidence_pressure",
    "max_unresolved_edge_pressure",
    "status",
    "reason_codes",
    "reason_code_counts",
    "rows",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_PAYLOAD_KEYS = (
    "generated_at",
    "config_version",
    "memory_edge_count",
    "pass_count",
    "watch_count",
    "block_count",
    "attention_count",
    "mean_memory_reuse_score",
    "mean_evidence_alignment_score",
    "mean_edge_confidence_score",
    "mean_edge_watch_readiness_score",
    "max_stale_memory_pressure",
    "max_contradictory_evidence_pressure",
    "max_unresolved_edge_pressure",
    "status",
    "public_digest",
    "reason_codes",
    "reason_code_counts",
    "rows",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_PAYLOAD_KEYS = (
    "aggregate_row_number",
    "aggregate_row_hash",
    "status",
    "memory_reuse_score",
    "evidence_alignment_score",
    "edge_confidence_score",
    "stale_memory_pressure",
    "contradictory_evidence_pressure",
    "unresolved_edge_pressure",
    "edge_watch_readiness_score",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
REASON_CODE_COUNT_PAYLOAD_KEYS = (
    "reason_code",
    "count",
    "paper_only",
    "report_only",
    "readonly",
)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    _join_parts("raw", "_candidate", "_id"),
    _join_parts("mar", "ket", "_id"),
    _join_parts("mar", "ket", "_sl", "ug"),
    _join_parts("ques", "tion"),
    _join_parts("sou", "rce", "_u", "rl"),
    _join_parts("sou", "rce", "_te", "xt"),
    _join_parts("d", "sn"),
    _join_parts("ta", "ble", "_na", "me"),
    _join_parts("pri", "vate", "_to", "ken"),
    _join_parts("wal", "let"),
    _join_parts("or", "der"),
    _join_parts("tra", "de"),
    _join_parts("tra", "ding"),
    _join_parts("posi", "tion", "_si", "ze"),
    _join_parts("b", "uy"),
    _join_parts("se", "ll"),
    _join_parts("rec", "ommend"),
    _join_parts("siz", "ing"),
    _join_parts("li", "ve"),
    _join_parts("au", "th"),
    _join_parts("data", "base"),
    _join_parts("net", "work"),
    _join_parts("req", "uests"),
    _join_parts("ht", "tp"),
    _join_parts("so", "cket"),
    _join_parts("sub", "process"),
    _join_parts("sec", "ret"),
    _join_parts("api", "_key"),
    "://",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchStrategyMemoryEvidenceEdgeWatchConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_MEMORY_EVIDENCE_EDGE_WATCH_REPORT_CONFIG_VERSION
    )
    memory_pass_floor: Decimal = Decimal("0.750000")
    memory_watch_floor: Decimal = Decimal("0.550000")
    evidence_pass_floor: Decimal = Decimal("0.800000")
    evidence_watch_floor: Decimal = Decimal("0.600000")
    edge_pass_floor: Decimal = Decimal("0.700000")
    edge_watch_floor: Decimal = Decimal("0.500000")
    stale_memory_pressure_watch: Decimal = Decimal("0.400000")
    stale_memory_pressure_block: Decimal = Decimal("0.750000")
    contradictory_evidence_pressure_watch: Decimal = Decimal("0.350000")
    contradictory_evidence_pressure_block: Decimal = Decimal("0.700000")
    unresolved_edge_pressure_watch: Decimal = Decimal("0.400000")
    unresolved_edge_pressure_block: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyMemoryEvidenceEdgeWatchConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_MEMORY_EVIDENCE_EDGE_WATCH_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in CONFIG_DECIMAL_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_at_least("memory_pass_floor", self.memory_pass_floor, self.memory_watch_floor)
        _require_at_least(
            "evidence_pass_floor",
            self.evidence_pass_floor,
            self.evidence_watch_floor,
        )
        _require_at_least("edge_pass_floor", self.edge_pass_floor, self.edge_watch_floor)
        _require_at_most(
            "stale_memory_pressure_watch",
            self.stale_memory_pressure_watch,
            self.stale_memory_pressure_block,
        )
        _require_at_most(
            "contradictory_evidence_pressure_watch",
            self.contradictory_evidence_pressure_watch,
            self.contradictory_evidence_pressure_block,
        )
        _require_at_most(
            "unresolved_edge_pressure_watch",
            self.unresolved_edge_pressure_watch,
            self.unresolved_edge_pressure_block,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyMemoryEvidenceEdgeWatchInput(_FinalPublicDataclass):
    memory_key: str
    memory_reuse_score: Decimal
    evidence_alignment_score: Decimal
    edge_confidence_score: Decimal
    stale_memory_pressure: Decimal
    contradictory_evidence_pressure: Decimal
    unresolved_edge_pressure: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyMemoryEvidenceEdgeWatchInput, "input")
        _require_canonical_string("memory_key", self.memory_key)
        for field_name in INPUT_DECIMAL_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchStrategyMemoryEvidenceEdgeWatchRow(_FinalPublicDataclass):
    aggregate_row_number: Decimal
    aggregate_row_hash: str
    status: str
    memory_reuse_score: Decimal
    evidence_alignment_score: Decimal
    edge_confidence_score: Decimal
    stale_memory_pressure: Decimal
    contradictory_evidence_pressure: Decimal
    unresolved_edge_pressure: Decimal
    edge_watch_readiness_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyMemoryEvidenceEdgeWatchRow, "row")
        object.__setattr__(
            self,
            "aggregate_row_number",
            _normalize_positive_count("aggregate_row_number", self.aggregate_row_number),
        )
        _require_public_digest("aggregate_row_hash", self.aggregate_row_hash)
        _require_status("status", self.status)
        for field_name in ROW_DECIMAL_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.edge_watch_readiness_score != _edge_watch_readiness_score(
            self.memory_reuse_score,
            self.evidence_alignment_score,
            self.edge_confidence_score,
            self.stale_memory_pressure,
            self.contradictory_evidence_pressure,
            self.unresolved_edge_pressure,
        ):
            raise ValueError("edge_watch_readiness_score must match row values")
        if self.status != _row_status(self.reason_codes):
            raise ValueError("status must match reason_codes")
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchStrategyMemoryEvidenceEdgeWatchReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyMemoryEvidenceEdgeWatchReasonCodeCount,
            "reason_code_count",
        )
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyMemoryEvidenceEdgeWatchReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    memory_edge_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    attention_count: Decimal
    mean_memory_reuse_score: Decimal
    mean_evidence_alignment_score: Decimal
    mean_edge_confidence_score: Decimal
    mean_edge_watch_readiness_score: Decimal
    max_stale_memory_pressure: Decimal
    max_contradictory_evidence_pressure: Decimal
    max_unresolved_edge_pressure: Decimal
    status: str
    public_digest: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchStrategyMemoryEvidenceEdgeWatchReasonCodeCount, ...]
    rows: tuple[ResearchStrategyMemoryEvidenceEdgeWatchRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyMemoryEvidenceEdgeWatchReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in REPORT_COUNT_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in REPORT_PROBABILITY_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        _require_public_digest("public_digest", self.public_digest)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)
        if self.public_digest != _computed_report_digest(self):
            raise ValueError("public_digest must match report values")
        _reject_unsafe_public_payload("report", self)


def build_research_strategy_memory_evidence_edge_watch_report(
    memory_edges: Iterable[ResearchStrategyMemoryEvidenceEdgeWatchInput],
    *,
    config: ResearchStrategyMemoryEvidenceEdgeWatchConfig,
    generated_at: datetime,
) -> ResearchStrategyMemoryEvidenceEdgeWatchReport:
    if type(config) is not ResearchStrategyMemoryEvidenceEdgeWatchConfig:
        raise ValueError("config must be a ResearchStrategyMemoryEvidenceEdgeWatchConfig")
    _revalidate_config_for_build(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(memory_edges)
    row_values = sorted(
        (_row_values_for_input(value, config=config) for value in inputs),
        key=_row_values_sort_key,
    )
    rows = tuple(
        _row_from_values(_count(index), values)
        for index, values in enumerate(row_values, start=1)
    )
    values = _report_values(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        rows=rows,
    )
    return ResearchStrategyMemoryEvidenceEdgeWatchReport(
        **values,
        public_digest=_digest_from_mapping(values),
    )


def research_strategy_memory_evidence_edge_watch_report_digest(
    report: ResearchStrategyMemoryEvidenceEdgeWatchReport,
) -> str:
    if type(report) is not ResearchStrategyMemoryEvidenceEdgeWatchReport:
        raise ValueError("report must be a ResearchStrategyMemoryEvidenceEdgeWatchReport")
    _revalidate_report_for_payload(report)
    return _computed_report_digest(report)


def research_strategy_memory_evidence_edge_watch_report_payload(
    report: ResearchStrategyMemoryEvidenceEdgeWatchReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyMemoryEvidenceEdgeWatchReport:
        raise ValueError("report must be a ResearchStrategyMemoryEvidenceEdgeWatchReport")
    _revalidate_report_for_payload(report)
    payload = _json_ready(_report_payload_values(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_key_order("report payload", payload, REPORT_PAYLOAD_KEYS)
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
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


@dataclass(frozen=True)
class _RowValues:
    aggregate_row_hash: str
    status: str
    memory_reuse_score: Decimal
    evidence_alignment_score: Decimal
    edge_confidence_score: Decimal
    stale_memory_pressure: Decimal
    contradictory_evidence_pressure: Decimal
    unresolved_edge_pressure: Decimal
    edge_watch_readiness_score: Decimal
    reason_codes: tuple[str, ...]


def _row_values_for_input(
    value: ResearchStrategyMemoryEvidenceEdgeWatchInput,
    *,
    config: ResearchStrategyMemoryEvidenceEdgeWatchConfig,
) -> _RowValues:
    reason_codes = _row_reason_codes(value, config=config)
    return _RowValues(
        aggregate_row_hash=_public_hash(value.memory_key),
        status=_row_status(reason_codes),
        memory_reuse_score=value.memory_reuse_score,
        evidence_alignment_score=value.evidence_alignment_score,
        edge_confidence_score=value.edge_confidence_score,
        stale_memory_pressure=value.stale_memory_pressure,
        contradictory_evidence_pressure=value.contradictory_evidence_pressure,
        unresolved_edge_pressure=value.unresolved_edge_pressure,
        edge_watch_readiness_score=_edge_watch_readiness_score(
            value.memory_reuse_score,
            value.evidence_alignment_score,
            value.edge_confidence_score,
            value.stale_memory_pressure,
            value.contradictory_evidence_pressure,
            value.unresolved_edge_pressure,
        ),
        reason_codes=reason_codes,
    )


def _row_from_values(
    aggregate_row_number: Decimal,
    values: _RowValues,
) -> ResearchStrategyMemoryEvidenceEdgeWatchRow:
    return ResearchStrategyMemoryEvidenceEdgeWatchRow(
        aggregate_row_number=aggregate_row_number,
        aggregate_row_hash=values.aggregate_row_hash,
        status=values.status,
        memory_reuse_score=values.memory_reuse_score,
        evidence_alignment_score=values.evidence_alignment_score,
        edge_confidence_score=values.edge_confidence_score,
        stale_memory_pressure=values.stale_memory_pressure,
        contradictory_evidence_pressure=values.contradictory_evidence_pressure,
        unresolved_edge_pressure=values.unresolved_edge_pressure,
        edge_watch_readiness_score=values.edge_watch_readiness_score,
        reason_codes=values.reason_codes,
    )


def _row_reason_codes(
    value: ResearchStrategyMemoryEvidenceEdgeWatchInput,
    *,
    config: ResearchStrategyMemoryEvidenceEdgeWatchConfig,
) -> tuple[str, ...]:
    reason_codes = [f"input_{reason_code}" for reason_code in value.reason_codes]
    _append_floor_reason(
        reason_codes,
        "memory_reuse",
        value.memory_reuse_score,
        config.memory_pass_floor,
        config.memory_watch_floor,
    )
    _append_floor_reason(
        reason_codes,
        "evidence_alignment",
        value.evidence_alignment_score,
        config.evidence_pass_floor,
        config.evidence_watch_floor,
    )
    _append_floor_reason(
        reason_codes,
        "edge_confidence",
        value.edge_confidence_score,
        config.edge_pass_floor,
        config.edge_watch_floor,
    )
    _append_pressure_reason(
        reason_codes,
        "stale_memory_pressure",
        value.stale_memory_pressure,
        config.stale_memory_pressure_watch,
        config.stale_memory_pressure_block,
    )
    _append_pressure_reason(
        reason_codes,
        "contradictory_evidence_pressure",
        value.contradictory_evidence_pressure,
        config.contradictory_evidence_pressure_watch,
        config.contradictory_evidence_pressure_block,
    )
    _append_pressure_reason(
        reason_codes,
        "unresolved_edge_pressure",
        value.unresolved_edge_pressure,
        config.unresolved_edge_pressure_watch,
        config.unresolved_edge_pressure_block,
    )
    if not _has_attention_reason(reason_codes):
        reason_codes.append("memory_evidence_edge_watch_clear")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _append_floor_reason(
    reason_codes: list[str],
    prefix: str,
    score: Decimal,
    pass_floor: Decimal,
    watch_floor: Decimal,
) -> None:
    if score < watch_floor:
        reason_codes.append(f"{prefix}_block")
    elif score < pass_floor:
        reason_codes.append(f"{prefix}_watch")


def _append_pressure_reason(
    reason_codes: list[str],
    prefix: str,
    pressure: Decimal,
    watch_limit: Decimal,
    block_limit: Decimal,
) -> None:
    if pressure >= block_limit:
        reason_codes.append(f"{prefix}_block")
    elif pressure >= watch_limit:
        reason_codes.append(f"{prefix}_watch")


def _has_attention_reason(reason_codes: list[str]) -> bool:
    return any(
        reason_code.endswith("_watch") or reason_code.endswith("_block")
        for reason_code in reason_codes
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if not statuses:
        return "block"
    if any(status == "block" for status in statuses):
        return "block"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyMemoryEvidenceEdgeWatchRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    status = _rollup_status(tuple(row.status for row in rows))
    row_reason_codes = tuple(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
    )
    reason_code_set = frozenset(row_reason_codes)
    reason_codes = [f"memory_evidence_edge_watch_{status}"]
    reason_codes.extend(
        reason_code
        for reason_code in REPORT_REASON_PRIORITY
        if reason_code in reason_code_set
    )
    reason_codes.extend(
        sorted(
            reason_code
            for reason_code in reason_code_set
            if reason_code.startswith("input_")
        ),
    )
    return tuple(reason_codes)


def _reason_code_counts(
    rows: tuple[ResearchStrategyMemoryEvidenceEdgeWatchRow, ...],
    report_reason_codes: tuple[str, ...],
) -> tuple[ResearchStrategyMemoryEvidenceEdgeWatchReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyMemoryEvidenceEdgeWatchReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchStrategyMemoryEvidenceEdgeWatchReasonCodeCount(
            reason_code=reason_code,
            count=ONE if reason_code.startswith("memory_evidence_edge_watch_") else _count(
                counter[reason_code],
            ),
        )
        for reason_code in report_reason_codes
    )


def _report_values(
    *,
    generated_at: datetime,
    config_version: str,
    rows: tuple[ResearchStrategyMemoryEvidenceEdgeWatchRow, ...],
) -> dict[str, Any]:
    reason_codes = _report_reason_codes(rows)
    return {
        "generated_at": generated_at,
        "config_version": config_version,
        "memory_edge_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "attention_count": _count(sum(1 for row in rows if row.status != "pass")),
        "mean_memory_reuse_score": _mean(tuple(row.memory_reuse_score for row in rows)),
        "mean_evidence_alignment_score": _mean(
            tuple(row.evidence_alignment_score for row in rows),
        ),
        "mean_edge_confidence_score": _mean(
            tuple(row.edge_confidence_score for row in rows),
        ),
        "mean_edge_watch_readiness_score": _mean(
            tuple(row.edge_watch_readiness_score for row in rows),
        ),
        "max_stale_memory_pressure": _max_decimal(
            tuple(row.stale_memory_pressure for row in rows),
        ),
        "max_contradictory_evidence_pressure": _max_decimal(
            tuple(row.contradictory_evidence_pressure for row in rows),
        ),
        "max_unresolved_edge_pressure": _max_decimal(
            tuple(row.unresolved_edge_pressure for row in rows),
        ),
        "status": _rollup_status(tuple(row.status for row in rows)),
        "reason_codes": reason_codes,
        "reason_code_counts": _reason_code_counts(rows, reason_codes),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _normalize_inputs(
    memory_edges: Iterable[ResearchStrategyMemoryEvidenceEdgeWatchInput],
) -> tuple[ResearchStrategyMemoryEvidenceEdgeWatchInput, ...]:
    if isinstance(memory_edges, (str, bytes)):
        raise ValueError("memory_edges must be an iterable")
    try:
        rows = tuple(memory_edges)
    except TypeError as exc:
        raise ValueError("memory_edges must be an iterable") from exc
    seen_keys: set[str] = set()
    for row in rows:
        if type(row) is not ResearchStrategyMemoryEvidenceEdgeWatchInput:
            raise ValueError(
                "memory_edges must contain ResearchStrategyMemoryEvidenceEdgeWatchInput values",
            )
        _revalidate_input_for_build(row)
        if row.memory_key in seen_keys:
            raise ValueError("memory_edges must not contain duplicate memory_key values")
        seen_keys.add(row.memory_key)
    return rows


def _revalidate_config_for_build(
    config: ResearchStrategyMemoryEvidenceEdgeWatchConfig,
) -> None:
    _require_exact_type(
        config,
        ResearchStrategyMemoryEvidenceEdgeWatchConfig,
        "config",
    )
    _require_canonical_string("config_version", config.config_version)
    if (
        config.config_version
        != DEFAULT_RESEARCH_STRATEGY_MEMORY_EVIDENCE_EDGE_WATCH_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    for field_name in CONFIG_DECIMAL_FIELDS:
        _require_probability_six_decimal_decimal(field_name, getattr(config, field_name))
    _require_at_least("memory_pass_floor", config.memory_pass_floor, config.memory_watch_floor)
    _require_at_least(
        "evidence_pass_floor",
        config.evidence_pass_floor,
        config.evidence_watch_floor,
    )
    _require_at_least("edge_pass_floor", config.edge_pass_floor, config.edge_watch_floor)
    _require_at_most(
        "stale_memory_pressure_watch",
        config.stale_memory_pressure_watch,
        config.stale_memory_pressure_block,
    )
    _require_at_most(
        "contradictory_evidence_pressure_watch",
        config.contradictory_evidence_pressure_watch,
        config.contradictory_evidence_pressure_block,
    )
    _require_at_most(
        "unresolved_edge_pressure_watch",
        config.unresolved_edge_pressure_watch,
        config.unresolved_edge_pressure_block,
    )
    _require_hard_flags("config", config)
    _reject_unsafe_public_payload("config", config)


def _revalidate_input_for_build(
    value: ResearchStrategyMemoryEvidenceEdgeWatchInput,
) -> None:
    _require_exact_type(value, ResearchStrategyMemoryEvidenceEdgeWatchInput, "input")
    _require_canonical_string("memory_key", value.memory_key)
    for field_name in INPUT_DECIMAL_FIELDS:
        _require_probability_six_decimal_decimal(field_name, getattr(value, field_name))
    normalized_reason_codes = _normalize_reason_codes(
        "reason_codes",
        value.reason_codes,
        allow_empty=True,
    )
    if value.reason_codes != normalized_reason_codes:
        raise ValueError("reason_codes must be canonical")
    _require_hard_flags("input", value)
    _reject_unsafe_public_payload("input", value)


def _normalize_rows(
    rows: Iterable[ResearchStrategyMemoryEvidenceEdgeWatchRow],
) -> tuple[ResearchStrategyMemoryEvidenceEdgeWatchRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_hashes: set[str] = set()
    for row in values:
        if type(row) is not ResearchStrategyMemoryEvidenceEdgeWatchRow:
            raise ValueError(
                "rows must contain ResearchStrategyMemoryEvidenceEdgeWatchRow values",
            )
        _revalidate_row_for_payload(row)
        if row.aggregate_row_hash in seen_hashes:
            raise ValueError("rows must not contain duplicate aggregate_row_hash values")
        seen_hashes.add(row.aggregate_row_hash)
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("rows must use canonical sequence")
    return values


def _normalize_reason_code_counts(
    rows: Iterable[ResearchStrategyMemoryEvidenceEdgeWatchReasonCodeCount],
) -> tuple[ResearchStrategyMemoryEvidenceEdgeWatchReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen_codes: set[str] = set()
    for row in values:
        if type(row) is not ResearchStrategyMemoryEvidenceEdgeWatchReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchStrategyMemoryEvidenceEdgeWatchReasonCodeCount values",
            )
        _revalidate_reason_code_count_for_payload(row)
        if row.reason_code in seen_codes:
            raise ValueError("reason_code_counts must not contain duplicate reason_code values")
        seen_codes.add(row.reason_code)
    return values


def _row_sort_key(
    row: ResearchStrategyMemoryEvidenceEdgeWatchRow,
) -> tuple[Any, ...]:
    return (
        -STATUS_WEIGHT[row.status],
        -_max_decimal(
            (
                row.stale_memory_pressure,
                row.contradictory_evidence_pressure,
                row.unresolved_edge_pressure,
            ),
        ),
        -row.stale_memory_pressure,
        -row.contradictory_evidence_pressure,
        -row.unresolved_edge_pressure,
        row.edge_watch_readiness_score,
        row.memory_reuse_score,
        row.evidence_alignment_score,
        row.edge_confidence_score,
        row.reason_codes,
        row.aggregate_row_hash,
    )


def _row_values_sort_key(
    values: _RowValues,
) -> tuple[Any, ...]:
    return (
        -STATUS_WEIGHT[values.status],
        -_max_decimal(
            (
                values.stale_memory_pressure,
                values.contradictory_evidence_pressure,
                values.unresolved_edge_pressure,
            ),
        ),
        -values.stale_memory_pressure,
        -values.contradictory_evidence_pressure,
        -values.unresolved_edge_pressure,
        values.edge_watch_readiness_score,
        values.memory_reuse_score,
        values.evidence_alignment_score,
        values.edge_confidence_score,
        values.reason_codes,
        values.aggregate_row_hash,
    )


def _status_count(
    rows: tuple[ResearchStrategyMemoryEvidenceEdgeWatchRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _validate_report(report: ResearchStrategyMemoryEvidenceEdgeWatchReport) -> None:
    rows = report.rows
    if report.memory_edge_count != _count(len(rows)):
        raise ValueError("memory_edge_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.attention_count != _count(sum(1 for row in rows if row.status != "pass")):
        raise ValueError("attention_count must match rows")
    for field_name in (
        "memory_reuse_score",
        "evidence_alignment_score",
        "edge_confidence_score",
        "edge_watch_readiness_score",
    ):
        report_field_name = f"mean_{field_name}"
        if getattr(report, report_field_name) != _mean(
            tuple(getattr(row, field_name) for row in rows),
        ):
            raise ValueError(f"{report_field_name} must match rows")
    if report.max_stale_memory_pressure != _max_decimal(
        tuple(row.stale_memory_pressure for row in rows),
    ):
        raise ValueError("max_stale_memory_pressure must match rows")
    if report.max_contradictory_evidence_pressure != _max_decimal(
        tuple(row.contradictory_evidence_pressure for row in rows),
    ):
        raise ValueError("max_contradictory_evidence_pressure must match rows")
    if report.max_unresolved_edge_pressure != _max_decimal(
        tuple(row.unresolved_edge_pressure for row in rows),
    ):
        raise ValueError("max_unresolved_edge_pressure must match rows")
    if report.status != _rollup_status(tuple(row.status for row in rows)):
        raise ValueError("status must match rows")
    expected_reason_codes = _report_reason_codes(rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows, expected_reason_codes):
        raise ValueError("reason_code_counts must match rows")
    for index, row in enumerate(rows, start=1):
        if row.aggregate_row_number != _count(index):
            raise ValueError("aggregate_row_number must match rows")


def _revalidate_report_for_payload(
    report: ResearchStrategyMemoryEvidenceEdgeWatchReport,
) -> None:
    _require_exact_type(report, ResearchStrategyMemoryEvidenceEdgeWatchReport, "report")
    _require_utc_datetime("generated_at", report.generated_at)
    _require_canonical_string("config_version", report.config_version)
    for field_name in REPORT_COUNT_FIELDS:
        _require_count_six_decimal_decimal(field_name, getattr(report, field_name))
    for field_name in REPORT_PROBABILITY_FIELDS:
        _require_probability_six_decimal_decimal(field_name, getattr(report, field_name))
    _require_status("status", report.status)
    _require_public_digest("public_digest", report.public_digest)
    _require_reason_codes_tuple("reason_codes", report.reason_codes)
    if report.reason_codes != _normalize_report_reason_codes(report.reason_codes):
        raise ValueError("reason_codes must be canonical")
    if type(report.reason_code_counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    _normalize_reason_code_counts(report.reason_code_counts)
    if type(report.rows) is not tuple:
        raise ValueError("rows must be a tuple")
    _normalize_rows(report.rows)
    _validate_report(report)
    if report.public_digest != _computed_report_digest(report):
        raise ValueError("public_digest must match report values")
    _require_hard_flags("report", report)
    _reject_unsafe_public_payload("report", report)


def _revalidate_row_for_payload(row: object) -> None:
    _require_exact_type(row, ResearchStrategyMemoryEvidenceEdgeWatchRow, "row")
    _require_positive_count_six_decimal_decimal(
        "aggregate_row_number",
        row.aggregate_row_number,
    )
    _require_public_digest("aggregate_row_hash", row.aggregate_row_hash)
    _require_status("status", row.status)
    for field_name in ROW_DECIMAL_FIELDS:
        _require_probability_six_decimal_decimal(field_name, getattr(row, field_name))
    _require_reason_codes_tuple("reason_codes", row.reason_codes)
    if row.reason_codes != _normalize_reason_codes("reason_codes", row.reason_codes):
        raise ValueError("reason_codes must be canonical")
    if row.edge_watch_readiness_score != _edge_watch_readiness_score(
        row.memory_reuse_score,
        row.evidence_alignment_score,
        row.edge_confidence_score,
        row.stale_memory_pressure,
        row.contradictory_evidence_pressure,
        row.unresolved_edge_pressure,
    ):
        raise ValueError("edge_watch_readiness_score must match row values")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    _require_hard_flags("row", row)
    _reject_unsafe_public_payload("row", row)


def _revalidate_reason_code_count_for_payload(row: object) -> None:
    _require_exact_type(
        row,
        ResearchStrategyMemoryEvidenceEdgeWatchReasonCodeCount,
        "reason_code_count",
    )
    _require_canonical_string("reason_code", row.reason_code)
    _require_positive_count_six_decimal_decimal("count", row.count)
    _require_hard_flags("reason_code_count", row)
    _reject_unsafe_public_payload("reason_code_count", row)


def _normalize_report_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    return _normalize_reason_codes("reason_codes", reason_codes)


def _normalize_reason_codes(
    field_name: str,
    reason_codes: Iterable[str],
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    _require_reason_codes_tuple(field_name, reason_codes)
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_canonical_string("reason_code", reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    if not normalized and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(normalized)


def _require_reason_codes_tuple(field_name: str, value: object) -> None:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    for item in value:
        if type(item) is not str:
            raise ValueError(f"{field_name} must contain strings")


def _edge_watch_readiness_score(
    memory_reuse_score: Decimal,
    evidence_alignment_score: Decimal,
    edge_confidence_score: Decimal,
    stale_memory_pressure: Decimal,
    contradictory_evidence_pressure: Decimal,
    unresolved_edge_pressure: Decimal,
) -> Decimal:
    average_signal = _mean(
        (
            memory_reuse_score,
            evidence_alignment_score,
            edge_confidence_score,
        ),
    )
    max_pressure = _max_decimal(
        (
            stale_memory_pressure,
            contradictory_evidence_pressure,
            unresolved_edge_pressure,
        ),
    )
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_probability(average_signal - (max_pressure * Decimal("0.200000")))


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize(Decimal(value))


def _public_hash(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _computed_report_digest(
    report: ResearchStrategyMemoryEvidenceEdgeWatchReport,
) -> str:
    return _digest_from_mapping(_report_values_without_digest(report))


def _digest_from_mapping(values: Mapping[str, Any]) -> str:
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    _require_key_order("digest payload", payload, REPORT_DIGEST_KEYS)
    _reject_unsafe_public_payload("digest payload", payload)
    encoded = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _report_values_without_digest(
    report: ResearchStrategyMemoryEvidenceEdgeWatchReport,
) -> dict[str, Any]:
    return _report_values(
        generated_at=report.generated_at,
        config_version=report.config_version,
        rows=report.rows,
    )


def _report_payload_values(
    report: ResearchStrategyMemoryEvidenceEdgeWatchReport,
) -> dict[str, Any]:
    values = _report_values_without_digest(report)
    return {
        "generated_at": values["generated_at"],
        "config_version": values["config_version"],
        "memory_edge_count": values["memory_edge_count"],
        "pass_count": values["pass_count"],
        "watch_count": values["watch_count"],
        "block_count": values["block_count"],
        "attention_count": values["attention_count"],
        "mean_memory_reuse_score": values["mean_memory_reuse_score"],
        "mean_evidence_alignment_score": values["mean_evidence_alignment_score"],
        "mean_edge_confidence_score": values["mean_edge_confidence_score"],
        "mean_edge_watch_readiness_score": values["mean_edge_watch_readiness_score"],
        "max_stale_memory_pressure": values["max_stale_memory_pressure"],
        "max_contradictory_evidence_pressure": values[
            "max_contradictory_evidence_pressure"
        ],
        "max_unresolved_edge_pressure": values["max_unresolved_edge_pressure"],
        "status": values["status"],
        "public_digest": _digest_from_mapping(values),
        "reason_codes": values["reason_codes"],
        "reason_code_counts": values["reason_code_counts"],
        "rows": values["rows"],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if type(value) is ResearchStrategyMemoryEvidenceEdgeWatchReport:
        return _json_ready(_report_payload_values(value))
    if type(value) is ResearchStrategyMemoryEvidenceEdgeWatchRow:
        payload = {
            "aggregate_row_number": _json_ready(value.aggregate_row_number),
            "aggregate_row_hash": value.aggregate_row_hash,
            "status": value.status,
            "memory_reuse_score": _json_ready(value.memory_reuse_score),
            "evidence_alignment_score": _json_ready(value.evidence_alignment_score),
            "edge_confidence_score": _json_ready(value.edge_confidence_score),
            "stale_memory_pressure": _json_ready(value.stale_memory_pressure),
            "contradictory_evidence_pressure": _json_ready(
                value.contradictory_evidence_pressure,
            ),
            "unresolved_edge_pressure": _json_ready(value.unresolved_edge_pressure),
            "edge_watch_readiness_score": _json_ready(
                value.edge_watch_readiness_score,
            ),
            "reason_codes": _json_ready(value.reason_codes),
            "paper_only": value.paper_only,
            "report_only": value.report_only,
            "readonly": value.readonly,
        }
        _require_key_order("row payload", payload, ROW_PAYLOAD_KEYS)
        return payload
    if type(value) is ResearchStrategyMemoryEvidenceEdgeWatchReasonCodeCount:
        payload = {
            "reason_code": value.reason_code,
            "count": _json_ready(value.count),
            "paper_only": value.paper_only,
            "report_only": value.report_only,
            "readonly": value.readonly,
        }
        _require_key_order(
            "reason_code_count payload",
            payload,
            REASON_CODE_COUNT_PAYLOAD_KEYS,
        )
        return payload
    if is_dataclass(value) and not isinstance(value, type):
        raise ValueError("payload dataclass must use a canonical public schema")
    if type(value) is Decimal:
        _require_six_decimal_places("Decimal payload value", value)
        return format(value, ".6f")
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        raise ValueError("payload containers must be immutable before JSON conversion")
    raise ValueError("payload value is not JSON serializable")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a canonical public string")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass/watch/block")
    return value


def _require_public_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not PUBLIC_DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_key_order(
    label: str,
    value: Mapping[str, Any],
    expected_keys: tuple[str, ...],
) -> None:
    if tuple(value.keys()) != expected_keys:
        raise ValueError(f"{label} must use the canonical schema")


def _require_at_least(field_name: str, high_value: Decimal, low_value: Decimal) -> None:
    if high_value < low_value:
        raise ValueError(f"{field_name} must be at least its watch floor")


def _require_at_most(field_name: str, low_value: Decimal, high_value: Decimal) -> None:
    if low_value > high_value:
        raise ValueError(f"{field_name} must be at most its block threshold")


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    raw_value = _require_decimal(field_name, value)
    if raw_value < ZERO or raw_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return _quantize(raw_value)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    raw_value = _require_decimal(field_name, value)
    if raw_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(raw_value)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    raw_value = _require_decimal(field_name, value)
    if raw_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    _require_whole_count_decimal(field_name, raw_value)
    return _quantize(raw_value)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    raw_value = _require_decimal(field_name, value)
    if raw_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    _require_whole_count_decimal(field_name, raw_value)
    return _quantize(raw_value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not use signed zero")
    return value


def _require_nonnegative_six_decimal_decimal(field_name: str, value: object) -> Decimal:
    raw_value = _require_decimal(field_name, value)
    if raw_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    _require_six_decimal_places(field_name, raw_value)
    return raw_value


def _require_count_six_decimal_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_six_decimal_decimal(field_name, value)
    _require_whole_count_decimal(field_name, normalized)
    return normalized


def _require_positive_count_six_decimal_decimal(
    field_name: str,
    value: object,
) -> Decimal:
    normalized = _require_count_six_decimal_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_probability_six_decimal_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_six_decimal_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_utc_datetime(field_name: str, value: object) -> datetime:
    normalized = _as_utc(field_name, value)
    if value.tzinfo is not UTC or value != normalized:
        raise ValueError(f"{field_name} must be UTC-normalized")
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _require_six_decimal_places(field_name: str, value: object) -> Decimal:
    raw_value = _require_decimal(field_name, value)
    if (
        raw_value != _quantize(raw_value)
        or raw_value.as_tuple().exponent != QUANTUM.as_tuple().exponent
    ):
        raise ValueError(f"{field_name} must use six decimal places")
    return raw_value


def _require_whole_count_decimal(field_name: str, value: Decimal) -> None:
    with localcontext(DECIMAL_CONTEXT):
        integral_value = value.to_integral_value(rounding=ROUND_HALF_EVEN)
    if value != integral_value:
        raise ValueError(f"{field_name} must be a whole-count Decimal")


def _clamp_probability(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
            )
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
            )
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(label, item, f"{current_path}[{index}]")
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe public value")
