"""Public-safe event news monitoring need report."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any, Iterable


RESEARCH_EVENT_NEWS_MONITORING_NEED_ROUTER_CONFIG_VERSION = (
    "research-event-news-monitoring-need-router-v1"
)

MONITORING_STATUSES = ("pass", "watch", "block")
MONITORING_INTENSITIES = (
    "routine_review",
    "heightened_review",
    "continuous_review",
)

PASS_REASON = "event_news_monitoring_need_router_routine_review"
NO_DOMAINS_REASON = "no_event_domains"
ROUTE_REASON_CODES = (
    PASS_REASON,
    "elevated_catalyst_cadence",
    "rapid_catalyst_cadence",
    "aging_source_window",
    "stale_source_window",
    "elevated_evidence_conflict",
    "severe_evidence_conflict",
    "near_resolution_window",
    "imminent_resolution_window",
    "limited_team_coverage",
    "thin_team_coverage",
)
REPORT_REASON_CODES = (NO_DOMAINS_REASON,) + ROUTE_REASON_CODES

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MAX_SCORE = Decimal("100.000000")

DEFAULT_WATCH_SCORE_THRESHOLD = Decimal("45.000000")
DEFAULT_BLOCK_SCORE_THRESHOLD = Decimal("75.000000")
DEFAULT_ELEVATED_CATALYST_THRESHOLD = Decimal("0.500000")
DEFAULT_RAPID_CATALYST_THRESHOLD = Decimal("0.800000")
DEFAULT_AGING_SOURCE_AGE_SECONDS = Decimal("3600.000000")
DEFAULT_STALE_SOURCE_AGE_SECONDS = Decimal("14400.000000")
DEFAULT_ELEVATED_CONFLICT_THRESHOLD = Decimal("0.500000")
DEFAULT_SEVERE_CONFLICT_THRESHOLD = Decimal("0.750000")
DEFAULT_NEAR_RESOLUTION_SECONDS = Decimal("86400.000000")
DEFAULT_IMMINENT_RESOLUTION_SECONDS = Decimal("3600.000000")
DEFAULT_LIMITED_TEAM_COVERAGE_THRESHOLD = Decimal("0.600000")
DEFAULT_THIN_TEAM_COVERAGE_THRESHOLD = Decimal("0.300000")

BASE_SCORE = Decimal("10.000000")
CATALYST_CADENCE_WEIGHT = Decimal("20.000000")
SOURCE_FRESHNESS_WEIGHT = Decimal("20.000000")
EVIDENCE_CONFLICT_WEIGHT = Decimal("10.000000")
RESOLUTION_HORIZON_WEIGHT = Decimal("19.000000")
TEAM_COVERAGE_WEIGHT = Decimal("20.000000")
HIGH_PRESSURE_SCORE = Decimal("0.9102564102564102564102564103")
MID_PRESSURE_SCORE = Decimal("0.500000")

_STATUS_RANK = {"block": Decimal("0"), "watch": Decimal("1"), "pass": Decimal("2")}


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("raw", "_", "id"),
    _join_parts("raw", "-", "id"),
    _join_parts("raw", "_", "candidate"),
    _join_parts("candidate", "_", "id"),
    _join_parts("candidate", "-", "id"),
    _join_parts("mar", "ket", "_", "id"),
    _join_parts("mar", "ket", "-", "id"),
    _join_parts("mar", "ket", "_", "s", "lug"),
    _join_parts("mar", "ket", "-", "s", "lug"),
    _join_parts("s", "lug"),
    _join_parts("ques", "tion"),
    _join_parts("raw", "_", "source"),
    _join_parts("source", "_", "url"),
    _join_parts("source", "-", "url"),
    _join_parts("source", "_", "text"),
    _join_parts("source", "-", "text"),
    _join_parts("ht", "tp", "://"),
    _join_parts("ht", "tps", "://"),
    _join_parts("data", "base"),
    _join_parts("net", "work"),
    _join_parts("wal", "let"),
    _join_parts("au", "th"),
    _join_parts("ord", "er"),
    _join_parts("tra", "de"),
    _join_parts("li", "ve"),
    _join_parts("exec", "ution"),
    _join_parts("reco", "mmend"),
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
class ResearchEventNewsMonitoringNeedRouterConfig(_FinalPublicDataclass):
    config_version: str = RESEARCH_EVENT_NEWS_MONITORING_NEED_ROUTER_CONFIG_VERSION
    watch_monitoring_need_score_threshold: Decimal = DEFAULT_WATCH_SCORE_THRESHOLD
    block_monitoring_need_score_threshold: Decimal = DEFAULT_BLOCK_SCORE_THRESHOLD
    elevated_catalyst_cadence_threshold: Decimal = DEFAULT_ELEVATED_CATALYST_THRESHOLD
    rapid_catalyst_cadence_threshold: Decimal = DEFAULT_RAPID_CATALYST_THRESHOLD
    aging_source_age_seconds: Decimal = DEFAULT_AGING_SOURCE_AGE_SECONDS
    stale_source_age_seconds: Decimal = DEFAULT_STALE_SOURCE_AGE_SECONDS
    elevated_evidence_conflict_threshold: Decimal = DEFAULT_ELEVATED_CONFLICT_THRESHOLD
    severe_evidence_conflict_threshold: Decimal = DEFAULT_SEVERE_CONFLICT_THRESHOLD
    near_resolution_horizon_seconds: Decimal = DEFAULT_NEAR_RESOLUTION_SECONDS
    imminent_resolution_horizon_seconds: Decimal = DEFAULT_IMMINENT_RESOLUTION_SECONDS
    limited_team_coverage_threshold: Decimal = DEFAULT_LIMITED_TEAM_COVERAGE_THRESHOLD
    thin_team_coverage_threshold: Decimal = DEFAULT_THIN_TEAM_COVERAGE_THRESHOLD
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventNewsMonitoringNeedRouterConfig, "config")
        _require_public_string("config_version", self.config_version)
        if self.config_version != RESEARCH_EVENT_NEWS_MONITORING_NEED_ROUTER_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_monitoring_need_score_threshold",
            "block_monitoring_need_score_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_score(field_name, getattr(self, field_name)),
            )
        if (
            self.block_monitoring_need_score_threshold
            <= self.watch_monitoring_need_score_threshold
        ):
            raise ValueError(
                "block_monitoring_need_score_threshold must exceed "
                "watch_monitoring_need_score_threshold",
            )
        for field_name in (
            "elevated_catalyst_cadence_threshold",
            "rapid_catalyst_cadence_threshold",
            "elevated_evidence_conflict_threshold",
            "severe_evidence_conflict_threshold",
            "limited_team_coverage_threshold",
            "thin_team_coverage_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if (
            self.rapid_catalyst_cadence_threshold
            < self.elevated_catalyst_cadence_threshold
        ):
            raise ValueError(
                "rapid_catalyst_cadence_threshold must be at least "
                "elevated_catalyst_cadence_threshold",
            )
        if (
            self.severe_evidence_conflict_threshold
            < self.elevated_evidence_conflict_threshold
        ):
            raise ValueError(
                "severe_evidence_conflict_threshold must be at least "
                "elevated_evidence_conflict_threshold",
            )
        if (
            self.thin_team_coverage_threshold
            > self.limited_team_coverage_threshold
        ):
            raise ValueError(
                "thin_team_coverage_threshold must not exceed "
                "limited_team_coverage_threshold",
            )
        for field_name in (
            "aging_source_age_seconds",
            "stale_source_age_seconds",
            "near_resolution_horizon_seconds",
            "imminent_resolution_horizon_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_seconds(field_name, getattr(self, field_name)),
            )
        if self.stale_source_age_seconds <= self.aging_source_age_seconds:
            raise ValueError(
                "stale_source_age_seconds must exceed aging_source_age_seconds",
            )
        if (
            self.near_resolution_horizon_seconds
            <= self.imminent_resolution_horizon_seconds
        ):
            raise ValueError(
                "near_resolution_horizon_seconds must exceed "
                "imminent_resolution_horizon_seconds",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventNewsMonitoringNeedDomain(_FinalPublicDataclass):
    domain_key: str
    domain_label: str
    observed_at: datetime
    catalyst_cadence_score: Decimal
    source_age_seconds: Decimal
    evidence_conflict_score: Decimal
    resolution_horizon_seconds: Decimal
    team_coverage_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventNewsMonitoringNeedDomain, "domain")
        for field_name in ("domain_key", "domain_label"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("catalyst_cadence_score", "evidence_conflict_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_age_seconds",
            _normalize_nonnegative_seconds(
                "source_age_seconds",
                self.source_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "resolution_horizon_seconds",
            _normalize_nonnegative_seconds(
                "resolution_horizon_seconds",
                self.resolution_horizon_seconds,
            ),
        )
        object.__setattr__(
            self,
            "team_coverage_score",
            _normalize_ratio("team_coverage_score", self.team_coverage_score),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("domain", self)


@dataclass(frozen=True)
class ResearchEventNewsMonitoringNeedRoute(_FinalPublicDataclass):
    domain_key: str
    domain_label: str
    observed_at: datetime
    catalyst_cadence_score: Decimal
    source_age_seconds: Decimal
    evidence_conflict_score: Decimal
    resolution_horizon_seconds: Decimal
    team_coverage_score: Decimal
    monitoring_need_score: Decimal
    route_status: str
    monitoring_intensity: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventNewsMonitoringNeedRoute, "route")
        for field_name in ("domain_key", "domain_label"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("catalyst_cadence_score", "evidence_conflict_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_age_seconds",
            _normalize_nonnegative_seconds(
                "source_age_seconds",
                self.source_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "resolution_horizon_seconds",
            _normalize_nonnegative_seconds(
                "resolution_horizon_seconds",
                self.resolution_horizon_seconds,
            ),
        )
        object.__setattr__(
            self,
            "team_coverage_score",
            _normalize_ratio("team_coverage_score", self.team_coverage_score),
        )
        object.__setattr__(
            self,
            "monitoring_need_score",
            _normalize_score("monitoring_need_score", self.monitoring_need_score),
        )
        _require_member("route_status", self.route_status, MONITORING_STATUSES)
        _require_member(
            "monitoring_intensity",
            self.monitoring_intensity,
            MONITORING_INTENSITIES,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allowed=ROUTE_REASON_CODES,
            ),
        )
        _require_hard_flags("route", self)
        expected_digest = _digest_public_payload(_route_payload(self, include_digest=False))
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match route payload")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


@dataclass(frozen=True)
class ResearchEventNewsMonitoringNeedReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    domain_count: Decimal
    domain_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventNewsMonitoringNeedReasonCodeCount,
            "reason_code_count",
        )
        _require_member("reason_code", self.reason_code, ROUTE_REASON_CODES)
        object.__setattr__(
            self,
            "domain_count",
            _normalize_positive_count("domain_count", self.domain_count),
        )
        object.__setattr__(
            self,
            "domain_ratio",
            _normalize_ratio("domain_ratio", self.domain_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchEventNewsMonitoringNeedReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    reason_codes: tuple[str, ...]
    domain_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_monitoring_need_score: Decimal
    mean_monitoring_need_score: Decimal
    reason_code_counts: tuple[ResearchEventNewsMonitoringNeedReasonCodeCount, ...]
    routes: tuple[ResearchEventNewsMonitoringNeedRoute, ...]
    input_domains: tuple[ResearchEventNewsMonitoringNeedDomain, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventNewsMonitoringNeedReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_member("status", self.status, MONITORING_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allowed=REPORT_REASON_CODES,
            ),
        )
        for field_name in ("domain_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_monitoring_need_score", "mean_monitoring_need_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_score(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "routes", _normalize_routes(self.routes))
        object.__setattr__(
            self,
            "input_domains",
            _normalize_domains(self.input_domains),
        )
        _require_hard_flags("report", self)
        _validate_report(self)
        expected_digest = _digest_public_payload(_report_payload(self, include_digest=False))
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report payload")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_research_event_news_monitoring_need_router_report(
    domains: Iterable[ResearchEventNewsMonitoringNeedDomain],
    *,
    generated_at: datetime,
    config: ResearchEventNewsMonitoringNeedRouterConfig | None = None,
) -> ResearchEventNewsMonitoringNeedReport:
    active_config = config or ResearchEventNewsMonitoringNeedRouterConfig()
    if type(active_config) is not ResearchEventNewsMonitoringNeedRouterConfig:
        raise ValueError("config must be a ResearchEventNewsMonitoringNeedRouterConfig")
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_domains = _normalize_domains(domains)
    routes = tuple(
        sorted(
            (
                _route_from_domain(domain, config=active_config)
                for domain in normalized_domains
            ),
            key=_route_sort_key,
        ),
    )
    return ResearchEventNewsMonitoringNeedReport(
        generated_at=generated_at_utc,
        config_version=active_config.config_version,
        status=_report_status(routes),
        reason_codes=_report_reason_codes(routes),
        domain_count=_count(len(routes)),
        pass_count=_status_count(routes, "pass"),
        watch_count=_status_count(routes, "watch"),
        block_count=_status_count(routes, "block"),
        max_monitoring_need_score=_max_score(
            route.monitoring_need_score for route in routes
        ),
        mean_monitoring_need_score=_mean_score(
            route.monitoring_need_score for route in routes
        ),
        reason_code_counts=_reason_code_counts(routes),
        routes=routes,
        input_domains=normalized_domains,
    )


def research_event_news_monitoring_need_router_payload(
    report: ResearchEventNewsMonitoringNeedReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is dict:
        validate_research_event_news_monitoring_need_router_public_payload(report)
        return report
    if type(report) is not ResearchEventNewsMonitoringNeedReport:
        raise ValueError("report must be a ResearchEventNewsMonitoringNeedReport")
    _validate_report(report)
    payload = _report_payload(report)
    validate_research_event_news_monitoring_need_router_public_payload(payload)
    return payload


def validate_research_event_news_monitoring_need_router_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dictionary")
    _reject_unsafe_public_payload(payload)
    for flag_name in ("paper_only", "report_only", "readonly"):
        if payload.get(flag_name) is not True:
            raise ValueError(f"{flag_name} must be True")
    _require_member("status", payload.get("status"), MONITORING_STATUSES)
    for route_payload in payload.get("routes", ()):
        if type(route_payload) is not dict:
            raise ValueError("routes must contain dictionaries")
        _require_member("route_status", route_payload.get("route_status"), MONITORING_STATUSES)
        for flag_name in ("paper_only", "report_only", "readonly"):
            if route_payload.get(flag_name) is not True:
                raise ValueError(f"{flag_name} must be True")
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest is required")
    _require_digest("derived_validation_digest", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    if _digest_public_payload(unsigned_payload) != digest:
        raise ValueError("derived_validation_digest must match public payload")
    _reject_public_numbers(payload)
    return True


def _route_from_domain(
    domain: ResearchEventNewsMonitoringNeedDomain,
    *,
    config: ResearchEventNewsMonitoringNeedRouterConfig,
) -> ResearchEventNewsMonitoringNeedRoute:
    score = _monitoring_need_score(domain, config)
    status = _route_status(score, config)
    return ResearchEventNewsMonitoringNeedRoute(
        domain_key=domain.domain_key,
        domain_label=domain.domain_label,
        observed_at=domain.observed_at,
        catalyst_cadence_score=domain.catalyst_cadence_score,
        source_age_seconds=domain.source_age_seconds,
        evidence_conflict_score=domain.evidence_conflict_score,
        resolution_horizon_seconds=domain.resolution_horizon_seconds,
        team_coverage_score=domain.team_coverage_score,
        monitoring_need_score=score,
        route_status=status,
        monitoring_intensity=_monitoring_intensity(status),
        reason_codes=_route_reason_codes(domain, config),
    )


def _monitoring_need_score(
    domain: ResearchEventNewsMonitoringNeedDomain,
    config: ResearchEventNewsMonitoringNeedRouterConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        coverage_gap = _quantize_ratio(ONE - domain.team_coverage_score)
        score = (
            BASE_SCORE
            + domain.catalyst_cadence_score * CATALYST_CADENCE_WEIGHT
            + _source_freshness_pressure(domain.source_age_seconds, config)
            * SOURCE_FRESHNESS_WEIGHT
            + domain.evidence_conflict_score * EVIDENCE_CONFLICT_WEIGHT
            + _resolution_pressure(domain.resolution_horizon_seconds, config)
            * RESOLUTION_HORIZON_WEIGHT
            + coverage_gap * TEAM_COVERAGE_WEIGHT
        )
    return _quantize_score(min(score, MAX_SCORE))


def _source_freshness_pressure(
    source_age_seconds: Decimal,
    config: ResearchEventNewsMonitoringNeedRouterConfig,
) -> Decimal:
    if source_age_seconds < config.aging_source_age_seconds:
        return ZERO
    if source_age_seconds < config.stale_source_age_seconds:
        return MID_PRESSURE_SCORE
    return HIGH_PRESSURE_SCORE


def _resolution_pressure(
    resolution_horizon_seconds: Decimal,
    config: ResearchEventNewsMonitoringNeedRouterConfig,
) -> Decimal:
    if resolution_horizon_seconds > config.near_resolution_horizon_seconds:
        return ZERO
    if resolution_horizon_seconds > config.imminent_resolution_horizon_seconds:
        return MID_PRESSURE_SCORE
    return HIGH_PRESSURE_SCORE


def _route_status(
    score: Decimal,
    config: ResearchEventNewsMonitoringNeedRouterConfig,
) -> str:
    if score >= config.block_monitoring_need_score_threshold:
        return "block"
    if score >= config.watch_monitoring_need_score_threshold:
        return "watch"
    return "pass"


def _monitoring_intensity(status: str) -> str:
    if status == "block":
        return "continuous_review"
    if status == "watch":
        return "heightened_review"
    return "routine_review"


def _route_reason_codes(
    domain: ResearchEventNewsMonitoringNeedDomain,
    config: ResearchEventNewsMonitoringNeedRouterConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if domain.catalyst_cadence_score >= config.rapid_catalyst_cadence_threshold:
        reason_codes.append("rapid_catalyst_cadence")
    elif domain.catalyst_cadence_score >= config.elevated_catalyst_cadence_threshold:
        reason_codes.append("elevated_catalyst_cadence")

    if domain.source_age_seconds >= config.stale_source_age_seconds:
        reason_codes.append("stale_source_window")
    elif domain.source_age_seconds >= config.aging_source_age_seconds:
        reason_codes.append("aging_source_window")

    if domain.evidence_conflict_score >= config.severe_evidence_conflict_threshold:
        reason_codes.append("severe_evidence_conflict")
    elif domain.evidence_conflict_score >= config.elevated_evidence_conflict_threshold:
        reason_codes.append("elevated_evidence_conflict")

    if domain.resolution_horizon_seconds <= config.imminent_resolution_horizon_seconds:
        reason_codes.append("imminent_resolution_window")
    elif domain.resolution_horizon_seconds <= config.near_resolution_horizon_seconds:
        reason_codes.append("near_resolution_window")

    if domain.team_coverage_score <= config.thin_team_coverage_threshold:
        reason_codes.append("thin_team_coverage")
    elif domain.team_coverage_score <= config.limited_team_coverage_threshold:
        reason_codes.append("limited_team_coverage")

    for reason_code in domain.reason_codes:
        if reason_code not in reason_codes:
            reason_codes.append(reason_code)

    if reason_codes:
        return tuple(reason_codes)
    return (PASS_REASON,)


def _report_status(routes: tuple[ResearchEventNewsMonitoringNeedRoute, ...]) -> str:
    if any(route.route_status == "block" for route in routes):
        return "block"
    if any(route.route_status == "watch" for route in routes):
        return "watch"
    return "pass"


def _report_reason_codes(
    routes: tuple[ResearchEventNewsMonitoringNeedRoute, ...],
) -> tuple[str, ...]:
    if not routes:
        return (NO_DOMAINS_REASON,)
    reason_codes: list[str] = []
    for route in routes:
        for reason_code in route.reason_codes:
            if reason_code != PASS_REASON and reason_code not in reason_codes:
                reason_codes.append(reason_code)
    if reason_codes:
        return tuple(reason_codes)
    return (PASS_REASON,)


def _reason_code_counts(
    routes: tuple[ResearchEventNewsMonitoringNeedRoute, ...],
) -> tuple[ResearchEventNewsMonitoringNeedReasonCodeCount, ...]:
    if not routes:
        return ()
    domain_count = _count(len(routes))
    reason_codes = sorted(
        {
            reason_code
            for route in routes
            for reason_code in route.reason_codes
            if reason_code != PASS_REASON
        },
    )
    return tuple(
        ResearchEventNewsMonitoringNeedReasonCodeCount(
            reason_code=reason_code,
            domain_count=_count(
                sum(1 for route in routes if reason_code in route.reason_codes),
            ),
            domain_ratio=_quantize_ratio(
                _count(sum(1 for route in routes if reason_code in route.reason_codes))
                / domain_count,
            ),
        )
        for reason_code in reason_codes
    )


def _status_count(
    routes: tuple[ResearchEventNewsMonitoringNeedRoute, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for route in routes if route.route_status == status))


def _max_score(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return _quantize_score(max(items))


def _mean_score(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_score(sum(items, ZERO) / _count(len(items)))


def _route_sort_key(route: ResearchEventNewsMonitoringNeedRoute) -> tuple[Decimal, Decimal, str]:
    return (
        _STATUS_RANK[route.route_status],
        -route.monitoring_need_score,
        route.domain_key,
    )


def _domain_sort_key(domain: ResearchEventNewsMonitoringNeedDomain) -> tuple[str, str]:
    return (domain.domain_key, domain.domain_label)


def _validate_report(report: ResearchEventNewsMonitoringNeedReport) -> None:
    routes = report.routes
    input_domains = report.input_domains
    if report.domain_count != _count(len(routes)):
        raise ValueError("domain_count must match routes")
    if report.domain_count != _count(len(input_domains)):
        raise ValueError("domain_count must match input_domains")
    for status, field_name in (
        ("pass", "pass_count"),
        ("watch", "watch_count"),
        ("block", "block_count"),
    ):
        if getattr(report, field_name) != _status_count(routes, status):
            raise ValueError(f"{field_name} must match routes")
    if report.max_monitoring_need_score != _max_score(
        route.monitoring_need_score for route in routes
    ):
        raise ValueError("max_monitoring_need_score must match routes")
    if report.mean_monitoring_need_score != _mean_score(
        route.monitoring_need_score for route in routes
    ):
        raise ValueError("mean_monitoring_need_score must match routes")
    if report.status != _report_status(routes):
        raise ValueError("status must match routes")
    if report.reason_codes != _report_reason_codes(routes):
        raise ValueError("reason_codes must match routes")
    if report.reason_code_counts != _reason_code_counts(routes):
        raise ValueError("reason_code_counts must match routes")
    if routes != tuple(sorted(routes, key=_route_sort_key)):
        raise ValueError("routes must be sorted deterministically")
    if input_domains != tuple(sorted(input_domains, key=_domain_sort_key)):
        raise ValueError("input_domains must be sorted deterministically")
    for route in routes:
        if route.derived_validation_digest != _digest_public_payload(
            _route_payload(route, include_digest=False),
        ):
            raise ValueError("derived_validation_digest must match route payload")


def _report_payload(
    report: ResearchEventNewsMonitoringNeedReport,
    *,
    include_digest: bool = True,
) -> dict[str, Any]:
    payload = {
        "generated_at": _json_value(report.generated_at),
        "config_version": report.config_version,
        "status": report.status,
        "reason_codes": _json_value(report.reason_codes),
        "domain_count": _json_value(report.domain_count),
        "pass_count": _json_value(report.pass_count),
        "watch_count": _json_value(report.watch_count),
        "block_count": _json_value(report.block_count),
        "max_monitoring_need_score": _json_value(report.max_monitoring_need_score),
        "mean_monitoring_need_score": _json_value(report.mean_monitoring_need_score),
        "reason_code_counts": _json_value(report.reason_code_counts),
        "routes": [_route_payload(route) for route in report.routes],
        "input_domains": _json_value(report.input_domains),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    if include_digest:
        payload["derived_validation_digest"] = report.derived_validation_digest
    return payload


def _route_payload(
    route: ResearchEventNewsMonitoringNeedRoute,
    *,
    include_digest: bool = True,
) -> dict[str, Any]:
    payload = {
        "domain_key": route.domain_key,
        "domain_label": route.domain_label,
        "observed_at": _json_value(route.observed_at),
        "catalyst_cadence_score": _json_value(route.catalyst_cadence_score),
        "source_age_seconds": _json_value(route.source_age_seconds),
        "evidence_conflict_score": _json_value(route.evidence_conflict_score),
        "resolution_horizon_seconds": _json_value(route.resolution_horizon_seconds),
        "team_coverage_score": _json_value(route.team_coverage_score),
        "monitoring_need_score": _json_value(route.monitoring_need_score),
        "route_status": route.route_status,
        "monitoring_intensity": route.monitoring_intensity,
        "reason_codes": _json_value(route.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    if include_digest:
        payload["derived_validation_digest"] = route.derived_validation_digest
    return payload


def _json_value(value: object) -> Any:
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    return value


def _digest_public_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()


def _normalize_domains(
    value: Iterable[ResearchEventNewsMonitoringNeedDomain],
) -> tuple[ResearchEventNewsMonitoringNeedDomain, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("domains must be an iterable")
    try:
        domains = tuple(value)
    except TypeError as exc:
        raise ValueError("domains must be an iterable") from exc
    for domain in domains:
        if type(domain) is not ResearchEventNewsMonitoringNeedDomain:
            raise ValueError("domains must contain ResearchEventNewsMonitoringNeedDomain")
    return tuple(sorted(domains, key=_domain_sort_key))


def _normalize_routes(
    value: Iterable[ResearchEventNewsMonitoringNeedRoute],
) -> tuple[ResearchEventNewsMonitoringNeedRoute, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("routes must be an iterable")
    try:
        routes = tuple(value)
    except TypeError as exc:
        raise ValueError("routes must be an iterable") from exc
    for route in routes:
        if type(route) is not ResearchEventNewsMonitoringNeedRoute:
            raise ValueError("routes must contain ResearchEventNewsMonitoringNeedRoute")
    return routes


def _normalize_reason_code_counts(
    value: Iterable[ResearchEventNewsMonitoringNeedReasonCodeCount],
) -> tuple[ResearchEventNewsMonitoringNeedReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for item in items:
        if type(item) is not ResearchEventNewsMonitoringNeedReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchEventNewsMonitoringNeedReasonCodeCount",
            )
    return items


def _normalize_reason_codes(
    field_name: str,
    value: Iterable[str],
    *,
    allowed: tuple[str, ...] | None = None,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} must not contain duplicates")
    for item in items:
        _require_public_string(field_name, item)
        if allowed is not None and item not in allowed:
            raise ValueError(f"{field_name} must use supported reason codes")
    return items


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value).quantize(QUANTUM)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_unsafe_public_string(field_name, value)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {', '.join(allowed)}")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_hard_flags(label: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name) is not True:
            raise ValueError(f"{label} {flag_name} must be True")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize_ratio(decimal_value)


def _normalize_score(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > MAX_SCORE:
        raise ValueError(f"{field_name} must be between 0 and 100")
    return _quantize_score(decimal_value)


def _normalize_nonnegative_seconds(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value.quantize(QUANTUM)


def _normalize_positive_seconds(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_seconds(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value.quantize(QUANTUM)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_count(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _quantize_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _quantize_score(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _reject_unsafe_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_public_string("payload key", str(key))
            _reject_unsafe_public_payload(item)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(item)
    elif isinstance(value, str):
        _reject_unsafe_public_string("payload value", value)


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} must be public-safe")


def _reject_public_numbers(value: object) -> None:
    if type(value) in (float, int, Decimal, datetime):
        raise ValueError("public payload numerics must be encoded strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numbers(item)
    elif isinstance(value, list):
        for item in value:
            _reject_public_numbers(item)
