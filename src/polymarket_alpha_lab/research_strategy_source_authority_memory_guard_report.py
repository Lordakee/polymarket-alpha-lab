"""Pure report-only source authority and memory guard report."""

from __future__ import annotations

from collections import Counter
from dataclasses import InitVar, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from types import MappingProxyType
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_STRATEGY_SOURCE_AUTHORITY_MEMORY_GUARD_CONFIG_VERSION = (
    "research-strategy-source-authority-memory-guard-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
RESEARCH_STRATEGY_SOURCE_AUTHORITY_MEMORY_GUARD_STATUSES = (
    STATUS_PASS,
    STATUS_WATCH,
    STATUS_BLOCK,
)

REASON_EMPTY_INPUT = "empty_input"
REASON_AUTHORITY_BLOCK = "authority_score_block"
REASON_MEMORY_BLOCK = "memory_alignment_block"
REASON_FRESHNESS_BLOCK = "freshness_age_block"
REASON_COMPOSITE_BLOCK = "composite_guard_block"
REASON_AUTHORITY_WATCH = "authority_score_watch"
REASON_MEMORY_WATCH = "memory_alignment_watch"
REASON_FRESHNESS_WATCH = "freshness_age_watch"
REASON_COMPOSITE_WATCH = "composite_guard_watch"
REASON_PASS = "authority_memory_guard_pass"

_ROW_REASON_CODE_SEQUENCE = (
    REASON_AUTHORITY_BLOCK,
    REASON_MEMORY_BLOCK,
    REASON_FRESHNESS_BLOCK,
    REASON_COMPOSITE_BLOCK,
    REASON_AUTHORITY_WATCH,
    REASON_MEMORY_WATCH,
    REASON_FRESHNESS_WATCH,
    REASON_COMPOSITE_WATCH,
    REASON_PASS,
)
_REPORT_REASON_CODE_SEQUENCE = (REASON_EMPTY_INPUT, *_ROW_REASON_CODE_SEQUENCE)
_BLOCK_REASON_CODES = frozenset(
    (
        REASON_AUTHORITY_BLOCK,
        REASON_MEMORY_BLOCK,
        REASON_FRESHNESS_BLOCK,
        REASON_COMPOSITE_BLOCK,
    ),
)
_WATCH_REASON_CODES = frozenset(
    (
        REASON_AUTHORITY_WATCH,
        REASON_MEMORY_WATCH,
        REASON_FRESHNESS_WATCH,
        REASON_COMPOSITE_WATCH,
    ),
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_UP)
_STATUS_RANK = {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_ITEM_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_CONFIG_PAYLOAD_FIELDS = (
    "config_version",
    "pass_min_guard_score",
    "watch_min_guard_score",
    "min_pass_authority_score",
    "min_watch_authority_score",
    "min_pass_memory_alignment_score",
    "min_watch_memory_alignment_score",
    "freshness_watch_age_seconds",
    "freshness_block_age_seconds",
    "authority_weight",
    "memory_weight",
    "freshness_weight",
    "paper_only",
    "report_only",
    "readonly",
)
_TOP_LEVEL_PAYLOAD_FIELDS = (
    "generated_at",
    "config_version",
    "config",
    "status",
    "row_count",
    "pass_count",
    "watch_count",
    "block_count",
    "average_guard_score",
    "min_guard_score",
    "min_authority_score",
    "min_memory_alignment_score",
    "max_evidence_freshness_age_seconds",
    "rows",
    "reason_code_counts",
    "reason_codes",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
_ROW_PAYLOAD_FIELDS = (
    "item_digest",
    "authority_score",
    "authority_gap_score",
    "memory_alignment_score",
    "memory_gap_score",
    "evidence_freshness_age_seconds",
    "freshness_score",
    "authority_quorum_count",
    "guard_score",
    "observed_at",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
_REASON_COUNT_PAYLOAD_FIELDS = (
    "reason_code",
    "count",
    "row_ratio",
    "paper_only",
    "report_only",
    "readonly",
)
_UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "raw_candidate",
    "candidate_id",
    "candidate-id",
    "market_id",
    "market-id",
    "market_slug",
    "market-slug",
    "source_url",
    "source-url",
    "source_text",
    "source-text",
    "raw_url",
    "raw-url",
    "url",
    "dsn",
    "table",
    "token",
)
_UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "raw_candidate",
    "candidate_id",
    "market_id",
    "market_slug",
    "source_url",
    "source_text",
    "http://",
    "https://",
    "www.",
    "postgres://",
    "mysql://",
    "jdbc:",
    "dsn",
    "table",
    "token",
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


@dataclass(frozen=True, slots=True)
class ResearchStrategySourceAuthorityMemoryGuardConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_SOURCE_AUTHORITY_MEMORY_GUARD_CONFIG_VERSION
    )
    pass_min_guard_score: Decimal = Decimal("0.800000")
    watch_min_guard_score: Decimal = Decimal("0.600000")
    min_pass_authority_score: Decimal = Decimal("0.800000")
    min_watch_authority_score: Decimal = Decimal("0.600000")
    min_pass_memory_alignment_score: Decimal = Decimal("0.750000")
    min_watch_memory_alignment_score: Decimal = Decimal("0.550000")
    freshness_watch_age_seconds: Decimal = Decimal("86400.000000")
    freshness_block_age_seconds: Decimal = Decimal("259200.000000")
    authority_weight: Decimal = Decimal("0.500000")
    memory_weight: Decimal = Decimal("0.300000")
    freshness_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategySourceAuthorityMemoryGuardConfig)
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_SOURCE_AUTHORITY_MEMORY_GUARD_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_min_guard_score",
            "watch_min_guard_score",
            "min_pass_authority_score",
            "min_watch_authority_score",
            "min_pass_memory_alignment_score",
            "min_watch_memory_alignment_score",
            "authority_weight",
            "memory_weight",
            "freshness_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "freshness_watch_age_seconds",
            "freshness_block_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True, slots=True)
class ResearchStrategySourceAuthorityMemoryGuardInput(_FinalPublicDataclass):
    private_reference: str
    authority_score: Decimal
    memory_alignment_score: Decimal
    evidence_freshness_age_seconds: Decimal
    authority_quorum_count: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategySourceAuthorityMemoryGuardInput)
        object.__setattr__(
            self,
            "private_reference",
            _require_private_reference("private_reference", self.private_reference),
        )
        for field_name in ("authority_score", "memory_alignment_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_freshness_age_seconds",
            _require_nonnegative_decimal(
                "evidence_freshness_age_seconds",
                self.evidence_freshness_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "authority_quorum_count",
            _require_nonnegative_whole_decimal(
                "authority_quorum_count",
                self.authority_quorum_count,
            ),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_input_reason_codes(self.reason_codes),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True, slots=True)
class ResearchStrategySourceAuthorityMemoryGuardRow(_FinalPublicDataclass):
    item_digest: str
    authority_score: Decimal
    authority_gap_score: Decimal
    memory_alignment_score: Decimal
    memory_gap_score: Decimal
    evidence_freshness_age_seconds: Decimal
    freshness_score: Decimal
    authority_quorum_count: Decimal
    guard_score: Decimal
    observed_at: datetime
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[
        ResearchStrategySourceAuthorityMemoryGuardConfig | None
    ] = None

    def __post_init__(
        self,
        validation_config: ResearchStrategySourceAuthorityMemoryGuardConfig | None,
    ) -> None:
        _require_exact_type(self, ResearchStrategySourceAuthorityMemoryGuardRow)
        object.__setattr__(
            self,
            "item_digest",
            _require_item_digest("item_digest", self.item_digest),
        )
        for field_name in (
            "authority_score",
            "authority_gap_score",
            "memory_alignment_score",
            "memory_gap_score",
            "freshness_score",
            "guard_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_freshness_age_seconds",
            _require_nonnegative_decimal(
                "evidence_freshness_age_seconds",
                self.evidence_freshness_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "authority_quorum_count",
            _require_nonnegative_whole_decimal(
                "authority_quorum_count",
                self.authority_quorum_count,
            ),
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
        _reject_unsafe_public_payload(_json_ready(self), label="row")


@dataclass(frozen=True, slots=True)
class ResearchStrategySourceAuthorityMemoryGuardReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategySourceAuthorityMemoryGuardReasonCodeCount)
        _require_reason_code("reason_code", self.reason_code, _REPORT_REASON_CODE_SEQUENCE)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_whole_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload(_json_ready(self), label="reason_code_count")


@dataclass(frozen=True, slots=True)
class ResearchStrategySourceAuthorityMemoryGuardReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    config: ResearchStrategySourceAuthorityMemoryGuardConfig
    status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_guard_score: Decimal
    min_guard_score: Decimal
    min_authority_score: Decimal
    min_memory_alignment_score: Decimal
    max_evidence_freshness_age_seconds: Decimal
    rows: tuple[ResearchStrategySourceAuthorityMemoryGuardRow, ...]
    reason_code_counts: tuple[
        ResearchStrategySourceAuthorityMemoryGuardReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategySourceAuthorityMemoryGuardReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_SOURCE_AUTHORITY_MEMORY_GUARD_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        if type(self.config) is not ResearchStrategySourceAuthorityMemoryGuardConfig:
            raise ValueError(
                "config must be a ResearchStrategySourceAuthorityMemoryGuardConfig",
            )
        _require_hard_flags("report.config", self.config)
        if self.config_version != self.config.config_version:
            raise ValueError("config_version must match config")
        _require_status("status", self.status)
        for field_name in ("row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_guard_score",
            "min_guard_score",
            "min_authority_score",
            "min_memory_alignment_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_evidence_freshness_age_seconds",
            _require_nonnegative_decimal(
                "max_evidence_freshness_age_seconds",
                self.max_evidence_freshness_age_seconds,
            ),
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
        _reject_unsafe_public_payload(_json_ready(self), label="report")
        expected_digest = _report_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> Mapping[str, Any]:
        return research_strategy_source_authority_memory_guard_report_payload(self)


def build_research_strategy_source_authority_memory_guard_report(
    inputs: Sequence[ResearchStrategySourceAuthorityMemoryGuardInput],
    *,
    generated_at: datetime,
    config: ResearchStrategySourceAuthorityMemoryGuardConfig,
) -> ResearchStrategySourceAuthorityMemoryGuardReport:
    if type(config) is not ResearchStrategySourceAuthorityMemoryGuardConfig:
        raise ValueError("config must be a ResearchStrategySourceAuthorityMemoryGuardConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    for item in normalized_inputs:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must be at or before generated_at")
    rows = _sorted_rows(_row_from_input(item, config=config) for item in normalized_inputs)
    reason_codes = _report_reason_codes(rows)
    return ResearchStrategySourceAuthorityMemoryGuardReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        config=config,
        status=_report_status(rows),
        row_count=_count_decimal(len(rows)),
        pass_count=_count_status(rows, STATUS_PASS),
        watch_count=_count_status(rows, STATUS_WATCH),
        block_count=_count_status(rows, STATUS_BLOCK),
        average_guard_score=_average(row.guard_score for row in rows),
        min_guard_score=_minimum(row.guard_score for row in rows),
        min_authority_score=_minimum(row.authority_score for row in rows),
        min_memory_alignment_score=_minimum(
            tuple(row.memory_alignment_score for row in rows),
        ),
        max_evidence_freshness_age_seconds=_maximum_measure(
            tuple(row.evidence_freshness_age_seconds for row in rows),
        ),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows),
        reason_codes=reason_codes,
    )


def research_strategy_source_authority_memory_guard_report_payload(
    report_or_payload: (
        ResearchStrategySourceAuthorityMemoryGuardReport | Mapping[str, Any]
    ),
) -> Mapping[str, Any]:
    if isinstance(report_or_payload, ResearchStrategySourceAuthorityMemoryGuardReport):
        payload = _json_ready(report_or_payload)
    elif isinstance(report_or_payload, Mapping):
        payload = _plain_json_ready(
            report_or_payload,
            allow_frozen=type(report_or_payload) is MappingProxyType,
        )
    else:
        raise ValueError("report payload must be a report or mapping")
    validate_research_strategy_source_authority_memory_guard_public_payload(payload)
    return _freeze(payload)


def research_strategy_source_authority_memory_guard_report_digest(
    report: ResearchStrategySourceAuthorityMemoryGuardReport,
) -> str:
    if type(report) is not ResearchStrategySourceAuthorityMemoryGuardReport:
        raise ValueError("report must be a ResearchStrategySourceAuthorityMemoryGuardReport")
    return _report_digest(report)


def validate_research_strategy_source_authority_memory_guard_report_digest(
    report: ResearchStrategySourceAuthorityMemoryGuardReport,
) -> bool:
    if type(report) is not ResearchStrategySourceAuthorityMemoryGuardReport:
        raise ValueError("report must be a ResearchStrategySourceAuthorityMemoryGuardReport")
    _validate_report(report)
    _require_hard_flags("report", report)
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest does not match report payload")
    return True


def validate_research_strategy_source_authority_memory_guard_public_payload(
    payload: Mapping[str, Any],
) -> bool:
    normalized = _plain_json_ready(
        payload,
        allow_frozen=type(payload) is MappingProxyType,
    )
    _validate_payload_schema(normalized)
    _reject_unsafe_public_payload(normalized, label="public_payload")
    expected_digest = _payload_digest(normalized)
    if normalized.get("derived_validation_digest") != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    return True


def _validate_config(
    config: ResearchStrategySourceAuthorityMemoryGuardConfig,
) -> None:
    if config.pass_min_guard_score < config.watch_min_guard_score:
        raise ValueError("pass_min_guard_score must be at least watch_min_guard_score")
    if config.min_pass_authority_score < config.min_watch_authority_score:
        raise ValueError(
            "min_pass_authority_score must be at least min_watch_authority_score",
        )
    if config.min_pass_memory_alignment_score < config.min_watch_memory_alignment_score:
        raise ValueError(
            "min_pass_memory_alignment_score must be at least "
            "min_watch_memory_alignment_score",
        )
    if config.freshness_block_age_seconds <= config.freshness_watch_age_seconds:
        raise ValueError(
            "freshness_block_age_seconds must exceed freshness_watch_age_seconds",
        )
    with localcontext(_DECIMAL_CONTEXT):
        weight_sum = _quantize(
            config.authority_weight + config.memory_weight + config.freshness_weight,
        )
    if weight_sum != _ONE:
        raise ValueError("guard weights must sum to one")


def _row_from_input(
    item: ResearchStrategySourceAuthorityMemoryGuardInput,
    *,
    config: ResearchStrategySourceAuthorityMemoryGuardConfig,
) -> ResearchStrategySourceAuthorityMemoryGuardRow:
    freshness_score = _freshness_score(item.evidence_freshness_age_seconds, config)
    with localcontext(_DECIMAL_CONTEXT):
        guard_score = _quantize(
            item.authority_score * config.authority_weight
            + item.memory_alignment_score * config.memory_weight
            + freshness_score * config.freshness_weight,
        )
        authority_gap_score = _quantize(_ONE - item.authority_score)
        memory_gap_score = _quantize(_ONE - item.memory_alignment_score)
    reason_codes = _row_reason_codes(
        authority_score=item.authority_score,
        memory_alignment_score=item.memory_alignment_score,
        evidence_freshness_age_seconds=item.evidence_freshness_age_seconds,
        guard_score=guard_score,
        config=config,
    )
    return ResearchStrategySourceAuthorityMemoryGuardRow(
        item_digest=_digest_private_reference(item.private_reference),
        authority_score=item.authority_score,
        authority_gap_score=authority_gap_score,
        memory_alignment_score=item.memory_alignment_score,
        memory_gap_score=memory_gap_score,
        evidence_freshness_age_seconds=item.evidence_freshness_age_seconds,
        freshness_score=freshness_score,
        authority_quorum_count=item.authority_quorum_count,
        guard_score=guard_score,
        observed_at=item.observed_at,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _row_reason_codes(
    *,
    authority_score: Decimal,
    memory_alignment_score: Decimal,
    evidence_freshness_age_seconds: Decimal,
    guard_score: Decimal,
    config: ResearchStrategySourceAuthorityMemoryGuardConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if authority_score < config.min_watch_authority_score:
        reason_codes.append(REASON_AUTHORITY_BLOCK)
    elif authority_score < config.min_pass_authority_score:
        reason_codes.append(REASON_AUTHORITY_WATCH)

    if memory_alignment_score < config.min_watch_memory_alignment_score:
        reason_codes.append(REASON_MEMORY_BLOCK)
    elif memory_alignment_score < config.min_pass_memory_alignment_score:
        reason_codes.append(REASON_MEMORY_WATCH)

    if evidence_freshness_age_seconds >= config.freshness_block_age_seconds:
        reason_codes.append(REASON_FRESHNESS_BLOCK)
    elif evidence_freshness_age_seconds >= config.freshness_watch_age_seconds:
        reason_codes.append(REASON_FRESHNESS_WATCH)

    if guard_score < config.watch_min_guard_score:
        reason_codes.append(REASON_COMPOSITE_BLOCK)
    elif guard_score < config.pass_min_guard_score:
        reason_codes.append(REASON_COMPOSITE_WATCH)

    if not reason_codes:
        reason_codes.append(REASON_PASS)
    return tuple(reason for reason in _ROW_REASON_CODE_SEQUENCE if reason in reason_codes)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason in _BLOCK_REASON_CODES for reason in reason_codes):
        return STATUS_BLOCK
    if any(reason in _WATCH_REASON_CODES for reason in reason_codes):
        return STATUS_WATCH
    return STATUS_PASS


def _freshness_score(
    evidence_freshness_age_seconds: Decimal,
    config: ResearchStrategySourceAuthorityMemoryGuardConfig,
) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        raw_score = _ONE - (
            evidence_freshness_age_seconds / config.freshness_block_age_seconds
        )
    if raw_score < _ZERO:
        return _ZERO
    if raw_score > _ONE:
        return _ONE
    return _quantize(raw_score)


def _validate_row(
    row: ResearchStrategySourceAuthorityMemoryGuardRow,
    config: ResearchStrategySourceAuthorityMemoryGuardConfig | None,
) -> None:
    with localcontext(_DECIMAL_CONTEXT):
        expected_authority_gap = _quantize(_ONE - row.authority_score)
        expected_memory_gap = _quantize(_ONE - row.memory_alignment_score)
    if row.authority_gap_score != expected_authority_gap:
        raise ValueError("authority_gap_score does not match authority_score")
    if row.memory_gap_score != expected_memory_gap:
        raise ValueError("memory_gap_score does not match memory_alignment_score")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status does not match reason_codes")
    if row.status == STATUS_PASS and row.reason_codes != (REASON_PASS,):
        raise ValueError("reason_codes do not match pass status")
    if config is not None:
        if type(config) is not ResearchStrategySourceAuthorityMemoryGuardConfig:
            raise ValueError("validation_config must be a guard config")
        expected_freshness = _freshness_score(
            row.evidence_freshness_age_seconds,
            config,
        )
        if row.freshness_score != expected_freshness:
            raise ValueError("freshness_score does not match config")
        with localcontext(_DECIMAL_CONTEXT):
            expected_guard_score = _quantize(
                row.authority_score * config.authority_weight
                + row.memory_alignment_score * config.memory_weight
                + expected_freshness * config.freshness_weight,
            )
        if row.guard_score != expected_guard_score:
            raise ValueError("guard_score does not match config")
        expected_reasons = _row_reason_codes(
            authority_score=row.authority_score,
            memory_alignment_score=row.memory_alignment_score,
            evidence_freshness_age_seconds=row.evidence_freshness_age_seconds,
            guard_score=row.guard_score,
            config=config,
        )
        if row.reason_codes != expected_reasons:
            raise ValueError("reason_codes do not match config")


def _validate_report(report: ResearchStrategySourceAuthorityMemoryGuardReport) -> None:
    if type(report.config) is not ResearchStrategySourceAuthorityMemoryGuardConfig:
        raise ValueError("config must be a guard config")
    _require_hard_flags("report.config", report.config)
    if report.config_version != report.config.config_version:
        raise ValueError("config_version does not match config")
    for row in report.rows:
        _validate_row(row, report.config)
        if row.observed_at > report.generated_at:
            raise ValueError("row.observed_at must be at or before generated_at")
    row_count = _count_decimal(len(report.rows))
    if report.row_count != row_count:
        raise ValueError("row_count does not match rows")
    if report.pass_count != _count_status(report.rows, STATUS_PASS):
        raise ValueError("pass_count does not match rows")
    if report.watch_count != _count_status(report.rows, STATUS_WATCH):
        raise ValueError("watch_count does not match rows")
    if report.block_count != _count_status(report.rows, STATUS_BLOCK):
        raise ValueError("block_count does not match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status does not match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes do not match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts do not match rows")
    if report.average_guard_score != _average(row.guard_score for row in report.rows):
        raise ValueError("average_guard_score does not match rows")
    if report.min_guard_score != _minimum(row.guard_score for row in report.rows):
        raise ValueError("min_guard_score does not match rows")
    if report.min_authority_score != _minimum(row.authority_score for row in report.rows):
        raise ValueError("min_authority_score does not match rows")
    if report.min_memory_alignment_score != _minimum(
        tuple(row.memory_alignment_score for row in report.rows)
    ):
        raise ValueError("min_memory_alignment_score does not match rows")
    if report.max_evidence_freshness_age_seconds != _maximum_measure(
        tuple(row.evidence_freshness_age_seconds for row in report.rows)
    ):
        raise ValueError("max_evidence_freshness_age_seconds does not match rows")


def _report_status(
    rows: tuple[ResearchStrategySourceAuthorityMemoryGuardRow, ...],
) -> str:
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _count_status(
    rows: tuple[ResearchStrategySourceAuthorityMemoryGuardRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _report_reason_codes(
    rows: tuple[ResearchStrategySourceAuthorityMemoryGuardRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (REASON_EMPTY_INPUT,)
    found = {reason for row in rows for reason in row.reason_codes}
    return tuple(reason for reason in _ROW_REASON_CODE_SEQUENCE if reason in found)


def _reason_code_counts(
    rows: tuple[ResearchStrategySourceAuthorityMemoryGuardRow, ...],
) -> tuple[ResearchStrategySourceAuthorityMemoryGuardReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategySourceAuthorityMemoryGuardReasonCodeCount(
                reason_code=REASON_EMPTY_INPUT,
                count=_ONE,
                row_ratio=_ONE,
            ),
        )
    counts = Counter(reason for row in rows for reason in row.reason_codes)
    row_count = _count_decimal(len(rows))
    return tuple(
        ResearchStrategySourceAuthorityMemoryGuardReasonCodeCount(
            reason_code=reason,
            count=_count_decimal(counts[reason]),
            row_ratio=_safe_ratio(_count_decimal(counts[reason]), row_count),
        )
        for reason in _ROW_REASON_CODE_SEQUENCE
        if counts[reason] > 0
    )


def _sorted_rows(
    rows: Sequence[ResearchStrategySourceAuthorityMemoryGuardRow],
) -> tuple[ResearchStrategySourceAuthorityMemoryGuardRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _STATUS_RANK[row.status],
                row.guard_score,
                row.item_digest,
                row.authority_score,
                row.authority_gap_score,
                row.memory_alignment_score,
                row.memory_gap_score,
                row.evidence_freshness_age_seconds,
                row.freshness_score,
                row.authority_quorum_count,
                row.observed_at,
                row.reason_codes,
            ),
        ),
    )


def _normalize_inputs(
    inputs: Sequence[ResearchStrategySourceAuthorityMemoryGuardInput],
) -> tuple[ResearchStrategySourceAuthorityMemoryGuardInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be a sequence of guard inputs")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be a sequence of guard inputs") from exc
    for item in normalized:
        if type(item) is not ResearchStrategySourceAuthorityMemoryGuardInput:
            raise ValueError("inputs must contain guard inputs")
        _require_hard_flags("input", item)
    return normalized


def _normalize_rows(
    rows: Sequence[ResearchStrategySourceAuthorityMemoryGuardRow],
) -> tuple[ResearchStrategySourceAuthorityMemoryGuardRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be a sequence of guard rows")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be a sequence of guard rows") from exc
    for row in normalized:
        if type(row) is not ResearchStrategySourceAuthorityMemoryGuardRow:
            raise ValueError("rows must contain guard rows")
        _require_hard_flags("row", row)
    if normalized != _sorted_rows(normalized):
        raise ValueError("rows must be in deterministic report sequence")
    return normalized


def _normalize_reason_code_counts(
    counts: Sequence[ResearchStrategySourceAuthorityMemoryGuardReasonCodeCount],
) -> tuple[ResearchStrategySourceAuthorityMemoryGuardReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)):
        raise ValueError("reason_code_counts must be a sequence")
    try:
        normalized = tuple(counts)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be a sequence") from exc
    for count in normalized:
        if type(count) is not ResearchStrategySourceAuthorityMemoryGuardReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count rows")
        _require_hard_flags("reason_code_count", count)
    expected = tuple(
        reason for reason in _REPORT_REASON_CODE_SEQUENCE if reason in {c.reason_code for c in normalized}
    )
    if tuple(count.reason_code for count in normalized) != expected:
        raise ValueError("reason_code_counts must follow deterministic reason sequence")
    return normalized


def _normalize_input_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be a sequence of strings")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be a sequence of strings") from exc
    for reason in normalized:
        _require_public_identifier("reason_codes", reason)
        if reason in _UNSAFE_PUBLIC_VALUE_FRAGMENTS:
            raise ValueError("reason_codes must be public-safe")
    return tuple(dict.fromkeys(normalized))


def _normalize_row_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be a sequence")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be a sequence") from exc
    for reason in normalized:
        _require_reason_code("reason_codes", reason, _ROW_REASON_CODE_SEQUENCE)
    expected = tuple(reason for reason in _ROW_REASON_CODE_SEQUENCE if reason in normalized)
    if normalized != expected:
        raise ValueError("reason_codes must follow deterministic reason sequence")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    return normalized


def _normalize_report_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be a sequence")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be a sequence") from exc
    for reason in normalized:
        _require_reason_code("reason_codes", reason, _REPORT_REASON_CODE_SEQUENCE)
    expected = tuple(
        reason for reason in _REPORT_REASON_CODE_SEQUENCE if reason in normalized
    )
    if normalized != expected:
        raise ValueError("reason_codes must follow deterministic reason sequence")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    return normalized


def _average(values: Sequence[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(
            sum(normalized, _ZERO) / _count_decimal(len(normalized)),
        )


def _minimum(values: Sequence[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return _ZERO
    return min(normalized)


def _maximum_measure(values: Sequence[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return _ZERO
    return max(normalized)


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _count_decimal(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count value must be a nonnegative integer")
    return _quantize(Decimal(value))


def _require_exact_type(value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"value must be exactly {expected_type.__name__}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str or not value or not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    return value


def _require_private_reference(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _require_item_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _ITEM_DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 public pseudonym")
    return value


def _require_reason_code(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be a known reason code")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in RESEARCH_STRATEGY_SOURCE_AUTHORITY_MEMORY_GUARD_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    raw_value = _require_decimal(field_name, value)
    if raw_value < _ZERO or raw_value > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(raw_value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    raw_value = _require_decimal(field_name, value)
    if raw_value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    decimal_value = _quantize(raw_value)
    if decimal_value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    raw_value = _require_decimal(field_name, value)
    if raw_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(raw_value)


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    raw_value = _require_decimal(field_name, value)
    if raw_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if raw_value != raw_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole decimal")
    return _quantize(raw_value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not use signed zero")
    return value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime or value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware datetime")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} utcoffset must not be None")
    return value.astimezone(UTC)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _digest_private_reference(private_reference: str) -> str:
    return f"sha256:{sha256(private_reference.encode('utf-8')).hexdigest()}"


def _report_digest(report: ResearchStrategySourceAuthorityMemoryGuardReport) -> str:
    payload = _json_ready(report)
    return _payload_digest(payload)


def _payload_digest(payload: Mapping[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    # This is a self-consistency digest, not an authentication primitive.
    encoded = json.dumps(
        unsigned,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if type(value) is Decimal:
        return format(value, "f")
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _plain_json_ready(value: Any, *, allow_frozen: bool = False) -> Any:
    if value is None or type(value) in (bool, str):
        return value
    if type(value) in (int, float) or isinstance(value, Decimal):
        raise ValueError("public payload numeric values must be decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload object keys must be strings")
            ready[key] = _plain_json_ready(item, allow_frozen=allow_frozen)
        return ready
    if type(value) is list:
        return [_plain_json_ready(item, allow_frozen=allow_frozen) for item in value]
    if allow_frozen and type(value) is tuple:
        return [_plain_json_ready(item, allow_frozen=True) for item in value]
    raise ValueError("public payload value is not JSON serializable")


def _validate_payload_schema(payload: Mapping[str, Any]) -> None:
    _require_exact_payload_fields(
        "report",
        payload,
        _TOP_LEVEL_PAYLOAD_FIELDS,
    )
    config = _config_from_payload(payload["config"])
    rows_payload = _require_payload_list("rows", payload["rows"])
    rows = tuple(_row_from_payload(row, config=config) for row in rows_payload)
    reason_counts_payload = _require_payload_list(
        "reason_code_counts",
        payload["reason_code_counts"],
    )
    reason_counts = tuple(
        _reason_count_from_payload(count) for count in reason_counts_payload
    )
    report = ResearchStrategySourceAuthorityMemoryGuardReport(
        generated_at=_payload_datetime("generated_at", payload["generated_at"]),
        config_version=_payload_public_identifier(
            "config_version",
            payload["config_version"],
        ),
        config=config,
        status=_payload_status("status", payload["status"]),
        row_count=_payload_decimal("row_count", payload["row_count"]),
        pass_count=_payload_decimal("pass_count", payload["pass_count"]),
        watch_count=_payload_decimal("watch_count", payload["watch_count"]),
        block_count=_payload_decimal("block_count", payload["block_count"]),
        average_guard_score=_payload_decimal(
            "average_guard_score",
            payload["average_guard_score"],
        ),
        min_guard_score=_payload_decimal(
            "min_guard_score",
            payload["min_guard_score"],
        ),
        min_authority_score=_payload_decimal(
            "min_authority_score",
            payload["min_authority_score"],
        ),
        min_memory_alignment_score=_payload_decimal(
            "min_memory_alignment_score",
            payload["min_memory_alignment_score"],
        ),
        max_evidence_freshness_age_seconds=_payload_decimal(
            "max_evidence_freshness_age_seconds",
            payload["max_evidence_freshness_age_seconds"],
        ),
        rows=rows,
        reason_code_counts=reason_counts,
        reason_codes=_payload_reason_codes(
            "reason_codes",
            payload["reason_codes"],
            _REPORT_REASON_CODE_SEQUENCE,
        ),
        derived_validation_digest=_payload_digest_value(
            payload["derived_validation_digest"],
        ),
        paper_only=_payload_flag("paper_only", payload["paper_only"]),
        report_only=_payload_flag("report_only", payload["report_only"]),
        readonly=_payload_flag("readonly", payload["readonly"]),
    )
    if _json_ready(report) != payload:
        raise ValueError("report payload must use canonical report payload schema")


def _config_from_payload(
    payload: Any,
) -> ResearchStrategySourceAuthorityMemoryGuardConfig:
    _require_exact_payload_fields(
        "config",
        payload,
        _CONFIG_PAYLOAD_FIELDS,
    )
    return ResearchStrategySourceAuthorityMemoryGuardConfig(
        config_version=_payload_public_identifier(
            "config.config_version",
            payload["config_version"],
        ),
        pass_min_guard_score=_payload_decimal(
            "config.pass_min_guard_score",
            payload["pass_min_guard_score"],
        ),
        watch_min_guard_score=_payload_decimal(
            "config.watch_min_guard_score",
            payload["watch_min_guard_score"],
        ),
        min_pass_authority_score=_payload_decimal(
            "config.min_pass_authority_score",
            payload["min_pass_authority_score"],
        ),
        min_watch_authority_score=_payload_decimal(
            "config.min_watch_authority_score",
            payload["min_watch_authority_score"],
        ),
        min_pass_memory_alignment_score=_payload_decimal(
            "config.min_pass_memory_alignment_score",
            payload["min_pass_memory_alignment_score"],
        ),
        min_watch_memory_alignment_score=_payload_decimal(
            "config.min_watch_memory_alignment_score",
            payload["min_watch_memory_alignment_score"],
        ),
        freshness_watch_age_seconds=_payload_decimal(
            "config.freshness_watch_age_seconds",
            payload["freshness_watch_age_seconds"],
        ),
        freshness_block_age_seconds=_payload_decimal(
            "config.freshness_block_age_seconds",
            payload["freshness_block_age_seconds"],
        ),
        authority_weight=_payload_decimal(
            "config.authority_weight",
            payload["authority_weight"],
        ),
        memory_weight=_payload_decimal(
            "config.memory_weight",
            payload["memory_weight"],
        ),
        freshness_weight=_payload_decimal(
            "config.freshness_weight",
            payload["freshness_weight"],
        ),
        paper_only=_payload_flag("config.paper_only", payload["paper_only"]),
        report_only=_payload_flag("config.report_only", payload["report_only"]),
        readonly=_payload_flag("config.readonly", payload["readonly"]),
    )


def _row_from_payload(
    row: Any,
    *,
    config: ResearchStrategySourceAuthorityMemoryGuardConfig,
) -> ResearchStrategySourceAuthorityMemoryGuardRow:
    _require_exact_payload_fields("row", row, _ROW_PAYLOAD_FIELDS)
    return ResearchStrategySourceAuthorityMemoryGuardRow(
        item_digest=_payload_item_digest("item_digest", row["item_digest"]),
        authority_score=_payload_decimal("authority_score", row["authority_score"]),
        authority_gap_score=_payload_decimal(
            "authority_gap_score",
            row["authority_gap_score"],
        ),
        memory_alignment_score=_payload_decimal(
            "memory_alignment_score",
            row["memory_alignment_score"],
        ),
        memory_gap_score=_payload_decimal(
            "memory_gap_score",
            row["memory_gap_score"],
        ),
        evidence_freshness_age_seconds=_payload_decimal(
            "evidence_freshness_age_seconds",
            row["evidence_freshness_age_seconds"],
        ),
        freshness_score=_payload_decimal("freshness_score", row["freshness_score"]),
        authority_quorum_count=_payload_decimal(
            "authority_quorum_count",
            row["authority_quorum_count"],
        ),
        guard_score=_payload_decimal("guard_score", row["guard_score"]),
        observed_at=_payload_datetime("observed_at", row["observed_at"]),
        status=_payload_status("row.status", row["status"]),
        reason_codes=_payload_reason_codes(
            "row.reason_codes",
            row["reason_codes"],
            _ROW_REASON_CODE_SEQUENCE,
        ),
        paper_only=_payload_flag("row.paper_only", row["paper_only"]),
        report_only=_payload_flag("row.report_only", row["report_only"]),
        readonly=_payload_flag("row.readonly", row["readonly"]),
        validation_config=config,
    )


def _reason_count_from_payload(
    count: Any,
) -> ResearchStrategySourceAuthorityMemoryGuardReasonCodeCount:
    _require_exact_payload_fields(
        "reason count",
        count,
        _REASON_COUNT_PAYLOAD_FIELDS,
    )
    return ResearchStrategySourceAuthorityMemoryGuardReasonCodeCount(
        reason_code=_payload_reason_code(
            "reason_code",
            count["reason_code"],
            _REPORT_REASON_CODE_SEQUENCE,
        ),
        count=_payload_decimal("count", count["count"]),
        row_ratio=_payload_decimal("row_ratio", count["row_ratio"]),
        paper_only=_payload_flag(
            "reason_code_count.paper_only",
            count["paper_only"],
        ),
        report_only=_payload_flag(
            "reason_code_count.report_only",
            count["report_only"],
        ),
        readonly=_payload_flag("reason_code_count.readonly", count["readonly"]),
    )


def _require_exact_payload_fields(
    label: str,
    value: Any,
    expected_fields: tuple[str, ...],
) -> None:
    if not isinstance(value, Mapping):
        raise ValueError(f"unexpected {label} payload field")
    actual_fields = tuple(value)
    if frozenset(actual_fields) != frozenset(expected_fields):
        raise ValueError(f"unexpected {label} payload field")
    if actual_fields != expected_fields:
        raise ValueError(f"{label} payload must use canonical field order")


def _require_payload_list(field_name: str, value: object) -> list[Any]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return value


def _payload_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a decimal string")
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a decimal string") from exc
    decimal_value = _require_decimal(field_name, decimal_value)
    if decimal_value.as_tuple().exponent != -6 or format(decimal_value, "f") != value:
        raise ValueError(f"{field_name} must use a canonical Decimal string")
    return decimal_value


def _payload_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            f"{field_name} must be a canonical UTC datetime string",
        ) from exc
    normalized = _as_utc(field_name, parsed)
    if value != normalized.isoformat():
        raise ValueError(f"{field_name} must use canonical UTC datetime")
    return normalized


def _payload_public_identifier(field_name: str, value: object) -> str:
    return _require_public_identifier(field_name, value)


def _payload_item_digest(field_name: str, value: object) -> str:
    return _require_item_digest(field_name, value)


def _payload_status(field_name: str, value: object) -> str:
    return _require_status(field_name, value)


def _payload_reason_code(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> str:
    return _require_reason_code(field_name, value, allowed)


def _payload_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    items = _require_payload_list(field_name, value)
    return tuple(_payload_reason_code(field_name, item, allowed) for item in items)


def _payload_flag(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _payload_digest_value(value: object) -> str:
    _require_payload_digest(value)
    return value


def _require_payload_digest(value: object) -> None:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError("derived_validation_digest must be a sha256 hex digest")
def _reject_unsafe_public_payload(value: Any, *, label: str) -> None:
    for path, item in _walk_public_payload(value):
        key = path.rsplit(".", 1)[-1].casefold()
        if any(fragment in key for fragment in _UNSAFE_PUBLIC_KEY_FRAGMENTS):
            raise ValueError(f"{label} includes unsafe public key")
        if isinstance(item, str):
            rendered = item.casefold()
            if any(fragment in rendered for fragment in _UNSAFE_PUBLIC_VALUE_FRAGMENTS):
                raise ValueError(f"{label} includes unsafe public value")


def _walk_public_payload(value: Any, path: str = "payload") -> tuple[tuple[str, Any], ...]:
    if isinstance(value, Mapping):
        nested: list[tuple[str, Any]] = []
        for key, item in value.items():
            child_path = f"{path}.{key}"
            nested.append((child_path, item))
            nested.extend(_walk_public_payload(item, child_path))
        return tuple(nested)
    if isinstance(value, list):
        nested = []
        for index, item in enumerate(value):
            child_path = f"{path}[{index}]"
            nested.append((child_path, item))
            nested.extend(_walk_public_payload(item, child_path))
        return tuple(nested)
    return ((path, value),)


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_SOURCE_AUTHORITY_MEMORY_GUARD_CONFIG_VERSION",
    "RESEARCH_STRATEGY_SOURCE_AUTHORITY_MEMORY_GUARD_STATUSES",
    "ResearchStrategySourceAuthorityMemoryGuardConfig",
    "ResearchStrategySourceAuthorityMemoryGuardInput",
    "ResearchStrategySourceAuthorityMemoryGuardReasonCodeCount",
    "ResearchStrategySourceAuthorityMemoryGuardReport",
    "ResearchStrategySourceAuthorityMemoryGuardRow",
    "build_research_strategy_source_authority_memory_guard_report",
    "research_strategy_source_authority_memory_guard_report_digest",
    "research_strategy_source_authority_memory_guard_report_payload",
    "validate_research_strategy_source_authority_memory_guard_public_payload",
    "validate_research_strategy_source_authority_memory_guard_report_digest",
)
