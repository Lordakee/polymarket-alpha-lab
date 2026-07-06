"""Readonly source-latency escalation plan for research packets."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, localcontext
import hashlib
from typing import Any


__all__ = (
    "ResearchPacketSourceLatencyEscalationPlanV2Config",
    "ResearchPacketSourceLatencyEscalationPlanV2Report",
    "ResearchPacketSourceLatencyEscalationPlanV2Row",
    "ResearchPacketSourceLatencyEscalationPlanV2Source",
    "build_research_packet_source_latency_escalation_plan_v2",
    "research_packet_source_latency_escalation_plan_v2_payload",
)


DEFAULT_CONFIG_VERSION = "research-packet-source-latency-escalation-plan-v2"
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
DECIMAL_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
PRIORITY_CAP = Decimal("1.000000")
STALE_WARN_PENALTY = Decimal("0.150000")
STALE_ESCALATE_PENALTY = Decimal("0.350000")
STALE_CRITICAL_PENALTY = Decimal("0.600000")
MISSED_RECHECK_WEIGHT = Decimal("0.050000")
CONFIDENCE_GAP_WEIGHT = Decimal("0.300000")
WATCH_PRIORITY_THRESHOLD = Decimal("0.400000")
ESCALATE_PRIORITY_THRESHOLD = Decimal("0.650000")
CRITICAL_PRIORITY_THRESHOLD = Decimal("0.850000")

PUBLIC_ROW_PAYLOAD_FIELDS_WITHOUT_DIGEST = (
    "config_version",
    "packet_id",
    "source_id",
    "source_family",
    "observed_at",
    "generated_at",
    "source_age_seconds",
    "base_priority_score",
    "source_confidence_score",
    "missed_recheck_count",
    "stale_penalty_score",
    "escalation_priority_score",
    "escalation_tier",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
PUBLIC_REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST = (
    "config_version",
    "generated_at",
    "row_count",
    "watch_count",
    "escalate_count",
    "critical_count",
    "max_escalation_priority_score",
    "rows",
    "paper_only",
    "report_only",
    "readonly",
)
PUBLIC_REPORT_PAYLOAD_FIELDS = (
    *PUBLIC_REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    DERIVED_VALIDATION_DIGEST_FIELD,
)
ESCALATION_TIERS = ("normal", "watch", "escalate", "critical")
SAFE_ROW_REASON_CODES = (
    "source_latency_fresh",
    "source_latency_warn",
    "source_latency_stale",
    "source_latency_critical",
    "low_source_confidence",
    "missed_recheck_history",
    "latency_priority_watch",
    "latency_priority_escalate",
    "latency_priority_critical",
)
UNSAFE_PUBLIC_TERMS = (
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


@dataclass(frozen=True)
class ResearchPacketSourceLatencyEscalationPlanV2Config:
    config_version: str = DEFAULT_CONFIG_VERSION
    warn_stale_after_seconds: Decimal = Decimal("600.000000")
    escalate_stale_after_seconds: Decimal = Decimal("1800.000000")
    critical_stale_after_seconds: Decimal = Decimal("3600.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketSourceLatencyEscalationPlanV2Config:
            raise TypeError(
                "ResearchPacketSourceLatencyEscalationPlanV2Config does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceLatencyEscalationPlanV2Config:
            raise ValueError(
                "config must be exactly ResearchPacketSourceLatencyEscalationPlanV2Config",
            )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "warn_stale_after_seconds",
            "escalate_stale_after_seconds",
            "critical_stale_after_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.warn_stale_after_seconds >= self.escalate_stale_after_seconds:
            raise ValueError(
                "warn_stale_after_seconds must be less than escalate_stale_after_seconds",
            )
        if self.escalate_stale_after_seconds >= self.critical_stale_after_seconds:
            raise ValueError(
                "escalate_stale_after_seconds must be less than critical_stale_after_seconds",
            )
        _reject_unsafe_public_payload("config", self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchPacketSourceLatencyEscalationPlanV2Source:
    packet_id: str
    source_id: str
    source_family: str
    observed_at: datetime
    base_priority_score: Decimal
    source_confidence_score: Decimal
    missed_recheck_count: Decimal = Decimal("0.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketSourceLatencyEscalationPlanV2Source:
            raise TypeError(
                "ResearchPacketSourceLatencyEscalationPlanV2Source does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceLatencyEscalationPlanV2Source:
            raise ValueError(
                "source must be exactly ResearchPacketSourceLatencyEscalationPlanV2Source",
            )
        for field_name in ("packet_id", "source_id", "source_family"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "base_priority_score",
            _normalize_probability_decimal(
                "base_priority_score",
                self.base_priority_score,
            ),
        )
        object.__setattr__(
            self,
            "source_confidence_score",
            _normalize_probability_decimal(
                "source_confidence_score",
                self.source_confidence_score,
            ),
        )
        object.__setattr__(
            self,
            "missed_recheck_count",
            _normalize_nonnegative_whole_decimal(
                "missed_recheck_count",
                self.missed_recheck_count,
            ),
        )
        _reject_unsafe_public_payload("source", self)
        _require_hard_flags("source", self)


@dataclass(frozen=True)
class ResearchPacketSourceLatencyEscalationPlanV2Row:
    config_version: str
    packet_id: str
    source_id: str
    source_family: str
    observed_at: datetime
    generated_at: datetime
    source_age_seconds: Decimal
    base_priority_score: Decimal
    source_confidence_score: Decimal
    missed_recheck_count: Decimal
    stale_penalty_score: Decimal
    escalation_priority_score: Decimal
    escalation_tier: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketSourceLatencyEscalationPlanV2Row:
            raise TypeError(
                "ResearchPacketSourceLatencyEscalationPlanV2Row does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceLatencyEscalationPlanV2Row:
            raise ValueError("row must be exactly ResearchPacketSourceLatencyEscalationPlanV2Row")
        for field_name in ("config_version", "packet_id", "source_id", "source_family"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        if self.generated_at < self.observed_at:
            raise ValueError("generated_at must be >= observed_at")
        for field_name in (
            "source_age_seconds",
            "base_priority_score",
            "source_confidence_score",
            "missed_recheck_count",
            "stale_penalty_score",
            "escalation_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_probability_upper_bound(
            "base_priority_score",
            self.base_priority_score,
        )
        _require_probability_upper_bound(
            "source_confidence_score",
            self.source_confidence_score,
        )
        _require_probability_upper_bound("stale_penalty_score", self.stale_penalty_score)
        _require_probability_upper_bound(
            "escalation_priority_score",
            self.escalation_priority_score,
        )
        object.__setattr__(
            self,
            "missed_recheck_count",
            _normalize_nonnegative_whole_decimal(
                "missed_recheck_count",
                self.missed_recheck_count,
            ),
        )
        _require_member("escalation_tier", self.escalation_tier, ESCALATION_TIERS)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _reject_unsafe_public_payload("row", self)
        _require_hard_flags("row", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _row_derived_validation_digest(self),
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
        _validate_row_derived_validation_digest(self)


@dataclass(frozen=True)
class ResearchPacketSourceLatencyEscalationPlanV2Report:
    config_version: str
    generated_at: datetime
    rows: tuple[ResearchPacketSourceLatencyEscalationPlanV2Row, ...]
    row_count: Decimal
    watch_count: Decimal
    escalate_count: Decimal
    critical_count: Decimal
    max_escalation_priority_score: Decimal
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketSourceLatencyEscalationPlanV2Report:
            raise TypeError(
                "ResearchPacketSourceLatencyEscalationPlanV2Report does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceLatencyEscalationPlanV2Report:
            raise ValueError(
                "report must be exactly ResearchPacketSourceLatencyEscalationPlanV2Report",
            )
        _require_public_string("config_version", self.config_version)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        for field_name in (
            "row_count",
            "watch_count",
            "escalate_count",
            "critical_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_escalation_priority_score",
            _normalize_nonnegative_decimal(
                "max_escalation_priority_score",
                self.max_escalation_priority_score,
            ),
        )
        _require_probability_upper_bound(
            "max_escalation_priority_score",
            self.max_escalation_priority_score,
        )
        _reject_unsafe_public_payload("report", self)
        _require_hard_flags("report", self)
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
        _validate_report_consistency(self)


def build_research_packet_source_latency_escalation_plan_v2(
    sources: tuple[ResearchPacketSourceLatencyEscalationPlanV2Source, ...],
    *,
    generated_at: datetime,
    config: ResearchPacketSourceLatencyEscalationPlanV2Config,
) -> ResearchPacketSourceLatencyEscalationPlanV2Report:
    _require_exact_type("config", config, ResearchPacketSourceLatencyEscalationPlanV2Config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    if type(sources) is not tuple:
        raise ValueError("sources must be a tuple")
    rows = tuple(
        _build_row(source, generated_at=generated_at_utc, config=config)
        for source in sources
    )
    sorted_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                row.escalation_priority_score,
                row.source_age_seconds,
                row.source_id,
            ),
            reverse=True,
        ),
    )
    return ResearchPacketSourceLatencyEscalationPlanV2Report(
        config_version=config.config_version,
        generated_at=generated_at_utc,
        rows=sorted_rows,
        row_count=_count(len(sorted_rows)),
        watch_count=_count(sum(1 for row in sorted_rows if row.escalation_tier == "watch")),
        escalate_count=_count(
            sum(1 for row in sorted_rows if row.escalation_tier == "escalate"),
        ),
        critical_count=_count(
            sum(1 for row in sorted_rows if row.escalation_tier == "critical"),
        ),
        max_escalation_priority_score=_max_priority(sorted_rows),
    )


def research_packet_source_latency_escalation_plan_v2_payload(
    report: ResearchPacketSourceLatencyEscalationPlanV2Report | dict[str, object],
) -> dict[str, object]:
    if type(report) is ResearchPacketSourceLatencyEscalationPlanV2Report:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        _validate_report_derived_validation_digest(report)
        payload = _report_public_payload_values(report)
        payload[DERIVED_VALIDATION_DIGEST_FIELD] = report.derived_validation_digest
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _require_public_report_payload_fields(report)
        _validate_public_report_payload(report)
        return dict(report)
    raise ValueError("report must be a ResearchPacketSourceLatencyEscalationPlanV2Report")


def _build_row(
    source: ResearchPacketSourceLatencyEscalationPlanV2Source,
    *,
    generated_at: datetime,
    config: ResearchPacketSourceLatencyEscalationPlanV2Config,
) -> ResearchPacketSourceLatencyEscalationPlanV2Row:
    _require_exact_type("source", source, ResearchPacketSourceLatencyEscalationPlanV2Source)
    _require_hard_flags("source", source)
    _reject_unsafe_public_payload("source", source)
    if generated_at < source.observed_at:
        raise ValueError("generated_at must be >= observed_at")
    source_age_seconds = _duration_seconds(source.observed_at, generated_at)
    stale_penalty_score = _stale_penalty_score(source_age_seconds, config)
    escalation_priority_score = _priority_score(source, stale_penalty_score)
    escalation_tier = _escalation_tier(escalation_priority_score)
    return ResearchPacketSourceLatencyEscalationPlanV2Row(
        config_version=config.config_version,
        packet_id=source.packet_id,
        source_id=source.source_id,
        source_family=source.source_family,
        observed_at=source.observed_at,
        generated_at=generated_at,
        source_age_seconds=source_age_seconds,
        base_priority_score=source.base_priority_score,
        source_confidence_score=source.source_confidence_score,
        missed_recheck_count=source.missed_recheck_count,
        stale_penalty_score=stale_penalty_score,
        escalation_priority_score=escalation_priority_score,
        escalation_tier=escalation_tier,
        reason_codes=_row_reason_codes(
            source,
            stale_penalty_score=stale_penalty_score,
            escalation_tier=escalation_tier,
        ),
    )


def _stale_penalty_score(
    source_age_seconds: Decimal,
    config: ResearchPacketSourceLatencyEscalationPlanV2Config,
) -> Decimal:
    if source_age_seconds >= config.critical_stale_after_seconds:
        return STALE_CRITICAL_PENALTY
    if source_age_seconds >= config.escalate_stale_after_seconds:
        return STALE_ESCALATE_PENALTY
    if source_age_seconds >= config.warn_stale_after_seconds:
        return STALE_WARN_PENALTY
    return ZERO


def _priority_score(
    source: ResearchPacketSourceLatencyEscalationPlanV2Source,
    stale_penalty_score: Decimal,
) -> Decimal:
    with localcontext() as context:
        context.prec = 28
        confidence_gap = ONE - source.source_confidence_score
        score = (
            source.base_priority_score
            + stale_penalty_score
            + (source.missed_recheck_count * MISSED_RECHECK_WEIGHT)
            + (confidence_gap * CONFIDENCE_GAP_WEIGHT)
        )
    return _cap_priority(score)


def _escalation_tier(escalation_priority_score: Decimal) -> str:
    if escalation_priority_score >= CRITICAL_PRIORITY_THRESHOLD:
        return "critical"
    if escalation_priority_score >= ESCALATE_PRIORITY_THRESHOLD:
        return "escalate"
    if escalation_priority_score >= WATCH_PRIORITY_THRESHOLD:
        return "watch"
    return "normal"


def _row_reason_codes(
    source: ResearchPacketSourceLatencyEscalationPlanV2Source,
    *,
    stale_penalty_score: Decimal,
    escalation_tier: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if stale_penalty_score == STALE_CRITICAL_PENALTY:
        reason_codes.append("source_latency_critical")
    elif stale_penalty_score == STALE_ESCALATE_PENALTY:
        reason_codes.append("source_latency_stale")
    elif stale_penalty_score == STALE_WARN_PENALTY:
        reason_codes.append("source_latency_warn")
    else:
        reason_codes.append("source_latency_fresh")
    if source.source_confidence_score < Decimal("0.500000"):
        reason_codes.append("low_source_confidence")
    if source.missed_recheck_count > ZERO:
        reason_codes.append("missed_recheck_history")
    if escalation_tier != "normal":
        reason_codes.append(f"latency_priority_{escalation_tier}")
    return tuple(dict.fromkeys(reason_codes))


def _report_public_payload_values(
    report: ResearchPacketSourceLatencyEscalationPlanV2Report,
) -> dict[str, object]:
    return {
        "config_version": report.config_version,
        "generated_at": _datetime_payload(report.generated_at),
        "row_count": _decimal_payload(report.row_count),
        "watch_count": _decimal_payload(report.watch_count),
        "escalate_count": _decimal_payload(report.escalate_count),
        "critical_count": _decimal_payload(report.critical_count),
        "max_escalation_priority_score": _decimal_payload(
            report.max_escalation_priority_score,
        ),
        "rows": [_row_public_payload_values(row) for row in report.rows],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_public_payload_values(
    row: ResearchPacketSourceLatencyEscalationPlanV2Row,
) -> dict[str, object]:
    _validate_row_derived_validation_digest(row)
    payload = _row_public_payload_values_without_digest(row)
    payload[DERIVED_VALIDATION_DIGEST_FIELD] = row.derived_validation_digest
    return payload


def _row_public_payload_values_without_digest(
    row: ResearchPacketSourceLatencyEscalationPlanV2Row,
) -> dict[str, object]:
    return {
        "config_version": row.config_version,
        "packet_id": row.packet_id,
        "source_id": row.source_id,
        "source_family": row.source_family,
        "observed_at": _datetime_payload(row.observed_at),
        "generated_at": _datetime_payload(row.generated_at),
        "source_age_seconds": _decimal_payload(row.source_age_seconds),
        "base_priority_score": _decimal_payload(row.base_priority_score),
        "source_confidence_score": _decimal_payload(row.source_confidence_score),
        "missed_recheck_count": _decimal_payload(row.missed_recheck_count),
        "stale_penalty_score": _decimal_payload(row.stale_penalty_score),
        "escalation_priority_score": _decimal_payload(row.escalation_priority_score),
        "escalation_tier": row.escalation_tier,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_derived_validation_digest(
    row: ResearchPacketSourceLatencyEscalationPlanV2Row,
) -> str:
    return _derived_validation_digest(
        "research_packet_source_latency_escalation_plan_v2_row",
        _row_public_payload_values_without_digest(row),
        PUBLIC_ROW_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    )


def _report_derived_validation_digest(
    report: ResearchPacketSourceLatencyEscalationPlanV2Report,
) -> str:
    return _derived_validation_digest(
        "research_packet_source_latency_escalation_plan_v2_report",
        _report_public_payload_values(report),
        PUBLIC_REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    )


def _validate_row_derived_validation_digest(
    row: ResearchPacketSourceLatencyEscalationPlanV2Row,
) -> None:
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest must match row fields")


def _validate_report_derived_validation_digest(
    report: ResearchPacketSourceLatencyEscalationPlanV2Report,
) -> None:
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _derived_validation_digest(
    label: str,
    payload: dict[str, object],
    field_names: tuple[str, ...],
) -> str:
    values = tuple(
        f"{field_name}={_digest_payload_value(payload[field_name])}"
        for field_name in field_names
    )
    return hashlib.sha256((f"{label}|" + "|".join(values)).encode("utf-8")).hexdigest()


def _digest_payload_value(value: object) -> str:
    if isinstance(value, dict):
        return "{" + ",".join(
            f"{key}:{_digest_payload_value(value[key])}" for key in sorted(value)
        ) + "}"
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(_digest_payload_value(item) for item in value) + "]"
    return str(value)


def _require_public_report_payload_fields(payload: dict[str, object]) -> None:
    for field_name in PUBLIC_REPORT_PAYLOAD_FIELDS:
        if field_name not in payload:
            raise ValueError(f"{field_name} is required")
    extra_fields = sorted(set(payload) - set(PUBLIC_REPORT_PAYLOAD_FIELDS))
    if extra_fields:
        raise ValueError(f"unexpected public payload field: {extra_fields[0]}")


def _require_public_row_payload_fields(payload: dict[str, object]) -> None:
    for field_name in (*PUBLIC_ROW_PAYLOAD_FIELDS_WITHOUT_DIGEST, DERIVED_VALIDATION_DIGEST_FIELD):
        if field_name not in payload:
            raise ValueError(f"{field_name} is required")
    extra_fields = sorted(
        set(payload)
        - set((*PUBLIC_ROW_PAYLOAD_FIELDS_WITHOUT_DIGEST, DERIVED_VALIDATION_DIGEST_FIELD)),
    )
    if extra_fields:
        raise ValueError(f"unexpected public row payload field: {extra_fields[0]}")


def _validate_public_report_payload(payload: dict[str, object]) -> None:
    _require_public_string("config_version", payload["config_version"])
    _require_datetime_payload_string("generated_at", payload["generated_at"])
    for field_name in ("row_count", "watch_count", "escalate_count", "critical_count"):
        _require_decimal_payload_string(field_name, payload[field_name], whole=True)
    _require_decimal_payload_string(
        "max_escalation_priority_score",
        payload["max_escalation_priority_score"],
        probability=True,
    )
    rows_value = payload["rows"]
    if type(rows_value) is not list:
        raise ValueError("rows must be a list")
    for row_payload in rows_value:
        if type(row_payload) is not dict:
            raise ValueError("rows must contain dictionaries")
        _reject_unsafe_public_payload("row payload", row_payload)
        _require_public_row_payload_fields(row_payload)
        _validate_public_row_payload(row_payload)
    _require_hard_flags("payload", _DictFlags(payload))
    _normalize_sha256(
        DERIVED_VALIDATION_DIGEST_FIELD,
        payload[DERIVED_VALIDATION_DIGEST_FIELD],
    )
    if payload[DERIVED_VALIDATION_DIGEST_FIELD] != _derived_validation_digest(
        "research_packet_source_latency_escalation_plan_v2_report",
        payload,
        PUBLIC_REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    ):
        raise ValueError("derived_validation_digest must match payload fields")


def _validate_public_row_payload(payload: dict[str, object]) -> None:
    for field_name in ("config_version", "packet_id", "source_id", "source_family"):
        _require_public_string(field_name, payload[field_name])
    for field_name in ("observed_at", "generated_at"):
        _require_datetime_payload_string(field_name, payload[field_name])
    for field_name in (
        "source_age_seconds",
        "base_priority_score",
        "source_confidence_score",
        "missed_recheck_count",
        "stale_penalty_score",
        "escalation_priority_score",
    ):
        _require_decimal_payload_string(
            field_name,
            payload[field_name],
            probability=field_name
            in {
                "base_priority_score",
                "source_confidence_score",
                "stale_penalty_score",
                "escalation_priority_score",
            },
            whole=field_name == "missed_recheck_count",
        )
    _require_member("escalation_tier", payload["escalation_tier"], ESCALATION_TIERS)
    _normalize_public_reason_codes("reason_codes", payload["reason_codes"])
    _require_hard_flags("row payload", _DictFlags(payload))
    _normalize_sha256(
        DERIVED_VALIDATION_DIGEST_FIELD,
        payload[DERIVED_VALIDATION_DIGEST_FIELD],
    )
    if payload[DERIVED_VALIDATION_DIGEST_FIELD] != _derived_validation_digest(
        "research_packet_source_latency_escalation_plan_v2_row",
        payload,
        PUBLIC_ROW_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    ):
        raise ValueError("derived_validation_digest must match row payload fields")


def _validate_report_consistency(
    report: ResearchPacketSourceLatencyEscalationPlanV2Report,
) -> None:
    if report.row_count != _count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.watch_count != _count(
        sum(1 for row in report.rows if row.escalation_tier == "watch"),
    ):
        raise ValueError("watch_count must match rows")
    if report.escalate_count != _count(
        sum(1 for row in report.rows if row.escalation_tier == "escalate"),
    ):
        raise ValueError("escalate_count must match rows")
    if report.critical_count != _count(
        sum(1 for row in report.rows if row.escalation_tier == "critical"),
    ):
        raise ValueError("critical_count must match rows")
    if report.max_escalation_priority_score != _max_priority(report.rows):
        raise ValueError("max_escalation_priority_score must match rows")
    for row in report.rows:
        if row.config_version != report.config_version:
            raise ValueError("row config_version must match report config_version")
        if row.generated_at != report.generated_at:
            raise ValueError("row generated_at must match report generated_at")


def _normalize_rows(value: object) -> tuple[ResearchPacketSourceLatencyEscalationPlanV2Row, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows: list[ResearchPacketSourceLatencyEscalationPlanV2Row] = []
    for row in value:
        _require_exact_type("row", row, ResearchPacketSourceLatencyEscalationPlanV2Row)
        _require_hard_flags("row", row)
        _validate_row_derived_validation_digest(row)
        rows.append(row)
    return tuple(rows)


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    reason_codes: list[str] = []
    for reason_code in value:
        _require_public_string(field_name, reason_code)
        if reason_code not in SAFE_ROW_REASON_CODES:
            raise ValueError(f"{field_name} must be known")
        reason_codes.append(reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    return tuple(reason_codes)


def _normalize_public_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    reason_codes: list[str] = []
    for reason_code in value:
        _require_public_string(field_name, reason_code)
        if reason_code not in SAFE_ROW_REASON_CODES:
            raise ValueError(f"{field_name} must be known")
        reason_codes.append(reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    return tuple(reason_codes)


def _max_priority(
    rows: tuple[ResearchPacketSourceLatencyEscalationPlanV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.escalation_priority_score for row in rows)


def _duration_seconds(start: datetime, end: datetime) -> Decimal:
    start_utc = _as_utc("start", start)
    end_utc = _as_utc("end", end)
    delta = end_utc - start_utc
    seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    if seconds < ZERO:
        raise ValueError("duration seconds must be nonnegative")
    return _quantize_decimal(seconds)


def _count(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _cap_priority(value: Decimal) -> Decimal:
    if value > PRIORITY_CAP:
        return PRIORITY_CAP
    return _quantize_decimal(value)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    _require_probability_upper_bound(field_name, decimal_value)
    return decimal_value


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    decimal_value = _quantize_decimal(value)
    if decimal_value != value:
        raise ValueError(f"{field_name} must use the required decimal precision")
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return decimal_value


def _require_probability_upper_bound(field_name: str, value: Decimal) -> None:
    if value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")


def _quantize_decimal(value: Decimal) -> Decimal:
    return value.quantize(DECIMAL_QUANTUM)


def _decimal_payload(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("payload decimal must be a Decimal")
    if not value.is_finite():
        raise ValueError("payload decimal must be finite")
    return str(value)


def _datetime_payload(value: datetime) -> str:
    return _as_utc("datetime", value).isoformat()


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_datetime_payload_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime string") from exc
    _as_utc(field_name, parsed)


def _require_decimal_payload_string(
    field_name: str,
    value: object,
    *,
    probability: bool = False,
    whole: bool = False,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    decimal_value = _normalize_nonnegative_decimal(field_name, decimal_value)
    if probability:
        _require_probability_upper_bound(field_name, decimal_value)
    if whole and decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-count Decimal string")
    if str(decimal_value) != value:
        raise ValueError(f"{field_name} must use canonical Decimal string formatting")
    return decimal_value


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be stripped")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")
    _reject_unsafe_text(field_name, value)


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    for key in _iter_public_keys(payload):
        _reject_unsafe_text(f"{label}.{key}", key)
    for value in _iter_public_string_values(payload):
        _reject_unsafe_text(label, value)


def _reject_unsafe_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(term in lowered for term in UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} contains unsafe text")


def _iter_public_keys(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_public_keys(asdict(value))
    if type(value) is dict:
        keys: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            keys.append(key)
            keys.extend(_iter_public_keys(item))
        return tuple(keys)
    if isinstance(value, (list, tuple)):
        keys = []
        for item in value:
            keys.extend(_iter_public_keys(item))
        return tuple(keys)
    return ()


def _iter_public_string_values(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_public_string_values(asdict(value))
    if type(value) is dict:
        values: list[str] = []
        for item in value.values():
            values.extend(_iter_public_string_values(item))
        return tuple(values)
    if isinstance(value, (list, tuple)):
        values = []
        for item in value:
            values.extend(_iter_public_string_values(item))
        return tuple(values)
    if type(value) is str:
        return (value,)
    return ()


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 string")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 string")
    return value


class _DictFlags:
    def __init__(self, value: dict[str, object]) -> None:
        self.value = value

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")
