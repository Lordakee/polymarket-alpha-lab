"""Readonly transaction-cost threshold report for manual research review."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_STRATEGY_TRANSACTION_COST_THRESHOLD_CONFIG_VERSION = (
    "research-strategy-transaction-cost-threshold-report"
)

_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_SIX = Decimal("0.000001")
_ZERO = Decimal("0.000000")

_STATUS_PASS = "pass"
_STATUS_WATCH = "watch"
_STATUS_BLOCK = "block"
_STATUSES = (_STATUS_PASS, _STATUS_WATCH, _STATUS_BLOCK)

_ROW_REASON_CODES = (
    "total_cost_pass",
    "total_cost_watch",
    "total_cost_block",
    "component_cost_watch",
    "component_cost_block",
    "spread_cost_present",
    "taker_fee_present",
    "gas_friction_present",
    "deposit_friction_present",
    "settlement_friction_present",
)
_REPORT_REASON_CODES = (
    "threshold_report_pass",
    "threshold_report_watch",
    "threshold_report_block",
    "threshold_report_empty",
)
_UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "candidate",
    "market",
    "slug",
    "question",
    "source",
    "http://",
    "https://",
    "://",
    "dsn",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "private",
    "key",
    "buy",
    "sell",
    "recommend",
    "position",
)

__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_TRANSACTION_COST_THRESHOLD_CONFIG_VERSION",
    "ResearchStrategyTransactionCostThresholdConfig",
    "ResearchStrategyTransactionCostThresholdInput",
    "ResearchStrategyTransactionCostThresholdRow",
    "ResearchStrategyTransactionCostThresholdReport",
    "build_research_strategy_transaction_cost_threshold_report",
    "research_strategy_transaction_cost_threshold_report_payload",
    "validate_research_strategy_transaction_cost_threshold_report_payload",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls.__bases__ != (_FinalPublicDataclass,):
            raise TypeError("public dataclasses do not support subclassing")
        if not cls.__name__.startswith("ResearchStrategyTransactionCostThreshold"):
            raise TypeError("public dataclasses do not support subclassing")


@dataclass(frozen=True)
class ResearchStrategyTransactionCostThresholdConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_RESEARCH_STRATEGY_TRANSACTION_COST_THRESHOLD_CONFIG_VERSION
    watch_total_cost_threshold: Decimal = Decimal("0.030000")
    block_total_cost_threshold: Decimal = Decimal("0.080000")
    watch_component_cost_threshold: Decimal = Decimal("0.020000")
    block_component_cost_threshold: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyTransactionCostThresholdConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        for field_name in (
            "watch_total_cost_threshold",
            "block_total_cost_threshold",
            "watch_component_cost_threshold",
            "block_component_cost_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_total_cost_threshold <= self.watch_total_cost_threshold:
            raise ValueError("block_total_cost_threshold must exceed watch_total_cost_threshold")
        if self.block_component_cost_threshold <= self.watch_component_cost_threshold:
            raise ValueError(
                "block_component_cost_threshold must exceed watch_component_cost_threshold",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", _payload_value(self))


@dataclass(frozen=True)
class ResearchStrategyTransactionCostThresholdInput(_FinalPublicDataclass):
    review_label: str
    spread_cost: Decimal
    taker_fee_cost: Decimal
    gas_friction_cost: Decimal
    deposit_friction_cost: Decimal
    settlement_friction_cost: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyTransactionCostThresholdInput, "input")
        object.__setattr__(
            self,
            "review_label",
            _require_public_string("review_label", self.review_label),
        )
        for field_name in (
            "spread_cost",
            "taker_fee_cost",
            "gas_friction_cost",
            "deposit_friction_cost",
            "settlement_friction_cost",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", _payload_value(self))


@dataclass(frozen=True)
class ResearchStrategyTransactionCostThresholdRow(_FinalPublicDataclass):
    review_rank: Decimal
    review_label: str
    spread_cost: Decimal
    taker_fee_cost: Decimal
    gas_friction_cost: Decimal
    deposit_friction_cost: Decimal
    settlement_friction_cost: Decimal
    total_cost: Decimal
    max_component_cost: Decimal
    threshold_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyTransactionCostThresholdRow, "row")
        object.__setattr__(self, "review_rank", _require_positive_decimal("review_rank", self.review_rank))
        object.__setattr__(
            self,
            "review_label",
            _require_public_string("review_label", self.review_label),
        )
        for field_name in (
            "spread_cost",
            "taker_fee_cost",
            "gas_friction_cost",
            "deposit_friction_cost",
            "settlement_friction_cost",
            "total_cost",
            "max_component_cost",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("threshold_status", self.threshold_status)
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes, _ROW_REASON_CODES),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", _payload_value(self))
        _validate_row(self)


@dataclass(frozen=True)
class ResearchStrategyTransactionCostThresholdReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    watch_total_cost_threshold: Decimal
    block_total_cost_threshold: Decimal
    watch_component_cost_threshold: Decimal
    block_component_cost_threshold: Decimal
    threshold_status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_total_cost: Decimal
    max_total_cost: Decimal
    max_component_cost: Decimal
    rows: tuple[ResearchStrategyTransactionCostThresholdRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyTransactionCostThresholdReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        for field_name in (
            "watch_total_cost_threshold",
            "block_total_cost_threshold",
            "watch_component_cost_threshold",
            "block_component_cost_threshold",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "average_total_cost",
            "max_total_cost",
            "max_component_cost",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("threshold_status", self.threshold_status)
        object.__setattr__(self, "rows", _require_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes, _REPORT_REASON_CODES),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", _payload_value(self))
        _validate_report(self)
        _require_matching_digest(_payload_value(self))


def build_research_strategy_transaction_cost_threshold_report(
    inputs: Iterable[ResearchStrategyTransactionCostThresholdInput],
    *,
    config: ResearchStrategyTransactionCostThresholdConfig | None = None,
    generated_at: datetime,
) -> ResearchStrategyTransactionCostThresholdReport:
    cfg = config or ResearchStrategyTransactionCostThresholdConfig()
    if type(cfg) is not ResearchStrategyTransactionCostThresholdConfig:
        raise ValueError(
            "config must be exactly ResearchStrategyTransactionCostThresholdConfig",
        )
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_inputs(inputs)
    rows = tuple(
        _row_for_input(review_rank=index, value=value, config=cfg)
        for index, value in enumerate(_sorted_inputs(normalized), start=1)
    )
    status = _report_status(rows)
    values: dict[str, Any] = {
        "generated_at": generated_at_utc,
        "config_version": cfg.config_version,
        "watch_total_cost_threshold": cfg.watch_total_cost_threshold,
        "block_total_cost_threshold": cfg.block_total_cost_threshold,
        "watch_component_cost_threshold": cfg.watch_component_cost_threshold,
        "block_component_cost_threshold": cfg.block_component_cost_threshold,
        "threshold_status": status,
        "row_count": _count_decimal(len(rows)),
        "pass_count": _status_count(rows, _STATUS_PASS),
        "watch_count": _status_count(rows, _STATUS_WATCH),
        "block_count": _status_count(rows, _STATUS_BLOCK),
        "average_total_cost": _average(row.total_cost for row in rows),
        "max_total_cost": max((row.total_cost for row in rows), default=_ZERO),
        "max_component_cost": max((row.max_component_cost for row in rows), default=_ZERO),
        "rows": rows,
        "reason_codes": _report_reason_codes(status, rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    payload = _payload_value(values)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    values["derived_validation_digest"] = _derived_validation_digest(payload)
    return ResearchStrategyTransactionCostThresholdReport(**values)


def research_strategy_transaction_cost_threshold_report_payload(
    report: ResearchStrategyTransactionCostThresholdReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyTransactionCostThresholdReport:
        raise ValueError(
            "report must be exactly ResearchStrategyTransactionCostThresholdReport",
        )
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("payload", payload)
    _require_matching_digest(payload)
    return payload


def validate_research_strategy_transaction_cost_threshold_report_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    _reject_unsafe_public_payload("payload", payload)
    _require_payload_hard_flags(payload)
    _require_matching_digest(payload)
    return True


def _row_for_input(
    *,
    review_rank: int,
    value: ResearchStrategyTransactionCostThresholdInput,
    config: ResearchStrategyTransactionCostThresholdConfig,
) -> ResearchStrategyTransactionCostThresholdRow:
    components = (
        value.spread_cost,
        value.taker_fee_cost,
        value.gas_friction_cost,
        value.deposit_friction_cost,
        value.settlement_friction_cost,
    )
    total_cost = _sum_decimals(components)
    max_component_cost = max(components, default=_ZERO)
    status = _threshold_status(total_cost, max_component_cost, config)
    return ResearchStrategyTransactionCostThresholdRow(
        review_rank=_count_decimal(review_rank),
        review_label=value.review_label,
        spread_cost=value.spread_cost,
        taker_fee_cost=value.taker_fee_cost,
        gas_friction_cost=value.gas_friction_cost,
        deposit_friction_cost=value.deposit_friction_cost,
        settlement_friction_cost=value.settlement_friction_cost,
        total_cost=total_cost,
        max_component_cost=max_component_cost,
        threshold_status=status,
        reason_codes=_row_reason_codes(value, total_cost, max_component_cost, status, config),
    )


def _threshold_status(
    total_cost: Decimal,
    max_component_cost: Decimal,
    config: ResearchStrategyTransactionCostThresholdConfig,
) -> str:
    if (
        total_cost >= config.block_total_cost_threshold
        or max_component_cost >= config.block_component_cost_threshold
    ):
        return _STATUS_BLOCK
    if (
        total_cost >= config.watch_total_cost_threshold
        or max_component_cost >= config.watch_component_cost_threshold
    ):
        return _STATUS_WATCH
    return _STATUS_PASS


def _row_reason_codes(
    value: ResearchStrategyTransactionCostThresholdInput,
    total_cost: Decimal,
    max_component_cost: Decimal,
    status: str,
    config: ResearchStrategyTransactionCostThresholdConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if max_component_cost >= config.block_component_cost_threshold:
        reason_codes.append("component_cost_block")
    elif max_component_cost >= config.watch_component_cost_threshold:
        reason_codes.append("component_cost_watch")
    if total_cost >= config.block_total_cost_threshold:
        reason_codes.append("total_cost_block")
    elif total_cost >= config.watch_total_cost_threshold:
        reason_codes.append("total_cost_watch")
    elif status == _STATUS_PASS:
        reason_codes.append("total_cost_pass")
    if status != _STATUS_PASS:
        if value.spread_cost > _ZERO:
            reason_codes.append("spread_cost_present")
        if value.taker_fee_cost > _ZERO:
            reason_codes.append("taker_fee_present")
        if value.gas_friction_cost > _ZERO:
            reason_codes.append("gas_friction_present")
        if value.deposit_friction_cost > _ZERO:
            reason_codes.append("deposit_friction_present")
        if value.settlement_friction_cost > _ZERO:
            reason_codes.append("settlement_friction_present")
    return _require_reason_codes("reason_codes", tuple(reason_codes), _ROW_REASON_CODES)


def _normalize_inputs(
    inputs: Iterable[ResearchStrategyTransactionCostThresholdInput],
) -> tuple[ResearchStrategyTransactionCostThresholdInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Iterable):
        raise ValueError("inputs must be an iterable")
    normalized = tuple(inputs)
    seen: set[str] = set()
    for value in normalized:
        if type(value) is not ResearchStrategyTransactionCostThresholdInput:
            raise ValueError(
                "inputs must contain ResearchStrategyTransactionCostThresholdInput",
            )
        _require_hard_flags("input", value)
        if value.review_label in seen:
            raise ValueError("review_label must be unique")
        seen.add(value.review_label)
    return normalized


def _sorted_inputs(
    inputs: tuple[ResearchStrategyTransactionCostThresholdInput, ...],
) -> tuple[ResearchStrategyTransactionCostThresholdInput, ...]:
    return tuple(sorted(inputs, key=lambda item: item.review_label))


def _require_rows(
    rows: Iterable[ResearchStrategyTransactionCostThresholdRow],
) -> tuple[ResearchStrategyTransactionCostThresholdRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchStrategyTransactionCostThresholdRow:
            raise ValueError("rows must contain ResearchStrategyTransactionCostThresholdRow")
        _require_hard_flags("row", row)
    return tuple(sorted(normalized, key=lambda item: (item.review_rank, item.review_label)))


def _validate_row(row: ResearchStrategyTransactionCostThresholdRow) -> None:
    expected_total = _sum_decimals(
        (
            row.spread_cost,
            row.taker_fee_cost,
            row.gas_friction_cost,
            row.deposit_friction_cost,
            row.settlement_friction_cost,
        ),
    )
    if row.total_cost != expected_total:
        raise ValueError("total_cost must match component costs")
    expected_max = max(
        (
            row.spread_cost,
            row.taker_fee_cost,
            row.gas_friction_cost,
            row.deposit_friction_cost,
            row.settlement_friction_cost,
        ),
        default=_ZERO,
    )
    if row.max_component_cost != expected_max:
        raise ValueError("max_component_cost must match component costs")
    if row.threshold_status == _STATUS_PASS and "total_cost_pass" not in row.reason_codes:
        raise ValueError("threshold_status must match reason_codes")
    if row.threshold_status == _STATUS_WATCH and not any(
        reason_code.endswith("_watch") for reason_code in row.reason_codes
    ):
        raise ValueError("threshold_status must match reason_codes")
    if row.threshold_status == _STATUS_BLOCK and not any(
        reason_code.endswith("_block") for reason_code in row.reason_codes
    ):
        raise ValueError("threshold_status must match reason_codes")


def _validate_report(report: ResearchStrategyTransactionCostThresholdReport) -> None:
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count + report.watch_count + report.block_count != report.row_count:
        raise ValueError("status counts must match row_count")
    if report.pass_count != _status_count(report.rows, _STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, _STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, _STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.average_total_cost != _average(row.total_cost for row in report.rows):
        raise ValueError("average_total_cost must match rows")
    if report.max_total_cost != max((row.total_cost for row in report.rows), default=_ZERO):
        raise ValueError("max_total_cost must match rows")
    if report.max_component_cost != max(
        (row.max_component_cost for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_component_cost must match rows")
    if report.threshold_status != _report_status(report.rows):
        raise ValueError("threshold_status must match rows")
    if report.reason_codes != _report_reason_codes(report.threshold_status, report.rows):
        raise ValueError("reason_codes must match rows")


def _report_status(rows: tuple[ResearchStrategyTransactionCostThresholdRow, ...]) -> str:
    if any(row.threshold_status == _STATUS_BLOCK for row in rows):
        return _STATUS_BLOCK
    if any(row.threshold_status == _STATUS_WATCH for row in rows):
        return _STATUS_WATCH
    return _STATUS_PASS


def _report_reason_codes(
    status: str,
    rows: tuple[ResearchStrategyTransactionCostThresholdRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("threshold_report_empty",)
    if status == _STATUS_BLOCK:
        return ("threshold_report_block",)
    if status == _STATUS_WATCH:
        return ("threshold_report_watch",)
    return ("threshold_report_pass",)


def _status_count(
    rows: tuple[ResearchStrategyTransactionCostThresholdRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.threshold_status == status))


def _average(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return _ZERO
    return _six(_sum_decimals(normalized) / _count_decimal(len(normalized)))


def _sum_decimals(values: Iterable[Decimal]) -> Decimal:
    total = _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        for value in values:
            total += value
    return _six(total)


def _count_decimal(value: int) -> Decimal:
    return _six(Decimal(value))


def _payload_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(_six(value))
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple | list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            ready[key] = _payload_value(item)
        return ready
    if type(value) in (int, float):
        raise ValueError("public payload must use Decimal strings")
    if type(value) is str:
        _require_safe_public_text("public payload value", value)
    return value


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            _require_safe_public_text(f"{label} key", key)
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"payload {key} must be True")
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    if isinstance(value, list | tuple):
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    if type(value) is str:
        _require_safe_public_text(path or label, value)
        return
    if type(value) in (int, float):
        raise ValueError("public payload must use Decimal strings")
    if value is None or type(value) is bool:
        return


def _require_payload_hard_flags(payload: dict[str, Any]) -> None:
    for key in ("paper_only", "report_only", "readonly"):
        if payload.get(key) is not True:
            raise ValueError(f"payload {key} must be True")


def _derived_validation_digest(payload: dict[str, Any]) -> str:
    material = {
        key: value
        for key, value in payload.items()
        if key != "derived_validation_digest"
    }
    return sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()


def _require_matching_digest(payload: dict[str, Any]) -> None:
    if "derived_validation_digest" not in payload:
        raise ValueError("derived_validation_digest is required")
    _require_digest("derived_validation_digest", payload["derived_validation_digest"])
    if payload["derived_validation_digest"] != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest does not match report payload")


def _require_digest(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a sha256 hex digest")


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_public_string(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value:
        raise ValueError(f"{name} must be non-empty")
    if value.strip() != value:
        raise ValueError(f"{name} must be canonical")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{name} must be canonical")
    _require_safe_public_text(name, value)
    return value


def _require_safe_public_text(name: str, value: str) -> None:
    lower = value.lower()
    if any(fragment in lower for fragment in _UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{name} contains unsafe public surface")


def _require_status(name: str, value: object) -> None:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{name} must be one of {_STATUSES}")


def _require_reason_codes(
    name: str,
    values: Iterable[str],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError(f"{name} must be an iterable")
    normalized = tuple(values)
    if not normalized:
        raise ValueError(f"{name} must not be empty")
    for value in normalized:
        if type(value) is not str or value not in allowed:
            raise ValueError(f"{name} must contain known reason codes")
    return normalized


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_nonnegative_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return decimal_value


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _six(value)


def _six(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_SIX)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)
