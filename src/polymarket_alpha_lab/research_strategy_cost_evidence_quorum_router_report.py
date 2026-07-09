"""Report-only cost, evidence, and quorum router readiness report.

This module builds deterministic public research reports only. It exposes no
database, network, wallet, auth, order, sizing, recommendation, or live trading
surface.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import InitVar, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_STRATEGY_COST_EVIDENCE_QUORUM_ROUTER_REPORT_CONFIG_VERSION = (
    "research-strategy-cost-evidence-quorum-router-report-v0"
)
RESEARCH_STRATEGY_COST_EVIDENCE_QUORUM_ROUTER_REPORT_STATUSES = (
    "pass",
    "watch",
    "block",
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

REASON_EMPTY_INPUT = "empty_input"
REASON_SCOPE_REVIEWED = "scope_reviewed"
REASON_MANUAL_REVIEW_REQUESTED = "manual_review_requested"
REASON_EVIDENCE_PACKET_AVAILABLE = "evidence_packet_available"
REASON_COST_PRESSURE_BLOCK = "cost_pressure_block"
REASON_COST_PRESSURE_WATCH = "cost_pressure_watch"
REASON_EVIDENCE_STRENGTH_BLOCK = "evidence_strength_block"
REASON_EVIDENCE_STRENGTH_WATCH = "evidence_strength_watch"
REASON_QUORUM_BLOCK = "quorum_block"
REASON_QUORUM_WATCH = "quorum_watch"
REASON_FRESHNESS_BLOCK = "freshness_block"
REASON_FRESHNESS_WATCH = "freshness_watch"
REASON_ROUTER_SCORE_BLOCK = "router_score_block"
REASON_ROUTER_SCORE_WATCH = "router_score_watch"
REASON_ROUTER_READY_PASS = "router_ready_pass"

_UPSTREAM_REASON_CODE_SEQUENCE = (
    REASON_SCOPE_REVIEWED,
    REASON_MANUAL_REVIEW_REQUESTED,
    REASON_EVIDENCE_PACKET_AVAILABLE,
)
_GENERATED_ROW_REASON_CODE_SEQUENCE = (
    REASON_COST_PRESSURE_BLOCK,
    REASON_EVIDENCE_STRENGTH_BLOCK,
    REASON_QUORUM_BLOCK,
    REASON_FRESHNESS_BLOCK,
    REASON_ROUTER_SCORE_BLOCK,
    REASON_COST_PRESSURE_WATCH,
    REASON_EVIDENCE_STRENGTH_WATCH,
    REASON_QUORUM_WATCH,
    REASON_FRESHNESS_WATCH,
    REASON_ROUTER_SCORE_WATCH,
    REASON_ROUTER_READY_PASS,
)
_ROW_REASON_CODE_SEQUENCE = (
    *_UPSTREAM_REASON_CODE_SEQUENCE,
    *_GENERATED_ROW_REASON_CODE_SEQUENCE,
)
_REASON_CODE_SEQUENCE = (REASON_EMPTY_INPUT, *_ROW_REASON_CODE_SEQUENCE)
_BLOCK_REASON_CODES = frozenset(
    (
        REASON_COST_PRESSURE_BLOCK,
        REASON_EVIDENCE_STRENGTH_BLOCK,
        REASON_QUORUM_BLOCK,
        REASON_FRESHNESS_BLOCK,
        REASON_ROUTER_SCORE_BLOCK,
    ),
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DIGEST_FIELD = "derived_validation_digest"
_STATUS_VALUES = frozenset(RESEARCH_STRATEGY_COST_EVIDENCE_QUORUM_ROUTER_REPORT_STATUSES)
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PRIVATE_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_UNSAFE_PUBLIC_FRAGMENTS = (
    "raw",
    "candidate",
    "market",
    "slug",
    "question",
    "source",
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
    "order",
    "trade",
    "position",
    "sizing",
    "buy",
    "sell",
    "recommend",
    "private key",
    "secret",
    "credential",
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
class ResearchStrategyCostEvidenceQuorumRouterConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_COST_EVIDENCE_QUORUM_ROUTER_REPORT_CONFIG_VERSION
    )
    pass_min_router_score: Decimal = Decimal("0.800000")
    watch_min_router_score: Decimal = Decimal("0.600000")
    max_pass_cost_pressure_score: Decimal = Decimal("0.250000")
    max_watch_cost_pressure_score: Decimal = Decimal("0.450000")
    min_pass_evidence_strength_score: Decimal = Decimal("0.800000")
    min_watch_evidence_strength_score: Decimal = Decimal("0.600000")
    min_pass_quorum_score: Decimal = Decimal("0.800000")
    min_watch_quorum_score: Decimal = Decimal("0.600000")
    min_pass_freshness_score: Decimal = Decimal("0.750000")
    min_watch_freshness_score: Decimal = Decimal("0.500000")
    cost_efficiency_weight: Decimal = Decimal("0.300000")
    evidence_strength_weight: Decimal = Decimal("0.300000")
    quorum_weight: Decimal = Decimal("0.250000")
    freshness_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyCostEvidenceQuorumRouterConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_COST_EVIDENCE_QUORUM_ROUTER_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_min_router_score",
            "watch_min_router_score",
            "max_pass_cost_pressure_score",
            "max_watch_cost_pressure_score",
            "min_pass_evidence_strength_score",
            "min_watch_evidence_strength_score",
            "min_pass_quorum_score",
            "min_watch_quorum_score",
            "min_pass_freshness_score",
            "min_watch_freshness_score",
            "cost_efficiency_weight",
            "evidence_strength_weight",
            "quorum_weight",
            "freshness_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_min_router_score < self.watch_min_router_score:
            raise ValueError(
                "pass_min_router_score must be at least watch_min_router_score",
            )
        if self.max_pass_cost_pressure_score > self.max_watch_cost_pressure_score:
            raise ValueError(
                "max_pass_cost_pressure_score must not exceed "
                "max_watch_cost_pressure_score",
            )
        _require_min_threshold_pair(
            "evidence strength threshold",
            self.min_watch_evidence_strength_score,
            self.min_pass_evidence_strength_score,
        )
        _require_min_threshold_pair(
            "quorum threshold",
            self.min_watch_quorum_score,
            self.min_pass_quorum_score,
        )
        _require_min_threshold_pair(
            "freshness threshold",
            self.min_watch_freshness_score,
            self.min_pass_freshness_score,
        )
        weight_sum = _quantize(
            self.cost_efficiency_weight
            + self.evidence_strength_weight
            + self.quorum_weight
            + self.freshness_weight,
        )
        if weight_sum != _ONE:
            raise ValueError("router weights must sum to one")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyCostEvidenceQuorumRouterInput(_FinalPublicDataclass):
    route_ref: str
    cost_pressure_score: Decimal
    evidence_strength_score: Decimal
    quorum_score: Decimal
    freshness_score: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyCostEvidenceQuorumRouterInput, "input")
        object.__setattr__(
            self,
            "route_ref",
            _require_private_ref("route_ref", self.route_ref),
        )
        for field_name in (
            "cost_pressure_score",
            "evidence_strength_score",
            "quorum_score",
            "freshness_score",
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
            _normalize_upstream_reason_codes(self.reason_codes),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyCostEvidenceQuorumRouterPublicNote(_FinalPublicDataclass):
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyCostEvidenceQuorumRouterPublicNote,
            "public note",
        )
        object.__setattr__(self, "key", _require_public_identifier("key", self.key))
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public note", self)
        _reject_unsafe_public_payload("public note", self)


@dataclass(frozen=True)
class ResearchStrategyCostEvidenceQuorumRouterRow(_FinalPublicDataclass):
    route_digest: str
    cost_pressure_score: Decimal
    cost_efficiency_score: Decimal
    evidence_strength_score: Decimal
    evidence_gap_score: Decimal
    quorum_score: Decimal
    quorum_gap_score: Decimal
    freshness_score: Decimal
    freshness_gap_score: Decimal
    router_score: Decimal
    observed_at: datetime
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[
        ResearchStrategyCostEvidenceQuorumRouterConfig | None
    ] = None

    def __post_init__(
        self,
        validation_config: ResearchStrategyCostEvidenceQuorumRouterConfig | None,
    ) -> None:
        _require_exact_type(self, ResearchStrategyCostEvidenceQuorumRouterRow, "row")
        object.__setattr__(
            self,
            "route_digest",
            _require_private_digest("route_digest", self.route_digest),
        )
        for field_name in (
            "cost_pressure_score",
            "cost_efficiency_score",
            "evidence_strength_score",
            "evidence_gap_score",
            "quorum_score",
            "quorum_gap_score",
            "freshness_score",
            "freshness_gap_score",
            "router_score",
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
class ResearchStrategyCostEvidenceQuorumRouterReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyCostEvidenceQuorumRouterReasonCodeCount,
            "reason count",
        )
        _require_reason_code("reason_code", self.reason_code, _REASON_CODE_SEQUENCE)
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
class ResearchStrategyCostEvidenceQuorumRouterReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_router_score: Decimal
    min_router_score: Decimal
    max_cost_pressure_score: Decimal
    min_evidence_strength_score: Decimal
    min_quorum_score: Decimal
    min_freshness_score: Decimal
    rows: tuple[ResearchStrategyCostEvidenceQuorumRouterRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyCostEvidenceQuorumRouterReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    public_notes: tuple[ResearchStrategyCostEvidenceQuorumRouterPublicNote, ...] = ()
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyCostEvidenceQuorumRouterReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_COST_EVIDENCE_QUORUM_ROUTER_REPORT_CONFIG_VERSION
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
            "average_router_score",
            "min_router_score",
            "max_cost_pressure_score",
            "min_evidence_strength_score",
            "min_quorum_score",
            "min_freshness_score",
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
        object.__setattr__(self, "public_notes", _normalize_public_notes(self.public_notes))
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
        return research_strategy_cost_evidence_quorum_router_report_payload(self)


def build_research_strategy_cost_evidence_quorum_router_report(
    inputs: Sequence[ResearchStrategyCostEvidenceQuorumRouterInput],
    *,
    generated_at: datetime,
    config: ResearchStrategyCostEvidenceQuorumRouterConfig | None = None,
    public_notes: Sequence[ResearchStrategyCostEvidenceQuorumRouterPublicNote] = (),
) -> ResearchStrategyCostEvidenceQuorumRouterReport:
    """Build a deterministic, readonly cost/evidence/quorum router report."""

    cfg = config or ResearchStrategyCostEvidenceQuorumRouterConfig()
    if type(cfg) is not ResearchStrategyCostEvidenceQuorumRouterConfig:
        raise ValueError(
            "config must be a ResearchStrategyCostEvidenceQuorumRouterConfig",
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
            ResearchStrategyCostEvidenceQuorumRouterReasonCodeCount(
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
        "average_router_score": _average_ratio(tuple(row.router_score for row in rows)),
        "min_router_score": min((row.router_score for row in rows), default=_ZERO),
        "max_cost_pressure_score": max(
            (row.cost_pressure_score for row in rows),
            default=_ZERO,
        ),
        "min_evidence_strength_score": min(
            (row.evidence_strength_score for row in rows),
            default=_ZERO,
        ),
        "min_quorum_score": min((row.quorum_score for row in rows), default=_ZERO),
        "min_freshness_score": min((row.freshness_score for row in rows), default=_ZERO),
        "rows": rows,
        "reason_code_counts": reason_code_counts,
        "reason_codes": reason_codes,
        "public_notes": _normalize_public_notes(public_notes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyCostEvidenceQuorumRouterReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_strategy_cost_evidence_quorum_router_report_payload(
    value: ResearchStrategyCostEvidenceQuorumRouterReport | dict[str, object],
) -> dict[str, object]:
    if type(value) is ResearchStrategyCostEvidenceQuorumRouterReport:
        _require_hard_flags("report", value)
        payload = _report_payload(value)
    elif type(value) is dict:
        payload = _copy_json_object(value)
    else:
        raise ValueError(
            "value must be a ResearchStrategyCostEvidenceQuorumRouterReport or dict",
        )
    _validate_payload_statuses(payload)
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_payload_digest(payload)
    return payload


def validate_research_strategy_cost_evidence_quorum_router_report_payload(
    value: dict[str, object],
) -> bool:
    research_strategy_cost_evidence_quorum_router_report_payload(value)
    return True


def validate_research_strategy_cost_evidence_quorum_router_report_digest(
    report: ResearchStrategyCostEvidenceQuorumRouterReport,
) -> bool:
    if type(report) is not ResearchStrategyCostEvidenceQuorumRouterReport:
        raise ValueError("report must be a ResearchStrategyCostEvidenceQuorumRouterReport")
    research_strategy_cost_evidence_quorum_router_report_payload(report)
    return True


def _row_for_input(
    row: ResearchStrategyCostEvidenceQuorumRouterInput,
    config: ResearchStrategyCostEvidenceQuorumRouterConfig,
) -> ResearchStrategyCostEvidenceQuorumRouterRow:
    cost_efficiency = _inverse_ratio(row.cost_pressure_score)
    evidence_gap = _inverse_ratio(row.evidence_strength_score)
    quorum_gap = _inverse_ratio(row.quorum_score)
    freshness_gap = _inverse_ratio(row.freshness_score)
    router_score = _router_score(
        cost_efficiency_score=cost_efficiency,
        evidence_strength_score=row.evidence_strength_score,
        quorum_score=row.quorum_score,
        freshness_score=row.freshness_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        upstream_reason_codes=row.reason_codes,
        cost_pressure_score=row.cost_pressure_score,
        evidence_strength_score=row.evidence_strength_score,
        quorum_score=row.quorum_score,
        freshness_score=row.freshness_score,
        router_score=router_score,
        config=config,
    )
    return ResearchStrategyCostEvidenceQuorumRouterRow(
        route_digest=_private_ref_digest(row.route_ref),
        cost_pressure_score=row.cost_pressure_score,
        cost_efficiency_score=cost_efficiency,
        evidence_strength_score=row.evidence_strength_score,
        evidence_gap_score=evidence_gap,
        quorum_score=row.quorum_score,
        quorum_gap_score=quorum_gap,
        freshness_score=row.freshness_score,
        freshness_gap_score=freshness_gap,
        router_score=router_score,
        observed_at=row.observed_at,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _row_reason_codes(
    *,
    upstream_reason_codes: tuple[str, ...],
    cost_pressure_score: Decimal,
    evidence_strength_score: Decimal,
    quorum_score: Decimal,
    freshness_score: Decimal,
    router_score: Decimal,
    config: ResearchStrategyCostEvidenceQuorumRouterConfig,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    if cost_pressure_score > config.max_watch_cost_pressure_score:
        reason_codes.append(REASON_COST_PRESSURE_BLOCK)
    elif cost_pressure_score > config.max_pass_cost_pressure_score:
        reason_codes.append(REASON_COST_PRESSURE_WATCH)
    if evidence_strength_score < config.min_watch_evidence_strength_score:
        reason_codes.append(REASON_EVIDENCE_STRENGTH_BLOCK)
    elif evidence_strength_score < config.min_pass_evidence_strength_score:
        reason_codes.append(REASON_EVIDENCE_STRENGTH_WATCH)
    if quorum_score < config.min_watch_quorum_score:
        reason_codes.append(REASON_QUORUM_BLOCK)
    elif quorum_score < config.min_pass_quorum_score:
        reason_codes.append(REASON_QUORUM_WATCH)
    if freshness_score < config.min_watch_freshness_score:
        reason_codes.append(REASON_FRESHNESS_BLOCK)
    elif freshness_score < config.min_pass_freshness_score:
        reason_codes.append(REASON_FRESHNESS_WATCH)
    if router_score < config.watch_min_router_score:
        reason_codes.append(REASON_ROUTER_SCORE_BLOCK)
    elif router_score < config.pass_min_router_score:
        reason_codes.append(REASON_ROUTER_SCORE_WATCH)
    generated = tuple(
        reason_code
        for reason_code in reason_codes
        if reason_code in _GENERATED_ROW_REASON_CODE_SEQUENCE
    )
    if not generated:
        reason_codes.append(REASON_ROUTER_READY_PASS)
    return _normalize_row_reason_codes(tuple(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes):
        return STATUS_BLOCK
    if REASON_ROUTER_READY_PASS in reason_codes:
        return STATUS_PASS
    return STATUS_WATCH


def _report_status(
    rows: tuple[ResearchStrategyCostEvidenceQuorumRouterRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _status_count(
    rows: tuple[ResearchStrategyCostEvidenceQuorumRouterRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _row_sort_key(row: ResearchStrategyCostEvidenceQuorumRouterRow) -> tuple[int, Decimal, str]:
    return (_status_rank(row.status), row.router_score, row.route_digest)


def _status_rank(value: str) -> int:
    return {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[value]


def _reason_code_counts(
    rows: tuple[ResearchStrategyCostEvidenceQuorumRouterRow, ...],
) -> tuple[ResearchStrategyCostEvidenceQuorumRouterReasonCodeCount, ...]:
    total = _decimal_count(len(rows))
    counts: Counter[str] = Counter(
        reason_code for row in rows for reason_code in row.reason_codes
    )
    return tuple(
        ResearchStrategyCostEvidenceQuorumRouterReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            row_ratio=_ratio(_decimal_count(count), total),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )


def _router_score(
    *,
    cost_efficiency_score: Decimal,
    evidence_strength_score: Decimal,
    quorum_score: Decimal,
    freshness_score: Decimal,
    config: ResearchStrategyCostEvidenceQuorumRouterConfig,
) -> Decimal:
    score = (
        cost_efficiency_score * config.cost_efficiency_weight
        + evidence_strength_score * config.evidence_strength_weight
        + quorum_score * config.quorum_weight
        + freshness_score * config.freshness_weight
    )
    return _clamp_ratio(score)


def _validate_row(
    row: ResearchStrategyCostEvidenceQuorumRouterRow,
    config: ResearchStrategyCostEvidenceQuorumRouterConfig | None,
) -> None:
    if config is not None:
        if type(config) is not ResearchStrategyCostEvidenceQuorumRouterConfig:
            raise ValueError(
                "validation_config must be a "
                "ResearchStrategyCostEvidenceQuorumRouterConfig",
            )
        if row.cost_efficiency_score != _inverse_ratio(row.cost_pressure_score):
            raise ValueError("cost_efficiency_score must match cost_pressure_score")
        if row.evidence_gap_score != _inverse_ratio(row.evidence_strength_score):
            raise ValueError("evidence_gap_score must match evidence_strength_score")
        if row.quorum_gap_score != _inverse_ratio(row.quorum_score):
            raise ValueError("quorum_gap_score must match quorum_score")
        if row.freshness_gap_score != _inverse_ratio(row.freshness_score):
            raise ValueError("freshness_gap_score must match freshness_score")
        expected_router_score = _router_score(
            cost_efficiency_score=row.cost_efficiency_score,
            evidence_strength_score=row.evidence_strength_score,
            quorum_score=row.quorum_score,
            freshness_score=row.freshness_score,
            config=config,
        )
        if row.router_score != expected_router_score:
            raise ValueError("router_score must match component scores")
        upstream_reason_codes = tuple(
            reason_code
            for reason_code in row.reason_codes
            if reason_code in _UPSTREAM_REASON_CODE_SEQUENCE
        )
        expected_reasons = _row_reason_codes(
            upstream_reason_codes=upstream_reason_codes,
            cost_pressure_score=row.cost_pressure_score,
            evidence_strength_score=row.evidence_strength_score,
            quorum_score=row.quorum_score,
            freshness_score=row.freshness_score,
            router_score=row.router_score,
            config=config,
        )
        if row.reason_codes != expected_reasons:
            raise ValueError("reason_codes must match row inputs")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if (
        REASON_ROUTER_READY_PASS in row.reason_codes
        and row.reason_codes[-1] != REASON_ROUTER_READY_PASS
    ):
        raise ValueError("pass reason must not be mixed with risk reasons")


def _validate_report(report: ResearchStrategyCostEvidenceQuorumRouterReport) -> None:
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic ordering")
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, STATUS_PASS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, STATUS_WATCH)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, STATUS_BLOCK)):
        raise ValueError("block_count must match rows")
    if report.average_router_score != _average_ratio(
        tuple(row.router_score for row in report.rows),
    ):
        raise ValueError("average_router_score must match rows")
    if report.min_router_score != min((row.router_score for row in report.rows), default=_ZERO):
        raise ValueError("min_router_score must match rows")
    if report.max_cost_pressure_score != max(
        (row.cost_pressure_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_cost_pressure_score must match rows")
    if report.min_evidence_strength_score != min(
        (row.evidence_strength_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_evidence_strength_score must match rows")
    if report.min_quorum_score != min((row.quorum_score for row in report.rows), default=_ZERO):
        raise ValueError("min_quorum_score must match rows")
    if report.min_freshness_score != min(
        (row.freshness_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_freshness_score must match rows")
    expected_counts = _reason_code_counts(report.rows)
    expected_codes = tuple(row.reason_code for row in expected_counts)
    if not report.rows:
        expected_counts = (
            ResearchStrategyCostEvidenceQuorumRouterReasonCodeCount(
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
    inputs: Sequence[ResearchStrategyCostEvidenceQuorumRouterInput],
) -> tuple[ResearchStrategyCostEvidenceQuorumRouterInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    normalized = tuple(inputs)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyCostEvidenceQuorumRouterInput:
            raise ValueError("inputs must contain ResearchStrategyCostEvidenceQuorumRouterInput")
        _require_hard_flags("input", row)
        digest = _private_ref_digest(row.route_ref)
        if digest in seen:
            raise ValueError("inputs must be unique by route digest")
        seen.add(digest)
    return normalized


def _normalize_rows(
    rows: tuple[ResearchStrategyCostEvidenceQuorumRouterRow, ...],
) -> tuple[ResearchStrategyCostEvidenceQuorumRouterRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchStrategyCostEvidenceQuorumRouterRow:
            raise ValueError("rows must contain ResearchStrategyCostEvidenceQuorumRouterRow")
        _require_hard_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic ordering")
    digests = tuple(row.route_digest for row in normalized)
    if len(set(digests)) != len(digests):
        raise ValueError("rows must have unique route digests")
    return normalized


def _normalize_reason_code_counts(
    rows: tuple[ResearchStrategyCostEvidenceQuorumRouterReasonCodeCount, ...],
) -> tuple[ResearchStrategyCostEvidenceQuorumRouterReasonCodeCount, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchStrategyCostEvidenceQuorumRouterReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyCostEvidenceQuorumRouterReasonCodeCount",
            )
        _require_hard_flags("reason count", row)
    if normalized != tuple(
        sorted(normalized, key=lambda item: (-item.count, item.reason_code)),
    ):
        raise ValueError("reason_code_counts must use deterministic ordering")
    if len(set(row.reason_code for row in normalized)) != len(normalized):
        raise ValueError("reason_code_counts must not contain duplicates")
    return normalized


def _normalize_public_notes(
    public_notes: Sequence[ResearchStrategyCostEvidenceQuorumRouterPublicNote],
) -> tuple[ResearchStrategyCostEvidenceQuorumRouterPublicNote, ...]:
    if type(public_notes) not in (list, tuple):
        raise ValueError("public_notes must be a list or tuple")
    normalized = tuple(public_notes)
    for note in normalized:
        if type(note) is not ResearchStrategyCostEvidenceQuorumRouterPublicNote:
            raise ValueError(
                "public_notes must contain "
                "ResearchStrategyCostEvidenceQuorumRouterPublicNote",
            )
        _require_hard_flags("public note", note)
    keys = tuple(note.key for note in normalized)
    if keys != tuple(sorted(keys)):
        raise ValueError("public_notes must be sorted by key")
    if len(set(keys)) != len(keys):
        raise ValueError("public_notes must have unique keys")
    return normalized


def _normalize_upstream_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code, _UPSTREAM_REASON_CODE_SEQUENCE)
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
    normalized = tuple(reason_code for reason_code in _ROW_REASON_CODE_SEQUENCE if reason_code in value)
    if normalized != value:
        raise ValueError("reason_codes must be unique and deterministic")
    if REASON_ROUTER_READY_PASS in value:
        generated = tuple(
            reason_code
            for reason_code in value
            if reason_code in _GENERATED_ROW_REASON_CODE_SEQUENCE
        )
        if generated != (REASON_ROUTER_READY_PASS,):
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


def _report_payload(report: ResearchStrategyCostEvidenceQuorumRouterReport) -> dict[str, object]:
    payload = _report_payload_without_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        status=report.status,
        row_count=report.row_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        average_router_score=report.average_router_score,
        min_router_score=report.min_router_score,
        max_cost_pressure_score=report.max_cost_pressure_score,
        min_evidence_strength_score=report.min_evidence_strength_score,
        min_quorum_score=report.min_quorum_score,
        min_freshness_score=report.min_freshness_score,
        rows=report.rows,
        reason_code_counts=report.reason_code_counts,
        reason_codes=report.reason_codes,
        public_notes=report.public_notes,
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


def _report_digest(report: ResearchStrategyCostEvidenceQuorumRouterReport) -> str:
    return _report_digest_from_values(
        {
            "generated_at": report.generated_at,
            "config_version": report.config_version,
            "status": report.status,
            "row_count": report.row_count,
            "pass_count": report.pass_count,
            "watch_count": report.watch_count,
            "block_count": report.block_count,
            "average_router_score": report.average_router_score,
            "min_router_score": report.min_router_score,
            "max_cost_pressure_score": report.max_cost_pressure_score,
            "min_evidence_strength_score": report.min_evidence_strength_score,
            "min_quorum_score": report.min_quorum_score,
            "min_freshness_score": report.min_freshness_score,
            "rows": report.rows,
            "reason_code_counts": report.reason_code_counts,
            "reason_codes": report.reason_codes,
            "public_notes": report.public_notes,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    return _public_payload_digest(_report_payload_without_digest(**dict(values)))


def _public_payload_digest(payload: dict[str, object]) -> str:
    payload_without_digest = {
        key: value for key, value in payload.items() if key != _DIGEST_FIELD
    }
    encoded = json.dumps(
        payload_without_digest,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _validate_payload_digest(payload: dict[str, object]) -> None:
    digest = payload.get(_DIGEST_FIELD)
    if type(digest) is not str or _DIGEST_RE.fullmatch(digest) is None:
        raise ValueError("derived_validation_digest must be a sha256 digest")
    expected = _public_payload_digest(payload)
    if digest != expected:
        raise ValueError("derived_validation_digest mismatch")


def _validate_payload_statuses(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "status" and item not in _STATUS_VALUES:
                raise ValueError("status must be pass, watch, or block")
            _validate_payload_statuses(item)
    elif isinstance(value, list):
        for item in value:
            _validate_payload_statuses(item)


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("decimal values must be exact Decimal instances")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("datetime values must be exact datetime instances")
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("payload contains unsupported JSON value")


def _copy_json_object(value: dict[str, object]) -> dict[str, object]:
    if type(value) is not dict:
        raise ValueError("payload must be a JSON object")
    return {key: _copy_json_value(item) for key, item in value.items()}


def _copy_json_value(value: object) -> object:
    if type(value) is dict:
        return {key: _copy_json_value(item) for key, item in value.items()}
    if type(value) is list:
        return [_copy_json_value(item) for item in value]
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("payload must contain JSON strings, booleans, lists, and objects")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


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


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole number")
    return decimal_value


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count must be an int")
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize(Decimal(value))


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
    decimal_value = _quantize(value)
    if decimal_value < _ZERO:
        return _ZERO
    if decimal_value > _ONE:
        return _ONE
    return decimal_value


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _require_min_threshold_pair(label: str, watch_value: Decimal, pass_value: Decimal) -> None:
    if pass_value < watch_value:
        raise ValueError(f"{label} pass threshold must be at least watch threshold")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if _PUBLIC_IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public identifier")
    return value


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    if len(normalized) > 240:
        raise ValueError(f"{field_name} must be 240 characters or fewer")
    return normalized


def _require_private_ref(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    if len(normalized) > 512:
        raise ValueError(f"{field_name} must be 512 characters or fewer")
    return normalized


def _private_ref_digest(value: str) -> str:
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()}"


def _require_private_digest(field_name: str, value: object) -> str:
    if type(value) is not str or _PRIVATE_DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a private sha256 digest")
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str or _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _require_reason_code(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be a known reason code")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUS_VALUES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _field_value(value: object, field_name: str) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    raise ValueError(f"{field_name} is required")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if _field_value(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(label, field.name)
            _reject_unsafe_public_payload(label, getattr(value, field.name))
        return
    if isinstance(value, Mapping):
        if not allow_json_containers and type(value) is not dict:
            raise ValueError(f"{label} must use plain public payload containers")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} public fields must be strings")
            _reject_unsafe_public_key(label, key)
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str and _has_unsafe_public_fragment(value):
        raise ValueError(f"unsafe public value in {label}")


def _reject_unsafe_public_key(label: str, key: str) -> None:
    if _has_unsafe_public_fragment(key):
        raise ValueError(f"unsafe public field in {label}")


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.casefold()
    return any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS)


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_COST_EVIDENCE_QUORUM_ROUTER_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_COST_EVIDENCE_QUORUM_ROUTER_REPORT_STATUSES",
    "ResearchStrategyCostEvidenceQuorumRouterConfig",
    "ResearchStrategyCostEvidenceQuorumRouterInput",
    "ResearchStrategyCostEvidenceQuorumRouterPublicNote",
    "ResearchStrategyCostEvidenceQuorumRouterReasonCodeCount",
    "ResearchStrategyCostEvidenceQuorumRouterReport",
    "ResearchStrategyCostEvidenceQuorumRouterRow",
    "build_research_strategy_cost_evidence_quorum_router_report",
    "research_strategy_cost_evidence_quorum_router_report_payload",
    "validate_research_strategy_cost_evidence_quorum_router_report_digest",
    "validate_research_strategy_cost_evidence_quorum_router_report_payload",
)
