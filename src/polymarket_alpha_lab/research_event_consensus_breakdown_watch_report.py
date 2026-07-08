"""Pure report-only specialist consensus breakdown watch reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_EVENT_CONSENSUS_BREAKDOWN_WATCH_CONFIG_VERSION = (
    "research-event-consensus-breakdown-watch-report-v0"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SIX = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

ROW_REASON_CODES = (
    "consensus_breakdown_pass",
    "consensus_breakdown_watch_score",
    "consensus_breakdown_block_score",
    "thin_specialist_team",
    "confidence_dispersion_watch",
    "confidence_dispersion_block",
    "evidence_contradiction_watch",
    "evidence_contradiction_block",
    "catalyst_pressure_watch",
    "catalyst_pressure_block",
    "memory_staleness_watch",
    "memory_staleness_block",
    "rule_clarity_watch",
    "rule_clarity_block",
)
REPORT_REASON_CODES = (
    "consensus_breakdown_report_pass",
    "consensus_breakdown_report_watch",
    "consensus_breakdown_report_block",
    "consensus_breakdown_report_empty",
)
UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "".join(("li", "ve")),
    "".join(("au", "th")),
    "".join(("wall", "et")),
    "".join(("or", "der")),
    "".join(("net", "work")),
    "".join(("data", "base")),
    "".join(("per", "sist")),
    "".join(("sign", "ing")),
    "".join(("muta", "tion")),
    "".join(("b", "uy")),
    "".join(("s", "ell")),
    "".join(("tr", "ade")),
    "".join(("reco", "mmend")),
    "".join(("pos", "ition")),
)

__all__ = (
    "DEFAULT_RESEARCH_EVENT_CONSENSUS_BREAKDOWN_WATCH_CONFIG_VERSION",
    "ResearchEventConsensusBreakdownWatchConfig",
    "ResearchEventConsensusBreakdownWatchObservation",
    "ResearchEventConsensusBreakdownWatchRow",
    "ResearchEventConsensusBreakdownWatchReport",
    "build_research_event_consensus_breakdown_watch_report",
    "research_event_consensus_breakdown_watch_report_payload",
    "validate_research_event_consensus_breakdown_watch_report_payload",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls.__bases__ != (_FinalPublicDataclass,):
            raise TypeError("public dataclasses do not support subclassing")
        if not cls.__name__.startswith("ResearchEventConsensusBreakdownWatch"):
            raise TypeError("public dataclasses do not support subclassing")


@dataclass(frozen=True)
class ResearchEventConsensusBreakdownWatchConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_RESEARCH_EVENT_CONSENSUS_BREAKDOWN_WATCH_CONFIG_VERSION
    watch_score_floor: Decimal = Decimal("0.400000")
    block_score_floor: Decimal = Decimal("0.700000")
    confidence_dispersion_weight: Decimal = Decimal("0.250000")
    evidence_contradiction_weight: Decimal = Decimal("0.250000")
    catalyst_pressure_weight: Decimal = Decimal("0.200000")
    memory_staleness_weight: Decimal = Decimal("0.200000")
    rule_ambiguity_weight: Decimal = Decimal("0.100000")
    fresh_memory_age_hours: Decimal = Decimal("12.000000")
    stale_memory_age_hours: Decimal = Decimal("48.000000")
    minimum_team_count: Decimal = Decimal("3.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventConsensusBreakdownWatchConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        for field_name in (
            "watch_score_floor",
            "block_score_floor",
            "confidence_dispersion_weight",
            "evidence_contradiction_weight",
            "catalyst_pressure_weight",
            "memory_staleness_weight",
            "rule_ambiguity_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "fresh_memory_age_hours",
            "stale_memory_age_hours",
            "minimum_team_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_score_floor <= self.watch_score_floor:
            raise ValueError("block_score_floor must exceed watch_score_floor")
        if self.stale_memory_age_hours <= self.fresh_memory_age_hours:
            raise ValueError("stale_memory_age_hours must exceed fresh_memory_age_hours")
        _require_decimal_equal(
            "breakdown pressure weights",
            self.confidence_dispersion_weight
            + self.evidence_contradiction_weight
            + self.catalyst_pressure_weight
            + self.memory_staleness_weight
            + self.rule_ambiguity_weight,
            ONE,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", _payload_value(self))


@dataclass(frozen=True, init=False)
class ResearchEventConsensusBreakdownWatchObservation(_FinalPublicDataclass):
    event_family: str
    consensus_bucket: str
    observed_at: datetime
    team_count: Decimal
    aggregate_confidence_mean: Decimal
    aggregate_confidence_min: Decimal
    aggregate_confidence_max: Decimal
    evidence_contradiction_score: Decimal
    catalyst_pressure_score: Decimal
    memory_age_hours: Decimal
    rule_clarity_score: Decimal
    analysis_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init__(
        self,
        *,
        event_family: str,
        consensus_bucket: str,
        observed_at: datetime,
        team_count: Decimal,
        aggregate_confidence_mean: Decimal,
        aggregate_confidence_min: Decimal,
        aggregate_confidence_max: Decimal,
        evidence_contradiction_score: Decimal,
        catalyst_pressure_score: Decimal,
        memory_age_hours: Decimal,
        rule_clarity_score: Decimal,
        analysis_version: str,
        paper_only: bool = True,
        report_only: bool = True,
        readonly: bool = True,
        **raw_identifier_kwargs: object,
    ) -> None:
        _reject_raw_identifier_kwargs(raw_identifier_kwargs)
        for field_name, value in (
            ("event_family", event_family),
            ("consensus_bucket", consensus_bucket),
            ("observed_at", observed_at),
            ("team_count", team_count),
            ("aggregate_confidence_mean", aggregate_confidence_mean),
            ("aggregate_confidence_min", aggregate_confidence_min),
            ("aggregate_confidence_max", aggregate_confidence_max),
            ("evidence_contradiction_score", evidence_contradiction_score),
            ("catalyst_pressure_score", catalyst_pressure_score),
            ("memory_age_hours", memory_age_hours),
            ("rule_clarity_score", rule_clarity_score),
            ("analysis_version", analysis_version),
            ("paper_only", paper_only),
            ("report_only", report_only),
            ("readonly", readonly),
        ):
            object.__setattr__(self, field_name, value)
        self.__post_init__()

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventConsensusBreakdownWatchObservation,
            "observation",
        )
        for field_name in ("event_family", "consensus_bucket", "analysis_version"):
            object.__setattr__(
                self,
                field_name,
                _require_public_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "team_count",
            _require_nonnegative_decimal("team_count", self.team_count),
        )
        for field_name in (
            "aggregate_confidence_mean",
            "aggregate_confidence_min",
            "aggregate_confidence_max",
            "evidence_contradiction_score",
            "catalyst_pressure_score",
            "rule_clarity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "memory_age_hours",
            _require_nonnegative_decimal("memory_age_hours", self.memory_age_hours),
        )
        if self.aggregate_confidence_min > self.aggregate_confidence_max:
            raise ValueError("aggregate_confidence_min must not exceed max")
        if not (
            self.aggregate_confidence_min
            <= self.aggregate_confidence_mean
            <= self.aggregate_confidence_max
        ):
            raise ValueError("aggregate_confidence_mean must sit within min and max")
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", _payload_value(self))


@dataclass(frozen=True)
class ResearchEventConsensusBreakdownWatchRow(_FinalPublicDataclass):
    rank: Decimal
    event_family: str
    consensus_bucket: str
    observed_at: datetime
    team_count: Decimal
    aggregate_confidence_mean: Decimal
    aggregate_confidence_min: Decimal
    aggregate_confidence_max: Decimal
    confidence_dispersion_score: Decimal
    evidence_contradiction_score: Decimal
    catalyst_pressure_score: Decimal
    memory_age_hours: Decimal
    memory_staleness_score: Decimal
    rule_clarity_score: Decimal
    rule_ambiguity_score: Decimal
    breakdown_pressure_score: Decimal
    breakdown_status: str
    reason_codes: tuple[str, ...]
    analysis_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventConsensusBreakdownWatchRow, "row")
        object.__setattr__(self, "rank", _require_positive_decimal("rank", self.rank))
        for field_name in ("event_family", "consensus_bucket", "analysis_version"):
            object.__setattr__(
                self,
                field_name,
                _require_public_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "team_count",
            _require_nonnegative_decimal("team_count", self.team_count),
        )
        object.__setattr__(
            self,
            "memory_age_hours",
            _require_nonnegative_decimal("memory_age_hours", self.memory_age_hours),
        )
        for field_name in (
            "aggregate_confidence_mean",
            "aggregate_confidence_min",
            "aggregate_confidence_max",
            "confidence_dispersion_score",
            "evidence_contradiction_score",
            "catalyst_pressure_score",
            "memory_staleness_score",
            "rule_clarity_score",
            "rule_ambiguity_score",
            "breakdown_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.aggregate_confidence_min > self.aggregate_confidence_max:
            raise ValueError("aggregate_confidence_min must not exceed max")
        if not (
            self.aggregate_confidence_min
            <= self.aggregate_confidence_mean
            <= self.aggregate_confidence_max
        ):
            raise ValueError("aggregate_confidence_mean must sit within min and max")
        _require_status("breakdown_status", self.breakdown_status)
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", _payload_value(self))


@dataclass(frozen=True)
class ResearchEventConsensusBreakdownWatchReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    report_status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_breakdown_pressure_score: Decimal
    max_breakdown_pressure_score: Decimal
    average_confidence_dispersion_score: Decimal
    max_memory_age_hours: Decimal
    rows: tuple[ResearchEventConsensusBreakdownWatchRow, ...]
    analysis_versions: tuple[tuple[str, str, str], ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventConsensusBreakdownWatchReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        _require_status("report_status", self.report_status)
        for field_name in ("row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_breakdown_pressure_score",
            "max_breakdown_pressure_score",
            "average_confidence_dispersion_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_memory_age_hours",
            _require_nonnegative_decimal("max_memory_age_hours", self.max_memory_age_hours),
        )
        object.__setattr__(self, "rows", _require_rows(self.rows))
        object.__setattr__(
            self,
            "analysis_versions",
            _require_analysis_versions(self.analysis_versions),
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


def build_research_event_consensus_breakdown_watch_report(
    observations: Iterable[ResearchEventConsensusBreakdownWatchObservation],
    *,
    config: ResearchEventConsensusBreakdownWatchConfig | None = None,
    generated_at: datetime,
) -> ResearchEventConsensusBreakdownWatchReport:
    cfg = config or ResearchEventConsensusBreakdownWatchConfig()
    if type(cfg) is not ResearchEventConsensusBreakdownWatchConfig:
        raise ValueError(
            "config must be exactly ResearchEventConsensusBreakdownWatchConfig",
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
        "report_status": status,
        "row_count": _count_decimal(len(rows)),
        "pass_count": _status_count(rows, STATUS_PASS),
        "watch_count": _status_count(rows, STATUS_WATCH),
        "block_count": _status_count(rows, STATUS_BLOCK),
        "average_breakdown_pressure_score": _average(
            row.breakdown_pressure_score for row in rows
        ),
        "max_breakdown_pressure_score": max(
            (row.breakdown_pressure_score for row in rows),
            default=ZERO,
        ),
        "average_confidence_dispersion_score": _average(
            row.confidence_dispersion_score for row in rows
        ),
        "max_memory_age_hours": max(
            (row.memory_age_hours for row in rows),
            default=ZERO,
        ),
        "rows": rows,
        "analysis_versions": tuple(
            sorted(
                (
                    item.event_family,
                    item.consensus_bucket,
                    item.analysis_version,
                )
                for item in normalized
            ),
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
    return ResearchEventConsensusBreakdownWatchReport(**values)


def research_event_consensus_breakdown_watch_report_payload(
    report: ResearchEventConsensusBreakdownWatchReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEventConsensusBreakdownWatchReport:
        raise ValueError(
            "report must be exactly ResearchEventConsensusBreakdownWatchReport",
        )
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("payload", payload)
    _require_matching_digest(payload)
    return payload


def validate_research_event_consensus_breakdown_watch_report_payload(
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
    observation: ResearchEventConsensusBreakdownWatchObservation,
    config: ResearchEventConsensusBreakdownWatchConfig,
) -> ResearchEventConsensusBreakdownWatchRow:
    confidence_dispersion_score = _confidence_dispersion_score(observation)
    memory_staleness_score = _memory_staleness_score(
        observation.memory_age_hours,
        config,
    )
    rule_ambiguity_score = _clamp_ratio(ONE - observation.rule_clarity_score)
    breakdown_pressure_score = _breakdown_pressure_score(
        confidence_dispersion_score=confidence_dispersion_score,
        evidence_contradiction_score=observation.evidence_contradiction_score,
        catalyst_pressure_score=observation.catalyst_pressure_score,
        memory_staleness_score=memory_staleness_score,
        rule_ambiguity_score=rule_ambiguity_score,
        config=config,
    )
    status = _row_status(breakdown_pressure_score, config)
    return ResearchEventConsensusBreakdownWatchRow(
        rank=_count_decimal(rank),
        event_family=observation.event_family,
        consensus_bucket=observation.consensus_bucket,
        observed_at=observation.observed_at,
        team_count=observation.team_count,
        aggregate_confidence_mean=observation.aggregate_confidence_mean,
        aggregate_confidence_min=observation.aggregate_confidence_min,
        aggregate_confidence_max=observation.aggregate_confidence_max,
        confidence_dispersion_score=confidence_dispersion_score,
        evidence_contradiction_score=observation.evidence_contradiction_score,
        catalyst_pressure_score=observation.catalyst_pressure_score,
        memory_age_hours=observation.memory_age_hours,
        memory_staleness_score=memory_staleness_score,
        rule_clarity_score=observation.rule_clarity_score,
        rule_ambiguity_score=rule_ambiguity_score,
        breakdown_pressure_score=breakdown_pressure_score,
        breakdown_status=status,
        reason_codes=_row_reason_codes(
            observation=observation,
            confidence_dispersion_score=confidence_dispersion_score,
            memory_staleness_score=memory_staleness_score,
            rule_ambiguity_score=rule_ambiguity_score,
            breakdown_pressure_score=breakdown_pressure_score,
            config=config,
        ),
        analysis_version=observation.analysis_version,
    )


def _confidence_dispersion_score(
    observation: ResearchEventConsensusBreakdownWatchObservation,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            observation.aggregate_confidence_max - observation.aggregate_confidence_min,
        )


def _memory_staleness_score(
    memory_age_hours: Decimal,
    config: ResearchEventConsensusBreakdownWatchConfig,
) -> Decimal:
    if memory_age_hours <= config.fresh_memory_age_hours:
        return ZERO
    if memory_age_hours >= config.stale_memory_age_hours:
        return ONE
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            (memory_age_hours - config.fresh_memory_age_hours)
            / (config.stale_memory_age_hours - config.fresh_memory_age_hours),
        )


def _breakdown_pressure_score(
    *,
    confidence_dispersion_score: Decimal,
    evidence_contradiction_score: Decimal,
    catalyst_pressure_score: Decimal,
    memory_staleness_score: Decimal,
    rule_ambiguity_score: Decimal,
    config: ResearchEventConsensusBreakdownWatchConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            confidence_dispersion_score * config.confidence_dispersion_weight
            + evidence_contradiction_score * config.evidence_contradiction_weight
            + catalyst_pressure_score * config.catalyst_pressure_weight
            + memory_staleness_score * config.memory_staleness_weight
            + rule_ambiguity_score * config.rule_ambiguity_weight,
        )


def _row_status(
    breakdown_pressure_score: Decimal,
    config: ResearchEventConsensusBreakdownWatchConfig,
) -> str:
    if breakdown_pressure_score >= config.block_score_floor:
        return STATUS_BLOCK
    if breakdown_pressure_score >= config.watch_score_floor:
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    *,
    observation: ResearchEventConsensusBreakdownWatchObservation,
    confidence_dispersion_score: Decimal,
    memory_staleness_score: Decimal,
    rule_ambiguity_score: Decimal,
    breakdown_pressure_score: Decimal,
    config: ResearchEventConsensusBreakdownWatchConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if breakdown_pressure_score >= config.block_score_floor:
        codes.append("consensus_breakdown_block_score")
    elif breakdown_pressure_score >= config.watch_score_floor:
        codes.append("consensus_breakdown_watch_score")
    else:
        codes.append("consensus_breakdown_pass")
    if observation.team_count < config.minimum_team_count:
        codes.append("thin_specialist_team")
    _append_component_reason(
        codes,
        "confidence_dispersion",
        confidence_dispersion_score,
        config,
        breakdown_pressure_score,
    )
    _append_component_reason(
        codes,
        "evidence_contradiction",
        observation.evidence_contradiction_score,
        config,
        breakdown_pressure_score,
    )
    _append_component_reason(
        codes,
        "catalyst_pressure",
        observation.catalyst_pressure_score,
        config,
        breakdown_pressure_score,
    )
    _append_component_reason(
        codes,
        "memory_staleness",
        memory_staleness_score,
        config,
        breakdown_pressure_score,
    )
    _append_component_reason(
        codes,
        "rule_clarity",
        rule_ambiguity_score,
        config,
        breakdown_pressure_score,
    )
    return _require_reason_codes("reason_codes", tuple(codes), ROW_REASON_CODES)


def _append_component_reason(
    codes: list[str],
    prefix: str,
    value: Decimal,
    config: ResearchEventConsensusBreakdownWatchConfig,
    breakdown_pressure_score: Decimal,
) -> None:
    if value >= config.block_score_floor:
        codes.append(f"{prefix}_block")
    elif value >= config.watch_score_floor or (
        value > ZERO and breakdown_pressure_score >= config.watch_score_floor
    ):
        codes.append(f"{prefix}_watch")


def _normalize_observations(
    observations: Iterable[ResearchEventConsensusBreakdownWatchObservation],
) -> tuple[ResearchEventConsensusBreakdownWatchObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable of observations")
    try:
        normalized = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable of observations") from exc
    for item in normalized:
        if type(item) is not ResearchEventConsensusBreakdownWatchObservation:
            raise ValueError(
                "observations must contain ResearchEventConsensusBreakdownWatchObservation",
            )
    keys = [(item.event_family, item.consensus_bucket) for item in normalized]
    if len(set(keys)) != len(keys):
        raise ValueError("observations must not contain duplicate public keys")
    return normalized


def _sorted_observations(
    observations: tuple[ResearchEventConsensusBreakdownWatchObservation, ...],
) -> tuple[ResearchEventConsensusBreakdownWatchObservation, ...]:
    return tuple(sorted(observations, key=lambda item: (item.event_family, item.consensus_bucket)))


def _status_count(
    rows: tuple[ResearchEventConsensusBreakdownWatchRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.breakdown_status == status))


def _report_status(rows: tuple[ResearchEventConsensusBreakdownWatchRow, ...]) -> str:
    if not rows:
        return STATUS_WATCH
    if any(row.breakdown_status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.breakdown_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchEventConsensusBreakdownWatchRow, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("consensus_breakdown_report_empty",)
    if status == STATUS_BLOCK:
        return ("consensus_breakdown_report_block",)
    if status == STATUS_WATCH:
        return ("consensus_breakdown_report_watch",)
    return ("consensus_breakdown_report_pass",)


def _average(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _six(sum(items, ZERO) / Decimal(len(items)))


def _validate_report(report: ResearchEventConsensusBreakdownWatchReport) -> None:
    rows = report.rows
    _require_decimal_equal("row_count", report.row_count, _count_decimal(len(rows)))
    _require_decimal_equal("pass_count", report.pass_count, _status_count(rows, STATUS_PASS))
    _require_decimal_equal("watch_count", report.watch_count, _status_count(rows, STATUS_WATCH))
    _require_decimal_equal("block_count", report.block_count, _status_count(rows, STATUS_BLOCK))
    _require_decimal_equal(
        "average_breakdown_pressure_score",
        report.average_breakdown_pressure_score,
        _average(row.breakdown_pressure_score for row in rows),
    )
    _require_decimal_equal(
        "max_breakdown_pressure_score",
        report.max_breakdown_pressure_score,
        max((row.breakdown_pressure_score for row in rows), default=ZERO),
    )
    _require_decimal_equal(
        "average_confidence_dispersion_score",
        report.average_confidence_dispersion_score,
        _average(row.confidence_dispersion_score for row in rows),
    )
    _require_decimal_equal(
        "max_memory_age_hours",
        report.max_memory_age_hours,
        max((row.memory_age_hours for row in rows), default=ZERO),
    )
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(rows, report.report_status):
        raise ValueError("reason_codes must match rows")
    expected_versions = tuple(
        sorted((row.event_family, row.consensus_bucket, row.analysis_version) for row in rows)
    )
    if report.analysis_versions != expected_versions:
        raise ValueError("analysis_versions must match rows")


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
    _require_digest("derived_validation_digest", payload["derived_validation_digest"])
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
) -> tuple[ResearchEventConsensusBreakdownWatchRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for item in value:
        if type(item) is not ResearchEventConsensusBreakdownWatchRow:
            raise ValueError("rows must contain ResearchEventConsensusBreakdownWatchRow")
    keys = [(item.event_family, item.consensus_bucket) for item in value]
    if len(set(keys)) != len(keys):
        raise ValueError("rows must not contain duplicate public keys")
    if tuple(sorted(value, key=lambda item: (item.event_family, item.consensus_bucket))) != value:
        raise ValueError("rows must be sorted by public keys")
    return value


def _require_analysis_versions(value: object) -> tuple[tuple[str, str, str], ...]:
    if type(value) is not tuple:
        raise ValueError("analysis_versions must be a tuple")
    normalized: list[tuple[str, str, str]] = []
    for item in value:
        if type(item) is not tuple or len(item) != 3:
            raise ValueError("analysis_versions entries must be triples")
        event_family, consensus_bucket, analysis_version = item
        normalized.append(
            (
                _require_public_string("event_family", event_family),
                _require_public_string("consensus_bucket", consensus_bucket),
                _require_public_string("analysis_version", analysis_version),
            ),
        )
    result = tuple(normalized)
    if tuple(sorted(result)) != result:
        raise ValueError("analysis_versions must be sorted")
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
            raise ValueError(f"{name} {flag_name} must be True")


def _reject_raw_identifier_kwargs(values: dict[str, object]) -> None:
    if "event_id" in values:
        raise ValueError("raw event identifiers are not accepted")
    if "market_id" in values:
        raise ValueError("raw market identifiers are not accepted")
    if "source_reference" in values:
        raise ValueError("raw source identifiers are not accepted")
    if values:
        first_key = next(iter(values))
        raise TypeError(f"unexpected public field: {first_key}")
