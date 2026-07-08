"""Pure public-safe catalyst volatility pressure report by domain."""

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


DEFAULT_RESEARCH_EVENT_CATALYST_VOLATILITY_PRESSURE_REPORT_CONFIG_VERSION = (
    "research-event-catalyst-volatility-pressure-report-v0"
)

VOLATILITY_PRESSURE_STATUSES = ("pass", "watch", "block")
STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}

PASS_REASON = "volatility_pressure_pass"
CATALYST_RECENCY_REASON = "catalyst_recency"
EVIDENCE_CONTRADICTION_REASON = "evidence_contradiction"
LIQUIDITY_STRESS_REASON = "liquidity_stress"
PROBABILITY_MOVEMENT_REASON = "probability_movement"
RESOLUTION_PROXIMITY_REASON = "resolution_proximity"
CATALYST_RECENCY_PRESENT_REASON = "catalyst_recency_present"
EVIDENCE_CONTRADICTION_PRESENT_REASON = "evidence_contradiction_present"
LIQUIDITY_STRESS_PRESENT_REASON = "liquidity_stress_present"
PROBABILITY_MOVEMENT_PRESENT_REASON = "probability_movement_present"
RESOLUTION_PROXIMITY_PRESENT_REASON = "resolution_proximity_present"

ROW_REASON_CODES = (
    CATALYST_RECENCY_REASON,
    EVIDENCE_CONTRADICTION_REASON,
    LIQUIDITY_STRESS_REASON,
    PROBABILITY_MOVEMENT_REASON,
    RESOLUTION_PROXIMITY_REASON,
    PASS_REASON,
)
REPORT_REASON_CODES = (
    CATALYST_RECENCY_PRESENT_REASON,
    EVIDENCE_CONTRADICTION_PRESENT_REASON,
    LIQUIDITY_STRESS_PRESENT_REASON,
    PROBABILITY_MOVEMENT_PRESENT_REASON,
    RESOLUTION_PROXIMITY_PRESENT_REASON,
    PASS_REASON,
)
ROW_TO_REPORT_REASON = {
    CATALYST_RECENCY_REASON: CATALYST_RECENCY_PRESENT_REASON,
    EVIDENCE_CONTRADICTION_REASON: EVIDENCE_CONTRADICTION_PRESENT_REASON,
    LIQUIDITY_STRESS_REASON: LIQUIDITY_STRESS_PRESENT_REASON,
    PROBABILITY_MOVEMENT_REASON: PROBABILITY_MOVEMENT_PRESENT_REASON,
    RESOLUTION_PROXIMITY_REASON: RESOLUTION_PROXIMITY_PRESENT_REASON,
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
        _join_parts("li", "ve"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("bro", "ker"),
        _join_parts("ord", "er"),
        _join_parts("tr", "ade"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("sig", "ning"),
        _join_parts("b", "uy"),
        _join_parts("s", "ell"),
        _join_parts("rec", "ommend"),
        _join_parts("pos", "ition"),
    ),
)
RAW_REFERENCE_FRAGMENTS = frozenset(
    (
        _join_parts("eve", "nt_id"),
        "event-id",
        _join_parts("mar", "ket_id"),
        "market-id",
        _join_parts("sou", "rce_id"),
        "source-id",
        _join_parts("condition", "_id"),
        "condition-id",
        "clob",
        "0x",
    ),
)


@dataclass(frozen=True)
class ResearchEventCatalystVolatilityPressureConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_CATALYST_VOLATILITY_PRESSURE_REPORT_CONFIG_VERSION
    )
    catalyst_recency_watch_hours: Decimal = Decimal("72.000000")
    catalyst_recency_block_hours: Decimal = Decimal("6.000000")
    evidence_contradiction_watch_threshold: Decimal = Decimal("0.250000")
    evidence_contradiction_block_threshold: Decimal = Decimal("0.600000")
    liquidity_stress_watch_threshold: Decimal = Decimal("0.500000")
    liquidity_stress_block_threshold: Decimal = Decimal("0.750000")
    probability_movement_watch_threshold: Decimal = Decimal("0.500000")
    probability_movement_block_threshold: Decimal = Decimal("0.800000")
    resolution_proximity_watch_hours: Decimal = Decimal("72.000000")
    resolution_proximity_block_hours: Decimal = Decimal("12.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_CATALYST_VOLATILITY_PRESSURE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "catalyst_recency_watch_hours",
            "catalyst_recency_block_hours",
            "resolution_proximity_watch_hours",
            "resolution_proximity_block_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "evidence_contradiction_watch_threshold",
            "evidence_contradiction_block_threshold",
            "liquidity_stress_watch_threshold",
            "liquidity_stress_block_threshold",
            "probability_movement_watch_threshold",
            "probability_movement_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_score_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        require_paper_only_flags("catalyst volatility pressure config", self)


@dataclass(frozen=True)
class ResearchEventCatalystVolatilityPressureInput:
    domain_label: str
    catalyst_recency_hours: Decimal
    evidence_contradiction_score: Decimal
    liquidity_stress_score: Decimal
    probability_movement_score: Decimal
    resolution_proximity_hours: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "domain_label",
            _require_public_string("domain_label", self.domain_label),
        )
        for field_name in (
            "catalyst_recency_hours",
            "resolution_proximity_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "evidence_contradiction_score",
            "liquidity_stress_score",
            "probability_movement_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_score_decimal(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("catalyst volatility pressure input", self)


@dataclass(frozen=True)
class ResearchEventCatalystVolatilityPressureDomainRow:
    domain_label: str
    status: str
    catalyst_recency_hours: Decimal
    evidence_contradiction_score: Decimal
    liquidity_stress_score: Decimal
    probability_movement_score: Decimal
    resolution_proximity_hours: Decimal
    pressure_flag_count: Decimal
    catalyst_recency: bool
    evidence_contradiction: bool
    liquidity_stress: bool
    probability_movement: bool
    resolution_proximity: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "domain_label",
            _require_public_string("domain_label", self.domain_label),
        )
        _require_status("status", self.status)
        for field_name in (
            "catalyst_recency_hours",
            "resolution_proximity_hours",
            "pressure_flag_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "evidence_contradiction_score",
            "liquidity_stress_score",
            "probability_movement_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_score_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "catalyst_recency",
            "evidence_contradiction",
            "liquidity_stress",
            "probability_movement",
            "resolution_proximity",
        ):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _reject_unsafe_public_payload("catalyst volatility pressure row", self)
        reject_unsafe_surface_fields("catalyst volatility pressure row", self)
        require_paper_only_flags("catalyst volatility pressure row", self)


