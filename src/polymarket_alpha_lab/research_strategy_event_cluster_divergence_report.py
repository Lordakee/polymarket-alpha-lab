"""Pure event-cluster divergence report for strategy research."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_STRATEGY_EVENT_CLUSTER_DIVERGENCE_REPORT_CONFIG_VERSION = (
    "research-strategy-event-cluster-divergence-report-v0"
)

REPORT_STATUSES = ("pass", "watch", "block")
SOURCE_CLASSES = ("official", "primary", "model")

PASS_REASON = "event_cluster_divergence_pass"
SIGNAL_DISPERSION_WATCH_REASON = "cluster_signal_dispersion_watch"
SIGNAL_DISPERSION_BLOCK_REASON = "cluster_signal_dispersion_block"
EVIDENCE_FRESHNESS_WATCH_REASON = "evidence_freshness_watch"
EVIDENCE_FRESHNESS_BLOCK_REASON = "evidence_freshness_block"
SOURCE_CLASS_COVERAGE_WATCH_REASON = "source_class_coverage_watch"
SOURCE_CLASS_COVERAGE_BLOCK_REASON = "source_class_coverage_block"
CONTRADICTION_PRESSURE_WATCH_REASON = "unresolved_contradiction_pressure_watch"
CONTRADICTION_PRESSURE_BLOCK_REASON = "unresolved_contradiction_pressure_block"
MANUAL_REVIEW_URGENCY_WATCH_REASON = "manual_review_urgency_watch"
MANUAL_REVIEW_URGENCY_BLOCK_REASON = "manual_review_urgency_block"

REASON_CODES = (
    PASS_REASON,
    SIGNAL_DISPERSION_WATCH_REASON,
    SIGNAL_DISPERSION_BLOCK_REASON,
    EVIDENCE_FRESHNESS_WATCH_REASON,
    EVIDENCE_FRESHNESS_BLOCK_REASON,
    SOURCE_CLASS_COVERAGE_WATCH_REASON,
    SOURCE_CLASS_COVERAGE_BLOCK_REASON,
    CONTRADICTION_PRESSURE_WATCH_REASON,
    CONTRADICTION_PRESSURE_BLOCK_REASON,
    MANUAL_REVIEW_URGENCY_WATCH_REASON,
    MANUAL_REVIEW_URGENCY_BLOCK_REASON,
)

STATUS_RANK = {"block": Decimal("0"), "watch": Decimal("1"), "pass": Decimal("2")}
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")

UNSAFE_PUBLIC_KEYS = frozenset(
    (
        "raw_candidate_id",
        "raw_market_id",
        "raw_market_slug",
        "raw_market_question",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "private_token",
    ),
)


@dataclass(frozen=True)
class ResearchStrategyEventClusterDivergenceReportConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_EVENT_CLUSTER_DIVERGENCE_REPORT_CONFIG_VERSION
    )
    signal_dispersion_watch_threshold: Decimal = Decimal("0.200000")
    signal_dispersion_block_threshold: Decimal = Decimal("0.350000")
    freshness_watch_age_seconds: Decimal = Decimal("7200.000000")
    freshness_block_age_seconds: Decimal = Decimal("21600.000000")
    minimum_source_class_count: Decimal = Decimal("3.000000")
    contradiction_watch_ratio_threshold: Decimal = Decimal("0.250000")
    contradiction_block_ratio_threshold: Decimal = Decimal("0.600000")
    manual_review_watch_urgency_threshold: Decimal = Decimal("0.500000")
    manual_review_block_urgency_threshold: Decimal = Decimal("0.800000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "signal_dispersion_watch_threshold",
            "signal_dispersion_block_threshold",
            "contradiction_watch_ratio_threshold",
            "contradiction_block_ratio_threshold",
            "manual_review_watch_urgency_threshold",
            "manual_review_block_urgency_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "freshness_watch_age_seconds",
            "freshness_block_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "minimum_source_class_count",
            _require_positive_decimal(
                "minimum_source_class_count",
                self.minimum_source_class_count,
            ),
        )
        _require_lte(
            "signal_dispersion thresholds",
            self.signal_dispersion_watch_threshold,
            self.signal_dispersion_block_threshold,
        )
        _require_lte(
            "freshness thresholds",
            self.freshness_watch_age_seconds,
            self.freshness_block_age_seconds,
        )
        _require_lte(
            "contradiction thresholds",
            self.contradiction_watch_ratio_threshold,
            self.contradiction_block_ratio_threshold,
        )
        _require_lte(
            "manual review thresholds",
            self.manual_review_watch_urgency_threshold,
            self.manual_review_block_urgency_threshold,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyEventClusterDivergenceInputRow:
    raw_candidate_id: str
    raw_market_id: str
    raw_market_slug: str
    raw_market_question: str
    cluster_key: str
    source_class: str
    signal_score: Decimal
    evidence_observed_at: datetime
    unresolved_contradiction_count: Decimal
    total_evidence_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "raw_candidate_id",
            "raw_market_id",
            "raw_market_slug",
            "raw_market_question",
            "cluster_key",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_source_class("source_class", self.source_class)
        object.__setattr__(
            self,
            "signal_score",
            _normalize_ratio("signal_score", self.signal_score),
        )
        object.__setattr__(
            self,
            "evidence_observed_at",
            _as_utc("evidence_observed_at", self.evidence_observed_at),
        )
        object.__setattr__(
            self,
            "unresolved_contradiction_count",
            _normalize_nonnegative_decimal(
                "unresolved_contradiction_count",
                self.unresolved_contradiction_count,
            ),
        )
        object.__setattr__(
            self,
            "total_evidence_count",
            _normalize_nonnegative_decimal(
                "total_evidence_count",
                self.total_evidence_count,
            ),
        )
        if self.unresolved_contradiction_count > self.total_evidence_count:
            raise ValueError(
                "total_evidence_count must be >= unresolved_contradiction_count",
            )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class ResearchStrategyEventClusterDivergenceReportRow:
    cluster_row_number: Decimal
    cluster_hash: str
    signal_count: Decimal
    candidate_count: Decimal
    market_count: Decimal
    source_class_count: Decimal
    source_class_coverage_ratio: Decimal
    signal_min_score: Decimal
    signal_max_score: Decimal
    signal_dispersion: Decimal
    max_evidence_age_seconds: Decimal
    unresolved_contradiction_count: Decimal
    total_evidence_count: Decimal
    contradiction_pressure_ratio: Decimal
    manual_review_urgency_score: Decimal
    review_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "cluster_row_number",
            _require_positive_decimal("cluster_row_number", self.cluster_row_number),
        )
        _require_sha256("cluster_hash", self.cluster_hash)
        for field_name in (
            "signal_count",
            "candidate_count",
            "market_count",
            "source_class_count",
            "max_evidence_age_seconds",
            "unresolved_contradiction_count",
            "total_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_class_coverage_ratio",
            "signal_min_score",
            "signal_max_score",
            "signal_dispersion",
            "contradiction_pressure_ratio",
            "manual_review_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_report_status("review_status", self.review_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_report_row(self)
        _require_hard_flags("report row", self)


@dataclass(frozen=True)
class ResearchStrategyEventClusterDivergenceReport:
    generated_at: datetime
    config_version: str
    report_status: str
    reason_codes: tuple[str, ...]
    input_row_count: Decimal
    cluster_count: Decimal
    pass_cluster_count: Decimal
    watch_cluster_count: Decimal
    block_cluster_count: Decimal
    average_signal_dispersion: Decimal
    average_source_class_coverage_ratio: Decimal
    average_contradiction_pressure_ratio: Decimal
    max_evidence_age_seconds: Decimal
    max_manual_review_urgency_score: Decimal
    derived_validation_digest: str
    rows: tuple[ResearchStrategyEventClusterDivergenceReportRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_report_status("report_status", self.report_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        for field_name in (
            "input_row_count",
            "cluster_count",
            "pass_cluster_count",
            "watch_cluster_count",
            "block_cluster_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_signal_dispersion",
            "average_source_class_coverage_ratio",
            "average_contradiction_pressure_ratio",
            "max_manual_review_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_evidence_age_seconds",
            _normalize_nonnegative_decimal(
                "max_evidence_age_seconds",
                self.max_evidence_age_seconds,
            ),
        )
        _require_sha256("derived_validation_digest", self.derived_validation_digest)
        object.__setattr__(self, "rows", _normalize_report_rows(self.rows))
        _validate_report(self)
        if self.derived_validation_digest != _derived_validation_digest(self):
            raise ValueError("derived_validation_digest does not match report payload")
        _require_hard_flags("report", self)


def build_research_strategy_event_cluster_divergence_report(
    input_rows: list[ResearchStrategyEventClusterDivergenceInputRow]
    | tuple[ResearchStrategyEventClusterDivergenceInputRow, ...],
    *,
    config: ResearchStrategyEventClusterDivergenceReportConfig,
    generated_at: datetime,
) -> ResearchStrategyEventClusterDivergenceReport:
    if type(config) is not ResearchStrategyEventClusterDivergenceReportConfig:
        raise ValueError(
            "config must be a ResearchStrategyEventClusterDivergenceReportConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _normalize_input_rows(input_rows, generated_at=generated_at_utc)
    report_rows = _build_report_rows(
        rows,
        config=config,
        generated_at=generated_at_utc,
    )
    reason_codes = _report_reason_codes(report_rows)
    values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "report_status": _report_status_from_rows(report_rows),
        "reason_codes": reason_codes,
        "input_row_count": _decimal_count(len(rows)),
        "cluster_count": _decimal_count(len(report_rows)),
        "pass_cluster_count": _status_count(report_rows, "pass"),
        "watch_cluster_count": _status_count(report_rows, "watch"),
        "block_cluster_count": _status_count(report_rows, "block"),
        "average_signal_dispersion": _average(
            tuple(row.signal_dispersion for row in report_rows),
        ),
        "average_source_class_coverage_ratio": _average(
            tuple(row.source_class_coverage_ratio for row in report_rows),
        ),
        "average_contradiction_pressure_ratio": _average(
            tuple(row.contradiction_pressure_ratio for row in report_rows),
        ),
        "max_evidence_age_seconds": _max_decimal(
            tuple(row.max_evidence_age_seconds for row in report_rows),
        ),
        "max_manual_review_urgency_score": _max_decimal(
            tuple(row.manual_review_urgency_score for row in report_rows),
        ),
        "rows": report_rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyEventClusterDivergenceReport(
        **values,
        derived_validation_digest=_digest_from_values(values),
    )


def research_strategy_event_cluster_divergence_report_payload(
    report: ResearchStrategyEventClusterDivergenceReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is dict:
        payload = dict(report)
        _validate_public_payload(payload)
        return payload
    if type(report) is not ResearchStrategyEventClusterDivergenceReport:
        raise ValueError(
            "report must be a ResearchStrategyEventClusterDivergenceReport",
        )
    _require_hard_flags("report", report)
    if report.derived_validation_digest != _derived_validation_digest(report):
        raise ValueError("derived_validation_digest does not match report payload")
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload(payload)
    return payload


def _normalize_input_rows(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[ResearchStrategyEventClusterDivergenceInputRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchStrategyEventClusterDivergenceInputRow:
            raise ValueError("input rows must contain divergence input rows")
        _require_hard_flags("input row", row)
        if row.evidence_observed_at > generated_at:
            raise ValueError("evidence_observed_at must not be in the future")
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _cluster_hash(row.cluster_key),
                row.raw_candidate_id,
                row.raw_market_id,
                row.source_class,
                row.signal_score,
                row.evidence_observed_at,
            ),
        ),
    )


def _build_report_rows(
    input_rows: tuple[ResearchStrategyEventClusterDivergenceInputRow, ...],
    *,
    config: ResearchStrategyEventClusterDivergenceReportConfig,
    generated_at: datetime,
) -> tuple[ResearchStrategyEventClusterDivergenceReportRow, ...]:
    grouped: dict[str, list[ResearchStrategyEventClusterDivergenceInputRow]] = {}
    for row in input_rows:
        grouped.setdefault(row.cluster_key, []).append(row)
    row_values = tuple(
        _cluster_row_values(
            cluster_key=cluster_key,
            rows=tuple(cluster_rows),
            config=config,
            generated_at=generated_at,
        )
        for cluster_key, cluster_rows in grouped.items()
    )
    ranked = tuple(sorted(row_values, key=_row_values_sort_key))
    return tuple(
        ResearchStrategyEventClusterDivergenceReportRow(
            cluster_row_number=_decimal_count(index),
            **values,
        )
        for index, values in enumerate(ranked, start=1)
    )


def _cluster_row_values(
    *,
    cluster_key: str,
    rows: tuple[ResearchStrategyEventClusterDivergenceInputRow, ...],
    config: ResearchStrategyEventClusterDivergenceReportConfig,
    generated_at: datetime,
) -> dict[str, object]:
    signal_scores = tuple(row.signal_score for row in rows)
    min_signal = min(signal_scores)
    max_signal = max(signal_scores)
    signal_dispersion = _normalize_ratio("signal_dispersion", max_signal - min_signal)
    max_age_seconds = _max_decimal(
        tuple(_age_seconds(generated_at, row.evidence_observed_at) for row in rows),
    )
    unresolved_count = _sum_decimal(
        tuple(row.unresolved_contradiction_count for row in rows),
    )
    total_evidence_count = _sum_decimal(tuple(row.total_evidence_count for row in rows))
    contradiction_ratio = _ratio(unresolved_count, total_evidence_count)
    source_class_count = _decimal_count(len({row.source_class for row in rows}))
    source_class_coverage_ratio = min(
        ONE,
        _ratio(source_class_count, config.minimum_source_class_count),
    )
    manual_urgency = _manual_review_urgency_score(
        signal_dispersion=signal_dispersion,
        max_age_seconds=max_age_seconds,
        source_class_coverage_ratio=source_class_coverage_ratio,
        contradiction_pressure_ratio=contradiction_ratio,
        config=config,
    )
    reason_codes = _row_reason_codes(
        signal_dispersion=signal_dispersion,
        max_age_seconds=max_age_seconds,
        source_class_coverage_ratio=source_class_coverage_ratio,
        contradiction_pressure_ratio=contradiction_ratio,
        manual_review_urgency_score=manual_urgency,
        config=config,
    )
    return {
        "cluster_hash": _cluster_hash(cluster_key),
        "signal_count": _decimal_count(len(rows)),
        "candidate_count": _decimal_count(len({row.raw_candidate_id for row in rows})),
        "market_count": _decimal_count(len({row.raw_market_id for row in rows})),
        "source_class_count": source_class_count,
        "source_class_coverage_ratio": source_class_coverage_ratio,
        "signal_min_score": min_signal,
        "signal_max_score": max_signal,
        "signal_dispersion": signal_dispersion,
        "max_evidence_age_seconds": max_age_seconds,
        "unresolved_contradiction_count": unresolved_count,
        "total_evidence_count": total_evidence_count,
        "contradiction_pressure_ratio": contradiction_ratio,
        "manual_review_urgency_score": manual_urgency,
        "review_status": _row_status_from_reason_codes(reason_codes),
        "reason_codes": reason_codes,
    }


def _row_reason_codes(
    *,
    signal_dispersion: Decimal,
    max_age_seconds: Decimal,
    source_class_coverage_ratio: Decimal,
    contradiction_pressure_ratio: Decimal,
    manual_review_urgency_score: Decimal,
    config: ResearchStrategyEventClusterDivergenceReportConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    _append_threshold_reason(
        reasons,
        metric=signal_dispersion,
        watch_threshold=config.signal_dispersion_watch_threshold,
        block_threshold=config.signal_dispersion_block_threshold,
        watch_reason=SIGNAL_DISPERSION_WATCH_REASON,
        block_reason=SIGNAL_DISPERSION_BLOCK_REASON,
    )
    _append_threshold_reason(
        reasons,
        metric=max_age_seconds,
        watch_threshold=config.freshness_watch_age_seconds,
        block_threshold=config.freshness_block_age_seconds,
        watch_reason=EVIDENCE_FRESHNESS_WATCH_REASON,
        block_reason=EVIDENCE_FRESHNESS_BLOCK_REASON,
    )
    if source_class_coverage_ratio < Decimal("0.500000"):
        reasons.append(SOURCE_CLASS_COVERAGE_BLOCK_REASON)
    elif source_class_coverage_ratio < ONE:
        reasons.append(SOURCE_CLASS_COVERAGE_WATCH_REASON)
    _append_threshold_reason(
        reasons,
        metric=contradiction_pressure_ratio,
        watch_threshold=config.contradiction_watch_ratio_threshold,
        block_threshold=config.contradiction_block_ratio_threshold,
        watch_reason=CONTRADICTION_PRESSURE_WATCH_REASON,
        block_reason=CONTRADICTION_PRESSURE_BLOCK_REASON,
    )
    _append_threshold_reason(
        reasons,
        metric=manual_review_urgency_score,
        watch_threshold=config.manual_review_watch_urgency_threshold,
        block_threshold=config.manual_review_block_urgency_threshold,
        watch_reason=MANUAL_REVIEW_URGENCY_WATCH_REASON,
        block_reason=MANUAL_REVIEW_URGENCY_BLOCK_REASON,
    )
    if not reasons:
        reasons.append(PASS_REASON)
    return tuple(reason for reason in REASON_CODES if reason in reasons)


def _append_threshold_reason(
    reasons: list[str],
    *,
    metric: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
    watch_reason: str,
    block_reason: str,
) -> None:
    if metric >= block_threshold:
        reasons.append(block_reason)
    elif metric >= watch_threshold:
        reasons.append(watch_reason)


def _manual_review_urgency_score(
    *,
    signal_dispersion: Decimal,
    max_age_seconds: Decimal,
    source_class_coverage_ratio: Decimal,
    contradiction_pressure_ratio: Decimal,
    config: ResearchStrategyEventClusterDivergenceReportConfig,
) -> Decimal:
    return min(
        ONE,
        max(
            _ratio(signal_dispersion, config.signal_dispersion_block_threshold),
            _ratio(max_age_seconds, config.freshness_block_age_seconds),
            ONE - source_class_coverage_ratio,
            _ratio(
                contradiction_pressure_ratio,
                config.contradiction_block_ratio_threshold,
            ),
        ),
    ).quantize(QUANT)


def _row_values_sort_key(
    values: dict[str, object],
) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal, str]:
    return (
        STATUS_RANK[str(values["review_status"])],
        -_expect_decimal(values["manual_review_urgency_score"]),
        -_expect_decimal(values["contradiction_pressure_ratio"]),
        -_expect_decimal(values["signal_dispersion"]),
        -_expect_decimal(values["max_evidence_age_seconds"]),
        str(values["cluster_hash"]),
    )


def _normalize_report_rows(
    value: object,
) -> tuple[ResearchStrategyEventClusterDivergenceReportRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_hashes: set[str] = set()
    expected_row_number = Decimal("1.000000")
    for row in rows:
        if type(row) is not ResearchStrategyEventClusterDivergenceReportRow:
            raise ValueError("rows must contain report rows")
        _require_hard_flags("report row", row)
        if row.cluster_hash in seen_hashes:
            raise ValueError("rows must be unique by cluster_hash")
        seen_hashes.add(row.cluster_hash)
        if row.cluster_row_number != expected_row_number:
            raise ValueError("cluster_row_number must be contiguous")
        expected_row_number += ONE
    if tuple(sorted(rows, key=_report_row_sort_key)) != rows:
        raise ValueError("rows must be deterministic")
    return rows


def _report_row_sort_key(
    row: ResearchStrategyEventClusterDivergenceReportRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal, str]:
    return (
        STATUS_RANK[row.review_status],
        -row.manual_review_urgency_score,
        -row.contradiction_pressure_ratio,
        -row.signal_dispersion,
        -row.max_evidence_age_seconds,
        row.cluster_hash,
    )


def _validate_report_row(
    row: ResearchStrategyEventClusterDivergenceReportRow,
) -> None:
    if row.signal_min_score > row.signal_max_score:
        raise ValueError("signal_min_score must be <= signal_max_score")
    if row.signal_dispersion != _normalize_ratio(
        "signal_dispersion",
        row.signal_max_score - row.signal_min_score,
    ):
        raise ValueError("signal_dispersion must match signal score range")
    if row.unresolved_contradiction_count > row.total_evidence_count:
        raise ValueError(
            "unresolved_contradiction_count must not exceed total_evidence_count",
        )
    if row.contradiction_pressure_ratio != _ratio(
        row.unresolved_contradiction_count,
        row.total_evidence_count,
    ):
        raise ValueError("contradiction_pressure_ratio must match evidence counts")
    if row.review_status != _row_status_from_reason_codes(row.reason_codes):
        raise ValueError("review_status must match reason_codes")


def _validate_report(report: ResearchStrategyEventClusterDivergenceReport) -> None:
    if report.input_row_count != _sum_decimal(
        tuple(row.signal_count for row in report.rows),
    ):
        raise ValueError("input_row_count must match rows")
    if report.cluster_count != _decimal_count(len(report.rows)):
        raise ValueError("cluster_count must match rows")
    if report.pass_cluster_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_cluster_count must match rows")
    if report.watch_cluster_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_cluster_count must match rows")
    if report.block_cluster_count != _status_count(report.rows, "block"):
        raise ValueError("block_cluster_count must match rows")
    if (
        report.pass_cluster_count
        + report.watch_cluster_count
        + report.block_cluster_count
        != report.cluster_count
    ):
        raise ValueError("cluster status counts must sum to cluster_count")
    if report.average_signal_dispersion != _average(
        tuple(row.signal_dispersion for row in report.rows),
    ):
        raise ValueError("average_signal_dispersion must match rows")
    if report.average_source_class_coverage_ratio != _average(
        tuple(row.source_class_coverage_ratio for row in report.rows),
    ):
        raise ValueError("average_source_class_coverage_ratio must match rows")
    if report.average_contradiction_pressure_ratio != _average(
        tuple(row.contradiction_pressure_ratio for row in report.rows),
    ):
        raise ValueError("average_contradiction_pressure_ratio must match rows")
    if report.max_evidence_age_seconds != _max_decimal(
        tuple(row.max_evidence_age_seconds for row in report.rows),
    ):
        raise ValueError("max_evidence_age_seconds must match rows")
    if report.max_manual_review_urgency_score != _max_decimal(
        tuple(row.manual_review_urgency_score for row in report.rows),
    ):
        raise ValueError("max_manual_review_urgency_score must match rows")
    if report.report_status != _report_status_from_rows(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _report_reason_codes(
    rows: tuple[ResearchStrategyEventClusterDivergenceReportRow, ...],
) -> tuple[str, ...]:
    reasons = tuple(
        reason
        for reason in REASON_CODES
        if reason != PASS_REASON and any(reason in row.reason_codes for row in rows)
    )
    if reasons:
        return reasons
    return (PASS_REASON,)


def _row_status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return "block"
    if any(reason.endswith("_watch") for reason in reason_codes):
        return "watch"
    return "pass"


def _report_status_from_rows(
    rows: tuple[ResearchStrategyEventClusterDivergenceReportRow, ...],
) -> str:
    if any(row.review_status == "block" for row in rows):
        return "block"
    if any(row.review_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _status_count(
    rows: tuple[ResearchStrategyEventClusterDivergenceReportRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.review_status == status))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _ratio(_sum_decimal(values), _decimal_count(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values).quantize(QUANT)


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return total.quantize(QUANT)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _age_seconds(end_at: datetime, start_at: datetime) -> Decimal:
    delta = _as_utc("end_at", end_at) - _as_utc("start_at", start_at)
    age_seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    if age_seconds < ZERO:
        raise ValueError("age_seconds must be nonnegative")
    return age_seconds.quantize(QUANT)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value).quantize(QUANT)


def _expect_decimal(value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError("expected Decimal")
    return value


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    decimal_value = value.quantize(QUANT)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} must have a concrete UTC offset")
    return value.astimezone(UTC)


def _require_report_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REPORT_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_source_class(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SOURCE_CLASSES:
        raise ValueError(f"{field_name} must be official, primary, or model")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_reason_code("reason_codes", reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    if tuple(reason for reason in REASON_CODES if reason in reason_codes) != reason_codes:
        raise ValueError("reason_codes must be deterministic")
    return reason_codes


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODES:
        raise ValueError(f"{field_name} must be known")


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_lte(label: str, left: Decimal, right: Decimal) -> None:
    if left > right:
        raise ValueError(f"{label} must be nondecreasing")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be stripped")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _cluster_hash(cluster_key: str) -> str:
    _require_canonical_string("cluster_key", cluster_key)
    return sha256(
        ("research_strategy_event_cluster_divergence:" + cluster_key).encode("utf-8"),
    ).hexdigest()


def _derived_validation_digest(
    report: ResearchStrategyEventClusterDivergenceReport,
) -> str:
    values = asdict(report)
    values.pop("derived_validation_digest")
    return _digest_from_values(values)


def _digest_from_values(values: dict[str, Any]) -> str:
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    _reject_unsafe_public_payload("digest payload", payload)
    return _payload_validation_digest(payload)


def _payload_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = {
        key: item for key, item in payload.items() if key != "derived_validation_digest"
    }
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _validate_public_payload(payload: dict[str, Any]) -> None:
    _reject_unsafe_public_payload("payload", payload)
    _require_hard_flags("payload", _PayloadFlags(payload))
    supplied_digest = payload.get("derived_validation_digest")
    _require_sha256("derived_validation_digest", supplied_digest)
    if supplied_digest != _payload_validation_digest(payload):
        raise ValueError("derived_validation_digest does not match report payload")
    _reject_public_numeric_values(payload)


def _reject_public_numeric_values(value: object) -> None:
    if isinstance(value, (bool, str)) or value is None:
        return
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numeric_values(item)
        return
    raise ValueError("public payload numeric values must be Decimal-derived strings")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} payload keys must be strings")
            if key in UNSAFE_PUBLIC_KEYS:
                raise ValueError(f"{label} contains unsafe public key")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        raise ValueError("JSON numeric values must be Decimal-derived strings")
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


class _PayloadFlags:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.paper_only = payload.get("paper_only")
        self.report_only = payload.get("report_only")
        self.readonly = payload.get("readonly")


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_EVENT_CLUSTER_DIVERGENCE_REPORT_CONFIG_VERSION",
    "REPORT_STATUSES",
    "ResearchStrategyEventClusterDivergenceReportConfig",
    "ResearchStrategyEventClusterDivergenceInputRow",
    "ResearchStrategyEventClusterDivergenceReportRow",
    "ResearchStrategyEventClusterDivergenceReport",
    "build_research_strategy_event_cluster_divergence_report",
    "research_strategy_event_cluster_divergence_report_payload",
)
