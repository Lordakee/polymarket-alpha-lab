"""Readonly SLA gate for research packet source recency."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json


DEFAULT_RESEARCH_PACKET_LIVE_SOURCE_RECENCY_SLA_GATE_V2_CONFIG_VERSION = (
    "research-packet-live-source-recency-sla-gate-v2"
)

DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
TWO = Decimal("2.000000")
COUNT_QUANT = Decimal("0.000001")
RATIO_QUANT = Decimal("0.000001")
SECONDS_QUANT = Decimal("0.000001")
SCORE_QUANT = Decimal("0.000001")
MICROSECONDS_PER_SECOND = Decimal("1000000")
SECONDS_PER_DAY = Decimal("86400")

SOURCE_TIERS = ("official", "primary", "secondary", "live")
ROW_STATUSES = ("pass", "warn", "blocked")
REPORT_STATUSES = ROW_STATUSES

PASS_REASON = "live_source_recency_sla_pass"
WARN_REASON = "live_source_recency_sla_warn"
BLOCKED_REASON = "live_source_recency_sla_blocked"
SOURCE_AGE_FRESH_REASON = "source_age_fresh"
SOURCE_AGE_STALE_REASON = "source_age_stale"
REQUIRED_RECENCY_MET_REASON = "required_recency_met"
REQUIRED_RECENCY_MISSED_REASON = "required_recency_missed"
MARKET_RESOLUTION_BUFFER_CLEAR_REASON = "market_resolution_buffer_clear"
MARKET_RESOLUTION_NEAR_REASON = "market_resolution_near"
OFFICIAL_SOURCE_TIER_REASON = "official_source_tier"
PRIMARY_SOURCE_TIER_REASON = "primary_source_tier"
SECONDARY_SOURCE_TIER_REASON = "secondary_source_tier"
LIVE_SOURCE_TIER_REASON = "live_source_tier"
GATE_EMPTY_REASON = "live_source_recency_sla_gate_empty"

ROW_REASON_CODES = (
    PASS_REASON,
    WARN_REASON,
    BLOCKED_REASON,
    SOURCE_AGE_FRESH_REASON,
    SOURCE_AGE_STALE_REASON,
    REQUIRED_RECENCY_MET_REASON,
    REQUIRED_RECENCY_MISSED_REASON,
    MARKET_RESOLUTION_BUFFER_CLEAR_REASON,
    MARKET_RESOLUTION_NEAR_REASON,
    OFFICIAL_SOURCE_TIER_REASON,
    PRIMARY_SOURCE_TIER_REASON,
    SECONDARY_SOURCE_TIER_REASON,
    LIVE_SOURCE_TIER_REASON,
)
REPORT_REASON_CODES = (
    PASS_REASON,
    WARN_REASON,
    BLOCKED_REASON,
    GATE_EMPTY_REASON,
    SOURCE_AGE_STALE_REASON,
    REQUIRED_RECENCY_MISSED_REASON,
    MARKET_RESOLUTION_NEAR_REASON,
)
SOURCE_TIER_REASON = {
    "official": OFFICIAL_SOURCE_TIER_REASON,
    "primary": PRIMARY_SOURCE_TIER_REASON,
    "secondary": SECONDARY_SOURCE_TIER_REASON,
    "live": LIVE_SOURCE_TIER_REASON,
}
STATUS_WEIGHT = {"blocked": 0, "warn": 1, "pass": 2}
SOURCE_TIER_SCORES = {
    "official": Decimal("1.000000"),
    "primary": Decimal("0.900000"),
    "secondary": Decimal("0.750000"),
    "live": Decimal("0.850000"),
}

PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
FORBIDDEN_PUBLIC_TEXT_TOKENS = (
    "auth",
    "buy",
    "database",
    "mutation",
    "order",
    "persist",
    "sell",
    "signing",
    "trade",
    "trading",
    "wallet",
)
ROW_PAYLOAD_FIELDS = (
    "packet_id",
    "market_id",
    "source_id",
    "source_tier",
    "row_status",
    "observed_at",
    "market_resolution_at",
    "source_age_seconds",
    "market_time_to_resolution_seconds",
    "required_recency_seconds",
    "effective_recency_sla_seconds",
    "seconds_over_effective_sla",
    "source_age_score",
    "market_time_to_resolution_score",
    "source_tier_score",
    "information_freshness_score",
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
    "warn_row_count",
    "blocked_row_count",
    "issue_row_count",
    "issue_ratio",
    "max_source_age_seconds",
    "max_seconds_over_effective_sla",
    "min_information_freshness_score",
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


@dataclass(frozen=True)
class ResearchPacketLiveSourceRecencySlaGateV2Config:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_LIVE_SOURCE_RECENCY_SLA_GATE_V2_CONFIG_VERSION
    )
    near_resolution_seconds: Decimal = Decimal("7200.000000")
    critical_resolution_seconds: Decimal = Decimal("900.000000")
    minimum_effective_recency_seconds: Decimal = Decimal("60.000000")
    blocked_age_multiplier: Decimal = Decimal("2.000000")
    source_age_weight: Decimal = Decimal("0.700000")
    market_time_to_resolution_weight: Decimal = Decimal("0.200000")
    source_tier_weight: Decimal = Decimal("0.100000")
    pass_score_floor: Decimal = Decimal("0.800000")
    warn_score_floor: Decimal = Decimal("0.350000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketLiveSourceRecencySlaGateV2Config does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchPacketLiveSourceRecencySlaGateV2Config,
        )
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        for field_name in (
            "near_resolution_seconds",
            "critical_resolution_seconds",
            "minimum_effective_recency_seconds",
            "blocked_age_multiplier",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_seconds(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_age_weight",
            "market_time_to_resolution_weight",
            "source_tier_weight",
            "pass_score_floor",
            "warn_score_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _reject_forbidden_public_payload("config", self)
        _require_phase_flags("config", self)


@dataclass(frozen=True)
class ResearchPacketLiveSourceRecencySlaGateV2InputRow:
    packet_id: str
    market_id: str
    source_id: str
    source_tier: str
    observed_at: datetime
    market_resolution_at: datetime
    required_recency_seconds: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketLiveSourceRecencySlaGateV2InputRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "input row",
            self,
            ResearchPacketLiveSourceRecencySlaGateV2InputRow,
        )
        for field_name in ("packet_id", "market_id", "source_id"):
            object.__setattr__(
                self,
                field_name,
                _require_canonical_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_tier",
            _require_member("source_tier", self.source_tier, SOURCE_TIERS),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "market_resolution_at",
            _as_utc("market_resolution_at", self.market_resolution_at),
        )
        object.__setattr__(
            self,
            "required_recency_seconds",
            _require_positive_seconds(
                "required_recency_seconds",
                self.required_recency_seconds,
            ),
        )
        _reject_forbidden_public_payload("input row", self)
        _require_phase_flags("input row", self)


@dataclass(frozen=True)
class ResearchPacketLiveSourceRecencySlaGateV2Row:
    packet_id: str
    market_id: str
    source_id: str
    source_tier: str
    row_status: str
    observed_at: datetime
    market_resolution_at: datetime
    source_age_seconds: Decimal
    market_time_to_resolution_seconds: Decimal
    required_recency_seconds: Decimal
    effective_recency_sla_seconds: Decimal
    seconds_over_effective_sla: Decimal
    source_age_score: Decimal
    market_time_to_resolution_score: Decimal
    source_tier_score: Decimal
    information_freshness_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketLiveSourceRecencySlaGateV2Row does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchPacketLiveSourceRecencySlaGateV2Row)
        for field_name in ("packet_id", "market_id", "source_id"):
            object.__setattr__(
                self,
                field_name,
                _require_canonical_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_tier",
            _require_member("source_tier", self.source_tier, SOURCE_TIERS),
        )
        object.__setattr__(
            self,
            "row_status",
            _require_member("row_status", self.row_status, ROW_STATUSES),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "market_resolution_at",
            _as_utc("market_resolution_at", self.market_resolution_at),
        )
        for field_name in (
            "source_age_seconds",
            "market_time_to_resolution_seconds",
            "required_recency_seconds",
            "effective_recency_sla_seconds",
            "seconds_over_effective_sla",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_seconds(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_age_score",
            "market_time_to_resolution_score",
            "source_tier_score",
            "information_freshness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _reject_forbidden_public_payload("row", self)
        _require_phase_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchPacketLiveSourceRecencySlaGateV2Report:
    generated_at: datetime
    config_version: str
    report_status: str
    source_row_count: Decimal
    pass_row_count: Decimal
    warn_row_count: Decimal
    blocked_row_count: Decimal
    issue_row_count: Decimal
    issue_ratio: Decimal
    max_source_age_seconds: Decimal
    max_seconds_over_effective_sla: Decimal
    min_information_freshness_score: Decimal
    rows: tuple[ResearchPacketLiveSourceRecencySlaGateV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketLiveSourceRecencySlaGateV2Report does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchPacketLiveSourceRecencySlaGateV2Report)
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
            "warn_row_count",
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
        for field_name in (
            "max_source_age_seconds",
            "max_seconds_over_effective_sla",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_seconds(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_information_freshness_score",
            _require_probability(
                "min_information_freshness_score",
                self.min_information_freshness_score,
            ),
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
        _reject_forbidden_public_payload("report", self)
        _require_phase_flags("report", self)
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
        return research_packet_live_source_recency_sla_gate_v2_report_to_payload(self)


def build_research_packet_live_source_recency_sla_gate_v2_report(
    source_rows: object,
    *,
    config: ResearchPacketLiveSourceRecencySlaGateV2Config,
    generated_at: datetime,
) -> ResearchPacketLiveSourceRecencySlaGateV2Report:
    _require_exact_type("config", config, ResearchPacketLiveSourceRecencySlaGateV2Config)
    _require_phase_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_rows = _normalize_input_rows(source_rows)
    _validate_unique_source_keys(normalized_rows)
    _validate_source_times(normalized_rows, generated_at_utc)

    rows = _sort_sla_rows(
        tuple(_row_from_input(row, config=config, generated_at=generated_at_utc) for row in normalized_rows),
    )
    issue_count = _decimal_count(sum(1 for row in rows if row.row_status != "pass"))
    return ResearchPacketLiveSourceRecencySlaGateV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=_report_status(rows),
        source_row_count=_decimal_count(len(rows)),
        pass_row_count=_status_count(rows, "pass"),
        warn_row_count=_status_count(rows, "warn"),
        blocked_row_count=_status_count(rows, "blocked"),
        issue_row_count=issue_count,
        issue_ratio=_ratio(issue_count, _decimal_count(len(rows))),
        max_source_age_seconds=max(
            (row.source_age_seconds for row in rows),
            default=ZERO,
        ),
        max_seconds_over_effective_sla=max(
            (row.seconds_over_effective_sla for row in rows),
            default=ZERO,
        ),
        min_information_freshness_score=min(
            (row.information_freshness_score for row in rows),
            default=ZERO,
        ),
        rows=rows,
        reason_codes=_report_reason_codes(rows),
    )


def research_packet_live_source_recency_sla_gate_v2_report_to_payload(
    report: ResearchPacketLiveSourceRecencySlaGateV2Report | dict[str, object],
) -> dict[str, object]:
    if type(report) is ResearchPacketLiveSourceRecencySlaGateV2Report:
        _reject_forbidden_public_payload("report", report)
        _require_phase_flags("report", report)
        _validate_report_derived_validation_digest(report)
        _validate_report(report)
        payload = _report_public_payload_values(report)
        payload[DERIVED_VALIDATION_DIGEST_FIELD] = report.derived_validation_digest
        return payload
    if type(report) is dict:
        _reject_forbidden_public_payload("payload", report)
        _require_public_payload_fields(report)
        _validate_public_payload(report)
        return _copy_json_object(report)
    raise ValueError(
        "report must be a ResearchPacketLiveSourceRecencySlaGateV2Report or payload dict",
    )


def _row_from_input(
    source_row: ResearchPacketLiveSourceRecencySlaGateV2InputRow,
    *,
    config: ResearchPacketLiveSourceRecencySlaGateV2Config,
    generated_at: datetime,
) -> ResearchPacketLiveSourceRecencySlaGateV2Row:
    source_age_seconds = _duration_seconds(source_row.observed_at, generated_at)
    time_to_resolution_seconds = _duration_seconds(
        generated_at,
        source_row.market_resolution_at,
    )
    effective_recency_sla_seconds = _effective_recency_sla_seconds(
        source_row.required_recency_seconds,
        time_to_resolution_seconds,
        config,
    )
    seconds_over_effective_sla = _seconds_over_sla(
        source_age_seconds,
        effective_recency_sla_seconds,
    )
    source_age_score = _source_age_score(
        source_age_seconds,
        effective_recency_sla_seconds,
    )
    time_to_resolution_score = _time_to_resolution_score(
        time_to_resolution_seconds,
        config,
    )
    source_tier_score = SOURCE_TIER_SCORES[source_row.source_tier]
    freshness_score = _information_freshness_score(
        config=config,
        source_age_score=source_age_score,
        time_to_resolution_score=time_to_resolution_score,
        source_tier_score=source_tier_score,
    )
    status = _row_status(
        source_age_seconds=source_age_seconds,
        time_to_resolution_seconds=time_to_resolution_seconds,
        effective_recency_sla_seconds=effective_recency_sla_seconds,
        information_freshness_score=freshness_score,
        config=config,
    )
    return ResearchPacketLiveSourceRecencySlaGateV2Row(
        packet_id=source_row.packet_id,
        market_id=source_row.market_id,
        source_id=source_row.source_id,
        source_tier=source_row.source_tier,
        row_status=status,
        observed_at=source_row.observed_at,
        market_resolution_at=source_row.market_resolution_at,
        source_age_seconds=source_age_seconds,
        market_time_to_resolution_seconds=time_to_resolution_seconds,
        required_recency_seconds=source_row.required_recency_seconds,
        effective_recency_sla_seconds=effective_recency_sla_seconds,
        seconds_over_effective_sla=seconds_over_effective_sla,
        source_age_score=source_age_score,
        market_time_to_resolution_score=time_to_resolution_score,
        source_tier_score=source_tier_score,
        information_freshness_score=freshness_score,
        reason_codes=_row_reason_codes(
            status=status,
            source_tier=source_row.source_tier,
            source_age_seconds=source_age_seconds,
            time_to_resolution_score=time_to_resolution_score,
            seconds_over_effective_sla=seconds_over_effective_sla,
        ),
    )


def _effective_recency_sla_seconds(
    required_recency_seconds: Decimal,
    market_time_to_resolution_seconds: Decimal,
    config: ResearchPacketLiveSourceRecencySlaGateV2Config,
) -> Decimal:
    horizon_factor = max(
        ONE / TWO,
        _capped_ratio(market_time_to_resolution_seconds, config.near_resolution_seconds),
    )
    with localcontext(DECIMAL_CONTEXT):
        candidate = required_recency_seconds * horizon_factor
    return max(config.minimum_effective_recency_seconds, candidate).quantize(
        SECONDS_QUANT,
    )


def _source_age_score(
    source_age_seconds: Decimal,
    effective_recency_sla_seconds: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _cap_probability(ONE - source_age_seconds / effective_recency_sla_seconds)


def _time_to_resolution_score(
    market_time_to_resolution_seconds: Decimal,
    config: ResearchPacketLiveSourceRecencySlaGateV2Config,
) -> Decimal:
    return _capped_ratio(market_time_to_resolution_seconds, config.near_resolution_seconds)


def _information_freshness_score(
    *,
    config: ResearchPacketLiveSourceRecencySlaGateV2Config,
    source_age_score: Decimal,
    time_to_resolution_score: Decimal,
    source_tier_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            source_age_score * config.source_age_weight
            + time_to_resolution_score * config.market_time_to_resolution_weight
            + source_tier_score * config.source_tier_weight
        )
    return _cap_probability(score)


def _seconds_over_sla(source_age_seconds: Decimal, effective_sla_seconds: Decimal) -> Decimal:
    if source_age_seconds <= effective_sla_seconds:
        return ZERO
    return (source_age_seconds - effective_sla_seconds).quantize(SECONDS_QUANT)


def _row_status(
    *,
    source_age_seconds: Decimal,
    time_to_resolution_seconds: Decimal,
    effective_recency_sla_seconds: Decimal,
    information_freshness_score: Decimal,
    config: ResearchPacketLiveSourceRecencySlaGateV2Config,
) -> str:
    with localcontext(DECIMAL_CONTEXT):
        blocked_age = (
            effective_recency_sla_seconds * config.blocked_age_multiplier
        ).quantize(SECONDS_QUANT)
    if information_freshness_score < config.warn_score_floor:
        return "blocked"
    if source_age_seconds > blocked_age:
        return "blocked"
    if (
        source_age_seconds > effective_recency_sla_seconds
        and time_to_resolution_seconds <= config.critical_resolution_seconds
    ):
        return "blocked"
    if information_freshness_score < config.pass_score_floor:
        return "warn"
    if source_age_seconds > effective_recency_sla_seconds:
        return "warn"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    source_tier: str,
    source_age_seconds: Decimal,
    time_to_resolution_score: Decimal,
    seconds_over_effective_sla: Decimal,
) -> tuple[str, ...]:
    reasons = [
        {"pass": PASS_REASON, "warn": WARN_REASON, "blocked": BLOCKED_REASON}[status],
        (
            SOURCE_AGE_FRESH_REASON
            if seconds_over_effective_sla == ZERO
            else SOURCE_AGE_STALE_REASON
        ),
        (
            REQUIRED_RECENCY_MET_REASON
            if seconds_over_effective_sla == ZERO
            else REQUIRED_RECENCY_MISSED_REASON
        ),
        (
            MARKET_RESOLUTION_BUFFER_CLEAR_REASON
            if time_to_resolution_score >= Decimal("0.500000")
            else MARKET_RESOLUTION_NEAR_REASON
        ),
        SOURCE_TIER_REASON[source_tier],
    ]
    if source_age_seconds == ZERO and SOURCE_AGE_FRESH_REASON not in reasons:
        reasons.append(SOURCE_AGE_FRESH_REASON)
    return tuple(reason for reason in ROW_REASON_CODES if reason in reasons)


def _report_status(
    rows: tuple[ResearchPacketLiveSourceRecencySlaGateV2Row, ...],
) -> str:
    if not rows:
        return "blocked"
    if any(row.row_status == "blocked" for row in rows):
        return "blocked"
    if any(row.row_status == "warn" for row in rows):
        return "warn"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchPacketLiveSourceRecencySlaGateV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return (BLOCKED_REASON, GATE_EMPTY_REASON)
    status = _report_status(rows)
    reasons = [{"pass": PASS_REASON, "warn": WARN_REASON, "blocked": BLOCKED_REASON}[status]]
    for reason in (
        SOURCE_AGE_STALE_REASON,
        REQUIRED_RECENCY_MISSED_REASON,
        MARKET_RESOLUTION_NEAR_REASON,
    ):
        if any(reason in row.reason_codes for row in rows):
            reasons.append(reason)
    return tuple(reasons)


def _status_count(
    rows: tuple[ResearchPacketLiveSourceRecencySlaGateV2Row, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.row_status == status))


def _normalize_input_rows(
    source_rows: object,
) -> tuple[ResearchPacketLiveSourceRecencySlaGateV2InputRow, ...]:
    try:
        rows = tuple(source_rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("source_rows must be iterable") from exc
    for row in rows:
        _require_exact_type(
            "source row",
            row,
            ResearchPacketLiveSourceRecencySlaGateV2InputRow,
        )
        _require_phase_flags("source row", row)
    return rows


def _normalize_sla_rows(
    value: object,
) -> tuple[ResearchPacketLiveSourceRecencySlaGateV2Row, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        _require_exact_type("row", row, ResearchPacketLiveSourceRecencySlaGateV2Row)
        _require_phase_flags("row", row)
    return _sort_sla_rows(rows)


def _sort_sla_rows(
    rows: tuple[ResearchPacketLiveSourceRecencySlaGateV2Row, ...],
) -> tuple[ResearchPacketLiveSourceRecencySlaGateV2Row, ...]:
    return tuple(sorted(rows, key=_sla_row_sort_key))


def _sla_row_sort_key(
    row: ResearchPacketLiveSourceRecencySlaGateV2Row,
) -> tuple[int, Decimal, Decimal, str, str, str]:
    return (
        STATUS_WEIGHT[row.row_status],
        row.information_freshness_score,
        -row.seconds_over_effective_sla,
        row.packet_id,
        row.market_id,
        row.source_id,
    )


def _validate_config(config: ResearchPacketLiveSourceRecencySlaGateV2Config) -> None:
    if config.critical_resolution_seconds > config.near_resolution_seconds:
        raise ValueError("critical_resolution_seconds must be <= near_resolution_seconds")
    if config.warn_score_floor > config.pass_score_floor:
        raise ValueError("warn_score_floor must be <= pass_score_floor")
    with localcontext(DECIMAL_CONTEXT):
        weight_sum = (
            config.source_age_weight
            + config.market_time_to_resolution_weight
            + config.source_tier_weight
        ).quantize(SCORE_QUANT)
    if weight_sum != ONE:
        raise ValueError("score weights must sum to 1.000000")


def _validate_unique_source_keys(
    rows: tuple[ResearchPacketLiveSourceRecencySlaGateV2InputRow, ...],
) -> None:
    keys = tuple((row.packet_id, row.market_id, row.source_id) for row in rows)
    if len(set(keys)) != len(keys):
        raise ValueError("source rows must have unique packet, market, and source keys")


def _validate_source_times(
    rows: tuple[ResearchPacketLiveSourceRecencySlaGateV2InputRow, ...],
    generated_at: datetime,
) -> None:
    for row in rows:
        if row.observed_at > generated_at:
            raise ValueError("observed_at must be <= generated_at")
        if row.market_resolution_at < generated_at:
            raise ValueError("market_resolution_at must be >= generated_at")


def _validate_row(row: ResearchPacketLiveSourceRecencySlaGateV2Row) -> None:
    if row.source_tier_score != SOURCE_TIER_SCORES[row.source_tier]:
        raise ValueError("source_tier_score must match source_tier")
    if row.seconds_over_effective_sla != _seconds_over_sla(
        row.source_age_seconds,
        row.effective_recency_sla_seconds,
    ):
        raise ValueError("seconds_over_effective_sla must match age and effective SLA")


def _validate_report(report: ResearchPacketLiveSourceRecencySlaGateV2Report) -> None:
    if report.source_row_count != _decimal_count(len(report.rows)):
        raise ValueError("source_row_count must match rows")
    if report.pass_row_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_row_count must match rows")
    if report.warn_row_count != _status_count(report.rows, "warn"):
        raise ValueError("warn_row_count must match rows")
    if report.blocked_row_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_row_count must match rows")
    if report.issue_row_count != _decimal_count(
        sum(1 for row in report.rows if row.row_status != "pass"),
    ):
        raise ValueError("issue_row_count must match rows")
    if (
        report.pass_row_count + report.warn_row_count + report.blocked_row_count
        != report.source_row_count
    ):
        raise ValueError("status counts must sum to source_row_count")
    if report.issue_ratio != _ratio(report.issue_row_count, report.source_row_count):
        raise ValueError("issue_ratio must match issue counts")
    if report.max_source_age_seconds != max(
        (row.source_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_source_age_seconds must match rows")
    if report.max_seconds_over_effective_sla != max(
        (row.seconds_over_effective_sla for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_seconds_over_effective_sla must match rows")
    if report.min_information_freshness_score != min(
        (row.information_freshness_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("min_information_freshness_score must match rows")
    if report.rows != _sort_sla_rows(report.rows):
        raise ValueError("rows must be sorted")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _duration_seconds(start: datetime, end: datetime) -> Decimal:
    start_utc = _as_utc("start", start)
    end_utc = _as_utc("end", end)
    delta = end_utc - start_utc
    seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    )
    if seconds < ZERO:
        raise ValueError("duration seconds must be nonnegative")
    return seconds.quantize(SECONDS_QUANT)


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
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")
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
    decimal_value = _require_decimal(field_name, value, SCORE_QUANT)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_nonnegative_count(field_name: str, value: object) -> Decimal:
    return _require_nonnegative_decimal(field_name, value, COUNT_QUANT)


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
    return value.quantize(SCORE_QUANT)


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


def _require_phase_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _reject_forbidden_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_forbidden_public_field(field.name)
            _reject_forbidden_public_payload(
                f"{label}.{field.name}",
                getattr(value, field.name),
            )
        return
    if type(value) is dict:
        for key, child in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} public fields must be strings")
            _reject_forbidden_public_field(key)
            _reject_forbidden_public_payload(f"{label}.{key}", child)
        return
    if type(value) in (list, tuple):
        for index, child in enumerate(value):
            _reject_forbidden_public_payload(f"{label}[{index}]", child)
        return
    if type(value) is str:
        lowered_value = value.lower()
        if any(token in lowered_value for token in FORBIDDEN_PUBLIC_TEXT_TOKENS):
            raise ValueError(f"forbidden public value in {label}")


def _reject_forbidden_public_field(field_name: str) -> None:
    lowered_field = field_name.lower()
    if any(token in lowered_field for token in FORBIDDEN_PUBLIC_TEXT_TOKENS):
        raise ValueError(f"forbidden public field {field_name}")


def _report_public_payload_values(
    report: ResearchPacketLiveSourceRecencySlaGateV2Report,
) -> dict[str, object]:
    return {
        field_name: _payload_value(getattr(report, field_name))
        for field_name in REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST
    }


def _payload_value(value: object) -> object:
    if type(value) is Decimal:
        return str(value.quantize(COUNT_QUANT))
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
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


def _report_derived_validation_digest(
    report: ResearchPacketLiveSourceRecencySlaGateV2Report,
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
    report: ResearchPacketLiveSourceRecencySlaGateV2Report,
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
        "warn_row_count",
        "blocked_row_count",
        "issue_row_count",
        "issue_ratio",
        "max_source_age_seconds",
        "max_seconds_over_effective_sla",
        "min_information_freshness_score",
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
    for field_name in ("packet_id", "market_id", "source_id"):
        _require_payload_string(field_name, row_payload[field_name])
    _require_member("source_tier", row_payload["source_tier"], SOURCE_TIERS)
    _require_member("row_status", row_payload["row_status"], ROW_STATUSES)
    _require_payload_string("observed_at", row_payload["observed_at"])
    _require_payload_string("market_resolution_at", row_payload["market_resolution_at"])
    for field_name in (
        "source_age_seconds",
        "market_time_to_resolution_seconds",
        "required_recency_seconds",
        "effective_recency_sla_seconds",
        "seconds_over_effective_sla",
        "source_age_score",
        "market_time_to_resolution_score",
        "source_tier_score",
        "information_freshness_score",
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
    "DEFAULT_RESEARCH_PACKET_LIVE_SOURCE_RECENCY_SLA_GATE_V2_CONFIG_VERSION",
    "PASS_REASON",
    "REPORT_STATUSES",
    "ROW_STATUSES",
    "SOURCE_TIERS",
    "WARN_REASON",
    "ResearchPacketLiveSourceRecencySlaGateV2Config",
    "ResearchPacketLiveSourceRecencySlaGateV2InputRow",
    "ResearchPacketLiveSourceRecencySlaGateV2Report",
    "ResearchPacketLiveSourceRecencySlaGateV2Row",
    "build_research_packet_live_source_recency_sla_gate_v2_report",
    "research_packet_live_source_recency_sla_gate_v2_report_to_payload",
)
