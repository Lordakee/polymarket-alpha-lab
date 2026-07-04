"""Paper-only reducer for strategy team memory signal weights."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
from hashlib import sha256


__all__ = (
    "DEFAULT_STRATEGY_TEAM_MEMORY_SIGNAL_WEIGHT_GATE_DIGEST_CONFIG_VERSION",
    "StrategyTeamMemorySignalWeightGateDigestConfig",
    "StrategyTeamMemorySignalWeightGateInput",
    "StrategyTeamMemorySignalWeightGateReasonCodeCount",
    "StrategyTeamMemorySignalWeightGateReport",
    "StrategyTeamMemorySignalWeightGateRow",
    "build_strategy_team_memory_signal_weight_gate_digest",
    "strategy_team_memory_signal_weight_gate_digest_payload",
)


DEFAULT_STRATEGY_TEAM_MEMORY_SIGNAL_WEIGHT_GATE_DIGEST_CONFIG_VERSION = (
    "strategy-team-memory-signal-weight-gate-digest-v0"
)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MEMORY_GROUP_WEIGHT = Decimal("0.600000")
SUPPORT_GROUP_WEIGHT = Decimal("0.400000")
EMPTY_REASON_CODE = "strategy_team_memory_signal_weight_gate_digest_empty"
STATUS_VALUES = ("blocked", "watch", "pass")
STATUS_SORT_PRIORITY = {"blocked": 0, "watch": 1, "pass": 2}
DECIMAL_CONTEXT = Context(prec=64)
ROW_REASON_PRIORITY = (
    "team_memory_signal_weight_blocked",
    "team_memory_signal_weight_watch",
    "team_memory_signal_weight_pass",
    "team_memory_signal_weight_below_watch",
    "team_memory_signal_weight_below_pass",
    "forecast_calibration_memory_below_watch",
    "forecast_calibration_memory_below_pass",
    "resolution_accuracy_memory_below_watch",
    "resolution_accuracy_memory_below_pass",
    "source_reliability_below_watch",
    "source_reliability_below_pass",
    "information_velocity_below_watch",
    "information_velocity_below_pass",
    "disagreement_pressure_above_watch",
    "disagreement_pressure_above_pass",
    "conflict_arbitration_below_watch",
    "conflict_arbitration_below_pass",
    "workload_capacity_below_watch",
    "workload_capacity_below_pass",
)
REPORT_REASON_PRIORITY = (*ROW_REASON_PRIORITY, EMPTY_REASON_CODE)
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
    "exchange" "_" "mutation",
    "bro" "ker",
    "can" "cel",
    "re" "place",
    "sign" "ing",
    "live" "_" "trading",
    "live" " " "trading",
)
UNSAFE_VALUE_FRAGMENTS = SENSITIVE_REFERENCE_MARKERS + UNSAFE_FIELD_FRAGMENTS


@dataclass(frozen=True)
class StrategyTeamMemorySignalWeightGateDigestConfig:
    config_version: str = (
        DEFAULT_STRATEGY_TEAM_MEMORY_SIGNAL_WEIGHT_GATE_DIGEST_CONFIG_VERSION
    )
    min_pass_team_memory_signal_weight: Decimal = Decimal("0.700000")
    min_watch_team_memory_signal_weight: Decimal = Decimal("0.450000")
    min_component_pass_score: Decimal = Decimal("0.650000")
    min_component_watch_score: Decimal = Decimal("0.400000")
    max_pass_disagreement_pressure: Decimal = Decimal("0.250000")
    max_watch_disagreement_pressure: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "min_pass_team_memory_signal_weight",
            "min_watch_team_memory_signal_weight",
            "min_component_pass_score",
            "min_component_watch_score",
            "max_pass_disagreement_pressure",
            "max_watch_disagreement_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_pass_team_memory_signal_weight < self.min_watch_team_memory_signal_weight:
            raise ValueError("pass team memory signal weight must not be below watch")
        if self.min_component_pass_score < self.min_component_watch_score:
            raise ValueError("component pass score must not be below watch")
        if self.max_pass_disagreement_pressure > self.max_watch_disagreement_pressure:
            raise ValueError("pass disagreement pressure must not exceed watch")
        _require_safety_flags("config", self)


@dataclass(frozen=True)
class StrategyTeamMemorySignalWeightGateInput:
    candidate_id: str
    team_id: str
    category_id: str
    observed_at: datetime
    forecast_calibration_memory_score: Decimal
    resolution_accuracy_memory_score: Decimal
    source_reliability_score: Decimal
    information_velocity_score: Decimal
    disagreement_pressure: Decimal
    conflict_arbitration_score: Decimal
    workload_capacity_score: Decimal
    public_reference: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("candidate_id", self.candidate_id)
        _require_public_string("team_id", self.team_id)
        _require_public_string("category_id", self.category_id)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "forecast_calibration_memory_score",
            "resolution_accuracy_memory_score",
            "source_reliability_score",
            "information_velocity_score",
            "disagreement_pressure",
            "conflict_arbitration_score",
            "workload_capacity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_canonical_string("public_reference", self.public_reference)
        object.__setattr__(
            self,
            "public_reference",
            _redacted_reference(self.public_reference),
        )
        _require_safety_flags("input", self)


@dataclass(frozen=True)
class StrategyTeamMemorySignalWeightGateRow:
    candidate_id: str
    team_id: str
    category_id: str
    observed_at: datetime
    redacted_public_reference: str
    forecast_calibration_memory_score: Decimal
    resolution_accuracy_memory_score: Decimal
    source_reliability_score: Decimal
    information_velocity_score: Decimal
    disagreement_pressure: Decimal
    disagreement_alignment_score: Decimal
    conflict_arbitration_score: Decimal
    workload_capacity_score: Decimal
    team_memory_signal_weight: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("candidate_id", self.candidate_id)
        _require_public_string("team_id", self.team_id)
        _require_public_string("category_id", self.category_id)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_redacted_reference(self.redacted_public_reference)
        for field_name in (
            "forecast_calibration_memory_score",
            "resolution_accuracy_memory_score",
            "source_reliability_score",
            "information_velocity_score",
            "disagreement_pressure",
            "disagreement_alignment_score",
            "conflict_arbitration_score",
            "workload_capacity_score",
            "team_memory_signal_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
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
class StrategyTeamMemorySignalWeightGateReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_reason_code("reason_code", self.reason_code)
        if _has_unsafe_value(self.reason_code):
            raise ValueError("reason_code has unsafe value")
        object.__setattr__(
            self,
            "count",
            _normalize_count_decimal("count", self.count),
        )
        _require_safety_flags("reason count", self)


@dataclass(frozen=True)
class StrategyTeamMemorySignalWeightGateReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    candidate_team_count: Decimal
    team_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_team_memory_signal_weight: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[StrategyTeamMemorySignalWeightGateReasonCodeCount, ...]
    rows: tuple[StrategyTeamMemorySignalWeightGateRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "input_count",
            "candidate_team_count",
            "team_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_team_memory_signal_weight",
            _normalize_unit_decimal(
                "average_team_memory_signal_weight",
                self.average_team_memory_signal_weight,
            ),
        )
        _require_member("status", self.status, STATUS_VALUES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_safety_flags("report", self)


def build_strategy_team_memory_signal_weight_gate_digest(
    signals: Iterable[object],
    *,
    config: StrategyTeamMemorySignalWeightGateDigestConfig,
    generated_at: datetime,
) -> StrategyTeamMemorySignalWeightGateReport:
    if type(config) is not StrategyTeamMemorySignalWeightGateDigestConfig:
        raise ValueError("config must be a StrategyTeamMemorySignalWeightGateDigestConfig")
    generated_at = _as_utc("generated_at", generated_at)
    _require_safety_flags("config", config)
    input_signals = _normalize_signals(signals)
    rows = tuple(
        sorted(
            (_row_from_signal(signal, config=config) for signal in input_signals),
            key=_row_sort_key,
        ),
    )
    return StrategyTeamMemorySignalWeightGateReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=_count_decimal(len(input_signals)),
        candidate_team_count=_count_decimal(len(rows)),
        team_count=_count_decimal(len({row.team_id for row in rows})),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        average_team_memory_signal_weight=_average_team_memory_signal_weight(rows),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def strategy_team_memory_signal_weight_gate_digest_payload(
    report: StrategyTeamMemorySignalWeightGateReport,
) -> dict[str, object]:
    if type(report) is not StrategyTeamMemorySignalWeightGateReport:
        raise ValueError("report must be a StrategyTeamMemorySignalWeightGateReport")
    _require_safety_flags("report", report)
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "input_count": _count_payload(report.input_count),
        "candidate_team_count": _count_payload(report.candidate_team_count),
        "team_count": _count_payload(report.team_count),
        "pass_count": _count_payload(report.pass_count),
        "watch_count": _count_payload(report.watch_count),
        "blocked_count": _count_payload(report.blocked_count),
        "average_team_memory_signal_weight": _decimal_payload(
            report.average_team_memory_signal_weight,
        ),
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "reason_code_counts": [
            _reason_code_count_payload(reason_count)
            for reason_count in report.reason_code_counts
        ],
        "rows": [_row_payload(row) for row in report.rows],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_payload(row: StrategyTeamMemorySignalWeightGateRow) -> dict[str, object]:
    _require_safety_flags("row", row)
    return {
        "candidate_id": row.candidate_id,
        "team_id": row.team_id,
        "category_id": row.category_id,
        "observed_at": row.observed_at.isoformat(),
        "redacted_public_reference": row.redacted_public_reference,
        "forecast_calibration_memory_score": _decimal_payload(
            row.forecast_calibration_memory_score,
        ),
        "resolution_accuracy_memory_score": _decimal_payload(
            row.resolution_accuracy_memory_score,
        ),
        "source_reliability_score": _decimal_payload(row.source_reliability_score),
        "information_velocity_score": _decimal_payload(row.information_velocity_score),
        "disagreement_pressure": _decimal_payload(row.disagreement_pressure),
        "disagreement_alignment_score": _decimal_payload(
            row.disagreement_alignment_score,
        ),
        "conflict_arbitration_score": _decimal_payload(row.conflict_arbitration_score),
        "workload_capacity_score": _decimal_payload(row.workload_capacity_score),
        "team_memory_signal_weight": _decimal_payload(row.team_memory_signal_weight),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _reason_code_count_payload(
    reason_count: StrategyTeamMemorySignalWeightGateReasonCodeCount,
) -> dict[str, object]:
    _require_safety_flags("reason count", reason_count)
    return {
        "reason_code": reason_count.reason_code,
        "count": _count_payload(reason_count.count),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_from_signal(
    signal: StrategyTeamMemorySignalWeightGateInput,
    *,
    config: StrategyTeamMemorySignalWeightGateDigestConfig,
) -> StrategyTeamMemorySignalWeightGateRow:
    disagreement_alignment_score = _subtract_from_one(signal.disagreement_pressure)
    team_memory_signal_weight = _team_memory_signal_weight(
        signal,
        disagreement_alignment_score=disagreement_alignment_score,
    )
    status = _row_status(
        signal,
        team_memory_signal_weight=team_memory_signal_weight,
        config=config,
    )
    return StrategyTeamMemorySignalWeightGateRow(
        candidate_id=signal.candidate_id,
        team_id=signal.team_id,
        category_id=signal.category_id,
        observed_at=signal.observed_at,
        redacted_public_reference=signal.public_reference,
        forecast_calibration_memory_score=signal.forecast_calibration_memory_score,
        resolution_accuracy_memory_score=signal.resolution_accuracy_memory_score,
        source_reliability_score=signal.source_reliability_score,
        information_velocity_score=signal.information_velocity_score,
        disagreement_pressure=signal.disagreement_pressure,
        disagreement_alignment_score=disagreement_alignment_score,
        conflict_arbitration_score=signal.conflict_arbitration_score,
        workload_capacity_score=signal.workload_capacity_score,
        team_memory_signal_weight=team_memory_signal_weight,
        status=status,
        reason_codes=_row_reason_codes(
            signal,
            status=status,
            team_memory_signal_weight=team_memory_signal_weight,
            config=config,
        ),
    )


def _team_memory_signal_weight(
    signal: StrategyTeamMemorySignalWeightGateInput,
    *,
    disagreement_alignment_score: Decimal,
) -> Decimal:
    memory_score = _average_decimal(
        (
            signal.forecast_calibration_memory_score,
            signal.resolution_accuracy_memory_score,
            signal.source_reliability_score,
        ),
    )
    support_score = _average_decimal(
        (
            signal.information_velocity_score,
            disagreement_alignment_score,
            signal.conflict_arbitration_score,
            signal.workload_capacity_score,
        ),
    )
    with localcontext(DECIMAL_CONTEXT):
        return (
            (memory_score * MEMORY_GROUP_WEIGHT)
            + (support_score * SUPPORT_GROUP_WEIGHT)
        ).quantize(QUANTUM)


def _row_status(
    signal: StrategyTeamMemorySignalWeightGateInput,
    *,
    team_memory_signal_weight: Decimal,
    config: StrategyTeamMemorySignalWeightGateDigestConfig,
) -> str:
    component_scores = _component_scores(signal)
    if (
        team_memory_signal_weight < config.min_watch_team_memory_signal_weight
        or any(score < config.min_component_watch_score for score in component_scores)
        or signal.disagreement_pressure > config.max_watch_disagreement_pressure
    ):
        return "blocked"
    if (
        team_memory_signal_weight >= config.min_pass_team_memory_signal_weight
        and all(score >= config.min_component_pass_score for score in component_scores)
        and signal.disagreement_pressure <= config.max_pass_disagreement_pressure
    ):
        return "pass"
    return "watch"


def _row_reason_codes(
    signal: StrategyTeamMemorySignalWeightGateInput,
    *,
    status: str,
    team_memory_signal_weight: Decimal,
    config: StrategyTeamMemorySignalWeightGateDigestConfig,
) -> tuple[str, ...]:
    reason_codes = [_terminal_reason_code(status)]
    if team_memory_signal_weight < config.min_watch_team_memory_signal_weight:
        reason_codes.append("team_memory_signal_weight_below_watch")
    elif team_memory_signal_weight < config.min_pass_team_memory_signal_weight:
        reason_codes.append("team_memory_signal_weight_below_pass")
    reason_codes.extend(
        _score_reason_codes(
            "forecast_calibration_memory",
            signal.forecast_calibration_memory_score,
            config=config,
        ),
    )
    reason_codes.extend(
        _score_reason_codes(
            "resolution_accuracy_memory",
            signal.resolution_accuracy_memory_score,
            config=config,
        ),
    )
    reason_codes.extend(
        _score_reason_codes(
            "source_reliability",
            signal.source_reliability_score,
            config=config,
        ),
    )
    reason_codes.extend(
        _score_reason_codes(
            "information_velocity",
            signal.information_velocity_score,
            config=config,
        ),
    )
    if signal.disagreement_pressure > config.max_watch_disagreement_pressure:
        reason_codes.append("disagreement_pressure_above_watch")
    elif signal.disagreement_pressure > config.max_pass_disagreement_pressure:
        reason_codes.append("disagreement_pressure_above_pass")
    reason_codes.extend(
        _score_reason_codes(
            "conflict_arbitration",
            signal.conflict_arbitration_score,
            config=config,
        ),
    )
    reason_codes.extend(
        _score_reason_codes(
            "workload_capacity",
            signal.workload_capacity_score,
            config=config,
        ),
    )
    return _normalize_reason_codes(tuple(reason_codes), require_nonempty=True)


def _score_reason_codes(
    prefix: str,
    score: Decimal,
    *,
    config: StrategyTeamMemorySignalWeightGateDigestConfig,
) -> tuple[str, ...]:
    if score < config.min_component_watch_score:
        return (f"{prefix}_below_watch",)
    if score < config.min_component_pass_score:
        return (f"{prefix}_below_pass",)
    return ()


def _terminal_reason_code(status: str) -> str:
    if status == "blocked":
        return "team_memory_signal_weight_blocked"
    if status == "watch":
        return "team_memory_signal_weight_watch"
    return "team_memory_signal_weight_pass"


def _component_scores(
    signal: StrategyTeamMemorySignalWeightGateInput,
) -> tuple[Decimal, ...]:
    return (
        signal.forecast_calibration_memory_score,
        signal.resolution_accuracy_memory_score,
        signal.source_reliability_score,
        signal.information_velocity_score,
        signal.conflict_arbitration_score,
        signal.workload_capacity_score,
    )


def _normalize_signals(
    signals: Iterable[object],
) -> tuple[StrategyTeamMemorySignalWeightGateInput, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must be an iterable")
    try:
        rows = tuple(signals)
    except TypeError as exc:
        raise ValueError("signals must be an iterable") from exc
    normalized = tuple(_signal_from_supplied_row(row) for row in rows)
    seen_keys: set[tuple[str, str]] = set()
    for row in normalized:
        key = (row.candidate_id, row.team_id)
        if key in seen_keys:
            raise ValueError("signals must be unique")
        seen_keys.add(key)
    return normalized


def _signal_from_supplied_row(
    row: object,
) -> StrategyTeamMemorySignalWeightGateInput:
    if type(row) is StrategyTeamMemorySignalWeightGateInput:
        _require_safety_flags("input", row)
        return row
    raise ValueError("signals must contain StrategyTeamMemorySignalWeightGateInput")


def _normalize_rows(
    rows: object,
) -> tuple[StrategyTeamMemorySignalWeightGateRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not StrategyTeamMemorySignalWeightGateRow:
            raise ValueError("rows must contain StrategyTeamMemorySignalWeightGateRow")
        _require_safety_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return normalized


def _normalize_reason_code_counts(
    counts: object,
) -> tuple[StrategyTeamMemorySignalWeightGateReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized = tuple(counts)
    for count in normalized:
        if type(count) is not StrategyTeamMemorySignalWeightGateReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason code counts")
        _require_safety_flags("reason count", count)
    if normalized != tuple(sorted(normalized, key=_reason_count_sort_key)):
        raise ValueError("reason_code_counts must be deterministically sorted")
    return normalized


def _row_sort_key(
    row: StrategyTeamMemorySignalWeightGateRow,
) -> tuple[int, Decimal, str, str, str]:
    return (
        STATUS_SORT_PRIORITY[row.status],
        row.team_memory_signal_weight,
        row.team_id,
        row.candidate_id,
        row.category_id,
    )


def _reason_count_sort_key(
    reason_count: StrategyTeamMemorySignalWeightGateReasonCodeCount,
) -> tuple[Decimal, tuple[int, str]]:
    return (-reason_count.count, _reason_sort_key(reason_count.reason_code))


def _status_count(
    rows: tuple[StrategyTeamMemorySignalWeightGateRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _average_team_memory_signal_weight(
    rows: tuple[StrategyTeamMemorySignalWeightGateRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _ratio_decimal(
        _sum_decimal(row.team_memory_signal_weight for row in rows),
        _count_decimal(len(rows)),
    )


def _report_status(rows: tuple[StrategyTeamMemorySignalWeightGateRow, ...]) -> str:
    if not rows or any(row.status == "blocked" for row in rows):
        return "blocked"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[StrategyTeamMemorySignalWeightGateRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    observed: set[str] = set()
    for row in rows:
        observed.update(row.reason_codes)
    selected = [
        reason_code
        for reason_code in REPORT_REASON_PRIORITY
        if reason_code in observed
    ]
    extras = sorted(observed.difference(REPORT_REASON_PRIORITY))
    return tuple((*selected, *extras))


def _reason_code_counts(
    rows: tuple[StrategyTeamMemorySignalWeightGateRow, ...],
) -> tuple[StrategyTeamMemorySignalWeightGateReasonCodeCount, ...]:
    if not rows:
        return (
            StrategyTeamMemorySignalWeightGateReasonCodeCount(
                reason_code=EMPTY_REASON_CODE,
                count=_count_decimal(1),
            ),
        )
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        sorted(
            (
                StrategyTeamMemorySignalWeightGateReasonCodeCount(
                    reason_code=reason_code,
                    count=_count_decimal(count),
                )
                for reason_code, count in counts.items()
            ),
            key=_reason_count_sort_key,
        ),
    )


def _validate_row(row: StrategyTeamMemorySignalWeightGateRow) -> None:
    if row.disagreement_alignment_score != _subtract_from_one(row.disagreement_pressure):
        raise ValueError("disagreement_alignment_score must match disagreement pressure")


def _validate_report(report: StrategyTeamMemorySignalWeightGateReport) -> None:
    if report.input_count != _count_decimal(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.candidate_team_count != _count_decimal(len(report.rows)):
        raise ValueError("candidate_team_count must match rows")
    if report.team_count != _count_decimal(len({row.team_id for row in report.rows})):
        raise ValueError("team_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if (
        report.average_team_memory_signal_weight
        != _average_team_memory_signal_weight(report.rows)
    ):
        raise ValueError("average_team_memory_signal_weight must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
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
            raise ValueError(f"unsafe field in {label}")


def _iter_keys(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_keys(asdict(value))
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("mapping keys must be strings")
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


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be a unit Decimal")
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


def _subtract_from_one(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (ONE - value).quantize(QUANTUM)


def _ratio_decimal(numerator: Decimal, denominator: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    return _ratio_decimal(_sum_decimal(values), _count_decimal(len(values)))


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        total = ZERO
        for value in values:
            total += value
        return total.quantize(QUANTUM)


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
    unique = tuple(dict.fromkeys(reason_codes))
    return tuple(sorted(unique, key=_reason_sort_key))


def _require_canonical_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    if value != value.lower() or value.strip() != value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    for part in value.split("_"):
        if not part or not part.isalnum() or part != part.lower():
            raise ValueError(f"{field_name} must contain canonical reason codes")


def _reason_sort_key(reason_code: str) -> tuple[int, str]:
    if reason_code in REPORT_REASON_PRIORITY:
        return (REPORT_REASON_PRIORITY.index(reason_code), reason_code)
    return (len(REPORT_REASON_PRIORITY), reason_code)


def _redacted_reference(value: str) -> str:
    digest = sha256(value.encode("utf-8")).hexdigest()[:16]
    return f"reference_{digest}"


def _require_redacted_reference(value: object) -> None:
    _require_canonical_string("redacted_public_reference", value)
    if not value.startswith("reference_"):
        raise ValueError("redacted_public_reference must be redacted")
    if _has_unsafe_value(value):
        raise ValueError("redacted_public_reference has unsafe value")


def _has_unsafe_value(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_VALUE_FRAGMENTS)


def _decimal_payload(value: Decimal) -> str:
    return format(_normalize_decimal("payload decimal", value), "f")


def _count_payload(value: Decimal) -> str:
    return str(int(_normalize_count_decimal("payload count", value)))
