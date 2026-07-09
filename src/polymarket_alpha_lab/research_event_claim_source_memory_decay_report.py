"""Pure report-only event claim source memory decay reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_EVENT_CLAIM_SOURCE_MEMORY_DECAY_REPORT_CONFIG_VERSION = (
    "research-event-claim-source-memory-decay-report-v1"
)

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"
EVENT_CLAIM_SOURCE_MEMORY_DECAY_STATUSES = (
    PASS_STATUS,
    WATCH_STATUS,
    BLOCK_STATUS,
)
STATUS_RANK = {
    BLOCK_STATUS: Decimal("0.000000"),
    WATCH_STATUS: Decimal("1.000000"),
    PASS_STATUS: Decimal("2.000000"),
}

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

NO_INPUTS_REASON = "event_claim_source_memory_decay_no_inputs"

UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "market",
    "question",
    "source_url",
    "source_text",
    "private_claim_ref",
    "private_source_ref",
    "dsn",
    "table",
    "tok" + "en",
    "wal" + "let",
    "or" + "der",
    "trade",
    "trading",
    "live",
    "siz" + "ing",
    "recommend",
    "position",
    "execution",
    "au" + "th",
    "secret",
    "://",
    "?",
    "@",
    "=",
)

__all__ = (
    "EVENT_CLAIM_SOURCE_MEMORY_DECAY_STATUSES",
    "DEFAULT_RESEARCH_EVENT_CLAIM_SOURCE_MEMORY_DECAY_REPORT_CONFIG_VERSION",
    "ResearchEventClaimSourceMemoryDecayConfig",
    "ResearchEventClaimSourceMemoryDecayInput",
    "ResearchEventClaimSourceMemoryDecayReasonCodeCount",
    "ResearchEventClaimSourceMemoryDecayReport",
    "ResearchEventClaimSourceMemoryDecayRow",
    "build_research_event_claim_source_memory_decay_report",
    "research_event_claim_source_memory_decay_report_payload",
    "validate_research_event_claim_source_memory_decay_report_payload",
)


@dataclass(frozen=True)
class ResearchEventClaimSourceMemoryDecayConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_CLAIM_SOURCE_MEMORY_DECAY_REPORT_CONFIG_VERSION
    )
    minimum_pass_source_count: Decimal = Decimal("3.000000")
    minimum_watch_source_count: Decimal = Decimal("2.000000")
    maximum_pass_average_age_hours: Decimal = Decimal("12.000000")
    maximum_watch_average_age_hours: Decimal = Decimal("48.000000")
    minimum_pass_average_quality_score: Decimal = Decimal("0.800000")
    minimum_watch_average_quality_score: Decimal = Decimal("0.500000")
    maximum_pass_conflict_ratio: Decimal = Decimal("0.000000")
    maximum_watch_conflict_ratio: Decimal = Decimal("0.250000")
    minimum_pass_memory_decay_score: Decimal = Decimal("0.750000")
    minimum_watch_memory_decay_score: Decimal = Decimal("0.450000")
    source_count_weight: Decimal = Decimal("0.200000")
    freshness_weight: Decimal = Decimal("0.400000")
    quality_weight: Decimal = Decimal("0.300000")
    conflict_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventClaimSourceMemoryDecayConfig, "config")
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_CLAIM_SOURCE_MEMORY_DECAY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match supported value")
        for field_name in (
            "minimum_pass_source_count",
            "minimum_watch_source_count",
            "maximum_pass_average_age_hours",
            "maximum_watch_average_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "minimum_pass_average_quality_score",
            "minimum_watch_average_quality_score",
            "maximum_pass_conflict_ratio",
            "maximum_watch_conflict_ratio",
            "minimum_pass_memory_decay_score",
            "minimum_watch_memory_decay_score",
            "source_count_weight",
            "freshness_weight",
            "quality_weight",
            "conflict_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.minimum_pass_source_count < self.minimum_watch_source_count:
            raise ValueError("minimum_pass_source_count must be at least watch")
        if self.maximum_pass_average_age_hours > self.maximum_watch_average_age_hours:
            raise ValueError("maximum_pass_average_age_hours must not exceed watch")
        if (
            self.minimum_pass_average_quality_score
            < self.minimum_watch_average_quality_score
        ):
            raise ValueError("minimum_pass_average_quality_score must be at least watch")
        if self.maximum_pass_conflict_ratio > self.maximum_watch_conflict_ratio:
            raise ValueError("maximum_pass_conflict_ratio must not exceed watch")
        if self.minimum_pass_memory_decay_score < self.minimum_watch_memory_decay_score:
            raise ValueError("minimum_pass_memory_decay_score must be at least watch")
        if _weight_sum(self) != ONE:
            raise ValueError("weights must sum to 1.000000")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventClaimSourceMemoryDecayInput:
    private_claim_ref: str
    private_source_ref: str
    observed_at: datetime
    source_quality_score: Decimal
    conflicts_with_claim: bool = False
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventClaimSourceMemoryDecayInput, "input")
        _require_private_ref("private_claim_ref", self.private_claim_ref)
        _require_private_ref("private_source_ref", self.private_source_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "source_quality_score",
            _require_ratio_decimal("source_quality_score", self.source_quality_score),
        )
        if type(self.conflicts_with_claim) is not bool:
            raise ValueError("conflicts_with_claim must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchEventClaimSourceMemoryDecayRow:
    public_claim_ref: str
    source_count: Decimal
    average_source_age_hours: Decimal
    source_count_score: Decimal
    freshness_score: Decimal
    average_source_quality_score: Decimal
    quality_score: Decimal
    conflict_ratio: Decimal
    conflict_score: Decimal
    memory_decay_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventClaimSourceMemoryDecayRow, "row")
        _require_public_label("public_claim_ref", self.public_claim_ref)
        for field_name in ("source_count", "average_source_age_hours"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_count_score",
            "freshness_score",
            "average_source_quality_score",
            "quality_score",
            "conflict_ratio",
            "conflict_score",
            "memory_decay_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchEventClaimSourceMemoryDecayReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventClaimSourceMemoryDecayReasonCodeCount,
            "reason_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        _require_hard_flags("reason_count", self)


@dataclass(frozen=True)
class ResearchEventClaimSourceMemoryDecayReport:
    generated_at: datetime
    config_version: str
    status: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    stale_claim_count: Decimal
    low_quality_claim_count: Decimal
    thin_source_claim_count: Decimal
    conflicted_claim_count: Decimal
    average_memory_decay_score: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchEventClaimSourceMemoryDecayReasonCodeCount, ...]
    rows: tuple[ResearchEventClaimSourceMemoryDecayRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventClaimSourceMemoryDecayReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "stale_claim_count",
            "low_quality_claim_count",
            "thin_source_claim_count",
            "conflicted_claim_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_memory_decay_score",
            _require_ratio_decimal(
                "average_memory_decay_score",
                self.average_memory_decay_score,
            ),
        )
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
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != _report_derived_validation_digest(self):
                raise ValueError(
                    "derived_validation_digest does not match public payload",
                )

    @property
    def public_payload(self) -> dict[str, Any]:
        return research_event_claim_source_memory_decay_report_payload(self)


def build_research_event_claim_source_memory_decay_report(
    inputs: Iterable[ResearchEventClaimSourceMemoryDecayInput],
    *,
    config: ResearchEventClaimSourceMemoryDecayConfig,
    generated_at: datetime,
) -> ResearchEventClaimSourceMemoryDecayReport:
    if type(config) is not ResearchEventClaimSourceMemoryDecayConfig:
        raise ValueError("config must be a ResearchEventClaimSourceMemoryDecayConfig")
    generated_at = _as_utc("generated_at", generated_at)
    _require_hard_flags("config", config)
    normalized = _normalize_inputs(inputs)
    for value in normalized:
        if value.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")

    grouped: dict[str, list[ResearchEventClaimSourceMemoryDecayInput]] = {}
    seen_claim_sources: set[tuple[str, str]] = set()
    for value in sorted(
        normalized,
        key=lambda item: (_private_digest(item.private_claim_ref), _private_digest(item.private_source_ref)),
    ):
        key = (value.private_claim_ref, value.private_source_ref)
        if key in seen_claim_sources:
            raise ValueError("private_source_ref values must be unique per claim")
        seen_claim_sources.add(key)
        grouped.setdefault(value.private_claim_ref, []).append(value)

    rows = tuple(
        sorted(
            (
                _row_from_inputs(
                    claim_items,
                    config=config,
                    generated_at=generated_at,
                    public_claim_ref=_public_claim_ref(index),
                )
                for index, claim_items in enumerate(
                    (
                        grouped[key]
                        for key in sorted(grouped, key=_private_digest)
                    ),
                    start=1,
                )
            ),
            key=_row_sort_key,
        ),
    )
    return ResearchEventClaimSourceMemoryDecayReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=_report_status(rows),
        input_count=_count_decimal(len(normalized)),
        row_count=_count_decimal(len(rows)),
        pass_count=_status_count(rows, PASS_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        block_count=_status_count(rows, BLOCK_STATUS),
        stale_claim_count=_non_pass_reason_count(
            rows,
            "event_claim_source_memory_decay_freshness",
        ),
        low_quality_claim_count=_non_pass_reason_count(
            rows,
            "event_claim_source_memory_decay_quality",
        ),
        thin_source_claim_count=_non_pass_reason_count(
            rows,
            "event_claim_source_memory_decay_source_count",
        ),
        conflicted_claim_count=_non_pass_reason_count(
            rows,
            "event_claim_source_memory_decay_conflict",
        ),
        average_memory_decay_score=_average_row_decimal(rows, "memory_decay_score"),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_report_reason_code_counts(rows),
        rows=rows,
    )


def research_event_claim_source_memory_decay_report_payload(
    report: ResearchEventClaimSourceMemoryDecayReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEventClaimSourceMemoryDecayReport:
        raise ValueError("report must be a ResearchEventClaimSourceMemoryDecayReport")
    _require_hard_flags("report", report)
    _reject_unsafe_public_payload("report", report)
    payload = _json_value(report)
    if type(payload) is not dict:
        raise ValueError("report must serialize to a JSON object")
    validate_research_event_claim_source_memory_decay_report_payload(payload)
    return payload


def validate_research_event_claim_source_memory_decay_report_payload(
    payload: dict[str, Any],
) -> dict[str, Any]:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _require_payload_hard_flags(payload)
    _reject_unsafe_public_payload("payload", payload)
    provided_digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", provided_digest)
    if provided_digest != _payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest does not match public payload")
    return payload


def _row_from_inputs(
    values: list[ResearchEventClaimSourceMemoryDecayInput],
    *,
    config: ResearchEventClaimSourceMemoryDecayConfig,
    generated_at: datetime,
    public_claim_ref: str,
) -> ResearchEventClaimSourceMemoryDecayRow:
    source_count = _count_decimal(len(values))
    age_values = tuple(_hours_between(value.observed_at, generated_at) for value in values)
    average_source_age_hours = _average_decimal(age_values)
    average_source_quality_score = _average_decimal(
        tuple(value.source_quality_score for value in values),
    )
    conflict_count = _count_decimal(
        sum(1 for value in values if value.conflicts_with_claim),
    )
    with localcontext(DECIMAL_CONTEXT):
        conflict_ratio = _quantize_decimal(conflict_count / source_count)

    freshness_score = _score_for_maximum(
        average_source_age_hours,
        config.maximum_pass_average_age_hours,
        config.maximum_watch_average_age_hours,
    )
    quality_score = _score_for_minimum(
        average_source_quality_score,
        config.minimum_pass_average_quality_score,
        config.minimum_watch_average_quality_score,
    )
    conflict_score = _score_for_maximum(
        conflict_ratio,
        config.maximum_pass_conflict_ratio,
        config.maximum_watch_conflict_ratio,
    )
    source_count_score = _source_count_score(
        source_count,
        config=config,
        freshness_score=freshness_score,
        quality_score=quality_score,
        conflict_score=conflict_score,
    )
    with localcontext(DECIMAL_CONTEXT):
        memory_decay_score = _quantize_decimal(
            source_count_score * config.source_count_weight
            + freshness_score * config.freshness_weight
            + quality_score * config.quality_weight
            + conflict_score * config.conflict_weight,
        )
    status = _status_from_score(memory_decay_score, config)
    reason_codes = tuple(
        sorted(
            _input_reason_codes(values)
            + (
                _reason_for_metric(
                    "event_claim_source_memory_decay_source_count",
                    source_count_score,
                ),
                _reason_for_metric(
                    "event_claim_source_memory_decay_freshness",
                    freshness_score,
                ),
                _reason_for_metric(
                    "event_claim_source_memory_decay_quality",
                    quality_score,
                ),
                _reason_for_metric(
                    "event_claim_source_memory_decay_conflict",
                    conflict_score,
                ),
                f"event_claim_source_memory_decay_status_{status}",
            ),
        ),
    )
    return ResearchEventClaimSourceMemoryDecayRow(
        public_claim_ref=public_claim_ref,
        source_count=source_count,
        average_source_age_hours=average_source_age_hours,
        source_count_score=source_count_score,
        freshness_score=freshness_score,
        average_source_quality_score=average_source_quality_score,
        quality_score=quality_score,
        conflict_ratio=conflict_ratio,
        conflict_score=conflict_score,
        memory_decay_score=memory_decay_score,
        status=status,
        reason_codes=reason_codes,
    )


def _score_for_minimum(value: Decimal, pass_value: Decimal, watch_value: Decimal) -> Decimal:
    if value >= pass_value:
        return ONE
    if value >= watch_value:
        return Decimal("0.500000")
    return ZERO


def _score_for_maximum(value: Decimal, pass_value: Decimal, watch_value: Decimal) -> Decimal:
    if value <= pass_value:
        return ONE
    if value <= watch_value:
        return Decimal("0.500000")
    return ZERO


def _source_count_score(
    value: Decimal,
    *,
    config: ResearchEventClaimSourceMemoryDecayConfig,
    freshness_score: Decimal,
    quality_score: Decimal,
    conflict_score: Decimal,
) -> Decimal:
    if value >= config.minimum_pass_source_count:
        return ONE
    if (
        freshness_score == ONE
        and quality_score == ONE
        and conflict_score == ONE
    ):
        return ONE
    if value >= config.minimum_watch_source_count:
        return Decimal("0.500000")
    return ZERO


def _status_from_score(
    value: Decimal,
    config: ResearchEventClaimSourceMemoryDecayConfig,
) -> str:
    if value == ONE:
        return PASS_STATUS
    if value >= config.minimum_watch_memory_decay_score:
        return WATCH_STATUS
    return BLOCK_STATUS


def _reason_for_metric(prefix: str, score: Decimal) -> str:
    if score == ONE:
        suffix = PASS_STATUS
    elif score == ZERO:
        suffix = BLOCK_STATUS
    else:
        suffix = WATCH_STATUS
    return f"{prefix}_{suffix}"


def _input_reason_codes(
    values: list[ResearchEventClaimSourceMemoryDecayInput],
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                f"input_{reason_code}"
                for value in values
                for reason_code in value.reason_codes
            },
        ),
    )


def _normalize_inputs(
    inputs: Iterable[ResearchEventClaimSourceMemoryDecayInput],
) -> tuple[ResearchEventClaimSourceMemoryDecayInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable of input rows")
    normalized = tuple(inputs)
    for value in normalized:
        if type(value) is not ResearchEventClaimSourceMemoryDecayInput:
            raise ValueError("inputs must contain ResearchEventClaimSourceMemoryDecayInput")
        _require_hard_flags("input", value)
    return normalized


def _normalize_rows(
    rows: tuple[ResearchEventClaimSourceMemoryDecayRow, ...],
) -> tuple[ResearchEventClaimSourceMemoryDecayRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchEventClaimSourceMemoryDecayRow:
            raise ValueError("rows must contain ResearchEventClaimSourceMemoryDecayRow")
    return tuple(sorted(rows, key=_row_sort_key))


def _normalize_reason_code_counts(
    reason_code_counts: tuple[ResearchEventClaimSourceMemoryDecayReasonCodeCount, ...],
) -> tuple[ResearchEventClaimSourceMemoryDecayReasonCodeCount, ...]:
    if type(reason_code_counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for value in reason_code_counts:
        if type(value) is not ResearchEventClaimSourceMemoryDecayReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchEventClaimSourceMemoryDecayReasonCodeCount",
            )
    return tuple(sorted(reason_code_counts, key=lambda item: item.reason_code))


def _normalize_reason_codes(
    field_name: str,
    value: tuple[str, ...],
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized = tuple(_require_reason_code(field_name, item) for item in value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    return tuple(sorted(normalized))


def _require_reason_code(field_name: str, value: str) -> str:
    value = _require_public_label(field_name, value)
    if any(fragment in value for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public payload")
    return value


def _report_status(rows: tuple[ResearchEventClaimSourceMemoryDecayRow, ...]) -> str:
    if not rows:
        return WATCH_STATUS
    if any(row.status == BLOCK_STATUS for row in rows):
        return BLOCK_STATUS
    if any(row.status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _status_count(
    rows: tuple[ResearchEventClaimSourceMemoryDecayRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _non_pass_reason_count(
    rows: tuple[ResearchEventClaimSourceMemoryDecayRow, ...],
    prefix: str,
) -> Decimal:
    return _count_decimal(
        sum(
            1
            for row in rows
            if f"{prefix}_{WATCH_STATUS}" in row.reason_codes
            or f"{prefix}_{BLOCK_STATUS}" in row.reason_codes
        ),
    )


def _report_reason_codes(
    rows: tuple[ResearchEventClaimSourceMemoryDecayRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    return tuple(sorted({reason_code for row in rows for reason_code in row.reason_codes}))


def _report_reason_code_counts(
    rows: tuple[ResearchEventClaimSourceMemoryDecayRow, ...],
) -> tuple[ResearchEventClaimSourceMemoryDecayReasonCodeCount, ...]:
    counter: Counter[str] = Counter(
        reason_code for row in rows for reason_code in row.reason_codes
    )
    if not counter:
        counter[NO_INPUTS_REASON] = 1
    return tuple(
        ResearchEventClaimSourceMemoryDecayReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(count),
        )
        for reason_code, count in sorted(counter.items())
    )


def _row_sort_key(row: ResearchEventClaimSourceMemoryDecayRow) -> tuple[Decimal, Decimal, str]:
    return (
        STATUS_RANK[row.status],
        row.memory_decay_score,
        row.public_claim_ref,
    )


def _hours_between(observed_at: datetime, generated_at: datetime) -> Decimal:
    seconds = Decimal(str((generated_at - observed_at).total_seconds()))
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(seconds / Decimal("3600"))


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(sum(values, ZERO) / _count_decimal(len(values)))


def _average_row_decimal(
    rows: tuple[ResearchEventClaimSourceMemoryDecayRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(
            sum((getattr(row, field_name) for row in rows), ZERO)
            / _count_decimal(len(rows)),
        )


def _validate_row_consistency(row: ResearchEventClaimSourceMemoryDecayRow) -> None:
    if f"event_claim_source_memory_decay_status_{row.status}" not in row.reason_codes:
        raise ValueError("status must match reason_codes")
    if row.status == PASS_STATUS and row.memory_decay_score != ONE:
        raise ValueError("memory_decay_score must match pass status")


def _validate_report_consistency(report: ResearchEventClaimSourceMemoryDecayReport) -> None:
    rows = report.rows
    expected_pairs = {
        "status": _report_status(rows),
        "row_count": _count_decimal(len(rows)),
        "pass_count": _status_count(rows, PASS_STATUS),
        "watch_count": _status_count(rows, WATCH_STATUS),
        "block_count": _status_count(rows, BLOCK_STATUS),
        "stale_claim_count": _non_pass_reason_count(
            rows,
            "event_claim_source_memory_decay_freshness",
        ),
        "low_quality_claim_count": _non_pass_reason_count(
            rows,
            "event_claim_source_memory_decay_quality",
        ),
        "thin_source_claim_count": _non_pass_reason_count(
            rows,
            "event_claim_source_memory_decay_source_count",
        ),
        "conflicted_claim_count": _non_pass_reason_count(
            rows,
            "event_claim_source_memory_decay_conflict",
        ),
        "average_memory_decay_score": _average_row_decimal(rows, "memory_decay_score"),
        "reason_codes": _report_reason_codes(rows),
        "reason_code_counts": _report_reason_code_counts(rows),
    }
    for field_name, expected_value in expected_pairs.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    if report.input_count < report.row_count:
        raise ValueError("input_count must be at least row_count")


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _weight_sum(config: ResearchEventClaimSourceMemoryDecayConfig) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(
            config.source_count_weight
            + config.freshness_weight
            + config.quality_weight
            + config.conflict_weight,
        )


def _public_claim_ref(index: int) -> str:
    return f"public-claim-{index:06d}"


def _private_digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _report_derived_validation_digest(
    report: ResearchEventClaimSourceMemoryDecayReport,
) -> str:
    payload = _json_value(report, include_digest=False)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(
        digest_payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_value(value: Any, *, include_digest: bool = True) -> Any:
    if isinstance(value, Decimal):
        return str(_quantize_decimal(value))
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if is_dataclass(value):
        return {
            field.name: _json_value(
                getattr(value, field.name),
                include_digest=include_digest,
            )
            for field in fields(value)
            if include_digest or field.name != "derived_validation_digest"
        }
    if isinstance(value, tuple):
        return [_json_value(item, include_digest=include_digest) for item in value]
    if isinstance(value, list):
        return [_json_value(item, include_digest=include_digest) for item in value]
    if isinstance(value, (str, bool)) or value is None:
        return value
    raise ValueError(f"unsupported public payload value: {type(value).__name__}")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_private_ref(field_name: str, value: str) -> None:
    if type(value) is not str or value == "":
        raise ValueError(f"{field_name} must be a non-empty string")


def _require_public_label(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "" or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789-_")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must contain only public label characters")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be non-negative")
    return value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return value


def _quantize_decimal(value: Decimal) -> Decimal:
    try:
        return value.quantize(QUANTUM)
    except InvalidOperation as exc:
        raise ValueError("decimal value must fit configured precision") from exc


def _require_status(field_name: str, value: str) -> None:
    if value not in EVENT_CLAIM_SOURCE_MEMORY_DECAY_STATUSES:
        raise ValueError(f"{field_name} must be one of pass/watch/block")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_payload_hard_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value):
        _reject_unsafe_public_payload(label, _json_value(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_public_text(label, str(key))
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (tuple, list)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, str):
        _reject_unsafe_public_text(label, value)
        return
    if isinstance(value, (Decimal, datetime, bool)) or value is None:
        return
    raise ValueError(f"{label} contains unsafe public payload")


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{label} contains unsafe public payload")