@dataclass(frozen=True)
class ResearchEventCatalystVolatilityPressureReport:
    generated_at: datetime
    config_version: str
    status: str
    reason_codes: tuple[str, ...]
    domain_count: Decimal
    pass_domain_count: Decimal
    watch_domain_count: Decimal
    block_domain_count: Decimal
    flagged_domain_count: Decimal
    catalyst_recency_domain_count: Decimal
    evidence_contradiction_domain_count: Decimal
    liquidity_stress_domain_count: Decimal
    probability_movement_domain_count: Decimal
    resolution_proximity_domain_count: Decimal
    flagged_domain_ratio: Decimal
    min_catalyst_recency_hours: Decimal
    min_resolution_proximity_hours: Decimal
    max_evidence_contradiction_score: Decimal
    max_liquidity_stress_score: Decimal
    max_probability_movement_score: Decimal
    rows: tuple[ResearchEventCatalystVolatilityPressureDomainRow, ...]
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
            "domain_count",
            "pass_domain_count",
            "watch_domain_count",
            "block_domain_count",
            "flagged_domain_count",
            "catalyst_recency_domain_count",
            "evidence_contradiction_domain_count",
            "liquidity_stress_domain_count",
            "probability_movement_domain_count",
            "resolution_proximity_domain_count",
            "flagged_domain_ratio",
            "min_catalyst_recency_hours",
            "min_resolution_proximity_hours",
            "max_evidence_contradiction_score",
            "max_liquidity_stress_score",
            "max_probability_movement_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _reject_unsafe_public_payload("catalyst volatility pressure report", self)
        reject_unsafe_surface_fields("catalyst volatility pressure report", self)
        require_paper_only_flags("catalyst volatility pressure report", self)
        _validate_derived_validation_digest(self)


