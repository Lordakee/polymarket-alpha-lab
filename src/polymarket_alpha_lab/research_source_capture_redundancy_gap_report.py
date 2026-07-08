"""Pure report-only aggregate source capture redundancy gap report."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_SOURCE_CAPTURE_REDUNDANCY_GAP_REPORT_CONFIG_VERSION = (
    "source-capture-redundancy-gap-report-v0"
)

QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

STATUSES = ("pass", "watch", "block")
REASON_CODES = (
    "empty_capture_set",
    "capture_redundancy_gap_block",
    "capture_redundancy_gap_watch",
    "source_family_imbalance_block",
    "source_family_imbalance_watch",
    "freshness_gap_block",
    "freshness_gap_watch",
    "contradiction_pressure_block",
    "contradiction_pressure_watch",
    "source_capture_redundancy_gap_block",
    "source_capture_redundancy_gap_watch",
    "source_capture_redundancy_gap_pass",
)
PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "candidate_id",
    "market_id",
    "slug",
    "question",
    "url",
    "source_text",
    "dsn",
    "table_name",
    "token",
    "wallet",
    "order",
    "trade",
    "sizing",
    "recommendation",
    "auth",
    "database",
    "network",
    "live",
)
UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "candidate",
    "market",
    "slug",
    "question",
    "://",
    "www.",
    "url",
    "source_text",
    "source text",
    "dsn",
    "postgres",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "sizing",
    "recommendation",
    "auth",
    "database",
    "network",
    "live",
    "secret",
    "password",
    "private_key",
    "api_key",
)


@dataclass(frozen=True)
class ResearchSourceCaptureRedundancyGapConfig:
    config_version: str = DEFAULT_RESEARCH_SOURCE_CAPTURE_REDUNDANCY_GAP_REPORT_CONFIG_VERSION
    min_capture_count: Decimal = Decimal("2")
    min_source_family_count: Decimal = Decimal("2")
    max_dominant_source_family_share: Decimal = Decimal("0.750000")
    max_capture_age_seconds: Decimal = Decimal("3600.000000")
    watch_contradiction_pressure: Decimal = Decimal("0.350000")
    block_contradiction_pressure: Decimal = Decimal("0.700000")
    watch_gap_pressure_score: Decimal = Decimal("0.250000")
    block_gap_pressure_score: Decimal = Decimal("0.600000")
    redundancy_gap_weight: Decimal = Decimal("0.300000")
    source_family_imbalance_weight: Decimal = Decimal("0.250000")
    freshness_gap_weight: Decimal = Decimal("0.200000")
    contradiction_pressure_weight: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceCaptureRedundancyGapConfig:
            raise TypeError(
                "ResearchSourceCaptureRedundancyGapConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceCaptureRedundancyGapConfig:
            raise ValueError(
                "config must be exactly ResearchSourceCaptureRedundancyGapConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_CAPTURE_REDUNDANCY_GAP_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("min_capture_count", "min_source_family_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_capture_age_seconds",
            _normalize_positive_decimal(
                "max_capture_age_seconds",
                self.max_capture_age_seconds,
            ),
        )
        for field_name in (
            "max_dominant_source_family_share",
            "watch_contradiction_pressure",
            "block_contradiction_pressure",
            "watch_gap_pressure_score",
            "block_gap_pressure_score",
            "redundancy_gap_weight",
            "source_family_imbalance_weight",
            "freshness_gap_weight",
            "contradiction_pressure_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.block_contradiction_pressure <= self.watch_contradiction_pressure:
            raise ValueError(
                "block_contradiction_pressure must exceed watch_contradiction_pressure",
            )
        if self.block_gap_pressure_score <= self.watch_gap_pressure_score:
            raise ValueError(
                "block_gap_pressure_score must exceed watch_gap_pressure_score",
            )
        if (
            self.redundancy_gap_weight
            + self.source_family_imbalance_weight
            + self.freshness_gap_weight
            + self.contradiction_pressure_weight
        ) != ONE:
            raise ValueError("gap pressure weights must sum to one")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceCaptureRecord:
    capture_group: str
    source_family: str
    captured_at: datetime
    contradiction_pressure: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceCaptureRecord:
            raise TypeError("ResearchSourceCaptureRecord does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceCaptureRecord:
            raise ValueError("record must be exactly ResearchSourceCaptureRecord")
        _require_public_identifier("capture_group", self.capture_group)
        _require_public_identifier("source_family", self.source_family)
        object.__setattr__(self, "captured_at", _as_utc("captured_at", self.captured_at))
        object.__setattr__(
            self,
            "contradiction_pressure",
            _normalize_probability(
                "contradiction_pressure",
                self.contradiction_pressure,
            ),
        )
        _require_hard_flags("record", self)
        _reject_unsafe_public_payload("record", self)


@dataclass(frozen=True)
class ResearchSourceCaptureRedundancyGapReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceCaptureRedundancyGapReasonCodeCount:
            raise TypeError(
                "ResearchSourceCaptureRedundancyGapReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceCaptureRedundancyGapReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "ResearchSourceCaptureRedundancyGapReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_count("count", self.count),
        )
        _require_hard_flags("reason count", self)
        _reject_unsafe_public_payload("reason count", self)


@dataclass(frozen=True)
class ResearchSourceCaptureRedundancyGapReport:
    generated_at: datetime
    config_version: str
    status: str
    capture_group_count: Decimal
    capture_count: Decimal
    under_redundant_capture_group_count: Decimal
    source_family_imbalance_group_count: Decimal
    stale_capture_group_count: Decimal
    stale_capture_count: Decimal
    contradiction_pressure_group_count: Decimal
    max_capture_age_seconds: Decimal
    max_dominant_source_family_share: Decimal
    max_contradiction_pressure: Decimal
    redundancy_gap_ratio: Decimal
    source_family_imbalance_ratio: Decimal
    freshness_gap_ratio: Decimal
    contradiction_pressure_ratio: Decimal
    gap_pressure_score: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchSourceCaptureRedundancyGapReasonCodeCount, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceCaptureRedundancyGapReport:
            raise TypeError(
                "ResearchSourceCaptureRedundancyGapReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceCaptureRedundancyGapReport:
            raise ValueError(
                "report must be exactly ResearchSourceCaptureRedundancyGapReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_CAPTURE_REDUNDANCY_GAP_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in (
            "capture_group_count",
            "capture_count",
            "under_redundant_capture_group_count",
            "source_family_imbalance_group_count",
            "stale_capture_group_count",
            "stale_capture_count",
            "contradiction_pressure_group_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_capture_age_seconds",):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_dominant_source_family_share",
            "max_contradiction_pressure",
            "redundancy_gap_ratio",
            "source_family_imbalance_ratio",
            "freshness_gap_ratio",
            "contradiction_pressure_ratio",
            "gap_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload(
            "ResearchSourceCaptureRedundancyGapReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


@dataclass(frozen=True)
class _CaptureGroupSummary:
    capture_count: Decimal
    source_family_count: Decimal
    stale_capture_count: Decimal
    newest_capture_age_seconds: Decimal
    max_capture_age_seconds: Decimal
    dominant_source_family_share: Decimal
    max_contradiction_pressure: Decimal


def build_research_source_capture_redundancy_gap_report(
    captures: Iterable[ResearchSourceCaptureRecord],
    *,
    config: ResearchSourceCaptureRedundancyGapConfig | None = None,
    generated_at: datetime,
) -> ResearchSourceCaptureRedundancyGapReport:
    """Build a local, aggregate-only source capture redundancy gap report."""

    if config is None:
        config = ResearchSourceCaptureRedundancyGapConfig()
    if type(config) is not ResearchSourceCaptureRedundancyGapConfig:
        raise ValueError("config must be a ResearchSourceCaptureRedundancyGapConfig")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_captures = _normalize_captures(captures)
    for item in normalized_captures:
        if item.captured_at > generated_at:
            raise ValueError("captured_at must not be after generated_at")
    summaries = _capture_group_summaries(
        normalized_captures,
        generated_at=generated_at,
        config=config,
    )
    group_count = _count_decimal(len(summaries))
    capture_count = _count_decimal(len(normalized_captures))
    under_redundant_group_count = _count_decimal(
        sum(
            1
            for summary in summaries
            if summary.capture_count < config.min_capture_count
        ),
    )
    source_family_imbalance_group_count = _count_decimal(
        sum(1 for summary in summaries if _has_source_family_imbalance(summary, config)),
    )
    stale_capture_group_count = _count_decimal(
        sum(
            1
            for summary in summaries
            if summary.newest_capture_age_seconds > config.max_capture_age_seconds
        ),
    )
    stale_capture_count = _sum_decimals(
        tuple(summary.stale_capture_count for summary in summaries),
    )
    contradiction_pressure_group_count = _count_decimal(
        sum(
            1
            for summary in summaries
            if summary.max_contradiction_pressure >= config.watch_contradiction_pressure
        ),
    )
    max_capture_age_seconds = max(
        (summary.max_capture_age_seconds for summary in summaries),
        default=ZERO,
    )
    max_dominant_source_family_share = max(
        (summary.dominant_source_family_share for summary in summaries),
        default=ZERO,
    )
    max_contradiction_pressure = max(
        (summary.max_contradiction_pressure for summary in summaries),
        default=ZERO,
    )
    redundancy_gap_ratio = _ratio(under_redundant_group_count, group_count)
    source_family_imbalance_ratio = _ratio(
        source_family_imbalance_group_count,
        group_count,
    )
    freshness_gap_ratio = _ratio(stale_capture_group_count, group_count)
    contradiction_pressure_ratio = _average(
        tuple(summary.max_contradiction_pressure for summary in summaries),
    )
    gap_pressure_score = _gap_pressure_score(
        redundancy_gap_ratio=redundancy_gap_ratio,
        source_family_imbalance_ratio=source_family_imbalance_ratio,
        freshness_gap_ratio=freshness_gap_ratio,
        contradiction_pressure_ratio=contradiction_pressure_ratio,
        config=config,
    )
    status = _status_from_gap_pressure(
        gap_pressure_score=gap_pressure_score,
        group_count=group_count,
        config=config,
    )
    reason_codes = _report_reason_codes(
        status=status,
        group_count=group_count,
        under_redundant_capture_group_count=under_redundant_group_count,
        source_family_imbalance_group_count=source_family_imbalance_group_count,
        stale_capture_group_count=stale_capture_group_count,
        contradiction_pressure_group_count=contradiction_pressure_group_count,
        max_contradiction_pressure=max_contradiction_pressure,
        redundancy_gap_ratio=redundancy_gap_ratio,
        source_family_imbalance_ratio=source_family_imbalance_ratio,
        freshness_gap_ratio=freshness_gap_ratio,
        config=config,
    )
    reason_code_counts = _reason_code_counts(reason_codes)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "status": status,
        "capture_group_count": group_count,
        "capture_count": capture_count,
        "under_redundant_capture_group_count": under_redundant_group_count,
        "source_family_imbalance_group_count": source_family_imbalance_group_count,
        "stale_capture_group_count": stale_capture_group_count,
        "stale_capture_count": stale_capture_count,
        "contradiction_pressure_group_count": contradiction_pressure_group_count,
        "max_capture_age_seconds": max_capture_age_seconds,
        "max_dominant_source_family_share": max_dominant_source_family_share,
        "max_contradiction_pressure": max_contradiction_pressure,
        "redundancy_gap_ratio": redundancy_gap_ratio,
        "source_family_imbalance_ratio": source_family_imbalance_ratio,
        "freshness_gap_ratio": freshness_gap_ratio,
        "contradiction_pressure_ratio": contradiction_pressure_ratio,
        "gap_pressure_score": gap_pressure_score,
        "reason_codes": reason_codes,
        "reason_code_counts": reason_code_counts,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSourceCaptureRedundancyGapReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_source_capture_redundancy_gap_report_payload(
    report: ResearchSourceCaptureRedundancyGapReport,
) -> dict[str, object]:
    if type(report) is not ResearchSourceCaptureRedundancyGapReport:
        raise ValueError("report must be a ResearchSourceCaptureRedundancyGapReport")
    _require_hard_flags("report", report)
    return report.payload


def research_source_capture_redundancy_gap_report_digest(
    report: ResearchSourceCaptureRedundancyGapReport,
) -> str:
    if type(report) is not ResearchSourceCaptureRedundancyGapReport:
        raise ValueError("report must be a ResearchSourceCaptureRedundancyGapReport")
    _require_hard_flags("report", report)
    return _report_digest_from_values(_report_values_without_digest(report))


def _capture_group_summaries(
    captures: tuple[ResearchSourceCaptureRecord, ...],
    *,
    generated_at: datetime,
    config: ResearchSourceCaptureRedundancyGapConfig,
) -> tuple[_CaptureGroupSummary, ...]:
    grouped: dict[str, list[ResearchSourceCaptureRecord]] = {}
    for item in captures:
        grouped.setdefault(item.capture_group, []).append(item)
    summaries: list[_CaptureGroupSummary] = []
    for capture_group in sorted(grouped):
        items = tuple(
            sorted(
                grouped[capture_group],
                key=lambda item: (item.captured_at, item.source_family),
            ),
        )
        age_seconds = tuple(
            _seconds_between(generated_at, item.captured_at) for item in items
        )
        family_counts: dict[str, int] = {}
        for item in items:
            family_counts[item.source_family] = family_counts.get(item.source_family, 0) + 1
        capture_count = _count_decimal(len(items))
        dominant_family_count = _count_decimal(max(family_counts.values(), default=0))
        summaries.append(
            _CaptureGroupSummary(
                capture_count=capture_count,
                source_family_count=_count_decimal(len(family_counts)),
                stale_capture_count=_count_decimal(
                    sum(1 for age in age_seconds if age > config.max_capture_age_seconds),
                ),
                newest_capture_age_seconds=min(age_seconds, default=ZERO),
                max_capture_age_seconds=max(age_seconds, default=ZERO),
                dominant_source_family_share=_ratio(
                    dominant_family_count,
                    capture_count,
                ),
                max_contradiction_pressure=max(
                    (item.contradiction_pressure for item in items),
                    default=ZERO,
                ),
            ),
        )
    return tuple(summaries)


def _has_source_family_imbalance(
    summary: _CaptureGroupSummary,
    config: ResearchSourceCaptureRedundancyGapConfig,
) -> bool:
    return (
        summary.source_family_count < config.min_source_family_count
        or summary.dominant_source_family_share > config.max_dominant_source_family_share
    )


def _gap_pressure_score(
    *,
    redundancy_gap_ratio: Decimal,
    source_family_imbalance_ratio: Decimal,
    freshness_gap_ratio: Decimal,
    contradiction_pressure_ratio: Decimal,
    config: ResearchSourceCaptureRedundancyGapConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            redundancy_gap_ratio * config.redundancy_gap_weight
            + source_family_imbalance_ratio * config.source_family_imbalance_weight
            + freshness_gap_ratio * config.freshness_gap_weight
            + contradiction_pressure_ratio * config.contradiction_pressure_weight
        )
    return _normalize_probability("gap_pressure_score", score)


def _status_from_gap_pressure(
    *,
    gap_pressure_score: Decimal,
    group_count: Decimal,
    config: ResearchSourceCaptureRedundancyGapConfig,
) -> str:
    if group_count == ZERO:
        return "block"
    if gap_pressure_score >= config.block_gap_pressure_score:
        return "block"
    if gap_pressure_score >= config.watch_gap_pressure_score:
        return "watch"
    return "pass"


def _report_reason_codes(
    *,
    status: str,
    group_count: Decimal,
    under_redundant_capture_group_count: Decimal,
    source_family_imbalance_group_count: Decimal,
    stale_capture_group_count: Decimal,
    contradiction_pressure_group_count: Decimal,
    max_contradiction_pressure: Decimal,
    redundancy_gap_ratio: Decimal,
    source_family_imbalance_ratio: Decimal,
    freshness_gap_ratio: Decimal,
    config: ResearchSourceCaptureRedundancyGapConfig,
) -> tuple[str, ...]:
    if group_count == ZERO:
        return ("empty_capture_set", "source_capture_redundancy_gap_block")
    reason_codes: list[str] = []
    if under_redundant_capture_group_count > ZERO:
        if redundancy_gap_ratio >= config.block_gap_pressure_score:
            reason_codes.append("capture_redundancy_gap_block")
        else:
            reason_codes.append("capture_redundancy_gap_watch")
    if source_family_imbalance_group_count > ZERO:
        if source_family_imbalance_ratio >= config.block_gap_pressure_score:
            reason_codes.append("source_family_imbalance_block")
        else:
            reason_codes.append("source_family_imbalance_watch")
    if stale_capture_group_count > ZERO:
        if freshness_gap_ratio >= config.block_gap_pressure_score:
            reason_codes.append("freshness_gap_block")
        else:
            reason_codes.append("freshness_gap_watch")
    if contradiction_pressure_group_count > ZERO:
        if max_contradiction_pressure >= config.block_contradiction_pressure:
            reason_codes.append("contradiction_pressure_block")
        else:
            reason_codes.append("contradiction_pressure_watch")
    reason_codes.append(f"source_capture_redundancy_gap_{status}")
    return _normalize_reason_codes(tuple(reason_codes))


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[ResearchSourceCaptureRedundancyGapReasonCodeCount, ...]:
    return tuple(
        ResearchSourceCaptureRedundancyGapReasonCodeCount(
            reason_code=reason_code,
            count=COUNT_QUANTUM,
        )
        for reason_code in reason_codes
    )


def _validate_report_consistency(
    report: ResearchSourceCaptureRedundancyGapReport,
) -> None:
    if report.capture_group_count == ZERO:
        if report.status != "block":
            raise ValueError("empty reports must use block status")
        if "empty_capture_set" not in report.reason_codes:
            raise ValueError("empty reports must include empty_capture_set")
    if report.capture_count < report.capture_group_count:
        raise ValueError("capture_count must be at least capture_group_count")
    for field_name in (
        "under_redundant_capture_group_count",
        "source_family_imbalance_group_count",
        "stale_capture_group_count",
        "contradiction_pressure_group_count",
    ):
        if getattr(report, field_name) > report.capture_group_count:
            raise ValueError(f"{field_name} must not exceed capture_group_count")
    if report.stale_capture_count > report.capture_count:
        raise ValueError("stale_capture_count must not exceed capture_count")
    expected_reason_code_counts = _reason_code_counts(report.reason_codes)
    if report.reason_code_counts != expected_reason_code_counts:
        raise ValueError("reason_code_counts must match reason_codes")
    if report.status == "pass" and "source_capture_redundancy_gap_pass" not in report.reason_codes:
        raise ValueError("pass reports must include pass reason code")
    if report.status == "watch" and "source_capture_redundancy_gap_watch" not in report.reason_codes:
        raise ValueError("watch reports must include watch reason code")
    if report.status == "block" and "source_capture_redundancy_gap_block" not in report.reason_codes:
        raise ValueError("block reports must include block reason code")


def _normalize_captures(
    captures: Iterable[ResearchSourceCaptureRecord],
) -> tuple[ResearchSourceCaptureRecord, ...]:
    if isinstance(captures, (str, bytes)) or not isinstance(captures, Iterable):
        raise ValueError("captures must be an iterable")
    normalized: list[ResearchSourceCaptureRecord] = []
    for item in captures:
        if type(item) is not ResearchSourceCaptureRecord:
            raise ValueError("captures must contain ResearchSourceCaptureRecord")
        _require_hard_flags("record", item)
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.capture_group,
                item.captured_at,
                item.source_family,
                item.contradiction_pressure,
            ),
        ),
    )


def _normalize_reason_code_counts(
    values: Sequence[ResearchSourceCaptureRedundancyGapReasonCodeCount],
) -> tuple[ResearchSourceCaptureRedundancyGapReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError("reason_code_counts must be a sequence")
    normalized: list[ResearchSourceCaptureRedundancyGapReasonCodeCount] = []
    for value in values:
        if type(value) is not ResearchSourceCaptureRedundancyGapReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceCaptureRedundancyGapReasonCodeCount",
            )
        _require_hard_flags("reason count", value)
        normalized.append(value)
    return tuple(sorted(normalized, key=lambda item: REASON_CODES.index(item.reason_code)))


def _normalize_reason_codes(values: Sequence[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for value in values:
        reason_code = _require_reason_code("reason_code", value)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in normalized)


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str or value not in REASON_CODES:
        raise ValueError(f"{field_name} must be a supported reason code")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _reject_unsafe_public_string(field_name, value)
    if not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(COUNT_QUANTUM, rounding=ROUND_HALF_EVEN)
    if normalized != value:
        raise ValueError(f"{field_name} must be an integral Decimal")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_count(field_name, value)
    if normalized < COUNT_QUANTUM - COUNT_QUANTUM:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= COUNT_QUANTUM - COUNT_QUANTUM:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _count_decimal(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return COUNT_QUANTUM - COUNT_QUANTUM
    return sum(values, COUNT_QUANTUM - COUNT_QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == COUNT_QUANTUM - COUNT_QUANTUM:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        value = numerator / denominator
    return _normalize_probability("ratio", value)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        value = sum(values, ZERO) / Decimal(len(values))
    return _normalize_probability("average", value)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    seconds = Decimal(str((later - earlier).total_seconds()))
    return _normalize_nonnegative_decimal("capture_age_seconds", seconds)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _report_values_without_digest(
    report: ResearchSourceCaptureRedundancyGapReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        payload,
        allow_json_containers=True,
    )
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


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe public value")


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_CAPTURE_REDUNDANCY_GAP_REPORT_CONFIG_VERSION",
    "ResearchSourceCaptureRecord",
    "ResearchSourceCaptureRedundancyGapConfig",
    "ResearchSourceCaptureRedundancyGapReasonCodeCount",
    "ResearchSourceCaptureRedundancyGapReport",
    "build_research_source_capture_redundancy_gap_report",
    "research_source_capture_redundancy_gap_report_digest",
    "research_source_capture_redundancy_gap_report_payload",
)
