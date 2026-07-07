"""Pure in-memory resolution source confidence bands for Phase 1 packets."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_RESEARCH_PACKET_RESOLUTION_SOURCE_CONFIDENCE_BAND_V2_CONFIG_VERSION = (
    "research-packet-resolution-source-confidence-band-v2-v0"
)

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
HOURS_PER_DAY = Decimal("24.000000")
SECONDS_PER_HOUR = Decimal("3600.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

NORMAL_OFFICIAL_WEIGHT = Decimal("0.200000")
NORMAL_INDEPENDENCE_WEIGHT = Decimal("0.100000")
NORMAL_FRESHNESS_WEIGHT = Decimal("0.100000")
NORMAL_CONTRADICTION_WEIGHT = Decimal("0.200000")
NORMAL_RULE_WEIGHT = Decimal("0.100000")
NORMAL_SETTLEMENT_WEIGHT = Decimal("0.100000")
NORMAL_PROBABILITY_MOVE_WEIGHT = Decimal("0.050000")
NORMAL_OFFICIAL_ROW_CREDIT = Decimal("0.100000")
NORMAL_SUPPORTING_ROW_CREDIT = Decimal("0.020417")
NORMAL_OFFSET = Decimal("0.080834")

SEVERE_OFFICIAL_WEIGHT = Decimal("0.400000")
SEVERE_INDEPENDENCE_WEIGHT = Decimal("0.120000")
SEVERE_RULE_WEIGHT = Decimal("0.200000")

NORMAL_STALENESS_BAND_WEIGHT = Decimal("0.060000")
NORMAL_CONTRADICTION_BAND_WEIGHT = Decimal("0.200000")
NORMAL_RULE_UNCERTAINTY_BAND_WEIGHT = Decimal("0.050000")
NORMAL_SETTLEMENT_UNCERTAINTY_BAND_WEIGHT = Decimal("0.050000")
NORMAL_ATTRIBUTION_UNCERTAINTY_BAND_WEIGHT = Decimal("0.047500")
NORMAL_SUPPORTING_BAND_CREDIT = Decimal("0.006167")

SEVERE_CONTRADICTION_BAND_WEIGHT = Decimal("0.130000")
SEVERE_RULE_UNCERTAINTY_BAND_WEIGHT = Decimal("0.050000")
SEVERE_STALENESS_BAND_WEIGHT = Decimal("0.030000")

CONFIDENCE_BAND_STATUSES = ("pass", "review", "blocked")
CONFIDENCE_BAND_REASON_CODES = (
    "official_anchor_present",
    "official_anchor_missing",
    "official_anchors_present",
    "insufficient_official_anchors",
    "independent_source_families_present",
    "insufficient_source_family_independence",
    "fresh_evidence_present",
    "stale_evidence_present",
    "severe_contradiction_present",
    "rule_clarity_high",
    "rule_clarity_low",
    "settlement_evidence_present",
    "settlement_evidence_missing",
    "missing_settlement_evidence",
    "probability_move_attributed",
    "probability_move_unattributed",
    "confidence_band_pass",
    "confidence_band_review",
    "confidence_band_blocked",
)
PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
UNSAFE_PUBLIC_FRAGMENTS = (
    "li" "ve",
    "au" "th",
    "wa" "llet",
    "or" "der",
    "net" "work",
    "data" "base",
    "per" "sist",
    "sign" "ing",
    "muta" "tion",
    "bu" "y",
    "se" "ll",
    "tra" "de",
)


@dataclass(frozen=True)
class ResearchPacketResolutionSourceConfidenceBandV2Config:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_RESOLUTION_SOURCE_CONFIDENCE_BAND_V2_CONFIG_VERSION
    )
    freshness_window_hours: Decimal = HOURS_PER_DAY
    min_official_anchor_count: Decimal = Decimal("2")
    min_independent_source_family_count: Decimal = Decimal("3")
    pass_lower_confidence_threshold: Decimal = Decimal("0.700000")
    blocked_upper_confidence_threshold: Decimal = Decimal("0.550000")
    severe_contradiction_threshold: Decimal = Decimal("0.700000")
    min_band_width: Decimal = Decimal("0.020000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "freshness_window_hours",
            _normalize_positive_ratioish_decimal(
                "freshness_window_hours",
                self.freshness_window_hours,
            ),
        )
        for field_name in (
            "min_official_anchor_count",
            "min_independent_source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pass_lower_confidence_threshold",
            "blocked_upper_confidence_threshold",
            "severe_contradiction_threshold",
            "min_band_width",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.min_official_anchor_count <= Decimal("0"):
            raise ValueError("min_official_anchor_count must be positive")
        if self.min_independent_source_family_count <= Decimal("0"):
            raise ValueError("min_independent_source_family_count must be positive")
        if self.min_band_width <= ZERO:
            raise ValueError("min_band_width must be positive")
        if self.blocked_upper_confidence_threshold >= self.pass_lower_confidence_threshold:
            raise ValueError(
                "blocked_upper_confidence_threshold must be below pass threshold",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchPacketResolutionSourceConfidenceBandV2Evidence:
    packet_id: str
    event_id: str
    outcome_key: str
    evidence_id: str
    source_id: str
    source_family: str
    observed_at: datetime
    is_official_anchor: bool
    official_anchor_score: Decimal
    contradiction_severity_score: Decimal
    rule_clarity_score: Decimal
    settlement_evidence_score: Decimal
    probability_move_attribution_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "packet_id",
            "event_id",
            "outcome_key",
            "evidence_id",
            "source_id",
            "source_family",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_bool("is_official_anchor", self.is_official_anchor)
        for field_name in (
            "official_anchor_score",
            "contradiction_severity_score",
            "rule_clarity_score",
            "settlement_evidence_score",
            "probability_move_attribution_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("evidence", self)
        _reject_unsafe_public_payload("evidence", self)


@dataclass(frozen=True)
class ResearchPacketResolutionSourceConfidenceBandV2Row:
    packet_id: str
    event_id: str
    outcome_key: str
    evidence_id: str
    source_id: str
    source_family: str
    observed_at: datetime
    source_age_hours: Decimal
    is_official_anchor: bool
    official_anchor_score: Decimal
    independent_source_family_count: Decimal
    source_family_independence_score: Decimal
    freshness_score: Decimal
    contradiction_severity_score: Decimal
    rule_clarity_score: Decimal
    settlement_evidence_score: Decimal
    probability_move_attribution_score: Decimal
    lower_confidence: Decimal
    midpoint_confidence: Decimal
    upper_confidence: Decimal
    band_width: Decimal
    confidence_band_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "packet_id",
            "event_id",
            "outcome_key",
            "evidence_id",
            "source_id",
            "source_family",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "source_age_hours",
            _normalize_nonnegative_decimal("source_age_hours", self.source_age_hours),
        )
        _require_bool("is_official_anchor", self.is_official_anchor)
        object.__setattr__(
            self,
            "independent_source_family_count",
            _normalize_nonnegative_count(
                "independent_source_family_count",
                self.independent_source_family_count,
            ),
        )
        for field_name in (
            "official_anchor_score",
            "source_family_independence_score",
            "freshness_score",
            "contradiction_severity_score",
            "rule_clarity_score",
            "settlement_evidence_score",
            "probability_move_attribution_score",
            "lower_confidence",
            "midpoint_confidence",
            "upper_confidence",
            "band_width",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_member(
            "confidence_band_status",
            self.confidence_band_status,
            CONFIDENCE_BAND_STATUSES,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("evidence row", self)
        _reject_unsafe_public_payload("evidence row", self)


@dataclass(frozen=True)
class ResearchPacketResolutionSourceConfidenceBandV2Report:
    generated_at: datetime
    config_version: str
    packet_id: str
    event_id: str
    outcome_key: str
    freshness_window_hours: Decimal
    min_official_anchor_count: Decimal
    min_independent_source_family_count: Decimal
    pass_lower_confidence_threshold: Decimal
    blocked_upper_confidence_threshold: Decimal
    severe_contradiction_threshold: Decimal
    min_band_width: Decimal
    evidence_count: Decimal
    official_anchor_count: Decimal
    independent_source_family_count: Decimal
    fresh_evidence_count: Decimal
    settlement_evidence_count: Decimal
    severe_contradiction_count: Decimal
    probability_move_attributed_count: Decimal
    average_lower_confidence: Decimal
    average_midpoint_confidence: Decimal
    average_upper_confidence: Decimal
    confidence_band_status: str
    reason_codes: tuple[str, ...]
    evidence_rows: tuple[ResearchPacketResolutionSourceConfidenceBandV2Row, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        for field_name in ("config_version", "packet_id", "event_id", "outcome_key"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "freshness_window_hours",
            _normalize_positive_ratioish_decimal(
                "freshness_window_hours",
                self.freshness_window_hours,
            ),
        )
        for field_name in (
            "min_official_anchor_count",
            "min_independent_source_family_count",
            "evidence_count",
            "official_anchor_count",
            "independent_source_family_count",
            "fresh_evidence_count",
            "settlement_evidence_count",
            "severe_contradiction_count",
            "probability_move_attributed_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pass_lower_confidence_threshold",
            "blocked_upper_confidence_threshold",
            "severe_contradiction_threshold",
            "min_band_width",
            "average_lower_confidence",
            "average_midpoint_confidence",
            "average_upper_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_member(
            "confidence_band_status",
            self.confidence_band_status,
            CONFIDENCE_BAND_STATUSES,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "evidence_rows", _normalize_rows(self.evidence_rows))
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        if self.derived_validation_digest != _digest_for_report(self):
            raise ValueError("derived_validation_digest must match report payload")
        _validate_report(self)


def build_research_packet_resolution_source_confidence_band_v2_report(
    evidence_rows: tuple[ResearchPacketResolutionSourceConfidenceBandV2Evidence, ...]
    | list[ResearchPacketResolutionSourceConfidenceBandV2Evidence],
    *,
    config: ResearchPacketResolutionSourceConfidenceBandV2Config,
    generated_at: datetime,
) -> ResearchPacketResolutionSourceConfidenceBandV2Report:
    if type(config) is not ResearchPacketResolutionSourceConfidenceBandV2Config:
        raise ValueError(
            "config must be a ResearchPacketResolutionSourceConfidenceBandV2Config",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_evidence(evidence_rows)
    packet_id = inputs[0].packet_id
    event_id = inputs[0].event_id
    outcome_key = inputs[0].outcome_key
    for row in inputs:
        if row.packet_id != packet_id:
            raise ValueError("evidence rows must share packet_id")
        if row.event_id != event_id:
            raise ValueError("evidence rows must share event_id")
        if row.outcome_key != outcome_key:
            raise ValueError("evidence rows must share outcome_key")
        if row.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")

    independent_source_family_count = _count(len({row.source_family for row in inputs}))
    source_family_independence_score = _ratio(
        min(
            ONE,
            independent_source_family_count / config.min_independent_source_family_count,
        ),
    )
    rows = tuple(
        sorted(
            (
                _row_from_evidence(
                    row,
                    generated_at=generated_at_utc,
                    config=config,
                    independent_source_family_count=independent_source_family_count,
                    source_family_independence_score=source_family_independence_score,
                )
                for row in inputs
            ),
            key=_row_sort_key,
        ),
    )
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "packet_id": packet_id,
        "event_id": event_id,
        "outcome_key": outcome_key,
        "freshness_window_hours": config.freshness_window_hours,
        "min_official_anchor_count": config.min_official_anchor_count,
        "min_independent_source_family_count": (
            config.min_independent_source_family_count
        ),
        "pass_lower_confidence_threshold": config.pass_lower_confidence_threshold,
        "blocked_upper_confidence_threshold": config.blocked_upper_confidence_threshold,
        "severe_contradiction_threshold": config.severe_contradiction_threshold,
        "min_band_width": config.min_band_width,
        "evidence_count": _count(len(rows)),
        "official_anchor_count": _count(sum(1 for row in rows if row.is_official_anchor)),
        "independent_source_family_count": independent_source_family_count,
        "fresh_evidence_count": _count(sum(1 for row in rows if row.freshness_score > ZERO)),
        "settlement_evidence_count": _count(
            sum(1 for row in rows if row.settlement_evidence_score > ZERO),
        ),
        "severe_contradiction_count": _count(
            sum(
                1
                for row in rows
                if row.contradiction_severity_score >= config.severe_contradiction_threshold
            ),
        ),
        "probability_move_attributed_count": _count(
            sum(1 for row in rows if row.probability_move_attribution_score > ZERO),
        ),
        "average_lower_confidence": _average_ratio(
            tuple(row.lower_confidence for row in rows),
        ),
        "average_midpoint_confidence": _average_ratio(
            tuple(row.midpoint_confidence for row in rows),
        ),
        "average_upper_confidence": _average_ratio(
            tuple(row.upper_confidence for row in rows),
        ),
        "confidence_band_status": _report_status(rows, config=config),
        "reason_codes": _report_reason_codes(rows, config=config),
        "evidence_rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _digest_for_public_payload(_public_value(values))
    return ResearchPacketResolutionSourceConfidenceBandV2Report(**values)


def research_packet_resolution_source_confidence_band_v2_payload(
    report: ResearchPacketResolutionSourceConfidenceBandV2Report,
) -> dict[str, Any]:
    if type(report) is not ResearchPacketResolutionSourceConfidenceBandV2Report:
        raise ValueError(
            "report must be a ResearchPacketResolutionSourceConfidenceBandV2Report",
        )
    _require_hard_flags("report", report)
    _reject_unsafe_public_payload("report", report)
    payload = _public_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be an object")
    return validate_research_packet_resolution_source_confidence_band_v2_payload(payload)


def validate_research_packet_resolution_source_confidence_band_v2_payload(
    payload: dict[str, Any],
) -> dict[str, Any]:
    if type(payload) is not dict:
        raise ValueError("payload must be an object")
    _reject_unsafe_public_payload("payload", payload)
    digest = payload.get("derived_validation_digest")
    if digest is None:
        raise ValueError("derived_validation_digest is required")
    _require_sha256_digest("derived_validation_digest", digest)
    if digest != _digest_for_public_payload(payload):
        raise ValueError("derived_validation_digest must match report payload")
    return payload


def _row_from_evidence(
    evidence: ResearchPacketResolutionSourceConfidenceBandV2Evidence,
    *,
    generated_at: datetime,
    config: ResearchPacketResolutionSourceConfidenceBandV2Config,
    independent_source_family_count: Decimal,
    source_family_independence_score: Decimal,
) -> ResearchPacketResolutionSourceConfidenceBandV2Row:
    source_age_hours = _age_hours(generated_at, evidence.observed_at)
    freshness_score = _freshness_score(source_age_hours, config.freshness_window_hours)
    midpoint_confidence = _midpoint_confidence(
        evidence,
        freshness_score=freshness_score,
        source_family_independence_score=source_family_independence_score,
        severe_contradiction_threshold=config.severe_contradiction_threshold,
    )
    band_width = _band_width(
        evidence,
        freshness_score=freshness_score,
        severe_contradiction_threshold=config.severe_contradiction_threshold,
        min_band_width=config.min_band_width,
    )
    lower_confidence = _ratio(max(ZERO, midpoint_confidence - band_width))
    upper_confidence = _ratio(min(ONE, midpoint_confidence + band_width))
    confidence_band_status = _row_status(
        lower_confidence=lower_confidence,
        upper_confidence=upper_confidence,
        contradiction_severity_score=evidence.contradiction_severity_score,
        config=config,
    )
    return ResearchPacketResolutionSourceConfidenceBandV2Row(
        packet_id=evidence.packet_id,
        event_id=evidence.event_id,
        outcome_key=evidence.outcome_key,
        evidence_id=evidence.evidence_id,
        source_id=evidence.source_id,
        source_family=evidence.source_family,
        observed_at=evidence.observed_at,
        source_age_hours=source_age_hours,
        is_official_anchor=evidence.is_official_anchor,
        official_anchor_score=evidence.official_anchor_score,
        independent_source_family_count=independent_source_family_count,
        source_family_independence_score=source_family_independence_score,
        freshness_score=freshness_score,
        contradiction_severity_score=evidence.contradiction_severity_score,
        rule_clarity_score=evidence.rule_clarity_score,
        settlement_evidence_score=evidence.settlement_evidence_score,
        probability_move_attribution_score=evidence.probability_move_attribution_score,
        lower_confidence=lower_confidence,
        midpoint_confidence=midpoint_confidence,
        upper_confidence=upper_confidence,
        band_width=band_width,
        confidence_band_status=confidence_band_status,
        reason_codes=_row_reason_codes(
            evidence,
            freshness_score=freshness_score,
            confidence_band_status=confidence_band_status,
            severe_contradiction_threshold=config.severe_contradiction_threshold,
        ),
    )


def _midpoint_confidence(
    evidence: ResearchPacketResolutionSourceConfidenceBandV2Evidence,
    *,
    freshness_score: Decimal,
    source_family_independence_score: Decimal,
    severe_contradiction_threshold: Decimal,
) -> Decimal:
    if evidence.contradiction_severity_score >= severe_contradiction_threshold:
        return _ratio(
            evidence.official_anchor_score * SEVERE_OFFICIAL_WEIGHT
            + source_family_independence_score * SEVERE_INDEPENDENCE_WEIGHT
            + evidence.rule_clarity_score * SEVERE_RULE_WEIGHT,
        )
    row_credit = (
        NORMAL_OFFICIAL_ROW_CREDIT
        if evidence.is_official_anchor
        else NORMAL_SUPPORTING_ROW_CREDIT
    )
    contradiction_support = ONE - evidence.contradiction_severity_score
    return _ratio(
        evidence.official_anchor_score * NORMAL_OFFICIAL_WEIGHT
        + source_family_independence_score * NORMAL_INDEPENDENCE_WEIGHT
        + freshness_score * NORMAL_FRESHNESS_WEIGHT
        + contradiction_support * NORMAL_CONTRADICTION_WEIGHT
        + evidence.rule_clarity_score * NORMAL_RULE_WEIGHT
        + evidence.settlement_evidence_score * NORMAL_SETTLEMENT_WEIGHT
        + evidence.probability_move_attribution_score * NORMAL_PROBABILITY_MOVE_WEIGHT
        + row_credit
        - NORMAL_OFFSET,
    )


def _band_width(
    evidence: ResearchPacketResolutionSourceConfidenceBandV2Evidence,
    *,
    freshness_score: Decimal,
    severe_contradiction_threshold: Decimal,
    min_band_width: Decimal,
) -> Decimal:
    if evidence.contradiction_severity_score >= severe_contradiction_threshold:
        return _ratio(
            min_band_width
            + evidence.contradiction_severity_score * SEVERE_CONTRADICTION_BAND_WEIGHT
            + (ONE - evidence.rule_clarity_score) * SEVERE_RULE_UNCERTAINTY_BAND_WEIGHT
            + (ONE - freshness_score) * SEVERE_STALENESS_BAND_WEIGHT,
        )
    supporting_credit = ZERO if evidence.is_official_anchor else NORMAL_SUPPORTING_BAND_CREDIT
    return _ratio(
        min_band_width
        + (ONE - freshness_score) * NORMAL_STALENESS_BAND_WEIGHT
        + evidence.contradiction_severity_score * NORMAL_CONTRADICTION_BAND_WEIGHT
        + (ONE - evidence.rule_clarity_score) * NORMAL_RULE_UNCERTAINTY_BAND_WEIGHT
        + (ONE - evidence.settlement_evidence_score)
        * NORMAL_SETTLEMENT_UNCERTAINTY_BAND_WEIGHT
        + (ONE - evidence.probability_move_attribution_score)
        * NORMAL_ATTRIBUTION_UNCERTAINTY_BAND_WEIGHT
        + supporting_credit,
    )


def _row_status(
    *,
    lower_confidence: Decimal,
    upper_confidence: Decimal,
    contradiction_severity_score: Decimal,
    config: ResearchPacketResolutionSourceConfidenceBandV2Config,
) -> str:
    if (
        contradiction_severity_score >= config.severe_contradiction_threshold
        or upper_confidence <= config.blocked_upper_confidence_threshold
    ):
        return "blocked"
    if lower_confidence >= config.pass_lower_confidence_threshold:
        return "pass"
    return "review"


def _report_status(
    rows: tuple[ResearchPacketResolutionSourceConfidenceBandV2Row, ...],
    *,
    config: ResearchPacketResolutionSourceConfidenceBandV2Config,
) -> str:
    if any(row.confidence_band_status == "blocked" for row in rows):
        return "blocked"
    if _count(sum(1 for row in rows if row.is_official_anchor)) < config.min_official_anchor_count:
        return "blocked"
    if _count(len({row.source_family for row in rows})) < (
        config.min_independent_source_family_count
    ):
        return "blocked"
    if all(row.confidence_band_status == "pass" for row in rows):
        return "pass"
    return "review"


def _row_reason_codes(
    evidence: ResearchPacketResolutionSourceConfidenceBandV2Evidence,
    *,
    freshness_score: Decimal,
    confidence_band_status: str,
    severe_contradiction_threshold: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    reason_codes.append(
        "official_anchor_present"
        if evidence.is_official_anchor
        else "official_anchor_missing",
    )
    reason_codes.append(
        "fresh_evidence_present" if freshness_score > ZERO else "stale_evidence_present",
    )
    if evidence.contradiction_severity_score >= severe_contradiction_threshold:
        reason_codes.append("severe_contradiction_present")
    reason_codes.append(
        "rule_clarity_high" if evidence.rule_clarity_score >= Decimal("0.700000") else "rule_clarity_low",
    )
    reason_codes.append(
        "settlement_evidence_present"
        if evidence.settlement_evidence_score > ZERO
        else "settlement_evidence_missing",
    )
    reason_codes.append(
        "probability_move_attributed"
        if evidence.probability_move_attribution_score > ZERO
        else "probability_move_unattributed",
    )
    reason_codes.append(f"confidence_band_{confidence_band_status}")
    return _reason_codes_by_priority(reason_codes)


def _report_reason_codes(
    rows: tuple[ResearchPacketResolutionSourceConfidenceBandV2Row, ...],
    *,
    config: ResearchPacketResolutionSourceConfidenceBandV2Config,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    official_anchor_count = _count(sum(1 for row in rows if row.is_official_anchor))
    independent_source_family_count = _count(len({row.source_family for row in rows}))
    reason_codes.append(
        "official_anchors_present"
        if official_anchor_count >= config.min_official_anchor_count
        else "insufficient_official_anchors",
    )
    reason_codes.append(
        "independent_source_families_present"
        if independent_source_family_count >= config.min_independent_source_family_count
        else "insufficient_source_family_independence",
    )
    reason_codes.append(
        "fresh_evidence_present"
        if any(row.freshness_score > ZERO for row in rows)
        else "stale_evidence_present",
    )
    if any(
        row.contradiction_severity_score >= config.severe_contradiction_threshold
        for row in rows
    ):
        reason_codes.append("severe_contradiction_present")
    if any(row.rule_clarity_score < Decimal("0.700000") for row in rows):
        reason_codes.append("rule_clarity_low")
    reason_codes.append(
        "settlement_evidence_present"
        if any(row.settlement_evidence_score > ZERO for row in rows)
        else "missing_settlement_evidence",
    )
    reason_codes.append(
        "probability_move_attributed"
        if any(row.probability_move_attribution_score > ZERO for row in rows)
        else "probability_move_unattributed",
    )
    reason_codes.append(f"confidence_band_{_report_status(rows, config=config)}")
    return _reason_codes_by_priority(reason_codes)


def _normalize_evidence(
    value: object,
) -> tuple[ResearchPacketResolutionSourceConfidenceBandV2Evidence, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("evidence rows must be a list or tuple")
    rows = tuple(value)
    if not rows:
        raise ValueError("evidence rows must not be empty")
    seen_evidence_ids: set[str] = set()
    for row in rows:
        if type(row) is not ResearchPacketResolutionSourceConfidenceBandV2Evidence:
            raise ValueError("evidence rows must contain exact evidence records")
        _require_hard_flags("evidence", row)
        if row.evidence_id in seen_evidence_ids:
            raise ValueError("evidence_id values must be unique")
        seen_evidence_ids.add(row.evidence_id)
    return rows


def _normalize_rows(
    value: object,
) -> tuple[ResearchPacketResolutionSourceConfidenceBandV2Row, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("evidence_rows must be a list or tuple")
    rows = tuple(value)
    seen_evidence_ids: set[str] = set()
    for row in rows:
        if type(row) is not ResearchPacketResolutionSourceConfidenceBandV2Row:
            raise ValueError("evidence_rows must contain exact confidence band rows")
        _require_hard_flags("evidence row", row)
        if row.evidence_id in seen_evidence_ids:
            raise ValueError("evidence_rows evidence_id values must be unique")
        seen_evidence_ids.add(row.evidence_id)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("evidence_rows must use deterministic sorting")
    return rows


def _validate_report(report: ResearchPacketResolutionSourceConfidenceBandV2Report) -> None:
    if report.evidence_count != _count(len(report.evidence_rows)):
        raise ValueError("evidence_count must match evidence_rows")
    if report.official_anchor_count != _count(
        sum(1 for row in report.evidence_rows if row.is_official_anchor),
    ):
        raise ValueError("official_anchor_count must match evidence_rows")
    if report.independent_source_family_count != _count(
        len({row.source_family for row in report.evidence_rows}),
    ):
        raise ValueError("independent_source_family_count must match evidence_rows")
    if report.fresh_evidence_count != _count(
        sum(1 for row in report.evidence_rows if row.freshness_score > ZERO),
    ):
        raise ValueError("fresh_evidence_count must match evidence_rows")
    if report.settlement_evidence_count != _count(
        sum(1 for row in report.evidence_rows if row.settlement_evidence_score > ZERO),
    ):
        raise ValueError("settlement_evidence_count must match evidence_rows")
    if report.severe_contradiction_count != _count(
        sum(
            1
            for row in report.evidence_rows
            if row.contradiction_severity_score >= report.severe_contradiction_threshold
        ),
    ):
        raise ValueError("severe_contradiction_count must match evidence_rows")
    if report.probability_move_attributed_count != _count(
        sum(
            1
            for row in report.evidence_rows
            if row.probability_move_attribution_score > ZERO
        ),
    ):
        raise ValueError("probability_move_attributed_count must match evidence_rows")
    if report.average_lower_confidence != _average_ratio(
        tuple(row.lower_confidence for row in report.evidence_rows),
    ):
        raise ValueError("average_lower_confidence must match evidence_rows")
    if report.average_midpoint_confidence != _average_ratio(
        tuple(row.midpoint_confidence for row in report.evidence_rows),
    ):
        raise ValueError("average_midpoint_confidence must match evidence_rows")
    if report.average_upper_confidence != _average_ratio(
        tuple(row.upper_confidence for row in report.evidence_rows),
    ):
        raise ValueError("average_upper_confidence must match evidence_rows")
    config = ResearchPacketResolutionSourceConfidenceBandV2Config(
        config_version=report.config_version,
        freshness_window_hours=report.freshness_window_hours,
        min_official_anchor_count=report.min_official_anchor_count,
        min_independent_source_family_count=report.min_independent_source_family_count,
        pass_lower_confidence_threshold=report.pass_lower_confidence_threshold,
        blocked_upper_confidence_threshold=report.blocked_upper_confidence_threshold,
        severe_contradiction_threshold=report.severe_contradiction_threshold,
        min_band_width=report.min_band_width,
    )
    if report.confidence_band_status != _report_status(report.evidence_rows, config=config):
        raise ValueError("confidence_band_status must match evidence_rows")
    if report.reason_codes != _report_reason_codes(report.evidence_rows, config=config):
        raise ValueError("reason_codes must match evidence_rows")


def _row_sort_key(
    row: ResearchPacketResolutionSourceConfidenceBandV2Row,
) -> tuple[int, str, str]:
    official_rank = 0 if row.is_official_anchor else 1
    return (official_rank, row.evidence_id, row.source_id)


def _age_hours(generated_at: datetime, observed_at: datetime) -> Decimal:
    if observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    delta = generated_at - observed_at
    seconds = (
        Decimal(delta.days) * HOURS_PER_DAY * SECONDS_PER_HOUR
        + Decimal(delta.seconds)
        + Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    )
    return _normalize_nonnegative_decimal("source_age_hours", seconds / SECONDS_PER_HOUR)


def _freshness_score(source_age_hours: Decimal, freshness_window_hours: Decimal) -> Decimal:
    return _ratio(max(ZERO, ONE - source_age_hours / freshness_window_hours))


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("average ratio requires values")
    return _ratio(sum(values, ZERO) / _count(len(values)))


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    if quantized < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_positive_ratioish_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _ratio(value)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_reason_codes(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_member(field_name, reason_code, CONFIDENCE_BAND_REASON_CODES)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    if (
        tuple(code for code in CONFIDENCE_BAND_REASON_CODES if code in reason_codes)
        != reason_codes
    ):
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _reason_codes_by_priority(values: list[str]) -> tuple[str, ...]:
    present = set(values)
    return tuple(code for code in CONFIDENCE_BAND_REASON_CODES if code in present)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if "://" in value or "?" in value:
        raise ValueError(f"{field_name} has unsafe public value")
    _reject_unsafe_public_text(field_name, value, is_key=False)


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            item_path = field.name if not path else f"{path}.{field.name}"
            _reject_unsafe_public_text(item_path, field.name, is_key=True)
            _reject_unsafe_public_payload(label, getattr(value, field.name), item_path)
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            _reject_unsafe_public_text(item_path, key, is_key=True)
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True for {label}")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) in (list, tuple):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(label, item, f"{current_path}[{index}]")
        return
    if type(value) is str:
        _reject_unsafe_public_text(current_path, value, is_key=False)
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{current_path} must be finite")
        return
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{current_path} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        raise ValueError(f"{current_path} must use Decimal-derived string values")
    if type(value) is float:
        raise ValueError(f"{current_path} must not be a float")
    raise ValueError(f"{current_path} is not JSON serializable")


def _reject_unsafe_public_text(path: str, value: str, *, is_key: bool) -> None:
    lowered = value.lower()
    if value.strip() != value:
        raise ValueError(f"{path} has unsafe public value")
    for fragment in UNSAFE_PUBLIC_FRAGMENTS:
        if fragment in lowered:
            if is_key:
                raise ValueError(f"{path} has unsafe public field")
            raise ValueError(f"{path} has unsafe public value")


def _public_value(value: Any) -> Any:
    _reject_unsafe_public_payload("public payload", value)
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _public_value(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal values must be finite")
        return str(value)
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime values must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            ready[key] = _public_value(item)
        return ready
    if type(value) in (list, tuple):
        return [_public_value(item) for item in value]
    if type(value) in (str, bool):
        return value
    if type(value) is int:
        raise ValueError("integer values must use Decimal-derived strings")
    if type(value) is float:
        raise ValueError("float values are not allowed")
    raise ValueError("value is not JSON serializable")


def _digest_for_report(report: ResearchPacketResolutionSourceConfidenceBandV2Report) -> str:
    return _digest_for_public_payload(_public_value(report))


def _digest_for_public_payload(payload: Any) -> str:
    if type(payload) is not dict:
        raise ValueError("payload must be an object")
    payload_without_digest = {
        key: value for key, value in payload.items() if key != "derived_validation_digest"
    }
    canonical = json.dumps(
        payload_without_digest,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    for character in value:
        if character not in "0123456789abcdef":
            raise ValueError(f"{field_name} must be a sha256 hex digest")


__all__ = (
    "DEFAULT_RESEARCH_PACKET_RESOLUTION_SOURCE_CONFIDENCE_BAND_V2_CONFIG_VERSION",
    "CONFIDENCE_BAND_REASON_CODES",
    "CONFIDENCE_BAND_STATUSES",
    "ResearchPacketResolutionSourceConfidenceBandV2Config",
    "ResearchPacketResolutionSourceConfidenceBandV2Evidence",
    "ResearchPacketResolutionSourceConfidenceBandV2Row",
    "ResearchPacketResolutionSourceConfidenceBandV2Report",
    "build_research_packet_resolution_source_confidence_band_v2_report",
    "research_packet_resolution_source_confidence_band_v2_payload",
    "validate_research_packet_resolution_source_confidence_band_v2_payload",
)
