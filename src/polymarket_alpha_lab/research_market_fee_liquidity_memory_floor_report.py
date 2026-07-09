"""Pure fee and liquidity memory-floor research report."""

from __future__ import annotations

import json
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_CONFIG_VERSION = "fee-liquidity-memory-floor-report-v0"
STATUSES = ("pass", "watch", "block")

PASS_REASON = "cost_floor_pass"
FEE_NEAR_REASON = "fee_near_memory_floor"
FEE_ABOVE_REASON = "fee_above_memory_floor"
LIQUIDITY_BELOW_REASON = "liquidity_below_memory_floor"
SPREAD_ABOVE_REASON = "spread_above_ceiling"
THIN_MEMORY_REASON = "thin_memory_floor"
NO_INPUTS_REASON = "no_inputs"

REASON_CODE_SEQUENCE = (
    PASS_REASON,
    FEE_ABOVE_REASON,
    FEE_NEAR_REASON,
    LIQUIDITY_BELOW_REASON,
    SPREAD_ABOVE_REASON,
    THIN_MEMORY_REASON,
    NO_INPUTS_REASON,
)
BLOCK_REASONS = (FEE_ABOVE_REASON, LIQUIDITY_BELOW_REASON, SPREAD_ABOVE_REASON)

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
RATIO_QUANTUM = Decimal("0.000001")
COUNT_ONE = Decimal("1")

PUBLIC_TEXT_BLOCKLIST = (
    "candidate",
    "market",
    "source",
    "url",
    "text",
    "dsn",
    "table",
    "token",
    "postgresql://",
    "http://",
    "https://",
)

__all__ = (
    "DEFAULT_CONFIG_VERSION",
    "STATUSES",
    "ResearchMarketFeeLiquidityMemoryFloorReportConfig",
    "ResearchMarketFeeLiquidityMemoryFloorInput",
    "ResearchMarketFeeLiquidityMemoryFloorReasonCodeCount",
    "ResearchMarketFeeLiquidityMemoryFloorReport",
    "ResearchMarketFeeLiquidityMemoryFloorRow",
    "build_research_market_fee_liquidity_memory_floor_report",
    "research_market_fee_liquidity_memory_floor_report_payload",
)


