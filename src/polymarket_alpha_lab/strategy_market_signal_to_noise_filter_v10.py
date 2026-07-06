"""Read-only market signal-to-noise filter for Phase 1 strategy outputs."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import UNSAFE_SURFACE_FIELD_FRAGMENTS


SIGNAL_QUALITY_STATUSES = (
    "confirmed_signal",
    "watch_signal",
    "noise_rejected",
)
FILTER_ACTIONS = (
    "keep_candidate",
    "review_manually",
    "drop_candidate",
)
REASON_CODES = (
    "material_market_move",
    "market_move_below_threshold",
    "confirmed_by_sources",
    "source_confirmation_absent",
    "source_confirmation_sparse",
    "reliable_sources",
    "source_reliability_mixed",
    "source_reliability_low",
    "rumor_pressure_present",
    "rumor_pressure_high",
    "model_consensus",
    "model_disagreement_moderate",
    "model_disagreement_high",
    "fresh_window",
    "stale_window",
    "signal_score_passed",
    "signal_score_review",
    "signal_score_failed",
)

COUNT_QUANTUM = Decimal("1")
VALUE_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_VALUE = Decimal("0.000000")
ONE = Decimal("1.000000")

MATERIAL_MARKET_MOVE_BPS = Decimal("50.000000")
CONFIRMED_SOURCE_COUNT = Decimal("2")
LOW_RELIABILITY_SCORE = Decimal("0.500000")
RELIABLE_SOURCE_SCORE = Decimal("0.750000")
HIGH_RUMOR_COUNT = Decimal("3")
CONSENSUS_DISAGREEMENT_SCORE = Decimal("0.200000")
HIGH_DISAGREEMENT_SCORE = Decimal("0.500000")
FRESH_WINDOW_MINUTES = Decimal("60.000000")
PASS_SCORE = Decimal("2.000000")
REVIEW_SCORE = Decimal("0.000000")

MOVE_SCORE_WEIGHT = Decimal("0.010000")
CONFIRMATION_SCORE_WEIGHT = Decimal("0.700000")
RELIABILITY_SCORE_WEIGHT = Decimal("0.750000")
DISAGREEMENT_SCORE_WEIGHT = Decimal("1.500000")
WINDOW_SCORE_WEIGHT = Decimal("0.009166666666666666666666666667")
FIRST_RUMOR_SCORE_WEIGHT = Decimal("1.300000")
NEXT_RUMOR_SCORE_WEIGHT = Decimal("0.9083333333333333333333333333")

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)


@dataclass(frozen=True)
class StrategyMarketSignalToNoiseFilterV10Input:
    market_id: str
    market_move_bps: Decimal
    source_confirmation_count: Decimal
    rumor_count: Decimal
    source_reliability_score: Decimal
    model_disagreement_score: Decimal
    time_window_minutes: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        object.__setattr__(
            self,
            "market_move_bps",
            _normalize_nonnegative_value("market_move_bps", self.market_move_bps),
        )
        object.__setattr__(
            self,
            "source_confirmation_count",
            _normalize_nonnegative_count(
                "source_confirmation_count",
                self.source_confirmation_count,
            ),
        )
        object.__setattr__(
            self,
            "rumor_count",
            _normalize_nonnegative_count("rumor_count", self.rumor_count),
        )
        object.__setattr__(
            self,
            "source_reliability_score",
            _normalize_ratio(
                "source_reliability_score",
                self.source_reliability_score,
            ),
        )
        object.__setattr__(
            self,
            "model_disagreement_score",
            _normalize_ratio(
                "model_disagreement_score",
                self.model_disagreement_score,
            ),
        )
        object.__setattr__(
            self,
            "time_window_minutes",
            _normalize_positive_value("time_window_minutes", self.time_window_minutes),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class StrategyMarketSignalToNoiseFilterV10Payload:
    market_id: str
    market_move_bps: Decimal
    source_confirmation_count: Decimal
    rumor_count: Decimal
    source_reliability_score: Decimal
    model_disagreement_score: Decimal
    time_window_minutes: Decimal
    signal_to_noise_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        object.__setattr__(
            self,
            "market_move_bps",
            _normalize_nonnegative_value("market_move_bps", self.market_move_bps),
        )
        object.__setattr__(
            self,
            "source_confirmation_count",
            _normalize_nonnegative_count(
                "source_confirmation_count",
                self.source_confirmation_count,
            ),
        )
        object.__setattr__(
            self,
            "rumor_count",
            _normalize_nonnegative_count("rumor_count", self.rumor_count),
        )
        object.__setattr__(
            self,
            "source_reliability_score",
            _normalize_ratio(
                "source_reliability_score",
                self.source_reliability_score,
            ),
        )
        object.__setattr__(
            self,
            "model_disagreement_score",
            _normalize_ratio(
                "model_disagreement_score",
                self.model_disagreement_score,
            ),
        )
        object.__setattr__(
            self,
            "time_window_minutes",
            _normalize_positive_value("time_window_minutes", self.time_window_minutes),
        )
        object.__setattr__(
            self,
            "signal_to_noise_score",
            _normalize_value("signal_to_noise_score", self.signal_to_noise_score),
        )
        _require_hard_flags("payload", self)


@dataclass(frozen=True)
class StrategyMarketSignalToNoiseFilterV10Result:
    market_id: str
    signal_quality_status: str
    signal_to_noise_score: Decimal
    filter_action: str
    reason_codes: tuple[str, ...]
    payload: StrategyMarketSignalToNoiseFilterV10Payload
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        _require_member(
            "signal_quality_status",
            self.signal_quality_status,
            SIGNAL_QUALITY_STATUSES,
        )
        object.__setattr__(
            self,
            "signal_to_noise_score",
            _normalize_value("signal_to_noise_score", self.signal_to_noise_score),
        )
        _require_member("filter_action", self.filter_action, FILTER_ACTIONS)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if type(self.payload) is not StrategyMarketSignalToNoiseFilterV10Payload:
            raise ValueError(
                "payload must be a StrategyMarketSignalToNoiseFilterV10Payload",
            )
        _require_hard_flags("payload", self.payload)
        _validate_result(self)
        _require_hard_flags("result", self)


def strategy_market_signal_to_noise_filter_v10(
    value: StrategyMarketSignalToNoiseFilterV10Input,
) -> StrategyMarketSignalToNoiseFilterV10Result:
    if type(value) is not StrategyMarketSignalToNoiseFilterV10Input:
        raise ValueError("value must be a StrategyMarketSignalToNoiseFilterV10Input")
    _require_hard_flags("input", value)
    score = _signal_to_noise_score(value)
    status = _signal_quality_status(score)
    return StrategyMarketSignalToNoiseFilterV10Result(
        market_id=value.market_id,
        signal_quality_status=status,
        signal_to_noise_score=score,
        filter_action=_filter_action(status),
        reason_codes=_reason_codes(value, status),
        payload=StrategyMarketSignalToNoiseFilterV10Payload(
            market_id=value.market_id,
            market_move_bps=value.market_move_bps,
            source_confirmation_count=value.source_confirmation_count,
            rumor_count=value.rumor_count,
            source_reliability_score=value.source_reliability_score,
            model_disagreement_score=value.model_disagreement_score,
            time_window_minutes=value.time_window_minutes,
            signal_to_noise_score=score,
        ),
    )


def strategy_market_signal_to_noise_filter_v10_payload(
    value: StrategyMarketSignalToNoiseFilterV10Result | dict[str, Any],
) -> dict[str, Any]:
    if type(value) is StrategyMarketSignalToNoiseFilterV10Result:
        _require_hard_flags("result", value)
        _reject_unsafe_payload_keys("signal filter result", value)
        payload = _json_ready(value)
    elif type(value) is dict:
        _require_hard_flags("payload", _DictFlags(value))
        _reject_unsafe_payload_keys("signal filter payload", value)
        payload = _json_ready(value)
    else:
        raise ValueError(
            "value must be a StrategyMarketSignalToNoiseFilterV10Result",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_strings("payload", payload)
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


def _signal_to_noise_score(value: StrategyMarketSignalToNoiseFilterV10Input) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        first_rumor = min(value.rumor_count, ONE)
        next_rumors = max(value.rumor_count - first_rumor, ZERO_COUNT)
        score = (
            value.market_move_bps * MOVE_SCORE_WEIGHT
            + value.source_confirmation_count * CONFIRMATION_SCORE_WEIGHT
            + value.source_reliability_score * RELIABILITY_SCORE_WEIGHT
            - value.model_disagreement_score * DISAGREEMENT_SCORE_WEIGHT
            - value.time_window_minutes * WINDOW_SCORE_WEIGHT
            - first_rumor * FIRST_RUMOR_SCORE_WEIGHT
            - next_rumors * NEXT_RUMOR_SCORE_WEIGHT
        )
        return _quantize_value(score)


def _signal_quality_status(score: Decimal) -> str:
    if score >= PASS_SCORE:
        return "confirmed_signal"
    if score > REVIEW_SCORE:
        return "watch_signal"
    return "noise_rejected"


def _filter_action(status: str) -> str:
    if status == "confirmed_signal":
        return "keep_candidate"
    if status == "watch_signal":
        return "review_manually"
    return "drop_candidate"


def _reason_codes(
    value: StrategyMarketSignalToNoiseFilterV10Input,
    status: str,
) -> tuple[str, ...]:
    codes: list[str] = []
    if value.market_move_bps >= MATERIAL_MARKET_MOVE_BPS:
        codes.append("material_market_move")
    else:
        codes.append("market_move_below_threshold")
    if value.source_confirmation_count >= CONFIRMED_SOURCE_COUNT:
        codes.append("confirmed_by_sources")
    elif value.source_confirmation_count == ZERO_COUNT:
        codes.append("source_confirmation_absent")
    else:
        codes.append("source_confirmation_sparse")
    if value.source_reliability_score >= RELIABLE_SOURCE_SCORE:
        codes.append("reliable_sources")
    elif value.source_reliability_score < LOW_RELIABILITY_SCORE:
        codes.append("source_reliability_low")
    else:
        codes.append("source_reliability_mixed")
    if value.rumor_count >= HIGH_RUMOR_COUNT:
        codes.append("rumor_pressure_high")
    elif value.rumor_count > ZERO_COUNT:
        codes.append("rumor_pressure_present")
    if value.model_disagreement_score >= HIGH_DISAGREEMENT_SCORE:
        codes.append("model_disagreement_high")
    elif value.model_disagreement_score <= CONSENSUS_DISAGREEMENT_SCORE:
        codes.append("model_consensus")
    else:
        codes.append("model_disagreement_moderate")
    if value.time_window_minutes <= FRESH_WINDOW_MINUTES:
        codes.append("fresh_window")
    else:
        codes.append("stale_window")
    if status == "confirmed_signal":
        codes.append("signal_score_passed")
    elif status == "watch_signal":
        codes.append("signal_score_review")
    else:
        codes.append("signal_score_failed")
    return tuple(codes)


def _validate_result(value: StrategyMarketSignalToNoiseFilterV10Result) -> None:
    if value.market_id != value.payload.market_id:
        raise ValueError("payload must match result")
    if value.signal_to_noise_score != value.payload.signal_to_noise_score:
        raise ValueError("payload must match result")
    if value.signal_quality_status != _signal_quality_status(value.signal_to_noise_score):
        raise ValueError("signal_quality_status must match score")
    if value.filter_action != _filter_action(value.signal_quality_status):
        raise ValueError("filter_action must match status")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a tuple")
    try:
        codes = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be a tuple") from exc
    for code in codes:
        _require_member(field_name, code, REASON_CODES)
    if len(set(codes)) != len(codes):
        raise ValueError(f"{field_name} must not contain duplicates")
    return codes


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, (str, bool)) or value is None:
        return value
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_strings(label: str, value: object) -> None:
    if type(value) is str:
        if _has_unsafe_surface_fragment(value):
            raise ValueError(f"unsafe live surface value in {label}")
        return
    if isinstance(value, dict):
        for item in value.values():
            _reject_unsafe_public_strings(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_strings(label, item)
        return


def _reject_unsafe_payload_keys(label: str, value: object) -> None:
    for key in _iter_payload_keys(value):
        if _has_unsafe_surface_fragment(key):
            raise ValueError(f"unsafe live surface field in {label}: {key}")


def _iter_payload_keys(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_payload_keys(asdict(value))
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            keys.append(key)
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    if isinstance(value, (list, tuple)):
        keys = []
        for item in value:
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    return ()


def _has_unsafe_surface_fragment(value: str) -> bool:
    lowered = value.lower()
    tokens = tuple(
        part
        for part in "".join(char if char.isalnum() else "_" for char in lowered).split(
            "_",
        )
        if part
    )
    for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS:
        if "_" in fragment:
            if fragment in lowered:
                return True
            continue
        if fragment in tokens:
            return True
    return False


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed:
        raise ValueError(f"{field_name} is not supported")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_value(field_name, value)
    if decimal_value < ZERO_VALUE or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return decimal_value.quantize(COUNT_QUANTUM)


def _normalize_positive_value(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_value(field_name, value)
    if decimal_value <= ZERO_VALUE:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_nonnegative_value(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_value(field_name, value)
    if decimal_value < ZERO_VALUE:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_value(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    return _quantize_value(decimal_value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _quantize_value(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(VALUE_QUANTUM)


__all__ = (
    "FILTER_ACTIONS",
    "REASON_CODES",
    "SIGNAL_QUALITY_STATUSES",
    "StrategyMarketSignalToNoiseFilterV10Input",
    "StrategyMarketSignalToNoiseFilterV10Payload",
    "StrategyMarketSignalToNoiseFilterV10Result",
    "strategy_market_signal_to_noise_filter_v10",
    "strategy_market_signal_to_noise_filter_v10_payload",
)
