"""Read-only Phase 1 strategy readiness signal aggregator."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any


CONFIG_VERSION = "strategy-phase1-readiness-aggregator-v0"
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=28, rounding=ROUND_HALF_EVEN)
STATUSES = ("ready", "watch", "block")
STATUS_PRIORITY = {"ready": 0, "watch": 1, "block": 2}
COUNT_DECIMAL_FIELDS = frozenset(
    (
        "signal_count",
        "ready_count",
        "watch_count",
        "block_count",
        "manual_blocker_count",
    ),
)
FIXED_SIX_DECIMAL_FIELDS = frozenset(
    (
        "edge_score",
        "cost_score",
        "liquidity_score",
        "resolution_score",
        "freshness_score",
        "readiness_score",
        "mean_edge_score",
        "mean_cost_score",
        "mean_liquidity_score",
        "mean_resolution_score",
        "mean_freshness_score",
    ),
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class StrategyPhase1ReadinessSignal(_FinalDataclass):
    signal_id: str
    event_ref: str
    market_ref: str
    observed_at: datetime
    edge_score: Decimal
    cost_score: Decimal
    liquidity_score: Decimal
    resolution_score: Decimal
    freshness_score: Decimal
    manual_blocker_count: Decimal
    source_status: str
    source_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_dataclass(self, StrategyPhase1ReadinessSignal, "signal")
        for field_name in ("signal_id", "event_ref", "market_ref"):
            _require_nonempty_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "edge_score",
            "cost_score",
            "liquidity_score",
            "resolution_score",
            "freshness_score",
        ):
            object.__setattr__(self, field_name, _normalize_decimal(field_name, getattr(self, field_name)))
        object.__setattr__(
            self,
            "manual_blocker_count",
            _normalize_nonnegative_count("manual_blocker_count", self.manual_blocker_count),
        )
        _require_source_status(self.source_status)
        object.__setattr__(
            self,
            "source_reason_codes",
            _normalize_reason_codes("source_reason_codes", self.source_reason_codes),
        )
        _require_safety_flags(self)


@dataclass(frozen=True)
class StrategyPhase1ReadinessRow(_FinalDataclass):
    signal_id: str
    event_ref: str
    market_ref: str
    observed_at: datetime
    edge_score: Decimal
    cost_score: Decimal
    liquidity_score: Decimal
    resolution_score: Decimal
    freshness_score: Decimal
    manual_blocker_count: Decimal
    source_status: str
    source_reason_codes: tuple[str, ...]
    readiness_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_dataclass(self, StrategyPhase1ReadinessRow, "row")
        for field_name in ("signal_id", "event_ref", "market_ref"):
            _require_nonempty_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "edge_score",
            "cost_score",
            "liquidity_score",
            "resolution_score",
            "freshness_score",
            "readiness_score",
        ):
            object.__setattr__(self, field_name, _normalize_decimal(field_name, getattr(self, field_name)))
        object.__setattr__(
            self,
            "manual_blocker_count",
            _normalize_nonnegative_count("manual_blocker_count", self.manual_blocker_count),
        )
        _require_source_status(self.source_status)
        object.__setattr__(
            self,
            "source_reason_codes",
            _normalize_reason_codes("source_reason_codes", self.source_reason_codes),
        )
        _require_status(self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_safety_flags(self)
        _apply_or_verify_digest(self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class StrategyPhase1ReadinessReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    signal_count: Decimal
    ready_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    manual_blocker_count: Decimal
    mean_edge_score: Decimal
    mean_cost_score: Decimal
    mean_liquidity_score: Decimal
    mean_resolution_score: Decimal
    mean_freshness_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyPhase1ReadinessRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_dataclass(self, StrategyPhase1ReadinessReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_nonempty_string("config_version", self.config_version)
        if self.config_version != CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "signal_count",
            "ready_count",
            "watch_count",
            "block_count",
            "manual_blocker_count",
        ):
            object.__setattr__(self, field_name, _normalize_nonnegative_count(field_name, getattr(self, field_name)))
        for field_name in (
            "mean_edge_score",
            "mean_cost_score",
            "mean_liquidity_score",
            "mean_resolution_score",
            "mean_freshness_score",
        ):
            object.__setattr__(self, field_name, _normalize_decimal(field_name, getattr(self, field_name)))
        _require_status(self.status)
        object.__setattr__(self, "reason_codes", _normalize_report_reason_codes(self.reason_codes))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_safety_flags(self)
        _apply_or_verify_digest(self)
        _validate_report_consistency(self)


def build_strategy_phase1_readiness_report(
    signals: Iterable[StrategyPhase1ReadinessSignal],
    *,
    generated_at: datetime,
) -> StrategyPhase1ReadinessReport:
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_signals = _normalize_signals(signals)
    rows = tuple(
        sorted(
            (
                _row_from_signal(signal, generated_at=generated_at_utc)
                for signal in normalized_signals
            ),
            key=_row_sort_key,
        ),
    )
    return StrategyPhase1ReadinessReport(
        generated_at=generated_at_utc,
        config_version=CONFIG_VERSION,
        signal_count=_count(len(rows)),
        ready_count=_status_count(rows, "ready"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        manual_blocker_count=_sum_decimals(tuple(row.manual_blocker_count for row in rows)),
        mean_edge_score=_mean(tuple(row.edge_score for row in rows)),
        mean_cost_score=_mean(tuple(row.cost_score for row in rows)),
        mean_liquidity_score=_mean(tuple(row.liquidity_score for row in rows)),
        mean_resolution_score=_mean(tuple(row.resolution_score for row in rows)),
        mean_freshness_score=_mean(tuple(row.freshness_score for row in rows)),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def strategy_phase1_readiness_report_payload(
    report: StrategyPhase1ReadinessReport,
) -> dict[str, Any]:
    if type(report) is not StrategyPhase1ReadinessReport:
        raise ValueError("report must be a StrategyPhase1ReadinessReport")
    _require_safety_flags(report)
    _verify_report_integrity(report)
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _row_from_signal(
    signal: StrategyPhase1ReadinessSignal,
    *,
    generated_at: datetime,
) -> StrategyPhase1ReadinessRow:
    observed_at = _as_utc("observed_at", signal.observed_at)
    if observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    readiness_score = _readiness_score(signal)
    status = _status_for(signal, readiness_score=readiness_score)
    reason_codes = _reason_codes_for(
        signal,
        status=status,
        readiness_score=readiness_score,
    )
    return StrategyPhase1ReadinessRow(
        signal_id=signal.signal_id,
        event_ref=signal.event_ref,
        market_ref=signal.market_ref,
        observed_at=observed_at,
        edge_score=signal.edge_score,
        cost_score=signal.cost_score,
        liquidity_score=signal.liquidity_score,
        resolution_score=signal.resolution_score,
        freshness_score=signal.freshness_score,
        manual_blocker_count=signal.manual_blocker_count,
        source_status=signal.source_status,
        source_reason_codes=signal.source_reason_codes,
        readiness_score=readiness_score,
        status=status,
        reason_codes=reason_codes,
    )


def _readiness_score(signal: StrategyPhase1ReadinessSignal) -> Decimal:
    edge_component = _bounded_probability(_divide_decimal(_minimum_decimal(signal.edge_score, Decimal("0.080000")), Decimal("0.200000")))
    cost_component = _bounded_probability(_subtract_decimal(ONE, _multiply_decimal(signal.cost_score, Decimal("15.000000"))))
    penalty = _source_status_penalty(signal.source_status)
    if signal.manual_blocker_count > ZERO:
        penalty = _add_decimal(penalty, Decimal("0.010000"))
    return _quantize(
        _subtract_decimal(
            _divide_decimal(
                _sum_decimals(
                    (
                        edge_component,
                        cost_component,
                        signal.liquidity_score,
                        signal.resolution_score,
                        signal.freshness_score,
                    ),
                ),
                Decimal("5.000000"),
            ),
            penalty,
        ),
    )


def _status_for(signal: StrategyPhase1ReadinessSignal, *, readiness_score: Decimal) -> str:
    if signal.manual_blocker_count > ZERO:
        return "block"
    if signal.source_status in ("block", "blocked"):
        return "block"
    if signal.edge_score <= ZERO:
        return "block"
    if signal.liquidity_score < Decimal("0.500000"):
        return "block"
    if signal.resolution_score < Decimal("0.500000"):
        return "block"
    if signal.source_status == "watch":
        return "watch"
    if signal.edge_score < Decimal("0.050000"):
        return "watch"
    if signal.cost_score > Decimal("0.040000"):
        return "watch"
    if signal.liquidity_score < Decimal("0.750000"):
        return "watch"
    if signal.resolution_score < Decimal("0.750000"):
        return "watch"
    if signal.freshness_score < Decimal("0.750000"):
        return "watch"
    if readiness_score < Decimal("0.700000"):
        return "watch"
    return "ready"


def _reason_codes_for(
    signal: StrategyPhase1ReadinessSignal,
    *,
    status: str,
    readiness_score: Decimal,
) -> tuple[str, ...]:
    if status == "ready":
        return ("phase1_readiness_ready",)
    codes: list[str] = []
    codes.extend(signal.source_reason_codes)
    if not signal.source_reason_codes and signal.source_status == "watch":
        codes.append("source_status_watch")
    if not signal.source_reason_codes and signal.source_status in ("block", "blocked"):
        codes.append("source_status_block")
    if signal.manual_blocker_count > ZERO:
        codes.append("manual_blocker_review")
    if signal.edge_score <= ZERO:
        codes.append("edge_pressure_block")
    elif signal.edge_score < Decimal("0.050000"):
        codes.append("edge_pressure_watch")
    if status != "block" and signal.cost_score > Decimal("0.040000"):
        codes.append("cost_pressure_watch")
    if signal.liquidity_score < Decimal("0.500000"):
        codes.append("liquidity_pressure_block")
    elif signal.liquidity_score < Decimal("0.750000"):
        codes.append("liquidity_pressure_watch")
    if signal.resolution_score < Decimal("0.500000"):
        codes.append("resolution_pressure_block")
    elif signal.resolution_score < Decimal("0.750000"):
        codes.append("resolution_pressure_watch")
    if status != "block" and signal.freshness_score < Decimal("0.750000"):
        codes.append("freshness_pressure_watch")
    if status == "watch" and readiness_score < Decimal("0.700000"):
        codes.append("readiness_score_watch")
    return _normalize_reason_codes("reason_codes", tuple(codes))


def _row_sort_key(row: StrategyPhase1ReadinessRow) -> tuple[int, Decimal, str, str, str]:
    return (
        STATUS_PRIORITY[row.status],
        -row.readiness_score,
        row.event_ref,
        row.market_ref,
        row.signal_id,
    )


def _report_status(rows: tuple[StrategyPhase1ReadinessRow, ...]) -> str:
    if not rows:
        return "watch"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "ready"


def _report_reason_codes(rows: tuple[StrategyPhase1ReadinessRow, ...]) -> tuple[str, ...]:
    if not rows:
        return ("phase1_readiness_report_empty",)
    status = _report_status(rows)
    codes = [f"phase1_readiness_report_{status}"]
    if any(row.manual_blocker_count > ZERO for row in rows):
        codes.append("manual_blocker_review")
    return tuple(codes)


def _status_count(rows: tuple[StrategyPhase1ReadinessRow, ...], status: str) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _normalize_signals(
    signals: Iterable[StrategyPhase1ReadinessSignal],
) -> tuple[StrategyPhase1ReadinessSignal, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must be an iterable of StrategyPhase1ReadinessSignal values")
    try:
        normalized = tuple(signals)
    except TypeError as exc:
        raise ValueError("signals must be an iterable of StrategyPhase1ReadinessSignal values") from exc
    for signal in normalized:
        if type(signal) is not StrategyPhase1ReadinessSignal:
            raise ValueError("signals must contain only StrategyPhase1ReadinessSignal values")
        _require_safety_flags(signal)
    return normalized


def _normalize_rows(
    rows: Iterable[StrategyPhase1ReadinessRow],
) -> tuple[StrategyPhase1ReadinessRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = rows
    for row in normalized:
        if type(row) is not StrategyPhase1ReadinessRow:
            raise ValueError("rows must contain only StrategyPhase1ReadinessRow values")
        _require_safety_flags(row)
        _verify_digest(row)
    return normalized


def _validate_report_serialization_contract(
    report: StrategyPhase1ReadinessReport,
) -> None:
    _require_exact_dataclass(report, StrategyPhase1ReadinessReport, "report")
    _require_normalized_utc("generated_at", report.generated_at)
    _require_nonempty_string("config_version", report.config_version)
    if report.config_version != CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")
    for field_name in (
        "signal_count",
        "ready_count",
        "watch_count",
        "block_count",
        "manual_blocker_count",
    ):
        _normalize_nonnegative_count(field_name, getattr(report, field_name))
        _require_stored_six_decimal(field_name, getattr(report, field_name))
    for field_name in (
        "mean_edge_score",
        "mean_cost_score",
        "mean_liquidity_score",
        "mean_resolution_score",
        "mean_freshness_score",
    ):
        _require_stored_six_decimal(field_name, getattr(report, field_name))
    _require_status(report.status)
    normalized_reasons = _normalize_report_reason_codes(report.reason_codes)
    if normalized_reasons != report.reason_codes:
        raise ValueError("reason_codes must be canonical")
    if type(report.rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in report.rows:
        _validate_row_serialization_contract(row)
    _require_digest("derived_validation_digest", report.derived_validation_digest)
    _require_safety_flags(report)


def _validate_row_serialization_contract(row: object) -> None:
    _require_exact_dataclass(row, StrategyPhase1ReadinessRow, "row")
    for field_name in ("signal_id", "event_ref", "market_ref"):
        _require_nonempty_string(field_name, getattr(row, field_name))
    _require_normalized_utc("observed_at", row.observed_at)
    for field_name in (
        "edge_score",
        "cost_score",
        "liquidity_score",
        "resolution_score",
        "freshness_score",
        "readiness_score",
    ):
        _require_stored_six_decimal(field_name, getattr(row, field_name))
    _normalize_nonnegative_count("manual_blocker_count", row.manual_blocker_count)
    _require_stored_six_decimal("manual_blocker_count", row.manual_blocker_count)
    _require_source_status(row.source_status)
    normalized_source_reasons = _normalize_reason_codes(
        "source_reason_codes",
        row.source_reason_codes,
    )
    if normalized_source_reasons != row.source_reason_codes:
        raise ValueError("source_reason_codes must be canonical")
    _require_status(row.status)
    normalized_reasons = _normalize_reason_codes("reason_codes", row.reason_codes)
    if normalized_reasons != row.reason_codes:
        raise ValueError("reason_codes must be canonical")
    _require_digest("derived_validation_digest", row.derived_validation_digest)
    _require_safety_flags(row)


def _validate_row_consistency(row: StrategyPhase1ReadinessRow) -> None:
    signal = StrategyPhase1ReadinessSignal(
        signal_id=row.signal_id,
        event_ref=row.event_ref,
        market_ref=row.market_ref,
        observed_at=row.observed_at,
        edge_score=row.edge_score,
        cost_score=row.cost_score,
        liquidity_score=row.liquidity_score,
        resolution_score=row.resolution_score,
        freshness_score=row.freshness_score,
        manual_blocker_count=row.manual_blocker_count,
        source_status=row.source_status,
        source_reason_codes=row.source_reason_codes,
    )
    expected_score = _readiness_score(signal)
    if row.readiness_score != expected_score:
        raise ValueError("readiness_score does not match component signals")
    expected_status = _status_for(signal, readiness_score=expected_score)
    if row.status != expected_status:
        raise ValueError("status does not match component signals")
    expected_reason_codes = _reason_codes_for(
        signal,
        status=expected_status,
        readiness_score=expected_score,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes do not match component signals")


def _validate_report_consistency(report: StrategyPhase1ReadinessReport) -> None:
    generated_at = _as_utc("generated_at", report.generated_at)
    if report.signal_count != _count(len(report.rows)):
        raise ValueError("signal_count must match rows")
    if report.ready_count != _status_count(report.rows, "ready"):
        raise ValueError("ready_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    expected_manual_blockers = _sum_decimals(tuple(row.manual_blocker_count for row in report.rows))
    if report.manual_blocker_count != expected_manual_blockers:
        raise ValueError("manual_blocker_count must match rows")
    if report.mean_edge_score != _mean(tuple(row.edge_score for row in report.rows)):
        raise ValueError("mean_edge_score must match rows")
    if report.mean_cost_score != _mean(tuple(row.cost_score for row in report.rows)):
        raise ValueError("mean_cost_score must match rows")
    if report.mean_liquidity_score != _mean(tuple(row.liquidity_score for row in report.rows)):
        raise ValueError("mean_liquidity_score must match rows")
    if report.mean_resolution_score != _mean(tuple(row.resolution_score for row in report.rows)):
        raise ValueError("mean_resolution_score must match rows")
    if report.mean_freshness_score != _mean(tuple(row.freshness_score for row in report.rows)):
        raise ValueError("mean_freshness_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if tuple(sorted(report.rows, key=_row_sort_key)) != report.rows:
        raise ValueError("rows must be sorted by status and readiness")
    for row in report.rows:
        if row.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        _validate_row_consistency(row)
        _verify_digest(row)


def _verify_report_integrity(report: StrategyPhase1ReadinessReport) -> None:
    _validate_report_serialization_contract(report)
    _validate_report_consistency(report)
    _verify_digest(report)
    for row in report.rows:
        _verify_digest(row)


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    for value in values:
        total = _add_decimal(total, value)
    return total


def _source_status_penalty(source_status: str) -> Decimal:
    if source_status == "watch":
        return Decimal("0.030000")
    return ZERO


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(_sum_decimals(values) / Decimal(len(values)))


def _add_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left + right)


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left - right)


def _multiply_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left * right)


def _divide_decimal(left: Decimal, right: Decimal) -> Decimal:
    if right == ZERO:
        raise ValueError("right must be nonzero")
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left / right)


def _minimum_decimal(left: Decimal, right: Decimal) -> Decimal:
    if left <= right:
        return left
    return right


def _bounded_probability(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return value


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _normalize_nonnegative_count(field_name: str, value: Decimal) -> Decimal:
    raw_value = _require_decimal(field_name, value)
    if raw_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if raw_value != raw_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return _quantize(raw_value)


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    return _quantize(_require_decimal(field_name, value))


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_stored_six_decimal(field_name: str, value: Decimal) -> None:
    _normalize_decimal(field_name, value)
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not be negative zero")
    if not value.same_quantum(QUANTUM):
        raise ValueError(f"{field_name} must use six decimal places")


def _require_exact_dataclass(
    value: object,
    expected_type: type[object],
    label: str,
) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(QUANTUM)
    if normalized.is_zero():
        return normalized.copy_abs()
    return normalized


def _require_nonempty_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_source_status(value: str) -> None:
    if type(value) is not str or value not in (
        "pass",
        "watch",
        "block",
        "ready",
        "blocked",
    ):
        raise ValueError("source_status must be a known source status")


def _require_status(value: str) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError("status must be a known status")


def _normalize_reason_codes(field_name: str, value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized = value
    for reason_code in normalized:
        _require_nonempty_string(field_name, reason_code)
    return tuple(sorted(set(normalized)))


def _normalize_report_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized = value
    seen: set[str] = set()
    ordered: list[str] = []
    for reason_code in normalized:
        _require_nonempty_string("reason_codes", reason_code)
        if reason_code not in seen:
            ordered.append(reason_code)
            seen.add(reason_code)
    return tuple(ordered)


def _require_safety_flags(value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only") is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly") is not True:
        raise ValueError("readonly must be True")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_normalized_utc(field_name: str, value: datetime) -> None:
    _as_utc(field_name, value)
    if value.tzinfo is not UTC:
        raise ValueError(f"{field_name} must be normalized to UTC")


def _apply_or_verify_digest(
    value: StrategyPhase1ReadinessRow | StrategyPhase1ReadinessReport,
) -> None:
    expected = _derived_digest(value)
    provided = value.derived_validation_digest
    if provided == "":
        object.__setattr__(value, "derived_validation_digest", expected)
        return
    _require_digest("derived_validation_digest", provided)
    if provided != expected:
        raise ValueError("derived_validation_digest does not match derived fields")


def _verify_digest(value: StrategyPhase1ReadinessRow | StrategyPhase1ReadinessReport) -> None:
    _require_digest("derived_validation_digest", value.derived_validation_digest)
    if value.derived_validation_digest != _derived_digest(value):
        raise ValueError("derived_validation_digest does not match derived fields")


def _derived_digest(value: StrategyPhase1ReadinessRow | StrategyPhase1ReadinessReport) -> str:
    digest_input = asdict(value)
    digest_input.pop("derived_validation_digest", None)
    encoded = dumps(
        _json_ready(digest_input),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _require_digest(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    for character in value:
        if character not in "0123456789abcdef":
            raise ValueError(f"{field_name} must be a sha256 hex digest")


def _json_ready(value: Any, *, field_name: str | None = None) -> Any:
    if isinstance(value, dict):
        return {
            key: _json_ready(item, field_name=key)
            for key, item in value.items()
        }
    if isinstance(value, tuple):
        return [_json_ready(item, field_name=field_name) for item in value]
    if isinstance(value, list):
        return [_json_ready(item, field_name=field_name) for item in value]
    if isinstance(value, Decimal):
        if field_name in COUNT_DECIMAL_FIELDS:
            with localcontext(DECIMAL_CONTEXT):
                return format(value.quantize(Decimal("1")), "f")
        if field_name in FIXED_SIX_DECIMAL_FIELDS:
            return format(value, "f")
        raise ValueError("Decimal payload field does not define a serialization format")
    if isinstance(value, datetime):
        return value.isoformat()
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload value is not JSON-ready")


__all__ = (
    "StrategyPhase1ReadinessReport",
    "StrategyPhase1ReadinessRow",
    "StrategyPhase1ReadinessSignal",
    "build_strategy_phase1_readiness_report",
    "strategy_phase1_readiness_report_payload",
)
