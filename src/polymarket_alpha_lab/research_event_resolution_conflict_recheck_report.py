"""Pure report-only queue for resolution conflict rechecks."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any


__all__ = (
    "ResearchEventResolutionConflictRecheckConfig",
    "ResearchEventResolutionConflictRecheckInput",
    "ResearchEventResolutionConflictRecheckReasonCodeCount",
    "ResearchEventResolutionConflictRecheckReport",
    "ResearchEventResolutionConflictRecheckRow",
    "STATUSES",
    "build_research_event_resolution_conflict_recheck_report",
    "research_event_resolution_conflict_recheck_report_payload",
    "validate_research_event_resolution_conflict_recheck_public_payload",
)


DEFAULT_CONFIG_VERSION = "research-resolution-conflict-recheck-report-v0"
STATUSES = ("pass", "watch", "block")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_QUANT = Decimal("0.000001")
_DEFAULT_WATCH_PRESSURE_THRESHOLD = Decimal("0.350000")
_DEFAULT_BLOCK_PRESSURE_THRESHOLD = Decimal("0.700000")
_CASE_KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_CASE_KEY_UNSAFE_TERMS = (
    "http",
    "url",
    "event",
    "market",
    "condition",
    "slug",
    "source",
    "ref",
    "text",
)
_RAW_ID_KEY_FRAGMENTS = (
    "event" + "_id",
    "market" + "_id",
    "market" + "_slug",
    "condition" + "_id",
    "source" + "_id",
    "source" + "_identifier",
    "source" + "_url",
    "source" + "_text",
    "source" + "_ref",
    "raw_" + "event",
    "raw_" + "market",
    "raw_" + "source",
)
_ACTION_FRAGMENTS = (
    "wal" + "let",
    "au" + "th",
    "or" + "der",
    "tra" + "de",
    "li" + "ve_execution",
    "recomm" + "end",
    "pos" + "ition",
    "siz" + "ing",
    "stake",
)


@dataclass(frozen=True)
class ResearchEventResolutionConflictRecheckConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    fresh_evidence_age_seconds: Decimal = Decimal("3600")
    stale_evidence_age_seconds: Decimal = Decimal("86400")
    oracle_watch_lag_seconds: Decimal = Decimal("1800")
    oracle_block_lag_seconds: Decimal = Decimal("14400")
    watch_recheck_pressure_threshold: Decimal = _DEFAULT_WATCH_PRESSURE_THRESHOLD
    block_recheck_pressure_threshold: Decimal = _DEFAULT_BLOCK_PRESSURE_THRESHOLD
    aggregate_contradiction_weight: Decimal = Decimal("0.300000")
    evidence_age_weight: Decimal = Decimal("0.200000")
    source_reliability_weight: Decimal = Decimal("0.200000")
    deadline_proximity_weight: Decimal = Decimal("0.150000")
    oracle_lag_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionConflictRecheckConfig:
            raise TypeError(
                "ResearchEventResolutionConflictRecheckConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "fresh_evidence_age_seconds",
            "stale_evidence_age_seconds",
            "oracle_watch_lag_seconds",
            "oracle_block_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_evidence_age_seconds <= self.fresh_evidence_age_seconds:
            raise ValueError(
                "stale_evidence_age_seconds must exceed fresh_evidence_age_seconds",
            )
        if self.oracle_block_lag_seconds <= self.oracle_watch_lag_seconds:
            raise ValueError(
                "oracle_block_lag_seconds must exceed oracle_watch_lag_seconds",
            )
        for field_name in (
            "watch_recheck_pressure_threshold",
            "block_recheck_pressure_threshold",
            "aggregate_contradiction_weight",
            "evidence_age_weight",
            "source_reliability_weight",
            "deadline_proximity_weight",
            "oracle_lag_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_recheck_pressure_threshold <= self.watch_recheck_pressure_threshold:
            raise ValueError(
                "block_recheck_pressure_threshold must exceed "
                "watch_recheck_pressure_threshold",
            )
        weight_sum = _quantize(
            self.aggregate_contradiction_weight
            + self.evidence_age_weight
            + self.source_reliability_weight
            + self.deadline_proximity_weight
            + self.oracle_lag_weight,
        )
        if weight_sum != _ONE:
            raise ValueError(
                "aggregate_contradiction_weight, evidence_age_weight, "
                "source_reliability_weight, deadline_proximity_weight, "
                "and oracle_lag_weight must sum to 1",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventResolutionConflictRecheckInput:
    public_case_key: str
    aggregate_contradiction_pressure: Decimal
    evidence_age_seconds: Decimal
    source_reliability_score: Decimal
    deadline_proximity: Decimal
    oracle_lag_seconds: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionConflictRecheckInput:
            raise TypeError(
                "ResearchEventResolutionConflictRecheckInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "public_case_key",
            _require_public_case_key("public_case_key", self.public_case_key),
        )
        object.__setattr__(
            self,
            "aggregate_contradiction_pressure",
            _require_probability_decimal(
                "aggregate_contradiction_pressure",
                self.aggregate_contradiction_pressure,
            ),
        )
        object.__setattr__(
            self,
            "evidence_age_seconds",
            _require_nonnegative_decimal("evidence_age_seconds", self.evidence_age_seconds),
        )
        object.__setattr__(
            self,
            "source_reliability_score",
            _require_probability_decimal(
                "source_reliability_score",
                self.source_reliability_score,
            ),
        )
        object.__setattr__(
            self,
            "deadline_proximity",
            _require_probability_decimal("deadline_proximity", self.deadline_proximity),
        )
        object.__setattr__(
            self,
            "oracle_lag_seconds",
            _require_nonnegative_decimal("oracle_lag_seconds", self.oracle_lag_seconds),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchEventResolutionConflictRecheckRow:
    public_case_key: str
    aggregate_contradiction_pressure: Decimal
    evidence_age_seconds: Decimal
    evidence_age_pressure: Decimal
    source_reliability_score: Decimal
    source_reliability_gap: Decimal
    deadline_proximity: Decimal
    oracle_lag_seconds: Decimal
    oracle_lag_pressure: Decimal
    conflict_recheck_pressure: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionConflictRecheckRow:
            raise TypeError(
                "ResearchEventResolutionConflictRecheckRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "public_case_key",
            _require_public_case_key("public_case_key", self.public_case_key),
        )
        for field_name in (
            "aggregate_contradiction_pressure",
            "evidence_age_pressure",
            "source_reliability_score",
            "source_reliability_gap",
            "deadline_proximity",
            "oracle_lag_pressure",
            "conflict_recheck_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("evidence_age_seconds", "oracle_lag_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
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
class ResearchEventResolutionConflictRecheckReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionConflictRecheckReasonCodeCount:
            raise TypeError(
                "ResearchEventResolutionConflictRecheckReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "reason_code",
            _require_reason_code("reason_code", self.reason_code),
        )
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchEventResolutionConflictRecheckReport:
    generated_at: datetime
    config_version: str
    case_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_conflict_recheck_pressure: Decimal | None
    max_conflict_recheck_pressure: Decimal
    max_evidence_age_seconds: Decimal
    max_oracle_lag_seconds: Decimal
    status: str
    rows: tuple[ResearchEventResolutionConflictRecheckRow, ...]
    reason_code_counts: tuple[ResearchEventResolutionConflictRecheckReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionConflictRecheckReport:
            raise TypeError(
                "ResearchEventResolutionConflictRecheckReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in ("case_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_conflict_recheck_pressure",
            _require_optional_probability_decimal(
                "average_conflict_recheck_pressure",
                self.average_conflict_recheck_pressure,
            ),
        )
        for field_name in (
            "max_conflict_recheck_pressure",
            "max_evidence_age_seconds",
            "max_oracle_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
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


def build_research_event_resolution_conflict_recheck_report(
    conflict_items: Iterable[object],
    *,
    config: ResearchEventResolutionConflictRecheckConfig,
    generated_at: datetime,
) -> ResearchEventResolutionConflictRecheckReport:
    if type(config) is not ResearchEventResolutionConflictRecheckConfig:
        raise ValueError("config must be a ResearchEventResolutionConflictRecheckConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_items = _normalize_conflict_items(conflict_items)
    rows = tuple(
        sorted(
            (_row_from_item(item, config=config) for item in normalized_items),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "case_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_conflict_recheck_pressure": _average_conflict_recheck_pressure(rows),
        "max_conflict_recheck_pressure": max(
            (row.conflict_recheck_pressure for row in rows),
            default=_ZERO,
        ),
        "max_evidence_age_seconds": max(
            (row.evidence_age_seconds for row in rows),
            default=_ZERO,
        ),
        "max_oracle_lag_seconds": max(
            (row.oracle_lag_seconds for row in rows),
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
    return ResearchEventResolutionConflictRecheckReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_event_resolution_conflict_recheck_report_payload(
    report: ResearchEventResolutionConflictRecheckReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEventResolutionConflictRecheckReport:
        raise ValueError(
            "report must be a ResearchEventResolutionConflictRecheckReport",
        )
    _require_hard_flags("report", report)
    _validate_report_consistency(report)
    if report.derived_validation_digest != _report_digest_from_values(
        _report_values_without_digest(report),
    ):
        raise ValueError("derived_validation_digest does not match report payload")
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_research_event_resolution_conflict_recheck_public_payload(payload)
    return payload


def validate_research_event_resolution_conflict_recheck_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_public_payload("public payload", payload)
    _reject_public_numerics(payload)
    _require_payload_flags("public payload", payload)
    digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    expected_digest = _digest_payload(unsigned_payload)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest does not match public payload")
    return True


def _row_from_item(
    item: ResearchEventResolutionConflictRecheckInput,
    *,
    config: ResearchEventResolutionConflictRecheckConfig,
) -> ResearchEventResolutionConflictRecheckRow:
    evidence_age_pressure = _linear_pressure(
        item.evidence_age_seconds,
        zero_at=config.fresh_evidence_age_seconds,
        capped_at=config.stale_evidence_age_seconds,
    )
    source_reliability_gap = _quantize(_ONE - item.source_reliability_score)
    oracle_lag_pressure = _linear_pressure(
        item.oracle_lag_seconds,
        zero_at=_ZERO,
        capped_at=config.oracle_block_lag_seconds,
    )
    conflict_recheck_pressure = _quantize(
        (
            item.aggregate_contradiction_pressure
            * config.aggregate_contradiction_weight
        )
        + (evidence_age_pressure * config.evidence_age_weight)
        + (source_reliability_gap * config.source_reliability_weight)
        + (item.deadline_proximity * config.deadline_proximity_weight)
        + (oracle_lag_pressure * config.oracle_lag_weight),
    )
    status = _row_status(conflict_recheck_pressure, config=config)
    return ResearchEventResolutionConflictRecheckRow(
        public_case_key=item.public_case_key,
        aggregate_contradiction_pressure=item.aggregate_contradiction_pressure,
        evidence_age_seconds=item.evidence_age_seconds,
        evidence_age_pressure=evidence_age_pressure,
        source_reliability_score=item.source_reliability_score,
        source_reliability_gap=source_reliability_gap,
        deadline_proximity=item.deadline_proximity,
        oracle_lag_seconds=item.oracle_lag_seconds,
        oracle_lag_pressure=oracle_lag_pressure,
        conflict_recheck_pressure=conflict_recheck_pressure,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            aggregate_contradiction_pressure=item.aggregate_contradiction_pressure,
            evidence_age_pressure=evidence_age_pressure,
            source_reliability_score=item.source_reliability_score,
            deadline_proximity=item.deadline_proximity,
            oracle_lag_seconds=item.oracle_lag_seconds,
            oracle_lag_pressure=oracle_lag_pressure,
            input_reason_codes=item.reason_codes,
            config=config,
        ),
    )


def _normalize_conflict_items(
    conflict_items: Iterable[object],
) -> tuple[ResearchEventResolutionConflictRecheckInput, ...]:
    if isinstance(conflict_items, (str, bytes)):
        raise ValueError("conflict_items must be an iterable")
    try:
        values = tuple(conflict_items)
    except TypeError as exc:
        raise ValueError("conflict_items must be an iterable") from exc
    normalized = tuple(_coerce_conflict_item(value) for value in values)
    public_case_keys = tuple(item.public_case_key for item in normalized)
    if len(set(public_case_keys)) != len(public_case_keys):
        raise ValueError("duplicate public_case_key")
    return normalized


def _coerce_conflict_item(
    value: object,
) -> ResearchEventResolutionConflictRecheckInput:
    if type(value) is ResearchEventResolutionConflictRecheckInput:
        _require_hard_flags("input", value)
        return value
    _require_hard_flags("input", value)
    return ResearchEventResolutionConflictRecheckInput(
        public_case_key=_field_value(value, "public_case_key"),
        aggregate_contradiction_pressure=_field_value(
            value,
            "aggregate_contradiction_pressure",
        ),
        evidence_age_seconds=_field_value(value, "evidence_age_seconds"),
        source_reliability_score=_field_value(value, "source_reliability_score"),
        deadline_proximity=_field_value(value, "deadline_proximity"),
        oracle_lag_seconds=_field_value(value, "oracle_lag_seconds"),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _field_value(value: object, field_name: str, *, default: object = None) -> object:
    if isinstance(value, Mapping):
        if field_name in value:
            return value[field_name]
        if default is not None:
            return default
        raise ValueError(f"{field_name} is required")
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not None:
        return default
    raise ValueError(f"{field_name} is required")


def _linear_pressure(value: Decimal, *, zero_at: Decimal, capped_at: Decimal) -> Decimal:
    if value <= zero_at:
        return _ZERO
    if value >= capped_at:
        return _ONE
    return _quantize((value - zero_at) / (capped_at - zero_at))


def _row_status(
    conflict_recheck_pressure: Decimal,
    *,
    config: ResearchEventResolutionConflictRecheckConfig,
) -> str:
    if conflict_recheck_pressure >= config.block_recheck_pressure_threshold:
        return "block"
    if conflict_recheck_pressure >= config.watch_recheck_pressure_threshold:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    aggregate_contradiction_pressure: Decimal,
    evidence_age_pressure: Decimal,
    source_reliability_score: Decimal,
    deadline_proximity: Decimal,
    oracle_lag_seconds: Decimal,
    oracle_lag_pressure: Decimal,
    input_reason_codes: tuple[str, ...],
    config: ResearchEventResolutionConflictRecheckConfig,
) -> tuple[str, ...]:
    codes: set[str] = {f"resolution_conflict_recheck_{status}"}
    if aggregate_contradiction_pressure >= Decimal("0.500000"):
        codes.add("aggregate_contradiction_high")
    elif aggregate_contradiction_pressure >= Decimal("0.250000"):
        codes.add("aggregate_contradiction_watch")
    else:
        codes.add("aggregate_contradiction_low")
    if evidence_age_pressure == _ONE:
        codes.add("evidence_age_stale")
    elif evidence_age_pressure > _ZERO:
        codes.add("evidence_age_aging")
    else:
        codes.add("evidence_age_fresh")
    if source_reliability_score < Decimal("0.500000"):
        codes.add("source_reliability_low")
    elif source_reliability_score < Decimal("0.800000"):
        codes.add("source_reliability_mixed")
    else:
        codes.add("source_reliability_strong")
    if deadline_proximity >= Decimal("0.750000"):
        codes.add("deadline_proximity_high")
    elif deadline_proximity >= Decimal("0.350000"):
        codes.add("deadline_proximity_watch")
    if oracle_lag_seconds >= config.oracle_block_lag_seconds:
        codes.add("oracle_lag_block")
    elif oracle_lag_seconds >= config.oracle_watch_lag_seconds or oracle_lag_pressure > _ZERO:
        codes.add("oracle_lag_watch")
    else:
        codes.add("oracle_lag_fresh")
    for reason_code in input_reason_codes:
        codes.add(f"input_{reason_code}")
    return tuple(sorted(codes))


def _report_status(rows: tuple[ResearchEventResolutionConflictRecheckRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchEventResolutionConflictRecheckRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_resolution_conflict_recheck_items",)
    if all(row.status == "pass" for row in rows):
        return ("resolution_conflict_recheck_pass",)
    return tuple(sorted({code for row in rows for code in row.reason_codes}))


def _reason_code_counts(
    rows: tuple[ResearchEventResolutionConflictRecheckRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchEventResolutionConflictRecheckReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchEventResolutionConflictRecheckReasonCodeCount(
                reason_code=reason_codes[0],
                count=_ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchEventResolutionConflictRecheckReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _row_sort_key(
    row: ResearchEventResolutionConflictRecheckRow,
) -> tuple[int, Decimal, str]:
    status_rank = {"block": 0, "watch": 1, "pass": 2}
    return (
        status_rank[row.status],
        -row.conflict_recheck_pressure,
        row.public_case_key,
    )


def _status_count(
    rows: tuple[ResearchEventResolutionConflictRecheckRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _average_conflict_recheck_pressure(
    rows: tuple[ResearchEventResolutionConflictRecheckRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(
        sum((row.conflict_recheck_pressure for row in rows), _ZERO)
        / Decimal(len(rows)),
    )


def _normalize_rows(
    rows: tuple[ResearchEventResolutionConflictRecheckRow, ...],
) -> tuple[ResearchEventResolutionConflictRecheckRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchEventResolutionConflictRecheckRow:
            raise ValueError(
                "rows must contain ResearchEventResolutionConflictRecheckRow values",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by status, pressure, and public_case_key")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchEventResolutionConflictRecheckReasonCodeCount, ...],
) -> tuple[ResearchEventResolutionConflictRecheckReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchEventResolutionConflictRecheckReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchEventResolutionConflictRecheckReasonCodeCount values",
            )
        _require_hard_flags("reason code count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row_consistency(row: ResearchEventResolutionConflictRecheckRow) -> None:
    if row.source_reliability_gap != _quantize(_ONE - row.source_reliability_score):
        raise ValueError("source_reliability_gap must match source_reliability_score")
    if not row.reason_codes:
        raise ValueError("reason_codes must be nonempty")
    if f"resolution_conflict_recheck_{row.status}" not in row.reason_codes:
        raise ValueError("reason_codes must include row status")
    if row.status == "pass" and row.conflict_recheck_pressure >= (
        _DEFAULT_WATCH_PRESSURE_THRESHOLD
    ):
        raise ValueError("conflict_recheck_pressure must match status")
    if row.status == "watch" and (
        row.conflict_recheck_pressure < _DEFAULT_WATCH_PRESSURE_THRESHOLD
        or row.conflict_recheck_pressure >= _DEFAULT_BLOCK_PRESSURE_THRESHOLD
    ):
        raise ValueError("conflict_recheck_pressure must match status")
    if (
        row.status == "block"
        and row.conflict_recheck_pressure < _DEFAULT_BLOCK_PRESSURE_THRESHOLD
    ):
        raise ValueError("conflict_recheck_pressure must match status")


def _validate_report_consistency(
    report: ResearchEventResolutionConflictRecheckReport,
) -> None:
    if report.case_count != _decimal_count(len(report.rows)):
        raise ValueError("case_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_conflict_recheck_pressure != _average_conflict_recheck_pressure(
        report.rows,
    ):
        raise ValueError("average_conflict_recheck_pressure must match rows")
    expected_max_pressure = max(
        (row.conflict_recheck_pressure for row in report.rows),
        default=_ZERO,
    )
    if report.max_conflict_recheck_pressure != expected_max_pressure:
        raise ValueError("max_conflict_recheck_pressure must match rows")
    expected_max_evidence_age = max(
        (row.evidence_age_seconds for row in report.rows),
        default=_ZERO,
    )
    if report.max_evidence_age_seconds != expected_max_evidence_age:
        raise ValueError("max_evidence_age_seconds must match rows")
    expected_max_oracle_lag = max(
        (row.oracle_lag_seconds for row in report.rows),
        default=_ZERO,
    )
    if report.max_oracle_lag_seconds != expected_max_oracle_lag:
        raise ValueError("max_oracle_lag_seconds must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _report_values_without_digest(
    report: ResearchEventResolutionConflictRecheckReport,
) -> dict[str, object]:
    return {
        field.name: getattr(report, field.name)
        for field in fields(report)
        if field.name != "derived_validation_digest"
    }


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    ready = _json_ready(dict(values))
    _reject_public_payload("report digest payload", ready)
    return _digest_payload(ready)


def _digest_payload(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, Decimal):
        raise ValueError("JSON value must use exact Decimal values")
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, datetime):
        raise ValueError("JSON datetime value must be an exact datetime")
    if type(value) is bool:
        return value
    if type(value) is int:
        raise ValueError("JSON numeric value must be Decimal-derived")
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if type(value) is str:
        _reject_text_value("JSON string value", value)
        return value
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_text_value("JSON object key", key)
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_public_payload(label: str, value: object) -> None:
    if type(value) is str:
        _reject_text_value(label, value)
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_text_value(label, key)
            _reject_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_payload(label, item)


def _reject_public_numerics(value: object) -> None:
    if isinstance(value, Decimal) or type(value) in (int, float):
        raise ValueError("public payload numerics must be Decimal strings")
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_public_numerics(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numerics(item)


def _require_payload_flags(label: str, payload: Mapping[str, object]) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if payload.get(flag_name) is not True:
            raise ValueError(f"{flag_name} must be True for {label}")
    for item in payload.values():
        if isinstance(item, Mapping):
            _require_payload_flags(label, item)
        elif isinstance(item, list):
            for child in item:
                if isinstance(child, Mapping):
                    _require_payload_flags(label, child)


def _reject_text_value(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in _RAW_ID_KEY_FRAGMENTS):
        raise ValueError(f"{label} contains raw identifier language")
    if any(fragment in normalized for fragment in _ACTION_FRAGMENTS):
        raise ValueError(f"{label} contains action language")
    if "://" in normalized:
        raise ValueError(f"{label} contains unsafe external reference language")


def _require_public_case_key(field_name: str, value: object) -> str:
    _require_public_string(field_name, value)
    normalized = value.lower()
    if not _CASE_KEY_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public-safe case key")
    if any(term in normalized for term in _CASE_KEY_UNSAFE_TERMS):
        raise ValueError(f"{field_name} must not contain raw identifier language")
    return value


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "" or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_text_value(field_name, value)
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    _require_public_string(field_name, value)
    if not _REASON_CODE_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase reason code")
    return value


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_reason_code(field_name, reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    if not normalized and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(sorted(normalized))


def _require_status(field_name: str, value: object) -> str:
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


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
    return normalized


def _require_optional_probability_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(field_name, value)


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value(rounding=ROUND_HALF_UP):
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_whole_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be an exact Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)
