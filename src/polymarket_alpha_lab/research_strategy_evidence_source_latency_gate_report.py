"""Pure report-only evidence latency gate."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_STRATEGY_EVIDENCE_SOURCE_LATENCY_GATE_REPORT_CONFIG_VERSION = (
    "research-strategy-evidence-source-latency-gate-report-v0"
)

__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_EVIDENCE_SOURCE_LATENCY_GATE_REPORT_CONFIG_VERSION",
    "ResearchStrategyEvidenceSourceLatencyGateConfig",
    "ResearchStrategyEvidenceSourceLatencyGateInput",
    "ResearchStrategyEvidenceSourceLatencyGateReasonCodeCount",
    "ResearchStrategyEvidenceSourceLatencyGateReport",
    "ResearchStrategyEvidenceSourceLatencyGateRow",
    "build_research_strategy_evidence_source_latency_gate_report",
    "research_strategy_evidence_source_latency_gate_digest",
    "research_strategy_evidence_source_latency_gate_digest_payload",
    "research_strategy_evidence_source_latency_gate_report_payload",
)


STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
STATUS_RANK = {
    STATUS_BLOCK: Decimal("0.000000"),
    STATUS_WATCH: Decimal("1.000000"),
    STATUS_PASS: Decimal("2.000000"),
}

MISSING_INPUTS_REASON = "evidence_source_latency_gate_missing_inputs"
PASS_REASON = "evidence_source_latency_gate_pass"
WATCH_REASON = "evidence_source_latency_gate_watch"
BLOCK_REASON = "evidence_source_latency_gate_block"
MISSING_CHECK_REASON = "missing_evidence_check"
LATENCY_BLOCK_REASON = "latency_above_block_threshold"
LATENCY_WATCH_REASON = "latency_above_watch_threshold"
RELIABILITY_BLOCK_REASON = "reliability_below_block_threshold"
RELIABILITY_WATCH_REASON = "reliability_below_watch_threshold"
CONFIRMATION_ZERO_REASON = "confirmation_count_zero"
CONFIRMATION_LOW_REASON = "confirmation_count_below_minimum"

REASON_CODE_SEQUENCE = (
    MISSING_INPUTS_REASON,
    PASS_REASON,
    WATCH_REASON,
    BLOCK_REASON,
    MISSING_CHECK_REASON,
    LATENCY_BLOCK_REASON,
    LATENCY_WATCH_REASON,
    RELIABILITY_BLOCK_REASON,
    RELIABILITY_WATCH_REASON,
    CONFIRMATION_ZERO_REASON,
    CONFIRMATION_LOW_REASON,
)
REASON_CODE_SET = frozenset(REASON_CODE_SEQUENCE)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")

PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
PUBLIC_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
UNSAFE_PUBLIC_FRAGMENTS = (
    "can" "didate",
    "mar" "ket",
    "sl" "ug",
    "ques" "tion",
    "source" "_" "url",
    "source" "-" "url",
    "source" " " "url",
    "source" "_" "text",
    "source" "-" "text",
    "source" " " "text",
    "raw" "_" "url",
    "raw" "-" "url",
    "raw" " " "url",
    "raw" "_" "text",
    "raw" "-" "text",
    "raw" " " "text",
    "d" "sn",
    "ta" "ble",
    "to" "ken",
    "wal" "let",
    "or" "der",
    "tr" "ade",
    "b" "uy",
    "s" "ell",
    "reco" "mmend",
    "siz" "ing",
    "data" "base",
    "net" "work",
    "au" "th",
    "li" "ve",
    "http://",
    "https://",
    "www.",
)

PUBLIC_ROW_FIELDS_WITHOUT_DIGEST = (
    "rank",
    "channel_label",
    "sample_count",
    "checked_count",
    "missing_check_count",
    "average_latency_seconds",
    "max_latency_seconds",
    "min_reliability_score",
    "min_confirmation_count",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
PUBLIC_ROW_FIELDS = (*PUBLIC_ROW_FIELDS_WITHOUT_DIGEST, "public_payload_digest")
PUBLIC_REASON_COUNT_FIELDS = (
    "reason_code",
    "count",
    "paper_only",
    "report_only",
    "readonly",
)
PUBLIC_REPORT_FIELDS_WITHOUT_DIGEST = (
    "generated_at",
    "config_version",
    "status",
    "evidence_count",
    "channel_count",
    "pass_count",
    "watch_count",
    "block_count",
    "missing_check_count",
    "average_latency_seconds",
    "max_latency_seconds",
    "min_reliability_score",
    "rows",
    "reason_code_counts",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
PUBLIC_REPORT_FIELDS = (*PUBLIC_REPORT_FIELDS_WITHOUT_DIGEST, "public_payload_digest")


@dataclass(frozen=True)
class ResearchStrategyEvidenceSourceLatencyGateConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_EVIDENCE_SOURCE_LATENCY_GATE_REPORT_CONFIG_VERSION
    )
    latency_watch_seconds: Decimal = Decimal("900.000000")
    latency_block_seconds: Decimal = Decimal("3600.000000")
    reliability_watch_threshold: Decimal = Decimal("0.500000")
    reliability_block_threshold: Decimal = Decimal("0.250000")
    minimum_confirmation_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyEvidenceSourceLatencyGateConfig:
            raise TypeError(
                "ResearchStrategyEvidenceSourceLatencyGateConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyEvidenceSourceLatencyGateConfig, "config")
        _require_supported_config_version(self.config_version)
        for field_name in ("latency_watch_seconds", "latency_block_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.latency_block_seconds <= self.latency_watch_seconds:
            raise ValueError("latency_block_seconds must exceed latency_watch_seconds")
        for field_name in (
            "reliability_watch_threshold",
            "reliability_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.reliability_watch_threshold <= self.reliability_block_threshold:
            raise ValueError(
                "reliability_watch_threshold must exceed reliability_block_threshold",
            )
        object.__setattr__(
            self,
            "minimum_confirmation_count",
            _require_positive_whole_decimal(
                "minimum_confirmation_count",
                self.minimum_confirmation_count,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyEvidenceSourceLatencyGateInput:
    evidence_ref: str
    channel_label: str
    available_at: datetime
    checked_at: datetime | None
    reliability_score: Decimal
    confirmation_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyEvidenceSourceLatencyGateInput:
            raise TypeError(
                "ResearchStrategyEvidenceSourceLatencyGateInput does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyEvidenceSourceLatencyGateInput, "input")
        _require_private_ref("evidence_ref", self.evidence_ref)
        object.__setattr__(
            self,
            "channel_label",
            _require_public_label("channel_label", self.channel_label),
        )
        object.__setattr__(
            self,
            "available_at",
            _as_utc("available_at", self.available_at),
        )
        object.__setattr__(
            self,
            "checked_at",
            _optional_utc("checked_at", self.checked_at),
        )
        if self.checked_at is not None and self.checked_at < self.available_at:
            raise ValueError("checked_at must not be before available_at")
        object.__setattr__(
            self,
            "reliability_score",
            _require_probability_decimal("reliability_score", self.reliability_score),
        )
        object.__setattr__(
            self,
            "confirmation_count",
            _require_nonnegative_whole_decimal(
                "confirmation_count",
                self.confirmation_count,
            ),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyEvidenceSourceLatencyGateRow:
    rank: Decimal
    channel_label: str
    sample_count: Decimal
    checked_count: Decimal
    missing_check_count: Decimal
    average_latency_seconds: Decimal
    max_latency_seconds: Decimal
    min_reliability_score: Decimal
    min_confirmation_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    public_payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyEvidenceSourceLatencyGateRow:
            raise TypeError(
                "ResearchStrategyEvidenceSourceLatencyGateRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyEvidenceSourceLatencyGateRow, "row")
        for field_name in (
            "rank",
            "sample_count",
            "checked_count",
            "missing_check_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.rank <= ZERO:
            raise ValueError("rank must be positive")
        if self.sample_count <= ZERO:
            raise ValueError("sample_count must be positive")
        object.__setattr__(
            self,
            "channel_label",
            _require_public_label("channel_label", self.channel_label),
        )
        for field_name in ("average_latency_seconds", "max_latency_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_reliability_score",
            _require_probability_decimal(
                "min_reliability_score",
                self.min_reliability_score,
            ),
        )
        object.__setattr__(
            self,
            "min_confirmation_count",
            _require_nonnegative_whole_decimal(
                "min_confirmation_count",
                self.min_confirmation_count,
            ),
        )
        _require_status(self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)
        expected_digest = _public_digest_from_values(_row_values_without_digest(self))
        if self.public_payload_digest:
            _require_digest("public_payload_digest", self.public_payload_digest)
            if self.public_payload_digest != expected_digest:
                raise ValueError("public_payload_digest must match row payload")
        else:
            object.__setattr__(self, "public_payload_digest", expected_digest)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchStrategyEvidenceSourceLatencyGateReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyEvidenceSourceLatencyGateReasonCodeCount:
            raise TypeError(
                "ResearchStrategyEvidenceSourceLatencyGateReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyEvidenceSourceLatencyGateReasonCodeCount,
            "reason_count",
        )
        object.__setattr__(self, "reason_code", _require_reason_code(self.reason_code))
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_count", self)


@dataclass(frozen=True)
class ResearchStrategyEvidenceSourceLatencyGateReport:
    generated_at: datetime
    config_version: str
    status: str
    evidence_count: Decimal
    channel_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    missing_check_count: Decimal
    average_latency_seconds: Decimal
    max_latency_seconds: Decimal
    min_reliability_score: Decimal
    rows: tuple[ResearchStrategyEvidenceSourceLatencyGateRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyEvidenceSourceLatencyGateReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    public_payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyEvidenceSourceLatencyGateReport:
            raise TypeError(
                "ResearchStrategyEvidenceSourceLatencyGateReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyEvidenceSourceLatencyGateReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_supported_config_version(self.config_version)
        _require_status(self.status)
        for field_name in (
            "evidence_count",
            "channel_count",
            "pass_count",
            "watch_count",
            "block_count",
            "missing_check_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_latency_seconds", "max_latency_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_reliability_score",
            _require_probability_decimal(
                "min_reliability_score",
                self.min_reliability_score,
            ),
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
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("report", self)
        expected_digest = _public_digest_from_values(_report_values_without_digest(self))
        if self.public_payload_digest:
            _require_digest("public_payload_digest", self.public_payload_digest)
            if self.public_payload_digest != expected_digest:
                raise ValueError("public_payload_digest must match report payload")
        else:
            object.__setattr__(self, "public_payload_digest", expected_digest)
        _validate_report_consistency(self)


def build_research_strategy_evidence_source_latency_gate_report(
    inputs: Iterable[ResearchStrategyEvidenceSourceLatencyGateInput],
    *,
    generated_at: datetime,
    config: ResearchStrategyEvidenceSourceLatencyGateConfig | None = None,
) -> ResearchStrategyEvidenceSourceLatencyGateReport:
    if config is None:
        config = ResearchStrategyEvidenceSourceLatencyGateConfig()
    _require_exact_type(config, ResearchStrategyEvidenceSourceLatencyGateConfig, "config")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    items = _normalize_inputs(inputs)
    for item in items:
        if item.available_at > generated_at:
            raise ValueError("available_at must not be after generated_at")
        if item.checked_at is not None and item.checked_at > generated_at:
            raise ValueError("checked_at must not be after generated_at")
    rows = _rank_rows(
        tuple(
            _row_from_group(channel_label, group_items, config=config)
            for channel_label, group_items in _group_inputs(items)
        ),
    )
    return ResearchStrategyEvidenceSourceLatencyGateReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=_report_status(rows),
        evidence_count=_count(len(items)),
        channel_count=_count(len(rows)),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        missing_check_count=sum((row.missing_check_count for row in rows), ZERO),
        average_latency_seconds=_checked_weighted_average(rows),
        max_latency_seconds=max((row.max_latency_seconds for row in rows), default=ZERO),
        min_reliability_score=min(
            (row.min_reliability_score for row in rows),
            default=ZERO,
        ),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows),
        reason_codes=_report_reason_codes(rows),
    )


def research_strategy_evidence_source_latency_gate_report_payload(
    report: ResearchStrategyEvidenceSourceLatencyGateReport | dict[str, object],
) -> dict[str, object]:
    if type(report) is ResearchStrategyEvidenceSourceLatencyGateReport:
        _require_hard_flags("report", report)
        if report.public_payload_digest != research_strategy_evidence_source_latency_gate_digest(
            report,
        ):
            raise ValueError("public_payload_digest must match report payload")
        payload = _json_ready(asdict(report))
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _reject_unsafe_public_payload("payload", payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _validate_public_report_payload(report)
        return dict(report)
    raise ValueError("report must be ResearchStrategyEvidenceSourceLatencyGateReport")


def research_strategy_evidence_source_latency_gate_digest_payload(
    report: ResearchStrategyEvidenceSourceLatencyGateReport,
) -> dict[str, object]:
    if type(report) is not ResearchStrategyEvidenceSourceLatencyGateReport:
        raise ValueError("report must be ResearchStrategyEvidenceSourceLatencyGateReport")
    payload = _json_ready(_report_values_without_digest(report))
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    payload["public_payload_digest"] = None
    return payload


def research_strategy_evidence_source_latency_gate_digest(
    report: ResearchStrategyEvidenceSourceLatencyGateReport,
) -> str:
    if type(report) is not ResearchStrategyEvidenceSourceLatencyGateReport:
        raise ValueError("report must be ResearchStrategyEvidenceSourceLatencyGateReport")
    return _public_digest_from_values(_report_values_without_digest(report))


def _row_from_group(
    channel_label: str,
    items: tuple[ResearchStrategyEvidenceSourceLatencyGateInput, ...],
    *,
    config: ResearchStrategyEvidenceSourceLatencyGateConfig,
) -> ResearchStrategyEvidenceSourceLatencyGateRow:
    latencies = tuple(
        _duration_seconds(item.available_at, item.checked_at)
        for item in items
        if item.checked_at is not None
    )
    missing_count = sum(1 for item in items if item.checked_at is None)
    checked_count = len(latencies)
    average_latency = _average(latencies) if latencies else ZERO
    max_latency = max(latencies, default=ZERO)
    min_reliability = min(item.reliability_score for item in items)
    min_confirmation = min(item.confirmation_count for item in items)
    reason_codes = _row_reason_codes(
        missing_check_count=_count(missing_count),
        max_latency_seconds=max_latency,
        min_reliability_score=min_reliability,
        min_confirmation_count=min_confirmation,
        config=config,
    )
    return ResearchStrategyEvidenceSourceLatencyGateRow(
        rank=ONE,
        channel_label=channel_label,
        sample_count=_count(len(items)),
        checked_count=_count(checked_count),
        missing_check_count=_count(missing_count),
        average_latency_seconds=average_latency,
        max_latency_seconds=max_latency,
        min_reliability_score=min_reliability,
        min_confirmation_count=min_confirmation,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    missing_check_count: Decimal,
    max_latency_seconds: Decimal,
    min_reliability_score: Decimal,
    min_confirmation_count: Decimal,
    config: ResearchStrategyEvidenceSourceLatencyGateConfig,
) -> tuple[str, ...]:
    detail_codes: list[str] = []
    if missing_check_count > ZERO:
        detail_codes.append(MISSING_CHECK_REASON)
    if max_latency_seconds >= config.latency_block_seconds:
        detail_codes.append(LATENCY_BLOCK_REASON)
    elif max_latency_seconds >= config.latency_watch_seconds:
        detail_codes.append(LATENCY_WATCH_REASON)
    if min_reliability_score < config.reliability_block_threshold:
        detail_codes.append(RELIABILITY_BLOCK_REASON)
    elif min_reliability_score < config.reliability_watch_threshold:
        detail_codes.append(RELIABILITY_WATCH_REASON)
    if min_confirmation_count == ZERO:
        detail_codes.append(CONFIRMATION_ZERO_REASON)
    elif min_confirmation_count < config.minimum_confirmation_count:
        detail_codes.append(CONFIRMATION_LOW_REASON)
    status = _status_from_detail_codes(tuple(detail_codes))
    return _normalize_reason_codes(
        "reason_codes",
        (f"evidence_source_latency_gate_{status}", *detail_codes),
    )


def _rank_rows(
    rows: tuple[ResearchStrategyEvidenceSourceLatencyGateRow, ...],
) -> tuple[ResearchStrategyEvidenceSourceLatencyGateRow, ...]:
    ranked_rows: list[ResearchStrategyEvidenceSourceLatencyGateRow] = []
    for index, row in enumerate(sorted(rows, key=_row_sort_key), start=1):
        ranked_rows.append(
            ResearchStrategyEvidenceSourceLatencyGateRow(
                rank=_count(index),
                channel_label=row.channel_label,
                sample_count=row.sample_count,
                checked_count=row.checked_count,
                missing_check_count=row.missing_check_count,
                average_latency_seconds=row.average_latency_seconds,
                max_latency_seconds=row.max_latency_seconds,
                min_reliability_score=row.min_reliability_score,
                min_confirmation_count=row.min_confirmation_count,
                status=row.status,
                reason_codes=row.reason_codes,
            ),
        )
    return tuple(ranked_rows)


def _row_sort_key(
    row: ResearchStrategyEvidenceSourceLatencyGateRow,
) -> tuple[Decimal, Decimal, Decimal, str]:
    return (
        STATUS_RANK[row.status],
        -row.missing_check_count,
        -row.max_latency_seconds,
        row.channel_label,
    )


def _group_inputs(
    items: tuple[ResearchStrategyEvidenceSourceLatencyGateInput, ...],
) -> tuple[tuple[str, tuple[ResearchStrategyEvidenceSourceLatencyGateInput, ...]], ...]:
    groups: dict[str, list[ResearchStrategyEvidenceSourceLatencyGateInput]] = {}
    for item in sorted(items, key=lambda value: (value.channel_label, value.evidence_ref)):
        groups.setdefault(item.channel_label, []).append(item)
    return tuple((key, tuple(groups[key])) for key in sorted(groups))


def _normalize_inputs(
    inputs: Iterable[ResearchStrategyEvidenceSourceLatencyGateInput],
) -> tuple[ResearchStrategyEvidenceSourceLatencyGateInput, ...]:
    if isinstance(inputs, (str, bytes, dict)):
        raise ValueError("inputs must be an iterable")
    try:
        items = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_refs: set[str] = set()
    for item in items:
        if type(item) is not ResearchStrategyEvidenceSourceLatencyGateInput:
            raise ValueError(
                "inputs must contain ResearchStrategyEvidenceSourceLatencyGateInput",
            )
        _require_hard_flags("input", item)
        if item.evidence_ref in seen_refs:
            raise ValueError("evidence_ref values must be unique")
        seen_refs.add(item.evidence_ref)
    return items


def _normalize_rows(
    rows: object,
) -> tuple[ResearchStrategyEvidenceSourceLatencyGateRow, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    normalized = tuple(rows)
    seen_channels: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyEvidenceSourceLatencyGateRow:
            raise ValueError("rows must contain ResearchStrategyEvidenceSourceLatencyGateRow")
        _require_hard_flags("row", row)
        if row.channel_label in seen_channels:
            raise ValueError("rows channel_label values must be unique")
        seen_channels.add(row.channel_label)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sorting")
    return normalized


def _normalize_reason_code_counts(
    rows: object,
) -> tuple[ResearchStrategyEvidenceSourceLatencyGateReasonCodeCount, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("reason_code_counts must be a tuple or list")
    normalized = tuple(rows)
    seen_codes: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyEvidenceSourceLatencyGateReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyEvidenceSourceLatencyGateReasonCodeCount",
            )
        _require_hard_flags("reason_count", row)
        if row.reason_code in seen_codes:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen_codes.add(row.reason_code)
    if normalized != tuple(sorted(normalized, key=lambda row: row.reason_code)):
        raise ValueError("reason_code_counts must use deterministic sorting")
    return normalized


def _reason_code_counts(
    rows: tuple[ResearchStrategyEvidenceSourceLatencyGateRow, ...],
) -> tuple[ResearchStrategyEvidenceSourceLatencyGateReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyEvidenceSourceLatencyGateReasonCodeCount(
                reason_code=MISSING_INPUTS_REASON,
                count=ZERO,
            ),
        )
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        ResearchStrategyEvidenceSourceLatencyGateReasonCodeCount(
            reason_code=reason_code,
            count=counts[reason_code],
        )
        for reason_code in sorted(counts)
    )


def _report_reason_codes(
    rows: tuple[ResearchStrategyEvidenceSourceLatencyGateRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (MISSING_INPUTS_REASON,)
    present = {reason_code for row in rows for reason_code in row.reason_codes}
    status_reason = {
        STATUS_PASS: PASS_REASON,
        STATUS_WATCH: WATCH_REASON,
        STATUS_BLOCK: BLOCK_REASON,
    }[_report_status(rows)]
    if status_reason == PASS_REASON:
        return (PASS_REASON,)
    detail_reasons = tuple(
        reason_code
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in present
        and reason_code
        not in (MISSING_INPUTS_REASON, PASS_REASON, WATCH_REASON, BLOCK_REASON)
    )
    return (status_reason, *detail_reasons)


def _report_status(
    rows: tuple[ResearchStrategyEvidenceSourceLatencyGateRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    first_reason = reason_codes[0]
    if first_reason == BLOCK_REASON:
        return STATUS_BLOCK
    if first_reason == WATCH_REASON:
        return STATUS_WATCH
    return STATUS_PASS


def _status_from_detail_codes(reason_codes: tuple[str, ...]) -> str:
    if any(
        reason_code
        in (MISSING_CHECK_REASON, LATENCY_BLOCK_REASON, RELIABILITY_BLOCK_REASON)
        for reason_code in reason_codes
    ):
        return STATUS_BLOCK
    if CONFIRMATION_ZERO_REASON in reason_codes:
        return STATUS_BLOCK
    if reason_codes:
        return STATUS_WATCH
    return STATUS_PASS


def _status_count(
    rows: tuple[ResearchStrategyEvidenceSourceLatencyGateRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _checked_weighted_average(
    rows: tuple[ResearchStrategyEvidenceSourceLatencyGateRow, ...],
) -> Decimal:
    checked_count = sum((row.checked_count for row in rows), ZERO)
    if checked_count == ZERO:
        return ZERO
    weighted_sum = sum(
        (row.average_latency_seconds * row.checked_count for row in rows),
        ZERO,
    )
    return _quantize(weighted_sum / checked_count)


def _validate_row_consistency(row: ResearchStrategyEvidenceSourceLatencyGateRow) -> None:
    if row.checked_count + row.missing_check_count != row.sample_count:
        raise ValueError("checked_count and missing_check_count must match sample_count")
    if row.average_latency_seconds > row.max_latency_seconds and row.checked_count > ZERO:
        raise ValueError("average_latency_seconds must not exceed max_latency_seconds")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(
    report: ResearchStrategyEvidenceSourceLatencyGateReport,
) -> None:
    expected_values = {
        "evidence_count": sum((row.sample_count for row in report.rows), ZERO),
        "channel_count": _count(len(report.rows)),
        "pass_count": _status_count(report.rows, STATUS_PASS),
        "watch_count": _status_count(report.rows, STATUS_WATCH),
        "block_count": _status_count(report.rows, STATUS_BLOCK),
        "missing_check_count": sum(
            (row.missing_check_count for row in report.rows),
            ZERO,
        ),
        "average_latency_seconds": _checked_weighted_average(report.rows),
        "max_latency_seconds": max(
            (row.max_latency_seconds for row in report.rows),
            default=ZERO,
        ),
        "min_reliability_score": min(
            (row.min_reliability_score for row in report.rows),
            default=ZERO,
        ),
    }
    for field_name, expected_value in expected_values.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _row_values_without_digest(
    row: ResearchStrategyEvidenceSourceLatencyGateRow,
) -> dict[str, object]:
    return {
        field.name: getattr(row, field.name)
        for field in fields(row)
        if field.name != "public_payload_digest"
    }


def _report_values_without_digest(
    report: ResearchStrategyEvidenceSourceLatencyGateReport,
) -> dict[str, object]:
    return {
        field.name: getattr(report, field.name)
        for field in fields(report)
        if field.name != "public_payload_digest"
    }


def _public_digest_from_values(value: object) -> str:
    ready = _json_ready(value)
    _reject_unsafe_public_payload("digest payload", ready)
    canonical_payload = json.dumps(
        ready,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical_payload.encode("utf-8")).hexdigest()


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is dict:
        return {str(key): _json_ready(item) for key, item in value.items()}
    if type(value) in (tuple, list):
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        return format(_quantize(value), "f")
    if type(value) is datetime:
        return value.isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("payload contains unsupported value")


def _validate_public_report_payload(payload: dict[str, object]) -> None:
    _require_exact_keys("payload", payload, PUBLIC_REPORT_FIELDS)
    _require_public_payload_flags("payload", payload)
    if type(payload["generated_at"]) is not str:
        raise ValueError("generated_at must be a string")
    if payload["config_version"] != (
        DEFAULT_RESEARCH_STRATEGY_EVIDENCE_SOURCE_LATENCY_GATE_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version must be supported")
    _require_status(payload["status"])
    for field_name in (
        "evidence_count",
        "channel_count",
        "pass_count",
        "watch_count",
        "block_count",
        "missing_check_count",
        "average_latency_seconds",
        "max_latency_seconds",
        "min_reliability_score",
    ):
        _require_decimal_string(payload, field_name)
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain objects")
        _validate_public_row_payload(row)
    reason_code_counts = payload["reason_code_counts"]
    if type(reason_code_counts) is not list:
        raise ValueError("reason_code_counts must be a list")
    for reason_count in reason_code_counts:
        if type(reason_count) is not dict:
            raise ValueError("reason_code_counts must contain objects")
        _validate_public_reason_count_payload(reason_count)
    _validate_public_reason_codes(payload["reason_codes"])
    _require_digest("public_payload_digest", payload["public_payload_digest"])
    expected_digest = _public_digest_from_ready_payload(
        payload,
        PUBLIC_REPORT_FIELDS_WITHOUT_DIGEST,
    )
    if payload["public_payload_digest"] != expected_digest:
        raise ValueError("public_payload_digest must match report payload")


def _validate_public_row_payload(payload: dict[str, object]) -> None:
    _require_exact_keys("row payload", payload, PUBLIC_ROW_FIELDS)
    _require_public_payload_flags("row payload", payload)
    for field_name in (
        "rank",
        "sample_count",
        "checked_count",
        "missing_check_count",
        "average_latency_seconds",
        "max_latency_seconds",
        "min_reliability_score",
        "min_confirmation_count",
    ):
        _require_decimal_string(payload, field_name)
    _require_public_label("channel_label", payload["channel_label"])
    _require_status(payload["status"])
    _validate_public_reason_codes(payload["reason_codes"])
    _require_digest("public_payload_digest", payload["public_payload_digest"])
    expected_digest = _public_digest_from_ready_payload(
        payload,
        PUBLIC_ROW_FIELDS_WITHOUT_DIGEST,
    )
    if payload["public_payload_digest"] != expected_digest:
        raise ValueError("public_payload_digest must match row payload")


def _validate_public_reason_count_payload(payload: dict[str, object]) -> None:
    _require_exact_keys("reason count payload", payload, PUBLIC_REASON_COUNT_FIELDS)
    _require_public_payload_flags("reason count payload", payload)
    _require_reason_code(payload["reason_code"])
    _require_decimal_string(payload, "count")


def _public_digest_from_ready_payload(
    payload: dict[str, object],
    field_names: tuple[str, ...],
) -> str:
    ready = {field_name: payload[field_name] for field_name in field_names}
    _reject_unsafe_public_payload("digest payload", ready)
    canonical_payload = json.dumps(
        ready,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical_payload.encode("utf-8")).hexdigest()


def _require_decimal_string(payload: dict[str, object], field_name: str) -> None:
    value = payload[field_name]
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc


def _validate_public_reason_codes(value: object) -> None:
    if type(value) is not list:
        raise ValueError("reason_codes must be a list")
    _normalize_reason_codes("reason_codes", tuple(value))


def _require_exact_keys(
    label: str,
    payload: dict[str, object],
    field_names: tuple[str, ...],
) -> None:
    if set(payload) != set(field_names):
        raise ValueError(f"{label} fields are not supported")


def _require_public_payload_flags(label: str, payload: dict[str, object]) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if payload.get(field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_public_string(label, str(key))
            _reject_unsafe_public_payload(label, item)
    elif isinstance(value, (tuple, list)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
    elif type(value) is str:
        _reject_unsafe_public_string(label, value)


def _reject_unsafe_public_string(label: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{label} contains unsafe public value")


def _duration_seconds(started_at: datetime, finished_at: datetime) -> Decimal:
    start = _as_utc("started_at", started_at)
    finish = _as_utc("finished_at", finished_at)
    if finish < start:
        raise ValueError("duration seconds must be nonnegative")
    delta = finish - start
    seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    return _quantize(seconds)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(sum(values, ZERO) / _count(len(values)))


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_whole_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return _quantize(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_private_ref(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public label")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_supported_config_version(value: object) -> None:
    if type(value) is not str:
        raise ValueError("config_version must be a string")
    if value != DEFAULT_RESEARCH_STRATEGY_EVIDENCE_SOURCE_LATENCY_GATE_REPORT_CONFIG_VERSION:
        raise ValueError("config_version must be supported")


def _require_status(value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError("status must be pass, watch, or block")


def _require_reason_code(value: object) -> str:
    if type(value) is not str or value not in REASON_CODE_SET:
        raise ValueError("reason_code must be supported")
    return value


def _normalize_reason_codes(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError(f"{field_name} must be a tuple or list")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    seen_codes: set[str] = set()
    for reason_code in reason_codes:
        _require_reason_code(reason_code)
        if reason_code in seen_codes:
            raise ValueError(f"{field_name} must be unique")
        seen_codes.add(reason_code)
    first_reason = reason_codes[0]
    if first_reason not in (PASS_REASON, WATCH_REASON, BLOCK_REASON, MISSING_INPUTS_REASON):
        raise ValueError(f"{field_name} must begin with a status reason")
    if first_reason == PASS_REASON and len(reason_codes) != 1:
        raise ValueError("pass reason_codes must stand alone")
    if first_reason in (WATCH_REASON, BLOCK_REASON) and len(reason_codes) == 1:
        raise ValueError("watch or block reason_codes require detail reasons")
    if first_reason == WATCH_REASON and any(
        reason_code
        in (
            MISSING_CHECK_REASON,
            LATENCY_BLOCK_REASON,
            RELIABILITY_BLOCK_REASON,
            CONFIRMATION_ZERO_REASON,
        )
        for reason_code in reason_codes[1:]
    ):
        raise ValueError("watch reason_codes must not contain block reasons")
    if first_reason == MISSING_INPUTS_REASON and len(reason_codes) != 1:
        raise ValueError("missing input reason_codes must stand alone")
    return reason_codes


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")
