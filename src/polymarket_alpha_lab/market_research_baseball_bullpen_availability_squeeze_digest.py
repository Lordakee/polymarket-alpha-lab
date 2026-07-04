"""Pure Phase 1 baseball bullpen availability squeeze digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import re
from typing import Any


DEFAULT_MARKET_RESEARCH_BASEBALL_BULLPEN_AVAILABILITY_SQUEEZE_DIGEST_CONFIG_VERSION = (
    "market-research-baseball-bullpen-availability-squeeze-digest-v0"
)

STATUSES = ("pass", "watch", "blocked")
ROW_REASON_CODES = (
    "baseball_bullpen_squeeze_back_to_back_usage",
    "baseball_bullpen_squeeze_clear",
    "baseball_bullpen_squeeze_high_reliever_workload",
    "baseball_bullpen_squeeze_leverage_arms_thin",
    "baseball_bullpen_squeeze_leverage_arms_unavailable",
    "baseball_bullpen_squeeze_short_starter_expectation",
    "baseball_bullpen_squeeze_source_disagreement",
    "baseball_bullpen_squeeze_stale_source",
    "baseball_bullpen_squeeze_travel_rest_pressure",
    "baseball_bullpen_squeeze_watch_reliever_workload",
)
REPORT_REASON_CODES = (
    "baseball_bullpen_squeeze_blocked_market_present",
    "baseball_bullpen_squeeze_watch_market_present",
    "baseball_bullpen_squeeze_workload_pressure_present",
    "baseball_bullpen_squeeze_leverage_availability_pressure_present",
    "baseball_bullpen_squeeze_starter_length_pressure_present",
    "baseball_bullpen_squeeze_travel_rest_pressure_present",
    "baseball_bullpen_squeeze_source_quality_pressure_present",
    "baseball_bullpen_squeeze_digest_clear",
    "baseball_bullpen_squeeze_digest_empty",
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
WATCH_RISK_SCORE = Decimal("0.500000")
STACKED_WATCH_RISK_SCORE = Decimal("0.750000")
SECONDS_PER_MINUTE = Decimal("60.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_RANK = {
    "blocked": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}
_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


__all__ = (
    "DEFAULT_MARKET_RESEARCH_BASEBALL_BULLPEN_AVAILABILITY_SQUEEZE_DIGEST_CONFIG_VERSION",
    "MarketResearchBaseballBullpenAvailabilitySqueezeDigestConfig",
    "MarketResearchBaseballBullpenAvailabilitySqueezeDigestReport",
    "MarketResearchBaseballBullpenAvailabilitySqueezeDigestRow",
    "MarketResearchBaseballBullpenAvailabilitySqueezeInputRow",
    "MarketResearchBaseballBullpenAvailabilitySqueezeReasonCodeCount",
    "build_market_research_baseball_bullpen_availability_squeeze_digest",
    "market_research_baseball_bullpen_availability_squeeze_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchBaseballBullpenAvailabilitySqueezeDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_BASEBALL_BULLPEN_AVAILABILITY_SQUEEZE_DIGEST_CONFIG_VERSION
    )
    watch_reliever_workload_index: Decimal = Decimal("0.650000")
    blocked_reliever_workload_index: Decimal = Decimal("0.850000")
    watch_back_to_back_usage_count: Decimal = Decimal("2.000000")
    blocked_back_to_back_usage_count: Decimal = Decimal("3.000000")
    watch_available_leverage_arm_count: Decimal = Decimal("1.000000")
    blocked_available_leverage_arm_count: Decimal = Decimal("0.000000")
    watch_starter_expected_innings: Decimal = Decimal("5.000000")
    blocked_starter_expected_innings: Decimal = Decimal("3.500000")
    watch_travel_rest_pressure_index: Decimal = Decimal("0.600000")
    blocked_travel_rest_pressure_index: Decimal = Decimal("0.800000")
    watch_source_age_minutes: Decimal = Decimal("90.000000")
    blocked_source_age_minutes: Decimal = Decimal("180.000000")
    watch_source_disagreement_index: Decimal = Decimal("0.400000")
    blocked_source_disagreement_index: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchBaseballBullpenAvailabilitySqueezeDigestConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_BASEBALL_BULLPEN_AVAILABILITY_SQUEEZE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_reliever_workload_index",
            "blocked_reliever_workload_index",
            "watch_travel_rest_pressure_index",
            "blocked_travel_rest_pressure_index",
            "watch_source_disagreement_index",
            "blocked_source_disagreement_index",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_back_to_back_usage_count",
            "blocked_back_to_back_usage_count",
            "watch_available_leverage_arm_count",
            "blocked_available_leverage_arm_count",
            "watch_starter_expected_innings",
            "blocked_starter_expected_innings",
            "watch_source_age_minutes",
            "blocked_source_age_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchBaseballBullpenAvailabilitySqueezeInputRow:
    source_id: str
    team_id: str
    opponent_id: str
    market_slug: str
    reliever_workload_index: Decimal
    back_to_back_usage_count: Decimal
    leverage_arm_available_count: Decimal
    starter_expected_innings: Decimal
    travel_rest_pressure_index: Decimal
    source_disagreement_index: Decimal
    source_updated_at: datetime
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchBaseballBullpenAvailabilitySqueezeInputRow,
            "input row",
        )
        for field_name in ("source_id", "team_id", "opponent_id", "market_slug"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "reliever_workload_index",
            "travel_rest_pressure_index",
            "source_disagreement_index",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "back_to_back_usage_count",
            "leverage_arm_available_count",
            "starter_expected_innings",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_updated_at",
            _as_utc("source_updated_at", self.source_updated_at),
        )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_open_reason_codes(
                "upstream_reason_codes",
                self.upstream_reason_codes,
            ),
        )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchBaseballBullpenAvailabilitySqueezeDigestRow:
    source_id: str
    team_id: str
    opponent_id: str
    market_slug: str
    row_status: str
    generated_at: datetime
    source_updated_at: datetime
    source_age_minutes: Decimal
    reliever_workload_index: Decimal
    back_to_back_usage_count: Decimal
    leverage_arm_available_count: Decimal
    starter_expected_innings: Decimal
    travel_rest_pressure_index: Decimal
    source_disagreement_index: Decimal
    squeeze_risk_score: Decimal
    upstream_reason_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchBaseballBullpenAvailabilitySqueezeDigestRow,
            "row",
        )
        for field_name in ("source_id", "team_id", "opponent_id", "market_slug"):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member("row_status", self.row_status, STATUSES)
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        object.__setattr__(
            self,
            "source_updated_at",
            _as_utc("source_updated_at", self.source_updated_at),
        )
        object.__setattr__(
            self,
            "source_age_minutes",
            _require_nonnegative_decimal("source_age_minutes", self.source_age_minutes),
        )
        for field_name in (
            "reliever_workload_index",
            "travel_rest_pressure_index",
            "source_disagreement_index",
            "squeeze_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "back_to_back_usage_count",
            "leverage_arm_available_count",
            "starter_expected_innings",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
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
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchBaseballBullpenAvailabilitySqueezeReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchBaseballBullpenAvailabilitySqueezeReasonCodeCount,
            "reason code count",
        )
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODES)
        object.__setattr__(self, "count", _require_nonnegative_decimal("count", self.count))
        object.__setattr__(self, "row_ratio", _require_ratio("row_ratio", self.row_ratio))
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchBaseballBullpenAvailabilitySqueezeDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    workload_pressure_count: Decimal
    leverage_availability_pressure_count: Decimal
    starter_length_pressure_count: Decimal
    travel_rest_pressure_count: Decimal
    source_quality_pressure_count: Decimal
    max_reliever_workload_index: Decimal
    max_back_to_back_usage_count: Decimal
    min_leverage_arm_available_count: Decimal
    min_starter_expected_innings: Decimal
    max_source_age_minutes: Decimal
    risk_score: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[MarketResearchBaseballBullpenAvailabilitySqueezeDigestRow, ...]
    reason_code_counts: tuple[
        MarketResearchBaseballBullpenAvailabilitySqueezeReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchBaseballBullpenAvailabilitySqueezeDigestReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_BASEBALL_BULLPEN_AVAILABILITY_SQUEEZE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "workload_pressure_count",
            "leverage_availability_pressure_count",
            "starter_length_pressure_count",
            "travel_rest_pressure_count",
            "source_quality_pressure_count",
            "max_reliever_workload_index",
            "max_back_to_back_usage_count",
            "min_leverage_arm_available_count",
            "min_starter_expected_innings",
            "max_source_age_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "risk_score", _require_ratio("risk_score", self.risk_score))
        _require_member("digest_status", self.digest_status, STATUSES)
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
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_baseball_bullpen_availability_squeeze_digest(
    input_rows: Iterable[MarketResearchBaseballBullpenAvailabilitySqueezeInputRow],
    *,
    config: MarketResearchBaseballBullpenAvailabilitySqueezeDigestConfig,
    generated_at: datetime,
) -> MarketResearchBaseballBullpenAvailabilitySqueezeDigestReport:
    if type(config) is not MarketResearchBaseballBullpenAvailabilitySqueezeDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchBaseballBullpenAvailabilitySqueezeDigestConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    _require_hard_flags("config", config)
    normalized = _normalize_input_rows(input_rows, generated_at=generated_at_utc)
    rows = tuple(
        sorted(
            (
                _row_from_input_row(row, config=config, generated_at=generated_at_utc)
                for row in normalized
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    digest_status = _digest_status(rows)
    row_count = _count_decimal(len(rows))
    return MarketResearchBaseballBullpenAvailabilitySqueezeDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=row_count,
        blocked_count=_status_count(rows, "blocked"),
        watch_count=_status_count(rows, "watch"),
        pass_count=_status_count(rows, "pass"),
        workload_pressure_count=_pressure_count(rows, _has_workload_pressure),
        leverage_availability_pressure_count=_pressure_count(
            rows,
            _has_leverage_availability_pressure,
        ),
        starter_length_pressure_count=_pressure_count(rows, _has_starter_length_pressure),
        travel_rest_pressure_count=_pressure_count(rows, _has_travel_rest_pressure),
        source_quality_pressure_count=_pressure_count(rows, _has_source_quality_pressure),
        max_reliever_workload_index=_max_row_decimal(rows, "reliever_workload_index"),
        max_back_to_back_usage_count=_max_row_decimal(rows, "back_to_back_usage_count"),
        min_leverage_arm_available_count=_min_row_decimal(
            rows,
            "leverage_arm_available_count",
        ),
        min_starter_expected_innings=_min_row_decimal(rows, "starter_expected_innings"),
        max_source_age_minutes=_max_row_decimal(rows, "source_age_minutes"),
        risk_score=_max_row_decimal(rows, "squeeze_risk_score"),
        digest_status=digest_status,
        recommended_next_step=_recommended_next_step(digest_status),
        rows=rows,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        reason_codes=reason_codes,
    )


def market_research_baseball_bullpen_availability_squeeze_digest_payload(
    report: MarketResearchBaseballBullpenAvailabilitySqueezeDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchBaseballBullpenAvailabilitySqueezeDigestReport:
        raise ValueError(
            "report must be exactly "
            "MarketResearchBaseballBullpenAvailabilitySqueezeDigestReport",
        )
    return _payload_value(report)


def _row_from_input_row(
    row: MarketResearchBaseballBullpenAvailabilitySqueezeInputRow,
    *,
    config: MarketResearchBaseballBullpenAvailabilitySqueezeDigestConfig,
    generated_at: datetime,
) -> MarketResearchBaseballBullpenAvailabilitySqueezeDigestRow:
    source_age_minutes = _age_minutes(generated_at, row.source_updated_at)
    reason_codes = _row_reason_codes(row, config=config, source_age_minutes=source_age_minutes)
    row_status = _row_status(row, config=config, source_age_minutes=source_age_minutes)
    return MarketResearchBaseballBullpenAvailabilitySqueezeDigestRow(
        source_id=row.source_id,
        team_id=row.team_id,
        opponent_id=row.opponent_id,
        market_slug=row.market_slug,
        row_status=row_status,
        generated_at=generated_at,
        source_updated_at=row.source_updated_at,
        source_age_minutes=source_age_minutes,
        reliever_workload_index=row.reliever_workload_index,
        back_to_back_usage_count=row.back_to_back_usage_count,
        leverage_arm_available_count=row.leverage_arm_available_count,
        starter_expected_innings=row.starter_expected_innings,
        travel_rest_pressure_index=row.travel_rest_pressure_index,
        source_disagreement_index=row.source_disagreement_index,
        squeeze_risk_score=_squeeze_risk_score(row_status, reason_codes),
        upstream_reason_codes=row.upstream_reason_codes,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    row: MarketResearchBaseballBullpenAvailabilitySqueezeInputRow,
    *,
    config: MarketResearchBaseballBullpenAvailabilitySqueezeDigestConfig,
    source_age_minutes: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if row.back_to_back_usage_count >= config.watch_back_to_back_usage_count:
        reason_codes.append("baseball_bullpen_squeeze_back_to_back_usage")
    if row.reliever_workload_index >= config.blocked_reliever_workload_index:
        reason_codes.append("baseball_bullpen_squeeze_high_reliever_workload")
    elif row.reliever_workload_index >= config.watch_reliever_workload_index:
        reason_codes.append("baseball_bullpen_squeeze_watch_reliever_workload")
    if row.leverage_arm_available_count <= config.blocked_available_leverage_arm_count:
        reason_codes.append("baseball_bullpen_squeeze_leverage_arms_unavailable")
    elif row.leverage_arm_available_count <= config.watch_available_leverage_arm_count:
        reason_codes.append("baseball_bullpen_squeeze_leverage_arms_thin")
    if row.starter_expected_innings <= config.watch_starter_expected_innings:
        reason_codes.append("baseball_bullpen_squeeze_short_starter_expectation")
    if row.source_disagreement_index >= config.watch_source_disagreement_index:
        reason_codes.append("baseball_bullpen_squeeze_source_disagreement")
    if source_age_minutes > config.watch_source_age_minutes:
        reason_codes.append("baseball_bullpen_squeeze_stale_source")
    if row.travel_rest_pressure_index >= config.watch_travel_rest_pressure_index:
        reason_codes.append("baseball_bullpen_squeeze_travel_rest_pressure")
    if not reason_codes:
        reason_codes.append("baseball_bullpen_squeeze_clear")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), ROW_REASON_CODES)


def _row_status(
    row: MarketResearchBaseballBullpenAvailabilitySqueezeInputRow,
    *,
    config: MarketResearchBaseballBullpenAvailabilitySqueezeDigestConfig,
    source_age_minutes: Decimal,
) -> str:
    if (
        row.reliever_workload_index >= config.blocked_reliever_workload_index
        or row.back_to_back_usage_count >= config.blocked_back_to_back_usage_count
        or row.leverage_arm_available_count <= config.blocked_available_leverage_arm_count
        or row.starter_expected_innings <= config.blocked_starter_expected_innings
        or row.travel_rest_pressure_index >= config.blocked_travel_rest_pressure_index
        or source_age_minutes > config.blocked_source_age_minutes
        or row.source_disagreement_index >= config.blocked_source_disagreement_index
    ):
        return "blocked"
    if _row_reason_codes(row, config=config, source_age_minutes=source_age_minutes) != (
        "baseball_bullpen_squeeze_clear",
    ):
        return "watch"
    return "pass"


def _squeeze_risk_score(row_status: str, reason_codes: tuple[str, ...]) -> Decimal:
    if row_status == "blocked":
        return ONE
    if row_status == "pass":
        return ZERO
    if _count_risk_reasons(reason_codes) >= Decimal("3.000000"):
        return STACKED_WATCH_RISK_SCORE
    return WATCH_RISK_SCORE


def _count_risk_reasons(reason_codes: tuple[str, ...]) -> Decimal:
    return _count_decimal(
        sum(1 for reason_code in reason_codes if reason_code != "baseball_bullpen_squeeze_clear"),
    )


def _report_reason_codes(
    rows: tuple[MarketResearchBaseballBullpenAvailabilitySqueezeDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("baseball_bullpen_squeeze_digest_empty",)
    reason_codes: list[str] = []
    if _status_count(rows, "blocked") > ZERO:
        reason_codes.append("baseball_bullpen_squeeze_blocked_market_present")
    if _status_count(rows, "watch") > ZERO:
        reason_codes.append("baseball_bullpen_squeeze_watch_market_present")
    if _pressure_count(rows, _has_workload_pressure) > ZERO:
        reason_codes.append("baseball_bullpen_squeeze_workload_pressure_present")
    if _pressure_count(rows, _has_leverage_availability_pressure) > ZERO:
        reason_codes.append("baseball_bullpen_squeeze_leverage_availability_pressure_present")
    if _pressure_count(rows, _has_starter_length_pressure) > ZERO:
        reason_codes.append("baseball_bullpen_squeeze_starter_length_pressure_present")
    if _pressure_count(rows, _has_travel_rest_pressure) > ZERO:
        reason_codes.append("baseball_bullpen_squeeze_travel_rest_pressure_present")
    if _pressure_count(rows, _has_source_quality_pressure) > ZERO:
        reason_codes.append("baseball_bullpen_squeeze_source_quality_pressure_present")
    if not reason_codes:
        reason_codes.append("baseball_bullpen_squeeze_digest_clear")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), REPORT_REASON_CODES)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[MarketResearchBaseballBullpenAvailabilitySqueezeDigestRow, ...],
) -> tuple[MarketResearchBaseballBullpenAvailabilitySqueezeReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if reason_codes == ("baseball_bullpen_squeeze_digest_empty",):
        return (
            MarketResearchBaseballBullpenAvailabilitySqueezeReasonCodeCount(
                reason_code="baseball_bullpen_squeeze_digest_empty",
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        MarketResearchBaseballBullpenAvailabilitySqueezeReasonCodeCount(
            reason_code=reason_code,
            count=_report_reason_row_count(reason_code, rows),
            row_ratio=_ratio(_report_reason_row_count(reason_code, rows), row_count),
        )
        for reason_code in reason_codes
    )


def _report_reason_row_count(
    reason_code: str,
    rows: tuple[MarketResearchBaseballBullpenAvailabilitySqueezeDigestRow, ...],
) -> Decimal:
    if reason_code == "baseball_bullpen_squeeze_blocked_market_present":
        return _status_count(rows, "blocked")
    if reason_code == "baseball_bullpen_squeeze_watch_market_present":
        return _status_count(rows, "watch")
    if reason_code == "baseball_bullpen_squeeze_workload_pressure_present":
        return _pressure_count(rows, _has_workload_pressure)
    if reason_code == "baseball_bullpen_squeeze_leverage_availability_pressure_present":
        return _pressure_count(rows, _has_leverage_availability_pressure)
    if reason_code == "baseball_bullpen_squeeze_starter_length_pressure_present":
        return _pressure_count(rows, _has_starter_length_pressure)
    if reason_code == "baseball_bullpen_squeeze_travel_rest_pressure_present":
        return _pressure_count(rows, _has_travel_rest_pressure)
    if reason_code == "baseball_bullpen_squeeze_source_quality_pressure_present":
        return _pressure_count(rows, _has_source_quality_pressure)
    if reason_code == "baseball_bullpen_squeeze_digest_clear":
        return _status_count(rows, "pass")
    raise ValueError("reason_code must be supported")


def _digest_status(
    rows: tuple[MarketResearchBaseballBullpenAvailabilitySqueezeDigestRow, ...],
) -> str:
    if not rows:
        return "blocked"
    if _status_count(rows, "blocked") > ZERO:
        return "blocked"
    if _status_count(rows, "watch") > ZERO:
        return "watch"
    return "pass"


def _recommended_next_step(status: str) -> str:
    if status == "pass":
        return "allow_report_only_baseball_bullpen_squeeze_screening"
    if status == "watch":
        return "monitor_report_only_baseball_bullpen_squeeze_screening"
    return "block_report_only_baseball_bullpen_squeeze_screening"


def _has_workload_pressure(
    row: MarketResearchBaseballBullpenAvailabilitySqueezeDigestRow,
) -> bool:
    return any(
        reason_code in row.reason_codes
        for reason_code in (
            "baseball_bullpen_squeeze_back_to_back_usage",
            "baseball_bullpen_squeeze_high_reliever_workload",
            "baseball_bullpen_squeeze_watch_reliever_workload",
        )
    )


def _has_leverage_availability_pressure(
    row: MarketResearchBaseballBullpenAvailabilitySqueezeDigestRow,
) -> bool:
    return any(
        reason_code in row.reason_codes
        for reason_code in (
            "baseball_bullpen_squeeze_leverage_arms_thin",
            "baseball_bullpen_squeeze_leverage_arms_unavailable",
        )
    )


def _has_starter_length_pressure(
    row: MarketResearchBaseballBullpenAvailabilitySqueezeDigestRow,
) -> bool:
    return "baseball_bullpen_squeeze_short_starter_expectation" in row.reason_codes


def _has_travel_rest_pressure(
    row: MarketResearchBaseballBullpenAvailabilitySqueezeDigestRow,
) -> bool:
    return "baseball_bullpen_squeeze_travel_rest_pressure" in row.reason_codes


def _has_source_quality_pressure(
    row: MarketResearchBaseballBullpenAvailabilitySqueezeDigestRow,
) -> bool:
    return any(
        reason_code in row.reason_codes
        for reason_code in (
            "baseball_bullpen_squeeze_source_disagreement",
            "baseball_bullpen_squeeze_stale_source",
        )
    )


def _pressure_count(
    rows: tuple[MarketResearchBaseballBullpenAvailabilitySqueezeDigestRow, ...],
    predicate: Any,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if predicate(row)))


def _validate_config(
    config: MarketResearchBaseballBullpenAvailabilitySqueezeDigestConfig,
) -> None:
    if config.watch_reliever_workload_index > config.blocked_reliever_workload_index:
        raise ValueError(
            "watch_reliever_workload_index must not exceed "
            "blocked_reliever_workload_index",
        )
    if config.watch_back_to_back_usage_count > config.blocked_back_to_back_usage_count:
        raise ValueError(
            "watch_back_to_back_usage_count must not exceed "
            "blocked_back_to_back_usage_count",
        )
    if (
        config.blocked_available_leverage_arm_count
        > config.watch_available_leverage_arm_count
    ):
        raise ValueError(
            "blocked_available_leverage_arm_count must not exceed "
            "watch_available_leverage_arm_count",
        )
    if config.blocked_starter_expected_innings > config.watch_starter_expected_innings:
        raise ValueError(
            "blocked_starter_expected_innings must not exceed "
            "watch_starter_expected_innings",
        )
    if config.watch_travel_rest_pressure_index > config.blocked_travel_rest_pressure_index:
        raise ValueError(
            "watch_travel_rest_pressure_index must not exceed "
            "blocked_travel_rest_pressure_index",
        )
    if config.watch_source_age_minutes > config.blocked_source_age_minutes:
        raise ValueError(
            "watch_source_age_minutes must not exceed blocked_source_age_minutes",
        )
    if config.watch_source_disagreement_index > config.blocked_source_disagreement_index:
        raise ValueError(
            "watch_source_disagreement_index must not exceed "
            "blocked_source_disagreement_index",
        )


def _validate_row(
    row: MarketResearchBaseballBullpenAvailabilitySqueezeDigestRow,
) -> None:
    if row.source_updated_at > row.generated_at:
        raise ValueError("source_updated_at must not exceed generated_at")
    if row.source_age_minutes != _age_minutes(row.generated_at, row.source_updated_at):
        raise ValueError("source_age_minutes must match source_updated_at")
    if row.row_status == "pass":
        if row.reason_codes != ("baseball_bullpen_squeeze_clear",):
            raise ValueError("reason_codes must match row_status")
        if row.squeeze_risk_score != ZERO:
            raise ValueError("squeeze_risk_score must match row_status")
        return
    if "baseball_bullpen_squeeze_clear" in row.reason_codes:
        raise ValueError("reason_codes must match row_status")
    if row.row_status == "blocked" and row.squeeze_risk_score != ONE:
        raise ValueError("squeeze_risk_score must match row_status")
    if row.row_status == "watch" and row.squeeze_risk_score != _squeeze_risk_score(
        row.row_status,
        row.reason_codes,
    ):
        raise ValueError("squeeze_risk_score must match row_status")


def _validate_report(
    report: MarketResearchBaseballBullpenAvailabilitySqueezeDigestReport,
) -> None:
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.blocked_count + report.watch_count + report.pass_count != report.row_count:
        raise ValueError("status counts must match rows")
    if report.workload_pressure_count != _pressure_count(report.rows, _has_workload_pressure):
        raise ValueError("workload_pressure_count must match rows")
    if report.leverage_availability_pressure_count != _pressure_count(
        report.rows,
        _has_leverage_availability_pressure,
    ):
        raise ValueError("leverage_availability_pressure_count must match rows")
    if report.starter_length_pressure_count != _pressure_count(
        report.rows,
        _has_starter_length_pressure,
    ):
        raise ValueError("starter_length_pressure_count must match rows")
    if report.travel_rest_pressure_count != _pressure_count(
        report.rows,
        _has_travel_rest_pressure,
    ):
        raise ValueError("travel_rest_pressure_count must match rows")
    if report.source_quality_pressure_count != _pressure_count(
        report.rows,
        _has_source_quality_pressure,
    ):
        raise ValueError("source_quality_pressure_count must match rows")
    if report.max_reliever_workload_index != _max_row_decimal(
        report.rows,
        "reliever_workload_index",
    ):
        raise ValueError("max_reliever_workload_index must match rows")
    if report.max_back_to_back_usage_count != _max_row_decimal(
        report.rows,
        "back_to_back_usage_count",
    ):
        raise ValueError("max_back_to_back_usage_count must match rows")
    if report.min_leverage_arm_available_count != _min_row_decimal(
        report.rows,
        "leverage_arm_available_count",
    ):
        raise ValueError("min_leverage_arm_available_count must match rows")
    if report.min_starter_expected_innings != _min_row_decimal(
        report.rows,
        "starter_expected_innings",
    ):
        raise ValueError("min_starter_expected_innings must match rows")
    if report.max_source_age_minutes != _max_row_decimal(report.rows, "source_age_minutes"):
        raise ValueError("max_source_age_minutes must match rows")
    if report.risk_score != _max_row_decimal(report.rows, "squeeze_risk_score"):
        raise ValueError("risk_score must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, report.rows):
        raise ValueError("reason_code_counts must match reason_codes")


def _normalize_input_rows(
    input_rows: Iterable[MarketResearchBaseballBullpenAvailabilitySqueezeInputRow],
    *,
    generated_at: datetime,
) -> tuple[MarketResearchBaseballBullpenAvailabilitySqueezeInputRow, ...]:
    if isinstance(input_rows, (str, bytes)) or not isinstance(input_rows, Iterable):
        raise ValueError(
            "input rows must contain "
            "MarketResearchBaseballBullpenAvailabilitySqueezeInputRow",
        )
    rows = tuple(input_rows)
    seen_source_ids: set[str] = set()
    for row in rows:
        if type(row) is not MarketResearchBaseballBullpenAvailabilitySqueezeInputRow:
            raise ValueError(
                "input rows must contain "
                "MarketResearchBaseballBullpenAvailabilitySqueezeInputRow",
            )
        _require_hard_flags("input row", row)
        if row.source_updated_at > generated_at:
            raise ValueError("source_updated_at must not exceed generated_at")
        if row.source_id in seen_source_ids:
            raise ValueError("input rows must not contain duplicate source_id values")
        seen_source_ids.add(row.source_id)
    return rows


def _normalize_rows(
    rows: Iterable[MarketResearchBaseballBullpenAvailabilitySqueezeDigestRow],
) -> tuple[MarketResearchBaseballBullpenAvailabilitySqueezeDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError(
            "rows must contain MarketResearchBaseballBullpenAvailabilitySqueezeDigestRow",
        )
    normalized = tuple(rows)
    seen_source_ids: set[str] = set()
    for row in normalized:
        if type(row) is not MarketResearchBaseballBullpenAvailabilitySqueezeDigestRow:
            raise ValueError(
                "rows must contain "
                "MarketResearchBaseballBullpenAvailabilitySqueezeDigestRow",
            )
        _require_hard_flags("row", row)
        if row.source_id in seen_source_ids:
            raise ValueError("rows must not contain duplicate source_id values")
        seen_source_ids.add(row.source_id)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    values: Iterable[MarketResearchBaseballBullpenAvailabilitySqueezeReasonCodeCount],
) -> tuple[MarketResearchBaseballBullpenAvailabilitySqueezeReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError("reason_code_counts must contain reason code counts")
    normalized = tuple(values)
    for value in normalized:
        if (
            type(value)
            is not MarketResearchBaseballBullpenAvailabilitySqueezeReasonCodeCount
        ):
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchBaseballBullpenAvailabilitySqueezeReasonCodeCount",
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
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    for value in normalized:
        _require_member("reason_code", value, allowed)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    return tuple(sorted(normalized, key=lambda value: allowed.index(value)))


def _row_sort_key(
    row: MarketResearchBaseballBullpenAvailabilitySqueezeDigestRow,
) -> tuple[Decimal, Decimal, str, str, str, str]:
    return (
        STATUS_RANK[row.row_status],
        -row.squeeze_risk_score,
        row.market_slug,
        row.team_id,
        row.opponent_id,
        row.source_id,
    )


def _status_count(
    rows: tuple[MarketResearchBaseballBullpenAvailabilitySqueezeDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.row_status == status))


def _max_row_decimal(
    rows: tuple[MarketResearchBaseballBullpenAvailabilitySqueezeDigestRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _min_row_decimal(
    rows: tuple[MarketResearchBaseballBullpenAvailabilitySqueezeDigestRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return min(getattr(row, field_name) for row in rows)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(numerator / denominator)


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _age_minutes(generated_at: datetime, source_updated_at: datetime) -> Decimal:
    delta = generated_at - source_updated_at
    whole_seconds = Decimal(delta.days * 86400 + delta.seconds)
    with localcontext(DECIMAL_CONTEXT):
        fractional_seconds = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
        return _require_nonnegative_decimal(
            "source_age_minutes",
            (whole_seconds + fractional_seconds) / SECONDS_PER_MINUTE,
        )


def _require_ratio(field_name: str, value: object) -> Decimal:
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
