"""Phase 1 resolution evidence sufficiency score report."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_RESEARCH_PACKET_RESOLUTION_EVIDENCE_SUFFICIENCY_SCORE_V2_CONFIG_VERSION = (
    "research-packet-resolution-evidence-sufficiency-score-v2"
)

PASS_REASON = "research_packet_resolution_evidence_sufficiency_score_v2_passed"
MISSING_OFFICIAL_ANCHOR_REASON = (
    "research_packet_resolution_evidence_sufficiency_score_v2_missing_official_anchor"
)
INSUFFICIENT_SOURCE_FAMILIES_REASON = (
    "research_packet_resolution_evidence_sufficiency_score_v2_insufficient_source_families"
)
STALE_EVIDENCE_REASON = (
    "research_packet_resolution_evidence_sufficiency_score_v2_stale_evidence"
)
CONTRADICTION_REVIEW_MISSING_REASON = (
    "research_packet_resolution_evidence_sufficiency_score_v2_contradiction_review_missing"
)
UNRESOLVED_CONTRADICTION_ELEVATED_REASON = (
    "research_packet_resolution_evidence_sufficiency_score_v2_unresolved_contradiction_elevated"
)
RULE_CLARITY_WEAK_REASON = (
    "research_packet_resolution_evidence_sufficiency_score_v2_rule_clarity_weak"
)
SETTLEMENT_EVIDENCE_MISSING_REASON = (
    "research_packet_resolution_evidence_sufficiency_score_v2_settlement_evidence_missing"
)
SOURCE_ATTRIBUTION_WEAK_REASON = (
    "research_packet_resolution_evidence_sufficiency_score_v2_source_attribution_weak"
)
NO_PACKETS_REASON = (
    "research_packet_resolution_evidence_sufficiency_score_v2_no_packets"
)

ROW_REASON_CODES = (
    MISSING_OFFICIAL_ANCHOR_REASON,
    INSUFFICIENT_SOURCE_FAMILIES_REASON,
    STALE_EVIDENCE_REASON,
    CONTRADICTION_REVIEW_MISSING_REASON,
    UNRESOLVED_CONTRADICTION_ELEVATED_REASON,
    RULE_CLARITY_WEAK_REASON,
    SETTLEMENT_EVIDENCE_MISSING_REASON,
    SOURCE_ATTRIBUTION_WEAK_REASON,
)
REPORT_REASON_CODES = (PASS_REASON,) + ROW_REASON_CODES + (NO_PACKETS_REASON,)
INSUFFICIENT_REASONS = frozenset(
    (
        MISSING_OFFICIAL_ANCHOR_REASON,
        STALE_EVIDENCE_REASON,
        CONTRADICTION_REVIEW_MISSING_REASON,
        UNRESOLVED_CONTRADICTION_ELEVATED_REASON,
        RULE_CLARITY_WEAK_REASON,
        SETTLEMENT_EVIDENCE_MISSING_REASON,
    ),
)
REPORT_STATUSES = ("sufficient", "watch", "insufficient")
STATUS_RANK = {
    "insufficient": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "sufficient": Decimal("2.000000"),
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
COMPONENT_COUNT = Decimal("7.000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        _join_parts("li", "ve"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("sign", "ing"),
        _join_parts("muta", "tion"),
        _join_parts("bu", "y"),
        _join_parts("se", "ll"),
        _join_parts("tra", "de"),
    ),
)


@dataclass(frozen=True)
class ResearchPacketResolutionEvidenceSufficiencyScoreV2Config:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_RESOLUTION_EVIDENCE_SUFFICIENCY_SCORE_V2_CONFIG_VERSION
    )
    min_official_anchor_count: Decimal = Decimal("1.000000")
    min_independent_source_family_count: Decimal = Decimal("2.000000")
    max_evidence_age_seconds: Decimal = Decimal("3600.000000")
    max_unresolved_contradiction_severity: Decimal = Decimal("0.250000")
    min_rule_clarity_score: Decimal = Decimal("0.750000")
    min_settlement_evidence_count: Decimal = Decimal("1.000000")
    min_source_attribution_coverage_ratio: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketResolutionEvidenceSufficiencyScoreV2Config "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_RESOLUTION_EVIDENCE_SUFFICIENCY_SCORE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_official_anchor_count",
            "min_independent_source_family_count",
            "min_settlement_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_evidence_age_seconds",
            _normalize_positive_decimal(
                "max_evidence_age_seconds",
                self.max_evidence_age_seconds,
            ),
        )
        for field_name in (
            "max_unresolved_contradiction_severity",
            "min_rule_clarity_score",
            "min_source_attribution_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchPacketResolutionEvidenceSufficiencyScoreV2Packet:
    event_id: str
    packet_id: str
    event_category: str
    captured_at: datetime
    official_anchor_count: Decimal
    independent_source_family_count: Decimal
    freshest_evidence_observed_at: datetime
    contradiction_reviewed: bool
    unresolved_contradiction_severity: Decimal
    resolution_rule_clarity_score: Decimal
    settlement_evidence_count: Decimal
    source_attribution_coverage_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketResolutionEvidenceSufficiencyScoreV2Packet "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        for field_name in ("event_id", "packet_id", "event_category"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "captured_at", _as_utc("captured_at", self.captured_at))
        object.__setattr__(
            self,
            "freshest_evidence_observed_at",
            _as_utc("freshest_evidence_observed_at", self.freshest_evidence_observed_at),
        )
        for field_name in (
            "official_anchor_count",
            "independent_source_family_count",
            "settlement_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_bool("contradiction_reviewed", self.contradiction_reviewed)
        for field_name in (
            "unresolved_contradiction_severity",
            "resolution_rule_clarity_score",
            "source_attribution_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchPacketResolutionEvidenceSufficiencyScoreV2ReasonCodeCount:
    reason_code: str
    packet_count: Decimal
    packet_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketResolutionEvidenceSufficiencyScoreV2ReasonCodeCount "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_member("reason_code", self.reason_code, ROW_REASON_CODES)
        object.__setattr__(
            self,
            "packet_count",
            _normalize_positive_count("packet_count", self.packet_count),
        )
        object.__setattr__(
            self,
            "packet_ratio",
            _normalize_ratio("packet_ratio", self.packet_ratio),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchPacketResolutionEvidenceSufficiencyScoreV2Row:
    event_id: str
    packet_id: str
    event_category: str
    captured_at: datetime
    official_anchor_count: Decimal
    independent_source_family_count: Decimal
    freshest_evidence_observed_at: datetime
    evidence_age_seconds: Decimal
    contradiction_reviewed: bool
    unresolved_contradiction_severity: Decimal
    resolution_rule_clarity_score: Decimal
    settlement_evidence_count: Decimal
    source_attribution_coverage_ratio: Decimal
    official_anchor_score: Decimal
    source_family_score: Decimal
    freshness_score: Decimal
    contradiction_review_score: Decimal
    rule_clarity_component_score: Decimal
    settlement_evidence_score: Decimal
    source_attribution_score: Decimal
    sufficiency_score: Decimal
    sufficiency_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketResolutionEvidenceSufficiencyScoreV2Row "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        for field_name in ("event_id", "packet_id", "event_category"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "captured_at", _as_utc("captured_at", self.captured_at))
        object.__setattr__(
            self,
            "freshest_evidence_observed_at",
            _as_utc("freshest_evidence_observed_at", self.freshest_evidence_observed_at),
        )
        for field_name in (
            "official_anchor_count",
            "independent_source_family_count",
            "settlement_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_age_seconds",
            _normalize_nonnegative_decimal(
                "evidence_age_seconds",
                self.evidence_age_seconds,
            ),
        )
        _require_bool("contradiction_reviewed", self.contradiction_reviewed)
        for field_name in (
            "unresolved_contradiction_severity",
            "resolution_rule_clarity_score",
            "source_attribution_coverage_ratio",
            "official_anchor_score",
            "source_family_score",
            "freshness_score",
            "contradiction_review_score",
            "rule_clarity_component_score",
            "settlement_evidence_score",
            "source_attribution_score",
            "sufficiency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("sufficiency_status", self.sufficiency_status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        _require_hard_flags(self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _row_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_sha256_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_row(self)


@dataclass(frozen=True)
class ResearchPacketResolutionEvidenceSufficiencyScoreV2Report:
    generated_at: datetime
    config_version: str
    report_status: str
    packet_count: Decimal
    sufficient_packet_count: Decimal
    watch_packet_count: Decimal
    insufficient_packet_count: Decimal
    attention_packet_count: Decimal
    official_anchor_gap_packet_count: Decimal
    source_family_gap_packet_count: Decimal
    stale_evidence_packet_count: Decimal
    contradiction_review_gap_packet_count: Decimal
    unresolved_contradiction_packet_count: Decimal
    rule_clarity_gap_packet_count: Decimal
    settlement_evidence_gap_packet_count: Decimal
    source_attribution_gap_packet_count: Decimal
    average_sufficiency_score: Decimal
    min_sufficiency_score_observed: Decimal
    min_official_anchor_count: Decimal
    min_independent_source_family_count: Decimal
    max_evidence_age_seconds: Decimal
    max_unresolved_contradiction_severity: Decimal
    min_rule_clarity_score: Decimal
    min_settlement_evidence_count: Decimal
    min_source_attribution_coverage_ratio: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchPacketResolutionEvidenceSufficiencyScoreV2ReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchPacketResolutionEvidenceSufficiencyScoreV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchPacketResolutionEvidenceSufficiencyScoreV2Report "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_RESOLUTION_EVIDENCE_SUFFICIENCY_SCORE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_member("report_status", self.report_status, REPORT_STATUSES)
        for field_name in (
            "packet_count",
            "sufficient_packet_count",
            "watch_packet_count",
            "insufficient_packet_count",
            "attention_packet_count",
            "official_anchor_gap_packet_count",
            "source_family_gap_packet_count",
            "stale_evidence_packet_count",
            "contradiction_review_gap_packet_count",
            "unresolved_contradiction_packet_count",
            "rule_clarity_gap_packet_count",
            "settlement_evidence_gap_packet_count",
            "source_attribution_gap_packet_count",
            "min_official_anchor_count",
            "min_independent_source_family_count",
            "min_settlement_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_sufficiency_score",
            "min_sufficiency_score_observed",
            "max_unresolved_contradiction_severity",
            "min_rule_clarity_score",
            "min_source_attribution_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_evidence_age_seconds",
            _normalize_nonnegative_decimal(
                "max_evidence_age_seconds",
                self.max_evidence_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags(self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_sha256_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_report(self)


def build_research_packet_resolution_evidence_sufficiency_score_v2_report(
    packets: list[ResearchPacketResolutionEvidenceSufficiencyScoreV2Packet]
    | tuple[ResearchPacketResolutionEvidenceSufficiencyScoreV2Packet, ...],
    *,
    config: ResearchPacketResolutionEvidenceSufficiencyScoreV2Config,
    generated_at: datetime,
) -> ResearchPacketResolutionEvidenceSufficiencyScoreV2Report:
    if type(config) is not ResearchPacketResolutionEvidenceSufficiencyScoreV2Config:
        raise ValueError(
            "config must be a "
            "ResearchPacketResolutionEvidenceSufficiencyScoreV2Config",
        )
    _require_hard_flags(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_packets = _normalize_packets(packets)
    _validate_packet_times(normalized_packets, generated_at=generated_at_utc)
    rows = tuple(
        sorted(
            (
                _row_for_packet(packet, config=config, generated_at=generated_at_utc)
                for packet in normalized_packets
            ),
            key=_row_sort_key,
        ),
    )
    packet_count = _count_decimal(len(rows))
    attention_count = _count_decimal(
        sum(1 for row in rows if row.sufficiency_status != "sufficient"),
    )
    return ResearchPacketResolutionEvidenceSufficiencyScoreV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=_report_status(rows),
        packet_count=packet_count,
        sufficient_packet_count=_status_count(rows, "sufficient"),
        watch_packet_count=_status_count(rows, "watch"),
        insufficient_packet_count=_status_count(rows, "insufficient"),
        attention_packet_count=attention_count,
        official_anchor_gap_packet_count=_reason_count(
            rows,
            MISSING_OFFICIAL_ANCHOR_REASON,
        ),
        source_family_gap_packet_count=_reason_count(
            rows,
            INSUFFICIENT_SOURCE_FAMILIES_REASON,
        ),
        stale_evidence_packet_count=_reason_count(rows, STALE_EVIDENCE_REASON),
        contradiction_review_gap_packet_count=_reason_count(
            rows,
            CONTRADICTION_REVIEW_MISSING_REASON,
        ),
        unresolved_contradiction_packet_count=_reason_count(
            rows,
            UNRESOLVED_CONTRADICTION_ELEVATED_REASON,
        ),
        rule_clarity_gap_packet_count=_reason_count(rows, RULE_CLARITY_WEAK_REASON),
        settlement_evidence_gap_packet_count=_reason_count(
            rows,
            SETTLEMENT_EVIDENCE_MISSING_REASON,
        ),
        source_attribution_gap_packet_count=_reason_count(
            rows,
            SOURCE_ATTRIBUTION_WEAK_REASON,
        ),
        average_sufficiency_score=_average_decimal(
            tuple(row.sufficiency_score for row in rows),
        ),
        min_sufficiency_score_observed=min(
            (row.sufficiency_score for row in rows),
            default=ZERO,
        ),
        min_official_anchor_count=config.min_official_anchor_count,
        min_independent_source_family_count=config.min_independent_source_family_count,
        max_evidence_age_seconds=config.max_evidence_age_seconds,
        max_unresolved_contradiction_severity=(
            config.max_unresolved_contradiction_severity
        ),
        min_rule_clarity_score=config.min_rule_clarity_score,
        min_settlement_evidence_count=config.min_settlement_evidence_count,
        min_source_attribution_coverage_ratio=(
            config.min_source_attribution_coverage_ratio
        ),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_packet_resolution_evidence_sufficiency_score_v2_payload(
    value: object,
) -> dict[str, Any]:
    if type(value) is ResearchPacketResolutionEvidenceSufficiencyScoreV2Report:
        revalidated = _revalidate_report(value)
        payload = _payload_value(revalidated)
        validate_research_packet_resolution_evidence_sufficiency_score_v2_public_payload(
            payload,
        )
        return payload
    if type(value) is dict:
        validate_research_packet_resolution_evidence_sufficiency_score_v2_public_payload(
            value,
        )
        return dict(value)
    raise ValueError(
        "value must be a ResearchPacketResolutionEvidenceSufficiencyScoreV2Report "
        "or dict",
    )


def validate_research_packet_resolution_evidence_sufficiency_score_v2_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("public payload", payload)
    _require_public_payload_flags(payload)
    _reject_public_numeric_values(payload)
    rows_value = payload.get("rows")
    if type(rows_value) is not list:
        raise ValueError("rows must be a list")
    for row_payload in rows_value:
        if type(row_payload) is not dict:
            raise ValueError("rows must contain dict values")
        _require_public_payload_flags(row_payload)
        row_digest = _payload_required_string(row_payload, "derived_validation_digest")
        _require_sha256_digest("derived_validation_digest", row_digest)
        if row_digest != _public_row_digest(row_payload):
            raise ValueError("derived_validation_digest must match row payload")
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != _public_report_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    return True


def _row_for_packet(
    packet: ResearchPacketResolutionEvidenceSufficiencyScoreV2Packet,
    *,
    config: ResearchPacketResolutionEvidenceSufficiencyScoreV2Config,
    generated_at: datetime,
) -> ResearchPacketResolutionEvidenceSufficiencyScoreV2Row:
    evidence_age_seconds = _duration_seconds(
        generated_at,
        packet.freshest_evidence_observed_at,
    )
    official_anchor_score = _safe_ratio(
        packet.official_anchor_count,
        config.min_official_anchor_count,
    )
    source_family_score = _safe_ratio(
        packet.independent_source_family_count,
        config.min_independent_source_family_count,
    )
    freshness_score = ONE if evidence_age_seconds <= config.max_evidence_age_seconds else ZERO
    contradiction_review_score = _contradiction_review_score(packet, config)
    rule_clarity_component_score = _safe_ratio(
        packet.resolution_rule_clarity_score,
        config.min_rule_clarity_score,
    )
    settlement_evidence_score = _safe_ratio(
        packet.settlement_evidence_count,
        config.min_settlement_evidence_count,
    )
    source_attribution_score = packet.source_attribution_coverage_ratio
    sufficiency_score = _average_decimal(
        (
            official_anchor_score,
            source_family_score,
            freshness_score,
            contradiction_review_score,
            rule_clarity_component_score,
            settlement_evidence_score,
            source_attribution_score,
        ),
    )
    reason_codes = _row_reason_codes(
        packet=packet,
        config=config,
        evidence_age_seconds=evidence_age_seconds,
    )
    return ResearchPacketResolutionEvidenceSufficiencyScoreV2Row(
        event_id=packet.event_id,
        packet_id=packet.packet_id,
        event_category=packet.event_category,
        captured_at=packet.captured_at,
        official_anchor_count=packet.official_anchor_count,
        independent_source_family_count=packet.independent_source_family_count,
        freshest_evidence_observed_at=packet.freshest_evidence_observed_at,
        evidence_age_seconds=evidence_age_seconds,
        contradiction_reviewed=packet.contradiction_reviewed,
        unresolved_contradiction_severity=packet.unresolved_contradiction_severity,
        resolution_rule_clarity_score=packet.resolution_rule_clarity_score,
        settlement_evidence_count=packet.settlement_evidence_count,
        source_attribution_coverage_ratio=packet.source_attribution_coverage_ratio,
        official_anchor_score=official_anchor_score,
        source_family_score=source_family_score,
        freshness_score=freshness_score,
        contradiction_review_score=contradiction_review_score,
        rule_clarity_component_score=rule_clarity_component_score,
        settlement_evidence_score=settlement_evidence_score,
        source_attribution_score=source_attribution_score,
        sufficiency_score=sufficiency_score,
        sufficiency_status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    packet: ResearchPacketResolutionEvidenceSufficiencyScoreV2Packet,
    config: ResearchPacketResolutionEvidenceSufficiencyScoreV2Config,
    evidence_age_seconds: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if packet.official_anchor_count < config.min_official_anchor_count:
        reason_codes.append(MISSING_OFFICIAL_ANCHOR_REASON)
    if packet.independent_source_family_count < config.min_independent_source_family_count:
        reason_codes.append(INSUFFICIENT_SOURCE_FAMILIES_REASON)
    if evidence_age_seconds > config.max_evidence_age_seconds:
        reason_codes.append(STALE_EVIDENCE_REASON)
    if not packet.contradiction_reviewed:
        reason_codes.append(CONTRADICTION_REVIEW_MISSING_REASON)
    elif (
        packet.unresolved_contradiction_severity
        > config.max_unresolved_contradiction_severity
    ):
        reason_codes.append(UNRESOLVED_CONTRADICTION_ELEVATED_REASON)
    if packet.resolution_rule_clarity_score < config.min_rule_clarity_score:
        reason_codes.append(RULE_CLARITY_WEAK_REASON)
    if packet.settlement_evidence_count < config.min_settlement_evidence_count:
        reason_codes.append(SETTLEMENT_EVIDENCE_MISSING_REASON)
    if (
        packet.source_attribution_coverage_ratio
        < config.min_source_attribution_coverage_ratio
    ):
        reason_codes.append(SOURCE_ATTRIBUTION_WEAK_REASON)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return tuple(reason_codes)


def _contradiction_review_score(
    packet: ResearchPacketResolutionEvidenceSufficiencyScoreV2Packet,
    config: ResearchPacketResolutionEvidenceSufficiencyScoreV2Config,
) -> Decimal:
    if not packet.contradiction_reviewed:
        return ZERO
    if packet.unresolved_contradiction_severity <= config.max_unresolved_contradiction_severity:
        return ONE
    return max(ONE - packet.unresolved_contradiction_severity, ZERO)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in INSUFFICIENT_REASONS for reason_code in reason_codes):
        return "insufficient"
    if reason_codes == (PASS_REASON,):
        return "sufficient"
    return "watch"


def _report_status(
    rows: tuple[ResearchPacketResolutionEvidenceSufficiencyScoreV2Row, ...],
) -> str:
    if not rows:
        return "insufficient"
    if any(row.sufficiency_status == "insufficient" for row in rows):
        return "insufficient"
    if any(row.sufficiency_status == "watch" for row in rows):
        return "watch"
    return "sufficient"


def _report_reason_codes(
    rows: tuple[ResearchPacketResolutionEvidenceSufficiencyScoreV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_PACKETS_REASON,)
    present = frozenset(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != PASS_REASON
    )
    if not present:
        return (PASS_REASON,)
    return tuple(reason_code for reason_code in ROW_REASON_CODES if reason_code in present)


def _reason_code_counts(
    rows: tuple[ResearchPacketResolutionEvidenceSufficiencyScoreV2Row, ...],
) -> tuple[ResearchPacketResolutionEvidenceSufficiencyScoreV2ReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    return tuple(
        ResearchPacketResolutionEvidenceSufficiencyScoreV2ReasonCodeCount(
            reason_code=reason_code,
            packet_count=_reason_count(rows, reason_code),
            packet_ratio=_safe_ratio(_reason_count(rows, reason_code), row_count),
        )
        for reason_code in ROW_REASON_CODES
        if _reason_count(rows, reason_code) > ZERO
    )


def _normalize_packets(
    value: object,
) -> tuple[ResearchPacketResolutionEvidenceSufficiencyScoreV2Packet, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("packets must be a list or tuple")
    packets = tuple(value)
    seen: set[tuple[str, str]] = set()
    for packet in packets:
        if type(packet) is not ResearchPacketResolutionEvidenceSufficiencyScoreV2Packet:
            raise ValueError(
                "packets must contain "
                "ResearchPacketResolutionEvidenceSufficiencyScoreV2Packet values",
            )
        _require_hard_flags(packet)
        identity = (packet.event_id, packet.packet_id)
        if identity in seen:
            raise ValueError("packets must be unique by event_id and packet_id")
        seen.add(identity)
    return packets


def _normalize_rows(
    value: object,
) -> tuple[ResearchPacketResolutionEvidenceSufficiencyScoreV2Row, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchPacketResolutionEvidenceSufficiencyScoreV2Row:
            raise ValueError(
                "rows must contain ResearchPacketResolutionEvidenceSufficiencyScoreV2Row "
                "values",
            )
        _require_hard_flags(row)
        identity = (row.event_id, row.packet_id)
        if identity in seen:
            raise ValueError("rows must be unique by event_id and packet_id")
        seen.add(identity)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchPacketResolutionEvidenceSufficiencyScoreV2ReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    seen: set[str] = set()
    for item in counts:
        if type(item) is not ResearchPacketResolutionEvidenceSufficiencyScoreV2ReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchPacketResolutionEvidenceSufficiencyScoreV2ReasonCodeCount values",
            )
        _require_hard_flags(item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(item.reason_code)
    expected = tuple(
        item
        for reason_code in ROW_REASON_CODES
        for item in counts
        if item.reason_code == reason_code
    )
    if counts != expected:
        raise ValueError("reason_code_counts must use deterministic sequence")
    return counts


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_member(field_name, reason_code, allowed_values)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    expected = tuple(reason_code for reason_code in allowed_values if reason_code in seen)
    if reason_codes != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return reason_codes


def _validate_packet_times(
    packets: tuple[ResearchPacketResolutionEvidenceSufficiencyScoreV2Packet, ...],
    *,
    generated_at: datetime,
) -> None:
    for packet in packets:
        for field_name in ("captured_at", "freshest_evidence_observed_at"):
            value = getattr(packet, field_name)
            if value > generated_at:
                raise ValueError(f"{field_name} must not be after generated_at")


def _validate_row(row: ResearchPacketResolutionEvidenceSufficiencyScoreV2Row) -> None:
    if row.sufficiency_status != _row_status(row.reason_codes):
        raise ValueError("sufficiency_status must match reason_codes")
    expected_score = _average_decimal(
        (
            row.official_anchor_score,
            row.source_family_score,
            row.freshness_score,
            row.contradiction_review_score,
            row.rule_clarity_component_score,
            row.settlement_evidence_score,
            row.source_attribution_score,
        ),
    )
    if row.sufficiency_score != expected_score:
        raise ValueError("sufficiency_score must match component scores")
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest must match row values")


def _validate_report(
    report: ResearchPacketResolutionEvidenceSufficiencyScoreV2Report,
) -> None:
    if report.packet_count != _count_decimal(len(report.rows)):
        raise ValueError("packet_count must match rows")
    if report.sufficient_packet_count != _status_count(report.rows, "sufficient"):
        raise ValueError("sufficient_packet_count must match rows")
    if report.watch_packet_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_packet_count must match rows")
    if report.insufficient_packet_count != _status_count(report.rows, "insufficient"):
        raise ValueError("insufficient_packet_count must match rows")
    if report.attention_packet_count != _count_decimal(
        sum(1 for row in report.rows if row.sufficiency_status != "sufficient"),
    ):
        raise ValueError("attention_packet_count must match rows")
    expected_reason_counts = (
        (MISSING_OFFICIAL_ANCHOR_REASON, "official_anchor_gap_packet_count"),
        (INSUFFICIENT_SOURCE_FAMILIES_REASON, "source_family_gap_packet_count"),
        (STALE_EVIDENCE_REASON, "stale_evidence_packet_count"),
        (
            CONTRADICTION_REVIEW_MISSING_REASON,
            "contradiction_review_gap_packet_count",
        ),
        (
            UNRESOLVED_CONTRADICTION_ELEVATED_REASON,
            "unresolved_contradiction_packet_count",
        ),
        (RULE_CLARITY_WEAK_REASON, "rule_clarity_gap_packet_count"),
        (SETTLEMENT_EVIDENCE_MISSING_REASON, "settlement_evidence_gap_packet_count"),
        (SOURCE_ATTRIBUTION_WEAK_REASON, "source_attribution_gap_packet_count"),
    )
    for reason_code, field_name in expected_reason_counts:
        if getattr(report, field_name) != _reason_count(report.rows, reason_code):
            raise ValueError(f"{field_name} must match rows")
    if report.average_sufficiency_score != _average_decimal(
        tuple(row.sufficiency_score for row in report.rows),
    ):
        raise ValueError("average_sufficiency_score must match rows")
    if report.min_sufficiency_score_observed != min(
        (row.sufficiency_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("min_sufficiency_score_observed must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report values")


def _revalidate_reason_code_count(
    value: object,
) -> ResearchPacketResolutionEvidenceSufficiencyScoreV2ReasonCodeCount:
    if type(value) is not ResearchPacketResolutionEvidenceSufficiencyScoreV2ReasonCodeCount:
        raise ValueError("reason_code_counts must contain exact values")
    return ResearchPacketResolutionEvidenceSufficiencyScoreV2ReasonCodeCount(
        **_dataclass_kwargs(value),
    )


def _revalidate_row(
    value: object,
) -> ResearchPacketResolutionEvidenceSufficiencyScoreV2Row:
    if type(value) is not ResearchPacketResolutionEvidenceSufficiencyScoreV2Row:
        raise ValueError("rows must contain exact row values")
    return ResearchPacketResolutionEvidenceSufficiencyScoreV2Row(
        **_dataclass_kwargs(value),
    )


def _revalidate_report(
    value: ResearchPacketResolutionEvidenceSufficiencyScoreV2Report,
) -> ResearchPacketResolutionEvidenceSufficiencyScoreV2Report:
    if type(value) is not ResearchPacketResolutionEvidenceSufficiencyScoreV2Report:
        raise ValueError(
            "value must be a ResearchPacketResolutionEvidenceSufficiencyScoreV2Report",
        )
    kwargs = _dataclass_kwargs(value)
    kwargs["rows"] = tuple(_revalidate_row(row) for row in value.rows)
    kwargs["reason_code_counts"] = tuple(
        _revalidate_reason_code_count(item) for item in value.reason_code_counts
    )
    return ResearchPacketResolutionEvidenceSufficiencyScoreV2Report(**kwargs)


def _row_sort_key(
    row: ResearchPacketResolutionEvidenceSufficiencyScoreV2Row,
) -> tuple[Decimal, Decimal, str, str, str]:
    return (
        STATUS_RANK[row.sufficiency_status],
        row.sufficiency_score,
        row.event_category,
        row.event_id,
        row.packet_id,
    )


def _status_count(
    rows: tuple[ResearchPacketResolutionEvidenceSufficiencyScoreV2Row, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.sufficiency_status == status))


def _reason_count(
    rows: tuple[ResearchPacketResolutionEvidenceSufficiencyScoreV2Row, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _duration_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(Decimal(delta.total_seconds()))


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        return ONE
    with localcontext(DECIMAL_CONTEXT):
        return min(_quantize(numerator / denominator), ONE)


def _count_decimal(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_count(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return decimal_value


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a public string")
    lowered = value.lower()
    if "://" in lowered or "?" in lowered:
        raise ValueError(f"{field_name} must be a public string")
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} must be a public string")


def _require_hard_flags(value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError("value must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError("value must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError("value must be readonly")


def _payload_value(value: object) -> Any:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("payload decimal value must be exact")
        if not value.is_finite() or not value.same_quantum(QUANTUM):
            raise ValueError("payload decimal value must be six decimal places")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("payload datetime value must be exact")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("payload datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in (
            ResearchPacketResolutionEvidenceSufficiencyScoreV2Config,
            ResearchPacketResolutionEvidenceSufficiencyScoreV2Packet,
            ResearchPacketResolutionEvidenceSufficiencyScoreV2ReasonCodeCount,
            ResearchPacketResolutionEvidenceSufficiencyScoreV2Report,
            ResearchPacketResolutionEvidenceSufficiencyScoreV2Row,
        ):
            raise ValueError("payload must use supported dataclasses")
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        return {
            str(key): _payload_value(item)
            for key, item in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload value is not supported")


def _row_derived_validation_digest(
    row: ResearchPacketResolutionEvidenceSufficiencyScoreV2Row,
) -> str:
    payload = _payload_value(row)
    if type(payload) is not dict:
        raise ValueError("row payload must be a dict")
    payload.pop("derived_validation_digest", None)
    return _digest_payload(payload)


def _report_derived_validation_digest(
    report: ResearchPacketResolutionEvidenceSufficiencyScoreV2Report,
) -> str:
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a dict")
    payload.pop("derived_validation_digest", None)
    return _digest_payload(payload)


def _public_row_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    return _digest_payload(digest_payload)


def _public_report_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    return _digest_payload(digest_payload)


def _digest_payload(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be present")
    return value


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _reject_public_numeric_values(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) in (int, float, Decimal):
        raise ValueError("public payload numeric values must be strings")
    if type(value) is dict:
        for item in value.values():
            _reject_public_numeric_values(item)
        return
    if type(value) is list:
        for item in value:
            _reject_public_numeric_values(item)


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
) -> None:
    current_path = path or label
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{current_path} public keys must be strings")
            _reject_public_text(f"{current_path}.{key}", key)
            _reject_unsafe_public_payload(label, item, f"{current_path}.{key}")
        return
    if type(value) is list:
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(label, item, f"{current_path}[{index}]")
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(label, item, f"{current_path}[{index}]")
        return
    if type(value) is str:
        _reject_public_text(current_path, value)


def _reject_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if value.strip() != value or "://" in lowered or "?" in lowered:
        raise ValueError(f"{field_name} contains unsafe public text")
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public text")


def _dataclass_kwargs(value: object) -> dict[str, Any]:
    return {field.name: getattr(value, field.name) for field in fields(value)}


__all__ = (
    "DEFAULT_RESEARCH_PACKET_RESOLUTION_EVIDENCE_SUFFICIENCY_SCORE_V2_CONFIG_VERSION",
    "ResearchPacketResolutionEvidenceSufficiencyScoreV2Config",
    "ResearchPacketResolutionEvidenceSufficiencyScoreV2Packet",
    "ResearchPacketResolutionEvidenceSufficiencyScoreV2ReasonCodeCount",
    "ResearchPacketResolutionEvidenceSufficiencyScoreV2Report",
    "ResearchPacketResolutionEvidenceSufficiencyScoreV2Row",
    "build_research_packet_resolution_evidence_sufficiency_score_v2_report",
    "research_packet_resolution_evidence_sufficiency_score_v2_payload",
    "validate_research_packet_resolution_evidence_sufficiency_score_v2_public_payload",
)
