"""Manual decision SLA breach readiness report."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from typing import Any


DEFAULT_MANUAL_DECISION_SLA_BREACH_READINESS_CONFIG_VERSION = (
    "manual-decision-sla-breach-readiness-v0"
)

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_QUANTUM = Decimal("0.000001")

SLA_STATUS_VALUES = ("pass", "watch", "breached")
BREACH_RISK_VALUES = ("low", "elevated", "critical")

PAYLOAD_FIELDS = (
    "config_version",
    "sla_status",
    "breach_risk",
    "decision_count",
    "pass_decision_count",
    "watch_decision_count",
    "breached_decision_count",
    "operator_missing_decision_count",
    "source_refresh_due_decision_count",
    "blocking_reason_decision_count",
    "urgent_close_decision_count",
    "pass_decision_ratio",
    "reason_codes",
    "rows",
    "paper_only",
    "report_only",
    "readonly",
    "derived_validation_digest",
)
ROW_PAYLOAD_FIELDS = (
    "decision_id",
    "queued_age_hours",
    "market_close_hours",
    "source_refresh_due",
    "operator_owner_present",
    "blocking_reason_count",
    "sla_status",
    "breach_risk",
    "reason_codes",
    "manual_next_step",
    "paper_only",
    "report_only",
    "readonly",
)
DECIMAL_PAYLOAD_FIELDS = (
    "decision_count",
    "pass_decision_count",
    "watch_decision_count",
    "breached_decision_count",
    "operator_missing_decision_count",
    "source_refresh_due_decision_count",
    "blocking_reason_decision_count",
    "urgent_close_decision_count",
    "pass_decision_ratio",
)
ROW_DECIMAL_PAYLOAD_FIELDS = (
    "queued_age_hours",
    "market_close_hours",
    "blocking_reason_count",
)

READY_REASON = "manual_decision_sla_ready"
NO_ITEMS_REASON = "no_manual_decision_sla_items"
SLA_BREACHED_REASON = "manual_decision_sla_breached"
QUEUE_WATCH_REASON = "manual_decision_queue_age_watch"
SOURCE_REFRESH_DUE_REASON = "source_refresh_due_before_manual_decision"
OWNER_MISSING_REASON = "operator_owner_missing"
BLOCKING_REASON = "manual_decision_blocking_reasons_present"
URGENT_CLOSE_REASON = "market_close_manual_decision_urgent"

SUMMARY_REASON_PRIORITY = (
    SLA_BREACHED_REASON,
    OWNER_MISSING_REASON,
    BLOCKING_REASON,
    SOURCE_REFRESH_DUE_REASON,
    QUEUE_WATCH_REASON,
)

PASS_NEXT_STEP = "allow_report_only_manual_decision_review"
QUEUE_NEXT_STEP = "watch_report_only_manual_decision_queue"
SOURCE_NEXT_STEP = "watch_report_only_refresh_sources"
OWNER_NEXT_STEP = "watch_report_only_assign_operator_owner"
BLOCKING_NEXT_STEP = "breach_report_only_clear_blocking_reasons"
BREACHED_NEXT_STEP = "breach_report_only_manual_decision_sla_review"

__all__ = (
    "DEFAULT_MANUAL_DECISION_SLA_BREACH_READINESS_CONFIG_VERSION",
    "ManualDecisionSlaBreachReadinessConfig",
    "ManualDecisionSlaBreachReadinessItem",
    "ManualDecisionSlaBreachReadinessReport",
    "ManualDecisionSlaBreachReadinessRow",
    "build_manual_decision_sla_breach_readiness_report",
    "manual_decision_sla_breach_readiness_report_payload",
)


class ManualDecisionSlaBreachReadinessPublicPayload(dict[str, object]):
    """Immutable public payload for manual decision SLA readiness."""

    def __readonly(self, *args: object, **kwargs: object) -> None:
        raise TypeError("public_payload is immutable")

    __setitem__ = __readonly
    __delitem__ = __readonly
    clear = __readonly
    pop = __readonly
    popitem = __readonly
    setdefault = __readonly
    update = __readonly


@dataclass(frozen=True)
class ManualDecisionSlaBreachReadinessConfig:
    config_version: str = DEFAULT_MANUAL_DECISION_SLA_BREACH_READINESS_CONFIG_VERSION
    queued_watch_after_hours: Decimal = Decimal("4.000000")
    queued_breach_after_hours: Decimal = Decimal("8.000000")
    market_close_urgent_hours: Decimal = Decimal("6.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ManualDecisionSlaBreachReadinessConfig:
            raise TypeError(
                "ManualDecisionSlaBreachReadinessConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ManualDecisionSlaBreachReadinessConfig:
            raise ValueError(
                "config must be exactly ManualDecisionSlaBreachReadinessConfig",
            )
        object.__setattr__(
            self,
            "config_version",
            _require_public_label("config_version", self.config_version),
        )
        object.__setattr__(
            self,
            "queued_watch_after_hours",
            _require_decimal("queued_watch_after_hours", self.queued_watch_after_hours),
        )
        object.__setattr__(
            self,
            "queued_breach_after_hours",
            _require_decimal("queued_breach_after_hours", self.queued_breach_after_hours),
        )
        object.__setattr__(
            self,
            "market_close_urgent_hours",
            _require_decimal("market_close_urgent_hours", self.market_close_urgent_hours),
        )
        if self.queued_watch_after_hours >= self.queued_breach_after_hours:
            raise ValueError("queued_watch_after_hours must be below breach hours")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ManualDecisionSlaBreachReadinessItem:
    decision_id: str
    queued_age_hours: Decimal
    market_close_hours: Decimal
    source_refresh_due: bool
    operator_owner_present: bool
    blocking_reason_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ManualDecisionSlaBreachReadinessItem:
            raise TypeError(
                "ManualDecisionSlaBreachReadinessItem does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ManualDecisionSlaBreachReadinessItem:
            raise ValueError("item must be exactly ManualDecisionSlaBreachReadinessItem")
        object.__setattr__(
            self,
            "decision_id",
            _require_public_label("decision_id", self.decision_id),
        )
        object.__setattr__(
            self,
            "queued_age_hours",
            _require_decimal("queued_age_hours", self.queued_age_hours),
        )
        object.__setattr__(
            self,
            "market_close_hours",
            _require_decimal("market_close_hours", self.market_close_hours),
        )
        _require_bool("source_refresh_due", self.source_refresh_due)
        _require_bool("operator_owner_present", self.operator_owner_present)
        object.__setattr__(
            self,
            "blocking_reason_count",
            _require_count_decimal("blocking_reason_count", self.blocking_reason_count),
        )
        _require_hard_flags("item", self)


@dataclass(frozen=True)
class ManualDecisionSlaBreachReadinessRow:
    decision_id: str
    queued_age_hours: Decimal
    market_close_hours: Decimal
    source_refresh_due: bool
    operator_owner_present: bool
    blocking_reason_count: Decimal
    sla_status: str
    breach_risk: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ManualDecisionSlaBreachReadinessRow:
            raise TypeError(
                "ManualDecisionSlaBreachReadinessRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ManualDecisionSlaBreachReadinessRow:
            raise ValueError("row must be exactly ManualDecisionSlaBreachReadinessRow")
        object.__setattr__(
            self,
            "decision_id",
            _require_public_label("decision_id", self.decision_id),
        )
        object.__setattr__(
            self,
            "queued_age_hours",
            _require_decimal("queued_age_hours", self.queued_age_hours),
        )
        object.__setattr__(
            self,
            "market_close_hours",
            _require_decimal("market_close_hours", self.market_close_hours),
        )
        _require_bool("source_refresh_due", self.source_refresh_due)
        _require_bool("operator_owner_present", self.operator_owner_present)
        object.__setattr__(
            self,
            "blocking_reason_count",
            _require_count_decimal("blocking_reason_count", self.blocking_reason_count),
        )
        _require_member("sla_status", self.sla_status, SLA_STATUS_VALUES)
        _require_member("breach_risk", self.breach_risk, BREACH_RISK_VALUES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "manual_next_step",
            _require_manual_next_step(self.manual_next_step),
        )
        _require_hard_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ManualDecisionSlaBreachReadinessReport:
    config_version: str
    sla_status: str
    breach_risk: str
    decision_count: Decimal
    pass_decision_count: Decimal
    watch_decision_count: Decimal
    breached_decision_count: Decimal
    operator_missing_decision_count: Decimal
    source_refresh_due_decision_count: Decimal
    blocking_reason_decision_count: Decimal
    urgent_close_decision_count: Decimal
    pass_decision_ratio: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[ManualDecisionSlaBreachReadinessRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ManualDecisionSlaBreachReadinessReport:
            raise TypeError(
                "ManualDecisionSlaBreachReadinessReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ManualDecisionSlaBreachReadinessReport:
            raise ValueError(
                "report must be exactly ManualDecisionSlaBreachReadinessReport",
            )
        object.__setattr__(
            self,
            "config_version",
            _require_public_label("config_version", self.config_version),
        )
        _require_member("sla_status", self.sla_status, SLA_STATUS_VALUES)
        _require_member("breach_risk", self.breach_risk, BREACH_RISK_VALUES)
        for field_name in DECIMAL_PAYLOAD_FIELDS:
            value = getattr(self, field_name)
            if field_name == "pass_decision_ratio":
                object.__setattr__(self, field_name, _require_ratio(field_name, value))
            else:
                object.__setattr__(self, field_name, _require_count_decimal(field_name, value))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report(self)
        if self.derived_validation_digest != _payload_digest(
            _payload_items(self, digest=""),
        ):
            raise ValueError("derived_validation_digest must match public payload")

    @property
    def public_payload(self) -> ManualDecisionSlaBreachReadinessPublicPayload:
        payload = ManualDecisionSlaBreachReadinessPublicPayload(
            _payload_items(self, digest=self.derived_validation_digest),
        )
        _validate_public_payload(payload)
        return payload


def build_manual_decision_sla_breach_readiness_report(
    items: Iterable[ManualDecisionSlaBreachReadinessItem],
    *,
    config: ManualDecisionSlaBreachReadinessConfig,
) -> ManualDecisionSlaBreachReadinessReport:
    if type(config) is not ManualDecisionSlaBreachReadinessConfig:
        raise ValueError("config must be a ManualDecisionSlaBreachReadinessConfig")
    _require_hard_flags("config", config)
    normalized = _normalize_items(items)
    rows = tuple(
        _row_for_item(item, config=config)
        for item in sorted(normalized, key=lambda item: item.decision_id)
    )
    values: dict[str, object] = {
        "config_version": config.config_version,
        "sla_status": _summary_status(rows),
        "breach_risk": _summary_risk(rows),
        "decision_count": _count(len(rows)),
        "pass_decision_count": _status_count(rows, "pass"),
        "watch_decision_count": _status_count(rows, "watch"),
        "breached_decision_count": _status_count(rows, "breached"),
        "operator_missing_decision_count": _operator_missing_count(rows),
        "source_refresh_due_decision_count": _source_refresh_due_count(rows),
        "blocking_reason_decision_count": _blocking_reason_count(rows),
        "urgent_close_decision_count": _urgent_close_count(rows, config=config),
        "pass_decision_ratio": _ratio(_status_count(rows, "pass"), _count(len(rows))),
        "reason_codes": _summary_reason_codes(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ManualDecisionSlaBreachReadinessReport(
        **values,
        derived_validation_digest=_payload_digest(_payload_values(values, digest="")),
    )


def manual_decision_sla_breach_readiness_report_payload(
    report: ManualDecisionSlaBreachReadinessReport | Mapping[str, object],
) -> ManualDecisionSlaBreachReadinessPublicPayload:
    if type(report) is ManualDecisionSlaBreachReadinessReport:
        _require_hard_flags("report", report)
        _validate_report(report)
        if report.derived_validation_digest != _payload_digest(
            _payload_items(report, digest=""),
        ):
            raise ValueError("derived_validation_digest must match report payload")
        return report.public_payload
    if isinstance(report, Mapping):
        _validate_public_payload(report)
        return ManualDecisionSlaBreachReadinessPublicPayload(dict(report))
    raise ValueError(
        "report must be a ManualDecisionSlaBreachReadinessReport or public payload",
    )


def _row_for_item(
    item: ManualDecisionSlaBreachReadinessItem,
    *,
    config: ManualDecisionSlaBreachReadinessConfig,
) -> ManualDecisionSlaBreachReadinessRow:
    reasons: list[str] = []
    if item.blocking_reason_count > ZERO:
        reasons.append(BLOCKING_REASON)
    elif item.queued_age_hours >= config.queued_breach_after_hours:
        reasons.append(SLA_BREACHED_REASON)
        if item.market_close_hours <= config.market_close_urgent_hours:
            reasons.append(URGENT_CLOSE_REASON)
    elif not item.operator_owner_present:
        reasons.append(OWNER_MISSING_REASON)
    elif item.source_refresh_due:
        reasons.append(SOURCE_REFRESH_DUE_REASON)
    elif item.queued_age_hours > config.queued_watch_after_hours:
        reasons.append(QUEUE_WATCH_REASON)
    elif item.market_close_hours <= config.market_close_urgent_hours:
        reasons.append(URGENT_CLOSE_REASON)
    else:
        reasons.append(READY_REASON)
    status = _row_status(tuple(reasons))
    return ManualDecisionSlaBreachReadinessRow(
        decision_id=item.decision_id,
        queued_age_hours=item.queued_age_hours,
        market_close_hours=item.market_close_hours,
        source_refresh_due=item.source_refresh_due,
        operator_owner_present=item.operator_owner_present,
        blocking_reason_count=item.blocking_reason_count,
        sla_status=status,
        breach_risk=_risk_for_status(status),
        reason_codes=tuple(reasons),
        manual_next_step=_next_step_for_reasons(tuple(reasons), status=status),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if SLA_BREACHED_REASON in reason_codes or BLOCKING_REASON in reason_codes:
        return "breached"
    if reason_codes == (READY_REASON,):
        return "pass"
    return "watch"


def _risk_for_status(status: str) -> str:
    if status == "breached":
        return "critical"
    if status == "watch":
        return "elevated"
    return "low"


def _next_step_for_reasons(reason_codes: tuple[str, ...], *, status: str) -> str:
    if status == "pass":
        return PASS_NEXT_STEP
    if BLOCKING_REASON in reason_codes:
        return BLOCKING_NEXT_STEP
    if status == "breached":
        return BREACHED_NEXT_STEP
    if OWNER_MISSING_REASON in reason_codes:
        return OWNER_NEXT_STEP
    if SOURCE_REFRESH_DUE_REASON in reason_codes:
        return SOURCE_NEXT_STEP
    return QUEUE_NEXT_STEP


def _summary_status(
    rows: tuple[ManualDecisionSlaBreachReadinessRow, ...],
) -> str:
    if not rows:
        return "breached"
    if any(row.sla_status == "breached" for row in rows):
        return "breached"
    if any(row.sla_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _summary_risk(
    rows: tuple[ManualDecisionSlaBreachReadinessRow, ...],
) -> str:
    return _risk_for_status(_summary_status(rows))


def _summary_reason_codes(
    rows: tuple[ManualDecisionSlaBreachReadinessRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_ITEMS_REASON,)
    seen = {reason for row in rows for reason in row.reason_codes}
    selected = tuple(reason for reason in SUMMARY_REASON_PRIORITY if reason in seen)
    if selected:
        return selected
    return (READY_REASON,)


def _validate_row(row: ManualDecisionSlaBreachReadinessRow) -> None:
    if row.breach_risk != _risk_for_status(row.sla_status):
        raise ValueError("breach_risk must match sla_status")
    if row.sla_status != _row_status(row.reason_codes):
        raise ValueError("sla_status must match reason_codes")
    if row.manual_next_step != _next_step_for_reasons(
        row.reason_codes,
        status=row.sla_status,
    ):
        raise ValueError("manual_next_step must match reason_codes")
    if row.sla_status == "pass" and row.reason_codes != (READY_REASON,):
        raise ValueError("reason_codes must match pass status")


def _validate_report(report: ManualDecisionSlaBreachReadinessReport) -> None:
    rows = report.rows
    if tuple(row.decision_id for row in rows) != tuple(
        sorted(row.decision_id for row in rows),
    ):
        raise ValueError("rows must be deterministic by decision_id")
    if report.decision_count != _count(len(rows)):
        raise ValueError("decision_count must match rows")
    if report.pass_decision_count != _status_count(rows, "pass"):
        raise ValueError("pass_decision_count must match rows")
    if report.watch_decision_count != _status_count(rows, "watch"):
        raise ValueError("watch_decision_count must match rows")
    if report.breached_decision_count != _status_count(rows, "breached"):
        raise ValueError("breached_decision_count must match rows")
    if report.operator_missing_decision_count != _operator_missing_count(rows):
        raise ValueError("operator_missing_decision_count must match rows")
    if report.source_refresh_due_decision_count != _source_refresh_due_count(rows):
        raise ValueError("source_refresh_due_decision_count must match rows")
    if report.blocking_reason_decision_count != _blocking_reason_count(rows):
        raise ValueError("blocking_reason_decision_count must match rows")
    if report.pass_decision_ratio != _ratio(report.pass_decision_count, report.decision_count):
        raise ValueError("pass_decision_ratio must match rows")
    if report.sla_status != _summary_status(rows):
        raise ValueError("sla_status must match rows")
    if report.breach_risk != _summary_risk(rows):
        raise ValueError("breach_risk must match rows")
    if report.reason_codes != _summary_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _payload_items(
    report: ManualDecisionSlaBreachReadinessReport,
    *,
    digest: str,
) -> dict[str, object]:
    return {
        "config_version": report.config_version,
        "sla_status": report.sla_status,
        "breach_risk": report.breach_risk,
        "decision_count": _decimal_string(report.decision_count),
        "pass_decision_count": _decimal_string(report.pass_decision_count),
        "watch_decision_count": _decimal_string(report.watch_decision_count),
        "breached_decision_count": _decimal_string(report.breached_decision_count),
        "operator_missing_decision_count": _decimal_string(
            report.operator_missing_decision_count,
        ),
        "source_refresh_due_decision_count": _decimal_string(
            report.source_refresh_due_decision_count,
        ),
        "blocking_reason_decision_count": _decimal_string(
            report.blocking_reason_decision_count,
        ),
        "urgent_close_decision_count": _decimal_string(
            report.urgent_close_decision_count,
        ),
        "pass_decision_ratio": _decimal_string(report.pass_decision_ratio),
        "reason_codes": list(report.reason_codes),
        "rows": [_row_payload(row) for row in report.rows],
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
        "derived_validation_digest": digest,
    }


def _payload_values(values: Mapping[str, object], *, digest: str) -> dict[str, object]:
    return {
        "config_version": values["config_version"],
        "sla_status": values["sla_status"],
        "breach_risk": values["breach_risk"],
        "decision_count": _decimal_string(values["decision_count"]),
        "pass_decision_count": _decimal_string(values["pass_decision_count"]),
        "watch_decision_count": _decimal_string(values["watch_decision_count"]),
        "breached_decision_count": _decimal_string(values["breached_decision_count"]),
        "operator_missing_decision_count": _decimal_string(
            values["operator_missing_decision_count"],
        ),
        "source_refresh_due_decision_count": _decimal_string(
            values["source_refresh_due_decision_count"],
        ),
        "blocking_reason_decision_count": _decimal_string(
            values["blocking_reason_decision_count"],
        ),
        "urgent_close_decision_count": _decimal_string(
            values["urgent_close_decision_count"],
        ),
        "pass_decision_ratio": _decimal_string(values["pass_decision_ratio"]),
        "reason_codes": list(values["reason_codes"]),
        "rows": [_row_payload(row) for row in values["rows"]],
        "paper_only": values["paper_only"],
        "report_only": values["report_only"],
        "readonly": values["readonly"],
        "derived_validation_digest": digest,
    }


def _row_payload(row: ManualDecisionSlaBreachReadinessRow) -> dict[str, object]:
    return {
        "decision_id": row.decision_id,
        "queued_age_hours": _decimal_string(row.queued_age_hours),
        "market_close_hours": _decimal_string(row.market_close_hours),
        "source_refresh_due": row.source_refresh_due,
        "operator_owner_present": row.operator_owner_present,
        "blocking_reason_count": _decimal_string(row.blocking_reason_count),
        "sla_status": row.sla_status,
        "breach_risk": row.breach_risk,
        "reason_codes": list(row.reason_codes),
        "manual_next_step": row.manual_next_step,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _validate_public_payload(payload: Mapping[str, object]) -> None:
    if not isinstance(payload, Mapping):
        raise ValueError("public payload must be a mapping")
    if tuple(payload) != PAYLOAD_FIELDS:
        raise ValueError("public payload fields must match report contract")
    _reject_public_numerics(payload)
    _require_public_label("config_version", payload["config_version"])
    _require_member("sla_status", payload["sla_status"], SLA_STATUS_VALUES)
    _require_member("breach_risk", payload["breach_risk"], BREACH_RISK_VALUES)
    _require_hard_flags("public payload", payload)
    for field_name in DECIMAL_PAYLOAD_FIELDS:
        if type(payload[field_name]) is not str:
            raise ValueError("public payload numerics must be decimal strings")
        if field_name == "pass_decision_ratio":
            _require_ratio(field_name, _parse_decimal_string(field_name, payload[field_name]))
        else:
            _require_count_decimal(field_name, _parse_decimal_string(field_name, payload[field_name]))
    reason_codes = _tuple_from_public_list("reason_codes", payload["reason_codes"])
    _normalize_reason_codes("reason_codes", reason_codes)
    rows = _rows_from_public(payload["rows"])
    if _summary_status(rows) != payload["sla_status"]:
        raise ValueError("sla_status must match rows")
    if _summary_risk(rows) != payload["breach_risk"]:
        raise ValueError("breach_risk must match rows")
    if _summary_reason_codes(rows) != reason_codes:
        raise ValueError("reason_codes must match rows")
    if _count(len(rows)) != _parse_decimal_string("decision_count", payload["decision_count"]):
        raise ValueError("decision_count must match rows")
    _require_digest("derived_validation_digest", payload["derived_validation_digest"])
    payload_without_digest = dict(payload)
    payload_without_digest["derived_validation_digest"] = ""
    if payload["derived_validation_digest"] != _payload_digest(payload_without_digest):
        raise ValueError("derived_validation_digest must match public payload")


def _rows_from_public(value: object) -> tuple[ManualDecisionSlaBreachReadinessRow, ...]:
    if type(value) is not list:
        raise ValueError("rows must be a public list")
    rows: list[ManualDecisionSlaBreachReadinessRow] = []
    for item in value:
        if type(item) is not dict:
            raise ValueError("row payload must be a public mapping")
        if tuple(item) != ROW_PAYLOAD_FIELDS:
            raise ValueError("row payload fields must match report contract")
        _reject_public_numerics(item)
        for field_name in ROW_DECIMAL_PAYLOAD_FIELDS:
            if type(item[field_name]) is not str:
                raise ValueError("row payload numerics must be decimal strings")
        rows.append(
            ManualDecisionSlaBreachReadinessRow(
                decision_id=item["decision_id"],
                queued_age_hours=_parse_decimal_string(
                    "queued_age_hours",
                    item["queued_age_hours"],
                ),
                market_close_hours=_parse_decimal_string(
                    "market_close_hours",
                    item["market_close_hours"],
                ),
                source_refresh_due=item["source_refresh_due"],
                operator_owner_present=item["operator_owner_present"],
                blocking_reason_count=_parse_decimal_string(
                    "blocking_reason_count",
                    item["blocking_reason_count"],
                ),
                sla_status=item["sla_status"],
                breach_risk=item["breach_risk"],
                reason_codes=_tuple_from_public_list(
                    "reason_codes",
                    item["reason_codes"],
                ),
                manual_next_step=item["manual_next_step"],
                paper_only=item["paper_only"],
                report_only=item["report_only"],
                readonly=item["readonly"],
            ),
        )
    normalized = tuple(rows)
    if tuple(row.decision_id for row in normalized) != tuple(
        sorted(row.decision_id for row in normalized),
    ):
        raise ValueError("rows must be deterministic by decision_id")
    return normalized


def _payload_digest(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(
        _json_ready(payload),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _json_ready(value: object) -> object:
    if type(value) is dict or isinstance(value, Mapping):
        converted: dict[str, object] = {}
        for name, item in value.items():
            if type(name) is not str:
                raise ValueError("public payload field names must be strings")
            converted[name] = _json_ready(item)
        return converted
    if type(value) is list or type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        return _decimal_string(value)
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("value is not public payload serializable")


def _normalize_items(
    items: Iterable[ManualDecisionSlaBreachReadinessItem],
) -> tuple[ManualDecisionSlaBreachReadinessItem, ...]:
    if isinstance(items, (str, bytes)):
        raise ValueError("items must be an iterable of readiness items")
    normalized: list[ManualDecisionSlaBreachReadinessItem] = []
    for item in items:
        if type(item) is not ManualDecisionSlaBreachReadinessItem:
            raise ValueError("items must contain ManualDecisionSlaBreachReadinessItem")
        _require_hard_flags("item", item)
        normalized.append(item)
    return tuple(normalized)


def _normalize_rows(
    rows: object,
) -> tuple[ManualDecisionSlaBreachReadinessRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ManualDecisionSlaBreachReadinessRow:
            raise ValueError("rows must contain ManualDecisionSlaBreachReadinessRow")
        _require_hard_flags("row", row)
    return rows


def _status_count(
    rows: tuple[ManualDecisionSlaBreachReadinessRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.sla_status == status))


def _operator_missing_count(
    rows: tuple[ManualDecisionSlaBreachReadinessRow, ...],
) -> Decimal:
    return _count(sum(1 for row in rows if not row.operator_owner_present))


def _source_refresh_due_count(
    rows: tuple[ManualDecisionSlaBreachReadinessRow, ...],
) -> Decimal:
    return _count(sum(1 for row in rows if row.source_refresh_due))


def _blocking_reason_count(
    rows: tuple[ManualDecisionSlaBreachReadinessRow, ...],
) -> Decimal:
    return _count(sum(1 for row in rows if row.blocking_reason_count > ZERO))


def _urgent_close_count(
    rows: tuple[ManualDecisionSlaBreachReadinessRow, ...],
    *,
    config: ManualDecisionSlaBreachReadinessConfig,
) -> Decimal:
    return _count(sum(1 for row in rows if row.market_close_hours <= config.market_close_urgent_hours))


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(DECIMAL_QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return (numerator / denominator).quantize(DECIMAL_QUANTUM, rounding=ROUND_HALF_UP)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value.quantize(DECIMAL_QUANTUM, rounding=ROUND_HALF_UP)


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _parse_decimal_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a decimal string")
    try:
        parsed = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a decimal string") from exc
    return _require_decimal(field_name, parsed)


def _decimal_string(value: object) -> str:
    if type(value) is not Decimal:
        raise ValueError("public payload numerics must be Decimal values")
    return format(value.quantize(DECIMAL_QUANTUM, rounding=ROUND_HALF_UP), "f")


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value or any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must be a public label")
    return value


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if isinstance(value, Mapping):
            flag_value = value.get(flag_name)
        else:
            flag_value = getattr(value, flag_name)
        if flag_value is not True:
            raise ValueError(f"{field_name} {flag_name} must be True")


def _normalize_reason_codes(field_name: str, values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        normalized.append(_require_public_label(field_name, value))
    if not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(dict.fromkeys(normalized))


def _tuple_from_public_list(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a public list")
    return tuple(_require_public_label(field_name, item) for item in value)


def _require_manual_next_step(value: object) -> str:
    label = _require_public_label("manual_next_step", value)
    if label not in (
        PASS_NEXT_STEP,
        QUEUE_NEXT_STEP,
        SOURCE_NEXT_STEP,
        OWNER_NEXT_STEP,
        BLOCKING_NEXT_STEP,
        BREACHED_NEXT_STEP,
    ):
        raise ValueError("manual_next_step must match SLA readiness reason")
    return label


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a digest")
    for character in value:
        if character not in "0123456789abcdef":
            raise ValueError(f"{field_name} must be a digest")


def _reject_public_numerics(value: object) -> None:
    if type(value) is int or type(value) is float:
        raise ValueError("public payload numerics must be decimal strings")
    if type(value) is dict:
        for item in value.values():
            _reject_public_numerics(item)
        return
    if type(value) is list:
        for item in value:
            _reject_public_numerics(item)
