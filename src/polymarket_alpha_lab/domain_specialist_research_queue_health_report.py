from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from decimal import Decimal, InvalidOperation, localcontext
import hashlib
import json
from typing import Any


__all__ = (
    "DEFAULT_DOMAIN_SPECIALIST_RESEARCH_QUEUE_HEALTH_REPORT_CONFIG_VERSION",
    "DomainSpecialistResearchQueueHealthConfig",
    "DomainSpecialistResearchQueueHealthInput",
    "DomainSpecialistResearchQueueHealthReport",
    "build_domain_specialist_research_queue_health_report",
    "domain_specialist_research_queue_health_report_digest",
    "domain_specialist_research_queue_health_report_payload",
)


DEFAULT_DOMAIN_SPECIALIST_RESEARCH_QUEUE_HEALTH_REPORT_CONFIG_VERSION = (
    "domain-specialist-research-queue-health-report-v0"
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
RATIO_QUANTUM = Decimal("0.000001")
BANDS = ("pass", "watch", "block")
BLOCK_REASON_PRIORITY = (
    "ready_candidate_ratio_block",
    "stale_candidate_ratio_block",
    "blocked_candidate_ratio_block",
    "average_source_age_block",
    "average_review_lag_block",
    "supabase_memory_not_ready_block",
    "playbook_not_ready_block",
    "queue_health_score_block",
)
ATTENTION_REASON_PRIORITY = (
    "ready_candidate_ratio_watch",
    "stale_candidate_ratio_watch",
    "blocked_candidate_ratio_watch",
    "average_source_age_watch",
    "average_review_lag_watch",
    "queue_health_score_watch",
)


@dataclass(frozen=True)
class DomainSpecialistResearchQueueHealthConfig:
    config_version: str = DEFAULT_DOMAIN_SPECIALIST_RESEARCH_QUEUE_HEALTH_REPORT_CONFIG_VERSION
    minimum_pass_ready_ratio: Decimal = Decimal("0.700000")
    minimum_watch_ready_ratio: Decimal = Decimal("0.400000")
    maximum_pass_stale_ratio: Decimal = Decimal("0.100000")
    maximum_watch_stale_ratio: Decimal = Decimal("0.250000")
    maximum_pass_blocked_ratio: Decimal = Decimal("0.050000")
    maximum_watch_blocked_ratio: Decimal = Decimal("0.150000")
    maximum_pass_source_age_seconds: Decimal = Decimal("86400.000000")
    maximum_watch_source_age_seconds: Decimal = Decimal("259200.000000")
    maximum_pass_review_lag_seconds: Decimal = Decimal("43200.000000")
    maximum_watch_review_lag_seconds: Decimal = Decimal("172800.000000")
    queue_health_pass_score: Decimal = Decimal("0.800000")
    queue_health_watch_score: Decimal = Decimal("0.500000")
    ready_ratio_weight: Decimal = Decimal("0.400000")
    source_age_weight: Decimal = Decimal("0.200000")
    review_lag_weight: Decimal = Decimal("0.200000")
    memory_readiness_weight: Decimal = Decimal("0.100000")
    playbook_readiness_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("config", self, DomainSpecialistResearchQueueHealthConfig)
        if self.config_version != DEFAULT_DOMAIN_SPECIALIST_RESEARCH_QUEUE_HEALTH_REPORT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "minimum_pass_ready_ratio",
            "minimum_watch_ready_ratio",
            "maximum_pass_stale_ratio",
            "maximum_watch_stale_ratio",
            "maximum_pass_blocked_ratio",
            "maximum_watch_blocked_ratio",
            "queue_health_pass_score",
            "queue_health_watch_score",
            "ready_ratio_weight",
            "source_age_weight",
            "review_lag_weight",
            "memory_readiness_weight",
            "playbook_readiness_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "maximum_pass_source_age_seconds",
            "maximum_watch_source_age_seconds",
            "maximum_pass_review_lag_seconds",
            "maximum_watch_review_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.minimum_pass_ready_ratio < self.minimum_watch_ready_ratio:
            raise ValueError("pass ready threshold must be at least watch threshold")
        if self.maximum_pass_stale_ratio > self.maximum_watch_stale_ratio:
            raise ValueError("pass stale threshold must not exceed watch threshold")
        if self.maximum_pass_blocked_ratio > self.maximum_watch_blocked_ratio:
            raise ValueError("pass blocked threshold must not exceed watch threshold")
        if self.maximum_pass_source_age_seconds > self.maximum_watch_source_age_seconds:
            raise ValueError("pass source age threshold must not exceed watch threshold")
        if self.maximum_pass_review_lag_seconds > self.maximum_watch_review_lag_seconds:
            raise ValueError("pass review lag threshold must not exceed watch threshold")
        if self.queue_health_pass_score < self.queue_health_watch_score:
            raise ValueError("pass score threshold must be at least watch threshold")
        if _weight_sum(self) != ONE:
            raise ValueError("queue health weights must sum to one")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class DomainSpecialistResearchQueueHealthInput:
    queued_candidate_count: Decimal
    stale_candidate_count: Decimal
    blocked_candidate_count: Decimal
    ready_candidate_count: Decimal
    average_source_age_seconds: Decimal
    average_review_lag_seconds: Decimal
    supabase_memory_ready: bool
    playbook_ready: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("input", self, DomainSpecialistResearchQueueHealthInput)
        for field_name in (
            "queued_candidate_count",
            "stale_candidate_count",
            "blocked_candidate_count",
            "ready_candidate_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_source_age_seconds", "average_review_lag_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_bool("supabase_memory_ready", self.supabase_memory_ready)
        _require_bool("playbook_ready", self.playbook_ready)
        if self.ready_candidate_count > self.queued_candidate_count:
            raise ValueError("ready_candidate_count must not exceed queued_candidate_count")
        if self.stale_candidate_count > self.queued_candidate_count:
            raise ValueError("stale_candidate_count must not exceed queued_candidate_count")
        if self.blocked_candidate_count > self.queued_candidate_count:
            raise ValueError("blocked_candidate_count must not exceed queued_candidate_count")
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class DomainSpecialistResearchQueueHealthReport:
    config_version: str
    queued_candidate_count: Decimal
    stale_candidate_count: Decimal
    blocked_candidate_count: Decimal
    ready_candidate_count: Decimal
    average_source_age_seconds: Decimal
    average_review_lag_seconds: Decimal
    supabase_memory_ready: bool
    playbook_ready: bool
    ready_ratio: Decimal
    stale_ratio: Decimal
    blocked_ratio: Decimal
    queue_health_score: Decimal
    queue_health_band: str
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("report", self, DomainSpecialistResearchQueueHealthReport)
        if self.config_version != DEFAULT_DOMAIN_SPECIALIST_RESEARCH_QUEUE_HEALTH_REPORT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "queued_candidate_count",
            "stale_candidate_count",
            "blocked_candidate_count",
            "ready_candidate_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_source_age_seconds", "average_review_lag_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_bool("supabase_memory_ready", self.supabase_memory_ready)
        _require_bool("playbook_ready", self.playbook_ready)
        for field_name in ("ready_ratio", "stale_ratio", "blocked_ratio", "queue_health_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_band("queue_health_band", self.queue_health_band)
        object.__setattr__(
            self,
            "blocked_reason_codes",
            _normalize_reason_codes(
                "blocked_reason_codes",
                self.blocked_reason_codes,
                BLOCK_REASON_PRIORITY,
            ),
        )
        object.__setattr__(
            self,
            "attention_reason_codes",
            _normalize_reason_codes(
                "attention_reason_codes",
                self.attention_reason_codes,
                ATTENTION_REASON_PRIORITY,
            ),
        )
        if self.ready_candidate_count > self.queued_candidate_count:
            raise ValueError("ready_candidate_count must not exceed queued_candidate_count")
        if self.stale_candidate_count > self.queued_candidate_count:
            raise ValueError("stale_candidate_count must not exceed queued_candidate_count")
        if self.blocked_candidate_count > self.queued_candidate_count:
            raise ValueError("blocked_candidate_count must not exceed queued_candidate_count")
        _require_hard_flags("report", self)

    @property
    def public_payload(self) -> dict[str, Any]:
        return domain_specialist_research_queue_health_report_payload(self)

    @property
    def digest(self) -> str:
        return domain_specialist_research_queue_health_report_digest(self)


def build_domain_specialist_research_queue_health_report(
    value: DomainSpecialistResearchQueueHealthInput,
    *,
    config: DomainSpecialistResearchQueueHealthConfig,
) -> DomainSpecialistResearchQueueHealthReport:
    if type(config) is not DomainSpecialistResearchQueueHealthConfig:
        raise ValueError("config must be a DomainSpecialistResearchQueueHealthConfig")
    if type(value) is not DomainSpecialistResearchQueueHealthInput:
        raise ValueError("value must be a DomainSpecialistResearchQueueHealthInput")
    _require_hard_flags("config", config)
    _require_hard_flags("input", value)
    ready_ratio = _safe_ratio(value.ready_candidate_count, value.queued_candidate_count)
    stale_ratio = _safe_ratio(value.stale_candidate_count, value.queued_candidate_count)
    blocked_ratio = _safe_ratio(value.blocked_candidate_count, value.queued_candidate_count)
    source_age_score = _score_for_maximum(
        value.average_source_age_seconds,
        config.maximum_watch_source_age_seconds,
    )
    review_lag_score = _score_for_maximum(
        value.average_review_lag_seconds,
        config.maximum_watch_review_lag_seconds,
    )
    memory_readiness_score = ONE if value.supabase_memory_ready else ZERO
    playbook_readiness_score = ONE if value.playbook_ready else ZERO
    queue_health_score = _queue_health_score(
        ready_ratio=ready_ratio,
        source_age_score=source_age_score,
        review_lag_score=review_lag_score,
        memory_readiness_score=memory_readiness_score,
        playbook_readiness_score=playbook_readiness_score,
        config=config,
    )
    blocked_reason_codes = _blocked_reason_codes(
        ready_ratio=ready_ratio,
        stale_ratio=stale_ratio,
        blocked_ratio=blocked_ratio,
        source_age_seconds=value.average_source_age_seconds,
        review_lag_seconds=value.average_review_lag_seconds,
        queue_health_score=queue_health_score,
        memory_ready=value.supabase_memory_ready,
        playbook_ready=value.playbook_ready,
        config=config,
    )
    attention_reason_codes = ()
    if not blocked_reason_codes:
        attention_reason_codes = _attention_reason_codes(
            ready_ratio=ready_ratio,
            stale_ratio=stale_ratio,
            blocked_ratio=blocked_ratio,
            source_age_seconds=value.average_source_age_seconds,
            review_lag_seconds=value.average_review_lag_seconds,
            queue_health_score=queue_health_score,
            config=config,
        )
    return DomainSpecialistResearchQueueHealthReport(
        config_version=config.config_version,
        queued_candidate_count=value.queued_candidate_count,
        stale_candidate_count=value.stale_candidate_count,
        blocked_candidate_count=value.blocked_candidate_count,
        ready_candidate_count=value.ready_candidate_count,
        average_source_age_seconds=value.average_source_age_seconds,
        average_review_lag_seconds=value.average_review_lag_seconds,
        supabase_memory_ready=value.supabase_memory_ready,
        playbook_ready=value.playbook_ready,
        ready_ratio=ready_ratio,
        stale_ratio=stale_ratio,
        blocked_ratio=blocked_ratio,
        queue_health_score=queue_health_score,
        queue_health_band=_queue_health_band(
            queue_health_score,
            blocked_reason_codes,
            attention_reason_codes,
            config,
        ),
        blocked_reason_codes=blocked_reason_codes,
        attention_reason_codes=attention_reason_codes,
    )


def domain_specialist_research_queue_health_report_payload(
    report: DomainSpecialistResearchQueueHealthReport,
) -> dict[str, Any]:
    if type(report) is not DomainSpecialistResearchQueueHealthReport:
        raise ValueError("report must be a DomainSpecialistResearchQueueHealthReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def domain_specialist_research_queue_health_report_digest(
    report: DomainSpecialistResearchQueueHealthReport,
) -> str:
    payload = domain_specialist_research_queue_health_report_payload(report)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _queue_health_score(
    *,
    ready_ratio: Decimal,
    source_age_score: Decimal,
    review_lag_score: Decimal,
    memory_readiness_score: Decimal,
    playbook_readiness_score: Decimal,
    config: DomainSpecialistResearchQueueHealthConfig,
) -> Decimal:
    with localcontext() as context:
        context.prec = 28
        return _quantize(
            ready_ratio * config.ready_ratio_weight
            + source_age_score * config.source_age_weight
            + review_lag_score * config.review_lag_weight
            + memory_readiness_score * config.memory_readiness_weight
            + playbook_readiness_score * config.playbook_readiness_weight,
        )


def _blocked_reason_codes(
    *,
    ready_ratio: Decimal,
    stale_ratio: Decimal,
    blocked_ratio: Decimal,
    source_age_seconds: Decimal,
    review_lag_seconds: Decimal,
    queue_health_score: Decimal,
    memory_ready: bool,
    playbook_ready: bool,
    config: DomainSpecialistResearchQueueHealthConfig,
) -> tuple[str, ...]:
    values: list[str] = []
    if ready_ratio < config.minimum_watch_ready_ratio:
        values.append("ready_candidate_ratio_block")
    if stale_ratio > config.maximum_watch_stale_ratio:
        values.append("stale_candidate_ratio_block")
    if blocked_ratio > config.maximum_watch_blocked_ratio:
        values.append("blocked_candidate_ratio_block")
    if source_age_seconds > config.maximum_watch_source_age_seconds:
        values.append("average_source_age_block")
    if review_lag_seconds > config.maximum_watch_review_lag_seconds:
        values.append("average_review_lag_block")
    if memory_ready is not True:
        values.append("supabase_memory_not_ready_block")
    if playbook_ready is not True:
        values.append("playbook_not_ready_block")
    if queue_health_score < config.queue_health_watch_score:
        values.append("queue_health_score_block")
    return _normalize_reason_codes("blocked_reason_codes", tuple(values), BLOCK_REASON_PRIORITY)


def _attention_reason_codes(
    *,
    ready_ratio: Decimal,
    stale_ratio: Decimal,
    blocked_ratio: Decimal,
    source_age_seconds: Decimal,
    review_lag_seconds: Decimal,
    queue_health_score: Decimal,
    config: DomainSpecialistResearchQueueHealthConfig,
) -> tuple[str, ...]:
    values: list[str] = []
    if ready_ratio < config.minimum_pass_ready_ratio:
        values.append("ready_candidate_ratio_watch")
    if stale_ratio > config.maximum_pass_stale_ratio:
        values.append("stale_candidate_ratio_watch")
    if blocked_ratio > config.maximum_pass_blocked_ratio:
        values.append("blocked_candidate_ratio_watch")
    if source_age_seconds > config.maximum_pass_source_age_seconds:
        values.append("average_source_age_watch")
    if review_lag_seconds > config.maximum_pass_review_lag_seconds:
        values.append("average_review_lag_watch")
    if queue_health_score < config.queue_health_pass_score:
        values.append("queue_health_score_watch")
    return _normalize_reason_codes(
        "attention_reason_codes",
        tuple(values),
        ATTENTION_REASON_PRIORITY,
    )


def _queue_health_band(
    queue_health_score: Decimal,
    blocked_reason_codes: tuple[str, ...],
    attention_reason_codes: tuple[str, ...],
    config: DomainSpecialistResearchQueueHealthConfig,
) -> str:
    if blocked_reason_codes or queue_health_score < config.queue_health_watch_score:
        return "block"
    if attention_reason_codes or queue_health_score < config.queue_health_pass_score:
        return "watch"
    return "pass"


def _score_for_maximum(value: Decimal, maximum_watch_value: Decimal) -> Decimal:
    if maximum_watch_value == ZERO:
        return ZERO
    if value >= maximum_watch_value:
        return ZERO
    with localcontext() as context:
        context.prec = 28
        return _quantize(ONE - (value / maximum_watch_value))


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext() as context:
        context.prec = 28
        return _quantize(numerator / denominator)


def _weight_sum(config: DomainSpecialistResearchQueueHealthConfig) -> Decimal:
    return _quantize(
        config.ready_ratio_weight
        + config.source_age_weight
        + config.review_lag_weight
        + config.memory_readiness_weight
        + config.playbook_readiness_weight,
    )


def _payload_value(value: object) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
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


def _require_exact_type(
    field_name: str,
    value: object,
    expected_type: type[object],
) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} {flag_name} must be True")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    try:
        if not value.is_finite():
            raise ValueError(f"{field_name} must be finite")
        return value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(normalized)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return _quantize(normalized)


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return _quantize(normalized)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_band(field_name: str, value: object) -> None:
    if value not in BANDS:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _normalize_reason_codes(
    field_name: str,
    values: object,
    priority: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        if type(value) is not str or value not in priority:
            raise ValueError(f"{field_name} must contain supported reason codes")
        if value not in normalized:
            normalized.append(value)
    return tuple(code for code in priority if code in normalized)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)
