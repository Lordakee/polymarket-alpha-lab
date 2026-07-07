"""Paper-only fee and friction reconciliation for human research filters."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any


DEFAULT_RESEARCH_FEE_COST_RECONCILIATION_CONFIG_VERSION = (
    "research-fee-cost-reconciliation-v0"
)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"
STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCK_STATUS)

_PASS_REASON = "fee_cost_reconciliation_pass"
_ZERO_REASON = "zero_fee_cost_reconciliation"
_MISSING_NOTIONAL_REASON = "missing_expected_notional_for_positive_cost"
_MISSING_RESEARCH_UNITS_REASON = "missing_expected_research_units_for_positive_cost"
_COST_PER_UNIT_BLOCK_REASON = "cost_per_research_unit_above_block"
_TOTAL_SHARE_BLOCK_REASON = "total_cost_share_above_block"
_COST_PER_UNIT_WATCH_REASON = "cost_per_research_unit_above_watch"
_TOTAL_SHARE_WATCH_REASON = "total_cost_share_above_watch"

_REASON_CODE_ORDER = (
    _PASS_REASON,
    _ZERO_REASON,
    _MISSING_NOTIONAL_REASON,
    _MISSING_RESEARCH_UNITS_REASON,
    _COST_PER_UNIT_BLOCK_REASON,
    _TOTAL_SHARE_BLOCK_REASON,
    _COST_PER_UNIT_WATCH_REASON,
    _TOTAL_SHARE_WATCH_REASON,
)
_REASON_CODES = frozenset(_REASON_CODE_ORDER)

_UNSAFE_PUBLIC_FRAGMENTS = (
    "raw_candidate_id",
    "candidate_id",
    "candidate id",
    "market_id",
    "market id",
    "market_slug",
    "market slug",
    "question",
    "source_ref",
    "source ref",
    "source_url",
    "source url",
    "source_text",
    "source text",
    "http://",
    "https://",
    "dsn",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "position",
    "buy",
    "sell",
    "recommendation",
)


@dataclass(frozen=True)
class ResearchFeeCostReconciliationConfig:
    config_version: str = DEFAULT_RESEARCH_FEE_COST_RECONCILIATION_CONFIG_VERSION
    watch_total_cost_share: Decimal = Decimal("0.020000")
    block_total_cost_share: Decimal = Decimal("0.050000")
    watch_cost_per_research_unit: Decimal = Decimal("2.000000")
    block_cost_per_research_unit: Decimal = Decimal("5.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchFeeCostReconciliationConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        if self.config_version != DEFAULT_RESEARCH_FEE_COST_RECONCILIATION_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_total_cost_share",
            "block_total_cost_share",
            "watch_cost_per_research_unit",
            "block_cost_per_research_unit",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_total_cost_share > self.block_total_cost_share:
            raise ValueError("watch_total_cost_share must not exceed block_total_cost_share")
        if self.watch_cost_per_research_unit > self.block_cost_per_research_unit:
            raise ValueError(
                "watch_cost_per_research_unit must not exceed "
                "block_cost_per_research_unit",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchFeeCostReconciliationInput:
    research_case_label: str
    expected_notional: Decimal
    expected_research_units: Decimal
    taker_fee_rate: Decimal
    spread_cost_rate: Decimal
    deposit_cost: Decimal
    settlement_cost: Decimal
    slippage_expected_cost: Decimal
    slippage_worst_case_cost: Decimal
    slippage_observation_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchFeeCostReconciliationInput, "input")
        object.__setattr__(
            self,
            "research_case_label",
            _require_canonical_string("research_case_label", self.research_case_label),
        )
        for field_name in (
            "expected_notional",
            "expected_research_units",
            "taker_fee_rate",
            "spread_cost_rate",
            "deposit_cost",
            "settlement_cost",
            "slippage_expected_cost",
            "slippage_worst_case_cost",
            "slippage_observation_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.slippage_worst_case_cost < self.slippage_expected_cost:
            raise ValueError(
                "slippage_worst_case_cost must be greater than or equal to "
                "slippage_expected_cost",
            )
        if self.slippage_observation_count != _quantize(self.slippage_observation_count):
            raise ValueError("slippage_observation_count must align to decimal quantum")
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchFeeCostReconciliationReport:
    generated_at: datetime
    config_version: str
    research_case_label: str
    expected_notional: Decimal
    expected_research_units: Decimal
    taker_fee_rate: Decimal
    spread_cost_rate: Decimal
    taker_fee_cost: Decimal
    spread_cost: Decimal
    deposit_cost: Decimal
    settlement_cost: Decimal
    deposit_settlement_cost: Decimal
    slippage_expected_cost: Decimal
    slippage_worst_case_cost: Decimal
    slippage_observation_count: Decimal
    total_cost: Decimal
    total_cost_share: Decimal | None
    cost_per_research_unit: Decimal | None
    status: str
    reason_codes: tuple[str, ...]
    cost_explanation: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchFeeCostReconciliationReport, "report")
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        object.__setattr__(
            self,
            "research_case_label",
            _require_canonical_string("research_case_label", self.research_case_label),
        )
        for field_name in (
            "expected_notional",
            "expected_research_units",
            "taker_fee_rate",
            "spread_cost_rate",
            "taker_fee_cost",
            "spread_cost",
            "deposit_cost",
            "settlement_cost",
            "deposit_settlement_cost",
            "slippage_expected_cost",
            "slippage_worst_case_cost",
            "slippage_observation_count",
            "total_cost",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "total_cost_share",
            _normalize_optional_nonnegative_decimal(
                "total_cost_share",
                self.total_cost_share,
            ),
        )
        object.__setattr__(
            self,
            "cost_per_research_unit",
            _normalize_optional_nonnegative_decimal(
                "cost_per_research_unit",
                self.cost_per_research_unit,
            ),
        )
        if self.status not in STATUSES:
            raise ValueError("status must be pass, watch, or block")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "cost_explanation",
            _normalize_public_text_tuple("cost_explanation", self.cost_explanation),
        )
        _require_sha256("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        if self.derived_validation_digest != _digest_for_payload(
            _payload_without_digest(self),
        ):
            raise ValueError("derived_validation_digest must match report payload")
        _reject_unsafe_public_payload("report", self)


def build_research_fee_cost_reconciliation_report(
    value: ResearchFeeCostReconciliationInput,
    *,
    config: ResearchFeeCostReconciliationConfig,
    generated_at: datetime,
) -> ResearchFeeCostReconciliationReport:
    if type(value) is not ResearchFeeCostReconciliationInput:
        raise ValueError("value must be a ResearchFeeCostReconciliationInput")
    if type(config) is not ResearchFeeCostReconciliationConfig:
        raise ValueError("config must be a ResearchFeeCostReconciliationConfig")
    _require_hard_flags("input", value)
    _require_hard_flags("config", config)

    generated_at_utc = _as_utc("generated_at", generated_at)
    taker_fee_cost = _quantize(value.expected_notional * value.taker_fee_rate)
    spread_cost = _quantize(value.expected_notional * value.spread_cost_rate)
    deposit_settlement_cost = _quantize(value.deposit_cost + value.settlement_cost)
    total_cost = _quantize(
        taker_fee_cost
        + spread_cost
        + deposit_settlement_cost
        + value.slippage_expected_cost,
    )
    total_cost_share = _optional_ratio(total_cost, value.expected_notional)
    cost_per_research_unit = _optional_ratio(total_cost, value.expected_research_units)
    status, reason_codes = _status_and_reason_codes(
        total_cost=total_cost,
        total_cost_share=total_cost_share,
        cost_per_research_unit=cost_per_research_unit,
        expected_notional=value.expected_notional,
        expected_research_units=value.expected_research_units,
        config=config,
    )
    report_values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "research_case_label": value.research_case_label,
        "expected_notional": value.expected_notional,
        "expected_research_units": value.expected_research_units,
        "taker_fee_rate": value.taker_fee_rate,
        "spread_cost_rate": value.spread_cost_rate,
        "taker_fee_cost": taker_fee_cost,
        "spread_cost": spread_cost,
        "deposit_cost": value.deposit_cost,
        "settlement_cost": value.settlement_cost,
        "deposit_settlement_cost": deposit_settlement_cost,
        "slippage_expected_cost": value.slippage_expected_cost,
        "slippage_worst_case_cost": value.slippage_worst_case_cost,
        "slippage_observation_count": value.slippage_observation_count,
        "total_cost": total_cost,
        "total_cost_share": total_cost_share,
        "cost_per_research_unit": cost_per_research_unit,
        "status": status,
        "reason_codes": reason_codes,
        "cost_explanation": _cost_explanation(
            taker_fee_cost=taker_fee_cost,
            spread_cost=spread_cost,
            deposit_settlement_cost=deposit_settlement_cost,
            slippage_expected_cost=value.slippage_expected_cost,
            total_cost_share=total_cost_share,
            cost_per_research_unit=cost_per_research_unit,
        ),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchFeeCostReconciliationReport(
        **report_values,
        derived_validation_digest=_digest_for_payload(_json_payload(report_values)),
    )


def research_fee_cost_reconciliation_payload(
    report: ResearchFeeCostReconciliationReport,
) -> dict[str, Any]:
    if type(report) is not ResearchFeeCostReconciliationReport:
        raise ValueError("report must be a ResearchFeeCostReconciliationReport")
    _require_hard_flags("report", report)
    payload = _payload_without_digest(report)
    payload["derived_validation_digest"] = report.derived_validation_digest
    _reject_unsafe_public_payload("payload", payload)
    _require_hard_flags("payload", _DictFlags(payload))
    return payload


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _status_and_reason_codes(
    *,
    total_cost: Decimal,
    total_cost_share: Decimal | None,
    cost_per_research_unit: Decimal | None,
    expected_notional: Decimal,
    expected_research_units: Decimal,
    config: ResearchFeeCostReconciliationConfig,
) -> tuple[str, tuple[str, ...]]:
    if total_cost == ZERO:
        return PASS_STATUS, (_ZERO_REASON,)

    blocked: list[str] = []
    watch: list[str] = []
    if expected_notional == ZERO:
        blocked.append(_MISSING_NOTIONAL_REASON)
    if expected_research_units == ZERO:
        blocked.append(_MISSING_RESEARCH_UNITS_REASON)
    if (
        cost_per_research_unit is not None
        and cost_per_research_unit > config.block_cost_per_research_unit
    ):
        blocked.append(_COST_PER_UNIT_BLOCK_REASON)
    if total_cost_share is not None and total_cost_share > config.block_total_cost_share:
        blocked.append(_TOTAL_SHARE_BLOCK_REASON)
    if blocked:
        return BLOCK_STATUS, tuple(blocked)

    if (
        cost_per_research_unit is not None
        and cost_per_research_unit > config.watch_cost_per_research_unit
    ):
        watch.append(_COST_PER_UNIT_WATCH_REASON)
    if total_cost_share is not None and total_cost_share > config.watch_total_cost_share:
        watch.append(_TOTAL_SHARE_WATCH_REASON)
    if watch:
        return WATCH_STATUS, tuple(watch)
    return PASS_STATUS, (_PASS_REASON,)


def _cost_explanation(
    *,
    taker_fee_cost: Decimal,
    spread_cost: Decimal,
    deposit_settlement_cost: Decimal,
    slippage_expected_cost: Decimal,
    total_cost_share: Decimal | None,
    cost_per_research_unit: Decimal | None,
) -> tuple[str, ...]:
    return (
        f"taker_fee_cost={_decimal_payload(taker_fee_cost)}",
        f"spread_cost={_decimal_payload(spread_cost)}",
        f"deposit_settlement_cost={_decimal_payload(deposit_settlement_cost)}",
        f"slippage_expected_cost={_decimal_payload(slippage_expected_cost)}",
        f"total_cost_share={_optional_decimal_payload(total_cost_share)}",
        f"cost_per_research_unit={_optional_decimal_payload(cost_per_research_unit)}",
    )


def _validate_report_consistency(report: ResearchFeeCostReconciliationReport) -> None:
    if report.taker_fee_cost != _quantize(report.expected_notional * report.taker_fee_rate):
        raise ValueError("taker_fee_cost must match expected_notional and taker_fee_rate")
    if report.spread_cost != _quantize(report.expected_notional * report.spread_cost_rate):
        raise ValueError("spread_cost must match expected_notional and spread_cost_rate")
    if report.deposit_settlement_cost != _quantize(
        report.deposit_cost + report.settlement_cost,
    ):
        raise ValueError("deposit_settlement_cost must match deposit and settlement costs")
    expected_total_cost = _quantize(
        report.taker_fee_cost
        + report.spread_cost
        + report.deposit_settlement_cost
        + report.slippage_expected_cost,
    )
    if report.total_cost != expected_total_cost:
        raise ValueError("total_cost must match cost components")
    if report.total_cost_share != _optional_ratio(report.total_cost, report.expected_notional):
        raise ValueError("total_cost_share must match total_cost and expected_notional")
    if report.cost_per_research_unit != _optional_ratio(
        report.total_cost,
        report.expected_research_units,
    ):
        raise ValueError(
            "cost_per_research_unit must match total_cost and expected_research_units",
        )
    if report.slippage_worst_case_cost < report.slippage_expected_cost:
        raise ValueError("slippage_worst_case_cost must cover slippage_expected_cost")
    if report.cost_explanation != _cost_explanation(
        taker_fee_cost=report.taker_fee_cost,
        spread_cost=report.spread_cost,
        deposit_settlement_cost=report.deposit_settlement_cost,
        slippage_expected_cost=report.slippage_expected_cost,
        total_cost_share=report.total_cost_share,
        cost_per_research_unit=report.cost_per_research_unit,
    ):
        raise ValueError("cost_explanation must match cost components")


def _payload_without_digest(report: ResearchFeeCostReconciliationReport) -> dict[str, Any]:
    return _json_payload(
        {
            "generated_at": report.generated_at,
            "config_version": report.config_version,
            "research_case_label": report.research_case_label,
            "expected_notional": report.expected_notional,
            "expected_research_units": report.expected_research_units,
            "taker_fee_rate": report.taker_fee_rate,
            "spread_cost_rate": report.spread_cost_rate,
            "taker_fee_cost": report.taker_fee_cost,
            "spread_cost": report.spread_cost,
            "deposit_cost": report.deposit_cost,
            "settlement_cost": report.settlement_cost,
            "deposit_settlement_cost": report.deposit_settlement_cost,
            "slippage_expected_cost": report.slippage_expected_cost,
            "slippage_worst_case_cost": report.slippage_worst_case_cost,
            "slippage_observation_count": report.slippage_observation_count,
            "total_cost": report.total_cost,
            "total_cost_share": report.total_cost_share,
            "cost_per_research_unit": report.cost_per_research_unit,
            "status": report.status,
            "reason_codes": report.reason_codes,
            "cost_explanation": report.cost_explanation,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )


def _digest_for_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _json_payload(value: object) -> Any:
    if type(value) is Decimal:
        return _decimal_payload(value)
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if value is None or type(value) is bool or type(value) is str:
        return value
    if type(value) is tuple:
        return [_json_payload(item) for item in value]
    if type(value) is list:
        return [_json_payload(item) for item in value]
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            ready[key] = _json_payload(item)
        return ready
    raise ValueError("value is not JSON serializable")


def _optional_ratio(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    if denominator <= ZERO:
        return None
    return _quantize(numerator / denominator)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_unsafe_text(field_name, value)
    return value


def _normalize_public_text_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    normalized = tuple(value)
    if not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    for item in normalized:
        _require_canonical_string(field_name, item)
    return normalized


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    normalized = _normalize_public_text_tuple("reason_codes", value)
    for reason_code in normalized:
        if reason_code not in _REASON_CODES:
            raise ValueError("reason_codes must contain known values")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    expected_order = tuple(code for code in _REASON_CODE_ORDER if code in normalized)
    if normalized != expected_order:
        raise ValueError("reason_codes must be deterministic")
    return normalized


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label}.paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label}.report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label}.readonly must be True")


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(value)


def _normalize_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_decimal(field_name, value)


def _require_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)


def _decimal_payload(value: Decimal) -> str:
    return str(_quantize(value))


def _optional_decimal_payload(value: Decimal | None) -> str:
    if value is None:
        return "n/a"
    return _decimal_payload(value)


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_text(f"{current_path}.{field.name}", field.name)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                f"{current_path}.{field.name}",
            )
        return
    if type(value) is str:
        _reject_unsafe_text(current_path, value)
        return
    if type(value) is Decimal:
        _require_decimal(current_path, value)
        return
    if type(value) is datetime:
        _as_utc(current_path, value)
        return
    if value is None or type(value) is bool:
        return
    if type(value) in (int, float):
        raise ValueError(f"{current_path} must use Decimal-derived values")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _reject_unsafe_text(f"{current_path}.{key}", key)
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{current_path}.{key} must be True")
            _reject_unsafe_public_payload(label, item, f"{current_path}.{key}")
        return
    if type(value) in (list, tuple):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(label, item, f"{current_path}[{index}]")
        return
    raise ValueError(f"{current_path} is not publicly serializable")


def _reject_unsafe_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe public text")


__all__ = (
    "ResearchFeeCostReconciliationConfig",
    "ResearchFeeCostReconciliationInput",
    "ResearchFeeCostReconciliationReport",
    "build_research_fee_cost_reconciliation_report",
    "research_fee_cost_reconciliation_payload",
)