def build_research_event_catalyst_volatility_pressure_report(
    input_rows: list[ResearchEventCatalystVolatilityPressureInput]
    | tuple[ResearchEventCatalystVolatilityPressureInput, ...],
    *,
    config: ResearchEventCatalystVolatilityPressureConfig,
    generated_at: datetime,
) -> ResearchEventCatalystVolatilityPressureReport:
    if type(config) is not ResearchEventCatalystVolatilityPressureConfig:
        raise ValueError("config must be a ResearchEventCatalystVolatilityPressureConfig")
    require_paper_only_flags("catalyst volatility pressure config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_input_rows(input_rows)
    rows = _sort_rows(tuple(_row_from_input(input_row, config=config) for input_row in inputs))
    reason_codes = _report_reason_codes(rows)
    domain_count = _count(len(rows))

    return ResearchEventCatalystVolatilityPressureReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(rows),
        reason_codes=reason_codes,
        domain_count=domain_count,
        pass_domain_count=_status_count(rows, "pass"),
        watch_domain_count=_status_count(rows, "watch"),
        block_domain_count=_status_count(rows, "block"),
        flagged_domain_count=_flagged_count(rows),
        catalyst_recency_domain_count=_positive_bool_count(rows, "catalyst_recency"),
        evidence_contradiction_domain_count=_positive_bool_count(
            rows,
            "evidence_contradiction",
        ),
        liquidity_stress_domain_count=_positive_bool_count(rows, "liquidity_stress"),
        probability_movement_domain_count=_positive_bool_count(
            rows,
            "probability_movement",
        ),
        resolution_proximity_domain_count=_positive_bool_count(
            rows,
            "resolution_proximity",
        ),
        flagged_domain_ratio=_ratio(_flagged_count(rows), domain_count),
        min_catalyst_recency_hours=_min_decimal(row.catalyst_recency_hours for row in rows),
        min_resolution_proximity_hours=_min_decimal(
            row.resolution_proximity_hours for row in rows
        ),
        max_evidence_contradiction_score=_max_decimal(
            row.evidence_contradiction_score for row in rows
        ),
        max_liquidity_stress_score=_max_decimal(row.liquidity_stress_score for row in rows),
        max_probability_movement_score=_max_decimal(
            row.probability_movement_score for row in rows
        ),
        rows=rows,
        derived_validation_digest=_derived_validation_digest(
            generated_at=generated_at_utc,
            config_version=config.config_version,
            status=_report_status(rows),
            reason_codes=reason_codes,
            domain_count=domain_count,
            pass_domain_count=_status_count(rows, "pass"),
            watch_domain_count=_status_count(rows, "watch"),
            block_domain_count=_status_count(rows, "block"),
            flagged_domain_count=_flagged_count(rows),
            catalyst_recency_domain_count=_positive_bool_count(rows, "catalyst_recency"),
            evidence_contradiction_domain_count=_positive_bool_count(
                rows,
                "evidence_contradiction",
            ),
            liquidity_stress_domain_count=_positive_bool_count(rows, "liquidity_stress"),
            probability_movement_domain_count=_positive_bool_count(
                rows,
                "probability_movement",
            ),
            resolution_proximity_domain_count=_positive_bool_count(
                rows,
                "resolution_proximity",
            ),
            flagged_domain_ratio=_ratio(_flagged_count(rows), domain_count),
            min_catalyst_recency_hours=_min_decimal(
                row.catalyst_recency_hours for row in rows
            ),
            min_resolution_proximity_hours=_min_decimal(
                row.resolution_proximity_hours for row in rows
            ),
            max_evidence_contradiction_score=_max_decimal(
                row.evidence_contradiction_score for row in rows
            ),
            max_liquidity_stress_score=_max_decimal(
                row.liquidity_stress_score for row in rows
            ),
            max_probability_movement_score=_max_decimal(
                row.probability_movement_score for row in rows
            ),
            rows=rows,
            paper_only=True,
            report_only=True,
            readonly=True,
        ),
    )


