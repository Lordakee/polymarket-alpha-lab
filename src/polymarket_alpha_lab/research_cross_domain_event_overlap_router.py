"""Read-only cross-domain event overlap router reports."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any, Iterable

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)
from polymarket_alpha_lab.team_taxonomy import (
    TEAM_CATEGORIES,
    TEAM_ID_TO_PRIMARY_CATEGORY,
    require_category_id,
    require_team_id,
)


RESEARCH_CROSS_DOMAIN_EVENT_OVERLAP_ROUTER_CONFIG_VERSION = (
    "research-cross-domain-event-overlap-router-v1"
)

PUBLIC_STATUSES = ("pass", "watch", "block")
QUEUE_LANES = (
    "collaborative_research_standard",
    "collaborative_research_watch",
    "collaborative_research_block",
)
ROUTE_REASON_CODES = (
    "cross_domain_politics_crypto",
    "cross_domain_politics_macro",
    "cross_domain_politics_sports",
    "cross_domain_crypto_macro",
    "cross_domain_crypto_sports",
    "cross_domain_macro_sports",
    "cross_domain_other",
    "high_overlap_score",
    "source_confidence_supported",
    "high_urgency_score",
    "high_conflict_score",
    "stale_source_pressure",
    "insufficient_domain_overlap",
    "routed_to_collaborative_research",
    "no_events",
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MAX_SCORE = Decimal("100.000000")

DEFAULT_WATCH_ROUTING_SCORE_THRESHOLD = Decimal("45.000000")
DEFAULT_BLOCK_ROUTING_SCORE_THRESHOLD = Decimal("75.000000")
DEFAULT_SEVERE_CONFLICT_THRESHOLD = Decimal("0.850000")
DEFAULT_STALE_SOURCE_THRESHOLD = Decimal("0.750000")
OVERLAP_WEIGHT = Decimal("40.000000")
SOURCE_CONFIDENCE_WEIGHT = Decimal("20.000000")
URGENCY_WEIGHT = Decimal("20.000000")
CONFLICT_WEIGHT = Decimal("20.000000")
STALE_SOURCE_PENALTY = Decimal("10.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")

_CATEGORY_RANK = {category_id: index for index, category_id in enumerate(TEAM_CATEGORIES)}
_CATEGORY_TO_TEAM_ID = {
    category_id: team_id for team_id, category_id in TEAM_ID_TO_PRIMARY_CATEGORY.items()
}
_BUCKET_RANK = ("politics", "crypto", "macro", "sports", "other")
_STATUS_RANK = {"block": Decimal("0"), "watch": Decimal("1"), "pass": Decimal("2")}


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("raw", "_id"),
    _join_parts("raw", "-", "id"),
    _join_parts("raw", "_candidate"),
    _join_parts("candidate", "_id"),
    _join_parts("candidate", "-", "id"),
    _join_parts("market", "_id"),
    _join_parts("market", "-", "id"),
    _join_parts("market", "_slug"),
    _join_parts("market", "-", "slug"),
    _join_parts("slug"),
    _join_parts("ques", "tion"),
    _join_parts("source", "_ref"),
    _join_parts("source", "-", "ref"),
    _join_parts("source", "_url"),
    _join_parts("source", "-", "url"),
    _join_parts("source", "_text"),
    _join_parts("source", "-", "text"),
    _join_parts("http", "://"),
    _join_parts("https", "://"),
    _join_parts("d", "sn"),
    _join_parts("ta", "ble"),
    _join_parts("to", "ken"),
    _join_parts("wal", "let"),
    _join_parts("ord", "er"),
    _join_parts("tra", "de"),
    _join_parts("tradi", "ng"),
    _join_parts("po", "sition"),
    _join_parts("bu", "y"),
    _join_parts("se", "ll"),
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
class ResearchCrossDomainEventOverlapRouterConfig(_FinalPublicDataclass):
    config_version: str = RESEARCH_CROSS_DOMAIN_EVENT_OVERLAP_ROUTER_CONFIG_VERSION
    watch_routing_score_threshold: Decimal = DEFAULT_WATCH_ROUTING_SCORE_THRESHOLD
    block_routing_score_threshold: Decimal = DEFAULT_BLOCK_ROUTING_SCORE_THRESHOLD
    severe_conflict_threshold: Decimal = DEFAULT_SEVERE_CONFLICT_THRESHOLD
    stale_source_threshold: Decimal = DEFAULT_STALE_SOURCE_THRESHOLD
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchCrossDomainEventOverlapRouterConfig, "config")
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "watch_routing_score_threshold",
            "block_routing_score_threshold",
            "severe_conflict_threshold",
            "stale_source_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_or_score(field_name, getattr(self, field_name)),
            )
        if self.block_routing_score_threshold <= self.watch_routing_score_threshold:
            raise ValueError(
                "block_routing_score_threshold must exceed "
                "watch_routing_score_threshold",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchCrossDomainEventOverlapCandidate(_FinalPublicDataclass):
    event_key: str
    category_ids: tuple[str, ...]
    overlap_score: Decimal
    source_confidence_score: Decimal
    urgency_score: Decimal
    conflict_score: Decimal
    stale_source_score: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchCrossDomainEventOverlapCandidate, "event")
        _require_public_string("event_key", self.event_key)
        object.__setattr__(
            self,
            "category_ids",
            _normalize_category_ids(self.category_ids),
        )
        for field_name in (
            "overlap_score",
            "source_confidence_score",
            "urgency_score",
            "conflict_score",
            "stale_source_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_optional_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("event", self)


@dataclass(frozen=True)
class ResearchCrossDomainEventOverlapRoute(_FinalPublicDataclass):
    event_key: str
    route_status: str
    queue_lane: str
    category_ids: tuple[str, ...]
    assigned_team_ids: tuple[str, ...]
    overlap_score: Decimal
    source_confidence_score: Decimal
    urgency_score: Decimal
    conflict_score: Decimal
    stale_source_score: Decimal
    source_age_seconds: Decimal
    routing_score: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchCrossDomainEventOverlapRoute, "route")
        _require_public_string("event_key", self.event_key)
        _require_status("route_status", self.route_status)
        _require_member("queue_lane", self.queue_lane, QUEUE_LANES)
        object.__setattr__(
            self,
            "category_ids",
            _normalize_category_ids(self.category_ids),
        )
        object.__setattr__(
            self,
            "assigned_team_ids",
            _normalize_team_ids(self.assigned_team_ids),
        )
        for field_name in (
            "overlap_score",
            "source_confidence_score",
            "urgency_score",
            "conflict_score",
            "stale_source_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_age_seconds",
            _normalize_nonnegative_decimal("source_age_seconds", self.source_age_seconds),
        )
        object.__setattr__(
            self,
            "routing_score",
            _normalize_score("routing_score", self.routing_score),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_route(self)
        _reject_public_surface("route", self)
        _require_hard_flags("route", self)


@dataclass(frozen=True)
class ResearchCrossDomainEventOverlapReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchCrossDomainEventOverlapReasonCodeCount,
            "reason_count",
        )
        _require_member("reason_code", self.reason_code, ROUTE_REASON_CODES)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _reject_public_surface("reason_count", self)
        _require_hard_flags("reason_count", self)


@dataclass(frozen=True)
class ResearchCrossDomainEventOverlapReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_routing_score: Decimal
    max_routing_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchCrossDomainEventOverlapReasonCodeCount, ...]
    routes: tuple[ResearchCrossDomainEventOverlapRoute, ...]
    public_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchCrossDomainEventOverlapReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "event_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("mean_routing_score", "max_routing_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_score(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "routes", _normalize_routes(self.routes))
        _require_digest("public_digest", self.public_digest)
        _validate_report(self)
        _reject_public_surface("report", self)
        _require_hard_flags("report", self)


_PUBLIC_DATACLASS_TYPES = (
    ResearchCrossDomainEventOverlapCandidate,
    ResearchCrossDomainEventOverlapReasonCodeCount,
    ResearchCrossDomainEventOverlapReport,
    ResearchCrossDomainEventOverlapRoute,
    ResearchCrossDomainEventOverlapRouterConfig,
)


def build_research_cross_domain_event_overlap_report(
    events: Iterable[ResearchCrossDomainEventOverlapCandidate],
    *,
    generated_at: datetime,
    config: ResearchCrossDomainEventOverlapRouterConfig | None = None,
) -> ResearchCrossDomainEventOverlapReport:
    active_config = ResearchCrossDomainEventOverlapRouterConfig() if config is None else config
    if type(active_config) is not ResearchCrossDomainEventOverlapRouterConfig:
        raise ValueError("config must be a ResearchCrossDomainEventOverlapRouterConfig")
    _require_hard_flags("config", active_config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (
                _route_from_event(event, generated_at=generated_at_utc, config=active_config)
                for event in _normalize_events(events)
            ),
            key=_route_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    reason_code_counts = _reason_code_counts(rows, reason_codes)
    status = _report_status(rows)
    event_count = _count(len(rows))
    pass_count = _status_count(rows, "pass")
    watch_count = _status_count(rows, "watch")
    block_count = _status_count(rows, "block")
    mean_routing_score = _mean_routing_score(rows)
    max_routing_score = _max_routing_score(rows)
    digest = _derived_public_digest(
        generated_at=generated_at_utc,
        config_version=active_config.config_version,
        event_count=event_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        mean_routing_score=mean_routing_score,
        max_routing_score=max_routing_score,
        status=status,
        reason_codes=reason_codes,
        reason_code_counts=reason_code_counts,
        routes=rows,
    )
    return ResearchCrossDomainEventOverlapReport(
        generated_at=generated_at_utc,
        config_version=active_config.config_version,
        event_count=event_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        mean_routing_score=mean_routing_score,
        max_routing_score=max_routing_score,
        status=status,
        reason_codes=reason_codes,
        reason_code_counts=reason_code_counts,
        routes=rows,
        public_digest=digest,
    )


def research_cross_domain_event_overlap_router_payload(
    report: ResearchCrossDomainEventOverlapReport,
) -> dict[str, Any]:
    if type(report) is not ResearchCrossDomainEventOverlapReport:
        raise ValueError("report must be a ResearchCrossDomainEventOverlapReport")
    _require_hard_flags("report", report)
    _validate_report(report)
    payload = _report_payload(report, include_digest=True)
    _reject_public_surface("payload", payload)
    ready_payload = json_ready_no_floats(payload)
    if type(ready_payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _PayloadFlags(ready_payload))
    return ready_payload


def research_cross_domain_event_overlap_router_digest(
    report: ResearchCrossDomainEventOverlapReport,
) -> str:
    if type(report) is not ResearchCrossDomainEventOverlapReport:
        raise ValueError("report must be a ResearchCrossDomainEventOverlapReport")
    _validate_report(report)
    return report.public_digest


@dataclass(frozen=True)
class _PayloadFlags:
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


def _route_from_event(
    event: ResearchCrossDomainEventOverlapCandidate,
    *,
    generated_at: datetime,
    config: ResearchCrossDomainEventOverlapRouterConfig,
) -> ResearchCrossDomainEventOverlapRoute:
    if event.observed_at > generated_at:
        raise ValueError("observed_at must be no later than generated_at")
    source_age_seconds = _source_age_seconds(event.observed_at, generated_at)
    routing_score = _routing_score(event)
    reason_codes = _route_reason_codes(event, routing_score, config)
    route_status = _route_status(event, routing_score, config)
    return ResearchCrossDomainEventOverlapRoute(
        event_key=event.event_key,
        route_status=route_status,
        queue_lane=_queue_lane(route_status),
        category_ids=event.category_ids,
        assigned_team_ids=_assigned_team_ids(event.category_ids),
        overlap_score=event.overlap_score,
        source_confidence_score=event.source_confidence_score,
        urgency_score=event.urgency_score,
        conflict_score=event.conflict_score,
        stale_source_score=event.stale_source_score,
        source_age_seconds=source_age_seconds,
        routing_score=routing_score,
        observed_at=event.observed_at,
        reason_codes=reason_codes,
    )


def _routing_score(event: ResearchCrossDomainEventOverlapCandidate) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = event.overlap_score * OVERLAP_WEIGHT
        score += event.source_confidence_score * SOURCE_CONFIDENCE_WEIGHT
        score += event.urgency_score * URGENCY_WEIGHT
        score += event.conflict_score * CONFLICT_WEIGHT
        score -= event.stale_source_score * STALE_SOURCE_PENALTY
    if score < ZERO:
        return ZERO
    if score > MAX_SCORE:
        return MAX_SCORE
    return _quantize(score)


def _route_status(
    event: ResearchCrossDomainEventOverlapCandidate,
    routing_score: Decimal,
    config: ResearchCrossDomainEventOverlapRouterConfig,
) -> str:
    if not _has_domain_overlap(event.category_ids):
        return "block"
    if event.conflict_score >= config.severe_conflict_threshold:
        return "block"
    if routing_score >= config.block_routing_score_threshold:
        return "block"
    if routing_score >= config.watch_routing_score_threshold:
        return "watch"
    if event.stale_source_score >= config.stale_source_threshold:
        return "watch"
    return "pass"


def _queue_lane(route_status: str) -> str:
    if route_status == "pass":
        return "collaborative_research_standard"
    if route_status == "watch":
        return "collaborative_research_watch"
    return "collaborative_research_block"


def _route_reason_codes(
    event: ResearchCrossDomainEventOverlapCandidate,
    routing_score: Decimal,
    config: ResearchCrossDomainEventOverlapRouterConfig,
) -> tuple[str, ...]:
    reasons = set(event.reason_codes)
    reasons.update(_domain_reason_codes(event.category_ids))
    if event.overlap_score >= Decimal("0.600000"):
        reasons.add("high_overlap_score")
    if event.source_confidence_score >= Decimal("0.700000"):
        reasons.add("source_confidence_supported")
    if event.urgency_score >= Decimal("0.700000"):
        reasons.add("high_urgency_score")
    if event.conflict_score >= config.severe_conflict_threshold:
        reasons.add("high_conflict_score")
    if event.stale_source_score >= config.stale_source_threshold:
        reasons.add("stale_source_pressure")
    if not _has_domain_overlap(event.category_ids):
        reasons.add("insufficient_domain_overlap")
    if _has_domain_overlap(event.category_ids) and routing_score >= ZERO:
        reasons.add("routed_to_collaborative_research")
    return tuple(code for code in ROUTE_REASON_CODES if code in reasons)


def _domain_reason_codes(category_ids: tuple[str, ...]) -> tuple[str, ...]:
    buckets = tuple(dict.fromkeys(_category_bucket(category_id) for category_id in category_ids))
    if len(buckets) < 2:
        return ()
    reason_codes: set[str] = set()
    for left_index, left in enumerate(buckets):
        for right in buckets[left_index + 1 :]:
            pair = tuple(sorted((left, right), key=_BUCKET_RANK.index))
            if pair == ("politics", "crypto"):
                reason_codes.add("cross_domain_politics_crypto")
            elif pair == ("politics", "macro"):
                reason_codes.add("cross_domain_politics_macro")
            elif pair == ("politics", "sports"):
                reason_codes.add("cross_domain_politics_sports")
            elif pair == ("crypto", "macro"):
                reason_codes.add("cross_domain_crypto_macro")
            elif pair == ("crypto", "sports"):
                reason_codes.add("cross_domain_crypto_sports")
            elif pair == ("macro", "sports"):
                reason_codes.add("cross_domain_macro_sports")
            else:
                reason_codes.add("cross_domain_other")
    return tuple(code for code in ROUTE_REASON_CODES if code in reason_codes)


def _category_bucket(category_id: str) -> str:
    if category_id == "politics":
        return "politics"
    if category_id.startswith("finance.crypto."):
        return "crypto"
    if category_id.startswith("sports."):
        return "sports"
    if category_id.startswith("finance."):
        return "macro"
    return "other"


def _has_domain_overlap(category_ids: tuple[str, ...]) -> bool:
    return len({_category_bucket(category_id) for category_id in category_ids}) >= 2


def _assigned_team_ids(category_ids: tuple[str, ...]) -> tuple[str, ...]:
    team_ids = tuple(_CATEGORY_TO_TEAM_ID[category_id] for category_id in category_ids)
    return tuple(dict.fromkeys(team_ids))


def _source_age_seconds(observed_at: datetime, generated_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    microseconds = (
        Decimal(delta.days) * Decimal("86400000000")
        + Decimal(delta.seconds) * Decimal("1000000")
        + Decimal(delta.microseconds)
    )
    return _normalize_nonnegative_decimal(
        "source_age_seconds",
        microseconds / MICROSECONDS_PER_SECOND,
    )


def _report_payload(
    report: ResearchCrossDomainEventOverlapReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload = {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "event_count": report.event_count,
        "pass_count": report.pass_count,
        "watch_count": report.watch_count,
        "block_count": report.block_count,
        "mean_routing_score": report.mean_routing_score,
        "max_routing_score": report.max_routing_score,
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "reason_code_counts": [
            _reason_code_count_payload(row) for row in report.reason_code_counts
        ],
        "routes": [_route_payload(row) for row in report.routes],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    if include_digest:
        payload["public_digest"] = report.public_digest
    return payload


def _route_payload(row: ResearchCrossDomainEventOverlapRoute) -> dict[str, Any]:
    return {
        "event_key": row.event_key,
        "route_status": row.route_status,
        "queue_lane": row.queue_lane,
        "category_ids": list(row.category_ids),
        "assigned_team_ids": list(row.assigned_team_ids),
        "overlap_score": row.overlap_score,
        "source_confidence_score": row.source_confidence_score,
        "urgency_score": row.urgency_score,
        "conflict_score": row.conflict_score,
        "stale_source_score": row.stale_source_score,
        "source_age_seconds": row.source_age_seconds,
        "routing_score": row.routing_score,
        "observed_at": row.observed_at,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _reason_code_count_payload(
    row: ResearchCrossDomainEventOverlapReasonCodeCount,
) -> dict[str, Any]:
    return {
        "reason_code": row.reason_code,
        "count": row.count,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _derived_public_digest(
    *,
    generated_at: datetime,
    config_version: str,
    event_count: Decimal,
    pass_count: Decimal,
    watch_count: Decimal,
    block_count: Decimal,
    mean_routing_score: Decimal,
    max_routing_score: Decimal,
    status: str,
    reason_codes: tuple[str, ...],
    reason_code_counts: tuple[ResearchCrossDomainEventOverlapReasonCodeCount, ...],
    routes: tuple[ResearchCrossDomainEventOverlapRoute, ...],
) -> str:
    payload = {
        "generated_at": generated_at,
        "config_version": config_version,
        "event_count": event_count,
        "pass_count": pass_count,
        "watch_count": watch_count,
        "block_count": block_count,
        "mean_routing_score": mean_routing_score,
        "max_routing_score": max_routing_score,
        "status": status,
        "reason_codes": list(reason_codes),
        "reason_code_counts": [
            _reason_code_count_payload(row) for row in reason_code_counts
        ],
        "routes": [_route_payload(row) for row in routes],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    ready = json_ready_no_floats(payload)
    encoded = json.dumps(ready, separators=(",", ":"), sort_keys=True)
    return sha256(encoded.encode("utf-8")).hexdigest()


def _derived_public_digest_from_report(
    report: ResearchCrossDomainEventOverlapReport,
) -> str:
    return _derived_public_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        event_count=report.event_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        mean_routing_score=report.mean_routing_score,
        max_routing_score=report.max_routing_score,
        status=report.status,
        reason_codes=report.reason_codes,
        reason_code_counts=report.reason_code_counts,
        routes=report.routes,
    )


def _normalize_events(
    events: Iterable[ResearchCrossDomainEventOverlapCandidate],
) -> tuple[ResearchCrossDomainEventOverlapCandidate, ...]:
    if isinstance(events, str | bytes):
        raise ValueError("events must be an iterable")
    try:
        rows = tuple(events)
    except TypeError as exc:
        raise ValueError("events must be an iterable") from exc
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchCrossDomainEventOverlapCandidate:
            raise ValueError("events must contain ResearchCrossDomainEventOverlapCandidate values")
        _require_hard_flags("event", row)
        if row.event_key in seen:
            raise ValueError("event_key values must be unique")
        seen.add(row.event_key)
    return rows


def _normalize_routes(
    routes: Iterable[ResearchCrossDomainEventOverlapRoute],
) -> tuple[ResearchCrossDomainEventOverlapRoute, ...]:
    if isinstance(routes, str | bytes):
        raise ValueError("routes must be an iterable")
    try:
        rows = tuple(routes)
    except TypeError as exc:
        raise ValueError("routes must be an iterable") from exc
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchCrossDomainEventOverlapRoute:
            raise ValueError("routes must contain ResearchCrossDomainEventOverlapRoute values")
        _require_hard_flags("route", row)
        if row.event_key in seen:
            raise ValueError("route event_key values must be unique")
        seen.add(row.event_key)
    if rows != tuple(sorted(rows, key=_route_sort_key)):
        raise ValueError("routes must use deterministic sorting")
    return rows


def _normalize_reason_code_counts(
    rows: Iterable[ResearchCrossDomainEventOverlapReasonCodeCount],
) -> tuple[ResearchCrossDomainEventOverlapReasonCodeCount, ...]:
    if isinstance(rows, str | bytes):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchCrossDomainEventOverlapReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchCrossDomainEventOverlapReasonCodeCount values",
            )
        _require_hard_flags("reason_count", row)
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must contain unique reason codes")
        seen.add(row.reason_code)
    expected_sequence = tuple(
        sorted(normalized, key=lambda row: ROUTE_REASON_CODES.index(row.reason_code)),
    )
    if normalized != expected_sequence:
        raise ValueError("reason_code_counts must use deterministic sorting")
    return normalized


def _normalize_category_ids(value: object) -> tuple[str, ...]:
    if isinstance(value, str | bytes):
        raise ValueError("category_ids must be an iterable")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("category_ids must be an iterable") from exc
    if not items:
        raise ValueError("category_ids must contain at least one category")
    normalized = tuple(require_category_id("category_id", item) for item in items)
    if len(set(normalized)) != len(normalized):
        raise ValueError("category_ids must contain unique categories")
    return tuple(sorted(normalized, key=_CATEGORY_RANK.__getitem__))


def _normalize_team_ids(value: object) -> tuple[str, ...]:
    if isinstance(value, str | bytes):
        raise ValueError("assigned_team_ids must be an iterable")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("assigned_team_ids must be an iterable") from exc
    if not items:
        raise ValueError("assigned_team_ids must contain at least one team")
    normalized = tuple(require_team_id("team_id", item) for item in items)
    if len(set(normalized)) != len(normalized):
        raise ValueError("assigned_team_ids must contain unique teams")
    return normalized


def _normalize_optional_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, str | bytes):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} must contain unique reason codes")
    for item in items:
        _require_member(field_name, item, ROUTE_REASON_CODES)
    return tuple(code for code in ROUTE_REASON_CODES if code in items)


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    items = _normalize_optional_reason_codes(field_name, value)
    if not items:
        raise ValueError(f"{field_name} must contain at least one reason code")
    return items


def _normalize_report_reason_codes(value: object) -> tuple[str, ...]:
    return _normalize_reason_codes("reason_codes", value)


def _reason_code_counts(
    rows: tuple[ResearchCrossDomainEventOverlapRoute, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchCrossDomainEventOverlapReasonCodeCount, ...]:
    if not rows and reason_codes == ("no_events",):
        return (
            ResearchCrossDomainEventOverlapReasonCodeCount(
                reason_code="no_events",
                count=_count(1),
            ),
        )
    return tuple(
        ResearchCrossDomainEventOverlapReasonCodeCount(
            reason_code=reason_code,
            count=_count(
                sum(1 for row in rows if reason_code in row.reason_codes),
            ),
        )
        for reason_code in reason_codes
    )


def _report_reason_codes(
    rows: tuple[ResearchCrossDomainEventOverlapRoute, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_events",)
    codes = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
    }
    return tuple(code for code in ROUTE_REASON_CODES if code in codes)


def _report_status(rows: tuple[ResearchCrossDomainEventOverlapRoute, ...]) -> str:
    if any(row.route_status == "block" for row in rows):
        return "block"
    if any(row.route_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _status_count(
    rows: tuple[ResearchCrossDomainEventOverlapRoute, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.route_status == status))


def _mean_routing_score(rows: tuple[ResearchCrossDomainEventOverlapRoute, ...]) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        total = sum((row.routing_score for row in rows), ZERO)
        mean = total / _count(len(rows))
    return _normalize_score("mean_routing_score", mean)


def _max_routing_score(rows: tuple[ResearchCrossDomainEventOverlapRoute, ...]) -> Decimal:
    if not rows:
        return ZERO
    return max(row.routing_score for row in rows)


def _route_sort_key(
    row: ResearchCrossDomainEventOverlapRoute,
) -> tuple[Decimal, Decimal, str]:
    return (_STATUS_RANK[row.route_status], -row.routing_score, row.event_key)


def _validate_route(row: ResearchCrossDomainEventOverlapRoute) -> None:
    expected_status = _queue_lane(row.route_status)
    if row.queue_lane != expected_status:
        raise ValueError("queue_lane must match route_status")
    if row.assigned_team_ids != _assigned_team_ids(row.category_ids):
        raise ValueError("assigned_team_ids must match category_ids")
    if row.route_status == "pass" and "insufficient_domain_overlap" in row.reason_codes:
        raise ValueError("pass routes cannot have insufficient_domain_overlap")


def _validate_report(report: ResearchCrossDomainEventOverlapReport) -> None:
    if report.public_digest != _derived_public_digest_from_report(report):
        raise ValueError("public_digest must match public report fields")
    expected_counts = {
        "event_count": _count(len(report.routes)),
        "pass_count": _status_count(report.routes, "pass"),
        "watch_count": _status_count(report.routes, "watch"),
        "block_count": _status_count(report.routes, "block"),
    }
    for field_name, expected in expected_counts.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match routes")
    if report.status != _report_status(report.routes):
        raise ValueError("status must match routes")
    if report.reason_codes != _report_reason_codes(report.routes):
        raise ValueError("reason_codes must match routes")
    expected_reason_counts = _reason_code_counts(report.routes, report.reason_codes)
    if report.reason_code_counts != expected_reason_counts:
        raise ValueError("reason_code_counts must match routes")
    if report.mean_routing_score != _mean_routing_score(report.routes):
        raise ValueError("mean_routing_score must match routes")
    if report.max_routing_score != _max_routing_score(report.routes):
        raise ValueError("max_routing_score must match routes")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_ratio_or_score(field_name: str, value: object) -> Decimal:
    if field_name.endswith("_threshold") and "routing_score" in field_name:
        return _normalize_score(field_name, value)
    return _normalize_ratio(field_name, value)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be no greater than one")
    return normalized


def _normalize_score(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > MAX_SCORE:
        raise ValueError(f"{field_name} must be no greater than one hundred")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(value)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO or value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a nonnegative whole Decimal")
    return value.quantize(COUNT_QUANTUM)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be a positive whole Decimal")
    return normalized


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)


def _require_status(field_name: str, value: object) -> None:
    _require_member(field_name, value, PUBLIC_STATUSES)


def _require_member(field_name: str, value: object, members: tuple[str, ...]) -> None:
    if type(value) is not str or value not in members:
        raise ValueError(f"{field_name} must be a known public value")
    _reject_public_string(field_name, value)


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_public_string(field_name, value)


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be an exact public dataclass")


def _require_hard_flags(label: str, value: object) -> None:
    require_paper_only_flags(label, value)


def _reject_public_surface(label: str, payload: object) -> None:
    if is_dataclass(payload) and not isinstance(payload, type):
        _reject_public_surface(label, asdict(payload))
        return
    if isinstance(payload, dict):
        for key, value in payload.items():
            if type(key) is not str:
                raise ValueError(f"{label} payload keys must be strings")
            _reject_public_string(label, key)
            _reject_public_surface(label, value)
        return
    if isinstance(payload, (list, tuple)):
        for value in payload:
            _reject_public_surface(label, value)
        return
    if isinstance(payload, str):
        _reject_public_string(label, payload)


def _reject_public_string(field_name: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public value in {field_name}")


__all__ = (
    "PUBLIC_STATUSES",
    "QUEUE_LANES",
    "RESEARCH_CROSS_DOMAIN_EVENT_OVERLAP_ROUTER_CONFIG_VERSION",
    "ResearchCrossDomainEventOverlapCandidate",
    "ResearchCrossDomainEventOverlapReasonCodeCount",
    "ResearchCrossDomainEventOverlapReport",
    "ResearchCrossDomainEventOverlapRoute",
    "ResearchCrossDomainEventOverlapRouterConfig",
    "build_research_cross_domain_event_overlap_report",
    "research_cross_domain_event_overlap_router_digest",
    "research_cross_domain_event_overlap_router_payload",
)
