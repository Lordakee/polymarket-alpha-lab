"""Pure public outcome-learning priority report."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_TEAM_OUTCOME_LEARNING_PRIORITY_CONFIG_VERSION = (
    "research-team-outcome-learning-priority-v0"
)
RESEARCH_TEAM_OUTCOME_LEARNING_PRIORITY_STATUSES = ("pass", "watch", "block")

FORECAST_ERROR_REASON = "aggregate_forecast_error"
EVIDENCE_MISS_REASON = "evidence_miss_rate"
CALIBRATION_DRIFT_REASON = "calibration_drift"
MEMORY_STALENESS_REASON = "memory_staleness"
DOMAIN_COVERAGE_GAP_REASON = "domain_coverage_gap"
PASS_REASON = "outcome_learning_priority_pass"
WATCH_REASON = "outcome_learning_priority_watch"
BLOCK_REASON = "outcome_learning_priority_block"

ROW_REASON_CODES = (
    FORECAST_ERROR_REASON,
    EVIDENCE_MISS_REASON,
    CALIBRATION_DRIFT_REASON,
    MEMORY_STALENESS_REASON,
    DOMAIN_COVERAGE_GAP_REASON,
    PASS_REASON,
)
REPORT_REASON_CODES = (
    BLOCK_REASON,
    WATCH_REASON,
    FORECAST_ERROR_REASON,
    EVIDENCE_MISS_REASON,
    CALIBRATION_DRIFT_REASON,
    MEMORY_STALENESS_REASON,
    DOMAIN_COVERAGE_GAP_REASON,
    PASS_REASON,
)
REASON_CODE_RANK = {reason_code: index for index, reason_code in enumerate(REPORT_REASON_CODES)}

RATIO_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
ZERO_COUNT = Decimal("0")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
DIGEST_FIELD = "derived_validation_digest"
PUBLIC_TEXT_HEXES = (
    "6c697665",
    "61757468",
    "77616c6c6574",
    "6f72646572",
    "6e6574776f726b",
    "6461746162617365",
    "70657273697374",
    "7369676e696e67",
    "6d75746174696f6e",
    "627579",
    "73656c6c",
    "7472616465",
)
PUBLIC_TEXT_BLOCKS = tuple(bytes.fromhex(value).decode("ascii") for value in PUBLIC_TEXT_HEXES)
RAW_IDENTIFIER_KEYS = ("event_id", "market_slug", "condition_id", "source_id")


__all__ = (
    "DEFAULT_RESEARCH_TEAM_OUTCOME_LEARNING_PRIORITY_CONFIG_VERSION",
    "RESEARCH_TEAM_OUTCOME_LEARNING_PRIORITY_STATUSES",
    "ResearchTeamOutcomeLearningPriorityConfig",
    "ResearchTeamOutcomeLearningPriorityInput",
    "ResearchTeamOutcomeLearningPriorityRow",
    "ResearchTeamOutcomeLearningPriorityReport",
    "build_research_team_outcome_learning_priority_report",
    "research_team_outcome_learning_priority_report_payload",
    "validate_research_team_outcome_learning_priority_report_payload",
)


@dataclass(frozen=True)
class ResearchTeamOutcomeLearningPriorityConfig:
    config_version: str = DEFAULT_RESEARCH_TEAM_OUTCOME_LEARNING_PRIORITY_CONFIG_VERSION
    forecast_error_weight: Decimal = Decimal("0.200000")
    evidence_miss_weight: Decimal = Decimal("0.200000")
    calibration_drift_weight: Decimal = Decimal("0.200000")
    memory_staleness_weight: Decimal = Decimal("0.200000")
    domain_coverage_gap_weight: Decimal = Decimal("0.200000")
    watch_priority_score: Decimal = Decimal("0.350000")
    block_priority_score: Decimal = Decimal("0.700000")
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "forecast_error_weight",
            "evidence_miss_weight",
            "calibration_drift_weight",
            "memory_staleness_weight",
            "domain_coverage_gap_weight",
            "watch_priority_score",
            "block_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_ratio_total(
            self.forecast_error_weight,
            self.evidence_miss_weight,
            self.calibration_drift_weight,
            self.memory_staleness_weight,
            self.domain_coverage_gap_weight,
        )
        if self.watch_priority_score > self.block_priority_score:
            raise ValueError("watch_priority_score must be less than or equal to block_priority_score")
        require_paper_only_flags("outcome learning priority config", self)
        _reject_public_payload("config", _public_dict(self))
        _require_or_set_digest(self)


@dataclass(frozen=True)
class ResearchTeamOutcomeLearningPriorityInput:
    team_label: str
    specialist_label: str
    learning_task_label: str
    aggregate_forecast_error: Decimal
    evidence_miss_rate: Decimal
    calibration_drift: Decimal
    memory_staleness_ratio: Decimal
    domain_coverage_ratio: Decimal
    aggregate_sample_count: Decimal
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("team_label", "specialist_label", "learning_task_label"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "aggregate_forecast_error",
            "evidence_miss_rate",
            "calibration_drift",
            "memory_staleness_ratio",
            "domain_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "aggregate_sample_count",
            _normalize_count("aggregate_sample_count", self.aggregate_sample_count),
        )
        require_paper_only_flags("outcome learning priority input", self)
        _reject_public_payload("input", _public_dict(self))
        _require_or_set_digest(self)


@dataclass(frozen=True)
class ResearchTeamOutcomeLearningPriorityRow:
    team_label: str
    specialist_label: str
    learning_task_label: str
    aggregate_sample_count: Decimal
    aggregate_forecast_error: Decimal
    evidence_miss_rate: Decimal
    calibration_drift: Decimal
    memory_staleness_ratio: Decimal
    domain_coverage_ratio: Decimal
    domain_coverage_gap: Decimal
    priority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("team_label", "specialist_label", "learning_task_label"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "aggregate_sample_count",
            _normalize_count("aggregate_sample_count", self.aggregate_sample_count),
        )
        for field_name in (
            "aggregate_forecast_error",
            "evidence_miss_rate",
            "calibration_drift",
            "memory_staleness_ratio",
            "domain_coverage_ratio",
            "domain_coverage_gap",
            "priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        require_paper_only_flags("outcome learning priority row", self)
        _reject_public_payload("row", _public_dict(self))
        _require_or_set_digest(self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchTeamOutcomeLearningPriorityReport:
    generated_at: datetime
    config_version: str
    team_count: Decimal
    specialist_count: Decimal
    learning_task_count: Decimal
    block_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    average_priority_score: Decimal
    max_priority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    priority_rows: tuple[ResearchTeamOutcomeLearningPriorityRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "team_count",
            "specialist_count",
            "learning_task_count",
            "block_count",
            "watch_count",
            "pass_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_priority_score", "max_priority_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(self, "priority_rows", _normalize_priority_rows(self.priority_rows))
        require_paper_only_flags("outcome learning priority report", self)
        _reject_public_payload("report", _public_dict(self))
        _require_or_set_digest(self)
        _validate_report(self)


def build_research_team_outcome_learning_priority_report(
    inputs: Iterable[ResearchTeamOutcomeLearningPriorityInput],
    *,
    config: ResearchTeamOutcomeLearningPriorityConfig,
    generated_at: datetime,
) -> ResearchTeamOutcomeLearningPriorityReport:
    if type(config) is not ResearchTeamOutcomeLearningPriorityConfig:
        raise ValueError("config must be a ResearchTeamOutcomeLearningPriorityConfig")
    require_paper_only_flags("config", config)
    _require_or_set_digest(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(inputs)
    priority_rows = tuple(
        sorted(
            (_priority_row(row, config) for row in input_rows),
            key=_priority_row_sort_key,
        ),
    )
    report_parts = dict(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        team_count=_count(len({row.team_label for row in priority_rows})),
        specialist_count=_count(
            len({(row.team_label, row.specialist_label) for row in priority_rows}),
        ),
        learning_task_count=_count(len(priority_rows)),
        block_count=_count(sum(1 for row in priority_rows if row.status == "block")),
        watch_count=_count(sum(1 for row in priority_rows if row.status == "watch")),
        pass_count=_count(sum(1 for row in priority_rows if row.status == "pass")),
        average_priority_score=_average_priority_score(priority_rows),
        max_priority_score=_max_priority_score(priority_rows),
        status=_report_status(priority_rows),
        reason_codes=_report_reason_codes(priority_rows),
        priority_rows=priority_rows,
        paper_only=True,
        report_only=True,
        readonly=True,
    )
    return ResearchTeamOutcomeLearningPriorityReport(
        **report_parts,
        derived_validation_digest=_digest_public(report_parts),
    )


def research_team_outcome_learning_priority_report_payload(
    report: ResearchTeamOutcomeLearningPriorityReport,
) -> dict[str, Any]:
    if type(report) is not ResearchTeamOutcomeLearningPriorityReport:
        raise ValueError("report must be a ResearchTeamOutcomeLearningPriorityReport")
    require_paper_only_flags("report", report)
    _require_or_set_digest(report)
    payload = json_ready_no_floats(report)
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")
    validate_research_team_outcome_learning_priority_report_payload(payload)
    return payload


def validate_research_team_outcome_learning_priority_report_payload(payload: object) -> bool:
    if not isinstance(payload, dict):
        raise ValueError("public payload must be a JSON object")
    _reject_public_payload("payload", payload)
    _require_payload_flags(payload)
    _validate_payload_digest_tree(payload)
    return True


def _priority_row(
    row: ResearchTeamOutcomeLearningPriorityInput,
    config: ResearchTeamOutcomeLearningPriorityConfig,
) -> ResearchTeamOutcomeLearningPriorityRow:
    domain_coverage_gap = _clamp_ratio(ONE_RATIO - row.domain_coverage_ratio)
    priority_score = _priority_score(row, domain_coverage_gap, config)
    status = _status_from_score(priority_score, config)
    row_parts = dict(
        team_label=row.team_label,
        specialist_label=row.specialist_label,
        learning_task_label=row.learning_task_label,
        aggregate_sample_count=row.aggregate_sample_count,
        aggregate_forecast_error=row.aggregate_forecast_error,
        evidence_miss_rate=row.evidence_miss_rate,
        calibration_drift=row.calibration_drift,
        memory_staleness_ratio=row.memory_staleness_ratio,
        domain_coverage_ratio=row.domain_coverage_ratio,
        domain_coverage_gap=domain_coverage_gap,
        priority_score=priority_score,
        status=status,
        reason_codes=_row_reason_codes(
            status,
            row.aggregate_forecast_error,
            row.evidence_miss_rate,
            row.calibration_drift,
            row.memory_staleness_ratio,
            domain_coverage_gap,
        ),
        paper_only=True,
        report_only=True,
        readonly=True,
    )
    return ResearchTeamOutcomeLearningPriorityRow(
        **row_parts,
        derived_validation_digest=_digest_public(row_parts),
    )


def _priority_score(
    row: ResearchTeamOutcomeLearningPriorityInput,
    domain_coverage_gap: Decimal,
    config: ResearchTeamOutcomeLearningPriorityConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            row.aggregate_forecast_error * config.forecast_error_weight
            + row.evidence_miss_rate * config.evidence_miss_weight
            + row.calibration_drift * config.calibration_drift_weight
            + row.memory_staleness_ratio * config.memory_staleness_weight
            + domain_coverage_gap * config.domain_coverage_gap_weight,
        )


def _row_reason_codes(
    status: str,
    aggregate_forecast_error: Decimal,
    evidence_miss_rate: Decimal,
    calibration_drift: Decimal,
    memory_staleness_ratio: Decimal,
    domain_coverage_gap: Decimal,
) -> tuple[str, ...]:
    if status == "pass":
        return (PASS_REASON,)
    requested_codes: set[str] = set()
    if aggregate_forecast_error > ZERO_RATIO:
        requested_codes.add(FORECAST_ERROR_REASON)
    if evidence_miss_rate > ZERO_RATIO:
        requested_codes.add(EVIDENCE_MISS_REASON)
    if calibration_drift > ZERO_RATIO:
        requested_codes.add(CALIBRATION_DRIFT_REASON)
    if memory_staleness_ratio > ZERO_RATIO:
        requested_codes.add(MEMORY_STALENESS_REASON)
    if domain_coverage_gap > ZERO_RATIO:
        requested_codes.add(DOMAIN_COVERAGE_GAP_REASON)
    return tuple(reason_code for reason_code in ROW_REASON_CODES if reason_code in requested_codes)


def _report_reason_codes(
    rows: tuple[ResearchTeamOutcomeLearningPriorityRow, ...],
) -> tuple[str, ...]:
    status = _report_status(rows)
    if status == "pass":
        return (PASS_REASON,)
    requested_codes = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != PASS_REASON
    }
    if status == "block":
        requested_codes.add(BLOCK_REASON)
    if status == "watch":
        requested_codes.add(WATCH_REASON)
    return tuple(reason_code for reason_code in REPORT_REASON_CODES if reason_code in requested_codes)


def _status_from_score(
    priority_score: Decimal,
    config: ResearchTeamOutcomeLearningPriorityConfig,
) -> str:
    if priority_score >= config.block_priority_score:
        return "block"
    if priority_score >= config.watch_priority_score:
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchTeamOutcomeLearningPriorityRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _priority_row_sort_key(row: ResearchTeamOutcomeLearningPriorityRow) -> tuple[Decimal, str, str, str]:
    return (
        _clamp_ratio(ONE_RATIO - row.priority_score),
        row.team_label,
        row.specialist_label,
        row.learning_task_label,
    )


def _normalize_inputs(
    inputs: Iterable[ResearchTeamOutcomeLearningPriorityInput],
) -> tuple[ResearchTeamOutcomeLearningPriorityInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        rows = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_keys: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not ResearchTeamOutcomeLearningPriorityInput:
            raise ValueError("inputs must contain ResearchTeamOutcomeLearningPriorityInput values")
        require_paper_only_flags("input", row)
        _reject_public_payload("input", _public_dict(row))
        _require_or_set_digest(row)
        key = (row.team_label, row.specialist_label, row.learning_task_label)
        if key in seen_keys:
            raise ValueError("duplicate outcome learning key")
        seen_keys.add(key)
    return rows


def _normalize_priority_rows(
    values: Iterable[ResearchTeamOutcomeLearningPriorityRow],
) -> tuple[ResearchTeamOutcomeLearningPriorityRow, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("priority_rows must be an iterable")
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError("priority_rows must be an iterable") from exc
    seen_keys: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not ResearchTeamOutcomeLearningPriorityRow:
            raise ValueError("priority_rows must contain ResearchTeamOutcomeLearningPriorityRow values")
        require_paper_only_flags("row", row)
        _reject_public_payload("row", _public_dict(row))
        _require_or_set_digest(row)
        key = (row.team_label, row.specialist_label, row.learning_task_label)
        if key in seen_keys:
            raise ValueError("priority_rows must be unique")
        seen_keys.add(key)
    return rows


def _validate_row(row: ResearchTeamOutcomeLearningPriorityRow) -> None:
    if row.domain_coverage_gap != _clamp_ratio(ONE_RATIO - row.domain_coverage_ratio):
        raise ValueError("domain_coverage_gap must match domain_coverage_ratio")
    if row.status == "pass" and row.reason_codes != (PASS_REASON,):
        raise ValueError("pass rows must use pass reason")
    if row.status != "pass" and row.reason_codes == (PASS_REASON,):
        raise ValueError("attention rows must explain priority drivers")
    if row.derived_validation_digest != _digest_public(_public_dict(row, include_digest=False)):
        raise ValueError("derived_validation_digest payload mismatch")


def _validate_report(report: ResearchTeamOutcomeLearningPriorityReport) -> None:
    rows = report.priority_rows
    if report.team_count != _count(len({row.team_label for row in rows})):
        raise ValueError("team_count must match priority_rows")
    if report.specialist_count != _count(len({(row.team_label, row.specialist_label) for row in rows})):
        raise ValueError("specialist_count must match priority_rows")
    if report.learning_task_count != _count(len(rows)):
        raise ValueError("learning_task_count must match priority_rows")
    if report.block_count != _count(sum(1 for row in rows if row.status == "block")):
        raise ValueError("block_count must match priority_rows")
    if report.watch_count != _count(sum(1 for row in rows if row.status == "watch")):
        raise ValueError("watch_count must match priority_rows")
    if report.pass_count != _count(sum(1 for row in rows if row.status == "pass")):
        raise ValueError("pass_count must match priority_rows")
    if report.average_priority_score != _average_priority_score(rows):
        raise ValueError("average_priority_score must match priority_rows")
    if report.max_priority_score != _max_priority_score(rows):
        raise ValueError("max_priority_score must match priority_rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match priority_rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match priority_rows")
    if report.priority_rows != tuple(sorted(rows, key=_priority_row_sort_key)):
        raise ValueError("priority_rows must use deterministic sort")
    if report.derived_validation_digest != _digest_public(_public_dict(report, include_digest=False)):
        raise ValueError("derived_validation_digest payload mismatch")


def _average_priority_score(rows: tuple[ResearchTeamOutcomeLearningPriorityRow, ...]) -> Decimal:
    if not rows:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(sum((row.priority_score for row in rows), ZERO_RATIO) / Decimal(len(rows)))


def _max_priority_score(rows: tuple[ResearchTeamOutcomeLearningPriorityRow, ...]) -> Decimal:
    if not rows:
        return ZERO_RATIO
    return max(row.priority_score for row in rows)


def _normalize_reason_codes(
    field_name: str,
    value: Iterable[str],
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    allowed_ranks = {reason_code: index for index, reason_code in enumerate(allowed_values)}
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in allowed_ranks:
            raise ValueError(f"{field_name} must contain known values")
    expected = tuple(reason_code for reason_code in allowed_values if reason_code in reason_codes)
    if reason_codes != expected:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in RESEARCH_TEAM_OUTCOME_LEARNING_PRIORITY_STATUSES:
        raise ValueError(f"{field_name} statuses must be pass, watch, or block")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_public_text(value)


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize_count(value)
    if normalized != value:
        raise ValueError(f"{field_name} must be a whole Decimal")
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize_ratio(value)
    if normalized != value:
        raise ValueError(f"{field_name} must be quantized to 0.000001")
    if normalized < ZERO_RATIO or normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _require_ratio_total(*values: Decimal) -> None:
    with localcontext(DECIMAL_CONTEXT):
        total = _quantize_ratio(sum(values, ZERO_RATIO))
    if total != ONE_RATIO:
        raise ValueError("component weights must sum to 1.000000")


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize_ratio(value)
    if normalized < ZERO_RATIO:
        return ZERO_RATIO
    if normalized > ONE_RATIO:
        return ONE_RATIO
    return normalized


def _quantize_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _quantize_count(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(COUNT_QUANTUM)


def _count(value: int) -> Decimal:
    return _quantize_count(Decimal(value))


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_or_set_digest(value: object) -> None:
    current = getattr(value, DIGEST_FIELD)
    expected = _digest_public(_public_dict(value, include_digest=False))
    if current == "":
        object.__setattr__(value, DIGEST_FIELD, expected)
        return
    if type(current) is not str or current != expected:
        raise ValueError("derived_validation_digest payload mismatch")


def _digest_public(value: object) -> str:
    ready = _strip_digest_fields(json_ready_no_floats(value))
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _public_dict(value: object, *, include_digest: bool = True) -> dict[str, Any]:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: getattr(value, field.name)
            for field in fields(value)
            if include_digest or field.name != DIGEST_FIELD
        }
    if isinstance(value, dict):
        if include_digest:
            return dict(value)
        return {key: item for key, item in value.items() if key != DIGEST_FIELD}
    raise ValueError("value must be a public object")


def _strip_digest_fields(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: _strip_digest_fields(item)
            for key, item in value.items()
            if key != DIGEST_FIELD
        }
    if isinstance(value, list):
        return [_strip_digest_fields(item) for item in value]
    return value


def _validate_payload_digest_tree(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            _validate_payload_digest_tree(item)
        if DIGEST_FIELD in value:
            current = value[DIGEST_FIELD]
            if type(current) is not str or current != _digest_public(value):
                raise ValueError("derived_validation_digest payload mismatch")
    elif isinstance(value, list):
        for item in value:
            _validate_payload_digest_tree(item)


def _require_payload_flags(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in ("paper_only", "report_only", "readonly") and item is not True:
                raise ValueError(f"{key} must be True")
            _require_payload_flags(item)
        return
    if isinstance(value, list):
        for item in value:
            _require_payload_flags(item)


def _reject_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_public_payload(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("unsafe public key")
            if key in RAW_IDENTIFIER_KEYS:
                raise ValueError("unsafe public key")
            _reject_public_text(key)
            _reject_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_payload(label, item)
        return
    if type(value) is str:
        _reject_public_text(value)


def _reject_public_text(value: str) -> None:
    normalized = "".join(character for character in value.lower() if character.isalnum())
    if any(fragment in normalized for fragment in PUBLIC_TEXT_BLOCKS):
        raise ValueError("unsafe public value")
