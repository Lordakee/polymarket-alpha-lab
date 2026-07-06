"""Pure domain/team calibration gap scoring for team memory reviews."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

LOW_BRIER_ERROR = Decimal("0.120000")
WATCH_BRIER_ERROR = Decimal("0.250000")
LOW_CONFIDENCE_OVERSTATEMENT = Decimal("0.080000")
WATCH_CONFIDENCE_OVERSTATEMENT = Decimal("0.200000")
LOW_SOURCE_RELIABILITY_DRIFT = Decimal("0.050000")
WATCH_SOURCE_RELIABILITY_DRIFT = Decimal("0.150000")
COMPLETE_POSTMORTEM_RATE = Decimal("1.000000")
WATCH_POSTMORTEM_RATE = Decimal("0.700000")

CALIBRATION_STATUSES = ("calibrated", "watch", "gap")
REMEDIATION_PRIORITIES = ("low", "medium", "high")
SENSITIVE_PUBLIC_VALUE_TOKENS = (
    "secret",
    "token",
    "private",
    "key",
    "bearer",
    "dsn",
    "password",
)
UNSAFE_PUBLIC_VALUE_TOKENS = (
    "auth",
    "wallet",
    "account",
    "balance",
    "order",
    "cancel",
    "replace",
    "sign",
    "signed",
    "signing",
    "signature",
    "live",
)
UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "://",
    "sk_live",
    "pk_live",
    "exchange_mutation",
    "private_key",
)


@dataclass(frozen=True)
class TeamDomainCalibrationGapV10Config:
    brier_error_weight: Decimal = Decimal("0.400000")
    resolved_count_weight: Decimal = Decimal("0.100000")
    confidence_overstatement_weight: Decimal = Decimal("0.200000")
    source_reliability_drift_weight: Decimal = Decimal("0.150000")
    postmortem_incompletion_weight: Decimal = Decimal("0.150000")
    strong_resolved_market_count: Decimal = Decimal("40")
    watch_resolved_market_count: Decimal = Decimal("15")
    watch_gap_score: Decimal = Decimal("0.150000")
    high_gap_score: Decimal = Decimal("0.350000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "brier_error_weight",
            "resolved_count_weight",
            "confidence_overstatement_weight",
            "source_reliability_drift_weight",
            "postmortem_incompletion_weight",
            "watch_gap_score",
            "high_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "strong_resolved_market_count",
            "watch_resolved_market_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_integral_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        require_paper_only_flags("TeamDomainCalibrationGapV10Config", self)
        _reject_unsafe_public_payload("TeamDomainCalibrationGapV10Config", self)


@dataclass(frozen=True)
class TeamDomainCalibrationGapV10Input:
    domain_id: str
    team_id: str
    recent_brier_error: Decimal
    resolved_market_count: Decimal
    confidence_overstatement: Decimal
    source_reliability_drift: Decimal
    postmortem_completion: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "domain_id",
            _require_non_empty_string("domain_id", self.domain_id),
        )
        object.__setattr__(
            self,
            "team_id",
            _require_non_empty_string("team_id", self.team_id),
        )
        for field_name in (
            "recent_brier_error",
            "confidence_overstatement",
            "source_reliability_drift",
            "postmortem_completion",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "resolved_market_count",
            _normalize_integral_decimal(
                "resolved_market_count",
                self.resolved_market_count,
            ),
        )
        require_paper_only_flags("TeamDomainCalibrationGapV10Input", self)
        _reject_unsafe_public_payload("TeamDomainCalibrationGapV10Input", self)


@dataclass(frozen=True)
class TeamDomainCalibrationGapV10Result:
    domain_id: str
    team_id: str
    calibration_gap_score: Decimal
    calibration_status: str
    remediation_priority: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "domain_id",
            _require_non_empty_string("domain_id", self.domain_id),
        )
        object.__setattr__(
            self,
            "team_id",
            _require_non_empty_string("team_id", self.team_id),
        )
        object.__setattr__(
            self,
            "calibration_gap_score",
            _normalize_ratio("calibration_gap_score", self.calibration_gap_score),
        )
        if self.calibration_status not in CALIBRATION_STATUSES:
            raise ValueError("calibration_status must be calibrated, watch, or gap")
        if self.remediation_priority not in REMEDIATION_PRIORITIES:
            raise ValueError("remediation_priority must be low, medium, or high")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_result_consistency(self)
        require_paper_only_flags("TeamDomainCalibrationGapV10Result", self)
        _reject_unsafe_public_payload("TeamDomainCalibrationGapV10Result", self)


def score_team_domain_calibration_gap_v10(
    calibration: TeamDomainCalibrationGapV10Input,
    config: TeamDomainCalibrationGapV10Config | None = None,
) -> TeamDomainCalibrationGapV10Result:
    if type(calibration) is not TeamDomainCalibrationGapV10Input:
        raise ValueError("calibration must be a TeamDomainCalibrationGapV10Input")
    if config is None:
        config = TeamDomainCalibrationGapV10Config()
    if type(config) is not TeamDomainCalibrationGapV10Config:
        raise ValueError("config must be a TeamDomainCalibrationGapV10Config")
    require_paper_only_flags("TeamDomainCalibrationGapV10Input", calibration)
    require_paper_only_flags("TeamDomainCalibrationGapV10Config", config)

    gap_score = _calibration_gap_score(calibration, config)
    calibration_status = _calibration_status(gap_score, config)
    remediation_priority = _remediation_priority(calibration_status)

    return TeamDomainCalibrationGapV10Result(
        domain_id=calibration.domain_id,
        team_id=calibration.team_id,
        calibration_gap_score=gap_score,
        calibration_status=calibration_status,
        remediation_priority=remediation_priority,
        reason_codes=(
            f"team_domain_calibration_{calibration_status}",
            _brier_error_reason(calibration.recent_brier_error),
            _resolved_count_reason(calibration.resolved_market_count, config),
            _confidence_reason(calibration.confidence_overstatement),
            _source_drift_reason(calibration.source_reliability_drift),
            _postmortem_reason(calibration.postmortem_completion),
            f"calibration_priority_{remediation_priority}",
        ),
    )


def _calibration_gap_score(
    calibration: TeamDomainCalibrationGapV10Input,
    config: TeamDomainCalibrationGapV10Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        postmortem_incompletion = _clamp_ratio(ONE - calibration.postmortem_completion)
        score = (
            calibration.recent_brier_error * config.brier_error_weight
            + _resolved_count_gap(calibration.resolved_market_count, config)
            * config.resolved_count_weight
            + calibration.confidence_overstatement
            * config.confidence_overstatement_weight
            + calibration.source_reliability_drift
            * config.source_reliability_drift_weight
            + postmortem_incompletion * config.postmortem_incompletion_weight
        )
        return _clamp_ratio(score)


def _resolved_count_gap(
    resolved_market_count: Decimal,
    config: TeamDomainCalibrationGapV10Config,
) -> Decimal:
    if resolved_market_count >= config.strong_resolved_market_count:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            (config.strong_resolved_market_count - resolved_market_count)
            / config.strong_resolved_market_count,
        )


def _brier_error_reason(recent_brier_error: Decimal) -> str:
    if recent_brier_error <= LOW_BRIER_ERROR:
        return "brier_error_low"
    if recent_brier_error <= WATCH_BRIER_ERROR:
        return "brier_error_watch"
    return "brier_error_high"


def _resolved_count_reason(
    resolved_market_count: Decimal,
    config: TeamDomainCalibrationGapV10Config,
) -> str:
    if resolved_market_count >= config.strong_resolved_market_count:
        return "resolved_count_strong"
    if resolved_market_count >= config.watch_resolved_market_count:
        return "resolved_count_watch"
    return "resolved_count_low"


def _confidence_reason(confidence_overstatement: Decimal) -> str:
    if confidence_overstatement <= LOW_CONFIDENCE_OVERSTATEMENT:
        return "confidence_overstatement_low"
    if confidence_overstatement <= WATCH_CONFIDENCE_OVERSTATEMENT:
        return "confidence_overstatement_watch"
    return "confidence_overstatement_high"


def _source_drift_reason(source_reliability_drift: Decimal) -> str:
    if source_reliability_drift <= LOW_SOURCE_RELIABILITY_DRIFT:
        return "source_reliability_drift_low"
    if source_reliability_drift <= WATCH_SOURCE_RELIABILITY_DRIFT:
        return "source_reliability_drift_watch"
    return "source_reliability_drift_high"


def _postmortem_reason(postmortem_completion: Decimal) -> str:
    if postmortem_completion >= COMPLETE_POSTMORTEM_RATE:
        return "postmortem_completion_complete"
    if postmortem_completion >= WATCH_POSTMORTEM_RATE:
        return "postmortem_completion_watch"
    return "postmortem_completion_low"


def _calibration_status(
    calibration_gap_score: Decimal,
    config: TeamDomainCalibrationGapV10Config,
) -> str:
    if calibration_gap_score >= config.high_gap_score:
        return "gap"
    if calibration_gap_score >= config.watch_gap_score:
        return "watch"
    return "calibrated"


def _remediation_priority(calibration_status: str) -> str:
    if calibration_status == "gap":
        return "high"
    if calibration_status == "watch":
        return "medium"
    return "low"


def _validate_config(config: TeamDomainCalibrationGapV10Config) -> None:
    weights_total = (
        config.brier_error_weight
        + config.resolved_count_weight
        + config.confidence_overstatement_weight
        + config.source_reliability_drift_weight
        + config.postmortem_incompletion_weight
    ).quantize(SCORE_QUANT)
    if weights_total != ONE:
        raise ValueError("calibration gap weights must sum to 1.000000")
    if config.watch_resolved_market_count > config.strong_resolved_market_count:
        raise ValueError(
            "watch_resolved_market_count must not exceed "
            "strong_resolved_market_count",
        )
    if config.watch_gap_score > config.high_gap_score:
        raise ValueError("watch_gap_score must not exceed high_gap_score")


def _validate_result_consistency(result: TeamDomainCalibrationGapV10Result) -> None:
    if result.remediation_priority != _remediation_priority(result.calibration_status):
        raise ValueError("remediation_priority must match calibration_status")
    expected_status_reason = f"team_domain_calibration_{result.calibration_status}"
    if result.reason_codes[0] != expected_status_reason:
        raise ValueError("reason_codes must start with calibration_status")
    expected_priority_reason = f"calibration_priority_{result.remediation_priority}"
    if result.reason_codes[-1] != expected_priority_reason:
        raise ValueError("reason_codes must end with remediation_priority")


def _require_non_empty_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(SCORE_QUANT)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _normalize_integral_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return value.quantize(COUNT_QUANT)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _clamp_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return min(ONE, max(ZERO, value)).quantize(SCORE_QUANT)


def _normalize_reason_codes(field_name: str, values: object) -> tuple[str, ...]:
    if type(values) is not tuple or not values:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    normalized = tuple(_require_non_empty_string(field_name, value) for value in values)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    return normalized


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    reject_unsafe_surface_fields(label, value)
    for item in _iter_string_values(value):
        if _contains_unsafe_public_text(item):
            raise ValueError(f"unsafe string value in {label}")


def _contains_unsafe_public_text(value: str) -> bool:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS):
        return True
    tokens = _split_public_text_tokens(normalized)
    return any(
        token in tokens
        for token in (*SENSITIVE_PUBLIC_VALUE_TOKENS, *UNSAFE_PUBLIC_VALUE_TOKENS)
    )


def _split_public_text_tokens(value: str) -> tuple[str, ...]:
    normalized = "".join(char if char.isalnum() else "_" for char in value)
    return tuple(part for part in normalized.split("_") if part)


def _iter_string_values(value: object) -> tuple[str, ...]:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _iter_string_values(json_ready_no_floats(value))
    if type(value) is str:
        return (value,)
    if isinstance(value, dict):
        values: list[str] = []
        for item in value.values():
            values.extend(_iter_string_values(item))
        return tuple(values)
    if isinstance(value, (list, tuple)):
        values = []
        for item in value:
            values.extend(_iter_string_values(item))
        return tuple(values)
    return ()


__all__ = (
    "TeamDomainCalibrationGapV10Config",
    "TeamDomainCalibrationGapV10Input",
    "TeamDomainCalibrationGapV10Result",
    "score_team_domain_calibration_gap_v10",
)