@dataclass(frozen=True)
class ResearchMarketFeeLiquidityMemoryFloorReportConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    watch_fee_rate: Decimal = Decimal("0.010000")
    block_fee_rate: Decimal = Decimal("0.020000")
    max_spread_rate: Decimal = Decimal("0.030000")
    min_memory_sample_count: Decimal = Decimal("3")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketFeeLiquidityMemoryFloorReportConfig:
            raise TypeError(
                "ResearchMarketFeeLiquidityMemoryFloorReportConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketFeeLiquidityMemoryFloorReportConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchMarketFeeLiquidityMemoryFloorReportConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be supported")
        object.__setattr__(
            self,
            "watch_fee_rate",
            _require_positive_decimal("watch_fee_rate", self.watch_fee_rate),
        )
        object.__setattr__(
            self,
            "block_fee_rate",
            _require_positive_decimal("block_fee_rate", self.block_fee_rate),
        )
        object.__setattr__(
            self,
            "max_spread_rate",
            _require_positive_decimal("max_spread_rate", self.max_spread_rate),
        )
        object.__setattr__(
            self,
            "min_memory_sample_count",
            _require_positive_whole_decimal(
                "min_memory_sample_count",
                self.min_memory_sample_count,
            ),
        )
        if self.block_fee_rate <= self.watch_fee_rate:
            raise ValueError("block_fee_rate must be greater than watch_fee_rate")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketFeeLiquidityMemoryFloorInput:
    candidate_key: str
    market_key: str
    raw_reference: str
    observed_at: datetime
    fee_rate: Decimal
    liquidity_depth: Decimal
    liquidity_memory_floor: Decimal
    spread_rate: Decimal
    memory_sample_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketFeeLiquidityMemoryFloorInput:
            raise TypeError(
                "ResearchMarketFeeLiquidityMemoryFloorInput "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketFeeLiquidityMemoryFloorInput:
            raise ValueError(
                "input must be exactly ResearchMarketFeeLiquidityMemoryFloorInput",
            )
        _require_canonical_string("candidate_key", self.candidate_key)
        _require_canonical_string("market_key", self.market_key)
        _require_canonical_string("raw_reference", self.raw_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("fee_rate", "liquidity_depth", "spread_rate"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "liquidity_memory_floor",
            _require_positive_decimal(
                "liquidity_memory_floor",
                self.liquidity_memory_floor,
            ),
        )
        object.__setattr__(
            self,
            "memory_sample_count",
            _require_nonnegative_whole_decimal(
                "memory_sample_count",
                self.memory_sample_count,
            ),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchMarketFeeLiquidityMemoryFloorRow:
    identity_digest: str
    evidence_digest: str
    row_status: str
    fee_rate: Decimal
    spread_rate: Decimal
    liquidity_depth: Decimal
    liquidity_memory_floor: Decimal
    liquidity_floor_coverage_ratio: Decimal
    memory_sample_count: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketFeeLiquidityMemoryFloorRow:
            raise TypeError(
                "ResearchMarketFeeLiquidityMemoryFloorRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketFeeLiquidityMemoryFloorRow:
            raise ValueError(
                "row must be exactly ResearchMarketFeeLiquidityMemoryFloorRow",
            )
        _require_digest_token("identity_digest", self.identity_digest)
        _require_digest_token("evidence_digest", self.evidence_digest)
        _require_status("row_status", self.row_status)
        for field_name in (
            "fee_rate",
            "spread_rate",
            "liquidity_depth",
            "liquidity_floor_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _quantize(
                    _require_nonnegative_decimal(field_name, getattr(self, field_name)),
                ),
            )
        object.__setattr__(
            self,
            "liquidity_memory_floor",
            _require_positive_decimal(
                "liquidity_memory_floor",
                _quantize(
                    _require_positive_decimal(
                        "liquidity_memory_floor",
                        self.liquidity_memory_floor,
                    ),
                ),
            ),
        )
        object.__setattr__(
            self,
            "memory_sample_count",
            _require_nonnegative_whole_decimal(
                "memory_sample_count",
                self.memory_sample_count,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchMarketFeeLiquidityMemoryFloorReasonCodeCount:
    reason_code: str
    count: Decimal
    item_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketFeeLiquidityMemoryFloorReasonCodeCount:
            raise TypeError(
                "ResearchMarketFeeLiquidityMemoryFloorReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketFeeLiquidityMemoryFloorReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchMarketFeeLiquidityMemoryFloorReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "item_ratio",
            _quantize(_require_nonnegative_decimal("item_ratio", self.item_ratio)),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketFeeLiquidityMemoryFloorReport:
    generated_at: datetime
    config_version: str
    report_status: str
    item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_fee_rate: Decimal
    average_spread_rate: Decimal
    minimum_liquidity_floor_coverage_ratio: Decimal
    rows: tuple[ResearchMarketFeeLiquidityMemoryFloorRow, ...]
    reason_code_counts: tuple[ResearchMarketFeeLiquidityMemoryFloorReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketFeeLiquidityMemoryFloorReport:
            raise TypeError(
                "ResearchMarketFeeLiquidityMemoryFloorReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketFeeLiquidityMemoryFloorReport:
            raise ValueError(
                "report must be exactly ResearchMarketFeeLiquidityMemoryFloorReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("report_status", self.report_status)
        for field_name in ("item_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_fee_rate",
            "average_spread_rate",
            "minimum_liquidity_floor_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _quantize(
                    _require_nonnegative_decimal(field_name, getattr(self, field_name)),
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
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _require_hex_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        expected = _payload_digest(_payload_from_report(self, include_digest=False))
        if self.derived_validation_digest != expected:
            raise ValueError("derived_validation_digest must match report values")


_PUBLIC_DATACLASS_TYPES = (
    ResearchMarketFeeLiquidityMemoryFloorReportConfig,
    ResearchMarketFeeLiquidityMemoryFloorInput,
    ResearchMarketFeeLiquidityMemoryFloorReasonCodeCount,
    ResearchMarketFeeLiquidityMemoryFloorReport,
    ResearchMarketFeeLiquidityMemoryFloorRow,
)


def build_research_market_fee_liquidity_memory_floor_report(
    input_rows: tuple[object, ...] | list[object],
    *,
    config: ResearchMarketFeeLiquidityMemoryFloorReportConfig,
    generated_at: datetime,
) -> ResearchMarketFeeLiquidityMemoryFloorReport:
    if type(config) is not ResearchMarketFeeLiquidityMemoryFloorReportConfig:
        raise ValueError("config must be exact")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _normalize_input_rows(input_rows, generated_at=generated_at_utc)
    report_rows = tuple(
        sorted(
            (_build_row(row, config=config) for row in rows),
            key=lambda row: row.identity_digest,
        ),
    )
    reason_codes = _report_reason_codes(report_rows)
    report_values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "report_status": _report_status(report_rows),
        "item_count": _decimal_count(len(report_rows)),
        "pass_count": _status_count(report_rows, "pass"),
        "watch_count": _status_count(report_rows, "watch"),
        "block_count": _status_count(report_rows, "block"),
        "average_fee_rate": _average_decimal(tuple(row.fee_rate for row in report_rows)),
        "average_spread_rate": _average_decimal(
            tuple(row.spread_rate for row in report_rows),
        ),
        "minimum_liquidity_floor_coverage_ratio": _minimum_decimal(
            tuple(row.liquidity_floor_coverage_ratio for row in report_rows),
        ),
        "rows": report_rows,
        "reason_code_counts": _reason_code_counts(reason_codes, report_rows),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    report_values["derived_validation_digest"] = _payload_digest(
        _payload_from_mapping(report_values),
    )
    return ResearchMarketFeeLiquidityMemoryFloorReport(**report_values)


def research_market_fee_liquidity_memory_floor_report_payload(
    report: ResearchMarketFeeLiquidityMemoryFloorReport | dict[str, object],
) -> dict[str, object]:
    if type(report) is ResearchMarketFeeLiquidityMemoryFloorReport:
        _revalidate_public_dataclass("report", report)
        payload = _payload_from_report(report, include_digest=True)
        _validate_payload_schema(payload)
        _validate_payload_digest(payload)
        _reject_public_payload_text(payload)
        return payload
    if type(report) is dict:
        payload = dict(report)
        _validate_payload_digest(payload)
        _validate_payload_schema(payload)
        _reject_public_payload_text(payload)
        return payload
    raise ValueError("report must be exact report or dict")


def _build_row(
    row: ResearchMarketFeeLiquidityMemoryFloorInput,
    *,
    config: ResearchMarketFeeLiquidityMemoryFloorReportConfig,
) -> ResearchMarketFeeLiquidityMemoryFloorRow:
    coverage_ratio = _divide_quantized(
        row.liquidity_depth,
        row.liquidity_memory_floor,
    )
    reason_codes = _row_reason_codes(
        fee_rate=row.fee_rate,
        spread_rate=row.spread_rate,
        liquidity_floor_coverage_ratio=coverage_ratio,
        memory_sample_count=row.memory_sample_count,
        config=config,
    )
    return ResearchMarketFeeLiquidityMemoryFloorRow(
        identity_digest=_short_digest(row.candidate_key, row.market_key),
        evidence_digest=_short_digest(row.raw_reference),
        row_status=_row_status(reason_codes),
        fee_rate=_quantize(row.fee_rate),
        spread_rate=_quantize(row.spread_rate),
        liquidity_depth=_quantize(row.liquidity_depth),
        liquidity_memory_floor=_quantize(row.liquidity_memory_floor),
        liquidity_floor_coverage_ratio=coverage_ratio,
        memory_sample_count=row.memory_sample_count,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    fee_rate: Decimal,
    spread_rate: Decimal,
    liquidity_floor_coverage_ratio: Decimal,
    memory_sample_count: Decimal,
    config: ResearchMarketFeeLiquidityMemoryFloorReportConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if fee_rate >= config.block_fee_rate:
        reasons.append(FEE_ABOVE_REASON)
    elif fee_rate >= config.watch_fee_rate:
        reasons.append(FEE_NEAR_REASON)
    if liquidity_floor_coverage_ratio < ONE:
        reasons.append(LIQUIDITY_BELOW_REASON)
    if spread_rate > config.max_spread_rate:
        reasons.append(SPREAD_ABOVE_REASON)
    if memory_sample_count < config.min_memory_sample_count:
        reasons.append(THIN_MEMORY_REASON)
    if not reasons:
        reasons.append(PASS_REASON)
    return _normalize_reason_codes(tuple(reasons), allow_empty=False)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASONS for reason_code in reason_codes):
        return "block"
    if reason_codes == (PASS_REASON,):
        return "pass"
    return "watch"


def _report_reason_codes(
    rows: tuple[ResearchMarketFeeLiquidityMemoryFloorRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    seen = {reason_code for row in rows for reason_code in row.reason_codes}
    return tuple(reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in seen)


def _report_status(rows: tuple[ResearchMarketFeeLiquidityMemoryFloorRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.row_status == "block" for row in rows):
        return "block"
    if any(row.row_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[ResearchMarketFeeLiquidityMemoryFloorRow, ...],
) -> tuple[ResearchMarketFeeLiquidityMemoryFloorReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketFeeLiquidityMemoryFloorReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=COUNT_ONE,
                item_ratio=ZERO,
            ),
        )
    return tuple(
        ResearchMarketFeeLiquidityMemoryFloorReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(
                sum(1 for row in rows if reason_code in row.reason_codes),
            ),
            item_ratio=_ratio(
                _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes)),
                _decimal_count(len(rows)),
            ),
        )
        for reason_code in reason_codes
    )


def _normalize_input_rows(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[ResearchMarketFeeLiquidityMemoryFloorInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("input rows must be list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchMarketFeeLiquidityMemoryFloorInput:
            raise ValueError("input rows must contain exact values")
        _require_hard_flags("input", row)
        if row.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    return rows


def _normalize_rows(
    value: object,
) -> tuple[ResearchMarketFeeLiquidityMemoryFloorRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(value)
    previous: str | None = None
    for row in rows:
        if type(row) is not ResearchMarketFeeLiquidityMemoryFloorRow:
            raise ValueError("rows must contain exact row values")
        _require_hard_flags("row", row)
        if previous is not None:
            if previous == row.identity_digest:
                raise ValueError("rows identity_digest values must be unique")
            if previous > row.identity_digest:
                raise ValueError("rows must follow deterministic sequence")
        previous = row.identity_digest
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchMarketFeeLiquidityMemoryFloorReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    counts = tuple(value)
    previous_index: int | None = None
    for count in counts:
        if type(count) is not ResearchMarketFeeLiquidityMemoryFloorReasonCodeCount:
            raise ValueError("reason_code_counts must contain exact count values")
        _require_hard_flags("reason_code_count", count)
        index = REASON_CODE_SEQUENCE.index(count.reason_code)
        if previous_index is not None:
            if previous_index == index:
                raise ValueError("reason_code_counts must be unique")
            if previous_index > index:
                raise ValueError("reason_code_counts must follow deterministic sequence")
        previous_index = index
    return counts


def _normalize_reason_codes(value: object, *, allow_empty: bool) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized = tuple(value)
    if not allow_empty and not normalized:
        raise ValueError("reason_codes must be nonempty")
    seen: set[str] = set()
    for reason_code in normalized:
        _require_reason_code("reason_codes", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
    canonical = tuple(
        reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in seen
    )
    if normalized != canonical:
        raise ValueError("reason_codes must follow deterministic sequence")
    return normalized


def _payload_from_report(
    report: ResearchMarketFeeLiquidityMemoryFloorReport,
    *,
    include_digest: bool,
) -> dict[str, object]:
    payload = _payload_from_mapping(
        {field.name: getattr(report, field.name) for field in fields(report)},
    )
    if not include_digest:
        payload.pop("derived_validation_digest", None)
    return payload


def _payload_from_mapping(values: dict[str, object]) -> dict[str, object]:
    return {key: _payload_value(item) for key, item in values.items()}


def _payload_value(value: object) -> object:
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError("payload value must be supported")
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is str or type(value) is bool or value is None:
        return value
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    if type(value) is int or type(value) is float:
        raise ValueError("payload numbers must use Decimal strings")
    raise ValueError("payload value must be serializable")


def _payload_digest(payload_without_digest: dict[str, object]) -> str:
    try:
        canonical = json.dumps(
            payload_without_digest,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("payload must use canonical JSON values") from exc
    return sha256(canonical.encode("utf-8")).hexdigest()


def _validate_payload_digest(payload: dict[str, object]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_hex_digest("derived_validation_digest", digest)
    comparable = dict(payload)
    comparable.pop("derived_validation_digest", None)
    if digest != _payload_digest(comparable):
        raise ValueError("derived_validation_digest must match payload values")


def _validate_payload_schema(payload: dict[str, object]) -> None:
    _report_from_payload(payload)


def _report_from_payload(
    payload: dict[str, object],
) -> ResearchMarketFeeLiquidityMemoryFloorReport:
    _require_payload_keys(
        "payload",
        payload,
        tuple(field.name for field in fields(ResearchMarketFeeLiquidityMemoryFloorReport)),
    )
    return ResearchMarketFeeLiquidityMemoryFloorReport(
        generated_at=_payload_datetime("generated_at", payload["generated_at"]),
        config_version=_payload_string("config_version", payload["config_version"]),
        report_status=_payload_string("report_status", payload["report_status"]),
        item_count=_payload_decimal("item_count", payload["item_count"]),
        pass_count=_payload_decimal("pass_count", payload["pass_count"]),
        watch_count=_payload_decimal("watch_count", payload["watch_count"]),
        block_count=_payload_decimal("block_count", payload["block_count"]),
        average_fee_rate=_payload_decimal(
            "average_fee_rate",
            payload["average_fee_rate"],
        ),
        average_spread_rate=_payload_decimal(
            "average_spread_rate",
            payload["average_spread_rate"],
        ),
        minimum_liquidity_floor_coverage_ratio=_payload_decimal(
            "minimum_liquidity_floor_coverage_ratio",
            payload["minimum_liquidity_floor_coverage_ratio"],
        ),
        rows=tuple(_row_from_payload(item) for item in _payload_list("rows", payload["rows"])),
        reason_code_counts=tuple(
            _reason_code_count_from_payload(item)
            for item in _payload_list("reason_code_counts", payload["reason_code_counts"])
        ),
        reason_codes=tuple(
            _payload_string("reason_codes", item)
            for item in _payload_list("reason_codes", payload["reason_codes"])
        ),
        derived_validation_digest=_payload_string(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_payload_true("paper_only", payload["paper_only"]),
        report_only=_payload_true("report_only", payload["report_only"]),
        readonly=_payload_true("readonly", payload["readonly"]),
    )


def _row_from_payload(value: object) -> ResearchMarketFeeLiquidityMemoryFloorRow:
    payload = _payload_mapping("rows", value)
    _require_payload_keys(
        "row",
        payload,
        tuple(field.name for field in fields(ResearchMarketFeeLiquidityMemoryFloorRow)),
    )
    return ResearchMarketFeeLiquidityMemoryFloorRow(
        identity_digest=_payload_string("identity_digest", payload["identity_digest"]),
        evidence_digest=_payload_string("evidence_digest", payload["evidence_digest"]),
        row_status=_payload_string("row_status", payload["row_status"]),
        fee_rate=_payload_decimal("fee_rate", payload["fee_rate"]),
        spread_rate=_payload_decimal("spread_rate", payload["spread_rate"]),
        liquidity_depth=_payload_decimal("liquidity_depth", payload["liquidity_depth"]),
        liquidity_memory_floor=_payload_decimal(
            "liquidity_memory_floor",
            payload["liquidity_memory_floor"],
        ),
        liquidity_floor_coverage_ratio=_payload_decimal(
            "liquidity_floor_coverage_ratio",
            payload["liquidity_floor_coverage_ratio"],
        ),
        memory_sample_count=_payload_decimal(
            "memory_sample_count",
            payload["memory_sample_count"],
        ),
        reason_codes=tuple(
            _payload_string("reason_codes", item)
            for item in _payload_list("reason_codes", payload["reason_codes"])
        ),
        paper_only=_payload_true("paper_only", payload["paper_only"]),
        report_only=_payload_true("report_only", payload["report_only"]),
        readonly=_payload_true("readonly", payload["readonly"]),
    )


def _reason_code_count_from_payload(
    value: object,
) -> ResearchMarketFeeLiquidityMemoryFloorReasonCodeCount:
    payload = _payload_mapping("reason_code_counts", value)
    _require_payload_keys(
        "reason_code_count",
        payload,
        tuple(
            field.name
            for field in fields(ResearchMarketFeeLiquidityMemoryFloorReasonCodeCount)
        ),
    )
    return ResearchMarketFeeLiquidityMemoryFloorReasonCodeCount(
        reason_code=_payload_string("reason_code", payload["reason_code"]),
        count=_payload_decimal("count", payload["count"]),
        item_ratio=_payload_decimal("item_ratio", payload["item_ratio"]),
        paper_only=_payload_true("paper_only", payload["paper_only"]),
        report_only=_payload_true("report_only", payload["report_only"]),
        readonly=_payload_true("readonly", payload["readonly"]),
    )


def _require_payload_keys(
    field_name: str,
    value: dict[str, object],
    expected: tuple[str, ...],
) -> None:
    if set(value) != set(expected):
        raise ValueError(f"{field_name} keys must match payload schema")


def _payload_mapping(field_name: str, value: object) -> dict[str, object]:
    if type(value) is not dict:
        raise ValueError(f"{field_name} must be a payload object")
    if not all(type(key) is str for key in value):
        raise ValueError(f"{field_name} keys must be strings")
    return value


def _payload_list(field_name: str, value: object) -> list[object]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a payload list")
    return value


def _payload_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _payload_true(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return value


def _payload_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must use canonical Decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must use canonical Decimal string") from exc
    parsed = _require_decimal(field_name, parsed)
    if parsed.is_zero() and parsed.is_signed():
        raise ValueError(f"{field_name} must use canonical Decimal string")
    if field_name == "count" or field_name.endswith("_count"):
        normalized = _require_nonnegative_whole_decimal(field_name, parsed)
    else:
        normalized = _quantize(_require_nonnegative_decimal(field_name, parsed))
    if value != str(normalized):
        raise ValueError(f"{field_name} must use canonical Decimal string")
    return normalized


def _payload_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be datetime string") from exc
    normalized = _as_utc(field_name, parsed)
    if value != normalized.isoformat():
        raise ValueError(f"{field_name} must be canonical UTC datetime string")
    return normalized


def _reject_public_payload_text(value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _reject_blocked_public_text(key)
            _reject_public_payload_text(item)
        return
    if type(value) is list:
        for item in value:
            _reject_public_payload_text(item)
        return
    if type(value) is str:
        _reject_blocked_public_text(value)


def _reject_blocked_public_text(value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in PUBLIC_TEXT_BLOCKLIST):
        raise ValueError("payload contains blocked public text")


def _revalidate_public_dataclass(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{label} must be supported")
        _require_hard_flags(label, value)
        for field in fields(value):
            _revalidate_public_dataclass(field.name, getattr(value, field.name))
        type(value)(**{field.name: getattr(value, field.name) for field in fields(value)})
        return
    if type(value) is tuple:
        for item in value:
            _revalidate_public_dataclass(label, item)


def _validate_row_consistency(row: ResearchMarketFeeLiquidityMemoryFloorRow) -> None:
    if PASS_REASON in row.reason_codes and row.reason_codes != (PASS_REASON,):
        raise ValueError("pass reason_codes must stand alone in a row")
    if NO_INPUTS_REASON in row.reason_codes:
        raise ValueError("row reason_codes cannot contain no_inputs")
    if row.row_status != _row_status(row.reason_codes):
        raise ValueError("row_status must match reason_codes")
    if row.row_status == "pass" and row.reason_codes != (PASS_REASON,):
        raise ValueError("row_status pass requires pass reason")
    if row.row_status == "block" and not any(
        reason_code in BLOCK_REASONS for reason_code in row.reason_codes
    ):
        raise ValueError("row_status block requires block reason")
    if row.row_status == "watch" and row.reason_codes == (PASS_REASON,):
        raise ValueError("row_status watch requires watch reason")


def _validate_report_consistency(
    report: ResearchMarketFeeLiquidityMemoryFloorReport,
) -> None:
    if report.item_count != _decimal_count(len(report.rows)):
        raise ValueError("item_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.average_fee_rate != _average_decimal(tuple(row.fee_rate for row in report.rows)):
        raise ValueError("average_fee_rate must match rows")
    if report.average_spread_rate != _average_decimal(
        tuple(row.spread_rate for row in report.rows),
    ):
        raise ValueError("average_spread_rate must match rows")
    if report.minimum_liquidity_floor_coverage_ratio != _minimum_decimal(
        tuple(row.liquidity_floor_coverage_ratio for row in report.rows),
    ):
        raise ValueError("minimum_liquidity_floor_coverage_ratio must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, report.rows):
        raise ValueError("reason_code_counts must match rows")


def _status_count(
    rows: tuple[ResearchMarketFeeLiquidityMemoryFloorRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.row_status == status))


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _divide_quantized(_sum_decimals(values), Decimal(len(values)))


def _minimum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(min(values))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _divide_quantized(numerator, denominator)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value)


def _short_digest(*parts: str) -> str:
    joined = "\x1f".join(parts)
    return "sha256:" + sha256(joined.encode("utf-8")).hexdigest()[:16]


def _quantize(value: Decimal) -> Decimal:
    integer_digits = max(value.adjusted() + 1, 1)
    with localcontext() as context:
        context.prec = max(32, integer_digits + 16)
        context.rounding = ROUND_HALF_EVEN
        return value.quantize(RATIO_QUANTUM, rounding=ROUND_HALF_EVEN)


def _divide_quantized(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        raise ValueError("denominator must be nonzero")
    integer_digits = max(numerator.adjusted() - denominator.adjusted() + 1, 1)
    with localcontext() as context:
        context.prec = max(32, integer_digits + 16)
        context.rounding = ROUND_HALF_EVEN
        return _quantize(numerator / denominator)


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    integer_digits = max(max(value.adjusted() + 1, 1) for value in values)
    fractional_digits = max(max(-value.as_tuple().exponent, 0) for value in values)
    count_digits = len(str(len(values)))
    with localcontext() as context:
        context.prec = max(
            32,
            integer_digits + fractional_digits + count_digits + 8,
        )
        context.rounding = ROUND_HALF_EVEN
        return sum(values, ZERO)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized.is_zero():
        return ZERO
    return normalized


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized.to_integral_value()


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized.to_integral_value()


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty string")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be supported")


def _require_digest_token(field_name: str, value: object) -> None:
    if type(value) is not str or not value.startswith("sha256:") or len(value) != 23:
        raise ValueError(f"{field_name} must be redacted digest")
    suffix = value.removeprefix("sha256:")
    if suffix != suffix.lower():
        raise ValueError(f"{field_name} must be redacted digest")
    try:
        int(suffix, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be redacted digest") from exc


def _require_hex_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64 or value != value.lower():
        raise ValueError(f"{field_name} must be sha256 hex")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be sha256 hex") from exc


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")
