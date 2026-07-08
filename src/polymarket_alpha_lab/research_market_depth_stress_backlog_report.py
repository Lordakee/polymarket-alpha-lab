"""Pure report-only backlog builder for depth stress research checks."""

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
    "ResearchMarketDepthStressBacklogConfig",
    "ResearchMarketDepthStressBacklogInput",
    "ResearchMarketDepthStressBacklogReasonCodeCount",
    "ResearchMarketDepthStressBacklogReport",
    "ResearchMarketDepthStressBacklogRow",
    "build_research_market_depth_stress_backlog_report",
    "research_market_depth_stress_backlog_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-market-depth-stress-backlog-v0"
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_QUANT = Decimal("0.000001")
_STATUSES = frozenset(("pass", "watch", "block"))
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_CHECK_ID_UNSAFE_TERMS = (
    "http",
    "url",
    "market",
    "condition",
    "slug",
    "source",
    "raw",
)
_PAYLOAD_UNSAFE_FRAGMENTS = (
    "http://",
    "https://",
    "raw_market",
    "market_id",
    "condition_id",
    "source_id",
    "raw_source",
    "source_url",
    "source_text",
    "raw_url",
    "raw_text",
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
class ResearchMarketDepthStressBacklogConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    watch_stress_threshold: Decimal = Decimal("0.350000")
    block_stress_threshold: Decimal = Decimal("0.700000")
    fresh_quote_age_seconds: Decimal = Decimal("60.000000")
    stale_quote_age_seconds: Decimal = Decimal("900.000000")
    aggregate_depth_fade_weight: Decimal = Decimal("0.300000")
    spread_widening_weight: Decimal = Decimal("0.250000")
    quote_age_weight: Decimal = Decimal("0.200000")
    fee_friction_weight: Decimal = Decimal("0.150000")
    catalyst_pressure_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketDepthStressBacklogConfig, "config")
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in ("watch_stress_threshold", "block_stress_threshold"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_stress_threshold <= self.watch_stress_threshold:
            raise ValueError("block_stress_threshold must exceed watch_stress_threshold")
        for field_name in ("fresh_quote_age_seconds", "stale_quote_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_quote_age_seconds <= self.fresh_quote_age_seconds:
            raise ValueError("stale_quote_age_seconds must exceed fresh_quote_age_seconds")
        for field_name in (
            "aggregate_depth_fade_weight",
            "spread_widening_weight",
            "quote_age_weight",
            "fee_friction_weight",
            "catalyst_pressure_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        weight_sum = _quantize(
            self.aggregate_depth_fade_weight
            + self.spread_widening_weight
            + self.quote_age_weight
            + self.fee_friction_weight
            + self.catalyst_pressure_weight,
        )
        if weight_sum != _ONE:
            raise ValueError(
                "aggregate_depth_fade_weight, spread_widening_weight, "
                "quote_age_weight, fee_friction_weight, and catalyst_pressure_weight "
                "must sum to 1",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketDepthStressBacklogInput:
    public_check_id: str
    aggregate_depth_fade: Decimal
    spread_widening: Decimal
    quote_age_seconds: Decimal
    fee_friction: Decimal
    catalyst_pressure: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketDepthStressBacklogInput, "backlog input")
        _require_public_check_id("public_check_id", self.public_check_id)
        for field_name in (
            "aggregate_depth_fade",
            "spread_widening",
            "fee_friction",
            "catalyst_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "quote_age_seconds",
            _require_nonnegative_decimal("quote_age_seconds", self.quote_age_seconds),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("backlog input", self)


@dataclass(frozen=True)
class ResearchMarketDepthStressBacklogRow:
    public_check_id: str
    aggregate_depth_fade: Decimal
    spread_widening: Decimal
    quote_age_seconds: Decimal
    quote_age_pressure: Decimal
    fee_friction: Decimal
    catalyst_pressure: Decimal
    depth_stress_pressure: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketDepthStressBacklogRow, "row")
        _require_public_check_id("public_check_id", self.public_check_id)
        for field_name in (
            "aggregate_depth_fade",
            "spread_widening",
            "quote_age_pressure",
            "fee_friction",
            "catalyst_pressure",
            "depth_stress_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "quote_age_seconds",
            _require_nonnegative_decimal("quote_age_seconds", self.quote_age_seconds),
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
class ResearchMarketDepthStressBacklogReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketDepthStressBacklogReasonCodeCount,
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
class ResearchMarketDepthStressBacklogReport:
    generated_at: datetime
    config_version: str
    check_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_depth_stress_pressure: Decimal | None
    max_quote_age_seconds: Decimal
    max_aggregate_depth_fade: Decimal
    status: str
    rows: tuple[ResearchMarketDepthStressBacklogRow, ...]
    reason_code_counts: tuple[ResearchMarketDepthStressBacklogReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketDepthStressBacklogReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in ("check_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_depth_stress_pressure",
            _require_optional_probability_decimal(
                "average_depth_stress_pressure",
                self.average_depth_stress_pressure,
            ),
        )
        object.__setattr__(
            self,
            "max_quote_age_seconds",
            _require_nonnegative_decimal(
                "max_quote_age_seconds",
                self.max_quote_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "max_aggregate_depth_fade",
            _require_probability_decimal(
                "max_aggregate_depth_fade",
                self.max_aggregate_depth_fade,
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


def build_research_market_depth_stress_backlog_report(
    backlog_items: Iterable[object],
    *,
    config: ResearchMarketDepthStressBacklogConfig,
    generated_at: datetime,
) -> ResearchMarketDepthStressBacklogReport:
    if type(config) is not ResearchMarketDepthStressBacklogConfig:
        raise ValueError("config must be a ResearchMarketDepthStressBacklogConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_items = _normalize_backlog_items(backlog_items)
    rows = tuple(
        _row_from_item(item, config=config)
        for item in sorted(normalized_items, key=lambda value: value.public_check_id)
    )
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "check_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_depth_stress_pressure": _average_depth_stress_pressure(rows),
        "max_quote_age_seconds": max(
            (row.quote_age_seconds for row in rows),
            default=_ZERO,
        ),
        "max_aggregate_depth_fade": max(
            (row.aggregate_depth_fade for row in rows),
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
    return ResearchMarketDepthStressBacklogReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_market_depth_stress_backlog_report_payload(
    report: ResearchMarketDepthStressBacklogReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketDepthStressBacklogReport:
        raise ValueError("report must be a ResearchMarketDepthStressBacklogReport")
    _require_hard_flags("report", report)
    payload = _json_ready(asdict(report))
    _reject_public_payload("report payload", payload)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _row_from_item(
    item: ResearchMarketDepthStressBacklogInput,
    *,
    config: ResearchMarketDepthStressBacklogConfig,
) -> ResearchMarketDepthStressBacklogRow:
    quote_age_pressure = _quote_age_pressure(item.quote_age_seconds, config=config)
    depth_stress_pressure = _quantize(
        (item.aggregate_depth_fade * config.aggregate_depth_fade_weight)
        + (item.spread_widening * config.spread_widening_weight)
        + (quote_age_pressure * config.quote_age_weight)
        + (item.fee_friction * config.fee_friction_weight)
        + (item.catalyst_pressure * config.catalyst_pressure_weight),
    )
    status = _row_status(depth_stress_pressure, config=config)
    return ResearchMarketDepthStressBacklogRow(
        public_check_id=item.public_check_id,
        aggregate_depth_fade=item.aggregate_depth_fade,
        spread_widening=item.spread_widening,
        quote_age_seconds=item.quote_age_seconds,
        quote_age_pressure=quote_age_pressure,
        fee_friction=item.fee_friction,
        catalyst_pressure=item.catalyst_pressure,
        depth_stress_pressure=depth_stress_pressure,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            aggregate_depth_fade=item.aggregate_depth_fade,
            spread_widening=item.spread_widening,
            quote_age_pressure=quote_age_pressure,
            fee_friction=item.fee_friction,
            catalyst_pressure=item.catalyst_pressure,
            input_reason_codes=item.reason_codes,
        ),
    )


def _normalize_backlog_items(
    backlog_items: Iterable[object],
) -> tuple[ResearchMarketDepthStressBacklogInput, ...]:
    if isinstance(backlog_items, (str, bytes)):
        raise ValueError("backlog_items must be an iterable")
    try:
        values = tuple(backlog_items)
    except TypeError as exc:
        raise ValueError("backlog_items must be an iterable") from exc
    return tuple(_coerce_backlog_item(value) for value in values)


def _coerce_backlog_item(value: object) -> ResearchMarketDepthStressBacklogInput:
    if type(value) is ResearchMarketDepthStressBacklogInput:
        _require_hard_flags("backlog input", value)
        return value
    _require_hard_flags("backlog input", value)
    return ResearchMarketDepthStressBacklogInput(
        public_check_id=_field_value(value, "public_check_id"),
        aggregate_depth_fade=_field_value(value, "aggregate_depth_fade"),
        spread_widening=_field_value(value, "spread_widening"),
        quote_age_seconds=_field_value(value, "quote_age_seconds"),
        fee_friction=_field_value(value, "fee_friction"),
        catalyst_pressure=_field_value(value, "catalyst_pressure"),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _quote_age_pressure(
    quote_age_seconds: Decimal,
    *,
    config: ResearchMarketDepthStressBacklogConfig,
) -> Decimal:
    if quote_age_seconds <= config.fresh_quote_age_seconds:
        return _ZERO
    if quote_age_seconds >= config.stale_quote_age_seconds:
        return _ONE
    age_band = config.stale_quote_age_seconds - config.fresh_quote_age_seconds
    return _quantize((quote_age_seconds - config.fresh_quote_age_seconds) / age_band)


def _row_status(
    depth_stress_pressure: Decimal,
    *,
    config: ResearchMarketDepthStressBacklogConfig,
) -> str:
    if depth_stress_pressure >= config.block_stress_threshold:
        return "block"
    if depth_stress_pressure >= config.watch_stress_threshold:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    aggregate_depth_fade: Decimal,
    spread_widening: Decimal,
    quote_age_pressure: Decimal,
    fee_friction: Decimal,
    catalyst_pressure: Decimal,
    input_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    codes: set[str] = {f"depth_stress_{status}"}
    if aggregate_depth_fade >= Decimal("0.700000"):
        codes.add("aggregate_depth_fade_high")
    elif aggregate_depth_fade >= Decimal("0.300000"):
        codes.add("aggregate_depth_fade_watch")
    else:
        codes.add("aggregate_depth_fade_low")
    if spread_widening >= Decimal("0.700000"):
        codes.add("spread_widening_high")
    elif spread_widening >= Decimal("0.300000"):
        codes.add("spread_widening_watch")
    else:
        codes.add("spread_widening_low")
    if quote_age_pressure == _ONE:
        codes.add("quote_age_stale")
    elif quote_age_pressure > _ZERO:
        codes.add("quote_age_aging")
    else:
        codes.add("quote_age_fresh")
    if fee_friction >= Decimal("0.700000"):
        codes.add("fee_friction_high")
    elif fee_friction >= Decimal("0.250000"):
        codes.add("fee_friction_watch")
    else:
        codes.add("fee_friction_low")
    if catalyst_pressure >= Decimal("0.700000"):
        codes.add("catalyst_pressure_high")
    elif catalyst_pressure >= Decimal("0.350000"):
        codes.add("catalyst_pressure_watch")
    else:
        codes.add("catalyst_pressure_low")
    for reason_code in input_reason_codes:
        codes.add(f"input_{reason_code}")
    return tuple(sorted(codes))


def _report_status(rows: tuple[ResearchMarketDepthStressBacklogRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchMarketDepthStressBacklogRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_depth_stress_backlog_items",)
    if all(row.status == "pass" for row in rows):
        return ("depth_stress_pass",)
    return tuple(sorted({code for row in rows for code in row.reason_codes}))


def _reason_code_counts(
    rows: tuple[ResearchMarketDepthStressBacklogRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchMarketDepthStressBacklogReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketDepthStressBacklogReasonCodeCount(
                reason_code=reason_codes[0],
                count=_ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchMarketDepthStressBacklogReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _average_depth_stress_pressure(
    rows: tuple[ResearchMarketDepthStressBacklogRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(
        sum((row.depth_stress_pressure for row in rows), _ZERO) / Decimal(len(rows)),
    )


def _status_count(
    rows: tuple[ResearchMarketDepthStressBacklogRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_rows(
    rows: tuple[ResearchMarketDepthStressBacklogRow, ...],
) -> tuple[ResearchMarketDepthStressBacklogRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketDepthStressBacklogRow:
            raise ValueError("rows must contain ResearchMarketDepthStressBacklogRow values")
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.public_check_id))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by public_check_id")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchMarketDepthStressBacklogReasonCodeCount, ...],
) -> tuple[ResearchMarketDepthStressBacklogReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchMarketDepthStressBacklogReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketDepthStressBacklogReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row_consistency(row: ResearchMarketDepthStressBacklogRow) -> None:
    if not row.reason_codes:
        raise ValueError("reason_codes must be nonempty")
    if f"depth_stress_{row.status}" not in row.reason_codes:
        raise ValueError("reason_codes must include row status")


def _validate_report_consistency(report: ResearchMarketDepthStressBacklogReport) -> None:
    if report.check_count != _decimal_count(len(report.rows)):
        raise ValueError("check_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_depth_stress_pressure != _average_depth_stress_pressure(report.rows):
        raise ValueError("average_depth_stress_pressure must match rows")
    expected_max_quote_age = max(
        (row.quote_age_seconds for row in report.rows),
        default=_ZERO,
    )
    if report.max_quote_age_seconds != expected_max_quote_age:
        raise ValueError("max_quote_age_seconds must match rows")
    expected_max_depth_fade = max(
        (row.aggregate_depth_fade for row in report.rows),
        default=_ZERO,
    )
    if report.max_aggregate_depth_fade != expected_max_depth_fade:
        raise ValueError("max_aggregate_depth_fade must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    expected_reason_codes = _report_reason_codes(report.rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _report_values_without_digest(
    report: ResearchMarketDepthStressBacklogReport,
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


def _require_public_check_id(name: str, value: str) -> str:
    _require_public_identifier(name, value)
    normalized = value.lower()
    if any(term in normalized for term in _CHECK_ID_UNSAFE_TERMS):
        raise ValueError(f"{name} must not expose raw public surface identifiers")
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
    if value not in _STATUSES:
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
