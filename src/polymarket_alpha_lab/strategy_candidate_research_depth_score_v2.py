"""Readonly Phase 1 research-depth score for strategy candidates."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any, Iterable


DEFAULT_STRATEGY_CANDIDATE_RESEARCH_DEPTH_SCORE_V2_CONFIG_VERSION = (
    "strategy-candidate-research-depth-score-v2"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SIX = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

ROW_REASON_CODES = (
    "research_depth_ready",
    "research_depth_watch_score",
    "research_depth_blocked_score",
    "missing_research_sources",
    "missing_independent_sources",
    "missing_primary_sources",
    "thin_citation_depth",
    "stale_evidence_watch",
    "stale_evidence_blocked",
    "low_source_quality",
    "weak_resolution_alignment",
)
REPORT_REASON_CODES = (
    "research_depth_report_ready",
    "research_depth_report_watch",
    "research_depth_report_blocked",
    "research_depth_report_empty",
)
UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)

__all__ = (
    "DEFAULT_STRATEGY_CANDIDATE_RESEARCH_DEPTH_SCORE_V2_CONFIG_VERSION",
    "StrategyCandidateResearchDepthScoreV2Config",
    "StrategyCandidateResearchDepthScoreV2Observation",
    "StrategyCandidateResearchDepthScoreV2Row",
    "StrategyCandidateResearchDepthScoreV2Report",
    "build_strategy_candidate_research_depth_score_v2",
    "strategy_candidate_research_depth_score_v2_payload",
    "validate_strategy_candidate_research_depth_score_v2_payload",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls.__bases__ != (_FinalPublicDataclass,):
            raise TypeError("public dataclasses do not support subclassing")
        if not cls.__name__.startswith("StrategyCandidateResearchDepthScoreV2"):
            raise TypeError("public dataclasses do not support subclassing")


@dataclass(frozen=True)
class StrategyCandidateResearchDepthScoreV2Config(_FinalPublicDataclass):
    config_version: str = DEFAULT_STRATEGY_CANDIDATE_RESEARCH_DEPTH_SCORE_V2_CONFIG_VERSION
    minimum_source_count: Decimal = Decimal("4.000000")
    minimum_independent_source_count: Decimal = Decimal("2.000000")
    minimum_primary_source_count: Decimal = Decimal("1.000000")
    minimum_citation_count: Decimal = Decimal("6.000000")
    maximum_evidence_age_days: Decimal = Decimal("14.000000")
    minimum_source_quality_score: Decimal = Decimal("0.700000")
    minimum_resolution_alignment_score: Decimal = Decimal("0.700000")
    source_coverage_weight: Decimal = Decimal("0.250000")
    independent_source_weight: Decimal = Decimal("0.200000")
    primary_source_weight: Decimal = Decimal("0.150000")
    citation_depth_weight: Decimal = Decimal("0.150000")
    freshness_weight: Decimal = Decimal("0.150000")
    source_quality_weight: Decimal = Decimal("0.050000")
    resolution_alignment_weight: Decimal = Decimal("0.050000")
    missing_source_penalty_weight: Decimal = Decimal("0.150000")
    stale_evidence_penalty_weight: Decimal = Decimal("0.200000")
    ready_score_floor: Decimal = Decimal("0.750000")
    watch_score_floor: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            StrategyCandidateResearchDepthScoreV2Config,
            "config",
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        for field_name in (
            "minimum_source_count",
            "minimum_independent_source_count",
            "minimum_primary_source_count",
            "minimum_citation_count",
            "maximum_evidence_age_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "minimum_source_quality_score",
            "minimum_resolution_alignment_score",
            "source_coverage_weight",
            "independent_source_weight",
            "primary_source_weight",
            "citation_depth_weight",
            "freshness_weight",
            "source_quality_weight",
            "resolution_alignment_weight",
            "missing_source_penalty_weight",
            "stale_evidence_penalty_weight",
            "ready_score_floor",
            "watch_score_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_decimal_equal(
            "research depth score weights",
            self.source_coverage_weight
            + self.independent_source_weight
            + self.primary_source_weight
            + self.citation_depth_weight
            + self.freshness_weight
            + self.source_quality_weight
            + self.resolution_alignment_weight,
            ONE,
        )
        if self.ready_score_floor < self.watch_score_floor:
            raise ValueError("ready_score_floor must be at least watch_score_floor")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", _payload_value(self))


@dataclass(frozen=True)
class StrategyCandidateResearchDepthScoreV2Observation(_FinalPublicDataclass):
    candidate_id: str
    market_id: str
    observed_at: datetime
    source_count: Decimal
    independent_source_count: Decimal
    primary_source_count: Decimal
    citation_count: Decimal
    current_evidence_age_days: Decimal
    average_source_quality_score: Decimal
    resolution_alignment_score: Decimal
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            StrategyCandidateResearchDepthScoreV2Observation,
            "observation",
        )
        for field_name in ("candidate_id", "market_id", "source_config_version"):
            object.__setattr__(
                self,
                field_name,
                _require_public_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "source_count",
            "independent_source_count",
            "primary_source_count",
            "citation_count",
            "current_evidence_age_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_source_quality_score",
            "resolution_alignment_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.independent_source_count > self.source_count:
            raise ValueError("independent_source_count must not exceed source_count")
        if self.primary_source_count > self.source_count:
            raise ValueError("primary_source_count must not exceed source_count")
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", _payload_value(self))


@dataclass(frozen=True)
class StrategyCandidateResearchDepthScoreV2Row(_FinalPublicDataclass):
    rank: Decimal
    candidate_id: str
    market_id: str
    observed_at: datetime
    source_count: Decimal
    independent_source_count: Decimal
    primary_source_count: Decimal
    citation_count: Decimal
    current_evidence_age_days: Decimal
    source_coverage_score: Decimal
    independent_source_score: Decimal
    primary_source_score: Decimal
    citation_depth_score: Decimal
    evidence_freshness_score: Decimal
    average_source_quality_score: Decimal
    resolution_alignment_score: Decimal
    missing_source_penalty: Decimal
    stale_evidence_penalty: Decimal
    research_depth_score: Decimal
    depth_status: str
    reason_codes: tuple[str, ...]
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyCandidateResearchDepthScoreV2Row, "row")
        object.__setattr__(self, "rank", _require_positive_decimal("rank", self.rank))
        for field_name in ("candidate_id", "market_id", "source_config_version"):
            object.__setattr__(
                self,
                field_name,
                _require_public_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "source_count",
            "independent_source_count",
            "primary_source_count",
            "citation_count",
            "current_evidence_age_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_coverage_score",
            "independent_source_score",
            "primary_source_score",
            "citation_depth_score",
            "evidence_freshness_score",
            "average_source_quality_score",
            "resolution_alignment_score",
            "missing_source_penalty",
            "stale_evidence_penalty",
            "research_depth_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.independent_source_count > self.source_count:
            raise ValueError("independent_source_count must not exceed source_count")
        if self.primary_source_count > self.source_count:
            raise ValueError("primary_source_count must not exceed source_count")
        _require_status("depth_status", self.depth_status)
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", _payload_value(self))


@dataclass(frozen=True)
class StrategyCandidateResearchDepthScoreV2Report(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    depth_status: str
    row_count: Decimal
    ready_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_research_depth_score: Decimal
    average_missing_source_penalty: Decimal
    average_stale_evidence_penalty: Decimal
    max_current_evidence_age_days: Decimal
    rows: tuple[StrategyCandidateResearchDepthScoreV2Row, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyCandidateResearchDepthScoreV2Report, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        _require_status("depth_status", self.depth_status)
        for field_name in ("row_count", "ready_count", "watch_count", "blocked_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_research_depth_score",
            "average_missing_source_penalty",
            "average_stale_evidence_penalty",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_current_evidence_age_days",
            _require_nonnegative_decimal(
                "max_current_evidence_age_days",
                self.max_current_evidence_age_days,
            ),
        )
        object.__setattr__(self, "rows", _require_rows(self.rows))
        object.__setattr__(
            self,
            "source_config_versions",
            _require_source_config_versions(self.source_config_versions),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", _payload_value(self))
        _validate_report(self)
        _require_matching_digest(_payload_value(self))


def build_strategy_candidate_research_depth_score_v2(
    observations: Iterable[StrategyCandidateResearchDepthScoreV2Observation],
    *,
    config: StrategyCandidateResearchDepthScoreV2Config | None = None,
    generated_at: datetime,
) -> StrategyCandidateResearchDepthScoreV2Report:
    cfg = config or StrategyCandidateResearchDepthScoreV2Config()
    if type(cfg) is not StrategyCandidateResearchDepthScoreV2Config:
        raise ValueError(
            "config must be exactly StrategyCandidateResearchDepthScoreV2Config",
        )
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    for item in normalized:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
    rows = tuple(
        _row_for_observation(rank=index, observation=item, config=cfg)
        for index, item in enumerate(_sorted_observations(normalized), start=1)
    )
    status = _report_status(rows)
    values: dict[str, Any] = {
        "generated_at": generated_at_utc,
        "config_version": cfg.config_version,
        "depth_status": status,
        "row_count": _count_decimal(len(rows)),
        "ready_count": _status_count(rows, STATUS_READY),
        "watch_count": _status_count(rows, STATUS_WATCH),
        "blocked_count": _status_count(rows, STATUS_BLOCKED),
        "average_research_depth_score": _average(
            row.research_depth_score for row in rows
        ),
        "average_missing_source_penalty": _average(
            row.missing_source_penalty for row in rows
        ),
        "average_stale_evidence_penalty": _average(
            row.stale_evidence_penalty for row in rows
        ),
        "max_current_evidence_age_days": max(
            (row.current_evidence_age_days for row in rows),
            default=ZERO,
        ),
        "rows": rows,
        "source_config_versions": tuple(
            sorted((item.candidate_id, item.source_config_version) for item in normalized),
        ),
        "reason_codes": _report_reason_codes(rows, status),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    payload = _payload_value(values)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    values["derived_validation_digest"] = _derived_validation_digest(payload)
    return StrategyCandidateResearchDepthScoreV2Report(**values)


def strategy_candidate_research_depth_score_v2_payload(
    report: StrategyCandidateResearchDepthScoreV2Report,
) -> dict[str, Any]:
    if type(report) is not StrategyCandidateResearchDepthScoreV2Report:
        raise ValueError(
            "report must be exactly StrategyCandidateResearchDepthScoreV2Report",
        )
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("payload", payload)
    _require_matching_digest(payload)
    return payload


def validate_strategy_candidate_research_depth_score_v2_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    _reject_unsafe_public_payload("payload", payload)
    _require_payload_hard_flags(payload)
    _require_matching_digest(payload)
    return True


def _row_for_observation(
    *,
    rank: int,
    observation: StrategyCandidateResearchDepthScoreV2Observation,
    config: StrategyCandidateResearchDepthScoreV2Config,
) -> StrategyCandidateResearchDepthScoreV2Row:
    source_coverage_score = _coverage_score(
        observation.source_count,
        config.minimum_source_count,
    )
    independent_source_score = _coverage_score(
        observation.independent_source_count,
        config.minimum_independent_source_count,
    )
    primary_source_score = _coverage_score(
        observation.primary_source_count,
        config.minimum_primary_source_count,
    )
    citation_depth_score = _coverage_score(
        observation.citation_count,
        config.minimum_citation_count,
    )
    evidence_freshness_score = _freshness_score(
        observation.current_evidence_age_days,
        config.maximum_evidence_age_days,
    )
    missing_source_penalty = _missing_source_penalty(source_coverage_score, config)
    stale_evidence_penalty = _stale_evidence_penalty(evidence_freshness_score, config)
    research_depth_score = _research_depth_score(
        source_coverage_score=source_coverage_score,
        independent_source_score=independent_source_score,
        primary_source_score=primary_source_score,
        citation_depth_score=citation_depth_score,
        evidence_freshness_score=evidence_freshness_score,
        average_source_quality_score=observation.average_source_quality_score,
        resolution_alignment_score=observation.resolution_alignment_score,
        missing_source_penalty=missing_source_penalty,
        stale_evidence_penalty=stale_evidence_penalty,
        config=config,
    )
    status = _row_status(research_depth_score, config)
    return StrategyCandidateResearchDepthScoreV2Row(
        rank=_count_decimal(rank),
        candidate_id=observation.candidate_id,
        market_id=observation.market_id,
        observed_at=observation.observed_at,
        source_count=observation.source_count,
        independent_source_count=observation.independent_source_count,
        primary_source_count=observation.primary_source_count,
        citation_count=observation.citation_count,
        current_evidence_age_days=observation.current_evidence_age_days,
        source_coverage_score=source_coverage_score,
        independent_source_score=independent_source_score,
        primary_source_score=primary_source_score,
        citation_depth_score=citation_depth_score,
        evidence_freshness_score=evidence_freshness_score,
        average_source_quality_score=observation.average_source_quality_score,
        resolution_alignment_score=observation.resolution_alignment_score,
        missing_source_penalty=missing_source_penalty,
        stale_evidence_penalty=stale_evidence_penalty,
        research_depth_score=research_depth_score,
        depth_status=status,
        reason_codes=_row_reason_codes(
            observation=observation,
            research_depth_score=research_depth_score,
            evidence_freshness_score=evidence_freshness_score,
            config=config,
        ),
        source_config_version=observation.source_config_version,
    )


def _coverage_score(value: Decimal, target: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(value / target)


def _freshness_score(age_days: Decimal, maximum_age_days: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(ONE - (age_days / maximum_age_days))


def _missing_source_penalty(
    source_coverage_score: Decimal,
    config: StrategyCandidateResearchDepthScoreV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio((ONE - source_coverage_score) * config.missing_source_penalty_weight)


def _stale_evidence_penalty(
    evidence_freshness_score: Decimal,
    config: StrategyCandidateResearchDepthScoreV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio((ONE - evidence_freshness_score) * config.stale_evidence_penalty_weight)


def _research_depth_score(
    *,
    source_coverage_score: Decimal,
    independent_source_score: Decimal,
    primary_source_score: Decimal,
    citation_depth_score: Decimal,
    evidence_freshness_score: Decimal,
    average_source_quality_score: Decimal,
    resolution_alignment_score: Decimal,
    missing_source_penalty: Decimal,
    stale_evidence_penalty: Decimal,
    config: StrategyCandidateResearchDepthScoreV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        weighted_score = (
            source_coverage_score * config.source_coverage_weight
            + independent_source_score * config.independent_source_weight
            + primary_source_score * config.primary_source_weight
            + citation_depth_score * config.citation_depth_weight
            + evidence_freshness_score * config.freshness_weight
            + average_source_quality_score * config.source_quality_weight
            + resolution_alignment_score * config.resolution_alignment_weight
        )
        return _clamp_ratio(weighted_score - missing_source_penalty - stale_evidence_penalty)


def _row_status(
    research_depth_score: Decimal,
    config: StrategyCandidateResearchDepthScoreV2Config,
) -> str:
    if research_depth_score < config.watch_score_floor:
        return STATUS_BLOCKED
    if research_depth_score < config.ready_score_floor:
        return STATUS_WATCH
    return STATUS_READY


def _row_reason_codes(
    *,
    observation: StrategyCandidateResearchDepthScoreV2Observation,
    research_depth_score: Decimal,
    evidence_freshness_score: Decimal,
    config: StrategyCandidateResearchDepthScoreV2Config,
) -> tuple[str, ...]:
    codes: list[str] = []
    if research_depth_score < config.watch_score_floor:
        codes.append("research_depth_blocked_score")
    elif research_depth_score < config.ready_score_floor:
        codes.append("research_depth_watch_score")
    else:
        codes.append("research_depth_ready")
    if observation.source_count < config.minimum_source_count:
        codes.append("missing_research_sources")
    if observation.independent_source_count < config.minimum_independent_source_count:
        codes.append("missing_independent_sources")
    if observation.primary_source_count < config.minimum_primary_source_count:
        codes.append("missing_primary_sources")
    if observation.citation_count < config.minimum_citation_count:
        codes.append("thin_citation_depth")
    if observation.current_evidence_age_days > config.maximum_evidence_age_days:
        codes.append("stale_evidence_blocked")
    elif evidence_freshness_score < config.watch_score_floor:
        codes.append("stale_evidence_watch")
    if observation.average_source_quality_score < config.minimum_source_quality_score:
        codes.append("low_source_quality")
    if observation.resolution_alignment_score < config.minimum_resolution_alignment_score:
        codes.append("weak_resolution_alignment")
    return _require_reason_codes("reason_codes", tuple(codes), ROW_REASON_CODES)


def _normalize_observations(
    observations: Iterable[StrategyCandidateResearchDepthScoreV2Observation],
) -> tuple[StrategyCandidateResearchDepthScoreV2Observation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable of observations")
    try:
        normalized = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable of observations") from exc
    for item in normalized:
        if type(item) is not StrategyCandidateResearchDepthScoreV2Observation:
            raise ValueError(
                "observations must contain StrategyCandidateResearchDepthScoreV2Observation",
            )
    keys = [(item.candidate_id, item.market_id) for item in normalized]
    if len(set(keys)) != len(keys):
        raise ValueError("observations must not contain duplicate candidate_id and market_id")
    return normalized


def _sorted_observations(
    observations: tuple[StrategyCandidateResearchDepthScoreV2Observation, ...],
) -> tuple[StrategyCandidateResearchDepthScoreV2Observation, ...]:
    return tuple(sorted(observations, key=lambda item: (item.candidate_id, item.market_id)))


def _status_count(
    rows: tuple[StrategyCandidateResearchDepthScoreV2Row, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.depth_status == status))


def _report_status(rows: tuple[StrategyCandidateResearchDepthScoreV2Row, ...]) -> str:
    if not rows:
        return STATUS_WATCH
    if any(row.depth_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.depth_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_READY


def _report_reason_codes(
    rows: tuple[StrategyCandidateResearchDepthScoreV2Row, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("research_depth_report_empty",)
    if status == STATUS_BLOCKED:
        return ("research_depth_report_blocked",)
    if status == STATUS_WATCH:
        return ("research_depth_report_watch",)
    return ("research_depth_report_ready",)


def _average(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _six(sum(items, ZERO) / Decimal(len(items)))


def _validate_report(report: StrategyCandidateResearchDepthScoreV2Report) -> None:
    rows = report.rows
    _require_decimal_equal("row_count", report.row_count, _count_decimal(len(rows)))
    _require_decimal_equal("ready_count", report.ready_count, _status_count(rows, STATUS_READY))
    _require_decimal_equal("watch_count", report.watch_count, _status_count(rows, STATUS_WATCH))
    _require_decimal_equal(
        "blocked_count",
        report.blocked_count,
        _status_count(rows, STATUS_BLOCKED),
    )
    _require_decimal_equal(
        "average_research_depth_score",
        report.average_research_depth_score,
        _average(row.research_depth_score for row in rows),
    )
    _require_decimal_equal(
        "average_missing_source_penalty",
        report.average_missing_source_penalty,
        _average(row.missing_source_penalty for row in rows),
    )
    _require_decimal_equal(
        "average_stale_evidence_penalty",
        report.average_stale_evidence_penalty,
        _average(row.stale_evidence_penalty for row in rows),
    )
    expected_max_age = max((row.current_evidence_age_days for row in rows), default=ZERO)
    _require_decimal_equal(
        "max_current_evidence_age_days",
        report.max_current_evidence_age_days,
        expected_max_age,
    )
    if report.depth_status != _report_status(rows):
        raise ValueError("depth_status must match rows")
    if report.reason_codes != _report_reason_codes(rows, report.depth_status):
        raise ValueError("reason_codes must match rows")
    expected_versions = tuple(
        sorted((row.candidate_id, row.source_config_version) for row in rows)
    )
    if report.source_config_versions != expected_versions:
        raise ValueError("source_config_versions must match rows")


def _payload_value(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(
            {field.name: getattr(value, field.name) for field in fields(value)}
        )
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("public payload Decimal values must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is str:
        _require_safe_public_text("public payload value", value)
        return value
    if type(value) is bool or value is None:
        return value
    if type(value) in (int, float):
        raise ValueError("public payload numeric values must use Decimal strings")
    if type(value) is tuple or type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        payload: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _require_safe_public_text("public payload key", key)
            payload[key] = _payload_value(item)
        return payload
    raise ValueError("public payload contains unsupported value")


def _reject_unsafe_public_payload(name: str, value: Any) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _require_safe_public_text(f"{name} key", key)
            _reject_unsafe_public_payload(f"{name}.{key}", item)
        return
    if type(value) is list:
        for item in value:
            _reject_unsafe_public_payload(name, item)
        return
    if type(value) is str:
        _require_safe_public_text(name, value)
        return
    if type(value) in (int, float):
        raise ValueError("public payload numeric values must use Decimal strings")
    if type(value) is bool or value is None:
        return
    raise ValueError("public payload contains unsupported value")


def _require_payload_hard_flags(payload: dict[str, Any]) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if payload.get(flag_name) is not True:
            raise ValueError(f"payload {flag_name} must be True")
    for row in payload.get("rows", []):
        if type(row) is not dict:
            raise ValueError("payload rows must be dicts")
        for flag_name in ("paper_only", "report_only", "readonly"):
            if row.get(flag_name) is not True:
                raise ValueError(f"payload row {flag_name} must be True")


def _require_safe_public_text(name: str, value: str) -> None:
    lower = value.lower()
    if any(fragment in lower for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{name} contains unsafe public surface")


def _derived_validation_digest(payload: dict[str, Any]) -> str:
    material = {
        key: value
        for key, value in payload.items()
        if key != "derived_validation_digest"
    }
    return sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()


def _require_matching_digest(payload: dict[str, Any]) -> None:
    if "derived_validation_digest" not in payload:
        raise ValueError("derived_validation_digest is required")
    _require_digest(
        "derived_validation_digest",
        payload["derived_validation_digest"],
    )
    if payload["derived_validation_digest"] != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest does not match report payload")


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_public_string(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value:
        raise ValueError(f"{name} must be non-empty")
    if value.strip() != value:
        raise ValueError(f"{name} must be canonical")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{name} must be canonical")
    _require_safe_public_text(name, value)
    return value


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _six(value)


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return decimal_value


def _require_nonnegative_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{name} must be positive")
    return decimal_value


def _require_decimal_equal(name: str, actual: Decimal, expected: Decimal) -> None:
    if actual != _six(expected):
        raise ValueError(f"{name} must equal derived value")


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(SIX)


def _six(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(SIX)


def _clamp_ratio(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return _six(value)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_status(name: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{name} must be one of {STATUSES}")
    return value


def _require_reason_codes(
    name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    if not value:
        raise ValueError(f"{name} must not be empty")
    normalized: list[str] = []
    for item in value:
        if type(item) is not str or item not in allowed:
            raise ValueError(f"{name} contains an unsupported reason code")
        normalized.append(item)
    return tuple(normalized)


def _require_rows(
    value: object,
) -> tuple[StrategyCandidateResearchDepthScoreV2Row, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for item in value:
        if type(item) is not StrategyCandidateResearchDepthScoreV2Row:
            raise ValueError("rows must contain StrategyCandidateResearchDepthScoreV2Row")
    keys = [(item.candidate_id, item.market_id) for item in value]
    if len(set(keys)) != len(keys):
        raise ValueError("rows must not contain duplicate candidate_id and market_id")
    if tuple(sorted(value, key=lambda item: (item.candidate_id, item.market_id))) != value:
        raise ValueError("rows must be sorted by candidate_id and market_id")
    return value


def _require_source_config_versions(value: object) -> tuple[tuple[str, str], ...]:
    if type(value) is not tuple:
        raise ValueError("source_config_versions must be a tuple")
    normalized: list[tuple[str, str]] = []
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("source_config_versions entries must be pairs")
        candidate_id, config_version = item
        normalized.append(
            (
                _require_public_string("candidate_id", candidate_id),
                _require_public_string("source_config_version", config_version),
            ),
        )
    result = tuple(normalized)
    if tuple(sorted(result)) != result:
        raise ValueError("source_config_versions must be sorted")
    return result


def _require_digest(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{name} must be a sha256 hex digest")
    if any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{name} must be a sha256 hex digest")
    return value


def _require_hard_flags(name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{flag_name} must be True for {name}")
