"""Pure report-only team rationale reuse quality reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any

__all__ = (
    "DEFAULT_RESEARCH_TEAM_FORECAST_RATIONALE_REUSE_QUALITY_CONFIG_VERSION",
    "RATIONALE_REUSE_QUALITY_STATUSES",
    "ResearchTeamForecastRationaleReuseQualityConfig",
    "ResearchTeamForecastRationaleReuseQualityInput",
    "ResearchTeamForecastRationaleReuseQualityReasonCodeCount",
    "ResearchTeamForecastRationaleReuseQualityReport",
    "ResearchTeamForecastRationaleReuseQualityRow",
    "build_research_team_forecast_rationale_reuse_quality_report",
    "research_team_forecast_rationale_reuse_quality_report_digest",
    "research_team_forecast_rationale_reuse_quality_report_payload",
    "validate_research_team_forecast_rationale_reuse_quality_report_payload",
)


DEFAULT_RESEARCH_TEAM_FORECAST_RATIONALE_REUSE_QUALITY_CONFIG_VERSION = (
    "research-team-forecast-rationale-reuse-quality-report-v0"
)
RATIONALE_REUSE_QUALITY_STATUSES = ("pass", "watch", "block")

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
HEX_CHARS = frozenset("0123456789abcdef")
STATUS_WEIGHT = {
    "block": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}

BLOCK_REASON_CODES = (
    "rationale_freshness_block",
    "calibration_feedback_gap_block",
    "source_linkage_gap_block",
    "contradiction_carry_forward_block",
    "reuse_quality_pressure_block",
)
WATCH_REASON_CODES = (
    "rationale_freshness_watch",
    "calibration_feedback_gap_watch",
    "source_linkage_gap_watch",
    "contradiction_carry_forward_watch",
    "reuse_quality_pressure_watch",
)
EMPTY_REPORT_REASON_CODE = "rationale_reuse_quality_empty"
REPORT_REASON_PRIORITY = (
    "rationale_reuse_quality_block",
    *BLOCK_REASON_CODES,
    "rationale_reuse_quality_watch",
    *WATCH_REASON_CODES,
    "rationale_reuse_quality_pass",
)
ROW_REASON_CODES = (
    "rationale_reuse_quality_pass",
    "rationale_reuse_quality_watch",
    "rationale_reuse_quality_block",
    *BLOCK_REASON_CODES,
    *WATCH_REASON_CODES,
)
_PUBLIC_CODE_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_")
_UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        "candi" + "date",
        "mar" + "ket",
        "sl" + "ug",
        "quest" + "ion",
        "u" + "rl",
        "source_" + "text",
        "source " + "text",
        "source_" + "u" + "rl",
        "raw_" + "source",
        "raw_" + "candi" + "date",
        "d" + "sn",
        "ta" + "ble",
        "to" + "ken",
        "wal" + "let",
        "au" + "th",
        "or" + "der",
        "tr" + "ade",
        "li" + "ve",
        "data" + "base",
        "net" + "work",
        "requ" + "ests",
        "u" + "rl" + "lib",
        "sock" + "et",
        "sql" + "ite",
        "private_" + "key",
        "acco" + "unt",
        "sig" + "ning",
        "pos" + "ition",
        "reco" + "mmend",
        "siz" + "ing",
    ),
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise ValueError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchTeamForecastRationaleReuseQualityConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_FORECAST_RATIONALE_REUSE_QUALITY_CONFIG_VERSION
    )
    watch_rationale_age_hours: Decimal = Decimal("24.000000")
    block_rationale_age_hours: Decimal = Decimal("72.000000")
    watch_calibration_feedback_gap_ratio: Decimal = Decimal("0.250000")
    block_calibration_feedback_gap_ratio: Decimal = Decimal("0.500000")
    watch_source_linkage_gap_ratio: Decimal = Decimal("0.250000")
    block_source_linkage_gap_ratio: Decimal = Decimal("0.500000")
    watch_contradiction_carry_forward_ratio: Decimal = Decimal("0.250000")
    block_contradiction_carry_forward_ratio: Decimal = Decimal("0.600000")
    watch_reuse_quality_pressure: Decimal = Decimal("0.500000")
    block_reuse_quality_pressure: Decimal = Decimal("0.850000")
    freshness_weight: Decimal = Decimal("0.250000")
    calibration_feedback_weight: Decimal = Decimal("0.250000")
    source_linkage_weight: Decimal = Decimal("0.250000")
    contradiction_carry_forward_weight: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamForecastRationaleReuseQualityConfig,
            "config",
        )
        _require_config_version(self.config_version)
        for field_name in (
            "watch_rationale_age_hours",
            "block_rationale_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_calibration_feedback_gap_ratio",
            "block_calibration_feedback_gap_ratio",
            "watch_source_linkage_gap_ratio",
            "block_source_linkage_gap_ratio",
            "watch_contradiction_carry_forward_ratio",
            "block_contradiction_carry_forward_ratio",
            "watch_reuse_quality_pressure",
            "block_reuse_quality_pressure",
            "freshness_weight",
            "calibration_feedback_weight",
            "source_linkage_weight",
            "contradiction_carry_forward_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_unit_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamForecastRationaleReuseQualityInput(_FinalPublicDataclass):
    domain_key: str
    rationale_reuse_count: Decimal
    total_rationale_age_hours: Decimal
    calibration_feedback_item_count: Decimal
    calibration_feedback_uptake_count: Decimal
    linked_rationale_count: Decimal
    unresolved_contradiction_count: Decimal
    carried_forward_contradiction_count: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamForecastRationaleReuseQualityInput, "input")
        _require_public_code("domain_key", self.domain_key)
        for field_name in (
            "rationale_reuse_count",
            "calibration_feedback_item_count",
            "calibration_feedback_uptake_count",
            "linked_rationale_count",
            "unresolved_contradiction_count",
            "carried_forward_contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "total_rationale_age_hours",
            _require_nonnegative_decimal(
                "total_rationale_age_hours",
                self.total_rationale_age_hours,
            ),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _validate_input(self)
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchTeamForecastRationaleReuseQualityRow(_FinalPublicDataclass):
    domain_key: str
    rationale_reuse_count: Decimal
    mean_rationale_age_hours: Decimal
    calibration_feedback_item_count: Decimal
    calibration_feedback_uptake_count: Decimal
    calibration_feedback_uptake_ratio: Decimal
    linked_rationale_count: Decimal
    source_linkage_ratio: Decimal
    unresolved_contradiction_count: Decimal
    carried_forward_contradiction_count: Decimal
    contradiction_carry_forward_ratio: Decimal
    reuse_quality_pressure: Decimal
    reuse_status: str
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamForecastRationaleReuseQualityRow, "row")
        _require_public_code("domain_key", self.domain_key)
        for field_name in (
            "rationale_reuse_count",
            "calibration_feedback_item_count",
            "calibration_feedback_uptake_count",
            "linked_rationale_count",
            "unresolved_contradiction_count",
            "carried_forward_contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "mean_rationale_age_hours",
            _require_nonnegative_decimal(
                "mean_rationale_age_hours",
                self.mean_rationale_age_hours,
            ),
        )
        for field_name in (
            "calibration_feedback_uptake_ratio",
            "source_linkage_ratio",
            "contradiction_carry_forward_ratio",
            "reuse_quality_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("reuse_status", self.reuse_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _require_row_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchTeamForecastRationaleReuseQualityReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    domain_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamForecastRationaleReuseQualityReasonCodeCount,
            "reason_code_count",
        )
        _require_public_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _require_count_decimal("count", self.count))
        object.__setattr__(
            self,
            "domain_ratio",
            _require_unit_decimal("domain_ratio", self.domain_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamForecastRationaleReuseQualityReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    domain_count: Decimal
    total_rationale_reuse_count: Decimal
    total_calibration_feedback_item_count: Decimal
    total_calibration_feedback_uptake_count: Decimal
    total_linked_rationale_count: Decimal
    total_unresolved_contradiction_count: Decimal
    total_carried_forward_contradiction_count: Decimal
    aggregate_rationale_age_hours: Decimal
    aggregate_calibration_feedback_uptake_ratio: Decimal
    aggregate_source_linkage_ratio: Decimal
    aggregate_contradiction_carry_forward_ratio: Decimal
    max_reuse_quality_pressure: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchTeamForecastRationaleReuseQualityReasonCodeCount, ...]
    rows: tuple[ResearchTeamForecastRationaleReuseQualityRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamForecastRationaleReuseQualityReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_config_version(self.config_version)
        for field_name in (
            "domain_count",
            "total_rationale_reuse_count",
            "total_calibration_feedback_item_count",
            "total_calibration_feedback_uptake_count",
            "total_linked_rationale_count",
            "total_unresolved_contradiction_count",
            "total_carried_forward_contradiction_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "aggregate_rationale_age_hours",
            _require_nonnegative_decimal(
                "aggregate_rationale_age_hours",
                self.aggregate_rationale_age_hours,
            ),
        )
        for field_name in (
            "aggregate_calibration_feedback_uptake_ratio",
            "aggregate_source_linkage_ratio",
            "aggregate_contradiction_carry_forward_ratio",
            "max_reuse_quality_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("report_status", self.report_status)
        object.__setattr__(
            self,
            "reason_codes",
            _require_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _require_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _require_rows(self.rows))
        _require_hard_flags("report", self)
        if self.derived_validation_digest:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != _report_derived_validation_digest(self):
                raise ValueError("derived_validation_digest does not match report")
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        _validate_report_materialized_fields(self)
        _reject_unsafe_public_payload("report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_team_forecast_rationale_reuse_quality_report_payload(self)


def build_research_team_forecast_rationale_reuse_quality_report(
    rationale_items: Iterable[ResearchTeamForecastRationaleReuseQualityInput],
    *,
    config: ResearchTeamForecastRationaleReuseQualityConfig,
    generated_at: datetime,
) -> ResearchTeamForecastRationaleReuseQualityReport:
    if type(config) is not ResearchTeamForecastRationaleReuseQualityConfig:
        raise ValueError("config must be a ResearchTeamForecastRationaleReuseQualityConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(rationale_items)
    _reject_future_inputs(inputs, generated_at=generated_at_utc)
    rows = tuple(
        sorted(
            _rows_for_inputs(inputs, config=config),
            key=_row_sort_key,
        ),
    )
    totals = _report_totals(rows)
    return ResearchTeamForecastRationaleReuseQualityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        domain_count=_count(len(rows)),
        total_rationale_reuse_count=totals["rationale_reuse_count"],
        total_calibration_feedback_item_count=totals[
            "calibration_feedback_item_count"
        ],
        total_calibration_feedback_uptake_count=totals[
            "calibration_feedback_uptake_count"
        ],
        total_linked_rationale_count=totals["linked_rationale_count"],
        total_unresolved_contradiction_count=totals["unresolved_contradiction_count"],
        total_carried_forward_contradiction_count=totals[
            "carried_forward_contradiction_count"
        ],
        aggregate_rationale_age_hours=_aggregate_rationale_age(rows),
        aggregate_calibration_feedback_uptake_ratio=_ratio_or_one(
            totals["calibration_feedback_uptake_count"],
            totals["calibration_feedback_item_count"],
        ),
        aggregate_source_linkage_ratio=_ratio_or_one(
            totals["linked_rationale_count"],
            totals["rationale_reuse_count"],
        ),
        aggregate_contradiction_carry_forward_ratio=_ratio_or_zero(
            totals["carried_forward_contradiction_count"],
            totals["unresolved_contradiction_count"],
        ),
        max_reuse_quality_pressure=max(
            (row.reuse_quality_pressure for row in rows),
            default=ZERO,
        ),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        report_status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_team_forecast_rationale_reuse_quality_report_payload(
    report: ResearchTeamForecastRationaleReuseQualityReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamForecastRationaleReuseQualityReport:
        _require_hard_flags("report", report)
        _validate_report_materialized_fields(report)
        if report.derived_validation_digest != _report_derived_validation_digest(report):
            raise ValueError("derived_validation_digest does not match report")
        payload = _report_public_payload_for_digest(report)
        payload["derived_validation_digest"] = report.derived_validation_digest
        validate_research_team_forecast_rationale_reuse_quality_report_payload(payload)
        return payload
    if type(report) is dict:
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        validate_research_team_forecast_rationale_reuse_quality_report_payload(payload)
        return payload
    raise ValueError("report must be a ResearchTeamForecastRationaleReuseQualityReport")


def research_team_forecast_rationale_reuse_quality_report_digest(
    report: ResearchTeamForecastRationaleReuseQualityReport | dict[str, Any],
) -> str:
    payload = research_team_forecast_rationale_reuse_quality_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


def validate_research_team_forecast_rationale_reuse_quality_report_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    ready = _json_ready(payload)
    if type(ready) is not dict:
        raise ValueError("payload must be a dict")
    _require_payload_hard_flags(ready)
    _reject_unsafe_public_payload("payload", ready)
    _reject_public_numeric_values(ready)
    supplied_digest = _payload_required_string(ready, "derived_validation_digest")
    _require_sha256("derived_validation_digest", supplied_digest)
    if supplied_digest != _public_payload_derived_validation_digest(ready):
        raise ValueError("derived_validation_digest does not match payload")
    return True


def _normalize_inputs(
    rationale_items: Iterable[ResearchTeamForecastRationaleReuseQualityInput],
) -> tuple[ResearchTeamForecastRationaleReuseQualityInput, ...]:
    if isinstance(rationale_items, (str, bytes)):
        raise ValueError("rationale_items must be an iterable")
    try:
        items = tuple(rationale_items)
    except TypeError as exc:
        raise ValueError("rationale_items must be an iterable") from exc
    for item in items:
        if type(item) is not ResearchTeamForecastRationaleReuseQualityInput:
            raise ValueError(
                "rationale_items must contain "
                "ResearchTeamForecastRationaleReuseQualityInput",
            )
        _require_hard_flags("input", item)
    return items


def _reject_future_inputs(
    inputs: tuple[ResearchTeamForecastRationaleReuseQualityInput, ...],
    *,
    generated_at: datetime,
) -> None:
    for item in inputs:
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be in the future")


def _rows_for_inputs(
    inputs: tuple[ResearchTeamForecastRationaleReuseQualityInput, ...],
    *,
    config: ResearchTeamForecastRationaleReuseQualityConfig,
) -> tuple[ResearchTeamForecastRationaleReuseQualityRow, ...]:
    grouped: dict[str, list[ResearchTeamForecastRationaleReuseQualityInput]] = {}
    for item in inputs:
        grouped.setdefault(item.domain_key, []).append(item)
    return tuple(
        _row_for_domain(domain_key, tuple(grouped[domain_key]), config=config)
        for domain_key in sorted(grouped)
    )


def _row_for_domain(
    domain_key: str,
    items: tuple[ResearchTeamForecastRationaleReuseQualityInput, ...],
    *,
    config: ResearchTeamForecastRationaleReuseQualityConfig,
) -> ResearchTeamForecastRationaleReuseQualityRow:
    reuse_count = _sum_decimal(tuple(item.rationale_reuse_count for item in items))
    age_total = _sum_decimal(tuple(item.total_rationale_age_hours for item in items))
    feedback_item_count = _sum_decimal(
        tuple(item.calibration_feedback_item_count for item in items),
    )
    feedback_uptake_count = _sum_decimal(
        tuple(item.calibration_feedback_uptake_count for item in items),
    )
    linked_count = _sum_decimal(tuple(item.linked_rationale_count for item in items))
    contradiction_count = _sum_decimal(
        tuple(item.unresolved_contradiction_count for item in items),
    )
    carried_count = _sum_decimal(
        tuple(item.carried_forward_contradiction_count for item in items),
    )
    mean_age = _measure_ratio_or_zero(age_total, reuse_count)
    uptake_ratio = _ratio_or_one(feedback_uptake_count, feedback_item_count)
    linkage_ratio = _ratio_or_one(linked_count, reuse_count)
    contradiction_ratio = _ratio_or_zero(carried_count, contradiction_count)
    pressure = _reuse_quality_pressure(
        mean_rationale_age_hours=mean_age,
        calibration_feedback_uptake_ratio=uptake_ratio,
        source_linkage_ratio=linkage_ratio,
        contradiction_carry_forward_ratio=contradiction_ratio,
        config=config,
    )
    status = _reuse_status(
        mean_rationale_age_hours=mean_age,
        calibration_feedback_uptake_ratio=uptake_ratio,
        source_linkage_ratio=linkage_ratio,
        contradiction_carry_forward_ratio=contradiction_ratio,
        reuse_quality_pressure=pressure,
        config=config,
    )
    return ResearchTeamForecastRationaleReuseQualityRow(
        domain_key=domain_key,
        rationale_reuse_count=reuse_count,
        mean_rationale_age_hours=mean_age,
        calibration_feedback_item_count=feedback_item_count,
        calibration_feedback_uptake_count=feedback_uptake_count,
        calibration_feedback_uptake_ratio=uptake_ratio,
        linked_rationale_count=linked_count,
        source_linkage_ratio=linkage_ratio,
        unresolved_contradiction_count=contradiction_count,
        carried_forward_contradiction_count=carried_count,
        contradiction_carry_forward_ratio=contradiction_ratio,
        reuse_quality_pressure=pressure,
        reuse_status=status,
        observed_at=max(item.observed_at for item in items),
        reason_codes=_row_reason_codes(
            mean_rationale_age_hours=mean_age,
            calibration_feedback_uptake_ratio=uptake_ratio,
            source_linkage_ratio=linkage_ratio,
            contradiction_carry_forward_ratio=contradiction_ratio,
            reuse_quality_pressure=pressure,
            reuse_status=status,
            config=config,
        ),
    )


def _reuse_quality_pressure(
    *,
    mean_rationale_age_hours: Decimal,
    calibration_feedback_uptake_ratio: Decimal,
    source_linkage_ratio: Decimal,
    contradiction_carry_forward_ratio: Decimal,
    config: ResearchTeamForecastRationaleReuseQualityConfig,
) -> Decimal:
    calibration_gap = _clamp_unit(_quantize(ONE - calibration_feedback_uptake_ratio))
    linkage_gap = _clamp_unit(_quantize(ONE - source_linkage_ratio))
    with localcontext(DECIMAL_CONTEXT):
        pressure = (
            _weighted_pressure_component(
                mean_rationale_age_hours,
                config.block_rationale_age_hours,
                config.freshness_weight,
            )
            + _weighted_pressure_component(
                calibration_gap,
                ONE,
                config.calibration_feedback_weight,
            )
            + _weighted_pressure_component(
                linkage_gap,
                ONE,
                config.source_linkage_weight,
            )
            + _weighted_pressure_component(
                contradiction_carry_forward_ratio,
                ONE,
                config.contradiction_carry_forward_weight,
            )
        )
    return _clamp_unit(_quantize(pressure))


def _weighted_pressure_component(
    value: Decimal,
    block_value: Decimal,
    weight: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(_pressure_fraction(value, block_value) * weight)


def _pressure_fraction(value: Decimal, block_value: Decimal) -> Decimal:
    if block_value <= ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_unit(_quantize(value / block_value))


def _reuse_status(
    *,
    mean_rationale_age_hours: Decimal,
    calibration_feedback_uptake_ratio: Decimal,
    source_linkage_ratio: Decimal,
    contradiction_carry_forward_ratio: Decimal,
    reuse_quality_pressure: Decimal,
    config: ResearchTeamForecastRationaleReuseQualityConfig,
) -> str:
    calibration_gap = _clamp_unit(_quantize(ONE - calibration_feedback_uptake_ratio))
    linkage_gap = _clamp_unit(_quantize(ONE - source_linkage_ratio))
    if (
        mean_rationale_age_hours >= config.block_rationale_age_hours
        or calibration_gap >= config.block_calibration_feedback_gap_ratio
        or linkage_gap >= config.block_source_linkage_gap_ratio
        or contradiction_carry_forward_ratio
        >= config.block_contradiction_carry_forward_ratio
        or reuse_quality_pressure >= config.block_reuse_quality_pressure
    ):
        return "block"
    if (
        mean_rationale_age_hours >= config.watch_rationale_age_hours
        or calibration_gap >= config.watch_calibration_feedback_gap_ratio
        or linkage_gap >= config.watch_source_linkage_gap_ratio
        or contradiction_carry_forward_ratio
        >= config.watch_contradiction_carry_forward_ratio
        or reuse_quality_pressure >= config.watch_reuse_quality_pressure
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    mean_rationale_age_hours: Decimal,
    calibration_feedback_uptake_ratio: Decimal,
    source_linkage_ratio: Decimal,
    contradiction_carry_forward_ratio: Decimal,
    reuse_quality_pressure: Decimal,
    reuse_status: str,
    config: ResearchTeamForecastRationaleReuseQualityConfig,
) -> tuple[str, ...]:
    reason_codes = [f"rationale_reuse_quality_{reuse_status}"]
    if reuse_status == "pass":
        return _require_row_reason_codes(tuple(reason_codes))
    calibration_gap = _clamp_unit(_quantize(ONE - calibration_feedback_uptake_ratio))
    linkage_gap = _clamp_unit(_quantize(ONE - source_linkage_ratio))
    if mean_rationale_age_hours >= config.block_rationale_age_hours:
        reason_codes.append("rationale_freshness_block")
    elif mean_rationale_age_hours >= config.watch_rationale_age_hours:
        reason_codes.append("rationale_freshness_watch")
    if calibration_gap >= config.block_calibration_feedback_gap_ratio:
        reason_codes.append("calibration_feedback_gap_block")
    elif calibration_gap >= config.watch_calibration_feedback_gap_ratio:
        reason_codes.append("calibration_feedback_gap_watch")
    if linkage_gap >= config.block_source_linkage_gap_ratio:
        reason_codes.append("source_linkage_gap_block")
    elif linkage_gap >= config.watch_source_linkage_gap_ratio:
        reason_codes.append("source_linkage_gap_watch")
    if contradiction_carry_forward_ratio >= config.block_contradiction_carry_forward_ratio:
        reason_codes.append("contradiction_carry_forward_block")
    elif (
        contradiction_carry_forward_ratio
        >= config.watch_contradiction_carry_forward_ratio
    ):
        reason_codes.append("contradiction_carry_forward_watch")
    if reuse_quality_pressure >= config.block_reuse_quality_pressure:
        reason_codes.append("reuse_quality_pressure_block")
    elif reuse_quality_pressure >= config.watch_reuse_quality_pressure:
        reason_codes.append("reuse_quality_pressure_watch")
    return _require_row_reason_codes(tuple(reason_codes))


def _report_totals(
    rows: tuple[ResearchTeamForecastRationaleReuseQualityRow, ...],
) -> dict[str, Decimal]:
    return {
        "rationale_reuse_count": _sum_decimal(
            tuple(row.rationale_reuse_count for row in rows),
        ),
        "calibration_feedback_item_count": _sum_decimal(
            tuple(row.calibration_feedback_item_count for row in rows),
        ),
        "calibration_feedback_uptake_count": _sum_decimal(
            tuple(row.calibration_feedback_uptake_count for row in rows),
        ),
        "linked_rationale_count": _sum_decimal(
            tuple(row.linked_rationale_count for row in rows),
        ),
        "unresolved_contradiction_count": _sum_decimal(
            tuple(row.unresolved_contradiction_count for row in rows),
        ),
        "carried_forward_contradiction_count": _sum_decimal(
            tuple(row.carried_forward_contradiction_count for row in rows),
        ),
    }


def _aggregate_rationale_age(
    rows: tuple[ResearchTeamForecastRationaleReuseQualityRow, ...],
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        weighted_age = _sum_decimal(
            tuple(row.mean_rationale_age_hours * row.rationale_reuse_count for row in rows),
        )
    return _measure_ratio_or_zero(
        weighted_age,
        _sum_decimal(tuple(row.rationale_reuse_count for row in rows)),
    )


def _status_count(
    rows: tuple[ResearchTeamForecastRationaleReuseQualityRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.reuse_status == status))


def _report_status(rows: tuple[ResearchTeamForecastRationaleReuseQualityRow, ...]) -> str:
    if any(row.reuse_status == "block" for row in rows):
        return "block"
    if any(row.reuse_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamForecastRationaleReuseQualityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REPORT_REASON_CODE,)
    present = frozenset(reason_code for row in rows for reason_code in row.reason_codes)
    reason_codes = [f"rationale_reuse_quality_report_{_report_status(rows)}"]
    for reason_code in REPORT_REASON_PRIORITY:
        if reason_code in present:
            reason_codes.append(reason_code)
    return _require_report_reason_codes(tuple(reason_codes))


def _reason_code_counts(
    rows: tuple[ResearchTeamForecastRationaleReuseQualityRow, ...],
) -> tuple[ResearchTeamForecastRationaleReuseQualityReasonCodeCount, ...]:
    if not rows:
        return ()
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    denominator = _count(len(rows))
    priority = {reason_code: index for index, reason_code in enumerate(REPORT_REASON_PRIORITY)}
    return tuple(
        ResearchTeamForecastRationaleReuseQualityReasonCodeCount(
            reason_code=reason_code,
            count=count,
            domain_ratio=_ratio_or_zero(count, denominator),
        )
        for count, reason_code in sorted(
            ((_count(count), reason_code) for reason_code, count in counter.items()),
            key=lambda item: (priority.get(item[1], 999), item[1]),
        )
    )


def _row_sort_key(
    row: ResearchTeamForecastRationaleReuseQualityRow,
) -> tuple[Decimal, Decimal, str]:
    return (-STATUS_WEIGHT[row.reuse_status], -row.reuse_quality_pressure, row.domain_key)


def _validate_config(config: ResearchTeamForecastRationaleReuseQualityConfig) -> None:
    if config.block_rationale_age_hours <= ZERO:
        raise ValueError("block_rationale_age_hours must be greater than zero")
    for watch_field, block_field in (
        (
            "watch_rationale_age_hours",
            "block_rationale_age_hours",
        ),
        (
            "watch_calibration_feedback_gap_ratio",
            "block_calibration_feedback_gap_ratio",
        ),
        (
            "watch_source_linkage_gap_ratio",
            "block_source_linkage_gap_ratio",
        ),
        (
            "watch_contradiction_carry_forward_ratio",
            "block_contradiction_carry_forward_ratio",
        ),
        (
            "watch_reuse_quality_pressure",
            "block_reuse_quality_pressure",
        ),
    ):
        if getattr(config, watch_field) > getattr(config, block_field):
            raise ValueError(f"{watch_field} must not exceed {block_field}")
    weight_sum = _sum_decimal(
        (
            config.freshness_weight,
            config.calibration_feedback_weight,
            config.source_linkage_weight,
            config.contradiction_carry_forward_weight,
        ),
    )
    if weight_sum != ONE:
        raise ValueError("reuse quality weights must sum to one")


def _validate_input(item: ResearchTeamForecastRationaleReuseQualityInput) -> None:
    if item.rationale_reuse_count == ZERO and item.total_rationale_age_hours != ZERO:
        raise ValueError("total_rationale_age_hours requires rationale_reuse_count")
    if item.linked_rationale_count > item.rationale_reuse_count:
        raise ValueError("linked_rationale_count must not exceed rationale_reuse_count")
    if item.calibration_feedback_uptake_count > item.calibration_feedback_item_count:
        raise ValueError(
            "calibration_feedback_uptake_count must not exceed "
            "calibration_feedback_item_count",
        )
    if item.carried_forward_contradiction_count > item.unresolved_contradiction_count:
        raise ValueError(
            "carried_forward_contradiction_count must not exceed "
            "unresolved_contradiction_count",
        )


def _validate_row(row: ResearchTeamForecastRationaleReuseQualityRow) -> None:
    if row.linked_rationale_count > row.rationale_reuse_count:
        raise ValueError("linked_rationale_count must not exceed rationale_reuse_count")
    if row.calibration_feedback_uptake_count > row.calibration_feedback_item_count:
        raise ValueError(
            "calibration_feedback_uptake_count must not exceed "
            "calibration_feedback_item_count",
        )
    if row.carried_forward_contradiction_count > row.unresolved_contradiction_count:
        raise ValueError(
            "carried_forward_contradiction_count must not exceed "
            "unresolved_contradiction_count",
        )
    expected_status_reason = f"rationale_reuse_quality_{row.reuse_status}"
    if not row.reason_codes or row.reason_codes[0] != expected_status_reason:
        raise ValueError("reuse_status must match reason_codes")
    if row.reuse_status == "pass" and row.reason_codes != (
        "rationale_reuse_quality_pass",
    ):
        raise ValueError("pass rows require rationale_reuse_quality_pass")
    if row.reuse_status != "pass" and "rationale_reuse_quality_pass" in row.reason_codes:
        raise ValueError("queued rows must not contain pass reason_codes")


def _validate_report_materialized_fields(
    report: ResearchTeamForecastRationaleReuseQualityReport,
) -> None:
    rows = report.rows
    totals = _report_totals(rows)
    checks = {
        "domain_count": _count(len(rows)),
        "total_rationale_reuse_count": totals["rationale_reuse_count"],
        "total_calibration_feedback_item_count": totals[
            "calibration_feedback_item_count"
        ],
        "total_calibration_feedback_uptake_count": totals[
            "calibration_feedback_uptake_count"
        ],
        "total_linked_rationale_count": totals["linked_rationale_count"],
        "total_unresolved_contradiction_count": totals["unresolved_contradiction_count"],
        "total_carried_forward_contradiction_count": totals[
            "carried_forward_contradiction_count"
        ],
        "aggregate_rationale_age_hours": _aggregate_rationale_age(rows),
        "aggregate_calibration_feedback_uptake_ratio": _ratio_or_one(
            totals["calibration_feedback_uptake_count"],
            totals["calibration_feedback_item_count"],
        ),
        "aggregate_source_linkage_ratio": _ratio_or_one(
            totals["linked_rationale_count"],
            totals["rationale_reuse_count"],
        ),
        "aggregate_contradiction_carry_forward_ratio": _ratio_or_zero(
            totals["carried_forward_contradiction_count"],
            totals["unresolved_contradiction_count"],
        ),
        "max_reuse_quality_pressure": max(
            (row.reuse_quality_pressure for row in rows),
            default=ZERO,
        ),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
    }
    for field_name, expected in checks.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _require_rows(
    rows: tuple[ResearchTeamForecastRationaleReuseQualityRow, ...],
) -> tuple[ResearchTeamForecastRationaleReuseQualityRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchTeamForecastRationaleReuseQualityRow:
            raise ValueError(
                "rows must contain ResearchTeamForecastRationaleReuseQualityRow",
            )
        _require_hard_flags("row", row)
        if row.domain_key in seen:
            raise ValueError("rows must contain unique domain_key values")
        seen.add(row.domain_key)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    return normalized


def _require_reason_code_counts(
    counts: tuple[ResearchTeamForecastRationaleReuseQualityReasonCodeCount, ...],
) -> tuple[ResearchTeamForecastRationaleReuseQualityReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(counts)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen: set[str] = set()
    priority = {reason_code: index for index, reason_code in enumerate(REPORT_REASON_PRIORITY)}
    for item in normalized:
        if type(item) is not ResearchTeamForecastRationaleReuseQualityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTeamForecastRationaleReuseQualityReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must contain unique reason_code values")
        seen.add(item.reason_code)
    if normalized != tuple(
        sorted(
            normalized,
            key=lambda item: (priority.get(item.reason_code, 999), item.reason_code),
        ),
    ):
        raise ValueError("reason_code_counts must use deterministic sequence")
    return normalized


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_payload_hard_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"payload {field_name} must be True")


def _require_config_version(value: object) -> None:
    if type(value) is not str:
        raise ValueError("config_version must be a string")
    if value != DEFAULT_RESEARCH_TEAM_FORECAST_RATIONALE_REUSE_QUALITY_CONFIG_VERSION:
        raise ValueError("config_version must be supported")
    _reject_unsafe_public_text("config_version", value)


def _require_public_code(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a public code")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a public code")
    if any(character not in _PUBLIC_CODE_CHARS for character in value):
        raise ValueError(f"{field_name} must be a public code")
    _reject_unsafe_public_text(field_name, value)
    return value


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in RATIONALE_REUSE_QUALITY_STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _require_row_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must be non-empty")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_public_code("reason_code", reason_code)
        if reason_code not in ROW_REASON_CODES:
            raise ValueError("reason_code must be supported")
        if reason_code in seen:
            raise ValueError("reason_codes must not contain duplicates")
        seen.add(reason_code)
    return reason_codes


def _require_report_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must be non-empty")
    supported = {
        EMPTY_REPORT_REASON_CODE,
        "rationale_reuse_quality_report_pass",
        "rationale_reuse_quality_report_watch",
        "rationale_reuse_quality_report_block",
        *REPORT_REASON_PRIORITY,
    }
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_public_code("reason_code", reason_code)
        if reason_code not in supported:
            raise ValueError("reason_code must be supported")
        if reason_code in seen:
            raise ValueError("reason_codes must not contain duplicates")
        seen.add(reason_code)
    return reason_codes


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize(value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return normalized


def _require_unit_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    with localcontext(DECIMAL_CONTEXT):
        for value in values:
            total += value
    return _quantize(total)


def _ratio_or_zero(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_unit(_quantize(numerator / denominator))


def _measure_ratio_or_zero(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _ratio_or_one(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ONE
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_unit(_quantize(numerator / denominator))


def _clamp_unit(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return value


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if len(value) != 64 or any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Decimal):
        return format(_quantize(value), "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(child) for key, child in value.items()}
    return value


def _report_public_payload_for_digest(
    report: ResearchTeamForecastRationaleReuseQualityReport,
) -> dict[str, Any]:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a dict")
    payload.pop("derived_validation_digest", None)
    return payload


def _report_derived_validation_digest(
    report: ResearchTeamForecastRationaleReuseQualityReport,
) -> str:
    return _payload_digest(_report_public_payload_for_digest(report))


def _public_payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    payload_without_digest = dict(payload)
    payload_without_digest.pop("derived_validation_digest", None)
    return _payload_digest(payload_without_digest)


def _payload_digest(payload: dict[str, Any]) -> str:
    ready = _json_ready(payload)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _reject_public_numeric_values(value: Any) -> None:
    if type(value) in (float, int):
        raise ValueError("public payload numeric values must be decimal strings")
    if isinstance(value, dict):
        for child in value.values():
            _reject_public_numeric_values(child)
    elif isinstance(value, list):
        for child in value:
            _reject_public_numeric_values(child)


def _reject_unsafe_public_payload(label: str, value: Any) -> None:
    ready = _json_ready(value)
    _reject_unsafe_public_payload_ready(label, ready)


def _reject_unsafe_public_payload_ready(label: str, value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            _reject_unsafe_public_text(f"{label} key", str(key))
            _reject_unsafe_public_payload_ready(f"{label}.{key}", child)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_unsafe_public_payload_ready(f"{label}[{index}]", child)
    elif type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    for fragment in _UNSAFE_TEXT_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"unsafe public payload: {field_name}")
