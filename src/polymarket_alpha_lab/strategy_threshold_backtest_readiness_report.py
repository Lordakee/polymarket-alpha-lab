"""Pure report-only readiness summary for threshold backtest tuning."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import re
from typing import Any


__all__ = (
    "StrategyThresholdBacktestReadinessReport",
    "build_strategy_threshold_backtest_readiness_report",
    "strategy_threshold_backtest_readiness_report_digest",
    "strategy_threshold_backtest_readiness_report_payload",
)


_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_QUANT = Decimal("0.000001")
_MIN_HISTORICAL_SCREEN_COUNT = Decimal("100")
_MIN_SETTLED_MARKET_COUNT = Decimal("50")
_TARGET_HISTORICAL_SCREEN_COUNT = Decimal("120")
_TARGET_SETTLED_MARKET_COUNT = Decimal("80")
_CALIBRATION_ERROR_WATCH = Decimal("0.050000")
_CALIBRATION_ERROR_BLOCK = Decimal("0.100000")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")


@dataclass(frozen=True)
class StrategyThresholdBacktestReadinessReport:
    historical_screen_count: Decimal
    settled_market_count: Decimal
    domain_split_ready: bool
    cost_model_revision_current: bool
    slippage_model_revision_current: bool
    calibration_error_rate: Decimal
    supabase_history_ready: bool
    threshold_backtest_ready: bool
    sample_gap_count: Decimal
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    ready_ratio: Decimal
    digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyThresholdBacktestReadinessReport, "report")
        for field_name in ("historical_screen_count", "settled_market_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "domain_split_ready",
            "cost_model_revision_current",
            "slippage_model_revision_current",
            "supabase_history_ready",
            "threshold_backtest_ready",
        ):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "calibration_error_rate",
            _require_probability_decimal(
                "calibration_error_rate",
                self.calibration_error_rate,
            ),
        )
        object.__setattr__(
            self,
            "sample_gap_count",
            _require_nonnegative_whole_decimal("sample_gap_count", self.sample_gap_count),
        )
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
        return strategy_threshold_backtest_readiness_report_payload(self)


def build_strategy_threshold_backtest_readiness_report(
    *,
    historical_screen_count: Decimal,
    settled_market_count: Decimal,
    domain_split_ready: bool,
    cost_model_revision_current: bool,
    slippage_model_revision_current: bool,
    calibration_error_rate: Decimal,
    supabase_history_ready: bool,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> StrategyThresholdBacktestReadinessReport:
    values = {
        "historical_screen_count": _require_nonnegative_whole_decimal(
            "historical_screen_count",
            historical_screen_count,
        ),
        "settled_market_count": _require_nonnegative_whole_decimal(
            "settled_market_count",
            settled_market_count,
        ),
        "domain_split_ready": domain_split_ready,
        "cost_model_revision_current": cost_model_revision_current,
        "slippage_model_revision_current": slippage_model_revision_current,
        "calibration_error_rate": _require_probability_decimal(
            "calibration_error_rate",
            calibration_error_rate,
        ),
        "supabase_history_ready": supabase_history_ready,
        "paper_only": paper_only,
        "report_only": report_only,
        "readonly": readonly,
    }
    for field_name in (
        "domain_split_ready",
        "cost_model_revision_current",
        "slippage_model_revision_current",
        "supabase_history_ready",
    ):
        _require_bool(field_name, values[field_name])
    _require_hard_flags("report", _FlagView(paper_only, report_only, readonly))

    sample_gap_count = _sample_gap_count(
        values["historical_screen_count"],
        values["settled_market_count"],
    )
    blocked_reason_codes = _blocked_reason_codes(
        historical_screen_count=values["historical_screen_count"],
        settled_market_count=values["settled_market_count"],
        domain_split_ready=domain_split_ready,
        cost_model_revision_current=cost_model_revision_current,
        slippage_model_revision_current=slippage_model_revision_current,
        calibration_error_rate=values["calibration_error_rate"],
        supabase_history_ready=supabase_history_ready,
    )
    attention_reason_codes = _attention_reason_codes(
        historical_screen_count=values["historical_screen_count"],
        settled_market_count=values["settled_market_count"],
        calibration_error_rate=values["calibration_error_rate"],
        blocked_reason_codes=blocked_reason_codes,
    )
    report_values: dict[str, object] = {
        **values,
        "threshold_backtest_ready": not blocked_reason_codes
        and not attention_reason_codes,
        "sample_gap_count": sample_gap_count,
        "blocked_reason_codes": blocked_reason_codes,
        "attention_reason_codes": attention_reason_codes,
        "ready_ratio": _ready_ratio(
            values["historical_screen_count"],
            values["settled_market_count"],
        ),
    }
    return StrategyThresholdBacktestReadinessReport(
        **report_values,
        digest=_report_digest_from_values(report_values),
    )


def strategy_threshold_backtest_readiness_report_payload(
    report: StrategyThresholdBacktestReadinessReport,
) -> dict[str, Any]:
    if type(report) is not StrategyThresholdBacktestReadinessReport:
        raise ValueError("report must be a StrategyThresholdBacktestReadinessReport")
    _require_hard_flags("report", report)
    _validate_report_consistency(report)
    if report.digest != _report_digest_from_values(_report_values_without_digest(report)):
        raise ValueError("digest does not match report payload")
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def strategy_threshold_backtest_readiness_report_digest(
    report: StrategyThresholdBacktestReadinessReport,
) -> str:
    if type(report) is not StrategyThresholdBacktestReadinessReport:
        raise ValueError("report must be a StrategyThresholdBacktestReadinessReport")
    _require_hard_flags("report", report)
    _validate_report_consistency(report)
    return _report_digest_from_values(_report_values_without_digest(report))


@dataclass(frozen=True)
class _FlagView:
    paper_only: bool
    report_only: bool
    readonly: bool


def _sample_gap_count(
    historical_screen_count: Decimal,
    settled_market_count: Decimal,
) -> Decimal:
    historical_gap = max(_TARGET_HISTORICAL_SCREEN_COUNT - historical_screen_count, _ZERO)
    settled_gap = max(_TARGET_SETTLED_MARKET_COUNT - settled_market_count, _ZERO)
    return (historical_gap + settled_gap).quantize(Decimal("1"))


def _ready_ratio(
    historical_screen_count: Decimal,
    settled_market_count: Decimal,
) -> Decimal:
    historical_ratio = min(historical_screen_count / _TARGET_HISTORICAL_SCREEN_COUNT, _ONE)
    settled_ratio = min(settled_market_count / _TARGET_SETTLED_MARKET_COUNT, _ONE)
    return _quantize(min(historical_ratio, settled_ratio))


def _blocked_reason_codes(
    *,
    historical_screen_count: Decimal,
    settled_market_count: Decimal,
    domain_split_ready: bool,
    cost_model_revision_current: bool,
    slippage_model_revision_current: bool,
    calibration_error_rate: Decimal,
    supabase_history_ready: bool,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if historical_screen_count < _MIN_HISTORICAL_SCREEN_COUNT:
        reason_codes.append("insufficient_historical_screen_count")
    if settled_market_count < _MIN_SETTLED_MARKET_COUNT:
        reason_codes.append("insufficient_settled_market_count")
    if not domain_split_ready:
        reason_codes.append("domain_split_not_ready")
    if not cost_model_revision_current:
        reason_codes.append("cost_model_revision_stale")
    if not slippage_model_revision_current:
        reason_codes.append("slippage_model_revision_stale")
    if calibration_error_rate > _CALIBRATION_ERROR_BLOCK:
        reason_codes.append("calibration_error_rate_above_limit")
    if not supabase_history_ready:
        reason_codes.append("supabase_history_not_ready")
    return tuple(reason_codes)


def _attention_reason_codes(
    *,
    historical_screen_count: Decimal,
    settled_market_count: Decimal,
    calibration_error_rate: Decimal,
    blocked_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if blocked_reason_codes:
        return ()
    reason_codes: list[str] = []
    if historical_screen_count < _TARGET_HISTORICAL_SCREEN_COUNT:
        reason_codes.append("historical_screen_count_below_target")
    if settled_market_count < _TARGET_SETTLED_MARKET_COUNT:
        reason_codes.append("settled_market_count_below_target")
    if calibration_error_rate > _CALIBRATION_ERROR_WATCH:
        reason_codes.append("calibration_error_rate_watch")
    return tuple(reason_codes)


def _validate_report_consistency(report: StrategyThresholdBacktestReadinessReport) -> None:
    expected_blocked_reason_codes = _blocked_reason_codes(
        historical_screen_count=report.historical_screen_count,
        settled_market_count=report.settled_market_count,
        domain_split_ready=report.domain_split_ready,
        cost_model_revision_current=report.cost_model_revision_current,
        slippage_model_revision_current=report.slippage_model_revision_current,
        calibration_error_rate=report.calibration_error_rate,
        supabase_history_ready=report.supabase_history_ready,
    )
    expected_attention_reason_codes = _attention_reason_codes(
        historical_screen_count=report.historical_screen_count,
        settled_market_count=report.settled_market_count,
        calibration_error_rate=report.calibration_error_rate,
        blocked_reason_codes=expected_blocked_reason_codes,
    )
    if report.sample_gap_count != _sample_gap_count(
        report.historical_screen_count,
        report.settled_market_count,
    ):
        raise ValueError("sample_gap_count does not match report inputs")
    if report.blocked_reason_codes != expected_blocked_reason_codes:
        raise ValueError("blocked_reason_codes do not match report inputs")
    if report.attention_reason_codes != expected_attention_reason_codes:
        raise ValueError("attention_reason_codes do not match report inputs")
    expected_ready = (
        not expected_blocked_reason_codes
        and not expected_attention_reason_codes
    )
    if report.threshold_backtest_ready is not expected_ready:
        raise ValueError("threshold_backtest_ready does not match report inputs")
    if report.ready_ratio != _ready_ratio(
        report.historical_screen_count,
        report.settled_market_count,
    ):
        raise ValueError("ready_ratio does not match report inputs")


def _report_values_without_digest(
    report: StrategyThresholdBacktestReadinessReport,
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


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value.quantize(Decimal("1"))


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO or decimal_value > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(decimal_value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a valid Decimal") from exc


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be exactly bool")


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
