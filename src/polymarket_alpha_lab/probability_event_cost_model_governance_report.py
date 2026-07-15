"""Read-only readiness report for probability event cost model governance."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
from hashlib import sha256
import json
import re
from typing import Any


__all__ = (
    "ProbabilityEventCostModelGovernanceReport",
    "build_probability_event_cost_model_governance_report",
    "probability_event_cost_model_governance_report_digest",
    "probability_event_cost_model_governance_report_payload",
)


_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_QUANT = Decimal("0.000001")
_INPUT_COUNT = Decimal("8")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
_BANDS = frozenset(("ready", "attention", "blocked"))


@dataclass(frozen=True)
class ProbabilityEventCostModelGovernanceReport:
    taker_fee_model_ready: bool
    slippage_model_ready: bool
    spread_model_ready: bool
    liquidity_haircut_ready: bool
    settlement_cost_ready: bool
    revision_digest_present: bool
    threshold_backtest_ready: bool
    operator_safety_ready: bool
    cost_model_governance_ready: bool
    governance_band: str
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    ready_ratio: Decimal
    digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ProbabilityEventCostModelGovernanceReport, "report")
        for field_name in _READINESS_FIELDS:
            _require_bool(field_name, getattr(self, field_name))
        _require_bool("cost_model_governance_ready", self.cost_model_governance_ready)
        _require_band("governance_band", self.governance_band)
        object.__setattr__(
            self,
            "blocked_reason_codes",
            _normalize_reason_codes("blocked_reason_codes", self.blocked_reason_codes),
        )
        object.__setattr__(
            self,
            "attention_reason_codes",
            _normalize_reason_codes(
                "attention_reason_codes",
                self.attention_reason_codes,
            ),
        )
        object.__setattr__(
            self,
            "ready_ratio",
            _require_probability_decimal("ready_ratio", self.ready_ratio),
        )
        _require_digest("digest", self.digest)
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.digest != expected_digest:
            raise ValueError("digest does not match report payload")

    @property
    def public_payload(self) -> dict[str, Any]:
        return probability_event_cost_model_governance_report_payload(self)


def build_probability_event_cost_model_governance_report(
    *,
    taker_fee_model_ready: bool,
    slippage_model_ready: bool,
    spread_model_ready: bool,
    liquidity_haircut_ready: bool,
    settlement_cost_ready: bool,
    revision_digest_present: bool,
    threshold_backtest_ready: bool,
    operator_safety_ready: bool,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ProbabilityEventCostModelGovernanceReport:
    values = {
        "taker_fee_model_ready": taker_fee_model_ready,
        "slippage_model_ready": slippage_model_ready,
        "spread_model_ready": spread_model_ready,
        "liquidity_haircut_ready": liquidity_haircut_ready,
        "settlement_cost_ready": settlement_cost_ready,
        "revision_digest_present": revision_digest_present,
        "threshold_backtest_ready": threshold_backtest_ready,
        "operator_safety_ready": operator_safety_ready,
        "paper_only": paper_only,
        "report_only": report_only,
        "readonly": readonly,
    }
    for field_name in _READINESS_FIELDS:
        _require_bool(field_name, values[field_name])
    _require_hard_flags("report", _FlagView(paper_only, report_only, readonly))

    blocked_reason_codes = _blocked_reason_codes(values)
    attention_reason_codes = _attention_reason_codes(values, blocked_reason_codes)
    governance_band = _governance_band(blocked_reason_codes, attention_reason_codes)
    report_values: dict[str, object] = {
        **values,
        "cost_model_governance_ready": governance_band == "ready",
        "governance_band": governance_band,
        "blocked_reason_codes": blocked_reason_codes,
        "attention_reason_codes": attention_reason_codes,
        "ready_ratio": _ready_ratio(values),
    }
    return ProbabilityEventCostModelGovernanceReport(
        **report_values,
        digest=_report_digest_from_values(report_values),
    )


def probability_event_cost_model_governance_report_payload(
    report: ProbabilityEventCostModelGovernanceReport,
) -> dict[str, Any]:
    if type(report) is not ProbabilityEventCostModelGovernanceReport:
        raise ValueError("report must be a ProbabilityEventCostModelGovernanceReport")
    _require_hard_flags("report", report)
    _validate_report_consistency(report)
    if report.digest != _report_digest_from_values(_report_values_without_digest(report)):
        raise ValueError("digest does not match report payload")
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def probability_event_cost_model_governance_report_digest(
    report: ProbabilityEventCostModelGovernanceReport,
) -> str:
    if type(report) is not ProbabilityEventCostModelGovernanceReport:
        raise ValueError("report must be a ProbabilityEventCostModelGovernanceReport")
    _require_hard_flags("report", report)
    _validate_report_consistency(report)
    return _report_digest_from_values(_report_values_without_digest(report))


@dataclass(frozen=True)
class _FlagView:
    paper_only: bool
    report_only: bool
    readonly: bool


_READINESS_FIELDS = (
    "taker_fee_model_ready",
    "slippage_model_ready",
    "spread_model_ready",
    "liquidity_haircut_ready",
    "settlement_cost_ready",
    "revision_digest_present",
    "threshold_backtest_ready",
    "operator_safety_ready",
)
_CORE_BLOCKER_FIELDS = (
    "taker_fee_model_ready",
    "slippage_model_ready",
    "spread_model_ready",
    "liquidity_haircut_ready",
    "settlement_cost_ready",
    "operator_safety_ready",
)
_REASON_CODES = {
    "taker_fee_model_ready": "taker_fee_model_not_ready",
    "slippage_model_ready": "slippage_model_not_ready",
    "spread_model_ready": "spread_model_not_ready",
    "liquidity_haircut_ready": "liquidity_haircut_not_ready",
    "settlement_cost_ready": "settlement_cost_not_ready",
    "revision_digest_present": "revision_digest_missing",
    "threshold_backtest_ready": "threshold_backtest_not_ready",
    "operator_safety_ready": "operator_safety_not_ready",
}


def _blocked_reason_codes(values: dict[str, object]) -> tuple[str, ...]:
    if all(values[field_name] is True for field_name in _CORE_BLOCKER_FIELDS):
        return ()
    return tuple(
        _REASON_CODES[field_name]
        for field_name in _READINESS_FIELDS
        if values[field_name] is not True
    )


def _attention_reason_codes(
    values: dict[str, object],
    blocked_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if blocked_reason_codes:
        return ()
    return tuple(
        _REASON_CODES[field_name]
        for field_name in ("revision_digest_present", "threshold_backtest_ready")
        if values[field_name] is not True
    )


def _governance_band(
    blocked_reason_codes: tuple[str, ...],
    attention_reason_codes: tuple[str, ...],
) -> str:
    if blocked_reason_codes:
        return "blocked"
    if attention_reason_codes:
        return "attention"
    return "ready"


def _ready_ratio(values: dict[str, object]) -> Decimal:
    ready_count = sum(Decimal("1") for field_name in _READINESS_FIELDS if values[field_name])
    return _quantize(ready_count / _INPUT_COUNT)


def _validate_report_consistency(
    report: ProbabilityEventCostModelGovernanceReport,
) -> None:
    values = {field_name: getattr(report, field_name) for field_name in _READINESS_FIELDS}
    expected_blocked_reason_codes = _blocked_reason_codes(values)
    expected_attention_reason_codes = _attention_reason_codes(
        values,
        expected_blocked_reason_codes,
    )
    expected_band = _governance_band(
        expected_blocked_reason_codes,
        expected_attention_reason_codes,
    )
    if report.blocked_reason_codes != expected_blocked_reason_codes:
        raise ValueError("blocked_reason_codes do not match report inputs")
    if report.attention_reason_codes != expected_attention_reason_codes:
        raise ValueError("attention_reason_codes do not match report inputs")
    if report.governance_band != expected_band:
        raise ValueError("governance_band does not match report inputs")
    if report.cost_model_governance_ready is not (expected_band == "ready"):
        raise ValueError("cost_model_governance_ready does not match report inputs")
    if report.ready_ratio != _ready_ratio(values):
        raise ValueError("ready_ratio does not match report inputs")


def _report_values_without_digest(
    report: ProbabilityEventCostModelGovernanceReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("digest")
    return values


def _report_digest_from_values(values: dict[str, object]) -> str:
    payload = _json_ready(values)
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(text.encode()).hexdigest()


def _json_ready(value: object) -> object:
    if type(value) is Decimal:
        return _decimal_text(value)
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return {str(key): _json_ready(item) for key, item in value.items()}
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("report payload contains unsupported value type")


def _decimal_text(value: Decimal) -> str:
    if value == value.to_integral_value() and value.as_tuple().exponent >= 0:
        return str(value.quantize(Decimal("1")))
    return f"{value.quantize(_QUANT):f}"


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < _ZERO or value > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(value)


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be exactly bool")


def _require_band(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _BANDS:
        raise ValueError(f"{field_name} must be a supported band")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    for reason_code in reason_codes:
        if type(reason_code) is not str or not _REASON_CODE_RE.fullmatch(reason_code):
            raise ValueError(f"{field_name} must contain safe reason codes")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must not contain duplicates")
    return reason_codes


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT)