def research_event_catalyst_volatility_pressure_report_to_payload(
    report: ResearchEventCatalystVolatilityPressureReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEventCatalystVolatilityPressureReport:
        raise ValueError("report must be a ResearchEventCatalystVolatilityPressureReport")
    require_paper_only_flags("catalyst volatility pressure report", report)
    _reject_unsafe_public_payload("catalyst volatility pressure report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    reject_unsafe_surface_fields("catalyst volatility pressure payload", payload)
    _reject_unsafe_public_payload("catalyst volatility pressure payload", payload)
    return payload


def _normalize_input_rows(
    value: object,
) -> tuple[ResearchEventCatalystVolatilityPressureInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchEventCatalystVolatilityPressureInput:
            raise ValueError("input rows must contain catalyst volatility pressure inputs")
        require_paper_only_flags("catalyst volatility pressure input", row)
        if row.domain_label in seen:
            raise ValueError("domain_label values must be unique")
        seen.add(row.domain_label)
    return tuple(sorted(rows, key=lambda row: row.domain_label))


def _row_from_input(
    input_row: ResearchEventCatalystVolatilityPressureInput,
    *,
    config: ResearchEventCatalystVolatilityPressureConfig,
) -> ResearchEventCatalystVolatilityPressureDomainRow:
    catalyst_recency = input_row.catalyst_recency_hours <= config.catalyst_recency_watch_hours
    evidence_contradiction = (
        input_row.evidence_contradiction_score
        >= config.evidence_contradiction_watch_threshold
    )
    liquidity_stress = input_row.liquidity_stress_score >= config.liquidity_stress_watch_threshold
    probability_movement = (
        input_row.probability_movement_score >= config.probability_movement_watch_threshold
    )
    resolution_proximity = (
        input_row.resolution_proximity_hours <= config.resolution_proximity_watch_hours
    )
    reason_codes = _row_reason_codes(
        catalyst_recency=catalyst_recency,
        evidence_contradiction=evidence_contradiction,
        liquidity_stress=liquidity_stress,
        probability_movement=probability_movement,
        resolution_proximity=resolution_proximity,
    )

    return ResearchEventCatalystVolatilityPressureDomainRow(
        domain_label=input_row.domain_label,
        status=_row_status(input_row, config=config, reason_codes=reason_codes),
        catalyst_recency_hours=input_row.catalyst_recency_hours,
        evidence_contradiction_score=input_row.evidence_contradiction_score,
        liquidity_stress_score=input_row.liquidity_stress_score,
        probability_movement_score=input_row.probability_movement_score,
        resolution_proximity_hours=input_row.resolution_proximity_hours,
        pressure_flag_count=_count(
            sum(
                1
                for flag in (
                    catalyst_recency,
                    evidence_contradiction,
                    liquidity_stress,
                    probability_movement,
                    resolution_proximity,
                )
                if flag
            ),
        ),
        catalyst_recency=catalyst_recency,
        evidence_contradiction=evidence_contradiction,
        liquidity_stress=liquidity_stress,
        probability_movement=probability_movement,
        resolution_proximity=resolution_proximity,
        reason_codes=reason_codes,
    )


def _row_status(
    input_row: ResearchEventCatalystVolatilityPressureInput,
    *,
    config: ResearchEventCatalystVolatilityPressureConfig,
    reason_codes: tuple[str, ...],
) -> str:
    block_hit = (
        input_row.catalyst_recency_hours <= config.catalyst_recency_block_hours
        or input_row.evidence_contradiction_score
        >= config.evidence_contradiction_block_threshold
        or input_row.liquidity_stress_score >= config.liquidity_stress_block_threshold
        or input_row.probability_movement_score
        >= config.probability_movement_block_threshold
        or input_row.resolution_proximity_hours <= config.resolution_proximity_block_hours
    )
    if block_hit:
        return "block"
    if reason_codes != (PASS_REASON,):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    catalyst_recency: bool,
    evidence_contradiction: bool,
    liquidity_stress: bool,
    probability_movement: bool,
    resolution_proximity: bool,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if catalyst_recency:
        reason_codes.append(CATALYST_RECENCY_REASON)
    if evidence_contradiction:
        reason_codes.append(EVIDENCE_CONTRADICTION_REASON)
    if liquidity_stress:
        reason_codes.append(LIQUIDITY_STRESS_REASON)
    if probability_movement:
        reason_codes.append(PROBABILITY_MOVEMENT_REASON)
    if resolution_proximity:
        reason_codes.append(RESOLUTION_PROXIMITY_REASON)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return tuple(reason_codes)


def _sort_rows(
    rows: tuple[ResearchEventCatalystVolatilityPressureDomainRow, ...],
) -> tuple[ResearchEventCatalystVolatilityPressureDomainRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                STATUS_RANK[row.status],
                -row.pressure_flag_count,
                row.catalyst_recency_hours,
                row.resolution_proximity_hours,
                -row.evidence_contradiction_score,
                -row.liquidity_stress_score,
                -row.probability_movement_score,
                row.domain_label,
            ),
        ),
    )


def _normalize_rows(
    value: object,
) -> tuple[ResearchEventCatalystVolatilityPressureDomainRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchEventCatalystVolatilityPressureDomainRow:
            raise ValueError("rows must contain catalyst volatility pressure rows")
        require_paper_only_flags("catalyst volatility pressure row", row)
        if row.domain_label in seen:
            raise ValueError("rows must be unique by domain_label")
        seen.add(row.domain_label)
    if rows != _sort_rows(rows):
        raise ValueError("rows must be sorted deterministically")
    return rows


def _report_reason_codes(
    rows: tuple[ResearchEventCatalystVolatilityPressureDomainRow, ...],
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


def _report_status(rows: tuple[ResearchEventCatalystVolatilityPressureDomainRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _validate_config(config: ResearchEventCatalystVolatilityPressureConfig) -> None:
    if config.catalyst_recency_block_hours > config.catalyst_recency_watch_hours:
        raise ValueError("catalyst recency block threshold must not exceed watch threshold")
    if (
        config.evidence_contradiction_block_threshold
        < config.evidence_contradiction_watch_threshold
    ):
        raise ValueError(
            "evidence contradiction block threshold must be at least watch threshold",
        )
    if config.liquidity_stress_block_threshold < config.liquidity_stress_watch_threshold:
        raise ValueError("liquidity stress block threshold must be at least watch threshold")
    if (
        config.probability_movement_block_threshold
        < config.probability_movement_watch_threshold
    ):
        raise ValueError(
            "probability movement block threshold must be at least watch threshold",
        )
    if config.resolution_proximity_block_hours > config.resolution_proximity_watch_hours:
        raise ValueError(
            "resolution proximity block threshold must not exceed watch threshold",
        )


def _validate_row(row: ResearchEventCatalystVolatilityPressureDomainRow) -> None:
    flags = (
        row.catalyst_recency,
        row.evidence_contradiction,
        row.liquidity_stress,
        row.probability_movement,
        row.resolution_proximity,
    )
    if row.pressure_flag_count != _count(sum(1 for flag in flags if flag)):
        raise ValueError("pressure_flag_count must match flags")
    if row.pressure_flag_count % ONE != ZERO:
        raise ValueError("pressure_flag_count must be a whole Decimal")
    expected_reason_codes = _row_reason_codes(
        catalyst_recency=row.catalyst_recency,
        evidence_contradiction=row.evidence_contradiction,
        liquidity_stress=row.liquidity_stress,
        probability_movement=row.probability_movement,
        resolution_proximity=row.resolution_proximity,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row flags")
    if row.status == "pass" and row.pressure_flag_count != ZERO:
        raise ValueError("pass rows must not have pressure flags")
    if row.status in ("watch", "block") and row.pressure_flag_count == ZERO:
        raise ValueError("flagged rows must have pressure flags")


def _validate_report(report: ResearchEventCatalystVolatilityPressureReport) -> None:
    if report.domain_count != _count(len(report.rows)):
        raise ValueError("domain_count must match rows")
    if report.pass_domain_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_domain_count must match rows")
    if report.watch_domain_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_domain_count must match rows")
    if report.block_domain_count != _status_count(report.rows, "block"):
        raise ValueError("block_domain_count must match rows")
    if (
        report.pass_domain_count + report.watch_domain_count + report.block_domain_count
        != report.domain_count
    ):
        raise ValueError("status counts must sum to domain_count")
    expected_counts = {
        "flagged_domain_count": _flagged_count(report.rows),
        "catalyst_recency_domain_count": _positive_bool_count(
            report.rows,
            "catalyst_recency",
        ),
        "evidence_contradiction_domain_count": _positive_bool_count(
            report.rows,
            "evidence_contradiction",
        ),
        "liquidity_stress_domain_count": _positive_bool_count(
            report.rows,
            "liquidity_stress",
        ),
        "probability_movement_domain_count": _positive_bool_count(
            report.rows,
            "probability_movement",
        ),
        "resolution_proximity_domain_count": _positive_bool_count(
            report.rows,
            "resolution_proximity",
        ),
    }
    for field_name, expected in expected_counts.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.flagged_domain_ratio != _ratio(
        report.flagged_domain_count,
        report.domain_count,
    ):
        raise ValueError("flagged_domain_ratio must match rows")
    if report.min_catalyst_recency_hours != _min_decimal(
        row.catalyst_recency_hours for row in report.rows
    ):
        raise ValueError("min_catalyst_recency_hours must match rows")
    if report.min_resolution_proximity_hours != _min_decimal(
        row.resolution_proximity_hours for row in report.rows
    ):
        raise ValueError("min_resolution_proximity_hours must match rows")
    if report.max_evidence_contradiction_score != _max_decimal(
        row.evidence_contradiction_score for row in report.rows
    ):
        raise ValueError("max_evidence_contradiction_score must match rows")
    if report.max_liquidity_stress_score != _max_decimal(
        row.liquidity_stress_score for row in report.rows
    ):
        raise ValueError("max_liquidity_stress_score must match rows")
    if report.max_probability_movement_score != _max_decimal(
        row.probability_movement_score for row in report.rows
    ):
        raise ValueError("max_probability_movement_score must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")


def _status_count(
    rows: tuple[ResearchEventCatalystVolatilityPressureDomainRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _flagged_count(
    rows: tuple[ResearchEventCatalystVolatilityPressureDomainRow, ...],
) -> Decimal:
    return _count(sum(1 for row in rows if row.status != "pass"))


def _positive_bool_count(
    rows: tuple[ResearchEventCatalystVolatilityPressureDomainRow, ...],
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
    if type(value) is not str or value not in VOLATILITY_PRESSURE_STATUSES:
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
    domain_count: Decimal,
    pass_domain_count: Decimal,
    watch_domain_count: Decimal,
    block_domain_count: Decimal,
    flagged_domain_count: Decimal,
    catalyst_recency_domain_count: Decimal,
    evidence_contradiction_domain_count: Decimal,
    liquidity_stress_domain_count: Decimal,
    probability_movement_domain_count: Decimal,
    resolution_proximity_domain_count: Decimal,
    flagged_domain_ratio: Decimal,
    min_catalyst_recency_hours: Decimal,
    min_resolution_proximity_hours: Decimal,
    max_evidence_contradiction_score: Decimal,
    max_liquidity_stress_score: Decimal,
    max_probability_movement_score: Decimal,
    rows: tuple[ResearchEventCatalystVolatilityPressureDomainRow, ...],
    paper_only: bool,
    report_only: bool,
    readonly: bool,
) -> str:
    payload = {
        "generated_at": _as_utc("generated_at", generated_at),
        "config_version": config_version,
        "status": status,
        "reason_codes": reason_codes,
        "domain_count": domain_count,
        "pass_domain_count": pass_domain_count,
        "watch_domain_count": watch_domain_count,
        "block_domain_count": block_domain_count,
        "flagged_domain_count": flagged_domain_count,
        "catalyst_recency_domain_count": catalyst_recency_domain_count,
        "evidence_contradiction_domain_count": evidence_contradiction_domain_count,
        "liquidity_stress_domain_count": liquidity_stress_domain_count,
        "probability_movement_domain_count": probability_movement_domain_count,
        "resolution_proximity_domain_count": resolution_proximity_domain_count,
        "flagged_domain_ratio": flagged_domain_ratio,
        "min_catalyst_recency_hours": min_catalyst_recency_hours,
        "min_resolution_proximity_hours": min_resolution_proximity_hours,
        "max_evidence_contradiction_score": max_evidence_contradiction_score,
        "max_liquidity_stress_score": max_liquidity_stress_score,
        "max_probability_movement_score": max_probability_movement_score,
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
    report: ResearchEventCatalystVolatilityPressureReport,
) -> None:
    expected = _derived_validation_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        status=report.status,
        reason_codes=report.reason_codes,
        domain_count=report.domain_count,
        pass_domain_count=report.pass_domain_count,
        watch_domain_count=report.watch_domain_count,
        block_domain_count=report.block_domain_count,
        flagged_domain_count=report.flagged_domain_count,
        catalyst_recency_domain_count=report.catalyst_recency_domain_count,
        evidence_contradiction_domain_count=report.evidence_contradiction_domain_count,
        liquidity_stress_domain_count=report.liquidity_stress_domain_count,
        probability_movement_domain_count=report.probability_movement_domain_count,
        resolution_proximity_domain_count=report.resolution_proximity_domain_count,
        flagged_domain_ratio=report.flagged_domain_ratio,
        min_catalyst_recency_hours=report.min_catalyst_recency_hours,
        min_resolution_proximity_hours=report.min_resolution_proximity_hours,
        max_evidence_contradiction_score=report.max_evidence_contradiction_score,
        max_liquidity_stress_score=report.max_liquidity_stress_score,
        max_probability_movement_score=report.max_probability_movement_score,
        rows=report.rows,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )
    if report.derived_validation_digest != expected:
        raise ValueError("derived_validation_digest must match report payload")


__all__ = (
    "DEFAULT_RESEARCH_EVENT_CATALYST_VOLATILITY_PRESSURE_REPORT_CONFIG_VERSION",
    "ResearchEventCatalystVolatilityPressureConfig",
    "ResearchEventCatalystVolatilityPressureDomainRow",
    "ResearchEventCatalystVolatilityPressureInput",
    "ResearchEventCatalystVolatilityPressureReport",
    "build_research_event_catalyst_volatility_pressure_report",
    "research_event_catalyst_volatility_pressure_report_to_payload",
)
