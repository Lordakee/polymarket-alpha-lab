"""Pure report-only summary for public resolution evidence refresh SLA risk."""

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
    "ResearchResolutionEvidenceRefreshSlaConfig",
    "ResearchResolutionEvidenceRefreshSlaInput",
    "ResearchResolutionEvidenceRefreshSlaReasonCodeCount",
    "ResearchResolutionEvidenceRefreshSlaReport",
    "ResearchResolutionEvidenceRefreshSlaRow",
    "build_research_resolution_evidence_refresh_sla_report",
    "research_resolution_evidence_refresh_sla_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-resolution-evidence-refresh-sla-v0"
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_QUANT = Decimal("0.000001")
_STATUSES = ("pass", "watch", "block")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_BUCKET_ID_UNSAFE_TERMS = (
    "http",
    "url",
    "market",
    "condition",
    "slug",
    "source",
    "ref",
    "text",
)
_PAYLOAD_UNSAFE_FRAGMENTS = (
    "http://",
    "https://",
    "source_url",
    "source_text",
    "source_ref",
    "source_reference",
    "raw_url",
    "raw_text",
    "raw_ref",
    "market_slug",
    "market_id",
    "market_identifier",
    "condition_id",
)
_ACTION_TERMS = (
    "wal" + "let",
    "au" + "th",
    "or" + "der",
    "tra" + "de",
    "li" + "ve",
    "recomm" + "endation",
    "siz" + "ing",
)


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class ResearchResolutionEvidenceRefreshSlaConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    watch_aggregate_evidence_age_hours: Decimal = Decimal("12.000000")
    block_aggregate_evidence_age_hours: Decimal = Decimal("48.000000")
    watch_deadline_proximity_hours: Decimal = Decimal("24.000000")
    block_deadline_proximity_hours: Decimal = Decimal("2.000000")
    watch_oracle_lag_hours: Decimal = Decimal("6.000000")
    block_oracle_lag_hours: Decimal = Decimal("48.000000")
    watch_risk_threshold: Decimal = Decimal("0.350000")
    block_risk_threshold: Decimal = Decimal("0.700000")
    aggregate_evidence_age_weight: Decimal = Decimal("0.250000")
    deadline_proximity_weight: Decimal = Decimal("0.200000")
    oracle_lag_weight: Decimal = Decimal("0.200000")
    source_reliability_weight: Decimal = Decimal("0.200000")
    contradiction_pressure_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchResolutionEvidenceRefreshSlaConfig:
            raise TypeError(
                "ResearchResolutionEvidenceRefreshSlaConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchResolutionEvidenceRefreshSlaConfig, "config")
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_aggregate_evidence_age_hours",
            "block_aggregate_evidence_age_hours",
            "watch_deadline_proximity_hours",
            "block_deadline_proximity_hours",
            "watch_oracle_lag_hours",
            "block_oracle_lag_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.block_aggregate_evidence_age_hours
            <= self.watch_aggregate_evidence_age_hours
        ):
            raise ValueError(
                "block_aggregate_evidence_age_hours must exceed "
                "watch_aggregate_evidence_age_hours",
            )
        if self.watch_deadline_proximity_hours <= self.block_deadline_proximity_hours:
            raise ValueError(
                "watch_deadline_proximity_hours must exceed "
                "block_deadline_proximity_hours",
            )
        if self.block_oracle_lag_hours <= self.watch_oracle_lag_hours:
            raise ValueError("block_oracle_lag_hours must exceed watch_oracle_lag_hours")
        for field_name in (
            "watch_risk_threshold",
            "block_risk_threshold",
            "aggregate_evidence_age_weight",
            "deadline_proximity_weight",
            "oracle_lag_weight",
            "source_reliability_weight",
            "contradiction_pressure_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_risk_threshold <= self.watch_risk_threshold:
            raise ValueError("block_risk_threshold must exceed watch_risk_threshold")
        weight_sum = _quantize(
            self.aggregate_evidence_age_weight
            + self.deadline_proximity_weight
            + self.oracle_lag_weight
            + self.source_reliability_weight
            + self.contradiction_pressure_weight,
        )
        if weight_sum != _ONE:
            raise ValueError(
                "aggregate_evidence_age_weight, deadline_proximity_weight, "
                "oracle_lag_weight, source_reliability_weight, and "
                "contradiction_pressure_weight must sum to 1",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchResolutionEvidenceRefreshSlaInput:
    public_bucket_id: str
    aggregate_evidence_age_hours: Decimal
    hours_until_resolution_deadline: Decimal
    oracle_lag_hours: Decimal
    aggregate_source_reliability: Decimal
    contradiction_pressure: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchResolutionEvidenceRefreshSlaInput:
            raise TypeError(
                "ResearchResolutionEvidenceRefreshSlaInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchResolutionEvidenceRefreshSlaInput,
            "refresh SLA input",
        )
        _require_public_bucket_id("public_bucket_id", self.public_bucket_id)
        for field_name in (
            "aggregate_evidence_age_hours",
            "hours_until_resolution_deadline",
            "oracle_lag_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("aggregate_source_reliability", "contradiction_pressure"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("refresh SLA input", self)


@dataclass(frozen=True)
class ResearchResolutionEvidenceRefreshSlaRow:
    public_bucket_id: str
    aggregate_evidence_age_hours: Decimal
    aggregate_evidence_age_pressure: Decimal
    hours_until_resolution_deadline: Decimal
    deadline_proximity_pressure: Decimal
    oracle_lag_hours: Decimal
    oracle_lag_pressure: Decimal
    aggregate_source_reliability: Decimal
    source_reliability_gap: Decimal
    contradiction_pressure: Decimal
    refresh_sla_risk_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchResolutionEvidenceRefreshSlaRow:
            raise TypeError(
                "ResearchResolutionEvidenceRefreshSlaRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchResolutionEvidenceRefreshSlaRow, "row")
        _require_public_bucket_id("public_bucket_id", self.public_bucket_id)
        for field_name in (
            "aggregate_evidence_age_hours",
            "hours_until_resolution_deadline",
            "oracle_lag_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "aggregate_evidence_age_pressure",
            "deadline_proximity_pressure",
            "oracle_lag_pressure",
            "aggregate_source_reliability",
            "source_reliability_gap",
            "contradiction_pressure",
            "refresh_sla_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
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
class ResearchResolutionEvidenceRefreshSlaReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchResolutionEvidenceRefreshSlaReasonCodeCount:
            raise TypeError(
                "ResearchResolutionEvidenceRefreshSlaReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchResolutionEvidenceRefreshSlaReasonCodeCount,
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
class ResearchResolutionEvidenceRefreshSlaReport:
    generated_at: datetime
    config_version: str
    bucket_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_refresh_sla_risk_score: Decimal | None
    average_aggregate_evidence_age_hours: Decimal | None
    max_aggregate_evidence_age_hours: Decimal
    min_hours_until_resolution_deadline: Decimal | None
    max_oracle_lag_hours: Decimal
    status: str
    rows: tuple[ResearchResolutionEvidenceRefreshSlaRow, ...]
    reason_code_counts: tuple[
        ResearchResolutionEvidenceRefreshSlaReasonCodeCount,
        ...
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchResolutionEvidenceRefreshSlaReport:
            raise TypeError(
                "ResearchResolutionEvidenceRefreshSlaReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchResolutionEvidenceRefreshSlaReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in ("bucket_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_refresh_sla_risk_score",
            _require_optional_probability_decimal(
                "average_refresh_sla_risk_score",
                self.average_refresh_sla_risk_score,
            ),
        )
        object.__setattr__(
            self,
            "average_aggregate_evidence_age_hours",
            _require_optional_nonnegative_decimal(
                "average_aggregate_evidence_age_hours",
                self.average_aggregate_evidence_age_hours,
            ),
        )
        for field_name in (
            "max_aggregate_evidence_age_hours",
            "max_oracle_lag_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_hours_until_resolution_deadline",
            _require_optional_nonnegative_decimal(
                "min_hours_until_resolution_deadline",
                self.min_hours_until_resolution_deadline,
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


def build_research_resolution_evidence_refresh_sla_report(
    refresh_items: Iterable[object],
    *,
    config: ResearchResolutionEvidenceRefreshSlaConfig,
    generated_at: datetime,
) -> ResearchResolutionEvidenceRefreshSlaReport:
    if type(config) is not ResearchResolutionEvidenceRefreshSlaConfig:
        raise ValueError("config must be a ResearchResolutionEvidenceRefreshSlaConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_items = _normalize_refresh_items(refresh_items)
    rows = tuple(
        _row_from_item(item, config=config)
        for item in sorted(normalized_items, key=lambda value: value.public_bucket_id)
    )
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "bucket_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_refresh_sla_risk_score": _average_refresh_sla_risk_score(rows),
        "average_aggregate_evidence_age_hours": _average_aggregate_evidence_age_hours(
            rows,
        ),
        "max_aggregate_evidence_age_hours": max(
            (row.aggregate_evidence_age_hours for row in rows),
            default=_ZERO,
        ),
        "min_hours_until_resolution_deadline": _min_hours_until_resolution_deadline(rows),
        "max_oracle_lag_hours": max((row.oracle_lag_hours for row in rows), default=_ZERO),
        "status": _report_status(rows),
        "rows": rows,
        "reason_code_counts": _reason_code_counts(rows, reason_codes),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchResolutionEvidenceRefreshSlaReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_resolution_evidence_refresh_sla_report_payload(
    report: ResearchResolutionEvidenceRefreshSlaReport,
) -> dict[str, Any]:
    if type(report) is not ResearchResolutionEvidenceRefreshSlaReport:
        raise ValueError("report must be a ResearchResolutionEvidenceRefreshSlaReport")
    _require_hard_flags("report", report)
    payload = _json_ready(asdict(report))
    _reject_public_payload("report payload", payload)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _row_from_item(
    item: ResearchResolutionEvidenceRefreshSlaInput,
    *,
    config: ResearchResolutionEvidenceRefreshSlaConfig,
) -> ResearchResolutionEvidenceRefreshSlaRow:
    age_pressure = _upper_pressure(
        item.aggregate_evidence_age_hours,
        watch=config.watch_aggregate_evidence_age_hours,
        block=config.block_aggregate_evidence_age_hours,
    )
    deadline_pressure = _lower_pressure(
        item.hours_until_resolution_deadline,
        watch=config.watch_deadline_proximity_hours,
        block=config.block_deadline_proximity_hours,
    )
    lag_pressure = _upper_pressure(
        item.oracle_lag_hours,
        watch=config.watch_oracle_lag_hours,
        block=config.block_oracle_lag_hours,
    )
    reliability_gap = _quantize(_ONE - item.aggregate_source_reliability)
    risk_score = _quantize(
        (age_pressure * config.aggregate_evidence_age_weight)
        + (deadline_pressure * config.deadline_proximity_weight)
        + (lag_pressure * config.oracle_lag_weight)
        + (reliability_gap * config.source_reliability_weight)
        + (item.contradiction_pressure * config.contradiction_pressure_weight),
    )
    status = _row_status(risk_score, config=config)
    return ResearchResolutionEvidenceRefreshSlaRow(
        public_bucket_id=item.public_bucket_id,
        aggregate_evidence_age_hours=item.aggregate_evidence_age_hours,
        aggregate_evidence_age_pressure=age_pressure,
        hours_until_resolution_deadline=item.hours_until_resolution_deadline,
        deadline_proximity_pressure=deadline_pressure,
        oracle_lag_hours=item.oracle_lag_hours,
        oracle_lag_pressure=lag_pressure,
        aggregate_source_reliability=item.aggregate_source_reliability,
        source_reliability_gap=reliability_gap,
        contradiction_pressure=item.contradiction_pressure,
        refresh_sla_risk_score=risk_score,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            aggregate_evidence_age_pressure=age_pressure,
            deadline_proximity_pressure=deadline_pressure,
            oracle_lag_pressure=lag_pressure,
            aggregate_source_reliability=item.aggregate_source_reliability,
            contradiction_pressure=item.contradiction_pressure,
            input_reason_codes=item.reason_codes,
        ),
    )


def _normalize_refresh_items(
    refresh_items: Iterable[object],
) -> tuple[ResearchResolutionEvidenceRefreshSlaInput, ...]:
    if isinstance(refresh_items, (str, bytes)):
        raise ValueError("refresh_items must be an iterable")
    try:
        values = tuple(refresh_items)
    except TypeError as exc:
        raise ValueError("refresh_items must be an iterable") from exc
    return tuple(_coerce_refresh_item(value) for value in values)


def _coerce_refresh_item(value: object) -> ResearchResolutionEvidenceRefreshSlaInput:
    if type(value) is ResearchResolutionEvidenceRefreshSlaInput:
        _require_hard_flags("refresh SLA input", value)
        return value
    _require_hard_flags("refresh SLA input", value)
    return ResearchResolutionEvidenceRefreshSlaInput(
        public_bucket_id=_field_value(value, "public_bucket_id"),
        aggregate_evidence_age_hours=_field_value(
            value,
            "aggregate_evidence_age_hours",
        ),
        hours_until_resolution_deadline=_field_value(
            value,
            "hours_until_resolution_deadline",
        ),
        oracle_lag_hours=_field_value(value, "oracle_lag_hours"),
        aggregate_source_reliability=_field_value(
            value,
            "aggregate_source_reliability",
        ),
        contradiction_pressure=_field_value(value, "contradiction_pressure"),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _upper_pressure(value: Decimal, *, watch: Decimal, block: Decimal) -> Decimal:
    if value <= watch:
        return _ZERO
    if value >= block:
        return _ONE
    return _quantize((value - watch) / (block - watch))


def _lower_pressure(value: Decimal, *, watch: Decimal, block: Decimal) -> Decimal:
    if value >= watch:
        return _ZERO
    if value <= block:
        return _ONE
    return _quantize((watch - value) / (watch - block))


def _row_status(
    risk_score: Decimal,
    *,
    config: ResearchResolutionEvidenceRefreshSlaConfig,
) -> str:
    if risk_score >= config.block_risk_threshold:
        return "block"
    if risk_score >= config.watch_risk_threshold:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    aggregate_evidence_age_pressure: Decimal,
    deadline_proximity_pressure: Decimal,
    oracle_lag_pressure: Decimal,
    aggregate_source_reliability: Decimal,
    contradiction_pressure: Decimal,
    input_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    codes: set[str] = {f"resolution_evidence_refresh_sla_{status}"}
    if aggregate_evidence_age_pressure == _ONE:
        codes.add("aggregate_evidence_age_stale")
    elif aggregate_evidence_age_pressure > _ZERO:
        codes.add("aggregate_evidence_age_watch")
    else:
        codes.add("aggregate_evidence_age_fresh")
    if deadline_proximity_pressure == _ONE:
        codes.add("resolution_deadline_imminent")
    elif deadline_proximity_pressure > _ZERO:
        codes.add("resolution_deadline_near")
    else:
        codes.add("resolution_deadline_buffer_sufficient")
    if oracle_lag_pressure == _ONE:
        codes.add("oracle_lag_stale")
    elif oracle_lag_pressure > _ZERO:
        codes.add("oracle_lag_aging")
    else:
        codes.add("oracle_lag_fresh")
    if aggregate_source_reliability < Decimal("0.500000"):
        codes.add("source_reliability_low")
    elif aggregate_source_reliability < Decimal("0.800000"):
        codes.add("source_reliability_mixed")
    else:
        codes.add("source_reliability_strong")
    if contradiction_pressure >= Decimal("0.500000"):
        codes.add("contradiction_pressure_high")
    elif contradiction_pressure >= Decimal("0.250000"):
        codes.add("contradiction_pressure_watch")
    for reason_code in input_reason_codes:
        codes.add(f"input_{reason_code}")
    return tuple(sorted(codes))


def _report_status(
    rows: tuple[ResearchResolutionEvidenceRefreshSlaRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchResolutionEvidenceRefreshSlaRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_refresh_sla_items",)
    if all(row.status == "pass" for row in rows):
        return ("resolution_evidence_refresh_sla_pass",)
    return tuple(sorted({code for row in rows for code in row.reason_codes}))


def _reason_code_counts(
    rows: tuple[ResearchResolutionEvidenceRefreshSlaRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchResolutionEvidenceRefreshSlaReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchResolutionEvidenceRefreshSlaReasonCodeCount(
                reason_code=reason_codes[0],
                count=Decimal("1"),
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchResolutionEvidenceRefreshSlaReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _average_refresh_sla_risk_score(
    rows: tuple[ResearchResolutionEvidenceRefreshSlaRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(
        sum((row.refresh_sla_risk_score for row in rows), _ZERO) / Decimal(len(rows)),
    )


def _average_aggregate_evidence_age_hours(
    rows: tuple[ResearchResolutionEvidenceRefreshSlaRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(
        sum((row.aggregate_evidence_age_hours for row in rows), _ZERO)
        / Decimal(len(rows)),
    )


def _min_hours_until_resolution_deadline(
    rows: tuple[ResearchResolutionEvidenceRefreshSlaRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return min(row.hours_until_resolution_deadline for row in rows)


def _status_count(
    rows: tuple[ResearchResolutionEvidenceRefreshSlaRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_rows(
    rows: tuple[ResearchResolutionEvidenceRefreshSlaRow, ...],
) -> tuple[ResearchResolutionEvidenceRefreshSlaRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchResolutionEvidenceRefreshSlaRow:
            raise ValueError(
                "rows must contain ResearchResolutionEvidenceRefreshSlaRow values",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.public_bucket_id))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by public_bucket_id")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchResolutionEvidenceRefreshSlaReasonCodeCount, ...],
) -> tuple[ResearchResolutionEvidenceRefreshSlaReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchResolutionEvidenceRefreshSlaReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchResolutionEvidenceRefreshSlaReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row_consistency(row: ResearchResolutionEvidenceRefreshSlaRow) -> None:
    if row.source_reliability_gap != _quantize(_ONE - row.aggregate_source_reliability):
        raise ValueError("source_reliability_gap must match aggregate_source_reliability")
    if row.status == "pass" and row.refresh_sla_risk_score >= Decimal("0.350000"):
        raise ValueError("refresh_sla_risk_score must support pass status")
    if row.status == "watch" and (
        row.refresh_sla_risk_score < Decimal("0.350000")
        or row.refresh_sla_risk_score >= Decimal("0.700000")
    ):
        raise ValueError("refresh_sla_risk_score must support watch status")
    if row.status == "block" and row.refresh_sla_risk_score < Decimal("0.700000"):
        raise ValueError("refresh_sla_risk_score must support block status")


def _validate_report_consistency(
    report: ResearchResolutionEvidenceRefreshSlaReport,
) -> None:
    if report.bucket_count != _decimal_count(len(report.rows)):
        raise ValueError("bucket_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_refresh_sla_risk_score != _average_refresh_sla_risk_score(
        report.rows,
    ):
        raise ValueError("average_refresh_sla_risk_score must match rows")
    if report.average_aggregate_evidence_age_hours != (
        _average_aggregate_evidence_age_hours(report.rows)
    ):
        raise ValueError("average_aggregate_evidence_age_hours must match rows")
    if report.max_aggregate_evidence_age_hours != max(
        (row.aggregate_evidence_age_hours for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_aggregate_evidence_age_hours must match rows")
    if report.min_hours_until_resolution_deadline != _min_hours_until_resolution_deadline(
        report.rows,
    ):
        raise ValueError("min_hours_until_resolution_deadline must match rows")
    if report.max_oracle_lag_hours != max(
        (row.oracle_lag_hours for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_oracle_lag_hours must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _report_values_without_digest(
    report: ResearchResolutionEvidenceRefreshSlaReport,
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


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


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
        raise ValueError("count input must be an int")
    if value < 0:
        raise ValueError("count input must be nonnegative")
    return Decimal(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT)


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty public identifier")
    if _PUBLIC_IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public identifier")


def _require_public_bucket_id(field_name: str, value: object) -> None:
    _require_public_identifier(field_name, value)
    lowered = value.lower()
    if any(term in lowered for term in _BUCKET_ID_UNSAFE_TERMS):
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
