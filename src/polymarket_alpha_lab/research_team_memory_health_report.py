"""Pure report-only health summary for research-team long-term memory.

Callers provide local, already-loaded memory observations. This module never
opens external services; it only scores coverage, staleness, conflicts, and
traceability, then renders deterministic public summaries.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


__all__ = (
    "ResearchTeamMemoryHealthConfig",
    "ResearchTeamMemoryHealthReasonCodeCount",
    "ResearchTeamMemoryHealthReport",
    "ResearchTeamMemoryHealthRow",
    "ResearchTeamMemoryObservation",
    "build_research_team_memory_health_report",
    "research_team_memory_health_report_payload",
    "research_team_memory_health_report_text",
)


DEFAULT_CONFIG_VERSION = "research-team-memory-health-report-v0"
STATUSES = ("pass", "watch", "blocked")
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
DEFAULT_FRESH_AGE_SECONDS = Decimal("604800")
DEFAULT_STALE_AGE_SECONDS = Decimal("2592000")
DEFAULT_PASS_HEALTH_SCORE = Decimal("0.750000")
DEFAULT_WATCH_HEALTH_SCORE = Decimal("0.500000")
DEFAULT_PASS_COVERAGE_SCORE = Decimal("0.700000")
DEFAULT_MIN_TRACEABILITY_SCORE = Decimal("0.600000")
DEFAULT_BLOCKING_CONFLICT_COUNT = Decimal("3")
MEMORY_PLAN_FIELDS = (
    "memory_key",
    "team_domain",
    "memory_topic",
    "coverage_score",
    "last_reviewed_at",
    "conflict_count",
    "traceability_score",
    "public_summary",
    "review_status",
    "reviewed_at",
)
UNSAFE_PUBLIC_KEY_FRAGMENTS = ("source", "url", "table", "dsn", "token")
UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "://",
    "http:",
    "https:",
    "postgres:",
    "secret",
    "token",
    "dsn",
    "internal-record",
)


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class ResearchTeamMemoryHealthConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    fresh_age_seconds: Decimal = DEFAULT_FRESH_AGE_SECONDS
    stale_age_seconds: Decimal = DEFAULT_STALE_AGE_SECONDS
    pass_health_score: Decimal = DEFAULT_PASS_HEALTH_SCORE
    watch_health_score: Decimal = DEFAULT_WATCH_HEALTH_SCORE
    pass_coverage_score: Decimal = DEFAULT_PASS_COVERAGE_SCORE
    min_traceability_score: Decimal = DEFAULT_MIN_TRACEABILITY_SCORE
    blocking_conflict_count: Decimal = DEFAULT_BLOCKING_CONFLICT_COUNT
    coverage_weight: Decimal = Decimal("0.300000")
    freshness_weight: Decimal = Decimal("0.250000")
    conflict_weight: Decimal = Decimal("0.200000")
    traceability_weight: Decimal = Decimal("0.250000")
    conflict_penalty: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "fresh_age_seconds",
            _require_positive_decimal("fresh_age_seconds", self.fresh_age_seconds),
        )
        object.__setattr__(
            self,
            "stale_age_seconds",
            _require_positive_decimal("stale_age_seconds", self.stale_age_seconds),
        )
        if self.stale_age_seconds <= self.fresh_age_seconds:
            raise ValueError("stale_age_seconds must be greater than fresh_age_seconds")
        for field_name in (
            "pass_health_score",
            "watch_health_score",
            "pass_coverage_score",
            "min_traceability_score",
            "coverage_weight",
            "freshness_weight",
            "conflict_weight",
            "traceability_weight",
            "conflict_penalty",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_health_score <= self.watch_health_score:
            raise ValueError("pass_health_score must be greater than watch_health_score")
        object.__setattr__(
            self,
            "blocking_conflict_count",
            _require_positive_whole_decimal(
                "blocking_conflict_count",
                self.blocking_conflict_count,
            ),
        )
        weight_sum = _quantize(
            self.coverage_weight
            + self.freshness_weight
            + self.conflict_weight
            + self.traceability_weight,
        )
        if weight_sum != ONE:
            raise ValueError(
                "coverage_weight, freshness_weight, conflict_weight, "
                "and traceability_weight must sum to 1",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamMemoryObservation:
    team_domain: str
    memory_topic: str
    memory_record_key: str
    coverage_score: Decimal
    last_reviewed_at: datetime
    conflict_count: Decimal
    traceability_score: Decimal
    public_summary: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("team_domain", self.team_domain)
        _require_canonical_string("memory_topic", self.memory_topic)
        _require_canonical_string("memory_record_key", self.memory_record_key)
        object.__setattr__(
            self,
            "coverage_score",
            _require_probability_decimal("coverage_score", self.coverage_score),
        )
        object.__setattr__(
            self,
            "last_reviewed_at",
            _as_utc("last_reviewed_at", self.last_reviewed_at),
        )
        object.__setattr__(
            self,
            "conflict_count",
            _require_nonnegative_whole_decimal("conflict_count", self.conflict_count),
        )
        object.__setattr__(
            self,
            "traceability_score",
            _require_probability_decimal("traceability_score", self.traceability_score),
        )
        object.__setattr__(
            self,
            "public_summary",
            _require_public_text("public_summary", self.public_summary),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchTeamMemoryHealthRow:
    team_domain: str
    memory_topic: str
    coverage_score: Decimal
    last_reviewed_at: datetime
    memory_age_seconds: Decimal
    freshness_score: Decimal
    conflict_count: Decimal
    conflict_score: Decimal
    traceability_score: Decimal
    health_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    public_summary: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("team_domain", self.team_domain)
        _require_canonical_string("memory_topic", self.memory_topic)
        for field_name in (
            "coverage_score",
            "freshness_score",
            "conflict_score",
            "traceability_score",
            "health_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "last_reviewed_at",
            _as_utc("last_reviewed_at", self.last_reviewed_at),
        )
        object.__setattr__(
            self,
            "memory_age_seconds",
            _require_nonnegative_decimal("memory_age_seconds", self.memory_age_seconds),
        )
        object.__setattr__(
            self,
            "conflict_count",
            _require_nonnegative_whole_decimal("conflict_count", self.conflict_count),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        object.__setattr__(
            self,
            "public_summary",
            _require_public_text("public_summary", self.public_summary),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchTeamMemoryHealthReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamMemoryHealthReport:
    generated_at: datetime
    config_version: str
    team_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_health_score: Decimal | None
    status: str
    rows: tuple[ResearchTeamMemoryHealthRow, ...]
    reason_code_counts: tuple[ResearchTeamMemoryHealthReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in ("team_count", "pass_count", "watch_count", "blocked_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_health_score",
            _require_optional_probability_decimal(
                "average_health_score",
                self.average_health_score,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_team_memory_health_report_payload(self)


def build_research_team_memory_health_report(
    memory_rows: Iterable[object],
    *,
    config: ResearchTeamMemoryHealthConfig,
    generated_at: datetime,
) -> ResearchTeamMemoryHealthReport:
    if type(config) is not ResearchTeamMemoryHealthConfig:
        raise ValueError("config must be a ResearchTeamMemoryHealthConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    observations = _normalize_observations(memory_rows)
    for observation in observations:
        _reject_future_reviewed_at(observation, generated_at_utc)

    rows = tuple(
        _score_memory_observation(
            observation,
            config=config,
            generated_at=generated_at_utc,
        )
        for observation in sorted(
            observations,
            key=lambda item: (
                item.team_domain,
                item.memory_topic,
                item.memory_record_key,
            ),
        )
    )
    reason_codes = _summary_reason_codes(rows)

    return ResearchTeamMemoryHealthReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        team_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        blocked_count=_decimal_count(_status_count(rows, "blocked")),
        average_health_score=_average_health_score(rows),
        status=_summary_status(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_team_memory_health_report_payload(
    report: ResearchTeamMemoryHealthReport,
) -> dict[str, Any]:
    if type(report) is not ResearchTeamMemoryHealthReport:
        raise ValueError("report must be a ResearchTeamMemoryHealthReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    payload["memory_plan_fields"] = list(MEMORY_PLAN_FIELDS)
    _reject_unsafe_public_payload("research_team_memory_health_report_payload", payload)
    return payload


def research_team_memory_health_report_text(
    report: ResearchTeamMemoryHealthReport,
) -> str:
    if type(report) is not ResearchTeamMemoryHealthReport:
        raise ValueError("report must be a ResearchTeamMemoryHealthReport")
    _require_hard_flags("report", report)
    lines = [
        "Research team memory health report",
        f"generated_at: {report.generated_at.isoformat()}",
        f"status: {report.status}",
        f"teams: {report.team_count}",
        "Local Supabase/Postgres memory planning fields: "
        + ", ".join(MEMORY_PLAN_FIELDS),
        "rows:",
    ]
    if not report.rows:
        lines.append("- none")
    else:
        for row in report.rows:
            reason_codes = ",".join(row.reason_codes)
            lines.append(
                "- "
                f"{row.status} | {row.team_domain} | {row.memory_topic} | "
                f"health={row.health_score} | reasons={reason_codes}",
            )
    return "\n".join(lines)


def _score_memory_observation(
    observation: ResearchTeamMemoryObservation,
    *,
    config: ResearchTeamMemoryHealthConfig,
    generated_at: datetime,
) -> ResearchTeamMemoryHealthRow:
    memory_age_seconds = _age_seconds(generated_at, observation.last_reviewed_at)
    freshness_score = _freshness_score(
        memory_age_seconds,
        fresh_age_seconds=config.fresh_age_seconds,
        stale_age_seconds=config.stale_age_seconds,
    )
    conflict_score = _conflict_score(
        observation.conflict_count,
        conflict_penalty=config.conflict_penalty,
    )
    health_score = _health_score(
        coverage_score=observation.coverage_score,
        freshness_score=freshness_score,
        conflict_score=conflict_score,
        traceability_score=observation.traceability_score,
        config=config,
    )
    status = _row_status(
        coverage_score=observation.coverage_score,
        freshness_score=freshness_score,
        conflict_count=observation.conflict_count,
        traceability_score=observation.traceability_score,
        health_score=health_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        status=status,
        coverage_score=observation.coverage_score,
        freshness_score=freshness_score,
        conflict_count=observation.conflict_count,
        traceability_score=observation.traceability_score,
        config=config,
    )
    return ResearchTeamMemoryHealthRow(
        team_domain=observation.team_domain,
        memory_topic=observation.memory_topic,
        coverage_score=observation.coverage_score,
        last_reviewed_at=observation.last_reviewed_at,
        memory_age_seconds=memory_age_seconds,
        freshness_score=freshness_score,
        conflict_count=observation.conflict_count,
        conflict_score=conflict_score,
        traceability_score=observation.traceability_score,
        health_score=health_score,
        status=status,
        reason_codes=reason_codes,
        public_summary=observation.public_summary,
    )


def _normalize_observations(
    memory_rows: Iterable[object],
) -> tuple[ResearchTeamMemoryObservation, ...]:
    if isinstance(memory_rows, (str, bytes)):
        raise ValueError("memory_rows must be an iterable")
    try:
        values = tuple(memory_rows)
    except TypeError as exc:
        raise ValueError("memory_rows must be an iterable") from exc
    return tuple(_coerce_observation(value) for value in values)


def _coerce_observation(value: object) -> ResearchTeamMemoryObservation:
    if type(value) is ResearchTeamMemoryObservation:
        return value
    return ResearchTeamMemoryObservation(
        team_domain=_field_value(value, "team_domain"),
        memory_topic=_field_value(value, "memory_topic"),
        memory_record_key=_field_value(value, "memory_record_key"),
        coverage_score=_field_value(value, "coverage_score"),
        last_reviewed_at=_field_value(value, "last_reviewed_at"),
        conflict_count=_field_value(value, "conflict_count"),
        traceability_score=_field_value(value, "traceability_score"),
        public_summary=_field_value(value, "public_summary"),
        paper_only=_field_value(value, "paper_only", default=True),
        report_only=_field_value(value, "report_only", default=True),
        readonly=_field_value(value, "readonly", default=True),
    )


def _field_value(value: object, field_name: str, *, default: object = _MISSING) -> object:
    if isinstance(value, dict):
        if field_name in value:
            return value[field_name]
    elif hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{field_name} is required")


def _reject_future_reviewed_at(
    observation: ResearchTeamMemoryObservation,
    generated_at: datetime,
) -> None:
    if observation.last_reviewed_at > generated_at:
        raise ValueError("last_reviewed_at must not be after generated_at")


def _age_seconds(generated_at: datetime, reviewed_at: datetime) -> Decimal:
    delta = generated_at - reviewed_at
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    if delta.microseconds:
        seconds += Decimal(delta.microseconds) / Decimal("1000000")
    return _require_nonnegative_decimal("memory_age_seconds", seconds)


def _freshness_score(
    age_seconds: Decimal,
    *,
    fresh_age_seconds: Decimal,
    stale_age_seconds: Decimal,
) -> Decimal:
    if age_seconds <= fresh_age_seconds:
        return _quantize(ONE)
    if age_seconds >= stale_age_seconds:
        return _quantize(ZERO)
    return _bounded_probability(
        ONE - ((age_seconds - fresh_age_seconds) / (stale_age_seconds - fresh_age_seconds)),
    )


def _conflict_score(conflict_count: Decimal, *, conflict_penalty: Decimal) -> Decimal:
    return _bounded_probability(ONE - (conflict_count * conflict_penalty))


def _health_score(
    *,
    coverage_score: Decimal,
    freshness_score: Decimal,
    conflict_score: Decimal,
    traceability_score: Decimal,
    config: ResearchTeamMemoryHealthConfig,
) -> Decimal:
    return _bounded_probability(
        (coverage_score * config.coverage_weight)
        + (freshness_score * config.freshness_weight)
        + (conflict_score * config.conflict_weight)
        + (traceability_score * config.traceability_weight),
    )


def _row_status(
    *,
    coverage_score: Decimal,
    freshness_score: Decimal,
    conflict_count: Decimal,
    traceability_score: Decimal,
    health_score: Decimal,
    config: ResearchTeamMemoryHealthConfig,
) -> str:
    if (
        conflict_count >= config.blocking_conflict_count
        or freshness_score == ZERO
        or health_score < config.watch_health_score
        or traceability_score < config.min_traceability_score
    ):
        return "blocked"
    if (
        health_score >= config.pass_health_score
        and coverage_score >= config.pass_coverage_score
        and traceability_score >= config.min_traceability_score
        and conflict_count == ZERO
    ):
        return "pass"
    return "watch"


def _row_reason_codes(
    *,
    status: str,
    coverage_score: Decimal,
    freshness_score: Decimal,
    conflict_count: Decimal,
    traceability_score: Decimal,
    config: ResearchTeamMemoryHealthConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = [f"memory_health_{status}"]
    if coverage_score >= config.pass_coverage_score:
        reason_codes.append("strong_coverage")
    else:
        reason_codes.append("coverage_gap")
    if freshness_score == ONE:
        reason_codes.append("fresh_memory")
    elif freshness_score == ZERO:
        reason_codes.append("stale_memory")
    else:
        reason_codes.append("aging_memory")
    if conflict_count == ZERO:
        reason_codes.append("conflict_free")
    elif conflict_count >= config.blocking_conflict_count:
        reason_codes.append("conflict_backlog_blocked")
    else:
        reason_codes.append("conflict_backlog_watch")
    if traceability_score >= config.min_traceability_score:
        reason_codes.append("traceability_ready")
    else:
        reason_codes.append("traceability_gap")
    return tuple(sorted(set(reason_codes)))


def _summary_status(rows: tuple[ResearchTeamMemoryHealthRow, ...]) -> str:
    if not rows:
        return "blocked"
    statuses = {row.status for row in rows}
    if "blocked" in statuses:
        return "blocked"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _summary_reason_codes(rows: tuple[ResearchTeamMemoryHealthRow, ...]) -> tuple[str, ...]:
    if not rows:
        return ("no_memory_rows",)
    return tuple(sorted({reason_code for row in rows for reason_code in row.reason_codes}))


def _reason_code_counts(
    rows: tuple[ResearchTeamMemoryHealthRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchTeamMemoryHealthReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchTeamMemoryHealthReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts = Counter(reason_code for row in rows for reason_code in row.reason_codes)
    return tuple(
        ResearchTeamMemoryHealthReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
        )
        for reason_code in reason_codes
    )


def _status_count(rows: tuple[ResearchTeamMemoryHealthRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _average_health_score(
    rows: tuple[ResearchTeamMemoryHealthRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _bounded_probability(
        sum((row.health_score for row in rows), ZERO) / Decimal(len(rows)),
    )


def _validate_row_consistency(row: ResearchTeamMemoryHealthRow) -> None:
    status_code = f"memory_health_{row.status}"
    if status_code not in row.reason_codes:
        raise ValueError("reason_codes must include status reason")
    if row.status == "pass" and row.health_score < DEFAULT_WATCH_HEALTH_SCORE:
        raise ValueError("health_score must support pass status")
    if row.status == "blocked" and row.health_score >= DEFAULT_PASS_HEALTH_SCORE:
        raise ValueError("health_score must support blocked status")


def _validate_report_consistency(report: ResearchTeamMemoryHealthReport) -> None:
    if report.team_count != _decimal_count(len(report.rows)):
        raise ValueError("team_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _decimal_count(_status_count(report.rows, "blocked")):
        raise ValueError("blocked_count must match rows")
    if report.average_health_score != _average_health_score(report.rows):
        raise ValueError("average_health_score must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(report.rows):
        raise ValueError("status must match rows")
    expected_counts = _reason_code_counts(report.rows, report.reason_codes)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")


def _normalize_rows(values: object) -> tuple[ResearchTeamMemoryHealthRow, ...]:
    if type(values) is not tuple:
        raise ValueError("rows must be a tuple")
    for value in values:
        if type(value) is not ResearchTeamMemoryHealthRow:
            raise ValueError("rows must contain ResearchTeamMemoryHealthRow values")
    return values


def _normalize_reason_code_counts(
    values: object,
) -> tuple[ResearchTeamMemoryHealthReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for value in values:
        if type(value) is not ResearchTeamMemoryHealthReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTeamMemoryHealthReasonCodeCount values",
            )
    ordered = tuple(sorted(values, key=lambda item: item.reason_code))
    if tuple(item.reason_code for item in ordered) != tuple(
        sorted({item.reason_code for item in ordered}),
    ):
        raise ValueError("reason_code_counts must be unique by reason_code")
    return ordered


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_reason_code(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _payload_value(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {key: _payload_value(item) for key, item in asdict(value).items()}
    if type(value) is datetime:
        return value.isoformat()
    if type(value) is Decimal:
        return str(value)
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    return value


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if type(value) is str:
        lowered = value.lower()
        if any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
            raise ValueError(f"{path or label} has unsafe value")
        return
    if value is None or type(value) is bool:
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if type(value) is datetime:
        _as_utc(path or label, value)
        return
    if type(value) is float:
        raise ValueError(f"{path or label} must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            lowered_key = key.lower()
            if (
                lowered_key == "id"
                or lowered_key.endswith("_id")
                or any(fragment in lowered_key for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS)
            ):
                raise ValueError(f"unsafe public payload field in {label}: {key}")
            item_path = key if not path else f"{path}.{key}"
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError(f"{path or label} is not JSON serializable")


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
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_optional_probability_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(field_name, value)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _bounded_probability(value: Decimal) -> Decimal:
    if value < ZERO:
        return _quantize(ZERO)
    if value > ONE:
        return _quantize(ONE)
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")


def _require_public_text(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if any(fragment in value.lower() for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe value")
    return value


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must contain lowercase reason codes")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag_value = getattr(value, field_name, _MISSING)
        if flag_value is not True:
            raise ValueError(f"{label}.{field_name} must be True")
