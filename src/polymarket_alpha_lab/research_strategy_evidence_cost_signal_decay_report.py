"""Report-only evidence-cost signal decay research policy.

The module is deterministic and side-effect free. It accepts caller-supplied
rows, groups them into public report rows, and never exposes raw candidate
identifiers in the public payload.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from typing import Any

__all__ = (
    "ResearchStrategyEvidenceCostSignalDecayConfig",
    "ResearchStrategyEvidenceCostSignalDecayInput",
    "ResearchStrategyEvidenceCostSignalDecayReasonCodeCount",
    "ResearchStrategyEvidenceCostSignalDecayReport",
    "ResearchStrategyEvidenceCostSignalDecayRow",
    "build_research_strategy_evidence_cost_signal_decay_report",
    "research_strategy_evidence_cost_signal_decay_report_payload",
    "validate_research_strategy_evidence_cost_signal_decay_public_payload",
)


DEFAULT_CONFIG_VERSION = "research-strategy-evidence-cost-signal-decay-report-v0"
STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
STATUS_SORT_RANK = {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}

PASS_REASON = "strategy_evidence_cost_signal_decay_pass"
WATCH_REASON = "strategy_evidence_cost_signal_decay_watch"
BLOCK_REASON = "strategy_evidence_cost_signal_decay_block"
EMPTY_REASON = "strategy_evidence_cost_signal_decay_empty"
WEAK_SIGNAL_REASON = "strategy_evidence_cost_signal_decay_weak_signal"
STALE_SIGNAL_REASON = "strategy_evidence_cost_signal_decay_stale_signal"
SPARSE_EVIDENCE_REASON = "strategy_evidence_cost_signal_decay_sparse_evidence"
HIGH_COST_REASON = "strategy_evidence_cost_signal_decay_high_cost"
DECAYED_SIGNAL_REASON = "strategy_evidence_cost_signal_decay_decayed_signal"
STATUS_REASONS = (PASS_REASON, WATCH_REASON, BLOCK_REASON)
REASON_CODES = (
    PASS_REASON,
    WATCH_REASON,
    BLOCK_REASON,
    EMPTY_REASON,
    WEAK_SIGNAL_REASON,
    STALE_SIGNAL_REASON,
    SPARSE_EVIDENCE_REASON,
    HIGH_COST_REASON,
    DECAYED_SIGNAL_REASON,
)

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
HEX_DIGITS = "0123456789abcdef"
UNSAFE_PUBLIC_KEYS = {
    "candidate_id",
    "candidate_ids",
    "raw_candidate_id",
    "market_id",
    "market_ids",
    "market_slug",
    "market_slugs",
    "slug",
    "question",
    "source_url",
    "source_text",
    "dsn",
    "table",
    "table_name",
    "token",
}
UNSAFE_PUBLIC_VALUE_PARTS = (
    "http://",
    "https://",
    "postgres://",
    "postgresql://",
    "mysql://",
    "sqlite://",
    "wallet",
    " order",
    "order_",
    " trade",
    "trade_",
    "recommendation",
)
REPORT_PAYLOAD_SCHEMA = (
    "generated_at",
    "config_version",
    "candidate_count",
    "evidence_count",
    "pass_count",
    "watch_count",
    "block_count",
    "status",
    "rows",
    "reason_code_counts",
    "reason_codes",
    "fresh_signal_age_seconds",
    "stale_signal_age_seconds",
    "pass_signal_score_threshold",
    "watch_signal_score_threshold",
    "high_cost_watch_threshold",
    "high_cost_block_threshold",
    "min_evidence_count",
    "min_evidence_channel_count",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_PAYLOAD_SCHEMA = (
    "signal_hash",
    "evidence_count",
    "evidence_channel_count",
    "latest_observed_at",
    "latest_signal_age_seconds",
    "average_signal_strength",
    "decay_score",
    "decayed_signal_score",
    "total_evidence_cost",
    "cost_efficiency_score",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
REASON_CODE_COUNT_PAYLOAD_SCHEMA = (
    "reason_code",
    "row_count",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class ResearchStrategyEvidenceCostSignalDecayConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    fresh_signal_age_seconds: Decimal = Decimal("1800.000000")
    stale_signal_age_seconds: Decimal = Decimal("21600.000000")
    pass_signal_score_threshold: Decimal = Decimal("0.700000")
    watch_signal_score_threshold: Decimal = Decimal("0.400000")
    high_cost_watch_threshold: Decimal = Decimal("25.000000")
    high_cost_block_threshold: Decimal = Decimal("100.000000")
    min_evidence_count: Decimal = Decimal("2.000000")
    min_evidence_channel_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyEvidenceCostSignalDecayConfig:
            raise TypeError(
                "ResearchStrategyEvidenceCostSignalDecayConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyEvidenceCostSignalDecayConfig, "config")
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "fresh_signal_age_seconds",
            _positive_decimal("fresh_signal_age_seconds", self.fresh_signal_age_seconds),
        )
        object.__setattr__(
            self,
            "stale_signal_age_seconds",
            _positive_decimal("stale_signal_age_seconds", self.stale_signal_age_seconds),
        )
        if self.stale_signal_age_seconds <= self.fresh_signal_age_seconds:
            raise ValueError(
                "stale_signal_age_seconds must exceed fresh_signal_age_seconds",
            )
        for field_name in (
            "pass_signal_score_threshold",
            "watch_signal_score_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_signal_score_threshold <= self.watch_signal_score_threshold:
            raise ValueError(
                "pass_signal_score_threshold must exceed watch_signal_score_threshold",
            )
        for field_name in ("high_cost_watch_threshold", "high_cost_block_threshold"):
            object.__setattr__(
                self,
                field_name,
                _positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.high_cost_block_threshold <= self.high_cost_watch_threshold:
            raise ValueError(
                "high_cost_block_threshold must exceed high_cost_watch_threshold",
            )
        for field_name in ("min_evidence_count", "min_evidence_channel_count"):
            object.__setattr__(
                self,
                field_name,
                _positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyEvidenceCostSignalDecayInput:
    candidate_id: str
    evidence_channel: str
    signal_strength: Decimal
    evidence_cost: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyEvidenceCostSignalDecayInput:
            raise TypeError(
                "ResearchStrategyEvidenceCostSignalDecayInput "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyEvidenceCostSignalDecayInput, "input")
        _require_public_string("candidate_id", self.candidate_id)
        _require_public_string("evidence_channel", self.evidence_channel)
        object.__setattr__(
            self,
            "signal_strength",
            _probability_decimal("signal_strength", self.signal_strength),
        )
        object.__setattr__(
            self,
            "evidence_cost",
            _nonnegative_decimal("evidence_cost", self.evidence_cost),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyEvidenceCostSignalDecayRow:
    signal_hash: str
    evidence_count: Decimal
    evidence_channel_count: Decimal
    latest_observed_at: datetime
    latest_signal_age_seconds: Decimal
    average_signal_strength: Decimal
    decay_score: Decimal
    decayed_signal_score: Decimal
    total_evidence_cost: Decimal
    cost_efficiency_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyEvidenceCostSignalDecayRow:
            raise TypeError(
                "ResearchStrategyEvidenceCostSignalDecayRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyEvidenceCostSignalDecayRow, "row")
        _require_sha256_reference("signal_hash", self.signal_hash)
        for field_name in ("evidence_count", "evidence_channel_count"):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        object.__setattr__(
            self,
            "latest_signal_age_seconds",
            _nonnegative_decimal(
                "latest_signal_age_seconds",
                self.latest_signal_age_seconds,
            ),
        )
        for field_name in (
            "average_signal_strength",
            "decay_score",
            "decayed_signal_score",
            "cost_efficiency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "total_evidence_cost",
            _nonnegative_decimal("total_evidence_cost", self.total_evidence_cost),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchStrategyEvidenceCostSignalDecayReasonCodeCount:
    reason_code: str
    row_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyEvidenceCostSignalDecayReasonCodeCount:
            raise TypeError(
                "ResearchStrategyEvidenceCostSignalDecayReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyEvidenceCostSignalDecayReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "row_count",
            _nonnegative_whole_decimal("row_count", self.row_count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyEvidenceCostSignalDecayReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    evidence_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    status: str
    rows: tuple[ResearchStrategyEvidenceCostSignalDecayRow, ...]
    reason_code_counts: tuple[ResearchStrategyEvidenceCostSignalDecayReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    fresh_signal_age_seconds: Decimal = Decimal("1800.000000")
    stale_signal_age_seconds: Decimal = Decimal("21600.000000")
    pass_signal_score_threshold: Decimal = Decimal("0.700000")
    watch_signal_score_threshold: Decimal = Decimal("0.400000")
    high_cost_watch_threshold: Decimal = Decimal("25.000000")
    high_cost_block_threshold: Decimal = Decimal("100.000000")
    min_evidence_count: Decimal = Decimal("2.000000")
    min_evidence_channel_count: Decimal = Decimal("2.000000")
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyEvidenceCostSignalDecayReport:
            raise TypeError(
                "ResearchStrategyEvidenceCostSignalDecayReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyEvidenceCostSignalDecayReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        config = _config_from_report(self)
        for field_name in (
            "fresh_signal_age_seconds",
            "stale_signal_age_seconds",
            "pass_signal_score_threshold",
            "watch_signal_score_threshold",
            "high_cost_watch_threshold",
            "high_cost_block_threshold",
            "min_evidence_count",
            "min_evidence_channel_count",
        ):
            object.__setattr__(self, field_name, getattr(config, field_name))
        for field_name in (
            "candidate_count",
            "evidence_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_whole_decimal(field_name, getattr(self, field_name)),
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
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        expected_digest = _report_digest_from_public_payload(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
            return
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match public payload")

    @property
    def payload(self) -> "FrozenJsonObject":
        return research_strategy_evidence_cost_signal_decay_report_payload(self)


def build_research_strategy_evidence_cost_signal_decay_report(
    rows: Iterable[ResearchStrategyEvidenceCostSignalDecayInput],
    *,
    config: ResearchStrategyEvidenceCostSignalDecayConfig,
    generated_at: datetime,
) -> ResearchStrategyEvidenceCostSignalDecayReport:
    if type(config) is not ResearchStrategyEvidenceCostSignalDecayConfig:
        raise ValueError("config must be ResearchStrategyEvidenceCostSignalDecayConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(rows)
    for row in input_rows:
        if row.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")

    grouped: dict[str, list[ResearchStrategyEvidenceCostSignalDecayInput]] = {}
    for row in input_rows:
        grouped.setdefault(row.candidate_id, []).append(row)

    report_rows = tuple(
        sorted(
            (
                _row_from_inputs(candidate_id, tuple(grouped[candidate_id]), config, generated_at_utc)
                for candidate_id in sorted(grouped)
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _summary_reason_codes(report_rows)
    return ResearchStrategyEvidenceCostSignalDecayReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=_decimal_from_int(len(report_rows)),
        evidence_count=_sum_decimals(
            tuple(row.evidence_count for row in report_rows),
        ),
        pass_count=_status_count(report_rows, STATUS_PASS),
        watch_count=_status_count(report_rows, STATUS_WATCH),
        block_count=_status_count(report_rows, STATUS_BLOCK),
        status=_report_status(report_rows),
        rows=report_rows,
        reason_code_counts=_reason_code_counts(report_rows, reason_codes),
        reason_codes=reason_codes,
        fresh_signal_age_seconds=config.fresh_signal_age_seconds,
        stale_signal_age_seconds=config.stale_signal_age_seconds,
        pass_signal_score_threshold=config.pass_signal_score_threshold,
        watch_signal_score_threshold=config.watch_signal_score_threshold,
        high_cost_watch_threshold=config.high_cost_watch_threshold,
        high_cost_block_threshold=config.high_cost_block_threshold,
        min_evidence_count=config.min_evidence_count,
        min_evidence_channel_count=config.min_evidence_channel_count,
    )


def research_strategy_evidence_cost_signal_decay_report_payload(
    report: ResearchStrategyEvidenceCostSignalDecayReport,
) -> "FrozenJsonObject":
    if type(report) is not ResearchStrategyEvidenceCostSignalDecayReport:
        raise ValueError(
            "report must be ResearchStrategyEvidenceCostSignalDecayReport",
        )
    _require_hard_flags("report", report)
    _require_sha256_digest("derived_validation_digest", report.derived_validation_digest)
    expected_digest = _report_digest_from_public_payload(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match public payload")
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("report payload", payload)
    return _freeze_json_object(payload)


def validate_research_strategy_evidence_cost_signal_decay_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict and type(payload) is not FrozenJsonObject:
        raise ValueError("payload must be a JSON object")
    _validate_public_payload_schema(payload)
    _reject_unsafe_public_payload("public payload", payload)
    digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    if digest != _digest_payload(unsigned_payload):
        raise ValueError("derived_validation_digest must match public payload")
    _report_from_public_payload(payload)
    return True


class FrozenJsonObject(dict[str, Any]):
    def __setitem__(self, key: str, value: Any) -> None:
        raise TypeError("payload is immutable")

    def __delitem__(self, key: str) -> None:
        raise TypeError("payload is immutable")

    def clear(self) -> None:
        raise TypeError("payload is immutable")

    def pop(self, key: str, default: Any = None) -> Any:
        raise TypeError("payload is immutable")

    def popitem(self) -> tuple[str, Any]:
        raise TypeError("payload is immutable")

    def setdefault(self, key: str, default: Any = None) -> Any:
        raise TypeError("payload is immutable")

    def update(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("payload is immutable")

    def __ior__(self, other: object) -> "FrozenJsonObject":
        raise TypeError("payload is immutable")


class FrozenJsonArray(tuple[Any, ...]):
    def __eq__(self, other: object) -> bool:
        if isinstance(other, (list, tuple)):
            return tuple(self) == tuple(other)
        return False

    def append(self, value: Any) -> None:
        raise TypeError("payload is immutable")

    def extend(self, values: Any) -> None:
        raise TypeError("payload is immutable")


def _row_from_inputs(
    candidate_id: str,
    rows: tuple[ResearchStrategyEvidenceCostSignalDecayInput, ...],
    config: ResearchStrategyEvidenceCostSignalDecayConfig,
    generated_at: datetime,
) -> ResearchStrategyEvidenceCostSignalDecayRow:
    sorted_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                row.evidence_channel,
                row.observed_at.isoformat(),
                row.signal_strength,
                row.evidence_cost,
            ),
        ),
    )
    latest_observed_at = max(row.observed_at for row in sorted_rows)
    latest_age = _duration_seconds(latest_observed_at, generated_at)
    decay_scores = tuple(
        _decay_score(
            _duration_seconds(row.observed_at, generated_at),
            fresh_signal_age_seconds=config.fresh_signal_age_seconds,
            stale_signal_age_seconds=config.stale_signal_age_seconds,
        )
        for row in sorted_rows
    )
    average_signal_strength = _average_decimal(
        tuple(row.signal_strength for row in sorted_rows),
    )
    decay_score = _average_decimal(decay_scores)
    decayed_signal_score = _probability_product(average_signal_strength, decay_score)
    total_evidence_cost = _sum_decimals(
        tuple(row.evidence_cost for row in sorted_rows),
    )
    channel_count = _decimal_from_int(
        len({row.evidence_channel for row in sorted_rows}),
    )
    reason_codes = _row_reason_codes(
        evidence_count=_decimal_from_int(len(sorted_rows)),
        evidence_channel_count=channel_count,
        latest_signal_age_seconds=latest_age,
        decayed_signal_score=decayed_signal_score,
        total_evidence_cost=total_evidence_cost,
        config=config,
    )
    return ResearchStrategyEvidenceCostSignalDecayRow(
        signal_hash=_sha256_reference(candidate_id),
        evidence_count=_decimal_from_int(len(sorted_rows)),
        evidence_channel_count=channel_count,
        latest_observed_at=latest_observed_at,
        latest_signal_age_seconds=latest_age,
        average_signal_strength=average_signal_strength,
        decay_score=decay_score,
        decayed_signal_score=decayed_signal_score,
        total_evidence_cost=total_evidence_cost,
        cost_efficiency_score=_cost_efficiency_score(
            decayed_signal_score,
            total_evidence_cost,
            config.high_cost_block_threshold,
        ),
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    evidence_count: Decimal,
    evidence_channel_count: Decimal,
    latest_signal_age_seconds: Decimal,
    decayed_signal_score: Decimal,
    total_evidence_cost: Decimal,
    config: ResearchStrategyEvidenceCostSignalDecayConfig,
) -> tuple[str, ...]:
    details: list[str] = []
    block = False
    if total_evidence_cost >= config.high_cost_block_threshold:
        details.append(HIGH_COST_REASON)
        block = True
    elif total_evidence_cost >= config.high_cost_watch_threshold:
        details.append(HIGH_COST_REASON)
    if (
        evidence_count < config.min_evidence_count
        or evidence_channel_count < config.min_evidence_channel_count
    ):
        details.append(SPARSE_EVIDENCE_REASON)
        block = True
    if latest_signal_age_seconds >= config.stale_signal_age_seconds:
        details.append(STALE_SIGNAL_REASON)
    if decayed_signal_score < config.watch_signal_score_threshold:
        details.append(DECAYED_SIGNAL_REASON)
        block = True
    elif decayed_signal_score < config.pass_signal_score_threshold:
        details.append(WEAK_SIGNAL_REASON)

    if block:
        return (BLOCK_REASON, *tuple(dict.fromkeys(details)))
    if details:
        return (WATCH_REASON, *tuple(dict.fromkeys(details)))
    return (PASS_REASON,)


def _normalize_inputs(
    rows: Iterable[ResearchStrategyEvidenceCostSignalDecayInput],
) -> tuple[ResearchStrategyEvidenceCostSignalDecayInput, ...]:
    if isinstance(rows, (str, bytes, dict)):
        raise ValueError("rows must be an iterable of inputs")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable of inputs") from exc
    for row in normalized:
        if type(row) is not ResearchStrategyEvidenceCostSignalDecayInput:
            raise ValueError(
                "rows must contain ResearchStrategyEvidenceCostSignalDecayInput",
            )
        _require_hard_flags("input", row)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[ResearchStrategyEvidenceCostSignalDecayRow, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    normalized = tuple(rows)
    seen_hashes: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyEvidenceCostSignalDecayRow:
            raise ValueError(
                "rows must contain ResearchStrategyEvidenceCostSignalDecayRow",
            )
        _require_hard_flags("row", row)
        if row.signal_hash in seen_hashes:
            raise ValueError("rows signal_hash values must be unique")
        seen_hashes.add(row.signal_hash)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sorting")
    return normalized


def _normalize_reason_code_counts(
    rows: object,
) -> tuple[ResearchStrategyEvidenceCostSignalDecayReasonCodeCount, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("reason_code_counts must be a tuple or list")
    normalized = tuple(rows)
    seen_reason_codes: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyEvidenceCostSignalDecayReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyEvidenceCostSignalDecayReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", row)
        if row.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen_reason_codes.add(row.reason_code)
    if normalized != tuple(sorted(normalized, key=lambda row: row.reason_code)):
        raise ValueError("reason_code_counts must use deterministic sorting")
    return normalized


def _row_sort_key(
    row: ResearchStrategyEvidenceCostSignalDecayRow,
) -> tuple[int, Decimal, Decimal, str]:
    return (
        STATUS_SORT_RANK[row.status],
        row.total_evidence_cost.copy_negate(),
        row.decayed_signal_score.copy_negate(),
        row.signal_hash,
    )


def _summary_reason_codes(
    rows: tuple[ResearchStrategyEvidenceCostSignalDecayRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (BLOCK_REASON, EMPTY_REASON)
    reason_codes: list[str] = []
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code not in reason_codes:
                reason_codes.append(reason_code)
    return tuple(reason_codes)


def _reason_code_counts(
    rows: tuple[ResearchStrategyEvidenceCostSignalDecayRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchStrategyEvidenceCostSignalDecayReasonCodeCount, ...]:
    counts = Counter(reason_code for row in rows for reason_code in row.reason_codes)
    return tuple(
        ResearchStrategyEvidenceCostSignalDecayReasonCodeCount(
            reason_code=reason_code,
            row_count=_decimal_from_int(counts.get(reason_code, 0)),
        )
        for reason_code in sorted(reason_codes)
    )


def _report_status(
    rows: tuple[ResearchStrategyEvidenceCostSignalDecayRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _status_count(
    rows: tuple[ResearchStrategyEvidenceCostSignalDecayRow, ...],
    status: str,
) -> Decimal:
    return _decimal_from_int(sum(1 for row in rows if row.status == status))


def _validate_row_consistency(row: ResearchStrategyEvidenceCostSignalDecayRow) -> None:
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == STATUS_PASS and row.reason_codes != (PASS_REASON,):
        raise ValueError("pass rows must only use the pass reason")
    if row.status != STATUS_PASS and len(row.reason_codes) == 1:
        raise ValueError("watch and block rows require detail reason_codes")


def _validate_report_consistency(
    report: ResearchStrategyEvidenceCostSignalDecayReport,
) -> None:
    config = _config_from_report(report)
    for row in report.rows:
        _validate_row_against_report(
            row,
            config=config,
            generated_at=report.generated_at,
        )
    if report.candidate_count != _decimal_from_int(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.evidence_count != _sum_decimals(
        tuple(row.evidence_count for row in report.rows),
    ):
        raise ValueError("evidence_count must match rows")
    if report.pass_count != _status_count(report.rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(
        report.rows,
        report.reason_codes,
    ):
        raise ValueError("reason_code_counts must match rows")


def _config_from_report(
    report: ResearchStrategyEvidenceCostSignalDecayReport,
) -> ResearchStrategyEvidenceCostSignalDecayConfig:
    return ResearchStrategyEvidenceCostSignalDecayConfig(
        config_version=report.config_version,
        fresh_signal_age_seconds=report.fresh_signal_age_seconds,
        stale_signal_age_seconds=report.stale_signal_age_seconds,
        pass_signal_score_threshold=report.pass_signal_score_threshold,
        watch_signal_score_threshold=report.watch_signal_score_threshold,
        high_cost_watch_threshold=report.high_cost_watch_threshold,
        high_cost_block_threshold=report.high_cost_block_threshold,
        min_evidence_count=report.min_evidence_count,
        min_evidence_channel_count=report.min_evidence_channel_count,
    )


def _validate_row_against_report(
    row: ResearchStrategyEvidenceCostSignalDecayRow,
    *,
    config: ResearchStrategyEvidenceCostSignalDecayConfig,
    generated_at: datetime,
) -> None:
    if row.evidence_count <= ZERO:
        raise ValueError("row evidence_count must be positive")
    if row.evidence_channel_count <= ZERO:
        raise ValueError("row evidence_channel_count must be positive")
    if row.evidence_channel_count > row.evidence_count:
        raise ValueError("evidence_channel_count must not exceed evidence_count")
    expected_age = _duration_seconds(row.latest_observed_at, generated_at)
    if row.latest_signal_age_seconds != expected_age:
        raise ValueError(
            "latest_signal_age_seconds must match generated_at "
            "and latest_observed_at",
        )
    expected_decayed_signal_score = _probability_product(
        row.average_signal_strength,
        row.decay_score,
    )
    if row.decayed_signal_score != expected_decayed_signal_score:
        raise ValueError("decayed_signal_score must match recomputed value")
    expected_cost_efficiency_score = _cost_efficiency_score(
        row.decayed_signal_score,
        row.total_evidence_cost,
        config.high_cost_block_threshold,
    )
    if row.cost_efficiency_score != expected_cost_efficiency_score:
        raise ValueError("cost_efficiency_score must match recomputed value")
    expected_reason_codes = _row_reason_codes(
        evidence_count=row.evidence_count,
        evidence_channel_count=row.evidence_channel_count,
        latest_signal_age_seconds=row.latest_signal_age_seconds,
        decayed_signal_score=row.decayed_signal_score,
        total_evidence_cost=row.total_evidence_cost,
        config=config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match recomputed value")
    if row.status != _status_from_reason_codes(expected_reason_codes):
        raise ValueError("status must match recomputed value")


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes[0] == BLOCK_REASON:
        return STATUS_BLOCK
    if reason_codes[0] == WATCH_REASON:
        return STATUS_WATCH
    return STATUS_PASS


def _payload_value(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field_name: _payload_value(field_value)
            for field_name, field_value in asdict(value).items()
        }
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if type(value) is Decimal:
        return str(value)
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {
            _payload_value(key): _payload_value(item)
            for key, item in value.items()
        }
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported payload value type: {type(value).__name__}")


def _report_digest_from_public_payload(
    report: ResearchStrategyEvidenceCostSignalDecayReport,
) -> str:
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return _digest_payload(payload)


def _digest_payload(payload: dict[str, Any]) -> str:
    _reject_unsafe_public_payload("digest payload", payload)
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _validate_public_payload_schema(payload: dict[str, Any]) -> None:
    _require_exact_object_schema(
        "public payload",
        payload,
        REPORT_PAYLOAD_SCHEMA,
    )
    rows = payload["rows"]
    if type(rows) not in (list, FrozenJsonArray):
        raise ValueError("public payload rows must use exact canonical schema")
    for row in rows:
        _require_exact_object_schema(
            "public payload row",
            row,
            ROW_PAYLOAD_SCHEMA,
        )
    reason_code_counts = payload["reason_code_counts"]
    if type(reason_code_counts) not in (list, FrozenJsonArray):
        raise ValueError(
            "public payload reason_code_counts must use exact canonical schema",
        )
    for reason_code_count in reason_code_counts:
        _require_exact_object_schema(
            "public payload reason_code_count",
            reason_code_count,
            REASON_CODE_COUNT_PAYLOAD_SCHEMA,
        )
    reason_codes = payload["reason_codes"]
    if type(reason_codes) not in (list, FrozenJsonArray):
        raise ValueError("public payload reason_codes must use exact canonical schema")
    for row in rows:
        row_reason_codes = row["reason_codes"]
        if type(row_reason_codes) not in (list, FrozenJsonArray):
            raise ValueError(
                "public payload row reason_codes must use exact canonical schema",
            )


def _report_from_public_payload(
    payload: dict[str, Any],
) -> ResearchStrategyEvidenceCostSignalDecayReport:
    return ResearchStrategyEvidenceCostSignalDecayReport(
        generated_at=_canonical_datetime_from_payload(
            "generated_at",
            payload["generated_at"],
        ),
        config_version=_string_from_payload(
            "config_version",
            payload["config_version"],
        ),
        candidate_count=_canonical_decimal_from_payload(
            "candidate_count",
            payload["candidate_count"],
        ),
        evidence_count=_canonical_decimal_from_payload(
            "evidence_count",
            payload["evidence_count"],
        ),
        pass_count=_canonical_decimal_from_payload(
            "pass_count",
            payload["pass_count"],
        ),
        watch_count=_canonical_decimal_from_payload(
            "watch_count",
            payload["watch_count"],
        ),
        block_count=_canonical_decimal_from_payload(
            "block_count",
            payload["block_count"],
        ),
        status=_string_from_payload("status", payload["status"]),
        rows=tuple(_row_from_public_payload(row) for row in payload["rows"]),
        reason_code_counts=tuple(
            _reason_code_count_from_public_payload(reason_code_count)
            for reason_code_count in payload["reason_code_counts"]
        ),
        reason_codes=_string_tuple_from_payload(
            "reason_codes",
            payload["reason_codes"],
        ),
        fresh_signal_age_seconds=_canonical_decimal_from_payload(
            "fresh_signal_age_seconds",
            payload["fresh_signal_age_seconds"],
        ),
        stale_signal_age_seconds=_canonical_decimal_from_payload(
            "stale_signal_age_seconds",
            payload["stale_signal_age_seconds"],
        ),
        pass_signal_score_threshold=_canonical_decimal_from_payload(
            "pass_signal_score_threshold",
            payload["pass_signal_score_threshold"],
        ),
        watch_signal_score_threshold=_canonical_decimal_from_payload(
            "watch_signal_score_threshold",
            payload["watch_signal_score_threshold"],
        ),
        high_cost_watch_threshold=_canonical_decimal_from_payload(
            "high_cost_watch_threshold",
            payload["high_cost_watch_threshold"],
        ),
        high_cost_block_threshold=_canonical_decimal_from_payload(
            "high_cost_block_threshold",
            payload["high_cost_block_threshold"],
        ),
        min_evidence_count=_canonical_decimal_from_payload(
            "min_evidence_count",
            payload["min_evidence_count"],
        ),
        min_evidence_channel_count=_canonical_decimal_from_payload(
            "min_evidence_channel_count",
            payload["min_evidence_channel_count"],
        ),
        derived_validation_digest=_string_from_payload(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_true_bool_from_payload("paper_only", payload["paper_only"]),
        report_only=_true_bool_from_payload("report_only", payload["report_only"]),
        readonly=_true_bool_from_payload("readonly", payload["readonly"]),
    )


def _row_from_public_payload(
    payload: dict[str, Any],
) -> ResearchStrategyEvidenceCostSignalDecayRow:
    return ResearchStrategyEvidenceCostSignalDecayRow(
        signal_hash=_string_from_payload("signal_hash", payload["signal_hash"]),
        evidence_count=_canonical_decimal_from_payload(
            "evidence_count",
            payload["evidence_count"],
        ),
        evidence_channel_count=_canonical_decimal_from_payload(
            "evidence_channel_count",
            payload["evidence_channel_count"],
        ),
        latest_observed_at=_canonical_datetime_from_payload(
            "latest_observed_at",
            payload["latest_observed_at"],
        ),
        latest_signal_age_seconds=_canonical_decimal_from_payload(
            "latest_signal_age_seconds",
            payload["latest_signal_age_seconds"],
        ),
        average_signal_strength=_canonical_decimal_from_payload(
            "average_signal_strength",
            payload["average_signal_strength"],
        ),
        decay_score=_canonical_decimal_from_payload(
            "decay_score",
            payload["decay_score"],
        ),
        decayed_signal_score=_canonical_decimal_from_payload(
            "decayed_signal_score",
            payload["decayed_signal_score"],
        ),
        total_evidence_cost=_canonical_decimal_from_payload(
            "total_evidence_cost",
            payload["total_evidence_cost"],
        ),
        cost_efficiency_score=_canonical_decimal_from_payload(
            "cost_efficiency_score",
            payload["cost_efficiency_score"],
        ),
        status=_string_from_payload("status", payload["status"]),
        reason_codes=_string_tuple_from_payload(
            "reason_codes",
            payload["reason_codes"],
        ),
        paper_only=_true_bool_from_payload("paper_only", payload["paper_only"]),
        report_only=_true_bool_from_payload("report_only", payload["report_only"]),
        readonly=_true_bool_from_payload("readonly", payload["readonly"]),
    )


def _reason_code_count_from_public_payload(
    payload: dict[str, Any],
) -> ResearchStrategyEvidenceCostSignalDecayReasonCodeCount:
    return ResearchStrategyEvidenceCostSignalDecayReasonCodeCount(
        reason_code=_string_from_payload(
            "reason_code",
            payload["reason_code"],
        ),
        row_count=_canonical_decimal_from_payload(
            "row_count",
            payload["row_count"],
        ),
        paper_only=_true_bool_from_payload("paper_only", payload["paper_only"]),
        report_only=_true_bool_from_payload("report_only", payload["report_only"]),
        readonly=_true_bool_from_payload("readonly", payload["readonly"]),
    )


def _string_from_payload(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _string_tuple_from_payload(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) not in (list, FrozenJsonArray):
        raise ValueError(f"{field_name} must use exact canonical schema")
    values = tuple(value)
    for item in values:
        if type(item) is not str:
            raise ValueError(f"{field_name} values must be strings")
    return values


def _true_bool_from_payload(field_name: str, value: object) -> bool:
    if type(value) is not bool or value is not True:
        raise ValueError(f"{field_name} must be exactly true")
    return value


def _canonical_decimal_from_payload(
    field_name: str,
    value: object,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical six-place Decimal")
    try:
        raw = Decimal(value)
        normalized = _quantized_decimal(field_name, _raw_decimal(field_name, raw))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(
            f"{field_name} must be a canonical six-place Decimal",
        ) from exc
    if str(normalized) != value:
        raise ValueError(f"{field_name} must be a canonical six-place Decimal")
    return normalized


def _canonical_datetime_from_payload(
    field_name: str,
    value: object,
) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical UTC datetime")
    try:
        parsed = datetime.fromisoformat(value)
        normalized = _as_utc(field_name, parsed)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a canonical UTC datetime") from exc
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical UTC datetime")
    return normalized


def _require_exact_object_schema(
    label: str,
    value: object,
    expected_keys: tuple[str, ...],
) -> None:
    if type(value) not in (dict, FrozenJsonObject):
        raise ValueError(f"{label} must use exact canonical schema")
    if set(value) != set(expected_keys) or len(value) != len(expected_keys):
        raise ValueError(f"{label} must use exact canonical schema")


def _freeze_json_object(value: dict[str, Any]) -> FrozenJsonObject:
    return FrozenJsonObject({key: _freeze_json_value(item) for key, item in value.items()})


def _freeze_json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return _freeze_json_object(value)
    if isinstance(value, list):
        return FrozenJsonArray(_freeze_json_value(item) for item in value)
    return value


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} keys must be strings")
            normalized_key = key.lower()
            if normalized_key in UNSAFE_PUBLIC_KEYS:
                raise ValueError(f"{label} contains unsafe public key: {key}")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        lowered = value.lower()
        if any(part in lowered for part in UNSAFE_PUBLIC_VALUE_PARTS):
            raise ValueError(f"{label} contains unsafe public value")


def _sha256_reference(value: str) -> str:
    return f"sha256:{hashlib.sha256(value.encode('utf-8')).hexdigest()}"


def _require_sha256_reference(field_name: str, value: object) -> None:
    if type(value) is not str or not value.startswith("sha256:"):
        raise ValueError(f"{field_name} must be a sha256 reference")
    _require_sha256_digest(field_name, value.removeprefix("sha256:"))


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    if any(character not in HEX_DIGITS for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _duration_seconds(started_at: datetime, finished_at: datetime) -> Decimal:
    start = _as_utc("started_at", started_at)
    finish = _as_utc("finished_at", finished_at)
    if finish < start:
        raise ValueError("duration seconds must be nonnegative")
    delta = finish - start
    with localcontext(DECIMAL_CONTEXT):
        seconds = (
            Decimal(delta.days) * SECONDS_PER_DAY
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
        )
    return _quantize(seconds)


def _decay_score(
    age_seconds: Decimal,
    *,
    fresh_signal_age_seconds: Decimal,
    stale_signal_age_seconds: Decimal,
) -> Decimal:
    if age_seconds <= fresh_signal_age_seconds:
        return ONE
    if age_seconds >= stale_signal_age_seconds:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        score = (stale_signal_age_seconds - age_seconds) / (
            stale_signal_age_seconds - fresh_signal_age_seconds
        )
    return _quantize(score)


def _cost_efficiency_score(
    decayed_signal_score: Decimal,
    total_evidence_cost: Decimal,
    high_cost_block_threshold: Decimal,
) -> Decimal:
    if high_cost_block_threshold <= ZERO:
        raise ValueError("high_cost_block_threshold must be positive")
    with localcontext(DECIMAL_CONTEXT):
        cost_ratio = _quantize(total_evidence_cost / high_cost_block_threshold)
    if cost_ratio >= ONE:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        score = decayed_signal_score * (ONE - cost_ratio)
    return _clamp_probability(score)


def _probability_product(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        product = left * right
    return _clamp_probability(product)


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        average = _sum_decimals(values) / Decimal(len(values))
    return _quantize(average)


def _decimal_from_int(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        decimal_value = Decimal(value)
    return _quantize(decimal_value)


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return sum(values, ZERO)


def _positive_decimal(field_name: str, value: object) -> Decimal:
    raw = _raw_decimal(field_name, value)
    if raw <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return _quantized_decimal(field_name, raw)


def _nonnegative_decimal(field_name: str, value: object) -> Decimal:
    raw = _raw_decimal(field_name, value)
    if raw < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantized_decimal(field_name, raw)


def _positive_whole_decimal(field_name: str, value: object) -> Decimal:
    raw = _raw_decimal(field_name, value)
    if raw <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    if raw != raw.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return _quantized_decimal(field_name, raw)


def _nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    raw = _raw_decimal(field_name, value)
    if raw < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if raw != raw.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return _quantized_decimal(field_name, raw)


def _probability_decimal(field_name: str, value: object) -> Decimal:
    raw = _raw_decimal(field_name, value)
    if raw < ZERO or raw > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantized_decimal(field_name, raw)


def _decimal(field_name: str, value: object) -> Decimal:
    return _quantized_decimal(field_name, _raw_decimal(field_name, value))


def _raw_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not be signed zero")
    return value


def _quantized_decimal(field_name: str, value: Decimal) -> Decimal:
    try:
        return _quantize(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _clamp_probability(value: Decimal, *, field_name: str = "probability") -> Decimal:
    raw = _raw_decimal(field_name, value)
    if raw < ZERO or raw > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantized_decimal(field_name, raw)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of: pass, watch, block")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if value not in REASON_CODES:
        raise ValueError(f"{field_name} must be a known reason code")


def _normalize_reason_codes(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError(f"{field_name} must be a tuple or list")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    if reason_codes[0] not in STATUS_REASONS:
        raise ValueError(f"{field_name} must begin with a status reason")
    return reason_codes


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        field_value = getattr(value, field_name, None)
        if type(field_value) is not bool:
            raise ValueError(f"{label} {field_name} must be a bool")
        if field_value is not True:
            raise ValueError(f"{label} {field_name} must be True")
