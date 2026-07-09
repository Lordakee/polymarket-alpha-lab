"""Pure report-only summary for strategy review threshold backtest readiness."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import re
from typing import Any


__all__ = (
    "ResearchStrategyReviewThresholdBacktestReadinessConfig",
    "ResearchStrategyReviewThresholdBacktestReadinessInput",
    "ResearchStrategyReviewThresholdBacktestReadinessReasonCodeCount",
    "ResearchStrategyReviewThresholdBacktestReadinessReport",
    "ResearchStrategyReviewThresholdBacktestReadinessRow",
    "build_research_strategy_review_threshold_backtest_readiness_report",
    "research_strategy_review_threshold_backtest_readiness_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-strategy-review-threshold-backtest-readiness-v0"
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_QUANT = Decimal("0.000001")
_STATUSES = ("pass", "watch", "block")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_REVIEW_KEY_UNSAFE_TERMS = (
    "cand" + "idate",
    "mar" + "ket",
    "condition",
    "slug",
    "quest" + "ion",
    "http",
    "url",
    "text",
    "d" + "sn",
    "tab" + "le",
    "tok" + "en",
)
_PAYLOAD_UNSAFE_FRAGMENTS = (
    "cand" + "idate_id",
    "raw_" + "cand" + "idate",
    "mar" + "ket_id",
    "mar" + "ket_slug",
    "mar" + "ket_" + "quest" + "ion",
    "quest" + "ion",
    "http://",
    "https://",
    "url",
    "raw_url",
    "raw_text",
    "source_text",
    "source_ref",
    "d" + "sn",
    "tab" + "le_name",
    "tok" + "en",
    "data" + "base",
    "db" + "_",
    "db" + "-",
    "db" + ".",
    "net" + "work",
    "per" + "sist",
    "file" + "system",
    "file_" + "path",
    "file-" + "path",
    "file." + "path",
    "sup" + "abase",
    "post" + "gres",
)
_ACTION_TERMS = (
    "wal" + "let",
    "au" + "th",
    "or" + "der",
    "tra" + "de",
    "li" + "ve",
    "pos" + "ition",
    "siz" + "ing",
    "recomm" + "endation",
    "exec" + "ute",
    "exec" + "ution",
)


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class ResearchStrategyReviewThresholdBacktestReadinessConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    watch_readiness_pressure_threshold: Decimal = Decimal("0.350000")
    block_readiness_pressure_threshold: Decimal = Decimal("0.700000")
    calibration_sample_target_count: Decimal = Decimal("20")
    evidence_coverage_weight: Decimal = Decimal("0.200000")
    cost_drag_weight: Decimal = Decimal("0.150000")
    liquidity_quality_weight: Decimal = Decimal("0.200000")
    resolution_clarity_weight: Decimal = Decimal("0.150000")
    calibration_sample_depth_weight: Decimal = Decimal("0.150000")
    specialist_memory_quality_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyReviewThresholdBacktestReadinessConfig,
            "config",
        )
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_readiness_pressure_threshold",
            "block_readiness_pressure_threshold",
            "evidence_coverage_weight",
            "cost_drag_weight",
            "liquidity_quality_weight",
            "resolution_clarity_weight",
            "calibration_sample_depth_weight",
            "specialist_memory_quality_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.block_readiness_pressure_threshold
            <= self.watch_readiness_pressure_threshold
        ):
            raise ValueError(
                "block_readiness_pressure_threshold must exceed "
                "watch_readiness_pressure_threshold",
            )
        object.__setattr__(
            self,
            "calibration_sample_target_count",
            _require_positive_whole_decimal(
                "calibration_sample_target_count",
                self.calibration_sample_target_count,
            ),
        )
        weight_sum = _quantize(
            self.evidence_coverage_weight
            + self.cost_drag_weight
            + self.liquidity_quality_weight
            + self.resolution_clarity_weight
            + self.calibration_sample_depth_weight
            + self.specialist_memory_quality_weight,
        )
        if weight_sum != _ONE:
            raise ValueError(
                "evidence_coverage_weight, cost_drag_weight, "
                "liquidity_quality_weight, resolution_clarity_weight, "
                "calibration_sample_depth_weight, and "
                "specialist_memory_quality_weight must sum to 1",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyReviewThresholdBacktestReadinessInput:
    public_review_key: str
    evidence_coverage_score: Decimal
    cost_drag_pressure: Decimal
    liquidity_quality_score: Decimal
    resolution_clarity_score: Decimal
    calibration_sample_count: Decimal
    specialist_memory_quality_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyReviewThresholdBacktestReadinessInput,
            "backtest readiness input",
        )
        _require_public_review_key("public_review_key", self.public_review_key)
        for field_name in (
            "evidence_coverage_score",
            "cost_drag_pressure",
            "liquidity_quality_score",
            "resolution_clarity_score",
            "specialist_memory_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "calibration_sample_count",
            _require_nonnegative_whole_decimal(
                "calibration_sample_count",
                self.calibration_sample_count,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("backtest readiness input", self)


@dataclass(frozen=True)
class ResearchStrategyReviewThresholdBacktestReadinessRow:
    public_review_key: str
    evidence_coverage_score: Decimal
    evidence_coverage_gap: Decimal
    cost_drag_pressure: Decimal
    liquidity_quality_score: Decimal
    liquidity_quality_gap: Decimal
    resolution_clarity_score: Decimal
    resolution_clarity_gap: Decimal
    calibration_sample_count: Decimal
    calibration_sample_depth_score: Decimal
    calibration_sample_depth_gap: Decimal
    specialist_memory_quality_score: Decimal
    specialist_memory_quality_gap: Decimal
    backtest_readiness_pressure: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyReviewThresholdBacktestReadinessRow,
            "row",
        )
        _require_public_review_key("public_review_key", self.public_review_key)
        for field_name in (
            "evidence_coverage_score",
            "evidence_coverage_gap",
            "cost_drag_pressure",
            "liquidity_quality_score",
            "liquidity_quality_gap",
            "resolution_clarity_score",
            "resolution_clarity_gap",
            "calibration_sample_depth_score",
            "calibration_sample_depth_gap",
            "specialist_memory_quality_score",
            "specialist_memory_quality_gap",
            "backtest_readiness_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "calibration_sample_count",
            _require_nonnegative_whole_decimal(
                "calibration_sample_count",
                self.calibration_sample_count,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchStrategyReviewThresholdBacktestReadinessReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyReviewThresholdBacktestReadinessReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyReviewThresholdBacktestReadinessReport:
    generated_at: datetime
    config_version: str
    review_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_backtest_readiness_pressure: Decimal | None
    min_calibration_sample_count: Decimal
    status: str
    rows: tuple[ResearchStrategyReviewThresholdBacktestReadinessRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyReviewThresholdBacktestReadinessReasonCodeCount,
        ...
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyReviewThresholdBacktestReadinessReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in ("review_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_backtest_readiness_pressure",
            _require_optional_probability_decimal(
                "average_backtest_readiness_pressure",
                self.average_backtest_readiness_pressure,
            ),
        )
        object.__setattr__(
            self,
            "min_calibration_sample_count",
            _require_nonnegative_whole_decimal(
                "min_calibration_sample_count",
                self.min_calibration_sample_count,
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
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")


def build_research_strategy_review_threshold_backtest_readiness_report(
    readiness_items: Iterable[object],
    *,
    config: ResearchStrategyReviewThresholdBacktestReadinessConfig,
    generated_at: datetime,
) -> ResearchStrategyReviewThresholdBacktestReadinessReport:
    if type(config) is not ResearchStrategyReviewThresholdBacktestReadinessConfig:
        raise ValueError(
            "config must be a ResearchStrategyReviewThresholdBacktestReadinessConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_items = _normalize_readiness_items(readiness_items)
    rows = tuple(
        _row_from_item(item, config=config)
        for item in sorted(normalized_items, key=lambda value: value.public_review_key)
    )
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "review_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_backtest_readiness_pressure": _average_backtest_readiness_pressure(rows),
        "min_calibration_sample_count": min(
            (row.calibration_sample_count for row in rows),
            default=_ZERO,
        ),
        "status": _report_status(rows),
        "rows": rows,
        "reason_code_counts": _reason_code_counts(rows, reason_codes),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyReviewThresholdBacktestReadinessReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_strategy_review_threshold_backtest_readiness_report_payload(
    report: ResearchStrategyReviewThresholdBacktestReadinessReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyReviewThresholdBacktestReadinessReport:
        raise ValueError(
            "report must be a ResearchStrategyReviewThresholdBacktestReadinessReport",
        )
    _require_report_payload_integrity(report)
    payload = _json_ready(asdict(report))
    _reject_public_payload("report payload", payload)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _row_from_item(
    item: ResearchStrategyReviewThresholdBacktestReadinessInput,
    *,
    config: ResearchStrategyReviewThresholdBacktestReadinessConfig,
) -> ResearchStrategyReviewThresholdBacktestReadinessRow:
    evidence_coverage_gap = _quantize(_ONE - item.evidence_coverage_score)
    liquidity_quality_gap = _quantize(_ONE - item.liquidity_quality_score)
    resolution_clarity_gap = _quantize(_ONE - item.resolution_clarity_score)
    calibration_sample_depth_score = _calibration_sample_depth_score(
        item.calibration_sample_count,
        config=config,
    )
    calibration_sample_depth_gap = _quantize(_ONE - calibration_sample_depth_score)
    specialist_memory_quality_gap = _quantize(
        _ONE - item.specialist_memory_quality_score,
    )
    backtest_readiness_pressure = _quantize(
        (evidence_coverage_gap * config.evidence_coverage_weight)
        + (item.cost_drag_pressure * config.cost_drag_weight)
        + (liquidity_quality_gap * config.liquidity_quality_weight)
        + (resolution_clarity_gap * config.resolution_clarity_weight)
        + (calibration_sample_depth_gap * config.calibration_sample_depth_weight)
        + (specialist_memory_quality_gap * config.specialist_memory_quality_weight),
    )
    status = _row_status(backtest_readiness_pressure, config=config)
    return ResearchStrategyReviewThresholdBacktestReadinessRow(
        public_review_key=item.public_review_key,
        evidence_coverage_score=item.evidence_coverage_score,
        evidence_coverage_gap=evidence_coverage_gap,
        cost_drag_pressure=item.cost_drag_pressure,
        liquidity_quality_score=item.liquidity_quality_score,
        liquidity_quality_gap=liquidity_quality_gap,
        resolution_clarity_score=item.resolution_clarity_score,
        resolution_clarity_gap=resolution_clarity_gap,
        calibration_sample_count=item.calibration_sample_count,
        calibration_sample_depth_score=calibration_sample_depth_score,
        calibration_sample_depth_gap=calibration_sample_depth_gap,
        specialist_memory_quality_score=item.specialist_memory_quality_score,
        specialist_memory_quality_gap=specialist_memory_quality_gap,
        backtest_readiness_pressure=backtest_readiness_pressure,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            evidence_coverage_score=item.evidence_coverage_score,
            cost_drag_pressure=item.cost_drag_pressure,
            liquidity_quality_score=item.liquidity_quality_score,
            resolution_clarity_score=item.resolution_clarity_score,
            calibration_sample_depth_score=calibration_sample_depth_score,
            specialist_memory_quality_score=item.specialist_memory_quality_score,
            input_reason_codes=item.reason_codes,
        ),
    )


def _normalize_readiness_items(
    readiness_items: Iterable[object],
) -> tuple[ResearchStrategyReviewThresholdBacktestReadinessInput, ...]:
    if isinstance(readiness_items, (str, bytes)):
        raise ValueError("readiness_items must be an iterable")
    try:
        values = tuple(readiness_items)
    except TypeError as exc:
        raise ValueError("readiness_items must be an iterable") from exc
    return tuple(_coerce_readiness_item(value) for value in values)


def _coerce_readiness_item(
    value: object,
) -> ResearchStrategyReviewThresholdBacktestReadinessInput:
    if type(value) is ResearchStrategyReviewThresholdBacktestReadinessInput:
        _require_hard_flags("backtest readiness input", value)
        return value
    _require_hard_flags("backtest readiness input", value)
    return ResearchStrategyReviewThresholdBacktestReadinessInput(
        public_review_key=_field_value(value, "public_review_key"),
        evidence_coverage_score=_field_value(value, "evidence_coverage_score"),
        cost_drag_pressure=_field_value(value, "cost_drag_pressure"),
        liquidity_quality_score=_field_value(value, "liquidity_quality_score"),
        resolution_clarity_score=_field_value(value, "resolution_clarity_score"),
        calibration_sample_count=_field_value(value, "calibration_sample_count"),
        specialist_memory_quality_score=_field_value(
            value,
            "specialist_memory_quality_score",
        ),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _calibration_sample_depth_score(
    sample_count: Decimal,
    *,
    config: ResearchStrategyReviewThresholdBacktestReadinessConfig,
) -> Decimal:
    if sample_count >= config.calibration_sample_target_count:
        return _ONE
    return _quantize(sample_count / config.calibration_sample_target_count)


def _row_status(
    backtest_readiness_pressure: Decimal,
    *,
    config: ResearchStrategyReviewThresholdBacktestReadinessConfig,
) -> str:
    if backtest_readiness_pressure >= config.block_readiness_pressure_threshold:
        return "block"
    if backtest_readiness_pressure >= config.watch_readiness_pressure_threshold:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    evidence_coverage_score: Decimal,
    cost_drag_pressure: Decimal,
    liquidity_quality_score: Decimal,
    resolution_clarity_score: Decimal,
    calibration_sample_depth_score: Decimal,
    specialist_memory_quality_score: Decimal,
    input_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    codes: set[str] = {f"threshold_backtest_readiness_{status}"}
    if evidence_coverage_score < Decimal("0.500000"):
        codes.add("evidence_coverage_low")
    elif evidence_coverage_score < Decimal("0.800000"):
        codes.add("evidence_coverage_mixed")
    else:
        codes.add("evidence_coverage_strong")
    if cost_drag_pressure >= Decimal("0.500000"):
        codes.add("cost_drag_high")
    elif cost_drag_pressure >= Decimal("0.250000"):
        codes.add("cost_drag_watch")
    else:
        codes.add("cost_drag_low")
    if liquidity_quality_score < Decimal("0.500000"):
        codes.add("liquidity_quality_low")
    elif liquidity_quality_score < Decimal("0.800000"):
        codes.add("liquidity_quality_mixed")
    else:
        codes.add("liquidity_quality_strong")
    if resolution_clarity_score < Decimal("0.500000"):
        codes.add("resolution_clarity_low")
    elif resolution_clarity_score < Decimal("0.800000"):
        codes.add("resolution_clarity_mixed")
    else:
        codes.add("resolution_clarity_strong")
    if calibration_sample_depth_score < Decimal("0.500000"):
        codes.add("calibration_sample_depth_low")
    elif calibration_sample_depth_score < _ONE:
        codes.add("calibration_sample_depth_mixed")
    else:
        codes.add("calibration_sample_depth_sufficient")
    if specialist_memory_quality_score < Decimal("0.500000"):
        codes.add("specialist_memory_quality_low")
    elif specialist_memory_quality_score < Decimal("0.800000"):
        codes.add("specialist_memory_quality_mixed")
    else:
        codes.add("specialist_memory_quality_strong")
    for reason_code in input_reason_codes:
        codes.add(f"input_{reason_code}")
    return tuple(sorted(codes))


def _report_status(
    rows: tuple[ResearchStrategyReviewThresholdBacktestReadinessRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyReviewThresholdBacktestReadinessRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_backtest_readiness_items",)
    if all(row.status == "pass" for row in rows):
        return ("threshold_backtest_readiness_pass",)
    return tuple(sorted({code for row in rows for code in row.reason_codes}))


def _reason_code_counts(
    rows: tuple[ResearchStrategyReviewThresholdBacktestReadinessRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchStrategyReviewThresholdBacktestReadinessReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyReviewThresholdBacktestReadinessReasonCodeCount(
                reason_code=reason_codes[0],
                count=Decimal("1"),
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchStrategyReviewThresholdBacktestReadinessReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _average_backtest_readiness_pressure(
    rows: tuple[ResearchStrategyReviewThresholdBacktestReadinessRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(
        sum((row.backtest_readiness_pressure for row in rows), _ZERO)
        / Decimal(len(rows)),
    )


def _status_count(
    rows: tuple[ResearchStrategyReviewThresholdBacktestReadinessRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_rows(
    rows: tuple[ResearchStrategyReviewThresholdBacktestReadinessRow, ...],
) -> tuple[ResearchStrategyReviewThresholdBacktestReadinessRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchStrategyReviewThresholdBacktestReadinessRow:
            raise ValueError(
                "rows must contain "
                "ResearchStrategyReviewThresholdBacktestReadinessRow values",
            )
        _require_hard_flags("row", row)
    if len({row.public_review_key for row in rows}) != len(rows):
        raise ValueError("rows public_review_key values must be unique")
    sorted_rows = tuple(sorted(rows, key=lambda row: row.public_review_key))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by public_review_key")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[
        ResearchStrategyReviewThresholdBacktestReadinessReasonCodeCount,
        ...
    ],
) -> tuple[ResearchStrategyReviewThresholdBacktestReadinessReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchStrategyReviewThresholdBacktestReadinessReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyReviewThresholdBacktestReadinessReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _require_report_payload_integrity(
    report: ResearchStrategyReviewThresholdBacktestReadinessReport,
) -> None:
    _require_hard_flags("report", report)
    if type(report.rows) is not tuple:
        raise ValueError("rows must be a tuple")
    if type(report.reason_code_counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")

    checked_rows = tuple(_checked_row(row) for row in report.rows)
    checked_reason_code_counts = tuple(
        _checked_reason_code_count(reason_code_count)
        for reason_code_count in report.reason_code_counts
    )
    ResearchStrategyReviewThresholdBacktestReadinessReport(
        generated_at=report.generated_at,
        config_version=report.config_version,
        review_count=report.review_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        average_backtest_readiness_pressure=(
            report.average_backtest_readiness_pressure
        ),
        min_calibration_sample_count=report.min_calibration_sample_count,
        status=report.status,
        rows=checked_rows,
        reason_code_counts=checked_reason_code_counts,
        reason_codes=report.reason_codes,
        derived_validation_digest=report.derived_validation_digest,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def _checked_row(
    row: object,
) -> ResearchStrategyReviewThresholdBacktestReadinessRow:
    if type(row) is not ResearchStrategyReviewThresholdBacktestReadinessRow:
        raise ValueError(
            "rows must contain "
            "ResearchStrategyReviewThresholdBacktestReadinessRow values",
        )
    return ResearchStrategyReviewThresholdBacktestReadinessRow(
        **_field_values(
            "row",
            row,
            ResearchStrategyReviewThresholdBacktestReadinessRow,
        ),
    )


def _checked_reason_code_count(
    reason_code_count: object,
) -> ResearchStrategyReviewThresholdBacktestReadinessReasonCodeCount:
    if (
        type(reason_code_count)
        is not ResearchStrategyReviewThresholdBacktestReadinessReasonCodeCount
    ):
        raise ValueError(
            "reason_code_counts must contain "
            "ResearchStrategyReviewThresholdBacktestReadinessReasonCodeCount values",
        )
    return ResearchStrategyReviewThresholdBacktestReadinessReasonCodeCount(
        **_field_values(
            "reason_code_count",
            reason_code_count,
            ResearchStrategyReviewThresholdBacktestReadinessReasonCodeCount,
        ),
    )


def _field_values(
    label: str,
    value: object,
    expected_type: type[object],
) -> dict[str, object]:
    checked: dict[str, object] = {}
    for field in fields(expected_type):
        try:
            checked[field.name] = getattr(value, field.name)
        except AttributeError as exc:
            raise ValueError(f"{label} must contain {field.name}") from exc
    return checked


def _validate_row_consistency(
    row: ResearchStrategyReviewThresholdBacktestReadinessRow,
) -> None:
    if row.evidence_coverage_gap != _quantize(_ONE - row.evidence_coverage_score):
        raise ValueError("evidence_coverage_gap must match evidence_coverage_score")
    if row.liquidity_quality_gap != _quantize(_ONE - row.liquidity_quality_score):
        raise ValueError("liquidity_quality_gap must match liquidity_quality_score")
    if row.resolution_clarity_gap != _quantize(_ONE - row.resolution_clarity_score):
        raise ValueError("resolution_clarity_gap must match resolution_clarity_score")
    if row.calibration_sample_depth_gap != _quantize(
        _ONE - row.calibration_sample_depth_score,
    ):
        raise ValueError(
            "calibration_sample_depth_gap must match calibration_sample_depth_score",
        )
    if row.specialist_memory_quality_gap != _quantize(
        _ONE - row.specialist_memory_quality_score,
    ):
        raise ValueError(
            "specialist_memory_quality_gap must match specialist_memory_quality_score",
        )
    expected_status_reason_code = f"threshold_backtest_readiness_{row.status}"
    status_reason_codes = {
        f"threshold_backtest_readiness_{status}" for status in _STATUSES
    }
    if status_reason_codes.intersection(row.reason_codes) != {
        expected_status_reason_code,
    }:
        raise ValueError("reason_codes must match status")


def _validate_report_consistency(
    report: ResearchStrategyReviewThresholdBacktestReadinessReport,
) -> None:
    if report.review_count != _decimal_count(len(report.rows)):
        raise ValueError("review_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_backtest_readiness_pressure != (
        _average_backtest_readiness_pressure(report.rows)
    ):
        raise ValueError("average_backtest_readiness_pressure must match rows")
    if report.min_calibration_sample_count != min(
        (row.calibration_sample_count for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_calibration_sample_count must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _report_values_without_digest(
    report: ResearchStrategyReviewThresholdBacktestReadinessReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest")
    return values


def _report_digest_from_values(values: dict[str, object]) -> str:
    payload = _json_ready(values)
    _reject_public_payload("report digest payload", payload)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


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


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


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
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
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
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT)


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty public identifier")
    if _PUBLIC_IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public identifier")


def _require_public_review_key(field_name: str, value: object) -> None:
    _require_public_identifier(field_name, value)
    lowered = value.lower()
    if any(term in lowered for term in _REVIEW_KEY_UNSAFE_TERMS):
        raise ValueError(f"{field_name} must not contain unsafe public terms")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or _REASON_CODE_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must contain public snake_case reason codes")


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


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be one of {_STATUSES}")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if _field_value(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be true")


def _reject_public_payload(label: str, payload: object) -> None:
    encoded = json.dumps(_json_ready(payload), sort_keys=True).lower()
    for fragment in _PAYLOAD_UNSAFE_FRAGMENTS + _ACTION_TERMS:
        if fragment in encoded:
            raise ValueError(f"{label} contains unsafe public payload content")
