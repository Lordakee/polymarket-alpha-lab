"""Pure read-only strategy research packet completeness gap v10 report."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_CONFIG_VERSION = "strategy-research-packet-completeness-gap-v10"
COUNT_QUANT = Decimal("1")
SCORE_QUANT = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_SCORE = Decimal("0.000000")
ONE_SCORE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

FORECAST_STATUSES = ("fresh", "stale", "missing")
GAP_STATUSES = ("complete", "watch", "blocked")
REASON_CODES = (
    "source_families_complete",
    "missing_source_families",
    "resolution_criteria_present",
    "missing_resolution_criteria",
    "forecast_fresh",
    "forecast_stale",
    "forecast_missing",
    "cost_estimate_present",
    "missing_cost_estimate",
    "risk_notes_present",
    "missing_risk_notes",
    "packet_complete",
    "packet_gap_watch",
    "packet_gap_blocked",
)


@dataclass(frozen=True)
class StrategyResearchPacketCompletenessGapV10Config:
    config_version: str
    required_source_families: tuple[str, ...]
    max_forecast_age_seconds: Decimal
    missing_source_family_weight: Decimal
    missing_resolution_criteria_weight: Decimal
    stale_forecast_weight: Decimal
    absent_cost_estimate_weight: Decimal
    missing_risk_notes_weight: Decimal
    blocked_gap_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "required_source_families",
            _normalize_string_tuple(
                "required_source_families",
                self.required_source_families,
                allow_empty=False,
            ),
        )
        object.__setattr__(
            self,
            "max_forecast_age_seconds",
            _normalize_positive_seconds(
                "max_forecast_age_seconds",
                self.max_forecast_age_seconds,
            ),
        )
        for field_name in (
            "missing_source_family_weight",
            "missing_resolution_criteria_weight",
            "stale_forecast_weight",
            "absent_cost_estimate_weight",
            "missing_risk_notes_weight",
            "blocked_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_gap_score(field_name, getattr(self, field_name)),
            )
        reject_unsafe_surface_fields(
            "strategy research packet completeness gap v10 config",
            self,
        )
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class StrategyResearchPacketCompletenessGapV10Packet:
    packet_id: str
    market_slug: str
    source_families: tuple[str, ...]
    has_resolution_criteria: bool
    forecasted_at: datetime | None
    has_cost_estimate: bool
    risk_notes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("packet_id", self.packet_id)
        _require_canonical_string("market_slug", self.market_slug)
        object.__setattr__(
            self,
            "source_families",
            _normalize_string_tuple(
                "source_families",
                self.source_families,
                allow_empty=False,
            ),
        )
        _require_bool("has_resolution_criteria", self.has_resolution_criteria)
        if self.forecasted_at is not None:
            object.__setattr__(
                self,
                "forecasted_at",
                _as_utc("forecasted_at", self.forecasted_at),
            )
        _require_bool("has_cost_estimate", self.has_cost_estimate)
        object.__setattr__(
            self,
            "risk_notes",
            _normalize_string_tuple("risk_notes", self.risk_notes, allow_empty=True),
        )
        reject_unsafe_surface_fields(
            "strategy research packet completeness gap v10 packet",
            self,
        )
        require_paper_only_flags("packet", self)


@dataclass(frozen=True)
class StrategyResearchPacketCompletenessGapV10Result:
    packet_id: str
    market_slug: str
    missing_source_families: tuple[str, ...]
    missing_source_family_count: Decimal
    forecast_age_seconds: Decimal | None
    forecast_status: str
    source_family_gap_score: Decimal
    resolution_criteria_gap_score: Decimal
    forecast_gap_score: Decimal
    cost_estimate_gap_score: Decimal
    risk_notes_gap_score: Decimal
    max_possible_gap_score: Decimal
    total_gap_score: Decimal
    completeness_score: Decimal
    gap_status: str
    reason_codes: tuple[str, ...]
    result_sha256: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("packet_id", self.packet_id)
        _require_canonical_string("market_slug", self.market_slug)
        object.__setattr__(
            self,
            "missing_source_families",
            _normalize_string_tuple(
                "missing_source_families",
                self.missing_source_families,
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "missing_source_family_count",
            _normalize_nonnegative_count(
                "missing_source_family_count",
                self.missing_source_family_count,
            ),
        )
        if self.forecast_age_seconds is not None:
            object.__setattr__(
                self,
                "forecast_age_seconds",
                _normalize_nonnegative_seconds(
                    "forecast_age_seconds",
                    self.forecast_age_seconds,
                ),
            )
        _require_member("forecast_status", self.forecast_status, FORECAST_STATUSES)
        for field_name in (
            "source_family_gap_score",
            "resolution_criteria_gap_score",
            "forecast_gap_score",
            "cost_estimate_gap_score",
            "risk_notes_gap_score",
            "max_possible_gap_score",
            "total_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_gap_score(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "completeness_score",
            _normalize_completeness_score("completeness_score", self.completeness_score),
        )
        _require_member("gap_status", self.gap_status, GAP_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_sha256("result_sha256", self.result_sha256)
        reject_unsafe_surface_fields(
            "strategy research packet completeness gap v10 result",
            self,
        )
        require_paper_only_flags("result", self)
        _validate_result(self)


@dataclass(frozen=True)
class StrategyResearchPacketCompletenessGapV10Report:
    generated_at: datetime
    config_version: str
    packet_count: Decimal
    complete_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    max_gap_score: Decimal
    average_gap_score: Decimal
    results: tuple[StrategyResearchPacketCompletenessGapV10Result, ...]
    report_sha256: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "packet_count",
            "complete_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_gap_score",
            _normalize_gap_score("max_gap_score", self.max_gap_score),
        )
        object.__setattr__(
            self,
            "average_gap_score",
            _normalize_gap_score("average_gap_score", self.average_gap_score),
        )
        object.__setattr__(self, "results", _normalize_results(self.results))
        _require_sha256("report_sha256", self.report_sha256)
        reject_unsafe_surface_fields(
            "strategy research packet completeness gap v10 report",
            self,
        )
        require_paper_only_flags("report", self)
        _validate_report(self)


def build_strategy_research_packet_completeness_gap_v10_report(
    packets: tuple[StrategyResearchPacketCompletenessGapV10Packet, ...],
    *,
    config: StrategyResearchPacketCompletenessGapV10Config,
    generated_at: datetime,
) -> StrategyResearchPacketCompletenessGapV10Report:
    if type(config) is not StrategyResearchPacketCompletenessGapV10Config:
        raise ValueError("config must be a StrategyResearchPacketCompletenessGapV10Config")
    reject_unsafe_surface_fields(
        "strategy research packet completeness gap v10 config",
        config,
    )
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    packet_tuple = tuple(packets)
    results = tuple(_score_packet(packet, config, generated_at_utc) for packet in packet_tuple)
    packet_count = Decimal(len(results))
    complete_count = Decimal(sum(1 for result in results if result.gap_status == "complete"))
    watch_count = Decimal(sum(1 for result in results if result.gap_status == "watch"))
    blocked_count = Decimal(sum(1 for result in results if result.gap_status == "blocked"))
    max_gap_score = max((result.total_gap_score for result in results), default=ZERO_SCORE)
    if results:
        with localcontext(DECIMAL_CONTEXT):
            average_gap_score = (
                sum((result.total_gap_score for result in results), ZERO_SCORE) / packet_count
            ).quantize(SCORE_QUANT)
    else:
        average_gap_score = ZERO_SCORE
    values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "packet_count": packet_count,
        "complete_count": complete_count,
        "watch_count": watch_count,
        "blocked_count": blocked_count,
        "max_gap_score": max_gap_score,
        "average_gap_score": average_gap_score,
        "results": results,
        "report_sha256": "",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["report_sha256"] = _report_sha256_from_values(values)
    return StrategyResearchPacketCompletenessGapV10Report(**values)


def validate_strategy_research_packet_completeness_gap_v10_report(
    report: StrategyResearchPacketCompletenessGapV10Report,
) -> StrategyResearchPacketCompletenessGapV10Report:
    if type(report) is not StrategyResearchPacketCompletenessGapV10Report:
        raise ValueError("report must be a StrategyResearchPacketCompletenessGapV10Report")
    _validate_report(report)
    reject_unsafe_surface_fields(
        "strategy research packet completeness gap v10 report",
        report,
    )
    require_paper_only_flags("report", report)
    return report


def strategy_research_packet_completeness_gap_v10_payload(report: object) -> dict[str, Any]:
    reject_unsafe_surface_fields(
        "strategy research packet completeness gap v10 public payload",
        report,
    )
    if type(report) is not StrategyResearchPacketCompletenessGapV10Report:
        raise ValueError("payload must be a StrategyResearchPacketCompletenessGapV10Report")
    validate_strategy_research_packet_completeness_gap_v10_report(report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    return payload


def _score_packet(
    packet: StrategyResearchPacketCompletenessGapV10Packet,
    config: StrategyResearchPacketCompletenessGapV10Config,
    generated_at: datetime,
) -> StrategyResearchPacketCompletenessGapV10Result:
    if type(packet) is not StrategyResearchPacketCompletenessGapV10Packet:
        raise ValueError("packet must be a StrategyResearchPacketCompletenessGapV10Packet")
    reject_unsafe_surface_fields(
        "strategy research packet completeness gap v10 packet",
        packet,
    )
    require_paper_only_flags("packet", packet)
    missing_source_families = tuple(
        source_family
        for source_family in config.required_source_families
        if source_family not in packet.source_families
    )
    missing_source_family_count = Decimal(len(missing_source_families))
    forecast_age_seconds = _forecast_age_seconds(packet.forecasted_at, generated_at)
    forecast_status = _forecast_status(forecast_age_seconds, config.max_forecast_age_seconds)
    source_family_gap_score = _gap_product(
        missing_source_family_count,
        config.missing_source_family_weight,
    )
    resolution_criteria_gap_score = (
        ZERO_SCORE
        if packet.has_resolution_criteria
        else config.missing_resolution_criteria_weight
    )
    forecast_gap_score = ZERO_SCORE if forecast_status == "fresh" else config.stale_forecast_weight
    cost_estimate_gap_score = (
        ZERO_SCORE if packet.has_cost_estimate else config.absent_cost_estimate_weight
    )
    risk_notes_gap_score = ZERO_SCORE if packet.risk_notes else config.missing_risk_notes_weight
    max_possible_gap_score = _gap_sum(
        _gap_product(
            Decimal(len(config.required_source_families)),
            config.missing_source_family_weight,
        ),
        config.missing_resolution_criteria_weight,
        config.stale_forecast_weight,
        config.absent_cost_estimate_weight,
        config.missing_risk_notes_weight,
    )
    total_gap_score = _gap_sum(
        source_family_gap_score,
        resolution_criteria_gap_score,
        forecast_gap_score,
        cost_estimate_gap_score,
        risk_notes_gap_score,
    )
    completeness_score = _completeness_score(total_gap_score, max_possible_gap_score)
    gap_status = _gap_status(total_gap_score, config.blocked_gap_score)
    reason_codes = _reason_codes(
        missing_source_families=missing_source_families,
        has_resolution_criteria=packet.has_resolution_criteria,
        forecast_status=forecast_status,
        has_cost_estimate=packet.has_cost_estimate,
        has_risk_notes=bool(packet.risk_notes),
        gap_status=gap_status,
    )
    values = {
        "packet_id": packet.packet_id,
        "market_slug": packet.market_slug,
        "missing_source_families": missing_source_families,
        "missing_source_family_count": missing_source_family_count,
        "forecast_age_seconds": forecast_age_seconds,
        "forecast_status": forecast_status,
        "source_family_gap_score": source_family_gap_score,
        "resolution_criteria_gap_score": resolution_criteria_gap_score,
        "forecast_gap_score": forecast_gap_score,
        "cost_estimate_gap_score": cost_estimate_gap_score,
        "risk_notes_gap_score": risk_notes_gap_score,
        "max_possible_gap_score": max_possible_gap_score,
        "total_gap_score": total_gap_score,
        "completeness_score": completeness_score,
        "gap_status": gap_status,
        "reason_codes": reason_codes,
        "result_sha256": "",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["result_sha256"] = _result_sha256_from_values(values)
    return StrategyResearchPacketCompletenessGapV10Result(**values)


def _forecast_age_seconds(forecasted_at: datetime | None, generated_at: datetime) -> Decimal | None:
    if forecasted_at is None:
        return None
    if forecasted_at > generated_at:
        raise ValueError("forecasted_at must not be after generated_at")
    delta = generated_at - forecasted_at
    whole_seconds = (delta.days * 86400) + delta.seconds
    with localcontext(DECIMAL_CONTEXT):
        age_seconds = Decimal(whole_seconds) + (Decimal(delta.microseconds) / Decimal(1000000))
    return _normalize_nonnegative_seconds("forecast_age_seconds", age_seconds)


def _forecast_status(
    forecast_age_seconds: Decimal | None,
    max_forecast_age_seconds: Decimal,
) -> str:
    if forecast_age_seconds is None:
        return "missing"
    if forecast_age_seconds > max_forecast_age_seconds:
        return "stale"
    return "fresh"


def _reason_codes(
    *,
    missing_source_families: tuple[str, ...],
    has_resolution_criteria: bool,
    forecast_status: str,
    has_cost_estimate: bool,
    has_risk_notes: bool,
    gap_status: str,
) -> tuple[str, ...]:
    codes = [
        "missing_source_families"
        if missing_source_families
        else "source_families_complete",
        "resolution_criteria_present"
        if has_resolution_criteria
        else "missing_resolution_criteria",
        f"forecast_{forecast_status}",
        "cost_estimate_present" if has_cost_estimate else "missing_cost_estimate",
        "risk_notes_present" if has_risk_notes else "missing_risk_notes",
    ]
    if gap_status == "complete":
        codes.append("packet_complete")
    elif gap_status == "blocked":
        codes.append("packet_gap_blocked")
    else:
        codes.append("packet_gap_watch")
    return _normalize_reason_codes(tuple(codes))


def _gap_status(total_gap_score: Decimal, blocked_gap_score: Decimal) -> str:
    if total_gap_score == ZERO_SCORE:
        return "complete"
    if total_gap_score >= blocked_gap_score:
        return "blocked"
    return "watch"


def _gap_product(count: Decimal, score: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (count * score).quantize(SCORE_QUANT)


def _gap_sum(*values: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return sum(values, ZERO_SCORE).quantize(SCORE_QUANT)


def _completeness_score(total_gap_score: Decimal, max_possible_gap_score: Decimal) -> Decimal:
    if max_possible_gap_score == ZERO_SCORE:
        return ONE_SCORE
    with localcontext(DECIMAL_CONTEXT):
        return (ONE_SCORE - (total_gap_score / max_possible_gap_score)).quantize(SCORE_QUANT)


def _validate_result(result: StrategyResearchPacketCompletenessGapV10Result) -> None:
    if result.missing_source_family_count != Decimal(len(result.missing_source_families)):
        raise ValueError("missing_source_family_count must match missing_source_families")
    expected_total_gap_score = _gap_sum(
        result.source_family_gap_score,
        result.resolution_criteria_gap_score,
        result.forecast_gap_score,
        result.cost_estimate_gap_score,
        result.risk_notes_gap_score,
    )
    if result.total_gap_score != expected_total_gap_score:
        raise ValueError("total_gap_score must match component gap scores")
    if result.completeness_score != _completeness_score(
        result.total_gap_score,
        result.max_possible_gap_score,
    ):
        raise ValueError("completeness_score must match total_gap_score")
    if result.result_sha256 != _result_sha256_from_values(_result_values(result)):
        raise ValueError("result_sha256 must match result contents")


def _validate_report(report: StrategyResearchPacketCompletenessGapV10Report) -> None:
    for result in report.results:
        _validate_result(result)
    if report.packet_count != Decimal(len(report.results)):
        raise ValueError("packet_count must match results")
    complete_count = Decimal(sum(1 for result in report.results if result.gap_status == "complete"))
    watch_count = Decimal(sum(1 for result in report.results if result.gap_status == "watch"))
    blocked_count = Decimal(sum(1 for result in report.results if result.gap_status == "blocked"))
    if report.complete_count != complete_count:
        raise ValueError("complete_count must match results")
    if report.watch_count != watch_count:
        raise ValueError("watch_count must match results")
    if report.blocked_count != blocked_count:
        raise ValueError("blocked_count must match results")
    expected_max_gap_score = max(
        (result.total_gap_score for result in report.results),
        default=ZERO_SCORE,
    )
    if report.max_gap_score != expected_max_gap_score:
        raise ValueError("max_gap_score must match results")
    if report.results:
        with localcontext(DECIMAL_CONTEXT):
            expected_average_gap_score = (
                sum((result.total_gap_score for result in report.results), ZERO_SCORE)
                / Decimal(len(report.results))
            ).quantize(SCORE_QUANT)
    else:
        expected_average_gap_score = ZERO_SCORE
    if report.average_gap_score != expected_average_gap_score:
        raise ValueError("average_gap_score must match results")
    if report.report_sha256 != _report_sha256_from_values(_report_values(report)):
        raise ValueError("report_sha256 must match report contents")


def _normalize_results(
    values: tuple[StrategyResearchPacketCompletenessGapV10Result, ...],
) -> tuple[StrategyResearchPacketCompletenessGapV10Result, ...]:
    if type(values) is not tuple:
        raise ValueError("results must be a tuple")
    for value in values:
        if type(value) is not StrategyResearchPacketCompletenessGapV10Result:
            raise ValueError("results must contain StrategyResearchPacketCompletenessGapV10Result")
        _validate_result(value)
    return values


def _normalize_string_tuple(
    field_name: str,
    values: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not allow_empty and not values:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    normalized: list[str] = []
    for value in values:
        _require_canonical_string(field_name, value)
        if value in seen:
            raise ValueError(f"{field_name} must contain unique strings")
        seen.add(value)
        normalized.append(value)
    return tuple(normalized)


def _normalize_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not values:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for value in values:
        _require_canonical_string("reason_codes", value)
        if value not in REASON_CODES:
            raise ValueError("reason_codes contains unsupported value")
        if value in seen:
            raise ValueError("reason_codes contains duplicate value")
        seen.add(value)
    return values


def _normalize_gap_score(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    normalized = decimal_value.quantize(SCORE_QUANT)
    if normalized != decimal_value:
        raise ValueError(f"{field_name} must use six decimal places")
    if normalized < ZERO_SCORE:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_completeness_score(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_gap_score(field_name, value)
    if normalized > ONE_SCORE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    normalized = decimal_value.quantize(COUNT_QUANT)
    if normalized != decimal_value:
        raise ValueError(f"{field_name} must be a whole Decimal count")
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_seconds(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_seconds(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_seconds(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must contain canonical strings")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime or value.tzinfo is not UTC:
        raise ValueError(f"{field_name} must be timezone-aware UTC")
    return value


def _require_sha256(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or len(value) != 64
        or value.lower() != value
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _result_values(result: StrategyResearchPacketCompletenessGapV10Result) -> dict[str, Any]:
    return {field.name: getattr(result, field.name) for field in fields(result)}


def _report_values(report: StrategyResearchPacketCompletenessGapV10Report) -> dict[str, Any]:
    return {field.name: getattr(report, field.name) for field in fields(report)}


def _result_sha256_from_values(values: dict[str, Any]) -> str:
    payload = {key: value for key, value in values.items() if key != "result_sha256"}
    return _canonical_sha256(payload)


def _report_sha256_from_values(values: dict[str, Any]) -> str:
    payload = {key: value for key, value in values.items() if key != "report_sha256"}
    return _canonical_sha256(payload)


def _canonical_sha256(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        _canonical_payload_value(payload),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _canonical_payload_value(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _canonical_payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is tuple:
        return [_canonical_payload_value(item) for item in value]
    if type(value) is list:
        return [_canonical_payload_value(item) for item in value]
    if type(value) is dict:
        return {
            key: _canonical_payload_value(item)
            for key, item in value.items()
            if _require_json_key(key)
        }
    if type(value) in (str, bool, int):
        return value
    if type(value) is float:
        raise ValueError("payload must not contain float values")
    raise ValueError("payload contains unsupported value")


def _require_json_key(value: object) -> bool:
    if type(value) is not str:
        raise ValueError("payload keys must be strings")
    return True


__all__ = (
    "DEFAULT_CONFIG_VERSION",
    "FORECAST_STATUSES",
    "GAP_STATUSES",
    "REASON_CODES",
    "StrategyResearchPacketCompletenessGapV10Config",
    "StrategyResearchPacketCompletenessGapV10Packet",
    "StrategyResearchPacketCompletenessGapV10Report",
    "StrategyResearchPacketCompletenessGapV10Result",
    "build_strategy_research_packet_completeness_gap_v10_report",
    "strategy_research_packet_completeness_gap_v10_payload",
    "validate_strategy_research_packet_completeness_gap_v10_report",
)
