"""Pure Phase 1 report-only reducer for crude export terminal disruption digests."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import re
from typing import Any


DEFAULT_MARKET_RESEARCH_ENERGY_CRUDE_EXPORT_TERMINAL_DISRUPTION_DIGEST_CONFIG_VERSION = (
    "market-research-energy-crude-export-terminal-disruption-digest-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

DIGEST_STATUSES = ("pass", "watch", "blocked")
BLOCKED_PROBABILITY_REASON = "crude_export_terminal_disruption_blocked_probability"
BLOCKED_CAPACITY_REASON = "crude_export_terminal_disruption_blocked_capacity_loss"
WATCH_PROBABILITY_REASON = "crude_export_terminal_disruption_watch_probability"
WATCH_CAPACITY_REASON = "crude_export_terminal_disruption_watch_capacity_loss"
LONG_OUTAGE_REASON = "crude_export_terminal_disruption_long_outage"
VESSEL_DELAY_REASON = "crude_export_terminal_disruption_vessel_delay"
STALE_EVIDENCE_REASON = "crude_export_terminal_disruption_stale_evidence"
THIN_SOURCES_REASON = "crude_export_terminal_disruption_thin_sources"
INLINE_REASON = "crude_export_terminal_disruption_inline"
DIGEST_PASSED_REASON = "crude_export_terminal_disruption_digest_passed"
DIGEST_EMPTY_REASON = "crude_export_terminal_disruption_digest_empty"

ROW_REASON_CODES = (
    BLOCKED_PROBABILITY_REASON,
    BLOCKED_CAPACITY_REASON,
    WATCH_PROBABILITY_REASON,
    WATCH_CAPACITY_REASON,
    LONG_OUTAGE_REASON,
    VESSEL_DELAY_REASON,
    STALE_EVIDENCE_REASON,
    THIN_SOURCES_REASON,
    INLINE_REASON,
)
REPORT_REASON_CODES = (
    BLOCKED_PROBABILITY_REASON,
    BLOCKED_CAPACITY_REASON,
    WATCH_PROBABILITY_REASON,
    WATCH_CAPACITY_REASON,
    LONG_OUTAGE_REASON,
    VESSEL_DELAY_REASON,
    STALE_EVIDENCE_REASON,
    THIN_SOURCES_REASON,
    DIGEST_PASSED_REASON,
    DIGEST_EMPTY_REASON,
)
STATUS_RANK = {"blocked": 0, "watch": 1, "pass": 2}

BLOCK_NEXT_STEP = "block_report_only_energy_crude_export_terminal_disruption_screening"
MONITOR_NEXT_STEP = "monitor_report_only_energy_crude_export_terminal_disruption_screening"
ALLOW_NEXT_STEP = "allow_report_only_energy_crude_export_terminal_disruption_screening"

_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")
_EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_LINK_PATTERN = re.compile(r"\b" + "h" + r"ttps?://[^\s)>\]]+")
_HEX_ADDRESS_PATTERN = re.compile(r"\b0x[a-fA-F0-9]{40}\b")


__all__ = (
    "DEFAULT_MARKET_RESEARCH_ENERGY_CRUDE_EXPORT_TERMINAL_DISRUPTION_DIGEST_CONFIG_VERSION",
    "MarketResearchEnergyCrudeExportTerminalDisruptionDigestConfig",
    "MarketResearchEnergyCrudeExportTerminalDisruptionInput",
    "MarketResearchEnergyCrudeExportTerminalDisruptionDigestRow",
    "MarketResearchEnergyCrudeExportTerminalDisruptionTerminalSummary",
    "MarketResearchEnergyCrudeExportTerminalDisruptionReasonCodeCount",
    "MarketResearchEnergyCrudeExportTerminalDisruptionDigestReport",
    "build_market_research_energy_crude_export_terminal_disruption_digest",
    "market_research_energy_crude_export_terminal_disruption_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchEnergyCrudeExportTerminalDisruptionDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_ENERGY_CRUDE_EXPORT_TERMINAL_DISRUPTION_DIGEST_CONFIG_VERSION
    )
    watch_disruption_probability: Decimal = Decimal("0.300000")
    blocked_disruption_probability: Decimal = Decimal("0.700000")
    watch_capacity_loss_ratio: Decimal = Decimal("0.200000")
    blocked_capacity_loss_ratio: Decimal = Decimal("0.500000")
    long_outage_hours: Decimal = Decimal("24.000000")
    vessel_delay_watch_hours: Decimal = Decimal("12.000000")
    stale_after_hours: Decimal = Decimal("6.000000")
    min_source_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchEnergyCrudeExportTerminalDisruptionDigestConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_ENERGY_CRUDE_EXPORT_TERMINAL_DISRUPTION_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_disruption_probability",
            "blocked_disruption_probability",
            "watch_capacity_loss_ratio",
            "blocked_capacity_loss_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "long_outage_hours",
            "vessel_delay_watch_hours",
            "stale_after_hours",
            "min_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        _require_integral_decimal("min_source_count", self.min_source_count)
        if self.watch_disruption_probability > self.blocked_disruption_probability:
            raise ValueError(
                "watch_disruption_probability must not exceed "
                "blocked_disruption_probability",
            )
        if self.watch_capacity_loss_ratio > self.blocked_capacity_loss_ratio:
            raise ValueError(
                "watch_capacity_loss_ratio must not exceed blocked_capacity_loss_ratio",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchEnergyCrudeExportTerminalDisruptionInput:
    signal_id: str
    terminal_id: str
    terminal_name: str
    region: str
    market_slug: str
    observed_at: datetime
    source_count: Decimal
    disruption_probability: Decimal
    export_capacity_loss_ratio: Decimal
    expected_outage_hours: Decimal
    affected_export_capacity_bpd: Decimal
    vessel_queue_delay_hours: Decimal
    evidence_title: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchEnergyCrudeExportTerminalDisruptionInput,
            "input row",
        )
        for field_name in ("signal_id", "terminal_id", "region", "market_slug"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "terminal_name",
            _require_trimmed_string("terminal_name", self.terminal_name),
        )
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_decimal("source_count", self.source_count),
        )
        _require_integral_decimal("source_count", self.source_count)
        object.__setattr__(
            self,
            "disruption_probability",
            _require_ratio_decimal(
                "disruption_probability",
                self.disruption_probability,
            ),
        )
        object.__setattr__(
            self,
            "export_capacity_loss_ratio",
            _require_ratio_decimal(
                "export_capacity_loss_ratio",
                self.export_capacity_loss_ratio,
            ),
        )
        for field_name in (
            "expected_outage_hours",
            "affected_export_capacity_bpd",
            "vessel_queue_delay_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "evidence_title", _redact(self.evidence_title))
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchEnergyCrudeExportTerminalDisruptionDigestRow:
    signal_id: str
    terminal_id: str
    terminal_name: str
    region: str
    market_slug: str
    observed_at: datetime
    digest_status: str
    source_count: Decimal
    disruption_probability: Decimal
    export_capacity_loss_ratio: Decimal
    expected_outage_hours: Decimal
    affected_export_capacity_bpd: Decimal
    vessel_queue_delay_hours: Decimal
    evidence_age_hours: Decimal
    redacted_evidence_title: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchEnergyCrudeExportTerminalDisruptionDigestRow,
            "row",
        )
        for field_name in ("signal_id", "terminal_id", "region", "market_slug"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "terminal_name",
            _require_trimmed_string("terminal_name", self.terminal_name),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_member("digest_status", self.digest_status, DIGEST_STATUSES)
        for field_name in (
            "source_count",
            "disruption_probability",
            "export_capacity_loss_ratio",
            "expected_outage_hours",
            "affected_export_capacity_bpd",
            "vessel_queue_delay_hours",
            "evidence_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_integral_decimal("source_count", self.source_count)
        _require_ratio_decimal("disruption_probability", self.disruption_probability)
        _require_ratio_decimal(
            "export_capacity_loss_ratio",
            self.export_capacity_loss_ratio,
        )
        object.__setattr__(
            self,
            "redacted_evidence_title",
            _redact(self.redacted_evidence_title),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchEnergyCrudeExportTerminalDisruptionTerminalSummary:
    terminal_id: str
    terminal_name: str
    region: str
    input_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    max_disruption_probability: Decimal
    max_capacity_loss_ratio: Decimal
    total_expected_outage_hours: Decimal
    total_affected_export_capacity_bpd: Decimal
    max_vessel_queue_delay_hours: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchEnergyCrudeExportTerminalDisruptionTerminalSummary,
            "terminal summary",
        )
        _require_canonical_string("terminal_id", self.terminal_id)
        _require_canonical_string("region", self.region)
        object.__setattr__(
            self,
            "terminal_name",
            _require_trimmed_string("terminal_name", self.terminal_name),
        )
        for field_name in (
            "input_count",
            "watch_count",
            "blocked_count",
            "max_disruption_probability",
            "max_capacity_loss_ratio",
            "total_expected_outage_hours",
            "total_affected_export_capacity_bpd",
            "max_vessel_queue_delay_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_ratio_decimal("max_disruption_probability", self.max_disruption_probability)
        _require_ratio_decimal("max_capacity_loss_ratio", self.max_capacity_loss_ratio)
        if self.watch_count + self.blocked_count > self.input_count:
            raise ValueError("terminal summary status counts must not exceed input_count")
        if self.watch_count == ZERO and self.blocked_count == ZERO:
            raise ValueError("terminal summary must contain unresolved rows")
        _require_hard_flags("terminal summary", self)


@dataclass(frozen=True)
class MarketResearchEnergyCrudeExportTerminalDisruptionReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchEnergyCrudeExportTerminalDisruptionReasonCodeCount,
            "reason code count",
        )
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODES)
        object.__setattr__(self, "count", _require_nonnegative_decimal("count", self.count))
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchEnergyCrudeExportTerminalDisruptionDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    thin_source_count: Decimal
    total_expected_outage_hours: Decimal
    total_affected_export_capacity_bpd: Decimal
    max_disruption_probability: Decimal
    max_capacity_loss_ratio: Decimal
    max_vessel_queue_delay_hours: Decimal
    average_disruption_probability: Decimal
    unresolved_input_ratio: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[MarketResearchEnergyCrudeExportTerminalDisruptionDigestRow, ...]
    terminal_summaries: tuple[
        MarketResearchEnergyCrudeExportTerminalDisruptionTerminalSummary,
        ...,
    ]
    reason_code_counts: tuple[
        MarketResearchEnergyCrudeExportTerminalDisruptionReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchEnergyCrudeExportTerminalDisruptionDigestReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_ENERGY_CRUDE_EXPORT_TERMINAL_DISRUPTION_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "thin_source_count",
            "total_expected_outage_hours",
            "total_affected_export_capacity_bpd",
            "max_disruption_probability",
            "max_capacity_loss_ratio",
            "max_vessel_queue_delay_hours",
            "average_disruption_probability",
            "unresolved_input_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_ratio_decimal("max_disruption_probability", self.max_disruption_probability)
        _require_ratio_decimal("max_capacity_loss_ratio", self.max_capacity_loss_ratio)
        _require_ratio_decimal(
            "average_disruption_probability",
            self.average_disruption_probability,
        )
        _require_ratio_decimal("unresolved_input_ratio", self.unresolved_input_ratio)
        _require_member("digest_status", self.digest_status, DIGEST_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "terminal_summaries",
            _normalize_terminal_summaries(self.terminal_summaries),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_energy_crude_export_terminal_disruption_digest(
    inputs: Iterable[MarketResearchEnergyCrudeExportTerminalDisruptionInput],
    *,
    config: MarketResearchEnergyCrudeExportTerminalDisruptionDigestConfig,
    generated_at: datetime,
) -> MarketResearchEnergyCrudeExportTerminalDisruptionDigestReport:
    if type(config) is not MarketResearchEnergyCrudeExportTerminalDisruptionDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchEnergyCrudeExportTerminalDisruptionDigestConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (
                _row_from_input(
                    input_row,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for input_row in input_rows
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    digest_status = _digest_status(rows)
    row_count = _count_decimal(len(rows))

    return MarketResearchEnergyCrudeExportTerminalDisruptionDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count_decimal(len(input_rows)),
        row_count=row_count,
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        thin_source_count=_row_reason_count(rows, THIN_SOURCES_REASON),
        total_expected_outage_hours=_sum_decimal(
            row.expected_outage_hours for row in rows
        ),
        total_affected_export_capacity_bpd=_sum_decimal(
            row.affected_export_capacity_bpd for row in rows
        ),
        max_disruption_probability=_max_row_decimal(
            rows,
            "disruption_probability",
        ),
        max_capacity_loss_ratio=_max_row_decimal(rows, "export_capacity_loss_ratio"),
        max_vessel_queue_delay_hours=_max_row_decimal(
            rows,
            "vessel_queue_delay_hours",
        ),
        average_disruption_probability=_ratio(
            _sum_decimal(row.disruption_probability for row in rows),
            row_count,
        ),
        unresolved_input_ratio=_ratio(
            _status_count(rows, "watch") + _status_count(rows, "blocked"),
            row_count,
        ),
        digest_status=digest_status,
        recommended_next_step=_recommended_next_step(digest_status),
        rows=rows,
        terminal_summaries=_terminal_summaries(rows),
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        reason_codes=reason_codes,
    )


def market_research_energy_crude_export_terminal_disruption_digest_payload(
    report: MarketResearchEnergyCrudeExportTerminalDisruptionDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchEnergyCrudeExportTerminalDisruptionDigestReport:
        raise ValueError(
            "report must be exactly "
            "MarketResearchEnergyCrudeExportTerminalDisruptionDigestReport",
        )
    return _payload_value(report)


def _row_from_input(
    input_row: MarketResearchEnergyCrudeExportTerminalDisruptionInput,
    *,
    config: MarketResearchEnergyCrudeExportTerminalDisruptionDigestConfig,
    generated_at: datetime,
) -> MarketResearchEnergyCrudeExportTerminalDisruptionDigestRow:
    evidence_age_hours = _age_hours(generated_at, input_row.observed_at)
    reason_codes: list[str] = []
    if input_row.disruption_probability >= config.blocked_disruption_probability:
        reason_codes.append(BLOCKED_PROBABILITY_REASON)
    if input_row.export_capacity_loss_ratio >= config.blocked_capacity_loss_ratio:
        reason_codes.append(BLOCKED_CAPACITY_REASON)
    if (
        input_row.disruption_probability >= config.watch_disruption_probability
        and input_row.disruption_probability < config.blocked_disruption_probability
    ):
        reason_codes.append(WATCH_PROBABILITY_REASON)
    if (
        input_row.export_capacity_loss_ratio >= config.watch_capacity_loss_ratio
        and input_row.export_capacity_loss_ratio < config.blocked_capacity_loss_ratio
    ):
        reason_codes.append(WATCH_CAPACITY_REASON)
    if input_row.expected_outage_hours >= config.long_outage_hours:
        reason_codes.append(LONG_OUTAGE_REASON)
    if input_row.vessel_queue_delay_hours >= config.vessel_delay_watch_hours:
        reason_codes.append(VESSEL_DELAY_REASON)
    if evidence_age_hours > config.stale_after_hours:
        reason_codes.append(STALE_EVIDENCE_REASON)
    if input_row.source_count < config.min_source_count:
        reason_codes.append(THIN_SOURCES_REASON)
    if not reason_codes:
        reason_codes.append(INLINE_REASON)

    normalized_reasons = _normalize_reason_codes(
        "reason_codes",
        tuple(reason_codes),
        ROW_REASON_CODES,
    )
    return MarketResearchEnergyCrudeExportTerminalDisruptionDigestRow(
        signal_id=input_row.signal_id,
        terminal_id=input_row.terminal_id,
        terminal_name=input_row.terminal_name,
        region=input_row.region,
        market_slug=input_row.market_slug,
        observed_at=input_row.observed_at,
        digest_status=_status_for_reasons(normalized_reasons),
        source_count=input_row.source_count,
        disruption_probability=input_row.disruption_probability,
        export_capacity_loss_ratio=input_row.export_capacity_loss_ratio,
        expected_outage_hours=input_row.expected_outage_hours,
        affected_export_capacity_bpd=input_row.affected_export_capacity_bpd,
        vessel_queue_delay_hours=input_row.vessel_queue_delay_hours,
        evidence_age_hours=evidence_age_hours,
        redacted_evidence_title=input_row.evidence_title,
        reason_codes=normalized_reasons,
    )


def _terminal_summaries(
    rows: tuple[MarketResearchEnergyCrudeExportTerminalDisruptionDigestRow, ...],
) -> tuple[MarketResearchEnergyCrudeExportTerminalDisruptionTerminalSummary, ...]:
    keys = tuple(
        sorted(
            {
                (row.terminal_id, row.terminal_name, row.region)
                for row in rows
                if row.digest_status in ("watch", "blocked")
            },
        ),
    )
    summaries: list[MarketResearchEnergyCrudeExportTerminalDisruptionTerminalSummary] = []
    for terminal_id, terminal_name, region in keys:
        matching = tuple(row for row in rows if row.terminal_id == terminal_id)
        summaries.append(
            MarketResearchEnergyCrudeExportTerminalDisruptionTerminalSummary(
                terminal_id=terminal_id,
                terminal_name=terminal_name,
                region=region,
                input_count=_count_decimal(len(matching)),
                watch_count=_status_count(matching, "watch"),
                blocked_count=_status_count(matching, "blocked"),
                max_disruption_probability=_max_row_decimal(
                    matching,
                    "disruption_probability",
                ),
                max_capacity_loss_ratio=_max_row_decimal(
                    matching,
                    "export_capacity_loss_ratio",
                ),
                total_expected_outage_hours=_sum_decimal(
                    row.expected_outage_hours for row in matching
                ),
                total_affected_export_capacity_bpd=_sum_decimal(
                    row.affected_export_capacity_bpd for row in matching
                ),
                max_vessel_queue_delay_hours=_max_row_decimal(
                    matching,
                    "vessel_queue_delay_hours",
                ),
            ),
        )
    return tuple(summaries)


def _report_reason_codes(
    rows: tuple[MarketResearchEnergyCrudeExportTerminalDisruptionDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (DIGEST_EMPTY_REASON,)
    if all(row.reason_codes == (INLINE_REASON,) for row in rows):
        return (DIGEST_PASSED_REASON,)
    seen = {reason for row in rows for reason in row.reason_codes}
    seen.discard(INLINE_REASON)
    return tuple(reason for reason in REPORT_REASON_CODES if reason in seen)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[MarketResearchEnergyCrudeExportTerminalDisruptionDigestRow, ...],
) -> tuple[MarketResearchEnergyCrudeExportTerminalDisruptionReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    return tuple(
        MarketResearchEnergyCrudeExportTerminalDisruptionReasonCodeCount(
            reason_code=reason_code,
            count=_report_reason_count(reason_code, rows),
            row_ratio=_ratio(_report_reason_count(reason_code, rows), row_count),
        )
        for reason_code in reason_codes
    )


def _report_reason_count(
    reason_code: str,
    rows: tuple[MarketResearchEnergyCrudeExportTerminalDisruptionDigestRow, ...],
) -> Decimal:
    if reason_code == DIGEST_EMPTY_REASON:
        return ONE
    if reason_code == DIGEST_PASSED_REASON:
        return _count_decimal(sum(1 for row in rows if row.reason_codes == (INLINE_REASON,)))
    return _row_reason_count(rows, reason_code)


def _digest_status(
    rows: tuple[MarketResearchEnergyCrudeExportTerminalDisruptionDigestRow, ...],
) -> str:
    if not rows:
        return "blocked"
    if any(row.digest_status == "blocked" for row in rows):
        return "blocked"
    if any(row.digest_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _recommended_next_step(digest_status: str) -> str:
    if digest_status == "pass":
        return ALLOW_NEXT_STEP
    if digest_status == "watch":
        return MONITOR_NEXT_STEP
    return BLOCK_NEXT_STEP


def _status_for_reasons(reason_codes: tuple[str, ...]) -> str:
    if (
        BLOCKED_PROBABILITY_REASON in reason_codes
        or BLOCKED_CAPACITY_REASON in reason_codes
    ):
        return "blocked"
    if reason_codes == (INLINE_REASON,):
        return "pass"
    return "watch"


def _validate_row(
    row: MarketResearchEnergyCrudeExportTerminalDisruptionDigestRow,
) -> None:
    if row.digest_status != _status_for_reasons(row.reason_codes):
        raise ValueError("reason_codes must match digest_status")
    if row.digest_status == "pass" and row.reason_codes != (INLINE_REASON,):
        raise ValueError("reason_codes must match digest_status")
    if row.digest_status != "pass" and INLINE_REASON in row.reason_codes:
        raise ValueError("reason_codes must match digest_status")


def _validate_report(
    report: MarketResearchEnergyCrudeExportTerminalDisruptionDigestReport,
) -> None:
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.pass_count + report.watch_count + report.blocked_count != report.row_count:
        raise ValueError("status counts must match rows")
    if report.thin_source_count != _row_reason_count(report.rows, THIN_SOURCES_REASON):
        raise ValueError("thin_source_count must match rows")
    if report.total_expected_outage_hours != _sum_decimal(
        row.expected_outage_hours for row in report.rows
    ):
        raise ValueError("total_expected_outage_hours must match rows")
    if report.total_affected_export_capacity_bpd != _sum_decimal(
        row.affected_export_capacity_bpd for row in report.rows
    ):
        raise ValueError("total_affected_export_capacity_bpd must match rows")
    if report.max_disruption_probability != _max_row_decimal(
        report.rows,
        "disruption_probability",
    ):
        raise ValueError("max_disruption_probability must match rows")
    if report.max_capacity_loss_ratio != _max_row_decimal(
        report.rows,
        "export_capacity_loss_ratio",
    ):
        raise ValueError("max_capacity_loss_ratio must match rows")
    if report.max_vessel_queue_delay_hours != _max_row_decimal(
        report.rows,
        "vessel_queue_delay_hours",
    ):
        raise ValueError("max_vessel_queue_delay_hours must match rows")
    if report.average_disruption_probability != _ratio(
        _sum_decimal(row.disruption_probability for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_disruption_probability must match rows")
    if report.unresolved_input_ratio != _ratio(
        report.watch_count + report.blocked_count,
        report.row_count,
    ):
        raise ValueError("unresolved_input_ratio must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(
        report.reason_codes,
        report.rows,
    ):
        raise ValueError("reason_code_counts must match reason_codes")
    if report.terminal_summaries != _terminal_summaries(report.rows):
        raise ValueError("terminal_summaries must match rows")


def _normalize_inputs(
    inputs: Iterable[MarketResearchEnergyCrudeExportTerminalDisruptionInput],
) -> tuple[MarketResearchEnergyCrudeExportTerminalDisruptionInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Iterable):
        raise ValueError(
            "inputs must contain "
            "MarketResearchEnergyCrudeExportTerminalDisruptionInput values",
        )
    normalized = tuple(inputs)
    seen_signal_ids: set[str] = set()
    for input_row in normalized:
        if type(input_row) is not MarketResearchEnergyCrudeExportTerminalDisruptionInput:
            raise ValueError(
                "inputs must contain "
                "MarketResearchEnergyCrudeExportTerminalDisruptionInput values",
            )
        _require_hard_flags("input row", input_row)
        if input_row.signal_id in seen_signal_ids:
            raise ValueError("inputs must not contain duplicate signal_id values")
        seen_signal_ids.add(input_row.signal_id)
    return normalized


def _normalize_rows(
    rows: Iterable[MarketResearchEnergyCrudeExportTerminalDisruptionDigestRow],
) -> tuple[MarketResearchEnergyCrudeExportTerminalDisruptionDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError(
            "rows must contain "
            "MarketResearchEnergyCrudeExportTerminalDisruptionDigestRow values",
        )
    normalized = tuple(rows)
    seen_signal_ids: set[str] = set()
    for row in normalized:
        if type(row) is not MarketResearchEnergyCrudeExportTerminalDisruptionDigestRow:
            raise ValueError(
                "rows must contain "
                "MarketResearchEnergyCrudeExportTerminalDisruptionDigestRow values",
            )
        _require_hard_flags("row", row)
        if row.signal_id in seen_signal_ids:
            raise ValueError("rows must not contain duplicate signal_id values")
        seen_signal_ids.add(row.signal_id)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_terminal_summaries(
    summaries: Iterable[MarketResearchEnergyCrudeExportTerminalDisruptionTerminalSummary],
) -> tuple[MarketResearchEnergyCrudeExportTerminalDisruptionTerminalSummary, ...]:
    if isinstance(summaries, (str, bytes)) or not isinstance(summaries, Iterable):
        raise ValueError(
            "terminal_summaries must contain "
            "MarketResearchEnergyCrudeExportTerminalDisruptionTerminalSummary values",
        )
    normalized = tuple(summaries)
    seen_terminal_ids: set[str] = set()
    for summary in normalized:
        if type(summary) is not MarketResearchEnergyCrudeExportTerminalDisruptionTerminalSummary:
            raise ValueError(
                "terminal_summaries must contain "
                "MarketResearchEnergyCrudeExportTerminalDisruptionTerminalSummary values",
            )
        _require_hard_flags("terminal summary", summary)
        if summary.terminal_id in seen_terminal_ids:
            raise ValueError(
                "terminal_summaries must not contain duplicate terminal_id values",
            )
        seen_terminal_ids.add(summary.terminal_id)
    return tuple(sorted(normalized, key=lambda summary: summary.terminal_id))


def _normalize_reason_code_counts(
    values: Iterable[MarketResearchEnergyCrudeExportTerminalDisruptionReasonCodeCount],
) -> tuple[MarketResearchEnergyCrudeExportTerminalDisruptionReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError(
            "reason_code_counts must contain "
            "MarketResearchEnergyCrudeExportTerminalDisruptionReasonCodeCount values",
        )
    normalized = tuple(values)
    for value in normalized:
        if type(value) is not MarketResearchEnergyCrudeExportTerminalDisruptionReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchEnergyCrudeExportTerminalDisruptionReasonCodeCount values",
            )
        _require_hard_flags("reason code count", value)
    return tuple(
        sorted(
            normalized,
            key=lambda value: REPORT_REASON_CODES.index(value.reason_code),
        ),
    )


def _normalize_reason_codes(
    field_name: str,
    values: Iterable[str],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError(f"{field_name} must contain reason code strings")
    normalized = tuple(values)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    for value in normalized:
        _require_canonical_string("reason_code", value)
        if value not in allowed:
            raise ValueError(f"{field_name} must contain supported values")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    if INLINE_REASON in normalized and normalized != (INLINE_REASON,):
        raise ValueError(f"{field_name} inline reason must be exclusive")
    if DIGEST_PASSED_REASON in normalized and normalized != (DIGEST_PASSED_REASON,):
        raise ValueError(f"{field_name} pass reason must be exclusive")
    if DIGEST_EMPTY_REASON in normalized and normalized != (DIGEST_EMPTY_REASON,):
        raise ValueError(f"{field_name} empty reason must be exclusive")
    return tuple(reason for reason in allowed if reason in normalized)


def _row_sort_key(
    row: MarketResearchEnergyCrudeExportTerminalDisruptionDigestRow,
) -> tuple[int, Decimal, Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.digest_status],
        -row.disruption_probability,
        -row.export_capacity_loss_ratio,
        -row.vessel_queue_delay_hours,
        row.terminal_id,
        row.signal_id,
    )


def _status_count(
    rows: tuple[MarketResearchEnergyCrudeExportTerminalDisruptionDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.digest_status == status))


def _row_reason_count(
    rows: tuple[MarketResearchEnergyCrudeExportTerminalDisruptionDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_row_decimal(
    rows: tuple[MarketResearchEnergyCrudeExportTerminalDisruptionDigestRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimal values")
        total += value
    return _quantize_decimal(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(numerator / denominator)


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _age_hours(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    if delta.total_seconds() < 0:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(Decimal(str(delta.total_seconds())) / Decimal("3600"))


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
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
    quantized = _quantize_decimal(value)
    if quantized != value:
        raise ValueError(f"{field_name} must have at most 6 decimal places")
    return quantized


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_integral_decimal(field_name: str, value: Decimal) -> None:
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value or _CANONICAL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_trimmed_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonblank trimmed string")
    return value


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must contain supported values")


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


def _redact(value: object) -> str:
    text = _require_trimmed_string("redacted text", value)
    text = _LINK_PATTERN.sub("[REDACTED_URL]", text)
    text = _EMAIL_PATTERN.sub("[REDACTED_EMAIL]", text)
    return _HEX_ADDRESS_PATTERN.sub("[REDACTED_" + "W" + "ALLET]", text)


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
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
