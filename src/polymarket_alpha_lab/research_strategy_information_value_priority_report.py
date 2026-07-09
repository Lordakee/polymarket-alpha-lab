"""Report-only manual research information-value priority reducer.

The reducer ranks manual research items by expected information value. It is
pure, readonly, deterministic, and exposes only redacted public report payloads.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import InitVar, asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_STRATEGY_INFORMATION_VALUE_PRIORITY_REPORT_CONFIG_VERSION = (
    "research-strategy-information-value-priority-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

REASON_EMPTY_INPUT = "empty_input"
REASON_PRIORITY_SCORE_PASS = "priority_score_pass"
REASON_PRIORITY_SCORE_WATCH = "priority_score_watch"
REASON_PRIORITY_SCORE_BLOCK = "priority_score_block"
REASON_HIGH_UNCERTAINTY_REDUCTION = "high_uncertainty_reduction"
REASON_STALE_INFORMATION_GAP = "stale_information_gap"
REASON_EVIDENCE_QUALITY_GAP = "evidence_quality_gap"
REASON_LIQUIDITY_RELIABILITY_SUPPORT = "liquidity_reliability_support"
REASON_COST_DRAG_CONSTRAINT = "cost_drag_constraint"
REASON_RESOLUTION_CLARITY_GAP = "resolution_clarity_gap"

_ROW_REASON_CODE_SEQUENCE = (
    REASON_PRIORITY_SCORE_PASS,
    REASON_PRIORITY_SCORE_WATCH,
    REASON_PRIORITY_SCORE_BLOCK,
    REASON_HIGH_UNCERTAINTY_REDUCTION,
    REASON_STALE_INFORMATION_GAP,
    REASON_EVIDENCE_QUALITY_GAP,
    REASON_LIQUIDITY_RELIABILITY_SUPPORT,
    REASON_COST_DRAG_CONSTRAINT,
    REASON_RESOLUTION_CLARITY_GAP,
)
_REPORT_REASON_CODE_SEQUENCE = (
    REASON_EMPTY_INPUT,
    REASON_PRIORITY_SCORE_PASS,
    REASON_PRIORITY_SCORE_WATCH,
    REASON_PRIORITY_SCORE_BLOCK,
    REASON_HIGH_UNCERTAINTY_REDUCTION,
    REASON_STALE_INFORMATION_GAP,
    REASON_EVIDENCE_QUALITY_GAP,
    REASON_LIQUIDITY_RELIABILITY_SUPPORT,
    REASON_COST_DRAG_CONSTRAINT,
    REASON_RESOLUTION_CLARITY_GAP,
)
_STATUS_VALUES = frozenset((STATUS_PASS, STATUS_WATCH, STATUS_BLOCK))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_DIGEST_FIELD = "derived_validation_digest"
_REPORT_PAYLOAD_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "status",
        "row_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_expected_information_value_score",
        "highest_expected_information_value_score",
        "average_uncertainty_reduction_score",
        "average_freshness_gap_score",
        "average_evidence_quality_gap_score",
        "average_liquidity_reliability_score",
        "average_cost_drag_score",
        "average_resolution_clarity_gap_score",
        "rows",
        "reason_code_counts",
        "reason_codes",
        _DIGEST_FIELD,
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_ROW_PAYLOAD_FIELDS = frozenset(
    (
        "research_item_digest",
        "uncertainty_reduction_score",
        "freshness_gap_score",
        "evidence_quality_gap_score",
        "liquidity_reliability_score",
        "cost_drag_score",
        "cost_efficiency_score",
        "resolution_clarity_gap_score",
        "expected_information_value_score",
        "observed_at",
        "status",
        "reason_codes",
        _DIGEST_FIELD,
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_REASON_COUNT_PAYLOAD_FIELDS = frozenset(
    ("reason_code", "count", "row_ratio", "paper_only", "report_only", "readonly"),
)
_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PRIVATE_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "market",
    "slug",
    "question",
    "url",
    "source_url",
    "source-url",
    "source url",
    "source_text",
    "source-text",
    "source text",
    "dsn",
    "database",
    "table",
    "token",
    "wallet",
    "auth",
    "credential",
    "secret",
    "private key",
    "order",
    "trade",
    "position",
    "sizing",
    "buy",
    "sell",
    "recommend",
    "live",
    "http://",
    "https://",
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
class ResearchStrategyInformationValuePriorityConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_INFORMATION_VALUE_PRIORITY_REPORT_CONFIG_VERSION
    )
    priority_score_block_threshold: Decimal = Decimal("0.650000")
    priority_score_watch_threshold: Decimal = Decimal("0.450000")
    high_uncertainty_reduction_threshold: Decimal = Decimal("0.700000")
    stale_information_gap_threshold: Decimal = Decimal("0.700000")
    evidence_quality_gap_threshold: Decimal = Decimal("0.650000")
    liquidity_reliability_support_threshold: Decimal = Decimal("0.750000")
    cost_drag_constraint_threshold: Decimal = Decimal("0.600000")
    resolution_clarity_gap_threshold: Decimal = Decimal("0.650000")
    uncertainty_reduction_weight: Decimal = Decimal("0.300000")
    freshness_gap_weight: Decimal = Decimal("0.150000")
    evidence_quality_gap_weight: Decimal = Decimal("0.200000")
    liquidity_reliability_weight: Decimal = Decimal("0.150000")
    cost_efficiency_weight: Decimal = Decimal("0.100000")
    resolution_clarity_gap_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyInformationValuePriorityConfig,
            "config",
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_INFORMATION_VALUE_PRIORITY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "priority_score_block_threshold",
            "priority_score_watch_threshold",
            "high_uncertainty_reduction_threshold",
            "stale_information_gap_threshold",
            "evidence_quality_gap_threshold",
            "liquidity_reliability_support_threshold",
            "cost_drag_constraint_threshold",
            "resolution_clarity_gap_threshold",
            "uncertainty_reduction_weight",
            "freshness_gap_weight",
            "evidence_quality_gap_weight",
            "liquidity_reliability_weight",
            "cost_efficiency_weight",
            "resolution_clarity_gap_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.priority_score_block_threshold < self.priority_score_watch_threshold:
            raise ValueError(
                "priority_score_block_threshold must be at least "
                "priority_score_watch_threshold",
            )
        weight_sum = _quantize(
            self.uncertainty_reduction_weight
            + self.freshness_gap_weight
            + self.evidence_quality_gap_weight
            + self.liquidity_reliability_weight
            + self.cost_efficiency_weight
            + self.resolution_clarity_gap_weight,
        )
        if weight_sum != _ONE:
            raise ValueError("priority weights must sum to one")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyInformationValuePriorityInput(_FinalPublicDataclass):
    research_item_ref: str
    uncertainty_reduction_score: Decimal
    freshness_score: Decimal
    evidence_quality_score: Decimal
    liquidity_reliability_score: Decimal
    cost_drag_score: Decimal
    resolution_clarity_score: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyInformationValuePriorityInput, "input")
        object.__setattr__(
            self,
            "research_item_ref",
            _require_private_ref("research_item_ref", self.research_item_ref),
        )
        for field_name in (
            "uncertainty_reduction_score",
            "freshness_score",
            "evidence_quality_score",
            "liquidity_reliability_score",
            "cost_drag_score",
            "resolution_clarity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyInformationValuePriorityRow(_FinalPublicDataclass):
    research_item_digest: str
    uncertainty_reduction_score: Decimal
    freshness_gap_score: Decimal
    evidence_quality_gap_score: Decimal
    liquidity_reliability_score: Decimal
    cost_drag_score: Decimal
    cost_efficiency_score: Decimal
    resolution_clarity_gap_score: Decimal
    expected_information_value_score: Decimal
    observed_at: datetime
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[
        ResearchStrategyInformationValuePriorityConfig | None
    ] = None

    def __post_init__(
        self,
        validation_config: ResearchStrategyInformationValuePriorityConfig | None,
    ) -> None:
        _require_exact_type(self, ResearchStrategyInformationValuePriorityRow, "row")
        object.__setattr__(
            self,
            "research_item_digest",
            _require_private_digest("research_item_digest", self.research_item_digest),
        )
        for field_name in (
            "uncertainty_reduction_score",
            "freshness_gap_score",
            "evidence_quality_gap_score",
            "liquidity_reliability_score",
            "cost_drag_score",
            "cost_efficiency_score",
            "resolution_clarity_gap_score",
            "expected_information_value_score",
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
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                _ROW_REASON_CODE_SEQUENCE,
            ),
        )
        _validate_row(self, validation_config)
        _require_hard_flags("row", self)
        expected_digest = _digest_from_dataclass(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, _DIGEST_FIELD, expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest mismatch")
        _require_digest(_DIGEST_FIELD, self.derived_validation_digest)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchStrategyInformationValuePriorityReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyInformationValuePriorityReasonCodeCount,
            "reason count",
        )
        _require_reason_code("reason_code", self.reason_code, _REPORT_REASON_CODE_SEQUENCE)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason count", self)
        _reject_unsafe_public_payload("reason count", self)


@dataclass(frozen=True)
class ResearchStrategyInformationValuePriorityReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_expected_information_value_score: Decimal
    highest_expected_information_value_score: Decimal
    average_uncertainty_reduction_score: Decimal
    average_freshness_gap_score: Decimal
    average_evidence_quality_gap_score: Decimal
    average_liquidity_reliability_score: Decimal
    average_cost_drag_score: Decimal
    average_resolution_clarity_gap_score: Decimal
    rows: tuple[ResearchStrategyInformationValuePriorityRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyInformationValuePriorityReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyInformationValuePriorityReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_INFORMATION_VALUE_PRIORITY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in ("row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_expected_information_value_score",
            "highest_expected_information_value_score",
            "average_uncertainty_reduction_score",
            "average_freshness_gap_score",
            "average_evidence_quality_gap_score",
            "average_liquidity_reliability_score",
            "average_cost_drag_score",
            "average_resolution_clarity_gap_score",
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
            _normalize_report_reason_codes(
                "reason_codes",
                self.reason_codes,
            ),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        expected_digest = _digest_from_dataclass(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, _DIGEST_FIELD, expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest mismatch")
        _require_digest(_DIGEST_FIELD, self.derived_validation_digest)
        _reject_unsafe_public_payload("report", self)

    @property
    def payload(self) -> dict[str, object]:
        return research_strategy_information_value_priority_report_payload(self)


def build_research_strategy_information_value_priority_report(
    inputs: Sequence[ResearchStrategyInformationValuePriorityInput],
    *,
    generated_at: datetime,
    config: ResearchStrategyInformationValuePriorityConfig | None = None,
) -> ResearchStrategyInformationValuePriorityReport:
    """Build a deterministic, readonly manual research priority report."""

    cfg = config or ResearchStrategyInformationValuePriorityConfig()
    if type(cfg) is not ResearchStrategyInformationValuePriorityConfig:
        raise ValueError(
            "config must be a ResearchStrategyInformationValuePriorityConfig",
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
            ResearchStrategyInformationValuePriorityReasonCodeCount(
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
        "average_expected_information_value_score": _average_ratio(
            tuple(row.expected_information_value_score for row in rows),
        ),
        "highest_expected_information_value_score": max(
            (row.expected_information_value_score for row in rows),
            default=_ZERO,
        ),
        "average_uncertainty_reduction_score": _average_ratio(
            tuple(row.uncertainty_reduction_score for row in rows),
        ),
        "average_freshness_gap_score": _average_ratio(
            tuple(row.freshness_gap_score for row in rows),
        ),
        "average_evidence_quality_gap_score": _average_ratio(
            tuple(row.evidence_quality_gap_score for row in rows),
        ),
        "average_liquidity_reliability_score": _average_ratio(
            tuple(row.liquidity_reliability_score for row in rows),
        ),
        "average_cost_drag_score": _average_ratio(
            tuple(row.cost_drag_score for row in rows),
        ),
        "average_resolution_clarity_gap_score": _average_ratio(
            tuple(row.resolution_clarity_gap_score for row in rows),
        ),
        "rows": rows,
        "reason_code_counts": reason_code_counts,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyInformationValuePriorityReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_strategy_information_value_priority_report_payload(
    value: ResearchStrategyInformationValuePriorityReport | dict[str, object],
) -> dict[str, object]:
    if type(value) is ResearchStrategyInformationValuePriorityReport:
        _require_hard_flags("report", value)
        payload = _report_payload(value)
    elif type(value) is dict:
        payload = _copy_json_object(value)
    else:
        raise ValueError(
            "value must be a ResearchStrategyInformationValuePriorityReport or dict",
        )
    _validate_payload_statuses(payload)
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_public_payload_schema(payload)
    _validate_payload_digest(payload)
    return payload


def _row_for_input(
    row: ResearchStrategyInformationValuePriorityInput,
    config: ResearchStrategyInformationValuePriorityConfig,
) -> ResearchStrategyInformationValuePriorityRow:
    freshness_gap = _inverse_ratio(row.freshness_score)
    evidence_quality_gap = _inverse_ratio(row.evidence_quality_score)
    cost_efficiency = _inverse_ratio(row.cost_drag_score)
    resolution_clarity_gap = _inverse_ratio(row.resolution_clarity_score)
    priority_score = _priority_score(
        uncertainty_reduction_score=row.uncertainty_reduction_score,
        freshness_gap_score=freshness_gap,
        evidence_quality_gap_score=evidence_quality_gap,
        liquidity_reliability_score=row.liquidity_reliability_score,
        cost_efficiency_score=cost_efficiency,
        resolution_clarity_gap_score=resolution_clarity_gap,
        config=config,
    )
    reason_codes = _row_reason_codes(
        uncertainty_reduction_score=row.uncertainty_reduction_score,
        freshness_gap_score=freshness_gap,
        evidence_quality_gap_score=evidence_quality_gap,
        liquidity_reliability_score=row.liquidity_reliability_score,
        cost_drag_score=row.cost_drag_score,
        resolution_clarity_gap_score=resolution_clarity_gap,
        expected_information_value_score=priority_score,
        config=config,
    )
    return ResearchStrategyInformationValuePriorityRow(
        research_item_digest=_private_ref_digest(row.research_item_ref),
        uncertainty_reduction_score=row.uncertainty_reduction_score,
        freshness_gap_score=freshness_gap,
        evidence_quality_gap_score=evidence_quality_gap,
        liquidity_reliability_score=row.liquidity_reliability_score,
        cost_drag_score=row.cost_drag_score,
        cost_efficiency_score=cost_efficiency,
        resolution_clarity_gap_score=resolution_clarity_gap,
        expected_information_value_score=priority_score,
        observed_at=row.observed_at,
        status=_row_status(priority_score, config),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _priority_score(
    *,
    uncertainty_reduction_score: Decimal,
    freshness_gap_score: Decimal,
    evidence_quality_gap_score: Decimal,
    liquidity_reliability_score: Decimal,
    cost_efficiency_score: Decimal,
    resolution_clarity_gap_score: Decimal,
    config: ResearchStrategyInformationValuePriorityConfig,
) -> Decimal:
    return _quantize(
        uncertainty_reduction_score * config.uncertainty_reduction_weight
        + freshness_gap_score * config.freshness_gap_weight
        + evidence_quality_gap_score * config.evidence_quality_gap_weight
        + liquidity_reliability_score * config.liquidity_reliability_weight
        + cost_efficiency_score * config.cost_efficiency_weight
        + resolution_clarity_gap_score * config.resolution_clarity_gap_weight,
    )


def _row_status(
    priority_score: Decimal,
    config: ResearchStrategyInformationValuePriorityConfig,
) -> str:
    if priority_score >= config.priority_score_block_threshold:
        return STATUS_BLOCK
    if priority_score >= config.priority_score_watch_threshold:
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    *,
    uncertainty_reduction_score: Decimal,
    freshness_gap_score: Decimal,
    evidence_quality_gap_score: Decimal,
    liquidity_reliability_score: Decimal,
    cost_drag_score: Decimal,
    resolution_clarity_gap_score: Decimal,
    expected_information_value_score: Decimal,
    config: ResearchStrategyInformationValuePriorityConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    status = _row_status(expected_information_value_score, config)
    if status == STATUS_BLOCK:
        codes.append(REASON_PRIORITY_SCORE_BLOCK)
    elif status == STATUS_WATCH:
        codes.append(REASON_PRIORITY_SCORE_WATCH)
    else:
        codes.append(REASON_PRIORITY_SCORE_PASS)
    if uncertainty_reduction_score >= config.high_uncertainty_reduction_threshold:
        codes.append(REASON_HIGH_UNCERTAINTY_REDUCTION)
    if freshness_gap_score >= config.stale_information_gap_threshold:
        codes.append(REASON_STALE_INFORMATION_GAP)
    if evidence_quality_gap_score >= config.evidence_quality_gap_threshold:
        codes.append(REASON_EVIDENCE_QUALITY_GAP)
    if liquidity_reliability_score >= config.liquidity_reliability_support_threshold:
        codes.append(REASON_LIQUIDITY_RELIABILITY_SUPPORT)
    if cost_drag_score >= config.cost_drag_constraint_threshold:
        codes.append(REASON_COST_DRAG_CONSTRAINT)
    if resolution_clarity_gap_score >= config.resolution_clarity_gap_threshold:
        codes.append(REASON_RESOLUTION_CLARITY_GAP)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(codes),
        _ROW_REASON_CODE_SEQUENCE,
    )


def _report_status(rows: tuple[ResearchStrategyInformationValuePriorityRow, ...]) -> str:
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _row_sort_key(
    row: ResearchStrategyInformationValuePriorityRow,
) -> tuple[int, Decimal, str]:
    return (
        {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[row.status],
        -row.expected_information_value_score,
        row.research_item_digest,
    )


def _normalize_inputs(
    inputs: Sequence[ResearchStrategyInformationValuePriorityInput],
) -> tuple[ResearchStrategyInformationValuePriorityInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be a sequence")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be a sequence") from exc
    seen_refs: set[str] = set()
    for value in normalized:
        if type(value) is not ResearchStrategyInformationValuePriorityInput:
            raise ValueError(
                "inputs must contain only ResearchStrategyInformationValuePriorityInput values",
            )
        _require_hard_flags("input", value)
        if value.research_item_ref in seen_refs:
            raise ValueError("inputs must not contain duplicate research_item_ref values")
        seen_refs.add(value.research_item_ref)
    return normalized


def _normalize_rows(
    rows: Sequence[ResearchStrategyInformationValuePriorityRow],
) -> tuple[ResearchStrategyInformationValuePriorityRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be a sequence")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be a sequence") from exc
    seen_digests: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyInformationValuePriorityRow:
            raise ValueError(
                "rows must contain ResearchStrategyInformationValuePriorityRow values",
            )
        _require_hard_flags("row", row)
        if row.research_item_digest in seen_digests:
            raise ValueError("rows must not contain duplicate research_item_digest values")
        seen_digests.add(row.research_item_digest)
    return normalized


def _normalize_reason_code_counts(
    counts: Sequence[ResearchStrategyInformationValuePriorityReasonCodeCount],
) -> tuple[ResearchStrategyInformationValuePriorityReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)):
        raise ValueError("reason_code_counts must be a sequence")
    try:
        normalized = tuple(counts)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be a sequence") from exc
    seen_codes: set[str] = set()
    for count in normalized:
        if type(count) is not ResearchStrategyInformationValuePriorityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyInformationValuePriorityReasonCodeCount values",
            )
        _require_hard_flags("reason count", count)
        if count.reason_code in seen_codes:
            raise ValueError("reason_code_counts must not contain duplicate codes")
        seen_codes.add(count.reason_code)
    if tuple(sorted(normalized, key=lambda item: item.reason_code)) != normalized:
        raise ValueError("reason_code_counts must use deterministic sequence")
    return normalized


def _validate_row(
    row: ResearchStrategyInformationValuePriorityRow,
    config: ResearchStrategyInformationValuePriorityConfig | None,
) -> None:
    if row.cost_efficiency_score != _inverse_ratio(row.cost_drag_score):
        raise ValueError("cost_efficiency_score must match cost_drag_score")
    if config is None:
        return
    expected_score = _priority_score(
        uncertainty_reduction_score=row.uncertainty_reduction_score,
        freshness_gap_score=row.freshness_gap_score,
        evidence_quality_gap_score=row.evidence_quality_gap_score,
        liquidity_reliability_score=row.liquidity_reliability_score,
        cost_efficiency_score=row.cost_efficiency_score,
        resolution_clarity_gap_score=row.resolution_clarity_gap_score,
        config=config,
    )
    if row.expected_information_value_score != expected_score:
        raise ValueError("expected_information_value_score does not match inputs")
    if row.status != _row_status(row.expected_information_value_score, config):
        raise ValueError("status does not match expected_information_value_score")
    expected_codes = _row_reason_codes(
        uncertainty_reduction_score=row.uncertainty_reduction_score,
        freshness_gap_score=row.freshness_gap_score,
        evidence_quality_gap_score=row.evidence_quality_gap_score,
        liquidity_reliability_score=row.liquidity_reliability_score,
        cost_drag_score=row.cost_drag_score,
        resolution_clarity_gap_score=row.resolution_clarity_gap_score,
        expected_information_value_score=row.expected_information_value_score,
        config=config,
    )
    if row.reason_codes != expected_codes:
        raise ValueError("reason_codes do not match inputs")


def _validate_report(report: ResearchStrategyInformationValuePriorityReport) -> None:
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, STATUS_PASS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, STATUS_WATCH)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, STATUS_BLOCK)):
        raise ValueError("block_count must match rows")
    if report.row_count != report.pass_count + report.watch_count + report.block_count:
        raise ValueError("status counts must match row_count")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    expected_reason_counts = _reason_code_counts(report.rows)
    if not report.rows:
        expected_reason_counts = (
            ResearchStrategyInformationValuePriorityReasonCodeCount(
                reason_code=REASON_EMPTY_INPUT,
                count=_ONE,
                row_ratio=_ONE,
            ),
        )
    if report.reason_code_counts != expected_reason_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")
    if tuple(sorted(report.rows, key=_row_sort_key)) != report.rows:
        raise ValueError("rows must use deterministic sequence")
    if report.average_expected_information_value_score != _average_ratio(
        tuple(row.expected_information_value_score for row in report.rows),
    ):
        raise ValueError("average_expected_information_value_score must match rows")
    if report.highest_expected_information_value_score != max(
        (row.expected_information_value_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("highest_expected_information_value_score must match rows")
    if report.average_uncertainty_reduction_score != _average_ratio(
        tuple(row.uncertainty_reduction_score for row in report.rows),
    ):
        raise ValueError("average_uncertainty_reduction_score must match rows")
    if report.average_freshness_gap_score != _average_ratio(
        tuple(row.freshness_gap_score for row in report.rows),
    ):
        raise ValueError("average_freshness_gap_score must match rows")
    if report.average_evidence_quality_gap_score != _average_ratio(
        tuple(row.evidence_quality_gap_score for row in report.rows),
    ):
        raise ValueError("average_evidence_quality_gap_score must match rows")
    if report.average_liquidity_reliability_score != _average_ratio(
        tuple(row.liquidity_reliability_score for row in report.rows),
    ):
        raise ValueError("average_liquidity_reliability_score must match rows")
    if report.average_cost_drag_score != _average_ratio(
        tuple(row.cost_drag_score for row in report.rows),
    ):
        raise ValueError("average_cost_drag_score must match rows")
    if report.average_resolution_clarity_gap_score != _average_ratio(
        tuple(row.resolution_clarity_gap_score for row in report.rows),
    ):
        raise ValueError("average_resolution_clarity_gap_score must match rows")


def _reason_code_counts(
    rows: tuple[ResearchStrategyInformationValuePriorityRow, ...],
) -> tuple[ResearchStrategyInformationValuePriorityReasonCodeCount, ...]:
    if not rows:
        return ()
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    denominator = _decimal_count(len(rows))
    return tuple(
        ResearchStrategyInformationValuePriorityReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counter[reason_code]),
            row_ratio=_safe_divide(_decimal_count(counter[reason_code]), denominator),
        )
        for reason_code in sorted(counter)
    )


def _status_count(
    rows: tuple[ResearchStrategyInformationValuePriorityRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _safe_divide(sum(values, _ZERO), _decimal_count(len(values)))


def _safe_divide(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    return _quantize(numerator / denominator)


def _inverse_ratio(value: Decimal) -> Decimal:
    return _quantize(_ONE - value)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count value must be a nonnegative int")
    return Decimal(value).quantize(_QUANT)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _as_utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    normalized = _quantize(value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{name} must be between zero and one")
    return normalized


def _require_nonnegative_count_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    normalized = _quantize(value)
    if normalized < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if normalized != normalized.to_integral_value().quantize(_QUANT):
        raise ValueError(f"{name} must be a whole-count Decimal")
    return normalized


def _require_public_identifier(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a str")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{name} must be a public identifier")
    if _has_unsafe_fragment(value):
        raise ValueError(f"{name} contains unsafe public text")
    return value


def _require_private_ref(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a str")
    if value.strip() == "":
        raise ValueError(f"{name} must not be blank")
    return value


def _require_private_digest(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a private digest")
    if not _PRIVATE_DIGEST_RE.fullmatch(value):
        raise ValueError(f"{name} must be a private digest")
    return value


def _require_digest(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a digest")
    if not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{name} must be a digest")
    return value


def _require_status(name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUS_VALUES:
        raise ValueError(f"{name} must be pass, watch, or block")
    return value


def _require_reason_code(name: str, value: object, allowed: tuple[str, ...]) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{name} must be an allowed reason code")
    return value


def _normalize_reason_codes(
    name: str,
    values: Sequence[str],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be a sequence")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{name} must be a sequence") from exc
    for value in normalized:
        _require_reason_code(name, value, allowed)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{name} must not contain duplicates")
    order = {code: index for index, code in enumerate(allowed)}
    return tuple(sorted(normalized, key=order.__getitem__))


def _normalize_report_reason_codes(
    name: str,
    values: Sequence[str],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be a sequence")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{name} must be a sequence") from exc
    for value in normalized:
        _require_reason_code(name, value, _REPORT_REASON_CODE_SEQUENCE)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{name} must not contain duplicates")
    if tuple(sorted(normalized)) != normalized:
        raise ValueError(f"{name} must use deterministic sequence")
    return normalized


def _require_hard_flags(name: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{name} {field_name} must be True")


def _private_ref_digest(value: str) -> str:
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()


def _digest_from_dataclass(value: object) -> str:
    ready = _json_ready(value, omit_digest=True)
    encoded = json.dumps(
        ready,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    ready = _json_ready(dict(values), omit_digest=True)
    encoded = json.dumps(
        ready,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _report_payload(
    report: ResearchStrategyInformationValuePriorityReport,
) -> dict[str, object]:
    payload = _json_ready(report, omit_digest=False)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _json_ready(value: object, *, omit_digest: bool) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value), omit_digest=omit_digest)
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(_quantize(value))
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, int):
        raise ValueError("JSON numeric value must be Decimal-derived")
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if omit_digest and key == _DIGEST_FIELD:
                continue
            ready[key] = _json_ready(item, omit_digest=omit_digest)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item, omit_digest=omit_digest) for item in value]
    if isinstance(value, list):
        return [_json_ready(item, omit_digest=omit_digest) for item in value]
    raise ValueError("value is not JSON serializable")


def _copy_json_object(value: Mapping[str, object]) -> dict[str, object]:
    copied = _json_ready(value, omit_digest=False)
    if type(copied) is not dict:
        raise ValueError("payload must be a JSON object")
    return copied


def _validate_payload_statuses(payload: dict[str, object]) -> None:
    _require_status("payload.status", payload.get("status"))
    rows = payload.get("rows")
    if rows is None:
        raise ValueError("payload.rows is required")
    if type(rows) is not list:
        raise ValueError("payload.rows must be a list")
    for index, row in enumerate(rows):
        if type(row) is not dict:
            raise ValueError("payload.rows must contain JSON objects")
        _require_status(f"payload.rows[{index}].status", row.get("status"))


def _validate_public_payload_schema(payload: dict[str, object]) -> None:
    _require_payload_keys("payload", payload, _REPORT_PAYLOAD_FIELDS)
    _require_payload_hard_flags("payload", payload)
    _require_public_identifier("payload.config_version", payload.get("config_version"))
    _require_digest(f"payload.{_DIGEST_FIELD}", payload.get(_DIGEST_FIELD))
    _require_decimal_payload_count("payload.row_count", payload.get("row_count"))
    _require_decimal_payload_count("payload.pass_count", payload.get("pass_count"))
    _require_decimal_payload_count("payload.watch_count", payload.get("watch_count"))
    _require_decimal_payload_count("payload.block_count", payload.get("block_count"))
    for field_name in (
        "average_expected_information_value_score",
        "highest_expected_information_value_score",
        "average_uncertainty_reduction_score",
        "average_freshness_gap_score",
        "average_evidence_quality_gap_score",
        "average_liquidity_reliability_score",
        "average_cost_drag_score",
        "average_resolution_clarity_gap_score",
    ):
        _require_decimal_payload_ratio(f"payload.{field_name}", payload.get(field_name))
    reason_codes = payload.get("reason_codes")
    if type(reason_codes) is not list:
        raise ValueError("payload.reason_codes must be a list")
    normalized_reason_codes = _normalize_report_reason_codes(
        "payload.reason_codes",
        tuple(reason_codes),
    )
    if list(normalized_reason_codes) != reason_codes:
        raise ValueError("payload.reason_codes must use deterministic sequence")
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("payload.rows must be a list")
    for index, row in enumerate(rows):
        if type(row) is not dict:
            raise ValueError("payload.rows must contain JSON objects")
        _validate_public_payload_row(f"payload.rows[{index}]", row)
    reason_code_counts = payload.get("reason_code_counts")
    if type(reason_code_counts) is not list:
        raise ValueError("payload.reason_code_counts must be a list")
    for index, reason_count in enumerate(reason_code_counts):
        if type(reason_count) is not dict:
            raise ValueError("payload.reason_code_counts must contain JSON objects")
        _validate_public_payload_reason_count(
            f"payload.reason_code_counts[{index}]",
            reason_count,
        )


def _validate_public_payload_row(label: str, row: dict[str, object]) -> None:
    _require_payload_keys(label, row, _ROW_PAYLOAD_FIELDS)
    _require_payload_hard_flags(label, row)
    _require_private_digest(f"{label}.research_item_digest", row.get("research_item_digest"))
    _require_digest(f"{label}.{_DIGEST_FIELD}", row.get(_DIGEST_FIELD))
    _require_status(f"{label}.status", row.get("status"))
    for field_name in (
        "uncertainty_reduction_score",
        "freshness_gap_score",
        "evidence_quality_gap_score",
        "liquidity_reliability_score",
        "cost_drag_score",
        "cost_efficiency_score",
        "resolution_clarity_gap_score",
        "expected_information_value_score",
    ):
        _require_decimal_payload_ratio(f"{label}.{field_name}", row.get(field_name))
    if type(row.get("observed_at")) is not str:
        raise ValueError(f"{label}.observed_at must be a string")
    reason_codes = row.get("reason_codes")
    if type(reason_codes) is not list:
        raise ValueError(f"{label}.reason_codes must be a list")
    normalized_reason_codes = _normalize_reason_codes(
        f"{label}.reason_codes",
        tuple(reason_codes),
        _ROW_REASON_CODE_SEQUENCE,
    )
    if list(normalized_reason_codes) != reason_codes:
        raise ValueError(f"{label}.reason_codes must use deterministic sequence")


def _validate_public_payload_reason_count(
    label: str,
    reason_count: dict[str, object],
) -> None:
    _require_payload_keys(label, reason_count, _REASON_COUNT_PAYLOAD_FIELDS)
    _require_payload_hard_flags(label, reason_count)
    _require_reason_code(
        f"{label}.reason_code",
        reason_count.get("reason_code"),
        _REPORT_REASON_CODE_SEQUENCE,
    )
    _require_decimal_payload_count(f"{label}.count", reason_count.get("count"))
    _require_decimal_payload_ratio(f"{label}.row_ratio", reason_count.get("row_ratio"))


def _require_payload_keys(
    label: str,
    payload: dict[str, object],
    expected_fields: frozenset[str],
) -> None:
    field_names = frozenset(payload)
    if not field_names.issubset(expected_fields):
        raise ValueError(f"{label} contains unsupported public payload field")
    if field_names != expected_fields:
        raise ValueError(f"{label} is missing required public payload field")


def _require_payload_hard_flags(label: str, payload: dict[str, object]) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if payload.get(field_name) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _require_decimal_payload_ratio(name: str, value: object) -> Decimal:
    return _require_ratio_decimal(name, _require_decimal_payload_string(name, value))


def _require_decimal_payload_count(name: str, value: object) -> Decimal:
    return _require_nonnegative_count_decimal(
        name,
        _require_decimal_payload_string(name, value),
    )


def _require_decimal_payload_string(name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{name} must be a Decimal string")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{name} must be a Decimal string") from exc
    if str(_quantize(decimal_value)) != value:
        raise ValueError(f"{name} must be a canonical Decimal string")
    return decimal_value


def _validate_payload_digest(payload: dict[str, object]) -> None:
    _validate_one_payload_digest("payload", payload)
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("payload.rows must be a list")
    for index, row in enumerate(rows):
        if type(row) is not dict:
            raise ValueError("payload.rows must contain JSON objects")
        _validate_one_payload_digest(f"payload.rows[{index}]", row)


def _validate_one_payload_digest(label: str, payload: dict[str, object]) -> None:
    provided = payload.get(_DIGEST_FIELD)
    _require_digest(f"{label}.{_DIGEST_FIELD}", provided)
    digest_input = dict(payload)
    digest_input.pop(_DIGEST_FIELD, None)
    encoded = json.dumps(
        _json_ready(digest_input, omit_digest=True),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    expected = sha256(encoded).hexdigest()
    if provided != expected:
        raise ValueError("derived_validation_digest does not match public payload")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(
            label,
            asdict(value),
            allow_json_containers=allow_json_containers,
        )
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_fragment(key):
                raise ValueError(f"unsafe public field in {label}")
            if key in _PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{label}.{key} must be True")
            _reject_unsafe_public_payload(
                f"{label}.{key}",
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, tuple) or (allow_json_containers and isinstance(value, list)):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                f"{label}[{index}]",
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, list):
        raise ValueError(f"{label} must use immutable sequences")
    if type(value) is str:
        if _PRIVATE_DIGEST_RE.fullmatch(value) or _DIGEST_RE.fullmatch(value):
            return
        if _has_unsafe_fragment(value):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, float):
        raise ValueError(f"{label} must not contain floats")


def _has_unsafe_fragment(value: str) -> bool:
    normalized = value.casefold()
    return any(fragment in normalized for fragment in _UNSAFE_PUBLIC_FRAGMENTS)


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_INFORMATION_VALUE_PRIORITY_REPORT_CONFIG_VERSION",
    "ResearchStrategyInformationValuePriorityConfig",
    "ResearchStrategyInformationValuePriorityInput",
    "ResearchStrategyInformationValuePriorityReasonCodeCount",
    "ResearchStrategyInformationValuePriorityReport",
    "ResearchStrategyInformationValuePriorityRow",
    "build_research_strategy_information_value_priority_report",
    "research_strategy_information_value_priority_report_payload",
)
