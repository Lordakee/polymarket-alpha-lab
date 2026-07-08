"""Pure report-only reducer for aggregate source corroboration gaps."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_SOURCE_CORROBORATION_GAP_REPORT_CONFIG_VERSION = (
    "source-corroboration-gap-report-v0"
)

QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

DEFAULT_REQUIRED_SOURCE_CLASSES = (
    "official_reporting",
    "domain_specialist",
    "independent_archive",
)
STATUSES = ("pass", "watch", "block")
STATUS_RANK = {
    "block": Decimal("0"),
    "watch": Decimal("1"),
    "pass": Decimal("2"),
}
PASS_REASON = "source_corroboration_gap_passed"
REASON_CODE_ORDER = (
    "contradiction_pressure_block",
    "contradiction_pressure_watch",
    "coverage_gap_block",
    "coverage_gap_watch",
    "missing_independent_source_classes_block",
    "missing_independent_source_classes_watch",
    "recheck_urgency_block",
    "recheck_urgency_watch",
    "stale_corroboration_block",
    "stale_corroboration_watch",
    "source_corroboration_gap_block",
    "source_corroboration_gap_watch",
    PASS_REASON,
)
PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
UNSAFE_PUBLIC_FRAGMENTS = (
    "://",
    "www.",
    "raw",
    "url",
    "source_text",
    "candidate",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "dsn",
    "table",
    "wallet",
    "order",
    "network",
    "database",
    "token",
    "auth",
    "secret",
    "password",
    "private_key",
    "api_key",
    "trade",
    "trading",
)


@dataclass(frozen=True)
class ResearchSourceCorroborationGapReportConfig:
    config_version: str = DEFAULT_RESEARCH_SOURCE_CORROBORATION_GAP_REPORT_CONFIG_VERSION
    required_source_classes: tuple[str, ...] = DEFAULT_REQUIRED_SOURCE_CLASSES
    min_coverage_score: Decimal = Decimal("0.750000")
    max_corroboration_age_seconds: Decimal = Decimal("7200.000000")
    watch_recheck_urgency_score: Decimal = Decimal("0.350000")
    block_recheck_urgency_score: Decimal = Decimal("0.700000")
    block_missing_source_class_count: Decimal = Decimal("2")
    contradiction_pressure_weight: Decimal = Decimal("0.300000")
    stale_corroboration_weight: Decimal = Decimal("0.250000")
    coverage_gap_weight: Decimal = Decimal("0.250000")
    independence_gap_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceCorroborationGapReportConfig:
            raise TypeError(
                "ResearchSourceCorroborationGapReportConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceCorroborationGapReportConfig:
            raise ValueError(
                "config must be exactly ResearchSourceCorroborationGapReportConfig",
            )
        if self.config_version != DEFAULT_RESEARCH_SOURCE_CORROBORATION_GAP_REPORT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_public_identifier("config_version", self.config_version)
        object.__setattr__(
            self,
            "required_source_classes",
            _normalize_required_source_classes(self.required_source_classes),
        )
        for field_name in (
            "min_coverage_score",
            "watch_recheck_urgency_score",
            "block_recheck_urgency_score",
            "contradiction_pressure_weight",
            "stale_corroboration_weight",
            "coverage_gap_weight",
            "independence_gap_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_corroboration_age_seconds",
            _normalize_positive_decimal(
                "max_corroboration_age_seconds",
                self.max_corroboration_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "block_missing_source_class_count",
            _normalize_positive_count(
                "block_missing_source_class_count",
                self.block_missing_source_class_count,
            ),
        )
        if self.block_recheck_urgency_score <= self.watch_recheck_urgency_score:
            raise ValueError(
                "block_recheck_urgency_score must exceed watch_recheck_urgency_score",
            )
        if (
            self.contradiction_pressure_weight
            + self.stale_corroboration_weight
            + self.coverage_gap_weight
            + self.independence_gap_weight
        ) != ONE:
            raise ValueError("weights must sum to one")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceCorroborationSignal:
    corroboration_group_id: str
    source_class: str
    observed_at: datetime
    coverage_score: Decimal
    contradiction_pressure: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceCorroborationSignal:
            raise TypeError(
                "ResearchSourceCorroborationSignal does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceCorroborationSignal:
            raise ValueError("signal must be exactly ResearchSourceCorroborationSignal")
        _require_public_identifier("corroboration_group_id", self.corroboration_group_id)
        _require_public_identifier("source_class", self.source_class)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "coverage_score",
            _normalize_probability("coverage_score", self.coverage_score),
        )
        object.__setattr__(
            self,
            "contradiction_pressure",
            _normalize_probability(
                "contradiction_pressure",
                self.contradiction_pressure,
            ),
        )
        _require_hard_flags("signal", self)


@dataclass(frozen=True)
class ResearchSourceCorroborationGapReportRow:
    corroboration_group_id: str
    source_class_count: Decimal
    missing_source_class_count: Decimal
    stale_corroboration_count: Decimal
    coverage_gap_count: Decimal
    max_source_age_seconds: Decimal
    average_coverage_score: Decimal
    max_contradiction_pressure: Decimal
    recheck_urgency_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceCorroborationGapReportRow:
            raise TypeError(
                "ResearchSourceCorroborationGapReportRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceCorroborationGapReportRow:
            raise ValueError("row must be exactly ResearchSourceCorroborationGapReportRow")
        _require_public_identifier("corroboration_group_id", self.corroboration_group_id)
        for field_name in (
            "source_class_count",
            "missing_source_class_count",
            "stale_corroboration_count",
            "coverage_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_source_age_seconds",
            _normalize_nonnegative_decimal(
                "max_source_age_seconds",
                self.max_source_age_seconds,
            ),
        )
        for field_name in (
            "average_coverage_score",
            "max_contradiction_pressure",
            "recheck_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchSourceCorroborationGapReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceCorroborationGapReasonCodeCount:
            raise TypeError(
                "ResearchSourceCorroborationGapReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceCorroborationGapReasonCodeCount:
            raise ValueError(
                "reason count must be exactly ResearchSourceCorroborationGapReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class ResearchSourceCorroborationGapReport:
    generated_at: datetime
    config_version: str
    group_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_missing_source_class_count: Decimal
    max_stale_corroboration_count: Decimal
    max_coverage_gap_count: Decimal
    max_source_age_seconds: Decimal
    max_contradiction_pressure: Decimal
    max_recheck_urgency_score: Decimal
    average_recheck_urgency_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchSourceCorroborationGapReasonCodeCount, ...]
    rows: tuple[ResearchSourceCorroborationGapReportRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceCorroborationGapReport:
            raise TypeError(
                "ResearchSourceCorroborationGapReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceCorroborationGapReport:
            raise ValueError("report must be exactly ResearchSourceCorroborationGapReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        for field_name in (
            "group_count",
            "pass_count",
            "watch_count",
            "block_count",
            "max_missing_source_class_count",
            "max_stale_corroboration_count",
            "max_coverage_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_source_age_seconds",
            _normalize_nonnegative_decimal(
                "max_source_age_seconds",
                self.max_source_age_seconds,
            ),
        )
        for field_name in (
            "max_contradiction_pressure",
            "max_recheck_urgency_score",
            "average_recheck_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        _verify_report_digest(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_source_corroboration_gap_report_payload(self)


def build_research_source_corroboration_gap_report(
    signals: Iterable[ResearchSourceCorroborationSignal],
    *,
    config: ResearchSourceCorroborationGapReportConfig,
    generated_at: datetime,
) -> ResearchSourceCorroborationGapReport:
    if type(config) is not ResearchSourceCorroborationGapReportConfig:
        raise ValueError("config must be exactly ResearchSourceCorroborationGapReportConfig")
    generated_at = _as_utc("generated_at", generated_at)
    normalized_signals = _normalize_signals(signals)
    grouped: dict[str, list[ResearchSourceCorroborationSignal]] = {}
    for signal in normalized_signals:
        if signal.observed_at > generated_at:
            raise ValueError("observed_at cannot be after generated_at")
        grouped.setdefault(signal.corroboration_group_id, []).append(signal)

    rows = tuple(
        sorted(
            (
                _row_from_group(
                    group_id,
                    tuple(group_signals),
                    generated_at=generated_at,
                    config=config,
                )
                for group_id, group_signals in grouped.items()
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    reason_code_counts = _reason_code_counts(rows)
    group_count = _count_decimal(len(rows))
    pass_count = _count_decimal(sum(1 for row in rows if row.status == "pass"))
    watch_count = _count_decimal(sum(1 for row in rows if row.status == "watch"))
    block_count = _count_decimal(sum(1 for row in rows if row.status == "block"))
    status = _report_status(block_count, watch_count)
    max_missing = max((row.missing_source_class_count for row in rows), default=COUNT_QUANTUM * 0)
    max_stale = max((row.stale_corroboration_count for row in rows), default=COUNT_QUANTUM * 0)
    max_coverage = max((row.coverage_gap_count for row in rows), default=COUNT_QUANTUM * 0)
    max_age = max((row.max_source_age_seconds for row in rows), default=ZERO)
    max_contradiction = max((row.max_contradiction_pressure for row in rows), default=ZERO)
    max_urgency = max((row.recheck_urgency_score for row in rows), default=ZERO)
    average_urgency = _average_decimal(
        tuple(row.recheck_urgency_score for row in rows),
        default=ZERO,
    )
    unsigned_payload = _json_ready(
        {
            "generated_at": generated_at,
            "config_version": config.config_version,
            "group_count": group_count,
            "pass_count": pass_count,
            "watch_count": watch_count,
            "block_count": block_count,
            "max_missing_source_class_count": max_missing,
            "max_stale_corroboration_count": max_stale,
            "max_coverage_gap_count": max_coverage,
            "max_source_age_seconds": max_age,
            "max_contradiction_pressure": max_contradiction,
            "max_recheck_urgency_score": max_urgency,
            "average_recheck_urgency_score": average_urgency,
            "status": status,
            "reason_codes": reason_codes,
            "reason_code_counts": reason_code_counts,
            "rows": rows,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )
    return ResearchSourceCorroborationGapReport(
        generated_at=generated_at,
        config_version=config.config_version,
        group_count=group_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        max_missing_source_class_count=max_missing,
        max_stale_corroboration_count=max_stale,
        max_coverage_gap_count=max_coverage,
        max_source_age_seconds=max_age,
        max_contradiction_pressure=max_contradiction,
        max_recheck_urgency_score=max_urgency,
        average_recheck_urgency_score=average_urgency,
        status=status,
        reason_codes=reason_codes,
        reason_code_counts=reason_code_counts,
        rows=rows,
        derived_validation_digest=_digest_payload(unsigned_payload),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def research_source_corroboration_gap_report_payload(
    report: ResearchSourceCorroborationGapReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceCorroborationGapReport:
        raise ValueError("report must be exactly ResearchSourceCorroborationGapReport")
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload(payload)
    return payload


def research_source_corroboration_gap_report_digest(
    report: ResearchSourceCorroborationGapReport,
) -> str:
    payload = research_source_corroboration_gap_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


def _row_from_group(
    group_id: str,
    signals: tuple[ResearchSourceCorroborationSignal, ...],
    *,
    generated_at: datetime,
    config: ResearchSourceCorroborationGapReportConfig,
) -> ResearchSourceCorroborationGapReportRow:
    required_classes = set(config.required_source_classes)
    present_classes = frozenset(signal.source_class for signal in signals)
    missing_count = _count_decimal(len(required_classes.difference(present_classes)))
    source_class_count = _count_decimal(len(present_classes))
    ages = tuple(_age_seconds(generated_at, signal.observed_at) for signal in signals)
    max_age = max(ages)
    stale_count = _count_decimal(
        sum(1 for age in ages if age > config.max_corroboration_age_seconds),
    )
    coverage_gap_count = _count_decimal(
        sum(1 for signal in signals if signal.coverage_score < config.min_coverage_score),
    )
    average_coverage = _average_decimal(
        tuple(signal.coverage_score for signal in signals),
        default=ZERO,
    )
    max_contradiction = max(signal.contradiction_pressure for signal in signals)
    signal_count = _count_decimal(len(signals))
    required_count = _count_decimal(len(config.required_source_classes))
    stale_ratio = _safe_ratio(stale_count, signal_count)
    coverage_gap_ratio = _safe_ratio(coverage_gap_count, signal_count)
    independence_gap = _safe_ratio(missing_count, required_count)
    urgency = _normalize_probability(
        "recheck_urgency_score",
        (
            config.contradiction_pressure_weight * max_contradiction
            + config.stale_corroboration_weight * stale_ratio
            + config.coverage_gap_weight * coverage_gap_ratio
            + config.independence_gap_weight * independence_gap
        ),
    )
    reason_codes = _row_reason_codes(
        missing_count=missing_count,
        stale_count=stale_count,
        coverage_gap_count=coverage_gap_count,
        max_contradiction=max_contradiction,
        urgency=urgency,
        config=config,
    )
    status = "pass"
    if "source_corroboration_gap_block" in reason_codes:
        status = "block"
    elif "source_corroboration_gap_watch" in reason_codes:
        status = "watch"
    return ResearchSourceCorroborationGapReportRow(
        corroboration_group_id=group_id,
        source_class_count=source_class_count,
        missing_source_class_count=missing_count,
        stale_corroboration_count=stale_count,
        coverage_gap_count=coverage_gap_count,
        max_source_age_seconds=max_age,
        average_coverage_score=average_coverage,
        max_contradiction_pressure=max_contradiction,
        recheck_urgency_score=urgency,
        status=status,
        reason_codes=reason_codes,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _row_reason_codes(
    *,
    missing_count: Decimal,
    stale_count: Decimal,
    coverage_gap_count: Decimal,
    max_contradiction: Decimal,
    urgency: Decimal,
    config: ResearchSourceCorroborationGapReportConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    has_block = False
    has_watch = False
    if max_contradiction >= config.block_recheck_urgency_score:
        reasons.append("contradiction_pressure_block")
        has_block = True
    elif max_contradiction >= config.watch_recheck_urgency_score:
        reasons.append("contradiction_pressure_watch")
        has_watch = True
    if coverage_gap_count > COUNT_QUANTUM * 0:
        reasons.append("coverage_gap_block")
        has_block = True
    if missing_count >= config.block_missing_source_class_count:
        reasons.append("missing_independent_source_classes_block")
        has_block = True
    elif missing_count > COUNT_QUANTUM * 0:
        reasons.append("missing_independent_source_classes_watch")
        has_watch = True
    if urgency >= config.block_recheck_urgency_score:
        reasons.append("recheck_urgency_block")
        has_block = True
    elif urgency >= config.watch_recheck_urgency_score:
        reasons.append("recheck_urgency_watch")
        has_watch = True
    if stale_count > COUNT_QUANTUM * 0:
        reasons.append("stale_corroboration_block")
        has_block = True
    if has_block:
        reasons.append("source_corroboration_gap_block")
    elif has_watch:
        reasons.append("source_corroboration_gap_watch")
    else:
        reasons.append(PASS_REASON)
    return _ordered_reason_codes(reasons)


def _row_sort_key(row: ResearchSourceCorroborationGapReportRow) -> tuple[Decimal, Decimal, str]:
    return (STATUS_RANK[row.status], -row.recheck_urgency_score, row.corroboration_group_id)


def _report_reason_codes(
    rows: tuple[ResearchSourceCorroborationGapReportRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (PASS_REASON,)
    return _ordered_reason_codes(
        reason for row in rows for reason in row.reason_codes
    )


def _reason_code_counts(
    rows: tuple[ResearchSourceCorroborationGapReportRow, ...],
) -> tuple[ResearchSourceCorroborationGapReasonCodeCount, ...]:
    counts = Counter(reason for row in rows for reason in row.reason_codes)
    return tuple(
        ResearchSourceCorroborationGapReasonCodeCount(
            reason_code=reason,
            count=_count_decimal(counts[reason]),
        )
        for reason in REASON_CODE_ORDER
        if counts[reason] > 0
    )


def _report_status(block_count: Decimal, watch_count: Decimal) -> str:
    if block_count > COUNT_QUANTUM * 0:
        return "block"
    if watch_count > COUNT_QUANTUM * 0:
        return "watch"
    return "pass"


def _validate_report_consistency(report: ResearchSourceCorroborationGapReport) -> None:
    if report.group_count != _count_decimal(len(report.rows)):
        raise ValueError("group_count must match row count")
    if report.pass_count != _count_decimal(sum(1 for row in report.rows if row.status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count_decimal(sum(1 for row in report.rows if row.status == "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count_decimal(sum(1 for row in report.rows if row.status == "block")):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(report.block_count, report.watch_count):
        raise ValueError("status must match aggregate row statuses")


def _verify_report_digest(report: ResearchSourceCorroborationGapReport) -> None:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    if _digest_payload(unsigned_payload) != report.derived_validation_digest:
        raise ValueError("derived_validation_digest does not match report payload")


def _validate_public_payload(payload: dict[str, Any]) -> None:
    _reject_public_numerics(payload)
    _reject_unsafe_public_payload("public payload", payload)
    _require_hard_flags("public payload", _DictFlags(payload))
    digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    if _digest_payload(unsigned_payload) != digest:
        raise ValueError("derived_validation_digest does not match public payload")


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


def _normalize_signals(
    signals: Iterable[ResearchSourceCorroborationSignal],
) -> tuple[ResearchSourceCorroborationSignal, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must be an iterable of ResearchSourceCorroborationSignal")
    normalized: list[ResearchSourceCorroborationSignal] = []
    for signal in signals:
        if type(signal) is not ResearchSourceCorroborationSignal:
            raise ValueError("signals must contain exactly ResearchSourceCorroborationSignal")
        normalized.append(signal)
    return tuple(normalized)


def _normalize_rows(
    rows: tuple[ResearchSourceCorroborationGapReportRow, ...],
) -> tuple[ResearchSourceCorroborationGapReportRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchSourceCorroborationGapReportRow:
            raise ValueError("rows must contain exactly ResearchSourceCorroborationGapReportRow")
    return rows


def _normalize_reason_code_counts(
    reason_code_counts: tuple[ResearchSourceCorroborationGapReasonCodeCount, ...],
) -> tuple[ResearchSourceCorroborationGapReasonCodeCount, ...]:
    if type(reason_code_counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for reason_count in reason_code_counts:
        if type(reason_count) is not ResearchSourceCorroborationGapReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain exactly "
                "ResearchSourceCorroborationGapReasonCodeCount",
            )
    return reason_code_counts


def _normalize_required_source_classes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("required_source_classes must be a tuple")
    if not value:
        raise ValueError("required_source_classes must be non-empty")
    normalized: list[str] = []
    for source_class in value:
        normalized.append(_require_public_identifier("required_source_classes", source_class))
    if len(set(normalized)) != len(normalized):
        raise ValueError("required_source_classes must be unique")
    return tuple(normalized)


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized = tuple(_require_reason_code(field_name, reason) for reason in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    return normalized


def _ordered_reason_codes(reasons: Iterable[str]) -> tuple[str, ...]:
    present = frozenset(reasons)
    unknown = present.difference(REASON_CODE_ORDER)
    if unknown:
        raise ValueError("unknown reason code")
    return tuple(reason for reason in REASON_CODE_ORDER if reason in present)


def _require_reason_code(field_name: str, value: object) -> str:
    value = _require_public_identifier(field_name, value)
    if value not in REASON_CODE_ORDER:
        raise ValueError(f"{field_name} must be a supported reason code")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public value for {field_name}")
    if not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    return value


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if type(getattr(value, field_name, None)) is not bool:
            raise ValueError(f"{field_name} must be a bool for {label}")
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} utcoffset must not be None")
    return value.astimezone(UTC)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    return _normalize_nonnegative_decimal(
        "source_age_seconds",
        Decimal(delta.days * 86400 + delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000")),
    )


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _require_exact_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return _quantize(decimal_value, QUANTUM)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_exact_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return _quantize(decimal_value, QUANTUM)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_exact_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(decimal_value, QUANTUM)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_exact_decimal(field_name, value)
    if decimal_value <= COUNT_QUANTUM * 0:
        raise ValueError(f"{field_name} must be positive")
    return _quantize(decimal_value, COUNT_QUANTUM)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_exact_decimal(field_name, value)
    if decimal_value < COUNT_QUANTUM * 0:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(decimal_value, COUNT_QUANTUM)


def _require_exact_decimal(field_name: str, value: object) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _average_decimal(values: tuple[Decimal, ...], *, default: Decimal) -> Decimal:
    if not values:
        return default
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO) / _count_decimal(len(values)), QUANTUM)


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == COUNT_QUANTUM * 0:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator, QUANTUM)


def _quantize(value: Decimal, quantum: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(quantum)


def _digest_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _json_ready(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("value is not JSON serializable")


def _reject_public_numerics(value: object) -> None:
    if type(value) in (float, int):
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numerics(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numerics(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if type(value) is str:
        lowered = value.lower()
        if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            lowered_key = key.lower()
            forbidden_keys = (
                "raw",
                "url",
                "source_text",
                "candidate",
                "market_id",
                "market_slug",
                "slug",
                "question",
                "dsn",
                "table",
                "wallet",
                "order",
                "network",
                "database",
                "token",
                "auth",
                "secret",
                "private_key",
                "api_key",
                "trade",
                "trading",
            )
            if any(fragment in lowered_key for fragment in forbidden_keys):
                raise ValueError(f"unsafe public field in {label}: {key}")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)
