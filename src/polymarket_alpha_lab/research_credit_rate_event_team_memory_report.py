"""Pure aggregate credit and rates event team memory report."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any


DEFAULT_RESEARCH_CREDIT_RATE_EVENT_TEAM_MEMORY_REPORT_CONFIG_VERSION = (
    "research-credit-rate-event-team-memory-report-v0"
)

STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0")
ONE = Decimal("1")
QUANT = Decimal("0.000001")
DIGEST_HEX_LENGTH = 64

ROW_REASON_CODES = (
    "credit_rate_event_team_memory_memory_readiness_block",
    "credit_rate_event_team_memory_policy_freshness_block",
    "credit_rate_event_team_memory_evidence_reuse_block",
    "credit_rate_event_team_memory_calibration_readiness_block",
    "credit_rate_event_team_memory_memory_readiness_watch",
    "credit_rate_event_team_memory_policy_freshness_watch",
    "credit_rate_event_team_memory_evidence_reuse_watch",
    "credit_rate_event_team_memory_calibration_readiness_watch",
    "credit_rate_event_team_memory_ready",
)
REPORT_REASON_CODES = (
    "credit_rate_event_team_memory_block_teams_present",
    "credit_rate_event_team_memory_watch_teams_present",
    "credit_rate_event_team_memory_ready",
    "credit_rate_event_team_memory_empty",
)
UNSAFE_PUBLIC_FRAGMENTS = (
    "acc" "ount",
    "au" "th",
    "b" "uy",
    "bro" "ker",
    "can" "cel",
    "cre" "dential",
    "data" "base",
    "env" "iron",
    "li" "ve",
    "market_slug",
    "net" "work",
    "or" "der",
    "post" "gres",
    "pri" "vate_key",
    "req" "uest",
    "se" "cret",
    "se" "ll",
    "soc" "ket",
    "source_key",
    "s" "qlite",
    "sub" "mit",
    "supa" "base",
    "team_id",
    "tr" "ade",
    "user_id",
    "wa" "llet",
)

__all__ = (
    "DEFAULT_RESEARCH_CREDIT_RATE_EVENT_TEAM_MEMORY_REPORT_CONFIG_VERSION",
    "STATUSES",
    "ResearchCreditRateEventTeamMemoryReportConfig",
    "ResearchCreditRateEventTeamMemoryInput",
    "ResearchCreditRateEventTeamMemoryRow",
    "ResearchCreditRateEventTeamMemoryReasonCodeCount",
    "ResearchCreditRateEventTeamMemoryReport",
    "build_research_credit_rate_event_team_memory_report",
    "research_credit_rate_event_team_memory_report_digest",
    "research_credit_rate_event_team_memory_report_payload",
)


@dataclass(frozen=True)
class ResearchCreditRateEventTeamMemoryReportConfig:
    config_version: str = (
        DEFAULT_RESEARCH_CREDIT_RATE_EVENT_TEAM_MEMORY_REPORT_CONFIG_VERSION
    )
    memory_readiness_watch_threshold: Decimal = Decimal("0.800000")
    memory_readiness_block_threshold: Decimal = Decimal("0.600000")
    policy_freshness_watch_threshold: Decimal = Decimal("0.850000")
    policy_freshness_block_threshold: Decimal = Decimal("0.600000")
    evidence_reuse_watch_threshold: Decimal = Decimal("0.750000")
    evidence_reuse_block_threshold: Decimal = Decimal("0.500000")
    calibration_readiness_watch_threshold: Decimal = Decimal("0.800000")
    calibration_readiness_block_threshold: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchCreditRateEventTeamMemoryReportConfig,
            "config",
        )
        _require_public_label("config_version", self.config_version)
        for field_name in (
            "memory_readiness_watch_threshold",
            "memory_readiness_block_threshold",
            "policy_freshness_watch_threshold",
            "policy_freshness_block_threshold",
            "evidence_reuse_watch_threshold",
            "evidence_reuse_block_threshold",
            "calibration_readiness_watch_threshold",
            "calibration_readiness_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_floor_ceiling(
            "memory_readiness_block_threshold",
            self.memory_readiness_block_threshold,
            "memory_readiness_watch_threshold",
            self.memory_readiness_watch_threshold,
        )
        _require_floor_ceiling(
            "policy_freshness_block_threshold",
            self.policy_freshness_block_threshold,
            "policy_freshness_watch_threshold",
            self.policy_freshness_watch_threshold,
        )
        _require_floor_ceiling(
            "evidence_reuse_block_threshold",
            self.evidence_reuse_block_threshold,
            "evidence_reuse_watch_threshold",
            self.evidence_reuse_watch_threshold,
        )
        _require_floor_ceiling(
            "calibration_readiness_block_threshold",
            self.calibration_readiness_block_threshold,
            "calibration_readiness_watch_threshold",
            self.calibration_readiness_watch_threshold,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchCreditRateEventTeamMemoryInput:
    team_label: str
    event_family_label: str
    memory_fresh_count: Decimal
    memory_total_count: Decimal
    policy_fresh_count: Decimal
    policy_reference_count: Decimal
    evidence_reuse_count: Decimal
    evidence_case_count: Decimal
    calibration_ready_count: Decimal
    calibration_target_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchCreditRateEventTeamMemoryInput, "input")
        _require_public_label("team_label", self.team_label)
        _require_public_label("event_family_label", self.event_family_label)
        for field_name in (
            "memory_fresh_count",
            "memory_total_count",
            "policy_fresh_count",
            "policy_reference_count",
            "evidence_reuse_count",
            "evidence_case_count",
            "calibration_ready_count",
            "calibration_target_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "memory_total_count",
            "policy_reference_count",
            "evidence_case_count",
            "calibration_target_count",
        ):
            _require_positive_decimal(field_name, getattr(self, field_name))
        _validate_count_bounds(self)
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchCreditRateEventTeamMemoryRow:
    team_label: str
    event_family_label: str
    memory_fresh_count: Decimal
    memory_total_count: Decimal
    memory_readiness_ratio: Decimal
    policy_fresh_count: Decimal
    policy_reference_count: Decimal
    policy_freshness_ratio: Decimal
    evidence_reuse_count: Decimal
    evidence_case_count: Decimal
    evidence_reuse_ratio: Decimal
    calibration_ready_count: Decimal
    calibration_target_count: Decimal
    calibration_readiness_ratio: Decimal
    readiness_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchCreditRateEventTeamMemoryRow, "row")
        _require_public_label("team_label", self.team_label)
        _require_public_label("event_family_label", self.event_family_label)
        for field_name in (
            "memory_fresh_count",
            "memory_total_count",
            "policy_fresh_count",
            "policy_reference_count",
            "evidence_reuse_count",
            "evidence_case_count",
            "calibration_ready_count",
            "calibration_target_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "memory_total_count",
            "policy_reference_count",
            "evidence_case_count",
            "calibration_target_count",
        ):
            _require_positive_decimal(field_name, getattr(self, field_name))
        for field_name in (
            "memory_readiness_ratio",
            "policy_freshness_ratio",
            "evidence_reuse_ratio",
            "calibration_readiness_ratio",
            "readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, ROW_REASON_CODES),
        )
        _validate_count_bounds(self)
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchCreditRateEventTeamMemoryReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchCreditRateEventTeamMemoryReasonCodeCount,
            "reason_code_count",
        )
        _require_public_label("reason_code", self.reason_code)
        if self.reason_code not in ROW_REASON_CODES:
            raise ValueError("reason_code must be known")
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchCreditRateEventTeamMemoryReport:
    generated_at: datetime
    config_version: str
    status: str
    team_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_readiness_score: Decimal
    lowest_memory_readiness_ratio: Decimal
    lowest_policy_freshness_ratio: Decimal
    lowest_evidence_reuse_ratio: Decimal
    lowest_calibration_readiness_ratio: Decimal
    rows: tuple[ResearchCreditRateEventTeamMemoryRow, ...]
    reason_code_counts: tuple[ResearchCreditRateEventTeamMemoryReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchCreditRateEventTeamMemoryReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "team_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_readiness_score",
            "lowest_memory_readiness_ratio",
            "lowest_policy_freshness_ratio",
            "lowest_evidence_reuse_ratio",
            "lowest_calibration_readiness_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
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
            _normalize_reason_codes(self.reason_codes, REPORT_REASON_CODES),
        )
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest:
            _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_credit_rate_event_team_memory_report_payload(self)


def build_research_credit_rate_event_team_memory_report(
    inputs: list[ResearchCreditRateEventTeamMemoryInput]
    | tuple[ResearchCreditRateEventTeamMemoryInput, ...],
    *,
    config: ResearchCreditRateEventTeamMemoryReportConfig,
    generated_at: datetime,
) -> ResearchCreditRateEventTeamMemoryReport:
    if type(config) is not ResearchCreditRateEventTeamMemoryReportConfig:
        raise ValueError("config must be a ResearchCreditRateEventTeamMemoryReportConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(_row_for_input(item, config) for item in normalized_inputs)
    reason_codes = _report_reason_codes(rows)
    return ResearchCreditRateEventTeamMemoryReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_status_from_report_reason_codes(reason_codes),
        team_count=_decimal_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        average_readiness_score=_average(rows, "readiness_score"),
        lowest_memory_readiness_ratio=_minimum(rows, "memory_readiness_ratio"),
        lowest_policy_freshness_ratio=_minimum(rows, "policy_freshness_ratio"),
        lowest_evidence_reuse_ratio=_minimum(rows, "evidence_reuse_ratio"),
        lowest_calibration_readiness_ratio=_minimum(
            rows,
            "calibration_readiness_ratio",
        ),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows),
        reason_codes=reason_codes,
    )


def research_credit_rate_event_team_memory_report_payload(
    value: ResearchCreditRateEventTeamMemoryReport | dict[str, Any],
) -> dict[str, Any]:
    if type(value) is ResearchCreditRateEventTeamMemoryReport:
        _require_hard_flags("report", value)
        _reject_unsafe_public_payload("report", value)
        payload = _json_ready(asdict(value))
    elif type(value) is dict:
        payload = _json_ready(value)
    else:
        raise ValueError(
            "value must be a ResearchCreditRateEventTeamMemoryReport or JSON object",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    _reject_public_numeric_values(payload)
    _validate_payload_digest(payload)
    return payload


def research_credit_rate_event_team_memory_report_digest(
    report: ResearchCreditRateEventTeamMemoryReport,
) -> str:
    if type(report) is not ResearchCreditRateEventTeamMemoryReport:
        raise ValueError("report must be a ResearchCreditRateEventTeamMemoryReport")
    return report.derived_validation_digest


def _row_for_input(
    item: ResearchCreditRateEventTeamMemoryInput,
    config: ResearchCreditRateEventTeamMemoryReportConfig,
) -> ResearchCreditRateEventTeamMemoryRow:
    memory_readiness_ratio = _ratio(item.memory_fresh_count, item.memory_total_count)
    policy_freshness_ratio = _ratio(item.policy_fresh_count, item.policy_reference_count)
    evidence_reuse_ratio = _ratio(item.evidence_reuse_count, item.evidence_case_count)
    calibration_readiness_ratio = _ratio(
        item.calibration_ready_count,
        item.calibration_target_count,
    )
    readiness_score = (
        memory_readiness_ratio
        + policy_freshness_ratio
        + evidence_reuse_ratio
        + calibration_readiness_ratio
    ) / Decimal("4")
    reason_codes = _row_reason_codes(
        memory_readiness_ratio=memory_readiness_ratio,
        policy_freshness_ratio=policy_freshness_ratio,
        evidence_reuse_ratio=evidence_reuse_ratio,
        calibration_readiness_ratio=calibration_readiness_ratio,
        config=config,
    )
    return ResearchCreditRateEventTeamMemoryRow(
        team_label=item.team_label,
        event_family_label=item.event_family_label,
        memory_fresh_count=item.memory_fresh_count,
        memory_total_count=item.memory_total_count,
        memory_readiness_ratio=memory_readiness_ratio,
        policy_fresh_count=item.policy_fresh_count,
        policy_reference_count=item.policy_reference_count,
        policy_freshness_ratio=policy_freshness_ratio,
        evidence_reuse_count=item.evidence_reuse_count,
        evidence_case_count=item.evidence_case_count,
        evidence_reuse_ratio=evidence_reuse_ratio,
        calibration_ready_count=item.calibration_ready_count,
        calibration_target_count=item.calibration_target_count,
        calibration_readiness_ratio=calibration_readiness_ratio,
        readiness_score=readiness_score.quantize(QUANT),
        status=_status_from_row_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    memory_readiness_ratio: Decimal,
    policy_freshness_ratio: Decimal,
    evidence_reuse_ratio: Decimal,
    calibration_readiness_ratio: Decimal,
    config: ResearchCreditRateEventTeamMemoryReportConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if memory_readiness_ratio < config.memory_readiness_block_threshold:
        reason_codes.append("credit_rate_event_team_memory_memory_readiness_block")
    if policy_freshness_ratio < config.policy_freshness_block_threshold:
        reason_codes.append("credit_rate_event_team_memory_policy_freshness_block")
    if evidence_reuse_ratio < config.evidence_reuse_block_threshold:
        reason_codes.append("credit_rate_event_team_memory_evidence_reuse_block")
    if calibration_readiness_ratio < config.calibration_readiness_block_threshold:
        reason_codes.append("credit_rate_event_team_memory_calibration_readiness_block")
    if reason_codes:
        return tuple(reason_codes)
    if memory_readiness_ratio < config.memory_readiness_watch_threshold:
        reason_codes.append("credit_rate_event_team_memory_memory_readiness_watch")
    if policy_freshness_ratio < config.policy_freshness_watch_threshold:
        reason_codes.append("credit_rate_event_team_memory_policy_freshness_watch")
    if evidence_reuse_ratio < config.evidence_reuse_watch_threshold:
        reason_codes.append("credit_rate_event_team_memory_evidence_reuse_watch")
    if calibration_readiness_ratio < config.calibration_readiness_watch_threshold:
        reason_codes.append("credit_rate_event_team_memory_calibration_readiness_watch")
    if reason_codes:
        return tuple(reason_codes)
    return ("credit_rate_event_team_memory_ready",)


def _report_reason_codes(
    rows: tuple[ResearchCreditRateEventTeamMemoryRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("credit_rate_event_team_memory_empty",)
    reason_codes: list[str] = []
    if any(row.status == "block" for row in rows):
        reason_codes.append("credit_rate_event_team_memory_block_teams_present")
    if any(row.status == "watch" for row in rows):
        reason_codes.append("credit_rate_event_team_memory_watch_teams_present")
    if not reason_codes:
        reason_codes.append("credit_rate_event_team_memory_ready")
    return tuple(reason_codes)


def _status_from_row_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _status_from_report_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if "credit_rate_event_team_memory_block_teams_present" in reason_codes:
        return "block"
    if "credit_rate_event_team_memory_watch_teams_present" in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchCreditRateEventTeamMemoryRow, ...],
) -> tuple[ResearchCreditRateEventTeamMemoryReasonCodeCount, ...]:
    all_reason_codes = Counter(reason_code for row in rows for reason_code in row.reason_codes)
    return tuple(
        ResearchCreditRateEventTeamMemoryReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(all_reason_codes[reason_code]),
        )
        for reason_code in ROW_REASON_CODES
        if reason_code in all_reason_codes
    )


def _normalize_inputs(
    value: object,
) -> tuple[ResearchCreditRateEventTeamMemoryInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchCreditRateEventTeamMemoryInput:
            raise ValueError("inputs must contain input values")
        _require_hard_flags("input", row)
        key = (row.team_label, row.event_family_label)
        if key in seen:
            raise ValueError("inputs must be unique by team_label and event_family_label")
        seen.add(key)
    return tuple(sorted(rows, key=lambda row: (row.team_label, row.event_family_label)))


def _normalize_rows(
    value: object,
) -> tuple[ResearchCreditRateEventTeamMemoryRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchCreditRateEventTeamMemoryRow:
            raise ValueError("rows must contain row values")
        _require_hard_flags("row", row)
        key = (row.team_label, row.event_family_label)
        if key in seen:
            raise ValueError("rows must be unique by team_label and event_family_label")
        seen.add(key)
    return tuple(sorted(rows, key=lambda row: (row.team_label, row.event_family_label)))


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchCreditRateEventTeamMemoryReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchCreditRateEventTeamMemoryReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count values")
        _require_hard_flags("reason_code_count", row)
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(row.reason_code)
    expected = tuple(row for code in ROW_REASON_CODES for row in rows if row.reason_code == code)
    if rows != expected:
        raise ValueError("reason_code_counts must be deterministic")
    return rows


def _normalize_reason_codes(
    value: object,
    known_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must contain at least one value")
    for reason_code in reason_codes:
        _require_public_label("reason_code", reason_code)
        if reason_code not in known_reason_codes:
            raise ValueError("reason_codes must contain known values")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    expected = tuple(code for code in known_reason_codes if code in reason_codes)
    if reason_codes != expected:
        raise ValueError("reason_codes must be deterministic")
    return reason_codes


def _validate_count_bounds(
    value: ResearchCreditRateEventTeamMemoryInput | ResearchCreditRateEventTeamMemoryRow,
) -> None:
    if value.memory_fresh_count > value.memory_total_count:
        raise ValueError("memory_fresh_count must not exceed memory_total_count")
    if value.policy_fresh_count > value.policy_reference_count:
        raise ValueError("policy_fresh_count must not exceed policy_reference_count")
    if value.evidence_reuse_count > value.evidence_case_count:
        raise ValueError("evidence_reuse_count must not exceed evidence_case_count")
    if value.calibration_ready_count > value.calibration_target_count:
        raise ValueError(
            "calibration_ready_count must not exceed calibration_target_count",
        )


def _validate_row_consistency(row: ResearchCreditRateEventTeamMemoryRow) -> None:
    if row.memory_readiness_ratio != _ratio(
        row.memory_fresh_count,
        row.memory_total_count,
    ):
        raise ValueError("memory_readiness_ratio must match counts")
    if row.policy_freshness_ratio != _ratio(
        row.policy_fresh_count,
        row.policy_reference_count,
    ):
        raise ValueError("policy_freshness_ratio must match counts")
    if row.evidence_reuse_ratio != _ratio(
        row.evidence_reuse_count,
        row.evidence_case_count,
    ):
        raise ValueError("evidence_reuse_ratio must match counts")
    if row.calibration_readiness_ratio != _ratio(
        row.calibration_ready_count,
        row.calibration_target_count,
    ):
        raise ValueError("calibration_readiness_ratio must match counts")
    expected_score = (
        row.memory_readiness_ratio
        + row.policy_freshness_ratio
        + row.evidence_reuse_ratio
        + row.calibration_readiness_ratio
    ) / Decimal("4")
    if row.readiness_score != expected_score.quantize(QUANT):
        raise ValueError("readiness_score must match component ratios")
    if row.status != _status_from_row_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(report: ResearchCreditRateEventTeamMemoryReport) -> None:
    if report.team_count != _decimal_count(len(report.rows)):
        raise ValueError("team_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.average_readiness_score != _average(report.rows, "readiness_score"):
        raise ValueError("average_readiness_score must match rows")
    if report.lowest_memory_readiness_ratio != _minimum(
        report.rows,
        "memory_readiness_ratio",
    ):
        raise ValueError("lowest_memory_readiness_ratio must match rows")
    if report.lowest_policy_freshness_ratio != _minimum(
        report.rows,
        "policy_freshness_ratio",
    ):
        raise ValueError("lowest_policy_freshness_ratio must match rows")
    if report.lowest_evidence_reuse_ratio != _minimum(report.rows, "evidence_reuse_ratio"):
        raise ValueError("lowest_evidence_reuse_ratio must match rows")
    if report.lowest_calibration_readiness_ratio != _minimum(
        report.rows,
        "calibration_readiness_ratio",
    ):
        raise ValueError("lowest_calibration_readiness_ratio must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _status_from_report_reason_codes(report.reason_codes):
        raise ValueError("status must match reason_codes")


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


def _status_count(
    rows: tuple[ResearchCreditRateEventTeamMemoryRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _average(
    rows: tuple[ResearchCreditRateEventTeamMemoryRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO.quantize(QUANT)
    return (
        sum((getattr(row, field_name) for row in rows), ZERO) / Decimal(len(rows))
    ).quantize(QUANT)


def _minimum(
    rows: tuple[ResearchCreditRateEventTeamMemoryRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO.quantize(QUANT)
    return min(getattr(row, field_name) for row in rows).quantize(QUANT)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("ratio denominator must be positive")
    return (numerator / denominator).quantize(QUANT)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_label(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} must be public")


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value.quantize(QUANT)


def _require_positive_decimal(field_name: str, value: Decimal) -> None:
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")


def _require_ratio(field_name: str, value: object) -> Decimal:
    ratio = _require_nonnegative_decimal(field_name, value)
    if ratio > ONE:
        raise ValueError(f"{field_name} must not exceed 1.000000")
    return ratio


def _require_floor_ceiling(
    floor_name: str,
    floor_value: Decimal,
    ceiling_name: str,
    ceiling_value: Decimal,
) -> None:
    if floor_value > ceiling_value:
        raise ValueError(f"{floor_name} must not exceed {ceiling_name}")


def _require_status(field_name: str, value: object) -> None:
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != DIGEST_HEX_LENGTH:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    for public_value in _public_strings(value):
        lowered = public_value.lower()
        if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError(f"{label} must contain aggregate-safe labels")


def _public_strings(value: object) -> tuple[str, ...]:
    if is_dataclass(value):
        return _public_strings(asdict(value))
    if isinstance(value, dict):
        strings: list[str] = []
        for key, item in value.items():
            strings.extend(_public_strings(key))
            strings.extend(_public_strings(item))
        return tuple(strings)
    if isinstance(value, (list, tuple)):
        strings = []
        for item in value:
            strings.extend(_public_strings(item))
        return tuple(strings)
    if type(value) is str:
        return (value,)
    return ()


def _reject_public_numeric_values(value: object) -> None:
    if type(value) in (int, float):
        raise ValueError("payload must not contain int or float values")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
    elif isinstance(value, list):
        for item in value:
            _reject_public_numeric_values(item)


def _report_values_without_digest(
    report: ResearchCreditRateEventTeamMemoryReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest")
    return values


def _report_digest_from_values(values: dict[str, object]) -> str:
    payload = _json_ready(values)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    values = dict(payload)
    values.pop("derived_validation_digest")
    expected_digest = _report_digest_from_values(values)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest must match payload")


def _json_ready(value: object) -> Any:
    if is_dataclass(value):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        return format(value.quantize(QUANT), "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    return value
