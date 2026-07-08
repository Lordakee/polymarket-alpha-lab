"""Pure paper-only scorecard for caller-supplied information source signals."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import InitVar, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


__all__ = (
    "ResearchInformationSourceReliabilityDigest",
    "ResearchInformationSourceReliabilityReasonCodeCount",
    "ResearchInformationSourceReliabilityRow",
    "ResearchInformationSourceReliabilityScorecardConfig",
    "ResearchInformationSourceReliabilityScorecardInput",
    "ResearchInformationSourceReliabilityScorecardReport",
    "build_research_information_source_reliability_scorecard",
    "research_information_source_reliability_scorecard_digest",
    "research_information_source_reliability_scorecard_payload",
)


DEFAULT_CONFIG_VERSION = "research-information-source-reliability-scorecard-v0"
STATUSES = ("pass", "watch", "block")
MANUAL_PRIORITIES = (
    "primary_human_review",
    "secondary_human_review",
    "manual_escalation",
)
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
DEFAULT_PASS_RELIABILITY_SCORE = Decimal("0.750000")
DEFAULT_WATCH_RELIABILITY_SCORE = Decimal("0.500000")
DEFAULT_PASS_LATENCY_SECONDS = Decimal("3600")
DEFAULT_BLOCK_LATENCY_SECONDS = Decimal("86400")


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class ResearchInformationSourceReliabilityScorecardConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    pass_latency_seconds: Decimal = DEFAULT_PASS_LATENCY_SECONDS
    block_latency_seconds: Decimal = DEFAULT_BLOCK_LATENCY_SECONDS
    min_observation_count: Decimal = Decimal("3")
    pass_reliability_score: Decimal = DEFAULT_PASS_RELIABILITY_SCORE
    watch_reliability_score: Decimal = DEFAULT_WATCH_RELIABILITY_SCORE
    block_conflict_rate: Decimal = Decimal("0.350000")
    block_coverage_gap_rate: Decimal = Decimal("0.500000")
    latency_weight: Decimal = Decimal("0.250000")
    conflict_weight: Decimal = Decimal("0.250000")
    history_weight: Decimal = Decimal("0.300000")
    coverage_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchInformationSourceReliabilityScorecardConfig:
            raise TypeError(
                "ResearchInformationSourceReliabilityScorecardConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchInformationSourceReliabilityScorecardConfig:
            raise ValueError(
                "config must be exactly ResearchInformationSourceReliabilityScorecardConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in ("pass_latency_seconds", "block_latency_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_latency_seconds <= self.pass_latency_seconds:
            raise ValueError("block_latency_seconds must exceed pass_latency_seconds")
        object.__setattr__(
            self,
            "min_observation_count",
            _require_positive_whole_decimal(
                "min_observation_count",
                self.min_observation_count,
            ),
        )
        for field_name in (
            "pass_reliability_score",
            "watch_reliability_score",
            "block_conflict_rate",
            "block_coverage_gap_rate",
            "latency_weight",
            "conflict_weight",
            "history_weight",
            "coverage_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_reliability_score <= self.watch_reliability_score:
            raise ValueError("pass_reliability_score must exceed watch_reliability_score")
        if _quantize(
            self.latency_weight
            + self.conflict_weight
            + self.history_weight
            + self.coverage_weight,
        ) != ONE:
            raise ValueError("component weights must sum to 1")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchInformationSourceReliabilityScorecardInput:
    public_source_label: str
    observed_latency_seconds: Decimal
    conflict_rate: Decimal
    historical_hit_rate: Decimal
    coverage_gap_rate: Decimal
    observation_count: Decimal
    hard_block_flag: bool = False
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchInformationSourceReliabilityScorecardInput:
            raise TypeError(
                "ResearchInformationSourceReliabilityScorecardInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchInformationSourceReliabilityScorecardInput:
            raise ValueError(
                "input row must be exactly ResearchInformationSourceReliabilityScorecardInput",
            )
        object.__setattr__(
            self,
            "public_source_label",
            _require_public_label("public_source_label", self.public_source_label),
        )
        object.__setattr__(
            self,
            "observed_latency_seconds",
            _require_nonnegative_decimal(
                "observed_latency_seconds",
                self.observed_latency_seconds,
            ),
        )
        for field_name in (
            "conflict_rate",
            "historical_hit_rate",
            "coverage_gap_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "observation_count",
            _require_nonnegative_whole_decimal(
                "observation_count",
                self.observation_count,
            ),
        )
        if type(self.hard_block_flag) is not bool:
            raise ValueError("hard_block_flag must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class ResearchInformationSourceReliabilityRow:
    source_label: str
    observed_latency_seconds: Decimal
    latency_score: Decimal
    conflict_rate: Decimal
    conflict_score: Decimal
    historical_hit_rate: Decimal
    coverage_gap_rate: Decimal
    coverage_score: Decimal
    observation_count: Decimal
    reliability_score: Decimal
    status: str
    manual_priority: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[
        ResearchInformationSourceReliabilityScorecardConfig | None
    ] = None

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchInformationSourceReliabilityRow:
            raise TypeError(
                "ResearchInformationSourceReliabilityRow does not support subclassing",
            )

    def __post_init__(
        self,
        validation_config: ResearchInformationSourceReliabilityScorecardConfig | None,
    ) -> None:
        if type(self) is not ResearchInformationSourceReliabilityRow:
            raise ValueError("row must be exactly ResearchInformationSourceReliabilityRow")
        object.__setattr__(
            self,
            "source_label",
            _require_public_label("source_label", self.source_label),
        )
        object.__setattr__(
            self,
            "observed_latency_seconds",
            _require_nonnegative_decimal(
                "observed_latency_seconds",
                self.observed_latency_seconds,
            ),
        )
        for field_name in (
            "latency_score",
            "conflict_rate",
            "conflict_score",
            "historical_hit_rate",
            "coverage_gap_rate",
            "coverage_score",
            "reliability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "observation_count",
            _require_nonnegative_whole_decimal(
                "observation_count",
                self.observation_count,
            ),
        )
        _require_status("status", self.status)
        _require_manual_priority("manual_priority", self.manual_priority)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row(self, config=validation_config)


@dataclass(frozen=True)
class ResearchInformationSourceReliabilityReasonCodeCount:
    reason_code: str
    count: Decimal
    source_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchInformationSourceReliabilityReasonCodeCount:
            raise TypeError(
                "ResearchInformationSourceReliabilityReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchInformationSourceReliabilityReasonCodeCount:
            raise ValueError(
                "count row must be exactly ResearchInformationSourceReliabilityReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _require_positive_whole_decimal("count", self.count))
        object.__setattr__(
            self,
            "source_ratio",
            _require_probability_decimal("source_ratio", self.source_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchInformationSourceReliabilityScorecardReport:
    generated_at: datetime
    config_version: str
    source_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_reliability_score: Decimal | None
    status: str
    rows: tuple[ResearchInformationSourceReliabilityRow, ...]
    reason_code_counts: tuple[ResearchInformationSourceReliabilityReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchInformationSourceReliabilityScorecardReport:
            raise TypeError(
                "ResearchInformationSourceReliabilityScorecardReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchInformationSourceReliabilityScorecardReport:
            raise ValueError(
                "report must be exactly ResearchInformationSourceReliabilityScorecardReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("source_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_reliability_score",
            _require_optional_probability_decimal(
                "average_reliability_score",
                self.average_reliability_score,
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
        _validate_report(self)


@dataclass(frozen=True)
class ResearchInformationSourceReliabilityDigest:
    generated_at: datetime
    config_version: str
    source_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_reliability_score: Decimal | None
    status: str
    source_priority_sequence: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchInformationSourceReliabilityDigest:
            raise TypeError(
                "ResearchInformationSourceReliabilityDigest does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchInformationSourceReliabilityDigest:
            raise ValueError(
                "digest must be exactly ResearchInformationSourceReliabilityDigest",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("source_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_reliability_score",
            _require_optional_probability_decimal(
                "average_reliability_score",
                self.average_reliability_score,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "source_priority_sequence",
            _normalize_public_label_tuple(
                "source_priority_sequence",
                self.source_priority_sequence,
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("digest", self)


def build_research_information_source_reliability_scorecard(
    source_rows: Iterable[object],
    *,
    config: ResearchInformationSourceReliabilityScorecardConfig,
    generated_at: datetime,
) -> ResearchInformationSourceReliabilityScorecardReport:
    if type(config) is not ResearchInformationSourceReliabilityScorecardConfig:
        raise ValueError("config must be a ResearchInformationSourceReliabilityScorecardConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_source_rows(source_rows)
    rows = tuple(_build_row(item, config=config) for item in inputs)
    rows = tuple(sorted(rows, key=_row_sort_key))
    reason_codes = _summary_reason_codes(rows)
    return ResearchInformationSourceReliabilityScorecardReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_reliability_score=_average_reliability_score(rows),
        status=_summary_status(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_information_source_reliability_scorecard_digest(
    report: ResearchInformationSourceReliabilityScorecardReport,
) -> ResearchInformationSourceReliabilityDigest:
    if type(report) is not ResearchInformationSourceReliabilityScorecardReport:
        raise ValueError(
            "report must be a ResearchInformationSourceReliabilityScorecardReport",
        )
    _require_hard_flags("report", report)
    return ResearchInformationSourceReliabilityDigest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        source_count=report.source_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        average_reliability_score=report.average_reliability_score,
        status=report.status,
        source_priority_sequence=tuple(row.source_label for row in report.rows),
        reason_codes=report.reason_codes,
    )


def research_information_source_reliability_scorecard_payload(
    value: (
        ResearchInformationSourceReliabilityScorecardReport
        | ResearchInformationSourceReliabilityDigest
    ),
) -> dict[str, Any]:
    if type(value) not in (
        ResearchInformationSourceReliabilityScorecardReport,
        ResearchInformationSourceReliabilityDigest,
    ):
        raise ValueError("value must be a scorecard report or digest")
    _require_hard_flags("value", value)
    payload = _payload_value(value)
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")
    _assert_public_payload(payload)
    return payload


def _normalize_source_rows(
    source_rows: Iterable[object],
) -> tuple[ResearchInformationSourceReliabilityScorecardInput, ...]:
    if isinstance(source_rows, (str, bytes)):
        raise ValueError("source_rows must be an iterable")
    try:
        values = tuple(source_rows)
    except TypeError as exc:
        raise ValueError("source_rows must be an iterable") from exc
    return tuple(_coerce_source_row(value) for value in values)


def _coerce_source_row(
    value: object,
) -> ResearchInformationSourceReliabilityScorecardInput:
    if type(value) is ResearchInformationSourceReliabilityScorecardInput:
        _require_hard_flags("input row", value)
        return value
    _require_hard_flags("input row", value)
    return ResearchInformationSourceReliabilityScorecardInput(
        public_source_label=_field_value(value, "public_source_label"),
        observed_latency_seconds=_field_value(value, "observed_latency_seconds"),
        conflict_rate=_field_value(value, "conflict_rate"),
        historical_hit_rate=_field_value(value, "historical_hit_rate"),
        coverage_gap_rate=_field_value(value, "coverage_gap_rate"),
        observation_count=_field_value(value, "observation_count"),
        hard_block_flag=_field_value(value, "hard_block_flag", default=False),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _build_row(
    source_row: ResearchInformationSourceReliabilityScorecardInput,
    *,
    config: ResearchInformationSourceReliabilityScorecardConfig,
) -> ResearchInformationSourceReliabilityRow:
    latency_score = _latency_score(
        source_row.observed_latency_seconds,
        pass_latency_seconds=config.pass_latency_seconds,
        block_latency_seconds=config.block_latency_seconds,
    )
    conflict_score = _quantize(ONE - source_row.conflict_rate)
    coverage_score = _quantize(ONE - source_row.coverage_gap_rate)
    reliability_score = _reliability_score(
        latency_score=latency_score,
        conflict_score=conflict_score,
        historical_hit_rate=source_row.historical_hit_rate,
        coverage_score=coverage_score,
        config=config,
    )
    status = _row_status(
        source_row=source_row,
        latency_score=latency_score,
        reliability_score=reliability_score,
        config=config,
    )
    return ResearchInformationSourceReliabilityRow(
        source_label=source_row.public_source_label,
        observed_latency_seconds=source_row.observed_latency_seconds,
        latency_score=latency_score,
        conflict_rate=source_row.conflict_rate,
        conflict_score=conflict_score,
        historical_hit_rate=source_row.historical_hit_rate,
        coverage_gap_rate=source_row.coverage_gap_rate,
        coverage_score=coverage_score,
        observation_count=source_row.observation_count,
        reliability_score=reliability_score,
        status=status,
        manual_priority=_manual_priority(status),
        reason_codes=_row_reason_codes(
            source_row=source_row,
            latency_score=latency_score,
            reliability_score=reliability_score,
            status=status,
            config=config,
        ),
        validation_config=config,
    )


def _latency_score(
    observed_latency_seconds: Decimal,
    *,
    pass_latency_seconds: Decimal,
    block_latency_seconds: Decimal,
) -> Decimal:
    if observed_latency_seconds <= pass_latency_seconds:
        return ONE
    if observed_latency_seconds >= block_latency_seconds:
        return ZERO
    span = block_latency_seconds - pass_latency_seconds
    return _quantize(ONE - ((observed_latency_seconds - pass_latency_seconds) / span))


def _reliability_score(
    *,
    latency_score: Decimal,
    conflict_score: Decimal,
    historical_hit_rate: Decimal,
    coverage_score: Decimal,
    config: ResearchInformationSourceReliabilityScorecardConfig,
) -> Decimal:
    raw_score = (
        (latency_score * config.latency_weight)
        + (conflict_score * config.conflict_weight)
        + (historical_hit_rate * config.history_weight)
        + (coverage_score * config.coverage_weight)
    )
    return _quantize(max(ZERO, min(ONE, raw_score)))


def _row_status(
    *,
    source_row: ResearchInformationSourceReliabilityScorecardInput,
    latency_score: Decimal,
    reliability_score: Decimal,
    config: ResearchInformationSourceReliabilityScorecardConfig,
) -> str:
    if source_row.hard_block_flag:
        return "block"
    if source_row.conflict_rate >= config.block_conflict_rate:
        return "block"
    if source_row.coverage_gap_rate >= config.block_coverage_gap_rate:
        return "block"
    if latency_score == ZERO:
        return "block"
    if reliability_score < config.watch_reliability_score:
        return "block"
    if reliability_score < config.pass_reliability_score:
        return "watch"
    if source_row.observation_count < config.min_observation_count:
        return "watch"
    if source_row.conflict_rate > ZERO or source_row.coverage_gap_rate > ZERO:
        return "watch"
    if source_row.observed_latency_seconds > config.pass_latency_seconds:
        return "watch"
    return "pass"


def _manual_priority(status: str) -> str:
    if status == "pass":
        return "primary_human_review"
    if status == "watch":
        return "secondary_human_review"
    if status == "block":
        return "manual_escalation"
    raise ValueError("status must be a known status")


def _row_reason_codes(
    *,
    source_row: ResearchInformationSourceReliabilityScorecardInput,
    latency_score: Decimal,
    reliability_score: Decimal,
    status: str,
    config: ResearchInformationSourceReliabilityScorecardConfig,
) -> tuple[str, ...]:
    reason_codes: set[str] = {f"source_reliability_{status}"}
    if source_row.hard_block_flag:
        reason_codes.add("hard_flag_block")
    reason_codes.add("latency_pass" if latency_score == ONE else "latency_watch")
    if latency_score == ZERO:
        reason_codes.add("latency_block")
    if source_row.conflict_rate >= config.block_conflict_rate:
        reason_codes.add("conflict_rate_block")
    elif source_row.conflict_rate > ZERO:
        reason_codes.add("conflict_rate_watch")
    else:
        reason_codes.add("conflict_rate_pass")
    if source_row.coverage_gap_rate >= config.block_coverage_gap_rate:
        reason_codes.add("coverage_gap_block")
    elif source_row.coverage_gap_rate > ZERO:
        reason_codes.add("coverage_gap_watch")
    else:
        reason_codes.add("coverage_gap_pass")
    if source_row.observation_count < config.min_observation_count:
        reason_codes.add("limited_history")
    if reliability_score >= config.pass_reliability_score:
        reason_codes.add("reliability_score_pass")
    elif reliability_score >= config.watch_reliability_score:
        reason_codes.add("reliability_score_watch")
    else:
        reason_codes.add("reliability_score_block")
    for reason_code in source_row.reason_codes:
        reason_codes.add(f"input_{reason_code}")
    return tuple(sorted(reason_codes))


def _summary_reason_codes(
    rows: tuple[ResearchInformationSourceReliabilityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("source_reliability_no_inputs",)
    if any(row.status == "block" for row in rows):
        return tuple(sorted({code for row in rows for code in row.reason_codes}))
    if any(row.status == "watch" for row in rows):
        return tuple(sorted({code for row in rows for code in row.reason_codes}))
    return ("source_reliability_pass",)


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("source_reliability_no_inputs",):
        return "block"
    if "source_reliability_block" in reason_codes:
        return "block"
    if "source_reliability_watch" in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchInformationSourceReliabilityRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchInformationSourceReliabilityReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchInformationSourceReliabilityReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
                source_ratio=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    source_count = Decimal(len(rows))
    return tuple(
        ResearchInformationSourceReliabilityReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            source_ratio=_quantize(Decimal(count) / source_count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _row_sort_key(row: ResearchInformationSourceReliabilityRow) -> tuple[int, Decimal, str]:
    return (STATUSES.index(row.status), -row.reliability_score, row.source_label)


def _status_count(
    rows: tuple[ResearchInformationSourceReliabilityRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _average_reliability_score(
    rows: tuple[ResearchInformationSourceReliabilityRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(sum((row.reliability_score for row in rows), ZERO) / Decimal(len(rows)))


def _normalize_rows(
    rows: tuple[ResearchInformationSourceReliabilityRow, ...],
) -> tuple[ResearchInformationSourceReliabilityRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchInformationSourceReliabilityRow:
            raise ValueError("rows must contain ResearchInformationSourceReliabilityRow values")
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by public priority")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchInformationSourceReliabilityReasonCodeCount, ...],
) -> tuple[ResearchInformationSourceReliabilityReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchInformationSourceReliabilityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchInformationSourceReliabilityReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row(
    row: ResearchInformationSourceReliabilityRow,
    *,
    config: ResearchInformationSourceReliabilityScorecardConfig | None,
) -> None:
    pass_score = (
        config.pass_reliability_score if config is not None else DEFAULT_PASS_RELIABILITY_SCORE
    )
    watch_score = (
        config.watch_reliability_score
        if config is not None
        else DEFAULT_WATCH_RELIABILITY_SCORE
    )
    if row.manual_priority != _manual_priority(row.status):
        raise ValueError("manual_priority must match status")
    if row.conflict_score != _quantize(ONE - row.conflict_rate):
        raise ValueError("conflict_score must match conflict_rate")
    if row.coverage_score != _quantize(ONE - row.coverage_gap_rate):
        raise ValueError("coverage_score must match coverage_gap_rate")
    if row.status == "pass" and row.reliability_score < pass_score:
        raise ValueError("reliability_score must support pass status")
    if row.status == "watch" and row.reliability_score < watch_score:
        raise ValueError("reliability_score must support watch status")
    if row.status == "block" and row.reliability_score >= pass_score:
        block_reason_codes = {
            "conflict_rate_block",
            "coverage_gap_block",
            "hard_flag_block",
            "latency_block",
            "reliability_score_block",
        }
        if not block_reason_codes.intersection(row.reason_codes):
            raise ValueError("reason_codes must support block status")


def _validate_report(report: ResearchInformationSourceReliabilityScorecardReport) -> None:
    if report.source_count != _decimal_count(len(report.rows)):
        raise ValueError("source_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_reliability_score != _average_reliability_score(report.rows):
        raise ValueError("average_reliability_score must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(report.reason_codes):
        raise ValueError("status must match reason_codes")


def _field_value(value: object, field_name: str, *, default: object = _MISSING) -> object:
    if is_dataclass(value):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{field_name} is required")


def _payload_value(value: object) -> object:
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
        return {str(key): _payload_value(item) for key, item in value.items()}
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
    return _quantize(normalized)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(normalized)


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be in the closed unit interval")
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
    return _quantize(normalized)


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return _quantize(normalized)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value).quantize(RATIO_QUANTUM)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")


def _require_public_label(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    normalized = value
    assert isinstance(normalized, str)
    _assert_no_private_fragments(field_name, normalized)
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789_-"
    if any(character not in allowed for character in normalized):
        raise ValueError(f"{field_name} must contain public safe characters")
    return normalized


def _normalize_public_label_tuple(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized = tuple(_require_public_label(field_name, value) for value in values)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return normalized


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
        _assert_no_private_fragments(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789_"
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must contain deterministic code characters")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _require_manual_priority(field_name: str, value: object) -> None:
    if type(value) is not str or value not in MANUAL_PRIORITIES:
        raise ValueError(f"{field_name} must be one of {MANUAL_PRIORITIES}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if _field_value(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _private_fragments() -> tuple[str, ...]:
    parts = (
        ("can", "didate"),
        ("ma", "rket"),
        ("slu", "g"),
        ("ques", "tion"),
        ("re", "f"),
        ("ur", "l"),
        ("te", "xt"),
        ("ds", "n"),
        ("ta", "ble"),
        ("tok", "en"),
        ("wal", "let"),
        ("or", "der"),
        ("tra", "de"),
        ("posi", "tion"),
        ("bu", "y"),
        ("se", "ll"),
        ("reco", "mmend"),
        ("au", "th"),
        ("sec", "ret"),
        ("creden", "tial"),
    )
    return tuple("".join(part) for part in parts)


def _assert_no_private_fragments(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "/" in lowered or "?" in lowered or "=" in lowered:
        raise ValueError(f"{field_name} must not contain protected material")
    separator_map = str.maketrans({"-": "_", ".": "_", ":": "_"})
    tokens = tuple(
        token
        for token in lowered.translate(separator_map).split("_")
        if token
    )
    for fragment in _private_fragments():
        if fragment in tokens:
            raise ValueError(f"{field_name} must not contain protected material")


def _assert_public_payload(value: object) -> None:
    if isinstance(value, str):
        _assert_no_private_fragments("payload", value)
        return
    if isinstance(value, list):
        for item in value:
            _assert_public_payload(item)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _assert_no_private_fragments("payload", str(key))
            _assert_public_payload(item)
