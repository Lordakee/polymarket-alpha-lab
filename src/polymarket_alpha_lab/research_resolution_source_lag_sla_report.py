"""Pure report-only SLA summary for public-safe resolution source lag."""

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
    "ResearchResolutionSourceLagSlaConfig",
    "ResearchResolutionSourceLagSlaInput",
    "ResearchResolutionSourceLagSlaReasonCodeCount",
    "ResearchResolutionSourceLagSlaReport",
    "ResearchResolutionSourceLagSlaRow",
    "STATUSES",
    "build_research_resolution_source_lag_sla_report",
    "research_resolution_source_lag_sla_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-resolution-source-lag-sla-report-v0"
STATUSES = ("pass", "watch", "block")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_QUANT = Decimal("0.000001")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_KEY_UNSAFE_TERMS = (
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
    "://",
    "source_" + "url",
    "source_" + "text",
    "source_" + "ref",
    "source_" + "reference",
    "raw_" + "source",
    "raw_" + "url",
    "raw_" + "text",
    "raw_" + "ref",
    "market_" + "slug",
    "market_" + "id",
    "condition_" + "id",
)
_ACTION_TERMS = (
    "wal" + "let",
    "au" + "th_token",
    "oa" + "uth",
    "api_" + "key",
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
class ResearchResolutionSourceLagSlaConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    authoritative_source_watch_lag_seconds: Decimal = Decimal("1800")
    authoritative_source_block_lag_seconds: Decimal = Decimal("14400")
    secondary_corroboration_watch_lag_seconds: Decimal = Decimal("3600")
    secondary_corroboration_block_lag_seconds: Decimal = Decimal("21600")
    unresolved_queue_watch_age_seconds: Decimal = Decimal("43200")
    unresolved_queue_block_age_seconds: Decimal = Decimal("172800")
    watch_pressure_threshold: Decimal = Decimal("0.350000")
    block_pressure_threshold: Decimal = Decimal("0.700000")
    authoritative_source_lag_weight: Decimal = Decimal("0.300000")
    secondary_corroboration_lag_weight: Decimal = Decimal("0.200000")
    ambiguity_pressure_weight: Decimal = Decimal("0.200000")
    unresolved_queue_age_weight: Decimal = Decimal("0.200000")
    manual_escalation_urgency_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchResolutionSourceLagSlaConfig:
            raise TypeError(
                "ResearchResolutionSourceLagSlaConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchResolutionSourceLagSlaConfig, "config")
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "authoritative_source_watch_lag_seconds",
            "authoritative_source_block_lag_seconds",
            "secondary_corroboration_watch_lag_seconds",
            "secondary_corroboration_block_lag_seconds",
            "unresolved_queue_watch_age_seconds",
            "unresolved_queue_block_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.authoritative_source_block_lag_seconds
            <= self.authoritative_source_watch_lag_seconds
        ):
            raise ValueError(
                "authoritative_source_block_lag_seconds must exceed "
                "authoritative_source_watch_lag_seconds",
            )
        if (
            self.secondary_corroboration_block_lag_seconds
            <= self.secondary_corroboration_watch_lag_seconds
        ):
            raise ValueError(
                "secondary_corroboration_block_lag_seconds must exceed "
                "secondary_corroboration_watch_lag_seconds",
            )
        if self.unresolved_queue_block_age_seconds <= self.unresolved_queue_watch_age_seconds:
            raise ValueError(
                "unresolved_queue_block_age_seconds must exceed "
                "unresolved_queue_watch_age_seconds",
            )
        for field_name in (
            "watch_pressure_threshold",
            "block_pressure_threshold",
            "authoritative_source_lag_weight",
            "secondary_corroboration_lag_weight",
            "ambiguity_pressure_weight",
            "unresolved_queue_age_weight",
            "manual_escalation_urgency_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_pressure_threshold <= self.watch_pressure_threshold:
            raise ValueError("block_pressure_threshold must exceed watch_pressure_threshold")
        weight_sum = _quantize(
            self.authoritative_source_lag_weight
            + self.secondary_corroboration_lag_weight
            + self.ambiguity_pressure_weight
            + self.unresolved_queue_age_weight
            + self.manual_escalation_urgency_weight,
        )
        if weight_sum != _ONE:
            raise ValueError(
                "authoritative_source_lag_weight, "
                "secondary_corroboration_lag_weight, ambiguity_pressure_weight, "
                "unresolved_queue_age_weight, and manual_escalation_urgency_weight "
                "must sum to 1",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchResolutionSourceLagSlaInput:
    public_resolution_key: str
    authoritative_source_lag_seconds: Decimal
    secondary_corroboration_lag_seconds: Decimal
    ambiguity_pressure: Decimal
    unresolved_outcome_queue_age_seconds: Decimal
    manual_escalation_urgency: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchResolutionSourceLagSlaInput:
            raise TypeError(
                "ResearchResolutionSourceLagSlaInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchResolutionSourceLagSlaInput, "SLA input")
        _require_public_resolution_key("public_resolution_key", self.public_resolution_key)
        for field_name in (
            "authoritative_source_lag_seconds",
            "secondary_corroboration_lag_seconds",
            "unresolved_outcome_queue_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "ambiguity_pressure",
            "manual_escalation_urgency",
        ):
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
        _require_hard_flags("SLA input", self)


@dataclass(frozen=True)
class ResearchResolutionSourceLagSlaRow:
    public_resolution_key: str
    authoritative_source_lag_seconds: Decimal
    authoritative_source_lag_pressure: Decimal
    secondary_corroboration_lag_seconds: Decimal
    secondary_corroboration_lag_pressure: Decimal
    ambiguity_pressure: Decimal
    unresolved_outcome_queue_age_seconds: Decimal
    unresolved_outcome_queue_age_pressure: Decimal
    manual_escalation_urgency: Decimal
    sla_pressure: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchResolutionSourceLagSlaRow:
            raise TypeError(
                "ResearchResolutionSourceLagSlaRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchResolutionSourceLagSlaRow, "row")
        _require_public_resolution_key("public_resolution_key", self.public_resolution_key)
        for field_name in (
            "authoritative_source_lag_seconds",
            "secondary_corroboration_lag_seconds",
            "unresolved_outcome_queue_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "authoritative_source_lag_pressure",
            "secondary_corroboration_lag_pressure",
            "ambiguity_pressure",
            "unresolved_outcome_queue_age_pressure",
            "manual_escalation_urgency",
            "sla_pressure",
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
class ResearchResolutionSourceLagSlaReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchResolutionSourceLagSlaReasonCodeCount:
            raise TypeError(
                "ResearchResolutionSourceLagSlaReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchResolutionSourceLagSlaReasonCodeCount,
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
class ResearchResolutionSourceLagSlaReport:
    generated_at: datetime
    config_version: str
    resolution_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_sla_pressure: Decimal | None
    max_authoritative_source_lag_seconds: Decimal
    max_secondary_corroboration_lag_seconds: Decimal
    max_unresolved_outcome_queue_age_seconds: Decimal
    status: str
    rows: tuple[ResearchResolutionSourceLagSlaRow, ...]
    reason_code_counts: tuple[ResearchResolutionSourceLagSlaReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchResolutionSourceLagSlaReport:
            raise TypeError(
                "ResearchResolutionSourceLagSlaReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchResolutionSourceLagSlaReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in ("resolution_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_sla_pressure",
            _require_optional_probability_decimal(
                "average_sla_pressure",
                self.average_sla_pressure,
            ),
        )
        for field_name in (
            "max_authoritative_source_lag_seconds",
            "max_secondary_corroboration_lag_seconds",
            "max_unresolved_outcome_queue_age_seconds",
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


def build_research_resolution_source_lag_sla_report(
    sla_items: Iterable[object],
    *,
    config: ResearchResolutionSourceLagSlaConfig,
    generated_at: datetime,
) -> ResearchResolutionSourceLagSlaReport:
    if type(config) is not ResearchResolutionSourceLagSlaConfig:
        raise ValueError("config must be a ResearchResolutionSourceLagSlaConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_items = _normalize_sla_items(sla_items)
    rows = tuple(
        _row_from_item(item, config=config)
        for item in sorted(normalized_items, key=lambda value: value.public_resolution_key)
    )
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "resolution_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_sla_pressure": _average_sla_pressure(rows),
        "max_authoritative_source_lag_seconds": max(
            (row.authoritative_source_lag_seconds for row in rows),
            default=_ZERO,
        ),
        "max_secondary_corroboration_lag_seconds": max(
            (row.secondary_corroboration_lag_seconds for row in rows),
            default=_ZERO,
        ),
        "max_unresolved_outcome_queue_age_seconds": max(
            (row.unresolved_outcome_queue_age_seconds for row in rows),
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
    return ResearchResolutionSourceLagSlaReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_resolution_source_lag_sla_report_payload(
    report: ResearchResolutionSourceLagSlaReport,
) -> dict[str, Any]:
    if type(report) is not ResearchResolutionSourceLagSlaReport:
        raise ValueError("report must be a ResearchResolutionSourceLagSlaReport")
    _require_hard_flags("report", report)
    payload = _json_ready(asdict(report))
    _reject_public_payload("report payload", payload)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _row_from_item(
    item: ResearchResolutionSourceLagSlaInput,
    *,
    config: ResearchResolutionSourceLagSlaConfig,
) -> ResearchResolutionSourceLagSlaRow:
    authoritative_source_lag_pressure = _linear_pressure(
        item.authoritative_source_lag_seconds,
        capped_at=config.authoritative_source_block_lag_seconds,
    )
    secondary_corroboration_lag_pressure = _linear_pressure(
        item.secondary_corroboration_lag_seconds,
        capped_at=config.secondary_corroboration_block_lag_seconds,
    )
    unresolved_outcome_queue_age_pressure = _linear_pressure(
        item.unresolved_outcome_queue_age_seconds,
        capped_at=config.unresolved_queue_block_age_seconds,
    )
    sla_pressure = _quantize(
        (authoritative_source_lag_pressure * config.authoritative_source_lag_weight)
        + (
            secondary_corroboration_lag_pressure
            * config.secondary_corroboration_lag_weight
        )
        + (item.ambiguity_pressure * config.ambiguity_pressure_weight)
        + (unresolved_outcome_queue_age_pressure * config.unresolved_queue_age_weight)
        + (item.manual_escalation_urgency * config.manual_escalation_urgency_weight),
    )
    status = _row_status(sla_pressure, config=config)
    return ResearchResolutionSourceLagSlaRow(
        public_resolution_key=item.public_resolution_key,
        authoritative_source_lag_seconds=item.authoritative_source_lag_seconds,
        authoritative_source_lag_pressure=authoritative_source_lag_pressure,
        secondary_corroboration_lag_seconds=item.secondary_corroboration_lag_seconds,
        secondary_corroboration_lag_pressure=secondary_corroboration_lag_pressure,
        ambiguity_pressure=item.ambiguity_pressure,
        unresolved_outcome_queue_age_seconds=item.unresolved_outcome_queue_age_seconds,
        unresolved_outcome_queue_age_pressure=unresolved_outcome_queue_age_pressure,
        manual_escalation_urgency=item.manual_escalation_urgency,
        sla_pressure=sla_pressure,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            authoritative_source_lag_seconds=item.authoritative_source_lag_seconds,
            authoritative_source_lag_pressure=authoritative_source_lag_pressure,
            secondary_corroboration_lag_seconds=item.secondary_corroboration_lag_seconds,
            secondary_corroboration_lag_pressure=secondary_corroboration_lag_pressure,
            ambiguity_pressure=item.ambiguity_pressure,
            unresolved_outcome_queue_age_seconds=item.unresolved_outcome_queue_age_seconds,
            unresolved_outcome_queue_age_pressure=unresolved_outcome_queue_age_pressure,
            manual_escalation_urgency=item.manual_escalation_urgency,
            input_reason_codes=item.reason_codes,
            config=config,
        ),
    )


def _normalize_sla_items(
    sla_items: Iterable[object],
) -> tuple[ResearchResolutionSourceLagSlaInput, ...]:
    if isinstance(sla_items, (str, bytes)):
        raise ValueError("sla_items must be an iterable")
    try:
        values = tuple(sla_items)
    except TypeError as exc:
        raise ValueError("sla_items must be an iterable") from exc
    normalized = tuple(_coerce_sla_item(value) for value in values)
    public_resolution_keys = tuple(item.public_resolution_key for item in normalized)
    if len(set(public_resolution_keys)) != len(public_resolution_keys):
        raise ValueError("duplicate public_resolution_key")
    return normalized


def _coerce_sla_item(value: object) -> ResearchResolutionSourceLagSlaInput:
    if type(value) is ResearchResolutionSourceLagSlaInput:
        _require_hard_flags("SLA input", value)
        return value
    _require_hard_flags("SLA input", value)
    return ResearchResolutionSourceLagSlaInput(
        public_resolution_key=_field_value(value, "public_resolution_key"),
        authoritative_source_lag_seconds=_field_value(
            value,
            "authoritative_source_lag_seconds",
        ),
        secondary_corroboration_lag_seconds=_field_value(
            value,
            "secondary_corroboration_lag_seconds",
        ),
        ambiguity_pressure=_field_value(value, "ambiguity_pressure"),
        unresolved_outcome_queue_age_seconds=_field_value(
            value,
            "unresolved_outcome_queue_age_seconds",
        ),
        manual_escalation_urgency=_field_value(value, "manual_escalation_urgency"),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _linear_pressure(value: Decimal, *, capped_at: Decimal) -> Decimal:
    if value <= _ZERO:
        return _ZERO
    if value >= capped_at:
        return _ONE
    return _quantize(value / capped_at)


def _row_status(
    sla_pressure: Decimal,
    *,
    config: ResearchResolutionSourceLagSlaConfig,
) -> str:
    if sla_pressure >= config.block_pressure_threshold:
        return "block"
    if sla_pressure >= config.watch_pressure_threshold:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    authoritative_source_lag_seconds: Decimal,
    authoritative_source_lag_pressure: Decimal,
    secondary_corroboration_lag_seconds: Decimal,
    secondary_corroboration_lag_pressure: Decimal,
    ambiguity_pressure: Decimal,
    unresolved_outcome_queue_age_seconds: Decimal,
    unresolved_outcome_queue_age_pressure: Decimal,
    manual_escalation_urgency: Decimal,
    input_reason_codes: tuple[str, ...],
    config: ResearchResolutionSourceLagSlaConfig,
) -> tuple[str, ...]:
    codes: set[str] = {f"resolution_source_lag_sla_{status}"}
    if authoritative_source_lag_seconds >= config.authoritative_source_block_lag_seconds:
        codes.add("authoritative_source_lag_block")
    elif authoritative_source_lag_seconds >= config.authoritative_source_watch_lag_seconds:
        codes.add("authoritative_source_lag_watch")
    elif authoritative_source_lag_pressure > _ZERO:
        codes.add("authoritative_source_lag_low")
    else:
        codes.add("authoritative_source_lag_fresh")
    if (
        secondary_corroboration_lag_seconds
        >= config.secondary_corroboration_block_lag_seconds
    ):
        codes.add("secondary_corroboration_lag_block")
    elif (
        secondary_corroboration_lag_seconds
        >= config.secondary_corroboration_watch_lag_seconds
    ):
        codes.add("secondary_corroboration_lag_watch")
    elif secondary_corroboration_lag_pressure > _ZERO:
        codes.add("secondary_corroboration_lag_low")
    else:
        codes.add("secondary_corroboration_lag_fresh")
    if ambiguity_pressure >= Decimal("0.750000"):
        codes.add("ambiguity_pressure_high")
    elif ambiguity_pressure >= Decimal("0.350000"):
        codes.add("ambiguity_pressure_watch")
    else:
        codes.add("ambiguity_pressure_low")
    if (
        unresolved_outcome_queue_age_seconds
        >= config.unresolved_queue_block_age_seconds
    ):
        codes.add("unresolved_outcome_queue_age_block")
    elif (
        unresolved_outcome_queue_age_seconds
        >= config.unresolved_queue_watch_age_seconds
    ):
        codes.add("unresolved_outcome_queue_age_watch")
    elif unresolved_outcome_queue_age_pressure > _ZERO:
        codes.add("unresolved_outcome_queue_age_low")
    else:
        codes.add("unresolved_outcome_queue_age_fresh")
    if manual_escalation_urgency >= Decimal("0.750000"):
        codes.add("manual_escalation_urgency_high")
    elif manual_escalation_urgency >= Decimal("0.350000"):
        codes.add("manual_escalation_urgency_watch")
    else:
        codes.add("manual_escalation_urgency_low")
    for reason_code in input_reason_codes:
        codes.add(f"input_{reason_code}")
    return tuple(sorted(codes))


def _report_status(rows: tuple[ResearchResolutionSourceLagSlaRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchResolutionSourceLagSlaRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_resolution_source_lag_sla_items",)
    if all(row.status == "pass" for row in rows):
        return ("resolution_source_lag_sla_pass",)
    return tuple(sorted({code for row in rows for code in row.reason_codes}))


def _reason_code_counts(
    rows: tuple[ResearchResolutionSourceLagSlaRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchResolutionSourceLagSlaReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchResolutionSourceLagSlaReasonCodeCount(
                reason_code=reason_codes[0],
                count=_ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchResolutionSourceLagSlaReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _average_sla_pressure(
    rows: tuple[ResearchResolutionSourceLagSlaRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(sum((row.sla_pressure for row in rows), _ZERO) / Decimal(len(rows)))


def _status_count(rows: tuple[ResearchResolutionSourceLagSlaRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_rows(
    rows: tuple[ResearchResolutionSourceLagSlaRow, ...],
) -> tuple[ResearchResolutionSourceLagSlaRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchResolutionSourceLagSlaRow:
            raise ValueError("rows must contain ResearchResolutionSourceLagSlaRow values")
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.public_resolution_key))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by public_resolution_key")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchResolutionSourceLagSlaReasonCodeCount, ...],
) -> tuple[ResearchResolutionSourceLagSlaReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchResolutionSourceLagSlaReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchResolutionSourceLagSlaReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row_consistency(row: ResearchResolutionSourceLagSlaRow) -> None:
    if not row.reason_codes:
        raise ValueError("reason_codes must be nonempty")
    if f"resolution_source_lag_sla_{row.status}" not in row.reason_codes:
        raise ValueError("reason_codes must include row status")
    if row.status == "pass" and row.sla_pressure >= Decimal("0.350000"):
        raise ValueError("sla_pressure must match status")
    if row.status == "watch" and (
        row.sla_pressure < Decimal("0.350000") or row.sla_pressure >= Decimal("0.700000")
    ):
        raise ValueError("sla_pressure must match status")
    if row.status == "block" and row.sla_pressure < Decimal("0.700000"):
        raise ValueError("sla_pressure must match status")


def _validate_report_consistency(report: ResearchResolutionSourceLagSlaReport) -> None:
    if report.resolution_count != _decimal_count(len(report.rows)):
        raise ValueError("resolution_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_sla_pressure != _average_sla_pressure(report.rows):
        raise ValueError("average_sla_pressure must match rows")
    expected_max_authoritative = max(
        (row.authoritative_source_lag_seconds for row in report.rows),
        default=_ZERO,
    )
    if report.max_authoritative_source_lag_seconds != expected_max_authoritative:
        raise ValueError("max_authoritative_source_lag_seconds must match rows")
    expected_max_secondary = max(
        (row.secondary_corroboration_lag_seconds for row in report.rows),
        default=_ZERO,
    )
    if report.max_secondary_corroboration_lag_seconds != expected_max_secondary:
        raise ValueError("max_secondary_corroboration_lag_seconds must match rows")
    expected_max_queue_age = max(
        (row.unresolved_outcome_queue_age_seconds for row in report.rows),
        default=_ZERO,
    )
    if report.max_unresolved_outcome_queue_age_seconds != expected_max_queue_age:
        raise ValueError("max_unresolved_outcome_queue_age_seconds must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _report_values_without_digest(
    report: ResearchResolutionSourceLagSlaReport,
) -> dict[str, object]:
    return {
        field.name: getattr(report, field.name)
        for field in fields(report)
        if field.name != "derived_validation_digest"
    }


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    ready = _json_ready(dict(values))
    _reject_public_payload("report digest payload", ready)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":"))
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


def _field_value(value: object, name: str, default: object = _MISSING) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        if any(field.name == name for field in fields(value)):
            return getattr(value, name)
    elif isinstance(value, Mapping):
        if name in value:
            return value[name]
    elif hasattr(value, name):
        return getattr(value, name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{name} is required")


def _as_utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_public_identifier(name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{name} must be a public identifier")
    _reject_text_value(name, value)
    return value


def _require_public_resolution_key(name: str, value: str) -> str:
    _require_public_identifier(name, value)
    normalized = value.lower()
    if any(term in normalized for term in _PUBLIC_KEY_UNSAFE_TERMS):
        raise ValueError(f"{name} must not expose public source or market identifiers")
    return value


def _require_reason_code(name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not _REASON_CODE_RE.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase reason code")
    _reject_text_value(name, value)
    return value


def _normalize_reason_codes(
    name: str,
    value: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    if not allow_empty and not value:
        raise ValueError(f"{name} must be nonempty")
    normalized = tuple(_require_reason_code(name, item) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{name} must not contain duplicates")
    return tuple(sorted(normalized))


def _require_status(name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if value not in STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")
    return value


def _require_positive_decimal(name: str, value: Decimal) -> Decimal:
    result = _require_decimal(name, value)
    if result <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return _quantize(result)


def _require_nonnegative_decimal(name: str, value: Decimal) -> Decimal:
    result = _require_decimal(name, value)
    if result < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize(result)


def _require_positive_whole_decimal(name: str, value: Decimal) -> Decimal:
    result = _require_positive_decimal(name, value)
    if result != result.to_integral_value():
        raise ValueError(f"{name} must be a whole Decimal")
    return result


def _require_nonnegative_whole_decimal(name: str, value: Decimal) -> Decimal:
    result = _require_nonnegative_decimal(name, value)
    if result != result.to_integral_value():
        raise ValueError(f"{name} must be a whole Decimal")
    return result


def _require_probability_decimal(name: str, value: Decimal) -> Decimal:
    result = _require_decimal(name, value)
    if result < _ZERO or result > _ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return _quantize(result)


def _require_optional_probability_decimal(
    name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(name, value)


def _require_decimal(name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _require_digest(name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{name} must be a sha256 digest")
    return value


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


def _reject_public_payload(label: str, value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _reject_text_value(label, key)
            _reject_public_payload(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_payload(label, item)
        return
    if type(value) is str:
        _reject_text_value(label, value)


def _reject_text_value(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in _PAYLOAD_UNSAFE_FRAGMENTS):
        raise ValueError(f"{label} contains unsafe public surface text")
    if any(term in normalized for term in _ACTION_TERMS):
        raise ValueError(f"{label} contains unsafe action text")
