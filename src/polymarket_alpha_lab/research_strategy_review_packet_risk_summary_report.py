"""Report-only analyst review packet risk summary."""

from __future__ import annotations

from collections import Counter
from dataclasses import InitVar, asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any, Mapping, Sequence


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_REVIEW_PACKET_RISK_SUMMARY_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_REVIEW_PACKET_RISK_SUMMARY_STATUSES",
    "ResearchStrategyReviewPacketRiskInput",
    "ResearchStrategyReviewPacketRiskReasonCodeCount",
    "ResearchStrategyReviewPacketRiskSummaryConfig",
    "ResearchStrategyReviewPacketRiskSummaryReport",
    "ResearchStrategyReviewPacketRiskSummaryRow",
    "build_research_strategy_review_packet_risk_summary_report",
    "research_strategy_review_packet_risk_summary_report_digest",
    "research_strategy_review_packet_risk_summary_report_payload",
)


DEFAULT_RESEARCH_STRATEGY_REVIEW_PACKET_RISK_SUMMARY_REPORT_CONFIG_VERSION = (
    "research-strategy-review-packet-risk-summary-report-v0"
)
RESEARCH_STRATEGY_REVIEW_PACKET_RISK_SUMMARY_STATUSES = (
    "pass",
    "watch",
    "block",
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
REVIEW_STATE_PASS = "risk_summary_pass"
REVIEW_STATE_WATCH = "risk_summary_watch"
REVIEW_STATE_BLOCK = "risk_summary_block"

REASON_EMPTY_INPUT = "empty_input"
REASON_ANALYST_PACKET_SCOPE_READY = "analyst_packet_scope_ready"
REASON_MANUAL_REVIEW_REQUESTED = "manual_review_requested"
REASON_CAPACITY_REVIEW_REQUESTED = "capacity_review_requested"
REASON_EVIDENCE_GAP_BLOCK = "evidence_gap_block"
REASON_SOURCE_CONFLICT_BLOCK = "source_conflict_block"
REASON_MARKET_COST_PRESSURE_BLOCK = "market_cost_pressure_block"
REASON_LIQUIDITY_QUALITY_BLOCK = "liquidity_quality_block"
REASON_RESOLUTION_AMBIGUITY_BLOCK = "resolution_ambiguity_block"
REASON_TEAM_MEMORY_GAP_BLOCK = "team_memory_gap_block"
REASON_CAPACITY_PRESSURE_BLOCK = "capacity_pressure_block"
REASON_AGGREGATE_RISK_BLOCK = "aggregate_risk_block"
REASON_EVIDENCE_GAP_WATCH = "evidence_gap_watch"
REASON_SOURCE_CONFLICT_WATCH = "source_conflict_watch"
REASON_MARKET_COST_PRESSURE_WATCH = "market_cost_pressure_watch"
REASON_LIQUIDITY_QUALITY_WATCH = "liquidity_quality_watch"
REASON_RESOLUTION_AMBIGUITY_WATCH = "resolution_ambiguity_watch"
REASON_TEAM_MEMORY_GAP_WATCH = "team_memory_gap_watch"
REASON_CAPACITY_PRESSURE_WATCH = "capacity_pressure_watch"
REASON_AGGREGATE_RISK_WATCH = "aggregate_risk_watch"
REASON_REVIEW_PACKET_RISK_SUMMARY_PASS = "review_packet_risk_summary_pass"

UPSTREAM_REASON_CODES = (
    REASON_MANUAL_REVIEW_REQUESTED,
    REASON_CAPACITY_REVIEW_REQUESTED,
    REASON_ANALYST_PACKET_SCOPE_READY,
)
GENERATED_REASON_CODES = (
    REASON_EVIDENCE_GAP_BLOCK,
    REASON_SOURCE_CONFLICT_BLOCK,
    REASON_MARKET_COST_PRESSURE_BLOCK,
    REASON_LIQUIDITY_QUALITY_BLOCK,
    REASON_RESOLUTION_AMBIGUITY_BLOCK,
    REASON_TEAM_MEMORY_GAP_BLOCK,
    REASON_CAPACITY_PRESSURE_BLOCK,
    REASON_AGGREGATE_RISK_BLOCK,
    REASON_EVIDENCE_GAP_WATCH,
    REASON_SOURCE_CONFLICT_WATCH,
    REASON_MARKET_COST_PRESSURE_WATCH,
    REASON_LIQUIDITY_QUALITY_WATCH,
    REASON_RESOLUTION_AMBIGUITY_WATCH,
    REASON_TEAM_MEMORY_GAP_WATCH,
    REASON_CAPACITY_PRESSURE_WATCH,
    REASON_AGGREGATE_RISK_WATCH,
    REASON_REVIEW_PACKET_RISK_SUMMARY_PASS,
)
ALL_REASON_CODES = (
    *UPSTREAM_REASON_CODES,
    *GENERATED_REASON_CODES,
    REASON_EMPTY_INPUT,
)
BLOCK_REASON_CODES = frozenset(
    (
        REASON_EVIDENCE_GAP_BLOCK,
        REASON_SOURCE_CONFLICT_BLOCK,
        REASON_MARKET_COST_PRESSURE_BLOCK,
        REASON_LIQUIDITY_QUALITY_BLOCK,
        REASON_RESOLUTION_AMBIGUITY_BLOCK,
        REASON_TEAM_MEMORY_GAP_BLOCK,
        REASON_CAPACITY_PRESSURE_BLOCK,
        REASON_AGGREGATE_RISK_BLOCK,
    ),
)
WATCH_REASON_CODES = frozenset(
    (
        REASON_EVIDENCE_GAP_WATCH,
        REASON_SOURCE_CONFLICT_WATCH,
        REASON_MARKET_COST_PRESSURE_WATCH,
        REASON_LIQUIDITY_QUALITY_WATCH,
        REASON_RESOLUTION_AMBIGUITY_WATCH,
        REASON_TEAM_MEMORY_GAP_WATCH,
        REASON_CAPACITY_PRESSURE_WATCH,
        REASON_AGGREGATE_RISK_WATCH,
    ),
)

QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DIGEST_FIELD = "derived_validation_digest"
ROW_DIGEST_FIELD = "validation_digest"
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
PRIVATE_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
UNSAFE_PUBLIC_FRAGMENTS = (
    "can" "didate" "_" "id",
    "mar" "ket" "_" "id",
    "mar" "ket" "_" "s" "lug",
    "s" "lug",
    "ques" "tion",
    "source" "_" "u" "rl",
    "source" "-" "u" "rl",
    "source" " " "u" "rl",
    "source" "_" "text",
    "source" "-" "text",
    "source" " " "text",
    "d" "sn",
    "data" "base",
    "ta" "ble",
    "to" "ken",
    "wal" "let",
    "au" "th",
    "or" "der",
    "tr" "ade",
    "po" "sition",
    "siz" "ing",
    "b" "uy",
    "se" "ll",
    "reco" "mmend",
    "private" "_" "key",
    "private" " " "key",
    "http" ":" "/" "/",
    "https" ":" "/" "/",
    ":" "/" "/",
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchStrategyReviewPacketRiskSummaryConfig(_FinalDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_REVIEW_PACKET_RISK_SUMMARY_REPORT_CONFIG_VERSION
    )
    max_pass_dimension_risk_score: Decimal = Decimal("0.250000")
    max_watch_dimension_risk_score: Decimal = Decimal("0.500000")
    max_pass_aggregate_risk_score: Decimal = Decimal("0.250000")
    max_watch_aggregate_risk_score: Decimal = Decimal("0.500000")
    min_pass_liquidity_quality_score: Decimal = Decimal("0.750000")
    min_watch_liquidity_quality_score: Decimal = Decimal("0.500000")
    evidence_gap_weight: Decimal = Decimal("0.180000")
    source_conflict_weight: Decimal = Decimal("0.160000")
    market_cost_pressure_weight: Decimal = Decimal("0.150000")
    liquidity_quality_weight: Decimal = Decimal("0.140000")
    resolution_ambiguity_weight: Decimal = Decimal("0.150000")
    team_memory_gap_weight: Decimal = Decimal("0.120000")
    capacity_pressure_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyReviewPacketRiskSummaryConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_REVIEW_PACKET_RISK_SUMMARY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_pass_dimension_risk_score",
            "max_watch_dimension_risk_score",
            "max_pass_aggregate_risk_score",
            "max_watch_aggregate_risk_score",
            "min_pass_liquidity_quality_score",
            "min_watch_liquidity_quality_score",
            "evidence_gap_weight",
            "source_conflict_weight",
            "market_cost_pressure_weight",
            "liquidity_quality_weight",
            "resolution_ambiguity_weight",
            "team_memory_gap_weight",
            "capacity_pressure_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.max_pass_dimension_risk_score > self.max_watch_dimension_risk_score:
            raise ValueError(
                "max_pass_dimension_risk_score must not exceed "
                "max_watch_dimension_risk_score",
            )
        if self.max_pass_aggregate_risk_score > self.max_watch_aggregate_risk_score:
            raise ValueError(
                "max_pass_aggregate_risk_score must not exceed "
                "max_watch_aggregate_risk_score",
            )
        if self.min_pass_liquidity_quality_score < self.min_watch_liquidity_quality_score:
            raise ValueError(
                "min_pass_liquidity_quality_score must be at least "
                "min_watch_liquidity_quality_score",
            )
        weight_sum = _quantize(
            self.evidence_gap_weight
            + self.source_conflict_weight
            + self.market_cost_pressure_weight
            + self.liquidity_quality_weight
            + self.resolution_ambiguity_weight
            + self.team_memory_gap_weight
            + self.capacity_pressure_weight,
        )
        if weight_sum != ONE:
            raise ValueError("weights must sum to one")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyReviewPacketRiskInput(_FinalDataclass):
    internal_packet_ref: str
    evidence_gap_score: Decimal
    source_conflict_score: Decimal
    market_cost_pressure_score: Decimal
    liquidity_quality_score: Decimal
    resolution_ambiguity_score: Decimal
    team_memory_gap_score: Decimal
    capacity_pressure_score: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyReviewPacketRiskInput, "packet")
        object.__setattr__(
            self,
            "internal_packet_ref",
            _require_private_ref("internal_packet_ref", self.internal_packet_ref),
        )
        for field_name in (
            "evidence_gap_score",
            "source_conflict_score",
            "market_cost_pressure_score",
            "liquidity_quality_score",
            "resolution_ambiguity_score",
            "team_memory_gap_score",
            "capacity_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                self.reason_codes,
                allowed=UPSTREAM_REASON_CODES,
                field_name="reason_codes",
                require_nonempty=True,
            ),
        )
        _require_hard_flags("packet", self)


