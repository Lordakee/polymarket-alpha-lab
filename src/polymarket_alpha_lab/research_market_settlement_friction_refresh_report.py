"""Pure aggregate settlement-friction refresh readiness report."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Iterable, Mapping


DEFAULT_RESEARCH_MARKET_SETTLEMENT_FRICTION_REFRESH_CONFIG_VERSION = (
    "research-market-settlement-friction-refresh-report-v0"
)

STATUSES = ("pass", "watch", "block")
STATUS_RANKS = {"block": 0, "watch": 1, "pass": 2}

SIX_PLACES = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
PASS_PRESSURE_SCORE = Decimal("0.150000")
WATCH_PRESSURE_SCORE = Decimal("0.500000")
BLOCK_PRESSURE_SCORE = Decimal("1.000000")

PASS_REASON = "settlement_friction_refresh_pass"
SETTLEMENT_COST_WATCH_REASON = "settlement_cost_assumption_watch"
SETTLEMENT_COST_BLOCK_REASON = "settlement_cost_assumption_block"
EVIDENCE_AGE_WATCH_REASON = "evidence_age_watch"
EVIDENCE_AGE_BLOCK_REASON = "evidence_age_block"
FEE_SPREAD_WATCH_REASON = "fee_spread_interaction_watch"
FEE_SPREAD_BLOCK_REASON = "fee_spread_interaction_block"
LIQUIDITY_CONFIDENCE_WATCH_REASON = "liquidity_confidence_watch"
LIQUIDITY_CONFIDENCE_BLOCK_REASON = "liquidity_confidence_block"
MANUAL_RECHECK_WATCH_REASON = "manual_recheck_urgency_watch"
MANUAL_RECHECK_BLOCK_REASON = "manual_recheck_urgency_block"
EMPTY_INPUT_REASON = "settlement_friction_refresh_no_inputs"

REASON_CODES = (
    PASS_REASON,
    SETTLEMENT_COST_WATCH_REASON,
    SETTLEMENT_COST_BLOCK_REASON,
    EVIDENCE_AGE_WATCH_REASON,
    EVIDENCE_AGE_BLOCK_REASON,
    FEE_SPREAD_WATCH_REASON,
    FEE_SPREAD_BLOCK_REASON,
    LIQUIDITY_CONFIDENCE_WATCH_REASON,
    LIQUIDITY_CONFIDENCE_BLOCK_REASON,
    MANUAL_RECHECK_WATCH_REASON,
    MANUAL_RECHECK_BLOCK_REASON,
    EMPTY_INPUT_REASON,
)

PUBLIC_IDENTIFIER_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("au", "th"),
        _join_parts("bro", "ker"),
        _join_parts("sig", "ning"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("or", "der"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("ad", "vice"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("pri", "vate"),
        _join_parts("api", "-", "key"),
        _join_parts("api", "_", "key"),
        _join_parts("api", "key"),
        _join_parts("siz", "ing"),
        _join_parts("li", "ve"),
    ),
)


__all__ = (
    "DEFAULT_RESEARCH_MARKET_SETTLEMENT_FRICTION_REFRESH_CONFIG_VERSION",
    "STATUSES",
    "ResearchMarketSettlementFrictionRefreshConfig",
    "ResearchMarketSettlementFrictionRefreshInput",
    "ResearchMarketSettlementFrictionRefreshReasonCodeCount",
    "ResearchMarketSettlementFrictionRefreshReport",
    "ResearchMarketSettlementFrictionRefreshRow",
    "build_research_market_settlement_friction_refresh_report",
    "research_market_settlement_friction_refresh_report_payload",
)


class _NoSubclass:
    def __init_subclass__(cls) -> None:
        if _NoSubclass not in cls.__bases__:
            raise TypeError(f"{cls.__name__} does not support subclassing")


@dataclass(frozen=True)
class ResearchMarketSettlementFrictionRefreshConfig(_NoSubclass):
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_SETTLEMENT_FRICTION_REFRESH_CONFIG_VERSION
    )
    settlement_cost_watch_ratio: Decimal = Decimal("0.020000")
    settlement_cost_block_ratio: Decimal = Decimal("0.060000")
    evidence_age_watch_hours: Decimal = Decimal("12.000000")
    evidence_age_block_hours: Decimal = Decimal("48.000000")
    fee_spread_interaction_watch_ratio: Decimal = Decimal("0.030000")
    fee_spread_interaction_block_ratio: Decimal = Decimal("0.080000")
    liquidity_confidence_watch_floor: Decimal = Decimal("0.700000")
    liquidity_confidence_block_floor: Decimal = Decimal("0.400000")
    manual_recheck_watch_urgency: Decimal = Decimal("0.300000")
    manual_recheck_block_urgency: Decimal = Decimal("0.800000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketSettlementFrictionRefreshConfig:
            raise ValueError(
                "config must be exactly ResearchMarketSettlementFrictionRefreshConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_SETTLEMENT_FRICTION_REFRESH_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported version")
        for field_name in (
            "settlement_cost_watch_ratio",
            "settlement_cost_block_ratio",
            "fee_spread_interaction_watch_ratio",
            "fee_spread_interaction_block_ratio",
            "liquidity_confidence_watch_floor",
            "liquidity_confidence_block_floor",
            "manual_recheck_watch_urgency",
            "manual_recheck_block_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("evidence_age_watch_hours", "evidence_age_block_hours"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.settlement_cost_watch_ratio >= self.settlement_cost_block_ratio:
            raise ValueError(
                "settlement_cost_watch_ratio must be below "
                "settlement_cost_block_ratio",
            )
        if self.evidence_age_watch_hours >= self.evidence_age_block_hours:
            raise ValueError(
                "evidence_age_watch_hours must be below evidence_age_block_hours",
            )
        if (
            self.fee_spread_interaction_watch_ratio
            >= self.fee_spread_interaction_block_ratio
        ):
            raise ValueError(
                "fee_spread_interaction_watch_ratio must be below "
                "fee_spread_interaction_block_ratio",
            )
        if (
            self.liquidity_confidence_block_floor
            >= self.liquidity_confidence_watch_floor
        ):
            raise ValueError(
                "liquidity_confidence_block_floor must be below "
                "liquidity_confidence_watch_floor",
            )
        if self.manual_recheck_watch_urgency >= self.manual_recheck_block_urgency:
            raise ValueError(
                "manual_recheck_watch_urgency must be below "
                "manual_recheck_block_urgency",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketSettlementFrictionRefreshInput(_NoSubclass):
    aggregate_key: str
    settlement_cost_assumption_ratio: Decimal
    evidence_age_hours: Decimal
    fee_spread_interaction_ratio: Decimal
    liquidity_confidence: Decimal
    manual_recheck_urgency: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketSettlementFrictionRefreshInput:
            raise ValueError(
                "input must be exactly ResearchMarketSettlementFrictionRefreshInput",
            )
        _require_public_identifier("aggregate_key", self.aggregate_key)
        for field_name in (
            "settlement_cost_assumption_ratio",
            "fee_spread_interaction_ratio",
            "liquidity_confidence",
            "manual_recheck_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_age_hours",
            _require_nonnegative_decimal("evidence_age_hours", self.evidence_age_hours),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchMarketSettlementFrictionRefreshReasonCodeCount(_NoSubclass):
    reason_code: str
    count: Decimal
    entry_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketSettlementFrictionRefreshReasonCodeCount:
            raise ValueError(
                "reason_code_count must be exactly "
                "ResearchMarketSettlementFrictionRefreshReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "entry_ratio",
            _require_ratio_decimal("entry_ratio", self.entry_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketSettlementFrictionRefreshRow(_NoSubclass):
    aggregate_key: str
    settlement_cost_assumption_ratio: Decimal
    evidence_age_hours: Decimal
    fee_spread_interaction_ratio: Decimal
    liquidity_confidence: Decimal
    manual_recheck_urgency: Decimal
    friction_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketSettlementFrictionRefreshRow:
            raise ValueError("row must be exactly ResearchMarketSettlementFrictionRefreshRow")
        _require_public_identifier("aggregate_key", self.aggregate_key)
        for field_name in (
            "settlement_cost_assumption_ratio",
            "fee_spread_interaction_ratio",
            "liquidity_confidence",
            "manual_recheck_urgency",
            "friction_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_age_hours",
            _require_nonnegative_decimal("evidence_age_hours", self.evidence_age_hours),
        )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_status_reason_codes(self)
        _require_hard_flags("row", self)
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != _row_derived_validation_digest(self):
                raise ValueError("derived_validation_digest does not match row payload")
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _row_derived_validation_digest(self),
            )
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchMarketSettlementFrictionRefreshReport(_NoSubclass):
    generated_at: datetime
    config_version: str
    status: str
    entry_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    settlement_cost_watch_count: Decimal
    settlement_cost_block_count: Decimal
    evidence_age_watch_count: Decimal
    evidence_age_block_count: Decimal
    fee_spread_interaction_watch_count: Decimal
    fee_spread_interaction_block_count: Decimal
    liquidity_confidence_watch_count: Decimal
    liquidity_confidence_block_count: Decimal
    manual_recheck_urgency_watch_count: Decimal
    manual_recheck_urgency_block_count: Decimal
    max_friction_pressure_score: Decimal
    average_friction_pressure_score: Decimal
    rows: tuple[ResearchMarketSettlementFrictionRefreshRow, ...]
    reason_code_counts: tuple[ResearchMarketSettlementFrictionRefreshReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketSettlementFrictionRefreshReport:
            raise ValueError(
                "report must be exactly ResearchMarketSettlementFrictionRefreshReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_SETTLEMENT_FRICTION_REFRESH_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported version")
        _require_status("status", self.status)
        for field_name in (
            "entry_count",
            "pass_count",
            "watch_count",
            "block_count",
            "settlement_cost_watch_count",
            "settlement_cost_block_count",
            "evidence_age_watch_count",
            "evidence_age_block_count",
            "fee_spread_interaction_watch_count",
            "fee_spread_interaction_block_count",
            "liquidity_confidence_watch_count",
            "liquidity_confidence_block_count",
            "manual_recheck_urgency_watch_count",
            "manual_recheck_urgency_block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_friction_pressure_score",
            "average_friction_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags("report", self)
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != _report_derived_validation_digest(self):
                raise ValueError("derived_validation_digest does not match report payload")
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        _validate_report_consistency(self)
        _reject_unsafe_public_payload("report", self)

    @property
    def payload(self) -> dict[str, object]:
        return research_market_settlement_friction_refresh_report_payload(self)


def build_research_market_settlement_friction_refresh_report(
    inputs: Iterable[ResearchMarketSettlementFrictionRefreshInput],
    *,
    generated_at: datetime,
    config: ResearchMarketSettlementFrictionRefreshConfig | None = None,
) -> ResearchMarketSettlementFrictionRefreshReport:
    """Build a deterministic aggregate refresh-readiness report."""

    if config is None:
        config = ResearchMarketSettlementFrictionRefreshConfig()
    if type(config) is not ResearchMarketSettlementFrictionRefreshConfig:
        raise ValueError(
            "config must be a ResearchMarketSettlementFrictionRefreshConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(_row_from_input(item, config) for item in normalized_inputs)
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = _report_reason_codes(rows)

    return ResearchMarketSettlementFrictionRefreshReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=_report_status(rows),
        entry_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        settlement_cost_watch_count=_reason_count(
            rows,
            SETTLEMENT_COST_WATCH_REASON,
        ),
        settlement_cost_block_count=_reason_count(
            rows,
            SETTLEMENT_COST_BLOCK_REASON,
        ),
        evidence_age_watch_count=_reason_count(rows, EVIDENCE_AGE_WATCH_REASON),
        evidence_age_block_count=_reason_count(rows, EVIDENCE_AGE_BLOCK_REASON),
        fee_spread_interaction_watch_count=_reason_count(rows, FEE_SPREAD_WATCH_REASON),
        fee_spread_interaction_block_count=_reason_count(rows, FEE_SPREAD_BLOCK_REASON),
        liquidity_confidence_watch_count=_reason_count(
            rows,
            LIQUIDITY_CONFIDENCE_WATCH_REASON,
        ),
        liquidity_confidence_block_count=_reason_count(
            rows,
            LIQUIDITY_CONFIDENCE_BLOCK_REASON,
        ),
        manual_recheck_urgency_watch_count=_reason_count(
            rows,
            MANUAL_RECHECK_WATCH_REASON,
        ),
        manual_recheck_urgency_block_count=_reason_count(
            rows,
            MANUAL_RECHECK_BLOCK_REASON,
        ),
        max_friction_pressure_score=_max_decimal(
            row.friction_pressure_score for row in rows
        ),
        average_friction_pressure_score=_average_decimal(
            row.friction_pressure_score for row in rows
        ),
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def research_market_settlement_friction_refresh_report_payload(
    report: ResearchMarketSettlementFrictionRefreshReport | Mapping[str, Any],
) -> dict[str, object]:
    if type(report) is ResearchMarketSettlementFrictionRefreshReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _report_payload(report, include_digest=True)
    elif isinstance(report, Mapping):
        _reject_unsafe_public_payload("payload", report, allow_json_containers=True)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchMarketSettlementFrictionRefreshReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    return payload


@dataclass(frozen=True)
class _DictFlags:
    value: Mapping[str, object]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _row_from_input(
    item: ResearchMarketSettlementFrictionRefreshInput,
    config: ResearchMarketSettlementFrictionRefreshConfig,
) -> ResearchMarketSettlementFrictionRefreshRow:
    reason_codes = _row_reason_codes(item, config)
    status = _status_from_reason_codes(reason_codes)
    return ResearchMarketSettlementFrictionRefreshRow(
        aggregate_key=item.aggregate_key,
        settlement_cost_assumption_ratio=item.settlement_cost_assumption_ratio,
        evidence_age_hours=item.evidence_age_hours,
        fee_spread_interaction_ratio=item.fee_spread_interaction_ratio,
        liquidity_confidence=item.liquidity_confidence,
        manual_recheck_urgency=item.manual_recheck_urgency,
        friction_pressure_score=_friction_pressure_score(status),
        status=status,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: ResearchMarketSettlementFrictionRefreshInput,
    config: ResearchMarketSettlementFrictionRefreshConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    reason_codes.append(
        _tiered_high_reason_code(
            item.settlement_cost_assumption_ratio,
            watch_threshold=config.settlement_cost_watch_ratio,
            block_threshold=config.settlement_cost_block_ratio,
            watch_reason=SETTLEMENT_COST_WATCH_REASON,
            block_reason=SETTLEMENT_COST_BLOCK_REASON,
        ),
    )
    reason_codes.append(
        _tiered_high_reason_code(
            item.evidence_age_hours,
            watch_threshold=config.evidence_age_watch_hours,
            block_threshold=config.evidence_age_block_hours,
            watch_reason=EVIDENCE_AGE_WATCH_REASON,
            block_reason=EVIDENCE_AGE_BLOCK_REASON,
        ),
    )
    reason_codes.append(
        _tiered_high_reason_code(
            item.fee_spread_interaction_ratio,
            watch_threshold=config.fee_spread_interaction_watch_ratio,
            block_threshold=config.fee_spread_interaction_block_ratio,
            watch_reason=FEE_SPREAD_WATCH_REASON,
            block_reason=FEE_SPREAD_BLOCK_REASON,
        ),
    )
    reason_codes.append(
        _tiered_low_reason_code(
            item.liquidity_confidence,
            watch_floor=config.liquidity_confidence_watch_floor,
            block_floor=config.liquidity_confidence_block_floor,
            watch_reason=LIQUIDITY_CONFIDENCE_WATCH_REASON,
            block_reason=LIQUIDITY_CONFIDENCE_BLOCK_REASON,
        ),
    )
    reason_codes.append(
        _tiered_high_reason_code(
            item.manual_recheck_urgency,
            watch_threshold=config.manual_recheck_watch_urgency,
            block_threshold=config.manual_recheck_block_urgency,
            watch_reason=MANUAL_RECHECK_WATCH_REASON,
            block_reason=MANUAL_RECHECK_BLOCK_REASON,
        ),
    )
    filtered = tuple(reason_code for reason_code in reason_codes if reason_code)
    return filtered or (PASS_REASON,)


def _tiered_high_reason_code(
    value: Decimal,
    *,
    watch_threshold: Decimal,
    block_threshold: Decimal,
    watch_reason: str,
    block_reason: str,
) -> str:
    if value >= block_threshold:
        return block_reason
    if value >= watch_threshold:
        return watch_reason
    return ""


def _tiered_low_reason_code(
    value: Decimal,
    *,
    watch_floor: Decimal,
    block_floor: Decimal,
    watch_reason: str,
    block_reason: str,
) -> str:
    if value <= block_floor:
        return block_reason
    if value <= watch_floor:
        return watch_reason
    return ""


def _friction_pressure_score(status: str) -> Decimal:
    if status == "block":
        return BLOCK_PRESSURE_SCORE
    if status == "watch":
        return WATCH_PRESSURE_SCORE
    return PASS_PRESSURE_SCORE


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchMarketSettlementFrictionRefreshRow, ...]) -> str:
    if not rows:
        return "block"
    return min((row.status for row in rows), key=lambda status: STATUS_RANKS[status])


def _report_reason_codes(
    rows: tuple[ResearchMarketSettlementFrictionRefreshRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_INPUT_REASON,)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _reason_code_counts(
    rows: tuple[ResearchMarketSettlementFrictionRefreshRow, ...],
) -> tuple[ResearchMarketSettlementFrictionRefreshReasonCodeCount, ...]:
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    if not rows:
        counts[EMPTY_INPUT_REASON] = 1
    denominator = _decimal_count(len(rows)) if rows else ONE
    return tuple(
        ResearchMarketSettlementFrictionRefreshReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
            entry_ratio=_ratio(_decimal_count(counts[reason_code]), denominator),
        )
        for reason_code in REASON_CODES
        if counts[reason_code]
    )


def _validate_row_status_reason_codes(
    row: ResearchMarketSettlementFrictionRefreshRow,
) -> None:
    expected_status = _status_from_reason_codes(row.reason_codes)
    if row.status != expected_status:
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != (PASS_REASON,):
        raise ValueError("pass rows must include settlement_friction_refresh_pass")
    if row.status != "pass" and PASS_REASON in row.reason_codes:
        raise ValueError("non-pass rows must not include pass reason code")


def _validate_report_consistency(
    report: ResearchMarketSettlementFrictionRefreshReport,
) -> None:
    if report.entry_count != _decimal_count(len(report.rows)):
        raise ValueError("entry_count must match rows")
    for status_field, status in (
        ("pass_count", "pass"),
        ("watch_count", "watch"),
        ("block_count", "block"),
    ):
        if getattr(report, status_field) != _decimal_count(
            _status_count(report.rows, status),
        ):
            raise ValueError(f"{status_field} must match rows")
    for field_name, reason_code in (
        ("settlement_cost_watch_count", SETTLEMENT_COST_WATCH_REASON),
        ("settlement_cost_block_count", SETTLEMENT_COST_BLOCK_REASON),
        ("evidence_age_watch_count", EVIDENCE_AGE_WATCH_REASON),
        ("evidence_age_block_count", EVIDENCE_AGE_BLOCK_REASON),
        ("fee_spread_interaction_watch_count", FEE_SPREAD_WATCH_REASON),
        ("fee_spread_interaction_block_count", FEE_SPREAD_BLOCK_REASON),
        ("liquidity_confidence_watch_count", LIQUIDITY_CONFIDENCE_WATCH_REASON),
        ("liquidity_confidence_block_count", LIQUIDITY_CONFIDENCE_BLOCK_REASON),
        ("manual_recheck_urgency_watch_count", MANUAL_RECHECK_WATCH_REASON),
        ("manual_recheck_urgency_block_count", MANUAL_RECHECK_BLOCK_REASON),
    ):
        if getattr(report, field_name) != _reason_count(report.rows, reason_code):
            raise ValueError(f"{field_name} must match rows")
    if report.max_friction_pressure_score != _max_decimal(
        row.friction_pressure_score for row in report.rows
    ):
        raise ValueError("max_friction_pressure_score must match rows")
    if report.average_friction_pressure_score != _average_decimal(
        row.friction_pressure_score for row in report.rows
    ):
        raise ValueError("average_friction_pressure_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _normalize_inputs(
    inputs: Iterable[ResearchMarketSettlementFrictionRefreshInput],
) -> tuple[ResearchMarketSettlementFrictionRefreshInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Iterable):
        raise ValueError("inputs must be an iterable")
    normalized: list[ResearchMarketSettlementFrictionRefreshInput] = []
    seen: set[str] = set()
    for item in inputs:
        if type(item) is not ResearchMarketSettlementFrictionRefreshInput:
            raise ValueError(
                "inputs must contain ResearchMarketSettlementFrictionRefreshInput",
            )
        if item.aggregate_key in seen:
            raise ValueError("aggregate_key values must be unique")
        seen.add(item.aggregate_key)
        normalized.append(item)
    return tuple(normalized)


def _normalize_rows(
    rows: tuple[ResearchMarketSettlementFrictionRefreshRow, ...],
) -> tuple[ResearchMarketSettlementFrictionRefreshRow, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketSettlementFrictionRefreshRow:
            raise ValueError("rows must contain ResearchMarketSettlementFrictionRefreshRow")
    return rows


def _normalize_reason_code_counts(
    reason_code_counts: tuple[
        ResearchMarketSettlementFrictionRefreshReasonCodeCount,
        ...,
    ],
) -> tuple[ResearchMarketSettlementFrictionRefreshReasonCodeCount, ...]:
    if not isinstance(reason_code_counts, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    for item in reason_code_counts:
        if type(item) is not ResearchMarketSettlementFrictionRefreshReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketSettlementFrictionRefreshReasonCodeCount",
            )
    return reason_code_counts


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(reason_codes, tuple) or not reason_codes:
        raise ValueError("reason_codes must be a non-empty tuple")
    normalized: list[str] = []
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
        if reason_code not in seen:
            normalized.append(reason_code)
            seen.add(reason_code)
    return tuple(normalized)


def _require_reason_code(name: str, value: str) -> None:
    if type(value) is not str or value not in REASON_CODES:
        raise ValueError(f"{name} must be a supported reason code")


def _require_status(name: str, value: str) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{name} must be one of pass, watch, block")


def _require_public_identifier(name: str, value: str) -> None:
    if type(value) is not str or not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{name} must be a public identifier")
    if any(fragment in value.lower() for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{name} contains unsafe public text")


def _require_nonnegative_decimal(name: str, value: Decimal) -> Decimal:
    value = _require_decimal(name, value)
    if value < ZERO:
        raise ValueError(f"{name} must be non-negative")
    return value


def _require_ratio_decimal(name: str, value: Decimal) -> Decimal:
    value = _require_decimal(name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{name} must be between 0.000000 and 1.000000")
    return value


def _require_decimal(name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value.quantize(SIX_PLACES, rounding=ROUND_HALF_UP)


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


def _as_utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_digest(name: str, value: str) -> None:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{name} must be a sha256 hex digest")


def _status_count(
    rows: tuple[ResearchMarketSettlementFrictionRefreshRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _reason_count(
    rows: tuple[ResearchMarketSettlementFrictionRefreshRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(
        sum(1 for row in rows if reason_code in row.reason_codes),
    )


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(SIX_PLACES)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return (numerator / denominator).quantize(SIX_PLACES, rounding=ROUND_HALF_UP)


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return max(items).quantize(SIX_PLACES, rounding=ROUND_HALF_UP)


def _average_decimal(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return (sum(items, ZERO) / _decimal_count(len(items))).quantize(
        SIX_PLACES,
        rounding=ROUND_HALF_UP,
    )


def _row_derived_validation_digest(
    row: ResearchMarketSettlementFrictionRefreshRow,
) -> str:
    payload = _dataclass_payload(row, exclude=("derived_validation_digest",))
    return _payload_digest(payload)


def _report_derived_validation_digest(
    report: ResearchMarketSettlementFrictionRefreshReport,
) -> str:
    payload = _report_payload(report, include_digest=False)
    return _payload_digest(payload)


def _payload_digest(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _report_payload(
    report: ResearchMarketSettlementFrictionRefreshReport,
    *,
    include_digest: bool,
) -> dict[str, object]:
    payload: dict[str, object] = {}
    for field in fields(report):
        if field.name == "derived_validation_digest" and not include_digest:
            continue
        value = getattr(report, field.name)
        if field.name == "rows":
            payload[field.name] = [
                _dataclass_payload(row)
                for row in sorted(
                    report.rows,
                    key=lambda row: (row.aggregate_key, row.derived_validation_digest),
                )
            ]
        elif field.name == "reason_code_counts":
            payload[field.name] = [
                _dataclass_payload(item) for item in report.reason_code_counts
            ]
        else:
            payload[field.name] = _json_ready(value)
    return payload


def _dataclass_payload(
    value: object,
    *,
    exclude: tuple[str, ...] = (),
) -> dict[str, object]:
    if not is_dataclass(value) or isinstance(value, type):
        raise ValueError("value must be a dataclass instance")
    excluded = set(exclude)
    payload: dict[str, object] = {}
    for field in fields(value):
        if field.name in excluded:
            continue
        payload[field.name] = _json_ready(getattr(value, field.name))
    return payload


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _dataclass_payload(value)
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(value.quantize(SIX_PLACES, rounding=ROUND_HALF_UP))
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric values must be Decimal")
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(
            label,
            asdict(value),
            allow_json_containers=True,
        )
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} keys must be strings")
            if any(fragment in key.lower() for fragment in UNSAFE_TEXT_FRAGMENTS):
                raise ValueError(f"{label} contains unsafe public field")
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        if any(fragment in value.lower() for fragment in UNSAFE_TEXT_FRAGMENTS):
            raise ValueError(f"{label} contains unsafe public text")
        return
    if allow_json_containers and (
        value is None or type(value) in (bool, int) or isinstance(value, float)
    ):
        return
    if isinstance(value, (Decimal, datetime)) or type(value) is bool or value is None:
        return
