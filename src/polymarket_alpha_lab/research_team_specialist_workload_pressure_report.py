"""Public-safe specialist workload pressure report reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import InitVar, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_RESEARCH_TEAM_SPECIALIST_WORKLOAD_PRESSURE_REPORT_CONFIG_VERSION = (
    "research-team-specialist-workload-pressure-report-v0"
)

STATUSES = ("pass", "watch", "block")

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
MICROSECONDS_PER_SECOND = Decimal("1000000")

STATUS_WEIGHT = {
    "block": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
PAPER_ACTION_BY_STATUS = {
    "pass": "paper_specialist_workload_monitor",
    "watch": "paper_specialist_workload_watch",
    "block": "paper_specialist_workload_block",
}

PASS_ROW_REASON_CODE = "specialist_workload_clear"
EMPTY_REPORT_REASON_CODE = "specialist_workload_no_teams"
REPORT_PASS_REASON_CODE = "specialist_workload_report_clear"
REPORT_WATCH_REASON_CODE = "specialist_workload_report_watch"
REPORT_BLOCK_REASON_CODE = "specialist_workload_report_block"

PENDING_PACKET_BLOCK_REASON = "specialist_workload_pending_packet_block"
REVIEWER_AVAILABILITY_BLOCK_REASON = (
    "specialist_workload_reviewer_availability_block"
)
SLA_AGE_BLOCK_REASON = "specialist_workload_sla_age_block"
UNRESOLVED_ESCALATION_BLOCK_REASON = (
    "specialist_workload_unresolved_escalation_block"
)
MEMORY_WRITEBACK_BLOCK_REASON = "specialist_workload_memory_writeback_block"

PENDING_PACKET_WATCH_REASON = "specialist_workload_pending_packet_watch"
REVIEWER_AVAILABILITY_WATCH_REASON = (
    "specialist_workload_reviewer_availability_watch"
)
SLA_AGE_WATCH_REASON = "specialist_workload_sla_age_watch"
UNRESOLVED_ESCALATION_WATCH_REASON = (
    "specialist_workload_unresolved_escalation_watch"
)
MEMORY_WRITEBACK_WATCH_REASON = "specialist_workload_memory_writeback_watch"

BLOCK_REASON_CODES = (
    PENDING_PACKET_BLOCK_REASON,
    REVIEWER_AVAILABILITY_BLOCK_REASON,
    SLA_AGE_BLOCK_REASON,
    UNRESOLVED_ESCALATION_BLOCK_REASON,
    MEMORY_WRITEBACK_BLOCK_REASON,
)
WATCH_REASON_CODES = (
    PENDING_PACKET_WATCH_REASON,
    REVIEWER_AVAILABILITY_WATCH_REASON,
    SLA_AGE_WATCH_REASON,
    UNRESOLVED_ESCALATION_WATCH_REASON,
    MEMORY_WRITEBACK_WATCH_REASON,
)
ROW_REASON_CODES = BLOCK_REASON_CODES + WATCH_REASON_CODES + (PASS_ROW_REASON_CODE,)
REPORT_REASON_PREFIX_BY_STATUS = {
    "pass": REPORT_PASS_REASON_CODE,
    "watch": REPORT_WATCH_REASON_CODE,
    "block": REPORT_BLOCK_REASON_CODE,
}
REPORT_REASON_CODES = (
    EMPTY_REPORT_REASON_CODE,
    REPORT_PASS_REASON_CODE,
    REPORT_WATCH_REASON_CODE,
    REPORT_BLOCK_REASON_CODE,
) + BLOCK_REASON_CODES + WATCH_REASON_CODES
REASON_CODE_COUNT_PRIORITY = (
    EMPTY_REPORT_REASON_CODE,
    *BLOCK_REASON_CODES,
    *WATCH_REASON_CODES,
    PASS_ROW_REASON_CODE,
)

HEX_CHARS = frozenset("0123456789abcdef")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        _join_parts("mar", "ket"),
        _join_parts("candi", "date"),
        _join_parts("sl", "ug"),
        _join_parts("ques", "tion"),
        _join_parts("so", "urce"),
        _join_parts("u", "rl"),
        _join_parts("d", "sn"),
        _join_parts("ta", "ble"),
        _join_parts("to", "ken"),
        _join_parts("_", "id"),
        _join_parts("id", "_"),
        _join_parts("tex", "t"),
        _join_parts("wa", "llet"),
        _join_parts("au", "th"),
        _join_parts("or", "der"),
        _join_parts("tr", "ade"),
        _join_parts("li", "ve"),
        _join_parts("data", "base"),
        _join_parts("net", "work"),
        _join_parts("bro", "ker"),
        _join_parts("execution"),
        _join_parts("account"),
        _join_parts("private", "_", "key"),
        _join_parts("sign", "ing"),
        _join_parts("position"),
        _join_parts("buy"),
        _join_parts("sell"),
        _join_parts("recom", "mendation"),
        _join_parts("siz", "ing"),
    ),
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise ValueError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchTeamSpecialistWorkloadPressureConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_SPECIALIST_WORKLOAD_PRESSURE_REPORT_CONFIG_VERSION
    )
    max_pass_pending_packet_count: Decimal = Decimal("5")
    max_watch_pending_packet_count: Decimal = Decimal("12")
    min_pass_reviewer_available_count: Decimal = Decimal("2")
    min_watch_reviewer_available_count: Decimal = Decimal("1")
    max_pass_sla_age_hours: Decimal = Decimal("8.000000")
    max_watch_sla_age_hours: Decimal = Decimal("24.000000")
    max_pass_unresolved_escalation_count: Decimal = Decimal("0")
    max_watch_unresolved_escalation_count: Decimal = Decimal("2")
    max_pass_memory_writeback_delay_hours: Decimal = Decimal("12.000000")
    max_watch_memory_writeback_delay_hours: Decimal = Decimal("48.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistWorkloadPressureConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_SPECIALIST_WORKLOAD_PRESSURE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_pass_pending_packet_count",
            "max_watch_pending_packet_count",
            "min_pass_reviewer_available_count",
            "min_watch_reviewer_available_count",
            "max_pass_unresolved_escalation_count",
            "max_watch_unresolved_escalation_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_sla_age_hours",
            "max_watch_sla_age_hours",
            "max_pass_memory_writeback_delay_hours",
            "max_watch_memory_writeback_delay_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistWorkloadPressureInput(_FinalPublicDataclass):
    team_key: str
    team_domain: str
    observed_at: datetime
    pending_packet_count: Decimal
    reviewer_available_count: Decimal
    oldest_sla_age_hours: Decimal
    unresolved_escalation_count: Decimal
    memory_writeback_delay_hours: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSpecialistWorkloadPressureInput, "input")
        _require_safe_team_key("team_key", self.team_key)
        _require_safe_team_key("team_domain", self.team_domain)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "pending_packet_count",
            "reviewer_available_count",
            "unresolved_escalation_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "oldest_sla_age_hours",
            "memory_writeback_delay_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistWorkloadPressureRow(_FinalPublicDataclass):
    team_key: str
    team_domain: str
    workload_status: str
    generated_at: datetime
    observed_at: datetime
    observation_age_seconds: Decimal
    pending_packet_count: Decimal
    reviewer_available_count: Decimal
    oldest_sla_age_hours: Decimal
    unresolved_escalation_count: Decimal
    memory_writeback_delay_hours: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[
        ResearchTeamSpecialistWorkloadPressureConfig | None
    ] = None

    def __post_init__(
        self,
        validation_config: ResearchTeamSpecialistWorkloadPressureConfig | None,
    ) -> None:
        _require_exact_type(self, ResearchTeamSpecialistWorkloadPressureRow, "row")
        _require_safe_team_key("team_key", self.team_key)
        _require_safe_team_key("team_domain", self.team_domain)
        _require_status("workload_status", self.workload_status)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "observation_age_seconds",
            _require_nonnegative_decimal(
                "observation_age_seconds",
                self.observation_age_seconds,
            ),
        )
        for field_name in (
            "pending_packet_count",
            "reviewer_available_count",
            "unresolved_escalation_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "oldest_sla_age_hours",
            "memory_writeback_delay_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes),
        )
        _validate_row(self, config=validation_config)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistWorkloadPressureReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    team_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistWorkloadPressureReasonCodeCount,
            "reason_code_count",
        )
        _require_public_string("reason_code", self.reason_code)
        if self.reason_code not in REASON_CODE_COUNT_PRIORITY:
            raise ValueError("reason_code must be supported")
        object.__setattr__(self, "count", _require_count_decimal("count", self.count))
        object.__setattr__(
            self,
            "team_ratio",
            _require_ratio_decimal("team_ratio", self.team_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistWorkloadPressureReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    specialist_team_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    overloaded_team_count: Decimal
    total_pending_packet_count: Decimal
    total_reviewer_available_count: Decimal
    pending_packet_pressure_team_count: Decimal
    reviewer_gap_team_count: Decimal
    sla_breach_team_count: Decimal
    unresolved_escalation_team_count: Decimal
    memory_writeback_delay_team_count: Decimal
    max_pending_packet_count: Decimal
    min_reviewer_available_count: Decimal
    max_sla_age_hours: Decimal
    max_unresolved_escalation_count: Decimal
    max_memory_writeback_delay_hours: Decimal
    status: str
    paper_queue_action: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchTeamSpecialistWorkloadPressureReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchTeamSpecialistWorkloadPressureRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSpecialistWorkloadPressureReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_SPECIALIST_WORKLOAD_PRESSURE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "specialist_team_count",
            "pass_count",
            "watch_count",
            "block_count",
            "overloaded_team_count",
            "total_pending_packet_count",
            "total_reviewer_available_count",
            "pending_packet_pressure_team_count",
            "reviewer_gap_team_count",
            "sla_breach_team_count",
            "unresolved_escalation_team_count",
            "memory_writeback_delay_team_count",
            "max_pending_packet_count",
            "min_reviewer_available_count",
            "max_unresolved_escalation_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_sla_age_hours",
            "max_memory_writeback_delay_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        _require_public_string("paper_queue_action", self.paper_queue_action)
        object.__setattr__(self, "rows", _require_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _require_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _require_reason_code_counts(self.reason_code_counts),
        )
        if self.status != _rollup_status(tuple(row.workload_status for row in self.rows)):
            raise ValueError("status must match rows")
        if self.paper_queue_action != PAPER_ACTION_BY_STATUS[self.status]:
            raise ValueError("paper_queue_action must match status")
        if self.derived_validation_digest:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != _derived_validation_digest(self):
                raise ValueError("derived_validation_digest does not match report payload")
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _derived_validation_digest(self),
            )
        _validate_report_materialized_fields(self)
        _reject_unsafe_public_payload("report", self)
        _require_hard_flags("report", self)


def build_research_team_specialist_workload_pressure_report(
    workload_items: Iterable[ResearchTeamSpecialistWorkloadPressureInput],
    *,
    config: ResearchTeamSpecialistWorkloadPressureConfig,
    generated_at: datetime,
) -> ResearchTeamSpecialistWorkloadPressureReport:
    if type(config) is not ResearchTeamSpecialistWorkloadPressureConfig:
        raise ValueError("config must be a ResearchTeamSpecialistWorkloadPressureConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(workload_items)
    rows = tuple(
        sorted(
            (
                _row_from_input(item, config=config, generated_at=generated_at_utc)
                for item in inputs
            ),
            key=_row_sort_key,
        ),
    )
    status = _rollup_status(tuple(row.workload_status for row in rows))
    return ResearchTeamSpecialistWorkloadPressureReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        specialist_team_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        overloaded_team_count=_count(
            sum(row.workload_status != "pass" for row in rows),
        ),
        total_pending_packet_count=_sum_decimal(
            tuple(row.pending_packet_count for row in rows),
        ),
        total_reviewer_available_count=_sum_decimal(
            tuple(row.reviewer_available_count for row in rows),
        ),
        pending_packet_pressure_team_count=_reason_team_count(
            rows,
            PENDING_PACKET_BLOCK_REASON,
            PENDING_PACKET_WATCH_REASON,
        ),
        reviewer_gap_team_count=_reason_team_count(
            rows,
            REVIEWER_AVAILABILITY_BLOCK_REASON,
            REVIEWER_AVAILABILITY_WATCH_REASON,
        ),
        sla_breach_team_count=_reason_team_count(
            rows,
            SLA_AGE_BLOCK_REASON,
            SLA_AGE_WATCH_REASON,
        ),
        unresolved_escalation_team_count=_reason_team_count(
            rows,
            UNRESOLVED_ESCALATION_BLOCK_REASON,
            UNRESOLVED_ESCALATION_WATCH_REASON,
        ),
        memory_writeback_delay_team_count=_reason_team_count(
            rows,
            MEMORY_WRITEBACK_BLOCK_REASON,
            MEMORY_WRITEBACK_WATCH_REASON,
        ),
        max_pending_packet_count=_max_decimal(
            tuple(row.pending_packet_count for row in rows),
            count=True,
        ),
        min_reviewer_available_count=_min_decimal(
            tuple(row.reviewer_available_count for row in rows),
            count=True,
        ),
        max_sla_age_hours=_max_decimal(tuple(row.oldest_sla_age_hours for row in rows)),
        max_unresolved_escalation_count=_max_decimal(
            tuple(row.unresolved_escalation_count for row in rows),
            count=True,
        ),
        max_memory_writeback_delay_hours=_max_decimal(
            tuple(row.memory_writeback_delay_hours for row in rows),
        ),
        status=status,
        paper_queue_action=PAPER_ACTION_BY_STATUS[status],
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_team_specialist_workload_pressure_report_payload(
    report: ResearchTeamSpecialistWorkloadPressureReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamSpecialistWorkloadPressureReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        if report.derived_validation_digest != _derived_validation_digest(report):
            raise ValueError("derived_validation_digest does not match report payload")
        _validate_report_materialized_fields(report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be an object")
        _reject_unsafe_public_payload("payload", payload)
        _reject_public_numeric_values(payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _reject_public_numeric_values(report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be an object")
        parsed_payload = _validate_public_payload_contract(payload)
        _require_hard_flags("payload", _PayloadFlags(payload))
        supplied_digest = payload.get("derived_validation_digest")
        if type(supplied_digest) is not str:
            raise ValueError("derived_validation_digest is required")
        _require_sha256("derived_validation_digest", supplied_digest)
        if supplied_digest != _payload_validation_digest(payload):
            raise ValueError("derived_validation_digest does not match report payload")
        _validate_report_materialized_fields(parsed_payload)
        return payload
    raise ValueError("report must be a ResearchTeamSpecialistWorkloadPressureReport")


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


@dataclass(frozen=True)
class _PublicPayloadRow:
    team_key: str
    team_domain: str
    workload_status: str
    generated_at: datetime
    observed_at: datetime
    observation_age_seconds: Decimal
    pending_packet_count: Decimal
    reviewer_available_count: Decimal
    oldest_sla_age_hours: Decimal
    unresolved_escalation_count: Decimal
    memory_writeback_delay_hours: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool
    report_only: bool
    readonly: bool


@dataclass(frozen=True)
class _PublicPayloadReport:
    generated_at: datetime
    config_version: str
    specialist_team_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    overloaded_team_count: Decimal
    total_pending_packet_count: Decimal
    total_reviewer_available_count: Decimal
    pending_packet_pressure_team_count: Decimal
    reviewer_gap_team_count: Decimal
    sla_breach_team_count: Decimal
    unresolved_escalation_team_count: Decimal
    memory_writeback_delay_team_count: Decimal
    max_pending_packet_count: Decimal
    min_reviewer_available_count: Decimal
    max_sla_age_hours: Decimal
    max_unresolved_escalation_count: Decimal
    max_memory_writeback_delay_hours: Decimal
    status: str
    paper_queue_action: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchTeamSpecialistWorkloadPressureReasonCodeCount,
        ...,
    ]
    rows: tuple[_PublicPayloadRow, ...]
    derived_validation_digest: str
    paper_only: bool
    report_only: bool
    readonly: bool


def _normalize_inputs(
    workload_items: Iterable[ResearchTeamSpecialistWorkloadPressureInput],
) -> tuple[ResearchTeamSpecialistWorkloadPressureInput, ...]:
    if isinstance(workload_items, (str, bytes)):
        raise ValueError("workload_items must be an iterable")
    try:
        items = tuple(workload_items)
    except TypeError as exc:
        raise ValueError("workload_items must be an iterable") from exc
    seen: set[str] = set()
    for item in items:
        if type(item) is not ResearchTeamSpecialistWorkloadPressureInput:
            raise ValueError(
                "workload_items must contain "
                "ResearchTeamSpecialistWorkloadPressureInput",
            )
        _require_hard_flags("input", item)
        if item.team_key in seen:
            raise ValueError("team_key values must be unique")
        seen.add(item.team_key)
    return items


def _row_from_input(
    item: ResearchTeamSpecialistWorkloadPressureInput,
    *,
    config: ResearchTeamSpecialistWorkloadPressureConfig,
    generated_at: datetime,
) -> ResearchTeamSpecialistWorkloadPressureRow:
    if item.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    reason_codes = _row_reason_codes(item, config=config)
    return ResearchTeamSpecialistWorkloadPressureRow(
        team_key=item.team_key,
        team_domain=item.team_domain,
        workload_status=_row_status(reason_codes),
        generated_at=generated_at,
        observed_at=item.observed_at,
        observation_age_seconds=_datetime_delta_seconds(generated_at, item.observed_at),
        pending_packet_count=item.pending_packet_count,
        reviewer_available_count=item.reviewer_available_count,
        oldest_sla_age_hours=item.oldest_sla_age_hours,
        unresolved_escalation_count=item.unresolved_escalation_count,
        memory_writeback_delay_hours=item.memory_writeback_delay_hours,
        reason_codes=reason_codes,
        validation_config=config,
    )


def _row_reason_codes(
    item: ResearchTeamSpecialistWorkloadPressureInput,
    *,
    config: ResearchTeamSpecialistWorkloadPressureConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if item.pending_packet_count > config.max_watch_pending_packet_count:
        reason_codes.append(PENDING_PACKET_BLOCK_REASON)
    elif item.pending_packet_count > config.max_pass_pending_packet_count:
        reason_codes.append(PENDING_PACKET_WATCH_REASON)

    if item.reviewer_available_count < config.min_watch_reviewer_available_count:
        reason_codes.append(REVIEWER_AVAILABILITY_BLOCK_REASON)
    elif item.reviewer_available_count < config.min_pass_reviewer_available_count:
        reason_codes.append(REVIEWER_AVAILABILITY_WATCH_REASON)

    if item.oldest_sla_age_hours > config.max_watch_sla_age_hours:
        reason_codes.append(SLA_AGE_BLOCK_REASON)
    elif item.oldest_sla_age_hours > config.max_pass_sla_age_hours:
        reason_codes.append(SLA_AGE_WATCH_REASON)

    if item.unresolved_escalation_count > config.max_watch_unresolved_escalation_count:
        reason_codes.append(UNRESOLVED_ESCALATION_BLOCK_REASON)
    elif item.unresolved_escalation_count > config.max_pass_unresolved_escalation_count:
        reason_codes.append(UNRESOLVED_ESCALATION_WATCH_REASON)

    if item.memory_writeback_delay_hours > config.max_watch_memory_writeback_delay_hours:
        reason_codes.append(MEMORY_WRITEBACK_BLOCK_REASON)
    elif item.memory_writeback_delay_hours > config.max_pass_memory_writeback_delay_hours:
        reason_codes.append(MEMORY_WRITEBACK_WATCH_REASON)

    if not reason_codes:
        reason_codes.append(PASS_ROW_REASON_CODE)
    return tuple(
        reason_code for reason_code in ROW_REASON_CODES if reason_code in reason_codes
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "pass"


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if not statuses:
        return "block"
    if any(status == "block" for status in statuses):
        return "block"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamSpecialistWorkloadPressureRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REPORT_REASON_CODE,)
    status = _rollup_status(tuple(row.workload_status for row in rows))
    reason_codes = [REPORT_REASON_PREFIX_BY_STATUS[status]]
    row_reasons = frozenset(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != PASS_ROW_REASON_CODE
    )
    for reason_code in BLOCK_REASON_CODES + WATCH_REASON_CODES:
        if reason_code in row_reasons:
            reason_codes.append(reason_code)
    return tuple(reason_codes)


def _reason_code_counts(
    rows: tuple[ResearchTeamSpecialistWorkloadPressureRow, ...],
) -> tuple[ResearchTeamSpecialistWorkloadPressureReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchTeamSpecialistWorkloadPressureReasonCodeCount(
                reason_code=EMPTY_REPORT_REASON_CODE,
                count=_count(1),
                team_ratio=ONE_RATIO,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    denominator = _count(len(rows))
    priority = {
        reason_code: index
        for index, reason_code in enumerate(REASON_CODE_COUNT_PRIORITY)
    }
    return tuple(
        ResearchTeamSpecialistWorkloadPressureReasonCodeCount(
            reason_code=reason_code,
            count=count,
            team_ratio=_ratio(count, denominator),
        )
        for count, reason_code in sorted(
            ((_count(count), reason_code) for reason_code, count in counter.items()),
            key=lambda item: (-item[0], priority.get(item[1], 999), item[1]),
        )
    )


def _row_sort_key(
    row: ResearchTeamSpecialistWorkloadPressureRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, str, str]:
    return (
        -STATUS_WEIGHT[row.workload_status],
        -_row_severity_score(row),
        -row.pending_packet_count,
        row.reviewer_available_count,
        row.team_domain,
        row.team_key,
    )


def _row_severity_score(row: ResearchTeamSpecialistWorkloadPressureRow) -> Decimal:
    severity = STATUS_WEIGHT[row.workload_status]
    severity += _count(sum(reason != PASS_ROW_REASON_CODE for reason in row.reason_codes))
    severity += row.oldest_sla_age_hours / Decimal("1000")
    severity += row.memory_writeback_delay_hours / Decimal("1000")
    return _quantize_ratio(severity)


def _status_count(
    rows: tuple[ResearchTeamSpecialistWorkloadPressureRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(row.workload_status == status for row in rows))


def _reason_team_count(
    rows: tuple[ResearchTeamSpecialistWorkloadPressureRow, ...],
    *reason_codes: str,
) -> Decimal:
    return _count(
        sum(any(reason_code in row.reason_codes for reason_code in reason_codes) for row in rows),
    )


def _validate_config(config: ResearchTeamSpecialistWorkloadPressureConfig) -> None:
    if config.max_pass_pending_packet_count > config.max_watch_pending_packet_count:
        raise ValueError(
            "max_watch_pending_packet_count must be at least "
            "max_pass_pending_packet_count",
        )
    if config.min_watch_reviewer_available_count > config.min_pass_reviewer_available_count:
        raise ValueError(
            "min_watch_reviewer_available_count must not exceed "
            "min_pass_reviewer_available_count",
        )
    if config.max_pass_sla_age_hours > config.max_watch_sla_age_hours:
        raise ValueError(
            "max_watch_sla_age_hours must be at least max_pass_sla_age_hours",
        )
    if (
        config.max_pass_unresolved_escalation_count
        > config.max_watch_unresolved_escalation_count
    ):
        raise ValueError(
            "max_watch_unresolved_escalation_count must be at least "
            "max_pass_unresolved_escalation_count",
        )
    if (
        config.max_pass_memory_writeback_delay_hours
        > config.max_watch_memory_writeback_delay_hours
    ):
        raise ValueError(
            "max_watch_memory_writeback_delay_hours must be at least "
            "max_pass_memory_writeback_delay_hours",
        )


def _validate_row(
    row: ResearchTeamSpecialistWorkloadPressureRow,
    *,
    config: ResearchTeamSpecialistWorkloadPressureConfig | None,
) -> None:
    cfg = config or ResearchTeamSpecialistWorkloadPressureConfig()
    if type(cfg) is not ResearchTeamSpecialistWorkloadPressureConfig:
        raise ValueError("validation_config must be ResearchTeamSpecialistWorkloadPressureConfig")
    if row.observed_at > row.generated_at:
        raise ValueError("observed_at must not be in the future")
    if row.observation_age_seconds != _datetime_delta_seconds(
        row.generated_at,
        row.observed_at,
    ):
        raise ValueError("observation_age_seconds must match generated_at and observed_at")
    expected_reasons = _row_reason_codes(
        ResearchTeamSpecialistWorkloadPressureInput(
            team_key=row.team_key,
            team_domain=row.team_domain,
            observed_at=row.observed_at,
            pending_packet_count=row.pending_packet_count,
            reviewer_available_count=row.reviewer_available_count,
            oldest_sla_age_hours=row.oldest_sla_age_hours,
            unresolved_escalation_count=row.unresolved_escalation_count,
            memory_writeback_delay_hours=row.memory_writeback_delay_hours,
        ),
        config=cfg,
    )
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match row inputs")
    if row.workload_status != _row_status(row.reason_codes):
        raise ValueError("workload_status must match reason_codes")


def _validate_report_materialized_fields(
    report: ResearchTeamSpecialistWorkloadPressureReport,
) -> None:
    rows = report.rows
    if any(row.generated_at != report.generated_at for row in rows):
        raise ValueError("rows generated_at must match report generated_at")
    checks = {
        "specialist_team_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "overloaded_team_count": _count(
            sum(row.workload_status != "pass" for row in rows),
        ),
        "total_pending_packet_count": _sum_decimal(
            tuple(row.pending_packet_count for row in rows),
        ),
        "total_reviewer_available_count": _sum_decimal(
            tuple(row.reviewer_available_count for row in rows),
        ),
        "pending_packet_pressure_team_count": _reason_team_count(
            rows,
            PENDING_PACKET_BLOCK_REASON,
            PENDING_PACKET_WATCH_REASON,
        ),
        "reviewer_gap_team_count": _reason_team_count(
            rows,
            REVIEWER_AVAILABILITY_BLOCK_REASON,
            REVIEWER_AVAILABILITY_WATCH_REASON,
        ),
        "sla_breach_team_count": _reason_team_count(
            rows,
            SLA_AGE_BLOCK_REASON,
            SLA_AGE_WATCH_REASON,
        ),
        "unresolved_escalation_team_count": _reason_team_count(
            rows,
            UNRESOLVED_ESCALATION_BLOCK_REASON,
            UNRESOLVED_ESCALATION_WATCH_REASON,
        ),
        "memory_writeback_delay_team_count": _reason_team_count(
            rows,
            MEMORY_WRITEBACK_BLOCK_REASON,
            MEMORY_WRITEBACK_WATCH_REASON,
        ),
        "max_pending_packet_count": _max_decimal(
            tuple(row.pending_packet_count for row in rows),
            count=True,
        ),
        "min_reviewer_available_count": _min_decimal(
            tuple(row.reviewer_available_count for row in rows),
            count=True,
        ),
        "max_sla_age_hours": _max_decimal(tuple(row.oldest_sla_age_hours for row in rows)),
        "max_unresolved_escalation_count": _max_decimal(
            tuple(row.unresolved_escalation_count for row in rows),
            count=True,
        ),
        "max_memory_writeback_delay_hours": _max_decimal(
            tuple(row.memory_writeback_delay_hours for row in rows),
        ),
    }
    for field_name, expected in checks.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.status != _rollup_status(tuple(row.workload_status for row in rows)):
        raise ValueError("status must match rows")
    if report.paper_queue_action != PAPER_ACTION_BY_STATUS[report.status]:
        raise ValueError("paper_queue_action must match status")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _require_rows(
    rows: tuple[ResearchTeamSpecialistWorkloadPressureRow, ...],
) -> tuple[ResearchTeamSpecialistWorkloadPressureRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchTeamSpecialistWorkloadPressureRow:
            raise ValueError("rows must contain ResearchTeamSpecialistWorkloadPressureRow")
        _require_hard_flags("row", row)
        if row.team_key in seen:
            raise ValueError("rows must contain unique team_key values")
        seen.add(row.team_key)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted by status and team_key")
    return normalized


def _require_reason_code_counts(
    rows: tuple[ResearchTeamSpecialistWorkloadPressureReasonCodeCount, ...],
) -> tuple[ResearchTeamSpecialistWorkloadPressureReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for row in normalized:
        if type(row) is not ResearchTeamSpecialistWorkloadPressureReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTeamSpecialistWorkloadPressureReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", row)
    if len({row.reason_code for row in normalized}) != len(normalized):
        raise ValueError("reason_code_counts reason_code values must be unique")
    return normalized


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    require_paper_only_flags(label, value)


def _require_safe_team_key(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be lowercase snake case")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical non-empty string")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")
    _reject_unsafe_public_text(field_name, value)


def _require_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not normalized:
        raise ValueError("reason_codes must be non-empty")
    for reason_code in normalized:
        _require_public_string("reason_code", reason_code)
        if reason_code not in ROW_REASON_CODES:
            raise ValueError("reason_code must be supported")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    if normalized != tuple(reason for reason in ROW_REASON_CODES if reason in normalized):
        raise ValueError("reason_codes must be sorted")
    if PASS_ROW_REASON_CODE in normalized and len(normalized) != 1:
        raise ValueError("pass reason_codes must not be mixed with workload reasons")
    return normalized


def _require_report_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not normalized:
        raise ValueError("reason_codes must be non-empty")
    for reason_code in normalized:
        _require_public_string("reason_code", reason_code)
        if reason_code not in REPORT_REASON_CODES:
            raise ValueError("reason_code must be supported")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    return normalized


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if value.is_nan() or value.is_infinite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be non-negative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return normalized.quantize(COUNT_QUANTUM)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be non-negative")
    return _quantize_ratio(normalized)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must be no greater than 1")
    return normalized


def _quantize_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO_COUNT:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(RATIO_QUANTUM)


def _datetime_delta_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    micros = (
        Decimal(delta.days) * Decimal("86400000000")
        + Decimal(delta.seconds) * Decimal("1000000")
        + Decimal(delta.microseconds)
    )
    return _quantize_ratio(micros / MICROSECONDS_PER_SECOND)


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO_COUNT
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("sum values must be Decimal")
        total += value
    return total.quantize(COUNT_QUANTUM)


def _max_decimal(values: tuple[Decimal, ...], *, count: bool = False) -> Decimal:
    if not values:
        return ZERO_COUNT if count else ZERO_RATIO
    value = max(values)
    return value.quantize(COUNT_QUANTUM if count else RATIO_QUANTUM)


def _min_decimal(values: tuple[Decimal, ...], *, count: bool = False) -> Decimal:
    if not values:
        return ZERO_COUNT if count else ZERO_RATIO
    value = min(values)
    return value.quantize(COUNT_QUANTUM if count else RATIO_QUANTUM)


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if len(value) != 64 or any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _derived_validation_digest(
    report: ResearchTeamSpecialistWorkloadPressureReport,
) -> str:
    payload = _json_ready_without_digest(report)
    return _payload_validation_digest(payload)


def _payload_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = _strip_digest(payload)
    canonical = json.dumps(digest_payload, sort_keys=True, separators=(",", ":"))
    return sha256(canonical.encode("utf-8")).hexdigest()


def _strip_digest(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _strip_digest(item)
            for key, item in sorted(value.items())
            if key != "derived_validation_digest"
        }
    if isinstance(value, list):
        return [_strip_digest(item) for item in value]
    return value


def _json_ready_without_digest(
    report: ResearchTeamSpecialistWorkloadPressureReport,
) -> dict[str, Any]:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be an object")
    payload.pop("derived_validation_digest", None)
    return payload


def _json_ready(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) is Decimal:
        return str(value)
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return {str(key): _json_ready(item) for key, item in value.items()}
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported payload value type: {type(value).__name__}")


def _reject_public_numeric_values(value: object) -> None:
    if type(value) in (int, float):
        raise ValueError("public payload numeric values must be Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_numeric_values(item)


def _validate_public_payload_contract(
    value: object,
    path: str = "payload",
) -> _PublicPayloadReport:
    payload = _require_public_payload_object(
        value,
        path,
        _public_payload_keys(ResearchTeamSpecialistWorkloadPressureReport),
    )
    rows = _public_payload_rows(payload["rows"], f"{path}.rows")
    _require_public_rows(rows, f"{path}.rows")
    reason_code_counts = _public_payload_reason_code_counts(
        payload["reason_code_counts"],
        f"{path}.reason_code_counts",
    )
    return _PublicPayloadReport(
        generated_at=_public_datetime(
            "generated_at",
            payload["generated_at"],
            f"{path}.generated_at",
        ),
        config_version=_public_config_version(
            "config_version",
            payload["config_version"],
            f"{path}.config_version",
        ),
        specialist_team_count=_public_count_decimal(
            "specialist_team_count",
            payload["specialist_team_count"],
            f"{path}.specialist_team_count",
        ),
        pass_count=_public_count_decimal(
            "pass_count",
            payload["pass_count"],
            f"{path}.pass_count",
        ),
        watch_count=_public_count_decimal(
            "watch_count",
            payload["watch_count"],
            f"{path}.watch_count",
        ),
        block_count=_public_count_decimal(
            "block_count",
            payload["block_count"],
            f"{path}.block_count",
        ),
        overloaded_team_count=_public_count_decimal(
            "overloaded_team_count",
            payload["overloaded_team_count"],
            f"{path}.overloaded_team_count",
        ),
        total_pending_packet_count=_public_count_decimal(
            "total_pending_packet_count",
            payload["total_pending_packet_count"],
            f"{path}.total_pending_packet_count",
        ),
        total_reviewer_available_count=_public_count_decimal(
            "total_reviewer_available_count",
            payload["total_reviewer_available_count"],
            f"{path}.total_reviewer_available_count",
        ),
        pending_packet_pressure_team_count=_public_count_decimal(
            "pending_packet_pressure_team_count",
            payload["pending_packet_pressure_team_count"],
            f"{path}.pending_packet_pressure_team_count",
        ),
        reviewer_gap_team_count=_public_count_decimal(
            "reviewer_gap_team_count",
            payload["reviewer_gap_team_count"],
            f"{path}.reviewer_gap_team_count",
        ),
        sla_breach_team_count=_public_count_decimal(
            "sla_breach_team_count",
            payload["sla_breach_team_count"],
            f"{path}.sla_breach_team_count",
        ),
        unresolved_escalation_team_count=_public_count_decimal(
            "unresolved_escalation_team_count",
            payload["unresolved_escalation_team_count"],
            f"{path}.unresolved_escalation_team_count",
        ),
        memory_writeback_delay_team_count=_public_count_decimal(
            "memory_writeback_delay_team_count",
            payload["memory_writeback_delay_team_count"],
            f"{path}.memory_writeback_delay_team_count",
        ),
        max_pending_packet_count=_public_count_decimal(
            "max_pending_packet_count",
            payload["max_pending_packet_count"],
            f"{path}.max_pending_packet_count",
        ),
        min_reviewer_available_count=_public_count_decimal(
            "min_reviewer_available_count",
            payload["min_reviewer_available_count"],
            f"{path}.min_reviewer_available_count",
        ),
        max_sla_age_hours=_public_nonnegative_decimal(
            "max_sla_age_hours",
            payload["max_sla_age_hours"],
            f"{path}.max_sla_age_hours",
        ),
        max_unresolved_escalation_count=_public_count_decimal(
            "max_unresolved_escalation_count",
            payload["max_unresolved_escalation_count"],
            f"{path}.max_unresolved_escalation_count",
        ),
        max_memory_writeback_delay_hours=_public_nonnegative_decimal(
            "max_memory_writeback_delay_hours",
            payload["max_memory_writeback_delay_hours"],
            f"{path}.max_memory_writeback_delay_hours",
        ),
        status=_public_status("status", payload["status"], f"{path}.status"),
        paper_queue_action=_public_string(
            "paper_queue_action",
            payload["paper_queue_action"],
            f"{path}.paper_queue_action",
        ),
        reason_codes=_public_report_reason_codes(
            payload["reason_codes"],
            f"{path}.reason_codes",
        ),
        reason_code_counts=reason_code_counts,
        rows=rows,
        derived_validation_digest=_public_sha256(
            "derived_validation_digest",
            payload["derived_validation_digest"],
            f"{path}.derived_validation_digest",
        ),
        paper_only=_public_true_flag(payload["paper_only"], f"{path}.paper_only"),
        report_only=_public_true_flag(payload["report_only"], f"{path}.report_only"),
        readonly=_public_true_flag(payload["readonly"], f"{path}.readonly"),
    )


def _public_payload_keys(dataclass_type: type[object]) -> tuple[str, ...]:
    return tuple(field.name for field in fields(dataclass_type))


def _require_public_payload_object(
    value: object,
    path: str,
    expected_keys: tuple[str, ...],
) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError(f"{path} must be an object")
    for key in value:
        if type(key) is not str:
            raise ValueError(f"{path} contains unsafe public key")
    expected = frozenset(expected_keys)
    for key in expected_keys:
        if key not in value:
            raise ValueError(f"{path}.{key} is required")
    for key in value:
        if key not in expected:
            raise ValueError(f"{path}.{key} is unexpected")
    return value


def _public_payload_rows(value: object, path: str) -> tuple[_PublicPayloadRow, ...]:
    if type(value) is not list:
        raise ValueError(f"{path} must be a list")
    return tuple(
        _public_payload_row(item, f"{path}[{index}]")
        for index, item in enumerate(value)
    )


def _public_payload_row(value: object, path: str) -> _PublicPayloadRow:
    payload = _require_public_payload_object(
        value,
        path,
        _public_payload_keys(ResearchTeamSpecialistWorkloadPressureRow),
    )
    generated_at = _public_datetime(
        "generated_at",
        payload["generated_at"],
        f"{path}.generated_at",
    )
    observed_at = _public_datetime(
        "observed_at",
        payload["observed_at"],
        f"{path}.observed_at",
    )
    observation_age_seconds = _public_nonnegative_decimal(
        "observation_age_seconds",
        payload["observation_age_seconds"],
        f"{path}.observation_age_seconds",
    )
    reason_codes = _public_row_reason_codes(
        payload["reason_codes"],
        f"{path}.reason_codes",
    )
    workload_status = _public_status(
        "workload_status",
        payload["workload_status"],
        f"{path}.workload_status",
    )
    if observed_at > generated_at:
        raise ValueError(f"{path}.observed_at must not be in the future")
    if observation_age_seconds != _datetime_delta_seconds(generated_at, observed_at):
        raise ValueError(
            f"{path}.observation_age_seconds must match generated_at and observed_at",
        )
    if workload_status != _row_status(reason_codes):
        raise ValueError(f"{path}.workload_status must match reason_codes")
    return _PublicPayloadRow(
        team_key=_public_team_key("team_key", payload["team_key"], f"{path}.team_key"),
        team_domain=_public_team_key(
            "team_domain",
            payload["team_domain"],
            f"{path}.team_domain",
        ),
        workload_status=workload_status,
        generated_at=generated_at,
        observed_at=observed_at,
        observation_age_seconds=observation_age_seconds,
        pending_packet_count=_public_count_decimal(
            "pending_packet_count",
            payload["pending_packet_count"],
            f"{path}.pending_packet_count",
        ),
        reviewer_available_count=_public_count_decimal(
            "reviewer_available_count",
            payload["reviewer_available_count"],
            f"{path}.reviewer_available_count",
        ),
        oldest_sla_age_hours=_public_nonnegative_decimal(
            "oldest_sla_age_hours",
            payload["oldest_sla_age_hours"],
            f"{path}.oldest_sla_age_hours",
        ),
        unresolved_escalation_count=_public_count_decimal(
            "unresolved_escalation_count",
            payload["unresolved_escalation_count"],
            f"{path}.unresolved_escalation_count",
        ),
        memory_writeback_delay_hours=_public_nonnegative_decimal(
            "memory_writeback_delay_hours",
            payload["memory_writeback_delay_hours"],
            f"{path}.memory_writeback_delay_hours",
        ),
        reason_codes=reason_codes,
        paper_only=_public_true_flag(payload["paper_only"], f"{path}.paper_only"),
        report_only=_public_true_flag(payload["report_only"], f"{path}.report_only"),
        readonly=_public_true_flag(payload["readonly"], f"{path}.readonly"),
    )


def _require_public_rows(rows: tuple[_PublicPayloadRow, ...], path: str) -> None:
    seen: set[str] = set()
    for row in rows:
        if row.team_key in seen:
            raise ValueError(f"{path} must contain unique team_key values")
        seen.add(row.team_key)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError(f"{path} must be sorted by status and team_key")


def _public_payload_reason_code_counts(
    value: object,
    path: str,
) -> tuple[ResearchTeamSpecialistWorkloadPressureReasonCodeCount, ...]:
    if type(value) is not list:
        raise ValueError(f"{path} must be a list")
    return _require_reason_code_counts(
        tuple(
            _public_payload_reason_code_count(item, f"{path}[{index}]")
            for index, item in enumerate(value)
        ),
    )


def _public_payload_reason_code_count(
    value: object,
    path: str,
) -> ResearchTeamSpecialistWorkloadPressureReasonCodeCount:
    payload = _require_public_payload_object(
        value,
        path,
        _public_payload_keys(ResearchTeamSpecialistWorkloadPressureReasonCodeCount),
    )
    return ResearchTeamSpecialistWorkloadPressureReasonCodeCount(
        reason_code=_public_string(
            "reason_code",
            payload["reason_code"],
            f"{path}.reason_code",
        ),
        count=_public_count_decimal("count", payload["count"], f"{path}.count"),
        team_ratio=_public_ratio_decimal(
            "team_ratio",
            payload["team_ratio"],
            f"{path}.team_ratio",
        ),
        paper_only=_public_true_flag(payload["paper_only"], f"{path}.paper_only"),
        report_only=_public_true_flag(payload["report_only"], f"{path}.report_only"),
        readonly=_public_true_flag(payload["readonly"], f"{path}.readonly"),
    )


def _public_string(field_name: str, value: object, path: str) -> str:
    try:
        _require_public_string(field_name, value)
    except ValueError as exc:
        raise ValueError(f"{path} must be a canonical public string") from exc
    return value


def _public_config_version(field_name: str, value: object, path: str) -> str:
    config_version = _public_string(field_name, value, path)
    if (
        config_version
        != DEFAULT_RESEARCH_TEAM_SPECIALIST_WORKLOAD_PRESSURE_REPORT_CONFIG_VERSION
    ):
        raise ValueError(f"{path} must be the supported config_version")
    return config_version


def _public_team_key(field_name: str, value: object, path: str) -> str:
    try:
        _require_safe_team_key(field_name, value)
    except ValueError as exc:
        raise ValueError(f"{path} must be lowercase snake case") from exc
    return value


def _public_status(field_name: str, value: object, path: str) -> str:
    try:
        _require_status(field_name, value)
    except ValueError as exc:
        raise ValueError(f"{path} must be one of pass, watch, block") from exc
    return value


def _public_datetime(field_name: str, value: object, path: str) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{path} must be a canonical UTC datetime string")
    _public_string(field_name, value, path)
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{path} must be a canonical UTC datetime string") from exc
    normalized = _as_utc(field_name, parsed)
    if value != normalized.isoformat():
        raise ValueError(f"{path} must be a canonical UTC datetime string")
    return normalized


def _public_decimal(field_name: str, value: object, path: str) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{path} must be a Decimal-derived string")
    _public_string(field_name, value, path)
    try:
        return Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{path} must be a Decimal-derived string") from exc


def _public_count_decimal(field_name: str, value: object, path: str) -> Decimal:
    normalized = _require_count_decimal(
        field_name,
        _public_decimal(field_name, value, path),
    )
    if value != str(normalized):
        raise ValueError(f"{path} must be a canonical Decimal-derived string")
    return normalized


def _public_nonnegative_decimal(field_name: str, value: object, path: str) -> Decimal:
    normalized = _require_nonnegative_decimal(
        field_name,
        _public_decimal(field_name, value, path),
    )
    if value != str(normalized):
        raise ValueError(f"{path} must be a canonical Decimal-derived string")
    return normalized


def _public_ratio_decimal(field_name: str, value: object, path: str) -> Decimal:
    normalized = _require_ratio_decimal(
        field_name,
        _public_decimal(field_name, value, path),
    )
    if value != str(normalized):
        raise ValueError(f"{path} must be a canonical Decimal-derived string")
    return normalized


def _public_row_reason_codes(value: object, path: str) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{path} must be a list")
    try:
        return _require_reason_codes(tuple(value))
    except ValueError as exc:
        raise ValueError(f"{path} contains invalid reason_code") from exc


def _public_report_reason_codes(value: object, path: str) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{path} must be a list")
    try:
        return _require_report_reason_codes(tuple(value))
    except ValueError as exc:
        raise ValueError(f"{path} contains invalid reason_code") from exc


def _public_sha256(field_name: str, value: object, path: str) -> str:
    try:
        _require_sha256(field_name, value)
    except ValueError as exc:
        raise ValueError(f"{path} must be a sha256 hex digest") from exc
    return value


def _public_true_flag(value: object, path: str) -> bool:
    if value is not True:
        raise ValueError(f"{path} must be True")
    return True


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_payload(field.name, getattr(value, field.name))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} contains unsafe public key")
            _reject_unsafe_public_text("public key", key)
            _reject_unsafe_public_payload(key, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public text")


__all__ = (
    "DEFAULT_RESEARCH_TEAM_SPECIALIST_WORKLOAD_PRESSURE_REPORT_CONFIG_VERSION",
    "STATUSES",
    "ResearchTeamSpecialistWorkloadPressureConfig",
    "ResearchTeamSpecialistWorkloadPressureInput",
    "ResearchTeamSpecialistWorkloadPressureReasonCodeCount",
    "ResearchTeamSpecialistWorkloadPressureReport",
    "ResearchTeamSpecialistWorkloadPressureRow",
    "build_research_team_specialist_workload_pressure_report",
    "research_team_specialist_workload_pressure_report_payload",
)
