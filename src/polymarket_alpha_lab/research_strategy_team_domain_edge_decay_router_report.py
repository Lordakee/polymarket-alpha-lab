"""Report-only team-domain edge decay router scorecard."""

from __future__ import annotations

from collections import Counter
from dataclasses import InitVar, asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Iterable


DEFAULT_RESEARCH_STRATEGY_TEAM_DOMAIN_EDGE_DECAY_ROUTER_REPORT_CONFIG_VERSION = (
    "research-strategy-team-domain-edge-decay-router-report-v0"
)
RESEARCH_STRATEGY_TEAM_DOMAIN_EDGE_DECAY_ROUTER_STATUSES = (
    "pass",
    "watch",
    "block",
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

REASON_EDGE_ROUTER_REVIEW_READY = "edge_router_review_ready"
REASON_DOMAIN_ROUTER_REVIEW_REQUESTED = "domain_router_review_requested"
REASON_TEAM_CAPACITY_REVIEW_REQUESTED = "team_capacity_review_requested"
REASON_EDGE_DECAY_ROUTER_PASS = "edge_decay_router_pass"
REASON_ADJUSTED_EDGE_BLOCK = "adjusted_edge_block"
REASON_ADJUSTED_EDGE_WATCH = "adjusted_edge_watch"
REASON_DECAY_PRESSURE_BLOCK = "decay_pressure_block"
REASON_DECAY_PRESSURE_WATCH = "decay_pressure_watch"
REASON_DOMAIN_FIT_BLOCK = "domain_fit_block"
REASON_DOMAIN_FIT_WATCH = "domain_fit_watch"
REASON_EDGE_AGE_BLOCK = "edge_age_block"
REASON_EDGE_AGE_WATCH = "edge_age_watch"
REASON_EDGE_DECAY_BLOCK = "edge_decay_block"
REASON_EDGE_DECAY_WATCH = "edge_decay_watch"
REASON_EVIDENCE_FRESHNESS_BLOCK = "evidence_freshness_block"
REASON_EVIDENCE_FRESHNESS_WATCH = "evidence_freshness_watch"
REASON_TEAM_CAPACITY_BLOCK = "team_capacity_block"
REASON_TEAM_CAPACITY_WATCH = "team_capacity_watch"
REASON_REPORT_PASS = "edge_decay_router_report_pass"
REASON_REPORT_WATCH = "edge_decay_router_report_watch"
REASON_REPORT_BLOCK = "edge_decay_router_report_block"
REASON_NO_INPUTS = "edge_decay_router_no_inputs"
REASON_ADJUSTED_EDGE_REVIEW = "adjusted_edge_review"
REASON_DECAY_PRESSURE_REVIEW = "decay_pressure_review"
REASON_DOMAIN_FIT_REVIEW = "domain_fit_review"
REASON_EDGE_AGE_REVIEW = "edge_age_review"
REASON_EDGE_DECAY_REVIEW = "edge_decay_review"
REASON_EVIDENCE_FRESHNESS_REVIEW = "evidence_freshness_review"
REASON_TEAM_CAPACITY_REVIEW = "team_capacity_review"

UPSTREAM_REASON_CODES = (
    REASON_EDGE_ROUTER_REVIEW_READY,
    REASON_DOMAIN_ROUTER_REVIEW_REQUESTED,
    REASON_TEAM_CAPACITY_REVIEW_REQUESTED,
)
ROW_REASON_CODES = (
    REASON_EDGE_DECAY_ROUTER_PASS,
    REASON_EDGE_ROUTER_REVIEW_READY,
    REASON_DOMAIN_ROUTER_REVIEW_REQUESTED,
    REASON_TEAM_CAPACITY_REVIEW_REQUESTED,
    REASON_ADJUSTED_EDGE_BLOCK,
    REASON_ADJUSTED_EDGE_WATCH,
    REASON_DECAY_PRESSURE_BLOCK,
    REASON_DECAY_PRESSURE_WATCH,
    REASON_DOMAIN_FIT_BLOCK,
    REASON_DOMAIN_FIT_WATCH,
    REASON_EDGE_AGE_BLOCK,
    REASON_EDGE_AGE_WATCH,
    REASON_EDGE_DECAY_BLOCK,
    REASON_EDGE_DECAY_WATCH,
    REASON_EVIDENCE_FRESHNESS_BLOCK,
    REASON_EVIDENCE_FRESHNESS_WATCH,
    REASON_TEAM_CAPACITY_BLOCK,
    REASON_TEAM_CAPACITY_WATCH,
)
REPORT_REASON_CODES = (
    REASON_REPORT_PASS,
    REASON_REPORT_WATCH,
    REASON_REPORT_BLOCK,
    REASON_NO_INPUTS,
    REASON_ADJUSTED_EDGE_REVIEW,
    REASON_DECAY_PRESSURE_REVIEW,
    REASON_DOMAIN_FIT_REVIEW,
    REASON_EDGE_AGE_REVIEW,
    REASON_EDGE_DECAY_REVIEW,
    REASON_EVIDENCE_FRESHNESS_REVIEW,
    REASON_TEAM_CAPACITY_REVIEW,
)

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANT = Decimal("0.000001")
FRESHNESS_BONUS_WEIGHT = Decimal("0.087333")
DECAY_PRESSURE_WEIGHT = Decimal("0.391000")
EDGE_AGE_WEIGHT = Decimal("0.196365")
EDGE_DECAY_WEIGHT = Decimal("0.050000")
WATCH_EDGE_DECAY_RATIO = Decimal("0.200000")
BLOCK_EDGE_DECAY_RATIO = Decimal("0.450000")
DIGEST_FIELD = "derived_validation_digest"
STATUS_VALUES = frozenset(RESEARCH_STRATEGY_TEAM_DOMAIN_EDGE_DECAY_ROUTER_STATUSES)
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
    "DEFAULT_RESEARCH_STRATEGY_TEAM_DOMAIN_EDGE_DECAY_ROUTER_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_TEAM_DOMAIN_EDGE_DECAY_ROUTER_STATUSES",
    "ResearchStrategyTeamDomainEdgeDecayRouterConfig",
    "ResearchStrategyTeamDomainEdgeDecayRouterInput",
    "ResearchStrategyTeamDomainEdgeDecayRouterReasonCodeCount",
    "ResearchStrategyTeamDomainEdgeDecayRouterReport",
    "ResearchStrategyTeamDomainEdgeDecayRouterRow",
    "build_research_strategy_team_domain_edge_decay_router_report",
    "research_strategy_team_domain_edge_decay_router_report_digest",
    "research_strategy_team_domain_edge_decay_router_report_payload",
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
class ResearchStrategyTeamDomainEdgeDecayRouterConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_TEAM_DOMAIN_EDGE_DECAY_ROUTER_REPORT_CONFIG_VERSION
    )
    fresh_edge_age_seconds: Decimal = Decimal("86400.000000")
    stale_edge_age_seconds: Decimal = Decimal("604800.000000")
    min_pass_decay_adjusted_edge_score: Decimal = Decimal("0.650000")
    min_watch_decay_adjusted_edge_score: Decimal = Decimal("0.450000")
    min_pass_domain_fit_score: Decimal = Decimal("0.700000")
    min_watch_domain_fit_score: Decimal = Decimal("0.500000")
    min_pass_team_capacity_score: Decimal = Decimal("0.700000")
    min_watch_team_capacity_score: Decimal = Decimal("0.500000")
    min_pass_evidence_freshness_score: Decimal = Decimal("0.700000")
    min_watch_evidence_freshness_score: Decimal = Decimal("0.500000")
    max_pass_decay_pressure_score: Decimal = Decimal("0.200000")
    max_watch_decay_pressure_score: Decimal = Decimal("0.450000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyTeamDomainEdgeDecayRouterConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_id("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_TEAM_DOMAIN_EDGE_DECAY_ROUTER_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for name in ("fresh_edge_age_seconds", "stale_edge_age_seconds"):
            object.__setattr__(self, name, _require_positive_decimal(name, getattr(self, name)))
        for name in (
            "min_pass_decay_adjusted_edge_score",
            "min_watch_decay_adjusted_edge_score",
            "min_pass_domain_fit_score",
            "min_watch_domain_fit_score",
            "min_pass_team_capacity_score",
            "min_watch_team_capacity_score",
            "min_pass_evidence_freshness_score",
            "min_watch_evidence_freshness_score",
            "max_pass_decay_pressure_score",
            "max_watch_decay_pressure_score",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        if self.fresh_edge_age_seconds > self.stale_edge_age_seconds:
            raise ValueError("fresh_edge_age_seconds must not exceed stale_edge_age_seconds")
        _require_floor_pair(
            "min_pass_decay_adjusted_edge_score",
            self.min_pass_decay_adjusted_edge_score,
            "min_watch_decay_adjusted_edge_score",
            self.min_watch_decay_adjusted_edge_score,
        )
        _require_floor_pair(
            "min_pass_domain_fit_score",
            self.min_pass_domain_fit_score,
            "min_watch_domain_fit_score",
            self.min_watch_domain_fit_score,
        )
        _require_floor_pair(
            "min_pass_team_capacity_score",
            self.min_pass_team_capacity_score,
            "min_watch_team_capacity_score",
            self.min_watch_team_capacity_score,
        )
        _require_floor_pair(
            "min_pass_evidence_freshness_score",
            self.min_pass_evidence_freshness_score,
            "min_watch_evidence_freshness_score",
            self.min_watch_evidence_freshness_score,
        )
        _require_ceiling_pair(
            "max_pass_decay_pressure_score",
            self.max_pass_decay_pressure_score,
            "max_watch_decay_pressure_score",
            self.max_watch_decay_pressure_score,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyTeamDomainEdgeDecayRouterInput(_FinalPublicDataclass):
    route_ref: str
    evaluated_at: datetime
    last_edge_observed_at: datetime
    baseline_edge_score: Decimal
    current_edge_score: Decimal
    domain_fit_score: Decimal
    team_capacity_score: Decimal
    evidence_freshness_score: Decimal
    decay_pressure_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyTeamDomainEdgeDecayRouterInput, "input")
        object.__setattr__(self, "route_ref", _require_private_ref("route_ref", self.route_ref))
        for name in ("evaluated_at", "last_edge_observed_at"):
            object.__setattr__(self, name, _as_utc(name, getattr(self, name)))
        if self.last_edge_observed_at > self.evaluated_at:
            raise ValueError("last_edge_observed_at must not be after evaluated_at")
        for name in (
            "baseline_edge_score",
            "current_edge_score",
            "domain_fit_score",
            "team_capacity_score",
            "evidence_freshness_score",
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
class ResearchStrategyTeamDomainEdgeDecayRouterRow(_FinalPublicDataclass):
    aggregate_row_number: Decimal
    route_digest: str
    evaluated_at: datetime
    edge_age_seconds: Decimal
    edge_age_pressure: Decimal
    baseline_edge_score: Decimal
    current_edge_score: Decimal
    edge_decay_ratio: Decimal
    domain_fit_score: Decimal
    team_capacity_score: Decimal
    evidence_freshness_score: Decimal
    decay_pressure_score: Decimal
    decay_adjusted_edge_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[ResearchStrategyTeamDomainEdgeDecayRouterConfig | None] = None

    def __post_init__(
        self,
        validation_config: ResearchStrategyTeamDomainEdgeDecayRouterConfig | None,
    ) -> None:
        _require_exact_type(self, ResearchStrategyTeamDomainEdgeDecayRouterRow, "row")
        object.__setattr__(
            self,
            "aggregate_row_number",
            _require_positive_count("aggregate_row_number", self.aggregate_row_number),
        )
        object.__setattr__(self, "route_digest", _require_private_digest("route_digest", self.route_digest))
        object.__setattr__(self, "evaluated_at", _as_utc("evaluated_at", self.evaluated_at))
        object.__setattr__(
            self,
            "edge_age_seconds",
            _require_nonnegative_decimal("edge_age_seconds", self.edge_age_seconds),
        )
        for name in (
            "edge_age_pressure",
            "baseline_edge_score",
            "current_edge_score",
            "edge_decay_ratio",
            "domain_fit_score",
            "team_capacity_score",
            "evidence_freshness_score",
            "decay_pressure_score",
            "decay_adjusted_edge_score",
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
class ResearchStrategyTeamDomainEdgeDecayRouterReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyTeamDomainEdgeDecayRouterReasonCodeCount,
            "reason count",
        )
        _require_reason_code("reason_code", self.reason_code, (*ROW_REASON_CODES, REASON_NO_INPUTS))
        object.__setattr__(self, "count", _require_nonnegative_count("count", self.count))
        object.__setattr__(self, "row_ratio", _require_ratio_decimal("row_ratio", self.row_ratio))
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class ResearchStrategyTeamDomainEdgeDecayRouterReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_decay_adjusted_edge_score: Decimal
    lowest_decay_adjusted_edge_score: Decimal
    highest_edge_decay_ratio: Decimal
    highest_edge_age_seconds: Decimal
    highest_decay_pressure_score: Decimal
    lowest_domain_fit_score: Decimal
    lowest_team_capacity_score: Decimal
    lowest_evidence_freshness_score: Decimal
    rows: tuple[ResearchStrategyTeamDomainEdgeDecayRouterRow, ...]
    reason_code_counts: tuple[ResearchStrategyTeamDomainEdgeDecayRouterReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyTeamDomainEdgeDecayRouterReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_id("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_TEAM_DOMAIN_EDGE_DECAY_ROUTER_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for name in ("row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(self, name, _require_nonnegative_count(name, getattr(self, name)))
        for name in (
            "mean_decay_adjusted_edge_score",
            "lowest_decay_adjusted_edge_score",
            "highest_edge_decay_ratio",
            "highest_decay_pressure_score",
            "lowest_domain_fit_score",
            "lowest_team_capacity_score",
            "lowest_evidence_freshness_score",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        object.__setattr__(
            self,
            "highest_edge_age_seconds",
            _require_nonnegative_decimal("highest_edge_age_seconds", self.highest_edge_age_seconds),
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
        return research_strategy_team_domain_edge_decay_router_report_payload(self)


def build_research_strategy_team_domain_edge_decay_router_report(
    inputs: Iterable[ResearchStrategyTeamDomainEdgeDecayRouterInput],
    *,
    generated_at: datetime,
    config: ResearchStrategyTeamDomainEdgeDecayRouterConfig | None = None,
) -> ResearchStrategyTeamDomainEdgeDecayRouterReport:
    cfg = config or ResearchStrategyTeamDomainEdgeDecayRouterConfig()
    if type(cfg) is not ResearchStrategyTeamDomainEdgeDecayRouterConfig:
        raise ValueError("config must be a ResearchStrategyTeamDomainEdgeDecayRouterConfig")
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    normalized = _normalize_inputs(inputs)
    for value in normalized:
        if value.evaluated_at > report_time:
            raise ValueError("evaluated_at must not be after generated_at")
        if value.last_edge_observed_at > report_time:
            raise ValueError("last_edge_observed_at must not be after generated_at")
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
            ResearchStrategyTeamDomainEdgeDecayRouterReasonCodeCount(
                reason_code=REASON_NO_INPUTS,
                count=ONE,
                row_ratio=ONE,
            ),
        )
    return ResearchStrategyTeamDomainEdgeDecayRouterReport(
        generated_at=report_time,
        config_version=cfg.config_version,
        status=_report_status(rows),
        row_count=_count(len(rows)),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        mean_decay_adjusted_edge_score=_mean(
            tuple(row.decay_adjusted_edge_score for row in rows),
        ),
        lowest_decay_adjusted_edge_score=min(
            (row.decay_adjusted_edge_score for row in rows),
            default=ZERO,
        ),
        highest_edge_decay_ratio=max((row.edge_decay_ratio for row in rows), default=ZERO),
        highest_edge_age_seconds=max((row.edge_age_seconds for row in rows), default=ZERO),
        highest_decay_pressure_score=max((row.decay_pressure_score for row in rows), default=ZERO),
        lowest_domain_fit_score=min((row.domain_fit_score for row in rows), default=ZERO),
        lowest_team_capacity_score=min((row.team_capacity_score for row in rows), default=ZERO),
        lowest_evidence_freshness_score=min(
            (row.evidence_freshness_score for row in rows),
            default=ZERO,
        ),
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=_report_reason_codes(rows),
    )


def research_strategy_team_domain_edge_decay_router_report_payload(
    value: ResearchStrategyTeamDomainEdgeDecayRouterReport | dict[str, object],
) -> dict[str, object]:
    if type(value) is ResearchStrategyTeamDomainEdgeDecayRouterReport:
        _require_hard_flags("report", value)
        _verify_digest(value)
        payload = _json_ready(asdict(value))
    elif type(value) is dict:
        _require_hard_flags("payload", _DictFlags(value))
        payload = _copy_json_object(value)
    else:
        raise ValueError(
            "value must be a ResearchStrategyTeamDomainEdgeDecayRouterReport or dict",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _validate_payload_statuses(payload)
    _reject_unsafe_public_payload("payload", payload)
    _validate_payload_digest(payload)
    return payload


def research_strategy_team_domain_edge_decay_router_report_digest(
    report: ResearchStrategyTeamDomainEdgeDecayRouterReport,
) -> str:
    if type(report) is not ResearchStrategyTeamDomainEdgeDecayRouterReport:
        raise ValueError("report must be a ResearchStrategyTeamDomainEdgeDecayRouterReport")
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
    edge_age_seconds: Decimal
    edge_age_pressure: Decimal
    baseline_edge_score: Decimal
    current_edge_score: Decimal
    edge_decay_ratio: Decimal
    domain_fit_score: Decimal
    team_capacity_score: Decimal
    evidence_freshness_score: Decimal
    decay_pressure_score: Decimal
    decay_adjusted_edge_score: Decimal
    status: str
    reason_codes: tuple[str, ...]


def _prepare_row(
    value: ResearchStrategyTeamDomainEdgeDecayRouterInput,
    *,
    config: ResearchStrategyTeamDomainEdgeDecayRouterConfig,
    generated_at: datetime,
) -> _PreparedRow:
    edge_age_seconds = _seconds_between(generated_at, value.last_edge_observed_at)
    edge_age_pressure = _age_pressure(
        edge_age_seconds,
        fresh_age=config.fresh_edge_age_seconds,
        stale_age=config.stale_edge_age_seconds,
    )
    edge_decay_ratio = _edge_decay_ratio(value.baseline_edge_score, value.current_edge_score)
    decay_adjusted_edge_score = _decay_adjusted_edge_score(
        current_edge_score=value.current_edge_score,
        domain_fit_score=value.domain_fit_score,
        team_capacity_score=value.team_capacity_score,
        evidence_freshness_score=value.evidence_freshness_score,
        decay_pressure_score=value.decay_pressure_score,
        edge_age_pressure=edge_age_pressure,
        edge_decay_ratio=edge_decay_ratio,
    )
    reason_codes = _row_reason_codes(
        upstream_reason_codes=value.reason_codes,
        decay_adjusted_edge_score=decay_adjusted_edge_score,
        decay_pressure_score=value.decay_pressure_score,
        domain_fit_score=value.domain_fit_score,
        edge_age_pressure=edge_age_pressure,
        edge_decay_ratio=edge_decay_ratio,
        evidence_freshness_score=value.evidence_freshness_score,
        team_capacity_score=value.team_capacity_score,
        config=config,
    )
    return _PreparedRow(
        route_digest=_private_digest(value.route_ref),
        evaluated_at=value.evaluated_at,
        edge_age_seconds=edge_age_seconds,
        edge_age_pressure=edge_age_pressure,
        baseline_edge_score=value.baseline_edge_score,
        current_edge_score=value.current_edge_score,
        edge_decay_ratio=edge_decay_ratio,
        domain_fit_score=value.domain_fit_score,
        team_capacity_score=value.team_capacity_score,
        evidence_freshness_score=value.evidence_freshness_score,
        decay_pressure_score=value.decay_pressure_score,
        decay_adjusted_edge_score=decay_adjusted_edge_score,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_from_prepared(
    value: _PreparedRow,
    *,
    aggregate_row_number: Decimal,
    config: ResearchStrategyTeamDomainEdgeDecayRouterConfig,
) -> ResearchStrategyTeamDomainEdgeDecayRouterRow:
    return ResearchStrategyTeamDomainEdgeDecayRouterRow(
        aggregate_row_number=aggregate_row_number,
        route_digest=value.route_digest,
        evaluated_at=value.evaluated_at,
        edge_age_seconds=value.edge_age_seconds,
        edge_age_pressure=value.edge_age_pressure,
        baseline_edge_score=value.baseline_edge_score,
        current_edge_score=value.current_edge_score,
        edge_decay_ratio=value.edge_decay_ratio,
        domain_fit_score=value.domain_fit_score,
        team_capacity_score=value.team_capacity_score,
        evidence_freshness_score=value.evidence_freshness_score,
        decay_pressure_score=value.decay_pressure_score,
        decay_adjusted_edge_score=value.decay_adjusted_edge_score,
        status=value.status,
        reason_codes=value.reason_codes,
        validation_config=config,
    )


def _row_reason_codes(
    *,
    upstream_reason_codes: tuple[str, ...],
    decay_adjusted_edge_score: Decimal,
    decay_pressure_score: Decimal,
    domain_fit_score: Decimal,
    edge_age_pressure: Decimal,
    edge_decay_ratio: Decimal,
    evidence_freshness_score: Decimal,
    team_capacity_score: Decimal,
    config: ResearchStrategyTeamDomainEdgeDecayRouterConfig,
) -> tuple[str, ...]:
    codes = list(upstream_reason_codes)
    _append_floor_reason(
        codes,
        value=decay_adjusted_edge_score,
        watch_floor=config.min_watch_decay_adjusted_edge_score,
        pass_floor=config.min_pass_decay_adjusted_edge_score,
        block_code=REASON_ADJUSTED_EDGE_BLOCK,
        watch_code=REASON_ADJUSTED_EDGE_WATCH,
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
        value=domain_fit_score,
        watch_floor=config.min_watch_domain_fit_score,
        pass_floor=config.min_pass_domain_fit_score,
        block_code=REASON_DOMAIN_FIT_BLOCK,
        watch_code=REASON_DOMAIN_FIT_WATCH,
    )
    if edge_age_pressure >= ONE:
        codes.append(REASON_EDGE_AGE_BLOCK)
    elif edge_age_pressure > ZERO:
        codes.append(REASON_EDGE_AGE_WATCH)
    if edge_decay_ratio >= BLOCK_EDGE_DECAY_RATIO:
        codes.append(REASON_EDGE_DECAY_BLOCK)
    elif edge_decay_ratio > WATCH_EDGE_DECAY_RATIO:
        codes.append(REASON_EDGE_DECAY_WATCH)
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
        value=team_capacity_score,
        watch_floor=config.min_watch_team_capacity_score,
        pass_floor=config.min_pass_team_capacity_score,
        block_code=REASON_TEAM_CAPACITY_BLOCK,
        watch_code=REASON_TEAM_CAPACITY_WATCH,
    )
    if not any(_is_generated_row_reason(code) for code in codes):
        codes.insert(0, REASON_EDGE_DECAY_ROUTER_PASS)
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


def _decay_adjusted_edge_score(
    *,
    current_edge_score: Decimal,
    domain_fit_score: Decimal,
    team_capacity_score: Decimal,
    evidence_freshness_score: Decimal,
    decay_pressure_score: Decimal,
    edge_age_pressure: Decimal,
    edge_decay_ratio: Decimal,
) -> Decimal:
    with localcontext() as context:
        context.prec = 64
        quality_score = (
            current_edge_score
            + domain_fit_score
            + team_capacity_score
            + evidence_freshness_score
        ) / Decimal("4.000000")
        freshness_bonus = (
            (ONE - edge_age_pressure)
            * (ONE - decay_pressure_score)
            * FRESHNESS_BONUS_WEIGHT
        )
        adjusted = (
            quality_score
            + freshness_bonus
            - (decay_pressure_score * DECAY_PRESSURE_WEIGHT)
            - (edge_age_pressure * EDGE_AGE_WEIGHT)
            - (edge_decay_ratio * EDGE_DECAY_WEIGHT)
        )
    return _clamp_ratio(adjusted)


def _edge_decay_ratio(baseline_edge_score: Decimal, current_edge_score: Decimal) -> Decimal:
    if baseline_edge_score == ZERO:
        return ZERO
    with localcontext() as context:
        context.prec = 64
        value = (baseline_edge_score - current_edge_score) / baseline_edge_score
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
    return _require_nonnegative_decimal("edge_age_seconds", value)


def _normalize_inputs(
    inputs: Iterable[ResearchStrategyTeamDomainEdgeDecayRouterInput],
) -> tuple[ResearchStrategyTeamDomainEdgeDecayRouterInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Iterable):
        raise ValueError("inputs must be an iterable")
    normalized = tuple(inputs)
    for value in normalized:
        if type(value) is not ResearchStrategyTeamDomainEdgeDecayRouterInput:
            raise ValueError("inputs must contain ResearchStrategyTeamDomainEdgeDecayRouterInput")
        _require_hard_flags("input", value)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchStrategyTeamDomainEdgeDecayRouterRow],
) -> tuple[ResearchStrategyTeamDomainEdgeDecayRouterRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for value in normalized:
        if type(value) is not ResearchStrategyTeamDomainEdgeDecayRouterRow:
            raise ValueError("rows must contain ResearchStrategyTeamDomainEdgeDecayRouterRow")
        _require_hard_flags("row", value)
        _verify_digest(value)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    return normalized


def _normalize_reason_code_counts(
    counts: Iterable[ResearchStrategyTeamDomainEdgeDecayRouterReasonCodeCount],
) -> tuple[ResearchStrategyTeamDomainEdgeDecayRouterReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(counts)
    for value in normalized:
        if type(value) is not ResearchStrategyTeamDomainEdgeDecayRouterReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyTeamDomainEdgeDecayRouterReasonCodeCount",
            )
        _require_hard_flags("reason count", value)
    return tuple(sorted(normalized, key=lambda item: (-item.count, item.reason_code)))


def _reason_code_counts(
    rows: tuple[ResearchStrategyTeamDomainEdgeDecayRouterRow, ...],
) -> tuple[ResearchStrategyTeamDomainEdgeDecayRouterReasonCodeCount, ...]:
    total = _count(len(rows))
    counts: Counter[str] = Counter(reason for row in rows for reason in row.reason_codes)
    return tuple(
        ResearchStrategyTeamDomainEdgeDecayRouterReasonCodeCount(
            reason_code=reason,
            count=_count(count),
            row_ratio=_ratio(_count(count), total),
        )
        for reason, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )


def _report_reason_codes(
    rows: tuple[ResearchStrategyTeamDomainEdgeDecayRouterRow, ...],
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
        ((REASON_ADJUSTED_EDGE_BLOCK, REASON_ADJUSTED_EDGE_WATCH), REASON_ADJUSTED_EDGE_REVIEW),
        ((REASON_DECAY_PRESSURE_BLOCK, REASON_DECAY_PRESSURE_WATCH), REASON_DECAY_PRESSURE_REVIEW),
        ((REASON_DOMAIN_FIT_BLOCK, REASON_DOMAIN_FIT_WATCH), REASON_DOMAIN_FIT_REVIEW),
        ((REASON_EDGE_AGE_BLOCK, REASON_EDGE_AGE_WATCH), REASON_EDGE_AGE_REVIEW),
        ((REASON_EDGE_DECAY_BLOCK, REASON_EDGE_DECAY_WATCH), REASON_EDGE_DECAY_REVIEW),
        (
            (REASON_EVIDENCE_FRESHNESS_BLOCK, REASON_EVIDENCE_FRESHNESS_WATCH),
            REASON_EVIDENCE_FRESHNESS_REVIEW,
        ),
        ((REASON_TEAM_CAPACITY_BLOCK, REASON_TEAM_CAPACITY_WATCH), REASON_TEAM_CAPACITY_REVIEW),
    )
    for row_reasons, report_reason in review_pairs:
        if any(any(reason in row.reason_codes for reason in row_reasons) for row in rows):
            codes.append(report_reason)
    return _normalize_reason_codes("reason_codes", tuple(codes), REPORT_REASON_CODES)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return STATUS_BLOCK
    if REASON_EDGE_DECAY_ROUTER_PASS in reason_codes:
        return STATUS_PASS
    return STATUS_WATCH


def _report_status(rows: tuple[ResearchStrategyTeamDomainEdgeDecayRouterRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _status_count(
    rows: tuple[ResearchStrategyTeamDomainEdgeDecayRouterRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _prepared_sort_key(value: _PreparedRow) -> tuple[int, Decimal, str]:
    return (_status_rank(value.status), value.decay_adjusted_edge_score, value.route_digest)


def _row_sort_key(
    value: ResearchStrategyTeamDomainEdgeDecayRouterRow,
) -> tuple[int, Decimal, str]:
    return (_status_rank(value.status), value.decay_adjusted_edge_score, value.route_digest)


def _status_rank(status: str) -> int:
    return {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[status]


def _is_generated_row_reason(reason_code: str) -> bool:
    return reason_code not in UPSTREAM_REASON_CODES


def _validate_row(
    row: ResearchStrategyTeamDomainEdgeDecayRouterRow,
    config: ResearchStrategyTeamDomainEdgeDecayRouterConfig | None,
) -> None:
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if REASON_EDGE_DECAY_ROUTER_PASS in row.reason_codes and row.status != STATUS_PASS:
        raise ValueError("reason_codes must match status")
    if config is not None:
        expected = _row_reason_codes(
            upstream_reason_codes=tuple(
                reason for reason in row.reason_codes if reason in UPSTREAM_REASON_CODES
            ),
            decay_adjusted_edge_score=row.decay_adjusted_edge_score,
            decay_pressure_score=row.decay_pressure_score,
            domain_fit_score=row.domain_fit_score,
            edge_age_pressure=row.edge_age_pressure,
            edge_decay_ratio=row.edge_decay_ratio,
            evidence_freshness_score=row.evidence_freshness_score,
            team_capacity_score=row.team_capacity_score,
            config=config,
        )
        if row.reason_codes != expected:
            raise ValueError("reason_codes must match row scores")


def _validate_report(report: ResearchStrategyTeamDomainEdgeDecayRouterReport) -> None:
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
        ResearchStrategyTeamDomainEdgeDecayRouterReasonCodeCount(
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
