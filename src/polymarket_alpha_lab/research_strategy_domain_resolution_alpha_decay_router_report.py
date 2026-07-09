"""Report-only domain resolution alpha decay router scorecard."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_STRATEGY_DOMAIN_RESOLUTION_ALPHA_DECAY_ROUTER_REPORT_CONFIG_VERSION = (
    "research-strategy-domain-resolution-alpha-decay-router-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
RESEARCH_STRATEGY_DOMAIN_RESOLUTION_ALPHA_DECAY_ROUTER_STATUSES = (
    STATUS_PASS,
    STATUS_WATCH,
    STATUS_BLOCK,
)
STATUS_SORT_SEQUENCE = (STATUS_BLOCK, STATUS_WATCH, STATUS_PASS)

REASON_DOMAIN_RESOLUTION_ALPHA_DECAY_ROUTER_PASS = (
    "domain_resolution_alpha_decay_router_pass"
)
REASON_DOMAIN_RESOLUTION_ALPHA_READY = "domain_resolution_alpha_ready"
REASON_DOMAIN_RESOLUTION_RECHECK_REQUESTED = "domain_resolution_recheck_requested"
REASON_ALPHA_DECAY_REVIEW_REQUESTED = "alpha_decay_review_requested"
REASON_ROUTER_SCORE_BLOCK = "domain_resolution_alpha_decay_router_score_block"
REASON_ROUTER_SCORE_WATCH = "domain_resolution_alpha_decay_router_score_watch"
REASON_ALPHA_DECAY_BLOCK = "domain_resolution_alpha_decay_block"
REASON_ALPHA_DECAY_WATCH = "domain_resolution_alpha_decay_watch"
REASON_RESOLUTION_AGE_BLOCK = "domain_resolution_age_block"
REASON_RESOLUTION_AGE_WATCH = "domain_resolution_age_watch"
REASON_RESOLUTION_CONFIDENCE_BLOCK = "domain_resolution_confidence_block"
REASON_RESOLUTION_CONFIDENCE_WATCH = "domain_resolution_confidence_watch"
REASON_DOMAIN_RELIABILITY_BLOCK = "domain_reliability_block"
REASON_DOMAIN_RELIABILITY_WATCH = "domain_reliability_watch"
REASON_DECAY_PRESSURE_BLOCK = "domain_resolution_decay_pressure_block"
REASON_DECAY_PRESSURE_WATCH = "domain_resolution_decay_pressure_watch"

REASON_REPORT_PASS = "domain_resolution_alpha_decay_router_report_pass"
REASON_REPORT_WATCH = "domain_resolution_alpha_decay_router_report_watch"
REASON_REPORT_BLOCK = "domain_resolution_alpha_decay_router_report_block"
REASON_NO_INPUTS = "domain_resolution_alpha_decay_router_no_inputs"
REASON_ROUTER_SCORE_REVIEW = "domain_resolution_alpha_decay_router_score_review"
REASON_ALPHA_DECAY_REVIEW = "domain_resolution_alpha_decay_review"
REASON_RESOLUTION_AGE_REVIEW = "domain_resolution_age_review"
REASON_RESOLUTION_CONFIDENCE_REVIEW = "domain_resolution_confidence_review"
REASON_DOMAIN_RELIABILITY_REVIEW = "domain_reliability_review"
REASON_DECAY_PRESSURE_REVIEW = "domain_resolution_decay_pressure_review"

UPSTREAM_REASON_CODES = (
    REASON_DOMAIN_RESOLUTION_ALPHA_READY,
    REASON_DOMAIN_RESOLUTION_RECHECK_REQUESTED,
    REASON_ALPHA_DECAY_REVIEW_REQUESTED,
)
ROW_REASON_CODE_SEQUENCE = (
    REASON_DOMAIN_RESOLUTION_ALPHA_DECAY_ROUTER_PASS,
    REASON_DOMAIN_RESOLUTION_ALPHA_READY,
    REASON_DOMAIN_RESOLUTION_RECHECK_REQUESTED,
    REASON_ALPHA_DECAY_REVIEW_REQUESTED,
    REASON_ROUTER_SCORE_BLOCK,
    REASON_ROUTER_SCORE_WATCH,
    REASON_ALPHA_DECAY_BLOCK,
    REASON_ALPHA_DECAY_WATCH,
    REASON_RESOLUTION_AGE_BLOCK,
    REASON_RESOLUTION_AGE_WATCH,
    REASON_RESOLUTION_CONFIDENCE_BLOCK,
    REASON_RESOLUTION_CONFIDENCE_WATCH,
    REASON_DOMAIN_RELIABILITY_BLOCK,
    REASON_DOMAIN_RELIABILITY_WATCH,
    REASON_DECAY_PRESSURE_BLOCK,
    REASON_DECAY_PRESSURE_WATCH,
)
COUNT_REASON_CODE_SEQUENCE = (REASON_NO_INPUTS,) + ROW_REASON_CODE_SEQUENCE
REPORT_REASON_CODE_SEQUENCE = (
    REASON_REPORT_BLOCK,
    REASON_NO_INPUTS,
    REASON_REPORT_WATCH,
    REASON_REPORT_PASS,
    REASON_ROUTER_SCORE_REVIEW,
    REASON_ALPHA_DECAY_REVIEW,
    REASON_RESOLUTION_AGE_REVIEW,
    REASON_RESOLUTION_CONFIDENCE_REVIEW,
    REASON_DOMAIN_RELIABILITY_REVIEW,
    REASON_DECAY_PRESSURE_REVIEW,
)

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_UP)
DIGEST_FIELD = "derived_validation_digest"
SHA256_HEX_LENGTH = 64

PUBLIC_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
PRIVATE_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
FLAG_FIELDS = ("paper_only", "report_only", "readonly")
UNSAFE_PUBLIC_FRAGMENTS = (
    "raw",
    "candidate",
    "market_id",
    "market_slug",
    "market_question",
    "market",
    "slug",
    "question",
    "source_url",
    "source_text",
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
    "postgres://",
    "mysql://",
    "jdbc:",
    "://",
)

__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_DOMAIN_RESOLUTION_ALPHA_DECAY_ROUTER_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_DOMAIN_RESOLUTION_ALPHA_DECAY_ROUTER_STATUSES",
    "ResearchStrategyDomainResolutionAlphaDecayRouterConfig",
    "ResearchStrategyDomainResolutionAlphaDecayRouterInput",
    "ResearchStrategyDomainResolutionAlphaDecayRouterReasonCodeCount",
    "ResearchStrategyDomainResolutionAlphaDecayRouterReport",
    "ResearchStrategyDomainResolutionAlphaDecayRouterRow",
    "build_research_strategy_domain_resolution_alpha_decay_router_report",
    "research_strategy_domain_resolution_alpha_decay_router_report_digest",
    "research_strategy_domain_resolution_alpha_decay_router_report_payload",
    "validate_research_strategy_domain_resolution_alpha_decay_router_report_digest",
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
class ResearchStrategyDomainResolutionAlphaDecayRouterConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_DOMAIN_RESOLUTION_ALPHA_DECAY_ROUTER_REPORT_CONFIG_VERSION
    )
    fresh_resolution_age_seconds: Decimal = Decimal("3600.000000")
    stale_resolution_age_seconds: Decimal = Decimal("86400.000000")
    min_pass_router_score: Decimal = Decimal("0.700000")
    min_watch_router_score: Decimal = Decimal("0.500000")
    max_pass_alpha_decay_ratio: Decimal = Decimal("0.200000")
    max_watch_alpha_decay_ratio: Decimal = Decimal("0.450000")
    max_pass_resolution_age_pressure: Decimal = Decimal("0.200000")
    max_watch_resolution_age_pressure: Decimal = Decimal("0.750000")
    min_pass_resolution_confidence_score: Decimal = Decimal("0.750000")
    min_watch_resolution_confidence_score: Decimal = Decimal("0.500000")
    min_pass_domain_reliability_score: Decimal = Decimal("0.700000")
    min_watch_domain_reliability_score: Decimal = Decimal("0.500000")
    max_pass_decay_pressure_score: Decimal = Decimal("0.200000")
    max_watch_decay_pressure_score: Decimal = Decimal("0.450000")
    alpha_retention_weight: Decimal = Decimal("0.300000")
    resolution_confidence_weight: Decimal = Decimal("0.250000")
    domain_reliability_weight: Decimal = Decimal("0.200000")
    freshness_weight: Decimal = Decimal("0.150000")
    decay_relief_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyDomainResolutionAlphaDecayRouterConfig,
            "config",
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_label("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_DOMAIN_RESOLUTION_ALPHA_DECAY_ROUTER_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match the supported config version")
        for name in ("fresh_resolution_age_seconds", "stale_resolution_age_seconds"):
            object.__setattr__(
                self,
                name,
                _require_positive_decimal(name, getattr(self, name)),
            )
        for name in (
            "min_pass_router_score",
            "min_watch_router_score",
            "max_pass_alpha_decay_ratio",
            "max_watch_alpha_decay_ratio",
            "max_pass_resolution_age_pressure",
            "max_watch_resolution_age_pressure",
            "min_pass_resolution_confidence_score",
            "min_watch_resolution_confidence_score",
            "min_pass_domain_reliability_score",
            "min_watch_domain_reliability_score",
            "max_pass_decay_pressure_score",
            "max_watch_decay_pressure_score",
            "alpha_retention_weight",
            "resolution_confidence_weight",
            "domain_reliability_weight",
            "freshness_weight",
            "decay_relief_weight",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        if self.fresh_resolution_age_seconds > self.stale_resolution_age_seconds:
            raise ValueError(
                "fresh_resolution_age_seconds must not exceed stale_resolution_age_seconds",
            )
        _require_floor_pair(
            "min_pass_router_score",
            self.min_pass_router_score,
            "min_watch_router_score",
            self.min_watch_router_score,
        )
        _require_ceiling_pair(
            "max_pass_alpha_decay_ratio",
            self.max_pass_alpha_decay_ratio,
            "max_watch_alpha_decay_ratio",
            self.max_watch_alpha_decay_ratio,
        )
        _require_ceiling_pair(
            "max_pass_resolution_age_pressure",
            self.max_pass_resolution_age_pressure,
            "max_watch_resolution_age_pressure",
            self.max_watch_resolution_age_pressure,
        )
        _require_floor_pair(
            "min_pass_resolution_confidence_score",
            self.min_pass_resolution_confidence_score,
            "min_watch_resolution_confidence_score",
            self.min_watch_resolution_confidence_score,
        )
        _require_floor_pair(
            "min_pass_domain_reliability_score",
            self.min_pass_domain_reliability_score,
            "min_watch_domain_reliability_score",
            self.min_watch_domain_reliability_score,
        )
        _require_ceiling_pair(
            "max_pass_decay_pressure_score",
            self.max_pass_decay_pressure_score,
            "max_watch_decay_pressure_score",
            self.max_watch_decay_pressure_score,
        )
        weight_total = _quantize(
            self.alpha_retention_weight
            + self.resolution_confidence_weight
            + self.domain_reliability_weight
            + self.freshness_weight
            + self.decay_relief_weight,
        )
        if weight_total != ONE:
            raise ValueError("router weights must sum to one")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyDomainResolutionAlphaDecayRouterInput(_FinalPublicDataclass):
    route_ref: str
    evaluated_at: datetime
    last_resolution_observed_at: datetime
    baseline_alpha_score: Decimal
    current_alpha_score: Decimal
    resolution_confidence_score: Decimal
    domain_reliability_score: Decimal
    decay_pressure_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyDomainResolutionAlphaDecayRouterInput,
            "input",
        )
        object.__setattr__(self, "route_ref", _require_private_ref("route_ref", self.route_ref))
        for name in ("evaluated_at", "last_resolution_observed_at"):
            object.__setattr__(self, name, _as_utc(name, getattr(self, name)))
        if self.last_resolution_observed_at > self.evaluated_at:
            raise ValueError("last_resolution_observed_at must not be after evaluated_at")
        for name in (
            "baseline_alpha_score",
            "current_alpha_score",
            "resolution_confidence_score",
            "domain_reliability_score",
            "decay_pressure_score",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                UPSTREAM_REASON_CODES,
                allow_empty=True,
            ),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyDomainResolutionAlphaDecayRouterRow(_FinalPublicDataclass):
    aggregate_row_number: Decimal
    route_digest: str
    evaluated_at: datetime
    resolution_age_seconds: Decimal
    resolution_age_pressure: Decimal
    baseline_alpha_score: Decimal
    current_alpha_score: Decimal
    alpha_decay_ratio: Decimal
    alpha_retention_score: Decimal
    resolution_confidence_score: Decimal
    domain_reliability_score: Decimal
    decay_pressure_score: Decimal
    freshness_score: Decimal
    decay_relief_score: Decimal
    router_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDomainResolutionAlphaDecayRouterRow, "row")
        object.__setattr__(
            self,
            "aggregate_row_number",
            _require_positive_count_decimal(
                "aggregate_row_number",
                self.aggregate_row_number,
            ),
        )
        object.__setattr__(
            self,
            "route_digest",
            _require_private_digest("route_digest", self.route_digest),
        )
        object.__setattr__(self, "evaluated_at", _as_utc("evaluated_at", self.evaluated_at))
        object.__setattr__(
            self,
            "resolution_age_seconds",
            _require_nonnegative_decimal(
                "resolution_age_seconds",
                self.resolution_age_seconds,
            ),
        )
        for name in (
            "resolution_age_pressure",
            "baseline_alpha_score",
            "current_alpha_score",
            "alpha_decay_ratio",
            "alpha_retention_score",
            "resolution_confidence_score",
            "domain_reliability_score",
            "decay_pressure_score",
            "freshness_score",
            "decay_relief_score",
            "router_score",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        object.__setattr__(self, "status", _require_status("status", self.status))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                ROW_REASON_CODE_SEQUENCE,
                allow_empty=False,
            ),
        )
        _require_hard_flags("row", self)
        _validate_row(self)
        _apply_or_verify_digest(self)
        _reject_unsafe_public_payload("row", _payload_value(self))


@dataclass(frozen=True)
class ResearchStrategyDomainResolutionAlphaDecayRouterReasonCodeCount(
    _FinalPublicDataclass,
):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyDomainResolutionAlphaDecayRouterReasonCodeCount,
            "reason_code_count",
        )
        object.__setattr__(
            self,
            "reason_code",
            _require_member("reason_code", self.reason_code, COUNT_REASON_CODE_SEQUENCE),
        )
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(self, "row_ratio", _require_ratio_decimal("row_ratio", self.row_ratio))
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", _payload_value(self))


@dataclass(frozen=True)
class ResearchStrategyDomainResolutionAlphaDecayRouterReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_router_score: Decimal
    lowest_router_score: Decimal
    highest_alpha_decay_ratio: Decimal
    highest_resolution_age_seconds: Decimal
    lowest_resolution_confidence_score: Decimal
    lowest_domain_reliability_score: Decimal
    highest_decay_pressure_score: Decimal
    rows: tuple[ResearchStrategyDomainResolutionAlphaDecayRouterRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyDomainResolutionAlphaDecayRouterReasonCodeCount,
        ...
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDomainResolutionAlphaDecayRouterReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_label("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_DOMAIN_RESOLUTION_ALPHA_DECAY_ROUTER_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match the supported config version")
        object.__setattr__(self, "status", _require_status("status", self.status))
        for name in ("row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_count_decimal(name, getattr(self, name)),
            )
        for name in (
            "mean_router_score",
            "lowest_router_score",
            "highest_alpha_decay_ratio",
            "lowest_resolution_confidence_score",
            "lowest_domain_reliability_score",
            "highest_decay_pressure_score",
        ):
            object.__setattr__(self, name, _require_ratio_decimal(name, getattr(self, name)))
        object.__setattr__(
            self,
            "highest_resolution_age_seconds",
            _require_nonnegative_decimal(
                "highest_resolution_age_seconds",
                self.highest_resolution_age_seconds,
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
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODE_SEQUENCE,
                allow_empty=False,
            ),
        )
        _require_hard_flags("report", self)
        _validate_report(self)
        _apply_or_verify_digest(self)
        _reject_unsafe_public_payload("report", self.public_payload)

    @property
    def public_payload(self) -> dict[str, Any]:
        return research_strategy_domain_resolution_alpha_decay_router_report_payload(self)

    @property
    def payload(self) -> dict[str, Any]:
        return self.public_payload


def build_research_strategy_domain_resolution_alpha_decay_router_report(
    inputs: Iterable[ResearchStrategyDomainResolutionAlphaDecayRouterInput],
    *,
    generated_at: datetime,
    config: ResearchStrategyDomainResolutionAlphaDecayRouterConfig | None = None,
) -> ResearchStrategyDomainResolutionAlphaDecayRouterReport:
    cfg = config or ResearchStrategyDomainResolutionAlphaDecayRouterConfig()
    if type(cfg) is not ResearchStrategyDomainResolutionAlphaDecayRouterConfig:
        raise ValueError("config must be a ResearchStrategyDomainResolutionAlphaDecayRouterConfig")
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    normalized = _normalize_inputs(inputs)
    for value in normalized:
        if value.evaluated_at > report_time:
            raise ValueError("evaluated_at must not be after generated_at")
        if value.last_resolution_observed_at > report_time:
            raise ValueError("last_resolution_observed_at must not be after generated_at")
    prepared = tuple(
        sorted(
            (_prepare_row(value, config=cfg, generated_at=report_time) for value in normalized),
            key=_prepared_sort_key,
        ),
    )
    rows = tuple(
        _row_from_prepared(value, aggregate_row_number=_count_decimal(index))
        for index, value in enumerate(prepared, start=1)
    )
    reason_code_counts = _reason_code_counts(rows)
    if not rows:
        reason_code_counts = (
            ResearchStrategyDomainResolutionAlphaDecayRouterReasonCodeCount(
                reason_code=REASON_NO_INPUTS,
                count=ONE,
                row_ratio=ONE,
            ),
        )
    return ResearchStrategyDomainResolutionAlphaDecayRouterReport(
        generated_at=report_time,
        config_version=cfg.config_version,
        status=_report_status(rows),
        row_count=_count_decimal(len(rows)),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        mean_router_score=_mean_decimal(tuple(row.router_score for row in rows)),
        lowest_router_score=_min_decimal(tuple(row.router_score for row in rows)),
        highest_alpha_decay_ratio=_max_decimal(tuple(row.alpha_decay_ratio for row in rows)),
        highest_resolution_age_seconds=_max_decimal(
            tuple(row.resolution_age_seconds for row in rows),
        ),
        lowest_resolution_confidence_score=_min_decimal(
            tuple(row.resolution_confidence_score for row in rows),
        ),
        lowest_domain_reliability_score=_min_decimal(
            tuple(row.domain_reliability_score for row in rows),
        ),
        highest_decay_pressure_score=_max_decimal(
            tuple(row.decay_pressure_score for row in rows),
        ),
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=_report_reason_codes(rows),
    )


def research_strategy_domain_resolution_alpha_decay_router_report_payload(
    value: ResearchStrategyDomainResolutionAlphaDecayRouterReport | dict[str, Any],
) -> dict[str, Any]:
    if type(value) is ResearchStrategyDomainResolutionAlphaDecayRouterReport:
        _require_hard_flags("report", value)
        _verify_digest(value)
        payload = _payload_value(value)
    elif type(value) is dict:
        payload = _copy_json_object(value)
    else:
        raise ValueError(
            "value must be a ResearchStrategyDomainResolutionAlphaDecayRouterReport or dict",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _validate_payload_statuses(payload)
    _reject_unsafe_public_payload("payload", payload)
    _validate_payload_digest(payload)
    return payload


def research_strategy_domain_resolution_alpha_decay_router_report_digest(
    report: ResearchStrategyDomainResolutionAlphaDecayRouterReport,
) -> str:
    if type(report) is not ResearchStrategyDomainResolutionAlphaDecayRouterReport:
        raise ValueError("report must be a ResearchStrategyDomainResolutionAlphaDecayRouterReport")
    return _digest_for_value(report)


def validate_research_strategy_domain_resolution_alpha_decay_router_report_digest(
    value: ResearchStrategyDomainResolutionAlphaDecayRouterReport | dict[str, Any],
) -> None:
    research_strategy_domain_resolution_alpha_decay_router_report_payload(value)


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

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
    resolution_age_seconds: Decimal
    resolution_age_pressure: Decimal
    baseline_alpha_score: Decimal
    current_alpha_score: Decimal
    alpha_decay_ratio: Decimal
    alpha_retention_score: Decimal
    resolution_confidence_score: Decimal
    domain_reliability_score: Decimal
    decay_pressure_score: Decimal
    freshness_score: Decimal
    decay_relief_score: Decimal
    router_score: Decimal
    status: str
    reason_codes: tuple[str, ...]


def _prepare_row(
    value: ResearchStrategyDomainResolutionAlphaDecayRouterInput,
    *,
    config: ResearchStrategyDomainResolutionAlphaDecayRouterConfig,
    generated_at: datetime,
) -> _PreparedRow:
    resolution_age_seconds = _seconds_between(generated_at, value.last_resolution_observed_at)
    resolution_age_pressure = _age_pressure(
        resolution_age_seconds,
        fresh_age=config.fresh_resolution_age_seconds,
        stale_age=config.stale_resolution_age_seconds,
    )
    alpha_decay_ratio = _alpha_decay_ratio(
        value.baseline_alpha_score,
        value.current_alpha_score,
    )
    alpha_retention_score = _clamp_ratio(ONE - alpha_decay_ratio)
    freshness_score = _clamp_ratio(ONE - resolution_age_pressure)
    decay_relief_score = _clamp_ratio(ONE - value.decay_pressure_score)
    router_score = _router_score(
        alpha_retention_score=alpha_retention_score,
        resolution_confidence_score=value.resolution_confidence_score,
        domain_reliability_score=value.domain_reliability_score,
        freshness_score=freshness_score,
        decay_relief_score=decay_relief_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        upstream_reason_codes=value.reason_codes,
        router_score=router_score,
        alpha_decay_ratio=alpha_decay_ratio,
        resolution_age_pressure=resolution_age_pressure,
        resolution_confidence_score=value.resolution_confidence_score,
        domain_reliability_score=value.domain_reliability_score,
        decay_pressure_score=value.decay_pressure_score,
        config=config,
    )
    return _PreparedRow(
        route_digest=_private_digest(value.route_ref),
        evaluated_at=value.evaluated_at,
        resolution_age_seconds=resolution_age_seconds,
        resolution_age_pressure=resolution_age_pressure,
        baseline_alpha_score=value.baseline_alpha_score,
        current_alpha_score=value.current_alpha_score,
        alpha_decay_ratio=alpha_decay_ratio,
        alpha_retention_score=alpha_retention_score,
        resolution_confidence_score=value.resolution_confidence_score,
        domain_reliability_score=value.domain_reliability_score,
        decay_pressure_score=value.decay_pressure_score,
        freshness_score=freshness_score,
        decay_relief_score=decay_relief_score,
        router_score=router_score,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_from_prepared(
    value: _PreparedRow,
    *,
    aggregate_row_number: Decimal,
) -> ResearchStrategyDomainResolutionAlphaDecayRouterRow:
    return ResearchStrategyDomainResolutionAlphaDecayRouterRow(
        aggregate_row_number=aggregate_row_number,
        route_digest=value.route_digest,
        evaluated_at=value.evaluated_at,
        resolution_age_seconds=value.resolution_age_seconds,
        resolution_age_pressure=value.resolution_age_pressure,
        baseline_alpha_score=value.baseline_alpha_score,
        current_alpha_score=value.current_alpha_score,
        alpha_decay_ratio=value.alpha_decay_ratio,
        alpha_retention_score=value.alpha_retention_score,
        resolution_confidence_score=value.resolution_confidence_score,
        domain_reliability_score=value.domain_reliability_score,
        decay_pressure_score=value.decay_pressure_score,
        freshness_score=value.freshness_score,
        decay_relief_score=value.decay_relief_score,
        router_score=value.router_score,
        status=value.status,
        reason_codes=value.reason_codes,
    )


def _row_reason_codes(
    *,
    upstream_reason_codes: tuple[str, ...],
    router_score: Decimal,
    alpha_decay_ratio: Decimal,
    resolution_age_pressure: Decimal,
    resolution_confidence_score: Decimal,
    domain_reliability_score: Decimal,
    decay_pressure_score: Decimal,
    config: ResearchStrategyDomainResolutionAlphaDecayRouterConfig,
) -> tuple[str, ...]:
    codes = list(upstream_reason_codes)
    _append_floor_reason(
        codes,
        value=router_score,
        watch_floor=config.min_watch_router_score,
        pass_floor=config.min_pass_router_score,
        block_code=REASON_ROUTER_SCORE_BLOCK,
        watch_code=REASON_ROUTER_SCORE_WATCH,
    )
    _append_ceiling_reason(
        codes,
        value=alpha_decay_ratio,
        pass_ceiling=config.max_pass_alpha_decay_ratio,
        watch_ceiling=config.max_watch_alpha_decay_ratio,
        block_code=REASON_ALPHA_DECAY_BLOCK,
        watch_code=REASON_ALPHA_DECAY_WATCH,
    )
    _append_ceiling_reason(
        codes,
        value=resolution_age_pressure,
        pass_ceiling=config.max_pass_resolution_age_pressure,
        watch_ceiling=config.max_watch_resolution_age_pressure,
        block_code=REASON_RESOLUTION_AGE_BLOCK,
        watch_code=REASON_RESOLUTION_AGE_WATCH,
    )
    _append_floor_reason(
        codes,
        value=resolution_confidence_score,
        watch_floor=config.min_watch_resolution_confidence_score,
        pass_floor=config.min_pass_resolution_confidence_score,
        block_code=REASON_RESOLUTION_CONFIDENCE_BLOCK,
        watch_code=REASON_RESOLUTION_CONFIDENCE_WATCH,
    )
    _append_floor_reason(
        codes,
        value=domain_reliability_score,
        watch_floor=config.min_watch_domain_reliability_score,
        pass_floor=config.min_pass_domain_reliability_score,
        block_code=REASON_DOMAIN_RELIABILITY_BLOCK,
        watch_code=REASON_DOMAIN_RELIABILITY_WATCH,
    )
    _append_ceiling_reason(
        codes,
        value=decay_pressure_score,
        pass_ceiling=config.max_pass_decay_pressure_score,
        watch_ceiling=config.max_watch_decay_pressure_score,
        block_code=REASON_DECAY_PRESSURE_BLOCK,
        watch_code=REASON_DECAY_PRESSURE_WATCH,
    )
    if not any(_is_generated_row_reason(code) for code in codes):
        codes.insert(0, REASON_DOMAIN_RESOLUTION_ALPHA_DECAY_ROUTER_PASS)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(codes),
        ROW_REASON_CODE_SEQUENCE,
        allow_empty=False,
    )


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


def _router_score(
    *,
    alpha_retention_score: Decimal,
    resolution_confidence_score: Decimal,
    domain_reliability_score: Decimal,
    freshness_score: Decimal,
    decay_relief_score: Decimal,
    config: ResearchStrategyDomainResolutionAlphaDecayRouterConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        value = (
            (alpha_retention_score * config.alpha_retention_weight)
            + (resolution_confidence_score * config.resolution_confidence_weight)
            + (domain_reliability_score * config.domain_reliability_weight)
            + (freshness_score * config.freshness_weight)
            + (decay_relief_score * config.decay_relief_weight)
        )
    return _clamp_ratio(value)


def _alpha_decay_ratio(baseline_alpha_score: Decimal, current_alpha_score: Decimal) -> Decimal:
    if baseline_alpha_score == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        value = (baseline_alpha_score - current_alpha_score) / baseline_alpha_score
    return _clamp_ratio(value)


def _age_pressure(age_seconds: Decimal, *, fresh_age: Decimal, stale_age: Decimal) -> Decimal:
    if age_seconds <= fresh_age:
        return ZERO
    if age_seconds >= stale_age:
        return ONE
    with localcontext(DECIMAL_CONTEXT):
        value = (age_seconds - fresh_age) / (stale_age - fresh_age)
    return _clamp_ratio(value)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    value = Decimal(delta.days * 86400 + delta.seconds) + (
        Decimal(delta.microseconds) / Decimal("1000000.000000")
    )
    return _require_nonnegative_decimal("age_seconds", value)


def _normalize_inputs(
    inputs: Iterable[ResearchStrategyDomainResolutionAlphaDecayRouterInput],
) -> tuple[ResearchStrategyDomainResolutionAlphaDecayRouterInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Iterable):
        raise ValueError("inputs must be an iterable")
    normalized = tuple(inputs)
    for value in normalized:
        if type(value) is not ResearchStrategyDomainResolutionAlphaDecayRouterInput:
            raise ValueError(
                "inputs must contain ResearchStrategyDomainResolutionAlphaDecayRouterInput",
            )
        _require_hard_flags("input", value)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchStrategyDomainResolutionAlphaDecayRouterRow],
) -> tuple[ResearchStrategyDomainResolutionAlphaDecayRouterRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for value in normalized:
        if type(value) is not ResearchStrategyDomainResolutionAlphaDecayRouterRow:
            raise ValueError(
                "rows must contain ResearchStrategyDomainResolutionAlphaDecayRouterRow",
            )
        _require_hard_flags("row", value)
        _verify_digest(value)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    return normalized


def _normalize_reason_code_counts(
    counts: Iterable[ResearchStrategyDomainResolutionAlphaDecayRouterReasonCodeCount],
) -> tuple[ResearchStrategyDomainResolutionAlphaDecayRouterReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(counts)
    for value in normalized:
        if type(value) is not ResearchStrategyDomainResolutionAlphaDecayRouterReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyDomainResolutionAlphaDecayRouterReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", value)
    return tuple(sorted(normalized, key=_reason_count_sort_key))


def _reason_code_counts(
    rows: tuple[ResearchStrategyDomainResolutionAlphaDecayRouterRow, ...],
) -> tuple[ResearchStrategyDomainResolutionAlphaDecayRouterReasonCodeCount, ...]:
    total = _count_decimal(len(rows))
    counts: Counter[str] = Counter(reason for row in rows for reason in row.reason_codes)
    return tuple(
        ResearchStrategyDomainResolutionAlphaDecayRouterReasonCodeCount(
            reason_code=reason,
            count=_count_decimal(count),
            row_ratio=_ratio(_count_decimal(count), total),
        )
        for reason, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], _reason_sequence_index(item[0])),
        )
    )


def _report_reason_codes(
    rows: tuple[ResearchStrategyDomainResolutionAlphaDecayRouterRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (REASON_REPORT_BLOCK, REASON_NO_INPUTS)
    status = _report_status(rows)
    codes = [
        {
            STATUS_PASS: REASON_REPORT_PASS,
            STATUS_WATCH: REASON_REPORT_WATCH,
            STATUS_BLOCK: REASON_REPORT_BLOCK,
        }[status],
    ]
    review_pairs = (
        ((REASON_ROUTER_SCORE_BLOCK, REASON_ROUTER_SCORE_WATCH), REASON_ROUTER_SCORE_REVIEW),
        ((REASON_ALPHA_DECAY_BLOCK, REASON_ALPHA_DECAY_WATCH), REASON_ALPHA_DECAY_REVIEW),
        (
            (REASON_RESOLUTION_AGE_BLOCK, REASON_RESOLUTION_AGE_WATCH),
            REASON_RESOLUTION_AGE_REVIEW,
        ),
        (
            (REASON_RESOLUTION_CONFIDENCE_BLOCK, REASON_RESOLUTION_CONFIDENCE_WATCH),
            REASON_RESOLUTION_CONFIDENCE_REVIEW,
        ),
        (
            (REASON_DOMAIN_RELIABILITY_BLOCK, REASON_DOMAIN_RELIABILITY_WATCH),
            REASON_DOMAIN_RELIABILITY_REVIEW,
        ),
        ((REASON_DECAY_PRESSURE_BLOCK, REASON_DECAY_PRESSURE_WATCH), REASON_DECAY_PRESSURE_REVIEW),
    )
    for row_reasons, report_reason in review_pairs:
        if any(any(reason in row.reason_codes for reason in row_reasons) for row in rows):
            codes.append(report_reason)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(codes),
        REPORT_REASON_CODE_SEQUENCE,
        allow_empty=False,
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return STATUS_BLOCK
    if REASON_DOMAIN_RESOLUTION_ALPHA_DECAY_ROUTER_PASS in reason_codes:
        return STATUS_PASS
    return STATUS_WATCH


def _report_status(rows: tuple[ResearchStrategyDomainResolutionAlphaDecayRouterRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _status_count(
    rows: tuple[ResearchStrategyDomainResolutionAlphaDecayRouterRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _prepared_sort_key(value: _PreparedRow) -> tuple[int, Decimal, str]:
    return (_status_rank(value.status), value.router_score, value.route_digest)


def _row_sort_key(
    value: ResearchStrategyDomainResolutionAlphaDecayRouterRow,
) -> tuple[int, Decimal, str]:
    return (_status_rank(value.status), value.router_score, value.route_digest)


def _reason_count_sort_key(
    value: ResearchStrategyDomainResolutionAlphaDecayRouterReasonCodeCount,
) -> tuple[Decimal, int]:
    return (-value.count, _reason_sequence_index(value.reason_code))


def _status_rank(status: str) -> int:
    return {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[status]


def _reason_sequence_index(reason_code: str) -> int:
    sequence = COUNT_REASON_CODE_SEQUENCE + REPORT_REASON_CODE_SEQUENCE
    try:
        return sequence.index(reason_code)
    except ValueError:
        return len(sequence)


def _is_generated_row_reason(reason_code: str) -> bool:
    return (
        reason_code not in UPSTREAM_REASON_CODES
        and reason_code != REASON_DOMAIN_RESOLUTION_ALPHA_DECAY_ROUTER_PASS
    )


def _validate_row(row: ResearchStrategyDomainResolutionAlphaDecayRouterRow) -> None:
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.alpha_retention_score != _clamp_ratio(ONE - row.alpha_decay_ratio):
        raise ValueError("alpha_retention_score must match alpha_decay_ratio")
    if row.freshness_score != _clamp_ratio(ONE - row.resolution_age_pressure):
        raise ValueError("freshness_score must match resolution_age_pressure")
    if row.decay_relief_score != _clamp_ratio(ONE - row.decay_pressure_score):
        raise ValueError("decay_relief_score must match decay_pressure_score")


def _validate_report(report: ResearchStrategyDomainResolutionAlphaDecayRouterReport) -> None:
    rows = report.rows
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.row_count != _count_decimal(len(rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _status_count(rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.mean_router_score != _mean_decimal(tuple(row.router_score for row in rows)):
        raise ValueError("mean_router_score must match rows")
    if report.lowest_router_score != _min_decimal(tuple(row.router_score for row in rows)):
        raise ValueError("lowest_router_score must match rows")
    if report.highest_alpha_decay_ratio != _max_decimal(
        tuple(row.alpha_decay_ratio for row in rows),
    ):
        raise ValueError("highest_alpha_decay_ratio must match rows")
    if report.highest_resolution_age_seconds != _max_decimal(
        tuple(row.resolution_age_seconds for row in rows),
    ):
        raise ValueError("highest_resolution_age_seconds must match rows")
    if report.lowest_resolution_confidence_score != _min_decimal(
        tuple(row.resolution_confidence_score for row in rows),
    ):
        raise ValueError("lowest_resolution_confidence_score must match rows")
    if report.lowest_domain_reliability_score != _min_decimal(
        tuple(row.domain_reliability_score for row in rows),
    ):
        raise ValueError("lowest_domain_reliability_score must match rows")
    if report.highest_decay_pressure_score != _max_decimal(
        tuple(row.decay_pressure_score for row in rows),
    ):
        raise ValueError("highest_decay_pressure_score must match rows")
    expected_reason_counts = _reason_code_counts(rows)
    if not rows:
        expected_reason_counts = (
            ResearchStrategyDomainResolutionAlphaDecayRouterReasonCodeCount(
                reason_code=REASON_NO_INPUTS,
                count=ONE,
                row_ratio=ONE,
            ),
        )
    if report.reason_code_counts != expected_reason_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    expected_row_numbers = tuple(_count_decimal(index) for index in range(1, len(rows) + 1))
    if tuple(row.aggregate_row_number for row in rows) != expected_row_numbers:
        raise ValueError("aggregate_row_number must match row order")


def _mean_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        value = sum(values, ZERO) / Decimal(len(values))
    return _quantize(value)


def _min_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return min(values)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        value = numerator / denominator
    return _clamp_ratio(value)


def _count_decimal(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return _quantize(Decimal(value))


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return _quantize(normalized)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(normalized)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return _quantize(normalized)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(DECIMAL_QUANTUM)


def _clamp_ratio(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return _quantize(value)


def _require_floor_pair(
    pass_name: str,
    pass_value: Decimal,
    watch_name: str,
    watch_value: Decimal,
) -> None:
    if pass_value < watch_value:
        raise ValueError(f"{pass_name} must be greater than or equal to {watch_name}")


def _require_ceiling_pair(
    pass_name: str,
    pass_value: Decimal,
    watch_name: str,
    watch_value: Decimal,
) -> None:
    if pass_value > watch_value:
        raise ValueError(f"{pass_name} must be less than or equal to {watch_name}")


def _require_status(field_name: str, value: object) -> str:
    return _require_member(field_name, value, RESEARCH_STRATEGY_DOMAIN_RESOLUTION_ALPHA_DECAY_ROUTER_STATUSES)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")
    return value


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str or not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public label")
    return value


def _require_private_ref(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty private reference")
    return value


def _require_private_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not PRIVATE_DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 private digest")
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _normalize_reason_codes(
    field_name: str,
    values: object,
    allowed: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    for value in values:
        _require_member(field_name, value, allowed)
        seen.add(value)
    if not seen and not allow_empty:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(value for value in allowed if value in seen)


def _require_hard_flags(scope: str, value: object) -> None:
    for field_name in FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{scope} {field_name} must be True")


def _private_digest(value: str) -> str:
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()


def _apply_or_verify_digest(value: object) -> None:
    expected = _digest_for_value(value)
    supplied = getattr(value, DIGEST_FIELD)
    if supplied:
        _require_digest(DIGEST_FIELD, supplied)
        if supplied != expected:
            raise ValueError("derived_validation_digest must match payload")
    object.__setattr__(value, DIGEST_FIELD, expected)


def _verify_digest(value: object) -> None:
    supplied = getattr(value, DIGEST_FIELD)
    _require_digest(DIGEST_FIELD, supplied)
    if supplied != _digest_for_value(value):
        raise ValueError("derived_validation_digest must match payload")


def _digest_for_value(value: object) -> str:
    payload = _payload_value(value)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    payload.pop(DIGEST_FIELD, None)
    return _payload_digest(payload)


def _payload_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    supplied = payload.get(DIGEST_FIELD)
    _require_digest(DIGEST_FIELD, supplied)
    unsigned = dict(payload)
    unsigned.pop(DIGEST_FIELD, None)
    expected = _payload_digest(unsigned)
    if supplied != expected:
        raise ValueError("derived_validation_digest must match payload")


def _payload_value(value: object) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _copy_json_object(value: dict[str, Any]) -> dict[str, Any]:
    return {key: _copy_json_value(item) for key, item in value.items()}


def _copy_json_value(value: Any) -> Any:
    if type(value) is dict:
        return _copy_json_object(value)
    if type(value) is list:
        return [_copy_json_value(item) for item in value]
    if type(value) in (str, bool) or value is None:
        return value
    if type(value) in (int, float, Decimal):
        raise ValueError("payload must not contain raw numeric values")
    raise ValueError("payload must contain JSON-ready values")


def _validate_payload_statuses(value: Any) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if key == "status" and item not in RESEARCH_STRATEGY_DOMAIN_RESOLUTION_ALPHA_DECAY_ROUTER_STATUSES:
                raise ValueError("status must be pass, watch, or block")
            _validate_payload_statuses(item)
    elif type(value) is list:
        for item in value:
            _validate_payload_statuses(item)


def _reject_unsafe_public_payload(scope: str, value: Any) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{scope} public field must be a string")
            lowered_key = key.casefold()
            if any(fragment in lowered_key for fragment in UNSAFE_PUBLIC_FRAGMENTS):
                raise ValueError(f"{scope} unsafe public field: {key}")
            _reject_unsafe_public_payload(scope, item)
    elif type(value) is list:
        for item in value:
            _reject_unsafe_public_payload(scope, item)
    elif type(value) is str:
        lowered_value = value.casefold()
        if any(fragment in lowered_value for fragment in UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError(f"{scope} unsafe public value")
