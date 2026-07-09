"""Report-only evidence, memory, and confidence ladder report."""

from __future__ import annotations

from collections import Counter
from dataclasses import InitVar, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_STRATEGY_EVIDENCE_MEMORY_CONFIDENCE_LADDER_CONFIG_VERSION = (
    "research-strategy-evidence-memory-confidence-ladder-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

REASON_EMPTY_INPUT = "empty_input"
REASON_ANALYST_REVIEWED = "analyst_reviewed"
REASON_MEMORY_RECHECKED = "memory_rechecked"
REASON_MANUAL_CONFIDENCE_CHECK = "manual_confidence_check"
REASON_EVIDENCE_BLOCK = "evidence_block"
REASON_MEMORY_BLOCK = "memory_block"
REASON_CONFIDENCE_BLOCK = "confidence_block"
REASON_COMPOSITE_BLOCK = "composite_block"
REASON_EVIDENCE_WATCH = "evidence_watch"
REASON_MEMORY_WATCH = "memory_watch"
REASON_CONFIDENCE_WATCH = "confidence_watch"
REASON_COMPOSITE_WATCH = "composite_watch"
REASON_CONFIDENCE_LADDER_PASS = "confidence_ladder_pass"

_UPSTREAM_REASON_CODE_SEQUENCE = (
    REASON_ANALYST_REVIEWED,
    REASON_MEMORY_RECHECKED,
    REASON_MANUAL_CONFIDENCE_CHECK,
)
_GENERATED_ROW_REASON_CODE_SEQUENCE = (
    REASON_EVIDENCE_BLOCK,
    REASON_MEMORY_BLOCK,
    REASON_CONFIDENCE_BLOCK,
    REASON_COMPOSITE_BLOCK,
    REASON_EVIDENCE_WATCH,
    REASON_MEMORY_WATCH,
    REASON_CONFIDENCE_WATCH,
    REASON_COMPOSITE_WATCH,
    REASON_CONFIDENCE_LADDER_PASS,
)
_ROW_REASON_CODE_SEQUENCE = (
    *_UPSTREAM_REASON_CODE_SEQUENCE,
    *_GENERATED_ROW_REASON_CODE_SEQUENCE,
)
_REASON_CODE_SEQUENCE = (REASON_EMPTY_INPUT, *_ROW_REASON_CODE_SEQUENCE)
_BLOCK_REASON_CODES = frozenset(
    (
        REASON_EVIDENCE_BLOCK,
        REASON_MEMORY_BLOCK,
        REASON_CONFIDENCE_BLOCK,
        REASON_COMPOSITE_BLOCK,
    ),
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DIGEST_FIELD = "derived_validation_digest"
_STATUS_VALUES = frozenset((STATUS_PASS, STATUS_WATCH, STATUS_BLOCK))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PRIVATE_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "market",
    "source",
    "url",
    "text",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "://",
)
_TOP_LEVEL_PAYLOAD_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "status",
        "row_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_composite_score",
        "min_composite_score",
        "min_evidence_score",
        "min_memory_score",
        "min_confidence_score",
        "rows",
        "reason_code_counts",
        "reason_codes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_ROW_PAYLOAD_FIELDS = frozenset(
    (
        "item_digest",
        "evidence_score",
        "evidence_gap_score",
        "memory_score",
        "memory_gap_score",
        "confidence_score",
        "confidence_gap_score",
        "composite_score",
        "observed_at",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_REASON_COUNT_PAYLOAD_FIELDS = frozenset(
    (
        "reason_code",
        "count",
        "row_ratio",
        "paper_only",
        "report_only",
        "readonly",
    ),
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
class ResearchStrategyEvidenceMemoryConfidenceLadderConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_EVIDENCE_MEMORY_CONFIDENCE_LADDER_CONFIG_VERSION
    )
    pass_min_composite_score: Decimal = Decimal("0.800000")
    watch_min_composite_score: Decimal = Decimal("0.600000")
    min_pass_evidence_score: Decimal = Decimal("0.800000")
    min_watch_evidence_score: Decimal = Decimal("0.600000")
    min_pass_memory_score: Decimal = Decimal("0.750000")
    min_watch_memory_score: Decimal = Decimal("0.550000")
    min_pass_confidence_score: Decimal = Decimal("0.750000")
    min_watch_confidence_score: Decimal = Decimal("0.550000")
    evidence_weight: Decimal = Decimal("0.400000")
    memory_weight: Decimal = Decimal("0.300000")
    confidence_weight: Decimal = Decimal("0.300000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyEvidenceMemoryConfidenceLadderConfig)
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_EVIDENCE_MEMORY_CONFIDENCE_LADDER_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_min_composite_score",
            "watch_min_composite_score",
            "min_pass_evidence_score",
            "min_watch_evidence_score",
            "min_pass_memory_score",
            "min_watch_memory_score",
            "min_pass_confidence_score",
            "min_watch_confidence_score",
            "evidence_weight",
            "memory_weight",
            "confidence_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_min_composite_score < self.watch_min_composite_score:
            raise ValueError(
                "pass_min_composite_score must be at least watch_min_composite_score",
            )
        if self.min_pass_evidence_score < self.min_watch_evidence_score:
            raise ValueError(
                "min_pass_evidence_score must be at least min_watch_evidence_score",
            )
        if self.min_pass_memory_score < self.min_watch_memory_score:
            raise ValueError(
                "min_pass_memory_score must be at least min_watch_memory_score",
            )
        if self.min_pass_confidence_score < self.min_watch_confidence_score:
            raise ValueError(
                "min_pass_confidence_score must be at least min_watch_confidence_score",
            )
        weight_sum = _quantize(
            self.evidence_weight + self.memory_weight + self.confidence_weight,
        )
        if weight_sum != _ONE:
            raise ValueError("ladder weights must sum to one")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyEvidenceMemoryConfidenceLadderInput(_FinalPublicDataclass):
    private_reference: str
    evidence_score: Decimal
    memory_score: Decimal
    confidence_score: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyEvidenceMemoryConfidenceLadderInput)
        object.__setattr__(
            self,
            "private_reference",
            _require_private_reference("private_reference", self.private_reference),
        )
        for field_name in ("evidence_score", "memory_score", "confidence_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_upstream_reason_codes(self.reason_codes),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyEvidenceMemoryConfidenceLadderRow(_FinalPublicDataclass):
    item_digest: str
    evidence_score: Decimal
    evidence_gap_score: Decimal
    memory_score: Decimal
    memory_gap_score: Decimal
    confidence_score: Decimal
    confidence_gap_score: Decimal
    composite_score: Decimal
    observed_at: datetime
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[
        ResearchStrategyEvidenceMemoryConfidenceLadderConfig | None
    ] = None

    def __post_init__(
        self,
        validation_config: (
            ResearchStrategyEvidenceMemoryConfidenceLadderConfig | None
        ),
    ) -> None:
        _require_exact_type(self, ResearchStrategyEvidenceMemoryConfidenceLadderRow)
        object.__setattr__(
            self,
            "item_digest",
            _require_private_digest("item_digest", self.item_digest),
        )
        for field_name in (
            "evidence_score",
            "evidence_gap_score",
            "memory_score",
            "memory_gap_score",
            "confidence_score",
            "confidence_gap_score",
            "composite_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self, validation_config)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchStrategyEvidenceMemoryConfidenceLadderReasonCodeCount(
    _FinalPublicDataclass,
):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyEvidenceMemoryConfidenceLadderReasonCodeCount,
        )
        _require_reason_code("reason_code", self.reason_code, _REASON_CODE_SEQUENCE)
        object.__setattr__(
            self,
            "count",
            _require_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason count", self)
        _reject_unsafe_public_payload("reason count", self)


@dataclass(frozen=True)
class ResearchStrategyEvidenceMemoryConfidenceLadderReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_composite_score: Decimal
    min_composite_score: Decimal
    min_evidence_score: Decimal
    min_memory_score: Decimal
    min_confidence_score: Decimal
    rows: tuple[ResearchStrategyEvidenceMemoryConfidenceLadderRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyEvidenceMemoryConfidenceLadderReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyEvidenceMemoryConfidenceLadderReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_EVIDENCE_MEMORY_CONFIDENCE_LADDER_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in ("row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_composite_score",
            "min_composite_score",
            "min_evidence_score",
            "min_memory_score",
            "min_confidence_score",
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
            _normalize_report_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, _DIGEST_FIELD, expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest mismatch")
        _require_digest(_DIGEST_FIELD, self.derived_validation_digest)

    @property
    def payload(self) -> dict[str, object]:
        return research_strategy_evidence_memory_confidence_ladder_report_payload(self)


def build_research_strategy_evidence_memory_confidence_ladder_report(
    inputs: Sequence[ResearchStrategyEvidenceMemoryConfidenceLadderInput],
    *,
    generated_at: datetime,
    config: ResearchStrategyEvidenceMemoryConfidenceLadderConfig | None = None,
) -> ResearchStrategyEvidenceMemoryConfidenceLadderReport:
    cfg = config or ResearchStrategyEvidenceMemoryConfidenceLadderConfig()
    if type(cfg) is not ResearchStrategyEvidenceMemoryConfidenceLadderConfig:
        raise ValueError(
            "config must be a ResearchStrategyEvidenceMemoryConfidenceLadderConfig",
        )
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    for row in normalized_inputs:
        if row.observed_at > report_time:
            raise ValueError("observed_at must not be after generated_at")
    rows = tuple(
        sorted(
            (_row_for_input(row, cfg) for row in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(row.reason_code for row in reason_code_counts)
    if not rows:
        reason_code_counts = (
            ResearchStrategyEvidenceMemoryConfidenceLadderReasonCodeCount(
                reason_code=REASON_EMPTY_INPUT,
                count=_ONE,
                row_ratio=_ONE,
            ),
        )
        reason_codes = (REASON_EMPTY_INPUT,)
    values: dict[str, object] = {
        "generated_at": report_time,
        "config_version": cfg.config_version,
        "status": _report_status(rows),
        "row_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, STATUS_PASS)),
        "watch_count": _decimal_count(_status_count(rows, STATUS_WATCH)),
        "block_count": _decimal_count(_status_count(rows, STATUS_BLOCK)),
        "average_composite_score": _average_ratio(
            tuple(row.composite_score for row in rows),
        ),
        "min_composite_score": min(
            (row.composite_score for row in rows),
            default=_ZERO,
        ),
        "min_evidence_score": min((row.evidence_score for row in rows), default=_ZERO),
        "min_memory_score": min((row.memory_score for row in rows), default=_ZERO),
        "min_confidence_score": min(
            (row.confidence_score for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_code_counts": reason_code_counts,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyEvidenceMemoryConfidenceLadderReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_strategy_evidence_memory_confidence_ladder_report_payload(
    value: ResearchStrategyEvidenceMemoryConfidenceLadderReport | dict[str, object],
) -> dict[str, object]:
    if type(value) is ResearchStrategyEvidenceMemoryConfidenceLadderReport:
        _require_hard_flags("report", value)
        payload = _report_payload(value)
    elif type(value) is dict:
        payload = _copy_json_object(value)
    else:
        raise ValueError(
            "value must be a ResearchStrategyEvidenceMemoryConfidenceLadderReport or dict",
        )
    _validate_payload_shape(payload)
    _validate_payload_statuses(payload)
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_payload_digest(payload)
    _validate_payload_semantics(payload)
    return payload


def validate_research_strategy_evidence_memory_confidence_ladder_public_payload(
    value: dict[str, object],
) -> dict[str, object]:
    return research_strategy_evidence_memory_confidence_ladder_report_payload(value)


def _row_for_input(
    row: ResearchStrategyEvidenceMemoryConfidenceLadderInput,
    config: ResearchStrategyEvidenceMemoryConfidenceLadderConfig,
) -> ResearchStrategyEvidenceMemoryConfidenceLadderRow:
    evidence_gap = _inverse_ratio(row.evidence_score)
    memory_gap = _inverse_ratio(row.memory_score)
    confidence_gap = _inverse_ratio(row.confidence_score)
    composite_score = _composite_score(
        evidence_score=row.evidence_score,
        memory_score=row.memory_score,
        confidence_score=row.confidence_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        upstream_reason_codes=row.reason_codes,
        evidence_score=row.evidence_score,
        memory_score=row.memory_score,
        confidence_score=row.confidence_score,
        composite_score=composite_score,
        config=config,
    )
    return ResearchStrategyEvidenceMemoryConfidenceLadderRow(
        item_digest=_private_reference_digest(row.private_reference),
        evidence_score=row.evidence_score,
        evidence_gap_score=evidence_gap,
        memory_score=row.memory_score,
        memory_gap_score=memory_gap,
        confidence_score=row.confidence_score,
        confidence_gap_score=confidence_gap,
        composite_score=composite_score,
        observed_at=row.observed_at,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _row_reason_codes(
    *,
    upstream_reason_codes: tuple[str, ...],
    evidence_score: Decimal,
    memory_score: Decimal,
    confidence_score: Decimal,
    composite_score: Decimal,
    config: ResearchStrategyEvidenceMemoryConfidenceLadderConfig,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    if evidence_score < config.min_watch_evidence_score:
        reason_codes.append(REASON_EVIDENCE_BLOCK)
    elif evidence_score < config.min_pass_evidence_score:
        reason_codes.append(REASON_EVIDENCE_WATCH)
    if memory_score < config.min_watch_memory_score:
        reason_codes.append(REASON_MEMORY_BLOCK)
    elif memory_score < config.min_pass_memory_score:
        reason_codes.append(REASON_MEMORY_WATCH)
    if confidence_score < config.min_watch_confidence_score:
        reason_codes.append(REASON_CONFIDENCE_BLOCK)
    elif confidence_score < config.min_pass_confidence_score:
        reason_codes.append(REASON_CONFIDENCE_WATCH)
    if composite_score < config.watch_min_composite_score:
        reason_codes.append(REASON_COMPOSITE_BLOCK)
    elif composite_score < config.pass_min_composite_score:
        reason_codes.append(REASON_COMPOSITE_WATCH)
    generated = tuple(
        reason_code
        for reason_code in reason_codes
        if reason_code in _GENERATED_ROW_REASON_CODE_SEQUENCE
    )
    if not generated:
        reason_codes.append(REASON_CONFIDENCE_LADDER_PASS)
    return _normalize_row_reason_codes(tuple(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes):
        return STATUS_BLOCK
    if REASON_CONFIDENCE_LADDER_PASS in reason_codes:
        return STATUS_PASS
    return STATUS_WATCH


def _report_status(
    rows: tuple[ResearchStrategyEvidenceMemoryConfidenceLadderRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _status_count(
    rows: tuple[ResearchStrategyEvidenceMemoryConfidenceLadderRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _row_sort_key(
    row: ResearchStrategyEvidenceMemoryConfidenceLadderRow,
) -> tuple[int, Decimal, str]:
    return (_status_rank(row.status), row.composite_score, row.item_digest)


def _status_rank(value: str) -> int:
    return {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[value]


def _reason_code_counts(
    rows: tuple[ResearchStrategyEvidenceMemoryConfidenceLadderRow, ...],
) -> tuple[ResearchStrategyEvidenceMemoryConfidenceLadderReasonCodeCount, ...]:
    total = _decimal_count(len(rows))
    counts: Counter[str] = Counter(
        reason_code for row in rows for reason_code in row.reason_codes
    )
    return tuple(
        ResearchStrategyEvidenceMemoryConfidenceLadderReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            row_ratio=_ratio(_decimal_count(count), total),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )


def _composite_score(
    *,
    evidence_score: Decimal,
    memory_score: Decimal,
    confidence_score: Decimal,
    config: ResearchStrategyEvidenceMemoryConfidenceLadderConfig,
) -> Decimal:
    score = (
        evidence_score * config.evidence_weight
        + memory_score * config.memory_weight
        + confidence_score * config.confidence_weight
    )
    return _clamp_ratio(score)


def _validate_row(
    row: ResearchStrategyEvidenceMemoryConfidenceLadderRow,
    config: ResearchStrategyEvidenceMemoryConfidenceLadderConfig | None,
) -> None:
    if config is not None:
        if type(config) is not ResearchStrategyEvidenceMemoryConfidenceLadderConfig:
            raise ValueError(
                "validation_config must be a "
                "ResearchStrategyEvidenceMemoryConfidenceLadderConfig",
            )
        if row.evidence_gap_score != _inverse_ratio(row.evidence_score):
            raise ValueError("evidence_gap_score must match evidence_score")
        if row.memory_gap_score != _inverse_ratio(row.memory_score):
            raise ValueError("memory_gap_score must match memory_score")
        if row.confidence_gap_score != _inverse_ratio(row.confidence_score):
            raise ValueError("confidence_gap_score must match confidence_score")
        expected_composite_score = _composite_score(
            evidence_score=row.evidence_score,
            memory_score=row.memory_score,
            confidence_score=row.confidence_score,
            config=config,
        )
        if row.composite_score != expected_composite_score:
            raise ValueError("composite_score must match component scores")
        upstream_reason_codes = tuple(
            reason_code
            for reason_code in row.reason_codes
            if reason_code in _UPSTREAM_REASON_CODE_SEQUENCE
        )
        expected_reasons = _row_reason_codes(
            upstream_reason_codes=upstream_reason_codes,
            evidence_score=row.evidence_score,
            memory_score=row.memory_score,
            confidence_score=row.confidence_score,
            composite_score=row.composite_score,
            config=config,
        )
        if row.reason_codes != expected_reasons:
            raise ValueError("reason_codes must match row inputs")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if (
        REASON_CONFIDENCE_LADDER_PASS in row.reason_codes
        and row.reason_codes[-1] != REASON_CONFIDENCE_LADDER_PASS
    ):
        raise ValueError("pass reason must not be mixed with risk reasons")


def _validate_report(
    report: ResearchStrategyEvidenceMemoryConfidenceLadderReport,
) -> None:
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    for row in report.rows:
        if row.observed_at > report.generated_at:
            raise ValueError("row observed_at must not be after generated_at")
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, STATUS_PASS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, STATUS_WATCH)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, STATUS_BLOCK)):
        raise ValueError("block_count must match rows")
    if report.average_composite_score != _average_ratio(
        tuple(row.composite_score for row in report.rows),
    ):
        raise ValueError("average_composite_score must match rows")
    if report.min_composite_score != min(
        (row.composite_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_composite_score must match rows")
    if report.min_evidence_score != min(
        (row.evidence_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_evidence_score must match rows")
    if report.min_memory_score != min(
        (row.memory_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_memory_score must match rows")
    if report.min_confidence_score != min(
        (row.confidence_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_confidence_score must match rows")
    expected_counts = _reason_code_counts(report.rows)
    expected_codes = tuple(row.reason_code for row in expected_counts)
    if not report.rows:
        expected_counts = (
            ResearchStrategyEvidenceMemoryConfidenceLadderReasonCodeCount(
                reason_code=REASON_EMPTY_INPUT,
                count=_ONE,
                row_ratio=_ONE,
            ),
        )
        expected_codes = (REASON_EMPTY_INPUT,)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != expected_codes:
        raise ValueError("reason_codes must match reason_code_counts")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")


def _normalize_inputs(
    inputs: Sequence[ResearchStrategyEvidenceMemoryConfidenceLadderInput],
) -> tuple[ResearchStrategyEvidenceMemoryConfidenceLadderInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    normalized = tuple(inputs)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyEvidenceMemoryConfidenceLadderInput:
            raise ValueError(
                "inputs must contain ResearchStrategyEvidenceMemoryConfidenceLadderInput",
            )
        _require_hard_flags("input", row)
        digest = _private_reference_digest(row.private_reference)
        if digest in seen:
            raise ValueError("inputs must be unique by item digest")
        seen.add(digest)
    return normalized


def _normalize_rows(
    rows: tuple[ResearchStrategyEvidenceMemoryConfidenceLadderRow, ...],
) -> tuple[ResearchStrategyEvidenceMemoryConfidenceLadderRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchStrategyEvidenceMemoryConfidenceLadderRow:
            raise ValueError(
                "rows must contain ResearchStrategyEvidenceMemoryConfidenceLadderRow",
            )
        _require_hard_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    digests = tuple(row.item_digest for row in normalized)
    if len(set(digests)) != len(digests):
        raise ValueError("rows must have unique item digests")
    return normalized


def _normalize_reason_code_counts(
    rows: tuple[ResearchStrategyEvidenceMemoryConfidenceLadderReasonCodeCount, ...],
) -> tuple[ResearchStrategyEvidenceMemoryConfidenceLadderReasonCodeCount, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchStrategyEvidenceMemoryConfidenceLadderReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyEvidenceMemoryConfidenceLadderReasonCodeCount",
            )
        _require_hard_flags("reason count", row)
    if normalized != tuple(
        sorted(normalized, key=lambda item: (-item.count, item.reason_code)),
    ):
        raise ValueError("reason_code_counts must use deterministic sequence")
    if len(set(row.reason_code for row in normalized)) != len(normalized):
        raise ValueError("reason_code_counts must not contain duplicates")
    return normalized


def _normalize_upstream_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code(
            "reason_codes",
            reason_code,
            _UPSTREAM_REASON_CODE_SEQUENCE,
        )
    normalized = tuple(
        reason_code
        for reason_code in _UPSTREAM_REASON_CODE_SEQUENCE
        if reason_code in value
    )
    if normalized != value:
        raise ValueError("reason_codes must be unique and deterministic")
    return normalized


def _normalize_row_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code, _ROW_REASON_CODE_SEQUENCE)
    normalized = tuple(
        reason_code for reason_code in _ROW_REASON_CODE_SEQUENCE if reason_code in value
    )
    if normalized != value:
        raise ValueError("reason_codes must be unique and deterministic")
    if REASON_CONFIDENCE_LADDER_PASS in value:
        generated = tuple(
            reason_code
            for reason_code in value
            if reason_code in _GENERATED_ROW_REASON_CODE_SEQUENCE
        )
        if generated != (REASON_CONFIDENCE_LADDER_PASS,):
            raise ValueError("reason_codes cannot mix pass with risk reasons")
    return normalized


def _normalize_report_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code, _REASON_CODE_SEQUENCE)
    if len(set(value)) != len(value):
        raise ValueError("reason_codes must be unique and deterministic")
    return value


def _report_payload(
    report: ResearchStrategyEvidenceMemoryConfidenceLadderReport,
) -> dict[str, object]:
    payload = _report_payload_without_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        status=report.status,
        row_count=report.row_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        average_composite_score=report.average_composite_score,
        min_composite_score=report.min_composite_score,
        min_evidence_score=report.min_evidence_score,
        min_memory_score=report.min_memory_score,
        min_confidence_score=report.min_confidence_score,
        rows=report.rows,
        reason_code_counts=report.reason_code_counts,
        reason_codes=report.reason_codes,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )
    payload[_DIGEST_FIELD] = report.derived_validation_digest
    return payload


def _report_payload_without_digest(**values: object) -> dict[str, object]:
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _report_digest(report: ResearchStrategyEvidenceMemoryConfidenceLadderReport) -> str:
    return _report_digest_from_values(
        {
            "generated_at": report.generated_at,
            "config_version": report.config_version,
            "status": report.status,
            "row_count": report.row_count,
            "pass_count": report.pass_count,
            "watch_count": report.watch_count,
            "block_count": report.block_count,
            "average_composite_score": report.average_composite_score,
            "min_composite_score": report.min_composite_score,
            "min_evidence_score": report.min_evidence_score,
            "min_memory_score": report.min_memory_score,
            "min_confidence_score": report.min_confidence_score,
            "rows": report.rows,
            "reason_code_counts": report.reason_code_counts,
            "reason_codes": report.reason_codes,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        payload,
        allow_json_containers=True,
    )
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _validate_payload_digest(payload: dict[str, object]) -> None:
    digest = payload.get(_DIGEST_FIELD)
    _require_digest(_DIGEST_FIELD, digest)
    payload_without_digest = dict(payload)
    payload_without_digest.pop(_DIGEST_FIELD, None)
    canonical = json.dumps(
        payload_without_digest,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    expected = sha256(canonical.encode("utf-8")).hexdigest()
    if digest != expected:
        raise ValueError("derived_validation_digest mismatch")


def _validate_payload_semantics(payload: dict[str, object]) -> None:
    config = ResearchStrategyEvidenceMemoryConfidenceLadderConfig(
        config_version=_require_public_identifier(
            "config_version",
            payload["config_version"],
        ),
    )
    rows_value = payload["rows"]
    if type(rows_value) is not list:
        raise ValueError("rows must be a list")
    reason_counts_value = payload["reason_code_counts"]
    if type(reason_counts_value) is not list:
        raise ValueError("reason_code_counts must be a list")
    ResearchStrategyEvidenceMemoryConfidenceLadderReport(
        generated_at=_require_payload_datetime("generated_at", payload["generated_at"]),
        config_version=config.config_version,
        status=_require_status("status", payload["status"]),
        row_count=_payload_count_decimal("row_count", payload["row_count"]),
        pass_count=_payload_count_decimal("pass_count", payload["pass_count"]),
        watch_count=_payload_count_decimal("watch_count", payload["watch_count"]),
        block_count=_payload_count_decimal("block_count", payload["block_count"]),
        average_composite_score=_payload_ratio_decimal(
            "average_composite_score",
            payload["average_composite_score"],
        ),
        min_composite_score=_payload_ratio_decimal(
            "min_composite_score",
            payload["min_composite_score"],
        ),
        min_evidence_score=_payload_ratio_decimal(
            "min_evidence_score",
            payload["min_evidence_score"],
        ),
        min_memory_score=_payload_ratio_decimal(
            "min_memory_score",
            payload["min_memory_score"],
        ),
        min_confidence_score=_payload_ratio_decimal(
            "min_confidence_score",
            payload["min_confidence_score"],
        ),
        rows=tuple(_row_from_payload(row, config) for row in rows_value),
        reason_code_counts=tuple(
            _reason_count_from_payload(row) for row in reason_counts_value
        ),
        reason_codes=_payload_reason_codes(
            "reason_codes",
            payload["reason_codes"],
            _REASON_CODE_SEQUENCE,
        ),
        derived_validation_digest=payload[_DIGEST_FIELD],
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _row_from_payload(
    payload: object,
    config: ResearchStrategyEvidenceMemoryConfidenceLadderConfig,
) -> ResearchStrategyEvidenceMemoryConfidenceLadderRow:
    if type(payload) is not dict:
        raise ValueError("rows must contain objects")
    return ResearchStrategyEvidenceMemoryConfidenceLadderRow(
        item_digest=_require_private_digest("item_digest", payload["item_digest"]),
        evidence_score=_payload_ratio_decimal(
            "evidence_score",
            payload["evidence_score"],
        ),
        evidence_gap_score=_payload_ratio_decimal(
            "evidence_gap_score",
            payload["evidence_gap_score"],
        ),
        memory_score=_payload_ratio_decimal("memory_score", payload["memory_score"]),
        memory_gap_score=_payload_ratio_decimal(
            "memory_gap_score",
            payload["memory_gap_score"],
        ),
        confidence_score=_payload_ratio_decimal(
            "confidence_score",
            payload["confidence_score"],
        ),
        confidence_gap_score=_payload_ratio_decimal(
            "confidence_gap_score",
            payload["confidence_gap_score"],
        ),
        composite_score=_payload_ratio_decimal(
            "composite_score",
            payload["composite_score"],
        ),
        observed_at=_require_payload_datetime("observed_at", payload["observed_at"]),
        status=_require_status("status", payload["status"]),
        reason_codes=_payload_reason_codes(
            "reason_codes",
            payload["reason_codes"],
            _ROW_REASON_CODE_SEQUENCE,
        ),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
        validation_config=config,
    )


def _reason_count_from_payload(
    payload: object,
) -> ResearchStrategyEvidenceMemoryConfidenceLadderReasonCodeCount:
    if type(payload) is not dict:
        raise ValueError("reason_code_counts must contain objects")
    return ResearchStrategyEvidenceMemoryConfidenceLadderReasonCodeCount(
        reason_code=_require_reason_code(
            "reason_code",
            payload["reason_code"],
            _REASON_CODE_SEQUENCE,
        ),
        count=_payload_count_decimal("count", payload["count"]),
        row_ratio=_payload_ratio_decimal("row_ratio", payload["row_ratio"]),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _payload_reason_codes(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return tuple(
        _require_reason_code(field_name, reason_code, allowed_values)
        for reason_code in value
    )


def _validate_payload_shape(payload: dict[str, object]) -> None:
    _require_payload_fields("payload", payload, _TOP_LEVEL_PAYLOAD_FIELDS)
    for field_name in _PHASE_FLAG_FIELDS:
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    for field_name in (
        "row_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_composite_score",
        "min_composite_score",
        "min_evidence_score",
        "min_memory_score",
        "min_confidence_score",
    ):
        _require_payload_decimal_string(field_name, payload[field_name])
    _require_digest(_DIGEST_FIELD, payload[_DIGEST_FIELD])
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain objects")
        _validate_row_payload(row)
    reason_counts = payload["reason_code_counts"]
    if type(reason_counts) is not list:
        raise ValueError("reason_code_counts must be a list")
    for row in reason_counts:
        if type(row) is not dict:
            raise ValueError("reason_code_counts must contain objects")
        _validate_reason_count_payload(row)
    reason_codes = payload["reason_codes"]
    if type(reason_codes) is not list:
        raise ValueError("reason_codes must be a list")
    for reason_code in reason_codes:
        _require_reason_code("reason_codes", reason_code, _REASON_CODE_SEQUENCE)


def _validate_row_payload(payload: dict[str, object]) -> None:
    _require_payload_fields("row", payload, _ROW_PAYLOAD_FIELDS)
    for field_name in _PHASE_FLAG_FIELDS:
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    _require_private_digest("item_digest", payload["item_digest"])
    for field_name in (
        "evidence_score",
        "evidence_gap_score",
        "memory_score",
        "memory_gap_score",
        "confidence_score",
        "confidence_gap_score",
        "composite_score",
    ):
        _require_payload_decimal_string(field_name, payload[field_name])
    if payload["status"] not in _STATUS_VALUES:
        raise ValueError("status must be pass, watch, or block")
    reason_codes = payload["reason_codes"]
    if type(reason_codes) is not list:
        raise ValueError("reason_codes must be a list")
    for reason_code in reason_codes:
        _require_reason_code("reason_codes", reason_code, _ROW_REASON_CODE_SEQUENCE)


def _validate_reason_count_payload(payload: dict[str, object]) -> None:
    _require_payload_fields("reason_code_count", payload, _REASON_COUNT_PAYLOAD_FIELDS)
    for field_name in _PHASE_FLAG_FIELDS:
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    _require_reason_code("reason_code", payload["reason_code"], _REASON_CODE_SEQUENCE)
    _require_payload_decimal_string("count", payload["count"])
    _require_payload_decimal_string("row_ratio", payload["row_ratio"])


def _require_payload_fields(
    label: str,
    payload: dict[str, object],
    expected_fields: frozenset[str],
) -> None:
    keys = frozenset(payload)
    extras = keys - expected_fields
    if extras:
        raise ValueError(f"unexpected payload field: {sorted(extras)[0]}")
    missing = expected_fields - keys
    if missing:
        raise ValueError(f"missing payload field: {sorted(missing)[0]}")
    if not label:
        raise ValueError("payload label is required")


def _validate_payload_statuses(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key == "status" and item not in _STATUS_VALUES:
                raise ValueError("status must be pass, watch, or block")
            _validate_payload_statuses(item)
        return
    if isinstance(value, list):
        for item in value:
            _validate_payload_statuses(item)


def _copy_json_object(value: dict[str, object]) -> dict[str, object]:
    copied = _copy_json_value(value)
    if type(copied) is not dict:
        raise ValueError("payload must be a JSON object")
    return copied


def _copy_json_value(value: object) -> object:
    if value is None or type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("payload numeric values must be Decimal strings")
    if isinstance(value, Mapping):
        copied: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            copied[key] = _copy_json_value(item)
        return copied
    if isinstance(value, list):
        return [_copy_json_value(item) for item in value]
    raise ValueError("payload contains unsupported JSON value")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        ready: dict[str, Any] = {}
        for field in fields(value):
            ready[field.name] = _json_ready(getattr(value, field.name))
        return ready
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
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
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{current_path} keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        folded = value.casefold()
        for fragment in _UNSAFE_PUBLIC_FRAGMENTS:
            if fragment in folded:
                raise ValueError(f"unsafe public value at {current_path}")
        return
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    raise ValueError(f"{current_path} contains unsupported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    folded = key.casefold()
    for fragment in _UNSAFE_PUBLIC_FRAGMENTS:
        if fragment in folded:
            raise ValueError(f"unsafe public field at {path}.{key}")


def _require_exact_type(value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{expected_type.__name__} must not be subclassed")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if _PUBLIC_IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public identifier")
    return value


def _require_private_reference(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() == "":
        raise ValueError(f"{field_name} must be non-empty")
    return value


def _require_reason_code(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed_values:
        raise ValueError(f"{field_name} contains an unsupported reason code")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUS_VALUES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO or decimal_value > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_payload_decimal_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if str(_quantize(decimal_value)) != value:
        raise ValueError(f"{field_name} must be a six-place Decimal string")
    return decimal_value


def _payload_count_decimal(field_name: str, value: object) -> Decimal:
    return _require_count_decimal(
        field_name,
        _require_payload_decimal_string(field_name, value),
    )


def _payload_ratio_decimal(field_name: str, value: object) -> Decimal:
    return _require_ratio_decimal(
        field_name,
        _require_payload_decimal_string(field_name, value),
    )


def _require_payload_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO datetime")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime") from exc
    return _as_utc(field_name, parsed)


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str or _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _require_private_digest(field_name: str, value: object) -> str:
    if type(value) is not str or _PRIVATE_DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 private digest")
    return value


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(_QUANT)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    return _clamp_ratio(numerator / denominator)


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _ratio(sum(values, _ZERO), _decimal_count(len(values)))


def _inverse_ratio(value: Decimal) -> Decimal:
    return _clamp_ratio(_ONE - value)


def _clamp_ratio(value: Decimal) -> Decimal:
    quantized = _quantize(value)
    if quantized < _ZERO:
        return _ZERO
    if quantized > _ONE:
        return _ONE
    return quantized


def _private_reference_digest(value: str) -> str:
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_EVIDENCE_MEMORY_CONFIDENCE_LADDER_CONFIG_VERSION",
    "ResearchStrategyEvidenceMemoryConfidenceLadderConfig",
    "ResearchStrategyEvidenceMemoryConfidenceLadderInput",
    "ResearchStrategyEvidenceMemoryConfidenceLadderReasonCodeCount",
    "ResearchStrategyEvidenceMemoryConfidenceLadderReport",
    "ResearchStrategyEvidenceMemoryConfidenceLadderRow",
    "build_research_strategy_evidence_memory_confidence_ladder_report",
    "research_strategy_evidence_memory_confidence_ladder_report_payload",
    "validate_research_strategy_evidence_memory_confidence_ladder_public_payload",
)
