"""Pure Phase 1 source freshness alert score report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass, replace
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_PACKET_SOURCE_FRESHNESS_ALERT_SCORE_V2_CONFIG_VERSION = (
    "research-packet-source-freshness-alert-score-v2-v0"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SHA256_HEX_LENGTH = 64

SOURCE_AGE_WEIGHT = Decimal("0.200000")
OFFICIAL_SOURCE_LAG_WEIGHT = Decimal("0.200000")
INDEPENDENT_CORROBORATION_AGE_WEIGHT = Decimal("0.150000")
CONTRADICTION_UNRESOLVED_AGE_WEIGHT = Decimal("0.150000")
PROBABILITY_MOVE_WEIGHT = Decimal("0.150000")
CLOSE_URGENCY_WEIGHT = Decimal("0.150000")

STATUSES = ("pass", "watch", "blocked")
REASON_CODES = (
    "source_freshness_alert_no_inputs",
    "source_freshness_alert_status_pass",
    "source_freshness_alert_status_watch",
    "source_freshness_alert_status_blocked",
    "stale_source_age",
    "official_source_lag",
    "stale_independent_corroboration",
    "unresolved_contradiction",
    "material_probability_move",
    "close_resolution_urgency",
)
DETAIL_REASON_CODES = REASON_CODES[4:]
REPORT_NEXT_STEPS = {
    "pass": "source_freshness_alerts_clear_for_paper_report",
    "watch": "review_source_freshness_before_paper_report",
    "blocked": "refresh_sources_before_paper_report",
}
ROW_ACTIONS = {
    "pass": "source_freshness_clear",
    "watch": "review_source_freshness",
    "blocked": "refresh_source_evidence_first",
}
HARD_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
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

__all__ = (
    "DEFAULT_RESEARCH_PACKET_SOURCE_FRESHNESS_ALERT_SCORE_V2_CONFIG_VERSION",
    "REASON_CODES",
    "ResearchPacketSourceFreshnessAlertScoreV2Config",
    "ResearchPacketSourceFreshnessAlertScoreV2Input",
    "ResearchPacketSourceFreshnessAlertScoreV2Report",
    "ResearchPacketSourceFreshnessAlertScoreV2Row",
    "STATUSES",
    "build_research_packet_source_freshness_alert_score_v2_report",
    "research_packet_source_freshness_alert_score_v2_payload",
)


@dataclass(frozen=True)
class ResearchPacketSourceFreshnessAlertScoreV2Config:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_SOURCE_FRESHNESS_ALERT_SCORE_V2_CONFIG_VERSION
    )
    fresh_source_age_hours: Decimal = Decimal("6.000000")
    stale_source_age_span_hours: Decimal = Decimal("42.000000")
    allowed_official_source_lag_hours: Decimal = Decimal("12.000000")
    official_source_lag_span_hours: Decimal = Decimal("60.000000")
    fresh_independent_corroboration_age_hours: Decimal = Decimal("12.000000")
    stale_independent_corroboration_span_hours: Decimal = Decimal("60.000000")
    fresh_contradiction_resolution_hours: Decimal = Decimal("0.000000")
    stale_contradiction_unresolved_span_hours: Decimal = Decimal("24.000000")
    material_probability_move_threshold: Decimal = Decimal("0.050000")
    close_resolution_hours: Decimal = Decimal("24.000000")
    safe_resolution_hours: Decimal = Decimal("168.000000")
    blocked_priority_score: Decimal = Decimal("0.750000")
    watch_priority_score: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceFreshnessAlertScoreV2Config:
            raise ValueError("config must be a ResearchPacketSourceFreshnessAlertScoreV2Config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_SOURCE_FRESHNESS_ALERT_SCORE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "fresh_source_age_hours",
            "allowed_official_source_lag_hours",
            "fresh_independent_corroboration_age_hours",
            "fresh_contradiction_resolution_hours",
            "close_resolution_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "stale_source_age_span_hours",
            "official_source_lag_span_hours",
            "stale_independent_corroboration_span_hours",
            "stale_contradiction_unresolved_span_hours",
            "safe_resolution_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "material_probability_move_threshold",
            "blocked_priority_score",
            "watch_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.material_probability_move_threshold >= ONE:
            raise ValueError("material_probability_move_threshold must be below one")
        if self.close_resolution_hours >= self.safe_resolution_hours:
            raise ValueError("close_resolution_hours must be below safe_resolution_hours")
        if self.watch_priority_score >= self.blocked_priority_score:
            raise ValueError("watch_priority_score must be below blocked_priority_score")
        _require_hard_flags(self)
        _reject_unsafe_public_payload("config", asdict(self))


@dataclass(frozen=True)
class ResearchPacketSourceFreshnessAlertScoreV2Input:
    packet_ref: str
    question_ref: str
    source_age_hours: Decimal
    official_source_lag_hours: Decimal
    independent_corroboration_age_hours: Decimal
    contradiction_unresolved_age_hours: Decimal
    probability_move_magnitude: Decimal
    hours_to_resolution: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceFreshnessAlertScoreV2Input:
            raise ValueError("subject must be a ResearchPacketSourceFreshnessAlertScoreV2Input")
        for field_name in ("packet_ref", "question_ref"):
            _require_identifier(field_name, getattr(self, field_name))
        for field_name in (
            "source_age_hours",
            "official_source_lag_hours",
            "independent_corroboration_age_hours",
            "contradiction_unresolved_age_hours",
            "hours_to_resolution",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "probability_move_magnitude",
            _normalize_probability(
                "probability_move_magnitude",
                self.probability_move_magnitude,
            ),
        )
        _require_hard_flags(self)
        _reject_unsafe_public_payload("source freshness alert input", asdict(self))


@dataclass(frozen=True)
class ResearchPacketSourceFreshnessAlertScoreV2Row:
    packet_ref: str
    question_ref: str
    priority_rank: Decimal
    priority_score: Decimal
    source_age_score: Decimal
    official_source_lag_score: Decimal
    independent_corroboration_age_score: Decimal
    contradiction_unresolved_age_score: Decimal
    probability_move_score: Decimal
    close_urgency_score: Decimal
    source_age_hours: Decimal
    official_source_lag_hours: Decimal
    independent_corroboration_age_hours: Decimal
    contradiction_unresolved_age_hours: Decimal
    probability_move_magnitude: Decimal
    hours_to_resolution: Decimal
    alert_status: str
    recommended_research_action: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceFreshnessAlertScoreV2Row:
            raise ValueError("row must be a ResearchPacketSourceFreshnessAlertScoreV2Row")
        for field_name in ("packet_ref", "question_ref"):
            _require_identifier(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "priority_rank",
            _normalize_positive_decimal("priority_rank", self.priority_rank),
        )
        for field_name in (
            "priority_score",
            "source_age_score",
            "official_source_lag_score",
            "independent_corroboration_age_score",
            "contradiction_unresolved_age_score",
            "probability_move_score",
            "close_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_age_hours",
            "official_source_lag_hours",
            "independent_corroboration_age_hours",
            "contradiction_unresolved_age_hours",
            "hours_to_resolution",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "probability_move_magnitude",
            _normalize_probability(
                "probability_move_magnitude",
                self.probability_move_magnitude,
            ),
        )
        _require_choice("alert_status", self.alert_status, STATUSES)
        _require_choice(
            "recommended_research_action",
            self.recommended_research_action,
            tuple(ROW_ACTIONS.values()),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _require_hard_flags(self)
        _reject_unsafe_public_payload("source freshness alert row", asdict(self))
        _validate_row(self)


@dataclass(frozen=True)
class ResearchPacketSourceFreshnessAlertScoreV2Report:
    config_version: str
    status: str
    recommended_next_step: str
    input_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    stale_source_age_count: Decimal
    official_source_lag_count: Decimal
    stale_independent_corroboration_count: Decimal
    unresolved_contradiction_count: Decimal
    material_probability_move_count: Decimal
    close_resolution_urgency_count: Decimal
    highest_priority_score: Decimal
    rows: tuple[ResearchPacketSourceFreshnessAlertScoreV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceFreshnessAlertScoreV2Report:
            raise ValueError("report must be a ResearchPacketSourceFreshnessAlertScoreV2Report")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_SOURCE_FRESHNESS_ALERT_SCORE_V2_CONFIG_VERSION
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
            "stale_source_age_count",
            "official_source_lag_count",
            "stale_independent_corroboration_count",
            "unresolved_contradiction_count",
            "material_probability_move_count",
            "close_resolution_urgency_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "highest_priority_score",
            _normalize_probability("highest_priority_score", self.highest_priority_score),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _require_hard_flags(self)
        _reject_unsafe_public_payload("source freshness alert report", asdict(self))
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
                _normalize_derived_validation_digest(self.derived_validation_digest),
            )
        _validate_report(self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload("source freshness alert payload", payload)
        if type(payload) is not dict:
            raise ValueError("source freshness alert payload must be an object")
        return payload

    @classmethod
    def from_payload(
        cls,
        payload: object,
    ) -> ResearchPacketSourceFreshnessAlertScoreV2Report:
        _reject_unsafe_public_payload("source freshness alert payload", payload)
        payload_dict = _payload_dict("source freshness alert payload", payload)
        _require_payload_fields(payload_dict, _REPORT_PAYLOAD_FIELDS)
        rows_value = payload_dict["rows"]
        if not isinstance(rows_value, list):
            raise ValueError("rows must be a list")
        rows = tuple(_row_from_payload(item) for item in rows_value)
        return cls(
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
            stale_source_age_count=_decimal_from_payload(
                "stale_source_age_count",
                payload_dict["stale_source_age_count"],
            ),
            official_source_lag_count=_decimal_from_payload(
                "official_source_lag_count",
                payload_dict["official_source_lag_count"],
            ),
            stale_independent_corroboration_count=_decimal_from_payload(
                "stale_independent_corroboration_count",
                payload_dict["stale_independent_corroboration_count"],
            ),
            unresolved_contradiction_count=_decimal_from_payload(
                "unresolved_contradiction_count",
                payload_dict["unresolved_contradiction_count"],
            ),
            material_probability_move_count=_decimal_from_payload(
                "material_probability_move_count",
                payload_dict["material_probability_move_count"],
            ),
            close_resolution_urgency_count=_decimal_from_payload(
                "close_resolution_urgency_count",
                payload_dict["close_resolution_urgency_count"],
            ),
            highest_priority_score=_decimal_from_payload(
                "highest_priority_score",
                payload_dict["highest_priority_score"],
            ),
            rows=rows,
            reason_codes=_string_tuple_from_payload(
                "reason_codes",
                payload_dict["reason_codes"],
            ),
            derived_validation_digest=_payload_string(
                DERIVED_VALIDATION_DIGEST_FIELD,
                payload_dict[DERIVED_VALIDATION_DIGEST_FIELD],
            ),
            paper_only=_payload_bool("paper_only", payload_dict["paper_only"]),
            report_only=_payload_bool("report_only", payload_dict["report_only"]),
            readonly=_payload_bool("readonly", payload_dict["readonly"]),
        )


_REPORT_PAYLOAD_FIELDS = (
    "config_version",
    "status",
    "recommended_next_step",
    "input_count",
    "blocked_count",
    "watch_count",
    "pass_count",
    "stale_source_age_count",
    "official_source_lag_count",
    "stale_independent_corroboration_count",
    "unresolved_contradiction_count",
    "material_probability_move_count",
    "close_resolution_urgency_count",
    "highest_priority_score",
    "rows",
    "reason_codes",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
_ROW_PAYLOAD_FIELDS = (
    "packet_ref",
    "question_ref",
    "priority_rank",
    "priority_score",
    "source_age_score",
    "official_source_lag_score",
    "independent_corroboration_age_score",
    "contradiction_unresolved_age_score",
    "probability_move_score",
    "close_urgency_score",
    "source_age_hours",
    "official_source_lag_hours",
    "independent_corroboration_age_hours",
    "contradiction_unresolved_age_hours",
    "probability_move_magnitude",
    "hours_to_resolution",
    "alert_status",
    "recommended_research_action",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)


def build_research_packet_source_freshness_alert_score_v2_report(
    rows: object,
    *,
    config: ResearchPacketSourceFreshnessAlertScoreV2Config | None = None,
) -> ResearchPacketSourceFreshnessAlertScoreV2Report:
    if config is None:
        config = ResearchPacketSourceFreshnessAlertScoreV2Config()
    if type(config) is not ResearchPacketSourceFreshnessAlertScoreV2Config:
        raise ValueError("config must be a ResearchPacketSourceFreshnessAlertScoreV2Config")
    _require_hard_flags(config)
    source_rows = _normalize_input_rows(rows)
    ranked_rows = tuple(
        _ranked_row(row, rank=index + 1)
        for index, row in enumerate(
            sorted(
                (_unranked_row(item, config=config) for item in source_rows),
                key=_row_sort_key,
            ),
        )
    )
    status = _report_status(ranked_rows)
    return ResearchPacketSourceFreshnessAlertScoreV2Report(
        config_version=config.config_version,
        status=status,
        recommended_next_step=REPORT_NEXT_STEPS[status],
        input_count=_count(len(source_rows)),
        blocked_count=_status_count(ranked_rows, "blocked"),
        watch_count=_status_count(ranked_rows, "watch"),
        pass_count=_status_count(ranked_rows, "pass"),
        stale_source_age_count=_reason_count(ranked_rows, "stale_source_age"),
        official_source_lag_count=_reason_count(ranked_rows, "official_source_lag"),
        stale_independent_corroboration_count=_reason_count(
            ranked_rows,
            "stale_independent_corroboration",
        ),
        unresolved_contradiction_count=_reason_count(
            ranked_rows,
            "unresolved_contradiction",
        ),
        material_probability_move_count=_reason_count(
            ranked_rows,
            "material_probability_move",
        ),
        close_resolution_urgency_count=_reason_count(
            ranked_rows,
            "close_resolution_urgency",
        ),
        highest_priority_score=_max_priority_score(ranked_rows),
        rows=ranked_rows,
        reason_codes=_report_reason_codes(ranked_rows),
    )


def research_packet_source_freshness_alert_score_v2_payload(
    report: ResearchPacketSourceFreshnessAlertScoreV2Report,
) -> dict[str, object]:
    if type(report) is not ResearchPacketSourceFreshnessAlertScoreV2Report:
        raise ValueError(
            "report must be a ResearchPacketSourceFreshnessAlertScoreV2Report",
        )
    _require_hard_flags(report)
    _validate_report(report)
    return report.payload


def _unranked_row(
    subject: ResearchPacketSourceFreshnessAlertScoreV2Input,
    *,
    config: ResearchPacketSourceFreshnessAlertScoreV2Config,
) -> ResearchPacketSourceFreshnessAlertScoreV2Row:
    source_age_score = _age_score(
        subject.source_age_hours,
        config.fresh_source_age_hours,
        config.stale_source_age_span_hours,
    )
    official_source_lag_score = _age_score(
        subject.official_source_lag_hours,
        config.allowed_official_source_lag_hours,
        config.official_source_lag_span_hours,
    )
    independent_corroboration_age_score = _age_score(
        subject.independent_corroboration_age_hours,
        config.fresh_independent_corroboration_age_hours,
        config.stale_independent_corroboration_span_hours,
    )
    contradiction_unresolved_age_score = _age_score(
        subject.contradiction_unresolved_age_hours,
        config.fresh_contradiction_resolution_hours,
        config.stale_contradiction_unresolved_span_hours,
    )
    probability_move_score = _probability_move_score(
        subject.probability_move_magnitude,
        config.material_probability_move_threshold,
    )
    close_urgency_score = _close_urgency_score(subject.hours_to_resolution, config)
    priority_score = _priority_score(
        source_age_score=source_age_score,
        official_source_lag_score=official_source_lag_score,
        independent_corroboration_age_score=independent_corroboration_age_score,
        contradiction_unresolved_age_score=contradiction_unresolved_age_score,
        probability_move_score=probability_move_score,
        close_urgency_score=close_urgency_score,
    )
    alert_status = _alert_status(priority_score, config)
    return ResearchPacketSourceFreshnessAlertScoreV2Row(
        packet_ref=subject.packet_ref,
        question_ref=subject.question_ref,
        priority_rank=ONE,
        priority_score=priority_score,
        source_age_score=source_age_score,
        official_source_lag_score=official_source_lag_score,
        independent_corroboration_age_score=independent_corroboration_age_score,
        contradiction_unresolved_age_score=contradiction_unresolved_age_score,
        probability_move_score=probability_move_score,
        close_urgency_score=close_urgency_score,
        source_age_hours=subject.source_age_hours,
        official_source_lag_hours=subject.official_source_lag_hours,
        independent_corroboration_age_hours=subject.independent_corroboration_age_hours,
        contradiction_unresolved_age_hours=subject.contradiction_unresolved_age_hours,
        probability_move_magnitude=subject.probability_move_magnitude,
        hours_to_resolution=subject.hours_to_resolution,
        alert_status=alert_status,
        recommended_research_action=ROW_ACTIONS[alert_status],
        reason_codes=_row_reason_codes(
            alert_status=alert_status,
            source_age_score=source_age_score,
            official_source_lag_score=official_source_lag_score,
            independent_corroboration_age_score=independent_corroboration_age_score,
            contradiction_unresolved_age_score=contradiction_unresolved_age_score,
            probability_move_score=probability_move_score,
            close_urgency_score=close_urgency_score,
        ),
    )


def _ranked_row(
    row: ResearchPacketSourceFreshnessAlertScoreV2Row,
    *,
    rank: int,
) -> ResearchPacketSourceFreshnessAlertScoreV2Row:
    return replace(row, priority_rank=_count(rank))


def _row_sort_key(
    row: ResearchPacketSourceFreshnessAlertScoreV2Row,
) -> tuple[Decimal, str, str]:
    return (-row.priority_score, row.packet_ref, row.question_ref)


def _age_score(age: Decimal, fresh_age: Decimal, stale_span: Decimal) -> Decimal:
    if age <= fresh_age:
        return ZERO
    return _clamp_probability(_ratio(age - fresh_age, stale_span))


def _probability_move_score(move: Decimal, threshold: Decimal) -> Decimal:
    if move <= threshold:
        return ZERO
    return _clamp_probability(_ratio(move - threshold, ONE - threshold))


def _close_urgency_score(
    hours_to_resolution: Decimal,
    config: ResearchPacketSourceFreshnessAlertScoreV2Config,
) -> Decimal:
    if hours_to_resolution <= config.close_resolution_hours:
        return ONE
    if hours_to_resolution >= config.safe_resolution_hours:
        return ZERO
    return _clamp_probability(
        _ratio(
            config.safe_resolution_hours - hours_to_resolution,
            config.safe_resolution_hours - config.close_resolution_hours,
        ),
    )


def _priority_score(
    *,
    source_age_score: Decimal,
    official_source_lag_score: Decimal,
    independent_corroboration_age_score: Decimal,
    contradiction_unresolved_age_score: Decimal,
    probability_move_score: Decimal,
    close_urgency_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_probability(
            (
                source_age_score * SOURCE_AGE_WEIGHT
                + official_source_lag_score * OFFICIAL_SOURCE_LAG_WEIGHT
                + independent_corroboration_age_score
                * INDEPENDENT_CORROBORATION_AGE_WEIGHT
                + contradiction_unresolved_age_score
                * CONTRADICTION_UNRESOLVED_AGE_WEIGHT
                + probability_move_score * PROBABILITY_MOVE_WEIGHT
                + close_urgency_score * CLOSE_URGENCY_WEIGHT
            ).quantize(SCORE_QUANT),
        )


def _alert_status(
    priority_score: Decimal,
    config: ResearchPacketSourceFreshnessAlertScoreV2Config,
) -> str:
    if priority_score >= config.blocked_priority_score:
        return "blocked"
    if priority_score >= config.watch_priority_score:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    alert_status: str,
    source_age_score: Decimal,
    official_source_lag_score: Decimal,
    independent_corroboration_age_score: Decimal,
    contradiction_unresolved_age_score: Decimal,
    probability_move_score: Decimal,
    close_urgency_score: Decimal,
) -> tuple[str, ...]:
    codes = [f"source_freshness_alert_status_{alert_status}"]
    if source_age_score > ZERO:
        codes.append("stale_source_age")
    if official_source_lag_score > ZERO:
        codes.append("official_source_lag")
    if independent_corroboration_age_score > ZERO:
        codes.append("stale_independent_corroboration")
    if contradiction_unresolved_age_score > ZERO:
        codes.append("unresolved_contradiction")
    if probability_move_score > ZERO:
        codes.append("material_probability_move")
    if close_urgency_score > ZERO:
        codes.append("close_resolution_urgency")
    return tuple(codes)


def _report_reason_codes(
    rows: tuple[ResearchPacketSourceFreshnessAlertScoreV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("source_freshness_alert_no_inputs",)
    status = _report_status(rows)
    codes = [f"source_freshness_alert_status_{status}"]
    row_codes = {code for row in rows for code in row.reason_codes}
    for code in DETAIL_REASON_CODES:
        if code in row_codes:
            codes.append(code)
    return tuple(codes)


def _report_status(rows: tuple[ResearchPacketSourceFreshnessAlertScoreV2Row, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.alert_status == "blocked" for row in rows):
        return "blocked"
    if any(row.alert_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _status_count(
    rows: tuple[ResearchPacketSourceFreshnessAlertScoreV2Row, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.alert_status == status))


def _reason_count(
    rows: tuple[ResearchPacketSourceFreshnessAlertScoreV2Row, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_priority_score(
    rows: tuple[ResearchPacketSourceFreshnessAlertScoreV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.priority_score for row in rows)


def _validate_row(row: ResearchPacketSourceFreshnessAlertScoreV2Row) -> None:
    expected_priority_score = _priority_score(
        source_age_score=row.source_age_score,
        official_source_lag_score=row.official_source_lag_score,
        independent_corroboration_age_score=row.independent_corroboration_age_score,
        contradiction_unresolved_age_score=row.contradiction_unresolved_age_score,
        probability_move_score=row.probability_move_score,
        close_urgency_score=row.close_urgency_score,
    )
    if row.priority_score != expected_priority_score:
        raise ValueError("priority_score must match freshness alert drivers")
    if row.recommended_research_action != ROW_ACTIONS[row.alert_status]:
        raise ValueError("recommended_research_action must match alert_status")
    expected_reason_codes = _row_reason_codes(
        alert_status=row.alert_status,
        source_age_score=row.source_age_score,
        official_source_lag_score=row.official_source_lag_score,
        independent_corroboration_age_score=row.independent_corroboration_age_score,
        contradiction_unresolved_age_score=row.contradiction_unresolved_age_score,
        probability_move_score=row.probability_move_score,
        close_urgency_score=row.close_urgency_score,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match freshness alert drivers")
    details = tuple(reason for reason in row.reason_codes if reason in DETAIL_REASON_CODES)
    if row.alert_status == "pass" and details:
        raise ValueError("pass rows must not include detail reason codes")
    if row.alert_status != "pass" and not details:
        raise ValueError("non-pass rows must include detail reason codes")


def _validate_report(report: ResearchPacketSourceFreshnessAlertScoreV2Report) -> None:
    for row in report.rows:
        _validate_row(row)
    if report.derived_validation_digest != _derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")
    expected_status = _report_status(report.rows)
    if report.status != expected_status:
        raise ValueError("status must match rows")
    if report.recommended_next_step != REPORT_NEXT_STEPS[report.status]:
        raise ValueError("recommended_next_step must match status")
    if report.input_count != _count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.stale_source_age_count != _reason_count(report.rows, "stale_source_age"):
        raise ValueError("stale_source_age_count must match rows")
    if report.official_source_lag_count != _reason_count(
        report.rows,
        "official_source_lag",
    ):
        raise ValueError("official_source_lag_count must match rows")
    if report.stale_independent_corroboration_count != _reason_count(
        report.rows,
        "stale_independent_corroboration",
    ):
        raise ValueError("stale_independent_corroboration_count must match rows")
    if report.unresolved_contradiction_count != _reason_count(
        report.rows,
        "unresolved_contradiction",
    ):
        raise ValueError("unresolved_contradiction_count must match rows")
    if report.material_probability_move_count != _reason_count(
        report.rows,
        "material_probability_move",
    ):
        raise ValueError("material_probability_move_count must match rows")
    if report.close_resolution_urgency_count != _reason_count(
        report.rows,
        "close_resolution_urgency",
    ):
        raise ValueError("close_resolution_urgency_count must match rows")
    if report.highest_priority_score != _max_priority_score(report.rows):
        raise ValueError("highest_priority_score must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_input_rows(
    rows: object,
) -> tuple[ResearchPacketSourceFreshnessAlertScoreV2Input, ...]:
    if isinstance(rows, (str, bytes)) or not hasattr(rows, "__iter__"):
        raise ValueError(
            "rows must be an iterable of ResearchPacketSourceFreshnessAlertScoreV2Input",
        )
    normalized = tuple(rows)
    seen: set[tuple[str, str]] = set()
    for row in normalized:
        if type(row) is not ResearchPacketSourceFreshnessAlertScoreV2Input:
            raise ValueError(
                "rows must be ResearchPacketSourceFreshnessAlertScoreV2Input values",
            )
        _require_hard_flags(row)
        key = (row.packet_ref, row.question_ref)
        if key in seen:
            raise ValueError("rows must be unique by packet_ref and question_ref")
        seen.add(key)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[ResearchPacketSourceFreshnessAlertScoreV2Row, ...]:
    if isinstance(rows, (str, bytes)) or not hasattr(rows, "__iter__"):
        raise ValueError(
            "rows must be an iterable of ResearchPacketSourceFreshnessAlertScoreV2Row",
        )
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchPacketSourceFreshnessAlertScoreV2Row:
            raise ValueError(
                "rows must be ResearchPacketSourceFreshnessAlertScoreV2Row values",
            )
        _require_hard_flags(row)
    expected_ranks = tuple(_count(index + 1) for index in range(len(normalized)))
    actual_ranks = tuple(row.priority_rank for row in normalized)
    if actual_ranks != expected_ranks:
        raise ValueError("priority_rank must match row order")
    expected_order = tuple(sorted(normalized, key=_row_sort_key))
    if normalized != expected_order:
        raise ValueError("rows must use deterministic priority order")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent < SCORE_QUANT.as_tuple().exponent:
        raise ValueError(f"{field_name} must not exceed six decimal places")
    return _q(value)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_derived_validation_digest(value: object) -> str:
    if type(value) is not str:
        raise ValueError("derived_validation_digest must be a string")
    if len(value) != SHA256_HEX_LENGTH:
        raise ValueError("derived_validation_digest must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError("derived_validation_digest must be a sha256 hex digest")
    return value


def _q(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(SCORE_QUANT)


def _ratio(part: Decimal, whole: Decimal) -> Decimal:
    if whole == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (part / whole).quantize(SCORE_QUANT)


def _clamp_probability(value: Decimal) -> Decimal:
    normalized = _q(value)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(SCORE_QUANT)


def _require_identifier(field_name: str, value: object) -> str:
    return _require_canonical_string(field_name, value)


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "":
        raise ValueError(f"{field_name} must not be empty")
    if value != value.strip() or any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must be canonical")
    if value != value.lower():
        raise ValueError(f"{field_name} must be lowercase")
    return value


def _require_choice(field_name: str, value: object, choices: tuple[str, ...]) -> str:
    if type(value) is not str or value not in choices:
        raise ValueError(f"{field_name} must be a supported value")
    return value


def _normalize_reason_codes(value: object, *, allow_empty: bool) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    normalized = tuple(value)
    if not allow_empty and not normalized:
        raise ValueError("reason_codes must not be empty")
    for code in normalized:
        _require_canonical_string("reason_code", code)
        if code not in REASON_CODES:
            raise ValueError("reason_codes must be supported")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    return normalized


def _require_hard_flags(value: object) -> None:
    for field_name in HARD_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _derived_validation_digest(
    report: ResearchPacketSourceFreshnessAlertScoreV2Report,
) -> str:
    payload = _payload_value(asdict(report))
    if type(payload) is not dict:
        raise ValueError("source freshness alert payload must be an object")
    payload.pop(DERIVED_VALIDATION_DIGEST_FIELD, None)
    return _payload_digest(payload)


def _payload_digest(payload: dict[str, object]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop(DERIVED_VALIDATION_DIGEST_FIELD, None)
    encoded = json.dumps(
        digest_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _payload_value(value: Any) -> object:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal value must be finite")
        return str(value)
    if type(value) in (str, bool):
        return value
    if isinstance(value, dict):
        payload: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            payload[key] = _payload_value(item)
        return payload
    if isinstance(value, (list, tuple)):
        return [_payload_value(item) for item in value]
    raise ValueError("payload value is not supported")


def _reject_unsafe_public_payload(label: str, value: Any) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)
        return
    if value is None or type(value) in (bool, int):
        return
    if type(value) is Decimal:
        _normalize_decimal("public Decimal value", value)
        return
    raise ValueError(f"public payload value is not supported for {label}")


def _reject_unsafe_public_text(label: str, value: str) -> None:
    lowered = value.lower()
    if any(term in lowered for term in UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"unsafe public payload {label}: {value}")


def _payload_dict(field_name: str, value: object) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError(f"{field_name} must be an object")
    return value


def _require_payload_fields(payload: dict[str, Any], fields: tuple[str, ...]) -> None:
    expected = set(fields)
    actual = set(payload)
    if actual != expected:
        raise ValueError("payload fields must match source freshness alert schema")


def _payload_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _payload_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _decimal_from_payload(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    return _normalize_decimal(field_name, decimal_value)


def _string_tuple_from_payload(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    return tuple(_payload_string(field_name, item) for item in value)


def _row_from_payload(payload: object) -> ResearchPacketSourceFreshnessAlertScoreV2Row:
    payload_dict = _payload_dict("row", payload)
    _require_payload_fields(payload_dict, _ROW_PAYLOAD_FIELDS)
    return ResearchPacketSourceFreshnessAlertScoreV2Row(
        packet_ref=_payload_string("packet_ref", payload_dict["packet_ref"]),
        question_ref=_payload_string("question_ref", payload_dict["question_ref"]),
        priority_rank=_decimal_from_payload("priority_rank", payload_dict["priority_rank"]),
        priority_score=_decimal_from_payload("priority_score", payload_dict["priority_score"]),
        source_age_score=_decimal_from_payload(
            "source_age_score",
            payload_dict["source_age_score"],
        ),
        official_source_lag_score=_decimal_from_payload(
            "official_source_lag_score",
            payload_dict["official_source_lag_score"],
        ),
        independent_corroboration_age_score=_decimal_from_payload(
            "independent_corroboration_age_score",
            payload_dict["independent_corroboration_age_score"],
        ),
        contradiction_unresolved_age_score=_decimal_from_payload(
            "contradiction_unresolved_age_score",
            payload_dict["contradiction_unresolved_age_score"],
        ),
        probability_move_score=_decimal_from_payload(
            "probability_move_score",
            payload_dict["probability_move_score"],
        ),
        close_urgency_score=_decimal_from_payload(
            "close_urgency_score",
            payload_dict["close_urgency_score"],
        ),
        source_age_hours=_decimal_from_payload(
            "source_age_hours",
            payload_dict["source_age_hours"],
        ),
        official_source_lag_hours=_decimal_from_payload(
            "official_source_lag_hours",
            payload_dict["official_source_lag_hours"],
        ),
        independent_corroboration_age_hours=_decimal_from_payload(
            "independent_corroboration_age_hours",
            payload_dict["independent_corroboration_age_hours"],
        ),
        contradiction_unresolved_age_hours=_decimal_from_payload(
            "contradiction_unresolved_age_hours",
            payload_dict["contradiction_unresolved_age_hours"],
        ),
        probability_move_magnitude=_decimal_from_payload(
            "probability_move_magnitude",
            payload_dict["probability_move_magnitude"],
        ),
        hours_to_resolution=_decimal_from_payload(
            "hours_to_resolution",
            payload_dict["hours_to_resolution"],
        ),
        alert_status=_payload_string("alert_status", payload_dict["alert_status"]),
        recommended_research_action=_payload_string(
            "recommended_research_action",
            payload_dict["recommended_research_action"],
        ),
        reason_codes=_string_tuple_from_payload("reason_codes", payload_dict["reason_codes"]),
        paper_only=_payload_bool("paper_only", payload_dict["paper_only"]),
        report_only=_payload_bool("report_only", payload_dict["report_only"]),
        readonly=_payload_bool("readonly", payload_dict["readonly"]),
    )
