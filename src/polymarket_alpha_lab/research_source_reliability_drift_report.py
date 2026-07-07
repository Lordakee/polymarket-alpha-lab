"""Pure report-only evaluation of source reliability drift over time."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


__all__ = (
    "ResearchSourceReliabilityDriftConfig",
    "ResearchSourceReliabilityDriftReasonCodeCount",
    "ResearchSourceReliabilityDriftReport",
    "ResearchSourceReliabilityDriftRow",
    "ResearchSourceReliabilityHistoryPoint",
    "build_research_source_reliability_drift_report",
    "research_source_reliability_drift_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-source-reliability-drift-report-v0"
STATUSES = ("pass", "watch", "blocked")
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
NO_HISTORY_REASON_CODE = "no_reliability_history"
PASS_REASON_CODE = "reliability_drift_pass"
WATCH_REASON_CODE = "reliability_drift_watch"
BLOCKED_REASON_CODE = "reliability_drift_blocked"
SAFE_IDENTIFIER_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789-_")
SAFE_REASON_CODE_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_")
UNSAFE_KEY_FRAGMENTS = (
    "source_url",
    "source_text",
    "source_ref",
    "source_table",
    "dsn",
    "token",
)
UNSAFE_TEXT_FRAGMENTS = (
    "http://",
    "https://",
    "://",
    "dsn=",
    "token=",
    "bearer ",
)


@dataclass(frozen=True)
class ResearchSourceReliabilityDriftConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    min_history_points: Decimal = Decimal("3")
    quality_drop_watch: Decimal = Decimal("0.100000")
    quality_drop_block: Decimal = Decimal("0.250000")
    failure_rate_increase_watch: Decimal = Decimal("0.050000")
    failure_rate_increase_block: Decimal = Decimal("0.150000")
    stale_age_watch_seconds: Decimal = Decimal("86400")
    stale_age_block_seconds: Decimal = Decimal("259200")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceReliabilityDriftConfig:
            raise TypeError(
                "ResearchSourceReliabilityDriftConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceReliabilityDriftConfig:
            raise ValueError("config must be exactly ResearchSourceReliabilityDriftConfig")
        _require_public_identifier("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_history_points",
            _require_positive_whole_decimal("min_history_points", self.min_history_points),
        )
        for field_name in (
            "quality_drop_watch",
            "quality_drop_block",
            "failure_rate_increase_watch",
            "failure_rate_increase_block",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("stale_age_watch_seconds", "stale_age_block_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.quality_drop_watch >= self.quality_drop_block:
            raise ValueError("quality_drop_watch must be less than quality_drop_block")
        if self.failure_rate_increase_watch >= self.failure_rate_increase_block:
            raise ValueError(
                "failure_rate_increase_watch must be less than "
                "failure_rate_increase_block",
            )
        if self.stale_age_watch_seconds >= self.stale_age_block_seconds:
            raise ValueError(
                "stale_age_watch_seconds must be less than stale_age_block_seconds",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceReliabilityHistoryPoint:
    source_family: str
    observed_at: datetime
    quality_score: Decimal
    failure_rate: Decimal
    stale_age_seconds: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceReliabilityHistoryPoint:
            raise TypeError(
                "ResearchSourceReliabilityHistoryPoint does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceReliabilityHistoryPoint:
            raise ValueError(
                "history point must be exactly ResearchSourceReliabilityHistoryPoint",
            )
        _require_public_identifier("source_family", self.source_family)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("quality_score", "failure_rate"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "stale_age_seconds",
            _require_nonnegative_decimal("stale_age_seconds", self.stale_age_seconds),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("history point", self)
        _reject_unsafe_public_payload("history point", self)


@dataclass(frozen=True)
class ResearchSourceReliabilityDriftRow:
    source_family: str
    observation_count: Decimal
    first_observed_at: datetime
    latest_observed_at: datetime
    historical_quality_score: Decimal
    latest_quality_score: Decimal
    quality_score_drop: Decimal
    historical_failure_rate: Decimal
    latest_failure_rate: Decimal
    failure_rate_increase: Decimal
    latest_stale_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    explanations: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceReliabilityDriftRow:
            raise TypeError(
                "ResearchSourceReliabilityDriftRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceReliabilityDriftRow:
            raise ValueError("row must be exactly ResearchSourceReliabilityDriftRow")
        _require_public_identifier("source_family", self.source_family)
        object.__setattr__(
            self,
            "observation_count",
            _require_positive_whole_decimal("observation_count", self.observation_count),
        )
        object.__setattr__(
            self,
            "first_observed_at",
            _as_utc("first_observed_at", self.first_observed_at),
        )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        for field_name in (
            "historical_quality_score",
            "latest_quality_score",
            "quality_score_drop",
            "historical_failure_rate",
            "latest_failure_rate",
            "failure_rate_increase",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_stale_age_seconds",
            _require_nonnegative_decimal(
                "latest_stale_age_seconds",
                self.latest_stale_age_seconds,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        object.__setattr__(
            self,
            "explanations",
            _normalize_public_text_tuple("explanations", self.explanations),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourceReliabilityDriftReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceReliabilityDriftReasonCodeCount:
            raise TypeError(
                "ResearchSourceReliabilityDriftReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceReliabilityDriftReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchSourceReliabilityDriftReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason code count", self)
        _reject_unsafe_public_payload("reason code count", self)


@dataclass(frozen=True)
class ResearchSourceReliabilityDriftReport:
    generated_at: datetime
    config_version: str
    source_family_count: Decimal
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_latest_quality_score: Decimal | None
    average_quality_score_drop: Decimal | None
    average_failure_rate_increase: Decimal | None
    max_latest_stale_age_seconds: Decimal | None
    status: str
    rows: tuple[ResearchSourceReliabilityDriftRow, ...]
    reason_code_counts: tuple[ResearchSourceReliabilityDriftReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    explanations: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceReliabilityDriftReport:
            raise TypeError(
                "ResearchSourceReliabilityDriftReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceReliabilityDriftReport:
            raise ValueError("report must be exactly ResearchSourceReliabilityDriftReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        for field_name in (
            "source_family_count",
            "observation_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_latest_quality_score",
            "average_quality_score_drop",
            "average_failure_rate_increase",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_optional_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_latest_stale_age_seconds",
            _require_optional_nonnegative_decimal(
                "max_latest_stale_age_seconds",
                self.max_latest_stale_age_seconds,
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
        object.__setattr__(
            self,
            "explanations",
            _normalize_public_text_tuple("explanations", self.explanations),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        _reject_unsafe_public_payload("report", self)


def build_research_source_reliability_drift_report(
    history_points: Iterable[object],
    *,
    config: ResearchSourceReliabilityDriftConfig,
    generated_at: datetime,
) -> ResearchSourceReliabilityDriftReport:
    if type(config) is not ResearchSourceReliabilityDriftConfig:
        raise ValueError("config must be a ResearchSourceReliabilityDriftConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    history_items = _normalize_history_points(history_points)
    for item in history_items:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")

    grouped: dict[str, list[ResearchSourceReliabilityHistoryPoint]] = {}
    for item in history_items:
        grouped.setdefault(item.source_family, []).append(item)

    rows = tuple(
        _drift_row_from_history(
            source_family=source_family,
            history_points=tuple(grouped[source_family]),
            config=config,
        )
        for source_family in sorted(grouped)
    )
    reason_codes = _summary_reason_codes(rows)

    return ResearchSourceReliabilityDriftReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_family_count=_decimal_count(len(rows)),
        observation_count=sum((row.observation_count for row in rows), ZERO),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        blocked_count=_decimal_count(_status_count(rows, "blocked")),
        average_latest_quality_score=_average_row_decimal(
            rows,
            "latest_quality_score",
        ),
        average_quality_score_drop=_average_row_decimal(rows, "quality_score_drop"),
        average_failure_rate_increase=_average_row_decimal(
            rows,
            "failure_rate_increase",
        ),
        max_latest_stale_age_seconds=_max_latest_stale_age_seconds(rows),
        status=_summary_status(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
        explanations=_summary_explanations(rows, reason_codes),
    )


def research_source_reliability_drift_report_payload(
    report: ResearchSourceReliabilityDriftReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceReliabilityDriftReport:
        raise ValueError("report must be a ResearchSourceReliabilityDriftReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("report payload", payload, allow_json_containers=True)
    return payload


def _drift_row_from_history(
    *,
    source_family: str,
    history_points: tuple[ResearchSourceReliabilityHistoryPoint, ...],
    config: ResearchSourceReliabilityDriftConfig,
) -> ResearchSourceReliabilityDriftRow:
    sorted_points = tuple(
        sorted(
            history_points,
            key=lambda item: (
                item.observed_at,
                item.quality_score,
                item.failure_rate,
                item.stale_age_seconds,
            ),
        ),
    )
    latest = sorted_points[-1]
    prior_points = sorted_points[:-1]
    if prior_points:
        historical_quality_score = _average_decimal(
            tuple(item.quality_score for item in prior_points),
        )
        historical_failure_rate = _average_decimal(
            tuple(item.failure_rate for item in prior_points),
        )
    else:
        historical_quality_score = latest.quality_score
        historical_failure_rate = latest.failure_rate

    quality_score_drop = _positive_delta(
        historical_quality_score,
        latest.quality_score,
    )
    failure_rate_increase = _positive_delta(
        latest.failure_rate,
        historical_failure_rate,
    )
    status = _row_status(
        observation_count=_decimal_count(len(sorted_points)),
        quality_score_drop=quality_score_drop,
        failure_rate_increase=failure_rate_increase,
        latest_stale_age_seconds=latest.stale_age_seconds,
        config=config,
    )
    reason_codes = _row_reason_codes(
        status=status,
        observation_count=_decimal_count(len(sorted_points)),
        quality_score_drop=quality_score_drop,
        failure_rate_increase=failure_rate_increase,
        latest_stale_age_seconds=latest.stale_age_seconds,
        input_reason_codes=tuple(
            reason_code for item in sorted_points for reason_code in item.reason_codes
        ),
        config=config,
    )

    return ResearchSourceReliabilityDriftRow(
        source_family=source_family,
        observation_count=_decimal_count(len(sorted_points)),
        first_observed_at=sorted_points[0].observed_at,
        latest_observed_at=latest.observed_at,
        historical_quality_score=historical_quality_score,
        latest_quality_score=latest.quality_score,
        quality_score_drop=quality_score_drop,
        historical_failure_rate=historical_failure_rate,
        latest_failure_rate=latest.failure_rate,
        failure_rate_increase=failure_rate_increase,
        latest_stale_age_seconds=latest.stale_age_seconds,
        status=status,
        reason_codes=reason_codes,
        explanations=_row_explanations(
            status=status,
            quality_score_drop=quality_score_drop,
            failure_rate_increase=failure_rate_increase,
            latest_stale_age_seconds=latest.stale_age_seconds,
            reason_codes=reason_codes,
        ),
    )


def _normalize_history_points(
    history_points: Iterable[object],
) -> tuple[ResearchSourceReliabilityHistoryPoint, ...]:
    if isinstance(history_points, (str, bytes)):
        raise ValueError("history_points must be an iterable")
    try:
        values = tuple(history_points)
    except TypeError as exc:
        raise ValueError("history_points must be an iterable") from exc
    normalized: list[ResearchSourceReliabilityHistoryPoint] = []
    for value in values:
        if type(value) is not ResearchSourceReliabilityHistoryPoint:
            raise ValueError(
                "history_points must contain ResearchSourceReliabilityHistoryPoint "
                "items",
            )
        normalized.append(value)
    return tuple(normalized)


def _row_status(
    *,
    observation_count: Decimal,
    quality_score_drop: Decimal,
    failure_rate_increase: Decimal,
    latest_stale_age_seconds: Decimal,
    config: ResearchSourceReliabilityDriftConfig,
) -> str:
    if observation_count < config.min_history_points:
        return "blocked"
    if (
        quality_score_drop >= config.quality_drop_block
        or failure_rate_increase >= config.failure_rate_increase_block
        or latest_stale_age_seconds >= config.stale_age_block_seconds
    ):
        return "blocked"
    if (
        quality_score_drop >= config.quality_drop_watch
        or failure_rate_increase >= config.failure_rate_increase_watch
        or latest_stale_age_seconds >= config.stale_age_watch_seconds
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    observation_count: Decimal,
    quality_score_drop: Decimal,
    failure_rate_increase: Decimal,
    latest_stale_age_seconds: Decimal,
    input_reason_codes: tuple[str, ...],
    config: ResearchSourceReliabilityDriftConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if observation_count < config.min_history_points:
        codes.append("insufficient_reliability_history")
    if quality_score_drop >= config.quality_drop_block:
        codes.append("quality_score_drop_block")
    elif quality_score_drop >= config.quality_drop_watch:
        codes.append("quality_score_drop_watch")
    if failure_rate_increase >= config.failure_rate_increase_block:
        codes.append("failure_rate_increase_block")
    elif failure_rate_increase >= config.failure_rate_increase_watch:
        codes.append("failure_rate_increase_watch")
    if latest_stale_age_seconds >= config.stale_age_block_seconds:
        codes.append("stale_age_block")
    elif latest_stale_age_seconds >= config.stale_age_watch_seconds:
        codes.append("stale_age_watch")
    codes.extend(f"input_{reason_code}" for reason_code in input_reason_codes)
    if status == "pass":
        codes.append(PASS_REASON_CODE)
    elif status == "watch":
        codes.append(WATCH_REASON_CODE)
    else:
        codes.append(BLOCKED_REASON_CODE)
    return _normalize_reason_codes("reason_codes", tuple(codes), allow_empty=False)


def _row_explanations(
    *,
    status: str,
    quality_score_drop: Decimal,
    failure_rate_increase: Decimal,
    latest_stale_age_seconds: Decimal,
    reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if status == "pass":
        return ("Reliability drift is within configured bounds.",)
    explanations: list[str] = []
    if "insufficient_reliability_history" in reason_codes:
        explanations.append("Reliability history is below the configured minimum.")
    if "quality_score_drop_block" in reason_codes or "quality_score_drop_watch" in reason_codes:
        explanations.append(f"Quality score dropped by {quality_score_drop}.")
    if (
        "failure_rate_increase_block" in reason_codes
        or "failure_rate_increase_watch" in reason_codes
    ):
        explanations.append(f"Failure rate increased by {failure_rate_increase}.")
    if "stale_age_block" in reason_codes or "stale_age_watch" in reason_codes:
        explanations.append(f"Latest observation age is {latest_stale_age_seconds} seconds.")
    if not explanations:
        explanations.append("Reliability drift requires review.")
    return tuple(explanations)


def _summary_reason_codes(
    rows: tuple[ResearchSourceReliabilityDriftRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_HISTORY_REASON_CODE,)
    return tuple(sorted({reason_code for row in rows for reason_code in row.reason_codes}))


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if NO_HISTORY_REASON_CODE in reason_codes:
        return "blocked"
    if any(
        reason_code.endswith("_block")
        or reason_code.endswith("_blocked")
        or reason_code == "insufficient_reliability_history"
        for reason_code in reason_codes
    ):
        return "blocked"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _summary_explanations(
    rows: tuple[ResearchSourceReliabilityDriftRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("No reliability history was supplied.",)
    status = _summary_status(reason_codes)
    if status == "blocked":
        return ("At least one source family has blocked reliability drift.",)
    if status == "watch":
        return ("At least one source family needs reliability drift review.",)
    return ("All source families are within reliability drift bounds.",)


def _reason_code_counts(
    rows: tuple[ResearchSourceReliabilityDriftRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchSourceReliabilityDriftReasonCodeCount, ...]:
    if not rows:
        counter = Counter({NO_HISTORY_REASON_CODE: 1})
    else:
        counter = Counter(reason_code for row in rows for reason_code in row.reason_codes)
    return tuple(
        ResearchSourceReliabilityDriftReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counter[reason_code]),
        )
        for reason_code in reason_codes
    )


def _status_count(
    rows: tuple[ResearchSourceReliabilityDriftRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _average_row_decimal(
    rows: tuple[ResearchSourceReliabilityDriftRow, ...],
    field_name: str,
) -> Decimal | None:
    if not rows:
        return None
    return _average_decimal(tuple(getattr(row, field_name) for row in rows))


def _max_latest_stale_age_seconds(
    rows: tuple[ResearchSourceReliabilityDriftRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return max(row.latest_stale_age_seconds for row in rows)


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("values must be nonempty")
    return _quantize(sum(values, ZERO) / _decimal_count(len(values)))


def _positive_delta(left: Decimal, right: Decimal) -> Decimal:
    delta = left - right
    if delta < ZERO:
        delta = ZERO
    return _quantize(delta)


def _validate_row_consistency(row: ResearchSourceReliabilityDriftRow) -> None:
    if row.latest_observed_at < row.first_observed_at:
        raise ValueError("latest_observed_at must be after first_observed_at")
    if row.quality_score_drop != _positive_delta(
        row.historical_quality_score,
        row.latest_quality_score,
    ):
        raise ValueError("quality_score_drop must match quality scores")
    if row.failure_rate_increase != _positive_delta(
        row.latest_failure_rate,
        row.historical_failure_rate,
    ):
        raise ValueError("failure_rate_increase must match failure rates")


def _validate_report_consistency(report: ResearchSourceReliabilityDriftReport) -> None:
    if report.source_family_count != _decimal_count(len(report.rows)):
        raise ValueError("source_family_count must match rows")
    if report.observation_count != sum((row.observation_count for row in report.rows), ZERO):
        raise ValueError("observation_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _decimal_count(_status_count(report.rows, "blocked")):
        raise ValueError("blocked_count must match rows")
    if report.average_latest_quality_score != _average_row_decimal(
        report.rows,
        "latest_quality_score",
    ):
        raise ValueError("average_latest_quality_score must match rows")
    if report.average_quality_score_drop != _average_row_decimal(
        report.rows,
        "quality_score_drop",
    ):
        raise ValueError("average_quality_score_drop must match rows")
    if report.average_failure_rate_increase != _average_row_decimal(
        report.rows,
        "failure_rate_increase",
    ):
        raise ValueError("average_failure_rate_increase must match rows")
    if report.max_latest_stale_age_seconds != _max_latest_stale_age_seconds(report.rows):
        raise ValueError("max_latest_stale_age_seconds must match rows")
    expected_reason_codes = _summary_reason_codes(report.rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")
    if report.status != _summary_status(report.reason_codes):
        raise ValueError("status must match reason_codes")
    if report.explanations != _summary_explanations(report.rows, report.reason_codes):
        raise ValueError("explanations must match rows")


def _normalize_rows(values: object) -> tuple[ResearchSourceReliabilityDriftRow, ...]:
    if type(values) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized: list[ResearchSourceReliabilityDriftRow] = []
    for value in values:
        if type(value) is not ResearchSourceReliabilityDriftRow:
            raise ValueError("rows must contain ResearchSourceReliabilityDriftRow items")
        normalized.append(value)
    return tuple(normalized)


def _normalize_reason_code_counts(
    values: object,
) -> tuple[ResearchSourceReliabilityDriftReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized: list[ResearchSourceReliabilityDriftReasonCodeCount] = []
    for value in values:
        if type(value) is not ResearchSourceReliabilityDriftReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceReliabilityDriftReasonCodeCount items",
            )
        normalized.append(value)
    return tuple(normalized)


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


def _normalize_public_text_tuple(field_name: str, values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        normalized.append(_require_public_text(field_name, value))
    if not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(normalized)


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty public identifier")
    if any(character not in SAFE_IDENTIFIER_CHARS for character in value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_text(field_name, value)


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must contain public reason codes")
    if any(character not in SAFE_REASON_CODE_CHARS for character in value):
        raise ValueError(f"{field_name} must contain public reason codes")
    _reject_unsafe_text(field_name, value)


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must contain public text")
    _reject_unsafe_text(field_name, value)
    return value


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


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


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


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        field_value = getattr(value, field_name, None)
        if type(field_value) is not bool or field_value is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _payload_value(value: object) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {_payload_value(key): _payload_value(item) for key, item in value.items()}
    return value


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_key(label, field.name)
            _reject_unsafe_public_payload(
                f"{label}.{field.name}",
                getattr(value, field.name),
                allow_json_containers=True,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{label} must not contain mappings")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} keys must be strings")
            _reject_unsafe_key(label, key)
            _reject_unsafe_public_payload(
                f"{label}.{key}",
                item,
                allow_json_containers=True,
            )
        return
    if isinstance(value, tuple | list):
        if not allow_json_containers:
            raise ValueError(f"{label} must not contain containers")
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=True,
            )
        return
    if isinstance(value, str):
        _reject_unsafe_text(label, value)


def _reject_unsafe_key(label: str, key: str) -> None:
    lowered = key.lower()
    if any(fragment in lowered for fragment in UNSAFE_KEY_FRAGMENTS):
        raise ValueError(f"{label} contains unsafe public payload key")


def _reject_unsafe_text(label: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{label} contains unsafe public payload text")
    if any(fragment in lowered for fragment in UNSAFE_KEY_FRAGMENTS):
        raise ValueError(f"{label} contains unsafe public payload text")
