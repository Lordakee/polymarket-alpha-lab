"""Pure report-only reducer for sanitized Scrapling capture health."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_SOURCE_SCRAPLING_CAPTURE_HEALTH_REPORT_CONFIG_VERSION = (
    "research-source-scrapling-capture-health-report-v0"
)

QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
COUNT_ZERO = Decimal("0")
MICROSECOND_DIVISOR = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

STATUSES = ("pass", "watch", "block")
NEXT_STEPS = {
    "pass": "continue_report_only_scrapling_capture_review",
    "watch": "review_report_only_scrapling_capture_health",
    "block": "block_report_only_scrapling_capture_review",
}

PASS_REASON = "scrapling_capture_health_passed"
NO_INPUTS_REASON = "scrapling_capture_health_no_inputs"
REPORT_BLOCK_REASON = "scrapling_capture_health_block"
REPORT_WATCH_REASON = "scrapling_capture_health_watch"
REASON_CODE_ORDER = (
    "capture_staleness_block",
    "capture_freshness_block",
    "capture_freshness_watch",
    "parse_completeness_block",
    "parse_completeness_watch",
    "antibot_fallback_pressure_block",
    "antibot_fallback_pressure_watch",
    "source_family_quorum_block",
    "source_family_quorum_watch",
    NO_INPUTS_REASON,
    REPORT_BLOCK_REASON,
    REPORT_WATCH_REASON,
    PASS_REASON,
)

PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
UNSAFE_PUBLIC_FRAGMENTS = (
    "://",
    "www.",
    "raw",
    "url",
    "text",
    "candidate",
    "market",
    "slug",
    "question",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "network",
    "database",
    "secret",
    "password",
    "private_key",
    "api_key",
    "authentication",
    "authorization",
    "auth",
    "bearer",
    "credential",
    "recommendation",
    "sizing",
    "live",
)


@dataclass(frozen=True)
class ResearchSourceScraplingCaptureHealthConfig:
    config_version: str = DEFAULT_RESEARCH_SOURCE_SCRAPLING_CAPTURE_HEALTH_REPORT_CONFIG_VERSION
    fresh_capture_max_age_seconds: Decimal = Decimal("1800.000000")
    stale_capture_block_age_seconds: Decimal = Decimal("7200.000000")
    min_fresh_capture_pass_ratio: Decimal = Decimal("0.800000")
    min_fresh_capture_block_ratio: Decimal = Decimal("0.500000")
    min_parse_completeness_pass_ratio: Decimal = Decimal("0.900000")
    min_parse_completeness_block_ratio: Decimal = Decimal("0.600000")
    max_antibot_fallback_pass_ratio: Decimal = Decimal("0.100000")
    max_antibot_fallback_block_ratio: Decimal = Decimal("0.400000")
    min_source_family_pass_count: Decimal = Decimal("3")
    min_source_family_block_count: Decimal = Decimal("2")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingCaptureHealthConfig:
            raise TypeError(
                "ResearchSourceScraplingCaptureHealthConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceScraplingCaptureHealthConfig:
            raise ValueError(
                "config must be exactly ResearchSourceScraplingCaptureHealthConfig",
            )
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_SCRAPLING_CAPTURE_HEALTH_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_public_identifier("config_version", self.config_version)
        for field_name in (
            "fresh_capture_max_age_seconds",
            "stale_capture_block_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_fresh_capture_pass_ratio",
            "min_fresh_capture_block_ratio",
            "min_parse_completeness_pass_ratio",
            "min_parse_completeness_block_ratio",
            "max_antibot_fallback_pass_ratio",
            "max_antibot_fallback_block_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_source_family_pass_count",
            "min_source_family_block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        if self.fresh_capture_max_age_seconds >= self.stale_capture_block_age_seconds:
            raise ValueError(
                "fresh_capture_max_age_seconds must be below "
                "stale_capture_block_age_seconds",
            )
        if self.min_fresh_capture_block_ratio > self.min_fresh_capture_pass_ratio:
            raise ValueError(
                "min_fresh_capture_block_ratio must not exceed "
                "min_fresh_capture_pass_ratio",
            )
        if (
            self.min_parse_completeness_block_ratio
            > self.min_parse_completeness_pass_ratio
        ):
            raise ValueError(
                "min_parse_completeness_block_ratio must not exceed "
                "min_parse_completeness_pass_ratio",
            )
        if self.max_antibot_fallback_pass_ratio > self.max_antibot_fallback_block_ratio:
            raise ValueError(
                "max_antibot_fallback_pass_ratio must not exceed "
                "max_antibot_fallback_block_ratio",
            )
        if self.min_source_family_block_count > self.min_source_family_pass_count:
            raise ValueError(
                "min_source_family_block_count must not exceed "
                "min_source_family_pass_count",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceScraplingCaptureObservation:
    source_family: str
    captured_at: datetime
    captured_field_count: Decimal
    expected_field_count: Decimal
    capture_attempt_count: Decimal
    antibot_fallback_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingCaptureObservation:
            raise TypeError(
                "ResearchSourceScraplingCaptureObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceScraplingCaptureObservation:
            raise ValueError(
                "observation must be exactly ResearchSourceScraplingCaptureObservation",
            )
        _require_public_identifier("source_family", self.source_family)
        object.__setattr__(self, "captured_at", _as_utc("captured_at", self.captured_at))
        for field_name in (
            "captured_field_count",
            "expected_field_count",
            "capture_attempt_count",
            "antibot_fallback_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.expected_field_count == COUNT_ZERO:
            raise ValueError("expected_field_count must be positive")
        if self.capture_attempt_count == COUNT_ZERO:
            raise ValueError("capture_attempt_count must be positive")
        if self.captured_field_count > self.expected_field_count:
            raise ValueError("captured field count must not exceed expected field count")
        if self.antibot_fallback_count > self.capture_attempt_count:
            raise ValueError("fallback count must not exceed capture attempt count")
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchSourceScraplingCaptureHealthReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingCaptureHealthReasonCodeCount:
            raise TypeError(
                "ResearchSourceScraplingCaptureHealthReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceScraplingCaptureHealthReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "ResearchSourceScraplingCaptureHealthReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class ResearchSourceScraplingCaptureHealthReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    fresh_capture_count: Decimal
    stale_capture_count: Decimal
    source_family_count: Decimal
    captured_field_count: Decimal
    expected_field_count: Decimal
    capture_attempt_count: Decimal
    antibot_fallback_count: Decimal
    max_capture_age_seconds: Decimal
    average_capture_age_seconds: Decimal
    capture_freshness_ratio: Decimal
    parse_completeness_ratio: Decimal
    antibot_fallback_pressure_ratio: Decimal
    source_family_quorum_ratio: Decimal
    capture_freshness_status: str
    parse_completeness_status: str
    antibot_fallback_status: str
    source_family_quorum_status: str
    status: str
    next_step: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchSourceScraplingCaptureHealthReasonCodeCount,
        ...,
    ]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingCaptureHealthReport:
            raise TypeError(
                "ResearchSourceScraplingCaptureHealthReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceScraplingCaptureHealthReport:
            raise ValueError(
                "report must be exactly ResearchSourceScraplingCaptureHealthReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        for field_name in (
            "input_count",
            "fresh_capture_count",
            "stale_capture_count",
            "source_family_count",
            "captured_field_count",
            "expected_field_count",
            "capture_attempt_count",
            "antibot_fallback_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_capture_age_seconds", "average_capture_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "capture_freshness_ratio",
            "parse_completeness_ratio",
            "antibot_fallback_pressure_ratio",
            "source_family_quorum_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "capture_freshness_status",
            "parse_completeness_status",
            "antibot_fallback_status",
            "source_family_quorum_status",
            "status",
        ):
            _require_member(field_name, getattr(self, field_name), STATUSES)
        _require_public_identifier("next_step", self.next_step)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")
        _require_digest("derived_validation_digest", self.derived_validation_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return research_source_scrapling_capture_health_report_payload(self)


def build_research_source_scrapling_capture_health_report(
    observations: Iterable[ResearchSourceScraplingCaptureObservation],
    *,
    config: ResearchSourceScraplingCaptureHealthConfig,
    generated_at: datetime,
) -> ResearchSourceScraplingCaptureHealthReport:
    if type(config) is not ResearchSourceScraplingCaptureHealthConfig:
        raise ValueError(
            "config must be exactly ResearchSourceScraplingCaptureHealthConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    for observation in normalized_observations:
        if observation.captured_at > generated_at:
            raise ValueError("captured_at cannot be after generated_at")

    input_count = _count_decimal(len(normalized_observations))
    ages = tuple(
        _age_seconds(generated_at, observation.captured_at)
        for observation in normalized_observations
    )
    fresh_count = _count_decimal(
        sum(1 for age in ages if age <= config.fresh_capture_max_age_seconds),
    )
    stale_count = _count_decimal(
        sum(1 for age in ages if age >= config.stale_capture_block_age_seconds),
    )
    family_count = _count_decimal(
        len({observation.source_family for observation in normalized_observations}),
    )
    captured_field_count = sum(
        (observation.captured_field_count for observation in normalized_observations),
        COUNT_ZERO,
    )
    expected_field_count = sum(
        (observation.expected_field_count for observation in normalized_observations),
        COUNT_ZERO,
    )
    attempt_count = sum(
        (observation.capture_attempt_count for observation in normalized_observations),
        COUNT_ZERO,
    )
    fallback_count = sum(
        (observation.antibot_fallback_count for observation in normalized_observations),
        COUNT_ZERO,
    )
    capture_freshness_ratio = _safe_ratio(fresh_count, input_count)
    parse_completeness_ratio = _safe_ratio(captured_field_count, expected_field_count)
    fallback_pressure_ratio = _safe_ratio(fallback_count, attempt_count)
    family_quorum_ratio = min(
        ONE,
        _safe_ratio(family_count, config.min_source_family_pass_count),
    )
    max_age = max(ages, default=ZERO)
    average_age = _safe_ratio(sum(ages, ZERO), input_count)

    capture_freshness_status = _freshness_status(
        capture_freshness_ratio,
        stale_count,
        config,
    )
    parse_completeness_status = _lower_is_worse_status(
        parse_completeness_ratio,
        block_threshold=config.min_parse_completeness_block_ratio,
        pass_threshold=config.min_parse_completeness_pass_ratio,
    )
    fallback_status = _higher_is_worse_status(
        fallback_pressure_ratio,
        pass_threshold=config.max_antibot_fallback_pass_ratio,
        block_threshold=config.max_antibot_fallback_block_ratio,
    )
    family_status = _family_quorum_status(family_count, config)
    status = _aggregate_status(
        (
            capture_freshness_status,
            parse_completeness_status,
            fallback_status,
            family_status,
        ),
    )
    reason_codes = _report_reason_codes(
        input_count=input_count,
        capture_freshness_ratio=capture_freshness_ratio,
        stale_count=stale_count,
        parse_completeness_ratio=parse_completeness_ratio,
        fallback_pressure_ratio=fallback_pressure_ratio,
        family_count=family_count,
        status=status,
        config=config,
    )

    return ResearchSourceScraplingCaptureHealthReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=input_count,
        fresh_capture_count=fresh_count,
        stale_capture_count=stale_count,
        source_family_count=family_count,
        captured_field_count=captured_field_count,
        expected_field_count=expected_field_count,
        capture_attempt_count=attempt_count,
        antibot_fallback_count=fallback_count,
        max_capture_age_seconds=max_age,
        average_capture_age_seconds=average_age,
        capture_freshness_ratio=capture_freshness_ratio,
        parse_completeness_ratio=parse_completeness_ratio,
        antibot_fallback_pressure_ratio=fallback_pressure_ratio,
        source_family_quorum_ratio=family_quorum_ratio,
        capture_freshness_status=capture_freshness_status,
        parse_completeness_status=parse_completeness_status,
        antibot_fallback_status=fallback_status,
        source_family_quorum_status=family_status,
        status=status,
        next_step=NEXT_STEPS[status],
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def research_source_scrapling_capture_health_report_payload(
    report: ResearchSourceScraplingCaptureHealthReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceScraplingCaptureHealthReport:
        raise ValueError(
            "report must be exactly ResearchSourceScraplingCaptureHealthReport",
        )
    _validate_report_consistency(report)
    expected_digest = _report_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload(payload)
    return payload


def research_source_scrapling_capture_health_report_digest(
    report: ResearchSourceScraplingCaptureHealthReport,
) -> str:
    payload = research_source_scrapling_capture_health_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


def _normalize_observations(
    observations: Iterable[ResearchSourceScraplingCaptureObservation],
) -> tuple[ResearchSourceScraplingCaptureObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        normalized = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    for observation in normalized:
        if type(observation) is not ResearchSourceScraplingCaptureObservation:
            raise ValueError(
                "observations must contain ResearchSourceScraplingCaptureObservation",
            )
        _require_hard_flags("observation", observation)
    return tuple(sorted(normalized, key=_observation_sort_key))


def _observation_sort_key(
    observation: ResearchSourceScraplingCaptureObservation,
) -> tuple[str, str, Decimal, Decimal, Decimal, Decimal]:
    return (
        observation.source_family,
        observation.captured_at.isoformat(),
        observation.captured_field_count,
        observation.expected_field_count,
        observation.capture_attempt_count,
        observation.antibot_fallback_count,
    )


def _freshness_status(
    freshness_ratio: Decimal,
    stale_count: Decimal,
    config: ResearchSourceScraplingCaptureHealthConfig,
) -> str:
    if stale_count > COUNT_ZERO or freshness_ratio < config.min_fresh_capture_block_ratio:
        return "block"
    if freshness_ratio < config.min_fresh_capture_pass_ratio:
        return "watch"
    return "pass"


def _lower_is_worse_status(
    value: Decimal,
    *,
    block_threshold: Decimal,
    pass_threshold: Decimal,
) -> str:
    if value < block_threshold:
        return "block"
    if value < pass_threshold:
        return "watch"
    return "pass"


def _higher_is_worse_status(
    value: Decimal,
    *,
    pass_threshold: Decimal,
    block_threshold: Decimal,
) -> str:
    if value > block_threshold:
        return "block"
    if value > pass_threshold:
        return "watch"
    return "pass"


def _family_quorum_status(
    family_count: Decimal,
    config: ResearchSourceScraplingCaptureHealthConfig,
) -> str:
    if family_count < config.min_source_family_block_count:
        return "block"
    if family_count < config.min_source_family_pass_count:
        return "watch"
    return "pass"


def _aggregate_status(statuses: tuple[str, ...]) -> str:
    if "block" in statuses:
        return "block"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _report_reason_codes(
    *,
    input_count: Decimal,
    capture_freshness_ratio: Decimal,
    stale_count: Decimal,
    parse_completeness_ratio: Decimal,
    fallback_pressure_ratio: Decimal,
    family_count: Decimal,
    status: str,
    config: ResearchSourceScraplingCaptureHealthConfig,
) -> tuple[str, ...]:
    if input_count == COUNT_ZERO:
        return (NO_INPUTS_REASON, REPORT_BLOCK_REASON)

    reason_codes: list[str] = []
    if stale_count > COUNT_ZERO:
        reason_codes.append("capture_staleness_block")
    elif capture_freshness_ratio < config.min_fresh_capture_block_ratio:
        reason_codes.append("capture_freshness_block")
    elif capture_freshness_ratio < config.min_fresh_capture_pass_ratio:
        reason_codes.append("capture_freshness_watch")

    if parse_completeness_ratio < config.min_parse_completeness_block_ratio:
        reason_codes.append("parse_completeness_block")
    elif parse_completeness_ratio < config.min_parse_completeness_pass_ratio:
        reason_codes.append("parse_completeness_watch")

    if fallback_pressure_ratio > config.max_antibot_fallback_block_ratio:
        reason_codes.append("antibot_fallback_pressure_block")
    elif fallback_pressure_ratio > config.max_antibot_fallback_pass_ratio:
        reason_codes.append("antibot_fallback_pressure_watch")

    if family_count < config.min_source_family_block_count:
        reason_codes.append("source_family_quorum_block")
    elif family_count < config.min_source_family_pass_count:
        reason_codes.append("source_family_quorum_watch")

    if status == "pass":
        reason_codes.append(PASS_REASON)
    elif status == "watch":
        reason_codes.append(REPORT_WATCH_REASON)
    else:
        reason_codes.append(REPORT_BLOCK_REASON)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[ResearchSourceScraplingCaptureHealthReasonCodeCount, ...]:
    counts = Counter(reason_codes)
    return tuple(
        ResearchSourceScraplingCaptureHealthReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(counts[reason_code]),
            paper_only=True,
            report_only=True,
            readonly=True,
        )
        for reason_code in REASON_CODE_ORDER
        if reason_code in counts
    )


def _validate_report_consistency(
    report: ResearchSourceScraplingCaptureHealthReport,
) -> None:
    if report.next_step != NEXT_STEPS[report.status]:
        raise ValueError("next_step must match status")
    if report.fresh_capture_count > report.input_count:
        raise ValueError("fresh_capture_count must not exceed input_count")
    if report.stale_capture_count > report.input_count:
        raise ValueError("stale_capture_count must not exceed input_count")
    if report.captured_field_count > report.expected_field_count:
        raise ValueError("captured field count must not exceed expected field count")
    if report.antibot_fallback_count > report.capture_attempt_count:
        raise ValueError("fallback count must not exceed capture attempt count")
    if report.capture_freshness_ratio != _safe_ratio(
        report.fresh_capture_count,
        report.input_count,
    ):
        raise ValueError("capture_freshness_ratio must match aggregate counts")
    if report.parse_completeness_ratio != _safe_ratio(
        report.captured_field_count,
        report.expected_field_count,
    ):
        raise ValueError("parse_completeness_ratio must match aggregate counts")
    if report.antibot_fallback_pressure_ratio != _safe_ratio(
        report.antibot_fallback_count,
        report.capture_attempt_count,
    ):
        raise ValueError(
            "antibot_fallback_pressure_ratio must match aggregate counts",
        )
    expected_status = _aggregate_status(
        (
            report.capture_freshness_status,
            report.parse_completeness_status,
            report.antibot_fallback_status,
            report.source_family_quorum_status,
        ),
    )
    if report.status != expected_status:
        raise ValueError("status must match component statuses")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes):
        raise ValueError("reason_code_counts must match reason_codes")


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    for reason_code in normalized:
        _require_reason_code("reason_code", reason_code)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    return tuple(reason_code for reason_code in REASON_CODE_ORDER if reason_code in normalized)


def _normalize_reason_code_counts(
    counts: tuple[ResearchSourceScraplingCaptureHealthReasonCodeCount, ...],
) -> tuple[ResearchSourceScraplingCaptureHealthReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(counts)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for count in normalized:
        if type(count) is not ResearchSourceScraplingCaptureHealthReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceScraplingCaptureHealthReasonCodeCount",
            )
    return tuple(
        sorted(
            normalized,
            key=lambda item: REASON_CODE_ORDER.index(item.reason_code),
        ),
    )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} utcoffset must not be None")
    return value.astimezone(UTC)


def _age_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    if delta.days < 0:
        raise ValueError("age seconds must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        seconds = Decimal(delta.days * 86400 + delta.seconds)
        if delta.microseconds:
            seconds += Decimal(delta.microseconds) / MICROSECOND_DIVISOR
        return seconds.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == COUNT_ZERO or denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM, rounding=ROUND_HALF_EVEN)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= COUNT_ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < COUNT_ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized.quantize(COUNT_QUANTUM, rounding=ROUND_HALF_EVEN)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_member(field_name: str, value: object, options: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _reject_unsafe_public_string(field_name, value)
    if value not in options:
        raise ValueError(f"{field_name} must be one of {options!r}")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _reject_unsafe_public_string(field_name, value)
    if value not in REASON_CODE_ORDER:
        raise ValueError(f"{field_name} must be supported")


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _reject_unsafe_public_string(field_name, value)
    if not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a canonical public identifier")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = getattr(value, field_name, None)
        if type(flag) is not bool:
            raise ValueError(f"{label} {field_name} must be a bool")
        if flag is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _report_digest(report: ResearchSourceScraplingCaptureHealthReport) -> str:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    _validate_public_payload(payload)
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _validate_public_payload(value: object, path: str = "payload") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, path)
            _validate_public_payload(item, f"{path}.{key}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_public_payload(item, f"{path}[{index}]")
        return
    if type(value) is str:
        _reject_unsafe_public_string(path, value)
        return
    if value is None or type(value) is bool:
        return
    raise ValueError(f"{path} contains unsupported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public value")


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_SCRAPLING_CAPTURE_HEALTH_REPORT_CONFIG_VERSION",
    "ResearchSourceScraplingCaptureHealthConfig",
    "ResearchSourceScraplingCaptureHealthReasonCodeCount",
    "ResearchSourceScraplingCaptureHealthReport",
    "ResearchSourceScraplingCaptureObservation",
    "build_research_source_scrapling_capture_health_report",
    "research_source_scrapling_capture_health_report_digest",
    "research_source_scrapling_capture_health_report_payload",
)
