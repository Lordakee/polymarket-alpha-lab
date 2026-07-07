"""Pure Phase 1 readonly catalyst source freshness gate report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, localcontext
import hashlib
import json
from typing import Any


DEFAULT_RESEARCH_PACKET_CATALYST_SOURCE_FRESHNESS_GATE_V2_CONFIG_VERSION = (
    "research-packet-catalyst-source-freshness-gate-v2-v0"
)

DECIMAL_QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
WATCH_RISK_SCORE = Decimal("0.500000")
SECONDS_PER_HOUR = Decimal("3600.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")

STATUSES = ("pass", "watch", "blocked")
REASON_CODES = (
    "catalyst_source_freshness_gate_no_inputs",
    "catalyst_source_freshness_gate_status_pass",
    "catalyst_source_freshness_gate_status_watch",
    "catalyst_source_freshness_gate_status_blocked",
    "missing_official_source",
    "stale_official_source_watch",
    "stale_official_source_blocked",
    "stale_catalyst_source_watch",
    "stale_catalyst_source_blocked",
    "insufficient_fresh_sources_watch",
    "insufficient_fresh_sources_blocked",
    "weak_fresh_source_ratio_watch",
    "weak_fresh_source_ratio_blocked",
)
REASON_CODE_PRIORITY = REASON_CODES
BLOCK_REASONS = frozenset(
    (
        "missing_official_source",
        "stale_official_source_blocked",
        "stale_catalyst_source_blocked",
        "insufficient_fresh_sources_blocked",
        "weak_fresh_source_ratio_blocked",
    ),
)
WATCH_REASONS = frozenset(
    (
        "stale_official_source_watch",
        "stale_catalyst_source_watch",
        "insufficient_fresh_sources_watch",
        "weak_fresh_source_ratio_watch",
    ),
)
STATUS_REASON = {
    "pass": "catalyst_source_freshness_gate_status_pass",
    "watch": "catalyst_source_freshness_gate_status_watch",
    "blocked": "catalyst_source_freshness_gate_status_blocked",
}
REPORT_NEXT_STEPS = {
    "pass": "use_catalyst_sources_for_paper_report",
    "watch": "review_catalyst_sources_for_paper_report",
    "blocked": "collect_catalyst_sources_for_paper_report",
}
ROW_ACTIONS = {
    "pass": "catalyst_source_freshness_clear",
    "watch": "catalyst_source_freshness_review",
    "blocked": "catalyst_source_freshness_research_first",
}
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
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"

_CONFIG_PAYLOAD_FIELDS = (
    "config_version",
    "max_pass_official_source_age_hours",
    "max_watch_official_source_age_hours",
    "max_pass_catalyst_source_age_hours",
    "max_watch_catalyst_source_age_hours",
    "min_pass_official_source_count",
    "min_watch_official_source_count",
    "min_pass_fresh_source_count",
    "min_watch_fresh_source_count",
    "min_pass_fresh_source_ratio",
    "min_watch_fresh_source_ratio",
    "paper_only",
    "report_only",
    "readonly",
)
_INPUT_PAYLOAD_FIELDS = (
    "packet_ref",
    "question_ref",
    "catalyst_ref",
    "latest_official_source_at",
    "latest_catalyst_source_at",
    "official_source_count",
    "source_count",
    "fresh_source_count",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
_ROW_PAYLOAD_FIELDS = (
    "packet_ref",
    "question_ref",
    "catalyst_ref",
    "latest_official_source_at",
    "latest_catalyst_source_at",
    "official_source_count",
    "source_count",
    "fresh_source_count",
    "latest_official_source_age_hours",
    "latest_catalyst_source_age_hours",
    "fresh_source_ratio",
    "freshness_risk_score",
    "source_status",
    "recommended_research_action",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
_REPORT_PAYLOAD_FIELDS = (
    "generated_at",
    "config_version",
    "status",
    "recommended_next_step",
    "input_count",
    "blocked_count",
    "watch_count",
    "pass_count",
    "missing_official_source_count",
    "stale_official_source_count",
    "stale_catalyst_source_count",
    "insufficient_fresh_source_count",
    "highest_freshness_risk_score",
    "max_latest_official_source_age_hours",
    "max_latest_catalyst_source_age_hours",
    "min_fresh_source_ratio",
    "rows",
    "reason_codes",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)

__all__ = (
    "DEFAULT_RESEARCH_PACKET_CATALYST_SOURCE_FRESHNESS_GATE_V2_CONFIG_VERSION",
    "REASON_CODES",
    "ResearchPacketCatalystSourceFreshnessGateV2Config",
    "ResearchPacketCatalystSourceFreshnessGateV2Input",
    "ResearchPacketCatalystSourceFreshnessGateV2Report",
    "ResearchPacketCatalystSourceFreshnessGateV2Row",
    "STATUSES",
    "build_research_packet_catalyst_source_freshness_gate_v2_report",
    "research_packet_catalyst_source_freshness_gate_v2_payload",
)


@dataclass(frozen=True)
class ResearchPacketCatalystSourceFreshnessGateV2Config:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_CATALYST_SOURCE_FRESHNESS_GATE_V2_CONFIG_VERSION
    )
    max_pass_official_source_age_hours: Decimal = Decimal("12.000000")
    max_watch_official_source_age_hours: Decimal = Decimal("24.000000")
    max_pass_catalyst_source_age_hours: Decimal = Decimal("24.000000")
    max_watch_catalyst_source_age_hours: Decimal = Decimal("48.000000")
    min_pass_official_source_count: Decimal = Decimal("1.000000")
    min_watch_official_source_count: Decimal = Decimal("1.000000")
    min_pass_fresh_source_count: Decimal = Decimal("2.000000")
    min_watch_fresh_source_count: Decimal = Decimal("1.000000")
    min_pass_fresh_source_ratio: Decimal = Decimal("0.666667")
    min_watch_fresh_source_ratio: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketCatalystSourceFreshnessGateV2Config:
            raise ValueError(
                "config must be a ResearchPacketCatalystSourceFreshnessGateV2Config",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_CATALYST_SOURCE_FRESHNESS_GATE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "max_pass_official_source_age_hours",
            "max_watch_official_source_age_hours",
            "max_pass_catalyst_source_age_hours",
            "max_watch_catalyst_source_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_official_source_count",
            "min_watch_official_source_count",
            "min_pass_fresh_source_count",
            "min_watch_fresh_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("min_pass_fresh_source_ratio", "min_watch_fresh_source_ratio"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", asdict(self))

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload("config payload", payload)
        if type(payload) is not dict:
            raise ValueError("config payload must be an object")
        return payload


@dataclass(frozen=True)
class ResearchPacketCatalystSourceFreshnessGateV2Input:
    packet_ref: str
    question_ref: str
    catalyst_ref: str
    latest_official_source_at: datetime | None
    latest_catalyst_source_at: datetime
    official_source_count: Decimal
    source_count: Decimal
    fresh_source_count: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketCatalystSourceFreshnessGateV2Input:
            raise ValueError(
                "subject must be a ResearchPacketCatalystSourceFreshnessGateV2Input",
            )
        for field_name in ("packet_ref", "question_ref", "catalyst_ref"):
            _require_identifier(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "latest_official_source_at",
            _optional_utc("latest_official_source_at", self.latest_official_source_at),
        )
        object.__setattr__(
            self,
            "latest_catalyst_source_at",
            _as_utc("latest_catalyst_source_at", self.latest_catalyst_source_at),
        )
        for field_name in ("official_source_count", "source_count", "fresh_source_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.official_source_count > self.source_count:
            raise ValueError("official_source_count must be at most source_count")
        if self.fresh_source_count > self.source_count:
            raise ValueError("fresh_source_count must be at most source_count")
        if self.official_source_count == ZERO and self.latest_official_source_at is not None:
            raise ValueError("latest_official_source_at requires official_source_count")
        if self.official_source_count > ZERO and self.latest_official_source_at is None:
            raise ValueError("latest_official_source_at is required for official sources")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_source_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("subject", self)
        _reject_unsafe_public_payload("catalyst source freshness input", asdict(self))


@dataclass(frozen=True)
class ResearchPacketCatalystSourceFreshnessGateV2Row:
    packet_ref: str
    question_ref: str
    catalyst_ref: str
    latest_official_source_at: datetime | None
    latest_catalyst_source_at: datetime
    official_source_count: Decimal
    source_count: Decimal
    fresh_source_count: Decimal
    latest_official_source_age_hours: Decimal
    latest_catalyst_source_age_hours: Decimal
    fresh_source_ratio: Decimal
    freshness_risk_score: Decimal
    source_status: str
    recommended_research_action: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketCatalystSourceFreshnessGateV2Row:
            raise ValueError("row must be a ResearchPacketCatalystSourceFreshnessGateV2Row")
        for field_name in ("packet_ref", "question_ref", "catalyst_ref"):
            _require_identifier(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "latest_official_source_at",
            _optional_utc("latest_official_source_at", self.latest_official_source_at),
        )
        object.__setattr__(
            self,
            "latest_catalyst_source_at",
            _as_utc("latest_catalyst_source_at", self.latest_catalyst_source_at),
        )
        for field_name in ("official_source_count", "source_count", "fresh_source_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "latest_official_source_age_hours",
            "latest_catalyst_source_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("fresh_source_ratio", "freshness_risk_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_choice("source_status", self.source_status, STATUSES)
        _require_choice(
            "recommended_research_action",
            self.recommended_research_action,
            tuple(ROW_ACTIONS.values()),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("catalyst source freshness row", asdict(self))
        _validate_row(self)


@dataclass(frozen=True)
class ResearchPacketCatalystSourceFreshnessGateV2Report:
    generated_at: datetime
    config_version: str
    status: str
    recommended_next_step: str
    input_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    missing_official_source_count: Decimal
    stale_official_source_count: Decimal
    stale_catalyst_source_count: Decimal
    insufficient_fresh_source_count: Decimal
    highest_freshness_risk_score: Decimal
    max_latest_official_source_age_hours: Decimal
    max_latest_catalyst_source_age_hours: Decimal
    min_fresh_source_ratio: Decimal | None
    rows: tuple[ResearchPacketCatalystSourceFreshnessGateV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketCatalystSourceFreshnessGateV2Report:
            raise ValueError("report must be a ResearchPacketCatalystSourceFreshnessGateV2Report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_CATALYST_SOURCE_FRESHNESS_GATE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        _require_choice("status", self.status, STATUSES)
        _require_choice(
            "recommended_next_step",
            self.recommended_next_step,
            tuple(REPORT_NEXT_STEPS.values()),
        )
        for field_name in (
            "input_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "missing_official_source_count",
            "stale_official_source_count",
            "stale_catalyst_source_count",
            "insufficient_fresh_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "highest_freshness_risk_score",
            "max_latest_official_source_age_hours",
            "max_latest_catalyst_source_age_hours",
        ):
            normalizer = (
                _normalize_probability
                if field_name == "highest_freshness_risk_score"
                else _normalize_nonnegative_decimal
            )
            object.__setattr__(
                self,
                field_name,
                normalizer(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_fresh_source_ratio",
            _normalize_optional_probability(
                "min_fresh_source_ratio",
                self.min_fresh_source_ratio,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("catalyst source freshness report", asdict(self))
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _derived_validation_digest(self),
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
        _validate_report(self)
        _validate_report_derived_validation_digest(self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload("catalyst source freshness payload", payload)
        if type(payload) is not dict:
            raise ValueError("catalyst source freshness payload must be an object")
        _validate_report_derived_validation_digest(self)
        return payload

    @classmethod
    def from_payload(
        cls,
        payload: object,
    ) -> ResearchPacketCatalystSourceFreshnessGateV2Report:
        _reject_unsafe_public_payload("catalyst source freshness payload", payload)
        payload_dict = _payload_dict("catalyst source freshness payload", payload)
        _require_payload_fields(payload_dict, _REPORT_PAYLOAD_FIELDS)
        rows_value = payload_dict["rows"]
        if type(rows_value) is not list:
            raise ValueError("rows must be a list")
        rows = tuple(_row_from_payload(item) for item in rows_value)
        return cls(
            generated_at=_datetime_from_payload("generated_at", payload_dict["generated_at"]),
            config_version=_payload_string("config_version", payload_dict["config_version"]),
            status=_payload_string("status", payload_dict["status"]),
            recommended_next_step=_payload_string(
                "recommended_next_step",
                payload_dict["recommended_next_step"],
            ),
            input_count=_decimal_from_payload("input_count", payload_dict["input_count"]),
            blocked_count=_decimal_from_payload("blocked_count", payload_dict["blocked_count"]),
            watch_count=_decimal_from_payload("watch_count", payload_dict["watch_count"]),
            pass_count=_decimal_from_payload("pass_count", payload_dict["pass_count"]),
            missing_official_source_count=_decimal_from_payload(
                "missing_official_source_count",
                payload_dict["missing_official_source_count"],
            ),
            stale_official_source_count=_decimal_from_payload(
                "stale_official_source_count",
                payload_dict["stale_official_source_count"],
            ),
            stale_catalyst_source_count=_decimal_from_payload(
                "stale_catalyst_source_count",
                payload_dict["stale_catalyst_source_count"],
            ),
            insufficient_fresh_source_count=_decimal_from_payload(
                "insufficient_fresh_source_count",
                payload_dict["insufficient_fresh_source_count"],
            ),
            highest_freshness_risk_score=_decimal_from_payload(
                "highest_freshness_risk_score",
                payload_dict["highest_freshness_risk_score"],
            ),
            max_latest_official_source_age_hours=_decimal_from_payload(
                "max_latest_official_source_age_hours",
                payload_dict["max_latest_official_source_age_hours"],
            ),
            max_latest_catalyst_source_age_hours=_decimal_from_payload(
                "max_latest_catalyst_source_age_hours",
                payload_dict["max_latest_catalyst_source_age_hours"],
            ),
            min_fresh_source_ratio=_optional_decimal_from_payload(
                "min_fresh_source_ratio",
                payload_dict["min_fresh_source_ratio"],
            ),
            rows=rows,
            reason_codes=_payload_reason_codes("reason_codes", payload_dict["reason_codes"]),
            derived_validation_digest=_payload_string(
                DERIVED_VALIDATION_DIGEST_FIELD,
                payload_dict[DERIVED_VALIDATION_DIGEST_FIELD],
            ),
            paper_only=_payload_true("paper_only", payload_dict["paper_only"]),
            report_only=_payload_true("report_only", payload_dict["report_only"]),
            readonly=_payload_true("readonly", payload_dict["readonly"]),
        )


def build_research_packet_catalyst_source_freshness_gate_v2_report(
    rows: object,
    *,
    config: ResearchPacketCatalystSourceFreshnessGateV2Config,
    generated_at: datetime,
) -> ResearchPacketCatalystSourceFreshnessGateV2Report:
    if type(config) is not ResearchPacketCatalystSourceFreshnessGateV2Config:
        raise ValueError("config must be a ResearchPacketCatalystSourceFreshnessGateV2Config")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(rows)
    built_rows = tuple(_build_row(item, config=config, generated_at=generated_at_utc) for item in inputs)
    ranked_rows = _rank_rows(built_rows)
    return ResearchPacketCatalystSourceFreshnessGateV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(ranked_rows),
        recommended_next_step=REPORT_NEXT_STEPS[_report_status(ranked_rows)],
        input_count=_count(len(ranked_rows)),
        blocked_count=_count(sum(1 for row in ranked_rows if row.source_status == "blocked")),
        watch_count=_count(sum(1 for row in ranked_rows if row.source_status == "watch")),
        pass_count=_count(sum(1 for row in ranked_rows if row.source_status == "pass")),
        missing_official_source_count=_count(
            sum(1 for row in ranked_rows if "missing_official_source" in row.reason_codes),
        ),
        stale_official_source_count=_count(
            sum(
                1
                for row in ranked_rows
                if "stale_official_source_watch" in row.reason_codes
                or "stale_official_source_blocked" in row.reason_codes
            ),
        ),
        stale_catalyst_source_count=_count(
            sum(
                1
                for row in ranked_rows
                if "stale_catalyst_source_watch" in row.reason_codes
                or "stale_catalyst_source_blocked" in row.reason_codes
            ),
        ),
        insufficient_fresh_source_count=_count(
            sum(
                1
                for row in ranked_rows
                if "insufficient_fresh_sources_watch" in row.reason_codes
                or "insufficient_fresh_sources_blocked" in row.reason_codes
                or "weak_fresh_source_ratio_watch" in row.reason_codes
                or "weak_fresh_source_ratio_blocked" in row.reason_codes
            ),
        ),
        highest_freshness_risk_score=_max_decimal(
            row.freshness_risk_score for row in ranked_rows
        ),
        max_latest_official_source_age_hours=_max_decimal(
            row.latest_official_source_age_hours for row in ranked_rows
        ),
        max_latest_catalyst_source_age_hours=_max_decimal(
            row.latest_catalyst_source_age_hours for row in ranked_rows
        ),
        min_fresh_source_ratio=_min_decimal(row.fresh_source_ratio for row in ranked_rows),
        rows=ranked_rows,
        reason_codes=_report_reason_codes(ranked_rows),
    )


def research_packet_catalyst_source_freshness_gate_v2_payload(
    report: ResearchPacketCatalystSourceFreshnessGateV2Report,
) -> dict[str, object]:
    if type(report) is not ResearchPacketCatalystSourceFreshnessGateV2Report:
        raise ValueError("report must be a ResearchPacketCatalystSourceFreshnessGateV2Report")
    _require_hard_flags("report", report)
    _validate_report(report)
    _validate_report_derived_validation_digest(report)
    return report.payload


def _build_row(
    item: ResearchPacketCatalystSourceFreshnessGateV2Input,
    *,
    config: ResearchPacketCatalystSourceFreshnessGateV2Config,
    generated_at: datetime,
) -> ResearchPacketCatalystSourceFreshnessGateV2Row:
    _validate_input_timestamps(item, generated_at)
    latest_catalyst_source_age_hours = _hours_between(
        item.latest_catalyst_source_at,
        generated_at,
    )
    latest_official_source_age_hours = _official_source_age_hours(
        item.latest_official_source_at,
        config=config,
        generated_at=generated_at,
    )
    fresh_source_ratio = _fresh_source_ratio(
        source_count=item.source_count,
        fresh_source_count=item.fresh_source_count,
    )
    reason_codes = [
        *item.reason_codes,
        *_freshness_reason_codes(
            official_source_count=item.official_source_count,
            source_count=item.source_count,
            fresh_source_count=item.fresh_source_count,
            latest_official_source_age_hours=latest_official_source_age_hours,
            latest_catalyst_source_age_hours=latest_catalyst_source_age_hours,
            fresh_source_ratio=fresh_source_ratio,
            config=config,
        ),
    ]
    source_status = _row_status(reason_codes)
    reason_codes.append(STATUS_REASON[source_status])
    return ResearchPacketCatalystSourceFreshnessGateV2Row(
        packet_ref=item.packet_ref,
        question_ref=item.question_ref,
        catalyst_ref=item.catalyst_ref,
        latest_official_source_at=item.latest_official_source_at,
        latest_catalyst_source_at=item.latest_catalyst_source_at,
        official_source_count=item.official_source_count,
        source_count=item.source_count,
        fresh_source_count=item.fresh_source_count,
        latest_official_source_age_hours=latest_official_source_age_hours,
        latest_catalyst_source_age_hours=latest_catalyst_source_age_hours,
        fresh_source_ratio=fresh_source_ratio,
        freshness_risk_score=_risk_score_for_status(source_status),
        source_status=source_status,
        recommended_research_action=ROW_ACTIONS[source_status],
        reason_codes=_sort_reason_codes(tuple(reason_codes)),
    )


def _freshness_reason_codes(
    *,
    official_source_count: Decimal,
    source_count: Decimal,
    fresh_source_count: Decimal,
    latest_official_source_age_hours: Decimal,
    latest_catalyst_source_age_hours: Decimal,
    fresh_source_ratio: Decimal,
    config: ResearchPacketCatalystSourceFreshnessGateV2Config,
) -> tuple[str, ...]:
    del source_count
    reason_codes: list[str] = []
    if official_source_count < config.min_watch_official_source_count:
        reason_codes.append("missing_official_source")
    elif latest_official_source_age_hours > config.max_watch_official_source_age_hours:
        reason_codes.append("stale_official_source_blocked")
    elif latest_official_source_age_hours > config.max_pass_official_source_age_hours:
        reason_codes.append("stale_official_source_watch")

    if latest_catalyst_source_age_hours > config.max_watch_catalyst_source_age_hours:
        reason_codes.append("stale_catalyst_source_blocked")
    elif latest_catalyst_source_age_hours > config.max_pass_catalyst_source_age_hours:
        reason_codes.append("stale_catalyst_source_watch")

    if fresh_source_count < config.min_watch_fresh_source_count:
        reason_codes.append("insufficient_fresh_sources_blocked")
    elif fresh_source_count < config.min_pass_fresh_source_count:
        reason_codes.append("insufficient_fresh_sources_watch")

    if fresh_source_ratio < config.min_watch_fresh_source_ratio:
        reason_codes.append("weak_fresh_source_ratio_blocked")
    elif fresh_source_ratio < config.min_pass_fresh_source_ratio:
        reason_codes.append("weak_fresh_source_ratio_watch")
    return tuple(reason_codes)


def _official_source_age_hours(
    latest_official_source_at: datetime | None,
    *,
    config: ResearchPacketCatalystSourceFreshnessGateV2Config,
    generated_at: datetime,
) -> Decimal:
    if latest_official_source_at is None:
        return _quantize(config.max_watch_official_source_age_hours + ONE)
    return _hours_between(latest_official_source_at, generated_at)


def _validate_config(config: ResearchPacketCatalystSourceFreshnessGateV2Config) -> None:
    if config.max_pass_official_source_age_hours > config.max_watch_official_source_age_hours:
        raise ValueError(
            "max_pass_official_source_age_hours must be at most "
            "max_watch_official_source_age_hours",
        )
    if config.max_pass_catalyst_source_age_hours > config.max_watch_catalyst_source_age_hours:
        raise ValueError(
            "max_pass_catalyst_source_age_hours must be at most "
            "max_watch_catalyst_source_age_hours",
        )
    if config.min_pass_official_source_count < config.min_watch_official_source_count:
        raise ValueError(
            "min_pass_official_source_count must be at least "
            "min_watch_official_source_count",
        )
    if config.min_pass_fresh_source_count < config.min_watch_fresh_source_count:
        raise ValueError(
            "min_pass_fresh_source_count must be at least min_watch_fresh_source_count",
        )
    if config.min_pass_fresh_source_ratio < config.min_watch_fresh_source_ratio:
        raise ValueError(
            "min_pass_fresh_source_ratio must be at least min_watch_fresh_source_ratio",
        )


def _validate_row(row: ResearchPacketCatalystSourceFreshnessGateV2Row) -> None:
    if row.official_source_count > row.source_count:
        raise ValueError("official_source_count must be at most source_count")
    if row.fresh_source_count > row.source_count:
        raise ValueError("fresh_source_count must be at most source_count")
    if row.official_source_count == ZERO and row.latest_official_source_at is not None:
        raise ValueError("latest_official_source_at requires official_source_count")
    if row.official_source_count > ZERO and row.latest_official_source_at is None:
        raise ValueError("latest_official_source_at is required for official sources")
    if row.fresh_source_ratio != _fresh_source_ratio(
        source_count=row.source_count,
        fresh_source_count=row.fresh_source_count,
    ):
        raise ValueError("fresh_source_ratio must match source counts")
    if row.source_status != _row_status(row.reason_codes):
        raise ValueError("source_status must match reason_codes")
    if row.freshness_risk_score != _risk_score_for_status(row.source_status):
        raise ValueError("freshness_risk_score must match source_status")
    if row.recommended_research_action != ROW_ACTIONS[row.source_status]:
        raise ValueError("recommended_research_action must match source_status")
    if STATUS_REASON[row.source_status] not in row.reason_codes:
        raise ValueError("reason_codes must include source_status reason")


def _validate_report(report: ResearchPacketCatalystSourceFreshnessGateV2Report) -> None:
    rows = report.rows
    if report.input_count != _count(len(rows)):
        raise ValueError("input_count must match rows")
    if report.blocked_count != _count(sum(1 for row in rows if row.source_status == "blocked")):
        raise ValueError("blocked_count must match rows")
    if report.watch_count != _count(sum(1 for row in rows if row.source_status == "watch")):
        raise ValueError("watch_count must match rows")
    if report.pass_count != _count(sum(1 for row in rows if row.source_status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.missing_official_source_count != _count(
        sum(1 for row in rows if "missing_official_source" in row.reason_codes),
    ):
        raise ValueError("missing_official_source_count must match rows")
    if report.stale_official_source_count != _count(
        sum(
            1
            for row in rows
            if "stale_official_source_watch" in row.reason_codes
            or "stale_official_source_blocked" in row.reason_codes
        ),
    ):
        raise ValueError("stale_official_source_count must match rows")
    if report.stale_catalyst_source_count != _count(
        sum(
            1
            for row in rows
            if "stale_catalyst_source_watch" in row.reason_codes
            or "stale_catalyst_source_blocked" in row.reason_codes
        ),
    ):
        raise ValueError("stale_catalyst_source_count must match rows")
    if report.insufficient_fresh_source_count != _count(
        sum(
            1
            for row in rows
            if "insufficient_fresh_sources_watch" in row.reason_codes
            or "insufficient_fresh_sources_blocked" in row.reason_codes
            or "weak_fresh_source_ratio_watch" in row.reason_codes
            or "weak_fresh_source_ratio_blocked" in row.reason_codes
        ),
    ):
        raise ValueError("insufficient_fresh_source_count must match rows")
    if report.highest_freshness_risk_score != _max_decimal(
        row.freshness_risk_score for row in rows
    ):
        raise ValueError("highest_freshness_risk_score must match rows")
    if report.max_latest_official_source_age_hours != _max_decimal(
        row.latest_official_source_age_hours for row in rows
    ):
        raise ValueError("max_latest_official_source_age_hours must match rows")
    if report.max_latest_catalyst_source_age_hours != _max_decimal(
        row.latest_catalyst_source_age_hours for row in rows
    ):
        raise ValueError("max_latest_catalyst_source_age_hours must match rows")
    if report.min_fresh_source_ratio != _min_decimal(row.fresh_source_ratio for row in rows):
        raise ValueError("min_fresh_source_ratio must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.recommended_next_step != REPORT_NEXT_STEPS[report.status]:
        raise ValueError("recommended_next_step must match status")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    for row in rows:
        if row.latest_catalyst_source_at > report.generated_at:
            raise ValueError("latest_catalyst_source_at must not be after generated_at")
        if (
            row.latest_official_source_at is not None
            and row.latest_official_source_at > report.generated_at
        ):
            raise ValueError("latest_official_source_at must not be after generated_at")


def _validate_report_derived_validation_digest(
    report: ResearchPacketCatalystSourceFreshnessGateV2Report,
) -> None:
    if report.derived_validation_digest != _derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _normalize_inputs(
    rows: object,
) -> tuple[ResearchPacketCatalystSourceFreshnessGateV2Input, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable of catalyst source freshness inputs")
    try:
        normalized = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be an iterable of catalyst source freshness inputs") from exc
    seen_keys: set[tuple[str, str, str]] = set()
    for item in normalized:
        if type(item) is not ResearchPacketCatalystSourceFreshnessGateV2Input:
            raise ValueError(
                "rows must contain ResearchPacketCatalystSourceFreshnessGateV2Input values",
            )
        _require_hard_flags("input", item)
        key = (item.packet_ref, item.question_ref, item.catalyst_ref)
        if key in seen_keys:
            raise ValueError("rows must be unique by packet_ref question_ref catalyst_ref")
        seen_keys.add(key)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[ResearchPacketCatalystSourceFreshnessGateV2Row, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    seen_keys: set[tuple[str, str, str]] = set()
    for row in normalized:
        if type(row) is not ResearchPacketCatalystSourceFreshnessGateV2Row:
            raise ValueError(
                "rows must contain ResearchPacketCatalystSourceFreshnessGateV2Row values",
            )
        _require_hard_flags("row", row)
        key = (row.packet_ref, row.question_ref, row.catalyst_ref)
        if key in seen_keys:
            raise ValueError("rows must be unique by packet_ref question_ref catalyst_ref")
        seen_keys.add(key)
    if normalized != _rank_rows(normalized):
        raise ValueError("rows must be ranked")
    return normalized


def _rank_rows(
    rows: tuple[ResearchPacketCatalystSourceFreshnessGateV2Row, ...],
) -> tuple[ResearchPacketCatalystSourceFreshnessGateV2Row, ...]:
    return tuple(sorted(rows, key=_row_rank_key))


def _row_rank_key(
    row: ResearchPacketCatalystSourceFreshnessGateV2Row,
) -> tuple[int, Decimal, Decimal, Decimal, str, str, str]:
    return (
        {"blocked": 0, "watch": 1, "pass": 2}[row.source_status],
        -row.freshness_risk_score,
        -row.latest_catalyst_source_age_hours,
        -row.latest_official_source_age_hours,
        row.packet_ref,
        row.question_ref,
        row.catalyst_ref,
    )


def _validate_input_timestamps(
    item: ResearchPacketCatalystSourceFreshnessGateV2Input,
    generated_at: datetime,
) -> None:
    if item.latest_catalyst_source_at > generated_at:
        raise ValueError("latest_catalyst_source_at must not be after generated_at")
    if item.latest_official_source_at is not None and item.latest_official_source_at > generated_at:
        raise ValueError("latest_official_source_at must not be after generated_at")


def _report_status(
    rows: tuple[ResearchPacketCatalystSourceFreshnessGateV2Row, ...],
) -> str:
    if not rows:
        return "blocked"
    if any(row.source_status == "blocked" for row in rows):
        return "blocked"
    if any(row.source_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchPacketCatalystSourceFreshnessGateV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("catalyst_source_freshness_gate_no_inputs",)
    report_status = _report_status(rows)
    observed = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code in WATCH_REASONS or reason_code in BLOCK_REASONS
    }
    return _sort_reason_codes((STATUS_REASON[report_status], *tuple(observed)))


def _row_status(reason_codes: tuple[str, ...] | list[str]) -> str:
    if any(reason_code in BLOCK_REASONS for reason_code in reason_codes):
        return "blocked"
    if any(reason_code in WATCH_REASONS for reason_code in reason_codes):
        return "watch"
    return "pass"


def _risk_score_for_status(status: str) -> Decimal:
    return {
        "blocked": ONE,
        "watch": WATCH_RISK_SCORE,
        "pass": ZERO,
    }[status]


def _sort_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    source_reasons = sorted(reason_code for reason_code in reason_codes if reason_code not in REASON_CODES)
    gate_reasons = [
        reason_code
        for reason_code in REASON_CODE_PRIORITY
        if reason_code in reason_codes and reason_code not in source_reasons
    ]
    return tuple([*source_reasons, *gate_reasons])


def _normalize_source_reason_codes(field_name: str, values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_canonical_string(field_name, value)
        if _has_unsafe_public_token(value):
            raise ValueError(f"{field_name} has unsafe public payload value")
        if value not in normalized:
            normalized.append(value)
    return tuple(sorted(normalized))


def _normalize_row_reason_codes(field_name: str, values: object) -> tuple[str, ...]:
    normalized = _normalize_source_reason_codes(field_name, values)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    unknown_gate_reasons = [
        reason_code
        for reason_code in normalized
        if reason_code.startswith("catalyst_source_freshness_gate_")
        or reason_code.startswith("missing_official_source")
        or reason_code.startswith("stale_official_source")
        or reason_code.startswith("stale_catalyst_source")
        or reason_code.startswith("insufficient_fresh_sources")
        or reason_code.startswith("weak_fresh_source_ratio")
    ]
    if any(reason_code not in REASON_CODES for reason_code in unknown_gate_reasons):
        raise ValueError(f"{field_name} contains unknown gate reason code")
    return _sort_reason_codes(normalized)


def _normalize_report_reason_codes(field_name: str, values: object) -> tuple[str, ...]:
    normalized = _normalize_row_reason_codes(field_name, values)
    if any(reason_code not in REASON_CODES for reason_code in normalized):
        raise ValueError(f"{field_name} contains unknown report reason code")
    return normalized


def _fresh_source_ratio(*, source_count: Decimal, fresh_source_count: Decimal) -> Decimal:
    if source_count == ZERO:
        return ZERO
    with localcontext() as context:
        context.prec = 64
        return _quantize(fresh_source_count / source_count)


def _max_decimal(values: object) -> Decimal:
    items = tuple(values)  # type: ignore[arg-type]
    if not items:
        return ZERO
    return max(items)


def _min_decimal(values: object) -> Decimal | None:
    items = tuple(values)  # type: ignore[arg-type]
    if not items:
        return None
    return min(items)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(DECIMAL_QUANT)


def _hours_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    with localcontext() as context:
        context.prec = 64
        return _quantize((seconds + microseconds) / SECONDS_PER_HOUR)


def _normalize_optional_probability(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_probability(field_name, value)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = _quantize(value)
    if quantized != value:
        raise ValueError(f"{field_name} must not exceed six decimal places")
    return quantized


def _quantize(value: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = 64
        return value.quantize(DECIMAL_QUANT)


def _optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_identifier(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    assert type(value) is str
    if _has_unsafe_public_token(value):
        raise ValueError(f"{field_name} has unsafe public payload value")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _require_choice(field_name: str, value: object, choices: tuple[str, ...]) -> None:
    if type(value) is not str or value not in choices:
        raise ValueError(f"{field_name} must be one of {', '.join(choices)}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _derived_validation_digest(
    report: ResearchPacketCatalystSourceFreshnessGateV2Report,
) -> str:
    payload = _report_digest_payload(report)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(
        b"research_packet_catalyst_source_freshness_gate_v2|" + encoded,
    ).hexdigest()


def _report_digest_payload(
    report: ResearchPacketCatalystSourceFreshnessGateV2Report,
) -> dict[str, object]:
    payload = _payload_value(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report digest payload must be an object")
    payload.pop(DERIVED_VALIDATION_DIGEST_FIELD, None)
    return payload


def _payload_value(value: object) -> object:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is str:
        if _has_unsafe_public_token(value):
            raise ValueError("payload has unsafe public payload value")
        return value
    if type(value) is bool:
        return value
    if type(value) in (int, float):
        raise ValueError("payload numeric values must be Decimal-derived strings")
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        payload: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            if _has_unsafe_public_token(key):
                raise ValueError(f"unsafe public payload key: {key}")
            payload[key] = _payload_value(item)
        return payload
    raise ValueError("payload value is not JSON serializable")


def _row_from_payload(
    payload: object,
) -> ResearchPacketCatalystSourceFreshnessGateV2Row:
    payload_dict = _payload_dict("row payload", payload)
    _require_payload_fields(payload_dict, _ROW_PAYLOAD_FIELDS)
    return ResearchPacketCatalystSourceFreshnessGateV2Row(
        packet_ref=_payload_string("packet_ref", payload_dict["packet_ref"]),
        question_ref=_payload_string("question_ref", payload_dict["question_ref"]),
        catalyst_ref=_payload_string("catalyst_ref", payload_dict["catalyst_ref"]),
        latest_official_source_at=_optional_datetime_from_payload(
            "latest_official_source_at",
            payload_dict["latest_official_source_at"],
        ),
        latest_catalyst_source_at=_datetime_from_payload(
            "latest_catalyst_source_at",
            payload_dict["latest_catalyst_source_at"],
        ),
        official_source_count=_decimal_from_payload(
            "official_source_count",
            payload_dict["official_source_count"],
        ),
        source_count=_decimal_from_payload("source_count", payload_dict["source_count"]),
        fresh_source_count=_decimal_from_payload(
            "fresh_source_count",
            payload_dict["fresh_source_count"],
        ),
        latest_official_source_age_hours=_decimal_from_payload(
            "latest_official_source_age_hours",
            payload_dict["latest_official_source_age_hours"],
        ),
        latest_catalyst_source_age_hours=_decimal_from_payload(
            "latest_catalyst_source_age_hours",
            payload_dict["latest_catalyst_source_age_hours"],
        ),
        fresh_source_ratio=_decimal_from_payload(
            "fresh_source_ratio",
            payload_dict["fresh_source_ratio"],
        ),
        freshness_risk_score=_decimal_from_payload(
            "freshness_risk_score",
            payload_dict["freshness_risk_score"],
        ),
        source_status=_payload_string("source_status", payload_dict["source_status"]),
        recommended_research_action=_payload_string(
            "recommended_research_action",
            payload_dict["recommended_research_action"],
        ),
        reason_codes=_payload_reason_codes("reason_codes", payload_dict["reason_codes"]),
        paper_only=_payload_true("paper_only", payload_dict["paper_only"]),
        report_only=_payload_true("report_only", payload_dict["report_only"]),
        readonly=_payload_true("readonly", payload_dict["readonly"]),
    )


def _payload_dict(field_name: str, value: object) -> dict[str, object]:
    if type(value) is not dict:
        raise ValueError(f"{field_name} must be an object")
    payload: dict[str, object] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError(f"{field_name} keys must be strings")
        payload[key] = item
    return payload


def _require_payload_fields(
    payload: dict[str, object],
    fields: tuple[str, ...],
) -> None:
    expected = set(fields)
    observed = set(payload)
    if observed != expected:
        missing = sorted(expected - observed)
        extra = sorted(observed - expected)
        raise ValueError(f"payload fields mismatch missing={missing} extra={extra}")


def _payload_string(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    assert type(value) is str
    if _has_unsafe_public_token(value):
        raise ValueError(f"{field_name} has unsafe public payload value")
    return value


def _payload_true(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _payload_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return _normalize_row_reason_codes(field_name, tuple(value))


def _optional_decimal_from_payload(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _decimal_from_payload(field_name, value)


def _decimal_from_payload(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    return _normalize_decimal(field_name, decimal_value)


def _optional_datetime_from_payload(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _datetime_from_payload(field_name, value)


def _datetime_from_payload(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a datetime string") from exc
    return _as_utc(field_name, parsed)


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        if _has_unsafe_public_token(value):
            raise ValueError(f"{path or label} has unsafe public payload value")
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if type(value) is datetime:
        _as_utc(path or label, value)
        return
    if value is None or type(value) is bool:
        return
    if type(value) in (int, float):
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, dict):
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            if _has_unsafe_public_token(key):
                raise ValueError(f"unsafe public payload key in {label}: {key}")
            if key in PHASE_FLAG_FIELDS and nested_value is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_public_payload(label, nested_value, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, nested_value in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, nested_value, nested_path)
        return
    raise ValueError("public payload value is not JSON serializable")


def _has_unsafe_public_token(value: str) -> bool:
    lowered = value.lower()
    return any(token in lowered for token in UNSAFE_PUBLIC_TERMS)
