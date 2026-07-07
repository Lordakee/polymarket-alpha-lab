"""Readonly Decimal heatmap for specialist event-category coverage."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_TEAM_SPECIALIST_EVENT_COVERAGE_HEATMAP_V2_CONFIG_VERSION = (
    "team-specialist-event-coverage-heatmap-v2"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

ROW_STATUSES = ("pass", "watch", "blocked")
HEATMAP_STATUSES = ("pass", "watch", "blocked")
ROW_REASON_CODES = (
    "event_coverage_pass",
    "event_coverage_watch",
    "event_coverage_blocked",
    "specialist_coverage_present",
    "specialist_coverage_missing",
    "backlog_pressure_low",
    "backlog_pressure_watch",
    "backlog_pressure_high",
    "calibration_quality_strong",
    "calibration_quality_watch",
    "calibration_quality_weak",
    "source_family_coverage_strong",
    "source_family_coverage_watch",
    "source_family_coverage_weak",
    "recent_error_low",
    "recent_error_watch",
    "recent_error_high",
    "upcoming_event_load_low",
    "upcoming_event_load_watch",
    "upcoming_event_load_high",
)
REPORT_REASON_CODES = (
    "event_coverage_heatmap_passed",
    "event_coverage_heatmap_watch_rows",
    "event_coverage_heatmap_blocked_rows",
    "event_coverage_heatmap_empty",
)
UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)

__all__ = (
    "DEFAULT_TEAM_SPECIALIST_EVENT_COVERAGE_HEATMAP_V2_CONFIG_VERSION",
    "TeamSpecialistEventCoverageHeatmapV2Config",
    "TeamSpecialistEventCoverageHeatmapV2Input",
    "TeamSpecialistEventCoverageHeatmapV2Row",
    "TeamSpecialistEventCoverageHeatmapV2Report",
    "build_team_specialist_event_coverage_heatmap_v2",
)


@dataclass(frozen=True)
class TeamSpecialistEventCoverageHeatmapV2Config:
    config_version: str = DEFAULT_TEAM_SPECIALIST_EVENT_COVERAGE_HEATMAP_V2_CONFIG_VERSION
    coverage_weight: Decimal = Decimal("0.250000")
    backlog_pressure_weight: Decimal = Decimal("0.150000")
    calibration_quality_weight: Decimal = Decimal("0.200000")
    source_family_coverage_weight: Decimal = Decimal("0.150000")
    recent_error_weight: Decimal = Decimal("0.150000")
    upcoming_event_load_weight: Decimal = Decimal("0.100000")
    min_source_family_count: Decimal = Decimal("4")
    backlog_blocked_floor: Decimal = Decimal("10")
    upcoming_event_blocked_floor: Decimal = Decimal("8")
    pass_score_floor: Decimal = Decimal("0.850000")
    watch_score_floor: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        for field_name in (
            "coverage_weight",
            "backlog_pressure_weight",
            "calibration_quality_weight",
            "source_family_coverage_weight",
            "recent_error_weight",
            "upcoming_event_load_weight",
            "pass_score_floor",
            "watch_score_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_source_family_count",
            "backlog_blocked_floor",
            "upcoming_event_blocked_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _validate_config(self)
        _require_hard_flags("TeamSpecialistEventCoverageHeatmapV2Config", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistEventCoverageHeatmapV2Config",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistEventCoverageHeatmapV2Input:
    team_id: str
    event_category: str
    specialist_id: str | None
    open_backlog_count: Decimal
    calibration_quality_score: Decimal
    source_family_count: Decimal
    recent_error: Decimal
    upcoming_event_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "team_id",
            _require_public_string("team_id", self.team_id),
        )
        object.__setattr__(
            self,
            "event_category",
            _require_public_string("event_category", self.event_category),
        )
        if self.specialist_id is not None:
            object.__setattr__(
                self,
                "specialist_id",
                _require_public_string("specialist_id", self.specialist_id),
            )
        for field_name in (
            "calibration_quality_score",
            "recent_error",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "open_backlog_count",
            "source_family_count",
            "upcoming_event_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _require_hard_flags("TeamSpecialistEventCoverageHeatmapV2Input", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistEventCoverageHeatmapV2Input",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistEventCoverageHeatmapV2Row:
    rank: Decimal
    team_id: str
    event_category: str
    specialist_id: str | None
    open_backlog_count: Decimal
    calibration_quality_score: Decimal
    source_family_count: Decimal
    recent_error: Decimal
    upcoming_event_count: Decimal
    coverage_score: Decimal
    backlog_pressure_score: Decimal
    source_family_coverage_score: Decimal
    recent_error_score: Decimal
    upcoming_event_load_score: Decimal
    heatmap_score: Decimal
    row_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "rank",
            _normalize_positive_integral_decimal("rank", self.rank),
        )
        object.__setattr__(
            self,
            "team_id",
            _require_public_string("team_id", self.team_id),
        )
        object.__setattr__(
            self,
            "event_category",
            _require_public_string("event_category", self.event_category),
        )
        if self.specialist_id is not None:
            object.__setattr__(
                self,
                "specialist_id",
                _require_public_string("specialist_id", self.specialist_id),
            )
        for field_name in (
            "calibration_quality_score",
            "recent_error",
            "coverage_score",
            "backlog_pressure_score",
            "source_family_coverage_score",
            "recent_error_score",
            "upcoming_event_load_score",
            "heatmap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "open_backlog_count",
            "source_family_count",
            "upcoming_event_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _require_row_status("row_status", self.row_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("TeamSpecialistEventCoverageHeatmapV2Row", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistEventCoverageHeatmapV2Row",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistEventCoverageHeatmapV2Report:
    generated_at: datetime
    config_version: str
    heatmap_status: str
    row_count: Decimal
    category_count: Decimal
    pass_row_count: Decimal
    watch_row_count: Decimal
    blocked_row_count: Decimal
    average_heatmap_score: Decimal
    max_backlog_pressure_count: Decimal
    max_upcoming_event_count: Decimal
    rows: tuple[TeamSpecialistEventCoverageHeatmapV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        _require_heatmap_status("heatmap_status", self.heatmap_status)
        for field_name in (
            "row_count",
            "category_count",
            "pass_row_count",
            "watch_row_count",
            "blocked_row_count",
            "max_backlog_pressure_count",
            "max_upcoming_event_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "average_heatmap_score",
            _normalize_ratio("average_heatmap_score", self.average_heatmap_score),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("TeamSpecialistEventCoverageHeatmapV2Report", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistEventCoverageHeatmapV2Report",
            _payload_value(asdict(self)),
        )
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload(
            "TeamSpecialistEventCoverageHeatmapV2Report.payload",
            payload,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_team_specialist_event_coverage_heatmap_v2(
    coverage_inputs: object,
    *,
    config: TeamSpecialistEventCoverageHeatmapV2Config | None = None,
    generated_at: datetime,
) -> TeamSpecialistEventCoverageHeatmapV2Report:
    if config is None:
        config = TeamSpecialistEventCoverageHeatmapV2Config()
    if type(config) is not TeamSpecialistEventCoverageHeatmapV2Config:
        raise ValueError("config must be a TeamSpecialistEventCoverageHeatmapV2Config")
    _require_hard_flags("TeamSpecialistEventCoverageHeatmapV2Config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_coverage_inputs(coverage_inputs)
    rows = tuple(
        _row_for_input(rank=index, item=item, config=config)
        for index, item in enumerate(_sorted_inputs(inputs, config), start=1)
    )
    status = _heatmap_status(rows)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "heatmap_status": status,
        "row_count": Decimal(len(rows)).quantize(COUNT_QUANT),
        "category_count": Decimal(len({row.event_category for row in rows})).quantize(
            COUNT_QUANT,
        ),
        "pass_row_count": _status_count(rows, "pass"),
        "watch_row_count": _status_count(rows, "watch"),
        "blocked_row_count": _status_count(rows, "blocked"),
        "average_heatmap_score": _average_score(rows),
        "max_backlog_pressure_count": _max_backlog_count(rows),
        "max_upcoming_event_count": _max_upcoming_event_count(rows),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows, status),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _derived_validation_digest(values)
    return TeamSpecialistEventCoverageHeatmapV2Report(**values)


def _sorted_inputs(
    inputs: tuple[TeamSpecialistEventCoverageHeatmapV2Input, ...],
    config: TeamSpecialistEventCoverageHeatmapV2Config,
) -> tuple[TeamSpecialistEventCoverageHeatmapV2Input, ...]:
    return tuple(
        sorted(
            inputs,
            key=lambda item: (
                -_score_for_input(item, config),
                item.team_id,
                item.event_category,
            ),
        ),
    )


def _row_for_input(
    *,
    rank: int,
    item: TeamSpecialistEventCoverageHeatmapV2Input,
    config: TeamSpecialistEventCoverageHeatmapV2Config,
) -> TeamSpecialistEventCoverageHeatmapV2Row:
    score = _score_for_input(item, config)
    status = _row_status(score, config)
    return TeamSpecialistEventCoverageHeatmapV2Row(
        rank=Decimal(rank).quantize(COUNT_QUANT),
        team_id=item.team_id,
        event_category=item.event_category,
        specialist_id=item.specialist_id,
        open_backlog_count=item.open_backlog_count,
        calibration_quality_score=item.calibration_quality_score,
        source_family_count=item.source_family_count,
        recent_error=item.recent_error,
        upcoming_event_count=item.upcoming_event_count,
        coverage_score=_coverage_score(item),
        backlog_pressure_score=_backlog_pressure_score(item, config),
        source_family_coverage_score=_source_family_coverage_score(item, config),
        recent_error_score=_recent_error_score(item),
        upcoming_event_load_score=_upcoming_event_load_score(item, config),
        heatmap_score=score,
        row_status=status,
        reason_codes=_row_reason_codes(item, status, config),
    )


def _score_for_input(
    item: TeamSpecialistEventCoverageHeatmapV2Input,
    config: TeamSpecialistEventCoverageHeatmapV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            _coverage_score(item) * config.coverage_weight
            + _backlog_pressure_score(item, config) * config.backlog_pressure_weight
            + item.calibration_quality_score * config.calibration_quality_weight
            + _source_family_coverage_score(item, config)
            * config.source_family_coverage_weight
            + _recent_error_score(item) * config.recent_error_weight
            + _upcoming_event_load_score(item, config) * config.upcoming_event_load_weight
        )
        return _clamp_ratio(score)


def _coverage_score(item: TeamSpecialistEventCoverageHeatmapV2Input) -> Decimal:
    if item.specialist_id is None:
        return ZERO
    return ONE


def _backlog_pressure_score(
    item: TeamSpecialistEventCoverageHeatmapV2Input,
    config: TeamSpecialistEventCoverageHeatmapV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(ONE - item.open_backlog_count / config.backlog_blocked_floor)


def _source_family_coverage_score(
    item: TeamSpecialistEventCoverageHeatmapV2Input,
    config: TeamSpecialistEventCoverageHeatmapV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(item.source_family_count / config.min_source_family_count)


def _recent_error_score(item: TeamSpecialistEventCoverageHeatmapV2Input) -> Decimal:
    return _clamp_ratio(ONE - item.recent_error)


def _upcoming_event_load_score(
    item: TeamSpecialistEventCoverageHeatmapV2Input,
    config: TeamSpecialistEventCoverageHeatmapV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            ONE - item.upcoming_event_count / config.upcoming_event_blocked_floor,
        )


def _row_status(
    score: Decimal,
    config: TeamSpecialistEventCoverageHeatmapV2Config,
) -> str:
    if score >= config.pass_score_floor:
        return "pass"
    if score >= config.watch_score_floor:
        return "watch"
    return "blocked"


def _heatmap_status(rows: tuple[TeamSpecialistEventCoverageHeatmapV2Row, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.row_status == "blocked" for row in rows):
        return "blocked"
    if any(row.row_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _row_reason_codes(
    item: TeamSpecialistEventCoverageHeatmapV2Input,
    status: str,
    config: TeamSpecialistEventCoverageHeatmapV2Config,
) -> tuple[str, ...]:
    return (
        f"event_coverage_{status}",
        _coverage_reason(item),
        _backlog_reason(item, config),
        _tier_reason(
            item.calibration_quality_score,
            strong=Decimal("0.800000"),
            watch=Decimal("0.600000"),
            strong_reason="calibration_quality_strong",
            watch_reason="calibration_quality_watch",
            weak_reason="calibration_quality_weak",
        ),
        _source_family_reason(item, config),
        _recent_error_reason(item.recent_error),
        _upcoming_event_reason(item, config),
    )


def _coverage_reason(item: TeamSpecialistEventCoverageHeatmapV2Input) -> str:
    if item.specialist_id is None:
        return "specialist_coverage_missing"
    return "specialist_coverage_present"


def _backlog_reason(
    item: TeamSpecialistEventCoverageHeatmapV2Input,
    config: TeamSpecialistEventCoverageHeatmapV2Config,
) -> str:
    if item.open_backlog_count <= Decimal("2"):
        return "backlog_pressure_low"
    if item.open_backlog_count < config.backlog_blocked_floor:
        return "backlog_pressure_watch"
    return "backlog_pressure_high"


def _source_family_reason(
    item: TeamSpecialistEventCoverageHeatmapV2Input,
    config: TeamSpecialistEventCoverageHeatmapV2Config,
) -> str:
    if item.source_family_count >= config.min_source_family_count:
        return "source_family_coverage_strong"
    if item.source_family_count >= Decimal("2"):
        return "source_family_coverage_watch"
    return "source_family_coverage_weak"


def _upcoming_event_reason(
    item: TeamSpecialistEventCoverageHeatmapV2Input,
    config: TeamSpecialistEventCoverageHeatmapV2Config,
) -> str:
    if item.upcoming_event_count <= Decimal("2"):
        return "upcoming_event_load_low"
    if item.upcoming_event_count < config.upcoming_event_blocked_floor:
        return "upcoming_event_load_watch"
    return "upcoming_event_load_high"


def _tier_reason(
    value: Decimal,
    *,
    strong: Decimal,
    watch: Decimal,
    strong_reason: str,
    watch_reason: str,
    weak_reason: str,
) -> str:
    if value >= strong:
        return strong_reason
    if value >= watch:
        return watch_reason
    return weak_reason


def _recent_error_reason(value: Decimal) -> str:
    if value <= Decimal("0.120000"):
        return "recent_error_low"
    if value <= Decimal("0.250000"):
        return "recent_error_watch"
    return "recent_error_high"


def _report_reason_codes(
    rows: tuple[TeamSpecialistEventCoverageHeatmapV2Row, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("event_coverage_heatmap_empty",)
    reasons: list[str] = []
    if any(row.row_status == "blocked" for row in rows):
        reasons.append("event_coverage_heatmap_blocked_rows")
    if any(row.row_status == "watch" for row in rows):
        reasons.append("event_coverage_heatmap_watch_rows")
    if not reasons and status == "pass":
        reasons.append("event_coverage_heatmap_passed")
    return tuple(reasons)


def _status_count(
    rows: tuple[TeamSpecialistEventCoverageHeatmapV2Row, ...],
    status: str,
) -> Decimal:
    return Decimal(sum(1 for row in rows if row.row_status == status)).quantize(
        COUNT_QUANT,
    )


def _average_score(rows: tuple[TeamSpecialistEventCoverageHeatmapV2Row, ...]) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(sum(row.heatmap_score for row in rows) / Decimal(len(rows)))


def _max_backlog_count(
    rows: tuple[TeamSpecialistEventCoverageHeatmapV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO.quantize(COUNT_QUANT)
    return max(row.open_backlog_count for row in rows)


def _max_upcoming_event_count(
    rows: tuple[TeamSpecialistEventCoverageHeatmapV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO.quantize(COUNT_QUANT)
    return max(row.upcoming_event_count for row in rows)


def _normalize_coverage_inputs(
    value: object,
) -> tuple[TeamSpecialistEventCoverageHeatmapV2Input, ...]:
    if isinstance(value, (str, bytes)) or not hasattr(value, "__iter__"):
        raise ValueError("coverage_inputs must be an iterable")
    inputs = tuple(value)
    for item in inputs:
        if type(item) is not TeamSpecialistEventCoverageHeatmapV2Input:
            raise ValueError(
                "coverage inputs must be TeamSpecialistEventCoverageHeatmapV2Input",
            )
        _require_hard_flags("TeamSpecialistEventCoverageHeatmapV2Input", item)
    keys = tuple((item.team_id, item.event_category) for item in inputs)
    if len(set(keys)) != len(keys):
        raise ValueError("coverage inputs must not contain duplicate team/category keys")
    return inputs


def _normalize_rows(
    value: object,
) -> tuple[TeamSpecialistEventCoverageHeatmapV2Row, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not TeamSpecialistEventCoverageHeatmapV2Row:
            raise ValueError("rows must contain TeamSpecialistEventCoverageHeatmapV2Row")
    return value


def _validate_config(config: TeamSpecialistEventCoverageHeatmapV2Config) -> None:
    with localcontext(DECIMAL_CONTEXT):
        weights_total = (
            config.coverage_weight
            + config.backlog_pressure_weight
            + config.calibration_quality_weight
            + config.source_family_coverage_weight
            + config.recent_error_weight
            + config.upcoming_event_load_weight
        ).quantize(SCORE_QUANT)
    if weights_total != ONE:
        raise ValueError("heatmap weights must sum to 1.000000")
    if config.watch_score_floor > config.pass_score_floor:
        raise ValueError("watch_score_floor must not exceed pass_score_floor")


def _validate_report_consistency(report: TeamSpecialistEventCoverageHeatmapV2Report) -> None:
    rows = report.rows
    if report.row_count != Decimal(len(rows)).quantize(COUNT_QUANT):
        raise ValueError("row_count must match rows")
    if report.category_count != Decimal(len({row.event_category for row in rows})).quantize(
        COUNT_QUANT,
    ):
        raise ValueError("category_count must match rows")
    if (
        report.pass_row_count != _status_count(rows, "pass")
        or report.watch_row_count != _status_count(rows, "watch")
        or report.blocked_row_count != _status_count(rows, "blocked")
    ):
        raise ValueError("status counts must match rows")
    if report.pass_row_count + report.watch_row_count + report.blocked_row_count != (
        report.row_count
    ):
        raise ValueError("status counts must sum to row_count")
    _validate_rows_sorted(rows)
    expected_status = _heatmap_status(rows)
    if report.heatmap_status != expected_status:
        raise ValueError("heatmap_status must match rows")
    if report.reason_codes != _report_reason_codes(rows, report.heatmap_status):
        raise ValueError("reason_codes must match heatmap_status")
    if report.derived_validation_digest != _derived_validation_digest(asdict(report)):
        raise ValueError("derived_validation_digest must match report fields")
    if report.average_heatmap_score != _average_score(rows):
        raise ValueError("average_heatmap_score must match rows")
    if report.max_backlog_pressure_count != _max_backlog_count(rows):
        raise ValueError("max_backlog_pressure_count must match rows")
    if report.max_upcoming_event_count != _max_upcoming_event_count(rows):
        raise ValueError("max_upcoming_event_count must match rows")


def _validate_rows_sorted(
    rows: tuple[TeamSpecialistEventCoverageHeatmapV2Row, ...],
) -> None:
    expected = tuple(
        sorted(
            rows,
            key=lambda row: (
                -row.heatmap_score,
                row.team_id,
                row.event_category,
            ),
        ),
    )
    expected_ranks = tuple(
        Decimal(index).quantize(COUNT_QUANT) for index in range(1, len(rows) + 1)
    )
    actual_ranks = tuple(row.rank for row in rows)
    if rows != expected or actual_ranks != expected_ranks:
        raise ValueError("rows must be sorted by score and rank")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    normalized = value.strip()
    _reject_unsafe_public_payload(field_name, normalized)
    return normalized


def _require_row_status(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if value not in ROW_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_heatmap_status(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if value not in HEATMAP_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    normalized = tuple(_require_public_string(field_name, item) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    if any(item not in allowed for item in normalized):
        raise ValueError(f"{field_name} must contain known reason codes")
    return normalized


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


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return value.quantize(COUNT_QUANT)


def _normalize_positive_integral_decimal(field_name: str, value: object) -> Decimal:
    value = _normalize_nonnegative_integral_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _clamp_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return min(ONE, max(ZERO, value)).quantize(SCORE_QUANT)


def _require_sha256_digest(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {field_name}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {field_name}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {field_name}")


def _payload_value(value: object) -> object:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _payload_value(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if value is None or type(value) in (str, int, bool):
        return value
    raise ValueError("payload contains unsupported value")


def _derived_validation_digest(values: dict[str, object]) -> str:
    digest_payload = {
        key: _payload_value(item)
        for key, item in values.items()
        if key != "derived_validation_digest"
    }
    _reject_unsafe_public_payload("derived validation digest payload", digest_payload)
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public payload in {label}")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is float:
        raise ValueError(f"unsafe public payload in {label}")
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"unsafe public payload in {label}")
