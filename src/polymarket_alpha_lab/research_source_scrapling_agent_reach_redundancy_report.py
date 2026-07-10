"""Report-only redundancy gate for Scrapling and agent-reach evidence telemetry."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_SOURCE_SCRAPLING_AGENT_REACH_REDUNDANCY_REPORT_CONFIG_VERSION = (
    "research-source-scrapling-agent-reach-redundancy-report-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_UP)

STATUSES = ("pass", "watch", "block")
NO_INPUTS_REASON = "scrapling_agent_reach_redundancy_no_inputs"
PASS_REASON = "scrapling_agent_reach_redundancy_pass"
WATCH_REASON = "scrapling_agent_reach_redundancy_watch"
BLOCK_REASON = "scrapling_agent_reach_redundancy_block"

REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    "redundant_coverage_below_watch_threshold",
    "coverage_gap_above_watch_threshold",
    "conflict_ratio_above_watch_threshold",
    "confidence_gap_above_watch_threshold",
    "tool_agreement_below_watch_threshold",
    "redundant_coverage_below_pass_threshold",
    "coverage_gap_above_pass_threshold",
    "conflict_ratio_above_pass_threshold",
    "confidence_gap_above_pass_threshold",
    "tool_agreement_below_pass_threshold",
    BLOCK_REASON,
    WATCH_REASON,
    PASS_REASON,
)
BLOCK_REASON_CODES = frozenset(
    reason_code
    for reason_code in REASON_CODE_SEQUENCE
    if reason_code.endswith("_watch_threshold")
)

DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
DECIMAL_PAYLOAD_RE = re.compile(r"^(0|[1-9][0-9]*)\.[0-9]{6}$")
PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
UNSAFE_PUBLIC_FRAGMENTS = (
    "raw_candidate",
    "candidate_id",
    "candidate id",
    "market_id",
    "market id",
    "market_slug",
    "market slug",
    "slug",
    "question",
    "source_url",
    "source url",
    "source_text",
    "source text",
    "raw_text",
    "raw text",
    "url",
    "http://",
    "https://",
    "www.",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "live",
    "sizing",
    "recommendation",
)

__all__ = (
    "DEFAULT_RESEARCH_SOURCE_SCRAPLING_AGENT_REACH_REDUNDANCY_REPORT_CONFIG_VERSION",
    "ResearchSourceScraplingAgentReachRedundancyConfig",
    "ResearchSourceScraplingAgentReachRedundancyInput",
    "ResearchSourceScraplingAgentReachRedundancyReasonCodeCount",
    "ResearchSourceScraplingAgentReachRedundancyReport",
    "ResearchSourceScraplingAgentReachRedundancyRow",
    "STATUSES",
    "build_research_source_scrapling_agent_reach_redundancy_report",
    "research_source_scrapling_agent_reach_redundancy_report_digest",
    "research_source_scrapling_agent_reach_redundancy_report_payload",
    "validate_research_source_scrapling_agent_reach_redundancy_report_payload",
)


@dataclass(frozen=True)
class ResearchSourceScraplingAgentReachRedundancyConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_SCRAPLING_AGENT_REACH_REDUNDANCY_REPORT_CONFIG_VERSION
    )
    min_redundant_coverage_pass_ratio: Decimal = Decimal("0.750000")
    min_redundant_coverage_watch_ratio: Decimal = Decimal("0.300000")
    max_coverage_gap_pass_ratio: Decimal = Decimal("0.250000")
    max_coverage_gap_watch_ratio: Decimal = Decimal("0.500000")
    max_conflict_ratio_pass_ratio: Decimal = Decimal("0.100000")
    max_conflict_ratio_watch_ratio: Decimal = Decimal("0.400000")
    max_confidence_gap_pass_ratio: Decimal = Decimal("0.100000")
    max_confidence_gap_watch_ratio: Decimal = Decimal("0.400000")
    min_tool_agreement_pass_score: Decimal = Decimal("0.800000")
    min_tool_agreement_watch_score: Decimal = Decimal("0.500000")
    redundant_coverage_weight: Decimal = Decimal("0.315714")
    coverage_balance_weight: Decimal = Decimal("0.200000")
    conflict_resilience_weight: Decimal = Decimal("0.250000")
    confidence_alignment_weight: Decimal = Decimal("0.234286")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingAgentReachRedundancyConfig:
            raise TypeError(
                "ResearchSourceScraplingAgentReachRedundancyConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceScraplingAgentReachRedundancyConfig,
            "config",
        )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_SCRAPLING_AGENT_REACH_REDUNDANCY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_redundant_coverage_pass_ratio",
            "min_redundant_coverage_watch_ratio",
            "max_coverage_gap_pass_ratio",
            "max_coverage_gap_watch_ratio",
            "max_conflict_ratio_pass_ratio",
            "max_conflict_ratio_watch_ratio",
            "max_confidence_gap_pass_ratio",
            "max_confidence_gap_watch_ratio",
            "min_tool_agreement_pass_score",
            "min_tool_agreement_watch_score",
            "redundant_coverage_weight",
            "coverage_balance_weight",
            "conflict_resilience_weight",
            "confidence_alignment_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_ordered_floor(
            "redundant coverage",
            self.min_redundant_coverage_watch_ratio,
            self.min_redundant_coverage_pass_ratio,
        )
        _require_ordered_ceiling(
            "coverage gap",
            self.max_coverage_gap_pass_ratio,
            self.max_coverage_gap_watch_ratio,
        )
        _require_ordered_ceiling(
            "conflict ratio",
            self.max_conflict_ratio_pass_ratio,
            self.max_conflict_ratio_watch_ratio,
        )
        _require_ordered_ceiling(
            "confidence gap",
            self.max_confidence_gap_pass_ratio,
            self.max_confidence_gap_watch_ratio,
        )
        _require_ordered_floor(
            "tool agreement",
            self.min_tool_agreement_watch_score,
            self.min_tool_agreement_pass_score,
        )
        weight_sum = _sum_decimal(
            (
                self.redundant_coverage_weight,
                self.coverage_balance_weight,
                self.conflict_resilience_weight,
                self.confidence_alignment_weight,
            ),
        )
        if weight_sum != ONE:
            raise ValueError("tool agreement weights must sum to 1")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceScraplingAgentReachRedundancyInput:
    private_collection_ref: str
    observed_at: datetime
    required_evidence_count: Decimal
    scrapling_evidence_count: Decimal
    agent_reach_evidence_count: Decimal
    overlapping_evidence_count: Decimal
    conflicting_evidence_count: Decimal
    scrapling_confidence_score: Decimal
    agent_reach_confidence_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingAgentReachRedundancyInput:
            raise TypeError(
                "ResearchSourceScraplingAgentReachRedundancyInput does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceScraplingAgentReachRedundancyInput, "input")
        _require_private_string("private_collection_ref", self.private_collection_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "required_evidence_count",
            _normalize_positive_count(
                "required_evidence_count",
                self.required_evidence_count,
            ),
        )
        for field_name in (
            "scrapling_evidence_count",
            "agent_reach_evidence_count",
            "overlapping_evidence_count",
            "conflicting_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("scrapling_confidence_score", "agent_reach_confidence_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _validate_input_counts(self)
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchSourceScraplingAgentReachRedundancyRow:
    row_index: Decimal
    observed_at: datetime
    required_evidence_count: Decimal
    scrapling_evidence_count: Decimal
    agent_reach_evidence_count: Decimal
    overlapping_evidence_count: Decimal
    conflicting_evidence_count: Decimal
    scrapling_confidence_score: Decimal
    agent_reach_confidence_score: Decimal
    redundant_coverage_ratio: Decimal
    coverage_gap_ratio: Decimal
    conflict_ratio: Decimal
    confidence_gap_ratio: Decimal
    tool_agreement_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingAgentReachRedundancyRow:
            raise TypeError(
                "ResearchSourceScraplingAgentReachRedundancyRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceScraplingAgentReachRedundancyRow, "row")
        object.__setattr__(self, "row_index", _normalize_positive_count("row_index", self.row_index))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "required_evidence_count",
            _normalize_positive_count(
                "required_evidence_count",
                self.required_evidence_count,
            ),
        )
        for field_name in (
            "scrapling_evidence_count",
            "agent_reach_evidence_count",
            "overlapping_evidence_count",
            "conflicting_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("scrapling_confidence_score", "agent_reach_confidence_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "redundant_coverage_ratio",
            "coverage_gap_ratio",
            "conflict_ratio",
            "confidence_gap_ratio",
            "tool_agreement_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _validate_row_base_consistency(self)
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        if self.status != _status_from_reasons(self.reason_codes):
            raise ValueError("row status must match reason_codes")
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourceScraplingAgentReachRedundancyReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingAgentReachRedundancyReasonCodeCount:
            raise TypeError(
                "ResearchSourceScraplingAgentReachRedundancyReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceScraplingAgentReachRedundancyReasonCodeCount,
            "reason_code_count",
        )
        object.__setattr__(
            self,
            "reason_code",
            _normalize_reason_code("reason_code", self.reason_code),
        )
        object.__setattr__(
            self,
            "count",
            _normalize_positive_count("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchSourceScraplingAgentReachRedundancyReport:
    generated_at: datetime
    config_version: str
    config: ResearchSourceScraplingAgentReachRedundancyConfig
    input_count: Decimal
    row_count: Decimal
    required_evidence_count: Decimal
    scrapling_evidence_count: Decimal
    agent_reach_evidence_count: Decimal
    overlapping_evidence_count: Decimal
    conflicting_evidence_count: Decimal
    aggregate_redundant_coverage_ratio: Decimal
    aggregate_coverage_gap_ratio: Decimal
    aggregate_conflict_ratio: Decimal
    average_confidence_gap_ratio: Decimal
    average_tool_agreement_score: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchSourceScraplingAgentReachRedundancyReasonCodeCount, ...]
    rows: tuple[ResearchSourceScraplingAgentReachRedundancyRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingAgentReachRedundancyReport:
            raise TypeError(
                "ResearchSourceScraplingAgentReachRedundancyReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceScraplingAgentReachRedundancyReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_SCRAPLING_AGENT_REACH_REDUNDANCY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_exact_type(
            self.config,
            ResearchSourceScraplingAgentReachRedundancyConfig,
            "config",
        )
        _require_hard_flags("config", self.config)
        _reject_unsafe_public_payload("config", self.config)
        if self.config_version != self.config.config_version:
            raise ValueError("config_version must match config")
        for field_name in (
            "input_count",
            "row_count",
            "required_evidence_count",
            "scrapling_evidence_count",
            "agent_reach_evidence_count",
            "overlapping_evidence_count",
            "conflicting_evidence_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "aggregate_redundant_coverage_ratio",
            "aggregate_coverage_gap_ratio",
            "aggregate_conflict_ratio",
            "average_confidence_gap_ratio",
            "average_tool_agreement_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")
        _require_digest("derived_validation_digest", self.derived_validation_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return research_source_scrapling_agent_reach_redundancy_report_payload(self)


def build_research_source_scrapling_agent_reach_redundancy_report(
    inputs: Sequence[ResearchSourceScraplingAgentReachRedundancyInput],
    *,
    config: ResearchSourceScraplingAgentReachRedundancyConfig | None = None,
    generated_at: datetime,
) -> ResearchSourceScraplingAgentReachRedundancyReport:
    cfg = (
        ResearchSourceScraplingAgentReachRedundancyConfig()
        if config is None
        else _require_config(config)
    )
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        _row_from_input(
            row_index=_decimal_from_int(index),
            item=item,
            config=cfg,
            generated_at=generated_at_utc,
        )
        for index, item in enumerate(sorted(normalized_inputs, key=_input_sort_key), start=1)
    )
    return ResearchSourceScraplingAgentReachRedundancyReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        config=cfg,
        input_count=_decimal_from_int(len(normalized_inputs)),
        row_count=_decimal_from_int(len(rows)),
        required_evidence_count=_sum_decimal(row.required_evidence_count for row in rows),
        scrapling_evidence_count=_sum_decimal(row.scrapling_evidence_count for row in rows),
        agent_reach_evidence_count=_sum_decimal(row.agent_reach_evidence_count for row in rows),
        overlapping_evidence_count=_sum_decimal(row.overlapping_evidence_count for row in rows),
        conflicting_evidence_count=_sum_decimal(row.conflicting_evidence_count for row in rows),
        aggregate_redundant_coverage_ratio=_aggregate_redundant_coverage_ratio(rows),
        aggregate_coverage_gap_ratio=_aggregate_coverage_gap_ratio(rows),
        aggregate_conflict_ratio=_aggregate_conflict_ratio(rows),
        average_confidence_gap_ratio=_average_probability(
            tuple(row.confidence_gap_ratio for row in rows),
        ),
        average_tool_agreement_score=_average_probability(
            tuple(row.tool_agreement_score for row in rows),
        ),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_source_scrapling_agent_reach_redundancy_report_payload(
    value: ResearchSourceScraplingAgentReachRedundancyReport | Mapping[str, object],
) -> dict[str, Any]:
    if type(value) is ResearchSourceScraplingAgentReachRedundancyReport:
        _require_hard_flags("report", value)
        _validate_report_digest(value)
        payload = _json_ready(asdict(value))
    elif type(value) is dict:
        payload = _copy_canonical_json_object(value)
    else:
        raise ValueError(
            "value must be a ResearchSourceScraplingAgentReachRedundancyReport or dict",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_public_payload_digest(payload)
    _validate_public_payload_schema(payload)
    return payload


def research_source_scrapling_agent_reach_redundancy_report_digest(
    report: ResearchSourceScraplingAgentReachRedundancyReport,
) -> str:
    _require_exact_type(report, ResearchSourceScraplingAgentReachRedundancyReport, "report")
    _require_hard_flags("report", report)
    _validate_report_consistency(report)
    _reject_unsafe_public_payload("report", report)
    return _report_digest_from_values(_report_values_without_digest(report))


def validate_research_source_scrapling_agent_reach_redundancy_report_payload(
    payload: Mapping[str, object],
) -> bool:
    try:
        research_source_scrapling_agent_reach_redundancy_report_payload(payload)
    except ValueError:
        return False
    return True


def _require_config(
    config: ResearchSourceScraplingAgentReachRedundancyConfig,
) -> ResearchSourceScraplingAgentReachRedundancyConfig:
    _require_exact_type(config, ResearchSourceScraplingAgentReachRedundancyConfig, "config")
    _require_hard_flags("config", config)
    _reject_unsafe_public_payload("config", config)
    ResearchSourceScraplingAgentReachRedundancyConfig(
        **{field.name: getattr(config, field.name) for field in fields(config)}
    )
    return config


def _normalize_inputs(
    inputs: Sequence[ResearchSourceScraplingAgentReachRedundancyInput],
) -> tuple[ResearchSourceScraplingAgentReachRedundancyInput, ...]:
    if isinstance(inputs, (str, bytes, dict)):
        raise ValueError("inputs must be a sequence of redundancy inputs")
    normalized = tuple(inputs)
    for item in normalized:
        _require_exact_type(item, ResearchSourceScraplingAgentReachRedundancyInput, "input")
        _require_hard_flags("input", item)
    return normalized


def _input_sort_key(
    item: ResearchSourceScraplingAgentReachRedundancyInput,
) -> tuple[str, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal]:
    return (
        item.observed_at.isoformat(),
        item.required_evidence_count,
        item.scrapling_evidence_count,
        item.agent_reach_evidence_count,
        item.overlapping_evidence_count,
        item.conflicting_evidence_count,
        item.scrapling_confidence_score,
        item.agent_reach_confidence_score,
    )


def _row_sort_key(
    row: ResearchSourceScraplingAgentReachRedundancyRow,
) -> tuple[str, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal]:
    return (
        row.observed_at.isoformat(),
        row.required_evidence_count,
        row.scrapling_evidence_count,
        row.agent_reach_evidence_count,
        row.overlapping_evidence_count,
        row.conflicting_evidence_count,
        row.scrapling_confidence_score,
        row.agent_reach_confidence_score,
    )


def _row_from_input(
    *,
    row_index: Decimal,
    item: ResearchSourceScraplingAgentReachRedundancyInput,
    config: ResearchSourceScraplingAgentReachRedundancyConfig,
    generated_at: datetime,
) -> ResearchSourceScraplingAgentReachRedundancyRow:
    if item.observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    redundant_coverage_ratio = _ratio(
        item.overlapping_evidence_count,
        item.required_evidence_count,
    )
    coverage_gap_ratio = _ratio(
        _absolute_difference(
            item.scrapling_evidence_count,
            item.agent_reach_evidence_count,
        ),
        item.required_evidence_count,
    )
    conflict_ratio = _optional_ratio_default_zero(
        item.conflicting_evidence_count,
        item.overlapping_evidence_count,
    )
    confidence_gap_ratio = _normalize_probability(
        "confidence_gap_ratio",
        _absolute_difference(
            item.scrapling_confidence_score,
            item.agent_reach_confidence_score,
        ),
    )
    tool_agreement_score = _tool_agreement_score(
        redundant_coverage_ratio=redundant_coverage_ratio,
        coverage_gap_ratio=coverage_gap_ratio,
        conflict_ratio=conflict_ratio,
        confidence_gap_ratio=confidence_gap_ratio,
        config=config,
    )
    reason_codes = _row_reason_codes(
        redundant_coverage_ratio=redundant_coverage_ratio,
        coverage_gap_ratio=coverage_gap_ratio,
        conflict_ratio=conflict_ratio,
        confidence_gap_ratio=confidence_gap_ratio,
        tool_agreement_score=tool_agreement_score,
        config=config,
    )
    return ResearchSourceScraplingAgentReachRedundancyRow(
        row_index=row_index,
        observed_at=item.observed_at,
        required_evidence_count=item.required_evidence_count,
        scrapling_evidence_count=item.scrapling_evidence_count,
        agent_reach_evidence_count=item.agent_reach_evidence_count,
        overlapping_evidence_count=item.overlapping_evidence_count,
        conflicting_evidence_count=item.conflicting_evidence_count,
        scrapling_confidence_score=item.scrapling_confidence_score,
        agent_reach_confidence_score=item.agent_reach_confidence_score,
        redundant_coverage_ratio=redundant_coverage_ratio,
        coverage_gap_ratio=coverage_gap_ratio,
        conflict_ratio=conflict_ratio,
        confidence_gap_ratio=confidence_gap_ratio,
        tool_agreement_score=tool_agreement_score,
        status=_status_from_reasons(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    redundant_coverage_ratio: Decimal,
    coverage_gap_ratio: Decimal,
    conflict_ratio: Decimal,
    confidence_gap_ratio: Decimal,
    tool_agreement_score: Decimal,
    config: ResearchSourceScraplingAgentReachRedundancyConfig,
) -> tuple[str, ...]:
    block_reasons: list[str] = []
    if redundant_coverage_ratio < config.min_redundant_coverage_watch_ratio:
        block_reasons.append("redundant_coverage_below_watch_threshold")
    if coverage_gap_ratio > config.max_coverage_gap_watch_ratio:
        block_reasons.append("coverage_gap_above_watch_threshold")
    if conflict_ratio > config.max_conflict_ratio_watch_ratio:
        block_reasons.append("conflict_ratio_above_watch_threshold")
    if confidence_gap_ratio > config.max_confidence_gap_watch_ratio:
        block_reasons.append("confidence_gap_above_watch_threshold")
    if tool_agreement_score < config.min_tool_agreement_watch_score:
        block_reasons.append("tool_agreement_below_watch_threshold")
    if block_reasons:
        return _normalize_reason_codes(tuple(block_reasons))

    watch_reasons: list[str] = []
    if redundant_coverage_ratio < config.min_redundant_coverage_pass_ratio:
        watch_reasons.append("redundant_coverage_below_pass_threshold")
    if coverage_gap_ratio > config.max_coverage_gap_pass_ratio:
        watch_reasons.append("coverage_gap_above_pass_threshold")
    if conflict_ratio > config.max_conflict_ratio_pass_ratio:
        watch_reasons.append("conflict_ratio_above_pass_threshold")
    if confidence_gap_ratio > config.max_confidence_gap_pass_ratio:
        watch_reasons.append("confidence_gap_above_pass_threshold")
    if tool_agreement_score < config.min_tool_agreement_pass_score:
        watch_reasons.append("tool_agreement_below_pass_threshold")
    return _normalize_reason_codes(tuple(watch_reasons))


def _tool_agreement_score(
    *,
    redundant_coverage_ratio: Decimal,
    coverage_gap_ratio: Decimal,
    conflict_ratio: Decimal,
    confidence_gap_ratio: Decimal,
    config: ResearchSourceScraplingAgentReachRedundancyConfig,
) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        coverage_balance_score = _normalize_probability(
            "coverage_balance_score",
            ONE - coverage_gap_ratio,
        )
        conflict_resilience_score = _normalize_probability(
            "conflict_resilience_score",
            ONE - conflict_ratio,
        )
        confidence_alignment_score = _normalize_probability(
            "confidence_alignment_score",
            ONE - confidence_gap_ratio,
        )
        return _normalize_probability(
            "tool_agreement_score",
            redundant_coverage_ratio * config.redundant_coverage_weight
            + coverage_balance_score * config.coverage_balance_weight
            + conflict_resilience_score * config.conflict_resilience_weight
            + confidence_alignment_score * config.confidence_alignment_weight,
        )


def _status_from_reasons(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    if reason_codes:
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[ResearchSourceScraplingAgentReachRedundancyRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceScraplingAgentReachRedundancyRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    detail_reasons: list[str] = []
    for row in rows:
        detail_reasons.extend(row.reason_codes)
    if detail_reasons:
        return _normalize_reason_codes(tuple(dict.fromkeys(detail_reasons)))
    return (PASS_REASON,)


def _reason_code_counts(
    rows: tuple[ResearchSourceScraplingAgentReachRedundancyRow, ...],
) -> tuple[ResearchSourceScraplingAgentReachRedundancyReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchSourceScraplingAgentReachRedundancyReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=Decimal("1.000000"),
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    if not counts:
        counts[PASS_REASON] = len(rows)
    return tuple(
        ResearchSourceScraplingAgentReachRedundancyReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_from_int(counts[reason_code]),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if counts[reason_code] > 0
    )


def _validate_input_counts(
    item: ResearchSourceScraplingAgentReachRedundancyInput,
) -> None:
    _validate_evidence_counts(
        required_evidence_count=item.required_evidence_count,
        scrapling_evidence_count=item.scrapling_evidence_count,
        agent_reach_evidence_count=item.agent_reach_evidence_count,
        overlapping_evidence_count=item.overlapping_evidence_count,
        conflicting_evidence_count=item.conflicting_evidence_count,
    )


def _validate_evidence_counts(
    *,
    required_evidence_count: Decimal,
    scrapling_evidence_count: Decimal,
    agent_reach_evidence_count: Decimal,
    overlapping_evidence_count: Decimal,
    conflicting_evidence_count: Decimal,
) -> None:
    if scrapling_evidence_count > required_evidence_count:
        raise ValueError("scrapling_evidence_count must not exceed required_evidence_count")
    if agent_reach_evidence_count > required_evidence_count:
        raise ValueError("agent_reach_evidence_count must not exceed required_evidence_count")
    if overlapping_evidence_count > scrapling_evidence_count:
        raise ValueError("overlapping_evidence_count must not exceed Scrapling count")
    if overlapping_evidence_count > agent_reach_evidence_count:
        raise ValueError("overlapping_evidence_count must not exceed agent-reach count")
    if conflicting_evidence_count > overlapping_evidence_count:
        raise ValueError("conflicting_evidence_count must not exceed overlapping count")


def _validate_row_base_consistency(
    row: ResearchSourceScraplingAgentReachRedundancyRow,
) -> None:
    _validate_evidence_counts(
        required_evidence_count=row.required_evidence_count,
        scrapling_evidence_count=row.scrapling_evidence_count,
        agent_reach_evidence_count=row.agent_reach_evidence_count,
        overlapping_evidence_count=row.overlapping_evidence_count,
        conflicting_evidence_count=row.conflicting_evidence_count,
    )
    expected_redundant_coverage_ratio = _ratio(
        row.overlapping_evidence_count,
        row.required_evidence_count,
    )
    if row.redundant_coverage_ratio != expected_redundant_coverage_ratio:
        raise ValueError("redundant_coverage_ratio must match evidence counts")
    expected_coverage_gap_ratio = _ratio(
        _absolute_difference(
            row.scrapling_evidence_count,
            row.agent_reach_evidence_count,
        ),
        row.required_evidence_count,
    )
    if row.coverage_gap_ratio != expected_coverage_gap_ratio:
        raise ValueError("coverage_gap_ratio must match evidence counts")
    expected_conflict_ratio = _optional_ratio_default_zero(
        row.conflicting_evidence_count,
        row.overlapping_evidence_count,
    )
    if row.conflict_ratio != expected_conflict_ratio:
        raise ValueError("conflict_ratio must match evidence counts")
    expected_confidence_gap_ratio = _normalize_probability(
        "confidence_gap_ratio",
        _absolute_difference(
            row.scrapling_confidence_score,
            row.agent_reach_confidence_score,
        ),
    )
    if row.confidence_gap_ratio != expected_confidence_gap_ratio:
        raise ValueError("confidence_gap_ratio must match confidence scores")


def _validate_row_consistency(
    row: ResearchSourceScraplingAgentReachRedundancyRow,
    config: ResearchSourceScraplingAgentReachRedundancyConfig,
) -> None:
    _validate_row_base_consistency(row)
    expected_tool_agreement_score = _tool_agreement_score(
        redundant_coverage_ratio=row.redundant_coverage_ratio,
        coverage_gap_ratio=row.coverage_gap_ratio,
        conflict_ratio=row.conflict_ratio,
        confidence_gap_ratio=row.confidence_gap_ratio,
        config=config,
    )
    if row.tool_agreement_score != expected_tool_agreement_score:
        raise ValueError("tool_agreement_score must match component scores")
    expected_reason_codes = _row_reason_codes(
        redundant_coverage_ratio=row.redundant_coverage_ratio,
        coverage_gap_ratio=row.coverage_gap_ratio,
        conflict_ratio=row.conflict_ratio,
        confidence_gap_ratio=row.confidence_gap_ratio,
        tool_agreement_score=row.tool_agreement_score,
        config=config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("row reason_codes must match derived redundancy logic")
    expected_status = _status_from_reasons(expected_reason_codes)
    if row.status != expected_status:
        raise ValueError("row status must match derived redundancy logic")


def _validate_report_consistency(
    report: ResearchSourceScraplingAgentReachRedundancyReport,
) -> None:
    _require_config(report.config)
    if report.config_version != report.config.config_version:
        raise ValueError("config_version must match config")
    expected_sort_keys = tuple(sorted(_row_sort_key(row) for row in report.rows))
    actual_sort_keys = tuple(_row_sort_key(row) for row in report.rows)
    if actual_sort_keys != expected_sort_keys:
        raise ValueError("rows must use deterministic canonical ordering")
    for index, row in enumerate(report.rows, start=1):
        _validate_row_consistency(row, report.config)
        if row.observed_at > report.generated_at:
            raise ValueError("row observed_at must not be after generated_at")
        if row.row_index != _decimal_from_int(index):
            raise ValueError("row_index must be sequential in canonical row order")
    if report.input_count != _decimal_from_int(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.row_count != _decimal_from_int(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.required_evidence_count != _sum_decimal(
        row.required_evidence_count for row in report.rows
    ):
        raise ValueError("required_evidence_count must match rows")
    if report.scrapling_evidence_count != _sum_decimal(
        row.scrapling_evidence_count for row in report.rows
    ):
        raise ValueError("scrapling_evidence_count must match rows")
    if report.agent_reach_evidence_count != _sum_decimal(
        row.agent_reach_evidence_count for row in report.rows
    ):
        raise ValueError("agent_reach_evidence_count must match rows")
    if report.overlapping_evidence_count != _sum_decimal(
        row.overlapping_evidence_count for row in report.rows
    ):
        raise ValueError("overlapping_evidence_count must match rows")
    if report.conflicting_evidence_count != _sum_decimal(
        row.conflicting_evidence_count for row in report.rows
    ):
        raise ValueError("conflicting_evidence_count must match rows")
    if report.aggregate_redundant_coverage_ratio != _aggregate_redundant_coverage_ratio(
        report.rows,
    ):
        raise ValueError("aggregate_redundant_coverage_ratio must match rows")
    if report.aggregate_coverage_gap_ratio != _aggregate_coverage_gap_ratio(report.rows):
        raise ValueError("aggregate_coverage_gap_ratio must match rows")
    if report.aggregate_conflict_ratio != _aggregate_conflict_ratio(report.rows):
        raise ValueError("aggregate_conflict_ratio must match rows")
    if report.average_confidence_gap_ratio != _average_probability(
        tuple(row.confidence_gap_ratio for row in report.rows),
    ):
        raise ValueError("average_confidence_gap_ratio must match rows")
    if report.average_tool_agreement_score != _average_probability(
        tuple(row.tool_agreement_score for row in report.rows),
    ):
        raise ValueError("average_tool_agreement_score must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _aggregate_redundant_coverage_ratio(
    rows: tuple[ResearchSourceScraplingAgentReachRedundancyRow, ...],
) -> Decimal:
    required = _sum_decimal(row.required_evidence_count for row in rows)
    if required == ZERO:
        return ZERO
    return _ratio(_sum_decimal(row.overlapping_evidence_count for row in rows), required)


def _aggregate_coverage_gap_ratio(
    rows: tuple[ResearchSourceScraplingAgentReachRedundancyRow, ...],
) -> Decimal:
    required = _sum_decimal(row.required_evidence_count for row in rows)
    if required == ZERO:
        return ZERO
    gap = _absolute_difference(
        _sum_decimal(row.scrapling_evidence_count for row in rows),
        _sum_decimal(row.agent_reach_evidence_count for row in rows),
    )
    return _ratio(gap, required)


def _aggregate_conflict_ratio(
    rows: tuple[ResearchSourceScraplingAgentReachRedundancyRow, ...],
) -> Decimal:
    overlap = _sum_decimal(row.overlapping_evidence_count for row in rows)
    conflict = _sum_decimal(row.conflicting_evidence_count for row in rows)
    return _optional_ratio_default_zero(conflict, overlap)


def _status_count(
    rows: tuple[ResearchSourceScraplingAgentReachRedundancyRow, ...],
    status: str,
) -> Decimal:
    return _decimal_from_int(sum(1 for row in rows if row.status == status))


def _average_probability(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _normalize_probability(
            "average_probability",
            _sum_decimal(values) / _decimal_from_int(len(values)),
        )


def _sum_decimal(values: Sequence[Decimal] | Any) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(sum(tuple(values), ZERO))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("ratio denominator must be positive")
    with localcontext(_DECIMAL_CONTEXT):
        return _normalize_probability("ratio", numerator / denominator)


def _absolute_difference(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return abs(left - right)


def _optional_ratio_default_zero(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        if numerator != ZERO:
            raise ValueError("ratio numerator must be zero when denominator is zero")
        return ZERO
    return _ratio(numerator, denominator)


def _require_ordered_floor(
    label: str,
    watch_value: Decimal,
    pass_value: Decimal,
) -> None:
    if watch_value > pass_value:
        raise ValueError(f"{label} watch threshold must not exceed pass threshold")


def _require_ordered_ceiling(
    label: str,
    pass_value: Decimal,
    watch_value: Decimal,
) -> None:
    if pass_value > watch_value:
        raise ValueError(f"{label} pass threshold must not exceed watch threshold")


def _normalize_rows(
    rows: object,
) -> tuple[ResearchSourceScraplingAgentReachRedundancyRow, ...]:
    if isinstance(rows, (str, bytes, dict)):
        raise ValueError("rows must be a tuple of redundancy rows")
    normalized = tuple(rows)  # type: ignore[arg-type]
    for row in normalized:
        _require_exact_type(row, ResearchSourceScraplingAgentReachRedundancyRow, "row")
        _require_hard_flags("row", row)
        _reject_unsafe_public_payload("row", row)
    return normalized


def _normalize_reason_code_counts(
    counts: object,
) -> tuple[ResearchSourceScraplingAgentReachRedundancyReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes, dict)):
        raise ValueError("reason_code_counts must be a tuple")
    normalized = tuple(counts)  # type: ignore[arg-type]
    for item in normalized:
        _require_exact_type(
            item,
            ResearchSourceScraplingAgentReachRedundancyReasonCodeCount,
            "reason_code_count",
        )
        _require_hard_flags("reason_code_count", item)
        _reject_unsafe_public_payload("reason_code_count", item)
    return normalized


def _normalize_reason_codes(reason_codes: object) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        normalized = tuple(reason_codes)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    for reason_code in normalized:
        _normalize_reason_code("reason_code", reason_code)
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    return tuple(
        reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in normalized
    )


def _normalize_reason_code(field_name: str, value: object) -> str:
    _require_public_identifier(field_name, value)
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be supported")
    return value


def _require_status(field_name: str, value: object) -> None:
    _require_public_identifier(field_name, value)
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if PUBLIC_IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a safe public identifier")
    _reject_unsafe_public_string(field_name, value)


def _require_private_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "" or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    with localcontext(_DECIMAL_CONTEXT):
        integral_value = normalized.to_integral_value()
    if normalized != integral_value:
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not be signed zero")
    try:
        normalized = _quantize(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be quantizable to six decimals") from exc
    if normalized.is_zero() and normalized.is_signed():
        raise ValueError(f"{field_name} must not quantize to signed zero")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _decimal_from_int(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _validate_report_digest(
    report: ResearchSourceScraplingAgentReachRedundancyReport,
) -> None:
    _require_exact_type(report, ResearchSourceScraplingAgentReachRedundancyReport, "report")
    _require_hard_flags("report", report)
    expected_digest = research_source_scrapling_agent_reach_redundancy_report_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")


def _validate_public_payload_digest(payload: Mapping[str, object]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest)
    values = dict(payload)
    values.pop("derived_validation_digest", None)
    expected_digest = _report_digest_from_values(values)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest must match payload")


def _validate_public_payload_schema(payload: Mapping[str, object]) -> None:
    _require_exact_payload_keys(
        "payload",
        payload,
        _payload_field_names(ResearchSourceScraplingAgentReachRedundancyReport),
    )
    ResearchSourceScraplingAgentReachRedundancyReport(
        generated_at=_datetime_from_payload("generated_at", payload["generated_at"]),
        config_version=_string_from_payload("config_version", payload["config_version"]),
        config=_config_from_payload("config", payload["config"]),
        input_count=_count_from_payload("input_count", payload["input_count"]),
        row_count=_count_from_payload("row_count", payload["row_count"]),
        required_evidence_count=_count_from_payload(
            "required_evidence_count",
            payload["required_evidence_count"],
        ),
        scrapling_evidence_count=_count_from_payload(
            "scrapling_evidence_count",
            payload["scrapling_evidence_count"],
        ),
        agent_reach_evidence_count=_count_from_payload(
            "agent_reach_evidence_count",
            payload["agent_reach_evidence_count"],
        ),
        overlapping_evidence_count=_count_from_payload(
            "overlapping_evidence_count",
            payload["overlapping_evidence_count"],
        ),
        conflicting_evidence_count=_count_from_payload(
            "conflicting_evidence_count",
            payload["conflicting_evidence_count"],
        ),
        aggregate_redundant_coverage_ratio=_probability_from_payload(
            "aggregate_redundant_coverage_ratio",
            payload["aggregate_redundant_coverage_ratio"],
        ),
        aggregate_coverage_gap_ratio=_probability_from_payload(
            "aggregate_coverage_gap_ratio",
            payload["aggregate_coverage_gap_ratio"],
        ),
        aggregate_conflict_ratio=_probability_from_payload(
            "aggregate_conflict_ratio",
            payload["aggregate_conflict_ratio"],
        ),
        average_confidence_gap_ratio=_probability_from_payload(
            "average_confidence_gap_ratio",
            payload["average_confidence_gap_ratio"],
        ),
        average_tool_agreement_score=_probability_from_payload(
            "average_tool_agreement_score",
            payload["average_tool_agreement_score"],
        ),
        pass_count=_count_from_payload("pass_count", payload["pass_count"]),
        watch_count=_count_from_payload("watch_count", payload["watch_count"]),
        block_count=_count_from_payload("block_count", payload["block_count"]),
        status=_string_from_payload("status", payload["status"]),
        reason_codes=_reason_codes_from_payload("reason_codes", payload["reason_codes"]),
        reason_code_counts=_reason_code_counts_from_payload(
            "reason_code_counts",
            payload["reason_code_counts"],
        ),
        rows=_rows_from_payload("rows", payload["rows"]),
        derived_validation_digest=_string_from_payload(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_true_flag_from_payload("paper_only", payload["paper_only"]),
        report_only=_true_flag_from_payload("report_only", payload["report_only"]),
        readonly=_true_flag_from_payload("readonly", payload["readonly"]),
    )


def _rows_from_payload(
    field_name: str,
    value: object,
) -> tuple[ResearchSourceScraplingAgentReachRedundancyRow, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return tuple(
        _row_from_payload(f"{field_name}[{index}]", item)
        for index, item in enumerate(value)
    )


def _row_from_payload(
    field_name: str,
    value: object,
) -> ResearchSourceScraplingAgentReachRedundancyRow:
    if type(value) is not dict:
        raise ValueError(f"{field_name} must be a JSON object")
    _require_exact_payload_keys(
        field_name,
        value,
        _payload_field_names(ResearchSourceScraplingAgentReachRedundancyRow),
    )
    return ResearchSourceScraplingAgentReachRedundancyRow(
        row_index=_count_from_payload(f"{field_name}.row_index", value["row_index"]),
        observed_at=_datetime_from_payload(f"{field_name}.observed_at", value["observed_at"]),
        required_evidence_count=_count_from_payload(
            f"{field_name}.required_evidence_count",
            value["required_evidence_count"],
        ),
        scrapling_evidence_count=_count_from_payload(
            f"{field_name}.scrapling_evidence_count",
            value["scrapling_evidence_count"],
        ),
        agent_reach_evidence_count=_count_from_payload(
            f"{field_name}.agent_reach_evidence_count",
            value["agent_reach_evidence_count"],
        ),
        overlapping_evidence_count=_count_from_payload(
            f"{field_name}.overlapping_evidence_count",
            value["overlapping_evidence_count"],
        ),
        conflicting_evidence_count=_count_from_payload(
            f"{field_name}.conflicting_evidence_count",
            value["conflicting_evidence_count"],
        ),
        scrapling_confidence_score=_probability_from_payload(
            f"{field_name}.scrapling_confidence_score",
            value["scrapling_confidence_score"],
        ),
        agent_reach_confidence_score=_probability_from_payload(
            f"{field_name}.agent_reach_confidence_score",
            value["agent_reach_confidence_score"],
        ),
        redundant_coverage_ratio=_probability_from_payload(
            f"{field_name}.redundant_coverage_ratio",
            value["redundant_coverage_ratio"],
        ),
        coverage_gap_ratio=_probability_from_payload(
            f"{field_name}.coverage_gap_ratio",
            value["coverage_gap_ratio"],
        ),
        conflict_ratio=_probability_from_payload(
            f"{field_name}.conflict_ratio",
            value["conflict_ratio"],
        ),
        confidence_gap_ratio=_probability_from_payload(
            f"{field_name}.confidence_gap_ratio",
            value["confidence_gap_ratio"],
        ),
        tool_agreement_score=_probability_from_payload(
            f"{field_name}.tool_agreement_score",
            value["tool_agreement_score"],
        ),
        status=_string_from_payload(f"{field_name}.status", value["status"]),
        reason_codes=_reason_codes_from_payload(
            f"{field_name}.reason_codes",
            value["reason_codes"],
        ),
        paper_only=_true_flag_from_payload(f"{field_name}.paper_only", value["paper_only"]),
        report_only=_true_flag_from_payload(
            f"{field_name}.report_only",
            value["report_only"],
        ),
        readonly=_true_flag_from_payload(f"{field_name}.readonly", value["readonly"]),
    )


def _config_from_payload(
    field_name: str,
    value: object,
) -> ResearchSourceScraplingAgentReachRedundancyConfig:
    if type(value) is not dict:
        raise ValueError(f"{field_name} must be a JSON object")
    _require_exact_payload_keys(
        field_name,
        value,
        _payload_field_names(ResearchSourceScraplingAgentReachRedundancyConfig),
    )
    return ResearchSourceScraplingAgentReachRedundancyConfig(
        config_version=_string_from_payload(
            f"{field_name}.config_version",
            value["config_version"],
        ),
        min_redundant_coverage_pass_ratio=_probability_from_payload(
            f"{field_name}.min_redundant_coverage_pass_ratio",
            value["min_redundant_coverage_pass_ratio"],
        ),
        min_redundant_coverage_watch_ratio=_probability_from_payload(
            f"{field_name}.min_redundant_coverage_watch_ratio",
            value["min_redundant_coverage_watch_ratio"],
        ),
        max_coverage_gap_pass_ratio=_probability_from_payload(
            f"{field_name}.max_coverage_gap_pass_ratio",
            value["max_coverage_gap_pass_ratio"],
        ),
        max_coverage_gap_watch_ratio=_probability_from_payload(
            f"{field_name}.max_coverage_gap_watch_ratio",
            value["max_coverage_gap_watch_ratio"],
        ),
        max_conflict_ratio_pass_ratio=_probability_from_payload(
            f"{field_name}.max_conflict_ratio_pass_ratio",
            value["max_conflict_ratio_pass_ratio"],
        ),
        max_conflict_ratio_watch_ratio=_probability_from_payload(
            f"{field_name}.max_conflict_ratio_watch_ratio",
            value["max_conflict_ratio_watch_ratio"],
        ),
        max_confidence_gap_pass_ratio=_probability_from_payload(
            f"{field_name}.max_confidence_gap_pass_ratio",
            value["max_confidence_gap_pass_ratio"],
        ),
        max_confidence_gap_watch_ratio=_probability_from_payload(
            f"{field_name}.max_confidence_gap_watch_ratio",
            value["max_confidence_gap_watch_ratio"],
        ),
        min_tool_agreement_pass_score=_probability_from_payload(
            f"{field_name}.min_tool_agreement_pass_score",
            value["min_tool_agreement_pass_score"],
        ),
        min_tool_agreement_watch_score=_probability_from_payload(
            f"{field_name}.min_tool_agreement_watch_score",
            value["min_tool_agreement_watch_score"],
        ),
        redundant_coverage_weight=_probability_from_payload(
            f"{field_name}.redundant_coverage_weight",
            value["redundant_coverage_weight"],
        ),
        coverage_balance_weight=_probability_from_payload(
            f"{field_name}.coverage_balance_weight",
            value["coverage_balance_weight"],
        ),
        conflict_resilience_weight=_probability_from_payload(
            f"{field_name}.conflict_resilience_weight",
            value["conflict_resilience_weight"],
        ),
        confidence_alignment_weight=_probability_from_payload(
            f"{field_name}.confidence_alignment_weight",
            value["confidence_alignment_weight"],
        ),
        paper_only=_true_flag_from_payload(
            f"{field_name}.paper_only",
            value["paper_only"],
        ),
        report_only=_true_flag_from_payload(
            f"{field_name}.report_only",
            value["report_only"],
        ),
        readonly=_true_flag_from_payload(
            f"{field_name}.readonly",
            value["readonly"],
        ),
    )


def _reason_code_counts_from_payload(
    field_name: str,
    value: object,
) -> tuple[ResearchSourceScraplingAgentReachRedundancyReasonCodeCount, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return tuple(
        _reason_code_count_from_payload(f"{field_name}[{index}]", item)
        for index, item in enumerate(value)
    )


def _reason_code_count_from_payload(
    field_name: str,
    value: object,
) -> ResearchSourceScraplingAgentReachRedundancyReasonCodeCount:
    if type(value) is not dict:
        raise ValueError(f"{field_name} must be a JSON object")
    _require_exact_payload_keys(
        field_name,
        value,
        _payload_field_names(
            ResearchSourceScraplingAgentReachRedundancyReasonCodeCount,
        ),
    )
    return ResearchSourceScraplingAgentReachRedundancyReasonCodeCount(
        reason_code=_string_from_payload(
            f"{field_name}.reason_code",
            value["reason_code"],
        ),
        count=_count_from_payload(f"{field_name}.count", value["count"]),
        paper_only=_true_flag_from_payload(f"{field_name}.paper_only", value["paper_only"]),
        report_only=_true_flag_from_payload(
            f"{field_name}.report_only",
            value["report_only"],
        ),
        readonly=_true_flag_from_payload(f"{field_name}.readonly", value["readonly"]),
    )


def _reason_codes_from_payload(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return _normalize_reason_codes(tuple(value))


def _datetime_from_payload(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a UTC datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a UTC datetime string") from exc
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return normalized


def _count_from_payload(field_name: str, value: object) -> Decimal:
    return _normalize_nonnegative_count(field_name, _decimal_from_payload(field_name, value))


def _probability_from_payload(field_name: str, value: object) -> Decimal:
    return _normalize_probability(field_name, _decimal_from_payload(field_name, value))


def _decimal_from_payload(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    if DECIMAL_PAYLOAD_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    normalized = _normalize_decimal(field_name, Decimal(value))
    if str(normalized) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _string_from_payload(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _true_flag_from_payload(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _require_exact_payload_keys(
    field_name: str,
    value: Mapping[str, object],
    expected_keys: tuple[str, ...],
) -> None:
    actual_keys = set(value)
    expected_key_set = set(expected_keys)
    if actual_keys != expected_key_set:
        raise ValueError(f"{field_name} must contain exactly supported payload fields")


def _payload_field_names(cls: type[object]) -> tuple[str, ...]:
    return tuple(field.name for field in fields(cls))


def _report_values_without_digest(
    report: ResearchSourceScraplingAgentReachRedundancyReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest_payload",
        payload,
        allow_json_containers=True,
    )
    canonical_payload = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical_payload.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        if value.is_zero() and value.is_signed():
            raise ValueError("Decimal payload value must not be signed zero")
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


def _copy_canonical_json_object(value: object) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError("payload must be a canonical JSON object")
    return {
        key: _copy_canonical_json_value(f"payload.{key}", item)
        for key, item in value.items()
        if _require_json_key(key)
    }


def _copy_canonical_json_value(field_name: str, value: object) -> Any:
    if value is None or type(value) is bool or type(value) is str:
        return value
    if type(value) is dict:
        return {
            key: _copy_canonical_json_value(f"{field_name}.{key}", item)
            for key, item in value.items()
            if _require_json_key(key)
        }
    if type(value) is list:
        return [
            _copy_canonical_json_value(f"{field_name}[{index}]", item)
            for index, item in enumerate(value)
        ]
    raise ValueError(f"{field_name} must use canonical JSON scalar and container types")


def _require_json_key(value: object) -> bool:
    if type(value) is not str:
        raise ValueError("JSON object keys must be strings")
    return True


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
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, (tuple, list)):
        if not allow_json_containers and isinstance(value, list):
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{path}.{key} is not safe for public payloads")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public payload content")
