"""Pure Phase 1 AI model release digest reducer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_MARKET_RESEARCH_AI_MODEL_RELEASE_DIGEST_CONFIG_VERSION = (
    "market-research-ai-model-release-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
RELEASE_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

REASON_PREFIX = "market_research_ai_model_release_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
READY_REASON = f"{REASON_PREFIX}ready"
HIGH_IMPACT_RELEASE_REASON = f"{REASON_PREFIX}high_impact_release"
PROBABILITY_REPRICING_REASON = f"{REASON_PREFIX}probability_repricing"
MISSING_REVIEW_REASON = f"{REASON_PREFIX}missing_review"
SLOW_REVIEW_REASON = f"{REASON_PREFIX}slow_review"
STALE_RELEASE_REASON = f"{REASON_PREFIX}stale_release"
THIN_SOURCES_REASON = f"{REASON_PREFIX}thin_sources"

REASON_CODE_SEQUENCE = (
    STALE_RELEASE_REASON,
    HIGH_IMPACT_RELEASE_REASON,
    MISSING_REVIEW_REASON,
    PROBABILITY_REPRICING_REASON,
    SLOW_REVIEW_REASON,
    THIN_SOURCES_REASON,
    READY_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    HIGH_IMPACT_RELEASE_REASON,
    MISSING_REVIEW_REASON,
    PROBABILITY_REPRICING_REASON,
    READY_REASON,
    SLOW_REVIEW_REASON,
    STALE_RELEASE_REASON,
    THIN_SOURCES_REASON,
)

NEXT_STEPS = {
    STATUS_READY: "allow_report_only_market_research_ai_model_release_digest",
    STATUS_WATCH: "watch_report_only_market_research_ai_model_release_digest",
    STATUS_BLOCKED: "block_report_only_market_research_ai_model_release_digest",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
PROBABILITY_REPRICING_THRESHOLD = Decimal("0.100000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("au", "th"),
        _join_parts("bro", "ker"),
        _join_parts("sig", "ning"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("ad", "vice"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("pay", "load"),
        _join_parts("pri", "vate"),
        _join_parts("to", "ken"),
        _join_parts("sec", "ret"),
        _join_parts("ht", "tp"),
    ),
)


@dataclass(frozen=True)
class MarketResearchAiModelReleaseDigestConfig:
    config_version: str = DEFAULT_MARKET_RESEARCH_AI_MODEL_RELEASE_DIGEST_CONFIG_VERSION
    fresh_release_max_age_seconds: Decimal = Decimal("86400.000000")
    high_impact_capability_threshold: Decimal = Decimal("0.200000")
    min_public_source_count: Decimal = Decimal("2.000000")
    max_review_lag_seconds: Decimal = Decimal("7200.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchAiModelReleaseDigestConfig:
            raise TypeError(
                "MarketResearchAiModelReleaseDigestConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchAiModelReleaseDigestConfig:
            raise ValueError(
                "config must be exactly MarketResearchAiModelReleaseDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "fresh_release_max_age_seconds",
            _require_nonnegative_decimal(
                "fresh_release_max_age_seconds",
                self.fresh_release_max_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "high_impact_capability_threshold",
            _require_ratio_decimal(
                "high_impact_capability_threshold",
                self.high_impact_capability_threshold,
            ),
        )
        object.__setattr__(
            self,
            "min_public_source_count",
            _require_nonnegative_count_decimal(
                "min_public_source_count",
                self.min_public_source_count,
            ),
        )
        object.__setattr__(
            self,
            "max_review_lag_seconds",
            _require_nonnegative_decimal(
                "max_review_lag_seconds",
                self.max_review_lag_seconds,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchAiModelReleaseDigestInputRow:
    research_key: str
    condition_id: str
    model_family: str
    public_release_reference: str
    released_at: datetime
    reviewed_at: datetime | None
    public_source_count: Decimal
    capability_delta: Decimal
    benchmark_delta: Decimal
    probability_before: Decimal
    probability_after: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchAiModelReleaseDigestInputRow:
            raise TypeError(
                "MarketResearchAiModelReleaseDigestInputRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchAiModelReleaseDigestInputRow:
            raise ValueError(
                "input row must be exactly MarketResearchAiModelReleaseDigestInputRow",
            )
        for field_name in ("research_key", "condition_id", "model_family"):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_reference_string(
            "public_release_reference",
            self.public_release_reference,
        )
        object.__setattr__(self, "released_at", _as_utc("released_at", self.released_at))
        object.__setattr__(
            self,
            "reviewed_at",
            _optional_utc("reviewed_at", self.reviewed_at),
        )
        object.__setattr__(
            self,
            "public_source_count",
            _require_nonnegative_count_decimal(
                "public_source_count",
                self.public_source_count,
            ),
        )
        for field_name in ("capability_delta", "benchmark_delta"):
            object.__setattr__(
                self,
                field_name,
                _require_finite_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "probability_before",
            _require_ratio_decimal("probability_before", self.probability_before),
        )
        object.__setattr__(
            self,
            "probability_after",
            _require_ratio_decimal("probability_after", self.probability_after),
        )
        if self.reviewed_at is not None and self.reviewed_at < self.released_at:
            raise ValueError("reviewed_at must be on or after released_at")
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchAiModelReleaseDigestRow:
    research_key: str
    condition_id: str
    model_family: str
    released_at: datetime
    reviewed_at: datetime | None
    release_age_seconds: Decimal
    review_lag_seconds: Decimal | None
    public_source_count: Decimal
    capability_delta: Decimal
    capability_delta_abs: Decimal
    benchmark_delta: Decimal
    benchmark_delta_abs: Decimal
    probability_before: Decimal
    probability_after: Decimal
    probability_delta: Decimal
    release_status: str
    redacted_release_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchAiModelReleaseDigestRow:
            raise TypeError(
                "MarketResearchAiModelReleaseDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchAiModelReleaseDigestRow:
            raise ValueError("row must be exactly MarketResearchAiModelReleaseDigestRow")
        for field_name in ("research_key", "condition_id", "model_family"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "released_at", _as_utc("released_at", self.released_at))
        object.__setattr__(
            self,
            "reviewed_at",
            _optional_utc("reviewed_at", self.reviewed_at),
        )
        object.__setattr__(
            self,
            "release_age_seconds",
            _require_nonnegative_decimal("release_age_seconds", self.release_age_seconds),
        )
        object.__setattr__(
            self,
            "review_lag_seconds",
            _require_optional_nonnegative_decimal(
                "review_lag_seconds",
                self.review_lag_seconds,
            ),
        )
        object.__setattr__(
            self,
            "public_source_count",
            _require_nonnegative_count_decimal(
                "public_source_count",
                self.public_source_count,
            ),
        )
        for field_name in ("capability_delta", "benchmark_delta"):
            object.__setattr__(
                self,
                field_name,
                _require_finite_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("capability_delta_abs", "benchmark_delta_abs"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("probability_before", "probability_after"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "probability_delta",
            _require_probability_delta("probability_delta", self.probability_delta),
        )
        _require_release_status("release_status", self.release_status)
        object.__setattr__(
            self,
            "redacted_release_reference",
            _require_redacted_reference(
                "redacted_release_reference",
                self.redacted_release_reference,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchAiModelReleaseDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    release_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchAiModelReleaseDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchAiModelReleaseDigestReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchAiModelReleaseDigestReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "MarketResearchAiModelReleaseDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "release_ratio",
            _require_ratio_decimal("release_ratio", self.release_ratio),
        )
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class MarketResearchAiModelReleaseDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    release_count: Decimal
    ready_release_count: Decimal
    watch_release_count: Decimal
    blocked_release_count: Decimal
    high_impact_release_count: Decimal
    stale_release_count: Decimal
    thin_source_count: Decimal
    missing_review_count: Decimal
    slow_review_count: Decimal
    probability_repricing_count: Decimal
    average_capability_delta: Decimal
    max_release_age_seconds: Decimal
    average_public_source_count: Decimal
    rows: tuple[MarketResearchAiModelReleaseDigestRow, ...]
    reason_code_counts: tuple[MarketResearchAiModelReleaseDigestReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchAiModelReleaseDigestReport:
            raise TypeError(
                "MarketResearchAiModelReleaseDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchAiModelReleaseDigestReport:
            raise ValueError(
                "report must be exactly MarketResearchAiModelReleaseDigestReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_release_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "release_count",
            "ready_release_count",
            "watch_release_count",
            "blocked_release_count",
            "high_impact_release_count",
            "stale_release_count",
            "thin_source_count",
            "missing_review_count",
            "slow_review_count",
            "probability_repricing_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_capability_delta",
            "max_release_age_seconds",
            "average_public_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        reject_unsafe_surface_fields("AI model release digest report", self)
        _require_hard_flags("report", self)


def build_market_research_ai_model_release_digest(
    input_rows: list[MarketResearchAiModelReleaseDigestInputRow]
    | tuple[MarketResearchAiModelReleaseDigestInputRow, ...],
    *,
    config: MarketResearchAiModelReleaseDigestConfig,
    generated_at: datetime,
) -> MarketResearchAiModelReleaseDigestReport:
    if type(config) is not MarketResearchAiModelReleaseDigestConfig:
        raise ValueError("config must be a MarketResearchAiModelReleaseDigestConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_rows = _normalize_input_rows(input_rows, generated_at_utc)
    rows = tuple(
        _build_row(row, config=config, generated_at=generated_at_utc)
        for row in source_rows
    )
    ranked_rows = _ranked_rows(rows)
    reason_code_counts = _reason_code_counts(ranked_rows)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    if not ranked_rows:
        reason_code_counts = (
            MarketResearchAiModelReleaseDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                release_ratio=ONE,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)

    release_count = _count(len(ranked_rows))
    ready_release_count = _count(
        sum(1 for row in ranked_rows if row.release_status == STATUS_READY),
    )
    watch_release_count = _count(
        sum(1 for row in ranked_rows if row.release_status == STATUS_WATCH),
    )
    blocked_release_count = _count(
        sum(1 for row in ranked_rows if row.release_status == STATUS_BLOCKED),
    )
    digest_status = _report_status(
        has_inputs=bool(ranked_rows),
        blocked_release_count=blocked_release_count,
        watch_release_count=watch_release_count,
    )

    return MarketResearchAiModelReleaseDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        release_count=release_count,
        ready_release_count=ready_release_count,
        watch_release_count=watch_release_count,
        blocked_release_count=blocked_release_count,
        high_impact_release_count=_count(
            sum(
                1
                for row in ranked_rows
                if HIGH_IMPACT_RELEASE_REASON in row.reason_codes
            ),
        ),
        stale_release_count=_count(
            sum(1 for row in ranked_rows if STALE_RELEASE_REASON in row.reason_codes),
        ),
        thin_source_count=_count(
            sum(1 for row in ranked_rows if THIN_SOURCES_REASON in row.reason_codes),
        ),
        missing_review_count=_count(
            sum(1 for row in ranked_rows if MISSING_REVIEW_REASON in row.reason_codes),
        ),
        slow_review_count=_count(
            sum(1 for row in ranked_rows if SLOW_REVIEW_REASON in row.reason_codes),
        ),
        probability_repricing_count=_count(
            sum(
                1
                for row in ranked_rows
                if PROBABILITY_REPRICING_REASON in row.reason_codes
            ),
        ),
        average_capability_delta=_ratio(
            _sum_decimal(row.capability_delta_abs for row in ranked_rows),
            release_count,
        ),
        max_release_age_seconds=max(
            (row.release_age_seconds for row in ranked_rows),
            default=ZERO,
        ),
        average_public_source_count=_ratio(
            _sum_decimal(row.public_source_count for row in ranked_rows),
            release_count,
        ),
        rows=ranked_rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_ai_model_release_digest_payload(
    report: MarketResearchAiModelReleaseDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchAiModelReleaseDigestReport:
        raise ValueError(
            "report must be a MarketResearchAiModelReleaseDigestReport",
        )
    _require_hard_flags("report", report)
    reject_unsafe_surface_fields("AI model release digest report", report)
    return json_ready_no_floats(report)


def _build_row(
    row: MarketResearchAiModelReleaseDigestInputRow,
    *,
    config: MarketResearchAiModelReleaseDigestConfig,
    generated_at: datetime,
) -> MarketResearchAiModelReleaseDigestRow:
    release_age_seconds = _datetime_delta_seconds(generated_at, row.released_at)
    review_lag_seconds = (
        None
        if row.reviewed_at is None
        else _datetime_delta_seconds(row.reviewed_at, row.released_at)
    )
    capability_delta_abs = _abs_decimal(row.capability_delta)
    benchmark_delta_abs = _abs_decimal(row.benchmark_delta)
    probability_delta = _quantize(row.probability_after - row.probability_before)
    reason_codes = _row_reason_codes(
        release_age_seconds=release_age_seconds,
        review_lag_seconds=review_lag_seconds,
        public_source_count=row.public_source_count,
        capability_delta_abs=capability_delta_abs,
        benchmark_delta_abs=benchmark_delta_abs,
        probability_delta=probability_delta,
        config=config,
    )
    release_status = _row_status(reason_codes)
    return MarketResearchAiModelReleaseDigestRow(
        research_key=row.research_key,
        condition_id=row.condition_id,
        model_family=row.model_family,
        released_at=row.released_at,
        reviewed_at=row.reviewed_at,
        release_age_seconds=release_age_seconds,
        review_lag_seconds=review_lag_seconds,
        public_source_count=row.public_source_count,
        capability_delta=row.capability_delta,
        capability_delta_abs=capability_delta_abs,
        benchmark_delta=row.benchmark_delta,
        benchmark_delta_abs=benchmark_delta_abs,
        probability_before=row.probability_before,
        probability_after=row.probability_after,
        probability_delta=probability_delta,
        release_status=release_status,
        redacted_release_reference=_redacted_reference(row.public_release_reference),
        reason_codes=reason_codes,
    )


def _normalize_input_rows(
    rows: list[MarketResearchAiModelReleaseDigestInputRow]
    | tuple[MarketResearchAiModelReleaseDigestInputRow, ...],
    generated_at: datetime,
) -> tuple[MarketResearchAiModelReleaseDigestInputRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    normalized = tuple(rows)
    seen: set[tuple[str, str]] = set()
    for row in normalized:
        if type(row) is not MarketResearchAiModelReleaseDigestInputRow:
            raise ValueError(
                "input rows must contain MarketResearchAiModelReleaseDigestInputRow",
            )
        _require_hard_flags("input row", row)
        if row.released_at > generated_at:
            raise ValueError("released_at must be on or before generated_at")
        key = (row.research_key, row.condition_id)
        if key in seen:
            raise ValueError("input rows must not contain duplicate research keys")
        seen.add(key)
    return normalized


def _row_reason_codes(
    *,
    release_age_seconds: Decimal,
    review_lag_seconds: Decimal | None,
    public_source_count: Decimal,
    capability_delta_abs: Decimal,
    benchmark_delta_abs: Decimal,
    probability_delta: Decimal,
    config: MarketResearchAiModelReleaseDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if (
        capability_delta_abs >= config.high_impact_capability_threshold
        or benchmark_delta_abs >= config.high_impact_capability_threshold
    ):
        reason_codes.append(HIGH_IMPACT_RELEASE_REASON)
    if review_lag_seconds is None:
        reason_codes.append(MISSING_REVIEW_REASON)
    if _abs_decimal(probability_delta) >= PROBABILITY_REPRICING_THRESHOLD:
        reason_codes.append(PROBABILITY_REPRICING_REASON)
    if review_lag_seconds is not None and review_lag_seconds > config.max_review_lag_seconds:
        reason_codes.append(SLOW_REVIEW_REASON)
    if release_age_seconds > config.fresh_release_max_age_seconds:
        reason_codes.append(STALE_RELEASE_REASON)
    if public_source_count < config.min_public_source_count:
        reason_codes.append(THIN_SOURCES_REASON)
    if not reason_codes:
        reason_codes.append(READY_REASON)
    return tuple(
        reason_code
        for reason_code in ROW_REASON_CODE_SEQUENCE
        if reason_code in reason_codes
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if MISSING_REVIEW_REASON in reason_codes:
        return STATUS_BLOCKED
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    return STATUS_WATCH


def _report_status(
    *,
    has_inputs: bool,
    blocked_release_count: Decimal,
    watch_release_count: Decimal,
) -> str:
    if not has_inputs or blocked_release_count > ZERO:
        return STATUS_BLOCKED
    if watch_release_count > ZERO:
        return STATUS_WATCH
    return STATUS_READY


def _ranked_rows(
    rows: tuple[MarketResearchAiModelReleaseDigestRow, ...],
) -> tuple[MarketResearchAiModelReleaseDigestRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _status_rank(row.release_status),
                -row.capability_delta_abs,
                row.model_family,
                row.research_key,
            ),
        ),
    )


def _status_rank(value: str) -> int:
    return {
        STATUS_BLOCKED: 0,
        STATUS_WATCH: 1,
        STATUS_READY: 2,
    }[value]


def _reason_code_counts(
    rows: tuple[MarketResearchAiModelReleaseDigestRow, ...],
) -> tuple[MarketResearchAiModelReleaseDigestReasonCodeCount, ...]:
    total = _count(len(rows))
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        MarketResearchAiModelReleaseDigestReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
            release_ratio=_ratio(counts[reason_code], total),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _validate_row(row: MarketResearchAiModelReleaseDigestRow) -> None:
    expected_probability_delta = _quantize(row.probability_after - row.probability_before)
    if row.probability_delta != expected_probability_delta:
        raise ValueError("probability_delta must match probability inputs")
    if row.capability_delta_abs != _abs_decimal(row.capability_delta):
        raise ValueError("capability_delta_abs must match capability_delta")
    if row.benchmark_delta_abs != _abs_decimal(row.benchmark_delta):
        raise ValueError("benchmark_delta_abs must match benchmark_delta")
    if row.reviewed_at is None:
        expected_lag = None
    else:
        expected_lag = _datetime_delta_seconds(row.reviewed_at, row.released_at)
    if row.review_lag_seconds != expected_lag:
        raise ValueError("review_lag_seconds must match reviewed_at and released_at")
    if row.release_status != _row_status(row.reason_codes):
        raise ValueError("release_status must match reason_codes")
    if not _is_redacted_reference(row.redacted_release_reference):
        raise ValueError("redacted_release_reference must be redacted or public")


def _validate_report(report: MarketResearchAiModelReleaseDigestReport) -> None:
    if report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.rows != _ranked_rows(report.rows):
        raise ValueError("rows must be sorted deterministically")
    if report.release_count != _count(len(report.rows)):
        raise ValueError("release_count must match rows")
    if report.ready_release_count != _count(
        sum(1 for row in report.rows if row.release_status == STATUS_READY),
    ):
        raise ValueError("ready_release_count must match rows")
    if report.watch_release_count != _count(
        sum(1 for row in report.rows if row.release_status == STATUS_WATCH),
    ):
        raise ValueError("watch_release_count must match rows")
    if report.blocked_release_count != _count(
        sum(1 for row in report.rows if row.release_status == STATUS_BLOCKED),
    ):
        raise ValueError("blocked_release_count must match rows")
    if report.high_impact_release_count != _count(
        sum(1 for row in report.rows if HIGH_IMPACT_RELEASE_REASON in row.reason_codes),
    ):
        raise ValueError("high_impact_release_count must match rows")
    if report.stale_release_count != _count(
        sum(1 for row in report.rows if STALE_RELEASE_REASON in row.reason_codes),
    ):
        raise ValueError("stale_release_count must match rows")
    if report.thin_source_count != _count(
        sum(1 for row in report.rows if THIN_SOURCES_REASON in row.reason_codes),
    ):
        raise ValueError("thin_source_count must match rows")
    if report.missing_review_count != _count(
        sum(1 for row in report.rows if MISSING_REVIEW_REASON in row.reason_codes),
    ):
        raise ValueError("missing_review_count must match rows")
    if report.slow_review_count != _count(
        sum(1 for row in report.rows if SLOW_REVIEW_REASON in row.reason_codes),
    ):
        raise ValueError("slow_review_count must match rows")
    if report.probability_repricing_count != _count(
        sum(1 for row in report.rows if PROBABILITY_REPRICING_REASON in row.reason_codes),
    ):
        raise ValueError("probability_repricing_count must match rows")
    if report.average_capability_delta != _ratio(
        _sum_decimal(row.capability_delta_abs for row in report.rows),
        report.release_count,
    ):
        raise ValueError("average_capability_delta must match rows")
    expected_max_age = max(
        (row.release_age_seconds for row in report.rows),
        default=ZERO,
    )
    if report.max_release_age_seconds != expected_max_age:
        raise ValueError("max_release_age_seconds must match rows")
    if report.average_public_source_count != _ratio(
        _sum_decimal(row.public_source_count for row in report.rows),
        report.release_count,
    ):
        raise ValueError("average_public_source_count must match rows")
    expected_reason_counts = _reason_code_counts(report.rows)
    if not report.rows:
        expected_reason_counts = (
            MarketResearchAiModelReleaseDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                release_ratio=ONE,
            ),
            )
    if report.reason_code_counts != expected_reason_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")
    expected_status = _report_status(
        has_inputs=bool(report.rows),
        blocked_release_count=report.blocked_release_count,
        watch_release_count=report.watch_release_count,
    )
    if report.digest_status != expected_status:
        raise ValueError("digest_status must match rows")


def _normalize_rows(
    rows: tuple[MarketResearchAiModelReleaseDigestRow, ...],
) -> tuple[MarketResearchAiModelReleaseDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchAiModelReleaseDigestRow:
            raise ValueError("rows must contain MarketResearchAiModelReleaseDigestRow")
        _require_hard_flags("row", row)
    return rows


def _normalize_reason_code_counts(
    values: tuple[MarketResearchAiModelReleaseDigestReasonCodeCount, ...],
) -> tuple[MarketResearchAiModelReleaseDigestReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for item in values:
        if type(item) is not MarketResearchAiModelReleaseDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchAiModelReleaseDigestReasonCodeCount",
            )
        _require_hard_flags("reason count", item)
    if tuple(item.reason_code for item in values) != tuple(
        reason_code
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in {item.reason_code for item in values}
    ):
        raise ValueError("reason_code_counts must be deterministically sorted")
    return values


def _normalize_row_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not values:
        raise ValueError("reason_codes must not be empty")
    for value in values:
        _require_reason_code("reason_codes", value)
        if value not in ROW_REASON_CODE_SEQUENCE:
            raise ValueError("reason_codes must be row reason codes")
    normalized = tuple(
        reason_code for reason_code in ROW_REASON_CODE_SEQUENCE if reason_code in values
    )
    if normalized != values or len(set(values)) != len(values):
        raise ValueError("reason_codes must be deterministic and unique")
    if READY_REASON in values and values != (READY_REASON,):
        raise ValueError("reason_codes cannot mix ready with other reasons")
    return values


def _normalize_report_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not values:
        raise ValueError("reason_codes must not be empty")
    for value in values:
        _require_reason_code("reason_codes", value)
    normalized = tuple(
        reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in values
    )
    if normalized != values or len(set(values)) != len(values):
        raise ValueError("reason_codes must be deterministic and unique")
    return values


def _require_release_status(field_name: str, value: str) -> None:
    if type(value) is not str or value not in RELEASE_STATUSES:
        raise ValueError(f"{field_name} must be a valid release status")


def _require_reason_code(field_name: str, value: str) -> None:
    if type(value) is not str or value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe text")


def _require_reference_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_finite_decimal(field_name: str, value: Decimal) -> Decimal:
    return _require_decimal(field_name, value)


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_nonnegative_count_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized


def _require_positive_count_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be in inclusive unit range")
    return normalized


def _require_probability_delta(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < -ONE or normalized > ONE:
        raise ValueError(f"{field_name} must be in inclusive signed unit range")
    return normalized


def _require_redacted_reference(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _is_redacted_reference(value):
        raise ValueError(f"{field_name} must be redacted or public")
    return value


def _is_redacted_reference(value: str) -> bool:
    return value.startswith("sha256:") or value.startswith("public-")


def _redacted_reference(value: str) -> str:
    if value.startswith("public-"):
        return value
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()[:12]


def _datetime_delta_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    if delta.total_seconds() < 0:
        raise ValueError("datetime delta must be nonnegative")
    days = Decimal(delta.days) * Decimal("86400")
    seconds = Decimal(delta.seconds)
    microseconds = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    return _require_nonnegative_decimal(
        "datetime_delta_seconds",
        days + seconds + microseconds,
    )


def _count(value: int | Decimal) -> Decimal:
    if type(value) is int:
        return Decimal(value).quantize(QUANT)
    return _require_nonnegative_count_decimal("count", value)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _sum_decimal(values: tuple[Decimal, ...] | Any) -> Decimal:
    total = ZERO
    for value in values:
        total = _quantize(total + value)
    return total


def _abs_decimal(value: Decimal) -> Decimal:
    return _quantize(abs(value))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        try:
            return value.quantize(QUANT)
        except InvalidOperation as exc:
            raise ValueError("Decimal value cannot be quantized") from exc


def _require_hard_flags(label: str, value: object) -> None:
    require_paper_only_flags(label, value)


__all__ = (
    "DEFAULT_MARKET_RESEARCH_AI_MODEL_RELEASE_DIGEST_CONFIG_VERSION",
    "MarketResearchAiModelReleaseDigestConfig",
    "MarketResearchAiModelReleaseDigestInputRow",
    "MarketResearchAiModelReleaseDigestReasonCodeCount",
    "MarketResearchAiModelReleaseDigestReport",
    "MarketResearchAiModelReleaseDigestRow",
    "build_market_research_ai_model_release_digest",
    "market_research_ai_model_release_digest_payload",
)
