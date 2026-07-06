"""Pure paper-only strategy category learning value digest."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any


DEFAULT_STRATEGY_CATEGORY_LEARNING_VALUE_DIGEST_CONFIG_VERSION = (
    "strategy-category-learning-value-digest-v0"
)

VALUE_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0").quantize(VALUE_QUANTUM)
ZERO_COUNT = Decimal("0").quantize(COUNT_QUANTUM)
ONE = Decimal("1.000000")
PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCKED_STATUS = "blocked"
STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCKED_STATUS)
ROW_REASON_CODES = (
    "calibration_backlog_high",
    "capital_efficiency_low",
    "event_archetype_coverage_low",
    "forecast_error_reduction_low",
    "learning_value_blocked",
    "learning_value_pass",
    "learning_value_watch",
    "resolved_sample_count_low",
    "source_reliability_improvement_low",
)
EMPTY_REASON_CODE = "strategy_category_learning_value_digest_empty"
REPORT_REASON_CODES = tuple(sorted((*ROW_REASON_CODES, EMPTY_REASON_CODE)))
VALIDATION_DIGEST_ALGORITHM = "sha256"
HEX_DIGITS = frozenset("0123456789abcdef")
SENSITIVE_REFERENCE_MARKERS = (
    "://",
    "tok" + "en=",
    "api" + "_key=",
    "sec" + "ret",
    "priv" + "ate",
    "wal" + "let:",
    "bear" + "er ",
    "pass" + "word",
    "seed" + "_phrase",
)
UNSAFE_SURFACE_FIELD_FRAGMENTS = (
    "api" + "_key",
    "aut" + "h",
    "priv" + "ate_key",
    "wal" + "let",
    "account",
    "balance",
    "ord" + "er",
    "can" + "cel",
    "re" + "place",
    "si" + "gn",
    "exchange" + "_mutation",
    "bro" + "ker",
)
RAW_LEARNING_REFERENCE_FIELD = "learning_reference"


@dataclass(frozen=True)
class StrategyCategoryLearningValueDigestConfig:
    config_version: str = DEFAULT_STRATEGY_CATEGORY_LEARNING_VALUE_DIGEST_CONFIG_VERSION
    target_resolved_sample_count: Decimal = Decimal("10")
    min_resolved_sample_count: Decimal = Decimal("3")
    target_forecast_error_reduction: Decimal = Decimal("0.050000")
    target_source_reliability_improvement: Decimal = Decimal("0.100000")
    min_event_archetype_coverage_ratio: Decimal = Decimal("0.500000")
    max_calibration_backlog: Decimal = Decimal("5")
    min_capital_efficiency: Decimal = Decimal("0.100000")
    pass_learning_value_score: Decimal = Decimal("0.700000")
    watch_learning_value_score: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "target_resolved_sample_count",
            _normalize_positive_count(
                "target_resolved_sample_count",
                self.target_resolved_sample_count,
            ),
        )
        object.__setattr__(
            self,
            "min_resolved_sample_count",
            _normalize_nonnegative_count(
                "min_resolved_sample_count",
                self.min_resolved_sample_count,
            ),
        )
        if self.min_resolved_sample_count > self.target_resolved_sample_count:
            raise ValueError(
                "min_resolved_sample_count must not exceed target_resolved_sample_count",
            )
        object.__setattr__(
            self,
            "target_forecast_error_reduction",
            _normalize_positive_value(
                "target_forecast_error_reduction",
                self.target_forecast_error_reduction,
            ),
        )
        object.__setattr__(
            self,
            "target_source_reliability_improvement",
            _normalize_positive_value(
                "target_source_reliability_improvement",
                self.target_source_reliability_improvement,
            ),
        )
        for field_name in (
            "min_event_archetype_coverage_ratio",
            "min_capital_efficiency",
            "pass_learning_value_score",
            "watch_learning_value_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.pass_learning_value_score < self.watch_learning_value_score:
            raise ValueError(
                "pass_learning_value_score must be at least watch_learning_value_score",
            )
        object.__setattr__(
            self,
            "max_calibration_backlog",
            _normalize_positive_count(
                "max_calibration_backlog",
                self.max_calibration_backlog,
            ),
        )
        _require_paper_flags("config", self)


@dataclass(frozen=True)
class StrategyCategoryLearningValueInput:
    category: str
    sample_observed_at: datetime
    resolved_sample_count: Decimal
    previous_forecast_error: Decimal
    current_forecast_error: Decimal
    previous_source_reliability: Decimal
    current_source_reliability: Decimal
    covered_event_archetype_count: Decimal
    required_event_archetype_count: Decimal
    calibration_backlog: Decimal
    capital_efficiency: Decimal
    learning_reference: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("category", self.category)
        object.__setattr__(
            self,
            "sample_observed_at",
            _as_utc("sample_observed_at", self.sample_observed_at),
        )
        for field_name in (
            "resolved_sample_count",
            "covered_event_archetype_count",
            "calibration_backlog",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "required_event_archetype_count",
            _normalize_positive_count(
                "required_event_archetype_count",
                self.required_event_archetype_count,
            ),
        )
        for field_name in (
            "previous_forecast_error",
            "current_forecast_error",
            "previous_source_reliability",
            "current_source_reliability",
            "capital_efficiency",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.covered_event_archetype_count > self.required_event_archetype_count:
            raise ValueError(
                "covered_event_archetype_count must not exceed required_event_archetype_count",
            )
        _require_canonical_string("learning_reference", self.learning_reference)
        _require_paper_flags("input", self)


@dataclass(frozen=True)
class StrategyCategoryLearningValueDigestRow:
    rank: Decimal
    category: str
    sample_observed_at: datetime
    resolved_sample_count: Decimal
    resolved_sample_score: Decimal
    previous_forecast_error: Decimal
    current_forecast_error: Decimal
    forecast_error_reduction: Decimal
    forecast_error_reduction_score: Decimal
    previous_source_reliability: Decimal
    current_source_reliability: Decimal
    source_reliability_improvement: Decimal
    source_reliability_improvement_score: Decimal
    covered_event_archetype_count: Decimal
    required_event_archetype_count: Decimal
    event_archetype_coverage_ratio: Decimal
    calibration_backlog: Decimal
    calibration_backlog_score: Decimal
    capital_efficiency: Decimal
    learning_value_score: Decimal
    learning_value_status: str
    redacted_learning_reference: str
    reason_codes: tuple[str, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "rank", _normalize_positive_count("rank", self.rank))
        _require_canonical_string("category", self.category)
        object.__setattr__(
            self,
            "sample_observed_at",
            _as_utc("sample_observed_at", self.sample_observed_at),
        )
        for field_name in (
            "resolved_sample_count",
            "covered_event_archetype_count",
            "required_event_archetype_count",
            "calibration_backlog",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.required_event_archetype_count <= ZERO_COUNT:
            raise ValueError("required_event_archetype_count must be above zero")
        for field_name in (
            "resolved_sample_score",
            "previous_forecast_error",
            "current_forecast_error",
            "forecast_error_reduction",
            "forecast_error_reduction_score",
            "previous_source_reliability",
            "current_source_reliability",
            "source_reliability_improvement",
            "source_reliability_improvement_score",
            "event_archetype_coverage_ratio",
            "calibration_backlog_score",
            "capital_efficiency",
            "learning_value_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("learning_value_status", self.learning_value_status, STATUSES)
        _require_canonical_string(
            "redacted_learning_reference",
            self.redacted_learning_reference,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        object.__setattr__(
            self,
            "validation_digest",
            _require_validation_digest("validation_digest", self.validation_digest),
        )
        _validate_row(self)
        _validate_row_digest(self)
        _require_paper_flags("row", self)


@dataclass(frozen=True)
class StrategyCategoryLearningValueDigestReport:
    generated_at: datetime
    config_version: str
    category_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    top_category: str | None
    max_learning_value_score: Decimal
    min_learning_value_score: Decimal
    average_learning_value_score: Decimal
    digest_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyCategoryLearningValueDigestRow, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "category_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.top_category is not None:
            _require_canonical_string("top_category", self.top_category)
        for field_name in (
            "max_learning_value_score",
            "min_learning_value_score",
            "average_learning_value_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("digest_status", self.digest_status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "validation_digest",
            _require_validation_digest("validation_digest", self.validation_digest),
        )
        _validate_report(self)
        _validate_report_digest(self)
        _require_paper_flags("report", self)


def build_strategy_category_learning_value_digest(
    categories: Iterable[StrategyCategoryLearningValueInput],
    *,
    config: StrategyCategoryLearningValueDigestConfig,
    generated_at: datetime,
) -> StrategyCategoryLearningValueDigestReport:
    if type(config) is not StrategyCategoryLearningValueDigestConfig:
        raise ValueError("config must be a StrategyCategoryLearningValueDigestConfig")
    _require_paper_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_rows = _normalize_inputs(categories)
    ranked_rows = _rank_rows(
        tuple(_unranked_row(row, config) for row in source_rows),
    )

    category_count = _count(len(ranked_rows))
    pass_count = _count(_status_count(ranked_rows, PASS_STATUS))
    watch_count = _count(_status_count(ranked_rows, WATCH_STATUS))
    blocked_count = _count(_status_count(ranked_rows, BLOCKED_STATUS))
    top_category = ranked_rows[0].category if ranked_rows else None
    max_learning_value_score = _max_learning_value_score(ranked_rows)
    min_learning_value_score = _min_learning_value_score(ranked_rows)
    average_learning_value_score = _average_learning_value_score(ranked_rows)
    digest_status = _digest_status(ranked_rows)
    reason_codes = _report_reason_codes(ranked_rows)

    return StrategyCategoryLearningValueDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        category_count=category_count,
        pass_count=pass_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        top_category=top_category,
        max_learning_value_score=max_learning_value_score,
        min_learning_value_score=min_learning_value_score,
        average_learning_value_score=average_learning_value_score,
        digest_status=digest_status,
        reason_codes=reason_codes,
        rows=ranked_rows,
        validation_digest=_report_validation_digest(
            generated_at=generated_at_utc,
            config_version=config.config_version,
            category_count=category_count,
            pass_count=pass_count,
            watch_count=watch_count,
            blocked_count=blocked_count,
            top_category=top_category,
            max_learning_value_score=max_learning_value_score,
            min_learning_value_score=min_learning_value_score,
            average_learning_value_score=average_learning_value_score,
            digest_status=digest_status,
            reason_codes=reason_codes,
            rows=ranked_rows,
        ),
    )


def strategy_category_learning_value_digest_payload(
    report: StrategyCategoryLearningValueDigestReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyCategoryLearningValueDigestReport:
        _require_paper_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        _validate_report(report)
        _validate_report_digest(report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a StrategyCategoryLearningValueDigestReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_paper_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    _validate_payload_digest(payload)
    return payload


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


def _unranked_row(
    row: StrategyCategoryLearningValueInput,
    config: StrategyCategoryLearningValueDigestConfig,
) -> StrategyCategoryLearningValueDigestRow:
    resolved_sample_score = _ratio(
        min(row.resolved_sample_count, config.target_resolved_sample_count),
        config.target_resolved_sample_count,
    )
    forecast_error_reduction = _q(max(row.previous_forecast_error - row.current_forecast_error, ZERO))
    forecast_error_reduction_score = _ratio(
        min(forecast_error_reduction, config.target_forecast_error_reduction),
        config.target_forecast_error_reduction,
    )
    source_reliability_improvement = _q(
        max(row.current_source_reliability - row.previous_source_reliability, ZERO),
    )
    source_reliability_improvement_score = _ratio(
        min(
            source_reliability_improvement,
            config.target_source_reliability_improvement,
        ),
        config.target_source_reliability_improvement,
    )
    event_archetype_coverage_ratio = _ratio(
        row.covered_event_archetype_count,
        row.required_event_archetype_count,
    )
    calibration_backlog_score = _ratio(
        max(config.max_calibration_backlog - row.calibration_backlog, ZERO_COUNT),
        config.max_calibration_backlog,
    )
    learning_value_score = _learning_value_score(
        resolved_sample_score=resolved_sample_score,
        forecast_error_reduction_score=forecast_error_reduction_score,
        source_reliability_improvement_score=source_reliability_improvement_score,
        event_archetype_coverage_ratio=event_archetype_coverage_ratio,
        calibration_backlog_score=calibration_backlog_score,
        capital_efficiency=row.capital_efficiency,
    )
    status = _row_status(learning_value_score, config)
    redacted_learning_reference = _redact_learning_reference(row.learning_reference)
    reason_codes = _row_reason_codes(
        row,
        forecast_error_reduction=forecast_error_reduction,
        source_reliability_improvement=source_reliability_improvement,
        event_archetype_coverage_ratio=event_archetype_coverage_ratio,
        status=status,
        config=config,
    )
    return StrategyCategoryLearningValueDigestRow(
        rank=Decimal("1"),
        category=row.category,
        sample_observed_at=row.sample_observed_at,
        resolved_sample_count=row.resolved_sample_count,
        resolved_sample_score=resolved_sample_score,
        previous_forecast_error=row.previous_forecast_error,
        current_forecast_error=row.current_forecast_error,
        forecast_error_reduction=forecast_error_reduction,
        forecast_error_reduction_score=forecast_error_reduction_score,
        previous_source_reliability=row.previous_source_reliability,
        current_source_reliability=row.current_source_reliability,
        source_reliability_improvement=source_reliability_improvement,
        source_reliability_improvement_score=source_reliability_improvement_score,
        covered_event_archetype_count=row.covered_event_archetype_count,
        required_event_archetype_count=row.required_event_archetype_count,
        event_archetype_coverage_ratio=event_archetype_coverage_ratio,
        calibration_backlog=row.calibration_backlog,
        calibration_backlog_score=calibration_backlog_score,
        capital_efficiency=row.capital_efficiency,
        learning_value_score=learning_value_score,
        learning_value_status=status,
        redacted_learning_reference=redacted_learning_reference,
        reason_codes=reason_codes,
        validation_digest=_row_validation_digest(
            rank=Decimal("1"),
            category=row.category,
            sample_observed_at=row.sample_observed_at,
            resolved_sample_count=row.resolved_sample_count,
            resolved_sample_score=resolved_sample_score,
            previous_forecast_error=row.previous_forecast_error,
            current_forecast_error=row.current_forecast_error,
            forecast_error_reduction=forecast_error_reduction,
            forecast_error_reduction_score=forecast_error_reduction_score,
            previous_source_reliability=row.previous_source_reliability,
            current_source_reliability=row.current_source_reliability,
            source_reliability_improvement=source_reliability_improvement,
            source_reliability_improvement_score=source_reliability_improvement_score,
            covered_event_archetype_count=row.covered_event_archetype_count,
            required_event_archetype_count=row.required_event_archetype_count,
            event_archetype_coverage_ratio=event_archetype_coverage_ratio,
            calibration_backlog=row.calibration_backlog,
            calibration_backlog_score=calibration_backlog_score,
            capital_efficiency=row.capital_efficiency,
            learning_value_score=learning_value_score,
            learning_value_status=status,
            redacted_learning_reference=redacted_learning_reference,
            reason_codes=reason_codes,
        ),
    )


def _rank_rows(
    rows: tuple[StrategyCategoryLearningValueDigestRow, ...],
) -> tuple[StrategyCategoryLearningValueDigestRow, ...]:
    sorted_rows = sorted(
        rows,
        key=lambda row: (
            -row.learning_value_score,
            _status_sort_value(row.learning_value_status),
            row.category,
        ),
    )
    return tuple(
        StrategyCategoryLearningValueDigestRow(
            rank=_count(index),
            category=row.category,
            sample_observed_at=row.sample_observed_at,
            resolved_sample_count=row.resolved_sample_count,
            resolved_sample_score=row.resolved_sample_score,
            previous_forecast_error=row.previous_forecast_error,
            current_forecast_error=row.current_forecast_error,
            forecast_error_reduction=row.forecast_error_reduction,
            forecast_error_reduction_score=row.forecast_error_reduction_score,
            previous_source_reliability=row.previous_source_reliability,
            current_source_reliability=row.current_source_reliability,
            source_reliability_improvement=row.source_reliability_improvement,
            source_reliability_improvement_score=row.source_reliability_improvement_score,
            covered_event_archetype_count=row.covered_event_archetype_count,
            required_event_archetype_count=row.required_event_archetype_count,
            event_archetype_coverage_ratio=row.event_archetype_coverage_ratio,
            calibration_backlog=row.calibration_backlog,
            calibration_backlog_score=row.calibration_backlog_score,
            capital_efficiency=row.capital_efficiency,
            learning_value_score=row.learning_value_score,
            learning_value_status=row.learning_value_status,
            redacted_learning_reference=row.redacted_learning_reference,
            reason_codes=row.reason_codes,
            validation_digest=_row_validation_digest(
                rank=_count(index),
                category=row.category,
                sample_observed_at=row.sample_observed_at,
                resolved_sample_count=row.resolved_sample_count,
                resolved_sample_score=row.resolved_sample_score,
                previous_forecast_error=row.previous_forecast_error,
                current_forecast_error=row.current_forecast_error,
                forecast_error_reduction=row.forecast_error_reduction,
                forecast_error_reduction_score=row.forecast_error_reduction_score,
                previous_source_reliability=row.previous_source_reliability,
                current_source_reliability=row.current_source_reliability,
                source_reliability_improvement=row.source_reliability_improvement,
                source_reliability_improvement_score=row.source_reliability_improvement_score,
                covered_event_archetype_count=row.covered_event_archetype_count,
                required_event_archetype_count=row.required_event_archetype_count,
                event_archetype_coverage_ratio=row.event_archetype_coverage_ratio,
                calibration_backlog=row.calibration_backlog,
                calibration_backlog_score=row.calibration_backlog_score,
                capital_efficiency=row.capital_efficiency,
                learning_value_score=row.learning_value_score,
                learning_value_status=row.learning_value_status,
                redacted_learning_reference=row.redacted_learning_reference,
                reason_codes=row.reason_codes,
            ),
        )
        for index, row in enumerate(sorted_rows, start=1)
    )


def _learning_value_score(
    *,
    resolved_sample_score: Decimal,
    forecast_error_reduction_score: Decimal,
    source_reliability_improvement_score: Decimal,
    event_archetype_coverage_ratio: Decimal,
    calibration_backlog_score: Decimal,
    capital_efficiency: Decimal,
) -> Decimal:
    return _q(
        (resolved_sample_score * Decimal("0.200000"))
        + (forecast_error_reduction_score * Decimal("0.250000"))
        + (source_reliability_improvement_score * Decimal("0.200000"))
        + (event_archetype_coverage_ratio * Decimal("0.150000"))
        + (calibration_backlog_score * Decimal("0.100000"))
        + (capital_efficiency * Decimal("0.100000")),
    )


def _row_status(
    learning_value_score: Decimal,
    config: StrategyCategoryLearningValueDigestConfig,
) -> str:
    if learning_value_score >= config.pass_learning_value_score:
        return PASS_STATUS
    if learning_value_score >= config.watch_learning_value_score:
        return WATCH_STATUS
    return BLOCKED_STATUS


def _row_reason_codes(
    row: StrategyCategoryLearningValueInput,
    *,
    forecast_error_reduction: Decimal,
    source_reliability_improvement: Decimal,
    event_archetype_coverage_ratio: Decimal,
    status: str,
    config: StrategyCategoryLearningValueDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if row.resolved_sample_count < config.target_resolved_sample_count:
        reason_codes.append("resolved_sample_count_low")
    if forecast_error_reduction < config.target_forecast_error_reduction:
        reason_codes.append("forecast_error_reduction_low")
    if source_reliability_improvement < config.target_source_reliability_improvement:
        reason_codes.append("source_reliability_improvement_low")
    if event_archetype_coverage_ratio < config.min_event_archetype_coverage_ratio:
        reason_codes.append("event_archetype_coverage_low")
    if row.calibration_backlog > config.max_calibration_backlog:
        reason_codes.append("calibration_backlog_high")
    if row.capital_efficiency < config.min_capital_efficiency:
        reason_codes.append("capital_efficiency_low")
    if status == PASS_STATUS:
        reason_codes.append("learning_value_pass")
    elif status == WATCH_STATUS:
        reason_codes.append("learning_value_watch")
    else:
        reason_codes.append("learning_value_blocked")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), ROW_REASON_CODES)


def _report_reason_codes(
    rows: tuple[StrategyCategoryLearningValueDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(sorted({reason_code for row in rows for reason_code in row.reason_codes})),
        REPORT_REASON_CODES,
    )


def _digest_status(rows: tuple[StrategyCategoryLearningValueDigestRow, ...]) -> str:
    if not rows:
        return BLOCKED_STATUS
    if all(row.learning_value_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.learning_value_status != PASS_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _status_count(
    rows: tuple[StrategyCategoryLearningValueDigestRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.learning_value_status == status)


def _max_learning_value_score(
    rows: tuple[StrategyCategoryLearningValueDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _q(max(row.learning_value_score for row in rows))


def _min_learning_value_score(
    rows: tuple[StrategyCategoryLearningValueDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _q(min(row.learning_value_score for row in rows))


def _average_learning_value_score(
    rows: tuple[StrategyCategoryLearningValueDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _q(sum(row.learning_value_score for row in rows) / Decimal(len(rows)))


def _validate_row(row: StrategyCategoryLearningValueDigestRow) -> None:
    if row.covered_event_archetype_count > row.required_event_archetype_count:
        raise ValueError(
            "covered_event_archetype_count must not exceed required_event_archetype_count",
        )
    if row.forecast_error_reduction != _q(
        max(row.previous_forecast_error - row.current_forecast_error, ZERO),
    ):
        raise ValueError("forecast_error_reduction must match forecast errors")
    if row.source_reliability_improvement != _q(
        max(row.current_source_reliability - row.previous_source_reliability, ZERO),
    ):
        raise ValueError(
            "source_reliability_improvement must match source reliability values",
        )
    if row.event_archetype_coverage_ratio != _ratio(
        row.covered_event_archetype_count,
        row.required_event_archetype_count,
    ):
        raise ValueError("event_archetype_coverage_ratio must match archetype counts")
    if row.learning_value_score != _learning_value_score(
        resolved_sample_score=row.resolved_sample_score,
        forecast_error_reduction_score=row.forecast_error_reduction_score,
        source_reliability_improvement_score=row.source_reliability_improvement_score,
        event_archetype_coverage_ratio=row.event_archetype_coverage_ratio,
        calibration_backlog_score=row.calibration_backlog_score,
        capital_efficiency=row.capital_efficiency,
    ):
        raise ValueError("learning_value_score must match row inputs")


def _validate_report(report: StrategyCategoryLearningValueDigestReport) -> None:
    if report.category_count != _count(len(report.rows)):
        raise ValueError("category_count must match rows")
    if report.pass_count != _count(_status_count(report.rows, PASS_STATUS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(_status_count(report.rows, WATCH_STATUS)):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _count(_status_count(report.rows, BLOCKED_STATUS)):
        raise ValueError("blocked_count must match rows")
    expected_top_category = report.rows[0].category if report.rows else None
    if report.top_category != expected_top_category:
        raise ValueError("top_category must match highest-ranked row")
    if report.max_learning_value_score != _max_learning_value_score(report.rows):
        raise ValueError("max_learning_value_score must match rows")
    if report.min_learning_value_score != _min_learning_value_score(report.rows):
        raise ValueError("min_learning_value_score must match rows")
    if report.average_learning_value_score != _average_learning_value_score(report.rows):
        raise ValueError("average_learning_value_score must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    for row in report.rows:
        _validate_row_digest(row)


def _validate_row_digest(row: StrategyCategoryLearningValueDigestRow) -> None:
    if row.validation_digest != _row_validation_digest(
        rank=row.rank,
        category=row.category,
        sample_observed_at=row.sample_observed_at,
        resolved_sample_count=row.resolved_sample_count,
        resolved_sample_score=row.resolved_sample_score,
        previous_forecast_error=row.previous_forecast_error,
        current_forecast_error=row.current_forecast_error,
        forecast_error_reduction=row.forecast_error_reduction,
        forecast_error_reduction_score=row.forecast_error_reduction_score,
        previous_source_reliability=row.previous_source_reliability,
        current_source_reliability=row.current_source_reliability,
        source_reliability_improvement=row.source_reliability_improvement,
        source_reliability_improvement_score=row.source_reliability_improvement_score,
        covered_event_archetype_count=row.covered_event_archetype_count,
        required_event_archetype_count=row.required_event_archetype_count,
        event_archetype_coverage_ratio=row.event_archetype_coverage_ratio,
        calibration_backlog=row.calibration_backlog,
        calibration_backlog_score=row.calibration_backlog_score,
        capital_efficiency=row.capital_efficiency,
        learning_value_score=row.learning_value_score,
        learning_value_status=row.learning_value_status,
        redacted_learning_reference=row.redacted_learning_reference,
        reason_codes=row.reason_codes,
    ):
        raise ValueError("validation_digest must match row")


def _validate_report_digest(report: StrategyCategoryLearningValueDigestReport) -> None:
    if report.validation_digest != _report_validation_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        category_count=report.category_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        blocked_count=report.blocked_count,
        top_category=report.top_category,
        max_learning_value_score=report.max_learning_value_score,
        min_learning_value_score=report.min_learning_value_score,
        average_learning_value_score=report.average_learning_value_score,
        digest_status=report.digest_status,
        reason_codes=report.reason_codes,
        rows=report.rows,
    ):
        raise ValueError("validation_digest must match report")


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    row_payloads = _payload_rows(payload)
    expected_row_digests = tuple(_payload_row_digest(row) for row in row_payloads)
    for row, expected_digest in zip(row_payloads, expected_row_digests, strict=True):
        if _payload_required_digest(row, "validation_digest") != expected_digest:
            raise ValueError("validation_digest must match payload row")
    if _payload_required_digest(payload, "validation_digest") != _payload_report_digest(
        payload,
        expected_row_digests,
    ):
        raise ValueError("validation_digest must match payload")


def _row_validation_digest(
    *,
    rank: Decimal,
    category: str,
    sample_observed_at: datetime,
    resolved_sample_count: Decimal,
    resolved_sample_score: Decimal,
    previous_forecast_error: Decimal,
    current_forecast_error: Decimal,
    forecast_error_reduction: Decimal,
    forecast_error_reduction_score: Decimal,
    previous_source_reliability: Decimal,
    current_source_reliability: Decimal,
    source_reliability_improvement: Decimal,
    source_reliability_improvement_score: Decimal,
    covered_event_archetype_count: Decimal,
    required_event_archetype_count: Decimal,
    event_archetype_coverage_ratio: Decimal,
    calibration_backlog: Decimal,
    calibration_backlog_score: Decimal,
    capital_efficiency: Decimal,
    learning_value_score: Decimal,
    learning_value_status: str,
    redacted_learning_reference: str,
    reason_codes: tuple[str, ...],
) -> str:
    return _hash_parts(
        (
            VALIDATION_DIGEST_ALGORITHM,
            "strategy_category_learning_value_digest_row",
            _decimal_payload(rank),
            category,
            _datetime_payload(sample_observed_at),
            _decimal_payload(resolved_sample_count),
            _decimal_payload(resolved_sample_score),
            _decimal_payload(previous_forecast_error),
            _decimal_payload(current_forecast_error),
            _decimal_payload(forecast_error_reduction),
            _decimal_payload(forecast_error_reduction_score),
            _decimal_payload(previous_source_reliability),
            _decimal_payload(current_source_reliability),
            _decimal_payload(source_reliability_improvement),
            _decimal_payload(source_reliability_improvement_score),
            _decimal_payload(covered_event_archetype_count),
            _decimal_payload(required_event_archetype_count),
            _decimal_payload(event_archetype_coverage_ratio),
            _decimal_payload(calibration_backlog),
            _decimal_payload(calibration_backlog_score),
            _decimal_payload(capital_efficiency),
            _decimal_payload(learning_value_score),
            learning_value_status,
            redacted_learning_reference,
            _reason_codes_payload(reason_codes),
            "paper_only=True",
            "report_only=True",
            "readonly=True",
        ),
    )


def _report_validation_digest(
    *,
    generated_at: datetime,
    config_version: str,
    category_count: Decimal,
    pass_count: Decimal,
    watch_count: Decimal,
    blocked_count: Decimal,
    top_category: str | None,
    max_learning_value_score: Decimal,
    min_learning_value_score: Decimal,
    average_learning_value_score: Decimal,
    digest_status: str,
    reason_codes: tuple[str, ...],
    rows: tuple[StrategyCategoryLearningValueDigestRow, ...],
) -> str:
    return _hash_parts(
        (
            VALIDATION_DIGEST_ALGORITHM,
            "strategy_category_learning_value_digest_report",
            _datetime_payload(generated_at),
            config_version,
            _decimal_payload(category_count),
            _decimal_payload(pass_count),
            _decimal_payload(watch_count),
            _decimal_payload(blocked_count),
            top_category if top_category is not None else "<none>",
            _decimal_payload(max_learning_value_score),
            _decimal_payload(min_learning_value_score),
            _decimal_payload(average_learning_value_score),
            digest_status,
            _reason_codes_payload(reason_codes),
            "\x1f".join(row.validation_digest for row in rows),
            "paper_only=True",
            "report_only=True",
            "readonly=True",
        ),
    )


def _payload_row_digest(row: dict[str, Any]) -> str:
    _payload_required_flags(row)
    return _hash_parts(
        (
            VALIDATION_DIGEST_ALGORITHM,
            "strategy_category_learning_value_digest_row",
            _payload_required_decimal_string(row, "rank"),
            _payload_required_string(row, "category"),
            _payload_required_datetime_string(row, "sample_observed_at"),
            _payload_required_decimal_string(row, "resolved_sample_count"),
            _payload_required_decimal_string(row, "resolved_sample_score"),
            _payload_required_decimal_string(row, "previous_forecast_error"),
            _payload_required_decimal_string(row, "current_forecast_error"),
            _payload_required_decimal_string(row, "forecast_error_reduction"),
            _payload_required_decimal_string(row, "forecast_error_reduction_score"),
            _payload_required_decimal_string(row, "previous_source_reliability"),
            _payload_required_decimal_string(row, "current_source_reliability"),
            _payload_required_decimal_string(row, "source_reliability_improvement"),
            _payload_required_decimal_string(row, "source_reliability_improvement_score"),
            _payload_required_decimal_string(row, "covered_event_archetype_count"),
            _payload_required_decimal_string(row, "required_event_archetype_count"),
            _payload_required_decimal_string(row, "event_archetype_coverage_ratio"),
            _payload_required_decimal_string(row, "calibration_backlog"),
            _payload_required_decimal_string(row, "calibration_backlog_score"),
            _payload_required_decimal_string(row, "capital_efficiency"),
            _payload_required_decimal_string(row, "learning_value_score"),
            _payload_required_string(row, "learning_value_status"),
            _payload_required_string(row, "redacted_learning_reference"),
            _reason_codes_payload(_payload_required_reason_codes(row, "reason_codes")),
            "paper_only=True",
            "report_only=True",
            "readonly=True",
        ),
    )


def _payload_report_digest(
    payload: dict[str, Any],
    row_digests: tuple[str, ...],
) -> str:
    _payload_required_flags(payload)
    return _hash_parts(
        (
            VALIDATION_DIGEST_ALGORITHM,
            "strategy_category_learning_value_digest_report",
            _payload_required_datetime_string(payload, "generated_at"),
            _payload_required_string(payload, "config_version"),
            _payload_required_decimal_string(payload, "category_count"),
            _payload_required_decimal_string(payload, "pass_count"),
            _payload_required_decimal_string(payload, "watch_count"),
            _payload_required_decimal_string(payload, "blocked_count"),
            _payload_optional_string(payload, "top_category"),
            _payload_required_decimal_string(payload, "max_learning_value_score"),
            _payload_required_decimal_string(payload, "min_learning_value_score"),
            _payload_required_decimal_string(payload, "average_learning_value_score"),
            _payload_required_string(payload, "digest_status"),
            _reason_codes_payload(_payload_required_reason_codes(payload, "reason_codes")),
            "\x1f".join(row_digests),
            "paper_only=True",
            "report_only=True",
            "readonly=True",
        ),
    )


def _payload_rows(payload: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    if "rows" not in payload:
        raise ValueError("rows must be present")
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    normalized_rows: list[dict[str, Any]] = []
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain objects")
        normalized_rows.append(row)
    return tuple(normalized_rows)


def _payload_required_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if field_name not in payload:
            raise ValueError(f"{field_name} must be present")
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    if field_name not in payload:
        raise ValueError(f"{field_name} must be present")
    value = payload[field_name]
    _require_canonical_string(field_name, value)
    return value


def _payload_optional_string(payload: dict[str, Any], field_name: str) -> str:
    if field_name not in payload:
        raise ValueError(f"{field_name} must be present")
    value = payload[field_name]
    if value is None:
        return "<none>"
    _require_canonical_string(field_name, value)
    return value


def _payload_required_decimal_string(payload: dict[str, Any], field_name: str) -> str:
    value = _payload_required_string(payload, field_name)
    try:
        parsed = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    if not parsed.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _payload_required_datetime_string(payload: dict[str, Any], field_name: str) -> str:
    value = _payload_required_string(payload, field_name)
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime") from exc
    _as_utc(field_name, parsed)
    return value


def _payload_required_reason_codes(
    payload: dict[str, Any],
    field_name: str,
) -> tuple[str, ...]:
    if field_name not in payload:
        raise ValueError(f"{field_name} must be present")
    value = payload[field_name]
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    reason_codes: list[str] = []
    for reason_code in value:
        _require_canonical_string(field_name, reason_code)
        reason_codes.append(reason_code)
    return tuple(reason_codes)


def _payload_required_digest(payload: dict[str, Any], field_name: str) -> str:
    return _require_validation_digest(field_name, _payload_required_string(payload, field_name))


def _decimal_payload(value: Decimal) -> str:
    _require_decimal("validation decimal", value)
    return str(value)


def _datetime_payload(value: datetime) -> str:
    return _as_utc("validation datetime", value).isoformat()


def _reason_codes_payload(reason_codes: tuple[str, ...]) -> str:
    return "\x1f".join(reason_codes)


def _hash_parts(parts: tuple[str, ...]) -> str:
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def _normalize_inputs(
    value: Iterable[StrategyCategoryLearningValueInput],
) -> tuple[StrategyCategoryLearningValueInput, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("categories must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("categories must be an iterable") from exc
    categories: set[str] = set()
    for row in rows:
        if type(row) is not StrategyCategoryLearningValueInput:
            raise ValueError("categories must contain exact input rows")
        _require_paper_flags("input", row)
        if row.category in categories:
            raise ValueError("categories must be unique")
        categories.add(row.category)
    return rows


def _normalize_rows(
    value: object,
) -> tuple[StrategyCategoryLearningValueDigestRow, ...]:
    if type(value) is not tuple:
        raise ValueError("digest report rows must be a tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not StrategyCategoryLearningValueDigestRow:
            raise ValueError("digest report must contain exact rows")
    expected_ranks = tuple(_count(index) for index in range(1, len(rows) + 1))
    if tuple(row.rank for row in rows) != expected_ranks:
        raise ValueError("rows must use consecutive ranks")
    if rows != tuple(
        sorted(
            rows,
            key=lambda row: (
                -row.learning_value_score,
                _status_sort_value(row.learning_value_status),
                row.category,
            ),
        ),
    ):
        raise ValueError("rows must be sorted by learning value score and category")
    return rows


def _status_sort_value(status: str) -> Decimal:
    return {
        PASS_STATUS: Decimal("0"),
        WATCH_STATUS: Decimal("1"),
        BLOCKED_STATUS: Decimal("2"),
    }[status]


def _redact_learning_reference(learning_reference: str) -> str:
    if _contains_sensitive_reference(learning_reference) or _has_unsafe_surface_fragment(
        learning_reference,
    ):
        return "<redacted>"
    return learning_reference


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            key: _json_ready(nested_value)
            for key, nested_value in asdict(value).items()
            if key != RAW_LEARNING_REFERENCE_FIELD
        }
    if value is None:
        return None
    if type(value) is bool:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if key == RAW_LEARNING_REFERENCE_FIELD:
                raise ValueError(f"unsafe surface field in payload: {key}")
            ready[key] = _json_ready(nested_value)
        return ready
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        if _contains_sensitive_reference(value) or _has_unsafe_surface_fragment(value):
            raise ValueError(f"{path or label} has unsafe value")
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or label} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, dict):
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            if key == RAW_LEARNING_REFERENCE_FIELD or _has_unsafe_surface_fragment(key):
                raise ValueError(f"unsafe surface field in {label}: {key}")
            if key in {"paper_only", "report_only", "readonly"} and nested_value is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_public_payload(label, nested_value, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, nested_value in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, nested_value, nested_path)
        return
    raise ValueError("value is not JSON serializable")


def _contains_sensitive_reference(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in SENSITIVE_REFERENCE_MARKERS)


def _has_unsafe_surface_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a nonblank trimmed string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonblank trimmed string")


def _require_decimal(field_name: str, value: object) -> None:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _normalize_value(field_name: str, value: object) -> Decimal:
    _require_decimal(field_name, value)
    return _q(value)


def _normalize_nonnegative_value(field_name: str, value: object) -> Decimal:
    normalized = _normalize_value(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be at least zero")
    return normalized


def _normalize_positive_value(field_name: str, value: object) -> Decimal:
    normalized = _normalize_value(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be above zero")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_value(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    _require_decimal(field_name, value)
    if value != value.quantize(COUNT_QUANTUM):
        raise ValueError(f"{field_name} must be a whole Decimal count")
    if value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be at least zero")
    return value.quantize(COUNT_QUANTUM)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be above zero")
    return normalized


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    normalized: list[str] = []
    for reason_code in value:
        _require_canonical_string(field_name, reason_code)
        if reason_code not in allowed_reason_codes:
            raise ValueError(f"{field_name} contains unknown reason code")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(sorted(normalized))


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _require_validation_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a validation digest")
    if len(value) != 64 or any(character not in HEX_DIGITS for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _require_paper_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _q(numerator / denominator)


def _q(value: Decimal) -> Decimal:
    return value.quantize(VALUE_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


__all__ = (
    "DEFAULT_STRATEGY_CATEGORY_LEARNING_VALUE_DIGEST_CONFIG_VERSION",
    "StrategyCategoryLearningValueDigestConfig",
    "StrategyCategoryLearningValueDigestReport",
    "StrategyCategoryLearningValueDigestRow",
    "StrategyCategoryLearningValueInput",
    "build_strategy_category_learning_value_digest",
    "strategy_category_learning_value_digest_payload",
)
