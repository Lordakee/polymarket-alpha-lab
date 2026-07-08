"""Pure report-only precious-metals event specialist memory readiness report."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any


DEFAULT_RESEARCH_PRECIOUS_METALS_EVENT_TEAM_MEMORY_CONFIG_VERSION = (
    "research-precious-metals-event-team-memory-report-v0"
)

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"
STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCK_STATUS)

NO_OBSERVATIONS_REASON = "precious_metals_memory_no_observations"
PASS_REASON = "precious_metals_memory_pass"
WATCH_REASON = "precious_metals_memory_watch"
BLOCK_REASON = "precious_metals_memory_block"
MEMORY_SCORE_BELOW_WATCH_REASON = "memory_score_below_watch"
MEMORY_SCORE_BELOW_PASS_REASON = "memory_score_below_pass"
SOURCE_FRESHNESS_BELOW_WATCH_REASON = "source_freshness_below_watch"
SOURCE_FRESHNESS_BELOW_PASS_REASON = "source_freshness_below_pass"
SOURCE_AGE_ABOVE_WATCH_REASON = "source_age_above_watch"
SOURCE_AGE_ABOVE_PASS_REASON = "source_age_above_pass"
SOURCE_OBSERVATION_MISSING_REASON = "source_observation_missing"
GOLD_SPECIFICITY_BELOW_WATCH_REASON = "gold_specificity_below_watch"
GOLD_SPECIFICITY_BELOW_PASS_REASON = "gold_specificity_below_pass"

REASON_CODE_PRIORITY = (
    NO_OBSERVATIONS_REASON,
    BLOCK_REASON,
    WATCH_REASON,
    PASS_REASON,
    MEMORY_SCORE_BELOW_WATCH_REASON,
    SOURCE_FRESHNESS_BELOW_WATCH_REASON,
    SOURCE_AGE_ABOVE_WATCH_REASON,
    SOURCE_OBSERVATION_MISSING_REASON,
    GOLD_SPECIFICITY_BELOW_WATCH_REASON,
    MEMORY_SCORE_BELOW_PASS_REASON,
    SOURCE_FRESHNESS_BELOW_PASS_REASON,
    SOURCE_AGE_ABOVE_PASS_REASON,
    GOLD_SPECIFICITY_BELOW_PASS_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
RATIO_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO_COUNT = Decimal("0")
ONE_COUNT = Decimal("1")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
SHA256_HEX_LENGTH = 64

PUBLIC_IDENTIFIER_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789-_")
PUBLIC_REASON_CODE_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_")
UNSAFE_PUBLIC_FRAGMENTS = (
    "event_id",
    "event_slug",
    "market_id",
    "market_slug",
    "raw_event",
    "raw_market",
    "raw_source",
    "source_id",
    "source_url",
    "source_ref",
    "question",
    "slug",
    "url",
    "http://",
    "https://",
    "://",
    "wallet",
    "auth",
    "order",
    "trade",
    "live_execution",
    "execute",
    "private",
    "secret",
    "recommend",
    "sizing",
    "allocation",
)

__all__ = (
    "DEFAULT_RESEARCH_PRECIOUS_METALS_EVENT_TEAM_MEMORY_CONFIG_VERSION",
    "STATUSES",
    "ResearchPreciousMetalsEventTeamMemoryConfig",
    "ResearchPreciousMetalsEventTeamMemoryObservation",
    "ResearchPreciousMetalsEventTeamMemoryReasonCodeCount",
    "ResearchPreciousMetalsEventTeamMemoryReport",
    "ResearchPreciousMetalsEventTeamMemoryRow",
    "build_research_precious_metals_event_team_memory_report",
    "research_precious_metals_event_team_memory_report_digest",
    "research_precious_metals_event_team_memory_report_payload",
)


@dataclass(frozen=True)
class ResearchPreciousMetalsEventTeamMemoryConfig:
    config_version: str = DEFAULT_RESEARCH_PRECIOUS_METALS_EVENT_TEAM_MEMORY_CONFIG_VERSION
    min_pass_memory_score: Decimal = Decimal("0.750000")
    min_watch_memory_score: Decimal = Decimal("0.500000")
    min_pass_source_freshness_ratio: Decimal = Decimal("0.750000")
    min_watch_source_freshness_ratio: Decimal = Decimal("0.500000")
    max_pass_source_age_seconds: Decimal = Decimal("43200")
    max_watch_source_age_seconds: Decimal = Decimal("172800")
    min_pass_gold_specificity_ratio: Decimal = Decimal("0.700000")
    min_watch_gold_specificity_ratio: Decimal = Decimal("0.450000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPreciousMetalsEventTeamMemoryConfig:
            raise TypeError("ResearchPreciousMetalsEventTeamMemoryConfig is final")

    def __post_init__(self) -> None:
        if type(self) is not ResearchPreciousMetalsEventTeamMemoryConfig:
            raise ValueError(
                "config must be exactly ResearchPreciousMetalsEventTeamMemoryConfig",
            )
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        for field_name in (
            "min_pass_memory_score",
            "min_watch_memory_score",
            "min_pass_source_freshness_ratio",
            "min_watch_source_freshness_ratio",
            "min_pass_gold_specificity_ratio",
            "min_watch_gold_specificity_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_source_age_seconds",
            "max_watch_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchPreciousMetalsEventTeamMemoryObservation:
    event_family: str
    specialist_key: str
    memory_score: Decimal
    source_count: Decimal
    fresh_source_count: Decimal
    stale_source_count: Decimal
    latest_source_observed_at: datetime | None
    gold_specificity_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPreciousMetalsEventTeamMemoryObservation:
            raise TypeError("ResearchPreciousMetalsEventTeamMemoryObservation is final")

    def __post_init__(self) -> None:
        if type(self) is not ResearchPreciousMetalsEventTeamMemoryObservation:
            raise ValueError(
                "observation must be exactly "
                "ResearchPreciousMetalsEventTeamMemoryObservation",
            )
        object.__setattr__(
            self,
            "event_family",
            _require_public_identifier("event_family", self.event_family),
        )
        object.__setattr__(
            self,
            "specialist_key",
            _require_public_identifier("specialist_key", self.specialist_key),
        )
        object.__setattr__(
            self,
            "memory_score",
            _require_ratio_decimal("memory_score", self.memory_score),
        )
        for field_name in (
            "source_count",
            "fresh_source_count",
            "stale_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_source_observed_at",
            _as_optional_utc(
                "latest_source_observed_at",
                self.latest_source_observed_at,
            ),
        )
        object.__setattr__(
            self,
            "gold_specificity_ratio",
            _require_ratio_decimal(
                "gold_specificity_ratio",
                self.gold_specificity_ratio,
            ),
        )
        _validate_observation(self)
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchPreciousMetalsEventTeamMemoryRow:
    event_family: str
    specialist_key: str
    memory_score: Decimal
    source_count: Decimal
    fresh_source_count: Decimal
    stale_source_count: Decimal
    source_freshness_ratio: Decimal
    source_age_seconds: Decimal
    gold_specificity_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPreciousMetalsEventTeamMemoryRow:
            raise TypeError("ResearchPreciousMetalsEventTeamMemoryRow is final")

    def __post_init__(self) -> None:
        if type(self) is not ResearchPreciousMetalsEventTeamMemoryRow:
            raise ValueError("row must be exactly ResearchPreciousMetalsEventTeamMemoryRow")
        object.__setattr__(
            self,
            "event_family",
            _require_public_identifier("event_family", self.event_family),
        )
        object.__setattr__(
            self,
            "specialist_key",
            _require_public_identifier("specialist_key", self.specialist_key),
        )
        object.__setattr__(
            self,
            "memory_score",
            _require_ratio_decimal("memory_score", self.memory_score),
        )
        for field_name in (
            "source_count",
            "fresh_source_count",
            "stale_source_count",
            "source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("source_freshness_ratio", "gold_specificity_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchPreciousMetalsEventTeamMemoryReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPreciousMetalsEventTeamMemoryReasonCodeCount:
            raise TypeError(
                "ResearchPreciousMetalsEventTeamMemoryReasonCodeCount is final",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPreciousMetalsEventTeamMemoryReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchPreciousMetalsEventTeamMemoryReasonCodeCount",
            )
        object.__setattr__(
            self,
            "reason_code",
            _require_reason_code("reason_code", self.reason_code),
        )
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason code count", self)
        _reject_unsafe_public_payload("reason code count", self)


@dataclass(frozen=True)
class ResearchPreciousMetalsEventTeamMemoryReport:
    generated_at: datetime
    config_version: str
    event_specialist_count: Decimal
    source_count: Decimal
    fresh_source_count: Decimal
    stale_source_count: Decimal
    average_memory_score: Decimal
    overall_source_freshness_ratio: Decimal
    average_gold_specificity_ratio: Decimal
    max_source_age_seconds: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchPreciousMetalsEventTeamMemoryReasonCodeCount, ...]
    rows: tuple[ResearchPreciousMetalsEventTeamMemoryRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPreciousMetalsEventTeamMemoryReport:
            raise TypeError("ResearchPreciousMetalsEventTeamMemoryReport is final")

    def __post_init__(self) -> None:
        if type(self) is not ResearchPreciousMetalsEventTeamMemoryReport:
            raise ValueError(
                "report must be exactly ResearchPreciousMetalsEventTeamMemoryReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        for field_name in (
            "event_specialist_count",
            "source_count",
            "fresh_source_count",
            "stale_source_count",
            "max_source_age_seconds",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_memory_score",
            "overall_source_freshness_ratio",
            "average_gold_specificity_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload("report payload", payload)
        if type(payload) is not dict:
            raise ValueError("report payload must be a dict")
        return payload


def build_research_precious_metals_event_team_memory_report(
    observations: list[ResearchPreciousMetalsEventTeamMemoryObservation]
    | tuple[ResearchPreciousMetalsEventTeamMemoryObservation, ...],
    *,
    config: ResearchPreciousMetalsEventTeamMemoryConfig,
    generated_at: datetime,
) -> ResearchPreciousMetalsEventTeamMemoryReport:
    if type(config) is not ResearchPreciousMetalsEventTeamMemoryConfig:
        raise ValueError(
            "config must be exactly ResearchPreciousMetalsEventTeamMemoryConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_observations = _normalize_observations(
        observations,
        generated_at=generated_at_utc,
    )
    rows = _build_rows(input_observations, config, generated_at_utc)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "event_specialist_count": _count(len(rows)),
        "source_count": _sum_rows(rows, "source_count"),
        "fresh_source_count": _sum_rows(rows, "fresh_source_count"),
        "stale_source_count": _sum_rows(rows, "stale_source_count"),
        "average_memory_score": _average_row_ratio(rows, "memory_score"),
        "overall_source_freshness_ratio": _ratio(
            _sum_rows(rows, "fresh_source_count"),
            _sum_rows(rows, "source_count"),
        ),
        "average_gold_specificity_ratio": _average_row_ratio(
            rows,
            "gold_specificity_ratio",
        ),
        "max_source_age_seconds": _max_row_decimal(rows, "source_age_seconds"),
        "pass_count": _status_count(rows, PASS_STATUS),
        "watch_count": _status_count(rows, WATCH_STATUS),
        "block_count": _status_count(rows, BLOCK_STATUS),
        "status": _report_status(rows),
        "reason_codes": _report_reason_codes(rows),
        "reason_code_counts": _reason_code_counts(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchPreciousMetalsEventTeamMemoryReport(
        **values,
        derived_validation_digest=_digest_from_values(values),
    )


def research_precious_metals_event_team_memory_report_payload(
    report: ResearchPreciousMetalsEventTeamMemoryReport,
) -> dict[str, object]:
    if type(report) is not ResearchPreciousMetalsEventTeamMemoryReport:
        raise ValueError(
            "report must be exactly ResearchPreciousMetalsEventTeamMemoryReport",
        )
    _require_hard_flags("report", report)
    return report.payload


def research_precious_metals_event_team_memory_report_digest(
    report: ResearchPreciousMetalsEventTeamMemoryReport,
) -> str:
    if type(report) is not ResearchPreciousMetalsEventTeamMemoryReport:
        raise ValueError(
            "report must be exactly ResearchPreciousMetalsEventTeamMemoryReport",
        )
    return _digest_from_values(_report_values_without_digest(report))


def _build_rows(
    observations: tuple[ResearchPreciousMetalsEventTeamMemoryObservation, ...],
    config: ResearchPreciousMetalsEventTeamMemoryConfig,
    generated_at: datetime,
) -> tuple[ResearchPreciousMetalsEventTeamMemoryRow, ...]:
    rows = tuple(
        _row_for_observation(observation, config, generated_at)
        for observation in observations
    )
    return tuple(sorted(rows, key=_row_sort_key))


def _row_for_observation(
    observation: ResearchPreciousMetalsEventTeamMemoryObservation,
    config: ResearchPreciousMetalsEventTeamMemoryConfig,
    generated_at: datetime,
) -> ResearchPreciousMetalsEventTeamMemoryRow:
    source_freshness_ratio = _ratio(
        observation.fresh_source_count,
        observation.source_count,
    )
    source_age_seconds = (
        ZERO_COUNT
        if observation.latest_source_observed_at is None
        else _age_seconds(generated_at, observation.latest_source_observed_at)
    )
    status = _row_status(
        observation=observation,
        source_freshness_ratio=source_freshness_ratio,
        source_age_seconds=source_age_seconds,
        config=config,
    )
    return ResearchPreciousMetalsEventTeamMemoryRow(
        event_family=observation.event_family,
        specialist_key=observation.specialist_key,
        memory_score=observation.memory_score,
        source_count=observation.source_count,
        fresh_source_count=observation.fresh_source_count,
        stale_source_count=observation.stale_source_count,
        source_freshness_ratio=source_freshness_ratio,
        source_age_seconds=source_age_seconds,
        gold_specificity_ratio=observation.gold_specificity_ratio,
        status=status,
        reason_codes=_row_reason_codes(
            observation=observation,
            source_freshness_ratio=source_freshness_ratio,
            source_age_seconds=source_age_seconds,
            status=status,
            config=config,
        ),
    )


def _row_status(
    *,
    observation: ResearchPreciousMetalsEventTeamMemoryObservation,
    source_freshness_ratio: Decimal,
    source_age_seconds: Decimal,
    config: ResearchPreciousMetalsEventTeamMemoryConfig,
) -> str:
    if (
        observation.latest_source_observed_at is None
        or observation.memory_score < config.min_watch_memory_score
        or source_freshness_ratio < config.min_watch_source_freshness_ratio
        or source_age_seconds > config.max_watch_source_age_seconds
        or observation.gold_specificity_ratio < config.min_watch_gold_specificity_ratio
    ):
        return BLOCK_STATUS
    if (
        observation.memory_score < config.min_pass_memory_score
        or source_freshness_ratio < config.min_pass_source_freshness_ratio
        or source_age_seconds > config.max_pass_source_age_seconds
        or observation.gold_specificity_ratio < config.min_pass_gold_specificity_ratio
    ):
        return WATCH_STATUS
    return PASS_STATUS


def _row_reason_codes(
    *,
    observation: ResearchPreciousMetalsEventTeamMemoryObservation,
    source_freshness_ratio: Decimal,
    source_age_seconds: Decimal,
    status: str,
    config: ResearchPreciousMetalsEventTeamMemoryConfig,
) -> tuple[str, ...]:
    if status == PASS_STATUS:
        return (PASS_REASON,)
    if status == BLOCK_STATUS:
        reasons = [BLOCK_REASON]
        if observation.memory_score < config.min_watch_memory_score:
            reasons.append(MEMORY_SCORE_BELOW_WATCH_REASON)
        if source_freshness_ratio < config.min_watch_source_freshness_ratio:
            reasons.append(SOURCE_FRESHNESS_BELOW_WATCH_REASON)
        if source_age_seconds > config.max_watch_source_age_seconds:
            reasons.append(SOURCE_AGE_ABOVE_WATCH_REASON)
        if observation.latest_source_observed_at is None:
            reasons.append(SOURCE_OBSERVATION_MISSING_REASON)
        if observation.gold_specificity_ratio < config.min_watch_gold_specificity_ratio:
            reasons.append(GOLD_SPECIFICITY_BELOW_WATCH_REASON)
        return _normalize_reason_codes(tuple(reasons), require_nonempty=True)

    reasons = [WATCH_REASON]
    if observation.memory_score < config.min_pass_memory_score:
        reasons.append(MEMORY_SCORE_BELOW_PASS_REASON)
    if source_freshness_ratio < config.min_pass_source_freshness_ratio:
        reasons.append(SOURCE_FRESHNESS_BELOW_PASS_REASON)
    if source_age_seconds > config.max_pass_source_age_seconds:
        reasons.append(SOURCE_AGE_ABOVE_PASS_REASON)
    if observation.gold_specificity_ratio < config.min_pass_gold_specificity_ratio:
        reasons.append(GOLD_SPECIFICITY_BELOW_PASS_REASON)
    return _normalize_reason_codes(tuple(reasons), require_nonempty=True)


def _report_status(rows: tuple[ResearchPreciousMetalsEventTeamMemoryRow, ...]) -> str:
    if not rows:
        return BLOCK_STATUS
    if any(row.status == BLOCK_STATUS for row in rows):
        return BLOCK_STATUS
    if any(row.status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    rows: tuple[ResearchPreciousMetalsEventTeamMemoryRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_OBSERVATIONS_REASON,)
    return _normalize_reason_codes(
        tuple(reason for row in rows for reason in row.reason_codes),
        require_nonempty=True,
        deduplicate=True,
    )


def _reason_code_counts(
    rows: tuple[ResearchPreciousMetalsEventTeamMemoryRow, ...],
) -> tuple[ResearchPreciousMetalsEventTeamMemoryReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchPreciousMetalsEventTeamMemoryReasonCodeCount(
                reason_code=NO_OBSERVATIONS_REASON,
                count=ONE_COUNT,
            ),
        )
    counts = Counter(reason for row in rows for reason in row.reason_codes)
    return tuple(
        ResearchPreciousMetalsEventTeamMemoryReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: REASON_CODE_PRIORITY.index(item[0]),
        )
    )


def _normalize_observations(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[ResearchPreciousMetalsEventTeamMemoryObservation, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    observations = tuple(value)
    seen: set[tuple[str, str]] = set()
    for observation in observations:
        if type(observation) is not ResearchPreciousMetalsEventTeamMemoryObservation:
            raise ValueError(
                "observations must contain "
                "ResearchPreciousMetalsEventTeamMemoryObservation",
            )
        _require_hard_flags("observation", observation)
        if (
            observation.latest_source_observed_at is not None
            and observation.latest_source_observed_at > generated_at
        ):
            raise ValueError("latest_source_observed_at must not be in the future")
        key = (observation.event_family, observation.specialist_key)
        if key in seen:
            raise ValueError("event_family and specialist_key pairs must be unique")
        seen.add(key)
    return tuple(
        sorted(
            observations,
            key=lambda observation: (
                observation.event_family,
                observation.specialist_key,
            ),
        ),
    )


def _validate_config(config: ResearchPreciousMetalsEventTeamMemoryConfig) -> None:
    if config.min_pass_memory_score < config.min_watch_memory_score:
        raise ValueError(
            "min_pass_memory_score must be >= min_watch_memory_score",
        )
    if config.min_pass_source_freshness_ratio < config.min_watch_source_freshness_ratio:
        raise ValueError(
            "min_pass_source_freshness_ratio must be >= "
            "min_watch_source_freshness_ratio",
        )
    if config.max_pass_source_age_seconds > config.max_watch_source_age_seconds:
        raise ValueError(
            "max_pass_source_age_seconds must be <= max_watch_source_age_seconds",
        )
    if config.min_pass_gold_specificity_ratio < config.min_watch_gold_specificity_ratio:
        raise ValueError(
            "min_pass_gold_specificity_ratio must be >= "
            "min_watch_gold_specificity_ratio",
        )


def _validate_observation(
    observation: ResearchPreciousMetalsEventTeamMemoryObservation,
) -> None:
    if (
        observation.fresh_source_count + observation.stale_source_count
        != observation.source_count
    ):
        raise ValueError(
            "fresh and stale source counts must equal source_count",
        )


def _validate_row(row: ResearchPreciousMetalsEventTeamMemoryRow) -> None:
    if row.fresh_source_count + row.stale_source_count != row.source_count:
        raise ValueError(
            "fresh and stale source counts must equal source_count",
        )
    if row.source_freshness_ratio != _ratio(row.fresh_source_count, row.source_count):
        raise ValueError("source_freshness_ratio must match source counts")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchPreciousMetalsEventTeamMemoryReport) -> None:
    rows = report.rows
    if report.event_specialist_count != _count(len(rows)):
        raise ValueError("event_specialist_count must match rows")
    if report.source_count != _sum_rows(rows, "source_count"):
        raise ValueError("source_count must match rows")
    if report.fresh_source_count != _sum_rows(rows, "fresh_source_count"):
        raise ValueError("fresh_source_count must match rows")
    if report.stale_source_count != _sum_rows(rows, "stale_source_count"):
        raise ValueError("stale_source_count must match rows")
    if report.average_memory_score != _average_row_ratio(rows, "memory_score"):
        raise ValueError("average_memory_score must match rows")
    if report.overall_source_freshness_ratio != _ratio(
        _sum_rows(rows, "fresh_source_count"),
        _sum_rows(rows, "source_count"),
    ):
        raise ValueError("overall_source_freshness_ratio must match rows")
    if report.average_gold_specificity_ratio != _average_row_ratio(
        rows,
        "gold_specificity_ratio",
    ):
        raise ValueError("average_gold_specificity_ratio must match rows")
    if report.max_source_age_seconds != _max_row_decimal(rows, "source_age_seconds"):
        raise ValueError("max_source_age_seconds must match rows")
    if report.pass_count != _status_count(rows, PASS_STATUS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, WATCH_STATUS):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, BLOCK_STATUS):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if BLOCK_REASON in reason_codes or NO_OBSERVATIONS_REASON in reason_codes:
        return BLOCK_STATUS
    if WATCH_REASON in reason_codes:
        return WATCH_STATUS
    if reason_codes == (PASS_REASON,):
        return PASS_STATUS
    raise ValueError("reason_codes must include a status reason")


def _row_sort_key(row: ResearchPreciousMetalsEventTeamMemoryRow) -> tuple[int, str, str]:
    return (
        {BLOCK_STATUS: 0, WATCH_STATUS: 1, PASS_STATUS: 2}[row.status],
        row.event_family,
        row.specialist_key,
    )


def _status_count(
    rows: tuple[ResearchPreciousMetalsEventTeamMemoryRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(ONE_COUNT for row in rows if row.status == status))


def _sum_rows(
    rows: tuple[ResearchPreciousMetalsEventTeamMemoryRow, ...],
    field_name: str,
) -> Decimal:
    return _sum_decimal(tuple(getattr(row, field_name) for row in rows))


def _sum_row_ratios(
    rows: tuple[ResearchPreciousMetalsEventTeamMemoryRow, ...],
    field_name: str,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_ratio(
            sum((getattr(row, field_name) for row in rows), ZERO_RATIO),
        )


def _average_row_ratio(
    rows: tuple[ResearchPreciousMetalsEventTeamMemoryRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO_RATIO
    return _ratio(_sum_row_ratios(rows, field_name), _count(len(rows)))


def _max_row_decimal(
    rows: tuple[ResearchPreciousMetalsEventTeamMemoryRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO_COUNT
    return max(getattr(row, field_name) for row in rows)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    numerator = _require_nonnegative_decimal("ratio numerator", numerator)
    denominator = _require_nonnegative_decimal("ratio denominator", denominator)
    if denominator == ZERO_COUNT:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_ratio(numerator / denominator)


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_count(sum(values, ZERO_COUNT))


def _count(value: int) -> Decimal:
    return _quantize_count(Decimal(value))


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    with localcontext(DECIMAL_CONTEXT):
        value = Decimal(delta.days) * SECONDS_PER_DAY + Decimal(delta.seconds)
    if value < ZERO_COUNT:
        raise ValueError("latest_source_observed_at must not be in the future")
    return _quantize_count(value)


def _normalize_reason_code_counts(
    value: tuple[ResearchPreciousMetalsEventTeamMemoryReasonCodeCount, ...],
) -> tuple[ResearchPreciousMetalsEventTeamMemoryReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for item in value:
        if type(item) is not ResearchPreciousMetalsEventTeamMemoryReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchPreciousMetalsEventTeamMemoryReasonCodeCount",
            )
    if len({item.reason_code for item in value}) != len(value):
        raise ValueError("reason_code_counts must not contain duplicates")
    return tuple(
        sorted(
            value,
            key=lambda item: REASON_CODE_PRIORITY.index(item.reason_code),
        ),
    )


def _normalize_rows(
    value: tuple[ResearchPreciousMetalsEventTeamMemoryRow, ...],
) -> tuple[ResearchPreciousMetalsEventTeamMemoryRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not ResearchPreciousMetalsEventTeamMemoryRow:
            raise ValueError("rows must contain ResearchPreciousMetalsEventTeamMemoryRow")
    return tuple(sorted(value, key=_row_sort_key))


def _normalize_reason_codes(
    value: tuple[str, ...],
    *,
    require_nonempty: bool,
    deduplicate: bool = False,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if require_nonempty and not value:
        raise ValueError("reason_codes must not be empty")
    if not deduplicate and len(frozenset(value)) != len(value):
        raise ValueError("reason_codes must not contain duplicates")
    for reason_code in value:
        _require_reason_code("reason_code", reason_code)
    unique_values = frozenset(value) if deduplicate else value
    return tuple(
        reason_code
        for reason_code in REASON_CODE_PRIORITY
        if reason_code in unique_values
    )


def _require_status(field_name: str, value: str) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_reason_code(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be exactly str")
    if not value or value != value.strip():
        raise ValueError(f"{field_name} must be canonical")
    if any(char not in PUBLIC_REASON_CODE_CHARS for char in value):
        raise ValueError(f"{field_name} must be public-safe")
    if value not in REASON_CODE_PRIORITY:
        raise ValueError(f"{field_name} must be a known reason code")
    return value


def _require_public_identifier(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be exactly str")
    if not value or value != value.strip():
        raise ValueError(f"{field_name} must be canonical")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} must be public-safe")
    if any(char not in PUBLIC_IDENTIFIER_CHARS for char in value):
        raise ValueError(f"{field_name} must be public-safe")
    if lowered != value:
        raise ValueError(f"{field_name} must be canonical")
    return value


def _as_optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    if value.microsecond != 0:
        raise ValueError(f"{field_name} must be whole-second precision")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_nonnegative_whole_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return _quantize_count(decimal_value)


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_RATIO or decimal_value > ONE_RATIO:
        raise ValueError(f"{field_name} must be in the unit interval")
    return _quantize_ratio(decimal_value)


def _quantize_count(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(COUNT_QUANTUM)


def _quantize_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _require_hard_flags(label: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name) is not True:
            raise ValueError(f"{label} must keep {flag_name}=True")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} payload keys must be strings")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, str):
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{label} contains non public-safe text")


def _require_sha256_digest(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be exactly str")
    if len(value) != SHA256_HEX_LENGTH:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _report_values_without_digest(
    report: ResearchPreciousMetalsEventTeamMemoryReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest")
    return values


def _digest_from_values(values: dict[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload("digest payload", payload)
    encoded = dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: object) -> object:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) in (str, bool):
        return value
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")
