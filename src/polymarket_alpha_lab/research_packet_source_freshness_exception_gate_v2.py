"""Phase 1 paper-only gate for stale research-packet source evidence."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
import hashlib
import json
from typing import Any


DEFAULT_RESEARCH_PACKET_SOURCE_FRESHNESS_EXCEPTION_GATE_V2_CONFIG_VERSION = (
    "research-packet-source-freshness-exception-gate-v2-v0"
)

DECIMAL_CONTEXT = Context(prec=64)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")

GATE_STATUSES = ("pass", "blocked", "empty")
SOURCE_FRESHNESS_STATUSES = ("fresh", "stale_tolerated", "stale_blocked")

EMPTY_REASON = "source_freshness_exception_gate_empty"
FRESH_REASON = "source_evidence_fresh"
STALE_TOLERATED_REASON = "stale_evidence_tolerated"
EVENT_VELOCITY_TOO_HIGH_REASON = "event_velocity_too_high"
OFFICIAL_SOURCE_LAG_EXCESSIVE_REASON = "official_source_lag_excessive"
CONTRADICTION_SEVERITY_EXCESSIVE_REASON = "contradiction_severity_excessive"
PROBABILITY_MOVEMENT_EXCESSIVE_REASON = "probability_movement_excessive"
RESOLUTION_HORIZON_TOO_SHORT_REASON = "resolution_horizon_too_short"
SOURCE_FAMILY_RELIABILITY_LOW_REASON = "source_family_reliability_low"

ROW_REASON_CODES = (
    EVENT_VELOCITY_TOO_HIGH_REASON,
    OFFICIAL_SOURCE_LAG_EXCESSIVE_REASON,
    CONTRADICTION_SEVERITY_EXCESSIVE_REASON,
    PROBABILITY_MOVEMENT_EXCESSIVE_REASON,
    RESOLUTION_HORIZON_TOO_SHORT_REASON,
    SOURCE_FAMILY_RELIABILITY_LOW_REASON,
    STALE_TOLERATED_REASON,
    FRESH_REASON,
)
REPORT_REASON_CODES = (EMPTY_REASON, *ROW_REASON_CODES)

PUBLIC_PAYLOAD_FIELDS_WITHOUT_DIGEST = (
    "generated_at",
    "config_version",
    "gate_status",
    "observation_count",
    "fresh_source_count",
    "stale_source_count",
    "tolerated_stale_source_count",
    "blocked_stale_source_count",
    "exception_ratio",
    "tolerated_stale_source_ratio",
    "max_source_age_seconds",
    "rows",
    "reason_code_counts",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
PUBLIC_PAYLOAD_FIELDS = (
    *PUBLIC_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    DERIVED_VALIDATION_DIGEST_FIELD,
)

UNSAFE_PUBLIC_KEY_VALUE_TOKENS = (
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
class ResearchPacketSourceFreshnessExceptionGateV2Config:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_SOURCE_FRESHNESS_EXCEPTION_GATE_V2_CONFIG_VERSION
    )
    stale_source_age_seconds: Decimal = Decimal("86400.000000")
    max_event_velocity_for_exception: Decimal = Decimal("0.600000")
    max_official_source_lag_seconds: Decimal = Decimal("7200.000000")
    max_contradiction_severity_for_exception: Decimal = Decimal("0.200000")
    max_probability_movement_for_exception: Decimal = Decimal("0.030000")
    minimum_resolution_horizon_seconds: Decimal = Decimal("86400.000000")
    minimum_source_family_reliability: Decimal = Decimal("0.800000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketSourceFreshnessExceptionGateV2Config:
            raise TypeError(
                "ResearchPacketSourceFreshnessExceptionGateV2Config does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceFreshnessExceptionGateV2Config:
            raise ValueError(
                "config must be exactly "
                "ResearchPacketSourceFreshnessExceptionGateV2Config",
            )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_SOURCE_FRESHNESS_EXCEPTION_GATE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported version")
        for field_name in (
            "stale_source_age_seconds",
            "max_official_source_lag_seconds",
            "minimum_resolution_horizon_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_seconds(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_event_velocity_for_exception",
            "max_contradiction_severity_for_exception",
            "max_probability_movement_for_exception",
            "minimum_source_family_reliability",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _reject_unsafe_public_payload("config", self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchPacketSourceFreshnessExceptionGateV2Observation:
    packet_id: str
    market_id: str
    source_family: str
    source_observed_at: datetime
    event_velocity: Decimal
    official_source_lag_seconds: Decimal
    contradiction_severity: Decimal
    probability_movement: Decimal
    resolution_horizon_seconds: Decimal
    source_family_reliability: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketSourceFreshnessExceptionGateV2Observation:
            raise TypeError(
                "ResearchPacketSourceFreshnessExceptionGateV2Observation does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceFreshnessExceptionGateV2Observation:
            raise ValueError(
                "observation must be exactly "
                "ResearchPacketSourceFreshnessExceptionGateV2Observation",
            )
        for field_name in ("packet_id", "market_id", "source_family"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        for field_name in (
            "event_velocity",
            "contradiction_severity",
            "probability_movement",
            "source_family_reliability",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("official_source_lag_seconds", "resolution_horizon_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_seconds(field_name, getattr(self, field_name)),
            )
        _reject_unsafe_public_payload("observation", self)
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchPacketSourceFreshnessExceptionGateV2Row:
    packet_id: str
    market_id: str
    source_family: str
    source_observed_at: datetime
    source_age_seconds: Decimal
    event_velocity: Decimal
    official_source_lag_seconds: Decimal
    contradiction_severity: Decimal
    probability_movement: Decimal
    resolution_horizon_seconds: Decimal
    source_family_reliability: Decimal
    source_freshness_status: str
    gate_status: str
    stale_source_tolerated: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketSourceFreshnessExceptionGateV2Row:
            raise TypeError(
                "ResearchPacketSourceFreshnessExceptionGateV2Row does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceFreshnessExceptionGateV2Row:
            raise ValueError(
                "row must be exactly ResearchPacketSourceFreshnessExceptionGateV2Row",
            )
        for field_name in ("packet_id", "market_id", "source_family"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "source_observed_at",
            _as_utc("source_observed_at", self.source_observed_at),
        )
        for field_name in (
            "source_age_seconds",
            "official_source_lag_seconds",
            "resolution_horizon_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_seconds(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "event_velocity",
            "contradiction_severity",
            "probability_movement",
            "source_family_reliability",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_member(
            "source_freshness_status",
            self.source_freshness_status,
            SOURCE_FRESHNESS_STATUSES,
        )
        _require_member("gate_status", self.gate_status, ("pass", "blocked"))
        if type(self.stale_source_tolerated) is not bool:
            raise ValueError("stale_source_tolerated must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _reject_unsafe_public_payload("row", self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchPacketSourceFreshnessExceptionGateV2ReasonCodeCount:
    reason_code: str
    count: Decimal
    observation_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketSourceFreshnessExceptionGateV2ReasonCodeCount:
            raise TypeError(
                "ResearchPacketSourceFreshnessExceptionGateV2ReasonCodeCount does "
                "not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceFreshnessExceptionGateV2ReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchPacketSourceFreshnessExceptionGateV2ReasonCodeCount",
            )
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODES)
        object.__setattr__(self, "count", _require_count("count", self.count))
        object.__setattr__(
            self,
            "observation_ratio",
            _require_ratio_decimal("observation_ratio", self.observation_ratio),
        )
        _reject_unsafe_public_payload("reason_code_count", self)
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchPacketSourceFreshnessExceptionGateV2Report:
    generated_at: datetime
    config_version: str
    gate_status: str
    observation_count: Decimal
    fresh_source_count: Decimal
    stale_source_count: Decimal
    tolerated_stale_source_count: Decimal
    blocked_stale_source_count: Decimal
    exception_ratio: Decimal
    tolerated_stale_source_ratio: Decimal
    max_source_age_seconds: Decimal
    rows: tuple[ResearchPacketSourceFreshnessExceptionGateV2Row, ...]
    reason_code_counts: tuple[
        ResearchPacketSourceFreshnessExceptionGateV2ReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketSourceFreshnessExceptionGateV2Report:
            raise TypeError(
                "ResearchPacketSourceFreshnessExceptionGateV2Report does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceFreshnessExceptionGateV2Report:
            raise ValueError(
                "report must be exactly ResearchPacketSourceFreshnessExceptionGateV2Report",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_member("gate_status", self.gate_status, GATE_STATUSES)
        for field_name in (
            "observation_count",
            "fresh_source_count",
            "stale_source_count",
            "tolerated_stale_source_count",
            "blocked_stale_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("exception_ratio", "tolerated_stale_source_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_source_age_seconds",
            _require_seconds("max_source_age_seconds", self.max_source_age_seconds),
        )
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


def build_research_packet_source_freshness_exception_gate_v2_report(
    observations: object,
    *,
    generated_at: datetime,
    config: ResearchPacketSourceFreshnessExceptionGateV2Config | None = None,
) -> ResearchPacketSourceFreshnessExceptionGateV2Report:
    cfg = config or ResearchPacketSourceFreshnessExceptionGateV2Config()
    if type(cfg) is not ResearchPacketSourceFreshnessExceptionGateV2Config:
        raise ValueError(
            "config must be exactly "
            "ResearchPacketSourceFreshnessExceptionGateV2Config",
        )
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (
                _row_for_observation(
                    observation,
                    generated_at=generated_at_utc,
                    config=cfg,
                )
                for observation in _normalize_observations(
                    observations,
                    generated_at=generated_at_utc,
                )
            ),
            key=_row_sort_key,
        ),
    )
    stale_source_count = sum(
        1 for row in rows if row.source_freshness_status != "fresh"
    )
    tolerated_stale_source_count = sum(
        1 for row in rows if row.source_freshness_status == "stale_tolerated"
    )
    blocked_stale_source_count = sum(
        1 for row in rows if row.source_freshness_status == "stale_blocked"
    )
    fresh_source_count = sum(1 for row in rows if row.source_freshness_status == "fresh")
    return ResearchPacketSourceFreshnessExceptionGateV2Report(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        gate_status=_report_gate_status(rows),
        observation_count=_count(len(rows)),
        fresh_source_count=_count(fresh_source_count),
        stale_source_count=_count(stale_source_count),
        tolerated_stale_source_count=_count(tolerated_stale_source_count),
        blocked_stale_source_count=_count(blocked_stale_source_count),
        exception_ratio=_ratio(_count(blocked_stale_source_count), _count(len(rows))),
        tolerated_stale_source_ratio=_ratio(
            _count(tolerated_stale_source_count),
            _count(stale_source_count),
        ),
        max_source_age_seconds=_max_source_age_seconds(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows),
        reason_codes=_report_reason_codes(rows),
    )


def research_packet_source_freshness_exception_gate_v2_payload(
    report: ResearchPacketSourceFreshnessExceptionGateV2Report | dict[str, object],
) -> dict[str, object]:
    if type(report) is ResearchPacketSourceFreshnessExceptionGateV2Report:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        _validate_report_derived_validation_digest(report)
        payload = _json_ready(asdict(report))
        if not isinstance(payload, dict):
            raise ValueError("report payload must be a JSON object")
        _reject_unsafe_public_payload("payload", payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _require_public_payload_fields(report)
        _validate_public_payload(report)
        return dict(report)
    raise ValueError(
        "report must be ResearchPacketSourceFreshnessExceptionGateV2Report",
    )


def _row_for_observation(
    observation: ResearchPacketSourceFreshnessExceptionGateV2Observation,
    *,
    generated_at: datetime,
    config: ResearchPacketSourceFreshnessExceptionGateV2Config,
) -> ResearchPacketSourceFreshnessExceptionGateV2Row:
    source_age_seconds = _age_seconds(generated_at, observation.source_observed_at)
    reason_codes, source_freshness_status, gate_status, stale_source_tolerated = (
        _row_gate_fields(
            source_age_seconds=source_age_seconds,
            observation=observation,
            config=config,
        )
    )
    return ResearchPacketSourceFreshnessExceptionGateV2Row(
        packet_id=observation.packet_id,
        market_id=observation.market_id,
        source_family=observation.source_family,
        source_observed_at=observation.source_observed_at,
        source_age_seconds=source_age_seconds,
        event_velocity=observation.event_velocity,
        official_source_lag_seconds=observation.official_source_lag_seconds,
        contradiction_severity=observation.contradiction_severity,
        probability_movement=observation.probability_movement,
        resolution_horizon_seconds=observation.resolution_horizon_seconds,
        source_family_reliability=observation.source_family_reliability,
        source_freshness_status=source_freshness_status,
        gate_status=gate_status,
        stale_source_tolerated=stale_source_tolerated,
        reason_codes=reason_codes,
    )


def _row_gate_fields(
    *,
    source_age_seconds: Decimal,
    observation: ResearchPacketSourceFreshnessExceptionGateV2Observation,
    config: ResearchPacketSourceFreshnessExceptionGateV2Config,
) -> tuple[tuple[str, ...], str, str, bool]:
    if source_age_seconds <= config.stale_source_age_seconds:
        return (FRESH_REASON,), "fresh", "pass", False
    blockers: list[str] = []
    if observation.event_velocity > config.max_event_velocity_for_exception:
        blockers.append(EVENT_VELOCITY_TOO_HIGH_REASON)
    if observation.official_source_lag_seconds > config.max_official_source_lag_seconds:
        blockers.append(OFFICIAL_SOURCE_LAG_EXCESSIVE_REASON)
    if (
        observation.contradiction_severity
        > config.max_contradiction_severity_for_exception
    ):
        blockers.append(CONTRADICTION_SEVERITY_EXCESSIVE_REASON)
    if observation.probability_movement > config.max_probability_movement_for_exception:
        blockers.append(PROBABILITY_MOVEMENT_EXCESSIVE_REASON)
    if observation.resolution_horizon_seconds < config.minimum_resolution_horizon_seconds:
        blockers.append(RESOLUTION_HORIZON_TOO_SHORT_REASON)
    if observation.source_family_reliability < config.minimum_source_family_reliability:
        blockers.append(SOURCE_FAMILY_RELIABILITY_LOW_REASON)
    if blockers:
        return tuple(blockers), "stale_blocked", "blocked", False
    return (STALE_TOLERATED_REASON,), "stale_tolerated", "pass", True


def _normalize_observations(
    observations: object,
    *,
    generated_at: datetime,
) -> tuple[ResearchPacketSourceFreshnessExceptionGateV2Observation, ...]:
    if type(observations) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    normalized = tuple(observations)
    seen_keys: set[tuple[str, str]] = set()
    for observation in normalized:
        if type(observation) is not ResearchPacketSourceFreshnessExceptionGateV2Observation:
            raise ValueError(
                "observations must contain "
                "ResearchPacketSourceFreshnessExceptionGateV2Observation",
            )
        _require_hard_flags("observation", observation)
        if observation.source_observed_at > generated_at:
            raise ValueError("source_observed_at must not be in the future")
        key = (observation.packet_id, observation.market_id)
        if key in seen_keys:
            raise ValueError("observations must be unique by packet_id and market_id")
        seen_keys.add(key)
    return tuple(sorted(normalized, key=lambda row: (row.market_id, row.packet_id)))


def _normalize_rows(
    rows: object,
) -> tuple[ResearchPacketSourceFreshnessExceptionGateV2Row, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    expected = tuple(sorted(normalized, key=_row_sort_key))
    if normalized != expected:
        raise ValueError("rows must be sorted by gate status and identity")
    seen_keys: set[tuple[str, str]] = set()
    for row in normalized:
        if type(row) is not ResearchPacketSourceFreshnessExceptionGateV2Row:
            raise ValueError(
                "rows must contain ResearchPacketSourceFreshnessExceptionGateV2Row",
            )
        _require_hard_flags("row", row)
        key = (row.packet_id, row.market_id)
        if key in seen_keys:
            raise ValueError("rows must be unique by packet_id and market_id")
        seen_keys.add(key)
    return normalized


def _normalize_reason_code_counts(
    counts: object,
) -> tuple[ResearchPacketSourceFreshnessExceptionGateV2ReasonCodeCount, ...]:
    if type(counts) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized = tuple(counts)
    expected = tuple(sorted(normalized, key=_reason_code_count_sort_key))
    if normalized != expected:
        raise ValueError("reason_code_counts must follow deterministic reason order")
    seen_reason_codes: set[str] = set()
    for count in normalized:
        if type(count) is not ResearchPacketSourceFreshnessExceptionGateV2ReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchPacketSourceFreshnessExceptionGateV2ReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", count)
        if count.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen_reason_codes.add(count.reason_code)
    return normalized


def _validate_row(row: ResearchPacketSourceFreshnessExceptionGateV2Row) -> None:
    if row.source_freshness_status == "fresh":
        if row.reason_codes != (FRESH_REASON,):
            raise ValueError("fresh rows must use the fresh reason")
        if row.gate_status != "pass":
            raise ValueError("fresh rows must pass the gate")
        if row.stale_source_tolerated is not False:
            raise ValueError("fresh rows must not mark stale_source_tolerated")
        return
    if row.source_freshness_status == "stale_tolerated":
        if row.reason_codes != (STALE_TOLERATED_REASON,):
            raise ValueError("tolerated stale rows must use the tolerated reason")
        if row.gate_status != "pass":
            raise ValueError("tolerated stale rows must pass the gate")
        if row.stale_source_tolerated is not True:
            raise ValueError("tolerated stale rows must mark stale_source_tolerated")
        return
    if row.source_freshness_status == "stale_blocked":
        if row.gate_status != "blocked":
            raise ValueError("blocked stale rows must block the gate")
        if row.stale_source_tolerated is not False:
            raise ValueError("blocked stale rows must not tolerate stale evidence")
        if not set(row.reason_codes).isdisjoint(
            {STALE_TOLERATED_REASON, FRESH_REASON},
        ):
            raise ValueError("blocked stale rows must use blocker reasons only")
        return
    raise ValueError("source_freshness_status must be known")


def _validate_report(report: ResearchPacketSourceFreshnessExceptionGateV2Report) -> None:
    if report.observation_count != _count(len(report.rows)):
        raise ValueError("observation_count must match rows")
    if report.fresh_source_count != _count(
        sum(1 for row in report.rows if row.source_freshness_status == "fresh"),
    ):
        raise ValueError("fresh_source_count must match rows")
    if report.stale_source_count != _count(
        sum(1 for row in report.rows if row.source_freshness_status != "fresh"),
    ):
        raise ValueError("stale_source_count must match rows")
    if report.tolerated_stale_source_count != _count(
        sum(1 for row in report.rows if row.source_freshness_status == "stale_tolerated"),
    ):
        raise ValueError("tolerated_stale_source_count must match rows")
    if report.blocked_stale_source_count != _count(
        sum(1 for row in report.rows if row.source_freshness_status == "stale_blocked"),
    ):
        raise ValueError("blocked_stale_source_count must match rows")
    if report.stale_source_count != (
        report.tolerated_stale_source_count + report.blocked_stale_source_count
    ):
        raise ValueError("stale_source_count must match stale outcomes")
    if report.observation_count != report.fresh_source_count + report.stale_source_count:
        raise ValueError("observation_count must match freshness counts")
    if report.exception_ratio != _ratio(
        report.blocked_stale_source_count,
        report.observation_count,
    ):
        raise ValueError("exception_ratio must match blocked stale source count")
    if report.tolerated_stale_source_ratio != _ratio(
        report.tolerated_stale_source_count,
        report.stale_source_count,
    ):
        raise ValueError("tolerated_stale_source_ratio must match stale source count")
    if report.max_source_age_seconds != _max_source_age_seconds(report.rows):
        raise ValueError("max_source_age_seconds must match rows")
    if report.gate_status != _report_gate_status(report.rows):
        raise ValueError("gate_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _report_gate_status(
    rows: tuple[ResearchPacketSourceFreshnessExceptionGateV2Row, ...],
) -> str:
    if not rows:
        return "empty"
    if any(row.gate_status == "blocked" for row in rows):
        return "blocked"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchPacketSourceFreshnessExceptionGateV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    reasons: list[str] = []
    for reason_code in ROW_REASON_CODES:
        if any(reason_code in row.reason_codes for row in rows):
            reasons.append(reason_code)
    return tuple(reasons)


def _reason_code_counts(
    rows: tuple[ResearchPacketSourceFreshnessExceptionGateV2Row, ...],
) -> tuple[ResearchPacketSourceFreshnessExceptionGateV2ReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchPacketSourceFreshnessExceptionGateV2ReasonCodeCount(
                reason_code=EMPTY_REASON,
                count=_count(0),
                observation_ratio=ZERO,
            ),
        )
    counts: list[ResearchPacketSourceFreshnessExceptionGateV2ReasonCodeCount] = []
    for reason_code in ROW_REASON_CODES:
        reason_count = sum(1 for row in rows if reason_code in row.reason_codes)
        if reason_count:
            counts.append(
                ResearchPacketSourceFreshnessExceptionGateV2ReasonCodeCount(
                    reason_code=reason_code,
                    count=_count(reason_count),
                    observation_ratio=_ratio(_count(reason_count), _count(len(rows))),
                ),
            )
    return tuple(counts)


def _max_source_age_seconds(
    rows: tuple[ResearchPacketSourceFreshnessExceptionGateV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.source_age_seconds for row in rows)


def _row_sort_key(
    row: ResearchPacketSourceFreshnessExceptionGateV2Row,
) -> tuple[int, int, str, str, str]:
    return (
        0 if row.gate_status == "blocked" else 1,
        SOURCE_FRESHNESS_STATUSES.index(row.source_freshness_status),
        row.market_id,
        row.packet_id,
        row.source_family,
    )


def _reason_code_count_sort_key(
    count: ResearchPacketSourceFreshnessExceptionGateV2ReasonCodeCount,
) -> int:
    return REPORT_REASON_CODES.index(count.reason_code)


def _normalize_reason_codes(
    field_name: str,
    values: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    normalized = tuple(values)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    previous_rank: int | None = None
    for reason_code in normalized:
        _require_member("reason_code", reason_code, allowed)
        rank = allowed.index(reason_code)
        if previous_rank is not None and rank <= previous_rank:
            raise ValueError(f"{field_name} must follow deterministic reason order")
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
        previous_rank = rank
    row_reasons = allowed == ROW_REASON_CODES
    if row_reasons and FRESH_REASON in normalized and normalized != (FRESH_REASON,):
        raise ValueError("fresh reason must not be mixed")
    if (
        row_reasons
        and STALE_TOLERATED_REASON in normalized
        and normalized != (STALE_TOLERATED_REASON,)
    ):
        raise ValueError("tolerated reason must not be mixed")
    if EMPTY_REASON in normalized and normalized != (EMPTY_REASON,):
        raise ValueError("empty reason must not be mixed")
    return normalized


def _require_public_payload_fields(payload: dict[str, object]) -> None:
    payload_fields = tuple(payload.keys())
    if set(payload_fields) != set(PUBLIC_PAYLOAD_FIELDS):
        missing = sorted(set(PUBLIC_PAYLOAD_FIELDS) - set(payload_fields))
        extra = sorted(set(payload_fields) - set(PUBLIC_PAYLOAD_FIELDS))
        if missing:
            raise ValueError(f"public payload missing fields: {', '.join(missing)}")
        raise ValueError(f"public payload contains unsupported fields: {', '.join(extra)}")
    for field_name in PHASE_FLAG_FIELDS:
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True in public payload")


def _validate_public_payload(payload: dict[str, object]) -> None:
    expected_digest = _payload_derived_validation_digest(payload)
    actual_digest = _normalize_sha256(
        DERIVED_VALIDATION_DIGEST_FIELD,
        payload[DERIVED_VALIDATION_DIGEST_FIELD],
    )
    if actual_digest != expected_digest:
        raise ValueError("derived_validation_digest must match public payload")


def _report_derived_validation_digest(
    report: ResearchPacketSourceFreshnessExceptionGateV2Report,
) -> str:
    return _payload_derived_validation_digest(_json_ready(asdict(report)))


def _payload_derived_validation_digest(payload: object) -> str:
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")
    digest_payload = dict(payload)
    digest_payload.pop(DERIVED_VALIDATION_DIGEST_FIELD, None)
    _reject_unsafe_public_payload("digest_payload", digest_payload)
    encoded_payload = json.dumps(
        digest_payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded_payload).hexdigest()


def _validate_report_derived_validation_digest(
    report: ResearchPacketSourceFreshnessExceptionGateV2Report,
) -> None:
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be 64 hex characters")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be lowercase hex")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    if delta.total_seconds() < 0:
        raise ValueError("source_observed_at must not be in the future")
    micros = (
        delta.days * 86_400 * 1_000_000
        + delta.seconds * 1_000_000
        + delta.microseconds
    )
    with localcontext(DECIMAL_CONTEXT):
        return (Decimal(micros) / Decimal("1000000")).quantize(QUANTUM)


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical non-empty string")
    _reject_unsafe_public_text(field_name, value)


def _require_member(field_name: str, value: object, choices: tuple[str, ...]) -> None:
    _require_public_string(field_name, value)
    if value not in choices:
        raise ValueError(f"{field_name} must be one of {choices}")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _quantize_decimal(field_name: str, value: Decimal) -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANTUM)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc


def _require_seconds(field_name: str, value: object) -> Decimal:
    decimal_value = _quantize_decimal(field_name, _require_decimal(field_name, value))
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_seconds(field_name: str, value: object) -> Decimal:
    decimal_value = _require_seconds(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _quantize_decimal(field_name, _require_decimal(field_name, value))
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_count(field_name: str, value: object) -> Decimal:
    decimal_value = _quantize_decimal(field_name, _require_decimal(field_name, value))
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return decimal_value


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count value must be a nonnegative int")
    return Decimal(value).quantize(QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    normalized_numerator = _require_count("numerator", numerator)
    normalized_denominator = _require_count("denominator", denominator)
    if normalized_denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (normalized_numerator / normalized_denominator).quantize(QUANTUM)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if _has_unsafe_public_token(key):
                raise ValueError(f"unsafe public field in {label}: {key}")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    if _has_unsafe_public_token(value):
        raise ValueError(f"unsafe public value in {label}")


def _has_unsafe_public_token(value: str) -> bool:
    lowered = value.lower()
    return any(token in lowered for token in UNSAFE_PUBLIC_KEY_VALUE_TOKENS)


def _json_ready(value: Any) -> Any:
    if type(value) is float:
        raise ValueError("payload must not contain float values")
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat().replace("+00:00", "Z")
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    return value


__all__ = (
    "DEFAULT_RESEARCH_PACKET_SOURCE_FRESHNESS_EXCEPTION_GATE_V2_CONFIG_VERSION",
    "EMPTY_REASON",
    "FRESH_REASON",
    "STALE_TOLERATED_REASON",
    "EVENT_VELOCITY_TOO_HIGH_REASON",
    "OFFICIAL_SOURCE_LAG_EXCESSIVE_REASON",
    "CONTRADICTION_SEVERITY_EXCESSIVE_REASON",
    "PROBABILITY_MOVEMENT_EXCESSIVE_REASON",
    "RESOLUTION_HORIZON_TOO_SHORT_REASON",
    "SOURCE_FAMILY_RELIABILITY_LOW_REASON",
    "ResearchPacketSourceFreshnessExceptionGateV2Config",
    "ResearchPacketSourceFreshnessExceptionGateV2Observation",
    "ResearchPacketSourceFreshnessExceptionGateV2Row",
    "ResearchPacketSourceFreshnessExceptionGateV2ReasonCodeCount",
    "ResearchPacketSourceFreshnessExceptionGateV2Report",
    "build_research_packet_source_freshness_exception_gate_v2_report",
    "research_packet_source_freshness_exception_gate_v2_payload",
)
