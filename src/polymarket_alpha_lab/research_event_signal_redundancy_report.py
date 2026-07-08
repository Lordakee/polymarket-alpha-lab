"""Pure report reducer for public-safe research signal redundancy."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_EVENT_SIGNAL_REDUNDANCY_CONFIG_VERSION = (
    "research-event-signal-redundancy-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
REDUNDANCY_STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

EVIDENCE_OVERLAP_BLOCK_REASON = "research_event_signal_evidence_overlap_block"
EVIDENCE_OVERLAP_WATCH_REASON = "research_event_signal_evidence_overlap_watch"
CATALYST_OVERLAP_BLOCK_REASON = "research_event_signal_catalyst_overlap_block"
CATALYST_OVERLAP_WATCH_REASON = "research_event_signal_catalyst_overlap_watch"
SOURCE_CLASS_OVERLAP_BLOCK_REASON = (
    "research_event_signal_source_class_overlap_block"
)
SOURCE_CLASS_OVERLAP_WATCH_REASON = (
    "research_event_signal_source_class_overlap_watch"
)
TEAM_CONFIDENCE_DISPERSION_BLOCK_REASON = (
    "research_event_signal_team_confidence_dispersion_block"
)
TEAM_CONFIDENCE_DISPERSION_WATCH_REASON = (
    "research_event_signal_team_confidence_dispersion_watch"
)
RESOLUTION_AMBIGUITY_BLOCK_REASON = (
    "research_event_signal_resolution_ambiguity_block"
)
RESOLUTION_AMBIGUITY_WATCH_REASON = (
    "research_event_signal_resolution_ambiguity_watch"
)
PASS_REASON = "research_event_signal_redundancy_passed"
WATCH_PRESENT_REASON = "research_event_signal_redundancy_watch_present"
CLEAR_REASON = "research_event_signal_redundancy_clear"
EMPTY_REASON = "research_event_signal_redundancy_empty"

ROW_REASON_CODE_SEQUENCE = (
    EVIDENCE_OVERLAP_BLOCK_REASON,
    EVIDENCE_OVERLAP_WATCH_REASON,
    CATALYST_OVERLAP_BLOCK_REASON,
    CATALYST_OVERLAP_WATCH_REASON,
    SOURCE_CLASS_OVERLAP_BLOCK_REASON,
    SOURCE_CLASS_OVERLAP_WATCH_REASON,
    TEAM_CONFIDENCE_DISPERSION_BLOCK_REASON,
    TEAM_CONFIDENCE_DISPERSION_WATCH_REASON,
    RESOLUTION_AMBIGUITY_BLOCK_REASON,
    RESOLUTION_AMBIGUITY_WATCH_REASON,
    PASS_REASON,
)
REPORT_REASON_CODE_SEQUENCE = (
    EVIDENCE_OVERLAP_BLOCK_REASON,
    EVIDENCE_OVERLAP_WATCH_REASON,
    CATALYST_OVERLAP_BLOCK_REASON,
    CATALYST_OVERLAP_WATCH_REASON,
    SOURCE_CLASS_OVERLAP_BLOCK_REASON,
    SOURCE_CLASS_OVERLAP_WATCH_REASON,
    TEAM_CONFIDENCE_DISPERSION_BLOCK_REASON,
    TEAM_CONFIDENCE_DISPERSION_WATCH_REASON,
    RESOLUTION_AMBIGUITY_BLOCK_REASON,
    RESOLUTION_AMBIGUITY_WATCH_REASON,
    WATCH_PRESENT_REASON,
    CLEAR_REASON,
    EMPTY_REASON,
)
BLOCK_REASON_CODES = (
    EVIDENCE_OVERLAP_BLOCK_REASON,
    CATALYST_OVERLAP_BLOCK_REASON,
    SOURCE_CLASS_OVERLAP_BLOCK_REASON,
    TEAM_CONFIDENCE_DISPERSION_BLOCK_REASON,
    RESOLUTION_AMBIGUITY_BLOCK_REASON,
)

NEXT_STEPS = {
    STATUS_PASS: "allow_report_only_research_event_signal_redundancy",
    STATUS_WATCH: "watch_report_only_research_event_signal_redundancy",
    STATUS_BLOCK: "block_report_only_research_event_signal_redundancy",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
WATCH_RISK_SCORE = Decimal("0.500000")
_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


__all__ = (
    "DEFAULT_RESEARCH_EVENT_SIGNAL_REDUNDANCY_CONFIG_VERSION",
    "ResearchEventSignalRedundancyConfig",
    "ResearchEventSignalRedundancyInput",
    "ResearchEventSignalRedundancyRow",
    "ResearchEventSignalRedundancyReasonCodeCount",
    "ResearchEventSignalRedundancyReport",
    "build_research_event_signal_redundancy_report",
    "research_event_signal_redundancy_report_payload",
    "research_event_signal_redundancy_report_digest",
)


@dataclass(frozen=True)
class ResearchEventSignalRedundancyConfig:
    config_version: str = DEFAULT_RESEARCH_EVENT_SIGNAL_REDUNDANCY_CONFIG_VERSION
    evidence_overlap_watch_threshold: Decimal = Decimal("0.350000")
    evidence_overlap_block_threshold: Decimal = Decimal("0.700000")
    catalyst_overlap_watch_threshold: Decimal = Decimal("0.350000")
    catalyst_overlap_block_threshold: Decimal = Decimal("0.700000")
    source_class_overlap_watch_threshold: Decimal = Decimal("0.300000")
    source_class_overlap_block_threshold: Decimal = Decimal("0.700000")
    team_confidence_dispersion_watch_threshold: Decimal = Decimal("0.200000")
    team_confidence_dispersion_block_threshold: Decimal = Decimal("0.400000")
    resolution_ambiguity_watch_threshold: Decimal = Decimal("0.300000")
    resolution_ambiguity_block_threshold: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventSignalRedundancyConfig:
            raise TypeError(
                "ResearchEventSignalRedundancyConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventSignalRedundancyConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_EVENT_SIGNAL_REDUNDANCY_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "evidence_overlap_watch_threshold",
            "evidence_overlap_block_threshold",
            "catalyst_overlap_watch_threshold",
            "catalyst_overlap_block_threshold",
            "source_class_overlap_watch_threshold",
            "source_class_overlap_block_threshold",
            "team_confidence_dispersion_watch_threshold",
            "team_confidence_dispersion_block_threshold",
            "resolution_ambiguity_watch_threshold",
            "resolution_ambiguity_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_watch_not_above_block(
            "evidence_overlap_watch_threshold",
            self.evidence_overlap_watch_threshold,
            "evidence_overlap_block_threshold",
            self.evidence_overlap_block_threshold,
        )
        _require_watch_not_above_block(
            "catalyst_overlap_watch_threshold",
            self.catalyst_overlap_watch_threshold,
            "catalyst_overlap_block_threshold",
            self.catalyst_overlap_block_threshold,
        )
        _require_watch_not_above_block(
            "source_class_overlap_watch_threshold",
            self.source_class_overlap_watch_threshold,
            "source_class_overlap_block_threshold",
            self.source_class_overlap_block_threshold,
        )
        _require_watch_not_above_block(
            "team_confidence_dispersion_watch_threshold",
            self.team_confidence_dispersion_watch_threshold,
            "team_confidence_dispersion_block_threshold",
            self.team_confidence_dispersion_block_threshold,
        )
        _require_watch_not_above_block(
            "resolution_ambiguity_watch_threshold",
            self.resolution_ambiguity_watch_threshold,
            "resolution_ambiguity_block_threshold",
            self.resolution_ambiguity_block_threshold,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventSignalRedundancyInput:
    research_theme: str
    signal_family: str
    evidence_overlap_ratio: Decimal
    catalyst_overlap_ratio: Decimal
    source_class_overlap_ratio: Decimal
    team_confidence_dispersion: Decimal
    resolution_ambiguity_ratio: Decimal
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventSignalRedundancyInput:
            raise TypeError(
                "ResearchEventSignalRedundancyInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventSignalRedundancyInput, "input")
        _require_canonical_string("research_theme", self.research_theme)
        _require_canonical_string("signal_family", self.signal_family)
        for field_name in (
            "evidence_overlap_ratio",
            "catalyst_overlap_ratio",
            "source_class_overlap_ratio",
            "team_confidence_dispersion",
            "resolution_ambiguity_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_open_reason_codes(
                "upstream_reason_codes",
                self.upstream_reason_codes,
            ),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchEventSignalRedundancyRow:
    research_theme: str
    signal_family: str
    evidence_overlap_ratio: Decimal
    catalyst_overlap_ratio: Decimal
    source_class_overlap_ratio: Decimal
    team_confidence_dispersion: Decimal
    resolution_ambiguity_ratio: Decimal
    redundancy_status: str
    risk_score: Decimal
    upstream_reason_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventSignalRedundancyRow:
            raise TypeError(
                "ResearchEventSignalRedundancyRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventSignalRedundancyRow, "row")
        _require_canonical_string("research_theme", self.research_theme)
        _require_canonical_string("signal_family", self.signal_family)
        for field_name in (
            "evidence_overlap_ratio",
            "catalyst_overlap_ratio",
            "source_class_overlap_ratio",
            "team_confidence_dispersion",
            "resolution_ambiguity_ratio",
            "risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("redundancy_status", self.redundancy_status, REDUNDANCY_STATUSES)
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_open_reason_codes(
                "upstream_reason_codes",
                self.upstream_reason_codes,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                ROW_REASON_CODE_SEQUENCE,
            ),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchEventSignalRedundancyReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventSignalRedundancyReasonCodeCount:
            raise TypeError(
                "ResearchEventSignalRedundancyReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventSignalRedundancyReasonCodeCount,
            "reason code count",
        )
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODE_SEQUENCE)
        object.__setattr__(self, "count", _require_nonnegative_decimal("count", self.count))
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchEventSignalRedundancyReport:
    generated_at: datetime
    config_version: str
    redundancy_status: str
    recommended_next_step: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    evidence_overlap_count: Decimal
    catalyst_overlap_count: Decimal
    source_class_overlap_count: Decimal
    team_confidence_dispersion_count: Decimal
    resolution_ambiguity_count: Decimal
    max_evidence_overlap_ratio: Decimal
    max_catalyst_overlap_ratio: Decimal
    max_source_class_overlap_ratio: Decimal
    max_team_confidence_dispersion: Decimal
    max_resolution_ambiguity_ratio: Decimal
    redundancy_risk_score: Decimal
    rows: tuple[ResearchEventSignalRedundancyRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchEventSignalRedundancyReasonCodeCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventSignalRedundancyReport:
            raise TypeError(
                "ResearchEventSignalRedundancyReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventSignalRedundancyReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_EVENT_SIGNAL_REDUNDANCY_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_member("redundancy_status", self.redundancy_status, REDUNDANCY_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        if self.recommended_next_step != NEXT_STEPS[self.redundancy_status]:
            raise ValueError("recommended_next_step must match redundancy_status")
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "evidence_overlap_count",
            "catalyst_overlap_count",
            "source_class_overlap_count",
            "team_confidence_dispersion_count",
            "resolution_ambiguity_count",
            "max_evidence_overlap_ratio",
            "max_catalyst_overlap_ratio",
            "max_source_class_overlap_ratio",
            "max_team_confidence_dispersion",
            "max_resolution_ambiguity_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "redundancy_risk_score",
            _require_ratio_decimal(
                "redundancy_risk_score",
                self.redundancy_risk_score,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODE_SEQUENCE,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)


def build_research_event_signal_redundancy_report(
    inputs: tuple[object, ...],
    *,
    config: ResearchEventSignalRedundancyConfig | None = None,
    generated_at: datetime,
) -> ResearchEventSignalRedundancyReport:
    cfg = config or ResearchEventSignalRedundancyConfig()
    if type(cfg) is not ResearchEventSignalRedundancyConfig:
        raise ValueError("config must be exactly ResearchEventSignalRedundancyConfig")
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (_build_row(row, config=cfg) for row in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    redundancy_status = _report_status(rows)
    return ResearchEventSignalRedundancyReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        redundancy_status=redundancy_status,
        recommended_next_step=NEXT_STEPS[redundancy_status],
        input_count=_decimal_count(len(normalized_inputs)),
        row_count=_decimal_count(len(rows)),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        evidence_overlap_count=(
            _reason_count(EVIDENCE_OVERLAP_BLOCK_REASON, rows)
            + _reason_count(EVIDENCE_OVERLAP_WATCH_REASON, rows)
        ),
        catalyst_overlap_count=(
            _reason_count(CATALYST_OVERLAP_BLOCK_REASON, rows)
            + _reason_count(CATALYST_OVERLAP_WATCH_REASON, rows)
        ),
        source_class_overlap_count=(
            _reason_count(SOURCE_CLASS_OVERLAP_BLOCK_REASON, rows)
            + _reason_count(SOURCE_CLASS_OVERLAP_WATCH_REASON, rows)
        ),
        team_confidence_dispersion_count=(
            _reason_count(TEAM_CONFIDENCE_DISPERSION_BLOCK_REASON, rows)
            + _reason_count(TEAM_CONFIDENCE_DISPERSION_WATCH_REASON, rows)
        ),
        resolution_ambiguity_count=(
            _reason_count(RESOLUTION_AMBIGUITY_BLOCK_REASON, rows)
            + _reason_count(RESOLUTION_AMBIGUITY_WATCH_REASON, rows)
        ),
        max_evidence_overlap_ratio=_max_decimal(
            (row.evidence_overlap_ratio for row in rows),
            default=ZERO,
        ),
        max_catalyst_overlap_ratio=_max_decimal(
            (row.catalyst_overlap_ratio for row in rows),
            default=ZERO,
        ),
        max_source_class_overlap_ratio=_max_decimal(
            (row.source_class_overlap_ratio for row in rows),
            default=ZERO,
        ),
        max_team_confidence_dispersion=_max_decimal(
            (row.team_confidence_dispersion for row in rows),
            default=ZERO,
        ),
        max_resolution_ambiguity_ratio=_max_decimal(
            (row.resolution_ambiguity_ratio for row in rows),
            default=ZERO,
        ),
        redundancy_risk_score=_report_risk_score(rows),
        rows=rows,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
    )


def research_event_signal_redundancy_report_payload(
    report: ResearchEventSignalRedundancyReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEventSignalRedundancyReport:
        raise ValueError("report must be exactly ResearchEventSignalRedundancyReport")
    _validate_report_consistency(report)
    return _payload_value(report)


def research_event_signal_redundancy_report_digest(
    report: ResearchEventSignalRedundancyReport,
) -> str:
    payload = research_event_signal_redundancy_report_payload(report)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(canonical.encode("utf-8")).hexdigest()


def _build_row(
    row: ResearchEventSignalRedundancyInput,
    *,
    config: ResearchEventSignalRedundancyConfig,
) -> ResearchEventSignalRedundancyRow:
    reason_codes = _row_reason_codes(row, config=config)
    redundancy_status = _row_status(reason_codes)
    return ResearchEventSignalRedundancyRow(
        research_theme=row.research_theme,
        signal_family=row.signal_family,
        evidence_overlap_ratio=row.evidence_overlap_ratio,
        catalyst_overlap_ratio=row.catalyst_overlap_ratio,
        source_class_overlap_ratio=row.source_class_overlap_ratio,
        team_confidence_dispersion=row.team_confidence_dispersion,
        resolution_ambiguity_ratio=row.resolution_ambiguity_ratio,
        redundancy_status=redundancy_status,
        risk_score=_status_risk_score(redundancy_status),
        upstream_reason_codes=row.upstream_reason_codes,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    row: ResearchEventSignalRedundancyInput,
    *,
    config: ResearchEventSignalRedundancyConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    _append_threshold_reason(
        reasons,
        row.evidence_overlap_ratio,
        config.evidence_overlap_watch_threshold,
        config.evidence_overlap_block_threshold,
        EVIDENCE_OVERLAP_WATCH_REASON,
        EVIDENCE_OVERLAP_BLOCK_REASON,
    )
    _append_threshold_reason(
        reasons,
        row.catalyst_overlap_ratio,
        config.catalyst_overlap_watch_threshold,
        config.catalyst_overlap_block_threshold,
        CATALYST_OVERLAP_WATCH_REASON,
        CATALYST_OVERLAP_BLOCK_REASON,
    )
    _append_threshold_reason(
        reasons,
        row.source_class_overlap_ratio,
        config.source_class_overlap_watch_threshold,
        config.source_class_overlap_block_threshold,
        SOURCE_CLASS_OVERLAP_WATCH_REASON,
        SOURCE_CLASS_OVERLAP_BLOCK_REASON,
    )
    _append_threshold_reason(
        reasons,
        row.team_confidence_dispersion,
        config.team_confidence_dispersion_watch_threshold,
        config.team_confidence_dispersion_block_threshold,
        TEAM_CONFIDENCE_DISPERSION_WATCH_REASON,
        TEAM_CONFIDENCE_DISPERSION_BLOCK_REASON,
    )
    _append_threshold_reason(
        reasons,
        row.resolution_ambiguity_ratio,
        config.resolution_ambiguity_watch_threshold,
        config.resolution_ambiguity_block_threshold,
        RESOLUTION_AMBIGUITY_WATCH_REASON,
        RESOLUTION_AMBIGUITY_BLOCK_REASON,
    )
    if not reasons:
        reasons.append(PASS_REASON)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reasons),
        ROW_REASON_CODE_SEQUENCE,
    )


def _append_threshold_reason(
    reasons: list[str],
    value: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
    watch_reason: str,
    block_reason: str,
) -> None:
    if value >= block_threshold:
        reasons.append(block_reason)
    elif value >= watch_threshold:
        reasons.append(watch_reason)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason in BLOCK_REASON_CODES for reason in reason_codes):
        return STATUS_BLOCK
    if reason_codes == (PASS_REASON,):
        return STATUS_PASS
    return STATUS_WATCH


def _status_risk_score(status: str) -> Decimal:
    if status == STATUS_BLOCK:
        return ONE
    if status == STATUS_WATCH:
        return WATCH_RISK_SCORE
    return ZERO


def _report_reason_codes(
    rows: tuple[ResearchEventSignalRedundancyRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    present = {reason for row in rows for reason in row.reason_codes if reason != PASS_REASON}
    reasons = [reason for reason in REPORT_REASON_CODE_SEQUENCE if reason in present]
    if any(row.redundancy_status == STATUS_WATCH for row in rows):
        reasons.append(WATCH_PRESENT_REASON)
    if not reasons:
        reasons.append(CLEAR_REASON)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reasons),
        REPORT_REASON_CODE_SEQUENCE,
    )


def _report_status(rows: tuple[ResearchEventSignalRedundancyRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.redundancy_status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.redundancy_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[ResearchEventSignalRedundancyRow, ...],
) -> tuple[ResearchEventSignalRedundancyReasonCodeCount, ...]:
    row_count = _decimal_count(len(rows))
    if reason_codes == (EMPTY_REASON,):
        return (
            ResearchEventSignalRedundancyReasonCodeCount(
                reason_code=EMPTY_REASON,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        ResearchEventSignalRedundancyReasonCodeCount(
            reason_code=reason_code,
            count=_report_reason_count(reason_code, rows),
            row_ratio=_ratio(_report_reason_count(reason_code, rows), row_count),
        )
        for reason_code in reason_codes
    )


def _report_reason_count(
    reason_code: str,
    rows: tuple[ResearchEventSignalRedundancyRow, ...],
) -> Decimal:
    if reason_code == WATCH_PRESENT_REASON:
        return _status_count(rows, STATUS_WATCH)
    if reason_code == CLEAR_REASON:
        return _status_count(rows, STATUS_PASS)
    return _reason_count(reason_code, rows)


def _reason_count(
    reason_code: str,
    rows: tuple[ResearchEventSignalRedundancyRow, ...],
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _status_count(
    rows: tuple[ResearchEventSignalRedundancyRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.redundancy_status == status))


def _report_risk_score(rows: tuple[ResearchEventSignalRedundancyRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    weighted = _status_count(rows, STATUS_BLOCK) + (
        _status_count(rows, STATUS_WATCH) * WATCH_RISK_SCORE
    )
    return _ratio(weighted, _decimal_count(len(rows)))


def _validate_row_consistency(row: ResearchEventSignalRedundancyRow) -> None:
    if row.redundancy_status != _row_status(row.reason_codes):
        raise ValueError("reason_codes must match redundancy_status")
    if row.risk_score != _status_risk_score(row.redundancy_status):
        raise ValueError("risk_score must match redundancy_status")
    if row.redundancy_status == STATUS_PASS and row.reason_codes != (PASS_REASON,):
        raise ValueError("reason_codes must match redundancy_status")
    if row.redundancy_status != STATUS_PASS and PASS_REASON in row.reason_codes:
        raise ValueError("reason_codes must match redundancy_status")


def _validate_report_consistency(report: ResearchEventSignalRedundancyReport) -> None:
    if report.input_count != _decimal_count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _status_count(report.rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.pass_count + report.watch_count + report.block_count != report.row_count:
        raise ValueError("status counts must match rows")
    if report.evidence_overlap_count != (
        _reason_count(EVIDENCE_OVERLAP_BLOCK_REASON, report.rows)
        + _reason_count(EVIDENCE_OVERLAP_WATCH_REASON, report.rows)
    ):
        raise ValueError("evidence_overlap_count must match rows")
    if report.catalyst_overlap_count != (
        _reason_count(CATALYST_OVERLAP_BLOCK_REASON, report.rows)
        + _reason_count(CATALYST_OVERLAP_WATCH_REASON, report.rows)
    ):
        raise ValueError("catalyst_overlap_count must match rows")
    if report.source_class_overlap_count != (
        _reason_count(SOURCE_CLASS_OVERLAP_BLOCK_REASON, report.rows)
        + _reason_count(SOURCE_CLASS_OVERLAP_WATCH_REASON, report.rows)
    ):
        raise ValueError("source_class_overlap_count must match rows")
    if report.team_confidence_dispersion_count != (
        _reason_count(TEAM_CONFIDENCE_DISPERSION_BLOCK_REASON, report.rows)
        + _reason_count(TEAM_CONFIDENCE_DISPERSION_WATCH_REASON, report.rows)
    ):
        raise ValueError("team_confidence_dispersion_count must match rows")
    if report.resolution_ambiguity_count != (
        _reason_count(RESOLUTION_AMBIGUITY_BLOCK_REASON, report.rows)
        + _reason_count(RESOLUTION_AMBIGUITY_WATCH_REASON, report.rows)
    ):
        raise ValueError("resolution_ambiguity_count must match rows")
    if report.max_evidence_overlap_ratio != _max_decimal(
        (row.evidence_overlap_ratio for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_evidence_overlap_ratio must match rows")
    if report.max_catalyst_overlap_ratio != _max_decimal(
        (row.catalyst_overlap_ratio for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_catalyst_overlap_ratio must match rows")
    if report.max_source_class_overlap_ratio != _max_decimal(
        (row.source_class_overlap_ratio for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_source_class_overlap_ratio must match rows")
    if report.max_team_confidence_dispersion != _max_decimal(
        (row.team_confidence_dispersion for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_team_confidence_dispersion must match rows")
    if report.max_resolution_ambiguity_ratio != _max_decimal(
        (row.resolution_ambiguity_ratio for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_resolution_ambiguity_ratio must match rows")
    if report.redundancy_risk_score != _report_risk_score(report.rows):
        raise ValueError("redundancy_risk_score must match rows")
    if report.redundancy_status != _report_status(report.rows):
        raise ValueError("redundancy_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, report.rows):
        raise ValueError("reason_code_counts must match reason_codes")


def _normalize_inputs(
    inputs: tuple[object, ...],
) -> tuple[ResearchEventSignalRedundancyInput, ...]:
    if type(inputs) is not tuple:
        raise ValueError("inputs must be a tuple")
    seen_pairs: set[tuple[str, str]] = set()
    normalized: list[ResearchEventSignalRedundancyInput] = []
    for row in inputs:
        if type(row) is not ResearchEventSignalRedundancyInput:
            raise ValueError("inputs must contain ResearchEventSignalRedundancyInput")
        _require_hard_flags("input", row)
        pair = (row.research_theme, row.signal_family)
        if pair in seen_pairs:
            raise ValueError(
                "inputs must not contain duplicate research_theme and signal_family",
            )
        seen_pairs.add(pair)
        normalized.append(row)
    return tuple(normalized)


def _normalize_rows(
    rows: tuple[ResearchEventSignalRedundancyRow, ...],
) -> tuple[ResearchEventSignalRedundancyRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen_pairs: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchEventSignalRedundancyRow:
            raise ValueError("rows must contain ResearchEventSignalRedundancyRow")
        _require_hard_flags("row", row)
        pair = (row.research_theme, row.signal_family)
        if pair in seen_pairs:
            raise ValueError(
                "rows must not contain duplicate research_theme and signal_family",
            )
        seen_pairs.add(pair)
    return tuple(sorted(rows, key=_row_sort_key))


def _normalize_reason_code_counts(
    rows: tuple[ResearchEventSignalRedundancyReasonCodeCount, ...],
) -> tuple[ResearchEventSignalRedundancyReasonCodeCount, ...]:
    if type(rows) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for row in rows:
        if type(row) is not ResearchEventSignalRedundancyReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchEventSignalRedundancyReasonCodeCount",
            )
        _require_hard_flags("reason code count", row)
    return tuple(
        sorted(rows, key=lambda row: REPORT_REASON_CODE_SEQUENCE.index(row.reason_code)),
    )


def _normalize_open_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_canonical_string("reason_code", reason_code)
        if reason_code not in seen:
            normalized.append(reason_code)
            seen.add(reason_code)
    return tuple(sorted(normalized))


def _normalize_reason_codes(
    field_name: str,
    reason_codes: Iterable[str],
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Iterable):
        raise ValueError(f"{field_name} must contain reason code strings")
    normalized = tuple(reason_codes)
    seen: set[str] = set()
    for reason_code in normalized:
        _require_member("reason_code", reason_code, sequence)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    return tuple(reason_code for reason_code in sequence if reason_code in seen)


def _row_sort_key(row: ResearchEventSignalRedundancyRow) -> tuple[int, Decimal, str, str]:
    status_rank = {
        STATUS_BLOCK: 0,
        STATUS_WATCH: 1,
        STATUS_PASS: 2,
    }
    return (
        status_rank[row.redundancy_status],
        -row.risk_score,
        row.research_theme,
        row.signal_family,
    )


def _max_decimal(values: Iterable[Decimal], *, default: Decimal) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return default
    for value in normalized:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
    return _quantize(max(normalized))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _require_watch_not_above_block(
    watch_field_name: str,
    watch_value: Decimal,
    block_field_name: str,
    block_value: Decimal,
) -> None:
    if watch_value > block_value:
        raise ValueError(f"{watch_field_name} must not exceed {block_field_name}")


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be supported")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a plain str")
    if not value or value.strip() != value or _CANONICAL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _payload_value(value: object) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    return value
