"""Readonly research team capacity planner."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
import json
import re
from typing import Any, Sequence


DEFAULT_RESEARCH_TEAM_CAPACITY_PLANNER_CONFIG_VERSION = (
    "research-team-capacity-planner-v1"
)

_QUANT = Decimal("0.000001")
_COUNT_QUANT = Decimal("1")
_ZERO = Decimal("0.000000")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_STATUSES = ("block", "watch", "pass")
_CAPACITY_PLANS = (
    "block_role_or_domain_gap",
    "block_capacity_pressure",
    "watch_capacity_pressure",
    "watch_sla_pressure",
    "maintain_capacity",
)
_REASON_CODE_SEQUENCE = (
    "capacity_plan_pass",
    "capacity_plan_watch",
    "capacity_plan_block",
    "queue_pressure_watch",
    "queue_pressure_block",
    "sla_watch",
    "sla_block",
    "domain_coverage_complete",
    "domain_coverage_gap_block",
    "specialist_role_covered",
    "specialist_role_gap_block",
    "available_capacity_present",
    "available_capacity_block",
)
_UNSAFE_PUBLIC_TERMS = (
    "raw",
    "candidate",
    "market",
    "slug",
    "question",
    "source",
    "ref",
    "url",
    "dsn",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "position",
    "buy",
    "sell",
    "recommendation",
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_CAPACITY_PLANNER_CONFIG_VERSION",
    "ResearchTeamCapacityPlannerConfig",
    "ResearchTeamCapacityPlannerInput",
    "ResearchTeamCapacityPlannerReasonCodeCount",
    "ResearchTeamCapacityPlannerRow",
    "ResearchTeamCapacityPlannerReport",
    "build_research_team_capacity_plan",
    "research_team_capacity_plan_payload",
)


@dataclass(frozen=True)
class ResearchTeamCapacityPlannerConfig:
    config_version: str = DEFAULT_RESEARCH_TEAM_CAPACITY_PLANNER_CONFIG_VERSION
    watch_queue_pressure_ratio: Decimal = Decimal("0.750000")
    block_queue_pressure_ratio: Decimal = Decimal("1.000000")
    watch_sla_breach_count: Decimal = Decimal("1.000000")
    block_sla_breach_count: Decimal = Decimal("3.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamCapacityPlannerConfig:
            raise ValueError("config must be exactly ResearchTeamCapacityPlannerConfig")
        _require_public_identifier("config_version", self.config_version)
        for field_name in ("watch_queue_pressure_ratio", "block_queue_pressure_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("watch_sla_breach_count", "block_sla_breach_count"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchTeamCapacityPlannerInput:
    team_code: str
    domain_code: str
    specialist_role_code: str
    queued_item_count: Decimal
    active_item_count: Decimal
    capacity_item_count: Decimal
    sla_breach_count: Decimal
    required_domain_count: Decimal
    covered_domain_count: Decimal
    required_specialist_count: Decimal
    staffed_specialist_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamCapacityPlannerInput:
            raise ValueError("input must be exactly ResearchTeamCapacityPlannerInput")
        for field_name in ("team_code", "domain_code", "specialist_role_code"):
            _require_public_identifier(field_name, getattr(self, field_name))
        for field_name in (
            "queued_item_count",
            "active_item_count",
            "sla_breach_count",
            "covered_domain_count",
            "staffed_specialist_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "capacity_item_count",
            "required_domain_count",
            "required_specialist_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.covered_domain_count > self.required_domain_count:
            raise ValueError("covered_domain_count must not exceed required_domain_count")
        if self.staffed_specialist_count > self.required_specialist_count:
            raise ValueError(
                "staffed_specialist_count must not exceed required_specialist_count",
            )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchTeamCapacityPlannerReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamCapacityPlannerReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchTeamCapacityPlannerReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        _require_hard_flags("reason code count", self)
        _reject_unsafe_public_payload("reason code count", self)


@dataclass(frozen=True)
class ResearchTeamCapacityPlannerRow:
    team_code: str
    domain_code: str
    specialist_role_code: str
    queued_item_count: Decimal
    active_item_count: Decimal
    capacity_item_count: Decimal
    sla_breach_count: Decimal
    required_domain_count: Decimal
    covered_domain_count: Decimal
    required_specialist_count: Decimal
    staffed_specialist_count: Decimal
    queue_pressure_ratio: Decimal
    available_item_count: Decimal
    domain_coverage_ratio: Decimal
    domain_coverage_gap: Decimal
    specialist_role_gap: Decimal
    status: str
    capacity_plan: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamCapacityPlannerRow:
            raise ValueError("row must be exactly ResearchTeamCapacityPlannerRow")
        for field_name in ("team_code", "domain_code", "specialist_role_code"):
            _require_public_identifier(field_name, getattr(self, field_name))
        for field_name in (
            "queued_item_count",
            "active_item_count",
            "sla_breach_count",
            "covered_domain_count",
            "staffed_specialist_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "capacity_item_count",
            "required_domain_count",
            "required_specialist_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "queue_pressure_ratio",
            "domain_coverage_ratio",
            "domain_coverage_gap",
            "specialist_role_gap",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "available_item_count",
            _require_decimal("available_item_count", self.available_item_count),
        )
        _require_status("status", self.status)
        _require_capacity_plan("capacity_plan", self.capacity_plan)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchTeamCapacityPlannerReport:
    generated_at: datetime
    config_version: str
    report_status: str
    team_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_queue_pressure_ratio: Decimal
    total_specialist_role_gap: Decimal
    total_domain_coverage_gap: Decimal
    total_sla_breach_count: Decimal
    reason_code_counts: tuple[ResearchTeamCapacityPlannerReasonCodeCount, ...]
    rows: tuple[ResearchTeamCapacityPlannerRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamCapacityPlannerReport:
            raise ValueError("report must be exactly ResearchTeamCapacityPlannerReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        _require_status("report_status", self.report_status)
        for field_name in (
            "team_count",
            "pass_count",
            "watch_count",
            "block_count",
            "total_sla_breach_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_queue_pressure_ratio",
            "total_specialist_role_gap",
            "total_domain_coverage_gap",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
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


def build_research_team_capacity_plan(
    inputs: Sequence[ResearchTeamCapacityPlannerInput],
    *,
    generated_at: datetime,
    config: ResearchTeamCapacityPlannerConfig | None = None,
) -> ResearchTeamCapacityPlannerReport:
    if config is None:
        config = ResearchTeamCapacityPlannerConfig()
    if type(config) is not ResearchTeamCapacityPlannerConfig:
        raise ValueError("config must be exactly ResearchTeamCapacityPlannerConfig")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (_row_for_input(item, config=config) for item in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "report_status": _report_status(rows),
        "team_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "max_queue_pressure_ratio": _max_queue_pressure_ratio(rows),
        "total_specialist_role_gap": _sum_decimals(
            row.specialist_role_gap for row in rows
        ),
        "total_domain_coverage_gap": _sum_decimals(row.domain_coverage_gap for row in rows),
        "total_sla_breach_count": _sum_decimals(row.sla_breach_count for row in rows),
        "reason_code_counts": _reason_code_counts(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchTeamCapacityPlannerReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_team_capacity_plan_payload(
    report: ResearchTeamCapacityPlannerReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamCapacityPlannerReport:
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
    raise ValueError("report must be a ResearchTeamCapacityPlannerReport or payload")


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


def _row_for_input(
    item: ResearchTeamCapacityPlannerInput,
    *,
    config: ResearchTeamCapacityPlannerConfig,
) -> ResearchTeamCapacityPlannerRow:
    queue_pressure_ratio = _ratio(
        item.queued_item_count + item.active_item_count,
        item.capacity_item_count,
    )
    available_item_count = _quantize(
        item.capacity_item_count - item.active_item_count - item.queued_item_count,
    )
    domain_coverage_ratio = _ratio(item.covered_domain_count, item.required_domain_count)
    domain_coverage_gap = _quantize(
        item.required_domain_count - item.covered_domain_count,
    )
    specialist_role_gap = _quantize(
        item.required_specialist_count - item.staffed_specialist_count,
    )
    status = _row_status(
        queue_pressure_ratio=queue_pressure_ratio,
        available_item_count=available_item_count,
        domain_coverage_gap=domain_coverage_gap,
        specialist_role_gap=specialist_role_gap,
        sla_breach_count=item.sla_breach_count,
        config=config,
    )
    return ResearchTeamCapacityPlannerRow(
        team_code=item.team_code,
        domain_code=item.domain_code,
        specialist_role_code=item.specialist_role_code,
        queued_item_count=item.queued_item_count,
        active_item_count=item.active_item_count,
        capacity_item_count=item.capacity_item_count,
        sla_breach_count=item.sla_breach_count,
        required_domain_count=item.required_domain_count,
        covered_domain_count=item.covered_domain_count,
        required_specialist_count=item.required_specialist_count,
        staffed_specialist_count=item.staffed_specialist_count,
        queue_pressure_ratio=queue_pressure_ratio,
        available_item_count=available_item_count,
        domain_coverage_ratio=domain_coverage_ratio,
        domain_coverage_gap=domain_coverage_gap,
        specialist_role_gap=specialist_role_gap,
        status=status,
        capacity_plan=_capacity_plan(
            status=status,
            queue_pressure_ratio=queue_pressure_ratio,
            available_item_count=available_item_count,
            domain_coverage_gap=domain_coverage_gap,
            specialist_role_gap=specialist_role_gap,
            sla_breach_count=item.sla_breach_count,
            config=config,
        ),
        reason_codes=_row_reason_codes(
            status=status,
            queue_pressure_ratio=queue_pressure_ratio,
            available_item_count=available_item_count,
            domain_coverage_gap=domain_coverage_gap,
            specialist_role_gap=specialist_role_gap,
            sla_breach_count=item.sla_breach_count,
            config=config,
        ),
    )


def _row_status(
    *,
    queue_pressure_ratio: Decimal,
    available_item_count: Decimal,
    domain_coverage_gap: Decimal,
    specialist_role_gap: Decimal,
    sla_breach_count: Decimal,
    config: ResearchTeamCapacityPlannerConfig,
) -> str:
    if (
        domain_coverage_gap > _ZERO
        or specialist_role_gap > _ZERO
        or available_item_count <= _ZERO
        or queue_pressure_ratio >= config.block_queue_pressure_ratio
        or sla_breach_count >= config.block_sla_breach_count
    ):
        return "block"
    if (
        queue_pressure_ratio >= config.watch_queue_pressure_ratio
        or sla_breach_count >= config.watch_sla_breach_count
    ):
        return "watch"
    return "pass"


def _capacity_plan(
    *,
    status: str,
    queue_pressure_ratio: Decimal,
    available_item_count: Decimal,
    domain_coverage_gap: Decimal,
    specialist_role_gap: Decimal,
    sla_breach_count: Decimal,
    config: ResearchTeamCapacityPlannerConfig,
) -> str:
    if status == "block" and (domain_coverage_gap > _ZERO or specialist_role_gap > _ZERO):
        return "block_role_or_domain_gap"
    if status == "block":
        return "block_capacity_pressure"
    if queue_pressure_ratio >= config.watch_queue_pressure_ratio:
        return "watch_capacity_pressure"
    if sla_breach_count >= config.watch_sla_breach_count:
        return "watch_sla_pressure"
    if available_item_count <= _ZERO:
        return "block_capacity_pressure"
    return "maintain_capacity"


def _row_reason_codes(
    *,
    status: str,
    queue_pressure_ratio: Decimal,
    available_item_count: Decimal,
    domain_coverage_gap: Decimal,
    specialist_role_gap: Decimal,
    sla_breach_count: Decimal,
    config: ResearchTeamCapacityPlannerConfig,
) -> tuple[str, ...]:
    codes = [f"capacity_plan_{status}"]
    if queue_pressure_ratio >= config.block_queue_pressure_ratio:
        codes.append("queue_pressure_block")
    elif queue_pressure_ratio >= config.watch_queue_pressure_ratio:
        codes.append("queue_pressure_watch")
    if sla_breach_count >= config.block_sla_breach_count:
        codes.append("sla_block")
    elif sla_breach_count >= config.watch_sla_breach_count:
        codes.append("sla_watch")
    if domain_coverage_gap > _ZERO:
        codes.append("domain_coverage_gap_block")
    else:
        codes.append("domain_coverage_complete")
    if specialist_role_gap > _ZERO:
        codes.append("specialist_role_gap_block")
    else:
        codes.append("specialist_role_covered")
    if available_item_count <= _ZERO:
        codes.append("available_capacity_block")
    else:
        codes.append("available_capacity_present")
    return _normalize_reason_codes(tuple(codes))


def _report_status(rows: tuple[ResearchTeamCapacityPlannerRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _row_sort_key(row: ResearchTeamCapacityPlannerRow) -> tuple[int, str, str, str]:
    return (
        _STATUSES.index(row.status),
        row.team_code,
        row.domain_code,
        row.specialist_role_code,
    )


def _status_count(rows: tuple[ResearchTeamCapacityPlannerRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _reason_count(rows: tuple[ResearchTeamCapacityPlannerRow, ...], reason_code: str) -> int:
    return sum(1 for row in rows if reason_code in row.reason_codes)


def _reason_code_counts(
    rows: tuple[ResearchTeamCapacityPlannerRow, ...],
) -> tuple[ResearchTeamCapacityPlannerReasonCodeCount, ...]:
    return tuple(
        ResearchTeamCapacityPlannerReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(_reason_count(rows, reason_code)),
        )
        for reason_code in _REASON_CODE_SEQUENCE
        if _reason_count(rows, reason_code) > 0
    )


def _max_queue_pressure_ratio(rows: tuple[ResearchTeamCapacityPlannerRow, ...]) -> Decimal:
    if not rows:
        return _ZERO
    return max(row.queue_pressure_ratio for row in rows)


def _normalize_inputs(
    inputs: Sequence[ResearchTeamCapacityPlannerInput],
) -> tuple[ResearchTeamCapacityPlannerInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Sequence):
        raise ValueError("inputs must be a sequence")
    normalized: list[ResearchTeamCapacityPlannerInput] = []
    seen_keys: set[tuple[str, str, str]] = set()
    for item in inputs:
        if type(item) is not ResearchTeamCapacityPlannerInput:
            raise ValueError("inputs must contain ResearchTeamCapacityPlannerInput")
        _require_hard_flags("input", item)
        key = (item.team_code, item.domain_code, item.specialist_role_code)
        if key in seen_keys:
            raise ValueError("duplicate team/domain/role input")
        seen_keys.add(key)
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (item.team_code, item.domain_code, item.specialist_role_code),
        ),
    )


def _normalize_rows(
    rows: Sequence[ResearchTeamCapacityPlannerRow],
) -> tuple[ResearchTeamCapacityPlannerRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchTeamCapacityPlannerRow] = []
    seen_keys: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not ResearchTeamCapacityPlannerRow:
            raise ValueError("rows must contain ResearchTeamCapacityPlannerRow")
        _require_hard_flags("row", row)
        key = (row.team_code, row.domain_code, row.specialist_role_code)
        if key in seen_keys:
            raise ValueError("duplicate team/domain/role row")
        seen_keys.add(key)
        normalized.append(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    items: Sequence[ResearchTeamCapacityPlannerReasonCodeCount],
) -> tuple[ResearchTeamCapacityPlannerReasonCodeCount, ...]:
    if isinstance(items, (str, bytes)) or not isinstance(items, Sequence):
        raise ValueError("reason_code_counts must be a sequence")
    normalized: list[ResearchTeamCapacityPlannerReasonCodeCount] = []
    seen_codes: set[str] = set()
    for item in items:
        if type(item) is not ResearchTeamCapacityPlannerReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTeamCapacityPlannerReasonCodeCount",
            )
        _require_hard_flags("reason code count", item)
        if item.reason_code in seen_codes:
            raise ValueError("duplicate reason_code_counts reason_code")
        seen_codes.add(item.reason_code)
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: _REASON_CODE_SEQUENCE.index(item.reason_code),
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
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _validate_config(config: ResearchTeamCapacityPlannerConfig) -> None:
    if config.watch_queue_pressure_ratio > config.block_queue_pressure_ratio:
        raise ValueError(
            "watch_queue_pressure_ratio must not exceed block_queue_pressure_ratio",
        )
    if config.watch_sla_breach_count > config.block_sla_breach_count:
        raise ValueError("watch_sla_breach_count must not exceed block_sla_breach_count")


def _validate_row(row: ResearchTeamCapacityPlannerRow) -> None:
    expected_status_code = f"capacity_plan_{row.status}"
    if expected_status_code not in row.reason_codes:
        raise ValueError("row status must match reason_codes")
    if row.covered_domain_count > row.required_domain_count:
        raise ValueError("covered_domain_count must not exceed required_domain_count")
    if row.staffed_specialist_count > row.required_specialist_count:
        raise ValueError(
            "staffed_specialist_count must not exceed required_specialist_count",
        )
    if row.queue_pressure_ratio != _ratio(
        row.queued_item_count + row.active_item_count,
        row.capacity_item_count,
    ):
        raise ValueError("queue_pressure_ratio must match queued plus active over capacity")
    if row.available_item_count != _quantize(
        row.capacity_item_count - row.active_item_count - row.queued_item_count,
    ):
        raise ValueError("available_item_count must match capacity less queued and active")
    if row.domain_coverage_ratio != _ratio(
        row.covered_domain_count,
        row.required_domain_count,
    ):
        raise ValueError("domain_coverage_ratio must match covered over required")
    if row.domain_coverage_gap != _quantize(
        row.required_domain_count - row.covered_domain_count,
    ):
        raise ValueError("domain_coverage_gap must match required less covered")
    if row.specialist_role_gap != _quantize(
        row.required_specialist_count - row.staffed_specialist_count,
    ):
        raise ValueError("specialist_role_gap must match required less staffed")
    if row.status == "pass" and (
        "domain_coverage_complete" not in row.reason_codes
        or "specialist_role_covered" not in row.reason_codes
        or "available_capacity_present" not in row.reason_codes
    ):
        raise ValueError("pass rows must include complete coverage reasons")


def _validate_report(report: ResearchTeamCapacityPlannerReport) -> None:
    rows = report.rows
    if report.team_count != _decimal_count(len(rows)):
        raise ValueError("team_count must match rows")
    if report.pass_count != _decimal_count(_status_count(rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(rows, "block")):
        raise ValueError("block_count must match rows")
    if report.max_queue_pressure_ratio != _max_queue_pressure_ratio(rows):
        raise ValueError("max_queue_pressure_ratio must match rows")
    if report.total_specialist_role_gap != _sum_decimals(
        row.specialist_role_gap for row in rows
    ):
        raise ValueError("total_specialist_role_gap must match rows")
    if report.total_domain_coverage_gap != _sum_decimals(
        row.domain_coverage_gap for row in rows
    ):
        raise ValueError("total_domain_coverage_gap must match rows")
    if report.total_sla_breach_count != _sum_decimals(row.sla_breach_count for row in rows):
        raise ValueError("total_sla_breach_count must match rows")
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
    report: ResearchTeamCapacityPlannerReport,
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


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= _ZERO:
        raise ValueError("ratio denominator must be positive")
    return _quantize(numerator / denominator)


def _sum_decimals(values: Any) -> Decimal:
    total = _ZERO
    for value in values:
        total = _quantize(total + value)
    return total


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _reject_unsafe_public_string(field_name, value)
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    _require_public_identifier(field_name, value)
    if value not in _REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a supported reason code")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be pass/watch/block")
    return value


def _require_capacity_plan(field_name: str, value: object) -> str:
    _require_public_identifier(field_name, value)
    if value not in _CAPACITY_PLANS:
        raise ValueError(f"{field_name} must be a supported capacity plan")
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
