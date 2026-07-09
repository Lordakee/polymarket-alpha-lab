"""Report-only source resolution evidence-chain latency checks."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_SOURCE_RESOLUTION_EVIDENCE_CHAIN_LATENCY_REPORT_CONFIG_VERSION = (
    "research-source-resolution-evidence-chain-latency-report-v0"
)
RESEARCH_SOURCE_RESOLUTION_EVIDENCE_CHAIN_LATENCY_REPORT_STATUSES = (
    "pass",
    "watch",
    "block",
)

EMPTY_REASON = "research_source_resolution_evidence_chain_latency_empty"
CLEAR_REASON = "evidence_chain_latency_clear"
CHAIN_LATENCY_WATCH_REASON = "evidence_chain_latency_watch"
CHAIN_LATENCY_BLOCK_REASON = "evidence_chain_latency_block"
AUTHORITY_ACK_WATCH_REASON = "authority_ack_latency_watch"
AUTHORITY_ACK_BLOCK_REASON = "authority_ack_latency_block"
RESOLUTION_SYNC_WATCH_REASON = "resolution_sync_latency_watch"
RESOLUTION_SYNC_BLOCK_REASON = "resolution_sync_latency_block"
LOW_CHAIN_DEPTH_WATCH_REASON = "low_evidence_chain_depth_watch"
LOW_CHAIN_DEPTH_BLOCK_REASON = "low_evidence_chain_depth_block"
MANUAL_HANDOFF_WATCH_REASON = "manual_handoff_latency_watch"
MANUAL_HANDOFF_BLOCK_REASON = "manual_handoff_latency_block"

ROW_REASON_CODES = (
    CLEAR_REASON,
    CHAIN_LATENCY_BLOCK_REASON,
    CHAIN_LATENCY_WATCH_REASON,
    AUTHORITY_ACK_BLOCK_REASON,
    AUTHORITY_ACK_WATCH_REASON,
    RESOLUTION_SYNC_BLOCK_REASON,
    RESOLUTION_SYNC_WATCH_REASON,
    LOW_CHAIN_DEPTH_BLOCK_REASON,
    LOW_CHAIN_DEPTH_WATCH_REASON,
    MANUAL_HANDOFF_BLOCK_REASON,
    MANUAL_HANDOFF_WATCH_REASON,
)
REPORT_REASON_CODES = (EMPTY_REASON,) + ROW_REASON_CODES
REPORT_TRIGGER_REASON_CODES = tuple(
    reason for reason in REPORT_REASON_CODES if reason not in (EMPTY_REASON, CLEAR_REASON)
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
SHA256_HEX_LENGTH = 64

REPORT_PUBLIC_PAYLOAD_FIELDS = (
    "generated_at",
    "config_version",
    "resolution_cluster_count",
    "evidence_chain_count",
    "pass_resolution_cluster_count",
    "watch_resolution_cluster_count",
    "block_resolution_cluster_count",
    "chain_latency_breach_count",
    "authority_ack_latency_breach_count",
    "resolution_sync_latency_breach_count",
    "low_chain_depth_count",
    "manual_handoff_latency_count",
    "highest_latency_pressure_score",
    "slowest_chain_latency_seconds",
    "status",
    "reason_codes",
    "rows",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_DIGEST_PAYLOAD_FIELDS = tuple(
    field_name
    for field_name in REPORT_PUBLIC_PAYLOAD_FIELDS
    if field_name != "derived_validation_digest"
)
ROW_PUBLIC_PAYLOAD_FIELDS = (
    "resolution_cluster",
    "evidence_chain_count",
    "evidence_chain_family_count",
    "maximum_chain_latency_seconds",
    "average_chain_latency_seconds",
    "maximum_authority_ack_latency_seconds",
    "maximum_resolution_sync_latency_seconds",
    "minimum_chain_step_count",
    "pending_manual_handoff_count",
    "latency_pressure_score",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_COUNT_FIELDS = (
    "resolution_cluster_count",
    "evidence_chain_count",
    "pass_resolution_cluster_count",
    "watch_resolution_cluster_count",
    "block_resolution_cluster_count",
    "chain_latency_breach_count",
    "authority_ack_latency_breach_count",
    "resolution_sync_latency_breach_count",
    "low_chain_depth_count",
    "manual_handoff_latency_count",
)
ROW_COUNT_FIELDS = (
    "evidence_chain_count",
    "evidence_chain_family_count",
    "minimum_chain_step_count",
    "pending_manual_handoff_count",
)
ROW_LATENCY_FIELDS = (
    "maximum_chain_latency_seconds",
    "average_chain_latency_seconds",
    "maximum_authority_ack_latency_seconds",
    "maximum_resolution_sync_latency_seconds",
)

UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "market",
    "slug",
    "question",
    "://",
    "url",
    "text",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "live",
)

__all__ = (
    "DEFAULT_RESEARCH_SOURCE_RESOLUTION_EVIDENCE_CHAIN_LATENCY_REPORT_CONFIG_VERSION",
    "RESEARCH_SOURCE_RESOLUTION_EVIDENCE_CHAIN_LATENCY_REPORT_STATUSES",
    "ResearchSourceResolutionEvidenceChainLatencyConfig",
    "ResearchSourceResolutionEvidenceChainLatencyInput",
    "ResearchSourceResolutionEvidenceChainLatencyReport",
    "ResearchSourceResolutionEvidenceChainLatencyRow",
    "build_research_source_resolution_evidence_chain_latency_report",
    "research_source_resolution_evidence_chain_latency_report_digest",
    "research_source_resolution_evidence_chain_latency_report_payload",
    "validate_research_source_resolution_evidence_chain_latency_report_digest",
)


@dataclass(frozen=True)
class ResearchSourceResolutionEvidenceChainLatencyConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_RESOLUTION_EVIDENCE_CHAIN_LATENCY_REPORT_CONFIG_VERSION
    )
    chain_latency_watch_seconds: Decimal = Decimal("3600.000000")
    chain_latency_block_seconds: Decimal = Decimal("7200.000000")
    authority_ack_watch_seconds: Decimal = Decimal("1800.000000")
    authority_ack_block_seconds: Decimal = Decimal("3600.000000")
    resolution_sync_watch_seconds: Decimal = Decimal("1800.000000")
    resolution_sync_block_seconds: Decimal = Decimal("5400.000000")
    min_chain_step_count: Decimal = Decimal("3.000000")
    block_chain_step_count: Decimal = Decimal("1.000000")
    manual_handoff_watch_count: Decimal = Decimal("1.000000")
    manual_handoff_block_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceResolutionEvidenceChainLatencyConfig does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ResearchSourceResolutionEvidenceChainLatencyConfig)
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_RESOLUTION_EVIDENCE_CHAIN_LATENCY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "chain_latency_watch_seconds",
            "chain_latency_block_seconds",
            "authority_ack_watch_seconds",
            "authority_ack_block_seconds",
            "resolution_sync_watch_seconds",
            "resolution_sync_block_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_chain_step_count",
            "block_chain_step_count",
            "manual_handoff_watch_count",
            "manual_handoff_block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _validate_config(self)
        require_paper_only_flags("config", self)
        _reject_unsafe_public_surface("config", self)


@dataclass(frozen=True)
class ResearchSourceResolutionEvidenceChainLatencyInput:
    resolution_cluster: str
    evidence_chain_family: str
    first_evidence_observed_at: datetime
    latest_evidence_observed_at: datetime
    authority_acknowledged_at: datetime
    resolution_ready_at: datetime
    chain_step_count: Decimal
    pending_manual_handoff_count: Decimal = ZERO
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceResolutionEvidenceChainLatencyInput does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "resolution_cluster",
            _require_public_label("resolution_cluster", self.resolution_cluster),
        )
        object.__setattr__(
            self,
            "evidence_chain_family",
            _require_public_label("evidence_chain_family", self.evidence_chain_family),
        )
        for field_name in (
            "first_evidence_observed_at",
            "latest_evidence_observed_at",
            "authority_acknowledged_at",
            "resolution_ready_at",
        ):
            object.__setattr__(self, field_name, _as_utc(field_name, getattr(self, field_name)))
        for field_name in ("chain_step_count", "pending_manual_handoff_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _validate_input(self)
        require_paper_only_flags("latency input", self)
        _reject_unsafe_public_surface("input", self)


@dataclass(frozen=True)
class ResearchSourceResolutionEvidenceChainLatencyRow:
    resolution_cluster: str
    evidence_chain_count: Decimal
    evidence_chain_family_count: Decimal
    maximum_chain_latency_seconds: Decimal
    average_chain_latency_seconds: Decimal
    maximum_authority_ack_latency_seconds: Decimal
    maximum_resolution_sync_latency_seconds: Decimal
    minimum_chain_step_count: Decimal
    pending_manual_handoff_count: Decimal
    latency_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceResolutionEvidenceChainLatencyRow does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchSourceResolutionEvidenceChainLatencyRow)
        object.__setattr__(
            self,
            "resolution_cluster",
            _require_public_label("resolution_cluster", self.resolution_cluster),
        )
        for field_name in ROW_COUNT_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in ROW_LATENCY_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latency_pressure_score",
            _require_ratio_decimal(
                "latency_pressure_score",
                self.latency_pressure_score,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        require_paper_only_flags("latency row", self)
        _reject_unsafe_public_surface("row", self)


@dataclass(frozen=True)
class ResearchSourceResolutionEvidenceChainLatencyReport:
    generated_at: datetime
    config_version: str
    resolution_cluster_count: Decimal
    evidence_chain_count: Decimal
    pass_resolution_cluster_count: Decimal
    watch_resolution_cluster_count: Decimal
    block_resolution_cluster_count: Decimal
    chain_latency_breach_count: Decimal
    authority_ack_latency_breach_count: Decimal
    resolution_sync_latency_breach_count: Decimal
    low_chain_depth_count: Decimal
    manual_handoff_latency_count: Decimal
    highest_latency_pressure_score: Decimal
    slowest_chain_latency_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchSourceResolutionEvidenceChainLatencyRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchSourceResolutionEvidenceChainLatencyReport does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchSourceResolutionEvidenceChainLatencyReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_RESOLUTION_EVIDENCE_CHAIN_LATENCY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in REPORT_COUNT_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "highest_latency_pressure_score",
            _require_ratio_decimal(
                "highest_latency_pressure_score",
                self.highest_latency_pressure_score,
            ),
        )
        object.__setattr__(
            self,
            "slowest_chain_latency_seconds",
            _require_nonnegative_decimal(
                "slowest_chain_latency_seconds",
                self.slowest_chain_latency_seconds,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        require_paper_only_flags("latency report", self)
        _reject_unsafe_public_surface("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_digest_from_public_payload(self),
            )
        else:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != _report_digest_from_public_payload(self):
                raise ValueError("derived_validation_digest must match report payload")


def build_research_source_resolution_evidence_chain_latency_report(
    inputs: list[ResearchSourceResolutionEvidenceChainLatencyInput]
    | tuple[ResearchSourceResolutionEvidenceChainLatencyInput, ...],
    *,
    config: ResearchSourceResolutionEvidenceChainLatencyConfig,
    generated_at: datetime,
) -> ResearchSourceResolutionEvidenceChainLatencyReport:
    """Build a deterministic report-only source-resolution latency snapshot."""

    if type(config) is not ResearchSourceResolutionEvidenceChainLatencyConfig:
        raise ValueError(
            "config must be a ResearchSourceResolutionEvidenceChainLatencyConfig",
        )
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _latency_rows(
        _normalize_inputs(inputs, generated_at=generated_at_utc),
        config=config,
    )
    return ResearchSourceResolutionEvidenceChainLatencyReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        resolution_cluster_count=_count(len(rows)),
        evidence_chain_count=_sum_rows(rows, "evidence_chain_count"),
        pass_resolution_cluster_count=_status_count(rows, "pass"),
        watch_resolution_cluster_count=_status_count(rows, "watch"),
        block_resolution_cluster_count=_status_count(rows, "block"),
        chain_latency_breach_count=_reason_count(
            rows,
            (CHAIN_LATENCY_WATCH_REASON, CHAIN_LATENCY_BLOCK_REASON),
        ),
        authority_ack_latency_breach_count=_reason_count(
            rows,
            (AUTHORITY_ACK_WATCH_REASON, AUTHORITY_ACK_BLOCK_REASON),
        ),
        resolution_sync_latency_breach_count=_reason_count(
            rows,
            (RESOLUTION_SYNC_WATCH_REASON, RESOLUTION_SYNC_BLOCK_REASON),
        ),
        low_chain_depth_count=_reason_count(
            rows,
            (LOW_CHAIN_DEPTH_WATCH_REASON, LOW_CHAIN_DEPTH_BLOCK_REASON),
        ),
        manual_handoff_latency_count=_reason_count(
            rows,
            (MANUAL_HANDOFF_WATCH_REASON, MANUAL_HANDOFF_BLOCK_REASON),
        ),
        highest_latency_pressure_score=max(
            (row.latency_pressure_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        slowest_chain_latency_seconds=max(
            (row.maximum_chain_latency_seconds for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_source_resolution_evidence_chain_latency_report_payload(
    report: ResearchSourceResolutionEvidenceChainLatencyReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceResolutionEvidenceChainLatencyReport:
        raise ValueError(
            "report must be a ResearchSourceResolutionEvidenceChainLatencyReport",
        )
    validate_research_source_resolution_evidence_chain_latency_report_digest(report)
    require_paper_only_flags("report", report)
    _reject_unsafe_public_surface("report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _validate_public_payload_schema(payload, include_digest=True)
    _reject_unsafe_public_surface("payload", payload)
    return payload


def research_source_resolution_evidence_chain_latency_report_digest(
    report: ResearchSourceResolutionEvidenceChainLatencyReport,
) -> str:
    if type(report) is not ResearchSourceResolutionEvidenceChainLatencyReport:
        raise ValueError(
            "report must be a ResearchSourceResolutionEvidenceChainLatencyReport",
        )
    _validate_report(report)
    return _report_digest_from_public_payload(report)


def validate_research_source_resolution_evidence_chain_latency_report_digest(
    report: ResearchSourceResolutionEvidenceChainLatencyReport,
) -> None:
    if type(report) is not ResearchSourceResolutionEvidenceChainLatencyReport:
        raise ValueError(
            "report must be a ResearchSourceResolutionEvidenceChainLatencyReport",
        )
    _validate_report(report)
    _require_sha256("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != _report_digest_from_public_payload(report):
        raise ValueError("derived_validation_digest must match report payload")


def _latency_rows(
    inputs: tuple[ResearchSourceResolutionEvidenceChainLatencyInput, ...],
    *,
    config: ResearchSourceResolutionEvidenceChainLatencyConfig,
) -> tuple[ResearchSourceResolutionEvidenceChainLatencyRow, ...]:
    grouped: dict[str, list[ResearchSourceResolutionEvidenceChainLatencyInput]] = {}
    for item in inputs:
        grouped.setdefault(item.resolution_cluster, []).append(item)
    return tuple(
        sorted(
            (_latency_row(tuple(cluster_rows), config=config) for cluster_rows in grouped.values()),
            key=_row_sort_key,
        ),
    )


def _latency_row(
    cluster_rows: tuple[ResearchSourceResolutionEvidenceChainLatencyInput, ...],
    *,
    config: ResearchSourceResolutionEvidenceChainLatencyConfig,
) -> ResearchSourceResolutionEvidenceChainLatencyRow:
    chain_latencies = tuple(
        _duration_seconds(item.first_evidence_observed_at, item.resolution_ready_at)
        for item in cluster_rows
    )
    authority_ack_latencies = tuple(
        _duration_seconds(item.latest_evidence_observed_at, item.authority_acknowledged_at)
        for item in cluster_rows
    )
    resolution_sync_latencies = tuple(
        _duration_seconds(item.authority_acknowledged_at, item.resolution_ready_at)
        for item in cluster_rows
    )
    maximum_chain_latency_seconds = max(chain_latencies, default=ZERO).quantize(QUANT)
    average_chain_latency_seconds = _average(chain_latencies)
    maximum_authority_ack_latency_seconds = max(
        authority_ack_latencies,
        default=ZERO,
    ).quantize(QUANT)
    maximum_resolution_sync_latency_seconds = max(
        resolution_sync_latencies,
        default=ZERO,
    ).quantize(QUANT)
    minimum_chain_step_count = min(
        (item.chain_step_count for item in cluster_rows),
        default=ZERO,
    ).quantize(QUANT)
    pending_manual_handoff_count = sum(
        (item.pending_manual_handoff_count for item in cluster_rows),
        ZERO,
    ).quantize(QUANT)
    reason_codes = _row_reason_codes(
        maximum_chain_latency_seconds=maximum_chain_latency_seconds,
        maximum_authority_ack_latency_seconds=maximum_authority_ack_latency_seconds,
        maximum_resolution_sync_latency_seconds=maximum_resolution_sync_latency_seconds,
        minimum_chain_step_count=minimum_chain_step_count,
        pending_manual_handoff_count=pending_manual_handoff_count,
        config=config,
    )
    return ResearchSourceResolutionEvidenceChainLatencyRow(
        resolution_cluster=cluster_rows[0].resolution_cluster,
        evidence_chain_count=_count(len(cluster_rows)),
        evidence_chain_family_count=_count(
            len({item.evidence_chain_family for item in cluster_rows}),
        ),
        maximum_chain_latency_seconds=maximum_chain_latency_seconds,
        average_chain_latency_seconds=average_chain_latency_seconds,
        maximum_authority_ack_latency_seconds=maximum_authority_ack_latency_seconds,
        maximum_resolution_sync_latency_seconds=maximum_resolution_sync_latency_seconds,
        minimum_chain_step_count=minimum_chain_step_count,
        pending_manual_handoff_count=pending_manual_handoff_count,
        latency_pressure_score=_latency_pressure_score(
            maximum_chain_latency_seconds=maximum_chain_latency_seconds,
            maximum_authority_ack_latency_seconds=maximum_authority_ack_latency_seconds,
            maximum_resolution_sync_latency_seconds=maximum_resolution_sync_latency_seconds,
            minimum_chain_step_count=minimum_chain_step_count,
            pending_manual_handoff_count=pending_manual_handoff_count,
            config=config,
        ),
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    maximum_chain_latency_seconds: Decimal,
    maximum_authority_ack_latency_seconds: Decimal,
    maximum_resolution_sync_latency_seconds: Decimal,
    minimum_chain_step_count: Decimal,
    pending_manual_handoff_count: Decimal,
    config: ResearchSourceResolutionEvidenceChainLatencyConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if maximum_chain_latency_seconds >= config.chain_latency_block_seconds:
        reasons.append(CHAIN_LATENCY_BLOCK_REASON)
    elif maximum_chain_latency_seconds >= config.chain_latency_watch_seconds:
        reasons.append(CHAIN_LATENCY_WATCH_REASON)
    if maximum_authority_ack_latency_seconds >= config.authority_ack_block_seconds:
        reasons.append(AUTHORITY_ACK_BLOCK_REASON)
    elif maximum_authority_ack_latency_seconds >= config.authority_ack_watch_seconds:
        reasons.append(AUTHORITY_ACK_WATCH_REASON)
    if maximum_resolution_sync_latency_seconds >= config.resolution_sync_block_seconds:
        reasons.append(RESOLUTION_SYNC_BLOCK_REASON)
    elif maximum_resolution_sync_latency_seconds >= config.resolution_sync_watch_seconds:
        reasons.append(RESOLUTION_SYNC_WATCH_REASON)
    if minimum_chain_step_count <= config.block_chain_step_count:
        reasons.append(LOW_CHAIN_DEPTH_BLOCK_REASON)
    elif minimum_chain_step_count < config.min_chain_step_count:
        reasons.append(LOW_CHAIN_DEPTH_WATCH_REASON)
    if pending_manual_handoff_count >= config.manual_handoff_block_count:
        reasons.append(MANUAL_HANDOFF_BLOCK_REASON)
    elif pending_manual_handoff_count >= config.manual_handoff_watch_count:
        reasons.append(MANUAL_HANDOFF_WATCH_REASON)
    if not reasons:
        reasons.append(CLEAR_REASON)
    return tuple(reason for reason in ROW_REASON_CODES if reason in reasons)


def _latency_pressure_score(
    *,
    maximum_chain_latency_seconds: Decimal,
    maximum_authority_ack_latency_seconds: Decimal,
    maximum_resolution_sync_latency_seconds: Decimal,
    minimum_chain_step_count: Decimal,
    pending_manual_handoff_count: Decimal,
    config: ResearchSourceResolutionEvidenceChainLatencyConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        chain_pressure = _bounded_ratio(
            maximum_chain_latency_seconds / config.chain_latency_block_seconds,
        )
        ack_pressure = _bounded_ratio(
            maximum_authority_ack_latency_seconds / config.authority_ack_block_seconds,
        )
        sync_pressure = _bounded_ratio(
            maximum_resolution_sync_latency_seconds / config.resolution_sync_block_seconds,
        )
        if config.min_chain_step_count == ZERO:
            depth_pressure = ZERO
        else:
            depth_pressure = _bounded_ratio(
                (config.min_chain_step_count - minimum_chain_step_count)
                / config.min_chain_step_count,
            )
        if config.manual_handoff_block_count == ZERO:
            handoff_pressure = ONE if pending_manual_handoff_count > ZERO else ZERO
        else:
            handoff_pressure = _bounded_ratio(
                pending_manual_handoff_count / config.manual_handoff_block_count,
            )
        score = (
            chain_pressure
            + ack_pressure
            + sync_pressure
            + depth_pressure
            + handoff_pressure
        ) / Decimal("5.000000")
        return score.quantize(QUANT)


def _normalize_inputs(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[ResearchSourceResolutionEvidenceChainLatencyInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchSourceResolutionEvidenceChainLatencyInput:
            raise ValueError(
                "inputs must contain ResearchSourceResolutionEvidenceChainLatencyInput",
            )
        require_paper_only_flags("input", row)
        if row.first_evidence_observed_at > generated_at:
            raise ValueError("first_evidence_observed_at must not be in the future")
        if row.latest_evidence_observed_at > generated_at:
            raise ValueError("latest_evidence_observed_at must not be in the future")
        if row.authority_acknowledged_at > generated_at:
            raise ValueError("authority_acknowledged_at must not be in the future")
        if row.resolution_ready_at > generated_at:
            raise ValueError("resolution_ready_at must not be in the future")
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.resolution_cluster,
                row.evidence_chain_family,
                row.first_evidence_observed_at,
                row.latest_evidence_observed_at,
                row.authority_acknowledged_at,
                row.resolution_ready_at,
            ),
        ),
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return "block"
    if reason_codes == (CLEAR_REASON,):
        return "pass"
    return "watch"


def _report_status(rows: tuple[ResearchSourceResolutionEvidenceChainLatencyRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceResolutionEvidenceChainLatencyRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    reasons = tuple(
        reason
        for reason in REPORT_TRIGGER_REASON_CODES
        if any(reason in row.reason_codes for row in rows)
    )
    if reasons:
        return reasons
    return (CLEAR_REASON,)


def _row_sort_key(row: ResearchSourceResolutionEvidenceChainLatencyRow) -> tuple[Decimal, str]:
    return (-row.latency_pressure_score, row.resolution_cluster)


def _status_count(
    rows: tuple[ResearchSourceResolutionEvidenceChainLatencyRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchSourceResolutionEvidenceChainLatencyRow, ...],
    reasons: tuple[str, ...],
) -> Decimal:
    return _count(sum(1 for row in rows if any(reason in row.reason_codes for reason in reasons)))


def _sum_rows(
    rows: tuple[ResearchSourceResolutionEvidenceChainLatencyRow, ...],
    field_name: str,
) -> Decimal:
    return sum((getattr(row, field_name) for row in rows), ZERO).quantize(QUANT)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (sum(values, ZERO) / Decimal(len(values))).quantize(QUANT)


def _duration_seconds(start_at: datetime, end_at: datetime) -> Decimal:
    start_at_utc = _as_utc("start_at", start_at)
    end_at_utc = _as_utc("end_at", end_at)
    delta = end_at_utc - start_at_utc
    seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    if seconds < ZERO:
        raise ValueError("latency timestamps must be monotonic")
    return seconds.quantize(QUANT)


def _validate_config(config: ResearchSourceResolutionEvidenceChainLatencyConfig) -> None:
    if config.chain_latency_block_seconds <= config.chain_latency_watch_seconds:
        raise ValueError(
            "chain_latency_block_seconds must exceed chain_latency_watch_seconds",
        )
    if config.authority_ack_block_seconds <= config.authority_ack_watch_seconds:
        raise ValueError(
            "authority_ack_block_seconds must exceed authority_ack_watch_seconds",
        )
    if config.resolution_sync_block_seconds <= config.resolution_sync_watch_seconds:
        raise ValueError(
            "resolution_sync_block_seconds must exceed resolution_sync_watch_seconds",
        )
    if config.block_chain_step_count > config.min_chain_step_count:
        raise ValueError("block_chain_step_count must not exceed min_chain_step_count")
    if config.manual_handoff_block_count < config.manual_handoff_watch_count:
        raise ValueError(
            "manual_handoff_block_count must not be below manual_handoff_watch_count",
        )


def _validate_input(row: ResearchSourceResolutionEvidenceChainLatencyInput) -> None:
    _duration_seconds(row.first_evidence_observed_at, row.latest_evidence_observed_at)
    _duration_seconds(row.latest_evidence_observed_at, row.authority_acknowledged_at)
    _duration_seconds(row.authority_acknowledged_at, row.resolution_ready_at)
    if row.chain_step_count == ZERO:
        raise ValueError("chain_step_count must be positive")


def _validate_row(row: ResearchSourceResolutionEvidenceChainLatencyRow) -> None:
    if row.evidence_chain_count <= ZERO:
        raise ValueError("evidence_chain_count must be positive")
    if row.evidence_chain_family_count <= ZERO:
        raise ValueError("evidence_chain_family_count must be positive")
    if row.evidence_chain_family_count > row.evidence_chain_count:
        raise ValueError(
            "evidence_chain_family_count must not exceed evidence_chain_count",
        )
    if row.average_chain_latency_seconds > row.maximum_chain_latency_seconds:
        raise ValueError(
            "average_chain_latency_seconds must not exceed maximum_chain_latency_seconds",
        )
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != (CLEAR_REASON,):
        raise ValueError("pass rows must be clear")


def _validate_report(report: ResearchSourceResolutionEvidenceChainLatencyReport) -> None:
    if report.resolution_cluster_count != _count(len(report.rows)):
        raise ValueError("resolution_cluster_count must match rows")
    if report.evidence_chain_count != _sum_rows(report.rows, "evidence_chain_count"):
        raise ValueError("evidence_chain_count must match rows")
    for status, field_name in (
        ("pass", "pass_resolution_cluster_count"),
        ("watch", "watch_resolution_cluster_count"),
        ("block", "block_resolution_cluster_count"),
    ):
        if getattr(report, field_name) != _status_count(report.rows, status):
            raise ValueError(f"{field_name} must match rows")
    reason_count_fields = (
        (
            "chain_latency_breach_count",
            (CHAIN_LATENCY_WATCH_REASON, CHAIN_LATENCY_BLOCK_REASON),
        ),
        (
            "authority_ack_latency_breach_count",
            (AUTHORITY_ACK_WATCH_REASON, AUTHORITY_ACK_BLOCK_REASON),
        ),
        (
            "resolution_sync_latency_breach_count",
            (RESOLUTION_SYNC_WATCH_REASON, RESOLUTION_SYNC_BLOCK_REASON),
        ),
        (
            "low_chain_depth_count",
            (LOW_CHAIN_DEPTH_WATCH_REASON, LOW_CHAIN_DEPTH_BLOCK_REASON),
        ),
        (
            "manual_handoff_latency_count",
            (MANUAL_HANDOFF_WATCH_REASON, MANUAL_HANDOFF_BLOCK_REASON),
        ),
    )
    for field_name, reasons in reason_count_fields:
        if getattr(report, field_name) != _reason_count(report.rows, reasons):
            raise ValueError(f"{field_name} must match rows")
    if report.highest_latency_pressure_score != max(
        (row.latency_pressure_score for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("highest_latency_pressure_score must match rows")
    if report.slowest_chain_latency_seconds != max(
        (row.maximum_chain_latency_seconds for row in report.rows),
        default=ZERO,
    ).quantize(QUANT):
        raise ValueError("slowest_chain_latency_seconds must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic latency sort")


def _normalize_rows(
    value: object,
) -> tuple[ResearchSourceResolutionEvidenceChainLatencyRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceResolutionEvidenceChainLatencyRow:
            raise ValueError(
                "rows must contain ResearchSourceResolutionEvidenceChainLatencyRow",
            )
        require_paper_only_flags("latency row", row)
        if row.resolution_cluster in seen:
            raise ValueError("rows must be unique by resolution_cluster")
        seen.add(row.resolution_cluster)
    return tuple(sorted(rows, key=_row_sort_key))


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(QUANT)


def _bounded_ratio(value: Decimal) -> Decimal:
    return min(max(value, ZERO), ONE).quantize(QUANT)


def _require_exact_type(label: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    decimal_value = value.quantize(QUANT)
    if decimal_value != value:
        raise ValueError(f"{field_name} must use six decimal places")
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value == ZERO:
        return ZERO
    return decimal_value


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must not exceed 1")
    return decimal_value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason in reason_codes:
        _require_canonical_string(field_name, reason)
        if reason not in allowed:
            raise ValueError(f"{field_name} contains unsupported reason code")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must not contain duplicates")
    return tuple(reason for reason in allowed if reason in reason_codes)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in RESEARCH_SOURCE_RESOLUTION_EVIDENCE_CHAIN_LATENCY_REPORT_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_public_label(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    label = str(value)
    lowered = label.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe text")
    if not all(
        character.islower() or character.isdigit() or character in "._-"
        for character in label
    ):
        raise ValueError(f"{field_name} must use a canonical public label")
    return label


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "" or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_public_text(f"{label}.{key}", str(key), is_key=True)
            _reject_unsafe_public_surface(f"{label}.{key}", item)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_unsafe_public_surface(f"{label}[{index}]", item)
        return
    if hasattr(value, "__dataclass_fields__"):
        _reject_unsafe_public_surface(label, asdict(value))
        return
    if isinstance(value, str):
        _reject_unsafe_public_text(label, value, is_key=False)


def _reject_unsafe_public_text(label: str, value: str, *, is_key: bool) -> None:
    lowered = value.lower()
    key_allowed = {"config_version"}
    if is_key and lowered in key_allowed:
        return
    if not is_key and label.endswith("config_version"):
        return
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{label} contains unsafe public text")


def _report_digest_from_public_payload(
    report: ResearchSourceResolutionEvidenceChainLatencyReport,
) -> str:
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    payload = dict(payload)
    _require_exact_payload_fields(
        "report",
        payload,
        REPORT_PUBLIC_PAYLOAD_FIELDS,
    )
    payload.pop("derived_validation_digest")
    _validate_public_payload_schema(payload, include_digest=False)
    _reject_unsafe_public_surface("digest payload", payload)
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_public_payload_schema(
    payload: object,
    *,
    include_digest: bool,
) -> None:
    expected_fields = (
        REPORT_PUBLIC_PAYLOAD_FIELDS if include_digest else REPORT_DIGEST_PAYLOAD_FIELDS
    )
    report_payload = _require_exact_payload_fields("report", payload, expected_fields)
    _require_public_datetime_string("generated_at", report_payload["generated_at"])
    if (
        report_payload["config_version"]
        != DEFAULT_RESEARCH_SOURCE_RESOLUTION_EVIDENCE_CHAIN_LATENCY_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    for field_name in REPORT_COUNT_FIELDS:
        _require_public_decimal_string(
            field_name,
            report_payload[field_name],
            _require_nonnegative_whole_decimal,
        )
    _require_public_decimal_string(
        "highest_latency_pressure_score",
        report_payload["highest_latency_pressure_score"],
        _require_ratio_decimal,
    )
    _require_public_decimal_string(
        "slowest_chain_latency_seconds",
        report_payload["slowest_chain_latency_seconds"],
        _require_nonnegative_decimal,
    )
    _require_status("status", report_payload["status"])
    _require_public_reason_code_list(
        "reason_codes",
        report_payload["reason_codes"],
        REPORT_REASON_CODES,
    )
    rows = report_payload["rows"]
    if type(rows) is not list:
        raise ValueError("rows must be a list in the public payload schema")
    for index, row in enumerate(rows):
        _validate_public_row_payload_schema(index, row)
    if include_digest:
        _require_sha256(
            "derived_validation_digest",
            report_payload["derived_validation_digest"],
        )
    _require_public_payload_flags(report_payload)


def _validate_public_row_payload_schema(index: int, payload: object) -> None:
    row_payload = _require_exact_payload_fields(
        f"rows[{index}]",
        payload,
        ROW_PUBLIC_PAYLOAD_FIELDS,
    )
    _require_public_label("resolution_cluster", row_payload["resolution_cluster"])
    parsed_counts = {
        field_name: _require_public_decimal_string(
            field_name,
            row_payload[field_name],
            _require_nonnegative_whole_decimal,
        )
        for field_name in ROW_COUNT_FIELDS
    }
    if parsed_counts["evidence_chain_count"] <= ZERO:
        raise ValueError("evidence_chain_count must be positive")
    if parsed_counts["evidence_chain_family_count"] <= ZERO:
        raise ValueError("evidence_chain_family_count must be positive")
    if (
        parsed_counts["evidence_chain_family_count"]
        > parsed_counts["evidence_chain_count"]
    ):
        raise ValueError(
            "evidence_chain_family_count must not exceed evidence_chain_count",
        )
    for field_name in ROW_LATENCY_FIELDS:
        _require_public_decimal_string(
            field_name,
            row_payload[field_name],
            _require_nonnegative_decimal,
        )
    _require_public_decimal_string(
        "latency_pressure_score",
        row_payload["latency_pressure_score"],
        _require_ratio_decimal,
    )
    _require_status("status", row_payload["status"])
    reason_codes = _require_public_reason_code_list(
        "reason_codes",
        row_payload["reason_codes"],
        ROW_REASON_CODES,
    )
    if row_payload["status"] != _row_status(reason_codes):
        raise ValueError("status must match reason_codes")
    _require_public_payload_flags(row_payload)


def _require_exact_payload_fields(
    label: str,
    payload: object,
    expected_fields: tuple[str, ...],
) -> dict[str, Any]:
    if type(payload) is not dict:
        raise ValueError(f"{label} must be a dict in the public payload schema")
    if set(payload) != set(expected_fields):
        raise ValueError(f"{label} does not match the public payload schema")
    return payload


def _require_public_datetime_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string in the public payload schema")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            f"{field_name} must be an ISO-8601 datetime in the public payload schema",
        ) from exc
    if value != _as_utc(field_name, parsed).isoformat():
        raise ValueError(
            f"{field_name} must be a canonical UTC datetime in the public payload schema",
        )


def _require_public_decimal_string(
    field_name: str,
    value: object,
    validator: Any,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(
            f"{field_name} must be a Decimal string in the public payload schema",
        )
    try:
        parsed = Decimal(value)
    except Exception as exc:
        raise ValueError(
            f"{field_name} must be a Decimal string in the public payload schema",
        ) from exc
    normalized = validator(field_name, parsed)
    if value != str(normalized):
        raise ValueError(
            f"{field_name} must be canonical in the public payload schema",
        )
    return normalized


def _require_public_reason_code_list(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list in the public payload schema")
    normalized = _normalize_reason_codes(field_name, value, allowed)
    if list(normalized) != value:
        raise ValueError(f"{field_name} must be canonical in the public payload schema")
    return normalized


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if type(payload[field_name]) is not bool or payload[field_name] is not True:
            raise ValueError(f"{field_name} must be true in the public payload schema")


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != SHA256_HEX_LENGTH:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a sha256 hex digest") from exc
