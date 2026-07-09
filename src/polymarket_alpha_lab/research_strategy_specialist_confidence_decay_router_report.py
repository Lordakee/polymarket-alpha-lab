"""Report-only specialist confidence decay router scorecard."""

from __future__ import annotations

from collections import Counter
from dataclasses import InitVar, asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Iterable


DEFAULT_RESEARCH_STRATEGY_SPECIALIST_CONFIDENCE_DECAY_ROUTER_REPORT_CONFIG_VERSION = (
    "research-strategy-specialist-confidence-decay-router-report-v0"
)
RESEARCH_STRATEGY_SPECIALIST_CONFIDENCE_DECAY_ROUTER_STATUSES = (
    "pass",
    "watch",
    "block",
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

REASON_CONFIDENCE_ROUTER_REVIEW_READY = "confidence_router_review_ready"
REASON_SPECIALIST_ROUTER_REVIEW_REQUESTED = "specialist_router_review_requested"
REASON_EVIDENCE_ROUTER_REVIEW_REQUESTED = "evidence_router_review_requested"
REASON_SPECIALIST_CONFIDENCE_DECAY_ROUTER_PASS = (
    "specialist_confidence_decay_router_pass"
)
REASON_ADJUSTED_CONFIDENCE_BLOCK = "adjusted_confidence_block"
REASON_ADJUSTED_CONFIDENCE_WATCH = "adjusted_confidence_watch"
REASON_DECAY_PRESSURE_BLOCK = "decay_pressure_block"
REASON_DECAY_PRESSURE_WATCH = "decay_pressure_watch"
REASON_SPECIALIST_RELIABILITY_BLOCK = "specialist_reliability_block"
REASON_SPECIALIST_RELIABILITY_WATCH = "specialist_reliability_watch"
REASON_CONFIDENCE_AGE_BLOCK = "confidence_age_block"
REASON_CONFIDENCE_AGE_WATCH = "confidence_age_watch"
REASON_CONFIDENCE_DECAY_BLOCK = "confidence_decay_block"
REASON_CONFIDENCE_DECAY_WATCH = "confidence_decay_watch"
REASON_EVIDENCE_FRESHNESS_BLOCK = "evidence_freshness_block"
REASON_EVIDENCE_FRESHNESS_WATCH = "evidence_freshness_watch"
REASON_CONSENSUS_ALIGNMENT_BLOCK = "consensus_alignment_block"
REASON_CONSENSUS_ALIGNMENT_WATCH = "consensus_alignment_watch"
REASON_REPORT_PASS = "specialist_confidence_decay_router_report_pass"
REASON_REPORT_WATCH = "specialist_confidence_decay_router_report_watch"
REASON_REPORT_BLOCK = "specialist_confidence_decay_router_report_block"
REASON_NO_INPUTS = "specialist_confidence_decay_router_no_inputs"
REASON_ADJUSTED_CONFIDENCE_REVIEW = "adjusted_confidence_review"
REASON_DECAY_PRESSURE_REVIEW = "decay_pressure_review"
REASON_SPECIALIST_RELIABILITY_REVIEW = "specialist_reliability_review"
REASON_CONFIDENCE_AGE_REVIEW = "confidence_age_review"
REASON_CONFIDENCE_DECAY_REVIEW = "confidence_decay_review"
REASON_EVIDENCE_FRESHNESS_REVIEW = "evidence_freshness_review"
REASON_CONSENSUS_ALIGNMENT_REVIEW = "consensus_alignment_review"

UPSTREAM_REASON_CODES = (
    REASON_CONFIDENCE_ROUTER_REVIEW_READY,
    REASON_SPECIALIST_ROUTER_REVIEW_REQUESTED,
    REASON_EVIDENCE_ROUTER_REVIEW_REQUESTED,
)
ROW_REASON_CODES = (
    REASON_SPECIALIST_CONFIDENCE_DECAY_ROUTER_PASS,
    REASON_CONFIDENCE_ROUTER_REVIEW_READY,
    REASON_SPECIALIST_ROUTER_REVIEW_REQUESTED,
    REASON_EVIDENCE_ROUTER_REVIEW_REQUESTED,
    REASON_ADJUSTED_CONFIDENCE_BLOCK,
    REASON_ADJUSTED_CONFIDENCE_WATCH,
    REASON_DECAY_PRESSURE_BLOCK,
    REASON_DECAY_PRESSURE_WATCH,
    REASON_SPECIALIST_RELIABILITY_BLOCK,
    REASON_SPECIALIST_RELIABILITY_WATCH,
    REASON_CONFIDENCE_AGE_BLOCK,
    REASON_CONFIDENCE_AGE_WATCH,
    REASON_CONFIDENCE_DECAY_BLOCK,
    REASON_CONFIDENCE_DECAY_WATCH,
    REASON_EVIDENCE_FRESHNESS_BLOCK,
    REASON_EVIDENCE_FRESHNESS_WATCH,
    REASON_CONSENSUS_ALIGNMENT_BLOCK,
    REASON_CONSENSUS_ALIGNMENT_WATCH,
)
REPORT_REASON_CODES = (
    REASON_REPORT_PASS,
    REASON_REPORT_WATCH,
    REASON_REPORT_BLOCK,
    REASON_NO_INPUTS,
    REASON_ADJUSTED_CONFIDENCE_REVIEW,
    REASON_DECAY_PRESSURE_REVIEW,
    REASON_SPECIALIST_RELIABILITY_REVIEW,
    REASON_CONFIDENCE_AGE_REVIEW,
    REASON_CONFIDENCE_DECAY_REVIEW,
    REASON_EVIDENCE_FRESHNESS_REVIEW,
    REASON_CONSENSUS_ALIGNMENT_REVIEW,
)

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANT = Decimal("0.000001")
FRESHNESS_BONUS_WEIGHT = Decimal("0.076883")
DECAY_PRESSURE_WEIGHT = Decimal("0.200000")
CONFIDENCE_AGE_WEIGHT = Decimal("0.100000")
CONFIDENCE_DECAY_WEIGHT = Decimal("0.020000")
WATCH_CONFIDENCE_DECAY_RATIO = Decimal("0.200000")
BLOCK_CONFIDENCE_DECAY_RATIO = Decimal("0.450000")
DIGEST_FIELD = "derived_validation_digest"
STATUS_VALUES = frozenset(RESEARCH_STRATEGY_SPECIALIST_CONFIDENCE_DECAY_ROUTER_STATUSES)
FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
PUBLIC_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
PRIVATE_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
UNSAFE_PUBLIC_FRAGMENTS = (
    "raw",
    "candidate",
    "market",
    "slug",
    "question",
    "source",
    "url",
    "text",
    "dsn",
    "database",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "trading",
    "live",
    "position",
    "sizing",
    "recommend",
    "secret",
    "credential",
    "private",
    "http://",
    "https://",
    "://",
)

__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_SPECIALIST_CONFIDENCE_DECAY_ROUTER_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_SPECIALIST_CONFIDENCE_DECAY_ROUTER_STATUSES",
    "ResearchStrategySpecialistConfidenceDecayRouterConfig",
    "ResearchStrategySpecialistConfidenceDecayRouterInput",
    "ResearchStrategySpecialistConfidenceDecayRouterReasonCodeCount",
    "ResearchStrategySpecialistConfidenceDecayRouterReport",
    "ResearchStrategySpecialistConfidenceDecayRouterRow",
    "build_research_strategy_specialist_confidence_decay_router_report",
    "research_strategy_specialist_confidence_decay_router_report_digest",
    "research_strategy_specialist_confidence_decay_router_report_payload",
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
class ResearchStrategySpecialistConfidenceDecayRouterConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_SPECIALIST_CONFIDENCE_DECAY_ROUTER_REPORT_CONFIG_VERSION
    )
    fresh_confidence_age_seconds: Decimal = Decimal("3600.000000")
    stale_confidence_age_seconds: Decimal = Decimal("86400.000000")
    min_pass_decay_adjusted_confidence_score: Decimal = Decimal("0.700000")
    min_watch_decay_adjusted_confidence_score: Decimal = Decimal("0.500000")
    min_pass_specialist_reliability_score: Decimal = Decimal("0.750000")
    min_watch_specialist_reliability_score: Decimal = Decimal("0.550000")
    min_pass_evidence_freshness_score: Decimal = Decimal("0.700000")
    min_watch_evidence_freshness_score: Decimal = Decimal("0.500000")
    min_pass_consensus_alignment_score: Decimal = Decimal("0.700000")
    min_watch_consensus_alignment_score: Decimal = Decimal("0.500000")
    max_pass_decay_pressure_score: Decimal = Decimal("0.200000")
    max_watch_decay_pressure_score: Decimal = Decimal("0.450000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategySpecialistConfidenceDecayRouterConfig,
            "config",
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_id("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_SPECIALIST_CONFIDENCE_DECAY_ROUTER_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for name in ("fresh_confidence_age_seconds", "stale_confidence_age_seconds"):
            object.__setattr__(self, name, _require_positive_decimal(name, getattr(self, name)))
        for name in (
            "min_pass_decay_adjusted_confidence_score",
            "min_watch_decay_adjusted_confidence_score",
            "min_pass_specialist_reliability_score",
            "min_watch_specialist_reliability_score",
            "min_pass_evidence_freshness_score",
            "min_watch_evidence_freshness_score",
            "min_pass_consensus_alignment_score",
            "min_watch_consensus_alignment_score",
            "max_pass_decay_pressure_score",
            "max_watch_decay_pressure_score",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        if self.fresh_confidence_age_seconds > self.stale_confidence_age_seconds:
            raise ValueError(
                "fresh_confidence_age_seconds must not exceed stale_confidence_age_seconds",
            )
        _require_floor_pair(
            "min_pass_decay_adjusted_confidence_score",
            self.min_pass_decay_adjusted_confidence_score,
            "min_watch_decay_adjusted_confidence_score",
            self.min_watch_decay_adjusted_confidence_score,
        )
        _require_floor_pair(
            "min_pass_specialist_reliability_score",
            self.min_pass_specialist_reliability_score,
            "min_watch_specialist_reliability_score",
            self.min_watch_specialist_reliability_score,
        )
        _require_floor_pair(
            "min_pass_evidence_freshness_score",
            self.min_pass_evidence_freshness_score,
            "min_watch_evidence_freshness_score",
            self.min_watch_evidence_freshness_score,
        )
        _require_floor_pair(
            "min_pass_consensus_alignment_score",
            self.min_pass_consensus_alignment_score,
            "min_watch_consensus_alignment_score",
            self.min_watch_consensus_alignment_score,
        )
        _require_ceiling_pair(
            "max_pass_decay_pressure_score",
            self.max_pass_decay_pressure_score,
            "max_watch_decay_pressure_score",
            self.max_watch_decay_pressure_score,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategySpecialistConfidenceDecayRouterInput(_FinalPublicDataclass):
    route_ref: str
    evaluated_at: datetime
    last_confidence_observed_at: datetime
    baseline_confidence_score: Decimal
    current_confidence_score: Decimal
    specialist_reliability_score: Decimal
    evidence_freshness_score: Decimal
    consensus_alignment_score: Decimal
    decay_pressure_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategySpecialistConfidenceDecayRouterInput,
            "input",
        )
        object.__setattr__(self, "route_ref", _require_private_ref("route_ref", self.route_ref))
        for name in ("evaluated_at", "last_confidence_observed_at"):
            object.__setattr__(self, name, _as_utc(name, getattr(self, name)))
        if self.last_confidence_observed_at > self.evaluated_at:
            raise ValueError("last_confidence_observed_at must not be after evaluated_at")
        for name in (
            "baseline_confidence_score",
            "current_confidence_score",
            "specialist_reliability_score",
            "evidence_freshness_score",
            "consensus_alignment_score",
            "decay_pressure_score",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, UPSTREAM_REASON_CODES),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategySpecialistConfidenceDecayRouterRow(_FinalPublicDataclass):
    aggregate_row_number: Decimal
    route_digest: str
    evaluated_at: datetime
    confidence_age_seconds: Decimal
    confidence_age_pressure: Decimal
    baseline_confidence_score: Decimal
    current_confidence_score: Decimal
    confidence_decay_ratio: Decimal
    specialist_reliability_score: Decimal
    evidence_freshness_score: Decimal
    consensus_alignment_score: Decimal
    decay_pressure_score: Decimal
    decay_adjusted_confidence_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[ResearchStrategySpecialistConfidenceDecayRouterConfig | None] = None

    def __post_init__(
        self,
        validation_config: ResearchStrategySpecialistConfidenceDecayRouterConfig | None,
    ) -> None:
        _require_exact_type(
            self,
            ResearchStrategySpecialistConfidenceDecayRouterRow,
            "row",
        )
        object.__setattr__(
            self,
            "aggregate_row_number",
            _require_positive_count("aggregate_row_number", self.aggregate_row_number),
        )
        object.__setattr__(
            self,
            "route_digest",
            _require_private_digest("route_digest", self.route_digest),
        )
        object.__setattr__(self, "evaluated_at", _as_utc("evaluated_at", self.evaluated_at))
        object.__setattr__(
            self,
            "confidence_age_seconds",
            _require_nonnegative_decimal(
                "confidence_age_seconds",
                self.confidence_age_seconds,
            ),
        )
        for name in (
            "confidence_age_pressure",
            "baseline_confidence_score",
            "current_confidence_score",
            "confidence_decay_ratio",
            "specialist_reliability_score",
            "evidence_freshness_score",
            "consensus_alignment_score",
            "decay_pressure_score",
            "decay_adjusted_confidence_score",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("row", self)
        _validate_row(self, validation_config)
        _apply_or_verify_digest(self)


@dataclass(frozen=True)
class ResearchStrategySpecialistConfidenceDecayRouterReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategySpecialistConfidenceDecayRouterReasonCodeCount,
            "reason count",
        )
        _require_reason_code("reason_code", self.reason_code, (*ROW_REASON_CODES, REASON_NO_INPUTS))
        object.__setattr__(self, "count", _require_nonnegative_count("count", self.count))
        object.__setattr__(self, "row_ratio", _require_ratio_decimal("row_ratio", self.row_ratio))
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class ResearchStrategySpecialistConfidenceDecayRouterReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_decay_adjusted_confidence_score: Decimal
    lowest_decay_adjusted_confidence_score: Decimal
    highest_confidence_decay_ratio: Decimal
    highest_confidence_age_seconds: Decimal
    highest_decay_pressure_score: Decimal
    lowest_specialist_reliability_score: Decimal
    lowest_evidence_freshness_score: Decimal
    lowest_consensus_alignment_score: Decimal
    rows: tuple[ResearchStrategySpecialistConfidenceDecayRouterRow, ...]
    reason_code_counts: tuple[
        ResearchStrategySpecialistConfidenceDecayRouterReasonCodeCount,
        ...
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategySpecialistConfidenceDecayRouterReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_id("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_SPECIALIST_CONFIDENCE_DECAY_ROUTER_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for name in ("row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(self, name, _require_nonnegative_count(name, getattr(self, name)))
        for name in (
            "mean_decay_adjusted_confidence_score",
            "lowest_decay_adjusted_confidence_score",
            "highest_confidence_decay_ratio",
            "highest_decay_pressure_score",
            "lowest_specialist_reliability_score",
            "lowest_evidence_freshness_score",
            "lowest_consensus_alignment_score",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        object.__setattr__(
            self,
            "highest_confidence_age_seconds",
            _require_nonnegative_decimal(
                "highest_confidence_age_seconds",
                self.highest_confidence_age_seconds,
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
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        _require_hard_flags("report", self)
        _apply_or_verify_digest(self)
        _validate_report(self)

    @property
    def payload(self) -> dict[str, object]:
        return research_strategy_specialist_confidence_decay_router_report_payload(self)


def build_research_strategy_specialist_confidence_decay_router_report(
    inputs: Iterable[ResearchStrategySpecialistConfidenceDecayRouterInput],
    *,
    generated_at: datetime,
    config: ResearchStrategySpecialistConfidenceDecayRouterConfig | None = None,
) -> ResearchStrategySpecialistConfidenceDecayRouterReport:
    cfg = config or ResearchStrategySpecialistConfidenceDecayRouterConfig()
    if type(cfg) is not ResearchStrategySpecialistConfidenceDecayRouterConfig:
        raise ValueError("config must be a ResearchStrategySpecialistConfidenceDecayRouterConfig")
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    normalized = _normalize_inputs(inputs)
    for value in normalized:
        if value.evaluated_at > report_time:
            raise ValueError("evaluated_at must not be after generated_at")
        if value.last_confidence_observed_at > report_time:
            raise ValueError("last_confidence_observed_at must not be after generated_at")
    prepared = tuple(
        sorted(
            (_prepare_row(value, config=cfg, generated_at=report_time) for value in normalized),
            key=_prepared_sort_key,
        ),
    )
    rows = tuple(
        _row_from_prepared(value, aggregate_row_number=_count(index), config=cfg)
        for index, value in enumerate(prepared, start=1)
    )
    reason_code_counts = _reason_code_counts(rows)
    if not rows:
        reason_code_counts = (
            ResearchStrategySpecialistConfidenceDecayRouterReasonCodeCount(
                reason_code=REASON_NO_INPUTS,
                count=ONE,
                row_ratio=ONE,
            ),
        )
    return ResearchStrategySpecialistConfidenceDecayRouterReport(
        generated_at=report_time,
        config_version=cfg.config_version,
        status=_report_status(rows),
        row_count=_count(len(rows)),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        mean_decay_adjusted_confidence_score=_mean(
            tuple(row.decay_adjusted_confidence_score for row in rows),
        ),
        lowest_decay_adjusted_confidence_score=min(
            (row.decay_adjusted_confidence_score for row in rows),
            default=ZERO,
        ),
        highest_confidence_decay_ratio=max(
            (row.confidence_decay_ratio for row in rows),
            default=ZERO,
        ),
        highest_confidence_age_seconds=max(
            (row.confidence_age_seconds for row in rows),
            default=ZERO,
        ),
        highest_decay_pressure_score=max((row.decay_pressure_score for row in rows), default=ZERO),
        lowest_specialist_reliability_score=min(
            (row.specialist_reliability_score for row in rows),
            default=ZERO,
        ),
        lowest_evidence_freshness_score=min(
            (row.evidence_freshness_score for row in rows),
            default=ZERO,
        ),
        lowest_consensus_alignment_score=min(
            (row.consensus_alignment_score for row in rows),
            default=ZERO,
        ),
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=_report_reason_codes(rows),
    )


def research_strategy_specialist_confidence_decay_router_report_payload(
    value: ResearchStrategySpecialistConfidenceDecayRouterReport | dict[str, object],
) -> dict[str, object]:
    if type(value) is ResearchStrategySpecialistConfidenceDecayRouterReport:
        _require_hard_flags("report", value)
        _verify_digest(value)
        payload = _json_ready(asdict(value))
    elif type(value) is dict:
        _require_hard_flags("payload", _DictFlags(value))
        payload = _copy_json_object(value)
    else:
        raise ValueError(
            "value must be a ResearchStrategySpecialistConfidenceDecayRouterReport or dict",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _validate_payload_statuses(payload)
    _reject_unsafe_public_payload("payload", payload)
    _validate_payload_digest(payload)
    return payload


def research_strategy_specialist_confidence_decay_router_report_digest(
    report: ResearchStrategySpecialistConfidenceDecayRouterReport,
) -> str:
    if type(report) is not ResearchStrategySpecialistConfidenceDecayRouterReport:
        raise ValueError("report must be a ResearchStrategySpecialistConfidenceDecayRouterReport")
    return _digest_for_value(report)


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, object]

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
class _PreparedRow:
    route_digest: str
    evaluated_at: datetime
    confidence_age_seconds: Decimal
    confidence_age_pressure: Decimal
    baseline_confidence_score: Decimal
    current_confidence_score: Decimal
    confidence_decay_ratio: Decimal
    specialist_reliability_score: Decimal
    evidence_freshness_score: Decimal
    consensus_alignment_score: Decimal
    decay_pressure_score: Decimal
    decay_adjusted_confidence_score: Decimal
    status: str
    reason_codes: tuple[str, ...]


def _prepare_row(
    value: ResearchStrategySpecialistConfidenceDecayRouterInput,
    *,
    config: ResearchStrategySpecialistConfidenceDecayRouterConfig,
    generated_at: datetime,
) -> _PreparedRow:
    confidence_age_seconds = _seconds_between(generated_at, value.last_confidence_observed_at)
    confidence_age_pressure = _age_pressure(
        confidence_age_seconds,
        fresh_age=config.fresh_confidence_age_seconds,
        stale_age=config.stale_confidence_age_seconds,
    )
    confidence_decay_ratio = _confidence_decay_ratio(
        value.baseline_confidence_score,
        value.current_confidence_score,
    )
    decay_adjusted_confidence_score = _decay_adjusted_confidence_score(
        current_confidence_score=value.current_confidence_score,
        specialist_reliability_score=value.specialist_reliability_score,
        evidence_freshness_score=value.evidence_freshness_score,
        consensus_alignment_score=value.consensus_alignment_score,
        decay_pressure_score=value.decay_pressure_score,
        confidence_age_pressure=confidence_age_pressure,
        confidence_decay_ratio=confidence_decay_ratio,
    )
    reason_codes = _row_reason_codes(
        upstream_reason_codes=value.reason_codes,
        decay_adjusted_confidence_score=decay_adjusted_confidence_score,
        decay_pressure_score=value.decay_pressure_score,
        specialist_reliability_score=value.specialist_reliability_score,
        confidence_age_pressure=confidence_age_pressure,
        confidence_decay_ratio=confidence_decay_ratio,
        evidence_freshness_score=value.evidence_freshness_score,
        consensus_alignment_score=value.consensus_alignment_score,
        config=config,
    )
    return _PreparedRow(
        route_digest=_private_digest(value.route_ref),
        evaluated_at=value.evaluated_at,
        confidence_age_seconds=confidence_age_seconds,
        confidence_age_pressure=confidence_age_pressure,
        baseline_confidence_score=value.baseline_confidence_score,
        current_confidence_score=value.current_confidence_score,
        confidence_decay_ratio=confidence_decay_ratio,
        specialist_reliability_score=value.specialist_reliability_score,
        evidence_freshness_score=value.evidence_freshness_score,
        consensus_alignment_score=value.consensus_alignment_score,
        decay_pressure_score=value.decay_pressure_score,
        decay_adjusted_confidence_score=decay_adjusted_confidence_score,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_from_prepared(
    value: _PreparedRow,
    *,
    aggregate_row_number: Decimal,
    config: ResearchStrategySpecialistConfidenceDecayRouterConfig,
) -> ResearchStrategySpecialistConfidenceDecayRouterRow:
    return ResearchStrategySpecialistConfidenceDecayRouterRow(
        aggregate_row_number=aggregate_row_number,
        route_digest=value.route_digest,
        evaluated_at=value.evaluated_at,
        confidence_age_seconds=value.confidence_age_seconds,
        confidence_age_pressure=value.confidence_age_pressure,
        baseline_confidence_score=value.baseline_confidence_score,
        current_confidence_score=value.current_confidence_score,
        confidence_decay_ratio=value.confidence_decay_ratio,
        specialist_reliability_score=value.specialist_reliability_score,
        evidence_freshness_score=value.evidence_freshness_score,
        consensus_alignment_score=value.consensus_alignment_score,
        decay_pressure_score=value.decay_pressure_score,
        decay_adjusted_confidence_score=value.decay_adjusted_confidence_score,
        status=value.status,
        reason_codes=value.reason_codes,
        validation_config=config,
    )


def _row_reason_codes(
    *,
    upstream_reason_codes: tuple[str, ...],
    decay_adjusted_confidence_score: Decimal,
    decay_pressure_score: Decimal,
    specialist_reliability_score: Decimal,
    confidence_age_pressure: Decimal,
    confidence_decay_ratio: Decimal,
    evidence_freshness_score: Decimal,
    consensus_alignment_score: Decimal,
    config: ResearchStrategySpecialistConfidenceDecayRouterConfig,
) -> tuple[str, ...]:
    codes = list(upstream_reason_codes)
    _append_floor_reason(
        codes,
        value=decay_adjusted_confidence_score,
        watch_floor=config.min_watch_decay_adjusted_confidence_score,
        pass_floor=config.min_pass_decay_adjusted_confidence_score,
        block_code=REASON_ADJUSTED_CONFIDENCE_BLOCK,
        watch_code=REASON_ADJUSTED_CONFIDENCE_WATCH,
    )
    _append_ceiling_reason(
        codes,
        value=decay_pressure_score,
        pass_ceiling=config.max_pass_decay_pressure_score,
        watch_ceiling=config.max_watch_decay_pressure_score,
        block_code=REASON_DECAY_PRESSURE_BLOCK,
        watch_code=REASON_DECAY_PRESSURE_WATCH,
    )
    _append_floor_reason(
        codes,
        value=specialist_reliability_score,
        watch_floor=config.min_watch_specialist_reliability_score,
        pass_floor=config.min_pass_specialist_reliability_score,
        block_code=REASON_SPECIALIST_RELIABILITY_BLOCK,
        watch_code=REASON_SPECIALIST_RELIABILITY_WATCH,
    )
    if confidence_age_pressure >= ONE:
        codes.append(REASON_CONFIDENCE_AGE_BLOCK)
    elif confidence_age_pressure > ZERO:
        codes.append(REASON_CONFIDENCE_AGE_WATCH)
    if confidence_decay_ratio >= BLOCK_CONFIDENCE_DECAY_RATIO:
        codes.append(REASON_CONFIDENCE_DECAY_BLOCK)
    elif confidence_decay_ratio > WATCH_CONFIDENCE_DECAY_RATIO:
        codes.append(REASON_CONFIDENCE_DECAY_WATCH)
    _append_floor_reason(
        codes,
        value=evidence_freshness_score,
        watch_floor=config.min_watch_evidence_freshness_score,
        pass_floor=config.min_pass_evidence_freshness_score,
        block_code=REASON_EVIDENCE_FRESHNESS_BLOCK,
        watch_code=REASON_EVIDENCE_FRESHNESS_WATCH,
    )
    _append_floor_reason(
        codes,
        value=consensus_alignment_score,
        watch_floor=config.min_watch_consensus_alignment_score,
        pass_floor=config.min_pass_consensus_alignment_score,
        block_code=REASON_CONSENSUS_ALIGNMENT_BLOCK,
        watch_code=REASON_CONSENSUS_ALIGNMENT_WATCH,
    )
    if not any(_is_generated_row_reason(code) for code in codes):
        codes.insert(0, REASON_SPECIALIST_CONFIDENCE_DECAY_ROUTER_PASS)
    return _normalize_reason_codes("reason_codes", tuple(codes), ROW_REASON_CODES)


def _append_floor_reason(
    codes: list[str],
    *,
    value: Decimal,
    watch_floor: Decimal,
    pass_floor: Decimal,
    block_code: str,
    watch_code: str,
) -> None:
    if value < watch_floor:
        codes.append(block_code)
    elif value < pass_floor:
        codes.append(watch_code)


def _append_ceiling_reason(
    codes: list[str],
    *,
    value: Decimal,
    pass_ceiling: Decimal,
    watch_ceiling: Decimal,
    block_code: str,
    watch_code: str,
) -> None:
    if value > watch_ceiling:
        codes.append(block_code)
    elif value > pass_ceiling:
        codes.append(watch_code)


def _decay_adjusted_confidence_score(
    *,
    current_confidence_score: Decimal,
    specialist_reliability_score: Decimal,
    evidence_freshness_score: Decimal,
    consensus_alignment_score: Decimal,
    decay_pressure_score: Decimal,
    confidence_age_pressure: Decimal,
    confidence_decay_ratio: Decimal,
) -> Decimal:
    with localcontext() as context:
        context.prec = 64
        quality_score = (
            current_confidence_score
            + specialist_reliability_score
            + evidence_freshness_score
            + consensus_alignment_score
        ) / Decimal("4.000000")
        freshness_bonus = (
            (ONE - confidence_age_pressure)
            * (ONE - decay_pressure_score)
            * FRESHNESS_BONUS_WEIGHT
        )
        adjusted = (
            quality_score
            + freshness_bonus
            - (decay_pressure_score * DECAY_PRESSURE_WEIGHT)
            - (confidence_age_pressure * CONFIDENCE_AGE_WEIGHT)
            - (confidence_decay_ratio * CONFIDENCE_DECAY_WEIGHT)
        )
    return _clamp_ratio(adjusted)


def _confidence_decay_ratio(
    baseline_confidence_score: Decimal,
    current_confidence_score: Decimal,
) -> Decimal:
    if baseline_confidence_score == ZERO:
        return ZERO
    with localcontext() as context:
        context.prec = 64
        value = (
            baseline_confidence_score - current_confidence_score
        ) / baseline_confidence_score
    return _clamp_ratio(value)


def _age_pressure(
    age_seconds: Decimal,
    *,
    fresh_age: Decimal,
    stale_age: Decimal,
) -> Decimal:
    if age_seconds <= fresh_age:
        return ZERO
    if age_seconds >= stale_age:
        return ONE
    with localcontext() as context:
        context.prec = 64
        value = (age_seconds - fresh_age) / (stale_age - fresh_age)
    return _clamp_ratio(value)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    value = Decimal(delta.days * 86400 + delta.seconds) + (
        Decimal(delta.microseconds) / Decimal("1000000.000000")
    )
    return _require_nonnegative_decimal("confidence_age_seconds", value)


def _normalize_inputs(
    inputs: Iterable[ResearchStrategySpecialistConfidenceDecayRouterInput],
) -> tuple[ResearchStrategySpecialistConfidenceDecayRouterInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Iterable):
        raise ValueError("inputs must be an iterable")
    normalized = tuple(inputs)
    for value in normalized:
        if type(value) is not ResearchStrategySpecialistConfidenceDecayRouterInput:
            raise ValueError(
                "inputs must contain ResearchStrategySpecialistConfidenceDecayRouterInput",
            )
        _require_hard_flags("input", value)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchStrategySpecialistConfidenceDecayRouterRow],
) -> tuple[ResearchStrategySpecialistConfidenceDecayRouterRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for value in normalized:
        if type(value) is not ResearchStrategySpecialistConfidenceDecayRouterRow:
            raise ValueError(
                "rows must contain ResearchStrategySpecialistConfidenceDecayRouterRow",
            )
        _require_hard_flags("row", value)
        _verify_digest(value)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    return normalized


def _normalize_reason_code_counts(
    counts: Iterable[ResearchStrategySpecialistConfidenceDecayRouterReasonCodeCount],
) -> tuple[ResearchStrategySpecialistConfidenceDecayRouterReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(counts)
    for value in normalized:
        if type(value) is not ResearchStrategySpecialistConfidenceDecayRouterReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategySpecialistConfidenceDecayRouterReasonCodeCount",
            )
        _require_hard_flags("reason count", value)
    return tuple(sorted(normalized, key=lambda item: (-item.count, item.reason_code)))


def _reason_code_counts(
    rows: tuple[ResearchStrategySpecialistConfidenceDecayRouterRow, ...],
) -> tuple[ResearchStrategySpecialistConfidenceDecayRouterReasonCodeCount, ...]:
    total = _count(len(rows))
    counts: Counter[str] = Counter(reason for row in rows for reason in row.reason_codes)
    return tuple(
        ResearchStrategySpecialistConfidenceDecayRouterReasonCodeCount(
            reason_code=reason,
            count=_count(count),
            row_ratio=_ratio(_count(count), total),
        )
        for reason, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )


def _report_reason_codes(
    rows: tuple[ResearchStrategySpecialistConfidenceDecayRouterRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (REASON_REPORT_BLOCK, REASON_NO_INPUTS)
    status = _report_status(rows)
    codes: list[str] = [
        {
            STATUS_PASS: REASON_REPORT_PASS,
            STATUS_WATCH: REASON_REPORT_WATCH,
            STATUS_BLOCK: REASON_REPORT_BLOCK,
        }[status],
    ]
    review_pairs = (
        (
            (REASON_ADJUSTED_CONFIDENCE_BLOCK, REASON_ADJUSTED_CONFIDENCE_WATCH),
            REASON_ADJUSTED_CONFIDENCE_REVIEW,
        ),
        (
            (REASON_DECAY_PRESSURE_BLOCK, REASON_DECAY_PRESSURE_WATCH),
            REASON_DECAY_PRESSURE_REVIEW,
        ),
        (
            (REASON_SPECIALIST_RELIABILITY_BLOCK, REASON_SPECIALIST_RELIABILITY_WATCH),
            REASON_SPECIALIST_RELIABILITY_REVIEW,
        ),
        ((REASON_CONFIDENCE_AGE_BLOCK, REASON_CONFIDENCE_AGE_WATCH), REASON_CONFIDENCE_AGE_REVIEW),
        (
            (REASON_CONFIDENCE_DECAY_BLOCK, REASON_CONFIDENCE_DECAY_WATCH),
            REASON_CONFIDENCE_DECAY_REVIEW,
        ),
        (
            (REASON_EVIDENCE_FRESHNESS_BLOCK, REASON_EVIDENCE_FRESHNESS_WATCH),
            REASON_EVIDENCE_FRESHNESS_REVIEW,
        ),
        (
            (REASON_CONSENSUS_ALIGNMENT_BLOCK, REASON_CONSENSUS_ALIGNMENT_WATCH),
            REASON_CONSENSUS_ALIGNMENT_REVIEW,
        ),
    )
    for row_reasons, report_reason in review_pairs:
        if any(any(reason in row.reason_codes for reason in row_reasons) for row in rows):
            codes.append(report_reason)
    return _normalize_reason_codes("reason_codes", tuple(codes), REPORT_REASON_CODES)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return STATUS_BLOCK
    if REASON_SPECIALIST_CONFIDENCE_DECAY_ROUTER_PASS in reason_codes:
        return STATUS_PASS
    return STATUS_WATCH


def _report_status(rows: tuple[ResearchStrategySpecialistConfidenceDecayRouterRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _status_count(
    rows: tuple[ResearchStrategySpecialistConfidenceDecayRouterRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _prepared_sort_key(value: _PreparedRow) -> tuple[int, Decimal, str]:
    return (
        _status_rank(value.status),
        value.decay_adjusted_confidence_score,
        value.route_digest,
    )


def _row_sort_key(
    value: ResearchStrategySpecialistConfidenceDecayRouterRow,
) -> tuple[int, Decimal, str]:
    return (
        _status_rank(value.status),
        value.decay_adjusted_confidence_score,
        value.route_digest,
    )


def _status_rank(status: str) -> int:
    return {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[status]


def _is_generated_row_reason(reason_code: str) -> bool:
    return reason_code not in UPSTREAM_REASON_CODES


def _validate_row(
    row: ResearchStrategySpecialistConfidenceDecayRouterRow,
    config: ResearchStrategySpecialistConfidenceDecayRouterConfig | None,
) -> None:
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if REASON_SPECIALIST_CONFIDENCE_DECAY_ROUTER_PASS in row.reason_codes:
        if row.status != STATUS_PASS:
            raise ValueError("reason_codes must match status")
    if config is not None:
        expected = _row_reason_codes(
            upstream_reason_codes=tuple(
                reason for reason in row.reason_codes if reason in UPSTREAM_REASON_CODES
            ),
            decay_adjusted_confidence_score=row.decay_adjusted_confidence_score,
            decay_pressure_score=row.decay_pressure_score,
            specialist_reliability_score=row.specialist_reliability_score,
            confidence_age_pressure=row.confidence_age_pressure,
            confidence_decay_ratio=row.confidence_decay_ratio,
            evidence_freshness_score=row.evidence_freshness_score,
            consensus_alignment_score=row.consensus_alignment_score,
            config=config,
        )
        if row.reason_codes != expected:
            raise ValueError("reason_codes must match row scores")


def _validate_report(report: ResearchStrategySpecialistConfidenceDecayRouterReport) -> None:
    if report.row_count != _count(len(report.rows)):
        raise ValueError("row_count must match rows")
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
    if report.reason_code_counts != _reason_code_counts(report.rows) and report.rows:
        raise ValueError("reason_code_counts must match rows")
    if not report.rows and report.reason_code_counts != (
        ResearchStrategySpecialistConfidenceDecayRouterReasonCodeCount(
            reason_code=REASON_NO_INPUTS,
            count=ONE,
            row_ratio=ONE,
        ),
    ):
        raise ValueError("reason_code_counts must match empty report")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_public_id(name: str, value: str) -> str:
    if type(value) is not str or not PUBLIC_ID_RE.fullmatch(value):
        raise ValueError(f"{name} must be a public identifier")
    return value


def _require_private_ref(name: str, value: str) -> str:
    if type(value) is not str or value.strip() == "":
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _require_private_digest(name: str, value: str) -> str:
    if type(value) is not str or not PRIVATE_DIGEST_RE.fullmatch(value):
        raise ValueError(f"{name} must be a private sha256 digest")
    return value


def _require_digest(name: str, value: str) -> str:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{name} must be a SHA-256 digest")
    return value


def _require_status(name: str, value: str) -> None:
    if type(value) is not str or value not in STATUS_VALUES:
        raise ValueError(f"{name} must be pass, watch, or block")


def _require_reason_code(name: str, value: str, allowed: tuple[str, ...]) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{name} must be an allowed reason code")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_positive_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _require_nonnegative_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _require_nonnegative_count(name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_decimal(name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be an integer count")
    return normalized


def _require_positive_count(name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_count(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _require_ratio_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{name} must be between zero and one")
    return normalized


def _require_decimal(name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    try:
        return value.quantize(QUANT)
    except InvalidOperation as exc:
        raise ValueError(f"{name} must be quantizable") from exc


def _require_floor_pair(
    pass_name: str,
    pass_value: Decimal,
    watch_name: str,
    watch_value: Decimal,
) -> None:
    if pass_value < watch_value:
        raise ValueError(f"{pass_name} must be at least {watch_name}")


def _require_ceiling_pair(
    pass_name: str,
    pass_value: Decimal,
    watch_name: str,
    watch_value: Decimal,
) -> None:
    if pass_value > watch_value:
        raise ValueError(f"{pass_name} must not exceed {watch_name}")


def _normalize_reason_codes(
    name: str,
    value: Iterable[str],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise ValueError(f"{name} must be an iterable")
    normalized = tuple(value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{name} must not contain duplicates")
    for reason in normalized:
        _require_reason_code(name, reason, allowed)
    return tuple(reason for reason in allowed if reason in normalized)


def _as_utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext() as context:
        context.prec = 64
        return _clamp_ratio(numerator / denominator)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext() as context:
        context.prec = 64
        return _clamp_ratio(sum(values, ZERO) / _count(len(values)))


def _clamp_ratio(value: Decimal) -> Decimal:
    if value <= ZERO:
        return ZERO
    if value >= ONE:
        return ONE
    return value.quantize(QUANT)


def _private_digest(value: str) -> str:
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()}"


def _apply_or_verify_digest(value: object) -> None:
    expected = _digest_for_value(value)
    current = getattr(value, DIGEST_FIELD, None)
    if current == "":
        object.__setattr__(value, DIGEST_FIELD, expected)
        return
    if current != expected:
        raise ValueError("derived_validation_digest mismatch")
    _require_digest(DIGEST_FIELD, current)


def _verify_digest(value: object) -> None:
    if getattr(value, DIGEST_FIELD, None) != _digest_for_value(value):
        raise ValueError("derived_validation_digest mismatch")


def _digest_for_value(value: object) -> str:
    ready = _json_ready(asdict(value))
    if type(ready) is not dict:
        raise ValueError("digest value must be a JSON object")
    unsigned = dict(ready)
    unsigned.pop(DIGEST_FIELD, None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _validate_payload_digest(payload: dict[str, object]) -> None:
    current = payload.get(DIGEST_FIELD)
    if type(current) is not str:
        raise ValueError("derived_validation_digest must be present")
    unsigned = dict(payload)
    unsigned.pop(DIGEST_FIELD, None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    expected = sha256(encoded.encode("utf-8")).hexdigest()
    if current != expected:
        raise ValueError("derived_validation_digest mismatch")


def _validate_payload_statuses(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "status":
                _require_status("status", item)  # type: ignore[arg-type]
            else:
                _validate_payload_statuses(item)
        return
    if isinstance(value, list):
        for item in value:
            _validate_payload_statuses(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if _has_unsafe_fragment(key):
                raise ValueError(f"unsafe public field in {label}")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str and _has_unsafe_fragment(value):
        raise ValueError(f"unsafe public value in {label}")
    if type(value) in (int, float):
        raise ValueError(f"{label} must use Decimal-derived strings")


def _has_unsafe_fragment(value: str) -> bool:
    lowered = value.casefold()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _copy_json_object(value: dict[str, object]) -> dict[str, object]:
    return _json_ready(value)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("Decimal subclasses are not supported")
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(value.quantize(QUANT))
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if type(value) is bool:
        return value
    if type(value) is str:
        return value
    if type(value) in (int, float):
        raise ValueError("numeric JSON values must be Decimal-derived strings")
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")
