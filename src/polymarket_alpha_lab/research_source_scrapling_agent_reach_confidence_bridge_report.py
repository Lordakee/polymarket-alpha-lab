"""Report-only Scrapling and agent-reach confidence bridge diagnostics."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_SOURCE_SCRAPLING_AGENT_REACH_CONFIDENCE_BRIDGE_REPORT_CONFIG_VERSION = (
    "research-source-scrapling-agent-reach-confidence-bridge-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
RESEARCH_SOURCE_SCRAPLING_AGENT_REACH_CONFIDENCE_BRIDGE_STATUSES = (
    STATUS_PASS,
    STATUS_WATCH,
    STATUS_BLOCK,
)

NO_INPUTS_REASON = "scrapling_agent_reach_confidence_bridge_no_inputs"
PASS_REASON = "scrapling_agent_reach_confidence_bridge_pass"
BRIDGE_CONFIDENCE_BLOCK_REASON = "bridge_confidence_below_watch_threshold"
DUAL_TOOL_FLOOR_BLOCK_REASON = "dual_tool_floor_below_watch_threshold"
CONFIDENCE_GAP_BLOCK_REASON = "confidence_gap_above_watch_threshold"
CONTRADICTION_BLOCK_REASON = "contradiction_pressure_above_watch_threshold"
UNRESOLVED_GAP_BLOCK_REASON = "unresolved_gap_above_watch_threshold"
BRIDGE_CONFIDENCE_WATCH_REASON = "bridge_confidence_below_pass_threshold"
DUAL_TOOL_FLOOR_WATCH_REASON = "dual_tool_floor_below_pass_threshold"
CONFIDENCE_GAP_WATCH_REASON = "confidence_gap_above_pass_threshold"
CONTRADICTION_WATCH_REASON = "contradiction_pressure_above_pass_threshold"
UNRESOLVED_GAP_WATCH_REASON = "unresolved_gap_above_pass_threshold"

REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    BRIDGE_CONFIDENCE_BLOCK_REASON,
    DUAL_TOOL_FLOOR_BLOCK_REASON,
    CONFIDENCE_GAP_BLOCK_REASON,
    CONTRADICTION_BLOCK_REASON,
    UNRESOLVED_GAP_BLOCK_REASON,
    BRIDGE_CONFIDENCE_WATCH_REASON,
    DUAL_TOOL_FLOOR_WATCH_REASON,
    CONFIDENCE_GAP_WATCH_REASON,
    CONTRADICTION_WATCH_REASON,
    UNRESOLVED_GAP_WATCH_REASON,
    PASS_REASON,
)
BLOCK_REASON_CODES = frozenset(
    reason_code
    for reason_code in REASON_CODE_SEQUENCE
    if reason_code.endswith("_watch_threshold")
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")

UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "raw_",
    "_raw",
    "candidate",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "source_url",
    "source_text",
    "raw_text",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "live",
    "sizing",
    "recommend",
    "private",
    "secret",
)
UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "http://",
    "https://",
    "://",
    "raw_candidate",
    "candidate id",
    "candidate_id",
    "market id",
    "market_id",
    "market_slug",
    "source_url",
    "source_text",
    "raw_text",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "live",
    "sizing",
    "recommend",
    "private",
    "secret",
)

__all__ = (
    "DEFAULT_RESEARCH_SOURCE_SCRAPLING_AGENT_REACH_CONFIDENCE_BRIDGE_REPORT_CONFIG_VERSION",
    "RESEARCH_SOURCE_SCRAPLING_AGENT_REACH_CONFIDENCE_BRIDGE_STATUSES",
    "ResearchSourceScraplingAgentReachConfidenceBridgeConfig",
    "ResearchSourceScraplingAgentReachConfidenceBridgeObservation",
    "ResearchSourceScraplingAgentReachConfidenceBridgeReasonCodeCount",
    "ResearchSourceScraplingAgentReachConfidenceBridgeReport",
    "ResearchSourceScraplingAgentReachConfidenceBridgeRow",
    "build_research_source_scrapling_agent_reach_confidence_bridge_report",
    "research_source_scrapling_agent_reach_confidence_bridge_report_digest",
    "research_source_scrapling_agent_reach_confidence_bridge_report_payload",
    "validate_research_source_scrapling_agent_reach_confidence_bridge_report_payload",
)


@dataclass(frozen=True)
class ResearchSourceScraplingAgentReachConfidenceBridgeConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_SCRAPLING_AGENT_REACH_CONFIDENCE_BRIDGE_REPORT_CONFIG_VERSION
    )
    min_pass_bridge_confidence_score: Decimal = Decimal("0.850000")
    min_watch_bridge_confidence_score: Decimal = Decimal("0.550000")
    min_pass_dual_tool_floor_score: Decimal = Decimal("0.750000")
    min_watch_dual_tool_floor_score: Decimal = Decimal("0.500000")
    max_pass_confidence_gap_ratio: Decimal = Decimal("0.100000")
    max_watch_confidence_gap_ratio: Decimal = Decimal("0.400000")
    max_pass_contradiction_pressure_score: Decimal = Decimal("0.100000")
    max_watch_contradiction_pressure_score: Decimal = Decimal("0.350000")
    max_pass_unresolved_gap_score: Decimal = Decimal("0.100000")
    max_watch_unresolved_gap_score: Decimal = Decimal("0.300000")
    bridge_tool_confidence_weight: Decimal = Decimal("0.500000")
    bridge_authority_alignment_weight: Decimal = Decimal("0.218750")
    bridge_freshness_weight: Decimal = Decimal("0.281250")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingAgentReachConfidenceBridgeConfig:
            raise TypeError(
                "ResearchSourceScraplingAgentReachConfidenceBridgeConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceScraplingAgentReachConfidenceBridgeConfig,
            "config",
        )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_SCRAPLING_AGENT_REACH_CONFIDENCE_BRIDGE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_bridge_confidence_score",
            "min_watch_bridge_confidence_score",
            "min_pass_dual_tool_floor_score",
            "min_watch_dual_tool_floor_score",
            "max_pass_confidence_gap_ratio",
            "max_watch_confidence_gap_ratio",
            "max_pass_contradiction_pressure_score",
            "max_watch_contradiction_pressure_score",
            "max_pass_unresolved_gap_score",
            "max_watch_unresolved_gap_score",
            "bridge_tool_confidence_weight",
            "bridge_authority_alignment_weight",
            "bridge_freshness_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_ordered_floor(
            "bridge confidence",
            self.min_watch_bridge_confidence_score,
            self.min_pass_bridge_confidence_score,
        )
        _require_ordered_floor(
            "dual tool floor",
            self.min_watch_dual_tool_floor_score,
            self.min_pass_dual_tool_floor_score,
        )
        _require_ordered_ceiling(
            "confidence gap",
            self.max_pass_confidence_gap_ratio,
            self.max_watch_confidence_gap_ratio,
        )
        _require_ordered_ceiling(
            "contradiction pressure",
            self.max_pass_contradiction_pressure_score,
            self.max_watch_contradiction_pressure_score,
        )
        _require_ordered_ceiling(
            "unresolved gap",
            self.max_pass_unresolved_gap_score,
            self.max_watch_unresolved_gap_score,
        )
        weight_sum = _quantize(
            self.bridge_tool_confidence_weight
            + self.bridge_authority_alignment_weight
            + self.bridge_freshness_weight,
        )
        if weight_sum != ONE:
            raise ValueError("bridge confidence weights must sum to 1")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceScraplingAgentReachConfidenceBridgeObservation:
    private_bridge_ref: str
    observed_at: datetime
    scrapling_capture_confidence_score: Decimal
    scrapling_extraction_confidence_score: Decimal
    agent_reach_retrieval_confidence_score: Decimal
    agent_reach_corroboration_confidence_score: Decimal
    authority_alignment_score: Decimal
    freshness_score: Decimal
    contradiction_pressure_score: Decimal
    unresolved_gap_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingAgentReachConfidenceBridgeObservation:
            raise TypeError(
                "ResearchSourceScraplingAgentReachConfidenceBridgeObservation does "
                "not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceScraplingAgentReachConfidenceBridgeObservation,
            "observation",
        )
        _require_private_string("private_bridge_ref", self.private_bridge_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "scrapling_capture_confidence_score",
            "scrapling_extraction_confidence_score",
            "agent_reach_retrieval_confidence_score",
            "agent_reach_corroboration_confidence_score",
            "authority_alignment_score",
            "freshness_score",
            "contradiction_pressure_score",
            "unresolved_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchSourceScraplingAgentReachConfidenceBridgeRow:
    row_index: Decimal
    observed_at: datetime
    scrapling_confidence_score: Decimal
    agent_reach_confidence_score: Decimal
    authority_alignment_score: Decimal
    freshness_score: Decimal
    contradiction_pressure_score: Decimal
    unresolved_gap_score: Decimal
    confidence_gap_ratio: Decimal
    dual_tool_floor_score: Decimal
    bridge_confidence_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingAgentReachConfidenceBridgeRow:
            raise TypeError(
                "ResearchSourceScraplingAgentReachConfidenceBridgeRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceScraplingAgentReachConfidenceBridgeRow, "row")
        object.__setattr__(
            self,
            "row_index",
            _normalize_positive_count("row_index", self.row_index),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "scrapling_confidence_score",
            "agent_reach_confidence_score",
            "authority_alignment_score",
            "freshness_score",
            "contradiction_pressure_score",
            "unresolved_gap_score",
            "confidence_gap_ratio",
            "dual_tool_floor_score",
            "bridge_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _validate_row_derived_metrics(self)
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        if self.status != _status_from_reasons(self.reason_codes):
            raise ValueError("row status must match reason_codes")
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourceScraplingAgentReachConfidenceBridgeReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingAgentReachConfidenceBridgeReasonCodeCount:
            raise TypeError(
                "ResearchSourceScraplingAgentReachConfidenceBridgeReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceScraplingAgentReachConfidenceBridgeReasonCodeCount,
            "reason_code_count",
        )
        object.__setattr__(
            self,
            "reason_code",
            _normalize_reason_code("reason_code", self.reason_code),
        )
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchSourceScraplingAgentReachConfidenceBridgeReport:
    generated_at: datetime
    config_version: str
    observation_count: Decimal
    row_count: Decimal
    average_scrapling_confidence_score: Decimal
    average_agent_reach_confidence_score: Decimal
    average_authority_alignment_score: Decimal
    average_freshness_score: Decimal
    average_bridge_confidence_score: Decimal
    average_dual_tool_floor_score: Decimal
    average_confidence_gap_ratio: Decimal
    highest_confidence_gap_ratio: Decimal
    highest_contradiction_pressure_score: Decimal
    highest_unresolved_gap_score: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchSourceScraplingAgentReachConfidenceBridgeReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchSourceScraplingAgentReachConfidenceBridgeRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingAgentReachConfidenceBridgeReport:
            raise TypeError(
                "ResearchSourceScraplingAgentReachConfidenceBridgeReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceScraplingAgentReachConfidenceBridgeReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_SCRAPLING_AGENT_REACH_CONFIDENCE_BRIDGE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "observation_count",
            "row_count",
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
            "average_scrapling_confidence_score",
            "average_agent_reach_confidence_score",
            "average_authority_alignment_score",
            "average_freshness_score",
            "average_bridge_confidence_score",
            "average_dual_tool_floor_score",
            "average_confidence_gap_ratio",
            "highest_confidence_gap_ratio",
            "highest_contradiction_pressure_score",
            "highest_unresolved_gap_score",
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
        return research_source_scrapling_agent_reach_confidence_bridge_report_payload(self)


def build_research_source_scrapling_agent_reach_confidence_bridge_report(
    observations: Sequence[ResearchSourceScraplingAgentReachConfidenceBridgeObservation],
    *,
    config: ResearchSourceScraplingAgentReachConfidenceBridgeConfig | None = None,
    generated_at: datetime,
) -> ResearchSourceScraplingAgentReachConfidenceBridgeReport:
    cfg = (
        ResearchSourceScraplingAgentReachConfidenceBridgeConfig()
        if config is None
        else _require_config(config)
    )
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    derived_rows = tuple(
        _row_from_observation(
            row_index=_decimal_from_int(index),
            observation=observation,
            config=cfg,
            generated_at=generated_at_utc,
        )
        for index, observation in enumerate(
            sorted(normalized_observations, key=_observation_sort_key),
            start=1,
        )
    )
    rows = tuple(
        replace(row, row_index=_decimal_from_int(index))
        for index, row in enumerate(
            sorted(derived_rows, key=_row_sort_key),
            start=1,
        )
    )
    return ResearchSourceScraplingAgentReachConfidenceBridgeReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        observation_count=_decimal_from_int(len(normalized_observations)),
        row_count=_decimal_from_int(len(rows)),
        average_scrapling_confidence_score=_average_probability(
            tuple(row.scrapling_confidence_score for row in rows),
        ),
        average_agent_reach_confidence_score=_average_probability(
            tuple(row.agent_reach_confidence_score for row in rows),
        ),
        average_authority_alignment_score=_average_probability(
            tuple(row.authority_alignment_score for row in rows),
        ),
        average_freshness_score=_average_probability(
            tuple(row.freshness_score for row in rows),
        ),
        average_bridge_confidence_score=_average_probability(
            tuple(row.bridge_confidence_score for row in rows),
        ),
        average_dual_tool_floor_score=_average_probability(
            tuple(row.dual_tool_floor_score for row in rows),
        ),
        average_confidence_gap_ratio=_average_probability(
            tuple(row.confidence_gap_ratio for row in rows),
        ),
        highest_confidence_gap_ratio=_max_probability(
            tuple(row.confidence_gap_ratio for row in rows),
        ),
        highest_contradiction_pressure_score=_max_probability(
            tuple(row.contradiction_pressure_score for row in rows),
        ),
        highest_unresolved_gap_score=_max_probability(
            tuple(row.unresolved_gap_score for row in rows),
        ),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_source_scrapling_agent_reach_confidence_bridge_report_payload(
    value: ResearchSourceScraplingAgentReachConfidenceBridgeReport | Mapping[str, object],
) -> dict[str, Any]:
    if type(value) is ResearchSourceScraplingAgentReachConfidenceBridgeReport:
        _require_hard_flags("report", value)
        _validate_report_digest(value)
        payload = _json_ready(asdict(value))
        validate_schema = False
    elif isinstance(value, Mapping):
        payload = _copy_json_object(value)
        validate_schema = True
    else:
        raise ValueError(
            "value must be a ResearchSourceScraplingAgentReachConfidenceBridgeReport "
            "or dict",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_status_values_in_payload(payload)
    _validate_public_payload_digest(payload)
    if validate_schema:
        _validate_public_payload_schema(payload)
    return payload


def research_source_scrapling_agent_reach_confidence_bridge_report_digest(
    report: ResearchSourceScraplingAgentReachConfidenceBridgeReport,
) -> str:
    _require_exact_type(report, ResearchSourceScraplingAgentReachConfidenceBridgeReport, "report")
    _require_hard_flags("report", report)
    return _report_digest_from_values(_report_values_without_digest(report))


def validate_research_source_scrapling_agent_reach_confidence_bridge_report_payload(
    payload: Mapping[str, object],
) -> bool:
    try:
        research_source_scrapling_agent_reach_confidence_bridge_report_payload(payload)
    except ValueError:
        return False
    return True


def _require_config(
    config: ResearchSourceScraplingAgentReachConfidenceBridgeConfig,
) -> ResearchSourceScraplingAgentReachConfidenceBridgeConfig:
    _require_exact_type(config, ResearchSourceScraplingAgentReachConfidenceBridgeConfig, "config")
    _require_hard_flags("config", config)
    _reject_unsafe_public_payload("config", config)
    return config


def _normalize_observations(
    observations: Sequence[ResearchSourceScraplingAgentReachConfidenceBridgeObservation],
) -> tuple[ResearchSourceScraplingAgentReachConfidenceBridgeObservation, ...]:
    if isinstance(observations, (str, bytes, dict)):
        raise ValueError("observations must be a sequence of confidence bridge observations")
    normalized = tuple(observations)
    for observation in normalized:
        _require_exact_type(
            observation,
            ResearchSourceScraplingAgentReachConfidenceBridgeObservation,
            "observation",
        )
        _require_hard_flags("observation", observation)
    return normalized


def _observation_sort_key(
    observation: ResearchSourceScraplingAgentReachConfidenceBridgeObservation,
) -> tuple[str, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal]:
    return (
        observation.observed_at.isoformat(),
        observation.scrapling_capture_confidence_score,
        observation.scrapling_extraction_confidence_score,
        observation.agent_reach_retrieval_confidence_score,
        observation.agent_reach_corroboration_confidence_score,
        observation.authority_alignment_score,
        observation.freshness_score,
        observation.contradiction_pressure_score,
        observation.unresolved_gap_score,
    )


def _row_sort_key(
    row: ResearchSourceScraplingAgentReachConfidenceBridgeRow,
) -> tuple[
    str,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    str,
    tuple[str, ...],
]:
    return (
        row.observed_at.isoformat(),
        row.scrapling_confidence_score,
        row.agent_reach_confidence_score,
        row.authority_alignment_score,
        row.freshness_score,
        row.contradiction_pressure_score,
        row.unresolved_gap_score,
        row.confidence_gap_ratio,
        row.dual_tool_floor_score,
        row.bridge_confidence_score,
        row.status,
        row.reason_codes,
    )


def _row_from_observation(
    *,
    row_index: Decimal,
    observation: ResearchSourceScraplingAgentReachConfidenceBridgeObservation,
    config: ResearchSourceScraplingAgentReachConfidenceBridgeConfig,
    generated_at: datetime,
) -> ResearchSourceScraplingAgentReachConfidenceBridgeRow:
    if observation.observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    scrapling_confidence_score = _average_probability(
        (
            observation.scrapling_capture_confidence_score,
            observation.scrapling_extraction_confidence_score,
        ),
    )
    agent_reach_confidence_score = _average_probability(
        (
            observation.agent_reach_retrieval_confidence_score,
            observation.agent_reach_corroboration_confidence_score,
        ),
    )
    confidence_gap_ratio = _normalize_probability(
        "confidence_gap_ratio",
        abs(scrapling_confidence_score - agent_reach_confidence_score),
    )
    dual_tool_floor_score = min(scrapling_confidence_score, agent_reach_confidence_score)
    bridge_confidence_score = _bridge_confidence_score(
        scrapling_confidence_score=scrapling_confidence_score,
        agent_reach_confidence_score=agent_reach_confidence_score,
        authority_alignment_score=observation.authority_alignment_score,
        freshness_score=observation.freshness_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        bridge_confidence_score=bridge_confidence_score,
        dual_tool_floor_score=dual_tool_floor_score,
        confidence_gap_ratio=confidence_gap_ratio,
        contradiction_pressure_score=observation.contradiction_pressure_score,
        unresolved_gap_score=observation.unresolved_gap_score,
        config=config,
    )
    return ResearchSourceScraplingAgentReachConfidenceBridgeRow(
        row_index=row_index,
        observed_at=observation.observed_at,
        scrapling_confidence_score=scrapling_confidence_score,
        agent_reach_confidence_score=agent_reach_confidence_score,
        authority_alignment_score=observation.authority_alignment_score,
        freshness_score=observation.freshness_score,
        contradiction_pressure_score=observation.contradiction_pressure_score,
        unresolved_gap_score=observation.unresolved_gap_score,
        confidence_gap_ratio=confidence_gap_ratio,
        dual_tool_floor_score=dual_tool_floor_score,
        bridge_confidence_score=bridge_confidence_score,
        status=_status_from_reasons(reason_codes),
        reason_codes=reason_codes,
    )


def _bridge_confidence_score(
    *,
    scrapling_confidence_score: Decimal,
    agent_reach_confidence_score: Decimal,
    authority_alignment_score: Decimal,
    freshness_score: Decimal,
    config: ResearchSourceScraplingAgentReachConfidenceBridgeConfig,
) -> Decimal:
    tool_confidence_score = _average_probability(
        (scrapling_confidence_score, agent_reach_confidence_score),
    )
    return _normalize_probability(
        "bridge_confidence_score",
        tool_confidence_score * config.bridge_tool_confidence_weight
        + authority_alignment_score * config.bridge_authority_alignment_weight
        + freshness_score * config.bridge_freshness_weight,
    )


def _row_reason_codes(
    *,
    bridge_confidence_score: Decimal,
    dual_tool_floor_score: Decimal,
    confidence_gap_ratio: Decimal,
    contradiction_pressure_score: Decimal,
    unresolved_gap_score: Decimal,
    config: ResearchSourceScraplingAgentReachConfidenceBridgeConfig,
) -> tuple[str, ...]:
    block_reasons: list[str] = []
    if bridge_confidence_score < config.min_watch_bridge_confidence_score:
        block_reasons.append(BRIDGE_CONFIDENCE_BLOCK_REASON)
    if dual_tool_floor_score < config.min_watch_dual_tool_floor_score:
        block_reasons.append(DUAL_TOOL_FLOOR_BLOCK_REASON)
    if confidence_gap_ratio > config.max_watch_confidence_gap_ratio:
        block_reasons.append(CONFIDENCE_GAP_BLOCK_REASON)
    if contradiction_pressure_score > config.max_watch_contradiction_pressure_score:
        block_reasons.append(CONTRADICTION_BLOCK_REASON)
    if unresolved_gap_score > config.max_watch_unresolved_gap_score:
        block_reasons.append(UNRESOLVED_GAP_BLOCK_REASON)
    if block_reasons:
        return _normalize_reason_codes(tuple(block_reasons))

    watch_reasons: list[str] = []
    if bridge_confidence_score < config.min_pass_bridge_confidence_score:
        watch_reasons.append(BRIDGE_CONFIDENCE_WATCH_REASON)
    if dual_tool_floor_score < config.min_pass_dual_tool_floor_score:
        watch_reasons.append(DUAL_TOOL_FLOOR_WATCH_REASON)
    if confidence_gap_ratio > config.max_pass_confidence_gap_ratio:
        watch_reasons.append(CONFIDENCE_GAP_WATCH_REASON)
    if contradiction_pressure_score > config.max_pass_contradiction_pressure_score:
        watch_reasons.append(CONTRADICTION_WATCH_REASON)
    if unresolved_gap_score > config.max_pass_unresolved_gap_score:
        watch_reasons.append(UNRESOLVED_GAP_WATCH_REASON)
    return _normalize_reason_codes(tuple(watch_reasons))


def _status_from_reasons(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASON_CODES for reason_code in reason_codes):
        return STATUS_BLOCK
    if reason_codes:
        return STATUS_WATCH
    return STATUS_PASS


def _report_status(
    rows: tuple[ResearchSourceScraplingAgentReachConfidenceBridgeRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchSourceScraplingAgentReachConfidenceBridgeRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    detail_reasons: list[str] = []
    for row in rows:
        detail_reasons.extend(row.reason_codes)
    if detail_reasons:
        return _normalize_reason_codes(tuple(detail_reasons))
    return (PASS_REASON,)


def _reason_code_counts(
    rows: tuple[ResearchSourceScraplingAgentReachConfidenceBridgeRow, ...],
) -> tuple[ResearchSourceScraplingAgentReachConfidenceBridgeReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchSourceScraplingAgentReachConfidenceBridgeReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=Decimal("1.000000"),
            ),
        )
    report_reasons = _report_reason_codes(rows)
    counts = Counter(report_reasons)
    return tuple(
        ResearchSourceScraplingAgentReachConfidenceBridgeReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_from_int(counts[reason_code]),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if counts[reason_code] > 0
    )


def _validate_report_consistency(
    report: ResearchSourceScraplingAgentReachConfidenceBridgeReport,
) -> None:
    for row in report.rows:
        if row.observed_at > report.generated_at:
            raise ValueError("row observed_at must not be after generated_at")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be in canonical order")
    if tuple(row.row_index for row in report.rows) != tuple(
        _decimal_from_int(index) for index in range(1, len(report.rows) + 1)
    ):
        raise ValueError("row_index values must be sequential in canonical order")
    if report.observation_count != _decimal_from_int(len(report.rows)):
        raise ValueError("observation_count must match rows")
    if report.row_count != _decimal_from_int(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.average_scrapling_confidence_score != _average_probability(
        tuple(row.scrapling_confidence_score for row in report.rows),
    ):
        raise ValueError("average_scrapling_confidence_score must match rows")
    if report.average_agent_reach_confidence_score != _average_probability(
        tuple(row.agent_reach_confidence_score for row in report.rows),
    ):
        raise ValueError("average_agent_reach_confidence_score must match rows")
    if report.average_authority_alignment_score != _average_probability(
        tuple(row.authority_alignment_score for row in report.rows),
    ):
        raise ValueError("average_authority_alignment_score must match rows")
    if report.average_freshness_score != _average_probability(
        tuple(row.freshness_score for row in report.rows),
    ):
        raise ValueError("average_freshness_score must match rows")
    if report.average_bridge_confidence_score != _average_probability(
        tuple(row.bridge_confidence_score for row in report.rows),
    ):
        raise ValueError("average_bridge_confidence_score must match rows")
    if report.average_dual_tool_floor_score != _average_probability(
        tuple(row.dual_tool_floor_score for row in report.rows),
    ):
        raise ValueError("average_dual_tool_floor_score must match rows")
    if report.average_confidence_gap_ratio != _average_probability(
        tuple(row.confidence_gap_ratio for row in report.rows),
    ):
        raise ValueError("average_confidence_gap_ratio must match rows")
    if report.highest_confidence_gap_ratio != _max_probability(
        tuple(row.confidence_gap_ratio for row in report.rows),
    ):
        raise ValueError("highest_confidence_gap_ratio must match rows")
    if report.highest_contradiction_pressure_score != _max_probability(
        tuple(row.contradiction_pressure_score for row in report.rows),
    ):
        raise ValueError("highest_contradiction_pressure_score must match rows")
    if report.highest_unresolved_gap_score != _max_probability(
        tuple(row.unresolved_gap_score for row in report.rows),
    ):
        raise ValueError("highest_unresolved_gap_score must match rows")
    if report.pass_count != _status_count(report.rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _validate_row_derived_metrics(
    row: ResearchSourceScraplingAgentReachConfidenceBridgeRow,
) -> None:
    expected_confidence_gap_ratio = _normalize_probability(
        "confidence_gap_ratio",
        abs(row.scrapling_confidence_score - row.agent_reach_confidence_score),
    )
    if row.confidence_gap_ratio != expected_confidence_gap_ratio:
        raise ValueError(
            "confidence_gap_ratio must match scrapling and agent-reach confidence",
        )
    expected_dual_tool_floor_score = min(
        row.scrapling_confidence_score,
        row.agent_reach_confidence_score,
    )
    if row.dual_tool_floor_score != expected_dual_tool_floor_score:
        raise ValueError(
            "dual_tool_floor_score must match scrapling and agent-reach confidence",
        )


def _status_count(
    rows: tuple[ResearchSourceScraplingAgentReachConfidenceBridgeRow, ...],
    status: str,
) -> Decimal:
    return _decimal_from_int(sum(1 for row in rows if row.status == status))


def _average_probability(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _normalize_probability(
        "average_probability",
        sum(values, ZERO) / _decimal_from_int(len(values)),
    )


def _max_probability(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _normalize_probability("max_probability", max(values))


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
) -> tuple[ResearchSourceScraplingAgentReachConfidenceBridgeRow, ...]:
    if isinstance(rows, (str, bytes, dict)):
        raise ValueError("rows must be a tuple of confidence bridge rows")
    normalized = tuple(rows)  # type: ignore[arg-type]
    for row in normalized:
        _require_exact_type(row, ResearchSourceScraplingAgentReachConfidenceBridgeRow, "row")
        _require_hard_flags("row", row)
        _reject_unsafe_public_payload("row", row)
    return normalized


def _normalize_reason_code_counts(
    counts: object,
) -> tuple[ResearchSourceScraplingAgentReachConfidenceBridgeReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes, dict)):
        raise ValueError("reason_code_counts must be a tuple")
    normalized = tuple(counts)  # type: ignore[arg-type]
    for item in normalized:
        _require_exact_type(
            item,
            ResearchSourceScraplingAgentReachConfidenceBridgeReasonCodeCount,
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
    if value not in RESEARCH_SOURCE_SCRAPLING_AGENT_REACH_CONFIDENCE_BRIDGE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if PUBLIC_IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a safe public identifier")
    _reject_unsafe_public_string(field_name, value, key=False)


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
    if normalized != normalized.to_integral_value():
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
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
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
    report: ResearchSourceScraplingAgentReachConfidenceBridgeReport,
) -> None:
    _require_exact_type(report, ResearchSourceScraplingAgentReachConfidenceBridgeReport, "report")
    _require_hard_flags("report", report)
    expected_digest = research_source_scrapling_agent_reach_confidence_bridge_report_digest(
        report,
    )
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


def _validate_public_payload_schema(payload: dict[str, Any]) -> None:
    values = _require_exact_payload_fields(
        "payload",
        payload,
        ResearchSourceScraplingAgentReachConfidenceBridgeReport,
    )
    rows_value = values["rows"]
    if type(rows_value) is not list:
        raise ValueError("rows must be a JSON array")
    reason_code_counts_value = values["reason_code_counts"]
    if type(reason_code_counts_value) is not list:
        raise ValueError("reason_code_counts must be a JSON array")
    report = ResearchSourceScraplingAgentReachConfidenceBridgeReport(
        generated_at=_datetime_from_public_payload(
            "generated_at",
            values["generated_at"],
        ),
        config_version=_string_from_public_payload(
            "config_version",
            values["config_version"],
        ),
        observation_count=_decimal_from_public_payload(
            "observation_count",
            values["observation_count"],
        ),
        row_count=_decimal_from_public_payload("row_count", values["row_count"]),
        average_scrapling_confidence_score=_decimal_from_public_payload(
            "average_scrapling_confidence_score",
            values["average_scrapling_confidence_score"],
        ),
        average_agent_reach_confidence_score=_decimal_from_public_payload(
            "average_agent_reach_confidence_score",
            values["average_agent_reach_confidence_score"],
        ),
        average_authority_alignment_score=_decimal_from_public_payload(
            "average_authority_alignment_score",
            values["average_authority_alignment_score"],
        ),
        average_freshness_score=_decimal_from_public_payload(
            "average_freshness_score",
            values["average_freshness_score"],
        ),
        average_bridge_confidence_score=_decimal_from_public_payload(
            "average_bridge_confidence_score",
            values["average_bridge_confidence_score"],
        ),
        average_dual_tool_floor_score=_decimal_from_public_payload(
            "average_dual_tool_floor_score",
            values["average_dual_tool_floor_score"],
        ),
        average_confidence_gap_ratio=_decimal_from_public_payload(
            "average_confidence_gap_ratio",
            values["average_confidence_gap_ratio"],
        ),
        highest_confidence_gap_ratio=_decimal_from_public_payload(
            "highest_confidence_gap_ratio",
            values["highest_confidence_gap_ratio"],
        ),
        highest_contradiction_pressure_score=_decimal_from_public_payload(
            "highest_contradiction_pressure_score",
            values["highest_contradiction_pressure_score"],
        ),
        highest_unresolved_gap_score=_decimal_from_public_payload(
            "highest_unresolved_gap_score",
            values["highest_unresolved_gap_score"],
        ),
        pass_count=_decimal_from_public_payload("pass_count", values["pass_count"]),
        watch_count=_decimal_from_public_payload("watch_count", values["watch_count"]),
        block_count=_decimal_from_public_payload("block_count", values["block_count"]),
        status=_string_from_public_payload("status", values["status"]),
        reason_codes=_reason_codes_from_public_payload(
            "reason_codes",
            values["reason_codes"],
        ),
        reason_code_counts=tuple(
            _reason_code_count_from_public_payload(item)
            for item in reason_code_counts_value
        ),
        rows=tuple(_row_from_public_payload(item) for item in rows_value),
        derived_validation_digest=_string_from_public_payload(
            "derived_validation_digest",
            values["derived_validation_digest"],
        ),
        paper_only=_true_flag_from_public_payload(
            "paper_only",
            values["paper_only"],
        ),
        report_only=_true_flag_from_public_payload(
            "report_only",
            values["report_only"],
        ),
        readonly=_true_flag_from_public_payload("readonly", values["readonly"]),
    )
    if _json_ready(asdict(report)) != payload:
        raise ValueError("payload must use the canonical report schema")


def _row_from_public_payload(
    value: object,
) -> ResearchSourceScraplingAgentReachConfidenceBridgeRow:
    values = _require_exact_payload_fields(
        "row",
        value,
        ResearchSourceScraplingAgentReachConfidenceBridgeRow,
    )
    return ResearchSourceScraplingAgentReachConfidenceBridgeRow(
        row_index=_decimal_from_public_payload("row_index", values["row_index"]),
        observed_at=_datetime_from_public_payload("observed_at", values["observed_at"]),
        scrapling_confidence_score=_decimal_from_public_payload(
            "scrapling_confidence_score",
            values["scrapling_confidence_score"],
        ),
        agent_reach_confidence_score=_decimal_from_public_payload(
            "agent_reach_confidence_score",
            values["agent_reach_confidence_score"],
        ),
        authority_alignment_score=_decimal_from_public_payload(
            "authority_alignment_score",
            values["authority_alignment_score"],
        ),
        freshness_score=_decimal_from_public_payload(
            "freshness_score",
            values["freshness_score"],
        ),
        contradiction_pressure_score=_decimal_from_public_payload(
            "contradiction_pressure_score",
            values["contradiction_pressure_score"],
        ),
        unresolved_gap_score=_decimal_from_public_payload(
            "unresolved_gap_score",
            values["unresolved_gap_score"],
        ),
        confidence_gap_ratio=_decimal_from_public_payload(
            "confidence_gap_ratio",
            values["confidence_gap_ratio"],
        ),
        dual_tool_floor_score=_decimal_from_public_payload(
            "dual_tool_floor_score",
            values["dual_tool_floor_score"],
        ),
        bridge_confidence_score=_decimal_from_public_payload(
            "bridge_confidence_score",
            values["bridge_confidence_score"],
        ),
        status=_string_from_public_payload("status", values["status"]),
        reason_codes=_reason_codes_from_public_payload(
            "reason_codes",
            values["reason_codes"],
        ),
        paper_only=_true_flag_from_public_payload(
            "paper_only",
            values["paper_only"],
        ),
        report_only=_true_flag_from_public_payload(
            "report_only",
            values["report_only"],
        ),
        readonly=_true_flag_from_public_payload("readonly", values["readonly"]),
    )


def _reason_code_count_from_public_payload(
    value: object,
) -> ResearchSourceScraplingAgentReachConfidenceBridgeReasonCodeCount:
    values = _require_exact_payload_fields(
        "reason_code_count",
        value,
        ResearchSourceScraplingAgentReachConfidenceBridgeReasonCodeCount,
    )
    return ResearchSourceScraplingAgentReachConfidenceBridgeReasonCodeCount(
        reason_code=_string_from_public_payload(
            "reason_code",
            values["reason_code"],
        ),
        count=_decimal_from_public_payload("count", values["count"]),
        paper_only=_true_flag_from_public_payload(
            "paper_only",
            values["paper_only"],
        ),
        report_only=_true_flag_from_public_payload(
            "report_only",
            values["report_only"],
        ),
        readonly=_true_flag_from_public_payload("readonly", values["readonly"]),
    )


def _require_exact_payload_fields(
    label: str,
    value: object,
    expected_type: type[object],
) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError(f"{label} must be a JSON object")
    expected_fields = {field.name for field in fields(expected_type)}
    if set(value) != expected_fields:
        raise ValueError(f"{label} must contain exactly the supported fields")
    return value


def _decimal_from_public_payload(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        return Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc


def _datetime_from_public_payload(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime string") from exc
    return _as_utc(field_name, parsed)


def _string_from_public_payload(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _reason_codes_from_public_payload(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a JSON array")
    for item in value:
        if type(item) is not str:
            raise ValueError(f"{field_name} values must be strings")
    return tuple(value)


def _true_flag_from_public_payload(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _report_values_without_digest(
    report: ResearchSourceScraplingAgentReachConfidenceBridgeReport,
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


def _copy_json_object(value: Mapping[str, object]) -> dict[str, Any]:
    copied = _json_ready(value)
    if type(copied) is not dict:
        raise ValueError("payload must be a JSON object")
    return copied


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
        _reject_unsafe_public_string(current_path, value, key=False)


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS):
        raise ValueError(f"{path}.{key} contains unsafe public key text")


def _reject_unsafe_public_string(label: str, value: str, *, key: bool) -> None:
    fragments = UNSAFE_PUBLIC_KEY_FRAGMENTS if key else UNSAFE_PUBLIC_VALUE_FRAGMENTS
    lowered = value.lower()
    if any(fragment in lowered for fragment in fragments):
        raise ValueError(f"{label} contains unsafe public text")


def _validate_status_values_in_payload(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key == "status":
                _require_status("status", item)
            _validate_status_values_in_payload(item)
    elif isinstance(value, list):
        for item in value:
            _validate_status_values_in_payload(item)
