"""Pure report-only monitor for public-safe resolution source lag."""

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
    "ResearchResolutionSourceLagWatchConfig",
    "ResearchResolutionSourceLagWatchInput",
    "ResearchResolutionSourceLagWatchReasonCodeCount",
    "ResearchResolutionSourceLagWatchReport",
    "ResearchResolutionSourceLagWatchRow",
    "STATUSES",
    "build_research_resolution_source_lag_watch_report",
    "research_resolution_source_lag_watch_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-resolution-source-lag-watch-report-v0"
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
class ResearchResolutionSourceLagWatchConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    fresh_source_age_seconds: Decimal = Decimal("3600")
    stale_source_age_seconds: Decimal = Decimal("86400")
    oracle_watch_lag_seconds: Decimal = Decimal("1800")
    oracle_block_lag_seconds: Decimal = Decimal("14400")
    watch_pressure_threshold: Decimal = Decimal("0.350000")
    block_pressure_threshold: Decimal = Decimal("0.700000")
    aggregate_source_age_weight: Decimal = Decimal("0.250000")
    oracle_lag_weight: Decimal = Decimal("0.250000")
    deadline_proximity_weight: Decimal = Decimal("0.200000")
    contradiction_pressure_weight: Decimal = Decimal("0.200000")
    reliability_memory_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchResolutionSourceLagWatchConfig:
            raise TypeError(
                "ResearchResolutionSourceLagWatchConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchResolutionSourceLagWatchConfig, "config")
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "fresh_source_age_seconds",
            "stale_source_age_seconds",
            "oracle_watch_lag_seconds",
            "oracle_block_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_source_age_seconds <= self.fresh_source_age_seconds:
            raise ValueError("stale_source_age_seconds must exceed fresh_source_age_seconds")
        if self.oracle_block_lag_seconds <= self.oracle_watch_lag_seconds:
            raise ValueError("oracle_block_lag_seconds must exceed oracle_watch_lag_seconds")
        for field_name in (
            "watch_pressure_threshold",
            "block_pressure_threshold",
            "aggregate_source_age_weight",
            "oracle_lag_weight",
            "deadline_proximity_weight",
            "contradiction_pressure_weight",
            "reliability_memory_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_pressure_threshold <= self.watch_pressure_threshold:
            raise ValueError("block_pressure_threshold must exceed watch_pressure_threshold")
        weight_sum = _quantize(
            self.aggregate_source_age_weight
            + self.oracle_lag_weight
            + self.deadline_proximity_weight
            + self.contradiction_pressure_weight
            + self.reliability_memory_weight,
        )
        if weight_sum != _ONE:
            raise ValueError(
                "aggregate_source_age_weight, oracle_lag_weight, "
                "deadline_proximity_weight, contradiction_pressure_weight, "
                "and reliability_memory_weight must sum to 1",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchResolutionSourceLagWatchInput:
    public_case_key: str
    aggregate_source_age_seconds: Decimal
    oracle_lag_seconds: Decimal
    deadline_proximity: Decimal
    contradiction_pressure: Decimal
    reliability_memory_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchResolutionSourceLagWatchInput:
            raise TypeError(
                "ResearchResolutionSourceLagWatchInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchResolutionSourceLagWatchInput, "lag input")
        _require_public_case_key("public_case_key", self.public_case_key)
        for field_name in ("aggregate_source_age_seconds", "oracle_lag_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "deadline_proximity",
            "contradiction_pressure",
            "reliability_memory_score",
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
        _require_hard_flags("lag input", self)


@dataclass(frozen=True)
class ResearchResolutionSourceLagWatchRow:
    public_case_key: str
    aggregate_source_age_seconds: Decimal
    aggregate_source_age_pressure: Decimal
    oracle_lag_seconds: Decimal
    oracle_lag_pressure: Decimal
    deadline_proximity: Decimal
    contradiction_pressure: Decimal
    reliability_memory_score: Decimal
    reliability_memory_gap: Decimal
    lag_pressure: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchResolutionSourceLagWatchRow:
            raise TypeError(
                "ResearchResolutionSourceLagWatchRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchResolutionSourceLagWatchRow, "row")
        _require_public_case_key("public_case_key", self.public_case_key)
        for field_name in ("aggregate_source_age_seconds", "oracle_lag_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "aggregate_source_age_pressure",
            "oracle_lag_pressure",
            "deadline_proximity",
            "contradiction_pressure",
            "reliability_memory_score",
            "reliability_memory_gap",
            "lag_pressure",
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
class ResearchResolutionSourceLagWatchReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchResolutionSourceLagWatchReasonCodeCount:
            raise TypeError(
                "ResearchResolutionSourceLagWatchReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchResolutionSourceLagWatchReasonCodeCount,
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
class ResearchResolutionSourceLagWatchReport:
    generated_at: datetime
    config_version: str
    case_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_lag_pressure: Decimal | None
    max_aggregate_source_age_seconds: Decimal
    max_oracle_lag_seconds: Decimal
    status: str
    rows: tuple[ResearchResolutionSourceLagWatchRow, ...]
    reason_code_counts: tuple[ResearchResolutionSourceLagWatchReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchResolutionSourceLagWatchReport:
            raise TypeError(
                "ResearchResolutionSourceLagWatchReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchResolutionSourceLagWatchReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
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
            "average_lag_pressure",
            _require_optional_probability_decimal(
                "average_lag_pressure",
                self.average_lag_pressure,
            ),
        )
        for field_name in ("max_aggregate_source_age_seconds", "max_oracle_lag_seconds"):
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


def build_research_resolution_source_lag_watch_report(
    lag_items: Iterable[object],
    *,
    config: ResearchResolutionSourceLagWatchConfig,
    generated_at: datetime,
) -> ResearchResolutionSourceLagWatchReport:
    if type(config) is not ResearchResolutionSourceLagWatchConfig:
        raise ValueError("config must be a ResearchResolutionSourceLagWatchConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_items = _normalize_lag_items(lag_items)
    rows = tuple(
        _row_from_item(item, config=config)
        for item in sorted(normalized_items, key=lambda value: value.public_case_key)
    )
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "case_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_lag_pressure": _average_lag_pressure(rows),
        "max_aggregate_source_age_seconds": max(
            (row.aggregate_source_age_seconds for row in rows),
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
    return ResearchResolutionSourceLagWatchReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_resolution_source_lag_watch_report_payload(
    report: ResearchResolutionSourceLagWatchReport,
) -> dict[str, Any]:
    if type(report) is not ResearchResolutionSourceLagWatchReport:
        raise ValueError("report must be a ResearchResolutionSourceLagWatchReport")
    _require_hard_flags("report", report)
    payload = _json_ready(asdict(report))
    _reject_public_payload("report payload", payload)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _row_from_item(
    item: ResearchResolutionSourceLagWatchInput,
    *,
    config: ResearchResolutionSourceLagWatchConfig,
) -> ResearchResolutionSourceLagWatchRow:
    aggregate_source_age_pressure = _linear_pressure(
        item.aggregate_source_age_seconds,
        zero_at=config.fresh_source_age_seconds,
        capped_at=config.stale_source_age_seconds,
    )
    oracle_lag_pressure = _linear_pressure(
        item.oracle_lag_seconds,
        zero_at=_ZERO,
        capped_at=config.oracle_block_lag_seconds,
    )
    reliability_memory_gap = _quantize(_ONE - item.reliability_memory_score)
    lag_pressure = _quantize(
        (aggregate_source_age_pressure * config.aggregate_source_age_weight)
        + (oracle_lag_pressure * config.oracle_lag_weight)
        + (item.deadline_proximity * config.deadline_proximity_weight)
        + (item.contradiction_pressure * config.contradiction_pressure_weight)
        + (reliability_memory_gap * config.reliability_memory_weight),
    )
    status = _row_status(lag_pressure, config=config)
    return ResearchResolutionSourceLagWatchRow(
        public_case_key=item.public_case_key,
        aggregate_source_age_seconds=item.aggregate_source_age_seconds,
        aggregate_source_age_pressure=aggregate_source_age_pressure,
        oracle_lag_seconds=item.oracle_lag_seconds,
        oracle_lag_pressure=oracle_lag_pressure,
        deadline_proximity=item.deadline_proximity,
        contradiction_pressure=item.contradiction_pressure,
        reliability_memory_score=item.reliability_memory_score,
        reliability_memory_gap=reliability_memory_gap,
        lag_pressure=lag_pressure,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            aggregate_source_age_pressure=aggregate_source_age_pressure,
            oracle_lag_seconds=item.oracle_lag_seconds,
            oracle_lag_pressure=oracle_lag_pressure,
            deadline_proximity=item.deadline_proximity,
            contradiction_pressure=item.contradiction_pressure,
            reliability_memory_score=item.reliability_memory_score,
            input_reason_codes=item.reason_codes,
            config=config,
        ),
    )


def _normalize_lag_items(
    lag_items: Iterable[object],
) -> tuple[ResearchResolutionSourceLagWatchInput, ...]:
    if isinstance(lag_items, (str, bytes)):
        raise ValueError("lag_items must be an iterable")
    try:
        values = tuple(lag_items)
    except TypeError as exc:
        raise ValueError("lag_items must be an iterable") from exc
    normalized = tuple(_coerce_lag_item(value) for value in values)
    public_case_keys = tuple(item.public_case_key for item in normalized)
    if len(set(public_case_keys)) != len(public_case_keys):
        raise ValueError("duplicate public_case_key")
    return normalized


def _coerce_lag_item(value: object) -> ResearchResolutionSourceLagWatchInput:
    if type(value) is ResearchResolutionSourceLagWatchInput:
        _require_hard_flags("lag input", value)
        return value
    _require_hard_flags("lag input", value)
    return ResearchResolutionSourceLagWatchInput(
        public_case_key=_field_value(value, "public_case_key"),
        aggregate_source_age_seconds=_field_value(
            value,
            "aggregate_source_age_seconds",
        ),
        oracle_lag_seconds=_field_value(value, "oracle_lag_seconds"),
        deadline_proximity=_field_value(value, "deadline_proximity"),
        contradiction_pressure=_field_value(value, "contradiction_pressure"),
        reliability_memory_score=_field_value(value, "reliability_memory_score"),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _linear_pressure(value: Decimal, *, zero_at: Decimal, capped_at: Decimal) -> Decimal:
    if value <= zero_at:
        return _ZERO
    if value >= capped_at:
        return _ONE
    return _quantize(value / capped_at)


def _row_status(
    lag_pressure: Decimal,
    *,
    config: ResearchResolutionSourceLagWatchConfig,
) -> str:
    if lag_pressure >= config.block_pressure_threshold:
        return "block"
    if lag_pressure >= config.watch_pressure_threshold:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    aggregate_source_age_pressure: Decimal,
    oracle_lag_seconds: Decimal,
    oracle_lag_pressure: Decimal,
    deadline_proximity: Decimal,
    contradiction_pressure: Decimal,
    reliability_memory_score: Decimal,
    input_reason_codes: tuple[str, ...],
    config: ResearchResolutionSourceLagWatchConfig,
) -> tuple[str, ...]:
    codes: set[str] = {f"resolution_source_lag_{status}"}
    if aggregate_source_age_pressure == _ZERO:
        codes.add("aggregate_source_age_fresh")
    elif aggregate_source_age_pressure == _ONE:
        codes.add("aggregate_source_age_stale")
    else:
        codes.add("aggregate_source_age_aging")
    if oracle_lag_seconds >= config.oracle_block_lag_seconds:
        codes.add("oracle_lag_block")
    elif oracle_lag_seconds >= config.oracle_watch_lag_seconds or oracle_lag_pressure > _ZERO:
        codes.add("oracle_lag_watch")
    else:
        codes.add("oracle_lag_fresh")
    if deadline_proximity >= Decimal("0.750000"):
        codes.add("deadline_proximity_high")
    elif deadline_proximity >= Decimal("0.350000"):
        codes.add("deadline_proximity_watch")
    if contradiction_pressure >= Decimal("0.500000"):
        codes.add("contradiction_pressure_high")
    elif contradiction_pressure >= Decimal("0.250000"):
        codes.add("contradiction_pressure_watch")
    if reliability_memory_score < Decimal("0.500000"):
        codes.add("reliability_memory_low")
    elif reliability_memory_score < Decimal("0.800000"):
        codes.add("reliability_memory_mixed")
    else:
        codes.add("reliability_memory_strong")
    for reason_code in input_reason_codes:
        codes.add(f"input_{reason_code}")
    return tuple(sorted(codes))


def _report_status(rows: tuple[ResearchResolutionSourceLagWatchRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchResolutionSourceLagWatchRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_resolution_source_lag_items",)
    if all(row.status == "pass" for row in rows):
        return ("resolution_source_lag_pass",)
    return tuple(sorted({code for row in rows for code in row.reason_codes}))


def _reason_code_counts(
    rows: tuple[ResearchResolutionSourceLagWatchRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchResolutionSourceLagWatchReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchResolutionSourceLagWatchReasonCodeCount(
                reason_code=reason_codes[0],
                count=_ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchResolutionSourceLagWatchReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _average_lag_pressure(
    rows: tuple[ResearchResolutionSourceLagWatchRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(sum((row.lag_pressure for row in rows), _ZERO) / Decimal(len(rows)))


def _status_count(rows: tuple[ResearchResolutionSourceLagWatchRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_rows(
    rows: tuple[ResearchResolutionSourceLagWatchRow, ...],
) -> tuple[ResearchResolutionSourceLagWatchRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchResolutionSourceLagWatchRow:
            raise ValueError("rows must contain ResearchResolutionSourceLagWatchRow values")
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.public_case_key))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by public_case_key")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchResolutionSourceLagWatchReasonCodeCount, ...],
) -> tuple[ResearchResolutionSourceLagWatchReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchResolutionSourceLagWatchReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchResolutionSourceLagWatchReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row_consistency(row: ResearchResolutionSourceLagWatchRow) -> None:
    if row.reliability_memory_gap != _quantize(_ONE - row.reliability_memory_score):
        raise ValueError("reliability_memory_gap must match reliability_memory_score")
    if not row.reason_codes:
        raise ValueError("reason_codes must be nonempty")
    if f"resolution_source_lag_{row.status}" not in row.reason_codes:
        raise ValueError("reason_codes must include row status")
    if row.status == "pass" and row.lag_pressure >= Decimal("0.350000"):
        raise ValueError("lag_pressure must match status")
    if row.status == "watch" and (
        row.lag_pressure < Decimal("0.350000") or row.lag_pressure >= Decimal("0.700000")
    ):
        raise ValueError("lag_pressure must match status")
    if row.status == "block" and row.lag_pressure < Decimal("0.700000"):
        raise ValueError("lag_pressure must match status")


def _validate_report_consistency(report: ResearchResolutionSourceLagWatchReport) -> None:
    if report.case_count != _decimal_count(len(report.rows)):
        raise ValueError("case_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_lag_pressure != _average_lag_pressure(report.rows):
        raise ValueError("average_lag_pressure must match rows")
    expected_max_age = max(
        (row.aggregate_source_age_seconds for row in report.rows),
        default=_ZERO,
    )
    if report.max_aggregate_source_age_seconds != expected_max_age:
        raise ValueError("max_aggregate_source_age_seconds must match rows")
    expected_max_oracle_lag = max((row.oracle_lag_seconds for row in report.rows), default=_ZERO)
    if report.max_oracle_lag_seconds != expected_max_oracle_lag:
        raise ValueError("max_oracle_lag_seconds must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _report_values_without_digest(
    report: ResearchResolutionSourceLagWatchReport,
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


def _require_public_case_key(name: str, value: str) -> str:
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
