"""Readonly Decimal risk report for resolution source latency."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json


DEFAULT_RESEARCH_PACKET_RESOLUTION_SOURCE_LATENCY_RISK_SCORE_V2_CONFIG_VERSION = (
    "research-packet-resolution-source-latency-risk-score-v2"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_MINUTE = Decimal("60")
MICROSECONDS_PER_SECOND = 1_000_000
SECONDS_PER_DAY = 86_400

SOURCE_KINDS = ("official", "secondary", "reference")
RISK_STATUSES = ("pass", "watch", "blocked")
ROW_REASON_CODES = (
    "resolution_source_latency_risk_pass",
    "resolution_source_latency_risk_watch",
    "resolution_source_latency_risk_blocked",
    "official_source_fresh",
    "official_source_stale_penalty",
    "non_official_source_latency_only",
    "fast_refresh_boost_applied",
    "fast_refresh_boost_unavailable",
)
REPORT_REASON_CODES = (
    "resolution_source_latency_risk_report_passed",
    "resolution_source_latency_risk_report_watch_rows",
    "resolution_source_latency_risk_report_blocked_rows",
    "resolution_source_latency_risk_report_empty",
    "official_source_stale_penalty_rows",
    "fast_refresh_boost_rows",
)
UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)

__all__ = (
    "DEFAULT_RESEARCH_PACKET_RESOLUTION_SOURCE_LATENCY_RISK_SCORE_V2_CONFIG_VERSION",
    "ResearchPacketResolutionSourceLatencyRiskScoreV2Config",
    "ResearchPacketResolutionSourceLatencyObservationV2",
    "ResearchPacketResolutionSourceLatencyRiskScoreV2Row",
    "ResearchPacketResolutionSourceLatencyRiskScoreV2Report",
    "build_research_packet_resolution_source_latency_risk_score_v2",
)


@dataclass(frozen=True)
class ResearchPacketResolutionSourceLatencyRiskScoreV2Config:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_RESOLUTION_SOURCE_LATENCY_RISK_SCORE_V2_CONFIG_VERSION
    )
    max_latency_minutes: Decimal = Decimal("240")
    official_stale_after_minutes: Decimal = Decimal("120")
    fast_refresh_window_minutes: Decimal = Decimal("15")
    official_source_stale_penalty_score: Decimal = Decimal("0.250000")
    fast_refresh_boost_score: Decimal = Decimal("0.100000")
    pass_risk_ceiling: Decimal = Decimal("0.200000")
    watch_risk_ceiling: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_non_empty_string("config_version", self.config_version),
        )
        for field_name in (
            "max_latency_minutes",
            "official_stale_after_minutes",
            "fast_refresh_window_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "official_source_stale_penalty_score",
            "fast_refresh_boost_score",
            "pass_risk_ceiling",
            "watch_risk_ceiling",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.watch_risk_ceiling < self.pass_risk_ceiling:
            raise ValueError("watch_risk_ceiling must not be below pass_risk_ceiling")
        _require_hard_flags(
            "ResearchPacketResolutionSourceLatencyRiskScoreV2Config",
            self,
        )
        _reject_unsafe_public_payload(
            "ResearchPacketResolutionSourceLatencyRiskScoreV2Config",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class ResearchPacketResolutionSourceLatencyObservationV2:
    packet_id: str
    resolution_source_name: str
    source_kind: str
    resolution_event_at: datetime
    source_last_refreshed_at: datetime
    checked_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "packet_id",
            _require_non_empty_string("packet_id", self.packet_id),
        )
        object.__setattr__(
            self,
            "resolution_source_name",
            _require_non_empty_string(
                "resolution_source_name",
                self.resolution_source_name,
            ),
        )
        object.__setattr__(
            self,
            "source_kind",
            _require_allowed_string("source_kind", self.source_kind, SOURCE_KINDS),
        )
        object.__setattr__(
            self,
            "resolution_event_at",
            _as_utc("resolution_event_at", self.resolution_event_at),
        )
        object.__setattr__(
            self,
            "source_last_refreshed_at",
            _as_utc("source_last_refreshed_at", self.source_last_refreshed_at),
        )
        object.__setattr__(
            self,
            "checked_at",
            _as_utc("checked_at", self.checked_at),
        )
        if self.checked_at < self.resolution_event_at:
            raise ValueError("checked_at must be on or after resolution_event_at")
        if self.checked_at < self.source_last_refreshed_at:
            raise ValueError("checked_at must be on or after source_last_refreshed_at")
        _require_hard_flags(
            "ResearchPacketResolutionSourceLatencyObservationV2",
            self,
        )
        _reject_unsafe_public_payload(
            "ResearchPacketResolutionSourceLatencyObservationV2",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class ResearchPacketResolutionSourceLatencyRiskScoreV2Row:
    rank: Decimal
    packet_id: str
    resolution_source_name: str
    source_kind: str
    resolution_event_at: datetime
    source_last_refreshed_at: datetime
    checked_at: datetime
    source_latency_minutes: Decimal
    source_refresh_age_minutes: Decimal
    base_latency_risk_score: Decimal
    official_source_stale_penalty_score: Decimal
    fast_refresh_boost_score: Decimal
    resolution_source_latency_risk_score: Decimal
    risk_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "rank",
            _normalize_positive_integral_decimal("rank", self.rank),
        )
        for field_name in ("packet_id", "resolution_source_name"):
            object.__setattr__(
                self,
                field_name,
                _require_non_empty_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_kind",
            _require_allowed_string("source_kind", self.source_kind, SOURCE_KINDS),
        )
        for field_name in (
            "resolution_event_at",
            "source_last_refreshed_at",
            "checked_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_utc(field_name, getattr(self, field_name)),
            )
        for field_name in ("source_latency_minutes", "source_refresh_age_minutes"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "base_latency_risk_score",
            "official_source_stale_penalty_score",
            "fast_refresh_boost_score",
            "resolution_source_latency_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "risk_status",
            _require_allowed_string("risk_status", self.risk_status, RISK_STATUSES),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags(
            "ResearchPacketResolutionSourceLatencyRiskScoreV2Row",
            self,
        )
        _reject_unsafe_public_payload(
            "ResearchPacketResolutionSourceLatencyRiskScoreV2Row",
            _payload_value(asdict(self)),
        )
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchPacketResolutionSourceLatencyRiskScoreV2Report:
    generated_at: datetime
    config_version: str
    report_status: str
    source_count: Decimal
    official_source_count: Decimal
    stale_official_source_count: Decimal
    fast_refresh_source_count: Decimal
    average_resolution_source_latency_risk_score: Decimal
    top_resolution_source_latency_risk_score: Decimal
    bottom_resolution_source_latency_risk_score: Decimal
    rows: tuple[ResearchPacketResolutionSourceLatencyRiskScoreV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_non_empty_string("config_version", self.config_version),
        )
        object.__setattr__(
            self,
            "report_status",
            _require_allowed_string("report_status", self.report_status, RISK_STATUSES),
        )
        for field_name in (
            "source_count",
            "official_source_count",
            "stale_official_source_count",
            "fast_refresh_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "average_resolution_source_latency_risk_score",
            "top_resolution_source_latency_risk_score",
            "bottom_resolution_source_latency_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags(
            "ResearchPacketResolutionSourceLatencyRiskScoreV2Report",
            self,
        )
        _reject_unsafe_public_payload(
            "ResearchPacketResolutionSourceLatencyRiskScoreV2Report",
            _payload_value(asdict(self)),
        )
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload(
            "ResearchPacketResolutionSourceLatencyRiskScoreV2Report.payload",
            payload,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_packet_resolution_source_latency_risk_score_v2(
    observations: object,
    *,
    config: ResearchPacketResolutionSourceLatencyRiskScoreV2Config | None = None,
    generated_at: datetime,
) -> ResearchPacketResolutionSourceLatencyRiskScoreV2Report:
    if config is None:
        config = ResearchPacketResolutionSourceLatencyRiskScoreV2Config()
    if type(config) is not ResearchPacketResolutionSourceLatencyRiskScoreV2Config:
        raise ValueError(
            "config must be a ResearchPacketResolutionSourceLatencyRiskScoreV2Config",
        )
    _require_hard_flags("ResearchPacketResolutionSourceLatencyRiskScoreV2Config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    row_values = tuple(
        _row_values_for_observation(observation=item, config=config)
        for item in normalized_observations
    )
    sorted_values = tuple(
        sorted(
            row_values,
            key=lambda item: (
                -item["resolution_source_latency_risk_score"],
                item["packet_id"],
                item["resolution_source_name"],
            ),
        ),
    )
    rows = tuple(
        ResearchPacketResolutionSourceLatencyRiskScoreV2Row(
            rank=Decimal(index).quantize(COUNT_QUANT),
            **values,
        )
        for index, values in enumerate(sorted_values, start=1)
    )
    status = _report_status(rows)
    values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "report_status": status,
        "source_count": Decimal(len(rows)).quantize(COUNT_QUANT),
        "official_source_count": _official_source_count(rows),
        "stale_official_source_count": _stale_official_source_count(rows),
        "fast_refresh_source_count": _fast_refresh_source_count(rows),
        "average_resolution_source_latency_risk_score": _average_risk_score(rows),
        "top_resolution_source_latency_risk_score": _top_risk_score(rows),
        "bottom_resolution_source_latency_risk_score": _bottom_risk_score(rows),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows, status),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _derived_validation_digest(values)
    return ResearchPacketResolutionSourceLatencyRiskScoreV2Report(**values)


def _row_values_for_observation(
    *,
    observation: ResearchPacketResolutionSourceLatencyObservationV2,
    config: ResearchPacketResolutionSourceLatencyRiskScoreV2Config,
) -> dict[str, object]:
    source_latency_minutes = _minutes_between(
        observation.resolution_event_at,
        observation.checked_at,
    )
    source_refresh_age_minutes = _minutes_between(
        observation.source_last_refreshed_at,
        observation.checked_at,
    )
    base_latency_risk_score = _clamp_ratio(
        _safe_ratio(source_latency_minutes, config.max_latency_minutes),
    )
    stale_penalty = _official_stale_penalty(
        observation,
        source_refresh_age_minutes,
        config,
    )
    fast_refresh_boost = _fast_refresh_boost(source_refresh_age_minutes, config)
    risk_score = _clamp_ratio(
        base_latency_risk_score + stale_penalty - fast_refresh_boost,
    )
    risk_status = _risk_status(risk_score, config)
    return {
        "packet_id": observation.packet_id,
        "resolution_source_name": observation.resolution_source_name,
        "source_kind": observation.source_kind,
        "resolution_event_at": observation.resolution_event_at,
        "source_last_refreshed_at": observation.source_last_refreshed_at,
        "checked_at": observation.checked_at,
        "source_latency_minutes": source_latency_minutes,
        "source_refresh_age_minutes": source_refresh_age_minutes,
        "base_latency_risk_score": base_latency_risk_score,
        "official_source_stale_penalty_score": stale_penalty,
        "fast_refresh_boost_score": fast_refresh_boost,
        "resolution_source_latency_risk_score": risk_score,
        "risk_status": risk_status,
        "reason_codes": _row_reason_codes(
            observation,
            stale_penalty,
            fast_refresh_boost,
            risk_status,
        ),
    }


def _official_stale_penalty(
    observation: ResearchPacketResolutionSourceLatencyObservationV2,
    source_refresh_age_minutes: Decimal,
    config: ResearchPacketResolutionSourceLatencyRiskScoreV2Config,
) -> Decimal:
    if (
        observation.source_kind == "official"
        and source_refresh_age_minutes > config.official_stale_after_minutes
    ):
        return config.official_source_stale_penalty_score
    return ZERO


def _fast_refresh_boost(
    source_refresh_age_minutes: Decimal,
    config: ResearchPacketResolutionSourceLatencyRiskScoreV2Config,
) -> Decimal:
    if source_refresh_age_minutes <= config.fast_refresh_window_minutes:
        return config.fast_refresh_boost_score
    return ZERO


def _risk_status(
    risk_score: Decimal,
    config: ResearchPacketResolutionSourceLatencyRiskScoreV2Config,
) -> str:
    if risk_score <= config.pass_risk_ceiling:
        return "pass"
    if risk_score <= config.watch_risk_ceiling:
        return "watch"
    return "blocked"


def _row_reason_codes(
    observation: ResearchPacketResolutionSourceLatencyObservationV2,
    stale_penalty: Decimal,
    fast_refresh_boost: Decimal,
    risk_status: str,
) -> tuple[str, ...]:
    source_reason = (
        "official_source_stale_penalty"
        if stale_penalty > ZERO
        else "official_source_fresh"
    )
    if observation.source_kind != "official":
        source_reason = "non_official_source_latency_only"
    boost_reason = (
        "fast_refresh_boost_applied"
        if fast_refresh_boost > ZERO
        else "fast_refresh_boost_unavailable"
    )
    return (f"resolution_source_latency_risk_{risk_status}", source_reason, boost_reason)


def _report_status(
    rows: tuple[ResearchPacketResolutionSourceLatencyRiskScoreV2Row, ...],
) -> str:
    if not rows:
        return "blocked"
    if any(row.risk_status == "blocked" for row in rows):
        return "blocked"
    if any(row.risk_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchPacketResolutionSourceLatencyRiskScoreV2Row, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("resolution_source_latency_risk_report_empty",)
    reason_codes = [f"resolution_source_latency_risk_report_{status}_rows"]
    if _stale_official_source_count(rows) > ZERO:
        reason_codes.append("official_source_stale_penalty_rows")
    if _fast_refresh_source_count(rows) > ZERO:
        reason_codes.append("fast_refresh_boost_rows")
    if status == "pass":
        reason_codes[0] = "resolution_source_latency_risk_report_passed"
    return tuple(reason_codes)


def _official_source_count(
    rows: tuple[ResearchPacketResolutionSourceLatencyRiskScoreV2Row, ...],
) -> Decimal:
    return Decimal(sum(1 for row in rows if row.source_kind == "official")).quantize(
        COUNT_QUANT,
    )


def _stale_official_source_count(
    rows: tuple[ResearchPacketResolutionSourceLatencyRiskScoreV2Row, ...],
) -> Decimal:
    return Decimal(
        sum(row.official_source_stale_penalty_score > ZERO for row in rows),
    ).quantize(COUNT_QUANT)


def _fast_refresh_source_count(
    rows: tuple[ResearchPacketResolutionSourceLatencyRiskScoreV2Row, ...],
) -> Decimal:
    return Decimal(sum(row.fast_refresh_boost_score > ZERO for row in rows)).quantize(
        COUNT_QUANT,
    )


def _average_risk_score(
    rows: tuple[ResearchPacketResolutionSourceLatencyRiskScoreV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            sum(row.resolution_source_latency_risk_score for row in rows)
            / Decimal(len(rows)),
        )


def _top_risk_score(
    rows: tuple[ResearchPacketResolutionSourceLatencyRiskScoreV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.resolution_source_latency_risk_score for row in rows)


def _bottom_risk_score(
    rows: tuple[ResearchPacketResolutionSourceLatencyRiskScoreV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return min(row.resolution_source_latency_risk_score for row in rows)


def _validate_row_consistency(
    row: ResearchPacketResolutionSourceLatencyRiskScoreV2Row,
) -> None:
    if row.checked_at < row.resolution_event_at:
        raise ValueError("checked_at must be on or after resolution_event_at")
    if row.checked_at < row.source_last_refreshed_at:
        raise ValueError("checked_at must be on or after source_last_refreshed_at")
    if row.source_latency_minutes != _minutes_between(
        row.resolution_event_at,
        row.checked_at,
    ):
        raise ValueError("source_latency_minutes must match timestamps")
    if row.source_refresh_age_minutes != _minutes_between(
        row.source_last_refreshed_at,
        row.checked_at,
    ):
        raise ValueError("source_refresh_age_minutes must match timestamps")
    if row.official_source_stale_penalty_score > ZERO and row.source_kind != "official":
        raise ValueError("official_source_stale_penalty_score requires official source")
    if f"resolution_source_latency_risk_{row.risk_status}" not in row.reason_codes:
        raise ValueError("reason_codes must match risk_status")


def _validate_report_consistency(
    report: ResearchPacketResolutionSourceLatencyRiskScoreV2Report,
) -> None:
    expected_rows = tuple(
        sorted(
            report.rows,
            key=lambda row: (
                -row.resolution_source_latency_risk_score,
                row.packet_id,
                row.resolution_source_name,
            ),
        ),
    )
    expected_ranks = tuple(Decimal(index).quantize(COUNT_QUANT) for index in range(1, len(report.rows) + 1))
    if report.rows != expected_rows or tuple(row.rank for row in report.rows) != expected_ranks:
        raise ValueError("rows must be sorted by risk and rank")
    if report.source_count != Decimal(len(report.rows)).quantize(COUNT_QUANT):
        raise ValueError("source counts must match rows")
    if report.official_source_count != _official_source_count(report.rows):
        raise ValueError("source counts must match rows")
    if report.stale_official_source_count != _stale_official_source_count(report.rows):
        raise ValueError("source counts must match rows")
    if report.fast_refresh_source_count != _fast_refresh_source_count(report.rows):
        raise ValueError("source counts must match rows")
    if report.average_resolution_source_latency_risk_score != _average_risk_score(report.rows):
        raise ValueError("risk score rollups must match rows")
    if report.top_resolution_source_latency_risk_score != _top_risk_score(report.rows):
        raise ValueError("risk score rollups must match rows")
    if report.bottom_resolution_source_latency_risk_score != _bottom_risk_score(report.rows):
        raise ValueError("risk score rollups must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows, report.report_status):
        raise ValueError("reason_codes must match report_status")
    expected_digest = _derived_validation_digest(_dataclass_values(report))
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")


def _normalize_observations(
    observations: object,
) -> tuple[ResearchPacketResolutionSourceLatencyObservationV2, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must be an iterable")
    normalized = tuple(observations)
    for item in normalized:
        if type(item) is not ResearchPacketResolutionSourceLatencyObservationV2:
            raise ValueError(
                "items must be ResearchPacketResolutionSourceLatencyObservationV2",
            )
        _require_hard_flags("ResearchPacketResolutionSourceLatencyObservationV2", item)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[ResearchPacketResolutionSourceLatencyRiskScoreV2Row, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchPacketResolutionSourceLatencyRiskScoreV2Row:
            raise ValueError(
                "rows must contain ResearchPacketResolutionSourceLatencyRiskScoreV2Row",
            )
        _require_hard_flags("ResearchPacketResolutionSourceLatencyRiskScoreV2Row", row)
    return normalized


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise ValueError(f"{field_name} must be an iterable")
    normalized = tuple(
        _require_allowed_string(field_name, item, allowed_values) for item in value
    )
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{field_name} must not contain duplicates")
    return normalized


def _minutes_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    total_microseconds = (
        (delta.days * SECONDS_PER_DAY + delta.seconds) * MICROSECONDS_PER_SECOND
        + delta.microseconds
    )
    with localcontext(DECIMAL_CONTEXT):
        return (
            Decimal(total_microseconds)
            / Decimal(MICROSECONDS_PER_SECOND)
            / SECONDS_PER_MINUTE
        ).quantize(SCORE_QUANT)


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return numerator / denominator


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_exact_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    return decimal_value.quantize(SCORE_QUANT)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_exact_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be > 0.000000")
    return decimal_value.quantize(SCORE_QUANT).normalize()


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_exact_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    return decimal_value.quantize(SCORE_QUANT)


def _normalize_positive_integral_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_exact_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be > 0.000000")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return decimal_value.quantize(COUNT_QUANT)


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_exact_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return decimal_value.quantize(COUNT_QUANT)


def _require_exact_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _clamp_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return min(ONE, max(ZERO, value)).quantize(SCORE_QUANT)


def _require_non_empty_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty")
    _reject_unsafe_public_text(field_name, value)
    return value


def _require_allowed_string(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> str:
    normalized = _require_non_empty_string(field_name, value)
    if normalized not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_sha256_digest(field_name: str, value: object) -> None:
    _require_non_empty_string(field_name, value)
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {field_name}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {field_name}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {field_name}")


def _payload_value(value: object) -> object:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _payload_value(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if value is None or type(value) in (str, int, bool):
        return value
    raise ValueError("payload contains unsupported value")


def _dataclass_values(value: object) -> dict[str, object]:
    return {field.name: getattr(value, field.name) for field in fields(value)}


def _derived_validation_digest(values: dict[str, object]) -> str:
    digest_payload = {
        key: _payload_value(item)
        for key, item in values.items()
        if key != "derived_validation_digest"
    }
    _reject_unsafe_public_payload("derived validation digest payload", digest_payload)
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public payload in {label}")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is float:
        raise ValueError(f"unsafe public payload in {label}")
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"unsafe public payload in {label}")
