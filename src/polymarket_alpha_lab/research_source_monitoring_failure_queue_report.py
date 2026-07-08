"""Pure report reducer for research source monitoring failures."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)
from polymarket_alpha_lab.team_taxonomy import require_team_category_pair, require_team_id


DEFAULT_RESEARCH_SOURCE_MONITORING_FAILURE_QUEUE_CONFIG_VERSION = (
    "research-source-monitoring-failure-queue-v0"
)

FAILURE_TYPES = (
    "timeout",
    "parse_error",
    "auth_error",
    "rate_limit",
    "schema_change",
    "unavailable",
)
IMPACT_DOMAINS = (
    "resolution",
    "probability",
    "news_context",
    "liquidity",
    "rules",
)
STATUSES = ("pass", "watch", "block")
REFRESH_RISKS = ("low", "watch", "high")

NO_FAILURES_REASON = "no_source_monitoring_failures"
PASS_REASON = "source_monitoring_failure_pass"
WATCH_REASON = "source_monitoring_failure_watch"
BLOCK_REASON = "source_monitoring_failure_block"
LOW_REFRESH_RISK_REASON = "low_refresh_risk"
WATCH_REFRESH_RISK_REASON = "watch_refresh_risk"
HIGH_REFRESH_RISK_REASON = "high_refresh_risk"
ALTERNATIVE_SOURCES_AVAILABLE_REASON = "alternative_sources_available"
MISSING_ALTERNATIVE_SOURCE_REASON = "missing_alternative_source"
AFFECTED_MARKET_THRESHOLD_REASON = "affected_market_threshold_hit"
AFFECTED_CANDIDATE_THRESHOLD_REASON = "affected_candidate_threshold_hit"
HIGH_ESCALATION_PRIORITY_REASON = "high_escalation_priority"

STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}
RISK_WEIGHT = {"high": 0, "watch": 1, "low": 2}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")

UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "source_url",
    "source_text",
    "source_ref",
    "dsn",
    "table",
    "token",
    "market_id",
    "candidate_id",
)
UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "http://",
    "https://",
    "postgresql://",
    "mysql://",
    "sqlite://",
    "dsn=",
    "token=",
)


@dataclass(frozen=True)
class ResearchSourceMonitoringFailureQueueConfig:
    config_version: str = DEFAULT_RESEARCH_SOURCE_MONITORING_FAILURE_QUEUE_CONFIG_VERSION
    watch_refresh_age_seconds: Decimal = Decimal("7200.000000")
    block_refresh_age_seconds: Decimal = Decimal("86400.000000")
    min_alternative_source_count: Decimal = Decimal("1.000000")
    block_affected_market_count: Decimal = Decimal("5.000000")
    block_affected_candidate_count: Decimal = Decimal("20.000000")
    watch_escalation_priority_score: Decimal = Decimal("0.500000")
    block_escalation_priority_score: Decimal = Decimal("0.850000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "watch_refresh_age_seconds",
            "block_refresh_age_seconds",
            "min_alternative_source_count",
            "block_affected_market_count",
            "block_affected_candidate_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_escalation_priority_score",
            "block_escalation_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        if self.block_refresh_age_seconds <= self.watch_refresh_age_seconds:
            raise ValueError(
                "block_refresh_age_seconds must be greater than watch_refresh_age_seconds",
            )
        if self.block_escalation_priority_score <= self.watch_escalation_priority_score:
            raise ValueError(
                "block_escalation_priority_score must be greater than "
                "watch_escalation_priority_score",
            )
        require_paper_only_flags("config", self)
        reject_unsafe_surface_fields("config", self)
        _reject_unsafe_public_surface("config", asdict(self))


@dataclass(frozen=True)
class ResearchSourceMonitoringFailureEvent:
    failure_id: str
    source_alias: str
    team_id: str
    category_id: str
    failure_type: str
    impact_domain: str
    detected_at: datetime
    last_success_at: datetime | None
    affected_market_count: Decimal
    affected_candidate_count: Decimal
    refresh_attempt_count: Decimal
    alternative_sources: tuple[str, ...]
    escalation_priority_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("failure_id", "source_alias"):
            object.__setattr__(
                self,
                field_name,
                _require_public_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        _require_member("failure_type", self.failure_type, FAILURE_TYPES)
        _require_member("impact_domain", self.impact_domain, IMPACT_DOMAINS)
        object.__setattr__(self, "detected_at", _as_utc("detected_at", self.detected_at))
        object.__setattr__(
            self,
            "last_success_at",
            _as_optional_utc("last_success_at", self.last_success_at),
        )
        if self.last_success_at is not None and self.last_success_at > self.detected_at:
            raise ValueError("last_success_at must be <= detected_at")
        for field_name in (
            "affected_market_count",
            "affected_candidate_count",
            "refresh_attempt_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "alternative_sources",
            _normalize_public_string_tuple(
                "alternative_sources",
                self.alternative_sources,
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "escalation_priority_score",
            _require_probability(
                "escalation_priority_score",
                self.escalation_priority_score,
            ),
        )
        require_paper_only_flags("failure event", self)
        reject_unsafe_surface_fields("failure event", self)
        _reject_unsafe_public_surface("failure event", asdict(self))


@dataclass(frozen=True)
class ResearchSourceMonitoringFailureQueueItem:
    failure_id: str
    source_alias: str
    team_id: str
    category_id: str
    failure_type: str
    impact_domain: str
    queue_status: str
    priority_rank: Decimal
    detected_at: datetime
    last_success_at: datetime | None
    refresh_age_seconds: Decimal | None
    refresh_risk: str
    affected_market_count: Decimal
    affected_candidate_count: Decimal
    refresh_attempt_count: Decimal
    alternative_source_count: Decimal
    alternative_sources: tuple[str, ...]
    escalation_priority_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("failure_id", "source_alias"):
            object.__setattr__(
                self,
                field_name,
                _require_public_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        _require_member("failure_type", self.failure_type, FAILURE_TYPES)
        _require_member("impact_domain", self.impact_domain, IMPACT_DOMAINS)
        _require_member("queue_status", self.queue_status, STATUSES)
        object.__setattr__(
            self,
            "priority_rank",
            _require_positive_whole_decimal("priority_rank", self.priority_rank),
        )
        object.__setattr__(self, "detected_at", _as_utc("detected_at", self.detected_at))
        object.__setattr__(
            self,
            "last_success_at",
            _as_optional_utc("last_success_at", self.last_success_at),
        )
        object.__setattr__(
            self,
            "refresh_age_seconds",
            _normalize_optional_nonnegative_decimal(
                "refresh_age_seconds",
                self.refresh_age_seconds,
            ),
        )
        _require_member("refresh_risk", self.refresh_risk, REFRESH_RISKS)
        for field_name in (
            "affected_market_count",
            "affected_candidate_count",
            "refresh_attempt_count",
            "alternative_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "alternative_sources",
            _normalize_public_string_tuple(
                "alternative_sources",
                self.alternative_sources,
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "escalation_priority_score",
            _require_probability(
                "escalation_priority_score",
                self.escalation_priority_score,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        require_paper_only_flags("queue item", self)
        reject_unsafe_surface_fields("queue item", self)
        _reject_unsafe_public_surface("queue item", asdict(self))
        _validate_queue_item(self)


@dataclass(frozen=True)
class ResearchSourceMonitoringFailureQueueReport:
    generated_at: datetime
    config_version: str
    status: str
    failure_count: Decimal
    queue_item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    high_refresh_risk_count: Decimal
    missing_alternative_source_count: Decimal
    total_affected_market_count: Decimal
    total_affected_candidate_count: Decimal
    max_escalation_priority_score: Decimal
    reason_codes: tuple[str, ...]
    queue_items: tuple[ResearchSourceMonitoringFailureQueueItem, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_member("status", self.status, STATUSES)
        for field_name in (
            "failure_count",
            "queue_item_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "high_refresh_risk_count",
            "missing_alternative_source_count",
            "total_affected_market_count",
            "total_affected_candidate_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_escalation_priority_score",
            _require_probability(
                "max_escalation_priority_score",
                self.max_escalation_priority_score,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "queue_items",
            _normalize_queue_items(self.queue_items),
        )
        require_paper_only_flags("report", self)
        reject_unsafe_surface_fields("report", self)
        _reject_unsafe_public_surface("report", asdict(self))
        _validate_report(self)


@dataclass(frozen=True)
class _ScoredFailure:
    event: ResearchSourceMonitoringFailureEvent
    refresh_age_seconds: Decimal | None
    refresh_risk: str
    alternative_source_count: Decimal
    reason_codes: tuple[str, ...]
    queue_status: str


def build_research_source_monitoring_failure_queue_report(
    failure_events: object,
    *,
    config: ResearchSourceMonitoringFailureQueueConfig,
    generated_at: datetime,
) -> ResearchSourceMonitoringFailureQueueReport:
    if type(config) is not ResearchSourceMonitoringFailureQueueConfig:
        raise ValueError(
            "config must be a ResearchSourceMonitoringFailureQueueConfig",
        )
    require_paper_only_flags("config", config)
    reject_unsafe_surface_fields("config", config)
    _reject_unsafe_public_surface("config", asdict(config))
    generated_at_utc = _as_utc("generated_at", generated_at)
    events = _normalize_failure_events(failure_events, generated_at=generated_at_utc)
    scored_failures = tuple(
        _scored_failure(event, config=config, generated_at=generated_at_utc)
        for event in events
    )
    queue_items = _queue_items(scored_failures)
    reason_codes = _report_reason_codes(queue_items)

    return ResearchSourceMonitoringFailureQueueReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(queue_items),
        failure_count=_decimal_count(len(scored_failures)),
        queue_item_count=_decimal_count(len(queue_items)),
        pass_count=_decimal_count(
            sum(1 for item in queue_items if item.queue_status == "pass"),
        ),
        watch_count=_decimal_count(
            sum(1 for item in queue_items if item.queue_status == "watch"),
        ),
        blocked_count=_decimal_count(
            sum(1 for item in queue_items if item.queue_status == "block"),
        ),
        high_refresh_risk_count=_decimal_count(
            sum(1 for item in queue_items if item.refresh_risk == "high"),
        ),
        missing_alternative_source_count=_reason_count(
            queue_items,
            MISSING_ALTERNATIVE_SOURCE_REASON,
        ),
        total_affected_market_count=sum(
            (item.affected_market_count for item in queue_items),
            ZERO,
        ),
        total_affected_candidate_count=sum(
            (item.affected_candidate_count for item in queue_items),
            ZERO,
        ),
        max_escalation_priority_score=max(
            (item.escalation_priority_score for item in queue_items),
            default=ZERO,
        ),
        reason_codes=reason_codes,
        queue_items=queue_items,
    )


def research_source_monitoring_failure_queue_report_payload(
    report: ResearchSourceMonitoringFailureQueueReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceMonitoringFailureQueueReport:
        raise ValueError(
            "report must be a ResearchSourceMonitoringFailureQueueReport",
        )
    require_paper_only_flags("report", report)
    reject_unsafe_surface_fields("report", report)
    _reject_unsafe_public_surface("report", asdict(report))
    payload = json_ready_no_floats(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_surface("report payload", payload)
    return payload


def _normalize_failure_events(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[ResearchSourceMonitoringFailureEvent, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("failure_events must be a list or tuple")
    events = tuple(value)
    seen_failure_ids: set[str] = set()
    for event in events:
        if type(event) is not ResearchSourceMonitoringFailureEvent:
            raise ValueError(
                "failure_events must contain ResearchSourceMonitoringFailureEvent",
            )
        require_paper_only_flags("failure event", event)
        reject_unsafe_surface_fields("failure event", event)
        _reject_unsafe_public_surface("failure event", asdict(event))
        if event.failure_id in seen_failure_ids:
            raise ValueError("failure_events must not contain duplicate failure_id")
        seen_failure_ids.add(event.failure_id)
        if event.detected_at > generated_at:
            raise ValueError("detected_at must not be in the future")
    return tuple(
        sorted(
            events,
            key=lambda event: (
                event.team_id,
                event.category_id,
                event.detected_at,
                event.failure_id,
            ),
        ),
    )


def _scored_failure(
    event: ResearchSourceMonitoringFailureEvent,
    *,
    config: ResearchSourceMonitoringFailureQueueConfig,
    generated_at: datetime,
) -> _ScoredFailure:
    refresh_age_seconds = (
        None
        if event.last_success_at is None
        else _duration_seconds(event.last_success_at, generated_at)
    )
    refresh_risk = _refresh_risk(refresh_age_seconds, config=config)
    alternative_source_count = _decimal_count(len(event.alternative_sources))
    reason_codes = _item_reason_codes(
        event,
        refresh_risk=refresh_risk,
        alternative_source_count=alternative_source_count,
        config=config,
    )
    return _ScoredFailure(
        event=event,
        refresh_age_seconds=refresh_age_seconds,
        refresh_risk=refresh_risk,
        alternative_source_count=alternative_source_count,
        reason_codes=reason_codes,
        queue_status=_item_status(reason_codes),
    )


def _queue_items(
    scored_failures: tuple[_ScoredFailure, ...],
) -> tuple[ResearchSourceMonitoringFailureQueueItem, ...]:
    ranked_failures = tuple(
        sorted(
            scored_failures,
            key=lambda item: (
                STATUS_WEIGHT[item.queue_status],
                RISK_WEIGHT[item.refresh_risk],
                -item.event.escalation_priority_score,
                -item.event.affected_market_count,
                -item.event.affected_candidate_count,
                item.event.team_id,
                item.event.category_id,
                item.event.failure_id,
            ),
        ),
    )
    return tuple(
        ResearchSourceMonitoringFailureQueueItem(
            failure_id=item.event.failure_id,
            source_alias=item.event.source_alias,
            team_id=item.event.team_id,
            category_id=item.event.category_id,
            failure_type=item.event.failure_type,
            impact_domain=item.event.impact_domain,
            queue_status=item.queue_status,
            priority_rank=_decimal_count(index),
            detected_at=item.event.detected_at,
            last_success_at=item.event.last_success_at,
            refresh_age_seconds=item.refresh_age_seconds,
            refresh_risk=item.refresh_risk,
            affected_market_count=item.event.affected_market_count,
            affected_candidate_count=item.event.affected_candidate_count,
            refresh_attempt_count=item.event.refresh_attempt_count,
            alternative_source_count=item.alternative_source_count,
            alternative_sources=item.event.alternative_sources,
            escalation_priority_score=item.event.escalation_priority_score,
            reason_codes=item.reason_codes,
        )
        for index, item in enumerate(ranked_failures, start=1)
    )


def _item_reason_codes(
    event: ResearchSourceMonitoringFailureEvent,
    *,
    refresh_risk: str,
    alternative_source_count: Decimal,
    config: ResearchSourceMonitoringFailureQueueConfig,
) -> tuple[str, ...]:
    reason_codes = {
        f"failure_type_{event.failure_type}",
        f"impact_domain_{event.impact_domain}",
        f"{refresh_risk}_refresh_risk",
    }
    if alternative_source_count < config.min_alternative_source_count:
        reason_codes.add(MISSING_ALTERNATIVE_SOURCE_REASON)
    if event.affected_market_count >= config.block_affected_market_count:
        reason_codes.add(AFFECTED_MARKET_THRESHOLD_REASON)
    if event.affected_candidate_count >= config.block_affected_candidate_count:
        reason_codes.add(AFFECTED_CANDIDATE_THRESHOLD_REASON)
    if event.escalation_priority_score >= config.block_escalation_priority_score:
        reason_codes.add(HIGH_ESCALATION_PRIORITY_REASON)
    status = _status_from_inputs(
        refresh_risk=refresh_risk,
        alternative_source_count=alternative_source_count,
        event=event,
        config=config,
    )
    if status == "pass":
        reason_codes.add(ALTERNATIVE_SOURCES_AVAILABLE_REASON)
        reason_codes.add(PASS_REASON)
    elif status == "watch":
        reason_codes.add(WATCH_REASON)
    else:
        reason_codes.add(BLOCK_REASON)
    return _normalize_reason_codes(tuple(reason_codes))


def _status_from_inputs(
    *,
    refresh_risk: str,
    alternative_source_count: Decimal,
    event: ResearchSourceMonitoringFailureEvent,
    config: ResearchSourceMonitoringFailureQueueConfig,
) -> str:
    if (
        refresh_risk == "high"
        or alternative_source_count < config.min_alternative_source_count
        or event.affected_market_count >= config.block_affected_market_count
        or event.affected_candidate_count >= config.block_affected_candidate_count
        or event.escalation_priority_score >= config.block_escalation_priority_score
    ):
        return "block"
    if (
        refresh_risk == "watch"
        or event.escalation_priority_score >= config.watch_escalation_priority_score
    ):
        return "watch"
    return "pass"


def _item_status(reason_codes: tuple[str, ...]) -> str:
    if BLOCK_REASON in reason_codes:
        return "block"
    if WATCH_REASON in reason_codes:
        return "watch"
    return "pass"


def _report_status(
    queue_items: tuple[ResearchSourceMonitoringFailureQueueItem, ...],
) -> str:
    if any(item.queue_status == "block" for item in queue_items):
        return "block"
    if any(item.queue_status == "watch" for item in queue_items):
        return "watch"
    return "pass"


def _report_reason_codes(
    queue_items: tuple[ResearchSourceMonitoringFailureQueueItem, ...],
) -> tuple[str, ...]:
    if not queue_items:
        return (NO_FAILURES_REASON,)
    if all(item.queue_status == "pass" for item in queue_items):
        return (PASS_REASON,)
    return _normalize_reason_codes(
        tuple(reason for item in queue_items for reason in item.reason_codes),
    )


def _refresh_risk(
    refresh_age_seconds: Decimal | None,
    *,
    config: ResearchSourceMonitoringFailureQueueConfig,
) -> str:
    if refresh_age_seconds is None:
        return "high"
    if refresh_age_seconds >= config.block_refresh_age_seconds:
        return "high"
    if refresh_age_seconds >= config.watch_refresh_age_seconds:
        return "watch"
    return "low"


def _normalize_queue_items(
    value: object,
) -> tuple[ResearchSourceMonitoringFailureQueueItem, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("queue_items must be a list or tuple")
    items = tuple(value)
    seen_failure_ids: set[str] = set()
    for item in items:
        if type(item) is not ResearchSourceMonitoringFailureQueueItem:
            raise ValueError(
                "queue_items must contain ResearchSourceMonitoringFailureQueueItem",
            )
        require_paper_only_flags("queue item", item)
        reject_unsafe_surface_fields("queue item", item)
        _reject_unsafe_public_surface("queue item", asdict(item))
        if item.failure_id in seen_failure_ids:
            raise ValueError("queue_items must not contain duplicate failure_id")
        seen_failure_ids.add(item.failure_id)
    expected_ranks = tuple(_decimal_count(index) for index in range(1, len(items) + 1))
    if tuple(item.priority_rank for item in items) != expected_ranks:
        raise ValueError("queue_items must have contiguous priority_rank values")
    return items


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_reason_code("reason_codes", reason_code)
        normalized.append(reason_code)
    return tuple(sorted(set(normalized)))


def _validate_queue_item(item: ResearchSourceMonitoringFailureQueueItem) -> None:
    if (item.last_success_at is None) != (item.refresh_age_seconds is None):
        raise ValueError("refresh_age_seconds presence must match last_success_at")
    if item.alternative_source_count != _decimal_count(len(item.alternative_sources)):
        raise ValueError("alternative_source_count must match alternative_sources")
    if item.queue_status != _item_status(item.reason_codes):
        raise ValueError("queue_status must match reason_codes")
    expected_risk_reason = f"{item.refresh_risk}_refresh_risk"
    if expected_risk_reason not in item.reason_codes:
        raise ValueError("refresh_risk must match reason_codes")


def _validate_report(report: ResearchSourceMonitoringFailureQueueReport) -> None:
    if report.queue_item_count != _decimal_count(len(report.queue_items)):
        raise ValueError("queue_item_count must match queue_items")
    if report.queue_item_count > report.failure_count:
        raise ValueError("queue_item_count must not exceed failure_count")
    if report.pass_count != _status_count(report.queue_items, "pass"):
        raise ValueError("pass_count must match queue_items")
    if report.watch_count != _status_count(report.queue_items, "watch"):
        raise ValueError("watch_count must match queue_items")
    if report.blocked_count != _status_count(report.queue_items, "block"):
        raise ValueError("blocked_count must match queue_items")
    if report.high_refresh_risk_count != _decimal_count(
        sum(1 for item in report.queue_items if item.refresh_risk == "high"),
    ):
        raise ValueError("high_refresh_risk_count must match queue_items")
    if report.missing_alternative_source_count != _reason_count(
        report.queue_items,
        MISSING_ALTERNATIVE_SOURCE_REASON,
    ):
        raise ValueError("missing_alternative_source_count must match queue_items")
    if report.total_affected_market_count != sum(
        (item.affected_market_count for item in report.queue_items),
        ZERO,
    ):
        raise ValueError("total_affected_market_count must match queue_items")
    if report.total_affected_candidate_count != sum(
        (item.affected_candidate_count for item in report.queue_items),
        ZERO,
    ):
        raise ValueError("total_affected_candidate_count must match queue_items")
    if report.max_escalation_priority_score != max(
        (item.escalation_priority_score for item in report.queue_items),
        default=ZERO,
    ):
        raise ValueError("max_escalation_priority_score must match queue_items")
    if report.reason_codes != _report_reason_codes(report.queue_items):
        raise ValueError("reason_codes must match queue_items")
    if report.status != _report_status(report.queue_items):
        raise ValueError("status must match queue_items")


def _status_count(
    queue_items: tuple[ResearchSourceMonitoringFailureQueueItem, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for item in queue_items if item.queue_status == status))


def _reason_count(
    queue_items: tuple[ResearchSourceMonitoringFailureQueueItem, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for item in queue_items if reason_code in item.reason_codes))


def _duration_seconds(earlier: datetime, later: datetime) -> Decimal:
    earlier_utc = _as_utc("earlier", earlier)
    later_utc = _as_utc("later", later)
    if earlier_utc > later_utc:
        raise ValueError("earlier datetime must be <= later datetime")
    delta = later_utc - earlier_utc
    return _quantize(
        (Decimal(delta.days) * SECONDS_PER_DAY)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND),
    )


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or isinstance(value, bool):
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return Decimal(value).quantize(QUANT)


def _normalize_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_whole_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value().quantize(QUANT):
        raise ValueError(f"{field_name} must be a whole count")
    return decimal_value


def _require_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be <= 1")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != QUANT.as_tuple().exponent:
        raise ValueError(f"{field_name} must use 6 decimal places")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _normalize_public_string_tuple(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    normalized = tuple(_require_public_string(field_name, item) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    return tuple(sorted(normalized))


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be nonempty public text")
    if len(value) > 128:
        raise ValueError(f"{field_name} must not exceed 128 characters")
    allowed_characters = set("abcdefghijklmnopqrstuvwxyz0123456789._-")
    if any(character not in allowed_characters for character in value):
        raise ValueError(f"{field_name} must be public text")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must contain strings")
    allowed_reason_codes = {
        NO_FAILURES_REASON,
        PASS_REASON,
        WATCH_REASON,
        BLOCK_REASON,
        LOW_REFRESH_RISK_REASON,
        WATCH_REFRESH_RISK_REASON,
        HIGH_REFRESH_RISK_REASON,
        ALTERNATIVE_SOURCES_AVAILABLE_REASON,
        MISSING_ALTERNATIVE_SOURCE_REASON,
        AFFECTED_MARKET_THRESHOLD_REASON,
        AFFECTED_CANDIDATE_THRESHOLD_REASON,
        HIGH_ESCALATION_PRIORITY_REASON,
    }
    allowed_reason_codes.update(f"failure_type_{value}" for value in FAILURE_TYPES)
    allowed_reason_codes.update(f"impact_domain_{value}" for value in IMPACT_DOMAINS)
    if value not in allowed_reason_codes:
        raise ValueError(f"{field_name} contains an unknown reason code")
    _reject_unsafe_public_string(field_name, value)


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} keys must be strings")
            _reject_unsafe_public_key(label, key)
            _reject_unsafe_public_surface(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_surface(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_string(label, value)


def _reject_unsafe_public_key(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS):
        raise ValueError(f"unsafe public key in {label}: {value}")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS):
        raise ValueError(f"{field_name} must not contain unsafe private text")
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS):
        raise ValueError(f"{field_name} must not contain unsafe private text")


__all__ = (
    "ResearchSourceMonitoringFailureEvent",
    "ResearchSourceMonitoringFailureQueueConfig",
    "ResearchSourceMonitoringFailureQueueItem",
    "ResearchSourceMonitoringFailureQueueReport",
    "build_research_source_monitoring_failure_queue_report",
    "research_source_monitoring_failure_queue_report_payload",
)
