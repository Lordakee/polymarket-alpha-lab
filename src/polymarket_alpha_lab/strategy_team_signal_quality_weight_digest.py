"""Paper-only reducer for specialist strategy team signal quality weights."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
from hashlib import sha256


__all__ = (
    "StrategyTeamSignalQualityWeightDigestConfig",
    "StrategyTeamSignalQualityWeightDigestReport",
    "StrategyTeamSignalQualityWeightDigestRow",
    "StrategyTeamSignalQualityWeightSignal",
    "build_strategy_team_signal_quality_weight_digest",
    "strategy_team_signal_quality_weight_digest_payload",
)


DEFAULT_CONFIG_VERSION = "strategy-team-signal-quality-weight-digest-v0"
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
STATUS_VALUES = ("pass", "watch", "block")
REPORT_STATUS_VALUES = ("pass", "watch", "blocked")
EMPTY_REASON_CODE = "strategy_team_signal_quality_weight_digest_empty"
PASS_REASON_CODE = "signal_quality_weight_pass"
WATCH_REASON_CODE = "signal_quality_weight_watch"
BLOCK_REASON_CODE = "signal_quality_weight_block"
REPORT_REASON_PRIORITY = (
    PASS_REASON_CODE,
    WATCH_REASON_CODE,
    BLOCK_REASON_CODE,
    "calibration_quality_low",
    "source_reliability_low",
    "evidence_stale",
    "disagreement_rate_high",
    "cost_aware_edge_nonpositive",
    "drawdown_pressure_high",
    EMPTY_REASON_CODE,
)
STATUS_SORT_PRIORITY = {"pass": 0, "watch": 1, "block": 2}
DECIMAL_CONTEXT = Context(prec=64)
SENSITIVE_REFERENCE_MARKERS = (
    "se" "cret",
    "to" "ken",
    "pri" "vate",
    "api" "_" "ke" "y",
    "pri" "vate" "_" "ke" "y",
    "bear" "er",
    "dsn",
    "pass" "word",
    "wall" "et",
)
UNSAFE_FIELD_FRAGMENTS = (
    "au" "th",
    "wall" "et",
    "or" "der",
    "pri" "vate" "_" "ke" "y",
    "api" "_" "ke" "y",
    "exchange_mutation",
    "bro" "ker",
    "can" "cel",
    "re" "place",
    "sign" "ing",
    "live" "_" "trading",
    "live" " " "trading",
)
UNSAFE_VALUE_FRAGMENTS = SENSITIVE_REFERENCE_MARKERS + UNSAFE_FIELD_FRAGMENTS


@dataclass(frozen=True)
class StrategyTeamSignalQualityWeightDigestConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    min_pass_weighted_score: Decimal = Decimal("0.400000")
    min_watch_weighted_score: Decimal = Decimal("0.200000")
    min_calibration_quality: Decimal = Decimal("0.600000")
    min_source_reliability: Decimal = Decimal("0.600000")
    max_evidence_age_seconds: Decimal = Decimal("86400.000000")
    max_disagreement_rate: Decimal = Decimal("0.300000")
    min_cost_aware_edge: Decimal = Decimal("0.020000")
    max_drawdown_pressure: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "min_pass_weighted_score",
            "min_watch_weighted_score",
            "min_calibration_quality",
            "min_source_reliability",
            "max_disagreement_rate",
            "max_drawdown_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_evidence_age_seconds",
            _normalize_positive_decimal(
                "max_evidence_age_seconds",
                self.max_evidence_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "min_cost_aware_edge",
            _normalize_decimal("min_cost_aware_edge", self.min_cost_aware_edge),
        )
        if self.min_pass_weighted_score < self.min_watch_weighted_score:
            raise ValueError("min_pass_weighted_score must not be below watch threshold")
        _require_safety_flags("config", self)


@dataclass(frozen=True)
class StrategyTeamSignalQualityWeightSignal:
    team_id: str
    signal_id: str
    team_reference: str
    observed_at: datetime
    calibration_quality: Decimal
    source_reliability: Decimal
    evidence_age_seconds: Decimal
    disagreement_rate: Decimal
    cost_aware_edge: Decimal
    drawdown_pressure: Decimal
    raw_signal_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("team_id", self.team_id)
        _require_public_string("signal_id", self.signal_id)
        _require_canonical_string("team_reference", self.team_reference)
        object.__setattr__(self, "team_reference", _redacted_reference(self.team_reference))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "calibration_quality",
            "source_reliability",
            "disagreement_rate",
            "drawdown_pressure",
            "raw_signal_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_age_seconds",
            _normalize_nonnegative_decimal("evidence_age_seconds", self.evidence_age_seconds),
        )
        object.__setattr__(
            self,
            "cost_aware_edge",
            _normalize_decimal("cost_aware_edge", self.cost_aware_edge),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _require_safety_flags("signal", self)


@dataclass(frozen=True)
class StrategyTeamSignalQualityWeightDigestRow:
    team_id: str
    signal_id: str
    redacted_team_reference: str
    observed_at: datetime
    calibration_quality: Decimal
    source_reliability: Decimal
    freshness_quality: Decimal
    evidence_age_seconds: Decimal
    disagreement_rate: Decimal
    cost_aware_edge: Decimal
    drawdown_pressure: Decimal
    raw_signal_score: Decimal
    quality_weight: Decimal
    weighted_signal_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("team_id", self.team_id)
        _require_public_string("signal_id", self.signal_id)
        _require_public_string("redacted_team_reference", self.redacted_team_reference)
        _require_redacted_reference(self.redacted_team_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "calibration_quality",
            "source_reliability",
            "freshness_quality",
            "disagreement_rate",
            "drawdown_pressure",
            "raw_signal_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "evidence_age_seconds",
            "quality_weight",
            "weighted_signal_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "cost_aware_edge",
            _normalize_decimal("cost_aware_edge", self.cost_aware_edge),
        )
        _require_member("status", self.status, STATUS_VALUES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _validate_row(self)
        _require_safety_flags("row", self)


@dataclass(frozen=True)
class StrategyTeamSignalQualityWeightDigestReport:
    generated_at: datetime
    config_version: str
    signal_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    total_quality_weight: Decimal
    average_weighted_signal_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyTeamSignalQualityWeightDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in ("signal_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("total_quality_weight", "average_weighted_signal_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, REPORT_STATUS_VALUES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_safety_flags("report", self)


def build_strategy_team_signal_quality_weight_digest(
    signals: Iterable[object],
    *,
    config: StrategyTeamSignalQualityWeightDigestConfig,
    generated_at: datetime,
) -> StrategyTeamSignalQualityWeightDigestReport:
    if type(config) is not StrategyTeamSignalQualityWeightDigestConfig:
        raise ValueError("config must be a StrategyTeamSignalQualityWeightDigestConfig")
    generated_at = _as_utc("generated_at", generated_at)
    _require_safety_flags("config", config)
    source_signals = _normalize_signals(signals)
    rows = tuple(
        sorted(
            (_row_from_signal(signal, config=config) for signal in source_signals),
            key=_row_sort_key,
        ),
    )

    return StrategyTeamSignalQualityWeightDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        signal_count=_count_decimal(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        total_quality_weight=_sum_decimal(row.quality_weight for row in rows),
        average_weighted_signal_score=_average_weighted_signal_score(rows),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def strategy_team_signal_quality_weight_digest_payload(
    report: StrategyTeamSignalQualityWeightDigestReport,
) -> dict[str, object]:
    if type(report) is not StrategyTeamSignalQualityWeightDigestReport:
        raise ValueError("report must be a StrategyTeamSignalQualityWeightDigestReport")
    _require_safety_flags("report", report)
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "signal_count": _count_payload(report.signal_count),
        "pass_count": _count_payload(report.pass_count),
        "watch_count": _count_payload(report.watch_count),
        "block_count": _count_payload(report.block_count),
        "total_quality_weight": _decimal_payload(report.total_quality_weight),
        "average_weighted_signal_score": _decimal_payload(
            report.average_weighted_signal_score,
        ),
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "rows": [_row_payload(row) for row in report.rows],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_payload(row: StrategyTeamSignalQualityWeightDigestRow) -> dict[str, object]:
    _require_safety_flags("row", row)
    return {
        "team_id": row.team_id,
        "signal_id": row.signal_id,
        "redacted_team_reference": row.redacted_team_reference,
        "observed_at": row.observed_at.isoformat(),
        "calibration_quality": _decimal_payload(row.calibration_quality),
        "source_reliability": _decimal_payload(row.source_reliability),
        "freshness_quality": _decimal_payload(row.freshness_quality),
        "evidence_age_seconds": _decimal_payload(row.evidence_age_seconds),
        "disagreement_rate": _decimal_payload(row.disagreement_rate),
        "cost_aware_edge": _decimal_payload(row.cost_aware_edge),
        "drawdown_pressure": _decimal_payload(row.drawdown_pressure),
        "raw_signal_score": _decimal_payload(row.raw_signal_score),
        "quality_weight": _decimal_payload(row.quality_weight),
        "weighted_signal_score": _decimal_payload(row.weighted_signal_score),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_from_signal(
    signal: StrategyTeamSignalQualityWeightSignal,
    *,
    config: StrategyTeamSignalQualityWeightDigestConfig,
) -> StrategyTeamSignalQualityWeightDigestRow:
    freshness_quality = _freshness_quality(signal.evidence_age_seconds, config=config)
    quality_weight = _quality_weight(
        calibration_quality=signal.calibration_quality,
        source_reliability=signal.source_reliability,
        freshness_quality=freshness_quality,
        disagreement_rate=signal.disagreement_rate,
        cost_aware_edge=signal.cost_aware_edge,
        drawdown_pressure=signal.drawdown_pressure,
    )
    weighted_signal_score = _multiply_decimal(signal.raw_signal_score, quality_weight)
    status, terminal_reason = _status_and_reason(
        weighted_signal_score=weighted_signal_score,
        signal=signal,
        config=config,
    )
    return StrategyTeamSignalQualityWeightDigestRow(
        team_id=signal.team_id,
        signal_id=signal.signal_id,
        redacted_team_reference=signal.team_reference,
        observed_at=signal.observed_at,
        calibration_quality=signal.calibration_quality,
        source_reliability=signal.source_reliability,
        freshness_quality=freshness_quality,
        evidence_age_seconds=signal.evidence_age_seconds,
        disagreement_rate=signal.disagreement_rate,
        cost_aware_edge=signal.cost_aware_edge,
        drawdown_pressure=signal.drawdown_pressure,
        raw_signal_score=signal.raw_signal_score,
        quality_weight=quality_weight,
        weighted_signal_score=weighted_signal_score,
        status=status,
        reason_codes=_normalize_reason_codes(
            (
                *signal.reason_codes,
                terminal_reason,
                *_quality_reason_codes(
                    signal,
                    freshness_quality=freshness_quality,
                    config=config,
                ),
            ),
            require_nonempty=True,
        ),
    )


def _freshness_quality(
    evidence_age_seconds: Decimal,
    *,
    config: StrategyTeamSignalQualityWeightDigestConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        remaining = ONE - (evidence_age_seconds / config.max_evidence_age_seconds)
        if remaining < ZERO:
            return ZERO
        return remaining.quantize(QUANTUM)


def _quality_weight(
    *,
    calibration_quality: Decimal,
    source_reliability: Decimal,
    freshness_quality: Decimal,
    disagreement_rate: Decimal,
    cost_aware_edge: Decimal,
    drawdown_pressure: Decimal,
) -> Decimal:
    positive_edge = _max_decimal(cost_aware_edge, ZERO)
    with localcontext(DECIMAL_CONTEXT):
        weight = (
            (calibration_quality * Decimal("0.300000"))
            + (source_reliability * Decimal("0.250000"))
            + (freshness_quality * Decimal("0.150000"))
            + (positive_edge * Decimal("0.500000"))
            + ((ONE - disagreement_rate) * Decimal("0.150000"))
            + ((ONE - drawdown_pressure) * Decimal("0.100000"))
        )
        return _max_decimal(weight.quantize(QUANTUM), ZERO)


def _status_and_reason(
    *,
    weighted_signal_score: Decimal,
    signal: StrategyTeamSignalQualityWeightSignal,
    config: StrategyTeamSignalQualityWeightDigestConfig,
) -> tuple[str, str]:
    if (
        weighted_signal_score < config.min_watch_weighted_score
        or signal.calibration_quality < config.min_calibration_quality
        or signal.source_reliability < config.min_source_reliability
        or signal.evidence_age_seconds > config.max_evidence_age_seconds
        or signal.disagreement_rate > config.max_disagreement_rate
        or signal.cost_aware_edge <= ZERO
        or signal.drawdown_pressure > config.max_drawdown_pressure
    ):
        return "block", BLOCK_REASON_CODE
    if weighted_signal_score >= config.min_pass_weighted_score:
        return "pass", PASS_REASON_CODE
    return "watch", WATCH_REASON_CODE


def _quality_reason_codes(
    signal: StrategyTeamSignalQualityWeightSignal,
    *,
    freshness_quality: Decimal,
    config: StrategyTeamSignalQualityWeightDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if signal.calibration_quality < config.min_calibration_quality:
        reason_codes.append("calibration_quality_low")
    elif signal.calibration_quality >= Decimal("0.800000"):
        reason_codes.append("calibration_quality_strong")
    if signal.source_reliability < config.min_source_reliability:
        reason_codes.append("source_reliability_low")
    elif signal.source_reliability >= Decimal("0.800000"):
        reason_codes.append("source_reliability_strong")
    if freshness_quality == ZERO:
        reason_codes.append("evidence_stale")
    else:
        reason_codes.append("evidence_fresh")
    if signal.disagreement_rate > config.max_disagreement_rate:
        reason_codes.append("disagreement_rate_high")
    else:
        reason_codes.append("disagreement_contained")
    if signal.cost_aware_edge <= ZERO:
        reason_codes.append("cost_aware_edge_nonpositive")
    else:
        reason_codes.append("cost_aware_edge_positive")
    if signal.drawdown_pressure > config.max_drawdown_pressure:
        reason_codes.append("drawdown_pressure_high")
    else:
        reason_codes.append("drawdown_pressure_contained")
    return tuple(reason_codes)


def _normalize_signals(
    signals: Iterable[object],
) -> tuple[StrategyTeamSignalQualityWeightSignal, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must be an iterable")
    try:
        rows = tuple(signals)
    except TypeError as exc:
        raise ValueError("signals must be an iterable") from exc
    normalized = tuple(_signal_from_supplied_row(row) for row in rows)
    seen_signal_ids: set[str] = set()
    for row in normalized:
        if row.signal_id in seen_signal_ids:
            raise ValueError("duplicate signal_id")
        seen_signal_ids.add(row.signal_id)
    return normalized


def _signal_from_supplied_row(
    row: object,
) -> StrategyTeamSignalQualityWeightSignal:
    if type(row) is StrategyTeamSignalQualityWeightSignal:
        _require_safety_flags("signal", row)
        return row
    raise ValueError("signals must contain StrategyTeamSignalQualityWeightSignal")


def _normalize_rows(
    rows: object,
) -> tuple[StrategyTeamSignalQualityWeightDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not StrategyTeamSignalQualityWeightDigestRow:
            raise ValueError("rows must contain StrategyTeamSignalQualityWeightDigestRow")
        _require_safety_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return normalized


def _row_sort_key(
    row: StrategyTeamSignalQualityWeightDigestRow,
) -> tuple[int, Decimal, Decimal, str, str]:
    return (
        STATUS_SORT_PRIORITY[row.status],
        -row.weighted_signal_score,
        -row.quality_weight,
        row.team_id,
        row.signal_id,
    )


def _status_count(
    rows: tuple[StrategyTeamSignalQualityWeightDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _average_weighted_signal_score(
    rows: tuple[StrategyTeamSignalQualityWeightDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _ratio_decimal(
        _sum_decimal(row.weighted_signal_score for row in rows),
        _count_decimal(len(rows)),
    )


def _report_status(rows: tuple[StrategyTeamSignalQualityWeightDigestRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "blocked"
    if any(row.status == "watch" for row in rows) or not rows:
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[StrategyTeamSignalQualityWeightDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    observed: set[str] = set()
    for row in rows:
        observed.update(row.reason_codes)
    return tuple(
        reason_code
        for reason_code in REPORT_REASON_PRIORITY
        if reason_code in observed
    )


def _validate_row(row: StrategyTeamSignalQualityWeightDigestRow) -> None:
    if row.weighted_signal_score != _multiply_decimal(
        row.raw_signal_score,
        row.quality_weight,
    ):
        raise ValueError("weighted_signal_score must match raw_signal_score and quality_weight")


def _validate_report(report: StrategyTeamSignalQualityWeightDigestReport) -> None:
    if report.signal_count != _count_decimal(len(report.rows)):
        raise ValueError("signal_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.total_quality_weight != _sum_decimal(row.quality_weight for row in report.rows):
        raise ValueError("total_quality_weight must match rows")
    if report.average_weighted_signal_score != _average_weighted_signal_score(report.rows):
        raise ValueError("average_weighted_signal_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_safety_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only") is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly") is not True:
        raise ValueError(f"readonly must be True for {label}")
    _reject_unsafe_fields(label, value)


def _reject_unsafe_fields(label: str, payload: object) -> None:
    for key in _iter_keys(payload):
        normalized_key = key.lower()
        if any(fragment in normalized_key for fragment in UNSAFE_FIELD_FRAGMENTS):
            raise ValueError(f"unsafe surface field in {label}: {key}")


def _iter_keys(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_keys(asdict(value))
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            keys.append(key)
            keys.extend(_iter_keys(item))
        return tuple(keys)
    if isinstance(value, (list, tuple)):
        keys = []
        for item in value:
            keys.extend(_iter_keys(item))
        return tuple(keys)
    return ()


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if _has_unsafe_value(value):
        raise ValueError(f"{field_name} has unsafe value")


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a nonnegative count Decimal")
    return normalized


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be a probability Decimal")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANTUM)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc


def _multiply_decimal(first: Decimal, second: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (first * second).quantize(QUANTUM)


def _ratio_decimal(numerator: Decimal, denominator: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        total = ZERO
        for value in values:
            total += value
        return total.quantize(QUANTUM)


def _max_decimal(first: Decimal, second: Decimal) -> Decimal:
    return first if first >= second else second


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _normalize_reason_codes(
    values: object,
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        reason_codes = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if require_nonempty and not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_canonical_reason_code("reason_codes", reason_code)
        if _has_unsafe_value(reason_code):
            raise ValueError("reason_codes has unsafe value")
    return tuple(dict.fromkeys(reason_codes))


def _require_canonical_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    if value != value.lower() or value.strip() != value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    for part in value.split("_"):
        if not part or not part.isalnum() or part != part.lower():
            raise ValueError(f"{field_name} must contain canonical reason codes")


def _redacted_reference(team_reference: str) -> str:
    if _has_unsafe_value(team_reference):
        digest = sha256(team_reference.encode("utf-8")).hexdigest()[:16]
        return f"team_ref_{digest}"
    return team_reference


def _require_redacted_reference(value: str) -> None:
    if _has_unsafe_value(value):
        raise ValueError("redacted_team_reference must not expose unsafe values")


def _has_unsafe_value(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_VALUE_FRAGMENTS)


def _decimal_payload(value: Decimal) -> str:
    return format(_normalize_decimal("payload decimal", value), "f")


def _count_payload(value: Decimal) -> str:
    return str(int(_normalize_count_decimal("payload count", value)))
