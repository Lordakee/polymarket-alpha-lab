"""Pure report-only post-resolution learning priority report."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_STRATEGY_POST_RESOLUTION_LEARNING_PRIORITY_CONFIG_VERSION = (
    "research-strategy-post-resolution-learning-priority-report-v0"
)
POST_RESOLUTION_LEARNING_PRIORITY_STATUSES = ("pass", "watch", "block")

PASS_REASON = "post_resolution_learning_priority_pass"
WATCH_REASON = "post_resolution_learning_priority_watch"
BLOCK_REASON = "post_resolution_learning_priority_block"
EMPTY_REASON = "post_resolution_learning_priority_empty"

ROW_REASON_PRIORITY = (
    "settled_outcome_signal_block",
    "forecast_miss_block",
    "source_evidence_gap_block",
    "calibration_freshness_block",
    "review_backlog_block",
    "settled_outcome_signal_watch",
    "forecast_miss_watch",
    "source_evidence_gap_watch",
    "calibration_freshness_watch",
    "review_backlog_watch",
    BLOCK_REASON,
    WATCH_REASON,
    PASS_REASON,
)
REPORT_REASON_PRIORITY = (
    BLOCK_REASON,
    WATCH_REASON,
    PASS_REASON,
    EMPTY_REASON,
    "settled_outcome_signal_block",
    "forecast_miss_block",
    "source_evidence_gap_block",
    "calibration_freshness_block",
    "review_backlog_block",
    "settled_outcome_signal_watch",
    "forecast_miss_watch",
    "source_evidence_gap_watch",
    "calibration_freshness_watch",
    "review_backlog_watch",
)

DIGEST_FIELD = "derived_validation_digest"
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
HEX_DIGITS = frozenset("0123456789abcdef")

UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "candidate_id",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "source_url",
        "source_text",
        "raw_source",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommendation",
        "auth",
        "live",
        "buy",
        "sell",
        "private_key",
        "credential",
        "secret",
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_POST_RESOLUTION_LEARNING_PRIORITY_CONFIG_VERSION",
    "POST_RESOLUTION_LEARNING_PRIORITY_STATUSES",
    "ResearchStrategyPostResolutionLearningPriorityConfig",
    "ResearchStrategyPostResolutionLearningPriorityInput",
    "ResearchStrategyPostResolutionLearningPriorityRow",
    "ResearchStrategyPostResolutionLearningPriorityReport",
    "build_research_strategy_post_resolution_learning_priority_report",
    "research_strategy_post_resolution_learning_priority_report_public_payload",
    "validate_research_strategy_post_resolution_learning_priority_public_payload",
)


@dataclass(frozen=True)
class ResearchStrategyPostResolutionLearningPriorityConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_POST_RESOLUTION_LEARNING_PRIORITY_CONFIG_VERSION
    )
    watch_min_learning_priority_score: Decimal = Decimal("0.500000")
    block_min_learning_priority_score: Decimal = Decimal("0.750000")
    watch_min_settled_outcome_signal_strength: Decimal = Decimal("0.650000")
    block_min_settled_outcome_signal_strength: Decimal = Decimal("0.850000")
    watch_min_forecast_miss_severity: Decimal = Decimal("0.300000")
    block_min_forecast_miss_severity: Decimal = Decimal("0.600000")
    watch_min_source_evidence_gap: Decimal = Decimal("0.250000")
    block_min_source_evidence_gap: Decimal = Decimal("0.500000")
    watch_max_calibration_freshness_score: Decimal = Decimal("0.600000")
    block_max_calibration_freshness_score: Decimal = Decimal("0.350000")
    watch_min_review_backlog_count: Decimal = Decimal("3")
    block_min_review_backlog_count: Decimal = Decimal("8")
    settled_outcome_signal_weight: Decimal = Decimal("0.200000")
    forecast_miss_weight: Decimal = Decimal("0.300000")
    source_evidence_gap_weight: Decimal = Decimal("0.200000")
    calibration_staleness_weight: Decimal = Decimal("0.150000")
    review_backlog_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyPostResolutionLearningPriorityConfig:
            raise ValueError(
                "config must be exactly ResearchStrategyPostResolutionLearningPriorityConfig",
            )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_POST_RESOLUTION_LEARNING_PRIORITY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_min_learning_priority_score",
            "block_min_learning_priority_score",
            "watch_min_settled_outcome_signal_strength",
            "block_min_settled_outcome_signal_strength",
            "watch_min_forecast_miss_severity",
            "block_min_forecast_miss_severity",
            "watch_min_source_evidence_gap",
            "block_min_source_evidence_gap",
            "watch_max_calibration_freshness_score",
            "block_max_calibration_freshness_score",
            "settled_outcome_signal_weight",
            "forecast_miss_weight",
            "source_evidence_gap_weight",
            "calibration_staleness_weight",
            "review_backlog_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_min_review_backlog_count",
            "block_min_review_backlog_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        require_paper_only_flags("post-resolution learning priority config", self)
        _reject_unsafe_public_payload("config", _public_dict(self))


@dataclass(frozen=True)
class ResearchStrategyPostResolutionLearningPriorityInput:
    analyst_label: str
    learning_scope_label: str
    settled_outcome_signal_strength: Decimal
    forecast_miss_severity: Decimal
    source_evidence_gap: Decimal
    calibration_freshness_score: Decimal
    review_backlog_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyPostResolutionLearningPriorityInput:
            raise ValueError(
                "input must be exactly ResearchStrategyPostResolutionLearningPriorityInput",
            )
        for field_name in ("analyst_label", "learning_scope_label"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "settled_outcome_signal_strength",
            "forecast_miss_severity",
            "source_evidence_gap",
            "calibration_freshness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "review_backlog_count",
            _normalize_count("review_backlog_count", self.review_backlog_count),
        )
        require_paper_only_flags("post-resolution learning priority input", self)
        _reject_unsafe_public_payload("input", _public_dict(self))


@dataclass(frozen=True)
class ResearchStrategyPostResolutionLearningPriorityRow:
    analyst_label: str
    learning_scope_label: str
    settled_outcome_signal_strength: Decimal
    forecast_miss_severity: Decimal
    source_evidence_gap: Decimal
    calibration_freshness_score: Decimal
    review_backlog_count: Decimal
    calibration_staleness_score: Decimal
    review_backlog_pressure: Decimal
    learning_priority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyPostResolutionLearningPriorityRow:
            raise ValueError("row must be exactly ResearchStrategyPostResolutionLearningPriorityRow")
        for field_name in ("analyst_label", "learning_scope_label"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "settled_outcome_signal_strength",
            "forecast_miss_severity",
            "source_evidence_gap",
            "calibration_freshness_score",
            "calibration_staleness_score",
            "review_backlog_pressure",
            "learning_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "review_backlog_count",
            _normalize_count("review_backlog_count", self.review_backlog_count),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_PRIORITY),
        )
        require_paper_only_flags("post-resolution learning priority row", self)
        _validate_row(self)
        _reject_unsafe_public_payload("row", _public_dict(self))
        _require_or_set_digest(self)


@dataclass(frozen=True)
class ResearchStrategyPostResolutionLearningPriorityReport:
    generated_at: datetime
    config_version: str
    analyst_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    attention_count: Decimal
    average_learning_priority_score: Decimal
    max_learning_priority_score: Decimal
    max_forecast_miss_severity: Decimal
    max_source_evidence_gap: Decimal
    min_calibration_freshness_score: Decimal
    max_review_backlog_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchStrategyPostResolutionLearningPriorityRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyPostResolutionLearningPriorityReport:
            raise ValueError(
                "report must be exactly ResearchStrategyPostResolutionLearningPriorityReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "analyst_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "attention_count",
            "max_review_backlog_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_learning_priority_score",
            "max_learning_priority_score",
            "max_forecast_miss_severity",
            "max_source_evidence_gap",
            "min_calibration_freshness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_PRIORITY),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        require_paper_only_flags("post-resolution learning priority report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("report", _public_dict(self))
        _require_or_set_digest(self)

    @property
    def public_payload(self) -> dict[str, Any]:
        return research_strategy_post_resolution_learning_priority_report_public_payload(
            self,
        )


def build_research_strategy_post_resolution_learning_priority_report(
    inputs: Iterable[ResearchStrategyPostResolutionLearningPriorityInput],
    *,
    config: ResearchStrategyPostResolutionLearningPriorityConfig,
    generated_at: datetime,
) -> ResearchStrategyPostResolutionLearningPriorityReport:
    if type(config) is not ResearchStrategyPostResolutionLearningPriorityConfig:
        raise ValueError(
            "config must be exactly ResearchStrategyPostResolutionLearningPriorityConfig",
        )
    require_paper_only_flags("post-resolution learning priority config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (_row_from_input(item, config=config) for item in input_rows),
            key=_row_sort_key,
        ),
    )
    report_parts = dict(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        analyst_count=_count(len({row.analyst_label for row in rows})),
        row_count=_count(len(rows)),
        pass_count=_count(sum(1 for row in rows if row.status == "pass")),
        watch_count=_count(sum(1 for row in rows if row.status == "watch")),
        block_count=_count(sum(1 for row in rows if row.status == "block")),
        attention_count=_count(sum(1 for row in rows if row.status != "pass")),
        average_learning_priority_score=_average(row.learning_priority_score for row in rows),
        max_learning_priority_score=max(
            (row.learning_priority_score for row in rows),
            default=ZERO_RATIO,
        ),
        max_forecast_miss_severity=max(
            (row.forecast_miss_severity for row in rows),
            default=ZERO_RATIO,
        ),
        max_source_evidence_gap=max(
            (row.source_evidence_gap for row in rows),
            default=ZERO_RATIO,
        ),
        min_calibration_freshness_score=min(
            (row.calibration_freshness_score for row in rows),
            default=ZERO_RATIO,
        ),
        max_review_backlog_count=max(
            (row.review_backlog_count for row in rows),
            default=ZERO_COUNT,
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
        paper_only=True,
        report_only=True,
        readonly=True,
    )
    return ResearchStrategyPostResolutionLearningPriorityReport(
        **report_parts,
        derived_validation_digest=_digest_public(report_parts),
    )


def research_strategy_post_resolution_learning_priority_report_public_payload(
    report: ResearchStrategyPostResolutionLearningPriorityReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyPostResolutionLearningPriorityReport:
        raise ValueError(
            "report must be exactly ResearchStrategyPostResolutionLearningPriorityReport",
        )
    require_paper_only_flags("post-resolution learning priority report", report)
    _require_or_set_digest(report)
    payload = json_ready_no_floats(report)
    if not isinstance(payload, dict):
        raise ValueError("public payload must be a JSON object")
    validate_research_strategy_post_resolution_learning_priority_public_payload(payload)
    return payload


def validate_research_strategy_post_resolution_learning_priority_public_payload(
    payload: object,
) -> bool:
    if not isinstance(payload, dict):
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_payload("public payload", payload)
    _reject_raw_numeric_payload(payload)
    _require_payload_flags(payload)
    _validate_payload_digest_tree(payload)
    return True


def _row_from_input(
    item: ResearchStrategyPostResolutionLearningPriorityInput,
    *,
    config: ResearchStrategyPostResolutionLearningPriorityConfig,
) -> ResearchStrategyPostResolutionLearningPriorityRow:
    calibration_staleness_score = _clamp_ratio(
        ONE_RATIO - item.calibration_freshness_score,
    )
    review_backlog_pressure = _safe_ratio(
        item.review_backlog_count,
        config.block_min_review_backlog_count,
    )
    learning_priority_score = _learning_priority_score(
        item=item,
        calibration_staleness_score=calibration_staleness_score,
        review_backlog_pressure=review_backlog_pressure,
        config=config,
    )
    status = _row_status(
        item=item,
        learning_priority_score=learning_priority_score,
        config=config,
    )
    row_parts = dict(
        analyst_label=item.analyst_label,
        learning_scope_label=item.learning_scope_label,
        settled_outcome_signal_strength=item.settled_outcome_signal_strength,
        forecast_miss_severity=item.forecast_miss_severity,
        source_evidence_gap=item.source_evidence_gap,
        calibration_freshness_score=item.calibration_freshness_score,
        review_backlog_count=item.review_backlog_count,
        calibration_staleness_score=calibration_staleness_score,
        review_backlog_pressure=review_backlog_pressure,
        learning_priority_score=learning_priority_score,
        status=status,
        reason_codes=_row_reason_codes(
            item=item,
            status=status,
            learning_priority_score=learning_priority_score,
            config=config,
        ),
        paper_only=True,
        report_only=True,
        readonly=True,
    )
    return ResearchStrategyPostResolutionLearningPriorityRow(
        **row_parts,
        derived_validation_digest=_digest_public(row_parts),
    )


def _learning_priority_score(
    *,
    item: ResearchStrategyPostResolutionLearningPriorityInput,
    calibration_staleness_score: Decimal,
    review_backlog_pressure: Decimal,
    config: ResearchStrategyPostResolutionLearningPriorityConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            item.settled_outcome_signal_strength * config.settled_outcome_signal_weight
            + item.forecast_miss_severity * config.forecast_miss_weight
            + item.source_evidence_gap * config.source_evidence_gap_weight
            + calibration_staleness_score * config.calibration_staleness_weight
            + review_backlog_pressure * config.review_backlog_weight,
        )


def _row_status(
    *,
    item: ResearchStrategyPostResolutionLearningPriorityInput,
    learning_priority_score: Decimal,
    config: ResearchStrategyPostResolutionLearningPriorityConfig,
) -> str:
    if (
        learning_priority_score >= config.block_min_learning_priority_score
        or item.settled_outcome_signal_strength
        >= config.block_min_settled_outcome_signal_strength
        or item.forecast_miss_severity >= config.block_min_forecast_miss_severity
        or item.source_evidence_gap >= config.block_min_source_evidence_gap
        or item.calibration_freshness_score
        <= config.block_max_calibration_freshness_score
        or item.review_backlog_count >= config.block_min_review_backlog_count
    ):
        return "block"
    if (
        learning_priority_score >= config.watch_min_learning_priority_score
        or item.settled_outcome_signal_strength
        >= config.watch_min_settled_outcome_signal_strength
        or item.forecast_miss_severity >= config.watch_min_forecast_miss_severity
        or item.source_evidence_gap >= config.watch_min_source_evidence_gap
        or item.calibration_freshness_score
        <= config.watch_max_calibration_freshness_score
        or item.review_backlog_count >= config.watch_min_review_backlog_count
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    item: ResearchStrategyPostResolutionLearningPriorityInput,
    status: str,
    learning_priority_score: Decimal,
    config: ResearchStrategyPostResolutionLearningPriorityConfig,
) -> tuple[str, ...]:
    if status == "pass":
        return (PASS_REASON,)
    codes: set[str] = set()
    if (
        learning_priority_score >= config.block_min_learning_priority_score
        or item.settled_outcome_signal_strength
        >= config.block_min_settled_outcome_signal_strength
    ):
        codes.add("settled_outcome_signal_block")
    elif (
        learning_priority_score >= config.watch_min_learning_priority_score
        or item.settled_outcome_signal_strength
        >= config.watch_min_settled_outcome_signal_strength
    ):
        codes.add("settled_outcome_signal_watch")
    if item.forecast_miss_severity >= config.block_min_forecast_miss_severity:
        codes.add("forecast_miss_block")
    elif item.forecast_miss_severity >= config.watch_min_forecast_miss_severity:
        codes.add("forecast_miss_watch")
    if item.source_evidence_gap >= config.block_min_source_evidence_gap:
        codes.add("source_evidence_gap_block")
    elif item.source_evidence_gap >= config.watch_min_source_evidence_gap:
        codes.add("source_evidence_gap_watch")
    if item.calibration_freshness_score <= config.block_max_calibration_freshness_score:
        codes.add("calibration_freshness_block")
    elif item.calibration_freshness_score <= config.watch_max_calibration_freshness_score:
        codes.add("calibration_freshness_watch")
    if item.review_backlog_count >= config.block_min_review_backlog_count:
        codes.add("review_backlog_block")
    elif item.review_backlog_count >= config.watch_min_review_backlog_count:
        codes.add("review_backlog_watch")
    if status == "block":
        codes.add(BLOCK_REASON)
    else:
        codes.add(WATCH_REASON)
    return tuple(reason_code for reason_code in ROW_REASON_PRIORITY if reason_code in codes)


def _report_status(
    rows: tuple[ResearchStrategyPostResolutionLearningPriorityRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyPostResolutionLearningPriorityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON, PASS_REASON)
    status = _report_status(rows)
    codes = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code not in (PASS_REASON, WATCH_REASON, BLOCK_REASON)
    }
    if status == "block":
        codes.add(BLOCK_REASON)
    elif status == "watch":
        codes.add(WATCH_REASON)
    else:
        codes.add(PASS_REASON)
    return tuple(reason_code for reason_code in REPORT_REASON_PRIORITY if reason_code in codes)


def _row_sort_key(
    row: ResearchStrategyPostResolutionLearningPriorityRow,
) -> tuple[Decimal, Decimal, str, str]:
    status_rank = {
        "block": Decimal("0"),
        "watch": Decimal("1"),
        "pass": Decimal("2"),
    }[row.status]
    return (
        status_rank,
        -row.learning_priority_score,
        row.analyst_label,
        row.learning_scope_label,
    )


def _normalize_inputs(
    inputs: Iterable[ResearchStrategyPostResolutionLearningPriorityInput],
) -> tuple[ResearchStrategyPostResolutionLearningPriorityInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        rows = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchStrategyPostResolutionLearningPriorityInput:
            raise ValueError(
                "inputs must contain ResearchStrategyPostResolutionLearningPriorityInput values",
            )
        require_paper_only_flags("post-resolution learning priority input", row)
        _reject_unsafe_public_payload("input", _public_dict(row))
        key = (row.analyst_label, row.learning_scope_label)
        if key in seen_keys:
            raise ValueError("duplicate analyst learning scope")
        seen_keys.add(key)
    return rows


def _normalize_rows(
    values: Iterable[ResearchStrategyPostResolutionLearningPriorityRow],
) -> tuple[ResearchStrategyPostResolutionLearningPriorityRow, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchStrategyPostResolutionLearningPriorityRow:
            raise ValueError(
                "rows must contain ResearchStrategyPostResolutionLearningPriorityRow values",
            )
        require_paper_only_flags("post-resolution learning priority row", row)
        _reject_unsafe_public_payload("row", _public_dict(row))
        _require_or_set_digest(row)
        key = (row.analyst_label, row.learning_scope_label)
        if key in seen_keys:
            raise ValueError("rows must be unique by analyst and learning scope")
        seen_keys.add(key)
    return rows


def _validate_config(
    config: ResearchStrategyPostResolutionLearningPriorityConfig,
) -> None:
    if (
        config.watch_min_learning_priority_score
        >= config.block_min_learning_priority_score
    ):
        raise ValueError("watch priority threshold must be below block threshold")
    if (
        config.watch_min_settled_outcome_signal_strength
        >= config.block_min_settled_outcome_signal_strength
    ):
        raise ValueError("settled outcome signal threshold order is invalid")
    if config.watch_min_forecast_miss_severity >= config.block_min_forecast_miss_severity:
        raise ValueError("forecast miss threshold order is invalid")
    if config.watch_min_source_evidence_gap >= config.block_min_source_evidence_gap:
        raise ValueError("source evidence gap threshold order is invalid")
    if (
        config.watch_max_calibration_freshness_score
        <= config.block_max_calibration_freshness_score
    ):
        raise ValueError("calibration freshness threshold order is invalid")
    if config.watch_min_review_backlog_count >= config.block_min_review_backlog_count:
        raise ValueError("review backlog threshold order is invalid")
    _require_ratio_total(
        config.settled_outcome_signal_weight,
        config.forecast_miss_weight,
        config.source_evidence_gap_weight,
        config.calibration_staleness_weight,
        config.review_backlog_weight,
    )


def _validate_row(row: ResearchStrategyPostResolutionLearningPriorityRow) -> None:
    if row.calibration_staleness_score != _clamp_ratio(
        ONE_RATIO - row.calibration_freshness_score,
    ):
        raise ValueError("calibration_staleness_score must match freshness score")
    if row.status == "pass" and row.reason_codes != (PASS_REASON,):
        raise ValueError("pass rows must use pass reason")
    if row.status != "pass" and row.reason_codes == (PASS_REASON,):
        raise ValueError("attention rows must explain learning priority")
    expected_digest = _digest_public(_public_dict(row, include_digest=False))
    if row.derived_validation_digest not in ("", expected_digest):
        raise ValueError("derived_validation_digest payload mismatch")


def _validate_report(report: ResearchStrategyPostResolutionLearningPriorityReport) -> None:
    rows = report.rows
    if report.analyst_count != _count(len({row.analyst_label for row in rows})):
        raise ValueError("analyst_count must match rows")
    if report.row_count != _count(len(rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _count(sum(1 for row in rows if row.status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(sum(1 for row in rows if row.status == "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(sum(1 for row in rows if row.status == "block")):
        raise ValueError("block_count must match rows")
    if report.attention_count != _count(sum(1 for row in rows if row.status != "pass")):
        raise ValueError("attention_count must match rows")
    if report.average_learning_priority_score != _average(
        row.learning_priority_score for row in rows
    ):
        raise ValueError("average_learning_priority_score must match rows")
    if report.max_learning_priority_score != max(
        (row.learning_priority_score for row in rows),
        default=ZERO_RATIO,
    ):
        raise ValueError("max_learning_priority_score must match rows")
    if report.max_forecast_miss_severity != max(
        (row.forecast_miss_severity for row in rows),
        default=ZERO_RATIO,
    ):
        raise ValueError("max_forecast_miss_severity must match rows")
    if report.max_source_evidence_gap != max(
        (row.source_evidence_gap for row in rows),
        default=ZERO_RATIO,
    ):
        raise ValueError("max_source_evidence_gap must match rows")
    if report.min_calibration_freshness_score != min(
        (row.calibration_freshness_score for row in rows),
        default=ZERO_RATIO,
    ):
        raise ValueError("min_calibration_freshness_score must match rows")
    if report.max_review_backlog_count != max(
        (row.review_backlog_count for row in rows),
        default=ZERO_COUNT,
    ):
        raise ValueError("max_review_backlog_count must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use stable priority sort")
    expected_digest = _digest_public(_public_dict(report, include_digest=False))
    if report.derived_validation_digest not in ("", expected_digest):
        raise ValueError("derived_validation_digest payload mismatch")


def _normalize_reason_codes(
    field_name: str,
    value: Iterable[str],
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    ranks = {reason_code: index for index, reason_code in enumerate(allowed_values)}
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in ranks:
            raise ValueError(f"{field_name} must contain known values")
    expected = tuple(reason_code for reason_code in allowed_values if reason_code in reason_codes)
    if reason_codes != expected:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in POST_RESOLUTION_LEARNING_PRIORITY_STATUSES:
        raise ValueError(f"{field_name} statuses must be pass, watch, or block")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_public_text(value)


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize_count(value)
    if normalized != value:
        raise ValueError(f"{field_name} must be a whole Decimal")
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize_ratio(value)
    if normalized != value:
        raise ValueError(f"{field_name} must be quantized to 0.000001")
    if normalized < ZERO_RATIO or normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _require_ratio_total(*values: Decimal) -> None:
    with localcontext(DECIMAL_CONTEXT):
        total = _quantize_ratio(sum(values, ZERO_RATIO))
    if total != ONE_RATIO:
        raise ValueError("learning priority weights must sum to 1.000000")


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO_COUNT:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(numerator / denominator)


def _average(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(sum(items, ZERO_RATIO) / Decimal(len(items)))


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize_ratio(value)
    if normalized < ZERO_RATIO:
        return ZERO_RATIO
    if normalized > ONE_RATIO:
        return ONE_RATIO
    return normalized


def _quantize_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _quantize_count(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(COUNT_QUANTUM)


def _count(value: int) -> Decimal:
    return _quantize_count(Decimal(value))


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_or_set_digest(value: object) -> None:
    current = getattr(value, DIGEST_FIELD)
    expected = _digest_public(_public_dict(value, include_digest=False))
    if current == "":
        object.__setattr__(value, DIGEST_FIELD, expected)
        return
    if type(current) is not str or current != expected:
        raise ValueError("derived_validation_digest payload mismatch")
    _require_digest(DIGEST_FIELD, current)


def _digest_public(value: object) -> str:
    ready = json_ready_no_floats(value)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _public_dict(value: object, *, include_digest: bool = True) -> dict[str, Any]:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: getattr(value, field.name)
            for field in fields(value)
            if include_digest or field.name != DIGEST_FIELD
        }
    if isinstance(value, dict):
        if include_digest:
            return dict(value)
        return {key: item for key, item in value.items() if key != DIGEST_FIELD}
    raise ValueError("value must be a public object")


def _validate_payload_digest_tree(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            _validate_payload_digest_tree(item)
        if DIGEST_FIELD in value:
            current = value[DIGEST_FIELD]
            if type(current) is not str or current != _digest_public(
                _public_dict(value, include_digest=False),
            ):
                raise ValueError("derived_validation_digest payload mismatch")
            _require_digest(DIGEST_FIELD, current)
        return
    if isinstance(value, list):
        for item in value:
            _validate_payload_digest_tree(item)


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")
    if any(character not in HEX_DIGITS for character in value):
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")


def _require_payload_flags(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in ("paper_only", "report_only", "readonly") and item is not True:
                raise ValueError(f"{key} must be True")
            _require_payload_flags(item)
        return
    if isinstance(value, list):
        for item in value:
            _require_payload_flags(item)


def _reject_raw_numeric_payload(value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise ValueError("public payload numeric values must be Decimal strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_raw_numeric_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_raw_numeric_payload(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, _public_dict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("unsafe public key")
            _reject_public_text(key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, str):
        _reject_public_text(value)
        return
    if type(value) in (Decimal, datetime, bool) or value is None:
        return
    raise ValueError(f"unsafe public payload value in {label}")


def _reject_public_text(value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError("unsafe public text")