@dataclass(frozen=True)
class ResearchStrategyReviewPacketRiskSummaryRow(_FinalDataclass):
    row_number: Decimal
    review_packet_digest: str
    evidence_gap_score: Decimal
    source_conflict_score: Decimal
    market_cost_pressure_score: Decimal
    liquidity_quality_score: Decimal
    liquidity_risk_score: Decimal
    resolution_ambiguity_score: Decimal
    team_memory_gap_score: Decimal
    capacity_pressure_score: Decimal
    aggregate_risk_score: Decimal
    observed_at: datetime
    status: str
    review_state: str
    reason_codes: tuple[str, ...]
    validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[ResearchStrategyReviewPacketRiskSummaryConfig | None] = (
        None
    )

    def __post_init__(
        self,
        validation_config: ResearchStrategyReviewPacketRiskSummaryConfig | None,
    ) -> None:
        _require_exact_type(self, ResearchStrategyReviewPacketRiskSummaryRow, "row")
        object.__setattr__(
            self,
            "row_number",
            _require_nonnegative_count_decimal("row_number", self.row_number),
        )
        object.__setattr__(
            self,
            "review_packet_digest",
            _require_private_digest("review_packet_digest", self.review_packet_digest),
        )
        for field_name in (
            "evidence_gap_score",
            "source_conflict_score",
            "market_cost_pressure_score",
            "liquidity_quality_score",
            "liquidity_risk_score",
            "resolution_ambiguity_score",
            "team_memory_gap_score",
            "capacity_pressure_score",
            "aggregate_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_status("status", self.status)
        _require_review_state("review_state", self.review_state)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                self.reason_codes,
                allowed=ALL_REASON_CODES,
                field_name="reason_codes",
                require_nonempty=True,
            ),
        )
        _validate_row(self, validation_config)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)
        expected_digest = _row_digest(self)
        if self.validation_digest == "":
            object.__setattr__(self, ROW_DIGEST_FIELD, expected_digest)
        elif self.validation_digest != expected_digest:
            raise ValueError("validation_digest mismatch")
        _require_digest(ROW_DIGEST_FIELD, self.validation_digest)


