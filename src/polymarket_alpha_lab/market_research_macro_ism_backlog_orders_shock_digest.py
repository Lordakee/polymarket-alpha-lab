"""Pure Phase 1 macro ISM backlog-orders shock digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import re
from typing import Any


DEFAULT_MACRO_ISM_BACKLOG_ORDERS_SHOCK_DIGEST_CONFIG_VERSION = (
    "market-research-macro-ism-backlog-orders-shock-digest-v0"
)

SHOCK_STATUSES = ("pass", "watch", "blocked")
ROW_REASON_CODES = (
    "macro_ism_backlog_orders_blocked_shock",
    "macro_ism_backlog_orders_watch_shock",
    "macro_ism_backlog_orders_inline",
    "macro_ism_backlog_orders_new_orders_confirmation",
    "macro_ism_backlog_orders_production_constraint",
    "macro_ism_backlog_orders_supplier_deliveries_stress",
    "macro_ism_backlog_orders_source_stale",
    "macro_ism_backlog_orders_quorum_missing",
    "macro_ism_backlog_orders_source_disagreement",
    "macro_ism_backlog_orders_upstream_reasons",
)
REPORT_REASON_CODES = (
    "macro_ism_backlog_orders_shock_blocked_present",
    "macro_ism_backlog_orders_shock_watch_present",
    "macro_ism_backlog_orders_new_orders_confirmed_present",
    "macro_ism_backlog_orders_production_constraint_present",
    "macro_ism_backlog_orders_supplier_deliveries_stress_present",
    "macro_ism_backlog_orders_source_stale_present",
    "macro_ism_backlog_orders_quorum_gap_present",
    "macro_ism_backlog_orders_source_disagreement_present",
    "macro_ism_backlog_orders_upstream_reasons_present",
    "macro_ism_backlog_orders_shock_digest_clear",
    "macro_ism_backlog_orders_shock_digest_empty",
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
WATCH_RISK_SCORE = Decimal("0.500000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_RANK = {
    "blocked": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}
_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


__all__ = (
    "DEFAULT_MACRO_ISM_BACKLOG_ORDERS_SHOCK_DIGEST_CONFIG_VERSION",
    "MacroIsmBacklogOrdersShockDigestConfig",
    "MacroIsmBacklogOrdersShockObservation",
    "MacroIsmBacklogOrdersShockDigestRow",
    "MacroIsmBacklogOrdersShockReasonCodeCount",
    "MacroIsmBacklogOrdersShockDigestReport",
    "build_market_research_macro_ism_backlog_orders_shock_digest",
    "market_research_macro_ism_backlog_orders_shock_digest_payload",
)


@dataclass(frozen=True)
class MacroIsmBacklogOrdersShockDigestConfig:
    config_version: str = DEFAULT_MACRO_ISM_BACKLOG_ORDERS_SHOCK_DIGEST_CONFIG_VERSION
    watch_backlog_orders_surprise: Decimal = Decimal("2.000000")
    blocked_backlog_orders_surprise: Decimal = Decimal("4.000000")
    new_orders_confirmation_threshold: Decimal = Decimal("1.500000")
    production_constraint_threshold: Decimal = Decimal("2.500000")
    supplier_deliveries_stress_threshold: Decimal = Decimal("2.000000")
    stale_source_age_hours: Decimal = Decimal("48.000000")
    min_source_quorum_count: Decimal = Decimal("2.000000")
    source_disagreement_threshold: Decimal = Decimal("3.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MacroIsmBacklogOrdersShockDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_MACRO_ISM_BACKLOG_ORDERS_SHOCK_DIGEST_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_backlog_orders_surprise",
            "blocked_backlog_orders_surprise",
            "new_orders_confirmation_threshold",
            "production_constraint_threshold",
            "supplier_deliveries_stress_threshold",
            "stale_source_age_hours",
            "min_source_quorum_count",
            "source_disagreement_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_backlog_orders_surprise > self.blocked_backlog_orders_surprise:
            raise ValueError(
                "watch_backlog_orders_surprise must not exceed "
                "blocked_backlog_orders_surprise",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MacroIsmBacklogOrdersShockObservation:
    source_id: str
    release_id: str
    sector: str
    market_slug: str
    backlog_orders_index_surprise: Decimal
    new_orders_index_surprise: Decimal
    production_constraint_pressure: Decimal
    supplier_deliveries_stress: Decimal
    source_age_hours: Decimal
    source_quorum_count: Decimal
    source_disagreement: Decimal
    source_timestamp: datetime
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MacroIsmBacklogOrdersShockObservation, "observation")
        for field_name in ("source_id", "release_id", "sector", "market_slug"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "backlog_orders_index_surprise",
            "new_orders_index_surprise",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "production_constraint_pressure",
            "supplier_deliveries_stress",
            "source_age_hours",
            "source_quorum_count",
            "source_disagreement",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_timestamp",
            _as_utc("source_timestamp", self.source_timestamp),
        )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_open_reason_codes(
                "upstream_reason_codes",
                self.upstream_reason_codes,
            ),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class MacroIsmBacklogOrdersShockDigestRow:
    source_id: str
    release_id: str
    sector: str
    market_slug: str
    backlog_orders_index_surprise: Decimal
    positive_backlog_orders_surprise: Decimal
    new_orders_index_surprise: Decimal
    positive_new_orders_surprise: Decimal
    production_constraint_pressure: Decimal
    supplier_deliveries_stress: Decimal
    source_age_hours: Decimal
    source_quorum_count: Decimal
    source_disagreement: Decimal
    source_timestamp: datetime
    upstream_reason_codes: tuple[str, ...]
    shock_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MacroIsmBacklogOrdersShockDigestRow, "row")
        for field_name in ("source_id", "release_id", "sector", "market_slug"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "backlog_orders_index_surprise",
            "new_orders_index_surprise",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "positive_backlog_orders_surprise",
            "positive_new_orders_surprise",
            "production_constraint_pressure",
            "supplier_deliveries_stress",
            "source_age_hours",
            "source_quorum_count",
            "source_disagreement",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_timestamp",
            _as_utc("source_timestamp", self.source_timestamp),
        )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_open_reason_codes(
                "upstream_reason_codes",
                self.upstream_reason_codes,
            ),
        )
        _require_member("shock_status", self.shock_status, SHOCK_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MacroIsmBacklogOrdersShockReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MacroIsmBacklogOrdersShockReasonCodeCount, "reason code count")
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODES)
        object.__setattr__(self, "count", _require_nonnegative_decimal("count", self.count))
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MacroIsmBacklogOrdersShockDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    backlog_shock_count: Decimal
    demand_confirmation_count: Decimal
    supply_constraint_count: Decimal
    source_quality_gap_count: Decimal
    stale_source_count: Decimal
    max_backlog_orders_surprise: Decimal
    average_backlog_orders_surprise: Decimal
    shock_risk_score: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[MacroIsmBacklogOrdersShockDigestRow, ...]
    reason_code_counts: tuple[MacroIsmBacklogOrdersShockReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MacroIsmBacklogOrdersShockDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_MACRO_ISM_BACKLOG_ORDERS_SHOCK_DIGEST_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "backlog_shock_count",
            "demand_confirmation_count",
            "supply_constraint_count",
            "source_quality_gap_count",
            "stale_source_count",
            "max_backlog_orders_surprise",
            "average_backlog_orders_surprise",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "shock_risk_score",
            _require_ratio("shock_risk_score", self.shock_risk_score),
        )
        _require_member("digest_status", self.digest_status, SHOCK_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_macro_ism_backlog_orders_shock_digest(
    observations: Iterable[MacroIsmBacklogOrdersShockObservation],
    *,
    config: MacroIsmBacklogOrdersShockDigestConfig,
    generated_at: datetime,
) -> MacroIsmBacklogOrdersShockDigestReport:
    if type(config) is not MacroIsmBacklogOrdersShockDigestConfig:
        raise ValueError("config must be exactly MacroIsmBacklogOrdersShockDigestConfig")
    generated_at_utc = _as_utc("generated_at", generated_at)
    _require_hard_flags("config", config)
    normalized = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (
                _row_from_observation(observation, config=config)
                for observation in normalized
            ),
            key=_row_sort_key,
        ),
    )
    row_count = _count_decimal(len(rows))
    reason_codes = _report_reason_codes(rows)
    digest_status = _digest_status(rows)

    return MacroIsmBacklogOrdersShockDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=row_count,
        blocked_count=_status_count(rows, "blocked"),
        watch_count=_status_count(rows, "watch"),
        pass_count=_status_count(rows, "pass"),
        backlog_shock_count=_backlog_shock_count(rows),
        demand_confirmation_count=_reason_count(
            rows,
            "macro_ism_backlog_orders_new_orders_confirmation",
        ),
        supply_constraint_count=_supply_constraint_count(rows),
        source_quality_gap_count=_source_quality_gap_count(rows),
        stale_source_count=_reason_count(rows, "macro_ism_backlog_orders_source_stale"),
        max_backlog_orders_surprise=_max_row_decimal(
            rows,
            "positive_backlog_orders_surprise",
        ),
        average_backlog_orders_surprise=_ratio(
            _sum_decimal(row.positive_backlog_orders_surprise for row in rows),
            row_count,
        ),
        shock_risk_score=_shock_risk_score(rows),
        digest_status=digest_status,
        recommended_next_step=_recommended_next_step(digest_status),
        rows=rows,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        reason_codes=reason_codes,
    )


def market_research_macro_ism_backlog_orders_shock_digest_payload(
    report: MacroIsmBacklogOrdersShockDigestReport,
) -> dict[str, Any]:
    if type(report) is not MacroIsmBacklogOrdersShockDigestReport:
        raise ValueError("report must be exactly MacroIsmBacklogOrdersShockDigestReport")
    return _payload_value(report)


def _row_from_observation(
    observation: MacroIsmBacklogOrdersShockObservation,
    *,
    config: MacroIsmBacklogOrdersShockDigestConfig,
) -> MacroIsmBacklogOrdersShockDigestRow:
    positive_backlog_orders_surprise = _positive_decimal(
        observation.backlog_orders_index_surprise,
    )
    positive_new_orders_surprise = _positive_decimal(observation.new_orders_index_surprise)
    status = _row_status(
        observation,
        positive_backlog_orders_surprise=positive_backlog_orders_surprise,
        config=config,
    )
    return MacroIsmBacklogOrdersShockDigestRow(
        source_id=observation.source_id,
        release_id=observation.release_id,
        sector=observation.sector,
        market_slug=observation.market_slug,
        backlog_orders_index_surprise=observation.backlog_orders_index_surprise,
        positive_backlog_orders_surprise=positive_backlog_orders_surprise,
        new_orders_index_surprise=observation.new_orders_index_surprise,
        positive_new_orders_surprise=positive_new_orders_surprise,
        production_constraint_pressure=observation.production_constraint_pressure,
        supplier_deliveries_stress=observation.supplier_deliveries_stress,
        source_age_hours=observation.source_age_hours,
        source_quorum_count=observation.source_quorum_count,
        source_disagreement=observation.source_disagreement,
        source_timestamp=observation.source_timestamp,
        upstream_reason_codes=observation.upstream_reason_codes,
        shock_status=status,
        reason_codes=_row_reason_codes(
            observation,
            positive_backlog_orders_surprise=positive_backlog_orders_surprise,
            positive_new_orders_surprise=positive_new_orders_surprise,
            config=config,
        ),
    )


def _row_status(
    observation: MacroIsmBacklogOrdersShockObservation,
    *,
    positive_backlog_orders_surprise: Decimal,
    config: MacroIsmBacklogOrdersShockDigestConfig,
) -> str:
    if _has_blocking_source_quality_risk(observation, config=config):
        return "blocked"
    if positive_backlog_orders_surprise >= config.blocked_backlog_orders_surprise:
        return "blocked"
    if positive_backlog_orders_surprise >= config.watch_backlog_orders_surprise:
        return "watch"
    return "pass"


def _row_reason_codes(
    observation: MacroIsmBacklogOrdersShockObservation,
    *,
    positive_backlog_orders_surprise: Decimal,
    positive_new_orders_surprise: Decimal,
    config: MacroIsmBacklogOrdersShockDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if positive_backlog_orders_surprise >= config.blocked_backlog_orders_surprise:
        reason_codes.append("macro_ism_backlog_orders_blocked_shock")
    elif positive_backlog_orders_surprise >= config.watch_backlog_orders_surprise:
        reason_codes.append("macro_ism_backlog_orders_watch_shock")
    else:
        reason_codes.append("macro_ism_backlog_orders_inline")

    if positive_new_orders_surprise >= config.new_orders_confirmation_threshold:
        reason_codes.append("macro_ism_backlog_orders_new_orders_confirmation")
    if observation.production_constraint_pressure >= config.production_constraint_threshold:
        reason_codes.append("macro_ism_backlog_orders_production_constraint")
    if observation.supplier_deliveries_stress >= config.supplier_deliveries_stress_threshold:
        reason_codes.append("macro_ism_backlog_orders_supplier_deliveries_stress")
    if observation.source_age_hours >= config.stale_source_age_hours:
        reason_codes.append("macro_ism_backlog_orders_source_stale")
    if observation.source_quorum_count < config.min_source_quorum_count:
        reason_codes.append("macro_ism_backlog_orders_quorum_missing")
    if observation.source_disagreement >= config.source_disagreement_threshold:
        reason_codes.append("macro_ism_backlog_orders_source_disagreement")
    if observation.upstream_reason_codes:
        reason_codes.append("macro_ism_backlog_orders_upstream_reasons")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), ROW_REASON_CODES)


def _report_reason_codes(
    rows: tuple[MacroIsmBacklogOrdersShockDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("macro_ism_backlog_orders_shock_digest_empty",)
    reason_codes: list[str] = []
    if _reason_count(rows, "macro_ism_backlog_orders_blocked_shock") > ZERO:
        reason_codes.append("macro_ism_backlog_orders_shock_blocked_present")
    if _reason_count(rows, "macro_ism_backlog_orders_watch_shock") > ZERO:
        reason_codes.append("macro_ism_backlog_orders_shock_watch_present")
    if _reason_count(rows, "macro_ism_backlog_orders_new_orders_confirmation") > ZERO:
        reason_codes.append("macro_ism_backlog_orders_new_orders_confirmed_present")
    if _reason_count(rows, "macro_ism_backlog_orders_production_constraint") > ZERO:
        reason_codes.append("macro_ism_backlog_orders_production_constraint_present")
    if _reason_count(rows, "macro_ism_backlog_orders_supplier_deliveries_stress") > ZERO:
        reason_codes.append("macro_ism_backlog_orders_supplier_deliveries_stress_present")
    if _reason_count(rows, "macro_ism_backlog_orders_source_stale") > ZERO:
        reason_codes.append("macro_ism_backlog_orders_source_stale_present")
    if _reason_count(rows, "macro_ism_backlog_orders_quorum_missing") > ZERO:
        reason_codes.append("macro_ism_backlog_orders_quorum_gap_present")
    if _reason_count(rows, "macro_ism_backlog_orders_source_disagreement") > ZERO:
        reason_codes.append("macro_ism_backlog_orders_source_disagreement_present")
    if _reason_count(rows, "macro_ism_backlog_orders_upstream_reasons") > ZERO:
        reason_codes.append("macro_ism_backlog_orders_upstream_reasons_present")
    if not reason_codes:
        reason_codes.append("macro_ism_backlog_orders_shock_digest_clear")
    return tuple(reason for reason in REPORT_REASON_CODES if reason in reason_codes)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[MacroIsmBacklogOrdersShockDigestRow, ...],
) -> tuple[MacroIsmBacklogOrdersShockReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if reason_codes == ("macro_ism_backlog_orders_shock_digest_empty",):
        return (
            MacroIsmBacklogOrdersShockReasonCodeCount(
                reason_code="macro_ism_backlog_orders_shock_digest_empty",
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        MacroIsmBacklogOrdersShockReasonCodeCount(
            reason_code=reason_code,
            count=_report_reason_row_count(reason_code, rows),
            row_ratio=_ratio(_report_reason_row_count(reason_code, rows), row_count),
        )
        for reason_code in reason_codes
    )


def _report_reason_row_count(
    reason_code: str,
    rows: tuple[MacroIsmBacklogOrdersShockDigestRow, ...],
) -> Decimal:
    row_reason_code = {
        "macro_ism_backlog_orders_shock_blocked_present": (
            "macro_ism_backlog_orders_blocked_shock"
        ),
        "macro_ism_backlog_orders_shock_watch_present": (
            "macro_ism_backlog_orders_watch_shock"
        ),
        "macro_ism_backlog_orders_new_orders_confirmed_present": (
            "macro_ism_backlog_orders_new_orders_confirmation"
        ),
        "macro_ism_backlog_orders_production_constraint_present": (
            "macro_ism_backlog_orders_production_constraint"
        ),
        "macro_ism_backlog_orders_supplier_deliveries_stress_present": (
            "macro_ism_backlog_orders_supplier_deliveries_stress"
        ),
        "macro_ism_backlog_orders_source_stale_present": (
            "macro_ism_backlog_orders_source_stale"
        ),
        "macro_ism_backlog_orders_quorum_gap_present": (
            "macro_ism_backlog_orders_quorum_missing"
        ),
        "macro_ism_backlog_orders_source_disagreement_present": (
            "macro_ism_backlog_orders_source_disagreement"
        ),
        "macro_ism_backlog_orders_upstream_reasons_present": (
            "macro_ism_backlog_orders_upstream_reasons"
        ),
        "macro_ism_backlog_orders_shock_digest_clear": (
            "macro_ism_backlog_orders_inline"
        ),
    }[reason_code]
    return _reason_count(rows, row_reason_code)


def _digest_status(rows: tuple[MacroIsmBacklogOrdersShockDigestRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.shock_status == "blocked" for row in rows):
        return "blocked"
    if any(row.shock_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _recommended_next_step(status: str) -> str:
    if status == "pass":
        return "allow_report_only_macro_ism_backlog_orders_shock_screening"
    if status == "watch":
        return "monitor_report_only_macro_ism_backlog_orders_shock_screening"
    return "block_report_only_macro_ism_backlog_orders_shock_screening"


def _shock_risk_score(
    rows: tuple[MacroIsmBacklogOrdersShockDigestRow, ...],
) -> Decimal:
    digest_status = _digest_status(rows)
    if digest_status == "blocked":
        return ONE if rows else ZERO
    if digest_status == "watch":
        return WATCH_RISK_SCORE
    return ZERO


def _has_blocking_source_quality_risk(
    observation: MacroIsmBacklogOrdersShockObservation,
    *,
    config: MacroIsmBacklogOrdersShockDigestConfig,
) -> bool:
    return (
        observation.source_age_hours >= config.stale_source_age_hours
        or observation.source_quorum_count < config.min_source_quorum_count
        or observation.source_disagreement >= config.source_disagreement_threshold
    )


def _backlog_shock_count(
    rows: tuple[MacroIsmBacklogOrdersShockDigestRow, ...],
) -> Decimal:
    return _count_decimal(
        sum(
            1
            for row in rows
            if "macro_ism_backlog_orders_blocked_shock" in row.reason_codes
            or "macro_ism_backlog_orders_watch_shock" in row.reason_codes
        ),
    )


def _supply_constraint_count(
    rows: tuple[MacroIsmBacklogOrdersShockDigestRow, ...],
) -> Decimal:
    return _count_decimal(
        sum(
            1
            for row in rows
            if "macro_ism_backlog_orders_production_constraint" in row.reason_codes
            or "macro_ism_backlog_orders_supplier_deliveries_stress" in row.reason_codes
        ),
    )


def _source_quality_gap_count(
    rows: tuple[MacroIsmBacklogOrdersShockDigestRow, ...],
) -> Decimal:
    return _count_decimal(
        sum(
            1
            for row in rows
            if "macro_ism_backlog_orders_source_stale" in row.reason_codes
            or "macro_ism_backlog_orders_quorum_missing" in row.reason_codes
            or "macro_ism_backlog_orders_source_disagreement" in row.reason_codes
        ),
    )


def _validate_row(row: MacroIsmBacklogOrdersShockDigestRow) -> None:
    if row.positive_backlog_orders_surprise != _positive_decimal(
        row.backlog_orders_index_surprise,
    ):
        raise ValueError(
            "positive_backlog_orders_surprise must match "
            "backlog_orders_index_surprise",
        )
    if row.positive_new_orders_surprise != _positive_decimal(row.new_orders_index_surprise):
        raise ValueError(
            "positive_new_orders_surprise must match new_orders_index_surprise",
        )

    has_blocked_shock = "macro_ism_backlog_orders_blocked_shock" in row.reason_codes
    has_watch_shock = "macro_ism_backlog_orders_watch_shock" in row.reason_codes
    has_inline = "macro_ism_backlog_orders_inline" in row.reason_codes
    has_source_quality_risk = any(
        reason_code in row.reason_codes
        for reason_code in (
            "macro_ism_backlog_orders_source_stale",
            "macro_ism_backlog_orders_quorum_missing",
            "macro_ism_backlog_orders_source_disagreement",
        )
    )
    if sum((has_blocked_shock, has_watch_shock, has_inline)) != 1:
        raise ValueError("reason_codes must match backlog orders shock state")
    if has_blocked_shock and row.shock_status != "blocked":
        raise ValueError("reason_codes must match shock_status")
    if has_watch_shock and row.shock_status == "pass":
        raise ValueError("reason_codes must match shock_status")
    if has_watch_shock and row.shock_status == "blocked" and not has_source_quality_risk:
        raise ValueError("reason_codes must match shock_status")
    if row.shock_status == "blocked" and not (
        has_blocked_shock or has_source_quality_risk
    ):
        raise ValueError("reason_codes must match shock_status")
    if row.shock_status == "watch" and not has_watch_shock:
        raise ValueError("reason_codes must match shock_status")
    if row.shock_status == "pass" and not has_inline:
        raise ValueError("reason_codes must match shock_status")
    if (
        bool(row.upstream_reason_codes)
        != ("macro_ism_backlog_orders_upstream_reasons" in row.reason_codes)
    ):
        raise ValueError("reason_codes must match upstream_reason_codes")


def _validate_report(report: MacroIsmBacklogOrdersShockDigestReport) -> None:
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.blocked_count + report.watch_count + report.pass_count != report.row_count:
        raise ValueError("status counts must match rows")
    if report.backlog_shock_count != _backlog_shock_count(report.rows):
        raise ValueError("backlog_shock_count must match rows")
    if report.demand_confirmation_count != _reason_count(
        report.rows,
        "macro_ism_backlog_orders_new_orders_confirmation",
    ):
        raise ValueError("demand_confirmation_count must match rows")
    if report.supply_constraint_count != _supply_constraint_count(report.rows):
        raise ValueError("supply_constraint_count must match rows")
    if report.source_quality_gap_count != _source_quality_gap_count(report.rows):
        raise ValueError("source_quality_gap_count must match rows")
    if report.stale_source_count != _reason_count(
        report.rows,
        "macro_ism_backlog_orders_source_stale",
    ):
        raise ValueError("stale_source_count must match rows")
    if report.max_backlog_orders_surprise != _max_row_decimal(
        report.rows,
        "positive_backlog_orders_surprise",
    ):
        raise ValueError("max_backlog_orders_surprise must match rows")
    if report.average_backlog_orders_surprise != _ratio(
        _sum_decimal(row.positive_backlog_orders_surprise for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_backlog_orders_surprise must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.shock_risk_score != _shock_risk_score(report.rows):
        raise ValueError("shock_risk_score must match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, report.rows):
        raise ValueError("reason_code_counts must match reason_codes")


def _normalize_observations(
    observations: Iterable[MacroIsmBacklogOrdersShockObservation],
) -> tuple[MacroIsmBacklogOrdersShockObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must contain MacroIsmBacklogOrdersShockObservation")
    normalized = tuple(observations)
    seen_source_ids: set[str] = set()
    for observation in normalized:
        if type(observation) is not MacroIsmBacklogOrdersShockObservation:
            raise ValueError(
                "observations must contain MacroIsmBacklogOrdersShockObservation",
            )
        _require_hard_flags("observation", observation)
        if observation.source_id in seen_source_ids:
            raise ValueError("observations must not contain duplicate source_id values")
        seen_source_ids.add(observation.source_id)
    return normalized


def _normalize_rows(
    rows: Iterable[MacroIsmBacklogOrdersShockDigestRow],
) -> tuple[MacroIsmBacklogOrdersShockDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must contain MacroIsmBacklogOrdersShockDigestRow")
    normalized = tuple(rows)
    seen_source_ids: set[str] = set()
    for row in normalized:
        if type(row) is not MacroIsmBacklogOrdersShockDigestRow:
            raise ValueError("rows must contain MacroIsmBacklogOrdersShockDigestRow")
        _require_hard_flags("row", row)
        if row.source_id in seen_source_ids:
            raise ValueError("rows must not contain duplicate source_id values")
        seen_source_ids.add(row.source_id)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    values: Iterable[MacroIsmBacklogOrdersShockReasonCodeCount],
) -> tuple[MacroIsmBacklogOrdersShockReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError("reason_code_counts must contain reason code counts")
    normalized = tuple(values)
    for value in normalized:
        if type(value) is not MacroIsmBacklogOrdersShockReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MacroIsmBacklogOrdersShockReasonCodeCount",
            )
        _require_hard_flags("reason code count", value)
    return tuple(
        sorted(normalized, key=lambda value: REPORT_REASON_CODES.index(value.reason_code)),
    )


def _normalize_open_reason_codes(
    field_name: str,
    values: Iterable[str],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError(f"{field_name} must contain reason code strings")
    normalized: list[str] = []
    for value in values:
        _require_canonical_string("reason_code", value)
        if value not in normalized:
            normalized.append(value)
    return tuple(sorted(normalized))


def _normalize_reason_codes(
    field_name: str,
    values: Iterable[str],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError(f"{field_name} must contain reason code strings")
    normalized = tuple(values)
    for value in normalized:
        _require_member("reason_code", value, allowed)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    return tuple(sorted(normalized, key=lambda value: allowed.index(value)))


def _row_sort_key(
    row: MacroIsmBacklogOrdersShockDigestRow,
) -> tuple[Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.shock_status],
        -row.positive_backlog_orders_surprise,
        row.market_slug,
        row.source_id,
    )


def _status_count(
    rows: tuple[MacroIsmBacklogOrdersShockDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.shock_status == status))


def _reason_count(
    rows: tuple[MacroIsmBacklogOrdersShockDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_row_decimal(
    rows: tuple[MacroIsmBacklogOrdersShockDigestRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
        total += value
    return _quantize_decimal(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(numerator / denominator)


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _positive_decimal(value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError("value must be a Decimal")
    if value <= ZERO:
        return ZERO
    return _quantize_decimal(value)


def _require_ratio(field_name: str, value: object) -> Decimal:
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
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be supported")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
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
