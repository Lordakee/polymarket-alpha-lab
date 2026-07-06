"""Pure typed multi-team signal arbitration v4 reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_MULTI_TEAM_SIGNAL_ARBITRATION_V4_CONFIG_VERSION = (
    "strategy-multi-team-signal-arbitration-v4"
)

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
REDACTED_SOURCE_REFERENCE = "<redacted-source-reference>"

SIGNAL_SIDES = ("yes", "no")
WINNING_SIDES = ("yes", "no", "none")
ARBITRATION_STATUSES = ("accepted", "watch", "blocked")
REPORT_STATUSES = ("empty", "accepted", "watch", "blocked")
ROW_REASON_CODES = (
    "side_consensus_yes",
    "side_consensus_no",
    "side_split",
    "source_quality_supported",
    "source_quality_low",
    "resolution_risk_clear",
    "resolution_risk_high",
    "arbitration_accepted",
    "arbitration_watch",
    "arbitration_blocked",
)
REPORT_REASON_CODES = (
    "multi_team_signal_arbitration_v4_empty",
    *ROW_REASON_CODES,
)
UNSAFE_PUBLIC_VALUE_TOKENS = (
    "secret",
    "token",
    "private",
    "key",
    "bearer",
    "dsn",
    "password",
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
class StrategyMultiTeamSignalArbitrationV4Config:
    config_version: str = DEFAULT_STRATEGY_MULTI_TEAM_SIGNAL_ARBITRATION_V4_CONFIG_VERSION
    min_accept_weight_share: Decimal = Decimal("0.600000")
    min_watch_weight_share: Decimal = Decimal("0.500000")
    min_source_quality: Decimal = Decimal("0.600000")
    max_resolution_risk: Decimal = Decimal("0.300000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyMultiTeamSignalArbitrationV4Config:
            raise ValueError(
                "config must be a StrategyMultiTeamSignalArbitrationV4Config",
            )
        _require_public_canonical_string("config_version", self.config_version)
        for field_name in (
            "min_accept_weight_share",
            "min_watch_weight_share",
            "min_source_quality",
            "max_resolution_risk",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.min_accept_weight_share < self.min_watch_weight_share:
            raise ValueError("min_accept_weight_share must be >= min_watch_weight_share")
        require_paper_only_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class StrategyMultiTeamSignalArbitrationV4Signal:
    condition_id: str
    team_id: str
    signal_side: str
    probability: Decimal
    confidence: Decimal
    source_quality: Decimal
    resolution_risk: Decimal
    source_reference: str = REDACTED_SOURCE_REFERENCE
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyMultiTeamSignalArbitrationV4Signal:
            raise ValueError("signal must be a StrategyMultiTeamSignalArbitrationV4Signal")
        _require_public_canonical_string("condition_id", self.condition_id)
        _require_public_canonical_string("team_id", self.team_id)
        _require_member("signal_side", self.signal_side, SIGNAL_SIDES)
        for field_name in (
            "probability",
            "confidence",
            "source_quality",
            "resolution_risk",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_public_canonical_string("source_reference", self.source_reference)
        object.__setattr__(self, "source_reference", REDACTED_SOURCE_REFERENCE)
        require_paper_only_flags("signal", self)
        _reject_unsafe_public_payload("signal", self)


@dataclass(frozen=True)
class StrategyMultiTeamSignalArbitrationV4Row:
    condition_id: str
    arbitration_status: str
    winning_side: str
    team_count: Decimal
    winning_side_team_count: Decimal
    winning_side_weight_share: Decimal
    consensus_probability: Decimal
    average_confidence: Decimal
    average_source_quality: Decimal
    average_resolution_risk: Decimal
    source_references: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyMultiTeamSignalArbitrationV4Row:
            raise ValueError("row must be a StrategyMultiTeamSignalArbitrationV4Row")
        _require_public_canonical_string("condition_id", self.condition_id)
        _require_member("arbitration_status", self.arbitration_status, ARBITRATION_STATUSES)
        _require_member("winning_side", self.winning_side, WINNING_SIDES)
        for field_name in ("team_count", "winning_side_team_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "winning_side_weight_share",
            "consensus_probability",
            "average_confidence",
            "average_source_quality",
            "average_resolution_risk",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_references",
            _normalize_source_references(self.source_references),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        require_paper_only_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class StrategyMultiTeamSignalArbitrationV4Report:
    config_version: str
    status: str
    condition_count: Decimal
    input_count: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyMultiTeamSignalArbitrationV4Row, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyMultiTeamSignalArbitrationV4Report:
            raise ValueError("report must be a StrategyMultiTeamSignalArbitrationV4Report")
        _require_public_canonical_string("config_version", self.config_version)
        _require_member("status", self.status, REPORT_STATUSES)
        for field_name in ("condition_count", "input_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        require_paper_only_flags("report", self)
        _reject_unsafe_public_payload("report", self)


def build_strategy_multi_team_signal_arbitration_v4(
    signals: object,
    *,
    config: StrategyMultiTeamSignalArbitrationV4Config,
) -> StrategyMultiTeamSignalArbitrationV4Report:
    if type(config) is not StrategyMultiTeamSignalArbitrationV4Config:
        raise ValueError("config must be a StrategyMultiTeamSignalArbitrationV4Config")
    require_paper_only_flags("config", config)
    _reject_unsafe_public_payload("config", config)
    rows_input = _normalize_signals(signals)
    rows = tuple(
        _row_for_condition(condition_signals, config)
        for condition_signals in _condition_groups(rows_input)
    )
    return StrategyMultiTeamSignalArbitrationV4Report(
        config_version=config.config_version,
        status=_report_status(rows),
        condition_count=_count(len(rows)),
        input_count=_count(len(rows_input)),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def strategy_multi_team_signal_arbitration_v4_payload(
    report: StrategyMultiTeamSignalArbitrationV4Report,
) -> dict[str, Any]:
    if type(report) is not StrategyMultiTeamSignalArbitrationV4Report:
        raise ValueError("report must be a StrategyMultiTeamSignalArbitrationV4Report")
    require_paper_only_flags("report", report)
    _reject_unsafe_public_payload("report", report)
    payload = json_ready_no_floats(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("payload", payload)
    return payload


def _row_for_condition(
    signals: tuple[StrategyMultiTeamSignalArbitrationV4Signal, ...],
    config: StrategyMultiTeamSignalArbitrationV4Config,
) -> StrategyMultiTeamSignalArbitrationV4Row:
    condition_id = signals[0].condition_id
    side_weights = {
        "yes": _side_weight(signals, "yes"),
        "no": _side_weight(signals, "no"),
    }
    total_weight = side_weights["yes"] + side_weights["no"]
    weighted_winning_side = _weighted_winning_side(side_weights)
    winning_side_weight_share = _ratio(side_weights[weighted_winning_side], total_weight)
    side_reason = _side_reason(weighted_winning_side, winning_side_weight_share, config)
    average_source_quality = _average(tuple(signal.source_quality for signal in signals))
    average_resolution_risk = _average(tuple(signal.resolution_risk for signal in signals))
    reasons = _row_reason_codes(
        side_reason=side_reason,
        average_source_quality=average_source_quality,
        average_resolution_risk=average_resolution_risk,
        config=config,
    )
    arbitration_status = _arbitration_status(reasons)
    winning_side = weighted_winning_side
    if arbitration_status == "blocked":
        winning_side = "none"
    return StrategyMultiTeamSignalArbitrationV4Row(
        condition_id=condition_id,
        arbitration_status=arbitration_status,
        winning_side=winning_side,
        team_count=_count(len(signals)),
        winning_side_team_count=_count(
            len(tuple(signal for signal in signals if signal.signal_side == weighted_winning_side)),
        ),
        winning_side_weight_share=winning_side_weight_share,
        consensus_probability=_consensus_probability(signals, winning_side),
        average_confidence=_average(tuple(signal.confidence for signal in signals)),
        average_source_quality=average_source_quality,
        average_resolution_risk=average_resolution_risk,
        source_references=_source_references(signals),
        reason_codes=reasons,
    )


def _normalize_signals(
    signals: object,
) -> tuple[StrategyMultiTeamSignalArbitrationV4Signal, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must be an iterable of StrategyMultiTeamSignalArbitrationV4Signal")
    try:
        rows = tuple(signals)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(
            "signals must be an iterable of StrategyMultiTeamSignalArbitrationV4Signal",
        ) from exc
    for signal in rows:
        if type(signal) is not StrategyMultiTeamSignalArbitrationV4Signal:
            raise ValueError("signals must contain StrategyMultiTeamSignalArbitrationV4Signal")
        require_paper_only_flags("signal", signal)
        _reject_unsafe_public_payload("signal", signal)
    _require_unique_team_per_condition(rows)
    return tuple(sorted(rows, key=lambda signal: (signal.condition_id, signal.team_id)))


def _condition_groups(
    signals: tuple[StrategyMultiTeamSignalArbitrationV4Signal, ...],
) -> tuple[tuple[StrategyMultiTeamSignalArbitrationV4Signal, ...], ...]:
    groups: list[tuple[StrategyMultiTeamSignalArbitrationV4Signal, ...]] = []
    current_condition_id: str | None = None
    current: list[StrategyMultiTeamSignalArbitrationV4Signal] = []
    for signal in signals:
        if current_condition_id is None:
            current_condition_id = signal.condition_id
        if signal.condition_id != current_condition_id:
            groups.append(tuple(current))
            current = []
            current_condition_id = signal.condition_id
        current.append(signal)
    if current:
        groups.append(tuple(current))
    return tuple(groups)


def _require_unique_team_per_condition(
    signals: tuple[StrategyMultiTeamSignalArbitrationV4Signal, ...],
) -> None:
    seen: set[tuple[str, str]] = set()
    for signal in signals:
        key = (signal.condition_id, signal.team_id)
        if key in seen:
            raise ValueError("team_id must be unique per condition_id")
        seen.add(key)


def _side_weight(
    signals: tuple[StrategyMultiTeamSignalArbitrationV4Signal, ...],
    side: str,
) -> Decimal:
    return _sum_decimals(
        tuple(_signal_weight(signal) for signal in signals if signal.signal_side == side),
    )


def _signal_weight(signal: StrategyMultiTeamSignalArbitrationV4Signal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return signal.confidence * signal.source_quality * (ONE_RATIO - signal.resolution_risk)


def _weighted_winning_side(side_weights: dict[str, Decimal]) -> str:
    if side_weights["yes"] >= side_weights["no"]:
        return "yes"
    return "no"


def _side_reason(
    winning_side: str,
    winning_side_weight_share: Decimal,
    config: StrategyMultiTeamSignalArbitrationV4Config,
) -> str:
    if winning_side_weight_share >= config.min_accept_weight_share:
        return f"side_consensus_{winning_side}"
    return "side_split"


def _row_reason_codes(
    *,
    side_reason: str,
    average_source_quality: Decimal,
    average_resolution_risk: Decimal,
    config: StrategyMultiTeamSignalArbitrationV4Config,
) -> tuple[str, ...]:
    reasons = [side_reason]
    if average_source_quality < config.min_source_quality:
        reasons.append("source_quality_low")
    else:
        reasons.append("source_quality_supported")
    if average_resolution_risk > config.max_resolution_risk:
        reasons.append("resolution_risk_high")
    else:
        reasons.append("resolution_risk_clear")
    reasons.append(f"arbitration_{_arbitration_status(tuple(reasons))}")
    return tuple(reasons)


def _arbitration_status(reason_codes: tuple[str, ...]) -> str:
    if (
        "source_quality_low" in reason_codes
        or "resolution_risk_high" in reason_codes
    ):
        return "blocked"
    if "side_split" in reason_codes:
        return "watch"
    return "accepted"


def _consensus_probability(
    signals: tuple[StrategyMultiTeamSignalArbitrationV4Signal, ...],
    winning_side: str,
) -> Decimal:
    if winning_side in SIGNAL_SIDES:
        side_signals = tuple(signal for signal in signals if signal.signal_side == winning_side)
        side_weight = _sum_decimals(tuple(_signal_weight(signal) for signal in side_signals))
        if side_weight > ZERO_RATIO:
            weighted_values = tuple(
                signal.probability * _signal_weight(signal) for signal in side_signals
            )
            return _ratio(_sum_decimals(weighted_values), side_weight)
    return _average(tuple(signal.probability for signal in signals))


def _report_status(rows: tuple[StrategyMultiTeamSignalArbitrationV4Row, ...]) -> str:
    if not rows:
        return "empty"
    if any(row.arbitration_status == "blocked" for row in rows):
        return "blocked"
    if any(row.arbitration_status == "watch" for row in rows):
        return "watch"
    return "accepted"


def _report_reason_codes(rows: tuple[StrategyMultiTeamSignalArbitrationV4Row, ...]) -> tuple[str, ...]:
    status = _report_status(rows)
    if status == "empty":
        return ("multi_team_signal_arbitration_v4_empty",)
    if status == "accepted":
        return ("arbitration_accepted",)
    present = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if row.arbitration_status != "accepted"
    }
    return tuple(reason_code for reason_code in REPORT_REASON_CODES if reason_code in present)


def _source_references(
    signals: tuple[StrategyMultiTeamSignalArbitrationV4Signal, ...],
) -> tuple[str, ...]:
    return tuple(sorted({signal.source_reference for signal in signals}))


def _normalize_rows(
    rows: object,
) -> tuple[StrategyMultiTeamSignalArbitrationV4Row, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable of StrategyMultiTeamSignalArbitrationV4Row")
    try:
        normalized = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be an iterable of StrategyMultiTeamSignalArbitrationV4Row") from exc
    for row in normalized:
        if type(row) is not StrategyMultiTeamSignalArbitrationV4Row:
            raise ValueError("rows must contain StrategyMultiTeamSignalArbitrationV4Row")
    return tuple(sorted(normalized, key=lambda row: row.condition_id))


def _normalize_source_references(source_references: object) -> tuple[str, ...]:
    if isinstance(source_references, (str, bytes)):
        raise ValueError("source_references must be an iterable of strings")
    try:
        references = tuple(source_references)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("source_references must be an iterable of strings") from exc
    if not references:
        raise ValueError("source_references must not be empty")
    for reference in references:
        _require_public_canonical_string("source_reference", reference)
    return tuple(sorted(set(references)))


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of reason codes")
    try:
        reason_codes = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of reason codes") from exc
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must not contain duplicates")
    for reason_code in reason_codes:
        _require_public_canonical_string("reason_code", reason_code)
        _require_member("reason_code", reason_code, allowed)
    return reason_codes


def _validate_row(row: StrategyMultiTeamSignalArbitrationV4Row) -> None:
    if row.winning_side_team_count > row.team_count:
        raise ValueError("winning_side_team_count must not exceed team_count")
    expected_status_code = f"arbitration_{row.arbitration_status}"
    if expected_status_code not in row.reason_codes:
        raise ValueError("arbitration_status must match reason_codes")
    if row.arbitration_status == "blocked" and row.winning_side != "none":
        raise ValueError("blocked row winning_side must be none")
    if row.arbitration_status != "blocked" and row.winning_side == "none":
        raise ValueError("nonblocked row winning_side must not be none")


def _validate_report(report: StrategyMultiTeamSignalArbitrationV4Report) -> None:
    if report.condition_count != _count(len(report.rows)):
        raise ValueError("condition_count must match rows")
    if report.input_count != _sum_decimals(tuple(row.team_count for row in report.rows)):
        raise ValueError("input_count must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    return _ratio(_sum_decimals(values), _count(len(values)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO_RATIO or denominator == ZERO_COUNT:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(RATIO_QUANTUM)


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    total = Decimal("0")
    for value in values:
        with localcontext(DECIMAL_CONTEXT):
            total += value
    return total


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must be an integer Decimal")
    if quantized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(RATIO_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    if quantized < ZERO_RATIO or quantized > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return quantized


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_public_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS):
        raise ValueError(f"{field_name} must not contain sensitive content")
    tokens = tuple(token for token in normalized.replace("-", "_").split("_") if token)
    if any(token in UNSAFE_PUBLIC_VALUE_TOKENS for token in tokens):
        raise ValueError(f"{field_name} must not contain sensitive content")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    reject_unsafe_surface_fields(label, _surface_guard_payload(value))


def _surface_guard_payload(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _surface_guard_payload(asdict(value))
    if isinstance(value, dict):
        safe_payload: dict[str, object] = {}
        for key, item in value.items():
            safe_key = "selected_side" if key == "signal_side" else key
            safe_payload[safe_key] = _surface_guard_payload(item)
        return safe_payload
    if isinstance(value, (list, tuple)):
        return tuple(_surface_guard_payload(item) for item in value)
    return value


__all__ = (
    "DEFAULT_STRATEGY_MULTI_TEAM_SIGNAL_ARBITRATION_V4_CONFIG_VERSION",
    "StrategyMultiTeamSignalArbitrationV4Config",
    "StrategyMultiTeamSignalArbitrationV4Report",
    "StrategyMultiTeamSignalArbitrationV4Row",
    "StrategyMultiTeamSignalArbitrationV4Signal",
    "build_strategy_multi_team_signal_arbitration_v4",
    "strategy_multi_team_signal_arbitration_v4_payload",
)
