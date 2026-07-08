"""Pure report-only aggregation for team resolution feedback backlog pressure."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any


__all__ = (
    "STATUSES",
    "ResearchTeamResolutionFeedbackBacklogConfig",
    "ResearchTeamResolutionFeedbackBacklogInput",
    "ResearchTeamResolutionFeedbackBacklogReasonCodeCount",
    "ResearchTeamResolutionFeedbackBacklogReport",
    "ResearchTeamResolutionFeedbackBacklogRow",
    "build_research_team_resolution_feedback_backlog_report",
    "research_team_resolution_feedback_backlog_report_payload",
    "validate_research_team_resolution_feedback_backlog_public_payload",
)


DEFAULT_CONFIG_VERSION = "research-team-resolution-feedback-backlog-report-v0"
STATUSES = ("pass", "watch", "block")
_STATUS_SET = frozenset(STATUSES)
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_QUANT = Decimal("0.000001")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_UNSAFE_PUBLIC_TERMS = (
    "candidate",
    "market",
    "slug",
    "question",
    "source",
    "url",
    "http",
    "dsn",
    "table",
    "private",
    "token",
    "secret",
    "credential",
    "wallet",
    "auth",
    "order",
    "trade",
    "live",
    "network",
    "sizing",
    "recommend",
)
_REPORT_REASON_PRIORITY = (
    "resolution_feedback_backlog_block",
    "resolution_feedback_backlog_watch",
    "resolution_feedback_backlog_pass",
    "resolution_feedback_backlog_empty",
    "calibration_writeback_age_block",
    "manual_escalation_urgency_block",
    "stale_feedback_pressure_block",
    "calibration_writeback_age_watch",
    "manual_escalation_urgency_watch",
    "stale_feedback_pressure_watch",
)


@dataclass(frozen=True)
class ResearchTeamResolutionFeedbackBacklogConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    watch_calibration_writeback_age_seconds: Decimal = Decimal("3600.000000")
    block_calibration_writeback_age_seconds: Decimal = Decimal("86400.000000")
    stale_feedback_age_seconds: Decimal = Decimal("86400.000000")
    watch_stale_feedback_pressure: Decimal = Decimal("0.350000")
    block_stale_feedback_pressure: Decimal = Decimal("0.700000")
    watch_manual_escalation_urgency: Decimal = Decimal("0.500000")
    block_manual_escalation_urgency: Decimal = Decimal("0.900000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamResolutionFeedbackBacklogConfig,
            "config",
        )
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_calibration_writeback_age_seconds",
            "block_calibration_writeback_age_seconds",
            "stale_feedback_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.block_calibration_writeback_age_seconds
            <= self.watch_calibration_writeback_age_seconds
        ):
            raise ValueError(
                "block_calibration_writeback_age_seconds must exceed "
                "watch_calibration_writeback_age_seconds",
            )
        for field_name in (
            "watch_stale_feedback_pressure",
            "block_stale_feedback_pressure",
            "watch_manual_escalation_urgency",
            "block_manual_escalation_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_stale_feedback_pressure <= self.watch_stale_feedback_pressure:
            raise ValueError(
                "block_stale_feedback_pressure must exceed watch_stale_feedback_pressure",
            )
        if self.block_manual_escalation_urgency <= self.watch_manual_escalation_urgency:
            raise ValueError(
                "block_manual_escalation_urgency must exceed "
                "watch_manual_escalation_urgency",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamResolutionFeedbackBacklogInput:
    feedback_key: str
    team_key: str
    domain_key: str
    unresolved_outcome_feedback: bool
    calibration_writeback_age_seconds: Decimal
    feedback_age_seconds: Decimal
    feedback_priority: Decimal
    manual_escalation_requested: bool
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamResolutionFeedbackBacklogInput,
            "feedback input",
        )
        for field_name in ("feedback_key", "team_key", "domain_key"):
            _require_public_identifier(field_name, getattr(self, field_name))
        _require_bool("unresolved_outcome_feedback", self.unresolved_outcome_feedback)
        for field_name in (
            "calibration_writeback_age_seconds",
            "feedback_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "feedback_priority",
            _require_probability_decimal("feedback_priority", self.feedback_priority),
        )
        _require_bool("manual_escalation_requested", self.manual_escalation_requested)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("feedback input", self)


@dataclass(frozen=True)
class ResearchTeamResolutionFeedbackBacklogRow:
    feedback_key: str
    team_key: str
    domain_key: str
    unresolved_outcome_feedback: bool
    calibration_writeback_age_seconds: Decimal
    calibration_writeback_age_pressure: Decimal
    feedback_age_seconds: Decimal
    feedback_age_pressure: Decimal
    feedback_priority: Decimal
    stale_feedback_pressure: Decimal
    manual_escalation_requested: bool
    manual_escalation_urgency: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamResolutionFeedbackBacklogRow, "row")
        for field_name in ("feedback_key", "team_key", "domain_key"):
            _require_public_identifier(field_name, getattr(self, field_name))
        _require_bool("unresolved_outcome_feedback", self.unresolved_outcome_feedback)
        for field_name in ("calibration_writeback_age_seconds", "feedback_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "calibration_writeback_age_pressure",
            "feedback_age_pressure",
            "feedback_priority",
            "stale_feedback_pressure",
            "manual_escalation_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_bool("manual_escalation_requested", self.manual_escalation_requested)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchTeamResolutionFeedbackBacklogReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamResolutionFeedbackBacklogReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamResolutionFeedbackBacklogReport:
    generated_at: datetime
    config_version: str
    status: str
    feedback_count: Decimal
    unresolved_outcome_feedback_count: Decimal
    impacted_domain_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_calibration_writeback_age_seconds: Decimal
    stale_feedback_pressure: Decimal
    manual_escalation_urgency: Decimal
    rows: tuple[ResearchTeamResolutionFeedbackBacklogRow, ...]
    reason_code_counts: tuple[
        ResearchTeamResolutionFeedbackBacklogReasonCodeCount,
        ...
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamResolutionFeedbackBacklogReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in (
            "feedback_count",
            "unresolved_outcome_feedback_count",
            "impacted_domain_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_calibration_writeback_age_seconds",
            _require_nonnegative_decimal(
                "max_calibration_writeback_age_seconds",
                self.max_calibration_writeback_age_seconds,
            ),
        )
        for field_name in ("stale_feedback_pressure", "manual_escalation_urgency"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        object.__setattr__(
            self,
            "derived_validation_digest",
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            ),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")


def build_research_team_resolution_feedback_backlog_report(
    feedback_items: Iterable[ResearchTeamResolutionFeedbackBacklogInput],
    *,
    config: ResearchTeamResolutionFeedbackBacklogConfig,
    generated_at: datetime,
) -> ResearchTeamResolutionFeedbackBacklogReport:
    if type(config) is not ResearchTeamResolutionFeedbackBacklogConfig:
        raise ValueError(
            "config must be a ResearchTeamResolutionFeedbackBacklogConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_items = _normalize_feedback_items(feedback_items)
    rows = tuple(
        _row_from_item(item, config=config)
        for item in sorted(normalized_items, key=lambda value: value.feedback_key)
    )
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "feedback_count": _decimal_count(len(rows)),
        "unresolved_outcome_feedback_count": _decimal_count(
            sum(1 for row in rows if row.unresolved_outcome_feedback),
        ),
        "impacted_domain_count": _decimal_count(
            len(frozenset(row.domain_key for row in rows if row.status != "pass")),
        ),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "max_calibration_writeback_age_seconds": max(
            (row.calibration_writeback_age_seconds for row in rows),
            default=_ZERO,
        ),
        "stale_feedback_pressure": max(
            (row.stale_feedback_pressure for row in rows),
            default=_ZERO,
        ),
        "manual_escalation_urgency": max(
            (row.manual_escalation_urgency for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_code_counts": _reason_code_counts(rows, reason_codes),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchTeamResolutionFeedbackBacklogReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_team_resolution_feedback_backlog_report_payload(
    report: ResearchTeamResolutionFeedbackBacklogReport,
) -> dict[str, Any]:
    if type(report) is not ResearchTeamResolutionFeedbackBacklogReport:
        raise ValueError(
            "report must be a ResearchTeamResolutionFeedbackBacklogReport",
        )
    _require_hard_flags("report", report)
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_research_team_resolution_feedback_backlog_public_payload(payload)
    return payload


def validate_research_team_resolution_feedback_backlog_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_public_payload("report payload", payload)
    _require_payload_flags(payload)
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != _public_payload_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    return True


def _row_from_item(
    item: ResearchTeamResolutionFeedbackBacklogInput,
    *,
    config: ResearchTeamResolutionFeedbackBacklogConfig,
) -> ResearchTeamResolutionFeedbackBacklogRow:
    calibration_age_pressure = _age_pressure(
        item.calibration_writeback_age_seconds,
        watch_seconds=config.watch_calibration_writeback_age_seconds,
        block_seconds=config.block_calibration_writeback_age_seconds,
    )
    feedback_age_pressure = _age_pressure(
        item.feedback_age_seconds,
        watch_seconds=_ZERO,
        block_seconds=config.stale_feedback_age_seconds,
    )
    stale_pressure = _quantize(
        (feedback_age_pressure + item.feedback_priority) / Decimal("2"),
    )
    urgency_base = max(calibration_age_pressure, stale_pressure, item.feedback_priority)
    manual_urgency = _ONE if item.manual_escalation_requested else urgency_base
    status = _row_status(
        calibration_writeback_age_pressure=calibration_age_pressure,
        stale_feedback_pressure=stale_pressure,
        manual_escalation_urgency=manual_urgency,
        config=config,
    )
    return ResearchTeamResolutionFeedbackBacklogRow(
        feedback_key=item.feedback_key,
        team_key=item.team_key,
        domain_key=item.domain_key,
        unresolved_outcome_feedback=item.unresolved_outcome_feedback,
        calibration_writeback_age_seconds=item.calibration_writeback_age_seconds,
        calibration_writeback_age_pressure=calibration_age_pressure,
        feedback_age_seconds=item.feedback_age_seconds,
        feedback_age_pressure=feedback_age_pressure,
        feedback_priority=item.feedback_priority,
        stale_feedback_pressure=stale_pressure,
        manual_escalation_requested=item.manual_escalation_requested,
        manual_escalation_urgency=manual_urgency,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            calibration_writeback_age_pressure=calibration_age_pressure,
            stale_feedback_pressure=stale_pressure,
            manual_escalation_urgency=manual_urgency,
            input_reason_codes=item.reason_codes,
            config=config,
        ),
    )


def _normalize_feedback_items(
    feedback_items: Iterable[ResearchTeamResolutionFeedbackBacklogInput],
) -> tuple[ResearchTeamResolutionFeedbackBacklogInput, ...]:
    if isinstance(feedback_items, (str, bytes)):
        raise ValueError("feedback_items must be an iterable")
    try:
        items = tuple(feedback_items)
    except TypeError as exc:
        raise ValueError("feedback_items must be an iterable") from exc
    for item in items:
        if type(item) is not ResearchTeamResolutionFeedbackBacklogInput:
            raise ValueError(
                "feedback_items must contain "
                "ResearchTeamResolutionFeedbackBacklogInput values",
            )
        _require_hard_flags("feedback input", item)
    return items


def _age_pressure(
    value: Decimal,
    *,
    watch_seconds: Decimal,
    block_seconds: Decimal,
) -> Decimal:
    if value <= watch_seconds:
        return _ZERO
    if value >= block_seconds:
        return _ONE
    if watch_seconds == _ZERO:
        return _quantize(value / block_seconds)
    return _quantize((value - watch_seconds) / (block_seconds - watch_seconds))


def _row_status(
    *,
    calibration_writeback_age_pressure: Decimal,
    stale_feedback_pressure: Decimal,
    manual_escalation_urgency: Decimal,
    config: ResearchTeamResolutionFeedbackBacklogConfig,
) -> str:
    if (
        calibration_writeback_age_pressure >= _ONE
        or stale_feedback_pressure >= config.block_stale_feedback_pressure
        or manual_escalation_urgency >= config.block_manual_escalation_urgency
    ):
        return "block"
    if (
        calibration_writeback_age_pressure > _ZERO
        or stale_feedback_pressure >= config.watch_stale_feedback_pressure
        or manual_escalation_urgency >= config.watch_manual_escalation_urgency
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    calibration_writeback_age_pressure: Decimal,
    stale_feedback_pressure: Decimal,
    manual_escalation_urgency: Decimal,
    input_reason_codes: tuple[str, ...],
    config: ResearchTeamResolutionFeedbackBacklogConfig,
) -> tuple[str, ...]:
    if status == "pass":
        return ("resolution_feedback_backlog_pass",)
    codes: list[str] = []
    if calibration_writeback_age_pressure >= _ONE:
        codes.append("calibration_writeback_age_block")
    elif calibration_writeback_age_pressure > _ZERO:
        codes.append("calibration_writeback_age_watch")
    if manual_escalation_urgency >= config.block_manual_escalation_urgency:
        codes.append("manual_escalation_urgency_block")
    elif manual_escalation_urgency >= config.watch_manual_escalation_urgency:
        codes.append("manual_escalation_urgency_watch")
    if stale_feedback_pressure >= config.block_stale_feedback_pressure:
        codes.append("stale_feedback_pressure_block")
    elif stale_feedback_pressure >= config.watch_stale_feedback_pressure:
        codes.append("stale_feedback_pressure_watch")
    for reason_code in input_reason_codes:
        codes.append(f"input_{reason_code}")
    return tuple(dict.fromkeys(codes))


def _report_status(
    rows: tuple[ResearchTeamResolutionFeedbackBacklogRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamResolutionFeedbackBacklogRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("resolution_feedback_backlog_empty",)
    status = _report_status(rows)
    if status == "pass":
        return ("resolution_feedback_backlog_pass",)
    present = tuple(
        dict.fromkeys(
            reason_code
            for row in rows
            for reason_code in row.reason_codes
            if reason_code != "resolution_feedback_backlog_pass"
        ),
    )
    status_reason = (
        "resolution_feedback_backlog_block"
        if status == "block"
        else "resolution_feedback_backlog_watch"
    )
    return (status_reason,) + tuple(
        reason_code
        for reason_code in _REPORT_REASON_PRIORITY
        if reason_code in present
    ) + tuple(
        sorted(
            reason_code
            for reason_code in present
            if reason_code not in _REPORT_REASON_PRIORITY
        ),
    )


def _reason_code_counts(
    rows: tuple[ResearchTeamResolutionFeedbackBacklogRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchTeamResolutionFeedbackBacklogReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchTeamResolutionFeedbackBacklogReasonCodeCount(
                reason_code=reason_codes[0],
                count=_ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchTeamResolutionFeedbackBacklogReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _status_count(
    rows: tuple[ResearchTeamResolutionFeedbackBacklogRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _normalize_rows(
    rows: tuple[ResearchTeamResolutionFeedbackBacklogRow, ...],
) -> tuple[ResearchTeamResolutionFeedbackBacklogRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchTeamResolutionFeedbackBacklogRow:
            raise ValueError(
                "rows must contain ResearchTeamResolutionFeedbackBacklogRow values",
            )
        _require_hard_flags("row", row)
    if rows != tuple(sorted(rows, key=lambda row: row.feedback_key)):
        raise ValueError("rows must be sorted by feedback_key")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchTeamResolutionFeedbackBacklogReasonCodeCount, ...],
) -> tuple[ResearchTeamResolutionFeedbackBacklogReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchTeamResolutionFeedbackBacklogReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTeamResolutionFeedbackBacklogReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    if counts != tuple(sorted(counts, key=lambda value: value.reason_code)):
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row_consistency(row: ResearchTeamResolutionFeedbackBacklogRow) -> None:
    if not row.reason_codes:
        raise ValueError("reason_codes must be nonempty")
    if row.status == "pass" and row.reason_codes != (
        "resolution_feedback_backlog_pass",
    ):
        raise ValueError("pass rows must use the pass reason code")
    if row.status != "pass" and not any(
        reason_code.endswith(f"_{row.status}") for reason_code in row.reason_codes
    ):
        raise ValueError("reason_codes must include row status")


def _validate_report_consistency(
    report: ResearchTeamResolutionFeedbackBacklogReport,
) -> None:
    if report.feedback_count != _decimal_count(len(report.rows)):
        raise ValueError("feedback_count must match rows")
    if report.unresolved_outcome_feedback_count != _decimal_count(
        sum(1 for row in report.rows if row.unresolved_outcome_feedback),
    ):
        raise ValueError("unresolved_outcome_feedback_count must match rows")
    if report.impacted_domain_count != _decimal_count(
        len(frozenset(row.domain_key for row in report.rows if row.status != "pass")),
    ):
        raise ValueError("impacted_domain_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.max_calibration_writeback_age_seconds != max(
        (row.calibration_writeback_age_seconds for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_calibration_writeback_age_seconds must match rows")
    if report.stale_feedback_pressure != max(
        (row.stale_feedback_pressure for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("stale_feedback_pressure must match rows")
    if report.manual_escalation_urgency != max(
        (row.manual_escalation_urgency for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("manual_escalation_urgency must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _report_values_without_digest(
    report: ResearchTeamResolutionFeedbackBacklogReport,
) -> dict[str, object]:
    return {
        field.name: getattr(report, field.name)
        for field in fields(report)
        if field.name != "derived_validation_digest"
    }


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    ready = _json_ready(dict(values))
    _reject_public_payload("report digest payload", ready)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _public_payload_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest")
    _reject_public_payload("report digest payload", digest_payload)
    encoded = json.dumps(digest_payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, Decimal):
        raise ValueError("JSON value must use exact Decimal values")
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, datetime):
        raise ValueError("JSON datetime value must be an exact datetime")
    if type(value) is bool:
        return value
    if type(value) is int:
        raise ValueError("JSON numeric value must be Decimal-derived")
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if type(value) is str:
        _reject_text_value("JSON string value", value)
        return value
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_text_value("JSON object key", key)
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_public_payload(label: str, value: object, path: str = "") -> None:
    current_path = path or label
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_text_value(f"{current_path} key", key)
            item_path = key if not path else f"{path}.{key}"
            if key in ("paper_only", "report_only", "readonly") and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_public_payload(label, item, item_path)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _reject_public_payload(label, item, f"{current_path}[{index}]")
        return
    if type(value) is str:
        _reject_text_value(current_path, value)
        return
    if value is None or type(value) is bool:
        return
    if type(value) in (int, float) or isinstance(value, Decimal):
        raise ValueError(f"{current_path} must use Decimal-derived strings")
    raise ValueError(f"{current_path} is not JSON-ready")


def _reject_text_value(label: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{label} must be a string")
    if value.strip() != value:
        raise ValueError(f"{label} has unsafe public value")
    lowered = value.lower()
    if "://" in lowered or "?" in lowered:
        raise ValueError(f"{label} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{label} has unsafe public value")


def _require_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_identifier(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _reject_text_value(field_name, value)
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    return value


def _require_reason_code(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _reject_text_value(field_name, value)
    if not _REASON_CODE_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a reason code")
    return value


def _normalize_reason_codes(
    field_name: str,
    value: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must be nonempty")
    normalized: list[str] = []
    for reason_code in value:
        normalized.append(_require_reason_code(field_name, reason_code))
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    return tuple(normalized)


def _require_status(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in _STATUS_SET:
        raise ValueError(f"{field_name} must be one of pass/watch/block")
    return value


def _require_bool(field_name: str, value: bool) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_probability_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO or decimal_value > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_nonnegative_whole_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _quantize(Decimal(value))


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_sha256_digest(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")
