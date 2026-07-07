"""Pure report-only news coverage gap scoring for redacted research summaries."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_RESEARCH_NEWS_COVERAGE_GAP_SCORE_CONFIG_VERSION = (
    "research-news-coverage-gap-score-v0"
)

STATUSES = ("pass", "watch", "block")
ROW_REASON_CODES = (
    "news_coverage_low_source_diversity",
    "news_coverage_stale_public_coverage",
    "news_coverage_conflicting_summaries",
    "news_coverage_attention_gap",
)
REPORT_REASON_CODES = (
    "news_coverage_gap_empty",
    "news_coverage_gap_clear",
) + ROW_REASON_CODES
STATUS_RANK = {
    "block": Decimal("0"),
    "watch": Decimal("1"),
    "pass": Decimal("2"),
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
COUNT_ZERO = Decimal("0")
COUNT_QUANTUM = Decimal("1")
RATIO_ZERO = Decimal("0.000000")
RATIO_ONE = Decimal("1.000000")
RATIO_QUANTUM = Decimal("0.000001")
AGE_ZERO = Decimal("0.000000")
AGE_QUANTUM = Decimal("0.000001")
SHA256_LENGTH = 64


def _piece(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_SURFACE_FRAGMENTS = frozenset(
    (
        _piece("raw", "_", "candidate"),
        _piece("candidate", "_", "id"),
        "candidate",
        _piece("market", "_", "id"),
        _piece("market", "_", "slug"),
        _piece("market", "_", "question"),
        "question",
        _piece("source", "_", "ref"),
        _piece("source", "_", "url"),
        _piece("source", "_", "text"),
        "://",
        _piece("dsn"),
        _piece("table", "_", "name"),
        "table",
        _piece("tok", "en"),
        _piece("wal", "let"),
        _piece("au", "th"),
        _piece("ord", "er"),
        _piece("tra", "de"),
        _piece("pos", "ition"),
        _piece("buy"),
        _piece("sell"),
        _piece("reco", "mmend"),
    ),
)


@dataclass(frozen=True)
class ResearchNewsCoverageGapScoreConfig:
    config_version: str = DEFAULT_RESEARCH_NEWS_COVERAGE_GAP_SCORE_CONFIG_VERSION
    min_pass_source_family_count: Decimal = Decimal("3")
    min_watch_source_family_count: Decimal = Decimal("2")
    watch_source_age_seconds: Decimal = Decimal("86400.000000")
    block_source_age_seconds: Decimal = Decimal("259200.000000")
    watch_conflict_ratio: Decimal = Decimal("0.100000")
    block_conflict_ratio: Decimal = Decimal("0.500000")
    watch_attention_gap_ratio: Decimal = Decimal("0.250000")
    block_attention_gap_ratio: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchNewsCoverageGapScoreConfig does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchNewsCoverageGapScoreConfig:
            raise ValueError("config must be exactly ResearchNewsCoverageGapScoreConfig")
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_NEWS_COVERAGE_GAP_SCORE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_source_family_count",
            "min_watch_source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("watch_source_age_seconds", "block_source_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_age_seconds(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_conflict_ratio",
            "block_conflict_ratio",
            "watch_attention_gap_ratio",
            "block_attention_gap_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchNewsCoverageSummary:
    redacted_coverage_label: str
    public_topic_bucket: str
    source_family_count: Decimal
    fresh_source_count: Decimal
    total_summary_count: Decimal
    conflicting_summary_count: Decimal
    attention_baseline_count: Decimal
    coverage_mention_count: Decimal
    latest_source_age_seconds: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchNewsCoverageSummary does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchNewsCoverageSummary:
            raise ValueError("summary must be exactly ResearchNewsCoverageSummary")
        for field_name in ("redacted_coverage_label", "public_topic_bucket"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "source_family_count",
            "fresh_source_count",
            "total_summary_count",
            "conflicting_summary_count",
            "attention_baseline_count",
            "coverage_mention_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_source_age_seconds",
            _normalize_nonnegative_age_seconds(
                "latest_source_age_seconds",
                self.latest_source_age_seconds,
            ),
        )
        _validate_summary(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchNewsCoverageGapScoreReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchNewsCoverageGapScoreReasonCodeCount does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchNewsCoverageGapScoreReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchNewsCoverageGapScoreReasonCodeCount",
            )
        _require_member("reason_code", self.reason_code, ROW_REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_count("count", self.count),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchNewsCoverageGapScoreRow:
    redacted_coverage_label: str
    public_topic_bucket: str
    source_family_count: Decimal
    fresh_source_count: Decimal
    total_summary_count: Decimal
    conflicting_summary_count: Decimal
    attention_baseline_count: Decimal
    coverage_mention_count: Decimal
    latest_source_age_seconds: Decimal
    diversity_gap_ratio: Decimal
    freshness_gap_ratio: Decimal
    conflict_ratio: Decimal
    attention_gap_ratio: Decimal
    coverage_gap_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchNewsCoverageGapScoreRow does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchNewsCoverageGapScoreRow:
            raise ValueError("row must be exactly ResearchNewsCoverageGapScoreRow")
        for field_name in ("redacted_coverage_label", "public_topic_bucket"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "source_family_count",
            "fresh_source_count",
            "total_summary_count",
            "conflicting_summary_count",
            "attention_baseline_count",
            "coverage_mention_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_source_age_seconds",
            _normalize_nonnegative_age_seconds(
                "latest_source_age_seconds",
                self.latest_source_age_seconds,
            ),
        )
        for field_name in (
            "diversity_gap_ratio",
            "freshness_gap_ratio",
            "conflict_ratio",
            "attention_gap_ratio",
            "coverage_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchNewsCoverageGapScoreReport:
    generated_at: datetime
    config_version: str
    status: str
    summary_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    low_source_diversity_count: Decimal
    stale_coverage_count: Decimal
    conflict_count: Decimal
    attention_gap_count: Decimal
    max_attention_gap_ratio: Decimal
    max_conflict_ratio: Decimal
    max_coverage_gap_score: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchNewsCoverageGapScoreReasonCodeCount, ...]
    rows: tuple[ResearchNewsCoverageGapScoreRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchNewsCoverageGapScoreReport does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchNewsCoverageGapScoreReport:
            raise ValueError("report must be exactly ResearchNewsCoverageGapScoreReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_member("status", self.status, STATUSES)
        for field_name in (
            "summary_count",
            "pass_count",
            "watch_count",
            "block_count",
            "low_source_diversity_count",
            "stale_coverage_count",
            "conflict_count",
            "attention_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_attention_gap_ratio",
            "max_conflict_ratio",
            "max_coverage_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags(self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_sha256_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_report(self)


def build_research_news_coverage_gap_score_report(
    summaries: list[ResearchNewsCoverageSummary]
    | tuple[ResearchNewsCoverageSummary, ...],
    *,
    config: ResearchNewsCoverageGapScoreConfig,
    generated_at: datetime,
) -> ResearchNewsCoverageGapScoreReport:
    if type(config) is not ResearchNewsCoverageGapScoreConfig:
        raise ValueError("config must be a ResearchNewsCoverageGapScoreConfig")
    _require_hard_flags(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_summaries = _normalize_summaries(summaries)
    rows = tuple(
        sorted(
            (_row_from_summary(summary, config=config) for summary in normalized_summaries),
            key=_row_sort_key,
        ),
    )
    return ResearchNewsCoverageGapScoreReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(rows),
        summary_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        low_source_diversity_count=_reason_count(
            rows,
            "news_coverage_low_source_diversity",
        ),
        stale_coverage_count=_reason_count(
            rows,
            "news_coverage_stale_public_coverage",
        ),
        conflict_count=_reason_count(rows, "news_coverage_conflicting_summaries"),
        attention_gap_count=_reason_count(rows, "news_coverage_attention_gap"),
        max_attention_gap_ratio=max(
            (row.attention_gap_ratio for row in rows),
            default=RATIO_ZERO,
        ),
        max_conflict_ratio=max((row.conflict_ratio for row in rows), default=RATIO_ZERO),
        max_coverage_gap_score=max(
            (row.coverage_gap_score for row in rows),
            default=RATIO_ZERO,
        ),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_news_coverage_gap_score_report_payload(
    report: ResearchNewsCoverageGapScoreReport,
) -> dict[str, Any]:
    if type(report) is not ResearchNewsCoverageGapScoreReport:
        raise ValueError("report must be a ResearchNewsCoverageGapScoreReport")
    _validate_report(report)
    payload = _report_public_payload_for_digest(report)
    payload["derived_validation_digest"] = report.derived_validation_digest
    validate_research_news_coverage_gap_score_public_payload(payload)
    return payload


def validate_research_news_coverage_gap_score_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("research news coverage gap score payload", payload)
    _require_public_payload_flags(payload)
    _reject_public_numeric_values(payload)
    _require_public_payload_fields(payload)
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != _public_payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    return True


def _row_from_summary(
    summary: ResearchNewsCoverageSummary,
    *,
    config: ResearchNewsCoverageGapScoreConfig,
) -> ResearchNewsCoverageGapScoreRow:
    diversity_gap_ratio = _diversity_gap_ratio(summary, config)
    freshness_gap_ratio = _freshness_gap_ratio(summary, config)
    conflict_ratio = _ratio(
        summary.conflicting_summary_count,
        summary.total_summary_count,
    )
    attention_gap_ratio = _attention_gap_ratio(summary)
    coverage_gap_score = max(
        diversity_gap_ratio,
        freshness_gap_ratio,
        conflict_ratio,
        attention_gap_ratio,
    )
    reason_codes = _row_reason_codes(
        summary,
        conflict_ratio=conflict_ratio,
        attention_gap_ratio=attention_gap_ratio,
        config=config,
    )
    return ResearchNewsCoverageGapScoreRow(
        redacted_coverage_label=summary.redacted_coverage_label,
        public_topic_bucket=summary.public_topic_bucket,
        source_family_count=summary.source_family_count,
        fresh_source_count=summary.fresh_source_count,
        total_summary_count=summary.total_summary_count,
        conflicting_summary_count=summary.conflicting_summary_count,
        attention_baseline_count=summary.attention_baseline_count,
        coverage_mention_count=summary.coverage_mention_count,
        latest_source_age_seconds=summary.latest_source_age_seconds,
        diversity_gap_ratio=diversity_gap_ratio,
        freshness_gap_ratio=freshness_gap_ratio,
        conflict_ratio=conflict_ratio,
        attention_gap_ratio=attention_gap_ratio,
        coverage_gap_score=coverage_gap_score,
        status=_row_status(
            summary,
            conflict_ratio=conflict_ratio,
            attention_gap_ratio=attention_gap_ratio,
            config=config,
        ),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    summary: ResearchNewsCoverageSummary,
    *,
    conflict_ratio: Decimal,
    attention_gap_ratio: Decimal,
    config: ResearchNewsCoverageGapScoreConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if summary.source_family_count < config.min_pass_source_family_count:
        reason_codes.append("news_coverage_low_source_diversity")
    if (
        summary.fresh_source_count == COUNT_ZERO
        or summary.latest_source_age_seconds >= config.watch_source_age_seconds
    ):
        reason_codes.append("news_coverage_stale_public_coverage")
    if conflict_ratio >= config.watch_conflict_ratio:
        reason_codes.append("news_coverage_conflicting_summaries")
    if attention_gap_ratio >= config.watch_attention_gap_ratio:
        reason_codes.append("news_coverage_attention_gap")
    return tuple(reason_codes)


def _row_status(
    summary: ResearchNewsCoverageSummary,
    *,
    conflict_ratio: Decimal,
    attention_gap_ratio: Decimal,
    config: ResearchNewsCoverageGapScoreConfig,
) -> str:
    if (
        summary.source_family_count < config.min_watch_source_family_count
        or summary.fresh_source_count == COUNT_ZERO
        or summary.latest_source_age_seconds >= config.block_source_age_seconds
        or conflict_ratio >= config.block_conflict_ratio
        or attention_gap_ratio >= config.block_attention_gap_ratio
    ):
        return "block"
    if _row_reason_codes(
        summary,
        conflict_ratio=conflict_ratio,
        attention_gap_ratio=attention_gap_ratio,
        config=config,
    ):
        return "watch"
    return "pass"


def _diversity_gap_ratio(
    summary: ResearchNewsCoverageSummary,
    config: ResearchNewsCoverageGapScoreConfig,
) -> Decimal:
    missing = config.min_pass_source_family_count - summary.source_family_count
    if missing <= COUNT_ZERO:
        return RATIO_ZERO
    return _ratio(missing, config.min_pass_source_family_count)


def _freshness_gap_ratio(
    summary: ResearchNewsCoverageSummary,
    config: ResearchNewsCoverageGapScoreConfig,
) -> Decimal:
    if summary.fresh_source_count == COUNT_ZERO:
        return RATIO_ONE
    return min(_ratio(summary.latest_source_age_seconds, config.block_source_age_seconds), RATIO_ONE)


def _attention_gap_ratio(summary: ResearchNewsCoverageSummary) -> Decimal:
    missing = summary.attention_baseline_count - summary.coverage_mention_count
    if missing <= COUNT_ZERO:
        return RATIO_ZERO
    return _ratio(missing, summary.attention_baseline_count)


def _report_status(rows: tuple[ResearchNewsCoverageGapScoreRow, ...]) -> str:
    statuses = tuple(row.status for row in rows)
    if "block" in statuses:
        return "block"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _report_reason_codes(rows: tuple[ResearchNewsCoverageGapScoreRow, ...]) -> tuple[str, ...]:
    if not rows:
        return ("news_coverage_gap_empty",)
    present = frozenset(reason_code for row in rows for reason_code in row.reason_codes)
    if not present:
        return ("news_coverage_gap_clear",)
    return tuple(reason_code for reason_code in ROW_REASON_CODES if reason_code in present)


def _reason_code_counts(
    rows: tuple[ResearchNewsCoverageGapScoreRow, ...],
) -> tuple[ResearchNewsCoverageGapScoreReasonCodeCount, ...]:
    return tuple(
        ResearchNewsCoverageGapScoreReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(rows, reason_code),
        )
        for reason_code in ROW_REASON_CODES
        if _reason_count(rows, reason_code) > COUNT_ZERO
    )


def _normalize_summaries(value: object) -> tuple[ResearchNewsCoverageSummary, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("summaries must be a list or tuple")
    summaries = tuple(value)
    seen: set[tuple[str, str]] = set()
    for item in summaries:
        if type(item) is not ResearchNewsCoverageSummary:
            raise ValueError("summaries must contain ResearchNewsCoverageSummary values")
        _require_hard_flags(item)
        key = _summary_key(item)
        if key in seen:
            raise ValueError("summaries must not contain duplicate redacted coverage labels")
        seen.add(key)
    return summaries


def _normalize_rows(value: object) -> tuple[ResearchNewsCoverageGapScoreRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchNewsCoverageGapScoreRow:
            raise ValueError("rows must contain ResearchNewsCoverageGapScoreRow values")
        _require_hard_flags(row)
        key = _row_key(row)
        if key in seen:
            raise ValueError("rows must not contain duplicate coverage gap entries")
        seen.add(key)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchNewsCoverageGapScoreReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    seen: set[str] = set()
    for item in counts:
        if type(item) is not ResearchNewsCoverageGapScoreReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchNewsCoverageGapScoreReasonCodeCount values",
            )
        _require_hard_flags(item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(item.reason_code)
    expected = tuple(
        item
        for reason_code in ROW_REASON_CODES
        for item in counts
        if item.reason_code == reason_code
    )
    if counts != expected:
        raise ValueError("reason_code_counts must use deterministic sequence")
    return counts


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_member(field_name, reason_code, allowed_values)
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(reason_code)
    expected = tuple(reason_code for reason_code in allowed_values if reason_code in seen)
    if reason_codes != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return reason_codes


def _validate_config(config: ResearchNewsCoverageGapScoreConfig) -> None:
    if config.min_watch_source_family_count > config.min_pass_source_family_count:
        raise ValueError(
            "min_watch_source_family_count must not exceed "
            "min_pass_source_family_count",
        )
    if config.watch_source_age_seconds > config.block_source_age_seconds:
        raise ValueError("watch_source_age_seconds must not exceed block_source_age_seconds")
    if config.watch_conflict_ratio > config.block_conflict_ratio:
        raise ValueError("watch_conflict_ratio must not exceed block_conflict_ratio")
    if config.watch_attention_gap_ratio > config.block_attention_gap_ratio:
        raise ValueError(
            "watch_attention_gap_ratio must not exceed block_attention_gap_ratio",
        )


def _validate_summary(summary: ResearchNewsCoverageSummary) -> None:
    if summary.fresh_source_count > summary.source_family_count:
        raise ValueError("fresh_source_count must not exceed source_family_count")
    if summary.conflicting_summary_count > summary.total_summary_count:
        raise ValueError("conflicting_summary_count must not exceed total_summary_count")


def _validate_row(row: ResearchNewsCoverageGapScoreRow) -> None:
    if row.fresh_source_count > row.source_family_count:
        raise ValueError("fresh_source_count must not exceed source_family_count")
    if row.conflicting_summary_count > row.total_summary_count:
        raise ValueError("conflicting_summary_count must not exceed total_summary_count")
    if row.reason_codes and row.status == "pass":
        raise ValueError("pass rows must not carry reason_codes")
    if not row.reason_codes and row.status != "pass":
        raise ValueError("non-pass rows must carry reason_codes")
    if row.coverage_gap_score != max(
        row.diversity_gap_ratio,
        row.freshness_gap_ratio,
        row.conflict_ratio,
        row.attention_gap_ratio,
    ):
        raise ValueError("coverage_gap_score must match component ratios")


def _validate_report(report: ResearchNewsCoverageGapScoreReport) -> None:
    _require_hard_flags(report)
    rows = report.rows
    expected_values = {
        "status": _report_status(rows),
        "summary_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "low_source_diversity_count": _reason_count(
            rows,
            "news_coverage_low_source_diversity",
        ),
        "stale_coverage_count": _reason_count(
            rows,
            "news_coverage_stale_public_coverage",
        ),
        "conflict_count": _reason_count(rows, "news_coverage_conflicting_summaries"),
        "attention_gap_count": _reason_count(rows, "news_coverage_attention_gap"),
        "max_attention_gap_ratio": max(
            (row.attention_gap_ratio for row in rows),
            default=RATIO_ZERO,
        ),
        "max_conflict_ratio": max((row.conflict_ratio for row in rows), default=RATIO_ZERO),
        "max_coverage_gap_score": max(
            (row.coverage_gap_score for row in rows),
            default=RATIO_ZERO,
        ),
        "reason_codes": _report_reason_codes(rows),
        "reason_code_counts": _reason_code_counts(rows),
    }
    for field_name, expected_value in expected_values.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match report rows")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report payload")


def _summary_key(summary: ResearchNewsCoverageSummary) -> tuple[str, str]:
    return (summary.public_topic_bucket, summary.redacted_coverage_label)


def _row_key(row: ResearchNewsCoverageGapScoreRow) -> tuple[str, str]:
    return (row.public_topic_bucket, row.redacted_coverage_label)


def _row_sort_key(
    row: ResearchNewsCoverageGapScoreRow,
) -> tuple[Decimal, str, str]:
    return (
        STATUS_RANK[row.status],
        row.public_topic_bucket,
        row.redacted_coverage_label,
    )


def _status_count(rows: tuple[ResearchNewsCoverageGapScoreRow, ...], status: str) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchNewsCoverageGapScoreRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _report_public_payload_for_digest(
    report: ResearchNewsCoverageGapScoreReport,
) -> dict[str, Any]:
    return {
        "generated_at": _datetime_to_public_string(report.generated_at),
        "config_version": report.config_version,
        "status": report.status,
        "summary_count": _decimal_to_public_string(report.summary_count),
        "pass_count": _decimal_to_public_string(report.pass_count),
        "watch_count": _decimal_to_public_string(report.watch_count),
        "block_count": _decimal_to_public_string(report.block_count),
        "low_source_diversity_count": _decimal_to_public_string(
            report.low_source_diversity_count,
        ),
        "stale_coverage_count": _decimal_to_public_string(report.stale_coverage_count),
        "conflict_count": _decimal_to_public_string(report.conflict_count),
        "attention_gap_count": _decimal_to_public_string(report.attention_gap_count),
        "max_attention_gap_ratio": _decimal_to_public_string(
            report.max_attention_gap_ratio,
        ),
        "max_conflict_ratio": _decimal_to_public_string(report.max_conflict_ratio),
        "max_coverage_gap_score": _decimal_to_public_string(
            report.max_coverage_gap_score,
        ),
        "reason_codes": list(report.reason_codes),
        "reason_code_counts": [
            _reason_code_count_payload(item) for item in report.reason_code_counts
        ],
        "rows": [_row_payload(row) for row in report.rows],
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _row_payload(row: ResearchNewsCoverageGapScoreRow) -> dict[str, Any]:
    return {
        "redacted_coverage_label": row.redacted_coverage_label,
        "public_topic_bucket": row.public_topic_bucket,
        "source_family_count": _decimal_to_public_string(row.source_family_count),
        "fresh_source_count": _decimal_to_public_string(row.fresh_source_count),
        "total_summary_count": _decimal_to_public_string(row.total_summary_count),
        "conflicting_summary_count": _decimal_to_public_string(
            row.conflicting_summary_count,
        ),
        "attention_baseline_count": _decimal_to_public_string(
            row.attention_baseline_count,
        ),
        "coverage_mention_count": _decimal_to_public_string(row.coverage_mention_count),
        "latest_source_age_seconds": _decimal_to_public_string(
            row.latest_source_age_seconds,
        ),
        "diversity_gap_ratio": _decimal_to_public_string(row.diversity_gap_ratio),
        "freshness_gap_ratio": _decimal_to_public_string(row.freshness_gap_ratio),
        "conflict_ratio": _decimal_to_public_string(row.conflict_ratio),
        "attention_gap_ratio": _decimal_to_public_string(row.attention_gap_ratio),
        "coverage_gap_score": _decimal_to_public_string(row.coverage_gap_score),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _reason_code_count_payload(
    item: ResearchNewsCoverageGapScoreReasonCodeCount,
) -> dict[str, Any]:
    return {
        "reason_code": item.reason_code,
        "count": _decimal_to_public_string(item.count),
        "paper_only": item.paper_only,
        "report_only": item.report_only,
        "readonly": item.readonly,
    }


def _report_derived_validation_digest(
    report: ResearchNewsCoverageGapScoreReport,
) -> str:
    return _public_payload_derived_validation_digest(
        _report_public_payload_for_digest(report),
    )


def _public_payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _require_public_payload_fields(payload: dict[str, Any]) -> None:
    for key in (
        "generated_at",
        "config_version",
        "status",
        "summary_count",
        "pass_count",
        "watch_count",
        "block_count",
        "low_source_diversity_count",
        "stale_coverage_count",
        "conflict_count",
        "attention_gap_count",
        "max_attention_gap_ratio",
        "max_conflict_ratio",
        "max_coverage_gap_score",
        "reason_codes",
        "reason_code_counts",
        "rows",
        "paper_only",
        "report_only",
        "readonly",
    ):
        if key not in payload:
            raise ValueError(f"{key} is required")
    _require_member("status", _payload_required_string(payload, "status"), STATUSES)
    _validate_public_reason_codes(payload["reason_codes"], REPORT_REASON_CODES)
    _validate_public_reason_code_counts(payload["reason_code_counts"])
    if type(payload["rows"]) is not list:
        raise ValueError("rows must be a list")
    for row in payload["rows"]:
        _validate_public_row_payload(row)


def _validate_public_row_payload(value: object) -> None:
    if type(value) is not dict:
        raise ValueError("row must be a dict")
    row = value
    for key in (
        "redacted_coverage_label",
        "public_topic_bucket",
        "source_family_count",
        "fresh_source_count",
        "total_summary_count",
        "conflicting_summary_count",
        "attention_baseline_count",
        "coverage_mention_count",
        "latest_source_age_seconds",
        "diversity_gap_ratio",
        "freshness_gap_ratio",
        "conflict_ratio",
        "attention_gap_ratio",
        "coverage_gap_score",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ):
        if key not in row:
            raise ValueError(f"row.{key} is required")
    _require_member("row.status", _payload_required_string(row, "status"), STATUSES)
    _validate_public_reason_codes(row["reason_codes"], ROW_REASON_CODES)
    _require_public_payload_flags(row)


def _validate_public_reason_code_counts(value: object) -> None:
    if type(value) is not list:
        raise ValueError("reason_code_counts must be a list")
    seen: set[str] = set()
    for item in value:
        if type(item) is not dict:
            raise ValueError("reason_code_counts must contain dict values")
        reason_code = _payload_required_string(item, "reason_code")
        _require_member("reason_code", reason_code, ROW_REASON_CODES)
        if reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(reason_code)
        if "count" not in item:
            raise ValueError("reason_code_counts.count is required")
        _require_public_payload_flags(item)


def _validate_public_reason_codes(
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not list:
        raise ValueError("reason_codes must be a list")
    seen: set[str] = set()
    reason_codes = tuple(value)
    for reason_code in reason_codes:
        _require_member("reason_codes", reason_code, allowed_values)
        if reason_code in seen:
            raise ValueError("reason_codes must not contain duplicates")
        seen.add(reason_code)
    expected = tuple(reason_code for reason_code in allowed_values if reason_code in seen)
    if reason_codes != expected:
        raise ValueError("reason_codes must use deterministic sequence")


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
) -> None:
    current_path = path or label
    if type(value) is str:
        _reject_unsafe_text(current_path, value)
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{current_path} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{current_path} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{current_path} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{current_path} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float) or type(value) is int:
        raise ValueError(f"{current_path} must use Decimal strings")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            _reject_unsafe_text(nested_path, key)
            if key in ("paper_only", "report_only", "readonly") and item is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    if type(value) in (list, tuple):
        for index, item in enumerate(value):
            nested_path = f"{current_path}[{index}]"
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    raise ValueError(f"{current_path} is not JSON-ready")


def _reject_unsafe_text(context: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{context} must be a string")
    if value.strip() != value or value == "":
        raise ValueError(f"{context} contains unsafe public surface")
    if any(ord(character) < 32 for character in value):
        raise ValueError(f"{context} contains unsafe public surface")
    lowered = value.casefold()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_SURFACE_FRAGMENTS):
        raise ValueError(f"{context} contains unsafe public surface")


def _reject_public_numeric_values(value: object, path: str = "") -> None:
    if value is None or type(value) is bool:
        return
    if isinstance(value, (Decimal, int, float)):
        raise ValueError(
            f"public payload must use Decimal strings, not numeric values at {path}",
        )
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            _reject_public_numeric_values(item, nested_path)
    elif type(value) is list:
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]"
            _reject_public_numeric_values(item, nested_path)


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _reject_unsafe_text(field_name, value)
    return value


def _payload_required_string(payload: dict[str, Any], key: str) -> str:
    if key not in payload:
        raise ValueError(f"{key} is required")
    value = payload[key]
    if type(value) is not str:
        raise ValueError(f"{key} must be a string")
    _reject_unsafe_text(key, value)
    return value


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")
    return value


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < COUNT_ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    normalized = decimal_value.quantize(COUNT_QUANTUM, context=DECIMAL_CONTEXT)
    if normalized != decimal_value:
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_count(field_name, value)
    if decimal_value <= COUNT_ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_nonnegative_age_seconds(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < AGE_ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value.quantize(AGE_QUANTUM, context=DECIMAL_CONTEXT)


def _normalize_positive_age_seconds(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_age_seconds(field_name, value)
    if decimal_value <= AGE_ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < RATIO_ZERO or decimal_value > RATIO_ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value.quantize(RATIO_QUANTUM, context=DECIMAL_CONTEXT)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM, context=DECIMAL_CONTEXT)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == COUNT_ZERO:
        return RATIO_ZERO
    with localcontext(DECIMAL_CONTEXT):
        value = numerator / denominator
    if value < RATIO_ZERO:
        value = RATIO_ZERO
    if value > RATIO_ONE:
        value = RATIO_ONE
    return value.quantize(RATIO_QUANTUM, context=DECIMAL_CONTEXT)


def _decimal_to_public_string(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("public Decimal values must be exactly Decimal")
    if not value.is_finite():
        raise ValueError("public Decimal values must be finite")
    return format(value, "f")


def _datetime_to_public_string(value: datetime) -> str:
    return _as_utc("datetime", value).isoformat()


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    lowered = value.casefold()
    if lowered != value or len(value) != SHA256_LENGTH:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value
