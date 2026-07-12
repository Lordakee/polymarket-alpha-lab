"""Read-only Phase 1 specialist team research backlog WIP limit report."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN
from hashlib import sha256
import json
from typing import Any


REPORT_NAME = "specialist_team_research_backlog_wip_limit_report"
PHASE = "phase_1"

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
HOURS_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")

MAX_PASS_BACKLOG_TO_CAPACITY_RATIO = Decimal("1.000000")
MAX_WATCH_BACKLOG_TO_CAPACITY_RATIO = Decimal("1.500000")
MAX_PASS_BACKLOG_PER_ACTIVE_AGENT = Decimal("3.000000")
MAX_WATCH_BACKLOG_PER_ACTIVE_AGENT = Decimal("5.000000")
MAX_PASS_OLDEST_ITEM_AGE_HOURS = Decimal("12.000000")
MAX_WATCH_OLDEST_ITEM_AGE_HOURS = Decimal("24.000000")

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

PASS_REASON = "specialist_team_research_wip_clear"
BACKLOG_CAPACITY_WATCH_REASON = (
    "specialist_team_research_backlog_above_capacity_watch"
)
BACKLOG_CAPACITY_BLOCK_REASON = (
    "specialist_team_research_backlog_above_capacity_block"
)
AGENT_WIP_WATCH_REASON = "specialist_team_research_agent_wip_limit_watch"
AGENT_WIP_BLOCK_REASON = "specialist_team_research_agent_wip_limit_block"
BLOCKED_ITEM_REASON = "specialist_team_research_blocked_items_present"
OLDEST_ITEM_WATCH_REASON = "specialist_team_research_oldest_item_stale_watch"
OLDEST_ITEM_BLOCK_REASON = "specialist_team_research_oldest_item_stale_block"

REASON_CODE_ORDER = (
    BACKLOG_CAPACITY_BLOCK_REASON,
    AGENT_WIP_BLOCK_REASON,
    BLOCKED_ITEM_REASON,
    OLDEST_ITEM_BLOCK_REASON,
    BACKLOG_CAPACITY_WATCH_REASON,
    AGENT_WIP_WATCH_REASON,
    OLDEST_ITEM_WATCH_REASON,
    PASS_REASON,
)

NEXT_STEP_BY_STATUS = {
    STATUS_PASS: "continue_manual_research_triage",
    STATUS_WATCH: "review_team_research_backlog_before_new_intake",
    STATUS_BLOCK: "pause_new_research_intake_and_rebalance_team_queue",
}

PUBLIC_PAYLOAD_KEYS = frozenset(
    (
        "report_name",
        "phase",
        "wip_status",
        "reason_codes",
        "manual_next_step",
        "open_research_item_count",
        "active_agent_count",
        "team_capacity_count",
        "blocked_item_count",
        "oldest_item_age_hours",
        "backlog_to_capacity_ratio",
        "backlog_per_active_agent",
        "paper_only",
        "report_only",
        "readonly",
        "payload_digest",
    ),
)


@dataclass(frozen=True)
class SpecialistTeamResearchBacklogWipLimitReport:
    open_research_item_count: Decimal
    active_agent_count: Decimal
    team_capacity_count: Decimal
    blocked_item_count: Decimal
    oldest_item_age_hours: Decimal
    backlog_to_capacity_ratio: Decimal
    backlog_per_active_agent: Decimal
    wip_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    public_payload: dict[str, object]
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not SpecialistTeamResearchBacklogWipLimitReport:
            raise TypeError(
                "SpecialistTeamResearchBacklogWipLimitReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not SpecialistTeamResearchBacklogWipLimitReport:
            raise ValueError(
                "report must be exactly SpecialistTeamResearchBacklogWipLimitReport",
            )
        for field_name in (
            "open_research_item_count",
            "active_agent_count",
            "team_capacity_count",
            "blocked_item_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "oldest_item_age_hours",
            _require_hours_decimal("oldest_item_age_hours", self.oldest_item_age_hours),
        )
        for field_name in ("backlog_to_capacity_ratio", "backlog_per_active_agent"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("wip_status", self.wip_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        if self.manual_next_step != NEXT_STEP_BY_STATUS[self.wip_status]:
            raise ValueError("manual_next_step must match wip_status")
        _require_hard_flags("report", self)
        _require_payload_digest("payload_digest", self.payload_digest)
        _validate_report_consistency(self)
        expected_payload = _public_payload_for_report(self, include_digest=False)
        expected_digest = payload_digest_for_public_payload(expected_payload)
        if self.payload_digest != expected_digest:
            raise ValueError("payload_digest must match public_payload")
        expected_payload["payload_digest"] = expected_digest
        if self.public_payload != expected_payload:
            raise ValueError("public_payload must match report fields")


def build_specialist_team_research_backlog_wip_limit_report(
    *,
    open_research_item_count: Decimal,
    active_agent_count: Decimal,
    team_capacity_count: Decimal,
    blocked_item_count: Decimal,
    oldest_item_age_hours: Decimal,
) -> SpecialistTeamResearchBacklogWipLimitReport:
    open_count = _require_whole_decimal(
        "open_research_item_count",
        open_research_item_count,
    )
    active_count = _require_whole_decimal("active_agent_count", active_agent_count)
    capacity_count = _require_whole_decimal("team_capacity_count", team_capacity_count)
    blocked_count = _require_whole_decimal("blocked_item_count", blocked_item_count)
    oldest_hours = _require_hours_decimal(
        "oldest_item_age_hours",
        oldest_item_age_hours,
    )
    backlog_to_capacity = _ratio(open_count, capacity_count)
    backlog_per_agent = _ratio(open_count, active_count)
    reason_codes = _reason_codes(
        open_research_item_count=open_count,
        active_agent_count=active_count,
        team_capacity_count=capacity_count,
        blocked_item_count=blocked_count,
        oldest_item_age_hours=oldest_hours,
        backlog_to_capacity_ratio=backlog_to_capacity,
        backlog_per_active_agent=backlog_per_agent,
    )
    status = _status(reason_codes)
    values = {
        "open_research_item_count": open_count,
        "active_agent_count": active_count,
        "team_capacity_count": capacity_count,
        "blocked_item_count": blocked_count,
        "oldest_item_age_hours": oldest_hours,
        "backlog_to_capacity_ratio": backlog_to_capacity,
        "backlog_per_active_agent": backlog_per_agent,
        "wip_status": status,
        "reason_codes": reason_codes,
        "manual_next_step": NEXT_STEP_BY_STATUS[status],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    public_payload = _public_payload_from_values(values, include_digest=False)
    digest = payload_digest_for_public_payload(public_payload)
    public_payload["payload_digest"] = digest
    return SpecialistTeamResearchBacklogWipLimitReport(
        **values,
        public_payload=public_payload,
        payload_digest=digest,
    )


def validate_specialist_team_research_backlog_wip_limit_public_payload(
    payload: object,
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    _require_public_payload_schema(payload)
    expected_digest = payload_digest_for_public_payload(payload)
    if payload["payload_digest"] != expected_digest:
        raise ValueError("payload_digest must match public payload")


def payload_digest_for_public_payload(payload: dict[str, object]) -> str:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    unsigned = dict(payload)
    unsigned["payload_digest"] = ""
    encoded = json.dumps(
        _sort_json(unsigned),
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _reason_codes(
    *,
    open_research_item_count: Decimal,
    active_agent_count: Decimal,
    team_capacity_count: Decimal,
    blocked_item_count: Decimal,
    oldest_item_age_hours: Decimal,
    backlog_to_capacity_ratio: Decimal,
    backlog_per_active_agent: Decimal,
) -> tuple[str, ...]:
    del open_research_item_count, active_agent_count, team_capacity_count
    reasons: list[str] = []
    if backlog_to_capacity_ratio > MAX_WATCH_BACKLOG_TO_CAPACITY_RATIO:
        reasons.append(BACKLOG_CAPACITY_BLOCK_REASON)
    elif backlog_to_capacity_ratio > MAX_PASS_BACKLOG_TO_CAPACITY_RATIO:
        reasons.append(BACKLOG_CAPACITY_WATCH_REASON)

    if backlog_per_active_agent > MAX_WATCH_BACKLOG_PER_ACTIVE_AGENT:
        reasons.append(AGENT_WIP_BLOCK_REASON)
    elif backlog_per_active_agent > MAX_PASS_BACKLOG_PER_ACTIVE_AGENT:
        reasons.append(AGENT_WIP_WATCH_REASON)

    if blocked_item_count > ZERO:
        reasons.append(BLOCKED_ITEM_REASON)

    if oldest_item_age_hours > MAX_WATCH_OLDEST_ITEM_AGE_HOURS:
        reasons.append(OLDEST_ITEM_BLOCK_REASON)
    elif oldest_item_age_hours > MAX_PASS_OLDEST_ITEM_AGE_HOURS:
        reasons.append(OLDEST_ITEM_WATCH_REASON)

    return _normalize_reason_codes(tuple(reasons) or (PASS_REASON,))


def _status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") or reason == BLOCKED_ITEM_REASON for reason in reason_codes):
        return STATUS_BLOCK
    if any(reason.endswith("_watch") for reason in reason_codes):
        return STATUS_WATCH
    return STATUS_PASS


def _validate_report_consistency(
    report: SpecialistTeamResearchBacklogWipLimitReport,
) -> None:
    expected_reasons = _reason_codes(
        open_research_item_count=report.open_research_item_count,
        active_agent_count=report.active_agent_count,
        team_capacity_count=report.team_capacity_count,
        blocked_item_count=report.blocked_item_count,
        oldest_item_age_hours=report.oldest_item_age_hours,
        backlog_to_capacity_ratio=report.backlog_to_capacity_ratio,
        backlog_per_active_agent=report.backlog_per_active_agent,
    )
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match WIP inputs")
    if report.wip_status != _status(expected_reasons):
        raise ValueError("wip_status must match reason_codes")
    if report.backlog_to_capacity_ratio != _ratio(
        report.open_research_item_count,
        report.team_capacity_count,
    ):
        raise ValueError("backlog_to_capacity_ratio must match inputs")
    if report.backlog_per_active_agent != _ratio(
        report.open_research_item_count,
        report.active_agent_count,
    ):
        raise ValueError("backlog_per_active_agent must match inputs")


def _public_payload_for_report(
    report: SpecialistTeamResearchBacklogWipLimitReport,
    *,
    include_digest: bool,
) -> dict[str, object]:
    return _public_payload_from_values(
        {
            "open_research_item_count": report.open_research_item_count,
            "active_agent_count": report.active_agent_count,
            "team_capacity_count": report.team_capacity_count,
            "blocked_item_count": report.blocked_item_count,
            "oldest_item_age_hours": report.oldest_item_age_hours,
            "backlog_to_capacity_ratio": report.backlog_to_capacity_ratio,
            "backlog_per_active_agent": report.backlog_per_active_agent,
            "wip_status": report.wip_status,
            "reason_codes": report.reason_codes,
            "manual_next_step": report.manual_next_step,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
            "payload_digest": report.payload_digest,
        },
        include_digest=include_digest,
    )


def _public_payload_from_values(
    values: dict[str, object],
    *,
    include_digest: bool,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "report_name": REPORT_NAME,
        "phase": PHASE,
        "wip_status": values["wip_status"],
        "reason_codes": list(values["reason_codes"]),
        "manual_next_step": values["manual_next_step"],
        "open_research_item_count": _format_count(values["open_research_item_count"]),
        "active_agent_count": _format_count(values["active_agent_count"]),
        "team_capacity_count": _format_count(values["team_capacity_count"]),
        "blocked_item_count": _format_count(values["blocked_item_count"]),
        "oldest_item_age_hours": _format_fixed(
            values["oldest_item_age_hours"],
            HOURS_QUANTUM,
        ),
        "backlog_to_capacity_ratio": _format_fixed(
            values["backlog_to_capacity_ratio"],
            RATIO_QUANTUM,
        ),
        "backlog_per_active_agent": _format_fixed(
            values["backlog_per_active_agent"],
            RATIO_QUANTUM,
        ),
        "paper_only": values["paper_only"],
        "report_only": values["report_only"],
        "readonly": values["readonly"],
        "payload_digest": values.get("payload_digest", "") if include_digest else "",
    }
    _require_public_payload_schema(payload)
    return payload


def _require_public_payload_schema(payload: dict[str, object]) -> None:
    if frozenset(payload) != PUBLIC_PAYLOAD_KEYS:
        raise ValueError("public payload keys must match schema")
    if payload["report_name"] != REPORT_NAME:
        raise ValueError("report_name must match")
    if payload["phase"] != PHASE:
        raise ValueError("phase must match")
    _require_status("wip_status", payload["wip_status"])
    if type(payload["manual_next_step"]) is not str or not payload["manual_next_step"]:
        raise ValueError("manual_next_step must be a nonempty string")
    if payload["manual_next_step"] != NEXT_STEP_BY_STATUS[payload["wip_status"]]:
        raise ValueError("manual_next_step must match wip_status")
    if type(payload["reason_codes"]) is not list:
        raise ValueError("reason_codes must be a list")
    _normalize_reason_codes(tuple(payload["reason_codes"]))
    for field_name in (
        "open_research_item_count",
        "active_agent_count",
        "team_capacity_count",
        "blocked_item_count",
        "oldest_item_age_hours",
        "backlog_to_capacity_ratio",
        "backlog_per_active_agent",
    ):
        if type(payload[field_name]) is not str:
            raise ValueError(f"{field_name} must be a public decimal string")
    for flag_name in ("paper_only", "report_only", "readonly"):
        if payload[flag_name] is not True:
            raise ValueError(f"{flag_name} must be True")
    _require_payload_digest("payload_digest", payload["payload_digest"], allow_empty=True)


def _require_whole_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.quantize(COUNT_QUANTUM):
        raise ValueError(f"{field_name} must be a whole Decimal")
    return value.quantize(COUNT_QUANTUM)


def _require_hours_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value.quantize(HOURS_QUANTUM, rounding=ROUND_HALF_EVEN)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value.quantize(RATIO_QUANTUM, rounding=ROUND_HALF_EVEN)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if numerator == ZERO:
        return Decimal("0.000000")
    if denominator == ZERO:
        return numerator.quantize(RATIO_QUANTUM, rounding=ROUND_HALF_EVEN)
    return (numerator / denominator).quantize(RATIO_QUANTUM, rounding=ROUND_HALF_EVEN)


def _normalize_reason_codes(reason_codes: tuple[object, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple or not reason_codes:
        raise ValueError("reason_codes must be a nonempty tuple")
    allowed = frozenset(REASON_CODE_ORDER)
    normalized: list[str] = []
    for reason in reason_codes:
        if type(reason) is not str or reason not in allowed:
            raise ValueError("reason_codes must be canonical WIP reason codes")
        if reason not in normalized:
            normalized.append(reason)
    return tuple(
        reason for reason in REASON_CODE_ORDER if reason in frozenset(normalized)
    )


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _require_payload_digest(
    field_name: str,
    value: object,
    *,
    allow_empty: bool = False,
) -> None:
    if allow_empty and value == "":
        return
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _format_count(value: object) -> str:
    if type(value) is not Decimal:
        raise ValueError("count value must be Decimal")
    return format(value.quantize(COUNT_QUANTUM), "f")


def _format_fixed(value: object, quantum: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("fixed value must be Decimal")
    return format(value.quantize(quantum, rounding=ROUND_HALF_EVEN), "f")


def _sort_json(value: object) -> object:
    if isinstance(value, dict):
        return {key: _sort_json(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_sort_json(item) for item in value]
    return value


__all__ = [
    "SpecialistTeamResearchBacklogWipLimitReport",
    "build_specialist_team_research_backlog_wip_limit_report",
    "payload_digest_for_public_payload",
    "validate_specialist_team_research_backlog_wip_limit_public_payload",
]
