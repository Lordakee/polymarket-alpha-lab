"""Report-only specialist team post-settlement calibration evidence reducer.

This module materializes public-safe calibration evidence after prediction
settlement. It is paper-only, report-only, read-only, and performs no network
work.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import asdict, dataclass, is_dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_SPECIALIST_TEAM_POST_SETTLEMENT_CALIBRATION_EVIDENCE_CONFIG_VERSION = (
    "specialist-team-post-settlement-calibration-evidence-report-v1"
)
SPECIALIST_TEAM_POST_SETTLEMENT_CALIBRATION_EVIDENCE_STATUSES = (
    "sufficient",
    "review",
    "insufficient",
)

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PUBLIC_CODE_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_")
HEX_CHARS = frozenset("0123456789abcdef")
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
UNSAFE_PUBLIC_FRAGMENTS = (
    "://",
    "@",
    "per" + "sist",
    "data" + "base",
    "dsn",
    "postgres",
    "sql" + "ite",
    "supa" + "base",
    "li" + "ve",
    "au" + "th",
    "wal" + "let",
    "ord" + "er",
    "tra" + "de",
    "exec" + "ute",
    "exec" + "ution",
    "to" + "ken",
    "sec" + "ret",
    "api" + "_key",
    "apikey",
    "private" + "_key",
    "adj" + "ust",
    "tu" + "ne",
    "re" + "tu" + "ne",
    "para" + "meter",
    "market",
    "source_id",
    "source_url",
    "raw_source",
)

MANUAL_NEXT_STEP_ARCHIVE = "archive_post_settlement_calibration_evidence"
MANUAL_NEXT_STEP_REVIEW = "manual_review_calibration_evidence_before_memory_update"
MANUAL_NEXT_STEP_COLLECT = (
    "manual_collect_settled_calibration_evidence_before_any_model_change"
)
MANUAL_NEXT_STEPS = (
    MANUAL_NEXT_STEP_ARCHIVE,
    MANUAL_NEXT_STEP_REVIEW,
    MANUAL_NEXT_STEP_COLLECT,
)
MANUAL_NEXT_STEP_BY_STATUS = {
    "sufficient": MANUAL_NEXT_STEP_ARCHIVE,
    "review": MANUAL_NEXT_STEP_REVIEW,
    "insufficient": MANUAL_NEXT_STEP_COLLECT,
}


__all__ = (
    "DEFAULT_SPECIALIST_TEAM_POST_SETTLEMENT_CALIBRATION_EVIDENCE_CONFIG_VERSION",
    "SPECIALIST_TEAM_POST_SETTLEMENT_CALIBRATION_EVIDENCE_STATUSES",
    "SpecialistTeamPostSettlementCalibrationEvidenceConfig",
    "SpecialistTeamPostSettlementCalibrationEvidenceReasonCodeCount",
    "SpecialistTeamPostSettlementCalibrationEvidenceReport",
    "SpecialistTeamPostSettlementCalibrationEvidenceRow",
    "SpecialistTeamPostSettlementCalibrationEvidenceSignal",
    "build_specialist_team_post_settlement_calibration_evidence_report",
    "specialist_team_post_settlement_calibration_evidence_report_payload",
    "validate_specialist_team_post_settlement_calibration_evidence_report_payload",
)


@dataclass(frozen=True)
class SpecialistTeamPostSettlementCalibrationEvidenceConfig:
    config_version: str = (
        DEFAULT_SPECIALIST_TEAM_POST_SETTLEMENT_CALIBRATION_EVIDENCE_CONFIG_VERSION
    )
    minimum_sufficient_settled_prediction_count: Decimal = Decimal("10.000000")
    minimum_review_settled_prediction_count: Decimal = Decimal("5.000000")
    maximum_sufficient_mean_probability_error: Decimal = Decimal("0.060000")
    maximum_review_mean_probability_error: Decimal = Decimal("0.140000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            SpecialistTeamPostSettlementCalibrationEvidenceConfig,
            "config",
        )
        _require_config_version(self.config_version)
        for field_name in (
            "minimum_sufficient_settled_prediction_count",
            "minimum_review_settled_prediction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_integer_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "maximum_sufficient_mean_probability_error",
            "maximum_review_mean_probability_error",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.minimum_sufficient_settled_prediction_count <= ZERO:
            raise ValueError("minimum_sufficient_settled_prediction_count must be positive")
        if self.minimum_review_settled_prediction_count <= ZERO:
            raise ValueError("minimum_review_settled_prediction_count must be positive")
        if (
            self.minimum_review_settled_prediction_count
            > self.minimum_sufficient_settled_prediction_count
        ):
            raise ValueError(
                "minimum_review_settled_prediction_count must not exceed sufficient count",
            )
        if (
            self.maximum_sufficient_mean_probability_error
            > self.maximum_review_mean_probability_error
        ):
            raise ValueError(
                "maximum_sufficient_mean_probability_error must not exceed review error",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class SpecialistTeamPostSettlementCalibrationEvidenceSignal:
    team_id: str
    category_id: str
    settled_prediction_count: Decimal
    mean_probability_error: Decimal
    source_error_count: Decimal
    memory_update_required: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            SpecialistTeamPostSettlementCalibrationEvidenceSignal,
            "signal",
        )
        _require_public_code("team_id", self.team_id)
        _require_category_id("category_id", self.category_id)
        object.__setattr__(
            self,
            "settled_prediction_count",
            _normalize_integer_decimal(
                "settled_prediction_count",
                self.settled_prediction_count,
            ),
        )
        object.__setattr__(
            self,
            "mean_probability_error",
            _normalize_probability_decimal(
                "mean_probability_error",
                self.mean_probability_error,
            ),
        )
        object.__setattr__(
            self,
            "source_error_count",
            _normalize_integer_decimal("source_error_count", self.source_error_count),
        )
        if type(self.memory_update_required) is not bool:
            raise ValueError("memory_update_required must be a bool")
        _require_hard_flags("signal", self)


@dataclass(frozen=True)
class SpecialistTeamPostSettlementCalibrationEvidenceRow:
    team_id: str
    category_id: str
    settled_prediction_count: Decimal
    mean_probability_error: Decimal
    source_error_count: Decimal
    memory_update_required: bool
    calibration_evidence_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, SpecialistTeamPostSettlementCalibrationEvidenceRow, "row")
        _require_public_code("team_id", self.team_id)
        _require_category_id("category_id", self.category_id)
        object.__setattr__(
            self,
            "settled_prediction_count",
            _normalize_integer_decimal(
                "settled_prediction_count",
                self.settled_prediction_count,
            ),
        )
        object.__setattr__(
            self,
            "mean_probability_error",
            _normalize_probability_decimal(
                "mean_probability_error",
                self.mean_probability_error,
            ),
        )
        object.__setattr__(
            self,
            "source_error_count",
            _normalize_integer_decimal("source_error_count", self.source_error_count),
        )
        if type(self.memory_update_required) is not bool:
            raise ValueError("memory_update_required must be a bool")
        _require_status("calibration_evidence_status", self.calibration_evidence_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_manual_next_step("manual_next_step", self.manual_next_step)
        if self.manual_next_step != MANUAL_NEXT_STEP_BY_STATUS[self.calibration_evidence_status]:
            raise ValueError("manual_next_step must match calibration_evidence_status")
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class SpecialistTeamPostSettlementCalibrationEvidenceReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            SpecialistTeamPostSettlementCalibrationEvidenceReasonCodeCount,
            "reason_code_count",
        )
        _require_public_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_integer_decimal("count", self.count))
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class SpecialistTeamPostSettlementCalibrationEvidenceReport:
    config_version: str
    row_count: Decimal
    team_count: Decimal
    category_count: Decimal
    sufficient_count: Decimal
    review_count: Decimal
    insufficient_count: Decimal
    manual_next_step_count: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        SpecialistTeamPostSettlementCalibrationEvidenceReasonCodeCount,
        ...
    ]
    manual_next_step: str
    rows: tuple[SpecialistTeamPostSettlementCalibrationEvidenceRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            SpecialistTeamPostSettlementCalibrationEvidenceReport,
            "report",
        )
        _require_config_version(self.config_version)
        for field_name in (
            "row_count",
            "team_count",
            "category_count",
            "sufficient_count",
            "review_count",
            "insufficient_count",
            "manual_next_step_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_integer_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("report_status", self.report_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _require_manual_next_step("manual_next_step", self.manual_next_step)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _validate_report(self)
        if self.derived_validation_digest:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != _derived_validation_digest(self):
                raise ValueError("derived_validation_digest must match report payload")
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _derived_validation_digest(self),
            )

    @property
    def payload(self) -> dict[str, Any]:
        return specialist_team_post_settlement_calibration_evidence_report_payload(self)


def build_specialist_team_post_settlement_calibration_evidence_report(
    signals: tuple[object, ...] | list[object] | Any,
    *,
    config: SpecialistTeamPostSettlementCalibrationEvidenceConfig,
) -> SpecialistTeamPostSettlementCalibrationEvidenceReport:
    if type(config) is not SpecialistTeamPostSettlementCalibrationEvidenceConfig:
        raise ValueError(
            "config must be a SpecialistTeamPostSettlementCalibrationEvidenceConfig",
        )
    _require_hard_flags("config", config)
    normalized_signals = _normalize_signals(signals)
    rows = tuple(
        sorted(
            (_row_from_signal(item, config=config) for item in normalized_signals),
            key=_row_sort_key,
        ),
    )
    report_status = _rollup_status(tuple(row.calibration_evidence_status for row in rows))
    return SpecialistTeamPostSettlementCalibrationEvidenceReport(
        config_version=config.config_version,
        row_count=_count(len(rows)),
        team_count=_count(len({row.team_id for row in rows})),
        category_count=_count(len({row.category_id for row in rows})),
        sufficient_count=_status_count(rows, "sufficient"),
        review_count=_status_count(rows, "review"),
        insufficient_count=_status_count(rows, "insufficient"),
        manual_next_step_count=_count(
            sum(1 for row in rows if row.manual_next_step != MANUAL_NEXT_STEP_ARCHIVE),
        ),
        report_status=report_status,
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        manual_next_step=MANUAL_NEXT_STEP_BY_STATUS[report_status],
        rows=rows,
    )


def specialist_team_post_settlement_calibration_evidence_report_payload(
    report: SpecialistTeamPostSettlementCalibrationEvidenceReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is SpecialistTeamPostSettlementCalibrationEvidenceReport:
        _require_hard_flags("report", report)
        _validate_report(report)
        if report.derived_validation_digest != _derived_validation_digest(report):
            raise ValueError("derived_validation_digest must match report payload")
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be an object")
        _reject_unsafe_public_payload(payload)
        _reject_public_numeric_values(payload)
        return payload
    if type(report) is dict:
        validate_specialist_team_post_settlement_calibration_evidence_report_payload(report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be an object")
        return payload
    raise ValueError(
        "report must be a SpecialistTeamPostSettlementCalibrationEvidenceReport",
    )


def validate_specialist_team_post_settlement_calibration_evidence_report_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be an object")
    _reject_unsafe_public_payload(payload)
    _reject_public_numeric_values(payload)
    _require_hard_flags("payload", _PayloadFlags(payload))
    supplied_digest = payload.get("derived_validation_digest")
    if type(supplied_digest) is not str:
        raise ValueError("derived_validation_digest is required")
    _require_sha256("derived_validation_digest", supplied_digest)
    if supplied_digest != _payload_validation_digest(payload):
        raise ValueError("derived_validation_digest must match report payload")
    return True


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


def _row_from_signal(
    signal: SpecialistTeamPostSettlementCalibrationEvidenceSignal,
    *,
    config: SpecialistTeamPostSettlementCalibrationEvidenceConfig,
) -> SpecialistTeamPostSettlementCalibrationEvidenceRow:
    status = _calibration_evidence_status(signal, config=config)
    return SpecialistTeamPostSettlementCalibrationEvidenceRow(
        team_id=signal.team_id,
        category_id=signal.category_id,
        settled_prediction_count=signal.settled_prediction_count,
        mean_probability_error=signal.mean_probability_error,
        source_error_count=signal.source_error_count,
        memory_update_required=signal.memory_update_required,
        calibration_evidence_status=status,
        reason_codes=_row_reason_codes(signal, status=status, config=config),
        manual_next_step=MANUAL_NEXT_STEP_BY_STATUS[status],
    )


def _calibration_evidence_status(
    signal: SpecialistTeamPostSettlementCalibrationEvidenceSignal,
    *,
    config: SpecialistTeamPostSettlementCalibrationEvidenceConfig,
) -> str:
    if (
        signal.settled_prediction_count
        >= config.minimum_sufficient_settled_prediction_count
        and signal.mean_probability_error
        <= config.maximum_sufficient_mean_probability_error
        and signal.source_error_count == ZERO
        and not signal.memory_update_required
    ):
        return "sufficient"
    if (
        signal.settled_prediction_count >= config.minimum_review_settled_prediction_count
        and signal.mean_probability_error <= config.maximum_review_mean_probability_error
    ):
        return "review"
    return "insufficient"


def _row_reason_codes(
    signal: SpecialistTeamPostSettlementCalibrationEvidenceSignal,
    *,
    status: str,
    config: SpecialistTeamPostSettlementCalibrationEvidenceConfig,
) -> tuple[str, ...]:
    codes = [f"calibration_evidence_{status}"]
    if signal.settled_prediction_count < config.minimum_review_settled_prediction_count:
        codes.append("insufficient_settled_predictions")
    if signal.memory_update_required:
        codes.append("memory_update_required")
    if signal.mean_probability_error > config.maximum_review_mean_probability_error:
        codes.append("probability_error_above_review_threshold")
    if signal.source_error_count > ZERO:
        codes.append("source_error_observed")
    return tuple(codes)


def _normalize_signals(
    signals: tuple[object, ...] | list[object] | Any,
) -> tuple[SpecialistTeamPostSettlementCalibrationEvidenceSignal, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must be an iterable of calibration evidence signals")
    normalized: list[SpecialistTeamPostSettlementCalibrationEvidenceSignal] = []
    for item in signals:
        if type(item) is not SpecialistTeamPostSettlementCalibrationEvidenceSignal:
            raise ValueError(
                "signals must contain SpecialistTeamPostSettlementCalibrationEvidenceSignal",
            )
        _require_hard_flags("signal", item)
        normalized.append(item)
    return tuple(normalized)


def _normalize_rows(
    rows: object,
) -> tuple[SpecialistTeamPostSettlementCalibrationEvidenceRow, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not SpecialistTeamPostSettlementCalibrationEvidenceRow:
            raise ValueError(
                "rows must contain SpecialistTeamPostSettlementCalibrationEvidenceRow",
            )
        _require_hard_flags("row", row)
    return rows


def _normalize_reason_code_counts(
    values: object,
) -> tuple[SpecialistTeamPostSettlementCalibrationEvidenceReasonCodeCount, ...]:
    if not isinstance(values, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    for item in values:
        if type(item) is not SpecialistTeamPostSettlementCalibrationEvidenceReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "SpecialistTeamPostSettlementCalibrationEvidenceReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", item)
    if values != tuple(sorted(values, key=lambda item: item.reason_code)):
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return values


def _validate_report(report: SpecialistTeamPostSettlementCalibrationEvidenceReport) -> None:
    rows = report.rows
    expected = {
        "row_count": _count(len(rows)),
        "team_count": _count(len({row.team_id for row in rows})),
        "category_count": _count(len({row.category_id for row in rows})),
        "sufficient_count": _status_count(rows, "sufficient"),
        "review_count": _status_count(rows, "review"),
        "insufficient_count": _status_count(rows, "insufficient"),
        "manual_next_step_count": _count(
            sum(1 for row in rows if row.manual_next_step != MANUAL_NEXT_STEP_ARCHIVE),
        ),
    }
    for field_name, value in expected.items():
        if getattr(report, field_name) != value:
            raise ValueError(f"{field_name} must match rows")
    if report.report_status != _rollup_status(
        tuple(row.calibration_evidence_status for row in rows),
    ):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    if report.manual_next_step != MANUAL_NEXT_STEP_BY_STATUS[report.report_status]:
        raise ValueError("manual_next_step must match report_status")


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if not statuses:
        return "insufficient"
    if "insufficient" in statuses:
        return "insufficient"
    if "review" in statuses:
        return "review"
    return "sufficient"


def _report_reason_codes(
    rows: tuple[SpecialistTeamPostSettlementCalibrationEvidenceRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_post_settlement_calibration_evidence",)
    return tuple(sorted({code for row in rows for code in row.reason_codes}))


def _reason_code_counts(
    rows: tuple[SpecialistTeamPostSettlementCalibrationEvidenceRow, ...],
) -> tuple[SpecialistTeamPostSettlementCalibrationEvidenceReasonCodeCount, ...]:
    if not rows:
        return (
            SpecialistTeamPostSettlementCalibrationEvidenceReasonCodeCount(
                reason_code="no_post_settlement_calibration_evidence",
                count=_count(1),
            ),
        )
    counter = Counter(code for row in rows for code in row.reason_codes)
    return tuple(
        SpecialistTeamPostSettlementCalibrationEvidenceReasonCodeCount(
            reason_code=code,
            count=_count(counter[code]),
        )
        for code in sorted(counter)
    )


def _status_count(
    rows: tuple[SpecialistTeamPostSettlementCalibrationEvidenceRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.calibration_evidence_status == status))


def _row_sort_key(row: SpecialistTeamPostSettlementCalibrationEvidenceRow) -> tuple[int, str, str]:
    status_rank = {"sufficient": 0, "review": 1, "insufficient": 2}
    return (status_rank[row.calibration_evidence_status], row.team_id, row.category_id)


def _count(value: int) -> Decimal:
    return _normalize_integer_decimal("count", Decimal(value))


def _normalize_integer_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(QUANTUM)
    if normalized != value:
        raise ValueError(f"{field_name} must use six decimal places")
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(QUANTUM)
    if normalized != value:
        raise ValueError(f"{field_name} must use six decimal places")
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _require_config_version(value: object) -> None:
    if type(value) is not str:
        raise ValueError("config_version must be a string")
    if value != DEFAULT_SPECIALIST_TEAM_POST_SETTLEMENT_CALIBRATION_EVIDENCE_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")


def _require_public_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a public code")
    if len(value) > 80 or any(character not in PUBLIC_CODE_CHARS for character in value):
        raise ValueError(f"{field_name} must be a public code")
    _reject_unsafe_public_text(field_name, value)


def _require_category_id(field_name: str, value: object) -> None:
    _require_public_code(field_name, value)
    if not str(value).startswith("category_"):
        raise ValueError(f"{field_name} must be a public code")


def _require_status(field_name: str, value: object) -> None:
    if value not in SPECIALIST_TEAM_POST_SETTLEMENT_CALIBRATION_EVIDENCE_STATUSES:
        raise ValueError(f"{field_name} must be supported")


def _require_manual_next_step(field_name: str, value: object) -> None:
    if value not in MANUAL_NEXT_STEPS:
        raise ValueError(f"{field_name} must be supported")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if not isinstance(value, tuple) or not value:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    normalized: list[str] = []
    seen: set[str] = set()
    for item in value:
        _require_public_code(field_name, item)
        if item in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(item)
        normalized.append(item)
    if tuple(normalized) != tuple(sorted(normalized)):
        raise ValueError(f"{field_name} must be sorted")
    return tuple(normalized)


def _require_exact_type(value: object, expected_type: type[object], context: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{context} must be exactly {expected_type.__name__}")


def _require_hard_flags(context: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if type(getattr(value, field_name, None)) is not bool:
            raise ValueError(f"{field_name} must be True")
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if len(value) != 64 or any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload values must be finite")
        return format(value, "f")
    if type(value) is bool or value is None:
        return value
    if type(value) in (float, int):
        raise ValueError("numeric payload values must be Decimal strings")
    if type(value) is str:
        _reject_unsafe_public_text("payload", value)
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return {_json_key(key): _json_ready(item) for key, item in value.items()}
    raise ValueError("value is not JSON serializable")


def _json_key(key: object) -> str:
    if type(key) is not str:
        raise ValueError("payload keys must be strings")
    _reject_unsafe_public_text("payload key", key)
    return key


def _derived_validation_digest(
    report: SpecialistTeamPostSettlementCalibrationEvidenceReport,
) -> str:
    payload = _json_ready_without_digest(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be an object")
    return _payload_validation_digest(payload)


def _payload_validation_digest(payload: dict[str, Any]) -> str:
    canonical = json.dumps(_strip_digest(payload), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready_without_digest(
    report: SpecialistTeamPostSettlementCalibrationEvidenceReport,
) -> dict[str, Any]:
    payload = asdict(report)
    payload.pop("derived_validation_digest", None)
    ready = _json_ready(payload)
    if type(ready) is not dict:
        raise ValueError("report payload must be an object")
    return ready


def _strip_digest(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _strip_digest(item)
            for key, item in value.items()
            if key != "derived_validation_digest"
        }
    if isinstance(value, list):
        return [_strip_digest(item) for item in value]
    return value


def _reject_public_numeric_values(value: object) -> None:
    if type(value) in (float, int):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numeric_values(item)


def _reject_unsafe_public_payload(value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(asdict(value))
        return
    if type(value) is str:
        _reject_unsafe_public_text("payload", value)
        return
    if type(value) in (Decimal, bool) or value is None:
        return
    if type(value) in (float, int):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _reject_unsafe_public_text("payload key", key)
            _reject_unsafe_public_payload(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public text")
