"""Phase 1 readonly team-domain specialist capacity queue."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
import json
import re
from typing import Any, Sequence


DEFAULT_TEAM_DOMAIN_SPECIALIST_CAPACITY_QUEUE_V2_CONFIG_VERSION = (
    "team-domain-specialist-capacity-queue-v2"
)

_QUANT = Decimal("0.000001")
_COUNT_QUANT = Decimal("1")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_ROW_STATUSES = ("block", "watch", "pass")
_REPORT_STATUSES = ("empty", "block", "watch", "pass")
_ROW_REASON_CODE_SEQUENCE = (
    "specialist_capacity_pass",
    "specialist_capacity_watch",
    "specialist_capacity_block",
    "specialist_capacity_available",
    "specialist_capacity_no_available_capacity",
    "specialist_capacity_over_capacity",
    "specialist_capacity_overdue",
    "specialist_capacity_high_priority_pressure",
    "specialist_capacity_stale_assignment",
    "specialist_capacity_assignment_current",
    "specialist_capacity_utilization_watch",
)
_UNSAFE_PUBLIC_TERMS = (
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
    "DEFAULT_TEAM_DOMAIN_SPECIALIST_CAPACITY_QUEUE_V2_CONFIG_VERSION",
    "TeamDomainSpecialistCapacityQueueV2Config",
    "TeamDomainSpecialistCapacityQueueV2Input",
    "TeamDomainSpecialistCapacityQueueV2ReasonCodeCount",
    "TeamDomainSpecialistCapacityQueueV2Row",
    "TeamDomainSpecialistCapacityQueueV2Report",
    "build_team_domain_specialist_capacity_queue_v2",
    "team_domain_specialist_capacity_queue_v2_payload",
)


@dataclass(frozen=True)
class TeamDomainSpecialistCapacityQueueV2Config:
    config_version: str = DEFAULT_TEAM_DOMAIN_SPECIALIST_CAPACITY_QUEUE_V2_CONFIG_VERSION
    watch_utilization_ratio: Decimal = Decimal("0.800000")
    block_utilization_ratio: Decimal = Decimal("1.000000")
    overdue_watch_count: Decimal = Decimal("1.000000")
    high_priority_watch_count: Decimal = Decimal("2.000000")
    stale_assignment_after_seconds: Decimal = Decimal("604800.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not TeamDomainSpecialistCapacityQueueV2Config:
            raise ValueError(
                "config must be exactly TeamDomainSpecialistCapacityQueueV2Config",
            )
        _require_public_identifier("config_version", self.config_version)
        for field_name in ("watch_utilization_ratio", "block_utilization_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("overdue_watch_count", "high_priority_watch_count"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "stale_assignment_after_seconds",
            _require_positive_decimal(
                "stale_assignment_after_seconds",
                self.stale_assignment_after_seconds,
            ),
        )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class TeamDomainSpecialistCapacityQueueV2Input:
    team_id: str
    domain: str
    active_packet_count: Decimal
    max_packet_capacity: Decimal
    overdue_packet_count: Decimal
    high_priority_packet_count: Decimal
    latest_assignment_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not TeamDomainSpecialistCapacityQueueV2Input:
            raise ValueError(
                "assignment must be exactly TeamDomainSpecialistCapacityQueueV2Input",
            )
        _require_public_identifier("team_id", self.team_id)
        _require_public_identifier("domain", self.domain)
        object.__setattr__(
            self,
            "active_packet_count",
            _require_nonnegative_count_decimal(
                "active_packet_count",
                self.active_packet_count,
            ),
        )
        object.__setattr__(
            self,
            "max_packet_capacity",
            _require_positive_count_decimal(
                "max_packet_capacity",
                self.max_packet_capacity,
            ),
        )
        for field_name in ("overdue_packet_count", "high_priority_packet_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.overdue_packet_count > self.active_packet_count:
            raise ValueError(
                "overdue_packet_count must not exceed active_packet_count",
            )
        if self.high_priority_packet_count > self.active_packet_count:
            raise ValueError(
                "high_priority_packet_count must not exceed active_packet_count",
            )
        object.__setattr__(
            self,
            "latest_assignment_at",
            _as_utc("latest_assignment_at", self.latest_assignment_at),
        )
        _require_hard_flags("assignment", self)
        _reject_unsafe_public_payload("assignment", self)


@dataclass(frozen=True)
class TeamDomainSpecialistCapacityQueueV2ReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not TeamDomainSpecialistCapacityQueueV2ReasonCodeCount:
            raise ValueError(
                "reason_code_count must be exactly "
                "TeamDomainSpecialistCapacityQueueV2ReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class TeamDomainSpecialistCapacityQueueV2Row:
    team_id: str
    domain: str
    active_packet_count: Decimal
    max_packet_capacity: Decimal
    overdue_packet_count: Decimal
    high_priority_packet_count: Decimal
    latest_assignment_at: datetime
    utilization_ratio: Decimal
    capacity_gap: Decimal
    assignment_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not TeamDomainSpecialistCapacityQueueV2Row:
            raise ValueError("row must be exactly TeamDomainSpecialistCapacityQueueV2Row")
        _require_public_identifier("team_id", self.team_id)
        _require_public_identifier("domain", self.domain)
        object.__setattr__(
            self,
            "active_packet_count",
            _require_nonnegative_count_decimal(
                "active_packet_count",
                self.active_packet_count,
            ),
        )
        object.__setattr__(
            self,
            "max_packet_capacity",
            _require_positive_count_decimal(
                "max_packet_capacity",
                self.max_packet_capacity,
            ),
        )
        for field_name in ("overdue_packet_count", "high_priority_packet_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.overdue_packet_count > self.active_packet_count:
            raise ValueError(
                "overdue_packet_count must not exceed active_packet_count",
            )
        if self.high_priority_packet_count > self.active_packet_count:
            raise ValueError(
                "high_priority_packet_count must not exceed active_packet_count",
            )
        object.__setattr__(
            self,
            "latest_assignment_at",
            _as_utc("latest_assignment_at", self.latest_assignment_at),
        )
        object.__setattr__(
            self,
            "utilization_ratio",
            _require_nonnegative_decimal("utilization_ratio", self.utilization_ratio),
        )
        object.__setattr__(
            self,
            "capacity_gap",
            _require_decimal("capacity_gap", self.capacity_gap),
        )
        object.__setattr__(
            self,
            "assignment_age_seconds",
            _require_nonnegative_decimal(
                "assignment_age_seconds",
                self.assignment_age_seconds,
            ),
        )
        _require_row_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class TeamDomainSpecialistCapacityQueueV2Report:
    generated_at: datetime
    config_version: str
    report_status: str
    team_domain_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    over_capacity_count: Decimal
    overdue_count: Decimal
    high_priority_pressure_count: Decimal
    max_utilization_ratio: Decimal
    reason_code_counts: tuple[TeamDomainSpecialistCapacityQueueV2ReasonCodeCount, ...]
    rows: tuple[TeamDomainSpecialistCapacityQueueV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not TeamDomainSpecialistCapacityQueueV2Report:
            raise ValueError(
                "report must be exactly TeamDomainSpecialistCapacityQueueV2Report",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        _require_report_status("report_status", self.report_status)
        for field_name in (
            "team_domain_count",
            "pass_count",
            "watch_count",
            "block_count",
            "over_capacity_count",
            "overdue_count",
            "high_priority_pressure_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_utilization_ratio",
            _require_nonnegative_decimal(
                "max_utilization_ratio",
                self.max_utilization_ratio,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest:
            _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report contents")
        object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        _reject_unsafe_public_payload("payload", payload)
        _require_hard_flags("payload", _DictFlags(payload))
        _validate_payload_digest(payload)
        return payload


def build_team_domain_specialist_capacity_queue_v2(
    assignments: Sequence[TeamDomainSpecialistCapacityQueueV2Input],
    *,
    generated_at: datetime,
    config: TeamDomainSpecialistCapacityQueueV2Config | None = None,
) -> TeamDomainSpecialistCapacityQueueV2Report:
    if config is None:
        config = TeamDomainSpecialistCapacityQueueV2Config()
    if type(config) is not TeamDomainSpecialistCapacityQueueV2Config:
        raise ValueError(
            "config must be a TeamDomainSpecialistCapacityQueueV2Config",
        )
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_assignments = _normalize_assignments(assignments)
    for assignment in normalized_assignments:
        if assignment.latest_assignment_at > generated_at:
            raise ValueError("latest_assignment_at must not be after generated_at")
    rows = tuple(
        sorted(
            (
                _row_for_assignment(
                    assignment,
                    generated_at=generated_at,
                    config=config,
                )
                for assignment in normalized_assignments
            ),
            key=_row_sort_key,
        ),
    )
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "report_status": _report_status(rows),
        "team_domain_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "over_capacity_count": _decimal_count(
            _reason_count(rows, "specialist_capacity_over_capacity"),
        ),
        "overdue_count": _decimal_count(
            _reason_count(rows, "specialist_capacity_overdue"),
        ),
        "high_priority_pressure_count": _decimal_count(
            _reason_count(rows, "specialist_capacity_high_priority_pressure"),
        ),
        "max_utilization_ratio": _max_utilization_ratio(rows),
        "reason_code_counts": _reason_code_counts(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return TeamDomainSpecialistCapacityQueueV2Report(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def team_domain_specialist_capacity_queue_v2_payload(
    report: TeamDomainSpecialistCapacityQueueV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is TeamDomainSpecialistCapacityQueueV2Report:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        return report.payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        _require_hard_flags("payload", _DictFlags(payload))
        _validate_payload_digest(payload)
        _reject_unsafe_public_payload("payload", payload)
        return payload
    raise ValueError(
        "report must be a TeamDomainSpecialistCapacityQueueV2Report or payload",
    )


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


def _row_for_assignment(
    assignment: TeamDomainSpecialistCapacityQueueV2Input,
    *,
    generated_at: datetime,
    config: TeamDomainSpecialistCapacityQueueV2Config,
) -> TeamDomainSpecialistCapacityQueueV2Row:
    utilization_ratio = _utilization_ratio(
        assignment.active_packet_count,
        assignment.max_packet_capacity,
    )
    capacity_gap = _quantize(
        assignment.max_packet_capacity - assignment.active_packet_count,
    )
    assignment_age_seconds = _age_seconds(
        assignment.latest_assignment_at,
        generated_at,
    )
    stale_assignment = assignment_age_seconds > config.stale_assignment_after_seconds
    status = _row_status(
        utilization_ratio=utilization_ratio,
        capacity_gap=capacity_gap,
        overdue_packet_count=assignment.overdue_packet_count,
        high_priority_packet_count=assignment.high_priority_packet_count,
        stale_assignment=stale_assignment,
        config=config,
    )
    return TeamDomainSpecialistCapacityQueueV2Row(
        team_id=assignment.team_id,
        domain=assignment.domain,
        active_packet_count=assignment.active_packet_count,
        max_packet_capacity=assignment.max_packet_capacity,
        overdue_packet_count=assignment.overdue_packet_count,
        high_priority_packet_count=assignment.high_priority_packet_count,
        latest_assignment_at=assignment.latest_assignment_at,
        utilization_ratio=utilization_ratio,
        capacity_gap=capacity_gap,
        assignment_age_seconds=assignment_age_seconds,
        status=status,
        reason_codes=_row_reason_codes(
            assignment,
            utilization_ratio=utilization_ratio,
            capacity_gap=capacity_gap,
            stale_assignment=stale_assignment,
            status=status,
            config=config,
        ),
    )


def _utilization_ratio(active_packet_count: Decimal, max_packet_capacity: Decimal) -> Decimal:
    return _quantize(active_packet_count / max_packet_capacity)


def _row_status(
    *,
    utilization_ratio: Decimal,
    capacity_gap: Decimal,
    overdue_packet_count: Decimal,
    high_priority_packet_count: Decimal,
    stale_assignment: bool,
    config: TeamDomainSpecialistCapacityQueueV2Config,
) -> str:
    if capacity_gap <= _ZERO or utilization_ratio >= config.block_utilization_ratio:
        return "block"
    if (
        utilization_ratio >= config.watch_utilization_ratio
        or overdue_packet_count >= config.overdue_watch_count
        or high_priority_packet_count >= config.high_priority_watch_count
        or stale_assignment
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    assignment: TeamDomainSpecialistCapacityQueueV2Input,
    *,
    utilization_ratio: Decimal,
    capacity_gap: Decimal,
    stale_assignment: bool,
    status: str,
    config: TeamDomainSpecialistCapacityQueueV2Config,
) -> tuple[str, ...]:
    codes = [f"specialist_capacity_{status}"]
    if capacity_gap < _ZERO:
        codes.append("specialist_capacity_over_capacity")
    elif capacity_gap == _ZERO:
        codes.append("specialist_capacity_no_available_capacity")
    if assignment.overdue_packet_count >= config.overdue_watch_count:
        codes.append("specialist_capacity_overdue")
    if assignment.high_priority_packet_count >= config.high_priority_watch_count:
        codes.append("specialist_capacity_high_priority_pressure")
    if stale_assignment:
        codes.append("specialist_capacity_stale_assignment")
    elif status == "pass":
        codes.append("specialist_capacity_assignment_current")
    if status == "pass" and capacity_gap > _ZERO:
        codes.append("specialist_capacity_available")
    if len(codes) == 1 and utilization_ratio >= config.watch_utilization_ratio:
        codes.append("specialist_capacity_utilization_watch")
    return _normalize_reason_codes(tuple(codes))


def _report_status(
    rows: tuple[TeamDomainSpecialistCapacityQueueV2Row, ...],
) -> str:
    if not rows:
        return "empty"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _row_sort_key(
    row: TeamDomainSpecialistCapacityQueueV2Row,
) -> tuple[int, Decimal, str, str]:
    return (
        _ROW_STATUSES.index(row.status),
        -row.utilization_ratio,
        row.team_id,
        row.domain,
    )


def _status_count(
    rows: tuple[TeamDomainSpecialistCapacityQueueV2Row, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _reason_count(
    rows: tuple[TeamDomainSpecialistCapacityQueueV2Row, ...],
    reason_code: str,
) -> int:
    return sum(1 for row in rows if reason_code in row.reason_codes)


def _reason_code_counts(
    rows: tuple[TeamDomainSpecialistCapacityQueueV2Row, ...],
) -> tuple[TeamDomainSpecialistCapacityQueueV2ReasonCodeCount, ...]:
    return tuple(
        TeamDomainSpecialistCapacityQueueV2ReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(_reason_count(rows, reason_code)),
        )
        for reason_code in _ROW_REASON_CODE_SEQUENCE
        if _reason_count(rows, reason_code) > 0
    )


def _max_utilization_ratio(
    rows: tuple[TeamDomainSpecialistCapacityQueueV2Row, ...],
) -> Decimal:
    if not rows:
        return _ZERO
    return max(row.utilization_ratio for row in rows)


def _normalize_assignments(
    assignments: Sequence[TeamDomainSpecialistCapacityQueueV2Input],
) -> tuple[TeamDomainSpecialistCapacityQueueV2Input, ...]:
    if isinstance(assignments, (str, bytes)) or not isinstance(assignments, Sequence):
        raise ValueError("assignments must be a sequence")
    normalized: list[TeamDomainSpecialistCapacityQueueV2Input] = []
    seen_keys: set[tuple[str, str]] = set()
    for assignment in assignments:
        if type(assignment) is not TeamDomainSpecialistCapacityQueueV2Input:
            raise ValueError(
                "assignments must contain TeamDomainSpecialistCapacityQueueV2Input",
            )
        _require_hard_flags("assignment", assignment)
        key = (assignment.team_id, assignment.domain)
        if key in seen_keys:
            raise ValueError("duplicate team/domain assignment")
        seen_keys.add(key)
        normalized.append(assignment)
    return tuple(sorted(normalized, key=lambda item: (item.team_id, item.domain)))


def _normalize_rows(
    rows: Sequence[TeamDomainSpecialistCapacityQueueV2Row],
) -> tuple[TeamDomainSpecialistCapacityQueueV2Row, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[TeamDomainSpecialistCapacityQueueV2Row] = []
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not TeamDomainSpecialistCapacityQueueV2Row:
            raise ValueError("rows must contain TeamDomainSpecialistCapacityQueueV2Row")
        _require_hard_flags("row", row)
        key = (row.team_id, row.domain)
        if key in seen_keys:
            raise ValueError("duplicate team/domain row")
        seen_keys.add(key)
        normalized.append(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    reason_code_counts: Sequence[TeamDomainSpecialistCapacityQueueV2ReasonCodeCount],
) -> tuple[TeamDomainSpecialistCapacityQueueV2ReasonCodeCount, ...]:
    if (
        isinstance(reason_code_counts, (str, bytes))
        or not isinstance(reason_code_counts, Sequence)
    ):
        raise ValueError("reason_code_counts must be a sequence")
    normalized: list[TeamDomainSpecialistCapacityQueueV2ReasonCodeCount] = []
    seen_codes: set[str] = set()
    for item in reason_code_counts:
        if type(item) is not TeamDomainSpecialistCapacityQueueV2ReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "TeamDomainSpecialistCapacityQueueV2ReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", item)
        if item.reason_code in seen_codes:
            raise ValueError("duplicate reason_code_counts reason_code")
        seen_codes.add(item.reason_code)
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: _ROW_REASON_CODE_SEQUENCE.index(item.reason_code),
        ),
    )


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(
        reason_code
        for reason_code in _ROW_REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _validate_config(config: TeamDomainSpecialistCapacityQueueV2Config) -> None:
    if config.watch_utilization_ratio > config.block_utilization_ratio:
        raise ValueError(
            "watch_utilization_ratio must not exceed block_utilization_ratio",
        )


def _validate_row(row: TeamDomainSpecialistCapacityQueueV2Row) -> None:
    expected_status_code = f"specialist_capacity_{row.status}"
    if expected_status_code not in row.reason_codes:
        raise ValueError("row status must match reason_codes")
    expected_gap = _quantize(row.max_packet_capacity - row.active_packet_count)
    if row.capacity_gap != expected_gap:
        raise ValueError("capacity_gap must match max capacity minus active packets")
    expected_utilization = _utilization_ratio(
        row.active_packet_count,
        row.max_packet_capacity,
    )
    if row.utilization_ratio != expected_utilization:
        raise ValueError("utilization_ratio must match active packets over capacity")
    if row.capacity_gap < _ZERO and (
        "specialist_capacity_over_capacity" not in row.reason_codes
    ):
        raise ValueError("over-capacity rows must include over-capacity reason")
    if row.status == "pass" and (
        "specialist_capacity_available" not in row.reason_codes
        or "specialist_capacity_assignment_current" not in row.reason_codes
    ):
        raise ValueError("pass rows must include available current capacity reasons")


def _validate_report(report: TeamDomainSpecialistCapacityQueueV2Report) -> None:
    rows = report.rows
    if report.team_domain_count != _decimal_count(len(rows)):
        raise ValueError("team_domain_count must match rows")
    if report.pass_count != _decimal_count(_status_count(rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(rows, "block")):
        raise ValueError("block_count must match rows")
    if report.over_capacity_count != _decimal_count(
        _reason_count(rows, "specialist_capacity_over_capacity"),
    ):
        raise ValueError("over_capacity_count must match rows")
    if report.overdue_count != _decimal_count(
        _reason_count(rows, "specialist_capacity_overdue"),
    ):
        raise ValueError("overdue_count must match rows")
    if report.high_priority_pressure_count != _decimal_count(
        _reason_count(rows, "specialist_capacity_high_priority_pressure"),
    ):
        raise ValueError("high_priority_pressure_count must match rows")
    if report.max_utilization_ratio != _max_utilization_ratio(rows):
        raise ValueError("max_utilization_ratio must match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    if digest != _digest_for_json_payload(payload):
        raise ValueError("derived_validation_digest must match report contents")


def _report_values_without_digest(
    report: TeamDomainSpecialistCapacityQueueV2Report,
) -> dict[str, object]:
    return {
        field.name: getattr(report, field.name)
        for field in fields(report)
        if field.name != "derived_validation_digest"
    }


def _report_digest_from_values(values: dict[str, object]) -> str:
    return _digest_for_json_payload(_json_ready(values))


def _digest_for_json_payload(payload: dict[str, Any]) -> str:
    payload_without_digest = {
        key: value for key, value in payload.items() if key != "derived_validation_digest"
    }
    canonical_payload = json.dumps(
        payload_without_digest,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical_payload.encode("utf-8")).hexdigest()


def _age_seconds(value: datetime, generated_at: datetime) -> Decimal:
    if value >= generated_at:
        return _ZERO
    delta = generated_at - value
    seconds = (
        Decimal(delta.days) * Decimal("86400")
        + Decimal(delta.seconds)
        + Decimal(delta.microseconds) / Decimal("1000000")
    )
    return _quantize(seconds)


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    _require_public_identifier(field_name, value)
    if value not in _ROW_REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a supported reason code")
    return value


def _require_row_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _ROW_STATUSES:
        raise ValueError(f"{field_name} must be a known row status")
    return value


def _require_report_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _REPORT_STATUSES:
        raise ValueError(f"{field_name} must be a known report status")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = _quantize(value)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized.quantize(_COUNT_QUANT) != normalized:
        raise ValueError(f"{field_name} must be a whole number")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        _reject_unsafe_public_string(path or label, value)
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            _reject_unsafe_public_key(key, path or label)
            if key in _PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    raise ValueError("value is not JSON serializable")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON value must not be an int")
    if type(value) is bool or type(value) is str:
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")
