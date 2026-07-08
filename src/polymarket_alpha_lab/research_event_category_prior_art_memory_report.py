"""Pure report-only prior-art memory summary by event category."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any


DEFAULT_RESEARCH_EVENT_CATEGORY_PRIOR_ART_MEMORY_CONFIG_VERSION = (
    "research-event-category-prior-art-memory-report-v0"
)

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"
STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCK_STATUS)

NO_SAMPLES_REASON = "prior_art_memory_no_samples"
PASS_REASON = "prior_art_memory_pass"
WATCH_REASON = "prior_art_memory_watch"
BLOCK_REASON = "prior_art_memory_block"
SAMPLE_COUNT_BELOW_WATCH_REASON = "historical_sample_count_below_watch"
SAMPLE_COUNT_BELOW_PASS_REASON = "historical_sample_count_below_pass"
CALIBRATION_BELOW_WATCH_REASON = "calibration_quality_below_watch"
CALIBRATION_BELOW_PASS_REASON = "calibration_quality_below_pass"
AMBIGUITY_ABOVE_WATCH_REASON = "resolution_ambiguity_above_watch"
AMBIGUITY_ABOVE_PASS_REASON = "resolution_ambiguity_above_pass"
RELIABILITY_BELOW_WATCH_REASON = "source_reliability_below_watch"
RELIABILITY_BELOW_PASS_REASON = "source_reliability_below_pass"
STALE_ABOVE_WATCH_REASON = "stale_memory_above_watch"
STALE_ABOVE_PASS_REASON = "stale_memory_above_pass"

REASON_CODE_PRIORITY = (
    NO_SAMPLES_REASON,
    BLOCK_REASON,
    WATCH_REASON,
    PASS_REASON,
    SAMPLE_COUNT_BELOW_WATCH_REASON,
    CALIBRATION_BELOW_WATCH_REASON,
    AMBIGUITY_ABOVE_WATCH_REASON,
    RELIABILITY_BELOW_WATCH_REASON,
    STALE_ABOVE_WATCH_REASON,
    SAMPLE_COUNT_BELOW_PASS_REASON,
    CALIBRATION_BELOW_PASS_REASON,
    AMBIGUITY_ABOVE_PASS_REASON,
    RELIABILITY_BELOW_PASS_REASON,
    STALE_ABOVE_PASS_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
RATIO_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
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
    "DEFAULT_RESEARCH_EVENT_CATEGORY_PRIOR_ART_MEMORY_CONFIG_VERSION",
    "STATUSES",
    "ResearchEventCategoryPriorArtMemoryConfig",
    "ResearchEventCategoryPriorArtMemoryReasonCodeCount",
    "ResearchEventCategoryPriorArtMemoryReport",
    "ResearchEventCategoryPriorArtMemoryRow",
    "ResearchEventCategoryPriorArtMemorySample",
    "build_research_event_category_prior_art_memory_report",
    "research_event_category_prior_art_memory_report_digest",
    "research_event_category_prior_art_memory_report_payload",
)


@dataclass(frozen=True)
class ResearchEventCategoryPriorArtMemoryConfig:
    config_version: str = DEFAULT_RESEARCH_EVENT_CATEGORY_PRIOR_ART_MEMORY_CONFIG_VERSION
    min_pass_historical_sample_count: Decimal = Decimal("20")
    min_watch_historical_sample_count: Decimal = Decimal("5")
    min_pass_calibration_quality_ratio: Decimal = Decimal("0.700000")
    min_watch_calibration_quality_ratio: Decimal = Decimal("0.500000")
    max_pass_resolution_ambiguity_ratio: Decimal = Decimal("0.100000")
    max_watch_resolution_ambiguity_ratio: Decimal = Decimal("0.300000")
    min_pass_source_reliability_ratio: Decimal = Decimal("0.700000")
    min_watch_source_reliability_ratio: Decimal = Decimal("0.500000")
    max_pass_stale_memory_ratio: Decimal = Decimal("0.150000")
    max_watch_stale_memory_ratio: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventCategoryPriorArtMemoryConfig:
            raise TypeError("ResearchEventCategoryPriorArtMemoryConfig is final")

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventCategoryPriorArtMemoryConfig:
            raise ValueError(
                "config must be exactly ResearchEventCategoryPriorArtMemoryConfig",
            )
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        for field_name in (
            "min_pass_historical_sample_count",
            "min_watch_historical_sample_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_calibration_quality_ratio",
            "min_watch_calibration_quality_ratio",
            "max_pass_resolution_ambiguity_ratio",
            "max_watch_resolution_ambiguity_ratio",
            "min_pass_source_reliability_ratio",
            "min_watch_source_reliability_ratio",
            "max_pass_stale_memory_ratio",
            "max_watch_stale_memory_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchEventCategoryPriorArtMemorySample:
    event_category: str
    event_subcategory: str
    historical_sample_count: Decimal
    calibrated_sample_count: Decimal
    miscalibrated_sample_count: Decimal
    ambiguous_resolution_count: Decimal
    reliable_source_sample_count: Decimal
    stale_memory_sample_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventCategoryPriorArtMemorySample:
            raise TypeError("ResearchEventCategoryPriorArtMemorySample is final")

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventCategoryPriorArtMemorySample:
            raise ValueError(
                "sample must be exactly ResearchEventCategoryPriorArtMemorySample",
            )
        object.__setattr__(
            self,
            "event_category",
            _require_public_identifier("event_category", self.event_category),
        )
        object.__setattr__(
            self,
            "event_subcategory",
            _require_public_identifier("event_subcategory", self.event_subcategory),
        )
        for field_name in (
            "historical_sample_count",
            "calibrated_sample_count",
            "miscalibrated_sample_count",
            "ambiguous_resolution_count",
            "reliable_source_sample_count",
            "stale_memory_sample_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        _validate_sample(self)
        _require_hard_flags("sample", self)
        _reject_unsafe_public_payload("sample", self)


@dataclass(frozen=True)
class ResearchEventCategoryPriorArtMemoryRow:
    event_category: str
    event_subcategory: str
    historical_sample_count: Decimal
    calibrated_sample_count: Decimal
    miscalibrated_sample_count: Decimal
    ambiguous_resolution_count: Decimal
    reliable_source_sample_count: Decimal
    stale_memory_sample_count: Decimal
    calibration_quality_ratio: Decimal
    resolution_ambiguity_ratio: Decimal
    source_reliability_ratio: Decimal
    stale_memory_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventCategoryPriorArtMemoryRow:
            raise TypeError("ResearchEventCategoryPriorArtMemoryRow is final")

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventCategoryPriorArtMemoryRow:
            raise ValueError("row must be exactly ResearchEventCategoryPriorArtMemoryRow")
        object.__setattr__(
            self,
            "event_category",
            _require_public_identifier("event_category", self.event_category),
        )
        object.__setattr__(
            self,
            "event_subcategory",
            _require_public_identifier("event_subcategory", self.event_subcategory),
        )
        for field_name in (
            "historical_sample_count",
            "calibrated_sample_count",
            "miscalibrated_sample_count",
            "ambiguous_resolution_count",
            "reliable_source_sample_count",
            "stale_memory_sample_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "calibration_quality_ratio",
            "resolution_ambiguity_ratio",
            "source_reliability_ratio",
            "stale_memory_ratio",
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
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchEventCategoryPriorArtMemoryReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventCategoryPriorArtMemoryReasonCodeCount:
            raise TypeError("ResearchEventCategoryPriorArtMemoryReasonCodeCount is final")

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventCategoryPriorArtMemoryReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchEventCategoryPriorArtMemoryReasonCodeCount",
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
class ResearchEventCategoryPriorArtMemoryReport:
    generated_at: datetime
    config_version: str
    category_subcategory_count: Decimal
    historical_sample_count: Decimal
    calibrated_sample_count: Decimal
    miscalibrated_sample_count: Decimal
    ambiguous_resolution_count: Decimal
    reliable_source_sample_count: Decimal
    stale_memory_sample_count: Decimal
    average_calibration_quality_ratio: Decimal
    overall_resolution_ambiguity_ratio: Decimal
    overall_source_reliability_ratio: Decimal
    overall_stale_memory_ratio: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchEventCategoryPriorArtMemoryReasonCodeCount, ...]
    rows: tuple[ResearchEventCategoryPriorArtMemoryRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventCategoryPriorArtMemoryReport:
            raise TypeError("ResearchEventCategoryPriorArtMemoryReport is final")

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventCategoryPriorArtMemoryReport:
            raise ValueError(
                "report must be exactly ResearchEventCategoryPriorArtMemoryReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        for field_name in (
            "category_subcategory_count",
            "historical_sample_count",
            "calibrated_sample_count",
            "miscalibrated_sample_count",
            "ambiguous_resolution_count",
            "reliable_source_sample_count",
            "stale_memory_sample_count",
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
            "average_calibration_quality_ratio",
            "overall_resolution_ambiguity_ratio",
            "overall_source_reliability_ratio",
            "overall_stale_memory_ratio",
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


def build_research_event_category_prior_art_memory_report(
    samples: list[ResearchEventCategoryPriorArtMemorySample]
    | tuple[ResearchEventCategoryPriorArtMemorySample, ...],
    *,
    config: ResearchEventCategoryPriorArtMemoryConfig,
    generated_at: datetime,
) -> ResearchEventCategoryPriorArtMemoryReport:
    if type(config) is not ResearchEventCategoryPriorArtMemoryConfig:
        raise ValueError(
            "config must be exactly ResearchEventCategoryPriorArtMemoryConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_samples = _normalize_samples(samples)
    rows = _build_rows(input_samples, config)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "category_subcategory_count": _count(len(rows)),
        "historical_sample_count": _sum_rows(rows, "historical_sample_count"),
        "calibrated_sample_count": _sum_rows(rows, "calibrated_sample_count"),
        "miscalibrated_sample_count": _sum_rows(rows, "miscalibrated_sample_count"),
        "ambiguous_resolution_count": _sum_rows(rows, "ambiguous_resolution_count"),
        "reliable_source_sample_count": _sum_rows(rows, "reliable_source_sample_count"),
        "stale_memory_sample_count": _sum_rows(rows, "stale_memory_sample_count"),
        "average_calibration_quality_ratio": _average_row_ratio(
            rows,
            "calibration_quality_ratio",
        ),
        "overall_resolution_ambiguity_ratio": _ratio(
            _sum_rows(rows, "ambiguous_resolution_count"),
            _sum_rows(rows, "historical_sample_count"),
        ),
        "overall_source_reliability_ratio": _ratio(
            _sum_rows(rows, "reliable_source_sample_count"),
            _sum_rows(rows, "historical_sample_count"),
        ),
        "overall_stale_memory_ratio": _ratio(
            _sum_rows(rows, "stale_memory_sample_count"),
            _sum_rows(rows, "historical_sample_count"),
        ),
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
    return ResearchEventCategoryPriorArtMemoryReport(
        **values,
        derived_validation_digest=_digest_from_values(values),
    )


def research_event_category_prior_art_memory_report_payload(
    report: ResearchEventCategoryPriorArtMemoryReport,
) -> dict[str, object]:
    if type(report) is not ResearchEventCategoryPriorArtMemoryReport:
        raise ValueError(
            "report must be exactly ResearchEventCategoryPriorArtMemoryReport",
        )
    _require_hard_flags("report", report)
    return report.payload


def research_event_category_prior_art_memory_report_digest(
    report: ResearchEventCategoryPriorArtMemoryReport,
) -> str:
    if type(report) is not ResearchEventCategoryPriorArtMemoryReport:
        raise ValueError(
            "report must be exactly ResearchEventCategoryPriorArtMemoryReport",
        )
    return _digest_from_values(_report_values_without_digest(report))


def _build_rows(
    samples: tuple[ResearchEventCategoryPriorArtMemorySample, ...],
    config: ResearchEventCategoryPriorArtMemoryConfig,
) -> tuple[ResearchEventCategoryPriorArtMemoryRow, ...]:
    by_pair: dict[tuple[str, str], list[ResearchEventCategoryPriorArtMemorySample]] = {}
    for sample in samples:
        by_pair.setdefault((sample.event_category, sample.event_subcategory), []).append(
            sample,
        )
    rows = tuple(_row_for_pair(pair, tuple(pair_samples), config) for pair, pair_samples in by_pair.items())
    return tuple(sorted(rows, key=_row_sort_key))


def _row_for_pair(
    pair: tuple[str, str],
    samples: tuple[ResearchEventCategoryPriorArtMemorySample, ...],
    config: ResearchEventCategoryPriorArtMemoryConfig,
) -> ResearchEventCategoryPriorArtMemoryRow:
    historical_sample_count = _sum_samples(samples, "historical_sample_count")
    calibrated_sample_count = _sum_samples(samples, "calibrated_sample_count")
    miscalibrated_sample_count = _sum_samples(samples, "miscalibrated_sample_count")
    ambiguous_resolution_count = _sum_samples(samples, "ambiguous_resolution_count")
    reliable_source_sample_count = _sum_samples(samples, "reliable_source_sample_count")
    stale_memory_sample_count = _sum_samples(samples, "stale_memory_sample_count")
    calibration_quality_ratio = _ratio(calibrated_sample_count, historical_sample_count)
    resolution_ambiguity_ratio = _ratio(
        ambiguous_resolution_count,
        historical_sample_count,
    )
    source_reliability_ratio = _ratio(
        reliable_source_sample_count,
        historical_sample_count,
    )
    stale_memory_ratio = _ratio(stale_memory_sample_count, historical_sample_count)
    status = _row_status(
        historical_sample_count=historical_sample_count,
        calibration_quality_ratio=calibration_quality_ratio,
        resolution_ambiguity_ratio=resolution_ambiguity_ratio,
        source_reliability_ratio=source_reliability_ratio,
        stale_memory_ratio=stale_memory_ratio,
        config=config,
    )
    return ResearchEventCategoryPriorArtMemoryRow(
        event_category=pair[0],
        event_subcategory=pair[1],
        historical_sample_count=historical_sample_count,
        calibrated_sample_count=calibrated_sample_count,
        miscalibrated_sample_count=miscalibrated_sample_count,
        ambiguous_resolution_count=ambiguous_resolution_count,
        reliable_source_sample_count=reliable_source_sample_count,
        stale_memory_sample_count=stale_memory_sample_count,
        calibration_quality_ratio=calibration_quality_ratio,
        resolution_ambiguity_ratio=resolution_ambiguity_ratio,
        source_reliability_ratio=source_reliability_ratio,
        stale_memory_ratio=stale_memory_ratio,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            historical_sample_count=historical_sample_count,
            calibration_quality_ratio=calibration_quality_ratio,
            resolution_ambiguity_ratio=resolution_ambiguity_ratio,
            source_reliability_ratio=source_reliability_ratio,
            stale_memory_ratio=stale_memory_ratio,
            config=config,
        ),
    )


def _row_status(
    *,
    historical_sample_count: Decimal,
    calibration_quality_ratio: Decimal,
    resolution_ambiguity_ratio: Decimal,
    source_reliability_ratio: Decimal,
    stale_memory_ratio: Decimal,
    config: ResearchEventCategoryPriorArtMemoryConfig,
) -> str:
    if (
        historical_sample_count < config.min_watch_historical_sample_count
        or calibration_quality_ratio < config.min_watch_calibration_quality_ratio
        or resolution_ambiguity_ratio > config.max_watch_resolution_ambiguity_ratio
        or source_reliability_ratio < config.min_watch_source_reliability_ratio
        or stale_memory_ratio > config.max_watch_stale_memory_ratio
    ):
        return BLOCK_STATUS
    if (
        historical_sample_count < config.min_pass_historical_sample_count
        or calibration_quality_ratio < config.min_pass_calibration_quality_ratio
        or resolution_ambiguity_ratio > config.max_pass_resolution_ambiguity_ratio
        or source_reliability_ratio < config.min_pass_source_reliability_ratio
        or stale_memory_ratio > config.max_pass_stale_memory_ratio
    ):
        return WATCH_STATUS
    return PASS_STATUS


def _row_reason_codes(
    *,
    status: str,
    historical_sample_count: Decimal,
    calibration_quality_ratio: Decimal,
    resolution_ambiguity_ratio: Decimal,
    source_reliability_ratio: Decimal,
    stale_memory_ratio: Decimal,
    config: ResearchEventCategoryPriorArtMemoryConfig,
) -> tuple[str, ...]:
    if status == PASS_STATUS:
        return (PASS_REASON,)
    if status == BLOCK_STATUS:
        reasons = [BLOCK_REASON]
        if historical_sample_count < config.min_watch_historical_sample_count:
            reasons.append(SAMPLE_COUNT_BELOW_WATCH_REASON)
        if calibration_quality_ratio < config.min_watch_calibration_quality_ratio:
            reasons.append(CALIBRATION_BELOW_WATCH_REASON)
        if resolution_ambiguity_ratio > config.max_watch_resolution_ambiguity_ratio:
            reasons.append(AMBIGUITY_ABOVE_WATCH_REASON)
        if source_reliability_ratio < config.min_watch_source_reliability_ratio:
            reasons.append(RELIABILITY_BELOW_WATCH_REASON)
        if stale_memory_ratio > config.max_watch_stale_memory_ratio:
            reasons.append(STALE_ABOVE_WATCH_REASON)
        return tuple(reasons)
    reasons = [WATCH_REASON]
    if historical_sample_count < config.min_pass_historical_sample_count:
        reasons.append(SAMPLE_COUNT_BELOW_PASS_REASON)
    if calibration_quality_ratio < config.min_pass_calibration_quality_ratio:
        reasons.append(CALIBRATION_BELOW_PASS_REASON)
    if resolution_ambiguity_ratio > config.max_pass_resolution_ambiguity_ratio:
        reasons.append(AMBIGUITY_ABOVE_PASS_REASON)
    if source_reliability_ratio < config.min_pass_source_reliability_ratio:
        reasons.append(RELIABILITY_BELOW_PASS_REASON)
    if stale_memory_ratio > config.max_pass_stale_memory_ratio:
        reasons.append(STALE_ABOVE_PASS_REASON)
    return tuple(reasons)


def _report_status(rows: tuple[ResearchEventCategoryPriorArtMemoryRow, ...]) -> str:
    if not rows:
        return BLOCK_STATUS
    statuses = tuple(row.status for row in rows)
    if BLOCK_STATUS in statuses:
        return BLOCK_STATUS
    if WATCH_STATUS in statuses:
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    rows: tuple[ResearchEventCategoryPriorArtMemoryRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_SAMPLES_REASON,)
    present = {reason for row in rows for reason in row.reason_codes}
    return tuple(reason for reason in REASON_CODE_PRIORITY if reason in present)


def _reason_code_counts(
    rows: tuple[ResearchEventCategoryPriorArtMemoryRow, ...],
) -> tuple[ResearchEventCategoryPriorArtMemoryReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchEventCategoryPriorArtMemoryReasonCodeCount(
                reason_code=NO_SAMPLES_REASON,
                count=Decimal("1"),
            ),
        )
    counts = Counter(reason for row in rows for reason in row.reason_codes)
    return tuple(
        ResearchEventCategoryPriorArtMemoryReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
        )
        for reason_code in REASON_CODE_PRIORITY
        if reason_code in counts
    )


def _row_sort_key(row: ResearchEventCategoryPriorArtMemoryRow) -> tuple[int, Decimal, str, str]:
    return (
        {BLOCK_STATUS: 0, WATCH_STATUS: 1, PASS_STATUS: 2}[row.status],
        -_row_pressure_score(row),
        row.event_category,
        row.event_subcategory,
    )


def _row_pressure_score(row: ResearchEventCategoryPriorArtMemoryRow) -> Decimal:
    quality_gap = ONE_RATIO - row.calibration_quality_ratio
    reliability_gap = ONE_RATIO - row.source_reliability_ratio
    return (
        quality_gap
        + row.resolution_ambiguity_ratio
        + reliability_gap
        + row.stale_memory_ratio
    )


def _validate_config(config: ResearchEventCategoryPriorArtMemoryConfig) -> None:
    if config.min_watch_historical_sample_count > config.min_pass_historical_sample_count:
        raise ValueError(
            "min_watch_historical_sample_count must not exceed pass threshold",
        )
    if config.min_watch_calibration_quality_ratio > config.min_pass_calibration_quality_ratio:
        raise ValueError(
            "min_watch_calibration_quality_ratio must not exceed pass threshold",
        )
    if config.max_pass_resolution_ambiguity_ratio > config.max_watch_resolution_ambiguity_ratio:
        raise ValueError(
            "max_pass_resolution_ambiguity_ratio must not exceed watch threshold",
        )
    if config.min_watch_source_reliability_ratio > config.min_pass_source_reliability_ratio:
        raise ValueError(
            "min_watch_source_reliability_ratio must not exceed pass threshold",
        )
    if config.max_pass_stale_memory_ratio > config.max_watch_stale_memory_ratio:
        raise ValueError("max_pass_stale_memory_ratio must not exceed watch threshold")


def _validate_sample(sample: ResearchEventCategoryPriorArtMemorySample) -> None:
    if (
        sample.calibrated_sample_count + sample.miscalibrated_sample_count
        != sample.historical_sample_count
    ):
        raise ValueError(
            "calibration counts must sum to historical_sample_count",
        )
    if sample.ambiguous_resolution_count > sample.historical_sample_count:
        raise ValueError(
            "ambiguous_resolution_count must not exceed historical_sample_count",
        )
    if sample.reliable_source_sample_count > sample.historical_sample_count:
        raise ValueError(
            "reliable_source_sample_count must not exceed historical_sample_count",
        )
    if sample.stale_memory_sample_count > sample.historical_sample_count:
        raise ValueError(
            "stale_memory_sample_count must not exceed historical_sample_count",
        )


def _validate_row(row: ResearchEventCategoryPriorArtMemoryRow) -> None:
    if row.calibrated_sample_count + row.miscalibrated_sample_count != row.historical_sample_count:
        raise ValueError("calibration counts must sum to historical_sample_count")
    if row.ambiguous_resolution_count > row.historical_sample_count:
        raise ValueError("ambiguous_resolution_count must not exceed historical_sample_count")
    if row.reliable_source_sample_count > row.historical_sample_count:
        raise ValueError("reliable_source_sample_count must not exceed historical_sample_count")
    if row.stale_memory_sample_count > row.historical_sample_count:
        raise ValueError("stale_memory_sample_count must not exceed historical_sample_count")
    if row.calibration_quality_ratio != _ratio(
        row.calibrated_sample_count,
        row.historical_sample_count,
    ):
        raise ValueError("calibration_quality_ratio does not match row counts")
    if row.resolution_ambiguity_ratio != _ratio(
        row.ambiguous_resolution_count,
        row.historical_sample_count,
    ):
        raise ValueError("resolution_ambiguity_ratio does not match row counts")
    if row.source_reliability_ratio != _ratio(
        row.reliable_source_sample_count,
        row.historical_sample_count,
    ):
        raise ValueError("source_reliability_ratio does not match row counts")
    if row.stale_memory_ratio != _ratio(
        row.stale_memory_sample_count,
        row.historical_sample_count,
    ):
        raise ValueError("stale_memory_ratio does not match row counts")


def _validate_report(report: ResearchEventCategoryPriorArtMemoryReport) -> None:
    rows = report.rows
    if report.category_subcategory_count != _count(len(rows)):
        raise ValueError("category_subcategory_count does not match rows")
    for field_name in (
        "historical_sample_count",
        "calibrated_sample_count",
        "miscalibrated_sample_count",
        "ambiguous_resolution_count",
        "reliable_source_sample_count",
        "stale_memory_sample_count",
    ):
        if getattr(report, field_name) != _sum_rows(rows, field_name):
            raise ValueError(f"{field_name} does not match rows")
    if report.average_calibration_quality_ratio != _average_row_ratio(
        rows,
        "calibration_quality_ratio",
    ):
        raise ValueError("average_calibration_quality_ratio does not match rows")
    if report.overall_resolution_ambiguity_ratio != _ratio(
        report.ambiguous_resolution_count,
        report.historical_sample_count,
    ):
        raise ValueError("overall_resolution_ambiguity_ratio does not match rows")
    if report.overall_source_reliability_ratio != _ratio(
        report.reliable_source_sample_count,
        report.historical_sample_count,
    ):
        raise ValueError("overall_source_reliability_ratio does not match rows")
    if report.overall_stale_memory_ratio != _ratio(
        report.stale_memory_sample_count,
        report.historical_sample_count,
    ):
        raise ValueError("overall_stale_memory_ratio does not match rows")
    for status, field_name in (
        (PASS_STATUS, "pass_count"),
        (WATCH_STATUS, "watch_count"),
        (BLOCK_STATUS, "block_count"),
    ):
        if getattr(report, field_name) != _status_count(rows, status):
            raise ValueError(f"{field_name} does not match rows")
    if report.status != _report_status(rows):
        raise ValueError("status does not match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes do not match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts do not match rows")
    if tuple(sorted(rows, key=_row_sort_key)) != rows:
        raise ValueError("rows must be sorted deterministically")


def _normalize_samples(
    samples: list[ResearchEventCategoryPriorArtMemorySample]
    | tuple[ResearchEventCategoryPriorArtMemorySample, ...],
) -> tuple[ResearchEventCategoryPriorArtMemorySample, ...]:
    if type(samples) not in (list, tuple):
        raise ValueError("samples must be a list or tuple")
    normalized = tuple(samples)
    for sample in normalized:
        if type(sample) is not ResearchEventCategoryPriorArtMemorySample:
            raise ValueError(
                "samples must contain ResearchEventCategoryPriorArtMemorySample values",
            )
        _require_hard_flags("sample", sample)
    return normalized


def _normalize_rows(
    rows: tuple[ResearchEventCategoryPriorArtMemoryRow, ...],
) -> tuple[ResearchEventCategoryPriorArtMemoryRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchEventCategoryPriorArtMemoryRow:
            raise ValueError(
                "rows must contain ResearchEventCategoryPriorArtMemoryRow values",
            )
        _require_hard_flags("row", row)
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchEventCategoryPriorArtMemoryReasonCodeCount, ...],
) -> tuple[ResearchEventCategoryPriorArtMemoryReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchEventCategoryPriorArtMemoryReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchEventCategoryPriorArtMemoryReasonCodeCount values",
            )
        _require_hard_flags("reason code count", count)
    return counts


def _normalize_reason_codes(
    reason_codes: tuple[str, ...],
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized = tuple(_require_reason_code("reason_code", reason) for reason in reason_codes)
    if require_nonempty and not normalized:
        raise ValueError("reason_codes must not be empty")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    if tuple(reason for reason in REASON_CODE_PRIORITY if reason in normalized) != normalized:
        raise ValueError("reason_codes must follow priority order")
    return normalized


def _sum_samples(
    samples: tuple[ResearchEventCategoryPriorArtMemorySample, ...],
    field_name: str,
) -> Decimal:
    total = ZERO_COUNT
    for sample in samples:
        total += getattr(sample, field_name)
    return _count(total)


def _sum_rows(
    rows: tuple[ResearchEventCategoryPriorArtMemoryRow, ...],
    field_name: str,
) -> Decimal:
    total = ZERO_COUNT
    for row in rows:
        total += getattr(row, field_name)
    return _count(total)


def _average_row_ratio(
    rows: tuple[ResearchEventCategoryPriorArtMemoryRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO_RATIO
    total = ZERO_RATIO
    for row in rows:
        total += getattr(row, field_name)
    return _ratio(total, _count(len(rows)))


def _status_count(
    rows: tuple[ResearchEventCategoryPriorArtMemoryRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _count(value: int | Decimal) -> Decimal:
    if type(value) is int:
        return Decimal(value).quantize(COUNT_QUANTUM)
    return _require_nonnegative_whole_decimal("count", value)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO_COUNT:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(RATIO_QUANTUM)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_nonnegative_whole_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return value.quantize(COUNT_QUANTUM)


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_RATIO or value > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return value.quantize(RATIO_QUANTUM)


def _require_public_identifier(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be public-safe text")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be public-safe text")
    if normalized != value or normalized.lower() != normalized:
        raise ValueError(f"{field_name} must be public-safe text")
    if any(character not in PUBLIC_IDENTIFIER_CHARS for character in normalized):
        raise ValueError(f"{field_name} must be public-safe text")
    lowered = normalized.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} must be public-safe text")
    return normalized


def _require_reason_code(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a reason code")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be a reason code")
    if normalized != value or normalized.lower() != normalized:
        raise ValueError(f"{field_name} must be a reason code")
    if any(character not in PUBLIC_REASON_CODE_CHARS for character in normalized):
        raise ValueError(f"{field_name} must be a reason code")
    return normalized


def _require_status(field_name: str, value: str) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass/watch/block status")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_sha256_digest(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if len(value) != SHA256_HEX_LENGTH:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _report_values_without_digest(
    report: ResearchEventCategoryPriorArtMemoryReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest")
    return values


def _digest_from_values(values: dict[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload("digest payload", payload)
    encoded = dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        return _decimal_to_string(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _decimal_to_string(value: Decimal) -> str:
    if value == value.to_integral_value():
        return str(value.quantize(COUNT_QUANTUM))
    return format(value, "f")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, str):
        lowered = value.lower()
        if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError(f"{label} contains non public-safe text")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_public_payload(f"{label}.{key}", str(key))
            _reject_unsafe_public_payload(f"{label}.{key}", item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
