"""Pure strategy human-review queue SLA report reducer."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any


DEFAULT_RESEARCH_STRATEGY_HUMAN_REVIEW_QUEUE_SLA_REPORT_CONFIG_VERSION = (
    "research-strategy-human-review-queue-sla-report-v0"
)

STRATEGY_HUMAN_REVIEW_QUEUE_SLA_STATUSES = ("pass", "watch", "block")

NO_INPUTS_REASON = "human_review_queue_sla_no_inputs"
REPORT_PASS_REASON = "human_review_queue_sla_report_pass"
REPORT_WATCH_REASON = "human_review_queue_sla_report_watch"
REPORT_BLOCK_REASON = "human_review_queue_sla_report_block"
CLEAR_REASON = "human_review_queue_sla_clear"
REVIEW_AGE_BLOCK_REASON = "review_age_block"
EVIDENCE_URGENCY_BLOCK_REASON = "evidence_urgency_block"
SETTLEMENT_RISK_BLOCK_REASON = "settlement_risk_block"
QUEUE_CAPACITY_BLOCK_REASON = "queue_capacity_block"
REVIEW_AGE_WATCH_REASON = "review_age_watch"
EVIDENCE_URGENCY_WATCH_REASON = "evidence_urgency_watch"
SETTLEMENT_RISK_WATCH_REASON = "settlement_risk_watch"
QUEUE_CAPACITY_WATCH_REASON = "queue_capacity_watch"

STRATEGY_HUMAN_REVIEW_QUEUE_SLA_REASON_CODES = (
    NO_INPUTS_REASON,
    REPORT_PASS_REASON,
    REPORT_WATCH_REASON,
    REPORT_BLOCK_REASON,
    CLEAR_REASON,
    REVIEW_AGE_BLOCK_REASON,
    EVIDENCE_URGENCY_BLOCK_REASON,
    SETTLEMENT_RISK_BLOCK_REASON,
    QUEUE_CAPACITY_BLOCK_REASON,
    REVIEW_AGE_WATCH_REASON,
    EVIDENCE_URGENCY_WATCH_REASON,
    SETTLEMENT_RISK_WATCH_REASON,
    QUEUE_CAPACITY_WATCH_REASON,
)

_QUANT = Decimal("0.000001")
_WHOLE_QUANT = Decimal("1")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
_REASON_RANK = {
    reason_code: index
    for index, reason_code in enumerate(STRATEGY_HUMAN_REVIEW_QUEUE_SLA_REASON_CODES)
}
_LOWER = "abcdefghijklmnopqrstuvwxyz"
_DIGITS = "0123456789"
_LABEL_CHARS = frozenset(_LOWER + _DIGITS + "_.-")


def _j(*parts: str) -> str:
    return "".join(parts)


_UNSAFE_PUBLIC_FRAGMENTS = (
    _j("can", "didate", "_", "id"),
    _j("raw", "_", "can", "didate"),
    _j("ma", "rket", "_", "id"),
    _j("ma", "rket", "_", "slug"),
    _j("condition", "_", "id"),
    _j("sl", "ug"),
    _j("ques", "tion"),
    _j("source", "_", "text"),
    _j("raw", "_", "text"),
    _j("source", "_", "u", "rl"),
    _j("u", "rl"),
    _j(":", "//"),
    _j("w", "ww", "."),
    _j("d", "sn"),
    _j("table", "_", "name"),
    _j("to", "ken"),
    _j("wall", "et"),
    _j("au", "th"),
    _j("or", "der"),
    _j("tra", "de"),
    _j("b", "uy"),
    _j("se", "ll"),
    _j("rec", "ommend", "ation"),
    _j("siz", "ing"),
)

__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_HUMAN_REVIEW_QUEUE_SLA_REPORT_CONFIG_VERSION",
    "STRATEGY_HUMAN_REVIEW_QUEUE_SLA_STATUSES",
    "STRATEGY_HUMAN_REVIEW_QUEUE_SLA_REASON_CODES",
    "ResearchStrategyHumanReviewQueueSlaConfig",
    "ResearchStrategyHumanReviewQueueSlaInput",
    "ResearchStrategyHumanReviewQueueSlaReasonCodeCount",
    "ResearchStrategyHumanReviewQueueSlaReport",
    "ResearchStrategyHumanReviewQueueSlaRow",
    "build_research_strategy_human_review_queue_sla_report",
    "research_strategy_human_review_queue_sla_report_digest",
    "research_strategy_human_review_queue_sla_report_payload",
)


@dataclass(frozen=True)
class ResearchStrategyHumanReviewQueueSlaConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_HUMAN_REVIEW_QUEUE_SLA_REPORT_CONFIG_VERSION
    )
    watch_review_age_seconds: Decimal = Decimal("7200.000000")
    block_review_age_seconds: Decimal = Decimal("86400.000000")
    watch_evidence_urgency_score: Decimal = Decimal("0.650000")
    block_evidence_urgency_score: Decimal = Decimal("0.900000")
    watch_settlement_risk_pressure: Decimal = Decimal("0.550000")
    block_settlement_risk_pressure: Decimal = Decimal("0.850000")
    watch_queue_capacity_utilization: Decimal = Decimal("0.750000")
    block_queue_capacity_utilization: Decimal = Decimal("1.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyHumanReviewQueueSlaConfig:
            raise TypeError(
                "ResearchStrategyHumanReviewQueueSlaConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyHumanReviewQueueSlaConfig:
            raise ValueError(
                "config must be exactly ResearchStrategyHumanReviewQueueSlaConfig",
            )
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_HUMAN_REVIEW_QUEUE_SLA_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported value")
        for field_name in (
            "watch_review_age_seconds",
            "block_review_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_evidence_urgency_score",
            "block_evidence_urgency_score",
            "watch_settlement_risk_pressure",
            "block_settlement_risk_pressure",
            "watch_queue_capacity_utilization",
            "block_queue_capacity_utilization",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_review_age_seconds >= self.block_review_age_seconds:
            raise ValueError("watch_review_age_seconds must be below block threshold")
        if self.watch_evidence_urgency_score >= self.block_evidence_urgency_score:
            raise ValueError("watch_evidence_urgency_score must be below block threshold")
        if self.watch_settlement_risk_pressure >= self.block_settlement_risk_pressure:
            raise ValueError("watch_settlement_risk_pressure must be below block threshold")
        if self.watch_queue_capacity_utilization >= self.block_queue_capacity_utilization:
            raise ValueError(
                "watch_queue_capacity_utilization must be below block threshold",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyHumanReviewQueueSlaInput:
    review_bucket: str
    review_stage: str
    review_item_count: Decimal
    max_review_age_seconds: Decimal
    average_review_age_seconds: Decimal
    evidence_urgency_score: Decimal
    settlement_risk_pressure: Decimal
    queue_capacity_available: Decimal
    queue_capacity_required: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyHumanReviewQueueSlaInput:
            raise TypeError(
                "ResearchStrategyHumanReviewQueueSlaInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyHumanReviewQueueSlaInput:
            raise ValueError("input must be exactly ResearchStrategyHumanReviewQueueSlaInput")
        for field_name in ("review_bucket", "review_stage"):
            object.__setattr__(
                self,
                field_name,
                _require_public_label(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "review_item_count",
            _require_nonnegative_whole_decimal(
                "review_item_count",
                self.review_item_count,
            ),
        )
        for field_name in ("max_review_age_seconds", "average_review_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("evidence_urgency_score", "settlement_risk_pressure"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("queue_capacity_available", "queue_capacity_required"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.average_review_age_seconds > self.max_review_age_seconds:
            raise ValueError("average_review_age_seconds must not exceed max_review_age_seconds")
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyHumanReviewQueueSlaRow:
    review_bucket: str
    review_stage: str
    observed_at: datetime
    status: str
    review_item_count: Decimal
    max_review_age_seconds: Decimal
    average_review_age_seconds: Decimal
    evidence_urgency_score: Decimal
    settlement_risk_pressure: Decimal
    queue_capacity_available: Decimal
    queue_capacity_required: Decimal
    queue_capacity_utilization: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyHumanReviewQueueSlaRow:
            raise TypeError(
                "ResearchStrategyHumanReviewQueueSlaRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyHumanReviewQueueSlaRow:
            raise ValueError("row must be exactly ResearchStrategyHumanReviewQueueSlaRow")
        for field_name in ("review_bucket", "review_stage"):
            object.__setattr__(
                self,
                field_name,
                _require_public_label(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "review_item_count",
            _require_nonnegative_whole_decimal(
                "review_item_count",
                self.review_item_count,
            ),
        )
        for field_name in ("max_review_age_seconds", "average_review_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "evidence_urgency_score",
            "settlement_risk_pressure",
            "queue_capacity_utilization",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("queue_capacity_available", "queue_capacity_required"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchStrategyHumanReviewQueueSlaReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyHumanReviewQueueSlaReasonCodeCount:
            raise TypeError(
                "ResearchStrategyHumanReviewQueueSlaReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyHumanReviewQueueSlaReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "ResearchStrategyHumanReviewQueueSlaReasonCodeCount",
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
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class ResearchStrategyHumanReviewQueueSlaReport:
    generated_at: datetime
    config_version: str
    report_status: str
    review_age_status: str
    evidence_urgency_status: str
    settlement_risk_status: str
    queue_capacity_status: str
    review_bucket_count: Decimal
    review_item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_review_age_seconds: Decimal
    average_review_age_seconds: Decimal
    max_evidence_urgency_score: Decimal
    max_settlement_risk_pressure: Decimal
    max_queue_capacity_utilization: Decimal
    rows: tuple[ResearchStrategyHumanReviewQueueSlaRow, ...]
    reason_code_counts: tuple[ResearchStrategyHumanReviewQueueSlaReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyHumanReviewQueueSlaReport:
            raise TypeError(
                "ResearchStrategyHumanReviewQueueSlaReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyHumanReviewQueueSlaReport:
            raise ValueError("report must be exactly ResearchStrategyHumanReviewQueueSlaReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_HUMAN_REVIEW_QUEUE_SLA_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported value")
        for field_name in (
            "report_status",
            "review_age_status",
            "evidence_urgency_status",
            "settlement_risk_status",
            "queue_capacity_status",
        ):
            _require_status(field_name, getattr(self, field_name))
        for field_name in (
            "review_bucket_count",
            "review_item_count",
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
            "max_review_age_seconds",
            "average_review_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_evidence_urgency_score",
            "max_settlement_risk_pressure",
            "max_queue_capacity_utilization",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags("report", self)
        _validate_report(self)
        if self.derived_validation_digest:
            _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
            expected_digest = _report_digest_from_values(
                _report_payload_core(self, include_digest=False),
            )
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest does not match report payload")
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_digest_from_values(_report_payload_core(self, include_digest=False)),
            )

    @property
    def payload(self) -> dict[str, Any]:
        return research_strategy_human_review_queue_sla_report_payload(self)


def build_research_strategy_human_review_queue_sla_report(
    review_inputs: tuple[object, ...] | list[object],
    *,
    config: ResearchStrategyHumanReviewQueueSlaConfig,
    generated_at: datetime,
) -> ResearchStrategyHumanReviewQueueSlaReport:
    if type(config) is not ResearchStrategyHumanReviewQueueSlaConfig:
        raise ValueError("config must be ResearchStrategyHumanReviewQueueSlaConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(review_inputs, generated_at=generated_at_utc)
    rows = tuple(
        sorted(
            (_build_row(item, config=config) for item in inputs),
            key=lambda row: (
                _STATUS_RANK[row.status],
                row.review_bucket,
                row.review_stage,
                row.observed_at.isoformat(),
            ),
        ),
    )
    reason_codes = _report_reason_codes(rows)
    report_status = _status_from_reason_codes(reason_codes)
    return ResearchStrategyHumanReviewQueueSlaReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=report_status,
        review_age_status=_component_status(rows, REVIEW_AGE_BLOCK_REASON, REVIEW_AGE_WATCH_REASON),
        evidence_urgency_status=_component_status(
            rows,
            EVIDENCE_URGENCY_BLOCK_REASON,
            EVIDENCE_URGENCY_WATCH_REASON,
        ),
        settlement_risk_status=_component_status(
            rows,
            SETTLEMENT_RISK_BLOCK_REASON,
            SETTLEMENT_RISK_WATCH_REASON,
        ),
        queue_capacity_status=_component_status(
            rows,
            QUEUE_CAPACITY_BLOCK_REASON,
            QUEUE_CAPACITY_WATCH_REASON,
        ),
        review_bucket_count=_decimal_count(len(rows)),
        review_item_count=sum((row.review_item_count for row in rows), _ZERO),
        pass_count=_decimal_count(sum(1 for row in rows if row.status == "pass")),
        watch_count=_decimal_count(sum(1 for row in rows if row.status == "watch")),
        block_count=_decimal_count(sum(1 for row in rows if row.status == "block")),
        max_review_age_seconds=max(
            (row.max_review_age_seconds for row in rows),
            default=_ZERO,
        ),
        average_review_age_seconds=_average_decimal(
            tuple(row.average_review_age_seconds for row in rows),
        ),
        max_evidence_urgency_score=max(
            (row.evidence_urgency_score for row in rows),
            default=_ZERO,
        ),
        max_settlement_risk_pressure=max(
            (row.settlement_risk_pressure for row in rows),
            default=_ZERO,
        ),
        max_queue_capacity_utilization=max(
            (row.queue_capacity_utilization for row in rows),
            default=_ZERO,
        ),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows),
        reason_codes=reason_codes,
    )


def research_strategy_human_review_queue_sla_report_payload(
    value: object,
) -> dict[str, Any]:
    if isinstance(
        value,
        (
            ResearchStrategyHumanReviewQueueSlaConfig,
            ResearchStrategyHumanReviewQueueSlaInput,
            ResearchStrategyHumanReviewQueueSlaRow,
            ResearchStrategyHumanReviewQueueSlaReasonCodeCount,
            ResearchStrategyHumanReviewQueueSlaReport,
        ),
    ):
        _require_hard_flags("payload", value)
    elif type(value) is not dict:
        raise ValueError("value must be a queue SLA dataclass or payload dict")
    payload = _payload_value(value)
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _validate_payload_flags(payload, "payload")
    _reject_unsafe_public_payload(payload)
    if "derived_validation_digest" in payload:
        _validate_payload_digest(payload)
    return payload


def research_strategy_human_review_queue_sla_report_digest(value: object) -> str:
    payload = research_strategy_human_review_queue_sla_report_payload(value)
    if "derived_validation_digest" not in payload:
        return _report_digest_from_values(payload)
    digest = payload["derived_validation_digest"]
    _require_sha256_digest("derived_validation_digest", digest)
    return digest


def _build_row(
    item: ResearchStrategyHumanReviewQueueSlaInput,
    *,
    config: ResearchStrategyHumanReviewQueueSlaConfig,
) -> ResearchStrategyHumanReviewQueueSlaRow:
    utilization = _capacity_utilization(
        item.queue_capacity_required,
        item.queue_capacity_available,
    )
    generated_reasons = _row_generated_reason_codes(
        item,
        utilization=utilization,
        config=config,
    )
    reason_codes = (*item.reason_codes, *generated_reasons)
    if not generated_reasons:
        reason_codes = (*item.reason_codes, CLEAR_REASON)
    return ResearchStrategyHumanReviewQueueSlaRow(
        review_bucket=item.review_bucket,
        review_stage=item.review_stage,
        observed_at=item.observed_at,
        status=_status_from_reason_codes(reason_codes),
        review_item_count=item.review_item_count,
        max_review_age_seconds=item.max_review_age_seconds,
        average_review_age_seconds=item.average_review_age_seconds,
        evidence_urgency_score=item.evidence_urgency_score,
        settlement_risk_pressure=item.settlement_risk_pressure,
        queue_capacity_available=item.queue_capacity_available,
        queue_capacity_required=item.queue_capacity_required,
        queue_capacity_utilization=utilization,
        reason_codes=_normalize_reason_codes(reason_codes),
    )


def _row_generated_reason_codes(
    item: ResearchStrategyHumanReviewQueueSlaInput,
    *,
    utilization: Decimal,
    config: ResearchStrategyHumanReviewQueueSlaConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    _append_threshold_reason(
        reason_codes,
        item.max_review_age_seconds,
        config.watch_review_age_seconds,
        config.block_review_age_seconds,
        REVIEW_AGE_BLOCK_REASON,
        REVIEW_AGE_WATCH_REASON,
    )
    _append_threshold_reason(
        reason_codes,
        item.evidence_urgency_score,
        config.watch_evidence_urgency_score,
        config.block_evidence_urgency_score,
        EVIDENCE_URGENCY_BLOCK_REASON,
        EVIDENCE_URGENCY_WATCH_REASON,
    )
    _append_threshold_reason(
        reason_codes,
        item.settlement_risk_pressure,
        config.watch_settlement_risk_pressure,
        config.block_settlement_risk_pressure,
        SETTLEMENT_RISK_BLOCK_REASON,
        SETTLEMENT_RISK_WATCH_REASON,
    )
    _append_threshold_reason(
        reason_codes,
        utilization,
        config.watch_queue_capacity_utilization,
        config.block_queue_capacity_utilization,
        QUEUE_CAPACITY_BLOCK_REASON,
        QUEUE_CAPACITY_WATCH_REASON,
    )
    return tuple(reason_codes)


def _append_threshold_reason(
    reason_codes: list[str],
    value: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
    block_reason: str,
    watch_reason: str,
) -> None:
    if value >= block_threshold:
        reason_codes.append(block_reason)
    elif value >= watch_threshold:
        reason_codes.append(watch_reason)


def _capacity_utilization(required: Decimal, available: Decimal) -> Decimal:
    if required == _ZERO:
        return _ZERO
    if available == _ZERO:
        return _ONE
    return min(_ONE, _divide_decimal(required, available))


def _normalize_inputs(
    review_inputs: tuple[object, ...] | list[object],
    *,
    generated_at: datetime,
) -> tuple[ResearchStrategyHumanReviewQueueSlaInput, ...]:
    if type(review_inputs) not in (list, tuple):
        raise ValueError("review_inputs must be a list or tuple")
    normalized = tuple(review_inputs)
    seen: set[tuple[str, str]] = set()
    for item in normalized:
        if type(item) is not ResearchStrategyHumanReviewQueueSlaInput:
            raise ValueError(
                "review_inputs must contain ResearchStrategyHumanReviewQueueSlaInput",
            )
        _require_hard_flags("input", item)
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        key = (item.review_bucket, item.review_stage)
        if key in seen:
            raise ValueError("review_inputs must not contain duplicate aggregate keys")
        seen.add(key)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.review_bucket,
                item.review_stage,
                item.observed_at.isoformat(),
            ),
        ),
    )


def _report_reason_codes(
    rows: tuple[ResearchStrategyHumanReviewQueueSlaRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    generated = tuple(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code in _REASON_RANK and reason_code != CLEAR_REASON
    )
    report_status = _status_from_reason_codes(generated or (REPORT_PASS_REASON,))
    if report_status == "block":
        return _normalize_reason_codes((REPORT_BLOCK_REASON, *generated))
    if report_status == "watch":
        return _normalize_reason_codes((REPORT_WATCH_REASON, *generated))
    return (REPORT_PASS_REASON,)


def _reason_code_counts(
    rows: tuple[ResearchStrategyHumanReviewQueueSlaRow, ...],
) -> tuple[ResearchStrategyHumanReviewQueueSlaReasonCodeCount, ...]:
    if not rows:
        return ()
    counts: Counter[str] = Counter(
        reason_code for row in rows for reason_code in row.reason_codes
    )
    denominator = _decimal_count(len(rows))
    return tuple(
        ResearchStrategyHumanReviewQueueSlaReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            row_ratio=_divide_decimal(_decimal_count(count), denominator),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )


def _component_status(
    rows: tuple[ResearchStrategyHumanReviewQueueSlaRow, ...],
    block_reason: str,
    watch_reason: str,
) -> str:
    if not rows:
        return "block"
    if any(block_reason in row.reason_codes for row in rows):
        return "block"
    if any(watch_reason in row.reason_codes for row in rows):
        return "watch"
    return "pass"


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") or reason_code.endswith("report_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") or reason_code.endswith("report_watch") for reason_code in reason_codes):
        return "watch"
    if reason_codes == (NO_INPUTS_REASON,):
        return "block"
    return "pass"


def _report_payload_core(
    report: ResearchStrategyHumanReviewQueueSlaReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "report_status": report.report_status,
        "review_age_status": report.review_age_status,
        "evidence_urgency_status": report.evidence_urgency_status,
        "settlement_risk_status": report.settlement_risk_status,
        "queue_capacity_status": report.queue_capacity_status,
        "review_bucket_count": _decimal_to_string(report.review_bucket_count),
        "review_item_count": _decimal_to_string(report.review_item_count),
        "pass_count": _decimal_to_string(report.pass_count),
        "watch_count": _decimal_to_string(report.watch_count),
        "block_count": _decimal_to_string(report.block_count),
        "max_review_age_seconds": _decimal_to_string(report.max_review_age_seconds),
        "average_review_age_seconds": _decimal_to_string(report.average_review_age_seconds),
        "max_evidence_urgency_score": _decimal_to_string(report.max_evidence_urgency_score),
        "max_settlement_risk_pressure": _decimal_to_string(
            report.max_settlement_risk_pressure,
        ),
        "max_queue_capacity_utilization": _decimal_to_string(
            report.max_queue_capacity_utilization,
        ),
        "rows": [_row_payload(row) for row in report.rows],
        "reason_code_counts": [
            _reason_code_count_payload(reason_count)
            for reason_count in report.reason_code_counts
        ],
        "reason_codes": list(report.reason_codes),
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    if include_digest:
        payload["derived_validation_digest"] = report.derived_validation_digest
    return payload


def _row_payload(row: ResearchStrategyHumanReviewQueueSlaRow) -> dict[str, Any]:
    return {
        "review_bucket": row.review_bucket,
        "review_stage": row.review_stage,
        "observed_at": row.observed_at.isoformat(),
        "status": row.status,
        "review_item_count": _decimal_to_string(row.review_item_count),
        "max_review_age_seconds": _decimal_to_string(row.max_review_age_seconds),
        "average_review_age_seconds": _decimal_to_string(row.average_review_age_seconds),
        "evidence_urgency_score": _decimal_to_string(row.evidence_urgency_score),
        "settlement_risk_pressure": _decimal_to_string(row.settlement_risk_pressure),
        "queue_capacity_available": _decimal_to_string(row.queue_capacity_available),
        "queue_capacity_required": _decimal_to_string(row.queue_capacity_required),
        "queue_capacity_utilization": _decimal_to_string(row.queue_capacity_utilization),
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _reason_code_count_payload(
    reason_count: ResearchStrategyHumanReviewQueueSlaReasonCodeCount,
) -> dict[str, Any]:
    return {
        "reason_code": reason_count.reason_code,
        "count": _decimal_to_string(reason_count.count),
        "row_ratio": _decimal_to_string(reason_count.row_ratio),
        "paper_only": reason_count.paper_only,
        "report_only": reason_count.report_only,
        "readonly": reason_count.readonly,
    }


def _payload_value(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        if isinstance(value, ResearchStrategyHumanReviewQueueSlaReport):
            return _report_payload_core(value, include_digest=True)
        if isinstance(value, ResearchStrategyHumanReviewQueueSlaRow):
            return _row_payload(value)
        if isinstance(value, ResearchStrategyHumanReviewQueueSlaReasonCodeCount):
            return _reason_code_count_payload(value)
        result: dict[str, Any] = {}
        for field in fields(value):
            result[field.name] = _payload_value(getattr(value, field.name))
        return result
    if type(value) is Decimal:
        return _decimal_to_string(value)
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) is bool or type(value) is str or value is None:
        return value
    if type(value) in (int, float):
        raise ValueError("numeric public payload values must be Decimal strings")
    if type(value) is tuple or type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        return {
            _require_payload_key(key): _payload_value(item)
            for key, item in value.items()
        }
    raise ValueError("payload value is not public JSON safe")


def _report_digest_from_values(values: dict[str, Any]) -> str:
    _reject_unsafe_public_payload(values)
    encoded = json.dumps(
        values,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    expected = _report_digest_from_values(unsigned)
    if digest != expected:
        raise ValueError("derived_validation_digest does not match report payload")


def _validate_payload_flags(payload: dict[str, Any], label: str) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _reject_unsafe_public_payload(value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            _reject_unsafe_public_text(_require_payload_key(key))
            _reject_unsafe_public_payload(item)
        return
    if type(value) is list:
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(value)
        return
    if type(value) in (int, float) or type(value) is Decimal:
        raise ValueError("numeric public payload values must be Decimal strings")
    if value is None or type(value) is bool:
        return
    raise ValueError("unsafe public payload entry")


def _reject_unsafe_public_text(value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError("unsafe public payload entry")


def _normalize_rows(
    rows: tuple[ResearchStrategyHumanReviewQueueSlaRow, ...],
) -> tuple[ResearchStrategyHumanReviewQueueSlaRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchStrategyHumanReviewQueueSlaRow:
            raise ValueError("rows must contain ResearchStrategyHumanReviewQueueSlaRow")
        _require_hard_flags("row", row)
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _STATUS_RANK[row.status],
                row.review_bucket,
                row.review_stage,
                row.observed_at.isoformat(),
            ),
        ),
    )


def _normalize_reason_code_counts(
    reason_code_counts: tuple[ResearchStrategyHumanReviewQueueSlaReasonCodeCount, ...],
) -> tuple[ResearchStrategyHumanReviewQueueSlaReasonCodeCount, ...]:
    if type(reason_code_counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for reason_count in reason_code_counts:
        if type(reason_count) is not ResearchStrategyHumanReviewQueueSlaReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyHumanReviewQueueSlaReasonCodeCount",
            )
        _require_hard_flags("reason_code_counts", reason_count)
    return tuple(sorted(reason_code_counts, key=lambda item: (-item.count, item.reason_code)))


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple or not reason_codes:
        raise ValueError("reason_codes must be a non-empty tuple")
    normalized: list[str] = []
    seen: set[str] = set()
    for value in reason_codes:
        reason_code = _require_reason_code("reason_codes", value)
        if reason_code not in seen:
            normalized.append(reason_code)
            seen.add(reason_code)
    generated_codes = [code for code in normalized if code in _REASON_RANK]
    other_codes = [code for code in normalized if code not in _REASON_RANK]
    return tuple(other_codes) + tuple(
        code for code in STRATEGY_HUMAN_REVIEW_QUEUE_SLA_REASON_CODES if code in generated_codes
    )


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must contain strings")
    if value != value.strip() or value != value.lower() or not value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    if not all(char.isalnum() or char == "_" for char in value):
        raise ValueError(f"{field_name} must contain canonical reason codes")
    _reject_unsafe_public_text(value)
    return value


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value or value.lower() != value:
        raise ValueError(f"{field_name} must be public-safe label")
    if not all(char in _LABEL_CHARS for char in value):
        raise ValueError(f"{field_name} must be public-safe label")
    if len(value) > 128:
        raise ValueError(f"{field_name} must be public-safe label")
    try:
        _reject_unsafe_public_text(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be public-safe label") from exc
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STRATEGY_HUMAN_REVIEW_QUEUE_SLA_STATUSES:
        raise ValueError(f"{field_name} must be one of known public statuses")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    if not all(char in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.quantize(_WHOLE_QUANT):
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize_decimal(field_name, value)


def _quantize_decimal(field_name: str, value: Decimal) -> Decimal:
    try:
        with localcontext(_DECIMAL_CONTEXT):
            return value.quantize(_QUANT)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize_decimal("average", sum(values, _ZERO) / Decimal(len(values)))


def _divide_decimal(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize_decimal("ratio", numerator / denominator)


def _decimal_count(value: int) -> Decimal:
    return _quantize_decimal("count", Decimal(value))


def _decimal_to_string(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("payload decimal value must be a Decimal")
    return format(value, "f")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_payload_key(value: object) -> str:
    if type(value) is not str:
        raise ValueError("payload keys must be strings")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _validate_report(report: ResearchStrategyHumanReviewQueueSlaReport) -> None:
    rows = report.rows
    if report.review_bucket_count != _decimal_count(len(rows)):
        raise ValueError("review_bucket_count must match rows")
    if report.review_item_count != sum((row.review_item_count for row in rows), _ZERO):
        raise ValueError("review_item_count must match rows")
    if report.pass_count != _decimal_count(sum(1 for row in rows if row.status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(sum(1 for row in rows if row.status == "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(sum(1 for row in rows if row.status == "block")):
        raise ValueError("block_count must match rows")
    if report.max_review_age_seconds != max(
        (row.max_review_age_seconds for row in rows),
        default=_ZERO,
    ):
        raise ValueError("max_review_age_seconds must match rows")
    if report.average_review_age_seconds != _average_decimal(
        tuple(row.average_review_age_seconds for row in rows),
    ):
        raise ValueError("average_review_age_seconds must match rows")
    if report.max_evidence_urgency_score != max(
        (row.evidence_urgency_score for row in rows),
        default=_ZERO,
    ):
        raise ValueError("max_evidence_urgency_score must match rows")
    if report.max_settlement_risk_pressure != max(
        (row.settlement_risk_pressure for row in rows),
        default=_ZERO,
    ):
        raise ValueError("max_settlement_risk_pressure must match rows")
    if report.max_queue_capacity_utilization != max(
        (row.queue_capacity_utilization for row in rows),
        default=_ZERO,
    ):
        raise ValueError("max_queue_capacity_utilization must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.report_status != _status_from_reason_codes(report.reason_codes):
        raise ValueError("report_status must match reason_codes")
