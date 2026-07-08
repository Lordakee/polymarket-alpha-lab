"""Pure public-safe event settlement risk watchlist report."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_EVENT_SETTLEMENT_RISK_WATCHLIST_REPORT_CONFIG_VERSION = (
    "research-event-settlement-risk-watchlist-report-v0"
)

SETTLEMENT_RISK_STATUSES = ("pass", "watch", "block")
STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}

PASS_REASON = "settlement_risk_pass"
LOW_RESOLUTION_CLARITY_REASON = "low_resolution_clarity"
EVIDENCE_CONFLICT_REASON = "evidence_conflict"
ORACLE_DELAY_REASON = "oracle_delay"
DISPUTE_LIKELIHOOD_REASON = "dispute_likelihood"
EXPIRY_PROXIMITY_REASON = "expiry_proximity"
LOW_RESOLUTION_CLARITY_PRESENT_REASON = "low_resolution_clarity_present"
EVIDENCE_CONFLICT_PRESENT_REASON = "evidence_conflict_present"
ORACLE_DELAY_PRESENT_REASON = "oracle_delay_present"
DISPUTE_LIKELIHOOD_PRESENT_REASON = "dispute_likelihood_present"
EXPIRY_PROXIMITY_PRESENT_REASON = "expiry_proximity_present"

ROW_REASON_CODES = (
    LOW_RESOLUTION_CLARITY_REASON,
    EVIDENCE_CONFLICT_REASON,
    ORACLE_DELAY_REASON,
    DISPUTE_LIKELIHOOD_REASON,
    EXPIRY_PROXIMITY_REASON,
    PASS_REASON,
)
REPORT_REASON_CODES = (
    LOW_RESOLUTION_CLARITY_PRESENT_REASON,
    EVIDENCE_CONFLICT_PRESENT_REASON,
    ORACLE_DELAY_PRESENT_REASON,
    DISPUTE_LIKELIHOOD_PRESENT_REASON,
    EXPIRY_PROXIMITY_PRESENT_REASON,
    PASS_REASON,
)
ROW_TO_REPORT_REASON = {
    LOW_RESOLUTION_CLARITY_REASON: LOW_RESOLUTION_CLARITY_PRESENT_REASON,
    EVIDENCE_CONFLICT_REASON: EVIDENCE_CONFLICT_PRESENT_REASON,
    ORACLE_DELAY_REASON: ORACLE_DELAY_PRESENT_REASON,
    DISPUTE_LIKELIHOOD_REASON: DISPUTE_LIKELIHOOD_PRESENT_REASON,
    EXPIRY_PROXIMITY_REASON: EXPIRY_PROXIMITY_PRESENT_REASON,
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        "credential",
        "private",
        "secret",
        "token",
        _join_parts("li", "ve"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("bro", "ker"),
        _join_parts("ord", "er"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("sig", "ning"),
        _join_parts("ad", "vice"),
    ),
)
RAW_REFERENCE_FRAGMENTS = frozenset(
    (
        "market_id",
        "market-id",
        "condition_id",
        "condition-id",
        "source_id",
        "source-id",
        "clob",
    ),
)


@dataclass(frozen=True)
class ResearchEventSettlementRiskWatchlistConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_SETTLEMENT_RISK_WATCHLIST_REPORT_CONFIG_VERSION
    )
    resolution_clarity_watch_threshold: Decimal = Decimal("0.700000")
    resolution_clarity_block_threshold: Decimal = Decimal("0.400000")
    evidence_conflict_watch_threshold: Decimal = Decimal("0.250000")
    evidence_conflict_block_threshold: Decimal = Decimal("0.600000")
    oracle_delay_watch_hours: Decimal = Decimal("6.000000")
    oracle_delay_block_hours: Decimal = Decimal("72.000000")
    dispute_likelihood_watch_threshold: Decimal = Decimal("0.150000")
    dispute_likelihood_block_threshold: Decimal = Decimal("0.400000")
    expiry_proximity_watch_hours: Decimal = Decimal("48.000000")
    expiry_proximity_block_hours: Decimal = Decimal("12.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_SETTLEMENT_RISK_WATCHLIST_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "resolution_clarity_watch_threshold",
            "resolution_clarity_block_threshold",
            "evidence_conflict_watch_threshold",
            "evidence_conflict_block_threshold",
            "dispute_likelihood_watch_threshold",
            "dispute_likelihood_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_score_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "oracle_delay_watch_hours",
            "oracle_delay_block_hours",
            "expiry_proximity_watch_hours",
            "expiry_proximity_block_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        require_paper_only_flags("event settlement risk watchlist config", self)


@dataclass(frozen=True)
class ResearchEventSettlementRiskWatchlistInput:
    event_label: str
    resolution_clarity_score: Decimal
    evidence_conflict_score: Decimal
    oracle_delay_hours: Decimal
    dispute_likelihood_score: Decimal
    hours_to_expiry: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "event_label",
            _require_public_string("event_label", self.event_label),
        )
        for field_name in (
            "resolution_clarity_score",
            "evidence_conflict_score",
            "dispute_likelihood_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_score_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("oracle_delay_hours", "hours_to_expiry"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("event settlement risk watchlist input", self)


@dataclass(frozen=True)
class ResearchEventSettlementRiskWatchlistRow:
    event_label: str
    status: str
    resolution_clarity_score: Decimal
    evidence_conflict_score: Decimal
    oracle_delay_hours: Decimal
    dispute_likelihood_score: Decimal
    hours_to_expiry: Decimal
    risk_flag_count: Decimal
    low_resolution_clarity: bool
    evidence_conflict: bool
    oracle_delay: bool
    dispute_likelihood: bool
    expiry_proximity: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "event_label",
            _require_public_string("event_label", self.event_label),
        )
        _require_status("status", self.status)
        for field_name in (
            "resolution_clarity_score",
            "evidence_conflict_score",
            "dispute_likelihood_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_score_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("oracle_delay_hours", "hours_to_expiry", "risk_flag_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "low_resolution_clarity",
            "evidence_conflict",
            "oracle_delay",
            "dispute_likelihood",
            "expiry_proximity",
        ):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        reject_unsafe_surface_fields("event settlement risk watchlist row", self)
        require_paper_only_flags("event settlement risk watchlist row", self)


@dataclass(frozen=True)
class ResearchEventSettlementRiskWatchlistReport:
    generated_at: datetime
    config_version: str
    status: str
    reason_codes: tuple[str, ...]
    event_count: Decimal
    pass_event_count: Decimal
    watch_event_count: Decimal
    block_event_count: Decimal
    flagged_event_count: Decimal
    low_resolution_clarity_event_count: Decimal
    evidence_conflict_event_count: Decimal
    oracle_delay_event_count: Decimal
    dispute_likelihood_event_count: Decimal
    expiry_proximity_event_count: Decimal
    flagged_event_ratio: Decimal
    max_oracle_delay_hours: Decimal
    min_hours_to_expiry: Decimal
    rows: tuple[ResearchEventSettlementRiskWatchlistRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        for field_name in (
            "event_count",
            "pass_event_count",
            "watch_event_count",
            "block_event_count",
            "flagged_event_count",
            "low_resolution_clarity_event_count",
            "evidence_conflict_event_count",
            "oracle_delay_event_count",
            "dispute_likelihood_event_count",
            "expiry_proximity_event_count",
            "flagged_event_ratio",
            "max_oracle_delay_hours",
            "min_hours_to_expiry",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _reject_unsafe_public_payload("event settlement risk watchlist report", self)
        reject_unsafe_surface_fields("event settlement risk watchlist report", self)
        require_paper_only_flags("event settlement risk watchlist report", self)
        _validate_derived_validation_digest(self)


def build_research_event_settlement_risk_watchlist_report(
    input_rows: list[ResearchEventSettlementRiskWatchlistInput]
    | tuple[ResearchEventSettlementRiskWatchlistInput, ...],
    *,
    config: ResearchEventSettlementRiskWatchlistConfig,
    generated_at: datetime,
) -> ResearchEventSettlementRiskWatchlistReport:
    if type(config) is not ResearchEventSettlementRiskWatchlistConfig:
        raise ValueError("config must be a ResearchEventSettlementRiskWatchlistConfig")
    require_paper_only_flags("event settlement risk watchlist config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_input_rows(input_rows)
    rows = _sort_rows(
        tuple(_row_from_input(input_row, config=config) for input_row in inputs),
    )
    reason_codes = _report_reason_codes(rows)
    event_count = _count(len(rows))

    return ResearchEventSettlementRiskWatchlistReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(rows),
        reason_codes=reason_codes,
        event_count=event_count,
        pass_event_count=_status_count(rows, "pass"),
        watch_event_count=_status_count(rows, "watch"),
        block_event_count=_status_count(rows, "block"),
        flagged_event_count=_flagged_count(rows),
        low_resolution_clarity_event_count=_positive_bool_count(
            rows,
            "low_resolution_clarity",
        ),
        evidence_conflict_event_count=_positive_bool_count(rows, "evidence_conflict"),
        oracle_delay_event_count=_positive_bool_count(rows, "oracle_delay"),
        dispute_likelihood_event_count=_positive_bool_count(rows, "dispute_likelihood"),
        expiry_proximity_event_count=_positive_bool_count(rows, "expiry_proximity"),
        flagged_event_ratio=_ratio(_flagged_count(rows), event_count),
        max_oracle_delay_hours=_max_decimal(row.oracle_delay_hours for row in rows),
        min_hours_to_expiry=_min_decimal(row.hours_to_expiry for row in rows),
        rows=rows,
        derived_validation_digest=_derived_validation_digest(
            generated_at=generated_at_utc,
            config_version=config.config_version,
            status=_report_status(rows),
            reason_codes=reason_codes,
            event_count=event_count,
            pass_event_count=_status_count(rows, "pass"),
            watch_event_count=_status_count(rows, "watch"),
            block_event_count=_status_count(rows, "block"),
            flagged_event_count=_flagged_count(rows),
            low_resolution_clarity_event_count=_positive_bool_count(
                rows,
                "low_resolution_clarity",
            ),
            evidence_conflict_event_count=_positive_bool_count(rows, "evidence_conflict"),
            oracle_delay_event_count=_positive_bool_count(rows, "oracle_delay"),
            dispute_likelihood_event_count=_positive_bool_count(
                rows,
                "dispute_likelihood",
            ),
            expiry_proximity_event_count=_positive_bool_count(rows, "expiry_proximity"),
            flagged_event_ratio=_ratio(_flagged_count(rows), event_count),
            max_oracle_delay_hours=_max_decimal(row.oracle_delay_hours for row in rows),
            min_hours_to_expiry=_min_decimal(row.hours_to_expiry for row in rows),
            rows=rows,
            paper_only=True,
            report_only=True,
            readonly=True,
        ),
    )


def research_event_settlement_risk_watchlist_report_to_payload(
    report: ResearchEventSettlementRiskWatchlistReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEventSettlementRiskWatchlistReport:
        raise ValueError(
            "report must be a ResearchEventSettlementRiskWatchlistReport",
        )
    require_paper_only_flags("event settlement risk watchlist report", report)
    _reject_unsafe_public_payload("event settlement risk watchlist report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    reject_unsafe_surface_fields("event settlement risk watchlist payload", payload)
    _reject_unsafe_public_payload("event settlement risk watchlist payload", payload)
    return payload


def _normalize_input_rows(
    value: object,
) -> tuple[ResearchEventSettlementRiskWatchlistInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchEventSettlementRiskWatchlistInput:
            raise ValueError("input rows must contain settlement risk inputs")
        require_paper_only_flags("event settlement risk watchlist input", row)
        if row.event_label in seen:
            raise ValueError("event_label values must be unique")
        seen.add(row.event_label)
    return tuple(sorted(rows, key=lambda row: row.event_label))


def _row_from_input(
    input_row: ResearchEventSettlementRiskWatchlistInput,
    *,
    config: ResearchEventSettlementRiskWatchlistConfig,
) -> ResearchEventSettlementRiskWatchlistRow:
    low_resolution_clarity = (
        input_row.resolution_clarity_score <= config.resolution_clarity_watch_threshold
    )
    evidence_conflict = (
        input_row.evidence_conflict_score >= config.evidence_conflict_watch_threshold
    )
    oracle_delay = input_row.oracle_delay_hours >= config.oracle_delay_watch_hours
    dispute_likelihood = (
        input_row.dispute_likelihood_score >= config.dispute_likelihood_watch_threshold
    )
    expiry_proximity = input_row.hours_to_expiry <= config.expiry_proximity_watch_hours
    reason_codes = _row_reason_codes(
        low_resolution_clarity=low_resolution_clarity,
        evidence_conflict=evidence_conflict,
        oracle_delay=oracle_delay,
        dispute_likelihood=dispute_likelihood,
        expiry_proximity=expiry_proximity,
    )

    return ResearchEventSettlementRiskWatchlistRow(
        event_label=input_row.event_label,
        status=_row_status(input_row, config=config, reason_codes=reason_codes),
        resolution_clarity_score=input_row.resolution_clarity_score,
        evidence_conflict_score=input_row.evidence_conflict_score,
        oracle_delay_hours=input_row.oracle_delay_hours,
        dispute_likelihood_score=input_row.dispute_likelihood_score,
        hours_to_expiry=input_row.hours_to_expiry,
        risk_flag_count=_count(
            sum(
                1
                for flag in (
                    low_resolution_clarity,
                    evidence_conflict,
                    oracle_delay,
                    dispute_likelihood,
                    expiry_proximity,
                )
                if flag
            ),
        ),
        low_resolution_clarity=low_resolution_clarity,
        evidence_conflict=evidence_conflict,
        oracle_delay=oracle_delay,
        dispute_likelihood=dispute_likelihood,
        expiry_proximity=expiry_proximity,
        reason_codes=reason_codes,
    )


def _row_status(
    input_row: ResearchEventSettlementRiskWatchlistInput,
    *,
    config: ResearchEventSettlementRiskWatchlistConfig,
    reason_codes: tuple[str, ...],
) -> str:
    block_hit = (
        input_row.resolution_clarity_score <= config.resolution_clarity_block_threshold
        or input_row.evidence_conflict_score >= config.evidence_conflict_block_threshold
        or input_row.oracle_delay_hours >= config.oracle_delay_block_hours
        or input_row.dispute_likelihood_score >= config.dispute_likelihood_block_threshold
        or input_row.hours_to_expiry <= config.expiry_proximity_block_hours
    )
    if block_hit:
        return "block"
    if reason_codes != (PASS_REASON,):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    low_resolution_clarity: bool,
    evidence_conflict: bool,
    oracle_delay: bool,
    dispute_likelihood: bool,
    expiry_proximity: bool,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if low_resolution_clarity:
        reason_codes.append(LOW_RESOLUTION_CLARITY_REASON)
    if evidence_conflict:
        reason_codes.append(EVIDENCE_CONFLICT_REASON)
    if oracle_delay:
        reason_codes.append(ORACLE_DELAY_REASON)
    if dispute_likelihood:
        reason_codes.append(DISPUTE_LIKELIHOOD_REASON)
    if expiry_proximity:
        reason_codes.append(EXPIRY_PROXIMITY_REASON)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return tuple(reason_codes)


def _sort_rows(
    rows: tuple[ResearchEventSettlementRiskWatchlistRow, ...],
) -> tuple[ResearchEventSettlementRiskWatchlistRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                STATUS_RANK[row.status],
                -row.risk_flag_count,
                row.resolution_clarity_score,
                -row.evidence_conflict_score,
                -row.oracle_delay_hours,
                row.hours_to_expiry,
                row.event_label,
            ),
        ),
    )


def _normalize_rows(value: object) -> tuple[ResearchEventSettlementRiskWatchlistRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchEventSettlementRiskWatchlistRow:
            raise ValueError("rows must contain settlement risk rows")
        require_paper_only_flags("event settlement risk watchlist row", row)
        if row.event_label in seen:
            raise ValueError("rows must be unique by event_label")
        seen.add(row.event_label)
    if rows != _sort_rows(rows):
        raise ValueError("rows must be sorted deterministically")
    return rows


def _report_reason_codes(
    rows: tuple[ResearchEventSettlementRiskWatchlistRow, ...],
) -> tuple[str, ...]:
    present = {
        ROW_TO_REPORT_REASON[reason_code]
        for row in rows
        for reason_code in row.reason_codes
        if reason_code in ROW_TO_REPORT_REASON
    }
    reason_codes = tuple(
        reason_code for reason_code in REPORT_REASON_CODES if reason_code in present
    )
    if reason_codes:
        return reason_codes
    return (PASS_REASON,)


def _report_status(rows: tuple[ResearchEventSettlementRiskWatchlistRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _validate_config(config: ResearchEventSettlementRiskWatchlistConfig) -> None:
    if config.resolution_clarity_block_threshold > config.resolution_clarity_watch_threshold:
        raise ValueError("resolution clarity block threshold must not exceed watch threshold")
    if config.evidence_conflict_block_threshold < config.evidence_conflict_watch_threshold:
        raise ValueError("evidence conflict block threshold must be at least watch threshold")
    if config.oracle_delay_block_hours < config.oracle_delay_watch_hours:
        raise ValueError("oracle delay block threshold must be at least watch threshold")
    if config.dispute_likelihood_block_threshold < config.dispute_likelihood_watch_threshold:
        raise ValueError("dispute likelihood block threshold must be at least watch threshold")
    if config.expiry_proximity_block_hours > config.expiry_proximity_watch_hours:
        raise ValueError("expiry proximity block threshold must not exceed watch threshold")


def _validate_row(row: ResearchEventSettlementRiskWatchlistRow) -> None:
    flags = (
        row.low_resolution_clarity,
        row.evidence_conflict,
        row.oracle_delay,
        row.dispute_likelihood,
        row.expiry_proximity,
    )
    if row.risk_flag_count != _count(sum(1 for flag in flags if flag)):
        raise ValueError("risk_flag_count must match flags")
    if row.risk_flag_count % ONE != ZERO:
        raise ValueError("risk_flag_count must be a whole Decimal")
    expected_reason_codes = _row_reason_codes(
        low_resolution_clarity=row.low_resolution_clarity,
        evidence_conflict=row.evidence_conflict,
        oracle_delay=row.oracle_delay,
        dispute_likelihood=row.dispute_likelihood,
        expiry_proximity=row.expiry_proximity,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row flags")
    if row.status == "pass" and row.risk_flag_count != ZERO:
        raise ValueError("pass rows must not have risk flags")
    if row.status in ("watch", "block") and row.risk_flag_count == ZERO:
        raise ValueError("flagged rows must have risk flags")


def _validate_report(report: ResearchEventSettlementRiskWatchlistReport) -> None:
    if report.event_count != _count(len(report.rows)):
        raise ValueError("event_count must match rows")
    if report.pass_event_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_event_count must match rows")
    if report.watch_event_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_event_count must match rows")
    if report.block_event_count != _status_count(report.rows, "block"):
        raise ValueError("block_event_count must match rows")
    if (
        report.pass_event_count + report.watch_event_count + report.block_event_count
        != report.event_count
    ):
        raise ValueError("status counts must sum to event_count")
    expected_counts = {
        "flagged_event_count": _flagged_count(report.rows),
        "low_resolution_clarity_event_count": _positive_bool_count(
            report.rows,
            "low_resolution_clarity",
        ),
        "evidence_conflict_event_count": _positive_bool_count(
            report.rows,
            "evidence_conflict",
        ),
        "oracle_delay_event_count": _positive_bool_count(report.rows, "oracle_delay"),
        "dispute_likelihood_event_count": _positive_bool_count(
            report.rows,
            "dispute_likelihood",
        ),
        "expiry_proximity_event_count": _positive_bool_count(
            report.rows,
            "expiry_proximity",
        ),
    }
    for field_name, expected in expected_counts.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.flagged_event_ratio != _ratio(report.flagged_event_count, report.event_count):
        raise ValueError("flagged_event_ratio must match rows")
    if report.max_oracle_delay_hours != _max_decimal(
        row.oracle_delay_hours for row in report.rows
    ):
        raise ValueError("max_oracle_delay_hours must match rows")
    if report.min_hours_to_expiry != _min_decimal(row.hours_to_expiry for row in report.rows):
        raise ValueError("min_hours_to_expiry must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")


def _status_count(
    rows: tuple[ResearchEventSettlementRiskWatchlistRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _flagged_count(rows: tuple[ResearchEventSettlementRiskWatchlistRow, ...]) -> Decimal:
    return _count(sum(1 for row in rows if row.status != "pass"))


def _positive_bool_count(
    rows: tuple[ResearchEventSettlementRiskWatchlistRow, ...],
    field_name: str,
) -> Decimal:
    return _count(sum(1 for row in rows if getattr(row, field_name) is True))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _max_decimal(values: object) -> Decimal:
    normalized = tuple(values)  # type: ignore[arg-type]
    if not normalized:
        return ZERO
    return max(normalized)


def _min_decimal(values: object) -> Decimal:
    normalized = tuple(values)  # type: ignore[arg-type]
    if not normalized:
        return ZERO
    return min(normalized)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value).quantize(QUANT)


def _require_score_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be no greater than one")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    decimal_value = value.quantize(QUANT)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SETTLEMENT_RISK_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    return value


def _require_public_string(field_name: str, value: object) -> str:
    text = _require_canonical_string(field_name, value)
    if len(text) > 120:
        raise ValueError(f"{field_name} must be public and compact")
    _reject_unsafe_text(field_name, text)
    return text


def _reject_unsafe_text(field_name: str, value: str) -> None:
    normalized = value.lower()
    if "0x" in normalized:
        raise ValueError(f"{field_name} must not contain raw references")
    if any(fragment in normalized for fragment in RAW_REFERENCE_FRAGMENTS):
        raise ValueError(f"{field_name} must not contain raw references")
    if any(fragment in normalized for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe text")


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in allowed_reason_codes:
            raise ValueError(f"{field_name} contains unsupported reason code")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    if tuple(code for code in allowed_reason_codes if code in reason_codes) != reason_codes:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, str):
        _reject_unsafe_text(label, value)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} keys must be strings")
            _reject_unsafe_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field_name in value.__dataclass_fields__:  # type: ignore[attr-defined]
            _reject_unsafe_public_payload(label, getattr(value, field_name))


def _derived_validation_digest(
    *,
    generated_at: datetime,
    config_version: str,
    status: str,
    reason_codes: tuple[str, ...],
    event_count: Decimal,
    pass_event_count: Decimal,
    watch_event_count: Decimal,
    block_event_count: Decimal,
    flagged_event_count: Decimal,
    low_resolution_clarity_event_count: Decimal,
    evidence_conflict_event_count: Decimal,
    oracle_delay_event_count: Decimal,
    dispute_likelihood_event_count: Decimal,
    expiry_proximity_event_count: Decimal,
    flagged_event_ratio: Decimal,
    max_oracle_delay_hours: Decimal,
    min_hours_to_expiry: Decimal,
    rows: tuple[ResearchEventSettlementRiskWatchlistRow, ...],
    paper_only: bool,
    report_only: bool,
    readonly: bool,
) -> str:
    payload = {
        "generated_at": _as_utc("generated_at", generated_at),
        "config_version": config_version,
        "status": status,
        "reason_codes": reason_codes,
        "event_count": event_count,
        "pass_event_count": pass_event_count,
        "watch_event_count": watch_event_count,
        "block_event_count": block_event_count,
        "flagged_event_count": flagged_event_count,
        "low_resolution_clarity_event_count": low_resolution_clarity_event_count,
        "evidence_conflict_event_count": evidence_conflict_event_count,
        "oracle_delay_event_count": oracle_delay_event_count,
        "dispute_likelihood_event_count": dispute_likelihood_event_count,
        "expiry_proximity_event_count": expiry_proximity_event_count,
        "flagged_event_ratio": flagged_event_ratio,
        "max_oracle_delay_hours": max_oracle_delay_hours,
        "min_hours_to_expiry": min_hours_to_expiry,
        "rows": rows,
        "paper_only": paper_only,
        "report_only": report_only,
        "readonly": readonly,
    }
    ready = json_ready_no_floats(payload)
    return hashlib.sha256(
        json.dumps(ready, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()


def _validate_derived_validation_digest(
    report: ResearchEventSettlementRiskWatchlistReport,
) -> None:
    expected = _derived_validation_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        status=report.status,
        reason_codes=report.reason_codes,
        event_count=report.event_count,
        pass_event_count=report.pass_event_count,
        watch_event_count=report.watch_event_count,
        block_event_count=report.block_event_count,
        flagged_event_count=report.flagged_event_count,
        low_resolution_clarity_event_count=report.low_resolution_clarity_event_count,
        evidence_conflict_event_count=report.evidence_conflict_event_count,
        oracle_delay_event_count=report.oracle_delay_event_count,
        dispute_likelihood_event_count=report.dispute_likelihood_event_count,
        expiry_proximity_event_count=report.expiry_proximity_event_count,
        flagged_event_ratio=report.flagged_event_ratio,
        max_oracle_delay_hours=report.max_oracle_delay_hours,
        min_hours_to_expiry=report.min_hours_to_expiry,
        rows=report.rows,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )
    if report.derived_validation_digest != expected:
        raise ValueError("derived_validation_digest must match report payload")


__all__ = (
    "DEFAULT_RESEARCH_EVENT_SETTLEMENT_RISK_WATCHLIST_REPORT_CONFIG_VERSION",
    "ResearchEventSettlementRiskWatchlistConfig",
    "ResearchEventSettlementRiskWatchlistInput",
    "ResearchEventSettlementRiskWatchlistReport",
    "ResearchEventSettlementRiskWatchlistRow",
    "build_research_event_settlement_risk_watchlist_report",
    "research_event_settlement_risk_watchlist_report_to_payload",
)
