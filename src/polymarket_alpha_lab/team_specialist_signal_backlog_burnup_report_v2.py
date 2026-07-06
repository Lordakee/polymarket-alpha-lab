"""Readonly Decimal report for specialist signal backlog burnup pressure."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any
import json


DEFAULT_TEAM_SPECIALIST_SIGNAL_BACKLOG_BURNUP_REPORT_V2_CONFIG_VERSION = (
    "team-specialist-signal-backlog-burnup-report-v2"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

REPORT_STATUSES = ("pass", "watch", "blocked")
CAPACITY_PRESSURE_STATUSES = ("pass", "watch", "blocked")
ROW_REASON_CODES = (
    "signal_backlog_burnup_pass",
    "signal_backlog_burnup_watch",
    "signal_backlog_burnup_blocked",
    "capacity_pressure_pass",
    "capacity_pressure_watch",
    "capacity_pressure_blocked",
    "escalation_priority_pass",
    "escalation_priority_watch",
    "escalation_priority_blocked",
    "completion_backlog_clear",
    "completion_backlog_watch",
    "completion_backlog_blocked",
    "escalation_ratio_clear",
    "escalation_ratio_watch",
    "escalation_ratio_high",
)
REPORT_REASON_CODES = (
    "signal_backlog_burnup_passed",
    "signal_backlog_burnup_watch_rows",
    "signal_backlog_burnup_blocked_rows",
    "signal_backlog_burnup_empty",
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
    "DEFAULT_TEAM_SPECIALIST_SIGNAL_BACKLOG_BURNUP_REPORT_V2_CONFIG_VERSION",
    "TeamSpecialistSignalBacklogBurnupReportV2Config",
    "TeamSpecialistSignalBacklogBurnupV2Input",
    "TeamSpecialistSignalBacklogBurnupReportV2Row",
    "TeamSpecialistSignalBacklogBurnupReportV2Report",
    "build_team_specialist_signal_backlog_burnup_report_v2",
    "team_specialist_signal_backlog_burnup_report_v2_payload",
)


@dataclass(frozen=True)
class TeamSpecialistSignalBacklogBurnupReportV2Config:
    config_version: str = (
        DEFAULT_TEAM_SPECIALIST_SIGNAL_BACKLOG_BURNUP_REPORT_V2_CONFIG_VERSION
    )
    completion_weight: Decimal = Decimal("0.500000")
    capacity_pressure_weight: Decimal = Decimal("0.300000")
    escalation_weight: Decimal = Decimal("0.200000")
    capacity_pressure_watch_floor: Decimal = Decimal("0.750000")
    capacity_pressure_blocked_floor: Decimal = Decimal("0.950000")
    escalation_priority_watch_floor: Decimal = Decimal("0.300000")
    escalation_priority_blocked_floor: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_non_empty_string("config_version", self.config_version),
        )
        for field_name in (
            "completion_weight",
            "capacity_pressure_weight",
            "escalation_weight",
            "capacity_pressure_watch_floor",
            "capacity_pressure_blocked_floor",
            "escalation_priority_watch_floor",
            "escalation_priority_blocked_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("TeamSpecialistSignalBacklogBurnupReportV2Config", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistSignalBacklogBurnupReportV2Config",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistSignalBacklogBurnupV2Input:
    team_id: str
    snapshot_id: str
    captured_at: datetime
    completed_signal_count: Decimal
    carried_signal_count: Decimal
    escalated_signal_count: Decimal
    available_capacity_units: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "team_id",
            _require_non_empty_string("team_id", self.team_id),
        )
        object.__setattr__(
            self,
            "snapshot_id",
            _require_non_empty_string("snapshot_id", self.snapshot_id),
        )
        object.__setattr__(self, "captured_at", _as_utc("captured_at", self.captured_at))
        for field_name in (
            "completed_signal_count",
            "carried_signal_count",
            "escalated_signal_count",
            "available_capacity_units",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _require_hard_flags("TeamSpecialistSignalBacklogBurnupV2Input", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistSignalBacklogBurnupV2Input",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class TeamSpecialistSignalBacklogBurnupReportV2Row:
    rank: Decimal
    team_id: str
    snapshot_id: str
    captured_at: datetime
    completed_signal_count: Decimal
    carried_signal_count: Decimal
    escalated_signal_count: Decimal
    available_capacity_units: Decimal
    scope_signal_count: Decimal
    burnup_completion_ratio: Decimal
    capacity_pressure_ratio: Decimal
    escalation_ratio: Decimal
    backlog_burnup_score: Decimal
    escalation_priority_score: Decimal
    capacity_pressure_status: str
    report_status: str
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
            _require_non_empty_string("team_id", self.team_id),
        )
        object.__setattr__(
            self,
            "snapshot_id",
            _require_non_empty_string("snapshot_id", self.snapshot_id),
        )
        object.__setattr__(self, "captured_at", _as_utc("captured_at", self.captured_at))
        for field_name in (
            "completed_signal_count",
            "carried_signal_count",
            "escalated_signal_count",
            "available_capacity_units",
            "scope_signal_count",
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
            "burnup_completion_ratio",
            "capacity_pressure_ratio",
            "escalation_ratio",
            "backlog_burnup_score",
            "escalation_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_capacity_pressure_status(
            "capacity_pressure_status",
            self.capacity_pressure_status,
        )
        _require_report_status("report_status", self.report_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("TeamSpecialistSignalBacklogBurnupReportV2Row", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistSignalBacklogBurnupReportV2Row",
            _payload_value(asdict(self)),
        )
        _validate_row_consistency(self)


@dataclass(frozen=True)
class TeamSpecialistSignalBacklogBurnupReportV2Report:
    generated_at: datetime
    config_version: str
    report_status: str
    team_count: Decimal
    pass_team_count: Decimal
    watch_team_count: Decimal
    blocked_team_count: Decimal
    average_backlog_burnup_score: Decimal
    top_capacity_pressure_ratio: Decimal
    top_escalation_priority_score: Decimal
    rows: tuple[TeamSpecialistSignalBacklogBurnupReportV2Row, ...]
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
            _require_non_empty_string("config_version", self.config_version),
        )
        _require_report_status("report_status", self.report_status)
        for field_name in (
            "team_count",
            "pass_team_count",
            "watch_team_count",
            "blocked_team_count",
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
            "average_backlog_burnup_score",
            "top_capacity_pressure_ratio",
            "top_escalation_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _require_sha256_digest(
            "derived_validation_digest",
            self.derived_validation_digest,
        )
        _require_hard_flags("TeamSpecialistSignalBacklogBurnupReportV2Report", self)
        _reject_unsafe_public_payload(
            "TeamSpecialistSignalBacklogBurnupReportV2Report",
            _payload_value(asdict(self)),
        )
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload(
            "TeamSpecialistSignalBacklogBurnupReportV2Report.payload",
            payload,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_team_specialist_signal_backlog_burnup_report_v2(
    snapshots: object,
    *,
    config: TeamSpecialistSignalBacklogBurnupReportV2Config | None = None,
    generated_at: datetime,
) -> TeamSpecialistSignalBacklogBurnupReportV2Report:
    if config is None:
        config = TeamSpecialistSignalBacklogBurnupReportV2Config()
    if type(config) is not TeamSpecialistSignalBacklogBurnupReportV2Config:
        raise ValueError(
            "config must be a TeamSpecialistSignalBacklogBurnupReportV2Config",
        )
    _require_hard_flags("TeamSpecialistSignalBacklogBurnupReportV2Config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_snapshots = _normalize_snapshots(snapshots)
    for item in normalized_snapshots:
        if item.captured_at > generated_at_utc:
            raise ValueError("captured_at values must be at or before generated_at")

    rows = tuple(
        _row_for_snapshot(rank=index, snapshot=item, config=config)
        for index, item in enumerate(
            _sorted_snapshots(normalized_snapshots, config),
            start=1,
        )
    )
    status = _report_status(rows)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "report_status": status,
        "team_count": Decimal(len(rows)).quantize(COUNT_QUANT),
        "pass_team_count": _status_count(rows, "pass"),
        "watch_team_count": _status_count(rows, "watch"),
        "blocked_team_count": _status_count(rows, "blocked"),
        "average_backlog_burnup_score": _average_backlog_burnup_score(rows),
        "top_capacity_pressure_ratio": _top_capacity_pressure_ratio(rows),
        "top_escalation_priority_score": _top_escalation_priority_score(rows),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows, status),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _derived_validation_digest(values)
    return TeamSpecialistSignalBacklogBurnupReportV2Report(**values)


def team_specialist_signal_backlog_burnup_report_v2_payload(
    report: TeamSpecialistSignalBacklogBurnupReportV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is TeamSpecialistSignalBacklogBurnupReportV2Report:
        _require_hard_flags("TeamSpecialistSignalBacklogBurnupReportV2Report", report)
        payload = report.payload
        _verify_payload_digest(payload)
        return payload
    if type(report) is dict:
        payload = _payload_value(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a dict")
        _reject_unsafe_public_payload(
            "TeamSpecialistSignalBacklogBurnupReportV2Report.payload",
            payload,
        )
        _require_hard_flags("payload", _DictFlags(payload))
        _verify_payload_digest(payload)
        return payload
    raise ValueError("report must be a TeamSpecialistSignalBacklogBurnupReportV2Report")


@dataclass(frozen=True)
class _DictFlags:
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


def _sorted_snapshots(
    snapshots: tuple[TeamSpecialistSignalBacklogBurnupV2Input, ...],
    config: TeamSpecialistSignalBacklogBurnupReportV2Config,
) -> tuple[TeamSpecialistSignalBacklogBurnupV2Input, ...]:
    return tuple(
        sorted(
            snapshots,
            key=lambda item: (
                -_escalation_priority_score(item),
                -_capacity_pressure_ratio(item),
                item.team_id,
                item.snapshot_id,
            ),
        ),
    )


def _row_for_snapshot(
    *,
    rank: int,
    snapshot: TeamSpecialistSignalBacklogBurnupV2Input,
    config: TeamSpecialistSignalBacklogBurnupReportV2Config,
) -> TeamSpecialistSignalBacklogBurnupReportV2Row:
    scope = _scope_signal_count(snapshot)
    completion = _burnup_completion_ratio(snapshot)
    pressure = _capacity_pressure_ratio(snapshot)
    escalation = _escalation_ratio(snapshot)
    burnup_score = _backlog_burnup_score(
        completion=completion,
        pressure=pressure,
        escalation=escalation,
        config=config,
    )
    priority = _escalation_priority_score(snapshot)
    pressure_status = _capacity_pressure_status(pressure, config)
    status = _row_report_status(priority, config)
    return TeamSpecialistSignalBacklogBurnupReportV2Row(
        rank=Decimal(rank).quantize(COUNT_QUANT),
        team_id=snapshot.team_id,
        snapshot_id=snapshot.snapshot_id,
        captured_at=snapshot.captured_at,
        completed_signal_count=snapshot.completed_signal_count,
        carried_signal_count=snapshot.carried_signal_count,
        escalated_signal_count=snapshot.escalated_signal_count,
        available_capacity_units=snapshot.available_capacity_units,
        scope_signal_count=scope,
        burnup_completion_ratio=completion,
        capacity_pressure_ratio=pressure,
        escalation_ratio=escalation,
        backlog_burnup_score=burnup_score,
        escalation_priority_score=priority,
        capacity_pressure_status=pressure_status,
        report_status=status,
        reason_codes=_row_reason_codes(
            status=status,
            pressure_status=pressure_status,
            priority=priority,
            completion=completion,
            escalation=escalation,
            config=config,
        ),
    )


def _scope_signal_count(snapshot: TeamSpecialistSignalBacklogBurnupV2Input) -> Decimal:
    return (
        snapshot.completed_signal_count
        + snapshot.carried_signal_count
        + snapshot.escalated_signal_count
    ).quantize(COUNT_QUANT)


def _burnup_completion_ratio(
    snapshot: TeamSpecialistSignalBacklogBurnupV2Input,
) -> Decimal:
    scope = _scope_signal_count(snapshot)
    if scope == ZERO:
        return ONE
    return _ratio(snapshot.completed_signal_count, scope)


def _capacity_pressure_ratio(
    snapshot: TeamSpecialistSignalBacklogBurnupV2Input,
) -> Decimal:
    scope = _scope_signal_count(snapshot)
    if scope == ZERO:
        return ZERO
    if snapshot.available_capacity_units == ZERO:
        return ONE
    return _clamp_ratio(_ratio(scope, snapshot.available_capacity_units))


def _escalation_ratio(snapshot: TeamSpecialistSignalBacklogBurnupV2Input) -> Decimal:
    scope = _scope_signal_count(snapshot)
    if scope == ZERO:
        return ZERO
    return _ratio(snapshot.escalated_signal_count, scope)


def _backlog_burnup_score(
    *,
    completion: Decimal,
    pressure: Decimal,
    escalation: Decimal,
    config: TeamSpecialistSignalBacklogBurnupReportV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            completion * config.completion_weight
            + (ONE - pressure) * config.capacity_pressure_weight
            + (ONE - escalation) * config.escalation_weight,
        )


def _escalation_priority_score(
    snapshot: TeamSpecialistSignalBacklogBurnupV2Input,
) -> Decimal:
    completion = _burnup_completion_ratio(snapshot)
    pressure = _capacity_pressure_ratio(snapshot)
    escalation = _escalation_ratio(snapshot)
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            escalation * Decimal("0.500000")
            + pressure * Decimal("0.300000")
            + (ONE - completion) * Decimal("0.200000"),
        )


def _capacity_pressure_status(
    pressure: Decimal,
    config: TeamSpecialistSignalBacklogBurnupReportV2Config,
) -> str:
    if pressure >= config.capacity_pressure_blocked_floor:
        return "blocked"
    if pressure >= config.capacity_pressure_watch_floor:
        return "watch"
    return "pass"


def _row_report_status(
    priority: Decimal,
    config: TeamSpecialistSignalBacklogBurnupReportV2Config,
) -> str:
    if priority >= config.escalation_priority_blocked_floor:
        return "blocked"
    if priority >= config.escalation_priority_watch_floor:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    pressure_status: str,
    priority: Decimal,
    completion: Decimal,
    escalation: Decimal,
    config: TeamSpecialistSignalBacklogBurnupReportV2Config,
) -> tuple[str, ...]:
    return (
        f"signal_backlog_burnup_{status}",
        f"capacity_pressure_{pressure_status}",
        _priority_reason(priority, config),
        _completion_reason(completion),
        _escalation_reason(escalation),
    )


def _priority_reason(
    priority: Decimal,
    config: TeamSpecialistSignalBacklogBurnupReportV2Config,
) -> str:
    if priority >= config.escalation_priority_blocked_floor:
        return "escalation_priority_blocked"
    if priority >= config.escalation_priority_watch_floor:
        return "escalation_priority_watch"
    return "escalation_priority_pass"


def _completion_reason(completion: Decimal) -> str:
    if completion < Decimal("0.500000"):
        return "completion_backlog_blocked"
    if completion < Decimal("0.750000"):
        return "completion_backlog_watch"
    return "completion_backlog_clear"


def _escalation_reason(escalation: Decimal) -> str:
    if escalation >= Decimal("0.250000"):
        return "escalation_ratio_high"
    if escalation > ZERO:
        return "escalation_ratio_watch"
    return "escalation_ratio_clear"


def _report_status(
    rows: tuple[TeamSpecialistSignalBacklogBurnupReportV2Row, ...],
) -> str:
    if not rows:
        return "blocked"
    if any(row.report_status == "blocked" for row in rows):
        return "blocked"
    if any(row.report_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[TeamSpecialistSignalBacklogBurnupReportV2Row, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("signal_backlog_burnup_empty",)
    reasons: list[str] = []
    if any(row.report_status == "blocked" for row in rows):
        reasons.append("signal_backlog_burnup_blocked_rows")
    if any(row.report_status == "watch" for row in rows):
        reasons.append("signal_backlog_burnup_watch_rows")
    if not reasons and status == "pass":
        reasons.append("signal_backlog_burnup_passed")
    return tuple(reasons)


def _status_count(
    rows: tuple[TeamSpecialistSignalBacklogBurnupReportV2Row, ...],
    status: str,
) -> Decimal:
    return Decimal(sum(1 for row in rows if row.report_status == status)).quantize(
        COUNT_QUANT,
    )


def _average_backlog_burnup_score(
    rows: tuple[TeamSpecialistSignalBacklogBurnupReportV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            sum(row.backlog_burnup_score for row in rows) / Decimal(len(rows)),
        )


def _top_capacity_pressure_ratio(
    rows: tuple[TeamSpecialistSignalBacklogBurnupReportV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.capacity_pressure_ratio for row in rows)


def _top_escalation_priority_score(
    rows: tuple[TeamSpecialistSignalBacklogBurnupReportV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.escalation_priority_score for row in rows)


def _normalize_snapshots(
    value: object,
) -> tuple[TeamSpecialistSignalBacklogBurnupV2Input, ...]:
    if isinstance(value, (str, bytes)) or not hasattr(value, "__iter__"):
        raise ValueError("snapshots must be an iterable")
    snapshots = tuple(value)
    for item in snapshots:
        if type(item) is not TeamSpecialistSignalBacklogBurnupV2Input:
            raise ValueError(
                "snapshots must contain TeamSpecialistSignalBacklogBurnupV2Input",
            )
        _require_hard_flags("TeamSpecialistSignalBacklogBurnupV2Input", item)
    team_ids = tuple(item.team_id for item in snapshots)
    if len(set(team_ids)) != len(team_ids):
        raise ValueError("snapshots must not contain duplicate team_id values")
    return snapshots


def _normalize_rows(
    value: object,
) -> tuple[TeamSpecialistSignalBacklogBurnupReportV2Row, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not TeamSpecialistSignalBacklogBurnupReportV2Row:
            raise ValueError(
                "rows must contain TeamSpecialistSignalBacklogBurnupReportV2Row",
            )
        _require_hard_flags("TeamSpecialistSignalBacklogBurnupReportV2Row", row)
    return value


def _validate_config(config: TeamSpecialistSignalBacklogBurnupReportV2Config) -> None:
    with localcontext(DECIMAL_CONTEXT):
        weights_total = (
            config.completion_weight
            + config.capacity_pressure_weight
            + config.escalation_weight
        ).quantize(SCORE_QUANT)
    if weights_total != ONE:
        raise ValueError("score weights must sum to 1.000000")
    if config.capacity_pressure_watch_floor > config.capacity_pressure_blocked_floor:
        raise ValueError(
            "capacity_pressure_watch_floor must not exceed "
            "capacity_pressure_blocked_floor",
        )
    if (
        config.escalation_priority_watch_floor
        > config.escalation_priority_blocked_floor
    ):
        raise ValueError(
            "escalation_priority_watch_floor must not exceed "
            "escalation_priority_blocked_floor",
        )


def _validate_row_consistency(
    row: TeamSpecialistSignalBacklogBurnupReportV2Row,
) -> None:
    if row.scope_signal_count != (
        row.completed_signal_count
        + row.carried_signal_count
        + row.escalated_signal_count
    ).quantize(COUNT_QUANT):
        raise ValueError("scope_signal_count must match signal counts")


def _validate_report_consistency(
    report: TeamSpecialistSignalBacklogBurnupReportV2Report,
) -> None:
    rows = report.rows
    if report.team_count != Decimal(len(rows)).quantize(COUNT_QUANT):
        raise ValueError("team_count must match rows")
    if (
        report.pass_team_count != _status_count(rows, "pass")
        or report.watch_team_count != _status_count(rows, "watch")
        or report.blocked_team_count != _status_count(rows, "blocked")
    ):
        raise ValueError("status counts must match rows")
    if (
        report.pass_team_count + report.watch_team_count + report.blocked_team_count
        != report.team_count
    ):
        raise ValueError("status counts must sum to team_count")
    _validate_rows_sorted(rows)
    expected_status = _report_status(rows)
    if report.report_status != expected_status:
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(rows, report.report_status):
        raise ValueError("reason_codes must match report_status")
    if report.derived_validation_digest != _derived_validation_digest(asdict(report)):
        raise ValueError("derived_validation_digest must match report fields")
    if report.average_backlog_burnup_score != _average_backlog_burnup_score(rows):
        raise ValueError("average_backlog_burnup_score must match rows")
    if report.top_capacity_pressure_ratio != _top_capacity_pressure_ratio(rows):
        raise ValueError("top_capacity_pressure_ratio must match rows")
    if report.top_escalation_priority_score != _top_escalation_priority_score(rows):
        raise ValueError("top_escalation_priority_score must match rows")


def _validate_rows_sorted(
    rows: tuple[TeamSpecialistSignalBacklogBurnupReportV2Row, ...],
) -> None:
    expected = tuple(
        sorted(
            rows,
            key=lambda row: (
                -row.escalation_priority_score,
                -row.capacity_pressure_ratio,
                row.team_id,
                row.snapshot_id,
            ),
        ),
    )
    expected_ranks = tuple(
        Decimal(index).quantize(COUNT_QUANT) for index in range(1, len(rows) + 1)
    )
    actual_ranks = tuple(row.rank for row in rows)
    if rows != expected or actual_ranks != expected_ranks:
        raise ValueError("rows must be sorted by escalation priority and rank")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_non_empty_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    normalized = value.strip()
    _reject_unsafe_public_payload(field_name, normalized)
    return normalized


def _require_report_status(field_name: str, value: object) -> None:
    _require_non_empty_string(field_name, value)
    if value not in REPORT_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_capacity_pressure_status(field_name: str, value: object) -> None:
    _require_non_empty_string(field_name, value)
    if value not in CAPACITY_PRESSURE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    normalized = tuple(_require_non_empty_string(field_name, item) for item in value)
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


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(numerator / denominator)


def _clamp_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return min(ONE, max(ZERO, value)).quantize(SCORE_QUANT)


def _require_sha256_digest(field_name: str, value: object) -> None:
    _require_non_empty_string(field_name, value)
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
    if value is None or type(value) in (str, bool):
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


def _verify_payload_digest(payload: dict[str, Any]) -> None:
    _reject_unsafe_public_payload("public payload", payload)
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest is required")
    _require_sha256_digest("derived_validation_digest", digest)
    if digest != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public payload in {label}")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if value is None or type(value) in (Decimal, datetime, bool):
        return
    raise ValueError(f"unsafe public payload in {label}")


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"unsafe public payload in {label}")
