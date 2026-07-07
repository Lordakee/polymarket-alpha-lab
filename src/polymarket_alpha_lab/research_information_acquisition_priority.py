"""Pure report-only research information acquisition priority policy."""

from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Sequence


DEFAULT_RESEARCH_INFORMATION_ACQUISITION_PRIORITY_CONFIG_VERSION = (
    "research-information-acquisition-priority-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_EVIDENCE_GAP_WEIGHT = Decimal("0.350000")
_FRESHNESS_WEIGHT = Decimal("0.250000")
_RELIABILITY_WEIGHT = Decimal("0.200000")
_EVENT_TIMELINE_WEIGHT = Decimal("0.120000")
_TEAM_SLA_WEIGHT = Decimal("0.080000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"

STATUSES = ("pass", "watch", "block")
_HARD_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_STATUS_SORT_WEIGHT = {"block": 0, "watch": 1, "pass": 2}
_ACQUISITION_PLAN_BY_STATUS = {
    "pass": "report_only_standard_monitoring",
    "watch": "report_only_prioritized_collection",
    "block": "report_only_hold_until_collection_plan",
}
_ROW_PRIORITY_BY_STATUS = {
    "pass": "defer_collection",
    "watch": "prioritize_collection",
    "block": "collect_before_research_use",
}
_REASON_CODE_SEQUENCE = (
    "information_acquisition_no_inputs",
    "information_acquisition_status_pass",
    "information_acquisition_status_watch",
    "information_acquisition_status_block",
    "evidence_gap_priority",
    "source_stale_priority",
    "source_reliability_low",
    "event_timeline_compressed",
    "team_sla_compressed",
)
_DETAIL_REASON_CODES = _REASON_CODE_SEQUENCE[4:]
_UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "market_id",
    "market-id",
    "market id",
    "market_slug",
    "market-slug",
    "market slug",
    "market",
    "slug",
    "question",
    "source_ref",
    "source-ref",
    "source ref",
    "source_url",
    "source-url",
    "source url",
    "source_text",
    "source-text",
    "source text",
    "http://",
    "https://",
    "://",
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
    "recommend",
    "recommendation",
)

__all__ = (
    "DEFAULT_RESEARCH_INFORMATION_ACQUISITION_PRIORITY_CONFIG_VERSION",
    "ResearchInformationAcquisitionPriorityConfig",
    "ResearchInformationAcquisitionPriorityInput",
    "ResearchInformationAcquisitionPriorityReport",
    "ResearchInformationAcquisitionPriorityRow",
    "STATUSES",
    "build_research_information_acquisition_priority_report",
    "research_information_acquisition_priority_payload",
)


@dataclass(frozen=True)
class ResearchInformationAcquisitionPriorityConfig:
    config_version: str = DEFAULT_RESEARCH_INFORMATION_ACQUISITION_PRIORITY_CONFIG_VERSION
    watch_priority_score: Decimal = Decimal("0.250000")
    block_priority_score: Decimal = Decimal("0.700000")
    source_freshness_sla_hours: Decimal = Decimal("24.000000")
    event_urgency_window_hours: Decimal = Decimal("48.000000")
    standard_team_sla_hours: Decimal = Decimal("24.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchInformationAcquisitionPriorityConfig:
            raise TypeError(
                "ResearchInformationAcquisitionPriorityConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchInformationAcquisitionPriorityConfig:
            raise ValueError(
                "config must be exactly ResearchInformationAcquisitionPriorityConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_INFORMATION_ACQUISITION_PRIORITY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("watch_priority_score", "block_priority_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_freshness_sla_hours",
            "event_urgency_window_hours",
            "standard_team_sla_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_priority_score >= self.block_priority_score:
            raise ValueError("watch_priority_score must be below block_priority_score")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchInformationAcquisitionPriorityInput:
    research_item_ref: str
    evidence_gap_score: Decimal
    source_age_hours: Decimal
    source_reliability_score: Decimal
    event_starts_in_hours: Decimal
    team_sla_hours: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchInformationAcquisitionPriorityInput:
            raise TypeError(
                "ResearchInformationAcquisitionPriorityInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchInformationAcquisitionPriorityInput:
            raise ValueError(
                "input must be exactly ResearchInformationAcquisitionPriorityInput",
            )
        _require_public_identifier("research_item_ref", self.research_item_ref)
        _reject_unsafe_public_text("research_item_ref", self.research_item_ref)
        for field_name in ("evidence_gap_score", "source_reliability_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("source_age_hours", "event_starts_in_hours"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "team_sla_hours",
            _require_positive_decimal("team_sla_hours", self.team_sla_hours),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchInformationAcquisitionPriorityRow:
    acquisition_slot_ref: str
    priority_rank: Decimal
    priority_score: Decimal
    evidence_gap_score: Decimal
    source_freshness_score: Decimal
    source_reliability_gap_score: Decimal
    event_timeline_pressure_score: Decimal
    team_sla_pressure_score: Decimal
    source_age_hours: Decimal
    source_reliability_score: Decimal
    event_starts_in_hours: Decimal
    team_sla_hours: Decimal
    status: str
    acquisition_priority: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchInformationAcquisitionPriorityRow:
            raise TypeError(
                "ResearchInformationAcquisitionPriorityRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchInformationAcquisitionPriorityRow:
            raise ValueError("row must be exactly ResearchInformationAcquisitionPriorityRow")
        _require_slot_ref(self.acquisition_slot_ref)
        object.__setattr__(
            self,
            "priority_rank",
            _require_positive_count_decimal("priority_rank", self.priority_rank),
        )
        for field_name in (
            "priority_score",
            "evidence_gap_score",
            "source_freshness_score",
            "source_reliability_gap_score",
            "event_timeline_pressure_score",
            "team_sla_pressure_score",
            "source_reliability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("source_age_hours", "event_starts_in_hours"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "team_sla_hours",
            _require_positive_decimal("team_sla_hours", self.team_sla_hours),
        )
        _require_status("status", self.status)
        _require_choice(
            "acquisition_priority",
            self.acquisition_priority,
            tuple(_ROW_PRIORITY_BY_STATUS.values()),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchInformationAcquisitionPriorityReport:
    config_version: str
    status: str
    acquisition_plan: str
    item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    evidence_gap_priority_count: Decimal
    source_stale_priority_count: Decimal
    source_reliability_low_count: Decimal
    event_timeline_compressed_count: Decimal
    team_sla_compressed_count: Decimal
    highest_priority_score: Decimal
    rows: tuple[ResearchInformationAcquisitionPriorityRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchInformationAcquisitionPriorityReport:
            raise TypeError(
                "ResearchInformationAcquisitionPriorityReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchInformationAcquisitionPriorityReport:
            raise ValueError(
                "report must be exactly ResearchInformationAcquisitionPriorityReport",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_INFORMATION_ACQUISITION_PRIORITY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        _require_choice(
            "acquisition_plan",
            self.acquisition_plan,
            tuple(_ACQUISITION_PLAN_BY_STATUS.values()),
        )
        for field_name in (
            "item_count",
            "pass_count",
            "watch_count",
            "block_count",
            "evidence_gap_priority_count",
            "source_stale_priority_count",
            "source_reliability_low_count",
            "event_timeline_compressed_count",
            "team_sla_compressed_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "highest_priority_score",
            _require_ratio_decimal("highest_priority_score", self.highest_priority_score),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, _DERIVED_VALIDATION_DIGEST_FIELD, expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest mismatch")
        _require_digest(_DERIVED_VALIDATION_DIGEST_FIELD, self.derived_validation_digest)

    @property
    def payload(self) -> dict[str, object]:
        return research_information_acquisition_priority_payload(self)


def build_research_information_acquisition_priority_report(
    inputs: Sequence[ResearchInformationAcquisitionPriorityInput],
    *,
    config: ResearchInformationAcquisitionPriorityConfig | None = None,
) -> ResearchInformationAcquisitionPriorityReport:
    """Build a deterministic paper-only information acquisition priority report."""

    if config is None:
        config = ResearchInformationAcquisitionPriorityConfig()
    if type(config) is not ResearchInformationAcquisitionPriorityConfig:
        raise ValueError(
            "config must be exactly ResearchInformationAcquisitionPriorityConfig",
        )
    _require_hard_flags("config", config)
    normalized_inputs = _normalize_inputs(inputs)
    unranked_rows = tuple(
        (item.research_item_ref, _unranked_row(item, config=config))
        for item in normalized_inputs
    )
    ranked_rows = tuple(
        _ranked_row(row, rank=index + 1)
        for index, (_item_ref, row) in enumerate(
            sorted(unranked_rows, key=_unranked_sort_key),
        )
    )
    status = _report_status(ranked_rows)
    values: dict[str, object] = {
        "config_version": config.config_version,
        "status": status,
        "acquisition_plan": _ACQUISITION_PLAN_BY_STATUS[status],
        "item_count": _decimal_count(len(ranked_rows)),
        "pass_count": _status_count(ranked_rows, "pass"),
        "watch_count": _status_count(ranked_rows, "watch"),
        "block_count": _status_count(ranked_rows, "block"),
        "evidence_gap_priority_count": _reason_count(
            ranked_rows,
            "evidence_gap_priority",
        ),
        "source_stale_priority_count": _reason_count(
            ranked_rows,
            "source_stale_priority",
        ),
        "source_reliability_low_count": _reason_count(
            ranked_rows,
            "source_reliability_low",
        ),
        "event_timeline_compressed_count": _reason_count(
            ranked_rows,
            "event_timeline_compressed",
        ),
        "team_sla_compressed_count": _reason_count(
            ranked_rows,
            "team_sla_compressed",
        ),
        "highest_priority_score": _highest_priority_score(ranked_rows),
        "rows": ranked_rows,
        "reason_codes": _report_reason_codes(ranked_rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchInformationAcquisitionPriorityReport(**values)


def research_information_acquisition_priority_payload(
    report: ResearchInformationAcquisitionPriorityReport | dict[str, object],
) -> dict[str, object]:
    if type(report) is ResearchInformationAcquisitionPriorityReport:
        _require_hard_flags("report", report)
        _validate_report(report)
        payload = _report_public_payload_values(report)
        payload[_DERIVED_VALIDATION_DIGEST_FIELD] = report.derived_validation_digest
    elif type(report) is dict:
        payload = _copy_json_object(report)
    else:
        raise ValueError(
            "report must be a ResearchInformationAcquisitionPriorityReport or dict",
        )
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_public_payload_digest(payload)
    return payload


def _unranked_row(
    item: ResearchInformationAcquisitionPriorityInput,
    *,
    config: ResearchInformationAcquisitionPriorityConfig,
) -> ResearchInformationAcquisitionPriorityRow:
    source_freshness_score = _source_freshness_score(item.source_age_hours, config)
    source_reliability_gap_score = _quantize(_ONE - item.source_reliability_score)
    event_timeline_pressure_score = _event_timeline_pressure_score(
        item.event_starts_in_hours,
        config,
    )
    team_sla_pressure_score = _team_sla_pressure_score(item.team_sla_hours, config)
    priority_score = _priority_score(
        evidence_gap_score=item.evidence_gap_score,
        source_freshness_score=source_freshness_score,
        source_reliability_gap_score=source_reliability_gap_score,
        event_timeline_pressure_score=event_timeline_pressure_score,
        team_sla_pressure_score=team_sla_pressure_score,
    )
    status = _row_status(priority_score, config)
    return ResearchInformationAcquisitionPriorityRow(
        acquisition_slot_ref="acquisition-slot-000001",
        priority_rank=_ONE,
        priority_score=priority_score,
        evidence_gap_score=item.evidence_gap_score,
        source_freshness_score=source_freshness_score,
        source_reliability_gap_score=source_reliability_gap_score,
        event_timeline_pressure_score=event_timeline_pressure_score,
        team_sla_pressure_score=team_sla_pressure_score,
        source_age_hours=item.source_age_hours,
        source_reliability_score=item.source_reliability_score,
        event_starts_in_hours=item.event_starts_in_hours,
        team_sla_hours=item.team_sla_hours,
        status=status,
        acquisition_priority=_ROW_PRIORITY_BY_STATUS[status],
        reason_codes=_row_reason_codes(
            status=status,
            evidence_gap_score=item.evidence_gap_score,
            source_freshness_score=source_freshness_score,
            source_reliability_gap_score=source_reliability_gap_score,
            event_timeline_pressure_score=event_timeline_pressure_score,
            team_sla_pressure_score=team_sla_pressure_score,
        ),
    )


def _ranked_row(
    row: ResearchInformationAcquisitionPriorityRow,
    *,
    rank: int,
) -> ResearchInformationAcquisitionPriorityRow:
    return replace(
        row,
        acquisition_slot_ref=f"acquisition-slot-{rank:06d}",
        priority_rank=_decimal_count(rank),
    )


def _unranked_sort_key(
    item: tuple[str, ResearchInformationAcquisitionPriorityRow],
) -> tuple[int, Decimal, str]:
    research_item_ref, row = item
    return (_STATUS_SORT_WEIGHT[row.status], -row.priority_score, research_item_ref)


def _source_freshness_score(
    source_age_hours: Decimal,
    config: ResearchInformationAcquisitionPriorityConfig,
) -> Decimal:
    if source_age_hours <= config.source_freshness_sla_hours:
        return _ZERO
    return _clamp_ratio(
        (source_age_hours - config.source_freshness_sla_hours)
        / config.source_freshness_sla_hours,
    )


def _event_timeline_pressure_score(
    event_starts_in_hours: Decimal,
    config: ResearchInformationAcquisitionPriorityConfig,
) -> Decimal:
    if event_starts_in_hours >= config.event_urgency_window_hours:
        return _ZERO
    return _clamp_ratio(
        (config.event_urgency_window_hours - event_starts_in_hours)
        / config.event_urgency_window_hours,
    )


def _team_sla_pressure_score(
    team_sla_hours: Decimal,
    config: ResearchInformationAcquisitionPriorityConfig,
) -> Decimal:
    if team_sla_hours >= config.standard_team_sla_hours:
        return _ZERO
    return _clamp_ratio(
        (config.standard_team_sla_hours - team_sla_hours)
        / config.standard_team_sla_hours,
    )


def _priority_score(
    *,
    evidence_gap_score: Decimal,
    source_freshness_score: Decimal,
    source_reliability_gap_score: Decimal,
    event_timeline_pressure_score: Decimal,
    team_sla_pressure_score: Decimal,
) -> Decimal:
    return _clamp_ratio(
        evidence_gap_score * _EVIDENCE_GAP_WEIGHT
        + source_freshness_score * _FRESHNESS_WEIGHT
        + source_reliability_gap_score * _RELIABILITY_WEIGHT
        + event_timeline_pressure_score * _EVENT_TIMELINE_WEIGHT
        + team_sla_pressure_score * _TEAM_SLA_WEIGHT,
    )


def _row_status(
    priority_score: Decimal,
    config: ResearchInformationAcquisitionPriorityConfig,
) -> str:
    if priority_score >= config.block_priority_score:
        return "block"
    if priority_score >= config.watch_priority_score:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    evidence_gap_score: Decimal,
    source_freshness_score: Decimal,
    source_reliability_gap_score: Decimal,
    event_timeline_pressure_score: Decimal,
    team_sla_pressure_score: Decimal,
) -> tuple[str, ...]:
    codes = [f"information_acquisition_status_{status}"]
    if status == "pass":
        return tuple(codes)
    if evidence_gap_score > _ZERO:
        codes.append("evidence_gap_priority")
    if source_freshness_score > _ZERO:
        codes.append("source_stale_priority")
    if source_reliability_gap_score > _ZERO:
        codes.append("source_reliability_low")
    if event_timeline_pressure_score > _ZERO:
        codes.append("event_timeline_compressed")
    if team_sla_pressure_score > _ZERO:
        codes.append("team_sla_compressed")
    return tuple(code for code in _REASON_CODE_SEQUENCE if code in codes)


def _report_status(
    rows: tuple[ResearchInformationAcquisitionPriorityRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchInformationAcquisitionPriorityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("information_acquisition_no_inputs",)
    row_codes = {reason_code for row in rows for reason_code in row.reason_codes}
    return tuple(code for code in _REASON_CODE_SEQUENCE if code in row_codes)


def _status_count(
    rows: tuple[ResearchInformationAcquisitionPriorityRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchInformationAcquisitionPriorityRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _highest_priority_score(
    rows: tuple[ResearchInformationAcquisitionPriorityRow, ...],
) -> Decimal:
    return max((row.priority_score for row in rows), default=_ZERO)


def _validate_row(row: ResearchInformationAcquisitionPriorityRow) -> None:
    if row.acquisition_priority != _ROW_PRIORITY_BY_STATUS[row.status]:
        raise ValueError("acquisition_priority must match status")
    expected_priority_score = _priority_score(
        evidence_gap_score=row.evidence_gap_score,
        source_freshness_score=row.source_freshness_score,
        source_reliability_gap_score=row.source_reliability_gap_score,
        event_timeline_pressure_score=row.event_timeline_pressure_score,
        team_sla_pressure_score=row.team_sla_pressure_score,
    )
    if row.priority_score != expected_priority_score:
        raise ValueError("priority_score must match acquisition priority drivers")
    expected_reason_codes = _row_reason_codes(
        status=row.status,
        evidence_gap_score=row.evidence_gap_score,
        source_freshness_score=row.source_freshness_score,
        source_reliability_gap_score=row.source_reliability_gap_score,
        event_timeline_pressure_score=row.event_timeline_pressure_score,
        team_sla_pressure_score=row.team_sla_pressure_score,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match acquisition priority drivers")
    detail_codes = tuple(code for code in row.reason_codes if code in _DETAIL_REASON_CODES)
    if row.status == "pass" and detail_codes:
        raise ValueError("pass rows must not include priority detail reason codes")
    if row.status != "pass" and not detail_codes:
        raise ValueError("non-pass rows must include priority detail reason codes")


def _validate_report(report: ResearchInformationAcquisitionPriorityReport) -> None:
    for row in report.rows:
        _validate_row(row)
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.acquisition_plan != _ACQUISITION_PLAN_BY_STATUS[report.status]:
        raise ValueError("acquisition_plan must match status")
    if report.item_count != _decimal_count(len(report.rows)):
        raise ValueError("item_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    for field_name, reason_code in (
        ("evidence_gap_priority_count", "evidence_gap_priority"),
        ("source_stale_priority_count", "source_stale_priority"),
        ("source_reliability_low_count", "source_reliability_low"),
        ("event_timeline_compressed_count", "event_timeline_compressed"),
        ("team_sla_compressed_count", "team_sla_compressed"),
    ):
        if getattr(report, field_name) != _reason_count(report.rows, reason_code):
            raise ValueError(f"{field_name} must match rows")
    if report.highest_priority_score != _highest_priority_score(report.rows):
        raise ValueError("highest_priority_score must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic acquisition priority ordering")


def _normalize_inputs(
    inputs: Sequence[ResearchInformationAcquisitionPriorityInput],
) -> tuple[ResearchInformationAcquisitionPriorityInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    normalized = tuple(inputs)
    for item in normalized:
        if type(item) is not ResearchInformationAcquisitionPriorityInput:
            raise ValueError(
                "inputs items must be ResearchInformationAcquisitionPriorityInput",
            )
        _require_hard_flags("input", item)
    refs = tuple(item.research_item_ref for item in normalized)
    if len(set(refs)) != len(refs):
        raise ValueError("research_item_ref values must be unique")
    return normalized


def _normalize_rows(
    rows: tuple[ResearchInformationAcquisitionPriorityRow, ...],
) -> tuple[ResearchInformationAcquisitionPriorityRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchInformationAcquisitionPriorityRow:
            raise ValueError("rows items must be ResearchInformationAcquisitionPriorityRow")
        _require_hard_flags("row", row)
    slot_refs = tuple(row.acquisition_slot_ref for row in normalized)
    if len(set(slot_refs)) != len(slot_refs):
        raise ValueError("acquisition_slot_ref values must be unique")
    ranks = tuple(row.priority_rank for row in normalized)
    if ranks != tuple(_decimal_count(index + 1) for index in range(len(normalized))):
        raise ValueError("priority_rank values must be sequential")
    return normalized


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    for reason_code in normalized:
        if type(reason_code) is not str or reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_codes must contain known reason codes")
    expected_order = tuple(code for code in _REASON_CODE_SEQUENCE if code in normalized)
    if normalized != expected_order:
        raise ValueError("reason_codes must use canonical ordering")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    return normalized


def _row_sort_key(
    row: ResearchInformationAcquisitionPriorityRow,
) -> tuple[int, Decimal, str]:
    return (_STATUS_SORT_WEIGHT[row.status], -row.priority_score, row.acquisition_slot_ref)


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_text(field_name, value)


def _require_slot_ref(value: object) -> None:
    if type(value) is not str:
        raise ValueError("acquisition_slot_ref must be a string")
    if not re.fullmatch(r"acquisition-slot-[0-9]{6}", value):
        raise ValueError("acquisition_slot_ref must be a generated slot reference")


def _require_status(field_name: str, value: object) -> None:
    _require_choice(field_name, value, STATUSES)


def _require_choice(field_name: str, value: object, choices: tuple[str, ...]) -> None:
    if type(value) is not str or value not in choices:
        raise ValueError(f"{field_name} must be one of {', '.join(choices)}")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in _HARD_FLAG_FIELDS:
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} {flag_name} must be True")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO or decimal_value > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return decimal_value


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_count_decimal(field_name, value)
    if decimal_value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _quantize(Decimal(value))


def _clamp_ratio(value: Decimal) -> Decimal:
    return min(max(_quantize(value), _ZERO), _ONE)


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext() as context:
            context.rounding = ROUND_HALF_UP
            return value.quantize(_QUANT)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must be quantizable") from exc


def _decimal_payload(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return format(_require_decimal("payload decimal", value), "f")


def _report_public_payload_values(
    report: ResearchInformationAcquisitionPriorityReport,
) -> dict[str, object]:
    values: dict[str, object] = {
        "config_version": report.config_version,
        "status": report.status,
        "acquisition_plan": report.acquisition_plan,
        "item_count": _decimal_payload(report.item_count),
        "pass_count": _decimal_payload(report.pass_count),
        "watch_count": _decimal_payload(report.watch_count),
        "block_count": _decimal_payload(report.block_count),
        "evidence_gap_priority_count": _decimal_payload(
            report.evidence_gap_priority_count,
        ),
        "source_stale_priority_count": _decimal_payload(
            report.source_stale_priority_count,
        ),
        "source_reliability_low_count": _decimal_payload(
            report.source_reliability_low_count,
        ),
        "event_timeline_compressed_count": _decimal_payload(
            report.event_timeline_compressed_count,
        ),
        "team_sla_compressed_count": _decimal_payload(
            report.team_sla_compressed_count,
        ),
        "highest_priority_score": _decimal_payload(report.highest_priority_score),
        "reason_codes": list(report.reason_codes),
        "acquisition_rows": [_row_payload(row) for row in report.rows],
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    _reject_unsafe_public_payload("report payload", values, allow_json_containers=True)
    return values


def _row_payload(row: ResearchInformationAcquisitionPriorityRow) -> dict[str, object]:
    payload: dict[str, object] = {
        "acquisition_slot_ref": row.acquisition_slot_ref,
        "priority_rank": _decimal_payload(row.priority_rank),
        "priority_score": _decimal_payload(row.priority_score),
        "evidence_gap_score": _decimal_payload(row.evidence_gap_score),
        "source_freshness_score": _decimal_payload(row.source_freshness_score),
        "source_reliability_gap_score": _decimal_payload(
            row.source_reliability_gap_score,
        ),
        "event_timeline_pressure_score": _decimal_payload(
            row.event_timeline_pressure_score,
        ),
        "team_sla_pressure_score": _decimal_payload(row.team_sla_pressure_score),
        "source_age_hours": _decimal_payload(row.source_age_hours),
        "source_reliability_score": _decimal_payload(row.source_reliability_score),
        "event_starts_in_hours": _decimal_payload(row.event_starts_in_hours),
        "team_sla_hours": _decimal_payload(row.team_sla_hours),
        "status": row.status,
        "acquisition_priority": row.acquisition_priority,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }
    _reject_unsafe_public_payload("row payload", payload, allow_json_containers=True)
    return payload


def _report_digest(report: ResearchInformationAcquisitionPriorityReport) -> str:
    return _report_digest_from_values(_report_public_payload_values(report))


def _report_digest_from_values(values: dict[str, object]) -> str:
    digest_payload = _digest_ready(values)
    return sha256(
        json.dumps(digest_payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()


def _digest_ready(value: object) -> object:
    if type(value) is Decimal:
        return _decimal_payload(value)
    if type(value) is ResearchInformationAcquisitionPriorityRow:
        return _row_payload(value)
    if type(value) is tuple:
        return [_digest_ready(item) for item in value]
    if type(value) is list:
        return [_digest_ready(item) for item in value]
    if type(value) is dict:
        return {
            key: _digest_ready(item)
            for key, item in sorted(value.items())
            if key != _DERIVED_VALIDATION_DIGEST_FIELD
        }
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("digest values must be public JSON primitives")


def _validate_public_payload_digest(payload: dict[str, object]) -> None:
    if payload.get("paper_only") is not True:
        raise ValueError("paper_only must be True for payload")
    if payload.get("report_only") is not True:
        raise ValueError("report_only must be True for payload")
    if payload.get("readonly") is not True:
        raise ValueError("readonly must be True for payload")
    expected_digest = _report_digest_from_values(payload)
    digest = payload.get(_DERIVED_VALIDATION_DIGEST_FIELD)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest mismatch")
    _require_digest(_DERIVED_VALIDATION_DIGEST_FIELD, digest)


def _copy_json_object(value: dict[str, object]) -> dict[str, object]:
    copied = json.loads(json.dumps(value, sort_keys=True))
    if type(copied) is not dict:
        raise ValueError("payload must be a JSON object")
    return copied


def _reject_unsafe_public_text(field_name: str, value: object) -> None:
    if type(value) is not str:
        return
    folded = value.casefold()
    if any(fragment in folded for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public detail")


def _reject_unsafe_public_payload(
    field_name: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if type(value) is str:
        _reject_unsafe_public_text(field_name, value)
        return
    if type(value) is tuple:
        for item in value:
            _reject_unsafe_public_payload(
                field_name,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if allow_json_containers and type(value) is list:
        for item in value:
            _reject_unsafe_public_payload(
                field_name,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if allow_json_containers and type(value) is dict:
        for key, item in value.items():
            _reject_unsafe_public_text(field_name, key)
            _reject_unsafe_public_payload(
                field_name,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if hasattr(value, "__dataclass_fields__"):
        for field_name_on_value in value.__dataclass_fields__:
            item = getattr(value, field_name_on_value)
            _reject_unsafe_public_payload(
                field_name,
                item,
                allow_json_containers=allow_json_containers,
            )
