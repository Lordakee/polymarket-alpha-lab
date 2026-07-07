"""Pure readonly candidate monitoring summary for human research review."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_CANDIDATE_MONITORING_SUMMARY_CONFIG_VERSION",
    "ResearchCandidateMonitoringSummaryConfig",
    "ResearchCandidateMonitoringSummaryInput",
    "ResearchCandidateMonitoringSummaryReport",
    "ResearchCandidateMonitoringSummaryRow",
    "build_research_candidate_monitoring_summary",
    "build_research_candidate_monitoring_summary_from_public_payloads",
    "research_candidate_monitoring_summary_payload",
    "validate_research_candidate_monitoring_summary_public_payload",
)


DEFAULT_RESEARCH_CANDIDATE_MONITORING_SUMMARY_CONFIG_VERSION = (
    "research-candidate-monitoring-summary-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_REDACTED_SURFACE_RE = re.compile(r"^redacted-monitoring-surface-[0-9]{6}$")

_PUBLIC_STATUSES = ("pass", "watch", "block")
_MONITORING_SURFACES = (
    "snapshot_summary",
    "resolution_watch",
    "alert_queue",
    "pipeline_health",
)
_NEXT_HUMAN_ACTION_BY_STATUS = {
    "pass": "continue_manual_monitoring",
    "watch": "monitor_before_use",
    "block": "manual_rework_required",
}
_STATUS_WEIGHT = {
    "block": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}
_SURFACE_ORDER = {
    surface: Decimal(index).quantize(_QUANT)
    for index, surface in enumerate(_MONITORING_SURFACES)
}
_REASON_CODE_SEQUENCE = (
    "monitoring_block_present",
    "monitoring_watch_present",
    "monitoring_all_pass",
    "monitoring_surface_missing",
    "snapshot_summary_block",
    "snapshot_summary_watch",
    "snapshot_summary_pass",
    "resolution_watch_block",
    "resolution_watch_watch",
    "resolution_watch_pass",
    "alert_queue_block",
    "alert_queue_watch",
    "alert_queue_pass",
    "pipeline_health_block",
    "pipeline_health_watch",
    "pipeline_health_pass",
)
_REPORT_REASON_CODE_SEQUENCE = (
    "monitoring_block_present",
    "monitoring_watch_present",
    "monitoring_all_pass",
    "monitoring_surface_missing",
    "snapshot_summary_block",
    "resolution_watch_block",
    "alert_queue_block",
    "pipeline_health_block",
    "snapshot_summary_watch",
    "resolution_watch_watch",
    "alert_queue_watch",
    "pipeline_health_watch",
)
_REPORT_PAYLOAD_KEYS = (
    "generated_at",
    "config_version",
    "status",
    "surface_count",
    "pass_surface_count",
    "watch_surface_count",
    "block_surface_count",
    "total_input_count",
    "total_watch_count",
    "total_block_count",
    "total_trigger_count",
    "max_attention_score",
    "average_attention_score",
    "reason_codes",
    "rows",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
_ROW_PAYLOAD_KEYS = (
    "surface_ref",
    "monitoring_surface",
    "surface_rank",
    "public_status",
    "input_count",
    "watch_count",
    "block_count",
    "trigger_count",
    "attention_score",
    "monitoring_priority_score",
    "next_human_action",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
_UNSAFE_PUBLIC_FRAGMENTS = (
    "raw_candidate",
    "raw-candidate",
    "raw candidate",
    "candidate_id",
    "candidate-id",
    "candidate id",
    "market_id",
    "market-id",
    "market id",
    "market_slug",
    "market-slug",
    "market slug",
    "market_question",
    "market-question",
    "market question",
    "question",
    "source_ref",
    "source-ref",
    "source ref",
    "source_reference",
    "source-reference",
    "source reference",
    "source_url",
    "source-url",
    "source url",
    "source_text",
    "source-text",
    "source text",
    "http://",
    "https://",
    "://",
    "url",
    "dsn",
    "postgres://",
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
    "recommend",
)


@dataclass(frozen=True)
class ResearchCandidateMonitoringSummaryConfig:
    config_version: str = DEFAULT_RESEARCH_CANDIDATE_MONITORING_SUMMARY_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchCandidateMonitoringSummaryConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ResearchCandidateMonitoringSummaryConfig)
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_CANDIDATE_MONITORING_SUMMARY_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchCandidateMonitoringSummaryInput:
    monitoring_surface: str
    public_status: str
    input_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    attention_score: Decimal
    trigger_count: Decimal = Decimal("0.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchCandidateMonitoringSummaryInput does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("input", self, ResearchCandidateMonitoringSummaryInput)
        _require_monitoring_surface("monitoring_surface", self.monitoring_surface)
        _require_public_status("public_status", self.public_status)
        for field_name in ("input_count", "watch_count", "block_count", "trigger_count"):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "attention_score",
            _require_ratio_decimal("attention_score", self.attention_score),
        )
        _validate_input(self)
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchCandidateMonitoringSummaryRow:
    surface_ref: str
    monitoring_surface: str
    surface_rank: Decimal
    public_status: str
    input_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    trigger_count: Decimal
    attention_score: Decimal
    monitoring_priority_score: Decimal
    next_human_action: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchCandidateMonitoringSummaryRow does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchCandidateMonitoringSummaryRow)
        _require_surface_ref("surface_ref", self.surface_ref)
        _require_monitoring_surface("monitoring_surface", self.monitoring_surface)
        object.__setattr__(
            self,
            "surface_rank",
            _require_count_decimal("surface_rank", self.surface_rank),
        )
        _require_public_status("public_status", self.public_status)
        for field_name in ("input_count", "watch_count", "block_count", "trigger_count"):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("attention_score", "monitoring_priority_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_next_human_action("next_human_action", self.next_human_action)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchCandidateMonitoringSummaryReport:
    generated_at: datetime
    config_version: str
    status: str
    surface_count: Decimal
    pass_surface_count: Decimal
    watch_surface_count: Decimal
    block_surface_count: Decimal
    total_input_count: Decimal
    total_watch_count: Decimal
    total_block_count: Decimal
    total_trigger_count: Decimal
    max_attention_score: Decimal
    average_attention_score: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchCandidateMonitoringSummaryRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchCandidateMonitoringSummaryReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchCandidateMonitoringSummaryReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_CANDIDATE_MONITORING_SUMMARY_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_public_status("status", self.status)
        for field_name in (
            "surface_count",
            "pass_surface_count",
            "watch_surface_count",
            "block_surface_count",
            "total_input_count",
            "total_watch_count",
            "total_block_count",
            "total_trigger_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_attention_score", "average_attention_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report payload")
        _require_digest("derived_validation_digest", self.derived_validation_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return research_candidate_monitoring_summary_payload(self)


def build_research_candidate_monitoring_summary(
    inputs: tuple[ResearchCandidateMonitoringSummaryInput, ...]
    | list[ResearchCandidateMonitoringSummaryInput],
    *,
    generated_at: datetime,
    config: ResearchCandidateMonitoringSummaryConfig | None = None,
) -> ResearchCandidateMonitoringSummaryReport:
    """Aggregate desensitized monitoring reports for manual research review only."""

    if config is None:
        config = ResearchCandidateMonitoringSummaryConfig()
    if type(config) is not ResearchCandidateMonitoringSummaryConfig:
        raise ValueError("config must be a ResearchCandidateMonitoringSummaryConfig")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    sorted_inputs = tuple(sorted(normalized_inputs, key=_input_sort_key))
    rows = tuple(
        _row_from_input(item, index=index)
        for index, item in enumerate(sorted_inputs, start=1)
    )
    return ResearchCandidateMonitoringSummaryReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=_report_status(rows),
        surface_count=_decimal_count(len(rows)),
        pass_surface_count=_decimal_count(_status_count(rows, "pass")),
        watch_surface_count=_decimal_count(_status_count(rows, "watch")),
        block_surface_count=_decimal_count(_status_count(rows, "block")),
        total_input_count=_sum_decimal(row.input_count for row in rows),
        total_watch_count=_sum_decimal(row.watch_count for row in rows),
        total_block_count=_sum_decimal(row.block_count for row in rows),
        total_trigger_count=_sum_decimal(row.trigger_count for row in rows),
        max_attention_score=max((row.attention_score for row in rows), default=_ZERO),
        average_attention_score=_average_ratio(tuple(row.attention_score for row in rows)),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def build_research_candidate_monitoring_summary_from_public_payloads(
    *,
    candidate_snapshot_payload: dict[str, Any],
    resolution_watch_payload: dict[str, Any],
    alert_queue_payload: dict[str, Any],
    source_pipeline_health_payload: dict[str, Any],
    generated_at: datetime,
    config: ResearchCandidateMonitoringSummaryConfig | None = None,
) -> ResearchCandidateMonitoringSummaryReport:
    """Build the monitoring summary from already-public, desensitized payloads."""

    inputs = (
        _input_from_public_payload(
            "snapshot_summary",
            candidate_snapshot_payload,
            status_key="public_status",
            input_count_key="snapshot_count",
            attention_key="max_screening_priority_score",
        ),
        _input_from_public_payload(
            "resolution_watch",
            resolution_watch_payload,
            status_key="status",
            input_count_key="item_count",
            attention_key="max_combined_watch_score",
        ),
        _input_from_public_payload(
            "alert_queue",
            alert_queue_payload,
            status_key="queue_status",
            input_count_key="input_count",
            attention_key="highest_priority_score",
        ),
        _input_from_public_payload(
            "pipeline_health",
            source_pipeline_health_payload,
            status_key="status",
            input_count_key="input_count",
            attention_key="attention_ratio",
        ),
    )
    return build_research_candidate_monitoring_summary(
        inputs,
        generated_at=generated_at,
        config=config,
    )


def research_candidate_monitoring_summary_payload(
    value: ResearchCandidateMonitoringSummaryReport | dict[str, Any],
) -> dict[str, Any]:
    if type(value) is ResearchCandidateMonitoringSummaryReport:
        _require_hard_flags("report", value)
        _reject_unsafe_public_payload("report", value)
        payload = _report_payload(value)
    elif type(value) is dict:
        payload = _copy_json_object(value)
    else:
        raise ValueError(
            "value must be a ResearchCandidateMonitoringSummaryReport or dict",
        )
    _reject_unsafe_public_payload("public payload", payload)
    _validate_public_payload(payload)
    return payload


def validate_research_candidate_monitoring_summary_public_payload(
    payload: dict[str, Any],
) -> bool:
    research_candidate_monitoring_summary_payload(payload)
    return True


def _row_from_input(
    item: ResearchCandidateMonitoringSummaryInput,
    *,
    index: int,
) -> ResearchCandidateMonitoringSummaryRow:
    return ResearchCandidateMonitoringSummaryRow(
        surface_ref=_redacted_surface_ref(index),
        monitoring_surface=item.monitoring_surface,
        surface_rank=_decimal_count(index),
        public_status=item.public_status,
        input_count=item.input_count,
        watch_count=item.watch_count,
        block_count=item.block_count,
        trigger_count=item.trigger_count,
        attention_score=item.attention_score,
        monitoring_priority_score=_monitoring_priority_score(
            item.public_status,
            item.attention_score,
        ),
        next_human_action=_NEXT_HUMAN_ACTION_BY_STATUS[item.public_status],
        reason_codes=(f"{item.monitoring_surface}_{item.public_status}",),
    )


def _input_from_public_payload(
    monitoring_surface: str,
    payload: dict[str, Any],
    *,
    status_key: str,
    input_count_key: str,
    attention_key: str,
) -> ResearchCandidateMonitoringSummaryInput:
    _reject_unsafe_public_payload(f"{monitoring_surface} payload", payload)
    if type(payload) is not dict:
        raise ValueError(f"{monitoring_surface} payload must be a dict")
    _require_hard_flags(f"{monitoring_surface} payload", _DictFlags(payload))
    public_status = _require_payload_status(status_key, payload.get(status_key))
    reason_codes = payload.get("reason_codes")
    if type(reason_codes) is not list:
        raise ValueError("reason_codes must be a list")
    return ResearchCandidateMonitoringSummaryInput(
        monitoring_surface=monitoring_surface,
        public_status=public_status,
        input_count=_require_decimal_string(input_count_key, payload.get(input_count_key)),
        watch_count=_require_decimal_string("watch_count", payload.get("watch_count")),
        block_count=_require_decimal_string("block_count", payload.get("block_count")),
        attention_score=_require_decimal_string(attention_key, payload.get(attention_key)),
        trigger_count=_decimal_count(len(reason_codes)),
    )


def _monitoring_priority_score(public_status: str, attention_score: Decimal) -> Decimal:
    if public_status == "block":
        return _clamp_ratio(Decimal("0.550000") + attention_score * Decimal("0.500000"))
    if public_status == "watch":
        return _clamp_ratio(Decimal("0.450000") + attention_score * Decimal("0.500000"))
    return _clamp_ratio(attention_score)


def _report_status(rows: tuple[ResearchCandidateMonitoringSummaryRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.public_status == "block" for row in rows):
        return "block"
    if any(row.public_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchCandidateMonitoringSummaryRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("monitoring_block_present", "monitoring_surface_missing")
    reason_codes: list[str] = []
    if any(row.public_status == "block" for row in rows):
        reason_codes.append("monitoring_block_present")
    if any(row.public_status == "watch" for row in rows):
        reason_codes.append("monitoring_watch_present")
    if all(row.public_status == "pass" for row in rows):
        reason_codes.append("monitoring_all_pass")
    row_reason_codes = {reason_code for row in rows for reason_code in row.reason_codes}
    for reason_code in _REPORT_REASON_CODE_SEQUENCE:
        if reason_code in row_reason_codes and reason_code not in reason_codes:
            reason_codes.append(reason_code)
    return _normalize_report_reason_codes(tuple(reason_codes))


def _normalize_inputs(
    inputs: tuple[ResearchCandidateMonitoringSummaryInput, ...]
    | list[ResearchCandidateMonitoringSummaryInput],
) -> tuple[ResearchCandidateMonitoringSummaryInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    normalized = tuple(inputs)
    seen: set[str] = set()
    for item in normalized:
        if type(item) is not ResearchCandidateMonitoringSummaryInput:
            raise ValueError("inputs must contain ResearchCandidateMonitoringSummaryInput")
        _require_hard_flags("input", item)
        if item.monitoring_surface in seen:
            raise ValueError("duplicate monitoring_surface values are not allowed")
        seen.add(item.monitoring_surface)
    if normalized and seen != set(_MONITORING_SURFACES):
        raise ValueError("required monitoring surfaces must be present")
    return normalized


def _normalize_rows(
    rows: tuple[ResearchCandidateMonitoringSummaryRow, ...],
) -> tuple[ResearchCandidateMonitoringSummaryRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen_surface_refs: set[str] = set()
    seen_surfaces: set[str] = set()
    for index, row in enumerate(normalized, start=1):
        if type(row) is not ResearchCandidateMonitoringSummaryRow:
            raise ValueError("rows must contain ResearchCandidateMonitoringSummaryRow")
        _require_hard_flags("row", row)
        if row.surface_ref in seen_surface_refs:
            raise ValueError("surface_ref values must be unique")
        if row.monitoring_surface in seen_surfaces:
            raise ValueError("monitoring_surface values must be unique")
        if row.surface_ref != _redacted_surface_ref(index):
            raise ValueError("surface_ref values must use deterministic redaction")
        if row.surface_rank != _decimal_count(index):
            raise ValueError("surface_rank must match deterministic row order")
        seen_surface_refs.add(row.surface_ref)
        seen_surfaces.add(row.monitoring_surface)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic monitoring ordering")
    return normalized


def _validate_input(item: ResearchCandidateMonitoringSummaryInput) -> None:
    if item.watch_count > item.input_count:
        raise ValueError("watch_count must not exceed input_count")
    if item.block_count > item.input_count:
        raise ValueError("block_count must not exceed input_count")
    if item.public_status == "pass" and (item.watch_count > _ZERO or item.block_count > _ZERO):
        raise ValueError("pass inputs must not contain watch or block counts")
    if item.public_status == "watch" and item.block_count > _ZERO:
        raise ValueError("watch inputs must not contain block counts")


def _validate_row(row: ResearchCandidateMonitoringSummaryRow) -> None:
    if row.watch_count > row.input_count:
        raise ValueError("watch_count must not exceed input_count")
    if row.block_count > row.input_count:
        raise ValueError("block_count must not exceed input_count")
    if row.monitoring_priority_score != _monitoring_priority_score(
        row.public_status,
        row.attention_score,
    ):
        raise ValueError("monitoring_priority_score must match row fields")
    if row.next_human_action != _NEXT_HUMAN_ACTION_BY_STATUS[row.public_status]:
        raise ValueError("next_human_action must match public_status")
    expected_reason_codes = (f"{row.monitoring_surface}_{row.public_status}",)
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match monitoring_surface and public_status")


def _validate_report(report: ResearchCandidateMonitoringSummaryReport) -> None:
    rows = report.rows
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.surface_count != _decimal_count(len(rows)):
        raise ValueError("surface_count must match rows")
    if report.pass_surface_count != _decimal_count(_status_count(rows, "pass")):
        raise ValueError("pass_surface_count must match rows")
    if report.watch_surface_count != _decimal_count(_status_count(rows, "watch")):
        raise ValueError("watch_surface_count must match rows")
    if report.block_surface_count != _decimal_count(_status_count(rows, "block")):
        raise ValueError("block_surface_count must match rows")
    if report.total_input_count != _sum_decimal(row.input_count for row in rows):
        raise ValueError("total_input_count must match rows")
    if report.total_watch_count != _sum_decimal(row.watch_count for row in rows):
        raise ValueError("total_watch_count must match rows")
    if report.total_block_count != _sum_decimal(row.block_count for row in rows):
        raise ValueError("total_block_count must match rows")
    if report.total_trigger_count != _sum_decimal(row.trigger_count for row in rows):
        raise ValueError("total_trigger_count must match rows")
    if report.max_attention_score != max(
        (row.attention_score for row in rows),
        default=_ZERO,
    ):
        raise ValueError("max_attention_score must match rows")
    if report.average_attention_score != _average_ratio(
        tuple(row.attention_score for row in rows),
    ):
        raise ValueError("average_attention_score must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _input_sort_key(
    item: ResearchCandidateMonitoringSummaryInput,
) -> tuple[Decimal, Decimal, Decimal]:
    return (
        _STATUS_WEIGHT[item.public_status],
        -_monitoring_priority_score(item.public_status, item.attention_score),
        _SURFACE_ORDER[item.monitoring_surface],
    )


def _row_sort_key(
    row: ResearchCandidateMonitoringSummaryRow,
) -> tuple[Decimal, Decimal, Decimal]:
    return (
        _STATUS_WEIGHT[row.public_status],
        -row.monitoring_priority_score,
        _SURFACE_ORDER[row.monitoring_surface],
    )


def _status_count(
    rows: tuple[ResearchCandidateMonitoringSummaryRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.public_status == status)


def _sum_decimal(values: Any) -> Decimal:
    return _quantize(sum(values, _ZERO))


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _quantize(Decimal(value))


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _clamp_ratio(sum(values, _ZERO) / _decimal_count(len(values)))


def _clamp_ratio(value: Decimal) -> Decimal:
    return min(max(_quantize(value), _ZERO), _ONE)


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext() as context:
            context.rounding = ROUND_HALF_UP
            return value.quantize(_QUANT)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must be quantizable") from exc


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(label: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public detail")


def _require_surface_ref(field_name: str, value: object) -> None:
    if type(value) is not str or _REDACTED_SURFACE_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a redacted monitoring surface reference")


def _require_monitoring_surface(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _MONITORING_SURFACES:
        raise ValueError(f"{field_name} must be a supported monitoring surface")


def _require_public_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _PUBLIC_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_next_human_action(field_name: str, value: object) -> None:
    if type(value) is not str or value not in set(_NEXT_HUMAN_ACTION_BY_STATUS.values()):
        raise ValueError(f"{field_name} must be a supported human monitoring action")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must use six decimal places")
    return _quantize(value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO or decimal_value > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return decimal_value


def _require_decimal_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must use Decimal-derived string values")
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must use Decimal-derived string values") from exc
    return _require_decimal(field_name, decimal_value)


def _require_payload_status(field_name: str, value: object) -> str:
    _require_public_status(field_name, value)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    normalized = tuple(reason_codes)
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    for reason_code in normalized:
        if type(reason_code) is not str or reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_codes must contain known values")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    expected = tuple(
        reason_code for reason_code in _REASON_CODE_SEQUENCE if reason_code in normalized
    )
    if normalized != expected:
        raise ValueError("reason_codes must use canonical ordering")
    return normalized


def _normalize_report_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    normalized = tuple(reason_codes)
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    for reason_code in normalized:
        if type(reason_code) is not str or reason_code not in _REPORT_REASON_CODE_SEQUENCE:
            raise ValueError("reason_codes must contain known report values")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    expected = tuple(
        reason_code
        for reason_code in _REPORT_REASON_CODE_SEQUENCE
        if reason_code in normalized
    )
    if normalized != expected:
        raise ValueError("reason_codes must use canonical ordering")
    return normalized


def _report_digest(report: ResearchCandidateMonitoringSummaryReport) -> str:
    payload = _report_payload(report)
    payload.pop("derived_validation_digest", None)
    return _digest_payload(payload)


def _digest_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _report_payload(report: ResearchCandidateMonitoringSummaryReport) -> dict[str, Any]:
    return {
        "generated_at": _json_ready(report.generated_at),
        "config_version": report.config_version,
        "status": report.status,
        "surface_count": _json_ready(report.surface_count),
        "pass_surface_count": _json_ready(report.pass_surface_count),
        "watch_surface_count": _json_ready(report.watch_surface_count),
        "block_surface_count": _json_ready(report.block_surface_count),
        "total_input_count": _json_ready(report.total_input_count),
        "total_watch_count": _json_ready(report.total_watch_count),
        "total_block_count": _json_ready(report.total_block_count),
        "total_trigger_count": _json_ready(report.total_trigger_count),
        "max_attention_score": _json_ready(report.max_attention_score),
        "average_attention_score": _json_ready(report.average_attention_score),
        "reason_codes": _json_ready(report.reason_codes),
        "rows": [_row_payload(row) for row in report.rows],
        "derived_validation_digest": report.derived_validation_digest,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _row_payload(row: ResearchCandidateMonitoringSummaryRow) -> dict[str, Any]:
    return {
        "surface_ref": row.surface_ref,
        "monitoring_surface": row.monitoring_surface,
        "surface_rank": _json_ready(row.surface_rank),
        "public_status": row.public_status,
        "input_count": _json_ready(row.input_count),
        "watch_count": _json_ready(row.watch_count),
        "block_count": _json_ready(row.block_count),
        "trigger_count": _json_ready(row.trigger_count),
        "attention_score": _json_ready(row.attention_score),
        "monitoring_priority_score": _json_ready(row.monitoring_priority_score),
        "next_human_action": row.next_human_action,
        "reason_codes": _json_ready(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


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
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("JSON value must use Decimal-derived strings")
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _copy_json_object(value: dict[str, Any]) -> dict[str, Any]:
    copied = _json_ready(value)
    if type(copied) is not dict:
        raise ValueError("public payload must be a JSON object")
    return copied


def _validate_public_payload(payload: dict[str, Any]) -> None:
    if tuple(payload.keys()) != _REPORT_PAYLOAD_KEYS:
        if set(payload.keys()) != set(_REPORT_PAYLOAD_KEYS):
            raise ValueError("public payload must use the monitoring summary schema")
    for field_name in ("generated_at", "config_version"):
        if type(payload[field_name]) is not str:
            raise ValueError(f"{field_name} must be a string")
    if payload["config_version"] != DEFAULT_RESEARCH_CANDIDATE_MONITORING_SUMMARY_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")
    _require_public_status("status", payload["status"])
    for field_name in (
        "surface_count",
        "pass_surface_count",
        "watch_surface_count",
        "block_surface_count",
        "total_input_count",
        "total_watch_count",
        "total_block_count",
        "total_trigger_count",
        "max_attention_score",
        "average_attention_score",
    ):
        _require_decimal_string(field_name, payload[field_name])
    _normalize_report_reason_codes_from_payload("reason_codes", payload["reason_codes"])
    if type(payload["rows"]) is not list:
        raise ValueError("rows must be a list")
    for row in payload["rows"]:
        _validate_public_row_payload(row)
    _require_digest("derived_validation_digest", payload["derived_validation_digest"])
    _require_hard_flags("public payload", _DictFlags(payload))
    payload_without_digest = dict(payload)
    payload_without_digest.pop("derived_validation_digest", None)
    if payload["derived_validation_digest"] != _digest_payload(payload_without_digest):
        raise ValueError("derived_validation_digest must match public payload")


def _validate_public_row_payload(value: object) -> None:
    if type(value) is not dict:
        raise ValueError("rows must contain JSON objects")
    if tuple(value.keys()) != _ROW_PAYLOAD_KEYS:
        if set(value.keys()) != set(_ROW_PAYLOAD_KEYS):
            raise ValueError("row payload must use the monitoring summary schema")
    _require_surface_ref("surface_ref", value["surface_ref"])
    _require_monitoring_surface("monitoring_surface", value["monitoring_surface"])
    _require_public_status("public_status", value["public_status"])
    for field_name in (
        "surface_rank",
        "input_count",
        "watch_count",
        "block_count",
        "trigger_count",
        "attention_score",
        "monitoring_priority_score",
    ):
        _require_decimal_string(field_name, value[field_name])
    _require_next_human_action("next_human_action", value["next_human_action"])
    _normalize_reason_codes_from_payload("reason_codes", value["reason_codes"])
    _require_hard_flags("row payload", _DictFlags(value))


def _normalize_reason_codes_from_payload(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return _normalize_reason_codes(tuple(value))


def _normalize_report_reason_codes_from_payload(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return _normalize_report_reason_codes(tuple(value))


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


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"unsafe public value in {label}")
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public key in {label}")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public key in {label}")
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.casefold()
    return any(fragment in normalized for fragment in _UNSAFE_PUBLIC_FRAGMENTS)


def _redacted_surface_ref(index: int) -> str:
    if type(index) is not int or index < 1:
        raise ValueError("surface index must be a positive int")
    return f"redacted-monitoring-surface-{index:06d}"
