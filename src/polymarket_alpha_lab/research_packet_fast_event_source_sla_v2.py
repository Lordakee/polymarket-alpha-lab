"""Decimal-only research SLA report for fast event source refresh cadence."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any


DEFAULT_RESEARCH_PACKET_FAST_EVENT_SOURCE_SLA_V2_CONFIG_VERSION = (
    "research-packet-fast-event-source-sla-v2"
)

DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
TWO = Decimal("2.000000")
THREE = Decimal("3.000000")
SIX = Decimal("6.000000")
COUNT_QUANT = Decimal("0.000001")
RATIO_QUANT = Decimal("0.000001")
SCORE_QUANT = Decimal("0.000001")
SECONDS_QUANT = Decimal("0.000001")
MINUTES_QUANT = Decimal("0.000001")
PROBABILITY_QUANT = Decimal("0.000001")
VELOCITY_QUANT = Decimal("0.000001")
MODERATE_CONTRADICTION_SCORE = Decimal("0.500000")
HIGH_CONTRADICTION_SCORE = Decimal("0.750000")
HIGH_SPECIALIST_UNCERTAINTY = Decimal("0.750000")

CONTRADICTION_SEVERITIES = ("none", "moderate", "high")
ROW_STATUSES = ("pass", "watch", "blocked")
REPORT_STATUSES = ("pass", "watch", "blocked")

PASS_REASON = "fast_event_source_sla_pass"
WATCH_REASON = "fast_event_source_sla_watch"
BLOCKED_REASON = "fast_event_source_sla_blocked"
SOURCE_REFRESH_OVER_SLA_REASON = "source_refresh_over_sla"
EVENT_VELOCITY_HIGH_REASON = "event_velocity_high"
MARKET_PROBABILITY_MOVEMENT_HIGH_REASON = "market_probability_movement_high"
OFFICIAL_SOURCE_LAG_HIGH_REASON = "official_source_lag_high"
CONTRADICTION_SEVERITY_HIGH_REASON = "contradiction_severity_high"
RESOLUTION_HORIZON_NEAR_REASON = "resolution_horizon_near"
SPECIALIST_UNCERTAINTY_HIGH_REASON = "specialist_uncertainty_high"

REASON_CODES = (
    PASS_REASON,
    WATCH_REASON,
    BLOCKED_REASON,
    SOURCE_REFRESH_OVER_SLA_REASON,
    EVENT_VELOCITY_HIGH_REASON,
    MARKET_PROBABILITY_MOVEMENT_HIGH_REASON,
    OFFICIAL_SOURCE_LAG_HIGH_REASON,
    CONTRADICTION_SEVERITY_HIGH_REASON,
    RESOLUTION_HORIZON_NEAR_REASON,
    SPECIALIST_UNCERTAINTY_HIGH_REASON,
)
ROW_REASON_CODES = (
    PASS_REASON,
    SOURCE_REFRESH_OVER_SLA_REASON,
    EVENT_VELOCITY_HIGH_REASON,
    MARKET_PROBABILITY_MOVEMENT_HIGH_REASON,
    OFFICIAL_SOURCE_LAG_HIGH_REASON,
    CONTRADICTION_SEVERITY_HIGH_REASON,
    RESOLUTION_HORIZON_NEAR_REASON,
    SPECIALIST_UNCERTAINTY_HIGH_REASON,
)
REPORT_REASON_CODES = REASON_CODES
BLOCKING_ROW_REASONS = (
    EVENT_VELOCITY_HIGH_REASON,
    MARKET_PROBABILITY_MOVEMENT_HIGH_REASON,
    OFFICIAL_SOURCE_LAG_HIGH_REASON,
    CONTRADICTION_SEVERITY_HIGH_REASON,
    SPECIALIST_UNCERTAINTY_HIGH_REASON,
)
STATUS_WEIGHT = {"blocked": 0, "watch": 1, "pass": 2}

ROW_PAYLOAD_FIELDS = (
    "packet_id",
    "event_source_id",
    "row_status",
    "observed_refresh_age_seconds",
    "event_velocity_per_hour",
    "market_probability_movement",
    "official_source_lag_seconds",
    "contradiction_severity",
    "resolution_horizon_minutes",
    "specialist_uncertainty",
    "urgency_score",
    "required_refresh_sla_seconds",
    "seconds_over_required_refresh_sla",
    "source_refresh_cadence_adequacy_score",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST = (
    "generated_at",
    "config_version",
    "report_status",
    "source_row_count",
    "pass_row_count",
    "watch_row_count",
    "blocked_row_count",
    "issue_row_count",
    "issue_ratio",
    "max_observed_refresh_age_seconds",
    "max_urgency_score",
    "min_source_refresh_cadence_adequacy_score",
    "rows",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_PAYLOAD_FIELDS = (
    *REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    DERIVED_VALIDATION_DIGEST_FIELD,
)
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
UNSAFE_PUBLIC_PAYLOAD_TEXT_TOKENS = (
    "auth",
    "buy",
    "database",
    "live",
    "mutation",
    "network",
    "order",
    "persist",
    "sell",
    "signing",
    "trade",
    "wallet",
)


@dataclass(frozen=True)
class ResearchPacketFastEventSourceSlaV2Config:
    config_version: str = DEFAULT_RESEARCH_PACKET_FAST_EVENT_SOURCE_SLA_V2_CONFIG_VERSION
    max_refresh_sla_seconds: Decimal = Decimal("900.000000")
    min_refresh_sla_seconds: Decimal = Decimal("60.000000")
    high_event_velocity_per_hour: Decimal = Decimal("12.000000")
    high_probability_movement: Decimal = Decimal("0.080000")
    official_lag_sla_seconds: Decimal = Decimal("300.000000")
    near_resolution_minutes: Decimal = Decimal("120.000000")
    critical_resolution_minutes: Decimal = Decimal("30.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketFastEventSourceSlaV2Config does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchPacketFastEventSourceSlaV2Config,
        )
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        for field_name in (
            "max_refresh_sla_seconds",
            "min_refresh_sla_seconds",
            "official_lag_sla_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_seconds(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "high_event_velocity_per_hour",
            _require_positive_decimal(
                "high_event_velocity_per_hour",
                self.high_event_velocity_per_hour,
                VELOCITY_QUANT,
            ),
        )
        object.__setattr__(
            self,
            "high_probability_movement",
            _require_positive_probability(
                "high_probability_movement",
                self.high_probability_movement,
            ),
        )
        for field_name in ("near_resolution_minutes", "critical_resolution_minutes"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(
                    field_name,
                    getattr(self, field_name),
                    MINUTES_QUANT,
                ),
            )
        if self.min_refresh_sla_seconds > self.max_refresh_sla_seconds:
            raise ValueError("min_refresh_sla_seconds must be <= max_refresh_sla_seconds")
        if self.critical_resolution_minutes > self.near_resolution_minutes:
            raise ValueError(
                "critical_resolution_minutes must be <= near_resolution_minutes",
            )
        _reject_unsafe_public_payload("config", self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchPacketFastEventSourceSlaV2InputRow:
    packet_id: str
    event_source_id: str
    observed_refresh_age_seconds: Decimal
    event_velocity_per_hour: Decimal
    market_probability_movement: Decimal
    official_source_lag_seconds: Decimal
    contradiction_severity: str
    resolution_horizon_minutes: Decimal
    specialist_uncertainty: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketFastEventSourceSlaV2InputRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "input row",
            self,
            ResearchPacketFastEventSourceSlaV2InputRow,
        )
        for field_name in ("packet_id", "event_source_id"):
            object.__setattr__(
                self,
                field_name,
                _require_canonical_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "observed_refresh_age_seconds",
            _require_nonnegative_seconds(
                "observed_refresh_age_seconds",
                self.observed_refresh_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "event_velocity_per_hour",
            _require_nonnegative_decimal(
                "event_velocity_per_hour",
                self.event_velocity_per_hour,
                VELOCITY_QUANT,
            ),
        )
        object.__setattr__(
            self,
            "market_probability_movement",
            _require_probability(
                "market_probability_movement",
                self.market_probability_movement,
            ),
        )
        object.__setattr__(
            self,
            "official_source_lag_seconds",
            _require_nonnegative_seconds(
                "official_source_lag_seconds",
                self.official_source_lag_seconds,
            ),
        )
        object.__setattr__(
            self,
            "contradiction_severity",
            _require_member(
                "contradiction_severity",
                self.contradiction_severity,
                CONTRADICTION_SEVERITIES,
            ),
        )
        object.__setattr__(
            self,
            "resolution_horizon_minutes",
            _require_nonnegative_decimal(
                "resolution_horizon_minutes",
                self.resolution_horizon_minutes,
                MINUTES_QUANT,
            ),
        )
        object.__setattr__(
            self,
            "specialist_uncertainty",
            _require_probability(
                "specialist_uncertainty",
                self.specialist_uncertainty,
            ),
        )
        _reject_unsafe_public_payload("input row", self)
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class ResearchPacketFastEventSourceSlaV2Row:
    packet_id: str
    event_source_id: str
    row_status: str
    observed_refresh_age_seconds: Decimal
    event_velocity_per_hour: Decimal
    market_probability_movement: Decimal
    official_source_lag_seconds: Decimal
    contradiction_severity: str
    resolution_horizon_minutes: Decimal
    specialist_uncertainty: Decimal
    urgency_score: Decimal
    required_refresh_sla_seconds: Decimal
    seconds_over_required_refresh_sla: Decimal
    source_refresh_cadence_adequacy_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketFastEventSourceSlaV2Row does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchPacketFastEventSourceSlaV2Row)
        for field_name in ("packet_id", "event_source_id"):
            object.__setattr__(
                self,
                field_name,
                _require_canonical_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "row_status",
            _require_member("row_status", self.row_status, ROW_STATUSES),
        )
        for field_name in (
            "observed_refresh_age_seconds",
            "official_source_lag_seconds",
            "required_refresh_sla_seconds",
            "seconds_over_required_refresh_sla",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_seconds(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "event_velocity_per_hour",
            _require_nonnegative_decimal(
                "event_velocity_per_hour",
                self.event_velocity_per_hour,
                VELOCITY_QUANT,
            ),
        )
        for field_name in (
            "market_probability_movement",
            "specialist_uncertainty",
            "urgency_score",
            "source_refresh_cadence_adequacy_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "contradiction_severity",
            _require_member(
                "contradiction_severity",
                self.contradiction_severity,
                CONTRADICTION_SEVERITIES,
            ),
        )
        object.__setattr__(
            self,
            "resolution_horizon_minutes",
            _require_nonnegative_decimal(
                "resolution_horizon_minutes",
                self.resolution_horizon_minutes,
                MINUTES_QUANT,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                ROW_REASON_CODES,
            ),
        )
        _reject_unsafe_public_payload("row", self)
        _require_hard_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchPacketFastEventSourceSlaV2Report:
    generated_at: datetime
    config_version: str
    report_status: str
    source_row_count: Decimal
    pass_row_count: Decimal
    watch_row_count: Decimal
    blocked_row_count: Decimal
    issue_row_count: Decimal
    issue_ratio: Decimal
    max_observed_refresh_age_seconds: Decimal
    max_urgency_score: Decimal
    min_source_refresh_cadence_adequacy_score: Decimal
    rows: tuple[ResearchPacketFastEventSourceSlaV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketFastEventSourceSlaV2Report does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchPacketFastEventSourceSlaV2Report)
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        object.__setattr__(
            self,
            "report_status",
            _require_member("report_status", self.report_status, REPORT_STATUSES),
        )
        for field_name in (
            "source_row_count",
            "pass_row_count",
            "watch_row_count",
            "blocked_row_count",
            "issue_row_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "issue_ratio",
            _require_probability("issue_ratio", self.issue_ratio),
        )
        for field_name in ("max_observed_refresh_age_seconds",):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_seconds(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_urgency_score",
            "min_source_refresh_cadence_adequacy_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_sla_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _reject_unsafe_public_payload("report", self)
        _require_hard_flags("report", self)
        _validate_report(self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _normalize_sha256(
                    DERIVED_VALIDATION_DIGEST_FIELD,
                    self.derived_validation_digest,
                ),
            )
        _validate_report_derived_validation_digest(self)

    @property
    def payload(self) -> dict[str, object]:
        return research_packet_fast_event_source_sla_v2_report_to_payload(self)


def build_research_packet_fast_event_source_sla_v2_report(
    source_rows: object,
    *,
    config: ResearchPacketFastEventSourceSlaV2Config,
    generated_at: datetime,
) -> ResearchPacketFastEventSourceSlaV2Report:
    _require_exact_type("config", config, ResearchPacketFastEventSourceSlaV2Config)
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_rows = _normalize_input_rows(source_rows)
    _validate_unique_event_source_pairs(normalized_rows)

    rows = _sort_sla_rows(
        tuple(_row_from_input(row, config=config) for row in normalized_rows),
    )
    issue_count = _decimal_count(sum(1 for row in rows if row.row_status != "pass"))

    return ResearchPacketFastEventSourceSlaV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=_report_status(rows),
        source_row_count=_decimal_count(len(rows)),
        pass_row_count=_status_count(rows, "pass"),
        watch_row_count=_status_count(rows, "watch"),
        blocked_row_count=_status_count(rows, "blocked"),
        issue_row_count=issue_count,
        issue_ratio=_ratio(issue_count, _decimal_count(len(rows))),
        max_observed_refresh_age_seconds=max(
            (row.observed_refresh_age_seconds for row in rows),
            default=ZERO,
        ),
        max_urgency_score=max((row.urgency_score for row in rows), default=ZERO),
        min_source_refresh_cadence_adequacy_score=min(
            (row.source_refresh_cadence_adequacy_score for row in rows),
            default=ZERO,
        ),
        rows=rows,
        reason_codes=_report_reason_codes(rows),
    )


def research_packet_fast_event_source_sla_v2_report_to_payload(
    report: ResearchPacketFastEventSourceSlaV2Report | dict[str, object],
) -> dict[str, object]:
    if type(report) is ResearchPacketFastEventSourceSlaV2Report:
        _reject_unsafe_public_payload("report", report)
        _require_hard_flags("report", report)
        _validate_report_derived_validation_digest(report)
        _validate_report(report)
        payload = _report_public_payload_values(report)
        payload[DERIVED_VALIDATION_DIGEST_FIELD] = report.derived_validation_digest
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _require_public_payload_fields(report)
        _validate_public_payload(report)
        return _copy_json_object(report)
    raise ValueError(
        "report must be a ResearchPacketFastEventSourceSlaV2Report or payload dict",
    )


def _row_from_input(
    source_row: ResearchPacketFastEventSourceSlaV2InputRow,
    *,
    config: ResearchPacketFastEventSourceSlaV2Config,
) -> ResearchPacketFastEventSourceSlaV2Row:
    urgency_score = _urgency_score(source_row, config)
    required_refresh_sla_seconds = _required_refresh_sla_seconds(
        urgency_score,
        config,
    )
    seconds_over_sla = _seconds_over_required_refresh_sla(
        source_row.observed_refresh_age_seconds,
        required_refresh_sla_seconds,
    )
    adequacy_score = _source_refresh_cadence_adequacy_score(
        source_row.observed_refresh_age_seconds,
        required_refresh_sla_seconds,
    )
    reason_codes = _row_reason_codes(
        source_row,
        config=config,
        required_refresh_sla_seconds=required_refresh_sla_seconds,
    )
    return ResearchPacketFastEventSourceSlaV2Row(
        packet_id=source_row.packet_id,
        event_source_id=source_row.event_source_id,
        row_status=_row_status(reason_codes),
        observed_refresh_age_seconds=source_row.observed_refresh_age_seconds,
        event_velocity_per_hour=source_row.event_velocity_per_hour,
        market_probability_movement=source_row.market_probability_movement,
        official_source_lag_seconds=source_row.official_source_lag_seconds,
        contradiction_severity=source_row.contradiction_severity,
        resolution_horizon_minutes=source_row.resolution_horizon_minutes,
        specialist_uncertainty=source_row.specialist_uncertainty,
        urgency_score=urgency_score,
        required_refresh_sla_seconds=required_refresh_sla_seconds,
        seconds_over_required_refresh_sla=seconds_over_sla,
        source_refresh_cadence_adequacy_score=adequacy_score,
        reason_codes=reason_codes,
    )


def _urgency_score(
    source_row: ResearchPacketFastEventSourceSlaV2InputRow,
    config: ResearchPacketFastEventSourceSlaV2Config,
) -> Decimal:
    return _average_score(
        (
            _capped_ratio(
                source_row.event_velocity_per_hour,
                config.high_event_velocity_per_hour,
            ),
            _capped_ratio(
                source_row.market_probability_movement,
                config.high_probability_movement,
            ),
            _capped_ratio(
                source_row.official_source_lag_seconds,
                config.official_lag_sla_seconds,
            ),
            _contradiction_score(source_row.contradiction_severity),
            _resolution_horizon_score(
                source_row.resolution_horizon_minutes,
                config,
            ),
            source_row.specialist_uncertainty,
        ),
    )


def _required_refresh_sla_seconds(
    urgency_score: Decimal,
    config: ResearchPacketFastEventSourceSlaV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        candidate = config.max_refresh_sla_seconds * (ONE - urgency_score)
    return max(config.min_refresh_sla_seconds, candidate).quantize(SECONDS_QUANT)


def _seconds_over_required_refresh_sla(
    observed_refresh_age_seconds: Decimal,
    required_refresh_sla_seconds: Decimal,
) -> Decimal:
    if observed_refresh_age_seconds <= required_refresh_sla_seconds:
        return ZERO
    return (observed_refresh_age_seconds - required_refresh_sla_seconds).quantize(
        SECONDS_QUANT,
    )


def _source_refresh_cadence_adequacy_score(
    observed_refresh_age_seconds: Decimal,
    required_refresh_sla_seconds: Decimal,
) -> Decimal:
    if observed_refresh_age_seconds <= ZERO:
        return ONE
    if observed_refresh_age_seconds <= required_refresh_sla_seconds:
        return ONE
    return _capped_ratio(
        required_refresh_sla_seconds,
        observed_refresh_age_seconds,
    )


def _row_reason_codes(
    source_row: ResearchPacketFastEventSourceSlaV2InputRow,
    *,
    config: ResearchPacketFastEventSourceSlaV2Config,
    required_refresh_sla_seconds: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if source_row.observed_refresh_age_seconds > required_refresh_sla_seconds:
        reasons.append(SOURCE_REFRESH_OVER_SLA_REASON)
    if source_row.event_velocity_per_hour >= config.high_event_velocity_per_hour:
        reasons.append(EVENT_VELOCITY_HIGH_REASON)
    if source_row.market_probability_movement >= config.high_probability_movement:
        reasons.append(MARKET_PROBABILITY_MOVEMENT_HIGH_REASON)
    if source_row.official_source_lag_seconds >= config.official_lag_sla_seconds:
        reasons.append(OFFICIAL_SOURCE_LAG_HIGH_REASON)
    if source_row.contradiction_severity == "high":
        reasons.append(CONTRADICTION_SEVERITY_HIGH_REASON)
    if source_row.resolution_horizon_minutes <= config.near_resolution_minutes:
        reasons.append(RESOLUTION_HORIZON_NEAR_REASON)
    if source_row.specialist_uncertainty >= HIGH_SPECIALIST_UNCERTAINTY:
        reasons.append(SPECIALIST_UNCERTAINTY_HIGH_REASON)
    if not reasons:
        return (PASS_REASON,)
    return tuple(reason for reason in ROW_REASON_CODES if reason in reasons)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    blocking_reasons = sum(1 for reason in reason_codes if reason in BLOCKING_ROW_REASONS)
    if (
        CONTRADICTION_SEVERITY_HIGH_REASON in reason_codes
        or OFFICIAL_SOURCE_LAG_HIGH_REASON in reason_codes
        or blocking_reasons >= 2
    ):
        return "blocked"
    if reason_codes == (PASS_REASON,):
        return "pass"
    return "watch"


def _report_status(rows: tuple[ResearchPacketFastEventSourceSlaV2Row, ...]) -> str:
    if any(row.row_status == "blocked" for row in rows):
        return "blocked"
    if any(row.row_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchPacketFastEventSourceSlaV2Row, ...],
) -> tuple[str, ...]:
    status = _report_status(rows)
    if status == "pass":
        return (PASS_REASON,)
    reasons = [BLOCKED_REASON if status == "blocked" else WATCH_REASON]
    for reason in ROW_REASON_CODES[1:]:
        if any(reason in row.reason_codes for row in rows):
            reasons.append(reason)
    return tuple(reasons)


def _contradiction_score(contradiction_severity: str) -> Decimal:
    if contradiction_severity == "high":
        return HIGH_CONTRADICTION_SCORE
    if contradiction_severity == "moderate":
        return MODERATE_CONTRADICTION_SCORE
    return ZERO


def _resolution_horizon_score(
    resolution_horizon_minutes: Decimal,
    config: ResearchPacketFastEventSourceSlaV2Config,
) -> Decimal:
    if resolution_horizon_minutes <= config.critical_resolution_minutes:
        return ONE
    if resolution_horizon_minutes > config.near_resolution_minutes:
        return ZERO
    window = config.near_resolution_minutes - config.critical_resolution_minutes
    if window <= ZERO:
        return ONE
    with localcontext(DECIMAL_CONTEXT):
        return _cap_probability(
            (config.near_resolution_minutes - resolution_horizon_minutes) / window,
        )


def _average_score(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (sum(values, ZERO) / Decimal(len(values))).quantize(SCORE_QUANT)


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return _cap_probability(numerator / denominator)


def _cap_probability(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return value.quantize(PROBABILITY_QUANT)


def _normalize_input_rows(
    source_rows: object,
) -> tuple[ResearchPacketFastEventSourceSlaV2InputRow, ...]:
    try:
        rows = tuple(source_rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("source_rows must be iterable") from exc
    for row in rows:
        _require_exact_type("source row", row, ResearchPacketFastEventSourceSlaV2InputRow)
        _require_hard_flags("source row", row)
    return rows


def _validate_unique_event_source_pairs(
    rows: tuple[ResearchPacketFastEventSourceSlaV2InputRow, ...],
) -> None:
    pairs = tuple((row.packet_id, row.event_source_id) for row in rows)
    if len(set(pairs)) != len(pairs):
        raise ValueError("event source pairs must be unique")


def _normalize_sla_rows(
    value: object,
) -> tuple[ResearchPacketFastEventSourceSlaV2Row, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        _require_exact_type("row", row, ResearchPacketFastEventSourceSlaV2Row)
        _require_hard_flags("row", row)
    return _sort_sla_rows(rows)


def _sort_sla_rows(
    rows: tuple[ResearchPacketFastEventSourceSlaV2Row, ...],
) -> tuple[ResearchPacketFastEventSourceSlaV2Row, ...]:
    return tuple(sorted(rows, key=_sla_row_sort_key))


def _sla_row_sort_key(
    row: ResearchPacketFastEventSourceSlaV2Row,
) -> tuple[int, Decimal, Decimal, str, str]:
    return (
        STATUS_WEIGHT[row.row_status],
        -row.urgency_score,
        -row.seconds_over_required_refresh_sla,
        row.packet_id,
        row.event_source_id,
    )


def _status_count(
    rows: tuple[ResearchPacketFastEventSourceSlaV2Row, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.row_status == status))


def _validate_row(row: ResearchPacketFastEventSourceSlaV2Row) -> None:
    if row.seconds_over_required_refresh_sla != _seconds_over_required_refresh_sla(
        row.observed_refresh_age_seconds,
        row.required_refresh_sla_seconds,
    ):
        raise ValueError("seconds_over_required_refresh_sla must match refresh fields")
    if row.source_refresh_cadence_adequacy_score != (
        _source_refresh_cadence_adequacy_score(
            row.observed_refresh_age_seconds,
            row.required_refresh_sla_seconds,
        )
    ):
        raise ValueError(
            "source_refresh_cadence_adequacy_score must match refresh fields",
        )
    if row.row_status != _row_status(row.reason_codes):
        raise ValueError("row_status must match reason_codes")
    if row.reason_codes == (PASS_REASON,) and (
        row.seconds_over_required_refresh_sla != ZERO
    ):
        raise ValueError("pass row cannot be over required refresh SLA")


def _validate_report(report: ResearchPacketFastEventSourceSlaV2Report) -> None:
    if report.source_row_count != _decimal_count(len(report.rows)):
        raise ValueError("source_row_count must match rows")
    if report.pass_row_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_row_count must match rows")
    if report.watch_row_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_row_count must match rows")
    if report.blocked_row_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_row_count must match rows")
    if report.issue_row_count != _decimal_count(
        sum(1 for row in report.rows if row.row_status != "pass"),
    ):
        raise ValueError("issue_row_count must match rows")
    if report.pass_row_count + report.watch_row_count + report.blocked_row_count != (
        report.source_row_count
    ):
        raise ValueError("status counts must sum to source_row_count")
    if report.issue_ratio != _ratio(report.issue_row_count, report.source_row_count):
        raise ValueError("issue_ratio must match issue counts")
    if report.max_observed_refresh_age_seconds != max(
        (row.observed_refresh_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_observed_refresh_age_seconds must match rows")
    if report.max_urgency_score != max(
        (row.urgency_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_urgency_score must match rows")
    if report.min_source_refresh_cadence_adequacy_score != min(
        (row.source_refresh_cadence_adequacy_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError(
            "min_source_refresh_cadence_adequacy_score must match rows",
        )
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANT)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(RATIO_QUANT)


def _require_exact_type(
    field_name: str,
    value: object,
    expected_type: type[object],
) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value.strip() != value:
        raise ValueError(f"{field_name} must not contain leading or trailing whitespace")
    return value


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")
    return value


def _require_decimal(field_name: str, value: object, quantum: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(quantum)


def _require_positive_decimal(
    field_name: str,
    value: object,
    quantum: Decimal,
) -> Decimal:
    decimal_value = _require_decimal(field_name, value, quantum)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(
    field_name: str,
    value: object,
    quantum: Decimal,
) -> Decimal:
    decimal_value = _require_decimal(field_name, value, quantum)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_seconds(field_name: str, value: object) -> Decimal:
    return _require_positive_decimal(field_name, value, SECONDS_QUANT)


def _require_nonnegative_seconds(field_name: str, value: object) -> Decimal:
    return _require_nonnegative_decimal(field_name, value, SECONDS_QUANT)


def _require_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value, PROBABILITY_QUANT)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_positive_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _require_probability(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_count(field_name: str, value: object) -> Decimal:
    return _require_nonnegative_decimal(field_name, value, COUNT_QUANT)


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    codes = tuple(value)
    if not codes:
        raise ValueError(f"{field_name} must not be empty")
    for code in codes:
        _require_member("reason_code", code, allowed)
    if len(set(codes)) != len(codes):
        raise ValueError(f"{field_name} must not contain duplicates")
    return tuple(code for code in allowed if code in codes)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_field(field.name)
            _reject_unsafe_public_payload(
                f"{label}.{field.name}",
                getattr(value, field.name),
            )
        return
    if type(value) is dict:
        for key, child in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} public fields must be strings")
            _reject_unsafe_public_field(key)
            _reject_unsafe_public_payload(f"{label}.{key}", child)
        return
    if type(value) in (list, tuple):
        for index, child in enumerate(value):
            _reject_unsafe_public_payload(f"{label}[{index}]", child)
        return
    if type(value) is str:
        lowered_value = value.lower()
        if any(token in lowered_value for token in UNSAFE_PUBLIC_PAYLOAD_TEXT_TOKENS):
            raise ValueError(f"unsafe public value in {label}")


def _reject_unsafe_public_field(field_name: str) -> None:
    lowered_field = field_name.lower()
    if any(token in lowered_field for token in UNSAFE_PUBLIC_PAYLOAD_TEXT_TOKENS):
        raise ValueError(f"unsafe public field {field_name}")


def _report_public_payload_values(
    report: ResearchPacketFastEventSourceSlaV2Report,
) -> dict[str, object]:
    return {
        field_name: _payload_value(getattr(report, field_name))
        for field_name in REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST
    }


def _payload_value(value: object) -> object:
    if type(value) is Decimal:
        return _decimal_payload(value)
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        return {key: _payload_value(child) for key, child in value.items()}
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported public payload value {type(value).__name__}")


def _decimal_payload(value: Decimal) -> str:
    return str(value.quantize(COUNT_QUANT))


def _report_derived_validation_digest(
    report: ResearchPacketFastEventSourceSlaV2Report,
) -> str:
    return _digest_payload(_report_public_payload_values(report))


def _digest_payload(payload_without_digest: dict[str, object]) -> str:
    encoded = json.dumps(
        payload_without_digest,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _validate_report_derived_validation_digest(
    report: ResearchPacketFastEventSourceSlaV2Report,
) -> None:
    expected = _report_derived_validation_digest(report)
    if report.derived_validation_digest != expected:
        raise ValueError("derived_validation_digest must match public report payload")


def _require_public_payload_fields(payload: dict[str, object]) -> None:
    missing_fields = set(REPORT_PAYLOAD_FIELDS) - set(payload)
    if missing_fields:
        missing = ", ".join(sorted(missing_fields))
        raise ValueError(f"payload missing required fields: {missing}")
    extra_fields = set(payload) - set(REPORT_PAYLOAD_FIELDS)
    if extra_fields:
        extra = ", ".join(sorted(extra_fields))
        raise ValueError(f"payload contains unknown fields: {extra}")


def _validate_public_payload(payload: dict[str, object]) -> None:
    _normalize_sha256(
        DERIVED_VALIDATION_DIGEST_FIELD,
        payload[DERIVED_VALIDATION_DIGEST_FIELD],
    )
    _require_payload_string("generated_at", payload["generated_at"])
    _require_payload_string("config_version", payload["config_version"])
    _require_member("report_status", payload["report_status"], REPORT_STATUSES)
    for field_name in (
        "source_row_count",
        "pass_row_count",
        "watch_row_count",
        "blocked_row_count",
        "issue_row_count",
        "issue_ratio",
        "max_observed_refresh_age_seconds",
        "max_urgency_score",
        "min_source_refresh_cadence_adequacy_score",
    ):
        _require_decimal_payload_string(field_name, payload[field_name])
    _require_public_payload_reason_codes(
        "reason_codes",
        payload["reason_codes"],
        REPORT_REASON_CODES,
    )
    _require_public_payload_flags(payload)
    rows_value = payload["rows"]
    if type(rows_value) is not list:
        raise ValueError("rows must be a list")
    for row_payload in rows_value:
        if type(row_payload) is not dict:
            raise ValueError("rows must contain objects")
        _validate_public_row_payload(row_payload)
    payload_without_digest = {
        field_name: payload[field_name]
        for field_name in REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST
    }
    if payload[DERIVED_VALIDATION_DIGEST_FIELD] != _digest_payload(
        payload_without_digest,
    ):
        raise ValueError("derived_validation_digest must match public report payload")


def _validate_public_row_payload(row_payload: dict[str, object]) -> None:
    missing_fields = set(ROW_PAYLOAD_FIELDS) - set(row_payload)
    if missing_fields:
        missing = ", ".join(sorted(missing_fields))
        raise ValueError(f"row payload missing required fields: {missing}")
    extra_fields = set(row_payload) - set(ROW_PAYLOAD_FIELDS)
    if extra_fields:
        extra = ", ".join(sorted(extra_fields))
        raise ValueError(f"row payload contains unknown fields: {extra}")
    _require_payload_string("packet_id", row_payload["packet_id"])
    _require_payload_string("event_source_id", row_payload["event_source_id"])
    _require_member("row_status", row_payload["row_status"], ROW_STATUSES)
    _require_member(
        "contradiction_severity",
        row_payload["contradiction_severity"],
        CONTRADICTION_SEVERITIES,
    )
    for field_name in (
        "observed_refresh_age_seconds",
        "event_velocity_per_hour",
        "market_probability_movement",
        "official_source_lag_seconds",
        "resolution_horizon_minutes",
        "specialist_uncertainty",
        "urgency_score",
        "required_refresh_sla_seconds",
        "seconds_over_required_refresh_sla",
        "source_refresh_cadence_adequacy_score",
    ):
        _require_decimal_payload_string(field_name, row_payload[field_name])
    _require_public_payload_reason_codes(
        "reason_codes",
        row_payload["reason_codes"],
        ROW_REASON_CODES,
    )
    _require_public_payload_flags(row_payload)


def _require_payload_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _require_decimal_payload_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if str(decimal_value.quantize(COUNT_QUANT)) != value:
        raise ValueError(f"{field_name} must be a six-decimal string")
    return decimal_value


def _require_public_payload_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return _normalize_reason_codes(field_name, tuple(value), allowed)


def _require_public_payload_flags(payload: dict[str, object]) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _copy_json_object(payload: dict[str, object]) -> dict[str, object]:
    copied = json.loads(json.dumps(payload, separators=(",", ":"), sort_keys=True))
    if type(copied) is not dict:
        raise ValueError("payload must be an object")
    return copied


__all__ = (
    "BLOCKED_REASON",
    "DEFAULT_RESEARCH_PACKET_FAST_EVENT_SOURCE_SLA_V2_CONFIG_VERSION",
    "PASS_REASON",
    "REASON_CODES",
    "REPORT_STATUSES",
    "ROW_STATUSES",
    "ResearchPacketFastEventSourceSlaV2Config",
    "ResearchPacketFastEventSourceSlaV2InputRow",
    "ResearchPacketFastEventSourceSlaV2Report",
    "ResearchPacketFastEventSourceSlaV2Row",
    "SOURCE_REFRESH_OVER_SLA_REASON",
    "WATCH_REASON",
    "build_research_packet_fast_event_source_sla_v2_report",
    "research_packet_fast_event_source_sla_v2_report_to_payload",
)
