"""Pure cross-team signal reconciliation report."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_RESEARCH_STRATEGY_CROSS_TEAM_SIGNAL_RECONCILIATION_CONFIG_VERSION = (
    "research-strategy-cross-team-signal-reconciliation-report-v1"
)

_COUNT_QUANTUM = Decimal("1")
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_TWO = Decimal("2.000000")
_SIX = Decimal("6.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_STATUSES = ("block", "watch", "pass")
_STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}
_DIRECTIONS = ("oppose", "neutral", "support")
_FLAG_NAMES = ("paper_only", "report_only", "readonly")
_HEX_CHARS = frozenset("0123456789abcdef")
_BLOCK_REASONS = frozenset(
    (
        "team_coverage_block",
        "cross_team_conflict_block",
        "signal_strength_block",
        "source_authority_block",
        "calibration_history_block",
        "cost_drag_block",
        "liquidity_reliability_block",
        "resolution_clarity_block",
        "review_readiness_block",
    ),
)
_PASS_REASONS = frozenset(("cross_team_signal_reconciliation_pass",))
_REASON_PRIORITY = (
    "team_coverage_block",
    "cross_team_conflict_block",
    "cross_team_conflict_watch",
    "signal_strength_block",
    "signal_strength_watch",
    "source_authority_block",
    "source_authority_watch",
    "calibration_history_block",
    "calibration_history_watch",
    "cost_drag_block",
    "cost_drag_watch",
    "liquidity_reliability_block",
    "liquidity_reliability_watch",
    "resolution_clarity_block",
    "resolution_clarity_watch",
    "review_readiness_block",
    "review_readiness_watch",
    "cross_team_signal_reconciliation_pass",
    "cross_team_signal_reconciliation_empty",
)
_UNSAFE_TEXT_FRAGMENTS = (
    "can" "didate",
    "market" "_" "id",
    "market" "_" "slug",
    "quest" "ion",
    "http" "://",
    "http" "s://",
    "post" "gres://",
    "data" "base",
    "dsn",
    "net" "work",
    "recommend" "ation",
    "exec" "ution",
    "source" "_" "url",
    "source" "_" "text",
    "table",
    "table" "_" "name",
    "raw" "_" "text",
    "tok" "en",
    "sec" "ret",
    "pass" "word",
    "cred" "ential",
    "private" "_" "key",
    "api" "_" "key",
    "bear" "er",
    "wal" "let",
    "or" "der",
    "tra" "de",
    "li" "ve",
    "pos" "ition",
    "siz" "ing",
)


@dataclass(frozen=True)
class ResearchStrategyCrossTeamSignalReconciliationConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_CROSS_TEAM_SIGNAL_RECONCILIATION_CONFIG_VERSION
    )
    team_count_floor: Decimal = Decimal("2")
    signal_strength_pass_floor: Decimal = Decimal("0.650000")
    source_authority_pass_floor: Decimal = Decimal("0.700000")
    calibration_history_pass_floor: Decimal = Decimal("0.700000")
    cost_drag_watch_ceiling: Decimal = Decimal("0.300000")
    cost_drag_block_ceiling: Decimal = Decimal("0.600000")
    liquidity_reliability_watch_floor: Decimal = Decimal("0.450000")
    liquidity_reliability_pass_floor: Decimal = Decimal("0.700000")
    resolution_clarity_watch_floor: Decimal = Decimal("0.450000")
    resolution_clarity_pass_floor: Decimal = Decimal("0.700000")
    review_readiness_watch_floor: Decimal = Decimal("0.450000")
    review_readiness_pass_floor: Decimal = Decimal("0.700000")
    conflict_pressure_watch_threshold: Decimal = Decimal("0.250000")
    conflict_pressure_block_threshold: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyCrossTeamSignalReconciliationConfig,
            "config",
        )
        _require_public_text("config_version", self.config_version)
        object.__setattr__(
            self,
            "team_count_floor",
            _normalize_positive_count("team_count_floor", self.team_count_floor),
        )
        for field_name in (
            "signal_strength_pass_floor",
            "source_authority_pass_floor",
            "calibration_history_pass_floor",
            "cost_drag_watch_ceiling",
            "cost_drag_block_ceiling",
            "liquidity_reliability_watch_floor",
            "liquidity_reliability_pass_floor",
            "resolution_clarity_watch_floor",
            "resolution_clarity_pass_floor",
            "review_readiness_watch_floor",
            "review_readiness_pass_floor",
            "conflict_pressure_watch_threshold",
            "conflict_pressure_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        if self.cost_drag_watch_ceiling > self.cost_drag_block_ceiling:
            raise ValueError(
                "cost_drag_watch_ceiling must not exceed cost_drag_block_ceiling",
            )
        if (
            self.liquidity_reliability_watch_floor
            > self.liquidity_reliability_pass_floor
        ):
            raise ValueError(
                "liquidity_reliability_watch_floor must not exceed "
                "liquidity_reliability_pass_floor",
            )
        if self.resolution_clarity_watch_floor > self.resolution_clarity_pass_floor:
            raise ValueError(
                "resolution_clarity_watch_floor must not exceed "
                "resolution_clarity_pass_floor",
            )
        if self.review_readiness_watch_floor > self.review_readiness_pass_floor:
            raise ValueError(
                "review_readiness_watch_floor must not exceed "
                "review_readiness_pass_floor",
            )
        if (
            self.conflict_pressure_watch_threshold
            > self.conflict_pressure_block_threshold
        ):
            raise ValueError(
                "conflict_pressure_watch_threshold must not exceed "
                "conflict_pressure_block_threshold",
            )
        require_paper_only_flags("cross team signal reconciliation config", self)


@dataclass(frozen=True)
class ResearchStrategyCrossTeamSignalInput:
    signal_ref: str
    team_code: str
    signal_direction: str
    signal_strength: Decimal
    source_authority: Decimal
    calibration_history: Decimal
    cost_drag: Decimal
    liquidity_reliability: Decimal
    resolution_clarity: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyCrossTeamSignalInput, "signal")
        _require_public_text("signal_ref", self.signal_ref)
        _require_public_text("team_code", self.team_code)
        _require_direction("signal_direction", self.signal_direction)
        for field_name in (
            "signal_strength",
            "source_authority",
            "calibration_history",
            "cost_drag",
            "liquidity_reliability",
            "resolution_clarity",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("cross team signal input", self)


@dataclass(frozen=True)
class ResearchStrategyCrossTeamSignalReconciliationRow:
    signal_ref: str
    team_code: str
    signal_direction: str
    signal_strength: Decimal
    source_authority: Decimal
    calibration_history: Decimal
    cost_drag: Decimal
    liquidity_reliability: Decimal
    resolution_clarity: Decimal
    authority_calibrated_strength: Decimal
    cost_adjusted_liquidity_score: Decimal
    review_readiness_score: Decimal
    opposing_signal_pressure: Decimal
    status: str
    reason_codes: tuple[str, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyCrossTeamSignalReconciliationRow,
            "row",
        )
        _require_public_text("signal_ref", self.signal_ref)
        _require_public_text("team_code", self.team_code)
        _require_direction("signal_direction", self.signal_direction)
        for field_name in (
            "signal_strength",
            "source_authority",
            "calibration_history",
            "cost_drag",
            "liquidity_reliability",
            "resolution_clarity",
            "authority_calibrated_strength",
            "cost_adjusted_liquidity_score",
            "review_readiness_score",
            "opposing_signal_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes("reason_codes", self.reason_codes),
        )
        _require_digest("validation_digest", self.validation_digest)
        _validate_row(self)
        require_paper_only_flags("cross team signal reconciliation row", self)


@dataclass(frozen=True)
class ResearchStrategyCrossTeamSignalReconciliationReport:
    generated_at: datetime
    config_version: str
    signal_count: Decimal
    team_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    conflict_pressure_score: Decimal
    min_review_readiness_score: Decimal | None
    report_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchStrategyCrossTeamSignalReconciliationRow, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyCrossTeamSignalReconciliationReport,
            "report",
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_text("config_version", self.config_version)
        for field_name in (
            "signal_count",
            "team_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "conflict_pressure_score",
            _normalize_unit_decimal(
                "conflict_pressure_score",
                self.conflict_pressure_score,
            ),
        )
        if self.min_review_readiness_score is not None:
            object.__setattr__(
                self,
                "min_review_readiness_score",
                _normalize_unit_decimal(
                    "min_review_readiness_score",
                    self.min_review_readiness_score,
                ),
            )
        _require_status("report_status", self.report_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_digest("validation_digest", self.validation_digest)
        _validate_report(self)
        require_paper_only_flags("cross team signal reconciliation report", self)


def build_research_strategy_cross_team_signal_reconciliation_report(
    signals: Iterable[ResearchStrategyCrossTeamSignalInput],
    *,
    config: ResearchStrategyCrossTeamSignalReconciliationConfig,
    generated_at: datetime,
) -> ResearchStrategyCrossTeamSignalReconciliationReport:
    if type(config) is not ResearchStrategyCrossTeamSignalReconciliationConfig:
        raise ValueError(
            "config must be a ResearchStrategyCrossTeamSignalReconciliationConfig",
        )
    require_paper_only_flags("cross team signal reconciliation config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_signals = _normalize_signals(signals)
    readiness_by_ref = {
        item.signal_ref: _review_readiness_score(item) for item in normalized_signals
    }
    direction_by_ref = {
        item.signal_ref: item.signal_direction for item in normalized_signals
    }
    conflict_pressure_score = _conflict_pressure_score(
        normalized_signals,
        readiness_by_ref,
    )
    team_count = _count(len({item.team_code for item in normalized_signals}))
    rows = tuple(
        sorted(
            (
                _row_from_signal(
                    item,
                    config=config,
                    team_count=team_count,
                    readiness_by_ref=readiness_by_ref,
                    direction_by_ref=direction_by_ref,
                )
                for item in normalized_signals
            ),
            key=_row_sort_key,
        ),
    )
    report_values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "signal_count": _count(len(rows)),
        "team_count": team_count,
        "pass_count": _row_status_count(rows, "pass"),
        "watch_count": _row_status_count(rows, "watch"),
        "block_count": _row_status_count(rows, "block"),
        "conflict_pressure_score": conflict_pressure_score,
        "min_review_readiness_score": (
            None if not rows else min(row.review_readiness_score for row in rows)
        ),
        "report_status": _report_status(rows),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyCrossTeamSignalReconciliationReport(
        **report_values,
        validation_digest=_validation_digest(report_values),
    )


def research_strategy_cross_team_signal_reconciliation_report_payload(
    report: ResearchStrategyCrossTeamSignalReconciliationReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyCrossTeamSignalReconciliationReport:
        require_paper_only_flags("cross team signal reconciliation report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchStrategyCrossTeamSignalReconciliationReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be an object")
    _reject_unsafe_payload(payload)
    require_paper_only_flags(
        "cross team signal reconciliation payload",
        _PayloadFlags(payload),
    )
    return payload


@dataclass(frozen=True)
class _PayloadFlags:
    payload: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.payload.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.payload.get("report_only")

    @property
    def readonly(self) -> object:
        return self.payload.get("readonly")


def _normalize_signals(
    signals: Iterable[ResearchStrategyCrossTeamSignalInput],
) -> tuple[ResearchStrategyCrossTeamSignalInput, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must be an iterable")
    try:
        items = tuple(signals)
    except TypeError as exc:
        raise ValueError("signals must be an iterable") from exc
    seen: set[str] = set()
    for item in items:
        if type(item) is not ResearchStrategyCrossTeamSignalInput:
            raise ValueError(
                "signals must contain ResearchStrategyCrossTeamSignalInput",
            )
        require_paper_only_flags("cross team signal input", item)
        if item.signal_ref in seen:
            raise ValueError("signal_ref values must be unique")
        seen.add(item.signal_ref)
    return items


def _row_from_signal(
    signal: ResearchStrategyCrossTeamSignalInput,
    *,
    config: ResearchStrategyCrossTeamSignalReconciliationConfig,
    team_count: Decimal,
    readiness_by_ref: dict[str, Decimal],
    direction_by_ref: dict[str, str],
) -> ResearchStrategyCrossTeamSignalReconciliationRow:
    authority_calibrated_strength = _authority_calibrated_strength(signal)
    cost_adjusted_liquidity_score = _cost_adjusted_liquidity_score(signal)
    review_readiness_score = _review_readiness_score(signal)
    opposing_signal_pressure = _opposing_signal_pressure(
        signal,
        readiness_by_ref,
        direction_by_ref,
    )
    reason_codes = _row_reason_codes(
        signal,
        config=config,
        team_count=team_count,
        review_readiness_score=review_readiness_score,
        opposing_signal_pressure=opposing_signal_pressure,
    )
    row_values = {
        "signal_ref": signal.signal_ref,
        "team_code": signal.team_code,
        "signal_direction": signal.signal_direction,
        "signal_strength": signal.signal_strength,
        "source_authority": signal.source_authority,
        "calibration_history": signal.calibration_history,
        "cost_drag": signal.cost_drag,
        "liquidity_reliability": signal.liquidity_reliability,
        "resolution_clarity": signal.resolution_clarity,
        "authority_calibrated_strength": authority_calibrated_strength,
        "cost_adjusted_liquidity_score": cost_adjusted_liquidity_score,
        "review_readiness_score": review_readiness_score,
        "opposing_signal_pressure": opposing_signal_pressure,
        "status": _status_from_reason_codes(reason_codes),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyCrossTeamSignalReconciliationRow(
        **row_values,
        validation_digest=_validation_digest(row_values),
    )


def _row_reason_codes(
    signal: ResearchStrategyCrossTeamSignalInput,
    *,
    config: ResearchStrategyCrossTeamSignalReconciliationConfig,
    team_count: Decimal,
    review_readiness_score: Decimal,
    opposing_signal_pressure: Decimal,
) -> tuple[str, ...]:
    block_reasons: list[str] = []
    watch_reasons: list[str] = []
    if team_count < config.team_count_floor:
        block_reasons.append("team_coverage_block")
    if signal.signal_direction != "neutral":
        if opposing_signal_pressure >= config.conflict_pressure_block_threshold:
            block_reasons.append("cross_team_conflict_block")
        elif opposing_signal_pressure >= config.conflict_pressure_watch_threshold:
            watch_reasons.append("cross_team_conflict_watch")
    if signal.signal_strength < config.review_readiness_watch_floor:
        block_reasons.append("signal_strength_block")
    elif signal.signal_strength < config.signal_strength_pass_floor:
        watch_reasons.append("signal_strength_watch")
    if signal.source_authority < config.review_readiness_watch_floor:
        block_reasons.append("source_authority_block")
    elif signal.source_authority < config.source_authority_pass_floor:
        watch_reasons.append("source_authority_watch")
    if signal.calibration_history < config.review_readiness_watch_floor:
        block_reasons.append("calibration_history_block")
    elif signal.calibration_history < config.calibration_history_pass_floor:
        watch_reasons.append("calibration_history_watch")
    if signal.cost_drag >= config.cost_drag_block_ceiling:
        block_reasons.append("cost_drag_block")
    elif signal.cost_drag > config.cost_drag_watch_ceiling:
        watch_reasons.append("cost_drag_watch")
    if signal.liquidity_reliability < config.liquidity_reliability_watch_floor:
        block_reasons.append("liquidity_reliability_block")
    elif signal.liquidity_reliability < config.liquidity_reliability_pass_floor:
        watch_reasons.append("liquidity_reliability_watch")
    if signal.resolution_clarity < config.resolution_clarity_watch_floor:
        block_reasons.append("resolution_clarity_block")
    elif signal.resolution_clarity < config.resolution_clarity_pass_floor:
        watch_reasons.append("resolution_clarity_watch")
    if review_readiness_score < config.review_readiness_watch_floor:
        block_reasons.append("review_readiness_block")
    elif review_readiness_score < config.review_readiness_pass_floor:
        watch_reasons.append("review_readiness_watch")
    reason_codes = tuple(block_reasons + watch_reasons)
    if not reason_codes:
        reason_codes = ("cross_team_signal_reconciliation_pass",)
    return _normalize_row_reason_codes("reason_codes", reason_codes)


def _authority_calibrated_strength(
    signal: ResearchStrategyCrossTeamSignalInput,
) -> Decimal:
    authority_calibration_average = _ratio(
        signal.source_authority + signal.calibration_history,
        _TWO,
    )
    return _quantize(signal.signal_strength * authority_calibration_average)


def _cost_adjusted_liquidity_score(
    signal: ResearchStrategyCrossTeamSignalInput,
) -> Decimal:
    drag_clearance = _quantize(_ONE - signal.cost_drag)
    return min(signal.liquidity_reliability, drag_clearance)


def _review_readiness_score(
    signal: ResearchStrategyCrossTeamSignalInput,
) -> Decimal:
    return _ratio(
        _sum_decimal(
            (
                signal.signal_strength,
                signal.source_authority,
                signal.calibration_history,
                _ONE - signal.cost_drag,
                signal.liquidity_reliability,
                signal.resolution_clarity,
            ),
        ),
        _SIX,
    )


def _conflict_pressure_score(
    signals: tuple[ResearchStrategyCrossTeamSignalInput, ...],
    readiness_by_ref: dict[str, Decimal],
) -> Decimal:
    support_readiness = tuple(
        readiness_by_ref[item.signal_ref]
        for item in signals
        if item.signal_direction == "support"
    )
    oppose_readiness = tuple(
        readiness_by_ref[item.signal_ref]
        for item in signals
        if item.signal_direction == "oppose"
    )
    if not support_readiness or not oppose_readiness:
        return _ZERO
    return min(max(support_readiness), max(oppose_readiness))


def _opposing_signal_pressure(
    signal: ResearchStrategyCrossTeamSignalInput,
    readiness_by_ref: dict[str, Decimal],
    direction_by_ref: dict[str, str],
) -> Decimal:
    if signal.signal_direction == "neutral":
        return _ZERO
    opposing_direction = "oppose" if signal.signal_direction == "support" else "support"
    opposing_scores = tuple(
        readiness
        for signal_ref, readiness in readiness_by_ref.items()
        if signal_ref != signal.signal_ref
        and direction_by_ref[signal_ref] == opposing_direction
    )
    if not opposing_scores:
        return _ZERO
    return max(opposing_scores)


def _row_status_count(
    rows: tuple[ResearchStrategyCrossTeamSignalReconciliationRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason in _BLOCK_REASONS for reason in reason_codes):
        return "block"
    if reason_codes == ("cross_team_signal_reconciliation_pass",):
        return "pass"
    return "watch"


def _report_status(
    rows: tuple[ResearchStrategyCrossTeamSignalReconciliationRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyCrossTeamSignalReconciliationRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("cross_team_signal_reconciliation_empty",)
    return _normalize_report_reason_codes(
        "reason_codes",
        tuple(reason for row in rows for reason in row.reason_codes),
    )


def _normalize_rows(
    rows: object,
) -> tuple[ResearchStrategyCrossTeamSignalReconciliationRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not ResearchStrategyCrossTeamSignalReconciliationRow:
            raise ValueError(
                "rows must contain ResearchStrategyCrossTeamSignalReconciliationRow",
            )
        require_paper_only_flags("cross team signal reconciliation row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    return normalized


def _validate_row(row: ResearchStrategyCrossTeamSignalReconciliationRow) -> None:
    expected_authority_calibrated_strength = _authority_calibrated_strength(
        _input_from_row(row),
    )
    if row.authority_calibrated_strength != expected_authority_calibrated_strength:
        raise ValueError("authority_calibrated_strength must match inputs")
    if row.cost_adjusted_liquidity_score != _cost_adjusted_liquidity_score(
        _input_from_row(row),
    ):
        raise ValueError("cost_adjusted_liquidity_score must match inputs")
    if row.review_readiness_score != _review_readiness_score(_input_from_row(row)):
        raise ValueError("review_readiness_score must match inputs")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.validation_digest != _validation_digest(_row_digest_values(row)):
        raise ValueError("validation_digest must match row payload")


def _validate_report(
    report: ResearchStrategyCrossTeamSignalReconciliationReport,
) -> None:
    if report.signal_count != _count(len(report.rows)):
        raise ValueError("signal_count must match rows")
    if report.team_count != _count(len({row.team_code for row in report.rows})):
        raise ValueError("team_count must match rows")
    if report.pass_count != _row_status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _row_status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _row_status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.conflict_pressure_score != _report_conflict_pressure_score(report.rows):
        raise ValueError("conflict_pressure_score must match rows")
    expected_min = (
        None if not report.rows else min(row.review_readiness_score for row in report.rows)
    )
    if report.min_review_readiness_score != expected_min:
        raise ValueError("min_review_readiness_score must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.validation_digest != _validation_digest(_report_digest_values(report)):
        raise ValueError("validation_digest must match report payload")


def _input_from_row(
    row: ResearchStrategyCrossTeamSignalReconciliationRow,
) -> ResearchStrategyCrossTeamSignalInput:
    return ResearchStrategyCrossTeamSignalInput(
        signal_ref=row.signal_ref,
        team_code=row.team_code,
        signal_direction=row.signal_direction,
        signal_strength=row.signal_strength,
        source_authority=row.source_authority,
        calibration_history=row.calibration_history,
        cost_drag=row.cost_drag,
        liquidity_reliability=row.liquidity_reliability,
        resolution_clarity=row.resolution_clarity,
        paper_only=row.paper_only,
        report_only=row.report_only,
        readonly=row.readonly,
    )


def _report_conflict_pressure_score(
    rows: tuple[ResearchStrategyCrossTeamSignalReconciliationRow, ...],
) -> Decimal:
    support_readiness = tuple(
        row.review_readiness_score for row in rows if row.signal_direction == "support"
    )
    oppose_readiness = tuple(
        row.review_readiness_score for row in rows if row.signal_direction == "oppose"
    )
    if not support_readiness or not oppose_readiness:
        return _ZERO
    return min(max(support_readiness), max(oppose_readiness))


def _row_digest_values(
    row: ResearchStrategyCrossTeamSignalReconciliationRow,
) -> dict[str, Any]:
    return {
        "signal_ref": row.signal_ref,
        "team_code": row.team_code,
        "signal_direction": row.signal_direction,
        "signal_strength": row.signal_strength,
        "source_authority": row.source_authority,
        "calibration_history": row.calibration_history,
        "cost_drag": row.cost_drag,
        "liquidity_reliability": row.liquidity_reliability,
        "resolution_clarity": row.resolution_clarity,
        "authority_calibrated_strength": row.authority_calibrated_strength,
        "cost_adjusted_liquidity_score": row.cost_adjusted_liquidity_score,
        "review_readiness_score": row.review_readiness_score,
        "opposing_signal_pressure": row.opposing_signal_pressure,
        "status": row.status,
        "reason_codes": row.reason_codes,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _report_digest_values(
    report: ResearchStrategyCrossTeamSignalReconciliationReport,
) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "signal_count": report.signal_count,
        "team_count": report.team_count,
        "pass_count": report.pass_count,
        "watch_count": report.watch_count,
        "block_count": report.block_count,
        "conflict_pressure_score": report.conflict_pressure_score,
        "min_review_readiness_score": report.min_review_readiness_score,
        "report_status": report.report_status,
        "reason_codes": report.reason_codes,
        "rows": report.rows,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _row_sort_key(
    row: ResearchStrategyCrossTeamSignalReconciliationRow,
) -> tuple[int, Decimal, Decimal, str]:
    return (
        _STATUS_WEIGHT[row.status],
        -row.opposing_signal_pressure,
        row.review_readiness_score,
        row.signal_ref,
    )


def _normalize_row_reason_codes(name: str, values: object) -> tuple[str, ...]:
    codes = _normalize_public_reason_codes(name, values)
    if not codes:
        raise ValueError(f"{name} must not be empty")
    if codes == ("cross_team_signal_reconciliation_pass",):
        return codes
    if any(code in _PASS_REASONS for code in codes):
        raise ValueError(f"{name} pass reason must stand alone")
    return codes


def _normalize_report_reason_codes(name: str, values: object) -> tuple[str, ...]:
    codes = _normalize_public_reason_codes(name, values)
    if not codes:
        raise ValueError(f"{name} must not be empty")
    if codes == ("cross_team_signal_reconciliation_empty",):
        return codes
    if "cross_team_signal_reconciliation_empty" in codes:
        raise ValueError(f"{name} empty reason must stand alone")
    return codes


def _normalize_public_reason_codes(name: str, values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be an iterable")
    try:
        codes = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{name} must be an iterable") from exc
    for code in codes:
        _require_public_text(name, code)
        compact_code = "".join(part for part in code if part != "_")
        if not compact_code.isalnum() or code.lower() != code:
            raise ValueError(f"{name} must contain lowercase snake case values")
    return tuple(sorted(dict.fromkeys(codes), key=_reason_sort_key))


def _reason_sort_key(reason_code: str) -> tuple[int, str]:
    if reason_code in _REASON_PRIORITY:
        return (_REASON_PRIORITY.index(reason_code), reason_code)
    return (len(_REASON_PRIORITY), reason_code)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value).quantize(_COUNT_QUANTUM)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = _ZERO
    for value in values:
        total += _normalize_decimal("sum value", value)
    return _quantize(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    denominator = _normalize_decimal("denominator", denominator)
    if denominator <= _ZERO:
        raise ValueError("denominator must be positive")
    numerator = _normalize_decimal("numerator", numerator)
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _normalize_positive_count(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be an integer")
    return normalized.quantize(_COUNT_QUANTUM)


def _normalize_unit_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return _quantize(normalized)


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_direction(name: str, value: object) -> None:
    _require_public_text(name, value)
    if value not in _DIRECTIONS:
        raise ValueError(f"{name} must be oppose, neutral, or support")


def _require_status(name: str, value: object) -> None:
    _require_public_text(name, value)
    if value not in _STATUSES:
        raise ValueError(f"{name} must be block, watch, or pass")


def _require_text(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a non-empty canonical string")


def _require_public_text(name: str, value: object) -> None:
    _require_text(name, value)
    normalized = value.lower()
    if any(fragment in normalized for fragment in _UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{name} contains unsafe public text")


def _require_digest(name: str, value: object) -> None:
    _require_text(name, value)
    if len(value) != 64 or any(char not in _HEX_CHARS for char in value):
        raise ValueError(f"{name} must be a sha256 hex digest")


def _validation_digest(values: dict[str, Any]) -> str:
    ready = _json_ready(values)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is bool:
        return value
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return format(value, "f")
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is str:
        _require_public_text("JSON value", value)
        return value
    if type(value) in (int, float):
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _require_public_text("JSON object key", key)
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_payload(value: Any) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("unsafe payload key")
            if _has_unsafe_fragment(key):
                raise ValueError("unsafe payload key")
            if key in _FLAG_NAMES and item is not True:
                raise ValueError(f"{key} must be True in payload")
            _reject_unsafe_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_payload(item)
        return
    if type(value) in (int, float):
        raise ValueError("payload numeric values must use Decimal strings")
    if isinstance(value, datetime):
        if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("payload datetime values must be timezone-aware")
    if type(value) is str and _has_unsafe_fragment(value):
        raise ValueError("unsafe payload value")


def _has_unsafe_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in _UNSAFE_TEXT_FRAGMENTS)


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_CROSS_TEAM_SIGNAL_RECONCILIATION_CONFIG_VERSION",
    "ResearchStrategyCrossTeamSignalInput",
    "ResearchStrategyCrossTeamSignalReconciliationConfig",
    "ResearchStrategyCrossTeamSignalReconciliationReport",
    "ResearchStrategyCrossTeamSignalReconciliationRow",
    "build_research_strategy_cross_team_signal_reconciliation_report",
    "research_strategy_cross_team_signal_reconciliation_report_payload",
)
