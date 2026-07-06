"""Pure report reducer for team memory playbook decay alerts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_TEAM_MEMORY_PLAYBOOK_DECAY_ALERT_V10_CONFIG_VERSION = (
    "strategy-team-memory-playbook-decay-alert-v10"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
DECIMAL_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MAX_DECAY_SCORE = Decimal("100.000000")

STALE_UPDATE_DAYS = Decimal("45.000000")
AGING_UPDATE_DAYS = Decimal("21.000000")
FORECAST_ERROR_FULL_DECAY = Decimal("0.250000")
FORECAST_ERROR_HIGH = Decimal("0.200000")
FORECAST_ERROR_MODERATE = Decimal("0.080000")
SOURCE_FAILURE_HIGH = Decimal("0.250000")
SOURCE_FAILURE_ELEVATED = Decimal("0.050000")
DOMAIN_DRIFT_HIGH = Decimal("0.350000")
DOMAIN_DRIFT_MODERATE = Decimal("0.150000")
LOW_REUSE_FREQUENCY = Decimal("1.000000")
ACTIVE_REUSE_FREQUENCY = Decimal("5.000000")

STALENESS_POINTS = Decimal("30.000000")
FORECAST_ERROR_POINTS = Decimal("25.000000")
SOURCE_FAILURE_POINTS = Decimal("20.000000")
DOMAIN_DRIFT_POINTS = Decimal("20.000000")
LOW_REUSE_POINTS = Decimal("5.000000")

WATCH_DECAY_SCORE = Decimal("20.000000")
REFRESH_DECAY_SCORE = Decimal("45.000000")
CRITICAL_DECAY_SCORE = Decimal("75.000000")

ALERT_STATUSES = ("healthy", "watch", "refresh", "critical")
RECOMMENDED_ACTIONS = (
    "continue_playbook_monitoring",
    "schedule_playbook_decay_review",
    "queue_playbook_refresh",
    "escalate_specialist_playbook_rebuild",
    "recalibrate_forecast_examples",
    "repair_source_checklist",
    "refresh_domain_assumptions",
    "seed_specialist_reuse_trial",
)
SENSITIVE_MARKERS = (
    "api_key",
    "secret",
    "password",
    "private_key",
    "bearer ",
)


@dataclass(frozen=True)
class StrategyTeamMemoryPlaybookDecayAlertV10Input:
    specialist_id: str
    playbook_id: str
    domain_id: str
    days_since_update: Decimal
    recent_forecast_error: Decimal
    source_failure_rate: Decimal
    domain_drift: Decimal
    reuse_frequency: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("specialist_id", self.specialist_id)
        _require_canonical_string("playbook_id", self.playbook_id)
        _require_canonical_string("domain_id", self.domain_id)
        object.__setattr__(
            self,
            "days_since_update",
            _normalize_nonnegative_decimal(
                "days_since_update",
                self.days_since_update,
            ),
        )
        object.__setattr__(
            self,
            "recent_forecast_error",
            _normalize_unit_decimal(
                "recent_forecast_error",
                self.recent_forecast_error,
            ),
        )
        object.__setattr__(
            self,
            "source_failure_rate",
            _normalize_unit_decimal(
                "source_failure_rate",
                self.source_failure_rate,
            ),
        )
        object.__setattr__(
            self,
            "domain_drift",
            _normalize_unit_decimal("domain_drift", self.domain_drift),
        )
        object.__setattr__(
            self,
            "reuse_frequency",
            _normalize_nonnegative_decimal("reuse_frequency", self.reuse_frequency),
        )
        require_paper_only_flags(
            "strategy team memory playbook decay alert v10 input",
            self,
        )


@dataclass(frozen=True)
class StrategyTeamMemoryPlaybookDecayAlertV10Result:
    specialist_id: str
    playbook_id: str
    domain_id: str
    days_since_update: Decimal
    recent_forecast_error: Decimal
    source_failure_rate: Decimal
    domain_drift: Decimal
    reuse_frequency: Decimal
    decay_score: Decimal
    alert_status: str
    recommended_actions: tuple[str, ...]
    reason_codes: tuple[str, ...]
    validation_digest: str
    payload: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("specialist_id", self.specialist_id)
        _require_canonical_string("playbook_id", self.playbook_id)
        _require_canonical_string("domain_id", self.domain_id)
        object.__setattr__(
            self,
            "days_since_update",
            _normalize_nonnegative_decimal(
                "days_since_update",
                self.days_since_update,
            ),
        )
        object.__setattr__(
            self,
            "recent_forecast_error",
            _normalize_unit_decimal(
                "recent_forecast_error",
                self.recent_forecast_error,
            ),
        )
        object.__setattr__(
            self,
            "source_failure_rate",
            _normalize_unit_decimal(
                "source_failure_rate",
                self.source_failure_rate,
            ),
        )
        object.__setattr__(
            self,
            "domain_drift",
            _normalize_unit_decimal("domain_drift", self.domain_drift),
        )
        object.__setattr__(
            self,
            "reuse_frequency",
            _normalize_nonnegative_decimal("reuse_frequency", self.reuse_frequency),
        )
        object.__setattr__(
            self,
            "decay_score",
            _normalize_score("decay_score", self.decay_score),
        )
        _require_member("alert_status", self.alert_status, ALERT_STATUSES)
        object.__setattr__(
            self,
            "recommended_actions",
            _normalize_recommended_actions(self.recommended_actions),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "validation_digest",
            _normalize_validation_digest(self.validation_digest),
        )
        object.__setattr__(self, "payload", _normalize_payload("payload", self.payload))
        _validate_result(self)
        require_paper_only_flags(
            "strategy team memory playbook decay alert v10 result",
            self,
        )


def evaluate_strategy_team_memory_playbook_decay_alert_v10(
    playbook_signal: StrategyTeamMemoryPlaybookDecayAlertV10Input,
) -> StrategyTeamMemoryPlaybookDecayAlertV10Result:
    if type(playbook_signal) is not StrategyTeamMemoryPlaybookDecayAlertV10Input:
        raise ValueError(
            "playbook_signal must be a "
            "StrategyTeamMemoryPlaybookDecayAlertV10Input",
        )
    require_paper_only_flags(
        "strategy team memory playbook decay alert v10 input",
        playbook_signal,
    )

    decay_score, score_was_clamped = _decay_score(playbook_signal)
    alert_status = _alert_status(decay_score)
    recommended_actions = _recommended_actions(
        playbook_signal,
        alert_status=alert_status,
    )
    reason_codes = _reason_codes(
        playbook_signal,
        alert_status=alert_status,
        score_was_clamped=score_was_clamped,
    )
    payload = _payload(
        playbook_signal,
        decay_score=decay_score,
        alert_status=alert_status,
        recommended_actions=recommended_actions,
        reason_codes=reason_codes,
    )
    validation_digest = _validation_digest(payload)
    payload["validation_digest"] = validation_digest

    return StrategyTeamMemoryPlaybookDecayAlertV10Result(
        specialist_id=playbook_signal.specialist_id,
        playbook_id=playbook_signal.playbook_id,
        domain_id=playbook_signal.domain_id,
        days_since_update=playbook_signal.days_since_update,
        recent_forecast_error=playbook_signal.recent_forecast_error,
        source_failure_rate=playbook_signal.source_failure_rate,
        domain_drift=playbook_signal.domain_drift,
        reuse_frequency=playbook_signal.reuse_frequency,
        decay_score=decay_score,
        alert_status=alert_status,
        recommended_actions=recommended_actions,
        reason_codes=reason_codes,
        validation_digest=validation_digest,
        payload=payload,
    )


def strategy_team_memory_playbook_decay_alert_v10_payload(
    result: StrategyTeamMemoryPlaybookDecayAlertV10Result,
) -> dict[str, Any]:
    if type(result) is not StrategyTeamMemoryPlaybookDecayAlertV10Result:
        raise ValueError(
            "result must be a StrategyTeamMemoryPlaybookDecayAlertV10Result",
        )
    require_paper_only_flags(
        "strategy team memory playbook decay alert v10 result",
        result,
    )
    payload = json_ready_no_floats(result.payload)
    if type(payload) is not dict:
        raise ValueError("result payload must be a JSON object")
    _reject_unsafe_public_payload("strategy team memory playbook decay alert v10 payload", payload)
    _validate_result(result)
    require_paper_only_flags(
        "strategy team memory playbook decay alert v10 payload",
        _PayloadFlags(payload),
    )
    return payload


@dataclass(frozen=True)
class _PayloadFlags:
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


def _decay_score(
    value: (
        StrategyTeamMemoryPlaybookDecayAlertV10Input
        | StrategyTeamMemoryPlaybookDecayAlertV10Result
    ),
) -> tuple[Decimal, bool]:
    with localcontext(DECIMAL_CONTEXT):
        raw_score = STALENESS_POINTS * _capped_ratio(
            value.days_since_update,
            STALE_UPDATE_DAYS,
        )
        raw_score += FORECAST_ERROR_POINTS * _capped_ratio(
            value.recent_forecast_error,
            FORECAST_ERROR_FULL_DECAY,
        )
        raw_score += SOURCE_FAILURE_POINTS * value.source_failure_rate
        raw_score += DOMAIN_DRIFT_POINTS * value.domain_drift
        raw_score += LOW_REUSE_POINTS / (ONE + value.reuse_frequency)
    decay_score = _quantize(raw_score)
    if decay_score > MAX_DECAY_SCORE:
        return MAX_DECAY_SCORE, True
    if decay_score < ZERO:
        return ZERO, True
    return decay_score, False


def _alert_status(decay_score: Decimal) -> str:
    if decay_score >= CRITICAL_DECAY_SCORE:
        return "critical"
    if decay_score >= REFRESH_DECAY_SCORE:
        return "refresh"
    if decay_score >= WATCH_DECAY_SCORE:
        return "watch"
    return "healthy"


def _recommended_actions(
    value: (
        StrategyTeamMemoryPlaybookDecayAlertV10Input
        | StrategyTeamMemoryPlaybookDecayAlertV10Result
    ),
    *,
    alert_status: str,
) -> tuple[str, ...]:
    actions: list[str] = []
    if alert_status == "critical":
        actions.append("escalate_specialist_playbook_rebuild")
    elif alert_status == "refresh":
        actions.append("queue_playbook_refresh")
    elif alert_status == "watch":
        actions.append("schedule_playbook_decay_review")
    else:
        actions.append("continue_playbook_monitoring")

    if value.recent_forecast_error >= FORECAST_ERROR_MODERATE:
        actions.append("recalibrate_forecast_examples")
    if value.source_failure_rate >= SOURCE_FAILURE_ELEVATED:
        actions.append("repair_source_checklist")
    if value.domain_drift >= DOMAIN_DRIFT_MODERATE:
        actions.append("refresh_domain_assumptions")
    if value.reuse_frequency <= LOW_REUSE_FREQUENCY:
        actions.append("seed_specialist_reuse_trial")

    return _normalize_recommended_actions(tuple(actions))


def _reason_codes(
    value: (
        StrategyTeamMemoryPlaybookDecayAlertV10Input
        | StrategyTeamMemoryPlaybookDecayAlertV10Result
    ),
    *,
    alert_status: str,
    score_was_clamped: bool,
) -> tuple[str, ...]:
    reason_codes = [
        _update_age_reason_code(value.days_since_update),
        _forecast_error_reason_code(value.recent_forecast_error),
        _source_failure_reason_code(value.source_failure_rate),
        _domain_drift_reason_code(value.domain_drift),
        _reuse_reason_code(value.reuse_frequency),
    ]
    if score_was_clamped:
        reason_codes.append("decay_score_clamped")
    reason_codes.append(f"decay_alert_status_{alert_status}")
    return _normalize_reason_codes(tuple(reason_codes))


def _update_age_reason_code(days_since_update: Decimal) -> str:
    if days_since_update >= STALE_UPDATE_DAYS:
        return "playbook_update_stale"
    if days_since_update >= AGING_UPDATE_DAYS:
        return "playbook_update_aging"
    return "playbook_update_recent"


def _forecast_error_reason_code(recent_forecast_error: Decimal) -> str:
    if recent_forecast_error >= FORECAST_ERROR_HIGH:
        return "forecast_error_high"
    if recent_forecast_error >= FORECAST_ERROR_MODERATE:
        return "forecast_error_moderate"
    return "forecast_error_low"


def _source_failure_reason_code(source_failure_rate: Decimal) -> str:
    if source_failure_rate >= SOURCE_FAILURE_HIGH:
        return "source_failure_high"
    if source_failure_rate >= SOURCE_FAILURE_ELEVATED:
        return "source_failure_elevated"
    return "source_failure_low"


def _domain_drift_reason_code(domain_drift: Decimal) -> str:
    if domain_drift >= DOMAIN_DRIFT_HIGH:
        return "domain_drift_high"
    if domain_drift >= DOMAIN_DRIFT_MODERATE:
        return "domain_drift_moderate"
    return "domain_drift_low"


def _reuse_reason_code(reuse_frequency: Decimal) -> str:
    if reuse_frequency <= LOW_REUSE_FREQUENCY:
        return "playbook_reuse_low"
    if reuse_frequency >= ACTIVE_REUSE_FREQUENCY:
        return "playbook_reuse_active"
    return "playbook_reuse_moderate"


def _payload(
    value: (
        StrategyTeamMemoryPlaybookDecayAlertV10Input
        | StrategyTeamMemoryPlaybookDecayAlertV10Result
    ),
    *,
    decay_score: Decimal,
    alert_status: str,
    recommended_actions: tuple[str, ...],
    reason_codes: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "config_version": (
            DEFAULT_STRATEGY_TEAM_MEMORY_PLAYBOOK_DECAY_ALERT_V10_CONFIG_VERSION
        ),
        "specialist_id": value.specialist_id,
        "playbook_id": value.playbook_id,
        "domain_id": value.domain_id,
        "days_since_update": _decimal_payload(value.days_since_update),
        "recent_forecast_error": _decimal_payload(value.recent_forecast_error),
        "source_failure_rate": _decimal_payload(value.source_failure_rate),
        "domain_drift": _decimal_payload(value.domain_drift),
        "reuse_frequency": _decimal_payload(value.reuse_frequency),
        "decay_score": _decimal_payload(decay_score),
        "alert_status": alert_status,
        "recommended_actions": list(recommended_actions),
        "reason_codes": list(reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _validate_result(result: StrategyTeamMemoryPlaybookDecayAlertV10Result) -> None:
    signal = StrategyTeamMemoryPlaybookDecayAlertV10Input(
        specialist_id=result.specialist_id,
        playbook_id=result.playbook_id,
        domain_id=result.domain_id,
        days_since_update=result.days_since_update,
        recent_forecast_error=result.recent_forecast_error,
        source_failure_rate=result.source_failure_rate,
        domain_drift=result.domain_drift,
        reuse_frequency=result.reuse_frequency,
    )
    expected_score, score_was_clamped = _decay_score(signal)
    if result.decay_score != expected_score:
        raise ValueError("decay_score must match playbook decay inputs")
    expected_status = _alert_status(expected_score)
    if result.alert_status != expected_status:
        raise ValueError("alert_status must match decay_score")
    expected_actions = _recommended_actions(signal, alert_status=expected_status)
    if result.recommended_actions != expected_actions:
        raise ValueError("recommended_actions must match playbook decay inputs")
    expected_reasons = _reason_codes(
        signal,
        alert_status=expected_status,
        score_was_clamped=score_was_clamped,
    )
    if result.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match playbook decay inputs")
    expected_payload = _payload(
        signal,
        decay_score=expected_score,
        alert_status=expected_status,
        recommended_actions=expected_actions,
        reason_codes=expected_reasons,
    )
    expected_digest = _validation_digest(expected_payload)
    if result.validation_digest != expected_digest:
        raise ValueError("validation_digest must match playbook decay inputs")
    expected_payload["validation_digest"] = expected_digest
    if result.payload != expected_payload:
        raise ValueError("payload must match playbook decay inputs")


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_score(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > MAX_DECAY_SCORE:
        raise ValueError(f"{field_name} must be between 0 and 100")
    return decimal_value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _normalize_recommended_actions(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("recommended_actions must be a tuple")
    if not value:
        raise ValueError("recommended_actions must not be empty")
    seen: set[str] = set()
    normalized: list[str] = []
    for action in value:
        _require_member("recommended_actions", action, RECOMMENDED_ACTIONS)
        if action in seen:
            raise ValueError("recommended_actions must be unique")
        seen.add(action)
        normalized.append(action)
    return tuple(normalized)


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not value:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in value:
        _require_canonical_string("reason_codes", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
        normalized.append(reason_code)
    return tuple(normalized)


def _normalize_payload(field_name: str, value: object) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError(f"{field_name} must be a JSON object")
    normalized = json_ready_no_floats(value)
    if type(normalized) is not dict:
        raise ValueError(f"{field_name} must be a JSON object")
    _reject_unsafe_public_payload(field_name, normalized)
    return normalized


def _normalize_validation_digest(value: object) -> str:
    if type(value) is not str:
        raise ValueError("validation_digest must be a sha256 hex string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError("validation_digest must be a sha256 hex string")
    return value


def _validation_digest(payload: dict[str, Any]) -> str:
    canonical_payload = dict(payload)
    canonical_payload.pop("validation_digest", None)
    encoded = json.dumps(
        canonical_payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    reject_unsafe_surface_fields(label, payload)


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if not value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_sensitive_text(value)


def _reject_sensitive_text(value: str) -> None:
    lowered = value.lower()
    if any(marker in lowered for marker in SENSITIVE_MARKERS):
        raise ValueError("must not contain sensitive material")


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        ratio = numerator / denominator
    if ratio > ONE:
        return ONE
    if ratio < ZERO:
        return ZERO
    return ratio


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(DECIMAL_QUANTUM)


def _decimal_payload(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("payload decimal must be a Decimal")
    if not value.is_finite():
        raise ValueError("payload decimal must be finite")
    return str(_quantize(value))


__all__ = (
    "DEFAULT_STRATEGY_TEAM_MEMORY_PLAYBOOK_DECAY_ALERT_V10_CONFIG_VERSION",
    "StrategyTeamMemoryPlaybookDecayAlertV10Input",
    "StrategyTeamMemoryPlaybookDecayAlertV10Result",
    "evaluate_strategy_team_memory_playbook_decay_alert_v10",
    "strategy_team_memory_playbook_decay_alert_v10_payload",
)
