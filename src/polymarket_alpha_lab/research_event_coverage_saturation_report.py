"""Pure report-only coverage saturation report for aggregate research events."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any


__all__ = (
    "ResearchEventCoverageSaturationConfig",
    "ResearchEventCoverageSaturationReport",
    "ResearchEventCoverageSaturationRow",
    "ResearchEventCoverageSaturationSubject",
    "build_research_event_coverage_saturation_report",
    "research_event_coverage_saturation_report_payload",
)


CONFIG_VERSION = "research-event-coverage-saturation-report-v0"
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
COUNT_QUANTUM = Decimal("1")
SCORE_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_SCORE = Decimal("0.000000")
ONE_SCORE = Decimal("1.000000")

PASS = "pass"
WATCH = "watch"
BLOCK = "block"
STATUSES = (PASS, WATCH, BLOCK)
STATUS_SORT = {
    BLOCK: Decimal("0"),
    WATCH: Decimal("1"),
    PASS: Decimal("2"),
}

ROW_REASON_CODES = (
    "coverage_saturation_clear",
    "low_source_class_diversity_watch",
    "low_source_class_diversity_block",
    "aging_evidence_watch",
    "stale_evidence_age_block",
    "thin_catalyst_cadence_watch",
    "thin_catalyst_cadence_block",
    "constrained_team_capacity_watch",
    "constrained_team_capacity_block",
    "elevated_ambiguity_pressure_watch",
    "high_ambiguity_pressure_block",
)
REPORT_NUMERIC_FIELDS = (
    "coverage_bucket_count",
    "pass_count",
    "watch_count",
    "block_count",
    "average_coverage_saturation_score",
    "min_coverage_saturation_score",
    "min_source_class_diversity_score",
    "max_freshest_evidence_age_seconds",
    "min_catalyst_cadence_per_day",
    "min_team_capacity_score",
    "max_ambiguity_pressure_score",
)
ROW_NUMERIC_FIELDS = (
    "source_class_diversity_score",
    "freshest_evidence_age_seconds",
    "catalyst_cadence_per_day",
    "team_capacity_score",
    "ambiguity_pressure_score",
    "coverage_saturation_score",
)
PUBLIC_PAYLOAD_KEYS = (
    "generated_at",
    "config_version",
    *REPORT_NUMERIC_FIELDS,
    "status",
    "reason_code_counts",
    "rows",
    "derived_payload_digest",
    "paper_only",
    "report_only",
    "readonly",
)
PUBLIC_ROW_KEYS = (
    "coverage_bucket",
    *ROW_NUMERIC_FIELDS,
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
UNSAFE_BUCKET_FRAGMENTS = (
    "raw",
    "event-id",
    "market-id",
    "source-id",
    "condition-id",
    "event_id",
    "market_id",
    "source_id",
    "condition_id",
    "-id",
    "_id",
    "slug",
)
UNSAFE_PAYLOAD_FRAGMENTS = (
    "event_id",
    "market_id",
    "source_id",
    "condition_id",
    "slug",
    "wallet",
    "auth",
    "order",
    "trade",
    "live",
    "recommend",
    "buy",
    "sell",
    "position",
    "database",
    "network",
    "private_key",
    "token",
)


@dataclass(frozen=True)
class ResearchEventCoverageSaturationConfig:
    config_version: str = CONFIG_VERSION
    source_class_diversity_watch_floor: Decimal = Decimal("0.650000")
    source_class_diversity_block_floor: Decimal = Decimal("0.350000")
    fresh_evidence_max_age_seconds: Decimal = Decimal("3600")
    stale_evidence_block_age_seconds: Decimal = Decimal("21600")
    catalyst_cadence_watch_floor_per_day: Decimal = Decimal("1.000000")
    catalyst_cadence_block_floor_per_day: Decimal = Decimal("0.250000")
    team_capacity_watch_floor: Decimal = Decimal("0.550000")
    team_capacity_block_floor: Decimal = Decimal("0.250000")
    ambiguity_pressure_watch_threshold: Decimal = Decimal("0.400000")
    ambiguity_pressure_block_threshold: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventCoverageSaturationConfig:
            raise TypeError(
                "ResearchEventCoverageSaturationConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventCoverageSaturationConfig:
            raise ValueError(
                "config must be exactly ResearchEventCoverageSaturationConfig",
            )
        _require_string("config_version", self.config_version)
        if self.config_version != CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "source_class_diversity_watch_floor",
            "source_class_diversity_block_floor",
            "team_capacity_watch_floor",
            "team_capacity_block_floor",
            "ambiguity_pressure_watch_threshold",
            "ambiguity_pressure_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_score(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "fresh_evidence_max_age_seconds",
            "stale_evidence_block_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "catalyst_cadence_watch_floor_per_day",
            "catalyst_cadence_block_floor_per_day",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_measure(field_name, getattr(self, field_name)),
            )
        if self.source_class_diversity_block_floor >= self.source_class_diversity_watch_floor:
            raise ValueError(
                "source_class_diversity_watch_floor must exceed "
                "source_class_diversity_block_floor",
            )
        if self.fresh_evidence_max_age_seconds >= self.stale_evidence_block_age_seconds:
            raise ValueError(
                "stale_evidence_block_age_seconds must exceed "
                "fresh_evidence_max_age_seconds",
            )
        if self.catalyst_cadence_block_floor_per_day >= self.catalyst_cadence_watch_floor_per_day:
            raise ValueError(
                "catalyst_cadence_watch_floor_per_day must exceed "
                "catalyst_cadence_block_floor_per_day",
            )
        if self.team_capacity_block_floor >= self.team_capacity_watch_floor:
            raise ValueError("team_capacity_watch_floor must exceed team_capacity_block_floor")
        if self.ambiguity_pressure_watch_threshold >= self.ambiguity_pressure_block_threshold:
            raise ValueError(
                "ambiguity_pressure_block_threshold must exceed "
                "ambiguity_pressure_watch_threshold",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventCoverageSaturationSubject:
    coverage_bucket: str
    source_class_diversity_score: Decimal
    freshest_evidence_age_seconds: Decimal
    catalyst_cadence_per_day: Decimal
    team_capacity_score: Decimal
    ambiguity_pressure_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventCoverageSaturationSubject:
            raise TypeError(
                "ResearchEventCoverageSaturationSubject does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventCoverageSaturationSubject:
            raise ValueError(
                "subject must be exactly ResearchEventCoverageSaturationSubject",
            )
        _require_public_bucket("coverage_bucket", self.coverage_bucket)
        for field_name in (
            "source_class_diversity_score",
            "team_capacity_score",
            "ambiguity_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_score(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "freshest_evidence_age_seconds",
            _normalize_count(
                "freshest_evidence_age_seconds",
                self.freshest_evidence_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "catalyst_cadence_per_day",
            _normalize_nonnegative_measure(
                "catalyst_cadence_per_day",
                self.catalyst_cadence_per_day,
            ),
        )
        _require_hard_flags("subject", self)


@dataclass(frozen=True)
class ResearchEventCoverageSaturationRow:
    coverage_bucket: str
    source_class_diversity_score: Decimal
    freshest_evidence_age_seconds: Decimal
    catalyst_cadence_per_day: Decimal
    team_capacity_score: Decimal
    ambiguity_pressure_score: Decimal
    coverage_saturation_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventCoverageSaturationRow:
            raise TypeError(
                "ResearchEventCoverageSaturationRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventCoverageSaturationRow:
            raise ValueError("row must be exactly ResearchEventCoverageSaturationRow")
        _require_public_bucket("coverage_bucket", self.coverage_bucket)
        for field_name in (
            "source_class_diversity_score",
            "team_capacity_score",
            "ambiguity_pressure_score",
            "coverage_saturation_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_score(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "freshest_evidence_age_seconds",
            _normalize_count(
                "freshest_evidence_age_seconds",
                self.freshest_evidence_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "catalyst_cadence_per_day",
            _normalize_nonnegative_measure(
                "catalyst_cadence_per_day",
                self.catalyst_cadence_per_day,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchEventCoverageSaturationReport:
    generated_at: datetime
    config_version: str
    coverage_bucket_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_coverage_saturation_score: Decimal
    min_coverage_saturation_score: Decimal
    min_source_class_diversity_score: Decimal
    max_freshest_evidence_age_seconds: Decimal
    min_catalyst_cadence_per_day: Decimal
    min_team_capacity_score: Decimal
    max_ambiguity_pressure_score: Decimal
    status: str
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    rows: tuple[ResearchEventCoverageSaturationRow, ...]
    derived_payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventCoverageSaturationReport:
            raise TypeError(
                "ResearchEventCoverageSaturationReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventCoverageSaturationReport:
            raise ValueError("report must be exactly ResearchEventCoverageSaturationReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_string("config_version", self.config_version)
        if self.config_version != CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "coverage_bucket_count",
            "pass_count",
            "watch_count",
            "block_count",
            "max_freshest_evidence_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_coverage_saturation_score",
            "min_coverage_saturation_score",
            "min_source_class_diversity_score",
            "min_team_capacity_score",
            "max_ambiguity_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_score(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_catalyst_cadence_per_day",
            _normalize_nonnegative_measure(
                "min_catalyst_cadence_per_day",
                self.min_catalyst_cadence_per_day,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_digest_string(self.derived_payload_digest)
        _require_hard_flags("report", self)
        _validate_report(self)
        _reject_unsafe_public_payload(_payload_without_digest(self))
        _validate_report_digest(self)


def build_research_event_coverage_saturation_report(
    subjects: list[ResearchEventCoverageSaturationSubject]
    | tuple[ResearchEventCoverageSaturationSubject, ...],
    *,
    generated_at: datetime,
    config: ResearchEventCoverageSaturationConfig,
) -> ResearchEventCoverageSaturationReport:
    if type(config) is not ResearchEventCoverageSaturationConfig:
        raise ValueError("config must be a ResearchEventCoverageSaturationConfig")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (
                _row_from_subject(subject, config=config)
                for subject in _normalize_subjects(subjects)
            ),
            key=_row_sort_key,
        ),
    )
    coverage_bucket_count = _count(len(rows))
    pass_count = _status_count(rows, PASS)
    watch_count = _status_count(rows, WATCH)
    block_count = _status_count(rows, BLOCK)
    average_score = _average_score(row.coverage_saturation_score for row in rows)
    min_score = _min_decimal(
        (row.coverage_saturation_score for row in rows),
        default=ZERO_SCORE,
    )
    min_source = _min_decimal(
        (row.source_class_diversity_score for row in rows),
        default=ZERO_SCORE,
    )
    max_age = _max_decimal(
        (row.freshest_evidence_age_seconds for row in rows),
        default=ZERO_COUNT,
    )
    min_catalyst = _min_decimal(
        (row.catalyst_cadence_per_day for row in rows),
        default=ZERO_SCORE,
    )
    min_capacity = _min_decimal((row.team_capacity_score for row in rows), default=ZERO_SCORE)
    max_ambiguity = _max_decimal(
        (row.ambiguity_pressure_score for row in rows),
        default=ZERO_SCORE,
    )
    status = _report_status(rows)
    reason_code_counts = _reason_code_counts(rows)
    digest = _payload_digest(
        _payload_without_digest_values(
            generated_at=generated_at,
            config_version=config.config_version,
            coverage_bucket_count=coverage_bucket_count,
            pass_count=pass_count,
            watch_count=watch_count,
            block_count=block_count,
            average_coverage_saturation_score=average_score,
            min_coverage_saturation_score=min_score,
            min_source_class_diversity_score=min_source,
            max_freshest_evidence_age_seconds=max_age,
            min_catalyst_cadence_per_day=min_catalyst,
            min_team_capacity_score=min_capacity,
            max_ambiguity_pressure_score=max_ambiguity,
            status=status,
            reason_code_counts=reason_code_counts,
            rows=rows,
            paper_only=True,
            report_only=True,
            readonly=True,
        ),
    )
    return ResearchEventCoverageSaturationReport(
        generated_at=generated_at,
        config_version=config.config_version,
        coverage_bucket_count=coverage_bucket_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        average_coverage_saturation_score=average_score,
        min_coverage_saturation_score=min_score,
        min_source_class_diversity_score=min_source,
        max_freshest_evidence_age_seconds=max_age,
        min_catalyst_cadence_per_day=min_catalyst,
        min_team_capacity_score=min_capacity,
        max_ambiguity_pressure_score=max_ambiguity,
        status=status,
        reason_code_counts=reason_code_counts,
        rows=rows,
        derived_payload_digest=digest,
    )


def research_event_coverage_saturation_report_payload(
    report: ResearchEventCoverageSaturationReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchEventCoverageSaturationReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload(_payload_without_digest(report))
        payload = _report_payload(report)
    elif type(report) is dict:
        payload = _normalize_payload(report)
        _reject_unsafe_public_payload(payload)
        _validate_payload_digest(payload)
    else:
        raise ValueError(
            "report must be a ResearchEventCoverageSaturationReport or payload dict",
        )
    _require_payload_hard_flags(payload)
    return payload


def _row_from_subject(
    subject: ResearchEventCoverageSaturationSubject,
    *,
    config: ResearchEventCoverageSaturationConfig,
) -> ResearchEventCoverageSaturationRow:
    reason_codes = _row_reason_codes(subject, config=config)
    return ResearchEventCoverageSaturationRow(
        coverage_bucket=subject.coverage_bucket,
        source_class_diversity_score=subject.source_class_diversity_score,
        freshest_evidence_age_seconds=subject.freshest_evidence_age_seconds,
        catalyst_cadence_per_day=subject.catalyst_cadence_per_day,
        team_capacity_score=subject.team_capacity_score,
        ambiguity_pressure_score=subject.ambiguity_pressure_score,
        coverage_saturation_score=_coverage_saturation_score(subject, config=config),
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _coverage_saturation_score(
    subject: ResearchEventCoverageSaturationSubject,
    *,
    config: ResearchEventCoverageSaturationConfig,
) -> Decimal:
    values = (
        subject.source_class_diversity_score,
        _evidence_freshness_score(subject.freshest_evidence_age_seconds, config=config),
        _catalyst_cadence_score(subject.catalyst_cadence_per_day, config=config),
        subject.team_capacity_score,
        _normalize_score(
            "ambiguity_pressure_inverse_score",
            ONE_SCORE - subject.ambiguity_pressure_score,
        ),
    )
    return _average_score(values)


def _evidence_freshness_score(
    age_seconds: Decimal,
    *,
    config: ResearchEventCoverageSaturationConfig,
) -> Decimal:
    if age_seconds >= config.stale_evidence_block_age_seconds:
        return ZERO_SCORE
    with localcontext(DECIMAL_CONTEXT):
        score = ONE_SCORE - (age_seconds / config.stale_evidence_block_age_seconds)
    return _normalize_score("evidence_freshness_score", max(ZERO_SCORE, score))


def _catalyst_cadence_score(
    cadence_per_day: Decimal,
    *,
    config: ResearchEventCoverageSaturationConfig,
) -> Decimal:
    if config.catalyst_cadence_watch_floor_per_day == ZERO_SCORE:
        return ONE_SCORE
    with localcontext(DECIMAL_CONTEXT):
        score = cadence_per_day / config.catalyst_cadence_watch_floor_per_day
    return _normalize_score("catalyst_cadence_score", min(ONE_SCORE, score))


def _row_reason_codes(
    subject: ResearchEventCoverageSaturationSubject,
    *,
    config: ResearchEventCoverageSaturationConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if subject.source_class_diversity_score < config.source_class_diversity_block_floor:
        codes.append("low_source_class_diversity_block")
    elif subject.source_class_diversity_score < config.source_class_diversity_watch_floor:
        codes.append("low_source_class_diversity_watch")
    if subject.freshest_evidence_age_seconds > config.stale_evidence_block_age_seconds:
        codes.append("stale_evidence_age_block")
    elif subject.freshest_evidence_age_seconds > config.fresh_evidence_max_age_seconds:
        codes.append("aging_evidence_watch")
    if subject.catalyst_cadence_per_day < config.catalyst_cadence_block_floor_per_day:
        codes.append("thin_catalyst_cadence_block")
    elif subject.catalyst_cadence_per_day < config.catalyst_cadence_watch_floor_per_day:
        codes.append("thin_catalyst_cadence_watch")
    if subject.team_capacity_score < config.team_capacity_block_floor:
        codes.append("constrained_team_capacity_block")
    elif subject.team_capacity_score < config.team_capacity_watch_floor:
        codes.append("constrained_team_capacity_watch")
    if subject.ambiguity_pressure_score >= config.ambiguity_pressure_block_threshold:
        codes.append("high_ambiguity_pressure_block")
    elif subject.ambiguity_pressure_score >= config.ambiguity_pressure_watch_threshold:
        codes.append("elevated_ambiguity_pressure_watch")
    return tuple(codes) if codes else ("coverage_saturation_clear",)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(code.endswith("_block") for code in reason_codes):
        return BLOCK
    if any(code.endswith("_watch") for code in reason_codes):
        return WATCH
    return PASS


def _report_status(rows: tuple[ResearchEventCoverageSaturationRow, ...]) -> str:
    if any(row.status == BLOCK for row in rows):
        return BLOCK
    if any(row.status == WATCH for row in rows):
        return WATCH
    return PASS


def _normalize_subjects(
    subjects: list[ResearchEventCoverageSaturationSubject]
    | tuple[ResearchEventCoverageSaturationSubject, ...],
) -> tuple[ResearchEventCoverageSaturationSubject, ...]:
    if type(subjects) not in (list, tuple):
        raise ValueError("subjects must be a list or tuple")
    normalized = tuple(subjects)
    seen: set[str] = set()
    for subject in normalized:
        if type(subject) is not ResearchEventCoverageSaturationSubject:
            raise ValueError(
                "subjects must contain ResearchEventCoverageSaturationSubject values",
            )
        _require_hard_flags("subject", subject)
        if subject.coverage_bucket in seen:
            raise ValueError("duplicate coverage_bucket values are not allowed")
        seen.add(subject.coverage_bucket)
    return normalized


def _normalize_rows(
    rows: tuple[ResearchEventCoverageSaturationRow, ...],
) -> tuple[ResearchEventCoverageSaturationRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchEventCoverageSaturationRow:
            raise ValueError("rows must contain ResearchEventCoverageSaturationRow values")
        _require_hard_flags("row", row)
    return tuple(sorted(rows, key=_row_sort_key))


def _normalize_reason_code_counts(
    values: tuple[tuple[str, Decimal], ...],
) -> tuple[tuple[str, Decimal], ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized: list[tuple[str, Decimal]] = []
    for item in values:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("reason_code_counts must contain reason/count tuples")
        reason_code, count = item
        if type(reason_code) is not str:
            raise ValueError("reason_code must be a string")
        if reason_code not in ROW_REASON_CODES:
            raise ValueError("reason_code must be supported")
        normalized.append((reason_code, _normalize_count("reason_code_count", count)))
    return tuple(sorted(normalized, key=lambda item: (-item[1], item[0])))


def _normalize_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    for value in values:
        if type(value) is not str:
            raise ValueError("reason_codes must contain strings")
        if value not in ROW_REASON_CODES:
            raise ValueError("reason_code must be supported")
        if value not in normalized:
            normalized.append(value)
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    return tuple(normalized)


def _reason_code_counts(
    rows: tuple[ResearchEventCoverageSaturationRow, ...],
) -> tuple[tuple[str, Decimal], ...]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        sorted(
            ((reason_code, _count(count)) for reason_code, count in counter.items()),
            key=lambda item: (-item[1], item[0]),
        ),
    )


def _validate_row(row: ResearchEventCoverageSaturationRow) -> None:
    expected_status = _row_status(row.reason_codes)
    if row.status != expected_status:
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchEventCoverageSaturationReport) -> None:
    if report.coverage_bucket_count != _count(len(report.rows)):
        raise ValueError("coverage_bucket_count must match rows")
    if report.pass_count != _status_count(report.rows, PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, BLOCK):
        raise ValueError("block_count must match rows")
    if report.pass_count + report.watch_count + report.block_count != report.coverage_bucket_count:
        raise ValueError("status counts must match coverage_bucket_count")
    if report.average_coverage_saturation_score != _average_score(
        row.coverage_saturation_score for row in report.rows
    ):
        raise ValueError("average_coverage_saturation_score must match rows")
    if report.min_coverage_saturation_score != _min_decimal(
        (row.coverage_saturation_score for row in report.rows),
        default=ZERO_SCORE,
    ):
        raise ValueError("min_coverage_saturation_score must match rows")
    if report.min_source_class_diversity_score != _min_decimal(
        (row.source_class_diversity_score for row in report.rows),
        default=ZERO_SCORE,
    ):
        raise ValueError("min_source_class_diversity_score must match rows")
    if report.max_freshest_evidence_age_seconds != _max_decimal(
        (row.freshest_evidence_age_seconds for row in report.rows),
        default=ZERO_COUNT,
    ):
        raise ValueError("max_freshest_evidence_age_seconds must match rows")
    if report.min_catalyst_cadence_per_day != _min_decimal(
        (row.catalyst_cadence_per_day for row in report.rows),
        default=ZERO_SCORE,
    ):
        raise ValueError("min_catalyst_cadence_per_day must match rows")
    if report.min_team_capacity_score != _min_decimal(
        (row.team_capacity_score for row in report.rows),
        default=ZERO_SCORE,
    ):
        raise ValueError("min_team_capacity_score must match rows")
    if report.max_ambiguity_pressure_score != _max_decimal(
        (row.ambiguity_pressure_score for row in report.rows),
        default=ZERO_SCORE,
    ):
        raise ValueError("max_ambiguity_pressure_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _validate_report_digest(report: ResearchEventCoverageSaturationReport) -> None:
    expected = _payload_digest(_payload_without_digest(report))
    if report.derived_payload_digest != expected:
        raise ValueError("derived_payload_digest must match report contents")


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    expected = _payload_digest({key: value for key, value in payload.items() if key != "derived_payload_digest"})
    if payload["derived_payload_digest"] != expected:
        raise ValueError("derived_payload_digest must match payload contents")


def _payload_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _report_payload(report: ResearchEventCoverageSaturationReport) -> dict[str, Any]:
    payload = _payload_without_digest(report)
    return {
        **{
            key: value
            for key, value in payload.items()
            if key not in ("paper_only", "report_only", "readonly")
        },
        "derived_payload_digest": report.derived_payload_digest,
        "paper_only": payload["paper_only"],
        "report_only": payload["report_only"],
        "readonly": payload["readonly"],
    }


def _payload_without_digest(report: ResearchEventCoverageSaturationReport) -> dict[str, Any]:
    return _payload_without_digest_values(
        generated_at=report.generated_at,
        config_version=report.config_version,
        coverage_bucket_count=report.coverage_bucket_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        average_coverage_saturation_score=report.average_coverage_saturation_score,
        min_coverage_saturation_score=report.min_coverage_saturation_score,
        min_source_class_diversity_score=report.min_source_class_diversity_score,
        max_freshest_evidence_age_seconds=report.max_freshest_evidence_age_seconds,
        min_catalyst_cadence_per_day=report.min_catalyst_cadence_per_day,
        min_team_capacity_score=report.min_team_capacity_score,
        max_ambiguity_pressure_score=report.max_ambiguity_pressure_score,
        status=report.status,
        reason_code_counts=report.reason_code_counts,
        rows=report.rows,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def _payload_without_digest_values(
    *,
    generated_at: datetime,
    config_version: str,
    coverage_bucket_count: Decimal,
    pass_count: Decimal,
    watch_count: Decimal,
    block_count: Decimal,
    average_coverage_saturation_score: Decimal,
    min_coverage_saturation_score: Decimal,
    min_source_class_diversity_score: Decimal,
    max_freshest_evidence_age_seconds: Decimal,
    min_catalyst_cadence_per_day: Decimal,
    min_team_capacity_score: Decimal,
    max_ambiguity_pressure_score: Decimal,
    status: str,
    reason_code_counts: tuple[tuple[str, Decimal], ...],
    rows: tuple[ResearchEventCoverageSaturationRow, ...],
    paper_only: bool,
    report_only: bool,
    readonly: bool,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "generated_at": generated_at.isoformat(),
        "config_version": config_version,
        "coverage_bucket_count": _count_string(coverage_bucket_count),
        "pass_count": _count_string(pass_count),
        "watch_count": _count_string(watch_count),
        "block_count": _count_string(block_count),
        "average_coverage_saturation_score": _score_string(
            average_coverage_saturation_score,
        ),
        "min_coverage_saturation_score": _score_string(min_coverage_saturation_score),
        "min_source_class_diversity_score": _score_string(
            min_source_class_diversity_score,
        ),
        "max_freshest_evidence_age_seconds": _count_string(
            max_freshest_evidence_age_seconds,
        ),
        "min_catalyst_cadence_per_day": _score_string(min_catalyst_cadence_per_day),
        "min_team_capacity_score": _score_string(min_team_capacity_score),
        "max_ambiguity_pressure_score": _score_string(max_ambiguity_pressure_score),
        "status": status,
        "reason_code_counts": [
            [reason_code, _count_string(count)]
            for reason_code, count in reason_code_counts
        ],
        "rows": [_row_payload(row) for row in rows],
        "paper_only": paper_only,
        "report_only": report_only,
        "readonly": readonly,
    }
    return payload


def _row_payload(row: ResearchEventCoverageSaturationRow) -> dict[str, Any]:
    return {
        "coverage_bucket": row.coverage_bucket,
        "source_class_diversity_score": _score_string(row.source_class_diversity_score),
        "freshest_evidence_age_seconds": _count_string(row.freshest_evidence_age_seconds),
        "catalyst_cadence_per_day": _score_string(row.catalyst_cadence_per_day),
        "team_capacity_score": _score_string(row.team_capacity_score),
        "ambiguity_pressure_score": _score_string(row.ambiguity_pressure_score),
        "coverage_saturation_score": _score_string(row.coverage_saturation_score),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if tuple(payload.keys()) != PUBLIC_PAYLOAD_KEYS:
        raise ValueError("payload must match the public readonly schema")
    normalized = dict(payload)
    if type(normalized["generated_at"]) is not str:
        raise ValueError("generated_at must be an ISO string")
    _as_utc("generated_at", datetime.fromisoformat(normalized["generated_at"]))
    if normalized["config_version"] != CONFIG_VERSION:
        raise ValueError("config_version must be supported")
    for field_name in REPORT_NUMERIC_FIELDS:
        if type(normalized[field_name]) is not str:
            raise ValueError(f"{field_name} must be a Decimal-derived string")
        Decimal(normalized[field_name])
    _require_status("status", normalized["status"])
    if type(normalized["reason_code_counts"]) is not list:
        raise ValueError("reason_code_counts must be a list")
    for item in normalized["reason_code_counts"]:
        if type(item) is not list or len(item) != 2:
            raise ValueError("reason_code_counts must contain two-item lists")
        if item[0] not in ROW_REASON_CODES:
            raise ValueError("reason_code must be supported")
        if type(item[1]) is not str:
            raise ValueError("reason_code count must be a Decimal-derived string")
        Decimal(item[1])
    if type(normalized["rows"]) is not list:
        raise ValueError("rows must be a list")
    for row in normalized["rows"]:
        _validate_payload_row(row)
    _require_digest_string(normalized["derived_payload_digest"])
    _require_payload_hard_flags(normalized)
    return normalized


def _validate_payload_row(row: object) -> None:
    if type(row) is not dict:
        raise ValueError("rows must contain public row objects")
    if tuple(row.keys()) != PUBLIC_ROW_KEYS:
        raise ValueError("row must match the public readonly schema")
    _require_public_bucket("coverage_bucket", row["coverage_bucket"])
    for field_name in ROW_NUMERIC_FIELDS:
        if type(row[field_name]) is not str:
            raise ValueError(f"{field_name} must be a Decimal-derived string")
        Decimal(row[field_name])
    _require_status("status", row["status"])
    if type(row["reason_codes"]) is not list:
        raise ValueError("reason_codes must be a list")
    for value in row["reason_codes"]:
        if value not in ROW_REASON_CODES:
            raise ValueError("reason_code must be supported")
    _require_payload_hard_flags(row)


def _reject_unsafe_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _reject_unsafe_public_string(key)
            _reject_unsafe_public_payload(item)
    elif isinstance(value, list | tuple):
        for item in value:
            _reject_unsafe_public_payload(item)
    elif type(value) is str:
        _reject_unsafe_public_string(value)


def _reject_unsafe_public_string(value: str) -> None:
    lower = value.lower()
    if any(fragment in lower for fragment in UNSAFE_PAYLOAD_FRAGMENTS):
        raise ValueError("payload contains unsafe public surface")


def _require_payload_hard_flags(payload: dict[str, Any]) -> None:
    if payload.get("paper_only") is not True:
        raise ValueError("paper_only must be True")
    if payload.get("report_only") is not True:
        raise ValueError("report_only must be True")
    if payload.get("readonly") is not True:
        raise ValueError("readonly must be True")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be a canonical string")


def _require_public_bucket(field_name: str, value: object) -> None:
    _require_string(field_name, value)
    assert type(value) is str
    lower = value.lower()
    if any(fragment in lower for fragment in UNSAFE_BUCKET_FRAGMENTS):
        raise ValueError(f"{field_name} must be a public aggregate bucket")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass/watch/block")


def _require_digest_string(value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError("derived_payload_digest must be a sha256 hex string")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError("derived_payload_digest must be a sha256 hex string") from exc


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if value.is_nan() or value.is_infinite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _normalize_score(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO_SCORE or value > ONE_SCORE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(value, SCORE_QUANTUM)


def _normalize_count(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value(rounding=ROUND_HALF_EVEN):
        raise ValueError(f"{field_name} must be a whole Decimal")
    return _quantize(value, COUNT_QUANTUM)


def _normalize_nonnegative_measure(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO_SCORE:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(value, SCORE_QUANTUM)


def _quantize(value: Decimal, quantum: Decimal) -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(quantum)
    except InvalidOperation as exc:
        raise ValueError("Decimal value could not be normalized") from exc


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    offset = value.utcoffset()
    if offset is None:
        raise ValueError(f"{field_name} must have a valid UTC offset")
    return value.astimezone(UTC)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _status_count(rows: tuple[ResearchEventCoverageSaturationRow, ...], status: str) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _average_score(values: Any) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO_SCORE
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_score(
            "average_score",
            sum(normalized, ZERO_SCORE) / Decimal(len(normalized)),
        )


def _min_decimal(values: Any, *, default: Decimal) -> Decimal:
    normalized = tuple(values)
    return min(normalized) if normalized else default


def _max_decimal(values: Any, *, default: Decimal) -> Decimal:
    normalized = tuple(values)
    return max(normalized) if normalized else default


def _row_sort_key(row: ResearchEventCoverageSaturationRow) -> tuple[Decimal, str]:
    return (STATUS_SORT[row.status], row.coverage_bucket)


def _count_string(value: Decimal) -> str:
    return format(_normalize_count("count", value), "f")


def _score_string(value: Decimal) -> str:
    return format(_normalize_nonnegative_measure("score", value), "f")