@dataclass(frozen=True)
class ResearchStrategyReviewPacketRiskReasonCodeCount(_FinalDataclass):
    reason_code: str
    count: Decimal
    packet_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyReviewPacketRiskReasonCodeCount, "count")
        _require_reason_code("reason_code", self.reason_code, ALL_REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "packet_ratio",
            _require_ratio_decimal("packet_ratio", self.packet_ratio),
        )
        _require_hard_flags("count", self)
        _reject_unsafe_public_payload("count", self)


@dataclass(frozen=True)
class ResearchStrategyReviewPacketRiskSummaryReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    status: str
    packet_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_aggregate_risk_score: Decimal
    max_aggregate_risk_score: Decimal
    max_evidence_gap_score: Decimal
    max_source_conflict_score: Decimal
    max_market_cost_pressure_score: Decimal
    min_liquidity_quality_score: Decimal
    max_resolution_ambiguity_score: Decimal
    max_team_memory_gap_score: Decimal
    max_capacity_pressure_score: Decimal
    rows: tuple[ResearchStrategyReviewPacketRiskSummaryRow, ...]
    reason_code_counts: tuple[ResearchStrategyReviewPacketRiskReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyReviewPacketRiskSummaryReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_REVIEW_PACKET_RISK_SUMMARY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in ("packet_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_aggregate_risk_score",
            "max_aggregate_risk_score",
            "max_evidence_gap_score",
            "max_source_conflict_score",
            "max_market_cost_pressure_score",
            "min_liquidity_quality_score",
            "max_resolution_ambiguity_score",
            "max_team_memory_gap_score",
            "max_capacity_pressure_score",
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
            _normalize_reason_codes(
                self.reason_codes,
                allowed=ALL_REASON_CODES,
                field_name="reason_codes",
                require_nonempty=True,
            ),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, DIGEST_FIELD, expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest mismatch")
        _require_digest(DIGEST_FIELD, self.derived_validation_digest)

    @property
    def payload(self) -> dict[str, object]:
        return research_strategy_review_packet_risk_summary_report_payload(self)


def build_research_strategy_review_packet_risk_summary_report(
    packets: Sequence[ResearchStrategyReviewPacketRiskInput],
    *,
    config: ResearchStrategyReviewPacketRiskSummaryConfig | None = None,
    generated_at: datetime,
) -> ResearchStrategyReviewPacketRiskSummaryReport:
    cfg = config or ResearchStrategyReviewPacketRiskSummaryConfig()
    if type(cfg) is not ResearchStrategyReviewPacketRiskSummaryConfig:
        raise ValueError("config must be a ResearchStrategyReviewPacketRiskSummaryConfig")
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    normalized_packets = _normalize_packets(packets)
    for item in normalized_packets:
        if item.observed_at > report_time:
            raise ValueError("observed_at must not be after generated_at")

    sortable_rows = tuple(_row_parts(item, cfg) for item in normalized_packets)
    rows = tuple(
        _row_from_parts(index, parts, cfg)
        for index, parts in enumerate(sorted(sortable_rows, key=_parts_sort_key), start=1)
    )
    if rows:
        reason_code_counts = _reason_code_counts(rows)
        reason_codes = tuple(item.reason_code for item in reason_code_counts)
    else:
        reason_code_counts = (
            ResearchStrategyReviewPacketRiskReasonCodeCount(
                reason_code=REASON_EMPTY_INPUT,
                count=ONE,
                packet_ratio=ONE,
            ),
        )
        reason_codes = (REASON_EMPTY_INPUT,)

    values: dict[str, object] = {
        "generated_at": report_time,
        "config_version": cfg.config_version,
        "status": _report_status(rows),
        "packet_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, STATUS_PASS)),
        "watch_count": _decimal_count(_status_count(rows, STATUS_WATCH)),
        "block_count": _decimal_count(_status_count(rows, STATUS_BLOCK)),
        "average_aggregate_risk_score": _average_ratio(
            tuple(row.aggregate_risk_score for row in rows),
        ),
        "max_aggregate_risk_score": max(
            (row.aggregate_risk_score for row in rows),
            default=ZERO,
        ),
        "max_evidence_gap_score": max(
            (row.evidence_gap_score for row in rows),
            default=ZERO,
        ),
        "max_source_conflict_score": max(
            (row.source_conflict_score for row in rows),
            default=ZERO,
        ),
        "max_market_cost_pressure_score": max(
            (row.market_cost_pressure_score for row in rows),
            default=ZERO,
        ),
        "min_liquidity_quality_score": min(
            (row.liquidity_quality_score for row in rows),
            default=ZERO,
        ),
        "max_resolution_ambiguity_score": max(
            (row.resolution_ambiguity_score for row in rows),
            default=ZERO,
        ),
        "max_team_memory_gap_score": max(
            (row.team_memory_gap_score for row in rows),
            default=ZERO,
        ),
        "max_capacity_pressure_score": max(
            (row.capacity_pressure_score for row in rows),
            default=ZERO,
        ),
        "rows": rows,
        "reason_code_counts": reason_code_counts,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyReviewPacketRiskSummaryReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_strategy_review_packet_risk_summary_report_payload(
    value: ResearchStrategyReviewPacketRiskSummaryReport | dict[str, object],
) -> dict[str, object]:
    if type(value) is ResearchStrategyReviewPacketRiskSummaryReport:
        _require_hard_flags("report", value)
        payload = _report_payload(value)
    elif type(value) is dict:
        payload = _copy_json_object(value)
    else:
        raise ValueError(
            "value must be a ResearchStrategyReviewPacketRiskSummaryReport or dict",
        )
    _validate_payload_statuses(payload)
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_payload_row_digests(payload)
    _validate_payload_digest(payload)
    return payload


def research_strategy_review_packet_risk_summary_report_digest(
    value: ResearchStrategyReviewPacketRiskSummaryReport | dict[str, object],
) -> dict[str, object]:
    payload = research_strategy_review_packet_risk_summary_report_payload(value)
    return {
        key: item
        for key, item in payload.items()
        if key not in ("rows", "reason_code_counts", "reason_codes")
    }


def _row_parts(
    item: ResearchStrategyReviewPacketRiskInput,
    config: ResearchStrategyReviewPacketRiskSummaryConfig,
) -> dict[str, object]:
    liquidity_risk_score = _inverse_ratio(item.liquidity_quality_score)
    aggregate_risk_score = _aggregate_risk_score(
        evidence_gap_score=item.evidence_gap_score,
        source_conflict_score=item.source_conflict_score,
        market_cost_pressure_score=item.market_cost_pressure_score,
        liquidity_risk_score=liquidity_risk_score,
        resolution_ambiguity_score=item.resolution_ambiguity_score,
        team_memory_gap_score=item.team_memory_gap_score,
        capacity_pressure_score=item.capacity_pressure_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        item,
        liquidity_risk_score=liquidity_risk_score,
        aggregate_risk_score=aggregate_risk_score,
        config=config,
    )
    status = _row_status(reason_codes)
    return {
        "review_packet_digest": _private_ref_digest(item.internal_packet_ref),
        "evidence_gap_score": item.evidence_gap_score,
        "source_conflict_score": item.source_conflict_score,
        "market_cost_pressure_score": item.market_cost_pressure_score,
        "liquidity_quality_score": item.liquidity_quality_score,
        "liquidity_risk_score": liquidity_risk_score,
        "resolution_ambiguity_score": item.resolution_ambiguity_score,
        "team_memory_gap_score": item.team_memory_gap_score,
        "capacity_pressure_score": item.capacity_pressure_score,
        "aggregate_risk_score": aggregate_risk_score,
        "observed_at": item.observed_at,
        "status": status,
        "review_state": _review_state(status),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_from_parts(
    index: int,
    parts: Mapping[str, object],
    config: ResearchStrategyReviewPacketRiskSummaryConfig,
) -> ResearchStrategyReviewPacketRiskSummaryRow:
    return ResearchStrategyReviewPacketRiskSummaryRow(
        row_number=_decimal_count(index),
        validation_config=config,
        **parts,
    )


def _parts_sort_key(parts: Mapping[str, object]) -> tuple[Decimal, Decimal, str]:
    status = parts["status"]
    if status == STATUS_BLOCK:
        status_rank = Decimal("0.000000")
    elif status == STATUS_WATCH:
        status_rank = Decimal("1.000000")
    else:
        status_rank = Decimal("2.000000")
    aggregate_rank = ONE - _require_ratio_decimal(
        "aggregate_risk_score",
        parts["aggregate_risk_score"],
    )
    digest = _require_private_digest(
        "review_packet_digest",
        parts["review_packet_digest"],
    )
    return (status_rank, aggregate_rank, digest)


def _row_reason_codes(
    item: ResearchStrategyReviewPacketRiskInput,
    *,
    liquidity_risk_score: Decimal,
    aggregate_risk_score: Decimal,
    config: ResearchStrategyReviewPacketRiskSummaryConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = list(item.reason_codes)
    _append_risk_reason(
        reason_codes,
        value=item.evidence_gap_score,
        block_reason=REASON_EVIDENCE_GAP_BLOCK,
        watch_reason=REASON_EVIDENCE_GAP_WATCH,
        config=config,
    )
    _append_risk_reason(
        reason_codes,
        value=item.source_conflict_score,
        block_reason=REASON_SOURCE_CONFLICT_BLOCK,
        watch_reason=REASON_SOURCE_CONFLICT_WATCH,
        config=config,
    )
    _append_risk_reason(
        reason_codes,
        value=item.market_cost_pressure_score,
        block_reason=REASON_MARKET_COST_PRESSURE_BLOCK,
        watch_reason=REASON_MARKET_COST_PRESSURE_WATCH,
        config=config,
    )
    _append_liquidity_reason(reason_codes, item.liquidity_quality_score, config)
    _append_risk_reason(
        reason_codes,
        value=item.resolution_ambiguity_score,
        block_reason=REASON_RESOLUTION_AMBIGUITY_BLOCK,
        watch_reason=REASON_RESOLUTION_AMBIGUITY_WATCH,
        config=config,
    )
    _append_risk_reason(
        reason_codes,
        value=item.team_memory_gap_score,
        block_reason=REASON_TEAM_MEMORY_GAP_BLOCK,
        watch_reason=REASON_TEAM_MEMORY_GAP_WATCH,
        config=config,
    )
    _append_risk_reason(
        reason_codes,
        value=item.capacity_pressure_score,
        block_reason=REASON_CAPACITY_PRESSURE_BLOCK,
        watch_reason=REASON_CAPACITY_PRESSURE_WATCH,
        config=config,
    )
    if aggregate_risk_score > config.max_watch_aggregate_risk_score:
        reason_codes.append(REASON_AGGREGATE_RISK_BLOCK)
    elif aggregate_risk_score > config.max_pass_aggregate_risk_score:
        reason_codes.append(REASON_AGGREGATE_RISK_WATCH)
    if not any(reason in BLOCK_REASON_CODES or reason in WATCH_REASON_CODES for reason in reason_codes):
        reason_codes.append(REASON_REVIEW_PACKET_RISK_SUMMARY_PASS)
    return _normalize_reason_codes(
        tuple(reason_codes),
        allowed=ALL_REASON_CODES,
        field_name="reason_codes",
        require_nonempty=True,
    )


def _append_risk_reason(
    reason_codes: list[str],
    *,
    value: Decimal,
    block_reason: str,
    watch_reason: str,
    config: ResearchStrategyReviewPacketRiskSummaryConfig,
) -> None:
    if value > config.max_watch_dimension_risk_score:
        reason_codes.append(block_reason)
    elif value > config.max_pass_dimension_risk_score:
        reason_codes.append(watch_reason)


def _append_liquidity_reason(
    reason_codes: list[str],
    value: Decimal,
    config: ResearchStrategyReviewPacketRiskSummaryConfig,
) -> None:
    if value < config.min_watch_liquidity_quality_score:
        reason_codes.append(REASON_LIQUIDITY_QUALITY_BLOCK)
    elif value < config.min_pass_liquidity_quality_score:
        reason_codes.append(REASON_LIQUIDITY_QUALITY_WATCH)


def _aggregate_risk_score(
    *,
    evidence_gap_score: Decimal,
    source_conflict_score: Decimal,
    market_cost_pressure_score: Decimal,
    liquidity_risk_score: Decimal,
    resolution_ambiguity_score: Decimal,
    team_memory_gap_score: Decimal,
    capacity_pressure_score: Decimal,
    config: ResearchStrategyReviewPacketRiskSummaryConfig,
) -> Decimal:
    return _quantize(
        evidence_gap_score * config.evidence_gap_weight
        + source_conflict_score * config.source_conflict_weight
        + market_cost_pressure_score * config.market_cost_pressure_weight
        + liquidity_risk_score * config.liquidity_quality_weight
        + resolution_ambiguity_score * config.resolution_ambiguity_weight
        + team_memory_gap_score * config.team_memory_gap_weight
        + capacity_pressure_score * config.capacity_pressure_weight,
    )


def _validate_row(
    row: ResearchStrategyReviewPacketRiskSummaryRow,
    config: ResearchStrategyReviewPacketRiskSummaryConfig | None,
) -> None:
    if row.liquidity_risk_score != _inverse_ratio(row.liquidity_quality_score):
        raise ValueError("liquidity_risk_score must match liquidity_quality_score")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.review_state != _review_state(row.status):
        raise ValueError("review_state must match status")
    if config is not None:
        expected_aggregate = _aggregate_risk_score(
            evidence_gap_score=row.evidence_gap_score,
            source_conflict_score=row.source_conflict_score,
            market_cost_pressure_score=row.market_cost_pressure_score,
            liquidity_risk_score=row.liquidity_risk_score,
            resolution_ambiguity_score=row.resolution_ambiguity_score,
            team_memory_gap_score=row.team_memory_gap_score,
            capacity_pressure_score=row.capacity_pressure_score,
            config=config,
        )
        if row.aggregate_risk_score != expected_aggregate:
            raise ValueError("aggregate_risk_score must match weighted inputs")


def _validate_report(report: ResearchStrategyReviewPacketRiskSummaryReport) -> None:
    if report.packet_count != _decimal_count(len(report.rows)):
        raise ValueError("packet_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, STATUS_PASS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, STATUS_WATCH)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, STATUS_BLOCK)):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.average_aggregate_risk_score != _average_ratio(
        tuple(row.aggregate_risk_score for row in report.rows),
    ):
        raise ValueError("average_aggregate_risk_score must match rows")
    if report.max_aggregate_risk_score != max(
        (row.aggregate_risk_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_aggregate_risk_score must match rows")
    if report.max_evidence_gap_score != max(
        (row.evidence_gap_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_evidence_gap_score must match rows")
    if report.max_source_conflict_score != max(
        (row.source_conflict_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_source_conflict_score must match rows")
    if report.max_market_cost_pressure_score != max(
        (row.market_cost_pressure_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_market_cost_pressure_score must match rows")
    if report.min_liquidity_quality_score != min(
        (row.liquidity_quality_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("min_liquidity_quality_score must match rows")
    if report.max_resolution_ambiguity_score != max(
        (row.resolution_ambiguity_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_resolution_ambiguity_score must match rows")
    if report.max_team_memory_gap_score != max(
        (row.team_memory_gap_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_team_memory_gap_score must match rows")
    if report.max_capacity_pressure_score != max(
        (row.capacity_pressure_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_capacity_pressure_score must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        if not (
            not report.rows
            and report.reason_code_counts
            == (
                ResearchStrategyReviewPacketRiskReasonCodeCount(
                    reason_code=REASON_EMPTY_INPUT,
                    count=ONE,
                    packet_ratio=ONE,
                ),
            )
        ):
            raise ValueError("reason_code_counts must match rows")
    expected_reason_codes = tuple(item.reason_code for item in report.reason_code_counts)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match reason_code_counts")


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason in BLOCK_REASON_CODES for reason in reason_codes):
        return STATUS_BLOCK
    if any(reason in WATCH_REASON_CODES for reason in reason_codes):
        return STATUS_WATCH
    return STATUS_PASS


def _review_state(status: str) -> str:
    if status == STATUS_BLOCK:
        return REVIEW_STATE_BLOCK
    if status == STATUS_WATCH:
        return REVIEW_STATE_WATCH
    return REVIEW_STATE_PASS


def _report_status(rows: tuple[ResearchStrategyReviewPacketRiskSummaryRow, ...]) -> str:
    if not rows or any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _reason_code_counts(
    rows: tuple[ResearchStrategyReviewPacketRiskSummaryRow, ...],
) -> tuple[ResearchStrategyReviewPacketRiskReasonCodeCount, ...]:
    if not rows:
        return ()
    counts = Counter(reason for row in rows for reason in row.reason_codes)
    total = _decimal_count(len(rows))
    return tuple(
        ResearchStrategyReviewPacketRiskReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
            packet_ratio=_ratio(_decimal_count(counts[reason_code]), total),
        )
        for reason_code in ALL_REASON_CODES
        if reason_code in counts
    )


def _status_count(
    rows: tuple[ResearchStrategyReviewPacketRiskSummaryRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_packets(
    packets: Sequence[ResearchStrategyReviewPacketRiskInput],
) -> tuple[ResearchStrategyReviewPacketRiskInput, ...]:
    if type(packets) not in (list, tuple):
        raise ValueError("packets must be a list or tuple")
    normalized = tuple(packets)
    for item in normalized:
        if type(item) is not ResearchStrategyReviewPacketRiskInput:
            raise ValueError(
                "packets must contain ResearchStrategyReviewPacketRiskInput values",
            )
        _require_hard_flags("packet", item)
    return normalized


def _normalize_rows(
    rows: tuple[ResearchStrategyReviewPacketRiskSummaryRow, ...],
) -> tuple[ResearchStrategyReviewPacketRiskSummaryRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchStrategyReviewPacketRiskSummaryRow:
            raise ValueError("rows must contain ResearchStrategyReviewPacketRiskSummaryRow")
        _require_hard_flags("row", row)
    if tuple(sorted(normalized, key=_row_sort_key)) != normalized:
        raise ValueError("rows must be sorted deterministically")
    return normalized


def _normalize_reason_code_counts(
    values: tuple[ResearchStrategyReviewPacketRiskReasonCodeCount, ...],
) -> tuple[ResearchStrategyReviewPacketRiskReasonCodeCount, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized = tuple(values)
    for item in normalized:
        if type(item) is not ResearchStrategyReviewPacketRiskReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyReviewPacketRiskReasonCodeCount values",
            )
        _require_hard_flags("count", item)
    if tuple(sorted(normalized, key=_reason_count_sort_key)) != normalized:
        raise ValueError("reason_code_counts must be sorted deterministically")
    return normalized


def _normalize_reason_codes(
    values: tuple[str, ...],
    *,
    allowed: tuple[str, ...],
    field_name: str,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if type(values) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    normalized: list[str] = []
    for item in values:
        _require_reason_code(field_name, item, allowed)
        if item not in normalized:
            normalized.append(item)
    if require_nonempty and not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(item for item in allowed if item in normalized)


def _row_sort_key(row: ResearchStrategyReviewPacketRiskSummaryRow) -> tuple[Decimal, Decimal, str]:
    return _parts_sort_key(
        {
            "status": row.status,
            "aggregate_risk_score": row.aggregate_risk_score,
            "review_packet_digest": row.review_packet_digest,
        },
    )


def _reason_count_sort_key(
    item: ResearchStrategyReviewPacketRiskReasonCodeCount,
) -> tuple[Decimal, str]:
    for index, reason_code in enumerate(ALL_REASON_CODES):
        if reason_code == item.reason_code:
            return (_decimal_count(index), reason_code)
    return (_decimal_count(len(ALL_REASON_CODES)), item.reason_code)


def _report_payload(report: ResearchStrategyReviewPacketRiskSummaryReport) -> dict[str, object]:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    return payload


def _row_payload(row: ResearchStrategyReviewPacketRiskSummaryRow) -> dict[str, object]:
    payload = _json_ready(asdict(row))
    if type(payload) is not dict:
        raise ValueError("row payload must be a dict")
    _reject_unsafe_public_payload("row payload", payload, allow_json_containers=True)
    return payload


def _report_digest(report: ResearchStrategyReviewPacketRiskSummaryReport) -> str:
    return _report_digest_from_values(asdict(report))


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a dict")
    payload.pop(DIGEST_FIELD, None)
    return _sha256_json(payload)


def _row_digest(row: ResearchStrategyReviewPacketRiskSummaryRow) -> str:
    payload = _row_payload(row)
    payload.pop(ROW_DIGEST_FIELD, None)
    return _sha256_json(payload)


def _private_ref_digest(value: str) -> str:
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()


def _sha256_json(payload: Mapping[str, object]) -> str:
    rendered = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return sha256(rendered.encode("utf-8")).hexdigest()


def _validate_payload_statuses(payload: Mapping[str, object]) -> None:
    status = payload["status"]
    if status not in RESEARCH_STRATEGY_REVIEW_PACKET_RISK_SUMMARY_STATUSES:
        raise ValueError("status must be pass, watch, or block")
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain dict values")
        row_status = row["status"]
        if row_status not in RESEARCH_STRATEGY_REVIEW_PACKET_RISK_SUMMARY_STATUSES:
            raise ValueError("status must be pass, watch, or block")


def _validate_payload_row_digests(payload: Mapping[str, object]) -> None:
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain dict values")
        expected = _sha256_json(
            {
                key: item
                for key, item in row.items()
                if key != ROW_DIGEST_FIELD
            },
        )
        if row[ROW_DIGEST_FIELD] != expected:
            raise ValueError("validation_digest mismatch")


def _validate_payload_digest(payload: Mapping[str, object]) -> None:
    expected = _sha256_json(
        {
            key: item
            for key, item in payload.items()
            if key != DIGEST_FIELD
        },
    )
    if payload[DIGEST_FIELD] != expected:
        raise ValueError("derived_validation_digest mismatch")


def _copy_json_object(value: Mapping[str, object]) -> dict[str, object]:
    rendered = json.dumps(value, sort_keys=True, allow_nan=False)
    loaded = json.loads(rendered)
    if type(loaded) is not dict:
        raise ValueError("payload must be a dict")
    return loaded


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal or not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("datetime value must not be subclassed")
        if value.tzinfo is None:
            raise ValueError("datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, (str, bool)):
        return value
    if isinstance(value, int):
        raise ValueError("JSON value must not be an int")
    if isinstance(value, dict):
        output: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            output[key] = _json_ready(item)
        return output
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    payload: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(payload) and not isinstance(payload, type):
        _reject_unsafe_public_payload(
            label,
            asdict(payload),
            allow_json_containers=True,
        )
        return
    if isinstance(payload, Mapping):
        if not allow_json_containers:
            raise ValueError(f"unsafe public payload container in {label}")
        for key, item in payload.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_string(label, key, is_key=True)
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=True,
            )
        return
    if isinstance(payload, (list, tuple)):
        if not allow_json_containers:
            raise ValueError(f"unsafe public payload container in {label}")
        for item in payload:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=True,
            )
        return
    if isinstance(payload, str):
        _reject_unsafe_public_string(label, payload, is_key=False)


def _reject_unsafe_public_string(label: str, value: str, *, is_key: bool) -> None:
    normalized = value.casefold()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        if is_key:
            raise ValueError(f"unsafe public field in {label}: {value}")
        raise ValueError(f"unsafe public value in {label}: {value}")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise TypeError(f"{label} must be {expected_type.__name__}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value, is_key=False)
    return value


def _require_private_ref(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() == "":
        raise ValueError(f"{field_name} must not be blank")
    return value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal")
    normalized = _quantize(value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal")
    normalized = _quantize(value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_reason_code(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must contain strings")
    if value not in allowed:
        raise ValueError(f"{field_name} contains unsupported reason code")


def _require_status(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or value not in RESEARCH_STRATEGY_REVIEW_PACKET_RISK_SUMMARY_STATUSES
    ):
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_review_state(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or value not in (REVIEW_STATE_PASS, REVIEW_STATE_WATCH, REVIEW_STATE_BLOCK)
    ):
        raise ValueError(f"{field_name} must be a supported review state")


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str or DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _require_private_digest(field_name: str, value: object) -> str:
    if type(value) is not str or PRIVATE_DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a private sha256 digest")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _inverse_ratio(value: Decimal) -> Decimal:
    return _quantize(ONE - value)


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _ratio(sum(values, ZERO), _decimal_count(len(values)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANT, rounding=ROUND_HALF_UP)
