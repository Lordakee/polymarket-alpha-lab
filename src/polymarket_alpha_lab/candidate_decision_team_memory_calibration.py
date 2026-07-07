"""Pure team-memory calibration reducer for settled paper candidate results."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    UNSAFE_SURFACE_FIELD_FRAGMENTS,
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)
from polymarket_alpha_lab.team_taxonomy import require_team_id


DEFAULT_CANDIDATE_DECISION_TEAM_MEMORY_CALIBRATION_CONFIG_VERSION = (
    "candidate-decision-team-memory-calibration-v0"
)

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCKED_STATUS = "blocked"
STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCKED_STATUS)

PASS_ROW_REASON = "team_calibration_error_pass"
WATCH_ROW_REASON = "team_calibration_error_watch"
BLOCKED_ROW_REASON = "team_calibration_error_blocked"
ROW_REASON_CODES = (PASS_ROW_REASON, WATCH_ROW_REASON, BLOCKED_ROW_REASON)

CLEAR_REPORT_REASON = "candidate_decision_team_memory_calibration_clear"
WATCH_REPORT_REASON = "candidate_decision_team_memory_calibration_watch"
BLOCKED_REPORT_REASON = "candidate_decision_team_memory_calibration_blocked"
BLOCKED_PRESENT_REPORT_REASON = "team_calibration_error_blocked_present"
WATCH_PRESENT_REPORT_REASON = "team_calibration_error_watch_present"
REPORT_REASON_CODES = (
    CLEAR_REPORT_REASON,
    WATCH_REPORT_REASON,
    BLOCKED_REPORT_REASON,
    BLOCKED_PRESENT_REPORT_REASON,
    WATCH_PRESENT_REPORT_REASON,
)

NUMERIC_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
UTC_OFFSET = timedelta(0)
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)


@dataclass(frozen=True)
class CandidateDecisionTeamMemoryCalibrationConfig:
    config_version: str = (
        DEFAULT_CANDIDATE_DECISION_TEAM_MEMORY_CALIBRATION_CONFIG_VERSION
    )
    watch_mean_brier_error_at_or_above: Decimal = Decimal("0.010000")
    blocked_mean_brier_error_at_or_above: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_CANDIDATE_DECISION_TEAM_MEMORY_CALIBRATION_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the calibration config version")
        for field_name in (
            "watch_mean_brier_error_at_or_above",
            "blocked_mean_brier_error_at_or_above",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        require_paper_only_flags("CandidateDecisionTeamMemoryCalibrationConfig", self)
        reject_unsafe_surface_fields(
            "candidate decision team memory calibration config",
            self,
        )


@dataclass(frozen=True)
class CandidateDecisionTeamMemoryCalibrationInputRow:
    team_id: str
    redacted_candidate_ref: str
    redacted_market_ref: str
    forecast_probability: Decimal
    settled_outcome: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        object.__setattr__(
            self,
            "redacted_candidate_ref",
            _normalize_redacted_ref(
                "redacted_candidate_ref",
                self.redacted_candidate_ref,
            ),
        )
        object.__setattr__(
            self,
            "redacted_market_ref",
            _normalize_redacted_ref("redacted_market_ref", self.redacted_market_ref),
        )
        object.__setattr__(
            self,
            "forecast_probability",
            _normalize_ratio("forecast_probability", self.forecast_probability),
        )
        object.__setattr__(
            self,
            "settled_outcome",
            _normalize_settled_outcome(self.settled_outcome),
        )
        require_paper_only_flags(
            "CandidateDecisionTeamMemoryCalibrationInputRow",
            self,
        )
        reject_unsafe_surface_fields(
            "candidate decision team memory calibration input row",
            self,
        )
        _reject_unsafe_surface_values(
            "candidate decision team memory calibration input row",
            asdict(self),
        )


CandidateDecisionTeamMemoryCalibrationInput = (
    CandidateDecisionTeamMemoryCalibrationInputRow
)


@dataclass(frozen=True)
class CandidateDecisionTeamMemoryCalibrationTeamRow:
    team_rank: Decimal
    team_id: str
    settled_row_count: Decimal
    positive_outcome_count: Decimal
    negative_outcome_count: Decimal
    mean_forecast_probability: Decimal
    mean_outcome_value: Decimal
    mean_brier_error: Decimal
    max_brier_error: Decimal
    calibration_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "team_rank",
            _normalize_positive_decimal("team_rank", self.team_rank),
        )
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        for field_name in (
            "settled_row_count",
            "positive_outcome_count",
            "negative_outcome_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "mean_forecast_probability",
            "mean_outcome_value",
            "mean_brier_error",
            "max_brier_error",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("calibration_status", self.calibration_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_team_row(self)
        require_paper_only_flags(
            "CandidateDecisionTeamMemoryCalibrationTeamRow",
            self,
        )
        reject_unsafe_surface_fields(
            "candidate decision team memory calibration team row",
            self,
        )


@dataclass(frozen=True)
class CandidateDecisionTeamMemoryCalibrationReport:
    generated_at: datetime
    config_version: str
    input_row_count: Decimal
    team_count: Decimal
    blocked_team_count: Decimal
    watch_team_count: Decimal
    pass_team_count: Decimal
    mean_brier_error: Decimal
    max_team_mean_brier_error: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    team_rows: tuple[CandidateDecisionTeamMemoryCalibrationTeamRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_CANDIDATE_DECISION_TEAM_MEMORY_CALIBRATION_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the calibration config version")
        for field_name in (
            "input_row_count",
            "team_count",
            "blocked_team_count",
            "watch_team_count",
            "pass_team_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in ("mean_brier_error", "max_team_mean_brier_error"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("report_status", self.report_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(self, "team_rows", _normalize_team_rows(self.team_rows))
        _validate_report(self)
        require_paper_only_flags(
            "CandidateDecisionTeamMemoryCalibrationReport",
            self,
        )
        reject_unsafe_surface_fields(
            "candidate decision team memory calibration report",
            self,
        )


def build_candidate_decision_team_memory_calibration_report(
    rows: list[CandidateDecisionTeamMemoryCalibrationInputRow]
    | tuple[CandidateDecisionTeamMemoryCalibrationInputRow, ...],
    *,
    config: CandidateDecisionTeamMemoryCalibrationConfig,
    generated_at: datetime,
) -> CandidateDecisionTeamMemoryCalibrationReport:
    if type(config) is not CandidateDecisionTeamMemoryCalibrationConfig:
        raise ValueError(
            "config must be a CandidateDecisionTeamMemoryCalibrationConfig",
        )
    require_paper_only_flags("CandidateDecisionTeamMemoryCalibrationConfig", config)
    input_rows = _normalize_input_rows(rows)
    generated_at_utc = _as_utc("generated_at", generated_at)
    team_drafts = _team_drafts(input_rows, config=config)
    team_rows = tuple(
        _team_row(rank, draft)
        for rank, draft in enumerate(sorted(team_drafts, key=_team_draft_key), start=1)
    )
    return CandidateDecisionTeamMemoryCalibrationReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_row_count=_count_from_int(len(input_rows)),
        team_count=_count_from_int(len(team_rows)),
        blocked_team_count=_status_count(team_rows, BLOCKED_STATUS),
        watch_team_count=_status_count(team_rows, WATCH_STATUS),
        pass_team_count=_status_count(team_rows, PASS_STATUS),
        mean_brier_error=_mean_input_brier_error(input_rows),
        max_team_mean_brier_error=_max_team_mean_brier_error(team_rows),
        report_status=_report_status(team_rows),
        reason_codes=_report_reason_codes(team_rows),
        team_rows=team_rows,
    )


def candidate_decision_team_memory_calibration_report_to_jsonable(
    report: CandidateDecisionTeamMemoryCalibrationReport,
) -> dict[str, Any]:
    if type(report) is not CandidateDecisionTeamMemoryCalibrationReport:
        raise ValueError(
            "report must be a CandidateDecisionTeamMemoryCalibrationReport",
        )
    require_paper_only_flags("CandidateDecisionTeamMemoryCalibrationReport", report)
    _require_report_surface_flags(report)
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be an object")
    reject_unsafe_surface_fields(
        "candidate decision team memory calibration payload",
        payload,
    )
    _reject_unsafe_surface_values(
        "candidate decision team memory calibration payload",
        payload,
    )
    guarded = json_ready_no_floats(payload)
    if type(guarded) is not dict:
        raise ValueError("report payload must be an object")
    return guarded


def candidate_decision_team_memory_calibration_report_to_json(
    report: CandidateDecisionTeamMemoryCalibrationReport,
) -> str:
    return json.dumps(
        candidate_decision_team_memory_calibration_report_to_jsonable(report),
        sort_keys=True,
        separators=(",", ":"),
    )


def _require_report_surface_flags(
    report: CandidateDecisionTeamMemoryCalibrationReport,
) -> None:
    for row in report.team_rows:
        require_paper_only_flags("CandidateDecisionTeamMemoryCalibrationTeamRow", row)


def _normalize_input_rows(
    value: object,
) -> tuple[CandidateDecisionTeamMemoryCalibrationInputRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_keys: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not CandidateDecisionTeamMemoryCalibrationInputRow:
            raise ValueError(
                "rows must contain CandidateDecisionTeamMemoryCalibrationInputRow values",
            )
        require_paper_only_flags(
            "CandidateDecisionTeamMemoryCalibrationInputRow",
            row,
        )
        reject_unsafe_surface_fields(
            "candidate decision team memory calibration input row",
            row,
        )
        key = (row.team_id, row.redacted_candidate_ref, row.redacted_market_ref)
        if key in seen_keys:
            raise ValueError("rows must have unique team_id/redacted reference values")
        seen_keys.add(key)
    return rows


def _team_drafts(
    rows: tuple[CandidateDecisionTeamMemoryCalibrationInputRow, ...],
    *,
    config: CandidateDecisionTeamMemoryCalibrationConfig,
) -> tuple[
    tuple[str, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, str, tuple[str, ...]],
    ...,
]:
    team_ids = tuple(sorted({row.team_id for row in rows}))
    drafts: list[
        tuple[str, Decimal, Decimal, Decimal, Decimal, Decimal, str, tuple[str, ...]]
    ] = []
    for team_id in team_ids:
        team_rows = tuple(row for row in rows if row.team_id == team_id)
        count = _count_from_int(len(team_rows))
        positive_count = _count_from_int(
            sum(1 for row in team_rows if row.settled_outcome == ONE),
        )
        negative_count = count - positive_count
        mean_forecast = _mean_decimal(
            tuple(row.forecast_probability for row in team_rows),
        )
        mean_outcome = _mean_decimal(tuple(row.settled_outcome for row in team_rows))
        team_errors = tuple(_brier_error(row) for row in team_rows)
        mean_error = _mean_decimal(team_errors)
        max_error = _max_ratio(team_errors)
        status = _calibration_status(mean_error, config=config)
        drafts.append(
            (
                team_id,
                count,
                positive_count,
                negative_count,
                mean_forecast,
                mean_outcome,
                mean_error,
                max_error,
                status,
                (_row_reason_for_status(status),),
            ),
        )
    return tuple(drafts)


def _team_draft_key(
    draft: tuple[str, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, str, tuple[str, ...]],
) -> tuple[int, Decimal, str]:
    (
        team_id,
        _count,
        _positive_count,
        _negative_count,
        _mean_forecast,
        _mean_outcome,
        mean_error,
        _max_error,
        status,
        _reason_codes,
    ) = draft
    return (_status_severity(status), -mean_error, team_id)


def _team_row(
    rank: int,
    draft: tuple[str, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, str, tuple[str, ...]],
) -> CandidateDecisionTeamMemoryCalibrationTeamRow:
    (
        team_id,
        count,
        positive_count,
        negative_count,
        mean_forecast,
        mean_outcome,
        mean_error,
        max_error,
        status,
        reason_codes,
    ) = draft
    return CandidateDecisionTeamMemoryCalibrationTeamRow(
        team_rank=_count_from_int(rank),
        team_id=team_id,
        settled_row_count=count,
        positive_outcome_count=positive_count,
        negative_outcome_count=negative_count,
        mean_forecast_probability=mean_forecast,
        mean_outcome_value=mean_outcome,
        mean_brier_error=mean_error,
        max_brier_error=max_error,
        calibration_status=status,
        reason_codes=reason_codes,
    )


def _normalize_team_rows(
    value: object,
) -> tuple[CandidateDecisionTeamMemoryCalibrationTeamRow, ...]:
    if type(value) is not tuple:
        raise ValueError("team_rows must be a tuple")
    rows = tuple(value)
    seen_team_ids: set[str] = set()
    for index, row in enumerate(rows, start=1):
        if type(row) is not CandidateDecisionTeamMemoryCalibrationTeamRow:
            raise ValueError(
                "team_rows must contain CandidateDecisionTeamMemoryCalibrationTeamRow values",
            )
        require_paper_only_flags("CandidateDecisionTeamMemoryCalibrationTeamRow", row)
        if row.team_rank != _count_from_int(index):
            raise ValueError("team_rank must match row sequence")
        if row.team_id in seen_team_ids:
            raise ValueError("team_rows must have unique team_id values")
        seen_team_ids.add(row.team_id)
    return rows


def _validate_config(config: CandidateDecisionTeamMemoryCalibrationConfig) -> None:
    if config.blocked_mean_brier_error_at_or_above < (
        config.watch_mean_brier_error_at_or_above
    ):
        raise ValueError(
            "blocked_mean_brier_error_at_or_above must be at least watch threshold",
        )


def _validate_team_row(row: CandidateDecisionTeamMemoryCalibrationTeamRow) -> None:
    if row.settled_row_count <= ZERO:
        raise ValueError("settled_row_count must be positive")
    if row.positive_outcome_count + row.negative_outcome_count != row.settled_row_count:
        raise ValueError("outcome counts must match settled_row_count")
    if row.max_brier_error < row.mean_brier_error:
        raise ValueError("max_brier_error must be at least mean_brier_error")
    if row.reason_codes != (_row_reason_for_status(row.calibration_status),):
        raise ValueError("reason_codes must match calibration_status")


def _validate_report(report: CandidateDecisionTeamMemoryCalibrationReport) -> None:
    if report.team_count != _count_from_int(len(report.team_rows)):
        raise ValueError("team_count must match team_rows")
    if report.team_count > report.input_row_count:
        raise ValueError("team_count must not exceed input_row_count")
    if report.blocked_team_count != _status_count(report.team_rows, BLOCKED_STATUS):
        raise ValueError("blocked_team_count must match team_rows")
    if report.watch_team_count != _status_count(report.team_rows, WATCH_STATUS):
        raise ValueError("watch_team_count must match team_rows")
    if report.pass_team_count != _status_count(report.team_rows, PASS_STATUS):
        raise ValueError("pass_team_count must match team_rows")
    if (
        report.blocked_team_count + report.watch_team_count + report.pass_team_count
        != report.team_count
    ):
        raise ValueError("team status counts must match team_count")
    if report.input_row_count != _sum_team_counts(report.team_rows):
        raise ValueError("input_row_count must match team_rows")
    if report.mean_brier_error != _weighted_mean_team_error(report.team_rows):
        raise ValueError("mean_brier_error must match team_rows")
    if report.max_team_mean_brier_error != _max_team_mean_brier_error(report.team_rows):
        raise ValueError("max_team_mean_brier_error must match team_rows")
    if report.report_status != _report_status(report.team_rows):
        raise ValueError("report_status must match team_rows")
    if report.reason_codes != _report_reason_codes(report.team_rows):
        raise ValueError("reason_codes must match team_rows")
    if report.team_rows != tuple(sorted(report.team_rows, key=_team_row_key)):
        raise ValueError("team_rows must use deterministic sorting")


def _team_row_key(
    row: CandidateDecisionTeamMemoryCalibrationTeamRow,
) -> tuple[int, Decimal, str]:
    return (_status_severity(row.calibration_status), -row.mean_brier_error, row.team_id)


def _sum_team_counts(
    rows: tuple[CandidateDecisionTeamMemoryCalibrationTeamRow, ...],
) -> Decimal:
    total = ZERO
    for row in rows:
        total += row.settled_row_count
    return _normalize_nonnegative_integral_decimal("input_row_count", total)


def _weighted_mean_team_error(
    rows: tuple[CandidateDecisionTeamMemoryCalibrationTeamRow, ...],
) -> Decimal:
    total_count = _sum_team_counts(rows)
    if total_count == ZERO:
        return ZERO
    total = ZERO
    for row in rows:
        total += row.mean_brier_error * row.settled_row_count
    return _safe_ratio(total, total_count)


def _mean_input_brier_error(
    rows: tuple[CandidateDecisionTeamMemoryCalibrationInputRow, ...],
) -> Decimal:
    return _mean_decimal(tuple(_brier_error(row) for row in rows))


def _brier_error(row: CandidateDecisionTeamMemoryCalibrationInputRow) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        difference = row.forecast_probability - row.settled_outcome
        return _normalize_ratio("brier_error", difference * difference)


def _mean_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    total = ZERO
    for value in values:
        total += value
    return _safe_ratio(total, _count_from_int(len(values)))


def _max_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _normalize_ratio("max_ratio", max(values))


def _max_team_mean_brier_error(
    rows: tuple[CandidateDecisionTeamMemoryCalibrationTeamRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _normalize_ratio(
        "max_team_mean_brier_error",
        max(row.mean_brier_error for row in rows),
    )


def _status_count(
    rows: tuple[CandidateDecisionTeamMemoryCalibrationTeamRow, ...],
    status: str,
) -> Decimal:
    return _count_from_int(sum(1 for row in rows if row.calibration_status == status))


def _calibration_status(
    mean_brier_error: Decimal,
    *,
    config: CandidateDecisionTeamMemoryCalibrationConfig,
) -> str:
    if mean_brier_error >= config.blocked_mean_brier_error_at_or_above:
        return BLOCKED_STATUS
    if mean_brier_error >= config.watch_mean_brier_error_at_or_above:
        return WATCH_STATUS
    return PASS_STATUS


def _row_reason_for_status(status: str) -> str:
    if status == BLOCKED_STATUS:
        return BLOCKED_ROW_REASON
    if status == WATCH_STATUS:
        return WATCH_ROW_REASON
    if status == PASS_STATUS:
        return PASS_ROW_REASON
    raise ValueError("status must be pass, watch, or blocked")


def _report_status(
    rows: tuple[CandidateDecisionTeamMemoryCalibrationTeamRow, ...],
) -> str:
    if any(row.calibration_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.calibration_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    rows: tuple[CandidateDecisionTeamMemoryCalibrationTeamRow, ...],
) -> tuple[str, ...]:
    if not rows or all(row.calibration_status == PASS_STATUS for row in rows):
        return (CLEAR_REPORT_REASON,)
    reason_codes: list[str] = [
        BLOCKED_REPORT_REASON
        if _report_status(rows) == BLOCKED_STATUS
        else WATCH_REPORT_REASON,
    ]
    if any(row.calibration_status == BLOCKED_STATUS for row in rows):
        reason_codes.append(BLOCKED_PRESENT_REPORT_REASON)
    if any(row.calibration_status == WATCH_STATUS for row in rows):
        reason_codes.append(WATCH_PRESENT_REPORT_REASON)
    return tuple(reason_codes)


def _status_severity(status: str) -> int:
    if status == BLOCKED_STATUS:
        return 0
    if status == WATCH_STATUS:
        return 1
    if status == PASS_STATUS:
        return 2
    raise ValueError("status must be pass, watch, or blocked")


def _normalize_redacted_ref(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value.startswith("redacted_"):
        raise ValueError(f"{field_name} must be redacted")
    _reject_unsafe_surface_values(field_name, value)
    return value


def _normalize_settled_outcome(value: object) -> Decimal:
    settled_outcome = _normalize_ratio("settled_outcome", value)
    if settled_outcome not in (ZERO, ONE):
        raise ValueError("settled_outcome must be 0 or 1")
    return settled_outcome


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_ratio("ratio", numerator / denominator)


def _count_from_int(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count value must be a nonnegative int")
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(NUMERIC_QUANTUM)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return decimal_value


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        try:
            return decimal_value.quantize(NUMERIC_QUANTUM)
        except InvalidOperation as exc:
            raise ValueError(f"{field_name} must be a Decimal with valid scale") from exc


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    with localcontext(DECIMAL_CONTEXT):
        try:
            return decimal_value.quantize(NUMERIC_QUANTUM)
        except InvalidOperation as exc:
            raise ValueError(f"{field_name} must be a ratio Decimal") from exc


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() != UTC_OFFSET:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_canonical_string(field_name, reason_code)
        if reason_code not in allowed_reason_codes:
            raise ValueError(f"{field_name} contains an unsupported reason code")
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(reason_code)
    return reason_codes


def _reject_unsafe_surface_values(label: str, payload: object) -> None:
    unsafe_fragments = (*UNSAFE_SURFACE_FIELD_FRAGMENTS, "li" "ve", "execution")
    for value in _iter_payload_string_values(payload):
        normalized_value = value.lower()
        if any(fragment in normalized_value for fragment in unsafe_fragments):
            raise ValueError(f"unsafe live surface value in {label}")


def _iter_payload_string_values(value: object) -> tuple[str, ...]:
    if isinstance(value, dict):
        values: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            values.extend(_iter_payload_string_values(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(_iter_payload_string_values(item))
        return tuple(values)
    if type(value) is str:
        return (value,)
    return ()


def _json_ready(value: object) -> object:
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    return value


__all__ = (
    "DEFAULT_CANDIDATE_DECISION_TEAM_MEMORY_CALIBRATION_CONFIG_VERSION",
    "CandidateDecisionTeamMemoryCalibrationConfig",
    "CandidateDecisionTeamMemoryCalibrationInput",
    "CandidateDecisionTeamMemoryCalibrationInputRow",
    "CandidateDecisionTeamMemoryCalibrationReport",
    "CandidateDecisionTeamMemoryCalibrationTeamRow",
    "build_candidate_decision_team_memory_calibration_report",
    "candidate_decision_team_memory_calibration_report_to_json",
    "candidate_decision_team_memory_calibration_report_to_jsonable",
)
